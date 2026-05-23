#!/usr/bin/env python3
"""verified terminal result reviewer ACK review-handoff gate 的离线围栏测试。"""

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

import verified_terminal_result_material_owner_response_reviewer_ack_review_decision as decision_gate  # noqa: E402
import verified_terminal_result_material_owner_response_reviewer_ack_review_handoff as gate  # noqa: E402


# 测试约束 01：fixture 只表达 reviewer ACK review-decision safe summary。
# 测试约束 02：ready 只表示可 handoff 给人工 reviewer，不代表材料通过。
# 测试约束 03：missing material 只表达补证，不代表补证完成。
# 测试约束 04：reassignment 只表达人工路由变化，不启用控制。
# 测试约束 05：缺 review-decision 必须 blocked missing source review-decision。
# 测试约束 06：unsafe success/control/hardware/PR-resolution copy 必须 rejected。
# 测试约束 07：Robot diagnostics safe alias 必须可消费。
# 测试约束 08：输出保持 source=software_proof 与 not_proven。
# 测试约束 09：输出保持 delivery_success=false。
# 测试约束 10：输出保持 primary_actions_enabled=false。
# 测试约束 11：输出保持 safe_to_control=false。
# 测试约束 12：测试不访问 ROS graph、Nav2、硬件、云、GitHub 或手机 runtime。


class VerifiedTerminalResultReviewerAckReviewHandoffTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实外部或现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _decision_summary(
        self,
        evidence_ref: str,
        review_decision: str = decision_gate.ACCEPTED_FOR_REVIEW,
        decision_reasons: list[str] | None = None,
        next_required_evidence: list[str] | None = None,
    ) -> dict[str, object]:
        # source 使用上一轮 reviewer ACK review-decision 的安全消费面。
        return {
            "schema": decision_gate.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": decision_gate.CAPABILITY,
            "summary_alias": decision_gate.ROBOT_ALIAS,
            "evidence_boundary": decision_gate.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "safe_command_id": "cmd-terminal-reviewer-handoff-001",
            "command_id": "cmd-terminal-reviewer-handoff-001",
            "terminal_result_type": "delivery",
            "same_evidence_ref_required": True,
            "reviewer_ack_state": "reviewer_acknowledged_not_proven",
            "review_decision": review_decision,
            "decision_reasons": decision_reasons or ["reviewer ACK intake accepted for later review only"],
            "next_required_evidence": next_required_evidence or ["keep reviewer ACK attached to the same safe evidence_ref"],
            "reviewer_role": "terminal-result-reviewer",
            "reviewer_identity_label": "reviewer-a",
            "reassignment_target": "reviewer-b",
            "review_handoff_recommendation": "handoff_to_reviewer_ack_review_not_proven",
            "pr5_thread": {
                "thread_id": gate.PR5_THREAD_ID,
                "state": "unresolved",
                "material_state": "hardware_material_pending",
            },
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "capability": decision_gate.CAPABILITY,
                "source": "software_proof",
                "status": "not_proven",
                "review_decision": review_decision,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
            },
        }

    def _build(self, root: Path, payload: dict[str, object], evidence_ref: str) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦六态映射和安全边界。
        input_path = self._write_json(root, "reviewer_ack_review_decision.json", payload)
        return gate.build_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff(
            str(input_path),
            evidence_ref,
        )

    def test_accepted_decision_maps_to_real_material_reviewer_handoff_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._decision_summary("terminal-reviewer-handoff-001"),
                "terminal-reviewer-handoff-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(summary["summary_alias"], gate.ROBOT_ALIAS)
        self.assertEqual(artifact["handoff_status"], gate.READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertEqual(artifact[gate.ROBOT_ALIAS]["handoff_status"], gate.READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_missing_material_and_reassignment_are_supported_without_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing, missing_summary, missing_exit = self._build(
                Path(tmp),
                self._decision_summary(
                    "terminal-reviewer-handoff-002",
                    decision_gate.MISSING_MATERIAL,
                    ["missing material remains before reviewer ACK review"],
                    ["backfill missing terminal result material metadata"],
                ),
                "terminal-reviewer-handoff-002",
            )
            reassigned, reassigned_summary, reassigned_exit = self._build(
                Path(tmp),
                self._decision_summary("terminal-reviewer-handoff-003", decision_gate.REASSIGNMENT_REQUIRED),
                "terminal-reviewer-handoff-003",
            )

        self.assertEqual(missing_exit, 0)
        self.assertEqual(reassigned_exit, 0)
        self.assertEqual(missing["handoff_status"], gate.MISSING_MATERIAL)
        self.assertEqual(reassigned["handoff_status"], gate.REASSIGNMENT_REQUIRED)
        self.assertEqual(missing_summary["next_required_evidence"][0]["owner"], "field-owner")
        self.assertEqual(reassigned_summary["reassignment_target"], "reviewer-b")
        self.assertFalse(missing_summary["primary_actions_enabled"])
        self.assertFalse(reassigned_summary["safe_to_control"])

    def test_missing_source_review_decision_blocks_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing, missing_summary, missing_exit = gate.build_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff(
                str(root / "missing-decision.json"),
                "terminal-reviewer-handoff-004",
            )
            bad_path = self._write_json(root, "unsupported.json", {"schema": "unsupported", "source": "software_proof"})
            bad, _, bad_exit = gate.build_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff(
                str(bad_path),
                "terminal-reviewer-handoff-005",
            )

        self.assertNotEqual(missing_exit, 0)
        self.assertNotEqual(bad_exit, 0)
        self.assertEqual(missing["handoff_status"], gate.BLOCKED_MISSING_SOURCE_REVIEW_DECISION)
        self.assertEqual(bad["handoff_status"], gate.BLOCKED_MISSING_SOURCE_REVIEW_DECISION)
        self.assertIn("reviewer_ack_review_decision_json_missing", missing["handoff_reasons"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_evidence_ref_mismatch_gets_dedicated_fail_closed_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._decision_summary("terminal-reviewer-handoff-006"),
                "terminal-reviewer-handoff-other",
            )

        self.assertNotEqual(exit_code, 0)
        self.assertEqual(artifact["handoff_status"], gate.EVIDENCE_REF_MISMATCH)
        self.assertIn("evidence_ref_mismatch", artifact["handoff_reasons"])
        self.assertFalse(summary["safe_to_control"])

    def test_unsafe_raw_fields_and_success_claims_reject_without_raw_copy(self) -> None:
        for key, value in (
            ("raw_material_body", "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 raw artifact"),
            ("safe_note", "delivery_success=true and PRRT_kwDOSWB9286CJ3tX resolved"),
            ("safe_to_control", True),
        ):
            with self.subTest(key=key):
                with tempfile.TemporaryDirectory() as tmp:
                    payload = self._decision_summary(f"terminal-reviewer-handoff-{abs(hash(key))}")
                    payload[key] = value
                    artifact, summary, exit_code = self._build(Path(tmp), payload, payload["safe_evidence_ref"])  # type: ignore[arg-type]

                encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
                self.assertNotEqual(exit_code, 0)
                self.assertEqual(artifact["handoff_status"], gate.REJECTED_UNSAFE)
                self.assertIn("delivery_success=false", encoded)
                self.assertNotIn("Bearer abc", encoded)
                self.assertNotIn("/cmd_vel", encoded)
                self.assertNotIn("/dev/ttyUSB0", encoded)
                self.assertFalse(summary["safe_copy"]["safe_to_control"])

    def test_robot_alias_wrapper_is_supported_and_pr5_stays_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {decision_gate.ROBOT_ALIAS: self._decision_summary("terminal-reviewer-handoff-007")}
            artifact, summary, exit_code = self._build(Path(tmp), payload, "terminal-reviewer-handoff-007")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["handoff_status"], gate.READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF)
        self.assertEqual(summary["pr5_thread"]["thread_id"], gate.PR5_THREAD_ID)
        self.assertEqual(summary["pr5_thread"]["state"], "unresolved")
        self.assertEqual(summary["pr5_thread"]["material_state"], "hardware_material_pending")

    def test_cli_and_output_surface_required_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = self._write_json(root, "reviewer_ack_review_decision.json", self._decision_summary("terminal-reviewer-handoff-008"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.py"),
                    "--reviewer-ack-review-decision-json",
                    str(input_path),
                    "--evidence-ref",
                    "terminal-reviewer-handoff-008",
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
        self.assertIn(gate.READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF, result.stdout)
        self.assertIn("source=software_proof", result.stdout)
        self.assertIn("not_proven", result.stdout)
        self.assertIn("delivery_success=false", result.stdout)
        self.assertIn("primary_actions_enabled=false", result.stdout)
        self.assertIn("safe_to_control=false", result.stdout)
        self.assertIn(gate.PR5_THREAD_ID, result.stdout)


if __name__ == "__main__":
    unittest.main()
