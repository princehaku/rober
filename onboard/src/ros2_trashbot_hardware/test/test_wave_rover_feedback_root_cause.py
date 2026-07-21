import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


PACKAGE_SRC = Path(__file__).resolve().parents[1]
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))


def _module():
    return importlib.import_module("ros2_trashbot_hardware.wave_rover_feedback_root_cause")


def _write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_vendor_fixture(root: Path) -> Path:
    vendor_root = root / "waveshare_wave_rover" / "WAVE_ROVER_V0.9"
    vendor_root.mkdir(parents=True, exist_ok=True)
    (vendor_root / "json_cmd.h").write_text(
        "\n".join(
            [
                "#define FEEDBACK_BASE_INFO 1001",
                "#define CMD_PWM_INPUT 11",
                "#define CMD_ROS_CTRL 13",
                "#define CMD_BASE_FEEDBACK 130",
                "#define CMD_BASE_FEEDBACK_FLOW 131",
                "#define CMD_MM_TYPE_SET 900",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (vendor_root / "uart_ctrl.h").write_text(
        "\n".join(
            [
                "case CMD_PWM_INPUT:",
                'leftCtrl(jsonCmdReceive["L"]);',
                'rightCtrl(jsonCmdReceive["R"]);',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (vendor_root / "movtion_module.h").write_text(
        "\n".join(
            [
                "void initEncoders() {}",
                "void getLeftSpeed() {}",
                "void getRightSpeed() {}",
                "if (mainType != 3) {}",
                "speedGetA = pwmIntA;",
                "speedGetB = pwmIntB;",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (vendor_root / "ugv_advance.h").write_text(
        'jsonInfoHttp["L"] = speedGetA;\njsonInfoHttp["R"] = speedGetB;\n',
        encoding="utf-8",
    )
    (vendor_root / "ugv_config.h").write_text("byte mainType = 1;\n", encoding="utf-8")
    (vendor_root / "WAVE_ROVER_V0.9.ino").write_text(
        "initEncoders();\ngetLeftSpeed();\ngetRightSpeed();\nif (baseFeedbackFlow) {}\n",
        encoding="utf-8",
    )
    base_ctrl = vendor_root.parent / "ugv_rpi" / "base_ctrl.py"
    base_ctrl.parent.mkdir(parents=True, exist_ok=True)
    base_ctrl.write_text('self.ser.write((json.dumps(data) + \'\\n\').encode("utf-8"))\n', encoding="utf-8")
    return vendor_root


def _command_row(timestamp: float, left: int, right: int):
    return {
        "schema": "trashbot.wave_rover.command_debug.v1",
        "observed_at_unix_s": timestamp,
        "sent": True,
        "vendor_command": {"T": 11, "L": left, "R": right},
    }


def _feedback_row(timestamp: float, left: int, right: int):
    return {
        "schema": "trashbot.wave_rover.feedback_debug.v1",
        "observed_at_unix_s": timestamp,
        "left_speed": float(left),
        "right_speed": float(right),
        "vendor_frame": {"T": 1001, "L": left, "R": right, "r": 0, "p": 0, "y": "null", "v": 11.8},
    }


def _write_v8_fixture(root: Path) -> Path:
    artifact_dir = root / "v8"
    acceptance = {
        "schema": "trashbot.o1.current_wheel_feedback_hil.acceptance.v1",
        "authorization_id": "ceo_20260721_0651_current_wheel_feedback_hil_v8",
        "authorization_status": "consumed_no_retry",
        "attempt_id": "o1-current-wheel-feedback-hil-v8-attempt-1",
        "pre_stop": 1,
        "nonzero": 1,
        "post_stop": 1,
        "retry": 0,
        "no_retry": True,
        "nonzero_transport_response_accepted": True,
        "during_motion_t1001_observed": True,
        "during_motion_t1001_lr_nonzero_proven": False,
        "during_motion_t1001_observed_pairs": [[0, 0], [0, 0], [0, 0]],
        "post_stop_t1001_observed": True,
        "post_stop_t1001_lr_zero_proven": True,
        "t130_request_observed": False,
        "t13_wire_observed": False,
        "feedback_evidence_source_class": "bridge_debug_serial_derived",
        "raw_serial_byte_capture": False,
        "final_stopped": True,
        "hil_pass": False,
        "safe_to_control": False,
        "route_execution_success": False,
        "delivery_success": False,
    }
    _write_json(artifact_dir / "acceptance_summary.json", acceptance)
    _write_json(
        artifact_dir / "during_motion_t1001.json",
        {"T": 1001, "L": 0, "R": 0, "observed_at_unix_s": 100.11},
    )
    _write_json(
        artifact_dir / "post_stop_t1001.json",
        {"T": 1001, "L": 0, "R": 0, "observed_at_unix_s": 100.35},
    )
    _write_json(
        artifact_dir / "final_base_status.json",
        {
            "latest_command": {"vendor_command": {"L": 0, "R": 0, "T": 11}},
            "latest_t1001": {"T": 1001, "L": 0, "R": 0},
            "wheel_feedback_nonzero_frame_count": 0,
            "final_stopped": True,
        },
    )
    commands = [_command_row(100.00 + index * 0.05, 164, 164) for index in range(6)]
    commands.extend([_command_row(100.30, 0, 0), _command_row(100.40, 0, 0)])
    _write_jsonl(artifact_dir / "live_bridge_command_delta.jsonl", commands)
    feedback = [
        _feedback_row(100.01, 0, 0),
        _feedback_row(100.11, 0, 0),
        _feedback_row(100.21, 0, 0),
        _feedback_row(100.35, 0, 0),
    ]
    _write_jsonl(artifact_dir / "live_bridge_feedback_delta.jsonl", feedback)
    return artifact_dir


def _valid_runtime_inventory():
    return {
        "schema": "trashbot.wave_rover.readonly_runtime_inventory.v1",
        "readonly_only": True,
        "readonly_allowlist": ["systemctl_show", "systemctl_cat", "ps", "sha256sum"],
        "commands": [
            {
                "category": "systemctl_show",
                "command": "systemctl show trashbot-esp32-bridge.service --no-pager",
                "exit_code": 0,
                "stdout_summary": "active service; PID redacted",
                "stderr_summary": "",
            }
        ],
        "observations": {
            "runtime_main_type": None,
            "firmware_identity": None,
            "bridge_command_mode": "pwm",
            "deployed_bridge_sha256": "a" * 64,
        },
        "safety_counters": {
            "motion": 0,
            "control": 0,
            "stop": 0,
            "nonzero": 0,
            "service_mutation": 0,
            "uart_write": 0,
            "firmware_mutation": 0,
        },
    }


class WaveRoverFeedbackRootCauseTest(unittest.TestCase):
    def _fixture(self, tmpdir: str):
        root = Path(tmpdir)
        return _write_v8_fixture(root), _write_vendor_fixture(root)

    def test_valid_v8_and_vendor_sources_rank_encoder_path_first(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            result = module.build_root_cause_diagnostic(artifacts, vendor)

        self.assertTrue(result["input_valid"])
        self.assertEqual(result["status"], "diagnostic_complete_fail_closed")
        self.assertEqual(result["primary_classification"], "encoder_update_path_not_observed")
        self.assertEqual(result["root_cause_candidates"][0]["candidate_id"], "encoder_update_path_not_observed")
        self.assertEqual(result["v8_validation"]["historical_feedback_counts"]["during_window_t1001_frames"], 3)
        self.assertEqual(result["v8_validation"]["historical_bridge_command_counts"]["nonzero_t11_frames"], 6)
        self.assertFalse(result["hil_pass"])
        self.assertFalse(result["safe_to_control"])
        self.assertEqual(result["motion_command_count"], 0)
        self.assertEqual(result["service_mutation_count"], 0)
        self.assertFalse(result["unique_next_maintenance_action"]["motion_authorized_by_this_diagnostic"])

    def test_missing_v8_input_fails_closed(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            (artifacts / "during_motion_t1001.json").unlink()
            result = module.build_root_cause_diagnostic(artifacts, vendor)

        self.assertFalse(result["input_valid"])
        self.assertEqual(result["primary_classification"], "artifact_inconsistent_or_invalid")
        self.assertTrue(any(error.startswith("missing_input:during_motion_t1001.json") for error in result["validation_errors"]))

    def test_v8_count_conflict_fails_closed(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            acceptance_path = artifacts / "acceptance_summary.json"
            acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
            acceptance["retry"] = 1
            _write_json(acceptance_path, acceptance)
            result = module.build_root_cause_diagnostic(artifacts, vendor)

        self.assertFalse(result["input_valid"])
        self.assertTrue(any("v8_identity_or_count_conflict:retry" in error for error in result["validation_errors"]))

    def test_invalid_json_fails_closed(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            (artifacts / "post_stop_t1001.json").write_text("{not-json\n", encoding="utf-8")
            result = module.build_root_cause_diagnostic(artifacts, vendor)

        self.assertFalse(result["input_valid"])
        self.assertTrue(any(error.startswith("invalid_json:post_stop_t1001.json") for error in result["validation_errors"]))

    def test_invalid_jsonl_line_fails_closed(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            with (artifacts / "live_bridge_feedback_delta.jsonl").open("a", encoding="utf-8") as stream:
                stream.write("not-json\n")
            result = module.build_root_cause_diagnostic(artifacts, vendor)

        self.assertFalse(result["input_valid"])
        self.assertTrue(any(error.startswith("invalid_jsonl:live_bridge_feedback_delta.jsonl") for error in result["validation_errors"]))

    def test_dangerous_true_safety_field_fails_closed(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            acceptance_path = artifacts / "acceptance_summary.json"
            acceptance = json.loads(acceptance_path.read_text(encoding="utf-8"))
            acceptance["safe_to_control"] = True
            _write_json(acceptance_path, acceptance)
            result = module.build_root_cause_diagnostic(artifacts, vendor)

        self.assertFalse(result["input_valid"])
        self.assertIn("dangerous_or_missing_v8_safety_field:safe_to_control:True", result["validation_errors"])
        self.assertFalse(result["safe_to_control"])

    def test_missing_vendor_symbol_fails_closed(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            motion_path = vendor / "movtion_module.h"
            motion_path.write_text(motion_path.read_text(encoding="utf-8").replace("speedGetA = pwmIntA;", ""), encoding="utf-8")
            result = module.build_root_cause_diagnostic(artifacts, vendor)

        self.assertFalse(result["input_valid"])
        self.assertIn("vendor_code_path_missing:left_pwm_value_assignment", result["validation_errors"])

    def test_conflicting_vendor_define_fails_closed(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            json_cmd = vendor / "json_cmd.h"
            json_cmd.write_text(json_cmd.read_text(encoding="utf-8") + "#define CMD_PWM_INPUT 12\n", encoding="utf-8")
            result = module.build_root_cause_diagnostic(artifacts, vendor)

        self.assertFalse(result["input_valid"])
        self.assertTrue(any(error.startswith("vendor_define_conflict:CMD_PWM_INPUT") for error in result["validation_errors"]))

    def test_runtime_inventory_missing_fields_fails_closed(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            inventory_path = Path(tmpdir) / "inventory.json"
            _write_json(inventory_path, {"schema": "trashbot.wave_rover.readonly_runtime_inventory.v1"})
            result = module.build_root_cause_diagnostic(artifacts, vendor, inventory_path)

        self.assertFalse(result["input_valid"])
        self.assertIn("runtime_inventory_missing_field:observations", result["validation_errors"])
        self.assertIn("runtime_inventory_safety_counters_not_object", result["validation_errors"])

    def test_valid_inventory_keeps_unobserved_runtime_facts_explicit(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            inventory_path = Path(tmpdir) / "inventory.json"
            _write_json(inventory_path, _valid_runtime_inventory())
            result = module.build_root_cause_diagnostic(artifacts, vendor, inventory_path)

        self.assertTrue(result["input_valid"])
        candidates = {item["candidate_id"]: item for item in result["root_cause_candidates"]}
        self.assertEqual(candidates["runtime_main_type_not_observed"]["status"], "not_observed")
        self.assertEqual(candidates["runtime_firmware_identity_not_observed"]["status"], "not_observed")
        self.assertEqual(result["runtime_inventory_validation"]["safety_counters"]["uart_write"], 0)

    def test_runtime_inventory_rejects_mutation_hidden_under_readonly_category(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            inventory = _valid_runtime_inventory()
            inventory["commands"][0]["command"] = "systemctl restart trashbot-esp32-bridge.service"
            inventory_path = Path(tmpdir) / "inventory.json"
            _write_json(inventory_path, inventory)
            result = module.build_root_cause_diagnostic(artifacts, vendor, inventory_path)

        self.assertFalse(result["input_valid"])
        self.assertIn(
            "runtime_inventory_command_text_rejected:0:systemctl_show",
            result["validation_errors"],
        )

    def test_cli_writes_deterministic_safe_output_and_returns_zero(self):
        module = _module()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts, vendor = self._fixture(tmpdir)
            output = Path(tmpdir) / "result.json"
            result_code = module.main(
                [
                    "--v8-artifact-dir",
                    str(artifacts),
                    "--vendor-source-root",
                    str(vendor),
                    "--output",
                    str(output),
                ]
            )
            result = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result_code, 0)
        self.assertEqual(result["schema"], "trashbot.wave_rover.feedback_root_cause_diagnostic.v1")
        self.assertFalse(result["route_execution_success"])
        self.assertFalse(result["delivery_success"])
        self.assertEqual(result["firmware_mutation_count"], 0)


if __name__ == "__main__":
    unittest.main()
