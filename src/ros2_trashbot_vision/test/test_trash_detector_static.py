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
            "'roi'",
            "'parameters'",
            "'detections'",
            "vision_sample://",
        ):
            self.assertIn(field, source)

    def test_debug_image_publish_can_be_disabled(self):
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("if self.publish_debug_image:", source)
        self.assertIn("self._publish_debug_image(msg, debug_frame)", source)


if __name__ == "__main__":
    unittest.main()
