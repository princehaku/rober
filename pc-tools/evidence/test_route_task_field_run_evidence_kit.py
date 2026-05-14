#!/usr/bin/env python3
"""route/task field-run evidence kit gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_run_evidence_kit as kit  # noqa: E402


class RouteTaskFieldRunEvidenceKitTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试材料只写临时 JSON，确保工具不依赖 ROS2、Nav2、硬件或网络。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def make_material_dir(self, root: Path) -> Path:
        # evidence kit 的 happy path 需要目录文件齐全，但文件内容不被当作真实证明。
        material_dir = root / "materials"
        material_dir.mkdir(exist_ok=True)
        for name in kit.MATERIAL_FILES:
            (material_dir / name).write_text("placeholder\n", encoding="utf-8")
        return material_dir

    def console_artifact(self, evidence_ref: str) -> dict:
        # console 样本只覆盖 evidence kit 白名单消费字段。
        return {
            "schema": "trashbot.route_task_field_run_console.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_run_console_gate",
            "same_evidence_ref_required": True,
            "evidence_ref": evidence_ref,
            "console_verdict": "field_run_materials_prepared_not_proven",
            "execution_pack_summary": {"evidence_ref": evidence_ref},
            "route_status_summary": {"evidence_ref": evidence_ref},
            "task_record_summary": {"evidence_ref": evidence_ref},
            "completion_signal_summary": {"evidence_ref": evidence_ref},
            "materials_status": {"missing_materials": [], "mismatch_reasons": []},
            "robot_diagnostics_summary": {
                "evidence_ref": evidence_ref,
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
            "mobile_readonly_summary": {
                "evidence_ref": evidence_ref,
                "primary_actions_enabled": False,
                "delivery_success": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "delivery_success"],
            "primary_actions_enabled": False,
            "delivery_success": False,
        }

    def build_with_console(self, root: Path, console_payload: dict, material_dir: Path, evidence_ref: str) -> dict:
        # 公共 helper 让 case 聚焦 gate 规则，而不是文件读写样板。
        console_path = self.write_json(root, "console.json", console_payload)
        artifact, exit_code = kit.build_evidence_kit(str(console_path), str(material_dir), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact

    def test_ready_console_and_material_dir_become_evidence_kit_not_delivery_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "run-001.json")
            artifact = self.build_with_console(
                root,
                self.console_artifact(evidence_ref),
                self.make_material_dir(root),
                evidence_ref,
            )

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_run_evidence_kit.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_run_evidence_kit_gate",
        )
        self.assertEqual(artifact["schema_version"], 1)
        self.assertEqual(artifact["evidence_ref"], "file:run-001.json")
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertEqual(artifact["evidence_kit_verdict"], "field_run_evidence_kit_ready_not_proven")
        self.assertEqual(artifact["material_directory_manifest"]["missing_files"], [])
        self.assertIn("capture_templates", artifact)
        self.assertIn("commands_to_run", artifact)
        self.assertIn("commands_to_rerun", artifact)
        self.assertIn("operator_handoff", artifact)
        self.assertIn("robot_diagnostics_summary", artifact)
        self.assertIn("mobile_readonly_summary", artifact)
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["mobile_readonly_summary"]["delivery_success"])

    def test_missing_console_bad_json_and_unsupported_schema_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            material_dir = self.make_material_dir(root)
            missing_console, _ = kit.build_evidence_kit(str(root / "missing.json"), str(material_dir), "run-002")
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_console, _ = kit.build_evidence_kit(str(bad_path), str(material_dir), "run-002")
            unsupported = self.console_artifact("run-002")
            unsupported["schema"] = "trashbot.unsupported_console.v99"
            unsupported_artifact = self.build_with_console(root, unsupported, material_dir, "run-002")

        self.assertEqual(missing_console["evidence_kit_verdict"], "blocked_missing_console")
        self.assertEqual(bad_console["evidence_kit_verdict"], "blocked_bad_console")
        self.assertEqual(unsupported_artifact["evidence_kit_verdict"], "blocked_unsupported_console")
        self.assertFalse(missing_console["delivery_success"])
        self.assertFalse(bad_console["delivery_success"])

    def test_missing_material_dir_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            material_dir = root / "materials"
            material_dir.mkdir()
            (material_dir / "route_task_field_run_console.json").write_text("placeholder\n", encoding="utf-8")
            artifact = self.build_with_console(root, self.console_artifact("run-003"), material_dir, "run-003")

        self.assertEqual(artifact["evidence_kit_verdict"], "blocked_missing_materials")
        self.assertIn("route_status.json", artifact["missing_materials"])
        self.assertFalse(artifact["delivery_success"])

    def test_evidence_ref_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            console_payload = self.console_artifact("run-004")
            console_payload["task_record_summary"]["evidence_ref"] = "run-other"
            artifact = self.build_with_console(root, console_payload, self.make_material_dir(root), "run-004")

        self.assertEqual(artifact["evidence_kit_verdict"], "blocked_mismatch_evidence_ref")
        self.assertTrue(artifact["mismatch_reasons"])
        self.assertFalse(artifact["delivery_success"])

    def test_unsafe_summary_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            console_payload = self.console_artifact("run-005")
            console_payload["operator_next_steps"] = [
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            ]
            artifact = self.build_with_console(root, console_payload, self.make_material_dir(root), "run-005")

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["evidence_kit_verdict"], "blocked_unsafe_summary")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)

    def test_delivery_success_and_primary_actions_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            delivery_claim = self.console_artifact("run-006")
            delivery_claim["delivery_success"] = True
            delivery_artifact = self.build_with_console(root, delivery_claim, self.make_material_dir(root), "run-006")
            action_claim = self.console_artifact("run-007")
            action_claim["mobile_readonly_summary"]["primary_actions_enabled"] = True
            action_artifact = self.build_with_console(root, action_claim, self.make_material_dir(root), "run-007")

        self.assertEqual(delivery_artifact["evidence_kit_verdict"], "blocked_delivery_success_claim")
        self.assertEqual(action_artifact["evidence_kit_verdict"], "blocked_unsafe_summary")
        self.assertFalse(delivery_artifact["delivery_success"])
        self.assertFalse(action_artifact["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
