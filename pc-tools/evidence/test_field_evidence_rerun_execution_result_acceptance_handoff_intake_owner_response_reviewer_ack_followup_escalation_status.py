#!/usr/bin/env python3
"""reviewer ACK followup escalation status gate 的离线围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是常规包；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status as gate  # noqa: E402
import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff as handoff_gate  # noqa: E402


# 测试约束 01：fixture 只表达上一轮 safe reviewer ACK handoff，不模拟 raw ACK。
# 测试约束 02：pending/overdue/accepted 都不代表真实 owner response 完成。
# 测试约束 03：unsafe success/control/hardware copy 必须 fail closed。
# 测试约束 04：missing source 必须 blocked_missing_reviewer_ack_review_handoff_not_proven。
# 测试约束 05：source handoff 非 ready 必须 escalated_missing_real_material_not_proven。
# 测试约束 06：Robot diagnostics safe alias 必须可消费。
# 测试约束 07：same evidence_ref mismatch 必须 blocked。
# 测试约束 08：输出保持 source=software_proof 与 not_proven。
# 测试约束 09：输出保持 delivery_success=false、primary_actions_enabled=false、safe_to_control=false。
# 测试约束 10：测试不访问 ROS graph、Nav2、硬件、云或手机 runtime。


class FieldEvidenceRerunAcceptanceOwnerResponseReviewerAckFollowupEscalationStatusTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实外部或现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _handoff_summary(
        self,
        evidence_ref: str,
        handoff_status: str = handoff_gate.HANDOFF_READY,
    ) -> dict[str, object]:
        # source 使用上一轮 reviewer ACK review-handoff summary 的安全消费面。
        return {
            "schema": handoff_gate.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": handoff_gate.CAPABILITY,
            "handoff_status": handoff_status,
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff": handoff_status,
            "source_review_decision": "accepted_for_material_review_not_proven",
            "evidence_boundary": handoff_gate.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "reviewer_ack_state": "acknowledged",
            "ack_owner": "reviewer",
            "decision_reasons": ["reviewer ACK handoff fixture"],
            "handoff_reasons": ["reviewer ACK review decision ready for material handoff only"],
            "next_required_evidence": ["field owner response under same safe evidence_ref"],
            "field_owner_handoff": {
                "role": "field owner",
                "next_action": "queue_material_review_under_same_safe_evidence_ref_without_success_claim",
                "source": "software_proof",
                "status": "not_proven",
                "not_proven": True,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
            },
            "support_handoff": {
                "role": "support",
                "package_action": "send_sanitized_summary_only_to_field_owner_and_reviewer",
                "source": "software_proof",
                "status": "not_proven",
                "not_proven": True,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
            },
            "safe_copy": {
                "handoff_status": handoff_status,
                "source_review_decision": "accepted_for_material_review_not_proven",
                "reviewer_ack_state": "acknowledged",
                "safe_evidence_ref": evidence_ref,
                "source": "software_proof",
                "not_proven": True,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
            },
            "not_proven": True,
            "not_proven_items": ["real_owner_response_intake_completion"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _build(
        self,
        root: Path,
        payload: dict[str, object],
        due_status: str = "overdue",
        evidence_ref: str = "",
    ) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦状态映射和安全边界。
        source_path = self._write_json(root, "reviewer_ack_review_handoff.json", payload)
        return gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status(
            str(source_path),
            due_status,
            evidence_ref,
        )

    def test_ready_handoff_pending_maps_to_reviewer_ack_followup_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._handoff_summary("reviewer-ack-followup-901"),
                "pending",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["followup_status"], gate.PENDING_REVIEWER_ACK_FOLLOWUP)
        self.assertEqual(summary["summary_alias"], gate.ROBOT_ALIAS)
        self.assertEqual(artifact["safe_evidence_ref"], "reviewer-ack-followup-901")
        self.assertEqual(summary["source_handoff_status"], handoff_gate.HANDOFF_READY)
        self.assertEqual(summary["reviewer_ack_status"], "acknowledged")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_ready_handoff_overdue_maps_to_reviewer_ack_followup_overdue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._handoff_summary("reviewer-ack-followup-902"),
                "overdue",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["followup_status"], gate.OVERDUE_REVIEWER_ACK_FOLLOWUP)
        self.assertTrue(summary["support_escalation_owner"]["escalate"])
        self.assertIn("support escalation owner", summary["support_escalation_owner"]["role"])

    def test_ready_handoff_accepted_maps_to_real_material_reviewer_followup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._handoff_summary("reviewer-ack-followup-903"),
                "accepted",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["followup_status"], gate.READY_FOR_REAL_MATERIAL_REVIEWER_FOLLOWUP)
        self.assertIn("objective_5_external_cloud_4g_oss_cdn_db_queue_proof", summary["missing_required_evidence"])
        self.assertIn("real-material reviewer followup", summary["next_required_evidence"][0])

    def test_non_ready_source_handoff_blocks_missing_required_materials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._handoff_summary("reviewer-ack-followup-904", handoff_gate.HANDOFF_FIELD_OWNER_SUPPLEMENT),
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["followup_status"], gate.ESCALATED_MISSING_REAL_MATERIAL)
        self.assertIn("source_reviewer_ack_handoff_not_ready_for_followup", summary["followup_reasons"])

    def test_unsafe_claims_fail_closed_without_raw_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = self._handoff_summary("reviewer-ack-followup-905")
            payload["safe_note"] = "delivery_success=true"
            artifact, summary, exit_code = self._build(Path(tmp), payload)

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["followup_status"], gate.ESCALATED_MISSING_REAL_MATERIAL)
        self.assertIn("delivery_success_true_overclaim", summary["rejected_or_unsafe_reasons"])
        self.assertFalse(summary["proof_flags"]["delivery_success"])
        self.assertNotIn("delivery_success=true", encoded)

    def test_missing_handoff_maps_to_blocked_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status(
                str(Path(tmp) / "missing-reviewer-ack-handoff.json")
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["followup_status"], gate.BLOCKED_MISSING_REVIEWER_ACK_REVIEW_HANDOFF)
        self.assertIn("reviewer_ack_review_handoff_input_missing", artifact["followup_reasons"])
        self.assertEqual(summary["safe_evidence_ref"], "")
        self.assertFalse(summary["primary_actions_enabled"])

    def test_robot_alias_wrapper_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {handoff_gate.ROBOT_ALIAS: self._handoff_summary("reviewer-ack-followup-906")}
            artifact, summary, exit_code = self._build(Path(tmp), payload, "pending")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["followup_status"], gate.PENDING_REVIEWER_ACK_FOLLOWUP)
        self.assertEqual(artifact["safe_evidence_ref"], "reviewer-ack-followup-906")
        self.assertEqual(summary["source_schema"], handoff_gate.SUMMARY_SCHEMA)

    def test_expected_evidence_ref_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._handoff_summary("reviewer-ack-followup-907"),
                "pending",
                "reviewer-ack-followup-other",
            )

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["followup_status"], gate.BLOCKED_MISSING_REVIEWER_ACK_REVIEW_HANDOFF)
        self.assertIn("evidence_ref_mismatch", summary["followup_reasons"])

    def test_cli_prints_overdue_status_for_safe_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = self._write_json(root, "handoff.json", self._handoff_summary("reviewer-ack-followup-908"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.py"),
                    "--input",
                    str(source_path),
                    "--due-status",
                    "overdue",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn(gate.OVERDUE_REVIEWER_ACK_FOLLOWUP, result.stdout)
        self.assertIn("software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate", result.stdout)

    def test_output_preserves_required_boundary_literals_and_no_raw_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, _ = self._build(Path(tmp), self._handoff_summary("reviewer-ack-followup-909"), "accepted")

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status", encoded)
        self.assertIn("software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn(gate.PENDING_REVIEWER_ACK_FOLLOWUP, encoded)
        self.assertIn(gate.OVERDUE_REVIEWER_ACK_FOLLOWUP, encoded)
        self.assertIn(gate.ESCALATED_MISSING_REAL_MATERIAL, encoded)
        self.assertIn(gate.BLOCKED_MISSING_REVIEWER_ACK_REVIEW_HANDOFF, encoded)
        self.assertIn(gate.READY_FOR_REAL_MATERIAL_REVIEWER_FOLLOWUP, encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertNotIn("raw artifact", encoded)


if __name__ == "__main__":
    unittest.main()
