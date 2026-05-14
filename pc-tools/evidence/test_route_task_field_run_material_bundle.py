#!/usr/bin/env python3
"""route/task field-run material bundle gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_run_material_bundle as bundle  # noqa: E402


class RouteTaskFieldRunMaterialBundleTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，确保工具不依赖 ROS2、Nav2、硬件或网络。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def evidence_kit_artifact(self, evidence_ref: str) -> dict:
        # evidence kit 样本只覆盖 material bundle 白名单消费字段。
        return {
            "schema": "trashbot.route_task_field_run_evidence_kit.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_run_evidence_kit_gate",
            "same_evidence_ref_required": True,
            "evidence_ref": evidence_ref,
            "evidence_kit_verdict": "field_run_evidence_kit_ready_not_proven",
            "operator_handoff": {
                "status": "field_run_evidence_kit_ready_not_proven",
                "evidence_ref": evidence_ref,
                "next_steps": ["Hand this evidence kit to the field operator."],
                "same_evidence_ref_required": True,
                "delivery_success": False,
            },
            "robot_diagnostics_summary": {
                "schema": "trashbot.route_task_field_run_evidence_kit.v1",
                "evidence_boundary": "software_proof_docker_route_task_field_run_evidence_kit_gate",
                "status": "field_run_evidence_kit_ready_not_proven",
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
            "mobile_readonly_summary": {
                "schema": "trashbot.route_task_field_run_evidence_kit.v1",
                "evidence_boundary": "software_proof_docker_route_task_field_run_evidence_kit_gate",
                "status": "field_run_evidence_kit_ready_not_proven",
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "delivery_success"],
            "primary_actions_enabled": False,
            "delivery_success": False,
        }

    def build_with_kit(self, root: Path, kit_payload: dict, material_dir: Path, evidence_ref: str) -> dict:
        # 公共 helper 让 case 聚焦 gate 规则，而不是文件读写样板。
        kit_path = self.write_json(root, "evidence_kit.json", kit_payload)
        artifact, exit_code = bundle.build_material_bundle(str(kit_path), str(material_dir), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact

    def test_ready_evidence_kit_creates_material_scaffold_not_delivery_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            material_dir = root / "field_materials"
            evidence_ref = str(root / "run-001.json")
            artifact = self.build_with_kit(
                root,
                self.evidence_kit_artifact(evidence_ref),
                material_dir,
                evidence_ref,
            )
            created_files = sorted(path.name for path in material_dir.iterdir())

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_run_material_bundle.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_run_material_bundle_gate",
        )
        self.assertEqual(artifact["schema_version"], 1)
        self.assertEqual(artifact["evidence_ref"], "file:run-001.json")
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertEqual(artifact["material_bundle_verdict"], "field_run_material_bundle_ready_not_proven")
        self.assertEqual(
            artifact["material_bundle_summary"]["schema"],
            "trashbot.route_task_field_run_material_bundle_summary.v1",
        )
        self.assertEqual(artifact["material_directory_scaffold"]["directory_status"], "scaffold_ready")
        self.assertEqual(len(artifact["material_directory_scaffold"]["template_files"]), len(bundle.MATERIAL_TEMPLATES))
        self.assertIn("route_status_template.json", created_files)
        self.assertIn("task_record_template.json", created_files)
        self.assertIn("completion_material_template.json", created_files)
        self.assertIn("operator_notes.md", created_files)
        self.assertIn("robot_diagnostics_summary_template.json", created_files)
        self.assertIn("mobile_readonly_summary_template.json", created_files)
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["material_bundle_summary"]["delivery_success"])

    def test_summary_only_mode_does_not_require_material_dir(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            kit_path = self.write_json(root, "evidence_kit.json", self.evidence_kit_artifact("run-002"))
            artifact, exit_code = bundle.build_material_bundle(str(kit_path), "", "run-002")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["material_bundle_verdict"], "field_run_material_bundle_ready_not_proven")
        self.assertEqual(artifact["material_directory_scaffold"]["directory_status"], "not_requested")
        self.assertEqual(
            {entry["status"] for entry in artifact["material_directory_scaffold"]["template_files"]},
            {"not_requested"},
        )
        self.assertFalse(artifact["delivery_success"])

    def test_existing_operator_notes_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            material_dir = root / "field_materials"
            material_dir.mkdir()
            notes = material_dir / "operator_notes.md"
            notes.write_text("keep field notes\n", encoding="utf-8")
            artifact = self.build_with_kit(root, self.evidence_kit_artifact("run-003"), material_dir, "run-003")
            statuses = {entry["name"]: entry["status"] for entry in artifact["material_directory_scaffold"]["template_files"]}
            preserved_text = notes.read_text(encoding="utf-8")

        self.assertEqual(statuses["operator_notes.md"], "preserved_existing")
        self.assertEqual(preserved_text, "keep field notes\n")

    def test_missing_bad_and_unsupported_evidence_kit_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing, _ = bundle.build_material_bundle(str(root / "missing.json"), "", "run-004")
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad, _ = bundle.build_material_bundle(str(bad_path), "", "run-004")
            unsupported = self.evidence_kit_artifact("run-004")
            unsupported["schema"] = "trashbot.unsupported_evidence_kit.v99"
            unsupported_artifact = self.build_with_kit(root, unsupported, root / "materials", "run-004")

        self.assertEqual(missing["material_bundle_verdict"], "blocked_missing_evidence_kit")
        self.assertEqual(bad["material_bundle_verdict"], "blocked_bad_evidence_kit")
        self.assertEqual(unsupported_artifact["material_bundle_verdict"], "blocked_unsupported_evidence_kit")
        self.assertFalse(missing["delivery_success"])
        self.assertFalse(bad["delivery_success"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.evidence_kit_artifact("run-005")
            payload["mobile_readonly_summary"]["evidence_ref"] = "run-other"
            artifact = self.build_with_kit(root, payload, root / "materials", "run-005")

        self.assertEqual(artifact["material_bundle_verdict"], "blocked_mismatch_evidence_ref")
        self.assertTrue(artifact["mismatch_reasons"])
        self.assertFalse(artifact["delivery_success"])

    def test_unsafe_summary_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.evidence_kit_artifact("run-006")
            payload["operator_handoff"]["next_steps"] = [
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            ]
            artifact = self.build_with_kit(root, payload, root / "materials", "run-006")

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["material_bundle_verdict"], "blocked_unsafe_summary")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)

    def test_delivery_success_and_primary_actions_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            delivery_claim = self.evidence_kit_artifact("run-007")
            delivery_claim["delivery_success"] = True
            delivery_artifact = self.build_with_kit(root, delivery_claim, root / "materials-a", "run-007")
            action_claim = self.evidence_kit_artifact("run-008")
            action_claim["robot_diagnostics_summary"]["primary_actions_enabled"] = True
            action_artifact = self.build_with_kit(root, action_claim, root / "materials-b", "run-008")

        self.assertEqual(delivery_artifact["material_bundle_verdict"], "blocked_delivery_success_claim")
        self.assertEqual(action_artifact["material_bundle_verdict"], "blocked_unsafe_summary")
        self.assertFalse(delivery_artifact["delivery_success"])
        self.assertFalse(action_artifact["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
