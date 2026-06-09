from pathlib import Path
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PACKAGE_ROOT / "ros2_trashbot_vision" / "camera_publisher.py"
SETUP = PACKAGE_ROOT / "setup.py"


class CameraPublisherStaticTest(unittest.TestCase):
    def test_camera_publisher_declares_runtime_parameters_and_fail_closed_messages(self):
        source = SOURCE.read_text(encoding="utf-8")

        for parameter in ("device", "topic", "frame_id", "width", "height", "fps"):
            self.assertIn(f"'{parameter}'", source)
        self.assertIn("Failed to open camera device", source)
        self.assertIn("no synthetic frame will be published", source)
        self.assertIn("cv2.VideoCapture", source)

    def test_setup_registers_camera_console_script(self):
        source = SETUP.read_text(encoding="utf-8")

        self.assertIn(
            "camera_publisher = ros2_trashbot_vision.camera_publisher:main",
            source,
        )


if __name__ == "__main__":
    unittest.main()
