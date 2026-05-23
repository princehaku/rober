#!/usr/bin/env python3
"""reviewer ACK review-decision gate 的离线围栏测试。"""

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

import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake as intake  # noqa: E402
import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达 reviewer ACK intake safe summary。
# 测试约束 02：accepted 只表示进入 reviewer ACK 复核，不代表 reviewer resolution。
# 测试约束 03：needs_reassignment 只表达 owner 路由变化，不启用控制。
# 测试约束 04：field-owner supplement 只表达补材料，不代表补证完成。
# 测试约束 05：缺 intake/source 必须 blocked_missing_reviewer_ack_intake。
# 测试约束 06：unsafe success/control/hardware/PR-resolution copy 必须 rejected。
# 测试约束 07：Robot diagnostics safe alias 必须可消费。
# 测试约束 08：输出保持 source=software_proof 与 not_proven。
# 测试约束 09：输出保持 delivery_success=false。
# 测试约束 10：输出保持 primary_actions_enabled=false。
# 测试约束 11：输出保持 safe_to_control=false。
# 测试约束 12：测试不访问 ROS graph、Nav2、硬件、云、GitHub 或手机 runtime。


class FieldEvidenceRerunAcceptanceOwnerResponseReviewerAckReviewDecisionTest(unittest.TestCase):
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
        reassignment_target: str = "field-owner-b",
    ) -> dict[str, object]:
        # source 使用上一轮 reviewer ACK intake 的安全消费面。
        return {
            "schema": intake.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": intake.CAPABILITY,
            "reviewer_ack_state": ack_state,
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake": ack_state,
            "source_handoff_status": "reviewer_ack_intake_safe_not_proven",
            "evidence_boundary": intake.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "ack_reasons": ack_reasons or ["reviewer ACK received for later reviewer ACK review"],
            "next_required_evidence": ["keep reviewer ACK attached to the same safe evidence_ref"],
            "reviewer_acknowledgement": {
                "schema": "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_packet.v1",
                "source": "software_proof",
                "status": "not_proven",
                "reviewer_ack_state": ack_state,
                "ack_owner": "reviewer",
                "acknowledged_at": "2026-05-22T18:30:00Z",
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
            "not_proven_items": ["real_reviewer_resolution"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": (
                f"{intake.CAPABILITY}: reviewer_ack_state={ack_state}; evidence_ref={evidence_ref}; "
                "source=software_proof; not_proven; delivery_success=false; "
                "primary_actions_enabled=false; safe_to_control=false."
            ),
        }

    def _build(self, root: Path, payload: dict[str, object], evidence_ref: str) -> tuple[dict[str, object], dict[str, object], int]:
        # 公共 helper 让 case 聚焦五态映射和安全边界。
        input_path = self._write_json(root, "reviewer_ack_intake.json", payload)
        return gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision(
            str(input_path),
            evidence_ref,
        )

    def test_acknowledged_intake_maps_to_accepted_for_reviewer_ack_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._intake_summary("reviewer-ack-review-901"),
                "reviewer-ack-review-901",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], gate.SCHEMA)
        self.assertEqual(summary["schema"], gate.SUMMARY_SCHEMA)
        self.assertEqual(summary["summary_alias"], gate.ROBOT_ALIAS)
        self.assertEqual(artifact["review_decision"], gate.ACCEPTED)
        self.assertEqual(artifact["evidence_boundary"], gate.EVIDENCE_BOUNDARY)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])

    def test_needs_reassignment_is_supported_without_control_enablement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._intake_summary("reviewer-ack-review-902", intake.ACK_NEEDS_REASSIGNMENT),
                "reviewer-ack-review-902",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], gate.NEEDS_REASSIGNMENT)
        self.assertEqual(summary["reassignment_target"], "field-owner-b")
        self.assertIn("reassigned owner ACK", summary["next_required_evidence"][0]["materials"])
        self.assertFalse(summary["safe_to_control"])

    def test_field_owner_supplement_is_classified_before_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._intake_summary(
                    "reviewer-ack-review-903",
                    intake.ACK_ACKNOWLEDGED,
                    ["field_owner_supplement required for missing route/elevator material"],
                ),
                "reviewer-ack-review-903",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], gate.NEEDS_FIELD_OWNER_SUPPLEMENT)
        self.assertEqual(summary["next_required_evidence"][0]["owner"], "field-owner")
        self.assertFalse(summary["primary_actions_enabled"])

    def test_unsafe_ack_intake_and_overclaim_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            unsafe_payload = self._intake_summary("reviewer-ack-review-904")
            unsafe_payload["safe_note"] = "delivery_success=true and PRRT_kwDOSWB9286CJ3tX resolved"
            artifact, summary, exit_code = self._build(Path(tmp), unsafe_payload, "reviewer-ack-review-904")

        encoded = json.dumps(summary, ensure_ascii=False)
        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], gate.REJECTED_UNSAFE)
        self.assertIn("delivery_success=false", encoded)
        self.assertNotIn("delivery_success=true", encoded)
        self.assertFalse(summary["safe_copy"]["delivery_success"])

    def test_evidence_ref_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, exit_code = self._build(
                Path(tmp),
                self._intake_summary("reviewer-ack-review-905"),
                "reviewer-ack-review-other",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], gate.REJECTED_UNSAFE)
        self.assertIn("evidence_ref_mismatch", artifact["decision_reasons"])
        self.assertFalse(summary["safe_to_control"])

    def test_missing_or_bad_intake_maps_to_blocked_missing_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing, missing_summary, missing_exit = gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision(
                str(root / "missing-intake.json"),
                "reviewer-ack-review-906",
            )
            bad_path = self._write_json(root, "unsupported.json", {"schema": "unsupported", "source": "software_proof"})
            bad, _, bad_exit = gate.build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision(
                str(bad_path),
                "reviewer-ack-review-907",
            )

        self.assertEqual(missing_exit, 0)
        self.assertEqual(bad_exit, 0)
        self.assertEqual(missing["review_decision"], gate.BLOCKED_MISSING_INTAKE)
        self.assertEqual(bad["review_decision"], gate.BLOCKED_MISSING_INTAKE)
        self.assertIn("reviewer_ack_intake_json_missing", missing["decision_reasons"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_robot_alias_wrapper_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = {intake.ROBOT_ALIAS: self._intake_summary("reviewer-ack-review-908")}
            artifact, summary, exit_code = self._build(Path(tmp), payload, "reviewer-ack-review-908")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], gate.ACCEPTED)
        self.assertEqual(artifact["safe_evidence_ref"], "reviewer-ack-review-908")
        self.assertEqual(summary["previous_intake_reference"]["schema"], intake.SUMMARY_SCHEMA)

    def test_cli_prints_accepted_for_safe_ack_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = self._write_json(root, "reviewer_ack_intake.json", self._intake_summary("reviewer-ack-review-909"))
            result = subprocess.run(
                [
                    sys.executable,
                    str(EVIDENCE_DIR / "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision.py"),
                    "--reviewer-ack-intake-json",
                    str(input_path),
                    "--evidence-ref",
                    "reviewer-ack-review-909",
                ],
                check=False,
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn(gate.ACCEPTED, result.stdout)
        self.assertIn("software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_gate", result.stdout)

    def test_output_preserves_required_boundary_literals_and_no_raw_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary, _ = self._build(
                Path(tmp),
                self._intake_summary("reviewer-ack-review-910"),
                "reviewer-ack-review-910",
            )

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision", encoded)
        self.assertIn("software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_gate", encoded)
        self.assertIn(gate.ACCEPTED, encoded)
        self.assertIn(gate.NEEDS_REASSIGNMENT, encoded)
        self.assertIn(gate.NEEDS_FIELD_OWNER_SUPPLEMENT, encoded)
        self.assertIn(gate.REJECTED_UNSAFE, encoded)
        self.assertIn(gate.BLOCKED_MISSING_INTAKE, encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertNotIn("raw artifact", encoded)


if __name__ == "__main__":
    unittest.main()
