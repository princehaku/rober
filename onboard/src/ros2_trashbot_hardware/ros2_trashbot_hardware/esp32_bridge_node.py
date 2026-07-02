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
from pathlib import Path
import threading
import time
from typing import Any

from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, Imu
from std_srvs.srv import Trigger
import serial
from tf2_ros import TransformBroadcaster

from ros2_trashbot_hardware.bridge_config import (
    declare_bridge_parameters,
    load_bridge_config,
    validate_startup_config,
)
from ros2_trashbot_hardware.wave_rover_feedback import (
    parse_feedback_line,
    vendor_degrees_to_ros_radians,
)
from ros2_trashbot_hardware.wave_rover_protocol import (
    CMD_PWM_INPUT,
    CMD_ROS_CTRL,
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
        self.pwm_min_abs = config.pwm_min_abs
        self.pwm_max_abs = config.pwm_max_abs
        self.main_type = config.main_type
        self.module_type = config.module_type
        self.feedback_interval_ms = config.feedback_interval_ms
        self.publish_odom_tf = config.publish_odom_tf
        self.feedback_debug_log_path = config.feedback_debug_log_path
        self.command_debug_log_path = config.command_debug_log_path

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

        self.add_on_set_parameters_callback(self._runtime_parameter_callback)
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
            f"main_type={self.main_type}; "
            f"module_type={self.module_type}; "
            f"publish_odom_tf={self.publish_odom_tf}; "
            f"feedback_debug_log_enabled={bool(self.feedback_debug_log_path)}; "
            f"command_debug_log_enabled={bool(self.command_debug_log_path)}; "
            "odom source=ROS-side command integration until measured wheel odometry is validated"
        )

    def _runtime_parameter_callback(self, parameters: list[Any]) -> SetParametersResult:
        """允许运行中调整安全边界内的底盘映射参数，避免为试 PWM 重启串口 owner。"""
        tunable_names = {
            "command_mode",
            "track_width_m",
            "max_wheel_speed_mps",
            "pwm_min_abs",
            "pwm_max_abs",
            "feedback_debug_log_path",
            "command_debug_log_path",
        }
        changed: dict[str, Any] = {}
        for parameter in parameters:
            name = getattr(parameter, "name", "")
            if name in tunable_names:
                changed[name] = getattr(parameter, "value", None)
        if not changed:
            return SetParametersResult(successful=True)

        candidate = {
            "command_mode": str(changed.get("command_mode", self.command_mode)).lower(),
            "track_width_m": float(changed.get("track_width_m", self.track_width_m)),
            "max_wheel_speed_mps": float(changed.get("max_wheel_speed_mps", self.max_wheel_speed_mps)),
            "pwm_min_abs": int(changed.get("pwm_min_abs", self.pwm_min_abs)),
            "pwm_max_abs": int(changed.get("pwm_max_abs", self.pwm_max_abs)),
        }
        try:
            validate_startup_config(
                command_mode=candidate["command_mode"],
                track_width_m=candidate["track_width_m"],
                max_wheel_speed_mps=candidate["max_wheel_speed_mps"],
                pwm_min_abs=candidate["pwm_min_abs"],
                pwm_max_abs=candidate["pwm_max_abs"],
                main_type=self.main_type,
                module_type=self.module_type,
                feedback_interval_ms=self.feedback_interval_ms,
                odom_publish_hz=1.0,
            )
        except (TypeError, ValueError) as exc:
            return SetParametersResult(successful=False, reason=str(exc))

        # 所有参数先校验再一次性生效，避免 pwm_min/pwm_max 只更新一半导致下一帧映射异常。
        self.command_mode = candidate["command_mode"]
        self.track_width_m = candidate["track_width_m"]
        self.max_wheel_speed_mps = candidate["max_wheel_speed_mps"]
        self.pwm_min_abs = candidate["pwm_min_abs"]
        self.pwm_max_abs = candidate["pwm_max_abs"]
        if "feedback_debug_log_path" in changed:
            self.feedback_debug_log_path = str(changed["feedback_debug_log_path"] or "")
        if "command_debug_log_path" in changed:
            self.command_debug_log_path = str(changed["command_debug_log_path"] or "")
        self._append_runtime_config_debug_line(sorted(changed))
        self.get_logger().info(
            "Runtime WAVE ROVER bridge tuning applied: "
            f"command_mode={self.command_mode}; "
            f"pwm_min_abs={self.pwm_min_abs}; "
            f"pwm_max_abs={self.pwm_max_abs}; "
            f"max_wheel_speed_mps={self.max_wheel_speed_mps}"
        )
        return SetParametersResult(successful=True)

    def _append_runtime_config_debug_line(self, changed_names: list[str]) -> None:
        """把运行中调参写入命令日志，方便把现场 PWM 试跑和后续 wheel 反馈对齐。"""
        log_path = getattr(self, "command_debug_log_path", "")
        if not log_path:
            return
        record = {
            "schema": "trashbot.wave_rover.command_debug.v1",
            "observed_at_unix_s": time.time(),
            "source": "esp32_bridge_runtime_parameter_callback",
            "changed_parameter_names": changed_names,
            "command_mode": self.command_mode,
            "track_width_m": self.track_width_m,
            "max_wheel_speed_mps": self.max_wheel_speed_mps,
            "pwm_min_abs": self.pwm_min_abs,
            "pwm_max_abs": self.pwm_max_abs,
            "sends_motion": False,
        }
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        except OSError as exc:
            self.get_logger().warn(f"Failed to append WAVE ROVER runtime config debug log: {exc}")

    def _configure_vendor_feedback(self) -> None:
        # 厂商 json_cmd.h 定义 T=900/143/142/131；启动时统一配置，避免机型模式或反馈流被旧状态污染。
        for command in build_startup_config_commands(
            self.feedback_interval_ms,
            main_type=self.main_type,
            module_type=self.module_type,
        ):
            sent = self._send_json(command)
            self._append_startup_config_debug_line(command, sent)

    def _append_startup_config_debug_line(self, command: dict[str, Any], sent: bool) -> None:
        """记录启动配置帧，证明 T=900/T=131 等不是运动命令且已尝试写入 UART。"""
        log_path = getattr(self, "command_debug_log_path", "")
        if not log_path:
            return
        record = {
            "schema": "trashbot.wave_rover.command_debug.v1",
            "observed_at_unix_s": time.time(),
            "source": "esp32_bridge_startup_config",
            "vendor_command": command,
            "sent": bool(sent),
            "sends_motion": False,
        }
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        except OSError as exc:
            self.get_logger().warn(f"Failed to append WAVE ROVER startup config debug log: {exc}")

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

    def _publish_feedback(self, feedback: dict[str, Any]) -> None:
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

    def _append_feedback_debug_line(self, feedback: dict[str, Any]) -> None:
        """按需追加 vendor T=1001 原始反馈证据，不参与控制闭环。"""
        log_path = getattr(self, "feedback_debug_log_path", "")
        try:
            # 允许运行中 ros2 param set 打开/切换日志，不需要重启 bridge 或抢占 UART。
            log_path = str(self.get_parameter("feedback_debug_log_path").value)
        except Exception:
            pass
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
            "vendor_frame": feedback.get("vendor_frame"),
        }

        try:
            # 串口 reader 已拥有同一帧的解析结果；这里只做追加落盘，失败不能影响 topic 或停车服务。
            log_file_path = Path(log_path)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            with log_file_path.open("a", encoding="utf-8") as log_file:
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
                pwm_min_abs=self.pwm_min_abs,
                pwm_max_abs=self.pwm_max_abs,
            )
        except ValueError as exc:
            self.get_logger().error(str(exc))
            return

        sent = self._send_json(command)
        self._append_command_debug_line(msg, command, sent)
        if sent:
            self._last_cmd_linear = float(msg.linear.x)
            self._last_cmd_angular = float(msg.angular.z)
        else:
            self.get_logger().warn("Failed to forward /cmd_vel to WAVE ROVER ESP32")

    def _append_command_debug_line(self, msg: Twist, command: dict[str, Any], sent: bool) -> None:
        """按需记录 /cmd_vel 到 vendor JSON 的映射和串口写入结果。"""
        log_path = getattr(self, "command_debug_log_path", "")
        if not log_path:
            return

        sends_motion = any(
            abs(float(command.get(key, 0))) > 1e-9
            for key in ("L", "R", "X", "Z")
        )
        record = {
            "schema": "trashbot.wave_rover.command_debug.v1",
            "observed_at_unix_s": time.time(),
            "source": "esp32_bridge_cmd_vel_callback",
            "linear_x": float(msg.linear.x),
            "angular_z": float(msg.angular.z),
            "command_mode": self.command_mode,
            "vendor_command": command,
            "sent": bool(sent),
            "serial_write_returned": bool(sent),
            "sends_motion": sends_motion,
        }
        try:
            # 命令日志只在 proof 显式打开时使用，失败不能阻断停车或速度转发。
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        except OSError as exc:
            self.get_logger().warn(f"Failed to append WAVE ROVER command debug log: {exc}")

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
        # 停车同时覆盖 PWM、speed 和 ROS 三种 vendor 控制面，避免现场切换模式后残留运动。
        results = [
            self._send_json({"T": CMD_PWM_INPUT, "L": 0, "R": 0}),
            self._send_json({"T": CMD_SPEED_CTRL, "L": 0, "R": 0}),
            self._send_json({"T": CMD_ROS_CTRL, "X": 0, "Z": 0}),
        ]
        return any(results)

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
