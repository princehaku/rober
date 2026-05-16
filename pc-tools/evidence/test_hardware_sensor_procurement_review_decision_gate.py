#!/usr/bin/env python3
"""hardware_sensor_procurement_review_decision gate 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import hardware_sensor_procurement_review_decision_gate as gate  # noqa: E402


def ready_intake() -> dict:
    # fixture 模拟上一轮 intake 已收齐材料形状，但仍然不能证明真实采购或 HIL。
    return {
        "schema": "trashbot.hardware_sensor_procurement_intake_gate.v1",
        "schema_version": 1,
        "source": "software_proof",
        "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_intake_gate",
        "overall_status": "ready_for_hardware_sensor_procurement_review_not_proven",
        "hardware_sensor_procurement_intake": "ready_for_hardware_sensor_procurement_review_not_proven",
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "missing_materials": [],
        "placeholder_materials": [],
        "review_summary": {
            "schema": "trashbot.hardware_sensor_procurement_intake_summary.v1",
            "schema_version": 1,
            "source_schema": "trashbot.hardware_sensor_procurement_intake_gate.v1",
            "source": "software_proof",
            "evidence_boundary": "software_proof_docker_hardware_sensor_procurement_intake_gate",
            "source_evidence_boundary": "software_proof_docker_hardware_sensor_procurement_intake_gate",
            "status": "ready_for_hardware_sensor_procurement_review_not_proven",
            "hardware_sensor_procurement_intake": "ready_for_hardware_sensor_procurement_review_not_proven",
            "hardware_material_status": "hardware_material_pending",
            "sensor_materials": [
                {
                    "sensor": "2D LiDAR",
                    "sku_status": "present_not_proven",
                    "vendor_source_status": "present_not_proven",
                    "procurement_status": "quote_received_not_ordered",
                    "mounting_status": "present_not_proven",
                    "wiring_status": "present_not_proven",
                    "calibration_status": "present_not_proven",
                    "hil_entry_status": "present_not_proven",
                    "field_status": "not_proven",
                },
                {
                    "sensor": "ToF",
                    "sku_status": "present_not_proven",
                    "vendor_source_status": "present_not_proven",
                    "procurement_status": "quote_received_not_ordered",
                    "mounting_status": "present_not_proven",
                    "wiring_status": "present_not_proven",
                    "calibration_status": "present_not_proven",
                    "hil_entry_status": "present_not_proven",
                    "channel_count": 4,
                    "channel_count_source_status": "present_not_proven",
                    "field_status": "not_proven",
                },
            ],
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


class HardwareSensorProcurementReviewDecisionGateTest(unittest.TestCase):
    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # 测试只写临时 JSON，不污染真实 evidence bundle。
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def build(self, payload: dict):
        # 统一走文件入口，覆盖 CLI 同款解析路径。
        with tempfile.TemporaryDirectory() as td:
            path = self.write_json(Path(td), "intake.json", payload)
            return gate.build_hardware_sensor_procurement_review_decision(path, evidence_ref="sensor-review-test")

    def test_ready_intake_becomes_review_ready_not_proven(self):
        artifact, summary, exit_code = self.build(ready_intake())

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_sensor_procurement_review_decision.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_procurement_review_decision_summary.v1")
        self.assertEqual(artifact["review_decision"], "ready_for_procurement_review_not_proven")
        self.assertEqual(summary["hardware_sensor_procurement_review_decision"], "ready_for_procurement_review_not_proven")
        self.assertEqual(artifact["evidence_boundary"], "software_proof_docker_hardware_sensor_procurement_review_decision_gate")
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertTrue(artifact["hardware_material_pending"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertIn("real_sensor_hil_entry_pass", artifact["not_proven"])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", json.dumps(artifact, ensure_ascii=False))
        self.assertIn("rerun_commands", summary)

    def test_missing_intake_fails_closed_with_review_blocker(self):
        artifact, summary, exit_code = gate.build_hardware_sensor_procurement_review_decision(None)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], "blocked_missing_hardware_sensor_procurement_intake")
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("hardware_sensor_procurement_intake_gate.py", " ".join(artifact["rerun_commands"]))

    def test_procurement_source_gaps_map_to_hardware_handoff(self):
        payload = ready_intake()
        payload["overall_status"] = "blocked_missing_required_sensor_materials"
        payload["review_summary"]["status"] = "blocked_missing_required_sensor_materials"
        payload["review_summary"]["missing_materials"] = [
            "2D LiDAR.sku",
            "2D LiDAR.source_document",
            "ToF.channel_count_source",
        ]
        artifact, _summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], "blocked_missing_procurement_materials")
        self.assertEqual(artifact["blockers"][0]["category"], "procurement_source_material")
        self.assertIn("2D LiDAR.sku", artifact["blockers"][0]["fields"])
        self.assertIn("next_required_evidence", artifact)
        self.assertIn("Hardware Infra Engineer", json.dumps(artifact["owner_handoff"], ensure_ascii=False))

    def test_mounting_wiring_calibration_gaps_map_to_installation_decision(self):
        payload = ready_intake()
        payload["overall_status"] = "blocked_missing_required_sensor_materials"
        payload["review_summary"]["status"] = "blocked_missing_required_sensor_materials"
        payload["review_summary"]["missing_materials"] = [
            "2D LiDAR.mounting_plan",
            "ToF.wiring_plan",
            "ToF.power_budget",
            "ToF.calibration_plan",
            "ToF.hil_entry_material",
        ]
        artifact, _summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], "blocked_missing_mounting_wiring_calibration")
        self.assertEqual(artifact["blockers"][0]["category"], "mounting_wiring_power_calibration_hil_entry")
        self.assertIn("ToF.hil_entry_material", artifact["blockers"][0]["fields"])

    def test_summary_only_input_is_supported_and_stays_fail_closed(self):
        summary = ready_intake()["review_summary"]
        summary["status"] = "blocked_missing_required_sensor_materials"
        summary["sensor_materials"][0]["sku_status"] = "missing"
        artifact, _summary, exit_code = self.build(summary)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["source_intake_schema"], "trashbot.hardware_sensor_procurement_intake_summary.v1")
        self.assertEqual(artifact["review_decision"], "blocked_missing_procurement_materials")
        self.assertIn("2D LiDAR.sku", artifact["blockers"][0]["fields"])

    def test_unsupported_or_success_claim_fails_closed(self):
        payload = ready_intake()
        payload["schema"] = "trashbot.other.v1"
        artifact, _summary, exit_code = self.build(payload)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_decision"], "blocked_unsupported_hardware_sensor_procurement_intake")

        success_payload = ready_intake()
        success_payload["note"] = "delivery_success=true and LiDAR field pass"
        success_artifact, _success_summary, success_exit = self.build(success_payload)
        self.assertEqual(success_exit, 2)
        self.assertEqual(success_artifact["review_decision"], "blocked_unsupported_hardware_sensor_procurement_intake")
        self.assertFalse(success_artifact["delivery_success"])
        self.assertFalse(success_artifact["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
