#!/usr/bin/env python3
"""route_task_field_retest_acceptance_execution_rerun_result_review_decision 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；验收入口显式加入该目录，保持 CLI 与 unittest 同源。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import route_task_field_retest_acceptance_execution_rerun_result_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达 result intake summary，不创建材料目录。
# 测试约束 02：ready case 只能证明 review decision metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：backfill case 覆盖缺 route completion signal。
# 测试约束 07：backfill case 覆盖缺 task record。
# 测试约束 08：backfill case 覆盖缺 Nav2/fixed-route runtime log。
# 测试约束 09：backfill case 覆盖缺 dropoff/cancel completion。
# 测试约束 10：backfill case 覆盖缺 delivery result。
# 测试约束 11：backfill case 覆盖缺 elevator door state。
# 测试约束 12：backfill case 覆盖缺 target floor confirmation。
# 测试约束 13：backfill case 覆盖缺 human assistance record。
# 测试约束 14：mismatch case 验证 CLI evidence_ref 不能静默覆盖 source。
# 测试约束 15：unsupported case 验证错误 schema 不被包装成 decision。
# 测试约束 16：unsafe case 验证 raw path、checksum 和 runtime topic 被阻断。
# 测试约束 17：success case 验证成功/动作声明映射为 blocked。
# 测试约束 18：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 19：单测不访问 ROS graph、硬件、外部云或手机运行时。
# 测试约束 20：所有断言围绕契约字段，不依赖生成时间。
# 测试约束 21：未来新增 review decision 状态必须补对应测试和文档。


class RouteTaskFieldRetestAcceptanceExecutionRerunResultReviewDecisionTest(unittest.TestCase):
    def _intake_payload(
        self,
        evidence_ref: str = "ev-acceptance-rerun-result-review-001",
        status: str = "ready_for_acceptance_execution_rerun_result_review_not_proven",
        categories: list[str] | None = None,
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上游 result intake 摘要，不包含真实材料内容或 raw artifact。
        material_categories = categories or list(gate.REQUIRED_RERUN_RESULT_MATERIALS)
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate",
            "status": status,
            "rerun_result_intake_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "rerun_result_packet": {
                "rerun_result_packet_status": "ready",
                "safe_evidence_ref": evidence_ref,
                "result_material_categories": material_categories,
                "operator_note": "safe packet ready for metadata-only review decision",
            },
            "owner_handoff": [
                {
                    "owner": "Autonomy Algorithm Engineer",
                    "action": "prepare_rerun_result_review",
                }
            ],
            "next_required_evidence": ["Review safe rerun result packet with the same evidence_ref."],
            "safe_copy": {
                "schema": "trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake_summary.v1.safe_copy",
                "source": "software_proof",
                "status": status,
                "rerun_result_intake_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": list(gate.NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def test_complete_safe_intake_is_ready_for_handoff_but_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rerun_result_intake.json"
            path.write_text(json.dumps(self._intake_payload()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_decision(
                str(path),
                "ev-acceptance-rerun-result-review-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            artifact["schema"],
            "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision.v1",
        )
        self.assertEqual(
            summary["schema"],
            "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary.v1",
        )
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate",
        )
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["decision_status"], "ready_for_acceptance_execution_rerun_result_handoff")
        self.assertTrue(summary["review_decision_package"]["ready"])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_route_elevator_field_pass", summary["not_proven"])

    def test_missing_materials_need_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "partial_intake.json"
            path.write_text(
                json.dumps(
                    self._intake_payload(
                        categories=[
                            "route_completion_signal",
                            "task_record",
                            "nav2_fixed_route_runtime_log",
                        ]
                    )
                ),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_decision(
                str(path),
                "ev-acceptance-rerun-result-review-001",
            )

        self.assertEqual(artifact["decision_status"], "needs_acceptance_execution_rerun_result_backfill")
        self.assertIn("dropoff_or_cancel_completion", summary["review_decision_package"]["missing_materials"])
        self.assertIn("delivery_result", summary["review_decision_package"]["missing_materials"])
        self.assertIn("elevator_door_state", summary["review_decision_package"]["missing_materials"])
        self.assertIn("target_floor_confirmation", summary["review_decision_package"]["missing_materials"])
        self.assertIn("human_assistance_record", summary["review_decision_package"]["missing_materials"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_not_ready_source_intake_needs_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "not_ready.json"
            path.write_text(
                json.dumps(self._intake_payload(status="needs_acceptance_execution_rerun_result_backfill")),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_decision(
                str(path),
                "ev-acceptance-rerun-result-review-001",
            )

        self.assertEqual(artifact["decision_status"], "needs_acceptance_execution_rerun_result_backfill")
        self.assertIn("source_rerun_result_intake_status:needs_acceptance_execution_rerun_result_backfill", ",".join(summary["status_reasons"]))

    def test_mismatch_and_unsupported_intake_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            ready_path.write_text(json.dumps(self._intake_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._intake_payload(schema="trashbot.other.v1")), encoding="utf-8")

            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_decision(
                str(ready_path),
                "other-ref",
            )
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_decision(
                str(bad_schema_path),
                "ev-acceptance-rerun-result-review-001",
            )

        self.assertEqual(mismatch_artifact["decision_status"], "evidence_ref_mismatch_rerun_result")
        self.assertEqual(schema_artifact["decision_status"], "blocked_unsupported_rerun_result_intake")

    def test_unsafe_copy_and_success_claim_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe = self._intake_payload()
            unsafe["rerun_result_packet"] = {
                "safe_evidence_ref": "ev-acceptance-rerun-result-review-001",
                "result_material_categories": list(gate.REQUIRED_RERUN_RESULT_MATERIALS),
                "operator_note": "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456",
            }
            success = self._intake_payload(delivery_success=True)
            unsafe_path.write_text(json.dumps(unsafe), encoding="utf-8")
            success_path.write_text(json.dumps(success), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_decision(
                str(unsafe_path),
                "ev-acceptance-rerun-result-review-001",
            )
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_decision(
                str(success_path),
                "ev-acceptance-rerun-result-review-001",
            )

        self.assertEqual(unsafe_artifact["decision_status"], "blocked_unsafe_rerun_result")
        self.assertEqual(success_artifact["decision_status"], "blocked_unsafe_rerun_result")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_and_nested_source_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapper.json"
            path.write_text(
                json.dumps(
                    {
                        "payload": {
                            "route_task_field_retest_acceptance_execution_rerun_result_intake_summary": self._intake_payload(
                                "ev-wrapper-rerun-result-review-001"
                            )
                        }
                    }
                ),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_decision(
                str(path),
                "",
            )

        self.assertEqual(artifact["decision_status"], "ready_for_acceptance_execution_rerun_result_handoff")
        self.assertEqual(summary["safe_evidence_ref"], "ev-wrapper-rerun-result-review-001")


if __name__ == "__main__":
    unittest.main()
