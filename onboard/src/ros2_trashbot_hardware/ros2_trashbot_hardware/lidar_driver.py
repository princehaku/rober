"""ROS2 LiDAR driver/parser entrypoint for software proof."""

from __future__ import annotations

from typing import Any

from .lidar_packets import find_packets, make_mock_packet, packet_from_hex, parse_packet


def parse_bool(value: Any) -> bool:
    """Accept ROS launch style bool strings without requiring rclpy in tests."""

    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def packets_from_mock_config(mock_scan: Any, mock_packets: str) -> list[bytes]:
    """Return configured mock packets for software-only validation."""

    packets: list[bytes] = []
    if parse_bool(mock_scan):
        # 内置 mock 包用于无串口环境验证 LaserScan 转换链路。
        packets.append(make_mock_packet())
    for text in str(mock_packets or "").split("|"):
        if text.strip():
            packets.append(packet_from_hex(text))
    return packets


def scan_dict_from_packet(packet: bytes, *, frame_id: str = "laser_frame") -> dict[str, Any]:
    """Convert one packet to a LaserScan-shaped dict for tests and ROS adapter."""

    points = parse_packet(packet)
    angle_min = points[0].angle_rad if points else 0.0
    angle_max = points[-1].angle_rad if points else 0.0
    angle_increment = (angle_max - angle_min) / float(len(points) - 1) if len(points) > 1 else 0.0
    return {
        "frame_id": frame_id,
        "angle_min": angle_min,
        "angle_max": angle_max,
        "angle_increment": angle_increment,
        "time_increment": 0.0001,
        "scan_time": 0.1,
        "range_min": 0.05,
        "range_max": 8.0,
        "ranges": [point.distance_m for point in points],
        "intensities": [float(point.intensity) for point in points],
    }


def extract_packets_from_chunks(chunks: list[bytes]) -> list[bytes]:
    """Small helper used by tests to prove serial stream re-sync behavior."""

    packets: list[bytes] = []
    buffer = b""
    for chunk in chunks:
        buffer += chunk
        complete, buffer = find_packets(buffer)
        packets.extend(complete)
    return packets


def main() -> None:
    """Runtime entrypoint kept fail-fast until real ROS2 launch supplies rclpy."""

    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import LaserScan

    class _Node(Node):
        def __init__(self) -> None:
            super().__init__("lidar_driver")
            # 当前 runtime 骨架只支持 mock_scan，真实串口仍需 HIL 前置确认。
            self.declare_parameter("mock_scan", True)
            self.pub = self.create_publisher(LaserScan, "/scan", 10)
            self.timer = self.create_timer(0.1, self._tick)

        def _tick(self) -> None:
            scan_dict = scan_dict_from_packet(make_mock_packet())
            msg = LaserScan()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = scan_dict["frame_id"]
            msg.angle_min = scan_dict["angle_min"]
            msg.angle_max = scan_dict["angle_max"]
            msg.angle_increment = scan_dict["angle_increment"]
            msg.time_increment = scan_dict["time_increment"]
            msg.scan_time = scan_dict["scan_time"]
            msg.range_min = scan_dict["range_min"]
            msg.range_max = scan_dict["range_max"]
            msg.ranges = scan_dict["ranges"]
            msg.intensities = scan_dict["intensities"]
            self.pub.publish(msg)

    rclpy.init()
    node = _Node()
    rclpy.spin(node)
