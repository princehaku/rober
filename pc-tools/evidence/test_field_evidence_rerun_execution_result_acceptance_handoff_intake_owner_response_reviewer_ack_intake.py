#!/usr/bin/env python3
"""rerun acceptance reviewer ACK intake gate 的离线围栏测试。"""

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

import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff as previous_handoff  # noqa: E402
import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达上一跳 safe handoff，不模拟 raw field material。
# 测试约束 02：acknowledged 只表示 reviewer 收到，不代表 reviewer resolution。
# 测试约束 03：needs_reassignment 只表达人工路由变化，不启用控制。
# 测试约束 04：缺上一跳、缺 ACK、mismatch、unsafe 都必须 fail closed。
# 测试约束 05：所有输出保持 source=software_proof、software_proof、not_proven。
# 测试约束 06：所有输出保持 delivery_success=false。
# 测试约束 07：所有输出保持 primary_actions_enabled=false。
# 测试约束 08：所有输出保持 safe_to_control=false。
# 测试约束 09：测试不访问 ROS graph、Nav2、硬件、云、GitHub 或手机 runtime。


class FieldEvidenceRerunExecutionResultAcceptanceReviewerAckIntakeTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实外部或现场材料。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def previous_handoff_summary(self, evidence_ref: str, status: str = previous_handoff.READY_HANDOFF) -> dict:
        # 上一跳 source 必须显式带 capability、boundary 和同一 safe evidence_ref。
        return {
            "schema": previous_handoff.HANDOFF_SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "software_proof": True,
            "status": status,
            "handoff_status": status,
            "capability": gate.SOURCE_CAPABILITY,
            "evidence_boundary": previous_handoff.HANDOFF_BOUNDARY,
            "boundary": previous_handoff.HANDOFF_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "owner_support_reviewer_routing": {
                "owner": "field-owner",
                "support": "support",
                "reviewer": "reviewer",
            },
            "next_required_evidence": [
                "reviewer ACK packet under same evidence_ref",
                "real materials remain outside this gate",
            ],
            "safe_copy": {
                "capability": gate.SOURCE_CAPABILITY,
                "source": "software_proof",
                "status": status,
                "handoff_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
            },
            "not_proven": ["not_proven"],
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        }

    def ack_packet(self, evidence_ref: str, state: str = gate.ACK_ACKNOWLEDGED) -> dict:
        # ACK packet 只包含 reviewer-safe 标签和下一步，不包含 raw material body。
        return {
            "schema": gate.ACK_PACKET_SCHEMA,
            "source": "software_proof",
            "software_proof": True,
            "status": "not_proven",
            "reviewer_ack_state": state,
            "reviewer_role": "field-evidence-reviewer",
            "reviewer_identity_label": "reviewer-a",
            "ack_reason": "safe handoff metadata received for follow-up review",
            "owner_next_step": "keep owner response attached to this evidence_ref",
            "support_next_step": "watch for missing real field materials",
            "reviewer_next_step": "prepare separate review decision after real materials arrive",
            "next_required_evidence": [
                "same safe evidence_ref reviewer ACK summary",
                "separate true route/elevator material packet before any success claim",
            ],
            "reassignment_target": "reviewer-b",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "not_proven": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        }

    def build(self, root: Path, handoff_payload: dict, ack_payload: dict, evidence_ref: str) -> tuple[dict, dict, int]:
        # 公共 helper 让 case 聚焦状态映射和 fail-closed 边界。
        handoff_path = self.write_json(root, "handoff.json", handoff_payload)
        ack_path = self.write_json(root, "ack.json", ack_payload)
        return gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake(
            str(handoff_path),
            str(ack_path),
            evidence_ref,
        )

    def test_acknowledged_complete_safe_ack_outputs_robot_safe_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self.build(
                Path(tmp),
                self.previous_handoff_summary("rerun-reviewer-ack-001"),
                self.ack_packet("rerun-reviewer-ack-001"),
                "rerun-reviewer-ack-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_ACKNOWLEDGED)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertEqual(artifact[gate.ROBOT_ALIAS]["reviewer_ack_state"], gate.ACK_ACKNOWLEDGED)
        self.assertEqual(summary["reviewer_acknowledgement"]["reviewer_role"], "field-evidence-reviewer")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_needs_reassignment_is_supported_without_control_enablement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self.build(
                Path(tmp),
                self.previous_handoff_summary("rerun-reviewer-ack-002"),
                self.ack_packet("rerun-reviewer-ack-002", gate.ACK_NEEDS_REASSIGNMENT),
                "rerun-reviewer-ack-002",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_NEEDS_REASSIGNMENT)
        self.assertEqual(summary["reviewer_acknowledgement"]["reassignment_target"], "reviewer-b")
        self.assertIn("same safe evidence_ref", " ".join(summary["next_required_evidence"]))
        self.assertFalse(artifact["safe_to_control"])

    def test_missing_reviewer_role_needs_reassignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ack = self.ack_packet("rerun-reviewer-ack-003")
            ack.pop("reviewer_role")
            artifact, summary, exit_code = self.build(
                Path(tmp),
                self.previous_handoff_summary("rerun-reviewer-ack-003"),
                ack,
                "rerun-reviewer-ack-003",
            )

        self.assertNotEqual(exit_code, 0)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_NEEDS_REASSIGNMENT)
        self.assertIn("missing_ack_field:reviewer_role", artifact["ack_reasons"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_rejected_unsafe_material_refs_do_not_copy_raw_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ack = self.ack_packet("rerun-reviewer-ack-004")
            ack["raw_material_body"] = "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 raw artifact"
            artifact, summary, exit_code = self.build(
                Path(tmp),
                self.previous_handoff_summary("rerun-reviewer-ack-004"),
                ack,
                "rerun-reviewer-ack-004",
            )

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertNotEqual(exit_code, 0)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_REJECTED_UNSAFE)
        self.assertIn("delivery_success=false", encoded)
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)

    def test_blocked_missing_previous_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ack_path = self.write_json(root, "ack.json", self.ack_packet("rerun-reviewer-ack-005"))
            artifact, summary, exit_code = gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake(
                str(root / "missing-handoff.json"),
                str(ack_path),
                "rerun-reviewer-ack-005",
            )

        self.assertNotEqual(exit_code, 0)
        self.assertEqual(artifact["reviewer_ack_state"], gate.BLOCKED_MISSING_HANDOFF)
        self.assertIn("owner_response_review_handoff_json_missing", artifact["ack_reasons"])
        self.assertFalse(summary["delivery_success"])

    def test_evidence_ref_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self.build(
                Path(tmp),
                self.previous_handoff_summary("rerun-reviewer-ack-006"),
                self.ack_packet("other-rerun-reviewer-ack-006"),
                "rerun-reviewer-ack-006",
            )

        self.assertNotEqual(exit_code, 0)
        self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_EVIDENCE_REF_MISMATCH)
        self.assertIn("source_ack_or_requested_evidence_ref_mismatch", artifact["ack_reasons"])
        self.assertFalse(summary["safe_to_control"])

    def test_unsafe_success_o5_hil_and_pr5_claims_reject(self) -> None:
        for note in (
            "delivery_success=true",
            "Objective 5 external proof ready",
            "O1 HIL pass verified",
            "PR #5 reviewer resolved",
        ):
            with self.subTest(note=note):
                with tempfile.TemporaryDirectory() as tmp:
                    ack = self.ack_packet(f"rerun-reviewer-ack-{abs(hash(note))}")
                    ack["safe_note"] = note
                    artifact, summary, exit_code = self.build(
                        Path(tmp),
                        self.previous_handoff_summary(ack["safe_evidence_ref"]),
                        ack,
                        ack["safe_evidence_ref"],
                    )

                self.assertNotEqual(exit_code, 0)
                self.assertEqual(artifact["reviewer_ack_state"], gate.ACK_REJECTED_UNSAFE)
                self.assertFalse(summary["delivery_success"])
                self.assertFalse(summary["primary_actions_enabled"])
                self.assertFalse(summary["safe_to_control"])

    def test_cli_help_and_once_json_surface_required_literals(self) -> None:
        help_result = subprocess.run(
            [sys.executable, str(EVIDENCE_DIR / "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake.py"), "--help"],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(help_result.returncode, 0)
        self.assertIn(gate.CAPABILITY, help_result.stdout)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self.write_json(root, "handoff.json", self.previous_handoff_summary("rerun-reviewer-ack-007"))
            ack_path = self.write_json(root, "ack.json", self.ack_packet("rerun-reviewer-ack-007"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake.py"),
                    "--owner-response-review-handoff-json",
                    str(handoff_path),
                    "--reviewer-ack-json",
                    str(ack_path),
                    "--evidence-ref",
                    "rerun-reviewer-ack-007",
                    "--once-json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn(gate.CAPABILITY, result.stdout)
        self.assertIn(gate.EVIDENCE_BOUNDARY, result.stdout)
        self.assertIn("source=software_proof", result.stdout)
        self.assertIn("not_proven", result.stdout)
        self.assertIn("delivery_success=false", result.stdout)
        self.assertIn("primary_actions_enabled=false", result.stdout)
        self.assertIn("safe_to_control=false", result.stdout)


if __name__ == "__main__":
    unittest.main()
