#!/usr/bin/env python3
"""field evidence real material owner ack intake gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_real_material_followup_escalation_status as followup  # noqa: E402
import field_evidence_real_material_owner_ack_intake as intake  # noqa: E402


# 测试约束 01：fixture 只表达 followup safe summary，不模拟真实现场材料。
# 测试约束 02：acknowledged 只表示 owner 已接收分类，不代表 field pass。
# 测试约束 03：accepted/missing/rejected/blocked 必须保留材料类别语义。
# 测试约束 04：missing owner ack 必须 fail closed。
# 测试约束 05：evidence_ref mismatch 必须 fail closed。
# 测试约束 06：unsupported source/schema 必须 fail closed。
# 测试约束 07：success/control claim 必须 fail closed。
# 测试约束 08：输出保持 software_proof 与 not_proven。
# 测试约束 09：输出保持 safe_to_control=false。
# 测试约束 10：输出保持 delivery_success=false。
# 测试约束 11：输出保持 primary_actions_enabled=false。
# 测试约束 12：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRealMaterialOwnerAckIntakeTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实 route/elevator pass。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _followup_summary(self, evidence_ref: str, status: str = followup.READY_STATUS, unsafe: bool = False) -> dict[str, object]:
        # 样本沿用上一轮 followup escalation summary 的安全消费面。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_real_material_followup_escalation_status_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "field_evidence_real_material_followup_escalation_status": status,
            "followup_status": status,
            "evidence_boundary": "software_proof_docker_field_evidence_real_material_followup_escalation_status_gate",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "owner_escalation_items": [{"owner": ""robot-algorithm-engineer"", "missing_evidence": ["real elevator door state"]}],
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "source": "software_proof",
                "status": "not_proven",
                "field_evidence_real_material_followup_escalation_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
        }
        if unsafe:
            payload["safe_copy"] = {**payload["safe_copy"], "operator_note": "delivery_success=true"}
        return payload

    def _ack_packet(self, evidence_ref: str, ack_state: str = "acknowledged", unsafe: bool = False) -> dict[str, object]:
        # ack packet 是 owner-safe 表单，不包含真实 runtime log 或 raw artifact。
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_real_material_owner_ack_packet.v1",
            "source": "software_proof",
            "status": "not_proven",
            "owner_acknowledgement_state": ack_state,
            "owner_id": ""robot-algorithm-engineer"",
            "acknowledged_at": "2026-05-21T13:30:00Z",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "accepted_materials": ["route_elevator_runtime_materials"],
            "missing_materials": ["elevator_door_floor_materials"],
            "rejected_materials": ["dropoff_cancel_delivery_result_materials"],
            "blocked_materials": ["diagnostics_mobile_safe_summary_materials"],
            "safe_note": "owner ack only, all outcomes remain not_proven",
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "not_proven": True,
        }
        if unsafe:
            payload["safe_note"] = "field passed and control enabled"
        return payload

    def _build(
        self,
        root: Path,
        followup_payload: dict[str, object],
        ack_payload: dict[str, object],
        evidence_ref: str = "field-run-501",
    ) -> tuple[dict[str, object], dict[str, object]]:
        # 公共 helper 让 case 聚焦 intake 映射和边界。
        followup_path = self._write_json(root, "followup.json", followup_payload)
        ack_path = self._write_json(root, "ack.json", ack_payload)
        artifact, summary, exit_code = intake.build_field_evidence_real_material_owner_ack_intake(
            str(followup_path),
            str(ack_path),
            evidence_ref,
        )
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_acknowledged_packet_maps_to_owner_ack_intake_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._followup_summary("field-run-501"), self._ack_packet("field-run-501"))

        self.assertEqual(artifact["schema"], "trashbot.field_evidence_real_material_owner_ack_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_real_material_owner_ack_intake_summary.v1")
        self.assertEqual(summary["robot_diagnostics_schema"], "trashbot.robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary.v1")
        self.assertEqual(artifact["capability"], "field_evidence_real_material_owner_ack_intake")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_real_material_owner_ack_intake_gate",
        )
        self.assertEqual(artifact["owner_ack_intake_status"], "ready_for_field_evidence_real_material_owner_ack_intake_not_proven")
        self.assertEqual(summary["owner_acknowledgement"]["owner_acknowledgement_state"], "acknowledged")
        self.assertIn("route_elevator_runtime_materials", summary["material_categories"]["accepted"])
        self.assertIn("elevator_door_floor_materials", summary["material_categories"]["missing"])
        self.assertIn("dropoff_cancel_delivery_result_materials", summary["material_categories"]["rejected"])
        self.assertIn("diagnostics_mobile_safe_summary_materials", summary["material_categories"]["blocked"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_missing_ack_and_backfill_source_preserve_fail_closed_next_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(
                root,
                self._followup_summary("field-run-502", followup.BACKFILL_STATUS),
                self._ack_packet("field-run-502", ack_state="pending"),
                "field-run-502",
            )

        self.assertEqual(artifact["owner_ack_intake_status"], "missing_field_material_owner_ack_intake_not_proven")
        self.assertIn("provide_owner_safe_ack_packet_before_material_review", summary["owner_next_steps"])
        encoded = json.dumps(summary, ensure_ascii=False)
        self.assertIn("owner_acknowledgement_missing_or_pending", encoded)
        self.assertIn("not_proven", encoded)

    def test_robot_diagnostics_followup_alias_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alias = {
                "latest_status": {
                    "diagnostics": {
                        "robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary": self._followup_summary("field-run-503")
                    }
                }
            }
            artifact, summary = self._build(root, alias, self._ack_packet("field-run-503"), "field-run-503")

        self.assertEqual(artifact["owner_ack_intake_status"], "ready_for_field_evidence_real_material_owner_ack_intake_not_proven")
        self.assertEqual(summary["source_followup"]["schema"], "trashbot.field_evidence_real_material_followup_escalation_status_summary.v1")
        self.assertTrue(summary["same_evidence_ref_required"])

    def test_mismatch_unsupported_and_success_claims_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch, _ = self._build(root, self._followup_summary("field-run-504"), self._ack_packet("other-run"), "field-run-504")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsupported, _ = self._build(root, {"schema": "trashbot.unsupported.v1", "evidence_ref": "field-run-505"}, self._ack_packet("field-run-505"), "field-run-505")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe, unsafe_summary = self._build(root, self._followup_summary("field-run-506"), self._ack_packet("field-run-506", unsafe=True), "field-run-506")

        self.assertEqual(mismatch["owner_ack_intake_status"], "evidence_ref_mismatch_field_material_owner_ack_intake_blocked")
        self.assertEqual(unsupported["owner_ack_intake_status"], "blocked_unsupported_field_material_owner_ack_intake_source")
        self.assertEqual(unsafe["owner_ack_intake_status"], "blocked_rejected_or_unsafe_field_material_owner_ack_intake_not_proven")
        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertIn("delivery_success=false", encoded)
        self.assertFalse(unsafe["delivery_success"])

    def test_missing_source_outputs_blocked_status_without_control_enablement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ack_path = self._write_json(root, "ack.json", self._ack_packet("field-run-507"))
            artifact, summary, exit_code = intake.build_field_evidence_real_material_owner_ack_intake(
                str(root / "missing.json"),
                str(ack_path),
                "field-run-507",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["owner_ack_intake_status"], "blocked_unsupported_field_material_owner_ack_intake_source")
        self.assertFalse(summary["safe_to_control"])
        self.assertIn("followup_json_missing", artifact["blocked_reason"])

    def test_output_preserves_required_boundary_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._followup_summary("field-run-508"), self._ack_packet("field-run-508"), "field-run-508")

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_real_material_owner_ack_intake", encoded)
        self.assertIn("software_proof_docker_field_evidence_real_material_owner_ack_intake_gate", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Traceback", encoded)


if __name__ == "__main__":
    unittest.main()
