from pathlib import Path
import unittest


def _repo_root() -> Path:
    """定位仓库根；兼容源码在 onboard/src/ 下的深度。"""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "AGENTS.md").is_file() and (parent / "docs").is_dir():
            return parent
    raise RuntimeError("无法定位仓库根。")


REPO_ROOT = _repo_root()
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
        self.assertIn("No default detector is shipped", source)
        self.assertIn("not part of the current MVP default", source)


if __name__ == "__main__":
    unittest.main()
