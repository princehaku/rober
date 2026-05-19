#!/usr/bin/env python3
"""hardware_sensor_hil_entry_callback_intake gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：fixture 只表达 software-proof execution pack。
# 测试约束 02：ready case 仍保持 hardware_material_pending 和 not_proven。
# 测试约束 03：ready case 仍保持 delivery_success=false。
# 测试约束 04：ready case 仍保持 primary_actions_enabled=false。
# 测试约束 05：缺 execution pack 或 callback material 必须 fail closed。
# 测试约束 06：unsupported schema/boundary 必须 fail closed。
# 测试约束 07：evidence_ref mismatch 必须 fail closed。
# 测试约束 08：弱 bool 字符串 false 必须 fail closed。
# 测试约束 09：raw serial/UART、本机路径和凭证必须 fail closed。
# 测试约束 10：HIL pass / field pass / delivery success 文案必须 fail closed。
# 测试约束 11：safe_copy 只能输出白名单摘要。
# 测试约束 12：测试不访问 ROS、串口、网络、采购系统或真实传感器。

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import hardware_sensor_hil_entry_callback_intake_gate as gate  # noqa: E402


def ready_execution_pack() -> dict:
    # execution pack fixture 是上游模板包，不代表真实采购、安装、标定或 HIL。
    return {
        "schema": "trashbot.hardware_sensor_hil_entry_execution_pack.v1",
        "schema_version": 1,
        "source": "software_proof",
        "evidence_boundary": "software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate",
        "evidence_ref": "sensor-hil-callback-001",
        "execution_pack_status": "ready_for_hardware_sensor_hil_entry_execution_pack_not_proven",
        "hardware_sensor_hil_entry_execution_pack": "ready_for_hardware_sensor_hil_entry_execution_pack_not_proven",
        "next_required_evidence": [
            "Collect 2D LiDAR / ToF / mounting / wiring / power / calibration / operator materials.",
        ],
        "owner_handoff": [
            {
                "owner": "Hardware Infra Engineer",
                "action": "Collect sanitized callback materials under the same evidence_ref.",
            }
        ],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": ["real_sensor_hil_entry_pass", "delivery_success"],
        "execution_pack_summary": {
            "schema": "trashbot.hardware_sensor_hil_entry_execution_pack_summary.v1",
            "schema_version": 1,
            "source_schema": "trashbot.hardware_sensor_hil_entry_execution_pack.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate",
            "status": "ready_for_hardware_sensor_hil_entry_execution_pack_not_proven",
            "hardware_sensor_hil_entry_execution_pack": "ready_for_hardware_sensor_hil_entry_execution_pack_not_proven",
            "evidence_ref": "sensor-hil-callback-001",
            "next_required_evidence": [
                "Collect 2D LiDAR / ToF / mounting / wiring / power / calibration / operator materials.",
            ],
            "owner_handoff": [
                {
                    "owner": "Hardware Infra Engineer",
                    "action": "Collect sanitized callback materials under the same evidence_ref.",
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


def callback_materials() -> dict:
    # callback fixture 只放 summary/ref，不放完整 artifact、checksum 或本机路径。
    return {
        "schema": "trashbot.hardware_sensor_hil_entry_callback_materials.v1",
        "evidence_ref": "sensor-hil-callback-001",
        "callback_materials": {
            "2d_lidar_sku_source_receipt": {
                "summary": "2D LiDAR SKU/source/receipt callback reference collected for review.",
                "ref": "lidar-receipt-ref-001",
            },
            "tof_sku_source_receipt": {
                "summary": "ToF SKU/source/receipt callback reference collected for review.",
                "ref": "tof-receipt-ref-001",
            },
            "mounting": {"summary": "Mounting callback summary only.", "ref": "mounting-ref-001"},
            "wiring": {"summary": "Wiring callback summary only.", "ref": "wiring-ref-001"},
            "power": {"summary": "Power callback summary only.", "ref": "power-ref-001"},
            "calibration": {"summary": "Calibration callback summary only.", "ref": "calibration-ref-001"},
            "hil_entry_operator_result": {
                "status": "operator_result_material_submitted_not_proven",
                "summary": "Operator result callback summary awaiting review.",
                "ref": "operator-result-ref-001",
            },
        },
    }


class HardwareSensorHilEntryCallbackIntakeGateTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，不污染 sprint evidence。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def build(self, pack: dict, callback: dict):
        # 统一走文件入口，覆盖 CLI 同款读取与安全扫描。
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack_path = self.write_json(root, "pack.json", pack)
            callback_path = self.write_json(root, "callback.json", callback)
            return gate.build_hardware_sensor_hil_entry_callback_intake(pack_path, callback_path)

    def test_ready_callback_materials_become_not_proven_intake(self):
        artifact, summary, exit_code = self.build(ready_execution_pack(), callback_materials())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_sensor_hil_entry_callback_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_hil_entry_callback_intake_summary.v1")
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate",
        )
        self.assertEqual(
            artifact["callback_intake_status"],
            "ready_for_hardware_sensor_hil_entry_callback_intake_not_proven",
        )
        self.assertEqual(len(artifact["accepted_callback_materials"]), 7)
        self.assertEqual(artifact["missing_required_materials"], [])
        self.assertEqual(artifact["rejected_callback_materials"], [])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", json.dumps(artifact, ensure_ascii=False))
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", json.dumps(artifact, ensure_ascii=False))
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(artifact["evidence_status"], "not_proven")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_execution_pack_or_callback_fails_closed(self):
        missing_pack_artifact, missing_pack_summary, missing_pack_exit = gate.build_hardware_sensor_hil_entry_callback_intake(
            None, None
        )
        with tempfile.TemporaryDirectory() as td:
            pack_path = self.write_json(Path(td), "pack.json", ready_execution_pack())
            missing_callback_artifact, _summary, missing_callback_exit = gate.build_hardware_sensor_hil_entry_callback_intake(
                pack_path, None
            )

        self.assertEqual(missing_pack_exit, 2)
        self.assertEqual(missing_callback_exit, 2)
        self.assertEqual(
            missing_pack_artifact["callback_intake_status"],
            "blocked_missing_hardware_sensor_hil_entry_execution_pack",
        )
        self.assertEqual(
            missing_callback_artifact["callback_intake_status"],
            "blocked_missing_hardware_sensor_hil_entry_callback_materials",
        )
        self.assertEqual(missing_pack_summary["hardware_material_status"], "hardware_material_pending")

    def test_summary_and_wrapper_execution_pack_inputs_are_supported(self):
        pack_summary = ready_execution_pack()["execution_pack_summary"]
        wrapper = {"hardware_sensor_hil_entry_execution_pack_summary": pack_summary}
        summary_artifact, _summary, summary_exit = self.build(pack_summary, callback_materials())
        wrapper_artifact, _wrapper_summary, wrapper_exit = self.build(wrapper, callback_materials())

        self.assertEqual(summary_exit, 0)
        self.assertEqual(wrapper_exit, 0)
        self.assertEqual(summary_artifact["source_execution_pack_schema"], "trashbot.hardware_sensor_hil_entry_execution_pack_summary.v1")
        self.assertEqual(wrapper_artifact["schema_status"], "supported")

    def test_unsupported_schema_or_boundary_fails_closed(self):
        bad_schema = ready_execution_pack()
        bad_schema["schema"] = "trashbot.unsupported.v1"
        unsupported_artifact, _summary, unsupported_exit = self.build(bad_schema, callback_materials())

        bad_boundary = ready_execution_pack()["execution_pack_summary"]
        bad_boundary["evidence_boundary"] = "software_proof_other_gate"
        boundary_artifact, _boundary_summary, boundary_exit = self.build(bad_boundary, callback_materials())

        callback_bad_schema = callback_materials()
        callback_bad_schema["schema"] = "trashbot.unsupported_callback.v1"
        callback_artifact, _callback_summary, callback_exit = self.build(ready_execution_pack(), callback_bad_schema)

        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(boundary_exit, 2)
        self.assertEqual(callback_exit, 2)
        self.assertEqual(
            unsupported_artifact["callback_intake_status"],
            "blocked_unsupported_hardware_sensor_hil_entry_callback_intake",
        )
        self.assertEqual(boundary_artifact["schema_status"], "unsupported")
        self.assertEqual(callback_artifact["callback_schema_status"], "unsupported")

    def test_evidence_ref_mismatch_fails_closed(self):
        callback = callback_materials()
        callback["evidence_ref"] = "different-ref-001"
        artifact, _summary, exit_code = self.build(ready_execution_pack(), callback)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["callback_intake_status"], "blocked_evidence_ref_mismatch")

    def test_weak_execution_pack_contract_fails_closed(self):
        weak = ready_execution_pack()["execution_pack_summary"]
        weak["delivery_success"] = "false"
        weak_artifact, _summary, weak_exit = self.build(weak, callback_materials())

        not_ready = ready_execution_pack()
        not_ready["execution_pack_status"] = "blocked_hardware_sensor_hil_entry_execution_pack_not_ready"
        not_ready["hardware_sensor_hil_entry_execution_pack"] = "blocked_hardware_sensor_hil_entry_execution_pack_not_ready"
        not_ready["execution_pack_summary"]["status"] = "blocked_hardware_sensor_hil_entry_execution_pack_not_ready"
        not_ready["execution_pack_summary"]["hardware_sensor_hil_entry_execution_pack"] = "blocked_hardware_sensor_hil_entry_execution_pack_not_ready"
        not_ready_artifact, _not_ready_summary, not_ready_exit = self.build(not_ready, callback_materials())

        self.assertEqual(weak_exit, 2)
        self.assertEqual(not_ready_exit, 2)
        self.assertEqual(
            weak_artifact["callback_intake_status"],
            "blocked_weak_hardware_sensor_hil_entry_execution_pack_contract",
        )
        self.assertIn("blocked_hardware_sensor_hil_entry_execution_pack_not_ready", not_ready_artifact["blocked_reason"])

    def test_unsafe_copy_and_success_claim_fail_closed(self):
        unsafe = callback_materials()
        unsafe["callback_materials"]["wiring"] = {
            "summary": "Authorization: Bearer abc /dev/ttyUSB0 raw UART",
            "ref": "/Users/m4/private/wiring.json",
        }
        unsafe_artifact, _summary, unsafe_exit = self.build(ready_execution_pack(), unsafe)

        success = callback_materials()
        success["callback_materials"]["hil_entry_operator_result"]["summary"] = "HIL passed and delivery success"
        success["delivery_success"] = True
        success_artifact, success_summary, success_exit = self.build(ready_execution_pack(), success)

        encoded = json.dumps(unsafe_artifact, ensure_ascii=False)
        self.assertEqual(unsafe_exit, 2)
        self.assertEqual(success_exit, 2)
        self.assertEqual(
            unsafe_artifact["callback_intake_status"],
            "blocked_unsafe_hardware_sensor_hil_entry_callback_intake_copy",
        )
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
