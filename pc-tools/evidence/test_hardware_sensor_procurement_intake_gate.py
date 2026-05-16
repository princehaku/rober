#!/usr/bin/env python3
"""hardware_sensor_procurement_intake gate 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import hardware_sensor_procurement_intake_gate as gate  # noqa: E402


VENDOR_INDEX = """# Vendor Hardware and Software Reference Index
docs/vendor/VENDOR_INDEX.md
Orange Pi Zero 3
WAVE ROVER
UART
camera
"""

BOUNDARY_MD = """# Production Hardware Boundary
Hardware facts must start from `docs/vendor/VENDOR_INDEX.md`.
Current coverage includes Orange Pi Zero 3, WAVE ROVER, UART, and camera references.
The current local vendor tree does not prove that a project 2D LiDAR or ToF ring
has been purchased, mounted, wired, calibrated, or HIL-proven.
"""


def complete_intake() -> dict:
    # fixture 代表未来真实材料已经填入，但测试仍保持 not_proven 和控制关闭。
    return {
        "sensors": {
            "2D LiDAR": {
                "sku": "Example-Lidar-A1",
                "vendor": "Example Robotics",
                "source_document": "docs/vendor/future_lidar/example_lidar_a1_datasheet.pdf",
                "procurement_status": "quote_received_not_ordered",
                "mounting_plan": "front upper deck bracket review packet",
                "wiring_plan": "USB data cable to Orange Pi Zero 3 host port",
                "power_budget": "5V 500mA budget review pending bench measurement",
                "calibration_plan": "laser frame to base_link static transform checklist",
                "hil_entry_material": "controlled bench spin plus Nav2 bag capture checklist",
            },
            "ToF": {
                "sku": "Example-ToF-Ring-4ch",
                "vendor": "Example Sensors",
                "source_document": "docs/vendor/future_tof/example_tof_ring_datasheet.pdf",
                "procurement_status": "quote_received_not_ordered",
                "mounting_plan": "front/back/left/right near-field bracket sketch",
                "wiring_plan": "I2C mux harness to Orange Pi GPIO header after voltage review",
                "power_budget": "3V3 sensor rail budget review pending bench measurement",
                "calibration_plan": "per-channel distance threshold and occlusion checklist",
                "hil_entry_material": "near-field stop-zone bench checklist",
                "channel_count": 4,
                "channel_count_source": "docs/vendor/future_tof/example_tof_ring_datasheet.pdf section channel map",
            },
        }
    }


class HardwareSensorProcurementIntakeGateTest(unittest.TestCase):
    def write_file(self, root: Path, name: str, text: str) -> Path:
        # 测试只写临时材料，避免污染真实 sprint evidence 或 vendor 目录。
        path = root / name
        path.write_text(text, encoding="utf-8")
        return path

    def write_json(self, root: Path, name: str, payload: dict) -> Path:
        # JSON fixture 走与 CLI 相同的文件入口，覆盖解析和校验路径。
        return self.write_file(root, name, json.dumps(payload, ensure_ascii=False))

    def test_complete_intake_outputs_not_proven_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intake = self.write_json(root, "intake.json", complete_intake())
            vendor = self.write_file(root, "VENDOR_INDEX.md", VENDOR_INDEX)
            boundary = self.write_file(root, "production_hardware_boundary.md", BOUNDARY_MD)
            artifact, summary, exit_code = gate.build_hardware_sensor_procurement_intake(intake, vendor, boundary)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_sensor_procurement_intake_gate.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_sensor_procurement_intake_summary.v1")
        self.assertEqual(summary["source_schema"], "trashbot.hardware_sensor_procurement_intake_gate.v1")
        self.assertEqual(
            summary["source_evidence_boundary"],
            "software_proof_docker_hardware_sensor_procurement_intake_gate",
        )
        self.assertEqual(artifact["hardware_sensor_procurement_intake"], "ready_for_hardware_sensor_procurement_review_not_proven")
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(artifact["evidence_status"], "not_proven")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", artifact["vendor_boundary_note"])
        self.assertIn("real_tof_channel_count_source_accepted", artifact["not_proven"])

        sensors = {item["sensor"]: item for item in summary["sensor_materials"]}
        self.assertEqual(sensors["2D LiDAR"]["vendor_source_status"], "present_not_proven")
        self.assertEqual(sensors["ToF"]["channel_count"], 4)
        self.assertEqual(sensors["ToF"]["channel_count_source_status"], "present_not_proven")

    def test_missing_intake_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            vendor = self.write_file(root, "VENDOR_INDEX.md", VENDOR_INDEX)
            boundary = self.write_file(root, "production_hardware_boundary.md", BOUNDARY_MD)
            artifact, summary, exit_code = gate.build_hardware_sensor_procurement_intake(None, vendor, boundary)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_missing_hardware_sensor_procurement_intake")
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_tof_channel_source_requires_pending_flag(self):
        payload = complete_intake()
        del payload["sensors"]["ToF"]["channel_count_source"]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intake = self.write_json(root, "intake.json", payload)
            vendor = self.write_file(root, "VENDOR_INDEX.md", VENDOR_INDEX)
            boundary = self.write_file(root, "production_hardware_boundary.md", BOUNDARY_MD)
            artifact, _summary, exit_code = gate.build_hardware_sensor_procurement_intake(intake, vendor, boundary)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_missing_required_sensor_materials")
        self.assertIn("ToF.channel_count requires channel_count_source", " ".join(artifact["missing_materials"]))

    def test_tof_channel_product_target_pending_flag_is_allowed_but_not_proven(self):
        payload = complete_intake()
        del payload["sensors"]["ToF"]["channel_count_source"]
        payload["sensors"]["ToF"]["channel_count_product_target_pending_validation"] = True
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intake = self.write_json(root, "intake.json", payload)
            vendor = self.write_file(root, "VENDOR_INDEX.md", VENDOR_INDEX)
            boundary = self.write_file(root, "production_hardware_boundary.md", BOUNDARY_MD)
            artifact, summary, exit_code = gate.build_hardware_sensor_procurement_intake(intake, vendor, boundary)

        self.assertEqual(exit_code, 0)
        self.assertEqual(summary["sensor_materials"][1]["channel_count_source_status"], "product_target_pending_validation")
        self.assertIn("not_proven", json.dumps(artifact, ensure_ascii=False))

    def test_placeholder_material_fails_closed(self):
        payload = complete_intake()
        payload["sensors"]["2D LiDAR"]["sku"] = "TBD"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intake = self.write_json(root, "intake.json", payload)
            vendor = self.write_file(root, "VENDOR_INDEX.md", VENDOR_INDEX)
            boundary = self.write_file(root, "production_hardware_boundary.md", BOUNDARY_MD)
            artifact, _summary, exit_code = gate.build_hardware_sensor_procurement_intake(intake, vendor, boundary)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_placeholder_sensor_materials")
        self.assertIn("2D LiDAR.sku", artifact["placeholder_materials"])

    def test_success_or_control_claim_fails_closed(self):
        payload = complete_intake()
        payload["claim"] = "delivery_success=true and hil_pass=true"
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intake = self.write_json(root, "intake.json", payload)
            vendor = self.write_file(root, "VENDOR_INDEX.md", VENDOR_INDEX)
            boundary = self.write_file(root, "production_hardware_boundary.md", BOUNDARY_MD)
            artifact, _summary, exit_code = gate.build_hardware_sensor_procurement_intake(intake, vendor, boundary)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_success_or_control_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
