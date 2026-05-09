#!/usr/bin/env python3
"""WAVE ROVER UART JSON hardware smoke test.

Vendor sources:
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h

The ESP32 firmware uses one UTF-8 JSON object per UART line, terminated by \n.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

import serial


def encode(command: dict[str, Any]) -> bytes:
    return (json.dumps(command, separators=(",", ":")) + "\n").encode("utf-8")


def send(ser: serial.Serial, command: dict[str, Any]) -> None:
    frame = encode(command)
    ser.write(frame)
    ser.flush()
    print(f"> {frame.decode('utf-8').strip()}")


def stop(ser: serial.Serial) -> None:
    if ser.is_open:
        send(ser, {"T": 1, "L": 0, "R": 0})


def read_feedback(ser: serial.Serial, timeout_s: float) -> dict[str, Any] | None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        line = ser.readline()
        if not line:
            continue
        text = line.decode("utf-8", errors="replace").strip()
        print(f"< {text}")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        if data.get("T") == 1001:
            return data
    return None


def configure_feedback(ser: serial.Serial, feedback_interval_ms: int) -> None:
    send(ser, {"T": 143, "cmd": 0})
    send(ser, {"T": 142, "cmd": feedback_interval_ms})
    send(ser, {"T": 131, "cmd": 1})


def run_move_test(ser: serial.Serial, speed: float, duration_s: float) -> None:
    print(f"Running low-speed T=1 move test: L=R={speed} for {duration_s:.2f}s")
    send(ser, {"T": 1, "L": speed, "R": speed})
    time.sleep(duration_s)
    stop(ser)


def run_reverse_test(ser: serial.Serial, speed: float, duration_s: float) -> None:
    signed_speed = -abs(speed)
    print(f"Running low-speed reverse T=1 test: L=R={signed_speed} for {duration_s:.2f}s")
    send(ser, {"T": 1, "L": signed_speed, "R": signed_speed})
    time.sleep(duration_s)
    stop(ser)


def run_ros_mode_test(ser: serial.Serial, linear_x: float, angular_z: float, duration_s: float) -> None:
    print(
        "Running low-speed T=13 ROS-mode test: "
        f"X={linear_x}, Z={angular_z} for {duration_s:.2f}s"
    )
    send(ser, {"T": 13, "X": linear_x, "Z": angular_z})
    time.sleep(duration_s)
    send(ser, {"T": 13, "X": 0, "Z": 0})
    stop(ser)


def run_turn_test(ser: serial.Serial, angular_z: float, duration_s: float) -> None:
    print(f"Running in-place turn T=13 test: X=0, Z={angular_z} for {duration_s:.2f}s")
    send(ser, {"T": 13, "X": 0, "Z": angular_z})
    time.sleep(duration_s)
    send(ser, {"T": 13, "X": 0, "Z": 0})
    stop(ser)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test WAVE ROVER ESP32 UART JSON bridge.")
    parser.add_argument("--serial-port", required=True, help="Robot UART device, for example /dev/ttyS1")
    parser.add_argument("--baudrate", type=int, default=115200, help="UART baudrate; vendor default is 115200")
    parser.add_argument("--feedback-interval-ms", type=int, default=100)
    parser.add_argument("--feedback-timeout-s", type=float, default=5.0)
    parser.add_argument("--move-test", action="store_true", help="Run a short T=1 low-speed movement")
    parser.add_argument("--reverse-test", action="store_true", help="Run a short T=1 low-speed reverse movement")
    parser.add_argument("--ros-mode-test", action="store_true", help="Run a short T=13 X/Z movement")
    parser.add_argument("--turn-test", action="store_true", help="Run a short in-place T=13 angular movement")
    parser.add_argument("--test-speed", type=float, default=0.08)
    parser.add_argument("--test-duration-s", type=float, default=0.5)
    parser.add_argument("--ros-angular-z", type=float, default=0.0)
    parser.add_argument("--turn-angular-z", type=float, default=0.3)
    args = parser.parse_args()

    if args.feedback_interval_ms < 0:
        parser.error("--feedback-interval-ms must be >= 0")
    if args.test_duration_s <= 0:
        parser.error("--test-duration-s must be > 0")

    ser: serial.Serial | None = None
    try:
        ser = serial.Serial(args.serial_port, args.baudrate, timeout=0.2)
        print(f"Opened {args.serial_port} @ {args.baudrate}")
        stop(ser)
        configure_feedback(ser, args.feedback_interval_ms)

        feedback = read_feedback(ser, args.feedback_timeout_s)
        if feedback is None:
            print("ERROR: no T=1001 feedback received before timeout", file=sys.stderr)
            return 2
        print(f"T=1001 feedback OK: {feedback}")

        if args.move_test:
            run_move_test(ser, args.test_speed, args.test_duration_s)
        if args.reverse_test:
            run_reverse_test(ser, args.test_speed, args.test_duration_s)
        if args.ros_mode_test:
            run_ros_mode_test(ser, args.test_speed, args.ros_angular_z, args.test_duration_s)
        if args.turn_test:
            run_turn_test(ser, args.turn_angular_z, args.test_duration_s)
        return 0
    except KeyboardInterrupt:
        print("Interrupted; sending stop before exit", file=sys.stderr)
        return 130
    except (OSError, serial.SerialException) as exc:
        print(f"ERROR: serial failure: {exc}", file=sys.stderr)
        return 1
    finally:
        if ser is not None:
            try:
                stop(ser)
            except Exception as exc:  # noqa: BLE001 - best-effort emergency stop path.
                print(f"ERROR: failed to send final stop: {exc}", file=sys.stderr)
            ser.close()


if __name__ == "__main__":
    raise SystemExit(main())
