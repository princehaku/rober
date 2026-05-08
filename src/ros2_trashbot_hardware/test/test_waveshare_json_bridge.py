import importlib
import json
from pathlib import Path
import sys
import types
import unittest


PACKAGE_SRC = Path(__file__).resolve().parents[1]
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))


def _install_ros_stubs():
    rclpy = types.ModuleType("rclpy")
    rclpy.node = types.ModuleType("rclpy.node")
    rclpy.node.Node = object
    sys.modules.setdefault("rclpy", rclpy)
    sys.modules.setdefault("rclpy.node", rclpy.node)

    geometry_msgs = types.ModuleType("geometry_msgs")
    geometry_msgs.msg = types.ModuleType("geometry_msgs.msg")

    class Twist:
        pass

    geometry_msgs.msg.Twist = Twist
    sys.modules.setdefault("geometry_msgs", geometry_msgs)
    sys.modules.setdefault("geometry_msgs.msg", geometry_msgs.msg)

    nav_msgs = types.ModuleType("nav_msgs")
    nav_msgs.msg = types.ModuleType("nav_msgs.msg")
    nav_msgs.msg.Odometry = type("Odometry", (), {})
    sys.modules.setdefault("nav_msgs", nav_msgs)
    sys.modules.setdefault("nav_msgs.msg", nav_msgs.msg)

    sensor_msgs = types.ModuleType("sensor_msgs")
    sensor_msgs.msg = types.ModuleType("sensor_msgs.msg")
    sensor_msgs.msg.Imu = type("Imu", (), {})
    sensor_msgs.msg.BatteryState = type("BatteryState", (), {})
    sensor_msgs.msg.Range = type("Range", (), {})
    sys.modules.setdefault("sensor_msgs", sensor_msgs)
    sys.modules.setdefault("sensor_msgs.msg", sensor_msgs.msg)

    std_srvs = types.ModuleType("std_srvs")
    std_srvs.srv = types.ModuleType("std_srvs.srv")
    std_srvs.srv.Trigger = type("Trigger", (), {})
    sys.modules.setdefault("std_srvs", std_srvs)
    sys.modules.setdefault("std_srvs.srv", std_srvs.srv)

    serial = types.ModuleType("serial")
    serial.SerialException = Exception
    serial.Serial = object
    sys.modules.setdefault("serial", serial)


def _bridge_module():
    _install_ros_stubs()
    return importlib.import_module("ros2_trashbot_hardware.esp32_bridge")


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
                command_mode="pwm",
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

    def test_startup_config_rejects_nonpositive_max_wheel_speed(self):
        bridge = _bridge_module()

        with self.assertRaisesRegex(ValueError, "max_wheel_speed_mps must be > 0"):
            bridge.validate_startup_config(
                command_mode="speed",
                track_width_m=0.172,
                max_wheel_speed_mps=-0.1,
                feedback_interval_ms=100,
                odom_publish_hz=20.0,
            )

    def test_startup_config_rejects_invalid_mode_track_width_and_feedback_interval(self):
        bridge = _bridge_module()

        with self.assertRaisesRegex(ValueError, "command_mode must be one of"):
            bridge.validate_startup_config("pwm", 0.172, 1.3, 100, 20.0)
        with self.assertRaisesRegex(ValueError, "track_width_m must be > 0"):
            bridge.validate_startup_config("speed", 0.0, 1.3, 100, 20.0)
        with self.assertRaisesRegex(ValueError, "feedback_interval_ms must be >= 0"):
            bridge.validate_startup_config("speed", 0.172, 1.3, -1, 20.0)

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
            },
        )

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
