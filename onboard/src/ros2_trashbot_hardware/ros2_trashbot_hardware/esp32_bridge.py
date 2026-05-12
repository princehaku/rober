"""
Waveshare WAVE ROVER JSON serial bridge.

Protocol source:
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h

The official ESP32 firmware expects one UTF-8 JSON object per UART line.
"""

import json
import math
import threading
import time
from typing import Any, Optional

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, Imu
from std_srvs.srv import Trigger
import serial


CMD_SPEED_CTRL = 1
CMD_ROS_CTRL = 13
CMD_BASE_FEEDBACK_FLOW = 131
CMD_FEEDBACK_FLOW_INTERVAL = 142
CMD_UART_ECHO_MODE = 143
FEEDBACK_BASE_INFO = 1001
VALID_COMMAND_MODES = ("speed", "ros")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _round_float(value: float) -> float:
    return round(float(value), 6)


def vendor_degrees_to_ros_radians(value: float) -> float:
    """Convert WAVE ROVER IMU angle feedback from degrees to ROS radians.

    Vendor source: docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/IMU.cpp
    computes Euler angles with a 57.3 multiplier before publishing r/p/y.
    """
    return math.radians(float(value))


def encode_json_command(command: dict[str, Any]) -> bytes:
    """Encode one vendor JSON command as a newline-delimited UART frame."""
    return (json.dumps(command, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def build_cmd_vel_command(
    linear_x: float,
    angular_z: float,
    command_mode: str,
    track_width_m: float,
    max_wheel_speed_mps: float,
) -> dict[str, Any]:
    """Convert ROS cmd_vel to a WAVE ROVER JSON command.

    Default speed mode uses T=1 because docs/vendor/VENDOR_INDEX.md says T=13
    should only be preferred after hardware validation on this chassis.
    """
    mode = command_mode.lower()
    linear_x = float(linear_x)
    angular_z = float(angular_z)
    if not math.isfinite(linear_x) or not math.isfinite(angular_z):
        raise ValueError("cmd_vel values must be finite")

    if mode == "ros":
        return {"T": CMD_ROS_CTRL, "X": _round_float(linear_x), "Z": _round_float(angular_z)}

    if mode != "speed":
        raise ValueError(f"Unsupported command_mode: {command_mode}")

    if track_width_m <= 0:
        raise ValueError("track_width_m must be > 0")

    if max_wheel_speed_mps <= 0:
        raise ValueError("max_wheel_speed_mps must be > 0")

    left_mps = linear_x - angular_z * track_width_m / 2.0
    right_mps = linear_x + angular_z * track_width_m / 2.0
    left = _clamp(left_mps / max_wheel_speed_mps, -1.0, 1.0)
    right = _clamp(right_mps / max_wheel_speed_mps, -1.0, 1.0)
    return {"T": CMD_SPEED_CTRL, "L": _round_float(left), "R": _round_float(right)}


def validate_startup_config(
    command_mode: str,
    track_width_m: float,
    max_wheel_speed_mps: float,
    feedback_interval_ms: int,
    odom_publish_hz: float,
) -> None:
    """Validate driver params before opening the UART or moving the base."""
    if command_mode.lower() not in VALID_COMMAND_MODES:
        raise ValueError(f"command_mode must be one of {VALID_COMMAND_MODES}")
    if track_width_m <= 0:
        raise ValueError("track_width_m must be > 0")
    if max_wheel_speed_mps <= 0:
        raise ValueError("max_wheel_speed_mps must be > 0")
    if feedback_interval_ms < 0:
        raise ValueError("feedback_interval_ms must be >= 0")
    if odom_publish_hz <= 0:
        raise ValueError("odom_publish_hz must be > 0")


def build_startup_config_commands(feedback_interval_ms: int) -> list[dict[str, int]]:
    """Build vendor UART startup commands.

    Vendor source: docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
    defines T=143 echo mode, T=142 feedback interval, and T=131 feedback flow.
    """
    return [
        {"T": CMD_UART_ECHO_MODE, "cmd": 0},
        {"T": CMD_FEEDBACK_FLOW_INTERVAL, "cmd": int(feedback_interval_ms)},
        {"T": CMD_BASE_FEEDBACK_FLOW, "cmd": 1},
    ]


def parse_feedback_line(line: bytes | str) -> Optional[dict[str, float]]:
    """Parse WAVE ROVER T=1001 base feedback, ignoring unrelated UART lines."""
    try:
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        data = json.loads(line.strip())
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return None

    if data.get("T") != FEEDBACK_BASE_INFO:
        return None

    required = ("L", "R", "r", "p", "y", "v")
    if not all(key in data for key in required):
        return None

    try:
        feedback = {
            "left_speed": float(data["L"]),
            "right_speed": float(data["R"]),
            "roll": float(data["r"]),
            "pitch": float(data["p"]),
            "yaw": float(data["y"]),
            "voltage": float(data["v"]),
        }
    except (TypeError, ValueError):
        return None

    if not all(math.isfinite(value) for value in feedback.values()):
        return None

    return feedback


class ESP32Bridge(Node):
    """Bridge ROS2 topics/services to the official WAVE ROVER ESP32 firmware."""

    def __init__(self):
        super().__init__("esp32_bridge")

        self.declare_parameter("serial_port", "/dev/ttyUSB0")
        self.declare_parameter("serial_baudrate", 115200)
        self.declare_parameter("port", "")
        self.declare_parameter("baudrate", 0)
        self.declare_parameter("command_mode", "speed")
        self.declare_parameter("track_width_m", 0.172)
        self.declare_parameter("max_wheel_speed_mps", 1.3)
        self.declare_parameter("feedback_interval_ms", 100)
        self.declare_parameter("odom_publish_hz", 20.0)

        canonical_port = str(self.get_parameter("serial_port").value)
        alias_port = str(self.get_parameter("port").value)
        canonical_baudrate = int(self.get_parameter("serial_baudrate").value)
        alias_baudrate = int(self.get_parameter("baudrate").value)

        self.port = alias_port or canonical_port
        self.baudrate = alias_baudrate or canonical_baudrate
        self.command_mode = str(self.get_parameter("command_mode").value).lower()
        self.track_width_m = float(self.get_parameter("track_width_m").value)
        self.max_wheel_speed_mps = float(self.get_parameter("max_wheel_speed_mps").value)
        self.feedback_interval_ms = int(self.get_parameter("feedback_interval_ms").value)
        odom_publish_hz = float(self.get_parameter("odom_publish_hz").value)
        validate_startup_config(
            self.command_mode,
            self.track_width_m,
            self.max_wheel_speed_mps,
            self.feedback_interval_ms,
            odom_publish_hz,
        )

        self._serial_lock = threading.Lock()
        self._running = True
        self._last_send_time = 0.0
        self._last_cmd_linear = 0.0
        self._last_cmd_angular = 0.0
        self._odom_x = 0.0
        self._odom_y = 0.0
        self._odom_theta = 0.0
        self._last_odom_time = self.get_clock().now()

        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=0.1)
            self.get_logger().info(f"Connected to WAVE ROVER ESP32 on {self.port} @ {self.baudrate}")
        except serial.SerialException as exc:
            self.get_logger().fatal(f"Cannot open serial port {self.port}: {exc}")
            raise

        self.odom_pub = self.create_publisher(Odometry, "/odom", 10)
        self.imu_pub = self.create_publisher(Imu, "/imu/data", 10)
        self.battery_pub = self.create_publisher(BatteryState, "/battery", 10)

        self.cmd_vel_sub = self.create_subscription(Twist, "/cmd_vel", self._cmd_vel_callback, 10)

        self.stop_srv = self.create_service(Trigger, "/trashbot/stop", self._stop_callback)
        self.reset_odom_srv = self.create_service(
            Trigger, "/trashbot/reset_odom", self._reset_odom_callback
        )
        self.beep_srv = self.create_service(Trigger, "/trashbot/beep", self._beep_callback)

        self._reader_thread = threading.Thread(target=self._serial_reader, daemon=True)
        self._reader_thread.start()

        self._configure_vendor_feedback()
        self.odom_timer = self.create_timer(1.0 / odom_publish_hz, self._publish_odom)

        if alias_port:
            self.get_logger().warn("Parameter 'port' is deprecated; use 'serial_port'")
        if alias_baudrate:
            self.get_logger().warn("Parameter 'baudrate' is deprecated; use 'serial_baudrate'")
        self.get_logger().info(
            "ESP32Bridge ready: vendor WAVE ROVER UART protocol is one UTF-8 JSON "
            "object per newline; "
            f"command_mode={self.command_mode}; "
            "odom source=ROS-side command integration until measured wheel odometry is validated"
        )

    def _configure_vendor_feedback(self):
        for command in build_startup_config_commands(self.feedback_interval_ms):
            self._send_json(command)

    def _send_json(self, command: dict[str, Any]) -> bool:
        try:
            frame = encode_json_command(command)
            with self._serial_lock:
                if not self.serial.is_open:
                    return False
                self.serial.write(frame)
            self._last_send_time = time.time()
            return True
        except (serial.SerialException, OSError) as exc:
            self.get_logger().error(f"Serial write error: {exc}")
            return False

    def _serial_reader(self):
        while self._running:
            try:
                line = self.serial.readline()
                if not line:
                    continue
                feedback = parse_feedback_line(line)
                if feedback is not None:
                    self._publish_feedback(feedback)
            except Exception as exc:
                if self._running:
                    self.get_logger().error(f"Serial read error: {exc}")
                time.sleep(0.1)

    def _publish_feedback(self, feedback: dict[str, float]):
        now = self.get_clock().now().to_msg()

        imu = Imu()
        imu.header.stamp = now
        imu.header.frame_id = "imu_link"
        yaw = vendor_degrees_to_ros_radians(feedback["yaw"])
        imu.orientation.z = math.sin(yaw / 2.0)
        imu.orientation.w = math.cos(yaw / 2.0)
        self.imu_pub.publish(imu)

        battery = BatteryState()
        battery.header.stamp = now
        battery.voltage = feedback["voltage"]
        battery.present = True
        self.battery_pub.publish(battery)

    def _cmd_vel_callback(self, msg: Twist):
        try:
            command = build_cmd_vel_command(
                linear_x=msg.linear.x,
                angular_z=msg.angular.z,
                command_mode=self.command_mode,
                track_width_m=self.track_width_m,
                max_wheel_speed_mps=self.max_wheel_speed_mps,
            )
        except ValueError as exc:
            self.get_logger().error(str(exc))
            return

        if self._send_json(command):
            self._last_cmd_linear = float(msg.linear.x)
            self._last_cmd_angular = float(msg.angular.z)
        else:
            self.get_logger().warn("Failed to forward /cmd_vel to WAVE ROVER ESP32")

    def _publish_odom(self):
        # Temporary dead-reckoning from commanded velocity. The vendor T=1001
        # feedback reports wheel speed but not a complete odometry pose.
        now = self.get_clock().now()
        dt = (now - self._last_odom_time).nanoseconds / 1e9
        self._last_odom_time = now
        if dt <= 0:
            return

        self._odom_theta += self._last_cmd_angular * dt
        self._odom_x += self._last_cmd_linear * math.cos(self._odom_theta) * dt
        self._odom_y += self._last_cmd_linear * math.sin(self._odom_theta) * dt

        msg = Odometry()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = "odom"
        msg.child_frame_id = "base_link"
        msg.pose.pose.position.x = self._odom_x
        msg.pose.pose.position.y = self._odom_y
        msg.pose.pose.position.z = 0.0
        msg.pose.pose.orientation.z = math.sin(self._odom_theta / 2.0)
        msg.pose.pose.orientation.w = math.cos(self._odom_theta / 2.0)
        msg.twist.twist.linear.x = self._last_cmd_linear
        msg.twist.twist.angular.z = self._last_cmd_angular
        self.odom_pub.publish(msg)

    def _send_stop(self) -> bool:
        return self._send_json({"T": CMD_SPEED_CTRL, "L": 0, "R": 0})

    def _stop_callback(self, request, response):
        response.success = self._send_stop()
        response.message = "Motors stopped" if response.success else "Failed to send stop command"
        return response

    def _reset_odom_callback(self, request, response):
        self._odom_x = 0.0
        self._odom_y = 0.0
        self._odom_theta = 0.0
        self._last_odom_time = self.get_clock().now()
        response.success = True
        response.message = "ROS-side odometry reset; no vendor ESP32 reset command sent"
        return response

    def _beep_callback(self, request, response):
        response.success = False
        response.message = "Beep is not supported by the WAVE ROVER JSON base protocol"
        return response

    def destroy_node(self):
        self._running = False
        self._send_stop()
        if hasattr(self, "serial") and self.serial.is_open:
            self.serial.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ESP32Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
