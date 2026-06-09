"""Nav2 runtime proof helper 的本地静态测试。

这些测试只覆盖脚本存在性、CLI help 和 no-motion 安全边界。
本地开发机不能启动 ROS2，也不能触碰 WAVE ROVER、底盘 UART 或运动 API。
因此测试必须停在 argparse/help 和源码 guard 检查。
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o10_amcl_nav2_runtime_proof.py"


class Nav2RuntimeProofHelperTests(unittest.TestCase):
    """锁定正式 API 调用的 O10 no-motion helper 和安全边界。"""

    def test_helper_exists_and_is_executable(self) -> None:
        """API 通过同目录脚本名查找 helper，文件缺失会让 refresh 退化为 blocker。"""
        # 可执行位方便现场 SSH 直接复核，避免只在 Python subprocess 下可运行。
        self.assertTrue(SCRIPT.exists())
        self.assertTrue(os.access(SCRIPT, os.X_OK))

    def test_help_exits_before_ros2_runtime(self) -> None:
        """`--help` 必须只走 argparse，不启动 ROS2 或任何底盘接口。"""
        # help 模式由 argparse 在 parse_args 阶段退出，不会进入 build_proof。
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            text=True,
            capture_output=True,
            timeout=5,
        )

        self.assertEqual(0, result.returncode)
        self.assertIn("--output", result.stdout)
        self.assertIn("--map-proof", result.stdout)
        self.assertIn("--map-dir", result.stdout)
        self.assertIn("--timeout-s", result.stdout)
        self.assertNotIn("ros2 topic", result.stdout)
        self.assertNotIn("ros2 launch", result.stdout)

    def test_static_no_motion_guard_terms(self) -> None:
        """helper artifact 必须显式声明不会发车、不会调用底盘、不会写成功。"""
        text = SCRIPT.read_text(encoding="utf-8")

        # 这些 guard 字段是 upper API readback 防止误判的关键布尔值。
        for required in (
            "publishes_cmd_vel",
            "calls_base_manual",
            "uses_base_uart",
            "delivery_success",
        ):
            self.assertIn(required, text)

        # 禁止出现会发布速度、触碰底盘 API 或打开串口的直接入口。
        for forbidden in (
            "ros2 topic pub",
            "geometry_msgs/msg/Twist",
            "/api/base/",
            "/api/nav2/start",
            "serial.Serial",
        ):
            self.assertNotIn(forbidden, text)

    def test_static_read_only_nav2_collector_shape(self) -> None:
        """collector 只能只读现有 graph，不能发送 goal、发布 initialpose 或启动 Nav2。"""
        text = SCRIPT.read_text(encoding="utf-8")

        # O10 helper 的核心证据来自只读 topic/node/lifecycle/action/service 查询。
        for required in (
            "ros2 lifecycle get",
            "ros2 topic echo --once /scan",
            "ros2 topic echo --once /map",
            "ros2 topic echo --once /amcl_pose",
            "read_only_existing_ros_graph_no_motion",
        ):
            self.assertIn(required, text)

        # 即使读取 action/service 列表，也不能真的下发 Nav2 goal 或 compute path。
        for forbidden in (
            "ros2 action send_goal",
            "ros2 service call",
            "ComputePathToPose",
            "NavigateToPose",
            "initialpose_published\": True",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
