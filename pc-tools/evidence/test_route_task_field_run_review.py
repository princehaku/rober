#!/usr/bin/env python3
"""route/task field-run review console gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_run_review as review  # noqa: E402


class RouteTaskFieldRunReviewTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 每个 case 都用临时 JSON，确保 CLI 不依赖 ROS2、Nav2 或硬件现场。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def intake_payload(self, evidence_ref: str) -> dict:
        # ready 样本覆盖上一轮 intake 的稳定机器字段，本轮 review 负责重组为 operator 决策。
        return {
            "schema": "trashbot.route_task_field_run_intake_crosscheck.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_run_intake_crosscheck_gate",
            "overall_status": "ready_for_review",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "missing_materials": [],
            "mismatch_reasons": [],
            "commands_to_rerun": [
                f"export route status JSON with evidence_ref={evidence_ref}",
                "rerun route_task_field_run_intake.py after all five materials exist",
            ],
            "phone_safe_summary": {
                "status": "ready_for_review",
                "evidence_ref": evidence_ref,
                "delivery_success": False,
            },
            "not_proven": [
                "real_nav2_fixed_route_run",
                "real_hil_pass",
                "delivery_success",
            ],
            "primary_actions_enabled": False,
            "delivery_success": False,
        }

    def build_with_payload(self, root: Path, payload: dict) -> dict:
        # 公共 helper 让测试聚焦 review 决策，而不是文件读写样板。
        intake_path = self.write_json(root, "intake.json", payload)
        report, exit_code = review.build_review(str(intake_path))
        self.assertEqual(exit_code, 0)
        return report

    def test_ready_intake_becomes_operator_review_not_delivery_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            report = self.build_with_payload(root, self.intake_payload(str(root / "run-001.json")))

        self.assertEqual(report["schema"], "trashbot.route_task_field_run_review_console.v1")
        self.assertEqual(
            report["evidence_boundary"], "software_proof_docker_route_task_field_run_review_console_gate"
        )
        self.assertEqual(report["overall_status"], "ready_for_operator_review")
        self.assertEqual(
            report["review_decision"]["decision"], "ready_for_operator_review_not_delivery_claim"
        )
        self.assertEqual(report["evidence_ref"], "file:run-001.json")
        self.assertEqual(report["missing_materials"], [])
        self.assertEqual(report["mismatch_reasons"], [])
        self.assertFalse(report["delivery_success"])
        self.assertFalse(report["primary_actions_enabled"])
        self.assertIn("real_nav2_fixed_route_run", report["not_proven"])
        self.assertIn("real_hil_pass", report["not_proven"])
        self.assertIn("delivery_success", report["not_proven"])
        self.assertIn("operator_next_steps", report)
        self.assertIn("phone_safe_summary", report)
        self.assertEqual(report["phone_safe_summary"]["delivery_success"], False)
        self.assertIn("collect real route/task", " ".join(report["commands_to_rerun"]))

    def test_missing_materials_are_collected_into_operator_steps(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.intake_payload("run-002")
            payload["overall_status"] = "blocked_missing_material"
            payload["missing_materials"] = ["runtime_log:runtime_log_missing"]
            report = self.build_with_payload(root, payload)

        self.assertEqual(report["overall_status"], "blocked_missing_material")
        self.assertEqual(report["review_decision"]["decision"], "collect_missing_materials_then_rerun_intake")
        self.assertIn("runtime_log:runtime_log_missing", report["missing_materials"])
        self.assertIn("re-export missing field-run materials", report["commands_to_rerun"][0])
        self.assertFalse(report["delivery_success"])

    def test_mismatch_gets_same_evidence_ref_decision(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.intake_payload("run-003")
            payload["overall_status"] = "blocked_mismatch"
            payload["mismatch_reasons"] = ["runtime_log:evidence_ref_mismatch:run-other!=run-003"]
            report = self.build_with_payload(root, payload)

        self.assertEqual(report["overall_status"], "blocked_mismatch")
        self.assertEqual(report["review_decision"]["decision"], "rerun_sources_under_same_evidence_ref")
        self.assertIn("runtime_log:evidence_ref_mismatch:run-other!=run-003", report["mismatch_reasons"])
        self.assertIn("same evidence_ref", report["review_decision"]["reason"])

    def test_unsupported_schema_blocks_without_exception(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.intake_payload("run-004")
            payload["schema"] = "trashbot.unsupported_intake.v99"
            report = self.build_with_payload(root, payload)

        self.assertEqual(report["overall_status"], "blocked_unsupported_schema")
        self.assertEqual(report["source_intake"]["schema_status"], "unsupported")
        self.assertEqual(report["review_decision"]["decision"], "regenerate_intake_crosscheck")

    def test_missing_or_bad_intake_still_returns_blocked_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_report, _ = review.build_review(str(root / "missing.json"))
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_report, _ = review.build_review(str(bad_path))

        self.assertEqual(missing_report["overall_status"], "blocked_missing_intake")
        self.assertEqual(bad_report["overall_status"], "blocked_read_error")
        self.assertFalse(missing_report["delivery_success"])
        self.assertFalse(bad_report["delivery_success"])

    def test_unsafe_copy_is_blocked_and_redacted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.intake_payload("run-005")
            payload["phone_safe_summary"]["operator_note"] = (
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            )
            report = self.build_with_payload(root, payload)

        encoded = json.dumps(report, ensure_ascii=False)
        self.assertEqual(report["overall_status"], "blocked_unsafe_summary")
        self.assertEqual(report["review_decision"]["decision"], "fix_support_safe_summary_then_rerun_intake")
        self.assertIn("support_safe_mobile_summary:unsafe_summary", report["missing_materials"])
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)


if __name__ == "__main__":
    unittest.main()
