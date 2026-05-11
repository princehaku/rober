#!/usr/bin/env python3
"""Validate a WAVE ROVER HIL evidence packet directory.

Vendor sources:
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h

This gate is deliberately file-only: it does not import ROS2, pyserial, or open
devices. It validates archived run evidence against the WAVE ROVER UART JSON
contract: newline-delimited UTF-8 JSON and base feedback frames with T=1001.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
]

REQUIRED_FILES = [
    "command.txt",
    "serial.log",
    "feedback_T1001.log",
    "odom_once.jsonl",
    "imu_once.jsonl",
    "battery_once.jsonl",
]

TOPIC_FILES = [
    "odom_once.jsonl",
    "imu_once.jsonl",
    "battery_once.jsonl",
]

SERIAL_BLOCKED_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"serial failure",
        r"could not open port",
        r"no such file or directory",
        r"no_serial_candidates_found",
        r"no serial candidates",
        r"filenotfounderror",
        r"permission denied",
        r"pyserial_missing",
        r"missing dependency pyserial",
        r"blocked",
    ]
]

NON_HIL_SOURCE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"source\s*[=:]\s*software_proof",
        r'"source"\s*:\s*"software_proof"',
        r"source\s*[=:]\s*simulated",
        r'"source"\s*:\s*"simulated"',
        r"source\s*[=:]\s*legacy",
        r'"source"\s*:\s*"legacy"',
        r"run_template_",
        r"dry[-_ ]?run",
    ]
]

MOVE_OR_SMOKE_COMMAND_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"hardware_smoke_wave_rover\.py",
        r"--move-test",
        r"--reverse-test",
        r"--ros-mode-test",
        r"--turn-test",
        r"move-test",
        r"smoke",
    ]
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def extract_json_objects(text: str) -> list[dict[str, Any]]:
    """Extract parseable JSON objects from raw log lines."""
    objects: list[dict[str, Any]] = []
    decoder = json.JSONDecoder()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        for start in [idx for idx, char in enumerate(line) if char == "{"]:
            try:
                parsed, _ = decoder.raw_decode(line[start:])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                objects.append(parsed)
                break
    return objects


def parse_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    parsed: list[dict[str, Any]] = []
    errors: list[str] = []
    for line_no, raw_line in enumerate(read_text(path).splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}:{line_no}: {exc.msg}")
            continue
        if isinstance(data, dict):
            parsed.append(data)
        else:
            errors.append(f"{path.name}:{line_no}: expected JSON object")
    return parsed, errors


def extract_evidence_refs(text: str) -> set[str]:
    refs: set[str] = set()
    for match in re.finditer(r"--evidence-ref\s+([A-Za-z0-9_.:-]+)", text):
        refs.add(match.group(1).strip())
    for match in re.finditer(r"evidence_ref\s*[=:]\s*([A-Za-z0-9_.:-]+)", text):
        refs.add(match.group(1).strip())
    for match in re.finditer(r'"evidence_ref"\s*:\s*"([^"]+)"', text):
        refs.add(match.group(1).strip())
    return {ref for ref in refs if ref}


def extract_sources(text: str) -> set[str]:
    sources: set[str] = set()
    for match in re.finditer(r'source[=:]\s*"?([A-Za-z0-9_-]+)"?', text):
        sources.add(match.group(1).strip().strip('"'))
    for match in re.finditer(r'"source"\s*:\s*"([^"]+)"', text):
        sources.add(match.group(1).strip())
    return {source for source in sources if source}


def check_required_files(packet_dir: Path) -> tuple[dict[str, Any], list[str]]:
    checks: dict[str, Any] = {}
    failures: list[str] = []
    for name in REQUIRED_FILES:
        path = packet_dir / name
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
        ok = exists and size > 0
        checks[name] = {"exists": exists, "nonempty": size > 0, "size_bytes": size}
        if not exists:
            failures.append(f"missing_required_file:{name}")
        elif size <= 0:
            failures.append(f"empty_required_file:{name}")
    return checks, failures


def detect_serial_block(serial_text: str) -> str | None:
    lowered = serial_text.strip().lower()
    if not lowered:
        return "serial_log_empty"
    for pattern in SERIAL_BLOCKED_PATTERNS:
        if pattern.search(serial_text):
            return f"serial_log_blocked:{pattern.pattern}"
    opened = re.search(r"\bOpened\s+\S+\s+@\s+\d+", serial_text)
    feedback_seen = any(obj.get("T") == 1001 for obj in extract_json_objects(serial_text))
    if not opened and not feedback_seen:
        return "serial_log_lacks_opened_device_or_feedback"
    return None


def command_traces_smoke(command_text: str) -> bool:
    if not command_text.strip():
        return False
    return any(pattern.search(command_text) for pattern in MOVE_OR_SMOKE_COMMAND_PATTERNS)


def has_status_only_command(command_text: str) -> bool:
    return "--status" in command_text and not any(
        flag in command_text
        for flag in ["--move-test", "--reverse-test", "--ros-mode-test", "--turn-test"]
    )


def find_non_hil_source(text: str) -> str | None:
    for pattern in NON_HIL_SOURCE_PATTERNS:
        if pattern.search(text):
            return pattern.pattern
    return None


def evaluate_packet(packet_dir: Path, allow_software_proof: bool) -> tuple[dict[str, Any], int]:
    failures: list[str] = []
    checks, required_failures = check_required_files(packet_dir)
    failures.extend(required_failures)

    command_text = read_text(packet_dir / "command.txt") if (packet_dir / "command.txt").is_file() else ""
    serial_text = read_text(packet_dir / "serial.log") if (packet_dir / "serial.log").is_file() else ""
    feedback_text = read_text(packet_dir / "feedback_T1001.log") if (packet_dir / "feedback_T1001.log").is_file() else ""

    evidence_refs = set()
    evidence_refs.update(extract_evidence_refs(command_text))
    evidence_refs.update(extract_evidence_refs(serial_text))
    evidence_refs.update(extract_evidence_refs(feedback_text))
    if packet_dir.name.startswith("run_"):
        evidence_refs.add(packet_dir.name)

    sources = set()
    sources.update(extract_sources(command_text))
    sources.update(extract_sources(serial_text))
    sources.update(extract_sources(feedback_text))

    command_ok = command_traces_smoke(command_text)
    checks["command_trace"] = {
        "ok": command_ok,
        "status_only": has_status_only_command(command_text),
    }
    if not command_ok:
        failures.append("command_missing_smoke_or_move_trace")

    serial_blocked_reason = detect_serial_block(serial_text)
    checks["serial_log"] = {
        **checks.get("serial.log", {}),
        "blocked_reason": serial_blocked_reason,
    }
    if serial_blocked_reason:
        failures.append(serial_blocked_reason)

    feedback_objects = extract_json_objects(feedback_text)
    t1001_objects = [obj for obj in feedback_objects if obj.get("T") == 1001]
    checks["feedback_T1001"] = {
        **checks.get("feedback_T1001.log", {}),
        "parseable_json_objects": len(feedback_objects),
        "t1001_count": len(t1001_objects),
    }
    if not t1001_objects:
        failures.append("missing_parseable_T1001_feedback")

    topic_counts: dict[str, int] = {}
    topic_parse_errors: dict[str, list[str]] = {}
    for name in TOPIC_FILES:
        path = packet_dir / name
        if not path.is_file():
            topic_counts[name] = 0
            continue
        rows, errors = parse_jsonl(path)
        for row in rows:
            if isinstance(row.get("evidence_ref"), str) and row["evidence_ref"].strip():
                evidence_refs.add(row["evidence_ref"].strip())
            if isinstance(row.get("source"), str) and row["source"].strip():
                sources.add(row["source"].strip())
        topic_counts[name] = len(rows)
        if errors:
            topic_parse_errors[name] = errors
        if not rows:
            failures.append(f"missing_parseable_topic_sample:{name}")
    checks["topic_jsonl"] = {
        "sample_counts": topic_counts,
        "parse_errors": topic_parse_errors,
    }

    combined_text = "\n".join([command_text, serial_text, feedback_text])
    non_hil_source_reason = find_non_hil_source(combined_text)
    checks["source_boundary"] = {
        "sources_seen": sorted(sources),
        "non_hil_source_reason": non_hil_source_reason,
    }
    if non_hil_source_reason:
        failures.append(f"non_hil_source:{non_hil_source_reason}")
    for source in sorted(sources):
        if source != "hil_pass":
            failures.append(f"non_hil_source:{source}")

    checks["evidence_ref"] = {"refs_seen": sorted(evidence_refs)}
    if not evidence_refs:
        failures.append("missing_evidence_ref")
    elif len(evidence_refs) > 1:
        failures.append("contradictory_evidence_ref")

    evidence_ref = sorted(evidence_refs)[0] if len(evidence_refs) == 1 else None

    status = "hil_pass"
    if failures:
        if allow_software_proof and has_status_only_command(command_text):
            status = "software_proof"
        else:
            status = "blocked"

    blocked_reason = None
    if status == "blocked":
        blocked_reason = failures[0] if failures else "blocked"
    elif status == "software_proof":
        blocked_reason = "software_proof_allowed_status_only_packet"

    payload = {
        "status": status,
        "source": status,
        "evidence_ref": evidence_ref,
        "blocked_reason": blocked_reason,
        "failures": failures,
        "checks": checks,
        "vendor_sources": VENDOR_SOURCES,
    }
    return payload, 0 if status == "hil_pass" else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a file-only WAVE ROVER HIL evidence packet gate.",
    )
    parser.add_argument("--packet-dir", required=True, help="Evidence run directory to validate.")
    parser.add_argument(
        "--allow-software-proof",
        action="store_true",
        help="Allow status/template packets to return status=software_proof; exit remains nonzero.",
    )
    args = parser.parse_args()

    packet_dir = Path(args.packet_dir)
    if not packet_dir.is_dir():
        payload = {
            "status": "blocked",
            "source": "blocked",
            "evidence_ref": None,
            "blocked_reason": "packet_dir_missing",
            "failures": ["packet_dir_missing"],
            "checks": {"packet_dir": {"path": str(packet_dir), "exists": False}},
            "vendor_sources": VENDOR_SOURCES,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    payload, exit_code = evaluate_packet(packet_dir, args.allow_software_proof)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
