#!/usr/bin/env python3
"""hardware_sensor_hil_entry_readiness_review gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：fixture 只表达上游 software-proof summary，不表达真实硬件存在。
# 测试约束 02：ready case 必须保持 not_proven、delivery_success=false。
# 测试约束 03：ready case 必须保持 primary_actions_enabled=false。
# 测试约束 04：缺 receipt 或 config 必须 fail closed。
# 测试约束 05：unsupported schema/boundary 必须 fail closed。
# 测试约束 06：上游 blocked 状态不能被 readiness review 放行。
# 测试约束 07：evidence_ref 不一致必须 fail closed，避免材料混号。
# 测试约束 08：weak boolean 字符串 false 必须 fail closed。
# 测试约束 09：raw serial/topic/raw JSON copy 必须 fail closed。
# 测试约束 10：HIL/field/delivery success claim 必须 fail closed。
# 测试约束 11：测试只写临时 JSON，不污染真实 sprint evidence。
# 测试约束 12：测试不访问 ROS graph、串口、网络或真实传感器。
# 测试约束 13：summary wrapper case 保护 Robot/mobile 嵌套消费路径。
# 测试约束 14：vendor boundary 必须保留 docs/vendor/VENDOR_INDEX.md。
# 测试约束 15：测试字段名保持英文，方便 JSON consumer 稳定解析。

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import hardware_sensor_hil_entry_readiness_review_gate as gate  # noqa: E402


def receipt_summary() -> dict:
    # receipt fixture 是已脱敏材料摘要，不代表真实采购、安装或 HIL 完成。
    return {
        "schema": "trashbot.hardware_sensor_procurement_receipt_intake_summary.v1",
        "schema_version": 1,
        "source": "software_proof",
        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate",
        "status": "ready_for_hardware_sensor_procurement_receipt_intake_not_proven",
        "receipt_intake_status": "ready_for_hardware_sensor_procurement_receipt_intake_not_proven",
        "hardware_sensor_procurement_receipt_intake": "ready_for_hardware_sensor_procurement_receipt_intake_not_proven",
        "evidence_ref": "sensor-hil-entry-001",
        "accepted_materials": ["receipt", "source", "vendor", "sku", "wiring", "power"],
        "missing_materials": ["calibration", "hil_entry"],
        "rejected_materials": [],
        "next_required_evidence": [
            "Review accepted receipt/source/vendor/SKU refs before changing hardware boundary.",
        ],
        "owner_handoff": [
            {
                "owner": "Hardware Infra Engineer",
                "action": "Request reviewed install, wiring, power, calibration, and HIL-entry materials.",
            }
        ],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": ["real_sensor_hil_entry_pass", "delivery_success"],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def config_summary() -> dict:
    # config fixture 是 future 参数化摘要，不代表 sensor driver、TF 或 HIL 已运行。
    return {
        "schema": "trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1",
        "schema_version": 1,
        "source": "software_proof",
        "evidence_boundary": "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate",
        "status": "ready_for_hardware_sensor_hil_entry_config_precheck_not_proven",
        "hardware_sensor_hil_entry_config_precheck": "ready_for_hardware_sensor_hil_entry_config_precheck_not_proven",
        "evidence_ref": "sensor-hil-entry-001",
        "sensor_config_summary": {"sensor count": 3, "tof_channel_count": 4, "roles": ["2d_lidar", "monocular", "tof"]},
        "threshold_summary": {"thresholds": {"near_field_safety_m": 0.35, "confidence_min": 0.7}},
        "frame_id_summary": {"frame IDs": {"sensor_frame": "sensor_array_frame", "base_frame": "base_link"}},
        "safety_policy_summary": {"safety policy": {"mode": "fail_closed", "primary_actions_enabled": False}},
        "missing_config": [],
        "missing_evidence_refs": [],
        "next_required_evidence": [
            "Collect real bench/HIL-entry materials before claiming any hardware pass.",
        ],
        "owner_handoff": [
            {"owner": "Hardware Infra Engineer", "action": "Review refs before bench/HIL entry."}
        ],
        "not_proven": ["real_sensor_hil_entry_pass", "delivery_success"],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


class HardwareSensorHilEntryReadinessReviewGateTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，避免误写真实 evidence bundle。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def build(self, receipt: dict, config: dict):
        # 统一走文件入口，覆盖 CLI 同款解析、schema 和安全扫描。
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            receipt_path = self.write_json(root, "receipt_summary.json", receipt)
            config_path = self.write_json(root, "config_summary.json", config)
            return gate.build_hardware_sensor_hil_entry_readiness_review(receipt_path, config_path)

    def test_ready_sources_become_readiness_review_not_proven(self):
        artifact, summary, exit_code = self.build(receipt_summary(), config_summary())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_sensor_hil_entry_readiness_review.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_hil_entry_readiness_review_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate",
        )
        self.assertEqual(
            artifact["readiness_review_status"],
            "ready_for_hardware_sensor_hil_entry_readiness_review_not_proven",
        )
        self.assertEqual(summary["source_statuses"]["receipt_intake_status"], receipt_summary()["status"])
        self.assertEqual(summary["source_statuses"]["config_precheck_status"], config_summary()["status"])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", json.dumps(artifact, ensure_ascii=False))
        self.assertIn("real_sensor_hil_entry_pass", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_sources_fail_closed(self):
        artifact, summary, exit_code = gate.build_hardware_sensor_hil_entry_readiness_review(None, None)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["readiness_review_status"],
            "blocked_missing_hardware_sensor_hil_entry_readiness_review_source",
        )
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_nested_wrappers_are_supported(self):
        receipt_wrapper = {"hardware_sensor_procurement_receipt_intake_summary": receipt_summary()}
        config_wrapper = {"hardware_sensor_hil_entry_config_precheck_summary": config_summary()}
        artifact, _summary, exit_code = self.build(receipt_wrapper, config_wrapper)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema_status"]["receipt_intake"], "supported")
        self.assertEqual(artifact["schema_status"]["config_precheck"], "supported")

    def test_unsupported_schema_or_boundary_fails_closed(self):
        bad_receipt = receipt_summary()
        bad_receipt["schema"] = "trashbot.unsupported.v1"
        unsupported_artifact, _summary, unsupported_exit = self.build(bad_receipt, config_summary())

        bad_config = config_summary()
        bad_config["evidence_boundary"] = "software_proof_other_gate"
        boundary_artifact, _boundary_summary, boundary_exit = self.build(receipt_summary(), bad_config)

        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(boundary_exit, 2)
        self.assertEqual(
            unsupported_artifact["readiness_review_status"],
            "blocked_unsupported_hardware_sensor_hil_entry_readiness_review_source",
        )
        self.assertEqual(boundary_artifact["schema_status"]["config_precheck"], "unsupported")

    def test_upstream_not_ready_fails_closed(self):
        blocked_receipt = receipt_summary()
        blocked_receipt["status"] = "blocked_missing_hardware_sensor_procurement_receipt_materials"
        blocked_receipt["receipt_intake_status"] = "blocked_missing_hardware_sensor_procurement_receipt_materials"
        artifact, _summary, exit_code = self.build(blocked_receipt, config_summary())

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["readiness_review_status"],
            "blocked_upstream_hardware_sensor_hil_entry_not_ready",
        )

    def test_evidence_ref_mismatch_fails_closed(self):
        mismatch_config = config_summary()
        mismatch_config["evidence_ref"] = "sensor-hil-entry-002"
        artifact, _summary, exit_code = self.build(receipt_summary(), mismatch_config)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["readiness_review_status"],
            "blocked_hardware_sensor_hil_entry_readiness_review_evidence_ref_mismatch",
        )

    def test_weak_boolean_contract_fails_closed(self):
        weak_config = config_summary()
        weak_config["delivery_success"] = "false"
        artifact, _summary, exit_code = self.build(receipt_summary(), weak_config)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["readiness_review_status"],
            "blocked_weak_hardware_sensor_hil_entry_readiness_review_contract",
        )
        self.assertIn("delivery_success", artifact["blocked_reason"])

    def test_unsafe_copy_and_success_claim_fail_closed(self):
        unsafe_config = config_summary()
        unsafe_config["debug"] = "serial probe /dev/ttyUSB0 and /cmd_vel raw JSON"
        unsafe_artifact, _unsafe_summary, unsafe_exit = self.build(receipt_summary(), unsafe_config)

        success_receipt = receipt_summary()
        success_receipt["note"] = "delivery_success=true and HIL passed"
        success_artifact, success_summary, success_exit = self.build(success_receipt, config_summary())

        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(success_exit, 2)
        self.assertEqual(
            unsafe_artifact["readiness_review_status"],
            "blocked_unsafe_hardware_sensor_hil_entry_readiness_review_copy",
        )
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
