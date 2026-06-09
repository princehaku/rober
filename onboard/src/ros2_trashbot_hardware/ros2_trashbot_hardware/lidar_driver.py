"""ROS2 LiDAR 驱动入口，覆盖软件验证和真实串口运行路径。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .lidar_packets import find_packets, make_mock_packet, packet_from_hex, parse_packet


LIDAR_START_COMMAND = b"\xA5\x60"
LIDAR_STOP_COMMAND = b"\xA5\x00\xA5\x65\xA5\x65"


@dataclass(frozen=True)
class LidarRuntimeConfig:
    """运行参数独立于 rclpy，便于 fake serial 单测锁定硬件边界。"""

    serial_port: str = "/dev/ttyACM0"
    serial_baudrate: int = 150000
    frame_id: str = "laser_frame"
    scan_topic: str = "/scan"
    raw_packet_topic: str = "/lidar/raw_packet"
    publish_raw_packets: bool = False
    range_min: float = 0.05
    range_max: float = 8.0
    scan_time: float = 0.1
    time_increment: float = 0.0001
    mock_packets: str = ""
    mock_scan: bool = False
    read_size: int = 1024


def parse_bool(value: Any) -> bool:
    """解析 ROS launch 常见 bool 字符串，避免单测依赖 rclpy。"""

    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def packets_from_mock_config(mock_scan: Any, mock_packets: str) -> list[bytes]:
    """返回软件验证用 mock packet；该路径不能触碰真实串口。"""

    packets: list[bytes] = []
    if parse_bool(mock_scan):
        # 内置 mock 包用于无串口环境验证 LaserScan 转换链路。
        packets.append(make_mock_packet())
    for text in str(mock_packets or "").split("|"):
        if text.strip():
            packets.append(packet_from_hex(text))
    return packets


def uses_real_serial(config: LidarRuntimeConfig) -> bool:
    """只有两个 mock 入口都关闭时，才允许进入真实串口模式。"""

    # mock_scan 是 CI / 无硬件开发的主路径，必须保证它不会碰真实串口。
    if parse_bool(config.mock_scan):
        return False
    # mock_packets 允许回放捕获包；此时也不能打开串口，避免测试环境误控硬件。
    return not str(config.mock_packets or "").strip()


class LidarSerialSession:
    """集中管理 LiDAR 启停字节、串口句柄和 packet 重同步。"""

    def __init__(self, config: LidarRuntimeConfig, serial_factory: Any | None = None) -> None:
        self.config = config
        self._serial_factory = serial_factory
        self._serial: Any | None = None
        self._buffer = b""

    def open(self) -> None:
        """打开串口并发送 vendor 启动命令 A5 60。"""

        # pyserial 只在真实串口模式才导入，保证纯软件单测不需要安装依赖。
        factory = self._serial_factory
        if factory is None:
            import serial  # type: ignore[import-not-found]

            factory = serial.Serial
        # timeout 设短超时，避免 timer 回调在没有新包时长期阻塞 ROS executor。
        serial_obj = factory(
            port=self.config.serial_port,
            baudrate=int(self.config.serial_baudrate),
            timeout=0.02,
        )
        try:
            # 用户已用手动 Python 证明 A5 60 可让 STC USB Serial LiDAR 电机启动。
            serial_obj.write(LIDAR_START_COMMAND)
        except Exception:
            # 启动写入失败时立即释放句柄，避免半开串口阻塞下一轮排查。
            try:
                serial_obj.close()
            finally:
                self._serial = None
            raise
        self._serial = serial_obj

    def read_packets(self) -> list[bytes]:
        """读取当前可用 bytes，并返回完整 LiDAR packets。"""

        if self._serial is None:
            return []
        # read_size 保持可配置，后续真机调参时不需要改解析逻辑。
        chunk = self._serial.read(int(self.config.read_size)) or b""
        if not chunk:
            return []
        self._buffer += bytes(chunk)
        packets, self._buffer = find_packets(self._buffer)
        return packets

    def close(self) -> None:
        """生命周期退出时 best-effort 停止电机并关闭串口。"""

        if self._serial is None:
            return
        serial_obj = self._serial
        self._serial = None
        try:
            # vendor ROS2 参考退出时连续发送停止相关命令，先尽力让电机停转。
            serial_obj.write(LIDAR_STOP_COMMAND)
        except Exception:
            # 停止命令失败不能阻止 close；真实物理停转仍需 HIL 观察补证。
            pass
        finally:
            try:
                serial_obj.close()
            except Exception:
                # close 失败不应让 rclpy shutdown 卡住，风险在 sprint 文档中保留。
                pass


def scan_dict_from_packet(
    packet: bytes,
    *,
    frame_id: str = "laser_frame",
    range_min: float = 0.05,
    range_max: float = 8.0,
    scan_time: float = 0.1,
    time_increment: float = 0.0001,
) -> dict[str, Any]:
    """把一个完整 packet 转成 LaserScan 形状的字典供测试和 ROS adapter 使用。"""

    points = parse_packet(packet)
    angle_min = points[0].angle_rad if points else 0.0
    angle_max = points[-1].angle_rad if points else 0.0
    angle_increment = (angle_max - angle_min) / float(len(points) - 1) if len(points) > 1 else 0.0
    return {
        "frame_id": frame_id,
        "angle_min": angle_min,
        "angle_max": angle_max,
        "angle_increment": angle_increment,
        "time_increment": time_increment,
        "scan_time": scan_time,
        "range_min": range_min,
        "range_max": range_max,
        "ranges": [point.distance_m for point in points],
        "intensities": [float(point.intensity) for point in points],
    }


def extract_packets_from_chunks(chunks: list[bytes]) -> list[bytes]:
    """测试辅助函数，用于证明串口分片输入可以重同步成完整 packet。"""

    packets: list[bytes] = []
    buffer = b""
    for chunk in chunks:
        buffer += chunk
        complete, buffer = find_packets(buffer)
        packets.extend(complete)
    return packets


def main() -> None:
    """mock packet 和真实串口 LiDAR 的 ROS2 runtime 入口。"""

    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import LaserScan
    from std_msgs.msg import UInt8MultiArray

    class _Node(Node):
        def __init__(self) -> None:
            super().__init__("lidar_driver")
            self._declare_parameters()
            self.config = self._read_config()
            self.mock_packets = packets_from_mock_config(
                self.config.mock_scan,
                self.config.mock_packets,
            )
            self.mock_packet_index = 0
            self.serial_session: LidarSerialSession | None = None
            self.scan_pub = self.create_publisher(LaserScan, self.config.scan_topic, 10)
            self.raw_pub = None
            if self.config.publish_raw_packets:
                self.raw_pub = self.create_publisher(UInt8MultiArray, self.config.raw_packet_topic, 10)
            if uses_real_serial(self.config):
                self.serial_session = LidarSerialSession(self.config)
                self.serial_session.open()
                self.get_logger().info(
                    f"LiDAR serial started: {self.config.serial_port} @ {self.config.serial_baudrate}"
                )
            else:
                # mock 模式必须显式留痕，防止把软件包回放误读成真实雷达闭环。
                self.get_logger().info(f"LiDAR mock mode active: packets={len(self.mock_packets)}")
            self.timer = self.create_timer(0.02, self._tick)

        def _declare_parameters(self) -> None:
            # 参数名与 bringup/learn launch 对齐，避免两套入口产生漂移。
            self.declare_parameter("serial_port", "/dev/ttyACM0")
            self.declare_parameter("serial_baudrate", 150000)
            self.declare_parameter("frame_id", "laser_frame")
            self.declare_parameter("scan_topic", "/scan")
            self.declare_parameter("raw_packet_topic", "/lidar/raw_packet")
            self.declare_parameter("publish_raw_packets", False)
            self.declare_parameter("range_min", 0.05)
            self.declare_parameter("range_max", 8.0)
            self.declare_parameter("scan_time", 0.1)
            self.declare_parameter("time_increment", 0.0001)
            self.declare_parameter("mock_packets", "")
            self.declare_parameter("mock_scan", False)

        def _param(self, name: str) -> Any:
            # rclpy Parameter 在不同测试/运行路径里统一从 value 取真实值。
            return self.get_parameter(name).value

        def _read_config(self) -> LidarRuntimeConfig:
            return LidarRuntimeConfig(
                serial_port=str(self._param("serial_port")),
                serial_baudrate=int(self._param("serial_baudrate")),
                frame_id=str(self._param("frame_id")),
                scan_topic=str(self._param("scan_topic")),
                raw_packet_topic=str(self._param("raw_packet_topic")),
                publish_raw_packets=parse_bool(self._param("publish_raw_packets")),
                range_min=float(self._param("range_min")),
                range_max=float(self._param("range_max")),
                scan_time=float(self._param("scan_time")),
                time_increment=float(self._param("time_increment")),
                mock_packets=str(self._param("mock_packets")),
                mock_scan=parse_bool(self._param("mock_scan")),
            )

        def _tick(self) -> None:
            packets = self._next_packets()
            for packet in packets:
                self._publish_packet(packet)

        def _next_packets(self) -> list[bytes]:
            if self.mock_packets:
                # 每个 tick 发布一个 mock packet，保持软件验证链路持续有 /scan。
                packet = self.mock_packets[self.mock_packet_index % len(self.mock_packets)]
                self.mock_packet_index += 1
                return [packet]
            if self.serial_session is None:
                return []
            return self.serial_session.read_packets()

        def _publish_packet(self, packet: bytes) -> None:
            if self.raw_pub is not None:
                raw_msg = UInt8MultiArray()
                raw_msg.data = list(packet)
                self.raw_pub.publish(raw_msg)
            scan_dict = scan_dict_from_packet(
                packet,
                frame_id=self.config.frame_id,
                range_min=self.config.range_min,
                range_max=self.config.range_max,
                scan_time=self.config.scan_time,
                time_increment=self.config.time_increment,
            )
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
            self.scan_pub.publish(msg)

        def destroy_node(self) -> bool:
            # destroy_node 是 rclpy 正常生命周期出口，在这里集中释放真实串口。
            if self.serial_session is not None:
                self.serial_session.close()
            return super().destroy_node()

    rclpy.init()
    node = _Node()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
