#!/usr/bin/env python3
"""route/task field retest execution pack gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_retest_execution_pack as pack  # noqa: E402


class RouteTaskFieldRetestExecutionPackTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，确保 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def review_decision(self, evidence_ref: str, status: str = "ready_for_operator_terminal_review_not_proven") -> dict:
        # 样本只保留上一轮 terminal review decision 的白名单字段。
        return {
            "schema": "trashbot.route_task_terminal_review_decision.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_terminal_review_decision_gate",
            "same_evidence_ref_required": True,
            "evidence_ref": evidence_ref,
            "status": status,
            "review_decision": "request_field_retest_materials_not_proven",
            "decision_reason": "Terminal review is internally consistent, but field proof is still missing.",
            "owner_handoff": {
                "owner": "Autonomy Algorithm Engineer",
                "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
                "primary_actions_enabled": False,
            },
            "next_required_evidence": [
                "Run a real controlled route/task field retest using the same evidence_ref.",
                "Bring runtime route log, task record, terminal completion signal, and operator notes back to PC review.",
            ],
            "field_retest_request_guidance": [
                "Request field retest package with route status, task record, terminal completion signal, operator note, and recovery context.",
                "Ask the field operator to record what happened, not to mark delivery as complete from this software proof.",
            ],
            "robot_diagnostics_summary": {
                "schema": "trashbot.route_task_terminal_review_decision_summary.v1",
                "evidence_boundary": "software_proof_docker_route_task_terminal_review_decision_gate",
                "status": status,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "real_delivery"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(self, root: Path, payload: dict, evidence_ref: str = "") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        path = self.write_json(root, "review_decision.json", payload)
        artifact, summary, exit_code = pack.build_route_task_field_retest_execution_pack(str(path), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_review_decision_becomes_retest_pack_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary = self.build(root, self.review_decision("run-001"), "run-001")

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_execution_pack.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_execution_pack_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_execution_pack_gate",
        )
        self.assertEqual(artifact["status"], "ready_for_field_retest_execution_pack_not_proven")
        self.assertEqual(artifact["evidence_ref"], "run-001")
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertIn("required_field_materials", artifact)
        self.assertIn("rerun_commands", artifact)
        self.assertIn("operator_handoff", artifact)
        self.assertIn("field_retest_checklist", artifact)
        self.assertIn("real_nav2_fixed_route_run", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_summary_and_wrapper_input_are_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            summary_payload = self.review_decision("run-002")["robot_diagnostics_summary"]
            artifact, _summary = self.build(root, {"payload": {"summary": summary_payload}}, "run-002")

        self.assertEqual(artifact["source_review_decision"]["schema_status"], "supported")
        self.assertEqual(artifact["status"], "ready_for_field_retest_execution_pack_not_proven")
        self.assertEqual(artifact["evidence_ref"], "run-002")

    def test_elevator_source_adds_elevator_materials(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_decision("run-003")
            payload["field_retest_request_guidance"].append("If elevator is involved, capture door state and target floor.")
            artifact, _summary = self.build(root, payload, "run-003")

        material_names = [item["name"] for item in artifact["required_field_materials"]]
        self.assertIn("elevator_door_state", material_names)
        self.assertIn("target_floor_confirmation", material_names)
        self.assertIn("human_assistance_note", material_names)

    def test_missing_and_bad_json_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_artifact, missing_summary, _ = pack.build_route_task_field_retest_execution_pack(
                str(root / "missing.json"),
                "run-004",
            )
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_artifact, _bad_summary, _ = pack.build_route_task_field_retest_execution_pack(str(bad_path), "run-004")

        self.assertEqual(missing_artifact["status"], "blocked_missing_route_task_terminal_review_decision")
        self.assertEqual(bad_artifact["status"], "blocked_bad_json")
        self.assertFalse(missing_artifact["delivery_success"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_unsupported_schema_or_boundary_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_decision("run-005")
            payload["evidence_boundary"] = "software_proof_docker_wrong_gate"
            artifact, _summary = self.build(root, payload, "run-005")

        self.assertEqual(artifact["status"], "blocked_unsupported_schema")
        self.assertEqual(artifact["source_review_decision"]["schema_status"], "unsupported")
        self.assertFalse(artifact["delivery_success"])

    def test_missing_evidence_ref_and_same_ref_false_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_ref = self.review_decision("")
            artifact, _summary = self.build(root, missing_ref)
            same_ref_false = self.review_decision("run-006")
            same_ref_false["same_evidence_ref_required"] = False
            artifact_false, _summary_false = self.build(root, same_ref_false, "run-006")

        self.assertEqual(artifact["status"], "blocked_missing_evidence_ref")
        self.assertEqual(artifact_false["status"], "blocked_same_evidence_ref_not_required")
        self.assertTrue(artifact_false["same_evidence_ref_required"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, _summary = self.build(root, self.review_decision("run-007"), "run-other")

        self.assertEqual(artifact["status"], "blocked_same_evidence_ref_not_required")
        self.assertFalse(artifact["delivery_success"])

    def test_unsafe_copy_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_decision("run-008")
            payload["next_required_evidence"].append(
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response /Users/m4/raw.json"
            )
            artifact, _summary = self.build(root, payload, "run-008")

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
            payload = self.review_decision("run-009")
            payload["delivery_success"] = True
            payload["primary_actions_enabled"] = True
            artifact, summary = self.build(root, payload, "run-009")

        self.assertEqual(artifact["status"], "blocked_success_or_control_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_blocked_review_decision_stays_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, _summary = self.build(
                root,
                self.review_decision("run-010", "blocked_unsafe_copy"),
                "run-010",
            )

        self.assertEqual(artifact["status"], "blocked_review_decision_not_ready")
        self.assertIn("Repair the terminal review decision source", artifact["operator_handoff"]["handoff_note"])


if __name__ == "__main__":
    unittest.main()
