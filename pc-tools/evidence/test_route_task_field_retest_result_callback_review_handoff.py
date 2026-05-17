#!/usr/bin/env python3
"""route_task_field_retest_result_callback_review_handoff 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_result_callback_review_handoff as gate  # noqa: E402


# 测试约束 01：fixture 只表达 result callback review decision，不创建材料目录。
# 测试约束 02：ready case 只能证明 result review handoff metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：owner follow-up case 验证缺材料决策必须跟进。
# 测试约束 07：rerun case 验证 callback rerun 决策必须保留。
# 测试约束 08：mismatch case 验证证据号不一致必须复跑。
# 测试约束 09：unsupported case 验证 schema 漂移必须 fail closed。
# 测试约束 10：missing decision case 验证缺主键不能 ready。
# 测试约束 11：unsafe case 验证 raw path 和 ROS topic 不进入 summary。
# 测试约束 12：success case 验证成功/动作声明映射为 unsafe handoff。
# 测试约束 13：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 14：weak same-ref case 验证字符串 true 不能通过。
# 测试约束 15：单测不访问 ROS graph、Nav2 runtime 或硬件。
# 测试约束 16：单测不访问 cloud、phone、serial/UART 或 WAVE ROVER。
# 测试约束 17：所有断言围绕契约字段，不依赖生成时间。
# 测试约束 18：未来新增 mapping 必须补对应测试和文档。
# 测试约束 19：ready 测试同时检查 artifact 和 summary schema。
# 测试约束 20：ready 测试确认 review_ready_package 只是 metadata ready。
# 测试约束 21：mapping 测试覆盖 owner follow-up、callback rerun、mismatch、unsafe。
# 测试约束 22：wrapper 测试确认只通过安全 wrapper key 取 source。
# 测试约束 23：mismatch 测试确认 CLI evidence_ref 不能静默覆盖 source。
# 测试约束 24：unsupported schema 测试确认 schema 漂移必须复跑。
# 测试约束 25：missing decision 测试确认缺所有主键才算缺 decision。
# 测试约束 26：weak same-ref 测试确认字符串 true 不能替代布尔 true。
# 测试约束 27：unsafe 测试确认 raw path 不进入 summary。
# 测试约束 28：unsafe 测试确认 ROS topic 不进入 summary。
# 测试约束 29：success 测试确认 delivery_success=true 被阻断。
# 测试约束 30：所有 fixture 都使用安全 evidence_ref，不使用本机路径。
# 测试约束 31：所有 fixture 都保持 delivery_success=false，除专门 unsafe case。
# 测试约束 32：所有 fixture 都保持 primary_actions_enabled=false。
# 测试约束 33：测试不写仓库文件，只在 tempfile 中写临时 JSON。
# 测试约束 34：测试不依赖命令行输出，直接调用 build 函数。
# 测试约束 35：测试名称描述 fail-closed 行为，方便后续定位回归。
# 测试约束 36：若新增 handoff_status，必须同步补文档和 rg literal。


class RouteTaskFieldRetestResultCallbackReviewHandoffTest(unittest.TestCase):
    def _review_decision_payload(
        self,
        decision: str = "ready_for_result_review",
        evidence_ref: str = "ev-review-handoff-001",
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上一轮 review decision 摘要，不包含真实材料或 raw artifact。
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_result_callback_review_decision_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_result_callback_review_decision_gate",
            "status": decision,
            "review_decision": decision,
            "evidence_ref": evidence_ref,
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_match": {
                "status": "matched",
                "expected_evidence_ref": evidence_ref,
                "callback_evidence_ref": evidence_ref,
            },
            "next_required_evidence": ["Prepare sanitized result review packet."],
            "owner_follow_up": [{"owner": "Autonomy Algorithm Engineer", "action": "review_callback_decision"}],
            "safe_copy": {
                "review_decision": decision,
                "safe_evidence_ref": evidence_ref,
                "not_proven": "not_proven",
            },
            "not_proven": list(gate.NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def test_ready_for_result_review_maps_to_ready_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review_decision.json"
            path.write_text(json.dumps(self._review_decision_payload()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_route_task_field_retest_result_callback_review_handoff(str(path), "ev-review-handoff-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_result_callback_review_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_result_callback_review_handoff_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate",
        )
        self.assertEqual(artifact["handoff_status"], "ready_for_result_review_handoff")
        self.assertTrue(summary["review_ready_package"]["ready"])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_delivery_success", summary["not_proven"])

    def test_source_decisions_map_to_handoff_statuses(self) -> None:
        cases = {
            "needs_material_backfill": "needs_owner_follow_up",
            "needs_callback_rerun": "needs_callback_rerun",
            "evidence_ref_mismatch_rerun": "evidence_ref_mismatch_rerun",
            "rejected_unsafe_callback": "blocked_unsafe_review_handoff",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for decision, expected_status in cases.items():
                path = root / f"{decision}.json"
                path.write_text(json.dumps(self._review_decision_payload(decision=decision)), encoding="utf-8")

                artifact, summary, _exit_code = gate.build_route_task_field_retest_result_callback_review_handoff(str(path), "ev-review-handoff-001")

                self.assertEqual(artifact["handoff_status"], expected_status)
                self.assertFalse(summary["review_ready_package"]["ready"])
                self.assertEqual(summary["rerun_package"]["required"], expected_status != "ready_for_result_review_handoff")

    def test_wrapper_and_nested_review_decision_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapper.json"
            path.write_text(
                json.dumps(
                    {
                        "payload": {
                            "route_task_field_retest_result_callback_review_decision_summary": self._review_decision_payload(
                                evidence_ref="ev-review-handoff-002",
                            )
                        }
                    }
                ),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_result_callback_review_handoff(str(path), "")

        self.assertEqual(artifact["handoff_status"], "ready_for_result_review_handoff")
        self.assertEqual(summary["safe_evidence_ref"], "ev-review-handoff-002")

    def test_ref_mismatch_unsupported_schema_missing_decision_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            missing_decision_path = root / "missing_decision.json"
            weak_same_ref_path = root / "weak_same_ref.json"
            ready_path.write_text(json.dumps(self._review_decision_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._review_decision_payload(schema="trashbot.other.v1")), encoding="utf-8")
            missing_decision = self._review_decision_payload()
            missing_decision.pop("review_decision")
            missing_decision.pop("status")
            missing_decision["safe_copy"] = {"safe_evidence_ref": "ev-review-handoff-001", "not_proven": "not_proven"}
            missing_decision_path.write_text(json.dumps(missing_decision), encoding="utf-8")
            weak_same_ref_path.write_text(
                json.dumps(self._review_decision_payload(same_evidence_ref_required="true")),
                encoding="utf-8",
            )

            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_result_callback_review_handoff(str(ready_path), "other-ref")
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_result_callback_review_handoff(str(bad_schema_path), "ev-review-handoff-001")
            missing_artifact, _missing_summary, _ = gate.build_route_task_field_retest_result_callback_review_handoff(str(missing_decision_path), "ev-review-handoff-001")
            weak_artifact, _weak_summary, _ = gate.build_route_task_field_retest_result_callback_review_handoff(str(weak_same_ref_path), "ev-review-handoff-001")

        self.assertEqual(mismatch_artifact["handoff_status"], "evidence_ref_mismatch_rerun")
        self.assertEqual(schema_artifact["handoff_status"], "needs_callback_rerun")
        self.assertEqual(missing_artifact["handoff_status"], "needs_callback_rerun")
        self.assertEqual(weak_artifact["handoff_status"], "evidence_ref_mismatch_rerun")

    def test_unsafe_review_and_success_claim_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe_path.write_text(
                json.dumps(self._review_decision_payload(owner_follow_up=[{"note": "raw path /Users/m4/private.log /cmd_vel"}])),
                encoding="utf-8",
            )
            success_path.write_text(json.dumps(self._review_decision_payload(delivery_success=True)), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_result_callback_review_handoff(str(unsafe_path), "ev-review-handoff-001")
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_result_callback_review_handoff(str(success_path), "ev-review-handoff-001")

        self.assertEqual(unsafe_artifact["handoff_status"], "blocked_unsafe_review_handoff")
        self.assertEqual(success_artifact["handoff_status"], "blocked_unsafe_review_handoff")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)


if __name__ == "__main__":
    unittest.main()
