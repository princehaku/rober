#!/usr/bin/env python3
"""O1 LiDAR raw packet proof collector 的边界单元测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR.parent / "src" / "ros2_trashbot_hardware"
for candidate in (SCRIPT_DIR, PACKAGE_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import o1_lidar_raw_packet_proof_collector as collector  # noqa: E402
from ros2_trashbot_hardware.lidar_packets import make_mock_packet  # noqa: E402


class FakeSerial:
    """模拟 LiDAR 串口：记录写入 bytes，并按 chunk 返回 raw packet。"""

    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = list(chunks)
        self.writes: list[bytes] = []
        self.closed = False

    def write(self, data: bytes) -> int:
        """只记录 collector 写入的 start/stop bytes。"""
        self.writes.append(bytes(data))
        return len(data)

    def read(self, _: int) -> bytes:
        """读完后返回空 bytes，让采集循环按 timeout 退出。"""
        if self.chunks:
            return self.chunks.pop(0)
        return b""

    def close(self) -> None:
        """测试 close 是否被调用，避免真实脚本遗留串口句柄。"""
        self.closed = True


class FakeSerialFactory:
    """让测试可以检查 collector 的 port/baudrate 与写入序列。"""

    def __init__(self, chunks: list[bytes]) -> None:
        self.serial = FakeSerial(chunks)
        self.calls: list[tuple[str, int]] = []

    def __call__(self, port: str, baudrate: int) -> FakeSerial:
        self.calls.append((port, baudrate))
        return self.serial


class BrokenSerialFactory:
    """模拟串口打不开，collector 仍应输出 fail-closed artifact。"""

    def __call__(self, _: str, __: int) -> FakeSerial:
        raise OSError("port missing")


class MustNotOpenSerialFactory:
    """安全拒绝测试中若触发 open，说明 base UART 防线失效。"""

    def __call__(self, _: str, __: int) -> FakeSerial:
        raise AssertionError("serial_factory_should_not_be_called_for_forbidden_base_uart")


class LidarRawPacketProofCollectorTest(unittest.TestCase):
    def test_default_port_prefers_vendor_udev_symlink(self) -> None:
        self.assertEqual(collector.DEFAULT_PORT, "/dev/lidar")

    def test_summarize_packets_parses_project_mock_packet(self) -> None:
        packet = make_mock_packet()

        stats = collector.summarize_packets(packet, collector.fallback_find_packets, collector.fallback_parse_packet)

        self.assertEqual(stats["bytes_read"], len(packet))
        self.assertEqual(stats["sync_header_count"], 1)
        self.assertEqual(stats["packets_found"], 1)
        self.assertEqual(stats["packets_parse_ok"], 1)
        self.assertEqual(stats["points_total"], 3)
        self.assertEqual(stats["lsn_min"], 3)
        self.assertEqual(stats["lsn_max"], 3)
        self.assertGreater(stats["distance_m_max"], stats["distance_m_min"])

    def test_collect_sends_only_lidar_start_stop_and_records_raw_stats(self) -> None:
        packet = make_mock_packet()
        factory = FakeSerialFactory([b"\x00noise", packet[:6], packet[6:]])

        payload = collector.collect_raw_packet_proof(
            port="/dev/ttyACM0",
            baudrate=150000,
            timeout_s=0.2,
            serial_factory=factory,
        )

        self.assertEqual(factory.calls, [("/dev/ttyACM0", 150000)])
        self.assertTrue(factory.serial.closed)
        self.assertEqual(factory.serial.writes, [collector.LIDAR_START_COMMAND, collector.LIDAR_STOP_COMMAND])
        self.assertEqual(payload["base_commands_sent"], [])
        self.assertEqual(payload["proof"]["status"], "raw_packets_parsed")
        self.assertTrue(payload["proof"]["lidar_start_command_sent_by_collector"])
        self.assertTrue(payload["proof"]["lidar_stop_command_sent_by_collector"])
        self.assertFalse(payload["proof"]["ros2_driver_started_by_collector"])
        self.assertFalse(payload["target_port_safety"]["target_port_refused"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["ros2_scan_proven"])
        self.assertFalse(payload["hil_pass"])
        self.assertEqual(payload["packet_stats"]["packets_parse_ok"], 1)
        self.assertEqual(payload["packet_stats"]["points_total"], 3)

    def test_collect_fail_closed_when_serial_open_fails(self) -> None:
        payload = collector.collect_raw_packet_proof(
            port="/dev/missing",
            baudrate=150000,
            timeout_s=0.2,
            serial_factory=BrokenSerialFactory(),
        )

        self.assertFalse(payload["serial_open"]["ok"])
        self.assertEqual(payload["proof"]["status"], "blocked_or_not_observed")
        self.assertFalse(payload["proof"]["raw_bytes_observed"])
        self.assertFalse(payload["safe_to_control"])
        self.assertFalse(payload["robot_control_executed"])
        self.assertFalse(payload["delivery_success"])
        self.assertIsNotNone(payload["collector_error"])

    def test_collect_refuses_base_uart_before_opening_serial(self) -> None:
        payload = collector.collect_raw_packet_proof(
            port="/dev/ttyS5",
            baudrate=150000,
            timeout_s=0.2,
            serial_factory=MustNotOpenSerialFactory(),
        )

        self.assertFalse(payload["serial_open"]["ok"])
        self.assertTrue(payload["target_port_safety"]["refuses_base_uart"])
        self.assertTrue(payload["target_port_safety"]["target_port_refused"])
        self.assertEqual(payload["collector_error"]["type"], "forbidden_lidar_port")
        self.assertEqual(payload["lidar_commands_sent"], [])
        self.assertEqual(payload["base_commands_sent"], [])
        self.assertFalse(payload["proof"]["lidar_start_command_sent_by_collector"])
        self.assertFalse(payload["safe_to_control"])

    def test_atomic_write_json_creates_readable_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "proof" / "latest.json"
            payload = {"schema": collector.SCHEMA, "proof": {"status": "raw_packets_parsed"}}

            write_result = collector.atomic_write_json(str(output), payload)

            self.assertTrue(write_result["ok"])
            saved = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(saved["schema"], collector.SCHEMA)
            self.assertEqual(saved["proof"]["status"], "raw_packets_parsed")


if __name__ == "__main__":
    unittest.main()
