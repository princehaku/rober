#!/usr/bin/env python3
"""生成 field_evidence_material_resolution_review_handoff PC-only gate。

该 CLI 只消费上一轮 field_evidence_material_resolution_review_decision 的
脱敏 artifact、summary 或 Robot alias JSON。输出是 owner handoff package，
但仍然固定为 Docker-only software proof，不证明真实云、真实手机、真实路线/电梯、
HIL、terminal result、PR #5 resolution 或 delivery success。
"""

from __future__ import annotations

# 设计约束 01：只读取上一轮 review-decision 的 safe surface，不读取 raw 材料。
# 设计约束 02：ready handoff 只表示 owner 可接手复核，不表示路线/电梯现场通过。
# 设计约束 03：source=software_proof、not_proven 和三个 false flags 必须逐层固定。
# 设计约束 04：safe evidence_ref 是 owner handoff 的唯一串联主键，路径或混合 ref 要阻断。
# 设计约束 05：缺 source、坏 JSON、unsupported schema 也要产出 blocked artifact 便于留证。
# 设计约束 06：输入出现 success/control/cloud/phone/HIL/PR resolution claim 必须 fail closed。
# 设计约束 07：输出只带材料摘要与 owner action，不复制完整上游 artifact 或 raw body。
# 设计约束 08：handoff 不访问 ROS graph、Nav2 runtime、硬件、云、GitHub 或真实手机。
# 设计约束 09：exit code 只表达 PC gate handoff 状态，不表达真实 delivery result。
# 设计约束 10：中文注释保留证据边界，避免后续误把 handoff 写成 completion。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_material_resolution_review_decision as decision_gate


SCHEMA = "trashbot.field_evidence_material_resolution_review_handoff.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_material_resolution_review_handoff_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_field_evidence_material_resolution_review_handoff_summary"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_material_resolution_review_handoff"
SOURCE_CAPABILITY = decision_gate.CAPABILITY
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_material_resolution_review_handoff_gate"
SOURCE_BOUNDARY = decision_gate.EVIDENCE_BOUNDARY

SUPPORTED_SOURCE_SCHEMAS = {
    decision_gate.SCHEMA,
    decision_gate.SUMMARY_SCHEMA,
    decision_gate.ROBOT_ALIAS,
    f"trashbot.{decision_gate.ROBOT_ALIAS}.v1",
}

WRAPPER_KEYS = (
    "field_evidence_material_resolution_review_decision",
    "field_evidence_material_resolution_review_decision_summary",
    decision_gate.ROBOT_ALIAS,
    "robot_diagnostics_summary",
    "summary",
    "artifact",
    "payload",
    "data",
    "diagnostics",
    "latest_status",
    "safe_copy",
)

HANDOFF_READY = "ready_for_owner_handoff_not_proven"
HANDOFF_BACKFILL = "needs_more_evidence_owner_handoff_not_proven"
HANDOFF_REJECTED = "rejected_unsafe_resolution_owner_handoff_not_proven"
HANDOFF_BLOCKED = "blocked_missing_review_decision_handoff_not_proven"
HANDOFF_STATUSES = (HANDOFF_READY, HANDOFF_BACKFILL, HANDOFF_REJECTED, HANDOFF_BLOCKED)

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
    "log_path",
    "complete_artifact",
    "checksum",
    "credential",
    "credentials",
    "token",
    "secret",
    "password",
    "authorization",
    "access_key",
    "api_key",
    "cookie",
    "db_url",
    "database_url",
    "queue_url",
    "signed_url",
    "ack",
    "cursor",
    "control_command",
    "cmd_vel",
    "twist",
    "ros_topic",
    "ros_service",
    "ros_action",
    "serial_device",
    "uart",
    "wave_rover",
    "esp32",
    "orange_pi",
    "baudrate",
    "voltage",
    "pin",
    "wiring",
    "firmware",
    "pr5_resolution",
    "reviewer_resolution",
    "review_thread_resolved",
    "verified_terminal_result",
)

UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(hil_pass|field_pass|delivery_pass|verified_terminal_result)\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel|terminal result)\s+(success|succeeded|completed|complete|verified)\b"),
    re.compile(r"(?i)\b(PRRT_[A-Za-z0-9]+.*resolved|reviewer.*resolved|github.*resolved)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART|baudrate|GPIO|voltage|firmware|serial)\b"),
)

BLOCKED_CATEGORIES = {
    "external_cloud": "missing_real_public_https_tls_4g_oss_cdn_db_queue_or_worker_evidence",
    "terminal_result": "missing_verified_terminal_delivery_dropoff_or_cancel_result",
    "phone_browser": "missing_true_phone_device_or_browser_acceptance",
    "field_route_elevator": "missing_real_nav2_fixed_route_runtime_or_route_elevator_field_pass",
    "hardware_hil": "missing_real_hardware_wave_rover_uart_or_hil_pass",
    "pr5": "PRRT_kwDOSWB9286CJ3tX_unresolved_hardware_material_pending",
}

NOT_PROVEN_ITEMS = tuple(BLOCKED_CATEGORIES.values()) + (
    "delivery_success",
    "dropoff_or_cancel_completion",
    "primary_robot_action_enablement",
)

BOUNDARY_NOTE = (
    "field_evidence_material_resolution_review_handoff; "
    "software_proof_docker_field_evidence_material_resolution_review_handoff_gate; "
    "source=software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false"
)


def _utc_now() -> str:
    # UTC 时间戳让 Docker-only evidence 在跨机器收口时可稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每层输出重复 false flags，避免下游只读局部对象时误启用动作。
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
    # 递归安全扫描用稳定 JSON，覆盖 nested key 与 value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 输出短文本，不把日志、多行原文或完整 JSON 带给 Robot/mobile。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:240] or default


def _safe_list(value: Any, limit: int = 24) -> list[str]:
    # material/status 列表只保留短摘要，防止 raw artifact body 穿透。
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


def _read_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转为 blocked handoff，不抛 traceback。
    if not path:
        return {}, "review_decision_input_not_provided"
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "review_decision_input_missing"
    except json.JSONDecodeError:
        return {}, "review_decision_input_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "review_decision_input_read_error"
    if not isinstance(payload, dict):
        return {}, "review_decision_input_not_object"
    return payload, ""


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object；字符串 JSON 不自动展开，避免绕过 safe summary。
    return value if isinstance(value, dict) else {}


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归常见 safe wrapper key，不把任意 raw payload 都当 source。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 schema/capability 命中的 review-decision artifact/summary/alias。
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
    # 字段名命中 raw/control/credential/hardware 类别时拒绝，不回显敏感值。
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
    # 输入任何层把 false-state flag 改成 true，都不能进入 owner handoff。
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
    # 只输出类别原因，不输出命中的原始片段，保持 blocked artifact 脱敏。
    reasons: list[str] = []
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_control_credential_hardware_or_resolution_fields")
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
    # review-decision family schema 或 capability 命中，并且边界必须是上一轮 gate。
    if normalized["schema"] in SUPPORTED_SOURCE_SCHEMAS and normalized["source_boundary"] in {"", SOURCE_BOUNDARY}:
        return True
    if normalized["source_capability"] == SOURCE_CAPABILITY and normalized["source_boundary"] == SOURCE_BOUNDARY:
        return True
    return False


def _normalize_source(payload: dict[str, Any], read_issue: str) -> dict[str, Any]:
    # normalized 是唯一参与决策的数据面，输出不会直接引用输入原对象。
    source = _find_source(payload) if payload else {}
    safe_ref, ref_errors = _source_ref(source) if source else ("", [])
    material_summary = _dict(source.get("material_status_summary"))
    accepted = _safe_list(material_summary.get("accepted_materials") or source.get("accepted_material_refs"))
    missing = _safe_list(material_summary.get("missing_materials") or source.get("missing_required_materials") or source.get("next_required_evidence"))
    rejected = _safe_list(material_summary.get("rejected_materials") or source.get("rejected_material_refs"))
    blocked = _safe_list(material_summary.get("blocked_materials") or source.get("blocked_material_refs"))
    source_decision = _safe_text(source.get("decision") or source.get("field_evidence_material_resolution_review_decision")).lower()
    return {
        "read_issue": read_issue,
        "source": source,
        "schema": _safe_text(source.get("schema")),
        "source_boundary": _boundary(source),
        "source_capability": _safe_text(source.get("capability")),
        "source_decision": source_decision,
        "safe_evidence_ref": safe_ref,
        "ref_errors": ref_errors,
        "same_evidence_ref_required": source.get("same_evidence_ref_required", True),
        "accepted_material_refs": accepted,
        "missing_required_materials": missing,
        "rejected_material_refs": rejected,
        "blocked_material_refs": blocked,
        "unsafe_reasons": _unsafe_reasons(source) if source else [],
        "source_is_software_not_proven": _source_is_software_not_proven(source) if source else False,
    }


def _handoff_status(normalized: dict[str, Any]) -> tuple[str, list[str]]:
    # fail-closed 优先级：缺输入/不支持 -> unsafe -> weak ref -> decision 映射。
    if normalized["read_issue"]:
        return HANDOFF_BLOCKED, [normalized["read_issue"]]
    if not _schema_supported(normalized):
        return HANDOFF_BLOCKED, ["unsupported_resolution_review_decision_schema_or_boundary"]
    if normalized["unsafe_reasons"]:
        return HANDOFF_REJECTED, normalized["unsafe_reasons"]
    if not normalized["source_is_software_not_proven"]:
        return HANDOFF_REJECTED, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if normalized["ref_errors"] or not normalized["safe_evidence_ref"] or normalized["same_evidence_ref_required"] is not True:
        return HANDOFF_BLOCKED, normalized["ref_errors"] or ["missing_or_weak_same_evidence_ref"]
    source_decision = normalized["source_decision"]
    if source_decision == decision_gate.DECISION_ACCEPTED:
        return HANDOFF_READY, ["review_decision_ready_for_owner_handoff_only"]
    if source_decision == decision_gate.DECISION_NEEDS_MORE:
        return HANDOFF_BACKFILL, ["review_decision_requires_more_real_evidence"]
    if source_decision == decision_gate.DECISION_REJECTED:
        return HANDOFF_REJECTED, ["review_decision_rejected_unsafe_resolution"]
    if source_decision == decision_gate.DECISION_BLOCKED:
        return HANDOFF_BLOCKED, ["review_decision_blocked_missing_resolution_intake"]
    return HANDOFF_REJECTED, ["unknown_resolution_review_decision"]


def _next_required(normalized: dict[str, Any], handoff_status: str, reasons: list[str]) -> list[str]:
    # next_required_evidence 只描述人工补证动作，不描述机器人命令。
    if handoff_status == HANDOFF_READY:
        return [
            "Product owner reviews the sanitized handoff package under the same safe evidence_ref.",
            "Collect real external, terminal-result, phone/browser, field route/elevator, hardware/HIL, or PR #5 evidence before any completion claim.",
        ]
    if handoff_status == HANDOFF_BACKFILL:
        return normalized["missing_required_materials"] or list(BLOCKED_CATEGORIES.values())
    if handoff_status == HANDOFF_REJECTED:
        return normalized["rejected_material_refs"] or reasons
    return ["provide_supported_field_evidence_material_resolution_review_decision_artifact_summary_or_robot_alias"]


def _owner_handoff(normalized: dict[str, Any], handoff_status: str, reasons: list[str], next_required: list[str]) -> dict[str, Any]:
    # handoff 只指向人工 owner，不触发 ACK、cursor、fetch 或 robot command。
    if handoff_status == HANDOFF_READY:
        owner_next_action = "review_sanitized_resolution_handoff_without_marking_delivery_or_pr5_resolved"
        role = "Product Manager / OKR Owner"
    elif handoff_status == HANDOFF_BACKFILL:
        owner_next_action = "request_missing_real_evidence_under_same_safe_evidence_ref"
        role = "field material owner"
    elif handoff_status == HANDOFF_REJECTED:
        owner_next_action = "resubmit_safe_review_decision_without_success_control_raw_or_hardware_claims"
        role = "Product Manager / OKR Owner"
    else:
        owner_next_action = "provide_supported_review_decision_before_handoff_can_continue"
        role = "Product Manager / OKR Owner"
    return {
        "role": role,
        "owner_next_action": owner_next_action,
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "handoff_reasons": reasons,
        "next_required_real_evidence": next_required,
        "not_delivery_result": True,
        "not_delivery_success": True,
        "not_pr5_resolution": True,
        "safe_to_control": False,
        "primary_actions_enabled": False,
    }


def _material_status_summary(normalized: dict[str, Any], handoff_status: str, reasons: list[str]) -> dict[str, Any]:
    # 只保留材料分类摘要，不复制上一轮 review decision 的完整 artifact。
    return {
        "source_review_decision": normalized["source_decision"],
        "accepted_material_refs": normalized["accepted_material_refs"],
        "missing_required_materials": normalized["missing_required_materials"],
        "rejected_material_refs": normalized["rejected_material_refs"],
        "blocked_material_refs": normalized["blocked_material_refs"],
        "accepted_count": len(normalized["accepted_material_refs"]),
        "missing_count": len(normalized["missing_required_materials"]),
        "rejected_count": len(normalized["rejected_material_refs"]),
        "blocked_count": len(normalized["blocked_material_refs"]),
        "blocked_or_rejected_reasons": reasons if handoff_status in {HANDOFF_BLOCKED, HANDOFF_REJECTED} else [],
    }


def _safe_copy(handoff_status: str, normalized: dict[str, Any]) -> str:
    # safe_copy 是短文本白名单，便于 Robot/mobile 显示但不携带 raw artifact。
    return (
        f"{CAPABILITY}: handoff_status={handoff_status}; "
        f"evidence_ref={normalized['safe_evidence_ref'] or 'blocked'}; "
        f"evidence_boundary={EVIDENCE_BOUNDARY}; source=software_proof; not_proven; "
        "delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
    )


def build_field_evidence_material_resolution_review_handoff(input_path: str) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 review-handoff artifact 与 summary；ready 也只是 not_proven。"""
    payload, read_issue = _read_json(input_path)
    normalized = _normalize_source(payload, read_issue)
    handoff_status, reasons = _handoff_status(normalized)
    next_required = _next_required(normalized, handoff_status, reasons)
    owner_handoff = _owner_handoff(normalized, handoff_status, reasons, next_required)
    material_summary = _material_status_summary(normalized, handoff_status, reasons)
    generated_at = _utc_now()
    common = {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": normalized["schema"],
        "source_evidence_boundary": normalized["source_boundary"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "handoff_status": handoff_status,
        "allowed_handoff_statuses": list(HANDOFF_STATUSES),
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "handoff_reasons": reasons,
        "material_status_summary": material_summary,
        "accepted_material_refs": normalized["accepted_material_refs"],
        "rejected_material_refs": normalized["rejected_material_refs"],
        "missing_required_materials": normalized["missing_required_materials"],
        "blocked_material_refs": normalized["blocked_material_refs"],
        "blocked_categories": BLOCKED_CATEGORIES,
        "next_required_evidence": next_required,
        "owner_handoff": owner_handoff,
        "safe_copy": _safe_copy(handoff_status, normalized),
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
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
        ],
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "boundary_note": BOUNDARY_NOTE,
    }
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "field_evidence_material_resolution_review_handoff": handoff_status,
        **common,
        "source_review_decision": {
            "schema_supported": _schema_supported(normalized),
            "read_issue": read_issue,
            "source_decision": normalized["source_decision"],
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
        **common,
    }
    return artifact, summary, 0 if handoff_status == HANDOFF_READY else 2


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint artifact diff 与人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 不提供 fetch、ACK、cursor 或 robot command，只处理本地 safe JSON。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.field_evidence_material_resolution_review_handoff.v1 from a sanitized "
            "field_evidence_material_resolution_review_decision artifact, summary, or Robot alias. Keeps "
            "source=software_proof, not_proven, delivery_success=false, primary_actions_enabled=false, "
            "safe_to_control=false."
        )
    )
    parser.add_argument("--input", default="", help="sanitized resolution review decision artifact, summary, or Robot alias JSON")
    parser.add_argument("--output", type=Path, help="optional path for sanitized handoff artifact JSON")
    parser.add_argument("--summary-output", type=Path, help="optional path for sanitized handoff summary JSON")
    parser.add_argument("--output-dir", type=Path, help="optional directory for default artifact and summary names")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_field_evidence_material_resolution_review_handoff(args.input)
    if args.output_dir:
        _write_json(args.output_dir / "field_evidence_material_resolution_review_handoff.json", artifact)
        _write_json(args.output_dir / "field_evidence_material_resolution_review_handoff_summary.json", summary)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if not (args.output_dir or args.output or args.summary_output):
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
