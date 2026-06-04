#!/usr/bin/env python3
"""O1 LiDAR scan proof collector 的 fail-closed 单元测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import o1_lidar_scan_proof_collector as collector  # noqa: E402


def fake_path_exists(_: str) -> bool:
    """默认模拟远端 blocker：ROS2 setup/install 都不存在。"""
    return False


def fake_path_describer(path: str) -> dict[str, object]:
    """只返回路径元数据，不模拟任何设备打开动作。"""
    return {
        "path": path,
        "exists": path == "/dev/ttyACM0",
        "lexists": path == "/dev/ttyACM0",
        "is_symlink": False,
        "realpath": path if path == "/dev/ttyACM0" else None,
        "error": None,
    }


def fake_url_fetcher(url: str, _: float) -> dict[str, object]:
    """模拟 8787 只读 GET，radar 仍保留 scan not_proven。"""
    if url.endswith("/api/radar/status"):
        return {"ok": True, "status": "loaded", "payload": {"scan_status": "not_proven"}}
    return {"ok": True, "status": "loaded", "payload": {"status": "ready"}}


class CommandRecorder:
    """记录是否误运行 ros2/topic 命令。"""

    def __init__(self, responses: dict[str, dict[str, object]] | None = None) -> None:
        self.commands: list[str] = []
        self.responses = responses or {}

    def __call__(self, command: str, _: float) -> dict[str, object]:
        self.commands.append(command)
        for key, value in self.responses.items():
            if key in command:
                payload = dict(value)
                payload.setdefault("command", command)
                return payload
        return {"command": command, "returncode": 0, "stdout_preview": "ok", "stderr_preview": "", "ok": True}


class LidarScanProofCollectorTest(unittest.TestCase):
    def test_default_collector_reports_blockers_without_topic_reads(self) -> None:
        recorder = CommandRecorder()

        result = collector.build_probe_payload(
            upper_api_base_url="http://127.0.0.1:8787",
            expect_existing_topics=False,
            path_exists=fake_path_exists,
            path_describer=fake_path_describer,
            url_fetcher=fake_url_fetcher,
            command_runner=recorder,
        )

        blocker_codes = {item["code"] for item in result["blockers"]}
        self.assertEqual(result["schema"], "trashbot.o1.lidar_scan_proof.v1")
        self.assertIn("ros2_humble_setup_missing", blocker_codes)
        self.assertIn("rober_install_setup_missing", blocker_codes)
        self.assertIn("upper_api_scan_not_proven", blocker_codes)
        self.assertFalse(result["topic_reads"]["attempted"])
        self.assertFalse(result["proof"]["scan_once_observed"])
        self.assertFalse(result["proof"]["scan_hz_observed"])
        self.assertFalse(result["proof"]["raw_packet_once_observed"])
        self.assertFalse(result["proof"]["tf_observed"])
        self.assertFalse(result["proof"]["all_required_observations_observed"])
        self.assertEqual(set(result["proof"]["required_observations"]), {"scan_once", "scan_hz", "raw_packet_once", "tf"})
        self.assertFalse(result["proof"]["driver_started_by_collector"])
        self.assertFalse(result["proof"]["lidar_start_command_sent_by_collector"])
        self.assertFalse(result["safe_to_control"])
        self.assertFalse(result["sends_commands"])
        self.assertFalse(result["sends_motion_commands"])
        self.assertFalse(result["robot_control_executed"])
        self.assertEqual(recorder.commands, [])

    def test_expect_existing_topics_still_blocks_before_ros_runtime(self) -> None:
        recorder = CommandRecorder()

        result = collector.build_probe_payload(
            expect_existing_topics=True,
            path_exists=fake_path_exists,
            path_describer=fake_path_describer,
            url_fetcher=fake_url_fetcher,
            command_runner=recorder,
        )

        self.assertFalse(result["topic_reads"]["attempted"])
        self.assertEqual(result["topic_reads"]["reason"], "blocked_before_topic_read_by_ros2_runtime")
        self.assertEqual(recorder.commands, [])

    def test_topic_read_only_mode_records_scan_and_raw_packet_when_runtime_ready(self) -> None:
        recorder = CommandRecorder()

        result = collector.build_probe_payload(
            expect_existing_topics=True,
            path_exists=lambda _: True,
            path_describer=fake_path_describer,
            url_fetcher=lambda url, timeout: {"ok": True, "status": "loaded", "payload": {"scan_status": "scan_once_observed"}},
            command_runner=recorder,
        )

        self.assertTrue(result["topic_reads"]["attempted"])
        self.assertTrue(result["proof"]["scan_once_observed"])
        self.assertTrue(result["proof"]["scan_hz_observed"])
        self.assertTrue(result["proof"]["raw_packet_once_observed"])
        self.assertTrue(result["proof"]["tf_observed"])
        self.assertTrue(result["proof"]["all_required_observations_observed"])
        self.assertEqual(result["proof"]["status"], "scan_once_hz_raw_packet_tf_observed")
        self.assertEqual(len(recorder.commands), 5)
        self.assertTrue(any("command -v ros2" in command and "ros2 --help" in command for command in recorder.commands))
        self.assertTrue(any("ros2 topic echo --once /scan" in command for command in recorder.commands))
        self.assertTrue(any("ros2 topic hz /scan" in command for command in recorder.commands))
        self.assertTrue(any("ros2 topic echo --once /lidar/raw_packet" in command for command in recorder.commands))
        self.assertTrue(any("tf2_echo base_link laser_frame" in command for command in recorder.commands))
        self.assertFalse(any("/cmd_vel" in command for command in recorder.commands))
        self.assertFalse(any("A5 60" in command for command in recorder.commands))
        self.assertFalse(result["safe_to_control"])
        self.assertFalse(result["hil_pass"])

    def test_timeout_text_markers_still_count_for_hz_and_tf(self) -> None:
        recorder = CommandRecorder(
            {
                "ros2 topic hz /scan": {
                    "returncode": 124,
                    "ok": False,
                    "stdout_preview": "average rate: 6.250\n",
                    "stderr_preview": "",
                },
                "tf2_echo base_link laser_frame": {
                    "returncode": 124,
                    "ok": False,
                    "stdout_preview": "Translation: [0.000, 0.000, 0.000]\n",
                    "stderr_preview": "",
                },
            }
        )

        result = collector.build_probe_payload(
            expect_existing_topics=True,
            path_exists=lambda _: True,
            path_describer=fake_path_describer,
            url_fetcher=lambda url, timeout: {"ok": True, "status": "loaded", "payload": {"scan_status": "scan_once_observed"}},
            command_runner=recorder,
        )

        self.assertTrue(result["proof"]["scan_hz_observed"])
        self.assertEqual(result["proof"]["scan_hz_average_rate_hz"], 6.25)
        self.assertTrue(result["proof"]["tf_observed"])

    def test_atomic_write_json_creates_readable_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "runtime" / "lidar.json"
            payload = {"schema": "trashbot.o1.lidar_scan_proof.v1", "proof": {"status": "blocked_or_not_observed"}}

            write = collector.atomic_write_json(str(output), payload)

            self.assertTrue(write["ok"])
            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(saved["schema"], "trashbot.o1.lidar_scan_proof.v1")
            self.assertEqual(saved["proof"]["status"], "blocked_or_not_observed")


if __name__ == "__main__":
    unittest.main()
