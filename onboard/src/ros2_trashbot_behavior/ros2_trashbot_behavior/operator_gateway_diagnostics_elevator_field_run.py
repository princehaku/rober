"""Elevator field-run diagnostics summary helpers.

本模块承接 operator_gateway_diagnostics 的 elevator field-run material
validation、review 和 execution pack 摘要逻辑。这里的摘要只处理
software diagnostics metadata，不代表真实电梯运行、底盘运动、UART 反馈或 HIL 通过。
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
    _safe_pc_route_debug_value,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
)

ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SCHEMA = (
    "trashbot.elevator_field_run_material_validation.v1"
)

ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY_SCHEMA = (
    "trashbot.elevator_field_run_material_validation_summary.v1"
)

ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_GATE = (
    "software_proof_docker_elevator_field_material_validation_gate"
)

ELEVATOR_FIELD_RUN_REVIEW_SCHEMA = "trashbot.elevator_field_run_review.v1"

ELEVATOR_FIELD_RUN_REVIEW_SUMMARY_SCHEMA = "trashbot.elevator_field_run_review_summary.v1"

ELEVATOR_FIELD_RUN_REVIEW_GATE = "software_proof_docker_elevator_field_review_decision_gate"

ELEVATOR_FIELD_RUN_EXECUTION_PACK_SCHEMA = "trashbot.elevator_field_run_execution_pack.v1"

ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY_SCHEMA = (
    "trashbot.elevator_field_run_execution_pack_summary.v1"
)

ELEVATOR_FIELD_RUN_EXECUTION_PACK_GATE = (
    "software_proof_docker_elevator_field_rehearsal_execution_pack_gate"
)


def _elevator_field_run_material_validation_not_proven(validation=None, summary_fragment=None):
    # 电梯材料校验只读消费现场材料，不得把电梯、Nav2、HIL 或送达闭环标成已完成。
    validation = validation if isinstance(validation, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(validation.get("not_proven"), list):
        source_values.extend(validation.get("not_proven"))
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
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
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


def _elevator_field_run_review_not_proven(review=None, summary_fragment=None):
    # 电梯复核决策只是人工复盘元数据；真实电梯、控制动作和送达结果必须继续外部证明。
    review = review if isinstance(review, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(review.get("not_proven"), list):
        source_values.extend(review.get("not_proven"))
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
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
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


def _elevator_field_run_execution_pack_not_proven(pack=None, summary_fragment=None):
    # 电梯执行包只读承接 Autonomy artifact；真实电梯、控制链、ACK、Nav2、HIL 和交付结论必须继续未证明。
    pack = pack if isinstance(pack, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(pack.get("not_proven"), list):
        source_values.extend(pack.get("not_proven"))
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


def _default_elevator_field_run_material_validation_summary(path, status="not_configured", read_error=""):
    # 电梯现场材料校验默认阻塞；diagnostics 只能展示摘要，不能解锁 Start/Confirm/Cancel。
    return {
        "schema": ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_GATE,
        "source_schema": "",
        "source_evidence_boundary": "",
        "validation_verdict": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "elevator field-run material validation is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "materials_status": {
            "status": "blocked",
            "reason": "elevator field-run material validation is not configured",
        },
        "validation_summary": {
            "status": "blocked",
            "reason": "elevator field-run material validation is not configured",
        },
        "material_validation_checks": [],
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "elevator field-run material validation is not configured",
        },
        "mobile_readonly_summary": {
            "safe_copy": "Elevator field-run material validation is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Elevator field-run material validation is metadata-only; delivery_success=false.",
        },
        "not_proven": _elevator_field_run_material_validation_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
    }


def _default_elevator_field_run_review_summary(path, status="not_configured", read_error=""):
    # 复核决策默认 blocked；没有 artifact 时也不能让手机或机器人控制面推断可以开跑。
    return {
        "schema": ELEVATOR_FIELD_RUN_REVIEW_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ELEVATOR_FIELD_RUN_REVIEW_GATE,
        "source_schema": "",
        "source_evidence_boundary": "",
        "review_decision": {
            "status": status,
            "decision": "not_proven",
            "reason": read_error or "elevator field-run review decision is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "blocked_categories": [],
        "operator_next_steps": [],
        "commands_to_rerun": [],
        "capture_checklist": [],
        "review_summary": {
            "status": "blocked",
            "reason": "elevator field-run review decision is not configured",
        },
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "elevator field-run review decision is not configured",
        },
        "phone_safe_summary": {
            "safe_copy": "Elevator field-run review is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Elevator field-run review is metadata-only; delivery_success=false.",
        },
        "not_proven": _elevator_field_run_review_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
    }


def _default_elevator_field_run_execution_pack_summary(path, status="not_configured", read_error=""):
    # 执行包默认就是只读 blocked；即使 artifact 缺失也要显式保留动作链禁用状态。
    return {
        "schema": ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ELEVATOR_FIELD_RUN_EXECUTION_PACK_GATE,
        "source_schema": "",
        "source_evidence_boundary": "",
        "execution_pack_verdict": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "elevator field-run execution pack is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "controlled_rehearsal_manifest": {},
        "required_material_templates": [],
        "first_run_commands": [],
        "rerun_commands": [],
        "operator_handoff": {},
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "elevator field-run execution pack is not configured",
        },
        "phone_safe_summary": {
            "safe_copy": "Elevator field-run execution pack is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Elevator field-run execution pack is metadata-only; delivery_success=false.",
        },
        "not_proven": _elevator_field_run_execution_pack_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _elevator_field_run_material_validation_source_contract(value):
    # 电梯 gate 允许直接 artifact 或 summary wrapper，但 wrapper 必须保留原始电梯 schema/boundary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _elevator_field_run_review_source_contract(value):
    # review gate 允许直接读取决策 artifact 或 summary wrapper；wrapper 仍必须指向原始 review schema。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ELEVATOR_FIELD_RUN_REVIEW_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _elevator_field_run_execution_pack_source_contract(value):
    # execution pack 可直接来自 Autonomy artifact，也可来自 summary env；summary 必须保留原始 source/boundary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _elevator_execution_pack_requires_same_evidence_ref(summary_fragment, pack):
    # 这里故意只接受 JSON boolean true；字符串 "false" 在 Python 中是真值，不能被误当成同证据链约束成立。
    value = (
        summary_fragment.get("same_evidence_ref_required")
        if isinstance(summary_fragment, dict) and "same_evidence_ref_required" in summary_fragment
        else pack.get("same_evidence_ref_required", True)
        if isinstance(pack, dict)
        else True
    )
    return value is True


def summarize_elevator_field_run_material_validation(path):
    """构建 elevator field-run material validation 的 metadata-only diagnostics 摘要。"""
    validation_path = os.path.expanduser(str(path or ""))
    summary = _default_elevator_field_run_material_validation_summary(
        validation_path,
        read_error="elevator field-run material validation is not configured",
    )
    if not validation_path:
        return summary
    if not os.path.exists(validation_path):
        summary.update(
            {
                "validation_verdict": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "elevator field-run material validation missing",
                },
                "materials_status": {"status": "blocked", "reason": "elevator material validation artifact missing"},
                "validation_summary": {"status": "blocked", "reason": "elevator material validation artifact missing"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "elevator field-run material validation artifact missing",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Elevator field-run material validation is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator field-run material validation is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(validation_path, "r", encoding="utf-8") as f:
            validation = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading elevator field-run material validation: {exc}"
        )
        summary.update(
            {
                "validation_verdict": {"status": "read_error", "verdict": "not_proven", "reason": safe_error},
                "materials_status": {"status": "blocked", "reason": "elevator validation JSON read error"},
                "validation_summary": {"status": "blocked", "reason": "elevator validation JSON read error"},
                "robot_diagnostics_summary": {"status": "blocked", "reason": "elevator validation JSON read error"},
                "mobile_readonly_summary": {
                    "safe_copy": "Elevator field-run material validation could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator field-run material validation could not be read; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    if not isinstance(validation, dict):
        summary.update(
            {
                "validation_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "elevator field-run material validation JSON must be an object",
                },
                "materials_status": {"status": "blocked", "reason": "elevator validation JSON shape is invalid"},
                "validation_summary": {"status": "blocked", "reason": "elevator validation JSON shape is invalid"},
                "robot_diagnostics_summary": {"status": "blocked", "reason": "elevator validation JSON shape is invalid"},
                "mobile_readonly_summary": {
                    "safe_copy": "Elevator field-run material validation shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator field-run material validation shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # Autonomy 侧可能交付完整 artifact 或 summary；这里仅白名单读取摘要字段并固定控制面关闭。
    mobile_summary = {}
    for candidate in (
        validation.get("mobile_readonly_summary"),
        validation.get("mobile_safe_summary"),
        validation.get("phone_safe_summary"),
        validation.get("elevator_field_run_material_validation_summary"),
    ):
        if isinstance(candidate, dict):
            mobile_summary = candidate
            break
    robot_summary = (
        validation.get("robot_diagnostics_summary")
        if isinstance(validation.get("robot_diagnostics_summary"), dict)
        else validation.get("diagnostics_summary")
        if isinstance(validation.get("diagnostics_summary"), dict)
        else {}
    )
    source_schema, source_boundary = _elevator_field_run_material_validation_source_contract(validation)
    source_verdict = validation.get("validation_verdict")
    if not isinstance(source_verdict, dict):
        source_verdict = validation.get("material_validation_verdict")
    if isinstance(source_verdict, dict):
        verdict_status = _redact_route_task_rehearsal_text(
            source_verdict.get("status")
            or source_verdict.get("verdict")
            or source_verdict.get("decision")
            or validation.get("status")
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
            validation.get("status") or robot_summary.get("status") or "blocked"
        )
        verdict_value = _redact_route_task_rehearsal_text(
            validation.get("verdict") or robot_summary.get("verdict") or verdict_status or "not_proven"
        )
        verdict_reason = _redact_route_task_rehearsal_text(
            validation.get("reason") or robot_summary.get("reason") or ""
        )
    materials_status = (
        validation.get("materials_status")
        if isinstance(validation.get("materials_status"), dict)
        else robot_summary.get("materials_status") if isinstance(robot_summary.get("materials_status"), dict) else {}
    )
    validation_fragment = (
        validation.get("validation_summary")
        if isinstance(validation.get("validation_summary"), dict)
        else validation.get("summary") if isinstance(validation.get("summary"), dict) else {}
    )
    checks = (
        validation.get("material_validation_checks")
        if isinstance(validation.get("material_validation_checks"), list)
        else validation.get("validation_checks")
    )
    safe_copy = _redact_route_task_rehearsal_text(
        mobile_summary.get("safe_copy")
        or mobile_summary.get("safe_phone_copy")
        or validation.get("safe_copy")
        or validation.get("safe_phone_copy")
        or "Elevator field-run material validation is metadata-only; delivery_success=false."
    )
    safe_mobile_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(mobile_summary.get(key) or "").strip():
            safe_mobile_summary[key] = _redact_route_task_rehearsal_text(mobile_summary.get(key))
    safe_mobile_summary["safe_copy"] = safe_copy
    safe_mobile_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "validation_verdict": {
                "status": verdict_status or "blocked",
                "verdict": verdict_value or "not_proven",
                "reason": verdict_reason or "elevator field-run material validation consumed without explicit reason",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                mobile_summary.get("safe_evidence_ref")
                or mobile_summary.get("evidence_ref")
                or validation.get("safe_evidence_ref")
                or validation.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                mobile_summary.get(
                    "same_evidence_ref_required",
                    validation.get("same_evidence_ref_required", True),
                )
            ),
            "materials_status": _safe_pc_route_debug_dict(materials_status)
            or {"status": verdict_status or "blocked", "reason": "elevator validation consumed without explicit materials status"},
            "validation_summary": _safe_pc_route_debug_dict(validation_fragment)
            or {"status": verdict_status or "blocked", "reason": "elevator validation consumed without explicit summary"},
            "material_validation_checks": _safe_pc_route_debug_value(checks if isinstance(checks, list) else []),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                mobile_summary.get("operator_next_steps")
                if isinstance(mobile_summary.get("operator_next_steps"), list)
                else validation.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": verdict_status or "blocked",
                "reason": "elevator validation consumed without explicit robot diagnostics summary",
            },
            "mobile_readonly_summary": safe_mobile_summary,
            "not_proven": _elevator_field_run_material_validation_not_proven(validation, mobile_summary),
            "read_error": "",
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema != ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SCHEMA or source_boundary != ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_GATE:
        summary.update(
            {
                "validation_verdict": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "elevator field-run material validation schema or evidence boundary is unsupported",
                },
                "materials_status": {"status": "blocked", "reason": "unsupported schema or evidence boundary"},
                "validation_summary": {"status": "blocked", "reason": "unsupported schema or evidence boundary"},
                "material_validation_checks": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Elevator field-run material validation is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Elevator field-run material validation is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        not summary["same_evidence_ref_required"]
        or _route_task_field_run_console_has_unsafe_fields(validation)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "validation_verdict": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "elevator field-run material validation contains unsafe fields or weakens same evidence_ref constraints",
                },
                "materials_status": {"status": "blocked", "reason": "unsafe elevator material validation summary fields"},
                "validation_summary": {"status": "blocked", "reason": "unsafe elevator material validation summary fields"},
                "material_validation_checks": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe elevator material validation summary fields",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Elevator field-run material validation was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                    "safe_phone_copy": "Elevator field-run material validation was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_elevator_field_run_review(path):
    """构建 elevator field-run review decision 的 metadata-only diagnostics 摘要。"""
    review_path = os.path.expanduser(str(path or ""))
    summary = _default_elevator_field_run_review_summary(
        review_path,
        read_error="elevator field-run review decision is not configured",
    )
    if not review_path:
        return summary
    if not os.path.exists(review_path):
        summary.update(
            {
                "review_decision": {
                    "status": "missing",
                    "decision": "not_proven",
                    "reason": "elevator field-run review decision missing",
                },
                "review_summary": {"status": "blocked", "reason": "review decision artifact missing"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "elevator field-run review decision artifact missing",
                },
                "phone_safe_summary": {
                    "safe_copy": "Elevator field-run review decision is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator field-run review decision is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(review_path, "r", encoding="utf-8") as f:
            review = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading elevator field-run review decision: {exc}"
        )
        summary.update(
            {
                "review_decision": {"status": "read_error", "decision": "not_proven", "reason": safe_error},
                "review_summary": {"status": "blocked", "reason": "review decision JSON read error"},
                "robot_diagnostics_summary": {"status": "blocked", "reason": "review decision JSON read error"},
                "phone_safe_summary": {
                    "safe_copy": "Elevator field-run review decision could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator field-run review decision could not be read; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    if not isinstance(review, dict):
        summary.update(
            {
                "review_decision": {
                    "status": "read_error",
                    "decision": "not_proven",
                    "reason": "elevator field-run review decision JSON must be an object",
                },
                "review_summary": {"status": "blocked", "reason": "review decision JSON shape is invalid"},
                "robot_diagnostics_summary": {"status": "blocked", "reason": "review decision JSON shape is invalid"},
                "phone_safe_summary": {
                    "safe_copy": "Elevator field-run review decision shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator field-run review decision shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # Autonomy 可能输出完整 review artifact 或 summary wrapper；diagnostics 只消费支持人员需要的白名单字段。
    phone_summary = {}
    for candidate in (
        review.get("phone_safe_summary"),
        review.get("mobile_readonly_summary"),
        review.get("mobile_safe_summary"),
        review.get("elevator_field_run_review_summary"),
    ):
        if isinstance(candidate, dict):
            phone_summary = candidate
            break
    robot_summary = (
        review.get("robot_diagnostics_summary")
        if isinstance(review.get("robot_diagnostics_summary"), dict)
        else review.get("diagnostics_summary")
        if isinstance(review.get("diagnostics_summary"), dict)
        else {}
    )
    source_schema, source_boundary = _elevator_field_run_review_source_contract(review)
    source_decision = review.get("review_decision")
    if isinstance(source_decision, dict):
        decision_status = _redact_route_task_rehearsal_text(
            source_decision.get("status")
            or source_decision.get("decision")
            or source_decision.get("verdict")
            or review.get("status")
            or "blocked"
        )
        decision_value = _redact_route_task_rehearsal_text(
            source_decision.get("decision")
            or source_decision.get("verdict")
            or decision_status
            or "not_proven"
        )
        decision_reason = _redact_route_task_rehearsal_text(
            source_decision.get("reason") or source_decision.get("summary") or ""
        )
    else:
        decision_value = _redact_route_task_rehearsal_text(
            source_decision
            or review.get("decision")
            or phone_summary.get("review_decision")
            or phone_summary.get("decision")
            or "not_proven"
        )
        decision_status = _redact_route_task_rehearsal_text(review.get("status") or decision_value or "blocked")
        decision_reason = _redact_route_task_rehearsal_text(review.get("reason") or robot_summary.get("reason") or "")
    review_fragment = (
        review.get("review_summary")
        if isinstance(review.get("review_summary"), dict)
        else review.get("summary") if isinstance(review.get("summary"), dict) else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or review.get("safe_copy")
        or review.get("safe_phone_copy")
        or "Elevator field-run review is metadata-only; delivery_success=false."
    )
    safe_phone_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(phone_summary.get(key) or "").strip():
            safe_phone_summary[key] = _redact_route_task_rehearsal_text(phone_summary.get(key))
    safe_phone_summary["safe_copy"] = safe_copy
    safe_phone_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_decision": {
                "status": decision_status or "blocked",
                "decision": decision_value or "not_proven",
                "reason": decision_reason or "elevator field-run review consumed without explicit reason",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                phone_summary.get("safe_evidence_ref")
                or phone_summary.get("evidence_ref")
                or review.get("safe_evidence_ref")
                or review.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                phone_summary.get(
                    "same_evidence_ref_required",
                    review.get("same_evidence_ref_required", True),
                )
            ),
            "blocked_categories": _safe_route_task_rehearsal_list(
                phone_summary.get("blocked_categories")
                if isinstance(phone_summary.get("blocked_categories"), list)
                else review.get("blocked_categories")
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                phone_summary.get("operator_next_steps")
                if isinstance(phone_summary.get("operator_next_steps"), list)
                else review.get("operator_next_steps")
            ),
            "commands_to_rerun": _safe_route_task_rehearsal_list(
                phone_summary.get("commands_to_rerun")
                if isinstance(phone_summary.get("commands_to_rerun"), list)
                else review.get("commands_to_rerun")
            ),
            "capture_checklist": _safe_pc_route_debug_value(
                phone_summary.get("capture_checklist")
                if isinstance(phone_summary.get("capture_checklist"), list)
                else review.get("capture_checklist")
                if isinstance(review.get("capture_checklist"), list)
                else []
            ),
            "review_summary": _safe_pc_route_debug_dict(review_fragment)
            or {"status": decision_status or "blocked", "reason": "review decision consumed without explicit summary"},
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": decision_status or "blocked",
                "reason": "review decision consumed without explicit robot diagnostics summary",
            },
            "phone_safe_summary": safe_phone_summary,
            "not_proven": _elevator_field_run_review_not_proven(review, phone_summary),
            "read_error": "",
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema != ELEVATOR_FIELD_RUN_REVIEW_SCHEMA or source_boundary != ELEVATOR_FIELD_RUN_REVIEW_GATE:
        summary.update(
            {
                "review_decision": {
                    "status": "unsupported_schema",
                    "decision": "not_proven",
                    "reason": "elevator field-run review schema or evidence boundary is unsupported",
                },
                "blocked_categories": ["unsupported_schema_or_boundary"],
                "operator_next_steps": [],
                "commands_to_rerun": [],
                "capture_checklist": [],
                "review_summary": {"status": "blocked", "reason": "unsupported schema or evidence boundary"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "phone_safe_summary": {
                    "safe_copy": "Elevator field-run review is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Elevator field-run review is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        not summary["same_evidence_ref_required"]
        or _route_task_field_run_console_has_unsafe_fields(review)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "review_decision": {
                    "status": "unsafe_fields",
                    "decision": "not_proven",
                    "reason": "elevator field-run review contains unsafe fields or weakens same evidence_ref constraints",
                },
                "blocked_categories": ["unsafe_fields"],
                "operator_next_steps": [],
                "commands_to_rerun": [],
                "capture_checklist": [],
                "review_summary": {"status": "blocked", "reason": "unsafe review decision summary fields"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe review decision summary fields",
                },
                "phone_safe_summary": {
                    "safe_copy": "Elevator field-run review was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                    "safe_phone_copy": "Elevator field-run review was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_elevator_field_run_execution_pack(path):
    """构建 elevator field-run execution pack 的 metadata-only diagnostics 摘要。"""
    pack_path = os.path.expanduser(str(path or ""))
    summary = _default_elevator_field_run_execution_pack_summary(
        pack_path,
        read_error="elevator field-run execution pack is not configured",
    )
    if not pack_path:
        return summary
    if not os.path.exists(pack_path):
        summary.update(
            {
                "execution_pack_verdict": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "elevator field-run execution pack missing",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "elevator field-run execution pack missing",
                },
                "phone_safe_summary": {
                    "safe_copy": "Elevator field-run execution pack is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator field-run execution pack is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(pack_path, "r", encoding="utf-8") as f:
            pack = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading elevator field-run execution pack: {exc}"
        )
        summary.update(
            {
                "execution_pack_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": safe_error,
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution pack JSON read error",
                },
                "phone_safe_summary": {
                    "safe_copy": "Elevator field-run execution pack could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator field-run execution pack could not be read; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    if not isinstance(pack, dict):
        summary.update(
            {
                "execution_pack_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "elevator field-run execution pack JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution pack JSON shape is invalid",
                },
                "phone_safe_summary": {
                    "safe_copy": "Elevator field-run execution pack shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Elevator field-run execution pack shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # 这里只读取可展示给 diagnostics/mobile 的白名单字段，避免把执行包误接到动作面。
    summary_fragment = {}
    for candidate in (
        pack.get("phone_safe_summary"),
        pack.get("mobile_readonly_summary"),
        pack.get("mobile_safe_summary"),
        pack.get("elevator_field_run_execution_pack_summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    robot_summary = (
        pack.get("robot_diagnostics_summary")
        if isinstance(pack.get("robot_diagnostics_summary"), dict)
        else pack.get("diagnostics_summary")
        if isinstance(pack.get("diagnostics_summary"), dict)
        else {}
    )
    source_schema, source_boundary = _elevator_field_run_execution_pack_source_contract(pack)
    source_verdict = pack.get("execution_pack_verdict")
    if isinstance(source_verdict, dict):
        verdict_status = _redact_route_task_rehearsal_text(
            source_verdict.get("status")
            or source_verdict.get("verdict")
            or pack.get("status")
            or "blocked"
        )
        verdict_value = _redact_route_task_rehearsal_text(
            source_verdict.get("verdict") or source_verdict.get("decision") or verdict_status or "not_proven"
        )
        verdict_reason = _redact_route_task_rehearsal_text(
            source_verdict.get("reason") or source_verdict.get("summary") or ""
        )
    else:
        verdict_value = _redact_route_task_rehearsal_text(
            source_verdict
            or pack.get("verdict")
            or summary_fragment.get("execution_pack_verdict")
            or "not_proven"
        )
        verdict_status = _redact_route_task_rehearsal_text(pack.get("status") or verdict_value or "blocked")
        verdict_reason = _redact_route_task_rehearsal_text(pack.get("reason") or robot_summary.get("reason") or "")
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or pack.get("safe_copy")
        or pack.get("safe_phone_copy")
        or "Elevator field-run execution pack is metadata-only; delivery_success=false."
    )
    safe_phone_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            safe_phone_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    safe_phone_summary["safe_copy"] = safe_copy
    safe_phone_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "execution_pack_verdict": {
                "status": verdict_status or "blocked",
                "verdict": verdict_value or "not_proven",
                "reason": verdict_reason or "elevator field-run execution pack consumed without explicit reason",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or pack.get("safe_evidence_ref")
                or pack.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": _elevator_execution_pack_requires_same_evidence_ref(
                summary_fragment,
                pack,
            ),
            "controlled_rehearsal_manifest": _safe_pc_route_debug_dict(
                summary_fragment.get("controlled_rehearsal_manifest")
                if isinstance(summary_fragment.get("controlled_rehearsal_manifest"), dict)
                else pack.get("controlled_rehearsal_manifest")
                if isinstance(pack.get("controlled_rehearsal_manifest"), dict)
                else {}
            ),
            "required_material_templates": _safe_pc_route_debug_value(
                summary_fragment.get("required_material_templates")
                if isinstance(summary_fragment.get("required_material_templates"), list)
                else pack.get("required_material_templates")
                if isinstance(pack.get("required_material_templates"), list)
                else []
            ),
            "first_run_commands": _safe_route_task_rehearsal_list(
                summary_fragment.get("first_run_commands")
                if isinstance(summary_fragment.get("first_run_commands"), list)
                else pack.get("first_run_commands")
            ),
            "rerun_commands": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_commands")
                if isinstance(summary_fragment.get("rerun_commands"), list)
                else pack.get("rerun_commands")
            ),
            "operator_handoff": _safe_pc_route_debug_dict(
                summary_fragment.get("operator_handoff")
                if isinstance(summary_fragment.get("operator_handoff"), dict)
                else pack.get("operator_handoff")
                if isinstance(pack.get("operator_handoff"), dict)
                else {}
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": verdict_status or "blocked",
                "reason": "execution pack consumed without explicit robot diagnostics summary",
            },
            "phone_safe_summary": safe_phone_summary,
            "not_proven": _elevator_field_run_execution_pack_not_proven(pack, summary_fragment),
            "read_error": "",
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema != ELEVATOR_FIELD_RUN_EXECUTION_PACK_SCHEMA or source_boundary != ELEVATOR_FIELD_RUN_EXECUTION_PACK_GATE:
        summary.update(
            {
                "execution_pack_verdict": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "elevator field-run execution pack schema or evidence boundary is unsupported",
                },
                "controlled_rehearsal_manifest": {},
                "required_material_templates": [],
                "first_run_commands": [],
                "rerun_commands": [],
                "operator_handoff": {},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "phone_safe_summary": {
                    "safe_copy": "Elevator field-run execution pack is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Elevator field-run execution pack is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        not summary["same_evidence_ref_required"]
        or _route_task_field_run_console_has_unsafe_fields(pack)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "execution_pack_verdict": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "elevator field-run execution pack contains unsafe fields or control claims",
                },
                "controlled_rehearsal_manifest": {},
                "required_material_templates": [],
                "first_run_commands": [],
                "rerun_commands": [],
                "operator_handoff": {},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe execution pack summary fields",
                },
                "phone_safe_summary": {
                    "safe_copy": "Elevator field-run execution pack was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Elevator field-run execution pack was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary
