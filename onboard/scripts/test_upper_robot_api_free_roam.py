#!/usr/bin/env python3
"""upper_robot_api free-roam 控制合同测试。"""

from __future__ import annotations

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

    def test_start_unlocks_motion_even_when_mapping_readiness_is_degraded(self) -> None:
        """相机或雷达不 ready 只能降级建图 readiness，不能阻止低速自由移动。"""
        module = load_upper_robot_api_module()
        calls: list[dict[str, object]] = []

        def fake_param_sequence(action: str, *, enable_motion: bool = False, mapping_active: bool = True):
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

        def fake_param_sequence(action: str, *, enable_motion: bool = False, mapping_active: bool = True):
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

        def fake_param_sequence(action: str, *, enable_motion: bool = False, mapping_active: bool = True):
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

    def test_runtime_lidar_snapshot_allows_mapping_when_scan_proof_is_stale(self) -> None:
        """雷达 proof 旧时，free-roam runtime 的实时 /scan 快照仍可作为建图 readiness。"""
        module = load_upper_robot_api_module()
        calls: list[dict[str, object]] = []

        def fake_param_sequence(action: str, *, enable_motion: bool = False, mapping_active: bool = True):
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
