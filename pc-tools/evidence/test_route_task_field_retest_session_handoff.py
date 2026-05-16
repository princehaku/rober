#!/usr/bin/env python3
"""route/task field retest session handoff gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_retest_session_handoff as handoff  # noqa: E402


class RouteTaskFieldRetestSessionHandoffTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，确保 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def execution_pack(self, evidence_ref: str, status: str = "ready_for_field_retest_execution_pack_not_proven") -> dict:
        # 样本覆盖本轮要求的八类现场回填材料，但仍全部是 not_proven。
        materials = [
            "nav2_fixed_route_runtime_log",
            "route_completion_signal",
            "task_record",
            "door_state",
            "target_floor_confirmation",
            "human_assistance_note",
            "dropoff_or_cancel_completion",
            "delivery_result",
        ]
        return {
            "schema": "trashbot.route_task_field_retest_execution_pack.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_execution_pack_gate",
            "boundary": "software_proof_docker_route_task_field_retest_execution_pack_gate",
            "status": status,
            "execution_pack_verdict": status,
            "same_evidence_ref_required": True,
            "evidence_ref": evidence_ref,
            "required_field_materials": [{"name": name} for name in materials],
            "rerun_commands": [
                "rerun route_task_terminal_completion_rehearsal.py after field materials are attached",
                "rerun route_task_terminal_review_decision.py after terminal rehearsal is regenerated",
            ],
            "operator_handoff": {
                "owner": "Autonomy Algorithm Engineer",
                "primary_actions_enabled": False,
            },
            "field_retest_checklist": [
                "Confirm every field material uses the same evidence_ref.",
                "Collect facts and failure reasons only.",
            ],
            "not_proven": ["real_nav2_fixed_route_run", "real_delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(self, root: Path, payload: dict, evidence_ref: str = "run-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        path = self.write_json(root, "execution_pack.json", payload)
        artifact, summary, exit_code = handoff.build_route_task_field_retest_session_handoff(
            str(path),
            evidence_ref,
            "Autonomy Algorithm Engineer",
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_execution_pack_becomes_session_handoff_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary = self.build(root, self.execution_pack("run-001"), "run-001")

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_session_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_session_handoff_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_session_handoff_gate",
        )
        self.assertEqual(artifact["status"], "ready_for_field_retest_session_handoff_not_proven")
        self.assertEqual(artifact["evidence_ref"], "run-001")
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertIn("operator_handoff", artifact)
        self.assertIn("material_placeholders", artifact)
        self.assertIn("rerun_commands", artifact)
        self.assertIn("field_callback_checklist", artifact)
        self.assertIn("safe_copy", artifact)
        self.assertIn("fail_closed_summary", artifact)
        self.assertIn("real_nav2_fixed_route_run", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("nav2_fixed_route_runtime_log", summary["required_field_materials"])
        self.assertIn("delivery_result", summary["required_field_materials"])

    def test_summary_and_wrapper_input_are_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            summary_payload = {
                "schema": "trashbot.route_task_field_retest_execution_pack_summary.v1",
                "schema_version": 1,
                "evidence_boundary": "software_proof_docker_route_task_field_retest_execution_pack_gate",
                "status": "ready_for_field_retest_execution_pack_not_proven",
                "evidence_ref": "run-002",
                "same_evidence_ref_required": True,
                "required_field_materials": list(handoff.REQUIRED_MATERIAL_NAMES),
                "rerun_commands": ["rerun route_task_field_retest_execution_pack.py --once-json"],
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            artifact, _summary = self.build(root, {"payload": {"summary": summary_payload}}, "run-002")

        self.assertEqual(artifact["source_execution_pack"]["schema_status"], "supported")
        self.assertEqual(artifact["status"], "ready_for_field_retest_session_handoff_not_proven")
        self.assertEqual(artifact["evidence_ref"], "run-002")

    def test_missing_required_materials_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.execution_pack("run-003")
            payload["required_field_materials"] = [{"name": "nav2_fixed_route_runtime_log"}]
            artifact, summary = self.build(root, payload, "run-003")

        self.assertEqual(artifact["status"], "blocked_missing_required_materials")
        self.assertIn("route_completion_signal", artifact["source_execution_pack"]["missing_required_materials"])
        self.assertIn("delivery_result", summary["missing_required_materials"])
        self.assertFalse(artifact["delivery_success"])

    def test_placeholder_only_materials_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.execution_pack("run-004")
            payload["required_field_materials"] = [{"name": "TBD placeholder"}, {"name": "<sample>"}]
            artifact, _summary = self.build(root, payload, "run-004")

        self.assertEqual(artifact["status"], "blocked_placeholder_only_materials")
        self.assertTrue(artifact["source_execution_pack"]["placeholder_only_materials"])

    def test_missing_bad_json_and_unsupported_schema_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_artifact, missing_summary, _ = handoff.build_route_task_field_retest_session_handoff(
                str(root / "missing.json"),
                "run-005",
                "Autonomy Algorithm Engineer",
            )
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_artifact, _bad_summary, _ = handoff.build_route_task_field_retest_session_handoff(
                str(bad_path),
                "run-005",
            )
            unsupported = self.execution_pack("run-005")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _unsupported_summary = self.build(root, unsupported, "run-005")

        self.assertEqual(missing_artifact["status"], "blocked_missing_route_task_field_retest_execution_pack")
        self.assertEqual(bad_artifact["status"], "blocked_bad_json")
        self.assertEqual(unsupported_artifact["status"], "blocked_unsupported_schema")
        self.assertFalse(missing_artifact["delivery_success"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_missing_evidence_ref_and_same_ref_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_ref = self.execution_pack("")
            missing_ref_artifact, _summary = self.build(root, missing_ref, "")
            mismatch_artifact, _mismatch_summary = self.build(root, self.execution_pack("run-006"), "other-run")

        self.assertEqual(missing_ref_artifact["status"], "blocked_missing_evidence_ref")
        self.assertEqual(mismatch_artifact["status"], "blocked_same_evidence_ref_not_required")
        self.assertTrue(mismatch_artifact["same_evidence_ref_required"])

    def test_unsafe_copy_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.execution_pack("run-007")
            payload["operator_handoff"]["handoff_note"] = (
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response /Users/m4/raw.json"
            )
            artifact, _summary = self.build(root, payload, "run-007")

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["status"], "blocked_unsafe_copy")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)
        self.assertNotIn("/Users/m4/raw.json", encoded)

    def test_success_or_primary_action_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.execution_pack("run-008")
            payload["delivery_success"] = True
            payload["primary_actions_enabled"] = True
            artifact, summary = self.build(root, payload, "run-008")

        self.assertEqual(artifact["status"], "blocked_success_or_control_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_blocked_execution_pack_stays_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, _summary = self.build(
                root,
                self.execution_pack("run-009", "blocked_missing_required_materials"),
                "run-009",
            )

        self.assertEqual(artifact["status"], "blocked_execution_pack_not_ready")
        self.assertIn("Repair the route/task field retest execution pack", artifact["operator_handoff"]["handoff_note"])


if __name__ == "__main__":
    unittest.main()
