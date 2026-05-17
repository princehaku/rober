#!/usr/bin/env python3
"""route_task_field_retest_result_review_intake 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_result_review_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达 result callback review handoff，不创建材料目录。
# 测试约束 02：ready case 只能证明 result review intake metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：owner follow-up case 验证缺材料决策必须跟进。
# 测试约束 07：rerun case 验证 callback rerun 决策必须保留。
# 测试约束 08：mismatch case 验证证据号不一致必须复跑。
# 测试约束 09：unsupported case 验证 schema 漂移必须 fail closed。
# 测试约束 10：missing decision case 验证缺主键不能 ready。
# 测试约束 11：unsafe case 验证 raw path 和 ROS topic 不进入 summary。
# 测试约束 12：success case 验证成功/动作声明映射为 unsafe intake。
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
# 测试约束 36：若新增 intake_status，必须同步补文档和 rg literal。


class RouteTaskFieldRetestResultReviewIntakeTest(unittest.TestCase):
    def _handoff_payload(
        self,
        handoff_status: str = "ready_for_result_review_handoff",
        evidence_ref: str = "ev-review-intake-001",
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上一轮 handoff 摘要，不包含真实材料或 raw artifact。
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_result_callback_review_handoff_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate",
            "status": handoff_status,
            "handoff_status": handoff_status,
            "evidence_ref": evidence_ref,
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_match": {
                "status": "matched",
                "expected_evidence_ref": evidence_ref,
                "handoff_evidence_ref": evidence_ref,
            },
            "review_ready_package": {
                "ready": handoff_status == "ready_for_result_review_handoff",
                "status": handoff_status,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "next_required_evidence": ["Prepare metadata-only result review intake."],
            "owner_follow_up": [{"owner": "Autonomy Algorithm Engineer", "action": "register_intake"}],
            "safe_copy": {
                "handoff_status": handoff_status,
                "safe_evidence_ref": evidence_ref,
                "not_proven": "not_proven",
            },
            "not_proven": list(gate.NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def test_ready_handoff_maps_to_ready_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.json"
            path.write_text(json.dumps(self._handoff_payload()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_route_task_field_retest_result_review_intake(str(path), "ev-review-intake-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_result_review_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_result_review_intake_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_result_review_intake_gate",
        )
        self.assertEqual(artifact["intake_status"], "ready_for_result_review_intake")
        self.assertTrue(summary["result_review_intake_package"]["ready"])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_delivery_success", summary["not_proven"])

    def test_source_handoff_statuses_map_to_intake_statuses(self) -> None:
        cases = {
            "needs_owner_follow_up": "needs_owner_follow_up",
            "needs_callback_rerun": "needs_handoff_rerun",
            "evidence_ref_mismatch_rerun": "evidence_ref_mismatch_rerun",
            "blocked_unsafe_review_handoff": "blocked_unsafe_review_intake",
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for handoff_status, expected_status in cases.items():
                path = root / f"{handoff_status}.json"
                path.write_text(json.dumps(self._handoff_payload(handoff_status=handoff_status)), encoding="utf-8")

                artifact, summary, _exit_code = gate.build_route_task_field_retest_result_review_intake(str(path), "ev-review-intake-001")

                self.assertEqual(artifact["intake_status"], expected_status)
                self.assertFalse(summary["result_review_intake_package"]["ready"])
                self.assertEqual(summary["rerun_package"]["required"], expected_status != "ready_for_result_review_intake")

    def test_wrapper_and_nested_handoff_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapper.json"
            path.write_text(
                json.dumps(
                    {
                        "payload": {
                            "route_task_field_retest_result_callback_review_handoff_summary": self._handoff_payload(
                                evidence_ref="ev-review-intake-002",
                            )
                        }
                    }
                ),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_result_review_intake(str(path), "")

        self.assertEqual(artifact["intake_status"], "ready_for_result_review_intake")
        self.assertEqual(summary["safe_evidence_ref"], "ev-review-intake-002")

    def test_ref_mismatch_unsupported_schema_missing_status_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            missing_status_path = root / "missing_status.json"
            weak_same_ref_path = root / "weak_same_ref.json"
            ready_path.write_text(json.dumps(self._handoff_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._handoff_payload(schema="trashbot.other.v1")), encoding="utf-8")
            missing_status = self._handoff_payload()
            missing_status.pop("handoff_status")
            missing_status.pop("status")
            missing_status["safe_copy"] = {"safe_evidence_ref": "ev-review-intake-001", "not_proven": "not_proven"}
            missing_status_path.write_text(json.dumps(missing_status), encoding="utf-8")
            weak_same_ref_path.write_text(
                json.dumps(self._handoff_payload(same_evidence_ref_required="true")),
                encoding="utf-8",
            )

            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_result_review_intake(str(ready_path), "other-ref")
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_result_review_intake(str(bad_schema_path), "ev-review-intake-001")
            missing_artifact, _missing_summary, _ = gate.build_route_task_field_retest_result_review_intake(str(missing_status_path), "ev-review-intake-001")
            weak_artifact, _weak_summary, _ = gate.build_route_task_field_retest_result_review_intake(str(weak_same_ref_path), "ev-review-intake-001")

        self.assertEqual(mismatch_artifact["intake_status"], "evidence_ref_mismatch_rerun")
        self.assertEqual(schema_artifact["intake_status"], "needs_handoff_rerun")
        self.assertEqual(missing_artifact["intake_status"], "needs_handoff_rerun")
        self.assertEqual(weak_artifact["intake_status"], "evidence_ref_mismatch_rerun")

    def test_unsafe_review_and_success_claim_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe_path.write_text(
                json.dumps(self._handoff_payload(owner_follow_up=[{"note": "raw path /Users/m4/private.log /cmd_vel"}])),
                encoding="utf-8",
            )
            success_path.write_text(json.dumps(self._handoff_payload(delivery_success=True)), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_result_review_intake(str(unsafe_path), "ev-review-intake-001")
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_result_review_intake(str(success_path), "ev-review-intake-001")

        self.assertEqual(unsafe_artifact["intake_status"], "blocked_unsafe_review_intake")
        self.assertEqual(success_artifact["intake_status"], "blocked_unsafe_review_intake")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)


if __name__ == "__main__":
    unittest.main()
