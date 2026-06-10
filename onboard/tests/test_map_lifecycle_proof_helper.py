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
        self.assertIn("--map-name", result.stdout)
        self.assertIn("--timeout-s", result.stdout)
        self.assertNotIn("ros2 launch", result.stdout)

    def test_rejects_unsafe_map_name_before_ros_runtime(self) -> None:
        """map_name 只能是短基名，不能用路径穿越影响保存位置。"""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--map-name", "../bad"],
            check=False,
            text=True,
            capture_output=True,
            timeout=5,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("map_name must match", result.stderr)
        self.assertNotIn("ros2 launch", result.stdout + result.stderr)

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

    def test_launch_command_enables_complete_no_motion_tf_chain(self) -> None:
        """LiDAR+SLAM proof 必须同时补齐 odom->base_link 和 base_link->laser_frame。"""
        text = SCRIPT.read_text(encoding="utf-8")

        # /map proof 的上一轮 blocker 是 slam_toolbox 丢弃 laser_frame scan；
        # 这里锁定 smoke-only laser TF，避免回归成只有 odom TF 的半截拓扑。
        for required in (
            "static_laser_tf_enabled:=true",
            "no_motion_static_odom_tf:=true",
            "lidar_enabled:=true",
            "lidar_publish_raw_packets:=true",
        ):
            self.assertIn(required, text)

        # proof helper 只能启动 learn.launch.py 的传感器/SLAM窗口，不能绕到运动或 API 链路。
        for forbidden in (
            "/api/base/",
            "/api/map/start",
            "/api/nav2/",
            "/dev/ttyS5",
            "base_enabled:=true",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
