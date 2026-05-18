#!/usr/bin/env python3
"""route_task_field_retest_acceptance_execution_callback_review_decision 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；验收入口显式加入该目录，保持 CLI 与 unittest 同源。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import route_task_field_retest_acceptance_execution_callback_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达 acceptance callback intake 摘要，不创建材料目录。
# 测试约束 02：ready case 只能证明 controlled field rerun metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：missing case 验证缺材料必须 material backfill。
# 测试约束 07：rejected case 验证拒收材料必须 material backfill。
# 测试约束 08：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 09：mismatch case 验证 CLI evidence_ref 不能静默覆盖 source。
# 测试约束 10：unsupported case 验证 schema 漂移必须 fail closed。
# 测试约束 11：unsafe case 验证 raw path 和 ROS topic 不进入 summary。
# 测试约束 12：success case 验证成功/动作声明映射为 rejected_unsafe_callback。
# 测试约束 13：fixture 不包含真实 Nav2 runtime log。
# 测试约束 14：fixture 不包含真实 route completion signal。
# 测试约束 15：fixture 不包含真实 task record 内容。
# 测试约束 16：fixture 不包含真实 elevator door state。
# 测试约束 17：fixture 不包含真实 target floor confirmation。
# 测试约束 18：fixture 不包含真实 human assistance note。
# 测试约束 19：fixture 不包含真实 dropoff/cancel completion。
# 测试约束 20：fixture 不包含真实 delivery result。
# 测试约束 21：单测只验证 PC gate，不访问 ROS graph 或硬件。
# 测试约束 22：单测不访问外部云、OSS/CDN、DB/queue 或 4G。
# 测试约束 23：单测使用 tempfile 只写 JSON fixture。
# 测试约束 24：所有断言围绕契约字段，不依赖生成时间。
# 测试约束 25：未来新增 decision 必须补对应测试和文档。


class RouteTaskFieldRetestAcceptanceExecutionCallbackReviewDecisionTest(unittest.TestCase):
    def _intake_payload(
        self,
        evidence_ref: str = "ev-acceptance-review-001",
        received: list[dict[str, object]] | None = None,
        missing: list[dict[str, object]] | None = None,
        rejected: list[dict[str, object]] | None = None,
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上游 intake 摘要，不包含真实材料目录或 raw artifact。
        received_materials = received if received is not None else [
            {"material": "nav2_or_fixed_route_runtime_log", "required": True, "safe_note": "sanitized callback noted"},
            {"material": "delivery_result", "required": True, "safe_note": "metadata callback noted"},
            {"material": "diagnostics_mobile_safe_summary", "required": True, "safe_note": "read-only summary noted"},
        ]
        missing_materials = list(missing or [])
        rejected_materials = list(rejected or [])
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_acceptance_execution_callback_intake_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate",
            "status": "ready_for_field_retest_acceptance_execution_callback_intake_not_proven",
            "callback_intake_status": "ready_for_field_retest_acceptance_execution_callback_intake_not_proven",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "evidence_ref_status": {
                "status": "matched",
                "expected_evidence_ref": evidence_ref,
                "source_execution_pack_evidence_ref": evidence_ref,
                "callback_packet_evidence_ref": evidence_ref,
            },
            "received_materials": received_materials,
            "missing_materials": missing_materials,
            "rejected_materials": rejected_materials,
            "owner_next_steps": [{"owner": "Product Manager / OKR Owner", "action": "review_callback_intake_summary_before_field_rerun_decision"}],
            "not_proven": list(gate.NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def test_ready_for_controlled_field_rerun_summary_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "intake.json"
            path.write_text(json.dumps(self._intake_payload()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_route_task_field_retest_acceptance_execution_callback_review_decision(
                str(path),
                "ev-acceptance-review-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_acceptance_execution_callback_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_acceptance_execution_callback_review_decision_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate",
        )
        self.assertEqual(artifact["review_decision"], "ready_for_controlled_field_rerun")
        self.assertTrue(summary["field_rerun_readiness"]["ready"])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_delivery_result", summary["not_proven"])

    def test_missing_materials_map_to_needs_material_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.json"
            path.write_text(
                json.dumps(self._intake_payload(missing=[{"material": "delivery_result", "reason": "callback_response_missing"}])),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_callback_review_decision(
                str(path),
                "ev-acceptance-review-001",
            )

        self.assertEqual(artifact["review_decision"], "needs_material_backfill")
        self.assertFalse(summary["field_rerun_readiness"]["ready"])
        self.assertIn("delivery_result", summary["safe_copy"]["missing_material_keys"])

    def test_rejected_materials_map_to_needs_material_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rejected.json"
            path.write_text(
                json.dumps(self._intake_payload(rejected=[{"material": "task_record", "reason": "not_in_execution_pack"}])),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_callback_review_decision(
                str(path),
                "ev-acceptance-review-001",
            )

        self.assertEqual(artifact["review_decision"], "needs_material_backfill")
        self.assertIn("task_record", summary["safe_copy"]["rejected_material_keys"])

    def test_wrapper_and_nested_intake_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapper.json"
            path.write_text(
                json.dumps({"payload": {"route_task_field_retest_acceptance_execution_callback_intake_summary": self._intake_payload("ev-acceptance-review-002")}}),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_callback_review_decision(str(path), "")

        self.assertEqual(artifact["review_decision"], "ready_for_controlled_field_rerun")
        self.assertEqual(summary["safe_evidence_ref"], "ev-acceptance-review-002")

    def test_ref_mismatch_and_unsupported_callback_schema_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            ready_path.write_text(json.dumps(self._intake_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._intake_payload(schema="trashbot.other.v1")), encoding="utf-8")

            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_acceptance_execution_callback_review_decision(
                str(ready_path),
                "other-ref",
            )
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_acceptance_execution_callback_review_decision(
                str(bad_schema_path),
                "ev-acceptance-review-001",
            )

        self.assertEqual(mismatch_artifact["review_decision"], "evidence_ref_mismatch_rerun")
        self.assertEqual(schema_artifact["review_decision"], "needs_material_backfill")

    def test_unsafe_callback_and_success_claim_are_rejected_unsafe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe_path.write_text(
                json.dumps(self._intake_payload(owner_next_steps=[{"note": "raw path /Users/m4/private.log /cmd_vel"}])),
                encoding="utf-8",
            )
            success_path.write_text(json.dumps(self._intake_payload(delivery_success=True)), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_acceptance_execution_callback_review_decision(
                str(unsafe_path),
                "ev-acceptance-review-001",
            )
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_acceptance_execution_callback_review_decision(
                str(success_path),
                "ev-acceptance-review-001",
            )

        self.assertEqual(unsafe_artifact["review_decision"], "rejected_unsafe_callback")
        self.assertEqual(success_artifact["review_decision"], "rejected_unsafe_callback")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)


if __name__ == "__main__":
    unittest.main()
