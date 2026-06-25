"""free_roam_autonomy 的离线安全状态机测试。"""

import json
import subprocess
import sys
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_nav.free_roam_autonomy import (  # noqa: E402
    FreeRoamAutonomyController,
    FreeRoamConfig,
    FreeRoamSnapshot,
    STATE_AVOIDING,
    STATE_COMPLETED,
    STATE_LOCKED,
    STATE_RUNNING,
    STATE_TURNING_FOR_COVERAGE,
    build_free_roam_decision,
)


class FreeRoamAutonomyTest(unittest.TestCase):
    """自动扫图策略先证明 fail-closed，再证明受限自由跑动。"""

    def test_default_snapshot_is_locked_and_zero_velocity(self) -> None:
        """缺少现场事实时必须锁住，不能生成任何运动速度。"""
        decision = build_free_roam_decision({})

        self.assertEqual(decision["state"], STATE_LOCKED)
        self.assertEqual(decision["linear_x_mps"], 0.0)
        self.assertEqual(decision["angular_z_radps"], 0.0)
        self.assertTrue(decision["stop_required"])
        self.assertIn("地图记录未启动", {gate["evidence"] for gate in decision["gates"]})

    def test_clear_gates_drive_forward_at_bounded_speed(self) -> None:
        """所有门禁通过时只允许保守低速直行，给建图覆盖创造真实运动。"""
        controller = FreeRoamAutonomyController(FreeRoamConfig(max_speed_mps=0.11))

        decision = controller.update(
            FreeRoamSnapshot(
                operator_confirmed=True,
                mapping_active=True,
                stop_available=True,
                lidar_min_distance_m=1.2,
                lidar_age_s=0.1,
                map_free_cells=10,
                map_unknown_ratio=0.8,
                elapsed_s=3.0,
                now_s=100.0,
            )
        )

        self.assertEqual(decision.state, STATE_RUNNING)
        self.assertEqual(decision.linear_x_mps, 0.11)
        self.assertEqual(decision.angular_z_radps, 0.0)
        self.assertFalse(decision.stop_required)
        self.assertTrue(all(gate.state in {"ready", "not_proven"} for gate in decision.gates))

    def test_close_obstacle_turns_in_place_without_forward_motion(self) -> None:
        """雷达看到近障碍时不能继续正向速度，只能原地换向避让。"""
        controller = FreeRoamAutonomyController(FreeRoamConfig(obstacle_stop_distance_m=0.5))

        decision = controller.update(
            FreeRoamSnapshot(
                operator_confirmed=True,
                mapping_active=True,
                stop_available=True,
                lidar_min_distance_m=0.2,
                lidar_age_s=0.1,
                map_free_cells=20,
                map_unknown_ratio=0.7,
                elapsed_s=4.0,
                now_s=100.0,
            )
        )

        self.assertEqual(decision.state, STATE_AVOIDING)
        self.assertEqual(decision.linear_x_mps, 0.0)
        self.assertNotEqual(decision.angular_z_radps, 0.0)
        self.assertFalse(decision.stop_required)

    def test_stalled_coverage_turns_to_search_new_space(self) -> None:
        """地图覆盖不增长时像扫地机一样换向，而不是一直撞同一条线。"""
        controller = FreeRoamAutonomyController(FreeRoamConfig(coverage_stall_timeout_s=2.0))
        snapshot = FreeRoamSnapshot(
            operator_confirmed=True,
            mapping_active=True,
            stop_available=True,
            lidar_min_distance_m=1.0,
            lidar_age_s=0.1,
            map_free_cells=30,
            map_unknown_ratio=0.6,
            elapsed_s=5.0,
        )

        first = controller.update(snapshot.__class__(**{**snapshot.__dict__, "now_s": 100.0}))
        stalled = controller.update(snapshot.__class__(**{**snapshot.__dict__, "now_s": 103.0}))

        self.assertEqual(first.state, STATE_RUNNING)
        self.assertEqual(stalled.state, STATE_TURNING_FOR_COVERAGE)
        self.assertEqual(stalled.linear_x_mps, 0.0)
        self.assertNotEqual(stalled.angular_z_radps, 0.0)

    def test_runtime_or_target_coverage_completes_with_stop(self) -> None:
        """超时或覆盖达标都必须输出 completed + 零速度。"""
        timeout_decision = build_free_roam_decision(
            {
                "operator_confirmed": True,
                "mapping_active": True,
                "stop_available": True,
                "lidar_min_distance_m": 1.0,
                "lidar_age_s": 0.1,
                "elapsed_s": 60.0,
            }
        )
        covered_decision = build_free_roam_decision(
            {
                "operator_confirmed": True,
                "mapping_active": True,
                "stop_available": True,
                "lidar_min_distance_m": 1.0,
                "lidar_age_s": 0.1,
                "map_unknown_ratio": 0.1,
            }
        )

        for decision in (timeout_decision, covered_decision):
            self.assertEqual(decision["state"], STATE_COMPLETED)
            self.assertEqual(decision["linear_x_mps"], 0.0)
            self.assertEqual(decision["angular_z_radps"], 0.0)
            self.assertTrue(decision["stop_required"])

    def test_stale_lidar_locks_before_motion(self) -> None:
        """雷达旧数据不能被当成所见即所得的实时障碍信息。"""
        decision = build_free_roam_decision(
            {
                "operator_confirmed": True,
                "mapping_active": True,
                "stop_available": True,
                "lidar_min_distance_m": 2.0,
                "lidar_age_s": 9.0,
            }
        )

        self.assertEqual(decision["state"], STATE_LOCKED)
        self.assertEqual(decision["linear_x_mps"], 0.0)
        self.assertIn("雷达距离已过期", {gate["evidence"] for gate in decision["gates"]})

    def test_cli_defaults_to_locked_json(self) -> None:
        """console script 的模块入口默认也 fail closed，便于上车前 dry run。"""
        module_path = PACKAGE_ROOT / "ros2_trashbot_nav" / "free_roam_autonomy.py"

        result = subprocess.run(
            [sys.executable, str(module_path)],
            check=True,
            text=True,
            capture_output=True,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(payload["schema"], "trashbot.free_roam_autonomy.decision.v1")
        self.assertEqual(payload["state"], STATE_LOCKED)
        self.assertEqual(payload["linear_x_mps"], 0.0)


if __name__ == "__main__":
    unittest.main()
