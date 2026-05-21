#!/usr/bin/env python3
"""field evidence rerun execution result acceptance backfill gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_execution_result_acceptance_backfill as backfill  # noqa: E402


# 测试约束 01：fixture 只表达 safe acceptance packet 和 sanitized material-dir。
# 测试约束 02：ready status 只证明 backfill gate 可复账，不证明现场通过。
# 测试约束 03：八类 required_materials 必须全部同一 evidence_ref。
# 测试约束 04：task record、Nav2、fixed-route、电梯、dropoff/cancel 和 delivery result 都只是材料类别。
# 测试约束 05：true phone/browser evidence 只是材料类别，不证明真实手机通过。
# 测试约束 06：缺 packet、缺材料、placeholder、rejected material 必须 fail closed。
# 测试约束 07：same evidence_ref mismatch 必须 fail closed。
# 测试约束 08：raw path、ROS topic、checksum、serial/UART/WAVE ROVER 必须阻断。
# 测试约束 09：delivery_success=true、safe_to_control=true 必须拒绝。
# 测试约束 10：wrapper/nested JSON 必须可消费。
# 测试约束 11：所有输出保持 safe_to_control=false。
# 测试约束 12：所有输出保持 delivery_success=false。
# 测试约束 13：所有输出保持 primary_actions_enabled=false。
# 测试约束 14：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRerunExecutionResultAcceptanceBackfillTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不模拟真实现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _packet_summary(self, evidence_ref: str, ready: bool = True) -> dict[str, object]:
        # 样本沿用上一轮 field acceptance packet 的 summary 形态。
        status = backfill.READY_PACKET_STATUS if ready else "needs_material_backfill"
        return {
            "schema": "trashbot.field_evidence_rerun_execution_result_acceptance_packet_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate",
            "status": status,
            "acceptance_verdict": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_status": "matched",
            "required_materials": list(backfill.REQUIRED_MATERIALS),
            "accepted_materials": list(backfill.REQUIRED_MATERIALS),
            "missing_materials": [],
            "rejected_materials": [],
            "not_proven": list(backfill.NOT_PROVEN),
            "safe_copy": {
                "source": "software_proof",
                "status": status,
                "acceptance_verdict": status,
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

    def _write_materials(self, root: Path, evidence_ref: str, overrides: dict[str, dict[str, object] | str] | None = None) -> Path:
        # 八类材料用最小脱敏元数据，避免测试夹带 raw runtime log。
        material_dir = root / "materials"
        material_dir.mkdir()
        overrides = overrides or {}
        for name in backfill.REQUIRED_MATERIALS:
            payload: dict[str, object] | str = {
                "evidence_ref": evidence_ref,
                "status": "provided",
                "source": "software_proof",
                "review_note": f"{name} sanitized material index for metadata review",
            }
            if name in overrides:
                payload = overrides[name]
            target = material_dir / backfill.MATERIAL_ALIASES[name][0]
            if isinstance(payload, str):
                target.write_text(payload, encoding="utf-8")
            else:
                target.write_text(json.dumps(payload), encoding="utf-8")
        return material_dir

    def _build(self, root: Path, packet_payload: dict[str, object], material_dir: Path, evidence_ref: str = "rerun-001") -> tuple[dict[str, object], dict[str, object]]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        packet_path = self._write_json(root, "packet.json", packet_payload)
        artifact, summary, exit_code = backfill.build_field_evidence_rerun_execution_result_acceptance_backfill(
            str(packet_path),
            str(material_dir),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_complete_material_dir_builds_backfill_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_dir = self._write_materials(root, "rerun-001")
            artifact, summary = self._build(root, {"payload": {"summary": self._packet_summary("rerun-001")}}, material_dir)

        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_backfill.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate",
        )
        self.assertEqual(artifact["status"], "ready_for_field_evidence_rerun_execution_result_acceptance_backfill_not_proven")
        self.assertEqual(artifact["source_acceptance_packet"]["schema_status"], "supported")
        self.assertTrue(artifact["material_completeness"]["is_complete"])
        self.assertEqual(artifact["acceptance_backfill_gap_summary"]["gap_count"], 0)
        self.assertIn("Nav2/fixed-route runtime log", json.dumps(summary, ensure_ascii=False))
        self.assertIn("true phone/browser evidence", json.dumps(summary, ensure_ascii=False))
        self.assertIn("diagnostics/mobile safe summary", json.dumps(summary, ensure_ascii=False))
        self.assertIn("field_evidence_rerun_execution_result_acceptance_packet.py", " ".join(summary["rerun_commands"]))
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_artifact_input_and_nested_safe_copy_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_dir = self._write_materials(root, "rerun-002")
            artifact_input = self._packet_summary("rerun-002")
            artifact_input["schema"] = "trashbot.field_evidence_rerun_execution_result_acceptance_packet.v1"
            artifact_input["safe_copy"] = {
                "source": "software_proof",
                "evidence_ref": "rerun-002",
                "status": backfill.READY_PACKET_STATUS,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            artifact, summary = self._build(root, {"data": {"acceptance_packet": artifact_input}}, material_dir, "rerun-002")

        self.assertEqual(artifact["source_acceptance_packet"]["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_packet.v1")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertEqual(summary["safe_copy"]["material_completeness"]["accepted_count"], len(backfill.REQUIRED_MATERIALS))

    def test_missing_packet_bad_json_unsupported_and_packet_not_ready_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_dir = self._write_materials(root, "rerun-003")
            missing_artifact, missing_summary, _ = backfill.build_field_evidence_rerun_execution_result_acceptance_backfill(
                str(root / "missing.json"),
                str(material_dir),
                "rerun-003",
            )
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_artifact, _bad_summary, _ = backfill.build_field_evidence_rerun_execution_result_acceptance_backfill(
                str(bad_path),
                str(material_dir),
                "rerun-003",
            )
            unsupported = self._packet_summary("rerun-003")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _unsupported_summary = self._build(root, unsupported, material_dir, "rerun-003")
            not_ready_artifact, _not_ready_summary = self._build(root, self._packet_summary("rerun-003", ready=False), material_dir, "rerun-003")

        self.assertEqual(missing_artifact["status"], "blocked_missing_field_evidence_rerun_execution_result_acceptance_packet")
        self.assertEqual(bad_artifact["status"], "blocked_bad_json")
        self.assertEqual(unsupported_artifact["status"], "blocked_unsupported_schema")
        self.assertEqual(not_ready_artifact["status"], "blocked_acceptance_packet_not_ready")
        self.assertFalse(missing_artifact["delivery_success"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_missing_placeholder_mismatch_unsafe_and_success_claim_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_dir = self._write_materials(root, "rerun-004")
            (missing_dir / "delivery_result.json").unlink()
            missing_artifact, _missing_summary = self._build(root, self._packet_summary("rerun-004"), missing_dir, "rerun-004")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            placeholder_dir = self._write_materials(root, "rerun-005", {"elevator_evidence": {"evidence_ref": "rerun-005", "status": "placeholder"}})
            placeholder_artifact, _placeholder_summary = self._build(root, self._packet_summary("rerun-005"), placeholder_dir, "rerun-005")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch_dir = self._write_materials(root, "rerun-006", {"task_record": {"evidence_ref": "other-run", "status": "provided"}})
            mismatch_artifact, _mismatch_summary = self._build(root, self._packet_summary("rerun-006"), mismatch_dir, "rerun-006")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_dir = self._write_materials(
                root,
                "rerun-007",
                {"nav2_fixed_route_runtime_log": "evidence_ref: rerun-007\nAuthorization: Bearer abc\n/cmd_vel\n/dev/ttyUSB0\n"},
            )
            unsafe_artifact, _unsafe_summary = self._build(root, self._packet_summary("rerun-007"), unsafe_dir, "rerun-007")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            success_dir = self._write_materials(root, "rerun-008", {"delivery_result": {"evidence_ref": "rerun-008", "delivery_success": True}})
            success_artifact, success_summary = self._build(root, self._packet_summary("rerun-008"), success_dir, "rerun-008")

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(missing_artifact["status"], "blocked_missing_materials")
        self.assertEqual(placeholder_artifact["status"], "blocked_placeholder_only_materials")
        self.assertEqual(mismatch_artifact["status"], "blocked_same_evidence_ref_mismatch")
        self.assertEqual(unsafe_artifact["status"], "blocked_unsafe_material_copy")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertEqual(success_artifact["status"], "blocked_success_or_control_claim")
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])
        self.assertFalse(success_summary["safe_to_control"])

    def test_weak_same_ref_cli_ref_mismatch_and_source_success_claim_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            material_dir = self._write_materials(root, "rerun-009")
            weak = self._packet_summary("rerun-009")
            weak["same_evidence_ref_required"] = "true"
            weak_artifact, _weak_summary = self._build(root, weak, material_dir, "rerun-009")
            mismatch_artifact, _mismatch_summary = self._build(root, self._packet_summary("rerun-009"), material_dir, "another-run")
            source_success = self._packet_summary("rerun-009")
            source_success["safe_to_control"] = True
            source_success_artifact, _source_success_summary = self._build(root, source_success, material_dir, "rerun-009")

        self.assertEqual(weak_artifact["status"], "blocked_same_evidence_ref_not_required")
        self.assertEqual(mismatch_artifact["status"], "blocked_same_evidence_ref_not_required")
        self.assertEqual(source_success_artifact["status"], "blocked_unsafe_material_copy")


if __name__ == "__main__":
    unittest.main()
