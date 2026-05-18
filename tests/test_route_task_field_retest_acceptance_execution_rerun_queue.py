#!/usr/bin/env python3
"""route_task_field_retest_acceptance_execution_rerun_queue 的围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；验收入口显式加入该目录，保持 CLI 与 unittest 同源。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import route_task_field_retest_acceptance_execution_rerun_queue as gate  # noqa: E402


# 测试约束 01：fixture 只表达 handoff intake 和 queue request，不创建材料目录。
# 测试约束 02：queued case 只能证明受控复跑队列 metadata readiness。
# 测试约束 03：queued case 仍必须保留 delivery_success=false。
# 测试约束 04：queued case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：queued case 仍必须保留 not_proven。
# 测试约束 06：missing ack case 验证 owner ack 缺失时 fail closed。
# 测试约束 07：backfill case 验证上游 handoff intake 未 ready 时不排队。
# 测试约束 08：unsupported case 验证错误 schema 不被包装成队列。
# 测试约束 09：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 10：mismatch case 验证 CLI/request evidence_ref 不能静默覆盖 source。
# 测试约束 11：unsafe case 验证 raw path 和 runtime topic 不进入 summary。
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
# 测试约束 24：未来新增 rerun queue 状态必须补对应测试和文档。


class RouteTaskFieldRetestAcceptanceExecutionRerunQueueTest(unittest.TestCase):
    def _handoff_intake_payload(
        self,
        evidence_ref: str = "ev-acceptance-rerun-queue-001",
        status: str = "ready_for_controlled_field_rerun_queue",
        ack_state: str = "acknowledged",
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上游 handoff intake 摘要，不包含真实材料目录或 raw artifact。
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_acceptance_execution_handoff_intake_summary.v1",
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate",
            "status": status,
            "handoff_intake_status": status,
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "owner_acknowledgement_state": ack_state,
            "owner_handoff": [
                {
                    "owner": "Autonomy Algorithm Engineer",
                    "action": "queue_controlled_field_rerun_only_after_real_materials",
                }
            ],
            "next_required_evidence": ["Queue owner-safe rerun request before real controlled field materials arrive."],
            "safe_copy": {
                "handoff_intake_status": status,
                "status": status,
                "safe_evidence_ref": evidence_ref,
                "evidence_ref": evidence_ref,
                "owner_acknowledgement_state": ack_state,
            },
            "not_proven": list(gate.NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def _queue_request(self, evidence_ref: str = "ev-acceptance-rerun-queue-001", **extra: object) -> dict[str, object]:
        # queue request 只表达排队请求，不表达 route/elevator field pass。
        payload: dict[str, object] = {
            "owner": "field_owner",
            "owner_ack": True,
            "owner_acknowledgement_state": "acknowledged",
            "safe_evidence_ref": evidence_ref,
            "requested_rerun_reason": "controlled rerun requested after handoff intake review",
            "next_required_evidence": ["Collect real field material bundle with the same evidence_ref."],
        }
        payload.update(extra)
        return payload

    def test_ready_handoff_intake_is_queued_but_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = root / "handoff_intake.json"
            request_path = root / "queue_request.json"
            handoff_path.write_text(json.dumps(self._handoff_intake_payload()), encoding="utf-8")
            request_path.write_text(json.dumps(self._queue_request()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_queue(
                str(handoff_path),
                str(request_path),
                "ev-acceptance-rerun-queue-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate",
        )
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["rerun_queue_status"], "queued_for_controlled_field_rerun_not_proven")
        self.assertEqual(summary["owner_acknowledgement_state"], "acknowledged")
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_controlled_field_rerun_execution", summary["not_proven"])

    def test_missing_owner_ack_needs_owner_ack_before_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff_intake.json"
            path.write_text(
                json.dumps(self._handoff_intake_payload(ack_state="missing")),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_queue(
                str(path),
                "",
                "ev-acceptance-rerun-queue-001",
            )

        self.assertEqual(artifact["rerun_queue_status"], "needs_owner_ack_before_queue")
        self.assertEqual(summary["owner_acknowledgement_state"], "missing")
        self.assertIn("owner_acknowledgement_missing_before_queue", ",".join(summary["status_reasons"]))

    def test_backfill_when_source_handoff_intake_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = root / "handoff_intake.json"
            request_path = root / "queue_request.json"
            handoff_path.write_text(
                json.dumps(self._handoff_intake_payload(status="needs_acceptance_execution_handoff_backfill")),
                encoding="utf-8",
            )
            request_path.write_text(json.dumps(self._queue_request()), encoding="utf-8")

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_queue(
                str(handoff_path),
                str(request_path),
                "ev-acceptance-rerun-queue-001",
            )

        self.assertEqual(artifact["rerun_queue_status"], "needs_acceptance_execution_rerun_queue_backfill")
        self.assertIn("source_handoff_intake_status:needs_acceptance_execution_handoff_backfill", ",".join(summary["status_reasons"]))

    def test_mismatch_and_unsupported_schema_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            request_path = root / "request.json"
            ready_path.write_text(json.dumps(self._handoff_intake_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._handoff_intake_payload(schema="trashbot.other.v1")), encoding="utf-8")
            request_path.write_text(json.dumps(self._queue_request()), encoding="utf-8")

            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_queue(
                str(ready_path),
                str(request_path),
                "other-ref",
            )
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_queue(
                str(bad_schema_path),
                str(request_path),
                "ev-acceptance-rerun-queue-001",
            )

        self.assertEqual(mismatch_artifact["rerun_queue_status"], "evidence_ref_mismatch_rerun_queue")
        self.assertEqual(schema_artifact["rerun_queue_status"], "blocked_unsupported_handoff_intake")

    def test_unsafe_copy_and_success_claim_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            request_path = root / "request.json"
            unsafe_path.write_text(
                json.dumps(self._handoff_intake_payload(owner_handoff={"note": "raw path /Users/m4/private.log /cmd_vel"})),
                encoding="utf-8",
            )
            success_path.write_text(json.dumps(self._handoff_intake_payload(delivery_success=True)), encoding="utf-8")
            request_path.write_text(json.dumps(self._queue_request()), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_queue(
                str(unsafe_path),
                str(request_path),
                "ev-acceptance-rerun-queue-001",
            )
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_acceptance_execution_rerun_queue(
                str(success_path),
                str(request_path),
                "ev-acceptance-rerun-queue-001",
            )

        self.assertEqual(unsafe_artifact["rerun_queue_status"], "blocked_unsafe_rerun_queue")
        self.assertEqual(success_artifact["rerun_queue_status"], "blocked_unsafe_rerun_queue")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("checksum", encoded_summary.lower())

    def test_wrapper_and_nested_source_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff_path = root / "wrapper.json"
            request_path = root / "request_wrapper.json"
            handoff_path.write_text(
                json.dumps({"payload": {"route_task_field_retest_acceptance_execution_handoff_intake_summary": self._handoff_intake_payload("ev-wrapper-queue-001")}}),
                encoding="utf-8",
            )
            request_path.write_text(
                json.dumps({"data": {"queue_request": self._queue_request("ev-wrapper-queue-001")}}),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_acceptance_execution_rerun_queue(
                str(handoff_path),
                str(request_path),
                "",
            )

        self.assertEqual(artifact["rerun_queue_status"], "queued_for_controlled_field_rerun_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-wrapper-queue-001")


if __name__ == "__main__":
    unittest.main()
