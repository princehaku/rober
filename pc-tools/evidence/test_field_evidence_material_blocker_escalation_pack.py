#!/usr/bin/env python3
"""field evidence material blocker escalation pack gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_material_blocker_escalation_pack as pack  # noqa: E402
import field_evidence_real_material_followup_escalation_status as followup  # noqa: E402
import field_evidence_real_material_owner_ack_review_decision as owner_ack  # noqa: E402


# 测试约束 01：fixture 只表达 safe summary，不模拟 raw 现场材料。
# 测试约束 02：ready pack 仅表示可升级 owner，不表示现场通过。
# 测试约束 03：缺失/unsupported source 必须 fail closed。
# 测试约束 04：success/control claim 必须 fail closed。
# 测试约束 05：evidence_ref mismatch 必须 fail closed。
# 测试约束 06：输出保持 source=software_proof、status=not_proven。
# 测试约束 07：输出保持 safe_to_control=false。
# 测试约束 08：输出保持 delivery_success=false。
# 测试约束 09：输出保持 primary_actions_enabled=false。
# 测试约束 10：测试不访问 ROS graph、Nav2、硬件、云或手机 runtime。


class FieldEvidenceMaterialBlockerEscalationPackTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不代表真实现场文件。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _owner_ack_summary(self, evidence_ref: str) -> dict[str, object]:
        # 样本沿用 owner ack review decision summary 的安全消费面。
        return {
            "schema": owner_ack.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": "field_evidence_real_material_owner_ack_review_decision",
            "review_decision": "needs_more_evidence",
            "decision_status": "blocked_missing_field_materials_not_proven",
            "evidence_boundary": owner_ack.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "next_required_evidence": ["real field task record", "real route completion signal"],
            "blocked_reason": "owner_ack_review_still_missing_real_route_elevator_materials",
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "schema": f"{owner_ack.SUMMARY_SCHEMA}.safe_copy",
                "source": "software_proof",
                "status": "not_proven",
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "next_required_evidence": ["real field task record"],
                "blocked_reason": "owner_ack_review_still_missing_real_route_elevator_materials",
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
        }

    def _followup_summary(self, evidence_ref: str) -> dict[str, object]:
        # followup summary 代表上一轮升级状态，仍是 not_proven。
        return {
            "schema": followup.SUMMARY_SCHEMA,
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": "field_evidence_real_material_followup_escalation_status",
            "followup_status": "escalated_for_field_owner_followup_not_proven",
            "evidence_boundary": followup.EVIDENCE_BOUNDARY,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "next_required_evidence": ["real Nav2/fixed-route runtime log", "real dropoff completion material"],
            "blocked_reason": "field_owner_followup_overdue_pending_real_materials",
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "source": "software_proof",
                "status": "not_proven",
                "safe_evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "blocked_reason": "field_owner_followup_overdue_pending_real_materials",
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
        }

    def _build(self, root: Path, payload: dict[str, object], evidence_ref: str) -> tuple[dict[str, object], dict[str, object]]:
        # 公共 helper 让 case 聚焦安全边界和字段映射。
        path = self._write_json(root, "source.json", payload)
        artifact, summary, exit_code = pack.build_field_evidence_material_blocker_escalation_pack(str(path), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_owner_ack_review_summary_generates_escalation_pack_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, {"payload": self._owner_ack_summary("field-run-701")}, "field-run-701")

        self.assertEqual(artifact["schema"], pack.SCHEMA)
        self.assertEqual(summary["schema"], pack.SUMMARY_SCHEMA)
        self.assertEqual(artifact["field_evidence_material_blocker_escalation_pack_status"], pack.READY_STATUS)
        self.assertEqual(artifact["evidence_boundary"], pack.EVIDENCE_BOUNDARY)
        self.assertEqual(artifact["target_owner"], "Product Manager / OKR Owner")
        self.assertIn("real field task record", artifact["next_required_evidence"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["field_safe_copy"]["delivery_success"])

    def test_followup_summary_maps_to_overdue_owner_escalation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, {"latest_status": {"summary": self._followup_summary("field-run-702")}}, "field-run-702")

        self.assertEqual(artifact["field_evidence_material_blocker_escalation_pack_status"], pack.READY_STATUS)
        self.assertEqual(artifact["target_owner"], "field-owner + Product Manager / OKR Owner")
        self.assertIn("owner_followup_overdue", artifact["owner_escalation_level"])
        self.assertIn("real Nav2/fixed-route runtime log", summary["next_required_evidence"])
        self.assertEqual(summary["review_refs"]["pr5_thread_id"], pack.PR5_REVIEW_THREAD_ID)

    def test_missing_unsupported_unsafe_and_ref_mismatch_fail_closed_exit_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing, _, missing_code = pack.build_field_evidence_material_blocker_escalation_pack(str(root / "missing.json"), "field-run-703")
            unsupported, _ = self._build(root, {"schema": "trashbot.unsupported.v1", "evidence_ref": "field-run-703"}, "field-run-703")
            unsafe_payload = self._owner_ack_summary("field-run-704")
            unsafe_payload["safe_copy"]["operator_note"] = "delivery_success=true"
            unsafe, _ = self._build(root, unsafe_payload, "field-run-704")
            mismatch, _ = self._build(root, self._owner_ack_summary("field-run-705"), "other-run")

        self.assertEqual(missing_code, 0)
        self.assertEqual(missing["field_evidence_material_blocker_escalation_pack_status"], pack.MISSING_STATUS)
        self.assertEqual(unsupported["field_evidence_material_blocker_escalation_pack_status"], pack.UNSUPPORTED_STATUS)
        self.assertEqual(unsafe["field_evidence_material_blocker_escalation_pack_status"], pack.UNSAFE_STATUS)
        self.assertEqual(mismatch["field_evidence_material_blocker_escalation_pack_status"], pack.MISMATCH_STATUS)
        self.assertFalse(unsafe["safe_to_control"])
        self.assertFalse(unsafe["delivery_success"])

    def test_output_preserves_required_boundary_literals_and_safe_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._owner_ack_summary("field-run-706"), "field-run-706")

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_material_blocker_escalation_pack", encoded)
        self.assertIn("software_proof_docker_field_evidence_material_blocker_escalation_pack_gate", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertIn("next_required_evidence", encoded)
        self.assertIn("owner_escalation_level", encoded)
        self.assertIn("blocked_reason", encoded)
        self.assertIn("target_owner", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Traceback", encoded)


if __name__ == "__main__":
    unittest.main()
