#!/usr/bin/env python3
"""WAVE ROVER 最小起动阈值 probe。

本脚本只通过 ROS2 `/cmd_vel` 与 `/trashbot/stop` 走现有 esp32_bridge。
它不直接打开 WAVE ROVER UART，不绕过项目 stop service。
"""

from __future__ import annotations

import csv
import json
import math
import os
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_srvs.srv import Trigger


MAX_WHEEL_SPEED_MPS = 1.3
STEPS_MPS = [0.03, 0.05, 0.07, 0.09]
PUBLISH_WINDOW_S = 0.16
HARD_WINDOW_LIMIT_S = 0.18
SCAN_MIN_FRAMES = 3
SCAN_MIN_BINS = 80
SCAN_MIN_SPAN_DEG = 90.0
MOTION_PAIRED_BINS_MIN = 40
MOTION_MEDIAN_DIFF_MIN_M = 0.03
MOTION_CHANGED_RATIO_MIN = 0.12


@dataclass
class ScanProfile:
    """聚合一段窗口内的 LaserScan，减少单帧噪声对阈值判断的影响。"""

    frames: int
    healthy_frames: int
    bins: dict[int, list[float]]
    latest_stats: dict[str, Any]


class ProbeNode(Node):
    """ROS2 采集节点，集中管理订阅、发布和 stop service。"""

    def __init__(self, artifacts_dir: Path):
        super().__init__("wave_rover_min_actuation_probe")
        self.artifacts_dir = artifacts_dir
        self.scan_frames: list[LaserScan] = []
        self.odom_samples: list[tuple[float, float, float]] = []
        self.scan_stats_path = artifacts_dir / "scan_frame_stats.jsonl"
        self.odom_samples_path = artifacts_dir / "odom_samples.jsonl"
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.stop_client = self.create_client(Trigger, "/trashbot/stop")
        # 只订阅本轮验收需要的数据，避免引入导航或相机等额外变量。
        self.create_subscription(LaserScan, "/scan", self._on_scan, 10)
        self.create_subscription(Odometry, "/odom", self._on_odom, 10)

    def _on_scan(self, msg: LaserScan) -> None:
        stats = scan_stats(msg)
        self.scan_frames.append(msg)
        with self.scan_stats_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(stats, sort_keys=True, separators=(",", ":")) + "\n")

    def _on_odom(self, msg: Odometry) -> None:
        now = time.time()
        x = float(msg.pose.pose.position.x)
        y = float(msg.pose.pose.position.y)
        self.odom_samples.append((now, x, y))
        with self.odom_samples_path.open("a", encoding="utf-8") as handle:
            record = {"observed_at_unix_s": now, "x": x, "y": y}
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")

    def call_stop(self, timeout_s: float = 3.0) -> dict[str, Any]:
        if not self.stop_client.wait_for_service(timeout_sec=timeout_s):
            return {"success": False, "message": "stop service unavailable"}
        future = self.stop_client.call_async(Trigger.Request())
        deadline = time.monotonic() + timeout_s
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
            if future.done():
                response = future.result()
                return {"success": bool(response.success), "message": str(response.message)}
        return {"success": False, "message": "stop service timeout"}

    def publish_cmd(self, linear_x: float, angular_z: float) -> None:
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.angular.z = float(angular_z)
        self.cmd_pub.publish(msg)

    def publish_zero_and_stop(self) -> dict[str, Any]:
        # 零速发布和 stop service 双路径都执行，降低单次 ROS 消息丢失的风险。
        for _ in range(3):
            self.publish_cmd(0.0, 0.0)
            rclpy.spin_once(self, timeout_sec=0.03)
        return self.call_stop()

    def collect_window(self, duration_s: float) -> list[LaserScan]:
        start = len(self.scan_frames)
        deadline = time.monotonic() + duration_s
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
        return self.scan_frames[start:]


def scan_stats(msg: LaserScan) -> dict[str, Any]:
    finite_ranges = [float(v) for v in msg.ranges if math.isfinite(float(v)) and float(v) > 0.0]
    angle_span = float(msg.angle_max - msg.angle_min) * 180.0 / math.pi
    return {
        "observed_at_unix_s": time.time(),
        "frame_id": msg.header.frame_id,
        "ranges_count": len(msg.ranges),
        "finite_count": len(finite_ranges),
        "angle_min": float(msg.angle_min),
        "angle_max": float(msg.angle_max),
        "angle_span_deg": angle_span,
    }


def is_healthy_stats(stats: dict[str, Any]) -> bool:
    return (
        int(stats.get("ranges_count", 0)) >= SCAN_MIN_BINS
        and int(stats.get("finite_count", 0)) >= SCAN_MIN_BINS
        and float(stats.get("angle_span_deg", 0.0)) >= SCAN_MIN_SPAN_DEG
    )


def build_profile(frames: list[LaserScan]) -> ScanProfile:
    bins: dict[int, list[float]] = {}
    healthy = 0
    latest = {}
    for msg in frames:
        latest = scan_stats(msg)
        if is_healthy_stats(latest):
            healthy += 1
        # 角度量化到 0.5 度，保证 baseline/post 能有稳定可配对 bins。
        for index, value in enumerate(msg.ranges):
            distance = float(value)
            if not math.isfinite(distance) or distance <= 0.0:
                continue
            angle = float(msg.angle_min + index * msg.angle_increment)
            key = int(round((angle * 180.0 / math.pi) * 2.0))
            bins.setdefault(key, []).append(distance)
    return ScanProfile(frames=len(frames), healthy_frames=healthy, bins=bins, latest_stats=latest)


def compare_profiles(baseline: ScanProfile, post: ScanProfile) -> dict[str, Any]:
    diffs = []
    for key in sorted(set(baseline.bins) & set(post.bins)):
        left = statistics.median(baseline.bins[key])
        right = statistics.median(post.bins[key])
        diffs.append(abs(right - left))
    paired_bins = len(diffs)
    changed = sum(1 for diff in diffs if diff >= MOTION_MEDIAN_DIFF_MIN_M)
    changed_ratio = changed / paired_bins if paired_bins else 0.0
    median_diff = statistics.median(diffs) if diffs else 0.0
    mean_diff = statistics.fmean(diffs) if diffs else 0.0
    max_diff = max(diffs) if diffs else 0.0
    proven = (
        paired_bins >= MOTION_PAIRED_BINS_MIN
        and median_diff >= MOTION_MEDIAN_DIFF_MIN_M
        and changed_ratio >= MOTION_CHANGED_RATIO_MIN
        and baseline.frames >= SCAN_MIN_FRAMES
        and post.frames >= SCAN_MIN_FRAMES
        and baseline.healthy_frames >= SCAN_MIN_FRAMES
        and post.healthy_frames >= SCAN_MIN_FRAMES
    )
    return {
        "paired_bins": paired_bins,
        "median_abs_diff_m": median_diff,
        "mean_abs_diff_m": mean_diff,
        "max_abs_diff_m": max_diff,
        "changed_bin_ratio": changed_ratio,
        "changed_bins": changed,
        "baseline_scan_frames": baseline.frames,
        "baseline_healthy_scan_frames": baseline.healthy_frames,
        "post_scan_frames": post.frames,
        "post_healthy_scan_frames": post.healthy_frames,
        "baseline_latest_stats": baseline.latest_stats,
        "post_latest_stats": post.latest_stats,
        "physical_motion_lidar_delta_proven": proven,
    }


def expected_json(linear_x: float) -> dict[str, Any]:
    wheel = round(linear_x / MAX_WHEEL_SPEED_MPS, 6)
    return {"T": 1, "L": wheel, "R": wheel}


def odom_delta(samples: list[tuple[float, float, float]], start_index: int) -> float:
    segment = samples[start_index:]
    if len(segment) < 2:
        return 0.0
    _, x0, y0 = segment[0]
    _, x1, y1 = segment[-1]
    return math.hypot(x1 - x0, y1 - y0)


def summarize_feedback(path: Path, since_unix_s: float = 0.0) -> dict[str, Any]:
    records = []
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if float(record.get("observed_at_unix_s", 0.0)) >= since_unix_s:
                    records.append(record)
    nonzero = []
    for record in records:
        left = record.get("left_speed")
        right = record.get("right_speed")
        if left is None or right is None:
            continue
        if abs(float(left)) > 0.0 or abs(float(right)) > 0.0:
            nonzero.append(record)
    return {
        "record_count": len(records),
        "left_speed_nonzero": any(abs(float(r.get("left_speed", 0.0))) > 0.0 for r in nonzero),
        "right_speed_nonzero": any(abs(float(r.get("right_speed", 0.0))) > 0.0 for r in nonzero),
        "wheel_feedback_lr_nonzero_proven": bool(nonzero),
        "first_nonzero": nonzero[0] if nonzero else None,
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    artifacts_dir = Path(os.environ.get("PROBE_ARTIFACT_DIR", "/tmp/wave_rover_min_actuation_probe"))
    feedback_debug = Path(os.environ.get("WAVE_ROVER_FEEDBACK_DEBUG", str(artifacts_dir / "wave_rover_feedback_debug.jsonl")))
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    rclpy.init()
    node = ProbeNode(artifacts_dir)
    step_rows = []
    summary: dict[str, Any] = {
        "schema": "trashbot.wave_rover.min_actuation_probe.v1",
        "started_at_unix_s": time.time(),
        "motion_commands_sent": False,
        "max_step_linear_x_mps_sent": 0.0,
        "physical_motion_lidar_delta_proven": False,
        "wheel_feedback_lr_nonzero_proven": False,
        "min_actuation_step_proven": None,
        "safe_to_control": False,
        "delivery_success": False,
        "steps": [],
    }
    try:
        pre_stop = node.publish_zero_and_stop()
        summary["pre_stop"] = pre_stop
        if not pre_stop.get("success"):
            summary["failure_reason"] = "pre_stop_failed"
            return 2

        baseline_frames = node.collect_window(1.6)
        baseline = build_profile(baseline_frames)
        summary["baseline_profile"] = {
            "scan_frames": baseline.frames,
            "healthy_scan_frames": baseline.healthy_frames,
            "latest_stats": baseline.latest_stats,
        }
        if baseline.frames < SCAN_MIN_FRAMES or baseline.healthy_frames < SCAN_MIN_FRAMES:
            summary["failure_reason"] = "baseline_scan_unhealthy"
            return 3

        for step_index, linear_x in enumerate(STEPS_MPS, start=1):
            step_start = time.time()
            odom_start_index = len(node.odom_samples)
            feedback_start = step_start
            step: dict[str, Any] = {
                "step_index": step_index,
                "linear_x_mps": linear_x,
                "angular_z_radps": 0.0,
                "expected_json": expected_json(linear_x),
                "expected_json_source": "project speed mode formula linear.x/max_wheel_speed_mps; not hardware feedback",
            }

            command = Twist()
            command.linear.x = linear_x
            command.angular.z = 0.0
            publish_deadline = time.monotonic() + PUBLISH_WINDOW_S
            first_publish = time.monotonic()
            while rclpy.ok() and time.monotonic() < publish_deadline:
                node.cmd_pub.publish(command)
                rclpy.spin_once(node, timeout_sec=0.02)
            actual_window = time.monotonic() - first_publish
            step["actual_publish_window_s"] = actual_window
            summary["motion_commands_sent"] = True
            summary["max_step_linear_x_mps_sent"] = max(summary["max_step_linear_x_mps_sent"], linear_x)

            stop_result = node.publish_zero_and_stop()
            step["post_stop"] = stop_result
            post_frames = node.collect_window(1.8)
            post = build_profile(post_frames)
            metrics = compare_profiles(baseline, post)
            feedback = summarize_feedback(feedback_debug, feedback_start)
            step.update(metrics)
            step["feedback_summary"] = feedback
            step["command_integration_odom_delta_m"] = odom_delta(node.odom_samples, odom_start_index)
            step["abort_after_step"] = False
            step["step_elapsed_s"] = time.time() - step_start

            step_rows.append({
                "step_index": step_index,
                "linear_x_mps": linear_x,
                "actual_publish_window_s": actual_window,
                "paired_bins": metrics["paired_bins"],
                "median_abs_diff_m": metrics["median_abs_diff_m"],
                "changed_bin_ratio": metrics["changed_bin_ratio"],
                "post_healthy_scan_frames": metrics["post_healthy_scan_frames"],
                "wheel_feedback_lr_nonzero_proven": feedback["wheel_feedback_lr_nonzero_proven"],
                "command_integration_odom_delta_m": step["command_integration_odom_delta_m"],
            })
            summary["steps"].append(step)
            write_json(artifacts_dir / "wave_rover_min_actuation_probe_summary.json", summary)

            if actual_window > HARD_WINDOW_LIMIT_S:
                step["abort_after_step"] = True
                summary["failure_reason"] = "publish_window_exceeded_hard_limit"
                break
            if not stop_result.get("success"):
                step["abort_after_step"] = True
                summary["failure_reason"] = "post_stop_failed"
                break
            if metrics["physical_motion_lidar_delta_proven"] or feedback["wheel_feedback_lr_nonzero_proven"]:
                step["abort_after_step"] = True
                summary["min_actuation_step_proven"] = linear_x
                summary["physical_motion_lidar_delta_proven"] = bool(metrics["physical_motion_lidar_delta_proven"])
                summary["wheel_feedback_lr_nonzero_proven"] = bool(feedback["wheel_feedback_lr_nonzero_proven"])
                break

            # 下一步前重新建立静止 baseline，避免把上一阶梯残余噪声累入下一阶梯。
            node.collect_window(0.5)
            baseline_frames = node.collect_window(1.4)
            baseline = build_profile(baseline_frames)
            if baseline.frames < SCAN_MIN_FRAMES or baseline.healthy_frames < SCAN_MIN_FRAMES:
                summary["failure_reason"] = "inter_step_baseline_scan_unhealthy"
                break

        if summary["min_actuation_step_proven"] is None:
            summary["failure_reason"] = summary.get("failure_reason", "low_speed_steps_no_physical_or_wheel_feedback_proof")
        summary["final_stop"] = node.publish_zero_and_stop()
        summary["safe_to_control"] = bool(summary["final_stop"].get("success"))
        return 0
    finally:
        summary["finished_at_unix_s"] = time.time()
        try:
            summary["final_feedback_summary"] = summarize_feedback(feedback_debug, summary["started_at_unix_s"])
            if summary["min_actuation_step_proven"] is None and summary["final_feedback_summary"]["wheel_feedback_lr_nonzero_proven"]:
                summary["wheel_feedback_lr_nonzero_proven"] = True
        finally:
            write_json(artifacts_dir / "wave_rover_min_actuation_probe_summary.json", summary)
            csv_path = artifacts_dir / "step_metrics.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                fieldnames = [
                    "step_index",
                    "linear_x_mps",
                    "actual_publish_window_s",
                    "paired_bins",
                    "median_abs_diff_m",
                    "changed_bin_ratio",
                    "post_healthy_scan_frames",
                    "wheel_feedback_lr_nonzero_proven",
                    "command_integration_odom_delta_m",
                ]
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(step_rows)
            try:
                node.publish_zero_and_stop()
            except Exception:
                pass
            node.destroy_node()
            rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
