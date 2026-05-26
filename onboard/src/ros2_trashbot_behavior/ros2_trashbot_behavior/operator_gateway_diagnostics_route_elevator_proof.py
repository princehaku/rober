"""Route completion, elevator proof, and traceability diagnostics helpers.

本模块承接 operator_gateway_diagnostics 的路线完成、电梯复账和 traceability
只读诊断域。这里所有 summary 都是 metadata-only/software_proof，不能升级为
真实 Nav2、WAVE ROVER、串口反馈、HIL、投放完成或 delivery success。
"""

import json
import os

from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_artifacts import (
    _route_task_field_run_console_has_unsafe_fields,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_run import (
    _route_task_field_run_readiness_copy_is_unsafe,
    _route_task_field_run_readiness_has_unsafe_fields,
    _safe_pc_route_debug_dict,
    _safe_pc_route_debug_value,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_rehearsal import (
    _redact_route_task_rehearsal_text,
)
from ros2_trashbot_behavior.operator_gateway_http import normalize_elevator_assist


EVIDENCE_SOURCE_SOFTWARE = "software_proof"
EVIDENCE_SOURCE_HIL = "hil_pass"
VALID_EVIDENCE_SOURCES = {EVIDENCE_SOURCE_SOFTWARE, EVIDENCE_SOURCE_HIL}

ROUTE_PROOF_REQUIRED_FIELDS = (
    "coverage_rate",
    "covered_checkpoints",
    "total_checkpoints",
    "missing_checkpoints",
    "gate_status",
    "last_block_reason",
)
ROUTE_PROOF_WAITING_GATE_STATUSES = {
    "waiting_visual_gate",
    "waiting",
    "pending",
    "blocked_by_visual_gate",
    "waiting_camera_frame",
    "missing_live_frame",
    "keyframe_preflight_failed",
    "missing_keyframe",
    "no_live_descriptors",
    "insufficient_matches",
}
ROUTE_PROOF_READY_GATE_STATUSES = {"passed", "ready", "ok"}
ELEVATOR_ASSIST_HELP_REASONS = {
    "door_timeout",
    "door_closed_or_unknown",
    "target_floor_unconfirmed",
    "target_floor_evidence_unreliable",
    "unsafe_to_enter",
    "unsafe_to_exit",
    "manual_takeover_required",
}

ROUTE_TASK_COMPLETION_SIGNAL_SCHEMA = "trashbot.route_task_completion_signal.v1"
ROUTE_TASK_COMPLETION_SIGNAL_SUMMARY_SCHEMA = (
    "trashbot.route_task_completion_signal_summary.v1"
)
ROUTE_TASK_COMPLETION_SIGNAL_GATE = (
    "software_proof_docker_route_task_completion_signal_gate"
)
ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SCHEMA = (
    "trashbot.elevator_route_evidence_reconciliation.v1"
)
ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY_SCHEMA = (
    "trashbot.elevator_route_evidence_reconciliation_summary.v1"
)
ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_GATE = (
    "software_proof_docker_elevator_route_evidence_reconciliation_gate"
)
ELEVATOR_ACTION_FEEDBACK_TRACE_SCHEMA = "trashbot.elevator_action_feedback_trace.v1"
ELEVATOR_ACTION_FEEDBACK_TRACE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_elevator_action_feedback_trace_summary.v1"
)


def _safe_float(value):
    # route proof 的 coverage 可能来自 JSON 数字或表单字符串；解析失败必须返回 None 进入 unknown。
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _route_task_completion_signal_not_proven(signal=None, phone_summary=None):
    # completion signal 只描述材料是否足够进入人工复核；真实完成、ACK、Nav2/HIL 和投放结果仍必须外部证明。
    signal = signal if isinstance(signal, dict) else {}
    phone_summary = phone_summary if isinstance(phone_summary, dict) else {}
    values = []
    source_values = []
    if isinstance(signal.get("not_proven"), list):
        source_values.extend(signal.get("not_proven"))
    if isinstance(phone_summary.get("not_proven"), list):
        source_values.extend(phone_summary.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "real_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "production_readiness",
        "real_dropoff_completion",
        "real_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _elevator_route_evidence_reconciliation_not_proven(
    reconciliation=None,
    summary_fragment=None,
):
    # 电梯路线复账只读消费 Autonomy artifact；它只能说明材料同 ref 检查状态，不能代表任何机器人动作完成。
    reconciliation = reconciliation if isinstance(reconciliation, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(reconciliation.get("not_proven"), list):
        source_values.extend(reconciliation.get("not_proven"))
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
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "production_readiness",
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


def _default_route_task_completion_signal_summary(path, status="not_configured", read_error=""):
    # completion signal 是 Task A 的只读完成材料摘要；默认 blocked，避免缺配置时被误读成送达完成。
    return {
        "schema": ROUTE_TASK_COMPLETION_SIGNAL_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_COMPLETION_SIGNAL_GATE,
        "source_schema": "",
        "source_evidence_boundary": "",
        "completion_verdict": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "route-task completion signal artifact is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "fixed_route_summary": {},
        "task_record_summary": {},
        "state_transition_summary": {},
        "dropoff_completion": {"status": "not_proven"},
        "cancel_completion": {"status": "not_proven"},
        "failure_reason": "",
        "recovery_reason": "",
        "materials_status": {
            "status": "blocked",
            "reason": "route-task completion signal artifact is not configured",
        },
        "operator_next_steps": [],
        "phone_safe_summary": {
            "safe_copy": "Route-task completion signal is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Route-task completion signal is metadata-only; delivery_success=false.",
        },
        "not_proven": _route_task_completion_signal_not_proven(),
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _default_elevator_route_evidence_reconciliation_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 复账 artifact 默认 blocked；缺配置时也必须显式关闭动作链，避免 diagnostics 被手机端误用。
    return {
        "schema": ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "reconciliation_verdict": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "elevator route evidence reconciliation is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "source_states": {},
        "materials_status": {
            "status": "blocked",
            "reason": "elevator route evidence reconciliation is not configured",
        },
        "missing_materials": [],
        "mismatch_reasons": [],
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "elevator route evidence reconciliation is not configured",
        },
        "phone_safe_summary": {
            "safe_copy": "Elevator route evidence reconciliation is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Elevator route evidence reconciliation is metadata-only; delivery_success=false.",
        },
        "not_proven": _elevator_route_evidence_reconciliation_not_proven(),
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


def _route_task_completion_signal_source_contract(value):
    # completion signal 只接受原始 Task A artifact；summary wrapper 不能绕过 source gate 校验。
    value = value if isinstance(value, dict) else {}
    return str(value.get("schema") or ""), str(value.get("evidence_boundary") or "")


def _route_task_completion_signal_has_unsafe_control_claims(value):
    # completion signal 允许暴露 dropoff/cancel 的只读状态摘要，但不能把布尔成功或控制动作带进 diagnostics。
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "ack_post_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "nav2_triggered",
        "hil_pass",
        "production_ready",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "safe_to_control",
        "control_grant",
        "robot_command_allowed",
        "commands_enabled",
    }
    completion_metadata_keys = {"dropoff_completion", "cancel_completion"}
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text in unsafe_true_keys and bool(item):
                return True
            if key_text in completion_metadata_keys and item is True:
                return True
            if _route_task_completion_signal_has_unsafe_control_claims(item):
                return True
        return False
    if isinstance(value, list):
        return any(_route_task_completion_signal_has_unsafe_control_claims(item) for item in value)
    return False


def _elevator_route_evidence_reconciliation_source_contract(value):
    # 允许直接 artifact 或 summary wrapper；wrapper 必须保留原始 schema/boundary，防止把别的 gate 混入。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _elevator_route_reconciliation_requires_same_evidence_ref(summary_fragment, reconciliation):
    # 同 evidence_ref 是本 gate 的核心约束；只接受 JSON boolean true，字符串真值不能算通过。
    value = (
        summary_fragment.get("same_evidence_ref_required")
        if isinstance(summary_fragment, dict) and "same_evidence_ref_required" in summary_fragment
        else reconciliation.get("same_evidence_ref_required", True)
        if isinstance(reconciliation, dict)
        else True
    )
    return value is True


def _elevator_route_reconciliation_has_disabled_actions(reconciliation):
    # 本 gate 要求 source 明确写出两个 false；缺失或字符串 false 都不能当成 fail-closed 证明。
    if not isinstance(reconciliation, dict):
        return False
    return (
        reconciliation.get("delivery_success") is False
        and reconciliation.get("primary_actions_enabled") is False
    )


def summarize_route_task_completion_signal(path):
    """构建 route-task completion signal 的 metadata-only diagnostics 摘要。"""
    signal_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_completion_signal_summary(
        signal_path,
        read_error="route-task completion signal artifact is not configured",
    )
    if not signal_path:
        return summary
    if not os.path.exists(signal_path):
        summary.update(
            {
                "completion_verdict": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "route-task completion signal artifact missing",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "completion signal artifact missing",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task completion signal is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task completion signal is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(signal_path, "r", encoding="utf-8") as f:
            signal = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading route-task completion signal artifact: {exc}"
        )
        summary.update(
            {
                "completion_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": safe_error,
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "completion signal JSON read error",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task completion signal could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task completion signal could not be read; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    if not isinstance(signal, dict):
        summary.update(
            {
                "completion_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task completion signal JSON must be an object",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "completion signal JSON shape is invalid",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task completion signal shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task completion signal shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # Task A/Autonomy 可能把手机安全摘要放在多个兼容字段；Robot diagnostics 只读取白名单字段。
    phone_summary = {}
    for candidate in (
        signal.get("phone_safe_summary"),
        signal.get("phone_support_safe_summary"),
        signal.get("route_task_completion_signal_summary"),
        signal.get("route_task_completion_signal"),
    ):
        if isinstance(candidate, dict):
            phone_summary = candidate
            break
    source_schema, source_boundary = _route_task_completion_signal_source_contract(signal)
    source_verdict = phone_summary.get("completion_verdict")
    if not isinstance(source_verdict, dict):
        source_verdict = signal.get("completion_verdict")
    if isinstance(source_verdict, dict):
        verdict_status = _redact_route_task_rehearsal_text(
            source_verdict.get("status")
            or source_verdict.get("verdict")
            or source_verdict.get("decision")
            or signal.get("status")
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
            phone_summary.get("status")
            or phone_summary.get("overall_status")
            or signal.get("status")
            or "blocked"
        )
        verdict_value = _redact_route_task_rehearsal_text(
            phone_summary.get("verdict")
            or signal.get("verdict")
            or verdict_status
            or "not_proven"
        )
        verdict_reason = _redact_route_task_rehearsal_text(
            phone_summary.get("reason") or signal.get("reason") or ""
        )
    materials_status = (
        phone_summary.get("materials_status")
        if isinstance(phone_summary.get("materials_status"), dict)
        else signal.get("materials_status") if isinstance(signal.get("materials_status"), dict) else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or signal.get("safe_copy")
        or signal.get("safe_phone_copy")
        or "Route-task completion signal is metadata-only; delivery_success=false."
    )
    # completion signal 的字段可能接近“完成”语义；只保留脱敏摘要，真实执行成功一律不从这里推断。
    safe_phone_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(phone_summary.get(key) or "").strip():
            safe_phone_summary[key] = _redact_route_task_rehearsal_text(phone_summary.get(key))
    safe_phone_summary["safe_copy"] = safe_copy
    safe_phone_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": signal.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "completion_verdict": {
                "status": verdict_status or "blocked",
                "verdict": verdict_value or "not_proven",
                "reason": verdict_reason or "route-task completion signal consumed without explicit reason",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                phone_summary.get("safe_evidence_ref")
                or phone_summary.get("evidence_ref")
                or signal.get("safe_evidence_ref")
                or signal.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                phone_summary.get(
                    "same_evidence_ref_required",
                    signal.get("same_evidence_ref_required", True),
                )
            ),
            "fixed_route_summary": _safe_pc_route_debug_dict(signal.get("fixed_route_summary")),
            "task_record_summary": _safe_pc_route_debug_dict(signal.get("task_record_summary")),
            "state_transition_summary": _safe_pc_route_debug_dict(
                signal.get("state_transition_summary")
            ),
            "dropoff_completion": _safe_pc_route_debug_value(
                signal.get("dropoff_completion") or {"status": "not_proven"}
            ),
            "cancel_completion": _safe_pc_route_debug_value(
                signal.get("cancel_completion") or {"status": "not_proven"}
            ),
            "failure_reason": _redact_route_task_rehearsal_text(signal.get("failure_reason")),
            "recovery_reason": _redact_route_task_rehearsal_text(signal.get("recovery_reason")),
            "materials_status": _safe_pc_route_debug_dict(materials_status)
            or {
                "status": verdict_status or "blocked",
                "reason": "completion signal consumed without explicit materials status",
            },
            "operator_next_steps": _safe_route_task_rehearsal_list(
                phone_summary.get("operator_next_steps")
                if isinstance(phone_summary.get("operator_next_steps"), list)
                else signal.get("operator_next_steps")
            ),
            "phone_safe_summary": safe_phone_summary,
            "not_proven": _route_task_completion_signal_not_proven(signal, phone_summary),
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema != ROUTE_TASK_COMPLETION_SIGNAL_SCHEMA or source_boundary != ROUTE_TASK_COMPLETION_SIGNAL_GATE:
        summary.update(
            {
                "completion_verdict": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task completion signal schema or evidence boundary is unsupported",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task completion signal is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task completion signal is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        _route_task_field_run_readiness_has_unsafe_fields(phone_summary)
        or _route_task_completion_signal_has_unsafe_control_claims(signal)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "completion_verdict": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task completion signal contains unsafe summary fields or control claims",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "unsafe completion signal summary fields",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task completion signal was blocked because summary fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Route-task completion signal was blocked because summary fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_elevator_route_evidence_reconciliation(path):
    """构建 elevator route evidence reconciliation 的 metadata-only diagnostics 摘要。"""
    reconciliation_path = os.path.expanduser(str(path or ""))
    summary = _default_elevator_route_evidence_reconciliation_summary(
        reconciliation_path,
        read_error="elevator route evidence reconciliation is not configured",
    )
    if not reconciliation_path:
        return summary
    if not os.path.exists(reconciliation_path):
        summary.update(
            {
                "reconciliation_verdict": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "elevator route evidence reconciliation artifact missing",
                },
                "materials_status": {"status": "blocked", "reason": "reconciliation artifact missing"},
                "robot_diagnostics_summary": {"status": "blocked", "reason": "reconciliation artifact missing"},
                "phone_safe_summary": {
                    "safe_copy": "Elevator route evidence reconciliation is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator route evidence reconciliation is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(reconciliation_path, "r", encoding="utf-8") as f:
            reconciliation = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading elevator route evidence reconciliation: {exc}"
        )
        summary.update(
            {
                "reconciliation_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": safe_error,
                },
                "materials_status": {"status": "blocked", "reason": "reconciliation JSON read error"},
                "robot_diagnostics_summary": {"status": "blocked", "reason": "reconciliation JSON read error"},
                "phone_safe_summary": {
                    "safe_copy": "Elevator route evidence reconciliation could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator route evidence reconciliation could not be read; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    if not isinstance(reconciliation, dict):
        summary.update(
            {
                "reconciliation_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "elevator route evidence reconciliation JSON must be an object",
                },
                "materials_status": {"status": "blocked", "reason": "reconciliation JSON shape is invalid"},
                "robot_diagnostics_summary": {"status": "blocked", "reason": "reconciliation JSON shape is invalid"},
                "phone_safe_summary": {
                    "safe_copy": "Elevator route evidence reconciliation shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator route evidence reconciliation shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # Autonomy artifact/summary 可能使用不同摘要键；Robot 只读取白名单字段，避免透传原始材料。
    summary_fragment = {}
    for candidate in (
        reconciliation.get("phone_safe_summary"),
        reconciliation.get("mobile_readonly_summary"),
        reconciliation.get("mobile_safe_summary"),
        reconciliation.get("elevator_route_evidence_reconciliation_summary"),
        reconciliation.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    robot_summary = (
        reconciliation.get("robot_diagnostics_summary")
        if isinstance(reconciliation.get("robot_diagnostics_summary"), dict)
        else reconciliation.get("diagnostics_summary")
        if isinstance(reconciliation.get("diagnostics_summary"), dict)
        else {}
    )
    source_schema, source_boundary = _elevator_route_evidence_reconciliation_source_contract(
        reconciliation
    )
    source_verdict = summary_fragment.get("reconciliation_verdict")
    if not isinstance(source_verdict, dict):
        source_verdict = reconciliation.get("reconciliation_verdict")
    if isinstance(source_verdict, dict):
        verdict_status = _redact_route_task_rehearsal_text(
            source_verdict.get("status")
            or source_verdict.get("verdict")
            or source_verdict.get("decision")
            or reconciliation.get("status")
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
            summary_fragment.get("status")
            or summary_fragment.get("overall_status")
            or reconciliation.get("status")
            or "blocked"
        )
        verdict_value = _redact_route_task_rehearsal_text(
            summary_fragment.get("verdict")
            or reconciliation.get("verdict")
            or verdict_status
            or "not_proven"
        )
        verdict_reason = _redact_route_task_rehearsal_text(
            summary_fragment.get("reason") or reconciliation.get("reason") or ""
        )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or reconciliation.get("safe_copy")
        or reconciliation.get("safe_phone_copy")
        or "Elevator route evidence reconciliation is metadata-only; delivery_success=false."
    )
    safe_phone_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            safe_phone_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    safe_phone_summary["safe_copy"] = safe_copy
    safe_phone_summary["safe_phone_copy"] = safe_copy
    materials_status = (
        summary_fragment.get("materials_status")
        if isinstance(summary_fragment.get("materials_status"), dict)
        else reconciliation.get("materials_status")
        if isinstance(reconciliation.get("materials_status"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": reconciliation.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "reconciliation_verdict": {
                "status": verdict_status or "blocked",
                "verdict": verdict_value or "not_proven",
                "reason": verdict_reason or "elevator route evidence reconciliation consumed without explicit reason",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or reconciliation.get("safe_evidence_ref")
                or reconciliation.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": _elevator_route_reconciliation_requires_same_evidence_ref(
                summary_fragment,
                reconciliation,
            ),
            "source_states": _safe_pc_route_debug_dict(
                summary_fragment.get("source_states")
                if isinstance(summary_fragment.get("source_states"), dict)
                else reconciliation.get("source_states")
                if isinstance(reconciliation.get("source_states"), dict)
                else {}
            ),
            "materials_status": _safe_pc_route_debug_dict(materials_status)
            or {
                "status": verdict_status or "blocked",
                "reason": "reconciliation consumed without explicit materials status",
            },
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
                if isinstance(summary_fragment.get("missing_materials"), list)
                else reconciliation.get("missing_materials")
            ),
            "mismatch_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("mismatch_reasons")
                if isinstance(summary_fragment.get("mismatch_reasons"), list)
                else reconciliation.get("mismatch_reasons")
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                summary_fragment.get("operator_next_steps")
                if isinstance(summary_fragment.get("operator_next_steps"), list)
                else reconciliation.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": verdict_status or "blocked",
                "reason": "reconciliation consumed without explicit robot diagnostics summary",
            },
            "phone_safe_summary": safe_phone_summary,
            "not_proven": _elevator_route_evidence_reconciliation_not_proven(
                reconciliation,
                summary_fragment,
            ),
            "read_error": "",
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema != ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SCHEMA or source_boundary != ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_GATE:
        summary.update(
            {
                "reconciliation_verdict": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "elevator route evidence reconciliation schema or evidence boundary is unsupported",
                },
                "source_states": {},
                "materials_status": {"status": "blocked", "reason": "unsupported schema or evidence boundary"},
                "missing_materials": [],
                "mismatch_reasons": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "phone_safe_summary": {
                    "safe_copy": "Elevator route evidence reconciliation is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Elevator route evidence reconciliation is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        not summary["same_evidence_ref_required"]
        or not _elevator_route_reconciliation_has_disabled_actions(reconciliation)
        or _route_task_field_run_console_has_unsafe_fields(reconciliation)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "reconciliation_verdict": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "elevator route evidence reconciliation contains unsafe fields or weakens same evidence_ref constraints",
                },
                "source_states": {},
                "materials_status": {"status": "blocked", "reason": "unsafe reconciliation summary fields"},
                "missing_materials": [],
                "mismatch_reasons": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe reconciliation summary fields",
                },
                "phone_safe_summary": {
                    "safe_copy": "Elevator route evidence reconciliation was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                    "safe_phone_copy": "Elevator route evidence reconciliation was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def _read_task_record(path):
    # task_record 只是 traceability 输入，读取失败必须返回空对象并让上层进入缺材料状态。
    record_path = os.path.expanduser(str(path or ""))
    if not record_path or not os.path.exists(record_path):
        return {}
    try:
        with open(record_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _route_proof_from_task_record(task_record):
    # 兼容新旧 task_record 形态：顶层优先，其次读取最新 nav_result 里的 proof summary。
    if not isinstance(task_record, dict):
        return None, ""
    summary = task_record.get("route_proof_summary")
    if isinstance(summary, dict):
        return summary, "task_record.route_proof_summary"
    nav_results = task_record.get("nav_results")
    if not isinstance(nav_results, list):
        return None, ""
    for nav_result in reversed(nav_results):
        if not isinstance(nav_result, dict):
            continue
        candidate = nav_result.get("route_proof_summary")
        if isinstance(candidate, dict):
            return candidate, "task_record.nav_results.route_proof_summary"
        evidence = nav_result.get("evidence")
        if isinstance(evidence, dict) and isinstance(evidence.get("route_proof_summary"), dict):
            return evidence.get("route_proof_summary"), "task_record.nav_results.evidence.route_proof_summary"
    return None, ""


def _extract_route_proof_summary(latest_status, last_task):
    # gateway status 的实时字段优先于 task_record，避免旧文件覆盖当前内存状态。
    latest_status = latest_status if isinstance(latest_status, dict) else {}
    last_task = last_task if isinstance(last_task, dict) else {}
    for summary, source in (
        (latest_status.get("route_proof_summary"), "latest_status.route_proof_summary"),
        (last_task.get("route_proof_summary"), "last_task.route_proof_summary"),
    ):
        if isinstance(summary, dict):
            return dict(summary), source
    task_record_path = (
        latest_status.get("task_record_path")
        or last_task.get("task_record_path")
        or ""
    )
    task_record = _read_task_record(task_record_path)
    summary, source = _route_proof_from_task_record(task_record)
    if isinstance(summary, dict):
        return dict(summary), source
    return {}, ""


def normalize_evidence_source(value):
    """Normalize evidence provenance to user-facing contracts.

    Source tags are intentionally limited to two values so O2/O3 users can
    clearly distinguish offline replay evidence from real hardware-in-loop evidence:
    - hil_pass: evidence is robot-side validated with HIL/real hardware artifacts.
    - software_proof: software-only proof is available but HIL is still required.
    """
    normalized = str(value or "").strip().lower().replace("-", "_")
    if normalized in VALID_EVIDENCE_SOURCES:
        return normalized
    if normalized in {
        "task_orchestrator",
        "dry_run",
        "robot_sim",
        "simulated",
        "software",
        "software_proof",
    }:
        if normalized == "software":
            return EVIDENCE_SOURCE_SOFTWARE
        return EVIDENCE_SOURCE_SOFTWARE
    if normalized == "hil":
        return EVIDENCE_SOURCE_HIL
    return EVIDENCE_SOURCE_SOFTWARE


def _extract_traceability_field(payload, field_name, *fallbacks):
    """Read a traceability field using explicit ownership precedence.

    Priority:
    1) `payload` (authoritative task_record)
    2) each fallback payload in order
    """
    if isinstance(payload, dict) and field_name in payload:
        return payload.get(field_name)
    for fallback_payload in fallbacks:
        if isinstance(fallback_payload, dict) and field_name in fallback_payload:
            return fallback_payload.get(field_name)
    return None


def _extract_route_progress(payload, *fallbacks):
    # route_progress 可能嵌在 nav_results.evidence；从最新结果倒序读取可保留旧 task_record 兼容。
    for candidate_payload in (payload, *fallbacks):
        if not isinstance(candidate_payload, dict):
            continue
        route_progress = candidate_payload.get("route_progress")
        if isinstance(route_progress, dict) and route_progress:
            return dict(route_progress)
        nav_results = candidate_payload.get("nav_results")
        if not isinstance(nav_results, list):
            continue
        for nav_result in reversed(nav_results):
            if not isinstance(nav_result, dict):
                continue
            evidence = nav_result.get("evidence")
            if not isinstance(evidence, dict):
                continue
            route_progress = evidence.get("route_progress")
            if isinstance(route_progress, dict) and route_progress:
                return dict(route_progress)
    return {}


def coalesce_traceability_fields(latest_status, *, task_record=None, last_task=None):
    """Return one canonical traceability bundle for diagnostics and gateway status."""
    latest_status = latest_status if isinstance(latest_status, dict) else {}
    last_task = last_task if isinstance(last_task, dict) else {}
    if not isinstance(task_record, dict):
        task_record = _read_task_record(latest_status.get("task_record_path"))

    task_record_path = str(
        latest_status.get("task_record_path")
        or last_task.get("task_record_path")
        or ""
    ).strip()
    result_path = str(
        _extract_traceability_field(
            task_record,
            "result_path",
            latest_status,
            last_task,
        )
        or task_record_path
        or ""
    )
    evidence_ref = str(
        _extract_traceability_field(
            task_record,
            "evidence_ref",
            latest_status,
            last_task,
        )
        or result_path
        or task_record_path
        or ""
    )
    failure_code = str(
        _extract_traceability_field(
            task_record,
            "failure_code",
            latest_status,
            last_task,
        )
        or _extract_traceability_field(latest_status, "error_code")
        or _extract_traceability_field(last_task, "error_code")
        or ""
    )
    if "human_intervention_required" in task_record:
        human_intervention_required = bool(task_record.get("human_intervention_required"))
    elif "human_intervention_required" in latest_status:
        human_intervention_required = bool(latest_status.get("human_intervention_required"))
    elif "human_intervention_required" in last_task:
        human_intervention_required = bool(last_task.get("human_intervention_required"))
    else:
        human_intervention_required = False

    state_transition_history = task_record.get("state_transition_history")
    if not isinstance(state_transition_history, list):
        state_transition_history = task_record.get("state_transitions")
        if not isinstance(state_transition_history, list):
            state_transition_history = _extract_traceability_field(
                last_task,
                "state_transition_history",
                latest_status,
            )
            if not isinstance(state_transition_history, list):
                state_transition_history = []
    return {
        "source": normalize_evidence_source(
            _extract_traceability_field(
                task_record,
                "source",
                latest_status,
                last_task,
            )
            or ""
        ),
        "result_path": result_path,
        "evidence_ref": evidence_ref,
        "failure_code": failure_code,
        "human_intervention_required": bool(human_intervention_required),
        "state_transition_history": state_transition_history,
        "task_record_path": task_record_path,
        "route_progress": _extract_route_progress(task_record, latest_status, last_task),
    }


def _elevator_assist_from_task_record(task_record):
    # 电梯 assist 兼容顶层、events 和 nav_results 嵌套三种来源，保持旧 payload 可读。
    if not isinstance(task_record, dict):
        return None, ""
    direct = task_record.get("elevator_assist")
    if isinstance(direct, dict):
        return direct, "task_record.elevator_assist"
    events = task_record.get("elevator_assist_events")
    if isinstance(events, list) and events:
        latest_event = events[-1] if isinstance(events[-1], dict) else {}
        return {
            "enabled": True,
            "mode": "dry_run",
            "state": latest_event.get("state") or latest_event.get("phase") or "",
            "phase": latest_event.get("phase") or latest_event.get("state") or "",
            "requires_human_help": bool(latest_event.get("requires_human_help", False)),
            "reason": latest_event.get("reason", ""),
            "target_floor": latest_event.get("target_floor", ""),
            "evidence": latest_event.get("evidence") if isinstance(latest_event.get("evidence"), dict) else {},
            "events": events,
        }, "task_record.elevator_assist_events"
    nav_results = task_record.get("nav_results")
    if not isinstance(nav_results, list):
        return None, ""
    for nav_result in reversed(nav_results):
        if not isinstance(nav_result, dict):
            continue
        candidate = nav_result.get("elevator_assist")
        if isinstance(candidate, dict):
            return candidate, "task_record.nav_results.elevator_assist"
        evidence = nav_result.get("evidence")
        if isinstance(evidence, dict) and isinstance(evidence.get("elevator_assist"), dict):
            return evidence.get("elevator_assist"), "task_record.nav_results.evidence.elevator_assist"
    return None, ""


def _elevator_action_feedback_trace_from_payloads(*payloads):
    # diagnostics 只接受已经沉淀的 trace 摘要或 task_record 字段，不从任意 raw JSON 推导动作。
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        for key in (
            "elevator_action_feedback_trace",
            "robot_diagnostics_elevator_action_feedback_trace_summary",
        ):
            candidate = payload.get(key)
            if isinstance(candidate, dict):
                return candidate, key
    return {}, ""


def _elevator_trace_float(value):
    # trace 百分比来自 UI/日志，解析失败保持 None，避免把坏数据当作进度。
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_elevator_action_feedback_trace(trace=None, *, source=""):
    # 该 summary 给 mobile/full-stack 消费，只暴露阶段、current_step 和安全边界。
    # delivery_success/primary_actions_enabled 永远保持 false，防止 UI 把 trace 当成控制授权。
    trace = trace if isinstance(trace, dict) else {}
    source_text = str(source or "").strip()
    supported = trace.get("schema") == ELEVATOR_ACTION_FEEDBACK_TRACE_SCHEMA
    phases = []
    for phase in trace.get("phases") if isinstance(trace.get("phases"), list) else []:
        if not isinstance(phase, dict):
            continue
        phase_name = str(phase.get("phase") or "").strip()
        current_step = str(phase.get("current_step") or "").strip()
        if not phase_name or not current_step.startswith("elevator:"):
            continue
        phases.append(
            {
                "phase": phase_name,
                "current_step": current_step,
                "message": str(phase.get("message") or "").strip(),
                "percent": _elevator_trace_float(phase.get("percent")),
                "event": str(phase.get("event") or "").strip(),
                "status": "not_proven",
            }
        )
    status = (
        str(trace.get("status") or "elevator_action_feedback_trace_not_proven")
        if supported and phases
        else "blocked_missing_elevator_action_feedback_trace"
    )
    not_proven = []
    for item in list(trace.get("not_proven") if isinstance(trace.get("not_proven"), list) else []) + [
        "real_elevator",
        "real_nav2_or_fixed_route",
        "real_phone_device_or_browser",
        "real_hil_pass",
        "delivery_success",
    ]:
        text = str(item or "").strip()
        if text and text not in not_proven:
            not_proven.append(text)
    return {
        "schema": ELEVATOR_ACTION_FEEDBACK_TRACE_SUMMARY_SCHEMA,
        "source_schema": trace.get("schema", ""),
        "status": status,
        "source": "software_proof",
        "source_boundary": str(trace.get("source_boundary") or "").strip(),
        "safe_evidence_ref": str(trace.get("safe_evidence_ref") or "").strip(),
        "same_evidence_ref_required": bool(trace.get("same_evidence_ref_required", True)),
        "current_step": str(trace.get("current_step") or "").strip(),
        "message": str(trace.get("message") or "").strip(),
        "percent": _elevator_trace_float(trace.get("percent")),
        "event": str(trace.get("event") or "").strip(),
        "phases": phases,
        "phase_count": len(phases),
        "source_path": source_text,
        "phone_safe_summary": {
            "safe_copy": (
                "Elevator action feedback trace is metadata-only; "
                "delivery_success=false; primary_actions_enabled=false."
            ),
            "safe_phone_copy": (
                "电梯 action feedback trace 仅用于复盘展示；"
                "delivery_success=false; primary_actions_enabled=false。"
            ),
        },
        "not_proven": not_proven,
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def extract_elevator_assist(latest_status, last_task):
    # 最新 status/last_task 优先；task_record 只作为回放补充，避免旧文件覆盖当前电梯协助态。
    latest_status = latest_status if isinstance(latest_status, dict) else {}
    last_task = last_task if isinstance(last_task, dict) else {}
    for candidate, source in (
        (latest_status.get("elevator_assist"), "latest_status.elevator_assist"),
        (last_task.get("elevator_assist"), "last_task.elevator_assist"),
    ):
        if isinstance(candidate, dict):
            return normalize_elevator_assist(candidate), source

    task_record_path = latest_status.get("task_record_path") or last_task.get("task_record_path") or ""
    candidate, source = _elevator_assist_from_task_record(_read_task_record(task_record_path))
    if isinstance(candidate, dict):
        return normalize_elevator_assist(candidate), source
    return normalize_elevator_assist({}), ""


def classify_elevator_assist(elevator_assist, source=""):
    # 分类结果只给操作员提示下一步；所有机器人动作授权仍由上层状态机控制。
    elevator_assist = normalize_elevator_assist(elevator_assist)
    source_text = str(source or "")
    if not elevator_assist.get("enabled"):
        return {
            "state": "disabled",
            "reason": "elevator assisted delivery is not active",
            "next_step": "Continue the normal trash delivery flow.",
            "source": source_text,
        }

    phase = str(elevator_assist.get("phase") or elevator_assist.get("state") or "").strip()
    reason = str(elevator_assist.get("reason") or "").strip()
    if elevator_assist.get("requires_human_help") or phase in ELEVATOR_ASSIST_HELP_REASONS:
        return {
            "state": "needs_human_help",
            "reason": reason or elevator_assist.get("phone_copy") or "elevator assist requires human help",
            "next_step": "Ask an operator to confirm the elevator door, target floor, or safe takeover path.",
            "source": source_text,
        }
    if phase == "waiting_elevator_open":
        return {
            "state": "waiting_elevator_open",
            "reason": "waiting for the elevator door to open",
            "next_step": "Wait for door_open evidence or ask for help if the door does not open.",
            "source": source_text,
        }
    if phase == "requesting_floor_help":
        return {
            "state": "requesting_floor_help",
            "reason": "robot is asking a nearby person to press the target floor",
            "next_step": elevator_assist.get("speaker_prompt", ""),
            "source": source_text,
        }
    if phase == "waiting_target_floor":
        return {
            "state": "waiting_target_floor",
            "reason": "waiting for target floor arrival evidence",
            "next_step": "Keep the path clear and wait for target_floor_confirmed plus door_open evidence.",
            "source": source_text,
        }
    if phase == "exiting_elevator":
        return {
            "state": "exiting_elevator",
            "reason": "target floor evidence is ready and the robot is preparing to exit",
            "next_step": "Monitor safe_to_exit evidence while the robot leaves the elevator.",
            "source": source_text,
        }
    if phase == "resume_delivery":
        return {
            "state": "resume_delivery",
            "reason": "elevator segment is complete",
            "next_step": "Continue delivery to the trash station.",
            "source": source_text,
        }
    return {
        "state": "active",
        "reason": reason or elevator_assist.get("phone_copy") or "elevator assist is active",
        "next_step": elevator_assist.get("speaker_prompt", ""),
        "source": source_text,
    }


def _route_proof_missing_fields(route_proof_summary):
    # 所有字段都存在才允许进入具体 route proof 分类，避免部分材料被误判 ready。
    return [field for field in ROUTE_PROOF_REQUIRED_FIELDS if field not in route_proof_summary]


def classify_route_proof(route_proof_summary, source=""):
    # route proof 分类只读解释视觉/路线 proof 状态，不直接触发 Nav2 或任务完成。
    route_proof_summary = route_proof_summary if isinstance(route_proof_summary, dict) else {}
    source_text = str(source or "")
    if not route_proof_summary:
        return {
            "state": "unknown",
            "reason": "route_proof_summary is missing",
            "blocking_reason": "",
            "missing_fields": list(ROUTE_PROOF_REQUIRED_FIELDS),
            "source": source_text,
        }

    missing_fields = _route_proof_missing_fields(route_proof_summary)
    if missing_fields:
        return {
            "state": "unknown",
            "reason": f"route_proof_summary missing required fields: {', '.join(missing_fields)}",
            "blocking_reason": "",
            "missing_fields": missing_fields,
            "source": source_text,
        }

    gate_status = str(route_proof_summary.get("gate_status", "")).strip().lower()
    blocking_reason = str(route_proof_summary.get("last_block_reason", "")).strip()
    coverage_rate = _safe_float(route_proof_summary.get("coverage_rate"))
    missing_checkpoints = route_proof_summary.get("missing_checkpoints")
    if not isinstance(missing_checkpoints, list):
        missing_checkpoints = []
    missing_checkpoint_values = [str(item).strip() for item in missing_checkpoints if str(item).strip()]

    if gate_status in ROUTE_PROOF_WAITING_GATE_STATUSES:
        reason = "waiting for visual gate to pass"
        if blocking_reason:
            reason = f"waiting for visual gate: {blocking_reason}"
        return {
            "state": "waiting_visual_gate",
            "reason": reason,
            "blocking_reason": "",
            "missing_fields": [],
            "source": source_text,
        }

    if blocking_reason:
        return {
            "state": "blocked",
            "reason": f"blocked: {blocking_reason}",
            "blocking_reason": blocking_reason,
            "missing_fields": [],
            "source": source_text,
        }

    if coverage_rate is None:
        return {
            "state": "unknown",
            "reason": "route_proof_summary.coverage_rate is not a number",
            "blocking_reason": "",
            "missing_fields": [],
            "source": source_text,
        }

    if coverage_rate < 1.0 or missing_checkpoint_values:
        reason = f"coverage_rate={coverage_rate:.4f} indicates incomplete route proof"
        if missing_checkpoint_values:
            reason = f"missing checkpoints: {', '.join(missing_checkpoint_values)}"
        return {
            "state": "insufficient_coverage",
            "reason": reason,
            "blocking_reason": "",
            "missing_fields": [],
            "source": source_text,
        }

    if gate_status in ROUTE_PROOF_READY_GATE_STATUSES:
        return {
            "state": "ready",
            "reason": "route proof is ready",
            "blocking_reason": "",
            "missing_fields": [],
            "source": source_text,
        }

    return {
        "state": "unknown",
        "reason": f"unsupported gate_status: {gate_status or 'empty'}",
        "blocking_reason": "",
        "missing_fields": [],
        "source": source_text,
    }


__all__ = [
    "EVIDENCE_SOURCE_SOFTWARE",
    "EVIDENCE_SOURCE_HIL",
    "VALID_EVIDENCE_SOURCES",
    "ROUTE_PROOF_REQUIRED_FIELDS",
    "ROUTE_PROOF_WAITING_GATE_STATUSES",
    "ROUTE_PROOF_READY_GATE_STATUSES",
    "ELEVATOR_ASSIST_HELP_REASONS",
    "ROUTE_TASK_COMPLETION_SIGNAL_SCHEMA",
    "ROUTE_TASK_COMPLETION_SIGNAL_SUMMARY_SCHEMA",
    "ROUTE_TASK_COMPLETION_SIGNAL_GATE",
    "ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SCHEMA",
    "ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY_SCHEMA",
    "ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_GATE",
    "ELEVATOR_ACTION_FEEDBACK_TRACE_SCHEMA",
    "ELEVATOR_ACTION_FEEDBACK_TRACE_SUMMARY_SCHEMA",
    "_route_task_completion_signal_not_proven",
    "_elevator_route_evidence_reconciliation_not_proven",
    "_default_route_task_completion_signal_summary",
    "_default_elevator_route_evidence_reconciliation_summary",
    "_route_task_completion_signal_source_contract",
    "_route_task_completion_signal_has_unsafe_control_claims",
    "_elevator_route_evidence_reconciliation_source_contract",
    "_elevator_route_reconciliation_requires_same_evidence_ref",
    "_elevator_route_reconciliation_has_disabled_actions",
    "summarize_route_task_completion_signal",
    "summarize_elevator_route_evidence_reconciliation",
    "_read_task_record",
    "_route_proof_from_task_record",
    "_extract_route_proof_summary",
    "normalize_evidence_source",
    "_extract_traceability_field",
    "_extract_route_progress",
    "coalesce_traceability_fields",
    "_elevator_assist_from_task_record",
    "_elevator_action_feedback_trace_from_payloads",
    "_elevator_trace_float",
    "summarize_elevator_action_feedback_trace",
    "extract_elevator_assist",
    "classify_elevator_assist",
    "_route_proof_missing_fields",
    "classify_route_proof",
]
