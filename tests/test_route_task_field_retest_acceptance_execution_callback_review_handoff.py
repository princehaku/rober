#!/usr/bin/env python3
"""route_task_field_retest_acceptance_execution_callback_review_handoff 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；验收入口显式加入该目录，保持 CLI 与 unittest 同源。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import route_task_field_retest_acceptance_execution_callback_review_handoff as gate  # noqa: E402


# 测试约束 01：fixture 只表达 review decision 摘要，不创建材料目录。
# 测试约束 02：ready case 只能证明 handoff metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：owner follow-up case 验证材料补证路径。
# 测试约束 07：callback rerun case 验证 unsupported source fail closed。
# 测试约束 08：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 09：mismatch case 验证 CLI evidence_ref 不能静默覆盖 source。
# 测试约束 10：unsafe case 验证 raw path 和 runtime topic 不进入 summary。
# 测试约束 11：success case 验证成功/动作声明映射为 blocked。
# 测试约束 12：fixture 不包含真实 Nav2 runtime log。
# 测试约束 13：fixture 不包含真实 route completion signal。
# 测试约束 14：fixture 不包含真实 task record 内容。
# 测试约束 15：fixture 不包含真实 elevator door state。
# 测试约束 16：fixture 不包含真实 target floor confirmation。
# 测试约束 17：fixture 不包含真实 human assistance note。
# 测试约束 18：fixture 不包含真实 dropoff/cancel completion。
# 测试约束 19：fixture 不包含真实 delivery result。
# 测试约束 20：单测只验证 PC gate，不访问 ROS graph 或硬件。
# 测试约束 21：单测不访问外部云、OSS/CDN、DB/queue 或 4G。
# 测试约束 22：单测使用 tempfile 只写 JSON fixture。
# 测试约束 23：所有断言围绕契约字段，不依赖生成时间。
# 测试约束 24：未来新增 handoff 状态必须补对应测试和文档。


class RouteTaskFieldRetestAcceptanceExecutionCallbackReviewHandoffTest(unittest.TestCase):
    def _decision_payload(
        self,
        evidence_ref: str = "ev-acceptance-handoff-001",
        review_decision: str = "ready_for_controlled_field_rerun",
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上游 decision 摘要，不包含真实材料目录或 raw artifact。
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_acceptance_execution_callback_review_decision_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate",
            "status": review_decision,
            "review_decision": review_decision,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "same_evidence_ref_match": {
                "status": "matched",
                "expected_evidence_ref": evidence_ref,
                "source_evidence_ref": evidence_ref,
            },
            "owner_handoff": {
                "owner": "Autonomy Algorithm Engineer",
                "action": "review_acceptance_execution_callback_before_handoff",
            },
            "next_required_evidence": ["Prepare sanitized acceptance execution callback review handoff."],
            "safe_copy": {
                "review_decision": review_decision,
                "status": review_decision,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
            },
            "not_proven": list(gate.NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def test_ready_handoff_summary_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decision.json"
            path.write_text(json.dumps(self._decision_payload()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_route_task_field_retest_acceptance_execution_callback_review_handoff(
                str(path),
                "ev-acceptance-handoff-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate",
        )
        self.assertEqual(artifact["handoff_status"], "ready_for_acceptance_execution_callback_review_handoff")
        self.assertTrue(summary["handoff_package"]["ready"])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_delivery_result", summary["not_proven"])

    def test_owner_follow_up_and_callback_rerun_states_are_mapped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            follow_up_path = root / "follow_up.json"
            rerun_path = root / "rerun.json"
            follow_up_path.write_text(
                json.dumps(self._decision_payload(review_decision="needs_material_backfill")),
                encoding="utf-8",
            )
            rerun_path.write_text(
                json.dumps(self._decision_payload(review_decision="unsupported_future_decision")),
                encoding="utf-8",
            )

            follow_up_artifact, follow_up_summary, _ = gate.build_route_task_field_retest_acceptance_execution_callback_review_handoff(
                str(follow_up_path),
                "ev-acceptance-handoff-001",
            )
            rerun_artifact, rerun_summary, _ = gate.build_route_task_field_retest_acceptance_execution_callback_review_handoff(
                str(rerun_path),
                "ev-acceptance-handoff-001",
            )

        self.assertEqual(follow_up_artifact["handoff_status"], "needs_owner_follow_up")
        self.assertTrue(follow_up_summary["safe_rerun_hint"]["required"])
        self.assertEqual(rerun_artifact["handoff_status"], "needs_acceptance_execution_callback_rerun")
        self.assertIn("unsupported_source_review_decision", ",".join(rerun_summary["status_reasons"]))

    def test_wrapper_and_nested_decision_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapper.json"
            path.write_text(
                json.dumps({"payload": {"route_task_field_retest_acceptance_execution_callback_review_decision_summary": self._decision_payload("ev-acceptance-handoff-002")}}),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_callback_review_handoff(str(path), "")

        self.assertEqual(artifact["handoff_status"], "ready_for_acceptance_execution_callback_review_handoff")
        self.assertEqual(summary["safe_evidence_ref"], "ev-acceptance-handoff-002")

    def test_ref_mismatch_and_unsupported_schema_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            ready_path.write_text(json.dumps(self._decision_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._decision_payload(schema="trashbot.other.v1")), encoding="utf-8")

            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_acceptance_execution_callback_review_handoff(
                str(ready_path),
                "other-ref",
            )
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_acceptance_execution_callback_review_handoff(
                str(bad_schema_path),
                "ev-acceptance-handoff-001",
            )

        self.assertEqual(mismatch_artifact["handoff_status"], "evidence_ref_mismatch_rerun")
        self.assertEqual(schema_artifact["handoff_status"], "needs_acceptance_execution_callback_rerun")

    def test_unsafe_copy_and_success_claim_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe_path.write_text(
                json.dumps(self._decision_payload(owner_handoff={"note": "raw path /Users/m4/private.log /cmd_vel"})),
                encoding="utf-8",
            )
            success_path.write_text(json.dumps(self._decision_payload(delivery_success=True)), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_acceptance_execution_callback_review_handoff(
                str(unsafe_path),
                "ev-acceptance-handoff-001",
            )
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_acceptance_execution_callback_review_handoff(
                str(success_path),
                "ev-acceptance-handoff-001",
            )

        self.assertEqual(unsafe_artifact["handoff_status"], "blocked_unsafe_review_handoff")
        self.assertEqual(success_artifact["handoff_status"], "blocked_unsafe_review_handoff")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("checksum", encoded_summary.lower())


if __name__ == "__main__":
    unittest.main()
