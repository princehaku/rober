"""LiDAR packet helpers ported from the local ROS1 reference."""

from dataclasses import dataclass
from math import fmod, pi


PACKET_HEADER = b"\xaa\x55"
MIN_PACKET_SIZE = 8


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
    return MIN_PACKET_SIZE + int(lsn) * 3


def find_packets(buffer: bytes) -> tuple[list[bytes], bytes]:
    """Return complete packets and the remaining partial buffer."""

    packets: list[bytes] = []
    cursor = 0
    while True:
        start = buffer.find(PACKET_HEADER, cursor)
        if start < 0:
            # 保留最后 1 字节，避免下一次 read 拼出跨边界帧头。
            return packets, buffer[-1:] if buffer.endswith(b"\xaa") else b""
        if len(buffer) - start < MIN_PACKET_SIZE:
            return packets, buffer[start:]
        packet_size = expected_packet_size(buffer[start + 3])
        if len(buffer) - start < packet_size:
            return packets, buffer[start:]
        packets.append(buffer[start:start + packet_size])
        cursor = start + packet_size


def parse_packet(packet: bytes) -> list[LidarPoint]:
    """Parse one complete vendor packet into ordered scan points."""

    if len(packet) < MIN_PACKET_SIZE:
        raise ValueError("LiDAR packet too short")
    if not packet.startswith(PACKET_HEADER):
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
        sample_offset = MIN_PACKET_SIZE + index * 3
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


def make_mock_packet() -> bytes:
    """Build a deterministic software-only packet for launch/mock validation."""

    fsa = int(0.0 * 64.0) << 1
    lsa = int(30.0 * 64.0) << 1
    samples = [(4000, 12), (5000, 13), (6000, 14)]
    packet = bytearray(PACKET_HEADER)
    packet.extend((0x00, len(samples)))
    packet.extend((fsa & 0xFF, (fsa >> 8) & 0xFF, lsa & 0xFF, (lsa >> 8) & 0xFF))
    for distance_raw, intensity in samples:
        packet.extend((distance_raw & 0xFF, (distance_raw >> 8) & 0xFF, intensity))
    return bytes(packet)


def packet_from_hex(hex_text: str) -> bytes:
    """Parse a human supplied hex packet from launch parameters or tests."""

    normalized = hex_text.replace("0x", "").replace(",", " ").replace("|", " ")
    return bytes.fromhex(normalized)
