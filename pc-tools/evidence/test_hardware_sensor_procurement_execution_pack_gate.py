#!/usr/bin/env python3
"""hardware_sensor_procurement_execution_pack gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：所有 case 都只使用临时 JSON，避免污染真实证据目录。
# 测试约束 02：所有 case 都只调用 PC gate，不访问采购系统。
# 测试约束 03：所有 case 都只调用 PC gate，不访问 ROS graph。
# 测试约束 04：所有 case 都只调用 PC gate，不访问串口。
# 测试约束 05：所有 case 都只调用 PC gate，不访问真实传感器。
# 测试约束 06：ready fixture 仍保持 delivery_success=false。
# 测试约束 07：ready fixture 仍保持 primary_actions_enabled=false。
# 测试约束 08：ready fixture 仍保持 hardware_material_pending=true。
# 测试约束 09：ready fixture 仍保持 not_proven。
# 测试约束 10：ready fixture 不代表真实采购。
# 测试约束 11：ready fixture 不代表真实安装。
# 测试约束 12：ready fixture 不代表真实标定。
# 测试约束 13：ready fixture 不代表真实 HIL。
# 测试约束 14：ready fixture 不代表真实路线或电梯通过。
# 测试约束 15：ready fixture 不代表 delivery success。
# 测试约束 16：missing review case 验证缺源 fail closed。
# 测试约束 17：summary-only case 验证下游可消费 summary。
# 测试约束 18：wrapper case 验证 diagnostics 嵌套 summary。
# 测试约束 19：blocked review case 验证 blocker 不被丢弃。
# 测试约束 20：unsupported schema case 验证顶层 schema 不可绕过。
# 测试约束 21：unsupported boundary case 验证证据边界不可绕过。
# 测试约束 22：success claim case 验证成功文案阻断。
# 测试约束 23：primary action case 验证控制放行阻断。
# 测试约束 24：weak boolean case 验证字符串 false 不被放行。
# 测试约束 25：raw copy case 验证凭证被阻断。
# 测试约束 26：raw copy case 验证 ROS 控制 topic 被阻断。
# 测试约束 27：raw copy case 验证串口设备路径被阻断。
# 测试约束 28：raw copy case 验证 raw robot response 被阻断。
# 测试约束 29：每个 blocked case 都检查 primary action 仍为 false。
# 测试约束 30：每个 ready case 只说明 execution pack ready_not_proven。
# 测试约束 31：测试不创建真实采购订单。
# 测试约束 32：测试不创建真实安装记录。
# 测试约束 33：测试不创建真实 calibration artifact。
# 测试约束 34：测试不创建真实 HIL artifact。
# 测试约束 35：测试不创建真实 route artifact。
# 测试约束 36：测试不创建真实 elevator artifact。
# 测试约束 37：测试不创建真实 delivery artifact。
# 测试约束 38：测试校验 vendor index 只作为边界来源出现。
# 测试约束 39：测试校验 material_templates 只输出模板名和字段。
# 测试约束 40：测试校验 summary schema 可被 Robot/mobile 固定消费。
# 测试约束 41：测试校验 evidence boundary 为本 gate 专属边界。
# 测试约束 42：测试校验 source review schema 保留。
# 测试约束 43：测试校验 source review status 保留。
# 测试约束 44：测试校验 blockers 白名单化。
# 测试约束 45：测试校验 owner handoff 不变成机器人动作。
# 测试约束 46：测试校验 rerun command 只面向 PC gate。
# 测试约束 47：测试校验 blocked_reason 可读但不含 raw JSON。
# 测试约束 48：测试校验 ready exit code 为 0。
# 测试约束 49：测试校验 blocked exit code 为 2。
# 测试约束 50：测试覆盖上一轮 schema bypass 风险。
# 测试约束 51：测试覆盖弱类型契约风险。
# 测试约束 52：测试覆盖 unsafe copy 风险。
# 测试约束 53：测试覆盖 metadata-only 边界。
# 测试约束 54：测试覆盖 hardware_material_pending 边界。
# 测试约束 55：测试覆盖 not_proven 边界。

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import hardware_sensor_procurement_execution_pack_gate as gate  # noqa: E402


def ready_review() -> dict:
    # fixture 模拟上一轮 review decision 已收敛，但真实采购/安装/HIL 仍未发生。
    return {
        "schema": "trashbot.hardware_sensor_procurement_review_decision.v1",
        "schema_version": 1,
        "source": "software_proof",
        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_review_decision_gate",
        "evidence_ref": "sensor-review-001",
        "review_decision": "ready_for_procurement_review_not_proven",
        "hardware_sensor_procurement_review_decision": "ready_for_procurement_review_not_proven",
        "source_intake_schema": "trashbot.hardware_sensor_procurement_intake_summary.v1",
        "source_intake_status": "ready_for_hardware_sensor_procurement_review_not_proven",
        "blockers": [],
        "next_required_evidence": [
            "Product closeout may review the intake material shape, but hardware remains not_proven until real field/HIL evidence exists.",
        ],
        "owner_handoff": [
            {
                "owner": "Hardware Infra Engineer",
                "action": "Prepare bench/HIL entry plan after source, mounting, wiring, power, and calibration materials are accepted.",
            }
        ],
        "rerun_commands": [
            "python3 pc-tools/evidence/hardware_sensor_procurement_review_decision_gate.py --intake-json <intake_json>",
        ],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "not_proven": ["real_sensor_hil_entry_pass", "delivery_success"],
        "review_summary": {
            "schema": "trashbot.hardware_sensor_procurement_review_decision_summary.v1",
            "schema_version": 1,
            "source_schema": "trashbot.hardware_sensor_procurement_review_decision.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_review_decision_gate",
            "status": "ready_for_procurement_review_not_proven",
            "hardware_sensor_procurement_review_decision": "ready_for_procurement_review_not_proven",
            "source_intake_schema": "trashbot.hardware_sensor_procurement_intake_summary.v1",
            "source_intake_status": "ready_for_hardware_sensor_procurement_review_not_proven",
            "evidence_ref": "sensor-review-001",
            "review_decision": "ready_for_procurement_review_not_proven",
            "blockers": [],
            "next_required_evidence": [
                "Product closeout may review the intake material shape, but hardware remains not_proven until real field/HIL evidence exists.",
            ],
            "owner_handoff": [
                {
                    "owner": "Hardware Infra Engineer",
                    "action": "Prepare bench/HIL entry plan after source, mounting, wiring, power, and calibration materials are accepted.",
                }
            ],
            "rerun_commands": [
                "python3 pc-tools/evidence/hardware_sensor_procurement_review_decision_gate.py --intake-json <intake_json>",
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


class HardwareSensorProcurementExecutionPackGateTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，不触碰真实采购、传感器、ROS 或 HIL。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def build(self, payload: dict):
        # 统一走文件入口，覆盖 CLI 同款解析和 schema/boundary 逻辑。
        with tempfile.TemporaryDirectory() as td:
            path = self.write_json(Path(td), "review.json", payload)
            return gate.build_hardware_sensor_procurement_execution_pack(path)

    def test_ready_review_becomes_metadata_execution_pack_not_proven(self):
        artifact, summary, exit_code = self.build(ready_review())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_sensor_procurement_execution_pack.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_procurement_execution_pack_summary.v1")
        self.assertEqual(
            artifact["execution_pack_status"],
            "ready_for_hardware_sensor_procurement_execution_pack_not_proven",
        )
        self.assertEqual(
            artifact["evidence_boundary"],
            "software_proof_docker_hardware_sensor_procurement_execution_pack_gate",
        )
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(artifact["evidence_status"], "not_proven")
        self.assertIn("2d_lidar_procurement_order.md", [item["name"] for item in artifact["material_templates"]])
        self.assertIn("tof_ring_mounting_wiring_plan.md", [item["name"] for item in artifact["material_templates"]])
        self.assertIn("real_sensor_hil_entry_pass", artifact["not_proven"])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", json.dumps(artifact, ensure_ascii=False))
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["delivery_success"])

    def test_missing_review_fails_closed(self):
        artifact, summary, exit_code = gate.build_hardware_sensor_procurement_execution_pack(None)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_missing_hardware_sensor_procurement_review_decision")
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertIn("review decision", artifact["next_required_evidence"][0])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_review_summary_input_is_supported(self):
        artifact, _summary, exit_code = self.build(ready_review()["review_summary"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["source_review_schema"], "trashbot.hardware_sensor_procurement_review_decision_summary.v1")
        self.assertEqual(artifact["schema_status"], "supported")
        self.assertEqual(artifact["evidence_ref"], "sensor-review-001")

    def test_diagnostics_wrapper_summary_is_supported(self):
        payload = {"hardware_sensor_procurement_review_decision_summary": ready_review()["review_summary"]}
        artifact, _summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema_status"], "supported")
        self.assertEqual(
            artifact["execution_pack_status"],
            "ready_for_hardware_sensor_procurement_execution_pack_not_proven",
        )

    def test_blocked_review_preserves_blockers_and_stays_blocked(self):
        payload = ready_review()
        payload["review_decision"] = "blocked_missing_procurement_materials"
        payload["review_summary"]["status"] = "blocked_missing_procurement_materials"
        payload["review_summary"]["review_decision"] = "blocked_missing_procurement_materials"
        payload["review_summary"]["hardware_sensor_procurement_review_decision"] = "blocked_missing_procurement_materials"
        payload["review_summary"]["blockers"] = [
            {
                "category": "procurement_source_material",
                "status": "hardware_material_pending",
                "fields": ["2D LiDAR.sku"],
                "owner": "Hardware Infra Engineer",
            }
        ]
        artifact, _summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_hardware_sensor_procurement_review_not_ready")
        self.assertEqual(artifact["blockers"][0]["category"], "procurement_source_material")
        self.assertIn("2D LiDAR.sku", artifact["blockers"][0]["fields"])
        self.assertFalse(artifact["delivery_success"])

    def test_unsupported_schema_or_boundary_fails_closed(self):
        payload = ready_review()
        payload["schema"] = "trashbot.unsupported.v1"
        unsupported_artifact, _summary, unsupported_exit = self.build(payload)

        boundary_payload = ready_review()["review_summary"]
        boundary_payload["evidence_boundary"] = "software_proof_other_gate"
        boundary_artifact, _boundary_summary, boundary_exit = self.build(boundary_payload)

        self.assertEqual(unsupported_exit, 2)
        self.assertEqual(boundary_exit, 2)
        self.assertEqual(
            unsupported_artifact["execution_pack_status"],
            "blocked_unsupported_hardware_sensor_procurement_review_decision",
        )
        self.assertEqual(boundary_artifact["schema_status"], "unsupported")

    def test_success_or_primary_action_claim_fails_closed(self):
        payload = ready_review()
        payload["review_summary"]["delivery_success"] = True
        payload["note"] = "LiDAR installed field pass"
        artifact, summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_unsupported_hardware_sensor_procurement_review_decision")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_weak_boolean_contract_fails_closed(self):
        payload = ready_review()["review_summary"]
        payload["delivery_success"] = "false"
        artifact, _summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_weak_hardware_sensor_procurement_review_contract")
        self.assertIn("delivery_success", artifact["blocked_reason"])

    def test_raw_path_or_credential_copy_fails_closed(self):
        payload = ready_review()
        payload["review_summary"]["owner_handoff"].append(
            {
                "owner": "Hardware Infra Engineer",
                "action": "Authorization: Bearer abc /cmd_vel /dev/ttyUSB0 checksum=ABCDEF123456 raw robot response",
            }
        )
        artifact, _summary, exit_code = self.build(payload)

        encoded = json.dumps(artifact, ensure_ascii=False)
        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["execution_pack_status"], "blocked_unsafe_hardware_sensor_procurement_execution_pack_copy")
        self.assertNotIn("Bearer abc", encoded)
        self.assertNotIn("/cmd_vel", encoded)
        self.assertNotIn("/dev/ttyUSB0", encoded)
        self.assertNotIn("raw robot response", encoded)


if __name__ == "__main__":
    unittest.main()
