#!/usr/bin/env python3
"""route_task_field_retest_callback_review_decision 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_callback_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达 callback intake summary，不创建材料目录。
# 测试约束 02：ready case 只能证明 result intake metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：missing case 验证缺 delivery_result 时必须 backfill。
# 测试约束 07：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 08：mismatch case 验证 CLI evidence_ref 不能静默覆盖 source。
# 测试约束 09：unsupported case 验证 schema 漂移必须 fail closed。
# 测试约束 10：unsafe case 验证 raw path 和 ROS topic 不进入 summary。
# 测试约束 11：success case 验证成功/动作声明独立映射为 blocked_success_claim。
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
# 测试约束 23：测试中的 evidence_ref 是安全短引用。
# 测试约束 24：所有断言围绕契约字段，不依赖生成时间。
# 测试约束 25：未来新增 decision 必须补对应测试和文档。


class RouteTaskFieldRetestCallbackReviewDecisionTest(unittest.TestCase):
    def _intake_payload(self, evidence_ref: str = "ev-review-001", missing: list[str] | None = None, **extra: object) -> dict[str, object]:
        # fixture 只表达 callback intake 摘要，不包含真实材料目录或 raw artifact。
        missing = list(missing or [])
        received = [
            f"field_retest_packet/{evidence_ref}/{name}.json"
            for name in gate.REQUIRED_EVIDENCE_PACKET
            if name not in missing
        ]
        missing_files = [
            f"field_retest_packet/{evidence_ref}/{name}.json"
            for name in gate.REQUIRED_EVIDENCE_PACKET
            if name in missing
        ]
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_callback_intake_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_callback_intake_gate",
            "status": "ready_for_field_retest_callback_intake_not_proven",
            "intake_status": "ready_for_field_retest_callback_intake_not_proven",
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "received_filenames_summary": {
                "recommended_count": len(gate.REQUIRED_EVIDENCE_PACKET),
                "received_count": len(received),
                "missing_count": len(missing_files),
                "received_filenames": received,
                "missing_filenames": missing_files,
                "unexpected_filenames": [],
                "all_recommended_received": not missing,
            },
            "missing_materials": missing,
            "same_evidence_ref_match": {
                "status": "matched",
                "expected_evidence_ref": evidence_ref,
                "callback_evidence_ref": evidence_ref,
            },
            "next_backfill_action": "send_sanitized_material_summary_to_result_intake",
            "owner_handoff": {"handoff_status": "owner_review_required_not_proven"},
            "not_proven": list(gate.NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def test_ready_for_result_intake_summary_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "intake.json"
            path.write_text(json.dumps(self._intake_payload()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_route_task_field_retest_callback_review_decision(str(path), "ev-review-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_callback_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_callback_review_decision_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_callback_review_decision_gate",
        )
        self.assertEqual(artifact["review_decision"], "ready_for_result_intake")
        self.assertTrue(summary["result_intake_readiness"]["ready"])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("delivery_result", summary["required_evidence_packet"])

    def test_missing_materials_map_to_needs_material_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.json"
            path.write_text(json.dumps(self._intake_payload(missing=["delivery_result"])), encoding="utf-8")

            artifact, summary, _exit_code = gate.build_route_task_field_retest_callback_review_decision(str(path), "ev-review-001")

        self.assertEqual(artifact["review_decision"], "needs_material_backfill")
        self.assertFalse(summary["result_intake_readiness"]["ready"])
        self.assertIn("delivery_result", summary["missing_materials"])

    def test_wrapper_and_nested_intake_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapper.json"
            path.write_text(
                json.dumps({"payload": {"route_task_field_retest_callback_intake_summary": self._intake_payload("ev-review-002")}}),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_callback_review_decision(str(path), "")

        self.assertEqual(artifact["review_decision"], "ready_for_result_intake")
        self.assertEqual(summary["evidence_ref"], "ev-review-002")

    def test_ref_mismatch_and_unsupported_callback_schema_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            ready_path.write_text(json.dumps(self._intake_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._intake_payload(schema="trashbot.other.v1")), encoding="utf-8")

            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_callback_review_decision(
                str(ready_path),
                "other-ref",
            )
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_callback_review_decision(
                str(bad_schema_path),
                "ev-review-001",
            )

        self.assertEqual(mismatch_artifact["review_decision"], "evidence_ref_mismatch_rerun")
        self.assertEqual(schema_artifact["review_decision"], "unsupported_callback_schema")

    def test_unsafe_callback_and_success_claim_are_separate_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe_path.write_text(
                json.dumps(self._intake_payload(owner_handoff={"note": "raw path /Users/m4/private.log /cmd_vel"})),
                encoding="utf-8",
            )
            success_path.write_text(json.dumps(self._intake_payload(delivery_success=True)), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_callback_review_decision(str(unsafe_path), "ev-review-001")
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_callback_review_decision(str(success_path), "ev-review-001")

        self.assertEqual(unsafe_artifact["review_decision"], "blocked_unsafe_callback")
        self.assertEqual(success_artifact["review_decision"], "blocked_success_claim")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)


if __name__ == "__main__":
    unittest.main()
