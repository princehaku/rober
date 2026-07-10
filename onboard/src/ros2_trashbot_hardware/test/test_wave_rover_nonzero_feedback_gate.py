import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout


PACKAGE_SRC = Path(__file__).resolve().parents[1]
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))


def _gate_module():
    return importlib.import_module("ros2_trashbot_hardware.wave_rover_nonzero_feedback_gate")


class WaveRoverNonzeroFeedbackGateTest(unittest.TestCase):
    def test_positive_nonzero_sample_stays_software_proof_and_returns_direction_summary(self):
        gate = _gate_module()

        summary = gate.build_nonzero_feedback_gate_summary(
            feedback_sample_json={"T": 1001, "L": 61, "R": -61, "r": 0.2, "p": 0.1, "y": 0, "v": 11.8}
        )

        self.assertEqual(summary["status"], "software_proof_nonzero_lr_observed")
        self.assertEqual(summary["source"], "software_proof")
        self.assertEqual(
            summary["evidence_boundary"], "software_proof_o1_wave_rover_nonzero_feedback_hil_gate_only"
        )
        self.assertFalse(summary["hil_pass"])
        self.assertFalse(summary["safe_to_control"])
        self.assertTrue(summary["gate"]["valid_t1001_observed"])
        self.assertTrue(summary["gate"]["paired_nonzero_observed"])
        self.assertTrue(summary["gate"]["direction_summary_available"])
        self.assertEqual(summary["direction_summary"]["left_positive_right_negative"], 1)
        self.assertEqual(summary["latest_nonzero_pair"]["left_speed"], 61.0)
        self.assertEqual(summary["latest_nonzero_pair"]["right_speed"], -61.0)
        self.assertIn("same_run_hil_acceptance_record", summary["missing_hil_artifacts"])

    def test_all_zero_sample_blocks_gate(self):
        gate = _gate_module()

        summary = gate.build_nonzero_feedback_gate_summary(
            feedback_sample_json={"T": 1001, "L": 0, "R": 0, "r": 0.2, "p": 0.1, "y": 0, "v": 11.8}
        )

        self.assertEqual(summary["status"], "blocked_all_zero_or_partial_zero_lr")
        self.assertFalse(summary["gate"]["paired_nonzero_observed"])
        self.assertIn("no_same_frame_nonzero_lr_pair", summary["blockers"])
        self.assertIn("direction_summary_not_available", summary["blockers"])
        self.assertEqual(summary["direction_summary"]["both_zero"], 1)

    def test_bad_json_sample_blocks_with_invalid_feedback_status(self):
        gate = _gate_module()

        summary = gate.build_nonzero_feedback_gate_summary(feedback_sample_json="not json")

        self.assertEqual(summary["status"], "blocked_invalid_feedback")
        self.assertEqual(summary["counts"]["parsed_t1001_count"], 0)
        self.assertEqual(summary["counts"]["invalid_feedback_count"], 1)
        self.assertIn("no_valid_vendor_t1001_frame", summary["blockers"])

    def test_missing_required_t1001_fields_block_gate(self):
        gate = _gate_module()

        summary = gate.build_nonzero_feedback_gate_summary(feedback_sample_json={"T": 1001, "L": 12, "R": 12})

        self.assertEqual(summary["status"], "blocked_invalid_feedback")
        self.assertEqual(summary["counts"]["invalid_feedback_count"], 1)
        self.assertIn("real_vendor_t1001_capture", summary["missing_hil_artifacts"])

    def test_non_t1001_sample_is_ignored_and_reported_as_missing_valid_feedback(self):
        gate = _gate_module()

        summary = gate.build_nonzero_feedback_gate_summary(feedback_sample_json={"T": 130, "cmd": 1})

        self.assertEqual(summary["status"], "blocked_missing_valid_t1001")
        self.assertEqual(summary["counts"]["ignored_non_t1001_count"], 1)
        self.assertEqual(summary["counts"]["invalid_feedback_count"], 0)

    def test_log_file_can_mix_wrapper_frames_non_t1001_and_invalid_lines(self):
        gate = _gate_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "feedback_T1001.log"
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"timestamp": 1, "feedback": {"T": 130, "cmd": 1}}),
                        "not json at all",
                        json.dumps({"payload": {"T": 1001, "L": -20, "R": -20, "r": 0, "p": 0, "y": 0, "v": 11.6}}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            summary = gate.build_nonzero_feedback_gate_summary(feedback_log=log_path)

        self.assertEqual(summary["status"], "blocked_invalid_feedback")
        self.assertEqual(summary["counts"]["ignored_non_t1001_count"], 1)
        self.assertEqual(summary["counts"]["invalid_feedback_count"], 1)
        self.assertEqual(summary["direction_summary"]["both_negative"], 1)
        self.assertEqual(summary["latest_nonzero_pair"]["left_speed"], -20.0)
        self.assertIn("invalid_feedback_lines_present", summary["blockers"])
        self.assertTrue(summary["gate"]["paired_nonzero_observed"])

    def test_cli_writes_output_file_and_exit_code_for_success(self):
        gate = _gate_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.json"
            with redirect_stdout(io.StringIO()):
                result = gate.main(
                    [
                        "--feedback-sample-json",
                        json.dumps({"T": 1001, "L": 1, "R": 2, "r": 0, "p": 0, "y": 0, "v": 11.7}),
                        "--output",
                        str(output_path),
                    ]
                )
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "software_proof_nonzero_lr_observed")
        self.assertFalse(payload["hil_pass"])
        self.assertFalse(payload["safe_to_control"])

    def test_cli_returns_nonzero_for_blocked_gate(self):
        gate = _gate_module()

        with redirect_stdout(io.StringIO()):
            result = gate.main(["--feedback-sample-json", json.dumps({"T": 1001, "L": 0, "R": 0, "r": 0, "p": 0, "y": 0, "v": 11.7})])

        self.assertEqual(result, 4)

    def test_cli_returns_nonzero_when_invalid_and_nonzero_are_mixed(self):
        gate = _gate_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "feedback_T1001.log"
            log_path.write_text(
                "\n".join(
                    [
                        "not json at all",
                        json.dumps({"payload": {"T": 1001, "L": 20, "R": 20, "r": 0, "p": 0, "y": 0, "v": 11.6}}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()):
                result = gate.main([str(log_path)])

        self.assertEqual(result, 4)


if __name__ == "__main__":
    unittest.main()
