#!/usr/bin/env python3
"""生成 field evidence real material response intake artifact。

该 PC gate 承接上一轮 `field_evidence_real_material_request_dispatch` 的
safe artifact / summary / wrapper，并接收可选 field-owner response JSON。
它只把九类真实材料响应归类为 accepted、missing、rejected、blocked，供后续
review gate 使用；accepted 仅表示“可进入后续复核”，不是 route/elevator pass、
delivery result 或 delivery success。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_real_material_request_dispatch as dispatch
import route_task_field_retest_material_pack as material_pack


INTAKE_SCHEMA = "trashbot.field_evidence_real_material_response_intake.v1"
INTAKE_SUMMARY_SCHEMA = "trashbot.field_evidence_real_material_response_intake_summary.v1"
SCHEMA_VERSION = 1
INTAKE_BOUNDARY = "software_proof_docker_field_evidence_real_material_response_intake_gate"

# response intake 只能消费上一轮 request dispatch，避免绕过 field-owner 请求清单。
SOURCE_SCHEMAS = {dispatch.DISPATCH_SCHEMA, dispatch.DISPATCH_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {dispatch.DISPATCH_BOUNDARY}
READY_DISPATCH_STATUS = "ready_for_field_owner_real_material_request_not_proven"

# field-owner response 允许无 schema，便于先用安全表单或 fixture 进入 PC gate。
RESPONSE_SCHEMAS = {
    "",
    "trashbot.field_evidence_real_material_response_packet.v1",
    "trashbot.field_evidence_real_material_response_packet_summary.v1",
}

RESPONSE_STATUSES = ("accepted", "missing", "rejected", "blocked")
REQUIRED_MATERIALS = dispatch.REQUIRED_MATERIALS
BLOCKED_CLAIMS = (
    "real_field_rerun",
    "true_phone_browser_proof",
    "nav2_fixed_route_proof",
    "route_elevator_field_pass",
    "hil_pass",
    "wave_rover_uart_proof",
    "o5_external_proof",
    "pr5_thread_resolved",
    "delivery_result",
    "delivery_success",
)

# 设计约束 01：本 gate 不读取真实 ROS graph、Nav2 runtime、串口、云或手机 runtime。
# 设计约束 02：source 必须来自 request dispatch artifact/summary/wrapper。
# 设计约束 03：source=software_proof、not_proven 和三类 false flag 必须保留。
# 设计约束 04：field-owner response 缺失时只能 missing/blocked，不能伪造 accepted。
# 设计约束 05：accepted 只表示 ready for later review，不代表现场结果。
# 设计约束 06：所有材料必须绑定同一 safe evidence_ref。
# 设计约束 07：mixed evidence_ref 必须 rejected 或整体 fail closed。
# 设计约束 08：unsafe claim、raw topic、/cmd_vel 和本机路径必须 fail closed。
# 设计约束 09：serial/UART/WAVE ROVER、baudrate、checksum 和 traceback 不进入输出。
# 设计约束 10：credential、DB/queue URL、complete artifact 不进入输出。
# 设计约束 11：delivery_success/control claim 必须阻断，不能降级成 accepted。
# 设计约束 12：blocked 是真实采集依赖不可用，不是通过或完成。
# 设计约束 13：missing 是类别未回应，不是拒收或失败证明。
# 设计约束 14：rejected 是有回应但不符合安全契约。
# 设计约束 15：summary 是 Robot/mobile 安全面，不包含 raw response。
# 设计约束 16：safe_copy 字段稳定给后续 review/diagnostics/mobile 复用。
# 设计约束 17：最终 payload 再递归脱敏，防止新增字段绕过扫描。
# 设计约束 18：blocked artifact 也返回 exit code 0，便于 CI 和 sprint 留痕。
# 设计约束 19：状态名全部 snake_case，便于 rg 和下游解析。
# 设计约束 20：所有技术注释使用中文，解释保守边界。

BOUNDARY_NOTE = (
    "field_evidence_real_material_response_intake; "
    "software_proof_docker_field_evidence_real_material_response_intake_gate; "
    "trashbot.field_evidence_real_material_response_intake.v1; "
    "accepted; missing; rejected; blocked; source=software_proof; not_proven; "
    "safe_to_control=false; delivery_success=false; primary_actions_enabled=false"
)


def _utc_now() -> str:
    # UTC 时间便于 PC/Docker 主机之间按同一时间线审计 artifact。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都走 fail-closed 分类，避免默认 accepted。
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
    # wrapper 字段必须是 object；字符串 JSON 不当作可信嵌套对象。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 字段位置不同，取首个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归常见 safe wrapper key，避免把完整 raw material 当 source。
    candidates = [payload]
    for key in (
        "field_evidence_real_material_request_dispatch",
        "field_evidence_real_material_request_dispatch_summary",
        "field_evidence_real_material_response_packet",
        "field_evidence_real_material_response_packet_summary",
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
    # schema 命中上一轮 dispatch 时才作为可信 source；否则保留顶层解释 unsupported。
    for candidate in _candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _find_response(payload: dict[str, Any]) -> dict[str, Any]:
    # response 可有 packet schema，也可直接是安全表单字段。
    for candidate in _candidates(payload):
        schema = str(candidate.get("schema", "")).strip()
        if schema in RESPONSE_SCHEMAS and _has_any_response_material(candidate):
            return candidate
    return payload


def _has_any_response_material(payload: dict[str, Any]) -> bool:
    # 用于区分 wrapper 与实际 response；只看白名单材料容器。
    for key in ("materials", "material_responses", "responses", "received_materials", "blocked_materials"):
        value = payload.get(key)
        if isinstance(value, (dict, list)) and value:
            return True
    return False


def _source_view(source: dict[str, Any]) -> dict[str, Any]:
    # source view 只复制 intake 需要字段，不携带完整 request artifact。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return {
        "schema": _first_text(source.get("schema"), safe_copy.get("schema"), default=""),
        "schema_version": source.get("schema_version", safe_copy.get("schema_version", "")),
        "source": _first_text(source.get("source"), safe_copy.get("source"), robot.get("source"), mobile.get("source"), default=""),
        "evidence_boundary": _first_text(source.get("evidence_boundary"), source.get("boundary"), safe_copy.get("evidence_boundary"), default=""),
        "status": _first_text(
            source.get("request_dispatch_status"),
            source.get("status"),
            safe_copy.get("request_dispatch_status"),
            safe_copy.get("status"),
            robot.get("request_dispatch_status"),
            robot.get("status"),
            mobile.get("request_dispatch_status"),
            mobile.get("status"),
            default="missing",
        ),
        "safe_evidence_ref": _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            default="",
        ),
        "same_evidence_ref_required": source.get(
            "same_evidence_ref_required",
            safe_copy.get("same_evidence_ref_required", robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", True))),
        ),
        "required_materials": source.get("required_materials", safe_copy.get("required_materials", [])),
        "safe_to_control": source.get("safe_to_control", safe_copy.get("safe_to_control", robot.get("safe_to_control", mobile.get("safe_to_control")))),
        "delivery_success": source.get("delivery_success", safe_copy.get("delivery_success", robot.get("delivery_success", mobile.get("delivery_success")))),
        "primary_actions_enabled": source.get(
            "primary_actions_enabled",
            safe_copy.get("primary_actions_enabled", robot.get("primary_actions_enabled", mobile.get("primary_actions_enabled"))),
        ),
        "not_proven": source.get("not_proven", safe_copy.get("not_proven", "not_proven")),
    }


def _source_status(load_issue: str, source: dict[str, Any], source_safe: bool, unsafe: bool) -> dict[str, Any]:
    # source 合同、ready status 和安全 flag 全部满足后才允许接收 response。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded", "ready": False}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(source.get("evidence_boundary", ""))
    supported = schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES
    ready = supported and source.get("status") == READY_DISPATCH_STATUS and source_safe and not unsafe
    return {
        "load_status": "loaded",
        "load_issue": "",
        "schema_status": "supported" if supported else "unsupported",
        "ready": bool(ready),
    }


def _source_is_safe(source: dict[str, Any]) -> bool:
    # source=software_proof、not_proven、三类 false flag 是本链路不可放松的边界。
    encoded = material_pack._encoded(source)
    required = set(source.get("required_materials", [])) if isinstance(source.get("required_materials"), list) else set()
    return (
        source.get("source") == "software_proof"
        and "not_proven" in encoded
        and source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
        and set(REQUIRED_MATERIALS).issubset(required)
    )


def _unsafe_copy(value: Any) -> bool:
    # 禁词、路径和 success/control claim 统一视为不安全输入。
    return (
        material_pack._has_forbidden_copy(value)
        or material_pack._has_raw_path_copy(value)
        or material_pack._has_success_or_control_claim(value)
    )


def _evidence_ref(value: Any) -> str:
    # evidence_ref 若误填路径，使用 material_pack 的 basename 化逻辑。
    return material_pack._safe_ref(value)


def _response_material_map(response: dict[str, Any]) -> dict[str, Any]:
    # 支持 dict 和 list 两类表单形态，最终统一为 material name -> response item。
    for key in ("materials", "material_responses", "responses"):
        value = response.get(key)
        if isinstance(value, dict):
            return {str(name): item for name, item in value.items()}
        if isinstance(value, list):
            mapped: dict[str, Any] = {}
            for item in value:
                if isinstance(item, dict):
                    name = _first_text(item.get("name"), item.get("material"), item.get("category"), default="")
                    if name:
                        mapped[name] = item
            return mapped
    return {}


def _listed_materials(response: dict[str, Any], key: str) -> set[str]:
    # blocked/missing/rejected 简写列表便于现场表单只回状态不填内容。
    value = response.get(key)
    if isinstance(value, list):
        return {str(item.get("name") if isinstance(item, dict) else item) for item in value}
    if isinstance(value, dict):
        return {str(name) for name in value}
    return set()


def _item_status(name: str, item: Any, expected_ref: str, response_ref: str, response_missing: bool) -> tuple[str, list[str], dict[str, Any]]:
    # 单项分类只输出元数据，不复制完整材料内容。
    if response_missing:
        return "blocked", ["field_owner_response_json_not_provided"], {}
    if item is None:
        return "missing", ["required_category_absent"], {}
    if not isinstance(item, dict):
        return "rejected", ["response_item_not_object"], {"item_type": type(item).__name__}

    item_ref = _evidence_ref(_first_text(item.get("safe_evidence_ref"), item.get("evidence_ref"), response_ref, default=""))
    explicit = _first_text(item.get("classification"), item.get("status"), item.get("response_status"), default="").lower()
    safe_note = material_pack._safe_text(_first_text(item.get("summary"), item.get("note"), item.get("reason"), default=""))
    accepted_flag = item.get("accepted") is True or explicit == "accepted"
    blocked_flag = item.get("blocked") is True or explicit == "blocked"
    rejected_flag = item.get("rejected") is True or explicit == "rejected"
    missing_flag = item.get("missing") is True or explicit == "missing"
    reasons: list[str] = []

    if item_ref != expected_ref:
        reasons.append("evidence_ref_mismatch")
    if _unsafe_copy(item):
        reasons.append("unsafe_or_success_control_claim")
    if item.get("delivery_success") is True or item.get("safe_to_control") is True or item.get("primary_actions_enabled") is True:
        reasons.append("unsafe_false_flag_violation")
    if not item_ref:
        reasons.append("missing_evidence_ref")

    if reasons:
        status = "rejected"
        safe_note = ""
    elif blocked_flag:
        status = "blocked"
        reasons = ["field_owner_dependency_blocked"]
    elif rejected_flag:
        status = "rejected"
        reasons = ["field_owner_marked_rejected"]
    elif missing_flag:
        status = "missing"
        reasons = ["field_owner_marked_missing"]
    elif accepted_flag:
        status = "accepted"
        reasons = ["ready_for_later_review_only"]
    else:
        status = "rejected"
        reasons = ["missing_explicit_safe_acceptance_status"]

    details = {
        "material": name,
        "safe_evidence_ref": item_ref,
        "evidence_ref": item_ref,
        "field_owner_status": explicit or ("accepted" if accepted_flag else ""),
        "safe_summary": safe_note[:240],
        "ready_for_later_review_only": status == "accepted",
    }
    return status, reasons, details


def _classify_materials(
    response: dict[str, Any],
    expected_ref: str,
    response_missing: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # 九类材料逐项独立分类；整体 status 再由 accepted/missing/rejected/blocked 汇总。
    material_map = _response_material_map(response)
    response_ref = _evidence_ref(_first_text(response.get("safe_evidence_ref"), response.get("evidence_ref"), default=""))
    blocked_names = _listed_materials(response, "blocked_materials")
    missing_names = _listed_materials(response, "missing_materials")
    rejected_names = _listed_materials(response, "rejected_materials")
    accepted_names = _listed_materials(response, "accepted_materials") | _listed_materials(response, "received_materials")
    items: list[dict[str, Any]] = []
    counts = {status: 0 for status in RESPONSE_STATUSES}

    for name in REQUIRED_MATERIALS:
        item = material_map.get(name)
        if item is None and name in blocked_names:
            item = {"name": name, "status": "blocked", "safe_evidence_ref": response_ref, "reason": "field owner reported dependency unavailable"}
        elif item is None and name in missing_names:
            item = {"name": name, "status": "missing", "safe_evidence_ref": response_ref, "reason": "field owner did not capture material"}
        elif item is None and name in rejected_names:
            item = {"name": name, "status": "rejected", "safe_evidence_ref": response_ref, "reason": "field owner rejected material"}
        elif item is None and name in accepted_names:
            item = {"name": name, "status": "accepted", "safe_evidence_ref": response_ref, "summary": "accepted category index only"}

        status, reasons, details = _item_status(name, item, expected_ref, response_ref, response_missing)
        counts[status] += 1
        items.append(
            {
                "name": name,
                "classification": status,
                "classification_reasons": reasons,
                "safe_evidence_ref": details.get("safe_evidence_ref", expected_ref),
                "evidence_ref": details.get("evidence_ref", expected_ref),
                "ready_for_later_review_only": status == "accepted",
                "not_delivery_result": True,
                "not_delivery_success": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_summary": details.get("safe_summary", ""),
            }
        )
    return items, counts


def _overall_status(source_state: dict[str, Any], response_issue: str, counts: dict[str, Any]) -> str:
    # 整体 status 只反映 intake 可否进入后续 review，不表示现场通过。
    if source_state.get("load_issue"):
        return "blocked_missing_field_evidence_real_material_request_dispatch"
    if source_state.get("schema_status") != "supported":
        return "blocked_unsupported_request_dispatch_schema"
    if not source_state.get("ready"):
        return "blocked_request_dispatch_not_ready"
    if response_issue in {"field_owner_response_json_bad_json", "field_owner_response_json_read_error", "field_owner_response_json_not_object"}:
        return "blocked_bad_field_owner_response_json"
    if response_issue:
        return "blocked_missing_field_owner_response_json"
    if counts["rejected"]:
        return "blocked_rejected_field_owner_response"
    if counts["blocked"]:
        return "blocked_field_owner_dependency_unavailable"
    if counts["missing"]:
        return "blocked_missing_field_owner_materials"
    return "ready_for_field_evidence_real_material_review_not_proven"


def _safe_copy(status: str, evidence_ref: str, source_summary: dict[str, Any], response_items: list[dict[str, Any]], counts: dict[str, Any]) -> dict[str, Any]:
    # safe_copy 是后续 Robot/mobile/复核 gate 的唯一建议消费面。
    return {
        "schema": f"{INTAKE_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": status,
        "response_intake_status": status,
        "evidence_boundary": INTAKE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_request_dispatch": source_summary,
        "required_materials": list(REQUIRED_MATERIALS),
        "response_statuses": list(RESPONSE_STATUSES),
        "material_classification_counts": counts,
        "material_responses": response_items,
        "accepted_means": "ready_for_later_review_only",
        "blocked_claims": list(BLOCKED_CLAIMS),
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(status: str, evidence_ref: str, source_summary: dict[str, Any], response_items: list[dict[str, Any]], counts: dict[str, Any], safe_copy: dict[str, Any]) -> dict[str, Any]:
    # summary 字段保持稳定，便于 rg 围栏和后续跨 owner 对接。
    return {
        "schema": INTAKE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": status,
        "response_intake_status": status,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_request_dispatch": source_summary,
        "required_materials": list(REQUIRED_MATERIALS),
        "response_statuses": list(RESPONSE_STATUSES),
        "material_classification_counts": counts,
        "material_responses": response_items,
        "safe_copy": safe_copy,
        "accepted_means": "ready_for_later_review_only",
        "blocked_claims": list(BLOCKED_CLAIMS),
        "not_proven": ["not_proven"],
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_real_material_response_intake(
    request_dispatch_json: str,
    field_owner_response_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 request dispatch 与可选 field-owner response，生成 fail-closed intake。"""
    source_payload, source_issue = _load_json(request_dispatch_json, "request_dispatch_json")
    source_raw = _find_source(source_payload) if source_payload else {}
    source = _source_view(source_raw) if source_raw else {}
    source_ref = _evidence_ref(source.get("safe_evidence_ref", ""))
    requested_ref = _evidence_ref(evidence_ref) or source_ref
    source_safe_copy = _dict(source_raw, "safe_copy") if source_raw else {}
    source_unsafe = bool(source_raw) and (_unsafe_copy(source) or _unsafe_copy(source_safe_copy))
    source_safe = bool(source) and _source_is_safe(source)
    if evidence_ref and source_ref and requested_ref != source_ref:
        # CLI 指定 evidence_ref 与 source 不一致时，按同证据号硬约束失败。
        source["same_evidence_ref_required"] = False
        source_unsafe = True

    source_state = _source_status(source_issue, source, source_safe, source_unsafe)
    response_payload, response_issue = _load_json(field_owner_response_json, "field_owner_response_json")
    response = _find_response(response_payload) if response_payload else {}
    response_schema = material_pack._safe_text(response.get("schema", ""))
    response_ref = _evidence_ref(_first_text(response.get("safe_evidence_ref"), response.get("evidence_ref"), default=""))
    response_missing = bool(response_issue)
    response_unsafe = bool(response) and (_unsafe_copy(response) or response_schema not in RESPONSE_SCHEMAS)
    if response_ref and requested_ref and response_ref != requested_ref:
        # 顶层 response ref mismatch 让所有存在材料 rejected。
        response_unsafe = True

    response_items, counts = _classify_materials(response, requested_ref, response_missing)
    if response_unsafe:
        # 顶层 unsafe 不能只影响单项；所有非 missing 类别统一 rejected。
        for item in response_items:
            if item["classification"] != "missing":
                item["classification"] = "rejected"
                item["classification_reasons"] = ["unsafe_field_owner_response_or_evidence_ref_mismatch"]
        counts = {status: sum(1 for item in response_items if item["classification"] == status) for status in RESPONSE_STATUSES}
    status = _overall_status(source_state, response_issue, counts)
    source_summary = {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(source.get("evidence_boundary", "")),
        "status": material_pack._safe_text(source.get("status", "missing")),
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": source.get("same_evidence_ref_required", True),
        "source_is_software_proof_not_proven": bool(source_safe),
        "unsafe_copy": bool(source_unsafe),
        "success_or_control_claim": bool(source_raw) and material_pack._has_success_or_control_claim(source_raw),
    }
    safe_copy = _safe_copy(status, requested_ref, source_summary, response_items, counts)
    summary = _summary_payload(status, requested_ref, source_summary, response_items, counts, safe_copy)
    artifact = {
        "schema": INTAKE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": status,
        "response_intake_status": status,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_request_dispatch": source_summary,
        "field_owner_response": {
            "load_issue": response_issue,
            "schema": response_schema,
            "safe_evidence_ref": response_ref,
            "evidence_ref": response_ref,
            "unsafe_copy": bool(response_unsafe),
        },
        "required_materials": list(REQUIRED_MATERIALS),
        "response_statuses": list(RESPONSE_STATUSES),
        "material_classification_counts": counts,
        "material_responses": response_items,
        "safe_copy": safe_copy,
        "field_evidence_real_material_response_intake_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "accepted_means": "ready_for_later_review_only",
        "blocked_claims": list(BLOCKED_CLAIMS),
        "non_access_scope": [
            "low_level_robot_bus_topics",
            "motion_command_channels",
            "hardware_transport_details",
            "credential_or_database_queue_connection_material",
            "host_filesystem_locations",
            "debug_stack_hash_or_full_payload_material",
            "real robot runtime",
            "real phone browser runtime",
        ],
        "not_proven": ["not_proven"],
        "boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if material_pack._has_forbidden_copy(artifact) or material_pack._has_forbidden_copy(summary):
        # 最终防线：输出仍含禁词时强制 blocked，且保留所有 false flags。
        for payload in (artifact, summary):
            payload["status"] = "blocked_unsafe_field_owner_response_copy"
            payload["response_intake_status"] = "blocked_unsafe_field_owner_response_copy"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；未指定时由 CLI 打印 artifact。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 保持 dependency-free，便于 PC、Docker 和 focused unittest 共用。
    parser = argparse.ArgumentParser(description="Generate a field evidence real material response intake artifact")
    parser.add_argument("--request-dispatch-json", required=True, help="request dispatch artifact, summary, or wrapper JSON")
    parser.add_argument("--field-owner-response-json", default="", help="optional safe field-owner response JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref for response intake")
    parser.add_argument("--output", default="", help="optional response intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional response intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print response intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_real_material_response_intake(
        args.request_dispatch_json,
        args.field_owner_response_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_real_material_response_intake: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"response_intake_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"response_intake_status: {artifact['response_intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
