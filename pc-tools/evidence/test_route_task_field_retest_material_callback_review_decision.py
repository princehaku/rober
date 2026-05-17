#!/usr/bin/env python3
"""route_task_field_retest_material_callback_review_decision 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_material_callback_review_decision as gate  # noqa: E402


# 测试约束 01：fixture 只表达 material callback packet，不创建材料目录。
# 测试约束 02：ready case 只能证明 review decision metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：missing case 验证缺 material callback 时必须 backfill。
# 测试约束 07：pending ack case 验证 owner 未确认时不能 ready。
# 测试约束 08：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 09：mismatch case 验证 CLI evidence_ref 不能静默覆盖 source。
# 测试约束 10：unsupported case 验证 schema 漂移必须 fail closed。
# 测试约束 11：unsafe case 验证 raw path 和 ROS topic 不进入 summary。
# 测试约束 12：success case 验证成功/动作声明独立映射为 unsafe success。
# 测试约束 13：fixture 不包含真实 Nav2 runtime log。
# 测试约束 14：fixture 不包含真实 route completion signal。
# 测试约束 15：fixture 不包含真实 task record 内容。
# 测试约束 16：fixture 不包含真实 dropoff/cancel completion。
# 测试约束 17：fixture 不包含真实 delivery result。
# 测试约束 18：单测只验证 PC gate，不访问 ROS graph 或硬件。
# 测试约束 19：单测不访问外部云、OSS/CDN、DB/queue 或 4G。
# 测试约束 20：单测使用 tempfile 只写 JSON fixture。
# 测试约束 21：测试中的 evidence_ref 是安全短引用。
# 测试约束 22：所有断言围绕契约字段，不依赖生成时间。
# 测试约束 23：未来新增 decision 必须补对应测试和文档。


class RouteTaskFieldRetestMaterialCallbackReviewDecisionTest(unittest.TestCase):
    def _packet_payload(
        self,
        evidence_ref: str = "ev-material-review-001",
        accepted: list[str] | None = None,
        missing: list[str] | None = None,
        rejected: list[str] | None = None,
        ack: dict[str, object] | None = None,
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达 packet 摘要，不包含真实材料目录或 raw artifact。
        accepted = list(accepted if accepted is not None else gate.FIELD_CALLBACK_MATERIALS)
        missing = list(missing or [])
        rejected = list(rejected or [])
        items = [
            {
                "material": material,
                "safe_evidence_ref": evidence_ref,
                "accepted": material in accepted,
                "callback_status": "accepted_not_proven" if material in accepted else "pending_owner_callback",
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            for material in gate.FIELD_CALLBACK_MATERIALS
        ]
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_material_callback_packet_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_material_callback_packet_gate",
            "status": "ready_for_field_material_callback_not_proven",
            "callback_packet_status": "ready_for_field_material_callback_not_proven",
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "field_callback_items": items,
            "accepted_materials": accepted,
            "missing_materials": missing,
            "rejected_materials": rejected,
            "owner_acknowledgement": ack
            if ack is not None
            else {
                "owner_id": "autonomy-engineer",
                "material_callback_status": "material_callback_received_not_proven",
                "safe_note": "sanitized callback packet ready for review",
                "review_requested_at": "2026-05-18T00:00:00Z",
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

    def test_ready_review_decision_summary_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "packet.json"
            path.write_text(json.dumps(self._packet_payload()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_route_task_field_retest_material_callback_review_decision(
                str(path),
                "ev-material-review-001",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_material_callback_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_material_callback_review_decision_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_route_task_field_retest_material_callback_review_decision_gate",
        )
        self.assertEqual(artifact["review_decision"], "ready_for_controlled_field_rerun_not_proven")
        self.assertEqual(summary["material_callback_review_summary"]["accepted_count"], len(gate.FIELD_CALLBACK_MATERIALS))
        self.assertTrue(summary["material_callback_review_summary"]["owner_acknowledgement_ok"])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_nav2_fixed_route_runtime", summary["not_proven"])

    def test_missing_rejected_and_pending_ack_map_to_backfill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing_path = root / "missing.json"
            rejected_path = root / "rejected.json"
            pending_path = root / "pending.json"
            accepted_without_result = [name for name in gate.FIELD_CALLBACK_MATERIALS if name != "delivery_result"]
            missing_path.write_text(
                json.dumps(self._packet_payload(accepted=accepted_without_result, missing=["delivery_result"])),
                encoding="utf-8",
            )
            rejected_path.write_text(
                json.dumps(self._packet_payload(rejected=["task_record"])),
                encoding="utf-8",
            )
            pending_path.write_text(
                json.dumps(
                    self._packet_payload(
                        ack={"acknowledgement_status": "pending_owner_acknowledgement", "delivery_success": False, "primary_actions_enabled": False}
                    )
                ),
                encoding="utf-8",
            )

            missing_artifact, missing_summary, _ = gate.build_route_task_field_retest_material_callback_review_decision(str(missing_path), "ev-material-review-001")
            rejected_artifact, _rejected_summary, _ = gate.build_route_task_field_retest_material_callback_review_decision(str(rejected_path), "ev-material-review-001")
            pending_artifact, pending_summary, _ = gate.build_route_task_field_retest_material_callback_review_decision(str(pending_path), "ev-material-review-001")

        self.assertEqual(missing_artifact["review_decision"], "needs_material_callback_backfill_not_proven")
        self.assertIn("delivery_result", missing_summary["missing_materials"])
        self.assertEqual(rejected_artifact["review_decision"], "needs_material_callback_backfill_not_proven")
        self.assertEqual(pending_artifact["review_decision"], "needs_material_callback_backfill_not_proven")
        self.assertFalse(pending_summary["material_callback_review_summary"]["owner_acknowledgement_ok"])

    def test_wrapper_and_nested_packet_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapper.json"
            path.write_text(
                json.dumps({"payload": {"route_task_field_retest_material_callback_packet_summary": self._packet_payload("ev-material-review-002")}}),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_material_callback_review_decision(str(path), "")

        self.assertEqual(artifact["review_decision"], "ready_for_controlled_field_rerun_not_proven")
        self.assertEqual(summary["safe_evidence_ref"], "ev-material-review-002")

    def test_ref_mismatch_and_unsupported_packet_schema_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            ready_path.write_text(json.dumps(self._packet_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._packet_payload(schema="trashbot.other.v1")), encoding="utf-8")

            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_material_callback_review_decision(
                str(ready_path),
                "other-ref",
            )
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_material_callback_review_decision(
                str(bad_schema_path),
                "ev-material-review-001",
            )

        self.assertEqual(mismatch_artifact["review_decision"], "evidence_ref_mismatch_rerun_not_proven")
        self.assertEqual(schema_artifact["review_decision"], "unsupported_material_callback_packet_schema_not_proven")

    def test_unsafe_packet_and_success_claim_are_separate_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe_path.write_text(
                json.dumps(
                    self._packet_payload(
                        owner_acknowledgement={
                            "owner_id": "autonomy-engineer",
                            "material_callback_status": "material_callback_received_not_proven",
                            "safe_note": "raw path /Users/m4/private.log /cmd_vel",
                            "review_requested_at": "2026-05-18T00:00:00Z",
                        }
                    )
                ),
                encoding="utf-8",
            )
            success_path.write_text(json.dumps(self._packet_payload(delivery_success=True)), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_material_callback_review_decision(str(unsafe_path), "ev-material-review-001")
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_material_callback_review_decision(str(success_path), "ev-material-review-001")

        self.assertEqual(unsafe_artifact["review_decision"], "blocked_material_callback_review_not_proven")
        self.assertEqual(success_artifact["review_decision"], "unsafe_success_claim_rejected_not_proven")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)


if __name__ == "__main__":
    unittest.main()
