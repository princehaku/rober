import unittest
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_nav.route_proof_summary import (
    build_route_proof_summary,
    summarize_checkpoints_from_visual_gate,
)


class RouteProofSummaryTest(unittest.TestCase):
    def test_build_route_proof_summary_normalizes_partial_coverage(self):
        summary = build_route_proof_summary(
            total_checkpoints=4,
            covered_checkpoints=2,
            gate_status="waiting_camera_frame",
            last_block_reason="visual gate waiting for camera frame at checkpoint 2",
        )
        self.assertEqual(summary["coverage_rate"], 0.5)
        self.assertEqual(summary["covered_checkpoints"], 2)
        self.assertEqual(summary["total_checkpoints"], 4)
        self.assertEqual(summary["missing_checkpoints"], [2, 3])
        self.assertEqual(summary["gate_status"], "waiting_camera_frame")
        self.assertIn("checkpoint 2", summary["last_block_reason"])

    def test_build_route_proof_summary_forces_passed_when_fully_covered(self):
        summary = build_route_proof_summary(
            total_checkpoints=2,
            covered_checkpoints=9,
            gate_status="waiting_camera_frame",
            last_block_reason="stale reason",
            missing_checkpoints=[1],
        )
        self.assertEqual(summary["coverage_rate"], 1.0)
        self.assertEqual(summary["covered_checkpoints"], 2)
        self.assertEqual(summary["missing_checkpoints"], [])
        self.assertEqual(summary["gate_status"], "passed")
        self.assertEqual(summary["last_block_reason"], "")

    def test_summarize_checkpoints_uses_first_failing_checkpoint(self):
        summary = summarize_checkpoints_from_visual_gate(
            [
                {"index": 0, "status": "passed", "detail": "ok"},
                {
                    "index": 1,
                    "status": "missing_keyframe",
                    "detail": "visual gate missing keyframe for checkpoint 1",
                },
                {"index": 2, "status": "passed", "detail": "not reachable in practice"},
            ]
        )
        self.assertEqual(summary["coverage_rate"], 0.3333)
        self.assertEqual(summary["covered_checkpoints"], 1)
        self.assertEqual(summary["total_checkpoints"], 3)
        self.assertEqual(summary["missing_checkpoints"], [1, 2])
        self.assertEqual(summary["gate_status"], "missing_keyframe")
        self.assertIn("checkpoint 1", summary["last_block_reason"])

    def test_partial_coverage_can_keep_passed_gate_when_not_blocked(self):
        summary = build_route_proof_summary(
            total_checkpoints=3,
            covered_checkpoints=1,
            gate_status="passed",
            last_block_reason="",
        )
        self.assertEqual(summary["coverage_rate"], 0.3333)
        self.assertEqual(summary["covered_checkpoints"], 1)
        self.assertEqual(summary["total_checkpoints"], 3)
        self.assertEqual(summary["missing_checkpoints"], [1, 2])
        self.assertEqual(summary["gate_status"], "passed")
        self.assertEqual(summary["last_block_reason"], "")

    def test_build_route_proof_summary_ignores_missing_indexes_below_coverage(self):
        summary = build_route_proof_summary(
            total_checkpoints=4,
            covered_checkpoints=2,
            gate_status="waiting_camera_frame",
            last_block_reason="visual gate waiting for camera frame at checkpoint 2",
            missing_checkpoints=[0, 3, 7],
        )
        self.assertEqual(summary["coverage_rate"], 0.5)
        self.assertEqual(summary["covered_checkpoints"], 2)
        self.assertEqual(summary["total_checkpoints"], 4)
        self.assertEqual(summary["missing_checkpoints"], [3])
        self.assertEqual(summary["gate_status"], "waiting_camera_frame")
        self.assertIn("checkpoint 2", summary["last_block_reason"])


if __name__ == "__main__":
    unittest.main()
