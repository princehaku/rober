#!/usr/bin/env python3
"""生成 field_evidence_rerun_execution_result_review_decision 的 fail-closed PC gate。

该 gate 只读上一轮 `field_evidence_rerun_execution_result_intake` artifact、
summary、Robot safe alias 或 wrapper/nested JSON，把 result intake 状态转成
metadata-only review decision。它不读取真实现场材料、不访问 ROS graph、Nav2 /
fixed-route runtime、serial/UART、WAVE ROVER、真实电梯、外部云、真实手机/browser，
也不调度机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DECISION_SCHEMA = "trashbot.field_evidence_rerun_execution_result_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_review_decision_summary.v1"
SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate"

SOURCE_SCHEMAS = {
    "trashbot.field_evidence_rerun_execution_result_intake.v1",
    "trashbot.field_evidence_rerun_execution_result_intake_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_intake_gate"
SOURCE_STATUSES = ("accepted", "missing", "rejected", "blocked")

DECISION_STATUSES = {
    "accepted_for_review": "accepted_for_field_evidence_rerun_execution_result_review_not_proven",
    "needs_material_backfill": "needs_material_backfill_field_evidence_rerun_execution_result_review_not_proven",
    "rejected": "rejected_field_evidence_rerun_execution_result_review_not_proven",
    "blocked": "blocked_field_evidence_rerun_execution_result_review_not_proven",
}

NOT_PROVEN = (
    "real_field_evidence_rerun_execution",
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_field_task_record",
    "real_elevator_door_summary",
    "real_target_floor_or_floor_arrival_summary",
    "real_human_assistance_summary",
    "real_dropoff_completion",
    "real_cancel_completion",
    "real_delivery_result",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_browser_evidence",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
    "pr_5_resolved",
    "pr_6_runtime_proof",
)

BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_review_decision; "
    "software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate; "
    "accepted_for_review; needs_material_backfill; rejected; blocked; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 位于 execution result intake 之后，只复核 safe summary。
# 设计约束 02：accepted_for_review 只表示可进入人工/产品复核，不表示现场通过。
# 设计约束 03：missing intake 必须转成 needs_material_backfill，等待 owner 补证。
# 设计约束 04：rejected intake 必须保持 rejected，不能自动升级为 blocked。
# 设计约束 05：blocked intake、坏输入或 unsafe copy 必须 fail closed。
# 设计约束 06：schema 与 evidence_boundary 必须双重匹配，避免旧 gate 混用。
# 设计约束 07：同一 safe evidence_ref 是链路主键，CLI 不一致即阻断。
# 设计约束 08：same_evidence_ref_required 必须是真布尔 true。
# 设计约束 09：same_evidence_ref_status 只接受 matched 或 ready。
# 设计约束 10：source=software_proof 与 not_proven 必须保留到输出。
# 设计约束 11：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 12：输入出现成功、通过、控制授权或主动作文案必须 blocked。
# 设计约束 13：raw path、credential、DB/queue URL、ROS topic、串口和硬件细节必须阻断。
# 设计约束 14：summary 是下游 canonical 消费面，不复制 raw artifact。
# 设计约束 15：wrapper/nested JSON 只沿白名单 key 递归，避免采信 raw payload。
# 设计约束 16：owner_handoff 只表达人工责任，不授权现场动作。
# 设计约束 17：next_required_evidence 只列补证或复核动作，不写完成措辞。
# 设计约束 18：reconciliation_hint 只说明下一轮入口，不做自动合并。
# 设计约束 19：blocked 也返回 exit code 0，方便把阻断证据落盘。
# 设计约束 20：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 21：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 22：safe_copy 保持白名单，不包含完整 artifact、材料正文或 secret。

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
    "db_url",
    "database_url",
    "queue_url",
    "ROS topic",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "serial",
    "UART",
    "baudrate",
    "baud_rate",
    "WAVE ROVER",
    "low-level control",
    "low_level_control",
    "motor command",
    "Traceback",
    "checksum",
    "complete artifact",
    "raw artifact",
    "raw robot response",
)

SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed|result)\b"),
    re.compile(r"(?i)\bfield\s+rerun\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bphone/browser\s+(success|succeeded|passed|validated)\b"),
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action)\b"),
    re.compile(r"(?i)\bcontrol\s+(enabled|allowed|granted|authorized)\b"),
    re.compile(r"(?i)\bO5\s+external\s+proof\b"),
    re.compile(r"(?i)\bPR\s*#?5\s+(resolved|closed|complete|completed)\b"),
    re.compile(r"(?i)\bPR\s*#?6\s+runtime\s+proof\b"),
)

RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"(?i)\bROS\s+topic\b"), "[REDACTED_ROS_TOPIC]"),
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
    (re.compile(r"(?i)raw artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 时间让不同 PC/Docker 主机产物可按字符串排序审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，blocked 分支也不回显敏感原文。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 被误填成本机路径时只保留 basename，避免路径扩散到 UI。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线，防止新增嵌套字段绕过局部 helper。
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
        if value.get("safe_to_control") is True or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都输出 fail-closed artifact，便于自动化留痕。
    if not path:
        return {}, "execution_result_intake_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "execution_result_intake_missing"
    except json.JSONDecodeError:
        return {}, "execution_result_intake_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "execution_result_intake_read_error"
    if not isinstance(payload, dict):
        return {}, "execution_result_intake_not_object"
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


def _list_text(value: Any, limit: int = 24) -> list[str]:
    # 下游摘要只接受扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        return [_safe_text(item).strip() for item in value[:limit] if isinstance(item, (str, int, float, bool)) and _safe_text(item).strip()]
    if value in (None, ""):
        return []
    if isinstance(value, (str, int, float, bool)):
        return [_safe_text(value).strip()]
    return []


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_intake",
        "field_evidence_rerun_execution_result_intake_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_intake_summary",
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
            candidates.extend(_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # summary 优先；artifact 也可直接消费，但必须符合 schema/boundary。
    candidates = _candidates(payload)
    for candidate in candidates:
        if str(candidate.get("schema", "")).strip() == "trashbot.field_evidence_rerun_execution_result_intake_summary.v1":
            return candidate
    for candidate in candidates:
        if str(candidate.get("schema", "")).strip() == "trashbot.field_evidence_rerun_execution_result_intake.v1":
            return candidate
    return payload


def _schema(source: dict[str, Any]) -> str:
    # schema 字段只用于契约判断和输出解释。
    return _safe_text(source.get("schema", "")).strip()


def _boundary(source: dict[str, Any]) -> str:
    # boundary 兼容 evidence_boundary / boundary 两种既有字段。
    return _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止旧 JSON 或其它 gate 混用。
    return _schema(source) in SOURCE_SCHEMAS and _boundary(source) == SOURCE_BOUNDARY


def _source_is_software_not_proven(source: dict[str, Any]) -> bool:
    # 上游必须明确 software_proof/not_proven，不能把真实通过口径塞进本 gate。
    encoded = _encoded(source)
    return source.get("source") == "software_proof" and "not_proven" in encoded


def _flags_ok(source: dict[str, Any]) -> bool:
    # 三个动作旗标必须显式保持关闭；缺字段按不合格处理。
    return (
        source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层或 safe_copy/diagnostics/mobile 取。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return _safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            default="",
        )
    )


def _source_status(source: dict[str, Any]) -> str:
    # result_intake_status 是上游状态主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("result_intake_status"),
            source.get("status"),
            safe_copy.get("result_intake_status"),
            safe_copy.get("status"),
            default="",
        )
    ).strip()


def _same_ref_status(source: dict[str, Any]) -> str:
    # same-evidence-ref 状态兼容字符串字段；非 matched/ready 都保守 blocked。
    safe_copy = _dict(source, "safe_copy")
    value = _first_text(source.get("same_evidence_ref_status"), safe_copy.get("same_evidence_ref_status"), default="")
    return _safe_text(value or "missing_evidence_ref").strip()


def _copy_probe(source: dict[str, Any]) -> dict[str, Any]:
    # 只扫描可能进入 safe summary 的字段，避免 artifact non_access_scope 枚举触发误伤。
    return {
        "status_reasons": source.get("status_reasons"),
        "owner_handoff": source.get("owner_handoff"),
        "next_required_evidence": source.get("next_required_evidence"),
        "reconciliation_hint": source.get("reconciliation_hint"),
        "blocker_summary": source.get("blocker_summary"),
        "material_summary": source.get("material_summary"),
        "safe_copy": source.get("safe_copy"),
    }


def _decision(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_status: str,
    same_ref_status: str,
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 accepted_for_review。
    if success_claim:
        return "blocked", ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked", ["unsafe_copy_detected"]
    if load_issue or not _schema_supported(source):
        return "blocked", [load_issue or "unsupported_execution_result_intake_schema_or_boundary"]
    if not _source_is_software_not_proven(source):
        return "blocked", ["source_not_software_proof_or_missing_not_proven"]
    if not _flags_ok(source):
        return "blocked", ["source_action_flags_not_false"]
    if source.get("same_evidence_ref_required", True) is not True:
        return "blocked", ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return "blocked", ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref != source_ref:
        return "blocked", [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref_status not in {"matched", "ready"}:
        return "blocked", [f"same_evidence_ref:{same_ref_status}"]
    if source_status not in SOURCE_STATUSES:
        return "blocked", [f"unsupported_result_intake_status:{source_status or 'missing'}"]
    if source_status == "accepted":
        return "accepted_for_review", ["result_intake_accepted_for_review_only"]
    if source_status == "missing":
        return "needs_material_backfill", ["result_intake_missing_requires_material_backfill"]
    if source_status == "rejected":
        return "rejected", ["result_intake_rejected"]
    return "blocked", ["result_intake_blocked"]


def _source_reasons(source: dict[str, Any]) -> list[str]:
    # 上游 status_reasons 只作为上下文，不改变本 gate 状态机优先级。
    blocker = _dict(source, "blocker_summary")
    return _list_text(source.get("status_reasons")) or _list_text(blocker.get("status_reasons"))


def _next_required_evidence(decision: str, evidence_ref: str, reasons: list[str]) -> list[str]:
    # 下一步只列补证或复核动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == "accepted_for_review":
        return [
            f"Route the accepted-for-review execution result intake for evidence_ref={ref} to owner review.",
            "Keep not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false until independent real evidence exists.",
        ]
    if decision == "needs_material_backfill":
        return [f"Backfill owner-safe execution result packet material for evidence_ref={ref} and rerun result intake before review."]
    if decision == "rejected":
        return [f"Correct rejected execution result packet material for evidence_ref={ref} before any owner review handoff."]
    return [
        f"Regenerate supported execution result intake summary for evidence_ref={ref}.",
        "Remove raw paths, credentials, ROS topics, serial/UART detail, WAVE ROVER fields, checksums, raw artifacts, tracebacks, control claims, or success claims.",
        *reasons[:4],
    ]


def _owner_handoff(decision: str, evidence_ref: str, source_owner: dict[str, Any]) -> dict[str, Any]:
    # owner_handoff 只分派人工 review 责任，不授权 Robot/mobile 控制面。
    ref = evidence_ref or "<same_evidence_ref>"
    actions = {
        "accepted_for_review": "review_owner_safe_execution_result_intake",
        "needs_material_backfill": "request_owner_safe_execution_result_material_backfill",
        "rejected": "return_execution_result_material_for_owner_correction",
        "blocked": "repair_result_intake_source_or_remove_unsafe_copy",
    }
    return {
        "owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "action": actions.get(decision, "repair_result_intake_source_or_remove_unsafe_copy"),
        "review_decision": decision,
        "safe_evidence_ref": ref,
        "source_owner_handoff": _safe_value(source_owner),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _reconciliation_hint(decision: str, evidence_ref: str) -> dict[str, Any]:
    # reconciliation hint 只描述人工 review 入口，不做自动状态合并。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "review_decision": decision,
        "safe_evidence_ref": ref,
        "next_gate": "field_evidence_rerun_execution_result_review_handoff" if decision == "accepted_for_review" else "field_evidence_rerun_execution_result_intake",
        "accepted_is_field_pass": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(decision: str, status: str, evidence_ref: str, source_status: str, same_ref_status: str, next_required: list[str]) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料正文。
    return {
        "schema": f"{DECISION_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": status,
        "review_decision": decision,
        "result_review_decision": decision,
        "source_result_intake_status": source_status,
        "evidence_boundary": DECISION_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "next_required_evidence": next_required,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_result_review_decision(result_intake_json: str, evidence_ref: str = "") -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 execution result-intake summary，生成 metadata-only review decision artifact。"""
    payload, load_issue = _load_json(result_intake_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    source_status = _source_status(source) if source else ""
    same_ref_status = _same_ref_status(source) if source else "missing_evidence_ref"
    source_owner = _dict(source, "owner_handoff") if source else {}
    copy_probe = _copy_probe(source) if source else {}
    unsafe = bool(payload) and _has_forbidden_copy(copy_probe)
    success_claim = bool(payload) and (_has_success_claim(copy_probe) or _has_success_claim(source))
    decision, decision_reasons = _decision(load_issue, source, requested_ref, source_ref, source_status, same_ref_status, unsafe, success_claim)
    source_reasons = _source_reasons(source) if source else []
    all_reasons = decision_reasons + [reason for reason in source_reasons if reason not in decision_reasons]
    status = DECISION_STATUSES[decision]
    next_required = _next_required_evidence(decision, evidence_ref_out, all_reasons)
    owner_handoff = _owner_handoff(decision, evidence_ref_out, source_owner)
    reconciliation_hint = _reconciliation_hint(decision, evidence_ref_out)
    safe_copy = _safe_copy(decision, status, evidence_ref_out, source_status, same_ref_status, next_required)
    blocker_summary = {
        "blocked": decision == "blocked",
        "review_decision": decision,
        "source_result_intake_status": source_status,
        "decision_reasons": all_reasons,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = {
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": status,
        "review_decision": decision,
        "result_review_decision": decision,
        "decision_reasons": all_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "source_result_intake_schema": _schema(source) if source else "",
        "source_result_intake_status": source_status,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "reconciliation_hint": reconciliation_hint,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "accepted_for_review only means metadata can enter owner review.",
            "This review decision does not prove real route/elevator field execution, Nav2 runtime, HIL, phone/browser proof, delivery_result, or delivery_success.",
            "Keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": DECISION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": status,
        "review_decision": decision,
        "result_review_decision": decision,
        "decision_reasons": all_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_execution_result_intake": {
            "load_issue": load_issue,
            "schema": _schema(source) if source else "",
            "evidence_boundary": _boundary(source) if source else "",
            "source_result_intake_status": source_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(bool(payload) and _has_forbidden_copy(copy_probe)),
            "success_claim": bool(bool(payload) and (_has_success_claim(copy_probe) or _has_success_claim(source))),
        },
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "reconciliation_hint": reconciliation_hint,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_result_review_decision_summary": summary,
        "robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "raw_field_material_content",
            "complete_artifact",
            "local_path",
            "checksum",
            "credentials",
            "db_queue_url",
            "ros_topic",
            "ros_graph",
            "nav2_runtime",
            "fixed_route_runtime",
            "serial_uart",
            "wave_rover",
            "external_cloud",
            "oss_cdn",
            "4g_network",
            "phone_device_browser_runtime",
            "robot_action",
            "field_rerun_execution",
            "field_pass_claim",
            "pr5_resolution",
            "pr6_runtime_proof",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_success_claim(artifact) or _has_success_claim(summary):
        # 最终防线只拦截动作/成功声明；non_access_scope 不能因此自我降级。
        artifact["status"] = DECISION_STATUSES["blocked"]
        artifact["review_decision"] = "blocked"
        artifact["result_review_decision"] = "blocked"
        summary["status"] = DECISION_STATUSES["blocked"]
        summary["review_decision"] = "blocked"
        summary["result_review_decision"] = "blocked"
        artifact["field_evidence_rerun_execution_result_review_decision_summary"] = summary
        artifact["robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary"] = summary
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
    # CLI 保持 dependency-free，便于 PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun execution result review decision artifact")
    parser.add_argument("--result-intake-json", required=True, help="execution result intake artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review decision")
    parser.add_argument("--output", default="", help="optional review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_review_decision(args.result_intake_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_review_decision: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_rerun_execution_result_review_decision_summary_file: {_safe_ref(args.summary_output)}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
