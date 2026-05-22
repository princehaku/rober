#!/usr/bin/env python3
"""field evidence rerun acceptance backfill review decision gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_acceptance_backfill_review_decision as decision  # noqa: E402


# 测试约束 01：fixture 只表达 safe acceptance backfill metadata。
# 测试约束 02：ready decision 只证明可进入 review handoff，不证明现场通过。
# 测试约束 03：八类材料必须全部同一 evidence_ref 才能 ready。
# 测试约束 04：task/Nav2/route/elevator/dropoff/phone/browser 都只是材料类别。
# 测试约束 05：缺 backfill、缺材料、mismatch、unsafe 都必须 fail closed。
# 测试约束 06：所有输出保持 source=software_proof 与 not_proven。
# 测试约束 07：所有输出保持 safe_to_control=false。
# 测试约束 08：所有输出保持 delivery_success=false。
# 测试约束 09：所有输出保持 primary_actions_enabled=false。
# 测试约束 10：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionResultAcceptanceBackfillReviewDecisionTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def backfill_summary(self, evidence_ref: str, ready: bool = True) -> dict:
        # 样本沿用上一轮 acceptance backfill summary 的安全字段，不夹带 raw artifact。
        status = decision.READY_BACKFILL_STATUS if ready else "blocked_missing_materials"
        accepted = list(decision.REQUIRED_MATERIALS) if ready else list(decision.REQUIRED_MATERIALS[:-1])
        missing = [] if ready else [decision.REQUIRED_MATERIALS[-1]]
        return {
            "schema": "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate",
            "status": status,
            "backfill_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "required_materials": list(decision.REQUIRED_MATERIALS),
            "material_completeness": {
                "required_count": len(decision.REQUIRED_MATERIALS),
                "accepted_count": len(accepted),
                "accepted_materials": accepted,
                "missing_materials": missing,
                "rejected_materials": [],
                "is_complete": ready,
            },
            "acceptance_backfill_gap_summary": {
                "missing_materials": missing,
                "rejected_materials": {},
                "gap_count": len(missing),
            },
            "same_evidence_ref_alignment": {
                "status": "aligned" if ready else "blocked",
                "mismatched_materials": [],
                "missing_evidence_ref_materials": [],
            },
            "safe_lineage": {"source_acceptance_packet_status": "ready_for_field_owner_acceptance_review_not_proven"},
            "safe_copy": {
                "source": "software_proof",
                "evidence_ref": evidence_ref,
                "safe_evidence_ref": evidence_ref,
                "backfill_status": status,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "material_completeness": {
                    "required_count": len(decision.REQUIRED_MATERIALS),
                    "accepted_count": len(accepted),
                    "accepted_materials": accepted,
                    "missing_materials": missing,
                    "rejected_materials": [],
                    "is_complete": ready,
                },
            },
            "not_proven": list(decision.NOT_PROVEN),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(self, root: Path, payload: dict | str, evidence_ref: str = "rerun-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        source_path = self.write_json(root, "backfill.json", payload)
        artifact, summary, exit_code = decision.build_field_evidence_rerun_execution_result_acceptance_backfill_review_decision(
            str(source_path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_summary_builds_review_decision_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self.build(root, {"payload": {"summary": self.backfill_summary("rerun-001")}})

        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate",
        )
        self.assertEqual(artifact["review_decision"], "ready_for_field_rerun_result_acceptance_review_handoff")
        self.assertEqual(summary["review_decision"], "ready_for_field_rerun_result_acceptance_review_handoff")
        self.assertIn("needs_more_material", artifact["allowed_review_decisions"])
        self.assertIn("evidence_ref_mismatch", artifact["allowed_review_decisions"])
        self.assertIn("unsafe_rejected", artifact["allowed_review_decisions"])
        self.assertIn("blocked_missing_backfill", artifact["allowed_review_decisions"])
        self.assertEqual(artifact["source_acceptance_backfill"]["schema_status"], "supported")
        self.assertEqual(artifact["material_status"]["accepted_count"], len(decision.REQUIRED_MATERIALS))
        self.assertIn("field_evidence_rerun_execution_result_acceptance_backfill_review_decision.py", " ".join(summary["rerun_commands"]))
        self.assertIn("source=software_proof", artifact["boundary_note"])
        self.assertIn("not_proven", json.dumps(summary["safe_copy"], ensure_ascii=False))
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_artifact_input_and_nested_safe_copy_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.backfill_summary("rerun-002")
            source["schema"] = "trashbot.field_evidence_rerun_execution_result_acceptance_backfill.v1"
            artifact, summary = self.build(root, {"data": {"acceptance_backfill": source}}, "rerun-002")

        self.assertEqual(artifact["source_acceptance_backfill"]["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_backfill.v1")
        self.assertEqual(summary["safe_copy"]["review_decision"], decision.READY_DECISION)
        self.assertEqual(summary["owner_handoff"]["evidence_ref"], "rerun-002")

    def test_missing_bad_json_unsupported_and_backfill_not_ready_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_artifact, missing_summary, _ = decision.build_field_evidence_rerun_execution_result_acceptance_backfill_review_decision(
                str(root / "missing.json"),
                "rerun-003",
            )
            bad_artifact, _bad_summary = self.build(root, "{bad json", "rerun-003")
            unsupported = self.backfill_summary("rerun-003")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _unsupported_summary = self.build(root, unsupported, "rerun-003")
            not_ready_artifact, not_ready_summary = self.build(root, self.backfill_summary("rerun-003", ready=False), "rerun-003")

        self.assertEqual(missing_artifact["review_decision"], "blocked_missing_backfill")
        self.assertEqual(bad_artifact["review_decision"], "blocked_missing_backfill")
        self.assertEqual(unsupported_artifact["review_decision"], "blocked_missing_backfill")
        self.assertEqual(not_ready_artifact["review_decision"], "needs_more_material")
        self.assertIn("diagnostics_mobile_safe_summary", not_ready_summary["material_status"]["missing_materials"])
        self.assertFalse(missing_artifact["safe_to_control"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_missing_and_rejected_materials_need_more_material(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = self.backfill_summary("rerun-004", ready=False)
            missing["same_evidence_ref_alignment"]["status"] = "aligned"
            missing_artifact, missing_summary = self.build(root, missing, "rerun-004")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rejected = self.backfill_summary("rerun-005")
            rejected["material_completeness"]["accepted_count"] = len(decision.REQUIRED_MATERIALS) - 1
            rejected["material_completeness"]["accepted_materials"] = list(decision.REQUIRED_MATERIALS[:-1])
            rejected["material_completeness"]["rejected_materials"] = ["delivery_result"]
            rejected["material_completeness"]["is_complete"] = False
            rejected["acceptance_backfill_gap_summary"]["rejected_materials"] = {"delivery_result": ["placeholder_only"]}
            rejected["acceptance_backfill_gap_summary"]["gap_count"] = 1
            rejected_artifact, rejected_summary = self.build(root, rejected, "rerun-005")

        self.assertEqual(missing_artifact["review_decision"], "needs_more_material")
        self.assertIn("provide missing material: diagnostics_mobile_safe_summary", "\n".join(missing_summary["next_required_evidence"]))
        self.assertEqual(rejected_artifact["review_decision"], "needs_more_material")
        self.assertIn("repair rejected material: delivery_result", "\n".join(rejected_summary["next_required_evidence"]))

    def test_ref_mismatch_weak_same_ref_unsafe_and_control_claim_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch_artifact, _mismatch_summary = self.build(root, self.backfill_summary("rerun-006"), "another-run")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weak = self.backfill_summary("rerun-007")
            weak["same_evidence_ref_required"] = "true"
            weak_artifact, _weak_summary = self.build(root, weak, "rerun-007")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe = self.backfill_summary("rerun-008")
            unsafe["owner_handoff"] = {"note": "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0"}
            unsafe_artifact, _unsafe_summary = self.build(root, unsafe, "rerun-008")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = self.backfill_summary("rerun-009")
            control["safe_copy"]["safe_to_control"] = True
            control_artifact, control_summary = self.build(root, control, "rerun-009")

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(mismatch_artifact["review_decision"], "evidence_ref_mismatch")
        self.assertEqual(weak_artifact["review_decision"], "evidence_ref_mismatch")
        self.assertEqual(unsafe_artifact["review_decision"], "unsafe_rejected")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertEqual(control_artifact["review_decision"], "unsafe_rejected")
        self.assertFalse(control_artifact["safe_to_control"])
        self.assertFalse(control_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
