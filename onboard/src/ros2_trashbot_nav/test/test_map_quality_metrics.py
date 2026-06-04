import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_nav.map_quality_metrics import (  # noqa: E402
    PROOF_STATUS,
    SCHEMA,
    evaluate_map_quality,
)


class MapQualityMetricsTest(unittest.TestCase):
    def test_evaluate_map_quality_reports_coverage_and_waypoint_failures(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            map_yaml, waypoints = _write_map_fixture(root)

            report = evaluate_map_quality(str(map_yaml), waypoint_path=str(waypoints))

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["proof_status"], PROOF_STATUS)
        self.assertEqual(report["metrics"]["width"], 5)
        self.assertEqual(report["metrics"]["height"], 5)
        self.assertEqual(report["metrics"]["free_cells"], 20)
        self.assertEqual(report["metrics"]["occupied_cells"], 2)
        self.assertEqual(report["metrics"]["unknown_cells"], 3)
        self.assertEqual(report["metrics"]["coverage_area_m2"], 20.0)
        self.assertEqual(report["metrics"]["unknown_ratio"], 0.12)
        self.assertTrue(report["save_load_consistency"]["consistent"])

        summary = report["waypoint_reachability"]["summary"]
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["reachable"], 1)
        self.assertEqual(summary["blocked"], 1)
        self.assertEqual(summary["unknown"], 1)
        self.assertEqual(summary["out_of_bounds"], 1)
        self.assertEqual(summary["reachable_ratio"], 0.25)
        self.assertFalse(report["quality_gates"]["software_guard_pass"])
        self.assertIn("real_nav2_scan_map_consumption", report["not_proven"])
        self.assertEqual(
            {item["status"] for item in report["waypoint_reachability"]["items"]},
            {"free", "occupied", "unknown", "out_of_bounds"},
        )

    def test_map_quality_cli_outputs_json_and_nonzero_when_gate_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            map_yaml, waypoints = _write_map_fixture(root)
            cli = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "ros2_trashbot_nav.map_quality_metrics",
                    str(map_yaml),
                    "--waypoints",
                    str(waypoints),
                ],
                cwd=str(PACKAGE_ROOT),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(cli.returncode, 1, cli.stderr)
        payload = json.loads(cli.stdout)
        self.assertEqual(payload["schema"], SCHEMA)
        self.assertFalse(payload["quality_gates"]["software_guard_pass"])


def _write_map_fixture(root: Path):
    # P2 PGM 便于测试直观看到 free/unknown/occupied 分布。
    pgm = root / "map.pgm"
    pixels = [
        [254, 254, 205, 0, 254],
        [254, 254, 205, 0, 254],
        [254, 254, 254, 254, 254],
        [205, 254, 254, 254, 254],
        [254, 254, 254, 254, 254],
    ]
    pgm.write_text(
        "P2\n# nav2 map quality fixture\n5 5\n255\n"
        + "\n".join(" ".join(str(value) for value in row) for row in pixels)
        + "\n",
        encoding="ascii",
    )
    yaml_path = root / "map.yaml"
    yaml_path.write_text(
        "\n".join(
            [
                "image: map.pgm",
                "resolution: 1.0",
                "origin: [0.0, 0.0, 0.0]",
                "negate: 0",
                "occupied_thresh: 0.65",
                "free_thresh: 0.196",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    waypoint_path = root / "waypoints.json"
    waypoint_path.write_text(
        json.dumps(
            {
                "waypoints": [
                    {"frame_id": "map", "x": 0.5, "y": 0.5, "qw": 1.0},
                    {"frame_id": "map", "x": 3.5, "y": 4.5, "qw": 1.0},
                    {"frame_id": "map", "x": 2.5, "y": 4.5, "qw": 1.0},
                    {"frame_id": "map", "x": 9.0, "y": 9.0, "qw": 1.0},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return yaml_path, waypoint_path


if __name__ == "__main__":
    unittest.main()
