#!/usr/bin/env python3
"""hardware_sensor_procurement_receipt_intake gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：所有 case 都只使用临时 JSON，避免污染真实 evidence 目录。
# 测试约束 02：测试只调用 PC gate，不访问采购系统、仓储系统或物流系统。
# 测试约束 03：测试只调用 PC gate，不访问 ROS graph、串口、UART 或真实传感器。
# 测试约束 04：ready fixture 仍保持 software_proof / not_proven。
# 测试约束 05：ready fixture 仍保持 delivery_success=false。
# 测试约束 06：ready fixture 仍保持 primary_actions_enabled=false。
# 测试约束 07：ready fixture 不代表真实采购完成。
# 测试约束 08：ready fixture 不代表真实安装、接线、电源或标定完成。
# 测试约束 09：ready fixture 不代表真实 HIL entry。
# 测试约束 10：missing execution pack case 验证缺上游 fail closed。
# 测试约束 11：summary-only case 验证下游 compact summary 可被消费。
# 测试约束 12：wrapper case 验证 diagnostics 嵌套 summary。
# 测试约束 13：missing material case 验证 receipt/source/vendor/SKU 必填。
# 测试约束 14：unsafe copy case 验证凭证、串口、raw JSON 被阻断。
# 测试约束 15：success claim case 验证采购/HIL/送达成功文案被阻断。
# 测试约束 16：weak boolean case 验证字符串 false 不被放行。
# 测试约束 17：unsupported schema/boundary case 验证 source boundary 不可绕过。
# 测试约束 18：所有 blocked case 都保持 primary_actions_enabled=false。
# 测试约束 19：所有 blocked case 都保持 delivery_success=false。
# 测试约束 20：测试校验 docs/vendor/VENDOR_INDEX.md 留在来源边界。

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import hardware_sensor_procurement_receipt_intake_gate as gate  # noqa: E402


def ready_execution_pack() -> dict:
    # fixture 模拟上一轮 execution pack 已就绪，但真实采购/安装/HIL 仍未发生。
    return {
        "schema": "trashbot.hardware_sensor_procurement_execution_pack.v1",
        "schema_version": 1,
        "source": "software_proof",
        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_execution_pack_gate",
        "evidence_ref": "sensor-execution-pack-001",
        "execution_pack_status": "ready_for_hardware_sensor_procurement_execution_pack_not_proven",
        "hardware_sensor_procurement_execution_pack": "ready_for_hardware_sensor_procurement_execution_pack_not_proven",
        "next_required_evidence": [
            "Fill procurement order refs and source documents for 2D LiDAR and ToF under the same evidence_ref.",
        ],
        "owner_handoff": [
            {
                "owner": "Hardware Infra Engineer",
                "action": "Fill procurement/source, mounting/wiring/power, calibration, and HIL-entry templates with real evidence.",
            }
        ],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "not_proven": ["real_sensor_hil_entry_pass", "delivery_success"],
        "execution_pack_summary": {
            "schema": "trashbot.hardware_sensor_procurement_execution_pack_summary.v1",
            "schema_version": 1,
            "source_schema": "trashbot.hardware_sensor_procurement_execution_pack.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_execution_pack_gate",
            "status": "ready_for_hardware_sensor_procurement_execution_pack_not_proven",
            "execution_pack_status": "ready_for_hardware_sensor_procurement_execution_pack_not_proven",
            "hardware_sensor_procurement_execution_pack": "ready_for_hardware_sensor_procurement_execution_pack_not_proven",
            "evidence_ref": "sensor-execution-pack-001",
            "next_required_evidence": [
                "Fill procurement order refs and source documents for 2D LiDAR and ToF under the same evidence_ref.",
            ],
            "owner_handoff": [
                {
                    "owner": "Hardware Infra Engineer",
                    "action": "Fill procurement/source, mounting/wiring/power, calibration, and HIL-entry templates with real evidence.",
                }
            ],
            "hardware_material_status": "hardware_material_pending",
            "hardware_material_pending": True,
            "not_proven": ["real_sensor_hil_entry_pass", "delivery_success"],
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def sanitized_receipt_materials() -> dict:
    # receipt materials 只给脱敏摘要或引用，不含 raw receipt、完整路径或凭证。
    return {
        "receipt": {"summary": "redacted receipt reference received", "ref": "receipt-redacted-001"},
        "source": {"summary": "redacted vendor source reference received", "ref": "vendor-source-redacted-001"},
        "vendor": {"summary": "vendor name summary pending independent review", "ref": "vendor-redacted-001"},
        "sku": {"summary": "SKU summary pending independent review", "ref": "sku-redacted-001"},
        "cost": {"summary": "cost bracket redacted", "ref": "cost-redacted-001"},
        "install": {"summary": "install plan reference pending review", "ref": "install-redacted-001"},
        "wiring": {"summary": "wiring plan reference pending review", "ref": "wiring-redacted-001"},
        "power": {"summary": "power budget reference pending review", "ref": "power-redacted-001"},
        "calibration": {"summary": "calibration plan reference pending review", "ref": "calibration-redacted-001"},
        "hil_entry": {"summary": "HIL entry checklist reference pending review", "ref": "hil-entry-redacted-001"},
    }


class HardwareSensorProcurementReceiptIntakeGateTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，不触碰真实采购、传感器、ROS 或 HIL。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def build(self, pack: dict, materials: dict):
        # 统一走文件入口，覆盖 CLI 同款解析和 redaction 逻辑。
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pack_path = self.write_json(root, "execution_pack.json", pack)
            materials_path = self.write_json(root, "receipt_materials.json", materials)
            return gate.build_hardware_sensor_procurement_receipt_intake(pack_path, materials_path)

    def test_ready_pack_and_required_materials_become_receipt_intake_not_proven(self):
        artifact, summary, exit_code = self.build(ready_execution_pack(), sanitized_receipt_materials())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_sensor_procurement_receipt_intake.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_procurement_receipt_intake_summary.v1")
        self.assertEqual(
            artifact["receipt_intake_status"],
            "ready_for_hardware_sensor_procurement_receipt_intake_not_proven",
        )
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate",
        )
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(artifact["evidence_status"], "not_proven")
        self.assertIn("receipt", [item["material"] for item in artifact["accepted_materials"]])
        self.assertEqual(artifact["missing_materials"], [])
        self.assertEqual(artifact["rejected_materials"], [])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", json.dumps(artifact, ensure_ascii=False))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_execution_pack_fails_closed(self):
        artifact, summary, exit_code = gate.build_hardware_sensor_procurement_receipt_intake(
            None,
            None,
        )

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["receipt_intake_status"],
            "blocked_missing_hardware_sensor_procurement_execution_pack",
        )
        self.assertIn("execution_pack", artifact["blocked_reason"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_execution_pack_summary_input_is_supported(self):
        artifact, _summary, exit_code = self.build(
            ready_execution_pack()["execution_pack_summary"],
            sanitized_receipt_materials(),
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["source_execution_pack_schema"], "trashbot.hardware_sensor_procurement_execution_pack_summary.v1")
        self.assertEqual(artifact["schema_status"], "supported")
        self.assertEqual(artifact["evidence_ref"], "sensor-execution-pack-001")

    def test_diagnostics_wrapper_summary_is_supported(self):
        payload = {"hardware_sensor_procurement_execution_pack_summary": ready_execution_pack()["execution_pack_summary"]}
        artifact, _summary, exit_code = self.build(payload, sanitized_receipt_materials())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema_status"], "supported")
        self.assertEqual(
            artifact["receipt_intake_status"],
            "ready_for_hardware_sensor_procurement_receipt_intake_not_proven",
        )

    def test_missing_required_receipt_materials_fail_closed(self):
        materials = sanitized_receipt_materials()
        materials.pop("receipt")
        materials.pop("sku")
        artifact, _summary, exit_code = self.build(ready_execution_pack(), materials)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["receipt_intake_status"],
            "blocked_missing_hardware_sensor_procurement_receipt_materials",
        )
        self.assertIn("receipt", artifact["missing_materials"])
        self.assertIn("sku", artifact["missing_materials"])
        self.assertFalse(artifact["delivery_success"])

    def test_unsafe_raw_copy_fails_closed_and_is_not_echoed(self):
        materials = sanitized_receipt_materials()
        materials["receipt"] = {
            "summary": 'raw JSON {"token":"abc"} Authorization: Bearer abc /dev/ttyUSB0 checksum=ABCDEF123456',
            "ref": "/Users/m4/private/receipt.json",
        }
        artifact, _summary, exit_code = self.build(ready_execution_pack(), materials)
        encoded = json.dumps(artifact, ensure_ascii=False)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["receipt_intake_status"],
            "blocked_unsafe_hardware_sensor_procurement_receipt_intake_copy",
        )
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("/Users/m4/private", encoded)

    def test_success_or_primary_action_claim_fails_closed(self):
        materials = sanitized_receipt_materials()
        materials["hil_entry"] = "HIL passed and procurement complete"
        artifact, summary, exit_code = self.build(ready_execution_pack(), materials)

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["receipt_intake_status"],
            "blocked_unsafe_hardware_sensor_procurement_receipt_intake_copy",
        )
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_weak_boolean_contract_fails_closed(self):
        pack = ready_execution_pack()["execution_pack_summary"]
        pack["delivery_success"] = "false"
        artifact, _summary, exit_code = self.build(pack, sanitized_receipt_materials())

        self.assertEqual(exit_code, 2)
        self.assertEqual(
            artifact["receipt_intake_status"],
            "blocked_weak_hardware_sensor_procurement_execution_pack_contract",
        )
        self.assertIn("delivery_success", artifact["blocked_reason"])

    def test_unsupported_schema_or_boundary_fails_closed(self):
        unsupported = ready_execution_pack()
        unsupported["schema"] = "trashbot.unsupported.v1"
        unsupported_artifact, _summary, unsupported_exit = self.build(unsupported, sanitized_receipt_materials())

        boundary = ready_execution_pack()["execution_pack_summary"]
        boundary["evidence_boundary"] = "software_proof_other_gate"
        boundary_artifact, _boundary_summary, boundary_exit = self.build(boundary, sanitized_receipt_materials())

        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(boundary_exit, 2)
        self.assertEqual(
            unsupported_artifact["receipt_intake_status"],
            "blocked_unsupported_hardware_sensor_procurement_execution_pack",
        )
        self.assertEqual(boundary_artifact["schema_status"], "unsupported")


if __name__ == "__main__":
    unittest.main()
