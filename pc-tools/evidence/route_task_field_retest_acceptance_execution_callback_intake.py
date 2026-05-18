#!/usr/bin/env python3
"""生成 route/task field retest acceptance execution callback intake artifact。

该 gate 只消费 acceptance execution pack 的 artifact、summary、wrapper/nested
JSON，或 file/env 风格 source，以及现场同学回传的 safe callback packet。它把
现场回执复账成 callback intake artifact/summary，供 Robot diagnostics 与
mobile/web 只读消费；它不读取真实材料目录、不访问 ROS graph、Nav2 runtime、
硬件、真实电梯、外部云或真实手机/browser。
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_acceptance_execution_pack as pack


CALLBACK_INTAKE_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_callback_intake.v1"
CALLBACK_INTAKE_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_callback_intake_summary.v1"
SCHEMA_VERSION = 1
CALLBACK_INTAKE_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate"

# callback intake 只能承接上一轮 acceptance execution pack，不能跳过执行包直接吃 review decision。
SOURCE_SCHEMAS = {pack.PACK_SCHEMA, pack.PACK_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {pack.PACK_BOUNDARY}
READY_EXECUTION_PACK_STATUS = "ready_for_field_retest_acceptance_execution_pack_not_proven"

# callback packet 可以先无 schema，便于现场安全表单和 PC fixture 先落地。
CALLBACK_PACKET_SCHEMAS = {
    "",
    "trashbot.route_task_field_retest_acceptance_execution_callback_packet.v1",
    "trashbot.route_task_field_retest_acceptance_execution_callback_packet_summary.v1",
}
CALLBACK_PACKET_BOUNDARIES = {"", CALLBACK_INTAKE_BOUNDARY, pack.PACK_BOUNDARY}

# safe callback packet 字段白名单是本 gate 的安全边界，新增字段必须补测试。
CALLBACK_ALLOWED_FIELDS = {
    "schema",
    "schema_version",
    "evidence_boundary",
    "boundary",
    "evidence_ref",
    "safe_evidence_ref",
    "same_evidence_ref_required",
    "status",
    "callback_status",
    "material_responses",
    "received_materials",
    "missing_materials",
    "rejected_materials",
    "required_route_elevator_materials",
    "owner_next_steps",
    "next_required_evidence",
    "safe_copy",
    "delivery_success",
    "primary_actions_enabled",
}

REQUIRED_ROUTE_ELEVATOR_MATERIALS = list(pack.REQUIRED_ROUTE_ELEVATOR_MATERIALS) + ["diagnostics_mobile_safe_summary"]
NOT_PROVEN = list(pack.NOT_PROVEN)

# rg 围栏依赖这些 literal，人工复盘也能快速识别本 gate 边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_acceptance_execution_callback_intake; "
    "software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# callback 入口不允许携带底层工程细节、凭证、raw artifact 或真实通过措辞。
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

# 本地回执入口不能出现真实通过或动作放行措辞。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bcancel\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action)\b"),
)

# 绝对路径会泄漏 host 结构，也会诱导下游读取真实材料目录。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# 输出前统一脱敏；blocked artifact 也不能回显敏感输入。
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
    # UTC 让 PC/Docker 产物可以跨机器按时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，防止 callback note 带入敏感材料。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 若被误填成路径，只保留 basename，避免泄漏本机目录。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 最终 payload 递归脱敏，避免新增嵌套字段绕过 helper。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _encoded(value: Any) -> str:
    # 安全扫描覆盖键和值；不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 禁词在脱敏前检查，命中后直接 blocked，不做“清洗后 ready”。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_raw_path_copy(value: Any) -> bool:
    # callback intake 不读取真实材料目录；绝对路径 copy 一律视为不安全。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(value: Any) -> bool:
    # 顶层布尔和自由文案都检查，防止成功语义穿透到下游。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _unsafe_callback_copy(value: Any) -> bool:
    # callback 是外部回填入口，危险 copy 不允许降级成普通 note。
    return _has_forbidden_copy(value) or _has_raw_path_copy(value) or _has_success_or_control_claim(value)


def _unsafe_execution_pack_copy(value: Any) -> bool:
    # execution pack 自带 non_access_scope，不能因边界说明误判；这里只拦成功、路径和凭证。
    return _has_raw_path_copy(value) or _has_success_or_control_claim(value)


def _resolve_source_path(source: str) -> tuple[str, str]:
    # file:/env: 只解决“从哪里读 JSON”，不把来源本身写入 safe summary。
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
    # 缺输入、坏 JSON、非 object 都输出 blocked shape，方便自动化复盘。
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
    # 只接受 object 嵌套字段，字符串 wrapper 不能伪装可信 JSON。
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
    # 上游 list 只保留安全值并限制数量，避免复制完整 raw artifact。
    if isinstance(value, list):
        return _safe_value(value[:limit])
    if value in (None, ""):
        return []
    return [_safe_value(value)]


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免任意 raw payload 被当成 execution pack。
    candidates = [payload]
    for key in (
        "route_task_field_retest_acceptance_execution_pack",
        "route_task_field_retest_acceptance_execution_pack_summary",
        "route_task_field_retest_acceptance_execution_callback_intake",
        "route_task_field_retest_acceptance_execution_callback_intake_summary",
        "source_execution_pack",
        "execution_pack",
        "execution_pack_summary",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_execution_pack_source(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中时优先返回嵌套对象；否则保留顶层用于 unsupported 诊断。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _callback_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # callback wrapper 常见于现场表单导出，仍只取白名单嵌套对象。
    candidates = [payload]
    for key in (
        "route_task_field_retest_acceptance_execution_callback_packet",
        "route_task_field_retest_acceptance_execution_callback_packet_summary",
        "route_task_field_retest_acceptance_execution_callback_intake",
        "field_callback",
        "safe_callback_packet",
        "sanitized_callback",
        "callback",
        "packet",
        "safe_copy",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_callback_candidates(value))
    return candidates


def _find_callback_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 有 schema 的 callback 优先；无 schema 的顶层 sanitized object 也允许。
    for candidate in _callback_candidates(payload):
        callback_fields = set(candidate.keys()) & CALLBACK_ALLOWED_FIELDS
        if str(candidate.get("schema", "")).strip() in CALLBACK_PACKET_SCHEMAS and callback_fields:
            return candidate
    return payload


def _execution_pack_status(load_issue: str, source: dict[str, Any]) -> dict[str, Any]:
    # source schema 与 boundary 必须同时白名单化，防止跨 gate artifact 被误用。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = _safe_text(source.get("schema", "")).strip()
    boundary = _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _callback_status(load_issue: str, callback: dict[str, Any]) -> dict[str, Any]:
    # callback schema 可为空，但未知 schema、boundary 或字段必须阻断。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded", "field_status": "not_loaded"}
    schema = _safe_text(callback.get("schema", "")).strip()
    boundary = _safe_text(_first_text(callback.get("evidence_boundary"), callback.get("boundary"), default="")).strip()
    if schema not in CALLBACK_PACKET_SCHEMAS or boundary not in CALLBACK_PACKET_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported", "field_status": "not_checked"}
    unknown = sorted(set(callback.keys()) - CALLBACK_ALLOWED_FIELDS)
    if unknown:
        return {
            "load_status": "loaded",
            "load_issue": "",
            "schema_status": "supported",
            "field_status": "unsupported_fields",
            "unsupported_fields": unknown,
        }
    return {"load_status": "loaded", "load_issue": "", "schema_status": "supported", "field_status": "supported"}


def _execution_pack_ref(source: dict[str, Any]) -> str:
    # safe_evidence_ref 优先，兼容 nested summary 与 safe evidence bundle。
    summary = _dict(source, "route_task_field_retest_acceptance_execution_pack_summary")
    safe_bundle = _dict(source, "safe_evidence_bundle")
    safe_copy = _dict(source, "safe_copy")
    return _safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            summary.get("safe_evidence_ref"),
            summary.get("evidence_ref"),
            safe_bundle.get("safe_evidence_ref"),
            safe_bundle.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _callback_ref(callback: dict[str, Any]) -> str:
    # callback 必须能提供同一 evidence_ref 或 safe_evidence_ref。
    return _safe_ref(_first_text(callback.get("safe_evidence_ref"), callback.get("evidence_ref"), default=""))


def _same_ref_required(source: dict[str, Any], callback: dict[str, Any]) -> Any:
    # 弱类型字符串不能通过；必须保持 JSON boolean true。
    summary = _dict(source, "route_task_field_retest_acceptance_execution_pack_summary")
    safe_bundle = _dict(source, "safe_evidence_bundle")
    safe_copy = _dict(source, "safe_copy")
    return callback.get(
        "same_evidence_ref_required",
        source.get(
            "same_evidence_ref_required",
            summary.get("same_evidence_ref_required", safe_bundle.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True))),
        ),
    )


def _execution_pack_ready_status(source: dict[str, Any]) -> str:
    # 只有上一轮 ready_not_proven execution pack 能进入 callback intake ready 分支。
    summary = _dict(source, "route_task_field_retest_acceptance_execution_pack_summary")
    safe_bundle = _dict(source, "safe_evidence_bundle")
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("execution_pack_status"),
            source.get("status"),
            summary.get("execution_pack_status"),
            summary.get("status"),
            safe_bundle.get("execution_pack_status"),
            safe_copy.get("execution_pack_status"),
            default="missing",
        )
    )


def _source_materials(source: dict[str, Any]) -> list[str]:
    # required materials 可位于 artifact、summary 或 safe bundle；空值时回到固定契约。
    summary = _dict(source, "route_task_field_retest_acceptance_execution_pack_summary")
    safe_bundle = _dict(source, "safe_evidence_bundle")
    safe_copy = _dict(source, "safe_copy")
    raw = (
        source.get("required_route_elevator_materials")
        or summary.get("required_route_elevator_materials")
        or safe_bundle.get("required_route_elevator_materials")
        or safe_copy.get("required_route_elevator_materials")
        or REQUIRED_ROUTE_ELEVATOR_MATERIALS
    )
    materials = []
    for item in _safe_list(raw, limit=32):
        text = _safe_text(item).strip()
        if text and text not in materials:
            materials.append(text)
    for material in REQUIRED_ROUTE_ELEVATOR_MATERIALS:
        if material not in materials:
            materials.append(material)
    return materials


def _same_ref_match(source_ref: str, callback_ref: str, requested_ref: str) -> dict[str, Any]:
    # same evidence_ref 是现场回填链路主键，所有显式 ref 必须一致。
    expected = requested_ref or source_ref or callback_ref
    compared = [ref for ref in (source_ref, callback_ref, requested_ref) if ref]
    mismatches = sorted({ref for ref in compared if expected and ref != expected})
    if not expected or not compared:
        status = "missing_evidence_ref"
    elif mismatches:
        status = "mismatch"
    else:
        status = "matched"
    return {
        "status": status,
        "expected_evidence_ref": expected,
        "source_execution_pack_evidence_ref": source_ref,
        "callback_packet_evidence_ref": callback_ref,
        "requested_evidence_ref": requested_ref,
        "mismatched_evidence_refs": mismatches,
    }


def _material_key(value: Any) -> str:
    # material response 以材料类别为稳定复账主键，兼容 name/category/material 字段。
    if isinstance(value, dict):
        return _safe_text(_first_text(value.get("material"), value.get("category"), value.get("name"), default="")).strip()
    return _safe_text(value).strip()


def _parse_response_entries(value: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    # 回执必须是 object/list object，弱类型会 fail closed。
    if value in (None, ""):
        return {}, []
    entries: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for name, status in value.items():
            if isinstance(status, dict):
                item = {"material": name, **status}
            else:
                item = {"material": name, "status": status}
            entries.append(item)
    elif isinstance(value, list):
        if any(not isinstance(item, dict) for item in value):
            return {}, ["weak_material_responses"]
        entries = value
    else:
        return {}, ["weak_material_responses"]

    parsed: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    for item in entries:
        key = _material_key(item)
        status = item.get("status", item.get("result"))
        if not key or not isinstance(status, str):
            issues.append("weak_material_responses")
            continue
        normalized = status.strip().lower()
        if normalized in {"accepted", "received"}:
            normalized = "received"
        if normalized not in {"received", "missing", "rejected"}:
            issues.append("unsupported_material_response_status")
            continue
        parsed[key] = {
            "material": key,
            "status": normalized,
            "safe_note": _safe_text(_first_text(item.get("safe_note"), item.get("note"), item.get("reason"), default="")),
        }
    return parsed, sorted(set(issues))


def _list_responses(callback: dict[str, Any], key: str, status: str) -> tuple[dict[str, dict[str, Any]], str]:
    # 直接 received/missing/rejected list 也必须只含安全材料名或 object。
    value = callback.get(key)
    if value in (None, ""):
        return {}, ""
    if not isinstance(value, list):
        return {}, f"weak_{key}"
    parsed = {}
    for item in value:
        material = _material_key(item)
        if not material:
            return {}, f"weak_{key}"
        note = item.get("safe_note", item.get("note", "")) if isinstance(item, dict) else ""
        parsed[material] = {"material": material, "status": status, "safe_note": _safe_text(note)}
    return parsed, ""


def _callback_material_responses(callback: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    # callback 可用 material_responses，也可分 received/missing/rejected 三组表达。
    responses, issues = _parse_response_entries(callback.get("material_responses"))
    received, received_issue = _list_responses(callback, "received_materials", "received")
    missing, missing_issue = _list_responses(callback, "missing_materials", "missing")
    rejected, rejected_issue = _list_responses(callback, "rejected_materials", "rejected")
    merged = {**responses, **received, **missing, **rejected}
    issues.extend(issue for issue in (received_issue, missing_issue, rejected_issue) if issue)
    if not merged:
        issues.append("missing_material_responses")
    return merged, sorted(set(issues))


def _merge_material_updates(required_materials: list[str], responses: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    # received/missing/rejected 从 execution pack 要求逐项推导，不读取材料内容。
    received: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    required = [material for material in required_materials if material]
    for material in required:
        response = responses.get(material)
        base = {"material": material, "required": True}
        if not response:
            missing.append({**base, "reason": "callback_response_missing"})
        elif response["status"] == "received":
            received.append({**base, "safe_note": response["safe_note"]})
        elif response["status"] == "missing":
            missing.append({**base, "safe_note": response["safe_note"], "reason": "callback_marked_missing"})
        else:
            rejected.append({**base, "safe_note": response["safe_note"], "reason": "callback_marked_rejected"})
    for material, response in responses.items():
        if material not in required:
            rejected.append({"material": material, "required": False, "safe_note": response["safe_note"], "reason": "callback_material_not_in_execution_pack"})
    return received, missing, rejected


def _owner_next_steps(status: str, missing: list[dict[str, Any]], rejected: list[dict[str, Any]], evidence_ref: str) -> list[dict[str, Any]]:
    # owner next steps 只说明修回执或进入下一跳评审，不放行任何真实动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if not missing and not rejected and status == "ready_for_field_retest_acceptance_execution_callback_intake_not_proven":
        return [
            {
                "owner": "Product Manager / OKR Owner",
                "action": f"review acceptance execution callback intake summary for evidence_ref={ref}",
                "status": "not_proven_review_required",
            }
        ]
    next_steps = []
    if missing:
        next_steps.append({"owner": "Autonomy Algorithm Engineer", "action": "collect_missing_safe_callback_materials", "missing_materials": missing, "status": "blocked"})
    if rejected:
        next_steps.append({"owner": "Autonomy Algorithm Engineer", "action": "repair_rejected_safe_callback_materials", "rejected_materials": rejected, "status": "blocked"})
    if status.startswith("blocked_"):
        next_steps.append({"owner": "Robot Platform Engineer", "action": "keep_diagnostics_read_only_until_callback_intake_ready", "status": "metadata_only"})
    return _safe_value(next_steps)


def _next_required_evidence(status: str, missing: list[dict[str, Any]], rejected: list[dict[str, Any]], evidence_ref: str) -> list[str]:
    # next evidence 只列材料类别和动作，不包含本机路径或 raw artifact。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_field_retest_acceptance_execution_callback_intake_not_proven":
        return [f"Hand this callback intake summary to read-only Robot/mobile consumers under evidence_ref={ref}.", "Keep field closeout blocked until Product reviews real route/elevator materials."]
    if missing:
        names = ", ".join(item["material"] for item in missing[:12])
        return [f"Backfill missing safe callback materials for evidence_ref={ref}: {names}."]
    if rejected:
        names = ", ".join(item["material"] for item in rejected[:12])
        return [f"Repair rejected or unsupported callback materials for evidence_ref={ref}: {names}."]
    if status == "blocked_same_evidence_ref_mismatch":
        return [f"Rerun execution pack and callback packet with one safe evidence_ref={ref}."]
    if status == "blocked_unsafe_copy":
        return ["Remove raw paths, credentials, topics, hardware transport details, checksum, raw artifact, success wording, or control claims."]
    return ["Regenerate a supported acceptance execution pack and safe callback packet before reuse."]


def _rerun_commands(status: str, evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC evidence gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = [
        f"python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_pack.py --acceptance-review-decision-json <acceptance_review_decision.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_intake.py --acceptance-execution-pack-json <execution_pack.json> --callback-json <safe_callback_packet.json> --evidence-ref {ref}",
        "keep delivery_success=false and primary_actions_enabled=false until real field evidence is reviewed",
    ]
    if status.startswith("blocked_"):
        commands.append("repair safe callback packet, same evidence_ref, source schema, boundary, and strict material response types before reuse")
    return [_safe_text(command) for command in commands]


def _intake_status(
    source_issue: str,
    callback_issue: str,
    source_status: dict[str, Any],
    callback_status: dict[str, Any],
    source_ready: str,
    same_ref: dict[str, Any],
    same_ref_required: Any,
    unsafe: bool,
    parse_issues: list[str],
    missing: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
) -> str:
    # fail closed 顺序固定：输入可信性和安全边界优先于普通材料缺口。
    if source_issue in {"execution_pack_json_bad_json", "execution_pack_json_read_error", "execution_pack_json_not_object"}:
        return "blocked_bad_json"
    if callback_issue in {"callback_json_bad_json", "callback_json_read_error", "callback_json_not_object"}:
        return "blocked_bad_json"
    if source_issue:
        return "blocked_missing_execution_pack_json"
    if callback_issue:
        return "blocked_missing_callback_json"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_execution_pack_schema_or_boundary"
    if callback_status["schema_status"] != "supported" or callback_status["field_status"] != "supported":
        return "blocked_unsupported_callback_packet_schema_or_fields"
    if same_ref["status"] == "missing_evidence_ref":
        return "blocked_missing_evidence_ref"
    if same_ref["status"] == "mismatch":
        return "blocked_same_evidence_ref_mismatch"
    if same_ref_required is not True:
        return "blocked_same_evidence_ref_not_required"
    if unsafe:
        return "blocked_unsafe_copy"
    if parse_issues:
        return "blocked_weak_callback_fields"
    if source_ready != READY_EXECUTION_PACK_STATUS:
        return "blocked_execution_pack_not_ready"
    if rejected:
        return "blocked_rejected_callback_materials"
    if missing:
        return "blocked_missing_callback_materials"
    return "ready_for_field_retest_acceptance_execution_callback_intake_not_proven"


def _safe_copy(
    status: str,
    evidence_ref: str,
    received: list[dict[str, Any]],
    missing: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    owner_next_steps: list[dict[str, Any]],
    next_required_evidence: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或 callback。
    return {
        "schema": f"{CALLBACK_INTAKE_SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "callback_intake_status": status,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "received_materials": received,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "owner_next_steps": owner_next_steps,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "evidence_boundary": CALLBACK_INTAKE_BOUNDARY,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_acceptance_execution_callback_intake(
    acceptance_execution_pack_json: str,
    callback_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 execution pack 与 safe callback packet，生成 fail-closed callback intake。"""
    source_payload, source_issue, source_style = _load_json(acceptance_execution_pack_json, "execution_pack_json")
    callback_payload, callback_issue, callback_style = _load_json(callback_json, "callback_json")
    source = _find_execution_pack_source(source_payload) if source_payload else {}
    callback = _find_callback_source(callback_payload) if callback_payload else {}

    source_status = _execution_pack_status(source_issue, source)
    callback_status = _callback_status(callback_issue, callback)
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _execution_pack_ref(source)
    callback_ref = _callback_ref(callback)
    effective_ref = requested_ref or source_ref or callback_ref
    same_ref = _same_ref_match(source_ref, callback_ref, requested_ref)
    same_ref_required = _same_ref_required(source, callback)
    source_ready = _execution_pack_ready_status(source) if source else "missing"
    required_materials = _source_materials(source)

    material_responses, parse_issues = _callback_material_responses(callback)
    received_materials, missing_materials, rejected_materials = _merge_material_updates(required_materials, material_responses)
    unsafe = bool(source_payload or callback_payload) and (_unsafe_execution_pack_copy(source) or _unsafe_callback_copy(callback))
    status = _intake_status(
        source_issue,
        callback_issue,
        source_status,
        callback_status,
        source_ready,
        same_ref,
        same_ref_required,
        unsafe,
        parse_issues,
        missing_materials,
        rejected_materials,
    )

    owner_next_steps = _owner_next_steps(status, missing_materials, rejected_materials, effective_ref)
    next_required_evidence = _next_required_evidence(status, missing_materials, rejected_materials, effective_ref)
    rerun_commands = _rerun_commands(status, effective_ref)
    safe_copy = _safe_copy(status, effective_ref, received_materials, missing_materials, rejected_materials, owner_next_steps, next_required_evidence, rerun_commands)
    source_summary = {
        **source_status,
        "source_style": source_style,
        "schema": _safe_text(source.get("schema", "")),
        "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "execution_pack_status": source_ready,
        "safe_evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "required_materials_count": len(required_materials),
        "unsafe_copy": bool(_unsafe_execution_pack_copy(source)) if source else False,
    }
    callback_summary = {
        **callback_status,
        "source_style": callback_style,
        "schema": _safe_text(callback.get("schema", "")),
        "evidence_boundary": _safe_text(_first_text(callback.get("evidence_boundary"), callback.get("boundary"), default="")),
        "safe_evidence_ref": callback_ref,
        "parse_issues": parse_issues,
        "unsafe_copy": bool(_unsafe_callback_copy(callback)) if callback else False,
    }
    summary = {
        "schema": CALLBACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": CALLBACK_INTAKE_BOUNDARY,
        "boundary": CALLBACK_INTAKE_BOUNDARY,
        "status": status,
        "callback_intake_status": status,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "evidence_ref_status": same_ref,
        "source_execution_pack": source_summary,
        "safe_callback_packet": callback_summary,
        "required_route_elevator_materials": required_materials,
        "received_materials": _safe_value(received_materials),
        "missing_materials": _safe_value(missing_materials),
        "rejected_materials": _safe_value(rejected_materials),
        "owner_next_steps": owner_next_steps,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": CALLBACK_INTAKE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": CALLBACK_INTAKE_BOUNDARY,
        "boundary": CALLBACK_INTAKE_BOUNDARY,
        "status": status,
        "callback_intake_status": status,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "evidence_ref_status": same_ref,
        "source_execution_pack": source_summary,
        "safe_callback_packet": callback_summary,
        "required_route_elevator_materials": required_materials,
        "received_materials": _safe_value(received_materials),
        "missing_materials": _safe_value(missing_materials),
        "rejected_materials": _safe_value(rejected_materials),
        "owner_next_steps": owner_next_steps,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "route_task_field_retest_acceptance_execution_callback_intake_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_dir_scan",
            "raw_callback_artifact",
            "ros_graph",
            "real_nav2_runtime",
            "real_fixed_route_runtime",
            "route_elevator_field_pass",
            "hardware_transport",
            "hardware_feedback",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "real_phone_or_browser",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _unsafe_callback_copy(summary):
        # 最终防线：输出仍含危险 copy 时强制降级，并保留 fail-closed flags。
        artifact["status"] = "blocked_unsafe_copy"
        artifact["callback_intake_status"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["callback_intake_status"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["callback_intake_status"] = "blocked_unsafe_copy"
        summary["status"] = "blocked_unsafe_copy"
        summary["callback_intake_status"] = "blocked_unsafe_copy"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；未指定时由 CLI 打印到 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，方便 PC、Docker 和 focused unittest 共用。
    parser = argparse.ArgumentParser(description="Generate a route/task field retest acceptance execution callback intake artifact")
    parser.add_argument("--acceptance-execution-pack-json", required=True, help="acceptance execution pack artifact, summary, wrapper, file:<path>, or env:<VAR>")
    parser.add_argument("--callback-json", required=True, help="safe callback packet JSON, file:<path>, or env:<VAR>")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this callback intake gate")
    parser.add_argument("--output", default="", help="optional callback intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional callback intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print callback intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_acceptance_execution_callback_intake(
        args.acceptance_execution_pack_json,
        args.callback_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_acceptance_execution_callback_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_execution_callback_intake_summary_file: {_safe_ref(args.summary_output)}")
        print(f"acceptance_execution_callback_intake_status: {artifact['status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
