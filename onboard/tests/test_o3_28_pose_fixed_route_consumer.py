"""O3 fresh 28-pose fixed-route consumer 的离线单测。"""

from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "o3_28_pose_fixed_route_consumer.py"
SPEC = importlib.util.spec_from_file_location("o3_28_pose_fixed_route_consumer", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)


def fresh_source_summary() -> dict:
    """构造最小 fresh 28-pose artifact，锁定本轮 consumer 的输入合同。"""
    poses = []
    for index in range(28):
        poses.append(
            {
                "frame_id": "map",
                "source_index": index,
                "stamp": {"sec": 1783883494, "nanosec": 997523160},
                "x": 0.07615115310756959 + index * 0.025,
                "y": 0.2500000037252903,
                "z": 0.0,
                "qx": 0.0,
                "qy": 0.0,
                "qz": 0.0,
                "qw": 1.0,
            }
        )

    # 顶层和 proof 双写 safety false，是为了防止 wrapper 与原始 proof 口径分叉。
    false_fields = {
        "route_execution_success": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "robot_control_executed": False,
    }
    proof = {
        **false_fields,
        "status": "nav2_no_motion_path_generation_runtime_observed",
        "evidence_type": "robot_runtime_material",
        "path_generated": True,
        "path_generation_attempted": True,
        "path_generation_requested": True,
        "path_generation_boundary": "explicit_opt_in_compute_path_to_pose_cli_action_no_motion",
        "path_generation_service_name": "/compute_path_to_pose",
        "fresh_live_artifact_used": True,
        "historic_21_57_artifact_reused_as_live_proof": False,
        "path_point_count": 28,
        "path_structured_pose_count": 28,
        "path_structured_poses": poses,
        "blocked_reason": "expected_21_structured_pose_count_not_reproduced_current_live_returned_28_after_map_bounds_adaptation",
        "proof_boundary": "software_proof_o3_o1_strict_no_motion_fresh_structured_path_material_only",
        "path_goal_request": {
            "goal_frame_id": "map",
            "goal_x": 0.8,
            "goal_y": 0.2500000037252903,
            "goal_yaw": 0.0,
        },
    }
    return {
        **false_fields,
        "schema": "trashbot.live_full_structured_path_capture_summary.v1",
        "path_generated": True,
        "path_point_count": 28,
        "path_structured_pose_count": 28,
        "proof": proof,
    }


class O328PoseFixedRouteConsumerTests(unittest.TestCase):
    """只验证 artifact consumer，不启动 ROS2、不打开串口、不发运动命令。"""

    def write_source(self, root: Path, payload: dict) -> Path:
        """测试用 source summary 保持独立，避免污染 sprint artifact。"""
        path = root / "source_summary.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_validates_fresh_28_pose_source_contract(self) -> None:
        """fresh/live/28-pose 条件全部满足时返回规范化 pose。"""
        poses = HELPER.validate_source_summary(fresh_source_summary())

        self.assertEqual(28, len(poses))
        self.assertEqual(0, poses[0]["source_index"])
        self.assertEqual(27, poses[-1]["source_index"])
        self.assertEqual("map", poses[0]["frame_id"])
        self.assertEqual({"sec": 1783883494, "nanosec": 997523160}, poses[0]["stamp"])

    def test_rejects_historic_21_57_reuse_as_live_proof(self) -> None:
        """旧 21:57 partial stdout-tail 不能重新伪装成 primary fresh proof。"""
        payload = fresh_source_summary()
        payload["proof"]["historic_21_57_artifact_reused_as_live_proof"] = True

        with self.assertRaises(HELPER.ConsumerInputError):
            HELPER.validate_source_summary(payload)

    def test_rejects_missing_or_reindexed_pose(self) -> None:
        """structured pose 必须完整且 source_index 连续，不能补造或重排。"""
        payload = fresh_source_summary()
        payload["proof"]["path_structured_poses"][7]["source_index"] = 99

        with self.assertRaises(HELPER.ConsumerInputError):
            HELPER.validate_source_summary(payload)

    def test_writes_summary_jsonl_and_csv_with_false_safety_fields(self) -> None:
        """输出的 summary/JSONL/CSV 都围绕同一 route_intent_id 和 28 条 pose。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = self.write_source(root, fresh_source_summary())
            output_dir = root / "out"

            summary = HELPER.write_outputs(source_path, output_dir, "2026-07-12T20:02:00Z")

            self.assertTrue(summary["fresh_28_pose_structured_material_consumed"])
            self.assertFalse(summary["historic_21_57_artifact_primary_source"])
            self.assertEqual(28, summary["path_structured_pose_count"])
            self.assertFalse(summary["route_execution_success"])
            self.assertFalse(summary["delivery_success"])
            self.assertFalse(summary["hil_pass"])
            self.assertFalse(summary["safe_to_control"])
            self.assertFalse(summary["publishes_cmd_vel"])
            self.assertFalse(summary["calls_base_manual"])
            self.assertFalse(summary["uses_base_uart"])
            self.assertFalse(summary["robot_control_executed"])

            replay_events = [
                json.loads(line)
                for line in (output_dir / HELPER.REPLAY_NAME).read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(28, len(replay_events))
            self.assertTrue(all(event["event"] == "structured_pose" for event in replay_events))
            self.assertEqual(0, replay_events[0]["source_index"])
            self.assertEqual(27, replay_events[-1]["source_index"])

            with (output_dir / HELPER.ROUTE_CSV_NAME).open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(28, len(rows))
            self.assertEqual("0", rows[0]["source_index"])
            self.assertEqual("27", rows[-1]["source_index"])
            self.assertEqual(HELPER.ROUTE_INTENT_ID, rows[0]["route_intent_id"])
            self.assertEqual(HELPER.TASK_ID, rows[-1]["task_id"])


if __name__ == "__main__":
    unittest.main()
