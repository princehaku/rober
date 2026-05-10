import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_vision.vision_sample_manifest import summarize_manifest


class VisionSampleManifestSummaryTest(unittest.TestCase):
    def test_valid_manifest_summarizes_route_negative_and_detection_anomaly_samples(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            keyframes = root / "keyframes"
            samples = root / "20260510"
            keyframes.mkdir()
            samples.mkdir()
            (keyframes / "000.json").write_text("{}", encoding="utf-8")
            (keyframes / "000.jpg").write_bytes(b"route-jpeg")
            (samples / "det_001.json").write_text("{}", encoding="utf-8")
            (samples / "det_001_raw.jpg").write_bytes(b"raw-jpeg")
            (samples / "det_001_annotated.jpg").write_bytes(b"annotated-jpeg")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.vision_samples.v1",
                        "sample_output_dir": str(root),
                        "samples": [
                            {
                                "sample_id": "route_keyframe_000",
                                "sample_ref": "vision_sample://keyframes/000.json",
                                "timestamp": 1.0,
                                "frame_id": "map",
                                "raw_image": "keyframes/000.jpg",
                                "annotated_image": "",
                                "json": "keyframes/000.json",
                                "context": {
                                    "event_type": "route_keyframe",
                                    "route_id": "delivery",
                                    "checkpoint_id": "0",
                                    "anomaly_type": "",
                                },
                                "detection_count": 0,
                            },
                            {
                                "sample_id": "detection_001",
                                "sample_ref": "vision_sample://20260510/det_001.json",
                                "timestamp": 2.0,
                                "frame_id": "camera",
                                "raw_image": "20260510/det_001_raw.jpg",
                                "annotated_image": "20260510/det_001_annotated.jpg",
                                "json": "20260510/det_001.json",
                                "context": {
                                    "event_type": "detection",
                                    "route_id": "delivery",
                                    "checkpoint_id": "1",
                                    "anomaly_type": "low_light",
                                },
                                "detection_count": 2,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_manifest(str(manifest_path))

        self.assertEqual(summary["manifest_path"], str(manifest_path))
        self.assertEqual(summary["schema"], "trashbot.vision_samples.v1")
        self.assertEqual(summary["sample_count"], 2)
        self.assertEqual(summary["context_counts"], {"detection": 1, "route_keyframe": 1})
        self.assertEqual(summary["event_counts"], {"detection": 1, "route_keyframe": 1})
        self.assertEqual(summary["sample_type_counts"], {"detection": 1, "route_keyframe": 1})
        self.assertEqual(summary["negative_sample_count"], 1)
        self.assertEqual(summary["anomaly_sample_count"], 1)
        self.assertEqual(summary["route_keyframe_sample_count"], 1)
        self.assertEqual(summary["detection_sample_count"], 1)
        self.assertEqual(summary["file_counts"]["sample_ref"]["present"], 2)
        self.assertEqual(summary["file_counts"]["raw_image"]["present"], 2)
        self.assertEqual(summary["file_counts"]["annotated_image"]["present"], 1)
        self.assertEqual(summary["file_counts"]["annotated_image"]["empty"], 1)
        self.assertEqual(summary["field_coverage"]["missing"], {})
        self.assertEqual(summary["context_field_coverage"]["present"]["event_type"], 2)
        self.assertEqual(summary["context_field_coverage"]["missing"]["task_id"], 2)
        self.assertEqual(summary["missing_file_refs"], [])
        self.assertEqual(summary["errors"], [])
        self.assertEqual(summary["warnings"], [])

    def test_missing_required_file_refs_are_errors_and_cli_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest_path = root / "manifest.json"
            (root / "sample.json").write_text("{}", encoding="utf-8")
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

            summary = summarize_manifest(str(manifest_path))
            result = subprocess.run(
                [sys.executable, "-m", "ros2_trashbot_vision.vision_sample_manifest", str(manifest_path)],
                cwd=str(PACKAGE_ROOT),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing_raw.jpg", "\n".join(summary["errors"]))
        self.assertIn("missing_annotated.jpg", "\n".join(summary["warnings"]))
        self.assertEqual(summary["file_counts"]["raw_image"]["missing"], 1)
        self.assertEqual(summary["file_counts"]["annotated_image"]["missing"], 1)
        self.assertEqual(len(summary["missing_file_refs"]), 2)
        cli_summary = json.loads(result.stdout)
        self.assertEqual(cli_summary["sample_count"], 1)
        self.assertTrue(cli_summary["errors"])

    def test_empty_manifest_schema_problem_and_missing_sample_fields_are_not_silent_success(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            empty_manifest = root / "empty.json"
            empty_manifest.write_text(
                json.dumps({"schema": "trashbot.vision_samples.v2", "sample_output_dir": str(root), "samples": []}),
                encoding="utf-8",
            )
            missing_fields_manifest = root / "missing_fields.json"
            missing_fields_manifest.write_text(
                json.dumps({"schema": "trashbot.vision_samples.v1", "samples": [{"sample_id": "partial"}]}),
                encoding="utf-8",
            )

            empty_summary = summarize_manifest(str(empty_manifest))
            missing_summary = summarize_manifest(str(missing_fields_manifest))

        self.assertEqual(empty_summary["sample_count"], 0)
        self.assertIn("manifest.samples is empty", empty_summary["warnings"])
        self.assertIn("unexpected manifest schema: trashbot.vision_samples.v2", empty_summary["warnings"])
        self.assertIn("samples[0] missing required field: sample_ref", missing_summary["errors"])
        self.assertIn("samples[0].context must be an object", missing_summary["errors"])
        self.assertEqual(missing_summary["field_coverage"]["missing"]["sample_ref"], 1)
        self.assertEqual(missing_summary["file_counts"]["sample_ref"]["empty"], 1)
        self.assertEqual(missing_summary["sample_type_counts"], {"missing_context": 1})

    def test_route_data_recorder_style_manifest_uses_manifest_directory_when_output_dir_is_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            keyframes = root / "keyframes"
            keyframes.mkdir()
            (keyframes / "012.json").write_text("{}", encoding="utf-8")
            (keyframes / "012.jpg").write_bytes(b"route-frame")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.vision_samples.v1",
                        "samples": [
                            {
                                "sample_id": "route_keyframe_012",
                                "sample_ref": "vision_sample://keyframes/012.json",
                                "timestamp": 12.0,
                                "frame_id": "map",
                                "raw_image": "keyframes/012.jpg",
                                "annotated_image": "",
                                "json": "keyframes/012.json",
                                "context": {"event_type": "route_keyframe", "route_id": "r1", "checkpoint_id": "12"},
                                "detection_count": 0,
                                "max_confidence": 0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = summarize_manifest(str(manifest_path))

        self.assertEqual(summary["sample_output_dir"], str(root.resolve()))
        self.assertEqual(summary["route_keyframe_sample_count"], 1)
        self.assertEqual(summary["detection_sample_count"], 0)
        self.assertEqual(summary["negative_sample_count"], 1)
        self.assertEqual(summary["file_counts"]["sample_ref"]["present"], 1)
        self.assertEqual(summary["file_counts"]["json"]["present"], 1)
        self.assertEqual(summary["errors"], [])

    def test_bad_manifest_shape_reports_errors(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bad_root = root / "bad_root.json"
            bad_root.write_text("[]", encoding="utf-8")
            bad_samples = root / "bad_samples.json"
            bad_samples.write_text(json.dumps({"schema": "trashbot.vision_samples.v1", "samples": {}}), encoding="utf-8")

            bad_root_summary = summarize_manifest(str(bad_root))
            bad_samples_summary = summarize_manifest(str(bad_samples))

        self.assertIn("manifest root must be an object", bad_root_summary["errors"])
        self.assertIn("manifest.samples must be a list", bad_samples_summary["errors"])


if __name__ == "__main__":
    unittest.main()
