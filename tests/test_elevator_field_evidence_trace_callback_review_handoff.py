#!/usr/bin/env python3
"""elevator_field_evidence_trace_callback_review_handoff 的离线围栏测试。"""

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

import elevator_field_evidence_trace_callback_review_handoff as handoff  # noqa: E402


class ElevatorFieldEvidenceTraceCallbackReviewHandoffTest(unittest.TestCase):
    def _materials(self) -> list[str]:
        # fixture 只使用材料类别名，不读取真实现场材料目录。
        return list(handoff.REQUIRED_ROUTE_ELEVATOR_MATERIALS)

    def _review_summary(
        self,
        evidence_ref: str = "ev-elevator-handoff-001",
        review_decision: str = "ready_for_elevator_field_owner_handoff_not_proven",
        **extra: object,
    ) -> dict[str, object]:
        # ready summary 模拟上一轮 callback review decision 的 safe/redacted 输出。
        payload: dict[str, object] = {
            "schema": "trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "overall_status": "not_proven",
            "status": review_decision,
            "review_decision": review_decision,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": {"status": "matched"},
            "required_route_elevator_materials": self._materials(),
            "missing_required_materials": [],
            "rejected_callback_materials": [],
            "evidence_boundary": "software_proof_docker_elevator_field_evidence_trace_callback_review_decision_gate",
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

    def _build(self, root: Path, payload: dict[str, object] | str, ref: str = "ev-elevator-handoff-001") -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 handoff，而不是路径拼接。
        path = self._write_json(root, "review_decision.json", payload)
        artifact, summary, exit_code = handoff.build_elevator_field_evidence_trace_callback_review_handoff(str(path), ref)
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_review_decision_maps_to_field_execution_owner_handoff_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary = self._build(Path(tmp), self._review_summary())

        self.assertEqual(artifact["schema"], "trashbot.elevator_field_evidence_trace_callback_review_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.elevator_field_evidence_trace_callback_review_handoff_summary.v1")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["handoff_status"], "ready_for_field_execution_owner_handoff_not_proven")
        self.assertEqual(summary["source_review_decision"]["review_decision"], "ready_for_elevator_field_owner_handoff_not_proven")
        self.assertEqual(summary["missing_required_materials"], [])
        self.assertEqual(summary["rejected_callback_materials"], [])
        self.assertIn("real_route_elevator_field_pass", summary["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_backfill_review_decision_maps_to_owner_material_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payload = self._review_summary(
                review_decision="needs_route_elevator_material_backfill_not_proven",
                status="needs_route_elevator_material_backfill_not_proven",
                missing_required_materials=[{"material": "real_elevator_door_state", "reason": "field_owner_missing"}],
            )
            artifact, summary = self._build(Path(tmp), payload)

        self.assertEqual(artifact["handoff_status"], "ready_for_owner_material_backfill_not_proven")
        self.assertIn("real_elevator_door_state", json.dumps(summary["missing_required_materials"], ensure_ascii=False))
        self.assertIn("same_evidence_ref_real_field_material_backfill", summary["next_required_evidence"][0])

    def test_nested_file_and_env_sources_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapped_path = self._write_json(
                root,
                "wrapped.json",
                {
                    "payload": {
                        "robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary": self._review_summary(
                            "ev-elevator-handoff-002"
                        )
                    }
                },
            )
            os.environ["ROBER_ELEVATOR_FIELD_CALLBACK_REVIEW_DECISION_JSON"] = f"file:{wrapped_path}"
            try:
                artifact, summary, exit_code = handoff.build_elevator_field_evidence_trace_callback_review_handoff(
                    "env:ROBER_ELEVATOR_FIELD_CALLBACK_REVIEW_DECISION_JSON",
                    "ev-elevator-handoff-002",
                )
            finally:
                os.environ.pop("ROBER_ELEVATOR_FIELD_CALLBACK_REVIEW_DECISION_JSON", None)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["handoff_status"], "ready_for_field_execution_owner_handoff_not_proven")
        self.assertEqual(artifact["source_callback_review_decision"]["source_style"], "env_source")
        self.assertEqual(summary["safe_evidence_ref"], "ev-elevator-handoff-002")

    def test_missing_bad_json_and_unsupported_schema_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_json = self._write_json(root, "bad.json", "{bad-json")
            missing_artifact, missing_summary, _ = handoff.build_elevator_field_evidence_trace_callback_review_handoff(
                str(root / "missing.json"),
                "ev-elevator-handoff-001",
            )
            bad_artifact, _bad_summary, _ = handoff.build_elevator_field_evidence_trace_callback_review_handoff(
                str(bad_json),
                "ev-elevator-handoff-001",
            )
            unsupported_artifact, _unsupported_summary = self._build(
                root,
                self._review_summary(schema="trashbot.unsupported.v1"),
            )

        self.assertEqual(missing_artifact["handoff_status"], "blocked_missing_review_decision_not_proven")
        self.assertEqual(missing_summary["handoff_status"], "blocked_missing_review_decision_not_proven")
        self.assertEqual(bad_artifact["handoff_status"], "blocked_unsupported_review_decision_not_proven")
        self.assertEqual(unsupported_artifact["handoff_status"], "blocked_unsupported_review_decision_not_proven")

    def test_evidence_ref_mismatch_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch_artifact, mismatch_summary = self._build(root, self._review_summary("other-ref"))
            weak_artifact, _weak_summary = self._build(
                root,
                self._review_summary(same_evidence_ref_required="true"),
            )

        self.assertEqual(mismatch_artifact["handoff_status"], "blocked_evidence_ref_mismatch_not_proven")
        self.assertEqual(mismatch_summary["same_evidence_ref_status"]["status"], "mismatch")
        self.assertEqual(weak_artifact["handoff_status"], "blocked_evidence_ref_mismatch_not_proven")

    def test_unsupported_review_decision_requests_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary = self._build(
                Path(tmp),
                self._review_summary(
                    status="needs_callback_packet_rerun_not_proven",
                    review_decision="needs_callback_packet_rerun_not_proven",
                ),
            )

        self.assertEqual(artifact["handoff_status"], "needs_review_decision_rerun_not_proven")
        self.assertIn("unsupported_source_review_decision:needs_callback_packet_rerun_not_proven", summary["status_reasons"])

    def test_unsafe_copy_and_success_claim_fail_closed_and_stay_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_payload = self._review_summary(owner_handoff=["raw /Users/m4/field.log /cmd_vel checksum=abcdef123456"])
            success_payload = self._review_summary(delivery_success=True)
            unsafe_artifact, unsafe_summary = self._build(root, unsafe_payload)
            success_artifact, _success_summary = self._build(root, success_payload)

        self.assertEqual(unsafe_artifact["handoff_status"], "blocked_unsafe_handoff_copy_not_proven")
        self.assertEqual(success_artifact["handoff_status"], "blocked_unsafe_handoff_copy_not_proven")
        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("abcdef123456", encoded)


if __name__ == "__main__":
    unittest.main()
