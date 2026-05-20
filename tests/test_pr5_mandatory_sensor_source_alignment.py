#!/usr/bin/env python3
"""pr5_mandatory_sensor_source_alignment gate 的 focused unittest。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


# pc-tools 目录不是 Python package；测试直接导入同源 gate，避免复制实现逻辑。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

import pr5_mandatory_sensor_source_alignment as gate  # noqa: E402


# 测试约束 01：live repo 测试必须证明 canonical schema 和 boundary 不漂移。
# 测试约束 02：live repo 测试必须证明 PRRT_kwDOSWB9286CJ3tX 仍被显式引用。
# 测试约束 03：live repo 测试必须证明 hardware_material_pending 保留。
# 测试约束 04：live repo 测试必须证明 not_proven 保留。
# 测试约束 05：live repo 测试必须证明 safe_to_control=false 保留。
# 测试约束 06：live repo 测试必须证明 delivery_success=false 保留。
# 测试约束 07：live repo 测试必须证明 primary_actions_enabled=false 保留。
# 测试约束 08：live repo 测试必须证明 default hardware 未混入 LiDAR/ToF。
# 测试约束 09：live repo 测试必须证明 missing_materials 仍要求真实 2D LiDAR。
# 测试约束 10：live repo 测试必须证明 thread resolved 仍在 not_proven 缺口。
# 测试约束 11：temp ready 测试避免依赖真实 vendor 目录可写状态。
# 测试约束 12：temp ready 测试只证明 source alignment，不证明硬件履约。
# 测试约束 13：missing vendor citation 测试保护 docs/vendor/VENDOR_INDEX.md 入口。
# 测试约束 14：missing source file 测试保护本地 vendor refs 漂移。
# 测试约束 15：unsafe 测试保护 delivery_success=true 不能进入 ready path。
# 测试约束 16：unsafe 测试保护 PR thread resolved 肯定式不能进入 ready path。
# 测试约束 17：sanitization 测试保护输出不泄漏 /Users/ 本机路径。
# 测试约束 18：sanitization 测试保护输出不泄漏 /dev/tty 串口路径。
# 测试约束 19：sanitization 测试保护输出不泄漏 /dev/serial 串口路径。
# 测试约束 20：测试 fixture 只放最小语义 pattern，不复制完整 vendor 源码。
# 测试约束 21：临时 source ref 通过参数注入，避免修改真实 vendor 文件。
# 测试约束 22：临时 boundary 保留 Default Hardware Set 与 target baseline 分层。
# 测试约束 23：临时 vendor index 保留 Source Of Truth Order 和 Complete Material Coverage。
# 测试约束 24：所有测试都在本地文件系统完成，不需要 ROS2、硬件、Docker 或网络。
# 测试约束 25：失败测试必须断言 exit_code=2，避免 blocked 被误当 success。
# 测试约束 26：ready 测试必须断言 status 仍是 ready_not_proven。
# 测试约束 27：summary safe_copy 必须包含 thread id，便于下游只读展示。
# 测试约束 28：source boundary 测试必须确认 docs/vendor/VENDOR_INDEX.md 出现在输出。
# 测试约束 29：测试不调用 CLI 写仓库文件，避免污染 sprint evidence。
# 测试约束 30：测试文件的技术注释使用中文，符合仓库硬件任务注释约束。

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
The current local vendor files do not prove that a project 2D LiDAR or ToF
ring has been purchased, physically mounted, wired to the Orange Pi/WAVE ROVER,
calibrated, accepted into Nav2, or passed HIL.

Evidence state: `hardware_material_pending`, `not_proven`.

## PR #5 Mandatory Sensor Source Alignment Gate

`pr5_mandatory_sensor_source_alignment` answers PR #5 thread
`PRRT_kwDOSWB9286CJ3tX` with source-boundary evidence only.

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

## Source Of Truth Order

1. Local vendor files under `docs/vendor/`.

Hardware stack: Orange Pi Zero 3 and Waveshare WAVE ROVER.
Upper/lower controller link: UART, newline-delimited JSON.

## Complete Material Coverage

- Orange Pi Zero 3 user manual and schematic.
- WAVE ROVER chassis, firmware, and vendor app references.
"""


def source_ref(root: Path, domain: str, relative: str, text: str, patterns: tuple[str, ...]) -> dict[str, object]:
    # 测试源文件只保留最小 pattern，验证 gate 的 source-check 分支和 fail-closed 行为。
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {"domain": domain, "path": path, "patterns": patterns, "note": f"{domain} test source"}


class Pr5MandatorySensorSourceAlignmentTest(unittest.TestCase):
    def build_temp_sources(self, root: Path) -> tuple[Path, Path, tuple[dict[str, object], ...]]:
        # 临时 source set 避免测试依赖真实硬件或可写 vendor 目录。
        boundary = root / "production_hardware_boundary.md"
        vendor = root / "VENDOR_INDEX.md"
        boundary.write_text(BOUNDARY_MD, encoding="utf-8")
        vendor.write_text(VENDOR_INDEX, encoding="utf-8")
        refs = (
            source_ref(root, "readme", "README.md", "upper computer communicates with the lower computer using JSON commands via GPIO UART. AI vision and strategy planning. Real-time video.", (r"JSON commands via GPIO UART",)),
            source_ref(root, "base_ctrl", "base_ctrl.py", "serial.Serial json.loads json.dumps lidar_ser parse_lidar_frame", (r"serial\.Serial", r"lidar_ser")),
            source_ref(root, "config", "config.yaml", "use_lidar: false\ncmd_movition_ctrl: 1\ncmd_pwm_ctrl: 11\nvideo:\ncv:\n", (r"use_lidar:\s*false", r"video:", r"cv:")),
            source_ref(root, "json_cmd", "json_cmd.h", "#define CMD_SPEED_CTRL 1\n#define CMD_ROS_CTRL 13\n#define CMD_BASE_FEEDBACK 130\nCMD_BASE_FEEDBACK_FLOW", (r"CMD_SPEED_CTRL\s+1", r"CMD_ROS_CTRL\s+13")),
        )
        return boundary, vendor, refs

    def test_live_repo_docs_generate_canonical_alignment_not_proven(self):
        artifact, summary, exit_code = gate.build_pr5_mandatory_sensor_source_alignment()

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.pr5_mandatory_sensor_source_alignment.v1")
        self.assertEqual(summary["schema"], "trashbot.pr5_mandatory_sensor_source_alignment_summary.v1")
        self.assertEqual(artifact["thread_id"], "PRRT_kwDOSWB9286CJ3tX")
        self.assertEqual(artifact["evidence_boundary"], "software_proof_docker_pr5_mandatory_sensor_source_alignment_gate")
        self.assertEqual(artifact["overall_status"], "not_proven")
        self.assertEqual(artifact["hardware_material_status"], "hardware_material_pending")
        self.assertEqual(summary["mandatory_sensor_assumptions"]["material_state"], "hardware_material_pending")
        self.assertFalse(summary["mandatory_sensor_assumptions"]["default_hardware_includes_lidar_or_tof"])
        self.assertIn("real_2d_lidar_sku_source_receipt", artifact["missing_materials"])
        self.assertIn("pr5_review_thread_resolved", artifact["not_proven"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_temp_sources_ready_but_still_not_proven(self):
        with tempfile.TemporaryDirectory() as td:
            boundary, vendor, refs = self.build_temp_sources(Path(td))
            artifact, summary, exit_code = gate.build_pr5_mandatory_sensor_source_alignment(boundary, vendor, refs)

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["alignment_status"], "ready_for_pr5_mandatory_sensor_source_alignment_not_proven")
        self.assertEqual(summary["vendor_source_boundary"]["entrypoint"], "docs/vendor/VENDOR_INDEX.md")
        self.assertEqual(summary["vendor_source_boundary"]["lidar_tof_boundary"], "hardware_material_pending_not_proven")
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", summary["safe_copy"]["zh"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])

    def test_missing_vendor_citation_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            boundary, vendor, refs = self.build_temp_sources(Path(td))
            boundary.write_text(BOUNDARY_MD.replace("docs/vendor/VENDOR_INDEX.md", "vendor notes"), encoding="utf-8")
            artifact, summary, exit_code = gate.build_pr5_mandatory_sensor_source_alignment(boundary, vendor, refs)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["alignment_status"], "blocked_missing_pr5_mandatory_sensor_source_alignment_boundary")
        self.assertIn("boundary.boundary_cites_vendor_index.missing", artifact["missing_alignment_items"])
        self.assertEqual(summary["overall_status"], "not_proven")
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])

    def test_missing_source_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            boundary, vendor, refs = self.build_temp_sources(Path(td))
            Path(refs[0]["path"]).unlink()
            artifact, _summary, exit_code = gate.build_pr5_mandatory_sensor_source_alignment(boundary, vendor, refs)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["alignment_status"], "blocked_missing_pr5_mandatory_sensor_source_alignment_source")
        self.assertIn("readme.missing", artifact["missing_source_items"])
        self.assertFalse(artifact["safe_to_control"])

    def test_unsafe_success_or_resolution_claim_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            boundary, vendor, refs = self.build_temp_sources(Path(td))
            boundary.write_text(BOUNDARY_MD + "\nUnsafe: delivery_success=true and PRRT_kwDOSWB9286CJ3tX resolved.\n", encoding="utf-8")
            artifact, _summary, exit_code = gate.build_pr5_mandatory_sensor_source_alignment(boundary, vendor, refs)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["alignment_status"], "blocked_unsafe_pr5_mandatory_sensor_source_alignment_claim")
        self.assertIn("pr5_review_thread_resolved", artifact["not_proven"])
        self.assertFalse(artifact["delivery_success"])

    def test_artifact_and_summary_do_not_emit_raw_paths_or_serial_devices(self):
        artifact, summary, exit_code = gate.build_pr5_mandatory_sensor_source_alignment()
        serialized = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)

        self.assertEqual(exit_code, 0)
        self.assertNotIn("/Users/", serialized)
        self.assertNotIn("/dev/tty", serialized)
        self.assertNotIn("/dev/serial", serialized)
        self.assertIn("docs/vendor/VENDOR_INDEX.md", serialized)


if __name__ == "__main__":
    unittest.main()
