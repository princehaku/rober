"""Nav2 runtime proof helper 的本地静态测试。

这些测试不启动真实 ROS2，也不触碰 WAVE ROVER、底盘 UART 或运动 API。
测试目标是锁定 helper/API 的 CLI、managed runtime 参数透传和 no-motion 安全边界。
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o10_amcl_nav2_runtime_proof.py"
SPEC = importlib.util.spec_from_file_location("o10_amcl_nav2_runtime_proof", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


class Nav2RuntimeProofHelperTests(unittest.TestCase):
    """锁定正式 API 调用的 O10 no-motion helper 和 managed runtime 边界。"""

    def test_helper_exists_and_is_executable(self) -> None:
        """API 通过同目录脚本名查找 helper，文件缺失会让 refresh 退化为 blocker。"""
        self.assertTrue(SCRIPT.exists())
        self.assertTrue(os.access(SCRIPT, os.X_OK))

    def test_help_exits_before_ros2_runtime(self) -> None:
        """`--help` 必须只走 argparse，不启动 ROS2 或任何底盘接口。"""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            text=True,
            capture_output=True,
            timeout=5,
        )

        self.assertEqual(0, result.returncode)
        for required in (
            "--output",
            "--map-proof",
            "--map-dir",
            "--timeout-s",
            "--managed-runtime-opt-in",
            "--managed-timeout-s",
            "--managed-map-yaml",
            "--initialpose-opt-in",
            "--initialpose-yaw",
        ):
            self.assertIn(required, result.stdout)
        self.assertNotIn("ros2 launch", result.stdout)

    def test_parse_args_defaults_keep_read_only(self) -> None:
        """默认参数必须保持旧 collector 语义，不因新增 managed flag 产生副作用。"""
        args = HELPER.parse_args([])

        self.assertFalse(args.managed_runtime_opt_in)
        self.assertEqual("", args.managed_map_yaml)
        self.assertEqual(20.0, args.managed_timeout_s)
        self.assertFalse(args.initialpose_opt_in)

    def test_parse_args_managed_without_initialpose(self) -> None:
        """managed runtime 与 initialpose 解耦，单独开启 runtime 时不能隐式发布 pose。"""
        args = HELPER.parse_args(
            [
                "--managed-runtime-opt-in",
                "--managed-timeout-s",
                "12",
                "--managed-map-yaml",
                "/tmp/test_map.yaml",
            ]
        )

        self.assertTrue(args.managed_runtime_opt_in)
        self.assertEqual(12.0, args.managed_timeout_s)
        self.assertEqual("/tmp/test_map.yaml", args.managed_map_yaml)
        self.assertFalse(args.initialpose_opt_in)

    def test_parse_args_managed_with_initialpose(self) -> None:
        """只有两个 opt-in 都显式传入时，helper 才允许发布一次 `/initialpose`。"""
        args = HELPER.parse_args(
            [
                "--managed-runtime-opt-in",
                "--managed-map-yaml",
                "/tmp/test_map.yaml",
                "--initialpose-opt-in",
                "--initialpose-x",
                "1.5",
                "--initialpose-y",
                "-0.5",
                "--initialpose-yaw",
                "0.7",
            ]
        )

        request = HELPER.initialpose_request(args)
        self.assertTrue(args.managed_runtime_opt_in)
        self.assertTrue(request["enabled"])
        self.assertAlmostEqual(1.5, request["x"])
        self.assertAlmostEqual(-0.5, request["y"])
        self.assertAlmostEqual(0.7, request["yaw"])

    def test_managed_runtime_shell_stays_no_motion(self) -> None:
        """managed runtime 只允许 localization graph，禁止 planner/controller/底盘 UART。"""
        args = HELPER.parse_args(
            [
                "--managed-runtime-opt-in",
                "--managed-map-yaml",
                "/tmp/test_map.yaml",
            ]
        )
        shell = HELPER.build_managed_runtime_shell(
            args,
            map_yaml="/tmp/test_map.yaml",
            params_path="/tmp/runtime.yaml",
            log_path="/tmp/runtime.log",
        )

        for required in (
            "ros2 run ros2_trashbot_hardware lidar_driver",
            "/dev/ttyACM0",
            "nav2_map_server map_server",
            "nav2_amcl amcl",
            "nav2_lifecycle_manager lifecycle_manager",
            "blocked_device=/dev/ttyS5",
        ):
            self.assertIn(required, shell)

        for forbidden in (
            "serial_port:=/dev/ttyS5",
            "planner_server",
            "controller_server",
            "ros2 action send_goal",
            "compute_path_to_pose",
            "/cmd_vel",
            "serial.Serial",
        ):
            self.assertNotIn(forbidden, shell)

    def test_managed_param_file_only_lists_localization_nodes(self) -> None:
        """参数文件只能包含 map_server/amcl/lifecycle_manager，不能偷偷把运动栈拉起来。"""
        args = HELPER.parse_args([])
        text = HELPER.managed_param_file_text(args, "/tmp/test_map.yaml")

        for required in ("map_server:", "amcl:", "lifecycle_manager:", 'node_names: ["map_server", "amcl"]'):
            self.assertIn(required, text)
        for forbidden in ("planner_server", "controller_server", "bt_navigator", "cmd_vel"):
            self.assertNotIn(forbidden, text)

    def test_cleanup_guard_reports_remaining_processes(self) -> None:
        """进程组清理 guard 必须能显式回报残留，而不是静默吞掉 orphan。"""
        with mock.patch.object(
            HELPER,
            "process_group_members",
            return_value=[{"pid": 123, "pgid": 456, "command": "ros2 topic echo --once /scan"}],
        ):
            result = HELPER.managed_runtime_cleanup_guard(456)

        self.assertFalse(result["ok"])
        self.assertEqual("managed_runtime_process_group_cleanup_guard", result["boundary"])
        self.assertEqual(123, result["remaining_processes"][0]["pid"])

    def test_static_no_motion_guard_terms(self) -> None:
        """helper artifact 必须显式声明不会发车、不会调用底盘、不会写成功。"""
        text = SCRIPT.read_text(encoding="utf-8")

        for required in (
            "publishes_cmd_vel",
            "calls_base_manual",
            "uses_base_uart",
            "delivery_success",
            "managed_runtime_requested",
            "managed_runtime_started",
            "managed_runtime_process_group",
            "managed_runtime_cleanup_ok",
            "managed_runtime_boundary",
        ):
            self.assertIn(required, text)

        for forbidden in (
            "ros2 action send_goal",
            "NavigateToPose",
            "ComputePathToPose",
            "serial.Serial(",
        ):
            self.assertNotIn(forbidden, text)

    def test_static_opt_in_initialpose_collector_shape(self) -> None:
        """collector 默认只读；只有 opt-in 分支允许单次 /initialpose 定位 proof。"""
        text = SCRIPT.read_text(encoding="utf-8")

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

    def test_upper_api_passes_managed_and_initialpose_opt_in_only_from_body(self) -> None:
        """正式 HTTP refresh 必须显式透传 managed runtime 与 initialpose 两类 opt-in。"""
        api_text = (SCRIPT.parent / "upper_robot_api.py").read_text(encoding="utf-8")

        for required in (
            "managed_runtime_opt_in=bool(body.get(\"managed_runtime_opt_in\") is True)",
            "managed_timeout_s=clamp_float(body.get(\"managed_timeout_s\")",
            "managed_map_yaml=str(body.get(\"managed_map_yaml\") or \"\")[:400]",
            "initialpose_opt_in=bool(body.get(\"initialpose_opt_in\") is True)",
            "--managed-runtime-opt-in",
            "--managed-timeout-s",
            "--managed-map-yaml",
            "--initialpose-opt-in",
        ):
            self.assertIn(required, api_text)

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
