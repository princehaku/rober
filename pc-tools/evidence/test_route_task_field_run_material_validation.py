#!/usr/bin/env python3
"""route/task field-run material validation gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_run_material_validation as validation  # noqa: E402


class RouteTaskFieldRunMaterialValidationTest(unittest.TestCase):
    def write_json(self, path: Path, payload: dict) -> Path:
        # 测试只写临时文件，保证 gate 不依赖 ROS2、Nav2、硬件或网络。
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def material_bundle_artifact(self, evidence_ref: str) -> dict:
        # bundle 样本只覆盖 validation 需要读取的稳定契约字段。
        return {
            "schema": "trashbot.route_task_field_run_material_bundle.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_run_material_bundle_gate",
            "same_evidence_ref_required": True,
            "evidence_ref": evidence_ref,
            "material_bundle_verdict": "field_run_material_bundle_ready_not_proven",
            "material_bundle_summary": {
                "schema": "trashbot.route_task_field_run_material_bundle_summary.v1",
                "schema_version": 1,
                "evidence_boundary": "software_proof_docker_route_task_field_run_material_bundle_gate",
                "status": "field_run_material_bundle_ready_not_proven",
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "delivery_success"],
            "primary_actions_enabled": False,
            "delivery_success": False,
        }

    def write_filled_materials(self, material_dir: Path, evidence_ref: str) -> None:
        # 这些样本代表“已回填材料形状”，仍不声明真实成功。
        self.write_json(
            material_dir / "route_status_template.json",
            {
                "schema": "trashbot.route_task_field_run_route_status_material.v1",
                "evidence_ref": evidence_ref,
                "route_state": "field_recorded_not_proven",
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
        )
        self.write_json(
            material_dir / "task_record_template.json",
            {
                "schema": "trashbot.route_task_field_run_task_record_material.v1",
                "evidence_ref": evidence_ref,
                "state_transition_history": ["accepted", "navigating", "blocked_before_dropoff"],
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
        )
        self.write_json(
            material_dir / "completion_material_template.json",
            {
                "schema": "trashbot.route_task_field_run_completion_material.v1",
                "evidence_ref": evidence_ref,
                "dropoff_completion": {"present": False},
                "cancel_completion": {"present": True},
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
        )
        (material_dir / "operator_notes.md").write_text(
            "\n".join(
                [
                    "# Route Task Field Run Notes",
                    f"- evidence_ref: {evidence_ref}",
                    "- operator: field-tech",
                    "- observed route/task state: cancel path recorded",
                    "- failure or recovery reason: blocked before real dropoff",
                    "- materials collected: route/task/completion summaries",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.write_json(
            material_dir / "robot_diagnostics_summary_template.json",
            {
                "schema": "trashbot.route_task_field_run_robot_diagnostics_material.v1",
                "evidence_ref": evidence_ref,
                "summary_status": "field_material_filled",
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
        )
        self.write_json(
            material_dir / "mobile_readonly_summary_template.json",
            {
                "schema": "trashbot.route_task_field_run_mobile_summary_material.v1",
                "evidence_ref": evidence_ref,
                "summary_status": "field_material_filled",
                "operator_next_steps": ["Run intake before any success claim."],
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
        )

    def build_with_bundle(self, root: Path, bundle_payload: dict, material_dir: Path, evidence_ref: str) -> dict:
        # 公共 helper 让 case 聚焦 gate 规则，而不是文件读写样板。
        bundle_path = self.write_json(root / "material_bundle.json", bundle_payload)
        artifact, exit_code = validation.build_material_validation(str(bundle_path), str(material_dir), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact

    def test_filled_materials_validate_ready_not_delivery_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-001"
            material_dir = root / "materials"
            self.write_filled_materials(material_dir, evidence_ref)
            artifact = self.build_with_bundle(root, self.material_bundle_artifact(evidence_ref), material_dir, evidence_ref)

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_run_material_validation.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_run_material_validation_gate",
        )
        self.assertEqual(artifact["schema_version"], 1)
        self.assertEqual(artifact["evidence_ref"], evidence_ref)
        self.assertEqual(artifact["material_validation_verdict"], "field_run_material_validation_ready_not_proven")
        self.assertEqual(
            artifact["material_validation_summary"]["schema"],
            "trashbot.route_task_field_run_material_validation_summary.v1",
        )
        self.assertEqual(artifact["material_validation_summary"]["placeholder_materials"], [])
        self.assertEqual(artifact["material_validation_summary"]["missing_materials"], [])
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["material_validation_summary"]["delivery_success"])

    def test_unfilled_bundle_templates_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-002"
            material_dir = root / "materials"
            material_dir.mkdir()
            for spec in validation.MATERIAL_SPECS:
                if spec["kind"] == "json":
                    self.write_json(
                        material_dir / spec["name"],
                        {
                            "schema": f"trashbot.route_task_field_run_{spec['category']}_material_template.v1",
                            "evidence_ref": evidence_ref,
                            "filled_by": "",
                            "filled_at": "",
                            "primary_actions_enabled": False,
                            "delivery_success": False,
                        },
                    )
                else:
                    (material_dir / spec["name"]).write_text(
                        f"# Route Task Field Run Operator Notes\n- evidence_ref: {evidence_ref}\n- operator:\n",
                        encoding="utf-8",
                    )
            artifact = self.build_with_bundle(root, self.material_bundle_artifact(evidence_ref), material_dir, evidence_ref)

        self.assertEqual(artifact["material_validation_verdict"], "blocked_placeholder_materials")
        self.assertIn("route_status_template.json", artifact["material_validation_summary"]["placeholder_materials"])
        self.assertFalse(artifact["delivery_success"])

    def test_missing_bad_and_unsupported_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            material_dir = root / "materials"
            self.write_filled_materials(material_dir, "run-003")
            missing, _ = validation.build_material_validation(str(root / "missing.json"), str(material_dir), "run-003")
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad, _ = validation.build_material_validation(str(bad_path), str(material_dir), "run-003")
            unsupported = self.material_bundle_artifact("run-003")
            unsupported["schema"] = "trashbot.unsupported_material_bundle.v99"
            unsupported_artifact = self.build_with_bundle(root, unsupported, material_dir, "run-003")

        self.assertEqual(missing["material_validation_verdict"], "blocked_missing_material_bundle")
        self.assertEqual(bad["material_validation_verdict"], "blocked_bad_material_bundle")
        self.assertEqual(unsupported_artifact["material_validation_verdict"], "blocked_unsupported_material_bundle")
        self.assertFalse(missing["delivery_success"])
        self.assertFalse(bad["delivery_success"])

    def test_missing_material_file_and_bad_json_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-004"
            material_dir = root / "materials"
            self.write_filled_materials(material_dir, evidence_ref)
            (material_dir / "task_record_template.json").unlink()
            missing_artifact = self.build_with_bundle(root, self.material_bundle_artifact(evidence_ref), material_dir, evidence_ref)
            self.write_filled_materials(material_dir, evidence_ref)
            (material_dir / "route_status_template.json").write_text("{bad json", encoding="utf-8")
            bad_artifact = self.build_with_bundle(root, self.material_bundle_artifact(evidence_ref), material_dir, evidence_ref)

        self.assertEqual(missing_artifact["material_validation_verdict"], "blocked_missing_materials")
        self.assertIn("task_record_template.json", missing_artifact["material_validation_summary"]["missing_materials"])
        self.assertEqual(bad_artifact["material_validation_verdict"], "blocked_missing_materials")
        self.assertIn("route_status_template.json", bad_artifact["material_validation_summary"]["missing_materials"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            material_dir = root / "materials"
            self.write_filled_materials(material_dir, "run-005")
            payload = self.material_bundle_artifact("run-005")
            payload["material_bundle_summary"]["evidence_ref"] = "run-other"
            bundle_mismatch = self.build_with_bundle(root, payload, material_dir, "run-005")
            self.write_filled_materials(material_dir, "run-006")
            material_mismatch = self.build_with_bundle(root, self.material_bundle_artifact("run-005"), material_dir, "run-005")

        self.assertEqual(bundle_mismatch["material_validation_verdict"], "blocked_mismatch_evidence_ref")
        self.assertEqual(material_mismatch["material_validation_verdict"], "blocked_mismatch_evidence_ref")
        self.assertTrue(bundle_mismatch["mismatch_reasons"])
        self.assertTrue(material_mismatch["mismatch_reasons"])

    def test_unsafe_material_is_blocked_without_raw_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = "run-007"
            material_dir = root / "materials"
            self.write_filled_materials(material_dir, evidence_ref)
            (material_dir / "operator_notes.md").write_text(
                f"- evidence_ref: {evidence_ref}\nAuthorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response\n",
                encoding="utf-8",
            )
            artifact = self.build_with_bundle(root, self.material_bundle_artifact(evidence_ref), material_dir, evidence_ref)

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
            evidence_ref = "run-008"
            material_dir = root / "materials"
            self.write_filled_materials(material_dir, evidence_ref)
            delivery_claim = self.material_bundle_artifact(evidence_ref)
            delivery_claim["delivery_success"] = True
            delivery_artifact = self.build_with_bundle(root, delivery_claim, material_dir, evidence_ref)
            action_claim = self.material_bundle_artifact(evidence_ref)
            action_claim["material_bundle_summary"]["primary_actions_enabled"] = True
            action_artifact = self.build_with_bundle(root, action_claim, material_dir, evidence_ref)

        self.assertEqual(delivery_artifact["material_validation_verdict"], "blocked_delivery_success_claim")
        self.assertEqual(action_artifact["material_validation_verdict"], "blocked_primary_actions_claim")
        self.assertFalse(delivery_artifact["delivery_success"])
        self.assertFalse(action_artifact["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
