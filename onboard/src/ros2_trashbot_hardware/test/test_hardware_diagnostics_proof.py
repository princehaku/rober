import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout


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
    geometry_msgs.msg.Twist = type("Twist", (), {})
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


def _proof_module():
    _install_ros_stubs()
    return importlib.import_module("ros2_trashbot_hardware.hardware_diagnostics_proof")


class HardwareDiagnosticsProofTest(unittest.TestCase):
    def test_default_proof_artifact_contains_required_sections(self):
        proof_module = _proof_module()

        proof = proof_module.build_hardware_diagnostics_proof()

        self.assertEqual(proof["status"], "software_proof_ready")
        for key in (
            "vendor_sources",
            "config",
            "startup_commands",
            "cmd_vel_examples",
            "feedback_sample",
            "risk_flags",
            "hil_recipe",
        ):
            self.assertIn(key, proof)
        self.assertIn("docs/vendor/VENDOR_INDEX.md", proof["vendor_sources"])
        self.assertEqual(proof["config"]["command_mode"], "speed")
        self.assertEqual(proof["feedback_sample"]["status"], "parsed")
        self.assertEqual(proof["feedback_sample"]["parsed"]["voltage"], 11.7)

    def test_startup_commands_include_vendor_echo_interval_and_feedback_flow(self):
        proof_module = _proof_module()

        proof = proof_module.build_hardware_diagnostics_proof(
            config={"feedback_interval_ms": 75}
        )

        command_ids = [entry["command"]["T"] for entry in proof["startup_commands"]]
        self.assertEqual(command_ids, [143, 142, 131])
        self.assertEqual(proof["startup_commands"][1]["command"], {"T": 142, "cmd": 75})
        self.assertTrue(proof["startup_commands"][0]["uart_frame"].endswith("\n"))

    def test_cmd_vel_examples_reuse_speed_and_ros_protocol_builders(self):
        proof_module = _proof_module()

        proof = proof_module.build_hardware_diagnostics_proof()
        examples = proof["cmd_vel_examples"]

        self.assertEqual(examples["speed_mode_forward"]["command"], {"T": 1, "L": 0.5, "R": 0.5})
        self.assertEqual(
            examples["ros_mode_forward_unverified"]["command"], {"T": 13, "X": 0.1, "Z": 0.0}
        )
        self.assertEqual(json.loads(examples["speed_mode_forward"]["uart_frame"]), {"T": 1, "L": 0.5, "R": 0.5})

    def test_invalid_config_outputs_structured_invalid_config(self):
        proof_module = _proof_module()

        proof = proof_module.build_hardware_diagnostics_proof(
            config={"command_mode": "pwm"}
        )

        self.assertEqual(proof["status"], "invalid_config")
        self.assertEqual(proof["config_validation"]["status"], "invalid_config")
        self.assertIn("command_mode", proof["config_validation"]["error"])
        self.assertEqual(proof["startup_commands"], [])
        self.assertEqual(proof["cmd_vel_examples"], {})

    def test_invalid_speed_or_geometry_config_outputs_structured_error(self):
        proof_module = _proof_module()

        for config, expected in (
            ({"track_width_m": 0.0}, "track_width_m must be > 0"),
            ({"max_wheel_speed_mps": 0.0}, "max_wheel_speed_mps must be > 0"),
            ({"serial_baudrate": 0}, "serial_baudrate must be > 0"),
        ):
            with self.subTest(config=config):
                proof = proof_module.build_hardware_diagnostics_proof(config=config)
                self.assertEqual(proof["status"], "invalid_config")
                self.assertIn(expected, proof["config_validation"]["error"])

    def test_non_numeric_config_values_output_structured_invalid_config(self):
        proof_module = _proof_module()

        for config_key in (
            "serial_baudrate",
            "track_width_m",
            "max_wheel_speed_mps",
            "feedback_interval_ms",
            "odom_publish_hz",
        ):
            with self.subTest(config_key=config_key):
                proof = proof_module.build_hardware_diagnostics_proof(
                    config={config_key: "bad"}
                )
                self.assertEqual(proof["status"], "invalid_config")
                self.assertEqual(proof["config_validation"]["status"], "invalid_config")
                self.assertIn(config_key, proof["config_validation"]["error"])
                self.assertEqual(proof["startup_commands"], [])
                self.assertEqual(proof["cmd_vel_examples"], {})

    def test_bad_feedback_sample_outputs_structured_parse_failure(self):
        proof_module = _proof_module()

        proof = proof_module.build_hardware_diagnostics_proof(feedback_sample="not json\n")

        self.assertEqual(proof["status"], "feedback_parse_failed")
        self.assertEqual(proof["feedback_sample"]["status"], "feedback_parse_failed")
        self.assertEqual(proof["feedback_sample"]["raw"], "not json\n")
        self.assertIsNone(proof["feedback_sample"]["parsed"])

    def test_t13_and_hil_risk_flags_are_present(self):
        proof_module = _proof_module()

        proof = proof_module.build_hardware_diagnostics_proof(config={"command_mode": "ros"})
        risk_ids = {flag["id"] for flag in proof["risk_flags"]}

        self.assertIn("hil_required", risk_ids)
        self.assertIn("orange_pi_uart_unconfirmed", risk_ids)
        self.assertIn("ros_mode_t13_unverified", risk_ids)
        self.assertIn("odom_is_command_integration", risk_ids)
        self.assertIn("command_mode_ros_requires_hil", risk_ids)

    def test_cli_writes_json_file_and_returns_zero_for_valid_proof(self):
        proof_module = _proof_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "proof.json"
            with redirect_stdout(io.StringIO()):
                result = proof_module.main(["--output", str(output), "--feedback-interval-ms", "50"])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "software_proof_ready")
        self.assertEqual(payload["startup_commands"][1]["command"], {"T": 142, "cmd": 50})

    def test_cli_locks_exit_codes_for_invalid_config_and_bad_feedback(self):
        proof_module = _proof_module()

        with redirect_stdout(io.StringIO()):
            invalid = proof_module.main(["--command-mode", "pwm"])
        with redirect_stdout(io.StringIO()):
            bad_feedback = proof_module.main(["--feedback-sample-json", "not json"])

        self.assertEqual(invalid, 2)
        self.assertEqual(bad_feedback, 3)


if __name__ == "__main__":
    unittest.main()
