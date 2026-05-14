#!/usr/bin/env python3
"""route/task field-run execution pack gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_run_execution_pack as pack  # noqa: E402


class RouteTaskFieldRunExecutionPackTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 临时 JSON 确保测试只覆盖 Docker/local 软件 proof，不依赖 ROS2 或硬件。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def review_payload(self, evidence_ref: str) -> dict:
        # ready review 样本模拟上一轮 console 的稳定白名单字段。
        return {
            "schema": "trashbot.route_task_field_run_review_console.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_run_review_console_gate",
            "overall_status": "ready_for_operator_review",
            "review_decision": {
                "decision": "ready_for_operator_review_not_delivery_claim",
                "reason": "All software intake materials align.",
            },
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "operator_next_steps": [
                "Review the aligned software materials with support/operator.",
                "Plan the next real route/task field run using the same evidence_ref discipline.",
            ],
            "commands_to_rerun": [
                "rerun route_task_field_run_review.py --intake-json <intake_report.json> --once-json",
                "collect real route/task, HIL, and delivery evidence before any field claim",
            ],
            "phone_safe_summary": {
                "status": "ready_for_operator_review",
                "evidence_ref": evidence_ref,
                "delivery_success": False,
            },
            "not_proven": ["real_nav2_fixed_route_run", "real_hil_pass", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build_with_payload(self, root: Path, payload: dict) -> dict:
        # 公共 helper 让 case 聚焦 execution pack 契约，而非文件读写样板。
        review_path = self.write_json(root, "review.json", payload)
        result, exit_code = pack.build_execution_pack(str(review_path))
        self.assertEqual(exit_code, 0)
        return result

    def test_ready_review_becomes_execution_pack_not_delivery_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = self.build_with_payload(root, self.review_payload(str(root / "run-001.json")))

        self.assertEqual(result["schema"], "trashbot.route_task_field_run_execution_pack.v1")
        self.assertEqual(
            result["evidence_boundary"], "software_proof_docker_route_task_field_run_execution_pack_gate"
        )
        self.assertEqual(result["overall_status"], "ready_for_field_run_execution_pack")
        self.assertEqual(result["evidence_ref"], "file:run-001.json")
        self.assertTrue(result["same_evidence_ref_required"])
        self.assertEqual(result["field_run_manifest"]["execution_state"], "prepared_for_field_run")
        self.assertIn("required_material_templates", result)
        self.assertIn("first_run_commands", result)
        self.assertIn("rerun_commands", result)
        self.assertIn("phone_safe_summary", result)
        self.assertIn("real_nav2_fixed_route_run", result["not_proven"])
        self.assertIn("delivery_success", result["not_proven"])
        self.assertFalse(result["delivery_success"])
        self.assertFalse(result["primary_actions_enabled"])
        self.assertFalse(result["phone_safe_summary"]["delivery_success"])

    def test_blocked_review_stays_blocked_but_keeps_rerun_steps(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("run-002")
            payload["overall_status"] = "blocked_mismatch"
            payload["review_decision"]["decision"] = "rerun_sources_under_same_evidence_ref"
            payload["commands_to_rerun"] = ["re-export mismatched field-run materials under one evidence_ref=run-002"]
            result = self.build_with_payload(root, payload)

        self.assertEqual(result["overall_status"], "blocked_review_not_ready")
        self.assertEqual(result["field_run_manifest"]["execution_state"], "blocked_until_review_repaired")
        self.assertIn("re-export mismatched field-run materials", result["rerun_commands"][0])
        self.assertIn("same evidence_ref", " ".join(result["rerun_commands"]))
        self.assertFalse(result["delivery_success"])

    def test_missing_or_bad_review_returns_blocked_pack(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_result, _ = pack.build_execution_pack(str(root / "missing.json"))
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_result, _ = pack.build_execution_pack(str(bad_path))

        self.assertEqual(missing_result["overall_status"], "blocked_missing_review")
        self.assertEqual(bad_result["overall_status"], "blocked_read_error")
        self.assertFalse(missing_result["delivery_success"])
        self.assertFalse(bad_result["delivery_success"])

    def test_unsupported_schema_blocks_execution_pack(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("run-004")
            payload["schema"] = "trashbot.unsupported_review.v99"
            result = self.build_with_payload(root, payload)

        self.assertEqual(result["overall_status"], "blocked_unsupported_schema")
        self.assertEqual(result["field_run_manifest"]["source_review"]["schema_status"], "unsupported")
        self.assertFalse(result["delivery_success"])

    def test_delivery_or_primary_action_claim_blocks_pack(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("run-005")
            payload["delivery_success"] = True
            payload["primary_actions_enabled"] = True
            result = self.build_with_payload(root, payload)

        self.assertEqual(result["overall_status"], "blocked_review_not_ready")
        self.assertFalse(result["delivery_success"])
        self.assertFalse(result["primary_actions_enabled"])
        self.assertFalse(result["phone_safe_summary"]["delivery_success"])

    def test_unsafe_review_text_is_redacted_and_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_payload("run-006")
            payload["operator_next_steps"].append(
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response"
            )
            result = self.build_with_payload(root, payload)

        encoded = json.dumps(result, ensure_ascii=False)
        self.assertEqual(result["overall_status"], "blocked_unsafe_review")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)


if __name__ == "__main__":
    unittest.main()
