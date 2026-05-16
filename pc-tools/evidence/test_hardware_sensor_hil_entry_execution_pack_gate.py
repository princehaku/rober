#!/usr/bin/env python3
"""hardware_sensor_hil_entry_execution_pack gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：fixture 只表达 software-proof readiness review。
# 测试约束 02：ready case 仍保持 hardware_material_pending 和 not_proven。
# 测试约束 03：ready case 仍保持 delivery_success=false。
# 测试约束 04：ready case 仍保持 primary_actions_enabled=false。
# 测试约束 05：缺 readiness review 必须 fail closed。
# 测试约束 06：unsupported schema/boundary 必须 fail closed。
# 测试约束 07：readiness 未 ready 不能生成 ready execution pack。
# 测试约束 08：weak boolean 字符串 false 必须 fail closed。
# 测试约束 09：unsafe copy 和 raw serial path 必须 fail closed。
# 测试约束 10：HIL passed / field pass / 采购完成文案必须 fail closed。
# 测试约束 11：safe evidence_ref 缺失或像路径必须 fail closed。
# 测试约束 12：测试不访问 ROS、串口、网络、采购系统或真实传感器。

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import hardware_sensor_hil_entry_execution_pack_gate as gate  # noqa: E402


def ready_review() -> dict:
    # readiness fixture 是上游评审摘要，不代表真实采购、接线、标定或 HIL。
    return {
        "schema": "trashbot.hardware_sensor_hil_entry_readiness_review.v1",
        "schema_version": 1,
        "source": "software_proof",
        "evidence_boundary": "software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate",
        "evidence_ref": "sensor-hil-entry-001",
        "readiness_review_status": "ready_for_hardware_sensor_hil_entry_readiness_review_not_proven",
        "hardware_sensor_hil_entry_readiness_review": "ready_for_hardware_sensor_hil_entry_readiness_review_not_proven",
        "source_statuses": {
            "receipt_intake_status": "ready_for_hardware_sensor_procurement_receipt_intake_not_proven",
            "config_precheck_status": "ready_for_hardware_sensor_hil_entry_config_precheck_not_proven",
        },
        "next_required_evidence": [
            "Collect real bench/HIL-entry materials before claiming any hardware pass.",
        ],
        "owner_handoff": [
            {
                "owner": "Hardware Infra Engineer",
                "action": "Prepare HIL-entry material templates while keeping hardware_material_pending.",
            }
        ],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": ["real_sensor_hil_entry_pass", "delivery_success"],
        "readiness_review_summary": {
            "schema": "trashbot.hardware_sensor_hil_entry_readiness_review_summary.v1",
            "schema_version": 1,
            "source_schema": "trashbot.hardware_sensor_hil_entry_readiness_review.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate",
            "status": "ready_for_hardware_sensor_hil_entry_readiness_review_not_proven",
            "hardware_sensor_hil_entry_readiness_review": "ready_for_hardware_sensor_hil_entry_readiness_review_not_proven",
            "evidence_ref": "sensor-hil-entry-001",
            "source_statuses": {
                "receipt_intake_status": "ready_for_hardware_sensor_procurement_receipt_intake_not_proven",
                "config_precheck_status": "ready_for_hardware_sensor_hil_entry_config_precheck_not_proven",
            },
            "next_required_evidence": [
                "Collect real bench/HIL-entry materials before claiming any hardware pass.",
            ],
            "owner_handoff": [
                {
                    "owner": "Hardware Infra Engineer",
                    "action": "Prepare HIL-entry material templates while keeping hardware_material_pending.",
                }
            ],
            "hardware_material_status": "hardware_material_pending",
            "hardware_material_pending": True,
            "evidence_status": "not_proven",
            "not_proven": ["real_sensor_hil_entry_pass", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


class HardwareSensorHilEntryExecutionPackGateTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，不污染真实 sprint evidence。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def build(self, payload: dict):
        # 统一走文件入口，覆盖 CLI 同款 schema/boundary 和安全扫描。
        with tempfile.TemporaryDirectory() as td:
            path = self.write_json(Path(td), "readiness.json", payload)
            return gate.build_hardware_sensor_hil_entry_execution_pack(path)

    def test_ready_review_becomes_hil_entry_execution_pack_not_proven(self):
        artifact, summary, exit_code = self.build(ready_review())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_sensor_hil_entry_execution_pack.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_hil_entry_execution_pack_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate",
        )
        self.assertEqual(
            artifact["execution_pack_status"],
            "ready_for_hardware_sensor_hil_entry_execution_pack_not_proven",
        )
        names = [item["name"] for item in artifact["material_templates"]]
        self.assertIn("2d_lidar_sku_source_receipt.md", names)
        self.assertIn("tof_sku_source_receipt.md", names)
        self.assertIn("hil_entry_operator_checklist.md", names)
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(artifact["evidence_status"], "not_proven")
        self.assertIn("docs/vendor/VENDOR_INDEX.md", json.dumps(artifact, ensure_ascii=False))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_readiness_review_fails_closed(self):
        artifact, summary, exit_code = gate.build_hardware_sensor_hil_entry_execution_pack(None)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_missing_hardware_sensor_hil_entry_readiness_review")
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertFalse(summary["delivery_success"])

    def test_summary_and_wrapper_inputs_are_supported(self):
        summary_payload = ready_review()["readiness_review_summary"]
        summary_artifact, _summary, summary_exit = self.build(summary_payload)
        wrapper_payload = {"hardware_sensor_hil_entry_readiness_review_summary": ready_review()["readiness_review_summary"]}
        wrapper_artifact, _wrapper_summary, wrapper_exit = self.build(wrapper_payload)

        self.assertEqual(summary_exit, 0)
        self.assertEqual(wrapper_exit, 0)
        self.assertEqual(summary_artifact["source_readiness_schema"], "trashbot.hardware_sensor_hil_entry_readiness_review_summary.v1")
        self.assertEqual(wrapper_artifact["schema_status"], "supported")

    def test_unsupported_schema_or_boundary_fails_closed(self):
        bad_schema = ready_review()
        bad_schema["schema"] = "trashbot.unsupported.v1"
        unsupported_artifact, _summary, unsupported_exit = self.build(bad_schema)

        bad_boundary = ready_review()["readiness_review_summary"]
        bad_boundary["evidence_boundary"] = "software_proof_other_gate"
        boundary_artifact, _boundary_summary, boundary_exit = self.build(bad_boundary)

        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(boundary_exit, 2)
        self.assertEqual(
            unsupported_artifact["execution_pack_status"],
            "blocked_unsupported_hardware_sensor_hil_entry_readiness_review",
        )
        self.assertEqual(boundary_artifact["schema_status"], "unsupported")

    def test_readiness_not_ready_fails_closed(self):
        payload = ready_review()
        payload["readiness_review_status"] = "blocked_upstream_hardware_sensor_hil_entry_not_ready"
        payload["hardware_sensor_hil_entry_readiness_review"] = "blocked_upstream_hardware_sensor_hil_entry_not_ready"
        payload["readiness_review_summary"]["status"] = "blocked_upstream_hardware_sensor_hil_entry_not_ready"
        payload["readiness_review_summary"]["hardware_sensor_hil_entry_readiness_review"] = "blocked_upstream_hardware_sensor_hil_entry_not_ready"
        artifact, _summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_hardware_sensor_hil_entry_readiness_not_ready")

    def test_weak_boolean_or_missing_safe_ref_fails_closed(self):
        weak = ready_review()["readiness_review_summary"]
        weak["delivery_success"] = "false"
        weak_artifact, _summary, weak_exit = self.build(weak)

        bad_ref = ready_review()["readiness_review_summary"]
        bad_ref["evidence_ref"] = ""
        ref_artifact, _ref_summary, ref_exit = self.build(bad_ref)

        self.assertEqual(weak_exit, 2)
        self.assertEqual(ref_exit, 2)
        self.assertEqual(weak_artifact["execution_pack_status"], "blocked_weak_hardware_sensor_hil_entry_readiness_contract")
        self.assertIn("evidence_ref", ref_artifact["blocked_reason"])

    def test_unsafe_copy_and_success_claim_fail_closed(self):
        unsafe = ready_review()
        unsafe["readiness_review_summary"]["owner_handoff"].append(
            {"owner": "Hardware Infra Engineer", "action": "Authorization: Bearer abc /dev/ttyUSB0 raw JSON"}
        )
        unsafe_artifact, _summary, unsafe_exit = self.build(unsafe)

        success = ready_review()
        success["note"] = "HIL passed and 采购完成"
        success_artifact, success_summary, success_exit = self.build(success)

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(success_exit, 2)
        self.assertEqual(
            unsafe_artifact["execution_pack_status"],
            "blocked_unsafe_hardware_sensor_hil_entry_execution_pack_copy",
        )
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
