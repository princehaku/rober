#!/usr/bin/env python3
"""route/task terminal review decision gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_terminal_review_decision as decision  # noqa: E402


class RouteTaskTerminalReviewDecisionTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试材料只写临时 JSON，不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def terminal_rehearsal(self, evidence_ref: str, verdict: str = "ready_for_terminal_completion_rehearsal_not_proven") -> dict:
        # terminal rehearsal 样本只保留 review decision 所需的白名单字段。
        return {
            "schema": "trashbot.route_task_terminal_completion_rehearsal.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_terminal_completion_rehearsal_gate",
            "evidence_ref": evidence_ref,
            "terminal_verdict": verdict,
            "dropoff": {"material_status": "material_present_not_proven", "completion_claimed": True},
            "cancel": {"material_status": "not_provided", "completion_claimed": False},
            "failure_reason": "",
            "recovery_reason": "",
            "operator_next_steps": ["Preserve same evidence_ref for the next field material review."],
            "robot_diagnostics_summary": {
                "schema": "trashbot.route_task_terminal_completion_rehearsal_summary.v1",
                "evidence_boundary": "software_proof_docker_route_task_terminal_completion_rehearsal_gate",
                "terminal_verdict": verdict,
                "evidence_ref": evidence_ref,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "mobile_readonly_summary": {
                "terminal_verdict": verdict,
                "evidence_ref": evidence_ref,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_delivery", "real_terminal_completion"],
            "software_proof": "software_proof",
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(self, root: Path, payload: dict, evidence_ref: str = "") -> tuple[dict, dict]:
        # 公共 helper 让测试聚焦 fail-closed 规则，而不是文件读写样板。
        path = self.write_json(root, "terminal.json", payload)
        artifact, summary, exit_code = decision.build_route_task_terminal_review_decision(str(path), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_review_decision_is_not_proven_and_readonly(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary = self.build(root, self.terminal_rehearsal("run-001"), "run-001")

        self.assertEqual(artifact["schema"], "trashbot.route_task_terminal_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_terminal_review_decision_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_terminal_review_decision_gate",
        )
        self.assertEqual(artifact["status"], "ready_for_operator_terminal_review_not_proven")
        self.assertEqual(artifact["review_decision"], "request_field_retest_materials_not_proven")
        self.assertEqual(artifact["evidence_ref"], "run-001")
        self.assertIn("owner_handoff", artifact)
        self.assertIn("next_required_evidence", artifact)
        self.assertIn("field_retest_request_guidance", artifact)
        self.assertIn("software_proof", artifact["software_proof"])
        self.assertIn("real_terminal_completion", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_summary_input_is_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = {
                "schema": "trashbot.route_task_terminal_completion_rehearsal_summary.v1",
                "schema_version": 1,
                "evidence_boundary": "software_proof_docker_route_task_terminal_completion_rehearsal_gate",
                "status": "failed_with_recovery_reason_not_proven",
                "evidence_ref": "run-002",
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            artifact, _summary = self.build(root, payload, "run-002")

        self.assertEqual(artifact["status"], "review_failed_terminal_recovery_before_field_retest")
        self.assertEqual(artifact["review_decision"], "request_field_retest_after_recovery_review")

    def test_missing_and_bad_json_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, _summary, _ = decision.build_route_task_terminal_review_decision(str(root / "missing.json"), "run-003")
            self.assertEqual(artifact["status"], "blocked_missing_route_task_terminal_review_decision")

            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            artifact, _summary, _ = decision.build_route_task_terminal_review_decision(str(bad_path), "run-003")

        self.assertEqual(artifact["status"], "blocked_bad_json")
        self.assertFalse(artifact["delivery_success"])

    def test_unsupported_schema_or_boundary_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.terminal_rehearsal("run-004")
            payload["evidence_boundary"] = "software_proof_docker_wrong_gate"
            artifact, _summary = self.build(root, payload, "run-004")

        self.assertEqual(artifact["status"], "blocked_unsupported_schema")
        self.assertEqual(artifact["review_decision"], "rerun_supported_terminal_completion_rehearsal")

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, _summary = self.build(root, self.terminal_rehearsal("run-005"), "run-other")

        self.assertEqual(artifact["status"], "blocked_mismatch_evidence_ref")
        self.assertTrue(artifact["materials_status"]["mismatch_reasons"])

    def test_unsafe_copy_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.terminal_rehearsal("run-006")
            payload["robot_diagnostics_summary"]["operator_note"] = (
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 "
                "raw robot response /Users/m4/private/full.json HIL"
            )
            artifact, _summary = self.build(root, payload, "run-006")

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["status"], "blocked_unsafe_copy")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)

    def test_success_or_primary_action_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.terminal_rehearsal("run-007")
            payload["primary_actions_enabled"] = True
            artifact, summary = self.build(root, payload, "run-007")

        self.assertEqual(artifact["status"], "blocked_success_or_control_claim")
        self.assertEqual(artifact["review_decision"], "remove_success_or_control_claims_before_review")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_blocked_rehearsal_requests_repair_before_retest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, _summary = self.build(
                root,
                self.terminal_rehearsal("run-008", "blocked_missing_route_task_terminal_completion_rehearsal"),
                "run-008",
            )

        self.assertEqual(artifact["status"], "requires_rehearsal_repair_before_field_retest")
        self.assertEqual(artifact["review_decision"], "repair_terminal_rehearsal_before_retest_request")


if __name__ == "__main__":
    unittest.main()
