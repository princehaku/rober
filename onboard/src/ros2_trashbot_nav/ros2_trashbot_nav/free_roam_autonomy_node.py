"""扫地式自由建图 ROS2 接线节点。

节点负责把 /scan、/map、现场确认参数和 stop fallback 转成
FreeRoamAutonomyController 的输入输出。默认只写 artifact 和调用停止兜底，
不会发布 /cmd_vel；只有显式打开 enable_cmd_vel_publish 与 motion_hil_unlocked
两个参数后才会发布受限 Twist。
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import asdict
from typing import Any, Iterable

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_srvs.srv import Trigger

from ros2_trashbot_nav.free_roam_autonomy import (
    FreeRoamAutonomyController,
    FreeRoamConfig,
    FreeRoamDecision,
    FreeRoamSnapshot,
)


def finite_scan_min_distance(ranges: Iterable[Any]) -> float | None:
    """只接受有限正数雷达距离，避免 inf/nan/字符串让避障误判为安全。"""
    finite_values: list[float] = []
    for value in ranges:
        try:
            distance = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(distance) and distance > 0.0:
            finite_values.append(distance)
    return min(finite_values) if finite_values else None


def occupancy_grid_metrics(data: Iterable[Any]) -> dict[str, float | int | None]:
    """统计 free/unknown/occupied，让策略知道地图覆盖是否真的增长。"""
    free_cells = 0
    unknown_cells = 0
    occupied_cells = 0
    total_cells = 0
    for value in data:
        try:
            cell = int(value)
        except (TypeError, ValueError):
            continue
        total_cells += 1
        if cell == -1:
            unknown_cells += 1
        elif cell == 0:
            free_cells += 1
        elif cell > 0:
            occupied_cells += 1
    unknown_ratio = None if total_cells == 0 else unknown_cells / total_cells
    return {
        "free_cells": free_cells,
        "unknown_cells": unknown_cells,
        "occupied_cells": occupied_cells,
        "total_cells": total_cells,
        "unknown_ratio": unknown_ratio,
    }


def twist_from_decision(decision: FreeRoamDecision) -> Twist:
    """把策略速度转成 Twist；零速 decision 仍会显式输出零速 Twist。"""
    twist = Twist()
    twist.linear.x = float(decision.linear_x_mps)
    twist.angular.z = float(decision.angular_z_radps)
    return twist


class FreeRoamAutonomyNode(Node):
    """上车端自由扫图节点，默认 artifact-only，运动发布必须显式双重解锁。"""

    def __init__(self) -> None:
        super().__init__("free_roam_autonomy")
        self._declare_parameters()

        config = FreeRoamConfig(
            max_speed_mps=float(self.get_parameter("max_speed_mps").value),
            turn_speed_radps=float(self.get_parameter("turn_speed_radps").value),
            obstacle_stop_distance_m=float(self.get_parameter("obstacle_stop_distance_m").value),
            lidar_fresh_timeout_s=float(self.get_parameter("lidar_fresh_timeout_s").value),
            max_runtime_s=float(self.get_parameter("max_runtime_s").value),
            coverage_stall_timeout_s=float(self.get_parameter("coverage_stall_timeout_s").value),
            target_unknown_ratio=float(self.get_parameter("target_unknown_ratio").value),
        )
        self.controller = FreeRoamAutonomyController(config)
        self.started_at_s = time.monotonic()
        self.latest_scan_min_distance_m: float | None = None
        self.latest_scan_seen_at_s: float | None = None
        self.latest_map_metrics: dict[str, float | int | None] = occupancy_grid_metrics([])
        self.last_decision: FreeRoamDecision | None = None
        self.stop_request_in_flight = False

        scan_topic = str(self.get_parameter("scan_topic").value)
        map_topic = str(self.get_parameter("map_topic").value)
        cmd_vel_topic = str(self.get_parameter("cmd_vel_topic").value)
        stop_service = str(self.get_parameter("stop_service").value)
        tick_period_s = float(self.get_parameter("tick_period_s").value)

        # 订阅传感器只读事实；节点初始化本身不启动雷达、不启动建图。
        self.create_subscription(LaserScan, scan_topic, self._on_scan, 10)
        self.create_subscription(OccupancyGrid, map_topic, self._on_map, 10)

        # 发布器即使创建也不会发布，除非双参数显式解锁。
        self.cmd_vel_pub = self.create_publisher(Twist, cmd_vel_topic, 10)
        self.stop_client = self.create_client(Trigger, stop_service)
        self.create_timer(tick_period_s, self._tick)

        self.get_logger().info(
            "free_roam_autonomy started artifact_only=%s cmd_vel_topic=%s"
            % (not self._motion_publish_unlocked(), cmd_vel_topic)
        )

    def _declare_parameters(self) -> None:
        """集中声明参数，默认值全部偏向锁定和只读 artifact。"""
        self.declare_parameter("scan_topic", "/scan")
        self.declare_parameter("map_topic", "/map")
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("stop_service", "/trashbot/stop")
        self.declare_parameter("artifact_path", "/root/rober/onboard/runtime/free_roam_autonomy_latest.json")
        self.declare_parameter("operator_confirmed", False)
        self.declare_parameter("mapping_active", False)
        self.declare_parameter("stop_available", True)
        self.declare_parameter("external_stop_requested", False)
        self.declare_parameter("enable_stop_service", True)
        self.declare_parameter("enable_cmd_vel_publish", False)
        self.declare_parameter("motion_hil_unlocked", False)
        self.declare_parameter("tick_period_s", 0.5)
        self.declare_parameter("max_speed_mps", 0.12)
        self.declare_parameter("turn_speed_radps", 0.35)
        self.declare_parameter("obstacle_stop_distance_m", 0.45)
        self.declare_parameter("lidar_fresh_timeout_s", 1.5)
        self.declare_parameter("max_runtime_s", 60.0)
        self.declare_parameter("coverage_stall_timeout_s", 4.0)
        self.declare_parameter("target_unknown_ratio", 0.18)

    def _on_scan(self, msg: LaserScan) -> None:
        """记录最新雷达距离和本机接收时间，策略用接收年龄判断 WYSIWYG。"""
        self.latest_scan_min_distance_m = finite_scan_min_distance(msg.ranges)
        self.latest_scan_seen_at_s = time.monotonic()

    def _on_map(self, msg: OccupancyGrid) -> None:
        """记录地图覆盖指标；不保存地图、不改 map_server 状态。"""
        self.latest_map_metrics = occupancy_grid_metrics(msg.data)

    def _tick(self) -> None:
        """每个 tick 做一次策略决策、artifact 写入和必要的停止兜底。"""
        now_s = time.monotonic()
        snapshot = self._build_snapshot(now_s)
        decision = self.controller.update(snapshot)
        self.last_decision = decision

        if decision.stop_required:
            self._request_stop_once()
        self._publish_motion_if_unlocked(decision)
        self._write_artifact(snapshot, decision, now_s)

    def _build_snapshot(self, now_s: float) -> FreeRoamSnapshot:
        """把 ROS2 读数转换成策略输入，缺实时雷达时让策略锁住。"""
        lidar_age_s = None
        if self.latest_scan_seen_at_s is not None:
            lidar_age_s = max(0.0, now_s - self.latest_scan_seen_at_s)
        return FreeRoamSnapshot(
            operator_confirmed=bool(self.get_parameter("operator_confirmed").value),
            mapping_active=bool(self.get_parameter("mapping_active").value),
            stop_available=bool(self.get_parameter("stop_available").value),
            lidar_min_distance_m=self.latest_scan_min_distance_m,
            lidar_age_s=lidar_age_s,
            map_free_cells=self._metric_int("free_cells"),
            map_unknown_ratio=self._metric_float("unknown_ratio"),
            elapsed_s=max(0.0, now_s - self.started_at_s),
            external_stop_requested=bool(self.get_parameter("external_stop_requested").value),
            now_s=now_s,
        )

    def _metric_int(self, key: str) -> int | None:
        """地图指标可能为空，空值不能进入策略覆盖判断。"""
        value = self.latest_map_metrics.get(key)
        return int(value) if isinstance(value, int) else None

    def _metric_float(self, key: str) -> float | None:
        """unknown ratio 为空时交给策略继续依据安全门禁判断。"""
        value = self.latest_map_metrics.get(key)
        return float(value) if isinstance(value, (float, int)) else None

    def _request_stop_once(self) -> None:
        """需要停止时调用上车 stop 服务；未就绪时也不会阻塞 artifact 写入。"""
        if not bool(self.get_parameter("enable_stop_service").value):
            return
        if self.stop_request_in_flight:
            return
        if not self.stop_client.service_is_ready():
            return
        self.stop_request_in_flight = True
        future = self.stop_client.call_async(Trigger.Request())
        future.add_done_callback(lambda _future: self._clear_stop_request())

    def _clear_stop_request(self) -> None:
        """stop future 完成后允许下一次 stop_required 再次兜底。"""
        self.stop_request_in_flight = False

    def _publish_motion_if_unlocked(self, decision: FreeRoamDecision) -> None:
        """运动发布必须双重解锁；默认不会发布任何 /cmd_vel。"""
        if not self._motion_publish_unlocked():
            return
        self.cmd_vel_pub.publish(twist_from_decision(decision))

    def _motion_publish_unlocked(self) -> bool:
        """避免单个误配参数打开运动，必须显式同时打开 HIL 与发布开关。"""
        return (
            bool(self.get_parameter("enable_cmd_vel_publish").value)
            and bool(self.get_parameter("motion_hil_unlocked").value)
        )

    def _write_artifact(self, snapshot: FreeRoamSnapshot, decision: FreeRoamDecision, now_s: float) -> None:
        """写出最近一次状态，供上位机 summary 和现场验收读取。"""
        artifact_path = os.path.expanduser(str(self.get_parameter("artifact_path").value))
        payload = {
            "schema": "trashbot.free_roam_autonomy.runtime.v1",
            "observed_at_s": round(now_s, 4),
            "artifact_only": not self._motion_publish_unlocked(),
            "cmd_vel_publish_enabled": self._motion_publish_unlocked(),
            "snapshot": asdict(snapshot),
            "map_metrics": dict(self.latest_map_metrics),
            "decision": decision.to_dict(),
        }
        os.makedirs(os.path.dirname(artifact_path) or ".", exist_ok=True)
        with open(artifact_path, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")


def main(args: list[str] | None = None) -> int:
    """ROS2 节点入口；参数默认 artifact-only，不会自动发车。"""
    rclpy.init(args=args)
    node = FreeRoamAutonomyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
