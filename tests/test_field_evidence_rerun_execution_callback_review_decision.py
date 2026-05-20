#!/usr/bin/env python3
"""field_evidence_rerun_execution_callback_review_decision 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试显式加入 evidence 目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_callback_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达 safe execution callback-intake summary。
# 测试约束 02：ready case 只证明 metadata review-decision 可复账。
# 测试约束 03：ready 不能被解释成真实 field rerun 或 delivery success。
# 测试约束 04：missing/rejected/blocked 必须进入 next_required_evidence。
# 测试约束 05：same evidence_ref mismatch 必须 fail closed。
# 测试约束 06：unsupported schema/boundary 必须 fail closed。
# 测试约束 07：坏 JSON、缺输入和非 ready source 不能变 ready。
# 测试约束 08：raw path、ROS topic、checksum 必须被阻断和脱敏。
# 测试约束 09：safe_to_control=true、delivery_success=true 必须被阻断。
# 测试约束 10：未知 category 或跨组重复 category 必须 unsupported。
# 测试约束 11：wrapper/nested artifact 和 Robot safe alias 必须可消费。
# 测试约束 12：所有输出保留 safe_to_control=false。
# 测试约束 13：所有输出保留 delivery_success=false。
# 测试约束 14：所有输出保留 primary_actions_enabled=false。
# 测试约束 15：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionCallbackReviewDecisionTest(unittest.TestCase):
    def _summary(self, evidence_ref: str = "ev-field-exec-review-001", **extra: object) -> dict[str, object]:
        # summary fixture 沿用 execution_callback_intake 的 safe summary contract。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_rerun_execution_callback_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_callback_intake_gate",
            "status": "ready_for_field_evidence_rerun_execution_callback_intake_not_proven",
            "callback_intake_status": "ready_for_field_evidence_rerun_execution_callback_intake_not_proven",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "accepted_materials": list(gate.REQUIRED_MATERIAL_CATEGORIES),
            "missing_materials": [],
            "rejected_materials": [],
            "blocked_materials": [],
            "material_counts": {"accepted": len(gate.REQUIRED_MATERIAL_CATEGORIES), "missing": 0, "rejected": 0, "blocked": 0},
            "not_proven": list(gate.NOT_PROVEN),
            "safe_copy": {
                "source": "software_proof",
                "status": "ready_for_field_evidence_rerun_execution_callback_intake_not_proven",
                "callback_intake_status": "ready_for_field_evidence_rerun_execution_callback_intake_not_proven",
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
            "schema": "trashbot.field_evidence_rerun_execution_callback_intake.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_callback_intake_gate",
            "field_evidence_rerun_execution_callback_intake_summary": summary,
            "robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary": summary,
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

    def test_ready_review_decision_keeps_software_proof_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary_path = self._write(root, "summary.json", self._summary())

            artifact, summary, exit_code = gate.build_field_evidence_rerun_execution_callback_review_decision(summary_path, "ev-field-exec-review-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_callback_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_callback_review_decision_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate")
        self.assertEqual(summary["review_decision"], "ready")
        self.assertEqual(summary["status"], "ready_for_field_evidence_rerun_execution_callback_review_decision_not_proven")
        self.assertIn("owner_handoff", summary)
        self.assertIn("next_required_evidence", summary)
        self.assertIn("rerun_guidance", summary)
        self.assertIn("blocker_summary", summary)
        self.assertEqual(summary["material_counts"]["accepted"], len(gate.REQUIRED_MATERIAL_CATEGORIES))
        self.assertIn("task_record", summary["accepted_materials"])
        self.assertIn("nav2_fixed_route_runtime_log", summary["accepted_materials"])
        self.assertIn("phone_browser_evidence", summary["accepted_materials"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_phone_browser_evidence", summary["not_proven"])
        self.assertIn("robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary", artifact)

    def test_missing_rejected_blocked_and_source_not_ready_map_to_decisions(self) -> None:
        missing_summary = self._summary(
            accepted_materials=["task_record"],
            missing_materials=["phone_browser_evidence"],
            rejected_materials=[],
            blocked_materials=[],
        )
        rejected_summary = self._summary(
            accepted_materials=["task_record"],
            missing_materials=[],
            rejected_materials=["route_completion_signal"],
            blocked_materials=[],
        )
        blocked_summary = self._summary(
            accepted_materials=["task_record"],
            missing_materials=[],
            rejected_materials=[],
            blocked_materials=["nav2_fixed_route_runtime_log"],
        )
        source_not_ready = self._summary(status="blocked_field_evidence_rerun_execution_callback_materials_not_ready")
        source_not_ready["callback_intake_status"] = "blocked_field_evidence_rerun_execution_callback_materials_not_ready"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_path = self._write(root, "missing.json", missing_summary)
            rejected_path = self._write(root, "rejected.json", rejected_summary)
            blocked_path = self._write(root, "blocked.json", blocked_summary)
            not_ready_path = self._write(root, "not_ready.json", source_not_ready)

            missing_artifact, missing_out, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(missing_path, "")
            rejected_artifact, rejected_out, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(rejected_path, "")
            blocked_artifact, blocked_out, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(blocked_path, "")
            not_ready_artifact, not_ready_out, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(not_ready_path, "")

        self.assertEqual(missing_artifact["review_decision"], "missing")
        self.assertEqual(rejected_artifact["review_decision"], "rejected")
        self.assertEqual(blocked_artifact["review_decision"], "blocked")
        self.assertEqual(not_ready_artifact["review_decision"], "source_not_ready")
        self.assertIn("phone_browser_evidence", missing_out["next_required_evidence"][0])
        self.assertIn("route_completion_signal", rejected_out["next_required_evidence"][0])
        self.assertIn("nav2_fixed_route_runtime_log", blocked_out["next_required_evidence"][0])
        self.assertIn("source_callback_intake_status", not_ready_out["decision_reasons"][0])

    def test_missing_bad_json_unsupported_and_mismatch_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good_path = self._write(root, "summary.json", self._summary())
            bad_json = root / "bad.json"
            bad_json.write_text("{", encoding="utf-8")
            wrong_schema = self._write(root, "wrong.json", self._summary(schema="trashbot.other.v1"))
            mismatch = self._write(root, "mismatch.json", self._summary("other-ref"))

            missing_artifact, _missing_summary, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(str(root / "missing.json"), "")
            bad_artifact, _bad_summary, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(str(bad_json), "")
            unsupported_artifact, _unsupported_summary, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(wrong_schema, "")
            mismatch_artifact, _mismatch_summary, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(mismatch, "ev-field-exec-review-001")
            good_artifact, _good_summary, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(good_path, "ev-field-exec-review-001")

        self.assertEqual(missing_artifact["review_decision"], "unsupported")
        self.assertEqual(bad_artifact["review_decision"], "unsupported")
        self.assertEqual(unsupported_artifact["review_decision"], "unsupported")
        self.assertEqual(mismatch_artifact["review_decision"], "evidence_ref_mismatch")
        self.assertEqual(good_artifact["review_decision"], "ready")

    def test_unsafe_copy_success_claim_unknown_and_duplicate_category_fail_closed(self) -> None:
        unsafe = self._summary()
        unsafe["owner_handoff"] = {"note": "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"}
        success = self._summary(delivery_success=True)
        unknown = self._summary(accepted_materials=["unknown_category"])
        duplicate = self._summary(accepted_materials=["task_record"], missing_materials=["task_record"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = self._write(root, "unsafe.json", unsafe)
            success_path = self._write(root, "success.json", success)
            unknown_path = self._write(root, "unknown.json", unknown)
            duplicate_path = self._write(root, "duplicate.json", duplicate)

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(unsafe_path, "")
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(success_path, "")
            unknown_artifact, unknown_summary, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(unknown_path, "")
            duplicate_artifact, duplicate_summary, _ = gate.build_field_evidence_rerun_execution_callback_review_decision(duplicate_path, "")

        self.assertEqual(unsafe_artifact["review_decision"], "unsafe")
        self.assertEqual(success_artifact["review_decision"], "unsafe")
        self.assertEqual(unknown_artifact["review_decision"], "unsupported")
        self.assertEqual(duplicate_artifact["review_decision"], "unsupported")
        self.assertIn("unsupported_material_category:unknown_category", unknown_summary["decision_reasons"])
        self.assertIn("material_category_in_multiple_groups:task_record", duplicate_summary["decision_reasons"])
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_nested_artifact_and_robot_alias_are_supported(self) -> None:
        summary = self._summary("ev-wrapper-exec-review-001")
        summary.pop("accepted_materials")
        summary.pop("missing_materials")
        summary.pop("rejected_materials")
        summary.pop("blocked_materials")
        summary["material_groups"] = {
            "accepted": list(gate.REQUIRED_MATERIAL_CATEGORIES),
            "missing": [],
            "rejected": [],
            "blocked": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = self._write(root, "wrapper.json", {"payload": {"artifact": self._artifact(summary)}})

            artifact, out_summary, _exit_code = gate.build_field_evidence_rerun_execution_callback_review_decision(wrapper_path, "")

        self.assertEqual(artifact["review_decision"], "ready")
        self.assertEqual(out_summary["safe_evidence_ref"], "ev-wrapper-exec-review-001")
        self.assertEqual(out_summary["material_counts"]["accepted"], len(gate.REQUIRED_MATERIAL_CATEGORIES))


if __name__ == "__main__":
    unittest.main()
