#!/usr/bin/env python3
"""route/task field retest result acceptance packet gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import route_task_field_retest_result_acceptance_packet as packet  # noqa: E402


class RouteTaskFieldRetestResultAcceptancePacketTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def reconciliation_artifact(self, evidence_ref: str, ready: bool = True) -> dict:
        # 样本沿用上一轮 result reconciliation 的 artifact/summary 形态。
        status = (
            "ready_for_field_retest_result_reconciliation_not_proven"
            if ready
            else "blocked_missing_result_materials"
        )
        missing = [] if ready else ["delivery_result"]
        materials = {
            name: {
                "status": "provided",
                "evidence_ref": evidence_ref,
                "placeholder": False,
            }
            for name in packet.REQUIRED_RESULT_MATERIALS
        }
        if not ready:
            materials["delivery_result"]["status"] = "missing"
        return {
            "schema": "trashbot.route_task_field_retest_result_reconciliation.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_result_reconciliation_gate",
            "status": status,
            "reconciliation_verdict": status,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": {
                "required": True,
                "input_required_value": True,
                "evidence_ref": evidence_ref,
                "status": "aligned" if ready else "blocked",
                "missing_materials": missing,
                "mismatched_materials": [],
            },
            "source_result_intake_schema": "trashbot.route_task_field_retest_result_intake.v1",
            "source_result_intake_status": "ready_for_field_retest_result_intake_not_proven",
            "source_review_result_handoff_schema": "trashbot.route_task_field_retest_review_result_handoff.v1",
            "source_review_result_handoff_status": "ready_for_result_intake_handoff",
            "required_result_materials": list(packet.REQUIRED_RESULT_MATERIALS),
            "result_materials": materials,
            "missing_materials": missing,
            "mismatch_reasons": [],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(self, root: Path, payload: dict, evidence_ref: str = "run-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        path = self.write_json(root, "reconciliation.json", payload)
        artifact, summary, exit_code = packet.build_route_task_field_retest_result_acceptance_packet(
            str(path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_complete_reconciliation_builds_acceptance_packet_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact, summary = self.build(root, {"payload": {"artifact": self.reconciliation_artifact("run-001")}})

        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_result_acceptance_packet.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_result_acceptance_packet_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_result_acceptance_packet_gate",
        )
        self.assertEqual(artifact["status"], "ready_for_field_retest_result_acceptance_packet_not_proven")
        self.assertEqual(artifact["missing_materials"], [])
        self.assertEqual(artifact["mismatch_reasons"], [])
        self.assertEqual(artifact["safe_lineage"]["source_result_intake_schema"], "trashbot.route_task_field_retest_result_intake.v1")
        self.assertIn("owner_handoff", artifact)
        self.assertIn("rerun_commands", artifact)
        self.assertIn("pass_fail_criteria", artifact)
        self.assertIn("delivery_result", artifact["result_material_statuses"])
        self.assertIn("real_delivery_success", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_nested_summary_input_is_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            summary_input = self.reconciliation_artifact("run-002")
            summary_input["schema"] = "trashbot.route_task_field_retest_result_reconciliation_summary.v1"
            artifact, summary = self.build(root, {"data": {"result_reconciliation_summary": summary_input}}, "run-002")

        self.assertEqual(artifact["source_reconciliation"]["schema_status"], "supported")
        self.assertEqual(summary["status"], "ready_for_field_retest_result_acceptance_packet_not_proven")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertIn("route_task_field_retest_result_reconciliation.py", " ".join(summary["rerun_commands"]))

    def test_blocked_reconciliation_and_missing_materials_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            blocked = self.reconciliation_artifact("run-003", ready=False)
            artifact, summary = self.build(root, blocked, "run-003")

        self.assertEqual(artifact["status"], "blocked_reconciliation_not_ready")
        self.assertIn("delivery_result", artifact["missing_materials"])
        self.assertIn("delivery_result", summary["acceptance_gap_summary"]["missing_materials"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_bad_json_unsupported_and_ref_mismatch_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing_artifact, missing_summary, _ = packet.build_route_task_field_retest_result_acceptance_packet(
                str(root / "missing.json"),
                "run-004",
            )
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_artifact, _bad_summary, _ = packet.build_route_task_field_retest_result_acceptance_packet(
                str(bad_path),
                "run-004",
            )
            unsupported = self.reconciliation_artifact("run-004")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _unsupported_summary = self.build(root, unsupported, "run-004")
            mismatch = self.reconciliation_artifact("run-005")
            mismatch_artifact, _mismatch_summary = self.build(root, mismatch, "another-run")

        self.assertEqual(missing_artifact["status"], "blocked_missing_route_task_field_retest_result_reconciliation")
        self.assertEqual(bad_artifact["status"], "blocked_bad_json")
        self.assertEqual(unsupported_artifact["status"], "blocked_unsupported_schema")
        self.assertEqual(mismatch_artifact["status"], "blocked_same_evidence_ref_not_required")
        self.assertFalse(missing_artifact["delivery_success"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_weak_bool_mismatched_material_unsafe_and_success_claim_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            weak_bool = self.reconciliation_artifact("run-006")
            weak_bool["same_evidence_ref_required"] = "true"
            weak_artifact, _weak_summary = self.build(root, weak_bool, "run-006")
            mismatched = self.reconciliation_artifact("run-007")
            mismatched["same_evidence_ref_status"]["mismatched_materials"] = ["task_record"]
            mismatch_artifact, _mismatch_summary = self.build(root, mismatched, "run-007")
            unsafe = self.reconciliation_artifact("run-008")
            unsafe["result_materials"]["nav2_or_fixed_route_runtime_log"]["status"] = (
                "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 baudrate=115200 raw robot response /Users/m4/raw.json"
            )
            unsafe_artifact, _unsafe_summary = self.build(root, unsafe, "run-008")
            success = self.reconciliation_artifact("run-009")
            success["delivery_success"] = True
            success["primary_actions_enabled"] = True
            success_artifact, success_summary = self.build(root, success, "run-009")

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(weak_artifact["status"], "blocked_same_evidence_ref_not_required")
        self.assertEqual(mismatch_artifact["status"], "blocked_same_evidence_ref_mismatch")
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
