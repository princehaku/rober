#!/usr/bin/env python3
"""O11 Nav2 执行证明 helper 的轻量合同测试。"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPT_DIR / "o11_nav2_goal_execution_proof.py"


def load_module():
    """按脚本路径加载，避免测试依赖 ROS2 Python 环境。"""
    spec = importlib.util.spec_from_file_location("o11_nav2_goal_execution_proof_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("o11_nav2_goal_execution_proof.py module spec was not created")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class O11Nav2GoalExecutionProofTest(unittest.TestCase):
    def test_existing_runtime_mode_reuse_summary_detects_mismatch(self) -> None:
        """请求 ROS 但现场 bridge 是 PWM 时，必须把复用错位写进 artifact。"""
        module = load_module()

        summary = module.existing_runtime_mode_reuse_summary(
            {"base_command_mode": "pwm"},
            "ros",
        )

        self.assertEqual(summary["requested_base_command_mode"], "ros")
        self.assertFalse(summary["base_command_mode_matches_request"])
        self.assertTrue(summary["base_command_mode_mismatch_reused"])
        self.assertIn("实际模式 pwm", summary["base_command_mode_reuse_plain"])
        self.assertIn("请求 ros 未切换", summary["base_command_mode_reuse_plain"])

    def test_existing_runtime_mode_reuse_summary_accepts_matching_mode(self) -> None:
        """实际 bridge 模式匹配请求时，复用 runtime 不应被标为模式错位。"""
        module = load_module()

        summary = module.existing_runtime_mode_reuse_summary(
            {"base_command_mode": "pwm"},
            "pwm",
        )

        self.assertEqual(summary["requested_base_command_mode"], "pwm")
        self.assertTrue(summary["base_command_mode_matches_request"])
        self.assertFalse(summary["base_command_mode_mismatch_reused"])


if __name__ == "__main__":
    unittest.main()
