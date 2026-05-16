#!/usr/bin/env python3
"""生成 route/task field retest evidence dispatch artifact。

该 gate 只消费上一轮 route_task_field_retest_acceptance_brief 的 artifact、
summary 或 wrapper/nested JSON，把现场复测证据包拆成 owner、推荐文件名、
回填顺序和 callback checklist。它不读取真实材料目录，不访问 ROS graph、
Nav2 runtime、serial/UART、硬件、真实电梯、外部云或真实手机/browser。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_acceptance_brief as brief
import route_task_field_retest_material_pack as pack


# evidence dispatch 是 acceptance brief 之后的 PC 侧现场证据包派发契约。
DISPATCH_SCHEMA = "trashbot.route_task_field_retest_evidence_dispatch.v1"
DISPATCH_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_evidence_dispatch_summary.v1"
SCHEMA_VERSION = 1
DISPATCH_BOUNDARY = "software_proof_docker_route_task_field_retest_evidence_dispatch_gate"

# 只允许上一轮 acceptance brief 的 artifact 或 summary 进入本 gate。
SOURCE_SCHEMAS = {brief.BRIEF_SCHEMA, brief.BRIEF_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {brief.BRIEF_BOUNDARY, ""}

# literal 同时服务 rg 验收和人工复盘，避免证据边界被摘要层弱化。
BOUNDARY_NOTE = (
    "software_proof_docker_route_task_field_retest_evidence_dispatch_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# 八类材料沿用 acceptance brief 和 material pack，保证同一 evidence_ref 复账。
REQUIRED_EVIDENCE_PACKET = pack.REQUIRED_MATERIALS

# 本 gate 只派发证据包，不证明任何真实路线、电梯、投放、HIL 或云能力。
NOT_PROVEN = pack.NOT_PROVEN

# owner 映射固定，便于现场回填责任清楚且不依赖运行时系统。
MATERIAL_OWNER_BY_NAME = {
    "nav2_or_fixed_route_runtime_log": "Autonomy Algorithm Engineer",
    "route_completion_signal": "Autonomy Algorithm Engineer",
    "task_record": "Robot Platform Engineer",
    "door_state": "Autonomy Algorithm Engineer",
    "target_floor_confirmation": "Autonomy Algorithm Engineer",
    "human_assistance_note": "Product Manager / OKR Owner",
    "dropoff_or_cancel_completion": "Robot Platform Engineer",
    "delivery_result": "Product Manager / OKR Owner",
}

# 输入里出现这些原始工程细节时必须 fail closed，不能进入 Robot/mobile 摘要。
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

# success wording 和动作放行字段只能来自真实验收；本地派发层看到即阻断。
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
)

# raw 本机路径不允许被带进 dispatch；推荐文件名只使用相对路径。
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
    # UTC 时间让 Docker/local artifact 可以按生成顺序审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，避免 wrapper 里的敏感字段流入摘要。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 允许来自 CLI 或 source；路径形态只保留 basename。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 最终 payload 再递归脱敏一次，防止新增嵌套字段绕过 helper。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 下游只需要短清单；限长防止复制完整上游 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _encoded(value: Any) -> str:
    # 安全扫描覆盖键和值；不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 禁词必须在脱敏前检查，命中后输出 blocked 而不是修饰成 ready。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_raw_path_copy(value: Any) -> bool:
    # 本地绝对路径会泄露 host 结构，也会诱导下游去读真实目录。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(value: Any) -> bool:
    # 顶层布尔字段和自由文案都检查，保证动作放行不能穿透 wrapper。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _unsafe_copy(value: Any) -> bool:
    # 本 gate 不做“清洗后继续 ready”；检测到危险输入就 fail closed。
    return _has_forbidden_copy(value) or _has_raw_path_copy(value) or _has_success_or_control_claim(value)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都返回 blocked shape，便于自动化留痕。
    if not path:
        return {}, "acceptance_brief_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "acceptance_brief_json_missing"
    except json.JSONDecodeError:
        return {}, "acceptance_brief_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "acceptance_brief_json_read_error"
    if not isinstance(payload, dict):
        return {}, "acceptance_brief_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段；字符串 wrapper 不能伪装可信 JSON。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 的字段位置不同，取首个非空值。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免把任意 raw payload 当成 acceptance brief。
    candidates = [payload]
    for key in (
        "route_task_field_retest_evidence_dispatch",
        "route_task_field_retest_evidence_dispatch_summary",
        "route_task_field_retest_acceptance_brief",
        "route_task_field_retest_acceptance_brief_summary",
        "acceptance_brief",
        "acceptance_brief_summary",
        "brief",
        "brief_summary",
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
    # 优先消费 schema 命中的嵌套对象；没有命中时保留顶层解释 unsupported。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, str]:
    # schema 与 boundary 必须同时支持，防止跨 gate 材料跳级进入派发层。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = _safe_text(source.get("schema", "")).strip()
    boundary = _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # same evidence_ref 是 brief、dispatch、result intake 串联主键。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "acceptance_brief_summary")
    return _safe_ref(
        _first_text(
            source.get("evidence_ref"),
            summary.get("evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 弱类型字符串必须 fail closed；这里要求 JSON boolean true。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "acceptance_brief_summary")
    return source.get(
        "same_evidence_ref_required",
        summary.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
    )


def _source_acceptance_status(source: dict[str, Any]) -> str:
    # 上游 acceptance status 只决定是否派发，不被解释成真实现场通过。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "acceptance_brief_summary")
    return _safe_text(
        _first_text(
            source.get("acceptance_status"),
            source.get("status"),
            summary.get("acceptance_status"),
            summary.get("status"),
            safe_copy.get("acceptance_status"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _packet_names_from(value: Any) -> list[str]:
    # required_evidence_packet 支持 list[dict] 和 list[str]，但只取安全 name。
    names = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                name = _safe_text(_first_text(item.get("name"), item.get("material"), item.get("label"), default="")).strip()
            else:
                name = _safe_text(item).strip()
            if name and name not in names:
                names.append(name)
    return names


def _source_required_packet(source: dict[str, Any]) -> list[str]:
    # 只消费 acceptance brief 的 summary 字段，不读取真实材料目录补齐缺项。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "acceptance_brief_summary")
    for raw in (
        source.get("required_evidence_packet"),
        summary.get("required_evidence_packet"),
        safe_copy.get("required_evidence_packet"),
    ):
        names = _packet_names_from(raw)
        if names:
            return names
    return []


def _missing_required_packet(packet_names: list[str]) -> list[str]:
    # 派发层必须看见八类材料要求，否则无法保证现场回填口径完整。
    canonical = set(packet_names)
    return [name for name in REQUIRED_EVIDENCE_PACKET if name not in canonical]


def _dispatch_status(
    load_issue: str,
    source_status: dict[str, str],
    source_ref: str,
    requested_ref: str,
    same_ref_required: Any,
    unsafe_copy: bool,
    source_acceptance_status: str,
    missing_packet: list[str],
) -> str:
    # fail-closed 顺序固定，危险输入不会被普通缺失原因遮住。
    if load_issue in {"acceptance_brief_json_bad_json", "acceptance_brief_json_read_error", "acceptance_brief_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_acceptance_brief"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_schema"
    if not source_ref:
        return "blocked_missing_evidence_ref"
    if requested_ref and source_ref != requested_ref:
        return "blocked_same_evidence_ref_mismatch"
    if same_ref_required is not True:
        return "blocked_same_evidence_ref_not_required"
    if unsafe_copy:
        return "blocked_unsafe_acceptance_brief_copy"
    if source_acceptance_status != "ready_for_field_retest_acceptance_brief_not_proven":
        return "blocked_acceptance_brief_not_ready"
    if missing_packet:
        return "blocked_missing_required_evidence_packet"
    return "ready_for_field_retest_evidence_dispatch_not_proven"


def _recommended_filename(evidence_ref: str, material_name: str) -> str:
    # 推荐文件名是相对路径约定，故意不读、不探测真实材料目录。
    ref = evidence_ref or "<same_evidence_ref>"
    return f"field_retest_packet/{ref}/{material_name}.json"


def _required_evidence_packet(packet_names: list[str], evidence_ref: str) -> list[dict[str, Any]]:
    # 每个 packet item 同时给 owner 和推荐文件名，便于现场按同证据号回填。
    source_names = set(packet_names)
    labels = {
        "nav2_or_fixed_route_runtime_log": "Nav2/fixed-route runtime log",
        "route_completion_signal": "route completion signal",
        "task_record": "task record",
        "door_state": "door_state",
        "target_floor_confirmation": "target_floor_confirmation",
        "human_assistance_note": "human_assistance_note",
        "dropoff_or_cancel_completion": "dropoff_or_cancel_completion",
        "delivery_result": "delivery_result",
    }
    packet = []
    for name in REQUIRED_EVIDENCE_PACKET:
        packet.append(
            {
                "name": name,
                "label": labels[name],
                "owner": MATERIAL_OWNER_BY_NAME[name],
                "recommended_filename": _recommended_filename(evidence_ref, name),
                "required": True,
                "source_brief_status": "listed_by_acceptance_brief" if name in source_names else "missing_from_acceptance_brief",
                "same_evidence_ref_required": True,
            }
        )
    return packet


def _material_owners(required_packet: list[dict[str, Any]]) -> dict[str, list[str]]:
    # owner 聚合给 Robot/mobile 展示，不需要暴露完整 artifact。
    owners: dict[str, list[str]] = {}
    for item in required_packet:
        owner = _safe_text(item["owner"])
        owners.setdefault(owner, []).append(_safe_text(item["name"]))
    return owners


def _backfill_order() -> list[str]:
    # 回填顺序先采运行事实，再采终态和评审，避免先写结论后补证据。
    return [
        "nav2_or_fixed_route_runtime_log",
        "route_completion_signal",
        "task_record",
        "door_state",
        "target_floor_confirmation",
        "human_assistance_note",
        "dropoff_or_cancel_completion",
        "delivery_result",
    ]


def _callback_checklist(evidence_ref: str) -> list[str]:
    # callback checklist 要求现场回填失败原因，不允许回填成功口号。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"Confirm every material uses evidence_ref={ref}.",
        "Attach sanitized summaries only; do not attach raw logs, topics, device paths, credentials, or complete artifacts.",
        "Record route blocked reason when runtime log, completion signal, or task record is missing.",
        "Record elevator door_state, target_floor_confirmation, and human_assistance_note when elevator flow is involved.",
        "Record dropoff_or_cancel_completion and delivery_result only after field review attaches matching evidence.",
        "Re-run result intake and reconciliation after the packet is backfilled.",
    ]


def _fail_closed_rerun_notes(status: str, evidence_ref: str, source_acceptance_status: str, missing_packet: list[str]) -> list[str]:
    # rerun notes 把 blocked 原因转成下一步，不放现场通过措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    notes = [f"Rerun route_task_field_retest_evidence_dispatch.py with evidence_ref={ref} after acceptance brief repair."]
    if source_acceptance_status and source_acceptance_status != "ready_for_field_retest_acceptance_brief_not_proven":
        notes.append(f"Review source acceptance_status={source_acceptance_status} before evidence dispatch.")
    if missing_packet:
        notes.append("Restore required evidence packet items before dispatch: " + ", ".join(missing_packet))
    if status != "ready_for_field_retest_evidence_dispatch_not_proven":
        notes.append("Fix source schema, boundary, same evidence_ref, and safe copy before reusing this summary.")
    notes.append("Keep delivery_success=false and primary_actions_enabled=false until real field evidence is reviewed.")
    return [_safe_text(note) for note in notes[:6]]


def _same_ref_rule(evidence_ref: str) -> dict[str, Any]:
    # same-evidence-ref rule 是现场材料复账的硬约束，不能降级成字符串建议。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "same_evidence_ref_required": True,
        "evidence_ref": ref,
        "rule": "Every recommended filename and callback material must carry exactly the same safe evidence_ref.",
    }


def _safe_copy(status: str, evidence_ref: str, required_packet: list[dict[str, Any]]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不包含 raw artifact 或本机路径。
    return {
        "schema": f"{DISPATCH_SUMMARY_SCHEMA}.safe_copy",
        "dispatch_status": status,
        "evidence_boundary": DISPATCH_BOUNDARY,
        "evidence_ref": evidence_ref,
        "material_owners": _material_owners(required_packet),
        "recommended_filenames": [item["recommended_filename"] for item in required_packet],
        "required_evidence_packet": [item["name"] for item in required_packet],
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    material_owners: dict[str, list[str]],
    recommended_filenames: list[str],
    same_ref_rule: dict[str, Any],
    backfill_order: list[str],
    callback_checklist: list[str],
    fail_closed_rerun_notes: list[str],
    required_packet: list[dict[str, Any]],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是下游首选消费面，字段稳定且不包含 raw source。
    return {
        "schema": DISPATCH_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": DISPATCH_BOUNDARY,
        "boundary": DISPATCH_BOUNDARY,
        "status": status,
        "dispatch_status": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_rule": same_ref_rule,
        "material_owners": material_owners,
        "recommended_filenames": recommended_filenames,
        "backfill_order": backfill_order,
        "callback_checklist": callback_checklist,
        "fail_closed_rerun_notes": fail_closed_rerun_notes,
        "required_evidence_packet": required_packet,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_evidence_dispatch(
    acceptance_brief_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 acceptance brief，生成 fail-closed dispatch artifact 与 summary。"""
    payload, load_issue = _load_json(acceptance_brief_json)
    source = _find_source(payload) if payload else {}
    source_status = _source_status(load_issue, source)
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_evidence_ref(source)
    resolved_ref = requested_ref or source_ref
    same_ref_required = _same_ref_required(source)
    source_acceptance_status = _source_acceptance_status(source)
    packet_names = _source_required_packet(source)
    missing_packet = _missing_required_packet(packet_names)
    unsafe = bool(payload) and _unsafe_copy(source)
    status = _dispatch_status(
        load_issue,
        source_status,
        source_ref,
        requested_ref,
        same_ref_required,
        unsafe,
        source_acceptance_status,
        missing_packet,
    )

    required_packet = _required_evidence_packet(packet_names, resolved_ref)
    material_owners = _material_owners(required_packet)
    recommended_filenames = [item["recommended_filename"] for item in required_packet]
    same_ref_rule = _same_ref_rule(resolved_ref)
    backfill_order = _backfill_order()
    checklist = _callback_checklist(resolved_ref)
    rerun_notes = _fail_closed_rerun_notes(status, resolved_ref, source_acceptance_status, missing_packet)
    safe_copy = _safe_copy(status, resolved_ref, required_packet)
    summary = _summary_payload(
        status,
        resolved_ref,
        material_owners,
        recommended_filenames,
        same_ref_rule,
        backfill_order,
        checklist,
        rerun_notes,
        required_packet,
        safe_copy,
    )

    artifact = {
        "schema": DISPATCH_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": DISPATCH_BOUNDARY,
        "boundary": DISPATCH_BOUNDARY,
        "status": status,
        "dispatch_status": status,
        "evidence_ref": resolved_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_brief": {
            **source_status,
            "schema": _safe_text(source.get("schema", "")),
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
            "acceptance_status": source_acceptance_status,
            "evidence_ref": source_ref,
            "same_evidence_ref_required": same_ref_required,
            "required_evidence_packet_count": len(packet_names),
            "missing_required_evidence_packet": missing_packet,
            "unsafe_copy": bool(unsafe),
        },
        "dispatch_plan": {
            "dispatch_status": status,
            "material_owners": material_owners,
            "recommended_filenames": recommended_filenames,
            "same_evidence_ref_rule": same_ref_rule,
            "backfill_order": backfill_order,
            "callback_checklist": checklist,
            "fail_closed_rerun_notes": rerun_notes,
        },
        "required_evidence_packet": required_packet,
        "safe_copy": safe_copy,
        "route_task_field_retest_evidence_dispatch_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "ros_graph",
            "nav2_runtime",
            "serial_uart",
            "wave_rover",
            "real_elevator",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device_or_browser",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _unsafe_copy(summary):
        # 最终防线：summary 自身不安全时只降级状态，不回显 source。
        summary["status"] = "blocked_unsafe_dispatch_summary"
        summary["dispatch_status"] = "blocked_unsafe_dispatch_summary"
        artifact["status"] = "blocked_unsafe_dispatch_summary"
        artifact["dispatch_status"] = "blocked_unsafe_dispatch_summary"
        artifact["route_task_field_retest_evidence_dispatch_summary"] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时创建父目录；不指定时由 --once-json/stdout 展示 artifact。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，只把 acceptance brief JSON 转成 PC evidence dispatch。
    parser = argparse.ArgumentParser(description="Build route/task field retest evidence dispatch artifact")
    parser.add_argument("--acceptance-brief-json", required=True, help="acceptance brief artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for the evidence dispatch")
    parser.add_argument("--output", default="", help="optional evidence dispatch artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional evidence dispatch summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print evidence dispatch artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_evidence_dispatch(args.acceptance_brief_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_evidence_dispatch: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"dispatch_summary_file: {_safe_ref(args.summary_output)}")
        print(f"dispatch_status: {artifact['dispatch_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
