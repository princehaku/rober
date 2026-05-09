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
            "sample_output_dir",
            "save_detection_samples",
        ):
            self.assertIn(parameter, source)


if __name__ == "__main__":
    unittest.main()
