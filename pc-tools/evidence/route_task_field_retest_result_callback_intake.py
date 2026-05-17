#!/usr/bin/env python3
"""生成 route/task field retest result callback intake artifact。

该 gate 只消费 result review dispatch 的安全摘要和现场同学回传的 sanitized
callback packet。它复账 owner work orders 与 callback packet requirements
是否逐项回应，并把回执整理成后续 review decision 可消费的安全 summary。
它不读取真实材料目录、不访问 ROS graph、Nav2 runtime、硬件、外部云或真实
手机/browser。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CALLBACK_INTAKE_SCHEMA = "trashbot.route_task_field_retest_result_callback_intake.v1"
CALLBACK_INTAKE_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_result_callback_intake_summary.v1"
SCHEMA_VERSION = 1
CALLBACK_INTAKE_BOUNDARY = "software_proof_docker_route_task_field_retest_result_callback_intake_gate"

# result callback intake 只能承接上一轮 result review dispatch，不能复用旧 evidence dispatch 合同。
DISPATCH_SCHEMA = "trashbot.route_task_field_retest_result_review_dispatch.v1"
DISPATCH_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_result_review_dispatch_summary.v1"
DISPATCH_BOUNDARY = "software_proof_docker_route_task_field_retest_result_review_dispatch_gate"
SOURCE_SCHEMAS = {DISPATCH_SCHEMA, DISPATCH_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {DISPATCH_BOUNDARY}
READY_DISPATCH_STATUS = "ready_for_field_retest_result_review_dispatch_not_proven"

# callback packet 允许无 schema，便于 PC-only fixture 和现场安全表单先落地。
CALLBACK_PACKET_SCHEMAS = {
    "",
    "trashbot.route_task_field_retest_result_callback_packet.v1",
    "trashbot.route_task_field_retest_result_callback_packet_summary.v1",
}
CALLBACK_PACKET_BOUNDARIES = {"", CALLBACK_INTAKE_BOUNDARY, DISPATCH_BOUNDARY}

# callback 字段白名单是安全边界；新增字段必须先补测试和文档。
CALLBACK_ALLOWED_FIELDS = {
    "schema",
    "schema_version",
    "evidence_boundary",
    "boundary",
    "evidence_ref",
    "safe_evidence_ref",
    "same_evidence_ref_required",
    "owner_work_orders",
    "work_order_responses",
    "callback_packet_requirements",
    "requirement_responses",
    "accepted_updates",
    "missing_updates",
    "rejected_updates",
    "owner_follow_up",
    "review_decision_handoff",
    "rerun_commands",
    "safe_copy",
    "delivery_success",
    "primary_actions_enabled",
}

NOT_PROVEN = (
    "real_nav2_fixed_route_runtime",
    "real_route_completion_signal",
    "real_task_record",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_record",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# rg 围栏依赖这些 literal，人工复盘也能快速识别本 gate 的边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_result_callback_intake; "
    "software_proof_docker_route_task_field_retest_result_callback_intake_gate; "
    "safe_evidence_ref; owner_work_orders; callback_packet_requirements; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# 输入中出现底层工程细节或凭证时必须 fail closed，避免进入 Robot/mobile 展示面。
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

# 输出前再脱敏一次；blocked artifact 也不能回显敏感输入。
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
    # result callback intake 不读取真实材料目录；绝对路径 copy 一律视为不安全。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(value: Any) -> bool:
    # 顶层布尔和自由文案都检查，防止成功语义穿透到下游。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _unsafe_copy(value: Any) -> bool:
    # 本 gate 是 metadata-only 入口，危险 copy 不允许降级成普通 note。
    return _has_forbidden_copy(value) or _has_raw_path_copy(value) or _has_success_or_control_claim(value)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都输出 blocked shape，方便自动化复盘。
    if not path:
        return {}, f"{label}_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, f"{label}_missing"
    except json.JSONDecodeError:
        return {}, f"{label}_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, f"{label}_read_error"
    if not isinstance(payload, dict):
        return {}, f"{label}_not_object"
    return payload, ""


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
    # 只递归白名单 key，避免任意 raw payload 被当成 result review dispatch。
    candidates = [payload]
    for key in (
        "route_task_field_retest_result_review_dispatch",
        "route_task_field_retest_result_review_dispatch_summary",
        "route_task_field_retest_result_callback_intake",
        "route_task_field_retest_result_callback_intake_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "source_dispatch",
        "dispatch_artifact",
        "dispatch_summary",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_dispatch_source(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中时优先返回嵌套对象；否则保留顶层用于 unsupported 诊断。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _callback_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # callback wrapper 常见于现场表单导出，仍只取白名单嵌套对象。
    candidates = [payload]
    for key in (
        "route_task_field_retest_result_callback",
        "route_task_field_retest_result_callback_packet",
        "route_task_field_retest_result_callback_intake",
        "field_callback",
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


def _dispatch_status(load_issue: str, source: dict[str, Any]) -> dict[str, Any]:
    # dispatch schema 与 boundary 必须同时白名单化，防止跨 gate artifact 被误用。
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


def _dispatch_ref(source: dict[str, Any]) -> str:
    # safe_evidence_ref 优先，兼容上一轮 summary 的 evidence_ref 字段。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return _safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
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
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return callback.get(
        "same_evidence_ref_required",
        source.get(
            "same_evidence_ref_required",
            robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True))),
        ),
    )


def _dispatch_ready_status(source: dict[str, Any]) -> str:
    # 只有上一轮 ready_not_proven dispatch 能进入 callback intake ready 分支。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("status"),
            source.get("dispatch_status"),
            robot.get("status"),
            mobile.get("status"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _dispatch_list(source: dict[str, Any], key: str) -> list[Any]:
    # dispatch fields 可位于顶层、Robot/mobile summary 或 safe_copy。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return _safe_list(source.get(key) or robot.get(key) or mobile.get(key) or safe_copy.get(key))


def _order_key(order: Any) -> str:
    # owner + work_order 是 work order 的稳定复账主键。
    if not isinstance(order, dict):
        return _safe_text(order).strip()
    owner = _safe_text(order.get("owner", "")).strip()
    work_order = _safe_text(order.get("work_order", order.get("name", ""))).strip()
    return f"{owner}|{work_order}" if owner or work_order else ""


def _requirement_key(requirement: Any) -> str:
    # callback requirement 以上一轮 dispatch 的 name 字段为主键。
    if not isinstance(requirement, dict):
        return _safe_text(requirement).strip()
    return _safe_text(_first_text(requirement.get("name"), requirement.get("requirement"), default="")).strip()


def _parse_response_entries(value: Any, kind: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    # 回执必须是 object/list object，弱类型会 fail closed。
    if value in (None, ""):
        return {}, [f"missing_{kind}_responses"]
    entries: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for name, status in value.items():
            if isinstance(status, dict):
                item = {"name": name, **status}
            else:
                item = {"name": name, "status": status}
            entries.append(item)
    elif isinstance(value, list):
        if any(not isinstance(item, dict) for item in value):
            return {}, [f"weak_{kind}_responses"]
        entries = value
    else:
        return {}, [f"weak_{kind}_responses"]

    parsed: dict[str, dict[str, Any]] = {}
    issues: list[str] = []
    for item in entries:
        key = _order_key(item) if kind == "work_order" else _requirement_key(item)
        status = item.get("status", item.get("result"))
        if not key or not isinstance(status, str):
            issues.append(f"weak_{kind}_responses")
            continue
        normalized = status.strip().lower()
        if normalized not in {"accepted", "missing", "rejected"}:
            issues.append(f"unsupported_{kind}_status")
            continue
        parsed[key] = {
            "key": key,
            "status": normalized,
            "safe_note": _safe_text(_first_text(item.get("safe_note"), item.get("note"), item.get("reason"), default="")),
        }
    return parsed, sorted(set(issues))


def _callback_work_responses(callback: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    # 兼容 callback 直接用 owner_work_orders 回填，也兼容显式 work_order_responses。
    raw = callback.get("work_order_responses", callback.get("owner_work_orders"))
    return _parse_response_entries(raw, "work_order")


def _callback_requirement_responses(callback: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    # callback_packet_requirements 必须逐项回应，不能只给一个整体 ready 字段。
    raw = callback.get("requirement_responses", callback.get("callback_packet_requirements"))
    return _parse_response_entries(raw, "requirement")


def _merge_updates(kind: str, dispatch_items: list[Any], responses: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    # accepted/missing/rejected 三类从 dispatch 要求逐项推导，不读取材料内容。
    accepted: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    dispatch_keys = []
    for item in dispatch_items:
        key = _order_key(item) if kind == "work_order" else _requirement_key(item)
        if not key:
            continue
        dispatch_keys.append(key)
        response = responses.get(key)
        base = {"kind": kind, "key": key, "source_item": _safe_value(item)}
        if not response:
            missing.append({**base, "reason": "callback_response_missing"})
        elif response["status"] == "accepted":
            accepted.append({**base, "safe_note": response["safe_note"]})
        elif response["status"] == "missing":
            missing.append({**base, "safe_note": response["safe_note"], "reason": "callback_marked_missing"})
        else:
            rejected.append({**base, "safe_note": response["safe_note"], "reason": "callback_marked_rejected"})
    for key, response in responses.items():
        if key not in dispatch_keys:
            rejected.append({"kind": kind, "key": key, "safe_note": response["safe_note"], "reason": "callback_response_not_in_dispatch"})
    return accepted, missing, rejected


def _optional_list(callback: dict[str, Any], key: str) -> tuple[list[Any], str]:
    # 可选更新字段必须保持 list，避免 nested raw object 混进摘要。
    value = callback.get(key)
    if value in (None, ""):
        return [], ""
    if not isinstance(value, list):
        return [], f"weak_{key}"
    return _safe_list(value), ""


def _same_ref_match(dispatch_ref: str, callback_ref: str, requested_ref: str) -> dict[str, Any]:
    # same evidence_ref 是现场回填链路主键，所有显式 ref 必须一致。
    expected = requested_ref or dispatch_ref or callback_ref
    compared = [ref for ref in (dispatch_ref, callback_ref, requested_ref) if ref]
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
        "dispatch_evidence_ref": dispatch_ref,
        "callback_evidence_ref": callback_ref,
        "requested_evidence_ref": requested_ref,
        "mismatched_evidence_refs": mismatches,
    }


def _owner_follow_up(status: str, missing: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # follow-up 只说明下一步修回执，不放行任何真实动作。
    if not missing and not rejected and status == "ready_for_field_retest_result_callback_intake_not_proven":
        return [{"owner": "Product Manager / OKR Owner", "action": "review_callback_intake_summary_before_result_review_decision", "status": "not_proven_review_required"}]
    follow_up = []
    if missing:
        follow_up.append({"owner": "Autonomy Algorithm Engineer", "action": "collect_missing_callback_responses", "missing_updates": missing, "status": "blocked"})
    if rejected:
        follow_up.append({"owner": "Autonomy Algorithm Engineer", "action": "repair_rejected_callback_responses", "rejected_updates": rejected, "status": "blocked"})
    if status.startswith("blocked_"):
        follow_up.append({"owner": "Robot Platform Engineer", "action": "keep_diagnostics_read_only_until_safe_summary_ready", "status": "metadata_only"})
    return _safe_value(follow_up)


def _review_decision_handoff(status: str, evidence_ref: str, missing: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> dict[str, Any]:
    # handoff 是给下一跳 review decision 的输入摘要，不是 result intake 成功结论。
    if status == "ready_for_field_retest_result_callback_intake_not_proven" and not missing and not rejected:
        decision = "ready_for_result_callback_review_decision_not_proven"
    elif missing:
        decision = "needs_callback_response_backfill_not_proven"
    elif rejected:
        decision = "needs_callback_response_repair_not_proven"
    else:
        decision = "blocked_before_callback_review_decision"
    return {
        "decision": decision,
        "evidence_ref": evidence_ref,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(status: str, evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC evidence gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = [
        f"python3 pc-tools/evidence/route_task_field_retest_result_review_dispatch.py --review-decision-json <review_decision.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/route_task_field_retest_result_callback_intake.py --dispatch-json <dispatch.json> --callback-json <callback_packet.json> --evidence-ref {ref}",
        "keep delivery_success=false and primary_actions_enabled=false until real field evidence is reviewed",
    ]
    if status.startswith("blocked_"):
        commands.append("repair safe callback packet, same evidence_ref, source schema, boundary, and strict response types before reuse")
    return [_safe_text(command) for command in commands]


def _intake_status(
    dispatch_issue: str,
    callback_issue: str,
    dispatch_status: dict[str, Any],
    callback_status: dict[str, Any],
    dispatch_ready: str,
    same_ref: dict[str, Any],
    same_ref_required: Any,
    unsafe: bool,
    parse_issues: list[str],
    missing: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
) -> str:
    # fail closed 顺序固定：输入可信性和安全边界优先于普通回执缺口。
    if dispatch_issue in {"dispatch_json_bad_json", "dispatch_json_read_error", "dispatch_json_not_object"}:
        return "blocked_bad_json"
    if callback_issue in {"callback_json_bad_json", "callback_json_read_error", "callback_json_not_object"}:
        return "blocked_bad_json"
    if dispatch_issue:
        return "blocked_missing_dispatch_json"
    if callback_issue:
        return "blocked_missing_callback_json"
    if dispatch_status["schema_status"] != "supported":
        return "blocked_unsupported_dispatch_schema_or_boundary"
    if callback_status["schema_status"] != "supported" or callback_status["field_status"] != "supported":
        return "blocked_unsupported_callback_schema_or_fields"
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
    if dispatch_ready != READY_DISPATCH_STATUS:
        return "blocked_dispatch_not_ready"
    if rejected:
        return "blocked_rejected_callback_updates"
    if missing:
        return "blocked_missing_callback_updates"
    return "ready_for_field_retest_result_callback_intake_not_proven"


def _safe_copy(
    status: str,
    evidence_ref: str,
    accepted: list[dict[str, Any]],
    missing: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    owner_follow_up: list[dict[str, Any]],
    review_handoff: dict[str, Any],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或 callback。
    return {
        "schema": f"{CALLBACK_INTAKE_SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "accepted_updates": accepted,
        "missing_updates": missing,
        "rejected_updates": rejected,
        "owner_follow_up": owner_follow_up,
        "review_decision_handoff": review_handoff,
        "rerun_commands": rerun_commands,
        "evidence_boundary": CALLBACK_INTAKE_BOUNDARY,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_result_callback_intake(
    dispatch_json: str,
    callback_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 dispatch 与 callback packet JSON，生成 fail-closed callback intake。"""
    dispatch_payload, dispatch_issue = _load_json(dispatch_json, "dispatch_json")
    callback_payload, callback_issue = _load_json(callback_json, "callback_json")
    dispatch_source = _find_dispatch_source(dispatch_payload) if dispatch_payload else {}
    callback_source = _find_callback_source(callback_payload) if callback_payload else {}

    dispatch_source_status = _dispatch_status(dispatch_issue, dispatch_source)
    callback_source_status = _callback_status(callback_issue, callback_source)
    requested_ref = _safe_ref(evidence_ref)
    dispatch_ref = _dispatch_ref(dispatch_source)
    callback_ref = _callback_ref(callback_source)
    effective_ref = requested_ref or dispatch_ref or callback_ref
    same_ref = _same_ref_match(dispatch_ref, callback_ref, requested_ref)
    same_ref_required = _same_ref_required(dispatch_source, callback_source)
    dispatch_ready = _dispatch_ready_status(dispatch_source) if dispatch_source else "missing"

    owner_work_orders = _dispatch_list(dispatch_source, "owner_work_orders")
    callback_packet_requirements = _dispatch_list(dispatch_source, "callback_packet_requirements")
    work_responses, work_issues = _callback_work_responses(callback_source)
    requirement_responses, requirement_issues = _callback_requirement_responses(callback_source)
    work_accepted, work_missing, work_rejected = _merge_updates("work_order", owner_work_orders, work_responses)
    req_accepted, req_missing, req_rejected = _merge_updates("requirement", callback_packet_requirements, requirement_responses)
    extra_accepted, accepted_issue = _optional_list(callback_source, "accepted_updates")
    extra_missing, missing_issue = _optional_list(callback_source, "missing_updates")
    extra_rejected, rejected_issue = _optional_list(callback_source, "rejected_updates")

    accepted_updates = _safe_value(work_accepted + req_accepted + extra_accepted)
    missing_updates = _safe_value(work_missing + req_missing + extra_missing)
    rejected_updates = _safe_value(work_rejected + req_rejected + extra_rejected)
    parse_issues = sorted(set(work_issues + requirement_issues + [issue for issue in (accepted_issue, missing_issue, rejected_issue) if issue]))
    unsafe = bool(dispatch_payload or callback_payload) and (_unsafe_copy(dispatch_source) or _unsafe_copy(callback_source))
    status = _intake_status(
        dispatch_issue,
        callback_issue,
        dispatch_source_status,
        callback_source_status,
        dispatch_ready,
        same_ref,
        same_ref_required,
        unsafe,
        parse_issues,
        missing_updates,
        rejected_updates,
    )

    owner_follow_up = _owner_follow_up(status, missing_updates, rejected_updates)
    review_handoff = _review_decision_handoff(status, effective_ref, missing_updates, rejected_updates)
    rerun_commands = _rerun_commands(status, effective_ref)
    safe_copy = _safe_copy(status, effective_ref, accepted_updates, missing_updates, rejected_updates, owner_follow_up, review_handoff, rerun_commands)
    source_dispatch_summary = {
        **dispatch_source_status,
        "schema": _safe_text(dispatch_source.get("schema", "")),
        "evidence_boundary": _safe_text(_first_text(dispatch_source.get("evidence_boundary"), dispatch_source.get("boundary"), default="")),
        "status": dispatch_ready,
        "safe_evidence_ref": dispatch_ref,
        "same_evidence_ref_required": same_ref_required,
        "owner_work_orders_count": len(owner_work_orders),
        "callback_packet_requirements_count": len(callback_packet_requirements),
        "unsafe_copy": bool(_unsafe_copy(dispatch_source)) if dispatch_source else False,
    }
    callback_packet_summary = {
        **callback_source_status,
        "schema": _safe_text(callback_source.get("schema", "")),
        "evidence_boundary": _safe_text(_first_text(callback_source.get("evidence_boundary"), callback_source.get("boundary"), default="")),
        "safe_evidence_ref": callback_ref,
        "parse_issues": parse_issues,
        "unsafe_copy": bool(_unsafe_copy(callback_source)) if callback_source else False,
    }
    summary = {
        "schema": CALLBACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": CALLBACK_INTAKE_BOUNDARY,
        "boundary": CALLBACK_INTAKE_BOUNDARY,
        "status": status,
        "intake_status": status,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_match": same_ref,
        "source_dispatch": source_dispatch_summary,
        "callback_packet": callback_packet_summary,
        "owner_work_orders": owner_work_orders,
        "callback_packet_requirements": callback_packet_requirements,
        "accepted_updates": accepted_updates,
        "missing_updates": missing_updates,
        "rejected_updates": rejected_updates,
        "owner_follow_up": owner_follow_up,
        "review_decision_handoff": review_handoff,
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
        "intake_status": status,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_match": same_ref,
        "source_dispatch": source_dispatch_summary,
        "callback_packet": callback_packet_summary,
        "owner_work_orders": owner_work_orders,
        "callback_packet_requirements": callback_packet_requirements,
        "accepted_updates": accepted_updates,
        "missing_updates": missing_updates,
        "rejected_updates": rejected_updates,
        "owner_follow_up": owner_follow_up,
        "review_decision_handoff": review_handoff,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
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
    if _unsafe_copy(artifact) or _unsafe_copy(summary):
        # 最终防线：输出仍含禁词时强制降级，并保留 fail-closed flags。
        artifact["status"] = "blocked_unsafe_copy"
        artifact["intake_status"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["intake_status"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["intake_status"] = "blocked_unsafe_copy"
        summary["status"] = "blocked_unsafe_copy"
        summary["intake_status"] = "blocked_unsafe_copy"
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest result callback intake artifact")
    parser.add_argument("--dispatch-json", required=True, help="result review dispatch artifact, summary, or wrapper JSON")
    parser.add_argument("--callback-json", required=True, help="safe callback packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this callback intake gate")
    parser.add_argument("--output", default="", help="optional callback intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional callback intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print callback intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_result_callback_intake(
        args.dispatch_json,
        args.callback_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_result_callback_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"result_callback_intake_summary_file: {_safe_ref(args.summary_output)}")
        print(f"result_callback_intake_status: {artifact['status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
