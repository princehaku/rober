#!/usr/bin/env python3
"""route_task_field_retest_result_review_decision 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_result_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达 result review intake，不创建材料目录。
# 测试约束 02：ready case 只能证明 acceptance backfill metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：缺材料 case 验证 route/elevator result materials 必须回填。
# 测试约束 07：缺输入 case 验证没有 intake 不能静默 ready。
# 测试约束 08：mismatch case 验证证据号不一致必须复跑。
# 测试约束 09：unsupported case 验证 schema 或 boundary 漂移必须 fail closed。
# 测试约束 10：weak same-ref case 验证字符串 true 不能通过。
# 测试约束 11：unsafe case 验证 raw path 和 ROS topic 不进入 summary。
# 测试约束 12：success case 验证成功/动作声明映射为 unsupported fail closed。
# 测试约束 13：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 14：单测不访问 ROS graph、Nav2 runtime 或硬件。
# 测试约束 15：单测不访问 cloud、phone、serial/UART 或 WAVE ROVER。
# 测试约束 16：所有断言围绕契约字段，不依赖生成时间。
# 测试约束 17：未来新增 decision_status，必须同步补文档和测试。
# 测试约束 18：ready 测试同时检查 artifact 和 summary schema。
# 测试约束 19：ready 测试确认 result_review_decision_package 只是 metadata ready。
# 测试约束 20：mapping 测试覆盖材料缺口、缺输入、unsupported 和 mismatch。
# 测试约束 21：wrapper 测试确认只通过安全 wrapper key 取 source。
# 测试约束 22：mismatch 测试确认 CLI evidence_ref 不能静默覆盖 source。
# 测试约束 23：unsupported schema 测试确认 schema 漂移必须复跑。
# 测试约束 24：weak same-ref 测试确认字符串 true 不能替代布尔 true。
# 测试约束 25：unsafe 测试确认 raw path 不进入 summary。
# 测试约束 26：unsafe 测试确认 ROS topic 不进入 summary。
# 测试约束 27：success 测试确认 delivery_success=true 被阻断。
# 测试约束 28：所有 fixture 都使用安全 evidence_ref，不使用本机路径。
# 测试约束 29：所有 fixture 都保持 delivery_success=false，除专门 unsafe case。
# 测试约束 30：所有 fixture 都保持 primary_actions_enabled=false。
# 测试约束 31：测试不写仓库文件，只在 tempfile 中写临时 JSON。
# 测试约束 32：测试不依赖命令行输出，直接调用 build 函数。
# 测试约束 33：测试名称描述 fail-closed 行为，方便后续定位回归。
# 测试约束 34：材料完整 fixture 仍不代表真实现场通过。
# 测试约束 35：材料缺口 fixture 默认包含全部 required result materials。
# 测试约束 36：rg literal 覆盖 not_proven、delivery_success=false 和 action disabled。


class RouteTaskFieldRetestResultReviewDecisionTest(unittest.TestCase):
    def _intake_payload(
        self,
        intake_status: str = "ready_for_result_review_intake",
        evidence_ref: str = "ev-review-decision-001",
        accepted_materials: list[str] | None = None,
        missing_materials: list[str] | None = None,
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上一轮 intake 摘要，不包含真实材料正文或 raw artifact。
        accepted = list(accepted_materials or [])
        missing = list(missing_materials if missing_materials is not None else [])
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_result_review_intake_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_result_review_intake_gate",
            "status": intake_status,
            "intake_status": intake_status,
            "evidence_ref": evidence_ref,
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_match": {
                "status": "matched",
                "expected_evidence_ref": evidence_ref,
                "intake_evidence_ref": evidence_ref,
            },
            "result_review_intake_package": {
                "ready": intake_status == "ready_for_result_review_intake",
                "status": intake_status,
                "accepted_materials": accepted,
                "missing_materials": missing,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "result_materials": {
                "accepted_materials": accepted,
                "missing_materials": missing,
                "rejected_materials": [],
            },
            "next_required_evidence": ["Prepare metadata-only result review decision."],
            "owner_follow_up": [{"owner": "Autonomy Algorithm Engineer", "action": "register_decision"}],
            "safe_copy": {
                "intake_status": intake_status,
                "result_review_intake_ready": intake_status == "ready_for_result_review_intake",
                "safe_evidence_ref": evidence_ref,
                "not_proven": "not_proven",
            },
            "not_proven": list(gate.NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def test_complete_intake_maps_to_ready_for_acceptance_backfill_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "intake.json"
            path.write_text(
                json.dumps(self._intake_payload(accepted_materials=list(gate.REQUIRED_RESULT_MATERIALS))),
                encoding="utf-8",
            )

            artifact, summary, exit_code = gate.build_route_task_field_retest_result_review_decision(str(path), "ev-review-decision-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_result_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_result_review_decision_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_result_review_decision_gate",
        )
        self.assertEqual(artifact["decision_status"], "ready_for_result_acceptance_backfill_not_proven")
        self.assertTrue(summary["result_review_decision_package"]["ready"])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_delivery_success", summary["not_proven"])

    def test_missing_materials_and_not_ready_intake_map_to_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_path = root / "missing.json"
            not_ready_path = root / "not_ready.json"
            missing_path.write_text(json.dumps(self._intake_payload()), encoding="utf-8")
            not_ready_path.write_text(
                json.dumps(self._intake_payload(intake_status="needs_owner_follow_up")),
                encoding="utf-8",
            )

            missing_artifact, missing_summary, _ = gate.build_route_task_field_retest_result_review_decision(str(missing_path), "ev-review-decision-001")
            not_ready_artifact, _not_ready_summary, _ = gate.build_route_task_field_retest_result_review_decision(str(not_ready_path), "ev-review-decision-001")

        self.assertEqual(missing_artifact["decision_status"], "needs_route_elevator_material_backfill_not_proven")
        self.assertIn("elevator_door_state", missing_summary["result_review_decision_package"]["missing_materials"])
        self.assertEqual(not_ready_artifact["decision_status"], "needs_route_elevator_material_backfill_not_proven")

    def test_wrapper_and_nested_intake_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapper.json"
            path.write_text(
                json.dumps(
                    {
                        "payload": {
                            "route_task_field_retest_result_review_intake_summary": self._intake_payload(
                                evidence_ref="ev-review-decision-002",
                                accepted_materials=list(gate.REQUIRED_RESULT_MATERIALS),
                            )
                        }
                    }
                ),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_result_review_decision(str(path), "")

        self.assertEqual(artifact["decision_status"], "ready_for_result_acceptance_backfill_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-review-decision-002")

    def test_missing_unsupported_mismatch_and_weak_same_ref_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            weak_same_ref_path = root / "weak_same_ref.json"
            ready_path.write_text(
                json.dumps(self._intake_payload(accepted_materials=list(gate.REQUIRED_RESULT_MATERIALS))),
                encoding="utf-8",
            )
            bad_schema_path.write_text(
                json.dumps(self._intake_payload(schema="trashbot.other.v1")),
                encoding="utf-8",
            )
            weak_same_ref_path.write_text(
                json.dumps(self._intake_payload(same_evidence_ref_required="true")),
                encoding="utf-8",
            )

            missing_artifact, _missing_summary, _ = gate.build_route_task_field_retest_result_review_decision(str(root / "missing.json"), "ev-review-decision-001")
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_result_review_decision(str(bad_schema_path), "ev-review-decision-001")
            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_result_review_decision(str(ready_path), "other-ref")
            weak_artifact, _weak_summary, _ = gate.build_route_task_field_retest_result_review_decision(str(weak_same_ref_path), "ev-review-decision-001")

        self.assertEqual(missing_artifact["decision_status"], "blocked_missing_result_review_intake_not_proven")
        self.assertEqual(schema_artifact["decision_status"], "unsupported_result_review_intake_schema_not_proven")
        self.assertEqual(mismatch_artifact["decision_status"], "evidence_ref_mismatch_rerun_not_proven")
        self.assertEqual(weak_artifact["decision_status"], "evidence_ref_mismatch_rerun_not_proven")

    def test_unsafe_review_and_success_claim_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe_path.write_text(
                json.dumps(self._intake_payload(owner_follow_up=[{"note": "raw path /Users/m4/private.log /cmd_vel"}])),
                encoding="utf-8",
            )
            success_path.write_text(
                json.dumps(self._intake_payload(delivery_success=True)),
                encoding="utf-8",
            )

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_result_review_decision(str(unsafe_path), "ev-review-decision-001")
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_result_review_decision(str(success_path), "ev-review-decision-001")

        self.assertEqual(unsafe_artifact["decision_status"], "unsupported_result_review_intake_schema_not_proven")
        self.assertEqual(success_artifact["decision_status"], "unsupported_result_review_intake_schema_not_proven")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)


if __name__ == "__main__":
    unittest.main()
