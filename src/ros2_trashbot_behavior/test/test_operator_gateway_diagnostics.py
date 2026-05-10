import unittest
import json
import sys
import tempfile
from pathlib import Path


BEHAVIOR_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
VISION_PACKAGE_ROOT = BEHAVIOR_PACKAGE_ROOT.parent / "ros2_trashbot_vision"
sys.path.insert(0, str(BEHAVIOR_PACKAGE_ROOT))
sys.path.insert(0, str(VISION_PACKAGE_ROOT))

from ros2_trashbot_behavior.operator_gateway_diagnostics import (
    build_diagnostics_payload,
    normalize_log_refs,
    summarize_hardware_proof,
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
        self.assertEqual(payload["hardware_proof"]["status"], "read_error")
        self.assertIn("not configured", payload["hardware_proof"]["read_error"])
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
        self.assertEqual(payload["vision_samples"]["integrity_summary"]["status"], "not_configured")
        self.assertEqual(payload["vision_samples"]["integrity_error_count"], 1)
        self.assertEqual(payload["hardware_proof"]["status"], "read_error")

    def test_hardware_proof_ready_with_hil_risk_maps_to_needs_hil(self):
        with tempfile.TemporaryDirectory() as td:
            proof_path = Path(td) / "hardware-proof.json"
            proof_path.write_text(
                json.dumps(
                    {
                        "status": "software_proof_ready",
                        "vendor_sources": ["docs/vendor/VENDOR_INDEX.md"],
                        "risk_flags": [
                            {
                                "id": "hil_required",
                                "severity": "high",
                                "detail": "Offline proof still needs hardware-in-loop.",
                            }
                        ],
                        "hil_recipe": {"no_motion": "python3 scripts/hardware_smoke_wave_rover.py"},
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_hardware_proof(str(proof_path))

        self.assertEqual(summary["status"], "needs_hil")
        self.assertEqual(summary["source_status"], "software_proof_ready")
        self.assertTrue(summary["exists"])
        self.assertEqual(summary["vendor_sources"], ["docs/vendor/VENDOR_INDEX.md"])
        self.assertEqual(summary["risk_flags"][0]["id"], "hil_required")
        self.assertIn("hardware-in-loop still required", summary["summary"])
        self.assertNotIn("hardware passed", summary["summary"].lower())
        self.assertNotIn("hil passed", summary["summary"].lower())

    def test_hardware_proof_ready_without_hil_risk_maps_to_software_proof(self):
        with tempfile.TemporaryDirectory() as td:
            proof_path = Path(td) / "hardware-proof.json"
            proof_path.write_text(
                json.dumps(
                    {
                        "status": "software_proof_ready",
                        "vendor_sources": ["docs/vendor/VENDOR_INDEX.md"],
                        "risk_flags": [
                            {
                                "id": "doc_review",
                                "severity": "medium",
                                "detail": "Keep vendor references with the support package.",
                            }
                        ],
                        "hil_recipe": {},
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_hardware_proof(str(proof_path))

        self.assertEqual(summary["status"], "software_proof")
        self.assertIn("Software proof is ready only", summary["summary"])
        self.assertIn("does not validate real UART", summary["summary"])

    def test_hardware_proof_invalid_config_maps_to_invalid_config(self):
        with tempfile.TemporaryDirectory() as td:
            proof_path = Path(td) / "hardware-proof.json"
            proof_path.write_text(
                json.dumps(
                    {
                        "status": "invalid_config",
                        "vendor_sources": ["docs/vendor/VENDOR_INDEX.md"],
                        "config_validation": {"error": "track_width_m must be positive"},
                        "risk_flags": [],
                        "hil_recipe": {},
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_hardware_proof(str(proof_path))

        self.assertEqual(summary["status"], "invalid_config")
        self.assertEqual(summary["read_error"], "track_width_m must be positive")
        self.assertIn("Fix the reported bridge configuration", summary["next_step"])

    def test_hardware_proof_feedback_parse_failed_stays_conservative(self):
        with tempfile.TemporaryDirectory() as td:
            proof_path = Path(td) / "hardware-proof.json"
            proof_path.write_text(
                json.dumps(
                    {
                        "status": "feedback_parse_failed",
                        "vendor_sources": ["docs/vendor/VENDOR_INDEX.md"],
                        "risk_flags": [],
                        "hil_recipe": {},
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_hardware_proof(str(proof_path))

        self.assertEqual(summary["status"], "needs_hil")
        self.assertIn("feedback parsing failed", summary["summary"])

    def test_hardware_proof_read_errors_are_structured(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            missing = root / "missing.json"
            corrupt = root / "corrupt.json"
            non_dict = root / "non-dict.json"
            missing_status = root / "missing-status.json"
            corrupt.write_text("{bad json", encoding="utf-8")
            non_dict.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
            missing_status.write_text(json.dumps({"risk_flags": []}), encoding="utf-8")

            missing_summary = summarize_hardware_proof(str(missing))
            corrupt_summary = summarize_hardware_proof(str(corrupt))
            non_dict_summary = summarize_hardware_proof(str(non_dict))
            missing_status_summary = summarize_hardware_proof(str(missing_status))

        self.assertEqual(missing_summary["status"], "read_error")
        self.assertFalse(missing_summary["exists"])
        self.assertIn("not found", missing_summary["read_error"])
        self.assertEqual(corrupt_summary["status"], "read_error")
        self.assertTrue(corrupt_summary["exists"])
        self.assertIn("failed reading", corrupt_summary["read_error"])
        self.assertEqual(non_dict_summary["status"], "read_error")
        self.assertIn("must be an object", non_dict_summary["read_error"])
        self.assertEqual(missing_status_summary["status"], "read_error")
        self.assertIn("missing status", missing_status_summary["read_error"])

    def test_diagnostics_payload_includes_configured_hardware_proof(self):
        with tempfile.TemporaryDirectory() as td:
            proof_path = Path(td) / "hardware-proof.json"
            proof_path.write_text(
                json.dumps({"status": "software_proof_ready", "risk_flags": [], "vendor_sources": []}),
                encoding="utf-8",
            )

            payload = build_diagnostics_payload(
                {"state": "waiting_for_trash"},
                software_version="",
                map_version="",
                route_version="",
                log_refs=[],
                vision_sample_manifest_ref="",
                operator_status_file="/tmp/status.json",
                hardware_proof_ref=str(proof_path),
            )

        self.assertEqual(payload["hardware_proof"]["status"], "software_proof")
        self.assertEqual(payload["hardware_proof"]["artifact_ref"], str(proof_path))

    def test_log_refs_are_normalized_without_claiming_file_existence(self):
        self.assertEqual(normalize_log_refs(None), [])
        self.assertEqual(normalize_log_refs(""), [])
        self.assertEqual(normalize_log_refs("a,b, c "), ["a", "b", "c"])
        self.assertEqual(normalize_log_refs(["a", 3, ""]), ["a", "3"])

    def test_vision_manifest_summary_reports_latest_sample(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            samples = root / "samples"
            samples.mkdir()
            (samples / "old.json").write_text("{}", encoding="utf-8")
            (samples / "old_raw.jpg").write_bytes(b"old")
            (samples / "new.json").write_text("{}", encoding="utf-8")
            (samples / "new_raw.jpg").write_bytes(b"new")
            (samples / "new_annotated.jpg").write_bytes(b"annotated")
            manifest_path = Path(td) / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.vision_samples.v1",
                        "sample_output_dir": str(root),
                        "samples": [
                            {
                                "sample_id": "old",
                                "sample_ref": "vision_sample://samples/old.json",
                                "timestamp": 1.0,
                                "frame_id": "map",
                                "raw_image": "samples/old_raw.jpg",
                                "annotated_image": "",
                                "json": "samples/old.json",
                                "context": {"route_id": "old-route", "event_type": "route_keyframe"},
                                "detection_count": 0,
                                "max_confidence": 0,
                            },
                            {
                                "sample_id": "new",
                                "sample_ref": "vision_sample://samples/new.json",
                                "timestamp": 2.0,
                                "frame_id": "camera",
                                "raw_image": "samples/new_raw.jpg",
                                "annotated_image": "samples/new_annotated.jpg",
                                "json": "samples/new.json",
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
        self.assertEqual(summary["latest_sample_ref"], "vision_sample://samples/new.json")
        self.assertEqual(summary["latest_timestamp"], 2.0)
        self.assertEqual(summary["latest_context"]["task_id"], "task-7")
        self.assertEqual(summary["latest_detection_count"], 2)
        self.assertEqual(summary["latest_max_confidence"], 91)
        self.assertEqual(summary["event_counts"], {"route_keyframe": 1, "anomaly": 1})
        self.assertEqual(summary["review_queue_count"], 2)
        self.assertEqual(summary["review_queue"][0]["reason"], "route_keyframe_review")
        self.assertEqual(summary["review_queue"][1]["reason"], "anomaly_sample")
        self.assertEqual(summary["integrity_summary"]["status"], "ok")
        self.assertEqual(summary["integrity_error_count"], 0)
        self.assertEqual(summary["integrity_warning_count"], 0)
        self.assertEqual(summary["missing_file_ref_count"], 0)
        self.assertEqual(summary["file_counts"]["sample_ref"]["present"], 2)
        self.assertEqual(summary["file_counts"]["raw_image"]["present"], 2)
        self.assertEqual(summary["file_counts"]["annotated_image"]["present"], 1)
        self.assertEqual(summary["context_field_coverage"]["present"]["event_type"], 2)
        self.assertEqual(summary["context_field_coverage"]["present"]["route_id"], 2)
        self.assertEqual(summary["context_field_coverage"]["missing"]["task_id"], 1)
        self.assertEqual(summary["read_error"], "")

    def test_vision_manifest_summary_builds_bounded_review_queue(self):
        with tempfile.TemporaryDirectory() as td:
            manifest_path = Path(td) / "manifest.json"
            samples = [
                {
                    "sample_id": "normal-reviewed",
                    "sample_ref": "vision_sample://normal-reviewed.json",
                    "timestamp": 1.0,
                    "context": {"event_type": "detection"},
                    "detection_count": 1,
                    "max_confidence": 95,
                    "review_status": "accepted",
                },
                {
                    "sample_id": "low-confidence",
                    "sample_ref": "vision_sample://low-confidence.json",
                    "timestamp": 2.0,
                    "context": {"event_type": "detection"},
                    "detection_count": 1,
                    "max_confidence": 62,
                },
                {
                    "sample_id": "route-keyframe",
                    "sample_ref": "vision_sample://route-keyframe.json",
                    "timestamp": 3.0,
                    "context": {"event_type": "route_keyframe", "route_id": "route-a"},
                    "detection_count": 0,
                    "max_confidence": 0,
                },
                {
                    "sample_id": "anomaly",
                    "sample_ref": "vision_sample://anomaly.json",
                    "timestamp": 4.0,
                    "context": {"event_type": "anomaly", "anomaly_type": "blocked_view"},
                    "detection_count": 0,
                    "max_confidence": 0,
                },
            ]
            manifest_path.write_text(
                json.dumps({"schema": "trashbot.vision_samples.v1", "samples": samples}),
                encoding="utf-8",
            )

            summary = summarize_vision_manifest(str(manifest_path))

        self.assertEqual(summary["event_counts"], {"detection": 2, "route_keyframe": 1, "anomaly": 1})
        self.assertEqual(summary["review_queue_count"], 3)
        self.assertEqual(
            [item["reason"] for item in summary["review_queue"]],
            ["low_confidence_detection", "route_keyframe_review", "anomaly_sample"],
        )
        self.assertEqual(summary["review_queue"][-1]["sample_ref"], "vision_sample://anomaly.json")

    def test_vision_manifest_summary_handles_missing_and_corrupt_files(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.json"
            corrupt = Path(td) / "corrupt.json"
            corrupt.write_text("{bad json", encoding="utf-8")

            missing_summary = summarize_vision_manifest(str(missing))
            corrupt_summary = summarize_vision_manifest(str(corrupt))

        self.assertFalse(missing_summary["exists"])
        self.assertIn("not found", missing_summary["read_error"])
        self.assertEqual(missing_summary["integrity_summary"]["status"], "error")
        self.assertEqual(missing_summary["integrity_error_count"], 1)
        self.assertTrue(corrupt_summary["exists"])
        self.assertIn("failed reading", corrupt_summary["read_error"])
        self.assertEqual(corrupt_summary["integrity_summary"]["status"], "error")
        self.assertGreaterEqual(corrupt_summary["integrity_error_count"], 1)

    def test_vision_manifest_summary_reports_missing_file_refs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "sample.json").write_text("{}", encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.vision_samples.v1",
                        "sample_output_dir": ".",
                        "samples": [
                            {
                                "sample_id": "bad",
                                "sample_ref": "vision_sample://sample.json",
                                "timestamp": 1.0,
                                "frame_id": "camera",
                                "raw_image": "missing_raw.jpg",
                                "annotated_image": "missing_annotated.jpg",
                                "json": "sample.json",
                                "context": {"event_type": "detection", "anomaly_type": ""},
                                "detection_count": 0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_vision_manifest(str(manifest_path))

        self.assertTrue(summary["exists"])
        self.assertEqual(summary["sample_count"], 1)
        self.assertEqual(summary["integrity_summary"]["status"], "error")
        self.assertEqual(summary["integrity_error_count"], 1)
        self.assertEqual(summary["integrity_warning_count"], 1)
        self.assertEqual(summary["missing_file_ref_count"], 2)
        self.assertEqual(summary["file_counts"]["raw_image"]["missing"], 1)
        self.assertEqual(summary["file_counts"]["annotated_image"]["missing"], 1)
        self.assertEqual(summary["context_field_coverage"]["present"]["event_type"], 1)
        self.assertEqual(summary["context_field_coverage"]["missing"]["task_id"], 1)
        self.assertEqual(summary["missing_file_refs"][0]["field"], "raw_image")

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
        self.assertEqual(summary["event_counts"], {})
        self.assertEqual(summary["review_queue_count"], 0)
        self.assertEqual(summary["review_queue"], [])
        self.assertEqual(summary["read_error"], "")


if __name__ == "__main__":
    unittest.main()
