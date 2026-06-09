"""WAVE ROVER ESP32 bridge 的 ROS2 运行时 glue。

Vendor 来源：
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/IMU.cpp

本模块是唯一打开串口和发布 ROS topic 的层，协议事实由纯函数模块提供。
"""

from __future__ import annotations

import json
import math
import threading
import time
from typing import Any

from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, Imu
from std_srvs.srv import Trigger
import serial
from tf2_ros import TransformBroadcaster

from ros2_trashbot_hardware.bridge_config import declare_bridge_parameters, load_bridge_config
from ros2_trashbot_hardware.wave_rover_feedback import (
    parse_feedback_line,
    vendor_degrees_to_ros_radians,
)
from ros2_trashbot_hardware.wave_rover_protocol import (
    CMD_SPEED_CTRL,
    build_cmd_vel_command,
    build_startup_config_commands,
    encode_json_command,
)


class ESP32Bridge(Node):
    """把 ROS2 topic/service 桥接到官方 WAVE ROVER ESP32 固件。"""

    def __init__(self):
        super().__init__("esp32_bridge")

        declare_bridge_parameters(self)
        config = load_bridge_config(self)

        self.port = config.port
        self.baudrate = config.baudrate
        self.command_mode = config.command_mode
        self.track_width_m = config.track_width_m
        self.max_wheel_speed_mps = config.max_wheel_speed_mps
        self.feedback_interval_ms = config.feedback_interval_ms
        self.publish_odom_tf = config.publish_odom_tf
        self.feedback_debug_log_path = config.feedback_debug_log_path

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
        # TF 与 /odom 必须同源，避免后续集成时出现 topic 与 TF 两套不同的里程计事实。
        self.odom_tf_broadcaster = TransformBroadcaster(self) if self.publish_odom_tf else None

        self.cmd_vel_sub = self.create_subscription(Twist, "/cmd_vel", self._cmd_vel_callback, 10)

        self.stop_srv = self.create_service(Trigger, "/trashbot/stop", self._stop_callback)
        self.reset_odom_srv = self.create_service(
            Trigger, "/trashbot/reset_odom", self._reset_odom_callback
        )
        self.beep_srv = self.create_service(Trigger, "/trashbot/beep", self._beep_callback)

        self._reader_thread = threading.Thread(target=self._serial_reader, daemon=True)
        self._reader_thread.start()

        self._configure_vendor_feedback()
        self.odom_timer = self.create_timer(1.0 / config.odom_publish_hz, self._publish_odom)

        if config.alias_port_used:
            self.get_logger().warn("Parameter 'port' is deprecated; use 'serial_port'")
        if config.alias_baudrate_used:
            self.get_logger().warn("Parameter 'baudrate' is deprecated; use 'serial_baudrate'")
        self.get_logger().info(
            "ESP32Bridge ready: vendor WAVE ROVER UART protocol is one UTF-8 JSON "
            "object per newline; "
            f"command_mode={self.command_mode}; "
            f"publish_odom_tf={self.publish_odom_tf}; "
            f"feedback_debug_log_enabled={bool(self.feedback_debug_log_path)}; "
            "odom source=ROS-side command integration until measured wheel odometry is validated"
        )

    def _configure_vendor_feedback(self) -> None:
        # 厂商 json_cmd.h 定义 T=143/142/131；启动时统一配置，避免节点运行后才临时补帧。
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

    def _serial_reader(self) -> None:
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

    def _publish_feedback(self, feedback: dict[str, float | None]) -> None:
        now = self.get_clock().now().to_msg()

        imu = Imu()
        imu.header.stamp = now
        imu.header.frame_id = "imu_link"
        # 当前只把 vendor y 映射为 yaw；roll/pitch 暂不发布，避免制造未经 HIL 对齐的姿态事实。
        yaw_degrees = feedback["yaw"]
        if yaw_degrees is None:
            # 当真实板子明确回传 yaw unavailable 时，仍发布 IMU 样本，但用 ROS 约定显式声明 orientation 不可用。
            imu.orientation.w = 1.0
            imu.orientation_covariance[0] = -1.0
        else:
            yaw = vendor_degrees_to_ros_radians(yaw_degrees)
            imu.orientation.z = math.sin(yaw / 2.0)
            imu.orientation.w = math.cos(yaw / 2.0)
        self.imu_pub.publish(imu)

        battery = BatteryState()
        battery.header.stamp = now
        # parser 已确保 v 是有限数值；这里不再二次兜底，避免把真实电压样本误吞掉。
        battery.voltage = float(feedback["voltage"])
        battery.present = True
        self.battery_pub.publish(battery)

        self._append_feedback_debug_line(feedback)

    def _append_feedback_debug_line(self, feedback: dict[str, float | None]) -> None:
        """按需追加 vendor T=1001 原始反馈证据，不参与控制闭环。"""
        log_path = getattr(self, "feedback_debug_log_path", "")
        if not log_path:
            return

        yaw = feedback["yaw"]
        record = {
            "schema": "trashbot.wave_rover.feedback_debug.v1",
            "observed_at_unix_s": time.time(),
            "source": "wave_rover_uart_t1001",
            "left_speed": feedback["left_speed"],
            "right_speed": feedback["right_speed"],
            "roll": feedback["roll"],
            "pitch": feedback["pitch"],
            "yaw": yaw,
            "yaw_available": yaw is not None,
            "voltage": feedback["voltage"],
        }

        try:
            # 串口 reader 已拥有同一帧的解析结果；这里只做追加落盘，失败不能影响 topic 或停车服务。
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        except OSError as exc:
            self.get_logger().warn(f"Failed to append WAVE ROVER feedback debug log: {exc}")

    def _cmd_vel_callback(self, msg: Twist) -> None:
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

    def _publish_odom(self) -> None:
        # 这里是命令积分，不是实测轮速里程计；HIL 前不能把它写成真实 odom。
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
        if self.odom_tf_broadcaster is not None:
            self.odom_tf_broadcaster.sendTransform(self._build_odom_transform(msg))

    def _build_odom_transform(self, odom: Odometry) -> TransformStamped:
        """把 command integration 的 odom 复制为同源 TF，避免 topic/TF 数据漂移。"""
        transform = TransformStamped()
        transform.header.stamp = odom.header.stamp
        transform.header.frame_id = odom.header.frame_id
        transform.child_frame_id = odom.child_frame_id
        transform.transform.translation.x = odom.pose.pose.position.x
        transform.transform.translation.y = odom.pose.pose.position.y
        transform.transform.translation.z = odom.pose.pose.position.z
        transform.transform.rotation.x = odom.pose.pose.orientation.x
        transform.transform.rotation.y = odom.pose.pose.orientation.y
        transform.transform.rotation.z = odom.pose.pose.orientation.z
        transform.transform.rotation.w = odom.pose.pose.orientation.w
        return transform

    def _send_stop(self) -> bool:
        # 停车命令使用 T=1 零左右轮速，这是 vendor speed control 的最小安全路径。
        return self._send_json({"T": CMD_SPEED_CTRL, "L": 0, "R": 0})

    def _stop_callback(self, request: Any, response: Any) -> Any:
        response.success = self._send_stop()
        response.message = "Motors stopped" if response.success else "Failed to send stop command"
        return response

    def _reset_odom_callback(self, request: Any, response: Any) -> Any:
        self._odom_x = 0.0
        self._odom_y = 0.0
        self._odom_theta = 0.0
        self._last_odom_time = self.get_clock().now()
        response.success = True
        response.message = "ROS-side odometry reset; no vendor ESP32 reset command sent"
        return response

    def _beep_callback(self, request: Any, response: Any) -> Any:
        response.success = False
        response.message = "Beep is not supported by the WAVE ROVER JSON base protocol"
        return response

    def destroy_node(self) -> None:
        self._running = False
        self._send_stop()
        if hasattr(self, "serial") and self.serial.is_open:
            self.serial.close()
        super().destroy_node()
