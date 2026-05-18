#!/usr/bin/env python3
"""生成 route/task field retest acceptance execution callback review decision artifact。

该 PC-only gate 只读取上一轮 acceptance execution callback intake 的 artifact、
summary 或 wrapper/nested JSON，把 received/missing/rejected 材料状态转成
下一步复核决策。它不读取真实材料目录、不访问 ROS graph、Nav2 runtime、
serial/UART、WAVE ROVER、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本 gate 是 acceptance execution callback intake 后的新契约，不能复用上一层 schema。
DECISION_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_callback_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_callback_review_decision_summary.v1"
SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate"

# 只接受上一轮 callback intake，避免跳过回执摄取直接解释现场材料。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_acceptance_execution_callback_intake.v1",
    "trashbot.route_task_field_retest_acceptance_execution_callback_intake_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate"
READY_SOURCE_STATUS = "ready_for_field_retest_acceptance_execution_callback_intake_not_proven"

# not_proven 固定覆盖真实路线、电梯、投放、HIL、手机和 O5 外部证据缺口。
NOT_PROVEN = (
    "real_nav2_fixed_route_runtime",
    "real_fixed_route_field_rerun",
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
    "route_task_field_retest_acceptance_execution_callback_review_decision; "
    "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false; "
    "ready_for_controlled_field_rerun; needs_material_backfill; evidence_ref_mismatch_rerun"
)

# 输入里出现底层工程细节或凭证时必须 fail closed，不能进入 Robot/mobile 展示面。
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

# 本地复核决策不能出现真实通过或动作放行措辞。
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
    # evidence_ref 若被误填成本机路径，只保留 basename，避免泄漏目录。
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


def _unsafe_copy(value: Any) -> bool:
    # 禁词在脱敏前检查，命中后直接 rejected，不做“清洗后 ready”。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY) or any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _success_or_control_claim(value: Any) -> bool:
    # 顶层布尔和自由文案都检查，防止成功语义穿透到下游。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都必须产生可落盘的 fail-closed decision。
    if not path:
        return {}, "callback_intake_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "callback_intake_missing"
    except json.JSONDecodeError:
        return {}, "callback_intake_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "callback_intake_read_error"
    if not isinstance(payload, dict):
        return {}, "callback_intake_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段，字符串 wrapper 不可信。
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
        "route_task_field_retest_acceptance_execution_callback_intake",
        "route_task_field_retest_acceptance_execution_callback_intake_summary",
        "route_task_field_retest_acceptance_execution_callback_review_decision",
        "route_task_field_retest_acceptance_execution_callback_review_decision_summary",
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
    # 优先选择 schema 命中的 acceptance callback intake 对象；否则保留顶层解释失败。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(source: dict[str, Any]) -> str:
    # intake status 是上游状态主键；缺失时不能默认 ready。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("callback_intake_status"),
            source.get("intake_status"),
            source.get("status"),
            robot.get("callback_intake_status"),
            robot.get("status"),
            mobile.get("callback_intake_status"),
            mobile.get("status"),
            safe_copy.get("callback_intake_status"),
            safe_copy.get("status"),
            default="",
        )
    )


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层、summary 或 safe_copy 取，最终仍做路径收敛。
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


def _same_ref_status(source: dict[str, Any]) -> dict[str, Any]:
    # callback intake 使用 evidence_ref_status；兼容后续 safe summary 的同义字段。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    raw = source.get(
        "evidence_ref_status",
        source.get("same_evidence_ref_match", robot.get("evidence_ref_status", mobile.get("evidence_ref_status", safe_copy.get("evidence_ref_status")))),
    )
    if isinstance(raw, dict):
        return _safe_value(raw)
    if isinstance(raw, str):
        return {"status": _safe_text(raw)}
    return {"status": "missing_evidence_ref"}


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止旧 JSON 或其它 gate 混用。
    schema = str(source.get("schema", "")).strip()
    boundary = str(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    return schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY


def _list_items(value: Any, limit: int = 64) -> list[Any]:
    # 材料状态只接受 list，避免弱类型字符串被当成已回收材料。
    if not isinstance(value, list):
        return []
    return _safe_value(value[:limit])


def _materials_from_source(source: dict[str, Any], key: str) -> list[Any]:
    # received/missing/rejected 可位于顶层、summary 或 safe_copy，统一白名单提取。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, robot, mobile, safe_copy):
        items = _list_items(candidate.get(key))
        if items:
            return items
    return []


def _material_keys(items: list[Any]) -> list[str]:
    # 下游只需要可读材料键，不复制完整材料内容。
    keys: list[str] = []
    for item in items[:32]:
        if isinstance(item, dict):
            key = _first_text(item.get("material"), item.get("category"), item.get("name"), item.get("key"), default="")
            keys.append(_safe_text(key or "material"))
        else:
            keys.append(_safe_text(item))
    return keys


def _review_decision(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_status: str,
    same_ref: dict[str, Any],
    received: list[Any],
    missing: list[Any],
    rejected: list[Any],
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 ready 或 backfill。
    if success_claim:
        return "rejected_unsafe_callback", ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "rejected_unsafe_callback", ["unsafe_copy_detected"]
    if load_issue or not _schema_supported(source):
        return "needs_material_backfill", [load_issue or "unsupported_acceptance_execution_callback_intake_schema_or_boundary"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun", [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref.get("status") not in {"matched", "ready"}:
        return "evidence_ref_mismatch_rerun", [f"same_evidence_ref:{same_ref.get('status', 'missing')}"]
    if source_status != READY_SOURCE_STATUS:
        return "needs_material_backfill", [f"source_callback_intake_status:{source_status or 'missing'}"]
    if missing:
        return "needs_material_backfill", ["missing_materials_present"]
    if rejected:
        return "needs_material_backfill", ["rejected_materials_present"]
    if not received:
        return "needs_material_backfill", ["received_materials_empty"]
    return "ready_for_controlled_field_rerun", []


def _field_rerun_readiness(decision: str) -> dict[str, Any]:
    # readiness 是只读判断，不会触发 Robot action 或 mobile action。
    return {
        "ready": decision == "ready_for_controlled_field_rerun",
        "state": "ready_for_controlled_field_rerun" if decision == "ready_for_controlled_field_rerun" else "not_ready",
        "blocked_by": "" if decision == "ready_for_controlled_field_rerun" else decision,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(decision: str, evidence_ref: str, missing: list[Any], rejected: list[Any]) -> list[str]:
    # 下一步证据只列材料动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == "ready_for_controlled_field_rerun":
        return [f"Schedule controlled field rerun review using sanitized callback intake under evidence_ref={ref}."]
    if decision == "needs_material_backfill":
        missing_keys = _material_keys(missing)
        rejected_keys = _material_keys(rejected)
        if missing_keys:
            return [f"Backfill missing acceptance execution callback materials for evidence_ref={ref}: " + ", ".join(missing_keys[:12])]
        if rejected_keys:
            return [f"Repair rejected acceptance execution callback materials for evidence_ref={ref}: " + ", ".join(rejected_keys[:12])]
        return [f"Regenerate supported acceptance execution callback intake for evidence_ref={ref}."]
    if decision == "evidence_ref_mismatch_rerun":
        return [f"Regenerate callback intake with one evidence_ref={ref}.", "Rerun this review decision after refs match."]
    return ["Regenerate callback intake without raw paths, credentials, ROS topics, serial/UART, WAVE ROVER detail, checksums, control claims, or success claims."]


def _owner_handoff(decision: str, evidence_ref: str, missing: list[Any], rejected: list[Any]) -> dict[str, Any]:
    # owner handoff 保持元数据责任分配，不把动作交给 Robot/mobile。
    return {
        "owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
        "handoff_status": "ready_for_controlled_field_rerun_not_proven" if decision == "ready_for_controlled_field_rerun" else "callback_repair_required_not_proven",
        "handoff_note": f"Review acceptance execution callback intake for evidence_ref={evidence_ref or '<same_evidence_ref>'}; keep Robot/mobile read-only and primary actions disabled.",
        "missing_material_keys": _material_keys(missing),
        "rejected_material_keys": _material_keys(rejected),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # command 只给 PC operator 复跑，不访问 ROS graph、硬件、云或手机设备。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_intake.py --acceptance-execution-pack-json <execution_pack.json> --callback-json <safe_callback_packet.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_decision.py --callback-intake-json <callback_intake.json> --evidence-ref {ref} --once-json",
    ]


def _safe_copy(
    decision: str,
    evidence_ref: str,
    source_status: str,
    received: list[Any],
    missing: list[Any],
    rejected: list[Any],
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料内容。
    return {
        "schema": f"{DECISION_SUMMARY_SCHEMA}.safe_copy",
        "review_decision": decision,
        "status": decision,
        "evidence_boundary": DECISION_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "source_callback_intake_status": source_status,
        "received_material_keys": _material_keys(received),
        "missing_material_keys": _material_keys(missing),
        "rejected_material_keys": _material_keys(rejected),
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    decision: str,
    status_reasons: list[str],
    evidence_ref: str,
    source_status: str,
    same_ref: dict[str, Any],
    received: list[Any],
    missing: list[Any],
    rejected: list[Any],
    next_required: list[str],
    owner_handoff: dict[str, Any],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 Robot/mobile 兼容消费面，字段稳定且 fail closed。
    return {
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_match": same_ref,
        "source_callback_intake_status": source_status,
        "source_callback_intake_schema": "trashbot.route_task_field_retest_acceptance_execution_callback_intake_summary.v1",
        "received_materials": received,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "received_material_keys": _material_keys(received),
        "missing_material_keys": _material_keys(missing),
        "rejected_material_keys": _material_keys(rejected),
        "field_rerun_readiness": _field_rerun_readiness(decision),
        "next_required_evidence": next_required,
        "owner_handoff": owner_handoff,
        "rerun_commands": _rerun_commands(evidence_ref),
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This review decision is metadata-only and does not read field material directories.",
            "Keep not_proven, delivery_success=false, and primary_actions_enabled=false until real evidence review.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_acceptance_execution_callback_review_decision(
    callback_intake_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 acceptance execution callback intake，生成 metadata-only review decision artifact。"""
    payload, load_issue = _load_json(callback_intake_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    source_status = _source_status(source) if source else ""
    same_ref = _same_ref_status(source) if source else {"status": "missing_evidence_ref"}
    received = _materials_from_source(source, "received_materials") if source else []
    missing = _materials_from_source(source, "missing_materials") if source else []
    rejected = _materials_from_source(source, "rejected_materials") if source else []
    unsafe = bool(payload) and _unsafe_copy(source)
    success_claim = bool(payload) and _success_or_control_claim(source)
    decision, status_reasons = _review_decision(
        load_issue,
        source,
        requested_ref,
        source_ref,
        source_status,
        same_ref,
        received,
        missing,
        rejected,
        unsafe,
        success_claim,
    )
    next_required = _next_required_evidence(decision, evidence_ref_out, missing, rejected)
    owner_handoff = _owner_handoff(decision, evidence_ref_out, missing, rejected)
    safe_copy = _safe_copy(decision, evidence_ref_out, source_status, received, missing, rejected)
    summary = _summary_payload(
        decision,
        status_reasons,
        evidence_ref_out,
        source_status,
        same_ref,
        received,
        missing,
        rejected,
        next_required,
        owner_handoff,
        safe_copy,
    )
    artifact = {
        "schema": DECISION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_match": same_ref,
        "source_callback_intake": {
            "load_issue": load_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "source_callback_intake_status": source_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "received_materials": received,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "field_rerun_readiness": _field_rerun_readiness(decision),
        "next_required_evidence": next_required,
        "owner_handoff": owner_handoff,
        "rerun_commands": _rerun_commands(evidence_ref_out),
        "safe_copy": safe_copy,
        "route_task_field_retest_acceptance_execution_callback_review_decision_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_dir_scan",
            "raw_field_material_content",
            "ros_graph",
            "real_nav2_runtime",
            "real_fixed_route_runtime",
            "route_elevator_field_pass",
            "route_completion_signal",
            "task_record_completion_signal",
            "dropoff_or_cancel_completion",
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
    if _unsafe_copy(artifact) or _unsafe_copy(summary) or _success_or_control_claim(artifact) or _success_or_control_claim(summary):
        # 最终防线：输出自身仍不安全时强制降级，并保留 fail-closed flags。
        artifact["status"] = "rejected_unsafe_callback"
        artifact["review_decision"] = "rejected_unsafe_callback"
        summary["status"] = "rejected_unsafe_callback"
        summary["review_decision"] = "rejected_unsafe_callback"
        artifact["route_task_field_retest_acceptance_execution_callback_review_decision_summary"] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest acceptance execution callback review decision artifact")
    parser.add_argument("--callback-intake-json", required=True, help="acceptance execution callback intake artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review decision")
    parser.add_argument("--output", default="", help="optional review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_acceptance_execution_callback_review_decision(args.callback_intake_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_acceptance_execution_callback_review_decision: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_execution_callback_review_decision_summary_file: {_safe_ref(args.summary_output)}")
        print(f"acceptance_execution_callback_review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
