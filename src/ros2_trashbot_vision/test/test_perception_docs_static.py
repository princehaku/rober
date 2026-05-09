from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
EVALUATION = REPO_ROOT / "docs" / "vision" / "perception_upgrade_evaluation.md"


class PerceptionDocsStaticTest(unittest.TestCase):
    def test_upgrade_evaluation_covers_required_options_and_tradeoffs(self):
        source = EVALUATION.read_text(encoding="utf-8")

        for option in ("OpenCV", "YOLO", "RT-DETR", "Depth camera"):
            self.assertIn(option, source)
        for dimension in (
            "Development cost",
            "Compute need",
            "Robustness",
            "Production cost",
            "Landing conditions",
        ):
            self.assertIn(dimension, source)
        self.assertIn("Scattered-trash detection is an enhancement", source)
        self.assertIn("Current MVP default", source)


if __name__ == "__main__":
    unittest.main()
