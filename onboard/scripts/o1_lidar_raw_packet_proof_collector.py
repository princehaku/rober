#!/usr/bin/env python3
"""O1 LiDAR raw packet proof collector：采集原始 bytes 的 packet/point 统计。"""

from __future__ import annotations

import argparse
import json
import os
import select
import sys
import tempfile
import termios
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SCHEMA = "trashbot.o1.lidar_raw_packet_proof.v1"
DEFAULT_PORT = "/dev/lidar"
DEFAULT_BAUDRATE = 150000
DEFAULT_TIMEOUT_S = 3.0
DEFAULT_OUTPUT_PATH = "/tmp/o1_lidar_raw_packet_proof_latest.json"
LIDAR_START_COMMAND = b"\xA5\x60"
LIDAR_STOP_COMMAND = b"\xA5\x00\xA5\x65\xA5\x65"
PACKET_HEADER = b"\xAA\x55"
MIN_PACKET_SIZE = 8
FORBIDDEN_LIDAR_PORTS = frozenset({"/dev/ttyS5", "/dev/ttyAMA0", "/dev/serial0"})

# 本脚本允许启动/停止 LiDAR 串口，这是本轮 raw packet proof 的目标行为。
# 串口事实来自 docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp 和 VENDOR_INDEX。
# 本脚本不启动 ROS2 driver，不读取 /scan，不发布 /cmd_vel，不触碰底盘控制口。
# Artifact 只能证明 raw bytes 可读取、packet 可解析、points 可统计。
# 真实 /scan、TF、SLAM/Nav2、HIL 和 safe_to_control 必须由后续独立材料证明。
# 如果调用方误传底盘 UART，本脚本必须在 open 前拒绝，不能把 A5 bytes 写入 WAVE ROVER。
VENDOR_SOURCES = (
    "AGENTS.md",
    "OKR.md",
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/lidar_pkg_ros2-main/README.md",
    "docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp",
    "docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml",
    "docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules",
    "docs/vendor/lidar_ros/README.md",
    "onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py",
)

# 禁止项写入 artifact，避免后续把 LiDAR 材料误读成底盘/HIL 准入。
FORBIDDEN_BASE_ACTIONS_NOT_SENT = (
    {"command": {"T": 1}, "reason": "LiDAR raw proof must not send wheel speed commands"},
    {"command": {"T": 13}, "reason": "LiDAR raw proof must not send ROS velocity JSON"},
    {"command": {"T": 130}, "reason": "base feedback request is outside LiDAR raw proof"},
    {"command": {"T": 131}, "reason": "base feedback flow is outside LiDAR raw proof"},
    {"command": "/cmd_vel", "reason": "collector never publishes ROS motion"},
    {"command": "/api/base/manual", "reason": "collector never calls upper base manual API"},
)


def _u16_le(data: bytes, offset: int) -> int:
    """vendor packet 低字节在前；fallback parser 只用于 stdin 无包导入场景。"""
    return data[offset] | (data[offset + 1] << 8)


def fallback_expected_packet_size(lsn: int) -> int:
    """PH/CT/LSN/FSA/LSA 加 LSN 组三字节采样，来自本地 parser。"""
    return MIN_PACKET_SIZE + int(lsn) * 3


def fallback_find_packets(buffer: bytes) -> tuple[list[bytes], bytes]:
    """在连续 bytes 中按 0xAA55 和 LSN 找完整 packet。"""
    packets: list[bytes] = []
    cursor = 0
    while True:
        start = buffer.find(PACKET_HEADER, cursor)
        if start < 0:
            return packets, buffer[-1:] if buffer.endswith(b"\xaa") else b""
        if len(buffer) - start < MIN_PACKET_SIZE:
            return packets, buffer[start:]
        packet_size = fallback_expected_packet_size(buffer[start + 3])
        if len(buffer) - start < packet_size:
            return packets, buffer[start:]
        packets.append(buffer[start : start + packet_size])
        cursor = start + packet_size


def fallback_parse_packet(packet: bytes) -> list[dict[str, float | int]]:
    """最小 parser 与 lidar_packets.py 同公式，用于远端 stdin 安全 fallback。"""
    if len(packet) < MIN_PACKET_SIZE:
        raise ValueError("LiDAR packet too short")
    if not packet.startswith(PACKET_HEADER):
        raise ValueError("LiDAR packet header must be 0xAA55")
    lsn = packet[3]
    if len(packet) != fallback_expected_packet_size(lsn):
        raise ValueError(f"LiDAR packet size {len(packet)} does not match LSN {lsn}")

    start_angle_deg = float(_u16_le(packet, 4) >> 1) / 64.0
    end_angle_deg = float(_u16_le(packet, 6) >> 1) / 64.0
    diff_angle_deg = end_angle_deg - start_angle_deg
    if lsn > 1 and diff_angle_deg < 0:
        diff_angle_deg += 360.0

    points: list[dict[str, float | int]] = []
    for index in range(lsn):
        sample_offset = MIN_PACKET_SIZE + index * 3
        distance_m = float(_u16_le(packet, sample_offset)) / 4.0 / 1000.0
        if distance_m <= 0.01:
            continue
        angle_deg = start_angle_deg if lsn <= 1 else start_angle_deg + diff_angle_deg * index / (lsn - 1)
        angle_deg %= 360.0
        points.append({"angle_rad": angle_deg * 3.141592653589793 / 180.0, "distance_m": distance_m, "intensity": packet[sample_offset + 2]})
    return points


def load_packet_parser() -> tuple[Callable[[bytes], tuple[list[bytes], bytes]], Callable[[bytes], Any], str]:
    """优先复用项目 parser；stdin 到远端无法 import 时才走内置 fallback。"""
    try:
        from ros2_trashbot_hardware.lidar_packets import find_packets, parse_packet

        return find_packets, parse_packet, "ros2_trashbot_hardware.lidar_packets"
    except Exception:
        pass

    # 本地直接运行脚本时，把 ROS2 package 源码路径加入 sys.path。
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[2] if len(script_path.parents) >= 3 else Path.cwd()
    package_path = repo_root / "onboard" / "src" / "ros2_trashbot_hardware"
    if str(package_path) not in sys.path:
        sys.path.insert(0, str(package_path))
    try:
        from ros2_trashbot_hardware.lidar_packets import find_packets, parse_packet

        return find_packets, parse_packet, "onboard/src/ros2_trashbot_hardware/.../lidar_packets.py"
    except Exception:
        return fallback_find_packets, fallback_parse_packet, "inline_fallback_ported_from_lidar_packets.py"


def utc_now() -> str:
    """UTC 时间用于跨机器 artifact 对齐。"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def compact_error(error: BaseException) -> dict[str, str]:
    """错误文本限长，避免串口异常或远端路径噪声撑爆 artifact。"""
    return {"type": type(error).__name__, "message": str(error)[:500]}


def hex_bytes(data: bytes) -> str:
    """artifact 中的命令和样例统一用小写 hex，便于 shell/readback 对照。"""
    return data.hex(" ")


def forbidden_lidar_port(port: str) -> bool:
    """LiDAR collector 只碰传感器口，禁止常见 WAVE ROVER/base UART 路径。"""
    normalized = str(port).strip()
    return normalized in FORBIDDEN_LIDAR_PORTS


class TermiosSerial:
    """pyserial 不存在时的 Linux tty fallback，支持 stdin 远端最小 smoke。"""

    def __init__(self, port: str, baudrate: int, read_timeout_s: float = 0.1) -> None:
        self.port = port
        self.baudrate = baudrate
        self.read_timeout_s = read_timeout_s
        self.fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        self._configure()

    def _configure(self) -> None:
        """配置 raw 串口；150000 必须由 Linux termios 常量支持。"""
        baud_attr = f"B{int(self.baudrate)}"
        if not hasattr(termios, baud_attr):
            raise OSError(f"termios does not expose {baud_attr}; install pyserial on target")
        attrs = termios.tcgetattr(self.fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = getattr(termios, baud_attr) | termios.CS8 | termios.CREAD | termios.CLOCAL
        attrs[3] = 0
        attrs[4] = getattr(termios, baud_attr)
        attrs[5] = getattr(termios, baud_attr)
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 1
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        termios.tcflush(self.fd, termios.TCIOFLUSH)

    def write(self, data: bytes) -> int:
        """写入 LiDAR vendor start/stop bytes，不用于底盘 JSON。"""
        return os.write(self.fd, data)

    def read(self, size: int) -> bytes:
        """短 timeout 读取，避免现场 smoke 卡住 SSH stdin。"""
        readable, _, _ = select.select([self.fd], [], [], self.read_timeout_s)
        if not readable:
            return b""
        return os.read(self.fd, size)

    def close(self) -> None:
        """关闭 tty 前 flush 一次，确保 stop bytes 已交给内核。"""
        try:
            termios.tcdrain(self.fd)
        finally:
            os.close(self.fd)


def open_serial(port: str, baudrate: int) -> Any:
    """优先 pyserial；缺依赖时使用 termios fallback 便于 `python3 -s -`。"""
    try:
        import serial  # type: ignore

        return serial.Serial(port=port, baudrate=baudrate, timeout=0.1, write_timeout=1.0)
    except ImportError:
        return TermiosSerial(port, baudrate)


def point_to_dict(point: Any) -> dict[str, float | int]:
    """兼容 dataclass parser 和 fallback dict parser。"""
    if isinstance(point, dict):
        return {"angle_rad": float(point["angle_rad"]), "distance_m": float(point["distance_m"]), "intensity": int(point["intensity"])}
    return {"angle_rad": float(point.angle_rad), "distance_m": float(point.distance_m), "intensity": int(point.intensity)}


def build_empty_stats() -> dict[str, Any]:
    """集中定义 stats 结构，测试和文档能稳定引用字段。"""
    return {
        "bytes_read": 0,
        "sync_header_count": 0,
        "packets_found": 0,
        "packets_parse_ok": 0,
        "packet_parse_errors": 0,
        "points_total": 0,
        "nonzero_point_packets": 0,
        "lsn_min": None,
        "lsn_max": None,
        "packet_size_min": None,
        "packet_size_max": None,
        "distance_m_min": None,
        "distance_m_max": None,
        "intensity_min": None,
        "intensity_max": None,
        "sample_packet_hex": [],
    }


def update_min_max(stats: dict[str, Any], key_min: str, key_max: str, value: float | int) -> None:
    """统计范围字段只在有样本时落值，不制造 0 值假象。"""
    stats[key_min] = value if stats[key_min] is None else min(stats[key_min], value)
    stats[key_max] = value if stats[key_max] is None else max(stats[key_max], value)


def summarize_packets(raw_data: bytes, find_packets: Callable[[bytes], tuple[list[bytes], bytes]], parse_packet: Callable[[bytes], Any]) -> dict[str, Any]:
    """对原始 bytes 做 packet 和 point 统计，不生成 LaserScan。"""
    stats = build_empty_stats()
    stats["bytes_read"] = len(raw_data)
    stats["sync_header_count"] = raw_data.count(PACKET_HEADER)
    packets, remainder = find_packets(raw_data)
    stats["packets_found"] = len(packets)
    stats["partial_remainder_bytes"] = len(remainder)
    errors: list[dict[str, Any]] = []

    for packet in packets:
        lsn = packet[3] if len(packet) > 3 else None
        if isinstance(lsn, int):
            update_min_max(stats, "lsn_min", "lsn_max", lsn)
        update_min_max(stats, "packet_size_min", "packet_size_max", len(packet))
        if len(stats["sample_packet_hex"]) < 3:
            stats["sample_packet_hex"].append(hex_bytes(packet[:96]))
        try:
            points = [point_to_dict(point) for point in parse_packet(packet)]
            stats["packets_parse_ok"] += 1
            stats["points_total"] += len(points)
            if points:
                stats["nonzero_point_packets"] += 1
            for point in points:
                update_min_max(stats, "distance_m_min", "distance_m_max", point["distance_m"])
                update_min_max(stats, "intensity_min", "intensity_max", point["intensity"])
        except Exception as exc:
            stats["packet_parse_errors"] += 1
            if len(errors) < 5:
                errors.append({"packet_hex": hex_bytes(packet[:32]), "error": compact_error(exc)})

    stats["parse_error_samples"] = errors
    return stats


def proof_flags() -> dict[str, bool]:
    """LiDAR raw bytes 不能升级为底盘/HIL/ROS2 scan 准入。"""
    return {
        "safe_to_control": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "ros2_scan_proven": False,
        "tf_proven": False,
        "slam_nav2_proven": False,
        "hil_pass": False,
        "delivery_success": False,
    }


def collect_raw_packet_proof(
    *,
    port: str = DEFAULT_PORT,
    baudrate: int = DEFAULT_BAUDRATE,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    serial_factory: Callable[[str, int], Any] = open_serial,
) -> dict[str, Any]:
    """打开 LiDAR 串口，发送 start，读取 raw bytes，finally 发送 stop。"""
    timeout_s = min(max(float(timeout_s), 0.2), 30.0)
    find_packets, parse_packet, parser_source = load_packet_parser()
    generated_at = utc_now()
    raw_chunks: list[bytes] = []
    serial_open: dict[str, Any] = {"ok": False, "port": port, "baudrate": baudrate}
    command_writes: list[dict[str, Any]] = []
    collector_error: dict[str, Any] | None = None
    serial_handle: Any | None = None

    if forbidden_lidar_port(port):
        collector_error = {
            "type": "forbidden_lidar_port",
            "message": f"refusing to open base UART path {port}; use /dev/lidar or a confirmed STC ttyACM/by-id path",
        }
    else:
        try:
            serial_handle = serial_factory(port, int(baudrate))
            serial_open["ok"] = True
            start_written = serial_handle.write(LIDAR_START_COMMAND)
            command_writes.append({"name": "lidar_start", "hex": hex_bytes(LIDAR_START_COMMAND), "bytes_written": start_written, "allowed_by_task": True})

            deadline = time.monotonic() + timeout_s
            while time.monotonic() < deadline:
                chunk = serial_handle.read(4096)
                if chunk:
                    raw_chunks.append(bytes(chunk))
                else:
                    time.sleep(0.01)
        except Exception as exc:
            collector_error = compact_error(exc)
        finally:
            if serial_handle is not None:
                try:
                    stop_written = serial_handle.write(LIDAR_STOP_COMMAND)
                    command_writes.append({"name": "lidar_stop", "hex": hex_bytes(LIDAR_STOP_COMMAND), "bytes_written": stop_written, "allowed_by_task": True})
                except Exception as exc:
                    command_writes.append({"name": "lidar_stop", "hex": hex_bytes(LIDAR_STOP_COMMAND), "error": compact_error(exc), "allowed_by_task": True})
                try:
                    serial_handle.close()
                except Exception as exc:
                    serial_open["close_error"] = compact_error(exc)

    raw_data = b"".join(raw_chunks)
    packet_stats = summarize_packets(raw_data, find_packets, parse_packet)
    proof_status = "raw_packets_parsed" if packet_stats["packets_parse_ok"] > 0 and packet_stats["points_total"] > 0 else "blocked_or_not_observed"
    return {
        "schema": SCHEMA,
        "generated_at": generated_at,
        "vendor_sources": list(VENDOR_SOURCES),
        "evidence_boundary": "lidar_raw_packet_parse_material_readiness_only",
        "parser_source": parser_source,
        "target": {"port": port, "baudrate": int(baudrate)},
        "target_port_safety": {
            "default_port": DEFAULT_PORT,
            "forbidden_lidar_ports": sorted(FORBIDDEN_LIDAR_PORTS),
            "refuses_base_uart": True,
            "target_port_refused": forbidden_lidar_port(port),
        },
        "serial_open": serial_open,
        "lidar_commands_sent": command_writes,
        "base_commands_sent": [],
        "forbidden_base_actions_not_sent": list(FORBIDDEN_BASE_ACTIONS_NOT_SENT),
        "packet_stats": packet_stats,
        "proof": {
            "status": proof_status,
            "raw_bytes_observed": packet_stats["bytes_read"] > 0,
            "sync_header_observed": packet_stats["sync_header_count"] > 0,
            "packet_parse_ok": packet_stats["packets_parse_ok"] > 0,
            "points_observed": packet_stats["points_total"] > 0,
            "lidar_start_command_sent_by_collector": any(item.get("name") == "lidar_start" and item.get("bytes_written", 0) > 0 for item in command_writes),
            "lidar_stop_command_sent_by_collector": any(item.get("name") == "lidar_stop" and item.get("bytes_written", 0) > 0 for item in command_writes),
            "ros2_driver_started_by_collector": False,
            "launch_started_by_collector": False,
        },
        "collector_error": collector_error,
        **proof_flags(),
    }


def atomic_write_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """artifact 原子写入，防止 readback 读到半截 JSON。"""
    destination = Path(path)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        with tempfile.NamedTemporaryFile("wb", delete=False, dir=str(destination.parent), prefix=f".{destination.name}.") as handle:
            temp_name = handle.name
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, destination)
        return {"ok": True, "path": str(destination), "bytes": len(encoded)}
    except Exception as exc:
        return {"ok": False, "path": str(destination), "error": compact_error(exc)}


def parse_args(argv: list[str]) -> argparse.Namespace:
    """CLI 兼容 `python3 -s - ... < script.py` 远端 stdin 跑法。"""
    parser = argparse.ArgumentParser(description="Collect O1 LiDAR raw packet proof artifact.")
    parser.add_argument("--once-json", action="store_true", help="print one JSON payload and exit")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH, help="optional artifact output path")
    parser.add_argument("--timeout-s", type=float, default=DEFAULT_TIMEOUT_S, help="serial read timeout in seconds")
    parser.add_argument("--port", default=DEFAULT_PORT, help="LiDAR serial port")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="LiDAR serial baudrate")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """入口只做一次采集；失败也输出 fail-closed artifact。"""
    args = parse_args(list(argv) if argv is not None else sys.argv[1:])
    payload = collect_raw_packet_proof(port=args.port, baudrate=args.baudrate, timeout_s=args.timeout_s)
    if args.output:
        payload["artifact_write"] = atomic_write_json(args.output, payload)
    if args.once_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["serial_open"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
