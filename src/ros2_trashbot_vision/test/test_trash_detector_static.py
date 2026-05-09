from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "ros2_trashbot_vision" / "ros2_trashbot_vision" / "trash_detector.py"


class TrashDetectorStaticTest(unittest.TestCase):
    def test_debug_and_roi_parameters_are_declared(self):
        source = SOURCE.read_text(encoding="utf-8")

        for parameter in (
            "roi_x",
            "roi_y",
            "roi_width",
            "roi_height",
            "debug_image_topic",
            "publish_debug_image",
            "sample_output_dir",
            "save_detection_samples",
            "sample_date_subdirs",
            "sample_task_id",
            "sample_route_id",
            "sample_checkpoint_id",
            "sample_event_type",
            "sample_anomaly_type",
            "sample_manifest_name",
            "sample_manifest_max_entries",
            "save_empty_detection_samples",
        ):
            self.assertIn(parameter, source)

    def test_detection_sample_json_contains_replay_metadata(self):
        source = SOURCE.read_text(encoding="utf-8")

        for field in (
            "'sample_id'",
            "'sample_ref'",
            "'raw_image'",
            "'annotated_image'",
            "'detector'",
            "'context'",
            "'task_id'",
            "'route_id'",
            "'checkpoint_id'",
            "'event_type'",
            "'anomaly_type'",
            "'roi'",
            "'parameters'",
            "'detections'",
            "'schema': 'trashbot.vision_samples.v1'",
            "'detection_count'",
            "'max_confidence'",
            "vision_sample://",
        ):
            self.assertIn(field, source)

    def test_debug_image_publish_can_be_disabled(self):
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("if self.publish_debug_image:", source)
        self.assertIn("self._publish_debug_image(msg, debug_frame)", source)

    def test_detection_sample_context_has_delivery_and_anomaly_fields(self):
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("def _sample_context(self):", source)
        for assignment in (
            "'task_id': self.sample_task_id",
            "'route_id': self.sample_route_id",
            "'checkpoint_id': self.sample_checkpoint_id",
            "'event_type': self.sample_event_type",
            "'anomaly_type': self.sample_anomaly_type",
        ):
            self.assertIn(assignment, source)

    def test_detection_sample_manifest_is_bounded_and_rebuildable(self):
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("def _write_sample_manifest(self, payload):", source)
        self.assertIn("json.JSONDecodeError", source)
        self.assertIn("manifest['samples'][-self.sample_manifest_max_entries:]", source)
        self.assertIn("self._write_sample_manifest(payload)", source)
        self.assertIn("def _manifest_path(self):", source)

    def test_detection_sample_writes_images_defensively(self):
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("def _write_image_or_raise(self, path, frame):", source)
        self.assertIn("if not cv2.imwrite(path, frame):", source)
        self.assertIn("raise OSError", source)
        self.assertIn("self._write_image_or_raise(raw_path, frame)", source)
        self.assertIn("self._write_image_or_raise(annotated_path, debug_frame)", source)

    def test_sample_ids_are_sequence_backed_and_empty_samples_are_optional(self):
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("self._sample_sequence = 0", source)
        self.assertIn("self._sample_sequence += 1", source)
        self.assertIn("time.time_ns()", source)
        self.assertIn("detections or self.save_empty_detection_samples", source)


if __name__ == "__main__":
    unittest.main()
