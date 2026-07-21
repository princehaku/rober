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
    def test_phase0_no_go_manifest_keeps_authorization_unconsumed(self) -> None:
        """Phase 0 未全绿时所有动作计数必须为零，授权也不能被误标为已消费。"""
        module = load_module()

        manifest = module.build_phase0_no_go_manifest(
            # 授权身份必须原样进入冻结产物。
            authorization_id="ceo-2026-07-21-bounded-motion",
            # 测试只提供第一个门禁失败，不伪造其余绿门。
            phase0={"first_failure": "upper_health_wrong_port"},
            # 命令账本保留原始非零 exit 便于追责。
            command_ledger=[{"phase": "phase0", "exit_code": 7}],
            # 最终 base 状态仍必须保持 fail-closed。
            final_readback={"base_status": {"safe_to_control": False}},
        )

        # schema 与固定目标是 Product/Algorithm 的机器消费入口。
        self.assertEqual(manifest["schema"], module.BOUNDED_MISSION_SCHEMA)
        self.assertEqual(manifest["target"], module.BOUNDED_MISSION_TARGET)
        self.assertFalse(manifest["READINESS_GO"])
        # 未发 pre-stop 是 authorization unconsumed 的唯一可靠边界。
        self.assertEqual(manifest["authorization_state"], "unconsumed_phase0_no_go")
        for key in (
            # 逐项检查危险计数，避免只断言一个总计数漏字段。
            "pre_stop_invocation_count",
            "navigate_to_pose_invocation_count",
            "post_stop_invocation_count",
            "service_mutation_count",
            "uart_open_count",
            "uart_write_count",
            "retry_count",
            "second_goal_count",
        ):
            self.assertEqual(manifest[key], 0, key)

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

    def test_managed_bridge_command_uses_field_http_wave_rover_defaults(self) -> None:
        """helper 自启动 runtime 时必须沿用当前现场可跑的 HTTP + WAVE ROVER 机型口径。"""
        module = load_module()

        command = module.managed_esp32_bridge_command(
            "/tmp/feedback.jsonl",
            "/tmp/command.jsonl",
            "pwm",
        )

        self.assertIn("-p command_transport:=http", command)
        self.assertIn("-p wave_rover_http_base_url:=http://192.168.1.3", command)
        self.assertIn("-p main_type:=1", command)
        self.assertIn("-p module_type:=0", command)
        self.assertIn("-p pwm_min_abs:=164", command)
        self.assertIn("-p pwm_max_abs:=164", command)


if __name__ == "__main__":
    unittest.main()
