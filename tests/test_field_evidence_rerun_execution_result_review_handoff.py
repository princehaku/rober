#!/usr/bin/env python3
"""field_evidence_rerun_execution_result_review_handoff 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_review_handoff as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe review-decision summary。
# 测试约束 02：ready handoff 只证明 metadata handoff 可复账。
# 测试约束 03：ready handoff 不能被解释成真实 field rerun 或 delivery success。
# 测试约束 04：needs/rejected/blocked 必须进入对应 fail-closed handoff。
# 测试约束 05：same evidence_ref mismatch 必须 fail closed。
# 测试约束 06：unsupported schema/boundary 必须 fail closed。
# 测试约束 07：坏 JSON、缺输入和未知 review decision 不能变 ready。
# 测试约束 08：raw path、ROS topic、checksum 必须被阻断和脱敏。
# 测试约束 09：safe_to_control=true、delivery_success=true 必须被阻断。
# 测试约束 10：wrapper/nested artifact 和 Robot safe alias 必须可消费。
# 测试约束 11：所有输出保留 safe_to_control=false。
# 测试约束 12：所有输出保留 delivery_success=false。
# 测试约束 13：所有输出保留 primary_actions_enabled=false。
# 测试约束 14：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionResultReviewHandoffTest(unittest.TestCase):
    def _summary(
        self,
        evidence_ref: str = "ev-field-result-handoff-001",
        review_decision: str = "accepted_for_review",
        **extra: object,
    ) -> dict[str, object]:
        # summary fixture 沿用 execution_result_review_decision 的 safe summary contract。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_execution_result_review_decision_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate",
            "status": review_decision,
            "review_decision": review_decision,
            "result_review_decision": review_decision,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "decision_reasons": [f"fixture_review_decision_{review_decision}"],
            "owner_handoff": {"owner": "Autonomy Algorithm Engineer", "action": "fixture_safe_owner_handoff"},
            "next_required_evidence": ["fixture safe next evidence"],
            "reconciliation_hint": {"safe": True},
            "blocker_summary": {"status_reasons": ["fixture blocker summary"]},
            "not_proven": list(gate.NOT_PROVEN),
            "safe_copy": {
                "source": "software_proof",
                "status": review_decision,
                "review_decision": review_decision,
                "result_review_decision": review_decision,
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
            "schema": "trashbot.field_evidence_rerun_execution_result_review_decision.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate",
            "field_evidence_rerun_execution_result_review_decision_summary": summary,
            "robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary": summary,
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

    def test_accepted_review_decision_builds_owner_handoff_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = self._write(root, "summary.json", self._summary())

            artifact, summary, exit_code = gate.build_field_evidence_rerun_execution_result_review_handoff(
                summary_path,
                "ev-field-result-handoff-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_result_review_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_result_review_handoff_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate")
        self.assertEqual(summary["source_review_decision"], "accepted_for_review")
        self.assertEqual(summary["handoff_status"], "ready_for_field_evidence_rerun_execution_result_review_owner_handoff_not_proven")
        self.assertIn("owner_handoff", summary)
        self.assertIn("blocker_summary", summary)
        self.assertIn("next_required_real_materials", summary)
        self.assertIn("reconciliation_guidance", summary)
        self.assertIn("rerun_guidance", summary)
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_delivery_success", summary["not_proven"])
        self.assertIn("true_phone_browser_evidence", summary["next_required_real_materials"])

    def test_non_ready_review_decisions_map_to_fail_closed_handoffs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            needs_path = self._write(root, "needs.json", self._summary(review_decision="needs_material_backfill"))
            rejected_path = self._write(root, "rejected.json", self._summary(review_decision="rejected"))
            blocked_path = self._write(root, "blocked.json", self._summary(review_decision="blocked"))

            needs_artifact, needs_out, _ = gate.build_field_evidence_rerun_execution_result_review_handoff(needs_path, "")
            rejected_artifact, rejected_out, _ = gate.build_field_evidence_rerun_execution_result_review_handoff(rejected_path, "")
            blocked_artifact, blocked_out, _ = gate.build_field_evidence_rerun_execution_result_review_handoff(blocked_path, "")

        self.assertEqual(needs_artifact["handoff_status"], "needs_field_owner_material_backfill_for_execution_result_review_handoff_not_proven")
        self.assertEqual(rejected_artifact["handoff_status"], "rejected_field_evidence_rerun_execution_result_review_handoff_not_proven")
        self.assertEqual(blocked_artifact["handoff_status"], "blocked_field_evidence_rerun_execution_result_review_handoff_not_proven")
        self.assertIn("same_safe_evidence_ref_task_record", needs_out["next_required_real_materials"])
        self.assertIn("Correct rejected", rejected_out["next_required_evidence"][0])
        self.assertIn("Repair blocked", blocked_out["next_required_evidence"][0])

    def test_missing_bad_json_unsupported_mismatch_and_unknown_status_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_json = root / "bad.json"
            bad_json.write_text("{", encoding="utf-8")
            wrong_schema = self._write(root, "wrong.json", self._summary(schema="trashbot.other.v1"))
            mismatch = self._write(root, "mismatch.json", self._summary("other-ref"))
            unknown_status = self._write(root, "unknown.json", self._summary(review_decision="ready"))

            missing_artifact, _missing_summary, _ = gate.build_field_evidence_rerun_execution_result_review_handoff(str(root / "missing.json"), "")
            bad_artifact, _bad_summary, _ = gate.build_field_evidence_rerun_execution_result_review_handoff(str(bad_json), "")
            unsupported_artifact, _unsupported_summary, _ = gate.build_field_evidence_rerun_execution_result_review_handoff(wrong_schema, "")
            mismatch_artifact, _mismatch_summary, _ = gate.build_field_evidence_rerun_execution_result_review_handoff(mismatch, "ev-field-result-handoff-001")
            unknown_artifact, unknown_summary, _ = gate.build_field_evidence_rerun_execution_result_review_handoff(unknown_status, "")

        self.assertEqual(missing_artifact["handoff_status"], "blocked_unsupported_field_evidence_rerun_execution_result_review_decision")
        self.assertEqual(bad_artifact["handoff_status"], "blocked_unsupported_field_evidence_rerun_execution_result_review_decision")
        self.assertEqual(unsupported_artifact["handoff_status"], "blocked_unsupported_field_evidence_rerun_execution_result_review_decision")
        self.assertEqual(mismatch_artifact["handoff_status"], "evidence_ref_mismatch_field_evidence_rerun_execution_result_review_handoff")
        self.assertEqual(unknown_artifact["handoff_status"], "blocked_unsupported_field_evidence_rerun_execution_result_review_decision")
        self.assertIn("unsupported_review_decision:ready", unknown_summary["status_reasons"])

    def test_unsafe_copy_and_success_claim_fail_closed_and_redact(self) -> None:
        unsafe = self._summary()
        unsafe["owner_handoff"] = {"note": "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"}
        success = self._summary(delivery_success=True)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = self._write(root, "unsafe.json", unsafe)
            success_path = self._write(root, "success.json", success)

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_execution_result_review_handoff(unsafe_path, "")
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_execution_result_review_handoff(success_path, "")

        self.assertEqual(unsafe_artifact["handoff_status"], "blocked_unsafe_field_evidence_rerun_execution_result_review_handoff")
        self.assertEqual(success_artifact["handoff_status"], "blocked_unsafe_field_evidence_rerun_execution_result_review_handoff")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_nested_artifact_and_robot_alias_are_supported(self) -> None:
        summary = self._summary("ev-wrapper-result-handoff-001")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = self._write(root, "wrapper.json", {"payload": {"artifact": self._artifact(summary)}})

            artifact, out_summary, _exit_code = gate.build_field_evidence_rerun_execution_result_review_handoff(wrapper_path, "")

        self.assertEqual(artifact["handoff_status"], "ready_for_field_evidence_rerun_execution_result_review_owner_handoff_not_proven")
        self.assertEqual(out_summary["safe_evidence_ref"], "ev-wrapper-result-handoff-001")
        self.assertEqual(out_summary["source_review_decision"], "accepted_for_review")


if __name__ == "__main__":
    unittest.main()
