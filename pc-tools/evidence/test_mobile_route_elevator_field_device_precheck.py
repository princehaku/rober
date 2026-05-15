#!/usr/bin/env python3
"""mobile route/elevator field-device precheck gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import mobile_route_elevator_field_device_precheck as precheck  # noqa: E402


class MobileRouteElevatorFieldDevicePrecheckTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 临时文件让测试不依赖 ROS2、Nav2、真实电梯、真实设备或云。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def handoff_payload(self, evidence_ref: str) -> dict:
        # handoff 样本来自上一轮 gate；它仍只是 software proof，不是现场通过。
        return {
            "schema": "trashbot.route_elevator_field_session_handoff.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_route_elevator_field_session_handoff_gate",
            "handoff_verdict": "ready_for_field_session_handoff_not_proven",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched_same_evidence_ref",
            "mobile_readonly_summary": {
                "schema": "trashbot.route_elevator_field_session_handoff_summary.v1",
                "evidence_boundary": "software_proof_docker_route_elevator_field_session_handoff_gate",
                "status": "ready_for_field_session_handoff_not_proven",
                "evidence_ref": evidence_ref,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "real_elevator_door_state", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build_from_handoff(self, payload: dict, evidence_ref: str) -> tuple[dict, dict, int]:
        # 公共 helper 让 case 聚焦 schema、same-evidence-ref 和 fail-closed 规则。
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            handoff_path = self.write_json(root, "handoff.json", payload)
            return precheck.build_precheck(str(handoff_path), evidence_ref)

    def test_ready_precheck_not_proven_with_same_evidence_ref(self):
        artifact, summary, exit_code = self.build_from_handoff(self.handoff_payload("run-001"), "run-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.mobile_route_elevator_field_device_precheck.v1")
        self.assertEqual(summary["schema"], "trashbot.mobile_route_elevator_field_device_precheck_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_mobile_route_elevator_field_device_precheck_gate",
        )
        self.assertEqual(artifact["precheck_verdict"], "ready_for_field_device_precheck_not_proven")
        self.assertEqual(artifact["same_evidence_ref_status"], "matched_same_evidence_ref")
        self.assertIn("door_state.json", summary["required_route_elevator_field_material_names"])
        self.assertIn("real_device_browser_loaded_current_mobile_web", summary["device_pwa_observation_checklist_names"])
        self.assertIn("real_phone_device_or_browser", artifact["not_proven"])
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["real_device_observed"])
        self.assertFalse(artifact["pwa_install_prompt_observed"])
        self.assertFalse(artifact["route_elevator_field_pass"])
        self.assertFalse(artifact["dropoff_completion"])
        self.assertFalse(artifact["cancel_completion"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertEqual(artifact["mobile_copy_summary"]["schema"], "trashbot.mobile_route_elevator_field_device_precheck_copy.v1")

    def test_missing_bad_json_and_unsupported_contract_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_artifact, _, missing_exit = precheck.build_precheck(str(root / "missing.json"), "run-002")

            bad_json = root / "bad.json"
            bad_json.write_text("{bad json", encoding="utf-8")
            bad_artifact, _, bad_exit = precheck.build_precheck(str(bad_json), "run-002")

            unsupported = self.handoff_payload("run-002")
            unsupported["schema"] = "trashbot.unsupported_handoff.v99"
            unsupported_artifact, _, unsupported_exit = self.build_from_handoff(unsupported, "run-002")

        self.assertEqual(missing_exit, 2)
        self.assertEqual(bad_exit, 2)
        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(missing_artifact["precheck_verdict"], "blocked_missing_inputs")
        self.assertEqual(bad_artifact["precheck_verdict"], "blocked_missing_inputs")
        self.assertEqual(unsupported_artifact["precheck_verdict"], "blocked_invalid_input")
        self.assertIn("route_elevator_field_session_handoff:unsupported_schema", unsupported_artifact["missing_or_blocked"])

    def test_evidence_ref_mismatch_fails_closed(self):
        artifact, summary, exit_code = self.build_from_handoff(self.handoff_payload("run-source"), "run-target")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["precheck_verdict"], "blocked_evidence_ref_mismatch")
        self.assertIn("route_elevator_field_session_handoff:evidence_ref", artifact["missing_or_blocked"])
        self.assertFalse(summary["delivery_success"])

    def test_success_and_control_claims_fail_closed(self):
        delivery_claim = self.handoff_payload("run-003")
        delivery_claim["delivery_success"] = True
        action_claim = self.handoff_payload("run-003")
        action_claim["mobile_readonly_summary"]["primary_actions_enabled"] = True

        delivery_artifact, _, delivery_exit = self.build_from_handoff(delivery_claim, "run-003")
        action_artifact, _, action_exit = self.build_from_handoff(action_claim, "run-003")

        self.assertEqual(delivery_exit, 2)
        self.assertEqual(action_exit, 2)
        self.assertEqual(delivery_artifact["precheck_verdict"], "blocked_success_or_control_claim")
        self.assertEqual(action_artifact["precheck_verdict"], "blocked_success_or_control_claim")
        self.assertFalse(delivery_artifact["delivery_success"])
        self.assertFalse(action_artifact["primary_actions_enabled"])

    def test_validate_existing_summary_accepts_not_proven_and_blocks_true_flags(self):
        ready_artifact, summary, _ = self.build_from_handoff(self.handoff_payload("run-004"), "run-004")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            summary_path = self.write_json(root, "summary.json", summary)
            validated, validated_summary, validated_exit = precheck.validate_precheck(str(summary_path), "run-004")

            bad = dict(summary)
            bad["real_device_observed"] = True
            bad_path = self.write_json(root, "bad_summary.json", bad)
            blocked, _, blocked_exit = precheck.validate_precheck(str(bad_path), "run-004")

        self.assertEqual(ready_artifact["precheck_verdict"], "ready_for_field_device_precheck_not_proven")
        self.assertEqual(validated_exit, 0)
        self.assertEqual(validated["precheck_verdict"], "validated_field_device_precheck_not_proven")
        self.assertEqual(validated_summary["same_evidence_ref_status"], "matched_same_evidence_ref")
        self.assertEqual(blocked_exit, 2)
        self.assertEqual(blocked["precheck_verdict"], "blocked_invalid_precheck")
        self.assertIn("success_or_control_claim", blocked["missing_or_blocked"])

    def test_unsafe_copy_is_redacted_and_blocked(self):
        payload = self.handoff_payload("run-005")
        payload["operator_note"] = "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
        artifact, _, exit_code = self.build_from_handoff(payload, "run-005")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["precheck_verdict"], "blocked_unsafe_copy")
        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("raw robot response", encoded)
        self.assertFalse(artifact["delivery_success"])


if __name__ == "__main__":
    unittest.main()
