#!/usr/bin/env python3
"""生成 elevator field evidence trace callback review handoff artifact。

该 PC-only gate 只读取上一轮 callback review decision 的 artifact、summary
或 wrapper/nested diagnostics JSON，把 review decision 转成 owner handoff
package。它不读取真实材料目录，不访问 ROS graph、Nav2/fixed-route runtime、
serial/UART、WAVE ROVER、真实电梯、云服务或真实手机/browser，也不证明现场通过。
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_SCHEMA = "trashbot.elevator_field_evidence_trace_callback_review_handoff.v1"
SUMMARY_SCHEMA = "trashbot.elevator_field_evidence_trace_callback_review_handoff_summary.v1"
SOURCE_ARTIFACT_SCHEMA = "trashbot.elevator_field_evidence_trace_callback_review_decision.v1"
SOURCE_SUMMARY_SCHEMA = "trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_elevator_field_evidence_trace_callback_review_handoff_gate"
SOURCE_BOUNDARY = "software_proof_docker_elevator_field_evidence_trace_callback_review_decision_gate"

# rg 围栏和下游只读消费者依赖这些 literal 来确认边界没有放宽。
BOUNDARY_NOTE = (
    "elevator_field_evidence_trace_callback_review_handoff; "
    "elevator_field_evidence_trace_callback_review_decision; safe_evidence_ref; "
    "source=software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; ready_for_owner_material_backfill_not_proven; "
    "ready_for_field_execution_owner_handoff_not_proven"
)

# handoff 仍然要求这八类真实材料，但 gate 只列清单，不读取真实文件。
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

# not_proven 固定输出，防止 handoff ready 被误读为现场 route/elevator pass。
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
READY_REVIEW_DECISION = "ready_for_elevator_field_owner_handoff_not_proven"
BACKFILL_REVIEW_DECISION = "needs_route_elevator_material_backfill_not_proven"

DECISION_TO_HANDOFF = {
    READY_REVIEW_DECISION: "ready_for_field_execution_owner_handoff_not_proven",
    BACKFILL_REVIEW_DECISION: "ready_for_owner_material_backfill_not_proven",
}

# 输入如果带路径、凭证、控制 topic、传输细节或 raw 内容，必须 fail closed。
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

# 成功或动作授权文案会误导 Robot/mobile，因此和 unsafe copy 一样阻断。
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

# 本机绝对路径不能进入 handoff summary。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# blocked artifact 也要脱敏，避免错误输入被复制进证据归档。
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
    # UTC 便于不同 PC/Docker 主机生成的证据按字符串排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本统一脱敏，blocked 分支也不回显危险原文。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 若误填为路径，只保留 basename，避免泄漏本机目录。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 最终输出递归脱敏，防止新增嵌套字段绕过局部 helper。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
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
    # forbidden copy 在脱敏前判定，不能清洗后再当成 ready。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY) or any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(value: Any) -> bool:
    # 布尔字段和自然语言都检查，避免交付成功或动作授权语义穿透。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _unsafe_copy(value: Any) -> bool:
    # 对外 handoff 只允许 phone-safe metadata，不允许 raw/control/hardware/success copy。
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


def _load_json(source: str) -> tuple[dict[str, Any], str, str]:
    # 缺输入、坏 JSON、非 object 都转成可落盘 handoff，不抛异常中断自动化。
    path, source_style = _resolve_source_path(source)
    if not path:
        return {}, "review_decision_not_provided", source_style
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "review_decision_missing", source_style
    except json.JSONDecodeError:
        return {}, "review_decision_bad_json", source_style
    except (OSError, UnicodeDecodeError):
        return {}, "review_decision_read_error", source_style
    if not isinstance(payload, dict):
        return {}, "review_decision_not_object", source_style
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


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "elevator_field_evidence_trace_callback_review_handoff",
        "elevator_field_evidence_trace_callback_review_handoff_summary",
        "elevator_field_evidence_trace_callback_review_decision",
        "elevator_field_evidence_trace_callback_review_decision_summary",
        "robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择上一轮 review decision schema；否则保留顶层用于 unsupported 诊断。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层、diagnostics 或 safe_copy 取，最终仍做路径收敛。
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


def _source_review_decision(source: dict[str, Any]) -> str:
    # review_decision 是上游主状态；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("review_decision"),
            source.get("status"),
            safe_copy.get("review_decision"),
            safe_copy.get("status"),
            default="",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 任一显式 weak same-ref 都必须 fail closed。
    for candidate in _source_candidates(source):
        if "same_evidence_ref_required" in candidate:
            return candidate.get("same_evidence_ref_required")
    return True


def _same_ref_status(source: dict[str, Any]) -> dict[str, Any]:
    # 上游可能使用 same_evidence_ref_status、match object 或 safe_copy 字符串。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        raw = candidate.get("same_evidence_ref_status") or candidate.get("same_evidence_ref_match")
        if isinstance(raw, dict):
            return _safe_value(raw)
        if isinstance(raw, str):
            return {"status": _safe_text(raw)}
    return {"status": "missing_evidence_ref"}


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema、boundary、source、overall_status 是上一轮 review decision 契约。
    schema = str(source.get("schema", "")).strip()
    boundary = str(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    source_value = str(_first_text(source.get("source"), default="")).strip()
    overall_status = str(_first_text(source.get("overall_status"), default="")).strip()
    boundary_ok = boundary == SOURCE_BOUNDARY
    source_ok = source_value in {"software_proof"} or source_value.startswith("software_proof")
    status_ok = overall_status in {"not_proven"} or overall_status.endswith("_not_proven")
    return schema in SOURCE_SCHEMAS and boundary_ok and source_ok and status_ok


def _material_name(value: Any) -> str:
    # 材料列表兼容字符串和 object，但只提取白名单化的 material/name/category。
    if isinstance(value, dict):
        return _safe_text(_first_text(value.get("material"), value.get("name"), value.get("category"), default="")).strip()
    return _safe_text(value).strip()


def _material_list(source: dict[str, Any], field: str) -> list[dict[str, Any]]:
    # missing/rejected 可能在顶层、Robot/mobile 或 safe_copy，统一扁平化。
    result: list[dict[str, Any]] = []
    for candidate in _source_candidates(source):
        value = candidate.get(field)
        if not isinstance(value, list):
            continue
        for item in value[:64]:
            name = _material_name(item)
            if not name:
                continue
            entry = {"material": name}
            if isinstance(item, dict):
                reason = _safe_text(_first_text(item.get("reason"), item.get("safe_note"), item.get("note"), default=""))
                if reason:
                    entry["reason"] = reason
            if entry not in result:
                result.append(entry)
    return result


def _required_materials(source: dict[str, Any]) -> list[str]:
    # required list 可由上游扩展，但基础八类必须保留。
    materials: list[str] = []
    for candidate in _source_candidates(source):
        raw = candidate.get("required_route_elevator_materials")
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


def _same_ref_match(requested_ref: str, source_ref: str, same_ref: dict[str, Any], required: Any) -> dict[str, Any]:
    # CLI ref 与上游 ref 同时存在时必须一致；same_ref_required 必须是布尔 True。
    mismatch = bool(requested_ref and source_ref and requested_ref != source_ref)
    status = _safe_text(same_ref.get("status", "missing_evidence_ref"))
    if required is not True:
        final_status = "weak_same_evidence_ref_required"
    elif mismatch:
        final_status = "mismatch"
    elif not (requested_ref or source_ref):
        final_status = "missing_evidence_ref"
    elif status not in {"matched", "ready"}:
        final_status = status or "missing_evidence_ref"
    else:
        final_status = "matched"
    return {
        "status": final_status,
        "requested_ref": requested_ref,
        "source_ref": source_ref,
        "source_same_ref_status": status,
        "same_evidence_ref_required": required,
    }


def _handoff_status(
    load_issue: str,
    source: dict[str, Any],
    source_review_decision: str,
    same_ref_match: dict[str, Any],
    unsafe: bool,
) -> tuple[str, list[str]]:
    # fail-closed 顺序固定：可读性、契约、安全、同 ref、上游状态。
    if load_issue in {"review_decision_not_provided", "review_decision_missing"}:
        return "blocked_missing_review_decision_not_proven", [load_issue]
    if load_issue or not _schema_supported(source):
        return "blocked_unsupported_review_decision_not_proven", [load_issue or "unsupported_review_decision_schema_or_boundary"]
    if unsafe:
        return "blocked_unsafe_handoff_copy_not_proven", ["unsafe_copy_or_success_claim_detected"]
    if source.get("delivery_success") is not False or source.get("primary_actions_enabled") is not False:
        return "blocked_unsupported_review_decision_not_proven", ["required_false_flags_missing_or_not_false"]
    if same_ref_match["status"] != "matched":
        return "blocked_evidence_ref_mismatch_not_proven", [f"same_evidence_ref:{same_ref_match['status']}"]
    if source_review_decision not in DECISION_TO_HANDOFF:
        return "needs_review_decision_rerun_not_proven", [f"unsupported_source_review_decision:{source_review_decision or 'missing'}"]
    return DECISION_TO_HANDOFF[source_review_decision], []


def _owner_handoff(handoff_status: str, evidence_ref: str, missing: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> dict[str, list[str]]:
    # owner handoff 是只读责任分配，不改变 delivery action 或 UI gating。
    ref = evidence_ref or "<same_evidence_ref>"
    material_names = [item["material"] for item in (missing or rejected)] or list(REQUIRED_ROUTE_ELEVATOR_MATERIALS)
    if handoff_status == "ready_for_field_execution_owner_handoff_not_proven":
        return {
            "autonomy": [
                f"Review real Nav2/fixed-route runtime log under safe_evidence_ref={ref}.",
                f"Review route completion signal under safe_evidence_ref={ref}.",
            ],
            "robot": [
                "Review field task record and diagnostics same-ref summary.",
                "Keep robot diagnostics read-only and fail-closed.",
            ],
            "full_stack": [
                "Render phone-safe handoff package without enabling primary actions.",
                "Keep all primary action gating unchanged.",
            ],
            "field_owner": [
                "Keep real elevator door, target floor, assistance, dropoff/cancel, and delivery result materials ready for later review.",
            ],
        }
    if handoff_status == "ready_for_owner_material_backfill_not_proven":
        return {
            "autonomy": [f"Hold field execution review until owner material backfill is complete for safe_evidence_ref={ref}."],
            "robot": ["Keep robot diagnostics read-only; do not convert backfill state into route/elevator pass."],
            "full_stack": ["Show owner material backfill status without enabling primary actions."],
            "field_owner": [f"Backfill or repair route/elevator materials: {', '.join(material_names[:12])}."],
        }
    return {
        "autonomy": [f"Rerun or repair callback review decision under safe_evidence_ref={ref} before handoff."],
        "robot": ["Keep downstream diagnostics blocked until supported handoff summary exists."],
        "full_stack": ["Render fail-closed copy only; primary actions remain disabled."],
        "field_owner": ["Do not treat this handoff as field material acceptance."],
    }


def _next_required_evidence(handoff_status: str, evidence_ref: str, missing: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> list[str]:
    # 下一步只描述材料/复跑动作，不授权 Robot/mobile 控制动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == "ready_for_field_execution_owner_handoff_not_proven":
        return [
            f"same_evidence_ref_field_execution_owner_review:{ref}",
            "Keep software_proof/not_proven until real route/elevator field materials are reviewed.",
        ]
    if handoff_status == "ready_for_owner_material_backfill_not_proven":
        names = [item["material"] for item in (missing or rejected)] or list(REQUIRED_ROUTE_ELEVATOR_MATERIALS)
        return [f"same_evidence_ref_real_field_material_backfill:{ref}:{','.join(names[:12])}"]
    if handoff_status == "blocked_evidence_ref_mismatch_not_proven":
        return [f"rerun_callback_review_decision_with_same_safe_evidence_ref:{ref}"]
    if handoff_status == "blocked_unsafe_handoff_copy_not_proven":
        return ["regenerate_review_decision_without_raw_paths_credentials_topics_transport_checksums_or_success_claims"]
    return [f"provide_supported_callback_review_decision_and_rerun_handoff:{ref}"]


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只包含 PC evidence gates，不包含 ROS、Nav2、硬件、云或手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/elevator_field_evidence_trace_callback_review_decision.py --callback-intake-json <callback_intake_summary.json> --evidence-ref {ref} --once-json",
        f"python3 pc-tools/evidence/elevator_field_evidence_trace_callback_review_handoff.py --callback-review-decision-json <callback_review_decision_summary.json> --evidence-ref {ref} --once-json",
        "keep source=software_proof, overall_status=not_proven, delivery_success=false, primary_actions_enabled=false",
    ]


def _safe_copy(handoff_status: str, evidence_ref: str, source_review_decision: str, next_required: list[str]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 首选消费面，不包含 raw source 或完整 artifact。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "handoff_status": handoff_status,
        "status": handoff_status,
        "source": "software_proof",
        "overall_status": "not_proven",
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "source_review_decision": source_review_decision,
        "next_required_evidence": next_required,
        "same_evidence_ref_required": True,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_elevator_field_evidence_trace_callback_review_handoff(
    callback_review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 callback review decision，生成 metadata-only handoff artifact。"""
    payload, load_issue, source_style = _load_json(callback_review_decision_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    effective_ref = requested_ref or source_ref
    source_review_decision = _source_review_decision(source) if source else ""
    same_ref = _same_ref_status(source) if source else {"status": "missing_evidence_ref"}
    same_required = _same_ref_required(source) if source else True
    same_ref_match = _same_ref_match(requested_ref, source_ref, same_ref, same_required)
    missing = _material_list(source, "missing_required_materials") if source else []
    rejected = _material_list(source, "rejected_callback_materials") if source else []
    required_materials = _required_materials(source) if source else list(REQUIRED_ROUTE_ELEVATOR_MATERIALS)
    unsafe = bool(payload) and _unsafe_copy(source)
    handoff_status, reasons = _handoff_status(load_issue, source, source_review_decision, same_ref_match, unsafe)
    owner_handoff = _owner_handoff(handoff_status, effective_ref, missing, rejected)
    next_required = _next_required_evidence(handoff_status, effective_ref, missing, rejected)
    rerun_commands = _rerun_commands(effective_ref)
    safe_copy = _safe_copy(handoff_status, effective_ref, source_review_decision, next_required)

    source_summary = {
        "load_issue": load_issue,
        "source_style": source_style,
        "schema": _safe_text(source.get("schema", "")) if source else "",
        "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
        "source": _safe_text(_first_text(source.get("source"), default="")) if source else "",
        "overall_status": _safe_text(_first_text(source.get("overall_status"), default="")) if source else "",
        "review_decision": source_review_decision,
        "safe_evidence_ref": source_ref,
        "same_evidence_ref_status": same_ref_match,
        "unsafe_copy": bool(unsafe),
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "overall_status": "not_proven",
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_match,
        "source_review_decision": {
            "schema": source_summary["schema"],
            "review_decision": source_review_decision,
            "safe_evidence_ref": source_ref,
        },
        "required_route_elevator_materials": required_materials,
        "missing_required_materials": missing,
        "rejected_callback_materials": rejected,
        "owner_handoff": owner_handoff,
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
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_match,
        "source_callback_review_decision": source_summary,
        "required_route_elevator_materials": required_materials,
        "missing_required_materials": missing,
        "rejected_callback_materials": rejected,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "elevator_field_evidence_trace_callback_review_handoff_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_dir_scan",
            "raw_callback_body",
            "raw_review_decision_body",
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
        handoff_status = "blocked_unsafe_handoff_copy_not_proven"
        for target in (artifact, summary):
            target["status"] = handoff_status
            target["handoff_status"] = handoff_status
        artifact["elevator_field_evidence_trace_callback_review_handoff_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate elevator field evidence trace callback review handoff artifact")
    parser.add_argument("--callback-review-decision-json", required=True, help="callback review decision artifact, summary, wrapper/nested JSON, file:<path>, or env:<VAR>")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this handoff")
    parser.add_argument("--output", default="", help="optional handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional sanitized summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_elevator_field_evidence_trace_callback_review_handoff(
        args.callback_review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"elevator_field_evidence_trace_callback_review_handoff: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"elevator_field_evidence_trace_callback_review_handoff_summary_file:{_safe_ref(args.summary_output)}")
        print(f"handoff_status:{artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
