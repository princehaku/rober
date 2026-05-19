#!/usr/bin/env python3
"""pr5_vendor_source_review_packet gate 的顶层验收测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 package；测试显式导入同源 CLI，避免复制 gate 逻辑。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import pr5_vendor_source_review_packet as gate  # noqa: E402


BOUNDARY_MD = """# Production Hardware Boundary

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
- Acceptance rule: do not treat 2D LiDAR or ToF as part of the Default Hardware
  Set until the exact SKU, vendor/source document, procurement status,
  mechanical mount, wiring path, calibration method, and HIL result are linked
  from the relevant hardware runbook or sprint evidence.
"""


class Pr5VendorSourceReviewPacketTest(unittest.TestCase):
    def test_live_repo_docs_generate_thread_specific_packet(self):
        artifact, summary, exit_code = gate.build_pr5_vendor_source_review_packet()

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.pr5_vendor_source_review_packet.v1")
        self.assertEqual(summary["schema"], "trashbot.pr5_vendor_source_review_packet_summary.v1")
        self.assertEqual(artifact["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["evidence_boundary"], "software_proof_docker_pr5_vendor_source_review_packet_gate")
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertIn("real_2d_lidar_sku_source_receipt", artifact["missing_materials"])
        self.assertIn("docs/vendor/VENDOR_INDEX.md", json.dumps(summary, ensure_ascii=False))
        self.assertIn("2D LiDAR", summary["safe_copy"]["zh"])
        self.assertIn("ToF", summary["safe_copy"]["zh"])

    def test_temp_boundary_without_vendor_citation_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            boundary = Path(td) / "production_hardware_boundary.md"
            boundary.write_text(BOUNDARY_MD.replace("docs/vendor/VENDOR_INDEX.md", "vendor docs"), encoding="utf-8")
            artifact, summary, exit_code = gate.build_pr5_vendor_source_review_packet(boundary)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_packet_status"], "blocked_missing_pr5_vendor_source_review_context")
        self.assertIn("boundary_cites_vendor_index.missing", artifact["missing_review_context"])
        self.assertEqual(summary["overall_status"], "not_proven")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_temp_boundary_matching_context_still_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            boundary = Path(td) / "production_hardware_boundary.md"
            boundary.write_text(BOUNDARY_MD, encoding="utf-8")
            artifact, summary, exit_code = gate.build_pr5_vendor_source_review_packet(boundary)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["review_packet_status"], "ready_for_pr5_vendor_source_review_packet_not_proven")
        self.assertEqual(summary["hardware_material_status"], "hardware_material_pending")
        self.assertIn("tof_procurement", summary["not_proven"])
        self.assertIn("real_sensor_hil_entry", summary["missing_materials"])

    def test_success_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            boundary = Path(td) / "production_hardware_boundary.md"
            boundary.write_text(BOUNDARY_MD + "\nUnsafe: delivery_success=true and hil_pass=true.\n", encoding="utf-8")
            artifact, _summary, exit_code = gate.build_pr5_vendor_source_review_packet(boundary)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["review_packet_status"], "blocked_unsafe_pr5_vendor_source_review_packet_claim")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_cli_writes_artifact_and_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            boundary = root / "production_hardware_boundary.md"
            boundary.write_text(BOUNDARY_MD, encoding="utf-8")
            artifact_path = root / "packet.json"
            summary_path = root / "summary.json"

            exit_code = gate.main(
                [
                    "--boundary-md",
                    str(boundary),
                    "--output",
                    str(artifact_path),
                    "--summary-output",
                    str(summary_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            # CLI 写出的文件仍是软件证明，不包含真实硬件通过含义。
            self.assertEqual(artifact["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
            self.assertEqual(summary["evidence_status"], "not_proven")
            self.assertFalse(summary["delivery_success"])
            self.assertFalse(summary["primary_actions_enabled"])


if __name__ == "__main__":
    unittest.main()
