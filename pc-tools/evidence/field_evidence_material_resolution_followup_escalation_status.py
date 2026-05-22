#!/usr/bin/env python3
"""生成 field_evidence_material_resolution_followup_escalation_status PC gate。

该 CLI 只消费上一轮 field_evidence_material_resolution_review_handoff 的
脱敏 artifact、summary 或 Robot alias JSON。输出只表示 handoff 已发出，但
真实 owner response material 仍 missing / pending / overdue / escalated；它不是
field pass、terminal result、PR #5 reviewer resolution、HIL 或 delivery success。
"""

from __future__ import annotations

# 设计约束 01：只消费 review-handoff safe surface，不读取 raw artifact。
# 设计约束 02：本 capability/schema/boundary 与旧 real-material followup 完全分离。
# 设计约束 03：handoff sent 只表示 owner 已被路由，不表示 owner 已回复真实材料。
# 设计约束 04：safe evidence_ref 是 followup 与 handoff 串联的唯一主键。
# 设计约束 05：43a3f01 / a384c84 只作为 lineage，不作为真实材料证据。
# 设计约束 06：PR #5 comment 3269642220 只表示 software-proof reply 已发布。
# 设计约束 07：PRRT_kwDOSWB9286CJ3tX 必须保持 unresolved / hardware_material_pending。
# 设计约束 08：source=software_proof、not_proven 与三个 false flags 固定不变。
# 设计约束 09：缺输入、坏 schema、弱 evidence_ref 或 unsafe copy 均 fail closed。
# 设计约束 10：输出只给 owner/CEO escalation，不生成 robot control/action 建议。
# 设计约束 11：summary 是 Robot/mobile 唯一建议消费面，不携带 raw 上游对象。
# 设计约束 12：CLI 不访问 ROS graph、GitHub live API、外部云、硬件或真实手机。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_material_resolution_review_handoff as handoff_gate


SCHEMA = "trashbot.field_evidence_material_resolution_followup_escalation_status.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_material_resolution_followup_escalation_status_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_material_resolution_followup_escalation_status"
SOURCE_CAPABILITY = handoff_gate.CAPABILITY
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate"
SOURCE_BOUNDARY = handoff_gate.EVIDENCE_BOUNDARY

PREVIOUS_HANDOFF_COMMIT = "43a3f01"
PREVIOUS_REVIEW_DECISION_COMMIT = "a384c84"
PR5_THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"
PR5_COMMENT_ID = "3269642220"

SUPPORTED_SOURCE_SCHEMAS = {
    handoff_gate.SCHEMA,
    handoff_gate.SUMMARY_SCHEMA,
    handoff_gate.ROBOT_ALIAS,
    f"trashbot.{handoff_gate.ROBOT_ALIAS}.v1",
}

WRAPPER_KEYS = (
    "field_evidence_material_resolution_review_handoff",
    "field_evidence_material_resolution_review_handoff_summary",
    handoff_gate.ROBOT_ALIAS,
    "robot_diagnostics_summary",
    "summary",
    "artifact",
    "payload",
    "data",
    "diagnostics",
    "latest_status",
    "safe_copy",
)

PENDING_STATUS = "pending_owner_response_not_proven"
OVERDUE_STATUS = "overdue_owner_response_not_proven"
ESCALATED_STATUS = "escalated_for_owner_action_not_proven"
BLOCKED_STATUS = "blocked_missing_or_unsafe_review_handoff_followup_not_proven"
FOLLOWUP_STATUSES = (PENDING_STATUS, OVERDUE_STATUS, ESCALATED_STATUS, BLOCKED_STATUS)

SAFE_EVIDENCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,100}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\b\.\.?/|/dev/|/Users/|/tmp/|/var/|/home/|/ws/)")

FORBIDDEN_KEY_TERMS = (
    "raw_artifact",
    "raw_artifacts",
    "raw_body",
    "raw_payload",
    "raw_fields",
    "raw_materials",
    "raw_log",
    "artifact_path",
    "local_path",
    "file_path",
    "credential",
    "credentials",
    "token",
    "secret",
    "password",
    "authorization",
    "signed_url",
    "ros_topic",
    "ros_service",
    "ros_action",
    "cmd_vel",
    "serial_device",
    "uart_device",
    "wave_rover_feedback",
    "verified_terminal_result",
    "reviewer_resolution",
    "review_thread_resolved",
    "field_pass",
    "hil_pass",
    "cloud_proof",
    "phone_proof",
)

UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bnot_proven\s*[:=]\s*false\b"),
    re.compile(r"(?i)\b(hil_pass|field_pass|delivery_pass|verified_terminal_result)\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel|terminal result)\s+(success|succeeded|completed|complete|verified)\b"),
    re.compile(r"(?i)\b(PRRT_[A-Za-z0-9]+.*resolved|reviewer.*resolved|github.*resolved)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART device|serial device|baudrate|GPIO|voltage|firmware)\b"),
    re.compile(r"(?i)\b(real phone proof|true phone proof|cloud proof|field pass|HIL pass)\b"),
)

OWNER_RESPONSE_MATERIALS = (
    "owner response material",
    "real terminal delivery/dropoff/cancel result material",
    "real public HTTPS/TLS, 4G/SIM, OSS/CDN, DB/queue, or worker evidence",
    "true phone/browser evidence",
    "real route/elevator field pass evidence",
    "real hardware/HIL evidence",
    "PR #5 reviewer resolution material",
)

BOUNDARY_NOTE = (
    "field_evidence_material_resolution_followup_escalation_status; "
    "software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate; "
    "source=software_proof; not_proven; owner response material missing; "
    "delivery_success=false; primary_actions_enabled=false; safe_to_control=false; "
    "escalate without claiming field/cloud/phone/HIL/PR resolution proof"
)


def _utc_now() -> str:
    # UTC 时间让 PC gate 产物跨机器可稳定比对。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每层重复 false flags，避免下游消费局部字段时误启控制。
    return {
        "source": SOURCE,
        "status": STATUS,
        "software_proof": True,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _encoded(value: Any) -> str:
    # 稳定 JSON 字符串用于递归安全扫描，覆盖嵌套 key/value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 自由文本只保留短摘要，避免 raw log 或多行 artifact 穿透。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:240] or default


def _safe_list(value: Any, limit: int = 24) -> list[str]:
    # 列表字段只输出短文本，且过滤本机路径类片段。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            text = _safe_text(item.get("name") or item.get("material") or item.get("summary") or item.get("reason"))
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text):
            result.append(text)
    return list(dict.fromkeys(result))


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object，字符串化 JSON 不自动展开。
    return value if isinstance(value, dict) else {}


def _read_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入或坏 JSON 不抛 traceback，统一变成 blocked status。
    if not path:
        return {}, "review_handoff_input_not_provided"
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "review_handoff_input_missing"
    except json.JSONDecodeError:
        return {}, "review_handoff_input_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "review_handoff_input_read_error"
    if not isinstance(payload, dict):
        return {}, "review_handoff_input_not_object"
    return payload, ""


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归常见 safe wrapper key，不把任意 raw payload 当作 source。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 schema/capability 命中的 review-handoff artifact/summary/alias。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SUPPORTED_SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


def _boundary(payload: dict[str, Any]) -> str:
    # source boundary 可以在 evidence_boundary 或 boundary 字段中出现。
    return _safe_text(payload.get("evidence_boundary") or payload.get("boundary"))


def _source_ref(payload: dict[str, Any]) -> tuple[str, list[str]]:
    # evidence_ref 必须短、稳定、非路径；多个 ref 不一致直接 blocked。
    refs = []
    for candidate in _candidates(payload):
        for key in ("safe_evidence_ref", "evidence_ref"):
            text = _safe_text(candidate.get(key))
            if text:
                refs.append(text)
    unique_refs = list(dict.fromkeys(refs))
    reasons: list[str] = []
    for ref in unique_refs:
        if not SAFE_EVIDENCE_REF_RE.fullmatch(ref) or PATH_LIKE_RE.search(ref):
            reasons.append("unsafe_evidence_ref")
    if len(unique_refs) > 1:
        reasons.append("evidence_ref_mismatch")
    return (unique_refs[0] if unique_refs and not reasons else ""), list(dict.fromkeys(reasons))


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 字段名命中 raw/control/credential/proof-claim 类别时拒绝，不回显敏感值。
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            if any(term in key_text.lower() for term in FORBIDDEN_KEY_TERMS):
                paths.append(key_path)
            paths.extend(_unsafe_key_paths(child, key_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_unsafe_key_paths(child, f"{prefix}[{index}]"))
    return paths


def _truthy_false_flags(value: Any) -> list[str]:
    # 输入任何层把 false-state flag 改成 true，都不能进入 followup escalation。
    reasons: list[str] = []
    if isinstance(value, dict):
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control"):
            if value.get(key) is True:
                reasons.append(f"{key}_true_overclaim")
        for child in value.values():
            reasons.extend(_truthy_false_flags(child))
    elif isinstance(value, list):
        for child in value:
            reasons.extend(_truthy_false_flags(child))
    elif isinstance(value, str):
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control"):
            if re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value):
                reasons.append(f"{key}_true_overclaim")
    return reasons


def _unsafe_reasons(value: dict[str, Any]) -> list[str]:
    # 只输出类别原因，不把命中的原始片段带进 blocked artifact。
    reasons: list[str] = []
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_control_credential_path_resolution_or_proof_fields")
    encoded = _encoded(value)
    if PATH_LIKE_RE.search(encoded) or any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS):
        reasons.append("unsafe_path_credential_ros_control_hardware_success_or_resolution_claim")
    reasons.extend(_truthy_false_flags(value))
    return list(dict.fromkeys(reasons))


def _source_is_software_not_proven(source: dict[str, Any]) -> bool:
    # source 合同必须保持 software_proof / not_proven / false flags。
    encoded = _encoded(source)
    return (
        _safe_text(source.get("source")) == SOURCE
        and "not_proven" in encoded
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
        and source.get("safe_to_control") is False
    )


def _schema_supported(normalized: dict[str, Any]) -> bool:
    # review-handoff family schema 或 capability 命中，并且边界必须是上一轮 gate。
    if normalized["schema"] in SUPPORTED_SOURCE_SCHEMAS and normalized["source_boundary"] in {"", SOURCE_BOUNDARY}:
        return True
    if normalized["source_capability"] == SOURCE_CAPABILITY and normalized["source_boundary"] == SOURCE_BOUNDARY:
        return True
    return False


def _normalize_source(payload: dict[str, Any], read_issue: str) -> dict[str, Any]:
    # normalized 是唯一参与决策的数据面，输出不会直接引用输入原对象。
    source = _find_source(payload) if payload else {}
    safe_ref, ref_errors = _source_ref(source) if source else ("", [])
    source_handoff = _safe_text(source.get("handoff_status") or source.get("field_evidence_material_resolution_review_handoff")).lower()
    owner_handoff = _dict(source.get("owner_handoff"))
    material_summary = _dict(source.get("material_status_summary"))
    missing = _safe_list(
        source.get("missing_required_materials")
        or material_summary.get("missing_required_materials")
        or material_summary.get("missing_materials")
        or source.get("next_required_evidence")
    )
    reasons = _safe_list(source.get("handoff_reasons"))
    return {
        "read_issue": read_issue,
        "source": source,
        "schema": _safe_text(source.get("schema")),
        "source_boundary": _boundary(source),
        "source_capability": _safe_text(source.get("capability")),
        "source_handoff_status": source_handoff,
        "safe_evidence_ref": safe_ref,
        "ref_errors": ref_errors,
        "same_evidence_ref_required": source.get("same_evidence_ref_required", True),
        "source_owner_action": _safe_text(owner_handoff.get("owner_next_action")),
        "missing_required_materials": missing,
        "handoff_reasons": reasons,
        "unsafe_reasons": _unsafe_reasons(source) if source else [],
        "source_is_software_not_proven": _source_is_software_not_proven(source) if source else False,
    }


def _followup_status(normalized: dict[str, Any], due_status: str) -> tuple[str, list[str]]:
    # fail-closed 优先级：缺输入/不支持 -> unsafe -> weak ref -> handoff sent。
    if normalized["read_issue"]:
        return BLOCKED_STATUS, [normalized["read_issue"]]
    if not _schema_supported(normalized):
        return BLOCKED_STATUS, ["unsupported_resolution_review_handoff_schema_or_boundary"]
    if normalized["unsafe_reasons"]:
        return BLOCKED_STATUS, normalized["unsafe_reasons"]
    if not normalized["source_is_software_not_proven"]:
        return BLOCKED_STATUS, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if normalized["ref_errors"] or not normalized["safe_evidence_ref"] or normalized["same_evidence_ref_required"] is not True:
        return BLOCKED_STATUS, normalized["ref_errors"] or ["missing_or_weak_same_evidence_ref"]
    if normalized["source_handoff_status"] != handoff_gate.HANDOFF_READY:
        return BLOCKED_STATUS, ["previous_handoff_not_ready_or_not_sent"]
    if due_status == "pending":
        return PENDING_STATUS, ["handoff_sent_owner_response_material_pending"]
    if due_status == "overdue":
        return OVERDUE_STATUS, ["handoff_sent_owner_response_material_overdue"]
    return ESCALATED_STATUS, ["handoff_sent_escalate_owner_response_material_missing"]


def _next_required(status: str, normalized: dict[str, Any]) -> list[str]:
    # next_required_evidence 只描述补证/升级动作，不描述机器人命令。
    if status == BLOCKED_STATUS:
        return ["provide_supported_field_evidence_material_resolution_review_handoff_artifact_summary_or_robot_alias"]
    missing = normalized["missing_required_materials"] or list(OWNER_RESPONSE_MATERIALS)
    return list(dict.fromkeys(["owner response material"] + missing))


def _owner_escalation(status: str, due_status: str, normalized: dict[str, Any], next_required: list[str]) -> dict[str, Any]:
    # escalation 只面向 owner/CEO 决策，不触发 ACK、cursor 或 robot command。
    if status == BLOCKED_STATUS:
        owner_action = "resubmit_supported_safe_review_handoff_before_followup_escalation"
        ceo_action = "do_not_count_this_as_owner_followup_until_safe_handoff_is_available"
    elif status == PENDING_STATUS:
        owner_action = "collect_owner_response_material_under_same_safe_evidence_ref"
        ceo_action = "wait_for_owner_response_material_without_okr_lift"
    elif status == OVERDUE_STATUS:
        owner_action = "owner_response_material_is_overdue_escalate_to_material_owner"
        ceo_action = "escalate_owner_response_material_due_date"
    else:
        owner_action = "escalate_owner_response_material_missing_to_ceo_for_decision"
        ceo_action = "decide_owner_material_deadline_or_reprioritize_blocked_work"
    return {
        **_safe_flags(),
        "owner": "field_material_owner",
        "review_owner": "Product Manager / OKR Owner",
        "due_status": due_status if status != BLOCKED_STATUS else "blocked_missing_supported_handoff",
        "owner_response_material_status": "missing" if status != BLOCKED_STATUS else "blocked_unknown",
        "owner_action": owner_action,
        "ceo_escalation_recommendation": ceo_action,
        "next_required_evidence": next_required,
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "escalate": status in {OVERDUE_STATUS, ESCALATED_STATUS},
    }


def _safe_copy(status: str, normalized: dict[str, Any]) -> str:
    # safe_copy 是短文本白名单，便于 Robot/mobile 显示但不携带 raw artifact。
    ref = normalized["safe_evidence_ref"] or "blocked"
    return (
        f"{CAPABILITY}: followup_status={status}; evidence_ref={ref}; "
        f"lineage={PREVIOUS_HANDOFF_COMMIT}->{PREVIOUS_REVIEW_DECISION_COMMIT}; "
        f"PR #5 {PR5_THREAD_ID}=unresolved hardware_material_pending; "
        f"comment {PR5_COMMENT_ID}=software_proof reply only; "
        f"evidence_boundary={EVIDENCE_BOUNDARY}; source=software_proof; not_proven; "
        "owner response material missing; escalate; "
        "delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
    )


def build_field_evidence_material_resolution_followup_escalation_status(
    input_path: str,
    due_status: str = "escalated",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 followup escalation artifact 与 summary；任何状态都不代表真实完成。"""
    normalized_due_status = due_status if due_status in {"pending", "overdue", "escalated"} else "escalated"
    payload, read_issue = _read_json(input_path)
    normalized = _normalize_source(payload, read_issue)
    followup_status, reasons = _followup_status(normalized, normalized_due_status)
    next_required = _next_required(followup_status, normalized)
    owner_escalation = _owner_escalation(followup_status, normalized_due_status, normalized, next_required)
    generated_at = _utc_now()
    common = {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": normalized["schema"],
        "source_evidence_boundary": normalized["source_boundary"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "followup_status": followup_status,
        "allowed_followup_statuses": list(FOLLOWUP_STATUSES),
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "owner_response_material_status": owner_escalation["owner_response_material_status"],
        "due_status": owner_escalation["due_status"],
        "blocked_reason": ";".join(reasons),
        "followup_reasons": reasons,
        "next_required_evidence": next_required,
        "owner_escalation": owner_escalation,
        "lineage": {
            "previous_handoff": PREVIOUS_HANDOFF_COMMIT,
            "previous_review_decision": PREVIOUS_REVIEW_DECISION_COMMIT,
            "previous_handoff_capability": handoff_gate.CAPABILITY,
            "previous_review_decision_capability": handoff_gate.SOURCE_CAPABILITY,
        },
        "pr5_thread": {
            "thread_id": PR5_THREAD_ID,
            "state": "unresolved",
            "material_state": "hardware_material_pending",
            "comment_id": PR5_COMMENT_ID,
            "comment_status": "software_proof_reply_only_not_reviewer_resolution",
        },
        "safe_copy": _safe_copy(followup_status, normalized),
        "summary_alias": ROBOT_ALIAS,
        "fail_closed_flags": {
            "software_proof": True,
            "not_proven": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        },
        "safety_markers": [
            "software_proof",
            "not_proven",
            "owner response material missing",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
        ],
        "not_proven_items": list(OWNER_RESPONSE_MATERIALS),
        "boundary_note": BOUNDARY_NOTE,
    }
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "field_evidence_material_resolution_followup_escalation_status": followup_status,
        **common,
        "source_review_handoff": {
            "schema_supported": _schema_supported(normalized),
            "read_issue": read_issue,
            "source_handoff_status": normalized["source_handoff_status"],
            "source_is_software_proof_not_proven": normalized["source_is_software_not_proven"],
            "unsafe_reasons": normalized["unsafe_reasons"],
            "ref_errors": normalized["ref_errors"],
        },
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        "field_evidence_material_resolution_followup_escalation_status": followup_status,
        **common,
    }
    return artifact, summary, 0 if followup_status != BLOCKED_STATUS else 2


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint artifact diff 与人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只做本地 JSON gate，不提供 fetch、ACK、cursor 或 robot command。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.field_evidence_material_resolution_followup_escalation_status.v1 from a sanitized "
            "field_evidence_material_resolution_review_handoff artifact, summary, or Robot alias. Keeps "
            "source=software_proof, not_proven, owner response material missing, delivery_success=false, "
            "primary_actions_enabled=false, safe_to_control=false, and supports escalate status."
        )
    )
    parser.add_argument("--input", default="", help="sanitized resolution review handoff artifact, summary, or Robot alias JSON")
    parser.add_argument(
        "--due-status",
        choices=("pending", "overdue", "escalated"),
        default="escalated",
        help="owner response material due state to encode without proving completion",
    )
    parser.add_argument("--output", type=Path, help="optional path for sanitized followup escalation artifact JSON")
    parser.add_argument("--summary-output", type=Path, help="optional path for sanitized followup escalation summary JSON")
    parser.add_argument("--output-dir", type=Path, help="optional directory for default artifact and summary names")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_field_evidence_material_resolution_followup_escalation_status(
        args.input,
        args.due_status,
    )
    if args.output_dir:
        _write_json(args.output_dir / "field_evidence_material_resolution_followup_escalation_status.json", artifact)
        _write_json(args.output_dir / "field_evidence_material_resolution_followup_escalation_status_summary.json", summary)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if not (args.output_dir or args.output or args.summary_output):
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
