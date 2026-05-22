#!/usr/bin/env python3
"""acceptance owner response review decision gate 的围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake as intake  # noqa: E402
import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达上一轮 safe owner response intake 和 review packet。
# 测试约束 02：ready 只表示 ready_for_owner_response_review_handoff_not_proven。
# 测试约束 03：missing/rework/ref-mismatch/unsafe/blocked 均保持 fail-closed。
# 测试约束 04：同一 safe evidence_ref 是 source 与 review packet 的硬约束。
# 测试约束 05：success/control/O5/HIL/PR #5 resolution claim 必须 rejected。
# 测试约束 06：PR #5 thread X 必须保持 unresolved / hardware_material_pending。
# 测试约束 07：输出保持 source=software_proof、software_proof 和 not_proven。
# 测试约束 08：输出保持 delivery_success=false。
# 测试约束 09：输出保持 primary_actions_enabled=false。
# 测试约束 10：输出保持 safe_to_control=false。
# 测试约束 11：测试不访问 ROS graph、硬件、外部云、手机 runtime 或 raw logs。


class FieldEvidenceRerunExecutionResultAcceptanceOwnerResponseReviewDecisionTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不模拟真实现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _owner_response_intake_summary(self, evidence_ref: str, status: str = "accepted") -> dict[str, object]:
        # source 使用上一轮 owner response intake 的安全消费面。
        return {
            "schema": intake.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": intake.CAPABILITY,
            "evidence_boundary": intake.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake": status,
            "owner_response_status": status,
            "allowed_owner_response_statuses": list(intake.ALLOWED_OWNER_RESPONSE_STATUSES),
            "owner_response_reasons": ["accepted_for_review_not_proven"],
            "accepted_materials": list(intake.REQUIRED_OWNER_RESPONSE_MATERIALS) if status == "accepted" else [],
            "missing_materials": [] if status == "accepted" else ["true phone/browser evidence"],
            "rejected_materials": [],
            "blocked_materials": [],
            "required_owner_response_materials": list(intake.REQUIRED_OWNER_RESPONSE_MATERIALS),
            "not_proven": True,
            "software_proof": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "source": "software_proof",
                "status": "not_proven",
                "owner_response_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "accepted_materials": list(intake.REQUIRED_OWNER_RESPONSE_MATERIALS) if status == "accepted" else [],
                "missing_materials": [] if status == "accepted" else ["true phone/browser evidence"],
                "rejected_materials": [],
                "blocked_materials": [],
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "evidence_boundary": intake.EVIDENCE_BOUNDARY,
            },
        }

    def _review_packet(self, evidence_ref: str) -> dict[str, object]:
        # review 样本只给安全类别索引，不携带真实 raw field log。
        return {
            "schema": gate.REVIEW_PACKET_SCHEMA,
            "source": "software_proof",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "materials": {
                name: {
                    "name": name,
                    "status": "confirmed",
                    "safe_evidence_ref": evidence_ref,
                    "summary": f"sanitized review category index for {name}",
                    "delivery_success": False,
                    "safe_to_control": False,
                    "primary_actions_enabled": False,
                }
                for name in gate.REQUIRED_REVIEW_MATERIALS
            },
            "not_proven": "not_proven",
            "software_proof": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        }

    def _build(
        self,
        root: Path,
        source_payload: dict[str, object],
        review_payload: dict[str, object],
        evidence_ref: str = "field-rerun-owner-review-101",
    ) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦分类和安全边界。
        source_path = self._write_json(root, "owner-response-intake.json", source_payload)
        review_path = self._write_json(root, "owner-response-review.json", review_payload)
        return gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision(
            str(source_path),
            str(review_path),
            evidence_ref,
        )

    def test_safe_complete_review_packet_is_ready_for_handoff_not_proven_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._owner_response_intake_summary("field-rerun-owner-review-101"),
                self._review_packet("field-rerun-owner-review-101"),
            )

        encoded = json.dumps(summary, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["capability"], gate.CAPABILITY)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertEqual(artifact["owner_response_review_decision"], gate.READY)
        self.assertEqual(len(artifact["review_confirmed_materials"]), len(gate.REQUIRED_REVIEW_MATERIALS))
        self.assertEqual(artifact["review_needs_rework_materials"], [])
        self.assertIn("ready_for_owner_response_review_handoff_not_proven", encoded)
        self.assertIn("source=software_proof", artifact["boundary_note"])
        self.assertIn("no OKR percentage lift", encoded)
        self.assertEqual(artifact["pr5_thread"]["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(artifact["pr5_thread"]["state"], "unresolved")
        self.assertEqual(artifact["pr5_thread"]["material_state"], "hardware_material_pending")
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["safe_to_control"])

    def test_missing_required_review_material_needs_owner_rework(self) -> None:
        packet = self._review_packet("field-rerun-owner-review-102")
        materials = packet["materials"]
        self.assertIsInstance(materials, dict)
        materials.pop("true phone/browser evidence")
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._owner_response_intake_summary("field-rerun-owner-review-102"),
                packet,
                "field-rerun-owner-review-102",
            )

        self.assertEqual(artifact["owner_response_review_decision"], gate.NEEDS_REWORK)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("true phone/browser evidence", artifact["review_needs_rework_materials"])
        self.assertIn("missing_or_incomplete_required_review_material_not_proven", artifact["decision_reasons"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_unsafe_or_rejected_material_refs_are_rejected(self) -> None:
        packet = self._review_packet("field-rerun-owner-review-103")
        materials = packet["materials"]
        self.assertIsInstance(materials, dict)
        materials["delivery result"] = {
            "name": "delivery result",
            "status": "rejected",
            "safe_evidence_ref": "field-rerun-owner-review-103",
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._owner_response_intake_summary("field-rerun-owner-review-103"),
                packet,
                "field-rerun-owner-review-103",
            )

        self.assertEqual(artifact["owner_response_review_decision"], gate.UNSAFE_REJECTED)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("delivery result", artifact["review_unsafe_rejected_materials"])
        self.assertIn("unsafe_owner_response_review_material_not_proven", json.dumps(summary, ensure_ascii=False))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["safe_to_control"])

    def test_blocked_missing_previous_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_source = root / "missing-owner-response-intake.json"
            review_path = self._write_json(root, "owner-response-review.json", self._review_packet("field-rerun-owner-review-104"))
            artifact, summary, exit_code = gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision(
                str(missing_source),
                str(review_path),
                "field-rerun-owner-review-104",
            )

        self.assertEqual(artifact["owner_response_review_decision"], gate.BLOCKED_MISSING_INTAKE)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("owner_response_intake_json_missing", artifact["decision_reasons"])
        self.assertIn("blocked_missing_owner_response_intake", json.dumps(summary, ensure_ascii=False))
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_evidence_ref_mismatch_uses_ref_mismatch_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._owner_response_intake_summary("field-rerun-owner-review-105"),
                self._review_packet("other-field-rerun-owner-review-105"),
                "field-rerun-owner-review-105",
            )

        self.assertEqual(artifact["owner_response_review_decision"], gate.REF_MISMATCH)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("review_packet_evidence_ref_mismatch", artifact["decision_reasons"])
        self.assertIn("review_evidence_ref_mismatch", json.dumps(summary, ensure_ascii=False))
        self.assertFalse(artifact["safe_to_control"])

    def test_unsafe_success_o5_hil_and_pr5_resolution_claim_rejected_without_copy(self) -> None:
        unsafe_packet = self._review_packet("field-rerun-owner-review-106")
        unsafe_packet["operator_note"] = "delivery_success=true with O5 external proof, O1 HIL pass, and PR #5 reviewer resolved"
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._owner_response_intake_summary("field-rerun-owner-review-106"),
                unsafe_packet,
                "field-rerun-owner-review-106",
            )

        encoded = json.dumps(summary, ensure_ascii=False)
        self.assertEqual(artifact["owner_response_review_decision"], gate.UNSAFE_REJECTED)
        self.assertNotEqual(exit_code, 0)
        self.assertIn("unsafe_path_credential_ros_control_hardware_success_or_resolution_claim", artifact["decision_reasons"])
        self.assertNotIn("reviewer resolved", encoded)
        self.assertNotIn("delivery_success=true", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_cli_help_and_once_json_include_required_literals(self) -> None:
        help_result = subprocess.run(
            [
                sys.executable,
                str(EVIDENCE_DIR / "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision.py"),
                "--help",
            ],
            check=False,
            text=True,
            capture_output=True,
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._write_json(root, "owner-response-intake.json", self._owner_response_intake_summary("field-rerun-owner-review-107"))
            review = self._write_json(root, "owner-response-review.json", self._review_packet("field-rerun-owner-review-107"))
            run_result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision.py"),
                    "--owner-response-intake-json",
                    str(source),
                    "--owner-response-review-json",
                    str(review),
                    "--evidence-ref",
                    "field-rerun-owner-review-107",
                    "--once-json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(help_result.returncode, 0)
        self.assertIn("--owner-response-intake-json", help_result.stdout)
        self.assertIn("--owner-response-review-json", help_result.stdout)
        self.assertEqual(run_result.returncode, 0)
        self.assertIn(gate.CAPABILITY, run_result.stdout)
        self.assertIn(gate.EVIDENCE_BOUNDARY, run_result.stdout)
        self.assertIn("source=software_proof", run_result.stdout)
        self.assertIn("not_proven", run_result.stdout)
        self.assertIn("delivery_success", run_result.stdout)
        self.assertIn("primary_actions_enabled", run_result.stdout)
        self.assertIn("safe_to_control", run_result.stdout)
        self.assertIn(gate.READY, run_result.stdout)
        self.assertIn(gate.NEEDS_REWORK, run_result.stdout)
        self.assertIn(gate.REF_MISMATCH, run_result.stdout)
        self.assertIn(gate.UNSAFE_REJECTED, run_result.stdout)
        self.assertIn(gate.BLOCKED_MISSING_INTAKE, run_result.stdout)


if __name__ == "__main__":
    unittest.main()
