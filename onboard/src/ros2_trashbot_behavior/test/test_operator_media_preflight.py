import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


BEHAVIOR_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BEHAVIOR_PACKAGE_ROOT))

from ros2_trashbot_behavior.operator_gateway_http import status_payload
from ros2_trashbot_behavior.operator_media_preflight import (
    O7_BOARD_MEDIA_PREFLIGHT_SCHEMA,
    build_o7_board_media_preflight,
)
from ros2_trashbot_behavior.operator_realtime_status import build_o7_board_realtime_status


class OperatorMediaPreflightTest(unittest.TestCase):
    def test_default_preflight_does_not_touch_devices_or_claim_success(self):
        with mock.patch("pathlib.Path.exists", side_effect=AssertionError("device path touched")):
            summary = build_o7_board_media_preflight()

        self.assertEqual(summary["schema"], O7_BOARD_MEDIA_PREFLIGHT_SCHEMA)
        self.assertEqual(summary["overall_state"], "blocked")
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["device_probe_allowed"])
        self.assertFalse(summary["device_probe_attempted"])
        self.assertIn("not_proven", json.dumps(summary, sort_keys=True))
        self.assertNotIn("success", json.dumps(summary, sort_keys=True).lower())

    def test_unsafe_inputs_are_redacted_and_blocked(self):
        summary = build_o7_board_media_preflight(
            camera_path="/dev/ttyUSB0",
            audio_input_path="/cmd_vel",
            extra_paths=["Authorization Bearer token"],
        )
        encoded = json.dumps(summary, ensure_ascii=False, sort_keys=True)

        self.assertIn("redacted_unsafe_input", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Authorization", encoded)
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("camera_path", summary["blocked"])

    def test_missing_explicit_path_blocks_without_device_probe(self):
        missing_path = "/tmp/trashbot-media-preflight-missing-file"
        summary = build_o7_board_media_preflight(camera_path=missing_path)
        camera = summary["path_checks"][0]

        self.assertEqual(camera["state"], "blocked")
        self.assertEqual(camera["reason"], "configured_path_missing")
        self.assertFalse(camera["device_probe_attempted"])
        self.assertIn("resolve_blocked_preflight_items", summary["next_required_evidence"])

    def test_allow_device_probe_is_shallow_and_still_not_runtime_pass(self):
        with tempfile.NamedTemporaryFile() as handle:
            summary = build_o7_board_media_preflight(
                camera_path=handle.name,
                allow_device_probe=True,
            )
        camera = summary["path_checks"][0]

        self.assertTrue(summary["device_probe_allowed"])
        self.assertTrue(camera["device_probe_attempted"])
        self.assertEqual(camera["device_probe_result"], "shallow_path_check_only")
        self.assertEqual(camera["state"], "not_proven")
        self.assertIn("real_camera_video_source", summary["not_proven"])

    def test_realtime_status_embeds_media_preflight_next_evidence_fail_closed(self):
        preflight = build_o7_board_media_preflight(camera_path="/tmp/does-not-exist-media")
        status = build_o7_board_realtime_status({"o7_board_media_preflight": preflight})

        self.assertEqual(status["media_preflight"]["schema"], O7_BOARD_MEDIA_PREFLIGHT_SCHEMA)
        self.assertIn("resolve_blocked_preflight_items", status["next_required_evidence"])
        self.assertFalse(status["primary_actions_enabled"])
        self.assertFalse(status["manual_control_policy"]["safe_to_control"])
        self.assertFalse(status["nav_goal_policy"]["safe_to_control"])

    def test_status_payload_accepts_preflight_source_without_enabling_control(self):
        payload = status_payload(
            "waiting_for_trash",
            o7_board_media_preflight={"overall_state": "not_proven"},
        )
        status = payload["o7_board_realtime_status"]

        self.assertEqual(status["media_preflight"]["overall_state"], "not_proven")
        self.assertFalse(status["primary_actions_enabled"])
        self.assertFalse(status["manual_control_policy"]["enabled"])
        self.assertFalse(status["nav_goal_policy"]["enabled"])

    def test_realtime_status_redacts_unsafe_external_media_preflight_source(self):
        malicious = {
            "overall_state": "not_proven",
            "path_checks": [
                {
                    "name": "camera_path",
                    "path": "/dev/ttyUSB0",
                    "detail": "Authorization Bearer token on /cmd_vel",
                }
            ],
            "capabilities": {
                "rtc": {
                    "state": "not_proven",
                    "raw_topic": "/cmd_vel",
                    "safe_to_control": True,
                    "primary_actions_enabled": True,
                }
            },
            "blocked": ["token leaked from /dev/ttyUSB0"],
            "not_proven": ["Bearer secret password"],
            "next_required_evidence": ["Authorization header and /cmd_vel trace"],
        }

        status = build_o7_board_realtime_status({"o7_board_media_preflight": malicious})
        encoded = json.dumps(status, ensure_ascii=False, sort_keys=True)

        self.assertIn("redacted_unsafe_input", encoded)
        self.assertIn("unsafe_media_preflight_source_redacted", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Authorization", encoded)
        self.assertNotIn("Bearer", encoded)
        self.assertNotIn(" token ", f" {encoded} ")
        self.assertNotIn("secret", encoded.lower())
        self.assertNotIn("password", encoded.lower())
        self.assertFalse(status["media_preflight"]["safe_to_control"])
        self.assertFalse(status["media_preflight"]["primary_actions_enabled"])
        self.assertFalse(status["primary_actions_enabled"])
        self.assertFalse(status["manual_control_policy"]["safe_to_control"])
        self.assertFalse(status["nav_goal_policy"]["safe_to_control"])

    def test_status_payload_redacts_unsafe_media_preflight_source(self):
        payload = status_payload(
            "waiting_for_trash",
            o7_board_media_preflight={
                "path_checks": [{"path": "/cmd_vel", "credential": "Authorization Bearer token"}],
                "next_required_evidence": ["/dev/ttyUSB0 raw smoke"],
                "primary_actions_enabled": True,
                "safe_to_control": True,
            },
        )
        encoded = json.dumps(payload["o7_board_realtime_status"], ensure_ascii=False, sort_keys=True)

        self.assertIn("redacted_unsafe_input", encoded)
        self.assertIn("unsafe_media_preflight_source_redacted", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Authorization", encoded)
        self.assertNotIn("Bearer", encoded)
        self.assertNotIn("token", encoded.lower())
        self.assertFalse(payload["o7_board_realtime_status"]["primary_actions_enabled"])

    def test_cli_default_outputs_stable_safe_json(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ros2_trashbot_behavior.operator_media_preflight",
            ],
            cwd=str(BEHAVIOR_PACKAGE_ROOT),
            check=True,
            text=True,
            capture_output=True,
        )
        summary = json.loads(result.stdout)
        encoded = json.dumps(summary, sort_keys=True)

        self.assertEqual(summary["schema"], O7_BOARD_MEDIA_PREFLIGHT_SCHEMA)
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn(summary["overall_state"], {"blocked", "not_proven"})
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("success", encoded.lower())


if __name__ == "__main__":
    unittest.main()
