import tempfile
import unittest
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_nav.route_utils import (
    load_waypoints_from_csv,
    validate_waypoints,
)


class RouteCsvToYamlTest(unittest.TestCase):
    def test_load_waypoints_from_csv_parses_numeric_fields(self):
        csv_content = (
            "index,sec,nanosec,x,y,z,qx,qy,qz,qw,frame\n"
            "0,1,2,1.25,2.5,0.0,0.0,0.0,0.1,0.99,000.jpg\n"
        )
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "route.csv"
            csv_path.write_text(csv_content, encoding="utf-8")
            waypoints = load_waypoints_from_csv(str(csv_path), "map")

        self.assertEqual(len(waypoints), 1)
        wp = waypoints[0]
        self.assertEqual(wp["frame_id"], "map")
        self.assertEqual(wp["x"], 1.25)
        self.assertEqual(wp["y"], 2.5)
        self.assertEqual(wp["qz"], 0.1)
        self.assertEqual(wp["qw"], 0.99)

    def test_load_waypoints_from_csv_ignores_image_frame_column_for_pose_frame_id(self):
        csv_content = (
            "index,sec,nanosec,x,y,z,qx,qy,qz,qw,frame\n"
            "0,1,2,1.25,2.5,0.0,0.0,0.0,0.1,0.99,000.jpg\n"
        )
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "route.csv"
            csv_path.write_text(csv_content, encoding="utf-8")
            waypoints = load_waypoints_from_csv(str(csv_path), "map")

        self.assertEqual(waypoints[0]["frame_id"], "map")

    def test_load_waypoints_from_csv_uses_explicit_frame_id_column(self):
        csv_content = (
            "index,sec,nanosec,frame_id,x,y,z,qx,qy,qz,qw,frame\n"
            "0,1,2,odom,1.25,2.5,0.0,0.0,0.0,0.1,0.99,000.jpg\n"
        )
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "route.csv"
            csv_path.write_text(csv_content, encoding="utf-8")
            waypoints = load_waypoints_from_csv(str(csv_path), "map")

        self.assertEqual(waypoints[0]["frame_id"], "odom")

    def test_load_waypoints_from_csv_falls_back_when_frame_id_is_blank(self):
        csv_content = (
            "index,sec,nanosec,frame_id,x,y,z,qx,qy,qz,qw,frame\n"
            "0,1,2,   ,1.25,2.5,0.0,0.0,0.0,0.1,0.99,000.jpg\n"
        )
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "route.csv"
            csv_path.write_text(csv_content, encoding="utf-8")
            waypoints = load_waypoints_from_csv(str(csv_path), "map")

        self.assertEqual(waypoints[0]["frame_id"], "map")

    def test_load_waypoints_from_csv_rejects_bad_numeric_values(self):
        csv_content = (
            "index,sec,nanosec,x,y,z,qx,qy,qz,qw,frame\n"
            "0,1,2,not-a-number,2.5,0.0,0.0,0.0,0.1,0.99,000.jpg\n"
        )
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "route.csv"
            csv_path.write_text(csv_content, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "line 2"):
                load_waypoints_from_csv(str(csv_path), "map")

    def test_validate_waypoints_rejects_empty_route(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            validate_waypoints([], "fixed_route.yaml")

    def test_validate_waypoints_rejects_missing_required_pose_fields(self):
        with self.assertRaisesRegex(ValueError, "missing required field"):
            validate_waypoints([{"x": 1.0, "qw": 1.0}], "fixed_route.yaml")

    def test_validate_waypoints_rejects_non_mapping_waypoint(self):
        with self.assertRaisesRegex(ValueError, "must be a mapping"):
            validate_waypoints(["bad"], "fixed_route.yaml")

    def test_validate_waypoints_returns_numeric_waypoints(self):
        waypoints = validate_waypoints(
            [{"frame_id": "map", "x": "1.0", "y": "2.0", "qw": "1.0"}],
            "fixed_route.yaml",
        )

        self.assertEqual(
            waypoints[0],
            {
                "frame_id": "map",
                "x": 1.0,
                "y": 2.0,
                "z": 0.0,
                "qx": 0.0,
                "qy": 0.0,
                "qz": 0.0,
                "qw": 1.0,
            },
        )


if __name__ == "__main__":
    unittest.main()
