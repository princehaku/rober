#!/usr/bin/env python3
"""route_task_field_retest_acceptance_execution_rerun_result_intake 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；验收入口显式加入该目录，保持 CLI 与 unittest 同源。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import route_task_field_retest_acceptance_execution_rerun_result_intake as gate  # noqa: E402


# 测试约束 01：fixture 只表达 rerun queue 和 safe result packet，不创建材料目录。
# 测试约束 02：ready case 只能证明 result-review intake metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：missing result case 验证缺 result packet 时 fail closed。
# 测试约束 07：backfill case 验证上游 rerun queue 未 queued 时不进入 review。
# 测试约束 08：unsupported case 验证错误 schema 不被包装成 intake。
# 测试约束 09：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 10：mismatch case 验证 CLI/result evidence_ref 不能静默覆盖 source。
# 测试约束 11：unsafe case 验证 raw path、checksum 和 runtime topic 不进入 summary。
# 测试约束 12：success case 验证成功/动作声明映射为 blocked。
# 测试约束 13：fixture 不包含真实 Nav2 runtime log。
# 测试约束 14：fixture 不包含真实 route completion signal。
# 测试约束 15：fixture 不包含真实 task record 内容。
# 测试约束 16：fixture 不包含真实 elevator door state。
# 测试约束 17：fixture 不包含真实 target floor confirmation。
# 测试约束 18：fixture 不包含真实 human assistance note。
# 测试约束 19：fixture 不包含真实 dropoff/cancel completion。
# 测试约束 20：单测只验证 PC gate，不访问 ROS graph 或硬件。
# 测试约束 21：单测不访问外部云、OSS/CDN、DB/queue 或 4G。
# 测试约束 22：单测使用 tempfile 只写 JSON fixture。
# 测试约束 23：所有断言围绕契约字段，不依赖生成时间。
# 测试约束 24：未来新增 rerun result intake 状态必须补对应测试和文档。


class RouteTaskFieldRetestAcceptanceExecutionRerunResultIntakeTest(unittest.TestCase):
    def _rerun_queue_payload(
        self,
        evidence_ref: str = "ev-acceptance-rerun-result-001",
        status: str = "queued_for_controlled_field_rerun_not_proven",
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上游 rerun queue 摘要，不包含真实材料目录或 raw artifact。
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate",
            "status": status,
            "rerun_queue_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "owner_handoff": [
                {
                    "owner": "Autonomy Algorithm Engineer",
                    "action": "hold_queue_until_real_controlled_field_materials_arrive",
                }
            ],
            "next_required_evidence": ["Collect safe rerun result packet with the same evidence_ref."],
            "safe_copy": {
                "rerun_queue_status": status,
                "status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
            },
            "not_proven": list(gate.NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _result_packet(self, evidence_ref: str = "ev-acceptance-rerun-result-001", **extra: object) -> dict[str, object]:
        # result packet 只表达 owner-safe 类别摘要，不表达 route/elevator field pass。
        payload: dict[str, object] = {
            "owner": "field_owner",
            "rerun_result_packet_status": "submitted",
            "safe_evidence_ref": evidence_ref,
            "result_material_categories": [
                "nav2_fixed_route_runtime_log",
                "route_completion_signal",
                "task_record",
                "delivery_result",
            ],
            "operator_note": "safe packet received for later human review only",
        }
        payload.update(extra)
        return payload

    def test_safe_result_packet_is_ready_for_review_but_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue_path = root / "rerun_queue.json"
            result_path = root / "rerun_result.json"
            queue_path.write_text(json.dumps(self._rerun_queue_payload()), encoding="utf-8")
            result_path.write_text(json.dumps(self._result_packet()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_result_intake(
                str(queue_path),
                str(result_path),
                "ev-acceptance-rerun-result-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate",
        )
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["rerun_result_intake_status"], "ready_for_acceptance_execution_rerun_result_review_not_proven")
        self.assertEqual(summary["rerun_result_packet"]["rerun_result_packet_status"], "ready")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_acceptance_execution_rerun_result", summary["not_proven"])

    def test_missing_result_packet_needs_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rerun_queue.json"
            path.write_text(json.dumps(self._rerun_queue_payload()), encoding="utf-8")

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_result_intake(
                str(path),
                "",
                "ev-acceptance-rerun-result-001",
            )

        self.assertEqual(artifact["rerun_result_intake_status"], "needs_acceptance_execution_rerun_result_backfill")
        self.assertIn("rerun_result_packet_missing_or_unbound", ",".join(summary["status_reasons"]))
        self.assertFalse(summary["primary_actions_enabled"])

    def test_backfill_when_source_rerun_queue_is_not_queued(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue_path = root / "rerun_queue.json"
            result_path = root / "rerun_result.json"
            queue_path.write_text(
                json.dumps(self._rerun_queue_payload(status="needs_acceptance_execution_rerun_queue_backfill")),
                encoding="utf-8",
            )
            result_path.write_text(json.dumps(self._result_packet()), encoding="utf-8")

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_result_intake(
                str(queue_path),
                str(result_path),
                "ev-acceptance-rerun-result-001",
            )

        self.assertEqual(artifact["rerun_result_intake_status"], "needs_acceptance_execution_rerun_result_backfill")
        self.assertIn("source_rerun_queue_status:needs_acceptance_execution_rerun_queue_backfill", ",".join(summary["status_reasons"]))

    def test_mismatch_and_unsupported_queue_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            result_path = root / "result.json"
            ready_path.write_text(json.dumps(self._rerun_queue_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._rerun_queue_payload(schema="trashbot.other.v1")), encoding="utf-8")
            result_path.write_text(json.dumps(self._result_packet()), encoding="utf-8")

            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_intake(
                str(ready_path),
                str(result_path),
                "other-ref",
            )
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_intake(
                str(bad_schema_path),
                str(result_path),
                "ev-acceptance-rerun-result-001",
            )

        self.assertEqual(mismatch_artifact["rerun_result_intake_status"], "evidence_ref_mismatch_rerun_result")
        self.assertEqual(schema_artifact["rerun_result_intake_status"], "blocked_unsupported_rerun_queue")

    def test_unsafe_copy_and_success_claim_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue_path = root / "rerun_queue.json"
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            queue_path.write_text(json.dumps(self._rerun_queue_payload()), encoding="utf-8")
            unsafe_path.write_text(
                json.dumps(self._result_packet(operator_note="raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456")),
                encoding="utf-8",
            )
            success_path.write_text(json.dumps(self._result_packet(delivery_success=True)), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_intake(
                str(queue_path),
                str(unsafe_path),
                "ev-acceptance-rerun-result-001",
            )
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_result_intake(
                str(queue_path),
                str(success_path),
                "ev-acceptance-rerun-result-001",
            )

        self.assertEqual(unsafe_artifact["rerun_result_intake_status"], "blocked_unsafe_rerun_result")
        self.assertEqual(success_artifact["rerun_result_intake_status"], "blocked_unsafe_rerun_result")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_and_nested_source_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue_path = root / "wrapper.json"
            result_path = root / "result_wrapper.json"
            queue_path.write_text(
                json.dumps({"payload": {"route_task_field_retest_acceptance_execution_rerun_queue_summary": self._rerun_queue_payload("ev-wrapper-result-001")}}),
                encoding="utf-8",
            )
            result_path.write_text(
                json.dumps({"data": {"safe_rerun_result_packet": self._result_packet("ev-wrapper-result-001")}}),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_result_intake(
                str(queue_path),
                str(result_path),
                "",
            )

        self.assertEqual(artifact["rerun_result_intake_status"], "ready_for_acceptance_execution_rerun_result_review_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-wrapper-result-001")


if __name__ == "__main__":
    unittest.main()
