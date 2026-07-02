import importlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest


PACKAGE_SRC = Path(__file__).resolve().parents[1]
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))


def _install_ros_stubs():
    rclpy = types.ModuleType("rclpy")
    rclpy.node = types.ModuleType("rclpy.node")
    rclpy.node.Node = object
    sys.modules["rclpy"] = rclpy
    sys.modules["rclpy.node"] = rclpy.node

    rcl_interfaces = types.ModuleType("rcl_interfaces")
    rcl_interfaces.msg = types.ModuleType("rcl_interfaces.msg")

    class SetParametersResult:
        def __init__(self, successful=False, reason=""):
            self.successful = successful
            self.reason = reason

    rcl_interfaces.msg.SetParametersResult = SetParametersResult
    sys.modules["rcl_interfaces"] = rcl_interfaces
    sys.modules["rcl_interfaces.msg"] = rcl_interfaces.msg

    geometry_msgs = types.ModuleType("geometry_msgs")
    geometry_msgs.msg = types.ModuleType("geometry_msgs.msg")

    class _Header:
        def __init__(self):
            self.stamp = None
            self.frame_id = ""

    class _Vector3:
        def __init__(self):
            self.x = 0.0
            self.y = 0.0
            self.z = 0.0

    class _Quaternion:
        def __init__(self):
            self.x = 0.0
            self.y = 0.0
            self.z = 0.0
            self.w = 0.0

    class _Transform:
        def __init__(self):
            self.translation = _Vector3()
            self.rotation = _Quaternion()

    class TransformStamped:
        def __init__(self):
            self.header = _Header()
            self.child_frame_id = ""
            self.transform = _Transform()

    class Twist:
        pass

    geometry_msgs.msg.TransformStamped = TransformStamped
    geometry_msgs.msg.Twist = Twist
    sys.modules["geometry_msgs"] = geometry_msgs
    sys.modules["geometry_msgs.msg"] = geometry_msgs.msg

    nav_msgs = types.ModuleType("nav_msgs")
    nav_msgs.msg = types.ModuleType("nav_msgs.msg")

    class _Point:
        def __init__(self):
            self.x = 0.0
            self.y = 0.0
            self.z = 0.0

    class _Pose:
        def __init__(self):
            self.position = _Point()
            self.orientation = _Quaternion()

    class _PoseWithCovariance:
        def __init__(self):
            self.pose = _Pose()

    class _TwistValues:
        def __init__(self):
            self.linear = _Vector3()
            self.angular = _Vector3()

    class _TwistWithCovariance:
        def __init__(self):
            self.twist = _TwistValues()

    class Odometry:
        def __init__(self):
            self.header = _Header()
            self.child_frame_id = ""
            self.pose = _PoseWithCovariance()
            self.twist = _TwistWithCovariance()

    nav_msgs.msg.Odometry = Odometry
    sys.modules["nav_msgs"] = nav_msgs
    sys.modules["nav_msgs.msg"] = nav_msgs.msg

    sensor_msgs = types.ModuleType("sensor_msgs")
    sensor_msgs.msg = types.ModuleType("sensor_msgs.msg")

    class _Orientation:
        def __init__(self):
            self.x = 0.0
            self.y = 0.0
            self.z = 0.0
            self.w = 0.0

    class Imu:
        def __init__(self):
            self.header = _Header()
            self.orientation = _Orientation()
            self.orientation_covariance = [0.0] * 9

    class BatteryState:
        def __init__(self):
            self.header = _Header()
            self.voltage = 0.0
            self.present = False

    sensor_msgs.msg.Imu = Imu
    sensor_msgs.msg.BatteryState = BatteryState
    sensor_msgs.msg.Range = type("Range", (), {})
    sys.modules["sensor_msgs"] = sensor_msgs
    sys.modules["sensor_msgs.msg"] = sensor_msgs.msg

    std_srvs = types.ModuleType("std_srvs")
    std_srvs.srv = types.ModuleType("std_srvs.srv")
    std_srvs.srv.Trigger = type("Trigger", (), {})
    sys.modules["std_srvs"] = std_srvs
    sys.modules["std_srvs.srv"] = std_srvs.srv

    serial = types.ModuleType("serial")
    serial.SerialException = Exception
    serial.Serial = object
    sys.modules["serial"] = serial

    tf2_ros = types.ModuleType("tf2_ros")

    class TransformBroadcaster:
        def __init__(self, node):
            self.node = node
            self.messages = []

        def sendTransform(self, message):
            self.messages.append(message)

    tf2_ros.TransformBroadcaster = TransformBroadcaster
    sys.modules["tf2_ros"] = tf2_ros


def _bridge_module():
    _install_ros_stubs()
    return importlib.import_module("ros2_trashbot_hardware.esp32_bridge")


class _FakePublisher:
    def __init__(self):
        self.messages = []

    def publish(self, message):
        self.messages.append(message)


class _FakeClockNow:
    def __init__(self, nanoseconds=0):
        self.nanoseconds = nanoseconds

    def to_msg(self):
        return "fake-stamp"

    def __sub__(self, other):
        return _FakeClockNow(self.nanoseconds - other.nanoseconds)


class _FakeClock:
    def __init__(self, *nanoseconds_values):
        self._values = list(nanoseconds_values) or [0]

    def now(self):
        if len(self._values) > 1:
            return _FakeClockNow(self._values.pop(0))
        return _FakeClockNow(self._values[0])


class _FakeParameter:
    def __init__(self, value):
        self.value = value


class _FakeBroadcaster:
    def __init__(self):
        self.messages = []

    def sendTransform(self, message):
        self.messages.append(message)


class _FakeLogger:
    def __init__(self):
        self.warnings = []
        self.infos = []

    def warn(self, message):
        self.warnings.append(message)

    def info(self, message):
        self.infos.append(message)


class _FakeBridgeNode:
    def __init__(self):
        self.destroyed = False
        self.logger = _FakeLogger()

    def destroy_node(self):
        self.destroyed = True

    def get_logger(self):
        return self.logger


class WaveshareJsonBridgeTest(unittest.TestCase):
    def test_cmd_vel_defaults_to_waveshare_speed_json_line(self):
        bridge = _bridge_module()

        command = bridge.build_cmd_vel_command(
            linear_x=0.65,
            angular_z=0.0,
            command_mode="speed",
            track_width_m=0.172,
            max_wheel_speed_mps=1.3,
        )
        encoded = bridge.encode_json_command(command)

        self.assertEqual(json.loads(encoded.decode("utf-8")), {"T": 1, "L": 0.5, "R": 0.5})
        self.assertTrue(encoded.endswith(b"\n"))

    def test_main_ignores_duplicate_rclpy_shutdown_from_managed_sigint(self):
        bridge = _bridge_module()
        fake_node = _FakeBridgeNode()
        calls: list[str] = []
        original_rclpy = bridge.rclpy
        original_bridge = bridge.ESP32Bridge

        def shutdown_once_more():
            calls.append("shutdown")
            raise RuntimeError("failed to shutdown: rcl_shutdown already called on the given context")

        bridge.rclpy = types.SimpleNamespace(
            init=lambda args=None: calls.append("init"),
            spin=lambda node: calls.append("spin"),
            shutdown=shutdown_once_more,
        )
        bridge.ESP32Bridge = lambda: fake_node
        try:
            bridge.main(args=["--ros-args"])
        finally:
            bridge.rclpy = original_rclpy
            bridge.ESP32Bridge = original_bridge

        self.assertEqual(calls, ["init", "spin", "shutdown"])
        self.assertTrue(fake_node.destroyed)
        self.assertIn("忽略重复 rclpy shutdown", fake_node.logger.warnings[0])

    def test_main_reraises_unexpected_rclpy_shutdown_errors(self):
        bridge = _bridge_module()
        fake_node = _FakeBridgeNode()
        original_rclpy = bridge.rclpy
        original_bridge = bridge.ESP32Bridge

        bridge.rclpy = types.SimpleNamespace(
            init=lambda args=None: None,
            spin=lambda node: None,
            shutdown=lambda: (_ for _ in ()).throw(RuntimeError("different shutdown failure")),
        )
        bridge.ESP32Bridge = lambda: fake_node
        try:
            with self.assertRaisesRegex(RuntimeError, "different shutdown failure"):
                bridge.main()
        finally:
            bridge.rclpy = original_rclpy
            bridge.ESP32Bridge = original_bridge

        self.assertTrue(fake_node.destroyed)

    def test_cmd_vel_ros_mode_uses_t13_x_z_fields(self):
        bridge = _bridge_module()

        command = bridge.build_cmd_vel_command(
            linear_x=0.1,
            angular_z=0.3,
            command_mode="ros",
            track_width_m=0.172,
            max_wheel_speed_mps=1.3,
        )

        self.assertEqual(command, {"T": 13, "X": 0.1, "Z": 0.3})

    def test_cmd_vel_speed_mode_clamps_wheel_values(self):
        bridge = _bridge_module()

        command = bridge.build_cmd_vel_command(
            linear_x=9.0,
            angular_z=0.0,
            command_mode="speed",
            track_width_m=0.172,
            max_wheel_speed_mps=1.3,
        )

        self.assertEqual(command, {"T": 1, "L": 1.0, "R": 1.0})

    def test_cmd_vel_pwm_mode_uses_vendor_sample_t11_pwm(self):
        bridge = _bridge_module()

        command = bridge.build_cmd_vel_command(
            linear_x=0.12,
            angular_z=0.0,
            command_mode="pwm",
            track_width_m=0.172,
            max_wheel_speed_mps=1.3,
            pwm_min_abs=164,
            pwm_max_abs=164,
        )

        self.assertEqual(command, {"T": 11, "L": 164, "R": 164})

    def test_positive_angular_z_lowers_left_and_raises_right_wheel(self):
        bridge = _bridge_module()

        command = bridge.build_cmd_vel_command(
            linear_x=0.2,
            angular_z=1.0,
            command_mode="speed",
            track_width_m=0.4,
            max_wheel_speed_mps=1.0,
        )

        self.assertEqual(command["T"], 1)
        self.assertLess(command["L"], command["R"])
        self.assertEqual(command["L"], 0.0)
        self.assertEqual(command["R"], 0.4)

    def test_cmd_vel_rejects_invalid_command_mode(self):
        bridge = _bridge_module()

        with self.assertRaisesRegex(ValueError, "Unsupported command_mode"):
            bridge.build_cmd_vel_command(
                linear_x=0.0,
                angular_z=0.0,
                command_mode="bad_mode",
                track_width_m=0.172,
                max_wheel_speed_mps=1.3,
            )

    def test_cmd_vel_rejects_nonpositive_max_wheel_speed(self):
        bridge = _bridge_module()

        with self.assertRaisesRegex(ValueError, "max_wheel_speed_mps must be > 0"):
            bridge.build_cmd_vel_command(
                linear_x=0.0,
                angular_z=0.0,
                command_mode="speed",
                track_width_m=0.172,
                max_wheel_speed_mps=0.0,
            )

    def test_cmd_vel_rejects_non_finite_motion_values(self):
        bridge = _bridge_module()

        for linear_x, angular_z in (("NaN", 0.0), (0.0, "Infinity"), (float("-inf"), 0.0)):
            with self.subTest(linear_x=linear_x, angular_z=angular_z):
                with self.assertRaisesRegex(ValueError, "cmd_vel values must be finite"):
                    bridge.build_cmd_vel_command(
                        linear_x=linear_x,
                        angular_z=angular_z,
                        command_mode="speed",
                        track_width_m=0.172,
                        max_wheel_speed_mps=1.3,
                    )

    def test_startup_config_rejects_nonpositive_max_wheel_speed(self):
        bridge = _bridge_module()

        with self.assertRaisesRegex(ValueError, "max_wheel_speed_mps must be > 0"):
            bridge.validate_startup_config(
                command_mode="speed",
                track_width_m=0.172,
                max_wheel_speed_mps=-0.1,
                pwm_min_abs=90,
                pwm_max_abs=90,
                feedback_interval_ms=100,
                odom_publish_hz=20.0,
            )

    def test_startup_config_rejects_invalid_mode_track_width_and_feedback_interval(self):
        bridge = _bridge_module()

        with self.assertRaisesRegex(ValueError, "command_mode must be one of"):
            bridge.validate_startup_config("bad_mode", 0.172, 1.3, 90, 90, 100, 20.0)
        with self.assertRaisesRegex(ValueError, "track_width_m must be > 0"):
            bridge.validate_startup_config("speed", 0.0, 1.3, 90, 90, 100, 20.0)
        with self.assertRaisesRegex(ValueError, "feedback_interval_ms must be >= 0"):
            bridge.validate_startup_config("speed", 0.172, 1.3, 90, 90, -1, 20.0)

    def test_base_feedback_line_parses_imu_and_battery_fields(self):
        bridge = _bridge_module()

        feedback = bridge.parse_feedback_line(
            b'{"T":1001,"L":0.2,"R":0.3,"r":1.0,"p":2.0,"y":3.0,"v":11.7}\n'
        )

        self.assertEqual(
            feedback,
            {
                "left_speed": 0.2,
                "right_speed": 0.3,
                "roll": 1.0,
                "pitch": 2.0,
                "yaw": 3.0,
                "voltage": 11.7,
                "vendor_frame": {"T": 1001, "L": 0.2, "R": 0.3, "r": 1.0, "p": 2.0, "y": 3.0, "v": 11.7},
            },
        )

    def test_base_feedback_line_accepts_null_yaw_without_dropping_voltage(self):
        bridge = _bridge_module()

        for yaw_value in ("null", None):
            with self.subTest(yaw_value=yaw_value):
                payload = {
                    "T": 1001,
                    "L": 0.2,
                    "R": 0.3,
                    "r": 1.0,
                    "p": 2.0,
                    "y": yaw_value,
                    "v": 11.7,
                }
                feedback = bridge.parse_feedback_line(json.dumps(payload))

                self.assertEqual(feedback["voltage"], 11.7)
                self.assertIsNone(feedback["yaw"])

    def test_feedback_parser_ignores_bad_or_unknown_lines(self):
        bridge = _bridge_module()

        self.assertIsNone(bridge.parse_feedback_line(b"not json\n"))
        self.assertIsNone(bridge.parse_feedback_line(b'{"T":999,"x":1}\n'))
        self.assertIsNone(bridge.parse_feedback_line(b'{"T":1001,"L":0.2}\n'))
        self.assertIsNone(
            bridge.parse_feedback_line(
                b'{"T":1001,"L":"nan?","R":0.3,"r":1.0,"p":2.0,"y":3.0,"v":11.7}\n'
            )
        )

    def test_feedback_parser_rejects_non_finite_numeric_values(self):
        bridge = _bridge_module()

        for key in ("L", "R", "r", "p", "v"):
            payload = {"T": 1001, "L": 0.2, "R": 0.3, "r": 1.0, "p": 2.0, "y": 3.0, "v": 11.7}
            payload[key] = "NaN"
            self.assertIsNone(bridge.parse_feedback_line(json.dumps(payload)))

            payload[key] = "Infinity"
            self.assertIsNone(bridge.parse_feedback_line(json.dumps(payload)))

        for yaw_value in ("NaN", "Infinity", "-Infinity", "yaw?"):
            payload = {"T": 1001, "L": 0.2, "R": 0.3, "r": 1.0, "p": 2.0, "y": yaw_value, "v": 11.7}
            self.assertIsNone(bridge.parse_feedback_line(json.dumps(payload)))

    def test_publish_feedback_marks_orientation_unavailable_when_yaw_missing(self):
        bridge = _bridge_module()

        node = bridge.ESP32Bridge.__new__(bridge.ESP32Bridge)
        node.imu_pub = _FakePublisher()
        node.battery_pub = _FakePublisher()
        node.get_clock = lambda: _FakeClock()

        node._publish_feedback(
            {
                "left_speed": 0.2,
                "right_speed": 0.3,
                "roll": 1.0,
                "pitch": 2.0,
                "yaw": None,
                "voltage": 11.7,
            }
        )

        self.assertEqual(len(node.imu_pub.messages), 1)
        self.assertEqual(len(node.battery_pub.messages), 1)
        imu = node.imu_pub.messages[0]
        battery = node.battery_pub.messages[0]
        self.assertEqual(imu.header.frame_id, "imu_link")
        self.assertEqual(imu.orientation.w, 1.0)
        self.assertEqual(imu.orientation_covariance[0], -1.0)
        self.assertEqual(battery.voltage, 11.7)
        self.assertTrue(battery.present)

    def test_publish_feedback_appends_debug_jsonl_when_path_enabled(self):
        bridge = _bridge_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "feedback.jsonl"
            node = bridge.ESP32Bridge.__new__(bridge.ESP32Bridge)
            node.imu_pub = _FakePublisher()
            node.battery_pub = _FakePublisher()
            node.get_clock = lambda: _FakeClock()
            node.get_logger = lambda: _FakeLogger()
            # 调试日志只记录已解析的同帧 vendor 字段，避免和串口 owner 抢读 raw UART。
            node.feedback_debug_log_path = str(log_path)

            node._publish_feedback(
                {
                    "left_speed": 0.2,
                    "right_speed": 0.3,
                    "roll": 1.0,
                    "pitch": 2.0,
                    "yaw": 3.0,
                    "voltage": 11.7,
                    "vendor_frame": {"T": 1001, "L": 0.2, "R": 0.3, "r": 1.0, "p": 2.0, "y": 3.0, "v": 11.7},
                }
            )

            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["schema"], "trashbot.wave_rover.feedback_debug.v1")
            self.assertGreater(record["observed_at_unix_s"], 0)
            self.assertEqual(record["source"], "wave_rover_uart_t1001")
            self.assertEqual(record["left_speed"], 0.2)
            self.assertEqual(record["right_speed"], 0.3)
            self.assertEqual(record["roll"], 1.0)
            self.assertEqual(record["pitch"], 2.0)
            self.assertEqual(record["yaw"], 3.0)
            self.assertTrue(record["yaw_available"])
            self.assertEqual(record["voltage"], 11.7)
            self.assertEqual(
                record["vendor_frame"],
                {"T": 1001, "L": 0.2, "R": 0.3, "r": 1.0, "p": 2.0, "y": 3.0, "v": 11.7},
            )

    def test_publish_feedback_reads_dynamic_debug_log_parameter(self):
        bridge = _bridge_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "dynamic_feedback.jsonl"
            node = bridge.ESP32Bridge.__new__(bridge.ESP32Bridge)
            node.imu_pub = _FakePublisher()
            node.battery_pub = _FakePublisher()
            node.get_clock = lambda: _FakeClock()
            node.get_logger = lambda: _FakeLogger()
            node.feedback_debug_log_path = ""
            node.get_parameter = lambda name: _FakeParameter(str(log_path) if name == "feedback_debug_log_path" else "")

            node._publish_feedback(
                {
                    "left_speed": 0.4,
                    "right_speed": 0.5,
                    "roll": 1.0,
                    "pitch": 2.0,
                    "yaw": None,
                    "voltage": 11.9,
                    "vendor_frame": {"T": 1001, "L": 0.4, "R": 0.5, "r": 1.0, "p": 2.0, "y": None, "v": 11.9},
                }
            )

            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["left_speed"], 0.4)
            self.assertEqual(record["right_speed"], 0.5)
            self.assertFalse(record["yaw_available"])

    def test_publish_feedback_warns_but_keeps_topics_when_debug_log_fails(self):
        bridge = _bridge_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            logger = _FakeLogger()
            node = bridge.ESP32Bridge.__new__(bridge.ESP32Bridge)
            node.imu_pub = _FakePublisher()
            node.battery_pub = _FakePublisher()
            node.get_clock = lambda: _FakeClock()
            node.get_logger = lambda: logger
            # 目录路径会触发 OSError；此时仍必须先完成 topic 发布，不能影响安全 stop 线程。
            node.feedback_debug_log_path = temp_dir

            node._publish_feedback(
                {
                    "left_speed": 0.2,
                    "right_speed": 0.3,
                    "roll": 1.0,
                    "pitch": 2.0,
                    "yaw": None,
                    "voltage": 11.7,
                }
            )

            self.assertEqual(len(node.imu_pub.messages), 1)
            self.assertEqual(len(node.battery_pub.messages), 1)
            self.assertEqual(node.imu_pub.messages[0].orientation_covariance[0], -1.0)
            self.assertEqual(node.battery_pub.messages[0].voltage, 11.7)
            self.assertIn("Failed to append WAVE ROVER feedback debug log", logger.warnings[0])

    def test_cmd_vel_appends_command_debug_jsonl_when_path_enabled(self):
        bridge = _bridge_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "command.jsonl"
            node = bridge.ESP32Bridge.__new__(bridge.ESP32Bridge)
            node.command_mode = "pwm"
            node.track_width_m = 0.172
            node.max_wheel_speed_mps = 1.3
            node.pwm_min_abs = 164
            node.pwm_max_abs = 164
            node.command_debug_log_path = str(log_path)
            node._last_cmd_linear = 0.0
            node._last_cmd_angular = 0.0
            node._send_json = lambda command: True
            node.get_logger = lambda: _FakeLogger()

            message = types.SimpleNamespace(
                linear=types.SimpleNamespace(x=0.2),
                angular=types.SimpleNamespace(z=0.0),
            )
            node._cmd_vel_callback(message)

            record = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(record["schema"], "trashbot.wave_rover.command_debug.v1")
            self.assertEqual(record["source"], "esp32_bridge_cmd_vel_callback")
            self.assertEqual(record["command_mode"], "pwm")
            self.assertEqual(record["linear_x"], 0.2)
            self.assertEqual(record["vendor_command"], {"L": 164, "R": 164, "T": 11})
            self.assertEqual(node._last_cmd_linear, 0.2)

    def test_runtime_pwm_parameter_update_changes_next_cmd_vel_mapping(self):
        bridge = _bridge_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "command.jsonl"
            logger = _FakeLogger()
            sent_commands = []
            node = bridge.ESP32Bridge.__new__(bridge.ESP32Bridge)
            node.command_mode = "pwm"
            node.track_width_m = 0.172
            node.max_wheel_speed_mps = 1.3
            node.pwm_min_abs = 164
            node.pwm_max_abs = 164
            node.feedback_interval_ms = 100
            node.feedback_debug_log_path = ""
            node.command_debug_log_path = str(log_path)
            node._last_cmd_linear = 0.0
            node._last_cmd_angular = 0.0
            node._send_json = lambda command: sent_commands.append(command) or True
            node.get_logger = lambda: logger

            result = node._runtime_parameter_callback(
                [
                    types.SimpleNamespace(name="pwm_min_abs", value=220),
                    types.SimpleNamespace(name="pwm_max_abs", value=220),
                ]
            )
            node._cmd_vel_callback(
                types.SimpleNamespace(
                    linear=types.SimpleNamespace(x=0.08),
                    angular=types.SimpleNamespace(z=0.0),
                )
            )

            self.assertTrue(result.successful)
            self.assertEqual(node.pwm_min_abs, 220)
            self.assertEqual(node.pwm_max_abs, 220)
            self.assertEqual(sent_commands[-1], {"T": 11, "L": 220, "R": 220})
            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(records[0]["source"], "esp32_bridge_runtime_parameter_callback")
            self.assertEqual(records[0]["changed_parameter_names"], ["pwm_max_abs", "pwm_min_abs"])
            self.assertFalse(records[0]["sends_motion"])
            self.assertEqual(records[-1]["vendor_command"], {"T": 11, "L": 220, "R": 220})
            self.assertIn("Runtime WAVE ROVER bridge tuning applied", logger.infos[0])

    def test_runtime_pwm_parameter_update_rejects_invalid_range_atomically(self):
        bridge = _bridge_module()

        node = bridge.ESP32Bridge.__new__(bridge.ESP32Bridge)
        node.command_mode = "pwm"
        node.track_width_m = 0.172
        node.max_wheel_speed_mps = 1.3
        node.pwm_min_abs = 164
        node.pwm_max_abs = 164
        node.feedback_interval_ms = 100
        node.feedback_debug_log_path = ""
        node.command_debug_log_path = ""
        node.get_logger = lambda: _FakeLogger()

        result = node._runtime_parameter_callback(
            [
                types.SimpleNamespace(name="pwm_min_abs", value=260),
                types.SimpleNamespace(name="pwm_max_abs", value=260),
            ]
        )

        self.assertFalse(result.successful)
        self.assertIn("pwm_min_abs/pwm_max_abs", result.reason)
        self.assertEqual(node.pwm_min_abs, 164)
        self.assertEqual(node.pwm_max_abs, 164)

    def test_declare_and_load_bridge_config_defaults_to_pwm_command_mode(self):
        bridge_config = importlib.import_module("ros2_trashbot_hardware.bridge_config")

        class _ConfigNode:
            def __init__(self):
                self.parameters = {}

            def declare_parameter(self, name, value):
                self.parameters[name] = value

            def get_parameter(self, name):
                return _FakeParameter(self.parameters[name])

        node = _ConfigNode()
        bridge_config.declare_bridge_parameters(node)
        config = bridge_config.load_bridge_config(node)

        self.assertEqual(config.command_mode, "pwm")
        self.assertEqual(config.pwm_min_abs, 164)
        self.assertEqual(config.pwm_max_abs, 164)
        self.assertTrue(config.publish_odom_tf)
        self.assertEqual(config.feedback_debug_log_path, "/root/rober/onboard/runtime/wave_rover_feedback_debug.jsonl")
        self.assertEqual(config.command_debug_log_path, "")

    def test_publish_odom_sends_matching_tf_when_enabled(self):
        bridge = _bridge_module()

        node = bridge.ESP32Bridge.__new__(bridge.ESP32Bridge)
        node._last_cmd_linear = 1.0
        node._last_cmd_angular = 0.5
        node._odom_x = 0.0
        node._odom_y = 0.0
        node._odom_theta = 0.0
        node._last_odom_time = _FakeClockNow(0)
        node.get_clock = lambda: _FakeClock(1_000_000_000)
        node.odom_pub = _FakePublisher()
        node.odom_tf_broadcaster = _FakeBroadcaster()

        node._publish_odom()

        self.assertEqual(len(node.odom_pub.messages), 1)
        self.assertEqual(len(node.odom_tf_broadcaster.messages), 1)
        odom = node.odom_pub.messages[0]
        transform = node.odom_tf_broadcaster.messages[0]
        self.assertEqual(transform.header.frame_id, odom.header.frame_id)
        self.assertEqual(transform.child_frame_id, odom.child_frame_id)
        self.assertEqual(transform.transform.translation.x, odom.pose.pose.position.x)
        self.assertEqual(transform.transform.translation.y, odom.pose.pose.position.y)
        self.assertEqual(transform.transform.translation.z, odom.pose.pose.position.z)
        self.assertEqual(transform.transform.rotation.x, odom.pose.pose.orientation.x)
        self.assertEqual(transform.transform.rotation.y, odom.pose.pose.orientation.y)
        self.assertEqual(transform.transform.rotation.z, odom.pose.pose.orientation.z)
        self.assertEqual(transform.transform.rotation.w, odom.pose.pose.orientation.w)

    def test_publish_odom_skips_tf_when_disabled(self):
        bridge = _bridge_module()

        node = bridge.ESP32Bridge.__new__(bridge.ESP32Bridge)
        node._last_cmd_linear = 0.2
        node._last_cmd_angular = 0.0
        node._odom_x = 0.0
        node._odom_y = 0.0
        node._odom_theta = 0.0
        node._last_odom_time = _FakeClockNow(0)
        node.get_clock = lambda: _FakeClock(500_000_000)
        node.odom_pub = _FakePublisher()
        node.odom_tf_broadcaster = None

        node._publish_odom()

        self.assertEqual(len(node.odom_pub.messages), 1)

    def test_startup_config_sends_echo_interval_and_feedback_flow(self):
        bridge = _bridge_module()

        commands = bridge.build_startup_config_commands(feedback_interval_ms=75)

        self.assertEqual(
            commands,
            [
                {"T": 143, "cmd": 0},
                {"T": 142, "cmd": 75},
                {"T": 131, "cmd": 1},
            ],
        )

    def test_vendor_yaw_degrees_convert_to_ros_radians(self):
        bridge = _bridge_module()

        self.assertAlmostEqual(bridge.vendor_degrees_to_ros_radians(180.0), 3.141592653589793)


if __name__ == "__main__":
    unittest.main()
