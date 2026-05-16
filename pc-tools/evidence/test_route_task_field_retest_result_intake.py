#!/usr/bin/env python3
"""route/task field retest result intake gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_retest_result_intake as intake  # noqa: E402


class RouteTaskFieldRetestResultIntakeTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，确保 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def material(self, name: str, evidence_ref: str, status: str = "provided") -> dict:
        # 每个材料只提供元数据摘要；gate 不打开任何现场文件。
        return {
            "name": name,
            "status": status,
            "evidence_ref": evidence_ref,
            "review_note": f"{name} metadata attached for review",
        }

    def handoff_summary(self, evidence_ref: str, with_materials: bool = True) -> dict:
        # 样本模拟 session handoff 后回填 summary 的 wrapper 输入。
        payload = {
            "schema": "trashbot.route_task_field_retest_session_handoff_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_session_handoff_gate",
            "status": "ready_for_field_retest_session_handoff_not_proven",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "required_result_materials": list(intake.REQUIRED_RESULT_MATERIALS),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        if with_materials:
            payload["returned_materials"] = [self.material(name, evidence_ref) for name in intake.REQUIRED_RESULT_MATERIALS]
        return payload

    def build(self, root: Path, payload: dict, evidence_ref: str = "run-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        path = self.write_json(root, "result.json", payload)
        artifact, summary, exit_code = intake.build_route_task_field_retest_result_intake(str(path), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_complete_handoff_backfill_becomes_result_intake_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary = self.build(root, {"payload": {"summary": self.handoff_summary("run-001")}}, "run-001")

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_result_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_result_intake_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_result_intake_gate",
        )
        self.assertEqual(artifact["status"], "ready_for_field_retest_result_intake_not_proven")
        self.assertTrue(artifact["material_completeness"]["is_complete"])
        self.assertEqual(artifact["missing_materials"], [])
        self.assertIn("nav2_or_fixed_route_runtime_log", artifact["result_materials"])
        self.assertIn("operator_next_steps", artifact)
        self.assertIn("field_callback_checklist", artifact)
        self.assertIn("rerun_summary", artifact)
        self.assertIn("fail_closed_phone_safe_summary", artifact)
        self.assertIn("real_delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_result_artifact_and_nested_summary_are_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result_summary = {
                "schema": "trashbot.route_task_field_retest_result_summary.v1",
                "schema_version": 1,
                "evidence_boundary": "software_proof_docker_route_task_field_retest_result_intake_gate",
                "status": "not_proven",
                "evidence_ref": "run-002",
                "same_evidence_ref_required": True,
                "result_materials": {
                    name: self.material(name, "run-002") for name in intake.REQUIRED_RESULT_MATERIALS
                },
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            artifact, _summary = self.build(root, {"data": {"result_summary": result_summary}}, "run-002")

        self.assertEqual(artifact["source_result"]["schema_status"], "supported")
        self.assertEqual(artifact["status"], "ready_for_field_retest_result_intake_not_proven")
        self.assertTrue(artifact["material_completeness"]["is_complete"])

    def test_missing_materials_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.handoff_summary("run-003")
            payload["returned_materials"] = [self.material("nav2_or_fixed_route_runtime_log", "run-003")]
            artifact, summary = self.build(root, payload, "run-003")

        self.assertEqual(artifact["status"], "blocked_missing_result_materials")
        self.assertIn("route_completion_signal", artifact["missing_materials"])
        self.assertIn("delivery_result", summary["missing_materials"])
        self.assertFalse(artifact["delivery_success"])

    def test_placeholder_only_materials_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.handoff_summary("run-004", with_materials=False)
            payload["returned_materials"] = [
                self.material(name, "run-004", "placeholder_required_not_collected_by_this_gate")
                for name in intake.REQUIRED_RESULT_MATERIALS
            ]
            artifact, _summary = self.build(root, payload, "run-004")

        self.assertEqual(artifact["status"], "blocked_placeholder_only_materials")
        self.assertFalse(artifact["material_completeness"]["is_complete"])

    def test_missing_bad_json_and_unsupported_schema_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_artifact, missing_summary, _ = intake.build_route_task_field_retest_result_intake(
                str(root / "missing.json"),
                "run-005",
            )
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_artifact, _bad_summary, _ = intake.build_route_task_field_retest_result_intake(str(bad_path), "run-005")
            unsupported = self.handoff_summary("run-005")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _unsupported_summary = self.build(root, unsupported, "run-005")

        self.assertEqual(missing_artifact["status"], "blocked_missing_route_task_field_retest_result")
        self.assertEqual(bad_artifact["status"], "blocked_bad_json")
        self.assertEqual(unsupported_artifact["status"], "blocked_unsupported_schema")
        self.assertFalse(missing_artifact["delivery_success"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_evidence_ref_mismatch_and_weak_bool_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mismatch = self.handoff_summary("run-006")
            mismatch["returned_materials"][0]["evidence_ref"] = "other-run"
            mismatch_artifact, _mismatch_summary = self.build(root, mismatch, "run-006")
            weak_bool = self.handoff_summary("run-007")
            weak_bool["same_evidence_ref_required"] = "true"
            weak_artifact, _weak_summary = self.build(root, weak_bool, "run-007")

        self.assertEqual(mismatch_artifact["status"], "blocked_same_evidence_ref_mismatch")
        self.assertIn("nav2_or_fixed_route_runtime_log", mismatch_artifact["material_completeness"]["same_evidence_ref_mismatches"])
        self.assertEqual(weak_artifact["status"], "blocked_same_evidence_ref_not_required")

    def test_unsafe_copy_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.handoff_summary("run-008")
            payload["returned_materials"][0]["review_note"] = (
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response /Users/m4/raw.json"
            )
            artifact, _summary = self.build(root, payload, "run-008")

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
            payload = self.handoff_summary("run-009")
            payload["delivery_success"] = True
            payload["primary_actions_enabled"] = True
            artifact, summary = self.build(root, payload, "run-009")

        self.assertEqual(artifact["status"], "blocked_success_or_control_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
