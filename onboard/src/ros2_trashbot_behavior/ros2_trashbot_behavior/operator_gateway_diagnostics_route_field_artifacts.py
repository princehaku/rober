"""Route field-run artifact diagnostics summary helpers.

本模块承接 operator_gateway_diagnostics 的 route field artifact 摘要逻辑。
这些 artifact 只提供 software_proof/metadata-only 诊断材料，不能升级为
真实路线通过、Nav2/HIL proof、WAVE ROVER 运动证明或 delivery success。
"""

import json
import os

from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_run import (
    _redact_route_task_rehearsal_text,
    _route_task_field_run_intake_has_unsafe_control_claims,
    _route_task_field_run_readiness_copy_is_unsafe,
    _route_task_field_run_readiness_has_unsafe_fields,
    _safe_pc_route_debug_dict,
    _safe_pc_route_debug_value,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
)

ROUTE_TASK_FIELD_RUN_RECONCILIATION_SCHEMA = "trashbot.route_task_field_run_reconciliation.v1"

ROUTE_TASK_FIELD_RUN_RECONCILIATION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_reconciliation_summary.v1"
)

ROUTE_TASK_FIELD_RUN_RECONCILIATION_GATE = (
    "software_proof_docker_route_task_field_run_reconciliation_gate"
)

ROUTE_TASK_FIELD_RUN_CONSOLE_SCHEMA = "trashbot.route_task_field_run_console.v1"

ROUTE_TASK_FIELD_RUN_CONSOLE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_console_summary.v1"
)

ROUTE_TASK_FIELD_RUN_CONSOLE_GATE = (
    "software_proof_docker_route_task_field_run_console_gate"
)

ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SCHEMA = "trashbot.route_task_field_run_evidence_kit.v1"

ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_evidence_kit_summary.v1"
)

ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_GATE = (
    "software_proof_docker_route_task_field_run_evidence_kit_gate"
)

ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SCHEMA = "trashbot.route_task_field_run_material_bundle.v1"

ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_material_bundle_summary.v1"
)

ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_GATE = (
    "software_proof_docker_route_task_field_run_material_bundle_gate"
)

ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SCHEMA = (
    "trashbot.route_task_field_run_material_validation.v1"
)

ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_material_validation_summary.v1"
)

ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_GATE = (
    "software_proof_docker_route_task_field_run_material_validation_gate"
)

def _route_task_field_run_reconciliation_not_proven(reconciliation=None, phone_summary=None):
    # reconciliation 只复核现场材料是否一致；真实控制、ACK、Nav2、HIL 和交付结论必须继续外部证明。
    reconciliation = reconciliation if isinstance(reconciliation, dict) else {}
    phone_summary = phone_summary if isinstance(phone_summary, dict) else {}
    values = []
    source_values = []
    if isinstance(reconciliation.get("not_proven"), list):
        source_values.extend(reconciliation.get("not_proven"))
    if isinstance(phone_summary.get("not_proven"), list):
        source_values.extend(phone_summary.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "production_readiness",
        "dropoff_or_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values

def _route_task_field_run_console_not_proven(console=None, mobile_summary=None):
    # field-run console 是现场执行前的只读控制台摘要；真实控制、ACK、Nav2/HIL 和投放结果都必须外部证明。
    console = console if isinstance(console, dict) else {}
    mobile_summary = mobile_summary if isinstance(mobile_summary, dict) else {}
    values = []
    source_values = []
    if isinstance(console.get("not_proven"), list):
        source_values.extend(console.get("not_proven"))
    if isinstance(mobile_summary.get("not_proven"), list):
        source_values.extend(mobile_summary.get("not_proven"))
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

def _route_task_field_run_evidence_kit_not_proven(kit=None, summary_fragment=None):
    # evidence kit 只把现场运行证据包材料投到 diagnostics；真实控制、ACK、Nav2/HIL 和交付结论必须外部证明。
    kit = kit if isinstance(kit, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(kit.get("not_proven"), list):
        source_values.extend(kit.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
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

def _route_task_field_run_material_bundle_not_proven(bundle=None, summary_fragment=None):
    # material bundle 是现场材料包摘要，不是控制入口；真实动作、ACK、Nav2/HIL 和交付结论必须继续外部证明。
    bundle = bundle if isinstance(bundle, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(bundle.get("not_proven"), list):
        source_values.extend(bundle.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
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

def _route_task_field_run_material_validation_not_proven(validation=None, summary_fragment=None):
    # material validation 只确认材料包是否可交给现场复核；真实控制、ACK、Nav2/HIL 和交付结论必须外部证明。
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

def _default_route_task_field_run_reconciliation_summary(path, status="not_configured", read_error=""):
    # reconciliation 摘要只暴露白名单字段；默认不配置时也必须明确保持 metadata-only 和不可操作。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_RECONCILIATION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_RECONCILIATION_GATE,
        "source_schema": "",
        "source_evidence_boundary": "",
        "reconciliation_verdict": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field-run reconciliation artifact is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "materials_status": {
            "status": "blocked",
            "reason": "route-task field-run reconciliation artifact is not configured",
        },
        "operator_next_steps": [],
        "phone_safe_summary": {
            "safe_copy": "Route-task field-run reconciliation is metadata-only; not delivery success.",
            "safe_phone_copy": "Route-task field-run reconciliation is metadata-only; not delivery success.",
        },
        "not_proven": _route_task_field_run_reconciliation_not_proven(),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }

def _default_route_task_field_run_console_summary(path, status="not_configured", read_error=""):
    # console summary 只把 PC/operator 现场步骤投到 diagnostics；默认 blocked 防止缺 artifact 时误启控制链路。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_CONSOLE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_CONSOLE_GATE,
        "source_schema": "",
        "source_evidence_boundary": "",
        "console_verdict": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field-run console summary is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "field_run_plan": {
            "status": "blocked",
            "steps": [],
        },
        "capture_checklist": {
            "status": "blocked",
            "items": [],
        },
        "dropoff_completion": {"status": "not_proven"},
        "cancel_completion": {"status": "not_proven"},
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field-run console summary is not configured",
        },
        "mobile_readonly_summary": {
            "safe_copy": "Route-task field-run console is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Route-task field-run console is metadata-only; delivery_success=false.",
        },
        "not_proven": _route_task_field_run_console_not_proven(),
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

def _default_route_task_field_run_evidence_kit_summary(path, status="not_configured", read_error=""):
    # evidence kit 默认不配置时也必须 fail-closed；diagnostics 不因为缺材料打开任何机器人动作。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_GATE,
        "source_schema": "",
        "source_evidence_boundary": "",
        "kit_verdict": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field-run evidence kit is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "materials_status": {
            "status": "blocked",
            "reason": "route-task field-run evidence kit is not configured",
        },
        "field_run_plan": {
            "status": "blocked",
            "steps": [],
        },
        "capture_checklist": {
            "status": "blocked",
            "items": [],
        },
        "completion_signal_summary": {},
        "reconciliation_summary": {},
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field-run evidence kit is not configured",
        },
        "mobile_readonly_summary": {
            "safe_copy": "Route-task field-run evidence kit is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Route-task field-run evidence kit is metadata-only; delivery_success=false.",
        },
        "not_proven": _route_task_field_run_evidence_kit_not_proven(),
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

def _default_route_task_field_run_material_bundle_summary(path, status="not_configured", read_error=""):
    # material bundle 默认缺失时保持 fail-closed，避免现场材料包摘要被误用成机器人控制证据。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_GATE,
        "source_schema": "",
        "source_evidence_boundary": "",
        "bundle_verdict": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field-run material bundle is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "materials_status": {
            "status": "blocked",
            "reason": "route-task field-run material bundle is not configured",
        },
        "material_directory_scaffold": {
            "status": "blocked",
            "files": [],
        },
        "bundle_summary": {
            "status": "blocked",
            "reason": "route-task field-run material bundle is not configured",
        },
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field-run material bundle is not configured",
        },
        "mobile_readonly_summary": {
            "safe_copy": "Route-task field-run material bundle is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Route-task field-run material bundle is metadata-only; delivery_success=false.",
        },
        "not_proven": _route_task_field_run_material_bundle_not_proven(),
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

def _default_route_task_field_run_material_validation_summary(path, status="not_configured", read_error=""):
    # validation 默认 fail-closed；它只服务 diagnostics 展示，不能变成现场动作或验收通过信号。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_GATE,
        "source_schema": "",
        "source_evidence_boundary": "",
        "validation_verdict": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "route-task field-run material validation is not configured",
        },
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "materials_status": {
            "status": "blocked",
            "reason": "route-task field-run material validation is not configured",
        },
        "validation_summary": {
            "status": "blocked",
            "reason": "route-task field-run material validation is not configured",
        },
        "material_validation_checks": [],
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "route-task field-run material validation is not configured",
        },
        "mobile_readonly_summary": {
            "safe_copy": "Route-task field-run material validation is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Route-task field-run material validation is metadata-only; delivery_success=false.",
        },
        "not_proven": _route_task_field_run_material_validation_not_proven(),
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

def _route_task_field_run_console_has_unsafe_fields(value):
    # console artifact 可以携带 dropoff/cancel 的只读状态字典，但任何控制触发、ACK 或 raw 设备字段都要 fail-closed。
    unsafe_key_fragments = (
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "checksum",
        "traceback",
        "raw_payload",
        "raw_response",
        "raw_robot",
        "serial",
        "uart",
        "baud",
        "cmd_vel",
        "wave_rover",
        "ack_payload",
        "command_envelope",
        "status_envelope",
    )
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
        "remote_ack_posted",
        "terminal_ack_posted",
    }
    completion_metadata_keys = {"dropoff_completion", "cancel_completion"}
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text in unsafe_true_keys and bool(item):
                return True
            if key_text in completion_metadata_keys and item is True:
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _route_task_field_run_console_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(_route_task_field_run_console_has_unsafe_fields(item) for item in value)
    if isinstance(value, str):
        redacted = _redact_route_task_rehearsal_text(value)
        lowered = redacted.lower()
        return (
            "/api/collect" in lowered
            or "ack posted" in lowered
            or "cursor advanced" in lowered
            or "raw artifact" in lowered
            or "credential" in lowered
            or "serial" in lowered
            or "uart" in lowered
            or "wave rover" in lowered
            or any(marker in redacted for marker in (
                "[REDACTED_AUTH_HEADER]",
                "Bearer [REDACTED]",
                "[REDACTED_URL]",
                "/dev/[REDACTED_SERIAL]",
                "[REDACTED_BAUD]",
                "[REDACTED_TRACEBACK]",
                "[REDACTED_LOCAL_PATH]",
            ))
        )
    return False

def _route_task_field_run_evidence_kit_source_contract(value):
    # 支持直接消费 evidence kit，也支持消费 diagnostics/mobile 传来的 summary wrapper，但 wrapper 仍必须指向 kit schema。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _route_task_field_run_material_bundle_source_contract(value):
    # 支持直接消费 material bundle 或已生成的 summary wrapper；wrapper 必须仍指向同一 source/boundary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _route_task_field_run_material_validation_source_contract(value):
    # 支持直接消费 validation artifact 或 summary wrapper；wrapper 必须保留原始 schema/boundary 以免跨门槛误读。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def summarize_route_task_field_run_reconciliation(path):
    """构建 route-task field-run reconciliation 的 metadata-only diagnostics 摘要。"""
    reconciliation_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_reconciliation_summary(
        reconciliation_path,
        read_error="route-task field-run reconciliation artifact is not configured",
    )
    if not reconciliation_path:
        return summary
    if not os.path.exists(reconciliation_path):
        summary.update(
            {
                "reconciliation_verdict": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "route-task field-run reconciliation artifact missing",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "reconciliation artifact missing",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task field-run reconciliation is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run reconciliation is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(reconciliation_path, "r", encoding="utf-8") as f:
            reconciliation = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading route-task field-run reconciliation artifact: {exc}"
        )
        summary.update(
            {
                "reconciliation_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": safe_error,
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "reconciliation JSON read error",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task field-run reconciliation could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run reconciliation could not be read; metadata remains blocked/not_proven.",
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
                    "reason": "route-task field-run reconciliation JSON must be an object",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "reconciliation JSON shape is invalid",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task field-run reconciliation shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run reconciliation shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # Task A 的产物可能把 phone-safe 摘要放在多个兼容键下；这里只读取白名单摘要字段。
    phone_summary = {}
    for candidate in (
        reconciliation.get("phone_safe_summary"),
        reconciliation.get("phone_support_safe_summary"),
        reconciliation.get("route_task_field_run_reconciliation_summary"),
        reconciliation.get("route_task_field_run_reconciliation"),
    ):
        if isinstance(candidate, dict):
            phone_summary = candidate
            break
    source_schema = str(reconciliation.get("schema") or "")
    source_boundary = str(reconciliation.get("evidence_boundary") or "")
    source_verdict = phone_summary.get("reconciliation_verdict")
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
            phone_summary.get("status")
            or phone_summary.get("overall_status")
            or reconciliation.get("status")
            or "blocked"
        )
        verdict_value = _redact_route_task_rehearsal_text(
            phone_summary.get("verdict")
            or reconciliation.get("verdict")
            or verdict_status
            or "not_proven"
        )
        verdict_reason = _redact_route_task_rehearsal_text(
            phone_summary.get("reason") or reconciliation.get("reason") or ""
        )
    materials_status = (
        phone_summary.get("materials_status")
        if isinstance(phone_summary.get("materials_status"), dict)
        else reconciliation.get("materials_status") if isinstance(reconciliation.get("materials_status"), dict) else {}
    )
    operator_next_steps = _safe_route_task_rehearsal_list(
        phone_summary.get("operator_next_steps")
        if isinstance(phone_summary.get("operator_next_steps"), list)
        else reconciliation.get("operator_next_steps")
    )
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or reconciliation.get("safe_copy")
        or reconciliation.get("safe_phone_copy")
        or "Route-task field-run reconciliation is metadata-only; not delivery success."
    )
    # phone_safe_summary 只保留面向操作员的安全文案，避免把 Task A artifact 的任意字段透传到 diagnostics。
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
            "reconciliation_verdict": {
                "status": verdict_status or "blocked",
                "verdict": verdict_value or "not_proven",
                "reason": verdict_reason or "route-task field-run reconciliation consumed without explicit reason",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                phone_summary.get("safe_evidence_ref")
                or phone_summary.get("evidence_ref")
                or reconciliation.get("safe_evidence_ref")
                or reconciliation.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                phone_summary.get(
                    "same_evidence_ref_required",
                    reconciliation.get("same_evidence_ref_required", True),
                )
            ),
            "materials_status": _safe_pc_route_debug_dict(materials_status)
            or {
                "status": verdict_status or "blocked",
                "reason": "reconciliation consumed without explicit materials status",
            },
            "operator_next_steps": operator_next_steps,
            "phone_safe_summary": safe_phone_summary,
            "not_proven": _route_task_field_run_reconciliation_not_proven(reconciliation, phone_summary),
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_RECONCILIATION_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_RECONCILIATION_GATE:
        summary.update(
            {
                "reconciliation_verdict": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field-run reconciliation schema or evidence boundary is unsupported",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task field-run reconciliation is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field-run reconciliation is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        _route_task_field_run_readiness_has_unsafe_fields(phone_summary)
        or _route_task_field_run_intake_has_unsafe_control_claims(reconciliation)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "reconciliation_verdict": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field-run reconciliation contains unsafe summary fields or control claims",
                },
                "materials_status": {
                    "status": "blocked",
                    "reason": "unsafe reconciliation summary fields",
                },
                "phone_safe_summary": {
                    "safe_copy": "Route-task field-run reconciliation was blocked because summary fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Route-task field-run reconciliation was blocked because summary fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary

def summarize_route_task_field_run_console(path):
    """构建 route-task field-run console 的 metadata-only diagnostics 摘要。"""
    console_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_console_summary(
        console_path,
        read_error="route-task field-run console summary is not configured",
    )
    if not console_path:
        return summary
    if not os.path.exists(console_path):
        summary.update(
            {
                "console_verdict": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "route-task field-run console summary missing",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "field-run console summary artifact missing",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run console is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run console is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(console_path, "r", encoding="utf-8") as f:
            console = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading route-task field-run console summary: {exc}"
        )
        summary.update(
            {
                "console_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": safe_error,
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "field-run console JSON read error",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run console could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run console could not be read; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    if not isinstance(console, dict):
        summary.update(
            {
                "console_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field-run console JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "field-run console JSON shape is invalid",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run console shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run console shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # Task A/PC 工具可能同时提供 robot 和 mobile 摘要；diagnostics 只读取白名单字段并固定控制面关闭。
    mobile_summary = (
        console.get("mobile_readonly_summary")
        if isinstance(console.get("mobile_readonly_summary"), dict)
        else console.get("mobile_safe_summary") if isinstance(console.get("mobile_safe_summary"), dict) else {}
    )
    robot_summary = (
        console.get("robot_diagnostics_summary")
        if isinstance(console.get("robot_diagnostics_summary"), dict)
        else console.get("diagnostics_summary") if isinstance(console.get("diagnostics_summary"), dict) else {}
    )
    source_schema = str(console.get("schema") or "")
    source_boundary = str(console.get("evidence_boundary") or "")
    source_verdict = console.get("console_verdict")
    if isinstance(source_verdict, dict):
        verdict_status = _redact_route_task_rehearsal_text(
            source_verdict.get("status")
            or source_verdict.get("verdict")
            or source_verdict.get("decision")
            or console.get("status")
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
            console.get("status") or robot_summary.get("status") or "blocked"
        )
        verdict_value = _redact_route_task_rehearsal_text(
            console.get("verdict") or robot_summary.get("verdict") or verdict_status or "not_proven"
        )
        verdict_reason = _redact_route_task_rehearsal_text(
            console.get("reason") or robot_summary.get("reason") or ""
        )
    safe_copy = _redact_route_task_rehearsal_text(
        mobile_summary.get("safe_copy")
        or mobile_summary.get("safe_phone_copy")
        or console.get("safe_copy")
        or console.get("safe_phone_copy")
        or "Route-task field-run console is metadata-only; delivery_success=false."
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
            "console_verdict": {
                "status": verdict_status or "blocked",
                "verdict": verdict_value or "not_proven",
                "reason": verdict_reason or "route-task field-run console consumed without explicit reason",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                mobile_summary.get("safe_evidence_ref")
                or mobile_summary.get("evidence_ref")
                or console.get("safe_evidence_ref")
                or console.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                mobile_summary.get(
                    "same_evidence_ref_required",
                    console.get("same_evidence_ref_required", True),
                )
            ),
            "field_run_plan": _safe_pc_route_debug_dict(console.get("field_run_plan"))
            or {
                "status": "blocked",
                "steps": [],
            },
            "capture_checklist": _safe_pc_route_debug_dict(console.get("capture_checklist"))
            or {
                "status": "blocked",
                "items": [],
            },
            "dropoff_completion": _safe_pc_route_debug_value(
                console.get("dropoff_completion") or {"status": "not_proven"}
            ),
            "cancel_completion": _safe_pc_route_debug_value(
                console.get("cancel_completion") or {"status": "not_proven"}
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                mobile_summary.get("operator_next_steps")
                if isinstance(mobile_summary.get("operator_next_steps"), list)
                else console.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": verdict_status or "blocked",
                "reason": "field-run console consumed without explicit robot diagnostics summary",
            },
            "mobile_readonly_summary": safe_mobile_summary,
            "not_proven": _route_task_field_run_console_not_proven(console, mobile_summary),
            "read_error": "",
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_CONSOLE_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_CONSOLE_GATE:
        summary.update(
            {
                "console_verdict": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field-run console schema or evidence boundary is unsupported",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "field_run_plan": {
                    "status": "blocked",
                    "steps": [],
                },
                "capture_checklist": {
                    "status": "blocked",
                    "items": [],
                },
                "dropoff_completion": {"status": "not_proven"},
                "cancel_completion": {"status": "not_proven"},
                "operator_next_steps": [],
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run console is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field-run console is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        _route_task_field_run_console_has_unsafe_fields(console)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "console_verdict": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field-run console contains unsafe fields or control claims",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe field-run console summary fields",
                },
                "field_run_plan": {
                    "status": "blocked",
                    "steps": [],
                },
                "capture_checklist": {
                    "status": "blocked",
                    "items": [],
                },
                "dropoff_completion": {"status": "not_proven"},
                "cancel_completion": {"status": "not_proven"},
                "operator_next_steps": [],
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run console was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Route-task field-run console was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary

def summarize_route_task_field_run_evidence_kit(path):
    """构建 route-task field-run evidence kit 的 metadata-only diagnostics 摘要。"""
    kit_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_evidence_kit_summary(
        kit_path,
        read_error="route-task field-run evidence kit is not configured",
    )
    if not kit_path:
        return summary
    if not os.path.exists(kit_path):
        summary.update(
            {
                "kit_verdict": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "route-task field-run evidence kit missing",
                },
                "materials_status": {"status": "blocked", "reason": "evidence kit artifact missing"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "route-task field-run evidence kit artifact missing",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run evidence kit is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run evidence kit is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(kit_path, "r", encoding="utf-8") as f:
            kit = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading route-task field-run evidence kit: {exc}"
        )
        summary.update(
            {
                "kit_verdict": {"status": "read_error", "verdict": "not_proven", "reason": safe_error},
                "materials_status": {"status": "blocked", "reason": "evidence kit JSON read error"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "evidence kit JSON read error",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run evidence kit could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run evidence kit could not be read; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    if not isinstance(kit, dict):
        summary.update(
            {
                "kit_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field-run evidence kit JSON must be an object",
                },
                "materials_status": {"status": "blocked", "reason": "evidence kit JSON shape is invalid"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "evidence kit JSON shape is invalid",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run evidence kit shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run evidence kit shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # summary 来源可能已经是白名单摘要；仍只读取安全字段，并固定控制面关闭。
    mobile_summary = {}
    for candidate in (
        kit.get("mobile_readonly_summary"),
        kit.get("mobile_safe_summary"),
        kit.get("phone_safe_summary"),
        kit.get("route_task_field_run_evidence_kit_summary"),
    ):
        if isinstance(candidate, dict):
            mobile_summary = candidate
            break
    robot_summary = (
        kit.get("robot_diagnostics_summary")
        if isinstance(kit.get("robot_diagnostics_summary"), dict)
        else kit.get("diagnostics_summary") if isinstance(kit.get("diagnostics_summary"), dict) else {}
    )
    source_schema, source_boundary = _route_task_field_run_evidence_kit_source_contract(kit)
    source_verdict = kit.get("kit_verdict")
    if not isinstance(source_verdict, dict):
        source_verdict = kit.get("evidence_kit_verdict")
    if isinstance(source_verdict, dict):
        verdict_status = _redact_route_task_rehearsal_text(
            source_verdict.get("status")
            or source_verdict.get("verdict")
            or source_verdict.get("decision")
            or kit.get("status")
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
            kit.get("status") or robot_summary.get("status") or "blocked"
        )
        verdict_value = _redact_route_task_rehearsal_text(
            kit.get("verdict") or robot_summary.get("verdict") or verdict_status or "not_proven"
        )
        verdict_reason = _redact_route_task_rehearsal_text(
            kit.get("reason") or robot_summary.get("reason") or ""
        )
    materials_status = (
        kit.get("materials_status")
        if isinstance(kit.get("materials_status"), dict)
        else robot_summary.get("materials_status") if isinstance(robot_summary.get("materials_status"), dict) else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        mobile_summary.get("safe_copy")
        or mobile_summary.get("safe_phone_copy")
        or kit.get("safe_copy")
        or kit.get("safe_phone_copy")
        or "Route-task field-run evidence kit is metadata-only; delivery_success=false."
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
            "kit_verdict": {
                "status": verdict_status or "blocked",
                "verdict": verdict_value or "not_proven",
                "reason": verdict_reason or "route-task field-run evidence kit consumed without explicit reason",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                mobile_summary.get("safe_evidence_ref")
                or mobile_summary.get("evidence_ref")
                or kit.get("safe_evidence_ref")
                or kit.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                mobile_summary.get(
                    "same_evidence_ref_required",
                    kit.get("same_evidence_ref_required", True),
                )
            ),
            "materials_status": _safe_pc_route_debug_dict(materials_status)
            or {"status": verdict_status or "blocked", "reason": "evidence kit consumed without explicit materials status"},
            "field_run_plan": _safe_pc_route_debug_dict(kit.get("field_run_plan"))
            or {"status": "blocked", "steps": []},
            "capture_checklist": _safe_pc_route_debug_dict(kit.get("capture_checklist"))
            or {"status": "blocked", "items": []},
            "completion_signal_summary": _safe_pc_route_debug_dict(kit.get("completion_signal_summary")),
            "reconciliation_summary": _safe_pc_route_debug_dict(kit.get("reconciliation_summary")),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                mobile_summary.get("operator_next_steps")
                if isinstance(mobile_summary.get("operator_next_steps"), list)
                else kit.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": verdict_status or "blocked",
                "reason": "evidence kit consumed without explicit robot diagnostics summary",
            },
            "mobile_readonly_summary": safe_mobile_summary,
            "not_proven": _route_task_field_run_evidence_kit_not_proven(kit, mobile_summary),
            "read_error": "",
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_GATE:
        summary.update(
            {
                "kit_verdict": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field-run evidence kit schema or evidence boundary is unsupported",
                },
                "materials_status": {"status": "blocked", "reason": "unsupported schema or evidence boundary"},
                "field_run_plan": {"status": "blocked", "steps": []},
                "capture_checklist": {"status": "blocked", "items": []},
                "completion_signal_summary": {},
                "reconciliation_summary": {},
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run evidence kit is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field-run evidence kit is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        not summary["same_evidence_ref_required"]
        or _route_task_field_run_console_has_unsafe_fields(kit)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "kit_verdict": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field-run evidence kit contains unsafe fields or weakens same evidence_ref constraints",
                },
                "materials_status": {"status": "blocked", "reason": "unsafe evidence kit summary fields"},
                "field_run_plan": {"status": "blocked", "steps": []},
                "capture_checklist": {"status": "blocked", "items": []},
                "completion_signal_summary": {},
                "reconciliation_summary": {},
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe evidence kit summary fields",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run evidence kit was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                    "safe_phone_copy": "Route-task field-run evidence kit was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                },
            }
        )
        return summary

    return summary

def summarize_route_task_field_run_material_bundle(path):
    """构建 route-task field-run material bundle 的 metadata-only diagnostics 摘要。"""
    bundle_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_material_bundle_summary(
        bundle_path,
        read_error="route-task field-run material bundle is not configured",
    )
    if not bundle_path:
        return summary
    if not os.path.exists(bundle_path):
        summary.update(
            {
                "bundle_verdict": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "route-task field-run material bundle missing",
                },
                "materials_status": {"status": "blocked", "reason": "material bundle artifact missing"},
                "bundle_summary": {"status": "blocked", "reason": "material bundle artifact missing"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "route-task field-run material bundle artifact missing",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run material bundle is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run material bundle is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(bundle_path, "r", encoding="utf-8") as f:
            bundle = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading route-task field-run material bundle: {exc}"
        )
        summary.update(
            {
                "bundle_verdict": {"status": "read_error", "verdict": "not_proven", "reason": safe_error},
                "materials_status": {"status": "blocked", "reason": "material bundle JSON read error"},
                "bundle_summary": {"status": "blocked", "reason": "material bundle JSON read error"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "material bundle JSON read error",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run material bundle could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run material bundle could not be read; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    if not isinstance(bundle, dict):
        summary.update(
            {
                "bundle_verdict": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "route-task field-run material bundle JSON must be an object",
                },
                "materials_status": {"status": "blocked", "reason": "material bundle JSON shape is invalid"},
                "bundle_summary": {"status": "blocked", "reason": "material bundle JSON shape is invalid"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "material bundle JSON shape is invalid",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run material bundle shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run material bundle shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # 只接受白名单摘要字段；即使源文件是 summary wrapper，也固定控制面关闭。
    mobile_summary = {}
    for candidate in (
        bundle.get("mobile_readonly_summary"),
        bundle.get("mobile_safe_summary"),
        bundle.get("phone_safe_summary"),
        bundle.get("route_task_field_run_material_bundle_summary"),
    ):
        if isinstance(candidate, dict):
            mobile_summary = candidate
            break
    robot_summary = (
        bundle.get("robot_diagnostics_summary")
        if isinstance(bundle.get("robot_diagnostics_summary"), dict)
        else bundle.get("diagnostics_summary") if isinstance(bundle.get("diagnostics_summary"), dict) else {}
    )
    source_schema, source_boundary = _route_task_field_run_material_bundle_source_contract(bundle)
    source_verdict = bundle.get("bundle_verdict")
    if not isinstance(source_verdict, dict):
        source_verdict = bundle.get("material_bundle_verdict")
    if isinstance(source_verdict, dict):
        verdict_status = _redact_route_task_rehearsal_text(
            source_verdict.get("status")
            or source_verdict.get("verdict")
            or source_verdict.get("decision")
            or bundle.get("status")
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
            bundle.get("status") or robot_summary.get("status") or "blocked"
        )
        verdict_value = _redact_route_task_rehearsal_text(
            bundle.get("verdict") or robot_summary.get("verdict") or verdict_status or "not_proven"
        )
        verdict_reason = _redact_route_task_rehearsal_text(
            bundle.get("reason") or robot_summary.get("reason") or ""
        )
    materials_status = (
        bundle.get("materials_status")
        if isinstance(bundle.get("materials_status"), dict)
        else robot_summary.get("materials_status") if isinstance(robot_summary.get("materials_status"), dict) else {}
    )
    material_scaffold = (
        bundle.get("material_directory_scaffold")
        if isinstance(bundle.get("material_directory_scaffold"), dict)
        else bundle.get("material_scaffold") if isinstance(bundle.get("material_scaffold"), dict) else {}
    )
    bundle_fragment = (
        bundle.get("bundle_summary")
        if isinstance(bundle.get("bundle_summary"), dict)
        else bundle.get("summary") if isinstance(bundle.get("summary"), dict) else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        mobile_summary.get("safe_copy")
        or mobile_summary.get("safe_phone_copy")
        or bundle.get("safe_copy")
        or bundle.get("safe_phone_copy")
        or "Route-task field-run material bundle is metadata-only; delivery_success=false."
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
            "bundle_verdict": {
                "status": verdict_status or "blocked",
                "verdict": verdict_value or "not_proven",
                "reason": verdict_reason or "route-task field-run material bundle consumed without explicit reason",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                mobile_summary.get("safe_evidence_ref")
                or mobile_summary.get("evidence_ref")
                or bundle.get("safe_evidence_ref")
                or bundle.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                mobile_summary.get(
                    "same_evidence_ref_required",
                    bundle.get("same_evidence_ref_required", True),
                )
            ),
            "materials_status": _safe_pc_route_debug_dict(materials_status)
            or {"status": verdict_status or "blocked", "reason": "material bundle consumed without explicit materials status"},
            "material_directory_scaffold": _safe_pc_route_debug_dict(material_scaffold)
            or {"status": "blocked", "files": []},
            "bundle_summary": _safe_pc_route_debug_dict(bundle_fragment)
            or {"status": verdict_status or "blocked", "reason": "material bundle consumed without explicit summary"},
            "operator_next_steps": _safe_route_task_rehearsal_list(
                mobile_summary.get("operator_next_steps")
                if isinstance(mobile_summary.get("operator_next_steps"), list)
                else bundle.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": verdict_status or "blocked",
                "reason": "material bundle consumed without explicit robot diagnostics summary",
            },
            "mobile_readonly_summary": safe_mobile_summary,
            "not_proven": _route_task_field_run_material_bundle_not_proven(bundle, mobile_summary),
            "read_error": "",
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_GATE:
        summary.update(
            {
                "bundle_verdict": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field-run material bundle schema or evidence boundary is unsupported",
                },
                "materials_status": {"status": "blocked", "reason": "unsupported schema or evidence boundary"},
                "material_directory_scaffold": {"status": "blocked", "files": []},
                "bundle_summary": {"status": "blocked", "reason": "unsupported schema or evidence boundary"},
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run material bundle is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field-run material bundle is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        not summary["same_evidence_ref_required"]
        or _route_task_field_run_console_has_unsafe_fields(bundle)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "bundle_verdict": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "route-task field-run material bundle contains unsafe fields or weakens same evidence_ref constraints",
                },
                "materials_status": {"status": "blocked", "reason": "unsafe material bundle summary fields"},
                "material_directory_scaffold": {"status": "blocked", "files": []},
                "bundle_summary": {"status": "blocked", "reason": "unsafe material bundle summary fields"},
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe material bundle summary fields",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run material bundle was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                    "safe_phone_copy": "Route-task field-run material bundle was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                },
            }
        )
        return summary

    return summary

def summarize_route_task_field_run_material_validation(path):
    """构建 route-task field-run material validation 的 metadata-only diagnostics 摘要。"""
    validation_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_material_validation_summary(
        validation_path,
        read_error="route-task field-run material validation is not configured",
    )
    if not validation_path:
        return summary
    if not os.path.exists(validation_path):
        summary.update(
            {
                "validation_verdict": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "route-task field-run material validation missing",
                },
                "materials_status": {"status": "blocked", "reason": "material validation artifact missing"},
                "validation_summary": {"status": "blocked", "reason": "material validation artifact missing"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "route-task field-run material validation artifact missing",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run material validation is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run material validation is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(validation_path, "r", encoding="utf-8") as f:
            validation = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading route-task field-run material validation: {exc}"
        )
        summary.update(
            {
                "validation_verdict": {"status": "read_error", "verdict": "not_proven", "reason": safe_error},
                "materials_status": {"status": "blocked", "reason": "material validation JSON read error"},
                "validation_summary": {"status": "blocked", "reason": "material validation JSON read error"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "material validation JSON read error",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run material validation could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run material validation could not be read; metadata remains blocked/not_proven.",
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
                    "reason": "route-task field-run material validation JSON must be an object",
                },
                "materials_status": {"status": "blocked", "reason": "material validation JSON shape is invalid"},
                "validation_summary": {"status": "blocked", "reason": "material validation JSON shape is invalid"},
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "material validation JSON shape is invalid",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run material validation shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Route-task field-run material validation shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # Autonomy 可能交付 artifact 或 summary wrapper；diagnostics 只白名单消费摘要字段并固定控制面关闭。
    mobile_summary = {}
    for candidate in (
        validation.get("mobile_readonly_summary"),
        validation.get("mobile_safe_summary"),
        validation.get("phone_safe_summary"),
        validation.get("route_task_field_run_material_validation_summary"),
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
    source_schema, source_boundary = _route_task_field_run_material_validation_source_contract(validation)
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
        or "Route-task field-run material validation is metadata-only; delivery_success=false."
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
                "reason": verdict_reason or "route-task field-run material validation consumed without explicit reason",
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
            or {"status": verdict_status or "blocked", "reason": "material validation consumed without explicit materials status"},
            "validation_summary": _safe_pc_route_debug_dict(validation_fragment)
            or {"status": verdict_status or "blocked", "reason": "material validation consumed without explicit summary"},
            "material_validation_checks": _safe_pc_route_debug_value(checks if isinstance(checks, list) else []),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                mobile_summary.get("operator_next_steps")
                if isinstance(mobile_summary.get("operator_next_steps"), list)
                else validation.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": verdict_status or "blocked",
                "reason": "material validation consumed without explicit robot diagnostics summary",
            },
            "mobile_readonly_summary": safe_mobile_summary,
            "not_proven": _route_task_field_run_material_validation_not_proven(validation, mobile_summary),
            "read_error": "",
            "metadata_only": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_GATE:
        summary.update(
            {
                "validation_verdict": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "route-task field-run material validation schema or evidence boundary is unsupported",
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
                    "safe_copy": "Route-task field-run material validation is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Route-task field-run material validation is not a supported diagnostics source; no delivery result is proven.",
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
                    "reason": "route-task field-run material validation contains unsafe fields or weakens same evidence_ref constraints",
                },
                "materials_status": {"status": "blocked", "reason": "unsafe material validation summary fields"},
                "validation_summary": {"status": "blocked", "reason": "unsafe material validation summary fields"},
                "material_validation_checks": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe material validation summary fields",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Route-task field-run material validation was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                    "safe_phone_copy": "Route-task field-run material validation was blocked because fields could expose control data, weaken evidence_ref constraints, or imply delivery success.",
                },
            }
        )
        return summary

    return summary

