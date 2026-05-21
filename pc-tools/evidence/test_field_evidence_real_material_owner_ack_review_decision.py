#!/usr/bin/env python3
"""field evidence real material owner ack review decision gate 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools/evidence 不是 package；测试显式加入目录以复用 CLI 模块。
EVIDENCE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_real_material_owner_ack_intake as intake  # noqa: E402
import field_evidence_real_material_owner_ack_review_decision as decision  # noqa: E402


# 测试约束 01：fixture 只表达 owner-ack-intake safe summary。
# 测试约束 02：accepted decision 仅表示 structured review，不表示现场通过。
# 测试约束 03：缺 owner-ack-intake source 时必须 rejected。
# 测试约束 04：missing/blocked material 映射 needs_more_evidence。
# 测试约束 05：rejected/mixed/unsafe 映射 rejected，不允许降级。
# 测试约束 06：Robot diagnostics safe alias 必须可消费。
# 测试约束 07：输出保持 source=software_proof、status=not_proven。
# 测试约束 08：输出保持 safe_to_control=false。
# 测试约束 09：输出保持 delivery_success=false。
# 测试约束 10：输出保持 primary_actions_enabled=false。
# 测试约束 11：三值 decision enum 必须稳定。
# 测试约束 12：单测不访问 ROS graph、硬件、外部云或手机 runtime。


class FieldEvidenceRealMaterialOwnerAckReviewDecisionTest(unittest.TestCase):
    def _write_json(self, root: Path, name: str, payload: object) -> Path:
        # 临时 JSON 只服务离线围栏，不模拟真实现场 runtime。
        path = root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def _intake_summary(
        self,
        evidence_ref: str,
        categories: dict[str, list[str]] | None = None,
        status: str = intake.READY_STATUS,
        unsafe: bool = False,
    ) -> dict[str, object]:
        # 样本沿用上一轮 owner-ack-intake summary 的安全消费面。
        categories = categories or {
            "accepted": list(intake.REQUIRED_CATEGORIES),
            "missing": [],
            "rejected": [],
            "blocked": [],
        }
        payload: dict[str, object] = {
            "schema": "trashbot.field_evidence_real_material_owner_ack_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "status": "not_proven",
            "capability": "field_evidence_real_material_owner_ack_intake",
            "owner_ack_intake_status": status,
            "field_evidence_real_material_owner_ack_intake_status": status,
            "evidence_boundary": "software_proof_docker_field_evidence_real_material_owner_ack_intake_gate",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "material_categories": categories,
            "not_proven": ["not_proven"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_copy": {
                "schema": "trashbot.field_evidence_real_material_owner_ack_intake_summary.v1.safe_copy",
                "source": "software_proof",
                "status": "not_proven",
                "owner_ack_intake_status": status,
                "field_evidence_real_material_owner_ack_intake_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "material_categories": categories,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
        }
        if unsafe:
            payload["safe_copy"] = {**payload["safe_copy"], "operator_note": "delivery_success=true"}
        return payload

    def _build(self, root: Path, payload: dict[str, object], evidence_ref: str = "field-run-601") -> tuple[dict[str, object], dict[str, object]]:
        # 公共 helper 让 case 聚焦 decision 映射和 fail-closed 规则。
        path = self._write_json(root, "owner_ack_intake.json", payload)
        artifact, summary, exit_code = decision.build_field_evidence_real_material_owner_ack_review_decision(str(path), evidence_ref)
        self.assertEqual(exit_code, 0)
        return artifact, summary

    def test_all_accepted_categories_map_to_accepted_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(
                root,
                {"payload": {"field_evidence_real_material_owner_ack_intake_summary": self._intake_summary("field-run-601")}},
            )

        self.assertEqual(artifact["schema"], "trashbot.field_evidence_real_material_owner_ack_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_real_material_owner_ack_review_decision_summary.v1")
        self.assertEqual(artifact["capability"], "field_evidence_real_material_owner_ack_review_decision")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_field_evidence_real_material_owner_ack_review_decision_gate",
        )
        self.assertEqual(artifact["review_decision"], "accepted")
        self.assertEqual(summary["material_category_counts"]["accepted"], len(intake.REQUIRED_CATEGORIES))
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["safe_copy"]["delivery_success"])
        self.assertIn("accepted_owner_ack_review_decision_not_field_pass", json.dumps(artifact, ensure_ascii=False))

    def test_missing_or_blocked_categories_require_more_evidence(self) -> None:
        categories = {
            "accepted": ["route_elevator_runtime_materials"],
            "missing": ["elevator_door_floor_materials"],
            "rejected": [],
            "blocked": ["diagnostics_mobile_safe_summary_materials"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._intake_summary("field-run-602", categories), "field-run-602")

        self.assertEqual(artifact["review_decision"], "needs_more_evidence")
        self.assertEqual(summary["owner_handoff"]["owner"], "field-owner")
        self.assertEqual(summary["material_category_counts"]["missing"], 1)
        self.assertEqual(summary["material_category_counts"]["blocked"], 1)
        self.assertIn("backfill_missing_or_blocked_owner_ack_categories", json.dumps(summary, ensure_ascii=False))

    def test_rejected_unsafe_mixed_and_success_claims_fail_closed(self) -> None:
        rejected_categories = {
            "accepted": ["route_elevator_runtime_materials"],
            "missing": [],
            "rejected": ["dropoff_cancel_delivery_result_materials"],
            "blocked": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rejected, _ = self._build(root, self._intake_summary("field-run-603", rejected_categories), "field-run-603")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe, unsafe_summary = self._build(root, self._intake_summary("field-run-604", unsafe=True), "field-run-604")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mixed, _ = self._build(root, self._intake_summary("field-run-605"), "other-run")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            success_payload = self._intake_summary("field-run-606")
            success_payload["delivery_success"] = True
            success_claim, _ = self._build(root, success_payload, "field-run-606")

        encoded = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertEqual(rejected["review_decision"], "rejected")
        self.assertEqual(unsafe["review_decision"], "rejected")
        self.assertEqual(mixed["review_decision"], "rejected")
        self.assertEqual(success_claim["review_decision"], "rejected")
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("token", encoded.lower())
        self.assertFalse(success_claim["delivery_success"])

    def test_missing_bad_and_unsupported_source_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing, missing_summary, _ = decision.build_field_evidence_real_material_owner_ack_review_decision(
                str(root / "missing.json"),
                "field-run-607",
            )
            unsupported, _ = self._build(
                root,
                {"schema": "trashbot.unsupported.v1", "evidence_ref": "field-run-607"},
                "field-run-607",
            )

        self.assertEqual(missing["review_decision"], "rejected")
        self.assertEqual(unsupported["review_decision"], "rejected")
        self.assertFalse(missing_summary["primary_actions_enabled"])
        self.assertIn("owner_ack_intake_json_missing", missing["decision_reasons"])

    def test_robot_diagnostics_safe_alias_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alias = {
                "latest_status": {
                    "diagnostics": {
                        "robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary": self._intake_summary("field-run-608")
                    }
                }
            }
            artifact, summary = self._build(root, alias, "field-run-608")

        self.assertEqual(artifact["review_decision"], "accepted")
        self.assertEqual(summary["source_owner_ack_intake"]["schema_status"], "supported")
        self.assertTrue(summary["same_evidence_ref_required"])

    def test_output_preserves_required_boundary_literals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact, summary = self._build(root, self._intake_summary("field-run-609"), "field-run-609")

        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        self.assertIn("field_evidence_real_material_owner_ack_review_decision", encoded)
        self.assertIn("software_proof_docker_field_evidence_real_material_owner_ack_review_decision_gate", encoded)
        self.assertIn("accepted", encoded)
        self.assertIn("needs_more_evidence", encoded)
        self.assertIn("rejected", encoded)
        self.assertIn("source=software_proof", encoded)
        self.assertIn("not_proven", encoded)
        self.assertIn("delivery_success=false", encoded)
        self.assertIn("primary_actions_enabled=false", encoded)
        self.assertIn("safe_to_control=false", encoded)
        self.assertNotIn("/dev/ttyUSB", encoded)
        self.assertNotIn("Traceback", encoded)


if __name__ == "__main__":
    unittest.main()
