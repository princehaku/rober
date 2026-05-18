#!/usr/bin/env python3
"""生成 elevator field evidence trace material backfill intake artifact。

该 PC-only gate 只读取上一轮 callback review handoff 的 artifact/summary，
以及现场 owner 提供的安全材料引用包。它校验同一 safe evidence_ref、
required materials、安全 copy 和 not_proven 边界；不读取真实材料文件、
不访问 ROS/Nav2、硬件、云或真实手机/browser，也不证明真实送达成功。
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_SCHEMA = "trashbot.elevator_field_evidence_trace_material_backfill_intake.v1"
SUMMARY_SCHEMA = "trashbot.elevator_field_evidence_trace_material_backfill_intake_summary.v1"
SOURCE_ARTIFACT_SCHEMA = "trashbot.elevator_field_evidence_trace_callback_review_handoff.v1"
SOURCE_SUMMARY_SCHEMA = "trashbot.elevator_field_evidence_trace_callback_review_handoff_summary.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_elevator_field_evidence_trace_material_backfill_intake_gate"
SOURCE_BOUNDARY = "software_proof_docker_elevator_field_evidence_trace_callback_review_handoff_gate"

# 这些 literal 同时服务 rg 围栏和下游 Robot/mobile 白名单消费。
BOUNDARY_NOTE = (
    "elevator_field_evidence_trace_material_backfill_intake; "
    "elevator_field_evidence_trace_callback_review_handoff; safe_evidence_ref; "
    "same_evidence_ref_required; source=software_proof; not_proven; "
    "delivery_success=false; primary_actions_enabled=false; "
    "needs_required_material_backfill_not_proven; ready_for_material_review_not_proven; "
    "real_elevator_door_state; real_delivery_result"
)

# required materials 是后续真实现场复核的类别清单，本 gate 只验证安全引用是否齐全。
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

# not_proven 固定写入 artifact/summary，防止 ready 状态被误解释成现场闭环完成。
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

SOURCE_SCHEMAS = {SOURCE_ARTIFACT_SCHEMA, SOURCE_SUMMARY_SCHEMA}
SUPPORTED_HANDOFF_STATUSES = {
    "ready_for_owner_material_backfill_not_proven",
    "ready_for_field_execution_owner_handoff_not_proven",
}

# operator material packet 可以没有 schema，但有 schema 时必须是 safe refs only。
MATERIAL_PACKET_SCHEMAS = {
    "",
    "trashbot.elevator_field_evidence_trace_material_backfill_packet.v1",
    "trashbot.elevator_field_evidence_trace_material_backfill_packet_summary.v1",
    ARTIFACT_SCHEMA,
    SUMMARY_SCHEMA,
}

# 外部材料包只允许这些安全字段，避免 raw artifact 或完整现场日志被复制进 summary。
MATERIAL_PACKET_ALLOWED_FIELDS = {
    "schema",
    "schema_version",
    "source",
    "overall_status",
    "status",
    "packet_status",
    "safe_evidence_ref",
    "evidence_ref",
    "same_evidence_ref_required",
    "same_evidence_ref_status",
    "provided_material_refs",
    "accepted_material_refs",
    "received_material_refs",
    "missing_required_materials",
    "missing_materials",
    "rejected_material_refs",
    "rejected_materials",
    "material_refs",
    "materials",
    "safe_copy",
    "redaction_status",
    "owner_acknowledgement",
    "next_required_evidence",
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
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action)\b"),
)

RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

PLACEHOLDER_PATTERNS = (
    re.compile(r"(?i)\b(todo|tbd|placeholder|sample|example|dummy|fake|null|none)\b"),
    re.compile(r"^<[^>]+>$"),
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
    # UTC 便于 PC/Docker 主机之间按字符串排序 evidence artifact。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本统一脱敏，blocked 分支也不回显危险原文。
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
    # 递归脱敏是最终防线；不能替代前置 unsafe fail-closed 判定。
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
    return any(token in encoded for token in FORBIDDEN_COPY) or any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(value: Any) -> bool:
    # 布尔字段和自然语言都检查，防止 field pass 或动作授权语义穿透。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _unsafe_copy(value: Any) -> bool:
    # 对外 summary 只允许 phone-safe metadata，不允许 raw/control/hardware/success copy。
    return _has_forbidden_copy(value) or _has_success_or_control_claim(value)


def _resolve_source_path(source: str) -> tuple[str, str]:
    # 支持 file:/env:，但 source path 不会进入 summary。
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


def _load_json(source: str, label: str) -> tuple[dict[str, Any], str, str]:
    # 缺输入、坏 JSON、非 object 都转成可落盘 artifact，不抛异常中断自动化。
    path, source_style = _resolve_source_path(source)
    if not path:
        return {}, f"{label}_not_provided", source_style
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


def _source_candidates(payload: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    # 只递归白名单 wrapper，避免 raw payload 被误采信。
    candidates = [payload]
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value, keys))
    return candidates


def _find_handoff(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择上一轮 handoff schema；否则保留顶层用于 unsupported 诊断。
    keys = (
        "elevator_field_evidence_trace_callback_review_handoff",
        "elevator_field_evidence_trace_callback_review_handoff_summary",
        "robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    )
    for candidate in _source_candidates(payload, keys):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _find_material_packet(payload: dict[str, Any]) -> dict[str, Any]:
    # 无 schema packet 也允许，但必须含材料引用字段且不能带未知字段。
    keys = (
        "operator_material_packet",
        "material_backfill_packet",
        "material_packet",
        "materials_packet",
        "safe_material_packet",
        "safe_copy",
        "summary",
        "payload",
        "data",
    )
    for candidate in _source_candidates(payload, keys):
        if set(candidate.keys()) & MATERIAL_PACKET_ALLOWED_FIELDS:
            return candidate
    return payload


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


def _same_ref_match(refs: dict[str, str], same_ref_required: Any) -> dict[str, Any]:
    # same evidence_ref 是现场材料复账主键；所有显式 ref 必须一致且非空。
    expected = next((ref for ref in refs.values() if ref), "")
    mismatches = sorted({ref for ref in refs.values() if ref and expected and ref != expected})
    missing = sorted(key for key, ref in refs.items() if key in {"handoff", "operator_material_packet"} and not ref)
    if same_ref_required is not True:
        status = "weak_same_evidence_ref_required"
    elif not expected or missing:
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
        "same_evidence_ref_required": same_ref_required,
    }


def _handoff_status(handoff: dict[str, Any]) -> str:
    # handoff_status 是上游主状态；status 只用于兼容 summary。
    safe_copy = _dict(handoff, "safe_copy")
    return _safe_text(_first_text(handoff.get("handoff_status"), handoff.get("status"), safe_copy.get("handoff_status"), safe_copy.get("status"), default=""))


def _handoff_supported(issue: str, handoff: dict[str, Any]) -> dict[str, Any]:
    # 上一轮 handoff 必须保持 software_proof、not_proven、false flags 和正确 boundary。
    if issue:
        return {"load_status": "blocked", "load_issue": issue, "schema_status": "not_loaded", "safe_evidence_ref": ""}
    schema = _safe_text(handoff.get("schema", "")).strip()
    boundary = _safe_text(_first_text(handoff.get("evidence_boundary"), handoff.get("boundary"), default="")).strip()
    source = _safe_text(_first_text(handoff.get("source"), default="")).strip()
    overall = _safe_text(_first_text(handoff.get("overall_status"), handoff.get("status"), default="")).strip()
    status = _handoff_status(handoff)
    supported = (
        schema in SOURCE_SCHEMAS
        and boundary == SOURCE_BOUNDARY
        and (source == "software_proof" or source.startswith("software_proof"))
        and (overall == "not_proven" or overall.endswith("_not_proven"))
        and status in SUPPORTED_HANDOFF_STATUSES
        and handoff.get("delivery_success") is False
        and handoff.get("primary_actions_enabled") is False
    )
    return {
        "load_status": "loaded",
        "load_issue": "",
        "schema_status": "supported" if supported else "unsupported",
        "schema": schema,
        "evidence_boundary": boundary,
        "source": source,
        "overall_status": overall,
        "handoff_status": status,
        "safe_evidence_ref": _source_ref(handoff),
        "unsafe_copy": bool(_unsafe_copy(handoff)) if handoff else False,
    }


def _packet_status(issue: str, packet: dict[str, Any], source_style: str) -> dict[str, Any]:
    # material packet 是 operator 入口；未知字段或弱边界都不能默认透传。
    if issue:
        return {"load_status": "blocked", "load_issue": issue, "schema_status": "not_loaded", "field_status": "not_loaded", "source_style": source_style}
    schema = _safe_text(packet.get("schema", "")).strip()
    source = _safe_text(_first_text(packet.get("source"), packet.get("evidence_boundary"), default="")).strip()
    overall = _safe_text(_first_text(packet.get("overall_status"), packet.get("status"), default="")).strip()
    unknown = sorted(set(packet.keys()) - MATERIAL_PACKET_ALLOWED_FIELDS)
    schema_ok = schema in MATERIAL_PACKET_SCHEMAS
    source_ok = source in {"", "software_proof"} or source.startswith("software_proof")
    overall_ok = overall in {"", "not_proven", "safe_refs_only"} or overall.endswith("_not_proven")
    return {
        "load_status": "loaded",
        "load_issue": "",
        "schema_status": "supported" if schema_ok and source_ok and overall_ok else "unsupported",
        "field_status": "supported" if not unknown else "unsupported_fields",
        "unsupported_fields": unknown,
        "source_style": source_style,
        "schema": schema,
        "packet_status": _safe_text(_first_text(packet.get("packet_status"), packet.get("status"), default="safe_refs_only")),
        "safe_evidence_ref": _source_ref(packet),
        "unsafe_copy": bool(_unsafe_copy(packet)) if packet else False,
    }


def _material_name(value: Any) -> str:
    # 材料主键兼容字符串和 object，避免现场表单格式稍有差异就失效。
    if isinstance(value, dict):
        return _safe_text(_first_text(value.get("material"), value.get("name"), value.get("category"), default="")).strip()
    return _safe_text(value).strip()


def _material_ref(value: Any) -> str:
    # 材料 ref 只允许安全摘要 token，不允许本机路径、原始 URL credential 或占位符。
    if isinstance(value, dict):
        ref = _first_text(value.get("safe_ref"), value.get("ref"), value.get("file_ref"), value.get("evidence_ref"), value.get("safe_note"), default="")
    else:
        ref = value
    return _safe_text(ref).strip()


def _is_placeholder_ref(value: str) -> bool:
    # 占位 ref 不能被当作真实材料引用齐全。
    text = value.strip()
    return not text or any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS)


def _packet_material_entries(packet: dict[str, Any]) -> list[dict[str, Any]]:
    # 支持 list/dict 两种安全材料引用包，但只抽取材料类别和安全 ref。
    entries: list[dict[str, Any]] = []
    for field in ("provided_material_refs", "accepted_material_refs", "received_material_refs", "materials"):
        raw = packet.get(field)
        if not isinstance(raw, list):
            continue
        for item in raw[:64]:
            name = _material_name(item)
            ref = _material_ref(item)
            if isinstance(item, str):
                ref = item
            if name:
                entries.append({"material": name, "safe_ref": _safe_text(ref or name), "source_field": field})
    raw_refs = packet.get("material_refs")
    if isinstance(raw_refs, dict):
        for name, ref in list(raw_refs.items())[:64]:
            entries.append({"material": _safe_text(name), "safe_ref": _material_ref(ref), "source_field": "material_refs"})
    return entries


def _required_materials(handoff: dict[str, Any]) -> list[str]:
    # required list 可以由 handoff 扩展，但基础八类必须保留。
    materials: list[str] = []
    for candidate in _source_candidates(
        handoff,
        ("source_review_decision", "safe_copy", "summary", "robot_diagnostics_summary", "mobile_readonly_summary"),
    ):
        raw = candidate.get("required_route_elevator_materials") or candidate.get("required_materials")
        if not isinstance(raw, list):
            continue
        for item in raw[:64]:
            name = _material_name(item)
            if name and name not in materials:
                materials.append(name)
    for material in REQUIRED_ROUTE_ELEVATOR_MATERIALS:
        if material not in materials:
            materials.append(material)
    return materials


def _blocked_materials(packet: dict[str, Any], *fields: str) -> set[str]:
    # operator 明示 missing/rejected 的材料不能进入 accepted。
    blocked: set[str] = set()
    for field in fields:
        raw = packet.get(field)
        if not isinstance(raw, list):
            continue
        for item in raw[:64]:
            name = _material_name(item)
            if name:
                blocked.add(name)
    return blocked


def _merge_materials(required: list[str], packet: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    # 这里只判断“安全引用是否齐全”，不打开或评价真实材料内容。
    provided: dict[str, dict[str, Any]] = {}
    for entry in _packet_material_entries(packet):
        name = entry["material"]
        if name not in provided:
            provided[name] = entry
    blocked = _blocked_materials(packet, "missing_required_materials", "missing_materials", "rejected_material_refs", "rejected_materials")
    accepted: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for material in required:
        entry = provided.get(material)
        if material in blocked:
            rejected.append({"material": material, "required": True, "reason": "operator_packet_marked_missing_or_rejected"})
        elif not entry:
            missing.append({"material": material, "required": True, "reason": "operator_packet_ref_missing"})
        elif _is_placeholder_ref(entry.get("safe_ref", "")):
            missing.append({"material": material, "required": True, "reason": "operator_packet_ref_placeholder"})
        else:
            accepted.append({"material": material, "safe_ref": entry["safe_ref"], "required": True})
    for material, entry in provided.items():
        if material not in required:
            rejected.append({"material": material, "safe_ref": entry.get("safe_ref", ""), "required": False, "reason": "operator_packet_material_not_required"})
    return accepted, missing, rejected


def _intake_status(
    handoff_issue: str,
    packet_issue: str,
    handoff_status: dict[str, Any],
    packet_status: dict[str, Any],
    same_ref: dict[str, Any],
    unsafe: bool,
    missing: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
) -> str:
    # fail-closed 顺序固定：可读性、契约、安全、同 ref，再处理材料缺口。
    if handoff_issue:
        return "blocked_missing_handoff_not_proven"
    if handoff_status["schema_status"] != "supported":
        return "blocked_unsupported_handoff_not_proven"
    if packet_issue:
        return "blocked_missing_material_packet_not_proven"
    if packet_status["schema_status"] != "supported" or packet_status["field_status"] != "supported":
        return "blocked_unsupported_handoff_not_proven"
    if unsafe:
        return "blocked_unsafe_material_ref_not_proven"
    if same_ref["status"] != "matched":
        return "blocked_evidence_ref_mismatch_not_proven"
    if missing or rejected:
        return "needs_required_material_backfill_not_proven"
    return "ready_for_material_review_not_proven"


def _next_required_evidence(status: str, evidence_ref: str, missing: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> list[str]:
    # 下一步只描述复核/补齐动作，不授权 Robot/mobile 控制动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_material_review_not_proven":
        return [f"same_evidence_ref_material_review:{ref}", "Keep software_proof/not_proven until real materials are reviewed."]
    if status == "needs_required_material_backfill_not_proven":
        names = [item["material"] for item in (missing or rejected)] or list(REQUIRED_ROUTE_ELEVATOR_MATERIALS)
        return [f"same_evidence_ref_missing_material_backfill_then_review:{ref}:{','.join(names[:12])}"]
    if status == "blocked_evidence_ref_mismatch_not_proven":
        return [f"rerun_material_backfill_with_same_safe_evidence_ref:{ref}"]
    if status == "blocked_unsafe_material_ref_not_proven":
        return ["regenerate_material_packet_without_raw_paths_credentials_topics_transport_checksums_or_success_claims"]
    return [f"provide_supported_callback_review_handoff_and_safe_material_packet:{ref}"]


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只包含 PC evidence gates，不包含 ROS、Nav2、硬件、云或手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/elevator_field_evidence_trace_material_backfill_intake.py --handoff-json <callback_review_handoff_summary.json> --material-packet-json <safe_material_packet.json> --evidence-ref {ref} --once-json",
        "keep source=software_proof, overall_status=not_proven, delivery_success=false, primary_actions_enabled=false",
    ]


def _safe_copy(
    status: str,
    evidence_ref: str,
    accepted: list[dict[str, Any]],
    missing: list[dict[str, Any]],
    next_required: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 首选消费面，不包含 raw material packet 或完整 handoff。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "intake_status": status,
        "source": "software_proof",
        "overall_status": "not_proven",
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "accepted_material_refs": accepted,
        "missing_required_materials": missing,
        "next_required_evidence": next_required,
        "same_evidence_ref_required": True,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_elevator_field_evidence_trace_material_backfill_intake(
    handoff_json: str,
    material_packet_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 handoff/material packet，生成 metadata-only material backfill intake。"""
    handoff_payload, handoff_issue, handoff_style = _load_json(handoff_json, "handoff_json")
    packet_payload, packet_issue, packet_style = _load_json(material_packet_json, "material_packet_json")
    handoff = _find_handoff(handoff_payload) if handoff_payload else {}
    packet = _find_material_packet(packet_payload) if packet_payload else {}
    handoff_summary = _handoff_supported(handoff_issue, handoff)
    packet_summary = _packet_status(packet_issue, packet, packet_style)

    requested_ref = _safe_ref(evidence_ref)
    refs = {
        "requested": requested_ref,
        "handoff": _source_ref(handoff),
        "operator_material_packet": _source_ref(packet),
    }
    effective_ref = requested_ref or refs["handoff"] or refs["operator_material_packet"]
    same_ref_required = _same_ref_required(handoff, packet)
    same_ref = _same_ref_match(refs, same_ref_required)
    required_materials = _required_materials(handoff)
    accepted, missing, rejected = _merge_materials(required_materials, packet)
    unsafe = bool(handoff_payload or packet_payload) and (_unsafe_copy(handoff) or _unsafe_copy(packet))
    status = _intake_status(handoff_issue, packet_issue, handoff_summary, packet_summary, same_ref, unsafe, missing, rejected)
    next_required = _safe_value(_next_required_evidence(status, effective_ref, missing, rejected))
    rerun_commands = _safe_value(_rerun_commands(effective_ref))
    safe_copy = _safe_copy(status, effective_ref, _safe_value(accepted), _safe_value(missing), next_required)

    source_handoff = {
        **handoff_summary,
        "source_style": handoff_style,
        "schema": _safe_text(handoff.get("schema", "")),
        "handoff_status": _handoff_status(handoff),
        "safe_evidence_ref": refs["handoff"],
    }
    operator_material_packet = {
        **packet_summary,
        "packet_status": packet_summary.get("packet_status", "safe_refs_only"),
        "safe_evidence_ref": refs["operator_material_packet"],
        "provided_material_refs": [item["material"] for item in accepted],
        "rejected_material_refs": _safe_value(rejected),
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
        "source_handoff": source_handoff,
        "operator_material_packet": operator_material_packet,
        "required_materials": required_materials,
        "required_route_elevator_materials": required_materials,
        "accepted_material_refs": _safe_value(accepted),
        "missing_required_materials": _safe_value(missing),
        "rejected_material_refs": _safe_value(rejected),
        "next_required_evidence": next_required,
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
        "source_handoff": source_handoff,
        "operator_material_packet": operator_material_packet,
        "required_materials": required_materials,
        "required_route_elevator_materials": required_materials,
        "accepted_material_refs": _safe_value(accepted),
        "missing_required_materials": _safe_value(missing),
        "rejected_material_refs": _safe_value(rejected),
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "elevator_field_evidence_trace_material_backfill_intake_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_dir_scan",
            "raw_material_body",
            "raw_callback_handoff_body",
            "ros_graph",
            "real_nav2_runtime",
            "real_fixed_route_runtime",
            "real_route_elevator_field_pass",
            "hardware_transport",
            "hardware_feedback",
            "external_cloud",
            "real_phone_or_browser",
            "robot_action",
        ],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _unsafe_copy(summary):
        # 最终输出若仍不安全，强制降级，但 flags 继续保持 false。
        status = "blocked_unsafe_material_ref_not_proven"
        for target in (artifact, summary):
            target["status"] = status
            target["intake_status"] = status
        artifact["elevator_field_evidence_trace_material_backfill_intake_summary"] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 空 output 表示只打印 stdout；指定路径时自动建目录用于证据归档。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，便于 macOS PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate elevator field evidence trace material backfill intake artifact")
    parser.add_argument("--handoff-json", required=True, help="callback review handoff artifact, summary, wrapper/nested JSON, file:<path>, or env:<VAR>")
    parser.add_argument("--material-packet-json", required=True, help="operator safe material packet/file refs JSON, file:<path>, or env:<VAR>")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this material backfill intake")
    parser.add_argument("--output", default="", help="optional material backfill intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional sanitized summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_elevator_field_evidence_trace_material_backfill_intake(
        args.handoff_json,
        args.material_packet_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"elevator_field_evidence_trace_material_backfill_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"elevator_field_evidence_trace_material_backfill_intake_summary_file:{_safe_ref(args.summary_output)}")
        print(f"elevator_field_evidence_trace_material_backfill_intake_status:{artifact['status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
