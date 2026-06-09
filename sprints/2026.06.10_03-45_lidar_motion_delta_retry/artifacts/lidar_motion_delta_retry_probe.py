#!/usr/bin/env python3
"""低速 LiDAR motion-delta 探针。

本脚本只用于 sprint 证据采集，不进入产品代码；它把安全停机放在运动命令之前。
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, Imu, LaserScan
from std_srvs.srv import Trigger


def _finite_ranges(scan: LaserScan) -> list[tuple[float, float]]:
    """提取有限距离点；只比较真实返回点，避免把 inf/nan 当运动证据。"""
    points: list[tuple[float, float]] = []
    for index, value in enumerate(scan.ranges):
        distance = float(value)
        if not math.isfinite(distance):
            continue
        angle = float(scan.angle_min) + float(scan.angle_increment) * index
        points.append((angle, distance))
    return points


def _scan_stats(scan: LaserScan) -> dict[str, Any]:
    """记录聚合帧形态；角度覆盖不足时禁止把 delta 判成真实运动。"""
    finite = _finite_ranges(scan)
    span = float(scan.angle_max) - float(scan.angle_min)
    return {
        "stamp_unix_s": time.time(),
        "frame_id": scan.header.frame_id,
        "ranges_count": len(scan.ranges),
        "finite_count": len(finite),
        "angle_min": float(scan.angle_min),
        "angle_max": float(scan.angle_max),
        "angle_span_deg": math.degrees(span),
        "range_min": float(scan.range_min),
        "range_max": float(scan.range_max),
    }


def _profile(scans: list[LaserScan], bin_deg: float = 1.0) -> dict[int, float]:
    """按角度分箱取中位数；用多帧中位数压制单帧抖动。"""
    bins: dict[int, list[float]] = {}
    for scan in scans:
        for angle, distance in _finite_ranges(scan):
            key = int(round(math.degrees(angle) / bin_deg))
            bins.setdefault(key, []).append(distance)
    return {key: statistics.median(values) for key, values in bins.items() if values}


def _delta_metrics(before: list[LaserScan], after: list[LaserScan]) -> dict[str, Any]:
    """计算 baseline/post 可比角度 bin 的距离变化。"""
    before_profile = _profile(before)
    after_profile = _profile(after)
    paired = sorted(set(before_profile) & set(after_profile))
    diffs = [abs(after_profile[key] - before_profile[key]) for key in paired]
    changed_threshold_m = 0.05
    changed = [value for value in diffs if value >= changed_threshold_m]
    return {
        "paired_bins": len(paired),
        "median_abs_diff_m": statistics.median(diffs) if diffs else 0.0,
        "mean_abs_diff_m": statistics.fmean(diffs) if diffs else 0.0,
        "max_abs_diff_m": max(diffs) if diffs else 0.0,
        "changed_bin_ratio": (len(changed) / len(paired)) if paired else 0.0,
        "changed_bin_abs_threshold_m": changed_threshold_m,
        "sample_diffs": [{"bin_deg": key, "abs_diff_m": diff} for key, diff in zip(paired[:80], diffs[:80])],
    }


def _odom_xy(odom: Odometry | None) -> tuple[float, float] | None:
    """只取 command integration 位置；结果不会被当成物理运动证明。"""
    if odom is None:
        return None
    return (float(odom.pose.pose.position.x), float(odom.pose.pose.position.y))


class MotionDeltaProbe(Node):
    """订阅传感器、执行一次受控脉冲，并把证据写成 artifacts。"""

    def __init__(self, args: argparse.Namespace):
        super().__init__("lidar_motion_delta_retry_probe")
        self.args = args
        self.scans: list[LaserScan] = []
        self.scan_stats: list[dict[str, Any]] = []
        self.last_odom: Odometry | None = None
        self.odom_samples: list[dict[str, Any]] = []
        self.battery_samples: list[dict[str, Any]] = []
        self.imu_samples = 0
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.stop_client = self.create_client(Trigger, "/trashbot/stop")
        self.create_subscription(LaserScan, "/scan", self._on_scan, 20)
        self.create_subscription(Odometry, "/odom", self._on_odom, 20)
        self.create_subscription(BatteryState, "/battery", self._on_battery, 10)
        self.create_subscription(Imu, "/imu/data", self._on_imu, 10)

    def _on_scan(self, msg: LaserScan) -> None:
        """保存 scan 原始消息和轻量统计，便于事后复核聚合质量。"""
        self.scans.append(msg)
        self.scan_stats.append(_scan_stats(msg))

    def _on_odom(self, msg: Odometry) -> None:
        """记录命令积分里程计；这里只用于边界说明，不作为实测位移。"""
        self.last_odom = msg
        xy = _odom_xy(msg)
        self.odom_samples.append({"stamp_unix_s": time.time(), "x": xy[0], "y": xy[1]})

    def _on_battery(self, msg: BatteryState) -> None:
        """记录电压样本，辅助判断底盘反馈链路是否仍在发布。"""
        self.battery_samples.append({"stamp_unix_s": time.time(), "voltage": float(msg.voltage)})

    def _on_imu(self, msg: Imu) -> None:
        """只计数 IMU 样本；本轮不做姿态标定结论。"""
        self.imu_samples += 1

    def spin_for(self, duration_s: float) -> None:
        """按固定时间泵 ROS 回调，避免异步订阅没有机会收帧。"""
        deadline = time.monotonic() + duration_s
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)

    def call_stop(self, timeout_s: float = 3.0) -> dict[str, Any]:
        """调用安全停车 service；失败时外层必须禁止运动。"""
        if not self.stop_client.wait_for_service(timeout_sec=timeout_s):
            return {"success": False, "message": "stop service unavailable"}
        future = self.stop_client.call_async(Trigger.Request())
        deadline = time.monotonic() + timeout_s
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
            if future.done():
                result = future.result()
                return {"success": bool(result.success), "message": str(result.message)}
        return {"success": False, "message": "stop service timeout"}

    def publish_zero(self) -> None:
        """发布零速，和 service stop 形成双保险。"""
        self.cmd_pub.publish(Twist())
        self.spin_for(0.1)

    def run(self) -> dict[str, Any]:
        """执行安全门、短脉冲、post 采样和汇总判定。"""
        start_wall = time.time()
        pre_stop = self.call_stop()
        self.publish_zero()
        motion_sent = False
        actual_duration_s = 0.0

        self.spin_for(self.args.baseline_s)
        baseline = list(self.scans)
        baseline_odom = _odom_xy(self.last_odom)
        baseline_latest = self.scan_stats[-1] if self.scan_stats else {}
        scan_healthy = (
            len(baseline) >= self.args.min_baseline_frames
            and baseline_latest.get("ranges_count", 0) >= self.args.min_ranges
            and baseline_latest.get("finite_count", 0) >= self.args.min_finite
            and baseline_latest.get("angle_span_deg", 0.0) >= self.args.min_angle_span_deg
        )
        safe_precheck = bool(pre_stop["success"]) and scan_healthy

        if safe_precheck:
            twist = Twist()
            twist.linear.x = min(float(self.args.linear_x), 0.03)
            twist.angular.z = 0.0
            pulse_start = time.monotonic()
            while time.monotonic() - pulse_start < min(float(self.args.pulse_s), 0.25):
                self.cmd_pub.publish(twist)
                rclpy.spin_once(self, timeout_sec=0.02)
                time.sleep(0.02)
            actual_duration_s = time.monotonic() - pulse_start
            motion_sent = True

        self.publish_zero()
        post_stop = self.call_stop()
        self.publish_zero()
        pre_post_count = len(self.scans)
        self.spin_for(self.args.post_s)
        post = list(self.scans[pre_post_count:]) or list(self.scans[len(baseline):])
        post_odom = _odom_xy(self.last_odom)

        delta = _delta_metrics(baseline, post)
        latest_post = _scan_stats(post[-1]) if post else {}
        odom_delta = None
        if baseline_odom is not None and post_odom is not None:
            odom_delta = math.hypot(post_odom[0] - baseline_odom[0], post_odom[1] - baseline_odom[1])

        thresholds = {
            "min_paired_bins": 40,
            "median_abs_diff_m_gte": 0.03,
            "changed_bin_ratio_gte": 0.12,
            "min_ranges": self.args.min_ranges,
            "min_finite": self.args.min_finite,
            "min_angle_span_deg": self.args.min_angle_span_deg,
        }
        lidar_delta_proven = (
            bool(motion_sent)
            and delta["paired_bins"] >= thresholds["min_paired_bins"]
            and delta["median_abs_diff_m"] >= thresholds["median_abs_diff_m_gte"]
            and delta["changed_bin_ratio"] >= thresholds["changed_bin_ratio_gte"]
            and latest_post.get("ranges_count", 0) >= self.args.min_ranges
            and latest_post.get("finite_count", 0) >= self.args.min_finite
            and latest_post.get("angle_span_deg", 0.0) >= self.args.min_angle_span_deg
        )

        return {
            "schema": "trashbot.lidar_motion_delta_retry.v1",
            "started_at_unix_s": start_wall,
            "completed_at_unix_s": time.time(),
            "motion_commands_sent": motion_sent,
            "pulse_linear_x_mps": min(float(self.args.linear_x), 0.03) if motion_sent else 0.0,
            "pulse_angular_z_radps": 0.0,
            "actual_pulse_duration_s": actual_duration_s,
            "pre_stop": pre_stop,
            "post_stop": post_stop,
            "stop_confirmed": bool(post_stop["success"]),
            "safe_precheck_passed": safe_precheck,
            "scan_healthy": scan_healthy,
            "scan_frames_baseline": len(baseline),
            "scan_frames_post": len(post),
            "baseline_latest_scan": baseline_latest,
            "post_latest_scan": latest_post,
            "delta": delta,
            "thresholds": thresholds,
            "command_integration_odom_delta_m": odom_delta,
            "odom_source": "ROS-side command integration; not measured wheel odometry",
            "battery_samples": self.battery_samples[-10:],
            "imu_sample_count": self.imu_samples,
            "physical_motion_lidar_delta_proven": lidar_delta_proven,
            "delivery_success": False,
            "failure_reason": None
            if lidar_delta_proven
            else ("safety_precheck_failed" if not safe_precheck else "scan_delta_below_conservative_threshold"),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--linear-x", type=float, default=0.03)
    parser.add_argument("--pulse-s", type=float, default=0.22)
    parser.add_argument("--baseline-s", type=float, default=2.0)
    parser.add_argument("--post-s", type=float, default=2.5)
    parser.add_argument("--min-baseline-frames", type=int, default=3)
    parser.add_argument("--min-ranges", type=int, default=80)
    parser.add_argument("--min-finite", type=int, default=80)
    parser.add_argument("--min-angle-span-deg", type=float, default=90.0)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rclpy.init()
    node = MotionDeltaProbe(args)
    try:
        summary = node.run()
    finally:
        # 异常路径也发零速；真实停机结果以 summary 或外层清场命令为准。
        try:
            node.publish_zero()
            node.call_stop(timeout_s=1.0)
        finally:
            node.destroy_node()
            rclpy.shutdown()

    (output_dir / "lidar_motion_delta_retry_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "scan_frame_stats.jsonl").open("w", encoding="utf-8") as handle:
        for record in node.scan_stats:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    with (output_dir / "scan_delta_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "value"])
        writer.writeheader()
        for key, value in summary["delta"].items():
            if key != "sample_diffs":
                writer.writerow({"metric": key, "value": value})

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
