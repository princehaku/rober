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
            "--managed-lifecycle-start-delay-s",
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
        self.assertEqual(3.0, args.managed_lifecycle_start_delay_s)
        self.assertFalse(args.initialpose_opt_in)
        self.assertFalse(args.path_generation_opt_in)
        self.assertEqual(20.0, args.path_generation_timeout_s)
        self.assertEqual("map", args.path_goal_frame_id)
        self.assertEqual(0.8, args.path_goal_x)
        self.assertEqual(0.0, args.path_goal_y)
        self.assertEqual(0.0, args.path_goal_yaw)

    def test_parse_amcl_pose_extracts_map_pose(self) -> None:
        """AMCL YAML 只读解析要给 PC 地图 overlay 提供 x/y/yaw，解析失败时由调用方保持空值。"""
        pose = HELPER.parse_amcl_pose(
            """
header:
  frame_id: map
pose:
  pose:
    position:
      x: 0.25
      y: 0.75
      z: 0.0
    orientation:
      x: 0.0
      y: 0.0
      z: 0.7071068
      w: 0.7071068
"""
        )

        self.assertIsNotNone(pose)
        self.assertEqual("map", pose["frame_id"])
        self.assertAlmostEqual(0.25, pose["x"])
        self.assertAlmostEqual(0.75, pose["y"])
        self.assertAlmostEqual(1.5708, pose["yaw"], places=3)
        self.assertEqual("/amcl_pose", pose["source"])

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
            "starting role=static_tf_broadcaster",
            "managed_static_tf_broadcaster",
            "static_tf_odom_base static_tf_base_laser",
            "StaticTransformBroadcaster",
            "nav2_map_server map_server",
            "nav2_amcl amcl",
            "nav2_lifecycle_manager lifecycle_manager",
            "waiting before lifecycle_manager start delay_s=3",
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
        self.assertIn("waiting before lifecycle_manager start delay_s=3", shell)
        self.assertLess(shell.index("starting role=planner_server"), shell.index("waiting before lifecycle_manager start"))
        self.assertLess(shell.index("waiting before lifecycle_manager start"), shell.index("starting role=lifecycle_manager"))
        for forbidden in ("controller_server", "bt_navigator", "FollowPath", "/cmd_vel", "ros2 action send_goal"):
            self.assertNotIn(forbidden, shell)

    def test_path_generation_request_adapts_out_of_bounds_goal_to_map(self) -> None:
        """固定 proof 点越过新地图边界时，只能改 planner-only 起终点，不能触发运动层。"""
        args = HELPER.parse_args(
            [
                "--initialpose-opt-in",
                "--initialpose-x",
                "0",
                "--initialpose-y",
                "0",
                "--path-generation-opt-in",
                "--path-goal-x",
                "0.8",
                "--path-goal-y",
                "0",
            ]
        )
        map_analysis = {
            "ok": True,
            "resolution": 0.05,
            "bounds": {"min_x": -6.15, "min_y": -5.92, "max_x": 5.10, "max_y": -0.02},
            "cell_counts": {"free": 0, "unknown": 26506, "occupied": 44, "other": 0},
        }

        request = HELPER.path_generation_request(
            args,
            map_analysis=map_analysis,
            initialpose_payload=HELPER.initialpose_request(args),
        )

        self.assertTrue(request["enabled"])
        self.assertTrue(request["use_start"])
        self.assertTrue(request["adapted_from_map_bounds"])
        self.assertEqual("map_bounds_adapted_no_motion_planner_probe", request["adaptation_boundary"])
        self.assertAlmostEqual(-0.27, request["start_y"], places=2)
        self.assertAlmostEqual(-0.27, request["y"], places=2)
        self.assertAlmostEqual(0.8, request["x"])
        self.assertFalse(request["map_goal_diagnostics"]["start_in_bounds"])
        self.assertFalse(request["map_goal_diagnostics"]["goal_in_bounds"])
        self.assertEqual(0, request["map_free_cell_count"])
        self.assertFalse(request["map_has_free_cells_for_path_proof"])

    def test_resolve_managed_map_yaml_prefers_free_cell_candidate(self) -> None:
        """默认 managed runtime 必须避开空 trashbot_map，优先使用包含 free cell 的地图。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            maps = Path(temp_dir)
            empty_yaml = maps / "trashbot_map.yaml"
            empty_pgm = maps / "trashbot_map.pgm"
            usable_yaml = maps / "fixed_free_cells.yaml"
            usable_pgm = maps / "fixed_free_cells.pgm"
            empty_yaml.write_text(
                "image: trashbot_map.pgm\nresolution: 0.05\norigin: [0, 0, 0]\n",
                encoding="utf-8",
            )
            empty_pgm.write_bytes(b"P5\n2 1\n255\n" + bytes([205, 205]))
            usable_yaml.write_text(
                "image: fixed_free_cells.pgm\nresolution: 0.05\norigin: [0, 0, 0]\n",
                encoding="utf-8",
            )
            usable_pgm.write_bytes(b"P5\n2 1\n255\n" + bytes([205, 254]))
            args = HELPER.parse_args([])
            map_yaml, source = HELPER.resolve_managed_map_yaml(
                args,
                {
                    "map_yaml_candidates": [
                        {"path": str(empty_yaml), "mtime_ms": 20},
                        {"path": str(usable_yaml), "mtime_ms": 10},
                    ]
                },
            )

        self.assertEqual(str(usable_yaml), map_yaml)
        self.assertEqual("canonical_map_proof_usable_yaml_candidate", source)

    def test_effective_map_inputs_uses_managed_runtime_when_map_consumed(self) -> None:
        """本轮 managed runtime 已消费可用地图时，旧 canonical map proof blocker 不应阻止 planner。"""
        map_inputs = {
            "inputs_ready": False,
            "root_causes": [{"layer": "canonical map proof", "reason": "map_lifecycle_proof_not_clean"}],
        }
        effective = HELPER.effective_map_inputs_for_runtime(
            map_inputs,
            managed_runtime_requested=True,
            managed_runtime_started=True,
            managed_map_analysis={"cell_counts": {"free": 3}},
            map_once_observed=True,
        )

        self.assertTrue(effective["inputs_ready"])
        self.assertTrue(effective["managed_runtime_map_inputs_ready"])
        self.assertEqual([], effective["root_causes"])
        self.assertEqual([{"layer": "canonical map proof", "reason": "map_lifecycle_proof_not_clean"}], map_inputs["root_causes"])

    def test_effective_map_inputs_keeps_blocker_until_runtime_map_observed(self) -> None:
        """只有启动 runtime 不够，必须确认 /map 被观测到才允许覆盖旧 map proof。"""
        map_inputs = {
            "inputs_ready": False,
            "root_causes": [{"layer": "canonical map proof", "reason": "map_lifecycle_proof_not_clean"}],
        }
        effective = HELPER.effective_map_inputs_for_runtime(
            map_inputs,
            managed_runtime_requested=True,
            managed_runtime_started=True,
            managed_map_analysis={"cell_counts": {"free": 3}},
            map_once_observed=False,
        )

        self.assertIs(map_inputs, effective)

    def test_managed_runtime_observed_node_names_uses_wait_history(self) -> None:
        """planner lifecycle CLI 超时时，也要保留 wait history 里的节点观测证据。"""
        managed_runtime = {
            "wait_result": {
                "node_list": {"node_names": ["map_server"]},
                "observed_node_names": ["planner_server"],
                "history": [
                    {"node_list_command": {"node_names": ["amcl", "planner_server"]}},
                    {
                        "cumulative_node_names": ["controller_server"],
                        "node_list_command": {"stdout": "/lifecycle_manager\n"},
                    },
                ],
            }
        }

        names = HELPER.managed_runtime_observed_node_names(managed_runtime)

        self.assertIn("/map_server", names)
        self.assertIn("/amcl", names)
        self.assertIn("/planner_server", names)
        self.assertIn("/controller_server", names)

    def test_path_generation_blocks_unknown_only_map_before_action(self) -> None:
        """没有 free cell 的地图不能进入 Nav2 action，避免把弱地图误报为可规划。"""
        args = HELPER.parse_args(
            [
                "--initialpose-opt-in",
                "--path-generation-opt-in",
                "--path-goal-x",
                "0.8",
            ]
        )
        map_analysis = {
            "ok": True,
            "resolution": 0.05,
            "bounds": {"min_x": -6.15, "min_y": -5.92, "max_x": 5.10, "max_y": -0.02},
            "cell_counts": {"free": 0, "unknown": 26506, "occupied": 44, "other": 0},
        }

        request, result, summary, root_causes = HELPER.maybe_compute_path_generation(
            args,
            ros2_ok=True,
            localization_ready=True,
            planner_server_active=True,
            map_analysis=map_analysis,
            initialpose_payload=HELPER.initialpose_request(args),
        )

        self.assertTrue(request["enabled"])
        self.assertFalse(result["attempted"])
        self.assertFalse(result["service_available"])
        self.assertEqual("path_generation_blocked_by_map_has_no_free_cells", result["boundary"])
        self.assertEqual("path_generation_blocked_by_map_has_no_free_cells", summary["boundary"])
        self.assertEqual(
            [{"layer": "map quality", "reason": "map_has_no_free_cells_for_nav2_path_proof"}],
            root_causes,
        )
        self.assertEqual(0, result["path_goal_request"]["map_free_cell_count"])
        self.assertFalse(result["path_goal_request"]["map_has_free_cells_for_path_proof"])

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

    def test_tf_source_diagnostics_classifies_amcl_map_odom_missing(self) -> None:
        """source inventory 要先于 tf2_echo 给出 AMCL 未广播 map->odom 的下一层原因。"""
        args = HELPER.parse_args([])
        combined_stdout = """
__TOPIC_LIST_T__
/tf [tf2_msgs/msg/TFMessage]
/tf_static [tf2_msgs/msg/TFMessage]
__AMCL_NODE_INFO__
/amcl
  Subscribers:
    * /initialpose [geometry_msgs/msg/PoseWithCovarianceStamped]
    * /scan [sensor_msgs/msg/LaserScan]
  Publishers:
    * /amcl_pose [geometry_msgs/msg/PoseWithCovarianceStamped]
    * /particle_cloud [nav2_msgs/msg/ParticleCloud]
__AMCL_PARAMS__
__PARAM__tf_broadcast=Boolean value is: True
__PARAM__global_frame_id=String value is: map
__PARAM__odom_frame_id=String value is: odom
__PARAM__base_frame_id=String value is: base_link
__TF_ONCE__
WARNING: topic echo timed out
__TF_STATIC_ONCE__
transforms:
- header:
    frame_id: odom
  child_frame_id: base_link
- header:
    frame_id: base_link
  child_frame_id: laser_frame
"""
        amcl_pose = {"stdout": "header:\n  frame_id: map\npose:\n  pose:\n"}
        source = HELPER.build_tf_source_diagnostics(
            args,
            {"stdout": combined_stdout, "ok": True},
            amcl_pose_result=amcl_pose,
        )
        observed = {
            "map_to_odom": bool(source["map_to_odom_source_observed"]),
            "odom_to_base_link": bool(source["odom_to_base_link_source_observed"]),
            "base_link_to_laser_frame": bool(source["base_link_to_laser_frame_source_observed"]),
            "map_to_base_link": False,
        }
        diagnostics = HELPER.build_tf_chain_diagnostics(
            args=args,
            results={"map_to_odom": {"executed": True, "ok": False, "stdout": "Invalid frame ID \"map\""}},
            observed=observed,
            tf_source_diagnostics=source,
        )

        classification = HELPER.classify_tf_chain_failure(args=args, observed=observed, diagnostics=diagnostics)

        self.assertTrue(source["tf_topics_observed"]["/tf"])
        self.assertTrue(source["tf_static_observed"])
        self.assertEqual("map", source["amcl_pose_frame_id"])
        self.assertEqual("True", source["amcl_tf_broadcast_param"])
        self.assertTrue(source["amcl_param_probe_ok"])
        self.assertTrue(source["amcl_node_info_observed"])
        self.assertTrue(source["odom_to_base_link_source_observed"])
        self.assertTrue(source["base_link_to_laser_frame_source_observed"])
        self.assertTrue(source["tf_source_root_cause_detail"]["odom_to_base_link_source_observed"])
        self.assertFalse(source["map_to_odom_source_observed"])
        self.assertEqual("amcl_map_to_odom_tf_not_observed_on_tf", source["amcl_tf_root_cause"])
        self.assertEqual("blocked_by_missing_map_to_odom", classification["map_to_base_link"])
        self.assertEqual("amcl_map_to_odom_tf_not_observed_on_tf", classification["reason"])

    def test_rclpy_amcl_probe_overrides_empty_cli_param_markers(self) -> None:
        """AMCL 参数必须能从轻量 rclpy probe 填实，不能再停在 CLI marker 空段。"""
        args = HELPER.parse_args([])
        combined_stdout = """
__TOPIC_LIST_T__
/tf [tf2_msgs/msg/TFMessage]
/tf_static [tf2_msgs/msg/TFMessage]
__AMCL_NODE_INFO__
__AMCL_PARAMS__
__TF_ONCE__
__TF_STATIC_ONCE__
"""
        amcl_probe = {
            "param_probe_ok": True,
            "node_info_observed": True,
            "params": {
                "tf_broadcast": True,
                "global_frame_id": "map",
                "odom_frame_id": "odom",
                "base_frame_id": "base_link",
            },
            "publishers": [{"topic": "/amcl_pose", "type": "geometry_msgs/msg/PoseWithCovarianceStamped"}],
            "subscribers": [{"topic": "/scan", "type": "sensor_msgs/msg/LaserScan"}],
            "boundary": "rclpy_amcl_params_and_graph_observed",
        }

        source = HELPER.build_tf_source_diagnostics(
            args,
            {"stdout": combined_stdout, "ok": True},
            amcl_pose_result={"stdout": "header:\n  frame_id: map\n"},
            amcl_probe=amcl_probe,
        )

        self.assertTrue(source["amcl_param_probe_ok"])
        self.assertTrue(source["amcl_node_info_observed"])
        self.assertEqual("true", source["amcl_tf_broadcast_param"])
        self.assertEqual("odom", source["amcl_frame_params"]["odom_frame_id"])
        self.assertEqual("/amcl_pose", source["amcl_node_publishers"][0]["topic"])

    def test_tf_source_diagnostics_keeps_static_tf_when_amcl_params_lag(self) -> None:
        """AMCL 参数服务晚到时，source probe 仍必须保留 /tf_static 采样结果。"""
        args = HELPER.parse_args([])
        amcl_probe = {
            "param_probe_ok": False,
            "node_info_observed": False,
            "params": {},
            "topic_types": {"/tf_static": "tf2_msgs/msg/TFMessage"},
            "static_edges": [
                {"parent": "odom", "child": "base_link", "topic": "/tf_static"},
                {"parent": "base_link", "child": "laser_frame", "topic": "/tf_static"},
            ],
            "dynamic_edges": [],
            "command_statuses": {"rclpy_graph": 0, "tf": 124, "tf_static": 0},
            "boundary": "amcl_parameter_service_unavailable_after_tf_probe",
        }

        source = HELPER.build_tf_source_diagnostics(
            args,
            {"stdout": "", "ok": False},
            amcl_pose_result={"stdout": "header:\n  frame_id: map\n"},
            amcl_probe=amcl_probe,
        )

        self.assertFalse(source["tf_topics_observed"]["/tf"])
        self.assertTrue(source["tf_static_observed"])
        self.assertTrue(source["odom_to_base_link_source_observed"])
        self.assertTrue(source["base_link_to_laser_frame_source_observed"])
        self.assertFalse(source["amcl_param_probe_ok"])
        self.assertEqual("/tf_topic_missing", source["amcl_tf_root_cause"])

    def test_tf_probe_uses_wider_echo_window_after_source_probe(self) -> None:
        """现场 ros2 CLI 启动慢，四段 fallback tf2_echo 必须使用统一宽窗口。"""
        text = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("collect_amcl_rclpy_probe(timeout_s=4.0)", text)
        self.assertIn("TF_ECHO_SHELL_TIMEOUT_S = 10.0", text)
        self.assertIn("TF_ECHO_PROCESS_TIMEOUT_S = 14.0", text)
        self.assertEqual(4, text.count("timeout {TF_ECHO_SHELL_TIMEOUT_S:g} ros2 run tf2_ros tf2_echo"))
        self.assertNotIn("timeout 2 ros2 run tf2_ros tf2_echo", text)

    def test_managed_static_tf_process_summary_classifies_roles(self) -> None:
        """static TF 源必须记录进程角色，便于区分没启动和 QoS 未观测。"""
        args = HELPER.parse_args([])
        runtime = {"started": True, "process_group": 456}
        fake_members = [
            {
                "pid": 11,
                "pgid": 456,
                "command": (
                    "python3 -c 'rclpy.create_node(\"managed_static_tf_broadcaster\")' "
                    "static_tf_odom_base static_tf_base_laser odom_to_base_link base_link_to_laser_frame"
                ),
            },
        ]
        with mock.patch.object(HELPER, "process_group_members", return_value=fake_members):
            summary = HELPER.managed_static_tf_process_summary(args, runtime)

        self.assertTrue(summary["all_expected_processes_observed"])
        self.assertEqual(["static_tf_base_laser", "static_tf_odom_base"], summary["observed_roles"])
        self.assertEqual("single_rclpy_static_transform_broadcaster_transient_local", summary["source_strategy"])
        self.assertEqual(1, len(summary["processes"]))
        self.assertEqual(
            ["static_tf_base_laser", "static_tf_odom_base"],
            summary["processes"][0]["roles"],
        )

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
            "planner_server_observed",
            "planner_server_ready_for_path_generation",
            "controller_server_active",
            "controller_server_observed",
            "controller_server_requested",
            "planner_readiness_summary",
            "managed_runtime_wait_result",
            "require_planner_server=bool(args.path_generation_opt_in)",
            "explicit_opt_in_compute_path_to_pose_action_no_motion",
            "if source_chain_complete:",
            "planner_recheck_deferred_until_localization_ready",
        ):
            self.assertIn(required, text)
        self.assertNotIn("source_chain_complete and not args.path_generation_opt_in", text)

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
        """PC 检查路径固定 body 不应被 upper cap 截断，PC 必须等得更久。"""
        spec = importlib.util.spec_from_file_location("upper_robot_api", SCRIPT.parent / "upper_robot_api.py")
        assert spec is not None and spec.loader is not None
        api_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api_mod)

        budget = api_mod.nav2_runtime_proof_process_timeout_budget(
            timeout_s=30.0,
            managed_runtime_opt_in=True,
            managed_timeout_s=30.0,
            initialpose_opt_in=True,
            path_generation_opt_in=True,
            path_generation_timeout_s=30.0,
        )

        # fixed 30s collector + 30s managed + 30s path 会形成 120s raw 预算；upper 不截断它。
        self.assertEqual(120.0, budget["raw_timeout_s"])
        self.assertEqual(120.0, budget["process_timeout_s"])
        self.assertEqual(132.0, budget["cap_s"])
        self.assertEqual(150.0, budget["pc_proxy_budget_s"])
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
                timeout_s=30.0,
                managed_runtime_opt_in=True,
                managed_timeout_s=30.0,
                managed_map_yaml="/tmp/maps/trashbot_map.yaml",
                initialpose_opt_in=True,
                initialpose_x=0.0,
                initialpose_y=0.0,
                initialpose_yaw=0.0,
                initialpose_frame_id="map",
                path_generation_opt_in=True,
                path_generation_timeout_s=30.0,
                path_goal_frame_id="map",
                path_goal_x=0.8,
                path_goal_y=0.0,
                path_goal_yaw=0.0,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(120.0, result["process_timeout_s"])
        self.assertEqual(120.0, run_mock.call_args.args[1])
        self.assertTrue(run_mock.call_args.kwargs["cleanup_residuals"])

    def test_upper_api_does_not_cleanup_external_nav2_runtime_when_reusing_graph(self) -> None:
        """复用已启动 Nav2 lifecycle 时，helper 超时不能扫杀外部 ROS 栈。"""
        spec = importlib.util.spec_from_file_location("upper_robot_api", SCRIPT.parent / "upper_robot_api.py")
        assert spec is not None and spec.loader is not None
        api_mod = importlib.util.module_from_spec(spec)
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
            api_mod.run_nav2_runtime_proof_helper(
                artifact_path="/tmp/nav2.json",
                map_proof_path="/tmp/map.json",
                map_artifact_dir="/tmp/maps",
                timeout_s=30.0,
                managed_runtime_opt_in=False,
                managed_timeout_s=0.0,
                managed_map_yaml="",
                initialpose_opt_in=True,
                initialpose_x=0.0,
                initialpose_y=0.0,
                initialpose_yaw=0.0,
                initialpose_frame_id="map",
                path_generation_opt_in=True,
                path_generation_timeout_s=30.0,
                path_goal_frame_id="map",
                path_goal_x=0.8,
                path_goal_y=0.0,
                path_goal_yaw=0.0,
            )

        self.assertFalse(run_mock.call_args.kwargs["cleanup_residuals"])

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

        # 超出 fixed body 的扩展场景仍要封顶；PC 150s 预算仍比 upper cap 更长。
        self.assertEqual(132.0, budget["process_timeout_s"])
        self.assertEqual(150.0, budget["raw_timeout_s"])
        self.assertEqual(132.0, budget["cap_s"])
        self.assertEqual(150.0, budget["pc_proxy_budget_s"])
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
        transform = HELPER.parse_tf_echo_transform(result, parent_frame_id="base_link", child_frame_id="laser_frame")
        self.assertIsNotNone(transform)
        self.assertEqual("base_link", transform["parent_frame_id"])
        self.assertEqual("laser_frame", transform["child_frame_id"])
        self.assertAlmostEqual(1.0, transform["translation"]["x"])
        self.assertAlmostEqual(2.0, transform["translation"]["y"])
        self.assertAlmostEqual(0.0, transform["rotation"]["yaw"])

    def test_tf_static_yaml_transform_is_parsed_for_lidar_extrinsic(self) -> None:
        """`/tf_static` 的 YAML echo 已有外参时，helper 不能只记录 edge 而丢数值。"""
        text = (
            "transforms:\n"
            "- header:\n"
            "    stamp:\n"
            "      sec: 1782364051\n"
            "      nanosec: 613206066\n"
            "    frame_id: base_link\n"
            "  child_frame_id: laser_frame\n"
            "  transform:\n"
            "    translation:\n"
            "      x: 0.0\n"
            "      y: 0.0\n"
            "      z: 0.0\n"
            "    rotation:\n"
            "      x: 0.0\n"
            "      y: 0.0\n"
            "      z: 0.0\n"
            "      w: 1.0\n"
        )

        transforms = HELPER.parse_tf_topic_transforms(text, source_topic="/tf_static")
        transform = HELPER.find_tf_topic_transform(
            transforms,
            parent_frame_id="base_link",
            child_frame_id="laser_frame",
        )

        self.assertIsNotNone(transform)
        self.assertEqual("/tf_static", transform["source"])
        self.assertAlmostEqual(0.0, transform["translation"]["x"])
        self.assertAlmostEqual(0.0, transform["translation"]["y"])
        self.assertAlmostEqual(0.0, transform["translation"]["z"])
        self.assertAlmostEqual(0.0, transform["rotation"]["yaw"])

    def test_tf_source_diagnostics_exposes_lidar_extrinsic_transform(self) -> None:
        """source inventory 快路径必须把 `base_link -> laser_frame` 数值交给 upper/PC。"""
        args = HELPER.parse_args([])
        transform = {
            "parent_frame_id": "base_link",
            "child_frame_id": "laser_frame",
            "translation": {"x": 0.12, "y": -0.03, "z": 0.08},
            "rotation": {"yaw": 0.0, "quaternion": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}},
            "source": "/tf_static",
        }
        probe = {
            "topic_types": {"/tf": "tf2_msgs/msg/TFMessage", "/tf_static": "tf2_msgs/msg/TFMessage"},
            "params": {"tf_broadcast": "true", "global_frame_id": "map", "odom_frame_id": "odom", "base_frame_id": "base_link"},
            "dynamic_edges": [{"parent": "map", "child": "odom", "topic": "/tf"}],
            "static_edges": [
                {"parent": "odom", "child": "base_link", "topic": "/tf_static"},
                {"parent": "base_link", "child": "laser_frame", "topic": "/tf_static"},
            ],
            "static_transforms": [transform],
            "publishers": [{"topic": "/tf", "type": "tf2_msgs/msg/TFMessage"}],
            "subscribers": [{"topic": "/scan", "type": "sensor_msgs/msg/LaserScan"}],
            "node_info_observed": True,
            "param_probe_ok": True,
            "command_statuses": {"rclpy_graph": 0, "tf": 0, "tf_static": 0},
            "boundary": "rclpy_amcl_params_graph_tf_probe_observed",
        }

        diagnostics = HELPER.build_tf_source_diagnostics(
            args,
            {"stdout": ""},
            amcl_pose_result={"stdout": ""},
            amcl_probe=probe,
        )

        self.assertTrue(diagnostics["base_link_to_laser_frame_source_observed"])
        self.assertEqual(transform, diagnostics["base_link_to_laser_frame_source_transform"])
        self.assertIn(transform, diagnostics["tf_frame_inventory"]["static_transforms"])

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
