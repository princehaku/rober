#!/usr/bin/env python3
"""field evidence rerun acceptance review handoff gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_acceptance_review_handoff as handoff  # noqa: E402


# 测试约束 01：fixture 只表达 safe review-decision metadata。
# 测试约束 02：ready handoff 只证明可交接，不证明现场通过。
# 测试约束 03：checklist 是真实材料清单，不读取真实材料。
# 测试约束 04：缺 review decision、缺材料、mismatch、unsafe 都必须 fail closed。
# 测试约束 05：所有输出保持 source=software_proof 与 not_proven。
# 测试约束 06：所有输出保持 safe_to_control=false。
# 测试约束 07：所有输出保持 delivery_success=false。
# 测试约束 08：所有输出保持 primary_actions_enabled=false。
# 测试约束 09：单测不访问 ROS graph、硬件、外部云或手机 runtime。
# 测试约束 10：source boundary 必须是上一轮 review-decision gate。


class FieldEvidenceRerunExecutionResultAcceptanceReviewHandoffTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict | str) -> Path:
        # 测试只写临时 JSON，保证 gate 不依赖 ROS2、Nav2、硬件、手机或外部云。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def review_decision_summary(self, evidence_ref: str, ready: bool = True) -> dict:
        # 样本沿用上一轮 review-decision summary 的安全字段，不夹带 raw artifact。
        status = handoff.READY_SOURCE_DECISION if ready else "needs_more_material"
        accepted = list(handoff.review_decision.REQUIRED_MATERIALS) if ready else list(handoff.review_decision.REQUIRED_MATERIALS[:-1])
        missing = [] if ready else [handoff.review_decision.REQUIRED_MATERIALS[-1]]
        return {
            "schema": "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate",
            "status": status,
            "review_decision": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_status": {
                "status": "accepted" if ready else "missing",
                "accepted_materials": accepted,
                "missing_materials": missing,
                "rejected_materials": [],
                "accepted_count": len(accepted),
                "required_count": len(handoff.review_decision.REQUIRED_MATERIALS),
                "is_complete": ready,
            },
            "owner_handoff": {
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "next_required_evidence": ["safe owner handoff only"],
            },
            "safe_copy": {
                "source": "software_proof",
                "evidence_ref": evidence_ref,
                "safe_evidence_ref": evidence_ref,
                "status": status,
                "review_decision": status,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "material_status": {
                    "status": "accepted" if ready else "missing",
                    "accepted_materials": accepted,
                    "missing_materials": missing,
                    "rejected_materials": [],
                    "accepted_count": len(accepted),
                    "required_count": len(handoff.review_decision.REQUIRED_MATERIALS),
                    "is_complete": ready,
                },
            },
            "not_proven": list(handoff.NOT_PROVEN),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def build(self, root: Path, payload: dict | str, evidence_ref: str = "rerun-handoff-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 state、boundary 和 fail-closed 规则。
        source_path = self.write_json(root, "review_decision.json", payload)
        artifact, summary, exit_code = handoff.build_field_evidence_rerun_execution_result_acceptance_review_handoff(
            str(source_path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_review_decision_builds_handoff_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self.build(root, {"payload": {"summary": self.review_decision_summary("rerun-handoff-001")}})

        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_review_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_review_handoff_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate",
        )
        self.assertEqual(artifact["handoff_status"], "ready_for_field_owner_support_reviewer_handoff_not_proven")
        self.assertEqual(summary["handoff_status"], "ready_for_field_owner_support_reviewer_handoff_not_proven")
        self.assertIn("handoff_needs_more_material", artifact["allowed_handoff_states"])
        self.assertIn("handoff_evidence_ref_mismatch", artifact["allowed_handoff_states"])
        self.assertIn("handoff_unsafe_rejected", artifact["allowed_handoff_states"])
        self.assertIn("blocked_missing_review_decision", artifact["allowed_handoff_states"])
        self.assertEqual(len(artifact["handoff_checklist"]), len(handoff.HANDOFF_CHECKLIST))
        self.assertIn("true task record", json.dumps(artifact["handoff_checklist"], ensure_ascii=False))
        self.assertIn("source=software_proof", artifact["boundary_note"])
        self.assertIn("not_proven", json.dumps(summary["safe_copy"], ensure_ascii=False))
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_artifact_input_and_robot_safe_alias_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.review_decision_summary("rerun-handoff-002")
            source["schema"] = "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_review_decision.v1"
            artifact, summary = self.build(
                root,
                {"robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary": source},
                "rerun-handoff-002",
            )

        self.assertEqual(artifact["source_review_decision"]["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_review_decision.v1")
        self.assertEqual(summary["safe_copy"]["handoff_status"], handoff.READY_HANDOFF)
        self.assertEqual(summary["owner_handoff"]["evidence_ref"], "rerun-handoff-002")

    def test_missing_bad_json_unsupported_and_non_ready_review_decision_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_artifact, missing_summary, _ = handoff.build_field_evidence_rerun_execution_result_acceptance_review_handoff(
                str(root / "missing.json"),
                "rerun-handoff-003",
            )
            bad_artifact, _bad_summary = self.build(root, "{bad json", "rerun-handoff-003")
            unsupported = self.review_decision_summary("rerun-handoff-003")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _unsupported_summary = self.build(root, unsupported, "rerun-handoff-003")
            not_ready_artifact, not_ready_summary = self.build(root, self.review_decision_summary("rerun-handoff-003", ready=False), "rerun-handoff-003")

        self.assertEqual(missing_artifact["handoff_status"], "blocked_missing_review_decision")
        self.assertEqual(bad_artifact["handoff_status"], "blocked_missing_review_decision")
        self.assertEqual(unsupported_artifact["handoff_status"], "blocked_missing_review_decision")
        self.assertEqual(not_ready_artifact["handoff_status"], "handoff_needs_more_material")
        self.assertIn("diagnostics_mobile_safe_summary", not_ready_summary["material_status"]["missing_materials"])
        self.assertFalse(missing_artifact["safe_to_control"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_missing_and_rejected_materials_need_more_material(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = self.review_decision_summary("rerun-handoff-004")
            missing["material_status"]["missing_materials"] = ["delivery_result"]
            missing["material_status"]["accepted_count"] = len(handoff.review_decision.REQUIRED_MATERIALS) - 1
            missing["material_status"]["is_complete"] = False
            missing_artifact, missing_summary = self.build(root, missing, "rerun-handoff-004")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rejected = self.review_decision_summary("rerun-handoff-005")
            rejected["material_status"]["rejected_materials"] = ["true_phone_browser_evidence"]
            rejected["material_status"]["accepted_count"] = len(handoff.review_decision.REQUIRED_MATERIALS) - 1
            rejected["material_status"]["is_complete"] = False
            rejected_artifact, rejected_summary = self.build(root, rejected, "rerun-handoff-005")

        self.assertEqual(missing_artifact["handoff_status"], "handoff_needs_more_material")
        self.assertIn("repair missing material before handoff: delivery_result", "\n".join(missing_summary["next_required_evidence"]))
        self.assertEqual(rejected_artifact["handoff_status"], "handoff_needs_more_material")
        self.assertIn("repair rejected material before handoff: true_phone_browser_evidence", "\n".join(rejected_summary["next_required_evidence"]))

    def test_ref_mismatch_weak_same_ref_unsafe_and_control_claim_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch_artifact, _mismatch_summary = self.build(root, self.review_decision_summary("rerun-handoff-006"), "another-run")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weak = self.review_decision_summary("rerun-handoff-007")
            weak["same_evidence_ref_required"] = "true"
            weak_artifact, _weak_summary = self.build(root, weak, "rerun-handoff-007")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe = self.review_decision_summary("rerun-handoff-008")
            unsafe["owner_handoff"] = {"note": "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0"}
            unsafe_artifact, _unsafe_summary = self.build(root, unsafe, "rerun-handoff-008")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            control = self.review_decision_summary("rerun-handoff-009")
            control["safe_copy"]["safe_to_control"] = True
            control_artifact, control_summary = self.build(root, control, "rerun-handoff-009")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            forbidden_claim = self.review_decision_summary("rerun-handoff-010")
            forbidden_claim["owner_handoff"] = {"note": "external proof accepted and PR #5 resolved"}
            forbidden_artifact, _forbidden_summary = self.build(root, forbidden_claim, "rerun-handoff-010")

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(mismatch_artifact["handoff_status"], "handoff_evidence_ref_mismatch")
        self.assertEqual(weak_artifact["handoff_status"], "handoff_evidence_ref_mismatch")
        self.assertEqual(unsafe_artifact["handoff_status"], "handoff_unsafe_rejected")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertEqual(control_artifact["handoff_status"], "handoff_unsafe_rejected")
        self.assertEqual(forbidden_artifact["handoff_status"], "handoff_unsafe_rejected")
        self.assertFalse(control_artifact["safe_to_control"])
        self.assertFalse(control_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
