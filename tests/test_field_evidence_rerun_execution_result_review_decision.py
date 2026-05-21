#!/usr/bin/env python3
"""field_evidence_rerun_execution_result_review_decision 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe execution result-intake summary。
# 测试约束 02：accepted_for_review 只证明 metadata review decision 可复账。
# 测试约束 03：accepted_for_review 不能被解释成真实 field rerun 或 delivery success。
# 测试约束 04：missing/rejected/blocked 必须进入对应 fail-closed decision。
# 测试约束 05：same evidence_ref mismatch 必须 fail closed。
# 测试约束 06：unsupported schema/boundary 必须 fail closed。
# 测试约束 07：坏 JSON、缺输入和未知 source status 不能变 accepted_for_review。
# 测试约束 08：raw path、ROS topic、checksum 必须被阻断和脱敏。
# 测试约束 09：safe_to_control=true、delivery_success=true 必须被阻断。
# 测试约束 10：wrapper/nested artifact 和 Robot safe alias 必须可消费。
# 测试约束 11：所有输出保留 safe_to_control=false。
# 测试约束 12：所有输出保留 delivery_success=false。
# 测试约束 13：所有输出保留 primary_actions_enabled=false。
# 测试约束 14：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionResultReviewDecisionTest(unittest.TestCase):
    def _summary(
        self,
        evidence_ref: str = "ev-field-result-review-001",
        result_intake_status: str = "accepted",
        **extra: object,
    ) -> dict[str, object]:
        # summary fixture 沿用 execution_result_intake 的 safe summary contract。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_execution_result_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_result_intake_gate",
            "status": result_intake_status,
            "result_intake_status": result_intake_status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "status_reasons": [f"fixture_result_intake_{result_intake_status}"],
            "material_summary": {"sanitized": True},
            "owner_handoff": {"owner": "Autonomy Algorithm Engineer", "action": "fixture_safe_owner_review"},
            "next_required_evidence": ["fixture safe next evidence"],
            "not_proven": list(gate.NOT_PROVEN),
            "safe_copy": {
                "source": "software_proof",
                "status": result_intake_status,
                "result_intake_status": result_intake_status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_status": "matched",
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _artifact(self, summary: dict[str, object]) -> dict[str, object]:
        # artifact fixture 携带 nested summary 和 Robot alias，验证 wrapper 解析。
        return {
            "schema": "trashbot.field_evidence_rerun_execution_result_intake.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_result_intake_gate",
            "field_evidence_rerun_execution_result_intake_summary": summary,
            "robot_diagnostics_field_evidence_rerun_execution_result_intake_summary": summary,
            "not_proven": list(gate.NOT_PROVEN),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _write(self, root: Path, name: str, payload: object) -> str:
        # 临时文件只服务 JSON 输入输出围栏，不模拟真实材料路径。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_accepted_review_decision_keeps_software_proof_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = self._write(root, "summary.json", self._summary())

            artifact, summary, exit_code = gate.build_field_evidence_rerun_execution_result_review_decision(
                summary_path,
                "ev-field-result-review-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_result_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_result_review_decision_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate")
        self.assertEqual(summary["review_decision"], "accepted_for_review")
        self.assertEqual(summary["source_result_intake_status"], "accepted")
        self.assertIn("owner_handoff", summary)
        self.assertIn("next_required_evidence", summary)
        self.assertIn("reconciliation_hint", summary)
        self.assertIn("blocker_summary", summary)
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_delivery_success", summary["not_proven"])
        self.assertIn("robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary", artifact)

    def test_missing_rejected_and_blocked_map_to_fail_closed_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_path = self._write(root, "missing.json", self._summary(result_intake_status="missing"))
            rejected_path = self._write(root, "rejected.json", self._summary(result_intake_status="rejected"))
            blocked_path = self._write(root, "blocked.json", self._summary(result_intake_status="blocked"))

            missing_artifact, missing_out, _ = gate.build_field_evidence_rerun_execution_result_review_decision(missing_path, "")
            rejected_artifact, rejected_out, _ = gate.build_field_evidence_rerun_execution_result_review_decision(rejected_path, "")
            blocked_artifact, blocked_out, _ = gate.build_field_evidence_rerun_execution_result_review_decision(blocked_path, "")

        self.assertEqual(missing_artifact["review_decision"], "needs_material_backfill")
        self.assertEqual(rejected_artifact["review_decision"], "rejected")
        self.assertEqual(blocked_artifact["review_decision"], "blocked")
        self.assertIn("Backfill", missing_out["next_required_evidence"][0])
        self.assertIn("Correct rejected", rejected_out["next_required_evidence"][0])
        self.assertIn("Regenerate supported", blocked_out["next_required_evidence"][0])

    def test_missing_bad_json_unsupported_mismatch_and_unknown_status_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_json = root / "bad.json"
            bad_json.write_text("{", encoding="utf-8")
            wrong_schema = self._write(root, "wrong.json", self._summary(schema="trashbot.other.v1"))
            mismatch = self._write(root, "mismatch.json", self._summary("other-ref"))
            unknown_status = self._write(root, "unknown.json", self._summary(result_intake_status="ready"))

            missing_artifact, _missing_summary, _ = gate.build_field_evidence_rerun_execution_result_review_decision(str(root / "missing.json"), "")
            bad_artifact, _bad_summary, _ = gate.build_field_evidence_rerun_execution_result_review_decision(str(bad_json), "")
            unsupported_artifact, _unsupported_summary, _ = gate.build_field_evidence_rerun_execution_result_review_decision(wrong_schema, "")
            mismatch_artifact, _mismatch_summary, _ = gate.build_field_evidence_rerun_execution_result_review_decision(mismatch, "ev-field-result-review-001")
            unknown_artifact, unknown_summary, _ = gate.build_field_evidence_rerun_execution_result_review_decision(unknown_status, "")

        self.assertEqual(missing_artifact["review_decision"], "blocked")
        self.assertEqual(bad_artifact["review_decision"], "blocked")
        self.assertEqual(unsupported_artifact["review_decision"], "blocked")
        self.assertEqual(mismatch_artifact["review_decision"], "blocked")
        self.assertEqual(unknown_artifact["review_decision"], "blocked")
        self.assertIn("unsupported_result_intake_status:ready", unknown_summary["decision_reasons"])

    def test_unsafe_copy_and_success_claim_fail_closed_and_redact(self) -> None:
        unsafe = self._summary()
        unsafe["owner_handoff"] = {"note": "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"}
        success = self._summary(delivery_success=True)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = self._write(root, "unsafe.json", unsafe)
            success_path = self._write(root, "success.json", success)

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_execution_result_review_decision(unsafe_path, "")
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_execution_result_review_decision(success_path, "")

        self.assertEqual(unsafe_artifact["review_decision"], "blocked")
        self.assertEqual(success_artifact["review_decision"], "blocked")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_nested_artifact_and_robot_alias_are_supported(self) -> None:
        summary = self._summary("ev-wrapper-result-review-001")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = self._write(root, "wrapper.json", {"payload": {"artifact": self._artifact(summary)}})

            artifact, out_summary, _exit_code = gate.build_field_evidence_rerun_execution_result_review_decision(wrapper_path, "")

        self.assertEqual(artifact["review_decision"], "accepted_for_review")
        self.assertEqual(out_summary["safe_evidence_ref"], "ev-wrapper-result-review-001")
        self.assertEqual(out_summary["source_result_intake_status"], "accepted")


if __name__ == "__main__":
    unittest.main()
