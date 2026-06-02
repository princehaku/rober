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

    def __init__(self, port: str, baudrate: int, timeout: float) -> None:
        if self.__class__.fail_on_open:
            raise OSError("fake serial open failed")
        # 记录初始化参数，确保实现没有偷偷改 vendor 115200/端口语义。
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.frames: list[bytes] = []
        self.closed = False
        self.__class__.instances.append(self)

    def write(self, frame: bytes) -> int:
        if self.__class__.fail_on_write:
            raise OSError("fake serial write failed")
        # vendor 协议是一行一个 UTF-8 JSON，测试按 bytes 保留换行边界。
        self.frames.append(frame)
        return len(frame)

    def close(self) -> None:
        self.closed = True

    @classmethod
    def reset(cls) -> None:
        cls.instances = []
        cls.fail_on_open = False
        cls.fail_on_write = False


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


if __name__ == "__main__":
    unittest.main()
