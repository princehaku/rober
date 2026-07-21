"""O11 Nav2 执行 helper 的静态单测。

这些测试不启动 ROS2、不打开串口，只锁定托管 runtime 的底盘参数和反馈摘要逻辑。
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o11_nav2_goal_execution_proof.py"
SPEC = importlib.util.spec_from_file_location("o11_nav2_goal_execution_proof", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


class O11Nav2GoalExecutionProofTests(unittest.TestCase):
    """锁定 O11 从 NavigateToPose 到真实底盘反馈的证明边界。"""

    def test_corrected_phase0_manifest_keeps_forbidden_surfaces_zero(self) -> None:
        """第二轮 corrected NO-GO 必须显式保留远端写入、部署和 UART 零计数。"""
        manifest = HELPER.build_corrected_phase0_no_go_manifest(
            # 当前授权只有 pre-stop 发出后才算消费。
            authorization_id="ceo_20260721_1048_corrected_phase0_bounded_mission_v1",
            task_id="o6-o7-corrected-phase0-20260721-1050",
            # 缺 current user receipt endpoint 时必须在动作 pipe 前封存。
            phase0={"READINESS_GO": False, "first_failure": "current_task_receipt_capability_missing"},
            # planner-only probe 可以出现，但 NavigateToPose 计数仍为零。
            command_ledger=[{"category": "compute_path_to_pose_planner_only", "exit_code": 0}],
            # holder preservation 是 cleanup 断言的一部分。
            final_readback={"existing_services_and_holders_preserved": True},
            local_remote_sha={"upper_match": False, "capability_accepted": False},
        )

        # 目标和授权必须与冻结 sprint 完全一致。
        self.assertEqual(manifest["target"], {"frame_id": "map", "x": 0.8, "y": 0.25, "yaw": 0.0})
        self.assertEqual(manifest["phase0_invocation_count"], 1)
        self.assertEqual(manifest["navigate_to_pose_invocation_count"], 0)
        self.assertEqual(manifest["remote_write_count"], 0)
        self.assertEqual(manifest["deploy_count"], 0)
        self.assertEqual(manifest["uart_open_count"], 0)
        self.assertEqual(manifest["uart_write_count"], 0)
        self.assertFalse(manifest["mission_attempt"])
        self.assertFalse(manifest["route_execution_success"])

    def test_corrected_attempt_rejects_retry_even_after_green_phase0(self) -> None:
        """全绿授权也不扩大为 retry；构造器必须在冻结 manifest 前拒绝。"""
        with self.assertRaisesRegex(ValueError, "retry_or_second_goal_forbidden"):
            HELPER.build_corrected_bounded_mission_attempt_manifest(
                # 其余 identity 只用于到达 retry 校验。
                authorization_id="bounded-motion-test",
                task_id="task-current",
                action_id="action-current",
                phase0={"READINESS_GO": True},
                command_ledger=[],
                action={
                    # pre-stop 已消费授权，但 retry=1 仍必须 fail closed。
                    "pre_stop_invocation_count": 1,
                    # 这里故意把 retry 置一，验证不会被静默 clamp。
                    "retry_count": 1,
                    # second goal 仍为零，隔离本用例的单一失败原因。
                    "second_goal_count": 0,
                },
                # 构造器应在使用 readback 前就拒绝错误 counter。
                final_readback={},
                local_remote_sha={},
            )

    def test_phase0_no_go_does_not_emit_current_mission_evidence(self) -> None:
        """只读准入失败不能消费授权，也不能借历史反馈提升 mission/HIL 字段。"""
        manifest = HELPER.build_phase0_no_go_manifest(
            # 测试授权只验证状态机，不授予任何真实动作。
            authorization_id="bounded-motion-test",
            # Phase 0 明确红门，构造器必须直接封存 NO-GO。
            phase0={"READINESS_GO": False},
            # 空账本用于证明构造器不会凭空产生调用。
            command_ledger=[],
            # 即使 final readback 含历史反馈，也不得算 current window。
            final_readback={"base_status": {"t1001_observed_count": 80}},
        )

        # mission、route 与 HIL 三层结论必须同时保持 false。
        self.assertFalse(manifest["mission_attempt"])
        self.assertFalse(manifest["route_execution_success"])
        self.assertFalse(manifest["hil_pass"])
        self.assertEqual(manifest["t1001_observed_count"], 0)
        self.assertEqual(manifest["feedback_sample_invocation_count"], 0)
        self.assertTrue(manifest["cleanup"]["completed"])
        self.assertEqual(manifest["cleanup"]["run_owned_residual_process_count"], 0)

    def test_managed_bridge_defaults_to_pwm_motion_path(self) -> None:
        """自动驾驶托管 bridge 默认走 vendor T=11 PWM164，不把雷达作为底盘发命令前置。"""
        command = HELPER.managed_esp32_bridge_command("/tmp/o11_feedback.jsonl", "/tmp/o11_command.jsonl")

        self.assertIn("ros2_trashbot_hardware esp32_bridge", command)
        self.assertIn("-p serial_port:=/dev/ttyS5", command)
        self.assertIn("-p command_mode:=pwm", command)
        self.assertIn("-p pwm_min_abs:=164", command)
        self.assertIn("-p pwm_max_abs:=164", command)
        self.assertIn("-p feedback_debug_log_path:=/tmp/o11_feedback.jsonl", command)
        self.assertIn("-p command_debug_log_path:=/tmp/o11_command.jsonl", command)
        self.assertNotIn("command_mode:=ros", command)
        self.assertNotIn("command_mode:=speed", command)

    def test_managed_bridge_can_override_to_pwm_motion_path(self) -> None:
        """现场需要 A/B 复验时仍可显式切回 vendor T=11 PWM 通路。"""
        command = HELPER.managed_esp32_bridge_command(
            "/tmp/o11_feedback.jsonl",
            "/tmp/o11_command.jsonl",
            "pwm",
        )

        self.assertIn("-p command_mode:=pwm", command)

    def test_wheel_zero_proof_status_tracks_actual_base_mode(self) -> None:
        """Nav2 已切到某个底盘模式后，L/R=0 的缺口必须跟随真实模式文案。"""
        self.assertEqual(
            "nav2_goal_succeeded_with_ros_commands_but_wheel_lr_zero",
            HELPER.wheel_zero_proof_status_for_mode("ros"),
        )
        self.assertEqual(
            "nav2_goal_succeeded_with_pwm_commands_but_wheel_lr_zero",
            HELPER.wheel_zero_proof_status_for_mode("pwm"),
        )
        self.assertEqual(
            "nav2_goal_succeeded_with_pwm_commands_but_wheel_lr_zero",
            HELPER.wheel_zero_proof_status_for_mode("not-a-mode"),
        )

    def test_feedback_debug_log_summary_proves_nonzero_wheel_feedback(self) -> None:
        """只有真实 T=1001 左右轮非零样本才能把 Nav2 HIL 证明推进为 true。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "feedback.jsonl"
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"left_speed": 0, "right_speed": 0, "observed_at_unix_s": 1.0}),
                        json.dumps({"left_speed": 90, "right_speed": 90, "observed_at_unix_s": 2.0}),
                        "not-json",
                    ]
                ),
                encoding="utf-8",
            )

            summary = HELPER.summarize_feedback_debug_log(str(log_path))

        self.assertTrue(summary["exists"])
        self.assertEqual(summary["sample_count"], 2)
        self.assertEqual(summary["nonzero_sample_count"], 1)
        self.assertEqual(summary["malformed_line_count"], 1)
        self.assertTrue(summary["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual(summary["latest_nonzero_pair"]["left_speed"], 90.0)
        self.assertEqual(summary["latest_nonzero_pair"]["right_speed"], 90.0)

    def test_feedback_debug_log_summary_accepts_vendor_frame_lr(self) -> None:
        """新 bridge 日志保留原始 vendor_frame；O11 要能直接用 T=1001 L/R 兜底复核。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "feedback.jsonl"
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"vendor_frame": {"T": 1001, "L": 0, "R": 0}, "observed_at_unix_s": 1.0}),
                        json.dumps({"vendor_frame": {"T": 1001, "L": 0.08, "R": 0.07}, "observed_at_unix_s": 2.0}),
                    ]
                ),
                encoding="utf-8",
            )

            summary = HELPER.summarize_feedback_debug_log(str(log_path))

        self.assertEqual(summary["sample_count"], 2)
        self.assertEqual(summary["nonzero_sample_count"], 1)
        self.assertTrue(summary["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual(summary["latest_nonzero_pair"]["left_speed"], 0.08)
        self.assertEqual(summary["latest_nonzero_pair"]["right_speed"], 0.07)

    def test_missing_feedback_log_does_not_claim_hil(self) -> None:
        """反馈日志缺失时保持 fail-closed，不能仅凭 action 成功推导 HIL。"""
        summary = HELPER.summarize_feedback_debug_log("/tmp/does-not-exist-o11-feedback.jsonl")

        self.assertFalse(summary["exists"])
        self.assertFalse(summary["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual(summary["reason"], "feedback_debug_log_unreadable")

    def test_feedback_debug_log_summary_uses_tail_window_for_large_logs(self) -> None:
        """现场反馈日志会到数百万行；O11 只能看最近窗口，不能全量读取导致上位机 OOM。"""
        original_tail_bytes = HELPER.DEBUG_LOG_TAIL_BYTES
        HELPER.DEBUG_LOG_TAIL_BYTES = 260
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                log_path = Path(temp_dir) / "feedback.jsonl"
                old_nonzero = json.dumps({"vendor_frame": {"T": 1001, "L": 8, "R": 8}, "observed_at_unix_s": 1.0})
                recent_zero_lines = [
                    json.dumps({"vendor_frame": {"T": 1001, "L": 0, "R": 0}, "observed_at_unix_s": float(index)})
                    for index in range(100, 110)
                ]
                log_path.write_text("\n".join([old_nonzero, *recent_zero_lines]), encoding="utf-8")

                summary = HELPER.summarize_feedback_debug_log(str(log_path))
        finally:
            HELPER.DEBUG_LOG_TAIL_BYTES = original_tail_bytes

        self.assertTrue(summary["exists"])
        self.assertTrue(summary["tail_truncated"])
        self.assertGreater(summary["file_bytes"], summary["tail_window_bytes"])
        self.assertFalse(summary["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual(summary["latest_pair"]["left_speed"], 0.0)
        self.assertIsNone(summary["latest_nonzero_pair"])

    def test_command_debug_log_summary_tracks_nonzero_vendor_commands(self) -> None:
        """命令日志用于区分 Nav2 没发非零速度，还是底盘反馈没有跟上。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "command.jsonl"
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"vendor_command": {"T": 11, "L": 0, "R": 0}, "linear_x": 0, "angular_z": 0}),
                        json.dumps({"vendor_command": {"T": 11, "L": 90, "R": 90}, "linear_x": 0.2, "angular_z": 0}),
                        "bad-json",
                    ]
                ),
                encoding="utf-8",
            )

            summary = HELPER.summarize_command_debug_log(str(log_path))

        self.assertTrue(summary["exists"])
        self.assertEqual(summary["sample_count"], 2)
        self.assertEqual(summary["nonzero_command_count"], 1)
        self.assertEqual(summary["malformed_line_count"], 1)
        self.assertTrue(summary["nonzero_command_observed"])
        self.assertEqual(summary["command_mode_counts"], {"pwm": 2})
        self.assertEqual(summary["latest_nonzero_command_mode"], "pwm")
        self.assertEqual(summary["latest_nonzero_command"]["vendor_command"], {"T": 11, "L": 90, "R": 90})

    def test_command_debug_log_summary_tracks_ros_t13_nonzero_commands(self) -> None:
        """ROS/T=13 重跑必须把 X/Z 非零计为底盘命令已到 bridge。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "command.jsonl"
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"command_mode": "ros", "vendor_command": {"T": 13, "X": 0, "Z": 0}, "linear_x": 0, "angular_z": 0}),
                        json.dumps({"command_mode": "ros", "vendor_command": {"T": 13, "X": 0.08, "Z": 0.0}, "linear_x": 0.08, "angular_z": 0}),
                    ]
                ),
                encoding="utf-8",
            )

            summary = HELPER.summarize_command_debug_log(str(log_path))

        self.assertEqual(summary["sample_count"], 2)
        self.assertEqual(summary["nonzero_command_count"], 1)
        self.assertTrue(summary["nonzero_command_observed"])
        self.assertEqual(summary["command_mode_counts"], {"ros": 2})
        self.assertEqual(summary["latest_nonzero_command_mode"], "ros")
        self.assertEqual(summary["latest_nonzero_command"]["vendor_command"], {"T": 13, "X": 0.08, "Z": 0.0})

    def test_extracts_bridge_debug_runtime_from_existing_process_args(self) -> None:
        """复用现场 bridge 时必须从进程参数找回 debug log，否则 Nav2 执行后看不见底盘证据。"""
        args_text = (
            "/opt/ros/humble/bin/ros2 run ros2_trashbot_hardware esp32_bridge --ros-args "
            "-p serial_port:=/dev/ttyS5 -p command_mode:=speed "
            "-p feedback_debug_log_path:=/tmp/o11_feedback.jsonl "
            "-p command_debug_log_path:=/tmp/o11_command.jsonl"
        )

        runtime = HELPER.bridge_debug_runtime_from_args(args_text)

        self.assertEqual("/tmp/o11_feedback.jsonl", runtime["base_feedback_log_path"])
        self.assertEqual("/tmp/o11_command.jsonl", runtime["base_command_log_path"])
        self.assertEqual("speed", runtime["base_command_mode"])

    def test_existing_runtime_process_probe_recommends_reuse_when_bridge_exists(self) -> None:
        """action list 在坏 graph 上可能超时；已有 bridge 进程时必须保守复用现场 runtime。"""
        fake_ps = "\n".join(
            [
                "101 /usr/bin/python3 /opt/ros/humble/bin/ros2 run ros2_trashbot_hardware esp32_bridge --ros-args "
                "-p serial_port:=/dev/ttyS5 -p command_mode:=ros "
                "-p feedback_debug_log_path:=/tmp/o11_feedback.jsonl "
                "-p command_debug_log_path:=/tmp/o11_command.jsonl",
                "202 /opt/ros/humble/lib/rclcpp_components/component_container_isolated --ros-args -r __node:=nav2_container",
            ]
        )
        completed = mock.Mock(returncode=0, stdout=fake_ps)

        with mock.patch.object(HELPER.subprocess, "run", return_value=completed):
            probe = HELPER.existing_runtime_process_probe()

        self.assertTrue(probe["checked"])
        self.assertTrue(probe["base_bridge_observed"])
        self.assertTrue(probe["nav2_observed"])
        self.assertTrue(probe["reuse_recommended"])
        self.assertEqual(probe["reason"], "existing_runtime_process_observed")
        self.assertTrue(probe["base_bridge_debug_log_paths_observed"])
        self.assertEqual("/tmp/o11_feedback.jsonl", probe["base_feedback_log_path"])
        self.assertEqual("/tmp/o11_command.jsonl", probe["base_command_log_path"])
        self.assertEqual("ros", probe["base_command_mode"])

    def test_reuse_existing_runtime_when_action_probe_times_out_but_process_exists(self) -> None:
        """NavigateToPose 探针失败也不能直接启动第二套 runtime；进程证据足够触发复用。"""
        action_probe = {
            "checked": True,
            "available": False,
            "reason": "existing_action_probe_failed",
            "error": {"type": "TimeoutExpired"},
        }
        process_probe = {
            "checked": True,
            "reuse_recommended": True,
            "reason": "existing_runtime_process_observed",
        }

        self.assertTrue(HELPER.should_reuse_existing_runtime(action_probe, process_probe))
        self.assertEqual(
            HELPER.existing_runtime_reuse_reason(action_probe, process_probe),
            "existing_runtime_process_observed",
        )

    def test_feedback_debug_log_tracks_imu_delta_separately_from_wheel_feedback(self) -> None:
        """IMU 姿态变化是运动迹象，不能被误包装成 L/R 轮速非零。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "feedback.jsonl"
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"left_speed": 0, "right_speed": 0, "roll": -1.6, "pitch": 0.3}),
                        json.dumps({"left_speed": 0, "right_speed": 0, "roll": -9.4, "pitch": 4.5}),
                    ]
                ),
                encoding="utf-8",
            )

            summary = HELPER.summarize_feedback_debug_log(str(log_path))

        self.assertFalse(summary["wheel_feedback_lr_nonzero_proven"])
        self.assertTrue(summary["imu_attitude_delta_observed"])
        self.assertGreater(summary["imu_attitude_delta_summary"]["max_abs_roll_delta"], 7.0)


if __name__ == "__main__":
    unittest.main()
