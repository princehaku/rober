from pathlib import Path
import sys
import tempfile
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_behavior.delivery_navigation import (
    find_waypoint_pose,
    load_waypoint_file,
)


class DeliveryNavigationTest(unittest.TestCase):
    def test_find_waypoint_pose_by_name(self):
        data = {
            "waypoints": [
                {
                    "name": "trash_station",
                    "type": 2,
                    "x": 1.25,
                    "y": 2.5,
                    "z": 0.0,
                    "orientation_z": 0.1,
                    "orientation_w": 0.99,
                }
            ]
        }

        pose = find_waypoint_pose(data, "trash_station")

        self.assertEqual(pose["frame_id"], "map")
        self.assertEqual(pose["x"], 1.25)
        self.assertEqual(pose["y"], 2.5)
        self.assertEqual(pose["qz"], 0.1)
        self.assertEqual(pose["qw"], 0.99)

    def test_find_waypoint_pose_falls_back_to_first_bin_when_target_is_blank(self):
        data = {
            "waypoints": [
                {"name": "patrol_a", "type": 0, "x": 0.0, "y": 0.0},
                {"name": "bin_a", "type": 2, "x": 3.0, "y": 4.0},
            ]
        }

        pose = find_waypoint_pose(data, "")

        self.assertEqual(pose["name"], "bin_a")
        self.assertEqual(pose["x"], 3.0)
        self.assertEqual(pose["y"], 4.0)

    def test_find_waypoint_pose_rejects_missing_target(self):
        data = {"waypoints": [{"name": "bin_a", "type": 2, "x": 3.0, "y": 4.0}]}

        with self.assertRaisesRegex(ValueError, "delivery target not found"):
            find_waypoint_pose(data, "missing")

    def test_load_waypoint_file_reads_yaml(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "waypoints.yaml"
            path.write_text(
                "waypoints:\n"
                "  - name: bin_a\n"
                "    type: 2\n"
                "    x: 3.0\n"
                "    y: 4.0\n",
                encoding="utf-8",
            )

            data = load_waypoint_file(path)

        self.assertEqual(data["waypoints"][0]["name"], "bin_a")


if __name__ == "__main__":
    unittest.main()
