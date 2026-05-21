#!/usr/bin/env python3
"""field evidence real material request dispatch gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_real_material_request_dispatch as dispatch  # noqa: E402


# 测试约束 01：fixture 只表达 safe acceptance backfill summary。
# 测试约束 02：ready status 只证明 request dispatch 可派发，不证明现场通过。
# 测试约束 03：九类 required_materials 必须全部同一 evidence_ref。
# 测试约束 04：task record、Nav2、fixed-route、电梯、人工协助、dropoff/cancel 和 delivery result 都只是待采材料。
# 测试约束 05：true phone/browser evidence 只是材料请求，不证明真实手机通过。
# 测试约束 06：缺 source、bad JSON、unsupported schema、未 ready 必须 fail closed。
# 测试约束 07：same evidence_ref mismatch 必须 fail closed。
# 测试约束 08：raw path、ROS topic、checksum、serial/UART/WAVE ROVER 必须阻断。
# 测试约束 09：delivery_success=true、safe_to_control=true 必须拒绝。
# 测试约束 10：wrapper/nested JSON 必须可消费。
# 测试约束 11：所有输出保持 safe_to_control=false。
# 测试约束 12：所有输出保持 delivery_success=false。
# 测试约束 13：所有输出保持 primary_actions_enabled=false。
# 测试约束 14：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRealMaterialRequestDispatchTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不模拟真实现场材料。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _backfill_summary(self, evidence_ref: str, ready: bool = True) -> dict[str, object]:
        # 样本沿用上一轮 acceptance backfill 的 summary 形态。
        status = dispatch.READY_BACKFILL_STATUS if ready else "blocked_missing_materials"
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
            "material_completeness": {
                "required_count": 8,
                "accepted_count": 8 if ready else 7,
                "is_complete": ready,
                "missing_materials": [] if ready else ["delivery_result"],
                "rejected_materials": [],
            },
            "acceptance_backfill_gap_summary": {
                "gap_count": 0 if ready else 1,
                "missing_materials": [] if ready else ["delivery_result"],
            },
            "not_proven": ["not_proven"],
            "safe_copy": {
                "source": "software_proof",
                "status": status,
                "backfill_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "material_completeness": {"is_complete": ready},
                "acceptance_backfill_gap_summary": {"gap_count": 0 if ready else 1},
            },
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }

    def _build(self, root: Path, payload: dict[str, object], evidence_ref: str = "field-run-001") -> tuple[dict[str, object], dict[str, object]]:
        # 公共 helper 让 case 聚焦 schema、boundary 和 fail-closed 规则。
        source_path = self._write_json(root, "backfill.json", payload)
        artifact, summary, exit_code = dispatch.build_field_evidence_real_material_request_dispatch(
            str(source_path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_backfill_builds_real_material_request_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, {"payload": {"summary": self._backfill_summary("field-run-001")}})

        self.assertEqual(artifact["schema"], "trashbot.field_evidence_real_material_request_dispatch.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_real_material_request_dispatch_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_real_material_request_dispatch_gate",
        )
        self.assertEqual(artifact["status"], "ready_for_field_owner_real_material_request_not_proven")
        self.assertEqual(artifact["source_acceptance_backfill"]["schema_status"], "supported")
        self.assertEqual(artifact["required_materials"], list(dispatch.REQUIRED_MATERIALS))
        self.assertEqual(len(artifact["request_items"]), 9)
        self.assertIn("elevator_door_floor_evidence", artifact["required_materials"])
        self.assertIn("human_assistance_note", artifact["required_materials"])
        self.assertIn("true phone/browser evidence", json.dumps(summary, ensure_ascii=False))
        self.assertIn("not_proven", json.dumps(artifact, ensure_ascii=False))
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_artifact_input_and_nested_safe_copy_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact_input = self._backfill_summary("field-run-002")
            artifact_input["schema"] = "trashbot.field_evidence_rerun_execution_result_acceptance_backfill.v1"
            artifact_input["safe_copy"] = {
                "source": "software_proof",
                "evidence_ref": "field-run-002",
                "status": dispatch.READY_BACKFILL_STATUS,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "material_completeness": {"is_complete": True},
            }
            artifact, summary = self._build(root, {"data": {"acceptance_backfill": artifact_input}}, "field-run-002")

        self.assertEqual(artifact["source_acceptance_backfill"]["schema"], "trashbot.field_evidence_rerun_execution_result_acceptance_backfill.v1")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertEqual(summary["safe_copy"]["required_materials"], list(dispatch.REQUIRED_MATERIALS))

    def test_missing_bad_json_unsupported_and_not_ready_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_artifact, missing_summary, _ = dispatch.build_field_evidence_real_material_request_dispatch(
                str(root / "missing.json"),
                "field-run-003",
            )
            bad_path = root / "bad.json"
            bad_path.write_text("{bad json", encoding="utf-8")
            bad_artifact, _bad_summary, _ = dispatch.build_field_evidence_real_material_request_dispatch(
                str(bad_path),
                "field-run-003",
            )
            unsupported = self._backfill_summary("field-run-003")
            unsupported["schema"] = "trashbot.unsupported.v1"
            unsupported_artifact, _unsupported_summary = self._build(root, unsupported, "field-run-003")
            not_ready_artifact, _not_ready_summary = self._build(root, self._backfill_summary("field-run-003", ready=False), "field-run-003")

        self.assertEqual(missing_artifact["status"], "blocked_missing_field_evidence_rerun_execution_result_acceptance_backfill")
        self.assertEqual(bad_artifact["status"], "blocked_bad_json")
        self.assertEqual(unsupported_artifact["status"], "blocked_unsupported_schema")
        self.assertEqual(not_ready_artifact["status"], "blocked_acceptance_backfill_not_ready")
        self.assertFalse(missing_artifact["delivery_success"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_mismatch_weak_same_ref_unsafe_and_success_claim_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weak = self._backfill_summary("field-run-004")
            weak["same_evidence_ref_required"] = "true"
            weak_artifact, _weak_summary = self._build(root, weak, "field-run-004")
            mismatch_artifact, _mismatch_summary = self._build(root, self._backfill_summary("field-run-004"), "other-field-run")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe = self._backfill_summary("field-run-005")
            unsafe["safe_copy"] = {
                "source": "software_proof",
                "status": dispatch.READY_BACKFILL_STATUS,
                "evidence_ref": "field-run-005",
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "acceptance_backfill_gap_summary": {"operator_note": "Authorization: Bearer abc"},
            }
            unsafe_artifact, _unsafe_summary = self._build(root, unsafe, "field-run-005")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            success = self._backfill_summary("field-run-006")
            success["safe_to_control"] = True
            success_artifact, success_summary = self._build(root, success, "field-run-006")

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(weak_artifact["status"], "blocked_same_evidence_ref_not_required")
        self.assertEqual(mismatch_artifact["status"], "blocked_same_evidence_ref_not_required")
        self.assertEqual(unsafe_artifact["status"], "blocked_unsafe_source_state")
        self.assertNotIn("Bearer abc", encoded)
        self.assertEqual(success_artifact["status"], "blocked_unsafe_source_state")
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])
        self.assertFalse(success_summary["safe_to_control"])

    def test_output_does_not_expose_forbidden_raw_runtime_or_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._backfill_summary("field-run-007"), "field-run-007")

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Traceback", encoded)
        self.assertNotIn("checksum", encoded)
        self.assertIn("software_proof_docker_field_evidence_real_material_request_dispatch_gate", encoded)
        self.assertIn("delivery_success", encoded)
        self.assertFalse(artifact["safe_copy"]["delivery_success"])


if __name__ == "__main__":
    unittest.main()
