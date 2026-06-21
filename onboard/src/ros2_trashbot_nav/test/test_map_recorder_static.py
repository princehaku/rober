"""map_recorder 地图保存合同的静态回归测试。"""

from pathlib import Path
import unittest


MAP_RECORDER = Path(__file__).resolve().parents[1] / "ros2_trashbot_nav" / "map_recorder.py"


class MapRecorderStaticTests(unittest.TestCase):
    """不依赖 ROS runtime，锁定 PGM 像素语义。"""

    def test_free_cells_are_not_saved_as_unknown(self) -> None:
        """free cell 必须写成 254，否则保存出的地图永远没有可通行区域。"""
        source = MAP_RECORDER.read_text(encoding="utf-8")

        self.assertIn("pixels.append(205)  # unknown", source)
        self.assertIn("pixels.append(254)  # free", source)
        self.assertIn("pixels.append(0)    # occupied", source)
        self.assertNotIn("elif val == 0:\n                    pixels.append(205)  # free", source)


if __name__ == "__main__":
    unittest.main()
