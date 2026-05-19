#!/usr/bin/env python3
"""pr5_review_thread_closeout gate 的顶层验收测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 不是 Python package；测试入口显式加入 evidence 目录以复用 CLI 同源逻辑。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import pr5_review_thread_closeout_gate as gate  # noqa: E402


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
- Acceptance rule: do not treat 2D LiDAR or ToF as part of the Default Hardware
  Set until the exact SKU, vendor/source document, procurement status,
  mechanical mount, wiring path, calibration method, and HIL result are linked
  from the relevant hardware runbook or sprint evidence.
"""

VENDOR_INDEX = """# Vendor Hardware and Software Reference Index

Hardware stack: Orange Pi Zero 3 and Waveshare WAVE ROVER.
Upper/lower controller link: UART, newline-delimited JSON.

## Complete Material Coverage

- Orange Pi Zero 3 user manual and schematic.
- WAVE ROVER chassis, firmware, and vendor app references.
"""

OKR_MD = """# rober OKR

## 4.1 当前 OKR 进度快照

| Objective | 当前进度 | 本轮证据与边界 | 主要缺口 |
| --- | --- | --- | --- |
| Objective 1：硬件协议可信底盘 | 约 81% | software_proof only | still missing HIL |
| Objective 5：云中转 + OSS/CDN 数据通路产品化（历史 O6） | 约 68% | software_proof only | external proof missing |

## 6. 当前最高优先级

- 下一轮按 `OKR.md` 4.1 重新排序。当前数值最低完成度仍是 Objective 5（约 68%），但只有拿到至少一种真实外部材料时才应继续推进 O5 completion。
"""


class Pr5ReviewThreadCloseoutGateTest(unittest.TestCase):
    def write_sources(
        self,
        root: Path,
        boundary_text: str = BOUNDARY_MD,
        vendor_text: str = VENDOR_INDEX,
        okr_text: str = OKR_MD,
    ) -> tuple[Path, Path, Path]:
        # 临时源只模拟 repo-local Markdown，不接触真实 GitHub、串口、ROS 或硬件。
        boundary = root / "production_hardware_boundary.md"
        vendor = root / "VENDOR_INDEX.md"
        okr = root / "OKR.md"
        boundary.write_text(boundary_text, encoding="utf-8")
        vendor.write_text(vendor_text, encoding="utf-8")
        okr.write_text(okr_text, encoding="utf-8")
        return boundary, vendor, okr

    def decisions_by_key(self, artifact: dict) -> dict[str, str]:
        # 用 key 索引避免测试依赖输出顺序之外的展示细节。
        return {item["thread_key"]: item["decision"] for item in artifact["thread_decisions"]}

    def test_live_repo_docs_generate_closeout_summary_not_proven(self):
        artifact, summary, exit_code = gate.build_pr5_review_thread_closeout()

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.pr5_review_thread_closeout.v1")
        self.assertEqual(summary["schema"], "trashbot.pr5_review_thread_closeout_summary.v1")
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["evidence_boundary"], "software_proof_docker_pr5_review_thread_closeout_gate")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        decisions = self.decisions_by_key(artifact)
        self.assertEqual(
            decisions["p1_production_hardware_boundary_default_vs_mandatory_sensor_baseline"],
            "ready_to_close_on_mainline_docs",
        )
        self.assertEqual(
            decisions["p2_okr_lowest_objective_narrative_vs_table"],
            "ready_to_close_on_mainline_docs",
        )
        self.assertEqual(
            decisions["p2_mandatory_sensor_assumptions_missing_vendor_citation"],
            "blocked_pending_real_materials",
        )
        self.assertIn("docs/vendor/VENDOR_INDEX.md#Complete Material Coverage", json.dumps(summary, ensure_ascii=False))

    def test_temp_sources_match_expected_three_thread_decisions(self):
        with tempfile.TemporaryDirectory() as td:
            boundary, vendor, okr = self.write_sources(Path(td))
            artifact, summary, exit_code = gate.build_pr5_review_thread_closeout(boundary, vendor, okr)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["closeout_status"], "pr5_review_thread_closeout_not_proven")
        self.assertEqual(summary["overall_status"], "not_proven")
        decisions = self.decisions_by_key(artifact)
        self.assertEqual(set(decisions.values()), {"ready_to_close_on_mainline_docs", "blocked_pending_real_materials"})
        self.assertIn("real_hil_entry", artifact["missing_real_materials"])
        self.assertIn("real_wave_rover_uart_hil", artifact["not_proven"])

    def test_output_dir_writes_default_artifact_and_summary_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            boundary, vendor, okr = self.write_sources(root)
            output_dir = root / "evidence"

            exit_code = gate.main(
                [
                    "--boundary-md",
                    str(boundary),
                    "--vendor-index",
                    str(vendor),
                    "--okr-md",
                    str(okr),
                    "--output-dir",
                    str(output_dir),
                ]
            )

            artifact_path = output_dir / "pr5_review_thread_closeout.json"
            summary_path = output_dir / "pr5_review_thread_closeout_summary.json"
            self.assertEqual(exit_code, 0)
            self.assertTrue(artifact_path.exists())
            self.assertTrue(summary_path.exists())
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            # 新 CLI 只是路径兼容；输出仍必须保持软件证明和未验证硬件边界。
            self.assertEqual(artifact["source"], "software_proof")
            self.assertEqual(summary["overall_status"], "not_proven")
            self.assertFalse(artifact["delivery_success"])
            self.assertFalse(summary["primary_actions_enabled"])

    def test_okr_lowest_mismatch_fails_that_thread_closed(self):
        with tempfile.TemporaryDirectory() as td:
            broken_okr = OKR_MD.replace("当前数值最低完成度仍是 Objective 5（约 68%）", "当前数值最低完成度仍是 Objective 1（约 81%）")
            boundary, vendor, okr = self.write_sources(Path(td), okr_text=broken_okr)
            artifact, _summary, exit_code = gate.build_pr5_review_thread_closeout(boundary, vendor, okr)

        self.assertEqual(exit_code, 2)
        decisions = self.decisions_by_key(artifact)
        self.assertEqual(
            decisions["p2_okr_lowest_objective_narrative_vs_table"],
            "still_open_missing_current_evidence",
        )
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_default_hardware_lidar_tof_conflict_stays_open(self):
        with tempfile.TemporaryDirectory() as td:
            broken_boundary = BOUNDARY_MD.replace("- Speaker or buzzer.", "- Speaker or buzzer.\n- 2D LiDAR.")
            boundary, vendor, okr = self.write_sources(Path(td), boundary_text=broken_boundary)
            artifact, _summary, exit_code = gate.build_pr5_review_thread_closeout(boundary, vendor, okr)

        self.assertEqual(exit_code, 2)
        decisions = self.decisions_by_key(artifact)
        self.assertEqual(
            decisions["p1_production_hardware_boundary_default_vs_mandatory_sensor_baseline"],
            "still_open_missing_current_evidence",
        )

    def test_missing_vendor_fails_closed_for_all_threads(self):
        with tempfile.TemporaryDirectory() as td:
            boundary, vendor, okr = self.write_sources(Path(td))
            vendor.unlink()
            artifact, summary, exit_code = gate.build_pr5_review_thread_closeout(boundary, vendor, okr)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["closeout_status"], "blocked_missing_pr5_review_thread_closeout_repo_evidence")
        self.assertTrue(all(item["decision"] == "still_open_missing_current_evidence" for item in artifact["thread_decisions"]))
        self.assertEqual(summary["source_load_status"]["vendor_index"], "missing")

    def test_unsupported_thread_summary_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            boundary, vendor, okr = self.write_sources(Path(td))
            summary_path = Path(td) / "thread_summary.json"
            summary_path.write_text(json.dumps({"schema": "wrong", "threads": []}), encoding="utf-8")
            artifact, _summary, exit_code = gate.build_pr5_review_thread_closeout(boundary, vendor, okr, summary_path)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["closeout_status"], "blocked_unsupported_pr5_review_thread_summary")
        self.assertIn("thread_summary.unsupported_schema", artifact["thread_summary_issues"])

    def test_success_or_control_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            unsafe_boundary = BOUNDARY_MD + "\nUnsafe claim: delivery_success=true and hil_pass=true.\n"
            boundary, vendor, okr = self.write_sources(Path(td), boundary_text=unsafe_boundary)
            artifact, _summary, exit_code = gate.build_pr5_review_thread_closeout(boundary, vendor, okr)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["closeout_status"], "blocked_unsafe_pr5_review_thread_closeout_claim")
        self.assertTrue(all(item["decision"] == "still_open_missing_current_evidence" for item in artifact["thread_decisions"]))


if __name__ == "__main__":
    unittest.main()
