#!/usr/bin/env python3
"""field evidence real material followup escalation status gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_real_material_followup_escalation_status as escalation  # noqa: E402
import field_evidence_real_material_response_review_handoff as handoff  # noqa: E402


# 测试约束 01：fixture 只表达 handoff safe summary，不模拟真实现场材料。
# 测试约束 02：ready handoff 也只能生成 escalation status，不能生成 field pass。
# 测试约束 03：missing evidence 必须保留 route/elevator/field material 缺口。
# 测试约束 04：Robot diagnostics safe alias 必须可消费。
# 测试约束 05：evidence_ref mismatch 必须 fail closed。
# 测试约束 06：unsupported schema/boundary 必须 fail closed。
# 测试约束 07：success/control claim 必须 fail closed。
# 测试约束 08：输出保持 software_proof 与 not_proven。
# 测试约束 09：输出保持 safe_to_control=false。
# 测试约束 10：输出保持 delivery_success=false。
# 测试约束 11：输出保持 primary_actions_enabled=false。
# 测试约束 12：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRealMaterialFollowupEscalationStatusTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实 route/elevator pass。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _handoff_summary(
        self,
        evidence_ref: str,
        handoff_status: str = handoff.READY_HANDOFF,
        unsafe: bool = False,
    ) -> dict[str, object]:
        # 样本沿用上一轮 handoff summary 的安全消费面。
        missing = ["real elevator door state", "real target floor confirmation", "real delivery result"]
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_real_material_response_review_handoff_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "handoff_status": handoff_status,
            "evidence_boundary": "software_proof_docker_field_evidence_real_material_response_review_handoff_gate",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "blocked_reason": "route_elevator_field_materials_missing",
            "next_required_evidence": missing,
            "missing_required_materials": missing if handoff_status == handoff.BACKFILL_HANDOFF else [],
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "source": "software_proof",
                "status": "not_proven",
                "handoff_status": handoff_status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "next_required_evidence": missing,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
        }
        if unsafe:
            payload["safe_copy"] = {**payload["safe_copy"], "operator_note": "delivery_success=true"}
        return payload

    def _build(self, root: Path, payload: dict[str, object], evidence_ref: str = "field-run-401") -> tuple[dict[str, object], dict[str, object]]:
        # 公共 helper 让 case 聚焦 escalation 映射和边界。
        path = self._write_json(root, "handoff.json", payload)
        artifact, summary, exit_code = escalation.build_field_evidence_real_material_followup_escalation_status(str(path), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_ready_handoff_maps_to_owner_sla_escalation_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, {"payload": {"field_evidence_real_material_response_review_handoff_summary": self._handoff_summary("field-run-401")}})

        self.assertEqual(artifact["schema"], "trashbot.field_evidence_real_material_followup_escalation_status.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_real_material_followup_escalation_status_summary.v1")
        self.assertEqual(artifact["capability"], "field_evidence_real_material_followup_escalation_status")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_real_material_followup_escalation_status_gate",
        )
        self.assertEqual(artifact["status"], "not_proven")
        self.assertEqual(
            artifact["field_evidence_real_material_followup_escalation_status"],
            "escalated_for_field_owner_followup_not_proven",
        )
        self.assertEqual(summary["owner_escalation_items"][0]["owner"], "autonomy-engineer")
        self.assertEqual(summary["owner_escalation_items"][0]["due_status"], "overdue_pending_real_route_elevator_field_materials")
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_backfill_handoff_preserves_missing_evidence_and_next_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._handoff_summary("field-run-402", handoff.BACKFILL_HANDOFF), "field-run-402")

        self.assertEqual(
            artifact["field_evidence_real_material_followup_escalation_status"],
            "blocked_missing_field_material_followup_escalation_not_proven",
        )
        encoded = json.dumps(summary, ensure_ascii=False)
        self.assertIn("real elevator door state", encoded)
        self.assertIn("real delivery result", encoded)
        self.assertIn("field_owners_supply_same_ref_real_materials", summary["next_action"])

    def test_robot_diagnostics_handoff_alias_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alias = {
                "latest_status": {
                    "diagnostics": {
                        "robot_diagnostics_field_evidence_real_material_response_review_handoff_summary": self._handoff_summary("field-run-403")
                    }
                }
            }
            artifact, summary = self._build(root, alias, "field-run-403")

        self.assertEqual(
            artifact["field_evidence_real_material_followup_escalation_status"],
            "escalated_for_field_owner_followup_not_proven",
        )
        self.assertEqual(summary["source_handoff"]["schema"], "trashbot.field_evidence_real_material_response_review_handoff_summary.v1")
        self.assertTrue(summary["same_evidence_ref_required"])

    def test_mismatch_unsupported_and_success_claims_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mismatch, _ = self._build(root, self._handoff_summary("field-run-404"), "other-run")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsupported, _ = self._build(root, {"schema": "trashbot.unsupported.v1", "evidence_ref": "field-run-405"}, "field-run-405")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe, unsafe_summary = self._build(root, self._handoff_summary("field-run-406", unsafe=True), "field-run-406")

        self.assertEqual(
            mismatch["field_evidence_real_material_followup_escalation_status"],
            "evidence_ref_mismatch_field_material_followup_escalation_blocked",
        )
        self.assertEqual(
            unsupported["field_evidence_real_material_followup_escalation_status"],
            "blocked_unsupported_field_material_followup_escalation_source",
        )
        self.assertEqual(
            unsafe["field_evidence_real_material_followup_escalation_status"],
            "blocked_rejected_or_unsafe_handoff_followup_escalation_not_proven",
        )
        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertIn("delivery_success=false", encoded)
        self.assertFalse(unsafe["delivery_success"])

    def test_missing_source_outputs_blocked_status_without_control_enablement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary, exit_code = escalation.build_field_evidence_real_material_followup_escalation_status(
                str(root / "missing.json"),
                "field-run-407",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            artifact["field_evidence_real_material_followup_escalation_status"],
            "blocked_unsupported_field_material_followup_escalation_source",
        )
        self.assertFalse(summary["safe_to_control"])
        self.assertIn("handoff_json_missing", artifact["blocked_reason"])

    def test_output_preserves_required_boundary_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._handoff_summary("field-run-408"), "field-run-408")

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_real_material_followup_escalation_status", encoded)
        self.assertIn("software_proof_docker_field_evidence_real_material_followup_escalation_status_gate", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", encoded)
        self.assertIn("3269642220", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Traceback", encoded)


if __name__ == "__main__":
    unittest.main()
