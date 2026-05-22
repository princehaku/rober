#!/usr/bin/env python3
"""生成 field evidence material resolution owner response intake gate。

该 PC gate 只消费上一轮
`field_evidence_material_resolution_followup_escalation_status` 的 safe
artifact / summary / Robot alias，并可选消费脱敏后的 owner response material
metadata。输出只把 owner 回复材料归类为 accepted/missing/rejected/unsafe，供后续
review 使用；accepted 仅表示 accepted_for_review_not_proven，不代表 OKR 进展、
PR #5 thread resolved、field pass、phone/cloud proof、HIL 或 delivery success。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_material_resolution_followup_escalation_status as followup


SCHEMA = "trashbot.field_evidence_material_resolution_owner_response_intake.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_material_resolution_owner_response_intake_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_material_resolution_owner_response_intake"
SOURCE_CAPABILITY = followup.CAPABILITY
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_material_resolution_owner_response_intake_gate"
SOURCE_BOUNDARY = followup.EVIDENCE_BOUNDARY

# 设计约束 01：本 gate 只处理脱敏 metadata，不读取真实文件、ROS graph、手机或云端。
# 设计约束 02：上一环必须是 followup escalation status，不能绕过 owner handoff。
# 设计约束 03：accepted 只表示进入后续 review，不证明现场、云、手机、HIL 或 OKR。
# 设计约束 04：同一 safe evidence_ref 是跨 handoff / escalation / response 的硬约束。
# 设计约束 05：缺 owner response material 必须 blocked/not_proven，不能伪造 accepted。
# 设计约束 06：显式 rejected 或 unsafe material 必须 fail closed。
# 设计约束 07：PR #5 thread X 保持 unresolved / hardware_material_pending。
# 设计约束 08：delivery_success、primary_actions_enabled、safe_to_control 永远为 false。
# 设计约束 09：reviewer-resolution、field/cloud/phone/HIL proof claim 统一拒绝。
# 设计约束 10：summary 是后续 Robot/mobile 唯一建议消费面，不包含 raw artifact。
# 设计约束 11：所有技术注释保持中文，解释安全边界与参数取舍。
# 设计约束 12：CLI 不提供 ACK、GitHub resolve、robot command 或 action trigger。

SUPPORTED_SOURCE_SCHEMAS = {
    followup.SCHEMA,
    followup.SUMMARY_SCHEMA,
    followup.ROBOT_ALIAS,
    f"trashbot.{followup.ROBOT_ALIAS}.v1",
}
RESPONSE_SCHEMAS = {
    "",
    "trashbot.field_evidence_material_resolution_owner_response_packet.v1",
    "trashbot.field_evidence_material_resolution_owner_response_packet_summary.v1",
}

MISSING_REVIEW_READINESS = "blocked_missing_owner_response_material_not_proven"
ACCEPTED_REVIEW_READINESS = "accepted_for_review_not_proven"
REJECTED_REVIEW_READINESS = "rejected_unsafe_owner_response_material_not_proven"
OWNER_RESPONSE_STATUSES = ("missing", "received_not_reviewed", "rejected_not_proven")

DEFAULT_REQUIRED_MATERIALS = (
    "owner response material",
    "real terminal delivery/dropoff/cancel result material",
    "real public HTTPS/TLS, 4G/SIM, OSS/CDN, DB/queue, or worker evidence",
    "true phone/browser evidence",
    "real route/elevator field pass evidence",
    "real hardware/HIL evidence",
    "PR #5 reviewer resolution material",
)

WRAPPER_KEYS = (
    "field_evidence_material_resolution_followup_escalation_status",
    "field_evidence_material_resolution_followup_escalation_status_summary",
    followup.ROBOT_ALIAS,
    "robot_diagnostics_summary",
    "summary",
    "artifact",
    "payload",
    "data",
    "safe_copy",
)

SAFE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,100}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\b\.\.?/|/dev/|/Users/|/tmp/|/var/|/home/|/ws/)")
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
    re.compile(r"(?i)\b(PRRT_[A-Za-z0-9]+[^,;]{0,80}\bresolved\b|reviewer[^,;]{0,80}\bresolved\b|github[^,;]{0,80}\bresolved\b)"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART device|serial device|baudrate|GPIO|voltage|firmware)\b"),
    re.compile(r"(?i)\b(real phone proof|true phone proof|cloud proof|field proof|HIL proof)\b"),
)


def _utc_now() -> str:
    # UTC 时间让本地 Docker、PC 和 CI 产物可按同一时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # false flags 在 artifact、summary、safe_copy 中重复，避免局部消费误启控制。
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
    # 自由文本只保留短摘要，避免 raw log 或多行 artifact 穿透。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:240] or default


def _safe_list(value: Any, limit: int = 32) -> list[str]:
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


def _safe_ref(value: Any) -> str:
    # evidence_ref 只能是短安全标识；路径、空值和弱字符串都拒绝。
    text = _safe_text(value)
    if text and SAFE_REF_RE.fullmatch(text) and not PATH_LIKE_RE.search(text):
        return text
    return ""


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object，字符串化 JSON 不自动展开。
    return value if isinstance(value, dict) else {}


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转成可审计 blocked reason。
    if not path:
        return {}, f"{label}_not_provided"
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, f"{label}_missing"
    except json.JSONDecodeError:
        return {}, f"{label}_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, f"{label}_read_error"
    if not isinstance(payload, dict):
        return {}, f"{label}_not_object"
    return payload, ""


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归 safe wrapper key，不把任意 raw payload 当作可信 source。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 必须命中上一环 followup schema/capability，避免跳链 intake。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SUPPORTED_SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


def _find_response(payload: dict[str, Any]) -> dict[str, Any]:
    # response 可直接是安全表单，也可包在 safe_copy / summary 中。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        if schema in RESPONSE_SCHEMAS and _has_response_material(candidate):
            return candidate
    return payload


def _has_response_material(payload: dict[str, Any]) -> bool:
    # 用白名单字段判断是否是 owner response，而不是泛化展开整个 payload。
    for key in ("materials", "material_responses", "responses", "accepted_materials", "missing_materials", "rejected_materials", "unsafe_materials"):
        value = payload.get(key)
        if isinstance(value, (dict, list)) and value:
            return True
    return False


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
    # 输入任何层把 false-state flag 改成 true，都不能进入 review。
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


def _source_ref(source: dict[str, Any]) -> tuple[str, list[str]]:
    # source 内多个 evidence_ref 不一致时直接 blocked，保护同一证据号链路。
    refs = []
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
    return (clean[0] if clean and not reasons else ""), list(dict.fromkeys(reasons))


def _source_is_safe(source: dict[str, Any]) -> bool:
    # 上一环必须保留 software_proof / not_proven / false flags。
    encoded = _encoded(source)
    return (
        _safe_text(source.get("source")) == SOURCE
        and "not_proven" in encoded
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
        and source.get("safe_to_control") is False
    )


def _source_view(payload: dict[str, Any], read_issue: str) -> dict[str, Any]:
    # normalized source 是唯一参与 source 合同判断的数据面。
    source = _find_source(payload) if payload else {}
    ref, ref_errors = _source_ref(source) if source else ("", [])
    followup_status = _safe_text(
        source.get("followup_status") or source.get("field_evidence_material_resolution_followup_escalation_status")
    )
    return {
        "read_issue": read_issue,
        "schema": _safe_text(source.get("schema")),
        "capability": _safe_text(source.get("capability")),
        "evidence_boundary": _safe_text(source.get("evidence_boundary") or source.get("boundary")),
        "followup_status": followup_status,
        "owner_response_material_status": _safe_text(source.get("owner_response_material_status")),
        "safe_evidence_ref": ref,
        "ref_errors": ref_errors,
        "same_evidence_ref_required": source.get("same_evidence_ref_required", True),
        "next_required_evidence": _safe_list(source.get("next_required_evidence") or source.get("not_proven_items")),
        "lineage": _dict(source.get("lineage")),
        "pr5_thread": _dict(source.get("pr5_thread")),
        "source_is_safe": _source_is_safe(source) if source else False,
        "unsafe_reasons": _unsafe_reasons(source) if source else [],
    }


def _source_ready(source: dict[str, Any]) -> tuple[bool, list[str]]:
    # source 不 ready 时不继续消费 owner response，防止用新材料掩盖坏 handoff。
    reasons: list[str] = []
    schema_ok = source["schema"] in SUPPORTED_SOURCE_SCHEMAS or source["capability"] == SOURCE_CAPABILITY
    boundary_ok = source["evidence_boundary"] == SOURCE_BOUNDARY
    if source["read_issue"]:
        reasons.append(source["read_issue"])
    if not schema_ok:
        reasons.append("unsupported_followup_escalation_status_schema")
    if not boundary_ok:
        reasons.append("missing_or_wrong_followup_proof_boundary")
    if source["unsafe_reasons"]:
        reasons.extend(source["unsafe_reasons"])
    if not source["source_is_safe"]:
        reasons.append("source_not_software_proof_not_proven_or_false_flags_changed")
    if source["ref_errors"] or not source["safe_evidence_ref"] or source["same_evidence_ref_required"] is not True:
        reasons.extend(source["ref_errors"] or ["missing_or_weak_same_evidence_ref"])
    if source["followup_status"] not in {followup.PENDING_STATUS, followup.OVERDUE_STATUS, followup.ESCALATED_STATUS}:
        reasons.append("previous_escalation_status_not_owner_response_pending_or_escalated")
    return not reasons, list(dict.fromkeys(reasons))


def _response_material_map(response: dict[str, Any]) -> dict[str, Any]:
    # 支持 dict/list 表单，统一为 material name -> response item。
    for key in ("materials", "material_responses", "responses"):
        value = response.get(key)
        if isinstance(value, dict):
            return {str(name): item for name, item in value.items()}
        if isinstance(value, list):
            mapped: dict[str, Any] = {}
            for item in value:
                if isinstance(item, dict):
                    name = _safe_text(item.get("name") or item.get("material") or item.get("category"))
                    if name:
                        mapped[name] = item
            return mapped
    return {}


def _listed_materials(response: dict[str, Any], key: str) -> set[str]:
    # 简写列表让 owner 只提交类别索引，也能进入分类流程。
    value = response.get(key)
    if isinstance(value, list):
        return {_safe_text(item.get("name") if isinstance(item, dict) else item) for item in value if _safe_text(item.get("name") if isinstance(item, dict) else item)}
    if isinstance(value, dict):
        return {_safe_text(name) for name in value if _safe_text(name)}
    return set()


def _response_required(source: dict[str, Any], response: dict[str, Any]) -> list[str]:
    # required 优先来自上一环 next_required_evidence，再兼容 response.required_materials。
    required = _safe_list(source.get("next_required_evidence")) or _safe_list(response.get("required_materials"))
    return required or list(DEFAULT_REQUIRED_MATERIALS)


def _classify_item(name: str, item: Any, expected_ref: str, response_ref: str, response_missing: bool) -> tuple[str, list[str]]:
    # 单项分类保守处理：缺项 missing，显式 accepted 才进入 accepted。
    if response_missing:
        return "missing", ["owner_response_material_not_provided"]
    if item is None:
        return "missing", ["required_owner_response_material_absent"]
    if not isinstance(item, dict):
        return "rejected", ["owner_response_material_item_not_object"]

    explicit = _safe_text(item.get("classification") or item.get("status") or item.get("response_status")).lower()
    item_ref = _safe_ref(item.get("safe_evidence_ref") or item.get("evidence_ref") or response_ref)
    reasons: list[str] = []
    if item_ref != expected_ref:
        reasons.append("evidence_ref_mismatch")
    if _unsafe_reasons(item):
        reasons.append("unsafe_owner_response_material")
    if not item_ref:
        reasons.append("missing_safe_evidence_ref")
    if reasons:
        return "unsafe", list(dict.fromkeys(reasons))
    if item.get("rejected") is True or explicit == "rejected":
        return "rejected", ["owner_marked_rejected_not_proven"]
    if item.get("unsafe") is True or explicit == "unsafe":
        return "unsafe", ["owner_marked_unsafe_not_proven"]
    if item.get("missing") is True or explicit == "missing":
        return "missing", ["owner_marked_missing_not_proven"]
    if item.get("accepted") is True or explicit in {"accepted", "received_not_reviewed"}:
        return "accepted", ["received_not_reviewed_ready_for_later_review_only"]
    return "rejected", ["missing_explicit_safe_owner_response_status"]


def _classify_materials(source: dict[str, Any], response: dict[str, Any], response_issue: str, expected_ref: str) -> tuple[dict[str, list[str]], list[dict[str, Any]], list[str]]:
    # 逐项分类后再汇总 readiness；这样 partial response 不会被 happy path 覆盖。
    required = _response_required(source, response)
    material_map = _response_material_map(response)
    response_ref = _safe_ref(response.get("safe_evidence_ref") or response.get("evidence_ref"))
    accepted_names = _listed_materials(response, "accepted_materials") | _listed_materials(response, "received_materials")
    missing_names = _listed_materials(response, "missing_materials")
    rejected_names = _listed_materials(response, "rejected_materials")
    unsafe_names = _listed_materials(response, "unsafe_materials")
    response_missing = bool(response_issue)
    response_unsafe = _unsafe_reasons(response) if response else []
    categories = {"accepted": [], "missing": [], "rejected": [], "unsafe": []}
    details: list[dict[str, Any]] = []

    for name in required:
        item = material_map.get(name)
        if item is None and name in accepted_names:
            item = {"name": name, "status": "accepted", "safe_evidence_ref": response_ref, "summary": "accepted category index only"}
        elif item is None and name in missing_names:
            item = {"name": name, "status": "missing", "safe_evidence_ref": response_ref}
        elif item is None and name in rejected_names:
            item = {"name": name, "status": "rejected", "safe_evidence_ref": response_ref}
        elif item is None and name in unsafe_names:
            item = {"name": name, "status": "unsafe", "safe_evidence_ref": response_ref}
        status, reasons = _classify_item(name, item, expected_ref, response_ref, response_missing)
        categories[status].append(name)
        details.append(
            {
                "name": name,
                "classification": status,
                "classification_reasons": reasons,
                "safe_evidence_ref": expected_ref,
                "accepted_means": "accepted_for_review_not_proven" if status == "accepted" else "not_accepted",
                "not_proven": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
        )
    if response_unsafe:
        # 顶层 response unsafe 使全部非 missing 材料进入 unsafe，避免部分绕过。
        for key in ("accepted", "rejected"):
            categories["unsafe"].extend(categories[key])
            categories[key] = []
        for detail in details:
            if detail["classification"] != "missing":
                detail["classification"] = "unsafe"
                detail["classification_reasons"] = ["unsafe_owner_response_packet"]
    return categories, details, response_unsafe


def _readiness(source_ready: bool, source_reasons: list[str], response_issue: str, categories: dict[str, list[str]], response_unsafe: list[str]) -> tuple[str, str, list[str]]:
    # readiness 只决定是否进入后续 review，不表示真实证明成立。
    if not source_ready:
        return MISSING_REVIEW_READINESS, "missing", source_reasons
    if response_issue:
        return MISSING_REVIEW_READINESS, "missing", [response_issue]
    if response_unsafe or categories["unsafe"] or categories["rejected"]:
        return REJECTED_REVIEW_READINESS, "rejected_not_proven", response_unsafe or ["rejected_or_unsafe_owner_response_material"]
    if categories["missing"]:
        return MISSING_REVIEW_READINESS, "missing", ["missing_owner_response_material_not_proven"]
    return ACCEPTED_REVIEW_READINESS, "received_not_reviewed", ["accepted_for_review_not_proven"]


def _safe_copy(readiness: str, owner_status: str, evidence_ref: str, categories: dict[str, list[str]]) -> dict[str, Any]:
    # safe_copy 是后续 review/diagnostics/mobile 的白名单消费面。
    return {
        **_safe_flags(),
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "capability": CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "owner_response_material_status": owner_status,
        "review_readiness": readiness,
        "accepted_materials": categories["accepted"],
        "missing_materials": categories["missing"],
        "rejected_materials": categories["rejected"],
        "unsafe_materials": categories["unsafe"],
        "accepted_means": "accepted_for_review_not_proven",
        "pr5_thread": {
            "thread_id": followup.PR5_THREAD_ID,
            "state": "unresolved",
            "material_state": "hardware_material_pending",
        },
    }


def build_field_evidence_material_resolution_owner_response_intake(
    followup_summary_json: str,
    owner_response_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 followup summary 与可选 owner response，生成 fail-closed intake。"""
    source_payload, source_issue = _load_json(followup_summary_json, "followup_summary_json")
    source = _source_view(source_payload, source_issue)
    source_ok, source_reasons = _source_ready(source)
    requested_ref = _safe_ref(evidence_ref) or source["safe_evidence_ref"]
    if evidence_ref and requested_ref != source["safe_evidence_ref"]:
        # CLI 指定 ref 与 source 不一致时，按同证据号硬约束失败。
        source_ok = False
        source_reasons.append("evidence_ref_mismatch")
    response_payload, response_issue = _load_json(owner_response_json, "owner_response_json")
    response = _find_response(response_payload) if response_payload else {}
    response_schema = _safe_text(response.get("schema"))
    if response and response_schema not in RESPONSE_SCHEMAS:
        response_issue = "owner_response_json_unsupported_schema"
    categories, response_details, response_unsafe = _classify_materials(source, response, response_issue, requested_ref)
    readiness, owner_status, reasons = _readiness(source_ok, source_reasons, response_issue, categories, response_unsafe)
    generated_at = _utc_now()
    safe_copy = _safe_copy(readiness, owner_status, requested_ref, categories)
    common = {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "owner_response_material_status": owner_status,
        "allowed_owner_response_material_statuses": list(OWNER_RESPONSE_STATUSES),
        "review_readiness": readiness,
        "accepted_materials": categories["accepted"],
        "missing_materials": categories["missing"],
        "rejected_materials": categories["rejected"],
        "unsafe_materials": categories["unsafe"],
        "review_reasons": list(dict.fromkeys(reasons)),
        "material_response_details": response_details,
        "accepted_means": "accepted_for_review_not_proven",
        "previous_escalation_reference": {
            "capability": SOURCE_CAPABILITY,
            "schema": source["schema"],
            "evidence_boundary": source["evidence_boundary"],
            "followup_status": source["followup_status"],
            "safe_evidence_ref": source["safe_evidence_ref"],
        },
        "previous_handoff_reference": {
            "capability": "field_evidence_material_resolution_review_handoff",
            "trace": "field_evidence_material_resolution_review_handoff",
            "previous_handoff": source["lineage"].get("previous_handoff", followup.PREVIOUS_HANDOFF_COMMIT),
            "safe_evidence_ref": source["safe_evidence_ref"],
        },
        "pr5_thread": {
            "thread_id": followup.PR5_THREAD_ID,
            "state": "unresolved",
            "material_state": "hardware_material_pending",
            "comment_id": followup.PR5_COMMENT_ID,
            "comment_status": "software_proof_reply_only_not_reviewer_resolution",
        },
        "blocked_claims": [
            "field_proof",
            "cloud_proof",
            "phone_proof",
            "hil_pass",
            "delivery_success",
            "reviewer_resolution",
            "okr_movement",
        ],
        "safe_copy": safe_copy,
        "summary_alias": ROBOT_ALIAS,
        "safety_markers": [
            "source=software_proof",
            "not_proven",
            "primary_actions_enabled=false",
            "delivery_success=false",
            "safe_to_control=false",
            "accepted_for_review_not_proven",
        ],
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        "field_evidence_material_resolution_owner_response_intake": readiness,
        **common,
    }
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "field_evidence_material_resolution_owner_response_intake": readiness,
        "source_followup_summary": {
            "ready": source_ok,
            "read_issue": source_issue,
            "schema": source["schema"],
            "evidence_boundary": source["evidence_boundary"],
            "unsafe_reasons": source["unsafe_reasons"],
            "source_reasons": source_reasons,
        },
        "owner_response_packet": {
            "load_issue": response_issue,
            "schema": response_schema,
            "unsafe_reasons": response_unsafe,
        },
        **common,
    }
    return artifact, summary, 0


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint artifact diff 与人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只做本地 JSON gate，不提供 fetch、resolve、ACK 或 robot command。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.field_evidence_material_resolution_owner_response_intake.v1 from a sanitized "
            "field_evidence_material_resolution_followup_escalation_status artifact/summary/Robot alias plus optional "
            "owner response material metadata. Keeps source=software_proof, not_proven, "
            "primary_actions_enabled=false, delivery_success=false, safe_to_control=false."
        )
    )
    parser.add_argument("--followup-summary-json", required=True, help="sanitized followup escalation status artifact, summary, or Robot alias JSON")
    parser.add_argument("--owner-response-json", default="", help="optional sanitized owner response material metadata JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output", type=Path, help="optional owner response intake artifact JSON output path")
    parser.add_argument("--summary-output", type=Path, help="optional owner response intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_field_evidence_material_resolution_owner_response_intake(
        args.followup_summary_json,
        args.owner_response_json,
        args.evidence_ref,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_material_resolution_owner_response_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"owner_response_intake_summary_file:{_safe_ref(args.summary_output)}")
        print(f"review_readiness:{artifact['review_readiness']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
