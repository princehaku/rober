#!/usr/bin/env python3
"""field evidence real material response review decision gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_real_material_response_intake as intake  # noqa: E402
import field_evidence_real_material_response_review_decision as decision  # noqa: E402


# 测试约束 01：fixture 只表达 response-intake safe summary。
# 测试约束 02：accepted decision 仅表示 later review，不表示现场通过。
# 测试约束 03：缺 response-intake source 时必须 blocked。
# 测试约束 04：missing material 映射 material backfill。
# 测试约束 05：rejected/mixed/unsafe 映射 rejected，不允许降级。
# 测试约束 06：blocked material 映射 real environment unavailable。
# 测试约束 07：Robot diagnostics safe alias 必须可消费。
# 测试约束 08：输出保持 source=software_proof、status=not_proven。
# 测试约束 09：输出保持 safe_to_control=false。
# 测试约束 10：输出保持 delivery_success=false。
# 测试约束 11：输出保持 primary_actions_enabled=false。
# 测试约束 12：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRealMaterialResponseReviewDecisionTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不模拟真实现场 runtime。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _intake_summary(
        self,
        evidence_ref: str,
        counts: dict[str, int] | None = None,
        status: str = decision.READY_INTAKE_STATUS,
        unsafe: bool = False,
    ) -> dict[str, object]:
        # 样本沿用上一轮 response-intake summary 的安全消费面。
        counts = counts or {"accepted": 9, "missing": 0, "rejected": 0, "blocked": 0}
        material_responses = []
        for index, name in enumerate(intake.REQUIRED_MATERIALS):
            if index < counts.get("accepted", 0):
                classification = "accepted"
            elif index < counts.get("accepted", 0) + counts.get("missing", 0):
                classification = "missing"
            elif index < counts.get("accepted", 0) + counts.get("missing", 0) + counts.get("rejected", 0):
                classification = "rejected"
            else:
                classification = "blocked"
            material_responses.append(
                {
                    "name": name,
                    "classification": classification,
                    "safe_evidence_ref": evidence_ref,
                    "ready_for_later_review_only": classification == "accepted",
                    "safe_summary": "sanitized category index",
                }
            )
        if unsafe:
            material_responses[0]["safe_summary"] = "unsafe raw /cmd_vel with token"
        return {
            "schema": "trashbot.field_evidence_real_material_response_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_real_material_response_intake_gate",
            "status": status,
            "response_intake_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "required_materials": list(intake.REQUIRED_MATERIALS),
            "material_classification_counts": counts,
            "material_responses": material_responses,
            "not_proven": ["not_proven"],
            "safe_copy": {
                "source": "software_proof",
                "status": status,
                "response_intake_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "material_classification_counts": counts,
                "material_responses": material_responses,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _build(self, root: Path, payload: dict[str, object], evidence_ref: str = "field-run-201") -> tuple[dict[str, object], dict[str, object]]:
        # 公共 helper 让 case 聚焦 decision 映射和 fail-closed 规则。
        path = self._write_json(root, "response_intake.json", payload)
        artifact, summary, exit_code = decision.build_field_evidence_real_material_response_review_decision(str(path), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_all_accepted_materials_map_to_later_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(
                root,
                {"payload": {"field_evidence_real_material_response_intake_summary": self._intake_summary("field-run-201")}},
            )

        self.assertEqual(artifact["schema"], "trashbot.field_evidence_real_material_response_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_real_material_response_review_decision_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_real_material_response_review_decision_gate",
        )
        self.assertEqual(artifact["status"], "not_proven")
        self.assertEqual(artifact["review_decision"], "accepted_for_later_review_not_proven")
        self.assertEqual(artifact["material_classification_counts"]["accepted"], 9)
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_copy"]["delivery_success"])
        self.assertIn("accepted_for_later_review_not_proven_only", json.dumps(artifact, ensure_ascii=False))

    def test_missing_materials_require_backfill_not_acceptance(self) -> None:
        counts = {"accepted": 7, "missing": 2, "rejected": 0, "blocked": 0}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._intake_summary("field-run-202", counts), "field-run-202")

        self.assertEqual(artifact["review_decision"], "needs_material_backfill_not_proven")
        self.assertEqual(summary["owner_handoff"]["owner"], "field-owner")
        self.assertEqual(len(summary["missing_materials"]), 2)
        self.assertIn("backfill_missing_real_material_categories", json.dumps(summary, ensure_ascii=False))

    def test_blocked_materials_map_to_real_environment_unavailable(self) -> None:
        counts = {"accepted": 5, "missing": 0, "rejected": 0, "blocked": 4}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(
                root,
                self._intake_summary("field-run-203", counts, status="blocked_field_owner_dependency_unavailable"),
                "field-run-203",
            )

        self.assertEqual(artifact["review_decision"], "blocked_real_environment_unavailable_not_proven")
        self.assertEqual(len(summary["blocked_materials"]), 4)
        self.assertIn("field_environment_or_dependency_unavailable", summary["decision_reasons"])

    def test_rejected_unsafe_mixed_and_success_claims_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rejected, _ = self._build(
                root,
                self._intake_summary("field-run-204", {"accepted": 8, "missing": 0, "rejected": 1, "blocked": 0}),
                "field-run-204",
            )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe, unsafe_summary = self._build(root, self._intake_summary("field-run-205", unsafe=True), "field-run-205")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mixed, _ = self._build(root, self._intake_summary("field-run-206"), "other-run")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            success_payload = self._intake_summary("field-run-207")
            success_payload["delivery_success"] = True
            success_claim, _ = self._build(root, success_payload, "field-run-207")

        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertEqual(rejected["review_decision"], "rejected_unsafe_or_mixed_response_not_proven")
        self.assertEqual(unsafe["review_decision"], "rejected_unsafe_or_mixed_response_not_proven")
        self.assertEqual(mixed["review_decision"], "rejected_unsafe_or_mixed_response_not_proven")
        self.assertEqual(success_claim["review_decision"], "rejected_unsafe_or_mixed_response_not_proven")
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("token", encoded.lower())
        self.assertFalse(success_claim["delivery_success"])

    def test_missing_bad_and_unsupported_source_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing, missing_summary, _ = decision.build_field_evidence_real_material_response_review_decision(
                str(root / "missing.json"),
                "field-run-208",
            )
            unsupported, _ = self._build(
                root,
                {"schema": "trashbot.unsupported.v1", "evidence_ref": "field-run-208"},
                "field-run-208",
            )

        self.assertEqual(missing["review_decision"], "blocked_missing_field_evidence_real_material_response_intake_not_proven")
        self.assertEqual(unsupported["review_decision"], "rejected_unsafe_or_mixed_response_not_proven")
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_robot_diagnostics_safe_alias_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alias = {
                "latest_status": {
                    "diagnostics": {
                        "robot_diagnostics_field_evidence_real_material_response_intake_summary": self._intake_summary("field-run-209")
                    }
                }
            }
            artifact, summary = self._build(root, alias, "field-run-209")

        self.assertEqual(artifact["review_decision"], "accepted_for_later_review_not_proven")
        self.assertEqual(summary["source_response_intake"]["schema_status"], "supported")
        self.assertTrue(summary["same_evidence_ref_required"])

    def test_output_preserves_required_boundary_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._intake_summary("field-run-210"), "field-run-210")

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("software_proof_docker_field_evidence_real_material_response_review_decision_gate", encoded)
        self.assertIn("accepted_for_later_review_not_proven", encoded)
        self.assertIn("needs_material_backfill_not_proven", encoded)
        self.assertIn("rejected_unsafe_or_mixed_response_not_proven", encoded)
        self.assertIn("blocked_real_environment_unavailable_not_proven", encoded)
        self.assertIn("same_evidence_ref_required", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Traceback", encoded)


if __name__ == "__main__":
    unittest.main()
