#!/usr/bin/env python3
"""WAVE ROVER HIL packet intake dependency-free gate.

该工具只读取 packet directory 内的文件，不打开串口、不扫描 /dev、不调用
ROS graph。它把未来真实 HIL packet 的文件 contract 先接入 PC 围栏；
本机 synthetic fixture 只能证明 software_proof，不证明 hil_pass。
Vendor 来源见 docs/vendor/VENDOR_INDEX.md、json_cmd.h、uart_ctrl.h、
ugv_rpi/base_ctrl.py 与 ugv_rpi/config.yaml。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.wave_rover_hil_packet_intake.v1"
SUMMARY_SCHEMA = "trashbot.wave_rover_hil_packet_intake_summary.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_wave_rover_hil_packet_intake_gate"
SOURCE = "software_proof"
SAME_EVIDENCE_REF_REQUIRED = True

# json_cmd.h 定义 FEEDBACK_BASE_INFO 1001；本 gate 只接收该类 feedback。
FEEDBACK_TYPE = 1001
REQUIRED_FEEDBACK_FIELDS = ("T", "L", "R", "r", "p", "y", "v")
WRAPPER_PAYLOAD_KEYS = ("feedback", "payload", "message")

# 文件名是 contract 的一部分，摘要只暴露 basename，避免泄漏本机路径。
REQUIRED_FILES = (
    "feedback_T1001.log",
    "odom_once.jsonl",
    "imu_once.jsonl",
    "battery_once.jsonl",
    "operator_hil_report",
)

TOPIC_REQUIREMENTS = {
    "odom": ("pose", "twist", "position", "orientation", "linear", "angular"),
    "imu": ("orientation", "angular_velocity", "linear_acceleration", "rpy", "yaw"),
    "battery": ("voltage", "percentage", "power_supply_status", "current"),
}

OPERATOR_REQUIRED_FIELDS = (
    "operator",
    "run_timestamp",
    "robot_id",
    "serial_visibility_statement",
    "stop_path_statement",
    "result_boundary",
)

SAFE_EVIDENCE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")

# 这些 token 不应出现在 packet 内容里；它们会把本机路径、串口或凭证带给下游。
UNSAFE_TOKEN_PATTERNS = (
    re.compile(r"/dev/[A-Za-z0-9_.\-/]+"),
    re.compile(r"/Users/[A-Za-z0-9_.\-/]+"),
    re.compile(r"/tmp/[A-Za-z0-9_.\-/]+"),
    re.compile(r"\bserial_(port|device|path)\b", re.IGNORECASE),
    re.compile(r"\bbaud(rate)?\b", re.IGNORECASE),
    re.compile(r"\braw_(path|packet|feedback)\b", re.IGNORECASE),
    re.compile(r"\braw\s+(path|packet|feedback)\b", re.IGNORECASE),
    re.compile(r"\b(checksum|traceback)\b", re.IGNORECASE),
    re.compile(r"\b(password|passwd|secret|token|credential|authorization)\b", re.IGNORECASE),
)

SUCCESS_CLAIM_PATTERNS = (
    re.compile(r'"delivery_success"\s*:\s*true', re.IGNORECASE),
    re.compile(r"\bdelivery_success\s*=\s*true\b", re.IGNORECASE),
    re.compile(r'"primary_actions_enabled"\s*:\s*true', re.IGNORECASE),
    re.compile(r"\bprimary_actions_enabled\s*=\s*true\b", re.IGNORECASE),
    re.compile(r"\bhil_pass\s*[:=]\s*(true|pass|passed|success|ok)\b", re.IGNORECASE),
    re.compile(r"\b(hil_passed|hil pass(ed)?|hil success)\b", re.IGNORECASE),
)

NOT_PROVEN = (
    "real_wave_rover",
    "real_uart",
    "hil_pass",
    "real_odom",
    "real_imu",
    "real_battery",
    "delivery_success",
)

NEXT_REQUIRED_EVIDENCE = (
    "real WAVE ROVER HIL run",
    "real feedback_T1001.log",
    "real odom_once.jsonl",
    "real imu_once.jsonl",
    "real battery_once.jsonl",
    "operator_hil_report",
    "same evidence_ref HIL packet",
)

VENDOR_SOURCES = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
)


def _utc_now() -> str:
    # UTC 只用于 artifact 排序，不代表 HIL 运行时间。
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: Path) -> tuple[str, str]:
    # 所有 IO 错误都转换为 blocked issue，避免异常堆栈进入摘要。
    try:
        return path.read_text(encoding="utf-8"), ""
    except FileNotFoundError:
        return "", "missing"
    except UnicodeDecodeError:
        return "", "unicode_decode_error"
    except OSError:
        return "", "read_error"


def _json_object(value: Any) -> dict[str, Any] | None:
    # wrapper 里的 message/payload 可能是 JSON 字符串，坏 JSON 直接视为不可用。
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
    return None


def _nested_dict(value: Any) -> dict[str, Any]:
    # 上游 packet 可能缺 header/evidence，按空对象处理可以保持 fail-closed。
    return value if isinstance(value, dict) else {}


def _extract_evidence_ref(payload: dict[str, Any]) -> str:
    # evidence_ref 只从白名单位置读，避免深层 raw 字段误入 contract。
    candidates = (
        payload.get("evidence_ref"),
        _nested_dict(payload.get("header")).get("evidence_ref"),
        _nested_dict(payload.get("evidence")).get("evidence_ref"),
        _nested_dict(payload.get("route_progress")).get("evidence_ref"),
    )
    for candidate in candidates:
        text = str(candidate or "").strip()
        if text:
            return text
    return ""


def _safe_ref(value: str) -> bool:
    # safe evidence_ref 是下游跨文件关联键，不能携带路径或任意文本。
    return bool(value and SAFE_EVIDENCE_REF.match(value))


def _scan_unsafe_text(label: str, text: str) -> list[str]:
    # 扫描原始内容是为了阻止 raw path/serial/credential 进入 artifact 输入域。
    issues: list[str] = []
    for pattern in UNSAFE_TOKEN_PATTERNS:
        if pattern.search(text):
            issues.append(f"{label}:unsafe_token:{pattern.pattern}")
    for pattern in SUCCESS_CLAIM_PATTERNS:
        if pattern.search(text):
            issues.append(f"{label}:success_claim:{pattern.pattern}")
    return issues


def _required_paths(packet_dir: Path) -> tuple[dict[str, Path], list[str]]:
    # operator report 允许 json 或 md，但必须唯一，避免报告来源歧义。
    issues: list[str] = []
    paths = {
        "feedback": packet_dir / "feedback_T1001.log",
        "odom": packet_dir / "odom_once.jsonl",
        "imu": packet_dir / "imu_once.jsonl",
        "battery": packet_dir / "battery_once.jsonl",
    }
    report_json = packet_dir / "operator_hil_report.json"
    report_md = packet_dir / "operator_hil_report.md"
    report_candidates = [path for path in (report_json, report_md) if path.exists()]
    if len(report_candidates) != 1:
        issues.append("operator_hil_report_missing_or_ambiguous")
        paths["operator_report"] = report_json
    else:
        paths["operator_report"] = report_candidates[0]
    for name, path in paths.items():
        if name != "operator_report" and not path.exists():
            issues.append(f"{path.name}:missing")
    return paths, issues


def _extract_feedback(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    # 直接 T=1001 与 wrapper T=1001 都支持；非 1001 在本 contract 中 blocked。
    if payload.get("T") == FEEDBACK_TYPE:
        return payload, ""
    for key in WRAPPER_PAYLOAD_KEYS:
        nested = _json_object(payload.get(key))
        if nested and nested.get("T") == FEEDBACK_TYPE:
            merged = dict(nested)
            if "evidence_ref" not in merged:
                merged["evidence_ref"] = _extract_evidence_ref(payload)
            return merged, ""
    return None, "missing_T1001"


def _parse_feedback_log(path: Path) -> dict[str, Any]:
    # feedback log 每行必须是 JSON object；任何坏行都让 packet blocked。
    text, read_issue = _read_text(path)
    errors = [f"feedback_T1001.log:{read_issue}"] if read_issue else []
    errors.extend(_scan_unsafe_text("feedback_T1001.log", text))
    records: list[dict[str, Any]] = []
    refs: list[str] = []
    if read_issue:
        return {"status": "blocked", "record_count": 0, "evidence_refs": [], "errors": errors}

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"line_{line_number}:bad_json")
            continue
        if not isinstance(payload, dict):
            errors.append(f"line_{line_number}:not_object")
            continue
        feedback, issue = _extract_feedback(payload)
        if issue or feedback is None:
            errors.append(f"line_{line_number}:{issue}")
            continue
        missing = [field for field in REQUIRED_FEEDBACK_FIELDS if field not in feedback]
        if missing:
            errors.append(f"line_{line_number}:missing_fields:{','.join(missing)}")
        evidence_ref = _extract_evidence_ref(feedback) or _extract_evidence_ref(payload)
        if not _safe_ref(evidence_ref):
            errors.append(f"line_{line_number}:missing_or_unsafe_evidence_ref")
        else:
            refs.append(evidence_ref)
        if not missing and _safe_ref(evidence_ref):
            records.append({"line": line_number, "evidence_ref": evidence_ref})

    if not records:
        errors.append("feedback_T1001_no_valid_records")
    if len(set(refs)) > 1:
        errors.append("feedback_T1001_evidence_ref_mismatch")
    return {
        "status": "pass" if not errors else "blocked",
        "record_count": len(records),
        "evidence_ref": refs[0] if len(set(refs)) == 1 else "",
        "evidence_refs": sorted(set(refs)),
        "required_fields": list(REQUIRED_FEEDBACK_FIELDS),
        "vendor_feedback_type": "T=1001",
        "errors": sorted(set(errors)),
    }


def _parse_once_jsonl(path: Path, label: str) -> dict[str, Any]:
    # once JSONL 只接受第一条有效 object；多条数据不增加真实性。
    text, read_issue = _read_text(path)
    issues = [f"{label}:{read_issue}"] if read_issue else []
    issues.extend(_scan_unsafe_text(path.name, text))
    if read_issue:
        return {"status": "blocked", "evidence_ref": "", "minimum_fields_status": "blocked", "issues": issues}

    payload: dict[str, Any] | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            issues.append(f"{label}_line_{line_number}:bad_json")
            break
        if not isinstance(candidate, dict):
            issues.append(f"{label}_line_{line_number}:not_object")
            break
        payload = candidate
        break
    if payload is None:
        issues.append(f"{label}:empty")
        payload = {}

    evidence_ref = _extract_evidence_ref(payload)
    if not _safe_ref(evidence_ref):
        issues.append(f"{label}:missing_or_unsafe_evidence_ref")
        evidence_ref = ""
    fields_ok = any(field in payload for field in TOPIC_REQUIREMENTS[label])
    if not fields_ok:
        issues.append(f"{label}:missing_minimum_fields")
    return {
        "status": "pass" if not issues else "blocked",
        "evidence_ref": evidence_ref,
        "minimum_fields_status": "pass" if fields_ok else "blocked",
        "issues": sorted(set(issues)),
    }


def _parse_operator_report(path: Path) -> dict[str, Any]:
    # 报告摘要只输出字段状态，不回显 operator notes，避免人工材料泄漏本机细节。
    text, read_issue = _read_text(path)
    issues = [f"operator_hil_report:{read_issue}"] if read_issue else []
    issues.extend(_scan_unsafe_text(path.name, text))
    payload: dict[str, Any] = {}
    report_format = path.suffix.lstrip(".") or "missing"

    if not read_issue and path.suffix == ".json":
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError:
            issues.append("operator_hil_report:bad_json")
        else:
            if isinstance(loaded, dict):
                payload = loaded
            else:
                issues.append("operator_hil_report:not_object")
    elif not read_issue and path.suffix == ".md":
        payload = _parse_md_report(text)
    elif not read_issue:
        issues.append("operator_hil_report:unsupported_extension")

    missing = [field for field in OPERATOR_REQUIRED_FIELDS if not str(payload.get(field, "")).strip()]
    if missing:
        issues.append(f"operator_hil_report:missing_fields:{','.join(missing)}")
    evidence_ref = _extract_evidence_ref(payload)
    if not _safe_ref(evidence_ref):
        issues.append("operator_hil_report:missing_or_unsafe_evidence_ref")
        evidence_ref = ""

    return {
        "status": "pass" if not issues else "blocked",
        "format": report_format,
        "evidence_ref": evidence_ref,
        "required_fields": list(OPERATOR_REQUIRED_FIELDS),
        "missing_fields": missing,
        "safe_summary": {
            "operator_present": bool(str(payload.get("operator", "")).strip()),
            "run_timestamp_present": bool(str(payload.get("run_timestamp", "")).strip()),
            "robot_id_present": bool(str(payload.get("robot_id", "")).strip()),
            "serial_visibility_statement_present": bool(str(payload.get("serial_visibility_statement", "")).strip()),
            "stop_path_statement_present": bool(str(payload.get("stop_path_statement", "")).strip()),
            "result_boundary": str(payload.get("result_boundary", ""))[:80],
        },
        "issues": sorted(set(issues)),
    }


def _parse_md_report(text: str) -> dict[str, Any]:
    # Markdown 支持简单 key: value；不会把正文整段带进 summary。
    payload: dict[str, Any] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized = key.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in (*OPERATOR_REQUIRED_FIELDS, "evidence_ref"):
            payload[normalized] = value.strip()
    return payload


def _align_evidence_refs(parts: dict[str, dict[str, Any]], requested_ref: str) -> dict[str, Any]:
    # 所有输入文件必须同一个 evidence_ref；请求值存在时也必须一致。
    refs = {name: part.get("evidence_ref", "") for name, part in parts.items() if part.get("evidence_ref")}
    issues: list[str] = []
    expected_ref = requested_ref.strip()
    if expected_ref and not _safe_ref(expected_ref):
        issues.append("requested_evidence_ref_unsafe")
    observed_refs = {ref for ref in refs.values() if ref}
    if expected_ref and any(ref != expected_ref for ref in observed_refs):
        issues.append("requested_evidence_ref_mismatch")
    if not expected_ref and len(observed_refs) == 1:
        expected_ref = next(iter(observed_refs))
    elif not expected_ref:
        issues.append("evidence_ref_missing_or_ambiguous")
    if len(observed_refs) > 1:
        issues.append("packet_evidence_ref_mismatch")
    return {
        "status": "pass" if not issues else "blocked",
        "evidence_ref": expected_ref if _safe_ref(expected_ref) else "",
        "observed_refs": refs,
        "issues": sorted(set(issues)),
    }


def build_summary(packet_dir: str, evidence_ref: str = "") -> tuple[dict[str, Any], int]:
    # packet_dir 不展开到 artifact；摘要只报告 contract 状态，避免本机路径泄漏。
    root = Path(packet_dir)
    missing_issues: list[str] = []
    paths: dict[str, Path] = {}
    if not root.exists() or not root.is_dir():
        missing_issues.append("packet_dir_missing")
    else:
        paths, missing_issues = _required_paths(root)

    if missing_issues and not paths:
        parts = _empty_parts()
        alignment = {"status": "blocked", "evidence_ref": "", "observed_refs": {}, "issues": ["packet_dir_missing"]}
    else:
        feedback = _parse_feedback_log(paths["feedback"])
        odom = _parse_once_jsonl(paths["odom"], "odom")
        imu = _parse_once_jsonl(paths["imu"], "imu")
        battery = _parse_once_jsonl(paths["battery"], "battery")
        operator_report = _parse_operator_report(paths["operator_report"])
        parts = {
            "feedback": feedback,
            "odom": odom,
            "imu": imu,
            "battery": battery,
            "operator_report": operator_report,
        }
        alignment = _align_evidence_refs(parts, evidence_ref)

    part_statuses = {name: part.get("status", "blocked") for name, part in parts.items()}
    all_issues = sorted(
        set(
            missing_issues
            + alignment.get("issues", [])
            + [issue for part in parts.values() for issue in part.get("errors", []) + part.get("issues", [])]
        )
    )
    packet_status = "pass" if not all_issues and all(status == "pass" for status in part_statuses.values()) else "blocked"
    overall_status = "ready_for_hil_packet_review_not_proven" if packet_status == "pass" else "blocked_not_proven"

    summary = {
        "schema": SCHEMA,
        "summary_schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": overall_status,
        "packet_status": packet_status,
        "same_evidence_ref_required": SAME_EVIDENCE_REF_REQUIRED,
        "evidence_ref": alignment.get("evidence_ref", ""),
        "required_files": list(REQUIRED_FILES),
        "file_status": {
            "feedback_T1001.log": part_statuses.get("feedback", "blocked"),
            "odom_once.jsonl": part_statuses.get("odom", "blocked"),
            "imu_once.jsonl": part_statuses.get("imu", "blocked"),
            "battery_once.jsonl": part_statuses.get("battery", "blocked"),
            "operator_hil_report": part_statuses.get("operator_report", "blocked"),
        },
        "feedback_T1001": parts["feedback"],
        "topic_once": {
            "odom": parts["odom"],
            "imu": parts["imu"],
            "battery": parts["battery"],
        },
        "operator_hil_report": parts["operator_report"],
        "evidence_ref_alignment": alignment,
        "issues": all_issues,
        "vendor_sources": list(VENDOR_SOURCES),
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "next_required_evidence": list(NEXT_REQUIRED_EVIDENCE),
    }
    return summary, 0 if overall_status == "ready_for_hil_packet_review_not_proven" else 2


def _empty_parts() -> dict[str, dict[str, Any]]:
    # packet_dir 缺失时仍输出完整 shape，方便下游 fail-closed 消费。
    return {
        "feedback": {"status": "blocked", "record_count": 0, "evidence_ref": "", "evidence_refs": [], "errors": ["packet_dir_missing"]},
        "odom": {"status": "blocked", "evidence_ref": "", "minimum_fields_status": "blocked", "issues": ["packet_dir_missing"]},
        "imu": {"status": "blocked", "evidence_ref": "", "minimum_fields_status": "blocked", "issues": ["packet_dir_missing"]},
        "battery": {"status": "blocked", "evidence_ref": "", "minimum_fields_status": "blocked", "issues": ["packet_dir_missing"]},
        "operator_report": {"status": "blocked", "format": "missing", "evidence_ref": "", "issues": ["packet_dir_missing"]},
    }


def write_json(payload: dict[str, Any], output: str) -> None:
    # 输出路径是用户指定 artifact 位置；内容中不回写该路径。
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a WAVE ROVER HIL packet directory as software-proof intake only.",
    )
    parser.add_argument("packet_dir", nargs="?", help="Directory containing feedback_T1001.log, topic once JSONL files, and operator_hil_report")
    parser.add_argument("--evidence-ref", default="", help="Expected safe evidence_ref shared by every packet file")
    parser.add_argument("--summary-output", default="", help="Optional path for full JSON summary artifact")
    parser.add_argument("--once-json", action="store_true", help="Print compact one-line JSON summary to stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.packet_dir:
        # argparse 的 help 可独立运行；缺 packet_dir 时返回 blocked artifact 而不是 traceback。
        summary, exit_code = build_summary("__missing_packet_dir__", args.evidence_ref)
    else:
        summary, exit_code = build_summary(args.packet_dir, args.evidence_ref)
    if args.summary_output:
        write_json(summary, args.summary_output)
    if args.once_json or not args.summary_output:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
