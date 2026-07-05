#!/usr/bin/env python3
"""upper_robot_api free-roam 控制合同测试。"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_PATH = SCRIPT_DIR / "upper_robot_api.py"


def load_upper_robot_api_module():
    """按文件路径加载脚本，避免测试依赖 ROS2 package 安装状态。"""
    spec = importlib.util.spec_from_file_location("upper_robot_api_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("upper_robot_api.py module spec was not created")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UpperRobotApiFreeRoamTest(unittest.TestCase):
    def test_upper_robot_api_exposes_api_health_route_constant(self) -> None:
        """PC 先用轻量 /api/health 判断 API 活性，不能只依赖重 /api/status。"""
        module = load_upper_robot_api_module()

        self.assertEqual(module.ROUTE_PATHS["health"], "/api/health")

    def test_base_status_get_skips_direct_t130_by_default(self) -> None:
        """普通 summary 刷新不能用 GET /api/base/status 抢 UART；轮速采样走显式接口。"""
        module = load_upper_robot_api_module()
        original_request = module.request_base_feedback_once
        original_env = module.os.environ.pop(module.BASE_STATUS_DIRECT_FEEDBACK_ENV, None)

        def fail_if_called(*_args, **_kwargs):
            raise AssertionError("GET /api/base/status must not send direct T=130 by default")

        module.request_base_feedback_once = fail_if_called
        try:
            with tempfile.TemporaryDirectory() as td:
                api = module.UpperRobotApi(
                    camera_base_url="http://127.0.0.1:8088",
                    base_port="/dev/null",
                    base_baudrate=115200,
                    max_speed=0.12,
                    feedback_samples_artifact_path=str(Path(td) / "base_feedback_samples_latest.json"),
                )

                payload = api.base_status()

            self.assertEqual(payload["schema"], "trashbot.upper_robot_api.v1.base_status")
            self.assertFalse(payload["direct_feedback_on_get_enabled"])
            self.assertEqual(payload["explicit_feedback_request_endpoint"], "/api/base/feedback-request")
            self.assertEqual(payload["explicit_feedback_samples_endpoint"], "/api/base/feedback-samples")
            self.assertFalse(payload["feedback_readback"]["request"]["attempted"])
            self.assertEqual(payload["feedback_readback"]["request"]["reason"], "base_status_get_lightweight_no_direct_t130")
            self.assertIn("lightweight GET /api/base/status", payload["feedback_readback"]["feedback_ack"]["reason"])
            self.assertFalse(payload["feedback_readback"]["sends_commands"])
            self.assertFalse(payload["sends_commands"])
            self.assertFalse(payload["sends_motion_commands"])
            self.assertFalse(payload["robot_control_executed"])
        finally:
            module.request_base_feedback_once = original_request
            if original_env is None:
                module.os.environ.pop(module.BASE_STATUS_DIRECT_FEEDBACK_ENV, None)
            else:
                module.os.environ[module.BASE_STATUS_DIRECT_FEEDBACK_ENV] = original_env

    def test_bridge_feedback_debug_summary_reads_log_tail_only(self) -> None:
        """bridge JSONL 可能很大；状态读取只能扫尾部，避免 base/status 超时或 OOM。"""
        module = load_upper_robot_api_module()
        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "wave_rover_feedback_debug.jsonl"
            with log_path.open("w", encoding="utf-8") as handle:
                for index in range(30000):
                    handle.write(json.dumps({"source": "noise", "index": index}) + "\n")
                handle.write(json.dumps({
                    "source": "wave_rover_uart_t1001",
                    "vendor_frame": {"L": 12, "R": 13, "r": 0.1, "p": 0.2, "y": 0.3, "v": 12.4},
                }) + "\n")

            summary = module.summarize_bridge_feedback_debug_log(str(log_path), max_lines=8)

        self.assertEqual(summary["status"] if "status" in summary else summary["artifact"]["status"], "loaded")
        self.assertLess(summary["artifact"]["bytes_scanned"], summary["artifact"]["bytes_read"])
        self.assertEqual(summary["artifact"]["tail_line_count"], 8)
        self.assertEqual(summary["t1001_observed_count"], 1)
        self.assertTrue(summary["wheel_feedback_lr_nonzero_proven"])
        self.assertEqual(summary["latest_frame"]["L"], 12)
        self.assertFalse(summary["sends_commands"])

    def test_ros_manual_control_reports_bridge_feedback_as_motion_window(self) -> None:
        """ROS 手控由 bridge 持有 UART 时，PC 仍要看到本次窗口的 T1001 帧数。"""
        module = load_upper_robot_api_module()
        original_debug_log_path = module.DEFAULT_BRIDGE_FEEDBACK_DEBUG_LOG_PATH
        original_ros_transaction = module.manual_motion_ros_cmd_vel_transaction

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            log_path = root / "wave_rover_feedback_debug.jsonl"
            feedback_artifact_path = root / "base_feedback_samples_latest.json"
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "source": "wave_rover_uart_t1001",
                                "vendor_frame": {"L": 0, "R": 0, "r": 0.0, "p": 0.0, "y": "null", "v": 12.3},
                            }
                        ),
                        json.dumps(
                            {
                                "source": "wave_rover_uart_t1001",
                                "vendor_frame": {"L": 0, "R": 0, "r": 1.25, "p": 0.1, "y": "null", "v": 12.3},
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            def fake_ros_transaction(*, port, baudrate, command, pulse_ms):
                """测试只验证反馈合并；ROS 发布本身用结构化成功桩替代。"""
                return {
                    "mode": "ros_cmd_vel_bridge",
                    "command_result": {"ok": True, "command": command, "pulse_ms": pulse_ms},
                    "stop_result": {"ok": True, "command": {"linear_x": 0.0, "angular_z": 0.0}},
                    "feedback_during_motion": module.skipped_manual_feedback_payload(
                        port,
                        baudrate,
                        "ros_cmd_vel_path_uses_bridge_feedback_not_direct_uart",
                    ),
                    "feedback_after_stop": module.skipped_manual_feedback_payload(
                        port,
                        baudrate,
                        "ros_cmd_vel_path_uses_bridge_feedback_not_direct_uart",
                    ),
                    "serial_session_error": None,
                    "blocked_base_uart": port,
                }

            module.DEFAULT_BRIDGE_FEEDBACK_DEBUG_LOG_PATH = str(log_path)
            module.manual_motion_ros_cmd_vel_transaction = fake_ros_transaction
            try:
                api = module.UpperRobotApi(
                    camera_base_url="http://127.0.0.1:8088",
                    base_port="/dev/ttyS5",
                    base_baudrate=115200,
                    max_speed=0.12,
                    feedback_samples_artifact_path=str(feedback_artifact_path),
                )

                result = asyncio.run(
                    api.manual_control(
                        {
                            "direction": "forward",
                            "command_mode": "ros",
                            "speed": 0.08,
                            "duration_ms": 120,
                        }
                    )
                )
            finally:
                module.DEFAULT_BRIDGE_FEEDBACK_DEBUG_LOG_PATH = original_debug_log_path
                module.manual_motion_ros_cmd_vel_transaction = original_ros_transaction

        feedback = result["feedback_during_motion"]
        self.assertEqual(feedback["schema"], "trashbot.upper_robot_api.v1.base_manual_bridge_feedback")
        self.assertEqual(feedback["feedback_source"], "esp32_bridge_feedback_debug_log")
        self.assertEqual(len(feedback["t1001_feedback_frames"]), 2)
        self.assertTrue(result["feedback_ack"]["t1001_observed"])
        self.assertEqual(result["manual_wheel_feedback_summary"]["matched_frame_count"], 2)
        self.assertFalse(result["wheel_feedback_lr_nonzero_proven"])
        self.assertTrue(result["imu_attitude_delta_observed"])
        self.assertEqual(result["motion_signal_source"], "imu_attitude_delta")
        self.assertEqual(result["manual_feedback_samples_latest"]["t1001_observed_count"], 1)
        self.assertEqual(result["manual_feedback_samples_latest"]["samples"][0]["t1001_feedback_frame_count"], 2)

    def test_lidar_driver_diagnostics_artifact_flattens_status_for_pc(self) -> None:
        """driver 写出的诊断状态必须被 API 展平成 PC 可直接显示的字段。"""
        module = load_upper_robot_api_module()
        with tempfile.TemporaryDirectory() as td:
            diagnostics_path = Path(td) / "lidar_driver_diagnostics.json"
            diagnostics_path.write_text(json.dumps({
                "schema": "trashbot.o1.lidar_driver_diagnostics.v1",
                "state": "running",
                "diagnosis": {
                    "status": "serial_open_but_no_bytes",
                    "next_action_plain": "LiDAR 串口已打开且启动命令已写入，但没有读到任何字节。",
                },
                "serial": {
                    "serial_port": "/dev/ttyACM0",
                    "serial_baudrate": 230400,
                    "start_command_written": True,
                    "read_call_count": 24,
                    "empty_read_count": 24,
                    "bytes_read_total": 0,
                    "packet_count_total": 0,
                },
                "runtime": {
                    "published_scan_count": 0,
                    "published_raw_packet_count": 0,
                },
            }, ensure_ascii=False), encoding="utf-8")

            latest = module.read_lidar_driver_diagnostics_artifact(str(diagnostics_path))

        self.assertEqual(latest["status"], "loaded")
        self.assertEqual(latest["diagnosis_status"], "serial_open_but_no_bytes")
        self.assertIn("没有读到任何字节", latest["next_action_plain"])
        self.assertEqual(latest["serial"]["bytes_read_total"], 0)

    def test_lidar_scan_proof_refresh_uses_driver_diagnostics_preview(self) -> None:
        """雷达刷新默认使用轻量 diagnostics 点位，避免现场再启动 ROS2 CLI collector。"""
        module = load_upper_robot_api_module()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            diagnostics_path = root / "lidar_driver_diagnostics.json"
            artifact_path = root / "lidar_scan_proof_latest.json"
            diagnostics_path.write_text(json.dumps({
                "schema": "trashbot.o1.lidar_driver_diagnostics.v1",
                "generated_at_ms": module.now_ms(),
                "state": "running",
                "diagnosis": {
                    "status": "scan_published",
                    "next_action_plain": "LiDAR driver 已发布 /scan。",
                },
                "runtime": {
                    "published_scan_count": 8,
                    "published_raw_packet_count": 64,
                    "last_scan_range_count": 3,
                },
                "serial": {
                    "packet_count_total": 64,
                    "bytes_read_total": 2048,
                },
                "scan_preview": {
                    "scan_preview_points": [
                        {"x_m": 1.0, "y_m": 0.0, "range_m": 1.0, "angle_rad": 0.0, "frame_id": "laser_frame", "source_index": 0},
                    ],
                    "scan_preview_point_count": 1,
                    "scan_preview_source_point_count": 3,
                    "scan_preview_frame_id": "laser_frame",
                    "scan_preview_source": "lidar_driver_diagnostics.last_scan_preview",
                },
            }, ensure_ascii=False), encoding="utf-8")
            lifecycle_status = {
                "status": "loaded",
                "running": True,
                "driver_diagnostics_path": str(diagnostics_path),
                "latest_result": {
                    "driver_diagnostics_path": str(diagnostics_path),
                    "frame_id": "laser_frame",
                    "static_tf": "base_link -> laser_frame",
                },
            }

            result = module.run_lidar_driver_diagnostics_scan_proof_refresh(
                artifact_path=str(artifact_path),
                lifecycle_status=lifecycle_status,
            )
            latest_status, latest = module.read_lidar_scan_proof_latest_artifact(str(artifact_path))

        self.assertEqual(result["command_result"]["mode"], "lidar_driver_diagnostics_refresh")
        self.assertTrue(result["command_result"]["ok"])
        self.assertEqual(latest_status, 200)
        self.assertEqual(latest["scan_preview_point_count"], 1)
        self.assertEqual(latest["scan_preview_frame_id"], "laser_frame")
        proof = latest["latest_result"]["proof"]
        self.assertTrue(proof["all_required_observations_observed"])
        self.assertFalse(latest["latest_result"]["topic_reads"]["attempted"])

    def test_start_unlocks_motion_even_when_mapping_readiness_is_degraded(self) -> None:
        """相机或雷达不 ready 只能降级建图 readiness，不能阻止低速自由移动。"""
        module = load_upper_robot_api_module()
        calls: list[dict[str, object]] = []

        def fake_param_sequence(action: str, *, enable_motion: bool = False, mapping_active: bool = True, artifact_path: str = ""):
            calls.append({
                "action": action,
                "enable_motion": enable_motion,
                "mapping_active": mapping_active,
            })
            return {
                "mode": "free_roam_param_sequence",
                "action": action,
                "motion_unlock_requested": bool(action == "start" and enable_motion),
                "executed": True,
                "ok": True,
                "touched_parameters": [
                    "operator_confirmed",
                    "mapping_active",
                    "stop_available",
                    "external_stop_requested",
                    "motion_hil_unlocked",
                    "enable_cmd_vel_publish",
                ],
                "blocked_parameters_not_touched": ["cmd_vel_topic"],
            }

        original_param_sequence = module.run_free_roam_param_sequence
        module.run_free_roam_param_sequence = fake_param_sequence
        try:
            with tempfile.TemporaryDirectory() as td:
                api = module.UpperRobotApi(
                    camera_base_url="http://127.0.0.1:8088",
                    base_port="/dev/null",
                    base_baudrate=115200,
                    max_speed=0.12,
                    free_roam_autonomy_artifact_path=str(Path(td) / "free_roam.json"),
                )
                api.free_roam_motion_readiness = lambda: {
                    "ready": True,
                    "missing": [],
                    "free_move_ready": True,
                    "motion_without_radar_allowed": True,
                    "free_move_without_camera_allowed": True,
                    "mapping_readiness": {
                        "ready": False,
                        "missing": ["camera_first_frame_not_observed", "radar_scan_proof_not_fresh"],
                        "requires_camera_first_frame": True,
                        "requires_fresh_radar_scan": True,
                        "free_move_allowed_when_mapping_not_ready": True,
                    },
                }
                api.free_roam_autonomy_latest = lambda: (200, {"decision_state": "stopping"})

                payload = api.free_roam_autonomy_control(
                    "start",
                    {"confirm_operator_safety": True, "confirm_mapping_active": True},
                )

            self.assertEqual(calls, [{
                "action": "start",
                "enable_motion": True,
                "mapping_active": False,
            }])
            self.assertEqual(payload["status"], "requested")
            self.assertTrue(payload["motion_unlock_requested"])
            self.assertFalse(payload["does_not_set_motion_unlock"])
            self.assertTrue(payload["publishes_cmd_vel"])
            self.assertTrue(payload["sends_motion_commands"])
            self.assertTrue(payload["mapping_active_requested"])
            self.assertFalse(payload["mapping_active_applied"])
            self.assertFalse(payload["sensor_readiness"]["mapping_readiness"]["ready"])
            self.assertEqual(payload["blocked_parameters_not_touched"], ["cmd_vel_topic"])
            self.assertFalse(payload["robot_control_executed"])
            self.assertFalse(payload["safe_to_control"])
        finally:
            module.run_free_roam_param_sequence = original_param_sequence

    def test_start_uses_free_move_ready_not_mapping_ready(self) -> None:
        """旧调用可能把整体 ready 写成 false；start 必须优先看 free_move_ready。"""
        module = load_upper_robot_api_module()
        calls: list[dict[str, object]] = []

        def fake_param_sequence(action: str, *, enable_motion: bool = False, mapping_active: bool = True, artifact_path: str = ""):
            calls.append({
                "action": action,
                "enable_motion": enable_motion,
                "mapping_active": mapping_active,
            })
            return {
                "mode": "free_roam_param_sequence",
                "action": action,
                "motion_unlock_requested": bool(action == "start" and enable_motion),
                "executed": True,
                "ok": True,
                "touched_parameters": ["operator_confirmed", "motion_hil_unlocked", "enable_cmd_vel_publish"],
                "blocked_parameters_not_touched": ["cmd_vel_topic"],
            }

        original_param_sequence = module.run_free_roam_param_sequence
        module.run_free_roam_param_sequence = fake_param_sequence
        try:
            with tempfile.TemporaryDirectory() as td:
                api = module.UpperRobotApi(
                    camera_base_url="http://127.0.0.1:8088",
                    base_port="/dev/null",
                    base_baudrate=115200,
                    max_speed=0.12,
                    free_roam_autonomy_artifact_path=str(Path(td) / "free_roam.json"),
                )
                api.free_roam_motion_readiness = lambda: {
                    "ready": False,
                    "missing": [],
                    "free_move_ready": True,
                    "mapping_readiness": {
                        "ready": False,
                        "missing": ["camera_first_frame_not_observed"],
                        "free_move_allowed_when_mapping_not_ready": True,
                    },
                }
                api.free_roam_autonomy_latest = lambda: (200, {"decision_state": "stopping"})

                payload = api.free_roam_autonomy_control(
                    "start",
                    {"confirm_operator_safety": True, "confirm_mapping_active": True},
                )

            self.assertEqual(calls, [{
                "action": "start",
                "enable_motion": True,
                "mapping_active": False,
            }])
            self.assertEqual(payload["status"], "requested")
            self.assertTrue(payload["free_move_start_ready"])
            self.assertEqual(payload["free_move_blocked_reasons"], [])
            self.assertFalse(payload["mapping_readiness_ready"])
            self.assertEqual(payload["mapping_blocked_reasons"], ["camera_first_frame_not_observed"])
            self.assertTrue(payload["motion_unlock_requested"])
            self.assertTrue(payload["publishes_cmd_vel"])
        finally:
            module.run_free_roam_param_sequence = original_param_sequence

    def test_start_waits_for_runtime_artifact_after_real_param_load(self) -> None:
        """真实 ros2 param load 成功后，start 响应要短等状态机进入运行态，避免读到旧 stopping。"""
        module = load_upper_robot_api_module()
        calls: list[dict[str, object]] = []
        latest_calls: list[str] = []

        def fake_param_sequence(action: str, *, enable_motion: bool = False, mapping_active: bool = True, artifact_path: str = ""):
            calls.append({
                "action": action,
                "enable_motion": enable_motion,
                "mapping_active": mapping_active,
            })
            return {
                "mode": "free_roam_param_sequence",
                "action": action,
                "motion_unlock_requested": bool(action == "start" and enable_motion),
                "executed": True,
                "ok": True,
                "results": [
                    {
                        "write_strategy": "ros2_param_load",
                        "executed": True,
                        "ok": True,
                    }
                ],
                "touched_parameters": [
                    "operator_confirmed",
                    "mapping_active",
                    "stop_available",
                    "external_stop_requested",
                    "motion_hil_unlocked",
                    "enable_cmd_vel_publish",
                ],
                "blocked_parameters_not_touched": ["cmd_vel_topic"],
            }

        original_param_sequence = module.run_free_roam_param_sequence
        module.run_free_roam_param_sequence = fake_param_sequence
        try:
            with tempfile.TemporaryDirectory() as td:
                api = module.UpperRobotApi(
                    camera_base_url="http://127.0.0.1:8088",
                    base_port="/dev/null",
                    base_baudrate=115200,
                    max_speed=0.12,
                    free_roam_autonomy_artifact_path=str(Path(td) / "free_roam.json"),
                )
                api.free_roam_motion_readiness = lambda: {
                    "ready": True,
                    "missing": [],
                    "free_move_ready": True,
                    "mapping_readiness": {"ready": False, "missing": ["camera_first_frame_not_observed"]},
                }

                def fake_latest():
                    latest_calls.append("latest")
                    return 200, {
                        "decision_state": "running",
                        "cmd_vel_publish_enabled": True,
                    }

                api.free_roam_autonomy_latest = fake_latest

                payload = api.free_roam_autonomy_control(
                    "start",
                    {"confirm_operator_safety": True, "confirm_mapping_active": False},
                )

            self.assertEqual(calls, [{
                "action": "start",
                "enable_motion": True,
                "mapping_active": False,
            }])
            self.assertGreaterEqual(len(latest_calls), 2)
            self.assertEqual(payload["status"], "requested")
            self.assertTrue(payload["start_runtime_wait"]["waited"])
            self.assertTrue(payload["start_runtime_wait"]["ok"])
            self.assertEqual(payload["start_runtime_wait"]["decision_state"], "running")
            self.assertTrue(payload["latest_cmd_vel_publish_enabled"])
            self.assertEqual(payload["latest_decision_state"], "running")
            self.assertTrue(payload["publishes_cmd_vel"])
        finally:
            module.run_free_roam_param_sequence = original_param_sequence

    def test_missing_free_roam_node_is_started_before_param_load(self) -> None:
        """自由移动节点缺失时，上位机 API 要先托管启动 runtime，再写参数。"""
        module = load_upper_robot_api_module()
        probes = [
            {"available": False, "status": "node_not_found"},
            {"available": True, "status": "available"},
        ]
        starts: list[str] = []
        original_probe = module.free_roam_param_probe
        original_node_probe = module.free_roam_node_list_probe
        original_start = module.start_managed_free_roam_runtime
        original_sleep = module.time.sleep
        module.free_roam_param_probe = lambda: probes.pop(0) if probes else {"available": True, "status": "available"}
        module.free_roam_node_list_probe = lambda: {"observed": False, "status": "not_observed", "nodes": []}
        module.start_managed_free_roam_runtime = lambda artifact_path: starts.append(artifact_path) or {
            "mode": "managed_free_roam_runtime_start",
            "executed": True,
            "ok": True,
            "pid": 123,
        }
        module.time.sleep = lambda _seconds: None
        try:
            result = module.ensure_free_roam_runtime_for_param_load("/tmp/free_roam.json")
        finally:
            module.free_roam_param_probe = original_probe
            module.free_roam_node_list_probe = original_node_probe
            module.start_managed_free_roam_runtime = original_start
            module.time.sleep = original_sleep

        self.assertEqual(starts, ["/tmp/free_roam.json"])
        self.assertTrue(result["available"])
        self.assertTrue(result["started_by_api"])
        self.assertEqual(result["status"], "started_and_param_available")

    def test_param_sequence_reports_runtime_unavailable_after_managed_start(self) -> None:
        """托管启动后参数服务仍不可用时，失败原因必须直接指向 runtime。"""
        module = load_upper_robot_api_module()
        original_ensure = module.ensure_free_roam_runtime_for_param_load
        module.ensure_free_roam_runtime_for_param_load = lambda _artifact_path: {
            "mode": "free_roam_runtime_ensure",
            "status": "unavailable_after_managed_start",
            "available": False,
            "started_by_api": True,
            "start": {"executed": True, "ok": True},
        }
        try:
            result = module.run_free_roam_param_sequence(
                "start",
                enable_motion=True,
                mapping_active=False,
                artifact_path="/tmp/free_roam.json",
            )
        finally:
            module.ensure_free_roam_runtime_for_param_load = original_ensure

        self.assertFalse(result["ok"])
        self.assertTrue(result["executed"])
        self.assertEqual(result["reason"], "free_roam_runtime_unavailable_after_managed_start")
        self.assertEqual(result["blocked_parameters_not_touched"], [
            "motion_hil_unlocked",
            "enable_cmd_vel_publish",
            "cmd_vel_topic",
        ])

    def test_runtime_lidar_snapshot_allows_mapping_when_scan_proof_is_stale(self) -> None:
        """雷达 proof 旧时，free-roam runtime 的实时 /scan 快照仍可作为建图 readiness。"""
        module = load_upper_robot_api_module()
        calls: list[dict[str, object]] = []

        def fake_param_sequence(action: str, *, enable_motion: bool = False, mapping_active: bool = True, artifact_path: str = ""):
            calls.append({
                "action": action,
                "enable_motion": enable_motion,
                "mapping_active": mapping_active,
            })
            return {
                "mode": "free_roam_param_sequence",
                "action": action,
                "motion_unlock_requested": bool(action == "start" and enable_motion),
                "executed": True,
                "ok": True,
                "touched_parameters": [
                    "operator_confirmed",
                    "mapping_active",
                    "stop_available",
                    "external_stop_requested",
                    "motion_hil_unlocked",
                    "enable_cmd_vel_publish",
                ],
                "blocked_parameters_not_touched": ["cmd_vel_topic"],
            }

        original_param_sequence = module.run_free_roam_param_sequence
        module.run_free_roam_param_sequence = fake_param_sequence
        try:
            with tempfile.TemporaryDirectory() as td:
                artifact_path = Path(td) / "free_roam.json"
                artifact_path.write_text(json.dumps({
                    "schema": "trashbot.free_roam_autonomy.runtime.v1",
                    "artifact_only": True,
                    "cmd_vel_publish_enabled": False,
                    "snapshot": {
                        "lidar_age_s": 0.04,
                        "lidar_min_distance_m": 0.72,
                        "mapping_active": False,
                    },
                    "decision": {
                        "schema": "trashbot.free_roam_autonomy.decision.v1",
                        "state": "stopping",
                        "gates": [
                            {
                                "id": "lidar_fresh",
                                "state": "ready",
                                "evidence": "雷达距离 0.72m，延迟 0.04s",
                            },
                        ],
                    },
                }, ensure_ascii=False), encoding="utf-8")
                api = module.UpperRobotApi(
                    camera_base_url="http://127.0.0.1:8088",
                    base_port="/dev/null",
                    base_baudrate=115200,
                    max_speed=0.12,
                    free_roam_autonomy_artifact_path=str(artifact_path),
                )
                api.camera_motion_readiness = lambda: {
                    "ready": True,
                    "missing": [],
                    "status": "ready",
                    "source_readiness": "first_frame_observed",
                }
                api.radar_status = lambda: {
                    "lifecycle_running": True,
                    "lifecycle_state": "running",
                    "latest_scan_proof_fresh": False,
                    "continuous_window_observed": False,
                    "continuity_blocked_reasons": ["latest_scan_proof_stale"],
                }

                readiness = api.free_roam_motion_readiness()
                payload = api.free_roam_autonomy_control(
                    "start",
                    {"confirm_operator_safety": True, "confirm_mapping_active": True},
                )

            self.assertTrue(readiness["mapping_readiness"]["ready"])
            self.assertEqual(readiness["mapping_readiness"]["missing"], [])
            self.assertTrue(readiness["radar"]["runtime_scan_ready"])
            self.assertFalse(readiness["radar"]["proof_ready"])
            self.assertEqual(readiness["radar"]["runtime_scan"]["source"], "free_roam_runtime_scan_snapshot")
            self.assertEqual(calls, [{
                "action": "start",
                "enable_motion": True,
                "mapping_active": True,
            }])
            self.assertTrue(payload["mapping_active_requested"])
            self.assertTrue(payload["mapping_active_applied"])
            self.assertTrue(payload["sensor_readiness"]["mapping_readiness"]["ready"])
            self.assertTrue(payload["publishes_cmd_vel"])
            self.assertFalse(payload["robot_control_executed"])
            self.assertFalse(payload["safe_to_control"])
        finally:
            module.run_free_roam_param_sequence = original_param_sequence

    def test_latest_is_artifact_only_and_does_not_call_camera_or_radar_status(self) -> None:
        """latest 必须快速读 artifact；相机 HTTP 或雷达完整 status 慢时不能拖死该入口。"""
        module = load_upper_robot_api_module()
        with tempfile.TemporaryDirectory() as td:
            artifact_path = Path(td) / "free_roam.json"
            scan_proof_path = Path(td) / "scan_proof.json"
            artifact_path.write_text(json.dumps({
                "schema": "trashbot.free_roam_autonomy.runtime.v1",
                "artifact_only": True,
                "cmd_vel_publish_enabled": False,
                "snapshot": {
                    "lidar_age_s": 0.04,
                    "lidar_min_distance_m": 0.72,
                    "mapping_active": False,
                },
                "decision": {
                    "schema": "trashbot.free_roam_autonomy.decision.v1",
                    "state": "stopping",
                    "reason": "现场请求停止",
                    "stop_required": True,
                    "gates": [],
                },
            }, ensure_ascii=False), encoding="utf-8")
            api = module.UpperRobotApi(
                camera_base_url="http://127.0.0.1:8088",
                base_port="/dev/null",
                base_baudrate=115200,
                max_speed=0.12,
                free_roam_autonomy_artifact_path=str(artifact_path),
                lidar_scan_proof_artifact_path=str(scan_proof_path),
            )

            def fail_camera():
                raise AssertionError("free_roam_autonomy_latest must not call camera_motion_readiness")

            def fail_radar():
                raise AssertionError("free_roam_autonomy_latest must not call radar_status")

            api.camera_motion_readiness = fail_camera
            api.radar_status = fail_radar

            http_status, payload = api.free_roam_autonomy_latest()

        self.assertEqual(http_status, 200)
        self.assertTrue(payload["free_roam_runtime_artifact_proven"])
        self.assertTrue(payload["free_move_start_ready"])
        self.assertTrue(payload["motion_without_radar_allowed"])
        self.assertEqual(payload["camera_readiness"]["status"], "deferred_to_camera_health_endpoint")
        self.assertEqual(payload["camera_readiness"]["endpoint"], module.ROUTE_PATHS["camera_health"])
        self.assertTrue(payload["radar_readiness"]["runtime_scan_ready"])
        self.assertFalse(payload["radar_readiness"]["proof_ready"])
        self.assertEqual(payload["radar_readiness"]["lifecycle_running"], "not_checked_by_free_roam_latest")
        self.assertFalse(payload["free_roam_mapping_start_ready"])
        self.assertEqual(payload["free_roam_mapping_start_missing_reasons"], ["camera_first_frame_not_observed"])


if __name__ == "__main__":
    unittest.main()
