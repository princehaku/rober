#!/usr/bin/env python3
"""route/task field retest result reconciliation gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_retest_result_reconciliation as reconciliation  # noqa: E402


class RouteTaskFieldRetestResultReconciliationTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，确保 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def material(self, name: str, evidence_ref: str, status: str = "provided") -> dict:
        # 每类材料只模拟摘要元数据；reconciliation 不打开真实现场文件。
        return {
            "name": name,
            "status": status,
            "evidence_ref": evidence_ref,
            "review_note": f"{name} metadata attached for reconciliation",
        }

    def intake_artifact(self, evidence_ref: str, with_materials: bool = True) -> dict:
        # 样本沿用上一轮 result intake 的 artifact 形态。
        payload = {
            "schema": "trashbot.route_task_field_retest_result_intake.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_result_intake_gate",
            "status": "ready_for_field_retest_result_intake_not_proven",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        if with_materials:
            payload["result_materials"] = {
                name: self.material(name, evidence_ref) for name in reconciliation.REQUIRED_RESULT_MATERIALS
            }
        return payload

    def build(self, root: Path, payload: dict, evidence_ref: str = "run-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        path = self.write_json(root, "result.json", payload)
        artifact, summary, exit_code = reconciliation.build_route_task_field_retest_result_reconciliation(
            str(path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_complete_result_intake_reconciles_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary = self.build(root, {"payload": {"artifact": self.intake_artifact("run-001")}}, "run-001")

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_result_reconciliation.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_result_reconciliation_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_result_reconciliation_gate",
        )
        self.assertEqual(artifact["reconciliation_verdict"], "ready_for_field_retest_result_reconciliation_not_proven")
        self.assertEqual(artifact["missing_materials"], [])
        self.assertEqual(artifact["mismatch_reasons"], [])
        self.assertEqual(artifact["same_evidence_ref_status"]["status"], "aligned")
        self.assertIn("operator_next_steps", artifact)
        self.assertIn("rerun_summary", artifact)
        self.assertIn("field_callback_checklist", artifact)
        self.assertIn("fail_closed_phone_safe_summary", artifact)
        self.assertIn("real_delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_nested_result_summary_is_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result_summary = self.intake_artifact("run-002")
            result_summary["schema"] = "trashbot.route_task_field_retest_result_summary.v1"
            artifact, _summary = self.build(root, {"data": {"result_summary": result_summary}}, "run-002")

        self.assertEqual(artifact["source_result"]["schema_status"], "supported")
        self.assertEqual(artifact["status"], "ready_for_field_retest_result_reconciliation_not_proven")
        self.assertIn("delivery_result", artifact["result_materials"])

    def test_execution_pack_placeholder_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            execution_pack = {
                "schema": "trashbot.route_task_field_retest_execution_pack.v1",
                "schema_version": 1,
                "evidence_boundary": "software_proof_docker_route_task_field_retest_execution_pack_gate",
                "status": "ready_for_field_retest_execution_pack_not_proven",
                "evidence_ref": "run-003",
                "same_evidence_ref_required": True,
                "required_field_materials": list(reconciliation.REQUIRED_RESULT_MATERIALS),
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            artifact, summary = self.build(root, execution_pack, "run-003")

        self.assertEqual(artifact["status"], "blocked_placeholder_only_materials")
        self.assertIn("all detected result materials are placeholders only", artifact["mismatch_reasons"])
        self.assertIn("nav2_or_fixed_route_runtime_log", summary["missing_materials"])

    def test_missing_bad_json_and_unsupported_schema_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_artifact, missing_summary, _ = reconciliation.build_route_task_field_retest_result_reconciliation(
                str(root / "missing.json"),
                "run-004",
            )
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_artifact, _bad_summary, _ = reconciliation.build_route_task_field_retest_result_reconciliation(
                str(bad_path),
                "run-004",
            )
            unsupported = self.intake_artifact("run-004")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _unsupported_summary = self.build(root, unsupported, "run-004")

        self.assertEqual(missing_artifact["status"], "blocked_missing_route_task_field_retest_result")
        self.assertEqual(bad_artifact["status"], "blocked_bad_json")
        self.assertEqual(unsupported_artifact["status"], "blocked_unsupported_schema")
        self.assertFalse(missing_artifact["delivery_success"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_missing_materials_mismatch_and_weak_bool_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing = self.intake_artifact("run-005")
            missing["result_materials"].pop("delivery_result")
            missing_artifact, _missing_summary = self.build(root, missing, "run-005")
            mismatch = self.intake_artifact("run-006")
            mismatch["result_materials"]["task_record"]["evidence_ref"] = "other-run"
            mismatch_artifact, _mismatch_summary = self.build(root, mismatch, "run-006")
            weak_bool = self.intake_artifact("run-007")
            weak_bool["same_evidence_ref_required"] = "true"
            weak_artifact, _weak_summary = self.build(root, weak_bool, "run-007")

        self.assertEqual(missing_artifact["status"], "blocked_missing_result_materials")
        self.assertIn("delivery_result", missing_artifact["missing_materials"])
        self.assertEqual(mismatch_artifact["status"], "blocked_same_evidence_ref_mismatch")
        self.assertIn("task_record", mismatch_artifact["same_evidence_ref_status"]["mismatched_materials"])
        self.assertEqual(weak_artifact["status"], "blocked_same_evidence_ref_not_required")

    def test_unsafe_copy_and_success_claim_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            unsafe = self.intake_artifact("run-008")
            unsafe["result_materials"]["nav2_or_fixed_route_runtime_log"]["review_note"] = (
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response /Users/m4/raw.json"
            )
            unsafe_artifact, _unsafe_summary = self.build(root, unsafe, "run-008")
            success = self.intake_artifact("run-009")
            success["delivery_success"] = True
            success["primary_actions_enabled"] = True
            success_artifact, success_summary = self.build(root, success, "run-009")

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(unsafe_artifact["status"], "blocked_unsafe_material_copy")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)
        self.assertNotIn("/Users/m4/raw.json", encoded)
        self.assertEqual(success_artifact["status"], "blocked_success_or_control_claim")
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
