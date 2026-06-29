import importlib.util
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "o1_lidar_scan_proof_collector.py"
SPEC = importlib.util.spec_from_file_location("o1_lidar_scan_proof_collector", SCRIPT_PATH)
collector = importlib.util.module_from_spec(SPEC)
assert SPEC is not None
assert SPEC.loader is not None
SPEC.loader.exec_module(collector)


class LidarScanProofCollectorTest(unittest.TestCase):
    def test_topic_echo_commands_disable_ros_daemon(self):
        commands = collector.build_topic_read_commands(5.0)

        self.assertIn("ros2 topic echo --no-daemon --once /scan sensor_msgs/msg/LaserScan", commands["scan_once"])
        self.assertIn(
            "ros2 topic echo --no-daemon --once /lidar/raw_packet std_msgs/msg/UInt8MultiArray",
            commands["raw_packet_once"],
        )

    def test_topic_hz_keeps_humble_supported_syntax(self):
        commands = collector.build_topic_read_commands(5.0)

        self.assertIn("timeout 12 ros2 topic hz /scan", commands["scan_hz"])
        self.assertNotIn("topic hz --no-daemon", commands["scan_hz"])


if __name__ == "__main__":
    unittest.main()
