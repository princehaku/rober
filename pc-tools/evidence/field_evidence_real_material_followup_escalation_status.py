#!/usr/bin/env python3
"""生成 field_evidence_real_material_followup_escalation_status PC gate。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_real_material_response_review_handoff as handoff
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.field_evidence_real_material_followup_escalation_status.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_real_material_followup_escalation_status_summary.v1"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_real_material_followup_escalation_status"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_real_material_followup_escalation_status_gate"

# 只接受 17-18 response-review-handoff 安全 artifact / summary / Robot alias。
SOURCE_SCHEMAS = {handoff.HANDOFF_SCHEMA, handoff.HANDOFF_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {handoff.HANDOFF_BOUNDARY}

READY_STATUS = "escalated_for_field_owner_followup_not_proven"
BACKFILL_STATUS = "blocked_missing_field_material_followup_escalation_not_proven"
REJECTED_STATUS = "blocked_rejected_or_unsafe_handoff_followup_escalation_not_proven"
UNSUPPORTED_STATUS = "blocked_unsupported_field_material_followup_escalation_source"
MISMATCH_STATUS = "evidence_ref_mismatch_field_material_followup_escalation_blocked"

DEFAULT_EVIDENCE_REF = "field-real-material-followup-2026-05-21T18-00Z"
SAFE_EVIDENCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,96}$")

PR4_REVIEW_REF = "3269642220"
PR5_REVIEW_THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"
FOLLOWUP_DUE_STATUS = "overdue_pending_real_route_elevator_field_materials"

# 输出文字必须能被 rg 围栏和人工审计快速确认边界。
BOUNDARY_NOTE = (
    "field_evidence_real_material_followup_escalation_status; "
    "software_proof_docker_field_evidence_real_material_followup_escalation_status_gate; "
    "source=software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; "
    "route/elevator and delivery outcome remain unproven"
)

NOT_PROVEN_ITEMS = (
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_record",
    "real_field_task_record",
    "real_dropoff_completion_material",
    "real_cancel_completion_material",
    "real_delivery_result",
    "real_delivery_success",
)

DEFAULT_MISSING_EVIDENCE = (
    "real Nav2/fixed-route runtime log",
    "real route completion signal",
    "real field task record",
    "real elevator door state",
    "real target floor confirmation",
    "real human assistance record",
    "real dropoff completion material",
    "real cancel completion material",
    "real delivery result",
)

FORBIDDEN_COPY = (
    "Authorization",
    "OSS_ACCESS_KEY",
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
    "Traceback",
    "checksum",
    "complete artifact",
    "raw artifact",
)

SUCCESS_OR_CONTROL_PATTERNS = (
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\broute/elevator\s+(success|succeeded|passed|validated)\b"),
    re.compile(r"(?i)\bcontrol\s+(enabled|allowed|authorized)\b"),
)


# 设计约束 01：本 gate 只消费 handoff 安全 surface，不读 raw field material。
# 设计约束 02：source schema 与 boundary 必须同时匹配上一轮 handoff。
# 设计约束 03：Robot alias 只作为安全别名，不提升证据等级。
# 设计约束 04：输出只做 escalation status，不生成现场复跑结果。
# 设计约束 05：owner、SLA、next_action 和 missing_evidence 必须显式可审计。
# 设计约束 06：ready handoff 仍只代表可升级给现场 owner，不代表 field pass。
# 设计约束 07：backfill/rejected/blocked source 都要转成 fail-closed escalation。
# 设计约束 08：source=software_proof、not_proven 与 false flags 必须保留。
# 设计约束 09：evidence_ref mismatch 不能静默接收，避免混合证据号。
# 设计约束 10：不输出 raw ROS topic、控制通道、硬件串口或本机路径。
# 设计约束 11：不输出凭证、DB/queue URL、checksum 或完整 artifact 文案。
# 设计约束 12：success/control claim 必须 fail closed。
# 设计约束 13：summary 是 Robot/mobile 唯一建议消费面。
# 设计约束 14：blocked artifact 也保持 exit 0，便于 Docker-only 留痕。
# 设计约束 15：CLI dependency-free，不访问 ROS graph、外部云或真实手机。
# 设计约束 16：所有输出递归脱敏后再做最后安全扫描。
# 设计约束 17：PR #4 / PR #5 review refs 仅作为追责定位线索。
# 设计约束 18：本文件不新增硬件参数，因此不读取 vendor 细节。


def _utc_now() -> str:
    # UTC 让 PC gate artifact 在不同主机上都可按字面排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每层重复 false flags，避免下游只读局部对象时误启控制。
    return {
        "source": "software_proof",
        "status": "not_proven",
        "software_proof": True,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _encoded(value: Any) -> str:
    # 安全扫描使用稳定 JSON，覆盖所有嵌套 key/value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any) -> str:
    # 自由文本统一走既有 material_pack 脱敏逻辑，保持同家族风格。
    return material_pack._safe_text(value)


def _safe_list(value: Any, limit: int = 32) -> list[str]:
    # summary 只输出短文本列表，避免把完整 artifact 搬到 escalation status。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                text = _first_text(item.get("material_group"), item.get("material"), item.get("name"), item.get("action"))
            else:
                text = str(item if item is not None else "")
            safe = _safe_text(text).strip()
            if safe:
                items.append(safe)
        return items
    if value in (None, ""):
        return []
    text = _safe_text(value).strip()
    return [text] if text else []


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只信任 object wrapper，字符串化 JSON 不作为安全 source。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 Robot alias 字段位置不同。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺 source 时不能构造 ready escalation，只能说明 source 不可用。
    if not path:
        return {}, "handoff_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "handoff_json_missing"
    except json.JSONDecodeError:
        return {}, "handoff_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "handoff_json_read_error"
    if not isinstance(payload, dict):
        return {}, "handoff_json_not_object"
    return payload, ""


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 递归白名单 key 覆盖 artifact/summary/Robot alias，但不采信 raw payload。
    candidates = [payload]
    for key in (
        "field_evidence_real_material_followup_escalation_status",
        "field_evidence_real_material_followup_escalation_status_summary",
        "field_evidence_real_material_response_review_handoff",
        "field_evidence_real_material_response_review_handoff_summary",
        "robot_diagnostics_field_evidence_real_material_response_review_handoff_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
        "diagnostics",
        "latest_status",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 schema 命中的 handoff source；否则保留顶层解释 unsupported。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_schema(source: dict[str, Any]) -> str:
    # schema 单独抽取，便于 blocked reason 可读。
    return _safe_text(source.get("schema", "")).strip()


def _source_boundary(source: dict[str, Any]) -> str:
    # 兼容 evidence_boundary / boundary 两种既有字段。
    return _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双白名单，防止其他 gate 的 safe copy 越权。
    return _source_schema(source) in SOURCE_SCHEMAS and _source_boundary(source) in SOURCE_BOUNDARIES


def _source_ref(source: dict[str, Any]) -> str:
    # evidence_ref 是 handoff 到 escalation 的唯一串联主键。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return material_pack._safe_ref(
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


def _requested_ref(value: str, source_ref: str) -> tuple[str, str]:
    # CLI evidence_ref 允许为空；非空时必须短文本且不能路径化。
    ref = str(value or source_ref or DEFAULT_EVIDENCE_REF).strip()
    if not SAFE_EVIDENCE_REF_RE.fullmatch(ref):
        return "", "unsafe_evidence_ref_format"
    return material_pack._safe_ref(ref), ""


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 字符串 true 不接受，避免弱 typing 绕过同证据号要求。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return source.get(
        "same_evidence_ref_required",
        safe_copy.get("same_evidence_ref_required", robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", True))),
    )


def _source_status(source: dict[str, Any]) -> str:
    # handoff_status 是业务映射核心，其他 status 只作兜底解释。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(_first_text(source.get("handoff_status"), safe_copy.get("handoff_status"), source.get("status"), default="")).strip()


def _source_software_not_proven(source: dict[str, Any]) -> bool:
    # 五个边界字段必须同时满足，不能只靠 schema 判断安全。
    safe_copy = _dict(source, "safe_copy")
    encoded = _encoded(source)
    source_text = _first_text(source.get("source"), safe_copy.get("source"), default="")
    return (
        source_text == "software_proof"
        and "not_proven" in encoded
        and source.get("safe_to_control", safe_copy.get("safe_to_control")) is False
        and source.get("delivery_success", safe_copy.get("delivery_success")) is False
        and source.get("primary_actions_enabled", safe_copy.get("primary_actions_enabled")) is False
    )


def _has_unsafe_copy(value: Any) -> bool:
    # 输入里若夹带凭证、路径、raw artifact 或 success claim，就不能生成 ready escalation。
    encoded = _encoded(value)
    return (
        any(token in encoded for token in FORBIDDEN_COPY)
        or any(pattern.search(encoded) for pattern in SUCCESS_OR_CONTROL_PATTERNS)
        or material_pack._has_raw_path_copy(value)
        or material_pack._has_success_or_control_claim(value)
    )


def _source_missing_evidence(source: dict[str, Any]) -> list[str]:
    # 上游 handoff 缺项优先；为空时回落到 route/elevator 稳定缺口清单。
    safe_copy = _dict(source, "safe_copy")
    for key in ("next_required_evidence", "missing_required_materials"):
        items = _safe_list(source.get(key))
        if items:
            return items
        items = _safe_list(safe_copy.get(key))
        if items:
            return items
    return list(DEFAULT_MISSING_EVIDENCE)


def _source_blocked_reason(source: dict[str, Any], load_issue: str) -> str:
    # blocked reason 只取短安全字段；缺失时给出可行动解释。
    if load_issue:
        return load_issue
    safe_copy = _dict(source, "safe_copy")
    reason = _safe_text(_first_text(source.get("blocked_reason"), safe_copy.get("blocked_reason"), default="")).strip()
    return reason or "route_elevator_field_materials_remain_missing_from_safe_handoff_source"


def _status_for_source(
    *,
    load_issue: str,
    source: dict[str, Any],
    source_ref: str,
    requested_ref: str,
    ref_error: str,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏 source 落入 ready escalation。
    if ref_error:
        return MISMATCH_STATUS, [ref_error]
    if load_issue:
        return UNSUPPORTED_STATUS, [load_issue]
    if _has_unsafe_copy(source):
        return REJECTED_STATUS, ["unsafe_or_success_control_claim_in_handoff_source"]
    if not _schema_supported(source):
        return UNSUPPORTED_STATUS, ["unsupported_handoff_schema_or_boundary"]
    if not _source_software_not_proven(source):
        return UNSUPPORTED_STATUS, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if _same_ref_required(source) is not True:
        return MISMATCH_STATUS, ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return MISMATCH_STATUS, ["safe_evidence_ref_missing"]
    if requested_ref != source_ref:
        return MISMATCH_STATUS, [f"requested_ref:{requested_ref}!={source_ref}"]

    handoff_status = _source_status(source)
    if handoff_status == handoff.READY_HANDOFF:
        return READY_STATUS, ["handoff_ready_but_still_requires_real_material_followup"]
    if handoff_status == handoff.BACKFILL_HANDOFF:
        return BACKFILL_STATUS, ["handoff_requires_missing_material_backfill"]
    if handoff_status in (handoff.REJECTED_HANDOFF, handoff.BLOCKED_HANDOFF):
        return REJECTED_STATUS, [f"handoff_status:{handoff_status}"]
    return REJECTED_STATUS, ["unknown_handoff_status"]


def _owner_escalation_items(evidence_ref: str, missing_evidence: list[str], blocked_reason: str) -> list[dict[str, Any]]:
    # owner/SLA/next_action 拆成现场 owner 可直接执行的三组，不启用任何机器人动作。
    owner_specs = (
        (
            ""robot-algorithm-engineer"",
            "Autonomy Algorithm Engineer",
            "collect_route_elevator_runtime_materials_under_same_evidence_ref",
            missing_evidence,
        ),
        (
            "robot-software-engineer",
            "Robot Platform Engineer",
            "provide_readonly_task_record_dropoff_cancel_delivery_result_materials",
            [
                "real field task record",
                "real dropoff completion material",
                "real cancel completion material",
                "real delivery result",
            ],
        ),
        (
            "product-okr-owner",
            "Product Manager / OKR Owner",
            "escalate_owner_sla_when_real_materials_remain_missing",
            [
                "field owner signoff for missing route/elevator materials",
                "SLA decision for controlled field rerun materials",
                "explicit blocked reason if real environment remains unavailable",
            ],
        ),
    )
    items: list[dict[str, Any]] = []
    for owner_id, owner_name, next_action, evidence in owner_specs:
        items.append(
            {
                **_safe_flags(),
                "owner": owner_id,
                "owner_handoff": owner_name,
                "sla": "next_controlled_field_rerun_material_window_required",
                "due_status": FOLLOWUP_DUE_STATUS,
                "next_action": next_action,
                "missing_evidence": list(dict.fromkeys(evidence)),
                "blocked_reason": blocked_reason,
                "safe_evidence_ref": evidence_ref,
                "same_evidence_ref_required": True,
                "escalation_level": "field_owner_followup_required_before_any_route_elevator_claim",
            }
        )
    return items


def _safe_copy(
    escalation_status: str,
    reasons: list[str],
    evidence_ref: str,
    source_summary: dict[str, Any],
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    # safe_copy 是下游唯一复制面，保持短字段和明确 false flags。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        **_safe_flags(),
        "capability": CAPABILITY,
        "field_evidence_real_material_followup_escalation_status": escalation_status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_handoff": source_summary,
        "blocked_reason": ";".join(reasons),
        "owner_escalation_items": items,
        "next_action": "field_owners_supply_same_ref_real_materials_before_any_route_elevator_or_delivery_claim",
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "boundary_note": BOUNDARY_NOTE,
    }


def _summary_payload(
    escalation_status: str,
    reasons: list[str],
    evidence_ref: str,
    source_summary: dict[str, Any],
    items: list[dict[str, Any]],
    safe_copy: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    # summary 镜像 artifact 的稳定消费字段，供 Robot alias 和 mobile 只读展示。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        **_safe_flags(),
        "capability": CAPABILITY,
        "field_evidence_real_material_followup_escalation_status": escalation_status,
        "followup_status": escalation_status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_handoff": source_summary,
        "blocked_reason": ";".join(reasons),
        "owner_escalation_items": items,
        "owner_count": len(items),
        "review_refs": {"pr4_review_ref": PR4_REVIEW_REF, "pr5_thread_id": PR5_REVIEW_THREAD_ID},
        "next_action": "field_owners_supply_same_ref_real_materials_before_any_route_elevator_or_delivery_claim",
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "safe_copy": safe_copy,
        "boundary_note": BOUNDARY_NOTE,
    }


def build_field_evidence_real_material_followup_escalation_status(
    handoff_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 response-review-handoff safe source，生成 owner/SLA escalation 状态。"""
    payload, load_issue = _load_json(handoff_json)
    source = _find_source(payload) if payload else {}
    source_ref = _source_ref(source) if source else ""
    requested_ref, ref_error = _requested_ref(evidence_ref, source_ref)
    escalation_status, reasons = _status_for_source(
        load_issue=load_issue,
        source=source,
        source_ref=source_ref,
        requested_ref=requested_ref,
        ref_error=ref_error,
    )
    blocked_reason = _source_blocked_reason(source, load_issue)
    missing_evidence = _source_missing_evidence(source)
    source_summary = {
        "schema": _source_schema(source),
        "evidence_boundary": _source_boundary(source),
        "handoff_status": _source_status(source),
        "safe_evidence_ref": source_ref,
        "same_evidence_ref_required": _same_ref_required(source) if source else True,
        "source_is_software_proof_not_proven": _source_software_not_proven(source) if source else False,
        "blocked_reason": blocked_reason,
        "source_source": "field_evidence_real_material_response_review_handoff",
    }
    items = _owner_escalation_items(requested_ref, missing_evidence, blocked_reason)
    generated_at = _utc_now()
    safe_copy = _safe_copy(escalation_status, reasons, requested_ref, source_summary, items)
    summary = _summary_payload(escalation_status, reasons, requested_ref, source_summary, items, safe_copy, generated_at)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        **_safe_flags(),
        "capability": CAPABILITY,
        "field_evidence_real_material_followup_escalation_status": escalation_status,
        "followup_status": escalation_status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_handoff": source_summary,
        "blocked_reason": ";".join(reasons),
        "owner_escalation_items": items,
        "review_refs": {"pr4_review_ref": PR4_REVIEW_REF, "pr5_thread_id": PR5_REVIEW_THREAD_ID},
        "next_action": "field_owners_supply_same_ref_real_materials_before_any_route_elevator_or_delivery_claim",
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "safe_copy": safe_copy,
        "field_evidence_real_material_followup_escalation_status_summary": summary,
        "robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "non_access_scope": [
            "raw_field_materials",
            "real route/elevator runtime",
            "real delivery result",
            "real phone browser runtime",
            "robot control channels",
            "hardware serial or transport details",
            "host filesystem locations",
            "credential_or_database_queue_connection_material",
        ],
        "boundary_note": BOUNDARY_NOTE,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if _has_unsafe_copy(artifact) or _has_unsafe_copy(summary):
        # 最后一层防线：脱敏后仍不安全时保留 false flags 并切到 rejected。
        for output in (artifact, summary):
            output["field_evidence_real_material_followup_escalation_status"] = REJECTED_STATUS
            output["followup_status"] = REJECTED_STATUS
            output["blocked_reason"] = "unsafe_copy_after_sanitization"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 输出路径只用于落盘；payload 自身不回写绝对路径。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只做本地 JSON gate，可在 Docker-only 主机重复运行。
    parser = argparse.ArgumentParser(
        description=(
            "Generate field_evidence_real_material_followup_escalation_status software_proof gate; "
            "keeps not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false."
        )
    )
    parser.add_argument("--handoff-json", required=True, help="response-review-handoff artifact, summary, or Robot safe alias JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref for escalation status")
    parser.add_argument("--output", default="", help="optional escalation artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional escalation summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print escalation artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_real_material_followup_escalation_status(args.handoff_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_real_material_followup_escalation_status: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_real_material_followup_escalation_status_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"followup_status: {artifact['field_evidence_real_material_followup_escalation_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
