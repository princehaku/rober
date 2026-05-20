#!/usr/bin/env python3
"""field_evidence_rerun_material_dispatch 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；验收入口显式加入该目录，保持 CLI 与 unittest 同源。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import field_evidence_rerun_material_dispatch as gate  # noqa: E402


# 测试约束 01：fixture 只表达安全 summary，不创建真实材料目录。
# 测试约束 02：ready case 只能证明 dispatch package metadata readiness。
# 测试约束 03：required material groups 必须覆盖真实 route/elevator/phone 材料。
# 测试约束 04：ready case 仍必须保留 safe_to_control=false。
# 测试约束 05：ready case 仍必须保留 delivery_success=false。
# 测试约束 06：ready case 仍必须保留 primary_actions_enabled=false。
# 测试约束 07：ready case 仍必须保留 not_proven。
# 测试约束 08：mismatch case 验证 CLI evidence_ref 不能静默覆盖 source。
# 测试约束 09：unsupported case 验证错误 schema/boundary 不被包装成 ready。
# 测试约束 10：unsafe case 验证 raw path、ROS topic、checksum 被阻断。
# 测试约束 11：success case 验证控制/成功声明映射为 blocked。
# 测试约束 12：wrapper case 验证自动化嵌套 JSON 可被消费。
# 测试约束 13：real-material status summary 可作为兼容 source。
# 测试约束 14：单测不访问 ROS graph、硬件、外部云或手机运行时。
# 测试约束 15：所有断言围绕契约字段，不依赖生成时间。


class FieldEvidenceRerunMaterialDispatchTest(unittest.TestCase):
    def _handoff_payload(
        self,
        evidence_ref: str = "ev-field-dispatch-001",
        schema: str = "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary.v1",
        boundary: str = "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate",
        **extra: object,
    ) -> dict[str, object]:
        # fixture 只表达上游 handoff 摘要，不包含真实材料内容或 raw artifact。
        payload: dict[str, object] = {
            "schema": schema,
            "schema_version": 1,
            "source": "software_proof",
            "evidence_boundary": boundary,
            "status": "ready_for_acceptance_execution_rerun_result_owner_handoff",
            "handoff_status": "ready_for_acceptance_execution_rerun_result_owner_handoff",
            "safe_evidence_ref": evidence_ref,
            "evidence_ref": evidence_ref,
            "same_evidence_ref_required": True,
            "rerun_commands": [
                "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py --once-json"
            ],
            "safe_copy": {
                "schema": f"{schema}.safe_copy",
                "source": "software_proof",
                "status": "ready_for_acceptance_execution_rerun_result_owner_handoff",
                "safe_evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "not_proven": "not_proven",
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": list(gate.NOT_PROVEN),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        payload.update(extra)
        return payload

    def test_supported_handoff_becomes_dispatch_package_but_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff_summary.json"
            path.write_text(json.dumps(self._handoff_payload()), encoding="utf-8")

            artifact, summary, exit_code = gate.build_field_evidence_rerun_material_dispatch(str(path), "ev-field-dispatch-001")

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.field_evidence_rerun_material_dispatch.v1")
        self.assertEqual(summary["schema"], "trashbot.field_evidence_rerun_material_dispatch_summary.v1")
        self.assertEqual(summary["evidence_boundary"], "software_proof_docker_field_evidence_rerun_material_dispatch_gate")
        self.assertEqual(summary["dispatch_status"], "ready_for_field_evidence_rerun_material_dispatch_not_proven")
        material_names = [item["material_group"] for item in summary["required_material_groups"]]
        self.assertIn("real route completion signal", material_names)
        self.assertIn("real field task record", material_names)
        self.assertIn("real Nav2/fixed-route runtime log", material_names)
        self.assertIn("real phone/browser evidence", material_names)
        self.assertFalse(summary["safe_to_control"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_phone_browser_evidence", summary["not_proven"])

    def test_owner_work_orders_commands_and_callback_requirements_are_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff_summary.json"
            path.write_text(json.dumps(self._handoff_payload()), encoding="utf-8")

            _artifact, summary, _exit_code = gate.build_field_evidence_rerun_material_dispatch(str(path), "")

        self.assertEqual(len(summary["owner_work_orders"]), 3)
        self.assertIn("Autonomy Algorithm Engineer", {item["owner"] for item in summary["owner_work_orders"]})
        self.assertIn("field_evidence_rerun_material_dispatch.py", "\n".join(summary["rerun_commands"]))
        self.assertTrue(summary["callback_packet_requirements"]["same_evidence_ref_required"])
        self.assertIn("raw_artifact", summary["callback_packet_requirements"]["forbidden_fields"])
        self.assertEqual(summary["safe_copy"]["safe_to_control"], False)

    def test_mismatch_and_unsupported_source_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ready_path = root / "ready.json"
            bad_schema_path = root / "bad_schema.json"
            ready_path.write_text(json.dumps(self._handoff_payload()), encoding="utf-8")
            bad_schema_path.write_text(json.dumps(self._handoff_payload(schema="trashbot.other.v1")), encoding="utf-8")

            mismatch_artifact, _mismatch_summary, _ = gate.build_field_evidence_rerun_material_dispatch(str(ready_path), "other-ref")
            schema_artifact, _schema_summary, _ = gate.build_field_evidence_rerun_material_dispatch(str(bad_schema_path), "ev-field-dispatch-001")

        self.assertEqual(mismatch_artifact["dispatch_status"], "evidence_ref_mismatch_field_evidence_rerun_material_dispatch_blocked")
        self.assertEqual(schema_artifact["dispatch_status"], "blocked_unsupported_field_evidence_rerun_material_dispatch_source")

    def test_unsafe_copy_and_success_claim_are_blocked_and_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsafe_path = root / "unsafe.json"
            success_path = root / "success.json"
            unsafe = self._handoff_payload()
            unsafe["operator_note"] = "raw artifact /Users/m4/private.log /cmd_vel checksum=abcdef123456"
            success = self._handoff_payload(delivery_success=True)
            unsafe_path.write_text(json.dumps(unsafe), encoding="utf-8")
            success_path.write_text(json.dumps(success), encoding="utf-8")

            unsafe_artifact, unsafe_summary, _ = gate.build_field_evidence_rerun_material_dispatch(str(unsafe_path), "ev-field-dispatch-001")
            success_artifact, _success_summary, _ = gate.build_field_evidence_rerun_material_dispatch(str(success_path), "ev-field-dispatch-001")

        self.assertEqual(unsafe_artifact["dispatch_status"], "blocked_unsafe_field_evidence_rerun_material_dispatch_copy")
        self.assertEqual(success_artifact["dispatch_status"], "blocked_unsafe_field_evidence_rerun_material_dispatch_copy")
        encoded_summary = json.dumps(unsafe_summary, ensure_ascii=False)
        self.assertNotIn("/Users/m4", encoded_summary)
        self.assertNotIn("/cmd_vel", encoded_summary)
        self.assertNotIn("abcdef123456", encoded_summary)

    def test_wrapper_and_real_material_status_sources_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrapper_path = root / "wrapper.json"
            status_path = root / "status.json"
            wrapper_path.write_text(
                json.dumps({"payload": {"route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary": self._handoff_payload("ev-wrapper-field-dispatch-001")}}),
                encoding="utf-8",
            )
            status_path.write_text(
                json.dumps(
                    self._handoff_payload(
                        "ev-status-field-dispatch-001",
                        schema="trashbot.real_material_followup_escalation_status_summary.v1",
                        boundary="software_proof_docker_real_material_followup_escalation_status_gate",
                        status="blocked_pending_real_materials",
                        handoff_status="",
                        real_material_followup_escalation_status="blocked_pending_real_materials",
                    )
                ),
                encoding="utf-8",
            )

            wrapper_artifact, wrapper_summary, _ = gate.build_field_evidence_rerun_material_dispatch(str(wrapper_path), "")
            status_artifact, status_summary, _ = gate.build_field_evidence_rerun_material_dispatch(str(status_path), "")

        self.assertEqual(wrapper_artifact["dispatch_status"], "ready_for_field_evidence_rerun_material_dispatch_not_proven")
        self.assertEqual(wrapper_summary["safe_evidence_ref"], "ev-wrapper-field-dispatch-001")
        self.assertEqual(status_artifact["dispatch_status"], "ready_for_field_evidence_rerun_material_dispatch_not_proven")
        self.assertEqual(status_summary["source_status"], "blocked_pending_real_materials")


if __name__ == "__main__":
    unittest.main()
