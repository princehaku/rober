#!/usr/bin/env python3
"""mobile field material review decision gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import mobile_field_material_review_decision as review  # noqa: E402


class MobileFieldMaterialReviewDecisionTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、真实手机、硬件或云。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def intake_summary(self, evidence_ref: str) -> dict:
        # ready 样本只代表 intake 形状合格，仍不是现场成功或真实送达证据。
        return {
            "schema": "trashbot.mobile_field_material_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_mobile_field_material_intake_gate",
            "status": "ready_for_mobile_field_material_review_not_proven",
            "intake_verdict": "ready_for_mobile_field_material_review_not_proven",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched_same_evidence_ref",
            "material_statuses": [
                {
                    "name": name,
                    "status": "present_not_proven",
                    "present": True,
                    "same_evidence_ref_required": True,
                    "evidence_ref": evidence_ref,
                    "missing_or_blocked": [],
                }
                for name in review.MATERIAL_DECISION_MAP
            ],
            "missing_or_blocked": [],
            "not_proven": ["real_phone_device_or_browser", "real_nav2_fixed_route_run", "delivery_success"],
            "route_elevator_field_pass": False,
            "nav2_fixed_route_completed": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build_with_payload(self, root: Path, payload: dict, evidence_ref: str = "") -> tuple[dict, dict, int]:
        # 公共 helper 让测试关注状态映射，而不是文件读写样板。
        intake_path = self.write_json(root, "intake.json", payload)
        return review.build_review_decision(str(intake_path), evidence_ref)

    def test_ready_intake_becomes_owner_handoff_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary, exit_code = self.build_with_payload(
                root,
                self.intake_summary(str(root / "same-evidence-ref.json")),
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.mobile_field_material_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.mobile_field_material_review_decision_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_mobile_field_material_review_decision_gate",
        )
        self.assertEqual(artifact["review_decision"], "ready_for_owner_handoff_not_proven")
        self.assertEqual(artifact["evidence_ref"], "file:same-evidence-ref.json")
        self.assertEqual(artifact["same_evidence_ref_status"], "matched_same_evidence_ref")
        self.assertEqual(artifact["owner_handoff"], "Product closeout")
        self.assertIn("next-required-evidence", artifact)
        self.assertIn("not_proven", artifact)
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_material_gaps_map_to_required_review_decisions_and_owners(self):
        cases = {
            "device_pwa_observation": ("blocked_missing_real_phone_or_pwa_observation", "Full-stack"),
            "route_elevator_field_materials": ("blocked_missing_route_elevator_field_materials", "Product closeout"),
            "nav2_fixed_route_runtime_log": ("blocked_missing_nav2_or_fixed_route_runtime_log", "Autonomy"),
            "task_record": ("blocked_missing_same_evidence_ref_task_record_or_completion_signal", "Robot"),
            "completion_signal": ("blocked_missing_same_evidence_ref_task_record_or_completion_signal", "Robot"),
            "dropoff_cancel_material_status": ("blocked_missing_dropoff_or_cancel_completion", "Robot"),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for material, (expected_decision, expected_owner) in cases.items():
                payload = self.intake_summary(f"run-{material}")
                for item in payload["material_statuses"]:
                    if item["name"] == material:
                        item["status"] = "missing_or_unreadable"
                        item["missing_or_blocked"] = [f"{material}_missing"]
                artifact, _summary, exit_code = self.build_with_payload(root, payload)
                self.assertEqual(exit_code, 2)
                self.assertEqual(artifact["review_decision"], expected_decision)
                self.assertEqual(artifact["owner_handoff"], expected_owner)
                self.assertIn(material, json.dumps(artifact["blocked_materials"], ensure_ascii=False))

    def test_mismatch_missing_placeholder_unsafe_and_success_wording_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mismatch_payload = self.intake_summary("run-source")
            mismatch_payload["same_evidence_ref_status"] = "not_proven"
            mismatch_artifact, _, mismatch_exit = self.build_with_payload(root, mismatch_payload, "run-target")

            missing_ref_payload = self.intake_summary("")
            missing_ref_artifact, _, missing_ref_exit = self.build_with_payload(root, missing_ref_payload)

            placeholder_payload = self.intake_summary("run-placeholder")
            placeholder_payload["operator_note"] = "TODO replace_me"
            placeholder_artifact, _, placeholder_exit = self.build_with_payload(root, placeholder_payload)

            unsafe_payload = self.intake_summary("run-unsafe")
            unsafe_payload["operator_note"] = "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            unsafe_artifact, _, unsafe_exit = self.build_with_payload(root, unsafe_payload)

            success_payload = self.intake_summary("run-success")
            success_payload["delivery_success"] = True
            success_artifact, _, success_exit = self.build_with_payload(root, success_payload)

        self.assertEqual(mismatch_exit, 2)
        self.assertEqual(missing_ref_exit, 2)
        self.assertEqual(placeholder_exit, 2)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(success_exit, 2)
        self.assertEqual(mismatch_artifact["review_decision"], "blocked_invalid_intake")
        self.assertEqual(missing_ref_artifact["review_decision"], "blocked_invalid_intake")
        self.assertEqual(placeholder_artifact["review_decision"], "blocked_invalid_intake")
        self.assertEqual(unsafe_artifact["review_decision"], "blocked_invalid_intake")
        self.assertNotIn("Bearer abc", json.dumps(unsafe_artifact, ensure_ascii=False))
        self.assertNotIn("/cmd_vel", json.dumps(unsafe_artifact, ensure_ascii=False))
        self.assertEqual(success_artifact["review_decision"], "blocked_invalid_intake")
        self.assertFalse(success_artifact["delivery_success"])

    def test_full_intake_artifact_and_invalid_inputs_are_handled(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            nested_payload = {
                "schema": "trashbot.mobile_field_material_intake.v1",
                "evidence_boundary": "software_proof_docker_mobile_field_material_intake_gate",
                "evidence_ref": "outer-ref",
                "mobile_field_material_intake_summary": self.intake_summary("inner-ref"),
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            nested_artifact, _, nested_exit = self.build_with_payload(root, nested_payload)

            missing_artifact, _, missing_exit = review.build_review_decision(str(root / "missing.json"))
            unsupported = self.intake_summary("run-unsupported")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _, unsupported_exit = self.build_with_payload(root, unsupported)

        self.assertEqual(nested_exit, 0)
        self.assertEqual(nested_artifact["evidence_ref"], "inner-ref")
        self.assertEqual(nested_artifact["review_decision"], "ready_for_owner_handoff_not_proven")
        self.assertEqual(missing_exit, 2)
        self.assertEqual(missing_artifact["review_decision"], "blocked_invalid_intake")
        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(unsupported_artifact["review_decision"], "blocked_invalid_intake")
        self.assertFalse(missing_artifact["review_summary"]["delivery_success"])


if __name__ == "__main__":
    unittest.main()
