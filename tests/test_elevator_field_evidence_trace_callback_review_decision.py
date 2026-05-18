#!/usr/bin/env python3
"""elevator_field_evidence_trace_callback_review_decision 的离线围栏测试。"""

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

import elevator_field_evidence_trace_callback_review_decision as review  # noqa: E402


class ElevatorFieldEvidenceTraceCallbackReviewDecisionTest(unittest.TestCase):
    def _materials(self) -> list[str]:
        # fixture 只使用材料类别名，不读取真实现场材料目录。
        return list(review.REQUIRED_ROUTE_ELEVATOR_MATERIALS)

    def _intake_summary(self, evidence_ref: str = "ev-elevator-field-001", **extra: object) -> dict[str, object]:
        # ready summary 模拟上一轮 callback intake 的 safe/redacted 输出。
        payload: dict[str, object] = {
            "schema": "trashbot.elevator_field_evidence_trace_callback_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "overall_status": "not_proven",
            "status": "callback_packet_intake_ready_for_review_not_proven",
            "intake_status": "callback_packet_intake_ready_for_review_not_proven",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": {"status": "matched"},
            "required_route_elevator_materials": self._materials(),
            "missing_required_materials": [],
            "rejected_callback_materials": [],
            "evidence_boundary": "software_proof_docker_elevator_field_evidence_trace_callback_intake_gate",
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

    def _build(self, root: Path, payload: dict[str, object] | str, ref: str = "ev-elevator-field-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 decision，而不是路径拼接。
        path = self._write_json(root, "intake.json", payload)
        artifact, summary, exit_code = review.build_elevator_field_evidence_trace_callback_review_decision(str(path), ref)
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_intake_maps_to_owner_handoff_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary = self._build(Path(tmp), self._intake_summary())

        self.assertEqual(artifact["schema"], "trashbot.elevator_field_evidence_trace_callback_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["review_decision"], "ready_for_elevator_field_owner_handoff_not_proven")
        self.assertEqual(summary["source_callback_intake"]["intake_status"], "callback_packet_intake_ready_for_review_not_proven")
        self.assertEqual(summary["missing_required_materials"], [])
        self.assertEqual(summary["rejected_callback_materials"], [])
        self.assertIn("real_route_elevator_field_pass", summary["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_nested_file_and_env_sources_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapped_path = self._write_json(
                root,
                "wrapped.json",
                {"payload": {"elevator_field_evidence_trace_callback_intake_summary": self._intake_summary("ev-elevator-field-002")}},
            )
            os.environ["ROBER_ELEVATOR_FIELD_CALLBACK_INTAKE_JSON"] = f"file:{wrapped_path}"
            try:
                artifact, summary, exit_code = review.build_elevator_field_evidence_trace_callback_review_decision(
                    "env:ROBER_ELEVATOR_FIELD_CALLBACK_INTAKE_JSON",
                    "ev-elevator-field-002",
                )
            finally:
                os.environ.pop("ROBER_ELEVATOR_FIELD_CALLBACK_INTAKE_JSON", None)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_decision"], "ready_for_elevator_field_owner_handoff_not_proven")
        self.assertEqual(artifact["source_callback_intake"]["source_style"], "env_source")
        self.assertEqual(summary["safe_evidence_ref"], "ev-elevator-field-002")

    def test_missing_bad_json_and_unsupported_schema_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_json = self._write_json(root, "bad.json", "{bad-json")
            missing_artifact, missing_summary, _ = review.build_elevator_field_evidence_trace_callback_review_decision(
                str(root / "missing.json"),
                "ev-elevator-field-001",
            )
            bad_artifact, _bad_summary, _ = review.build_elevator_field_evidence_trace_callback_review_decision(
                str(bad_json),
                "ev-elevator-field-001",
            )
            unsupported_artifact, _unsupported_summary = self._build(
                root,
                self._intake_summary(schema="trashbot.unsupported.v1"),
            )

        self.assertEqual(missing_artifact["review_decision"], "blocked_missing_callback_intake_not_proven")
        self.assertEqual(missing_summary["review_decision"], "blocked_missing_callback_intake_not_proven")
        self.assertEqual(bad_artifact["review_decision"], "blocked_unsupported_callback_intake_not_proven")
        self.assertEqual(unsupported_artifact["review_decision"], "blocked_unsupported_callback_intake_not_proven")

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

    def test_missing_or_rejected_materials_need_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_payload = self._intake_summary(
                status="needs_route_elevator_material_backfill_not_proven",
                intake_status="needs_route_elevator_material_backfill_not_proven",
                missing_required_materials=[
                    {"material": "real_nav2_or_fixed_route_runtime_log", "reason": "callback_response_missing"}
                ],
            )
            rejected_payload = self._intake_summary(
                rejected_callback_materials=[
                    {"material": "real_target_floor_confirmation", "reason": "needs safer summary"}
                ],
            )
            missing_artifact, missing_summary = self._build(root, missing_payload)
            rejected_artifact, rejected_summary = self._build(root, rejected_payload)

        self.assertEqual(missing_artifact["review_decision"], "needs_route_elevator_material_backfill_not_proven")
        self.assertIn("real_nav2_or_fixed_route_runtime_log", json.dumps(missing_summary["missing_required_materials"], ensure_ascii=False))
        self.assertEqual(rejected_artifact["review_decision"], "needs_route_elevator_material_backfill_not_proven")
        self.assertIn("needs safer summary", json.dumps(rejected_summary["rejected_callback_materials"], ensure_ascii=False))

    def test_non_ready_intake_requests_callback_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary = self._build(
                Path(tmp),
                self._intake_summary(
                    status="blocked_missing_callback_packet_not_proven",
                    intake_status="blocked_missing_callback_packet_not_proven",
                ),
            )

        self.assertEqual(artifact["review_decision"], "needs_callback_packet_rerun_not_proven")
        self.assertIn("source_intake_status:blocked_missing_callback_packet_not_proven", summary["decision_reasons"])

    def test_unsafe_copy_and_success_claim_fail_closed_and_stay_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_payload = self._intake_summary(owner_handoff=["raw /Users/m4/field.log /cmd_vel checksum=abcdef123456"])
            success_payload = self._intake_summary(delivery_success=True)
            unsafe_artifact, unsafe_summary = self._build(root, unsafe_payload)
            success_artifact, _success_summary = self._build(root, success_payload)

        self.assertEqual(unsafe_artifact["review_decision"], "blocked_unsafe_callback_review_copy_not_proven")
        self.assertEqual(success_artifact["review_decision"], "blocked_unsafe_callback_review_copy_not_proven")
        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("abcdef123456", encoded)


if __name__ == "__main__":
    unittest.main()
