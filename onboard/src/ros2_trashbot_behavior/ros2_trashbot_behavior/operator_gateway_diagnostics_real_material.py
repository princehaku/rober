"""Real-material metadata-only diagnostics helpers.

本模块承接 operator_gateway_diagnostics facade 中真实材料 metadata 诊断逻辑。
它只消费已消毒 summary / wrapper，不读取串口、ROS graph、硬件设备或原始材料。
"""

import json
import os
import re

from ros2_trashbot_behavior.operator_gateway_diagnostics_route_rehearsal import (
    _redact_route_task_rehearsal_text,
    _safe_pc_route_debug_dict,
    _safe_pc_route_debug_value,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_run import (
    _route_task_field_run_readiness_has_unsafe_fields,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_verified_terminal_material import (
    EVIDENCE_SOURCE_SOFTWARE,
    _task_terminal_field_material_intake_copy_is_unsafe,
)


HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SCHEMA = (
    "trashbot.hardware_real_material_escalation_request.v1"
)
HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.hardware_real_material_escalation_request_summary.v1"
)
HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_hardware_real_material_escalation_request_summary.v1"
)
HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_GATE = (
    "software_proof_docker_hardware_real_material_escalation_request_gate"
)
REAL_MATERIAL_READINESS_BOARD_SCHEMA = "trashbot.real_material_readiness_board.v1"
REAL_MATERIAL_READINESS_BOARD_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.real_material_readiness_board_summary.v1"
)
REAL_MATERIAL_READINESS_BOARD_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_real_material_readiness_board_summary.v1"
)
REAL_MATERIAL_READINESS_BOARD_GATE = "software_proof_docker_real_material_readiness_board_gate"
REAL_MATERIAL_EVIDENCE_INTAKE_SCHEMA = "trashbot.real_material_evidence_intake.v1"
REAL_MATERIAL_EVIDENCE_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.real_material_evidence_intake_summary.v1"
)
REAL_MATERIAL_EVIDENCE_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_real_material_evidence_intake_summary.v1"
)
REAL_MATERIAL_EVIDENCE_INTAKE_GATE = (
    "software_proof_docker_real_material_evidence_intake_gate"
)
REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA = (
    "trashbot.real_material_followup_escalation_status.v1"
)
REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.real_material_followup_escalation_status_summary.v1"
)
REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_real_material_followup_escalation_status_summary.v1"
)
REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE = (
    "software_proof_docker_real_material_followup_escalation_status_gate"
)


HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_REQUIRED_NOT_PROVEN = (
    "real_wave_rover",
    "real_uart",
    "real_hil_pass",
    "real_2d_lidar",
    "real_tof",
    "real_procurement_receipt",
    "real_install_wiring_power_calibration",
    "route_elevator_field_pass",
    "delivery_success",
    "primary_actions_enabled",
)
REAL_MATERIAL_READINESS_BOARD_REQUIRED_NOT_PROVEN = (
    "objective_5_external_proof",
    "public_https_tls",
    "real_4g_or_sim",
    "oss_cdn_live_traffic",
    "production_db_queue",
    "real_wave_rover_uart_hil_materials",
    "real_2d_lidar_tof_materials",
    "route_elevator_field_pass",
    "real_phone_device_or_browser",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)
REAL_MATERIAL_EVIDENCE_INTAKE_REQUIRED_NOT_PROVEN = (
    "real_materials_observed",
    "raw_material_manifest",
    "real_hil_pass",
    "real_public_cloud",
    "real_phone_device_or_browser",
    "route_elevator_field_pass",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)
REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_REQUIRED_NOT_PROVEN = (
    "objective_5_external_proof",
    "real_public_https_tls",
    "real_4g_or_sim",
    "oss_cdn_live_traffic",
    "production_db_queue",
    "worker_cutover_or_migration",
    "real_wave_rover_uart_hil_materials",
    "real_2d_lidar_tof_materials",
    "route_elevator_field_pass",
    "real_phone_device_or_browser",
    "real_materials_observed",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)
REAL_MATERIAL_MANIFEST_TEMPLATE_FIELDS = (
    "manifest_template",
    "template_groups",
    "required_item_templates",
)
REAL_MATERIAL_MANIFEST_TEMPLATE_ALLOWED_KEYS = {
    "schema",
    "status",
    "boundary",
    "evidence_boundary",
    "source_evidence_boundary",
    "source",
    "not_proven",
    "material_group",
    "material_groups",
    "required_item_name",
    "required_item_names",
    "required_item_templates",
    "summary_hint",
    "material_ref_hint",
    "owner_handoff",
    "objective_ref",
    "next_action",
    "same_evidence_ref_required",
    "safe_evidence_ref",
    "evidence_ref",
    "template_evidence_ref",
    "safe_template_evidence_ref",
}
REAL_MATERIAL_MANIFEST_TEMPLATE_EVIDENCE_REF_KEYS = {
    "safe_evidence_ref",
    "evidence_ref",
    "template_evidence_ref",
    "safe_template_evidence_ref",
}



def _dedupe_ordered(values):
    # diagnostics 摘要要保持 Hardware gate 的顺序，同时避免重复 not_proven / missing material 文案刷屏。
    items = []
    for value in values:
        text = _redact_route_task_rehearsal_text(value)
        if text and text not in items:
            items.append(text)
    return items




def _hardware_real_material_escalation_request_not_proven(request=None, summary_fragment=None):
    # 真实材料升级请求只能说明“还缺哪些材料”，不能被 UI 或诊断层解释为硬件闭环。
    request = request if isinstance(request, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for source in (request, summary_fragment):
        if isinstance(source.get("not_proven"), list):
            source_values.extend(source.get("not_proven"))
        if isinstance(source.get("missing_real_materials"), list):
            source_values.extend(source.get("missing_real_materials"))
        if isinstance(source.get("required_real_materials"), list):
            source_values.extend(source.get("required_real_materials"))
    for item in (
        list(source_values)
        + list(HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_REQUIRED_NOT_PROVEN)
    ):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _real_material_readiness_board_not_proven(board=None, summary_fragment=None):
    # readiness board 只是跨端路由面板；所有真实材料、控制授权和交付结论仍必须保持未证明。
    board = board if isinstance(board, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for source in (board, summary_fragment):
        if isinstance(source.get("not_proven"), list):
            source_values.extend(source.get("not_proven"))
        if isinstance(source.get("next_required_evidence"), list):
            source_values.extend(source.get("next_required_evidence"))
        for group in source.get("material_groups", []):
            if not isinstance(group, dict):
                continue
            if isinstance(group.get("next_required_evidence"), list):
                source_values.extend(group.get("next_required_evidence"))
            if str(group.get("blocking_reason") or "").strip():
                source_values.append(group.get("blocking_reason"))
    for item in list(source_values) + list(REAL_MATERIAL_READINESS_BOARD_REQUIRED_NOT_PROVEN):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _real_material_evidence_intake_not_proven(intake=None, summary_fragment=None):
    # evidence intake 只消费已消毒摘要；真实材料、真实手机、公网、HIL 和控制授权继续外部证明。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for source in (intake, summary_fragment):
        if isinstance(source.get("not_proven"), list):
            source_values.extend(source.get("not_proven"))
        if isinstance(source.get("missing_real_materials"), list):
            source_values.extend(source.get("missing_real_materials"))
        if isinstance(source.get("next_required_evidence"), list):
            source_values.extend(source.get("next_required_evidence"))
    for item in list(source_values) + list(REAL_MATERIAL_EVIDENCE_INTAKE_REQUIRED_NOT_PROVEN):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _real_material_followup_escalation_status_not_proven(status=None, summary_fragment=None):
    # follow-up status 是升级追责面板，不是材料验收；所有真实材料和控制结论继续保持未证明。
    status = status if isinstance(status, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for source in (status, summary_fragment):
        if isinstance(source.get("not_proven"), list):
            source_values.extend(source.get("not_proven"))
        if isinstance(source.get("next_required_evidence"), list):
            source_values.extend(source.get("next_required_evidence"))
        for group in source.get("material_groups", []):
            if not isinstance(group, dict):
                continue
            if str(group.get("blocked_reason") or "").strip():
                source_values.append(group.get("blocked_reason"))
            if isinstance(group.get("next_required_evidence"), list):
                source_values.extend(group.get("next_required_evidence"))
    for item in (
        list(source_values)
        + list(REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_REQUIRED_NOT_PROVEN)
    ):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _default_hardware_real_material_escalation_request_summary(
    path,
    status="blocked_missing_hardware_real_material_escalation_request_summary",
    read_error="",
):
    # 默认缺省态保持 not_proven，防止缺材料请求被误解为已采集真实硬件证据。
    safe_copy = (
        "Hardware real material escalation request is metadata-only; "
        "software_proof, not_proven, delivery_success=false and "
        "primary_actions_enabled=false."
    )
    return {
        "schema": HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {"schema": "", "evidence_boundary": "", "metadata_only": True},
        "status": status,
        "overall_status": "not_proven",
        "request_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error
            or "hardware_real_material_escalation_request summary is not configured",
        },
        "safe_evidence_ref": "",
        "missing_real_materials": [],
        "required_real_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "safe_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _hardware_real_material_escalation_request_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
        "request_only": True,
        "hardware_material_pending": True,
        "real_hardware_observed": False,
        "wave_rover_verified": False,
        "uart_verified": False,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
        "sensor_wiring_verified": False,
        "sensor_power_budget_verified": False,
        "sensor_calibrated_on_robot": False,
        "route_elevator_field_pass": False,
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
    }


def _default_real_material_readiness_board_summary(
    path,
    status="blocked_missing_real_material_readiness_board_summary",
    read_error="",
):
    # 缺源或缺 summary 时必须 fail closed；Robot 不能用 readiness board 推导真实材料已就绪。
    safe_copy = (
        "Real material readiness board is routing-only; software_proof, not_proven, "
        "delivery_success=false, primary_actions_enabled=false, safe_to_control=false."
    )
    return {
        "schema": REAL_MATERIAL_READINESS_BOARD_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": REAL_MATERIAL_READINESS_BOARD_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {"schema": "", "evidence_boundary": "", "metadata_only": True},
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "board_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": read_error or "real_material_readiness_board summary is not configured",
        },
        "safe_evidence_ref": "",
        "material_groups": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "safe_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _real_material_readiness_board_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "routing_only": True,
        "summary_required": True,
        "real_materials_observed": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
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


def _default_real_material_evidence_intake_summary(
    path,
    status="blocked_missing_real_material_evidence_intake_summary",
    read_error="",
):
    # 缺少已消毒 summary 时直接 fail closed，避免 Robot 侧回读真实材料 manifest 或路径。
    safe_copy = (
        "Real material evidence intake is metadata-only; software_proof, "
        "not_proven, delivery_success=false, primary_actions_enabled=false, "
        "safe_to_control=false."
    )
    return {
        "schema": REAL_MATERIAL_EVIDENCE_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": REAL_MATERIAL_EVIDENCE_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {"schema": "", "evidence_boundary": "", "metadata_only": True},
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "intake_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": read_error or "real_material_evidence_intake summary is not configured",
        },
        "safe_evidence_ref": "",
        "accepted_materials": [],
        "missing_real_materials": [],
        "rejected_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "real_material_manifest_template": {},
        "safe_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _real_material_evidence_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
        "real_materials_observed": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
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


def _default_real_material_followup_escalation_status_summary(
    path,
    status="blocked_missing_real_material_followup_escalation_status_summary",
    read_error="",
):
    # 缺 summary 时不回退读取 manifest/materials；Robot 只能拿已消毒的升级状态摘要。
    safe_copy = (
        "Real material follow-up escalation status is metadata-only; software_proof, "
        "not_proven, delivery_success=false, primary_actions_enabled=false, "
        "safe_to_control=false."
    )
    return {
        "schema": REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {"schema": "", "evidence_boundary": "", "metadata_only": True},
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "followup_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": read_error
            or "real_material_followup_escalation_status summary is not configured",
        },
        "safe_evidence_ref": "",
        "material_group": "",
        "field_owner": "",
        "due_status": "",
        "blocked_reason": "",
        "next_required_evidence": [],
        "escalation_level": "",
        "rerun_command": "",
        "rerun_status_summary": {},
        "source_template_status": "",
        "source_intake_status": "",
        "review_route": [],
        "owner_handoff": [],
        "material_groups": [],
        "safe_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _real_material_followup_escalation_status_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
        "real_materials_observed": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
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


def _hardware_real_material_escalation_request_source_contract(value):
    # Robot 侧只接受 Hardware worker 已消毒 summary；artifact wrapper 也必须内含同 boundary summary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SOURCE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _real_material_readiness_board_source_contract(value):
    # 支持 PC gate artifact 或已消毒 summary；summary 必须回指同一个 board source schema。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == REAL_MATERIAL_READINESS_BOARD_SOURCE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or REAL_MATERIAL_READINESS_BOARD_SCHEMA)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _real_material_evidence_intake_source_contract(value):
    # Robot alias 只信任 intake artifact 的 sanitized summary；summary wrapper 必须回指同一 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == REAL_MATERIAL_EVIDENCE_INTAKE_SOURCE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or REAL_MATERIAL_EVIDENCE_INTAKE_SCHEMA)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _real_material_followup_escalation_status_source_contract(value):
    # follow-up status 必须来自 PC gate 的 summary；artifact wrapper 也只能承载已消毒 summary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _real_material_evidence_ref_is_unsafe(value):
    # evidence_ref 只允许短的逻辑引用；本地路径、脱敏标记、空白或 shell 字符都不能进 diagnostics。
    text = str(value or "").strip()
    if (
        not text
        or text.startswith("local_path_redacted:")
        or "[REDACTED" in text
        or not re.fullmatch(r"(?:evidence://)?[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}", text)
    ):
        return True
    return False


def _real_material_followup_escalation_status_has_unsafe_fields(value, key_path=""):
    # 升级状态只允许可展示摘要；raw manifest/materials、凭证、checksum、成功或控制字段全部阻断。
    unsafe_key_fragments = (
        "raw_manifest",
        "raw_material",
        "raw_materials",
        "full_manifest",
        "material_manifest",
        "credential",
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "checksum",
        "raw_artifact",
        "raw_json",
        "raw_payload",
        "raw_response",
        "raw_robot",
        "ros_graph",
        "ros_topic",
        "topic_name",
        "serial",
        "uart",
        "baud",
        "cmd_vel",
        "wave_rover",
        "ack_payload",
        "command_envelope",
        "status_envelope",
        "success_status",
        "control_grant",
        "robot_command_allowed",
        "commands_enabled",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
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
        "dropoff_completion",
        "cancel_completion",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _real_material_followup_escalation_status_has_unsafe_fields(
                item,
                current_path,
            ):
                return True
    if isinstance(value, list):
        return any(
            _real_material_followup_escalation_status_has_unsafe_fields(item, key_path)
            for item in value
        )
    if isinstance(value, str):
        return _task_terminal_field_material_intake_copy_is_unsafe(value)
    return False


def _real_material_manifest_template_scalar_is_unsafe(key, value):
    # template 字段只作为手机安全提示；路径、凭证、串口、ROS topic 或控制暗示都必须整段拒绝。
    key_text = str(key or "").strip().lower()
    if key_text in REAL_MATERIAL_MANIFEST_TEMPLATE_EVIDENCE_REF_KEYS:
        return _real_material_evidence_ref_is_unsafe(value)
    if key_text == "same_evidence_ref_required":
        return value is not True
    text = _redact_route_task_rehearsal_text(value)
    if any(
        marker in text
        for marker in (
            "[REDACTED_AUTH_HEADER]",
            "Bearer [REDACTED]",
            "[REDACTED_URL]",
            "/dev/[REDACTED_SERIAL]",
            "[REDACTED_BAUD]",
            "[REDACTED_TRACEBACK]",
            "[REDACTED_LOCAL_PATH]",
        )
    ):
        return True
    if key_text in {"summary_hint", "material_ref_hint", "next_action"}:
        return _task_terminal_field_material_intake_copy_is_unsafe(text)
    return False


def _safe_real_material_manifest_template_value(value, key="", depth=0):
    # 这里不用通用递归透传；manifest template 是跨 worker 合同，必须逐 key 白名单。
    if depth > 4:
        return None, True
    if isinstance(value, dict):
        safe = {}
        for raw_key, raw_item in value.items():
            safe_key = str(raw_key or "").strip()
            normalized_key = safe_key.lower()
            if normalized_key not in REAL_MATERIAL_MANIFEST_TEMPLATE_ALLOWED_KEYS:
                return None, True
            safe_item, unsafe = _safe_real_material_manifest_template_value(
                raw_item,
                normalized_key,
                depth=depth + 1,
            )
            if unsafe:
                return None, True
            safe[normalized_key] = safe_item
        return safe, False
    if isinstance(value, list):
        safe_items = []
        for item in value[:20]:
            safe_item, unsafe = _safe_real_material_manifest_template_value(
                item,
                key,
                depth=depth + 1,
            )
            if unsafe:
                return None, True
            safe_items.append(safe_item)
        return safe_items, False
    if isinstance(value, bool):
        if _real_material_manifest_template_scalar_is_unsafe(key, value):
            return None, True
        return value, False
    if value is None:
        return None, False
    if isinstance(value, (int, float)):
        # 模板白名单没有数值型生产材料字段；拒绝数值可避免尺寸、电压、baud 等硬件 raw 值泄露。
        return None, True
    if _real_material_manifest_template_scalar_is_unsafe(key, value):
        return None, True
    return _redact_route_task_rehearsal_text(value), False


def _safe_real_material_manifest_template_alias(intake, summary_fragment):
    # 兼容 Hardware worker 可能写入的 manifest_template/template_groups/required_item_templates 三种入口。
    safe_template = {}
    for source in (summary_fragment, intake):
        if not isinstance(source, dict):
            continue
        for field in REAL_MATERIAL_MANIFEST_TEMPLATE_FIELDS:
            if field not in source or field in safe_template:
                continue
            safe_value, unsafe = _safe_real_material_manifest_template_value(source.get(field))
            if unsafe:
                return {}, True
            safe_template[field] = safe_value
    return safe_template, False



def _pr5_review_thread_closeout_copy_is_unsafe(value):
    # 允许安全边界里的 false/not_proven 文案；其余 success/control/HIL/field-pass 语义一律降级。
    redacted = _redact_route_task_rehearsal_text(value)
    guarded = redacted.lower()
    for phrase in (
        "delivery_success=false",
        "primary_actions_enabled=false",
        "not_proven",
        "not proven",
        "metadata-only",
        "software_proof",
        "must not",
        "not real",
        "不证明",
    ):
        guarded = guarded.replace(phrase, "")
    return (
        "success" in guarded
        or "passed" in guarded
        or "field pass" in guarded
        or "hil pass" in guarded
        or "control enabled" in guarded
        or "start delivery" in guarded
        or "confirm dropoff" in guarded
        or "cancel delivery" in guarded
        or "/cmd_vel" in guarded
        or "ack posted" in guarded
        or "cursor advanced" in guarded
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


def _pr5_review_thread_closeout_has_unsafe_fields(value, key_path=""):
    # PR review 原文、控制入口、凭证、本机路径和 raw artifact 都不能泄进 Robot diagnostics。
    unsafe_key_fragments = (
        "raw",
        "body",
        "comment",
        "credential",
        "token",
        "secret",
        "ack",
        "cursor",
        "cmd_vel",
        "command",
        "control",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text == "not_proven":
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if key_text == "delivery_success" and item is not False:
                return True
            if key_text == "primary_actions_enabled" and item is not False:
                return True
            if _pr5_review_thread_closeout_has_unsafe_fields(item, current_path):
                return True
    if isinstance(value, list):
        return any(_pr5_review_thread_closeout_has_unsafe_fields(item, key_path) for item in value)
    if isinstance(value, str):
        return _pr5_review_thread_closeout_copy_is_unsafe(value)
    return False


def summarize_pr5_review_thread_closeout(source):
    """构建 PR #5 review thread closeout 的 metadata-only Robot diagnostics 摘要。"""
    # 这里故意要求 Hardware gate 的 sanitized summary；缺 summary 不能退回读取 raw review thread。


def summarize_hardware_real_material_escalation_request(source):
    """构建真实硬件材料升级请求的 metadata-only Robot diagnostics 摘要。"""
    # 只读消费 Hardware worker 的 sanitized summary；不能读取串口、ROS graph 或原始硬件材料正文。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_real_material_escalation_request_summary(
        source_path,
        read_error="hardware_real_material_escalation_request summary is not configured",
    )
    if isinstance(source, dict):
        request = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = "hardware_real_material_escalation_request summary artifact missing"
            summary["request_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                request = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware_real_material_escalation_request summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["request_status"]["reason"] = safe_error
            return summary

    if not isinstance(request, dict):
        summary["request_status"]["reason"] = "hardware_real_material_escalation_request JSON must be an object"
        return summary

    raw_schema = str(request.get("schema") or "")
    summary_fragment = {}
    source_schema, source_boundary = _hardware_real_material_escalation_request_source_contract(
        request
    )
    if raw_schema == HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SOURCE_SUMMARY_SCHEMA:
        summary_fragment = request
    else:
        for candidate in (
            request.get("hardware_real_material_escalation_request_summary"),
            request.get("robot_diagnostics_hardware_real_material_escalation_request_summary"),
            request.get("diagnostics_summary"),
            request.get("robot_diagnostics_summary"),
            request.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if isinstance(summary_fragment, dict) and summary_fragment:
        nested_schema, nested_boundary = (
            _hardware_real_material_escalation_request_source_contract(summary_fragment)
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    accepted_schemas = {
        HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SCHEMA,
        HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SOURCE_SUMMARY_SCHEMA,
    }
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or request.get("safe_copy")
        or request.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    request_status = (
        summary_fragment.get("request_status")
        if isinstance(summary_fragment.get("request_status"), dict)
        else request.get("request_status")
        if isinstance(request.get("request_status"), dict)
        else {}
    )
    status = _redact_route_task_rehearsal_text(
        request_status.get("status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or request.get("status")
        or request.get("overall_status")
        or "not_proven"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or request.get("safe_evidence_ref")
        or request.get("evidence_ref", "")
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else request.get("robot_diagnostics_summary")
        if isinstance(request.get("robot_diagnostics_summary"), dict)
        else {}
    )
    safe_robot_summary = {
        "safe_copy": _redact_route_task_rehearsal_text(
            robot_summary.get("safe_copy") or safe_copy
        ),
        "safe_phone_copy": _redact_route_task_rehearsal_text(
            robot_summary.get("safe_phone_copy") or safe_copy
        ),
    }
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or request.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "status": status,
            "overall_status": "not_proven",
            "request_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    request_status.get("reason")
                    or summary_fragment.get("reason")
                    or request.get("reason")
                    or "hardware real material escalation request is software_proof only"
                ),
            },
            "safe_evidence_ref": safe_evidence_ref,
            "missing_real_materials": _dedupe_ordered(
                _safe_route_task_rehearsal_list(
                    summary_fragment.get("missing_real_materials")
                    if isinstance(summary_fragment.get("missing_real_materials"), list)
                    else request.get("missing_real_materials")
                )
            ),
            "required_real_materials": _dedupe_ordered(
                _safe_route_task_rehearsal_list(
                    summary_fragment.get("required_real_materials")
                    if isinstance(summary_fragment.get("required_real_materials"), list)
                    else request.get("required_real_materials")
                )
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
                if isinstance(summary_fragment.get("next_required_evidence"), list)
                else request.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
                if isinstance(summary_fragment.get("owner_handoff"), list)
                else request.get("owner_handoff")
            ),
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "robot_diagnostics_summary": safe_robot_summary,
            "not_proven": _hardware_real_material_escalation_request_not_proven(
                request,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    if (
        source_schema not in accepted_schemas
        or source_boundary != HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_GATE
    ):
        summary["status"] = "unsupported_schema"
        summary["request_status"] = {
            "status": "unsupported_schema",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": "hardware_real_material_escalation_request schema or evidence boundary is unsupported",
        }
        summary["safe_evidence_ref"] = ""
        return summary
    if not isinstance(summary_fragment, dict) or not summary_fragment:
        summary["status"] = "blocked_missing_hardware_real_material_escalation_request_summary"
        summary["request_status"] = {
            "status": "blocked_missing_hardware_real_material_escalation_request_summary",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": "hardware_real_material_escalation_request is missing sanitized summary",
        }
        summary["safe_evidence_ref"] = ""
        return summary
    if (
        request.get("delivery_success") is not False
        or request.get("primary_actions_enabled") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or _pr5_review_thread_closeout_has_unsafe_fields(request)
        or _pr5_review_thread_closeout_has_unsafe_fields(summary_fragment)
        or _pr5_review_thread_closeout_copy_is_unsafe(safe_copy)
        or _pr5_review_thread_closeout_copy_is_unsafe(safe_robot_summary.get("safe_copy", ""))
        or not safe_evidence_ref
        or safe_evidence_ref.startswith("local_path_redacted:")
    ):
        # 任一 unsafe 字段都降级为 not_proven，避免材料请求变成控制授权或 HIL 通过声明。
        blocked_copy = (
            "Hardware real material escalation request was blocked because the summary "
            "could expose raw hardware/control data or imply success; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_hardware_real_material_escalation_request_summary",
                "request_status": {
                    "status": "blocked_unsafe_hardware_real_material_escalation_request_summary",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware_real_material_escalation_request contains unsafe fields, success wording, weak evidence_ref, or enabled actions",
                },
                "safe_evidence_ref": "",
                "safe_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary


def summarize_real_material_readiness_board(source):
    """构建真实材料就绪看板的 metadata-only Robot diagnostics 摘要。"""
    # Robot 只消费 PC gate 的 board artifact/summary，不读取 PC gate 的原始证据正文或任何控制入口。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_real_material_readiness_board_summary(
        source_path,
        read_error="real_material_readiness_board summary is not configured",
    )
    if isinstance(source, dict):
        board = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = "real_material_readiness_board summary artifact missing"
            summary["board_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                board = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading real_material_readiness_board summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["board_status"]["reason"] = safe_error
            return summary

    if not isinstance(board, dict):
        summary["board_status"]["reason"] = "real_material_readiness_board JSON must be an object"
        return summary

    raw_schema = str(board.get("schema") or "")
    source_schema, source_boundary = _real_material_readiness_board_source_contract(board)
    if raw_schema in {
        REAL_MATERIAL_READINESS_BOARD_SCHEMA,
        REAL_MATERIAL_READINESS_BOARD_SOURCE_SUMMARY_SCHEMA,
    }:
        summary_fragment = board
    else:
        summary_fragment = {}
        for candidate in (
            board.get("real_material_readiness_board_summary"),
            board.get("robot_diagnostics_real_material_readiness_board_summary"),
            board.get("diagnostics_summary"),
            board.get("robot_diagnostics_summary"),
            board.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if isinstance(summary_fragment, dict) and summary_fragment:
        nested_schema, nested_boundary = _real_material_readiness_board_source_contract(
            summary_fragment
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    accepted_schemas = {
        REAL_MATERIAL_READINESS_BOARD_SCHEMA,
        REAL_MATERIAL_READINESS_BOARD_SOURCE_SUMMARY_SCHEMA,
    }
    board_status = (
        summary_fragment.get("board_status")
        if isinstance(summary_fragment.get("board_status"), dict)
        else board.get("board_status")
        if isinstance(board.get("board_status"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or board.get("safe_copy")
        or board.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    status = _redact_route_task_rehearsal_text(
        board_status.get("status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or board.get("status")
        or board.get("overall_status")
        or "not_proven"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status") or board.get("overall_status") or status
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or board.get("source")
        or board_status.get("evidence_source")
        or ""
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or board.get("safe_evidence_ref")
        or board.get("evidence_ref", "")
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else board.get("robot_diagnostics_summary")
        if isinstance(board.get("robot_diagnostics_summary"), dict)
        else {}
    )
    safe_robot_summary = {
        "safe_copy": _redact_route_task_rehearsal_text(
            robot_summary.get("safe_copy") or safe_copy
        ),
        "safe_phone_copy": _redact_route_task_rehearsal_text(
            robot_summary.get("safe_phone_copy") or safe_copy
        ),
    }
    material_groups_source = (
        summary_fragment.get("material_groups")
        if isinstance(summary_fragment.get("material_groups"), list)
        else board.get("material_groups")
    )
    next_required_source = (
        summary_fragment.get("next_required_evidence")
        if isinstance(summary_fragment.get("next_required_evidence"), list)
        else board.get("next_required_evidence")
    )
    owner_handoff_source = (
        summary_fragment.get("owner_handoff")
        if isinstance(summary_fragment.get("owner_handoff"), list)
        else board.get("owner_handoff")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or board.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "board_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    board_status.get("reason")
                    or summary_fragment.get("reason")
                    or board.get("reason")
                    or "real material readiness board is software_proof only"
                ),
            },
            "safe_evidence_ref": safe_evidence_ref,
            "material_groups": _safe_pc_route_debug_value(
                material_groups_source if isinstance(material_groups_source, list) else []
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(next_required_source),
            "owner_handoff": _safe_route_task_rehearsal_list(owner_handoff_source),
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "robot_diagnostics_summary": safe_robot_summary,
            "not_proven": _real_material_readiness_board_not_proven(board, summary_fragment),
            "read_error": "",
        }
    )
    boundary_supported = not source_boundary or source_boundary == REAL_MATERIAL_READINESS_BOARD_GATE
    if source_schema not in accepted_schemas or not boundary_supported:
        summary.update(
            {
                "status": "unsupported_schema",
                "board_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "real_material_readiness_board schema or evidence boundary is unsupported",
                },
                "safe_evidence_ref": "",
                "material_groups": [],
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary

    # 只接受明确的 software_proof/not_proven/false 控制布尔值；缺失或字符串 false 都降级。
    if (
        source_value != EVIDENCE_SOURCE_SOFTWARE
        or status != "not_proven"
        or overall_status != "not_proven"
        or board.get("delivery_success") is not False
        or board.get("primary_actions_enabled") is not False
        or board.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _route_task_field_run_readiness_has_unsafe_fields(board)
        or _route_task_field_run_readiness_has_unsafe_fields(summary_fragment)
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy)
        or _task_terminal_field_material_intake_copy_is_unsafe(
            safe_robot_summary.get("safe_copy", "")
        )
    ):
        blocked_copy = (
            "Real material readiness board was blocked because the source did not remain "
            "software_proof/not_proven with delivery_success=false, "
            "primary_actions_enabled=false, and safe_to_control=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_real_material_readiness_board_summary",
                "board_status": {
                    "status": "blocked_unsafe_real_material_readiness_board_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "real_material_readiness_board contains unsupported status, unsafe fields, success wording, or control claims",
                },
                "safe_evidence_ref": "",
                "material_groups": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "safe_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary


def summarize_real_material_evidence_intake(source):
    """构建真实材料证据入口的 metadata-only Robot diagnostics 摘要。"""
    # Robot 侧只消费 intake gate 的 sanitized summary；artifact 本体只能作为 summary wrapper 容器。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_real_material_evidence_intake_summary(
        source_path,
        read_error="real_material_evidence_intake summary is not configured",
    )
    if isinstance(source, dict):
        intake = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = "real_material_evidence_intake summary artifact missing"
            summary["intake_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading real_material_evidence_intake summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["intake_status"]["reason"] = safe_error
            return summary

    if not isinstance(intake, dict):
        summary["intake_status"]["reason"] = "real_material_evidence_intake JSON must be an object"
        return summary

    raw_schema = str(intake.get("schema") or "")
    source_schema, source_boundary = _real_material_evidence_intake_source_contract(intake)
    if raw_schema == REAL_MATERIAL_EVIDENCE_INTAKE_SOURCE_SUMMARY_SCHEMA:
        summary_fragment = intake
    else:
        summary_fragment = {}
        for candidate in (
            intake.get("real_material_evidence_intake_summary"),
            intake.get("robot_diagnostics_real_material_evidence_intake_summary"),
            intake.get("diagnostics_summary"),
            intake.get("robot_diagnostics_summary"),
            intake.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if isinstance(summary_fragment, dict) and summary_fragment:
        nested_schema, nested_boundary = _real_material_evidence_intake_source_contract(
            summary_fragment
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    accepted_schemas = {
        REAL_MATERIAL_EVIDENCE_INTAKE_SCHEMA,
        REAL_MATERIAL_EVIDENCE_INTAKE_SOURCE_SUMMARY_SCHEMA,
    }
    intake_status = (
        summary_fragment.get("intake_status")
        if isinstance(summary_fragment.get("intake_status"), dict)
        else intake.get("intake_status")
        if isinstance(intake.get("intake_status"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or intake.get("safe_copy")
        or intake.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    status = _redact_route_task_rehearsal_text(
        intake_status.get("status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or intake.get("status")
        or intake.get("overall_status")
        or "not_proven"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status") or intake.get("overall_status") or status
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or intake.get("source")
        or intake_status.get("evidence_source")
        or ""
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or intake.get("safe_evidence_ref")
        or intake.get("evidence_ref", "")
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else intake.get("robot_diagnostics_summary")
        if isinstance(intake.get("robot_diagnostics_summary"), dict)
        else {}
    )
    safe_robot_summary = {
        "safe_copy": _redact_route_task_rehearsal_text(
            robot_summary.get("safe_copy") or safe_copy
        ),
        "safe_phone_copy": _redact_route_task_rehearsal_text(
            robot_summary.get("safe_phone_copy") or safe_copy
        ),
    }
    real_material_manifest_template, manifest_template_unsafe = (
        _safe_real_material_manifest_template_alias(intake, summary_fragment)
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or intake.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "intake_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    intake_status.get("reason")
                    or summary_fragment.get("reason")
                    or intake.get("reason")
                    or "real material evidence intake is software_proof only"
                ),
            },
            "safe_evidence_ref": safe_evidence_ref,
            "accepted_materials": _safe_pc_route_debug_value(
                summary_fragment.get("accepted_materials")
                if isinstance(summary_fragment.get("accepted_materials"), list)
                else []
            ),
            "missing_real_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_real_materials")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "real_material_manifest_template": real_material_manifest_template,
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "robot_diagnostics_summary": safe_robot_summary,
            "not_proven": _real_material_evidence_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    boundary_supported = source_boundary == REAL_MATERIAL_EVIDENCE_INTAKE_GATE
    if source_schema not in accepted_schemas or not boundary_supported:
        summary.update(
            {
                "status": "unsupported_schema",
                "intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "real_material_evidence_intake schema or evidence boundary is unsupported",
                },
                "safe_evidence_ref": "",
                "accepted_materials": [],
                "missing_real_materials": [],
                "rejected_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "real_material_manifest_template": {},
            }
        )
        return summary
    if raw_schema == REAL_MATERIAL_EVIDENCE_INTAKE_SCHEMA and not summary_fragment:
        summary.update(
            {
                "status": "blocked_missing_real_material_evidence_intake_summary",
                "intake_status": {
                    "status": "blocked_missing_real_material_evidence_intake_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "real_material_evidence_intake artifact is missing sanitized summary",
                },
                "safe_evidence_ref": "",
                "real_material_manifest_template": {},
            }
        )
        return summary

    # summary 必须显式保持软件证明和 false 控制位；任何 raw/credential/control/success 字段都降级。
    if (
        source_value != EVIDENCE_SOURCE_SOFTWARE
        or status != "not_proven"
        or overall_status != "not_proven"
        or _real_material_evidence_ref_is_unsafe(safe_evidence_ref)
        or intake.get("delivery_success") is not False
        or intake.get("primary_actions_enabled") is not False
        or intake.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or manifest_template_unsafe
        or _route_task_field_run_readiness_has_unsafe_fields(intake)
        or _route_task_field_run_readiness_has_unsafe_fields(summary_fragment)
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy)
        or _task_terminal_field_material_intake_copy_is_unsafe(
            safe_robot_summary.get("safe_copy", "")
        )
    ):
        blocked_copy = (
            "Real material evidence intake was blocked because the summary did not remain "
            "software_proof/not_proven with delivery_success=false, "
            "primary_actions_enabled=false, and safe_to_control=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_real_material_evidence_intake_summary",
                "intake_status": {
                    "status": "blocked_unsafe_real_material_evidence_intake_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "real_material_evidence_intake contains unsafe fields, success wording, weak evidence_ref, or control claims",
                },
                "safe_evidence_ref": "",
                "accepted_materials": [],
                "missing_real_materials": [],
                "rejected_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "real_material_manifest_template": {},
                "safe_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary


def summarize_real_material_followup_escalation_status(source):
    """构建真实材料 follow-up escalation status 的 summary-only Robot diagnostics 摘要。"""
    # 这里故意只读 sanitized summary；raw manifest/materials 即使存在也不能进入 Robot diagnostics。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_real_material_followup_escalation_status_summary(
        source_path,
        read_error="real_material_followup_escalation_status summary is not configured",
    )
    if isinstance(source, dict):
        followup = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "real_material_followup_escalation_status summary artifact missing"
            )
            summary["followup_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                followup = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading real_material_followup_escalation_status summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["followup_status"]["reason"] = safe_error
            return summary

    if not isinstance(followup, dict):
        summary["followup_status"]["reason"] = (
            "real_material_followup_escalation_status JSON must be an object"
        )
        return summary

    raw_schema = str(followup.get("schema") or "")
    source_schema, source_boundary = (
        _real_material_followup_escalation_status_source_contract(followup)
    )
    if raw_schema == REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA:
        summary_fragment = followup
    else:
        summary_fragment = {}
        for candidate in (
            followup.get("real_material_followup_escalation_status_summary"),
            followup.get(
                "robot_diagnostics_real_material_followup_escalation_status_summary"
            ),
            followup.get("diagnostics_summary"),
            followup.get("robot_diagnostics_summary"),
            followup.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if isinstance(summary_fragment, dict) and summary_fragment:
        nested_schema, nested_boundary = (
            _real_material_followup_escalation_status_source_contract(summary_fragment)
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    accepted_schemas = {
        REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
        REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
    }
    followup_status = (
        summary_fragment.get("followup_status")
        if isinstance(summary_fragment.get("followup_status"), dict)
        else summary_fragment.get("escalation_status")
        if isinstance(summary_fragment.get("escalation_status"), dict)
        else followup.get("followup_status")
        if isinstance(followup.get("followup_status"), dict)
        else followup.get("escalation_status")
        if isinstance(followup.get("escalation_status"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or followup.get("safe_copy")
        or followup.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    status = _redact_route_task_rehearsal_text(
        followup_status.get("status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or followup.get("status")
        or followup.get("overall_status")
        or "not_proven"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status") or followup.get("overall_status") or status
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or followup.get("source")
        or followup_status.get("evidence_source")
        or ""
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or followup.get("safe_evidence_ref")
        or followup.get("evidence_ref", "")
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else followup.get("robot_diagnostics_summary")
        if isinstance(followup.get("robot_diagnostics_summary"), dict)
        else {}
    )
    safe_robot_summary = {
        "safe_copy": _redact_route_task_rehearsal_text(
            robot_summary.get("safe_copy") or safe_copy
        ),
        "safe_phone_copy": _redact_route_task_rehearsal_text(
            robot_summary.get("safe_phone_copy") or safe_copy
        ),
    }
    material_groups_source = (
        summary_fragment.get("material_groups")
        if isinstance(summary_fragment.get("material_groups"), list)
        else []
    )
    rerun_status_summary_source = (
        summary_fragment.get("rerun_status_summary")
        if isinstance(summary_fragment.get("rerun_status_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or followup.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "followup_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    followup_status.get("reason")
                    or summary_fragment.get("reason")
                    or followup.get("reason")
                    or "real material follow-up escalation status is software_proof only"
                ),
            },
            "safe_evidence_ref": safe_evidence_ref,
            "material_group": _redact_route_task_rehearsal_text(
                summary_fragment.get("material_group") or followup.get("material_group") or ""
            ),
            "field_owner": _redact_route_task_rehearsal_text(
                summary_fragment.get("field_owner") or followup.get("field_owner") or ""
            ),
            "due_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("due_status") or followup.get("due_status") or ""
            ),
            "blocked_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocked_reason")
                or followup.get("blocked_reason")
                or followup_status.get("reason")
                or ""
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "escalation_level": _redact_route_task_rehearsal_text(
                summary_fragment.get("escalation_level")
                or followup.get("escalation_level")
                or ""
            ),
            "rerun_command": _redact_route_task_rehearsal_text(
                summary_fragment.get("rerun_command") or followup.get("rerun_command") or ""
            ),
            "rerun_status_summary": _safe_pc_route_debug_dict(
                rerun_status_summary_source
            ),
            "source_template_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_template_status")
                or followup.get("source_template_status")
                or ""
            ),
            "source_intake_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_intake_status")
                or followup.get("source_intake_status")
                or ""
            ),
            "review_route": _safe_route_task_rehearsal_list(
                summary_fragment.get("review_route")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "material_groups": _safe_pc_route_debug_value(material_groups_source),
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "robot_diagnostics_summary": safe_robot_summary,
            "not_proven": _real_material_followup_escalation_status_not_proven(
                followup,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    boundary_supported = source_boundary == REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE
    if source_schema not in accepted_schemas or not boundary_supported:
        summary.update(
            {
                "status": "unsupported_schema",
                "followup_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "real_material_followup_escalation_status schema or "
                        "evidence boundary is unsupported"
                    ),
                },
                "safe_evidence_ref": "",
                "material_groups": [],
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary
    if raw_schema == REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA and not summary_fragment:
        summary.update(
            {
                "status": "blocked_missing_real_material_followup_escalation_status_summary",
                "followup_status": {
                    "status": (
                        "blocked_missing_real_material_followup_escalation_status_summary"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "real_material_followup_escalation_status artifact is "
                        "missing sanitized summary"
                    ),
                },
                "safe_evidence_ref": "",
                "material_groups": [],
            }
        )
        return summary

    # 任一成功/控制/raw 材料线索都降级；rerun_command 只是人工重跑提示，不得进入命令通路。
    if (
        source_value != EVIDENCE_SOURCE_SOFTWARE
        or status != "not_proven"
        or overall_status != "not_proven"
        or _real_material_evidence_ref_is_unsafe(safe_evidence_ref)
        or followup.get("delivery_success") is not False
        or followup.get("primary_actions_enabled") is not False
        or followup.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _real_material_followup_escalation_status_has_unsafe_fields(followup)
        or _real_material_followup_escalation_status_has_unsafe_fields(summary_fragment)
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy)
        or _task_terminal_field_material_intake_copy_is_unsafe(
            safe_robot_summary.get("safe_copy", "")
        )
    ):
        blocked_copy = (
            "Real material follow-up escalation status was blocked because the "
            "summary did not remain software_proof/not_proven with "
            "delivery_success=false, primary_actions_enabled=false, and "
            "safe_to_control=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_real_material_followup_escalation_status_summary",
                "followup_status": {
                    "status": (
                        "blocked_unsafe_real_material_followup_escalation_status_summary"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "real_material_followup_escalation_status contains unsafe "
                        "fields, success wording, weak evidence_ref, or control claims"
                    ),
                },
                "safe_evidence_ref": "",
                "material_groups": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_command": "",
                "rerun_status_summary": {},
                "safe_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

