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
    def test_corrected_phase0_no_go_manifest_is_explicit_and_unconsumed(self) -> None:
        """corrected 红门必须补齐 remote/deploy 计数，并拒绝把背景反馈算成任务证据。"""
        module = load_module()

        manifest = module.build_corrected_phase0_no_go_manifest(
            # 固定授权与 task identity，便于 Product/Algorithm 对账。
            authorization_id="ceo_20260721_1048_corrected_phase0_bounded_mission_v1",
            task_id="o6-o7-corrected-phase0-20260721-1050",
            # stop capability 未证明为 stop-only 时必须在动作前失败。
            phase0={"READINESS_GO": False, "first_failure": "base_stop_contract_not_proven_stop_only"},
            # 账本只包含只读兼容门，不包含动作 pipe。
            command_ledger=[{"phase": "phase0", "category": "upper_capability_readback", "exit_code": 0}],
            # final readback 可含背景反馈，但 current 任务计数不得提升。
            final_readback={
                "base_status": {"fresh_background_t1001_count": 12},
                "existing_services_and_holders_preserved": True,
            },
            # SHA mismatch 作为显式事实保留，不要求部署对齐。
            local_remote_sha={"upper_match": False, "capability_accepted": False},
        )

        # 新 schema 防止与上一轮错误探针产物混淆。
        self.assertEqual(manifest["schema"], module.CORRECTED_BOUNDED_MISSION_SCHEMA)
        # pre-stop 为零时授权状态与布尔位必须同时表达未消费。
        self.assertEqual(manifest["authorization_state"], "unconsumed_phase0_no_go")
        self.assertFalse(manifest["authorization_consumed"])
        # 背景反馈只能留在 final readback，不能进入 current 计数。
        self.assertEqual(manifest["t1001_observed_count"], 0)
        # cleanup 必须证明既有 services/holders 没有被本轮改变。
        self.assertTrue(manifest["cleanup"]["existing_services_and_holders_preserved"])
        for key in (
            # direct mutation/action/retry 字段都必须显式存在且为零。
            "pre_stop_invocation_count",
            "user_action_receipt_count",
            "navigate_to_pose_invocation_count",
            "post_stop_invocation_count",
            "remote_write_count",
            "deploy_count",
            "uart_open_count",
            "uart_write_count",
            "retry_count",
            "second_goal_count",
        ):
            self.assertEqual(manifest[key], 0, key)

    def test_corrected_phase0_no_go_builder_rejects_green_gate(self) -> None:
        """全绿 gate 不能偷走 NO-GO 路径，必须交给唯一 live pipe。"""
        module = load_module()

        with self.assertRaisesRegex(ValueError, "rejects_readiness_go"):
            # 专用 NO-GO builder 拒绝绿门，避免调用方跳过唯一 live runner。
            module.build_corrected_phase0_no_go_manifest(
                # 这些值只用于证明 fail-fast，不会生成 artifact。
                authorization_id="bounded-motion-test",
                task_id="task-test",
                phase0={"READINESS_GO": True},
                command_ledger=[],
                final_readback={},
                local_remote_sha={},
            )

    def test_corrected_attempt_manifest_consumes_authorization_once(self) -> None:
        """全绿后唯一 pipe 必须是 1/1/1/1，direct UART 与 retry 仍为零。"""
        module = load_module()

        manifest = module.build_corrected_bounded_mission_attempt_manifest(
            # identity 都由冻结 runner 提供，构造器不重新生成 action id。
            authorization_id="ceo_20260721_1048_corrected_phase0_bounded_mission_v1",
            task_id="task-current",
            action_id="action-current",
            phase0={"READINESS_GO": True},
            command_ledger=[],
            action={
                # 四个主调用都恰好一次，且无 retry/second goal。
                "pre_stop_invocation_count": 1,
                # receipt 必须排在 goal 之前，由 runner 时间戳证明顺序。
                "user_action_receipt_count": 1,
                # goal count 只记录 NavigateToPose，不包含 planner-only path。
                "navigate_to_pose_invocation_count": 1,
                # post-stop 必须在 finally 中恰好一次。
                "post_stop_invocation_count": 1,
                # terminal success 时不需要额外 cancel。
                "cancel_invocation_count": 0,
                # feedback latest 只读一次，避免隐藏 retry。
                "feedback_sample_invocation_count": 1,
                "retry_count": 0,
                "second_goal_count": 0,
                "goal_accepted": True,
                # route progress 与 terminal 必须各自存在才可推导 success。
                "terminal_status": "succeeded",
                "route_progress": {"observed": True},
                "user_action_receipt": {"status": "recorded"},
            },
            final_readback={
                # route success 还必须看到 final stopped 与 clean cleanup。
                "final_stopped": True,
                "cleanup_completed": True,
                "goal_active": False,
                "existing_services_and_holders_preserved": True,
                "final_stop_confirmation": "upper_stop_only_confirmed",
            },
            local_remote_sha={"capability_accepted": True},
        )

        # pre-stop 发出后授权只能是 consumed。
        self.assertTrue(manifest["authorization_consumed"])
        self.assertEqual(manifest["pre_stop_invocation_count"], 1)
        self.assertEqual(manifest["navigate_to_pose_invocation_count"], 1)
        self.assertEqual(manifest["post_stop_invocation_count"], 1)
        self.assertEqual(manifest["uart_open_count"], 0)
        self.assertEqual(manifest["uart_write_count"], 0)
        self.assertTrue(manifest["mission_attempt"])
        self.assertTrue(manifest["route_execution_success"])
        self.assertFalse(manifest["delivery_success"])

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
