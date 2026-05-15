#!/usr/bin/env python3
"""elevator field-run execution pack gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import elevator_field_run_execution_pack as pack  # noqa: E402


class ElevatorFieldRunExecutionPackTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、硬件、电梯或网络。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def review_payload(self, evidence_ref: str) -> dict:
        # ready 样本模拟上一轮 review 的白名单字段，仍不是现场送达成功证据。
        return {
            "schema": "trashbot.elevator_field_run_review.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_elevator_field_review_decision_gate",
            "same_evidence_ref_required": True,
            "evidence_ref": evidence_ref,
            "review_decision": "ready_for_controlled_elevator_field_rehearsal_not_proven",
            "blocked_categories": [],
            "operator_next_steps": [
                "Review the aligned elevator materials under one evidence_ref.",
                "Prepare a controlled elevator field rehearsal with observer and stop path.",
                "Keep delivery_success=false until real completion evidence exists.",
            ],
            "commands_to_rerun": [
                "python3 pc-tools/evidence/elevator_field_run_review.py --validation-json <validation_json>",
                "prepare controlled elevator rehearsal packet; keep not_proven",
            ],
            "capture_checklist": [
                {"name": "door_state.json", "category": "door_state", "status": "filled_material"},
                {
                    "name": "target_floor_confirmation.json",
                    "category": "target_floor_confirmation",
                    "status": "filled_material",
                },
                {
                    "name": "human_assistance_operator_note.md",
                    "category": "human_assistance",
                    "status": "filled_material",
                },
                {
                    "name": "nav2_fixed_route_runtime_log.json",
                    "category": "nav2_fixed_route_runtime",
                    "status": "filled_material",
                },
                {"name": "task_record.json", "category": "task_record", "status": "filled_material"},
                {"name": "completion_signal.json", "category": "completion_signal", "status": "filled_material"},
                {
                    "name": "diagnostics_mobile_safe_summary.json",
                    "category": "diagnostics_mobile_safe_summary",
                    "status": "filled_material",
                },
            ],
            "not_proven": ["real_elevator_door_state", "real_hil_pass", "delivery_success"],
            "review_summary": {
                "schema": "trashbot.elevator_field_run_review_summary.v1",
                "schema_version": 1,
                "evidence_boundary": "software_proof_docker_elevator_field_review_decision_gate",
                "status": "ready_for_controlled_elevator_field_rehearsal_not_proven",
                "review_decision": "ready_for_controlled_elevator_field_rehearsal_not_proven",
                "evidence_ref": evidence_ref,
                "blocked_categories": [],
                "operator_next_steps": [
                    "Review the aligned elevator materials under one evidence_ref.",
                    "Prepare a controlled elevator field rehearsal with observer and stop path.",
                ],
                "commands_to_rerun": [
                    "python3 pc-tools/evidence/elevator_field_run_review.py --validation-json <validation_json>",
                ],
                "not_proven": ["real_elevator_door_state", "real_hil_pass", "delivery_success"],
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build_with_payload(self, root: Path, payload: dict) -> dict:
        # 公共 helper 让 case 聚焦 execution pack 契约，而非文件读写样板。
        review_path = self.write_json(root, "review.json", payload)
        artifact, exit_code = pack.build_execution_pack(str(review_path))
        self.assertEqual(exit_code, 0)
        return artifact

    def test_ready_review_becomes_rehearsal_execution_pack_not_delivery_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = self.build_with_payload(root, self.review_payload(str(root / "elevator-run-001.json")))

        self.assertEqual(artifact["schema"], "trashbot.elevator_field_run_execution_pack.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_elevator_field_rehearsal_execution_pack_gate",
        )
        self.assertEqual(
            artifact["execution_pack_verdict"],
            "ready_for_controlled_elevator_field_rehearsal_execution_pack_not_proven",
        )
        self.assertEqual(artifact["evidence_ref"], "file:elevator-run-001.json")
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertEqual(
            artifact["controlled_rehearsal_manifest"]["execution_state"],
            "prepared_for_controlled_rehearsal",
        )
        self.assertTrue(artifact["controlled_rehearsal_manifest"]["human_observer_required"])
        self.assertTrue(artifact["controlled_rehearsal_manifest"]["stop_path_required"])
        self.assertIn("required_material_templates", artifact)
        self.assertIn("first_run_commands", artifact)
        self.assertIn("rerun_commands", artifact)
        self.assertIn("operator_handoff", artifact)
        self.assertEqual(
            artifact["execution_pack_summary"]["schema"],
            "trashbot.elevator_field_run_execution_pack_summary.v1",
        )
        self.assertIn("real_elevator_door_state", artifact["not_proven"])
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["execution_pack_summary"]["delivery_success"])

    def test_review_summary_input_is_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("summary-run")["review_summary"]
            artifact = self.build_with_payload(root, payload)

        self.assertEqual(
            artifact["execution_pack_verdict"],
            "ready_for_controlled_elevator_field_rehearsal_execution_pack_not_proven",
        )
        self.assertEqual(artifact["controlled_rehearsal_manifest"]["source_review"]["schema_status"], "supported")
        self.assertEqual(artifact["evidence_ref"], "summary-run")

    def test_blocked_review_stays_blocked_but_keeps_rerun_commands(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("run-002")
            payload["review_decision"] = "blocked_missing_materials"
            payload["review_summary"]["review_decision"] = "blocked_missing_materials"
            payload["review_summary"]["status"] = "blocked_missing_materials"
            payload["blocked_categories"] = ["missing_materials"]
            payload["commands_to_rerun"] = ["collect missing elevator files under evidence_ref=run-002"]
            artifact = self.build_with_payload(root, payload)

        self.assertEqual(artifact["execution_pack_verdict"], "blocked_review_not_ready")
        self.assertEqual(
            artifact["controlled_rehearsal_manifest"]["execution_state"],
            "blocked_until_review_repaired",
        )
        self.assertIn("elevator_field_run_execution_pack.py", " ".join(artifact["rerun_commands"]))
        self.assertFalse(artifact["delivery_success"])

    def test_missing_bad_or_unsupported_review_returns_blocked_pack(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_artifact, _ = pack.build_execution_pack(str(root / "missing.json"))
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_artifact, _ = pack.build_execution_pack(str(bad_path))
            unsupported = self.review_payload("run-004")
            unsupported["schema"] = "trashbot.unsupported_review.v99"
            unsupported_artifact = self.build_with_payload(root, unsupported)

        self.assertEqual(missing_artifact["execution_pack_verdict"], "blocked_missing_review")
        self.assertEqual(bad_artifact["execution_pack_verdict"], "blocked_read_error")
        self.assertEqual(unsupported_artifact["execution_pack_verdict"], "blocked_unsupported_schema")
        self.assertFalse(missing_artifact["delivery_success"])
        self.assertFalse(bad_artifact["delivery_success"])

    def test_delivery_or_primary_action_claim_blocks_pack(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("run-005")
            payload["delivery_success"] = True
            payload["review_summary"]["primary_actions_enabled"] = True
            artifact = self.build_with_payload(root, payload)

        self.assertEqual(artifact["execution_pack_verdict"], "blocked_success_or_control_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["execution_pack_summary"]["delivery_success"])

    def test_success_copy_claim_blocks_pack_without_enabling_actions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("run-005b")
            payload["operator_next_steps"].append("delivery completed after dropoff success")
            artifact = self.build_with_payload(root, payload)

        self.assertEqual(artifact["execution_pack_verdict"], "blocked_success_or_control_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["execution_pack_summary"]["delivery_success"])

    def test_unsafe_review_text_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("run-006")
            payload["operator_next_steps"].append(
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            )
            artifact = self.build_with_payload(root, payload)

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["execution_pack_verdict"], "blocked_unsafe_copy")
        self.assertNotIn("Authorization", encoded)
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)


if __name__ == "__main__":
    unittest.main()
