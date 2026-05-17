#!/usr/bin/env python3
"""WAVE ROVER HIL packet review-decision dependency-free gate.

该工具只读取上一轮 wave_rover_hil_packet_intake artifact/summary JSON。
它不打开串口、不扫描 /dev、不调用 ROS graph，也不把 synthetic packet
升级成 hil_pass。Vendor 来源见 docs/vendor/VENDOR_INDEX.md、json_cmd.h、
uart_ctrl.h、ugv_rpi/base_ctrl.py 与 ugv_rpi/config.yaml。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.wave_rover_hil_packet_review_decision.v1"
SUMMARY_SCHEMA = "trashbot.wave_rover_hil_packet_review_decision_summary.v1"
INTAKE_SCHEMA = "trashbot.wave_rover_hil_packet_intake.v1"
INTAKE_SUMMARY_SCHEMA = "trashbot.wave_rover_hil_packet_intake_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_wave_rover_hil_packet_review_decision_gate"
INTAKE_BOUNDARY = "software_proof_docker_wave_rover_hil_packet_intake_gate"

# safe evidence_ref 只能作为跨 artifact 关联键，不能携带本机路径或任意说明。
SAFE_EVIDENCE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")

REQUIRED_FILES = (
    "feedback_T1001.log",
    "odom_once.jsonl",
    "imu_once.jsonl",
    "battery_once.jsonl",
    "operator_hil_report",
)

REAL_REQUIRED_MATERIALS = (
    "real feedback_T1001.log",
    "real odom_once.jsonl",
    "real imu_once.jsonl",
    "real battery_once.jsonl",
    "operator_hil_report",
)

NEXT_REQUIRED_EVIDENCE = (
    "real WAVE ROVER HIL run",
    "same evidence_ref HIL packet",
    "real feedback_T1001.log",
    "real odom_once.jsonl",
    "real imu_once.jsonl",
    "real battery_once.jsonl",
    "operator_hil_report",
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

VENDOR_SOURCES = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
)

# 输入摘要不能携带本机路径、串口参数、凭证或成功断言。
UNSAFE_INPUT_PATTERNS = (
    re.compile(r"/dev/[A-Za-z0-9_.\-/]+"),
    re.compile(r"/Users/[A-Za-z0-9_.\-/]+"),
    re.compile(r"/tmp/[A-Za-z0-9_.\-/]+"),
    re.compile(r"\bserial_(port|device|path)\b", re.IGNORECASE),
    re.compile(r"\bbaud(rate)?\b", re.IGNORECASE),
    re.compile(r"\braw_(path|packet|feedback)\b", re.IGNORECASE),
    re.compile(r"\b(checksum|traceback)\b", re.IGNORECASE),
    re.compile(r"\b(password|passwd|secret|token|credential|authorization)\b", re.IGNORECASE),
    re.compile(r'"delivery_success"\s*:\s*true', re.IGNORECASE),
    re.compile(r"\bdelivery_success\s*=\s*true\b", re.IGNORECASE),
    re.compile(r'"primary_actions_enabled"\s*:\s*true', re.IGNORECASE),
    re.compile(r"\bprimary_actions_enabled\s*=\s*true\b", re.IGNORECASE),
    re.compile(r"\bhil_pass\s*[:=]\s*(true|pass|passed|success|ok)\b", re.IGNORECASE),
    re.compile(r"\b(hil_passed|hil pass(ed)?|hil success)\b", re.IGNORECASE),
)


def _utc_now() -> str:
    # UTC 时间只用于 artifact 排序，不代表真实 HIL 运行时间。
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺 intake summary 是可预期 blocked 状态，不把 traceback 写入下游。
    if path is None:
        return {}, "missing"
    try:
        payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "missing"
    except json.JSONDecodeError:
        return {}, "invalid_json"
    except (OSError, UnicodeDecodeError):
        return {}, "read_error"
    if not isinstance(payload, dict):
        return {}, "invalid_json"
    return payload, ""


def _dict(value: Any) -> dict[str, Any]:
    # summary 可能被上游包在 wrapper 里；非 object 一律忽略。
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    # 下游只关心列表语义，缺字段按空列表 fail-closed 处理。
    return list(value) if isinstance(value, (list, tuple)) else []


def _text(value: Any, default: str = "") -> str:
    # 输出到 mobile/diagnostics 前统一收窄为短字符串。
    if value is None:
        return default
    text = value.strip() if isinstance(value, str) else str(value).strip()
    return text or default


def _safe_ref(value: str) -> bool:
    # evidence_ref 是唯一可跨 surface 展示的关联键。
    return bool(value and SAFE_EVIDENCE_REF.match(value))


def _effective_intake(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先消费 sanitized summary，再兼容直接 intake artifact。
    for key in (
        "wave_rover_hil_packet_intake_summary",
        "hil_packet_intake_summary",
        "intake_summary",
        "summary",
    ):
        nested = _dict(payload.get(key))
        if nested.get("schema") in {INTAKE_SCHEMA, INTAKE_SUMMARY_SCHEMA} or nested.get("summary_schema") == INTAKE_SUMMARY_SCHEMA:
            return nested
    return payload


def _scan_unsafe_input(payload: dict[str, Any]) -> list[str]:
    # 扫描序列化摘要可覆盖嵌套 note 里的危险成功文案。
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return [f"unsafe_input:{pattern.pattern}" for pattern in UNSAFE_INPUT_PATTERNS if pattern.search(text)]


def _schema_status(payload: dict[str, Any], intake: dict[str, Any]) -> str:
    # 只接受上一轮 intake gate 的 artifact/summary，避免误吃其他证据。
    schema = _text(intake.get("schema") or payload.get("schema"))
    summary_schema = _text(intake.get("summary_schema") or payload.get("summary_schema"))
    boundary = _text(intake.get("evidence_boundary") or payload.get("evidence_boundary"))
    source = _text(intake.get("source") or payload.get("source"))
    if schema and schema not in {INTAKE_SCHEMA, INTAKE_SUMMARY_SCHEMA}:
        return "unsupported_schema"
    if not schema and summary_schema != INTAKE_SUMMARY_SCHEMA:
        return "unsupported_schema"
    if boundary != INTAKE_BOUNDARY:
        return "unsupported_boundary"
    if source != SOURCE:
        return "unsupported_source"
    return "supported"


def _flag_status(intake: dict[str, Any]) -> list[str]:
    # 三个边界 flag 是 Robot/mobile fail-closed 的硬门槛。
    issues: list[str] = []
    if intake.get("delivery_success") is not False:
        issues.append("delivery_success_not_false")
    if intake.get("primary_actions_enabled") is not False:
        issues.append("primary_actions_enabled_not_false")
    if intake.get("same_evidence_ref_required") is not True:
        issues.append("same_evidence_ref_required_not_true")
    not_proven = {str(item) for item in _list(intake.get("not_proven"))}
    missing_not_proven = [item for item in NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        issues.append("not_proven_missing:" + ",".join(missing_not_proven))
    return issues


def _file_statuses(intake: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    # accepted 只表示上一轮软件围栏材料齐全，不表示真实上车材料已接受。
    file_status = _dict(intake.get("file_status"))
    required_files = {str(item) for item in _list(intake.get("required_files"))}
    accepted: list[str] = []
    missing: list[str] = []
    rejected: list[str] = []
    for name in REQUIRED_FILES:
        status = _text(file_status.get(name), "missing")
        if name not in required_files:
            missing.append(f"{name}:not_declared_by_intake")
        elif status == "pass":
            accepted.append(f"software-proof {name}")
        elif status == "missing":
            missing.append(name)
        else:
            rejected.append(f"{name}:{status}")
    return accepted, missing, rejected


def _evidence_ref_status(intake: dict[str, Any], expected_ref: str) -> tuple[str, list[str]]:
    # CLI 指定值存在时必须与 intake summary 完全一致。
    observed = _text(intake.get("evidence_ref"))
    issues: list[str] = []
    if not _safe_ref(observed):
        issues.append("intake_evidence_ref_missing_or_unsafe")
    if expected_ref and not _safe_ref(expected_ref):
        issues.append("requested_evidence_ref_unsafe")
    if expected_ref and observed and expected_ref != observed:
        issues.append("requested_evidence_ref_mismatch")
    return observed if _safe_ref(observed) else "", issues


def _review_decision(load_issue: str, schema_status: str, issues: list[str], source_status: str) -> str:
    # 决策枚举保持窄集合，便于下游只读消费。
    if load_issue:
        return "blocked_missing_wave_rover_hil_packet_intake"
    if schema_status != "supported":
        return "blocked_unsupported_wave_rover_hil_packet_intake"
    if any(issue.startswith("unsafe_input") for issue in issues):
        return "blocked_unsafe_wave_rover_hil_packet_claim"
    if "requested_evidence_ref_mismatch" in issues or "intake_evidence_ref_missing_or_unsafe" in issues:
        return "blocked_wave_rover_hil_packet_evidence_ref_mismatch"
    if source_status not in {"ready_for_hil_packet_review_not_proven", "not_proven"}:
        return "blocked_wave_rover_hil_packet_intake_not_ready"
    if issues:
        return "blocked_wave_rover_hil_packet_review_contract"
    return "blocked_pending_real_hil_packet"


def _owner_handoff() -> dict[str, str]:
    # owner handoff 只描述补证动作，不包含串口或 /cmd_vel 操作。
    return {
        "hardware-engineer": "collect real HIL packet on a host with WAVE ROVER UART access",
        "robot-software-engineer": "keep diagnostics read-only until review_decision changes with real evidence",
        "full-stack-software-engineer": "keep mobile panel read-only and actions disabled",
    }


def _rerun_commands() -> list[str]:
    # rerun commands 只给 PC evidence gate，不打开 ROS graph 或串口。
    return [
        "python3 pc-tools/evidence/wave_rover_hil_packet_intake.py --packet-dir <real_packet_dir>",
        "python3 pc-tools/evidence/wave_rover_hil_packet_review_decision.py --intake-summary <summary.json>",
    ]


def _summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # summary 是 Robot/mobile 应消费的稳定、去路径化 contract。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": artifact["review_decision"],
        "wave_rover_hil_packet_review_decision": artifact["review_decision"],
        "evidence_ref": artifact["evidence_ref"],
        "review_decision": artifact["review_decision"],
        "accepted_required_materials": artifact["accepted_required_materials"],
        "missing_required_materials": artifact["missing_required_materials"],
        "rejected_required_materials": artifact["rejected_required_materials"],
        "next_required_evidence": artifact["next_required_evidence"],
        "owner_handoff": artifact["owner_handoff"],
        "rerun_commands": artifact["rerun_commands"],
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "boundary_note": "software_proof only; not_proven; delivery_success=false; primary_actions_enabled=false",
    }


def build_review_decision(intake_summary: str | Path | None = None, evidence_ref: str = "") -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 intake artifact/summary，生成 WAVE ROVER HIL packet review decision。"""

    path = Path(intake_summary) if intake_summary else None
    payload, load_issue = _read_json(path)
    intake = _effective_intake(payload)
    schema_status = "missing" if load_issue else _schema_status(payload, intake)
    source_status = _text(intake.get("overall_status") or intake.get("status"), "missing_source_status")
    accepted, missing, rejected = _file_statuses(intake) if not load_issue else ([], list(REQUIRED_FILES), [])
    observed_ref, ref_issues = _evidence_ref_status(intake, evidence_ref.strip()) if not load_issue else ("", ["intake_evidence_ref_missing_or_unsafe"])

    issues = sorted(
        set(
            ([] if not load_issue else [f"intake_summary:{load_issue}"])
            + ([] if schema_status in {"supported", "missing"} else [schema_status])
            + _scan_unsafe_input(payload)
            + _flag_status(intake)
            + ref_issues
            + [f"missing_required_material:{item}" for item in missing]
            + [f"rejected_required_material:{item}" for item in rejected]
        )
    )
    decision = _review_decision(load_issue, schema_status, issues, source_status)

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "summary_schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": "not_proven",
        "review_decision": decision,
        "wave_rover_hil_packet_review_decision": decision,
        "source_intake_schema": _text(intake.get("schema") or payload.get("schema"), "missing"),
        "source_intake_summary_schema": _text(intake.get("summary_schema") or payload.get("summary_schema"), "missing"),
        "source_intake_boundary": _text(intake.get("evidence_boundary") or payload.get("evidence_boundary"), "missing"),
        "source_intake_status": source_status,
        "schema_status": schema_status,
        "same_evidence_ref_required": True,
        "evidence_ref": observed_ref,
        "accepted_required_materials": accepted,
        "missing_required_materials": list(REAL_REQUIRED_MATERIALS),
        "software_proof_missing_materials": missing,
        "rejected_required_materials": rejected,
        "next_required_evidence": list(NEXT_REQUIRED_EVIDENCE),
        "owner_handoff": _owner_handoff(),
        "rerun_commands": _rerun_commands(),
        "issues": issues,
        "vendor_sources": list(VENDOR_SOURCES),
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "non_access_scope": [
            "serial_uart",
            "dev_device_probe",
            "ros_graph",
            "cmd_vel",
            "hardware_bus",
            "hil_runtime",
            "delivery_execution",
        ],
        "boundary_note": "software_proof only; not_proven; delivery_success=false; primary_actions_enabled=false",
    }
    summary = _summary(artifact)
    artifact["review_summary"] = summary
    exit_code = 0 if decision == "blocked_pending_real_hil_packet" else 2
    return artifact, summary, exit_code


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出文件内容不回显本机绝对路径，避免路径进入下游 artifact。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只做 review decision，不访问真实 UART、ROS2 或 HIL。
    parser = argparse.ArgumentParser(
        description="Generate WAVE ROVER HIL packet review-decision software-proof artifact."
    )
    parser.add_argument("--intake-summary", default="", help="Previous wave_rover_hil_packet_intake artifact or summary JSON.")
    parser.add_argument("--evidence-ref", default="", help="Optional expected safe evidence_ref shared with the intake summary.")
    parser.add_argument("--output", default="", help="Write full review-decision artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact review-decision summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_review_decision(args.intake_summary or None, args.evidence_ref)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("wave_rover_hil_packet_review_decision: artifact_file:" + (Path(args.output).name if args.output else ""))
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
