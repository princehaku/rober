#!/usr/bin/env python3
"""field evidence real material response review handoff gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_real_material_response_review_decision as decision  # noqa: E402
import field_evidence_real_material_response_review_handoff as handoff  # noqa: E402


# 测试约束 01：fixture 只表达 review-decision safe summary。
# 测试约束 02：ready handoff 仅表示 field-owner 可接手，不表示现场通过。
# 测试约束 03：missing/backfill 必须保留缺失材料列表。
# 测试约束 04：rejected/mixed/unsafe 必须 fail closed。
# 测试约束 05：blocked/missing source 映射真实环境或 source 不可用。
# 测试约束 06：Robot diagnostics safe alias 必须可消费。
# 测试约束 07：输出保持 source=software_proof、status=not_proven。
# 测试约束 08：输出保持 safe_to_control=false。
# 测试约束 09：输出保持 delivery_success=false。
# 测试约束 10：输出保持 primary_actions_enabled=false。
# 测试约束 11：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRealMaterialResponseReviewHandoffTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不模拟真实现场 runtime。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _decision_summary(
        self,
        evidence_ref: str,
        review_decision: str = decision.ACCEPTED_DECISION,
        unsafe: bool = False,
    ) -> dict[str, object]:
        # 样本沿用上一轮 review decision summary 的安全消费面。
        missing = ["elevator_door_floor_evidence", "true_phone_browser_evidence"] if review_decision == decision.BACKFILL_DECISION else []
        rejected = ["unsafe_response_copy"] if review_decision == decision.REJECTED_DECISION else []
        blocked = ["real_route_elevator_materials"] if review_decision == decision.BLOCKED_DECISION else []
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_real_material_response_review_decision_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "review_decision": review_decision,
            "evidence_boundary": "software_proof_docker_field_evidence_real_material_response_review_decision_gate",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "decision_reasons": ["fixture_reason"],
            "accepted_materials": ["safe_task_record"],
            "missing_materials": missing,
            "rejected_materials": rejected,
            "blocked_materials": blocked,
            "next_required_evidence": [{"owner": "field-owner", "materials": missing or blocked or rejected}],
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "source": "software_proof",
                "status": "not_proven",
                "review_decision": review_decision,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "missing_materials": missing,
                "rejected_materials": rejected,
                "blocked_materials": blocked,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
        }
        if unsafe:
            payload["safe_copy"] = {**payload["safe_copy"], "owner_note": "unsafe /cmd_vel token raw"}
        return payload

    def _build(self, root: Path, payload: dict[str, object], evidence_ref: str = "field-run-301") -> tuple[dict[str, object], dict[str, object]]:
        # 公共 helper 让 case 聚焦 handoff 映射和 fail-closed 规则。
        path = self._write_json(root, "review_decision.json", payload)
        artifact, summary, exit_code = handoff.build_field_evidence_real_material_response_review_handoff(str(path), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_accepted_review_decision_maps_to_field_owner_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(
                root,
                {"payload": {"field_evidence_real_material_response_review_decision_summary": self._decision_summary("field-run-301")}},
            )

        self.assertEqual(artifact["schema"], "trashbot.field_evidence_real_material_response_review_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_real_material_response_review_handoff_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_real_material_response_review_handoff_gate",
        )
        self.assertEqual(artifact["status"], "not_proven")
        self.assertEqual(artifact["handoff_status"], "ready_for_field_owner_handoff_not_proven")
        self.assertEqual(summary["field_owner_handoff"]["owner"], "field-owner")
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertIn("ready_for_field_owner_handoff_not_proven", json.dumps(artifact, ensure_ascii=False))

    def test_backfill_review_decision_preserves_missing_required_materials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._decision_summary("field-run-302", decision.BACKFILL_DECISION), "field-run-302")

        self.assertEqual(artifact["handoff_status"], "needs_material_backfill_handoff_not_proven")
        self.assertEqual(summary["missing_required_materials"], ["elevator_door_floor_evidence", "true_phone_browser_evidence"])
        self.assertIn("backfill_missing_required_materials", summary["field_owner_handoff"]["action"])

    def test_rejected_unsafe_mixed_and_success_claims_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rejected, _ = self._build(root, self._decision_summary("field-run-303", decision.REJECTED_DECISION), "field-run-303")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe, unsafe_summary = self._build(root, self._decision_summary("field-run-304", unsafe=True), "field-run-304")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mixed, _ = self._build(root, self._decision_summary("field-run-305"), "other-run")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            success_payload = self._decision_summary("field-run-306")
            success_payload["delivery_success"] = True
            success, _ = self._build(root, success_payload, "field-run-306")

        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertEqual(rejected["handoff_status"], "rejected_unsafe_or_mixed_handoff_not_proven")
        self.assertEqual(unsafe["handoff_status"], "rejected_unsafe_or_mixed_handoff_not_proven")
        self.assertEqual(mixed["handoff_status"], "rejected_unsafe_or_mixed_handoff_not_proven")
        self.assertEqual(success["handoff_status"], "rejected_unsafe_or_mixed_handoff_not_proven")
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("token", encoded.lower())
        self.assertFalse(success["delivery_success"])

    def test_blocked_missing_and_unsupported_source_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocked, blocked_summary = self._build(root, self._decision_summary("field-run-307", decision.BLOCKED_DECISION), "field-run-307")
            missing, missing_summary, _ = handoff.build_field_evidence_real_material_response_review_handoff(
                str(root / "missing.json"),
                "field-run-308",
            )
            unsupported, _ = self._build(
                root,
                {"schema": "trashbot.unsupported.v1", "evidence_ref": "field-run-309"},
                "field-run-309",
            )

        self.assertEqual(blocked["handoff_status"], "blocked_real_environment_unavailable_handoff_not_proven")
        self.assertEqual(missing["handoff_status"], "blocked_real_environment_unavailable_handoff_not_proven")
        self.assertEqual(unsupported["handoff_status"], "rejected_unsafe_or_mixed_handoff_not_proven")
        self.assertIn("real_route_elevator_materials", blocked_summary["next_required_evidence"])
        self.assertFalse(missing_summary["primary_actions_enabled"])

    def test_robot_diagnostics_safe_alias_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alias = {
                "latest_status": {
                    "diagnostics": {
                        "robot_diagnostics_field_evidence_real_material_response_review_decision_summary": self._decision_summary("field-run-310")
                    }
                }
            }
            artifact, summary = self._build(root, alias, "field-run-310")

        self.assertEqual(artifact["handoff_status"], "ready_for_field_owner_handoff_not_proven")
        self.assertEqual(summary["source_review_decision"]["schema_status"], "supported")
        self.assertTrue(summary["same_evidence_ref_required"])

    def test_output_preserves_required_boundary_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._decision_summary("field-run-311"), "field-run-311")

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("software_proof_docker_field_evidence_real_material_response_review_handoff_gate", encoded)
        self.assertIn("ready_for_field_owner_handoff_not_proven", encoded)
        self.assertIn("needs_material_backfill_handoff_not_proven", encoded)
        self.assertIn("rejected_unsafe_or_mixed_handoff_not_proven", encoded)
        self.assertIn("blocked_real_environment_unavailable_handoff_not_proven", encoded)
        self.assertIn("same_evidence_ref_required", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Traceback", encoded)


if __name__ == "__main__":
    unittest.main()
