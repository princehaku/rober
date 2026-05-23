#!/usr/bin/env python3
"""verified terminal result reviewer ACK review-decision gate 的离线围栏测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是常规 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import verified_terminal_result_material_owner_response_reviewer_ack_intake as intake  # noqa: E402
import verified_terminal_result_material_owner_response_reviewer_ack_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达 reviewer ACK intake safe summary。
# 测试约束 02：accepted 只表示进入人工 review，不代表 reviewer resolution。
# 测试约束 03：missing material 只表达补证，不代表补证完成。
# 测试约束 04：reassignment 只表达人工路由变化，不启用控制。
# 测试约束 05：缺 intake/source 必须 blocked missing source intake。
# 测试约束 06：unsafe success/control/hardware/PR-resolution copy 必须 rejected。
# 测试约束 07：Robot diagnostics safe alias 必须可消费。
# 测试约束 08：输出保持 source=software_proof 与 not_proven。
# 测试约束 09：输出保持 delivery_success=false。
# 测试约束 10：输出保持 primary_actions_enabled=false。
# 测试约束 11：输出保持 safe_to_control=false。
# 测试约束 12：测试不访问 ROS graph、Nav2、硬件、云、GitHub 或手机 runtime。


class VerifiedTerminalResultReviewerAckReviewDecisionTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实外部或现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _intake_summary(
        self,
        evidence_ref: str,
        ack_state: str = intake.ACK_ACKNOWLEDGED,
        ack_reasons: list[str] | None = None,
        next_required_evidence: list[str] | None = None,
        reassignment_target: str = "reviewer-b",
    ) -> dict[str, object]:
        # source 使用上一轮 reviewer ACK intake 的安全消费面。
        return {
            "schema": intake.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": intake.CAPABILITY,
            "reviewer_ack_state": ack_state,
            "source_handoff_status": "ready_for_terminal_result_owner_response_review_handoff_not_proven",
            "evidence_boundary": intake.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "safe_command_id": "cmd-terminal-reviewer-ack-review-001",
            "command_id": "cmd-terminal-reviewer-ack-review-001",
            "terminal_result_type": "delivery",
            "same_evidence_ref_required": True,
            "ack_reasons": ack_reasons or ["reviewer ACK received for later review"],
            "next_required_evidence": next_required_evidence or ["keep reviewer ACK attached to the same safe evidence_ref"],
            "reviewer_acknowledgement": {
                "schema": intake.ACK_PACKET_SCHEMA,
                "source": "software_proof",
                "status": "not_proven",
                "reviewer_ack_state": ack_state,
                "reviewer_role": "terminal-result-reviewer",
                "reviewer_identity_label": "reviewer-a",
                "reassignment_target": reassignment_target,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "delivery_success": False,
                "safe_to_control": False,
                "primary_actions_enabled": False,
                "not_proven": True,
            },
            "not_proven": ["not_proven"],
            "not_proven_items": ["real_terminal_result", "pr5_reviewer_resolution"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "capability": intake.CAPABILITY,
                "source": "software_proof",
                "status": "not_proven",
                "reviewer_ack_state": ack_state,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
            },
        }

    def _build(self, root: Path, payload: dict[str, object], evidence_ref: str) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦六态映射和安全边界。
        input_path = self._write_json(root, "reviewer_ack_intake.json", payload)
        return gate.build_verified_terminal_result_material_owner_response_reviewer_ack_review_decision(
            str(input_path),
            evidence_ref,
        )

    def test_acknowledged_intake_maps_to_accepted_for_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._intake_summary("terminal-reviewer-decision-001"),
                "terminal-reviewer-decision-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(summary["summary_alias"], gate.ROBOT_ALIAS)
        self.assertEqual(artifact["review_decision"], gate.ACCEPTED_FOR_REVIEW)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertEqual(artifact[gate.ROBOT_ALIAS]["review_decision"], gate.ACCEPTED_FOR_REVIEW)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_missing_material_classification_is_supported_without_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._intake_summary(
                    "terminal-reviewer-decision-002",
                    ack_reasons=["missing material owner supplement still required"],
                    next_required_evidence=["backfill missing terminal result material metadata"],
                ),
                "terminal-reviewer-decision-002",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], gate.MISSING_MATERIAL)
        self.assertEqual(summary["next_required_evidence"][0]["owner"], "field-owner")
        self.assertFalse(summary["primary_actions_enabled"])

    def test_reassignment_required_is_supported_without_control_enablement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._intake_summary("terminal-reviewer-decision-003", intake.ACK_NEEDS_REASSIGNMENT),
                "terminal-reviewer-decision-003",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], gate.REASSIGNMENT_REQUIRED)
        self.assertEqual(summary["reassignment_target"], "reviewer-b")
        self.assertIn("same safe evidence_ref", json.dumps(summary["next_required_evidence"], ensure_ascii=False))
        self.assertFalse(summary["safe_to_control"])

    def test_missing_source_intake_blocks_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing, missing_summary, missing_exit = gate.build_verified_terminal_result_material_owner_response_reviewer_ack_review_decision(
                str(root / "missing-intake.json"),
                "terminal-reviewer-decision-004",
            )
            bad_path = self._write_json(root, "unsupported.json", {"schema": "unsupported", "source": "software_proof"})
            bad, _, bad_exit = gate.build_verified_terminal_result_material_owner_response_reviewer_ack_review_decision(
                str(bad_path),
                "terminal-reviewer-decision-005",
            )

        self.assertNotEqual(missing_exit, 0)
        self.assertNotEqual(bad_exit, 0)
        self.assertEqual(missing["review_decision"], gate.BLOCKED_MISSING_SOURCE_INTAKE)
        self.assertEqual(bad["review_decision"], gate.BLOCKED_MISSING_SOURCE_INTAKE)
        self.assertIn("reviewer_ack_intake_json_missing", missing["decision_reasons"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_evidence_ref_mismatch_gets_dedicated_fail_closed_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._intake_summary("terminal-reviewer-decision-006"),
                "terminal-reviewer-decision-other",
            )

        self.assertNotEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], gate.EVIDENCE_REF_MISMATCH)
        self.assertIn("evidence_ref_mismatch", artifact["decision_reasons"])
        self.assertFalse(summary["safe_to_control"])

    def test_unsafe_raw_fields_and_success_claims_reject_without_raw_copy(self) -> None:
        for key, value in (
            ("raw_material_body", "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 raw artifact"),
            ("safe_note", "delivery_success=true and PRRT_kwDOSWB9286CJ3tX resolved"),
            ("safe_to_control", True),
        ):
            with self.subTest(key=key):
                with tempfile.TemporaryDirectory() as tmp:
                    payload = self._intake_summary(f"terminal-reviewer-decision-{abs(hash(key))}")
                    payload[key] = value
                    artifact, summary, exit_code = self._build(Path(tmp), payload, payload["safe_evidence_ref"])  # type: ignore[arg-type]

                encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
                self.assertNotEqual(exit_code, 0)
                self.assertEqual(artifact["review_decision"], gate.REJECTED_UNSAFE)
                self.assertIn("delivery_success=false", encoded)
                self.assertNotIn("Bearer abc", encoded)
                self.assertNotIn("/cmd_vel", encoded)
                self.assertNotIn("/dev/ttyUSB0", encoded)
                self.assertFalse(summary["safe_copy"]["safe_to_control"])

    def test_robot_alias_wrapper_is_supported_and_pr5_stays_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {intake.ROBOT_ALIAS: self._intake_summary("terminal-reviewer-decision-007")}
            artifact, summary, exit_code = self._build(Path(tmp), payload, "terminal-reviewer-decision-007")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], gate.ACCEPTED_FOR_REVIEW)
        self.assertEqual(summary["pr5_thread"]["thread_id"], gate.PR5_THREAD_ID)
        self.assertEqual(summary["pr5_thread"]["state"], "unresolved")
        self.assertEqual(summary["pr5_thread"]["material_state"], "hardware_material_pending")

    def test_cli_and_output_surface_required_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = self._write_json(root, "reviewer_ack_intake.json", self._intake_summary("terminal-reviewer-decision-008"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "verified_terminal_result_material_owner_response_reviewer_ack_review_decision.py"),
                    "--reviewer-ack-intake-json",
                    str(input_path),
                    "--evidence-ref",
                    "terminal-reviewer-decision-008",
                    "--once-json",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(gate.CAPABILITY, result.stdout)
        self.assertIn(gate.EVIDENCE_BOUNDARY, result.stdout)
        self.assertIn(gate.ROBOT_ALIAS, result.stdout)
        self.assertIn(gate.ACCEPTED_FOR_REVIEW, result.stdout)
        self.assertIn("source=software_proof", result.stdout)
        self.assertIn("not_proven", result.stdout)
        self.assertIn("delivery_success=false", result.stdout)
        self.assertIn("primary_actions_enabled=false", result.stdout)
        self.assertIn("safe_to_control=false", result.stdout)
        self.assertIn(gate.PR5_THREAD_ID, result.stdout)


if __name__ == "__main__":
    unittest.main()
