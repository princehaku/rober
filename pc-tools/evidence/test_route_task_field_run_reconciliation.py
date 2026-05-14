#!/usr/bin/env python3
"""route/task field-run reconciliation gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_run_reconciliation as reconciliation  # noqa: E402


class RouteTaskFieldRunReconciliationTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 临时 JSON 让测试只覆盖 Docker/local 软件 proof，不依赖 ROS2、Nav2 或硬件现场。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def execution_pack_payload(self, evidence_ref: str) -> dict:
        # ready execution pack 样本模拟上一轮现场执行包的稳定白名单字段。
        return {
            "schema": "trashbot.route_task_field_run_execution_pack.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_run_execution_pack_gate",
            "overall_status": "ready_for_field_run_execution_pack",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "field_run_manifest": {
                "execution_state": "prepared_for_field_run",
                "evidence_ref": evidence_ref,
                "required_material_names": [
                    "route_status_json",
                    "task_record_json",
                    "nav2_or_fixed_route_runtime_log",
                    "robot_side_task_evidence",
                    "support_safe_mobile_summary",
                    "pc_review_console_json",
                ],
            },
            "operator_next_steps": ["Review the aligned software materials with support/operator."],
            "phone_safe_summary": {
                "status": "ready_for_field_run_execution_pack",
                "evidence_ref": evidence_ref,
                "delivery_success": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "real_hil_pass", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def intake_payload(self, evidence_ref: str) -> dict:
        # ready intake 样本代表五份现场 JSON 已完成同 evidence_ref 软件复账。
        return {
            "schema": "trashbot.route_task_field_run_intake_crosscheck.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_run_intake_crosscheck_gate",
            "overall_status": "ready_for_review",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "source_materials": [
                {"name": "route_status", "load_status": "loaded", "schema_status": "supported", "evidence_ref": evidence_ref},
                {"name": "task_record", "load_status": "loaded", "schema_status": "supported", "evidence_ref": evidence_ref},
                {"name": "runtime_log", "load_status": "loaded", "schema_status": "supported", "evidence_ref": evidence_ref},
                {
                    "name": "robot_side_task_evidence",
                    "load_status": "loaded",
                    "schema_status": "supported",
                    "evidence_ref": evidence_ref,
                },
                {
                    "name": "support_safe_mobile_summary",
                    "load_status": "loaded",
                    "schema_status": "supported",
                    "evidence_ref": evidence_ref,
                },
            ],
            "missing_materials": [],
            "mismatch_reasons": [],
            "phone_safe_summary": {
                "status": "ready_for_review",
                "evidence_ref": evidence_ref,
                "material_status": {
                    "route_status": "present",
                    "task_record": "present",
                    "runtime_log": "present",
                    "robot_side_task_evidence": "present",
                    "support_safe_mobile_summary": "present",
                },
                "delivery_success": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "real_hil_pass", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def review_payload(self, evidence_ref: str) -> dict:
        # review console 也可作为 --intake-json 输入，便于 operator/support 复账链复用。
        return {
            "schema": "trashbot.route_task_field_run_review_console.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_run_review_console_gate",
            "overall_status": "ready_for_operator_review",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "review_decision": {"decision": "ready_for_operator_review_not_delivery_claim"},
            "missing_materials": [],
            "mismatch_reasons": [],
            "operator_next_steps": ["Review aligned software materials."],
            "phone_safe_summary": {
                "status": "ready_for_operator_review",
                "evidence_ref": evidence_ref,
                "delivery_success": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "real_hil_pass", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build_with_payloads(
        self,
        root: Path,
        pack_payload: dict,
        intake_payload: dict,
        evidence_ref: str = "",
    ) -> dict:
        # 公共 helper 让 case 聚焦 reconciliation 契约，而不是文件读写样板。
        pack_path = self.write_json(root, "execution_pack.json", pack_payload)
        intake_path = self.write_json(root, "intake.json", intake_payload)
        artifact, exit_code = reconciliation.build_reconciliation(str(pack_path), str(intake_path), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact

    def test_ready_pack_and_intake_become_reconciliation_not_delivery_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "run-001.json")
            artifact = self.build_with_payloads(
                root,
                self.execution_pack_payload(evidence_ref),
                self.intake_payload(evidence_ref),
                evidence_ref,
            )

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_run_reconciliation.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_run_reconciliation_gate",
        )
        self.assertEqual(artifact["reconciliation_verdict"], "ready_for_route_task_field_run_reconciliation")
        self.assertEqual(artifact["evidence_ref"], "file:run-001.json")
        self.assertTrue(artifact["same_evidence_ref_required"])
        self.assertEqual(artifact["materials_status"]["kind"], "intake_crosscheck")
        self.assertIn("Review the aligned software materials", artifact["operator_next_steps"][0])
        self.assertEqual(artifact["materials_status"]["source_phone_safe_summary"]["evidence_ref"], "file:run-001.json")
        self.assertIn("operator_next_steps", artifact)
        self.assertIn("phone_safe_summary", artifact)
        self.assertIn("real_nav2_fixed_route_run", artifact["not_proven"])
        self.assertIn("delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["phone_safe_summary"]["delivery_success"])

    def test_ready_pack_and_review_console_are_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = self.build_with_payloads(
                root,
                self.execution_pack_payload("run-002"),
                self.review_payload("run-002"),
                "run-002",
            )

        self.assertEqual(artifact["reconciliation_verdict"], "ready_for_route_task_field_run_reconciliation")
        self.assertEqual(artifact["materials_status"]["kind"], "review_console")
        self.assertEqual(artifact["materials_status"]["review_decision"]["decision"], "ready_for_operator_review_not_delivery_claim")

    def test_missing_execution_pack_and_missing_intake_are_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intake_path = self.write_json(root, "intake.json", self.intake_payload("run-003"))
            pack_path = self.write_json(root, "pack.json", self.execution_pack_payload("run-003"))
            missing_pack, _ = reconciliation.build_reconciliation(str(root / "missing-pack.json"), str(intake_path), "run-003")
            missing_intake, _ = reconciliation.build_reconciliation(str(pack_path), str(root / "missing-intake.json"), "run-003")

        self.assertEqual(missing_pack["reconciliation_verdict"], "blocked_missing_execution_pack")
        self.assertEqual(missing_intake["reconciliation_verdict"], "blocked_missing_intake")
        self.assertFalse(missing_pack["delivery_success"])
        self.assertFalse(missing_intake["delivery_success"])

    def test_bad_json_blocks_without_exception(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack_path = self.write_json(root, "pack.json", self.execution_pack_payload("run-004"))
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            artifact, _ = reconciliation.build_reconciliation(str(pack_path), str(bad_path), "run-004")

        self.assertEqual(artifact["reconciliation_verdict"], "blocked_bad_json")
        self.assertFalse(artifact["delivery_success"])

    def test_unsupported_schema_and_boundary_are_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            unsupported_schema = self.execution_pack_payload("run-005")
            unsupported_schema["schema"] = "trashbot.unsupported_pack.v99"
            schema_artifact = self.build_with_payloads(root, unsupported_schema, self.intake_payload("run-005"), "run-005")

            unsupported_boundary = self.execution_pack_payload("run-006")
            unsupported_boundary["evidence_boundary"] = "software_proof_wrong_boundary"
            boundary_artifact = self.build_with_payloads(root, unsupported_boundary, self.intake_payload("run-006"), "run-006")

        self.assertEqual(schema_artifact["reconciliation_verdict"], "blocked_unsupported_schema")
        self.assertEqual(boundary_artifact["reconciliation_verdict"], "blocked_unsupported_boundary")

    def test_missing_evidence_ref_and_mismatch_are_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_ref_pack = self.execution_pack_payload("")
            missing_ref_intake = self.intake_payload("")
            missing_ref = self.build_with_payloads(root, missing_ref_pack, missing_ref_intake)

            mismatch = self.build_with_payloads(
                root,
                self.execution_pack_payload("run-007"),
                self.intake_payload("run-other"),
                "run-007",
            )

        self.assertEqual(missing_ref["reconciliation_verdict"], "blocked_missing_evidence_ref")
        self.assertEqual(mismatch["reconciliation_verdict"], "blocked_evidence_ref_mismatch")

    def test_missing_materials_block_reconciliation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intake = self.intake_payload("run-008")
            intake["missing_materials"] = ["runtime_log:runtime_log_missing"]
            intake["overall_status"] = "blocked_missing_material"
            artifact = self.build_with_payloads(root, self.execution_pack_payload("run-008"), intake, "run-008")

        self.assertEqual(artifact["reconciliation_verdict"], "blocked_missing_materials")
        self.assertIn("runtime_log:runtime_log_missing", artifact["materials_status"]["missing_materials"])
        self.assertFalse(artifact["delivery_success"])

    def test_unsafe_summary_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intake = self.intake_payload("run-009")
            intake["phone_safe_summary"]["operator_note"] = (
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            )
            artifact = self.build_with_payloads(root, self.execution_pack_payload("run-009"), intake, "run-009")

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["reconciliation_verdict"], "blocked_unsafe_summary")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)


if __name__ == "__main__":
    unittest.main()
