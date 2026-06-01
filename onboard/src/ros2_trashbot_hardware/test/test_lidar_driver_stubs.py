import sys
from pathlib import Path
import unittest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_hardware.lidar_driver import parse_bool, scan_dict_from_packet
from ros2_trashbot_hardware.lidar_packets import make_mock_packet


class LidarDriverStubsTest(unittest.TestCase):
    def test_parse_bool_accepts_launch_style_values(self):
        self.assertTrue(parse_bool("true"))
        self.assertTrue(parse_bool("1"))
        self.assertFalse(parse_bool("false"))
        self.assertFalse(parse_bool(""))

    def test_scan_dict_is_laserscan_shaped_without_ros_imports(self):
        scan = scan_dict_from_packet(make_mock_packet(), frame_id="laser_frame")
        self.assertEqual(scan["frame_id"], "laser_frame")
        self.assertEqual(len(scan["ranges"]), 3)
        self.assertGreater(scan["angle_increment"], 0.0)
