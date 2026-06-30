import math
import sys
from pathlib import Path
import unittest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from ros2_trashbot_hardware.lidar_driver import (
    LIDAR_START_COMMAND,
    LIDAR_STOP_COMMAND,
    LidarRuntimeConfig,
    LidarScanAggregator,
    LidarSerialSession,
    packets_from_mock_config,
    parse_bool,
    scan_dict_from_packet,
    uses_real_serial,
)
from ros2_trashbot_hardware.lidar_packets import find_packets, make_mock_packet, make_stc_mock_packet


class FakeSerial:
    instances = []

    def __init__(self, *, port, baudrate, timeout):
        # fake serial 记录参数，证明 runtime 采用 launch 下发的串口配置。
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.writes = []
        self.read_chunks = [b"noise" + make_mock_packet()]
        self.closed = False
        FakeSerial.instances.append(self)

    def write(self, data):
        # 记录原始 bytes，避免把 hex 字符串误当成真正串口命令。
        self.writes.append(bytes(data))
        return len(data)

    def read(self, size):
        # 按真实串口 read 语义返回 bytes；size 只由 driver 控制。
        self.last_read_size = size
        if self.read_chunks:
            return self.read_chunks.pop(0)
        return b""

    def close(self):
        self.closed = True


class FakeStartWriteFailure(FakeSerial):
    def write(self, data):
        # 启动命令失败必须释放串口，避免下一轮 HIL 被半开句柄挡住。
        self.writes.append(bytes(data))
        raise OSError("start write failed")


class FakeStopWriteFailure(FakeSerial):
    def write(self, data):
        # 停止命令失败时仍应 close；物理停转由后续 HIL 观察补证。
        self.writes.append(bytes(data))
        if bytes(data) == LIDAR_STOP_COMMAND:
            raise OSError("stop write failed")
        return len(data)


class FakeSplitSerial(FakeSerial):
    def __init__(self, *, port, baudrate, timeout):
        super().__init__(port=port, baudrate=baudrate, timeout=timeout)
        packet = make_mock_packet()
        # 模拟真实 USB 串口把帧头和 payload 拆到多次 read 的情况。
        self.read_chunks = [b"noise" + packet[:1], packet[1:5], packet[5:]]


class FakeStcSerial(FakeSerial):
    def __init__(self, *, port, baudrate, timeout):
        super().__init__(port=port, baudrate=baudrate, timeout=timeout)
        packet = make_stc_mock_packet()
        # 真实 STC 帧头只有 0x54，单测覆盖噪声后按固定 47 字节重同步。
        self.read_chunks = [b"noise" + packet]


class FakeEmptySerial(FakeSerial):
    def __init__(self, *, port, baudrate, timeout):
        super().__init__(port=port, baudrate=baudrate, timeout=timeout)
        # live 故障排查最需要区分：串口已打开但 read 长期没有任何字节。
        self.read_chunks = []


class LidarDriverStubsTest(unittest.TestCase):
    def setUp(self):
        FakeSerial.instances = []

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

    def test_stc_vendor_packet_parses_wave_rover_frame(self):
        scan = scan_dict_from_packet(make_stc_mock_packet(start_angle_deg=0.0), frame_id="laser_frame")

        self.assertEqual(scan["frame_id"], "laser_frame")
        self.assertEqual(len(scan["ranges"]), 12)
        self.assertAlmostEqual(scan["ranges"][0], 1.0)
        self.assertAlmostEqual(scan["angle_min"], math.radians(180.0))

    def test_find_packets_ignores_invalid_stc_header_before_ydlidar_packet(self):
        packet = make_mock_packet()

        packets, remainder = find_packets(b"noise\x54\x00payload" + packet)

        self.assertEqual(packets, [packet])
        self.assertEqual(remainder, b"")

    def test_scan_aggregator_waits_for_more_than_one_narrow_packet(self):
        aggregator = LidarScanAggregator(max_packets=4, min_points=9)

        # 单个窄角 packet 不能再直接发布，否则 motion-delta 仍会只配到极少 bin。
        scan = aggregator.add_packet(make_mock_packet(0.0, 20.0))

        self.assertIsNone(scan)

    def test_scan_aggregator_publishes_sorted_frame_on_angle_wrap(self):
        aggregator = LidarScanAggregator(max_packets=8, min_points=99)

        # 回绕 packet 纳入同一帧后再排序，能覆盖 0 度附近和高角度区间。
        self.assertIsNone(aggregator.add_packet(make_mock_packet(300.0, 330.0)))
        scan = aggregator.add_packet(make_mock_packet(5.0, 35.0))

        self.assertIsNotNone(scan)
        assert scan is not None
        self.assertEqual(len(scan["ranges"]), 6)
        self.assertAlmostEqual(scan["angle_min"], math.radians(5.0))
        self.assertAlmostEqual(scan["angle_max"], math.radians(330.0))
        self.assertGreater(math.degrees(scan["angle_max"] - scan["angle_min"]), 300.0)

    def test_scan_aggregator_fallback_uses_packet_and_point_thresholds(self):
        aggregator = LidarScanAggregator(max_packets=2, min_points=6)

        # 兜底必须同时有足够 packet 和点数，避免异常现场长时间没有 /scan。
        self.assertIsNone(aggregator.add_packet(make_mock_packet(0.0, 10.0)))
        scan = aggregator.add_packet(make_mock_packet(15.0, 25.0))

        self.assertIsNotNone(scan)
        assert scan is not None
        self.assertEqual(len(scan["ranges"]), 6)

    def test_real_serial_session_sends_start_and_stop_commands(self):
        config = LidarRuntimeConfig(serial_port="/dev/ttyACM0", serial_baudrate=230400)
        session = LidarSerialSession(config, serial_factory=FakeSerial)

        session.open()
        packets = session.read_packets()
        session.close()

        fake = FakeSerial.instances[0]
        self.assertEqual(fake.port, "/dev/ttyACM0")
        self.assertEqual(fake.baudrate, 230400)
        self.assertEqual(fake.writes[0], LIDAR_START_COMMAND)
        self.assertEqual(fake.writes[-1], LIDAR_STOP_COMMAND)
        self.assertEqual(len(packets), 1)
        self.assertTrue(fake.closed)
        diagnostics = session.diagnostics()
        self.assertTrue(diagnostics["start_command_written"])
        self.assertGreater(diagnostics["bytes_read_total"], 0)
        self.assertEqual(diagnostics["packet_count_total"], 1)
        self.assertIn("aa 55", diagnostics["last_packet_preview_hex"])

    def test_real_serial_session_diagnostics_reports_empty_reads(self):
        config = LidarRuntimeConfig(serial_port="/dev/ttyACM0", serial_baudrate=230400)
        session = LidarSerialSession(config, serial_factory=FakeEmptySerial)

        session.open()
        self.assertEqual(session.read_packets(), [])
        self.assertEqual(session.read_packets(), [])
        diagnostics = session.diagnostics()
        session.close()

        self.assertTrue(diagnostics["start_command_written"])
        self.assertEqual(diagnostics["read_call_count"], 2)
        self.assertEqual(diagnostics["empty_read_count"], 2)
        self.assertEqual(diagnostics["bytes_read_total"], 0)
        self.assertEqual(diagnostics["packet_count_total"], 0)

    def test_start_write_failure_closes_serial_handle(self):
        config = LidarRuntimeConfig(serial_port="/dev/ttyACM0", serial_baudrate=230400)
        session = LidarSerialSession(config, serial_factory=FakeStartWriteFailure)

        with self.assertRaises(OSError):
            session.open()

        fake = FakeSerial.instances[0]
        self.assertEqual(fake.writes, [LIDAR_START_COMMAND])
        self.assertTrue(fake.closed)
        self.assertEqual(session.read_packets(), [])

    def test_stop_write_failure_still_closes_serial_handle(self):
        config = LidarRuntimeConfig(serial_port="/dev/ttyACM0", serial_baudrate=230400)
        session = LidarSerialSession(config, serial_factory=FakeStopWriteFailure)

        session.open()
        session.close()

        fake = FakeSerial.instances[0]
        self.assertEqual(fake.writes, [LIDAR_START_COMMAND, LIDAR_STOP_COMMAND])
        self.assertTrue(fake.closed)
        self.assertEqual(session.read_packets(), [])

    def test_serial_session_resyncs_split_packet_reads(self):
        config = LidarRuntimeConfig(serial_port="/dev/ttyACM0", serial_baudrate=230400)
        session = LidarSerialSession(config, serial_factory=FakeSplitSerial)

        session.open()
        self.assertEqual(session.read_packets(), [])
        self.assertEqual(session.read_packets(), [])
        packets = session.read_packets()
        session.close()

        self.assertEqual(packets, [make_mock_packet()])

    def test_serial_session_reads_stc_vendor_packet(self):
        config = LidarRuntimeConfig(serial_port="/dev/ttyACM0", serial_baudrate=230400)
        session = LidarSerialSession(config, serial_factory=FakeStcSerial)

        session.open()
        packets = session.read_packets()
        session.close()

        self.assertEqual(packets, [make_stc_mock_packet()])

    def test_mock_scan_does_not_open_serial(self):
        config = LidarRuntimeConfig(mock_scan=True)

        self.assertFalse(uses_real_serial(config))
        self.assertEqual(len(packets_from_mock_config(config.mock_scan, config.mock_packets)), 1)
        self.assertEqual(FakeSerial.instances, [])

    def test_mock_packets_do_not_open_serial(self):
        packet_hex = make_mock_packet().hex(" ")
        config = LidarRuntimeConfig(mock_scan=False, mock_packets=packet_hex)

        self.assertFalse(uses_real_serial(config))
        self.assertEqual(len(packets_from_mock_config(config.mock_scan, config.mock_packets)), 1)
        self.assertEqual(FakeSerial.instances, [])

    def test_lidar_lifecycle_passes_driver_diagnostics_path(self):
        script_path = PACKAGE_ROOT.parents[1] / "scripts" / "o1_lidar_lifecycle.sh"

        script = script_path.read_text(encoding="utf-8")

        self.assertIn('DIAGNOSTICS_FILE="$RUNTIME_DIR/lidar_driver_diagnostics.json"', script)
        self.assertIn('"driver_diagnostics_path": f"{runtime_dir}/lidar_driver_diagnostics.json"', script)
        self.assertIn('-p diagnostics_path:="$DIAGNOSTICS_FILE"', script)
