#!/usr/bin/env python3
"""route_task_field_retest_review_result_handoff 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import route_task_field_retest_review_result_handoff as gate  # noqa: E402


# 测试约束 01：fixture 只表达 callback review decision，不创建材料目录。
# 测试约束 02：ready case 只能证明 result-intake handoff metadata readiness。
# 测试约束 03：ready case 仍必须保留 delivery_success=false。
# 测试约束 04：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 05：ready case 仍必须保留 not_proven。
# 测试约束 06：backfill case 验证缺材料时必须 blocked。
# 测试约束 07：mismatch case 验证证据号不一致必须复跑。
# 测试约束 08：unsupported case 验证 schema 漂移必须 fail closed。
# 测试约束 09：unsafe case 验证 raw path 和 ROS topic 不进入 summary。
# 测试约束 10：success case 验证成功/动作声明映射为 unsafe source review。
# 测试约束 11：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 12：单测不访问 ROS graph、Nav2 runtime 或硬件。
# 测试约束 13：单测不访问 cloud、phone、serial/UART 或 WAVE ROVER。
# 测试约束 14：所有断言围绕契约字段，不依赖生成时间。
# 测试约束 15：未来新增 mapping 必须补对应测试和文档。


class RouteTaskFieldRetestReviewResultHandoffTest(unittest.TestCase):
    def _review_payload(self, decision: str = "ready_for_result_intake", evidence_ref: str = "ev-handoff-001", **extra: object) -> dict[str, object]:
        # fixture 只表达上一轮 review summary，不包含真实材料或 raw artifact。
        payload: dict[str, object] = {
            "schema": "trashbot.route_task_field_retest_callback_review_decision_summary.v1",
            "schema_version": 1,
            "evidence_boundary": "software_proof_docker_route_task_field_retest_callback_review_decision_gate",
            "status": decision,
            "review_decision": decision,
            "evidence_ref": evidence_ref,
            "safe_evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "missing_materials": [],
            "required_evidence_packet": list(gate.REQUIRED_EVIDENCE_PACKET),
            "result_intake_readiness": {
                "ready": decision == "ready_for_result_intake",
                "state": "ready_for_result_intake" if decision == "ready_for_result_intake" else "not_ready",
            },
            "safe_copy": {
                "review_decision": decision,
                "evidence_ref": evidence_ref,
                "not_proven": "not_proven",
            },
            "not_proven": list(gate.NOT_PROVEN),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def test_ready_for_result_intake_maps_to_ready_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.json"
            path.write_text(json.dumps(self._review_payload()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_route_task_field_retest_review_result_handoff(str(path), "ev-handoff-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.route_task_field_retest_review_result_handoff.v1")
        self.assertEqual(summary["schema"], "trashbot.route_task_field_retest_review_result_handoff_summary.v1")
        self.assertEqual(artifact["evidence_boundary"], "software_proof_docker_route_task_field_retest_review_result_handoff_gate")
        self.assertEqual(artifact["handoff_status"], "ready_for_result_intake_handoff")
        self.assertEqual(summary["result_intake_readiness"], "ready_for_result_material_intake")
        self.assertTrue(summary["result_intake_readiness_detail"]["ready"])
        self.assertEqual(summary["safe_copy"]["not_proven"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_review_decision_blocked_mappings_are_preserved(self) -> None:
        cases = {
            "needs_material_backfill": ("blocked_until_material_backfill", "not_ready"),
            "evidence_ref_mismatch_rerun": ("blocked_until_same_evidence_ref_rerun", "not_ready"),
            "unsupported_callback_schema": ("blocked_unsupported_source_schema", "not_ready"),
            "blocked_unsafe_callback": ("blocked_unsafe_source_review", "not_ready"),
            "blocked_success_claim": ("blocked_unsafe_source_review", "not_ready"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for decision, (handoff_status, readiness) in cases.items():
                path = root / f"{decision}.json"
                path.write_text(json.dumps(self._review_payload(decision=decision)), encoding="utf-8")

                artifact, summary, _exit_code = gate.build_route_task_field_retest_review_result_handoff(str(path), "ev-handoff-001")

                self.assertEqual(artifact["handoff_status"], handoff_status)
                self.assertEqual(summary["result_intake_readiness"], readiness)
                self.assertFalse(summary["result_intake_readiness_detail"]["ready"])

    def test_wrapper_and_nested_review_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrapper.json"
            path.write_text(
                json.dumps({"payload": {"route_task_field_retest_callback_review_decision_summary": self._review_payload(evidence_ref="ev-handoff-002")}}),
                encoding="utf-8",
            )

            artifact, summary, _exit_code = gate.build_route_task_field_retest_review_result_handoff(str(path), "")

        self.assertEqual(artifact["handoff_status"], "ready_for_result_intake_handoff")
        self.assertEqual(summary["evidence_ref"], "ev-handoff-002")

    def test_ref_mismatch_and_unsupported_schema_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            ready_path.write_text(json.dumps(self._review_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._review_payload(schema="trashbot.other.v1")), encoding="utf-8")

            mismatch_artifact, _mismatch_summary, _ = gate.build_route_task_field_retest_review_result_handoff(str(ready_path), "other-ref")
            schema_artifact, _schema_summary, _ = gate.build_route_task_field_retest_review_result_handoff(str(bad_schema_path), "ev-handoff-001")

        self.assertEqual(mismatch_artifact["handoff_status"], "blocked_until_same_evidence_ref_rerun")
        self.assertEqual(schema_artifact["handoff_status"], "blocked_unsupported_source_schema")

    def test_unsafe_review_and_success_claim_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe_path.write_text(
                json.dumps(self._review_payload(owner_handoff={"note": "raw path /Users/m4/private.log /cmd_vel"})),
                encoding="utf-8",
            )
            success_path.write_text(json.dumps(self._review_payload(delivery_success=True)), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_route_task_field_retest_review_result_handoff(str(unsafe_path), "ev-handoff-001")
            success_artifact, _success_summary, _ = gate.build_route_task_field_retest_review_result_handoff(str(success_path), "ev-handoff-001")

        self.assertEqual(unsafe_artifact["handoff_status"], "blocked_unsafe_source_review")
        self.assertEqual(success_artifact["handoff_status"], "blocked_unsafe_source_review")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)


if __name__ == "__main__":
    unittest.main()
