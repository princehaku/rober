import json
import os
import re

from ros2_trashbot_behavior.operator_gateway_http import normalize_elevator_assist, status_payload
from ros2_trashbot_behavior.remote_cloud_relay import (
    build_phone_credential_rotation_summary,
    build_phone_network_recovery_summary,
    build_phone_oss_cdn_manifest_summary,
    build_phone_production_store_queue_summary,
    build_phone_production_recovery_summary,
    build_phone_provisioning_audit_summary,
    build_phone_queue_ordering_drill_summary,
    build_phone_transaction_isolation_summary,
)

# Diagnostics must stay available even when the optional vision package is not
# installed in a minimal operator-gateway environment.
try:
    from ros2_trashbot_vision.vision_sample_manifest import summarize_manifest
except ImportError:
    summarize_manifest = None


REVIEW_QUEUE_LIMIT = 5
LOW_CONFIDENCE_REVIEW_THRESHOLD = 75
HARDWARE_PROOF_STATUSES = {"software_proof", "needs_hil", "invalid_config", "read_error"}
EVIDENCE_SOURCE_SOFTWARE = "software_proof"
EVIDENCE_SOURCE_HIL = "hil_pass"
VALID_EVIDENCE_SOURCES = {EVIDENCE_SOURCE_SOFTWARE, EVIDENCE_SOURCE_HIL}
REVIEW_DECISION_VALUES = {"approved", "rejected", "needs_retry"}
REVIEW_DECISION_ORDER = ("approved", "rejected", "needs_retry")
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
ROUTE_TASK_REHEARSAL_SCHEMA = "trashbot.route_task_rehearsal_artifact"
ROUTE_TASK_REHEARSAL_DIAGNOSTICS_SCHEMA = "trashbot.route_task_rehearsal_diagnostics_summary.v1"
ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_SCHEMA = "trashbot.route_task_rehearsal_execution_bundle"
ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_SUMMARY_SCHEMA = (
    "trashbot.route_task_rehearsal_execution_bundle_summary.v1"
)
ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_SCHEMA = "trashbot.route_task_rehearsal_operator_review.v1"
ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_SUMMARY_SCHEMA = (
    "trashbot.route_task_rehearsal_operator_review_summary.v1"
)
ROUTE_TASK_REHEARSAL_ARTIFACT_GATE = "software_proof_docker_route_task_rehearsal_artifact_gate"
ROUTE_TASK_REHEARSAL_DIAGNOSTICS_GATE = "software_proof_docker_route_task_rehearsal_diagnostics_gate"
ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_GATE = (
    "software_proof_docker_route_task_rehearsal_execution_bundle_gate"
)
ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_GATE = (
    "software_proof_docker_route_task_rehearsal_operator_review_gate"
)
PC_ROUTE_DEBUG_CONSOLE_SCHEMA = "trashbot.pc_route_debug_console.v1"
PC_ROUTE_DEBUG_CONSOLE_SUMMARY_SCHEMA = "trashbot.pc_route_debug_console_summary.v1"
PC_ROUTE_DEBUG_CONSOLE_GATE = "software_proof_docker_pc_route_debug_console_gate"
PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_SUMMARY_SCHEMA = (
    "trashbot.pc_route_elevator_console_integration_summary.v1"
)
PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_GATE = (
    "software_proof_docker_pc_route_elevator_console_integration_gate"
)
ROUTE_TASK_FIELD_RUN_READINESS_SCHEMA = "trashbot.route_task_field_run_readiness.v1"
ROUTE_TASK_FIELD_RUN_READINESS_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_readiness_summary.v1"
)
ROUTE_TASK_FIELD_RUN_READINESS_GATE = (
    "software_proof_docker_route_task_field_run_readiness_gate"
)
ROUTE_TASK_FIELD_RUN_INTAKE_SCHEMA = "trashbot.route_task_field_run_intake_crosscheck.v1"
ROUTE_TASK_FIELD_RUN_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_intake_summary.v1"
)
ROUTE_TASK_FIELD_RUN_INTAKE_GATE = (
    "software_proof_docker_route_task_field_run_intake_crosscheck_gate"
)
ROUTE_TASK_FIELD_RUN_REVIEW_SCHEMA = "trashbot.route_task_field_run_review_console.v1"
ROUTE_TASK_FIELD_RUN_REVIEW_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_review_summary.v1"
)
ROUTE_TASK_FIELD_RUN_REVIEW_GATE = (
    "software_proof_docker_route_task_field_run_review_console_gate"
)
ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_SCHEMA = "trashbot.route_task_field_run_execution_pack.v1"
ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_execution_pack_summary.v1"
)
ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_GATE = (
    "software_proof_docker_route_task_field_run_execution_pack_gate"
)
ROUTE_TASK_FIELD_RUN_RECONCILIATION_SCHEMA = "trashbot.route_task_field_run_reconciliation.v1"
ROUTE_TASK_FIELD_RUN_RECONCILIATION_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_reconciliation_summary.v1"
)
ROUTE_TASK_FIELD_RUN_RECONCILIATION_GATE = (
    "software_proof_docker_route_task_field_run_reconciliation_gate"
)
ROUTE_TASK_COMPLETION_SIGNAL_SCHEMA = "trashbot.route_task_completion_signal.v1"
ROUTE_TASK_COMPLETION_SIGNAL_SUMMARY_SCHEMA = (
    "trashbot.route_task_completion_signal_summary.v1"
)
ROUTE_TASK_COMPLETION_SIGNAL_GATE = (
    "software_proof_docker_route_task_completion_signal_gate"
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
ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SCHEMA = (
    "trashbot.elevator_route_evidence_reconciliation.v1"
)
ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY_SCHEMA = (
    "trashbot.elevator_route_evidence_reconciliation_summary.v1"
)
ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_GATE = (
    "software_proof_docker_elevator_route_evidence_reconciliation_gate"
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
ROUTE_TASK_REHEARSAL_REQUIRED_NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "wave_rover_motion",
    "real_serial_or_uart_feedback",
    "real_hil_pass",
    "delivery_success",
)
ROUTE_TASK_REHEARSAL_TEXT_REDACTIONS = (
    (re.compile(r"(?i)\bAuthorization\s*:\s*(?:Bearer\s+)?[^,\s]+"), "[REDACTED_AUTH_HEADER]"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\b(oss[_-]?secret|access[_-]?key[_-]?secret|ak|sk|root[_-]?password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_SERIAL]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_BAUD]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?<![\w:])(?:~|/Users|/tmp|/var|/private|/ws|/home|/root)/[^\s,;}\\\"]+"), "[REDACTED_LOCAL_PATH]"),
)


def _redact_route_task_rehearsal_text(value):
    text = str(value or "")
    for pattern, replacement in ROUTE_TASK_REHEARSAL_TEXT_REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def _safe_route_task_rehearsal_ref(value):
    text = str(value or "").strip()
    if not text:
        return ""
    redacted = _redact_route_task_rehearsal_text(text)
    if "[REDACTED_LOCAL_PATH]" in redacted:
        basename = os.path.basename(os.path.expanduser(text).rstrip(os.sep)) or "artifact"
        return f"local_path_redacted:{basename}"
    return redacted


def _safe_route_task_rehearsal_list(value, limit=8):
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        items.append(_redact_route_task_rehearsal_text(item))
        if len(items) >= limit:
            break
    return items


def _route_task_rehearsal_not_proven(artifact=None):
    artifact = artifact if isinstance(artifact, dict) else {}
    values = []
    source_values = artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else []
    for item in list(source_values) + list(ROUTE_TASK_REHEARSAL_REQUIRED_NOT_PROVEN):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _pc_route_debug_not_proven(console=None):
    # PC 调试台只能提供软件侧可读性材料，真实路线、硬件和交付结论必须显式保持未证明。
    console = console if isinstance(console, dict) else {}
    values = []
    source_values = console.get("not_proven") if isinstance(console.get("not_proven"), list) else []
    required = (
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_or_cancel_completion",
        "delivery_success",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _pc_route_elevator_reconciliation_not_proven(reconciliation=None):
    # PC console 的电梯/路线对账只保留软件侧嵌套摘要；动作面和真实交付证据必须继续外部采集。
    reconciliation = reconciliation if isinstance(reconciliation, dict) else {}
    values = []
    source_values = (
        reconciliation.get("not_proven") if isinstance(reconciliation.get("not_proven"), list) else []
    )
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "terminal_ack",
        "cursor_advance_or_persistence",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "real_elevator_operation",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_or_cancel_completion",
        "delivery_success",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _route_task_field_run_readiness_not_proven(readiness=None):
    # field-run readiness 只做下一次上车前材料交接，真实路线、HIL 和交付结论必须始终保留未证明项。
    readiness = readiness if isinstance(readiness, dict) else {}
    values = []
    source_values = readiness.get("not_proven") if isinstance(readiness.get("not_proven"), list) else []
    required = (
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_or_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _route_task_field_run_intake_not_proven(intake=None):
    # intake/crosscheck 只证明材料接收和同 evidence_ref 软件复核；真实运行结论必须单独采集。
    intake = intake if isinstance(intake, dict) else {}
    values = []
    source_values = intake.get("not_proven") if isinstance(intake.get("not_proven"), list) else []
    required = (
        "collect_dropoff_cancel_control",
        "ack_post",
        "cursor_advance_or_persistence",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_or_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _route_task_field_run_review_not_proven(review=None, phone_summary=None):
    # review console 是人工复核摘要，不参与控制面；所有真实动作、ACK、HIL 和交付结论都必须保留未证明。
    review = review if isinstance(review, dict) else {}
    phone_summary = phone_summary if isinstance(phone_summary, dict) else {}
    values = []
    source_values = []
    if isinstance(review.get("not_proven"), list):
        source_values.extend(review.get("not_proven"))
    if isinstance(phone_summary.get("not_proven"), list):
        source_values.extend(phone_summary.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "ack_post",
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


def _route_task_field_run_execution_pack_not_proven(pack=None, phone_summary=None):
    # execution pack 只把现场执行包的材料状态投到 diagnostics；控制面、ACK、HIL 和交付结论都必须显式未证明。
    pack = pack if isinstance(pack, dict) else {}
    phone_summary = phone_summary if isinstance(phone_summary, dict) else {}
    values = []
    source_values = []
    if isinstance(pack.get("not_proven"), list):
        source_values.extend(pack.get("not_proven"))
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
        "dropoff_or_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _elevator_route_evidence_reconciliation_not_proven(reconciliation=None, summary_fragment=None):
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


def _first_route_task_rehearsal_value(*values):
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _default_route_task_rehearsal_summary(path, state="not_configured", read_error=""):
    # diagnostics 只读消费 artifact；默认状态必须保守，不能把缺文件解释成路线或任务通过。
    return {
        "schema": ROUTE_TASK_REHEARSAL_DIAGNOSTICS_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_REHEARSAL_DIAGNOSTICS_GATE,
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "artifact_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "crosscheck_status": {
            "status": "",
            "scope": "status/replay/task_record software alignment only",
            "software_mismatch_count": 0,
            "software_mismatches": [],
        },
        "hil_alignment_status": {
            "status": "",
            "alignment_status": "not_proven",
            "evidence_ref_match": False,
            "not_real_hil_when_status_is_missing_blocked_or_software_proof": True,
            "detail": "not real HIL; route/task rehearsal diagnostics were not configured",
            "mismatch_count": 0,
        },
        "not_proven": _route_task_rehearsal_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_phone_copy": "Route/task rehearsal diagnostics are not configured; this is not delivery success.",
        "next_step": "Attach a route/task rehearsal artifact from evidence_crosscheck before using diagnostics for route/task replay support.",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _default_pc_route_debug_console_summary(path, state="not_configured", read_error=""):
    # diagnostics 默认 fail-closed：没配置 PC console artifact 时不能推断路线可用或控制可执行。
    return {
        "schema": PC_ROUTE_DEBUG_CONSOLE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PC_ROUTE_DEBUG_CONSOLE_GATE,
        "overall_status": "blocked",
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "console_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "availability": {
            "status": "blocked",
            "reason": "pc route debug console summary is not configured",
        },
        "route_debug_status": {
            "status": "not_proven",
            "current_checkpoint": "",
            "target": "",
            "matching_status": "",
            "failure_reason": "",
        },
        "route_progress": {},
        "keyframe_preflight": {},
        "recent_task_summary": {},
        "route_elevator_reconciliation": _default_pc_route_elevator_reconciliation_summary(),
        "not_proven": _pc_route_debug_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "PC route debug console is not configured; this is not delivery success.",
        "safe_phone_copy": "PC route debug console is not configured; this is not delivery success.",
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
    }


def _default_pc_route_elevator_reconciliation_summary(state="not_configured", read_error=""):
    # 嵌套 summary 有自己的软件证明边界，但不能提升父级 PC console 的控制能力。
    return {
        "schema": PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_GATE,
        "overall_status": "blocked",
        "state": state,
        "source_evidence_boundary": "",
        "availability": {
            "status": "blocked",
            "reason": "route elevator reconciliation summary is not configured",
        },
        "reconciliation_status": {
            "status": "not_proven",
            "reason": read_error or "route elevator reconciliation summary is not configured",
        },
        "elevator_assist_status": {},
        "route_completion_status": {},
        "operator_next_steps": [],
        "not_proven": _pc_route_elevator_reconciliation_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route elevator reconciliation is not configured; this is not delivery success.",
        "safe_phone_copy": "Route elevator reconciliation is not configured; this is not delivery success.",
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
    }


def _default_route_task_field_run_readiness_summary(path, state="not_configured", read_error=""):
    # readiness artifact 不是控制面状态；默认 blocked 防止缺配置时被手机端误读为可执行路线任务。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_READINESS_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_READINESS_GATE,
        "overall_status": "blocked",
        "availability": {
            "status": "blocked",
            "reason": "route-task field-run readiness artifact is not configured",
        },
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "readiness_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "next_evidence": {
            "summary": "Attach the route-task field-run readiness handoff before planning a real run.",
            "missing_materials": [],
            "required_field_run_materials": [],
        },
        "commands_summary": [],
        "not_proven": _route_task_field_run_readiness_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field-run readiness is not configured; this is metadata-only and not delivery success.",
        "safe_phone_copy": "Route-task field-run readiness is not configured; this is metadata-only and not delivery success.",
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_run_intake_summary(path, state="not_configured", read_error=""):
    # intake/crosscheck 只能作为 diagnostics 元数据；默认 blocked，避免缺 artifact 时误放行手机控制。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_INTAKE_GATE,
        "overall_status": "blocked",
        "availability": {
            "status": "blocked",
            "reason": "route-task field-run intake artifact is not configured",
        },
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "intake_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "crosscheck": {
            "status": "not_proven",
            "missing_materials": [],
            "mismatch_reasons": [],
            "commands_to_rerun": [],
        },
        "not_proven": _route_task_field_run_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field-run intake is not configured; this is metadata-only and not delivery success.",
        "safe_phone_copy": "Route-task field-run intake is not configured; this is metadata-only and not delivery success.",
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_run_review_summary(path, state="not_configured", read_error=""):
    # review console 只把 Autonomy 产出的人工复核报告变成 diagnostics 摘要；默认必须保持控制面全关。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_REVIEW_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_REVIEW_GATE,
        "overall_status": "blocked",
        "availability": {
            "status": "blocked",
            "reason": "route-task field-run review report is not configured",
        },
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "review_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "review": {
            "decision": "not_proven",
            "missing_materials": [],
            "mismatch_reasons": [],
            "commands_to_rerun": [],
            "operator_next_steps": [],
        },
        "phone_safe_summary": {},
        "not_proven": _route_task_field_run_review_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field-run review is not configured; this is metadata-only and not delivery success.",
        "safe_phone_copy": "Route-task field-run review is not configured; this is metadata-only and not delivery success.",
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


def _default_route_task_field_run_execution_pack_summary(path, status="not_configured", read_error=""):
    # execution pack 是现场执行材料的只读摘要，不暴露 artifact 路径，避免 diagnostics 被误当成执行入口。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_GATE,
        "status": status,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "materials_status": {
            "status": "blocked",
            "reason": "route-task field-run execution pack is not configured",
        },
        "command_summary": [],
        "not_proven": _route_task_field_run_execution_pack_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field-run execution pack is metadata-only; not delivery success.",
        "safe_phone_copy": "Route-task field-run execution pack is metadata-only; not delivery success.",
        "metadata_only": True,
    }


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


def _default_elevator_route_evidence_reconciliation_summary(path, status="not_configured", read_error=""):
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


def _default_route_elevator_field_session_handoff_summary(path, status="not_configured", read_error=""):
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


def _safe_pc_route_debug_value(value, depth=0):
    # 递归脱敏只保留支撑人员可读摘要；深层或大列表会截断，避免把完整 artifact 泄露给 phone/support。
    if depth > 3:
        return "[REDACTED_NESTED_VALUE]"
    if isinstance(value, dict):
        safe = {}
        for key, item in list(value.items())[:20]:
            safe_key = _redact_route_task_rehearsal_text(key)
            safe[safe_key] = _safe_pc_route_debug_value(item, depth=depth + 1)
        return safe
    if isinstance(value, list):
        return [_safe_pc_route_debug_value(item, depth=depth + 1) for item in value[:8]]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _redact_route_task_rehearsal_text(value)


def _safe_pc_route_debug_dict(value):
    return _safe_pc_route_debug_value(value if isinstance(value, dict) else {})


def _route_task_field_run_readiness_has_unsafe_fields(value, key_path=""):
    # source artifact 可能来自人工拷贝；一旦出现控制/凭证/硬件 raw 字段或成功布尔值，整份 summary 降级。
    unsafe_key_fragments = (
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "credential",
        "checksum",
        "traceback",
        "raw_artifact",
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
        "dropoff_completion",
        "cancel_completion",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            nested_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _route_task_field_run_readiness_has_unsafe_fields(item, nested_path):
                return True
        return False
    if isinstance(value, list):
        return any(_route_task_field_run_readiness_has_unsafe_fields(item, key_path) for item in value)
    if isinstance(value, str):
        redacted = _redact_route_task_rehearsal_text(value)
        return any(marker in redacted for marker in (
            "[REDACTED_AUTH_HEADER]",
            "Bearer [REDACTED]",
            "[REDACTED_URL]",
            "/dev/[REDACTED_SERIAL]",
            "[REDACTED_BAUD]",
            "[REDACTED_TRACEBACK]",
            "[REDACTED_LOCAL_PATH]",
        ))
    return False


def _route_task_field_run_readiness_copy_is_unsafe(value):
    # 支持 copy 可以说 blocked/not_proven，但不能暗示控制动作、HIL 或交付成功已经发生。
    text = _redact_route_task_rehearsal_text(value).strip().lower()
    if not text:
        return True
    guarded_phrases = (
        "not delivery success",
        "not a delivery success",
        "no delivery success",
        "never delivery success",
        "not real hil",
        "not hil",
        "not a hil",
        "not proven",
        "not_proven",
        "metadata-only",
        "must not",
    )
    unsafe_phrases = (
        "delivery success",
        "hil pass",
        "real hil",
        "start delivery enabled",
        "confirm dropoff enabled",
        "cancel enabled",
        "ack posted",
        "cursor advanced",
        "nav2 started",
        "dropoff complete",
        "cancel complete",
    )
    guarded_text = text
    for guard in guarded_phrases:
        guarded_text = guarded_text.replace(guard, "")
    for phrase in unsafe_phrases:
        if phrase in guarded_text:
            return True
    return False


def _route_task_field_run_intake_has_unsafe_control_claims(value):
    # raw 材料可能存在于 source artifact 中，但 diagnostics 只白名单读取摘要；真实控制成功布尔值必须拦截。
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
        "dropoff_completion",
        "cancel_completion",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text in unsafe_true_keys and bool(item):
                return True
            if _route_task_field_run_intake_has_unsafe_control_claims(item):
                return True
        return False
    if isinstance(value, list):
        return any(_route_task_field_run_intake_has_unsafe_control_claims(item) for item in value)
    return False


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


def _elevator_route_evidence_reconciliation_source_contract(value):
    # 允许直接 artifact 或 summary wrapper；wrapper 必须保留原始 schema/boundary，防止把别的 gate 混入。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or "")
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _route_elevator_field_session_handoff_source_contract(value):
    # 支持直接 artifact 和已生成 summary；两者都必须停留在同一个 handoff gate，不能混用旧 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
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


def _pc_route_debug_safe_copy_is_unsafe(value):
    # 支持 copy 允许解释“未证明”，但不能暗示 Start/ACK/HIL/交付已经成立。
    text = _redact_route_task_rehearsal_text(value).strip().lower()
    if not text:
        return True
    guarded_phrases = (
        "not delivery success",
        "not a delivery success",
        "no delivery success",
        "never delivery success",
        "not real hil",
        "not hil",
        "not a hil",
        "not start",
        "not confirm",
        "not cancel",
        "must not",
        "metadata-only",
    )
    unsafe_phrases = (
        "delivery success",
        "hil pass",
        "real hil",
        "start delivery enabled",
        "confirm dropoff enabled",
        "cancel enabled",
        "ack posted",
        "cursor advanced",
        "nav2 started",
        "dropoff complete",
        "cancel complete",
    )
    guarded_text = text
    for guard in guarded_phrases:
        guarded_text = guarded_text.replace(guard, "")
    for phrase in unsafe_phrases:
        if phrase in guarded_text:
            return True
    return False


def _pc_route_elevator_reconciliation_has_unsafe_control_claims(value):
    # 嵌套对账摘要来自 PC console artifact，任何成功/控制布尔为真都必须让嵌套摘要 fail-closed。
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "nav2_triggered",
        "hil_pass",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "dropoff_completion",
        "cancel_completion",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text in unsafe_true_keys and bool(item):
                return True
            if _pc_route_elevator_reconciliation_has_unsafe_control_claims(item):
                return True
        return False
    if isinstance(value, list):
        return any(_pc_route_elevator_reconciliation_has_unsafe_control_claims(item) for item in value)
    return False


def _pc_route_elevator_reconciliation_safe_copy_is_unsafe(value):
    # 与父级 PC console copy 一致：允许说明 metadata-only，不允许暗示 ACK、Nav2、HIL 或交付成功。
    return _pc_route_debug_safe_copy_is_unsafe(value)


def _summarize_pc_route_elevator_reconciliation(value, source_boundary):
    """把 PC console 内嵌 route/elevator 对账片段收敛成只读、fail-closed summary。"""
    summary = _default_pc_route_elevator_reconciliation_summary(
        read_error="route elevator reconciliation summary is not configured",
    )
    if not isinstance(value, dict):
        return summary

    safe_copy = _redact_route_task_rehearsal_text(
        value.get("safe_copy")
        or value.get("safe_phone_copy")
        or "Route elevator reconciliation is metadata-only; not delivery success."
    )
    nested_boundary = str(value.get("evidence_boundary") or PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_GATE)
    availability = value.get("availability") if isinstance(value.get("availability"), dict) else {}
    reconciliation_status = (
        value.get("reconciliation_status")
        if isinstance(value.get("reconciliation_status"), dict)
        else {}
    )
    status_text = str(
        reconciliation_status.get("status")
        or availability.get("status")
        or value.get("status")
        or ""
    ).strip().lower()
    summary.update(
        {
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "availability": _safe_pc_route_debug_dict(availability),
            "reconciliation_status": _safe_pc_route_debug_dict(reconciliation_status),
            "elevator_assist_status": _safe_pc_route_debug_dict(value.get("elevator_assist_status")),
            "route_completion_status": _safe_pc_route_debug_dict(value.get("route_completion_status")),
            "operator_next_steps": _safe_route_task_rehearsal_list(value.get("operator_next_steps")),
            "not_proven": _pc_route_elevator_reconciliation_not_proven(value),
            "read_error": "",
        }
    )
    if nested_boundary != PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_boundary",
                "read_error": "route elevator reconciliation evidence boundary is unsupported",
                "availability": {
                    "status": "blocked",
                    "reason": "unsupported route elevator reconciliation boundary",
                },
                "safe_copy": "Route elevator reconciliation source boundary is unsupported; no delivery result is proven.",
                "safe_phone_copy": "Route elevator reconciliation source boundary is unsupported; no delivery result is proven.",
            }
        )
        return summary

    if (
        _pc_route_elevator_reconciliation_has_unsafe_control_claims(value)
        or _pc_route_elevator_reconciliation_safe_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_fields",
                "read_error": "route elevator reconciliation contains unsafe control or success claims",
                "availability": {
                    "status": "blocked",
                    "reason": "unsafe route elevator reconciliation fields",
                },
                "safe_copy": "Route elevator reconciliation was blocked because it could imply control or delivery success.",
                "safe_phone_copy": "Route elevator reconciliation was blocked because it could imply control or delivery success.",
            }
        )
        return summary

    summary["safe_copy"] = safe_copy
    summary["safe_phone_copy"] = safe_copy
    blocked_statuses = {"", "blocked", "missing", "read_error", "unsupported_schema", "unsafe_copy", "unsafe_fields"}
    if status_text in blocked_statuses:
        summary.update(
            {
                "overall_status": "blocked",
                "state": status_text or "blocked",
            }
        )
        return summary

    summary.update(
        {
            "overall_status": "degraded",
            "state": "available",
        }
    )
    return summary


def _default_route_task_rehearsal_execution_bundle_summary(path, state="not_configured", read_error=""):
    # bundle 是比旧 artifact 更上层的只读 manifest；默认必须 fail-closed，避免 diagnostics 被误当成控制入口。
    return {
        "schema": ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_GATE,
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "bundle_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "artifact_ref": "",
        "artifact_state": "",
        "crosscheck_status": {
            "status": "",
            "scope": "status/replay/task_record software alignment only",
            "software_mismatch_count": 0,
            "software_mismatches": [],
        },
        "hil_alignment_status": {
            "status": "",
            "alignment_status": "not_proven",
            "evidence_ref_match": False,
            "not_real_hil_when_status_is_missing_blocked_or_software_proof": True,
            "detail": "not real HIL; route/task rehearsal execution bundle was not configured",
            "mismatch_count": 0,
        },
        "not_proven": _route_task_rehearsal_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_phone_copy": "Route/task rehearsal execution bundle is not configured; this is not delivery success.",
        "next_step": "Attach a route/task rehearsal execution bundle manifest before using diagnostics for execution rehearsal support.",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
    }


def _default_route_task_rehearsal_operator_review_summary(path, state="not_configured", read_error=""):
    # review package 面向人工复核和手机支持，只能作为 diagnostics metadata，不能触发机器人动作。
    return {
        "schema": ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_GATE,
        "overall_status": "blocked",
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "review_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "crosscheck_status": {
            "status": "",
            "scope": "status/replay/task_record software alignment only",
            "software_mismatch_count": 0,
        },
        "hil_alignment_status": {
            "status": "",
            "alignment_status": "not_proven",
            "evidence_ref_match": False,
            "not_real_hil_when_status_is_missing_blocked_or_software_proof": True,
        },
        "mismatch_summary": {
            "software_mismatch_count": 0,
            "hil_mismatch_count": 0,
            "items": [],
        },
        "next_rehearsal_decision": "attach_route_task_rehearsal_operator_review",
        "not_proven": _route_task_rehearsal_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route/task rehearsal operator review is not configured; this is not delivery success.",
        "safe_phone_copy": "Route/task rehearsal operator review is not configured; this is not delivery success.",
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
    }


def _route_task_rehearsal_review_dict(*values):
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def _route_task_rehearsal_review_safe_copy_is_unsafe(value):
    # 手机端 copy 允许说“不是成功”，但不能把 review package 包装成动作、ACK 或真实 HIL 结论。
    text = _redact_route_task_rehearsal_text(value).strip().lower()
    if not text:
        return True
    guarded_phrases = (
        "not delivery success",
        "not a delivery success",
        "no delivery success",
        "never delivery success",
        "not real hil",
        "not hil",
        "not a hil",
        "not start",
        "not confirm",
        "not cancel",
        "must not",
    )
    unsafe_phrases = (
        "delivery success",
        "hil pass",
        "real hil",
        "start delivery enabled",
        "confirm dropoff enabled",
        "cancel enabled",
        "ack posted",
        "dropoff complete",
        "cancel complete",
    )
    guarded_text = text
    for guard in guarded_phrases:
        guarded_text = guarded_text.replace(guard, "")
    for phrase in unsafe_phrases:
        if phrase in guarded_text:
            return True
    return False


def _route_task_rehearsal_review_mismatch_summary(review, crosscheck, hil_alignment):
    source = review.get("mismatch_summary") if isinstance(review.get("mismatch_summary"), dict) else {}
    software_mismatches = crosscheck.get("software_mismatches")
    hil_mismatches = hil_alignment.get("mismatches")
    source_items = source.get("items") if isinstance(source.get("items"), list) else []
    items = source_items or (software_mismatches if isinstance(software_mismatches, list) else [])
    return {
        "software_mismatch_count": safe_int(
            source.get("software_mismatch_count"),
            default=len(software_mismatches) if isinstance(software_mismatches, list) else 0,
        ),
        "hil_mismatch_count": safe_int(
            source.get("hil_mismatch_count"),
            default=len(hil_mismatches) if isinstance(hil_mismatches, list) else 0,
        ),
        "items": _safe_route_task_rehearsal_list(items),
    }


def summarize_route_task_rehearsal_artifact(path):
    """构建只读、phone-safe 的 route/task rehearsal diagnostics summary。"""
    artifact_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_rehearsal_summary(
        artifact_path,
        read_error="route/task rehearsal artifact is not configured",
    )
    if not artifact_path:
        return summary
    if not os.path.exists(artifact_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route/task rehearsal artifact not found",
                "safe_phone_copy": "Route/task rehearsal artifact is missing; this is not delivery success.",
                "next_step": "Regenerate the route/task rehearsal artifact, then reopen diagnostics.",
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(artifact_path, "r", encoding="utf-8") as f:
            artifact = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(f"failed reading route/task rehearsal artifact: {exc}"),
                "safe_phone_copy": "Route/task rehearsal artifact could not be read; keep treating route/task proof as not_proven.",
                "next_step": "Fix the artifact JSON and rerun the diagnostics summary.",
            }
        )
        return summary

    if not isinstance(artifact, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route/task rehearsal artifact JSON must be an object",
                "safe_phone_copy": "Route/task rehearsal artifact shape is invalid; route/task proof remains not_proven.",
                "next_step": "Regenerate a JSON object artifact from evidence_crosscheck.",
            }
        )
        return summary

    source_schema = str(artifact.get("schema") or "")
    source_boundary = str(artifact.get("evidence_boundary") or "")
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": artifact.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "evidence_ref": _safe_route_task_rehearsal_ref(artifact.get("evidence_ref", "")),
            "not_proven": _route_task_rehearsal_not_proven(artifact),
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_REHEARSAL_SCHEMA or source_boundary != ROUTE_TASK_REHEARSAL_ARTIFACT_GATE:
        summary.update(
            {
                "state": "unsupported_schema",
                "read_error": "route/task rehearsal artifact schema or evidence boundary is unsupported",
                "safe_phone_copy": "Route/task rehearsal artifact is not a supported diagnostics source; no delivery result is proven.",
                "next_step": "Regenerate the artifact with the supported route/task rehearsal schema and boundary.",
            }
        )
        return summary

    crosscheck = artifact.get("crosscheck_status") if isinstance(artifact.get("crosscheck_status"), dict) else {}
    hil_alignment = artifact.get("hil_alignment_status") if isinstance(artifact.get("hil_alignment_status"), dict) else {}
    crosscheck_status = str(crosscheck.get("status") or "").strip().lower()
    software_mismatches = crosscheck.get("software_mismatches")
    hil_mismatches = hil_alignment.get("mismatches")
    summary["crosscheck_status"] = {
        "status": _redact_route_task_rehearsal_text(crosscheck_status),
        "scope": _redact_route_task_rehearsal_text(
            crosscheck.get("scope") or "status/replay/task_record software alignment only"
        ),
        "software_mismatch_count": len(software_mismatches) if isinstance(software_mismatches, list) else 0,
        "software_mismatches": _safe_route_task_rehearsal_list(software_mismatches),
    }
    alignment_status = str(hil_alignment.get("alignment_status") or "not_proven").strip()
    summary["hil_alignment_status"] = {
        "status": _redact_route_task_rehearsal_text(hil_alignment.get("status", "")),
        "alignment_status": _redact_route_task_rehearsal_text(alignment_status or "not_proven"),
        "evidence_ref_match": bool(hil_alignment.get("evidence_ref_match", False)),
        "not_real_hil_when_status_is_missing_blocked_or_software_proof": bool(
            hil_alignment.get("not_real_hil_when_status_is_missing_blocked_or_software_proof", True)
        ),
        "detail": _redact_route_task_rehearsal_text(
            hil_alignment.get("detail") or "not real HIL; route/task rehearsal remains software proof"
        ),
        "mismatch_count": len(hil_mismatches) if isinstance(hil_mismatches, list) else 0,
    }

    if crosscheck_status == "pass":
        summary.update(
            {
                "state": "crosscheck_pass",
                "safe_phone_copy": "Route/task rehearsal crosscheck passed as Docker/local software proof only; it is not delivery success.",
                "next_step": "Use the shared evidence_ref for support/replay, then collect real Nav2/fixed-route and HIL evidence before claiming delivery.",
            }
        )
        return summary
    if crosscheck_status == "fail":
        summary.update(
            {
                "state": "crosscheck_fail",
                "safe_phone_copy": "Route/task rehearsal crosscheck failed; keep route/task proof blocked and not_proven.",
                "next_step": "Inspect the sanitized software mismatches, fix the source artifact, and rerun evidence_crosscheck.",
            }
        )
        return summary

    summary.update(
        {
            "state": "unsupported_status",
            "read_error": "route/task rehearsal artifact crosscheck status is missing or unsupported",
            "safe_phone_copy": "Route/task rehearsal artifact has no supported crosscheck result; no route or delivery pass is proven.",
            "next_step": "Regenerate the artifact with crosscheck_status.status pass or fail.",
        }
    )
    return summary


def summarize_route_task_rehearsal_operator_review(path):
    """构建只读、phone/support-safe 的 operator review package 摘要。"""
    review_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_rehearsal_operator_review_summary(
        review_path,
        read_error="route/task rehearsal operator review package is not configured",
    )
    if not review_path:
        return summary
    if not os.path.exists(review_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route/task rehearsal operator review package not found",
                "safe_copy": "Route/task rehearsal operator review is missing; this is not delivery success.",
                "safe_phone_copy": "Route/task rehearsal operator review is missing; this is not delivery success.",
                "next_rehearsal_decision": "regenerate_operator_review_package",
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(review_path, "r", encoding="utf-8") as f:
            review = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading route/task rehearsal operator review package: {exc}"
                ),
                "safe_copy": "Route/task rehearsal operator review could not be read; keep proof blocked.",
                "safe_phone_copy": "Route/task rehearsal operator review could not be read; keep proof blocked.",
                "next_rehearsal_decision": "fix_operator_review_json",
            }
        )
        return summary

    if not isinstance(review, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route/task rehearsal operator review JSON must be an object",
                "safe_copy": "Route/task rehearsal operator review shape is invalid; proof remains blocked.",
                "safe_phone_copy": "Route/task rehearsal operator review shape is invalid; proof remains blocked.",
                "next_rehearsal_decision": "regenerate_operator_review_json_object",
            }
        )
        return summary

    source_schema = str(review.get("schema") or "")
    source_boundary = str(review.get("evidence_boundary") or "")
    crosscheck = _route_task_rehearsal_review_dict(
        review.get("crosscheck_status"),
        review.get("crosscheck"),
    )
    hil_alignment = _route_task_rehearsal_review_dict(
        review.get("hil_alignment_status"),
        review.get("hil_alignment"),
    )
    crosscheck_status = str(crosscheck.get("status") or "").strip().lower()
    safe_copy = _redact_route_task_rehearsal_text(
        review.get("safe_copy") or review.get("safe_phone_copy") or ""
    )
    next_decision = _redact_route_task_rehearsal_text(
        review.get("next_rehearsal_decision") or review.get("next_step") or ""
    )
    mismatch_summary = _route_task_rehearsal_review_mismatch_summary(
        review,
        crosscheck,
        hil_alignment,
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": review.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "evidence_ref": _safe_route_task_rehearsal_ref(review.get("evidence_ref", "")),
            "crosscheck_status": {
                "status": _redact_route_task_rehearsal_text(crosscheck_status),
                "scope": _redact_route_task_rehearsal_text(
                    crosscheck.get("scope") or "status/replay/task_record software alignment only"
                ),
                "software_mismatch_count": mismatch_summary["software_mismatch_count"],
            },
            "hil_alignment_status": {
                "status": _redact_route_task_rehearsal_text(hil_alignment.get("status", "")),
                "alignment_status": _redact_route_task_rehearsal_text(
                    hil_alignment.get("alignment_status") or "not_proven"
                ),
                "evidence_ref_match": bool(hil_alignment.get("evidence_ref_match", False)),
                "not_real_hil_when_status_is_missing_blocked_or_software_proof": bool(
                    hil_alignment.get("not_real_hil_when_status_is_missing_blocked_or_software_proof", True)
                ),
            },
            "mismatch_summary": mismatch_summary,
            "next_rehearsal_decision": next_decision or "continue_operator_review",
            "not_proven": _route_task_rehearsal_not_proven(review),
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_SCHEMA or source_boundary != ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_schema",
                "read_error": "route/task rehearsal operator review schema or evidence boundary is unsupported",
                "safe_copy": "Route/task rehearsal operator review is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "Route/task rehearsal operator review is not a supported diagnostics source; no delivery result is proven.",
                "next_rehearsal_decision": "regenerate_supported_operator_review_package",
            }
        )
        return summary

    if _route_task_rehearsal_review_safe_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_copy",
                "read_error": "route/task rehearsal operator review safe_copy is missing or unsafe",
                "safe_copy": "Route/task rehearsal operator review copy was blocked because it could imply control or delivery success.",
                "safe_phone_copy": "Route/task rehearsal operator review copy was blocked because it could imply control or delivery success.",
                "next_rehearsal_decision": "rewrite_phone_safe_operator_review_copy",
            }
        )
        return summary

    summary["safe_copy"] = safe_copy
    summary["safe_phone_copy"] = safe_copy
    if crosscheck_status == "pass":
        summary.update(
            {
                "overall_status": "degraded",
                "state": "crosscheck_pass",
                "next_rehearsal_decision": next_decision or "continue_rehearsal_review_without_control_actions",
            }
        )
        return summary
    if crosscheck_status == "fail":
        summary.update(
            {
                "overall_status": "blocked",
                "state": "crosscheck_fail",
                "safe_copy": "Route/task rehearsal operator review found mismatches; keep proof blocked and not_proven.",
                "safe_phone_copy": "Route/task rehearsal operator review found mismatches; keep proof blocked and not_proven.",
                "next_rehearsal_decision": next_decision or "fix_mismatches_and_regenerate_review_package",
            }
        )
        return summary

    summary.update(
        {
            "overall_status": "blocked",
            "state": "unsupported_status",
            "read_error": "route/task rehearsal operator review crosscheck status is missing or unsupported",
            "safe_copy": "Route/task rehearsal operator review has no supported crosscheck result; proof remains blocked.",
            "safe_phone_copy": "Route/task rehearsal operator review has no supported crosscheck result; proof remains blocked.",
            "next_rehearsal_decision": "regenerate_review_with_crosscheck_pass_or_fail",
        }
    )
    return summary


def summarize_pc_route_debug_console(path):
    """构建 PC route debug console 的 metadata-only diagnostics 摘要。"""
    console_path = os.path.expanduser(str(path or ""))
    summary = _default_pc_route_debug_console_summary(
        console_path,
        read_error="pc route debug console summary is not configured",
    )
    if not console_path:
        return summary
    if not os.path.exists(console_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "pc route debug console summary not found",
                "safe_copy": "PC route debug console summary is missing; this is not delivery success.",
                "safe_phone_copy": "PC route debug console summary is missing; this is not delivery success.",
                "availability": {
                    "status": "blocked",
                    "reason": "summary file missing",
                },
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(console_path, "r", encoding="utf-8") as f:
            console = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading pc route debug console summary: {exc}"
                ),
                "safe_copy": "PC route debug console summary could not be read; keep proof blocked.",
                "safe_phone_copy": "PC route debug console summary could not be read; keep proof blocked.",
                "availability": {
                    "status": "blocked",
                    "reason": "summary JSON read error",
                },
            }
        )
        return summary

    if not isinstance(console, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "pc route debug console JSON must be an object",
                "safe_copy": "PC route debug console summary shape is invalid; proof remains blocked.",
                "safe_phone_copy": "PC route debug console summary shape is invalid; proof remains blocked.",
            }
        )
        return summary

    source_schema = str(console.get("schema") or "")
    source_boundary = str(console.get("evidence_boundary") or "")
    safe_copy = _redact_route_task_rehearsal_text(
        console.get("safe_copy") or console.get("safe_phone_copy") or ""
    )
    availability = console.get("availability") if isinstance(console.get("availability"), dict) else {}
    route_debug_status = (
        console.get("route_debug_status")
        if isinstance(console.get("route_debug_status"), dict)
        else {}
    )
    route_elevator_reconciliation = _summarize_pc_route_elevator_reconciliation(
        console.get("route_elevator_reconciliation"),
        source_boundary,
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": console.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "availability": _safe_pc_route_debug_dict(availability),
            "route_debug_status": _safe_pc_route_debug_dict(route_debug_status),
            "route_progress": _safe_pc_route_debug_dict(console.get("route_progress")),
            "keyframe_preflight": _safe_pc_route_debug_dict(console.get("keyframe_preflight")),
            "recent_task_summary": _safe_pc_route_debug_dict(
                console.get("recent_task_summary") or console.get("recent_task")
            ),
            "route_elevator_reconciliation": route_elevator_reconciliation,
            "not_proven": _pc_route_debug_not_proven(console),
            "read_error": "",
        }
    )
    if source_schema != PC_ROUTE_DEBUG_CONSOLE_SCHEMA or source_boundary != PC_ROUTE_DEBUG_CONSOLE_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_schema",
                "read_error": "pc route debug console schema or evidence boundary is unsupported",
                "safe_copy": "PC route debug console summary is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "PC route debug console summary is not a supported diagnostics source; no delivery result is proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary

    if _pc_route_debug_safe_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_copy",
                "read_error": "pc route debug console safe_copy is missing or unsafe",
                "safe_copy": "PC route debug console copy was blocked because it could imply control or delivery success.",
                "safe_phone_copy": "PC route debug console copy was blocked because it could imply control or delivery success.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsafe support copy",
                },
            }
        )
        return summary

    availability_status = str(availability.get("status") or console.get("status") or "").strip().lower()
    blocked_statuses = {"", "blocked", "missing", "read_error", "unsupported_schema", "unsafe_copy"}
    summary["safe_copy"] = safe_copy
    summary["safe_phone_copy"] = safe_copy
    if availability_status in blocked_statuses:
        summary.update(
            {
                "overall_status": "blocked",
                "state": availability_status or "blocked",
            }
        )
        return summary

    summary.update(
        {
            "overall_status": "degraded",
            "state": "available",
        }
    )
    return summary


def summarize_route_task_field_run_readiness(path):
    """构建 route-task field-run readiness 的 phone/support-safe 摘要。"""
    readiness_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_readiness_summary(
        readiness_path,
        read_error="route-task field-run readiness artifact is not configured",
    )
    if not readiness_path:
        return summary
    if not os.path.exists(readiness_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route-task field-run readiness artifact not found",
                "safe_copy": "Route-task field-run readiness artifact is missing; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run readiness artifact is missing; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "readiness artifact missing",
                },
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(readiness_path, "r", encoding="utf-8") as f:
            readiness = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading route-task field-run readiness artifact: {exc}"
                ),
                "safe_copy": "Route-task field-run readiness artifact could not be read; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run readiness artifact could not be read; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "readiness JSON read error",
                },
            }
        )
        return summary

    if not isinstance(readiness, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route-task field-run readiness JSON must be an object",
                "safe_copy": "Route-task field-run readiness shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run readiness shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    source_schema = str(readiness.get("schema") or "")
    source_boundary = str(readiness.get("evidence_boundary") or "")
    phone_summary = (
        readiness.get("phone_support_safe_summary")
        if isinstance(readiness.get("phone_support_safe_summary"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or readiness.get("safe_copy")
        or readiness.get("safe_phone_copy")
        or "Route-task field-run readiness is metadata-only; not delivery success."
    )
    availability = (
        phone_summary.get("availability")
        if isinstance(phone_summary.get("availability"), dict)
        else readiness.get("availability") if isinstance(readiness.get("availability"), dict) else {}
    )
    missing_materials = _safe_route_task_rehearsal_list(
        phone_summary.get("missing_materials")
        if isinstance(phone_summary.get("missing_materials"), list)
        else readiness.get("missing_materials")
    )
    required_materials = _safe_route_task_rehearsal_list(
        phone_summary.get("required_field_run_materials")
        if isinstance(phone_summary.get("required_field_run_materials"), list)
        else readiness.get("required_field_run_materials")
    )
    commands_summary = _safe_route_task_rehearsal_list(
        phone_summary.get("commands_summary")
        if isinstance(phone_summary.get("commands_summary"), list)
        else readiness.get("commands_to_run")
    )
    next_evidence_summary = _redact_route_task_rehearsal_text(
        phone_summary.get("next_evidence_summary")
        or readiness.get("next_evidence_summary")
        or readiness.get("next_step")
        or "Collect the listed field-run materials with the same evidence_ref before claiming route/task execution."
    )
    overall_status = _redact_route_task_rehearsal_text(
        phone_summary.get("overall_status") or readiness.get("overall_status") or "blocked"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": readiness.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "overall_status": overall_status or "blocked",
            "availability": _safe_pc_route_debug_dict(availability)
            or {
                "status": overall_status or "blocked",
                "reason": "readiness summary consumed without explicit availability",
            },
            "evidence_ref": _safe_route_task_rehearsal_ref(readiness.get("evidence_ref", "")),
            "same_evidence_ref_required": bool(readiness.get("same_evidence_ref_required", True)),
            "next_evidence": {
                "summary": next_evidence_summary,
                "missing_materials": missing_materials,
                "required_field_run_materials": required_materials,
            },
            "commands_summary": commands_summary,
            "not_proven": _route_task_field_run_readiness_not_proven(readiness),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_READINESS_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_READINESS_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_schema",
                "read_error": "route-task field-run readiness schema or evidence boundary is unsupported",
                "safe_copy": "Route-task field-run readiness is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "Route-task field-run readiness is not a supported diagnostics source; no delivery result is proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary

    if _route_task_field_run_readiness_has_unsafe_fields(readiness) or _route_task_field_run_readiness_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_fields",
                "read_error": "route-task field-run readiness contains unsafe fields or copy",
                "safe_copy": "Route-task field-run readiness was blocked because it could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Route-task field-run readiness was blocked because it could expose raw/control data or imply delivery success.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsafe readiness fields",
                },
            }
        )
        return summary

    blocked_statuses = {"", "blocked", "blocked_missing_material", "blocked_unsupported_schema", "missing", "read_error"}
    status_text = str(overall_status or "").strip().lower()
    summary["state"] = "blocked" if status_text in blocked_statuses else "available"
    return summary


def summarize_route_task_field_run_intake(path):
    """构建 route-task field-run intake/crosscheck 的 phone/support-safe 摘要。"""
    intake_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_intake_summary(
        intake_path,
        read_error="route-task field-run intake artifact is not configured",
    )
    if not intake_path:
        return summary
    if not os.path.exists(intake_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route-task field-run intake artifact not found",
                "safe_copy": "Route-task field-run intake artifact is missing; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run intake artifact is missing; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "intake artifact missing",
                },
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(intake_path, "r", encoding="utf-8") as f:
            intake = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading route-task field-run intake artifact: {exc}"
                ),
                "safe_copy": "Route-task field-run intake artifact could not be read; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run intake artifact could not be read; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "intake JSON read error",
                },
            }
        )
        return summary

    if not isinstance(intake, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route-task field-run intake JSON must be an object",
                "safe_copy": "Route-task field-run intake shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run intake shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    # 支持 Task A 直接输出 phone-safe summary，也支持顶层 artifact 暴露同名摘要别名。
    phone_summary = {}
    for candidate in (
        intake.get("phone_support_safe_summary"),
        intake.get("route_task_field_run_intake_summary"),
        intake.get("route_task_field_run_intake"),
    ):
        if isinstance(candidate, dict):
            phone_summary = candidate
            break
    source_schema = str(intake.get("schema") or "")
    source_boundary = str(intake.get("evidence_boundary") or "")
    overall_status = _redact_route_task_rehearsal_text(
        phone_summary.get("overall_status") or intake.get("overall_status") or "blocked"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or intake.get("safe_copy")
        or intake.get("safe_phone_copy")
        or "Route-task field-run intake is metadata-only; not delivery success."
    )
    availability = (
        phone_summary.get("availability")
        if isinstance(phone_summary.get("availability"), dict)
        else intake.get("availability") if isinstance(intake.get("availability"), dict) else {}
    )
    missing_materials = _safe_route_task_rehearsal_list(
        phone_summary.get("missing_materials")
        if isinstance(phone_summary.get("missing_materials"), list)
        else intake.get("missing_materials")
    )
    mismatch_reasons = _safe_route_task_rehearsal_list(
        phone_summary.get("mismatch_reasons")
        if isinstance(phone_summary.get("mismatch_reasons"), list)
        else intake.get("mismatch_reasons")
    )
    commands_to_rerun = _safe_route_task_rehearsal_list(
        phone_summary.get("commands_to_rerun")
        if isinstance(phone_summary.get("commands_to_rerun"), list)
        else intake.get("commands_to_rerun")
    )
    crosscheck_status = _redact_route_task_rehearsal_text(
        phone_summary.get("crosscheck_status")
        or phone_summary.get("status")
        or intake.get("crosscheck_status")
        or overall_status
        or "not_proven"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": intake.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "overall_status": overall_status or "blocked",
            "availability": _safe_pc_route_debug_dict(availability)
            or {
                "status": overall_status or "blocked",
                "reason": "intake summary consumed without explicit availability",
            },
            "evidence_ref": _safe_route_task_rehearsal_ref(
                phone_summary.get("evidence_ref") or intake.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                phone_summary.get(
                    "same_evidence_ref_required",
                    intake.get("same_evidence_ref_required", True),
                )
            ),
            "crosscheck": {
                "status": crosscheck_status or "not_proven",
                "missing_materials": missing_materials,
                "mismatch_reasons": mismatch_reasons,
                "commands_to_rerun": commands_to_rerun,
            },
            "not_proven": _route_task_field_run_intake_not_proven(intake),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_INTAKE_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_INTAKE_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_schema",
                "read_error": "route-task field-run intake schema or evidence boundary is unsupported",
                "safe_copy": "Route-task field-run intake is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "Route-task field-run intake is not a supported diagnostics source; no delivery result is proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary

    if (
        _route_task_field_run_readiness_has_unsafe_fields(phone_summary)
        or _route_task_field_run_intake_has_unsafe_control_claims(intake)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_fields",
                "read_error": "route-task field-run intake contains unsafe summary fields or control claims",
                "safe_copy": "Route-task field-run intake was blocked because summary fields could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Route-task field-run intake was blocked because summary fields could expose raw/control data or imply delivery success.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsafe intake summary fields",
                },
            }
        )
        return summary

    blocked_statuses = {
        "",
        "blocked",
        "blocked_missing_material",
        "blocked_mismatch",
        "missing",
        "mismatch",
        "read_error",
        "not_proven",
    }
    status_text = str(overall_status or "").strip().lower()
    summary["state"] = "blocked" if status_text in blocked_statuses else "available"
    return summary


def summarize_route_task_field_run_review(path):
    """构建 route-task field-run review console 的 phone/support-safe 摘要。"""
    review_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_review_summary(
        review_path,
        read_error="route-task field-run review report is not configured",
    )
    if not review_path:
        return summary
    if not os.path.exists(review_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route-task field-run review report not found",
                "safe_copy": "Route-task field-run review report is missing; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run review report is missing; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "review report missing",
                },
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(review_path, "r", encoding="utf-8") as f:
            review = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading route-task field-run review report: {exc}"
                ),
                "safe_copy": "Route-task field-run review report could not be read; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run review report could not be read; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "review JSON read error",
                },
            }
        )
        return summary

    if not isinstance(review, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route-task field-run review JSON must be an object",
                "safe_copy": "Route-task field-run review shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run review shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    # Task A 可能输出 phone_safe_summary，也可能为了兼容使用既有 phone_support_safe_summary 或同名 summary。
    phone_summary = {}
    for candidate in (
        review.get("phone_safe_summary"),
        review.get("phone_support_safe_summary"),
        review.get("route_task_field_run_review_summary"),
        review.get("route_task_field_run_review"),
    ):
        if isinstance(candidate, dict):
            phone_summary = candidate
            break
    source_schema = str(review.get("schema") or "")
    source_boundary = str(review.get("evidence_boundary") or "")
    overall_status = _redact_route_task_rehearsal_text(
        phone_summary.get("overall_status") or review.get("overall_status") or "blocked"
    )
    review_decision = _redact_route_task_rehearsal_text(
        phone_summary.get("review_decision") or review.get("review_decision") or "not_proven"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or review.get("safe_copy")
        or review.get("safe_phone_copy")
        or "Route-task field-run review is metadata-only; not delivery success."
    )
    availability = (
        phone_summary.get("availability")
        if isinstance(phone_summary.get("availability"), dict)
        else review.get("availability") if isinstance(review.get("availability"), dict) else {}
    )
    missing_materials = _safe_route_task_rehearsal_list(
        phone_summary.get("missing_materials")
        if isinstance(phone_summary.get("missing_materials"), list)
        else review.get("missing_materials")
    )
    mismatch_reasons = _safe_route_task_rehearsal_list(
        phone_summary.get("mismatch_reasons")
        if isinstance(phone_summary.get("mismatch_reasons"), list)
        else review.get("mismatch_reasons")
    )
    commands_to_rerun = _safe_route_task_rehearsal_list(
        phone_summary.get("commands_to_rerun")
        if isinstance(phone_summary.get("commands_to_rerun"), list)
        else review.get("commands_to_rerun")
    )
    operator_next_steps = _safe_route_task_rehearsal_list(
        phone_summary.get("operator_next_steps")
        if isinstance(phone_summary.get("operator_next_steps"), list)
        else review.get("operator_next_steps")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": review.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "overall_status": overall_status or "blocked",
            "availability": _safe_pc_route_debug_dict(availability)
            or {
                "status": overall_status or "blocked",
                "reason": "review summary consumed without explicit availability",
            },
            "evidence_ref": _safe_route_task_rehearsal_ref(
                phone_summary.get("evidence_ref") or review.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                phone_summary.get(
                    "same_evidence_ref_required",
                    review.get("same_evidence_ref_required", True),
                )
            ),
            "review": {
                "decision": review_decision or "not_proven",
                "missing_materials": missing_materials,
                "mismatch_reasons": mismatch_reasons,
                "commands_to_rerun": commands_to_rerun,
                "operator_next_steps": operator_next_steps,
            },
            "phone_safe_summary": _safe_pc_route_debug_dict(phone_summary),
            "not_proven": _route_task_field_run_review_not_proven(review, phone_summary),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_REVIEW_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_REVIEW_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_schema",
                "read_error": "route-task field-run review schema or evidence boundary is unsupported",
                "safe_copy": "Route-task field-run review is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "Route-task field-run review is not a supported diagnostics source; no delivery result is proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary

    if (
        _route_task_field_run_readiness_has_unsafe_fields(phone_summary)
        or _route_task_field_run_intake_has_unsafe_control_claims(review)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_fields",
                "read_error": "route-task field-run review contains unsafe summary fields or control claims",
                "safe_copy": "Route-task field-run review was blocked because summary fields could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Route-task field-run review was blocked because summary fields could expose raw/control data or imply delivery success.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsafe review summary fields",
                },
            }
        )
        return summary

    blocked_statuses = {
        "",
        "blocked",
        "blocked_missing_material",
        "blocked_mismatch",
        "missing",
        "mismatch",
        "read_error",
        "not_proven",
    }
    status_text = str(overall_status or "").strip().lower()
    summary["state"] = "blocked" if status_text in blocked_statuses else "available"
    return summary


def summarize_route_task_field_run_execution_pack(path):
    """构建 route-task field-run execution pack 的 metadata-only diagnostics 摘要。"""
    pack_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_execution_pack_summary(
        pack_path,
        read_error="route-task field-run execution pack is not configured",
    )
    if not pack_path:
        return summary
    if not os.path.exists(pack_path):
        summary.update(
            {
                "status": "missing",
                "read_error": "route-task field-run execution pack not found",
                "materials_status": {
                    "status": "blocked",
                    "reason": "execution pack artifact missing",
                },
                "safe_copy": "Route-task field-run execution pack is missing; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run execution pack is missing; metadata remains blocked/not_proven.",
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(pack_path, "r", encoding="utf-8") as f:
            pack = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "status": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading route-task field-run execution pack: {exc}"
                ),
                "materials_status": {
                    "status": "blocked",
                    "reason": "execution pack JSON read error",
                },
                "safe_copy": "Route-task field-run execution pack could not be read; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run execution pack could not be read; metadata remains blocked/not_proven.",
            }
        )
        return summary

    if not isinstance(pack, dict):
        summary.update(
            {
                "status": "read_error",
                "read_error": "route-task field-run execution pack JSON must be an object",
                "materials_status": {
                    "status": "blocked",
                    "reason": "execution pack JSON shape is invalid",
                },
                "safe_copy": "Route-task field-run execution pack shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run execution pack shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    # 兼容 artifact 顶层摘要、phone-safe 摘要和同名 summary；只白名单读取可给 diagnostics 的字段。
    phone_summary = {}
    for candidate in (
        pack.get("phone_safe_summary"),
        pack.get("phone_support_safe_summary"),
        pack.get("route_task_field_run_execution_pack_summary"),
        pack.get("route_task_field_run_execution_pack"),
    ):
        if isinstance(candidate, dict):
            phone_summary = candidate
            break
    source_schema = str(pack.get("schema") or "")
    source_boundary = str(pack.get("evidence_boundary") or "")
    status = _redact_route_task_rehearsal_text(
        phone_summary.get("status")
        or phone_summary.get("overall_status")
        or pack.get("status")
        or pack.get("overall_status")
        or "blocked"
    )
    materials_status = (
        phone_summary.get("materials_status")
        if isinstance(phone_summary.get("materials_status"), dict)
        else pack.get("materials_status") if isinstance(pack.get("materials_status"), dict) else {}
    )
    command_source = (
        phone_summary.get("command_summary")
        if "command_summary" in phone_summary
        else phone_summary.get("commands_summary")
        if "commands_summary" in phone_summary
        else pack.get("command_summary")
        if "command_summary" in pack
        else pack.get("commands_summary")
    )
    if isinstance(command_source, list):
        command_summary = _safe_route_task_rehearsal_list(command_source)
    elif isinstance(command_source, dict):
        command_summary = _safe_pc_route_debug_value(command_source)
    elif str(command_source or "").strip():
        command_summary = [_redact_route_task_rehearsal_text(command_source)]
    else:
        command_summary = []
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or pack.get("safe_copy")
        or pack.get("safe_phone_copy")
        or "Route-task field-run execution pack is metadata-only; not delivery success."
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": pack.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "status": status or "blocked",
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                phone_summary.get("evidence_ref")
                or phone_summary.get("safe_evidence_ref")
                or pack.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                phone_summary.get(
                    "same_evidence_ref_required",
                    pack.get("same_evidence_ref_required", True),
                )
            ),
            "materials_status": _safe_pc_route_debug_dict(materials_status)
            or {
                "status": status or "blocked",
                "reason": "execution pack consumed without explicit materials status",
            },
            "command_summary": command_summary,
            "not_proven": _route_task_field_run_execution_pack_not_proven(pack, phone_summary),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_GATE:
        summary.update(
            {
                "status": "unsupported_schema",
                "read_error": "route-task field-run execution pack schema or evidence boundary is unsupported",
                "materials_status": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "safe_copy": "Route-task field-run execution pack is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "Route-task field-run execution pack is not a supported diagnostics source; no delivery result is proven.",
            }
        )
        return summary

    if (
        _route_task_field_run_readiness_has_unsafe_fields(phone_summary)
        or _route_task_field_run_intake_has_unsafe_control_claims(pack)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "status": "unsafe_fields",
                "read_error": "route-task field-run execution pack contains unsafe summary fields or control claims",
                "materials_status": {
                    "status": "blocked",
                    "reason": "unsafe execution pack summary fields",
                },
                "safe_copy": "Route-task field-run execution pack was blocked because summary fields could expose control data or imply delivery success.",
                "safe_phone_copy": "Route-task field-run execution pack was blocked because summary fields could expose control data or imply delivery success.",
            }
        )
        return summary

    return summary


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
    source_schema = str(signal.get("schema") or "")
    source_boundary = str(signal.get("evidence_boundary") or "")
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


def summarize_route_task_rehearsal_execution_bundle(path):
    """构建只读、仅元数据的 route/task rehearsal execution bundle 摘要。"""
    bundle_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_rehearsal_execution_bundle_summary(
        bundle_path,
        read_error="route/task rehearsal execution bundle is not configured",
    )
    if not bundle_path:
        return summary
    if not os.path.exists(bundle_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route/task rehearsal execution bundle not found",
                "safe_phone_copy": "Route/task rehearsal execution bundle is missing; this is not delivery success.",
                "next_step": "Regenerate the execution bundle manifest, then reopen diagnostics.",
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(bundle_path, "r", encoding="utf-8") as f:
            bundle = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading route/task rehearsal execution bundle: {exc}"
                ),
                "safe_phone_copy": "Route/task rehearsal execution bundle could not be read; keep proof not_proven.",
                "next_step": "Fix the manifest JSON and rerun the bundle generator.",
            }
        )
        return summary

    if not isinstance(bundle, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route/task rehearsal execution bundle JSON must be an object",
                "safe_phone_copy": "Route/task rehearsal execution bundle shape is invalid; proof remains not_proven.",
                "next_step": "Regenerate a JSON object manifest from route_task_rehearsal_bundle.",
            }
        )
        return summary

    source_schema = str(bundle.get("schema") or "")
    source_boundary = str(bundle.get("evidence_boundary") or "")
    diagnostics_summary = bundle.get("diagnostics_summary") if isinstance(bundle.get("diagnostics_summary"), dict) else {}
    artifact_summary = bundle.get("artifact_summary") if isinstance(bundle.get("artifact_summary"), dict) else {}
    artifacts = bundle.get("artifacts") if isinstance(bundle.get("artifacts"), dict) else {}
    not_proven_source = bundle.get("not_proven")
    if not isinstance(not_proven_source, list):
        not_proven_source = diagnostics_summary.get("not_proven")
    if not isinstance(not_proven_source, list):
        not_proven_source = artifact_summary.get("not_proven")
    if not isinstance(not_proven_source, list):
        not_proven_source = []
    artifact_ref = _first_route_task_rehearsal_value(
        bundle.get("route_task_rehearsal_artifact_ref"),
        bundle.get("rehearsal_artifact_ref"),
        bundle.get("artifact_ref"),
        bundle.get("artifact_path"),
        artifacts.get("route_task_rehearsal_artifact"),
        artifacts.get("rehearsal_artifact"),
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": bundle.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "evidence_ref": _safe_route_task_rehearsal_ref(
                _first_route_task_rehearsal_value(
                    bundle.get("evidence_ref"),
                    diagnostics_summary.get("evidence_ref"),
                    artifact_summary.get("evidence_ref"),
                )
            ),
            "artifact_ref": _safe_route_task_rehearsal_ref(artifact_ref),
            "artifact_state": _redact_route_task_rehearsal_text(
                _first_route_task_rehearsal_value(
                    diagnostics_summary.get("state"),
                    artifact_summary.get("state"),
                    bundle.get("artifact_state"),
                )
            ),
            "not_proven": _route_task_rehearsal_not_proven({"not_proven": not_proven_source}),
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_SCHEMA or source_boundary != ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_GATE:
        summary.update(
            {
                "state": "unsupported_schema",
                "read_error": "route/task rehearsal execution bundle schema or evidence boundary is unsupported",
                "safe_phone_copy": "Route/task rehearsal execution bundle is not a supported diagnostics source; no delivery result is proven.",
                "next_step": "Regenerate the manifest with the supported execution bundle schema and boundary.",
            }
        )
        return summary

    # 新旧生成器可能把 crosscheck/HIL 摘要放在 manifest 顶层、diagnostics_summary 或 artifact_summary；只读合并即可。
    crosscheck = bundle.get("crosscheck_status") if isinstance(bundle.get("crosscheck_status"), dict) else {}
    if not crosscheck:
        crosscheck = (
            diagnostics_summary.get("crosscheck_status")
            if isinstance(diagnostics_summary.get("crosscheck_status"), dict)
            else {}
        )
    if not crosscheck:
        crosscheck = (
            artifact_summary.get("crosscheck_status")
            if isinstance(artifact_summary.get("crosscheck_status"), dict)
            else {}
        )
    hil_alignment = bundle.get("hil_alignment_status") if isinstance(bundle.get("hil_alignment_status"), dict) else {}
    if not hil_alignment:
        hil_alignment = (
            diagnostics_summary.get("hil_alignment_status")
            if isinstance(diagnostics_summary.get("hil_alignment_status"), dict)
            else {}
        )
    if not hil_alignment:
        hil_alignment = (
            artifact_summary.get("hil_alignment_status")
            if isinstance(artifact_summary.get("hil_alignment_status"), dict)
            else {}
        )
    crosscheck_status = str(crosscheck.get("status") or "").strip().lower()
    software_mismatches = crosscheck.get("software_mismatches")
    hil_mismatches = hil_alignment.get("mismatches")
    summary["crosscheck_status"] = {
        "status": _redact_route_task_rehearsal_text(crosscheck_status),
        "scope": _redact_route_task_rehearsal_text(
            crosscheck.get("scope") or "status/replay/task_record software alignment only"
        ),
        "software_mismatch_count": len(software_mismatches) if isinstance(software_mismatches, list) else 0,
        "software_mismatches": _safe_route_task_rehearsal_list(software_mismatches),
    }
    alignment_status = str(hil_alignment.get("alignment_status") or "not_proven").strip()
    summary["hil_alignment_status"] = {
        "status": _redact_route_task_rehearsal_text(hil_alignment.get("status", "")),
        "alignment_status": _redact_route_task_rehearsal_text(alignment_status or "not_proven"),
        "evidence_ref_match": bool(hil_alignment.get("evidence_ref_match", False)),
        "not_real_hil_when_status_is_missing_blocked_or_software_proof": bool(
            hil_alignment.get("not_real_hil_when_status_is_missing_blocked_or_software_proof", True)
        ),
        "detail": _redact_route_task_rehearsal_text(
            hil_alignment.get("detail") or "not real HIL; execution bundle remains software proof"
        ),
        "mismatch_count": len(hil_mismatches) if isinstance(hil_mismatches, list) else 0,
    }

    if crosscheck_status == "pass":
        summary.update(
            {
                "state": "crosscheck_pass",
                "safe_phone_copy": "Route/task rehearsal execution bundle crosscheck passed as Docker/local software proof only; it is not delivery success.",
                "next_step": "Use the bundle for support/replay handoff, then collect real Nav2/fixed-route and HIL evidence before claiming delivery.",
            }
        )
        return summary
    if crosscheck_status == "fail":
        summary.update(
            {
                "state": "crosscheck_fail",
                "safe_phone_copy": "Route/task rehearsal execution bundle crosscheck failed; keep route/task proof blocked and not_proven.",
                "next_step": "Inspect sanitized software mismatches, fix source inputs, and regenerate the execution bundle.",
            }
        )
        return summary

    summary.update(
        {
            "state": "unsupported_status",
            "read_error": "route/task rehearsal execution bundle crosscheck status is missing or unsupported",
            "safe_phone_copy": "Route/task rehearsal execution bundle has no supported crosscheck result; no route or delivery pass is proven.",
            "next_step": "Regenerate the manifest with crosscheck_status.status pass or fail.",
        }
    )
    return summary


def _default_hardware_proof_summary(path, status="read_error", read_error=""):
    return {
        "status": status,
        "artifact_ref": str(path or ""),
        "source_status": "",
        "exists": False,
        "read_error": str(read_error or ""),
        "summary": "Hardware diagnostics proof is not available; no hardware pass can be inferred.",
        "next_step": "Run hardware_diagnostics_proof and then complete WAVE ROVER hardware-in-loop validation.",
        "vendor_sources": [],
        "risk_flags": [],
        "hil_recipe": {},
    }


def _hardware_proof_risk_text(flag):
    if isinstance(flag, dict):
        parts = [
            flag.get("id", ""),
            flag.get("severity", ""),
            flag.get("detail", ""),
            flag.get("message", ""),
        ]
        return " ".join(str(part) for part in parts if part)
    return str(flag)


def _has_hil_risk(risk_flags):
    if not isinstance(risk_flags, list):
        return True
    for flag in risk_flags:
        text = _hardware_proof_risk_text(flag).lower()
        severity = str(flag.get("severity", "")).lower() if isinstance(flag, dict) else ""
        flag_id = str(flag.get("id", "")).lower() if isinstance(flag, dict) else text
        if flag_id == "hil_required":
            return True
        if ("hil" in text or "hardware-in-loop" in text) and severity in {"high", "critical"}:
            return True
    return False


def summarize_hardware_proof(path):
    """Return a phone-safe summary of an offline WAVE ROVER proof artifact.

    Vendor/source boundary: the artifact itself is produced by the hardware
    package from docs/vendor/VENDOR_INDEX.md-backed WAVE ROVER references. This
    operator summary only reads and downgrades the artifact; it never upgrades
    software evidence into a hardware pass or invents extra hardware facts.
    """
    proof_path = os.path.expanduser(str(path or ""))
    summary = _default_hardware_proof_summary(
        proof_path,
        read_error="hardware diagnostics proof is not configured",
    )
    if not proof_path:
        return summary
    if not os.path.exists(proof_path):
        summary["read_error"] = f"hardware diagnostics proof not found: {proof_path}"
        return summary

    summary["exists"] = True
    try:
        with open(proof_path, "r", encoding="utf-8") as f:
            artifact = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary["read_error"] = f"failed reading hardware diagnostics proof: {exc}"
        return summary

    if not isinstance(artifact, dict):
        summary["read_error"] = "hardware diagnostics proof JSON must be an object"
        return summary

    source_status = str(artifact.get("status") or "")
    summary["source_status"] = source_status
    summary["vendor_sources"] = (
        list(artifact.get("vendor_sources")) if isinstance(artifact.get("vendor_sources"), list) else []
    )
    summary["risk_flags"] = (
        list(artifact.get("risk_flags")) if isinstance(artifact.get("risk_flags"), list) else []
    )
    summary["hil_recipe"] = artifact.get("hil_recipe") if isinstance(artifact.get("hil_recipe"), dict) else {}

    if not source_status:
        summary["read_error"] = "hardware diagnostics proof is missing status"
        return summary

    if source_status == "invalid_config":
        summary.update(
            {
                "status": "invalid_config",
                "summary": "Hardware diagnostics proof found an invalid bridge configuration.",
                "next_step": "Fix the reported bridge configuration, rerun software proof, then run WAVE ROVER HIL.",
                "read_error": str((artifact.get("config_validation") or {}).get("error", "")),
            }
        )
        return summary

    if source_status == "software_proof_ready":
        if _has_hil_risk(summary["risk_flags"]):
            summary.update(
                {
                    "status": "needs_hil",
                    "summary": "Software proof exists, hardware-in-loop still required before treating the robot as validated.",
                    "next_step": "Run the WAVE ROVER HIL recipe on a prepared robot and capture UART, motion, IMU, and battery evidence.",
                    "read_error": "",
                }
            )
            return summary
        summary.update(
            {
                "status": "software_proof",
                "summary": "Software proof is ready only; this does not validate real UART, wheel motion, IMU, battery, or HIL.",
                "next_step": "Use this artifact as software evidence, then schedule WAVE ROVER hardware-in-loop validation.",
                "read_error": "",
            }
        )
        return summary

    if source_status == "feedback_parse_failed":
        summary.update(
            {
                "status": "needs_hil",
                "summary": "Software artifact exists but feedback parsing failed; hardware-in-loop validation is still required.",
                "next_step": "Inspect the feedback sample, rerun proof with valid T=1001 feedback, then run WAVE ROVER HIL.",
                "read_error": "feedback sample did not parse as trusted hardware feedback",
            }
        )
        return summary

    summary["read_error"] = f"unsupported hardware diagnostics proof status: {source_status}"
    return summary


def normalize_log_refs(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item)]
    text = str(value).strip()
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def default_review_decision_log(path, status="read_error", read_error=""):
    return {
        "status": status,
        "decision_log_ref": str(path or ""),
        "exists": False,
        "decision_count": 0,
        "sample_count": 0,
        "read_error": str(read_error or ""),
    }


def review_decision_entry(record):
    return {
        "decision_id": str(record.get("decision_id", "")),
        "decision": str(record.get("decision", "")),
        "comment": str(record.get("comment", "")),
        "option": str(record.get("option", "")),
        "operator": str(record.get("operator", "")),
        "timestamp": record.get("timestamp"),
    }


def load_review_decision_log(path):
    decision_log_path = os.path.expanduser(str(path or ""))
    summary = default_review_decision_log(
        decision_log_path,
        status="not_configured",
        read_error="review decision log is not configured",
    )
    decision_index = {}
    if not decision_log_path:
        return summary, decision_index
    if not os.path.exists(decision_log_path):
        summary["status"] = "missing"
        summary["read_error"] = f"review decision log not found: {decision_log_path}"
        return summary, decision_index

    summary["exists"] = True
    summary["read_error"] = ""
    try:
        with open(decision_log_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    record = json.loads(text)
                except json.JSONDecodeError as exc:
                    summary["status"] = "read_error"
                    summary["read_error"] = f"invalid decision JSONL at line {line_number}: {exc}"
                    return summary, {}
                if not isinstance(record, dict):
                    continue
                sample_id = str(record.get("sample_id", "")).strip()
                decision = str(record.get("decision", "")).strip()
                if not sample_id or decision not in REVIEW_DECISION_VALUES:
                    continue
                summary["decision_count"] += 1
                decision_index[sample_id] = review_decision_entry(record)
    except OSError as exc:
        summary["status"] = "read_error"
        summary["read_error"] = f"failed reading review decision log: {exc}"
        return summary, {}

    summary["sample_count"] = len(decision_index)
    summary["status"] = "ok"
    return summary, decision_index


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_task_record(path):
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


def extract_elevator_assist(latest_status, last_task):
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
    return [field for field in ROUTE_PROOF_REQUIRED_FIELDS if field not in route_proof_summary]


def classify_route_proof(route_proof_summary, source=""):
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
    coverage_rate = safe_float(route_proof_summary.get("coverage_rate"))
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


def sample_event_type(sample):
    context = sample.get("context") if isinstance(sample.get("context"), dict) else {}
    return str(context.get("event_type") or "unknown")


def sample_review_reason(sample):
    event_type = sample_event_type(sample)
    detection_count = safe_int(sample.get("detection_count"))
    max_confidence = safe_int(sample.get("max_confidence"))
    context = sample.get("context") if isinstance(sample.get("context"), dict) else {}

    if context.get("anomaly_type") or event_type == "anomaly":
        return "anomaly_sample"
    if event_type == "route_keyframe":
        return "route_keyframe_review"
    if detection_count > 0 and max_confidence < LOW_CONFIDENCE_REVIEW_THRESHOLD:
        return "low_confidence_detection"
    if not str(sample.get("label_status", "")).strip() and not str(sample.get("review_status", "")).strip():
        return "unreviewed_sample"
    return ""


def vision_sample_review_item(sample, decision_index=None):
    context = sample.get("context") if isinstance(sample.get("context"), dict) else {}
    sample_id = str(sample.get("sample_id", ""))
    last_decision = None
    if isinstance(decision_index, dict):
        last_decision = dict(decision_index.get(sample_id) or {}) or None
    return {
        "sample_id": sample_id,
        "sample_ref": str(sample.get("sample_ref", "")),
        "timestamp": sample.get("timestamp"),
        "context": context,
        "event_type": sample_event_type(sample),
        "detection_count": safe_int(sample.get("detection_count")),
        "max_confidence": safe_int(sample.get("max_confidence")),
        "reason": sample_review_reason(sample),
        "review_status": "decided" if last_decision else "pending",
        "last_decision": last_decision,
    }


def build_vision_review_queue(samples, decision_index=None, limit=REVIEW_QUEUE_LIMIT):
    queue = []
    for sample in reversed(samples):
        if not isinstance(sample, dict):
            continue
        reason = sample_review_reason(sample)
        if not reason:
            continue
        item = vision_sample_review_item(sample, decision_index=decision_index)
        queue.append(item)
        if len(queue) >= limit:
            break
    return list(reversed(queue))


def _review_decision_distribution(counts, decided):
    decided = int(decided or 0)
    distribution = {}
    for decision in REVIEW_DECISION_ORDER:
        count = int(counts.get(decision, 0))
        distribution[decision] = {
            "count": count,
            "ratio": round(count / decided, 4) if decided > 0 else 0.0,
        }
    return distribution


def summarize_review_progress(samples, decision_index=None):
    decision_index = decision_index if isinstance(decision_index, dict) else {}
    reviewable = []
    decision_counts = {decision: 0 for decision in REVIEW_DECISION_ORDER}
    decided = 0
    next_pending_sample = None

    for sample in samples:
        if not isinstance(sample, dict):
            continue
        reason = sample_review_reason(sample)
        if not reason:
            continue
        reviewable.append(sample)
        sample_id = str(sample.get("sample_id", ""))
        decision_entry = decision_index.get(sample_id) if sample_id else None
        decision = str((decision_entry or {}).get("decision", "")).strip()
        if decision in REVIEW_DECISION_VALUES:
            decided += 1
            decision_counts[decision] += 1
            continue
        if next_pending_sample is None:
            next_pending_sample = {
                "sample_id": sample_id,
                "sample_ref": str(sample.get("sample_ref", "")),
                "reason": reason,
                "event_type": sample_event_type(sample),
                "timestamp": sample.get("timestamp"),
            }

    total = len(reviewable)
    pending = max(total - decided, 0)
    progress_summary = {
        "total": total,
        "decided": decided,
        "pending": pending,
        "coverage_rate": round(decided / total, 4) if total > 0 else 0.0,
    }
    return {
        "progress_summary": progress_summary,
        "decision_distribution": _review_decision_distribution(decision_counts, decided),
        "next_pending_sample": next_pending_sample,
    }


def default_integrity_fields(status, *, error="", warning=""):
    errors = [error] if error else []
    warnings = [warning] if warning else []
    return {
        "integrity_summary": {
            "status": status,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "missing_file_ref_count": 0,
            "sample_output_dir": "",
            "negative_sample_count": 0,
            "anomaly_sample_count": 0,
            "route_keyframe_sample_count": 0,
            "detection_sample_count": 0,
        },
        "integrity_errors": errors,
        "integrity_warnings": warnings,
        "integrity_error_count": len(errors),
        "integrity_warning_count": len(warnings),
        "missing_file_ref_count": 0,
        "missing_file_refs": [],
        "context_field_coverage": {"present": {}, "missing": {}},
        "file_counts": {},
    }


def integrity_status(checker_summary):
    if checker_summary.get("errors"):
        return "error"
    if checker_summary.get("warnings"):
        return "warning"
    return "ok"


def vision_manifest_integrity_fields(path):
    if not path:
        return default_integrity_fields(
            "not_configured",
            error="vision sample manifest is not configured",
        )
    if summarize_manifest is None:
        return default_integrity_fields(
            "checker_unavailable",
            warning="ros2_trashbot_vision.vision_sample_manifest is not importable",
        )

    try:
        checker_summary = summarize_manifest(path)
    except Exception as exc:
        return default_integrity_fields(
            "checker_failed",
            error=f"vision sample manifest checker failed: {exc}",
        )

    errors = [str(item) for item in checker_summary.get("errors", [])]
    warnings = [str(item) for item in checker_summary.get("warnings", [])]
    missing_file_refs = [
        item for item in checker_summary.get("missing_file_refs", []) if isinstance(item, dict)
    ]
    status = integrity_status({"errors": errors, "warnings": warnings})
    return {
        "integrity_summary": {
            "status": status,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "missing_file_ref_count": len(missing_file_refs),
            "sample_output_dir": str(checker_summary.get("sample_output_dir", "")),
            "negative_sample_count": safe_int(checker_summary.get("negative_sample_count")),
            "anomaly_sample_count": safe_int(checker_summary.get("anomaly_sample_count")),
            "route_keyframe_sample_count": safe_int(checker_summary.get("route_keyframe_sample_count")),
            "detection_sample_count": safe_int(checker_summary.get("detection_sample_count")),
        },
        "integrity_errors": errors,
        "integrity_warnings": warnings,
        "integrity_error_count": len(errors),
        "integrity_warning_count": len(warnings),
        "missing_file_ref_count": len(missing_file_refs),
        "missing_file_refs": missing_file_refs,
        "context_field_coverage": checker_summary.get("context_field_coverage", {"present": {}, "missing": {}}),
        "file_counts": checker_summary.get("file_counts", {}),
    }


def summarize_vision_manifest(path, decision_index=None):
    path = os.path.expanduser(str(path or ""))
    summary = {
        "manifest_ref": path,
        "exists": False,
        "schema": "",
        "sample_count": 0,
        "latest_sample_ref": "",
        "latest_timestamp": None,
        "latest_context": {},
        "latest_detection_count": 0,
        "latest_max_confidence": 0,
        "event_counts": {},
        "review_queue_count": 0,
        "review_queue": [],
        "progress_summary": {
            "total": 0,
            "decided": 0,
            "pending": 0,
            "coverage_rate": 0.0,
        },
        "decision_distribution": _review_decision_distribution({}, 0),
        "next_pending_sample": None,
        "read_error": "",
    }
    summary.update(vision_manifest_integrity_fields(path))
    if not path:
        summary["read_error"] = "vision sample manifest is not configured"
        return summary
    if not os.path.exists(path):
        summary["read_error"] = f"vision sample manifest not found: {path}"
        return summary

    summary["exists"] = True
    try:
        with open(path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary["read_error"] = f"failed reading vision sample manifest: {exc}"
        return summary

    samples = manifest.get("samples") if isinstance(manifest, dict) else None
    if not isinstance(samples, list):
        summary["read_error"] = "vision sample manifest has no samples list"
        return summary

    summary["schema"] = str(manifest.get("schema", ""))
    summary["sample_count"] = len(samples)
    event_counts = {}
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        event_type = sample_event_type(sample)
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    summary["event_counts"] = event_counts
    review_queue = build_vision_review_queue(samples, decision_index=decision_index)
    summary.update(summarize_review_progress(samples, decision_index=decision_index))
    summary["review_queue"] = review_queue
    summary["review_queue_count"] = len(review_queue)
    latest = samples[-1] if samples and isinstance(samples[-1], dict) else {}
    summary["latest_sample_ref"] = str(latest.get("sample_ref", ""))
    summary["latest_timestamp"] = latest.get("timestamp")
    summary["latest_context"] = latest.get("context") if isinstance(latest.get("context"), dict) else {}
    summary["latest_detection_count"] = safe_int(latest.get("detection_count"))
    summary["latest_max_confidence"] = safe_int(latest.get("max_confidence"))
    return summary


def build_diagnostics_payload(
    latest_status,
    *,
    software_version,
    map_version,
    route_version,
    log_refs,
    vision_sample_manifest_ref,
    review_decision_log_ref,
    operator_status_file,
    hardware_proof_ref="",
    oss_cdn_manifest_artifact_ref="",
    network_recovery_artifact_ref="",
    credential_rotation_artifact_ref="",
    provisioning_audit_artifact_ref="",
    production_store_queue_artifact_ref="",
    queue_ordering_drill_artifact_ref="",
    transaction_isolation_artifact_ref="",
    production_recovery_artifact_ref="",
    route_task_rehearsal_artifact_ref="",
    route_task_rehearsal_bundle_ref="",
    route_task_rehearsal_operator_review_ref="",
    pc_route_debug_console_ref="",
    route_task_field_run_readiness_ref="",
    route_task_field_run_intake_ref="",
    route_task_field_run_review_ref="",
    route_task_field_run_execution_pack_ref="",
    route_task_field_run_reconciliation_ref="",
    route_task_completion_signal_ref="",
    route_task_field_run_console_ref="",
    route_task_field_run_evidence_kit_ref="",
    route_task_field_run_material_bundle_ref="",
    route_task_field_run_material_validation_ref="",
    elevator_field_run_material_validation_ref="",
    elevator_field_run_review_ref="",
    elevator_field_run_execution_pack_ref="",
    elevator_route_evidence_reconciliation_ref="",
    route_elevator_field_session_handoff_ref="",
):
    latest_status = dict(latest_status or {})
    # phone-safe metadata 必须由 HTTP wrapper 重新生成；诊断 core 不转发状态文件里的旧对象。
    latest_status.pop("phone_support_bundle", None)
    latest_status.pop("voice_prompt_readiness", None)
    latest_status.pop("phone_offline_resume_readiness", None)
    last_task = dict(latest_status.get("last_task") or {})
    task_record_path = str(
        latest_status.get("task_record_path")
        or last_task.get("task_record_path")
        or ""
    )
    task_record = _read_task_record(task_record_path)
    route_proof_summary, route_proof_source = _extract_route_proof_summary(latest_status, last_task)
    route_proof_status = classify_route_proof(route_proof_summary, source=route_proof_source)
    elevator_assist, elevator_assist_source = extract_elevator_assist(latest_status, last_task)
    elevator_assist_status = classify_elevator_assist(elevator_assist, source=elevator_assist_source)
    traceability = coalesce_traceability_fields(
        latest_status,
        task_record=task_record,
        last_task=last_task,
    )
    source = normalize_evidence_source(traceability["source"])
    result_path = traceability["result_path"]
    evidence_ref = traceability["evidence_ref"]
    failure_code = traceability["failure_code"]
    human_intervention_required = traceability["human_intervention_required"]
    state_transition_history = traceability["state_transition_history"]
    route_progress = traceability["route_progress"]
    last_task["source"] = source
    last_task["result_path"] = result_path
    if "evidence_ref" in last_task:
        last_task["evidence_ref"] = evidence_ref
    else:
        last_task["evidence_ref"] = (
            str(task_record.get("result_path", "")).strip() or evidence_ref
        )
    last_task["failure_code"] = failure_code
    last_task["state_transition_history"] = state_transition_history
    last_task["human_intervention_required"] = human_intervention_required
    last_task["route_progress"] = route_progress
    failure = {
        "state": latest_status.get("state", ""),
        "message": latest_status.get("message", ""),
        "error_code": latest_status.get("error_code") or last_task.get("error_code", ""),
        "final_state": latest_status.get("final_state") or last_task.get("final_state", ""),
        "task_record_path": latest_status.get("task_record_path") or last_task.get("task_record_path", ""),
        "result_path": result_path,
        "source": source,
        "evidence_ref": evidence_ref,
        "failure_code": failure_code,
        "human_intervention_required": human_intervention_required,
        "state_transition_history": state_transition_history,
        "route_progress": route_progress,
    }
    review_decision_log, decision_index = load_review_decision_log(review_decision_log_ref)
    route_task_field_run_readiness_summary = summarize_route_task_field_run_readiness(
        route_task_field_run_readiness_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_READINESS", "")
    )
    route_task_field_run_intake_summary = summarize_route_task_field_run_intake(
        route_task_field_run_intake_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_INTAKE", "")
    )
    route_task_field_run_review_summary = summarize_route_task_field_run_review(
        route_task_field_run_review_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW_CONSOLE", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW", "")
    )
    route_task_field_run_execution_pack_summary = summarize_route_task_field_run_execution_pack(
        route_task_field_run_execution_pack_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_EXECUTION_PACK", "")
    )
    route_task_field_run_reconciliation_summary = summarize_route_task_field_run_reconciliation(
        route_task_field_run_reconciliation_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_RECONCILIATION", "")
    )
    route_task_completion_signal_summary = summarize_route_task_completion_signal(
        route_task_completion_signal_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_COMPLETION_SIGNAL", "")
    )
    route_task_field_run_console_summary = summarize_route_task_field_run_console(
        route_task_field_run_console_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_CONSOLE", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_CONSOLE_SUMMARY", "")
    )
    route_task_field_run_evidence_kit_summary = summarize_route_task_field_run_evidence_kit(
        route_task_field_run_evidence_kit_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SUMMARY", "")
    )
    route_task_field_run_material_bundle_summary = summarize_route_task_field_run_material_bundle(
        route_task_field_run_material_bundle_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY", "")
    )
    route_task_field_run_material_validation_summary = summarize_route_task_field_run_material_validation(
        route_task_field_run_material_validation_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY", "")
    )
    elevator_field_run_material_validation_summary = summarize_elevator_field_run_material_validation(
        elevator_field_run_material_validation_ref
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION", "")
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY", "")
    )
    elevator_field_run_review_summary = summarize_elevator_field_run_review(
        elevator_field_run_review_ref
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW", "")
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW_SUMMARY", "")
    )
    elevator_field_run_execution_pack_summary = summarize_elevator_field_run_execution_pack(
        elevator_field_run_execution_pack_ref
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK", "")
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY", "")
    )
    elevator_route_evidence_reconciliation_summary = summarize_elevator_route_evidence_reconciliation(
        elevator_route_evidence_reconciliation_ref
        or os.environ.get("TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION", "")
        or os.environ.get("TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY", "")
    )
    route_elevator_field_session_handoff_summary = summarize_route_elevator_field_session_handoff(
        route_elevator_field_session_handoff_ref
        or os.environ.get("TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF", "")
        or os.environ.get("TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY", "")
    )
    return status_payload(
        "diagnostics_ready",
        "diagnostics package ready",
        software_version=str(software_version or ""),
        map_version=str(map_version or ""),
        route_version=str(route_version or ""),
        latest_status=latest_status,
        last_task=last_task,
        source=source,
        result_path=result_path,
        evidence_ref=evidence_ref,
        failure_code=failure_code,
        human_intervention_required=human_intervention_required,
        state_transition_history=state_transition_history,
        route_progress=route_progress,
        failure=failure,
        log_refs=normalize_log_refs(log_refs),
        vision_sample_manifest_ref=str(vision_sample_manifest_ref or ""),
        review_decision_log_ref=str(review_decision_log_ref or ""),
        review_decision_log=review_decision_log,
        vision_samples=summarize_vision_manifest(
            vision_sample_manifest_ref,
            decision_index=decision_index,
        ),
        route_proof_summary=route_proof_summary,
        route_proof_status=route_proof_status,
        route_task_rehearsal=summarize_route_task_rehearsal_artifact(
            route_task_rehearsal_artifact_ref
            or os.environ.get("TRASHBOT_ROUTE_TASK_REHEARSAL_ARTIFACT", "")
        ),
        route_task_rehearsal_execution_bundle=summarize_route_task_rehearsal_execution_bundle(
            route_task_rehearsal_bundle_ref
            or os.environ.get("TRASHBOT_ROUTE_TASK_REHEARSAL_BUNDLE", "")
        ),
        route_task_rehearsal_operator_review=summarize_route_task_rehearsal_operator_review(
            route_task_rehearsal_operator_review_ref
            or os.environ.get("TRASHBOT_ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW", "")
        ),
        pc_route_debug_console=summarize_pc_route_debug_console(
            pc_route_debug_console_ref
            or os.environ.get("TRASHBOT_PC_ROUTE_DEBUG_CONSOLE", "")
        ),
        route_task_field_run_readiness=route_task_field_run_readiness_summary,
        route_task_field_run_readiness_summary=route_task_field_run_readiness_summary,
        route_task_field_run_intake=route_task_field_run_intake_summary,
        route_task_field_run_intake_summary=route_task_field_run_intake_summary,
        route_task_field_run_review=route_task_field_run_review_summary,
        route_task_field_run_review_summary=route_task_field_run_review_summary,
        route_task_field_run_execution_pack=route_task_field_run_execution_pack_summary,
        route_task_field_run_execution_pack_summary=route_task_field_run_execution_pack_summary,
        route_task_field_run_reconciliation=route_task_field_run_reconciliation_summary,
        route_task_field_run_reconciliation_summary=route_task_field_run_reconciliation_summary,
        route_task_completion_signal=route_task_completion_signal_summary,
        route_task_completion_signal_summary=route_task_completion_signal_summary,
        route_task_field_run_console=route_task_field_run_console_summary,
        route_task_field_run_console_summary=route_task_field_run_console_summary,
        route_task_field_run_evidence_kit=route_task_field_run_evidence_kit_summary,
        route_task_field_run_evidence_kit_summary=route_task_field_run_evidence_kit_summary,
        route_task_field_run_material_bundle=route_task_field_run_material_bundle_summary,
        route_task_field_run_material_bundle_summary=route_task_field_run_material_bundle_summary,
        route_task_field_run_material_validation=route_task_field_run_material_validation_summary,
        route_task_field_run_material_validation_summary=route_task_field_run_material_validation_summary,
        elevator_field_run_material_validation=elevator_field_run_material_validation_summary,
        elevator_field_run_material_validation_summary=elevator_field_run_material_validation_summary,
        elevator_field_run_review=elevator_field_run_review_summary,
        elevator_field_run_review_summary=elevator_field_run_review_summary,
        elevator_field_run_execution_pack=elevator_field_run_execution_pack_summary,
        elevator_field_run_execution_pack_summary=elevator_field_run_execution_pack_summary,
        elevator_route_evidence_reconciliation=elevator_route_evidence_reconciliation_summary,
        elevator_route_evidence_reconciliation_summary=elevator_route_evidence_reconciliation_summary,
        route_elevator_field_session_handoff=route_elevator_field_session_handoff_summary,
        route_elevator_field_session_handoff_summary=route_elevator_field_session_handoff_summary,
        elevator_assist=elevator_assist,
        elevator_assist_status=elevator_assist_status,
        hardware_proof=summarize_hardware_proof(hardware_proof_ref),
        oss_cdn_manifest=build_phone_oss_cdn_manifest_summary(oss_cdn_manifest_artifact_ref),
        network_recovery_drill=build_phone_network_recovery_summary(
            network_recovery_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT", "")
        ),
        credential_rotation=build_phone_credential_rotation_summary(
            credential_rotation_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT", "")
        ),
        provisioning_audit=build_phone_provisioning_audit_summary(
            provisioning_audit_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT", "")
        ),
        production_store_queue=build_phone_production_store_queue_summary(
            production_store_queue_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT", "")
        ),
        queue_ordering_drill=build_phone_queue_ordering_drill_summary(
            queue_ordering_drill_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT", "")
        ),
        transaction_isolation=build_phone_transaction_isolation_summary(
            transaction_isolation_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT", "")
        ),
        production_recovery=build_phone_production_recovery_summary(
            production_recovery_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT", "")
        ),
        operator_status_file=str(operator_status_file or ""),
    )
