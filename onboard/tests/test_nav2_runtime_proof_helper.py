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
import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o10_amcl_nav2_runtime_proof.py"
SPEC = importlib.util.spec_from_file_location("o10_amcl_nav2_runtime_proof", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


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
        self.assertIn("--initialpose-opt-in", result.stdout)
        self.assertIn("--initialpose-x", result.stdout)
        self.assertIn("--initialpose-yaw", result.stdout)
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
            "/cmd_vel geometry_msgs/msg/Twist",
            "geometry_msgs/msg/Twist",
            "/api/base/",
            "/api/nav2/start",
            "serial.Serial",
        ):
            self.assertNotIn(forbidden, text)

    def test_static_opt_in_initialpose_collector_shape(self) -> None:
        """collector 默认只读；只有 opt-in 分支允许单次 /initialpose 定位 proof。"""
        text = SCRIPT.read_text(encoding="utf-8")

        # O10 helper 的核心证据来自只读 topic/node/lifecycle/action/service 查询。
        for required in (
            "ros2 lifecycle get",
            "ros2 topic echo --once /scan",
            "ros2 topic echo --once /map",
            "ros2 topic echo --once /amcl_pose",
            "default_read_only_no_initialpose_publish",
            "ros2 topic pub --once /initialpose",
            "geometry_msgs/msg/PoseWithCovarianceStamped",
            "start_new_session=True",
            "os.killpg",
            "tf_echo_transform_observed(map_to_odom_tf)",
            "tf_echo_transform_observed(map_to_base_link_tf)",
            "read_only_existing_ros_graph_no_motion",
        ):
            self.assertIn(required, text)

        # 即使读取 action/service 列表，也不能真的下发 Nav2 goal 或 compute path。
        for forbidden in (
            "ros2 action send_goal",
            "ros2 service call",
            "ComputePathToPose",
            "NavigateToPose",
            "compute_path_to_pose ",
            "navigate_to_pose ",
        ):
            self.assertNotIn(forbidden, text)

    def test_upper_api_passes_initialpose_opt_in_only_from_body(self) -> None:
        """正式 HTTP refresh 只能通过 body 的显式 boolean opt-in 传递定位种子。"""
        api_text = (SCRIPT.parent / "upper_robot_api.py").read_text(encoding="utf-8")

        for required in (
            "initialpose_opt_in=bool(body.get(\"initialpose_opt_in\") is True)",
            "--initialpose-opt-in",
            "--initialpose-frame-id",
            "initialpose_x=clamp_float(body.get(\"initialpose_x\")",
            "initialpose_yaw=clamp_float(body.get(\"initialpose_yaw\")",
        ):
            self.assertIn(required, api_text)

        # API wrapper 也必须继续禁止底盘、速度和 HIL 成功标志。
        for required in (
            "\"publishes_cmd_vel\": False",
            "\"calls_base_manual\": False",
            "\"sends_base_motion_commands\": False",
            "\"hil_pass\": False",
        ):
            self.assertIn(required, api_text)

    def test_tf_echo_timeout_stdout_transform_counts_observed(self) -> None:
        """tf2_echo 正常持续输出时可能被 timeout 杀掉，不能因 rc=124 误判失败。"""
        result = {
            "ok": False,
            "returncode": 124,
            "stdout": (
                "At time 1781050000.000000000\n"
                "- Translation: [1.000, 2.000, 0.000]\n"
                "- Rotation: in Quaternion [0.000, 0.000, 0.000, 1.000]\n"
            ),
            "stderr": "",
        }

        self.assertTrue(HELPER.tf_echo_transform_observed(result))

    def test_tf_echo_failure_or_empty_output_not_observed(self) -> None:
        """TF 判定必须保守，lookup failure 或空输出不能被当成 transform。"""
        failure = {
            "ok": False,
            "returncode": 124,
            "stdout": "",
            "stderr": "Failure at 1.0: Could not transform map to base_link",
        }
        empty = {"ok": False, "returncode": 124, "stdout": "", "stderr": ""}

        self.assertFalse(HELPER.tf_echo_transform_observed(failure))
        self.assertFalse(HELPER.tf_echo_transform_observed(empty))


if __name__ == "__main__":
    unittest.main()
