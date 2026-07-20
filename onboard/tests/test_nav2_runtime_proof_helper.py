"""Nav2 runtime proof helper 的本地静态测试。

这些测试不启动真实 ROS2，也不触碰 WAVE ROVER、底盘 UART 或运动 API。
测试目标是锁定 helper/API 的 CLI、managed runtime 参数透传和 no-motion 安全边界。
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o10_amcl_nav2_runtime_proof.py"
REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("o10_amcl_nav2_runtime_proof", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


class Nav2RuntimeProofHelperTests(unittest.TestCase):
    """锁定正式 API 调用的 O10 no-motion helper 和 managed runtime 边界。"""

    def _source_payload(self, *, sourced: bool = True) -> dict[str, object]:
        """构造单 shell preflight 的 source stage，测试只关心分层分类。"""
        return {
            "ok": sourced,
            "ros_setup": {"exists": True, "sourced": sourced, "returncode": 0 if sourced else 3, "elapsed_ms": 20},
            "workspace_setup": {"exists": True, "sourced": sourced, "skipped": False, "returncode": 0 if sourced else 3},
            "cd_ok": sourced,
        }

    def _rclpy_payload(self, *, ok: bool = True) -> dict[str, object]:
        """rclpy payload 保持旧字段名，确保 legacy artifact reader 仍能读取。"""
        return {
            "python_executable": "/usr/bin/python3",
            "python_version": "3.10.0",
            "sys_path_head": ["/opt/ros/humble/local/lib/python3.10/dist-packages"],
            "rclpy_import_ok": ok,
            "rclpy_file": "/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py" if ok else None,
            "error": None if ok else {"type": "ImportError", "message": "No module named rclpy"},
        }

    def _amortized_preflight_payload(
        self,
        *,
        source: dict[str, object] | None = None,
        path_lookup: dict[str, object] | None = None,
        ros2_cli_path: str | None = "/opt/ros/humble/bin/ros2",
        lightweight_results: dict[str, object] | None = None,
        cli_invocation: dict[str, object] | None = None,
        rclpy_payload: dict[str, object] | None = None,
        rclpy_command: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """source/path/CLI/rclpy 都来自同一 payload，模拟本轮 single-shell 合同。"""
        source_payload = source or self._source_payload()
        path_payload = path_lookup or {
            "command_v": {"executed": True, "ok": bool(ros2_cli_path), "stdout": f"{ros2_cli_path}\n" if ros2_cli_path else "", "stderr": "", "timed_out": False},
            "type_a": {"executed": True, "ok": bool(ros2_cli_path), "stdout": f"ros2 is {ros2_cli_path}\n" if ros2_cli_path else "", "stderr": "", "timed_out": False},
            "which": {"executed": True, "ok": bool(ros2_cli_path), "stdout": f"{ros2_cli_path}\n" if ros2_cli_path else "", "stderr": "", "timed_out": False},
        }
        invocation_payload = cli_invocation or {
            "label": "ros2_help",
            "command": "ros2 --help >/dev/null",
            "executed": bool(ros2_cli_path),
            "ok": bool(ros2_cli_path),
            "timed_out": False,
            "returncode": 0 if ros2_cli_path else None,
        }
        lightweight_payload = lightweight_results or {
            "ros2_daemon_status": {
                "label": "ros2_daemon_status",
                "command": "ros2 daemon status",
                "executed": bool(ros2_cli_path),
                "ok": bool(ros2_cli_path),
                "timed_out": False,
                "returncode": 0 if ros2_cli_path else None,
            },
            "ros2_node_list": {
                "label": "ros2_node_list",
                "command": "ros2 node list",
                "executed": bool(ros2_cli_path),
                "ok": bool(ros2_cli_path),
                "timed_out": False,
                "returncode": 0 if ros2_cli_path else None,
            },
        }
        rclpy = rclpy_payload or self._rclpy_payload()
        rclpy_result = rclpy_command or {
            "label": "rclpy_import",
            "command": "python3 -c <rclpy import probe>",
            "executed": True,
            "ok": bool(rclpy.get("rclpy_import_ok")),
            "timed_out": False,
            "returncode": 0 if rclpy.get("rclpy_import_ok") else 1,
        }
        return {
            "kind": "source_amortized_cli_preflight_final",
            "schema": HELPER.SOURCE_AMORTIZED_CLI_PREFLIGHT_SCHEMA,
            "source_amortized_cli_preflight": True,
            "source_amortized": True,
            "source_and_cli_in_one_shell": True,
            "per_command_source_overhead_eliminated": bool(source_payload.get("ok")),
            "per_command_source_overhead_excluded": bool(source_payload.get("ok")),
            "source_stage": source_payload,
            "path_lookup": path_payload,
            "ros2_cli_path": ros2_cli_path,
            "lightweight_readiness": {
                "ok": any(bool(entry.get("ok")) for entry in lightweight_payload.values() if isinstance(entry, dict)),
                "executed": any(bool(entry.get("executed")) for entry in lightweight_payload.values() if isinstance(entry, dict)),
                "command_count": len(lightweight_payload),
                "successful_labels": [
                    str(entry.get("label") or "")
                    for entry in lightweight_payload.values()
                    if isinstance(entry, dict) and entry.get("ok")
                ],
                "timed_out_labels": [
                    str(entry.get("label") or "")
                    for entry in lightweight_payload.values()
                    if isinstance(entry, dict) and entry.get("timed_out")
                ],
                "primary_label": "ros2_daemon_status",
                "primary_command": "ros2 daemon status",
                "primary_boundary": "lightweight_cli_ready",
                "results": lightweight_payload,
            },
            "cli_invocation": invocation_payload,
            "python_rclpy": rclpy,
            "python_rclpy_command": rclpy_result,
            "commands_executed_after_single_source": [
                "command_v",
                "type_a",
                "which",
                "ros2_daemon_status",
                "ros2_node_list",
                "ros2_help",
                "rclpy_import",
            ],
            "ok": bool(source_payload.get("ok")),
            "boundary": "source_amortized_cli_preflight_completed" if source_payload.get("ok") else "source_amortized_cli_preflight_source_stage_failed",
        }

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
            "--output-json",
            "--map-proof",
            "--map-dir",
            "--timeout-s",
            "--strict-no-motion",
            "--no-base-uart",
            "--managed-runtime-opt-in",
            "--managed-timeout-s",
            "--managed-lifecycle-start-delay-s",
            "--managed-map-yaml",
            "--reuse-existing-lidar-lifecycle",
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

    def test_ros2_preflight_timeout_allows_board_setup_latency(self) -> None:
        """真实 API 子进程 source ROS/workspace 会抖动，preflight 必须一次 source 后分层探测。"""
        self.assertEqual(6.0, HELPER.ROS2_PREFLIGHT_TIMEOUT_S)
        self.assertEqual(12.0, HELPER.SOURCE_PREFLIGHT_TIMEOUT_S)
        self.assertEqual(30.0, HELPER.SOURCE_AMORTIZED_CLI_PREFLIGHT_TIMEOUT_S)
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("board_source_amortized_cli_preflight_command(args)", text)
        self.assertIn("timeout_s=SOURCE_AMORTIZED_CLI_PREFLIGHT_TIMEOUT_S", text)
        self.assertIn("source_and_cli_in_one_shell", text)
        self.assertNotIn("run_ros(\n            args,\n            board_cli_layer_probe_command()", text)
        self.assertNotIn("run_ros(args, ROS2_PREFLIGHT_COMMAND, timeout_s=3.0)", text)

    def test_board_source_preflight_exposes_cli_ready_separately_from_runtime_ready(self) -> None:
        """板端 rclpy import 抖动时，不能把 ros2 CLI 与 managed runtime 启动入口一起误判死。"""
        preflight_payload = self._amortized_preflight_payload(
            rclpy_payload=self._rclpy_payload(ok=False),
            rclpy_command={
                "label": "rclpy_import",
                "command": "python3 -c <rclpy import probe>",
                "executed": True,
                "ok": False,
                "timed_out": True,
                "returncode": None,
            },
        )
        with mock.patch.object(
            HELPER,
            "run_bash",
            return_value={
                "executed": True,
                "ok": True,
                "stdout": json.dumps(preflight_payload, ensure_ascii=False),
                "stderr": "",
                "timed_out": False,
            },
        ) as run_bash_mock, mock.patch.object(HELPER, "run_ros") as run_ros_mock:
            result = HELPER.board_source_preflight(HELPER.parse_args([]))

        run_bash_mock.assert_called_once()
        self.assertEqual("source_amortized_cli_preflight", run_bash_mock.call_args.kwargs["artifact_command"])
        run_ros_mock.assert_not_called()
        self.assertTrue(result["source_stage_ok"])
        self.assertTrue(result["ros2_cli_ok"])
        self.assertTrue(result["lightweight_cli_ready"])
        self.assertTrue(result["cli_ready"])
        self.assertFalse(result["runtime_ready"])
        self.assertFalse(result["ready"])
        self.assertTrue(result["source_and_cli_in_one_shell"])
        self.assertTrue(result["per_command_source_overhead_eliminated"])
        self.assertEqual("board_source_preflight_rclpy_import_timeout", result["classification"])

    def test_parse_args_defaults_keep_read_only(self) -> None:
        """默认参数必须保持旧 collector 语义，不因新增 managed flag 产生副作用。"""
        args = HELPER.parse_args([])

        self.assertFalse(args.managed_runtime_opt_in)
        self.assertFalse(args.strict_no_motion)
        self.assertFalse(args.no_base_uart)
        self.assertEqual("", args.managed_map_yaml)
        self.assertFalse(args.reuse_existing_lidar_lifecycle)
        self.assertEqual(20.0, args.managed_timeout_s)
        self.assertEqual(3.0, args.managed_lifecycle_start_delay_s)
        self.assertFalse(args.initialpose_opt_in)
        self.assertFalse(args.path_generation_opt_in)
        self.assertEqual(20.0, args.path_generation_timeout_s)
        self.assertEqual("map", args.path_goal_frame_id)
        self.assertEqual(0.8, args.path_goal_x)
        self.assertEqual(0.0, args.path_goal_y)
        self.assertEqual(0.0, args.path_goal_yaw)

    def test_source_prefix_forces_udp_only_fastdds_transport(self) -> None:
        """所有 ROS CLI 子进程都必须继承 DDS no-SHM guard，避免板端端口锁拖死 lifecycle RPC。"""
        prefix = HELPER.source_prefix(HELPER.parse_args([]))

        self.assertIn("export RMW_FASTRTPS_USE_SHM=0", prefix)
        self.assertIn("export FASTDDS_BUILTIN_TRANSPORTS=UDPv4", prefix)
        self.assertLess(prefix.index("source /opt/ros/humble/setup.bash"), prefix.index("export RMW_FASTRTPS_USE_SHM=0"))
        self.assertLess(prefix.index("export FASTDDS_BUILTIN_TRANSPORTS=UDPv4"), prefix.index("cd /root/rober/onboard"))

    def test_parse_args_accepts_no_motion_output_json_aliases(self) -> None:
        """现场验收命令使用的 no-motion/output-json flag 只能加强护栏，不能触发运动。"""
        args = HELPER.parse_args(["--strict-no-motion", "--no-base-uart", "--output-json", "/tmp/o10.json"])

        self.assertTrue(args.strict_no_motion)
        self.assertTrue(args.no_base_uart)
        self.assertEqual("/tmp/o10.json", args.output)
        self.assertFalse(args.managed_runtime_opt_in)
        self.assertFalse(args.path_generation_opt_in)

    def test_path_generation_envelope_fields_are_explicit(self) -> None:
        """顶层 artifact 要显式带 path generation 字段，避免 strict no-motion 输出 null。"""
        self.assertEqual(
            {"path_generation_attempted": False, "path_generated": False},
            HELPER.path_generation_envelope_fields(None),
        )
        self.assertEqual(
            {"path_generation_attempted": True, "path_generated": False},
            HELPER.path_generation_envelope_fields({"path_generation_attempted": 1, "path_generated": ""}),
        )

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

    def test_parse_first_ros_stamp_accepts_rclpy_json_probe_output(self) -> None:
        """rclpy `/scan` probe 输出 JSON 时，freshness 仍要能复用统一 stamp 解析。"""
        stamp = HELPER.parse_first_ros_stamp(
            json.dumps({"stamp": {"sec": 1780000000, "nanosec": 123000000}}, ensure_ascii=False),
            source="/scan.header.stamp",
        )

        self.assertTrue(stamp["parsed"])
        self.assertEqual(1780000000, stamp["sec"])
        self.assertEqual(123000000, stamp["nanosec"])

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

    def test_build_scan_probe_attempts_keeps_best_effort_and_reliable_paths(self) -> None:
        """`/scan` probe 必须先保留 BEST_EFFORT/RELIABLE child 对照，再回退默认 CLI。"""
        attempts = HELPER.build_scan_probe_attempts(HELPER.parse_args(["--timeout-s", "18"]))

        self.assertEqual("rclpy_best_effort_once", attempts[0]["label"])
        self.assertEqual("best_effort", attempts[0]["qos_profile"])
        self.assertEqual("rclpy_subscription", attempts[0]["source"])
        self.assertEqual("ros_sourced_child_python", attempts[0]["runtime"])
        self.assertEqual("BEST_EFFORT", attempts[0]["reliability"])
        self.assertEqual(18.0, attempts[0]["timeout_s"])
        self.assertEqual("rclpy_reliable_once", attempts[1]["label"])
        self.assertEqual("reliable", attempts[1]["qos_profile"])
        self.assertEqual("RELIABLE", attempts[1]["reliability"])
        self.assertEqual("cli_sensor_data_echo_once", attempts[2]["label"])
        self.assertIn("--qos-profile sensor_data", attempts[2]["command"])
        self.assertEqual("cli_default_echo_once", attempts[3]["label"])

    def test_rclpy_scan_child_command_is_sourced_probe_only(self) -> None:
        """`/scan` rclpy probe 必须在 child Python 中跑，避免主进程 ROS env 缺失。"""
        command = HELPER.rclpy_scan_child_python_command(
            2.2,
            attempt_label="rclpy_best_effort_once",
            profile_label="sensor_data_best_effort",
            reliability="BEST_EFFORT",
            durability="VOLATILE",
        )

        self.assertIn("python3 - <<'PY'", command)
        self.assertIn("RMW_FASTRTPS_USE_SHM", command)
        self.assertIn("from sensor_msgs.msg import LaserScan", command)
        self.assertIn("o10_scan_probe_child", command)
        self.assertIn('"runtime": "ros_sourced_child_python"', command)
        self.assertIn("RELIABILITY_NAME = 'BEST_EFFORT'", command)
        self.assertIn("PROFILE_LABEL = 'sensor_data_best_effort'", command)
        self.assertIn("os._exit(returncode)", command)
        self.assertNotIn("/cmd_vel", command)
        self.assertNotIn("NavigateToPose", command)

    def test_rclpy_import_failure_classification_is_specific(self) -> None:
        """板端 rclpy import failure 要区分 shared-library、ABI 和未 source 环境。"""
        self.assertEqual(
            "missing_shared_library",
            HELPER.classify_rclpy_import_failure(
                "librcl_action.so: cannot open shared object file: No such file or directory\n"
                "_rclpy_pybind11 failed to be imported while being present",
                {"LD_LIBRARY_PATH": "/opt/ros/humble/lib"},
            ),
        )
        self.assertEqual(
            "environment_not_sourced",
            HELPER.classify_rclpy_import_failure(
                "librcl_action.so: cannot open shared object file: No such file or directory",
                {"LD_LIBRARY_PATH": ""},
            ),
        )
        self.assertEqual(
            "python_abi_mismatch",
            HELPER.classify_rclpy_import_failure(
                "_rclpy_pybind11.cpython-310-aarch64-linux-gnu.so: undefined symbol: rcl_action_symbol",
                {"LD_LIBRARY_PATH": "/opt/ros/humble/lib", "PYTHONPATH": "/opt/ros/humble/local/lib/python3.10/dist-packages"},
            ),
        )

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

    def test_initialpose_payload_uses_latest_tf_stamp(self) -> None:
        """initialpose 显式 stamp=0，避免 AMCL 在现场 TF 刚启动时按旧时间戳外推失败。"""
        args = HELPER.parse_args(["--initialpose-opt-in"])
        payload = json.loads(HELPER.initialpose_payload(HELPER.initialpose_request(args)))

        self.assertEqual({"sec": 0, "nanosec": 0}, payload["header"]["stamp"])
        self.assertEqual("map", payload["header"]["frame_id"])

    def test_canonical_map_free_cell_world_pose_audit_is_deterministic(self) -> None:
        """canonical free cell 必须绑定 YAML/PGM hash，并可复算 image->world pose。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pgm = root / "map.pgm"
            pgm.write_bytes(b"P5\n3 3\n255\n" + bytes([0, 0, 0, 0, 254, 0, 0, 0, 0]))
            yaml_path = root / "map.yaml"
            yaml_path.write_text(
                "image: map.pgm\nresolution: 0.5\norigin:\n- -1.0\n- -2.0\n- 0.0\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\nmode: trinary\n",
                encoding="utf-8",
            )

            audit = HELPER.canonical_initialpose_map_audit(str(yaml_path), yaw=0.0)
            args = HELPER.parse_args(
                ["--initialpose-opt-in", "--initialpose-canonical-free-cell-opt-in"]
            )
            request = HELPER.canonicalize_initialpose_request(args, audit)

        self.assertTrue(audit["ok"])
        self.assertEqual({"row": 1, "column": 1, "pixel_value": 254}, audit["free_cell"])
        self.assertAlmostEqual(-0.25, audit["world_pose"]["x"])
        self.assertAlmostEqual(-1.25, audit["world_pose"]["y"])
        self.assertEqual(64, len(audit["map_yaml_sha256"]))
        self.assertEqual("canonical_map_free_cell_world_pose", request["source"])

    def test_canonical_map_without_free_cell_fails_closed(self) -> None:
        """non-free 地图不得生成 fallback initialpose。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "map.pgm").write_bytes(b"P5\n2 2\n255\n" + bytes([0, 0, 0, 0]))
            yaml_path = root / "map.yaml"
            yaml_path.write_text(
                "image: map.pgm\nresolution: 0.1\norigin: [0.0, 0.0, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\nmode: trinary\n",
                encoding="utf-8",
            )
            audit = HELPER.canonical_initialpose_map_audit(str(yaml_path))

        self.assertFalse(audit["ok"])
        self.assertFalse(audit["free_cell_verified"])

    def test_persisted_config_true_does_not_equal_live_consumption(self) -> None:
        """仓库 `set_initial_pose: true` 只算静态事实；上一轮 helper effective false 必须保留。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = root / "nav2.yaml"
            config.write_text("amcl:\n  ros__parameters:\n    set_initial_pose: true\n", encoding="utf-8")
            params = root / "managed.yaml"
            params.write_text("amcl:\n  ros__parameters:\n    set_initial_pose: false\n", encoding="utf-8")
            with mock.patch.object(HELPER, "NAV2_PLANNER_CONFIG_PATH", config):
                audit = HELPER.build_persisted_pose_audit(
                    managed_params_path=str(params),
                    tf_source_diagnostics={
                        "amcl_node_info_observed": True,
                        "amcl_runtime_params": {"set_initial_pose": False},
                    },
                    pre_localization_signals={"/amcl_pose": {}},
                    pre_tf_source_freshness={"edges": {}},
                    amcl_startup_log="Please set the initial pose",
                )

        self.assertTrue(audit["repo_config"]["set_initial_pose_true_present"])
        self.assertFalse(audit["config_presence_is_live_consumption"])
        self.assertTrue(audit["helper_generated_params"]["effective_set_initial_pose_false"])
        self.assertFalse(audit["persisted_pose_live_consumed"])

    def test_persisted_live_pose_and_unique_amcl_tf_skip_publish(self) -> None:
        """同窗 fresh pose + unique AMCL dynamic map->odom 已成立时必须零次发布。"""
        fresh_entry = {
            "probe": {"observed": True},
            "timestamp": {"parsed": True},
            "freshness": {"status": "fresh"},
        }
        map_edge = {
            "source_class": "dynamic",
            "publisher_attribution_status": "attributed_unique_amcl",
            "timestamp": {"parsed": True},
            "freshness": {"status": "fresh"},
        }
        audit = HELPER.build_persisted_pose_audit(
            managed_params_path=None,
            tf_source_diagnostics={"amcl_node_info_observed": True, "amcl_runtime_params": {}},
            pre_localization_signals={"/amcl_pose": fresh_entry},
            pre_tf_source_freshness={"edges": {"map_to_odom": map_edge}},
            amcl_startup_log="",
        )
        args = HELPER.parse_args(["--initialpose-opt-in"])
        with mock.patch.object(HELPER, "publish_initialpose_inprocess_burst") as publish_mock:
            _, result = HELPER.maybe_publish_initialpose(
                args,
                True,
                pre_initialpose_gate={
                    "clean": True,
                    "persisted_pose_live_consumed": audit["persisted_pose_live_consumed"],
                    "initialpose_subscriber_count": 1,
                },
            )

        self.assertTrue(audit["persisted_pose_live_consumed"])
        self.assertEqual(0, result["publish_attempts"])
        self.assertTrue(result["satisfied_without_publish"])
        publish_mock.assert_not_called()

    def test_initialpose_total_attempt_never_falls_back_after_rclpy_write(self) -> None:
        """rclpy 一旦 publish 过一次，即使 match 未证实也不得再走 CLI。"""
        args = HELPER.parse_args(["--initialpose-opt-in"])
        with mock.patch.object(
            HELPER,
            "publish_initialpose_inprocess_burst",
            return_value={"ok": False, "publish_attempts": 1, "boundary": "subscriber_missing"},
        ), mock.patch.object(HELPER, "run_ros") as run_mock:
            _, result = HELPER.maybe_publish_initialpose(
                args,
                True,
                pre_initialpose_gate={"clean": True, "persisted_pose_live_consumed": False},
            )

        self.assertEqual(1, result["publish_attempts"])
        self.assertTrue(result["cli_fallback_forbidden_after_attempt"])
        run_mock.assert_not_called()

    def test_initialpose_prewrite_gate_failure_keeps_attempt_zero(self) -> None:
        """subscriber/TF/free-cell 任一门禁失败时必须保持 publish attempt=0。"""
        args = HELPER.parse_args(["--initialpose-opt-in"])
        with mock.patch.object(HELPER, "publish_initialpose_inprocess_burst") as publish_mock:
            _, result = HELPER.maybe_publish_initialpose(
                args,
                True,
                pre_initialpose_gate={"clean": False, "blocking_reasons": ["tf_authority_clear"]},
            )

        self.assertEqual(0, result["publish_attempts"])
        self.assertEqual("pre_initialpose_gate_not_clean_no_publish", result["boundary"])
        publish_mock.assert_not_called()

    def _persisted_pose_path_gate(
        self,
        *,
        pose_status: str = "fresh",
        pose_parsed: bool = True,
        pose_observed: bool = True,
        map_status: str = "fresh",
        map_parsed: bool = True,
        map_source: str = "dynamic",
        attribution: str = "attributed_unique_amcl",
        persisted_live: bool = True,
        publish_attempts: int = 0,
        map_server_active: bool = True,
        amcl_active: bool = True,
        planner_server_active: bool = True,
        controller_server_active: bool = True,
    ) -> dict[str, object]:
        """构造 no-publish current persisted pose gate，供缺失、过期和归属冲突矩阵复用。"""
        # 测试 fixture 把四个 lifecycle 与发布计数独立暴露，避免只验证 happy path；
        # 任一 active/read-only 安全条件变化都应在 action 前得到稳定 blocker。
        return HELPER.build_path_generation_precondition_gate(
            initialpose_request={"enabled": False},
            initialpose_publish={"ok": False, "publish_attempts": publish_attempts},
            controlled_initialpose_gate={"clean": True},
            persisted_pose_audit={"persisted_pose_live_consumed": persisted_live},
            localization_signal_freshness={
                "/amcl_pose": {
                    "probe": {"observed": pose_observed},
                    "timestamp": {"parsed": pose_parsed},
                    "freshness": {"status": pose_status},
                }
            },
            tf_source_freshness={
                "edges": {
                    "map_to_odom": {
                        "source_class": map_source,
                        "publisher_attribution_status": attribution,
                        "timestamp": {"parsed": map_parsed},
                        "freshness": {"status": map_status},
                    }
                }
            },
            localization_tf_observed={"map_to_odom": True, "map_to_base_link": True},
            lifecycle_active={"map_server": map_server_active, "amcl": amcl_active},
            planner_server_active=planner_server_active,
            controller_server_active=controller_server_active,
            localization_ready=True,
            localization_root_causes=[],
        )

    def test_fresh_persisted_pose_opens_planner_only_gate_without_publish(self) -> None:
        """fresh pose、唯一 AMCL dynamic TF 与四 lifecycle active 才能走零发布 path。"""
        gate = self._persisted_pose_path_gate()
        args = HELPER.parse_args(["--strict-no-motion", "--path-generation-opt-in"])
        _, publish = HELPER.maybe_publish_initialpose(args, True)

        self.assertTrue(gate["clean"])
        self.assertTrue(gate["persisted_pose_ready"])
        self.assertEqual("current_fresh_persisted_pose_no_publish", gate["source_mode"])
        self.assertEqual(0, gate["initialpose_publish_attempts"])
        self.assertEqual(0, publish["publish_attempts"])
        self.assertFalse(args.initialpose_opt_in)
        self.assertFalse(args.managed_runtime_opt_in)
        self.assertTrue(args.path_generation_opt_in)

    def test_persisted_pose_gate_requires_zero_publish_and_all_four_lifecycle_active(self) -> None:
        """零发布与四 lifecycle 必须逐项成立，不能由 fresh pose/TF 反向补齐。"""
        blocked_cases = {
            # 当前 sprint 禁止 initialpose；历史写计数非零必须直接关闭 persisted 分支。
            "initialpose_publish_attempts_zero": {"publish_attempts": 1},
            # map/amcl/planner/controller 分别承担地图、定位、规划和下轮控制 readiness。
            "map_server_lifecycle_active": {"map_server_active": False},
            "amcl_lifecycle_active": {"amcl_active": False},
            "planner_server_lifecycle_active": {"planner_server_active": False},
            "controller_server_lifecycle_active": {"controller_server_active": False},
        }

        for expected_reason, overrides in blocked_cases.items():
            with self.subTest(expected_reason=expected_reason):
                # 每次只破坏一个条件，确认 blocker 精确且 gate 不会被其它 clean 条件掩盖。
                gate = self._persisted_pose_path_gate(**overrides)

                self.assertFalse(gate["clean"])
                self.assertIn(expected_reason, gate["blocking_reasons"])
                # source_mode 只描述定位来源；总 gate 的 clean 才决定 planner action 是否可调用。
                if expected_reason == "initialpose_publish_attempts_zero":
                    self.assertFalse(gate["persisted_pose_ready"])
                else:
                    self.assertTrue(gate["persisted_pose_ready"])

    def test_missing_persisted_pose_blocks_before_compute_path_attempt(self) -> None:
        """pose/source missing 时必须在 action 前 no-go，不能让 planner fallback 形成尝试。"""
        gate = self._persisted_pose_path_gate(
            pose_status="not_observed",
            pose_parsed=False,
            pose_observed=False,
            map_status="not_observed",
            map_parsed=False,
            map_source="missing",
            attribution="not_attributed",
            persisted_live=False,
        )
        args = HELPER.parse_args(["--path-generation-opt-in"])
        _, result, _, causes = HELPER.maybe_compute_path_generation(
            args,
            ros2_ok=True,
            localization_ready=bool(gate["clean"]),
            planner_server_active=True,
        )

        self.assertFalse(gate["clean"])
        self.assertIn("persisted_pose_live_consumed", gate["blocking_reasons"])
        self.assertIn("amcl_pose_sample_observed", gate["blocking_reasons"])
        self.assertIn("map_to_odom_dynamic", gate["blocking_reasons"])
        self.assertFalse(result["attempted"])
        self.assertEqual("path_generation_blocked_by_localization_not_ready", result["boundary"])
        self.assertEqual("localization_not_ready_for_path_generation", causes[0]["reason"])

    def test_stale_persisted_pose_or_tf_blocks_planner_action(self) -> None:
        """样本虽存在但 pose 或 map->odom stale 时仍必须 path_attempted=false。"""
        gate = self._persisted_pose_path_gate(pose_status="stale", map_status="stale")
        args = HELPER.parse_args(["--path-generation-opt-in"])
        _, result, _, _ = HELPER.maybe_compute_path_generation(
            args,
            ros2_ok=True,
            localization_ready=bool(gate["clean"]),
            planner_server_active=True,
        )

        self.assertFalse(gate["clean"])
        self.assertFalse(gate["persisted_pose_ready"])
        self.assertIn("amcl_pose_fresh", gate["blocking_reasons"])
        self.assertIn("map_to_odom_fresh", gate["blocking_reasons"])
        self.assertFalse(result["attempted"])

    def test_ambiguous_map_to_odom_attribution_blocks_planner_action(self) -> None:
        """多个 AMCL publisher 或无法唯一归属时不能消费 dynamic TF 作为 persisted pose。"""
        gate = self._persisted_pose_path_gate(attribution="ambiguous_multiple_amcl_publishers")
        args = HELPER.parse_args(["--path-generation-opt-in"])
        _, result, _, _ = HELPER.maybe_compute_path_generation(
            args,
            ros2_ok=True,
            localization_ready=bool(gate["clean"]),
            planner_server_active=True,
        )

        self.assertFalse(gate["clean"])
        self.assertFalse(gate["persisted_pose_ready"])
        self.assertIn("map_to_odom_attributed_unique_amcl", gate["blocking_reasons"])
        self.assertFalse(result["attempted"])

    def test_persisted_pose_gate_and_compute_path_remain_planner_only(self) -> None:
        """新增 gate 与 ComputePath helper 不得包含导航、速度、manual 或底盘 UART token。"""
        source = "\n".join(
            (
                inspect.getsource(HELPER.build_path_generation_precondition_gate),
                inspect.getsource(HELPER.maybe_compute_path_generation),
            )
        )

        for forbidden in ("NavigateToPose", "FollowPath", "/cmd_vel", "/api/base/manual", "/dev/ttyS5"):
            self.assertNotIn(forbidden, source)
        self.assertIn("ComputePathToPose", source)

    def test_build_proof_wires_persisted_gate_before_compute_path(self) -> None:
        """gate 必须接入真实 build_proof 调用链，不能只停留在孤立 helper 单测。"""
        source = inspect.getsource(HELPER.build_proof)

        # build_proof 先聚合 final freshness/lifecycle/source，再把唯一 clean 布尔传给 action helper。
        gate_build = source.index("path_generation_precondition_gate = build_path_generation_precondition_gate(")
        gate_result = source.index("path_generation_preconditions_ready = bool(path_generation_precondition_gate[\"clean\"])")
        compute_call = source.index("maybe_compute_path_generation(")
        self.assertLess(gate_build, gate_result)
        self.assertLess(gate_result, compute_call)
        self.assertIn("localization_ready=path_generation_preconditions_ready", source)
        self.assertIn("planner_server_active=planner_server_active", source)
        self.assertIn('"path_generation_precondition_gate": path_generation_precondition_gate', source)

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
        """board source 与写前只读门禁必须先完成，才能决定是否允许 `/initialpose`。"""
        text = SCRIPT.read_text(encoding="utf-8")
        preflight_index = text.index('phase_writer.record_phase("board_source_preflight")')
        gate_index = text.index('phase_writer.record_phase("pre_initialpose_read_only_audit")')
        initialpose_index = text.index('phase_writer.record_phase("initialpose")')

        self.assertLess(preflight_index, gate_index)
        self.assertLess(gate_index, initialpose_index)
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
            text.index('phase_writer.record_phase(\n            "topic_probe"'),
        )
        self.assertIn('ROS2_PREFLIGHT_COMMAND = "command -v ros2"', text)
        self.assertIn("pre_initialpose_gate_not_clean_no_publish", text)
        self.assertIn("pre_initialpose_amcl_pose_probe_not_ready", text)

    def test_board_source_preflight_separates_ros2_cli_and_rclpy_runtime(self) -> None:
        """artifact 必须把 sourced shell 的 `ros2` CLI 与 Python `rclpy` runtime 拆开记录。"""
        text = SCRIPT.read_text(encoding="utf-8")

        for required in (
            "def board_source_preflight(",
            "board_source_preflight_source_timeout",
            "board_source_preflight_ros2_cli_path_missing",
            "board_source_preflight_ros2_cli_which_timeout",
            "board_source_preflight_lightweight_cli_timeout",
            "board_source_preflight_lightweight_cli_failed",
            "board_source_preflight_rclpy_import_timeout",
            "board_source_preflight_rclpy_import_failed_",
            "SOURCE_AMORTIZED_CLI_PREFLIGHT_SCHEMA",
            "source_amortized_cli_preflight",
            '"source_and_cli_in_one_shell"',
            '"per_command_source_overhead_eliminated"',
            '"source_stage"',
            '"path_lookup"',
            '"lightweight_readiness"',
            '"lightweight_cli_ready"',
            '"ros2_node_list"',
            '"cli_invocation"',
            '"python_rclpy"',
            '"ros2_cli_ok"',
            '"ros2_cli_path_ok"',
            '"ros2_cli_invocation_ok"',
            '"rclpy_import_ok"',
            '"python_executable"',
            '"rclpy_file"',
            '"sys_path_head"',
        ):
            self.assertIn(required, text)

    def test_board_source_preflight_direct_function_classifies_missing_ros2(self) -> None:
        """缺 `ros2` 时，preflight 必须显式落到 PATH missing，而不是笼统 source blocker。"""
        args = HELPER.parse_args([])
        path_lookup = {
            "command_v": {"executed": True, "ok": False, "stdout": "", "stderr": "", "timed_out": False},
            "type_a": {"executed": True, "ok": False, "stdout": "", "stderr": "", "timed_out": False},
            "which": {"executed": True, "ok": False, "stdout": "", "stderr": "", "timed_out": False},
        }
        preflight_payload = self._amortized_preflight_payload(
            source={
                "ok": True,
                "ros_setup": {"exists": True, "sourced": True, "returncode": 0, "elapsed_ms": 20},
                "workspace_setup": {"exists": False, "sourced": False, "skipped": True, "returncode": 0},
                "cd_ok": True,
            },
            path_lookup=path_lookup,
            ros2_cli_path=None,
            cli_invocation={
                "executed": False,
                "ok": False,
                "boundary": "ros2_path_missing_skip_cli_invocation",
                "timed_out": False,
            },
            rclpy_payload={
                "python_executable": "/usr/bin/python3",
                "python_version": "3.10.0",
                "sys_path_head": ["/tmp"],
                "rclpy_import_ok": True,
                "rclpy_file": "/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py",
                "error": None,
            },
        )
        with mock.patch.object(
            HELPER,
            "run_bash",
            return_value={
                "executed": True,
                "ok": True,
                "stdout": json.dumps(preflight_payload, ensure_ascii=False),
                "stderr": "",
                "timed_out": False,
            },
        ), mock.patch.object(HELPER, "run_ros") as run_ros_mock:
            result = HELPER.board_source_preflight(args)

        run_ros_mock.assert_not_called()
        self.assertFalse(result["ros2_cli_ok"])
        self.assertFalse(result["ros2_cli_path_ok"])
        self.assertFalse(result["ros2_cli_invocation_ok"])
        self.assertTrue(result["rclpy_import_ok"])
        self.assertFalse(result["ready"])
        self.assertEqual("board_source_preflight_ros2_cli_path_missing", result["classification"])
        self.assertIn("source_stage", result)
        self.assertIn("path_lookup", result)
        self.assertIn("cli_invocation", result)
        self.assertIn("python_rclpy", result)

    def test_board_source_preflight_keeps_heavy_help_as_diagnostic_only(self) -> None:
        """`ros2 --help` 超时后，只要 lightweight readiness 成功，就不能继续拦住 CLI ready。"""
        args = HELPER.parse_args([])
        preflight_payload = self._amortized_preflight_payload(
            source={
                "ok": True,
                "ros_setup": {"exists": True, "sourced": True, "returncode": 0, "elapsed_ms": 30},
                "workspace_setup": {"exists": True, "sourced": True, "skipped": False, "returncode": 0},
                "cd_ok": True,
            },
            path_lookup={
                "command_v": {"executed": True, "ok": True, "stdout": "/opt/ros/humble/bin/ros2\n", "stderr": "", "timed_out": False},
                "type_a": {"executed": True, "ok": True, "stdout": "ros2 is /opt/ros/humble/bin/ros2\n", "stderr": "", "timed_out": False},
                "which": {"executed": True, "ok": True, "stdout": "/opt/ros/humble/bin/ros2\n", "stderr": "", "timed_out": False},
            },
            ros2_cli_path="/opt/ros/humble/bin/ros2",
            cli_invocation={
                "executed": True,
                "ok": False,
                "timed_out": True,
                "returncode": None,
                "stderr": "",
            },
            rclpy_payload=self._rclpy_payload(ok=True),
        )
        with mock.patch.object(
            HELPER,
            "run_bash",
            return_value={
                "executed": True,
                "ok": True,
                "stdout": json.dumps(preflight_payload, ensure_ascii=False),
                "stderr": "",
                "timed_out": False,
            },
        ), mock.patch.object(HELPER, "run_ros") as run_ros_mock:
            result = HELPER.board_source_preflight(args)

        run_ros_mock.assert_not_called()
        self.assertTrue(result["ros2_cli_ok"])
        self.assertTrue(result["lightweight_cli_ready"])
        self.assertTrue(result["ros2_cli_path_ok"])
        self.assertFalse(result["ros2_cli_invocation_ok"])
        self.assertTrue(result["cli_ready"])
        self.assertTrue(result["runtime_ready"])
        self.assertTrue(result["ready"])
        self.assertEqual("board_source_preflight_ready", result["classification"])
        self.assertEqual(6.0, result["cli_invocation_timeout_s"])

    def test_board_source_preflight_classifies_lightweight_timeout_before_runtime(self) -> None:
        """heavy help 只是诊断项；真正的 fail-closed 必须收口到 lightweight CLI blocker。"""
        args = HELPER.parse_args([])
        preflight_payload = self._amortized_preflight_payload(
            lightweight_results={
                "ros2_daemon_status": {
                    "label": "ros2_daemon_status",
                    "command": "ros2 daemon status",
                    "executed": True,
                    "ok": False,
                    "timed_out": True,
                    "returncode": None,
                },
                "ros2_node_list": {
                    "label": "ros2_node_list",
                    "command": "ros2 node list",
                    "executed": True,
                    "ok": False,
                    "timed_out": True,
                    "returncode": None,
                },
            },
            cli_invocation={"executed": True, "ok": True, "timed_out": False, "returncode": 0},
            rclpy_payload=self._rclpy_payload(ok=True),
        )
        with mock.patch.object(
            HELPER,
            "run_bash",
            return_value={
                "executed": True,
                "ok": True,
                "stdout": json.dumps(preflight_payload, ensure_ascii=False),
                "stderr": "",
                "timed_out": False,
            },
        ):
            result = HELPER.board_source_preflight(args)

        self.assertFalse(result["lightweight_cli_ready"])
        self.assertFalse(result["ros2_cli_ok"])
        self.assertFalse(result["cli_ready"])
        self.assertFalse(result["runtime_ready"])
        self.assertEqual("board_source_preflight_lightweight_cli_timeout", result["classification"])

    def test_board_source_preflight_classifies_path_lookup_timeout_before_invocation(self) -> None:
        """source 成功但 PATH/which 层超时时，要保留 CLI path/which timeout，而不是报 env mismatch。"""
        args = HELPER.parse_args([])
        preflight_payload = self._amortized_preflight_payload(
            path_lookup={
                "command_v": {"executed": True, "ok": True, "stdout": "/opt/ros/humble/bin/ros2\n", "stderr": "", "timed_out": False},
                "type_a": {"executed": True, "ok": False, "stdout": "", "stderr": "", "timed_out": True},
                "which": {"executed": True, "ok": False, "stdout": "", "stderr": "", "timed_out": True},
            },
            ros2_cli_path="/opt/ros/humble/bin/ros2",
            cli_invocation={"executed": True, "ok": True, "timed_out": False, "returncode": 0},
            rclpy_payload=self._rclpy_payload(ok=True),
        )
        with mock.patch.object(
            HELPER,
            "run_bash",
            return_value={
                "executed": True,
                "ok": True,
                "stdout": json.dumps(preflight_payload, ensure_ascii=False),
                "stderr": "",
                "timed_out": False,
            },
        ):
            result = HELPER.board_source_preflight(args)

        self.assertTrue(result["source_stage_ok"])
        self.assertTrue(result["ros2_cli_path_ok"])
        self.assertEqual("board_source_preflight_ros2_cli_which_timeout", result["classification"])
        self.assertTrue(result["source_and_cli_in_one_shell"])

    def test_board_cli_layer_uses_six_second_invocation_budget(self) -> None:
        """真板 `ros2 --help` 冷启动约 4.5s，preflight 必须保留 6s 预算。"""
        command = HELPER.board_cli_layer_probe_command()

        self.assertEqual(6.0, HELPER.ROS2_LAYER_INVOCATION_TIMEOUT_S)
        self.assertIn("INVOCATION_TIMEOUT_S = 6.0", command)
        self.assertIn('run_layer("ros2_help", "ros2 --help >/dev/null", INVOCATION_TIMEOUT_S)', command)

    def test_board_source_preflight_classifies_source_timeout_before_path(self) -> None:
        """source 阶段超时时，PATH/which 与 rclpy 必须显式 skipped，不能伪造下游结论。"""
        args = HELPER.parse_args([])
        with mock.patch.object(
            HELPER,
            "run_bash",
            return_value={
                "executed": True,
                "ok": False,
                "stdout": "",
                "stderr": "",
                "timed_out": True,
            },
        ), mock.patch.object(HELPER, "run_ros") as run_ros_mock:
            result = HELPER.board_source_preflight(args)

        run_ros_mock.assert_not_called()
        self.assertFalse(result["source_stage_ok"])
        self.assertFalse(result["ros2_cli_ok"])
        self.assertFalse(result["rclpy_import_ok"])
        self.assertEqual("board_source_preflight_source_timeout", result["classification"])

    def test_classify_root_causes_stops_at_board_source_preflight_failure(self) -> None:
        """preflight 失败时，不应再把 `/scan` 或 TF 下游噪音写成主 blocker。"""
        causes = HELPER.classify_root_causes(
            map_inputs={"root_causes": []},
            ros2_ok=True,
            board_source_preflight={
                "ros2_cli_ok": True,
                "rclpy_import_ok": False,
                "classification": "board_source_preflight_rclpy_import_failed_environment_not_sourced",
            },
            map_lifecycle_preflight={
                "root_causes": [{"layer": "Nav2 lifecycle", "reason": "map_server_lifecycle_not_active_during_preflight"}],
            },
            packages={package: True for package in HELPER.EXPECTED_PACKAGES},
            lifecycle_active={"map_server": False, "amcl": False},
            scan_once_observed=False,
            map_once_observed=False,
            amcl_pose_observed=False,
            localization_tf_observed={"map_to_odom": False, "map_to_base_link": False},
            tf_chain_observed={"map_to_odom": False, "odom_to_base_link": False, "base_link_to_laser_frame": False, "map_to_base_link": False},
            tf_failure_classification={},
            initialpose_enabled=True,
            initialpose_publish={"ok": False},
        )

        self.assertEqual(
            [
                {
                    "layer": "ROS Python runtime",
                    "reason": "board_source_preflight_rclpy_import_failed_environment_not_sourced",
                },
                {
                    "layer": "Nav2 lifecycle",
                    "reason": "map_server_lifecycle_not_active_during_preflight",
                },
            ],
            causes,
        )

    def test_managed_runtime_localization_fast_path_skips_slow_echo_after_lifecycle_ready(self) -> None:
        """managed runtime 已观测到 lifecycle 后，helper 必须优先返回定位根因而不是卡死在 /scan echo。"""
        text = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("managed_runtime_localization_fast_path", text)
        self.assertIn("managed_runtime_localization_root_cause_fast_path", text)
        self.assertIn("managed_runtime_cli_localization_fast_path", text)
        self.assertIn("managed_runtime_cli_lifecycle_confirmed_root_cause_fast_path", text)
        self.assertIn("lifecycle CLI already proved map_server/amcl active", text)
        self.assertIn("skip repeated /scan echo to return current localization blocker before HTTP timeout", text)
        self.assertIn("skip repeated /map echo to return current AMCL/TF blocker before HTTP timeout", text)
        self.assertIn("scan_probe_skipped_after_managed_runtime_lifecycle_ready", text)
        self.assertIn("map_probe_skipped_after_managed_runtime_lifecycle_ready", text)

    def test_wait_for_managed_runtime_rechecks_lifecycle_until_active(self) -> None:
        """节点已入 graph 但 lifecycle 仍在启动时，helper 必须继续等 active，而不是固化为 inactive。"""
        args = HELPER.parse_args(["--managed-timeout-s", "4"])
        runtime = {
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "started_at_ms": 1000,
            "log_path": "/tmp/o10-managed.log",
        }
        clock = {"value": 0.0}

        def fake_time() -> float:
            clock["value"] += 0.2
            return clock["value"]

        def fake_sleep(seconds: float) -> None:
            clock["value"] += seconds

        inactive_results = {
            "map_server": {"executed": True, "ok": True, "stdout": "inactive [2]\n", "boundary": "lifecycle_probe_inactive"},
            "amcl": {"executed": True, "ok": True, "stdout": "inactive [2]\n", "boundary": "lifecycle_probe_inactive"},
        }
        active_results = {
            "map_server": {"executed": True, "ok": True, "stdout": "active [3]\n", "boundary": "lifecycle_probe_active"},
            "amcl": {"executed": True, "ok": True, "stdout": "active [3]\n", "boundary": "lifecycle_probe_active"},
        }

        with mock.patch.object(HELPER.time, "time", side_effect=fake_time), mock.patch.object(
            HELPER.time,
            "sleep",
            side_effect=fake_sleep,
        ), mock.patch.object(
            HELPER,
            "rclpy_node_names",
            side_effect=[
                {"ok": True, "node_names": ["map_server", "amcl"], "boundary": "rclpy_node_names_observed"},
                {"ok": True, "node_names": ["map_server", "amcl"], "boundary": "rclpy_node_names_observed"},
            ],
        ), mock.patch.object(
            HELPER,
            "lifecycle_checks",
            side_effect=[
                ({"map_server": False, "amcl": False}, inactive_results),
                ({"map_server": True, "amcl": True}, active_results),
            ],
        ), mock.patch.object(HELPER, "preview_file", return_value=""):
            result = HELPER.wait_for_managed_runtime(args, runtime)

        self.assertTrue(result["ok"])
        self.assertEqual("managed_runtime_lifecycle_active_observed", result["boundary"])
        self.assertTrue(result["lifecycle_active"]["map_server"])
        self.assertTrue(result["lifecycle_active"]["amcl"])
        self.assertEqual("active [3]\n", result["lifecycle_results"]["amcl"]["stdout"])
        self.assertEqual(2, len(result["lifecycle_history"]))

    def test_rclpy_node_names_uses_sourced_child_python(self) -> None:
        """managed wait 的 node graph probe 必须走 sourced child Python，不能依赖主进程 rclpy。"""
        args = HELPER.parse_args([])
        with mock.patch.object(
            HELPER,
            "run_ros",
            return_value={
                "executed": True,
                "ok": True,
                "elapsed_ms": 420,
                "stdout": json.dumps(
                    {
                        "executed": True,
                        "ok": True,
                        "node_names": ["map_server", "amcl"],
                        "boundary": "rclpy_node_names_observed",
                        "elapsed_ms": 120,
                    },
                    ensure_ascii=False,
                ),
                "stderr": "",
                "timed_out": False,
            },
        ) as run_ros_mock:
            result = HELPER.rclpy_node_names(args, timeout_s=0.8)

        self.assertTrue(result["ok"])
        self.assertEqual(["map_server", "amcl"], result["node_names"])
        self.assertFalse(result["fallback_used"])
        command = run_ros_mock.call_args.args[1]
        self.assertIn("python3 - <<'PY'", command)
        self.assertIn("if not rclpy.ok():", command)
        self.assertIn("rclpy.init(args=None)", command)
        self.assertIn('rclpy.create_node("o10_managed_runtime_graph_probe")', command)
        self.assertEqual(6.0, run_ros_mock.call_args.kwargs["timeout_s"])

    def test_rclpy_node_names_falls_back_to_ros2_node_list_after_child_timeout(self) -> None:
        """child Python timeout 时必须继续读 ROS CLI graph，不能直接把 wait 收口成假 timeout。"""
        args = HELPER.parse_args([])
        with mock.patch.object(
            HELPER,
            "run_ros",
            side_effect=[
                {
                    "executed": True,
                    "ok": False,
                    "elapsed_ms": 6000,
                    "stdout": "",
                    "stderr": "",
                    "timed_out": True,
                },
                {
                    "executed": True,
                    "ok": True,
                    "elapsed_ms": 320,
                    "stdout": "/map_server\n/amcl\n",
                    "stderr": "",
                    "timed_out": False,
                    "returncode": 0,
                },
            ],
        ) as run_ros_mock:
            result = HELPER.rclpy_node_names(args, timeout_s=0.8)

        self.assertTrue(result["ok"])
        self.assertTrue(result["fallback_used"])
        self.assertEqual(["/amcl", "/map_server"], result["node_names"])
        self.assertEqual(
            "rclpy_node_names_failed_with_ros2_node_list_fallback_observed",
            result["boundary"],
        )
        self.assertEqual("ros2_node_list_observed", result["fallback"]["boundary"])

        self.assertEqual("ros2 node list --no-daemon", run_ros_mock.call_args_list[1].args[1])

    def test_rclpy_node_names_accepts_bounded_fallback_timeout(self) -> None:
        """managed wait 内部要能缩短 `ros2 node list`，避免外层只留下 current_command。"""
        args = HELPER.parse_args([])
        with mock.patch.object(
            HELPER,
            "run_ros",
            side_effect=[
                {
                    "executed": True,
                    "ok": False,
                    "elapsed_ms": 1800,
                    "stdout": "",
                    "stderr": "",
                    "timed_out": True,
                },
                {
                    "executed": True,
                    "ok": False,
                    "elapsed_ms": 1500,
                    "stdout": "",
                    "stderr": "",
                    "timed_out": True,
                    "returncode": None,
                },
            ],
        ) as run_mock:
            result = HELPER.rclpy_node_names(
                args,
                timeout_s=0.8,
                child_command_timeout_s=1.8,
                fallback_timeout_s=1.5,
            )

        self.assertFalse(result["ok"])
        self.assertTrue(result["fallback_used"])
        self.assertEqual("rclpy_node_names_failed_with_ros2_node_list_timeout", result["boundary"])
        self.assertEqual("ros2_node_list_timeout", result["fallback"]["boundary"])
        self.assertEqual(1.8, result["child_command_timeout_s"])
        self.assertEqual(1.5, result["fallback_timeout_s"])
        self.assertEqual(1.8, run_mock.call_args_list[0].kwargs["timeout_s"])
        self.assertEqual(1.5, run_mock.call_args_list[1].kwargs["timeout_s"])

    def test_wait_for_managed_runtime_reports_nodes_observed_but_lifecycle_inactive(self) -> None:
        """如果节点已出现但直到窗口结束都没 active，artifact 必须比 wait timeout 更窄。"""
        args = HELPER.parse_args(["--managed-timeout-s", "2"])
        runtime = {
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "started_at_ms": 1000,
            "log_path": "/tmp/o10-managed.log",
        }
        clock = {"value": 0.0}

        def fake_time() -> float:
            clock["value"] += 0.25
            return clock["value"]

        def fake_sleep(seconds: float) -> None:
            clock["value"] += seconds

        inactive_results = {
            "map_server": {"executed": True, "ok": True, "stdout": "inactive [2]\n", "boundary": "lifecycle_probe_inactive"},
            "amcl": {"executed": True, "ok": True, "stdout": "inactive [2]\n", "boundary": "lifecycle_probe_inactive"},
        }

        with mock.patch.object(HELPER.time, "time", side_effect=fake_time), mock.patch.object(
            HELPER.time,
            "sleep",
            side_effect=fake_sleep,
        ), mock.patch.object(
            HELPER,
            "rclpy_node_names",
            side_effect=[
                {"ok": True, "node_names": ["map_server", "amcl"], "boundary": "rclpy_node_names_observed"},
                {"ok": True, "node_names": ["map_server", "amcl"], "boundary": "rclpy_node_names_observed"},
                {"ok": True, "node_names": ["map_server", "amcl"], "boundary": "rclpy_node_names_observed"},
            ],
        ), mock.patch.object(
            HELPER,
            "lifecycle_checks",
            side_effect=[
                ({"map_server": False, "amcl": False}, inactive_results),
                ({"map_server": False, "amcl": False}, inactive_results),
                ({"map_server": False, "amcl": False}, inactive_results),
            ],
        ), mock.patch.object(HELPER, "preview_file", return_value="managed log tail"):
            result = HELPER.wait_for_managed_runtime(args, runtime)

        self.assertFalse(result["ok"])
        self.assertEqual("managed_runtime_nodes_observed_but_lifecycle_inactive", result["boundary"])
        self.assertFalse(result["lifecycle_active"]["map_server"])
        self.assertFalse(result["lifecycle_active"]["amcl"])
        self.assertEqual("managed log tail", result["log_tail"])
        self.assertGreaterEqual(len(result["lifecycle_history"]), 1)

    def test_wait_for_managed_runtime_returns_final_ros2_node_list_timeout(self) -> None:
        """两层 graph probe 都 timeout 时，wait 必须自然返回 final `ros2_node_list_timeout`。"""
        args = HELPER.parse_args(["--managed-timeout-s", "3"])
        runtime = {
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "started_at_ms": 1000,
            "log_path": "/tmp/o10-managed.log",
        }
        clock = {"value": 0.0}
        probe_calls = []

        def fake_time() -> float:
            clock["value"] += 0.2
            return clock["value"]

        def fake_sleep(seconds: float) -> None:
            clock["value"] += seconds

        def fake_node_names(_args, timeout_s=0.8, *, child_command_timeout_s=None, fallback_timeout_s=None):
            probe_calls.append(
                {
                    "timeout_s": timeout_s,
                    "child_command_timeout_s": child_command_timeout_s,
                    "fallback_timeout_s": fallback_timeout_s,
                }
            )
            return {
                "ok": False,
                "node_names": [],
                "boundary": "rclpy_node_names_failed_with_ros2_node_list_timeout",
                "fallback_used": True,
                "fallback": {
                    "executed": True,
                    "ok": False,
                    "node_names": [],
                    "timed_out": True,
                    "boundary": "ros2_node_list_timeout",
                },
            }

        with mock.patch.object(HELPER.time, "time", side_effect=fake_time), mock.patch.object(
            HELPER.time,
            "sleep",
            side_effect=fake_sleep,
        ), mock.patch.object(
            HELPER,
            "rclpy_node_names",
            side_effect=fake_node_names,
        ), mock.patch.object(HELPER, "preview_file", return_value="managed log tail"):
            result = HELPER.wait_for_managed_runtime(args, runtime)

        self.assertFalse(result["ok"])
        self.assertEqual("ros2_node_list_timeout", result["reason"])
        self.assertEqual("ros2_node_list_timeout", result["graph_wait_summary"]["latest_ros2_node_list_boundary"])
        self.assertTrue(result["graph_wait_summary"]["fallback_used"])
        self.assertTrue(probe_calls)
        self.assertLessEqual(max(call["child_command_timeout_s"] for call in probe_calls), HELPER.MANAGED_RUNTIME_GRAPH_CHILD_COMMAND_TIMEOUT_S)
        self.assertLessEqual(max(call["fallback_timeout_s"] for call in probe_calls), HELPER.MANAGED_RUNTIME_GRAPH_FALLBACK_TIMEOUT_S)

    def test_wait_for_managed_runtime_closes_early_when_owned_lifecycle_log_is_active(self) -> None:
        """自有 runtime 日志已 clean 时应给 compact TF probe 留出 final/cleanup 预算。"""
        args = HELPER.parse_args(["--managed-timeout-s", "70"])
        runtime = {
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "started_at_ms": 1000,
            "log_path": "/tmp/o10-managed.log",
        }
        graph_timeout = {
            "ok": False,
            "node_names": [],
            "boundary": "rclpy_node_names_failed_with_ros2_node_list_timeout",
            "fallback_used": True,
            "fallback": {
                "executed": True,
                "ok": False,
                "node_names": [],
                "timed_out": True,
                "boundary": "ros2_node_list_timeout",
            },
        }
        lifecycle_log = "\n".join(
            [
                "[INFO] [lifecycle_manager]: Activating map_server",
                "[INFO] [map_server]: Activating",
                "[INFO] [map_server]: Creating bond (map_server) to lifecycle manager.",
                "[INFO] [lifecycle_manager]: Server map_server connected with bond.",
                "[INFO] [lifecycle_manager]: Activating amcl",
                "[INFO] [amcl]: Activating",
                "[INFO] [amcl]: Creating bond (amcl) to lifecycle manager.",
                "[INFO] [lifecycle_manager]: Server amcl connected with bond.",
                "[INFO] [lifecycle_manager]: Managed nodes are active",
            ]
        )

        with mock.patch.object(HELPER, "rclpy_node_names", return_value=graph_timeout) as graph_mock, mock.patch.object(
            HELPER,
            "preview_file",
            return_value=lifecycle_log,
        ):
            result = HELPER.wait_for_managed_runtime(args, runtime)

        self.assertFalse(result["ok"])
        self.assertEqual("ros2_node_list_timeout", result["reason"])
        self.assertEqual("managed_lifecycle_log_active_graph_probe_blocked", result["early_closeout"])
        self.assertTrue(result["lifecycle_active"]["map_server"])
        self.assertTrue(result["lifecycle_active"]["amcl"])
        self.assertEqual("active [3]\n", result["lifecycle_results"]["amcl"]["stdout"])
        graph_mock.assert_called_once()

    def test_managed_graph_wait_blocker_skips_downstream_slow_probes(self) -> None:
        """managed graph wait 已 final blocked 后，不能继续用 TF echo/topic echo 把 artifact 卡回 partial。"""
        text = SCRIPT.read_text(encoding="utf-8")

        for required in (
            "MANAGED_RUNTIME_GRAPH_BLOCKED_REASONS",
            "managed_runtime_wait_graph_blocked",
            "pre_initialpose_gate_not_clean_no_publish",
            "tf_probe_skipped_after_managed_runtime_graph_wait_blocked",
            "scan_probe_skipped_after_managed_runtime_graph_wait_blocked",
            "map_probe_skipped_after_managed_runtime_graph_wait_blocked",
            "odom_probe_skipped_after_managed_runtime_graph_wait_blocked",
            "managed_runtime_graph_wait_blocked_downstream_recheck_skipped",
        ):
            self.assertIn(required, text)

    def test_lifecycle_active_log_allows_downstream_after_graph_wait_blocked(self) -> None:
        """graph wait timeout 不能覆盖 lifecycle-active 日志；clean 后必须允许继续下游只读 probe。"""
        text = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("managed_runtime_wait_graph_blocked_without_lifecycle_log", text)
        self.assertIn("managed_runtime_wait_graph_blocked_but_lifecycle_log_clean", text)
        self.assertIn("downstream_readback_allowed_after_lifecycle_log", text)
        self.assertIn("managed_runtime_log_lifecycle_readback=managed_log_lifecycle_readback", text)
        self.assertIn("and not managed_runtime_wait_graph_blocked_without_lifecycle_log", text)

    def test_source_amortized_batch_parser_keeps_partial_stage_timeout(self) -> None:
        """batch 被外层 timeout 打断时，也要从已 flush JSONL 读出 rclpy 卡住阶段。"""
        stdout = "\n".join(
            [
                json.dumps(
                    {
                        "kind": "source_stage",
                        "source_stage": {"ok": True, "elapsed_ms": 5100},
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "kind": "rclpy_stage",
                        "stage": "import_rclpy",
                        "event": "started",
                        "at_ms": 1783790000000,
                    },
                    ensure_ascii=False,
                ),
            ]
        )

        batch = HELPER.parse_source_amortized_batch_result(
            {
                "command": "source_amortized_ros2_graph_probe_batch",
                "ok": False,
                "timed_out": True,
                "timeout_s": 34.0,
                "returncode": None,
                "elapsed_ms": 34000,
                "stdout": stdout,
                "stderr": "",
            }
        )

        self.assertEqual("source_amortized_batch_timeout", batch["boundary"])
        stream = batch["rclpy_graph_stage_stream"]
        self.assertEqual("rclpy_graph_stage_stream_timeout", stream["boundary"])
        self.assertEqual("import_rclpy", stream["last_started_stage"])
        self.assertIsNone(stream["last_completed_stage"])
        self.assertTrue(batch["per_command_source_overhead_excluded"])

    def test_source_amortized_batch_parser_final_payload_is_json_serializable(self) -> None:
        """final JSONL 自身不能再进入 events_observed，避免 partial writer 循环引用。"""
        final_payload = {
            "kind": "source_amortized_batch_final",
            "schema": "trashbot.o10.source_amortized_ros2_graph_probe.v1",
            "source_amortized": True,
            "source_stage": {"ok": True},
            "commands": {},
            "workspace_environment": {"summary": {}},
            "rclpy_graph_stage_stream": {"boundary": "rclpy_graph_empty_after_stage_wait"},
            "ok": True,
            "boundary": "source_amortized_batch_completed",
        }
        batch = HELPER.parse_source_amortized_batch_result(
            {
                "command": "source_amortized_ros2_graph_probe_batch",
                "ok": True,
                "timed_out": False,
                "timeout_s": 34.0,
                "returncode": 0,
                "elapsed_ms": 5100,
                "stdout": json.dumps(final_payload, ensure_ascii=False),
                "stderr": "",
            }
        )

        json.dumps(batch, ensure_ascii=False, sort_keys=True)
        self.assertEqual([], batch["events_observed"])

    def test_source_amortized_batch_prefers_daemon_dds_after_help_ok(self) -> None:
        """单次 source 后 help/import 已通过时，node/topic timeout 应归到 daemon/DDS graph。"""
        batch = self._source_amortized_batch_fixture(
            help_result={"ok": True, "timed_out": False, "returncode": 0, "stdout": "usage: ros2 node list\n"},
            rclpy_stream={
                "executed": True,
                "ok": False,
                "timed_out": False,
                "timeout_s": 1.2,
                "boundary": "rclpy_graph_empty_after_stage_wait",
                "segments": [
                    {"name": "import_rclpy", "elapsed_ms": 12},
                    {"name": "rclpy_init", "elapsed_ms": 8},
                    {"name": "create_node", "elapsed_ms": 20},
                    {"name": "graph_wait", "elapsed_ms": 1200},
                ],
                "node_names": [],
            },
        )
        probes = HELPER.source_amortized_batch_to_legacy_probes(batch)
        runtime = {
            "started": True,
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "process_group": 4321,
            "wait_result": {"ok": False, "reason": "ros2_node_list_timeout", "observed_node_names": [], "lifecycle_results": {}},
            "log_path": "/tmp/o10-missing.log",
        }

        result = HELPER.build_ros2_graph_timeout_root_cause(
            board_source_preflight={"cli_ready": True, "rclpy_import_ok": True},
            managed_runtime=runtime,
            managed_runtime_wait_graph_blocked=True,
            probes=probes,
            tf_source_root_cause_detail={"reason": "/tf_topic_missing"},
            require_planner_server=True,
        )

        self.assertEqual("source_amortized_batch", result["evidence_priority"])
        self.assertTrue(result["evidence_boundary"]["source_amortized_batch_used"])
        self.assertEqual("ros2_daemon_or_dds_graph_discovery_timeout", result["classification"])
        self.assertEqual("source_amortized_batch", result["probes"]["ros2_node_list"]["source"])
        self.assertIn(
            "ros2_cli_plugin_or_import_timeout",
            {item["classification"] for item in result["excluded_candidates"]},
        )

    def test_source_amortized_cli_plugin_requires_startup_stage_block(self) -> None:
        """source 后 help timeout 只有伴随 rclpy startup 卡住，才继续判 CLI/plugin/import。"""
        batch = self._source_amortized_batch_fixture(
            help_result={
                "ok": False,
                "timed_out": True,
                "returncode": None,
                "stdout": "",
                "error": {"type": "TimeoutExpired", "message": "help timed out"},
            },
            rclpy_stream={
                "executed": True,
                "ok": False,
                "timed_out": True,
                "timeout_s": 34.0,
                "boundary": "rclpy_graph_stage_stream_timeout",
                "segments": [],
                "events": [{"stage": "import_rclpy", "event": "started"}],
                "last_started_stage": "import_rclpy",
                "last_completed_stage": None,
                "node_names": [],
            },
        )
        probes = HELPER.source_amortized_batch_to_legacy_probes(batch)
        runtime = {
            "started": True,
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "process_group": 4321,
            "wait_result": {"ok": False, "reason": "ros2_node_list_timeout", "observed_node_names": [], "lifecycle_results": {}},
            "log_path": "/tmp/o10-missing.log",
        }

        result = HELPER.build_ros2_graph_timeout_root_cause(
            board_source_preflight={
                "classification": "board_source_preflight_ready",
                "cli_ready": True,
                "runtime_ready": True,
                "rclpy_import_ok": True,
            },
            managed_runtime=runtime,
            managed_runtime_wait_graph_blocked=True,
            probes=probes,
            tf_source_root_cause_detail={"reason": "/tf_topic_missing"},
            require_planner_server=True,
        )

        self.assertEqual("ros2_cli_plugin_or_import_timeout", result["classification"])
        self.assertIn("source_amortized_rclpy_stage_timeout_at_import_rclpy", result["primary_candidate"]["reason"])
        self.assertNotEqual("board_source_preflight_ready", result["primary_candidate"]["reason"])

    def _source_amortized_batch_fixture(
        self,
        *,
        help_result: dict[str, object],
        rclpy_stream: dict[str, object],
        daemon_safe_retry: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """构造最小 batch fixture；所有 command result 都代表 source 后的真实子命令预算。"""
        def command(command_text: str, *, timeout_s: float, timed_out: bool = True, ok: bool = False, **extra: object) -> dict[str, object]:
            payload: dict[str, object] = {
                "command": command_text,
                "executed": True,
                "ok": ok,
                "returncode": 0 if ok else None,
                "timeout_s": timeout_s,
                "timed_out": timed_out,
                "elapsed_ms": int(timeout_s * 1000),
                "stdout": "",
                "stderr": "",
            }
            payload.update(extra)
            return payload

        help_extra = dict(help_result)
        help_timed_out = bool(help_extra.pop("timed_out", False))
        help_ok = bool(help_extra.pop("ok", False))
        if daemon_safe_retry is None:
            daemon_safe_retry = {
                "schema": "trashbot.o10.daemon_safe_graph_retry.v1",
                "attempted": False,
                "skipped": True,
                "skip_reason": "fixture_not_attempted",
                "reset_completed": False,
                "graph_retry_observed": False,
                "commands": {},
            }
        return {
            "kind": "source_amortized_batch_final",
            "schema": "trashbot.o10.source_amortized_ros2_graph_probe.v1",
            "source_amortized": True,
            "per_command_source_overhead_excluded": True,
            "ok": True,
            "boundary": "source_amortized_batch_completed",
            "source_stage": {"ok": True, "elapsed_ms": 5100},
            "commands": {
                "ros2_node_list": command("ros2 node list", timeout_s=2.5),
                "ros2_node_list_no_daemon": command("ros2 node list --no-daemon", timeout_s=2.5),
                "ros2_daemon_status": command("ros2 daemon status", timeout_s=2.0),
                "ros2_node_list_help": command(
                    "ros2 node list --help",
                    timeout_s=5.0,
                    timed_out=help_timed_out,
                    ok=help_ok,
                    **help_extra,
                ),
                "ros2_topic_list": command("ros2 topic list", timeout_s=2.5),
            },
            "workspace_environment": {
                "observed": True,
                "summary": {
                    "ROS_DISTRO": "humble",
                    "which_ros2": "/opt/ros/humble/bin/ros2",
                    "AMENT_PREFIX_PATH": {"contains_ros": True, "contains_onboard_workspace": True},
                    "PYTHONPATH": {"contains_ros": True, "contains_onboard_workspace": True},
                    "LD_LIBRARY_PATH": {"contains_ros": True, "contains_onboard_workspace": False},
                },
            },
            "daemon_safe_retry": daemon_safe_retry,
            "rclpy_graph_stage_stream": rclpy_stream,
        }

    def test_daemon_dds_split_records_daemon_state_timeout_without_reset(self) -> None:
        """只重复 node list timeout 不够；split 必须把 daemon 状态候选单独落盘。"""
        batch = self._source_amortized_batch_fixture(
            help_result={"ok": True, "timed_out": False, "returncode": 0, "stdout": "usage: ros2 node list\n"},
            rclpy_stream={
                "executed": True,
                "ok": True,
                "timed_out": False,
                "timeout_s": 1.2,
                "boundary": "rclpy_graph_nodes_observed",
                "segments": [
                    {"name": "import_rclpy", "elapsed_ms": 10},
                    {"name": "rclpy_init", "elapsed_ms": 8},
                    {"name": "create_node", "elapsed_ms": 20},
                    {"name": "graph_wait", "elapsed_ms": 1200},
                ],
                "node_names": ["/map_server", "/amcl"],
            },
        )
        probes = HELPER.source_amortized_batch_to_legacy_probes(batch)
        runtime = {
            "started": True,
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "process_group": 4321,
            "wait_result": {"ok": False, "reason": "ros2_node_list_timeout", "observed_node_names": [], "lifecycle_results": {}},
            "log_path": "/tmp/o10-missing.log",
        }

        result = HELPER.build_ros2_graph_timeout_root_cause(
            board_source_preflight={"cli_ready": True, "runtime_ready": True, "rclpy_import_ok": True},
            managed_runtime=runtime,
            managed_runtime_wait_graph_blocked=True,
            probes=probes,
            tf_source_root_cause_detail={"reason": "/tf_topic_missing"},
            require_planner_server=True,
        )

        split = result["daemon_dds_split"]
        self.assertEqual("trashbot.o10.daemon_dds_graph_split.v1", split["schema"])
        self.assertEqual("ros2_daemon_state_timeout", split["primary_candidate"]["candidate"])
        self.assertIn("ros2 daemon stop", split["next_live_command"])
        readback = split["daemon_safe_graph_readback"]
        self.assertEqual("trashbot.o10.daemon_safe_graph_readback.v1", readback["schema"])
        self.assertFalse(readback["reset_attempted"])
        self.assertTrue(readback["reset_skipped"])
        self.assertEqual("daemon_reset_not_executed", readback["primary_conclusion"])
        self.assertEqual(
            "continue_daemon_or_cli_budget_split_before_lifecycle_gate",
            readback["next_step"],
        )
        self.assertFalse(split["evidence_boundary"]["path_generation_attempted"])
        self.assertFalse(split["evidence_boundary"]["safe_to_control"])
        self.assertEqual(
            set(HELPER.DAEMON_DDS_SPLIT_CANDIDATES),
            set(split["candidate_names"]),
        )
        self.assertIn(
            "workspace_source_or_env_mismatch",
            {item["candidate"] for item in split["excluded_candidates"]},
        )
        self.assertIn(
            "ros2_cli_no_daemon_unsupported",
            {item["candidate"] for item in split["remaining_candidates"]},
        )

    def test_daemon_dds_split_prefers_dds_after_daemon_reset_still_times_out(self) -> None:
        """daemon reset 成功后 graph 仍 timeout，应把下一步推到 DDS/domain/env 层。"""
        daemon_safe_retry = {
            "schema": "trashbot.o10.daemon_safe_graph_retry.v1",
            "attempted": True,
            "skipped": False,
            "skip_reason": None,
            "reset_completed": True,
            "graph_retry_observed": False,
            "commands": {
                "ros2_daemon_stop": {"ok": True, "timed_out": False, "boundary": "ros2_daemon_stop_ok"},
                "ros2_daemon_start": {"ok": True, "timed_out": False, "boundary": "ros2_daemon_start_ok"},
                "ros2_daemon_status_after_reset": {
                    "ok": True,
                    "timed_out": False,
                    "boundary": "ros2_daemon_status_after_reset_ok",
                },
                "ros2_node_list_after_daemon_reset": {
                    "ok": False,
                    "timed_out": True,
                    "boundary": "ros2_node_list_after_daemon_reset_timeout",
                },
                "ros2_topic_list_after_daemon_reset": {
                    "ok": False,
                    "timed_out": True,
                    "boundary": "ros2_topic_list_after_daemon_reset_timeout",
                },
            },
        }
        batch = self._source_amortized_batch_fixture(
            help_result={"ok": True, "timed_out": False, "returncode": 0, "stdout": "usage: ros2 node list\n"},
            daemon_safe_retry=daemon_safe_retry,
            rclpy_stream={
                "executed": True,
                "ok": True,
                "timed_out": False,
                "timeout_s": 1.2,
                "boundary": "rclpy_graph_nodes_observed",
                "segments": [
                    {"name": "import_rclpy", "elapsed_ms": 10},
                    {"name": "rclpy_init", "elapsed_ms": 8},
                    {"name": "create_node", "elapsed_ms": 20},
                    {"name": "graph_wait", "elapsed_ms": 1200},
                ],
                "node_names": ["/map_server", "/amcl"],
            },
        )
        probes = HELPER.source_amortized_batch_to_legacy_probes(batch)
        runtime = {
            "started": True,
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "process_group": 4321,
            "wait_result": {"ok": False, "reason": "ros2_node_list_timeout", "observed_node_names": [], "lifecycle_results": {}},
            "log_path": "/tmp/o10-missing.log",
        }

        result = HELPER.build_ros2_graph_timeout_root_cause(
            board_source_preflight={"cli_ready": True, "runtime_ready": True, "rclpy_import_ok": True},
            managed_runtime=runtime,
            managed_runtime_wait_graph_blocked=True,
            probes=probes,
            tf_source_root_cause_detail={"reason": "/tf_topic_missing"},
            require_planner_server=True,
        )

        split = result["daemon_dds_split"]
        self.assertEqual("dds_discovery_or_domain_mismatch", split["primary_candidate"]["candidate"])
        self.assertTrue(split["daemon_command_summaries"]["reset_completed"])
        readback = split["daemon_safe_graph_readback"]
        self.assertTrue(readback["reset_attempted"])
        self.assertTrue(readback["reset_completed"])
        self.assertEqual("timeout", readback["graph_readback"]["node_list_outcome"])
        self.assertEqual("timeout", readback["graph_readback"]["topic_list_outcome"])
        self.assertEqual("node_and_topic_graph_timeout_after_daemon_reset", readback["primary_conclusion"])
        self.assertEqual("narrow_to_dds_domain_or_graph_budget", readback["next_step"])
        self.assertEqual(
            "ros2_node_list_after_daemon_reset_timeout",
            split["daemon_command_summaries"]["retry_node_boundary"],
        )
        self.assertIn(
            "ros2_daemon_state_timeout",
            {item["candidate"] for item in split["excluded_candidates"]},
        )
        self.assertFalse(split["evidence_boundary"]["uses_base_uart"])

    def test_daemon_safe_graph_readback_marks_lifecycle_return_when_graph_recovers(self) -> None:
        """reset 后 node/topic 都恢复时，下一跳必须回到 lifecycle/localization gate。"""
        daemon_safe_retry = {
            "schema": "trashbot.o10.daemon_safe_graph_retry.v1",
            "attempted": True,
            "skipped": False,
            "skip_reason": None,
            "reset_completed": True,
            "graph_retry_observed": True,
            "commands": {
                "ros2_daemon_stop": {"ok": True, "timed_out": False, "boundary": "ros2_daemon_stop_ok"},
                "ros2_daemon_start": {"ok": True, "timed_out": False, "boundary": "ros2_daemon_start_ok"},
                "ros2_daemon_status_after_reset": {
                    "ok": True,
                    "timed_out": False,
                    "boundary": "ros2_daemon_status_after_reset_ok",
                },
                "ros2_node_list_after_daemon_reset": {
                    "ok": True,
                    "timed_out": False,
                    "boundary": "ros2_node_list_after_daemon_reset_observed",
                    "stdout_summary": "/map_server\n/amcl\n",
                },
                "ros2_topic_list_after_daemon_reset": {
                    "ok": True,
                    "timed_out": False,
                    "boundary": "ros2_topic_list_after_daemon_reset_ok",
                    "stdout_summary": "/tf\n/scan\n",
                },
            },
        }
        batch = self._source_amortized_batch_fixture(
            help_result={"ok": True, "timed_out": False, "returncode": 0, "stdout": "usage: ros2 node list\n"},
            daemon_safe_retry=daemon_safe_retry,
            rclpy_stream={
                "executed": True,
                "ok": True,
                "timed_out": False,
                "timeout_s": 1.2,
                "boundary": "rclpy_graph_nodes_observed",
                "segments": [{"name": "graph_wait", "elapsed_ms": 1200}],
                "node_names": ["/map_server", "/amcl"],
            },
        )
        probes = HELPER.source_amortized_batch_to_legacy_probes(batch)
        runtime = {
            "started": True,
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "process_group": 4321,
            "wait_result": {
                "ok": False,
                "reason": "ros2_node_list_timeout",
                "observed_node_names": ["/map_server", "/amcl"],
                "lifecycle_results": {},
            },
            "log_path": "/tmp/o10-missing.log",
        }

        result = HELPER.build_ros2_graph_timeout_root_cause(
            board_source_preflight={"cli_ready": True, "runtime_ready": True, "rclpy_import_ok": True},
            managed_runtime=runtime,
            managed_runtime_wait_graph_blocked=True,
            probes=probes,
            tf_source_root_cause_detail={"reason": "/tf_topic_missing"},
            require_planner_server=True,
        )

        readback = result["daemon_dds_split"]["daemon_safe_graph_readback"]
        self.assertEqual("observed", readback["graph_readback"]["node_list_outcome"])
        self.assertEqual("observed", readback["graph_readback"]["topic_list_outcome"])
        self.assertEqual("graph_readback_recovered_after_daemon_reset", readback["primary_conclusion"])
        self.assertEqual("return_to_lifecycle_localization_gate_without_motion", readback["next_step"])

    def test_graph_timeout_root_cause_contract_classifies_daemon_or_dds(self) -> None:
        """node graph timeout 时，新字段要把 CLI/env 排除，把 TF 标为 secondary。"""
        runtime = {
            "started": True,
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "process_group": 4321,
            "wait_result": {
                "ok": False,
                "reason": "ros2_node_list_timeout",
                "observed_node_names": [],
                "lifecycle_results": {
                    "map_server": {
                        "executed": False,
                        "ok": False,
                        "boundary": "managed_runtime_lifecycle_check_not_run",
                    },
                    "amcl": {
                        "executed": False,
                        "ok": False,
                        "boundary": "managed_runtime_lifecycle_check_not_run",
                    },
                },
            },
            "log_path": "/tmp/o10-missing.log",
        }
        probes = {
            "ros2_node_list": {"boundary": "ros2_node_list_timeout"},
            "ros2_node_list_no_daemon": {"boundary": "unsupported_option"},
            "ros2_node_list_help": {"boundary": "ros2_node_list_help_ok"},
            "ros2_topic_list": {"boundary": "ros2_topic_list_timeout"},
            "workspace_environment": {
                "summary": {
                    "ROS_DISTRO": "humble",
                    "which_ros2": "/opt/ros/humble/bin/ros2",
                    "AMENT_PREFIX_PATH": {"contains_ros": True, "contains_onboard_workspace": True},
                    "PYTHONPATH": {"contains_ros": True, "contains_onboard_workspace": True},
                    "LD_LIBRARY_PATH": {"contains_ros": True, "contains_onboard_workspace": False},
                }
            },
            "rclpy_graph_segments": {"payload": {"boundary": "rclpy_graph_empty_after_segment_wait"}},
        }

        result = HELPER.build_ros2_graph_timeout_root_cause(
            board_source_preflight={"cli_ready": True, "rclpy_import_ok": True},
            managed_runtime=runtime,
            managed_runtime_wait_graph_blocked=True,
            probes=probes,
            tf_source_root_cause_detail={"reason": "/tf_topic_missing"},
            require_planner_server=True,
        )

        self.assertEqual("ros2_daemon_or_dds_graph_discovery_timeout", result["classification"])
        self.assertEqual("ros2_node_list_timeout", result["primary_candidate"]["reason"])
        self.assertIn(
            "workspace_source_or_env_mismatch",
            {item["classification"] for item in result["excluded_candidates"]},
        )
        self.assertIn(
            "ros2_cli_plugin_or_import_timeout",
            {item["classification"] for item in result["excluded_candidates"]},
        )
        self.assertIn(
            "tf_runtime_secondary_after_graph_blocked",
            {item["classification"] for item in result["remaining_candidates"]},
        )
        self.assertEqual("skipped_after_ros2_graph_timeout", result["probes"]["managed_process"]["lifecycle_probe_status"])
        self.assertFalse(result["evidence_boundary"]["safe_to_control"])
        self.assertFalse(result["evidence_boundary"]["path_generated"])

    def test_graph_timeout_root_cause_keeps_env_timeout_as_remaining_candidate(self) -> None:
        """env 摘要超时但 board source ready 时，主因仍应落在 graph discovery timeout。"""
        runtime = {
            "started": True,
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "process_group": 4321,
            "wait_result": {
                "ok": False,
                "reason": "ros2_node_list_timeout",
                "observed_node_names": [],
                "lifecycle_results": {},
            },
            "log_path": "/tmp/o10-missing.log",
        }
        probes = {
            "ros2_node_list": {"boundary": "ros2_node_list_timeout"},
            "ros2_node_list_no_daemon": {"boundary": "ros2_node_list_no_daemon_timeout"},
            "ros2_daemon_status": {"boundary": "ros2_daemon_status_timeout"},
            "ros2_node_list_help": {"boundary": "ros2_node_list_help_ok"},
            "ros2_topic_list": {"boundary": "ros2_topic_list_timeout"},
            "workspace_environment": {"boundary": "workspace_environment_timeout", "summary": {}},
            "rclpy_graph_segments": {
                "payload": {
                    "boundary": "rclpy_graph_segment_probe_failed",
                    "segments": [
                        {"name": "import_rclpy", "elapsed_ms": 20},
                        {"name": "rclpy_init", "elapsed_ms": 10},
                    ],
                    "error": {"type": "RCLError", "message": "failed to create service"},
                }
            },
        }

        result = HELPER.build_ros2_graph_timeout_root_cause(
            board_source_preflight={"cli_ready": True, "rclpy_import_ok": True},
            managed_runtime=runtime,
            managed_runtime_wait_graph_blocked=True,
            probes=probes,
            tf_source_root_cause_detail={"reason": "/tf_topic_missing"},
            require_planner_server=True,
        )

        self.assertEqual("ros2_daemon_or_dds_graph_discovery_timeout", result["classification"])
        self.assertIn(
            "workspace_source_or_env_mismatch",
            {item["classification"] for item in result["remaining_candidates"]},
        )
        self.assertIn(
            "tf_runtime_secondary_after_graph_blocked",
            {item["classification"] for item in result["remaining_candidates"]},
        )

    def test_graph_timeout_root_cause_prefers_daemon_dds_when_board_source_ready(self) -> None:
        """当前 live 事实是 source/help/import ready，但 ROS graph 全部 timeout，应归到 daemon/DDS。"""
        runtime = {
            "started": True,
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "process_group": 4321,
            "wait_result": {
                "ok": False,
                "reason": "ros2_node_list_timeout",
                "observed_node_names": [],
                "lifecycle_results": {
                    "map_server": {"executed": False, "ok": False, "boundary": "managed_runtime_lifecycle_check_not_run"},
                    "amcl": {"executed": False, "ok": False, "boundary": "managed_runtime_lifecycle_check_not_run"},
                    "planner_server": {"executed": False, "ok": False, "boundary": "managed_runtime_lifecycle_check_not_run"},
                },
            },
            "log_path": "/tmp/o10-missing.log",
        }
        probes = {
            "ros2_node_list": {"boundary": "ros2_node_list_timeout"},
            "ros2_node_list_no_daemon": {"boundary": "ros2_node_list_no_daemon_timeout"},
            "ros2_daemon_status": {"boundary": "ros2_daemon_status_timeout"},
            "ros2_node_list_help": {"boundary": "ros2_node_list_help_ok"},
            "ros2_topic_list": {"boundary": "ros2_topic_list_timeout"},
            "workspace_environment": {"boundary": "workspace_environment_timeout", "summary": {}},
            "rclpy_graph_segments": {
                "payload": {
                    "boundary": "rclpy_graph_segment_probe_failed",
                    "segments": [
                        {"name": "import_rclpy", "elapsed_ms": 231},
                        {"name": "rclpy_init", "elapsed_ms": 27},
                    ],
                    "error": {
                        "type": "RCLError",
                        "message": "failed to create service: rcl node's context is invalid",
                    },
                }
            },
        }

        result = HELPER.build_ros2_graph_timeout_root_cause(
            board_source_preflight={
                "classification": "board_source_preflight_ready",
                "cli_ready": True,
                "runtime_ready": True,
                "ros2_cli_invocation_ok": True,
                "rclpy_import_ok": True,
            },
            managed_runtime=runtime,
            managed_runtime_wait_graph_blocked=True,
            probes=probes,
            tf_source_root_cause_detail={"reason": "/tf_topic_missing"},
            require_planner_server=True,
        )

        self.assertEqual("ros2_daemon_or_dds_graph_discovery_timeout", result["classification"])
        self.assertEqual("ros2_daemon_or_dds_graph_discovery_timeout", result["primary_candidate"]["classification"])
        self.assertNotEqual("board_source_preflight_ready", result["primary_candidate"]["reason"])
        self.assertIn(
            "workspace_source_or_env_mismatch",
            {item["classification"] for item in result["remaining_candidates"]},
        )
        self.assertIn(
            "managed_process_lifecycle_not_ready",
            {item["classification"] for item in result["remaining_candidates"]},
        )
        self.assertIn(
            "tf_runtime_secondary_after_graph_blocked",
            {item["classification"] for item in result["remaining_candidates"]},
        )
        self.assertEqual("skipped_after_ros2_graph_timeout", result["probes"]["managed_process"]["lifecycle_probe_status"])

    def test_graph_timeout_root_cause_cli_plugin_reason_uses_timeout_boundaries(self) -> None:
        """help 与 rclpy graph 低预算 probe 超时时，primary reason 不能写成 preflight ready。"""
        runtime = {
            "started": True,
            "process": mock.Mock(poll=mock.Mock(return_value=None)),
            "process_group": 499439,
            "wait_result": {
                "ok": False,
                "reason": "ros2_node_list_timeout",
                "observed_node_names": [],
                "lifecycle_results": {
                    "map_server": {"executed": False, "ok": False, "boundary": "managed_runtime_lifecycle_check_not_run"},
                    "amcl": {"executed": False, "ok": False, "boundary": "managed_runtime_lifecycle_check_not_run"},
                    "planner_server": {"executed": False, "ok": False, "boundary": "managed_runtime_lifecycle_check_not_run"},
                },
            },
            "log_path": "/tmp/o10-missing.log",
        }
        probes = {
            "ros2_node_list": {"boundary": "ros2_node_list_timeout"},
            "ros2_node_list_no_daemon": {"boundary": "ros2_node_list_no_daemon_timeout"},
            "ros2_daemon_status": {"boundary": "ros2_daemon_status_timeout"},
            "ros2_node_list_help": {"boundary": "ros2_node_list_help_timeout"},
            "ros2_topic_list": {"boundary": "ros2_topic_list_timeout"},
            "workspace_environment": {"boundary": "workspace_environment_timeout", "summary": {}},
            "rclpy_graph_segments": {"boundary": "rclpy_graph_segment_probe_timeout", "payload": {}},
        }

        result = HELPER.build_ros2_graph_timeout_root_cause(
            board_source_preflight={
                "classification": "board_source_preflight_ready",
                "cli_ready": True,
                "runtime_ready": True,
                "ros2_cli_invocation_ok": True,
                "rclpy_import_ok": True,
            },
            managed_runtime=runtime,
            managed_runtime_wait_graph_blocked=True,
            probes=probes,
            tf_source_root_cause_detail={"reason": "/tf_topic_missing"},
            require_planner_server=True,
        )

        self.assertEqual("ros2_cli_plugin_or_import_timeout", result["classification"])
        self.assertEqual("ros2_cli_plugin_or_import_timeout", result["primary_candidate"]["classification"])
        self.assertEqual(
            "ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout",
            result["primary_candidate"]["reason"],
        )
        self.assertNotEqual("board_source_preflight_ready", result["primary_candidate"]["reason"])
        self.assertIn("managed_process_lifecycle_not_ready", {item["classification"] for item in result["remaining_candidates"]})
        self.assertIn("tf_runtime_secondary_after_graph_blocked", {item["classification"] for item in result["remaining_candidates"]})

    def test_no_daemon_unsupported_is_probe_boundary_not_failure(self) -> None:
        """`ros2 node list --no-daemon` 不支持时应记录 unsupported，而不是 CLI failure。"""
        result = {
            "ok": False,
            "timed_out": False,
            "stdout": "",
            "stderr": "usage: ros2 [-h]\nros2: error: unrecognized arguments: --no-daemon\n",
        }

        self.assertTrue(HELPER.ros2_no_daemon_unsupported(result))
        self.assertEqual("unsupported_option", HELPER.graph_command_boundary("ros2_node_list_no_daemon", result))

    def test_lifecycle_skipped_preflight_does_not_emit_inactive_root_cause(self) -> None:
        """graph timeout 后 lifecycle 未执行，只能标 skipped，不能生成 inactive blocker。"""
        lifecycle_results = {
            "map_server": {
                "executed": False,
                "ok": False,
                "boundary": "managed_runtime_lifecycle_check_not_run",
            },
            "amcl": {
                "executed": False,
                "ok": False,
                "boundary": "managed_runtime_lifecycle_check_not_run",
            },
        }

        preflight = HELPER.build_map_lifecycle_preflight(
            ros2_cli_ok=True,
            lifecycle_active={"map_server": False, "amcl": False},
            lifecycle_results=lifecycle_results,
        )
        causes = HELPER.classify_root_causes(
            map_inputs={"root_causes": []},
            ros2_ok=True,
            board_source_preflight={
                "ros2_cli_ok": True,
                "rclpy_import_ok": True,
                "classification": "board_source_preflight_ready",
            },
            map_lifecycle_preflight=preflight,
            packages={package: True for package in HELPER.EXPECTED_PACKAGES},
            lifecycle_active={"map_server": False, "amcl": False},
            scan_once_observed=True,
            map_once_observed=True,
            amcl_pose_observed=False,
            localization_tf_observed={"map_to_odom": False, "map_to_base_link": False},
            tf_chain_observed=HELPER.default_tf_chain_observed(),
            tf_failure_classification={},
            initialpose_enabled=False,
            initialpose_publish={"ok": False},
            lifecycle_results=lifecycle_results,
        )

        self.assertEqual("map_lifecycle_preflight_lifecycle_probe_skipped_after_graph_blocked", preflight["classification"])
        self.assertEqual([], preflight["root_causes"])
        self.assertNotIn("map_server_lifecycle_not_active", {cause["reason"] for cause in causes})
        self.assertNotIn("amcl_lifecycle_not_active", {cause["reason"] for cause in causes})

    def test_initialpose_topic_info_probe_reuses_prewrite_endpoint_inventory(self) -> None:
        """现场不跑 `/initialpose --verbose`，subscriber 由写前 endpoint inventory 提供。"""
        text = SCRIPT.read_text(encoding="utf-8")

        self.assertIn('initialpose_publish.get("subscriber_count") is None', text)
        self.assertIn('pre_initialpose_gate.get("initialpose_subscriber_count")', text)
        self.assertIn("initialpose_subscriber_count_already_observed_by_publish", text)
        self.assertIn("initialpose_verbose_info_skipped_to_avoid_cli_stall", text)
        self.assertNotIn('run_ros(args, "ros2 topic info /initialpose --verbose"', text)
        self.assertNotIn(
            'initialpose_info = run_ros(args, "ros2 topic info /initialpose --verbose", timeout_s=6.0) if ros2_ok else {"executed": False, "ok": False}',
            text,
        )

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
            "export RMW_FASTRTPS_USE_SHM=0",
            "export FASTDDS_BUILTIN_TRANSPORTS=UDPv4",
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

    def test_managed_runtime_can_reuse_existing_lidar_lifecycle_without_second_driver(self) -> None:
        """Gate 2 复用既有 150000 lifecycle 时，runtime 只拉 Nav2/TF，不再启动第二个 LiDAR driver。"""
        args = HELPER.parse_args(
            [
                "--managed-runtime-opt-in",
                "--managed-map-yaml",
                "/tmp/test_map.yaml",
                "--reuse-existing-lidar-lifecycle",
                "--managed-lidar-serial-baudrate",
                "150000",
            ]
        )
        shell = HELPER.build_managed_runtime_shell(
            args,
            map_yaml="/tmp/test_map.yaml",
            params_path="/tmp/runtime.yaml",
            log_path="/tmp/runtime.log",
        )

        self.assertIn("managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start", shell)
        self.assertIn("reuse_existing_lidar_lifecycle serial_port=/dev/ttyACM0 serial_baudrate=150000", shell)
        self.assertIn("driver_started_by_helper=false", shell)
        self.assertIn("nav2_map_server map_server", shell)
        self.assertIn("nav2_amcl amcl", shell)
        self.assertIn("managed_static_tf_broadcaster", shell)
        self.assertNotIn("ros2 run ros2_trashbot_hardware lidar_driver", shell)
        self.assertNotIn("serial_baudrate:=150000", shell)
        self.assertNotIn("serial.Serial", shell)
        self.assertNotIn("/dev/ttyS5", shell.replace("blocked_device=/dev/ttyS5", ""))

    def test_stale_managed_runtime_cleanup_parser_scopes_to_helper_process_groups(self) -> None:
        """stale cleanup 只能命中 helper 自己的 rober_nav2_localization 进程组。"""
        ps_text = "\n".join(
            [
                " 101 101 bash -lc managed_runtime_boundary=no_motion_localization_only /tmp/rober_nav2_localization_a.log",
                " 102 101 /opt/ros/humble/lib/nav2_map_server/map_server --params-file /tmp/rober_nav2_localization_a.yaml",
                " 103 103 /opt/ros/humble/lib/nav2_map_server/map_server --params-file /tmp/not_rober.yaml",
                " 104 104 /usr/bin/python3 unrelated_service.py",
                " 105 105 python3 -c managed_static_tf_broadcaster /tmp/rober_nav2_localization_b.yaml",
            ]
        )

        groups = HELPER.stale_managed_runtime_process_groups_from_ps(
            ps_text,
            current_process_group=999,
        )

        self.assertEqual({101, 105}, set(groups))
        self.assertEqual({101, 102}, {entry["pid"] for entry in groups[101]})
        self.assertEqual([105], [entry["pid"] for entry in groups[105]])
        self.assertNotIn(103, {entry["pid"] for members in groups.values() for entry in members})

    def test_managed_runtime_log_lifecycle_readback_marks_active(self) -> None:
        """runtime log 已有 active/bond 证据时，graph timeout 不能覆盖 lifecycle clean 事实。"""
        log_text = "\n".join(
            [
                "[INFO] [lifecycle_manager]: Activating map_server",
                "[INFO] [map_server]: Activating",
                "[INFO] [map_server]: Creating bond (map_server) to lifecycle manager.",
                "[INFO] [lifecycle_manager]: Server map_server connected with bond.",
                "[INFO] [lifecycle_manager]: Activating amcl",
                "[INFO] [amcl]: Activating",
                "[INFO] [amcl]: Creating bond (amcl) to lifecycle manager.",
                "[INFO] [lifecycle_manager]: Server amcl connected with bond.",
                "[INFO] [lifecycle_manager]: Managed nodes are active",
            ]
        )

        readback = HELPER.managed_runtime_log_lifecycle_active_readback(log_text)

        self.assertTrue(readback["clean"])
        self.assertTrue(readback["active"]["map_server"])
        self.assertTrue(readback["active"]["amcl"])
        self.assertEqual("active [3]\n", readback["results"]["map_server"]["stdout"])
        self.assertTrue(readback["evidence"]["managed_nodes_active_logged"])

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
        self.assertIn('frame_id: "map"', params)
        self.assertIn("service_timeout: 12.0", params)
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

    def test_path_generation_request_uses_observed_amcl_pose_as_planner_start(self) -> None:
        """AMCL pose 已观测时，用显式 start 避免 planner 回查当前 TF 时间窗。"""
        args = HELPER.parse_args(
            [
                "--path-generation-opt-in",
                "--path-goal-x",
                "0.8",
                "--path-goal-y",
                "0.0",
            ]
        )

        request = HELPER.path_generation_request(
            args,
            observed_start_pose={"frame_id": "map", "x": -0.19, "y": -0.05, "yaw": 0.28},
        )
        payload = json.loads(HELPER.cli_compute_path_goal_payload(request))

        self.assertTrue(request["use_start"])
        self.assertEqual("amcl_pose_observed_for_planner_only_start", request["start_source"])
        self.assertAlmostEqual(-0.19, request["start_x"], places=2)
        self.assertAlmostEqual(-0.05, request["start_y"], places=2)
        self.assertTrue(payload["use_start"])
        self.assertAlmostEqual(-0.19, payload["start"]["pose"]["position"]["x"], places=2)
        self.assertAlmostEqual(request["start_orientation_z"], payload["start"]["pose"]["orientation"]["z"])

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

    def test_cli_compute_path_goal_payload_stays_planner_only(self) -> None:
        """CLI fallback 只能构造 ComputePathToPose goal，不能出现控制或导航执行字段。"""
        request = HELPER.path_generation_request(
            HELPER.parse_args(
                [
                    "--path-generation-opt-in",
                    "--path-goal-x",
                    "0.8",
                    "--path-goal-y",
                    "0.1",
                ]
            )
        )
        payload = HELPER.cli_compute_path_goal_payload(request)

        self.assertIn('"goal"', payload)
        self.assertIn('"start"', payload)
        self.assertIn('"planner_id"', payload)
        self.assertIn('"use_start"', payload)
        self.assertNotIn("/cmd_vel", payload)
        self.assertNotIn("/api/base/manual", payload)
        self.assertNotIn("follow_path", payload.lower())
        self.assertNotIn("navigate", payload.lower())

    def test_compute_path_cli_fallback_generates_path_after_python_import_error(self) -> None:
        """主 Python action import 坏掉时，helper 必须实际尝试 sourced CLI action fallback。"""
        args = HELPER.parse_args(
            [
                "--path-generation-opt-in",
                "--path-generation-timeout-s",
                "7",
                "--path-goal-x",
                "0.8",
            ]
        )
        request = HELPER.path_generation_request(args)
        action_list = {
            "ok": True,
            "timed_out": False,
            "returncode": 0,
            "stdout": "/compute_path_to_pose [nav2_msgs/action/ComputePathToPose]\n",
            "stderr": "",
            "elapsed_ms": 100,
        }
        action_result = {
            "ok": True,
            "timed_out": False,
            "returncode": 0,
            "stdout": """
Goal accepted with ID: 123
Result:
  path:
    header:
      frame_id: map
    poses:
    - header:
        frame_id: map
        stamp:
          sec: 1783868111
          nanosec: 698275634
      pose:
        position:
          x: 0.0
          y: 0.0
          z: 0.0
        orientation:
          x: 0.0
          y: 0.0
          z: 0.0
          w: 1.0
    - header:
        frame_id: map
        stamp:
          sec: 1783868111
          nanosec: 698275634
      pose:
        position:
          x: 0.8
          y: 0.0
          z: 0.0
        orientation:
          x: 0.0
          y: 0.0
          z: 0.0
          w: 1.0
  planning_time:
    sec: 0
    nanosec: 2000000
  error_code: 0
  error_msg: ''
status: STATUS_SUCCEEDED
""",
            "stderr": "",
            "elapsed_ms": 250,
        }
        with mock.patch.object(HELPER, "run_ros", side_effect=[action_list, action_result]) as run_mock:
            result, causes = HELPER.compute_path_generation_cli_fallback(
                args,
                request,
                python_import_error={"type": "ImportError", "message": "librcl_action.so missing"},
            )

        self.assertTrue(result["fallback_used"])
        self.assertEqual("ros2_cli_action_send_goal", result["fallback_mode"])
        self.assertTrue(result["path_generated"])
        self.assertTrue(result["ok"])
        self.assertEqual(2, result["path_point_count"])
        self.assertEqual(2, result["path_structured_pose_count"])
        self.assertEqual(2, len(result["path_structured_poses"]))
        self.assertEqual("map", result["path_structured_poses"][0]["frame_id"])
        self.assertEqual({"sec": 1783868111, "nanosec": 698275634}, result["path_structured_poses"][0]["stamp"])
        self.assertAlmostEqual(0.8, result["path_structured_poses"][1]["x"])
        self.assertAlmostEqual(0.0, result["path_structured_poses"][1]["y"])
        self.assertEqual(2, result["path_preview_point_count"])
        self.assertEqual(2, result["path_preview_source_point_count"])
        self.assertEqual("map", result["path_preview_frame_id"])
        self.assertEqual(2, result["path_goal_response"]["path_structured_pose_count"])
        self.assertEqual(2, len(result["path_goal_response"]["path_structured_poses"]))
        self.assertEqual("explicit_opt_in_compute_path_to_pose_cli_action_no_motion", result["boundary"])
        self.assertEqual([], causes)
        command = run_mock.call_args_list[1].args[1]
        self.assertIn("ros2 action send_goal /compute_path_to_pose nav2_msgs/action/ComputePathToPose", command)
        self.assertIn("timeout 7", command)
        self.assertNotIn("/cmd_vel", command)
        self.assertNotIn("/api/base/manual", command)
        self.assertNotIn("FollowPath", command)
        self.assertNotIn("NavigateToPose", command)
        self.assertNotIn("controller_server", command)
        self.assertNotIn("bt_navigator", command)
        self.assertNotIn("WAVE ROVER", command)

    def test_historic_cli_stdout_tail_cannot_reconstruct_full_twenty_one_pose_path(self) -> None:
        """旧 artifact 只有截断 stdout_tail，必须收口为 historic_stdout_tail_truncated_full_pose_replay_unavailable。"""
        historic_artifact = (
            REPO_ROOT
            / "sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair"
            / "artifacts/algorithm/live_o10_reuse_existing_lidar_lifecycle_path_proof_after_fallback.raw.json"
        )
        payload = json.loads(historic_artifact.read_text(encoding="utf-8"))
        proof = payload["proof"]
        path_result = proof["commands"]["path_generation"]["result"]
        stdout_tail = path_result["fallback_attempts"][0]["stdout_tail"]

        parsed = HELPER.parse_cli_compute_path_result(
            {"ok": True, "timed_out": False, "returncode": 0, "stdout": stdout_tail, "stderr": "", "elapsed_ms": 1},
            action_name="/compute_path_to_pose",
        )

        self.assertEqual(21, proof["path_point_count"])
        self.assertEqual(14, parsed["path_structured_pose_count"])
        self.assertLess(parsed["path_structured_pose_count"], proof["path_point_count"])
        self.assertEqual("historic_stdout_tail_truncated_full_pose_replay_unavailable", "historic_stdout_tail_truncated_full_pose_replay_unavailable")
        self.assertNotIn("path_structured_poses", proof["path_goal_response"])
        self.assertFalse(proof["route_execution_success"])
        self.assertFalse(proof["delivery_success"])
        self.assertFalse(proof["hil_pass"])

    def test_managed_param_file_only_lists_localization_nodes(self) -> None:
        """参数文件只能包含 map_server/amcl/lifecycle_manager，不能偷偷把运动栈拉起来。"""
        args = HELPER.parse_args([])
        text = HELPER.managed_param_file_text(args, "/tmp/test_map.yaml")

        for required in (
            "map_server:",
            'frame_id: "map"',
            "amcl:",
            "lifecycle_manager:",
            "bond_timeout: 8.0",
            "service_timeout: 12.0",
            'node_names: ["map_server", "amcl"]',
        ):
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

    def test_cleanup_rejects_non_helper_process_group_identity(self) -> None:
        """expected PID 与 PGID 不一致时不得发 signal，避免误伤既有 LiDAR/ESP32/API。"""
        with mock.patch.object(
            HELPER,
            "process_group_members",
            return_value=[{"pid": 123, "pgid": 456, "command": "existing_lidar_driver"}],
        ), mock.patch.object(HELPER.os, "killpg") as kill_mock:
            result = HELPER.cleanup_process_group(456, expected_process_pid=999)

        self.assertFalse(result["attempted"])
        self.assertFalse(result["helper_owned_identity"]["verified"])
        self.assertEqual(1, result["residual_count"])
        kill_mock.assert_not_called()

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
            "NavigateToPose",
            "FollowPath",
            "ros2 run nav2_bt_navigator",
            "controller_server --ros-args",
            "serial.Serial(",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("nav2_msgs/action/ComputePathToPose", text)

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
            "process.communicate(timeout=1.0)",
            "drain_exc",
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

    def test_tf_source_diagnostics_accepts_dynamic_odom_base_link(self) -> None:
        """真实桥接节点会在 /tf 动态发布 odom->base_link，不能被误判为缺 static TF。"""
        args = HELPER.parse_args([])
        amcl_probe = {
            "param_probe_ok": True,
            "node_info_observed": True,
            "params": {
                "tf_broadcast": True,
                "global_frame_id": "map",
                "odom_frame_id": "odom",
                "base_frame_id": "base_link",
            },
            "publishers": [{"topic": "/tf", "type": "tf2_msgs/msg/TFMessage"}],
            "subscribers": [{"topic": "/scan", "type": "sensor_msgs/msg/LaserScan"}],
            "topic_types": {"/tf": "tf2_msgs/msg/TFMessage", "/tf_static": "tf2_msgs/msg/TFMessage"},
            "topic_endpoint_summaries": {
                "/tf": {
                    "publishers": [
                        {
                            "node_name": "amcl",
                            "node_namespace": "/",
                            "topic_type": "tf2_msgs/msg/TFMessage",
                            "qos_profile": {"reliability": "RELIABLE", "durability": "VOLATILE"},
                        }
                    ],
                    "subscribers": [],
                    "publisher_count": 1,
                    "subscriber_count": 0,
                    "inventory_observed": True,
                    "error": None,
                }
            },
            "dynamic_edges": [
                {"parent": "map", "child": "odom", "topic": "/tf"},
                {"parent": "odom", "child": "base_link", "topic": "/tf"},
            ],
            "static_edges": [{"parent": "base_link", "child": "laser_frame", "topic": "/tf_static"}],
            "command_statuses": {"rclpy_graph": 0, "tf": 0, "tf_static": 0},
            "boundary": "rclpy_amcl_params_graph_tf_probe_observed",
        }

        source = HELPER.build_tf_source_diagnostics(
            args,
            {"stdout": "", "ok": True},
            amcl_pose_result={"stdout": "header:\n  frame_id: map\n"},
            amcl_probe=amcl_probe,
        )

        self.assertTrue(source["map_to_odom_source_observed"])
        self.assertTrue(source["odom_to_base_link_source_observed"])
        self.assertTrue(source["odom_to_base_link_dynamic_source_observed"])
        self.assertFalse(source["odom_to_base_link_static_source_observed"])
        self.assertTrue(source["base_link_to_laser_frame_source_observed"])
        self.assertEqual("source_inventory_observed", source["amcl_tf_root_cause"])
        self.assertEqual(
            "attributed_unique_amcl",
            source["map_to_odom_publisher_attribution"]["publisher_attribution_status"],
        )

    def test_dynamic_map_to_odom_is_attributed_to_amcl_endpoint_with_fresh_stamp(self) -> None:
        """clean dynamic edge 必须同时关联 `/tf`、AMCL endpoint、可解析 stamp 和 fresh 判定。"""
        args = HELPER.parse_args([])
        generated_at_ms = 1_780_000_000_000
        amcl_probe = {
            "param_probe_ok": True,
            "node_info_observed": True,
            "params": {"tf_broadcast": True, "global_frame_id": "map", "odom_frame_id": "odom", "base_frame_id": "base_link"},
            "publishers": [{"topic": "/tf", "type": "tf2_msgs/msg/TFMessage"}],
            "subscribers": [{"topic": "/scan", "type": "sensor_msgs/msg/LaserScan"}],
            "topic_types": {"/tf": "tf2_msgs/msg/TFMessage"},
            "topic_endpoint_summaries": {
                "/tf": {
                    "publishers": [
                        {"node_name": "amcl", "node_namespace": "/", "topic_type": "tf2_msgs/msg/TFMessage", "qos_profile": {"reliability": "RELIABLE"}},
                        {"node_name": "odom_bridge", "node_namespace": "/", "topic_type": "tf2_msgs/msg/TFMessage", "qos_profile": {"reliability": "RELIABLE"}},
                    ],
                    "subscribers": [],
                    "publisher_count": 2,
                    "subscriber_count": 0,
                    "inventory_observed": True,
                    "error": None,
                }
            },
            "dynamic_edges": [{"parent": "map", "child": "odom", "topic": "/tf"}],
            "static_edges": [],
            "dynamic_transforms": [
                {
                    "parent_frame_id": "map",
                    "child_frame_id": "odom",
                    "stamp": HELPER.ros_stamp_parts_to_artifact(1_780_000_000, 0, source="/tf.header.stamp"),
                    "received_at_ms": generated_at_ms,
                    "source": "/tf",
                }
            ],
            "static_transforms": [],
            "command_statuses": {"rclpy_graph": 0, "tf": 0, "tf_static": 124},
            "boundary": "rclpy_amcl_params_graph_tf_probe_observed",
        }
        source = HELPER.build_tf_source_diagnostics(
            args,
            {"stdout": "", "ok": True},
            amcl_pose_result={"stdout": "header:\n  frame_id: map\n"},
            amcl_probe=amcl_probe,
        )
        freshness = HELPER.build_tf_source_freshness(
            args=args,
            generated_at_ms=generated_at_ms,
            tf_source_diagnostics=source,
        )
        edge = freshness["edges"]["map_to_odom"]

        self.assertEqual("/tf", edge["source_topic"])
        self.assertEqual("attributed_unique_amcl", edge["publisher_attribution_status"])
        self.assertEqual("/amcl", edge["publisher_endpoint"]["node_full_name"])
        self.assertTrue(edge["timestamp"]["parsed"])
        self.assertEqual(generated_at_ms, freshness["evaluated_at_ms"])
        self.assertEqual(generated_at_ms, edge["evaluated_at_ms"])
        self.assertEqual(generated_at_ms, edge["received_at_ms"])
        self.assertEqual("fresh", edge["freshness"]["status"])

    def test_dynamic_map_to_odom_multiple_amcl_endpoints_stays_ambiguous(self) -> None:
        """同名 AMCL endpoint 出现多份时必须保留候选并 fail closed，不能任选一个。"""
        attribution = HELPER.tf_map_to_odom_publisher_attribution(
            dynamic_source_observed=True,
            tf_endpoint_summary={
                "inventory_observed": True,
                "publisher_count": 2,
                "publishers": [
                    {"node_name": "amcl", "node_namespace": "/", "topic_type": "tf2_msgs/msg/TFMessage", "qos_profile": {"reliability": "RELIABLE"}},
                    {"node_name": "amcl", "node_namespace": "/", "topic_type": "tf2_msgs/msg/TFMessage", "qos_profile": {"reliability": "BEST_EFFORT"}},
                ],
            },
            amcl_publishers=[{"topic": "/tf", "type": "tf2_msgs/msg/TFMessage"}],
        )

        self.assertEqual("ambiguous_multiple_amcl_tf_publisher_endpoints", attribution["publisher_attribution_status"])
        self.assertIsNone(attribution["publisher_endpoint"])
        self.assertEqual(2, len(attribution["publisher_endpoint_candidates"]))

    def test_tf_source_child_pose_sample_drives_same_window_freshness_without_initialpose(self) -> None:
        """strict no-motion 禁发 initialpose 时，child 只读订阅仍应回写 pose stamp/freshness。"""
        generated_at_ms = 1_780_000_000_500
        sample = {
            "observed": True,
            "sample_count": 2,
            "received_at_ms": generated_at_ms,
            "frame_id": "map",
            "stamp": HELPER.ros_stamp_parts_to_artifact(
                1_780_000_000,
                400_000_000,
                source="/amcl_pose.header.stamp",
            ),
        }
        diagnostics = HELPER.default_tf_source_diagnostics(
            HELPER.parse_args([]),
            amcl_pose_result={"executed": False, "ok": False},
        )
        diagnostics["amcl_pose_sample"] = sample
        diagnostics["tf_frame_inventory"]["topic_types"] = {
            "/amcl_pose": "geometry_msgs/msg/PoseWithCovarianceStamped"
        }
        diagnostics["topic_endpoint_summaries"]["/amcl_pose"] = {
            "publishers": [
                {
                    "node_name": "amcl",
                    "node_namespace": "/",
                    "topic_type": "geometry_msgs/msg/PoseWithCovarianceStamped",
                    "qos_profile": {"reliability": "RELIABLE"},
                }
            ],
            "subscribers": [],
            "publisher_count": 1,
            "subscriber_count": 0,
            "inventory_observed": True,
            "error": None,
        }

        signals = HELPER.build_localization_signal_freshness(
            generated_at_ms=generated_at_ms,
            tf_source_diagnostics=diagnostics,
            tf_source_probe_result={"executed": True, "elapsed_ms": 3200},
            topic_list_result={"stdout": ""},
            scan_once={"executed": False, "ok": False},
            map_once={"executed": False, "ok": False},
            amcl_pose_once={"executed": False, "ok": False},
            post_initialpose_amcl_pose_once={"executed": False, "ok": False},
            odom_once={"executed": False, "ok": False},
            managed_runtime_started=True,
        )
        pose = signals["/amcl_pose"]
        compact = HELPER.compact_tf_source_child_payload({"amcl_pose_sample": sample})

        self.assertTrue(pose["probe"]["observed"])
        self.assertEqual("amcl_pose_sample_observed_by_tf_source_child", pose["probe"]["boundary"])
        self.assertTrue(pose["timestamp"]["parsed"])
        self.assertEqual("fresh", pose["freshness"]["status"])
        self.assertEqual(2, pose["direct_read_only_sample"]["sample_count"])
        self.assertEqual(sample, compact["amcl_pose_sample"])

    def test_dynamic_map_to_odom_stale_or_missing_timestamp_is_not_fresh(self) -> None:
        """publisher 已归因也不能覆盖 stale/missing stamp；freshness 必须单独 fail closed。"""
        common = {
            "name": "map_to_odom",
            "parent": "map",
            "child": "odom",
            "required_source_class": "dynamic",
            "dynamic_edges": [{"parent": "map", "child": "odom", "topic": "/tf"}],
            "static_edges": [],
            "static_transforms": [],
            "generated_at_ms": 1_780_000_000_000,
        }
        stale = HELPER.tf_edge_freshness_entry(
            **common,
            dynamic_transforms=[{
                "parent_frame_id": "map",
                "child_frame_id": "odom",
                "stamp": HELPER.ros_stamp_parts_to_artifact(1_779_999_990, 0, source="/tf.header.stamp"),
                "received_at_ms": 1_780_000_000_000,
            }],
        )
        missing = HELPER.tf_edge_freshness_entry(**common, dynamic_transforms=[])

        self.assertEqual("stale", stale["freshness"]["status"])
        self.assertEqual("unknown", missing["freshness"]["status"])
        self.assertEqual("transform_stamp_not_observed", missing["freshness"]["reason"])

    def test_tf_receipt_time_keeps_clean_header_fresh_despite_late_evaluation(self) -> None:
        """上轮 5090ms 形态中，collector 延迟不得再被追加到 dynamic TF stale gate。"""
        header_ms = 1_780_000_000_000
        received_at_ms = header_ms + 90
        evaluated_at_ms = header_ms + 5090
        edge = HELPER.tf_edge_freshness_entry(
            name="map_to_odom",
            parent="map",
            child="odom",
            required_source_class="dynamic",
            dynamic_edges=[{"parent": "map", "child": "odom", "topic": "/tf"}],
            static_edges=[],
            dynamic_transforms=[{
                "parent_frame_id": "map",
                "child_frame_id": "odom",
                "stamp": HELPER.ros_stamp_parts_to_artifact(1_780_000_000, 0, source="/tf.header.stamp"),
                "received_at_ms": received_at_ms,
            }],
            static_transforms=[],
            generated_at_ms=evaluated_at_ms,
        )

        self.assertEqual("fresh", edge["freshness"]["status"])
        self.assertEqual("header_age_at_receipt_ms", edge["freshness"]["decision_basis"])
        self.assertEqual(90, edge["header_age_at_receipt_ms"])
        self.assertEqual(5000, edge["receipt_age_at_evaluation_ms"])
        self.assertEqual(5090, edge["header_age_at_evaluation_ms"])
        self.assertEqual(90, edge["freshness"]["age_ms"])
        self.assertEqual(3000, edge["freshness"]["threshold_ms"])

    def test_tf_header_already_stale_at_receipt_stays_stale(self) -> None:
        """新 receipt 不能洗白真正迟到的 header，decision age 超过 3000ms 必须 stale。"""
        header_ms = 1_780_000_000_000
        edge = HELPER.tf_edge_freshness_entry(
            name="map_to_odom",
            parent="map",
            child="odom",
            required_source_class="dynamic",
            dynamic_edges=[{"parent": "map", "child": "odom", "topic": "/tf"}],
            static_edges=[],
            dynamic_transforms=[{
                "parent_frame_id": "map",
                "child_frame_id": "odom",
                "stamp": HELPER.ros_stamp_parts_to_artifact(1_780_000_000, 0, source="/tf.header.stamp"),
                "received_at_ms": header_ms + 3001,
            }],
            static_transforms=[],
            generated_at_ms=header_ms + 3500,
        )

        self.assertEqual("stale", edge["freshness"]["status"])
        self.assertEqual(3001, edge["freshness"]["header_age_at_receipt_ms"])
        self.assertEqual("older_than_threshold_at_callback_receipt", edge["freshness"]["reason"])

    def test_dynamic_tf_missing_or_invalid_receipt_fails_closed(self) -> None:
        """CLI/旧 artifact 没有 callback receipt 时，禁止拿 evaluation time 冒充接收时间。"""
        common = {
            "name": "map_to_odom",
            "parent": "map",
            "child": "odom",
            "required_source_class": "dynamic",
            "dynamic_edges": [{"parent": "map", "child": "odom", "topic": "/tf"}],
            "static_edges": [],
            "static_transforms": [],
            "generated_at_ms": 1_780_000_000_500,
        }
        stamp = HELPER.ros_stamp_parts_to_artifact(1_780_000_000, 0, source="/tf.header.stamp")
        missing = HELPER.tf_edge_freshness_entry(
            **common,
            dynamic_transforms=[{"parent_frame_id": "map", "child_frame_id": "odom", "stamp": stamp}],
        )
        invalid = HELPER.tf_edge_freshness_entry(
            **common,
            dynamic_transforms=[{
                "parent_frame_id": "map",
                "child_frame_id": "odom",
                "stamp": stamp,
                "received_at_ms": "command-finished-at",
            }],
        )

        self.assertEqual("unknown", missing["freshness"]["status"])
        self.assertEqual("callback_receipt_missing_or_invalid", missing["freshness"]["reason"])
        self.assertEqual("unknown", invalid["freshness"]["status"])
        self.assertIsNone(invalid["header_age_at_receipt_ms"])

    def test_dynamic_tf_invalid_header_or_clock_order_fails_closed(self) -> None:
        """header 不可解析或明显晚于 callback receipt 时必须 unknown，不能 clamp 成 fresh。"""
        common = {
            "name": "map_to_odom",
            "parent": "map",
            "child": "odom",
            "required_source_class": "dynamic",
            "dynamic_edges": [{"parent": "map", "child": "odom", "topic": "/tf"}],
            "static_edges": [],
            "static_transforms": [],
            "generated_at_ms": 1_780_000_001_000,
        }
        invalid_header = HELPER.tf_edge_freshness_entry(
            **common,
            dynamic_transforms=[{
                "parent_frame_id": "map",
                "child_frame_id": "odom",
                "stamp": {"parsed": False, "reason": "stamp_sec_parse_failed"},
                "received_at_ms": 1_780_000_000_000,
            }],
        )
        future_header = HELPER.tf_edge_freshness_entry(
            **common,
            dynamic_transforms=[{
                "parent_frame_id": "map",
                "child_frame_id": "odom",
                "stamp": HELPER.ros_stamp_parts_to_artifact(1_780_000_001, 0, source="/tf.header.stamp"),
                "received_at_ms": 1_780_000_000_000,
            }],
        )

        self.assertEqual("unknown", invalid_header["freshness"]["status"])
        self.assertEqual("stamp_sec_parse_failed", invalid_header["freshness"]["reason"])
        self.assertEqual("unknown", future_header["freshness"]["status"])
        self.assertEqual(
            "header_stamp_is_in_future_relative_to_callback_receipt",
            future_header["freshness"]["reason"],
        )

    def test_tf_message_transforms_share_single_callback_receipt(self) -> None:
        """同一 TFMessage 的多条 transform 必须共享 callback 入口记录的一次 receipt。"""
        def transform(parent: str, child: str) -> SimpleNamespace:
            return SimpleNamespace(
                header=SimpleNamespace(frame_id=parent, stamp=SimpleNamespace(sec=1_780_000_000, nanosec=0)),
                child_frame_id=child,
                transform=SimpleNamespace(
                    translation=SimpleNamespace(x=0.0, y=0.0, z=0.0),
                    rotation=SimpleNamespace(x=0.0, y=0.0, z=0.0, w=1.0),
                ),
            )

        receipt = 1_780_000_000_123
        transforms = HELPER.tf_message_transforms(
            SimpleNamespace(transforms=[transform("map", "odom"), transform("odom", "base_link")]),
            source_topic="/tf",
            received_at_ms=receipt,
        )

        self.assertEqual(2, len(transforms))
        self.assertEqual([receipt, receipt], [item["received_at_ms"] for item in transforms])

    def test_static_map_to_odom_does_not_inherit_dynamic_publisher_attribution(self) -> None:
        """即使 AMCL endpoint 存在，`/tf_static` 的 map->odom 也不得冒充 dynamic AMCL source。"""
        args = HELPER.parse_args([])
        source = {
            "tf_frame_inventory": {
                "dynamic_edges": [],
                "static_edges": [{"parent": "map", "child": "odom", "topic": "/tf_static"}],
                "dynamic_transforms": [],
                "static_transforms": [],
            },
            "map_to_odom_publisher_attribution": HELPER.tf_map_to_odom_publisher_attribution(
                dynamic_source_observed=False,
                tf_endpoint_summary={
                    "inventory_observed": True,
                    "publisher_count": 1,
                    "publishers": [{"node_name": "amcl", "node_namespace": "/", "topic_type": "tf2_msgs/msg/TFMessage"}],
                },
                amcl_publishers=[{"topic": "/tf", "type": "tf2_msgs/msg/TFMessage"}],
            ),
        }
        edge = HELPER.build_tf_source_freshness(
            args=args,
            generated_at_ms=1_780_000_000_000,
            tf_source_diagnostics=source,
        )["edges"]["map_to_odom"]

        self.assertFalse(edge["observed"])
        self.assertEqual("static", edge["source_class"])
        self.assertEqual("/tf_static", edge["source_topic"])
        self.assertFalse(edge["dynamic_source_observed"])
        self.assertEqual("not_attributed_dynamic_map_to_odom_not_observed", edge["publisher_attribution_status"])

    def test_signal_freshness_records_scan_probe_timeout_root_cause(self) -> None:
        """`/scan` topic 存在但 once probe timeout 时，root cause 必须落到 probe/freshness 层。"""
        generated_at_ms = 1_780_000_000_000
        tf_source_diagnostics = {
            "tf_frame_inventory": {
                "topic_types": {
                    "/scan": "sensor_msgs/msg/LaserScan",
                    "/amcl_pose": "geometry_msgs/msg/PoseWithCovarianceStamped",
                    "/odom": "nav_msgs/msg/Odometry",
                    "/tf": "tf2_msgs/msg/TFMessage",
                    "/tf_static": "tf2_msgs/msg/TFMessage",
                },
                "dynamic_edges": [],
                "static_edges": [],
                "dynamic_transforms": [],
                "static_transforms": [],
                "command_statuses": {"tf": 124, "tf_static": 124},
            },
            "topic_endpoint_summaries": {
                "/scan": {
                    "publisher_count": 1,
                    "subscriber_count": 1,
                    "publishers": [{"node_name": "lidar_driver", "node_namespace": "/", "topic_type": "sensor_msgs/msg/LaserScan"}],
                    "subscribers": [{"node_name": "amcl", "node_namespace": "/", "topic_type": "sensor_msgs/msg/LaserScan"}],
                }
            },
        }
        scan_once = {
            "executed": True,
            "ok": False,
            "returncode": 124,
            "elapsed_ms": 6010,
            "timeout_s": 8.0,
            "timed_out": True,
            "stdout": "",
            "stderr": "",
            "attempts": [
                {
                    "label": "rclpy_sensor_data_once",
                    "source": "rclpy_subscription",
                    "qos_profile": "sensor_data",
                    "timed_out": True,
                    "observed": False,
                    "boundary": "rclpy_scan_once_timeout",
                },
                {
                    "label": "cli_sensor_data_echo_once",
                    "source": "ros2_topic_echo_cli",
                    "qos_profile": "sensor_data",
                    "timed_out": True,
                    "observed": False,
                    "boundary": "scan_cli_sensor_data_timeout",
                },
            ],
            "best_attempt": {
                "label": "cli_sensor_data_echo_once",
                "source": "ros2_topic_echo_cli",
                "qos_profile": "sensor_data",
                "timed_out": True,
                "observed": False,
                "boundary": "scan_cli_sensor_data_timeout",
            },
            "qos_probe_boundary": "scan_cli_sensor_data_timeout",
            "source": "ros2_topic_echo_cli",
        }
        freshness = HELPER.build_localization_signal_freshness(
            generated_at_ms=generated_at_ms,
            tf_source_diagnostics=tf_source_diagnostics,
            tf_source_probe_result={"executed": True, "elapsed_ms": 4000, "boundary": "rclpy_probe"},
            topic_list_result={"stdout": "/scan\n/amcl_pose\n/odom\n/tf\n/tf_static\n"},
            scan_once=scan_once,
            amcl_pose_once={"executed": False, "ok": False},
            post_initialpose_amcl_pose_once={"executed": False, "ok": False},
            odom_once={"executed": False, "ok": False},
        )
        causes = HELPER.classify_root_causes(
            map_inputs={"root_causes": []},
            ros2_ok=True,
            board_source_preflight={
                "ros2_cli_ok": True,
                "rclpy_import_ok": True,
                "classification": "board_source_preflight_ready",
            },
            map_lifecycle_preflight={"root_causes": []},
            packages={package: True for package in HELPER.EXPECTED_PACKAGES},
            lifecycle_active={"map_server": True, "amcl": True},
            scan_once_observed=False,
            map_once_observed=True,
            amcl_pose_observed=False,
            localization_tf_observed={"map_to_odom": False, "map_to_base_link": False},
            tf_chain_observed=HELPER.default_tf_chain_observed(),
            tf_failure_classification={},
            initialpose_enabled=False,
            initialpose_publish={"ok": False},
            localization_signal_freshness=freshness,
            tf_source_freshness={"edges": {}},
        )

        self.assertEqual("sensor_msgs/msg/LaserScan", freshness["/scan"]["topic_type"])
        self.assertEqual(1, freshness["/scan"]["publishers"]["count"])
        self.assertTrue(freshness["/scan"]["probe"]["timed_out"])
        self.assertEqual("sensor_data", freshness["/scan"]["probe"]["best_attempt"]["qos_profile"])
        self.assertEqual(2, len(freshness["/scan"]["probe"]["attempts"]))
        self.assertEqual("scan_cli_sensor_data_timeout", freshness["/scan"]["probe"]["qos_probe_boundary"])
        self.assertEqual("/scan_qos_or_window_timeout", freshness["/scan"]["probe"]["classification"])
        self.assertEqual(1, freshness["/scan"]["publisher_inventory"]["publisher_count"])
        self.assertEqual(1, freshness["/scan"]["endpoint_inventory"]["publisher_count"])
        self.assertEqual("sensor_data", freshness["/scan"]["endpoint_inventory"]["requested_qos_profile"]["profile"])
        self.assertEqual(0, freshness["/scan"]["sample_timing"]["sample_count"])
        self.assertEqual("not_observed", freshness["/scan"]["freshness"]["status"])
        self.assertEqual("/scan_qos_or_window_timeout", causes[0]["reason"])

    def test_signal_root_cause_prefers_no_publishers_before_timeout(self) -> None:
        """topic 可见但无 publisher 时，应先收口到 publisher 层而不是 timeout。"""
        reason = HELPER.signal_root_cause_reason(
            {
                "topic_present": True,
                "endpoint_inventory_observed": True,
                "publishers": {"count": 0, "nodes": []},
                "probe": {"timed_out": True, "attempts": []},
                "freshness": {"status": "not_observed"},
            },
            "/scan",
            "/scan_once_not_observed",
        )

        self.assertEqual("/scan_no_publisher", reason)

    def test_scan_endpoint_inventory_shape_keeps_qos_and_runtime_fields(self) -> None:
        """`/scan` artifact 必须同屏呈现 publisher、endpoint QoS、sample timing 与 child runtime。"""
        endpoint_summary = {
            "inventory_observed": True,
            "publisher_count": 1,
            "subscriber_count": 1,
            "publishers": [
                {
                    "node_name": "lidar_driver",
                    "node_namespace": "/",
                    "topic_type": "sensor_msgs/msg/LaserScan",
                    "qos_profile": {"reliability": "BEST_EFFORT", "durability": "VOLATILE"},
                }
            ],
            "subscribers": [
                {
                    "node_name": "amcl",
                    "node_namespace": "/",
                    "topic_type": "sensor_msgs/msg/LaserScan",
                    "qos_profile": {"reliability": "BEST_EFFORT", "durability": "VOLATILE"},
                }
            ],
        }
        probe_result = {
            "executed": True,
            "ok": False,
            "returncode": 4,
            "timed_out": True,
            "timeout_s": 2.2,
            "elapsed_ms": 2240,
            "boundary": "rclpy_scan_child_timeout",
            "best_attempt": {
                "source": "rclpy_subscription",
                "qos_profile": "sensor_data",
                "timed_out": True,
                "observed": False,
                "import_check": {"attempted": True, "ok": True, "classification": None},
                "child_runtime": {
                    "import_ok": True,
                    "node_created": True,
                    "subscription_created": True,
                    "sample_wait_started": True,
                },
                "requested_qos_profile": {
                    "profile": "sensor_data",
                    "reliability": "BEST_EFFORT",
                    "durability": "VOLATILE",
                },
                "sample_timing": {
                    "probe_window_sec": 2.2,
                    "sample_wait_started_at_ms": 1_780_000_000_010,
                    "sample_wait_finished_at_ms": 1_780_000_002_230,
                    "timeout_boundary_ms": 1_780_000_002_210,
                    "first_sample_latency_ms": None,
                    "sample_count": 0,
                    "last_sample_stamp": None,
                    "last_sample_received_at_ms": None,
                    "timed_out": True,
                },
            },
        }

        entry = HELPER.build_signal_entry(
            topic="/scan",
            topic_type="sensor_msgs/msg/LaserScan",
            endpoint_summary=endpoint_summary,
            probe_result=probe_result,
            observed=False,
            stamp={"parsed": False},
            source_class="message",
            reference_ms=1_780_000_002_240,
            managed_runtime_started=True,
        )

        self.assertEqual(1, entry["publisher_inventory"]["publisher_count"])
        self.assertEqual("lidar_driver", entry["publisher_inventory"]["publisher_nodes"][0]["node_name"])
        self.assertEqual("BEST_EFFORT", entry["endpoint_inventory"]["endpoint_qos_profiles"]["publishers"][0]["reliability"])
        self.assertEqual("sensor_data", entry["endpoint_inventory"]["requested_qos_profile"]["profile"])
        self.assertEqual(0, entry["sample_timing"]["sample_count"])
        self.assertTrue(entry["sample_timing"]["timed_out"])
        self.assertTrue(entry["probe"]["child_runtime"]["subscription_created"])
        self.assertEqual("/scan_qos_or_window_timeout", entry["probe"]["classification"])
        self.assertTrue(entry["managed_runtime_scan_status"]["lidar_runtime_started"])

    def test_scan_freshness_prefers_child_endpoint_inventory(self) -> None:
        """主进程 rclpy graph 缺失时，`/scan` 仍要消费 child probe 里的 endpoint 清单。"""
        child_endpoint_inventory = {
            "inventory_observed": True,
            "publisher_count": 1,
            "subscriber_count": 1,
            "publishers": [
                {
                    "node_name": "lidar_driver",
                    "node_namespace": "/",
                    "topic_type": "sensor_msgs/msg/LaserScan",
                    "qos_profile": {"reliability": "BEST_EFFORT", "durability": "VOLATILE"},
                }
            ],
            "subscribers": [
                {
                    "node_name": "o10_scan_probe_child",
                    "node_namespace": "/",
                    "topic_type": "sensor_msgs/msg/LaserScan",
                    "qos_profile": {"reliability": "BEST_EFFORT", "durability": "VOLATILE"},
                }
            ],
            "source": "rclpy_child_get_publishers_info_by_topic",
        }
        scan_once = {
            "executed": True,
            "ok": False,
            "timed_out": True,
            "timeout_s": 8.0,
            "attempts": [
                {
                    "label": "rclpy_sensor_data_once",
                    "source": "rclpy_subscription",
                    "qos_profile": "sensor_data",
                    "timed_out": True,
                    "observed": False,
                    "endpoint_inventory": child_endpoint_inventory,
                    "child_runtime": {"subscription_created": True},
                    "sample_timing": {"probe_window_sec": 2.2, "sample_count": 0, "timed_out": True},
                    "requested_qos_profile": {
                        "history": "KEEP_LAST",
                        "depth": 5,
                        "reliability": "BEST_EFFORT",
                        "durability": "VOLATILE",
                    },
                }
            ],
            "best_attempt": {"label": "cli_default_echo_once", "source": "ros2_topic_echo_cli", "timed_out": True},
        }

        freshness = HELPER.build_localization_signal_freshness(
            generated_at_ms=1_780_000_000_000,
            tf_source_diagnostics={"tf_frame_inventory": {"topic_types": {"/scan": "sensor_msgs/msg/LaserScan"}}},
            tf_source_probe_result={"executed": False},
            topic_list_result={"stdout": "/scan [sensor_msgs/msg/LaserScan]\n"},
            scan_once=scan_once,
            amcl_pose_once={"executed": False, "ok": False},
            post_initialpose_amcl_pose_once={"executed": False, "ok": False},
            odom_once={"executed": False, "ok": False},
            managed_runtime_started=True,
        )

        scan = freshness["/scan"]
        self.assertTrue(scan["endpoint_inventory"]["inventory_observed"])
        self.assertEqual(1, scan["endpoint_inventory"]["publisher_count"])
        self.assertEqual("lidar_driver", scan["publisher_inventory"]["publisher_nodes"][0]["node_name"])
        self.assertEqual("/scan_publisher_visible_but_no_sample", scan["probe"]["classification"])

    def test_scan_probe_classification_covers_endpoint_timing_inventory_states(self) -> None:
        """本轮要求的六个 `/scan` 分类必须由独立字段稳定推导出来。"""
        base_probe = {"timed_out": True, "attempts": [], "best_attempt": {}}
        sample_timing_empty = {"sample_count": 0}

        cases = [
            (
                "/scan_no_publisher",
                True,
                {"inventory_observed": True, "publisher_count": 0},
                base_probe,
                sample_timing_empty,
                False,
                True,
            ),
            (
                "/scan_lidar_runtime_not_started",
                True,
                {"inventory_observed": True, "publisher_count": 0},
                base_probe,
                sample_timing_empty,
                False,
                False,
            ),
            (
                "/scan_publisher_visible_but_no_sample",
                True,
                {"inventory_observed": True, "publisher_count": 1},
                {"timed_out": False, "attempts": [], "best_attempt": {"qos_profile": "default"}},
                sample_timing_empty,
                False,
                True,
            ),
            (
                "/scan_reliable_and_best_effort_timeout",
                True,
                {"inventory_observed": True, "publisher_count": 1},
                {
                    "timed_out": True,
                    "attempts": [{"timed_out": True}, {"timed_out": True}],
                    "best_attempt": {"qos_profile": "sensor_data"},
                    "best_effort_attempt": {"timed_out": True},
                    "reliable_attempt": {"timed_out": True},
                },
                sample_timing_empty,
                False,
                True,
            ),
            (
                "/scan_qos_or_window_timeout",
                False,
                {"inventory_observed": True, "publisher_count": 1},
                {"timed_out": True, "attempts": [{"timed_out": True}], "best_attempt": {"qos_profile": "sensor_data"}},
                sample_timing_empty,
                False,
                True,
            ),
            (
                "/scan_rclpy_child_timeout_after_import",
                True,
                {"inventory_observed": False, "publisher_count": 0},
                {
                    "timed_out": True,
                    "attempts": [],
                    "best_attempt": {
                        "source": "rclpy_subscription",
                        "import_check": {"ok": True},
                        "child_runtime": {"subscription_created": True},
                    },
                },
                sample_timing_empty,
                False,
                None,
            ),
            (
                "/scan_sample_observed",
                True,
                {"inventory_observed": True, "publisher_count": 1},
                {"timed_out": False, "attempts": [], "best_attempt": {}},
                {"sample_count": 1},
                True,
                True,
            ),
        ]

        for expected, topic_present, endpoint_inventory, probe, sample_timing, observed, managed_started in cases:
            with self.subTest(expected=expected):
                self.assertEqual(
                    expected,
                    HELPER.scan_probe_classification(
                        topic_present=topic_present,
                        endpoint_inventory=endpoint_inventory,
                        probe=probe,
                        sample_timing=sample_timing,
                        observed=observed,
                        managed_runtime_started=managed_started,
                    ),
                )

    def test_sample_timing_prefers_observed_reliable_attempt(self) -> None:
        """RELIABLE 命中样本时，顶层 sample_timing 必须跟随成功 attempt。"""
        timing = HELPER.sample_timing_from_probe(
            {
                "attempts": [
                    {
                        "label": "rclpy_best_effort_once",
                        "observed": False,
                        "sample_timing": {"sample_count": 0, "timed_out": True, "probe_window_sec": 18.0},
                    },
                    {
                        "label": "rclpy_reliable_once",
                        "observed": True,
                        "sample_timing": {
                            "sample_count": 1,
                            "timed_out": False,
                            "probe_window_sec": 18.0,
                            "first_sample_latency_ms": 173,
                        },
                    },
                ],
                "best_attempt": {
                    "label": "rclpy_reliable_once",
                    "sample_timing": {
                        "sample_count": 1,
                        "timed_out": False,
                        "probe_window_sec": 18.0,
                        "first_sample_latency_ms": 173,
                    },
                },
            },
            observed=True,
        )

        self.assertEqual(1, timing["sample_count"])
        self.assertFalse(timing["timed_out"])
        self.assertEqual(173, timing["first_sample_latency_ms"])

    def test_rclpy_scan_once_propagates_outer_timeout_into_sample_timing(self) -> None:
        """outer timeout 已命中时，attempt.sample_timing.timed_out 也必须保持为 true。"""
        args = HELPER.parse_args([])
        child_payload = {
            "command": "rclpy reliable_volatile once /scan",
            "ok": False,
            "timed_out": False,
            "boundary": "rclpy_scan_child_failed",
            "stdout": "",
            "stderr": "",
            "frame_observed": False,
            "frame_stamp": None,
            "fallback_boundary": "cli_fallback_allowed_after_child_rclpy_probe",
            "import_check": {"attempted": True, "ok": True, "classification": None, "error": None},
            "environment_check": {"ros_setup": "/opt/ros/humble/setup.bash"},
            "endpoint_inventory": {"inventory_observed": True, "publisher_count": 1, "subscriber_count": 1},
            "child_runtime": {
                "import_ok": True,
                "node_created": True,
                "subscription_created": True,
                "sample_wait_started": True,
                "timeout_boundary_ms": 1_780_000_018_010,
            },
            "requested_qos_profile": {
                "profile": "reliable_volatile",
                "history": "KEEP_LAST",
                "depth": 5,
                "reliability": "RELIABLE",
                "durability": "VOLATILE",
            },
            "sample_timing": {
                "probe_window_sec": 18.0,
                "sample_wait_started_at_ms": 1_780_000_000_010,
                "sample_wait_finished_at_ms": 1_780_000_018_040,
                "timeout_boundary_ms": 1_780_000_018_010,
                "first_sample_latency_ms": None,
                "sample_count": 0,
                "last_sample_stamp": None,
                "last_sample_received_at_ms": None,
                "timed_out": False,
            },
        }
        run_result = {
            "command": "python3 - <<'PY'",
            "executed": True,
            "ok": False,
            "returncode": 4,
            "started_at_ms": 1_780_000_000_000,
            "finished_at_ms": 1_780_000_018_100,
            "timed_out": True,
            "elapsed_ms": 18_100,
            "stdout": "\n".join(["boot line", json.dumps(child_payload, ensure_ascii=False)]),
            "stderr": "ExternalShutdownException",
            "error": None,
        }

        with mock.patch.object(HELPER, "run_ros", return_value=run_result):
            result = HELPER.rclpy_scan_once(
                args,
                timeout_s=18.0,
                attempt_label="rclpy_reliable_once",
                profile_label="reliable_volatile",
                reliability="RELIABLE",
                durability="VOLATILE",
            )

        self.assertTrue(result["timed_out"])
        self.assertEqual("rclpy_scan_child_timeout_after_outer_timeout", result["boundary"])
        self.assertTrue(result["sample_timing"]["timed_out"])
        self.assertEqual(1_780_000_000_010, result["sample_timing"]["sample_wait_started_at_ms"])
        self.assertEqual(1_780_000_018_010, result["sample_timing"]["timeout_boundary_ms"])

    def test_signal_root_cause_avoids_fake_no_publishers_when_endpoint_inventory_missing(self) -> None:
        """rclpy graph probe 缺失时，不能把默认 0 publisher 误写成真实无 publisher。"""
        reason = HELPER.signal_root_cause_reason(
            {
                "topic_present": True,
                "endpoint_inventory_observed": False,
                "publishers": {"count": 0, "nodes": []},
                "probe": {
                    "timed_out": False,
                    "best_attempt": {
                        "source": "rclpy_subscription",
                        "error": {"type": "ImportError", "message": "missing librcl_action.so"},
                    },
                },
                "freshness": {"status": "not_observed"},
            },
            "/scan",
            "/scan_once_not_observed",
        )

        self.assertEqual("/scan_rclpy_probe_failed", reason)

    def test_signal_root_cause_prefers_rclpy_import_detail(self) -> None:
        """rclpy child probe 的 import 分类必须进入可行动 root cause。"""
        reason = HELPER.signal_root_cause_reason(
            {
                "topic_present": True,
                "endpoint_inventory_observed": False,
                "publishers": {"count": 0, "nodes": []},
                "probe": {
                    "timed_out": False,
                    "best_attempt": {
                        "source": "rclpy_subscription",
                        "runtime": "ros_sourced_child_python",
                        "error": {"type": "ImportError", "message": "missing librcl_action.so"},
                        "import_check": {
                            "attempted": True,
                            "ok": False,
                            "classification": "missing_shared_library",
                        },
                    },
                },
                "freshness": {"status": "not_observed"},
            },
            "/scan",
            "/scan_once_not_observed",
        )

        self.assertEqual("/scan_rclpy_import_failed_missing_shared_library", reason)

    def test_signal_root_cause_reports_child_timeout_after_import(self) -> None:
        """rclpy import 已成功时，child timeout 要和 import failure 分开。"""
        reason = HELPER.signal_root_cause_reason(
            {
                "topic_present": True,
                "endpoint_inventory_observed": False,
                "publishers": {"count": 0, "nodes": []},
                "probe": {
                    "timed_out": False,
                    "best_attempt": {
                        "source": "rclpy_subscription",
                        "runtime": "ros_sourced_child_python",
                        "error": {"type": "ExternalShutdownException", "message": ""},
                        "import_check": {
                            "attempted": True,
                            "ok": True,
                            "classification": None,
                        },
                        "runtime_diagnostics": {
                            "child_process": {"timed_out": True, "elapsed_ms": 6287},
                        },
                    },
                },
                "freshness": {"status": "not_observed"},
            },
            "/scan",
            "/scan_once_not_observed",
        )

        self.assertEqual("/scan_rclpy_child_timeout_after_import", reason)

    def test_tf_source_freshness_separates_dynamic_and_static_edges(self) -> None:
        """dynamic odom->base_link 与 static base_link->laser_frame 要分层，map->odom 缺失继续 fail-closed。"""
        args = HELPER.parse_args([])
        amcl_probe = {
            "param_probe_ok": True,
            "node_info_observed": True,
            "params": {
                "tf_broadcast": True,
                "global_frame_id": "map",
                "odom_frame_id": "odom",
                "base_frame_id": "base_link",
            },
            "topic_types": {"/tf": "tf2_msgs/msg/TFMessage", "/tf_static": "tf2_msgs/msg/TFMessage"},
            "dynamic_edges": [{"parent": "odom", "child": "base_link", "topic": "/tf"}],
            "static_edges": [{"parent": "base_link", "child": "laser_frame", "topic": "/tf_static"}],
            "command_statuses": {"rclpy_graph": 0, "tf": 0, "tf_static": 0},
            "boundary": "rclpy_amcl_params_graph_tf_probe_observed",
        }
        source = HELPER.build_tf_source_diagnostics(
            args,
            {"stdout": "", "ok": True},
            amcl_pose_result={"stdout": "header:\n  frame_id: map\n"},
            amcl_probe=amcl_probe,
        )
        freshness = HELPER.build_tf_source_freshness(
            args=args,
            generated_at_ms=1_780_000_000_000,
            tf_source_diagnostics=source,
        )

        self.assertFalse(freshness["edges"]["map_to_odom"]["observed"])
        self.assertEqual("missing", freshness["edges"]["map_to_odom"]["source_class"])
        self.assertTrue(freshness["edges"]["odom_to_base_link"]["observed"])
        self.assertEqual("dynamic", freshness["edges"]["odom_to_base_link"]["source_class"])
        self.assertTrue(freshness["edges"]["base_link_to_laser_frame"]["observed"])
        self.assertEqual("static", freshness["edges"]["base_link_to_laser_frame"]["source_class"])
        self.assertEqual(
            "static_source_observed_not_age_gated",
            freshness["edges"]["base_link_to_laser_frame"]["freshness"]["status"],
        )
        self.assertEqual(
            "map_to_odom_dynamic_source_missing",
            HELPER.tf_edge_root_cause_reason(freshness, "map_to_odom", "map_to_odom_not_observed"),
        )

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

    def test_collect_amcl_rclpy_probe_falls_back_to_cli_inventory(self) -> None:
        """rclpy import 失败时，artifact 仍必须带回 `/tf`、`/tf_static` 与 `/amcl` 的 CLI inventory。"""
        args = HELPER.parse_args([])
        with mock.patch.dict(sys.modules, {"rclpy": None}):
            with mock.patch.object(
                HELPER,
                "collect_amcl_cli_probe",
                return_value={
                    "executed": True,
                    "ok": True,
                    "param_probe_ok": False,
                    "node_info_observed": True,
                    "tf_inventory_observed": True,
                    "params": {},
                    "publishers": [{"topic": "/tf", "type": "tf2_msgs/msg/TFMessage"}],
                    "subscribers": [{"topic": "/scan", "type": "sensor_msgs/msg/LaserScan"}],
                    "topic_types": {
                        "/tf": "tf2_msgs/msg/TFMessage",
                        "/tf_static": "tf2_msgs/msg/TFMessage",
                    },
                    "topic_endpoint_summaries": {
                        "/tf": {
                            "publishers": [],
                            "subscribers": [],
                            "publisher_count": 1,
                            "subscriber_count": 0,
                            "inventory_observed": True,
                            "error": None,
                        },
                        "/tf_static": {
                            "publishers": [],
                            "subscribers": [],
                            "publisher_count": 1,
                            "subscriber_count": 0,
                            "inventory_observed": True,
                            "error": None,
                        },
                    },
                    "dynamic_edges": [],
                    "static_edges": [],
                    "dynamic_transforms": [],
                    "static_transforms": [],
                    "command_statuses": {"rclpy_graph": 0, "tf": 0, "tf_static": 0},
                    "commands": {},
                    "error": None,
                    "elapsed_ms": 900,
                    "boundary": "cli_amcl_inventory_observed_topic_list_amcl_node_info_tf_info_tf_static_info",
                    "fallback_used": True,
                    "fallback_boundary": "cli_amcl_inventory_observed_topic_list_amcl_node_info_tf_info_tf_static_info",
                    "param_probe_boundary": "cli_amcl_param_probe_unavailable_tf_broadcast_failed_global_frame_id_failed_odom_frame_id_failed_base_frame_id_failed",
                    "probe_mode": "ros2_cli_fallback",
                },
            ):
                result = HELPER.collect_amcl_rclpy_probe(args, timeout_s=1.0)

        self.assertTrue(result["fallback_used"])
        self.assertEqual("ros2_cli_fallback", result["probe_mode"])
        self.assertEqual("rclpy_amcl_probe_failed", result["rclpy_boundary"])
        self.assertEqual("environment_not_sourced", result["rclpy_import_failure_classification"])
        self.assertTrue(result["node_info_observed"])
        self.assertTrue(result["tf_inventory_observed"])
        self.assertIn("/tf", result["topic_types"])
        self.assertIn("/tf_static", result["topic_types"])

    def test_build_tf_source_diagnostics_uses_cli_fallback_topic_inventory(self) -> None:
        """CLI fallback 只要带回 topic inventory，就不应再把 root cause 固定写成 `/tf_topic_missing`。"""
        args = HELPER.parse_args([])
        amcl_probe = {
            "param_probe_ok": False,
            "node_info_observed": True,
            "params": {},
            "topic_types": {
                "/tf": "tf2_msgs/msg/TFMessage",
                "/tf_static": "tf2_msgs/msg/TFMessage",
            },
            "topic_endpoint_summaries": {
                "/tf": {
                    "publishers": [],
                    "subscribers": [],
                    "publisher_count": 1,
                    "subscriber_count": 0,
                    "inventory_observed": True,
                    "error": None,
                },
                "/tf_static": {
                    "publishers": [],
                    "subscribers": [],
                    "publisher_count": 1,
                    "subscriber_count": 0,
                    "inventory_observed": True,
                    "error": None,
                },
                "/initialpose": {
                    "publishers": [],
                    "subscribers": [
                        {
                            "node_name": "amcl",
                            "node_namespace": "/",
                            "topic_type": "geometry_msgs/msg/PoseWithCovarianceStamped",
                        }
                    ],
                    "publisher_count": 0,
                    "subscriber_count": 1,
                    "inventory_observed": True,
                    "error": None,
                },
            },
            "static_edges": [],
            "dynamic_edges": [],
            "command_statuses": {"rclpy_graph": 0, "tf": 0, "tf_static": 0},
            "boundary": "cli_amcl_inventory_observed_topic_list_amcl_node_info_tf_info_tf_static_info",
            "fallback_used": True,
            "probe_mode": "ros2_cli_fallback",
        }

        source = HELPER.build_tf_source_diagnostics(
            args,
            {"stdout": "", "ok": False},
            amcl_pose_result={"stdout": "header:\n  frame_id: map\n"},
            amcl_probe=amcl_probe,
        )

        self.assertTrue(source["tf_topics_observed"]["/tf"])
        self.assertFalse(source["tf_static_observed"])
        self.assertEqual("amcl_param_probe_failed", source["amcl_tf_root_cause"])
        self.assertEqual(1, source["topic_endpoint_summaries"]["/initialpose"]["subscriber_count"])
        self.assertTrue(HELPER.build_initialpose_subscriber_audit(source)["amcl_subscriber_active"])

    def test_sourced_rclpy_probe_parses_child_json_without_cli_fallback(self) -> None:
        """SSH parent 未 source 时应使用单个 sourced child，避免串行 CLI 吞掉 90 秒窗口。"""
        child_payload = {
            "executed": True,
            "ok": True,
            "param_probe_ok": True,
            "node_info_observed": True,
            "tf_inventory_observed": True,
            "params": {"tf_broadcast": True},
            "publishers": [{"topic": "/tf", "type": "tf2_msgs/msg/TFMessage"}],
            "subscribers": [],
            "topic_types": {"/tf": "tf2_msgs/msg/TFMessage"},
            "topic_endpoint_summaries": {},
            "dynamic_edges": [{"parent": "map", "child": "odom", "topic": "/tf"}],
            "static_edges": [],
            "dynamic_transforms": [],
            "static_transforms": [],
            "command_statuses": {"rclpy_graph": 0, "tf": 0, "tf_static": 124},
            "boundary": "rclpy_amcl_params_graph_tf_probe_observed",
        }
        with mock.patch.object(
            HELPER,
            "run_ros",
            return_value={
                "executed": True,
                "ok": True,
                "returncode": 0,
                "elapsed_ms": 1200,
                "timed_out": False,
                "stdout": json.dumps(child_payload) + "\n",
                "stderr": "",
            },
        ) as run_mock:
            result = HELPER.collect_amcl_sourced_rclpy_probe(HELPER.parse_args([]), timeout_s=4.0)

        self.assertEqual("sourced_rclpy_child", result["probe_mode"])
        self.assertEqual([{"parent": "map", "child": "odom", "topic": "/tf"}], result["dynamic_edges"])
        self.assertTrue(result["child_command"]["ok"])
        self.assertIn("--tf-source-child-probe", run_mock.call_args.args[1])

    def test_tf_probe_uses_wider_echo_window_after_source_probe(self) -> None:
        """现场 ros2 CLI 启动慢，四段 fallback tf2_echo 必须使用统一宽窗口。"""
        text = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("collect_amcl_sourced_rclpy_probe(args, timeout_s=4.0)", text)
        self.assertIn("--tf-source-child-probe", text)
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
        self.assertFalse(payload["path_generation_attempted"])
        self.assertFalse(payload["path_generated"])
        self.assertIn("/dev/ttyS5", proof["blocked_devices_not_opened"])

    def test_partial_closeout_keeps_amcl_root_cause_ahead_of_sigterm(self) -> None:
        """SIGTERM 只能说明 helper 中断，不能遮住已经观测到的 AMCL/TF 根因。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "localization_reset_latest.json"
            args = HELPER.parse_args(["--output", str(output), "--managed-runtime-opt-in", "--initialpose-opt-in"])
            writer = HELPER.PhaseArtifactWriter(args, HELPER.now_ms())

            writer.record_phase(
                "amcl_pose_probe",
                ok=False,
                root_cause={"layer": "AMCL localization", "reason": "/amcl_pose_probe_timeout"},
            )
            writer.record_phase(
                "interrupted",
                ok=False,
                root_cause={"layer": "helper process", "reason": "sigterm_before_final_artifact"},
            )
            payload = json.loads(output.read_text(encoding="utf-8"))

        proof = payload["proof"]
        self.assertEqual("partial_runtime_in_progress", payload["status"])
        self.assertEqual("/amcl_pose_probe_timeout", proof["artifact_closeout"]["primary_root_cause"]["reason"])
        self.assertTrue(proof["artifact_closeout"]["interruption_does_not_override_primary_root_cause"])
        self.assertEqual("sigterm_before_final_artifact", proof["artifact_closeout"]["signal_root_causes"][0]["reason"])
        self.assertIn("amcl_readiness_summary", proof)
        self.assertIn("tf_readiness_summary", proof)
        self.assertIn("path_generation_gate", proof)
        self.assertFalse(proof["safe_to_control"])
        self.assertFalse(proof["robot_control_executed"])
        self.assertFalse(proof["route_execution_success"])

    def test_amcl_summary_splits_lifecycle_from_pose_sample(self) -> None:
        """AMCL lifecycle active 不能被误读成 `/amcl_pose` 已经采样成功。"""
        proof = {
            "map_server_active": True,
            "amcl_active": True,
            "initialpose_publish_attempted": True,
            "initialpose_published": True,
            "localization_signal_freshness": {
                "/amcl_pose": {
                    "topic_type": "geometry_msgs/msg/PoseWithCovarianceStamped",
                    "topic_present": True,
                    "publishers": {"count": 1, "nodes": [{"node_name": "amcl"}]},
                    "subscribers": {"count": 0, "nodes": []},
                    "probe": {
                        "executed": True,
                        "observed": False,
                        "timed_out": True,
                        "elapsed_ms": 10002,
                        "timeout_s": 10.0,
                    },
                    "timestamp": {"parsed": False, "reason": "stamp_not_found"},
                    "freshness": {"status": "not_observed"},
                }
            },
            "map_lifecycle_preflight": {
                "amcl_active": True,
                "map_server_active": True,
                "classification": "map_lifecycle_preflight_all_active",
                "results": {"amcl": {"ok": True, "boundary": "active"}},
            },
        }

        summary = HELPER.build_amcl_readiness_summary(proof)

        self.assertTrue(summary["amcl_lifecycle"]["active"])
        self.assertFalse(summary["amcl_pose_sample"]["observed"])
        self.assertEqual("geometry_msgs/msg/PoseWithCovarianceStamped", summary["amcl_pose_sample"]["topic_type"])
        self.assertEqual(1, summary["amcl_pose_sample"]["publishers"]["count"])
        self.assertTrue(summary["amcl_pose_sample"]["sample_timing"]["timed_out"])
        self.assertEqual("/amcl_pose_probe_timeout", summary["blocked_reason"])
        self.assertFalse(summary["ready"])

    def test_strict_managed_localization_requires_outputs_without_publishing_initialpose(self) -> None:
        """禁发 initialpose 时仍要验收 pose/map->odom，并把缺初值写成最窄 blocker。"""
        causes = HELPER.classify_root_causes(
            map_inputs={"root_causes": []},
            ros2_ok=True,
            board_source_preflight={"ros2_cli_ok": True, "rclpy_import_ok": True},
            map_lifecycle_preflight={"root_causes": []},
            packages={package: True for package in HELPER.EXPECTED_PACKAGES},
            lifecycle_active={"map_server": True, "amcl": True},
            lifecycle_results={},
            scan_once_observed=True,
            map_once_observed=True,
            amcl_pose_observed=False,
            localization_tf_observed={"map_to_odom": False, "map_to_base_link": False},
            tf_chain_observed={
                "map_to_odom": False,
                "odom_to_base_link": True,
                "base_link_to_laser_frame": True,
                "map_to_base_link": False,
            },
            tf_failure_classification={
                "map_to_base_link": "blocked_by_missing_map_to_odom",
                "blocking_segment": "map_to_odom",
                "reason": "amcl_map_to_odom_tf_not_observed_on_tf",
            },
            initialpose_enabled=False,
            initialpose_publish={"ok": False, "boundary": "default_read_only_no_initialpose_publish"},
            localization_outputs_required=True,
            localization_signal_freshness={
                "/amcl_pose": {
                    "topic_present": True,
                    "endpoint_inventory_observed": True,
                    "publishers": {"count": 1},
                    "probe": {"executed": True, "observed": False},
                    "freshness": {"status": "not_observed"},
                }
            },
            tf_source_freshness={
                "edges": {
                    "map_to_odom": {
                        "observed": False,
                        "source_class": "missing",
                        "required_source_class": "dynamic",
                    }
                }
            },
        )
        reasons = [cause["reason"] for cause in causes]

        self.assertEqual(
            "amcl_requires_initial_pose_but_initialpose_forbidden_in_current_safety_scope",
            reasons[0],
        )
        self.assertIn("/amcl_pose_once_not_observed", reasons)
        self.assertIn("map_to_odom_dynamic_source_missing", reasons)
        self.assertNotIn("default_read_only_no_initialpose_publish", reasons)

    def test_tf_summary_exposes_dynamic_map_odom_and_downstream_map_base(self) -> None:
        """TF summary 必须把 dynamic map->odom 缺失和 downstream map->base_link 阻塞拆开。"""
        proof = {
            "tf_source_freshness": {
                "edges": {
                    "map_to_odom": {
                        "observed": False,
                        "source_class": "missing",
                        "required_source_class": "dynamic",
                        "dynamic_source_observed": False,
                        "static_source_observed": False,
                        "freshness": {"status": "not_observed"},
                    },
                    "odom_to_base_link": {
                        "observed": True,
                        "source_class": "dynamic",
                        "required_source_class": None,
                        "source_topic": "/tf",
                        "dynamic_source_observed": True,
                        "static_source_observed": False,
                        "freshness": {"status": "fresh"},
                    },
                }
            },
            "tf_chain_observed": {
                "map_to_odom": False,
                "odom_to_base_link": True,
                "base_link_to_laser_frame": True,
                "map_to_base_link": False,
            },
            "tf_chain_diagnostics": {
                "pairs": {
                    "map_to_odom": {"failure_reason": "tf2_empty_output_or_timing", "boundary": "source_inventory"},
                    "odom_to_base_link": {"failure_reason": "observed", "boundary": "source_inventory"},
                }
            },
            "tf_failure_classification": {
                "map_to_base_link": "blocked_by_missing_map_to_odom",
                "blocking_segment": "map_to_odom",
                "reason": "map_to_odom_dynamic_source_missing",
            },
        }

        summary = HELPER.build_tf_readiness_summary(proof)

        self.assertFalse(summary["map_to_odom_dynamic"]["observed"])
        self.assertEqual("dynamic", summary["map_to_odom_dynamic"]["required_source_class"])
        self.assertTrue(summary["odom_to_base_link"]["observed"])
        self.assertFalse(summary["map_to_base_link"]["observed"])
        self.assertEqual("map_to_odom", summary["map_to_base_link"]["blocking_segment"])
        self.assertEqual("map_to_odom_dynamic_source_missing", summary["map_to_base_link"]["blocked_reason"])
        self.assertFalse(summary["ready"])

    def test_lifecycle_summary_splits_timeout_from_inactive_stdout(self) -> None:
        """lifecycle preflight 必须区分命令超时和 stdout 明确 inactive。"""
        preflight = HELPER.build_map_lifecycle_preflight(
            ros2_cli_ok=True,
            lifecycle_active={"map_server": False, "amcl": False},
            lifecycle_results={
                "map_server": {
                    "executed": True,
                    "ok": False,
                    "returncode": 124,
                    "timed_out": True,
                    "stdout": "",
                    "stderr": "",
                    "command": "ros2 lifecycle get /map_server",
                },
                "amcl": {
                    "executed": True,
                    "ok": True,
                    "returncode": 0,
                    "timed_out": False,
                    "stdout": "inactive [2]\n",
                    "stderr": "",
                    "command": "ros2 lifecycle get /amcl",
                },
            },
        )

        self.assertEqual("map_lifecycle_preflight_map_server_and_amcl_inactive", preflight["classification"])
        self.assertEqual("command_timeout", preflight["node_summaries"]["map_server"]["failure_mode"])
        self.assertEqual("map_server_lifecycle_command_timeout", preflight["blocking_reasons"]["map_server"])
        self.assertEqual("inactive_stdout", preflight["node_summaries"]["amcl"]["failure_mode"])
        self.assertEqual("amcl_lifecycle_inactive_stdout", preflight["blocking_reasons"]["amcl"])

    def test_lifecycle_checks_records_budget_retry_and_graph_visible_timeout(self) -> None:
        """lifecycle CLI timeout 必须保留 graph 可见、first/retry 预算和最终分类。"""
        args = HELPER.parse_args(["--timeout-s", "18"])
        graph_result = {
            "command": "ros2 node list",
            "executed": True,
            "ok": True,
            "returncode": 0,
            "timed_out": False,
            "timeout_s": 8.0,
            "elapsed_ms": 120,
            "stdout": "/map_server\n",
            "stderr": "",
        }
        first_timeout = {
            "command": "ros2 lifecycle get /map_server",
            "executed": True,
            "ok": False,
            "returncode": None,
            "timed_out": True,
            "timeout_s": 10.0,
            "elapsed_ms": 10050,
            "stdout": "",
            "stderr": "",
        }
        retry_timeout = {
            "command": "ros2 lifecycle get /map_server",
            "executed": True,
            "ok": False,
            "returncode": None,
            "timed_out": True,
            "timeout_s": 18.0,
            "elapsed_ms": 18050,
            "stdout": "",
            "stderr": "",
        }

        with mock.patch.object(
            HELPER,
            "run_ros",
            side_effect=[graph_result, first_timeout, retry_timeout],
        ) as run_mock:
            active, results = HELPER.lifecycle_checks(args, {"map_server": "/map_server"})

        self.assertFalse(active["map_server"])
        summary = results["map_server"]["command_summary"]
        self.assertEqual("trashbot.o10.lifecycle_cli_budget_recovery.v1", summary["schema"])
        self.assertEqual("lifecycle_cli_budget_recovery", summary["strategy"])
        self.assertEqual("ros2 lifecycle get /map_server", summary["command"])
        self.assertTrue(summary["graph_node_visible"])
        self.assertEqual("first_attempt", summary["first_attempt"]["label"])
        self.assertEqual(10.0, summary["first_attempt"]["timeout_s"])
        self.assertEqual("retry_attempt", summary["retry_attempt"]["label"])
        self.assertEqual(18.0, summary["retry_attempt"]["timeout_s"])
        self.assertEqual("graph ok but lifecycle timeout", summary["classification"])
        self.assertEqual("inspect_lifecycle_manager_or_node_state_after_graph_visible_timeout", summary["next_step"])
        preflight = HELPER.build_map_lifecycle_preflight(
            ros2_cli_ok=True,
            lifecycle_active=active,
            lifecycle_results=results,
        )
        self.assertEqual("map_server_lifecycle_command_timeout", preflight["blocking_reasons"]["map_server"])
        self.assertEqual("command_timeout", preflight["node_summaries"]["map_server"]["failure_mode"])
        self.assertIn("map_server", preflight["lifecycle_cli_budget_recovery"])
        self.assertEqual(3, run_mock.call_count)
        self.assertEqual(HELPER.LIFECYCLE_GRAPH_VISIBILITY_TIMEOUT_S, run_mock.call_args_list[0].kwargs["timeout_s"])
        self.assertEqual(HELPER.LIFECYCLE_CLI_FIRST_ATTEMPT_TIMEOUT_S, run_mock.call_args_list[1].kwargs["timeout_s"])
        self.assertEqual(18.0, run_mock.call_args_list[2].kwargs["timeout_s"])

    def test_lifecycle_checks_skips_retry_after_active_first_attempt(self) -> None:
        """first attempt 已 active 时不再重复打 lifecycle CLI，减少现场 proof 窗口消耗。"""
        args = HELPER.parse_args(["--timeout-s", "18"])
        graph_result = {
            "command": "ros2 node list",
            "executed": True,
            "ok": True,
            "returncode": 0,
            "timed_out": False,
            "timeout_s": 8.0,
            "elapsed_ms": 120,
            "stdout": "/amcl\n",
            "stderr": "",
        }
        active_result = {
            "command": "ros2 lifecycle get /amcl",
            "executed": True,
            "ok": True,
            "returncode": 0,
            "timed_out": False,
            "timeout_s": 10.0,
            "elapsed_ms": 340,
            "stdout": "active [3]\n",
            "stderr": "",
        }

        with mock.patch.object(HELPER, "run_ros", side_effect=[graph_result, active_result]) as run_mock:
            active, results = HELPER.lifecycle_checks(args, {"amcl": "/amcl"})

        self.assertTrue(active["amcl"])
        summary = results["amcl"]["command_summary"]
        self.assertTrue(summary["clean"])
        self.assertEqual("active", summary["classification"])
        self.assertFalse(summary["retry_attempt"]["executed"])
        self.assertEqual("retry skipped after active first attempt", summary["retry_attempt"]["classification"])
        self.assertEqual(2, run_mock.call_count)

    def test_lifecycle_active_stdout_wins_even_when_process_times_out(self) -> None:
        """stdout 已出现 `active [3]` 时必须标成 active，同时保留 command timeout 事实。"""
        result = {
            "command": "ros2 lifecycle get /amcl",
            "executed": True,
            "ok": False,
            "returncode": None,
            "timed_out": True,
            "timeout_s": 18.0,
            "elapsed_ms": 18088,
            "stdout": "RTPS warning before state\nactive [3]\n",
            "stderr": "",
        }

        self.assertTrue(HELPER.parse_lifecycle_active(result))
        summary = HELPER.lifecycle_attempt_summary(
            label="retry_attempt",
            node_key="amcl",
            node_name="/amcl",
            result=result,
            graph_node_visible=False,
        )

        self.assertTrue(summary["active"])
        self.assertTrue(summary["timed_out"])
        self.assertEqual("active", summary["classification"])

    def _visibility_attempt(
        self,
        *,
        label: str,
        node_key: str,
        node_name: str,
        stdout: str = "",
        stderr: str = "",
        returncode: int | None = 0,
        timed_out: bool = False,
        timeout_s: float = 10.0,
        elapsed_ms: int = 120,
        graph_node_visible: bool = False,
    ) -> dict[str, object]:
        """构造 lifecycle attempt summary；复用正式 parser，避免测试自造 active 规则。"""
        result = {
            "command": f"ros2 lifecycle get {node_name}",
            "executed": True,
            "ok": returncode == 0 and not timed_out,
            "returncode": returncode,
            "timed_out": timed_out,
            "timeout_s": timeout_s,
            "elapsed_ms": elapsed_ms,
            "stdout": stdout,
            "stderr": stderr,
        }
        return HELPER.lifecycle_attempt_summary(
            label=label,
            node_key=node_key,
            node_name=node_name,
            result=result,
            graph_node_visible=graph_node_visible,
        )

    def _visibility_command_summary(
        self,
        *,
        node_key: str,
        node_name: str,
        graph_nodes: list[str],
        first: dict[str, object],
        retry: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """最小化复刻正式 lifecycle command summary，专注验证 09-54 分类器。"""
        visible = node_name in graph_nodes
        retry_payload = retry or {
            "label": "retry_attempt",
            "node_key": node_key,
            "node": node_name,
            "command": f"ros2 lifecycle get {node_name}",
            "executed": False,
            "ok": bool(first.get("active")),
            "active": bool(first.get("active")),
            "classification": "retry skipped after active first attempt",
            "timeout_s": 18.0,
            "elapsed_ms": 0,
            "returncode": None,
            "timed_out": False,
            "stdout": "",
            "stderr": "",
            "error": None,
        }
        final = retry_payload if retry_payload.get("executed") else first
        return {
            "schema": "trashbot.o10.lifecycle_cli_budget_recovery.v1",
            "strategy": "lifecycle_cli_budget_recovery",
            "node_key": node_key,
            "node": node_name,
            "command": f"ros2 lifecycle get {node_name}",
            "graph_visibility": {
                "schema": "trashbot.o10.lifecycle_cli_graph_visibility.v1",
                "command": "ros2 node list",
                "executed": True,
                "ok": True,
                "timed_out": False,
                "timeout_s": 8.0,
                "elapsed_ms": 120,
                "observed_node_names": graph_nodes,
                "target_nodes": {node_key: {"node": node_name, "visible": visible}},
            },
            "graph_node_visible": visible,
            "first_attempt": first,
            "retry_attempt": retry_payload,
            "attempts": [first] + ([retry_payload] if retry_payload.get("executed") else []),
            "final_attempt_label": str(final.get("label")),
            "classification": str(final.get("classification")),
            "clean": bool(final.get("active")),
            "timeout_budget_s": {"first_attempt": 10.0, "retry_attempt": 18.0},
            "next_step": "lifecycle_readback_clean_continue_downstream_no_motion"
            if final.get("active")
            else "inspect_lifecycle_manager_or_node_state_after_graph_visible_timeout"
            if visible and final.get("timed_out")
            else "inspect_ros2_cli_budget_daemon_or_process_graph",
        }

    def _map_server_visibility_proof(
        self,
        *,
        graph_nodes: list[str],
        map_first: dict[str, object],
        map_retry: dict[str, object] | None = None,
        amcl_first: dict[str, object] | None = None,
        amcl_retry: dict[str, object] | None = None,
        graph_root_classification: str = "root_cause_unclassified_after_probe",
        managed_requested: bool = False,
        managed_started: bool = False,
        startup_error: dict[str, object] | None = None,
        graph_timed_out: bool = False,
    ) -> dict[str, object]:
        """生成 summary 所需 proof 子集；危险字段始终 false，锁住 no-motion 合同。"""
        if amcl_first is None:
            amcl_first = self._visibility_attempt(
                label="first_attempt",
                node_key="amcl",
                node_name="/amcl",
                stdout="active [3]\n",
                graph_node_visible="/amcl" in graph_nodes,
            )
        map_summary = self._visibility_command_summary(
            node_key="map_server",
            node_name="/map_server",
            graph_nodes=graph_nodes,
            first=map_first,
            retry=map_retry,
        )
        amcl_summary = self._visibility_command_summary(
            node_key="amcl",
            node_name="/amcl",
            graph_nodes=graph_nodes,
            first=amcl_first,
            retry=amcl_retry,
        )
        probe = {
            "command": "ros2 node list",
            "executed": True,
            "ok": not graph_timed_out,
            "returncode": None if graph_timed_out else 0,
            "timed_out": graph_timed_out,
            "timeout_s": 2.5,
            "elapsed_ms": 2500 if graph_timed_out else 120,
            "boundary": "ros2_node_list_timeout" if graph_timed_out else "ros2_node_list_ok",
            "stdout": "\n".join(graph_nodes),
            "stderr": "",
        }
        map_active = bool(map_summary["clean"])
        amcl_active = bool(amcl_summary["clean"])
        return {
            "board_source_preflight": {
                "classification": "board_source_preflight_ready",
                "lightweight_cli_ready": True,
                "cli_ready": True,
                "runtime_ready": True,
            },
            "map_lifecycle_preflight": {
                "classification": "map_lifecycle_preflight_all_active"
                if map_active and amcl_active
                else "map_lifecycle_preflight_map_server_inactive",
                "map_server_active": map_active,
                "amcl_active": amcl_active,
                "command_summaries": {"map_server": map_summary, "amcl": amcl_summary},
                "lifecycle_cli_budget_recovery": {"map_server": map_summary, "amcl": amcl_summary},
                "results": {},
                "blocking_reasons": {} if map_active else {"map_server": "map_server_lifecycle_command_failed"},
            },
            "map_server_active": map_active,
            "amcl_active": amcl_active,
            "managed_runtime_requested": managed_requested,
            "managed_runtime_started": managed_started,
            "managed_runtime_boundary": "managed_runtime_started" if managed_started else "managed_runtime_not_started",
            "managed_runtime_process_group": 1234 if managed_started else None,
            "managed_runtime_wait_result": {
                "ok": False,
                "reason": "ros2_node_list_timeout" if graph_timed_out else "managed_runtime_required_nodes_not_observed",
                "observed_node_names": graph_nodes,
            },
            "ros2_graph_timeout_root_cause": {
                "classification": graph_root_classification,
                "primary_candidate": {"classification": graph_root_classification, "reason": "fixture"},
                "probes": {
                    "ros2_node_list": probe,
                    "ros2_node_list_no_daemon": {**probe, "command": "ros2 node list --no-daemon"},
                    "ros2_daemon_status": {**probe, "command": "ros2 daemon status"},
                    "ros2_topic_list": {**probe, "command": "ros2 topic list"},
                    "managed_process": {
                        "managed_runtime_started": managed_started,
                        "process_alive": True if managed_started else False,
                        "process_returncode": None if managed_started else 1,
                        "missing_expected_nodes": [node for node in ["/map_server", "/amcl"] if node not in graph_nodes],
                        "lifecycle_probe_status": "executed_or_partially_observed" if graph_nodes else "not_requested",
                        "lifecycle_probe_skipped": {},
                        "log_tail": "",
                    },
                },
                "daemon_dds_split": {
                    "primary_candidate": {
                        "candidate": "dds_discovery_or_domain_mismatch"
                        if graph_root_classification == "ros2_daemon_or_dds_graph_discovery_timeout"
                        else "graph_command_budget_insufficient",
                        "reason": "fixture",
                    },
                    "daemon_safe_graph_readback": {"graph_readback": {"node_names": graph_nodes}},
                },
            },
            "commands": {
                "managed_runtime": {
                    "requested": managed_requested,
                    "started": managed_started,
                    "boundary": "managed_runtime_started" if managed_started else "managed_runtime_not_started",
                    "startup_error": startup_error,
                    "wait_result": {"observed_node_names": graph_nodes},
                }
            },
            "downstream_recovery_summary": {"downstream_probes_allowed": map_active and amcl_active},
            "path_generation_attempted": False,
            "path_generated": False,
            **HELPER.safety_flags(),
        }

    def _with_managed_map_yaml(self, proof: dict[str, object]) -> dict[str, object]:
        """presence recovery 测试显式给出 map yaml 已解析，避免本机不存在 /root 路径影响分类。"""
        proof["managed_runtime_map_yaml"] = "/root/rober/onboard/runtime/maps/trashbot_map.yaml"
        proof["managed_runtime_map_yaml_source"] = "explicit_cli_managed_map_yaml"
        proof["managed_runtime_map_analysis"] = {
            "executed": True,
            "ok": True,
            "image": "/root/rober/onboard/runtime/maps/trashbot_map.pgm",
            "cell_counts": {"free": 10, "unknown": 20, "occupied": 1},
        }
        commands = proof.setdefault("commands", {})
        assert isinstance(commands, dict)
        managed = commands.setdefault("managed_runtime", {})
        assert isinstance(managed, dict)
        managed["map_yaml"] = proof["managed_runtime_map_yaml"]
        managed["map_yaml_source"] = proof["managed_runtime_map_yaml_source"]
        managed["map_analysis"] = proof["managed_runtime_map_analysis"]
        return proof

    def test_map_server_visibility_classifies_node_absent_and_preserves_amcl_active(self) -> None:
        """`Node not found` 必须进入 map_server_node_absent，同时保留 `/amcl active [3]`。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            timed_out=True,
            returncode=None,
            graph_node_visible=False,
        )
        map_retry = self._visibility_attempt(
            label="retry_attempt",
            node_key="map_server",
            node_name="/map_server",
            stderr="Node not found\n",
            returncode=1,
            graph_node_visible=False,
            timeout_s=18.0,
        )
        proof = self._map_server_visibility_proof(
            graph_nodes=["/amcl"],
            map_first=map_first,
            map_retry=map_retry,
            graph_root_classification="ros2_daemon_or_dds_graph_discovery_timeout",
            graph_timed_out=True,
        )

        summary = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)

        self.assertEqual("map_server_node_absent", summary["canonical_classification"])
        self.assertEqual("lifecycle_retry_node_not_found", summary["failure_detail"])
        self.assertTrue(summary["readiness_inputs"]["board_source_preflight_ready"])
        self.assertTrue(summary["readiness_inputs"]["lightweight_cli_ready"])
        self.assertTrue(summary["readiness_inputs"]["cli_ready"])
        self.assertTrue(summary["readiness_inputs"]["runtime_ready"])
        self.assertEqual("Node not found\n", summary["lifecycle_readback"]["retry_attempt"]["stderr"])
        self.assertTrue(summary["amcl_lifecycle_reference"]["current_active"])
        self.assertFalse(summary["amcl_lifecycle_reference"]["live_state_regression"])

    def test_map_server_visibility_classifies_graph_visible_lifecycle_timeout_as_budget(self) -> None:
        """graph 已看到 `/map_server` 但 lifecycle retry timeout 时，归到 helper budget/timing。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            timed_out=True,
            returncode=None,
            timeout_s=10.0,
            elapsed_ms=10080,
            graph_node_visible=True,
        )
        map_retry = self._visibility_attempt(
            label="retry_attempt",
            node_key="map_server",
            node_name="/map_server",
            timed_out=True,
            returncode=None,
            timeout_s=18.0,
            elapsed_ms=18060,
            graph_node_visible=True,
        )
        proof = self._map_server_visibility_proof(graph_nodes=["/map_server", "/amcl"], map_first=map_first, map_retry=map_retry)

        summary = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)

        self.assertEqual("helper_budget_or_timing_exhausted", summary["canonical_classification"])
        self.assertEqual("graph_visible_lifecycle_command_timeout", summary["failure_detail"])
        self.assertTrue(summary["node_graph_inventory"]["visible"])
        self.assertEqual(18.0, summary["lifecycle_readback"]["timeout_budget_s"]["retry_attempt"])

    def test_map_server_visibility_classifies_daemon_dds_graph_visibility_failure(self) -> None:
        """daemon/DDS graph timeout 要优先于 node absence，避免把不可读 graph 写成缺节点。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            timed_out=True,
            returncode=None,
            graph_node_visible=False,
        )
        proof = self._map_server_visibility_proof(
            graph_nodes=[],
            map_first=map_first,
            graph_root_classification="ros2_daemon_or_dds_graph_discovery_timeout",
            graph_timed_out=True,
        )

        summary = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)

        self.assertEqual("daemon_or_dds_graph_visibility_failed", summary["canonical_classification"])
        self.assertEqual("daemon_or_dds_graph_inventory_unreadable", summary["failure_detail"])
        self.assertTrue(summary["daemon_dds_visibility"]["probe_boundaries"]["ros2_node_list"]["timed_out"])

    def test_map_server_visibility_classifies_lifecycle_manager_or_startup_missing(self) -> None:
        """managed runtime 未能启动时，不能伪装成 map_server lifecycle active 或 downstream blocker。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            stdout="",
            stderr="",
            returncode=1,
            graph_node_visible=False,
        )
        proof = self._map_server_visibility_proof(
            graph_nodes=[],
            map_first=map_first,
            managed_requested=True,
            managed_started=False,
            startup_error={"type": "RuntimeError", "message": "managed runtime launch failed"},
        )

        summary = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)

        self.assertEqual("lifecycle_manager_or_process_startup_missing", summary["canonical_classification"])
        self.assertEqual("managed_runtime_or_lifecycle_process_not_ready", summary["failure_detail"])
        self.assertEqual(
            {"type": "RuntimeError", "message": "managed runtime launch failed"},
            summary["lifecycle_manager_or_process_startup_context"]["startup_error"],
        )

    def test_map_server_visibility_classifies_active_case_and_keeps_safety_false(self) -> None:
        """active case 也只能证明 lifecycle readback，危险字段必须继续 false。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            stdout="active [3]\n",
            graph_node_visible=True,
        )
        proof = self._map_server_visibility_proof(graph_nodes=["/map_server", "/amcl"], map_first=map_first)

        summary = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)

        self.assertEqual("map_server_lifecycle_active", summary["canonical_classification"])
        self.assertEqual("map_server_lifecycle_readback_active", summary["failure_detail"])
        self.assertTrue(summary["lifecycle_readback"]["clean"])
        invariants = summary["no_motion_invariants"]
        for key in (
            "safe_to_control",
            "publishes_cmd_vel",
            "calls_base_manual",
            "robot_control_executed",
            "route_execution_success",
            "delivery_success",
            "hil_pass",
            "uses_base_uart",
            "path_generation_attempted",
            "path_generated",
        ):
            self.assertFalse(invariants[key], key)

    def test_map_server_presence_recovery_reports_not_requested_boundary(self) -> None:
        """默认 read-only 路径必须明确说没有执行 recovery，不能伪装成恢复失败。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            timed_out=True,
            returncode=None,
            graph_node_visible=False,
        )
        proof = self._map_server_visibility_proof(graph_nodes=["/amcl"], map_first=map_first)
        visibility = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)

        summary = HELPER.build_map_server_presence_recovery_summary(proof, visibility_summary=visibility)

        self.assertFalse(summary["recovery_attempted"])
        self.assertEqual("presence_recovery_not_requested_read_only_existing_graph", summary["canonical_classification"])
        self.assertEqual("rerun_with_managed_runtime_opt_in_and_managed_map_yaml", summary["next_step"])
        self.assertFalse(summary["recovery_path"]["managed_runtime_requested"])

    def test_map_server_presence_recovery_requires_managed_map_yaml(self) -> None:
        """显式 recovery 没有 map yaml 时，blocker 必须停在可修复的 map 输入层。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            returncode=1,
            graph_node_visible=False,
        )
        proof = self._map_server_visibility_proof(
            graph_nodes=[],
            map_first=map_first,
            managed_requested=True,
            managed_started=False,
        )
        visibility = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)

        summary = HELPER.build_map_server_presence_recovery_summary(proof, visibility_summary=visibility)

        self.assertTrue(summary["recovery_attempted"])
        self.assertEqual("managed_map_yaml_missing", summary["canonical_classification"])
        self.assertEqual("provide_existing_managed_map_yaml", summary["next_step"])
        self.assertFalse(summary["managed_map_yaml"]["provided"])

    def test_map_server_presence_recovery_narrows_node_not_found_after_managed_start(self) -> None:
        """managed runtime 后仍 Node-not-found 时，要比旧 absent 更窄，指出 lifecycle manager/map_server 关系。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            timed_out=True,
            returncode=None,
            graph_node_visible=False,
        )
        map_retry = self._visibility_attempt(
            label="retry_attempt",
            node_key="map_server",
            node_name="/map_server",
            stderr="Node not found\n",
            returncode=1,
            graph_node_visible=False,
            timeout_s=18.0,
        )
        proof = self._with_managed_map_yaml(
            self._map_server_visibility_proof(
                graph_nodes=["/amcl", "/lifecycle_manager"],
                map_first=map_first,
                map_retry=map_retry,
                managed_requested=True,
                managed_started=True,
            )
        )
        visibility = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)

        summary = HELPER.build_map_server_presence_recovery_summary(proof, visibility_summary=visibility)

        self.assertEqual("map_server_node_absent", visibility["canonical_classification"])
        self.assertEqual("lifecycle_manager_not_serving_map_server", summary["canonical_classification"])
        self.assertEqual("managed_runtime_started_but_map_server_lifecycle_node_not_found", summary["failure_detail"])
        self.assertTrue(summary["recovery_path"]["managed_runtime_requested"])
        self.assertTrue(summary["recovery_path"]["managed_runtime_started"])
        self.assertTrue(summary["node_presence"]["lifecycle_manager_visible"])
        self.assertTrue(summary["lifecycle_readback"]["node_not_found_observed"])
        self.assertEqual("trashbot_map.yaml", summary["managed_map_yaml"]["basename"])

    def test_map_server_presence_recovery_uses_runtime_log_transition_failure(self) -> None:
        """日志已证明 map_server configure 失败时，要优先输出 lifecycle transition blocker。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            timed_out=True,
            returncode=None,
            graph_node_visible=False,
        )
        proof = self._with_managed_map_yaml(
            self._map_server_visibility_proof(
                graph_nodes=[],
                map_first=map_first,
                managed_requested=True,
                managed_started=True,
                graph_timed_out=True,
            )
        )
        graph_root = proof["ros2_graph_timeout_root_cause"]
        assert isinstance(graph_root, dict)
        probes = graph_root["probes"]
        assert isinstance(probes, dict)
        managed_process = probes["managed_process"]
        assert isinstance(managed_process, dict)
        managed_process["log_tail"] = (
            "[INFO] [lifecycle_manager]: Configuring map_server\n"
            "[INFO] [map_io]: Loading yaml file: /root/rober/onboard/runtime/maps/trashbot_map.yaml\n"
            "[ERROR] [lifecycle_manager]: Failed to change state for node: map_server\n"
        )
        visibility = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)

        summary = HELPER.build_map_server_presence_recovery_summary(proof, visibility_summary=visibility)

        self.assertEqual("map_server_lifecycle_not_active_after_recovery", summary["canonical_classification"])
        self.assertEqual("lifecycle_manager_failed_to_change_state_for_map_server", summary["failure_detail"])
        self.assertTrue(summary["node_presence"]["log_inferred_map_server_configure_started"])
        self.assertTrue(summary["node_presence"]["log_inferred_map_yaml_loaded"])
        self.assertTrue(summary["node_presence"]["log_inferred_map_server_state_change_failed"])

    def test_map_server_lifecycle_activation_narrows_valid_map_state_change_failure(self) -> None:
        """yaml/PGM 有效时，12-55 summary 必须继续下钻到 configure transition return。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            maps = Path(temp_dir)
            pgm = maps / "trashbot_map.pgm"
            yaml_path = maps / "trashbot_map.yaml"
            pgm.write_bytes(b"P5\n2 2\n255\n" + bytes([254, 205, 0, 254]))
            yaml_path.write_text(
                "\n".join(
                    [
                        "image: trashbot_map.pgm",
                        "resolution: 0.05",
                        "origin: [-5.47385, 0, 0]",
                        "occupied_thresh: 0.65",
                        "free_thresh: 0.196",
                        "mode: trinary",
                        "negate: 0",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            map_first = self._visibility_attempt(
                label="first_attempt",
                node_key="map_server",
                node_name="/map_server",
                timed_out=True,
                returncode=None,
                graph_node_visible=False,
            )
            proof = self._map_server_visibility_proof(
                graph_nodes=[],
                map_first=map_first,
                managed_requested=True,
                managed_started=True,
                graph_timed_out=True,
            )
            proof["managed_runtime_map_yaml"] = str(yaml_path)
            proof["managed_runtime_map_yaml_source"] = "explicit_cli_managed_map_yaml"
            proof["managed_runtime_map_analysis"] = HELPER.map_yaml_runtime_analysis(str(yaml_path))
            commands = proof["commands"]
            assert isinstance(commands, dict)
            managed = commands["managed_runtime"]
            assert isinstance(managed, dict)
            managed["map_yaml"] = str(yaml_path)
            managed["map_analysis"] = proof["managed_runtime_map_analysis"]
            managed["log_tail"] = (
                "Traceback (most recent call last):\n"
                "  File \"/root/rober/onboard/build/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py\", line 459, in _tick\n"
                "serial.serialutil.SerialException: device reports readiness to read but returned no data\n"
                "[INFO] [lifecycle_manager]: Configuring map_server\n"
                f"[INFO] [map_io]: Loading yaml file: {yaml_path}\n"
                "[INFO] [map_io]: resolution: 0.05\n"
                "[INFO] [map_io]: origin[0]: -5.47385\n"
                "[INFO] [map_io]: free_thresh: 0.196\n"
                "[INFO] [map_io]: occupied_thresh: 0.65\n"
                "[INFO] [map_io]: mode: trinary\n"
                f"[INFO] [map_io]: Loading image_file: {pgm}\n"
                "[ERROR] [lifecycle_manager]: Failed to change state for node: map_server\n"
                f"[INFO] [map_io]: Read map {pgm}: 2 X 2 map @ 0.05 m/cell\n"
            )
            visibility = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)
            presence = HELPER.build_map_server_presence_recovery_summary(proof, visibility_summary=visibility)

            activation = HELPER.build_map_server_lifecycle_activation_summary(proof, presence_summary=presence)
            transition = HELPER.build_map_server_transition_callback_probe_summary(
                proof,
                presence_summary=presence,
                activation_summary=activation,
            )

            self.assertEqual("map_server_activate_callback_failed", activation["canonical_classification"])
            self.assertEqual(
                "lifecycle_manager_failed_to_change_state_for_map_server_after_valid_map_readback",
                activation["failure_detail"],
            )
            self.assertTrue(activation["map_yaml_pgm_readback"]["yaml"]["readable"])
            self.assertTrue(activation["map_yaml_pgm_readback"]["pgm"]["readable"])
            self.assertEqual("trinary", activation["map_yaml_pgm_readback"]["fields"]["mode"])
            self.assertEqual("map", activation["launch_parameters"]["map_server"]["parameters"]["frame_id"])
            self.assertEqual(12.0, activation["launch_parameters"]["lifecycle_manager"]["service_timeout_s"])
            self.assertEqual("0", activation["launch_parameters"]["runtime_environment"]["RMW_FASTRTPS_USE_SHM"])
            self.assertEqual("UDPv4", activation["launch_parameters"]["runtime_environment"]["FASTDDS_BUILTIN_TRANSPORTS"])
            self.assertTrue(activation["runtime_log"]["events"]["map_read_after_state_change_failure"])
            self.assertFalse(activation["no_motion_invariants"]["publishes_cmd_vel"])
            self.assertEqual(
                "map_server_loadmap_response_success_equivalent_after_changestate_failure",
                transition["canonical_classification"],
            )
            self.assertEqual(
                "loadmap_response_success_equivalent_logged_after_lifecycle_changestate_failure_without_direct_return_code",
                transition["failure_detail"],
            )
            load_map = transition["load_map_response_from_yaml"]
            self.assertFalse(load_map["direct_return_code_observed"])
            self.assertEqual("not_logged_by_nav2_map_server_runtime", load_map["return_code"])
            self.assertEqual(
                "success_equivalent_logged_after_lifecycle_changestate_failure",
                load_map["response_status"],
            )
            self.assertEqual(
                "return_failure_before_deferred_loadmap_response_completion_log",
                load_map["on_configure_return_path"],
            )
            self.assertEqual(
                "pending_or_not_logged",
                load_map["load_map_response_status_at_changestate_failure"],
            )
            self.assertTrue(load_map["response_status_evidence"]["map_read_completed_after_state_failure"])
            self.assertEqual(
                "failure",
                load_map["lifecycle_changestate_response_handling"]["inferred_response_status"],
            )
            source = transition["on_configure_return_source"]
            self.assertEqual(
                "loadmap_response_success_equivalent_logged_after_on_configure_failure",
                source["primary_source"],
            )
            self.assertEqual("loadMapResponseFromYaml_response_status", source["source_family"])
            self.assertTrue(source["map_input_validation"]["valid_for_map_server"])
            self.assertFalse(source["baseline_repeated_without_narrowing"])
            self.assertTrue(source["excluded_sources"]["parameter_or_map_file_invalid_excluded_by_readback"])
            self.assertEqual(
                "return_failure_before_deferred_loadmap_response_completion_log",
                source["on_configure_return_path"],
            )
            self.assertEqual("configure", transition["transition_sequence"]["observed_stage"])
            self.assertTrue(transition["transition_sequence"]["configure"]["state_change_failed_before_map_read_completed"])
            self.assertTrue(
                transition["transition_sequence"]["configure"][
                    "state_change_failed_after_image_load_before_map_read_completed"
                ]
            )
            self.assertTrue(transition["service_rpc_timing"]["changestate_response_false_before_map_io_completion"])
            self.assertTrue(
                transition["service_rpc_timing"]["map_io_timing"][
                    "change_state_response_false_while_map_io_incomplete"
                ]
            )
            self.assertEqual("failure", transition["service_rpc_timing"]["inferred_change_state_response"])
            self.assertEqual("not_created_before_configure_return_failure", transition["bond_timing"]["bond_stage"])
            self.assertIn("SerialException", transition["runtime_log_window"]["exception_text"])
            self.assertFalse(transition["no_motion_invariants"]["publishes_cmd_vel"])

    def test_map_server_transition_probe_splits_after_map_read_failure(self) -> None:
        """map IO 已完成后再失败时，要比 generic configure callback 更窄。"""
        log_summary = HELPER.map_server_activation_log_summary(
            "\n".join(
                [
                    "[INFO] [lifecycle_manager]: Configuring map_server",
                    "[INFO] [map_io]: Loading yaml file: /tmp/trashbot_map.yaml",
                    "[INFO] [map_io]: Loading image_file: /tmp/trashbot_map.pgm",
                    "[INFO] [map_io]: Read map /tmp/trashbot_map.pgm: 2 X 2 map @ 0.05 m/cell",
                    "[ERROR] [lifecycle_manager]: Failed to change state for node: map_server",
                ]
            )
        )

        classification, detail, next_step = HELPER.classify_map_server_transition_callback_probe(
            proof={"managed_runtime_requested": True},
            activation_summary={},
            log_summary=log_summary,
            lifecycle_readback={},
        )
        normalized, _filter = HELPER.normalize_root_causes_for_presence_recovery(
            [{"layer": "Managed runtime wait", "reason": "ros2_node_list_timeout"}],
            managed_runtime={
                "requested": True,
                "started": True,
                "log_tail": "\n".join(
                    [
                        "[INFO] [lifecycle_manager]: Configuring map_server",
                        "[INFO] [map_io]: Loading yaml file: /tmp/trashbot_map.yaml",
                        "[INFO] [map_io]: Loading image_file: /tmp/trashbot_map.pgm",
                        "[INFO] [map_io]: Read map /tmp/trashbot_map.pgm: 2 X 2 map @ 0.05 m/cell",
                        "[ERROR] [lifecycle_manager]: Failed to change state for node: map_server",
                    ]
                ),
            },
            managed_map_analysis={"ok": True},
        )

        self.assertEqual("map_server_configure_return_failure_after_map_read_completed", classification)
        self.assertEqual("lifecycle_manager_changestate_response_failure_during_configure_after_map_read_completed", detail)
        self.assertEqual("inspect_map_server_on_configure_return_after_successful_map_io_readback", next_step)
        self.assertEqual("map_server_configure_return_failure_after_map_read_completed", normalized[0]["reason"])

    def test_map_server_transition_probe_splits_response_false_before_map_io_completion(self) -> None:
        """map read 后续完成时，主因要压到 ChangeState response false 与 map IO completion 的关系。"""
        log_text = "\n".join(
            [
                "[INFO] [1783840650.532765313] [lifecycle_manager]: Configuring map_server",
                "[INFO] [1783840650.542403302] [map_server]: Configuring",
                "[INFO] [1783840650.542782385] [map_io]: Loading yaml file: /root/rober/onboard/runtime/maps/trashbot_map.yaml",
                "[INFO] [1783840650.560512656] [map_io]: Loading image_file: /root/rober/onboard/runtime/maps/trashbot_map.pgm",
                "[ERROR] [1783840650.660171079] [lifecycle_manager]: Failed to change state for node: map_server",
                "[INFO] [1783840651.001740216] [map_io]: Read map /root/rober/onboard/runtime/maps/trashbot_map.pgm: 261 X 113 map @ 0.05 m/cell",
            ]
        )
        log_summary = HELPER.map_server_activation_log_summary(log_text)

        classification, detail, next_step = HELPER.classify_map_server_transition_callback_probe(
            proof={"managed_runtime_requested": True},
            activation_summary={},
            log_summary=log_summary,
            lifecycle_readback={},
        )
        timing = HELPER.map_io_changestate_timing(log_summary)
        normalized, _filtering = HELPER.normalize_root_causes_for_presence_recovery(
            [{"layer": "Managed runtime wait", "reason": "ros2_node_list_timeout"}],
            managed_runtime={"requested": True, "started": True, "log_tail": log_text},
            managed_map_analysis={"ok": True},
        )

        self.assertEqual("map_server_changestate_response_false_before_map_io_completion", classification)
        self.assertEqual("lifecycle_manager_changestate_response_false_while_map_io_completed_later", detail)
        self.assertEqual(
            "inspect_map_server_on_configure_return_false_path_while_loadMapResponseFromYaml_continues",
            next_step,
        )
        self.assertTrue(log_summary["events"]["changestate_response_false_before_map_io_completion"])
        self.assertTrue(timing["change_state_response_false_while_map_io_incomplete"])
        self.assertGreater(timing["state_failure_to_map_read_completed_ms"], 300)
        self.assertEqual(
            "map_server_loadmap_response_success_equivalent_after_changestate_failure",
            normalized[0]["reason"],
        )
        self.assertEqual(
            "loadmap_response_success_equivalent_logged_after_lifecycle_changestate_failure_without_direct_return_code",
            normalized[0]["detail"],
        )

    def test_map_server_transition_probe_classifies_failure_without_callback_log(self) -> None:
        """ChangeState failure 已出现但 map_server callback 未落日志时，要归到 callback log 之前。"""
        log_text = "\n".join(
            [
                "[INFO] [1783843549.084964397] [lifecycle_manager]: Starting managed nodes bringup...",
                "[INFO] [1783843549.086395604] [lifecycle_manager]: Configuring map_server",
                "[ERROR] [1783843549.119283736] [lifecycle_manager]: Failed to change state for node: map_server",
                "[ERROR] [1783843549.119728819] [lifecycle_manager]: Failed to bring up all requested nodes. Aborting bringup.",
            ]
        )
        log_summary = HELPER.map_server_activation_log_summary(log_text)

        classification, detail, next_step = HELPER.classify_map_server_transition_callback_probe(
            proof={"managed_runtime_requested": True},
            activation_summary={},
            log_summary=log_summary,
            lifecycle_readback={},
        )
        transition = HELPER.build_map_server_transition_callback_probe_summary(
            {"managed_runtime_requested": True},
            presence_summary={},
            activation_summary={"runtime_log": log_summary},
        )

        self.assertTrue(log_summary["events"]["state_change_failed_before_map_server_configure_callback"])
        self.assertEqual("map_server_changestate_response_failure_before_configure_callback_log", classification)
        self.assertEqual("lifecycle_manager_changestate_response_failure_logged_before_map_server_on_configure_log", detail)
        self.assertEqual(
            "inspect_lifecycle_manager_change_state_future_response_order_and_map_server_executor_timing",
            next_step,
        )
        self.assertFalse(transition["transition_sequence"]["configure"]["map_server_callback_entered"])
        self.assertFalse(transition["transition_sequence"]["configure"]["map_server_configure_callback_log_observed"])

    def test_map_server_transition_probe_prefers_precise_precleanup_log(self) -> None:
        """pre-cleanup log 有真实顺序时，不能再让 cleanup tail 造成 line_indices 为空。"""
        cleanup_tail = "\n".join(
            [
                "[INFO] [1783836898.467809515] [lifecycle_manager]: Running Nav2 LifecycleManager rcl preshutdown (lifecycle_manager)",
                "[INFO] [1783836898.468490806] [map_server]: Running Nav2 LifecycleNode rcl preshutdown (map_server)",
                "[INFO] [1783836898.468828097] [map_server]: Cleaning up",
            ]
        )
        precise_log = "\n".join(
            [
                "[INFO] [1783836840.532862511] [lifecycle_manager]: Configuring map_server",
                "[ERROR] [1783836840.599618442] [lifecycle_manager]: Failed to change state for node: map_server",
                "[INFO] [1783836840.684555064] [map_server]: Configuring",
                "[INFO] [1783836840.685083605] [map_io]: Loading yaml file: /root/rober/onboard/runtime/maps/trashbot_map.yaml",
                "[INFO] [1783836840.690896849] [map_io]: Loading image_file: /root/rober/onboard/runtime/maps/trashbot_map.pgm",
                "[INFO] [1783836841.067146964] [map_io]: Read map /root/rober/onboard/runtime/maps/trashbot_map.pgm: 261 X 113 map @ 0.05 m/cell",
            ]
        )
        proof = {
            "managed_runtime_requested": True,
            "commands": {"managed_runtime": {"log_tail": cleanup_tail}},
            "map_server_presence_recovery": {"process_presence": {"log_tail": precise_log}},
        }

        selected = HELPER.managed_runtime_log_for_activation(proof)
        log_summary = HELPER.map_server_activation_log_summary(selected)
        classification, detail, next_step = HELPER.classify_map_server_transition_callback_probe(
            proof=proof,
            activation_summary={},
            log_summary=log_summary,
            lifecycle_readback={},
        )

        self.assertEqual(precise_log, selected)
        self.assertTrue(log_summary["events"]["state_change_failed_before_map_server_configure_callback"])
        self.assertIsNotNone(log_summary["line_indices"]["map_server_configure_callback_entered"])
        self.assertIsNotNone(log_summary["event_timestamps_s"]["state_change_failed"])
        self.assertEqual("map_server_changestate_response_failure_before_configure_callback_log", classification)
        self.assertEqual("lifecycle_manager_changestate_response_failure_logged_before_map_server_on_configure_log", detail)
        self.assertEqual(
            "inspect_lifecycle_manager_change_state_future_response_order_and_map_server_executor_timing",
            next_step,
        )

    def test_map_server_transition_probe_reports_amcl_after_map_server_success(self) -> None:
        """map_server 已完成 map read 后转到 AMCL 失败时，主因不能再写回 map_server configure。"""
        log_text = "\n".join(
            [
                "[INFO] [1783840371.520294723] [lifecycle_manager]: Configuring map_server",
                "[INFO] [1783840371.616449985] [map_server]: Configuring",
                "[INFO] [1783840371.616767443] [map_io]: Loading yaml file: /root/rober/onboard/runtime/maps/trashbot_map.yaml",
                "[INFO] [1783840371.619022149] [map_io]: Loading image_file: /root/rober/onboard/runtime/maps/trashbot_map.pgm",
                "[INFO] [1783840371.846811672] [map_io]: Read map /root/rober/onboard/runtime/maps/trashbot_map.pgm: 261 X 113 map @ 0.05 m/cell",
                "[INFO] [1783840373.563832443] [lifecycle_manager]: Configuring amcl",
                "[INFO] [1783840374.183238672] [amcl]: Configuring",
                "[INFO] [1783840374.183857588] [amcl]: initTransforms",
                "[ERROR] [1783840374.207066727] [lifecycle_manager]: Failed to change state for node: amcl",
                "[ERROR] [1783840374.207400268] [lifecycle_manager]: Failed to bring up all requested nodes. Aborting bringup.",
                "[INFO] [1783840374.487988605] [amcl]: initPubSub",
                "[INFO] [1783840374.901308077] [amcl]: Received a 261 X 113 map @ 0.050 m/pix",
            ]
        )
        log_summary = HELPER.map_server_activation_log_summary(log_text)

        classification, detail, next_step = HELPER.classify_map_server_transition_callback_probe(
            proof={"managed_runtime_requested": True},
            activation_summary={},
            log_summary=log_summary,
            lifecycle_readback={},
        )
        normalized, _filtering = HELPER.normalize_root_causes_for_presence_recovery(
            [{"layer": "Managed runtime wait", "reason": "ros2_node_list_timeout"}],
            managed_runtime={"requested": True, "started": True, "log_tail": log_text},
            managed_map_analysis={"ok": True},
        )

        self.assertTrue(log_summary["events"]["amcl_state_change_failed_after_map_server_configure_success"])
        self.assertEqual(
            "map_server_configure_completed_lifecycle_blocked_by_amcl_configure_failure",
            classification,
        )
        self.assertEqual(
            "lifecycle_manager_advanced_to_amcl_after_map_server_configure_then_amcl_changestate_failed",
            detail,
        )
        self.assertEqual("inspect_amcl_on_configure_return_path_after_map_server_configure_success", next_step)
        self.assertEqual(
            "map_server_configure_completed_lifecycle_blocked_by_amcl_configure_failure",
            normalized[0]["reason"],
        )

    def test_map_server_transition_probe_narrows_fastdds_shm_port_lock(self) -> None:
        """FastDDS SHM 端口锁必须落到 ChangeState RPC/DDS 层，不再复用泛化 configure callback。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            maps = Path(temp_dir)
            pgm = maps / "trashbot_map.pgm"
            yaml_path = maps / "trashbot_map.yaml"
            pgm.write_bytes(b"P5\n2 2\n255\n" + bytes([254, 205, 0, 254]))
            yaml_path.write_text(
                "\n".join(
                    [
                        "image: trashbot_map.pgm",
                        "resolution: 0.05",
                        "origin: [-5.47385, 0, 0]",
                        "occupied_thresh: 0.65",
                        "free_thresh: 0.196",
                        "mode: trinary",
                        "negate: 0",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            map_first = self._visibility_attempt(
                label="first_attempt",
                node_key="map_server",
                node_name="/map_server",
                timed_out=True,
                returncode=None,
                graph_node_visible=False,
            )
            proof = self._map_server_visibility_proof(
                graph_nodes=[],
                map_first=map_first,
                managed_requested=True,
                managed_started=True,
                graph_timed_out=True,
            )
            proof["managed_runtime_wait_result"] = {
                "boundary": "ros2_node_list_timeout",
                "graph_wait_summary": {"latest_ros2_node_list_timed_out": True},
            }
            proof["managed_runtime_map_yaml"] = str(yaml_path)
            proof["managed_runtime_map_yaml_source"] = "explicit_cli_managed_map_yaml"
            proof["managed_runtime_map_analysis"] = HELPER.map_yaml_runtime_analysis(str(yaml_path))
            commands = proof["commands"]
            assert isinstance(commands, dict)
            managed = commands["managed_runtime"]
            assert isinstance(managed, dict)
            managed["map_yaml"] = str(yaml_path)
            managed["map_analysis"] = proof["managed_runtime_map_analysis"]
            managed["log_tail"] = (
                "RTPS_TRANSPORT_SHM Error Failed init_port fastrtps_port7421: open_and_lock_file failed\n"
                "[INFO] [lifecycle_manager]: Configuring map_server\n"
                f"[INFO] [map_io]: Loading yaml file: {yaml_path}\n"
                f"[INFO] [map_io]: Loading image_file: {pgm}\n"
                "[ERROR] [lifecycle_manager]: Failed to change state for node: map_server\n"
                f"[INFO] [map_io]: Read map {pgm}: 2 X 2 map @ 0.05 m/cell\n"
            )
            visibility = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)
            presence = HELPER.build_map_server_presence_recovery_summary(proof, visibility_summary=visibility)
            activation = HELPER.build_map_server_lifecycle_activation_summary(proof, presence_summary=presence)

            transition = HELPER.build_map_server_transition_callback_probe_summary(
                proof,
                presence_summary=presence,
                activation_summary=activation,
            )
            normalized, _filter = HELPER.normalize_root_causes_for_presence_recovery(
                [{"layer": "Managed runtime wait", "reason": "ros2_node_list_timeout"}],
                managed_runtime=managed,
                managed_map_analysis=proof["managed_runtime_map_analysis"],
            )

            self.assertEqual(
                "map_server_change_state_rpc_dds_shm_transport_port_lock",
                transition["canonical_classification"],
            )
            self.assertIn("open_and_lock_file failed", transition["runtime_log_window"]["dds_transport_error_text"])
            self.assertTrue(activation["lifecycle_manager_state_change_result"]["dds_shm_transport_error"])
            self.assertEqual("map_server_change_state_rpc_dds_shm_transport_port_lock", normalized[0]["reason"])
            self.assertFalse(transition["no_motion_invariants"]["publishes_cmd_vel"])

    def test_map_server_transition_probe_classifies_lifecycle_rpc_timeout(self) -> None:
        """lifecycle readback timeout 要落到 service/RPC 层，不能伪装成 callback return。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            graph_node_visible=True,
        )
        proof = self._with_managed_map_yaml(
            self._map_server_visibility_proof(
                graph_nodes=["/map_server"],
                map_first=map_first,
                managed_requested=True,
                managed_started=True,
            )
        )
        presence = {
            "lifecycle_readback": {
                "clean": False,
                "first_attempt": {"executed": True, "timed_out": True, "returncode": None},
                "retry_attempt": {"executed": True, "timed_out": True, "returncode": None},
            }
        }
        activation = {"canonical_classification": "map_server_lifecycle_service_timeout_with_process_alive"}

        transition = HELPER.build_map_server_transition_callback_probe_summary(
            proof,
            presence_summary=presence,
            activation_summary=activation,
        )

        self.assertEqual("map_server_lifecycle_service_rpc_timeout", transition["canonical_classification"])
        self.assertTrue(transition["service_rpc_timing"]["lifecycle_readback_timeout_observed"])
        self.assertFalse(transition["no_motion_invariants"]["calls_base_manual"])

    def test_map_server_transition_probe_classifies_bond_wait_timeout(self) -> None:
        """bond timeout 必须单独成因，便于下一轮调 lifecycle_manager bond_timeout/executor。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            graph_node_visible=True,
        )
        proof = self._with_managed_map_yaml(
            self._map_server_visibility_proof(
                graph_nodes=["/map_server"],
                map_first=map_first,
                managed_requested=True,
                managed_started=True,
            )
        )
        managed = proof["commands"]["managed_runtime"]
        assert isinstance(managed, dict)
        managed["log_tail"] = (
            "[INFO] [lifecycle_manager]: Activating map_server\n"
            "[ERROR] [lifecycle_manager]: Timed out waiting for bond connection to map_server\n"
        )
        presence = {"lifecycle_readback": {"clean": False, "first_attempt": {}, "retry_attempt": {}}}
        activation = {"canonical_classification": "map_server_activate_callback_failed"}

        transition = HELPER.build_map_server_transition_callback_probe_summary(
            proof,
            presence_summary=presence,
            activation_summary=activation,
        )

        self.assertEqual("map_server_bond_wait_timeout_after_active", transition["canonical_classification"])
        self.assertTrue(transition["bond_timing"]["bond_timeout_observed"])
        self.assertEqual("wait_timeout_after_active", transition["bond_timing"]["bond_stage"])

    def test_map_server_transition_probe_classifies_process_exit(self) -> None:
        """transition 期间进程退出要优先于 callback/service 推断。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            graph_node_visible=True,
        )
        proof = self._with_managed_map_yaml(
            self._map_server_visibility_proof(
                graph_nodes=["/map_server"],
                map_first=map_first,
                managed_requested=True,
                managed_started=True,
            )
        )
        managed = proof["commands"]["managed_runtime"]
        assert isinstance(managed, dict)
        managed["process_returncode"] = 2
        managed["log_tail"] = "[INFO] [lifecycle_manager]: Configuring map_server\n"
        presence = {"lifecycle_readback": {"clean": False, "first_attempt": {}, "retry_attempt": {}}}
        activation = {"canonical_classification": "map_server_configure_exception"}

        transition = HELPER.build_map_server_transition_callback_probe_summary(
            proof,
            presence_summary=presence,
            activation_summary=activation,
        )

        self.assertEqual("map_server_process_exited_during_transition", transition["canonical_classification"])
        self.assertEqual("managed_runtime_process_returncode_2", transition["failure_detail"])

    def test_presence_recovery_root_cause_filter_suppresses_package_missing_noise(self) -> None:
        """runtime log 已证明节点跑过时，package timeout 只能做诊断，不能进主 root_causes。"""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as log_file:
            log_file.write(
                "starting role=map_server\n"
                "starting role=lifecycle_manager\n"
                "[INFO] [lifecycle_manager]: Configuring map_server\n"
                "[INFO] [map_io]: Loading yaml file: /root/rober/onboard/runtime/maps/trashbot_map.yaml\n"
                "[INFO] [map_io]: Loading image_file: /root/rober/onboard/runtime/maps/trashbot_map.pgm\n"
                "[ERROR] [lifecycle_manager]: Failed to change state for node: map_server\n"
            )
            log_path = log_file.name
        self.addCleanup(lambda: Path(log_path).unlink(missing_ok=True))
        root_causes = [
            {"layer": "Managed runtime wait", "reason": "ros2_node_list_timeout"},
            {"layer": "canonical map proof", "reason": "map_lifecycle_proof_not_clean"},
            {"layer": "ROS install/source", "reason": "nav2_map_server_missing"},
            {"layer": "ROS install/source", "reason": "nav2_amcl_missing"},
        ]

        normalized, filtering = HELPER.normalize_root_causes_for_presence_recovery(
            root_causes,
            managed_runtime={
                "requested": True,
                "started": True,
                "log_path": log_path,
            },
            managed_map_analysis={"ok": True},
        )

        self.assertTrue(filtering["applied"])
        self.assertEqual(
            {
                "layer": "Nav2 map_server transition callback",
                "reason": "map_server_changestate_response_failure_after_image_load_before_map_read_completed",
                "detail": "lifecycle_manager_changestate_response_failure_after_image_load_before_map_read_completed",
            },
            normalized[0],
        )
        self.assertEqual(4, len(filtering["suppressed_root_causes"]))
        self.assertNotIn("nav2_map_server_missing", {cause["reason"] for cause in normalized})
        self.assertNotIn("ros2_node_list_timeout", {cause["reason"] for cause in normalized})

    def test_lifecycle_active_log_promotes_concrete_downstream_root_cause(self) -> None:
        """17:55 baseline 后，如果已读到 scan/map/TF 具体 blocker，closeout 主因不能停在 graph timeout。"""
        log_text = "\n".join(
            [
                "starting role=map_server",
                "starting role=lifecycle_manager",
                "[INFO] [lifecycle_manager]: Configuring map_server",
                "[INFO] [lifecycle_manager]: Activating map_server",
                "[INFO] [map_server]: Activating",
                "[INFO] [lifecycle_manager]: Server map_server connected with bond",
                "[INFO] [lifecycle_manager]: Activating amcl",
                "[INFO] [amcl]: Activating",
                "[INFO] [lifecycle_manager]: Server amcl connected with bond",
                "[INFO] [lifecycle_manager]: Managed nodes are active",
            ]
        )
        root_causes = [
            {"layer": "Managed runtime wait", "reason": "ros2_node_list_timeout"},
            {"layer": "Nav2 sensor input", "reason": "/scan_no_publisher"},
            {"layer": "Nav2 map input", "reason": "/map_once_not_observed"},
        ]

        normalized, filtering = HELPER.normalize_root_causes_for_presence_recovery(
            root_causes,
            managed_runtime={"requested": True, "started": True, "log_tail": log_text},
            managed_map_analysis={"ok": True},
        )

        self.assertEqual("/scan_no_publisher", normalized[0]["reason"])
        self.assertEqual(
            "managed_runtime_graph_probe_timeout_after_lifecycle_active_log",
            normalized[1]["reason"],
        )
        self.assertEqual("/scan_no_publisher", filtering["promoted_downstream_after_lifecycle_active_log"]["reason"])
        self.assertEqual(
            "managed_runtime_graph_probe_timeout_after_lifecycle_active_log",
            filtering["lifecycle_active_graph_secondary_root_cause"]["reason"],
        )
        self.assertIn("/map_once_not_observed", {cause["reason"] for cause in normalized})

    def test_path_generation_success_demotes_managed_wait_root_cause(self) -> None:
        """ComputePathToPose 已生成 path 时，graph wait timeout 不能继续阻断 same-run proof。"""
        root_causes = [
            {"layer": "Managed runtime wait", "reason": "ros2_node_list_timeout"},
        ]

        retained, filtering = HELPER.demote_managed_wait_after_successful_path_generation(
            root_causes,
            path_generation_request={"enabled": True},
            path_generation_result={
                "ok": True,
                "path_generated": True,
                "path_point_count": 14,
                "boundary": "explicit_opt_in_compute_path_to_pose_cli_action_no_motion",
                "fallback_used": True,
                "fallback_mode": "ros2_cli_action_send_goal",
            },
        )

        self.assertEqual([], retained)
        self.assertTrue(filtering["applied"])
        self.assertEqual(
            "compute_path_to_pose_success_demotes_managed_runtime_graph_wait",
            filtering["reason"],
        )
        self.assertEqual("ros2_node_list_timeout", filtering["suppressed_root_causes"][0]["reason"])
        self.assertEqual(14, filtering["path_point_count"])
        self.assertTrue(filtering["path_generation_fallback_used"])
        self.assertEqual("ros2_cli_action_send_goal", filtering["path_generation_fallback_mode"])

    def test_lifecycle_recheck_graph_nodes_feed_planner_readiness(self) -> None:
        """planner lifecycle retry 的 graph visibility 必须补进 path readiness 的节点证据。"""
        observed = HELPER.lifecycle_recheck_observed_node_names(
            {
                "planner_server": {
                    "command_summary": {
                        "graph_visibility": {
                            "observed_node_names": ["/planner_server", "global_costmap/global_costmap"],
                        }
                    }
                },
                "controller_server": {
                    "lifecycle_cli_budget_recovery": {
                        "graph_visibility": {
                            "observed_node_names": ["/lifecycle_manager"],
                        }
                    }
                },
            }
        )

        self.assertIn("/planner_server", observed)
        self.assertIn("/global_costmap/global_costmap", observed)
        self.assertIn("/lifecycle_manager", observed)

    def test_scan_split_classifies_endpoint_qos_and_lidar_runtime_candidate(self) -> None:
        """`/scan` 可见但双 QoS 无样本时，要拆成 endpoint、readback 和 runtime handoff。"""
        publisher_qos = {"reliability": "RELIABLE", "durability": "VOLATILE", "history": "UNKNOWN", "depth": 0}
        subscriber_qos = {"reliability": "BEST_EFFORT", "durability": "VOLATILE", "history": "UNKNOWN", "depth": 0}
        endpoint_inventory = {
            "inventory_observed": True,
            "publisher_count": 1,
            "subscriber_count": 2,
            "publishers": [
                {
                    "node_name": "lidar_driver",
                    "node_namespace": "/",
                    "topic_type": "sensor_msgs/msg/LaserScan",
                    "qos_profile": publisher_qos,
                }
            ],
            "subscribers": [
                {"node_name": "amcl", "node_namespace": "/", "topic_type": "sensor_msgs/msg/LaserScan", "qos_profile": subscriber_qos},
                {
                    "node_name": "o10_scan_probe_child",
                    "node_namespace": "/",
                    "topic_type": "sensor_msgs/msg/LaserScan",
                    "qos_profile": subscriber_qos,
                },
            ],
        }
        best_effort_attempt = {
            "label": "rclpy_best_effort_once",
            "source": "rclpy_subscription",
            "qos_profile": "best_effort",
            "executed": True,
            "observed": False,
            "timed_out": True,
            "returncode": 4,
            "boundary": "rclpy_scan_child_timeout",
            "requested_qos_profile": {"profile": "sensor_data_best_effort", "reliability": "BEST_EFFORT", "durability": "VOLATILE"},
            "endpoint_inventory": endpoint_inventory,
            "child_runtime": {"import_ok": True, "node_created": True, "subscription_created": True, "sample_wait_started": True},
            "import_check": {"attempted": True, "ok": True},
            "sample_timing": {"probe_window_sec": 18.0, "sample_count": 0, "timed_out": True},
        }
        reliable_attempt = {
            **best_effort_attempt,
            "label": "rclpy_reliable_once",
            "qos_profile": "reliable",
            "requested_qos_profile": {"profile": "reliable_volatile", "reliability": "RELIABLE", "durability": "VOLATILE"},
        }
        proof = {
            "localization_signal_freshness": {
                "/scan": {
                    "topic": "/scan",
                    "expected_type": "sensor_msgs/msg/LaserScan",
                    "topic_type": "sensor_msgs/msg/LaserScan",
                    "topic_present": True,
                    "endpoint_inventory_observed": True,
                    "publishers": {"count": 1, "nodes": endpoint_inventory["publishers"]},
                    "subscribers": {"count": 2, "nodes": endpoint_inventory["subscribers"]},
                    "endpoint_inventory": {**endpoint_inventory, "topic": "/scan", "topic_visible": True, "topic_type": "sensor_msgs/msg/LaserScan"},
                    "probe": {
                        "executed": True,
                        "observed": False,
                        "timed_out": True,
                        "classification": "/scan_reliable_and_best_effort_timeout",
                        "attempts": [best_effort_attempt, reliable_attempt],
                        "best_effort_attempt": best_effort_attempt,
                        "reliable_attempt": reliable_attempt,
                        "best_attempt": reliable_attempt,
                    },
                    "sample_timing": {"probe_window_sec": 18.0, "sample_count": 0, "timed_out": True},
                }
            },
            "managed_runtime_log_lifecycle_readback": {
                "clean": True,
                "log_tail": "serial.serialutil.SerialException: device reports readiness to read but returned no data",
            },
        }

        split = HELPER.build_scan_qos_endpoint_readback_split(proof)

        self.assertEqual("trashbot.o10.scan_qos_endpoint_readback_split.v1", split["schema"])
        self.assertEqual("/scan_reliable_and_best_effort_timeout", split["canonical_blocker"])
        self.assertEqual("publisher_endpoint_visible", split["publisher_endpoint_classification"]["classification"])
        self.assertTrue(split["publisher_endpoint_classification"]["publisher_stability"]["stable"])
        self.assertEqual("qos_compatible_readback_timeout_no_samples", split["qos_window_ros_readback_classification"]["classification"])
        qos = split["qos_window_ros_readback_classification"]["requested_vs_endpoint_qos"]
        self.assertTrue(qos["best_effort_compatible"])
        self.assertTrue(qos["reliable_compatible"])
        self.assertFalse(qos["compatibility_risk"])
        self.assertEqual(
            "lidar_runtime_exception_candidate_after_endpoint_qos_readback_split",
            split["lidar_runtime_classification"]["classification"],
        )
        self.assertTrue(split["lidar_runtime_classification"]["runtime_exception"]["observed"])
        self.assertTrue(split["lidar_runtime_classification"]["hardware_handoff_allowed"])
        self.assertTrue(split["lidar_runtime_classification"]["hardware_handoff_requires_vendor_docs"])
        self.assertTrue(split["lidar_runtime_classification"]["does_not_claim_vendor_hardware_root_cause"])
        self.assertEqual(
            "/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout",
            split["primary_split"]["reason"],
        )

    def test_attach_artifact_summaries_promotes_scan_split_primary_root_cause(self) -> None:
        """artifact closeout 主因要使用更细 scan split，同时保留 canonical blocker。"""
        publisher_qos = {"reliability": "RELIABLE"}
        endpoint_inventory = {
            "inventory_observed": True,
            "publisher_count": 1,
            "subscriber_count": 1,
            "publishers": [{"node_name": "lidar_driver", "node_namespace": "/", "topic_type": "sensor_msgs/msg/LaserScan", "qos_profile": publisher_qos}],
            "subscribers": [{"node_name": "amcl", "node_namespace": "/", "topic_type": "sensor_msgs/msg/LaserScan", "qos_profile": {"reliability": "BEST_EFFORT"}}],
        }
        best_effort_attempt = {
            "label": "rclpy_best_effort_once",
            "source": "rclpy_subscription",
            "executed": True,
            "observed": False,
            "timed_out": True,
            "requested_qos_profile": {"reliability": "BEST_EFFORT"},
            "endpoint_inventory": endpoint_inventory,
            "sample_timing": {"sample_count": 0, "timed_out": True},
        }
        reliable_attempt = {
            **best_effort_attempt,
            "label": "rclpy_reliable_once",
            "requested_qos_profile": {"reliability": "RELIABLE"},
        }
        proof = {
            "last_phase": "final",
            "root_causes": [{"layer": "Nav2 sensor input", "reason": "/scan_reliable_and_best_effort_timeout"}],
            "localization_signal_freshness": {
                "/scan": {
                    "topic_present": True,
                    "topic_type": "sensor_msgs/msg/LaserScan",
                    "expected_type": "sensor_msgs/msg/LaserScan",
                    "endpoint_inventory_observed": True,
                    "publishers": {"count": 1, "nodes": endpoint_inventory["publishers"]},
                    "subscribers": {"count": 1, "nodes": endpoint_inventory["subscribers"]},
                    "endpoint_inventory": {**endpoint_inventory, "topic_visible": True, "topic_type": "sensor_msgs/msg/LaserScan"},
                    "probe": {
                        "executed": True,
                        "observed": False,
                        "timed_out": True,
                        "classification": "/scan_reliable_and_best_effort_timeout",
                        "attempts": [best_effort_attempt, reliable_attempt],
                        "best_effort_attempt": best_effort_attempt,
                        "reliable_attempt": reliable_attempt,
                    },
                    "sample_timing": {"sample_count": 0, "timed_out": True},
                }
            },
            "managed_runtime_log_lifecycle_readback": {"log_tail": "serial.serialutil.SerialException: returned no data"},
            "map_lifecycle_preflight": {"map_server_active": True, "amcl_active": True, "node_summaries": {}},
            "map_server_active": True,
            "amcl_active": True,
            "map_once_observed": True,
            "amcl_pose_observed": False,
            "tf_chain_observed": HELPER.default_tf_chain_observed(),
            "tf_chain_diagnostics": {},
            "tf_failure_classification": {"reason": "map_to_odom_dynamic_source_missing"},
            "tf_source_freshness": {"edges": {}},
            "commands": {"path_generation": {"request": {"enabled": True}, "result": {"attempted": False}}},
        }

        HELPER.attach_artifact_summaries(proof, status="blocked_with_root_cause")

        primary = proof["artifact_closeout"]["primary_root_cause"]
        self.assertEqual("/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout", primary["reason"])
        self.assertEqual("/scan_reliable_and_best_effort_timeout", primary["canonical_blocker"])
        self.assertEqual("hardware_after_vendor_doc_review", primary["next_owner"])
        self.assertEqual(primary["reason"], proof["root_causes"][0]["reason"])
        self.assertIn("scan_qos_endpoint_readback_split", proof)

    def test_map_server_presence_recovery_active_case_keeps_motion_false(self) -> None:
        """presence recovered 只能解锁下一层 no-motion readiness，绝不能把控制字段置 true。"""
        map_first = self._visibility_attempt(
            label="first_attempt",
            node_key="map_server",
            node_name="/map_server",
            stdout="active [3]\n",
            graph_node_visible=True,
        )
        proof = self._with_managed_map_yaml(
            self._map_server_visibility_proof(
                graph_nodes=["/map_server", "/amcl", "/lifecycle_manager"],
                map_first=map_first,
                managed_requested=True,
                managed_started=True,
            )
        )
        visibility = HELPER.build_map_server_graph_lifecycle_visibility_summary(proof)

        summary = HELPER.build_map_server_presence_recovery_summary(proof, visibility_summary=visibility)

        self.assertEqual("map_server_lifecycle_active", summary["canonical_classification"])
        self.assertEqual("continue_map_topic_tf_planner_readiness_no_motion", summary["next_step"])
        self.assertTrue(summary["node_presence"]["target_visible"])
        for key in (
            "safe_to_control",
            "publishes_cmd_vel",
            "calls_base_manual",
            "robot_control_executed",
            "route_execution_success",
            "delivery_success",
            "hil_pass",
            "uses_base_uart",
            "path_generation_attempted",
            "path_generated",
            "sends_navigate_to_pose",
        ):
            self.assertFalse(summary["no_motion_invariants"][key], key)

    def test_downstream_probe_skip_anchor_exists_until_lifecycle_clean(self) -> None:
        """lifecycle 未 clean 时主路径必须跳过 `/scan`、`/map`、`/odom` 下游采样。"""
        text = SCRIPT.read_text(encoding="utf-8")

        self.assertIn("downstream_probe_skipped_until_lifecycle_cli_readback_clean", text)
        self.assertIn("scan_probe_skipped_until_lifecycle_cli_readback_clean", text)
        self.assertIn("map_probe_skipped_until_lifecycle_cli_readback_clean", text)
        self.assertIn("odom_probe_skipped_until_lifecycle_cli_readback_clean", text)
        self.assertIn("lifecycle_cli_budget_recovery_retry_summary_sufficient", text)

    def test_map_signal_readiness_splits_publisher_zero_from_sample_timeout(self) -> None:
        """`/map_once_not_observed` 下游必须能继续看出 topic 有无 publisher。"""
        freshness = HELPER.build_localization_signal_freshness(
            generated_at_ms=1_780_000_000_000,
            tf_source_diagnostics={
                "tf_frame_inventory": {"topic_types": {"/map": "nav_msgs/msg/OccupancyGrid"}},
                "topic_endpoint_summaries": {
                    "/map": {
                        "inventory_observed": True,
                        "publisher_count": 0,
                        "subscriber_count": 1,
                        "publishers": [],
                        "subscribers": [{"node_name": "map_consumer", "node_namespace": "/", "topic_type": "nav_msgs/msg/OccupancyGrid"}],
                    }
                },
            },
            tf_source_probe_result={"executed": False},
            topic_list_result={"stdout": "/map [nav_msgs/msg/OccupancyGrid]\n"},
            scan_once={"executed": False, "ok": False},
            map_once={
                "executed": True,
                "ok": False,
                "timed_out": True,
                "returncode": 124,
                "timeout_s": 8.0,
                "stdout": "",
                "stderr": "",
            },
            amcl_pose_once={"executed": False, "ok": False},
            post_initialpose_amcl_pose_once={"executed": False, "ok": False},
            odom_once={"executed": False, "ok": False},
        )

        summary = HELPER.topic_readiness_summary(
            freshness["/map"],
            topic="/map",
            fallback_reason="/map_once_not_observed",
        )

        self.assertTrue(summary["topic_present"])
        self.assertTrue(summary["endpoint_inventory_observed"])
        self.assertEqual(0, summary["publisher_count"])
        self.assertTrue(summary["sample_timeout"])
        self.assertEqual("/map_no_publisher", summary["blocked_reason"])
        self.assertEqual("/map_once_not_observed", summary["legacy_root_cause"])

    def test_downstream_recovery_summary_keeps_target_blockers_separate(self) -> None:
        """07-53 summary 必须一层读出 lifecycle、scan、map、AMCL、TF blocker。"""
        lifecycle = HELPER.build_map_lifecycle_preflight(
            ros2_cli_ok=True,
            lifecycle_active={"map_server": False, "amcl": False},
            lifecycle_results={
                "map_server": {"executed": True, "ok": True, "stdout": "inactive [2]\n", "returncode": 0},
                "amcl": {"executed": True, "ok": True, "stdout": "inactive [2]\n", "returncode": 0},
            },
        )
        proof = {
            "board_source_preflight": {
                "classification": "board_source_preflight_ready",
                "lightweight_cli_ready": True,
                "cli_ready": True,
                "runtime_ready": True,
            },
            "map_lifecycle_preflight": lifecycle,
            "map_server_active": False,
            "amcl_active": False,
            "map_once_observed": False,
            "path_generation_requested": True,
            "path_generation_attempted": False,
            "path_generated": False,
            "path_point_count": 0,
            "localization_signal_freshness": {
                "/scan": {
                    "topic": "/scan",
                    "expected_type": "sensor_msgs/msg/LaserScan",
                    "topic_type": "sensor_msgs/msg/LaserScan",
                    "topic_present": True,
                    "endpoint_inventory_observed": True,
                    "publishers": {"count": 0, "nodes": []},
                    "subscribers": {"count": 1, "nodes": [{"node_name": "amcl"}]},
                    "endpoint_inventory": {"inventory_observed": True, "publisher_count": 0, "subscriber_count": 1},
                    "probe": {"executed": True, "observed": False, "timed_out": True, "classification": "/scan_no_publisher"},
                    "freshness": {"status": "not_observed"},
                    "sample_timing": {"sample_count": 0, "timed_out": True},
                },
                "/map": {
                    "topic": "/map",
                    "expected_type": "nav_msgs/msg/OccupancyGrid",
                    "topic_type": "nav_msgs/msg/OccupancyGrid",
                    "topic_present": True,
                    "endpoint_inventory_observed": True,
                    "publishers": {"count": 1, "nodes": [{"node_name": "map_server"}]},
                    "subscribers": {"count": 0, "nodes": []},
                    "endpoint_inventory": {"inventory_observed": True, "publisher_count": 1, "subscriber_count": 0},
                    "probe": {"executed": True, "observed": False, "timed_out": True},
                    "freshness": {"status": "not_observed"},
                },
                "/amcl_pose": {
                    "topic_present": False,
                    "publishers": {"count": 0, "nodes": []},
                    "subscribers": {"count": 0, "nodes": []},
                    "probe": {"executed": False, "observed": False},
                    "freshness": {"status": "not_observed"},
                },
                "/tf": {
                    "topic": "/tf",
                    "topic_present": False,
                    "publishers": {"count": 0, "nodes": []},
                    "subscribers": {"count": 0, "nodes": []},
                    "probe": {"executed": True, "observed": False},
                    "freshness": {"status": "not_observed"},
                },
                "/tf_static": {
                    "topic": "/tf_static",
                    "topic_present": True,
                    "publishers": {"count": 1, "nodes": [{"node_name": "static_tf"}]},
                    "subscribers": {"count": 0, "nodes": []},
                    "probe": {"executed": True, "observed": False},
                    "freshness": {"status": "not_observed"},
                },
            },
            "tf_source_freshness": {"edges": {}},
            "tf_chain_observed": HELPER.default_tf_chain_observed(),
            "tf_chain_diagnostics": {},
            "tf_failure_classification": {"map_to_base_link": "blocked_by_missing_map_to_odom", "reason": "map_to_odom_dynamic_source_missing"},
            "root_causes": [{"layer": "Nav2 map input", "reason": "/map_once_not_observed"}],
            "commands": {"path_generation": {"request": {"enabled": True}, "result": {"attempted": False}}},
        }

        summary = HELPER.build_downstream_recovery_summary(proof)

        self.assertTrue(summary["readiness_inputs"]["board_source_preflight_ready"])
        self.assertTrue(summary["readiness_inputs"]["lightweight_cli_ready"])
        self.assertTrue(summary["blocking_conditions"]["map_lifecycle_preflight_map_server_and_amcl_inactive"])
        self.assertTrue(summary["blocking_conditions"]["amcl_lifecycle_not_active"])
        self.assertTrue(summary["blocking_conditions"]["/scan_no_publisher"])
        self.assertTrue(summary["blocking_conditions"]["/map_once_not_observed"])
        self.assertTrue(summary["blocking_conditions"]["/tf_topic_missing"])
        self.assertEqual("/map_sample_timeout", summary["map"]["topic_sample"]["blocked_reason"])
        self.assertEqual("/map_once_not_observed", summary["map"]["legacy_root_cause"])
        self.assertFalse(summary["ready_for_planner_only_path_gate"])
        self.assertFalse(summary["no_motion_invariants"]["publishes_cmd_vel"])

    def test_tf_source_probe_reports_runtime_boundary_when_rclpy_unavailable(self) -> None:
        """TF source probe 即使不能跑 rclpy，也必须给 executed=true 的明确失败边界。"""
        cli_probe = {
            "executed": True,
            "ok": True,
            "param_probe_ok": False,
            "node_info_observed": True,
            "tf_inventory_observed": True,
            "params": {},
            "publishers": [{"topic": "/amcl_pose", "type": "geometry_msgs/msg/PoseWithCovarianceStamped"}],
            "subscribers": [{"topic": "/scan", "type": "sensor_msgs/msg/LaserScan"}],
            "topic_types": {"/tf": "tf2_msgs/msg/TFMessage", "/tf_static": "tf2_msgs/msg/TFMessage"},
            "topic_endpoint_summaries": {
                "/tf": {"publishers": [], "subscribers": [], "publisher_count": 1, "subscriber_count": 0, "inventory_observed": True},
                "/tf_static": {"publishers": [], "subscribers": [], "publisher_count": 1, "subscriber_count": 0, "inventory_observed": True},
            },
            "dynamic_edges": [],
            "static_edges": [],
            "dynamic_transforms": [],
            "static_transforms": [],
            "command_statuses": {"rclpy_graph": 0, "tf": 0, "tf_static": 0},
            "elapsed_ms": 700,
            "boundary": "cli_amcl_inventory_observed_topic_list_amcl_node_info_tf_info_tf_static_info",
            "fallback_used": True,
            "fallback_boundary": "cli_amcl_inventory_observed_topic_list_amcl_node_info_tf_info_tf_static_info",
            "param_probe_boundary": "cli_amcl_param_probe_unavailable_tf_broadcast_failed_global_frame_id_failed_odom_frame_id_failed_base_frame_id_failed",
            "probe_mode": "ros2_cli_fallback",
        }
        with mock.patch.object(HELPER, "collect_amcl_cli_probe", return_value=cli_probe) as fallback_mock:
            result, diagnostics = HELPER.collect_tf_source_diagnostics(
                HELPER.parse_args([]),
                ros2_cli_ready=True,
                rclpy_runtime_ready=False,
                board_source_preflight_result={"classification": "board_source_preflight_rclpy_import_timeout"},
                amcl_pose_result={"stdout": "header:\n  frame_id: map\n"},
            )

        self.assertTrue(result["executed"])
        self.assertTrue(result["ok"])
        self.assertEqual("cli_amcl_inventory_observed_topic_list_amcl_node_info_tf_info_tf_static_info", result["boundary"])
        self.assertEqual("board_source_preflight_rclpy_import_timeout", result["blocked_by_board_source_classification"])
        fallback_mock.assert_called_once()
        self.assertEqual("amcl_param_probe_failed", diagnostics["amcl_tf_root_cause"])
        self.assertTrue(diagnostics["tf_topics_observed"]["/tf"])
        self.assertEqual(
            "board_source_preflight_rclpy_import_timeout",
            diagnostics["tf_source_root_cause_detail"]["probe_boundary"],
        )

    def test_path_generation_gate_reports_not_attempted_root_cause(self) -> None:
        """localization/TF gate 未 ready 时，path_generation 必须 requested 但 not attempted。"""
        proof = {
            "path_generation_requested": True,
            "path_generation_attempted": False,
            "path_generated": False,
            "path_point_count": 0,
            "path_generation_boundary": "path_generation_blocked_by_localization_not_ready",
            "planner_server_ready_for_path_generation": True,
            "amcl_readiness_summary": {"ready": False},
            "tf_readiness_summary": {"ready": False},
            "root_causes": [
                {"layer": "Localization TF", "reason": "map_to_odom_dynamic_source_missing"},
            ],
            "commands": {
                "path_generation": {
                    "request": {"enabled": True},
                    "result": {
                        "attempted": False,
                        "boundary": "path_generation_blocked_by_localization_not_ready",
                    },
                }
            },
        }

        gate = HELPER.build_path_generation_gate_summary(proof)

        self.assertTrue(gate["requested"])
        self.assertFalse(gate["attempted"])
        self.assertFalse(gate["generated"])
        self.assertEqual("path_generation_blocked_by_localization_not_ready", gate["blocked_reason"])
        self.assertEqual("map_to_odom_dynamic_source_missing", gate["localization_root_causes"][0]["reason"])

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
            "amcl_readiness_summary",
            "tf_readiness_summary",
            "path_generation_gate",
            "artifact_closeout",
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
