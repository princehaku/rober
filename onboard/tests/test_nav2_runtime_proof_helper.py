"""Nav2 runtime proof helper 的本地静态测试。

这些测试不启动真实 ROS2，也不触碰 WAVE ROVER、底盘 UART 或运动 API。
测试目标是锁定 helper/API 的 CLI、managed runtime 参数透传和 no-motion 安全边界。
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
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
            "--path-generation-opt-in",
            "--path-generation-timeout-s",
            "--path-goal-frame-id",
            "--path-goal-x",
            "--path-goal-y",
            "--path-goal-yaw",
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
        self.assertFalse(args.path_generation_opt_in)
        self.assertEqual(20.0, args.path_generation_timeout_s)
        self.assertEqual("map", args.path_goal_frame_id)
        self.assertEqual(0.8, args.path_goal_x)
        self.assertEqual(0.0, args.path_goal_y)
        self.assertEqual(0.0, args.path_goal_yaw)

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
        self.assertFalse(args.path_generation_opt_in)

    def test_package_checks_use_single_sourced_pkg_list_command(self) -> None:
        """包可用性是诊断信息，必须一次 pkg list 检查，不能逐包 prefix 阻塞主路径。"""
        args = HELPER.parse_args([])
        stdout = "\n".join(HELPER.EXPECTED_PACKAGES)
        with mock.patch.object(
            HELPER,
            "run_ros",
            return_value={
                "command": "ros2 pkg list",
                "executed": True,
                "ok": True,
                "returncode": 0,
                "elapsed_ms": 900,
                "stdout": stdout,
                "stderr": "",
            },
        ) as run_mock:
            packages, results, batch_result = HELPER.package_checks(args)

        run_mock.assert_called_once()
        command = run_mock.call_args.args[1]
        self.assertEqual("ros2 pkg list", command)
        self.assertEqual(HELPER.PACKAGE_CHECK_BATCH_TIMEOUT_S, run_mock.call_args.kwargs["timeout_s"])
        self.assertTrue(batch_result["ok"])
        self.assertTrue(all(packages.values()))
        self.assertEqual(set(HELPER.EXPECTED_PACKAGES), set(results))
        for package in HELPER.EXPECTED_PACKAGES:
            self.assertEqual(f"ros2 pkg list contains {package}", results[package]["command"])
            self.assertEqual("single_sourced_pkg_list_package_check", results[package]["diagnostic_mode"])

    def test_initialpose_phase_precedes_slow_topic_probe(self) -> None:
        """定位 reset 必须先尝试 `/initialpose`，再进入可能耗时的 preflight 诊断。"""
        text = SCRIPT.read_text(encoding="utf-8")
        initialpose_index = text.index('phase_writer.record_phase("initialpose")')

        self.assertLess(
            initialpose_index,
            text.index('phase_writer.record_phase(\n        "package_checks"'),
        )
        self.assertLess(
            initialpose_index,
            text.index('phase_writer.record_phase("graph_discovery"'),
        )
        self.assertLess(
            initialpose_index,
            text.index('phase_writer.record_phase("topic_probe"'),
        )
        self.assertIn('ROS2_PREFLIGHT_COMMAND = "command -v ros2"', text)
        self.assertIn("pre_initialpose_amcl_pose_probe_skipped_to_prioritize_initialpose", text)

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

    def test_path_generation_opt_in_adds_planner_without_controller(self) -> None:
        """path opt-in 只允许 planner_server 和 ComputePathToPose，不拉起 controller/BT。"""
        args = HELPER.parse_args(
            [
                "--managed-runtime-opt-in",
                "--managed-map-yaml",
                "/tmp/test_map.yaml",
                "--initialpose-opt-in",
                "--path-generation-opt-in",
                "--path-goal-x",
                "0.8",
            ]
        )
        request = HELPER.path_generation_request(args)
        params = HELPER.managed_param_file_text(args, "/tmp/test_map.yaml", include_planner_server=True)
        shell = HELPER.build_managed_runtime_shell(
            args,
            map_yaml="/tmp/test_map.yaml",
            params_path="/tmp/runtime.yaml",
            log_path="/tmp/runtime.log",
            include_planner_server=True,
        )

        self.assertTrue(request["enabled"])
        self.assertAlmostEqual(0.8, request["x"])
        self.assertIn("planner_server:", params)
        self.assertIn('node_names: ["map_server", "amcl", "planner_server"]', params)
        self.assertIn("nav2_planner planner_server", shell)
        self.assertIn("no_motion_path_generation_planner_only", shell)
        for forbidden in ("controller_server", "bt_navigator", "FollowPath", "/cmd_vel", "ros2 action send_goal"):
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
            "FollowPath",
            "ros2 run nav2_bt_navigator",
            "controller_server --ros-args",
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
            "tf_echo_transform_observed(odom_to_base_link_tf)",
            "tf_echo_transform_observed(base_link_to_laser_frame_tf)",
            "tf_echo_transform_observed(map_to_base_link_tf)",
            "tf_chain_observed",
            "tf_failure_classification",
            "read_only_existing_ros_graph_no_motion",
        ):
            self.assertIn(required, text)

    def test_tf_chain_failure_classifies_missing_odom_base_link(self) -> None:
        """`map->base_link` 失败必须下钻到缺失的链路段，而不是只给最终布尔值。"""
        args = HELPER.parse_args([])
        observed = {
            "map_to_odom": True,
            "odom_to_base_link": False,
            "base_link_to_laser_frame": True,
            "map_to_base_link": False,
        }
        diagnostics = HELPER.build_tf_chain_diagnostics(
            args=args,
            results={
                "map_to_odom": {"executed": True, "ok": True, "stdout": "Translation:\nRotation:"},
                "odom_to_base_link": {"executed": True, "ok": False, "returncode": 124, "stdout": "Waiting for transform"},
                "base_link_to_laser_frame": {"executed": True, "ok": True, "stdout": "Translation:\nRotation:"},
                "map_to_base_link": {"executed": False, "ok": False, "boundary": "skipped"},
            },
            observed=observed,
        )

        classification = HELPER.classify_tf_chain_failure(args=args, observed=observed, diagnostics=diagnostics)
        causes = HELPER.tf_chain_root_causes(classification, observed)

        self.assertEqual("blocked_by_missing_odom_to_base_link", classification["map_to_base_link"])
        self.assertEqual("odom_to_base_link", classification["blocking_segment"])
        self.assertEqual("tf2_timeout_or_timing", classification["reason"])
        self.assertEqual("map_to_base_link_blocked_by_missing_odom_to_base_link", causes[0]["reason"])
        self.assertEqual("odom_to_base_link", causes[0]["source"])

    def test_tf_chain_failure_classifies_frame_naming_mismatch(self) -> None:
        """如果 runtime frame 参数偏离默认合同，artifact 要明确提示命名不一致。"""
        args = HELPER.parse_args(["--managed-base-frame-id", "base_footprint"])
        observed = HELPER.default_tf_chain_observed()
        diagnostics = HELPER.build_tf_chain_diagnostics(args=args, results={}, observed=observed)

        classification = HELPER.classify_tf_chain_failure(args=args, observed=observed, diagnostics=diagnostics)

        self.assertEqual("frame_naming_mismatch", classification["map_to_base_link"])
        self.assertEqual("frame_contract", classification["blocking_segment"])
        self.assertFalse(classification["frame_naming_consistent"])

    def test_phase_artifact_writer_records_partial_progress(self) -> None:
        """helper 被外层 timeout 打断前，partial artifact 必须已经有阶段和命令证据。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "localization_reset_latest.json"
            args = HELPER.parse_args(["--output", str(output), "--managed-runtime-opt-in", "--initialpose-opt-in"])
            writer = HELPER.PhaseArtifactWriter(args, HELPER.now_ms())

            writer.record_phase("managed_runtime_started", ok=True, detail={"process_group": 123})
            writer.before_command("ros2 topic echo --once /amcl_pose", 8.0)
            writer.update_snapshot(managed_runtime_started=True, initialpose_published=True)
            payload = json.loads(output.read_text(encoding="utf-8"))

        proof = payload["proof"]
        self.assertEqual("partial_runtime_in_progress", payload["status"])
        self.assertEqual("managed_runtime_started", proof["last_successful_phase"])
        self.assertEqual("ros2 topic echo --once /amcl_pose", proof["current_command"]["command"])
        self.assertTrue(proof["managed_runtime_started"])
        self.assertTrue(proof["initialpose_published"])
        self.assertFalse(proof["sends_motion_commands"])
        self.assertIn("/dev/ttyS5", proof["blocked_devices_not_opened"])

    def test_static_path_generation_opt_in_collector_shape(self) -> None:
        """path generation opt-in 分支必须显式存在，且默认仍然不进入控制层。"""
        text = SCRIPT.read_text(encoding="utf-8")

        for required in (
            "path_generation_opt_in",
            "path_generation_timeout_s",
            "path_goal_frame_id",
            "path_goal_x",
            "path_goal_y",
            "path_goal_yaw",
            "ComputePathToPose",
            "path_generation_service_name",
            "path_generation_service_available",
            "path_generation_succeeded",
            "path_point_count",
            "package_check_mode",
            "package_availability",
            "package_checks_batch",
            "single_sourced_pkg_list_diagnostic",
            "planner_server_active",
            "controller_server_active",
            "controller_server_requested",
            "planner_readiness_summary",
            "explicit_opt_in_compute_path_to_pose_action_no_motion",
        ):
            self.assertIn(required, text)

        for forbidden in (
            "NavigateToPose",
            "FollowPath",
            "delivery_success=true",
        ):
            self.assertNotIn(forbidden, text)

    def test_upper_api_passes_managed_and_initialpose_opt_in_only_from_body(self) -> None:
        """正式 HTTP refresh 必须显式透传 managed runtime 与 initialpose 两类 opt-in。"""
        api_text = (SCRIPT.parent / "upper_robot_api.py").read_text(encoding="utf-8")

        for required in (
            "managed_runtime_opt_in=bool(body.get(\"managed_runtime_opt_in\") is True)",
            "managed_timeout_s=clamp_float(body.get(\"managed_timeout_s\")",
            "managed_map_yaml=str(body.get(\"managed_map_yaml\") or \"\")[:400]",
            "initialpose_opt_in=bool(body.get(\"initialpose_opt_in\") is True)",
            "path_generation_opt_in=bool(body.get(\"path_generation_opt_in\") is True)",
            "path_generation_timeout_s=clamp_float(body.get(\"path_generation_timeout_s\")",
            "path_goal_frame_id=str(body.get(\"path_goal_frame_id\") or \"map\")[:80]",
            "path_goal_x=clamp_float(body.get(\"path_goal_x\")",
            "path_goal_y=clamp_float(body.get(\"path_goal_y\")",
            "path_goal_yaw=clamp_float(body.get(\"path_goal_yaw\")",
            "--managed-runtime-opt-in",
            "--managed-timeout-s",
            "--managed-map-yaml",
            "--initialpose-opt-in",
            "--path-generation-opt-in",
            "--path-generation-timeout-s",
            "--path-goal-frame-id",
            "--path-goal-x",
            "--path-goal-y",
            "--path-goal-yaw",
        ):
            self.assertIn(required, api_text)

    def test_upper_api_pc_path_generation_timeout_stays_under_proxy_budget(self) -> None:
        """PC 检查路径固定 body 必须由上位机先收口，不能让 46s proxy 先超时。"""
        spec = importlib.util.spec_from_file_location("upper_robot_api", SCRIPT.parent / "upper_robot_api.py")
        assert spec is not None and spec.loader is not None
        api_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api_mod)

        budget = api_mod.nav2_runtime_proof_process_timeout_budget(
            timeout_s=8.0,
            managed_runtime_opt_in=False,
            managed_timeout_s=8.0,
            initialpose_opt_in=False,
            path_generation_opt_in=True,
            path_generation_timeout_s=8.0,
        )

        # 8s collector + 8s ComputePathToPose + 固定余量约 36s，给 PC proxy 留 HTTP 返回余量。
        self.assertEqual(36.0, budget["process_timeout_s"])
        self.assertLess(budget["process_timeout_s"], budget["pc_proxy_budget_s"])
        self.assertEqual("finish_before_pc_proxy_timeout_or_return_structured_timeout", budget["budget_policy"])

        fake_completed = {
            "timed_out": False,
            "returncode": 0,
            "stdout": "ok",
            "stderr": "",
            "process_group": 123,
            "cleanup_result": {"attempted": False, "ok": True},
        }
        with mock.patch.object(api_mod, "run_helper_bash_process_group", return_value=fake_completed) as run_mock:
            result = api_mod.run_nav2_runtime_proof_helper(
                artifact_path="/tmp/nav2.json",
                map_proof_path="/tmp/map.json",
                map_artifact_dir="/tmp/maps",
                timeout_s=8.0,
                managed_runtime_opt_in=False,
                managed_timeout_s=8.0,
                managed_map_yaml="",
                initialpose_opt_in=False,
                initialpose_x=0.0,
                initialpose_y=0.0,
                initialpose_yaw=0.0,
                initialpose_frame_id="map",
                path_generation_opt_in=True,
                path_generation_timeout_s=8.0,
                path_goal_frame_id="map",
                path_goal_x=0.8,
                path_goal_y=0.0,
                path_goal_yaw=0.0,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(36.0, result["process_timeout_s"])
        self.assertEqual(36.0, run_mock.call_args.args[1])

    def test_upper_api_managed_path_generation_timeout_is_capped(self) -> None:
        """managed/runtime 扩展场景也要封顶，超长 helper 必须结构化 timeout。"""
        spec = importlib.util.spec_from_file_location("upper_robot_api", SCRIPT.parent / "upper_robot_api.py")
        assert spec is not None and spec.loader is not None
        api_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api_mod)

        budget = api_mod.nav2_runtime_proof_process_timeout_budget(
            timeout_s=30.0,
            managed_runtime_opt_in=True,
            managed_timeout_s=45.0,
            initialpose_opt_in=True,
            path_generation_opt_in=True,
            path_generation_timeout_s=45.0,
        )

        # cap 小于 PC 46s；如果真实 runtime 更慢，API 先回 root cause，latest 仍可只读兜底。
        self.assertEqual(42.0, budget["process_timeout_s"])
        self.assertLess(budget["process_timeout_s"], budget["pc_proxy_budget_s"])

    def test_upper_api_runs_helper_under_ros_setup(self) -> None:
        """API subprocess 必须显式 source ROS 环境，避免 rclpy 在 service 内失效。"""
        api_mod = importlib.util.module_from_spec(
            importlib.util.spec_from_file_location("upper_robot_api", SCRIPT.parent / "upper_robot_api.py")
        )
        assert api_mod is not None
        spec = importlib.util.spec_from_file_location("upper_robot_api", SCRIPT.parent / "upper_robot_api.py")
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(api_mod)

        fake_completed = {
            "timed_out": False,
            "returncode": 0,
            "stdout": "ok",
            "stderr": "",
            "process_group": 123,
            "cleanup_result": {"attempted": False, "ok": True},
        }
        with mock.patch.object(api_mod, "run_helper_bash_process_group", return_value=fake_completed) as run_mock:
            result = api_mod.run_nav2_runtime_proof_helper(
                artifact_path="/tmp/nav2.json",
                map_proof_path="/tmp/map.json",
                map_artifact_dir="/tmp/maps",
                timeout_s=1.0,
                managed_runtime_opt_in=True,
                managed_timeout_s=1.0,
                managed_map_yaml="/tmp/test_map.yaml",
                initialpose_opt_in=True,
                initialpose_x=0.0,
                initialpose_y=0.0,
                initialpose_yaw=0.0,
                initialpose_frame_id="map",
                path_generation_opt_in=True,
                path_generation_timeout_s=1.0,
                path_goal_frame_id="map",
                path_goal_x=0.8,
                path_goal_y=0.0,
                path_goal_yaw=0.0,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(["bash", "-lc"], result["argv"][:2])
        self.assertIn("source /opt/ros/humble/setup.bash", result["argv"][2])
        self.assertIn("python3", result["argv"][2])
        self.assertIn("--path-generation-opt-in", result["argv"][2])
        self.assertIn("--initialpose-opt-in", result["argv"][2])
        run_mock.assert_called_once()
        self.assertEqual("/root/rober/onboard", run_mock.call_args.args[2])

        api_text = (SCRIPT.parent / "upper_robot_api.py").read_text(encoding="utf-8")
        for required in (
            "\"publishes_cmd_vel\": False",
            "\"calls_base_manual\": False",
            "\"sends_base_motion_commands\": False",
            "\"hil_pass\": False",
            "\"path_generation_requested\"",
            "\"path_generation_service_name\"",
            "\"path_generation_service_available\"",
            "\"path_generation_succeeded\"",
            "\"path_point_count\"",
            "\"planner_server_active\"",
            "\"controller_server_active\"",
            "\"controller_server_requested\"",
            "\"planner_readiness_summary\"",
        ):
            self.assertIn(required, api_text)

    def test_upper_api_timeout_writes_blocked_latest_artifact(self) -> None:
        """helper 超时也要写 blocked latest，避免 PC latest readback 退回 missing。"""
        spec = importlib.util.spec_from_file_location("upper_robot_api", SCRIPT.parent / "upper_robot_api.py")
        assert spec is not None and spec.loader is not None
        api_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api_mod)

        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "localization_reset_latest.json"
            timeout_result = {
                "timed_out": True,
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "process_group": 123,
                "cleanup_result": {"attempted": True, "ok": True},
                "error": {"type": "TimeoutExpired", "message": "timeout"},
            }
            with mock.patch.object(api_mod, "run_helper_bash_process_group", return_value=timeout_result):
                result = api_mod.run_nav2_runtime_proof_helper(
                    artifact_path=str(artifact_path),
                    map_proof_path="/tmp/map.json",
                    map_artifact_dir="/tmp/maps",
                    timeout_s=8.0,
                    managed_runtime_opt_in=True,
                    managed_timeout_s=12.0,
                    managed_map_yaml="",
                    initialpose_opt_in=True,
                    initialpose_x=0.0,
                    initialpose_y=0.0,
                    initialpose_yaw=0.0,
                    initialpose_frame_id="map",
                    path_generation_opt_in=False,
                    path_generation_timeout_s=4.0,
                    path_goal_frame_id="map",
                    path_goal_x=0.0,
                    path_goal_y=0.0,
                    path_goal_yaw=0.0,
                )
            payload = api_mod.json.loads(artifact_path.read_text(encoding="utf-8"))

        self.assertFalse(result["ok"])
        self.assertTrue(result["fallback_artifact_written"])
        self.assertEqual("blocked_with_root_cause", payload["status"])
        self.assertEqual("helper_process_timeout_before_artifact", payload["proof"]["root_causes"][0]["reason"])
        self.assertTrue(payload["proof"]["managed_runtime_requested"])
        self.assertTrue(payload["proof"]["initialpose_publish_attempted"])
        self.assertFalse(payload["proof"]["path_generation_requested"])
        self.assertFalse(payload["proof"]["initialpose_published"])
        self.assertFalse(payload["proof"]["amcl_pose_observed"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["publishes_cmd_vel"])
        self.assertIn("/dev/ttyS5", payload["proof"]["blocked_devices_not_opened"])

    def test_upper_api_timeout_preserves_helper_partial_artifact(self) -> None:
        """helper 已写 partial 时，upper timeout fallback 只能追加 root cause，不能抹掉阶段证据。"""
        spec = importlib.util.spec_from_file_location("upper_robot_api", SCRIPT.parent / "upper_robot_api.py")
        assert spec is not None and spec.loader is not None
        api_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api_mod)

        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_path = Path(temp_dir) / "localization_reset_latest.json"
            partial = {
                "schema": "trashbot.upper_robot_api.v1.nav2_lifecycle_runtime_proof",
                "status": "partial_runtime_in_progress",
                "proof": {
                    "status": "partial_runtime_in_progress",
                    "last_phase": "tf_probe",
                    "last_successful_phase": "initialpose",
                    "phase_history": [{"phase": "initialpose", "ok": True}],
                    "current_command": {"command": "timeout 4 ros2 run tf2_ros tf2_echo map base_link"},
                    "recent_commands": [{"command": "ros2 topic pub --once /initialpose", "ok": True}],
                    "package_availability": {"nav2_amcl": True, "nav2_map_server": True},
                    "package_check_mode": "single_sourced_pkg_list_diagnostic",
                    "package_checks_batch_ok": True,
                    "managed_runtime_requested": True,
                    "managed_runtime_started": True,
                    "initialpose_publish_attempted": True,
                    "initialpose_published": True,
                    "amcl_pose_observed": False,
                    "localization_tf_observed": {"map_to_odom": False, "map_to_base_link": False},
                    "root_causes": [{"layer": "AMCL localization", "reason": "/amcl_pose_once_not_observed"}],
                    "blocked_devices_not_opened": ["/dev/ttyS5"],
                },
            }
            artifact_path.write_text(json.dumps(partial), encoding="utf-8")
            timeout_result = {
                "timed_out": True,
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "process_group": 123,
                "cleanup_result": {"attempted": True, "ok": True},
                "error": {"type": "TimeoutExpired", "message": "timeout"},
            }
            with mock.patch.object(api_mod, "run_helper_bash_process_group", return_value=timeout_result):
                result = api_mod.run_nav2_runtime_proof_helper(
                    artifact_path=str(artifact_path),
                    map_proof_path="/tmp/map.json",
                    map_artifact_dir="/tmp/maps",
                    timeout_s=8.0,
                    managed_runtime_opt_in=True,
                    managed_timeout_s=12.0,
                    managed_map_yaml="",
                    initialpose_opt_in=True,
                    initialpose_x=0.0,
                    initialpose_y=0.0,
                    initialpose_yaw=0.0,
                    initialpose_frame_id="map",
                    path_generation_opt_in=False,
                    path_generation_timeout_s=4.0,
                    path_goal_frame_id="map",
                    path_goal_x=0.0,
                    path_goal_y=0.0,
                    path_goal_yaw=0.0,
                )
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))

        self.assertFalse(result["ok"])
        self.assertTrue(result["partial_artifact_preserved"])
        self.assertTrue(payload["proof"]["partial_artifact_preserved"])
        self.assertEqual("tf_probe", payload["proof"]["last_phase"])
        self.assertEqual("initialpose", payload["proof"]["last_successful_phase"])
        self.assertEqual("timeout 4 ros2 run tf2_ros tf2_echo map base_link", payload["proof"]["current_command"]["command"])
        self.assertEqual("single_sourced_pkg_list_diagnostic", payload["proof"]["package_check_mode"])
        self.assertTrue(payload["proof"]["package_availability"]["nav2_amcl"])
        self.assertTrue(payload["proof"]["package_checks_batch_ok"])
        self.assertTrue(payload["proof"]["initialpose_published"])
        self.assertTrue(payload["proof"]["managed_runtime_started"])
        self.assertEqual("helper_process_timeout_after_partial_artifact", payload["proof"]["root_causes"][-1]["reason"])
        self.assertEqual("/amcl_pose_once_not_observed", payload["proof"]["root_causes"][0]["reason"])

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
