"""Route/elevator field-session handoff diagnostics summary helpers.

本模块承接 operator_gateway_diagnostics 的 route/elevator field-session
handoff 摘要逻辑。这里的摘要只处理 metadata-only software proof，不代表
真实路线、电梯、WAVE ROVER 运动、串口反馈、HIL 或交付闭环通过。
"""

import json
import os

from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_artifacts import (
    _route_task_field_run_console_has_unsafe_fields,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_run import (
    _redact_route_task_rehearsal_text,
    _route_task_field_run_readiness_copy_is_unsafe,
    _safe_pc_route_debug_dict,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
)

ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SCHEMA = (
    "trashbot.route_elevator_field_session_handoff.v1"
)
ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.route_elevator_field_session_handoff_summary.v1"
)
ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_GATE = (
    "software_proof_docker_route_elevator_field_session_handoff_gate"
)


def _route_elevator_field_session_handoff_not_proven(handoff=None, summary_fragment=None):
    # 现场交接摘要只解释下一次 field session 需要补哪些材料；它不能授权控制或代表任何真实运行通过。
    handoff = handoff if isinstance(handoff, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(handoff.get("not_proven"), list):
        source_values.extend(handoff.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_elevator_operation",
        "real_elevator_door_state",
        "real_floor_confirmation",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "route_task_completion_real_world",
        "field_session_pass",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "real_dropoff_completion",
        "real_cancel_completion",
        "dropoff_or_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _default_route_elevator_field_session_handoff_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 现场交接默认 blocked；diagnostics 缺输入时也必须清楚说明这不是控制授权或现场通过证明。
    return {
        "schema": ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "handoff_verdict": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "route elevator field session handoff is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "source_summaries": {},
        "field_session_manifest": {},
        "required_materials_summary": [],
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route elevator field session handoff is not configured",
        },
        "mobile_readonly_summary": {
            "safe_copy": "Route/elevator field session handoff is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Route/elevator field session handoff is metadata-only; delivery_success=false.",
        },
        "not_proven": _route_elevator_field_session_handoff_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _route_elevator_field_session_handoff_source_contract(value):
    # 支持直接 artifact 和已生成 summary；两者都必须停留在同一个 handoff gate，不能混用旧 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_elevator_field_session_handoff_requires_same_evidence_ref(summary_fragment, handoff):
    # field session handoff 的价值是同一 evidence_ref 交接；只接受 JSON boolean true，字符串不算通过。
    value = (
        summary_fragment.get("same_evidence_ref_required")
        if isinstance(summary_fragment, dict) and "same_evidence_ref_required" in summary_fragment
        else handoff.get("same_evidence_ref_required", True)
        if isinstance(handoff, dict)
        else True
    )
    return value is True


def _route_elevator_field_session_handoff_has_disabled_actions(handoff):
    # source 必须显式保留 fail-closed 布尔值；缺失或字符串 false 都不能被手机端当作控制授权。
    if not isinstance(handoff, dict):
        return False
    return (
        handoff.get("delivery_success") is False
        and handoff.get("primary_actions_enabled") is False
    )


def summarize_route_elevator_field_session_handoff(path):
    """构建 route/elevator field session handoff 的 metadata-only diagnostics 摘要。"""
    handoff_path = os.path.expanduser(str(path or ""))
    summary = _default_route_elevator_field_session_handoff_summary(
        handoff_path,
        read_error="route elevator field session handoff is not configured",
    )
    if not handoff_path:
        return summary
    if not os.path.exists(handoff_path):
        summary.update(
            {
                "handoff_verdict": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "route elevator field session handoff artifact missing",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "handoff artifact missing"},
                "mobile_readonly_summary": {
                    "safe_copy": "Route/elevator field session handoff is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route/elevator field session handoff is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(handoff_path, "r", encoding="utf-8") as f:
            handoff = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading route elevator field session handoff: {exc}"
        )
        summary.update(
            {
                "handoff_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": safe_error,
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "handoff JSON read error"},
                "mobile_readonly_summary": {
                    "safe_copy": "Route/elevator field session handoff could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route/elevator field session handoff could not be read; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route elevator field session handoff JSON must be an object",
                },
                "robot_diagnostics_summary": {"status": "blocked", "reason": "handoff JSON shape is invalid"},
                "mobile_readonly_summary": {
                    "safe_copy": "Route/elevator field session handoff shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route/elevator field session handoff shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # 只读取 artifact/summary 中的白名单摘要；raw 材料、路径、checksum 和控制信封不会被透传到 diagnostics。
    summary_fragment = {}
    for candidate in (
        handoff.get("mobile_readonly_summary"),
        handoff.get("phone_safe_summary"),
        handoff.get("mobile_safe_summary"),
        handoff.get("robot_diagnostics_summary"),
        handoff.get("route_elevator_field_session_handoff_summary"),
        handoff.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    robot_summary = (
        handoff.get("robot_diagnostics_summary")
        if isinstance(handoff.get("robot_diagnostics_summary"), dict)
        else handoff.get("diagnostics_summary")
        if isinstance(handoff.get("diagnostics_summary"), dict)
        else {}
    )
    source_schema, source_boundary = _route_elevator_field_session_handoff_source_contract(handoff)
    source_verdict = summary_fragment.get("handoff_verdict")
    if not isinstance(source_verdict, dict):
        source_verdict = handoff.get("handoff_verdict")
    if isinstance(source_verdict, dict):
        verdict_status = _redact_route_task_rehearsal_text(
            source_verdict.get("status")
            or source_verdict.get("verdict")
            or source_verdict.get("decision")
            or handoff.get("status")
            or "blocked"
        )
        verdict_value = _redact_route_task_rehearsal_text(
            source_verdict.get("verdict")
            or source_verdict.get("decision")
            or verdict_status
            or "not_proven"
        )
        verdict_reason = _redact_route_task_rehearsal_text(
            source_verdict.get("reason") or source_verdict.get("summary") or ""
        )
    else:
        verdict_status = _redact_route_task_rehearsal_text(
            summary_fragment.get("handoff_verdict")
            or summary_fragment.get("status")
            or summary_fragment.get("overall_status")
            or handoff.get("handoff_verdict")
            or handoff.get("status")
            or "blocked"
        )
        verdict_value = _redact_route_task_rehearsal_text(
            summary_fragment.get("verdict")
            or handoff.get("verdict")
            or verdict_status
            or "not_proven"
        )
        verdict_reason = _redact_route_task_rehearsal_text(
            summary_fragment.get("reason") or handoff.get("reason") or ""
        )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or handoff.get("safe_copy")
        or handoff.get("safe_phone_copy")
        or "Route/elevator field session handoff is metadata-only; delivery_success=false."
    )
    mobile_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            mobile_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    mobile_summary["safe_copy"] = safe_copy
    mobile_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": handoff.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "handoff_verdict": {
                "status": verdict_status or "blocked",
                "verdict": verdict_value or "not_proven",
                "reason": verdict_reason or "route elevator field session handoff consumed without explicit reason",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or handoff.get("safe_evidence_ref")
                or handoff.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": _route_elevator_field_session_handoff_requires_same_evidence_ref(
                summary_fragment,
                handoff,
            ),
            "source_summaries": _safe_pc_route_debug_dict(
                summary_fragment.get("source_summaries")
                if isinstance(summary_fragment.get("source_summaries"), dict)
                else handoff.get("source_summaries")
                if isinstance(handoff.get("source_summaries"), dict)
                else {}
            ),
            "field_session_manifest": _safe_pc_route_debug_dict(
                summary_fragment.get("field_session_manifest")
                if isinstance(summary_fragment.get("field_session_manifest"), dict)
                else handoff.get("field_session_manifest")
                if isinstance(handoff.get("field_session_manifest"), dict)
                else {}
            ),
            "required_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("required_materials_summary")
                if isinstance(summary_fragment.get("required_materials_summary"), list)
                else handoff.get("required_materials_summary")
                if isinstance(handoff.get("required_materials_summary"), list)
                else handoff.get("required_materials")
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                summary_fragment.get("operator_next_steps")
                if isinstance(summary_fragment.get("operator_next_steps"), list)
                else handoff.get("operator_next_steps")
                if isinstance(handoff.get("operator_next_steps"), list)
                else handoff.get("operator_handoff", {}).get("operator_next_steps")
                if isinstance(handoff.get("operator_handoff"), dict)
                else []
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": verdict_status or "blocked",
                "reason": "handoff consumed without explicit robot diagnostics summary",
            },
            "mobile_readonly_summary": mobile_summary,
            "not_proven": _route_elevator_field_session_handoff_not_proven(
                handoff,
                summary_fragment,
            ),
            "read_error": "",
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SCHEMA,
        ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_GATE:
        summary.update(
            {
                "handoff_verdict": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route elevator field session handoff schema or evidence boundary is unsupported",
                },
                "source_summaries": {},
                "field_session_manifest": {},
                "required_materials_summary": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route/elevator field session handoff is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route/elevator field session handoff is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        not summary["same_evidence_ref_required"]
        or not _route_elevator_field_session_handoff_has_disabled_actions(handoff)
        or _route_task_field_run_console_has_unsafe_fields(handoff)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "handoff_verdict": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route elevator field session handoff contains unsafe fields or success/control claims",
                },
                "source_summaries": {},
                "field_session_manifest": {},
                "required_materials_summary": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe handoff summary fields",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route/elevator field session handoff was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                    "safe_phone_copy": "Route/elevator field session handoff was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                },
            }
        )
        return summary

    return summary
