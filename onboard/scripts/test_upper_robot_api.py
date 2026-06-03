#!/usr/bin/env python3
"""8787 统一上位机 Robot API 的硬件安全单元测试。"""

from __future__ import annotations

import asyncio
import json
import sys
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

    def __init__(self, port: str, baudrate: int, timeout: float) -> None:
        if self.__class__.fail_on_open:
            raise OSError("fake serial open failed")
        # 记录初始化参数，确保实现没有偷偷改 vendor 115200/端口语义。
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.frames: list[bytes] = []
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
        self.assertFalse(result["sends_commands"])
        self.assertFalse(result["robot_control_executed"])

    def test_base_status_does_not_trigger_feedback_request_or_serial_open(self) -> None:
        robot = api.UpperRobotApi("http://127.0.0.1:8088", "/dev/fake-base", 115200, max_speed=0.12)

        result = robot.base_status()

        self.assertEqual(result["feedback_ack"]["t1001_observed"], False)
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


if __name__ == "__main__":
    unittest.main()
