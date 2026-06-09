#!/usr/bin/env python3
# 中文注释：本脚本只服务本轮 micro sprint，不作为长期产品节点安装。
# 中文注释：脚本运行在真实上位机 ROS2 环境中，避免本地 mock 误导结论。
# 中文注释：本轮目标是看 LiDAR scan 是否能独立支持物理运动发生过。
# 中文注释：脚本不读取 encoder 结论，因为上一轮已证明 L/R 仍全零。
# 中文注释：脚本不使用 camera 画面，因为现场画面近黑且会占用无关资源。
# 中文注释：脚本不启动 Nav2，避免把自主导航风险带进短脉冲验证。
# 中文注释：运动命令只通过 `/cmd_vel`，保持与项目 ROS 主链路一致。
# 中文注释：`MAX_LINEAR_X_MPS` 固定为 0.03，低于历史安全上限。
# 中文注释：`MAX_PULSE_DURATION_S` 固定小于 0.25s，避免长时间运动。
# 中文注释：baseline 前先调用 stop，降低上轮残留速度污染结果的风险。
# 中文注释：motion 后立即发布零速，并调用 stop service 做硬边界。
# 中文注释：finally 中再次零速和 stop，覆盖脚本异常退出路径。
# 中文注释：summary 显式写 `safe_to_control=false`，避免被误读成准入。
# 中文注释：summary 显式写 `delivery_success=false`，本轮不是送达验收。
# 中文注释：summary 显式写 wheel feedback 未证明，避免复用错误证据。
# 中文注释：scan frame 只保存摘要，避免把大体量 LaserScan 全量落盘。
# 中文注释：profile 使用固定 bin 采样，便于 before/post 同索引比较。
# 中文注释：profile hash 只作为快速辨识，不作为任何通过条件。
# 中文注释：有限点过滤排除 inf/nan/0，避免空读数影响中位数。
# 中文注释：扇区 median 用于辅助定位变化方向，不单独证明运动。
# 中文注释：前向扇区窗口较窄，降低侧向环境变化误判的概率。
# 中文注释：left/right 扇区可能为空，因此 summary 允许 null。
# 中文注释：阶段 profile 先按帧聚合，再比较 before/post，降低单帧噪声。
# 中文注释：delta 使用绝对差中位数，避免个别异常 bin 放大结论。
# 中文注释：changed_bin_ratio 需要足够比例变化，避免单点跳变误判。
# 中文注释：min_paired_bins 是关键防线，scan 点太少时必须判失败。
# 中文注释：阈值采用保守策略，宁可未证明，也不把噪声写成运动。
# 中文注释：`command_integration_odom_delta_m` 只记录 ROS 积分，不算实测。
# 中文注释：`battery_topic_seen` 只证明 topic 可见，不做电池标定。
# 中文注释：`imu_topic_seen` 只证明 topic 可见，不做 IMU 标定。
# 中文注释：`tf_transform_count` 只证明 TF 有发布，不做机械外参标定。
# 中文注释：脚本不直接操作串口，串口由 esp32_bridge 持有并负责 stop。
# 中文注释：真实串口参数来自本轮远端命令和 vendor 资料，不在脚本猜测。
# 中文注释：脚本输出 schema，便于后续自动校验 artifact 版本。
# 中文注释：JSON 使用 sort_keys，便于 diff 和人工复核。
# 中文注释：CSV 只写核心指标，便于用命令行快速查看阈值。
# 中文注释：JSONL 每行一帧摘要，便于后续追加离线分析。
# 中文注释：本轮 motion phase 也采集 scan，但通过条件只比较 baseline/post。
# 中文注释：motion phase 可辅助判断脉冲窗口是否确实收到 scan。
# 中文注释：stop service timeout 会写入 failure 证据，不会被静默吞掉。
# 中文注释：如果 stop service 不存在，本轮不能视为安全通过。
# 中文注释：如果 scan frame 数不足，本轮不能视为物理运动证明。
# 中文注释：如果 odom 非零但 scan 未变，本轮仍判物理运动未证明。
# 中文注释：如果 scan 有变化但 paired bins 不足，本轮仍判未证明。
# 中文注释：如果只前方单点变化，本轮仍需 changed ratio 达标才通过。
# 中文注释：脚本不修改 ROS 参数、launch 文件或远端长期配置。
# 中文注释：脚本不清理进程；进程清理由外层远端控制脚本负责。
# 中文注释：外层清场必须恢复 upper API，本脚本只负责采样和 stop。
# 中文注释：本脚本输出的 `physical_motion_lidar_delta_proven` 是唯一结论位。
# 中文注释：人工阅读时应优先看 summary，再看 scan_delta_metrics.csv。
# 中文注释：若未来 LiDAR 驱动输出完整 360 scan，可复用相同阈值框架。
# 中文注释：若未来环境变化太大，仍需结合现场视频或轮上标记复核。
# 中文注释：本脚本没有把 `T=13` 纳入路径，继续使用已验证的 speed 模式。
# 中文注释：速度单位来自 ROS `/cmd_vel`，底盘映射由 esp32_bridge 负责。
# 中文注释：脚本内所有安全上限写成常量，防止命令行误传更大值。
# 中文注释：本轮不允许通过参数提高速度或脉冲时间。
# 中文注释：采样时使用 monotonic clock 控制窗口，避免系统时间跳变。
# 中文注释：LaserScan stamp 记录 ROS clock，便于和 ROS 日志对应。
# 中文注释：`time.time()` 只用于 summary 生成时间，不参与运动窗口。
# 中文注释：如果 rclpy shutdown 前异常，finally stop 仍会先尝试执行。
# 中文注释：异常路径仍可能依赖外层 cleanup，因此 tech-done 必须记录清场。
# 中文注释：本文件保留在 sprint tools 中，作为本轮证据可复跑入口。
"""LiDAR motion delta probe for one bounded real-board pulse."""

from __future__ import annotations

import csv
import hashlib
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
from tf2_msgs.msg import TFMessage


MAX_LINEAR_X_MPS = 0.03
MAX_PULSE_DURATION_S = 0.22


def _finite(value: float) -> bool:
    return math.isfinite(value) and value > 0.0


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _quantize(values: list[float | None]) -> list[int]:
    # 中文注释：量化到厘米级，避免把浮点打印抖动当成真实运动证据。
    result: list[int] = []
    for value in values:
        if value is None or not _finite(float(value)):
            result.append(-1)
        else:
            result.append(int(round(float(value) * 100.0)))
    return result


def _hash_profile(profile: list[float | None]) -> str:
    # 中文注释：hash 只用于快速比对 profile，不作为单独通过条件。
    payload = ",".join(str(item) for item in _quantize(profile)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def _sample_profile(ranges: list[float], bins: int = 120) -> list[float | None]:
    # 中文注释：固定 bin 数让不同时间点的 scan 可以按同一空间索引比较。
    if not ranges:
        return []
    chunk = max(1, len(ranges) // bins)
    profile: list[float | None] = []
    for start in range(0, len(ranges), chunk):
        finite_values = [value for value in ranges[start : start + chunk] if _finite(value)]
        profile.append(_median(finite_values))
        if len(profile) >= bins:
            break
    return profile


def _sector_medians(scan: LaserScan) -> dict[str, float | None]:
    # 中文注释：扇区采用角度窗口，便于判断前/左/右是否出现一致变化。
    sectors = {
        "front": (-0.35, 0.35),
        "left": (0.75, 1.45),
        "right": (-1.45, -0.75),
    }
    values: dict[str, list[float]] = {key: [] for key in sectors}
    for index, value in enumerate(scan.ranges):
        angle = scan.angle_min + index * scan.angle_increment
        if not _finite(value):
            continue
        for key, (low, high) in sectors.items():
            if low <= angle <= high:
                values[key].append(float(value))
    return {key: _median(items) for key, items in values.items()}


def _pose_xy(odom: Odometry | None) -> tuple[float, float] | None:
    if odom is None:
        return None
    pos = odom.pose.pose.position
    return float(pos.x), float(pos.y)


def _distance(a: tuple[float, float] | None, b: tuple[float, float] | None) -> float | None:
    if a is None or b is None:
        return None
    return math.hypot(b[0] - a[0], b[1] - a[1])


class ProbeNode(Node):
    def __init__(self, output_dir: Path) -> None:
        super().__init__("lidar_motion_delta_probe")
        self.output_dir = output_dir
        self.phase = "startup"
        self.frames: list[dict[str, Any]] = []
        self.latest_odom: Odometry | None = None
        self.odom_samples: list[tuple[float, float, float, str]] = []
        self.battery_seen = False
        self.imu_seen = False
        self.tf_count = 0
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.stop_client = self.create_client(Trigger, "/trashbot/stop")
        self.create_subscription(LaserScan, "/scan", self.on_scan, 10)
        self.create_subscription(Odometry, "/odom", self.on_odom, 10)
        self.create_subscription(BatteryState, "/battery", self.on_battery, 10)
        self.create_subscription(Imu, "/imu/data", self.on_imu, 10)
        self.create_subscription(TFMessage, "/tf", self.on_tf, 10)

    def on_scan(self, msg: LaserScan) -> None:
        finite_ranges = [float(value) for value in msg.ranges if _finite(value)]
        profile = _sample_profile(list(msg.ranges))
        sectors = _sector_medians(msg)
        stamp = self.get_clock().now().nanoseconds / 1_000_000_000.0
        # 中文注释：每帧只保留摘要和量化 profile，避免 artifacts 过大。
        self.frames.append(
            {
                "stamp_s": stamp,
                "phase": self.phase,
                "finite_count": len(finite_ranges),
                "finite_median": _median(finite_ranges),
                "front_median": sectors["front"],
                "left_median": sectors["left"],
                "right_median": sectors["right"],
                "profile_hash": _hash_profile(profile),
                "profile": profile,
            }
        )

    def on_odom(self, msg: Odometry) -> None:
        self.latest_odom = msg
        xy = _pose_xy(msg)
        if xy is not None:
            self.odom_samples.append((time.time(), xy[0], xy[1], self.phase))

    def on_battery(self, _: BatteryState) -> None:
        self.battery_seen = True

    def on_imu(self, _: Imu) -> None:
        self.imu_seen = True

    def on_tf(self, msg: TFMessage) -> None:
        self.tf_count += len(msg.transforms)

    def spin_for(self, duration_s: float, phase: str) -> None:
        # 中文注释：阶段标签在 spin 前设置，后续 delta 可以区分 before/motion/post。
        self.phase = phase
        deadline = time.monotonic() + duration_s
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)

    def publish_twist(self, linear_x: float) -> None:
        msg = Twist()
        msg.linear.x = float(linear_x)
        self.cmd_pub.publish(msg)

    def call_stop(self, timeout_s: float = 2.0) -> dict[str, Any]:
        # 中文注释：stop service 是本轮安全边界，失败必须进入 summary 风险字段。
        if not self.stop_client.wait_for_service(timeout_sec=timeout_s):
            return {"success": False, "message": "stop service unavailable"}
        future = self.stop_client.call_async(Trigger.Request())
        deadline = time.monotonic() + timeout_s
        while rclpy.ok() and time.monotonic() < deadline and not future.done():
            rclpy.spin_once(self, timeout_sec=0.05)
        if not future.done():
            return {"success": False, "message": "stop service timeout"}
        response = future.result()
        return {"success": bool(response.success), "message": str(response.message)}


def _phase_frames(frames: list[dict[str, Any]], phase: str) -> list[dict[str, Any]]:
    return [frame for frame in frames if frame["phase"] == phase]


def _aggregate_phase(frames: list[dict[str, Any]]) -> dict[str, Any]:
    profiles = [frame["profile"] for frame in frames if frame.get("profile")]
    finite_counts = [int(frame["finite_count"]) for frame in frames]
    # 中文注释：阶段代表 profile 取每个 bin 的中位数，用于抑制单帧噪声。
    if profiles:
        width = min(len(profile) for profile in profiles)
        aggregate_profile = [_median([profile[i] for profile in profiles if profile[i] is not None]) for i in range(width)]
    else:
        aggregate_profile = []
    return {
        "frame_count": len(frames),
        "finite_count_median": _median([float(item) for item in finite_counts]),
        "finite_median": _median([float(frame["finite_median"]) for frame in frames if frame["finite_median"] is not None]),
        "front_median": _median([float(frame["front_median"]) for frame in frames if frame["front_median"] is not None]),
        "left_median": _median([float(frame["left_median"]) for frame in frames if frame["left_median"] is not None]),
        "right_median": _median([float(frame["right_median"]) for frame in frames if frame["right_median"] is not None]),
        "profile_hash": _hash_profile(aggregate_profile),
        "profile": aggregate_profile,
    }


def _delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    p1 = before.get("profile") or []
    p2 = after.get("profile") or []
    pairs = [(float(a), float(b)) for a, b in zip(p1, p2) if a is not None and b is not None]
    diffs = [abs(b - a) for a, b in pairs]
    changed = [diff for diff in diffs if diff >= 0.08]
    sectors: dict[str, float | None] = {}
    for key in ("finite_median", "front_median", "left_median", "right_median"):
        a = before.get(key)
        b = after.get(key)
        sectors[f"{key}_delta_m"] = None if a is None or b is None else float(b) - float(a)
    # 中文注释：通过条件保守设置，需要足够帧数、bin 变化比例和中位差同时满足。
    median_abs = _median(diffs) or 0.0
    changed_ratio = (len(changed) / len(diffs)) if diffs else 0.0
    max_abs = max(diffs) if diffs else 0.0
    proven = len(pairs) >= 40 and median_abs >= 0.04 and changed_ratio >= 0.18
    return {
        "paired_bins": len(pairs),
        "median_abs_diff_m": median_abs,
        "max_abs_diff_m": max_abs,
        "changed_bin_ratio": changed_ratio,
        "sector_delta_m": sectors,
        "physical_motion_lidar_delta_proven": bool(proven),
        "threshold": {
            "min_paired_bins": 40,
            "median_abs_diff_m_gte": 0.04,
            "changed_bin_ratio_gte": 0.18,
            "changed_bin_abs_threshold_m": 0.08,
        },
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _write_csv(path: Path, delta: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        writer.writerow(["median_abs_diff_m", delta["median_abs_diff_m"]])
        writer.writerow(["max_abs_diff_m", delta["max_abs_diff_m"]])
        writer.writerow(["changed_bin_ratio", delta["changed_bin_ratio"]])
        writer.writerow(["paired_bins", delta["paired_bins"]])
        for key, value in delta["sector_delta_m"].items():
            writer.writerow([key, value])


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rclpy.init()
    node = ProbeNode(output_dir)
    try:
        # 中文注释：先停车再采 baseline，避免上轮残留速度污染本轮证据。
        pre_stop = node.call_stop()
        node.spin_for(3.0, "baseline")
        odom_before = _pose_xy(node.latest_odom)
        command_start = time.monotonic()
        node.phase = "motion"
        while time.monotonic() - command_start < MAX_PULSE_DURATION_S:
            node.publish_twist(MAX_LINEAR_X_MPS)
            rclpy.spin_once(node, timeout_sec=0.02)
        pulse_duration = time.monotonic() - command_start
        node.publish_twist(0.0)
        post_stop = node.call_stop()
        node.publish_twist(0.0)
        node.spin_for(4.0, "post")
        odom_after = _pose_xy(node.latest_odom)
    finally:
        # 中文注释：退出前再发一次零速，降低异常路径留下运动命令的风险。
        node.publish_twist(0.0)
        final_stop = node.call_stop()

    baseline = _aggregate_phase(_phase_frames(node.frames, "baseline"))
    motion = _aggregate_phase(_phase_frames(node.frames, "motion"))
    post = _aggregate_phase(_phase_frames(node.frames, "post"))
    scan_delta = _delta(baseline, post)
    command_odom_delta = _distance(odom_before, odom_after)
    failure_reason = None if scan_delta["physical_motion_lidar_delta_proven"] else "scan_delta_below_conservative_threshold"
    summary = {
        "schema": "rober.lidar_motion_delta_probe.v1",
        "generated_at_unix_s": time.time(),
        "vendor_sources": [
            "docs/vendor/VENDOR_INDEX.md",
            "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
            "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
            "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
        ],
        "motion_commands_sent": True,
        "max_pulse_duration_s": pulse_duration,
        "max_linear_x_mps": MAX_LINEAR_X_MPS,
        "pre_stop": pre_stop,
        "post_stop": post_stop,
        "final_stop": final_stop,
        "stop_confirmed": bool(pre_stop.get("success") and post_stop.get("success") and final_stop.get("success")),
        "scan_frames_before": baseline["frame_count"],
        "scan_frames_motion": motion["frame_count"],
        "scan_frames_after": post["frame_count"],
        "scan_phase_summary": {"baseline": baseline, "motion": motion, "post": post},
        "scan_delta_metric": scan_delta,
        "physical_motion_lidar_delta_proven": scan_delta["physical_motion_lidar_delta_proven"],
        "command_integration_odom_delta_m": command_odom_delta,
        "wheel_feedback_lr_nonzero_proven": False,
        "battery_topic_seen": node.battery_seen,
        "imu_topic_seen": node.imu_seen,
        "tf_transform_count": node.tf_count,
        "safe_to_control": False,
        "delivery_success": False,
        "failure_reason": failure_reason,
    }
    summary_path = output_dir / "lidar_motion_delta_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    _write_jsonl(output_dir / "scan_frame_stats.jsonl", node.frames)
    _write_csv(output_dir / "scan_delta_metrics.csv", scan_delta)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
