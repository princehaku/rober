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

    def test_vendor_sources_record_existing_wave_rover_lidar_reference(self):
        status = collector.build_source_status(lambda path: path in {"docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py"})

        self.assertEqual(230400, status["wave_rover_lidar_reference"]["baudrate"])
        self.assertEqual("0x54", status["wave_rover_lidar_reference"]["packet_header"])
        self.assertFalse(status["dedicated_lidar_vendor_doc_present_in_local_tree"])

    def test_lidar_process_probe_only_uses_lidar_candidate_paths(self):
        calls = []

        def runner(command, timeout_s):
            calls.append(command)
            return {"command": command, "returncode": 0, "stdout_preview": "", "stderr_preview": "", "ok": True}

        probe = collector.build_lidar_process_probe(
            {
                "/dev/ttyACM0": {"exists": True},
                "/dev/lidar": {"exists": False},
            },
            timeout_s=12.0,
            command_runner=runner,
        )

        self.assertTrue(probe["attempted"])
        self.assertEqual(["/dev/ttyACM0"], probe["paths"])
        self.assertTrue(all("/dev/ttyS5" not in command for command in calls))
        self.assertTrue(any("lsof" in command for command in calls))

    def test_proof_flags_keep_strict_no_motion_fields_false(self):
        flags = collector.proof_flags()

        self.assertFalse(flags["safe_to_control"])
        self.assertFalse(flags["publishes_cmd_vel"])
        self.assertFalse(flags["calls_base_manual"])
        self.assertFalse(flags["uses_base_uart"])
        self.assertFalse(flags["route_execution_success"])


if __name__ == "__main__":
    unittest.main()
