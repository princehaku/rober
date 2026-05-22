#!/usr/bin/env python3
"""field evidence rerun acceptance handoff intake gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_acceptance_handoff_intake as intake  # noqa: E402


# 测试约束 01：fixture 只表达 safe review-handoff 与 owner/support metadata。
# 测试约束 02：ready intake 只证明入口可复账，不证明现场材料为真。
# 测试约束 03：checklist 是真实材料清单，不读取真实材料。
# 测试约束 04：缺 review handoff、缺材料、mismatch、unsafe 都必须 fail closed。
# 测试约束 05：ready 分支 exit code 才能为 0，其他状态必须非零。
# 测试约束 06：所有输出保持 source=software_proof 与 not_proven。
# 测试约束 07：所有输出保持 safe_to_control=false。
# 测试约束 08：所有输出保持 delivery_success=false。
# 测试约束 09：所有输出保持 primary_actions_enabled=false。
# 测试约束 10：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionResultAcceptanceHandoffIntakeTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def review_handoff_summary(self, evidence_ref: str, ready: bool = True) -> dict:
        # 样本沿用上一轮 handoff summary 的安全字段，不夹带 raw artifact。
        status = intake.READY_SOURCE_HANDOFF if ready else "handoff_needs_more_material"
        return {
            "schema": "trashbot.field_evidence_rerun_execution_result_acceptance_review_handoff_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate",
            "status": status,
            "handoff_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_status": {
                "status": "accepted" if ready else "missing",
                "accepted_materials": list(intake.REQUIRED_OWNER_INTAKE_MATERIALS) if ready else list(intake.REQUIRED_OWNER_INTAKE_MATERIALS[:-1]),
                "missing_materials": [] if ready else [intake.REQUIRED_OWNER_INTAKE_MATERIALS[-1]],
                "rejected_materials": [],
                "accepted_count": len(intake.REQUIRED_OWNER_INTAKE_MATERIALS) if ready else len(intake.REQUIRED_OWNER_INTAKE_MATERIALS) - 1,
                "required_count": len(intake.REQUIRED_OWNER_INTAKE_MATERIALS),
                "is_complete": ready,
            },
            "owner_handoff": {
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "next_required_evidence": ["owner/support intake only"],
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
            "not_proven": list(intake.NOT_PROVEN),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def owner_packet(self, evidence_ref: str, materials: list[str] | None = None) -> dict:
        # owner/support packet 只确认安全类别，不提交真实 field material。
        return {
            "schema": "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_owner_intake.v1",
            "schema_version": 1,
            "source": "software_proof",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "acknowledged_materials": list(materials if materials is not None else intake.REQUIRED_OWNER_INTAKE_MATERIALS),
            "not_proven": "not_proven",
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(self, root: Path, handoff_payload: dict | str, owner_payload: dict | str, evidence_ref: str = "handoff-intake-001") -> tuple[dict, dict, int]:
        # 公共 helper 让 case 聚焦 state、boundary 和 fail-closed 规则。
        handoff_path = self.write_json(root, "review_handoff.json", handoff_payload)
        owner_path = self.write_json(root, "owner_intake.json", owner_payload)
        return intake.build_field_evidence_rerun_execution_result_acceptance_handoff_intake(
            str(handoff_path),
            str(owner_path),
            evidence_ref,
        )

    def test_ready_intake_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                {"payload": {"summary": self.review_handoff_summary("handoff-intake-001")}},
                {"payload": {"owner_intake": self.owner_packet("handoff-intake-001")}},
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_gate",
        )
        self.assertEqual(artifact["intake_status"], "ready_for_acceptance_handoff_owner_intake_not_proven")
        self.assertEqual(summary["intake_status"], "ready_for_acceptance_handoff_owner_intake_not_proven")
        self.assertIn("intake_needs_more_material", artifact["allowed_intake_states"])
        self.assertIn("intake_evidence_ref_mismatch", artifact["allowed_intake_states"])
        self.assertIn("intake_unsafe_rejected", artifact["allowed_intake_states"])
        self.assertIn("blocked_missing_review_handoff", artifact["allowed_intake_states"])
        self.assertEqual(len(artifact["required_materials"]), len(intake.REQUIRED_OWNER_INTAKE_MATERIALS))
        self.assertIn("true task record", json.dumps(artifact["intake_checklist"], ensure_ascii=False))
        self.assertIn("source=software_proof", artifact["boundary_note"])
        self.assertIn("not_proven", json.dumps(summary["safe_copy"], ensure_ascii=False))
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_material_needs_more_material_and_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                self.review_handoff_summary("handoff-intake-002"),
                self.owner_packet("handoff-intake-002", list(intake.REQUIRED_OWNER_INTAKE_MATERIALS[:-1])),
                "handoff-intake-002",
            )

        self.assertEqual(artifact["intake_status"], "intake_needs_more_material")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("true phone/browser evidence", artifact["material_status"]["missing_materials"])
        self.assertIn("provide safe owner/support acknowledgement", "\n".join(summary["next_required_evidence"]))
        self.assertFalse(artifact["safe_to_control"])

    def test_evidence_ref_mismatch_is_blocked_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = self.build(
                root,
                self.review_handoff_summary("handoff-intake-003"),
                self.owner_packet("another-intake-003"),
                "handoff-intake-003",
            )

        self.assertEqual(artifact["intake_status"], "intake_evidence_ref_mismatch")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("requested_source_owner_evidence_ref_mismatch", artifact["intake_reasons"])
        self.assertEqual(summary["safe_copy"]["intake_status"], "intake_evidence_ref_mismatch")

    def test_unsafe_and_success_claims_reject_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe = self.owner_packet("handoff-intake-004")
            unsafe["operator_note"] = "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 raw artifact"
            artifact, _summary, exit_code = self.build(
                root,
                self.review_handoff_summary("handoff-intake-004"),
                unsafe,
                "handoff-intake-004",
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            success = self.owner_packet("handoff-intake-005")
            success["operator_note"] = "verified terminal result, external proof accepted, PR #5 reviewer resolved"
            success_artifact, success_summary, success_exit = self.build(
                root,
                self.review_handoff_summary("handoff-intake-005"),
                success,
                "handoff-intake-005",
            )

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(artifact["intake_status"], "intake_unsafe_rejected")
        self.assertNotEqual(exit_code, 0)
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertEqual(success_artifact["intake_status"], "intake_unsafe_rejected")
        self.assertNotEqual(success_exit, 0)
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])

    def test_missing_review_handoff_is_blocked_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            owner_path = self.write_json(root, "owner_intake.json", self.owner_packet("handoff-intake-006"))
            artifact, summary, exit_code = intake.build_field_evidence_rerun_execution_result_acceptance_handoff_intake(
                str(root / "missing_review_handoff.json"),
                str(owner_path),
                "handoff-intake-006",
            )

        self.assertEqual(artifact["intake_status"], "blocked_missing_review_handoff")
        self.assertNotEqual(exit_code, 0)
        self.assertIn("review_handoff_json_missing", artifact["intake_reasons"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
