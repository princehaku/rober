import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_vision.elevator_opencv_baseline import (  # noqa: E402
    DOOR_CLOSED,
    DOOR_OPEN,
    DOOR_UNCERTAIN,
    INSIDE,
    OUTSIDE,
    SAFE_TO_EXIT,
    SCHEMA,
    UNSAFE_TO_EXIT,
    analyze_grayscale_matrix,
    elevator_taxonomy,
    evaluate_manifest,
)


class ElevatorOpenCvBaselineTest(unittest.TestCase):
    def test_taxonomy_exposes_required_labels_and_not_proven_boundary(self):
        taxonomy = elevator_taxonomy()

        self.assertEqual(taxonomy["schema"], SCHEMA)
        self.assertIn("door_state", taxonomy["labels"])
        self.assertIn("inside_outside", taxonomy["labels"])
        self.assertIn("safe_to_exit", taxonomy["labels"])
        self.assertIn("floor_display", taxonomy["roi_names"])
        self.assertTrue(taxonomy["sample_requirements"]["real_image_directory_required_for_field_eval"])
        self.assertIn("taxonomy_classes", taxonomy)
        self.assertIn("floor_target_positive", taxonomy["taxonomy_classes"])
        self.assertIn("quality_gate_defaults", taxonomy)
        self.assertIn("real_camera_elevator_recognition", taxonomy["not_proven"])

    def test_rule_baseline_detects_open_inside_and_safe_fixture(self):
        matrix = _fixture_matrix(panel=55, gap=180, floor=210, exit_path=170)

        result = analyze_grayscale_matrix(
            matrix,
            sample_id="open_inside_safe",
            image_ref="fixture://open_inside_safe",
            target_floor="3",
            expected_floor="3",
        )

        self.assertEqual(result["door_state"], DOOR_OPEN)
        self.assertEqual(result["inside_outside"], INSIDE)
        self.assertEqual(result["target_floor_candidate"], "3")
        self.assertEqual(result["safe_to_exit"], SAFE_TO_EXIT)
        self.assertGreaterEqual(result["confidence"], 0.58)
        self.assertEqual(result["uncertain_reasons"], [])
        self.assertIn("real_safe_exit", result["not_proven"])

    def test_rule_baseline_detects_closed_outside_and_unsafe_fixture(self):
        matrix = _fixture_matrix(panel=170, gap=165, floor=170, exit_path=150)

        result = analyze_grayscale_matrix(
            matrix,
            sample_id="closed_outside",
            image_ref="fixture://closed_outside",
            target_floor="3",
        )

        self.assertEqual(result["door_state"], DOOR_CLOSED)
        self.assertEqual(result["inside_outside"], OUTSIDE)
        self.assertEqual(result["safe_to_exit"], UNSAFE_TO_EXIT)
        self.assertIn("door_not_open:closed", result["uncertain_reasons"])
        self.assertIn("target_floor_not_confirmed", result["uncertain_reasons"])

    def test_rule_baseline_fails_closed_when_gap_delta_is_ambiguous(self):
        matrix = _fixture_matrix(panel=120, gap=95, floor=120, exit_path=120)

        result = analyze_grayscale_matrix(
            matrix,
            sample_id="ambiguous",
            image_ref="fixture://ambiguous",
        )

        self.assertEqual(result["door_state"], DOOR_UNCERTAIN)
        self.assertIn("door_gap_delta_uncertain", "\n".join(result["uncertain_reasons"]))

    def test_manifest_eval_reads_real_image_directory_and_summarizes_fp_fn(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_pgm(root / "open_safe.pgm", _fixture_matrix(panel=55, gap=180, floor=210, exit_path=170))
            _write_pgm(root / "closed_outside.pgm", _fixture_matrix(panel=170, gap=165, floor=170, exit_path=150))
            _write_pgm(root / "ambiguous.pgm", _fixture_matrix(panel=120, gap=95, floor=120, exit_path=120))
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_image_manifest.v1",
                        "image_dir": str(root),
                        "samples": [
                            {
                                "sample_id": "open_safe",
                                "image": "open_safe.pgm",
                                "target_floor": "3",
                                "expected_floor": "3",
                                "expected_door_state": "open",
                                "expected_inside_outside": "inside",
                                "expected_safe_to_exit": "safe",
                                "taxonomy_tags": ["door_open_positive", "floor_target_positive"],
                            },
                            {
                                "sample_id": "closed_outside",
                                "image": "closed_outside.pgm",
                                "target_floor": "3",
                                "expected_door_state": "closed",
                                "expected_inside_outside": "outside",
                                "expected_safe_to_exit": "unsafe",
                            },
                            {
                                "sample_id": "ambiguous",
                                "image": "ambiguous.pgm",
                                "expected_door_state": "open",
                                "expected_safe_to_exit": "safe",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = evaluate_manifest(str(manifest_path))
            cli = subprocess.run(
                [sys.executable, "-m", "ros2_trashbot_vision.elevator_opencv_baseline", str(manifest_path)],
                cwd=str(PACKAGE_ROOT),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(cli.returncode, 0, cli.stderr)
        self.assertEqual(summary["evaluated_count"], 3)
        self.assertEqual(summary["confusion"]["door_state"]["tp"], 1)
        self.assertEqual(summary["confusion"]["door_state"]["tn"], 1)
        self.assertEqual(summary["confusion"]["door_state"]["uncertain"], 1)
        self.assertEqual(summary["confusion"]["safe_to_exit"]["tp"], 1)
        self.assertEqual(summary["confusion"]["safe_to_exit"]["tn"], 1)
        self.assertEqual(summary["operator_summary"]["uncertain_total"], 2)
        self.assertTrue(summary["quality_metrics"]["software_guard_pass"])
        self.assertFalse(summary["quality_metrics"]["field_eval_ready"])
        self.assertEqual(summary["sample_coverage"]["counts"]["door_open_positive"], 2)
        self.assertEqual(summary["sample_coverage"]["counts"]["floor_target_positive"], 1)
        self.assertEqual(summary["sample_coverage"]["image_kinds"]["fixture"], 3)
        self.assertFalse(summary["sample_coverage"]["field_minimum_met"])
        self.assertTrue(summary["acceptance_gates"]["software_guard"]["pass"])
        self.assertFalse(summary["acceptance_gates"]["field_eval"]["pass"])
        self.assertIn("real_floor_ocr", summary["not_proven"])
        self.assertEqual(json.loads(cli.stdout)["evaluated_count"], 3)


def _fixture_matrix(*, panel: int, gap: int, floor: int, exit_path: int):
    # 画面大小固定为 20x20，便于 ROI 边界和 rule 阈值在测试中稳定复现。
    matrix = [[panel for _ in range(20)] for _ in range(20)]
    for y in range(2, 18):
        for x in range(9, 11):
            matrix[y][x] = gap
    for y in range(0, 3):
        for x in range(8, 13):
            matrix[y][x] = floor
    for y in range(14, 18):
        for x in range(6, 15):
            matrix[y][x] = exit_path
    return matrix


def _write_pgm(path: Path, matrix):
    height = len(matrix)
    width = len(matrix[0])
    pixels = " ".join(str(value) for row in matrix for value in row)
    path.write_text(f"P2\n# elevator fixture\n{width} {height}\n255\n{pixels}\n", encoding="ascii")


if __name__ == "__main__":
    unittest.main()
