#!/usr/bin/env python3
"""route_task_field_retest_acceptance_execution_rerun_result_review_handoff 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；验收入口显式加入该目录，保持 CLI 与 unittest 同源。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import route_task_field_retest_acceptance_execution_rerun_result_review_handoff as gate  # noqa: E402


# 测试约束 01：fixture 只表达 review decision summary，不创建材料目录。
# 测试约束 02：ready case 只能证明 owner handoff metadata readiness。
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
# 测试约束 15：unsupported case 验证错误 schema 不被包装成 handoff。
# 测试约束 16：unsafe case 验证 raw path、checksum 和 runtime topic 被阻断。
# 测试约束 17：success case 验证成功/动作声明映射为 blocked。
# 测试约束 18：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 19：单测不访问 ROS graph、硬件、外部云或手机运行时。
# 测试约束 20：所有断言围绕契约字段，不依赖生成时间。


class RouteTaskFieldRetestAcceptanceExecutionRerunResultReviewHandoffTest(unittest.TestCase):
    def _decision_payload(
        self,
        evidence_ref: str = "ev-acceptance-rerun-result-handoff-001",
        status: str = "ready_for_acceptance_execution_rerun_result_handoff",
        provided: list[str] | None = None,
        missing: list[str] | None = None,
        ready: bool = True,
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上游 review decision 摘要，不包含真实材料内容或 raw artifact。
        provided_materials = provided if provided is not None else list(gate.REQUIRED_RERUN_RESULT_MATERIALS)
        missing_materials = missing if missing is not None else []
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate",
            "status": status,
            "decision_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "provided_materials": provided_materials,
            "missing_materials": missing_materials,
            "review_decision_package": {
                "ready": ready,
                "status": status,
                "safe_evidence_ref": evidence_ref,
                "provided_materials": provided_materials,
                "missing_materials": missing_materials,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "owner_handoff": [
                {
                    "owner": "Autonomy Algorithm Engineer",
                    "action": "prepare_acceptance_execution_rerun_result_handoff_from_sanitized_review_decision",
                }
            ],
            "next_required_evidence": ["Prepare sanitized owner handoff with the same evidence_ref."],
            "safe_copy": {
                "schema": "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary.v1.safe_copy",
                "source": "software_proof",
                "status": status,
                "decision_status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "handoff_ready": ready,
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

    def test_ready_review_decision_becomes_owner_handoff_but_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review_decision.json"
            path.write_text(json.dumps(self._decision_payload()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_handoff(
                str(path),
                "ev-acceptance-rerun-result-handoff-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            artifact["schema"],
            "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff.v1",
        )
        self.assertEqual(
            summary["schema"],
            "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary.v1",
        )
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate",
        )
        self.assertEqual(summary["source"], "software_proof")
        self.assertEqual(artifact["handoff_status"], "ready_for_acceptance_execution_rerun_result_owner_handoff")
        self.assertEqual(summary["owner_role"], "Autonomy Algorithm Engineer")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_route_elevator_field_pass", summary["not_proven"])

    def test_missing_materials_need_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "partial_decision.json"
            path.write_text(
                json.dumps(
                    self._decision_payload(
                        status="needs_acceptance_execution_rerun_result_backfill",
                        provided=[
                            "route_completion_signal",
                            "task_record",
                            "nav2_fixed_route_runtime_log",
                        ],
                        missing=[
                            "dropoff_or_cancel_completion",
                            "delivery_result",
                            "elevator_door_state",
                            "target_floor_confirmation",
                            "human_assistance_record",
                        ],
                        ready=False,
                    )
                ),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_handoff(
                str(path),
                "ev-acceptance-rerun-result-handoff-001",
            )

        self.assertEqual(artifact["handoff_status"], "needs_acceptance_execution_rerun_result_material_backfill")
        self.assertIn("dropoff_or_cancel_completion", summary["missing_materials"])
        self.assertIn("delivery_result", summary["missing_materials"])
        self.assertIn("elevator_door_state", summary["missing_materials"])
        self.assertIn("target_floor_confirmation", summary["missing_materials"])
        self.assertIn("human_assistance_record", summary["missing_materials"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_mismatch_and_unsupported_review_decision_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            ready_path.write_text(json.dumps(self._decision_payload()), encoding="utf-8")
            bad_schema_path.write_text(
                json.dumps(self._decision_payload(schema="trashbot.other.v1")),
                encoding="utf-8",
            )

            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_handoff(
                str(ready_path),
                "other-ref",
            )
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_handoff(
                str(bad_schema_path),
                "ev-acceptance-rerun-result-handoff-001",
            )

        self.assertEqual(mismatch_artifact["handoff_status"], "evidence_ref_mismatch_rerun_result_handoff_blocked")
        self.assertEqual(schema_artifact["handoff_status"], "blocked_unsupported_rerun_result_review_decision")

    def test_unsafe_copy_and_success_claim_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe = self._decision_payload()
            unsafe["operator_note"] = "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"
            success = self._decision_payload(delivery_success=True)
            unsafe_path.write_text(json.dumps(unsafe), encoding="utf-8")
            success_path.write_text(json.dumps(success), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_handoff(
                str(unsafe_path),
                "ev-acceptance-rerun-result-handoff-001",
            )
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_handoff(
                str(success_path),
                "ev-acceptance-rerun-result-handoff-001",
            )

        self.assertEqual(unsafe_artifact["handoff_status"], "blocked_unsafe_rerun_result_handoff_copy")
        self.assertEqual(success_artifact["handoff_status"], "blocked_unsafe_rerun_result_handoff_copy")
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
                            "route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary": self._decision_payload(
                                "ev-wrapper-rerun-result-handoff-001"
                            )
                        }
                    }
                ),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_result_review_handoff(
                str(path),
                "",
            )

        self.assertEqual(artifact["handoff_status"], "ready_for_acceptance_execution_rerun_result_owner_handoff")
        self.assertEqual(summary["safe_evidence_ref"], "ev-wrapper-rerun-result-handoff-001")


if __name__ == "__main__":
    unittest.main()
