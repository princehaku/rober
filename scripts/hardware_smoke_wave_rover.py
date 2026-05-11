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
from datetime import datetime, timezone
from typing import Any
from shlex import quote

SCRIPT_VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
]

SOFTWARE_PROOF_SOURCE = "software_proof"
HIL_SOURCE = "hil_pass"
SERIAL_IMPORT_ERROR = (
    "ERROR: missing dependency pyserial.\n"
    "  Install once: python3 -m pip install pyserial\n"
    "  Then rerun the hardware command."
)
SERIAL_OPEN_ERROR_NOTE = (
    "BLOCKED: serial dependency or device access blocked.\n"
    "  Repro steps:\n"
    "  1) PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/hardware_smoke_wave_rover.py\n"
    "  2) python3 scripts/hardware_smoke_wave_rover.py --status\n"
    "  3) python3 scripts/hardware_smoke_wave_rover.py --move-test --serial-port <device> --baudrate <baudrate>\n"
    "  If pyserial is missing, install inside ros2-humble runtime as documented."
)


def build_run_evidence_ref(args: argparse.Namespace, source: str) -> str:
    now_utc = datetime.now(timezone.utc)
    serial_part = (args.serial_port or "noserial").replace("/", "-")
    speed_part = f"speed{abs(float(args.test_speed)):.3f}".replace(".", "p")
    duration_part = f"dur{args.test_duration_s:.2f}".replace(".", "p")
    return (
        f"run_{now_utc:%Y%m%dT%H%M%SZ}_"
        f"{serial_part}_{source}_{speed_part}_{duration_part}"
    )


def build_hil_parameter_lock(args: argparse.Namespace, evidence_ref: str) -> dict[str, Any]:
    return {
        "source": HIL_SOURCE,
        "evidence_ref": evidence_ref,
        "serial_port": args.serial_port,
        "baudrate": args.baudrate,
        "feedback_interval_ms": args.feedback_interval_ms,
        "feedback_timeout_s": args.feedback_timeout_s,
        "test_speed": args.test_speed,
        "test_duration_s": args.test_duration_s,
        "ros_angular_z": args.ros_angular_z,
        "turn_angular_z": args.turn_angular_z,
        "run_flags": sorted(
            flag
            for flag in ("move-test" if args.move_test else "",
                         "reverse-test" if args.reverse_test else "",
                         "ros-mode-test" if args.ros_mode_test else "",
                         "turn-test" if args.turn_test else "")
            if flag
        ),
    }


def print_command_template() -> str:
    return " ".join(quote(p) for p in sys.argv)

try:
    import serial
    from serial import SerialException
except ModuleNotFoundError:
    serial = None
    SerialException = OSError


def encode(command: dict[str, Any]) -> bytes:
    return (json.dumps(command, separators=(",", ":")) + "\n").encode("utf-8")


def send(ser: Any, command: dict[str, Any]) -> None:
    frame = encode(command)
    ser.write(frame)
    ser.flush()
    print(f"> {frame.decode('utf-8').strip()}")


def stop(ser: Any) -> None:
    if ser.is_open:
        send(ser, {"T": 1, "L": 0, "R": 0})


def read_feedback(
    ser: Any,
    timeout_s: float,
    min_samples: int = 2,
) -> tuple[list[dict[str, Any]], float | None]:
    """Read sampled T=1001 base feedback frames."""
    samples: list[dict[str, Any]] = []
    sample_intervals_ms: list[float] = []
    last_sample_t: float | None = None
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
            now = time.monotonic()
            if last_sample_t is not None:
                sample_intervals_ms.append((now - last_sample_t) * 1000.0)
            last_sample_t = now
            if isinstance(data, dict):
                samples.append(data)
            if len(samples) >= min_samples:
                break
    if not sample_intervals_ms:
        return samples, None
    return samples, sum(sample_intervals_ms) / len(sample_intervals_ms)


def print_status() -> None:
    """Print a software-only smoke template status."""
    template_ref = f"run_template_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
    print(json.dumps(
        {
            "status": "ready",
            "source": SOFTWARE_PROOF_SOURCE,
            "evidence_ref": template_ref,
            "script": "scripts/hardware_smoke_wave_rover.py",
            "vendor_sources": SCRIPT_VENDOR_SOURCES,
            "defaults": {
                "serial_port": "/dev/ttyUSB0",
                "baudrate": 115200,
                "feedback_interval_ms": 100,
                "feedback_timeout_s": 5.0,
                "test_speed": 0.05,
                "test_duration_s": 0.3,
            },
            "required_args_for_hil": [
                "--serial-port",
                "--baudrate",
                "--feedback-interval-ms",
                "--move-test",
            ],
            "startup_commands": [
                {"T": 143, "cmd": 0},
                {"T": 142, "cmd": 100},
                {"T": 131, "cmd": 1},
            ],
            "tests": [
                "--move-test",
                "--reverse-test",
                "--ros-mode-test",
                "--turn-test",
            ],
            "dependency_note": "pyserial required for hil commands",
            "command_template": "python3 scripts/hardware_smoke_wave_rover.py --move-test --serial-port <device> --baudrate <baud> --test-speed <speed> --test-duration-s <duration>",
        },
        indent=2,
        sort_keys=True,
    ))


def configure_feedback(ser: Any, feedback_interval_ms: int) -> None:
    send(ser, {"T": 143, "cmd": 0})
    send(ser, {"T": 142, "cmd": feedback_interval_ms})
    send(ser, {"T": 131, "cmd": 1})


def run_move_test(ser: Any, speed: float, duration_s: float) -> None:
    print(f"Running low-speed T=1 move test: L=R={speed} for {duration_s:.2f}s")
    send(ser, {"T": 1, "L": speed, "R": speed})
    time.sleep(duration_s)
    stop(ser)


def run_reverse_test(ser: Any, speed: float, duration_s: float) -> None:
    signed_speed = -abs(speed)
    print(f"Running low-speed reverse T=1 test: L=R={signed_speed} for {duration_s:.2f}s")
    send(ser, {"T": 1, "L": signed_speed, "R": signed_speed})
    time.sleep(duration_s)
    stop(ser)


def run_ros_mode_test(ser: Any, linear_x: float, angular_z: float, duration_s: float) -> None:
    print(
        "Running low-speed T=13 ROS-mode test: "
        f"X={linear_x}, Z={angular_z} for {duration_s:.2f}s"
    )
    send(ser, {"T": 13, "X": linear_x, "Z": angular_z})
    time.sleep(duration_s)
    send(ser, {"T": 13, "X": 0, "Z": 0})
    stop(ser)


def run_turn_test(ser: Any, angular_z: float, duration_s: float) -> None:
    print(f"Running in-place turn T=13 test: X=0, Z={angular_z} for {duration_s:.2f}s")
    send(ser, {"T": 13, "X": 0, "Z": angular_z})
    time.sleep(duration_s)
    send(ser, {"T": 13, "X": 0, "Z": 0})
    stop(ser)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test WAVE ROVER ESP32 UART JSON bridge.")
    parser.add_argument(
        "--serial-port",
        default="/dev/ttyUSB0",
        help="Robot UART device, for example /dev/ttyUSB0",
    )
    parser.add_argument("--baudrate", type=int, default=115200, help="UART baudrate; vendor default is 115200")
    parser.add_argument("--feedback-interval-ms", type=int, default=100)
    parser.add_argument("--feedback-timeout-s", type=float, default=5.0)
    parser.add_argument("--status", action="store_true", help="Print smoke template status only; no serial access.")
    parser.add_argument("--move-test", action="store_true", help="Run a short T=1 low-speed movement")
    parser.add_argument("--reverse-test", action="store_true", help="Run a short T=1 low-speed reverse movement")
    parser.add_argument("--ros-mode-test", action="store_true", help="Run a short T=13 X/Z movement")
    parser.add_argument("--turn-test", action="store_true", help="Run a short in-place T=13 angular movement")
    parser.add_argument("--test-speed", type=float, default=0.05)
    parser.add_argument("--test-duration-s", type=float, default=0.3)
    parser.add_argument("--ros-angular-z", type=float, default=0.0)
    parser.add_argument("--turn-angular-z", type=float, default=0.3)
    parser.add_argument("--evidence-ref", type=str, default="", help="Optional run-level evidence_ref override")
    args = parser.parse_args()

    if args.feedback_interval_ms < 0:
        parser.error("--feedback-interval-ms must be >= 0")
    if args.test_duration_s <= 0:
        parser.error("--test-duration-s must be > 0")
    if args.status:
        print_status()
        return 0
    if serial is None:
        print(SERIAL_IMPORT_ERROR, file=sys.stderr)
        return 2

    ser: Any | None = None
    try:
        evidence_ref = args.evidence_ref.strip() or build_run_evidence_ref(args, HIL_SOURCE)
        run_parameters = build_hil_parameter_lock(args, evidence_ref)
        command_signature = print_command_template()
        print(json.dumps({"source": HIL_SOURCE, "command": command_signature, "parameters": run_parameters}, indent=2, sort_keys=True))

        ser = serial.Serial(args.serial_port, args.baudrate, timeout=0.2)  # type: ignore[arg-type]
        print(f"Opened {args.serial_port} @ {args.baudrate}")
        stop(ser)
        configure_feedback(ser, args.feedback_interval_ms)

        feedback_samples, avg_feedback_interval_ms = read_feedback(
            ser,
            args.feedback_timeout_s,
            min_samples=2,
        )
        if not feedback_samples:
            print("ERROR: no T=1001 feedback received before timeout", file=sys.stderr)
            return 2
        if avg_feedback_interval_ms is None:
            print(
                f"WARN: T=1001 feedback received {len(feedback_samples)} sample only; "
                "feedback frequency cannot be inferred from single sample",
                file=sys.stderr,
            )
        else:
            print(
                f"T=1001 feedback rate: avg interval={avg_feedback_interval_ms:.2f}ms "
                f"(~{1000/avg_feedback_interval_ms:.2f}Hz)",
            )
        print(f"evidence_ref={evidence_ref}")
        print(f"source={HIL_SOURCE}")
        print(f"T=1001 feedback sample: {feedback_samples[0]}")
        print(
            "Firmware feedback fields present: "
            f"{[key for key in ['L', 'R', 'r', 'p', 'y', 'v'] if key in feedback_samples[0]]}",
        )
        print(
            json.dumps(
                {
                    "status": "hil_ready",
                    "source": HIL_SOURCE,
                    "evidence_ref": evidence_ref,
                },
                sort_keys=True,
            )
        )

        if not any([args.move_test, args.reverse_test, args.ros_mode_test, args.turn_test]):
            print("No movement flags set; smoke checks startup feedback only.")

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
    except (OSError, SerialException) as exc:
        print(f"ERROR: serial failure: {exc}", file=sys.stderr)
        print(SERIAL_OPEN_ERROR_NOTE, file=sys.stderr)
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
