#!/usr/bin/env python3
"""real_material_readiness_board gate 的离线围栏测试。"""

from __future__ import annotations

# 测试约束 01：ready case 只是 software_proof，不证明真实材料到位。
# 测试约束 02：四类材料组必须同时出现，避免某个 blocker 被遗漏。
# 测试约束 03：PR #5 unresolved thread 必须保留原始安全标识。
# 测试约束 04：硬件组必须引用 vendor source boundary，但不能声明 SKU 或电气实证。
# 测试约束 05：summary 必须能给 Robot/mobile 只读消费。
# 测试约束 06：缺 docs/vendor/VENDOR_INDEX.md 必须 fail closed。
# 测试约束 07：输出必须保持 delivery_success=false。
# 测试约束 08：输出必须保持 primary_actions_enabled=false 和 safe_to_control=false。

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "pc-tools" / "evidence" / "real_material_readiness_board.py"
SPEC = importlib.util.spec_from_file_location("real_material_readiness_board", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gate)


class RealMaterialReadinessBoardTest(unittest.TestCase):
    def test_ready_board_contains_four_fail_closed_groups(self):
        artifact, summary, exit_code = gate.build_real_material_readiness_board()
        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        group_ids = {group["group_id"] for group in artifact["material_groups"]}

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["schema"], "trashbot.real_material_readiness_board.v1")
        self.assertEqual(summary["schema"], "trashbot.real_material_readiness_board_summary.v1")
        self.assertEqual(group_ids, {"o5_external", "objective_1_pr5_hardware", "pr4_route_elevator", "objective_4_real_phone"})
        self.assertEqual(artifact["source"], "software_proof")
        self.assertEqual(artifact["status"], "not_proven")
        self.assertEqual(artifact["material_status"], "blocked_pending_real_materials")
        self.assertIn("Objective 5", encoded)
        self.assertIn("Objective 1", encoded)
        self.assertIn("Objective 4", encoded)
        self.assertIn("PR #4", encoded)
        self.assertIn("PR #5", encoded)
        self.assertIn("PRRT_kwDOSWB9286CJ3tX", encoded)
        self.assertIn("unresolved", encoded)
        self.assertIn("blocked_pending_real_materials", encoded)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(artifact["primary_actions_enabled"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(artifact["safe_to_control"])
        self.assertFalse(summary["safe_to_control"])

    def test_hardware_group_uses_vendor_boundary_without_real_proof_claim(self):
        artifact, summary, _ = gate.build_real_material_readiness_board()
        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        hardware_group = next(group for group in artifact["material_groups"] if group["group_id"] == "objective_1_pr5_hardware")

        self.assertIn("docs/vendor/VENDOR_INDEX.md", encoded)
        self.assertIn("docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py", encoded)
        self.assertIn("docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h", encoded)
        self.assertEqual(hardware_group["owner"], "hardware-engineer")
        self.assertEqual(hardware_group["source"], "software_proof")
        self.assertEqual(hardware_group["status"], "not_proven")
        self.assertEqual(hardware_group["material_status"], "blocked_pending_real_materials")
        self.assertFalse(hardware_group["delivery_success"])
        self.assertFalse(hardware_group["primary_actions_enabled"])
        self.assertFalse(hardware_group["safe_to_control"])

    def test_pr4_group_matches_autonomy_read_only_consult_boundary(self):
        artifact, summary, _ = gate.build_real_material_readiness_board()
        encoded = json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False)
        pr4_group = next(group for group in artifact["material_groups"] if group["group_id"] == "pr4_route_elevator")

        self.assertEqual(pr4_group["owner"], "autonomy-engineer")
        self.assertEqual(pr4_group["group_status"], "blocked_missing_pr4_route_elevator_real_materials")
        self.assertEqual(pr4_group["blocking_reason"], "missing_real_route_elevator_field_materials")
        self.assertIn("Objective 2", pr4_group["source_refs"])
        self.assertIn("Objective 3", pr4_group["source_refs"])
        for category in [
            "real_elevator_door_state",
            "target_floor_confirmation",
            "human_assistance_record",
            "nav2_fixed_route_runtime_log",
            "field_task_record",
            "route_completion_signal",
            "dropoff_completion_material",
            "cancel_completion_material",
            "delivery_result",
        ]:
            self.assertIn(category, pr4_group["missing_material_categories"])
            self.assertIn(category, encoded)
        self.assertFalse(pr4_group["delivery_success"])
        self.assertFalse(pr4_group["primary_actions_enabled"])
        self.assertFalse(pr4_group["safe_to_control"])

    def test_missing_vendor_index_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            missing_vendor = Path(td) / "missing_VENDOR_INDEX.md"
            artifact, summary, exit_code = gate.build_real_material_readiness_board(vendor_index=missing_vendor)

        self.assertEqual(exit_code, 2)
        self.assertEqual(artifact["real_material_readiness_board"], "blocked_missing_vendor_index")
        self.assertEqual(summary["real_material_readiness_board"], "blocked_missing_vendor_index")
        self.assertEqual(summary["status"], "not_proven")
        self.assertFalse(summary["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])

    def test_cli_writes_artifact_and_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact_path = root / "real_material_readiness_board.json"
            summary_path = root / "real_material_readiness_board_summary.json"
            exit_code = gate.main(["--output", str(artifact_path), "--summary-output", str(summary_path)])
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(artifact["real_material_readiness_board"], summary["real_material_readiness_board"])
        self.assertEqual(summary["group_count"], 4)
        self.assertFalse(artifact["delivery_success"])
        self.assertFalse(summary["primary_actions_enabled"])
        self.assertFalse(summary["safe_to_control"])


if __name__ == "__main__":
    unittest.main()
