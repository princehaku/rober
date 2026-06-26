#!/usr/bin/env python3
"""upper_robot_api free-roam 控制合同测试。"""

from __future__ import annotations

import importlib.util
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


if __name__ == "__main__":
    unittest.main()
