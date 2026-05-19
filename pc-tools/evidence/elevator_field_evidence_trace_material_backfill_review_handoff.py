#!/usr/bin/env python3
"""生成 elevator field evidence trace material backfill review handoff artifact。

该 PC-only gate 只消费上一轮 material backfill review decision 的 artifact、
summary 或 Robot diagnostics safe alias，并把 review decision 转换成现场 owner
handoff package。它不读取真实材料目录、ROS graph、Nav2 runtime、serial/UART、
WAVE ROVER、真实电梯、外部云或真实手机/browser；输出始终是 software proof。
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_SCHEMA = "trashbot.elevator_field_evidence_trace_material_backfill_review_handoff.v1"
SUMMARY_SCHEMA = "trashbot.elevator_field_evidence_trace_material_backfill_review_handoff_summary.v1"
SOURCE_ARTIFACT_SCHEMA = "trashbot.elevator_field_evidence_trace_material_backfill_review_decision.v1"
SOURCE_SUMMARY_SCHEMA = "trashbot.elevator_field_evidence_trace_material_backfill_review_decision_summary.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_elevator_field_evidence_trace_material_backfill_review_handoff_gate"
SOURCE_BOUNDARY = "software_proof_docker_elevator_field_evidence_trace_material_backfill_review_decision_gate"

# rg 围栏依赖这些 literal；人工复核也能一眼确认没有扩大到真实现场证明。
BOUNDARY_NOTE = (
    "elevator_field_evidence_trace_material_backfill_review_handoff; "
    "elevator_field_evidence_trace_material_backfill_review_decision; safe_evidence_ref; "
    "same_evidence_ref_required; source=software_proof; not_proven; "
    "delivery_success=false; primary_actions_enabled=false; "
    "ready_for_field_owner_material_backfill_rerun_not_proven; "
    "needs_field_owner_material_handoff_not_proven; safe_rerun_hints; phone_safe_copy"
)

# handoff 只列材料类别，不读取真实材料文件或目录。
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

# not_proven 固定输出，防止 ready 状态被误读成实机通过。
NOT_PROVEN = (
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime",
    "real_fixed_route_runtime",
    "real_field_task_record",
    "real_dropoff_or_cancel_completion",
    "real_delivery_success",
    "real_waverover_uart_hil",
    "real_phone_browser",
    "objective_5_external_proof",
    "delivery_success",
)

SOURCE_SCHEMAS = {SOURCE_ARTIFACT_SCHEMA, SOURCE_SUMMARY_SCHEMA}
SUPPORTED_REVIEW_DECISIONS = {
    "needs_required_material_backfill_not_proven",
    "ready_for_field_evidence_material_review_handoff_not_proven",
}

# safe evidence_ref 是跨 artifact 对账主键，禁止路径、空白和弱占位符。
SAFE_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
PLACEHOLDER_PATTERNS = (
    re.compile(r"(?i)\b(todo|tbd|placeholder|sample|example|dummy|fake|null|none)\b"),
    re.compile(r"^<[^>]+>$"),
)

# 任何 raw path、凭证、控制 topic、硬件 transport 或 traceback 都不允许进入 handoff。
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

# 成功或动作授权文案只能来自真实验收；本 gate 看到就 fail closed。
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

# blocked 输出也要脱敏，避免把坏输入复制成新的证据泄漏。
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
    # UTC 便于 PC 与 Docker-only 证据按时间线排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，summary 不回显危险原文。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线，避免新增嵌套字段绕过局部 helper。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _encoded(value: Any) -> str:
    # unsafe 扫描覆盖嵌套键和值；不可编码时退回安全文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _unsafe_copy(value: Any) -> bool:
    # 禁止词和成功/控制语义必须在脱敏前阻断，不能清洗后放行。
    encoded = _encoded(value)
    forbidden = any(token in encoded for token in FORBIDDEN_COPY)
    raw_path = any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)
    success = any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)
    if isinstance(value, dict):
        success = success or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True
    return forbidden or raw_path or success


def _resolve_source_path(source: str) -> tuple[str, str]:
    # 支持 file:/env: 包装；source path 只用于读取，不进入 summary。
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
    # 缺输入、坏 JSON、非 object 都落成 blocked artifact，便于自动化复盘。
    path, source_style = _resolve_source_path(source)
    if not path:
        return {}, "material_backfill_review_decision_not_provided", source_style
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "material_backfill_review_decision_missing", source_style
    except json.JSONDecodeError:
        return {}, "material_backfill_review_decision_bad_json", source_style
    except (OSError, UnicodeDecodeError):
        return {}, "material_backfill_review_decision_read_error", source_style
    if not isinstance(payload, dict):
        return {}, "material_backfill_review_decision_not_object", source_style
    return payload, "", source_style


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # wrapper 字段必须是 object；字符串化 JSON 不能伪装可信 summary。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、diagnostics 和 safe_copy 字段位置不同，取首个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 wrapper，避免任意 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "elevator_field_evidence_trace_material_backfill_review_handoff",
        "elevator_field_evidence_trace_material_backfill_review_handoff_summary",
        "elevator_field_evidence_trace_material_backfill_review_decision",
        "elevator_field_evidence_trace_material_backfill_review_decision_summary",
        "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary",
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


def _find_source_decision(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中时优先返回上一轮 review decision；否则保留顶层用于 unsupported 诊断。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _safe_ref(value: Any) -> str:
    # handoff 不做 basename 降级；路径形态必须在 same-ref 状态中拒绝。
    return _safe_text(value).strip()


def _valid_safe_ref(ref: str) -> bool:
    # safe_evidence_ref 必须是短 token，不能是路径、URL、空白或占位。
    if not ref or "/" in ref or "\\" in ref or ref.startswith(("file:", "env:")):
        return False
    if any(pattern.search(ref) for pattern in PLACEHOLDER_PATTERNS):
        return False
    return bool(SAFE_REF_PATTERN.match(ref))


def _source_ref(source: dict[str, Any]) -> str:
    # safe_copy 和 diagnostics wrapper 都可能承载同一个 evidence_ref。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
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
    # review_decision 是上游主状态；status 仅用于兼容 summary。
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
    # 弱类型字符串 true 不能通过，必须保持 JSON boolean true。
    for candidate in _source_candidates(source):
        if "same_evidence_ref_required" in candidate:
            return candidate.get("same_evidence_ref_required")
    return None


def _same_ref_status(source: dict[str, Any]) -> dict[str, Any]:
    # 上游可能使用 object 或字符串状态；统一成 object 方便下游渲染。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        raw = candidate.get("same_evidence_ref_status") or candidate.get("same_evidence_ref_match")
        if isinstance(raw, dict):
            return _safe_value(raw)
        if isinstance(raw, str):
            return {"status": _safe_text(raw)}
    return {"status": "missing_evidence_ref"}


def _same_ref_match(requested_ref: str, source_ref: str, source_status: dict[str, Any], required: Any) -> dict[str, Any]:
    # CLI 和 source ref 都存在时必须一致；source ref 自身也必须安全。
    mismatches = []
    if requested_ref and source_ref and requested_ref != source_ref:
        mismatches.append(source_ref)
    status = _safe_text(source_status.get("status", "missing_evidence_ref"))
    if required is not True:
        final_status = "weak_same_evidence_ref_required"
    elif not _valid_safe_ref(source_ref):
        final_status = "unsafe_or_missing_source_evidence_ref"
    elif requested_ref and not _valid_safe_ref(requested_ref):
        final_status = "unsafe_requested_evidence_ref"
    elif mismatches:
        final_status = "mismatch"
    elif status not in {"matched", "ready"}:
        final_status = status or "missing_evidence_ref"
    else:
        final_status = "matched"
    return {
        "status": final_status,
        "expected_evidence_ref": requested_ref or source_ref,
        "refs": {"requested": requested_ref, "material_backfill_review_decision": source_ref},
        "mismatched_evidence_refs": mismatches,
        "source_same_evidence_ref_status": status,
        "same_evidence_ref_required": required,
    }


def _list_material_entries(value: Any) -> list[dict[str, Any]]:
    # 材料列表兼容字符串和 object，但只输出 material/reason 安全摘要。
    entries: list[dict[str, Any]] = []
    if not isinstance(value, list):
        return entries
    for item in value[:64]:
        if isinstance(item, dict):
            material = _safe_text(_first_text(item.get("material"), item.get("name"), item.get("category"), default="")).strip()
            reason = _safe_text(_first_text(item.get("reason"), item.get("safe_note"), item.get("note"), default="")).strip()
        else:
            material = _safe_text(item).strip()
            reason = ""
        if material:
            entry: dict[str, Any] = {"material": material, "required": material in REQUIRED_ROUTE_ELEVATOR_MATERIALS}
            if reason:
                entry["reason"] = reason
            entries.append(entry)
    return entries


def _material_list(source: dict[str, Any], field: str) -> list[dict[str, Any]]:
    # missing/rejected 可能在顶层、Robot/mobile 或 safe_copy，统一扁平化去重。
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in _source_candidates(source):
        for entry in _list_material_entries(candidate.get(field)):
            key = entry["material"]
            if key not in seen:
                result.append(entry)
                seen.add(key)
    return result


def _required_materials(source: dict[str, Any]) -> list[str]:
    # 上游可扩展 required list，但基础八类必须保留。
    materials: list[str] = []
    for candidate in _source_candidates(source):
        raw = candidate.get("required_route_elevator_materials") or candidate.get("required_materials")
        if not isinstance(raw, list):
            continue
        for item in raw[:64]:
            name = _safe_text(item.get("material", "") if isinstance(item, dict) else item).strip()
            if name and name not in materials:
                materials.append(name)
    for material in REQUIRED_ROUTE_ELEVATOR_MATERIALS:
        if material not in materials:
            materials.append(material)
    return materials


def _source_contract(load_issue: str, source: dict[str, Any], source_style: str, review_decision: str) -> dict[str, Any]:
    # 上游 review decision 必须保持 schema、boundary、software_proof、not_proven 和 false flags。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded", "source_style": source_style}
    schema = _safe_text(source.get("schema", "")).strip()
    boundary = _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    source_kind = _safe_text(source.get("source", "")).strip()
    overall = _safe_text(source.get("overall_status", "")).strip()
    supported = (
        schema in SOURCE_SCHEMAS
        and boundary == SOURCE_BOUNDARY
        and source_kind == "software_proof"
        and overall == "not_proven"
        and review_decision in SUPPORTED_REVIEW_DECISIONS
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )
    return {
        "load_status": "loaded",
        "load_issue": "",
        "schema_status": "supported" if supported else "unsupported",
        "source_style": source_style,
        "schema": schema,
        "evidence_boundary": boundary,
        "source": source_kind,
        "overall_status": overall,
        "review_decision": review_decision,
        "safe_evidence_ref": _source_ref(source),
        "unsafe_copy": bool(_unsafe_copy(source)) if source else False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _handoff_status(
    load_issue: str,
    source_contract: dict[str, Any],
    same_ref: dict[str, Any],
    unsafe: bool,
    missing: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    # fail-closed 顺序固定：可读性、契约、安全、same-ref，再处理 handoff 完整性。
    if load_issue:
        return "blocked_missing_material_backfill_review_decision_not_proven", [load_issue]
    if unsafe:
        return "blocked_unsafe_material_review_handoff_not_proven", ["unsafe_material_review_handoff_copy_detected"]
    if source_contract["schema_status"] != "supported":
        return "blocked_unsupported_material_backfill_review_decision_not_proven", ["unsupported_material_backfill_review_decision_contract"]
    if same_ref["status"] != "matched":
        return "blocked_evidence_ref_mismatch_not_proven", [same_ref["status"]]
    if missing or rejected:
        return "needs_field_owner_material_handoff_not_proven", ["field_owner_material_backfill_required"]
    return "ready_for_field_owner_material_backfill_rerun_not_proven", ["field_owner_handoff_package_ready_for_safe_rerun"]


def _field_owner_handoff(status: str, evidence_ref: str, missing: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # field_owner_handoff 是人工材料交接清单，不是机器人动作或现场执行授权。
    targets = missing + rejected
    if not targets:
        targets = [{"material": material, "required": True, "reason": "ready_for_same_ref_rerun_review"} for material in REQUIRED_ROUTE_ELEVATOR_MATERIALS]
    action = "collect_same_evidence_ref_material_then_rerun_review_decision_and_handoff"
    if status == "ready_for_field_owner_material_backfill_rerun_not_proven":
        action = "rerun_material_backfill_review_decision_with_same_evidence_ref"
    return [
        {
            "owner": "field-owner",
            "required_material": item["material"],
            "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
            "next_action": action,
            "status": "not_proven",
        }
        for item in targets
    ]


def _safe_rerun_hints(status: str, evidence_ref: str) -> list[str]:
    # rerun hints 只描述 PC 证据链复跑，不触发 ACK、Start、Confirm 或 Cancel。
    ref = evidence_ref or "<same_evidence_ref>"
    hints = [
        "use_the_same_safe_evidence_ref",
        "provide_only_redacted_material_refs_to_robot_and_mobile",
        "rerun_review_decision_before_claiming_ready",
        f"safe_evidence_ref={ref}",
        "keep source=software_proof, overall_status=not_proven, delivery_success=false, primary_actions_enabled=false",
    ]
    if status == "needs_field_owner_material_handoff_not_proven":
        hints.append("collect_missing_or_repair_rejected_materials_before_rerun")
    return hints


def _phone_safe_copy(status: str, missing: list[dict[str, Any]], rejected: list[dict[str, Any]]) -> list[str]:
    # 中文短句用于手机只读展示，明确不证明真实通过。
    if status == "ready_for_field_owner_material_backfill_rerun_not_proven":
        return ["现场材料交接包已齐备，可按同一证据编号复跑材料复核；仍未证明真实路线、电梯或投放通过。"]
    if status == "needs_field_owner_material_handoff_not_proven":
        names = [item["material"] for item in missing + rejected]
        return [f"现场材料仍未证明真实通过，请补齐同一证据编号下的材料：{', '.join(names[:8])}。"]
    return ["材料交接包未达到安全消费条件；请修复上游复核结果后再交给现场 owner。"]


def _safe_copy(
    status: str,
    evidence_ref: str,
    source_review_decision: str,
    field_owner_handoff: list[dict[str, Any]],
    safe_rerun_hints: list[str],
    phone_safe_copy: list[str],
    missing: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不包含完整 source decision。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "handoff_status": status,
        "status": status,
        "source": "software_proof",
        "overall_status": "not_proven",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "source_review_decision": source_review_decision,
        "field_owner_handoff": field_owner_handoff,
        "safe_rerun_hints": safe_rerun_hints,
        "phone_safe_copy": phone_safe_copy,
        "missing_required_materials": missing,
        "rejected_materials": rejected,
        "same_evidence_ref_required": True,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_elevator_field_evidence_trace_material_backfill_review_handoff(
    material_backfill_review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 material backfill review decision，生成 metadata-only handoff。"""
    payload, load_issue, source_style = _load_json(material_backfill_review_decision_json)
    source = _find_source_decision(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    effective_ref = requested_ref or source_ref
    review_decision = _source_review_decision(source) if source else ""
    same_required = _same_ref_required(source) if source else None
    same_ref = _same_ref_match(requested_ref, source_ref, _same_ref_status(source) if source else {}, same_required)
    source_contract = _source_contract(load_issue, source, source_style, review_decision)
    missing = _material_list(source, "missing_required_materials") if source else []
    rejected = _material_list(source, "rejected_material_refs") + _material_list(source, "rejected_materials") if source else []
    required_materials = _required_materials(source) if source else list(REQUIRED_ROUTE_ELEVATOR_MATERIALS)
    unsafe = bool(payload) and (_unsafe_copy(source) or _unsafe_copy(requested_ref))
    status, reasons = _handoff_status(load_issue, source_contract, same_ref, unsafe, missing, rejected)
    field_owner_handoff = _safe_value(_field_owner_handoff(status, effective_ref, missing, rejected))
    safe_rerun_hints = _safe_value(_safe_rerun_hints(status, effective_ref))
    phone_copy = _safe_value(_phone_safe_copy(status, missing, rejected))
    source_summary = {
        **source_contract,
        "schema": _safe_text(source.get("schema", "")) if source else "",
        "review_decision": review_decision,
        "safe_evidence_ref": source_ref,
        "same_evidence_ref_status": same_ref,
    }
    safe_copy = _safe_copy(status, effective_ref, review_decision, field_owner_handoff, safe_rerun_hints, phone_copy, missing, rejected)

    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "overall_status": "not_proven",
        "status": status,
        "handoff_status": status,
        "status_reasons": reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref,
        "source_review_decision": {
            "schema": source_summary["schema"],
            "review_decision": review_decision,
            "evidence_boundary": source_summary.get("evidence_boundary", ""),
            "safe_evidence_ref": source_ref,
        },
        "required_route_elevator_materials": required_materials,
        "field_owner_handoff": field_owner_handoff,
        "safe_rerun_hints": safe_rerun_hints,
        "phone_safe_copy": phone_copy,
        "missing_required_materials": missing,
        "rejected_materials": rejected,
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
        "handoff_status": status,
        "status_reasons": reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref,
        "source_material_backfill_review_decision": source_summary,
        "required_route_elevator_materials": required_materials,
        "field_owner_handoff": field_owner_handoff,
        "safe_rerun_hints": safe_rerun_hints,
        "phone_safe_copy": phone_copy,
        "missing_required_materials": missing,
        "rejected_materials": rejected,
        "safe_copy": safe_copy,
        "elevator_field_evidence_trace_material_backfill_review_handoff_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "raw_material_body",
            "raw_material_directory",
            "raw_source_review_decision_body",
            "ros_graph",
            "nav2_runtime",
            "serial_uart",
            "waverover_hardware",
            "real_elevator",
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
        # 最终输出若仍不安全，强制降级且不改变 false flags。
        status = "blocked_unsafe_material_review_handoff_not_proven"
        for target in (artifact, summary):
            target["status"] = status
            target["handoff_status"] = status
        artifact["elevator_field_evidence_trace_material_backfill_review_handoff_summary"] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只打印 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，便于 macOS PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate elevator field evidence trace material backfill review handoff artifact")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--material-backfill-review-decision-json", help="review decision artifact, summary, wrapper, file:<path>, or env:<VAR>")
    source.add_argument("--material-backfill-review-decision-summary", help="alias of --material-backfill-review-decision-json")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this handoff")
    parser.add_argument("--output", default="", help="optional handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional sanitized summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout and exit")
    args = parser.parse_args()

    review_decision_json = args.material_backfill_review_decision_json or args.material_backfill_review_decision_summary or ""
    artifact, summary, exit_code = build_elevator_field_evidence_trace_material_backfill_review_handoff(
        review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"elevator_field_evidence_trace_material_backfill_review_handoff: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"elevator_field_evidence_trace_material_backfill_review_handoff_summary_file:{_safe_ref(args.summary_output)}")
        print(f"elevator_field_evidence_trace_material_backfill_review_handoff_status:{artifact['status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
