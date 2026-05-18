#!/usr/bin/env python3
"""生成 elevator field evidence trace callback intake artifact。

该 gate 只读消费 safe callback packet、elevator_action_feedback_trace summary、
Robot diagnostics safe summary，以及 required route/elevator materials 元数据。
它把现场 owner 的回填包收敛成同一 safe evidence_ref 下的可复盘 summary；
它不读取真实材料目录、不访问 ROS graph、Nav2/fixed-route runtime、硬件、云、
真实手机/browser，也不证明真实 route/elevator field pass 或 delivery success。
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_SCHEMA = "trashbot.elevator_field_evidence_trace_callback_intake.v1"
SUMMARY_SCHEMA = "trashbot.elevator_field_evidence_trace_callback_intake_summary.v1"
CALLBACK_PACKET_SCHEMA = "trashbot.elevator_field_evidence_trace_callback_packet.v1"
CALLBACK_PACKET_SUMMARY_SCHEMA = "trashbot.elevator_field_evidence_trace_callback_packet_summary.v1"
TRACE_SCHEMA = "trashbot.elevator_action_feedback_trace.v1"
TRACE_SUMMARY_SCHEMA = "trashbot.elevator_action_feedback_trace_summary.v1"
ROBOT_TRACE_SUMMARY_SCHEMA = "trashbot.robot_diagnostics_elevator_action_feedback_trace_summary.v1"
MATERIALS_SCHEMA = "trashbot.elevator_field_evidence_trace_required_materials.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_elevator_field_evidence_trace_callback_intake_gate"

# 这些 literal 同时服务 rg 验收和后续 Robot/mobile 白名单消费。
BOUNDARY_NOTE = (
    "elevator_field_evidence_trace_callback_intake; elevator_action_feedback_trace; "
    "safe_evidence_ref; source=software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; real_route_elevator_field_pass; "
    "callback_packet_intake_ready_for_review_not_proven"
)

# required materials 只表示后续必须补采的类别，不表示本 gate 会读取真实文件。
REQUIRED_ROUTE_ELEVATOR_MATERIALS = (
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_record",
    "real_nav2_or_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_field_task_record",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result",
)

# not_proven 固定写入 artifact/summary，防止下游把 metadata intake 当实机通过。
NOT_PROVEN = (
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime",
    "real_fixed_route_runtime",
    "real_task_record_runtime",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_record",
    "real_dropoff_or_cancel_completion",
    "real_delivery_success",
    "real_waverover_uart_hil",
    "real_phone_browser",
    "objective_5_external_proof",
    "delivery_success",
)

TRACE_SCHEMAS = {TRACE_SCHEMA, TRACE_SUMMARY_SCHEMA, ROBOT_TRACE_SUMMARY_SCHEMA}
DIAGNOSTICS_SCHEMAS = {TRACE_SUMMARY_SCHEMA, ROBOT_TRACE_SUMMARY_SCHEMA}
CALLBACK_SCHEMAS = {"", CALLBACK_PACKET_SCHEMA, CALLBACK_PACKET_SUMMARY_SCHEMA}
MATERIAL_SCHEMAS = {"", MATERIALS_SCHEMA, SUMMARY_SCHEMA}
SOURCE_VALUES = {"software_proof", ""}
OVERALL_VALUES = {"not_proven", "", "elevator_action_feedback_trace_not_proven"}
CALLBACK_BOUNDARIES = {"", EVIDENCE_BOUNDARY, "software_proof"}

# callback 是现场入口，字段必须白名单化，避免 raw artifact 被塞入摘要。
CALLBACK_ALLOWED_FIELDS = {
    "schema",
    "schema_version",
    "source",
    "evidence_boundary",
    "boundary",
    "status",
    "callback_status",
    "packet_status",
    "safe_evidence_ref",
    "evidence_ref",
    "same_evidence_ref_required",
    "owner_acknowledgement",
    "redaction_status",
    "trace_summary_ref",
    "diagnostics_summary_ref",
    "redacted_callback_packet_metadata",
    "accepted_callback_materials",
    "material_responses",
    "received_materials",
    "accepted_materials",
    "missing_required_materials",
    "missing_materials",
    "rejected_materials",
    "required_route_elevator_materials",
    "owner_handoff",
    "next_required_evidence",
    "safe_copy",
    "delivery_success",
    "primary_actions_enabled",
}

# 成功、控制、硬件、凭证、路径和 raw log 文案必须在脱敏前 fail closed。
FORBIDDEN_COPY = (
    "Authorization",
    "OSS_ACCESS_KEY",
    "OSS_SECRET",
    "access_key",
    "secret",
    "token",
    "password",
    "postgres://",
    "postgresql://",
    "mysql://",
    "redis://",
    "amqp://",
    "mongodb://",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "serial",
    "UART",
    "baudrate",
    "baud_rate",
    "WAVE ROVER",
    "Traceback",
    "checksum",
    "complete artifact",
    "raw robot response",
)

SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\b(real_)?route[_ -]?elevator[_ -]?field[_ -]?pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(real_)?route[_ -]?elevator[_ -]?field\s+passed\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bcancel\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
)

RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\bOSS_[A-Z_]*(ACCESS|SECRET)[A-Z_]*\b\s*[:=]\s*[^,\s]+"), "OSS_KEY=[REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_RATE]"),
    (re.compile(r"(?i)\bserial\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bUART\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bWAVE\s+ROVER\b"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"), r"\1[REDACTED_PATH]"),
    (re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 便于 Docker、PC 和后续 sprint 产物按时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本先脱敏，最终输出不回显路径、凭证、ROS topic 或硬件传输细节。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 若误填成本机路径，只保留 basename，避免泄漏 host 目录。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线；它不能替代前置 unsafe fail-closed 判定。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _encoded(value: Any) -> str:
    # unsafe 扫描需要覆盖嵌套键和值；不可编码时退回安全文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 禁止词必须在脱敏前命中并阻断，不能“清洗后 ready”。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_raw_path_copy(value: Any) -> bool:
    # 本 gate 不读取真实材料目录；绝对路径 copy 直接视为不安全。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(value: Any) -> bool:
    # 布尔字段和自然语言都检查，防止 route/elevator field pass 语义穿透。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _unsafe_copy(value: Any) -> bool:
    # 只读 intake 的外部输入不能携带路径、凭证、控制 topic、硬件事实或成功声明。
    return _has_forbidden_copy(value) or _has_raw_path_copy(value) or _has_success_or_control_claim(value)


def _resolve_source_path(source: str) -> tuple[str, str]:
    # file:/env: 只解析 JSON 来源，不把 source path 写入 safe summary。
    text = str(source or "").strip()
    if text.startswith("file:"):
        return text.removeprefix("file:"), "file_source"
    if text.startswith("env:"):
        name = text.removeprefix("env:").strip()
        if not name:
            return "", "env_source_name_missing"
        value = os.environ.get(name, "").strip()
        if not value:
            return "", "env_source_missing"
        return value.removeprefix("file:"), "env_source"
    return text, "path_source"


def _load_json(source: str, label: str, required: bool = True) -> tuple[dict[str, Any], str, str]:
    # 缺输入、坏 JSON、非 object 都返回机器可判定 issue，不抛异常中断自动化。
    path, source_style = _resolve_source_path(source)
    if not path:
        return {}, f"{label}_not_provided" if required else "", source_style
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, f"{label}_missing", source_style
    except json.JSONDecodeError:
        return {}, f"{label}_bad_json", source_style
    except (OSError, UnicodeDecodeError):
        return {}, f"{label}_read_error", source_style
    if not isinstance(payload, dict):
        return {}, f"{label}_not_object", source_style
    return payload, "", source_style


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段，字符串 wrapper 不能伪装可信 summary。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 字段位置不同，取首个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 64) -> list[Any]:
    # list 输入统一限长，避免把完整 callback body 或 raw artifact 复制出去。
    if isinstance(value, list):
        return _safe_value(value[:limit])
    if value in (None, ""):
        return []
    return [_safe_value(value)]


def _source_candidates(payload: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    # 只递归白名单 wrapper，避免任意嵌套 JSON 被当成可信来源。
    candidates = [payload]
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value, keys))
    return candidates


def _find_by_schema(payload: dict[str, Any], schemas: set[str], keys: tuple[str, ...]) -> dict[str, Any]:
    # schema 命中时优先；否则保留顶层用于 unsupported 诊断。
    for candidate in _source_candidates(payload, keys):
        if str(candidate.get("schema", "")).strip() in schemas:
            return candidate
    return payload


def _find_callback(payload: dict[str, Any]) -> dict[str, Any]:
    # 无 schema callback 也允许，但候选对象必须含白名单字段。
    keys = (
        "elevator_field_evidence_trace_callback_packet",
        "elevator_field_evidence_trace_callback_intake",
        "safe_callback_packet",
        "sanitized_callback",
        "callback_packet",
        "callback",
        "packet",
        "safe_copy",
        "payload",
        "data",
    )
    for candidate in _source_candidates(payload, keys):
        has_callback_field = bool(set(candidate.keys()) & CALLBACK_ALLOWED_FIELDS)
        if str(candidate.get("schema", "")).strip() in CALLBACK_SCHEMAS and has_callback_field:
            return candidate
    return payload


def _source_status(issue: str, source: dict[str, Any], schemas: set[str], label: str, source_style: str) -> dict[str, Any]:
    # trace/diagnostics summary 必须保持 software_proof、not_proven 和只读 flags。
    if issue:
        return {"load_status": "blocked", "load_issue": issue, "schema_status": "not_loaded", "source_style": source_style}
    schema = _safe_text(source.get("schema", "")).strip()
    source_value = _safe_text(_first_text(source.get("source"), source.get("source_boundary"), source.get("evidence_boundary"), default="")).strip()
    status_value = _safe_text(_first_text(source.get("overall_status"), source.get("status"), default="")).strip()
    flags_ok = source.get("delivery_success") is not True and source.get("primary_actions_enabled") is not True
    schema_ok = schema in schemas
    source_ok = source_value in SOURCE_VALUES or source_value.startswith("software_proof")
    status_ok = status_value in OVERALL_VALUES or status_value.endswith("_not_proven")
    return {
        "load_status": "loaded",
        "load_issue": "",
        "schema_status": "supported" if schema_ok and source_ok and status_ok and flags_ok else "unsupported",
        "source_style": source_style,
        "schema": schema,
        "source": source_value,
        "status": status_value,
        "safe_evidence_ref": _source_ref(source),
        "unsafe_copy": bool(_unsafe_copy(source)) if source else False,
        "label": label,
    }


def _callback_status(issue: str, callback: dict[str, Any], source_style: str) -> dict[str, Any]:
    # callback packet 是外部回填入口；未知 schema/boundary/字段都不能默认透传。
    if issue:
        return {"load_status": "blocked", "load_issue": issue, "schema_status": "not_loaded", "field_status": "not_loaded", "source_style": source_style}
    schema = _safe_text(callback.get("schema", "")).strip()
    boundary = _safe_text(_first_text(callback.get("evidence_boundary"), callback.get("boundary"), callback.get("source"), default="")).strip()
    unknown = sorted(set(callback.keys()) - CALLBACK_ALLOWED_FIELDS)
    schema_ok = schema in CALLBACK_SCHEMAS
    boundary_ok = boundary in CALLBACK_BOUNDARIES or boundary.startswith("software_proof")
    return {
        "load_status": "loaded",
        "load_issue": "",
        "schema_status": "supported" if schema_ok and boundary_ok else "unsupported",
        "field_status": "supported" if not unknown else "unsupported_fields",
        "unsupported_fields": unknown,
        "source_style": source_style,
        "schema": schema,
        "evidence_boundary": boundary,
        "safe_evidence_ref": _source_ref(callback),
        "unsafe_copy": bool(_unsafe_copy(callback)) if callback else False,
    }


def _source_ref(source: dict[str, Any]) -> str:
    # safe_copy 和 summary wrapper 都可能承载 ref，优先 safe_evidence_ref。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "summary")
    return _safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            summary.get("safe_evidence_ref"),
            summary.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _same_ref_required(*sources: dict[str, Any]) -> Any:
    # 任一输入显式弱化 same-ref 约束都必须 fail closed。
    for source in sources:
        if "same_evidence_ref_required" in source:
            return source.get("same_evidence_ref_required")
        safe_copy = _dict(source, "safe_copy")
        if "same_evidence_ref_required" in safe_copy:
            return safe_copy.get("same_evidence_ref_required")
    return True


def _same_ref_match(refs: dict[str, str]) -> dict[str, Any]:
    # same evidence_ref 是现场材料复账主键；所有显式 ref 必须一致且非空。
    expected = next((ref for ref in refs.values() if ref), "")
    mismatches = sorted({ref for ref in refs.values() if ref and expected and ref != expected})
    missing = sorted(key for key, ref in refs.items() if key in {"callback", "trace", "diagnostics"} and not ref)
    if not expected or missing:
        status = "missing_evidence_ref"
    elif mismatches:
        status = "mismatch"
    else:
        status = "matched"
    return {
        "status": status,
        "expected_evidence_ref": expected,
        "refs": refs,
        "missing_required_refs": missing,
        "mismatched_evidence_refs": mismatches,
    }


def _material_name(value: Any) -> str:
    # 材料主键兼容字符串和 object，避免现场表单格式稍有差异就失效。
    if isinstance(value, dict):
        return _safe_text(_first_text(value.get("material"), value.get("name"), value.get("category"), default="")).strip()
    return _safe_text(value).strip()


def _required_materials(material_source: dict[str, Any], trace: dict[str, Any], diagnostics: dict[str, Any], callback: dict[str, Any]) -> list[str]:
    # required list 可以来自显式材料文件、trace/diagnostics summary 或 callback packet。
    raw = (
        material_source.get("required_route_elevator_materials")
        or trace.get("required_route_elevator_materials")
        or diagnostics.get("required_route_elevator_materials")
        or callback.get("required_route_elevator_materials")
        or REQUIRED_ROUTE_ELEVATOR_MATERIALS
    )
    materials: list[str] = []
    for item in _safe_list(raw, limit=32):
        name = _material_name(item)
        if name and name not in materials:
            materials.append(name)
    for material in REQUIRED_ROUTE_ELEVATOR_MATERIALS:
        if material not in materials:
            materials.append(material)
    return materials


def _parse_material_responses(callback: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    # material_responses 使用机器可判定状态，弱类型不进入 ready。
    value = callback.get("material_responses")
    responses: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    entries: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for name, status in value.items():
            entries.append({"material": name, "status": status})
    elif isinstance(value, list):
        if any(not isinstance(item, dict) for item in value):
            return {}, ["weak_material_responses"]
        entries = value
    elif value not in (None, ""):
        return {}, ["weak_material_responses"]

    for key, status in (("received_materials", "received"), ("accepted_materials", "received"), ("missing_required_materials", "missing"), ("missing_materials", "missing"), ("rejected_materials", "rejected")):
        for item in _safe_list(callback.get(key), limit=32):
            name = _material_name(item)
            if name:
                note = item.get("safe_note", item.get("note", "")) if isinstance(item, dict) else ""
                entries.append({"material": name, "status": status, "safe_note": note})

    for item in entries:
        name = _material_name(item)
        raw_status = item.get("status", item.get("result"))
        if not name or not isinstance(raw_status, str):
            issues.append("weak_material_responses")
            continue
        status = raw_status.strip().lower()
        if status in {"accepted", "received", "recorded", "present"}:
            status = "received"
        if status in {"backfill_required", "missing", "pending"}:
            status = "missing"
        if status not in {"received", "missing", "rejected"}:
            issues.append("unsupported_material_response_status")
            continue
        responses[name] = {"material": name, "status": status, "safe_note": _safe_text(_first_text(item.get("safe_note"), item.get("note"), item.get("reason"), default=""))}
    return responses, sorted(set(issues))


def _merge_materials(required: list[str], responses: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    # 这里只判断“callback 是否对材料类别有安全回执”，不打开或评价真实材料内容。
    accepted: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for material in required:
        response = responses.get(material)
        base = {"material": material, "required": True}
        if not response:
            missing.append({**base, "reason": "callback_response_missing"})
        elif response["status"] == "received":
            accepted.append({**base, "safe_note": response["safe_note"]})
        elif response["status"] == "missing":
            missing.append({**base, "safe_note": response["safe_note"], "reason": "callback_marked_missing"})
        else:
            rejected.append({**base, "safe_note": response["safe_note"], "reason": "callback_marked_rejected"})
    for material, response in responses.items():
        if material not in required:
            rejected.append({"material": material, "required": False, "safe_note": response["safe_note"], "reason": "callback_material_not_required"})
    return accepted, missing, rejected


def _intake_status(
    callback_issue: str,
    trace_issue: str,
    diagnostics_issue: str,
    materials_issue: str,
    callback_status: dict[str, Any],
    trace_status: dict[str, Any],
    diagnostics_status: dict[str, Any],
    same_ref: dict[str, Any],
    same_ref_required: Any,
    unsafe: bool,
    parse_issues: list[str],
    missing: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
) -> str:
    # fail-closed 顺序固定：输入可信性、安全、同 ref，再处理材料缺口。
    bad_json_issues = {"callback_json_bad_json", "callback_json_read_error", "callback_json_not_object", "trace_summary_json_bad_json", "trace_summary_json_read_error", "trace_summary_json_not_object", "diagnostics_summary_json_bad_json", "diagnostics_summary_json_read_error", "diagnostics_summary_json_not_object", "required_materials_json_bad_json", "required_materials_json_read_error", "required_materials_json_not_object"}
    if callback_issue in bad_json_issues or trace_issue in bad_json_issues or diagnostics_issue in bad_json_issues or materials_issue in bad_json_issues:
        return "blocked_unsupported_or_bad_json_not_proven"
    if callback_issue:
        return "blocked_missing_callback_packet_not_proven"
    if trace_issue:
        return "blocked_missing_trace_summary_not_proven"
    if diagnostics_issue:
        return "blocked_missing_diagnostics_summary_not_proven"
    if callback_status["schema_status"] != "supported" or callback_status["field_status"] != "supported":
        return "blocked_unsupported_callback_packet_not_proven"
    if trace_status["schema_status"] != "supported" or diagnostics_status["schema_status"] != "supported":
        return "blocked_unsupported_trace_or_diagnostics_summary_not_proven"
    if same_ref["status"] != "matched" or same_ref_required is not True:
        return "blocked_evidence_ref_mismatch_not_proven"
    if unsafe:
        return "blocked_unsafe_callback_or_summary_copy_not_proven"
    if parse_issues:
        return "blocked_unsupported_callback_packet_not_proven"
    if missing or rejected:
        return "needs_route_elevator_material_backfill_not_proven"
    return "callback_packet_intake_ready_for_review_not_proven"


def _owner_handoff(status: str, missing: list[dict[str, Any]], rejected: list[dict[str, Any]], evidence_ref: str) -> list[str]:
    # handoff 只说明下一步材料回填，不授权任何 robot action。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "callback_packet_intake_ready_for_review_not_proven":
        return [
            f"Autonomy owner reviews sanitized callback packet intake for evidence_ref={ref}.",
            "Product/Robot reviewers keep field closeout blocked until real materials are reviewed.",
        ]
    if missing:
        return [f"Backfill missing route/elevator materials under evidence_ref={ref}: {', '.join(item['material'] for item in missing[:12])}."]
    if rejected:
        return [f"Repair rejected route/elevator callback materials under evidence_ref={ref}: {', '.join(item['material'] for item in rejected[:12])}."]
    return ["Regenerate callback packet, trace summary, diagnostics summary, and required materials with one safe evidence_ref."]


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只涉及 PC evidence gate，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/elevator_field_evidence_trace_callback_intake.py --callback-json <safe_callback_packet.json> --trace-summary-json <elevator_action_feedback_trace_summary.json> --diagnostics-summary-json <diagnostics_summary.json> --required-materials-json <required_materials.json> --evidence-ref {ref}",
        "keep source=software_proof, overall_status=not_proven, delivery_success=false, primary_actions_enabled=false",
    ]


def _safe_copy(
    status: str,
    evidence_ref: str,
    accepted: list[dict[str, Any]],
    missing: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    owner_handoff: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 首选消费面，不包含 raw callback 或完整上游 JSON。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "intake_status": status,
        "source": "software_proof",
        "overall_status": "not_proven",
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "accepted_callback_materials": accepted,
        "missing_required_materials": missing,
        "rejected_callback_materials": rejected,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "same_evidence_ref_required": True,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_elevator_field_evidence_trace_callback_intake(
    callback_json: str,
    trace_summary_json: str,
    diagnostics_summary_json: str,
    required_materials_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 callback/trace/diagnostics/material metadata，生成 fail-closed intake。"""
    callback_payload, callback_issue, callback_style = _load_json(callback_json, "callback_json")
    trace_payload, trace_issue, trace_style = _load_json(trace_summary_json, "trace_summary_json")
    diagnostics_payload, diagnostics_issue, diagnostics_style = _load_json(diagnostics_summary_json, "diagnostics_summary_json")
    materials_payload, materials_issue, materials_style = _load_json(required_materials_json, "required_materials_json", required=False)

    trace_keys = ("elevator_action_feedback_trace", "robot_diagnostics_elevator_action_feedback_trace_summary", "summary", "artifact", "payload", "data", "safe_copy")
    diagnostics_keys = ("robot_diagnostics_elevator_action_feedback_trace_summary", "elevator_action_feedback_trace", "summary", "artifact", "payload", "data", "safe_copy")
    materials_keys = ("required_route_elevator_materials_summary", "elevator_field_evidence_trace_required_materials", "summary", "payload", "data", "safe_copy")

    callback = _find_callback(callback_payload) if callback_payload else {}
    trace = _find_by_schema(trace_payload, TRACE_SCHEMAS, trace_keys) if trace_payload else {}
    diagnostics = _find_by_schema(diagnostics_payload, DIAGNOSTICS_SCHEMAS, diagnostics_keys) if diagnostics_payload else {}
    materials_source = _find_by_schema(materials_payload, MATERIAL_SCHEMAS, materials_keys) if materials_payload else {}

    callback_status = _callback_status(callback_issue, callback, callback_style)
    trace_status = _source_status(trace_issue, trace, TRACE_SCHEMAS, "elevator_action_feedback_trace", trace_style)
    diagnostics_status = _source_status(diagnostics_issue, diagnostics, DIAGNOSTICS_SCHEMAS, "robot_diagnostics_elevator_action_feedback_trace_summary", diagnostics_style)

    requested_ref = _safe_ref(evidence_ref)
    refs = {
        "requested": requested_ref,
        "callback": _source_ref(callback),
        "trace": _source_ref(trace),
        "diagnostics": _source_ref(diagnostics),
        "materials": _source_ref(materials_source),
    }
    effective_ref = requested_ref or refs["callback"] or refs["trace"] or refs["diagnostics"] or refs["materials"]
    same_ref = _same_ref_match(refs)
    same_ref_required = _same_ref_required(callback, trace, diagnostics, materials_source)
    required_materials = _required_materials(materials_source, trace, diagnostics, callback)
    responses, parse_issues = _parse_material_responses(callback)
    accepted, missing, rejected = _merge_materials(required_materials, responses)
    unsafe = bool(callback_payload or trace_payload or diagnostics_payload or materials_payload) and (
        _unsafe_copy(callback) or _unsafe_copy(trace) or _unsafe_copy(diagnostics) or _unsafe_copy(materials_source)
    )

    status = _intake_status(
        callback_issue,
        trace_issue,
        diagnostics_issue,
        materials_issue,
        callback_status,
        trace_status,
        diagnostics_status,
        same_ref,
        same_ref_required,
        unsafe,
        parse_issues,
        missing,
        rejected,
    )
    owner_handoff = _safe_value(_owner_handoff(status, missing, rejected, effective_ref))
    rerun_commands = _safe_value(_rerun_commands(effective_ref))
    safe_copy = _safe_copy(status, effective_ref, accepted, missing, rejected, owner_handoff, rerun_commands)

    source_trace = {
        **trace_status,
        "source_schema": _safe_text(trace.get("schema", "")),
        "trace_status": _safe_text(_first_text(trace.get("status"), trace.get("overall_status"), default="")),
        "safe_evidence_ref": refs["trace"],
    }
    source_diagnostics = {
        **diagnostics_status,
        "alias": "robot_diagnostics_elevator_action_feedback_trace_summary",
        "source_schema": _safe_text(diagnostics.get("schema", "")),
        "summary_status": _safe_text(_first_text(diagnostics.get("overall_status"), diagnostics.get("status"), default="")),
        "safe_evidence_ref": refs["diagnostics"],
    }
    callback_packet = {
        **callback_status,
        "packet_status": "callback_packet_metadata_received_not_proven" if not callback_issue else "callback_packet_missing_not_proven",
        "redaction_status": "blocked" if callback_status.get("unsafe_copy") else "redacted",
        "owner_acknowledgement": _safe_text(_first_text(callback.get("owner_acknowledgement"), default="field_owner_acknowledges_real_materials_still_required")),
        "safe_evidence_ref": refs["callback"],
        "parse_issues": parse_issues,
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "overall_status": "not_proven",
        "status": status,
        "intake_status": status,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref,
        "source_trace": source_trace,
        "source_diagnostics": source_diagnostics,
        "callback_packet": callback_packet,
        "required_route_elevator_materials": required_materials,
        "accepted_callback_materials": _safe_value(accepted),
        "missing_required_materials": _safe_value(missing),
        "rejected_callback_materials": _safe_value(rejected),
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "overall_status": "not_proven",
        "status": status,
        "intake_status": status,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref,
        "source_trace": source_trace,
        "source_diagnostics": source_diagnostics,
        "callback_packet": callback_packet,
        "required_route_elevator_materials": required_materials,
        "accepted_callback_materials": _safe_value(accepted),
        "missing_required_materials": _safe_value(missing),
        "rejected_callback_materials": _safe_value(rejected),
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "elevator_field_evidence_trace_callback_intake_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_dir_scan",
            "raw_callback_body",
            "ros_graph",
            "real_nav2_runtime",
            "real_fixed_route_runtime",
            "real_route_elevator_field_pass",
            "hardware_transport",
            "hardware_feedback",
            "external_cloud",
            "real_phone_or_browser",
        ],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _unsafe_copy(summary):
        # 最终输出仍不安全时，状态强制降级；flags 保持 false。
        artifact["status"] = "blocked_unsafe_callback_or_summary_copy_not_proven"
        artifact["intake_status"] = "blocked_unsafe_callback_or_summary_copy_not_proven"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_callback_or_summary_copy_not_proven"
        artifact["robot_diagnostics_summary"]["intake_status"] = "blocked_unsafe_callback_or_summary_copy_not_proven"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_callback_or_summary_copy_not_proven"
        artifact["mobile_readonly_summary"]["intake_status"] = "blocked_unsafe_callback_or_summary_copy_not_proven"
        summary["status"] = "blocked_unsafe_callback_or_summary_copy_not_proven"
        summary["intake_status"] = "blocked_unsafe_callback_or_summary_copy_not_proven"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 只在用户显式传 output 时写文件，默认 stdout 便于 CI/automation 捕获。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只依赖标准库，适配 macOS PC 和 Docker 本地验证。
    parser = argparse.ArgumentParser(description="Generate elevator field evidence trace callback intake artifact")
    parser.add_argument("--callback-json", required=True, help="safe callback packet JSON, file:<path>, or env:<VAR>")
    parser.add_argument("--trace-summary-json", required=True, help="elevator_action_feedback_trace summary JSON, file:<path>, or env:<VAR>")
    parser.add_argument("--diagnostics-summary-json", required=True, help="Robot diagnostics trace summary JSON, file:<path>, or env:<VAR>")
    parser.add_argument("--required-materials-json", default="", help="optional required route/elevator materials JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref")
    parser.add_argument("--output", default="", help="optional artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional sanitized summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_elevator_field_evidence_trace_callback_intake(
        args.callback_json,
        args.trace_summary_json,
        args.diagnostics_summary_json,
        args.required_materials_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"elevator_field_evidence_trace_callback_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"elevator_field_evidence_trace_callback_intake_summary_file:{_safe_ref(args.summary_output)}")
        print(f"elevator_field_evidence_trace_callback_intake_status:{artifact['status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
