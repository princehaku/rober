"""LiDAR lifecycle shell 脚本的安全边界测试。

这些测试只跑不需要 ROS2 的 status/guard 分支，避免本地开发机依赖真实雷达。
真实 start/stop HIL 由远端 smoke 负责，本文件锁定脚本不能误碰底盘 UART。
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "o1_lidar_lifecycle.sh"


class LidarLifecycleScriptTests(unittest.TestCase):
    """验证 lifecycle 脚本的可解析状态和危险串口拒绝逻辑。"""

    def test_status_returns_structured_json_when_not_running(self) -> None:
        """status 不应打开 ROS2 或串口，本地也必须能返回结构化 JSON。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                ["bash", str(SCRIPT_PATH), "status", "--runtime-dir", temp_dir],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["running"])
        self.assertIsNone(payload["pid"])
        self.assertEqual("/dev/ttyACM0", payload["serial_port"])
        self.assertEqual(150000, payload["baudrate"])
        self.assertFalse(payload["uses_base_uart"])
        self.assertFalse(payload["publishes_cmd_vel"])
        self.assertIn("/dev/ttyS5", payload["blocked_base_uart"])

    def test_start_rejects_wave_rover_base_uart_before_runtime(self) -> None:
        """即使本机没有 ROS2，/dev/ttyS5 也必须先被 guard 拒绝。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    "bash",
                    str(SCRIPT_PATH),
                    "start",
                    "--serial-port",
                    "/dev/ttyS5",
                    "--runtime-dir",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

        self.assertEqual(41, completed.returncode)
        self.assertIn("refusing WAVE ROVER base UART /dev/ttyS5", completed.stderr)

    def test_start_rejects_non_lidar_serial_path(self) -> None:
        """普通 USB 串口不能被当成 LiDAR，避免误接底盘或其他设备。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = subprocess.run(
                [
                    "bash",
                    str(SCRIPT_PATH),
                    "start",
                    "--serial-port",
                    "/dev/ttyUSB0",
                    "--runtime-dir",
                    temp_dir,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )

        self.assertEqual(40, completed.returncode)
        self.assertIn("refusing non-LiDAR-looking serial port", completed.stderr)


if __name__ == "__main__":
    unittest.main()
