#!/usr/bin/env python3
"""生成 route/task field retest acceptance execution handoff intake artifact。

该 PC-only gate 消费上一轮 callback review handoff artifact/summary，并可选消费
owner callback/intake JSON。它只把交接包和 owner acknowledgement 转成可复核的
metadata，不读取真实硬件、串口、网络、Nav2 runtime、mobile runtime 或材料目录。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本轮 gate 是 handoff 后的新 intake 契约，schema/status 不能复用上一轮 handoff。
INTAKE_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_handoff_intake.v1"
INTAKE_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_handoff_intake_summary.v1"
SCHEMA_VERSION = 1
INTAKE_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate"

# 上游只接受上一轮 callback review handoff artifact 或 summary。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff.v1",
    "trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate"
READY_SOURCE_STATUS = "ready_for_acceptance_execution_callback_review_handoff"

# owner ack 不要求强 schema，但只从白名单字段读取，避免采信 raw wrapper。
ACK_TRUE_VALUES = {"ack", "acked", "acknowledged", "accepted", "ready", "received", "confirmed"}
ACK_FALSE_VALUES = {"", "missing", "none", "pending", "needs_owner_ack", "rejected", "blocked"}

# not_proven 固定覆盖真实路线、电梯、终态、手机、HIL 和 O5 外部证据缺口。
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

# rg 围栏依赖这些 literal；人工审计也能快速确认边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_acceptance_execution_handoff_intake; "
    "software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate; "
    "ready_for_controlled_field_rerun_queue; needs_owner_ack; "
    "needs_acceptance_execution_handoff_backfill; evidence_ref_mismatch_rerun; "
    "blocked_unsafe_handoff_intake; not_proven; delivery_success=false; "
    "primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只消费 handoff 与 owner ack，不读取现场材料目录。
# 设计约束 02：owner ack 只代表交接回执，不证明现场复跑通过。
# 设计约束 03：ready 队列状态仍保持 not_proven 和动作禁用。
# 设计约束 04：source schema/boundary 不匹配必须 fail closed。
# 设计约束 05：缺 evidence_ref 不能进入受控复跑队列。
# 设计约束 06：same_evidence_ref_required 固定为 true，保护证据链主键。
# 设计约束 07：owner ack 与 source evidence_ref 不一致必须要求重跑。
# 设计约束 08：unsafe copy、凭证、runtime topic、硬件 transport 和路径必须阻断。
# 设计约束 09：success/control claim 必须阻断，不能进入 Robot/mobile。
# 设计约束 10：summary 是下游白名单，不复制完整 source 或 owner JSON。
# 设计约束 11：wrapper/nested JSON 只递归白名单 key，避免 raw payload 误采信。
# 设计约束 12：缺 owner ack 要明确停在 needs_owner_ack。
# 设计约束 13：source 非 ready 或需要 follow-up 时进入 handoff backfill。
# 设计约束 14：rerun hint 只给 PC operator，不访问 ROS graph 或硬件。
# 设计约束 15：输出递归脱敏，blocked artifact 也不泄漏 raw material。
# 设计约束 16：exit code 保持 0，让 blocked intake 也能落盘审计。
# 设计约束 17：该 gate 不改变 Start/Confirm/Cancel 或 Robot action gating。
# 设计约束 18：该 gate 不推进 Objective 5 external proof。
# 设计约束 19：该 gate 不替代真实 result review、delivery result 或 HIL。
# 设计约束 20：新增状态必须同步 tests，避免 happy path 冒充闭环。

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

# 成功或动作授权不能通过 owner ack 进入下游。
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

# 本机绝对路径不能进入 intake summary。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# 所有自由文本输出前先脱敏，保证 blocked case 也可保存。
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
    # UTC 时间让不同 PC/Docker 主机产物可排序审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本先脱敏，再进入 artifact 或 summary。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 若被误填成本机路径，只保留 basename。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线，防止新增嵌套字段绕过 helper。
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
    # 安全扫描使用稳定 JSON，覆盖键名和值。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # forbidden copy 命中说明输入不适合进入 Robot/mobile 摘要。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY) or any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_claim(value: Any) -> bool:
    # 布尔字段和自由文案都检查，避免 success/control claim 穿透。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # owner ack 是可选输入；source handoff 缺失则必须 fail closed。
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
    # 只接受 object 嵌套字段；字符串 wrapper 不可信。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 字段位置不同，取首个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _candidates(payload: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免 raw payload 被误采信。
    candidates = [payload]
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_candidates(value, keys))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 schema 命中的 handoff 对象；否则保留顶层用于 unsupported 解释。
    keys = (
        "route_task_field_retest_acceptance_execution_callback_review_handoff",
        "route_task_field_retest_acceptance_execution_callback_review_handoff_summary",
        "route_task_field_retest_acceptance_execution_handoff_intake",
        "route_task_field_retest_acceptance_execution_handoff_intake_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    )
    for candidate in _candidates(payload, keys):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _find_owner_ack(payload: dict[str, Any]) -> dict[str, Any]:
    # owner ack 支持常见 wrapper，但只提取白名单字段，不复制完整 callback。
    keys = (
        "owner_handoff_intake",
        "owner_callback",
        "owner_acknowledgement",
        "owner_acknowledgment",
        "acknowledgement",
        "acknowledgment",
        "handoff_intake",
        "route_task_field_retest_acceptance_execution_handoff_intake",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    )
    for candidate in _candidates(payload, keys):
        if _owner_ack_state(candidate) != "missing":
            return candidate
    return payload


def _list_text(value: Any, limit: int = 24) -> list[str]:
    # next evidence/rerun 摘要只输出扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit] if isinstance(item, (str, int, float, bool))]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _source_status(source: dict[str, Any]) -> str:
    # handoff_status 是上游主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(_first_text(source.get("handoff_status"), source.get("status"), safe_copy.get("handoff_status"), default=""))


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


def _source_owner_handoff(source: dict[str, Any]) -> list[Any]:
    # owner handoff 可来自上游顶层或 safe_copy；这里只安全透传摘要。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        item = candidate.get("owner_handoff")
        if isinstance(item, dict):
            return [_safe_value(item)]
        if isinstance(item, list):
            return _safe_value(item[:24])
    return []


def _source_next_required(source: dict[str, Any]) -> list[str]:
    # next_required_evidence 是交接后的行动清单，不代表已完成。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        items = _list_text(candidate.get("next_required_evidence"))
        if items:
            return items
    return []


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止其它 gate JSON 混入。
    schema = str(source.get("schema", "")).strip()
    boundary = str(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    return schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY


def _owner_ack_state(owner: dict[str, Any]) -> str:
    # 多字段兼容现场 owner callback，但只把显式 ack 视为 acknowledged。
    if not owner:
        return "missing"
    for key in ("owner_acknowledgement_state", "owner_acknowledgment_state", "acknowledgement_state", "acknowledgment_state", "ack_state", "state", "status"):
        value = _safe_text(owner.get(key)).strip().lower()
        if value in ACK_TRUE_VALUES:
            return "acknowledged"
        if value in ACK_FALSE_VALUES:
            return "missing" if value in {"", "missing", "none"} else value
    for key in ("owner_ack", "ack", "acknowledged", "accepted", "received", "confirmed"):
        value = owner.get(key)
        if value is True:
            return "acknowledged"
        if isinstance(value, str) and value.strip().lower() in ACK_TRUE_VALUES:
            return "acknowledged"
    return "missing"


def _owner_ref(owner: dict[str, Any]) -> str:
    # owner callback 也必须绑定同一个 safe evidence_ref。
    safe_copy = _dict(owner, "safe_copy")
    return _safe_ref(
        _first_text(
            owner.get("safe_evidence_ref"),
            owner.get("evidence_ref"),
            owner.get("ack_evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _owner_handoff_intake(owner: dict[str, Any], ack_state: str, evidence_ref: str) -> dict[str, Any]:
    # owner handoff 只保留回执摘要，拒绝 raw callback 内容进入 summary。
    return {
        "owner": _safe_text(_first_text(owner.get("owner"), owner.get("ack_owner"), default="field_owner")),
        "acknowledgement_state": ack_state,
        "safe_evidence_ref": evidence_ref,
        "received_at": _safe_text(_first_text(owner.get("received_at"), owner.get("ack_at"), default="")),
        "note": _safe_text(_first_text(owner.get("safe_note"), owner.get("note"), owner.get("summary"), default="")),
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _intake_status(
    source_load_issue: str,
    owner_load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_status: str,
    owner_ref: str,
    ack_state: str,
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 ready queue。
    reasons: list[str] = []
    if source_load_issue:
        reasons.append(source_load_issue)
    if owner_load_issue and owner_load_issue != "owner_intake_not_provided":
        reasons.append(owner_load_issue)
    if success_claim:
        return "blocked_unsafe_handoff_intake", reasons + ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked_unsafe_handoff_intake", reasons + ["unsafe_copy_detected"]
    if source_load_issue or not _schema_supported(source):
        return "needs_acceptance_execution_handoff_backfill", reasons + ["unsupported_acceptance_execution_handoff_schema_or_boundary"]
    if source.get("same_evidence_ref_required") is not True:
        return "evidence_ref_mismatch_rerun", reasons + ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return "evidence_ref_mismatch_rerun", reasons + ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun", reasons + [f"requested_ref:{requested_ref}!={source_ref}"]
    if owner_ref and owner_ref != source_ref:
        return "evidence_ref_mismatch_rerun", reasons + [f"owner_ref:{owner_ref}!={source_ref}"]
    if source_status != READY_SOURCE_STATUS:
        return "needs_acceptance_execution_handoff_backfill", reasons + [f"source_handoff_status:{source_status or 'missing'}"]
    if ack_state != "acknowledged":
        return "needs_owner_ack", reasons + ["owner_acknowledgement_missing"]
    return "ready_for_controlled_field_rerun_queue", reasons


def _next_required_evidence(status: str, evidence_ref: str, upstream_next: list[str]) -> list[str]:
    # 下一步只列证据动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_controlled_field_rerun_queue":
        return [f"Queue controlled field rerun request for evidence_ref={ref} with owner acknowledgement attached."]
    if status == "needs_owner_ack":
        return [f"Collect owner handoff acknowledgement JSON for evidence_ref={ref} before queueing rerun."]
    if status == "needs_acceptance_execution_handoff_backfill":
        return upstream_next or [f"Backfill supported callback review handoff package for evidence_ref={ref}."]
    if status == "evidence_ref_mismatch_rerun":
        return [f"Regenerate handoff and owner acknowledgement with one evidence_ref={ref}."]
    return ["Regenerate handoff intake without raw paths, credentials, runtime topics, hardware transport detail, unsafe material identifiers, control claims, or success claims."]


def _rerun_hint(status: str, evidence_ref: str) -> dict[str, Any]:
    # rerun hint 只给 PC operator 复跑，不访问 ROS graph、Nav2 或硬件。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "required": status != "ready_for_controlled_field_rerun_queue",
        "status": status,
        "safe_evidence_ref": ref,
        "commands": [
            "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py "
            f"--callback-review-decision-json <callback_review_decision.json> --evidence-ref {ref} --once-json",
            "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_handoff_intake.py "
            f"--handoff-json <callback_review_handoff.json> --owner-intake-json <owner_ack.json> --evidence-ref {ref} --once-json",
        ],
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(status: str, evidence_ref: str, source_status: str, ack_state: str, next_required: list[str]) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料内容。
    return {
        "schema": f"{INTAKE_SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "handoff_intake_status": status,
        "source_handoff_status": source_status,
        "owner_acknowledgement_state": ack_state,
        "evidence_boundary": INTAKE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "next_required_evidence": next_required,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_acceptance_execution_handoff_intake(
    handoff_json: str,
    owner_intake_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 handoff 和可选 owner ack，生成 handoff intake artifact。"""
    source_payload, source_load_issue = _load_json(handoff_json, "handoff_json")
    owner_payload, owner_load_issue = _load_json(owner_intake_json, "owner_intake")
    source = _find_source(source_payload) if source_payload else {}
    owner = _find_owner_ack(owner_payload) if owner_payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    owner_ref = _owner_ref(owner) if owner else ""
    evidence_ref_out = requested_ref or source_ref or owner_ref
    source_status = _source_status(source) if source else ""
    ack_state = _owner_ack_state(owner)
    upstream_handoff = _source_owner_handoff(source) if source else []
    upstream_next = _source_next_required(source) if source else []
    unsafe = (bool(source_payload) and _has_forbidden_copy(source)) or (bool(owner_payload) and _has_forbidden_copy(owner))
    success_claim = (bool(source_payload) and _has_success_claim(source)) or (bool(owner_payload) and _has_success_claim(owner))
    status, status_reasons = _intake_status(
        source_load_issue,
        owner_load_issue,
        source,
        requested_ref,
        source_ref,
        source_status,
        owner_ref,
        ack_state,
        unsafe,
        success_claim,
    )
    next_required = _next_required_evidence(status, evidence_ref_out, upstream_next)
    safe_rerun_hint = _rerun_hint(status, evidence_ref_out)
    owner_handoff_intake = _owner_handoff_intake(owner, ack_state, evidence_ref_out)
    owner_handoff = [
        {
            "owner": "Autonomy Algorithm Engineer",
            "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
            "action": "queue_controlled_field_rerun_only_after_real_materials" if status == "ready_for_controlled_field_rerun_queue" else "repair_handoff_intake_before_queueing",
            "safe_evidence_ref": evidence_ref_out or "<same_evidence_ref>",
            "source_handoff_status": source_status,
            "owner_acknowledgement_state": ack_state,
            "upstream_owner_handoff": upstream_handoff,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    ]
    safe_copy = _safe_copy(status, evidence_ref_out, source_status, ack_state, next_required)
    summary = {
        "schema": INTAKE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": status,
        "handoff_intake_status": status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "source_handoff_schema": _safe_text(source.get("schema", "")) if source else "",
        "source_handoff_status": source_status,
        "owner_acknowledgement_state": ack_state,
        "owner_handoff_intake": owner_handoff_intake,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "safe_rerun_hint": safe_rerun_hint,
        "same_evidence_ref_required": True,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This intake is metadata-only and does not read field material directories.",
            "Owner acknowledgement is not real route/elevator field_validation, HIL, delivery_result, or delivery_success.",
            "Keep not_proven, delivery_success=false, and primary_actions_enabled=false until real evidence exists.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": INTAKE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": status,
        "handoff_intake_status": status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "source_acceptance_execution_callback_review_handoff": {
            "load_issue": source_load_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "source_handoff_status": source_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(bool(source_payload) and _has_forbidden_copy(source)),
            "success_claim": bool(bool(source_payload) and _has_success_claim(source)),
        },
        "owner_acknowledgement": {
            "load_issue": owner_load_issue,
            "state": ack_state,
            "safe_evidence_ref": owner_ref,
            "unsafe_copy": bool(bool(owner_payload) and _has_forbidden_copy(owner)),
            "success_claim": bool(bool(owner_payload) and _has_success_claim(owner)),
        },
        "owner_handoff_intake": owner_handoff_intake,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "safe_rerun_hint": safe_rerun_hint,
        "safe_copy": safe_copy,
        "route_task_field_retest_acceptance_execution_handoff_intake_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "raw_field_material_content",
            "ros_graph",
            "nav2_runtime",
            "fixed_route_runtime",
            "hardware_transport",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device",
            "mobile_runtime",
            "robot_action",
            "field_rerun_execution",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_success_claim(artifact) or _has_success_claim(summary):
        # 最终防线只拦截动作/成功声明；禁词已在入口 fail closed。
        artifact["status"] = "blocked_unsafe_handoff_intake"
        artifact["handoff_intake_status"] = "blocked_unsafe_handoff_intake"
        summary["status"] = "blocked_unsafe_handoff_intake"
        summary["handoff_intake_status"] = "blocked_unsafe_handoff_intake"
        artifact["route_task_field_retest_acceptance_execution_handoff_intake_summary"] = summary
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
    # CLI dependency-free，便于 PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate a route/task field retest acceptance execution handoff intake artifact")
    parser.add_argument("--handoff-json", required=True, help="callback review handoff artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--owner-intake-json", default="", help="optional owner callback/intake acknowledgement JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this handoff intake")
    parser.add_argument("--output", default="", help="optional handoff intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print handoff intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_acceptance_execution_handoff_intake(
        args.handoff_json,
        args.owner_intake_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_acceptance_execution_handoff_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_execution_handoff_intake_summary_file: {_safe_ref(args.summary_output)}")
        print(f"handoff_intake_status: {artifact['handoff_intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
