#!/usr/bin/env python3
"""hardware_sensor_hil_entry_callback_review_decision gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：fixture 只表达 software-proof callback intake。
# 测试约束 02：ready case 仍保持 hardware_material_pending 和 not_proven。
# 测试约束 03：ready case 仍保持 delivery_success=false。
# 测试约束 04：ready case 仍保持 primary_actions_enabled=false。
# 测试约束 05：ready case 仍保持 safe_to_control=false。
# 测试约束 06：缺 input、unsupported schema/boundary 必须 fail closed。
# 测试约束 07：missing/rejected material 必须转成 review decision 缺口。
# 测试约束 08：weak bool 字符串 false 必须 fail closed。
# 测试约束 09：raw serial/UART、本机路径、凭证必须 fail closed。
# 测试约束 10：HIL pass / field pass / delivery success 文案必须 fail closed。
# 测试约束 11：summary/wrapper 输入也只能输出白名单摘要。
# 测试约束 12：测试不访问 ROS、串口、网络、采购系统或真实传感器。

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import hardware_sensor_hil_entry_callback_review_decision_gate as gate  # noqa: E402


def ready_callback_intake() -> dict:
    # callback intake fixture 是脱敏材料入口，不代表真实采购、安装、标定或 HIL。
    accepted = [
        {
            "material": "2d_lidar_sku_source_receipt",
            "status": "accepted_sanitized_reference",
            "summary": "2D LiDAR SKU/source/receipt callback reference collected for review.",
            "ref": "lidar-receipt-ref-001",
        },
        {
            "material": "tof_sku_source_receipt",
            "status": "accepted_sanitized_reference",
            "summary": "ToF SKU/source/receipt callback reference collected for review.",
            "ref": "tof-receipt-ref-001",
        },
        {"material": "mounting", "status": "accepted_sanitized_reference", "summary": "Mounting summary only.", "ref": "mounting-ref-001"},
        {"material": "wiring", "status": "accepted_sanitized_reference", "summary": "Wiring summary only.", "ref": "wiring-ref-001"},
        {"material": "power", "status": "accepted_sanitized_reference", "summary": "Power summary only.", "ref": "power-ref-001"},
        {"material": "calibration", "status": "accepted_sanitized_reference", "summary": "Calibration summary only.", "ref": "calibration-ref-001"},
        {
            "material": "hil_entry_operator_result",
            "status": "accepted_sanitized_reference",
            "summary": "Operator result callback summary awaiting review.",
            "ref": "operator-result-ref-001",
        },
    ]
    summary = {
        "schema": "trashbot.hardware_sensor_hil_entry_callback_intake_summary.v1",
        "schema_version": 1,
        "source_schema": "trashbot.hardware_sensor_hil_entry_callback_intake.v1",
        "source": "software_proof",
        "evidence_boundary": "software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate",
        "status": "ready_for_hardware_sensor_hil_entry_callback_intake_not_proven",
        "hardware_sensor_hil_entry_callback_intake": "ready_for_hardware_sensor_hil_entry_callback_intake_not_proven",
        "source_execution_pack_status": "ready_for_hardware_sensor_hil_entry_execution_pack_not_proven",
        "evidence_ref": "sensor-hil-callback-review-001",
        "accepted_callback_materials": [item["material"] for item in accepted],
        "missing_required_materials": [],
        "rejected_callback_materials": [],
        "operator_result_summary": {
            "status": "operator_result_material_submitted_not_proven",
            "summary": "Operator result callback summary awaiting review.",
        },
        "owner_handoff": [
            {
                "owner": "Hardware Infra Engineer",
                "action": "Review accepted callback materials for sufficiency.",
            }
        ],
        "next_required_evidence": [
            "Run hardware_sensor_hil_entry_callback_review_decision over this sanitized callback intake summary.",
        ],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": ["real_sensor_hil_entry_pass", "delivery_success"],
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }
    return {
        "schema": "trashbot.hardware_sensor_hil_entry_callback_intake.v1",
        "schema_version": 1,
        "source": "software_proof",
        "evidence_boundary": "software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate",
        "evidence_ref": "sensor-hil-callback-review-001",
        "callback_intake_status": "ready_for_hardware_sensor_hil_entry_callback_intake_not_proven",
        "hardware_sensor_hil_entry_callback_intake": "ready_for_hardware_sensor_hil_entry_callback_intake_not_proven",
        "accepted_callback_materials": accepted,
        "missing_required_materials": [],
        "rejected_callback_materials": [],
        "operator_result_summary": summary["operator_result_summary"],
        "owner_handoff": summary["owner_handoff"],
        "next_required_evidence": summary["next_required_evidence"],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": ["real_sensor_hil_entry_pass", "delivery_success"],
        "callback_intake_summary": summary,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


class HardwareSensorHilEntryCallbackReviewDecisionGateTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，不污染 sprint evidence。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def build(self, payload: dict, evidence_ref: str = ""):
        # 统一走文件入口，覆盖 CLI 同款读取、wrapper 和安全扫描。
        with tempfile.TemporaryDirectory() as td:
            path = self.write_json(Path(td), "callback_intake.json", payload)
            return gate.build_hardware_sensor_hil_entry_callback_review_decision(path, evidence_ref=evidence_ref)

    def test_ready_intake_becomes_owner_handoff_not_proven(self):
        artifact, summary, exit_code = self.build(ready_callback_intake())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_sensor_hil_entry_callback_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_hil_entry_callback_review_decision_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate",
        )
        self.assertEqual(
            artifact["review_decision"],
            "ready_for_hardware_sensor_hil_entry_callback_owner_handoff_not_proven",
        )
        self.assertEqual(len(artifact["accepted_materials"]), 7)
        self.assertEqual(artifact["missing_materials"], [])
        self.assertEqual(artifact["rejected_materials"], [])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", json.dumps(artifact, ensure_ascii=False))
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", json.dumps(artifact, ensure_ascii=False))
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(artifact["evidence_status"], "not_proven")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_missing_input_fails_closed(self):
        artifact, summary, exit_code = gate.build_hardware_sensor_hil_entry_callback_review_decision(None)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["review_decision"],
            "blocked_missing_or_unsupported_hardware_sensor_hil_entry_callback_intake_not_proven",
        )
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_summary_and_wrapper_inputs_are_supported(self):
        summary = ready_callback_intake()["callback_intake_summary"]
        wrapper = {"hardware_sensor_hil_entry_callback_intake_summary": summary}
        summary_artifact, _summary, summary_exit = self.build(summary)
        wrapper_artifact, _wrapper_summary, wrapper_exit = self.build(wrapper)

        self.assertEqual(summary_exit, 0)
        self.assertEqual(wrapper_exit, 0)
        self.assertEqual(summary_artifact["source_callback_intake_schema"], "trashbot.hardware_sensor_hil_entry_callback_intake_summary.v1")
        self.assertEqual(wrapper_artifact["schema_status"], "supported")

    def test_missing_materials_map_to_backfill_decision(self):
        payload = ready_callback_intake()
        payload["callback_intake_status"] = "blocked_missing_hardware_sensor_hil_entry_callback_materials"
        payload["hardware_sensor_hil_entry_callback_intake"] = "blocked_missing_hardware_sensor_hil_entry_callback_materials"
        payload["accepted_callback_materials"] = payload["accepted_callback_materials"][:-2]
        payload["missing_required_materials"] = ["calibration", "hil_entry_operator_result"]
        payload["callback_intake_summary"]["status"] = "blocked_missing_hardware_sensor_hil_entry_callback_materials"
        payload["callback_intake_summary"]["missing_required_materials"] = ["calibration", "hil_entry_operator_result"]
        artifact, _summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["review_decision"],
            "needs_hardware_sensor_hil_entry_callback_material_backfill_not_proven",
        )
        self.assertIn("calibration", " ".join(artifact["next_required_evidence"]))

    def test_rejected_materials_map_to_rejected_decision(self):
        payload = ready_callback_intake()
        payload["rejected_callback_materials"] = [{"material": "wiring", "reason": "unsafe_raw_or_success_claim"}]
        payload["callback_intake_summary"]["rejected_callback_materials"] = [{"material": "wiring", "reason": "unsafe_raw_or_success_claim"}]
        artifact, _summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["review_decision"],
            "blocked_rejected_hardware_sensor_hil_entry_callback_materials_not_proven",
        )
        self.assertEqual(artifact["rejected_materials"][0]["material"], "wiring")

    def test_unsupported_boundary_evidence_ref_mismatch_and_weak_contract_fail_closed(self):
        unsupported = ready_callback_intake()["callback_intake_summary"]
        unsupported["evidence_boundary"] = "software_proof_other_gate"
        unsupported_artifact, _unsupported_summary, unsupported_exit = self.build(unsupported)

        mismatch_artifact, _mismatch_summary, mismatch_exit = self.build(
            ready_callback_intake(),
            evidence_ref="different-evidence-ref-001",
        )

        weak = ready_callback_intake()["callback_intake_summary"]
        weak["delivery_success"] = "false"
        weak_artifact, _weak_summary, weak_exit = self.build(weak)

        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(mismatch_exit, 2)
        self.assertEqual(weak_exit, 2)
        self.assertEqual(
            unsupported_artifact["review_decision"],
            "blocked_missing_or_unsupported_hardware_sensor_hil_entry_callback_intake_not_proven",
        )
        self.assertEqual(mismatch_artifact["review_decision"], "blocked_evidence_ref_mismatch_not_proven")
        self.assertEqual(
            weak_artifact["review_decision"],
            "blocked_weak_hardware_sensor_hil_entry_callback_intake_contract_not_proven",
        )

    def test_unsafe_copy_and_success_claim_fail_closed_and_redacted(self):
        unsafe = ready_callback_intake()
        unsafe["accepted_callback_materials"][3]["summary"] = "Authorization: Bearer abc /dev/ttyUSB0 raw UART"
        unsafe_artifact, _unsafe_summary, unsafe_exit = self.build(unsafe)

        success = ready_callback_intake()
        success["accepted_callback_materials"][6]["summary"] = "HIL passed and delivery success"
        success["safe_to_control"] = True
        success_artifact, success_summary, success_exit = self.build(success)

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(success_exit, 2)
        self.assertEqual(
            unsafe_artifact["review_decision"],
            "blocked_unsafe_hardware_sensor_hil_entry_callback_review_decision_copy_not_proven",
        )
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])
        self.assertFalse(success_summary["safe_to_control"])


if __name__ == "__main__":
    unittest.main()
