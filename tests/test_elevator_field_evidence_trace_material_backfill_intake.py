#!/usr/bin/env python3
"""elevator_field_evidence_trace_material_backfill_intake 的离线围栏测试。"""

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

import elevator_field_evidence_trace_material_backfill_intake as intake  # noqa: E402


class ElevatorFieldEvidenceTraceMaterialBackfillIntakeTest(unittest.TestCase):
    def _materials(self) -> list[str]:
        # fixture 只使用材料类别名，不读取真实现场材料目录。
        return list(intake.REQUIRED_ROUTE_ELEVATOR_MATERIALS)

    def _handoff_summary(
        self,
        evidence_ref: str = "ev-elevator-material-001",
        handoff_status: str = "ready_for_owner_material_backfill_not_proven",
        **extra: object,
    ) -> dict[str, object]:
        # ready summary 模拟上一轮 callback review handoff 的 safe/redacted 输出。
        payload: dict[str, object] = {
            "schema": "trashbot.elevator_field_evidence_trace_callback_review_handoff_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "overall_status": "not_proven",
            "status": handoff_status,
            "handoff_status": handoff_status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": {"status": "matched"},
            "required_route_elevator_materials": self._materials(),
            "missing_required_materials": [{"material": material, "reason": "owner_backfill_required"} for material in self._materials()],
            "evidence_boundary": "software_proof_docker_elevator_field_evidence_trace_callback_review_handoff_gate",
            "not_proven": ["real_route_elevator_field_pass", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _packet(
        self,
        evidence_ref: str = "ev-elevator-material-001",
        materials: list[str] | None = None,
        **extra: object,
    ) -> dict[str, object]:
        # operator packet 只提供安全材料引用，不提供真实文件路径。
        selected = self._materials() if materials is None else materials
        payload: dict[str, object] = {
            "schema": "trashbot.elevator_field_evidence_trace_material_backfill_packet.v1",
            "source": "software_proof",
            "overall_status": "not_proven",
            "packet_status": "safe_refs_only",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "provided_material_refs": [
                {"material": material, "safe_ref": f"{evidence_ref}:{material}:redacted_ref"} for material in selected
            ],
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
        handoff_payload: dict[str, object] | str,
        packet_payload: dict[str, object] | str,
        ref: str = "ev-elevator-material-001",
    ) -> tuple[dict, dict]:
        # 公共 helper 让 case 聚焦 intake，而不是路径拼接。
        handoff_path = self._write_json(root, "handoff.json", handoff_payload)
        packet_path = self._write_json(root, "packet.json", packet_payload)
        artifact, summary, exit_code = intake.build_elevator_field_evidence_trace_material_backfill_intake(
            str(handoff_path),
            str(packet_path),
            ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_full_safe_material_refs_are_ready_for_material_review_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary = self._build(Path(tmp), self._handoff_summary(), self._packet())

        self.assertEqual(artifact["schema"], "trashbot.elevator_field_evidence_trace_material_backfill_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.elevator_field_evidence_trace_material_backfill_intake_summary.v1")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["intake_status"], "ready_for_material_review_not_proven")
        self.assertEqual(summary["source_handoff"]["handoff_status"], "ready_for_owner_material_backfill_not_proven")
        self.assertEqual(summary["operator_material_packet"]["packet_status"], "safe_refs_only")
        self.assertEqual(summary["missing_required_materials"], [])
        self.assertIn("real_elevator_door_state", json.dumps(summary["accepted_material_refs"], ensure_ascii=False))
        self.assertIn("real_delivery_result", json.dumps(summary["accepted_material_refs"], ensure_ascii=False))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_required_materials_need_backfill(self) -> None:
        partial = ["real_elevator_door_state", "real_target_floor_confirmation"]
        with tempfile.TemporaryDirectory() as tmp:
            artifact, summary = self._build(Path(tmp), self._handoff_summary(), self._packet(materials=partial))

        self.assertEqual(artifact["intake_status"], "needs_required_material_backfill_not_proven")
        encoded_missing = json.dumps(summary["missing_required_materials"], ensure_ascii=False)
        self.assertIn("real_human_assistance_record", encoded_missing)
        self.assertIn("real_delivery_result", encoded_missing)
        self.assertIn("same_evidence_ref_missing_material_backfill_then_review", summary["next_required_evidence"][0])

    def test_nested_env_sources_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = self._write_json(
                root,
                "wrapped_handoff.json",
                {"payload": {"elevator_field_evidence_trace_callback_review_handoff_summary": self._handoff_summary("ev-elevator-material-002")}},
            )
            packet_path = self._write_json(
                root,
                "wrapped_packet.json",
                {"data": {"operator_material_packet": self._packet("ev-elevator-material-002")}},
            )
            os.environ["ROBER_ELEVATOR_FIELD_HANDOFF_JSON"] = f"file:{handoff_path}"
            os.environ["ROBER_ELEVATOR_FIELD_MATERIAL_PACKET_JSON"] = f"file:{packet_path}"
            try:
                artifact, summary, exit_code = intake.build_elevator_field_evidence_trace_material_backfill_intake(
                    "env:ROBER_ELEVATOR_FIELD_HANDOFF_JSON",
                    "env:ROBER_ELEVATOR_FIELD_MATERIAL_PACKET_JSON",
                    "ev-elevator-material-002",
                )
            finally:
                os.environ.pop("ROBER_ELEVATOR_FIELD_HANDOFF_JSON", None)
                os.environ.pop("ROBER_ELEVATOR_FIELD_MATERIAL_PACKET_JSON", None)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["intake_status"], "ready_for_material_review_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-elevator-material-002")
        self.assertEqual(summary["source_handoff"]["source_style"], "env_source")

    def test_missing_bad_json_and_unsupported_handoff_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad_json = self._write_json(root, "bad.json", "{bad-json")
            packet = self._write_json(root, "packet.json", self._packet())
            missing_artifact, missing_summary, _ = intake.build_elevator_field_evidence_trace_material_backfill_intake(
                str(root / "missing.json"),
                str(packet),
                "ev-elevator-material-001",
            )
            bad_artifact, _bad_summary, _ = intake.build_elevator_field_evidence_trace_material_backfill_intake(
                str(bad_json),
                str(packet),
                "ev-elevator-material-001",
            )
            unsupported_artifact, _unsupported_summary = self._build(
                root,
                self._handoff_summary(schema="trashbot.unsupported.v1"),
                self._packet(),
            )

        self.assertEqual(missing_artifact["intake_status"], "blocked_missing_handoff_not_proven")
        self.assertEqual(missing_summary["intake_status"], "blocked_missing_handoff_not_proven")
        self.assertEqual(bad_artifact["intake_status"], "blocked_missing_handoff_not_proven")
        self.assertEqual(unsupported_artifact["intake_status"], "blocked_unsupported_handoff_not_proven")

    def test_missing_material_packet_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = self._write_json(root, "handoff.json", self._handoff_summary())
            missing_packet_artifact, _missing_packet_summary, _ = intake.build_elevator_field_evidence_trace_material_backfill_intake(
                str(handoff),
                str(root / "missing_packet.json"),
                "ev-elevator-material-001",
            )
            weak_artifact, _weak_summary = self._build(
                root,
                self._handoff_summary(same_evidence_ref_required="true"),
                self._packet(),
            )

        self.assertEqual(missing_packet_artifact["intake_status"], "blocked_missing_material_packet_not_proven")
        self.assertEqual(weak_artifact["intake_status"], "blocked_evidence_ref_mismatch_not_proven")

    def test_evidence_ref_mismatch_and_placeholder_refs_do_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch_artifact, mismatch_summary = self._build(root, self._handoff_summary("other-ref"), self._packet())
            placeholder_packet = self._packet()
            placeholder_packet["provided_material_refs"] = [
                {"material": material, "safe_ref": "TODO"} for material in self._materials()
            ]
            placeholder_artifact, placeholder_summary = self._build(root, self._handoff_summary(), placeholder_packet)

        self.assertEqual(mismatch_artifact["intake_status"], "blocked_evidence_ref_mismatch_not_proven")
        self.assertEqual(mismatch_summary["same_evidence_ref_status"]["status"], "mismatch")
        self.assertEqual(placeholder_artifact["intake_status"], "needs_required_material_backfill_not_proven")
        self.assertIn("operator_packet_ref_placeholder", json.dumps(placeholder_summary["missing_required_materials"]))

    def test_unsafe_copy_and_success_claim_fail_closed_and_stay_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_packet = self._packet(
                provided_material_refs=[
                    {"material": "real_elevator_door_state", "safe_ref": "/Users/m4/raw-field.log /cmd_vel checksum=abcdef123456"}
                ]
            )
            success_packet = self._packet(delivery_success=True)
            unsafe_artifact, unsafe_summary = self._build(root, self._handoff_summary(), unsafe_packet)
            success_artifact, _success_summary = self._build(root, self._handoff_summary(), success_packet)

        self.assertEqual(unsafe_artifact["intake_status"], "blocked_unsafe_material_ref_not_proven")
        self.assertEqual(success_artifact["intake_status"], "blocked_unsafe_material_ref_not_proven")
        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("abcdef123456", encoded)


if __name__ == "__main__":
    unittest.main()
