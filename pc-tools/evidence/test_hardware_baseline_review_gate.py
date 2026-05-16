#!/usr/bin/env python3
"""hardware_baseline_review gate 的离线围栏测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import hardware_baseline_review_gate as gate  # noqa: E402


BASELINE_MD = """# Production Hardware Boundary

## Navigation/Sensing Baseline (Mandatory for current MVP)

- Evidence state: `hardware_material_pending`, `not_proven`.
- Target baseline combo: monocular camera + one 2D LiDAR + ToF safety ring.
- Responsibility split:
  - 2D LiDAR: target primary SLAM/Nav2 mapping + localization input after procurement validation.
  - Monocular camera: elevator door/target-floor semantic evidence, snapshots and operator diagnostics.
  - ToF: target near-field collision safety and conservative enter/exit
    gating after wiring and HIL checks; it is not a primary SLAM source.
"""


class HardwareBaselineReviewGateTest(unittest.TestCase):
    def write_boundary(self, root: Path, text: str) -> Path:
        # 测试只写临时 Markdown，避免依赖真实传感器、Nav2 runtime 或仓库文档可写状态。
        path = root / "production_hardware_boundary.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_supported_baseline_outputs_autonomy_responsibility_summary(self):
        with tempfile.TemporaryDirectory() as td:
            boundary = self.write_boundary(Path(td), BASELINE_MD)
            artifact, summary, exit_code = gate.build_hardware_baseline_review(boundary)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.hardware_baseline_review_gate.v1")
        self.assertEqual(summary["schema"], "trashbot.hardware_baseline_review_summary.v1")
        self.assertEqual(artifact["hardware_baseline_review"], "hardware_baseline_review_not_proven")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(artifact["evidence_status"], "not_proven")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

        sensors = {item["sensor"]: item for item in artifact["sensor_responsibility_summary"]}
        self.assertEqual(sensors["2D LiDAR"]["autonomy_chain"], "SLAM/Nav2 main chain")
        self.assertEqual(sensors["2D LiDAR"]["material_status"], "hardware_material_pending")
        self.assertEqual(sensors["monocular"]["autonomy_chain"], "elevator/floor semantic evidence")
        self.assertTrue(sensors["ToF"]["not_primary_mapping_input"])
        self.assertEqual(sensors["ToF"]["field_status"], "not_proven")
        self.assertIn("real_tof_field_pass", artifact["not_proven"])

    def test_missing_sensor_phrase_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            boundary = self.write_boundary(Path(td), BASELINE_MD.replace("ToF: target near-field", "ToF: placeholder"))
            artifact, summary, exit_code = gate.build_hardware_baseline_review(boundary)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_incomplete_sensor_responsibility_baseline")
        self.assertIn("ToF target near-field collision safety gate", " ".join(artifact["missing_required_phrases"]))
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_file_fails_closed_with_required_phrases(self):
        with tempfile.TemporaryDirectory() as td:
            artifact, _summary, exit_code = gate.build_hardware_baseline_review(Path(td) / "missing.md")

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_missing_production_hardware_boundary")
        self.assertEqual(len(artifact["missing_required_phrases"]), len(gate.REQUIRED_BASELINE_RULES))
        self.assertIn("not_proven", json.dumps(artifact, ensure_ascii=False))

    def test_success_or_control_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            boundary = self.write_boundary(
                Path(td),
                BASELINE_MD + "\nField claim: delivery_success=true and ToF field pass.\n",
            )
            artifact, _summary, exit_code = gate.build_hardware_baseline_review(boundary)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["overall_status"], "blocked_success_or_control_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
