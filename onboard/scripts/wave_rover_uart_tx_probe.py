#!/usr/bin/env python3
"""WAVE ROVER UART TX 接收 smoke。

默认只发送非运动查询命令，用于验证上位机 TX 是否真的被 ESP32 解析。
需要真实短脉冲时必须显式传 `--motion-test`，脚本会在 finally 里连续 stop。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


def run_command(argv: list[str], timeout_s: float = 4.0) -> dict[str, Any]:
    """探测端口占用时只读系统状态，不修改 ROS graph。"""
    try:
        completed = subprocess.run(argv, check=False, capture_output=True, text=True, timeout=timeout_s)
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "timed_out": True,
        }


def parse_json_lines(lines: list[str]) -> list[dict[str, Any]]:
    """串口里可能夹杂启动日志；只把 JSON 行纳入证据。"""
    parsed: list[dict[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            parsed.append(value)
    return parsed


def read_for(ser: serial.Serial, seconds: float, max_preview: int = 12) -> dict[str, Any]:
    """收集一个时间窗口的反馈，并计算 T1001 / echo / 查询响应证据。"""
    deadline = time.time() + seconds
    lines: list[str] = []
    while time.time() < deadline:
        raw = ser.readline()
        if not raw:
            continue
        lines.append(raw.decode("utf-8", "replace").strip())
    parsed = parse_json_lines(lines)
    t1001 = [item for item in parsed if item.get("T") == 1001]
    nonzero = [
        item
        for item in t1001
        if item.get("L") not in (0, 0.0, None) or item.get("R") not in (0, 0.0, None)
    ]
    speed_rate = [item for item in parsed if item.get("T") == 139]
    return {
        "line_count": len(lines),
        "json_count": len(parsed),
        "preview": lines[:max_preview],
        "t1001_count": len(t1001),
        "t1001_nonzero_count": len(nonzero),
        "speed_rate_response_count": len(speed_rate),
        "latest_t1001": t1001[-1] if t1001 else None,
    }


def send_json(ser: serial.Serial, command: dict[str, Any], newline: str = "\n") -> dict[str, Any]:
    """按 vendor newline JSON 协议写一条命令，并记录本机 write 返回字节数。"""
    payload = json.dumps(command, separators=(",", ":")) + newline
    sent = ser.write(payload.encode("utf-8"))
    ser.flush()
    return {"command": command, "payload": payload, "bytes_written": sent}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe whether WAVE ROVER ESP32 receives UART TX commands.")
    parser.add_argument("--port", default="/dev/ttyS5", help="WAVE ROVER UART device.")
    parser.add_argument("--baudrate", type=int, default=115200, help="UART baudrate.")
    parser.add_argument("--allow-held-port", action="store_true", help="Open the port even if lsof reports an owner.")
    parser.add_argument("--motion-test", action="store_true", help="Send a short T=11 PWM pulse and auto-stop.")
    parser.add_argument("--pwm", type=int, default=180, help="PWM used only with --motion-test.")
    parser.add_argument("--window-s", type=float, default=0.45, help="Read window after each command.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary: dict[str, Any] = {
        "schema": "trashbot.wave_rover_uart_tx_probe.v1",
        "port": args.port,
        "baudrate": args.baudrate,
        "motion_test_requested": args.motion_test,
        "vendor_sources": [
            "docs/vendor/VENDOR_INDEX.md",
            "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
            "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
            "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h",
        ],
    }

    owner = run_command(["lsof", args.port])
    summary["port_owner"] = owner
    if owner.get("stdout") and not args.allow_held_port:
        summary.update(
            {
                "status": "port_held",
                "esp32_receive_confirmed": False,
                "next_action": "stop_esp32_bridge_before_direct_probe_or_use_ros_cmd_vel_path",
            }
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 3

    if not Path(args.port).exists():
        summary.update({"status": "port_missing", "esp32_receive_confirmed": False})
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 4

    try:
        import serial
    except ModuleNotFoundError as exc:
        summary.update(
            {
                "status": "pyserial_missing",
                "esp32_receive_confirmed": False,
                "error": str(exc),
                "next_action": "install_python3_serial_on_upper_computer",
            }
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 5

    ser = serial.Serial(
        args.port,
        args.baudrate,
        timeout=0.05,
        write_timeout=0.5,
        rtscts=False,
        dsrdtr=False,
        xonxoff=False,
    )
    writes: list[dict[str, Any]] = []
    windows: list[dict[str, Any]] = []
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        windows.append({"label": "initial", **read_for(ser, 0.8)})
        for command, newline in [
            ({"T": 143, "cmd": 1}, "\n"),
            ({"T": 139}, "\n"),
            ({"T": 900, "main": 2, "module": 0}, "\r\n"),
            ({"T": 131, "cmd": 1}, "\n"),
        ]:
            writes.append(send_json(ser, command, newline))
            windows.append({"label": f"after_T_{command['T']}", **read_for(ser, args.window_s)})
        if args.motion_test:
            # 运动测试只在现场安全时显式开启；finally 里仍会连续发三类 stop。
            writes.append(send_json(ser, {"T": 11, "L": args.pwm, "R": args.pwm}, "\n"))
            windows.append({"label": "after_motion_pwm", **read_for(ser, 1.2)})
    finally:
        for stop in ({"T": 11, "L": 0, "R": 0}, {"T": 1, "L": 0, "R": 0}, {"T": 13, "X": 0, "Z": 0}):
            try:
                writes.append(send_json(ser, stop, "\n"))
            except Exception as exc:  # pragma: no cover - 现场串口断开时保留错误证据
                writes.append({"command": stop, "error": str(exc)})
        ser.close()

    receive_confirmed = any(window["speed_rate_response_count"] > 0 for window in windows)
    motion_nonzero = any(window["t1001_nonzero_count"] > 0 for window in windows)
    summary.update(
        {
            "writes": writes,
            "windows": windows,
            "esp32_receive_confirmed": receive_confirmed,
            "wheel_lr_nonzero_observed": motion_nonzero,
            "status": "receive_confirmed" if receive_confirmed else "no_command_response",
            "next_action": (
                "use_uart_for_wasd"
                if receive_confirmed
                else "check_upper_tx_to_esp32_rx_wiring_pinmux_or_firmware_uart_receive"
            ),
            "robot_control_executed": bool(args.motion_test),
        }
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receive_confirmed else 2


if __name__ == "__main__":
    raise SystemExit(main())
