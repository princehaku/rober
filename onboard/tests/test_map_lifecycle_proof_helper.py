"""map lifecycle proof helper 的本地静态测试。

这些测试只覆盖脚本存在性、CLI help 和 no-motion 安全边界。
本地开发机不能触碰真实 LiDAR、WAVE ROVER 或 ROS2 runtime。
因此测试必须停在 argparse/help 和源代码 guard 检查。
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o3_map_lifecycle_proof.py"


class MapLifecycleProofHelperTests(unittest.TestCase):
    """锁定 API 可复现入口和本地无硬件验证边界。"""

    def test_helper_exists_and_is_executable(self) -> None:
        """API 通过同目录脚本名查找 helper，文件缺失会让 refresh 不可复现。"""
        # 可执行位不是 API 的必要条件，但能让现场 SSH 手工复核入口一致。
        self.assertTrue(SCRIPT.exists())
        self.assertTrue(os.access(SCRIPT, os.X_OK))

    def test_help_exits_before_hardware_runtime(self) -> None:
        """`--help` 必须只走 argparse，不启动 ROS2、LiDAR 或任何底盘接口。"""
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
        self.assertIn("--map-dir", result.stdout)
        self.assertIn("--timeout-s", result.stdout)
        self.assertNotIn("ros2 launch", result.stdout)

    def test_static_no_motion_guard_terms(self) -> None:
        """helper 只能做 no-motion map proof，不能夹带运动控制入口。"""
        text = SCRIPT.read_text(encoding="utf-8")

        # 这些调用形态一旦出现，说明 proof 入口可能主动碰 ROS motion 或底盘链路。
        for forbidden in ("ros2 topic pub", "geometry_msgs/msg/Twist", "serial.Serial", "requests."):
            self.assertNotIn(forbidden, text)

        # guard 字段要直接落入 artifact，API/readback 才能继续阻止误判可控。
        for required in (
            "safe_to_control",
            "publishes_cmd_vel",
            "calls_base_manual",
            "uses_base_uart",
            "delivery_success",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
