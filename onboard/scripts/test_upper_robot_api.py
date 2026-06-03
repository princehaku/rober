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
        robot = api.UpperRobotApi("http://127.0.0.1:8088", "/dev/fake-base", 115200, max_speed=0.12)

        result = asyncio.run(robot.manual_control({"direction": "forward", "speed": 9.0, "duration_ms": 9999}))

        self.assertTrue(result["accepted"])
        self.assertEqual(result["speed"], 0.12)
        self.assertEqual(result["duration_ms"], api.MAX_PULSE_MS)
        self.assertTrue(result["manual_command_executed"])
        self.assertTrue(result["auto_stop_attempted"])
        self.assertTrue(result["auto_stop_executed"])
        self.assertFalse(result["feedback_ack"]["t1001_observed"])
        self.assertEqual(len(FakeSerial.instances), 2)
        self.assertEqual(decoded_frame(FakeSerial.instances[0]), {"T": 1, "L": 0.12, "R": 0.12})
        self.assertEqual(decoded_frame(FakeSerial.instances[1]), {"T": 1, "L": 0, "R": 0})

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
        self.assertFalse(result["sends_commands"])
        self.assertFalse(result["robot_control_executed"])

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
            self.assertFalse(summary["sends_commands"])
            self.assertEqual(FakeSerial.instances, [])

            artifact_path.write_text("{not-json", encoding="utf-8")
            bad_status, bad = robot.radar_scan_proof_latest()

            self.assertEqual(bad_status, 422)
            self.assertEqual(bad["artifact"]["status"], "bad_json")
            self.assertFalse(bad["sends_commands"])
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
        self.assertEqual(status["feedback_ack"]["t1001_observed"], False)
        self.assertEqual(FakeSerial.instances, [])


def time_for_stale_artifact() -> float:
    """让 artifact mtime 落到过去，验证 freshness 不依赖真实硬件时间。"""
    return (api.now_ms() / 1000.0) - 120.0


if __name__ == "__main__":
    unittest.main()
