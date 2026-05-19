#!/usr/bin/env python3
"""elevator_field_evidence_trace_material_backfill_review_decision 的离线围栏测试。"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；验收入口显式加入 evidence 目录。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import elevator_field_evidence_trace_material_backfill_review_decision as decision  # noqa: E402


class ElevatorFieldEvidenceTraceMaterialBackfillReviewDecisionTest(unittest.TestCase):
    def _materials(self) -> list[str]:
        # fixture 只使用材料类别名，不读取真实现场材料目录。
        return list(decision.REQUIRED_ROUTE_ELEVATOR_MATERIALS)

    def _accepted(self, evidence_ref: str = "ev-elevator-material-review-001") -> list[dict[str, object]]:
        # accepted refs 是安全 token，不包含 raw path 或完整材料正文。
        return [
            {"material": material, "safe_ref": f"{evidence_ref}:{material}:redacted_ref", "required": True}
            for material in self._materials()
        ]

    def _intake_summary(
        self,
        evidence_ref: str = "ev-elevator-material-review-001",
        intake_status: str = "ready_for_material_review_not_proven",
        accepted: list[dict[str, object]] | None = None,
        missing: list[dict[str, object]] | None = None,
        rejected: list[dict[str, object]] | None = None,
        **extra: object,
    ) -> dict[str, object]:
        # summary 模拟上一轮 intake 的 safe/redacted 输出。
        payload: dict[str, object] = {
            "schema": "trashbot.elevator_field_evidence_trace_material_backfill_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "overall_status": "not_proven",
            "status": intake_status,
            "intake_status": intake_status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": {"status": "matched"},
            "required_route_elevator_materials": self._materials(),
            "accepted_material_refs": self._accepted(evidence_ref) if accepted is None else accepted,
            "missing_required_materials": [] if missing is None else missing,
            "rejected_material_refs": [] if rejected is None else rejected,
            "evidence_boundary": "software_proof_docker_elevator_field_evidence_trace_material_backfill_intake_gate",
            "not_proven": ["real_route_elevator_field_pass", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _write_json(self, root: Path, name: str, payload: dict[str, object] | str) -> Path:
        # 所有输入写入临时目录，避免依赖 repo 里的真实材料。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _build(
        self,
        root: Path,
        intake_payload: dict[str, object] | str,
        ref: str = "ev-elevator-material-review-001",
    ) -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 review decision，而不是路径拼接。
        intake_path = self._write_json(root, "intake.json", intake_payload)
        artifact, summary, exit_code = decision.build_elevator_field_evidence_trace_material_backfill_review_decision(
            str(intake_path),
            ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_full_safe_intake_is_ready_for_field_evidence_material_review_handoff_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary = self._build(Path(tmp), self._intake_summary())

        self.assertEqual(artifact["schema"], "trashbot.elevator_field_evidence_trace_material_backfill_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.elevator_field_evidence_trace_material_backfill_review_decision_summary.v1")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["review_decision"], "ready_for_field_evidence_material_review_handoff_not_proven")
        self.assertEqual(summary["source_intake"]["intake_status"], "ready_for_material_review_not_proven")
        self.assertEqual(summary["material_review_state"]["accepted_count"], len(self._materials()))
        self.assertIn("real_elevator_door_state", json.dumps(summary["accepted_material_refs"], ensure_ascii=False))
        self.assertIn("real_delivery_result", json.dumps(summary["accepted_material_refs"], ensure_ascii=False))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_required_materials_need_backfill(self) -> None:
        partial = self._accepted()[:2]
        missing = [{"material": material, "reason": "operator_packet_ref_missing"} for material in self._materials()[2:]]
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary = self._build(
                Path(tmp),
                self._intake_summary(
                    intake_status="needs_required_material_backfill_not_proven",
                    accepted=partial,
                    missing=missing,
                ),
            )

        self.assertEqual(artifact["review_decision"], "needs_required_material_backfill_not_proven")
        encoded_missing = json.dumps(summary["missing_required_materials"], ensure_ascii=False)
        self.assertIn("real_human_assistance_record", encoded_missing)
        self.assertIn("real_delivery_result", encoded_missing)
        self.assertIn("backfill_or_repair_required_material_refs", summary["next_required_evidence"][0])

    def test_nested_env_robot_diagnostics_alias_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapped_path = self._write_json(
                root,
                "wrapped_intake.json",
                {
                    "payload": {
                        "robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary": self._intake_summary(
                            "ev-elevator-material-review-002"
                        )
                    }
                },
            )
            os.environ["ROBER_ELEVATOR_FIELD_MATERIAL_BACKFILL_INTAKE_JSON"] = f"file:{wrapped_path}"
            try:
                artifact, summary, exit_code = decision.build_elevator_field_evidence_trace_material_backfill_review_decision(
                    "env:ROBER_ELEVATOR_FIELD_MATERIAL_BACKFILL_INTAKE_JSON",
                    "ev-elevator-material-review-002",
                )
            finally:
                os.environ.pop("ROBER_ELEVATOR_FIELD_MATERIAL_BACKFILL_INTAKE_JSON", None)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], "ready_for_field_evidence_material_review_handoff_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-elevator-material-review-002")
        self.assertEqual(summary["source_intake"]["source_style"], "env_source")

    def test_missing_bad_json_and_unsupported_intake_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_json = self._write_json(root, "bad.json", "{bad-json")
            missing_artifact, missing_summary, _ = decision.build_elevator_field_evidence_trace_material_backfill_review_decision(
                str(root / "missing.json"),
                "ev-elevator-material-review-001",
            )
            bad_artifact, _bad_summary, _ = decision.build_elevator_field_evidence_trace_material_backfill_review_decision(
                str(bad_json),
                "ev-elevator-material-review-001",
            )
            unsupported_artifact, _unsupported_summary = self._build(
                root,
                self._intake_summary(schema="trashbot.unsupported.v1"),
            )

        self.assertEqual(missing_artifact["review_decision"], "blocked_missing_material_backfill_intake_not_proven")
        self.assertEqual(missing_summary["review_decision"], "blocked_missing_material_backfill_intake_not_proven")
        self.assertEqual(bad_artifact["review_decision"], "blocked_missing_material_backfill_intake_not_proven")
        self.assertEqual(unsupported_artifact["review_decision"], "blocked_unsupported_material_backfill_intake_not_proven")

    def test_evidence_ref_mismatch_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch_artifact, mismatch_summary = self._build(root, self._intake_summary("other-ref"))
            weak_artifact, _weak_summary = self._build(
                root,
                self._intake_summary(same_evidence_ref_required="true"),
            )

        self.assertEqual(mismatch_artifact["review_decision"], "blocked_evidence_ref_mismatch_not_proven")
        self.assertEqual(mismatch_summary["same_evidence_ref_status"]["status"], "mismatch")
        self.assertEqual(weak_artifact["review_decision"], "blocked_evidence_ref_mismatch_not_proven")

    def test_unsafe_copy_success_claim_and_raw_path_fail_closed_and_stay_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_intake = self._intake_summary(
                accepted=[
                    {
                        "material": "real_elevator_door_state",
                        "safe_ref": "/Users/m4/raw-field.log /cmd_vel checksum=abcdef123456",
                        "required": True,
                    }
                ]
            )
            success_intake = self._intake_summary(delivery_success=True)
            unsafe_artifact, unsafe_summary = self._build(root, unsafe_intake)
            success_artifact, _success_summary = self._build(root, success_intake)

        self.assertEqual(unsafe_artifact["review_decision"], "blocked_unsafe_material_review_decision_not_proven")
        self.assertEqual(success_artifact["review_decision"], "blocked_unsafe_material_review_decision_not_proven")
        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("abcdef123456", encoded)


if __name__ == "__main__":
    unittest.main()
