"""LiDAR packet helpers for software mocks and WAVE ROVER/STC LiDAR frames."""

from dataclasses import dataclass
from math import fmod, pi


YDLIDAR_PACKET_HEADER = b"\xaa\x55"
YDLIDAR_MIN_PACKET_SIZE = 8
STC_PACKET_HEADER = b"\x54"
STC_VER_LEN = 0x2C
STC_PACKET_SIZE = 47
STC_SAMPLES_PER_PACKET = 12
STC_SAMPLE_ANGLE_STEP_DEG = 0.83333

# 兼容旧测试和外部引用；真实 WAVE ROVER/STC 雷达走 0x54 单字节帧头。
PACKET_HEADER = YDLIDAR_PACKET_HEADER
MIN_PACKET_SIZE = YDLIDAR_MIN_PACKET_SIZE


@dataclass(frozen=True)
class LidarPoint:
    """单个 LaserScan 采样点，角度使用弧度，距离使用米。"""

    angle_rad: float
    distance_m: float
    intensity: int


def _u16_le(data: bytes, offset: int) -> int:
    # vendor packet 低字节在前；集中处理可避免公式里散落位运算。
    return data[offset] | (data[offset + 1] << 8)


def expected_packet_size(lsn: int) -> int:
    # README 定义包长为 PH/CT/LSN/FSA/LSA 加 LSN 组三字节采样。
    return YDLIDAR_MIN_PACKET_SIZE + int(lsn) * 3


def _ydlidar_packet_size_at(buffer: bytes, start: int) -> int | None:
    # 旧 0xAA55 mock/回放需要继续支持，避免软件验证链路被真实雷达适配打断。
    if len(buffer) - start < YDLIDAR_MIN_PACKET_SIZE:
        return None
    return expected_packet_size(buffer[start + 3])


def _partial_header_tail(buffer: bytes) -> bytes:
    # read() 可能把帧头切在两次调用之间；保留最短尾巴用于下一轮重同步。
    if buffer.endswith(YDLIDAR_PACKET_HEADER[:1]):
        return buffer[-1:]
    if buffer.endswith(STC_PACKET_HEADER):
        return buffer[-1:]
    return b""


def _is_stc_header_at(buffer: bytes, start: int) -> bool | None:
    # STC 帧头只有 1 字节，必须同时校验第二字节 0x2C，避免把噪声误判为整帧。
    if len(buffer) - start < 2:
        return None
    return buffer[start] == STC_PACKET_HEADER[0] and buffer[start + 1] == STC_VER_LEN


def find_packets(buffer: bytes) -> tuple[list[bytes], bytes]:
    """Return complete packets and the remaining partial buffer."""

    packets: list[bytes] = []
    cursor = 0
    while cursor < len(buffer):
        ydlidar_start = buffer.find(YDLIDAR_PACKET_HEADER, cursor)
        stc_start = buffer.find(STC_PACKET_HEADER, cursor)
        starts = [index for index in (ydlidar_start, stc_start) if index >= 0]
        if not starts:
            return packets, _partial_header_tail(buffer[cursor:])

        start = min(starts)
        if buffer.startswith(YDLIDAR_PACKET_HEADER, start):
            packet_size = _ydlidar_packet_size_at(buffer, start)
            if packet_size is None or len(buffer) - start < packet_size:
                return packets, buffer[start:]
            packets.append(buffer[start:start + packet_size])
            cursor = start + packet_size
            continue

        if buffer.startswith(STC_PACKET_HEADER, start):
            # WAVE ROVER vendor base_ctrl.py 使用 0x54 固定 47 字节帧，每帧 12 个采样点。
            is_stc_header = _is_stc_header_at(buffer, start)
            if is_stc_header is None:
                return packets, buffer[start:]
            if not is_stc_header:
                cursor = start + 1
                continue
            if len(buffer) - start < STC_PACKET_SIZE:
                return packets, buffer[start:]
            packets.append(buffer[start:start + STC_PACKET_SIZE])
            cursor = start + STC_PACKET_SIZE
            continue

        cursor = start + 1
    return packets, b""


def _parse_ydlidar_packet(packet: bytes) -> list[LidarPoint]:
    if len(packet) < YDLIDAR_MIN_PACKET_SIZE:
        raise ValueError("LiDAR packet too short")
    if not packet.startswith(YDLIDAR_PACKET_HEADER):
        raise ValueError("LiDAR packet header must be 0xAA55")
    lsn = packet[3]
    if len(packet) != expected_packet_size(lsn):
        raise ValueError(f"LiDAR packet size {len(packet)} does not match LSN {lsn}")

    start_angle_deg = float(_u16_le(packet, 4) >> 1) / 64.0
    end_angle_deg = float(_u16_le(packet, 6) >> 1) / 64.0
    diff_angle_deg = end_angle_deg - start_angle_deg
    if lsn > 1 and diff_angle_deg < 0:
        # 角度跨 360 度时按 vendor C++ 参考补一圈。
        diff_angle_deg += 360.0

    points: list[LidarPoint] = []
    for index in range(lsn):
        sample_offset = YDLIDAR_MIN_PACKET_SIZE + index * 3
        distance_m = float(_u16_le(packet, sample_offset)) / 4.0 / 1000.0
        if distance_m <= 0.01:
            # 极小值对导航无意义，保留和参考 parser 相同的过滤边界。
            continue
        angle_deg = start_angle_deg
        if lsn > 1:
            angle_deg = start_angle_deg + diff_angle_deg * index / (lsn - 1)
        angle_deg = fmod(angle_deg, 360.0)
        if angle_deg < 0:
            angle_deg += 360.0
        points.append(LidarPoint(angle_deg * pi / 180.0, distance_m, packet[sample_offset + 2]))
    return points


def _parse_stc_packet(packet: bytes) -> list[LidarPoint]:
    if len(packet) != STC_PACKET_SIZE:
        raise ValueError(f"STC LiDAR packet size must be {STC_PACKET_SIZE} bytes")
    if not packet.startswith(STC_PACKET_HEADER):
        raise ValueError("STC LiDAR packet header must be 0x54")
    if packet[1] != STC_VER_LEN:
        raise ValueError("STC LiDAR ver_len byte must be 0x2C")

    # 资料来源：docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py。
    # vendor 代码按 start_angle + i*0.83333 + 180 计算角度，距离单位为毫米。
    start_angle_deg = float(_u16_le(packet, 4)) * 0.01
    points: list[LidarPoint] = []
    for index in range(STC_SAMPLES_PER_PACKET):
        sample_offset = 6 + index * 3
        distance_m = float(_u16_le(packet, sample_offset)) / 1000.0
        if distance_m <= 0.01:
            # 真实 STC 帧可能含 0 距离占位，过滤后避免污染 LaserScan。
            continue
        angle_deg = fmod(start_angle_deg + index * STC_SAMPLE_ANGLE_STEP_DEG + 180.0, 360.0)
        if angle_deg < 0:
            angle_deg += 360.0
        points.append(LidarPoint(angle_deg * pi / 180.0, distance_m, packet[sample_offset + 2]))
    return points


def parse_packet(packet: bytes) -> list[LidarPoint]:
    """Parse one complete vendor packet into ordered scan points."""

    if packet.startswith(YDLIDAR_PACKET_HEADER):
        return _parse_ydlidar_packet(packet)
    if packet.startswith(STC_PACKET_HEADER):
        return _parse_stc_packet(packet)
    raise ValueError("LiDAR packet header must be 0xAA55 or STC 0x54")


def make_mock_packet(
    start_angle_deg: float = 0.0,
    end_angle_deg: float = 30.0,
    samples: list[tuple[int, int]] | None = None,
) -> bytes:
    """构造确定性的纯软件 packet，用于 launch/mock 和聚合回归验证。"""

    # 参数化 mock packet 让聚合单测能构造角度回绕，不需要依赖真实串口数据。
    fsa = int(float(start_angle_deg) * 64.0) << 1
    lsa = int(float(end_angle_deg) * 64.0) << 1
    samples = samples or [(4000, 12), (5000, 13), (6000, 14)]
    packet = bytearray(YDLIDAR_PACKET_HEADER)
    packet.extend((0x00, len(samples)))
    packet.extend((fsa & 0xFF, (fsa >> 8) & 0xFF, lsa & 0xFF, (lsa >> 8) & 0xFF))
    for distance_raw, intensity in samples:
        packet.extend((distance_raw & 0xFF, (distance_raw >> 8) & 0xFF, intensity))
    return bytes(packet)


def make_stc_mock_packet(
    start_angle_deg: float = 0.0,
    samples: list[tuple[int, int]] | None = None,
) -> bytes:
    """构造 WAVE ROVER/STC 0x54 固定长度 packet，用于真机协议回归。"""

    samples = samples or [(1000 + index * 100, 20 + index) for index in range(STC_SAMPLES_PER_PACKET)]
    if len(samples) != STC_SAMPLES_PER_PACKET:
        raise ValueError(f"STC mock packet requires {STC_SAMPLES_PER_PACKET} samples")
    packet = bytearray(STC_PACKET_SIZE)
    packet[0] = STC_PACKET_HEADER[0]
    packet[1] = STC_VER_LEN
    raw_start_angle = int(float(start_angle_deg) / 0.01)
    packet[4] = raw_start_angle & 0xFF
    packet[5] = (raw_start_angle >> 8) & 0xFF
    for index, (distance_mm, intensity) in enumerate(samples):
        sample_offset = 6 + index * 3
        packet[sample_offset] = distance_mm & 0xFF
        packet[sample_offset + 1] = (distance_mm >> 8) & 0xFF
        packet[sample_offset + 2] = intensity & 0xFF
    return bytes(packet)


def packet_from_hex(hex_text: str) -> bytes:
    """Parse a human supplied hex packet from launch parameters or tests."""

    normalized = hex_text.replace("0x", "").replace(",", " ").replace("|", " ")
    return bytes.fromhex(normalized)
