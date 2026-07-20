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

# 使用标准库长连接客户端，才能显式控制连接复用和失败后的连接淘汰。
import http.client
import json
import math
from pathlib import Path
import threading
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

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
        self.command_transport = config.command_transport
        self.wave_rover_http_base_url = config.wave_rover_http_base_url
        self.http_timeout_s = config.http_timeout_s
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
        # HTTP transport 也只有 bridge 单 owner；锁保证 keep-alive 请求不交叉并保持 stop 顺序。
        self._http_lock = threading.Lock()
        # 连接对象与 origin key 配对，配置切换时不能误复用旧主机上的 socket。
        self._http_connection = None
        self._http_connection_key = ""
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
            "command_transport",
            "wave_rover_http_base_url",
            "http_timeout_s",
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

        current_transport = getattr(self, "command_transport", "serial")
        current_http_base_url = getattr(self, "wave_rover_http_base_url", "")
        current_http_timeout_s = getattr(self, "http_timeout_s", 0.6)
        candidate = {
            "command_transport": str(changed.get("command_transport", current_transport)).lower(),
            "wave_rover_http_base_url": str(
                changed.get("wave_rover_http_base_url", current_http_base_url)
            ).rstrip("/"),
            "http_timeout_s": float(changed.get("http_timeout_s", current_http_timeout_s)),
            "command_mode": str(changed.get("command_mode", self.command_mode)).lower(),
            "track_width_m": float(changed.get("track_width_m", self.track_width_m)),
            "max_wheel_speed_mps": float(changed.get("max_wheel_speed_mps", self.max_wheel_speed_mps)),
            "pwm_min_abs": int(changed.get("pwm_min_abs", self.pwm_min_abs)),
            "pwm_max_abs": int(changed.get("pwm_max_abs", self.pwm_max_abs)),
        }
        try:
            validate_startup_config(
                command_transport=candidate["command_transport"],
                wave_rover_http_base_url=candidate["wave_rover_http_base_url"],
                http_timeout_s=candidate["http_timeout_s"],
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
        self.command_transport = candidate["command_transport"]
        self.wave_rover_http_base_url = candidate["wave_rover_http_base_url"]
        self.http_timeout_s = candidate["http_timeout_s"]
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
            f"command_transport={self.command_transport}; "
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
            "command_transport": self.command_transport,
            "wave_rover_http_base_url": self.wave_rover_http_base_url,
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
        command_transport = getattr(self, "command_transport", "serial")
        record = {
            "schema": "trashbot.wave_rover.command_debug.v1",
            "observed_at_unix_s": time.time(),
            "source": "esp32_bridge_startup_config",
            "vendor_command": command,
            "sent": bool(sent),
            "command_transport": command_transport,
            "serial_write_returned": bool(sent) if command_transport == "serial" else None,
            "http_write_returned": bool(sent) if command_transport == "http" else None,
            "transport_write_returned": bool(sent),
            "sends_motion": False,
        }
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        except OSError as exc:
            self.get_logger().warn(f"Failed to append WAVE ROVER startup config debug log: {exc}")

    def _send_json(self, command: dict[str, Any]) -> bool:
        if getattr(self, "command_transport", "serial") == "http":
            return self._send_json_http(command)
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

    def _send_json_http(self, command: dict[str, Any]) -> bool:
        """通过 ESP32 原厂 HTTP `/js` 控制面下发 JSON，绕过现场 UART TX 断点。"""
        # 连接只在后续请求复用；当前 nonzero 失败绝不自动重发，避免一次按键变成两次运动。
        http_lock = getattr(self, "_http_lock", None)
        if http_lock is None:
            http_lock = threading.Lock()
            self._http_lock = http_lock
        try:
            # 紧凑 JSON 延续既有 vendor `/js?json=...` 线协议，不改写 T/L/R/X/Z 语义。
            payload = json.dumps(command, separators=(",", ":"))
            query = urllib.parse.urlencode({"json": payload})
            # 拆分 origin 与可选 base path，避免把完整 URL 交给连接层后丢失部署前缀。
            parsed = urllib.parse.urlsplit(self.wave_rover_http_base_url.rstrip("/"))
            # origin 变化必须换连接，否则动态参数更新后可能仍把命令送往旧 ESP32。
            connection_key = f"{parsed.scheme}://{parsed.netloc}"
            request_path = f"{parsed.path.rstrip('/')}/js?{query}"
            # 锁覆盖 request、response 和 body 消费，保证同一连接上响应不会串到下一条命令。
            with http_lock:
                connection = getattr(self, "_http_connection", None)
                if connection is None or getattr(self, "_http_connection_key", "") != connection_key:
                    # 替换 origin 前先关闭旧连接，避免持有无效 socket 或泄漏文件描述符。
                    if connection is not None:
                        connection.close()
                    # HTTP/HTTPS 只改变传输封装，vendor `/js` 请求内容保持完全相同。
                    connection_type = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
                    connection = connection_type(parsed.hostname, parsed.port, timeout=self.http_timeout_s)
                    self._http_connection = connection
                    self._http_connection_key = connection_key
                # 显式 keep-alive 便于现场确认意图；是否复用仍由服务端响应和客户端状态共同决定。
                connection.request("GET", request_path, headers={"Connection": "keep-alive"})
                response = connection.getresponse()
                # 必须完整消费 body，标准库才能安全地把同一连接留给下一条独立命令。
                response.read()
                ok = 200 <= int(response.status) < 300
            # 只有 2xx 才更新成功时间，HTTP 错误响应不能伪装成已下发。
            if ok:
                self._last_send_time = time.time()
            return ok
        except (OSError, http.client.HTTPException, urllib.error.URLError, TimeoutError) as exc:
            # 失败连接只为下一请求重建；这里不重放当前 command，stop/nonzero 顺序保持一进一出。
            with http_lock:
                connection = getattr(self, "_http_connection", None)
                if connection is not None:
                    try:
                        connection.close()
                    except OSError:
                        pass
                self._http_connection = None
                self._http_connection_key = ""
            self.get_logger().error(f"WAVE ROVER HTTP command error: {exc}")
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
        # callback 入口点位必须先于校验和映射，才能覆盖 bridge 内完整软件处理段。
        bridge_callback_mono_ns = time.monotonic_ns()
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

        # build 完成点位只表示 vendor JSON 已构造，不代表网络、固件或轮子已响应。
        vendor_command_built_mono_ns = time.monotonic_ns()
        # 传输开始/结束包住 `_send_json`，同时覆盖 serial 与 HTTP 的同步返回边界。
        transport_write_start_mono_ns = time.monotonic_ns()
        sent = self._send_json(command)
        transport_write_end_mono_ns = time.monotonic_ns()
        # 原始点位随日志一次写入，避免第二次读钟引入不可解释的统计偏移。
        self._append_command_debug_line(
            msg,
            command,
            sent,
            timing={
                "bridge_callback_mono_ns": bridge_callback_mono_ns,
                "vendor_command_built_mono_ns": vendor_command_built_mono_ns,
                "transport_write_start_mono_ns": transport_write_start_mono_ns,
                "transport_write_end_mono_ns": transport_write_end_mono_ns,
            },
        )
        if sent:
            self._last_cmd_linear = float(msg.linear.x)
            self._last_cmd_angular = float(msg.angular.z)
        else:
            self.get_logger().warn("Failed to forward /cmd_vel to WAVE ROVER ESP32")

    def _append_command_debug_line(
        self,
        msg: Twist,
        command: dict[str, Any],
        sent: bool,
        *,
        timing: dict[str, int] | None = None,
    ) -> None:
        """按需记录 /cmd_vel 到 vendor JSON 的映射和串口写入结果。"""
        log_path = getattr(self, "command_debug_log_path", "")
        if not log_path:
            return

        command_transport = getattr(self, "command_transport", "serial")
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
            "command_transport": command_transport,
            "vendor_command": command,
            "sent": bool(sent),
            "serial_write_returned": bool(sent) if command_transport == "serial" else None,
            "http_write_returned": bool(sent) if command_transport == "http" else None,
            "transport_write_returned": bool(sent),
            "sends_motion": sends_motion,
        }
        if timing:
            # 原始点位只在本进程 clock_id 内有效；对外优先消费已计算的 local spans。
            callback_ns = timing["bridge_callback_mono_ns"]
            built_ns = timing["vendor_command_built_mono_ns"]
            write_start_ns = timing["transport_write_start_mono_ns"]
            write_end_ns = timing["transport_write_end_mono_ns"]
            # 所有差值来自同一 monotonic clock，禁止与 PC/Upper 的原始纳秒直接相减。
            record.update(
                {
                    "clock_id": "python_monotonic_ns",
                    **timing,
                    "bridge_callback_to_command_built_ms": (built_ns - callback_ns) / 1_000_000,
                    "bridge_command_built_to_transport_begin_ms": (write_start_ns - built_ns) / 1_000_000,
                    "bridge_transport_write_ms": (write_end_ns - write_start_ns) / 1_000_000,
                    "bridge_callback_to_transport_end_ms": (write_end_ns - callback_ns) / 1_000_000,
                }
            )
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
