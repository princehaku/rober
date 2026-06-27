"""O11 Nav2 执行 helper 的静态单测。

这些测试不启动 ROS2、不打开串口，只锁定托管 runtime 的底盘参数和反馈摘要逻辑。
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o11_nav2_goal_execution_proof.py"
SPEC = importlib.util.spec_from_file_location("o11_nav2_goal_execution_proof", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


class O11Nav2GoalExecutionProofTests(unittest.TestCase):
    """锁定 O11 从 NavigateToPose 到真实底盘反馈的证明边界。"""

    def test_managed_bridge_defaults_to_ros_motion_path(self) -> None:
        """自动驾驶托管 bridge 默认走 vendor T=13 ROS 控制，不把雷达作为底盘发命令前置。"""
        command = HELPER.managed_esp32_bridge_command("/tmp/o11_feedback.jsonl", "/tmp/o11_command.jsonl")

        self.assertIn("ros2_trashbot_hardware esp32_bridge", command)
        self.assertIn("-p serial_port:=/dev/ttyS5", command)
        self.assertIn("-p command_mode:=ros", command)
        self.assertIn("-p pwm_min_abs:=164", command)
        self.assertIn("-p pwm_max_abs:=164", command)
        self.assertIn("-p feedback_debug_log_path:=/tmp/o11_feedback.jsonl", command)
        self.assertIn("-p command_debug_log_path:=/tmp/o11_command.jsonl", command)
        self.assertNotIn("command_mode:=pwm", command)
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
        """Nav2 已切到 ROS 后，L/R=0 的缺口不能继续被误写成 PWM 路径。"""
        self.assertEqual(
            "nav2_goal_succeeded_with_ros_commands_but_wheel_lr_zero",
            HELPER.wheel_zero_proof_status_for_mode("ros"),
        )
        self.assertEqual(
            "nav2_goal_succeeded_with_pwm_commands_but_wheel_lr_zero",
            HELPER.wheel_zero_proof_status_for_mode("pwm"),
        )
        self.assertEqual(
            "nav2_goal_succeeded_with_ros_commands_but_wheel_lr_zero",
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

    def test_missing_feedback_log_does_not_claim_hil(self) -> None:
        """反馈日志缺失时保持 fail-closed，不能仅凭 action 成功推导 HIL。"""
        summary = HELPER.summarize_feedback_debug_log("/tmp/does-not-exist-o11-feedback.jsonl")

        self.assertFalse(summary["exists"])
        self.assertFalse(summary["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual(summary["reason"], "feedback_debug_log_unreadable")

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
        self.assertEqual(summary["latest_nonzero_command"]["vendor_command"], {"T": 11, "L": 90, "R": 90})

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
