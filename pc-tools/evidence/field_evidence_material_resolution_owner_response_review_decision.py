#!/usr/bin/env python3
"""生成 field evidence material resolution owner response review decision。

该 PC-only gate 只消费上一轮
`field_evidence_material_resolution_owner_response_intake` 的 safe artifact、
summary 或 Robot alias。输出把 owner response material 归档为结构化 review
decision；accepted 仅表示 accepted_for_material_review_not_proven，不代表真实
cloud、phone、field pass、HIL、delivery success、PR #5 resolved 或 OKR lift。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_material_resolution_owner_response_intake as intake


SCHEMA = "trashbot.field_evidence_material_resolution_owner_response_review_decision.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_material_resolution_owner_response_review_decision_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_material_resolution_owner_response_review_decision"
SOURCE_CAPABILITY = intake.CAPABILITY
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate"
SOURCE_BOUNDARY = intake.EVIDENCE_BOUNDARY

ACCEPTED = "accepted_for_material_review_not_proven"
NEEDS_MORE = "needs_more_evidence_not_proven"
REJECTED_UNSAFE = "rejected_unsafe_material_response_not_proven"
BLOCKED_MISSING_INTAKE = "blocked_missing_owner_response_intake_not_proven"
REVIEW_DECISIONS = (ACCEPTED, NEEDS_MORE, REJECTED_UNSAFE, BLOCKED_MISSING_INTAKE)

# 设计约束 01：本 gate 只读上一轮 intake safe surface，不读取 raw 现场材料。
# 设计约束 02：schema 与 evidence boundary 必须同时命中上一轮 intake。
# 设计约束 03：同一 safe evidence_ref 是跨 intake / decision 的强约束。
# 设计约束 04：accepted 只表示可以进入后续 material review，不表示材料通过。
# 设计约束 05：missing materials 一律 needs_more_evidence，不静默 accepted。
# 设计约束 06：rejected/unsafe materials、success/control claim 一律 rejected。
# 设计约束 07：缺 source、坏 JSON、unsupported schema 一律 blocked missing intake。
# 设计约束 08：PR #5 thread X 固定 unresolved / hardware_material_pending。
# 设计约束 09：输出不包含 raw artifact、凭证、本机路径、ROS topic 或硬件细节。
# 设计约束 10：source=software_proof、not_proven 与三类 false flag 不可放松。
# 设计约束 11：CLI 只生成 JSON，不提供 ACK、GitHub resolve 或 robot command。
# 设计约束 12：所有技术注释使用中文，解释安全边界与参数取舍。
# 设计约束 13：summary 是 Robot/mobile 建议消费面，保持只读和 phone-safe。
# 设计约束 14：blocked artifact 也返回 0，方便 Docker-only sprint 留痕复核。

SOURCE_SCHEMAS = {
    intake.SCHEMA,
    intake.SUMMARY_SCHEMA,
    intake.ROBOT_ALIAS,
    f"trashbot.{intake.ROBOT_ALIAS}.v1",
}

WRAPPER_KEYS = (
    "field_evidence_material_resolution_owner_response_review_decision",
    "field_evidence_material_resolution_owner_response_review_decision_summary",
    "field_evidence_material_resolution_owner_response_intake",
    "field_evidence_material_resolution_owner_response_intake_summary",
    intake.ROBOT_ALIAS,
    "robot_diagnostics_summary",
    "mobile_readonly_summary",
    "safe_copy",
    "summary",
    "artifact",
    "payload",
    "data",
    "diagnostics",
    "latest_status",
)

SAFE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,100}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\b\.\.?/|/dev/|/Users/|/tmp/|/var/|/home/|/ws/)")
UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bnot_proven\s*[:=]\s*false\b"),
    re.compile(r"(?i)\b(hil_pass|field_pass|delivery_pass|verified_terminal_result)\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel|terminal result)\s+(success|succeeded|completed|complete|verified)\b"),
    re.compile(r"(?i)\b(PRRT_[A-Za-z0-9]+[^,;]{0,80}\bresolved\b|reviewer[^,;]{0,80}\bresolved\b|github[^,;]{0,80}\bresolved\b)"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART device|serial device|baudrate|GPIO|voltage|firmware)\b"),
    re.compile(r"(?i)\b(real phone proof|true phone proof|cloud proof|field proof|HIL proof)\b"),
)
FORBIDDEN_KEY_TERMS = (
    "raw_artifact",
    "raw_artifacts",
    "raw_body",
    "raw_payload",
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
    "cmd_vel",
    "ros_topic",
    "ros_service",
    "serial_device",
    "uart_device",
    "reviewer_resolution",
    "review_thread_resolved",
)


def _utc_now() -> str:
    # UTC 时间让 PC artifact 与 Docker proof 能按同一审计时间线排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # false flags 在 artifact/summary/safe_copy 中重复，避免局部消费误启控制。
    return {
        "source": SOURCE,
        "status": "not_proven",
        "software_proof": True,
        "not_proven": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _encoded(value: Any) -> str:
    # 稳定 JSON 字符串用于递归安全扫描，覆盖嵌套 key/value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 自由文本只保留短单行，避免 raw log 或多行 artifact 穿透。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:240] or default


def _safe_ref(value: Any) -> str:
    # evidence_ref 只能是短安全标识；路径、空值和弱字符串都拒绝。
    text = _safe_text(value)
    if text and SAFE_REF_RE.fullmatch(text) and not PATH_LIKE_RE.search(text):
        return text
    return ""


def _safe_list(value: Any, limit: int = 40) -> list[str]:
    # 列表字段只输出短文本，并过滤本机路径类片段。
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
    # wrapper 只接受 object，字符串化 JSON 不作为可信 safe source。
    return value if isinstance(value, dict) else {}


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转成可审计 blocked reason。
    if not path:
        return {}, "owner_response_intake_json_not_provided"
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "owner_response_intake_json_missing"
    except json.JSONDecodeError:
        return {}, "owner_response_intake_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "owner_response_intake_json_read_error"
    if not isinstance(payload, dict):
        return {}, "owner_response_intake_json_not_object"
    return payload, ""


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归已知 safe wrapper key，避免 raw payload 被误当作 intake source。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 必须命中 owner_response_intake schema/capability，不能跳链 review。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 字段名命中 raw/control/credential/resolution 类别时拒绝，不回显敏感值。
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
    # 输入任何层把 false-state flag 改成 true，都不能进入 accepted 分支。
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


def _unsafe_reasons(value: Any) -> list[str]:
    # 只输出类别原因，不把命中的原始片段带进 blocked artifact。
    reasons: list[str] = []
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_control_credential_path_resolution_or_proof_fields")
    encoded = _encoded(value)
    if PATH_LIKE_RE.search(encoded) or any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS):
        reasons.append("unsafe_path_credential_ros_control_hardware_success_or_resolution_claim")
    reasons.extend(_truthy_false_flags(value))
    return list(dict.fromkeys(reasons))


def _source_refs(source: dict[str, Any]) -> tuple[str, list[str]]:
    # source 内多个 evidence_ref 不一致时直接 fail closed。
    refs: list[str] = []
    for candidate in _candidates(source):
        for key in ("safe_evidence_ref", "evidence_ref"):
            ref = _safe_ref(candidate.get(key))
            if ref:
                refs.append(ref)
            elif candidate.get(key):
                refs.append("__unsafe_ref__")
    unique = list(dict.fromkeys(refs))
    reasons: list[str] = []
    if "__unsafe_ref__" in unique:
        reasons.append("unsafe_evidence_ref")
    clean = [ref for ref in unique if ref != "__unsafe_ref__"]
    if len(clean) > 1:
        reasons.append("evidence_ref_mismatch")
    return (clean[0] if clean and not reasons else ""), reasons


def _source_is_software_proof_not_proven(source: dict[str, Any]) -> bool:
    # 五个固定边界同时满足后，review decision 才能进入非 blocked 分支。
    encoded = _encoded(source)
    return (
        _safe_text(source.get("source")) == SOURCE
        and "not_proven" in encoded
        and source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _source_view(payload: dict[str, Any], load_issue: str) -> dict[str, Any]:
    # normalized source 是唯一参与合同判断的数据面。
    source = _find_source(payload) if payload else {}
    safe_copy = _dict(source.get("safe_copy"))
    evidence_ref, ref_errors = _source_refs(source) if source else ("", [])
    owner_status = _safe_text(source.get("owner_response_material_status") or safe_copy.get("owner_response_material_status"))
    return {
        "load_issue": load_issue,
        "schema": _safe_text(source.get("schema")),
        "capability": _safe_text(source.get("capability")),
        "evidence_boundary": _safe_text(source.get("evidence_boundary") or source.get("boundary") or safe_copy.get("evidence_boundary")),
        "review_readiness": _safe_text(source.get("review_readiness") or safe_copy.get("review_readiness")),
        "owner_response_material_status": owner_status,
        "safe_evidence_ref": evidence_ref,
        "ref_errors": ref_errors,
        "same_evidence_ref_required": source.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
        "accepted_materials": _safe_list(source.get("accepted_materials") or safe_copy.get("accepted_materials")),
        "missing_materials": _safe_list(source.get("missing_materials") or safe_copy.get("missing_materials")),
        "rejected_materials": _safe_list(source.get("rejected_materials") or safe_copy.get("rejected_materials")),
        "unsafe_materials": _safe_list(source.get("unsafe_materials") or safe_copy.get("unsafe_materials")),
        "review_reasons": _safe_list(source.get("review_reasons") or source.get("decision_reasons")),
        "previous_escalation_reference": _dict(source.get("previous_escalation_reference")),
        "previous_handoff_reference": _dict(source.get("previous_handoff_reference")),
        "pr5_thread": _dict(source.get("pr5_thread") or safe_copy.get("pr5_thread")),
        "source_is_software_proof_not_proven": _source_is_software_proof_not_proven(source) if source else False,
        "unsafe_reasons": _unsafe_reasons(source) if source else [],
    }


def _source_block_reasons(source: dict[str, Any], requested_ref: str) -> list[str]:
    # source 合同错误说明 intake 本身不可消费，应输出 blocked 或 rejected。
    reasons: list[str] = []
    schema_ok = source["schema"] in SOURCE_SCHEMAS or source["capability"] == SOURCE_CAPABILITY
    boundary_ok = source["evidence_boundary"] == SOURCE_BOUNDARY
    if source["load_issue"]:
        reasons.append(source["load_issue"])
    if not schema_ok:
        reasons.append("unsupported_owner_response_intake_schema")
    if not boundary_ok:
        reasons.append("missing_or_wrong_owner_response_intake_proof_boundary")
    if not source["source_is_software_proof_not_proven"]:
        reasons.append("source_not_software_proof_not_proven_or_false_flags_changed")
    if source["ref_errors"] or not source["safe_evidence_ref"] or source["same_evidence_ref_required"] is not True:
        reasons.extend(source["ref_errors"] or ["missing_or_weak_same_evidence_ref"])
    if requested_ref and source["safe_evidence_ref"] and requested_ref != source["safe_evidence_ref"]:
        reasons.append("evidence_ref_mismatch")
    return list(dict.fromkeys(reasons))


def _review_decision(source: dict[str, Any], requested_ref: str) -> tuple[str, list[str]]:
    # 决策优先级：无 intake/unsupported -> blocked；unsafe -> rejected；
    # rejected/unsafe materials -> rejected；missing -> needs_more；全 accepted 才 accepted。
    block_reasons = _source_block_reasons(source, requested_ref)
    if source["load_issue"] or "unsupported_owner_response_intake_schema" in block_reasons:
        return BLOCKED_MISSING_INTAKE, block_reasons
    if "missing_or_wrong_owner_response_intake_proof_boundary" in block_reasons:
        return BLOCKED_MISSING_INTAKE, block_reasons
    if source["unsafe_reasons"]:
        return REJECTED_UNSAFE, source["unsafe_reasons"]
    if block_reasons:
        return REJECTED_UNSAFE, block_reasons
    if source["unsafe_materials"] or source["rejected_materials"]:
        return REJECTED_UNSAFE, ["rejected_or_unsafe_owner_response_material"]
    if source["review_readiness"] == intake.REJECTED_REVIEW_READINESS or "rejected" in source["owner_response_material_status"]:
        return REJECTED_UNSAFE, source["review_reasons"] or ["owner_response_intake_rejected_not_proven"]
    if source["missing_materials"] or source["review_readiness"] == intake.MISSING_REVIEW_READINESS or "missing" in source["owner_response_material_status"]:
        return NEEDS_MORE, source["review_reasons"] or ["owner_response_material_missing_or_incomplete"]
    if source["review_readiness"] == intake.ACCEPTED_REVIEW_READINESS and source["accepted_materials"]:
        return ACCEPTED, ["owner response material accepted for later material review only"]
    return NEEDS_MORE, ["owner_response_intake_not_ready_for_material_review"]


def _next_required_evidence(decision: str, source: dict[str, Any]) -> list[dict[str, Any]]:
    # 下一步都是 owner/material-review 动作，不是机器人控制动作。
    if decision == ACCEPTED:
        return [
            {
                "owner": "Product Manager / OKR Owner",
                "action": "schedule_material_review_without_marking_field_cloud_phone_hil_or_delivery_success",
                "materials": source["accepted_materials"],
            }
        ]
    if decision == NEEDS_MORE:
        return [
            {
                "owner": "field-owner",
                "action": "backfill_missing_owner_response_material_under_same_safe_evidence_ref",
                "materials": source["missing_materials"] or list(intake.DEFAULT_REQUIRED_MATERIALS),
            }
        ]
    if decision == REJECTED_UNSAFE:
        return [
            {
                "owner": "field-owner",
                "action": "resubmit_sanitized_owner_response_without_unsafe_rejected_success_control_or_resolution_claims",
                "materials": source["rejected_materials"] + source["unsafe_materials"] or list(intake.DEFAULT_REQUIRED_MATERIALS),
            }
        ]
    return [
        {
            "owner": "field-owner",
            "action": "provide_supported_field_evidence_material_resolution_owner_response_intake_safe_artifact_or_summary",
            "materials": ["owner response material", "same safe evidence_ref", SOURCE_BOUNDARY],
        }
    ]


def _owner_action(decision: str) -> str:
    # owner_action 文案明确责任边界，防止 accepted 被误读成完成。
    if decision == ACCEPTED:
        return "review accepted owner response material later; keep not_proven and no OKR lift"
    if decision == NEEDS_MORE:
        return "backfill missing owner response material under the same safe evidence_ref"
    if decision == REJECTED_UNSAFE:
        return "remove unsafe, rejected, raw, success, control, credential, path, proof, or reviewer-resolution claims"
    return "rerun owner response intake and provide the safe summary before review decision"


def _safe_phone_copy(decision: str, evidence_ref: str, reasons: list[str]) -> dict[str, Any]:
    # phone copy 只说明状态与下一步，不暴露 raw artifact 或控制入口。
    return {
        "title": "owner response material 复核决策",
        "review_decision": decision,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "message": "accepted 只表示可进入后续材料复核，仍不是现场通过、云端通过、手机通过、HIL 或交付成功。",
        "decision_reasons": reasons,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "delivery_success": False,
    }


def _safe_copy(
    decision: str,
    reasons: list[str],
    evidence_ref: str,
    source: dict[str, Any],
    next_required_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    # safe_copy 是后续 diagnostics/mobile 建议消费面，字段稳定且全为短字段。
    return {
        **_safe_flags(),
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "capability": CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "previous_intake_reference": _previous_intake_reference(source),
        "owner_response_material_status": source["owner_response_material_status"] or "missing",
        "review_decision": decision,
        "decision_enum": list(REVIEW_DECISIONS),
        "decision_reasons": reasons,
        "accepted_materials": source["accepted_materials"],
        "missing_materials": source["missing_materials"],
        "rejected_materials": source["rejected_materials"],
        "unsafe_materials": source["unsafe_materials"],
        "next_required_evidence": next_required_evidence,
        "owner_action": _owner_action(decision),
        "safe_phone_copy": _safe_phone_copy(decision, evidence_ref, reasons),
        "pr5_thread": _pr5_thread(),
    }


def _previous_intake_reference(source: dict[str, Any]) -> dict[str, Any]:
    # 上一环引用只保留合同字段，避免把完整 intake artifact 带进输出。
    return {
        "capability": SOURCE_CAPABILITY,
        "schema": source["schema"],
        "evidence_boundary": source["evidence_boundary"],
        "review_readiness": source["review_readiness"],
        "safe_evidence_ref": source["safe_evidence_ref"],
        "previous_escalation_reference": source["previous_escalation_reference"],
        "previous_handoff_reference": source["previous_handoff_reference"],
    }


def _pr5_thread() -> dict[str, str]:
    # PR #5 状态固定保守表达，除非真实 reviewer evidence 更新。
    return {
        "thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "state": "unresolved",
        "material_state": "hardware_material_pending",
        "comment_id": "3269642220",
        "comment_status": "software_proof_reply_only_not_reviewer_resolution",
    }


def _summary_payload(
    decision: str,
    reasons: list[str],
    evidence_ref: str,
    source: dict[str, Any],
    next_required_evidence: list[dict[str, Any]],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 与 artifact 保持同一 decision，便于 Robot diagnostics safe alias。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "summary_only": True,
        "safe_to_render_on_phone": True,
        **_safe_flags(),
        "capability": CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "previous_intake_reference": _previous_intake_reference(source),
        "owner_response_material_status": source["owner_response_material_status"] or "missing",
        "review_decision": decision,
        "decision_enum": list(REVIEW_DECISIONS),
        "decision_reasons": reasons,
        "accepted_materials": source["accepted_materials"],
        "missing_materials": source["missing_materials"],
        "rejected_materials": source["rejected_materials"],
        "unsafe_materials": source["unsafe_materials"],
        "next_required_evidence": next_required_evidence,
        "owner_action": _owner_action(decision),
        "ceo_escalation_recommendation": _ceo_escalation_recommendation(decision),
        "review_handoff_recommendation": _review_handoff_recommendation(decision),
        "pr5_thread": _pr5_thread(),
        "safe_copy": safe_copy,
        "safe_phone_copy": _safe_phone_copy(decision, evidence_ref, reasons),
        "safety_markers": [
            "source=software_proof",
            "not_proven",
            "primary_actions_enabled=false",
            "delivery_success=false",
            "safe_to_control=false",
            "owner response material",
        ],
    }


def _ceo_escalation_recommendation(decision: str) -> str:
    # CEO escalation 只描述材料决策，不升级成产品成功或 OKR 进度。
    if decision == BLOCKED_MISSING_INTAKE:
        return "ask owner to provide the missing intake safe artifact before CEO can review blocker state"
    if decision == NEEDS_MORE:
        return "ask owner to backfill missing material; no OKR percentage lift"
    if decision == REJECTED_UNSAFE:
        return "ask owner to resubmit sanitized material; reject unsafe success/control/resolution claims"
    return "queue later material review; keep no field/cloud/phone/HIL/delivery success claim"


def _review_handoff_recommendation(decision: str) -> str:
    # review handoff 是文档/人工复核建议，不是 runtime 控制建议。
    if decision == ACCEPTED:
        return "handoff_to_material_review_not_proven"
    if decision == NEEDS_MORE:
        return "handoff_to_owner_backfill_not_proven"
    if decision == REJECTED_UNSAFE:
        return "handoff_to_sanitization_retry_not_proven"
    return "handoff_to_owner_response_intake_rerun_not_proven"


def build_field_evidence_material_resolution_owner_response_review_decision(
    owner_response_intake_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 owner-response-intake safe source，生成 fail-closed review decision。"""
    source_payload, load_issue = _load_json(owner_response_intake_json)
    source = _source_view(source_payload, load_issue)
    requested_ref = _safe_ref(evidence_ref) or source["safe_evidence_ref"]
    decision, reasons = _review_decision(source, requested_ref)
    if not requested_ref:
        # 缺 safe ref 时仍输出 blocked artifact，但不伪造证据号。
        requested_ref = "missing_safe_evidence_ref"
    reasons = list(dict.fromkeys(reasons or [decision]))
    next_required_evidence = _next_required_evidence(decision, source)
    safe_copy = _safe_copy(decision, reasons, requested_ref, source, next_required_evidence)
    summary = _summary_payload(decision, reasons, requested_ref, source, next_required_evidence, safe_copy)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "previous_intake_reference": _previous_intake_reference(source),
        "owner_response_material_status": source["owner_response_material_status"] or "missing",
        "review_decision": decision,
        "decision_enum": list(REVIEW_DECISIONS),
        "decision_reasons": reasons,
        "accepted_materials": source["accepted_materials"],
        "missing_materials": source["missing_materials"],
        "rejected_materials": source["rejected_materials"],
        "unsafe_materials": source["unsafe_materials"],
        "next_required_evidence": next_required_evidence,
        "owner_action": _owner_action(decision),
        "ceo_escalation_recommendation": _ceo_escalation_recommendation(decision),
        "review_handoff_recommendation": _review_handoff_recommendation(decision),
        "pr5_thread": _pr5_thread(),
        "safe_copy": safe_copy,
        "field_evidence_material_resolution_owner_response_review_decision_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "blocked_claims": [
            "real_cloud_proof",
            "public_https_tls",
            "4g_or_sim",
            "oss_cdn_live_traffic",
            "production_db_queue",
            "true_phone_browser_proof",
            "route_elevator_field_pass",
            "verified_terminal_result",
            "delivery_success",
            "hardware_or_hil_pass",
            "pr5_resolved",
            "okr_percentage_lift",
        ],
        "safety_markers": [
            "field_evidence_material_resolution_owner_response_review_decision",
            "software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate",
            "source=software_proof",
            "not_proven",
            "primary_actions_enabled=false",
            "delivery_success=false",
            "safe_to_control=false",
            "owner response material",
            ACCEPTED,
            NEEDS_MORE,
            REJECTED_UNSAFE,
            BLOCKED_MISSING_INTAKE,
        ],
    }
    return artifact, summary, 0


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint artifact diff 与人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 保持 dependency-free，便于 PC、Docker 和 focused unittest 共用。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.field_evidence_material_resolution_owner_response_review_decision.v1 from a sanitized "
            "field_evidence_material_resolution_owner_response_intake artifact/summary/Robot alias. Keeps "
            "source=software_proof, not_proven, primary_actions_enabled=false, delivery_success=false, "
            "safe_to_control=false, and owner response material as review input only."
        )
    )
    parser.add_argument("--owner-response-intake-json", required=True, help="sanitized owner response intake artifact, summary, or Robot alias JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output", type=Path, help="optional owner response review decision artifact JSON output path")
    parser.add_argument("--summary-output", type=Path, help="optional owner response review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_field_evidence_material_resolution_owner_response_review_decision(
        args.owner_response_intake_json,
        args.evidence_ref,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_material_resolution_owner_response_review_decision: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"owner_response_review_decision_summary_file:{_safe_ref(args.summary_output)}")
        print(f"review_decision:{artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
