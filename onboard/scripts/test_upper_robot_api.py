#!/usr/bin/env python3
"""8787 统一上位机 Robot API 的硬件安全单元测试。"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import upper_robot_api as api  # noqa: E402


class FakeSerial:
    """fake pyserial：只记录 JSON 行，不打开真实 UART。"""

    instances: list["FakeSerial"] = []
    fail_on_open = False
    fail_on_write = False
    read_lines: list[bytes] = []
    read_line_batches: list[list[bytes]] = []

    def __init__(self, port: str, baudrate: int, timeout: float) -> None:
        if self.__class__.fail_on_open:
            raise OSError("fake serial open failed")
        # 记录初始化参数，确保实现没有偷偷改 vendor 115200/端口语义。
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.frames: list[bytes] = []
        # 多样本测试需要每次打开串口拿到不同反馈，模拟现场逐帧材料。
        if self.__class__.read_line_batches:
            self.read_lines = list(self.__class__.read_line_batches.pop(0))
        else:
            # 每个 fake 实例复制一次预设反馈，避免测试之间共享读游标。
            self.read_lines = list(self.__class__.read_lines)
        self.closed = False
        self.__class__.instances.append(self)

    def write(self, frame: bytes) -> int:
        if self.__class__.fail_on_write:
            raise OSError("fake serial write failed")
        # vendor 协议是一行一个 UTF-8 JSON，测试按 bytes 保留换行边界。
        self.frames.append(frame)
        return len(frame)

    def readline(self) -> bytes:
        # 空 bytes 模拟 pyserial timeout，测试不会阻塞真实硬件。
        if not self.read_lines:
            return b""
        return self.read_lines.pop(0)

    def close(self) -> None:
        self.closed = True

    @classmethod
    def reset(cls) -> None:
        cls.instances = []
        cls.fail_on_open = False
        cls.fail_on_write = False
        cls.read_lines = []
        cls.read_line_batches = []


def install_fake_serial() -> None:
    """把 import serial 指向 fake 模块，避免单测触碰真实设备。"""
    FakeSerial.reset()
    fake_module = types.SimpleNamespace(Serial=FakeSerial)
    sys.modules["serial"] = fake_module


def decoded_frame(fake_serial: FakeSerial) -> dict[str, object]:
    """把 fake 串口写出的单行 JSON 解回对象，便于断言命令边界。"""
    [frame] = fake_serial.frames
    assert frame.endswith(b"\n")
    return json.loads(frame.decode("utf-8"))


class UpperRobotApiSafetyTest(unittest.TestCase):
    def setUp(self) -> None:
        install_fake_serial()

    def test_invalid_manual_direction_returns_structured_failure_without_serial_write(self) -> None:
        robot = api.UpperRobotApi("http://127.0.0.1:8088", "/dev/fake-base", 115200, max_speed=0.12)

        result = asyncio.run(robot.manual_control({"direction": "sideways", "speed": 0.08}))

        self.assertFalse(result["accepted"])
        self.assertEqual(result["error"]["type"], "unsupported_direction")
        self.assertFalse(result["sends_commands"])
        self.assertFalse(result["robot_control_executed"])
        self.assertEqual(FakeSerial.instances, [])

    def test_manual_pulse_is_low_speed_limited_and_always_attempts_stop(self) -> None:
        FakeSerial.read_lines = [b'{"T":1001,"L":0,"R":0,"r":1,"p":2,"y":3,"v":12.4}\n']
        robot = api.UpperRobotApi("http://127.0.0.1:8088", "/dev/fake-base", 115200, max_speed=0.12)

        result = asyncio.run(
            robot.manual_control(
                {"direction": "forward", "speed": 9.0, "duration_ms": 9999, "read_timeout_s": 0.01, "read_window_s": 0.01}
            )
        )

        self.assertTrue(result["accepted"])
        self.assertEqual(result["speed"], 0.12)
        self.assertEqual(result["duration_ms"], api.MAX_PULSE_MS)
        self.assertTrue(result["manual_command_executed"])
        self.assertTrue(result["auto_stop_attempted"])
        self.assertTrue(result["auto_stop_executed"])
        self.assertTrue(result["feedback_after_stop_attempted"])
        self.assertEqual(result["t1001_feedback_status"], "observed")
        self.assertTrue(result["feedback_ack"]["t1001_observed"])
        self.assertFalse(result["feedback_ack"]["robot_ack_connected"])
        self.assertFalse(result["safe_to_control"])
        self.assertFalse(result["hil_pass"])
        self.assertEqual(result["feedback_evidence"]["request"]["command"], {"T": 130})
        self.assertEqual(result["feedback_evidence"]["serial_open"]["port"], "/dev/fake-base")
        self.assertEqual(result["feedback_evidence"]["serial_open"]["baudrate"], 115200)
        self.assertEqual(result["feedback_evidence"]["observed_feedback_types"], [1001])
        self.assertEqual(len(FakeSerial.instances), 3)
        self.assertEqual(decoded_frame(FakeSerial.instances[0]), {"T": 1, "L": 0.12, "R": 0.12})
        self.assertEqual(decoded_frame(FakeSerial.instances[1]), {"T": 1, "L": 0, "R": 0})
        self.assertEqual(decoded_frame(FakeSerial.instances[2]), {"T": 130})

    def test_manual_pulse_preserves_serial_write_failure_and_stop_result(self) -> None:
        FakeSerial.fail_on_write = True
        robot = api.UpperRobotApi("http://127.0.0.1:8088", "/dev/fake-base", 115200, max_speed=0.12)

        result = asyncio.run(robot.manual_control({"direction": "left", "duration_ms": 0}))

        self.assertTrue(result["accepted"])
        self.assertFalse(result["manual_command_executed"])
        self.assertFalse(result["auto_stop_executed"])
        self.assertFalse(result["robot_control_executed"])
        self.assertEqual(len(result["serial_write_failures"]), 2)
        self.assertEqual(result["command_result"]["error"]["type"], "OSError")
        self.assertEqual(result["stop_result"]["error"]["type"], "OSError")
        self.assertFalse(result["feedback_after_stop_attempted"])
        self.assertEqual(result["t1001_feedback_status"], "skipped_due_to_manual_write_failure")
        self.assertEqual(len(FakeSerial.instances), 2)

    def test_stop_payload_robot_control_executed_reflects_stop_write_success(self) -> None:
        ok_payload = api.build_stop_payload("/dev/fake-base", 115200)
        self.assertTrue(ok_payload["stop_result"]["ok"])
        self.assertTrue(ok_payload["robot_control_executed"])

        FakeSerial.fail_on_open = True
        failed_payload = api.build_stop_payload("/dev/fake-base", 115200)
        self.assertFalse(failed_payload["stop_result"]["ok"])
        self.assertFalse(failed_payload["robot_control_executed"])
        self.assertEqual(failed_payload["serial_write_failures"][0]["type"], "OSError")

    def test_radar_status_documents_ttyacm0_ros2_lidar_contract(self) -> None:
        robot = api.UpperRobotApi("http://127.0.0.1:8088", "/dev/fake-base", 115200, max_speed=0.12)

        result = robot.radar_status()

        self.assertEqual(result["baudrate"], 150000)
        self.assertEqual(result["start_command_hex"], "a5 60")
        self.assertEqual(result["stop_command_hex"], "a5 00 a5 65 a5 65")
        self.assertEqual(result["observed_lidar_port_info"]["path"], "/dev/ttyACM0")
        self.assertIn("lidar_serial_port:=/dev/ttyACM0", result["ros2"]["launch"])
        self.assertEqual(result["ros2"]["scan_topic"], "/scan")
        self.assertEqual(result["scan_proof_latest"]["endpoint"], "/api/radar/scan-proof/latest")
        self.assertEqual(result["scan_proof_latest"]["artifact"]["status"], "missing")
        self.assertFalse(result["scan_proof_latest"]["sends_commands"])
        self.assertEqual(result["raw_packet_proof_latest"]["endpoint"], "/api/radar/raw-packet-proof/latest")
        self.assertEqual(result["raw_packet_proof_latest"]["artifact"]["status"], "missing")
        self.assertEqual(result["raw_packet_proof_latest"]["freshness"]["status"], "missing")
        self.assertIsNone(result["raw_packet_proof_latest"]["freshness"]["age_seconds"])
        self.assertFalse(result["raw_packet_proof_latest"]["sends_lidar_start_command"])
        self.assertFalse(result["raw_packet_proof_latest"]["opens_lidar_serial"])
        self.assertFalse(result["sends_commands"])
        self.assertFalse(result["robot_control_executed"])
        self.assertEqual(FakeSerial.instances, [])

    def test_lidar_scan_proof_latest_readback_is_read_only_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "lidar.json"
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                lidar_scan_proof_artifact_path=str(artifact_path),
            )

            missing_status, missing = robot.radar_scan_proof_latest()

            self.assertEqual(missing_status, 404)
            self.assertEqual(missing["artifact"]["status"], "missing")
            self.assertIsNone(missing["latest_result"])
            self.assertFalse(missing["sends_commands"])
            self.assertFalse(missing["sends_motion_commands"])
            self.assertFalse(missing["robot_control_executed"])
            self.assertEqual(FakeSerial.instances, [])

            artifact_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.o1.lidar_scan_proof.v1",
                        "proof": {
                            "status": "blocked_or_not_observed",
                            "scan_once_observed": False,
                            "raw_packet_once_observed": False,
                        },
                    }
                ),
                encoding="utf-8",
            )

            loaded_status, loaded = robot.radar_scan_proof_latest()
            summary = api.summarize_lidar_scan_proof_latest_artifact(str(artifact_path))

            self.assertEqual(loaded_status, 200)
            self.assertEqual(loaded["artifact"]["status"], "loaded")
            self.assertEqual(loaded["latest_result"]["schema"], "trashbot.o1.lidar_scan_proof.v1")
            self.assertFalse(loaded["readback_sends_commands"])
            self.assertEqual(summary["latest_proof_status"], "blocked_or_not_observed")
            self.assertFalse(summary["latest_scan_once_observed"])
            self.assertIsNone(summary["latest_scan_hz_observed"])
            self.assertIsNone(summary["latest_scan_hz_average_rate_hz"])
            self.assertFalse(summary["latest_raw_packet_once_observed"])
            self.assertIsNone(summary["latest_tf_observed"])
            self.assertIsNone(summary["latest_all_required_observations_observed"])
            self.assertIsNone(summary["latest_required_observations"])
            self.assertFalse(summary["sends_commands"])
            self.assertEqual(FakeSerial.instances, [])

            artifact_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.o1.lidar_scan_proof.v1",
                        "proof": {
                            "status": "scan_once_hz_raw_packet_tf_observed",
                            "scan_once_observed": True,
                            "scan_hz_observed": True,
                            "scan_hz_average_rate_hz": 7.25,
                            "raw_packet_once_observed": True,
                            "tf_observed": True,
                            "all_required_observations_observed": True,
                            "required_observations": {
                                "scan_once": {"topic": "/scan", "observed": True, "result_key": "scan_once"},
                                "scan_hz": {"topic": "/scan", "observed": True, "average_rate_hz": 7.25, "result_key": "scan_hz"},
                                "raw_packet_once": {"topic": "/lidar/raw_packet", "observed": True, "result_key": "raw_packet_once"},
                                "tf": {"parent_frame": "base_link", "child_frame": "laser_frame", "observed": True, "result_key": "tf"},
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )

            summary = api.summarize_lidar_scan_proof_latest_artifact(str(artifact_path))

            self.assertEqual(summary["latest_proof_status"], "scan_once_hz_raw_packet_tf_observed")
            self.assertTrue(summary["latest_scan_once_observed"])
            self.assertTrue(summary["latest_scan_hz_observed"])
            self.assertEqual(summary["latest_scan_hz_average_rate_hz"], 7.25)
            self.assertTrue(summary["latest_raw_packet_once_observed"])
            self.assertTrue(summary["latest_tf_observed"])
            self.assertTrue(summary["latest_all_required_observations_observed"])
            self.assertEqual(summary["latest_required_observations"]["scan_hz"]["average_rate_hz"], 7.25)
            self.assertEqual(summary["latest_required_observations"]["tf"]["child_frame"], "laser_frame")
            self.assertFalse(summary["sends_commands"])
            self.assertEqual(FakeSerial.instances, [])

            artifact_path.write_text("{not-json", encoding="utf-8")
            bad_status, bad = robot.radar_scan_proof_latest()

            self.assertEqual(bad_status, 422)
            self.assertEqual(bad["artifact"]["status"], "bad_json")
            self.assertFalse(bad["sends_commands"])
            self.assertEqual(FakeSerial.instances, [])

    def test_lidar_scan_proof_refresh_runs_read_only_collector_contract(self) -> None:
        calls: list[dict[str, object]] = []
        original_runner = api.run_lidar_scan_proof_collector

        def fake_runner(**kwargs: object) -> dict[str, object]:
            """模拟 collector 子进程，证明 upper API 只调只读 proof 入口。"""
            calls.append(kwargs)
            return {
                "command_result": {
                    "mode": "read_only_scan_proof_collector",
                    "executed": True,
                    "ok": True,
                    "script_path": "/fake/o1_lidar_scan_proof_collector.py",
                    "argv": ["python3", "o1_lidar_scan_proof_collector.py", "--expect-existing-topics"],
                    "returncode": 0,
                },
                "collector_payload": {
                    "schema": "trashbot.o1.lidar_scan_proof.v1",
                    "artifact": {"ok": True, "path": str(kwargs["artifact_path"])},
                    "proof": {
                        "status": "blocked_or_not_observed",
                        "scan_once_observed": False,
                        "scan_hz_observed": False,
                        "raw_packet_once_observed": False,
                        "tf_observed": False,
                        "all_required_observations_observed": False,
                    },
                    "blockers": [{"code": "upper_api_scan_not_proven", "detail": "8787 radar scan_status='not_proven'"}],
                    "safe_to_control": False,
                    "sends_motion_commands": False,
                    "robot_control_executed": False,
                },
                "parse_error": None,
            }

        api.run_lidar_scan_proof_collector = fake_runner  # type: ignore[assignment]
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                artifact_path = str(Path(tmpdir) / "lidar_scan_proof_latest.json")
                robot = api.UpperRobotApi(
                    "http://127.0.0.1:8088",
                    "/dev/fake-base",
                    115200,
                    max_speed=0.12,
                    lidar_scan_proof_artifact_path=artifact_path,
                )

                result = asyncio.run(robot.radar_scan_proof_refresh({"timeout_s": 2}))
                status = robot.radar_status()
        finally:
            api.run_lidar_scan_proof_collector = original_runner  # type: ignore[assignment]

        self.assertEqual(api.ROUTE_PATHS["radar_scan_proof_refresh"], "/api/radar/scan-proof/refresh")
        self.assertEqual(calls[0]["artifact_path"], artifact_path)
        self.assertEqual(calls[0]["upper_api_base_url"], "http://127.0.0.1:8787")
        self.assertEqual(calls[0]["timeout_s"], 2.0)
        self.assertEqual(result["endpoint"], "/api/radar/scan-proof/refresh")
        self.assertEqual(result["status"], "refreshed")
        self.assertEqual(result["proof_state"], "blocked_or_not_observed")
        self.assertEqual(result["evidence_type"], "blocked_with_root_cause")
        self.assertEqual(result["artifact_path"], artifact_path)
        self.assertEqual(result["command_result"]["mode"], "read_only_scan_proof_collector")
        self.assertEqual(result["blockers_summary"][0]["code"], "upper_api_scan_not_proven")
        self.assertFalse(result["scan_runtime_proven"])
        self.assertFalse(result["safe_to_control"])
        self.assertFalse(result["sends_commands"])
        self.assertFalse(result["sends_motion_commands"])
        self.assertFalse(result["robot_control_executed"])
        self.assertFalse(result["opens_lidar_serial"])
        self.assertFalse(result["starts_lidar_driver"])
        self.assertIn("/dev/ttyS5", result["blocked_devices_not_opened"])
        self.assertIn("A5 60", result["blocked_commands_not_sent"])
        self.assertEqual(status["controls"]["scan_proof_refresh"]["endpoint"], "/api/radar/scan-proof/refresh")
        self.assertFalse(status["controls"]["scan_proof_refresh"]["opens_lidar_serial"])
        self.assertEqual(FakeSerial.instances, [])

    def test_lidar_raw_packet_proof_latest_readback_missing_loaded_bad_json_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "raw_packet.json"
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                lidar_raw_packet_proof_artifact_path=str(artifact_path),
            )

            missing_status, missing = robot.radar_raw_packet_proof_latest()

            self.assertEqual(missing_status, 404)
            self.assertEqual(missing["artifact"]["status"], "missing")
            self.assertIsNone(missing["latest_result"])
            self.assertFalse(missing["sends_commands"])
            self.assertFalse(missing["sends_lidar_start_command"])
            self.assertFalse(missing["opens_lidar_serial"])
            self.assertFalse(missing["starts_ros2"])
            self.assertFalse(missing["calls_base_manual"])
            self.assertEqual(FakeSerial.instances, [])

            artifact_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.o1.lidar_raw_packet_proof.v1",
                        "generated_at_ms": api.now_ms(),
                        "packet_stats": {
                            "bytes_read": 9086,
                            "sync_header_count": 275,
                            "packets_parse_ok": 275,
                            "points_total": 1923,
                        },
                        "proof": {
                            "status": "raw_packets_parsed",
                            "raw_bytes_observed": True,
                            "sync_header_observed": True,
                            "packet_parse_ok": True,
                            "points_observed": True,
                        },
                    }
                ),
                encoding="utf-8",
            )

            loaded_status, loaded = robot.radar_raw_packet_proof_latest()
            summary = robot.radar_status()["raw_packet_proof_latest"]

            self.assertEqual(loaded_status, 200)
            self.assertEqual(loaded["artifact"]["status"], "loaded")
            self.assertEqual(loaded["latest_result"]["schema"], "trashbot.o1.lidar_raw_packet_proof.v1")
            self.assertFalse(loaded["readback_sends_commands"])
            self.assertFalse(loaded["sends_lidar_start_command"])
            self.assertEqual(summary["latest_proof_status"], "raw_packets_parsed")
            self.assertTrue(summary["raw_bytes_observed"])
            self.assertTrue(summary["sync_header_observed"])
            self.assertTrue(summary["packet_parse_ok"])
            self.assertTrue(summary["points_observed"])
            self.assertEqual(summary["bytes_read"], 9086)
            self.assertEqual(summary["sync_header_count"], 275)
            self.assertEqual(summary["packets_parse_ok"], 275)
            self.assertEqual(summary["points_total"], 1923)
            self.assertTrue(summary["latest_raw_bytes_observed"])
            self.assertTrue(summary["latest_sync_header_observed"])
            self.assertTrue(summary["latest_packet_parse_ok"])
            self.assertTrue(summary["latest_points_observed"])
            self.assertEqual(summary["latest_bytes_read"], 9086)
            self.assertEqual(summary["latest_sync_header_count"], 275)
            self.assertEqual(summary["latest_packets_parse_ok"], 275)
            self.assertEqual(summary["latest_points_total"], 1923)
            self.assertEqual(summary["freshness"]["status"], "fresh")
            self.assertIsInstance(summary["freshness"]["age_seconds"], float)
            self.assertIn("material_freshness_not_hil", summary["freshness"]["basis"])
            self.assertIn("mtime_ms", summary["artifact"])
            self.assertIn("age_ms", summary["artifact"])
            self.assertFalse(summary["opens_lidar_serial"])
            self.assertFalse(summary["starts_ros2"])
            self.assertFalse(summary["calls_base_manual"])
            self.assertEqual(FakeSerial.instances, [])

            old_mtime = time_for_default_stale_artifact()
            os.utime(artifact_path, (old_mtime, old_mtime))
            stale_summary = robot.radar_status()["raw_packet_proof_latest"]

            self.assertEqual(stale_summary["freshness"]["status"], "stale")
            self.assertGreater(stale_summary["freshness"]["age_seconds"], 60)
            self.assertEqual(stale_summary["latest_bytes_read"], stale_summary["bytes_read"])
            self.assertEqual(stale_summary["latest_sync_header_count"], stale_summary["sync_header_count"])

            artifact_path.write_text("{not-json", encoding="utf-8")
            bad_status, bad = robot.radar_raw_packet_proof_latest()
            bad_summary = robot.radar_status()["raw_packet_proof_latest"]

            self.assertEqual(bad_status, 422)
            self.assertEqual(bad["artifact"]["status"], "bad_json")
            self.assertEqual(bad_summary["artifact"]["status"], "bad_json")
            self.assertEqual(bad_summary["freshness"]["status"], "bad_json")
            self.assertIsInstance(bad_summary["freshness"]["age_seconds"], float)
            self.assertIsNone(bad_summary["latest_bytes_read"])
            self.assertFalse(bad["sends_commands"])
            self.assertFalse(bad_summary["sends_lidar_start_command"])
            self.assertEqual(FakeSerial.instances, [])

    def test_base_status_does_not_trigger_feedback_request_or_serial_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                feedback_samples_artifact_path=str(Path(tmpdir) / "missing.json"),
            )

            result = robot.base_status()

        self.assertEqual(result["feedback_ack"]["t1001_observed"], False)
        self.assertEqual(result["feedback_samples_latest"]["endpoint"], "/api/base/feedback-samples/latest")
        self.assertEqual(result["feedback_samples_latest"]["artifact"]["status"], "missing")
        self.assertEqual(result["feedback_samples_latest"]["freshness"]["status"], "missing")
        self.assertFalse(result["feedback_samples_latest"]["readback_sends_commands"])
        self.assertFalse(result["feedback_samples_latest"]["sends_commands"])
        self.assertFalse(result["feedback_samples_latest"]["sends_motion_commands"])
        self.assertFalse(result["feedback_samples_latest"]["robot_control_executed"])
        self.assertEqual(FakeSerial.instances, [])

    def test_feedback_request_sends_only_t130_and_parses_t1001(self) -> None:
        FakeSerial.read_lines = [
            b"not-json\n",
            b'{"T":1001,"L":0,"R":0,"r":1,"p":2,"y":3,"v":12.4}\n',
            b'{"T":1002}\n',
        ]
        robot = api.UpperRobotApi("http://127.0.0.1:8088", "/dev/fake-base", 115200, max_speed=0.12)

        result = asyncio.run(robot.base_feedback_request({"read_timeout_s": 0.01, "read_window_s": 0.01}))

        self.assertEqual(len(FakeSerial.instances), 1)
        self.assertEqual(result["serial_write"]["command"], {"T": 130})
        self.assertTrue(FakeSerial.instances[0].closed)
        self.assertEqual(result["serial_open"]["ok"], True)
        self.assertEqual(result["serial_write"]["ok"], True)
        self.assertEqual(result["read_line_count"], 3)
        self.assertEqual(result["parsed_json_count"], 2)
        self.assertEqual(result["invalid_json_count"], 1)
        self.assertEqual(result["observed_feedback_types"], [1001, 1002])
        self.assertEqual(result["t1001_feedback_status"], "observed")
        self.assertTrue(result["feedback_ack"]["t1001_observed"])
        self.assertFalse(result["feedback_ack"]["robot_ack_connected"])
        self.assertFalse(result["safe_to_control"])
        self.assertFalse(result["sends_motion_commands"])
        self.assertFalse(result["robot_control_executed"])
        self.assertFalse(result["delivery_success"])
        self.assertFalse(result["hil_pass"])
        self.assertIn("T=1", result["blocked_commands_not_sent"])
        self.assertIn("T=13", result["blocked_commands_not_sent"])
        self.assertIn("T=131", result["blocked_commands_not_sent"])
        self.assertIn("cmd_vel", result["blocked_commands_not_sent"])

    def test_feedback_request_write_failure_is_fail_closed(self) -> None:
        FakeSerial.fail_on_write = True
        robot = api.UpperRobotApi("http://127.0.0.1:8088", "/dev/fake-base", 115200, max_speed=0.12)

        result = asyncio.run(robot.base_feedback_request({"read_timeout_s": 0.01, "read_window_s": 0.01}))

        self.assertEqual(result["serial_write"]["command"], {"T": 130})
        self.assertEqual(result["serial_open"]["ok"], True)
        self.assertEqual(result["serial_write"]["ok"], False)
        self.assertEqual(result["t1001_feedback_status"], "write_failed")
        self.assertEqual(result["read_line_count"], 0)
        self.assertFalse(result["feedback_ack"]["t1001_observed"])
        self.assertFalse(result["safe_to_control"])
        self.assertFalse(result["sends_motion_commands"])
        self.assertFalse(result["robot_control_executed"])

    def test_feedback_samples_collects_multiple_t130_samples_and_aggregates_t1001(self) -> None:
        FakeSerial.read_lines = [
            b'{"T":1001,"L":0,"R":0,"r":1,"p":2,"y":3,"v":12.4}\n',
            b'{"T":130}\n',
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                feedback_samples_artifact_path=str(Path(tmpdir) / "latest.json"),
            )

            result = asyncio.run(
                robot.base_feedback_samples(
                    {"sample_count": 3, "sample_interval_s": 0, "read_timeout_s": 0.01, "read_window_s": 0.01}
                )
            )

        self.assertEqual(result["schema"], "trashbot.upper_robot_api.v1.base_feedback_samples_result")
        self.assertEqual(result["requested_sample_count"], 3)
        self.assertEqual(result["completed_sample_count"], 3)
        self.assertEqual(result["t1001_observed_count"], 3)
        self.assertEqual(result["observed_feedback_types"], [130, 1001])
        self.assertTrue(result["all_samples_observed_t1001"])
        self.assertFalse(result["partial_samples_observed_t1001"])
        self.assertTrue(result["feedback_ack"]["t1001_observed"])
        self.assertFalse(result["feedback_ack"]["robot_ack_connected"])
        self.assertEqual(len(FakeSerial.instances), 3)
        for fake_serial in FakeSerial.instances:
            self.assertEqual(decoded_frame(fake_serial), {"T": 130})
        self.assertFalse(result["safe_to_control"])
        self.assertFalse(result["sends_motion_commands"])
        self.assertFalse(result["robot_control_executed"])
        self.assertFalse(result["delivery_success"])
        self.assertFalse(result["hil_pass"])
        self.assertIn("/api/base/manual", result["blocked_commands_not_sent"])
        self.assertEqual(result["artifact"]["write"]["ok"], True)

    def test_feedback_samples_partial_t1001_remains_fail_closed(self) -> None:
        FakeSerial.read_line_batches = [
            [b'{"T":1001,"L":0,"R":0,"r":1,"p":2,"y":3,"v":12.4}\n'],
            [b'{"T":1002}\n'],
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                feedback_samples_artifact_path=str(Path(tmpdir) / "latest.json"),
            )

            result = asyncio.run(
                robot.base_feedback_samples(
                    {"sample_count": 2, "sample_interval_s": 0, "read_timeout_s": 0.01, "read_window_s": 0.01}
                )
            )

        self.assertEqual(result["t1001_observed_count"], 1)
        self.assertFalse(result["all_samples_observed_t1001"])
        self.assertTrue(result["partial_samples_observed_t1001"])
        self.assertEqual(result["samples"][0]["t1001_feedback_status"], "observed")
        self.assertEqual(result["samples"][1]["t1001_feedback_status"], "not_observed_after_t130")
        self.assertFalse(result["safe_to_control"])
        self.assertFalse(result["sends_motion_commands"])
        self.assertFalse(result["robot_control_executed"])

    def test_feedback_samples_persists_latest_artifact_and_latest_readback_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = str(Path(tmpdir) / "latest.json")
            FakeSerial.read_lines = [b'{"T":1001,"v":12.4}\n']
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                feedback_samples_artifact_path=artifact_path,
            )

            result = asyncio.run(
                robot.base_feedback_samples(
                    {"sample_count": 2, "sample_interval_s": 0, "read_timeout_s": 0.01, "read_window_s": 0.01}
                )
            )

            self.assertEqual(result["artifact"]["path"], artifact_path)
            self.assertTrue(result["artifact"]["write"]["ok"])
            saved = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
            self.assertEqual(saved["schema"], "trashbot.upper_robot_api.v1.base_feedback_samples_result")
            self.assertEqual(saved["t1001_observed_count"], 2)

            FakeSerial.reset()
            http_status, latest = robot.base_feedback_samples_latest()

            self.assertEqual(http_status, 200)
            self.assertTrue(latest["artifact"]["ok"])
            self.assertEqual(latest["artifact"]["status"], "loaded")
            self.assertEqual(latest["latest_result"]["t1001_observed_count"], 2)
            self.assertFalse(latest["readback_sends_commands"])
            self.assertFalse(latest["sends_commands"])
            self.assertFalse(latest["sends_motion_commands"])
            self.assertFalse(latest["robot_control_executed"])
            self.assertEqual(FakeSerial.instances, [])

    def test_feedback_samples_latest_summary_reports_fresh_and_stale_without_serial_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "latest.json"
            artifact_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.upper_robot_api.v1.base_feedback_samples_result",
                        "generated_at_ms": api.now_ms(),
                        "t1001_observed_count": 3,
                        "all_samples_observed_t1001": True,
                    }
                ),
                encoding="utf-8",
            )

            fresh = api.summarize_feedback_samples_latest_artifact(str(artifact_path), stale_after_ms=60_000)

            self.assertEqual(fresh["artifact"]["status"], "loaded")
            self.assertTrue(fresh["artifact"]["ok"])
            self.assertEqual(fresh["freshness"]["status"], "fresh")
            self.assertEqual(fresh["latest_t1001_observed_count"], 3)
            self.assertTrue(fresh["latest_all_samples_observed_t1001"])
            self.assertIn("mtime_ms", fresh["artifact"])
            self.assertIn("age_ms", fresh["artifact"])
            self.assertFalse(fresh["sends_commands"])
            self.assertFalse(fresh["sends_motion_commands"])
            self.assertFalse(fresh["robot_control_executed"])
            self.assertEqual(FakeSerial.instances, [])

            old_mtime = time_for_stale_artifact()
            os.utime(artifact_path, (old_mtime, old_mtime))

            stale = api.summarize_feedback_samples_latest_artifact(str(artifact_path), stale_after_ms=1)

            self.assertEqual(stale["artifact"]["status"], "loaded")
            self.assertEqual(stale["freshness"]["status"], "stale")
            self.assertEqual(FakeSerial.instances, [])

    def test_feedback_samples_latest_missing_or_bad_json_is_fail_closed_without_serial_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = str(Path(tmpdir) / "missing.json")
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                feedback_samples_artifact_path=missing_path,
            )

            missing_status, missing = robot.base_feedback_samples_latest()

            self.assertEqual(missing_status, 404)
            self.assertEqual(missing["artifact"]["status"], "missing")
            self.assertIsNone(missing["latest_result"])
            self.assertFalse(missing["sends_commands"])
            self.assertFalse(missing["robot_control_executed"])
            self.assertEqual(FakeSerial.instances, [])

            bad_path = Path(tmpdir) / "bad.json"
            bad_path.write_text("{not-json", encoding="utf-8")
            bad_robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                feedback_samples_artifact_path=str(bad_path),
            )

            bad_status, bad = bad_robot.base_feedback_samples_latest()

            self.assertEqual(bad_status, 422)
            self.assertEqual(bad["artifact"]["status"], "bad_json")
            self.assertIsNone(bad["latest_result"])
            self.assertFalse(bad["sends_commands"])
            self.assertFalse(bad["sends_motion_commands"])
            self.assertEqual(FakeSerial.instances, [])

            bad_summary = api.summarize_feedback_samples_latest_artifact(str(bad_path))
            self.assertEqual(bad_summary["artifact"]["status"], "bad_json")
            self.assertEqual(bad_summary["freshness"]["status"], "bad_json")
            self.assertFalse(bad_summary["sends_commands"])

            list_path = Path(tmpdir) / "list.json"
            list_path.write_text("[]", encoding="utf-8")
            list_summary = api.summarize_feedback_samples_latest_artifact(str(list_path))
            self.assertEqual(list_summary["artifact"]["status"], "json_not_object")
            self.assertEqual(list_summary["freshness"]["status"], "json_not_object")

    def test_feedback_samples_route_exists_and_status_does_not_trigger_it(self) -> None:
        robot = api.UpperRobotApi("http://127.0.0.1:8088", "/dev/fake-base", 115200, max_speed=0.12)

        status = robot.base_status()

        self.assertEqual(api.ROUTE_PATHS["base_feedback_samples"], "/api/base/feedback-samples")
        self.assertEqual(api.ROUTE_PATHS["base_feedback_samples_latest"], "/api/base/feedback-samples/latest")
        self.assertEqual(api.ROUTE_PATHS["radar_raw_packet_proof_latest"], "/api/radar/raw-packet-proof/latest")
        self.assertEqual(status["feedback_ack"]["t1001_observed"], False)
        self.assertEqual(FakeSerial.instances, [])

    def test_radar_start_stop_default_to_software_guard_without_base_uart(self) -> None:
        robot = api.UpperRobotApi("http://127.0.0.1:8088", "/dev/fake-base", 115200, max_speed=0.12)

        start = robot.radar_control("start")
        stop = robot.radar_control("stop")
        radar_status = robot.radar_status()

        self.assertEqual(start["endpoint"], "/api/radar/start")
        self.assertEqual(stop["endpoint"], "/api/radar/stop")
        self.assertEqual(start["command_result"]["mode"], "dry_run_stub")
        self.assertFalse(start["command_result"]["executed"])
        self.assertTrue(start["software_guard"])
        self.assertTrue(start["not_proven"])
        self.assertEqual(start["status"], "not_proven")
        self.assertFalse(start["scan_runtime_proven"])
        self.assertFalse(start["base_uart_touched"])
        self.assertFalse(start["uses_base_uart"])
        self.assertFalse(start["sends_base_motion_commands"])
        self.assertFalse(start["robot_control_executed"])
        self.assertIn("/dev/ttyS5", start["blocked_devices_not_touched"])
        self.assertIn("/api/base/manual", start["blocked_commands_not_sent"])
        self.assertEqual(radar_status["controls"]["start"]["endpoint"], "/api/radar/start")
        self.assertEqual(radar_status["controls"]["stop"]["endpoint"], "/api/radar/stop")
        self.assertEqual(FakeSerial.instances, [])

    def test_radar_start_configured_command_executes_but_remains_not_proven(self) -> None:
        command = f"{sys.executable} -c \"print('lidar-start-stub')\""
        robot = api.UpperRobotApi(
            "http://127.0.0.1:8088",
            "/dev/fake-base",
            115200,
            max_speed=0.12,
            radar_start_command=command,
        )

        result = robot.radar_control("start")

        self.assertTrue(result["command_result"]["executed"])
        self.assertTrue(result["command_result"]["ok"])
        self.assertIn("lidar-start-stub", result["command_result"]["stdout_preview"])
        self.assertTrue(result["configured_command"]["configured"])
        self.assertEqual(result["configured_command"]["env"], "ROBER_RADAR_START_COMMAND")
        self.assertEqual(result["status"], "not_proven")
        self.assertTrue(result["not_proven"])
        self.assertFalse(result["scan_runtime_proven"])
        self.assertFalse(result["safe_to_control"])
        self.assertFalse(result["robot_control_executed"])
        self.assertEqual(FakeSerial.instances, [])

    def test_map_lifecycle_and_localize_reset_are_fail_closed_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                map_artifact_dir=tmpdir,
                localization_artifact_path=str(Path(tmpdir) / "localize.json"),
            )

            start = robot.map_control("start", {"map_name": "lab"})
            reset = robot.map_control("reset", {})
            save = robot.map_control("save", {"artifact_path": str(Path(tmpdir) / "lab.yaml")})
            localize = robot.localize_reset({"pose": {"x": 1.0, "y": 2.0, "yaw": 0.0}})

        self.assertEqual(start["endpoint"], "/api/map/start")
        self.assertEqual(reset["endpoint"], "/api/map/reset")
        self.assertEqual(save["endpoint"], "/api/map/save")
        self.assertEqual(localize["endpoint"], "/api/localize/reset")
        self.assertEqual(start["command_result"]["mode"], "dry_run_stub")
        self.assertEqual(localize["target_ros2_topic"], "/initialpose")
        self.assertEqual(localize["requested_pose"], {"x": 1.0, "y": 2.0, "yaw": 0.0})
        for payload in (start, reset, save, localize):
            self.assertEqual(payload["status"], "not_proven")
            self.assertTrue(payload["software_guard"])
            self.assertTrue(payload["not_proven"])
            self.assertFalse(payload["map_artifact_proven"])
            self.assertFalse(payload["localization_proven"])
            self.assertFalse(payload["uses_base_uart"])
            self.assertFalse(payload["sends_base_motion_commands"])
            self.assertFalse(payload["robot_control_executed"])
            self.assertFalse(payload["safe_to_control"])
        self.assertEqual(FakeSerial.instances, [])

    def test_map_list_reads_artifacts_only_and_unified_status_exposes_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "lab.yaml").write_text("image: lab.pgm\n", encoding="utf-8")
            Path(tmpdir, "lab.pgm").write_bytes(b"P5\n1 1\n255\n\0")
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                map_artifact_dir=tmpdir,
            )

            async def fake_camera_health() -> tuple[int, dict[str, object]]:
                """本测试只验证 routes/status，不依赖 aiohttp camera proxy。"""
                return 200, {"status": "stubbed", "video_source": "test"}

            robot.camera_health = fake_camera_health  # type: ignore[method-assign]
            listing = robot.map_list()
            status = asyncio.run(robot.unified_status())

        self.assertEqual(listing["endpoint"], "/api/map/list")
        self.assertEqual(listing["map_count"], 2)
        self.assertEqual(sorted(item["name"] for item in listing["maps"]), ["lab.pgm", "lab.yaml"])
        self.assertTrue(listing["software_guard"])
        self.assertTrue(listing["not_proven"])
        self.assertFalse(listing["sends_commands"])
        self.assertFalse(listing["sends_base_motion_commands"])
        self.assertEqual(status["routes"]["radar_start"], "/api/radar/start")
        self.assertEqual(status["routes"]["radar_stop"], "/api/radar/stop")
        self.assertEqual(status["routes"]["map_start"], "/api/map/start")
        self.assertEqual(status["routes"]["map_reset"], "/api/map/reset")
        self.assertEqual(status["routes"]["map_save"], "/api/map/save")
        self.assertEqual(status["routes"]["map_load"], "/api/map/load")
        self.assertEqual(status["routes"]["map_list"], "/api/map/list")
        self.assertEqual(status["routes"]["map_proof_latest"], "/api/map/proof/latest")
        self.assertEqual(status["routes"]["localize_reset"], "/api/localize/reset")
        self.assertEqual(status["routes"]["localize_proof_latest"], "/api/localize/proof/latest")
        self.assertEqual(status["routes"]["nav2_status"], "/api/nav2/status")
        self.assertEqual(status["routes"]["nav2_start"], "/api/nav2/start")
        self.assertEqual(status["routes"]["nav2_stop"], "/api/nav2/stop")
        self.assertEqual(status["routes"]["elevator_status"], "/api/elevator/status")
        self.assertEqual(status["map"]["status"], "not_proven")
        self.assertEqual(status["localization"]["status"], "not_proven")
        self.assertEqual(status["nav2"]["status"], "not_proven")
        self.assertEqual(status["elevator"]["status"], "not_proven")
        self.assertEqual(FakeSerial.instances, [])

    def test_runtime_artifact_readbacks_cover_map_localize_nav2_and_elevator_without_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            map_proof_path = Path(tmpdir) / "map_proof.json"
            localize_path = Path(tmpdir) / "localize.json"
            nav2_path = Path(tmpdir) / "nav2.json"
            elevator_path = Path(tmpdir) / "elevator.json"
            map_proof_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.upper_robot_api.v1.map_lifecycle_runtime_proof",
                        "proof": {
                            "status": "fixture_map_material",
                            "evidence_ref": "map-fixture-001",
                            "map_once_observed": True,
                            "map_file_observed": True,
                            "map_metadata_observed": True,
                            "slam_toolbox_state": "active",
                        },
                    }
                ),
                encoding="utf-8",
            )
            localize_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.upper_robot_api.v1.localization_reset_artifact",
                        "proof": {
                            "status": "fixture_localization_material",
                            "initialpose_published": True,
                            "amcl_pose_observed": True,
                            "tf_fresh": True,
                            "pose_fresh": True,
                        },
                    }
                ),
                encoding="utf-8",
            )
            nav2_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.upper_robot_api.v1.nav2_lifecycle_runtime_proof",
                        "proof": {
                            "status": "fixture_nav2_material",
                            "map_server_active": True,
                            "amcl_active": True,
                            "planner_active": True,
                            "controller_active": True,
                            "scan_consumed": True,
                            "path_generated": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            elevator_path.write_text(
                json.dumps(
                    {
                        "schema": "trashbot.elevator_status_runtime_boundary.v1",
                        "proof": {
                            "status": "fixture_elevator_status",
                            "phase": "waiting_target_floor",
                            "opencv_evidence_ref": "elevator-fixture-001",
                            "target_floor_confirmed": False,
                            "safe_to_exit": False,
                            "manual_handoff_required": True,
                        },
                    }
                ),
                encoding="utf-8",
            )
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                map_lifecycle_proof_artifact_path=str(map_proof_path),
                localization_artifact_path=str(localize_path),
                nav2_lifecycle_artifact_path=str(nav2_path),
                elevator_status_artifact_path=str(elevator_path),
            )

            map_http_status, map_latest = robot.map_proof_latest()
            localize_http_status, localize_latest = robot.localize_proof_latest()
            nav2_status = robot.nav2_status()
            elevator_status = robot.elevator_status()

        self.assertEqual(map_http_status, 200)
        self.assertEqual(map_latest["artifact"]["status"], "loaded")
        self.assertEqual(map_latest["latest_result"]["proof"]["evidence_ref"], "map-fixture-001")
        self.assertFalse(map_latest["readback_sends_commands"])
        self.assertFalse(map_latest["starts_ros2"])
        self.assertFalse(map_latest["safe_to_control"])
        self.assertEqual(localize_http_status, 200)
        self.assertFalse(localize_latest["readback_sends_commands"])
        self.assertEqual(localize_latest["latest_result"]["proof"]["status"], "fixture_localization_material")
        self.assertEqual(nav2_status["proof_latest"]["latest_proof_status"], "fixture_nav2_material")
        self.assertTrue(nav2_status["proof_latest"]["latest_map_server_active"])
        self.assertTrue(nav2_status["proof_latest"]["latest_scan_consumed"])
        self.assertFalse(nav2_status["proof_latest"]["latest_path_generated"])
        self.assertFalse(nav2_status["nav2_runtime_proven"])
        self.assertEqual(elevator_status["proof_latest"]["latest_elevator_phase"], "waiting_target_floor")
        self.assertEqual(elevator_status["proof_latest"]["latest_opencv_evidence_ref"], "elevator-fixture-001")
        self.assertTrue(elevator_status["proof_latest"]["latest_handoff_required"])
        self.assertFalse(elevator_status["elevator_runtime_proven"])
        self.assertEqual(FakeSerial.instances, [])

    def test_runtime_artifact_readbacks_missing_and_bad_json_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            map_proof_path = Path(tmpdir) / "missing_map_proof.json"
            localize_path = Path(tmpdir) / "missing_localize.json"
            nav2_path = Path(tmpdir) / "missing_nav2.json"
            elevator_path = Path(tmpdir) / "missing_elevator.json"
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                map_lifecycle_proof_artifact_path=str(map_proof_path),
                localization_artifact_path=str(localize_path),
                nav2_lifecycle_artifact_path=str(nav2_path),
                elevator_status_artifact_path=str(elevator_path),
            )

            missing_map_status, missing_map = robot.map_proof_latest()
            missing_localize_status, missing_localize = robot.localize_proof_latest()
            missing_nav2 = robot.nav2_status()["proof_latest"]
            missing_elevator = robot.elevator_status()["proof_latest"]

            self.assertEqual(missing_map_status, 404)
            self.assertEqual(missing_localize_status, 404)
            self.assertEqual(missing_nav2["http_status"], 404)
            self.assertEqual(missing_elevator["http_status"], 404)
            for payload in (missing_map, missing_localize, missing_nav2, missing_elevator):
                self.assertEqual(payload["artifact"]["status"], "missing")
                self.assertTrue(payload["software_guard"])
                self.assertTrue(payload["not_proven"])
                self.assertFalse(payload["readback_sends_commands"])
                self.assertFalse(payload["sends_commands"])
                self.assertFalse(payload["starts_ros2"])
                self.assertFalse(payload["robot_control_executed"])
                self.assertFalse(payload["safe_to_control"])

            for artifact_path in (map_proof_path, localize_path, nav2_path, elevator_path):
                artifact_path.write_text("{not-json", encoding="utf-8")

            bad_map_status, bad_map = robot.map_proof_latest()
            bad_localize_status, bad_localize = robot.localize_proof_latest()
            bad_nav2 = robot.nav2_status()["proof_latest"]
            bad_elevator = robot.elevator_status()["proof_latest"]

            self.assertEqual(bad_map_status, 422)
            self.assertEqual(bad_localize_status, 422)
            self.assertEqual(bad_nav2["http_status"], 422)
            self.assertEqual(bad_elevator["http_status"], 422)
            for payload in (bad_map, bad_localize, bad_nav2, bad_elevator):
                self.assertEqual(payload["artifact"]["status"], "bad_json")
                self.assertTrue(payload["software_guard"])
                self.assertTrue(payload["not_proven"])
                self.assertFalse(payload["readback_sends_commands"])
                self.assertFalse(payload["sends_commands"])
                self.assertFalse(payload["starts_ros2"])
                self.assertFalse(payload["robot_control_executed"])
                self.assertFalse(payload["safe_to_control"])

        self.assertEqual(FakeSerial.instances, [])

    def test_nav2_configured_command_executes_but_remains_not_proven(self) -> None:
        command = f"{sys.executable} -c \"print('nav2-start-stub')\""
        robot = api.UpperRobotApi(
            "http://127.0.0.1:8088",
            "/dev/fake-base",
            115200,
            max_speed=0.12,
            nav2_start_command=command,
        )

        result = robot.nav2_control("start")

        self.assertEqual(result["endpoint"], "/api/nav2/start")
        self.assertTrue(result["command_result"]["executed"])
        self.assertTrue(result["command_result"]["ok"])
        self.assertIn("nav2-start-stub", result["command_result"]["stdout_preview"])
        self.assertTrue(result["configured_command"]["configured"])
        self.assertEqual(result["configured_command"]["env"], "ROBER_NAV2_START_COMMAND")
        self.assertEqual(result["status"], "not_proven")
        self.assertTrue(result["not_proven"])
        self.assertFalse(result["nav2_lifecycle_status"]["proof_latest"]["nav2_runtime_proven"])
        self.assertFalse(result["robot_control_executed"])
        self.assertFalse(result["safe_to_control"])
        self.assertEqual(FakeSerial.instances, [])

    def test_operator_report_post_persists_latest_and_readback_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = str(Path(tmpdir) / "operator_report_latest.json")
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                operator_report_artifact_path=artifact_path,
            )

            result = robot.operator_report(
                {
                    "evidence_ref": "operator_field_report_pending",
                    "note": "not_proven: waiting for field evidence",
                    "operator_present": True,
                    "physical_clearance_confirmed": True,
                    "emergency_stop_ready": True,
                }
            )

            self.assertEqual(result["schema"], "trashbot.upper_robot_api.v1.operator_report_result")
            self.assertEqual(result["endpoint"], "/api/operator/report")
            self.assertEqual(api.ROUTE_PATHS["operator_report"], "/api/operator/report")
            self.assertEqual(result["operator_report_status"], "ready_for_execution")
            self.assertEqual(result["operator_report"]["evidence_ref"], "operator_field_report_pending")
            self.assertTrue(result["artifact"]["write"]["ok"])
            self.assertFalse(result["safe_to_control"])
            self.assertFalse(result["robot_control_executed"])
            self.assertFalse(result["sends_commands"])
            self.assertFalse(result["sends_motion_commands"])
            self.assertIn("T=1001", result["does_not_replace"])
            self.assertIn("/api/base/stop", result["does_not_replace"])

            FakeSerial.reset()
            http_status, latest = robot.operator_report_latest()

            self.assertEqual(http_status, 200)
            self.assertEqual(latest["artifact"]["status"], "loaded")
            self.assertEqual(latest["latest_result"]["operator_report_status"], "ready_for_execution")
            self.assertFalse(latest["readback_sends_commands"])
            self.assertFalse(latest["sends_commands"])
            self.assertFalse(latest["sends_motion_commands"])
            self.assertFalse(latest["robot_control_executed"])
            self.assertFalse(latest["safe_to_control"])
            self.assertEqual(FakeSerial.instances, [])

    def test_operator_report_latest_missing_and_bad_json_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = str(Path(tmpdir) / "missing_operator_report.json")
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                operator_report_artifact_path=missing_path,
            )

            missing_status, missing = robot.operator_report_latest()

            self.assertEqual(missing_status, 404)
            self.assertEqual(missing["artifact"]["status"], "missing")
            self.assertIsNone(missing["latest_result"])
            self.assertFalse(missing["sends_commands"])
            self.assertFalse(missing["robot_control_executed"])

            bad_path = Path(tmpdir) / "bad_operator_report.json"
            bad_path.write_text("{not-json", encoding="utf-8")
            bad_robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                operator_report_artifact_path=str(bad_path),
            )

            bad_status, bad = bad_robot.operator_report_latest()

            self.assertEqual(bad_status, 422)
            self.assertEqual(bad["artifact"]["status"], "bad_json")
            self.assertFalse(bad["readback_sends_commands"])
            self.assertEqual(FakeSerial.instances, [])


class UpperRobotApiHttpRouteTest(unittest.IsolatedAsyncioTestCase):
    async def test_radar_scan_proof_refresh_http_post_is_not_405_and_stays_non_motion(self) -> None:
        try:
            from aiohttp.test_utils import TestClient, TestServer
        except Exception as exc:  # noqa: BLE001 - 本机缺 aiohttp 时保留类方法回归作为必跑证明。
            self.skipTest(f"aiohttp test client unavailable: {exc}")

        calls: list[dict[str, object]] = []
        original_runner = api.run_lidar_scan_proof_collector

        def fake_runner(**kwargs: object) -> dict[str, object]:
            """HTTP route smoke 只验证 8787 调度边界，不运行真实 ROS2 topic 命令。"""
            calls.append(kwargs)
            return {
                "command_result": {
                    "mode": "read_only_scan_proof_collector",
                    "executed": True,
                    "ok": True,
                    "script_path": "/fake/o1_lidar_scan_proof_collector.py",
                    "returncode": 0,
                },
                "collector_payload": {
                    "schema": "trashbot.o1.lidar_scan_proof.v1",
                    "artifact": {"ok": True, "path": str(kwargs["artifact_path"])},
                    "proof": {
                        "status": "scan_once_hz_raw_packet_tf_observed",
                        "scan_once_observed": True,
                        "scan_hz_observed": True,
                        "scan_hz_average_rate_hz": 7.5,
                        "raw_packet_once_observed": True,
                        "tf_observed": True,
                        "all_required_observations_observed": True,
                    },
                    "blockers": [],
                },
                "parse_error": None,
            }

        api.run_lidar_scan_proof_collector = fake_runner  # type: ignore[assignment]
        install_fake_serial()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                robot = api.UpperRobotApi(
                    "http://127.0.0.1:8088",
                    "/dev/fake-base",
                    115200,
                    max_speed=0.12,
                    lidar_scan_proof_artifact_path=str(Path(tmpdir) / "lidar_scan_proof_latest.json"),
                )
                client = TestClient(TestServer(api.create_app(robot)))
                await client.start_server()
                try:
                    response = await client.post("/api/radar/scan-proof/refresh", json={"timeout_s": 1})
                    body = await response.json()
                finally:
                    await client.close()
        finally:
            api.run_lidar_scan_proof_collector = original_runner  # type: ignore[assignment]

        self.assertEqual(response.status, 200)
        self.assertEqual(body["endpoint"], "/api/radar/scan-proof/refresh")
        self.assertEqual(body["evidence_type"], "robot_runtime_material")
        self.assertTrue(body["scan_runtime_proven"])
        self.assertTrue(body["ros2_runtime_proven"])
        self.assertFalse(body["safe_to_control"])
        self.assertFalse(body["sends_motion_commands"])
        self.assertFalse(body["robot_control_executed"])
        self.assertFalse(body["opens_lidar_serial"])
        self.assertEqual(calls[0]["timeout_s"], 1.0)
        self.assertEqual(FakeSerial.instances, [])

    async def test_operator_report_http_post_and_get_are_not_405_when_aiohttp_is_available(self) -> None:
        try:
            from aiohttp.test_utils import TestClient, TestServer
        except Exception as exc:  # noqa: BLE001 - 本机缺 aiohttp 时保留类方法回归作为必跑证明。
            self.skipTest(f"aiohttp test client unavailable: {exc}")

        install_fake_serial()
        with tempfile.TemporaryDirectory() as tmpdir:
            robot = api.UpperRobotApi(
                "http://127.0.0.1:8088",
                "/dev/fake-base",
                115200,
                max_speed=0.12,
                operator_report_artifact_path=str(Path(tmpdir) / "operator_report_latest.json"),
            )
            client = TestClient(TestServer(api.create_app(robot)))
            await client.start_server()
            try:
                post_response = await client.post(
                    "/api/operator/report",
                    json={"evidence_ref": "operator_field_report_pending", "note": "route smoke"},
                )
                post_body = await post_response.json()
                get_response = await client.get("/api/operator/report")
                get_body = await get_response.json()
            finally:
                await client.close()

        self.assertNotEqual(post_response.status, 405)
        self.assertNotEqual(get_response.status, 405)
        self.assertEqual(post_response.status, 200)
        self.assertEqual(get_response.status, 200)
        self.assertEqual(post_body["endpoint"], "/api/operator/report")
        self.assertEqual(get_body["latest_result"]["operator_report"]["evidence_ref"], "operator_field_report_pending")
        self.assertEqual(FakeSerial.instances, [])


def time_for_stale_artifact() -> float:
    """让 artifact mtime 落到过去，验证 freshness 不依赖真实硬件时间。"""
    return (api.now_ms() / 1000.0) - 120.0


def time_for_default_stale_artifact() -> float:
    """默认 15 分钟窗口需要更旧的 mtime，才能验证 raw packet freshness stale。"""
    return (api.now_ms() / 1000.0) - 1200.0


if __name__ == "__main__":
    unittest.main()
