import math
import sys
from pathlib import Path
import unittest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_hardware.lidar_packets import expected_packet_size, make_mock_packet, parse_packet


class LidarPacketsTest(unittest.TestCase):
    def test_mock_packet_uses_vendor_header_and_lsn_length(self):
        packet = make_mock_packet()
        self.assertEqual(packet[:2], b"\xaa\x55")
        self.assertEqual(len(packet), expected_packet_size(packet[3]))

    def test_parse_packet_converts_distance_and_angle(self):
        points = parse_packet(make_mock_packet())
        self.assertEqual(len(points), 3)
        self.assertAlmostEqual(points[0].distance_m, 1.0)
        self.assertAlmostEqual(points[2].angle_rad, math.radians(30.0))

    def test_parse_packet_rejects_bad_header_or_length(self):
        with self.assertRaises(ValueError):
            parse_packet(b"\x00\x55\x00\x00")
        with self.assertRaises(ValueError):
            parse_packet(make_mock_packet()[:-1])
