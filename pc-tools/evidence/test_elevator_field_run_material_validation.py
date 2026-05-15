#!/usr/bin/env python3
"""elevator assisted delivery material validation gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import elevator_field_run_material_validation as validation  # noqa: E402


class ElevatorFieldRunMaterialValidationTest(unittest.TestCase):
    def write_json(self, path: Path, payload: dict) -> Path:
        # 测试只写临时文件，保证 gate 不依赖 ROS2、Nav2、硬件或网络。
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def write_filled_materials(self, material_dir: Path, evidence_ref: str) -> None:
        # 这些样本代表“已回填材料形状”，仍不声明真实电梯或送达成功。
        self.write_json(
            material_dir / "door_state.json",
            {
                "schema": "trashbot.elevator_field_door_state_material.v1",
                "evidence_ref": evidence_ref,
                "door_state": "door_open_observed_not_proven",
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
        )
        self.write_json(
            material_dir / "target_floor_confirmation.json",
            {
                "schema": "trashbot.elevator_target_floor_confirmation_material.v1",
                "evidence_ref": evidence_ref,
                "target_floor_status": "operator_confirmed_not_proven",
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
        )
        (material_dir / "human_assistance_operator_note.md").write_text(
            "\n".join(
                [
                    "# Elevator Field Run Operator Note",
                    f"- evidence_ref: {evidence_ref}",
                    "- operator: field-tech",
                    "- observed door state: open state recorded",
                    "- target floor confirmation: human confirmation recorded",
                    "- human assistance note: person helped press the target floor",
                    "- failure or recovery reason: none in material shape only",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.write_json(
            material_dir / "nav2_fixed_route_runtime_log.json",
            {
                "schema": "trashbot.elevator_nav2_fixed_route_runtime_material.v1",
                "evidence_ref": evidence_ref,
                "runtime_status": "runtime_log_collected_not_proven",
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
        )
        self.write_json(
            material_dir / "task_record.json",
            {
                "schema": "trashbot.elevator_task_record_material.v1",
                "evidence_ref": evidence_ref,
                "state_transition_history": ["waiting_elevator_open", "requesting_floor_help", "resume_delivery"],
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
        )
        self.write_json(
            material_dir / "completion_signal.json",
            {
                "schema": "trashbot.elevator_completion_signal_material.v1",
                "evidence_ref": evidence_ref,
                "completion_signal": "manual_review_required_not_delivery_success",
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
        )
        self.write_json(
            material_dir / "diagnostics_mobile_safe_summary.json",
            {
                "schema": "trashbot.elevator_diagnostics_mobile_safe_material.v1",
                "evidence_ref": evidence_ref,
                "summary_status": "field_material_filled",
                "operator_next_steps": ["Review controlled field evidence before any success claim."],
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
        )

    def build(self, material_dir: Path, evidence_ref: str) -> dict:
        # 公共 helper 让 case 聚焦 gate 规则，而不是文件读写样板。
        artifact, exit_code = validation.build_material_validation(str(material_dir), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact

    def test_filled_materials_validate_ready_not_delivery_success(self):
        with tempfile.TemporaryDirectory() as td:
            evidence_ref = "elevator-run-001"
            material_dir = Path(td) / "materials"
            self.write_filled_materials(material_dir, evidence_ref)
            artifact = self.build(material_dir, evidence_ref)

        self.assertEqual(artifact["schema"], "trashbot.elevator_field_run_material_validation.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_elevator_field_material_validation_gate",
        )
        self.assertEqual(artifact["material_validation_verdict"], "elevator_field_material_validation_ready_not_proven")
        self.assertEqual(
            artifact["material_validation_summary"]["schema"],
            "trashbot.elevator_field_run_material_validation_summary.v1",
        )
        self.assertEqual(artifact["material_validation_summary"]["placeholder_materials"], [])
        self.assertEqual(artifact["material_validation_summary"]["missing_materials"], [])
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["material_validation_summary"]["delivery_success"])

    def test_unfilled_templates_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            evidence_ref = "elevator-run-002"
            material_dir = Path(td) / "materials"
            material_dir.mkdir()
            for spec in validation.MATERIAL_SPECS:
                if spec["kind"] == "json":
                    self.write_json(
                        material_dir / spec["name"],
                        {
                            "schema": f"trashbot.elevator_{spec['category']}_material_template.v1",
                            "evidence_ref": evidence_ref,
                            "filled_by": "",
                            "filled_at": "",
                            "primary_actions_enabled": False,
                            "delivery_success": False,
                        },
                    )
                else:
                    (material_dir / spec["name"]).write_text(
                        f"# Elevator Field Run Operator Note\n- evidence_ref: {evidence_ref}\n- operator:\n",
                        encoding="utf-8",
                    )
            artifact = self.build(material_dir, evidence_ref)

        self.assertEqual(artifact["material_validation_verdict"], "blocked_placeholder_materials")
        self.assertIn("door_state.json", artifact["material_validation_summary"]["placeholder_materials"])
        self.assertFalse(artifact["delivery_success"])

    def test_missing_material_dir_missing_file_and_bad_json_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "elevator-run-003"
            missing_dir = self.build(root / "missing", evidence_ref)
            material_dir = root / "materials"
            self.write_filled_materials(material_dir, evidence_ref)
            (material_dir / "task_record.json").unlink()
            missing_file = self.build(material_dir, evidence_ref)
            self.write_filled_materials(material_dir, evidence_ref)
            (material_dir / "door_state.json").write_text("{bad json", encoding="utf-8")
            bad_json = self.build(material_dir, evidence_ref)

        self.assertEqual(missing_dir["material_validation_verdict"], "blocked_missing_material_dir")
        self.assertEqual(missing_file["material_validation_verdict"], "blocked_missing_materials")
        self.assertIn("task_record.json", missing_file["material_validation_summary"]["missing_materials"])
        self.assertEqual(bad_json["material_validation_verdict"], "blocked_missing_materials")
        self.assertIn("door_state.json", bad_json["material_validation_summary"]["missing_materials"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            material_dir = Path(td) / "materials"
            self.write_filled_materials(material_dir, "elevator-run-004")
            self.write_json(
                material_dir / "completion_signal.json",
                {
                    "schema": "trashbot.elevator_completion_signal_material.v1",
                    "evidence_ref": "elevator-run-other",
                    "primary_actions_enabled": False,
                    "delivery_success": False,
                },
            )
            artifact = self.build(material_dir, "elevator-run-004")

        self.assertEqual(artifact["material_validation_verdict"], "blocked_mismatch_evidence_ref")
        self.assertTrue(artifact["mismatch_reasons"])

    def test_unsafe_material_is_blocked_without_raw_copy(self):
        with tempfile.TemporaryDirectory() as td:
            evidence_ref = "elevator-run-005"
            material_dir = Path(td) / "materials"
            self.write_filled_materials(material_dir, evidence_ref)
            (material_dir / "human_assistance_operator_note.md").write_text(
                f"- evidence_ref: {evidence_ref}\nAuthorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response\n",
                encoding="utf-8",
            )
            artifact = self.build(material_dir, evidence_ref)

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["material_validation_verdict"], "blocked_unsafe_summary")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)

    def test_delivery_success_and_primary_actions_claims_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "elevator-run-006"
            material_dir = root / "materials"
            self.write_filled_materials(material_dir, evidence_ref)
            self.write_json(
                material_dir / "completion_signal.json",
                {
                    "schema": "trashbot.elevator_completion_signal_material.v1",
                    "evidence_ref": evidence_ref,
                    "primary_actions_enabled": False,
                    "delivery_success": True,
                },
            )
            delivery_artifact = self.build(material_dir, evidence_ref)
            self.write_filled_materials(material_dir, evidence_ref)
            self.write_json(
                material_dir / "diagnostics_mobile_safe_summary.json",
                {
                    "schema": "trashbot.elevator_diagnostics_mobile_safe_material.v1",
                    "evidence_ref": evidence_ref,
                    "primary_actions_enabled": True,
                    "delivery_success": False,
                },
            )
            action_artifact = self.build(material_dir, evidence_ref)

        self.assertEqual(delivery_artifact["material_validation_verdict"], "blocked_delivery_success_claim")
        self.assertEqual(action_artifact["material_validation_verdict"], "blocked_primary_actions_claim")
        self.assertFalse(delivery_artifact["delivery_success"])
        self.assertFalse(action_artifact["primary_actions_enabled"])

    def test_evidence_ref_can_be_inferred_from_materials(self):
        with tempfile.TemporaryDirectory() as td:
            evidence_ref = "elevator-run-007"
            material_dir = Path(td) / "materials"
            self.write_filled_materials(material_dir, evidence_ref)
            artifact, exit_code = validation.build_material_validation(str(material_dir))

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["evidence_ref"], evidence_ref)
        self.assertEqual(artifact["material_validation_verdict"], "elevator_field_material_validation_ready_not_proven")


if __name__ == "__main__":
    unittest.main()
