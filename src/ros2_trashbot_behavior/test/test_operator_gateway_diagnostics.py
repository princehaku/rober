import unittest
import json
import tempfile
from pathlib import Path

from ros2_trashbot_behavior.operator_gateway_diagnostics import (
    build_diagnostics_payload,
    normalize_log_refs,
    summarize_vision_manifest,
)


class OperatorGatewayDiagnosticsTest(unittest.TestCase):
    def test_diagnostics_prefers_latest_status_terminal_fields(self):
        payload = build_diagnostics_payload(
            {
                "state": "failed",
                "message": "navigation failed",
                "error_code": "nav_failed",
                "final_state": "error",
                "task_record_path": "/tmp/current.json",
                "last_task": {
                    "error_code": "old_error",
                    "final_state": "old_state",
                    "task_record_path": "/tmp/old.json",
                },
            },
            software_version="1.2.3",
            map_version="",
            route_version="",
            log_refs=" /tmp/a.log, /tmp/b.log ",
            vision_sample_manifest_ref="/tmp/vision/manifest.json",
            operator_status_file="/tmp/status.json",
        )

        self.assertEqual(payload["state"], "diagnostics_ready")
        self.assertIn("Diagnostics are ready", payload["phone_copy"])
        self.assertEqual(payload["speaker_prompt"], "Diagnostics are ready.")
        self.assertEqual(payload["software_version"], "1.2.3")
        self.assertEqual(payload["map_version"], "")
        self.assertEqual(payload["route_version"], "")
        self.assertEqual(payload["failure"]["error_code"], "nav_failed")
        self.assertEqual(payload["failure"]["final_state"], "error")
        self.assertEqual(payload["failure"]["task_record_path"], "/tmp/current.json")
        self.assertEqual(payload["log_refs"], ["/tmp/a.log", "/tmp/b.log"])
        self.assertEqual(payload["vision_sample_manifest_ref"], "/tmp/vision/manifest.json")
        self.assertFalse(payload["vision_samples"]["exists"])
        self.assertIn("not found", payload["vision_samples"]["read_error"])
        self.assertEqual(payload["operator_status_file"], "/tmp/status.json")

    def test_diagnostics_falls_back_to_last_task_terminal_fields(self):
        payload = build_diagnostics_payload(
            {
                "state": "failed",
                "message": "delivery failed",
                "last_task": {
                    "error_code": "timed_out",
                    "final_state": "dropoff",
                    "task_record_path": "/tmp/task.json",
                },
            },
            software_version="",
            map_version="map-a",
            route_version="route-a",
            log_refs=["/tmp/robot.log", ""],
            vision_sample_manifest_ref="",
            operator_status_file="/tmp/status.json",
        )

        self.assertEqual(payload["failure"]["error_code"], "timed_out")
        self.assertEqual(payload["failure"]["final_state"], "dropoff")
        self.assertEqual(payload["failure"]["task_record_path"], "/tmp/task.json")
        self.assertEqual(payload["map_version"], "map-a")
        self.assertEqual(payload["route_version"], "route-a")
        self.assertEqual(payload["log_refs"], ["/tmp/robot.log"])

    def test_log_refs_are_normalized_without_claiming_file_existence(self):
        self.assertEqual(normalize_log_refs(None), [])
        self.assertEqual(normalize_log_refs(""), [])
        self.assertEqual(normalize_log_refs("a,b, c "), ["a", "b", "c"])
        self.assertEqual(normalize_log_refs(["a", 3, ""]), ["a", "3"])

    def test_vision_manifest_summary_reports_latest_sample(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.vision_samples.v1",
                        "samples": [
                            {
                                "sample_id": "old",
                                "sample_ref": "vision_sample://20260510/old.json",
                                "timestamp": 1.0,
                                "context": {"route_id": "old-route"},
                                "detection_count": 0,
                                "max_confidence": 0,
                            },
                            {
                                "sample_id": "new",
                                "sample_ref": "vision_sample://20260510/new.json",
                                "timestamp": 2.0,
                                "context": {
                                    "task_id": "task-7",
                                    "route_id": "route-a",
                                    "checkpoint_id": "cp-3",
                                    "event_type": "anomaly",
                                },
                                "detection_count": 2,
                                "max_confidence": 91,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_vision_manifest(str(manifest_path))

        self.assertTrue(summary["exists"])
        self.assertEqual(summary["schema"], "trashbot.vision_samples.v1")
        self.assertEqual(summary["sample_count"], 2)
        self.assertEqual(summary["latest_sample_ref"], "vision_sample://20260510/new.json")
        self.assertEqual(summary["latest_timestamp"], 2.0)
        self.assertEqual(summary["latest_context"]["task_id"], "task-7")
        self.assertEqual(summary["latest_detection_count"], 2)
        self.assertEqual(summary["latest_max_confidence"], 91)
        self.assertEqual(summary["read_error"], "")

    def test_vision_manifest_summary_handles_missing_and_corrupt_files(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.json"
            corrupt = Path(td) / "corrupt.json"
            corrupt.write_text("{bad json", encoding="utf-8")

            missing_summary = summarize_vision_manifest(str(missing))
            corrupt_summary = summarize_vision_manifest(str(corrupt))

        self.assertFalse(missing_summary["exists"])
        self.assertIn("not found", missing_summary["read_error"])
        self.assertTrue(corrupt_summary["exists"])
        self.assertIn("failed reading", corrupt_summary["read_error"])

    def test_vision_manifest_summary_handles_empty_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "manifest.json"
            manifest_path.write_text(
                json.dumps({"schema": "trashbot.vision_samples.v1", "samples": []}),
                encoding="utf-8",
            )

            summary = summarize_vision_manifest(str(manifest_path))

        self.assertTrue(summary["exists"])
        self.assertEqual(summary["schema"], "trashbot.vision_samples.v1")
        self.assertEqual(summary["sample_count"], 0)
        self.assertEqual(summary["latest_sample_ref"], "")
        self.assertEqual(summary["latest_context"], {})
        self.assertEqual(summary["read_error"], "")


if __name__ == "__main__":
    unittest.main()
