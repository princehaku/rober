#!/usr/bin/env python3
"""route/task field-run readiness gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_run_readiness as readiness  # noqa: E402


class RouteTaskFieldRunReadinessTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试统一走临时 JSON，确保工具不依赖 ROS2、硬件或仓库外状态。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def source_payloads(self, evidence_ref: str) -> tuple[dict, dict, dict]:
        # 三个上游 artifact 都带同一 evidence_ref，覆盖 ready_for_field_run_materials happy path。
        pc = {
            "schema": "trashbot.pc_route_debug_console.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_pc_route_debug_console_gate",
            "evidence_ref": evidence_ref,
            "route_progress": {"evidence_ref": evidence_ref, "checkpoint": 1},
            "not_proven": ["delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        review = {
            "schema": "trashbot.route_task_rehearsal_operator_review.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_rehearsal_operator_review_gate",
            "evidence_ref": evidence_ref,
            "next_rehearsal_decision": {"decision": "prepare_real_route_task_materials"},
            "safe_copy": {"status": "ready_for_real_route_task_or_hil_reconciliation"},
            "not_proven": ["real_hil_pass", "delivery_success"],
            "delivery_success": False,
        }
        bundle = {
            "schema": "trashbot.route_task_rehearsal_execution_bundle",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_rehearsal_execution_bundle_gate",
            "evidence_ref": evidence_ref,
            "crosscheck_status": {"status": "pass"},
            "diagnostics_summary": {"evidence_ref": evidence_ref, "status": "available_software_proof"},
            "not_proven": ["real_nav2_fixed_route_run", "delivery_success"],
        }
        return pc, review, bundle

    def test_ready_handoff_has_required_boundary_fields(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence_ref = str(root / "run-001.json")
            pc, review, bundle = self.source_payloads(evidence_ref)
            pc_path = self.write_json(root, "pc.json", pc)
            review_path = self.write_json(root, "review.json", review)
            bundle_path = self.write_json(root, "bundle.json", bundle)

            payload, exit_code = readiness.build_readiness(
                str(pc_path), str(review_path), str(bundle_path), evidence_ref=evidence_ref
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema"], "trashbot.route_task_field_run_readiness.v1")
        self.assertEqual(
            payload["evidence_boundary"], "software_proof_docker_route_task_field_run_readiness_gate"
        )
        self.assertEqual(payload["overall_status"], "ready_for_field_run_materials")
        self.assertTrue(payload["same_evidence_ref_required"])
        self.assertFalse(payload["delivery_success"])
        self.assertFalse(payload["primary_actions_enabled"])
        self.assertIn("real_nav2_fixed_route_run", payload["not_proven"])
        self.assertIn("real_hardware_feedback", payload["not_proven"])
        self.assertIn("objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof", payload["not_proven"])
        self.assertIn("required_field_run_materials", payload)
        self.assertIn("collect fixed-route/Nav2 runtime log", " ".join(payload["commands_to_run"]))
        self.assertEqual(payload["evidence_ref"], "file:run-001.json")

    def test_missing_material_blocks_without_exception(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pc, review, _ = self.source_payloads("run-002")
            pc_path = self.write_json(root, "pc.json", pc)
            review_path = self.write_json(root, "review.json", review)

            payload, _ = readiness.build_readiness(str(pc_path), str(review_path), str(root / "missing.json"))

        self.assertEqual(payload["overall_status"], "blocked_missing_material")
        self.assertIn("execution_bundle:execution_bundle_missing", payload["missing_materials"])
        self.assertFalse(payload["delivery_success"])

    def test_unsupported_schema_blocks_conservatively(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pc, review, bundle = self.source_payloads("run-003")
            pc["schema"] = "trashbot.some_other_schema"
            pc.pop("route_progress")
            pc_path = self.write_json(root, "pc.json", pc)
            review_path = self.write_json(root, "review.json", review)
            bundle_path = self.write_json(root, "bundle.json", bundle)

            payload, _ = readiness.build_readiness(str(pc_path), str(review_path), str(bundle_path))

        self.assertEqual(payload["overall_status"], "blocked_unsupported_schema")
        self.assertIn("pc_route_debug:unsupported_schema", payload["missing_materials"])

    def test_mismatched_evidence_ref_blocks_same_ref_handoff(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pc, review, bundle = self.source_payloads("run-004")
            bundle["evidence_ref"] = "run-other"
            bundle["diagnostics_summary"]["evidence_ref"] = "run-other"
            pc_path = self.write_json(root, "pc.json", pc)
            review_path = self.write_json(root, "review.json", review)
            bundle_path = self.write_json(root, "bundle.json", bundle)

            payload, _ = readiness.build_readiness(str(pc_path), str(review_path), str(bundle_path))

        self.assertEqual(payload["overall_status"], "blocked_missing_material")
        self.assertIn("evidence_ref:sources_do_not_share_same_ref", payload["missing_materials"])

    def test_sensitive_material_is_redacted_and_blocks_unsafe_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pc, review, bundle = self.source_payloads("run-005")
            pc["route_progress"]["debug"] = "Authorization: Bearer abc /dev/ttyUSB0 baudrate=115200"
            review["safe_copy"]["operator_note"] = "Traceback (most recent call last): raw robot response"
            pc_path = self.write_json(root, "pc.json", pc)
            review_path = self.write_json(root, "review.json", review)
            bundle_path = self.write_json(root, "bundle.json", bundle)

            payload, _ = readiness.build_readiness(str(pc_path), str(review_path), str(bundle_path))

        encoded = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("baudrate=115200", encoded)
        self.assertNotIn("raw robot response", encoded)
        self.assertFalse(payload["delivery_success"])


if __name__ == "__main__":
    unittest.main()
