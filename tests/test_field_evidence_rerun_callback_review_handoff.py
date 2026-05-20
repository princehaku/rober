#!/usr/bin/env python3
"""field_evidence_rerun_callback_review_handoff 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_callback_review_handoff as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe review-decision summary，不创建真实材料目录。
# 测试约束 02：accepted case 只证明 metadata handoff 可复账。
# 测试约束 03：ready handoff 不能被解释成真实 field pass。
# 测试约束 04：missing/rejected 必须保留 owner follow-up。
# 测试约束 05：blocked review decision 必须要求上游复跑。
# 测试约束 06：same evidence_ref mismatch 必须 fail closed。
# 测试约束 07：unsupported schema/boundary 必须 fail closed。
# 测试约束 08：坏 JSON、缺输入、弱类型 same-ref 都不能 ready。
# 测试约束 09：raw path、ROS topic、checksum 必须被阻断和脱敏。
# 测试约束 10：safe_to_control=true、delivery_success=true 必须被阻断。
# 测试约束 11：wrapper/nested artifact/summary JSON 必须可消费。
# 测试约束 12：所有输出保留 safe_to_control=false。
# 测试约束 13：所有输出保留 delivery_success=false。
# 测试约束 14：所有输出保留 primary_actions_enabled=false。
# 测试约束 15：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunCallbackReviewHandoffTest(unittest.TestCase):
    def _summary(
        self,
        evidence_ref: str = "ev-field-handoff-001",
        review_decision: str = "accepted",
        **extra: object,
    ) -> dict[str, object]:
        # summary fixture 沿用 callback_review_decision 的 safe summary contract。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_callback_review_decision_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_callback_review_decision_gate",
            "status": review_decision,
            "review_decision": review_decision,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "owner_handoff": {
                "owner": "Autonomy Algorithm Engineer",
                "handoff_status": f"{review_decision}_field_evidence_rerun_callback_review_not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "next_required_evidence": [f"Keep evidence_ref={evidence_ref} in the same software_proof chain."],
            "rerun_guidance": {
                "review_decision": (
                    "python3 pc-tools/evidence/field_evidence_rerun_callback_review_decision.py "
                    f"--callback-intake-json <callback_intake.json> --evidence-ref {evidence_ref} --once-json"
                )
            },
            "blocker_summary": {
                "blocked": review_decision != "accepted",
                "decision": review_decision,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_copy": {
                "source": "software_proof",
                "review_decision": review_decision,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": list(gate.NOT_PROVEN),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _artifact(self, summary: dict[str, object]) -> dict[str, object]:
        # artifact fixture 携带 nested summary；handoff 应优先消费 summary。
        return {
            "schema": "trashbot.field_evidence_rerun_callback_review_decision.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_callback_review_decision_gate",
            "review_decision": summary["review_decision"],
            "safe_evidence_ref": summary["safe_evidence_ref"],
            "evidence_ref": summary["evidence_ref"],
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "field_evidence_rerun_callback_review_decision_summary": summary,
            "robot_diagnostics_summary": summary,
            "mobile_readonly_summary": summary,
            "not_proven": list(gate.NOT_PROVEN),
            "non_access_scope": ["serial_uart", "wave_rover", "ros_graph"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _write(self, root: Path, name: str, payload: object) -> str:
        # 临时文件只服务 JSON 输入输出围栏，不模拟真实材料路径。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_accepted_review_decision_maps_to_ready_handoff_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = self._write(root, "summary.json", self._summary())

            artifact, summary, exit_code = gate.build_field_evidence_rerun_callback_review_handoff(
                summary_path,
                "ev-field-handoff-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_callback_review_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_callback_review_handoff_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_callback_review_handoff_gate")
        self.assertEqual(summary["handoff_status"], "ready_for_field_evidence_rerun_callback_review_handoff")
        self.assertEqual(summary["source_review_decision"], "accepted")
        self.assertIn("owner_handoff", summary)
        self.assertIn("handoff_package", summary)
        self.assertIn("next_required_evidence", summary)
        self.assertIn("rerun_guidance", summary)
        self.assertIn("blocker_summary", summary)
        self.assertTrue(summary["handoff_package"]["ready"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_phone_browser_evidence", summary["not_proven"])

    def test_missing_rejected_and_blocked_decisions_map_to_handoff_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_path = self._write(root, "missing.json", self._summary(review_decision="missing"))
            rejected_path = self._write(root, "rejected.json", self._summary(review_decision="rejected"))
            blocked_path = self._write(root, "blocked.json", self._summary(review_decision="blocked"))

            missing_artifact, missing_summary, _ = gate.build_field_evidence_rerun_callback_review_handoff(missing_path, "")
            rejected_artifact, rejected_summary, _ = gate.build_field_evidence_rerun_callback_review_handoff(rejected_path, "")
            blocked_artifact, blocked_summary, _ = gate.build_field_evidence_rerun_callback_review_handoff(blocked_path, "")

        self.assertEqual(missing_artifact["handoff_status"], "needs_owner_follow_up")
        self.assertEqual(rejected_artifact["handoff_status"], "needs_owner_follow_up")
        self.assertEqual(blocked_artifact["handoff_status"], "needs_field_evidence_rerun_callback_rerun")
        self.assertEqual(missing_summary["owner_handoff"]["action"], "backfill_or_correct_field_evidence_review_materials")
        self.assertEqual(rejected_summary["owner_handoff"]["action"], "backfill_or_correct_field_evidence_review_materials")
        self.assertTrue(blocked_summary["rerun_guidance"]["required"])

    def test_bad_json_unsupported_mismatch_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_json = root / "bad.json"
            bad_json.write_text("{", encoding="utf-8")
            wrong_schema = self._write(root, "wrong.json", self._summary(schema="trashbot.other.v1"))
            mismatch = self._write(root, "mismatch.json", self._summary("other-ref"))
            weak_same_ref = self._write(root, "weak.json", self._summary(same_evidence_ref_required="true"))
            ready_path = self._write(root, "ready.json", self._summary())

            missing_artifact, _missing_summary, _ = gate.build_field_evidence_rerun_callback_review_handoff(str(root / "missing.json"), "")
            bad_artifact, _bad_summary, _ = gate.build_field_evidence_rerun_callback_review_handoff(str(bad_json), "")
            unsupported_artifact, _unsupported_summary, _ = gate.build_field_evidence_rerun_callback_review_handoff(wrong_schema, "")
            mismatch_artifact, _mismatch_summary, _ = gate.build_field_evidence_rerun_callback_review_handoff(mismatch, "ev-field-handoff-001")
            weak_artifact, _weak_summary, _ = gate.build_field_evidence_rerun_callback_review_handoff(weak_same_ref, "")
            ready_artifact, _ready_summary, _ = gate.build_field_evidence_rerun_callback_review_handoff(ready_path, "ev-field-handoff-001")

        self.assertEqual(missing_artifact["handoff_status"], "needs_field_evidence_rerun_callback_rerun")
        self.assertEqual(bad_artifact["handoff_status"], "needs_field_evidence_rerun_callback_rerun")
        self.assertEqual(unsupported_artifact["handoff_status"], "needs_field_evidence_rerun_callback_rerun")
        self.assertEqual(mismatch_artifact["handoff_status"], "evidence_ref_mismatch_rerun")
        self.assertEqual(weak_artifact["handoff_status"], "evidence_ref_mismatch_rerun")
        self.assertEqual(ready_artifact["handoff_status"], "ready_for_field_evidence_rerun_callback_review_handoff")

    def test_unsafe_copy_and_success_claim_fail_closed_without_leaking_raw_text(self) -> None:
        unsafe = self._summary()
        unsafe["next_required_evidence"] = ["raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"]
        success = self._summary(delivery_success=True)
        success["safe_copy"] = {
            "source": "software_proof",
            "review_decision": "accepted",
            "safe_evidence_ref": "ev-field-handoff-001",
            "not_proven": "not_proven",
            "safe_to_control": False,
            "delivery_success": True,
            "primary_actions_enabled": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = self._write(root, "unsafe.json", unsafe)
            success_path = self._write(root, "success.json", success)

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_callback_review_handoff(unsafe_path, "")
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_callback_review_handoff(success_path, "")

        self.assertEqual(unsafe_artifact["handoff_status"], "blocked_unsafe_review_handoff")
        self.assertEqual(success_artifact["handoff_status"], "blocked_unsafe_review_handoff")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_nested_artifact_and_non_access_scope_are_supported(self) -> None:
        summary = self._summary("ev-wrapper-handoff-001")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = self._write(root, "wrapper.json", {"payload": {"artifact": self._artifact(summary)}})

            artifact, out_summary, _exit_code = gate.build_field_evidence_rerun_callback_review_handoff(wrapper_path, "")

        self.assertEqual(artifact["handoff_status"], "ready_for_field_evidence_rerun_callback_review_handoff")
        self.assertEqual(out_summary["safe_evidence_ref"], "ev-wrapper-handoff-001")
        self.assertFalse(out_summary["safe_to_control"])
        self.assertFalse(out_summary["delivery_success"])
        self.assertFalse(out_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
