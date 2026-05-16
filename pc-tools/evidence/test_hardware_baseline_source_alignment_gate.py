#!/usr/bin/env python3
"""hardware_baseline_source_alignment gate 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import hardware_baseline_source_alignment_gate as gate  # noqa: E402


BOUNDARY_MD = """# Production Hardware Boundary

## Default Hardware Set

- WAVE ROVER mobile chassis.
- Orange Pi Zero 3 upper computer.
- Portable WiFi or local network access.
- Monocular 1080p camera (default semantic evidence sensor).
- Microphone.
- Speaker or buzzer.

## Vendor/Source Attribution Boundary

Hardware facts must start from `docs/vendor/VENDOR_INDEX.md`.
The current local vendor tree does not prove that a project 2D LiDAR or ToF
ring has been purchased, physically mounted, wired to the Orange Pi/WAVE ROVER,
calibrated, accepted into Nav2, or passed HIL.

Evidence state: `hardware_material_pending`, `not_proven`.

## Navigation/Sensing Baseline (Product Target, Procurement Validation Pending)

- Target baseline combo: monocular camera + one 2D LiDAR + ToF safety ring.
  The monocular camera is the current default semantic evidence sensor; the 2D
  LiDAR and ToF ring are target hardware pending procurement/source
  attribution, mounting, wiring, calibration, and HIL evidence.
- ToF product target: 2 channels minimum, 4 channels recommended
  (front/back/left/right). These channel counts are product acceptance targets,
  not local vendor or HIL-proven facts.
- Responsibility split:
  - 2D LiDAR: target primary SLAM/Nav2 mapping + localization input after
    procurement validation and calibration evidence.
  - Monocular camera: elevator door/target-floor semantic evidence, snapshots and operator diagnostics.
  - ToF: target near-field collision safety and conservative enter/exit
    gating after wiring and HIL checks; it is not a primary SLAM source.
"""

VENDOR_INDEX = """# Vendor Hardware and Software Reference Index

Directory: `docs/vendor/`
Hardware stack: Orange Pi Zero 3 and Waveshare WAVE ROVER.
Upper/lower controller link: UART, newline-delimited JSON.
Camera material exists as vendor app/tutorial coverage.

## Complete Material Coverage

- Orange Pi Zero 3 user manual and schematic.
- WAVE ROVER chassis, firmware, and vendor app references.
"""


class HardwareBaselineSourceAlignmentGateTest(unittest.TestCase):
    def write_sources(self, root: Path, boundary_text: str = BOUNDARY_MD, vendor_text: str = VENDOR_INDEX) -> tuple[Path, Path]:
        # 测试只写临时 Markdown，避免依赖真实硬件、serial/UART 或仓库文档可写状态。
        boundary = root / "production_hardware_boundary.md"
        vendor = root / "VENDOR_INDEX.md"
        boundary.write_text(boundary_text, encoding="utf-8")
        vendor.write_text(vendor_text, encoding="utf-8")
        return boundary, vendor

    def test_live_repo_docs_are_source_aligned_not_proven(self):
        artifact, summary, exit_code = gate.build_hardware_baseline_source_alignment()

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_baseline_source_alignment.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_baseline_source_alignment_summary.v1")
        self.assertEqual(artifact["evidence_boundary"], "software_proof_docker_hardware_baseline_source_alignment_gate")
        self.assertEqual(artifact["overall_status"], "hardware_baseline_source_aligned_not_proven")
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(artifact["evidence_status"], "not_proven")
        self.assertFalse(artifact["default_hardware_set_summary"]["default_lidar_or_tof_included"])
        self.assertEqual(summary["vendor_source_boundary"]["lidar_tof_source_boundary"], "hardware_material_pending_not_proven")
        self.assertIn("real_sensor_hil_entry_pass", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_temp_sources_output_required_summaries(self):
        with tempfile.TemporaryDirectory() as td:
            boundary, vendor = self.write_sources(Path(td))
            artifact, summary, exit_code = gate.build_hardware_baseline_source_alignment(boundary, vendor)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["hardware_baseline_source_alignment"], "hardware_baseline_source_aligned_not_proven")
        self.assertIn("WAVE ROVER mobile chassis.", artifact["default_hardware_set_summary"]["items"])
        self.assertEqual(summary["target_sensor_baseline_summary"]["sensor_roles"]["ToF"], "target near-field collision safety and enter/exit gate; not primary SLAM source")
        self.assertEqual(summary["vendor_source_boundary"]["vendor_coverage"]["uart_json"], "covered_by_docs_vendor_index")
        self.assertEqual(artifact["missing_alignment_items"], [])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", json.dumps(artifact, ensure_ascii=False))

    def test_missing_vendor_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            boundary, vendor = self.write_sources(Path(td))
            vendor.unlink()
            artifact, summary, exit_code = gate.build_hardware_baseline_source_alignment(boundary, vendor)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_missing_hardware_baseline_source")
        self.assertIn("vendor_index.missing", artifact["missing_alignment_items"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_alignment_semantics_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            broken = BOUNDARY_MD.replace("docs/vendor/VENDOR_INDEX.md", "vendor notes").replace("hardware_material_pending", "installed")
            boundary, vendor = self.write_sources(Path(td), boundary_text=broken)
            artifact, _summary, exit_code = gate.build_hardware_baseline_source_alignment(boundary, vendor)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_missing_hardware_baseline_source_alignment")
        joined = " ".join(artifact["missing_alignment_items"])
        self.assertIn("product boundary cites docs/vendor/VENDOR_INDEX.md", joined)
        self.assertIn("hardware_material_pending", joined)

    def test_success_or_control_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            boundary, vendor = self.write_sources(
                Path(td),
                boundary_text=BOUNDARY_MD + "\nField claim: delivery_success=true and field_pass=true.\n",
            )
            artifact, _summary, exit_code = gate.build_hardware_baseline_source_alignment(boundary, vendor)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_success_or_control_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
