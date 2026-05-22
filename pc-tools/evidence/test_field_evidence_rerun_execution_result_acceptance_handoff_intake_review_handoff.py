#!/usr/bin/env python3
"""acceptance handoff intake review-handoff gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff as handoff  # noqa: E402


# 测试约束 01：fixture 只表达 safe review-decision 与 reviewer handoff metadata。
# 测试约束 02：ready review-handoff 只证明可交接，不证明现场材料为真。
# 测试约束 03：checklist 是真实材料清单，不读取真实材料。
# 测试约束 04：缺 decision、缺材料、mismatch、unsafe 都必须 fail closed。
# 测试约束 05：ready 分支 exit code 才能为 0，其他状态必须非零。
# 测试约束 06：所有输出保持 source=software_proof 与 not_proven。
# 测试约束 07：所有输出保持 safe_to_control=false。
# 测试约束 08：所有输出保持 delivery_success=false。
# 测试约束 09：所有输出保持 primary_actions_enabled=false。
# 测试约束 10：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionResultAcceptanceHandoffIntakeReviewHandoffTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def review_decision_summary(self, evidence_ref: str, ready: bool = True) -> dict:
        # 样本沿用上一轮 review-decision summary 的安全字段，不夹带 raw artifact。
        status = handoff.READY_SOURCE_DECISION if ready else "review_needs_owner_rework"
        return {
            "schema": "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_gate",
            "status": status,
            "review_decision": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_status": {
                "status": "accepted" if ready else "missing",
                "accepted_materials": list(handoff.HANDOFF_CHECKLIST) if ready else list(handoff.HANDOFF_CHECKLIST[:-1]),
                "missing_materials": [] if ready else [handoff.HANDOFF_CHECKLIST[-1]],
                "rejected_materials": [],
                "accepted_count": len(handoff.HANDOFF_CHECKLIST) if ready else len(handoff.HANDOFF_CHECKLIST) - 1,
                "required_count": len(handoff.HANDOFF_CHECKLIST),
                "is_complete": ready,
            },
            "owner_handoff": {
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "next_required_evidence": ["review handoff only"],
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_copy": {
                "source": "software_proof",
                "evidence_ref": evidence_ref,
                "safe_evidence_ref": evidence_ref,
                "status": status,
                "review_decision": status,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": list(handoff.NOT_PROVEN),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def handoff_packet(self, evidence_ref: str, materials: list[str] | None = None) -> dict:
        # handoff packet 只确认安全类别，不提交真实 field material。
        return {
            "schema": "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_support_reviewer_handoff_packet.v1",
            "schema_version": 1,
            "source": "software_proof",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "handoff_status": "ready_not_proven",
            "accepted_materials": list(materials if materials is not None else handoff.HANDOFF_CHECKLIST),
            "not_proven": "not_proven",
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(self, root: Path, decision_payload: dict | str, packet_payload: dict | str, evidence_ref: str = "review-handoff-001") -> tuple[dict, dict, int]:
        # 公共 helper 让 case 聚焦 state、boundary 和 fail-closed 规则。
        decision_path = self.write_json(root, "review_decision.json", decision_payload)
        packet_path = self.write_json(root, "handoff_packet.json", packet_payload)
        return handoff.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff(
            str(decision_path),
            str(packet_path),
            evidence_ref,
        )

    def test_ready_acceptance_review_handoff_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                {"payload": {"summary": self.review_decision_summary("review-handoff-001")}},
                {"payload": {"handoff_packet": self.handoff_packet("review-handoff-001")}},
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate",
        )
        self.assertEqual(artifact["handoff_status"], "ready_for_acceptance_review_handoff_not_proven")
        self.assertEqual(summary["handoff_status"], "ready_for_acceptance_review_handoff_not_proven")
        self.assertIn("handoff_needs_owner_rework", artifact["allowed_handoff_states"])
        self.assertIn("handoff_evidence_ref_mismatch", artifact["allowed_handoff_states"])
        self.assertIn("handoff_unsafe_rejected", artifact["allowed_handoff_states"])
        self.assertIn("blocked_missing_review_decision", artifact["allowed_handoff_states"])
        self.assertEqual(len(artifact["required_materials"]), len(handoff.HANDOFF_CHECKLIST))
        self.assertIn("true task record", json.dumps(artifact["handoff_checklist"], ensure_ascii=False))
        self.assertIn("source=software_proof", artifact["boundary_note"])
        self.assertIn("not_proven", json.dumps(summary["safe_copy"], ensure_ascii=False))
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_owner_rework_when_handoff_packet_missing_material(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                self.review_decision_summary("review-handoff-002"),
                self.handoff_packet("review-handoff-002", list(handoff.HANDOFF_CHECKLIST[:-1])),
                "review-handoff-002",
            )

        self.assertEqual(artifact["handoff_status"], "handoff_needs_owner_rework")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("true phone/browser evidence", artifact["material_status"]["missing_materials"])
        self.assertIn("handoff or rework safe material", "\n".join(summary["next_required_evidence"]))
        self.assertFalse(artifact["safe_to_control"])

    def test_evidence_ref_mismatch_is_blocked_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                self.review_decision_summary("review-handoff-003"),
                self.handoff_packet("another-review-handoff-003"),
                "review-handoff-003",
            )

        self.assertEqual(artifact["handoff_status"], "handoff_evidence_ref_mismatch")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("requested_source_handoff_evidence_ref_mismatch", artifact["handoff_reasons"])
        self.assertEqual(summary["safe_copy"]["handoff_status"], "handoff_evidence_ref_mismatch")

    def test_unsafe_and_success_claims_reject_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe = self.handoff_packet("review-handoff-004")
            unsafe["operator_note"] = "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 raw artifact"
            artifact, _summary, exit_code = self.build(
                root,
                self.review_decision_summary("review-handoff-004"),
                unsafe,
                "review-handoff-004",
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            success = self.handoff_packet("review-handoff-005")
            success["operator_note"] = "verified terminal result, external proof accepted, PR #5 reviewer resolved"
            success_artifact, success_summary, success_exit = self.build(
                root,
                self.review_decision_summary("review-handoff-005"),
                success,
                "review-handoff-005",
            )

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["handoff_status"], "handoff_unsafe_rejected")
        self.assertNotEqual(exit_code, 0)
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertEqual(success_artifact["handoff_status"], "handoff_unsafe_rejected")
        self.assertNotEqual(success_exit, 0)
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])

    def test_missing_review_decision_is_blocked_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet_path = self.write_json(root, "handoff_packet.json", self.handoff_packet("review-handoff-006"))
            artifact, summary, exit_code = handoff.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff(
                str(root / "missing_review_decision.json"),
                str(packet_path),
                "review-handoff-006",
            )

        self.assertEqual(artifact["handoff_status"], "blocked_missing_review_decision")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("review_decision_json_missing", artifact["handoff_reasons"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
