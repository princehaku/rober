#!/usr/bin/env python3
"""elevator_field_evidence_trace_callback_intake 的离线围栏测试。"""

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

import elevator_field_evidence_trace_callback_intake as intake  # noqa: E402


class ElevatorFieldEvidenceTraceCallbackIntakeTest(unittest.TestCase):
    def _materials(self) -> list[str]:
        # fixture 只列材料类别，不读取真实现场材料目录。
        return list(intake.REQUIRED_ROUTE_ELEVATOR_MATERIALS)

    def _callback_payload(self, evidence_ref: str = "ev-elevator-field-001", **extra: object) -> dict[str, object]:
        # callback packet 使用逐项 material_responses，便于机器判定缺项。
        payload: dict[str, object] = {
            "schema": "trashbot.elevator_field_evidence_trace_callback_packet.v1",
            "source": "software_proof",
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "owner_acknowledgement": "field owner acknowledges real materials still required",
            "material_responses": [
                {"material": material, "status": "received", "safe_note": f"{material} metadata recorded"}
                for material in self._materials()
            ],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _trace_payload(self, evidence_ref: str = "ev-elevator-field-001", **extra: object) -> dict[str, object]:
        # trace summary 来自 elevator_action_feedback_trace，不代表真实电梯运行。
        payload: dict[str, object] = {
            "schema": "trashbot.elevator_action_feedback_trace_summary.v1",
            "source": "software_proof",
            "overall_status": "not_proven",
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "current_step": "elevator:requesting_floor_help",
            "phases": [{"phase": "requesting_floor_help", "current_step": "elevator:requesting_floor_help"}],
            "required_route_elevator_materials": self._materials(),
            "not_proven": ["real_route_elevator_field_pass", "delivery_success=false"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _diagnostics_payload(self, evidence_ref: str = "ev-elevator-field-001", **extra: object) -> dict[str, object]:
        # diagnostics alias 是 phone-safe summary，不允许携带控制授权。
        payload: dict[str, object] = {
            "schema": "trashbot.robot_diagnostics_elevator_action_feedback_trace_summary.v1",
            "source": "software_proof",
            "overall_status": "not_proven",
            "status": "elevator_action_feedback_trace_not_proven",
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "current_step": "elevator:requesting_floor_help",
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _required_materials_payload(self, evidence_ref: str = "ev-elevator-field-001", **extra: object) -> dict[str, object]:
        # required materials artifact 只提供材料名和 same-ref，不提供真实文件内容。
        payload: dict[str, object] = {
            "schema": "trashbot.elevator_field_evidence_trace_required_materials.v1",
            "source": "software_proof",
            "overall_status": "not_proven",
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "required_route_elevator_materials": self._materials(),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _write_json(self, root: Path, name: str, payload: dict[str, object] | str) -> Path:
        # 所有测试文件都写到临时目录，避免依赖 repo 真实材料。
        path = root / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _build(
        self,
        root: Path,
        callback: dict[str, object] | str,
        trace: dict[str, object] | str,
        diagnostics: dict[str, object] | str,
        materials: dict[str, object] | str | None = None,
        evidence_ref: str = "ev-elevator-field-001",
    ) -> tuple[dict, dict]:
        # 公共 helper 让各 case 聚焦状态判定，而不是路径拼接。
        callback_path = self._write_json(root, "callback.json", callback)
        trace_path = self._write_json(root, "trace.json", trace)
        diagnostics_path = self._write_json(root, "diagnostics.json", diagnostics)
        materials_path = ""
        if materials is not None:
            materials_path = str(self._write_json(root, "materials.json", materials))
        artifact, summary, exit_code = intake.build_elevator_field_evidence_trace_callback_intake(
            str(callback_path),
            str(trace_path),
            str(diagnostics_path),
            materials_path,
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_callback_packet_intake_summary_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(
                root,
                self._callback_payload(),
                self._trace_payload(),
                self._diagnostics_payload(),
                self._required_materials_payload(),
            )

        self.assertEqual(artifact["schema"], "trashbot.elevator_field_evidence_trace_callback_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.elevator_field_evidence_trace_callback_intake_summary.v1")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["intake_status"], "callback_packet_intake_ready_for_review_not_proven")
        self.assertEqual(summary["same_evidence_ref_status"]["status"], "matched")
        self.assertEqual(len(summary["accepted_callback_materials"]), len(self._materials()))
        self.assertEqual(summary["missing_required_materials"], [])
        self.assertEqual(summary["rejected_callback_materials"], [])
        self.assertIn("real_route_elevator_field_pass", summary["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_nested_file_env_sources_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace_path = self._write_json(root, "nested_trace.json", {"payload": {"elevator_action_feedback_trace": self._trace_payload("ev-elevator-field-002")}})
            callback_path = self._write_json(root, "nested_callback.json", {"payload": {"safe_callback_packet": self._callback_payload("ev-elevator-field-002")}})
            diagnostics_path = self._write_json(root, "nested_diagnostics.json", {"payload": {"robot_diagnostics_elevator_action_feedback_trace_summary": self._diagnostics_payload("ev-elevator-field-002")}})
            os.environ["ROBER_ELEVATOR_TRACE_SUMMARY_JSON"] = f"file:{trace_path}"
            try:
                artifact, summary, _exit_code = intake.build_elevator_field_evidence_trace_callback_intake(
                    f"file:{callback_path}",
                    "env:ROBER_ELEVATOR_TRACE_SUMMARY_JSON",
                    str(diagnostics_path),
                    "",
                    "ev-elevator-field-002",
                )
            finally:
                os.environ.pop("ROBER_ELEVATOR_TRACE_SUMMARY_JSON", None)

        self.assertEqual(artifact["intake_status"], "callback_packet_intake_ready_for_review_not_proven")
        self.assertEqual(summary["source_trace"]["source_style"], "env_source")
        self.assertEqual(summary["callback_packet"]["field_status"], "supported")
        self.assertEqual(summary["safe_evidence_ref"], "ev-elevator-field-002")

    def test_missing_bad_json_and_unsupported_summaries_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_json = self._write_json(root, "bad.json", "{bad-json")
            trace_path = self._write_json(root, "trace.json", self._trace_payload())
            diagnostics_path = self._write_json(root, "diagnostics.json", self._diagnostics_payload())
            unsupported_trace = self._trace_payload(schema="trashbot.unsupported.v1")

            missing_artifact, _missing_summary, _ = intake.build_elevator_field_evidence_trace_callback_intake(
                str(root / "missing_callback.json"),
                str(trace_path),
                str(diagnostics_path),
                "",
                "ev-elevator-field-001",
            )
            bad_artifact, _bad_summary, _ = intake.build_elevator_field_evidence_trace_callback_intake(
                str(bad_json),
                str(trace_path),
                str(diagnostics_path),
                "",
                "ev-elevator-field-001",
            )
            unsupported_artifact, _unsupported_summary = self._build(
                root,
                self._callback_payload(),
                unsupported_trace,
                self._diagnostics_payload(),
            )

        self.assertEqual(missing_artifact["intake_status"], "blocked_missing_callback_packet_not_proven")
        self.assertEqual(bad_artifact["intake_status"], "blocked_unsupported_or_bad_json_not_proven")
        self.assertEqual(unsupported_artifact["intake_status"], "blocked_unsupported_trace_or_diagnostics_summary_not_proven")

    def test_evidence_ref_mismatch_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch_artifact, mismatch_summary = self._build(
                root,
                self._callback_payload("other-ref"),
                self._trace_payload(),
                self._diagnostics_payload(),
            )
            weak_artifact, _weak_summary = self._build(
                root,
                self._callback_payload(same_evidence_ref_required="true"),
                self._trace_payload(),
                self._diagnostics_payload(),
            )

        self.assertEqual(mismatch_artifact["intake_status"], "blocked_evidence_ref_mismatch_not_proven")
        self.assertEqual(mismatch_summary["same_evidence_ref_status"]["status"], "mismatch")
        self.assertEqual(weak_artifact["intake_status"], "blocked_evidence_ref_mismatch_not_proven")

    def test_missing_or_rejected_materials_need_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            partial_callback = self._callback_payload()
            partial_callback["material_responses"] = [
                {"material": "real_elevator_door_state", "status": "received", "safe_note": "metadata recorded"}
            ]
            missing_artifact, missing_summary = self._build(
                root,
                partial_callback,
                self._trace_payload(),
                self._diagnostics_payload(),
            )
            rejected_callback = self._callback_payload()
            rejected_callback["rejected_materials"] = [{"material": "real_target_floor_confirmation", "safe_note": "needs safer summary"}]
            rejected_artifact, rejected_summary = self._build(
                root,
                rejected_callback,
                self._trace_payload(),
                self._diagnostics_payload(),
            )

        self.assertEqual(missing_artifact["intake_status"], "needs_route_elevator_material_backfill_not_proven")
        self.assertIn("real_route_completion_signal", json.dumps(missing_summary["missing_required_materials"], ensure_ascii=False))
        self.assertEqual(rejected_artifact["intake_status"], "needs_route_elevator_material_backfill_not_proven")
        self.assertIn("needs safer summary", json.dumps(rejected_summary["rejected_callback_materials"], ensure_ascii=False))

    def test_unsafe_success_claim_unknown_field_and_weak_callback_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_callback = self._callback_payload(owner_handoff=["raw /Users/m4/field.log /cmd_vel checksum=abcdef123456"])
            unsafe_artifact, unsafe_summary = self._build(
                root,
                unsafe_callback,
                self._trace_payload(),
                self._diagnostics_payload(),
            )
            success_artifact, _success_summary = self._build(
                root,
                self._callback_payload(delivery_success=True),
                self._trace_payload(),
                self._diagnostics_payload(),
            )
            unknown_artifact, _unknown_summary = self._build(
                root,
                self._callback_payload(raw_log="/tmp/log.txt"),
                self._trace_payload(),
                self._diagnostics_payload(),
            )
            weak_callback = self._callback_payload(material_responses={"real_elevator_door_state": True})
            weak_artifact, _weak_summary = self._build(
                root,
                weak_callback,
                self._trace_payload(),
                self._diagnostics_payload(),
            )

        self.assertEqual(unsafe_artifact["intake_status"], "blocked_unsafe_callback_or_summary_copy_not_proven")
        self.assertEqual(success_artifact["intake_status"], "blocked_unsafe_callback_or_summary_copy_not_proven")
        self.assertEqual(unknown_artifact["intake_status"], "blocked_unsupported_callback_packet_not_proven")
        self.assertEqual(weak_artifact["intake_status"], "blocked_unsupported_callback_packet_not_proven")
        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("abcdef123456", encoded)


if __name__ == "__main__":
    unittest.main()
