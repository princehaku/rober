#!/usr/bin/env python3
"""route/task field retest result review dispatch gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_retest_result_review_dispatch as dispatch  # noqa: E402


class RouteTaskFieldRetestResultReviewDispatchTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def review_summary(self, evidence_ref: str, ready: bool = True) -> dict:
        # 样本沿用上一轮 backfill review decision summary 的安全字段，不夹带 raw artifact。
        accepted = list(dispatch.review_decision.backfill.REQUIRED_RESULT_MATERIALS) if ready else dispatch.review_decision.backfill.REQUIRED_RESULT_MATERIALS[:-1]
        missing = [] if ready else [dispatch.review_decision.backfill.REQUIRED_RESULT_MATERIALS[-1]]
        status = (
            "ready_for_field_retest_result_backfill_review_decision_not_proven"
            if ready
            else "blocked_missing_materials"
        )
        return {
            "schema": "trashbot.route_task_field_retest_result_backfill_review_decision_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate",
            "status": status,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "review_decision": {
                "decision": "accepted_for_owner_review_not_proven" if ready else "missing_materials_before_review",
                "status": status,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "accepted_materials": accepted,
            "missing_materials": missing,
            "rejected_materials": [],
            "safe_copy": {
                "evidence_ref": evidence_ref,
                "status": status,
                "accepted_materials": accepted,
                "missing_materials": missing,
                "rejected_materials": [],
            },
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(self, root: Path, payload: dict | str, evidence_ref: str = "run-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        source_path = self.write_json(root, "review_decision.json", payload)
        artifact, summary, exit_code = dispatch.build_route_task_field_retest_result_review_dispatch(
            str(source_path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_summary_builds_dispatch_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary = self.build(root, {"payload": {"summary": self.review_summary("run-001")}})

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_result_review_dispatch.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_result_review_dispatch_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_result_review_dispatch_gate",
        )
        self.assertEqual(artifact["status"], "ready_for_field_retest_result_review_dispatch_not_proven")
        self.assertEqual(artifact["source_review_decision"]["schema_status"], "supported")
        self.assertEqual(artifact["material_categories"]["missing_materials"], [])
        self.assertEqual(len(artifact["accepted_materials"]), len(dispatch.review_decision.backfill.REQUIRED_RESULT_MATERIALS))
        self.assertIn("owner_work_orders", artifact)
        self.assertIn("callback_packet_requirements", artifact)
        self.assertIn("route_task_field_retest_result_review_dispatch.py", " ".join(summary["rerun_commands"]))
        self.assertIn("not_proven", json.dumps(summary["safe_copy"], ensure_ascii=False))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_artifact_input_and_nested_safe_copy_are_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self.review_summary("run-002")
            source["schema"] = "trashbot.route_task_field_retest_result_backfill_review_decision.v1"
            artifact, summary = self.build(root, {"data": {"source_review_decision": source}}, "run-002")

        self.assertEqual(artifact["source_review_decision"]["schema"], "trashbot.route_task_field_retest_result_backfill_review_decision.v1")
        self.assertEqual(summary["safe_copy"]["accepted_materials"], list(dispatch.review_decision.backfill.REQUIRED_RESULT_MATERIALS))
        self.assertEqual(summary["owner_work_orders"][0]["evidence_ref"], "run-002")

    def test_missing_bad_json_unsupported_and_review_not_ready_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_artifact, missing_summary, _ = dispatch.build_route_task_field_retest_result_review_dispatch(
                str(root / "missing.json"),
                "run-003",
            )
            bad_artifact, _bad_summary = self.build(root, "{bad json", "run-003")
            unsupported = self.review_summary("run-003")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _unsupported_summary = self.build(root, unsupported, "run-003")
            not_ready_artifact, not_ready_summary = self.build(root, self.review_summary("run-003", ready=False), "run-003")

        self.assertEqual(missing_artifact["status"], "blocked_missing_route_task_field_retest_result_backfill_review_decision")
        self.assertEqual(bad_artifact["status"], "blocked_bad_json")
        self.assertEqual(unsupported_artifact["status"], "blocked_unsupported_schema")
        self.assertEqual(not_ready_artifact["status"], "blocked_review_decision_not_ready")
        self.assertIn("delivery_result", not_ready_summary["missing_materials"])
        self.assertFalse(missing_artifact["delivery_success"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_rejected_materials_are_reported_without_success_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = self.review_summary("run-004")
            payload["status"] = "blocked_rejected_materials"
            payload["accepted_materials"] = dispatch.review_decision.backfill.REQUIRED_RESULT_MATERIALS[:-1]
            payload["rejected_materials"] = ["task_record"]
            payload["safe_copy"]["accepted_materials"] = payload["accepted_materials"]
            payload["safe_copy"]["rejected_materials"] = ["task_record"]
            artifact, summary = self.build(root, payload, "run-004")

        self.assertEqual(artifact["status"], "blocked_review_decision_not_ready")
        self.assertEqual(artifact["rejected_materials"], ["task_record"])
        self.assertIn("repair missing or rejected review materials", json.dumps(summary["owner_work_orders"], ensure_ascii=False))

    def test_ref_mismatch_weak_same_ref_unsafe_and_control_claim_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mismatch_artifact, _mismatch_summary = self.build(root, self.review_summary("run-005"), "another-run")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            weak = self.review_summary("run-006")
            weak["same_evidence_ref_required"] = "true"
            weak_artifact, _weak_summary = self.build(root, weak, "run-006")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            unsafe = self.review_summary("run-007")
            unsafe["safe_copy"]["note"] = "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0"
            unsafe_artifact, _unsafe_summary = self.build(root, unsafe, "run-007")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            control = self.review_summary("run-008")
            control["safe_copy"]["primary_actions_enabled"] = True
            control_artifact, control_summary = self.build(root, control, "run-008")

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(mismatch_artifact["status"], "blocked_same_evidence_ref_mismatch")
        self.assertEqual(weak_artifact["status"], "blocked_same_evidence_ref_not_required")
        self.assertEqual(unsafe_artifact["status"], "blocked_unsafe_copy")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertEqual(control_artifact["status"], "blocked_success_or_control_claim")
        self.assertFalse(control_artifact["delivery_success"])
        self.assertFalse(control_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
