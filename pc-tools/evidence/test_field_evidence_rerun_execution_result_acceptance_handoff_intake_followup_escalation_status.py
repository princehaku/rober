#!/usr/bin/env python3
"""acceptance handoff intake follow-up escalation status gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status as followup  # noqa: E402


# 测试约束 01：fixture 只表达上一轮 safe review-handoff 与 follow-up policy。
# 测试约束 02：pending/overdue/escalated 只表示跟进状态，不证明现场材料为真。
# 测试约束 03：required materials 是安全类别清单，不读取真实材料。
# 测试约束 04：缺 source、缺材料、mismatch、unsafe 都必须 blocked。
# 测试约束 05：blocked 分支 exit code 必须非零。
# 测试约束 06：所有输出保持 source=software_proof 与 not_proven。
# 测试约束 07：所有输出保持 safe_to_control=false。
# 测试约束 08：所有输出保持 delivery_success=false。
# 测试约束 09：所有输出保持 primary_actions_enabled=false。
# 测试约束 10：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionResultAcceptanceHandoffIntakeFollowupEscalationStatusTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def review_handoff_summary(self, evidence_ref: str, ready: bool = True) -> dict:
        # 样本沿用上一轮 review-handoff summary 的安全字段，不夹带 raw artifact。
        status = followup.SOURCE_READY if ready else "handoff_needs_owner_rework"
        return {
            "schema": "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "capability": "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate",
            "status": status,
            "handoff_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_status": {
                "status": "accepted" if ready else "missing",
                "accepted_materials": list(followup.REQUIRED_FOLLOWUP_MATERIALS[:-2]) if ready else [],
                "missing_materials": [],
                "rejected_materials": [],
                "accepted_count": len(followup.REQUIRED_FOLLOWUP_MATERIALS[:-2]) if ready else 0,
                "required_count": len(followup.REQUIRED_FOLLOWUP_MATERIALS),
                "is_complete": ready,
            },
            "owner_handoff": {
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "next_required_evidence": ["follow-up status only"],
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_copy": {
                "source": "software_proof",
                "evidence_ref": evidence_ref,
                "safe_evidence_ref": evidence_ref,
                "status": status,
                "handoff_status": status,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": list(followup.NOT_PROVEN),
            "software_proof": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def followup_policy(self, evidence_ref: str, due_state: str = "pending", materials: list[str] | None = None) -> dict:
        # policy 只确认安全类别纳入跟进，不提交真实 field material。
        return {
            "schema": followup.POLICY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "due_state": due_state,
            "accepted_materials": list(materials if materials is not None else followup.REQUIRED_FOLLOWUP_MATERIALS),
            "not_proven": "not_proven",
            "software_proof": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(
        self,
        root: Path,
        handoff_payload: dict | str,
        policy_payload: dict | str,
        evidence_ref: str = "followup-001",
    ) -> tuple[dict, dict, int]:
        # 公共 helper 让 case 聚焦 due_state、boundary 和 fail-closed 规则。
        handoff_path = self.write_json(root, "review_handoff.json", handoff_payload)
        policy_path = self.write_json(root, "followup_policy.json", policy_payload)
        return followup.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status(
            str(handoff_path),
            str(policy_path),
            evidence_ref,
        )

    def test_pending_followup_status_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                {"payload": {"summary": self.review_handoff_summary("followup-001")}},
                {"payload": {"followup_escalation_policy": self.followup_policy("followup-001", "pending")}},
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], followup.SCHEMA)
        self.assertEqual(summary["schema"], followup.SUMMARY_SCHEMA)
        self.assertEqual(artifact["capability"], followup.CAPABILITY)
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate",
        )
        self.assertEqual(artifact["due_state"], "pending")
        self.assertEqual(summary["followup_status"], "pending")
        self.assertIn("overdue", artifact["allowed_due_states"])
        self.assertIn("escalated", artifact["allowed_due_states"])
        self.assertIn("blocked", artifact["allowed_due_states"])
        self.assertIn("source=software_proof", artifact["boundary_note"])
        self.assertIn("not_proven", json.dumps(summary["safe_copy"], ensure_ascii=False))
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_overdue_and_escalated_due_states_remain_software_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            overdue, _, overdue_exit = self.build(
                root,
                self.review_handoff_summary("followup-002"),
                self.followup_policy("followup-002", "overdue"),
                "followup-002",
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            escalated, escalated_summary, escalated_exit = self.build(
                root,
                self.review_handoff_summary("followup-003"),
                self.followup_policy("followup-003", "escalated"),
                "followup-003",
            )

        self.assertEqual(overdue_exit, 0)
        self.assertEqual(escalated_exit, 0)
        self.assertEqual(overdue["due_state"], "overdue")
        self.assertEqual(escalated["due_state"], "escalated")
        self.assertTrue(overdue["owner_escalation"]["escalate"])
        self.assertTrue(escalated_summary["owner_escalation"]["escalate"])
        self.assertIn("software_proof", json.dumps(escalated, ensure_ascii=False))
        self.assertFalse(overdue["delivery_success"])
        self.assertFalse(escalated["primary_actions_enabled"])

    def test_missing_review_handoff_or_required_material_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            policy_path = self.write_json(root, "followup_policy.json", self.followup_policy("followup-004"))
            missing, missing_summary, missing_exit = followup.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status(
                str(root / "missing_review_handoff.json"),
                str(policy_path),
                "followup-004",
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocked, blocked_summary, blocked_exit = self.build(
                root,
                self.review_handoff_summary("followup-005"),
                self.followup_policy("followup-005", "pending", list(followup.REQUIRED_FOLLOWUP_MATERIALS[:-1])),
                "followup-005",
            )

        self.assertEqual(missing["due_state"], "blocked")
        self.assertEqual(blocked["due_state"], "blocked")
        self.assertNotEqual(missing_exit, 0)
        self.assertNotEqual(blocked_exit, 0)
        self.assertIn("review_handoff_json_missing", missing["followup_reasons"])
        self.assertIn("followup_policy_missing_required_material_categories", blocked["followup_reasons"])
        self.assertIn("PR #5 hardware material remains pending", "\n".join(blocked_summary["material_status"]["missing_materials"]))
        self.assertFalse(missing_summary["primary_actions_enabled"])
        self.assertFalse(blocked["safe_to_control"])

    def test_evidence_ref_mismatch_is_blocked_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                self.review_handoff_summary("followup-006"),
                self.followup_policy("different-followup-006"),
                "followup-006",
            )

        self.assertEqual(artifact["due_state"], "blocked")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("requested_source_policy_evidence_ref_mismatch", artifact["followup_reasons"])
        self.assertEqual(summary["safe_copy"]["due_state"], "blocked")

    def test_unsafe_and_success_claims_reject_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe = self.followup_policy("followup-007")
            unsafe["operator_note"] = "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 raw artifact"
            artifact, _summary, exit_code = self.build(
                root,
                self.review_handoff_summary("followup-007"),
                unsafe,
                "followup-007",
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            success = self.followup_policy("followup-008")
            success["operator_note"] = "verified terminal result, external proof accepted, PR #5 reviewer resolved"
            success_artifact, success_summary, success_exit = self.build(
                root,
                self.review_handoff_summary("followup-008"),
                success,
                "followup-008",
            )

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["due_state"], "blocked")
        self.assertNotEqual(exit_code, 0)
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertEqual(success_artifact["due_state"], "blocked")
        self.assertNotEqual(success_exit, 0)
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])

    def test_unsupported_due_state_and_nonready_source_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsupported, _, unsupported_exit = self.build(
                root,
                self.review_handoff_summary("followup-009"),
                self.followup_policy("followup-009", "done"),
                "followup-009",
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nonready, _, nonready_exit = self.build(
                root,
                self.review_handoff_summary("followup-010", ready=False),
                self.followup_policy("followup-010", "pending"),
                "followup-010",
            )

        self.assertEqual(unsupported["due_state"], "blocked")
        self.assertEqual(nonready["due_state"], "blocked")
        self.assertNotEqual(unsupported_exit, 0)
        self.assertNotEqual(nonready_exit, 0)
        self.assertIn("unsupported_or_blocked_due_state", unsupported["followup_reasons"])
        self.assertIn("source_review_handoff_not_ready", nonready["followup_reasons"])


if __name__ == "__main__":
    unittest.main()
