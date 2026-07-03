import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ONBOARD_ROOT = Path(__file__).resolve().parents[3]
UPPER_ROBOT_API_PATH = ONBOARD_ROOT / "scripts" / "upper_robot_api.py"


def load_upper_robot_api_module():
    """测试直接加载上位机脚本，避免为了纯 JSON 目标点折叠启动 HTTP 服务。"""
    spec = importlib.util.spec_from_file_location("upper_robot_api_for_test", UPPER_ROBOT_API_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("upper_robot_api.py import spec missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UpperRobotApiMapPreviewTargetTest(unittest.TestCase):
    def test_route_target_prefers_path_preview_endpoint_when_path_points_exist(self):
        module = load_upper_robot_api_module()
        overlay = {
            "path_preview_points": [
                {"x": 0.0, "y": 0.0, "frame_id": "map", "source_index": 0},
                {"x": 1.2, "y": -0.4, "frame_id": "map", "source_index": 8},
            ],
        }

        target = module.route_target_overlay_from_path_preview(overlay)

        self.assertEqual(target["route_target_state"], "path_preview_goal_observed")
        self.assertEqual(target["route_target_source"], "path_preview_points")
        self.assertEqual(target["target"]["x"], 1.2)
        self.assertEqual(target["target"]["y"], -0.4)
        self.assertEqual(target["target"]["source_index"], 8)

    def test_goal_artifact_target_keeps_recent_nav2_goal_visible_without_path_points(self):
        module = load_upper_robot_api_module()
        with tempfile.TemporaryDirectory() as td:
            artifact = Path(td) / "nav2_goal_execution_latest.json"
            artifact.write_text(
                json.dumps(
                    {
                        "latest_result": {
                            "status": "goal_succeeded",
                            "goal_request": {
                                "frame_id": "map",
                                "x": 0.8,
                                "y": 0.05,
                                "yaw": 0.0,
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            target = module.nav2_goal_target_overlay_from_artifact(str(artifact))

        self.assertEqual(target["route_target_state"], "latest_goal_request_observed")
        self.assertEqual(target["route_target_source"], "latest_goal_request")
        self.assertEqual(target["target"]["x"], 0.8)
        self.assertEqual(target["target"]["y"], 0.05)
        self.assertEqual(target["target"]["frame_id"], "map")


if __name__ == "__main__":
    unittest.main()
