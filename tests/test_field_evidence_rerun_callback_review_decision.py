#!/usr/bin/env python3
"""field_evidence_rerun_callback_review_decision 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_callback_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe callback-intake summary，不创建真实材料目录。
# 测试约束 02：accepted case 只证明 metadata review 可复账。
# 测试约束 03：accepted 不能被解释成真实 field pass。
# 测试约束 04：missing/rejected/blocked 必须进入 next_required_evidence。
# 测试约束 05：same evidence_ref mismatch 必须 fail closed。
# 测试约束 06：unsupported schema/boundary 必须 fail closed。
# 测试约束 07：坏 JSON、缺输入、缺 nested summary 都不能 accepted。
# 测试约束 08：raw path、ROS topic、checksum 必须被阻断和脱敏。
# 测试约束 09：safe_to_control=true、delivery_success=true 必须被阻断。
# 测试约束 10：未知 material class 或重复 material group 必须 blocked。
# 测试约束 11：wrapper/nested JSON 必须可消费。
# 测试约束 12：所有输出保留 safe_to_control=false。
# 测试约束 13：所有输出保留 delivery_success=false。
# 测试约束 14：所有输出保留 primary_actions_enabled=false。
# 测试约束 15：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunCallbackReviewDecisionTest(unittest.TestCase):
    def _summary(self, evidence_ref: str = "ev-field-review-001", **extra: object) -> dict[str, object]:
        # summary fixture 沿用 callback_intake 的 safe summary contract。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_callback_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_callback_intake_gate",
            "status": "ready_for_field_evidence_rerun_callback_intake_not_proven",
            "callback_intake_status": "ready_for_field_evidence_rerun_callback_intake_not_proven",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "accepted_materials": list(gate.REQUIRED_MATERIAL_CLASSES),
            "missing_materials": [],
            "rejected_materials": [],
            "blocked_materials": [],
            "material_counts": {"accepted": len(gate.REQUIRED_MATERIAL_CLASSES), "missing": 0, "rejected": 0, "blocked": 0},
            "not_proven": list(gate.NOT_PROVEN),
            "safe_copy": {
                "source": "software_proof",
                "status": "ready_for_field_evidence_rerun_callback_intake_not_proven",
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
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
        # artifact fixture 必须携带 nested summary；缺 summary 会被 gate 阻断。
        return {
            "schema": "trashbot.field_evidence_rerun_callback_intake.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_callback_intake_gate",
            "field_evidence_rerun_callback_intake_summary": summary,
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

            artifact, summary, exit_code = gate.build_field_evidence_rerun_callback_review_decision(summary_path, "ev-field-review-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_callback_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_callback_review_decision_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_callback_review_decision_gate")
        self.assertEqual(summary["review_decision"], "accepted")
        self.assertIn("owner_handoff", summary)
        self.assertIn("next_required_evidence", summary)
        self.assertIn("rerun_guidance", summary)
        self.assertIn("blocker_summary", summary)
        self.assertEqual(summary["material_counts"]["accepted"], len(gate.REQUIRED_MATERIAL_CLASSES))
        self.assertIn("real route completion signal", summary["accepted_materials"])
        self.assertIn("real field task record", summary["accepted_materials"])
        self.assertIn("real Nav2/fixed-route runtime log", summary["accepted_materials"])
        self.assertIn("real phone/browser evidence", summary["accepted_materials"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_phone_browser_evidence", summary["not_proven"])

    def test_missing_rejected_and_blocked_groups_map_to_allowed_decisions(self) -> None:
        missing_summary = self._summary(
            accepted_materials=["real route completion signal"],
            missing_materials=["real phone/browser evidence"],
            rejected_materials=[],
            blocked_materials=[],
        )
        rejected_summary = self._summary(
            accepted_materials=["real route completion signal"],
            missing_materials=[],
            rejected_materials=["real field task record"],
            blocked_materials=[],
        )
        blocked_summary = self._summary(
            accepted_materials=["real route completion signal"],
            missing_materials=[],
            rejected_materials=[],
            blocked_materials=["real Nav2/fixed-route runtime log"],
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_path = self._write(root, "missing.json", missing_summary)
            rejected_path = self._write(root, "rejected.json", rejected_summary)
            blocked_path = self._write(root, "blocked.json", blocked_summary)

            missing_artifact, missing_out, _ = gate.build_field_evidence_rerun_callback_review_decision(missing_path, "")
            rejected_artifact, rejected_out, _ = gate.build_field_evidence_rerun_callback_review_decision(rejected_path, "")
            blocked_artifact, blocked_out, _ = gate.build_field_evidence_rerun_callback_review_decision(blocked_path, "")

        self.assertEqual(missing_artifact["review_decision"], "missing")
        self.assertEqual(rejected_artifact["review_decision"], "rejected")
        self.assertEqual(blocked_artifact["review_decision"], "blocked")
        self.assertIn("real phone/browser evidence", missing_out["next_required_evidence"][0])
        self.assertIn("real field task record", rejected_out["next_required_evidence"][0])
        self.assertIn("real Nav2/fixed-route runtime log", blocked_out["next_required_evidence"][0])

    def test_missing_bad_json_unsupported_mismatch_and_missing_summary_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good_path = self._write(root, "summary.json", self._summary())
            bad_json = root / "bad.json"
            bad_json.write_text("{", encoding="utf-8")
            wrong_schema = self._write(root, "wrong.json", self._summary(schema="trashbot.other.v1"))
            mismatch = self._write(root, "mismatch.json", self._summary("other-ref"))
            artifact_without_summary = self._write(root, "artifact.json", {"schema": "trashbot.field_evidence_rerun_callback_intake.v1"})

            missing_artifact, _missing_summary, _ = gate.build_field_evidence_rerun_callback_review_decision(str(root / "missing.json"), "")
            bad_artifact, _bad_summary, _ = gate.build_field_evidence_rerun_callback_review_decision(str(bad_json), "")
            unsupported_artifact, _unsupported_summary, _ = gate.build_field_evidence_rerun_callback_review_decision(wrong_schema, "")
            mismatch_artifact, _mismatch_summary, _ = gate.build_field_evidence_rerun_callback_review_decision(mismatch, "ev-field-review-001")
            no_summary_artifact, _no_summary, _ = gate.build_field_evidence_rerun_callback_review_decision(artifact_without_summary, "")
            good_artifact, _good_summary, _ = gate.build_field_evidence_rerun_callback_review_decision(good_path, "ev-field-review-001")

        self.assertEqual(missing_artifact["review_decision"], "blocked")
        self.assertEqual(bad_artifact["review_decision"], "blocked")
        self.assertEqual(unsupported_artifact["review_decision"], "blocked")
        self.assertEqual(mismatch_artifact["review_decision"], "blocked")
        self.assertEqual(no_summary_artifact["review_decision"], "blocked")
        self.assertEqual(good_artifact["review_decision"], "accepted")

    def test_unsafe_copy_success_claim_and_unknown_material_fail_closed(self) -> None:
        unsafe = self._summary()
        unsafe["owner_note"] = "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"
        success = self._summary(delivery_success=True)
        unknown = self._summary(accepted_materials=["unknown material"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = self._write(root, "unsafe.json", unsafe)
            success_path = self._write(root, "success.json", success)
            unknown_path = self._write(root, "unknown.json", unknown)

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_callback_review_decision(unsafe_path, "")
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_callback_review_decision(success_path, "")
            unknown_artifact, unknown_summary, _ = gate.build_field_evidence_rerun_callback_review_decision(unknown_path, "")

        self.assertEqual(unsafe_artifact["review_decision"], "blocked")
        self.assertEqual(success_artifact["review_decision"], "blocked")
        self.assertEqual(unknown_artifact["review_decision"], "blocked")
        self.assertIn("unsupported_material_class:unknown material", unknown_summary["status_reasons"])
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_nested_artifact_and_material_group_format_are_supported(self) -> None:
        summary = self._summary("ev-wrapper-review-001")
        summary.pop("accepted_materials")
        summary.pop("missing_materials")
        summary.pop("rejected_materials")
        summary.pop("blocked_materials")
        summary["material_groups"] = {
            "accepted": list(gate.REQUIRED_MATERIAL_CLASSES),
            "missing": [],
            "rejected": [],
            "blocked": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = self._write(root, "wrapper.json", {"payload": {"artifact": self._artifact(summary)}})

            artifact, out_summary, _exit_code = gate.build_field_evidence_rerun_callback_review_decision(wrapper_path, "")

        self.assertEqual(artifact["review_decision"], "accepted")
        self.assertEqual(out_summary["safe_evidence_ref"], "ev-wrapper-review-001")
        self.assertEqual(out_summary["material_counts"]["accepted"], len(gate.REQUIRED_MATERIAL_CLASSES))


if __name__ == "__main__":
    unittest.main()
