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


if __name__ == "__main__":
    unittest.main()
