#!/usr/bin/env python3
"""elevator field-run review decision gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import elevator_field_run_review as review  # noqa: E402


class ElevatorFieldRunReviewTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，保证 review CLI 不依赖 ROS2、Nav2、硬件或网络。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def validation_summary(self, evidence_ref: str) -> dict:
        # ready 样本只代表 validation artifact 形状合格，仍不是现场成功证据。
        return {
            "schema": "trashbot.elevator_field_run_material_validation_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_elevator_field_material_validation_gate",
            "status": "elevator_field_material_validation_ready_not_proven",
            "material_validation_verdict": "elevator_field_material_validation_ready_not_proven",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_files": [
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
            "missing_materials": [],
            "placeholder_materials": [],
            "mismatch_reasons": [],
            "operator_next_steps": ["Review controlled elevator field evidence before any success claim."],
            "not_proven": ["real_elevator_door_state", "real_hil_pass", "delivery_success"],
            "primary_actions_enabled": False,
            "delivery_success": False,
        }

    def build_with_payload(self, root: Path, payload: dict) -> dict:
        # 公共 helper 让测试聚焦状态映射，而不是文件读写样板。
        validation_path = self.write_json(root, "validation.json", payload)
        artifact, exit_code = review.build_review(str(validation_path))
        self.assertEqual(exit_code, 0)
        return artifact

    def test_ready_validation_becomes_controlled_rehearsal_decision_not_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = self.build_with_payload(root, self.validation_summary(str(root / "elevator-run-001.json")))

        self.assertEqual(artifact["schema"], "trashbot.elevator_field_run_review.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_elevator_field_review_decision_gate",
        )
        self.assertEqual(
            artifact["review_decision"],
            "ready_for_controlled_elevator_field_rehearsal_not_proven",
        )
        self.assertEqual(artifact["evidence_ref"], "file:elevator-run-001.json")
        self.assertEqual(artifact["review_summary"]["schema"], "trashbot.elevator_field_run_review_summary.v1")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertIn("not_proven", artifact)
        self.assertIn("real_hil_pass", artifact["not_proven"])
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertIn("prepare controlled elevator rehearsal", " ".join(artifact["commands_to_rerun"]))

    def test_full_validation_artifact_nested_summary_is_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = {
                "schema": "trashbot.elevator_field_run_material_validation.v1",
                "schema_version": 1,
                "evidence_boundary": "software_proof_docker_elevator_field_material_validation_gate",
                "material_validation_verdict": "elevator_field_material_validation_ready_not_proven",
                "evidence_ref": "outer-ref",
                "material_validation_summary": self.validation_summary("inner-ref"),
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            artifact = self.build_with_payload(root, payload)

        self.assertEqual(
            artifact["review_decision"],
            "ready_for_controlled_elevator_field_rehearsal_not_proven",
        )
        self.assertEqual(artifact["evidence_ref"], "inner-ref")
        self.assertEqual(artifact["source_validation"]["schema_status"], "supported")

    def test_missing_template_and_mismatch_states_map_to_operator_decisions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_payload = self.validation_summary("run-002")
            missing_payload["status"] = "blocked_missing_materials"
            missing_payload["material_validation_verdict"] = "blocked_missing_materials"
            missing_payload["missing_materials"] = ["door_state.json"]
            missing_artifact = self.build_with_payload(root, missing_payload)

            template_payload = self.validation_summary("run-003")
            template_payload["status"] = "blocked_placeholder_materials"
            template_payload["material_validation_verdict"] = "blocked_placeholder_materials"
            template_payload["placeholder_materials"] = ["human_assistance_operator_note.md"]
            template_artifact = self.build_with_payload(root, template_payload)

            mismatch_payload = self.validation_summary("run-004")
            mismatch_payload["status"] = "blocked_mismatch_evidence_ref"
            mismatch_payload["material_validation_verdict"] = "blocked_mismatch_evidence_ref"
            mismatch_payload["mismatch_reasons"] = ["task_record:evidence_ref_mismatch:other!=run-004"]
            mismatch_artifact = self.build_with_payload(root, mismatch_payload)

        self.assertEqual(missing_artifact["review_decision"], "blocked_missing_materials")
        self.assertIn("door_state.json", missing_artifact["missing_materials"])
        self.assertEqual(template_artifact["review_decision"], "blocked_template_materials")
        self.assertIn("human_assistance_operator_note.md", template_artifact["template_materials"])
        self.assertEqual(mismatch_artifact["review_decision"], "blocked_evidence_ref_mismatch")
        self.assertIn("same evidence_ref", " ".join(mismatch_artifact["operator_next_steps"]))

    def test_unsafe_copy_and_success_claim_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            unsafe_payload = self.validation_summary("run-005")
            unsafe_payload["operator_next_steps"] = [
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            ]
            unsafe_artifact = self.build_with_payload(root, unsafe_payload)

            success_payload = self.validation_summary("run-006")
            success_payload["delivery_success"] = True
            success_artifact = self.build_with_payload(root, success_payload)

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(unsafe_artifact["review_decision"], "blocked_unsafe_copy")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)
        self.assertEqual(success_artifact["review_decision"], "blocked_success_claim")
        self.assertFalse(success_artifact["delivery_success"])

    def test_invalid_missing_or_bad_validation_returns_blocked_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_artifact, _ = review.build_review(str(root / "missing.json"))
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_artifact, _ = review.build_review(str(bad_path))
            unsupported = self.validation_summary("run-007")
            unsupported["schema"] = "trashbot.unsupported_validation.v99"
            unsupported_artifact = self.build_with_payload(root, unsupported)

        self.assertEqual(missing_artifact["review_decision"], "blocked_invalid_validation")
        self.assertEqual(bad_artifact["review_decision"], "blocked_invalid_validation")
        self.assertEqual(unsupported_artifact["review_decision"], "blocked_invalid_validation")
        self.assertFalse(missing_artifact["review_summary"]["delivery_success"])


if __name__ == "__main__":
    unittest.main()
