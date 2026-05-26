import json
import os

from ros2_trashbot_behavior.operator_gateway_diagnostics_mobile_field import (
    _mobile_field_material_intake_has_unsafe_fields,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_run import (
    _route_task_field_run_readiness_copy_is_unsafe,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_rehearsal import (
    _redact_route_task_rehearsal_text,
    _safe_pc_route_debug_dict,
    _safe_pc_route_debug_value,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
)

WAVE_ROVER_FEEDBACK_REPLAY_SCHEMA = "trashbot.wave_rover_feedback_replay.v1"
WAVE_ROVER_FEEDBACK_REPLAY_SUMMARY_SCHEMA = "trashbot.wave_rover_feedback_replay_summary.v1"
WAVE_ROVER_FEEDBACK_REPLAY_GATE = (
    "software_proof_docker_wave_rover_feedback_replay_gate"
)
WAVE_ROVER_HIL_PACKET_INTAKE_SCHEMA = "trashbot.wave_rover_hil_packet_intake.v1"
WAVE_ROVER_HIL_PACKET_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.wave_rover_hil_packet_intake_summary.v1"
)
WAVE_ROVER_HIL_PACKET_INTAKE_GATE = (
    "software_proof_docker_wave_rover_hil_packet_intake_gate"
)
WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_SCHEMA = (
    "trashbot.wave_rover_hil_packet_review_decision.v1"
)
WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.wave_rover_hil_packet_review_decision_summary.v1"
)
WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_GATE = (
    "software_proof_docker_wave_rover_hil_packet_review_decision_gate"
)
WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_SCHEMA = (
    "trashbot.wave_rover_hil_packet_execution_pack.v1"
)
WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_SUMMARY_SCHEMA = (
    "trashbot.wave_rover_hil_packet_execution_pack_summary.v1"
)
WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_GATE = (
    "software_proof_docker_wave_rover_hil_packet_execution_pack_gate"
)
WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_SCHEMA = (
    "trashbot.wave_rover_hil_packet_collection_drill.v1"
)
WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_SUMMARY_SCHEMA = (
    "trashbot.wave_rover_hil_packet_collection_drill_summary.v1"
)
WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_GATE = (
    "software_proof_docker_wave_rover_hil_packet_collection_drill_gate"
)
HARDWARE_BASELINE_REVIEW_SCHEMA = "trashbot.hardware_baseline_review_gate.v1"
HARDWARE_BASELINE_REVIEW_SUMMARY_SCHEMA = "trashbot.hardware_baseline_review_summary.v1"
HARDWARE_BASELINE_REVIEW_GATE = "software_proof_docker_hardware_baseline_review_gate"
HARDWARE_BASELINE_SOURCE_ALIGNMENT_SCHEMA = "trashbot.hardware_baseline_source_alignment.v1"
HARDWARE_BASELINE_SOURCE_ALIGNMENT_SUMMARY_SCHEMA = (
    "trashbot.hardware_baseline_source_alignment_summary.v1"
)
HARDWARE_BASELINE_SOURCE_ALIGNMENT_GATE = (
    "software_proof_docker_hardware_baseline_source_alignment_gate"
)


def _wave_rover_feedback_replay_not_proven(replay=None, summary_fragment=None):
    # replay gate 只证明离线解析/对齐逻辑；真实串口、底盘反馈和 HIL 仍必须独立补证。
    replay = replay if isinstance(replay, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(replay.get("not_proven"), list):
        source_values.extend(replay.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "real_wave_rover_feedback",
        "real_serial_or_uart_feedback",
        "real_chassis_motion",
        "real_hil_pass",
        "delivery_success",
        "primary_actions",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _wave_rover_feedback_replay_has_not_proven(replay, summary_fragment):
    # 缺 not_proven 时不能默认安全；Hardware gate 必须显式保留未证明清单。
    for candidate in (summary_fragment, replay):
        if isinstance(candidate, dict) and isinstance(candidate.get("not_proven"), list):
            return bool(candidate.get("not_proven"))
    return False


def _wave_rover_hil_packet_intake_not_proven(packet=None, summary_fragment=None):
    # HIL packet intake 只证明资料包契约被读取；真实 HIL、串口、ROS topic 和交付成功仍未证明。
    packet = packet if isinstance(packet, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(packet.get("not_proven"), list):
        source_values.extend(packet.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "not_proven",
        "real_wave_rover",
        "real_uart",
        "hil_pass",
        "real_odom",
        "real_imu",
        "real_battery",
        "delivery_success",
        "primary_actions",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _wave_rover_hil_packet_intake_has_not_proven(packet, summary_fragment):
    # PC gate 必须显式给出 not_proven 列表和 overall_status=not_proven，缺任一项都按不安全处理。
    for candidate in (summary_fragment, packet):
        if not isinstance(candidate, dict):
            continue
        if not isinstance(candidate.get("not_proven"), list) or not candidate.get("not_proven"):
            continue
        status = str(
            candidate.get("overall_status")
            or candidate.get("status")
            or candidate.get("verdict")
            or ""
        ).strip()
        if status == "not_proven":
            return True
    return False


def _wave_rover_hil_packet_review_decision_not_proven(decision=None, summary_fragment=None):
    # review decision 只把 intake 资料分成 accepted/missing/rejected；真实 HIL 与底盘 topic 仍必须另证。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(decision.get("not_proven"), list):
        source_values.extend(decision.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "not_proven",
        "real_wave_rover",
        "real_uart",
        "hil_pass",
        "real_feedback_T1001",
        "real_odom",
        "real_imu",
        "real_battery",
        "delivery_success",
        "primary_actions",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _wave_rover_hil_packet_review_decision_has_not_proven(decision, summary_fragment):
    # PC review gate 必须显式给出 not_proven 和 overall_status=not_proven，缺字段不能默认安全。
    for candidate in (summary_fragment, decision):
        if not isinstance(candidate, dict):
            continue
        if not isinstance(candidate.get("not_proven"), list) or not candidate.get("not_proven"):
            continue
        status = str(
            candidate.get("overall_status")
            or candidate.get("status")
            or candidate.get("verdict")
            or ""
        ).strip()
        if status == "not_proven":
            return True
    return False


def _wave_rover_hil_packet_execution_pack_not_proven(pack=None, summary_fragment=None):
    # execution pack 只整理现场采集顺序；真实 WAVE ROVER、串口 topic、HIL 和交付成功仍必须另证。
    pack = pack if isinstance(pack, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(pack.get("not_proven"), list):
        source_values.extend(pack.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "not_proven",
        "real_wave_rover",
        "real_uart",
        "hil_pass",
        "real_feedback_T1001",
        "real_odom",
        "real_imu",
        "real_battery",
        "delivery_success",
        "primary_actions",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _wave_rover_hil_packet_collection_drill_not_proven(drill=None, summary_fragment=None):
    # collection drill 只展示采集演练元数据；不能证明真实串口、底盘运动、HIL 或投放成功。
    drill = drill if isinstance(drill, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for candidate in (drill, summary_fragment):
        if isinstance(candidate.get("not_proven"), list):
            source_values.extend(candidate.get("not_proven"))
        if isinstance(candidate.get("blocked_reasons"), list):
            source_values.extend(candidate.get("blocked_reasons"))
    required = (
        "not_proven",
        "software_proof_only",
        "real_wave_rover",
        "real_uart",
        "hil_pass",
        "real_feedback_T1001",
        "real_odom",
        "real_imu",
        "real_battery",
        "ack_mutation",
        "cursor_mutation",
        "route_or_nav2_runtime",
        "cmd_vel",
        "wave_rover_command",
        "safe_to_control",
        "delivery_success",
        "primary_actions",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _wave_rover_hil_packet_collection_drill_has_not_proven(drill, summary_fragment):
    # 来源必须显式声明 not_proven；缺字段时 Robot 不能替 PC gate 背书为安全摘要。
    for candidate in (summary_fragment, drill):
        if not isinstance(candidate, dict):
            continue
        if not isinstance(candidate.get("not_proven"), list) or not candidate.get("not_proven"):
            continue
        status = str(
            candidate.get("overall_status")
            or candidate.get("status")
            or candidate.get("verdict")
            or ""
        ).strip()
        if status == "not_proven":
            return True
    return False


def _hardware_baseline_review_not_proven(review=None, summary_fragment=None):
    # hardware baseline review 只消费 Autonomy/Hardware 的材料结论；真实传感器、控制和 HIL 必须另有证据。
    review = review if isinstance(review, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(review.get("not_proven"), list):
        source_values.extend(review.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
        "real_sensor_device_proof",
        "real_nav2_fixed_route_run",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "delivery_success",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _hardware_baseline_source_alignment_not_proven(alignment=None, summary_fragment=None):
    # source alignment 只证明 Hardware 基线材料来源已被软件门禁整理；不能证明真实器件、接线或 HIL。
    alignment = alignment if isinstance(alignment, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(alignment.get("not_proven"), list):
        source_values.extend(alignment.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "not_proven",
        "software_proof",
        "hardware_baseline_source_alignment",
        "vendor_source_alignment_review",
        "hardware_material_pending",
        "real_sensor_device_proof",
        "sensor_procurement_completed",
        "sensor_installed_on_robot",
        "sensor_wiring_verified",
        "sensor_power_budget_verified",
        "real_nav2_fixed_route_run",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _default_wave_rover_feedback_replay_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 缺少 replay artifact 时仍输出完整 false 栅栏，防止 diagnostics 被误解成硬件反馈或远控入口。
    return {
        "schema": WAVE_ROVER_FEEDBACK_REPLAY_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": WAVE_ROVER_FEEDBACK_REPLAY_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "feedback_replay_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "WAVE ROVER feedback replay summary is not configured",
        },
        "safe_evidence_ref": "",
        "feedback_alignment": {"verdict": "not_proven"},
        "interval_alignment": {"verdict": "not_proven"},
        "topic_alignment": {"verdict": "not_proven"},
        "next_required_evidence": [],
        "not_proven": _wave_rover_feedback_replay_not_proven(),
        "boundary": WAVE_ROVER_FEEDBACK_REPLAY_GATE,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "real_wave_rover_feedback": False,
        "real_serial_or_uart_feedback": False,
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


def _default_wave_rover_hil_packet_intake_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 默认摘要始终带 false 栅栏，避免缺配置时被上游 UI 当作 HIL 或可执行动作证据。
    return {
        "schema": WAVE_ROVER_HIL_PACKET_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": WAVE_ROVER_HIL_PACKET_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "overall_status": "not_proven",
        "packet_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "WAVE ROVER HIL packet intake summary is not configured",
        },
        "safe_evidence_ref": "",
        "required_files": [],
        "missing_files": [],
        "operator_report_status": "not_proven",
        "next_required_evidence": [],
        "not_proven": _wave_rover_hil_packet_intake_not_proven(),
        "boundary": WAVE_ROVER_HIL_PACKET_INTAKE_GATE,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_robot_copy": (
            "WAVE ROVER HIL packet intake is metadata-only; not HIL pass; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "metadata_only": True,
        "real_hardware_observed": False,
        "real_wave_rover": False,
        "real_uart": False,
        "real_odom": False,
        "real_imu": False,
        "real_battery": False,
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


def _default_wave_rover_hil_packet_review_decision_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 默认 review 摘要必须完整 fail-closed，避免缺配置时被误当作真实 HIL packet 审核通过。
    return {
        "schema": WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "overall_status": "not_proven",
        "review_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "WAVE ROVER HIL packet review decision is not configured",
        },
        "review_decision": "blocked_not_configured",
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "accepted_required_materials": [],
        "missing_required_materials": [],
        "rejected_required_materials": [],
        "next_required_evidence": [],
        "owner_handoff": {},
        "rerun_commands": [],
        "not_proven": _wave_rover_hil_packet_review_decision_not_proven(),
        "boundary": WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_GATE,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_robot_copy": (
            "WAVE ROVER HIL packet review decision is metadata-only; not HIL pass; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "metadata_only": True,
        "real_hardware_observed": False,
        "real_wave_rover": False,
        "real_uart": False,
        "real_odom": False,
        "real_imu": False,
        "real_battery": False,
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


def _default_wave_rover_hil_packet_execution_pack_summary(
    path,
    status="blocked_missing_wave_rover_hil_packet_execution_pack",
    read_error="",
):
    # 缺配置也必须给出完整 false 栅栏，避免 operator diagnostics 被误读为 HIL 可执行或主动作授权。
    boundary_flags = {
        "metadata_only": True,
        "real_hardware_observed": False,
        "real_wave_rover": False,
        "real_uart": False,
        "real_feedback_T1001": False,
        "real_odom": False,
        "real_imu": False,
        "real_battery": False,
        "hil_pass": False,
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
        "production_ready": False,
    }
    return {
        "schema": WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "overall_status": "not_proven",
        "execution_pack_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "WAVE ROVER HIL packet execution pack is not configured",
        },
        "safe_evidence_ref": "",
        "required_material_templates": [],
        "collection_sequence": [],
        "owner_handoff": {},
        "rerun_commands": [],
        "boundary_flags": dict(boundary_flags),
        "not_proven": _wave_rover_hil_packet_execution_pack_not_proven(),
        "boundary": WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_GATE,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_robot_copy": (
            "WAVE ROVER HIL packet execution pack is metadata-only; not real HIL; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        **boundary_flags,
    }


def _default_wave_rover_hil_packet_collection_drill_summary(
    path,
    status="blocked_missing_wave_rover_hil_packet_collection_drill",
    read_error="",
):
    # 默认摘要完整补齐 false 栅栏，避免缺 collection drill 时 UI 或 API 误开控制入口。
    boundary_flags = {
        "metadata_only": True,
        "real_hardware_observed": False,
        "real_wave_rover": False,
        "real_uart": False,
        "real_feedback_T1001": False,
        "real_odom": False,
        "real_imu": False,
        "real_battery": False,
        "hil_pass": False,
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
        "production_ready": False,
    }
    return {
        "schema": WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "overall_status": "not_proven",
        "collection_drill_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "WAVE ROVER HIL packet collection drill is not configured",
        },
        "safe_evidence_ref": "",
        "required_material_templates": [],
        "preflight_checklist": [],
        "collection_sequence": [],
        "backfill_commands": [],
        "owner_handoff": {},
        "blocked_reasons": [],
        "boundary_flags": dict(boundary_flags),
        "not_proven": _wave_rover_hil_packet_collection_drill_not_proven(),
        "boundary": WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_GATE,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_robot_copy": (
            "WAVE ROVER HIL packet collection drill is metadata-only; not real HIL; "
            "delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
        ),
        **boundary_flags,
    }


def _default_hardware_baseline_review_summary(path, status="not_configured", read_error=""):
    # 缺少硬件 baseline review 时也必须显式 fail-closed，避免 diagnostics 被误当成硬件准入通过。
    return {
        "schema": HARDWARE_BASELINE_REVIEW_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_BASELINE_REVIEW_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "hardware baseline review is not configured",
        },
        "hardware_material_status": "hardware_material_pending",
        "blockers": ["hardware_material_pending"],
        "next_required_evidence": [],
        "review_summary": {
            "status": "hardware_material_pending",
            "reason": "hardware baseline review is not configured",
        },
        "safe_evidence_ref": "",
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Hardware baseline review is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
            "safe_phone_copy": (
                "Hardware baseline review is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
        },
        "not_proven": _hardware_baseline_review_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "route_elevator_field_pass": False,
        "nav2_fixed_route_run": False,
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


def _default_hardware_baseline_source_alignment_summary(
    path,
    status="blocked_missing_hardware_baseline_source_alignment",
    read_error="",
):
    # 缺少 source alignment 时必须保持 blocked；Robot diagnostics 只显示材料边界，不放开动作链路。
    return {
        "schema": HARDWARE_BASELINE_SOURCE_ALIGNMENT_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_BASELINE_SOURCE_ALIGNMENT_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {
            "schema": "",
            "evidence_boundary": "",
            "metadata_only": True,
        },
        "alignment_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "hardware baseline source alignment is not configured",
        },
        "hardware_material_status": "hardware_material_pending",
        "source_alignment_status": "blocked_missing_hardware_baseline_source_alignment",
        "blockers": ["blocked_missing_hardware_baseline_source_alignment"],
        "baseline_source_summary": {
            "status": "blocked_missing_hardware_baseline_source_alignment",
            "reason": "hardware baseline source alignment is not configured",
        },
        "default_hardware_set_summary": {},
        "target_sensor_baseline_summary": {},
        "vendor_source_boundary": {},
        "missing_alignment_items": [],
        "source_inventory_summary": [],
        "unresolved_sources": [],
        "owner_handoff": [],
        "next_required_evidence": [],
        "safe_evidence_ref": "",
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Hardware baseline source alignment is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
            "safe_phone_copy": (
                "Hardware baseline source alignment is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
        },
        "not_proven": _hardware_baseline_source_alignment_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "source_alignment_reviewed": False,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
        "sensor_wiring_verified": False,
        "sensor_power_budget_verified": False,
        "route_elevator_field_pass": False,
        "nav2_fixed_route_run": False,
        "dropoff_completion": False,
        "cancel_completion": False,
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


def _hardware_baseline_source_alignment_has_unsafe_fields(value, key_path=""):
    # 复用现场材料的防泄漏规则，并额外拦截硬件细节字段，防止 vendor/raw source 泄进 diagnostics。
    if _mobile_field_material_intake_has_unsafe_fields(value, key_path):
        return True
    extra_key_fragments = (
        "hardware_detail",
        "hardware_details",
        "raw_source",
        "raw_vendor",
        "private_source",
        "field_pass",
        "hil",
        "control",
        "ack_payload",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if any(fragment in key_text for fragment in extra_key_fragments):
                return True
            if _hardware_baseline_source_alignment_has_unsafe_fields(item, current_path):
                return True
        return False
    if isinstance(value, list):
        return any(
            _hardware_baseline_source_alignment_has_unsafe_fields(item, key_path)
            for item in value
        )
    return False


def _wave_rover_feedback_replay_source_contract(value):
    # 支持直接 artifact、summary wrapper 和嵌套 diagnostics；summary 仍必须回指本 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == WAVE_ROVER_FEEDBACK_REPLAY_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _wave_rover_hil_packet_intake_source_contract(value):
    # 支持 direct artifact、Robot-compatible summary、diagnostics summary；summary 必须回指同一 packet gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == WAVE_ROVER_HIL_PACKET_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _wave_rover_hil_packet_review_decision_source_contract(value):
    # 支持 direct artifact、summary wrapper 和 Robot-compatible summary；wrapper 必须回指 review-decision gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _wave_rover_hil_packet_execution_pack_source_contract(value):
    # 支持 Hardware worker 的 direct artifact 或已消毒 summary；summary 必须回指同一 execution-pack gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _wave_rover_hil_packet_collection_drill_source_contract(value):
    # 支持 direct artifact、summary wrapper 和 nested diagnostics；summary 必须回指 collection-drill gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_baseline_review_source_contract(value):
    # 允许直接 artifact 或已生成 summary；summary 仍必须回指 baseline review schema 和同一软件证据边界。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_BASELINE_REVIEW_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_baseline_source_alignment_source_contract(value):
    # 支持直接 artifact 或已消毒 summary；summary wrapper 必须回指同一 source-alignment gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_BASELINE_SOURCE_ALIGNMENT_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or HARDWARE_BASELINE_SOURCE_ALIGNMENT_SCHEMA)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_baseline_source_alignment_field(alignment, summary_fragment, key, default):
    # Hardware gate 的 direct artifact 和 summary-output 都可作为来源；Robot 只复制白名单字段。
    if key in alignment:
        return alignment.get(key)
    if key in summary_fragment:
        return summary_fragment.get(key)
    return default


def _hardware_baseline_source_alignment_status(alignment, summary_fragment, status_source):
    # direct artifact 要优先保留 gate 产出的对齐状态，避免被默认 pending 文案降级。
    for value in (
        status_source.get("status"),
        alignment.get("status"),
        alignment.get("overall_status"),
        alignment.get("hardware_baseline_source_alignment"),
        summary_fragment.get("status"),
        summary_fragment.get("overall_status"),
        summary_fragment.get("hardware_baseline_source_alignment"),
    ):
        text = str(value or "").strip()
        if text:
            return _redact_route_task_rehearsal_text(text)
    return "hardware_material_pending"


def _wave_rover_feedback_replay_has_disabled_actions(replay, summary_fragment):
    # replay source 和 summary 都必须显式关闭主动作；缺字段或字符串 false 都不能算安全。
    replay = replay if isinstance(replay, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else replay.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else replay.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _wave_rover_hil_packet_intake_has_disabled_actions(packet, summary_fragment):
    # intake source 和 summary 都必须显式关闭动作；缺字段或字符串 false 都不能算 diagnostics-safe。
    packet = packet if isinstance(packet, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else packet.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else packet.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _wave_rover_hil_packet_intake_same_evidence_ref_ok(packet, summary_fragment):
    # 同 evidence_ref 是 packet intake 的关键约束；显式 mismatch 或字符串布尔都必须 fail closed。
    packet = packet if isinstance(packet, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    same_required = (
        summary_fragment.get("same_evidence_ref_required")
        if "same_evidence_ref_required" in summary_fragment
        else packet.get("same_evidence_ref_required")
    )
    if same_required is not True:
        return False
    for candidate in (summary_fragment, packet):
        if candidate.get("evidence_ref_match") is False or candidate.get("same_evidence_ref") is False:
            return False
        mismatches = candidate.get("evidence_ref_mismatches")
        if isinstance(mismatches, list) and mismatches:
            return False
    return True


def _wave_rover_hil_packet_review_decision_has_disabled_actions(decision, summary_fragment):
    # review decision source 和 summary 都必须显式关闭动作；缺字段或字符串 false 都不能算 diagnostics-safe。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else decision.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else decision.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _wave_rover_hil_packet_review_decision_same_evidence_ref_ok(decision, summary_fragment):
    # review decision 继承 packet chain 的同 evidence_ref 约束；字符串 true/false 不算安全布尔。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    same_required = (
        summary_fragment.get("same_evidence_ref_required")
        if "same_evidence_ref_required" in summary_fragment
        else decision.get("same_evidence_ref_required")
    )
    if same_required is not True:
        return False
    for candidate in (summary_fragment, decision):
        if candidate.get("evidence_ref_match") is False or candidate.get("same_evidence_ref") is False:
            return False
        mismatches = candidate.get("evidence_ref_mismatches")
        if isinstance(mismatches, list) and mismatches:
            return False
    return True


def _wave_rover_hil_packet_execution_pack_has_disabled_actions(pack, summary_fragment):
    # execution pack source 和 summary 都必须显式关闭动作；缺字段或字符串 false 都不能算 diagnostics-safe。
    pack = pack if isinstance(pack, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else pack.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else pack.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _wave_rover_hil_packet_collection_drill_has_disabled_actions(drill, summary_fragment):
    # collection drill 还必须显式 safe_to_control=false，避免“采集演练”被前端误读为可控状态。
    drill = drill if isinstance(drill, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else drill.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else drill.get("primary_actions_enabled")
    )
    safe_to_control = (
        summary_fragment.get("safe_to_control")
        if "safe_to_control" in summary_fragment
        else drill.get("safe_to_control")
    )
    return (
        delivery_success is False
        and primary_actions_enabled is False
        and safe_to_control is False
    )


def _wave_rover_hil_packet_review_decision_has_unsafe_fields(value, key_path=""):
    # review decision 的安全边界和 intake 一致：只允许白名单摘要，拒绝 raw/HIL pass/控制成功 claim。
    return _wave_rover_hil_packet_intake_has_unsafe_fields(value, key_path)


def _wave_rover_hil_packet_intake_has_unsafe_fields(value, key_path=""):
    # 只允许 metadata 摘要字段；raw artifact、串口、校验值、凭证和成功文案都不能进入 diagnostics。
    unsafe_key_fragments = (
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "credential",
        "checksum",
        "traceback",
        "raw_path",
        "raw_file",
        "raw_artifact",
        "raw_packet",
        "raw_feedback",
        "raw_serial",
        "raw_uart",
        "local_path",
        "artifact_path",
        "serial_path",
        "uart_path",
        "device_path",
        "baud",
        "baudrate",
        "command_envelope",
        "status_envelope",
        "ack_payload",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "nav2_triggered",
        "hil_pass",
        "production_ready",
        "real_hardware_observed",
        "real_wave_rover",
        "real_uart",
        "real_odom",
        "real_imu",
        "real_battery",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _wave_rover_hil_packet_intake_has_unsafe_fields(item, current_path):
                return True
        return False
    if isinstance(value, list):
        return any(_wave_rover_hil_packet_intake_has_unsafe_fields(item, key_path) for item in value)
    if isinstance(value, str):
        redacted = _redact_route_task_rehearsal_text(value)
        guarded = redacted.lower()
        for phrase in (
            "not delivery success",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            "not_proven",
            "not proven",
            "metadata-only",
            "must not",
            "not real",
            "not hil pass",
            "不证明",
        ):
            guarded = guarded.replace(phrase, "")
        return (
            "[redacted_local_path]" in guarded
            or "[redacted_serial]" in guarded
            or "[redacted_baud]" in guarded
            or "[redacted_traceback]" in guarded
            or "/dev/" in guarded
            or "ttyusb" in guarded
            or "ttyama" in guarded
            or "serial path" in guarded
            or "uart path" in guarded
            or "baudrate" in guarded
            or "checksum" in guarded
            or "traceback" in guarded
            or "raw artifact" in guarded
            or "local path" in guarded
            or "ack posted" in guarded
            or "remote ack" in guarded
            or "cursor advanced" in guarded
            or "nav2 started" in guarded
            or "hil pass" in guarded
            or "delivery success" in guarded
            or "safe_to_control=true" in guarded
            or "safe to control" in guarded
        )
    return False


def _wave_rover_feedback_replay_has_unsafe_fields(value, key_path=""):
    # 允许 feedback/interval/topic verdict 字段，但拒绝 raw 串口、原始反馈、控制动作和成功 claim。
    unsafe_key_fragments = (
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "credential",
        "checksum",
        "traceback",
        "raw_path",
        "raw_file",
        "raw_feedback",
        "raw_serial",
        "raw_uart",
        "serial_path",
        "uart_path",
        "device_path",
        "baud",
        "baudrate",
        "command_envelope",
        "status_envelope",
        "ack_payload",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "nav2_triggered",
        "hil_pass",
        "production_ready",
        "real_hardware_observed",
        "real_wave_rover_feedback",
        "real_serial_or_uart_feedback",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _wave_rover_feedback_replay_has_unsafe_fields(item, current_path):
                return True
        return False
    if isinstance(value, list):
        return any(_wave_rover_feedback_replay_has_unsafe_fields(item, key_path) for item in value)
    if isinstance(value, str):
        redacted = _redact_route_task_rehearsal_text(value)
        guarded = redacted.lower()
        for phrase in (
            "not delivery success",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "not_proven",
            "not proven",
            "metadata-only",
            "must not",
            "not real",
            "不证明",
        ):
            guarded = guarded.replace(phrase, "")
        return (
            "/dev/" in guarded
            or "ttyusb" in guarded
            or "ttyama" in guarded
            or "serial path" in guarded
            or "uart path" in guarded
            or "baudrate" in guarded
            or "raw feedback" in guarded
            or "ack posted" in guarded
            or "remote ack" in guarded
            or "cursor advanced" in guarded
            or "nav2 started" in guarded
            or "hil pass" in guarded
            or "delivery success" in guarded
        )
    return False


def summarize_wave_rover_feedback_replay(source):
    """构建 WAVE ROVER feedback replay 的 metadata-only diagnostics 摘要。"""
    # 本 consumer 只读 Hardware gate 的安全摘要；不接触真实串口、不请求反馈流、不触发远控。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_wave_rover_feedback_replay_summary(
        source_path,
        read_error="WAVE ROVER feedback replay summary is not configured",
    )
    if isinstance(source, dict):
        replay = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "feedback_replay_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "WAVE ROVER feedback replay artifact missing",
                    },
                    "read_error": "WAVE ROVER feedback replay artifact missing",
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                replay = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading WAVE ROVER feedback replay summary: {exc}"
            )
            summary.update(
                {
                    "feedback_replay_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                    },
                    "read_error": safe_error,
                }
            )
            return summary

    if not isinstance(replay, dict):
        summary.update(
            {
                "feedback_replay_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "WAVE ROVER feedback replay JSON must be an object",
                }
            }
        )
        return summary

    # 兼容 direct artifact、summary wrapper、latest_status 和 diagnostics nested summary。
    summary_fragment = {}
    for candidate in (
        replay.get("wave_rover_feedback_replay_summary"),
        replay.get("robot_diagnostics_summary"),
        replay.get("diagnostics_summary"),
        replay.get("phone_safe_summary"),
        replay.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _wave_rover_feedback_replay_source_contract(replay)
    status_source = (
        replay.get("feedback_replay_status")
        if isinstance(replay.get("feedback_replay_status"), dict)
        else replay.get("replay_status")
        if isinstance(replay.get("replay_status"), dict)
        else summary_fragment.get("feedback_replay_status")
        if isinstance(summary_fragment.get("feedback_replay_status"), dict)
        else summary_fragment.get("replay_status")
        if isinstance(summary_fragment.get("replay_status"), dict)
        else {}
    )
    feedback_alignment = (
        replay.get("feedback_alignment")
        if isinstance(replay.get("feedback_alignment"), dict)
        else summary_fragment.get("feedback_alignment")
        if isinstance(summary_fragment.get("feedback_alignment"), dict)
        else {"verdict": replay.get("feedback_alignment_verdict") or summary_fragment.get("feedback_alignment_verdict") or "not_proven"}
    )
    interval_alignment = (
        replay.get("interval_alignment")
        if isinstance(replay.get("interval_alignment"), dict)
        else summary_fragment.get("interval_alignment")
        if isinstance(summary_fragment.get("interval_alignment"), dict)
        else {"verdict": replay.get("interval_alignment_verdict") or summary_fragment.get("interval_alignment_verdict") or "not_proven"}
    )
    topic_alignment = (
        replay.get("topic_alignment")
        if isinstance(replay.get("topic_alignment"), dict)
        else summary_fragment.get("topic_alignment")
        if isinstance(summary_fragment.get("topic_alignment"), dict)
        else {"verdict": replay.get("topic_alignment_verdict") or summary_fragment.get("topic_alignment_verdict") or "not_proven"}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": replay.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "feedback_replay_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or replay.get("status")
                    or "blocked"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or replay.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or replay.get("reason")
                    or "WAVE ROVER feedback replay consumed without real HIL evidence"
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or replay.get("safe_evidence_ref")
                or replay.get("evidence_ref", "")
            ),
            "feedback_alignment": _safe_pc_route_debug_value(feedback_alignment),
            "interval_alignment": _safe_pc_route_debug_value(interval_alignment),
            "topic_alignment": _safe_pc_route_debug_value(topic_alignment),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                replay.get("next_required_evidence")
                if isinstance(replay.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "not_proven": _wave_rover_feedback_replay_not_proven(replay, summary_fragment),
            "boundary": WAVE_ROVER_FEEDBACK_REPLAY_GATE,
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "real_wave_rover_feedback": False,
            "real_serial_or_uart_feedback": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        WAVE_ROVER_FEEDBACK_REPLAY_SCHEMA,
        WAVE_ROVER_FEEDBACK_REPLAY_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != WAVE_ROVER_FEEDBACK_REPLAY_GATE:
        summary.update(
            {
                "feedback_replay_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "WAVE ROVER feedback replay schema or evidence boundary is unsupported",
                },
                "feedback_alignment": {"verdict": "not_proven"},
                "interval_alignment": {"verdict": "not_proven"},
                "topic_alignment": {"verdict": "not_proven"},
                "next_required_evidence": [],
            }
        )
        return summary

    if (
        not _wave_rover_feedback_replay_has_not_proven(replay, summary_fragment)
        or not _wave_rover_feedback_replay_has_disabled_actions(replay, summary_fragment)
        or _wave_rover_feedback_replay_has_unsafe_fields(replay)
    ):
        summary.update(
            {
                "feedback_replay_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "WAVE ROVER feedback replay contains unsafe fields, missing not_proven, or success/control claims",
                },
                "feedback_alignment": {"verdict": "not_proven"},
                "interval_alignment": {"verdict": "not_proven"},
                "topic_alignment": {"verdict": "not_proven"},
                "next_required_evidence": [],
            }
        )
        return summary

    return summary


def summarize_wave_rover_hil_packet_intake(source):
    """构建 WAVE ROVER HIL packet intake 的 metadata-only diagnostics 摘要。"""
    # Robot 只消费 PC gate 的安全摘要；这里不读串口、不订阅 ROS topic、不触发 Start/Confirm/Cancel。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_wave_rover_hil_packet_intake_summary(
        source_path,
        read_error="WAVE ROVER HIL packet intake summary is not configured",
    )
    if isinstance(source, dict):
        packet = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "packet_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "WAVE ROVER HIL packet intake artifact missing",
                    },
                    "read_error": "WAVE ROVER HIL packet intake artifact missing",
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                packet = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading WAVE ROVER HIL packet intake summary: {exc}"
            )
            summary.update(
                {
                    "packet_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                    },
                    "read_error": safe_error,
                }
            )
            return summary

    if not isinstance(packet, dict):
        summary.update(
            {
                "packet_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "WAVE ROVER HIL packet intake JSON must be an object",
                }
            }
        )
        return summary

    # 兼容 top-level、summary alias、Robot-compatible summary 和 nested diagnostics/summary。
    summary_fragment = {}
    for candidate in (
        packet.get("wave_rover_hil_packet_intake_summary"),
        packet.get("robot_diagnostics_summary"),
        packet.get("robot_diagnostics_wave_rover_hil_packet_intake_summary"),
        packet.get("diagnostics_summary"),
        packet.get("phone_safe_summary"),
        packet.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _wave_rover_hil_packet_intake_source_contract(packet)
    packet_status = (
        packet.get("packet_status")
        if isinstance(packet.get("packet_status"), dict)
        else summary_fragment.get("packet_status")
        if isinstance(summary_fragment.get("packet_status"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": packet.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "overall_status": "not_proven",
            "packet_status": {
                "status": _redact_route_task_rehearsal_text(
                    packet_status.get("status")
                    or summary_fragment.get("packet_status")
                    or packet.get("packet_status")
                    or "blocked"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    packet_status.get("verdict")
                    or summary_fragment.get("overall_status")
                    or packet.get("overall_status")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    packet_status.get("reason")
                    or summary_fragment.get("reason")
                    or packet.get("reason")
                    or "WAVE ROVER HIL packet intake consumed without real HIL evidence"
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or packet.get("safe_evidence_ref")
                or packet.get("evidence_ref", "")
            ),
            "required_files": _safe_route_task_rehearsal_list(
                packet.get("required_files")
                if isinstance(packet.get("required_files"), list)
                else summary_fragment.get("required_files")
            ),
            "missing_files": _safe_route_task_rehearsal_list(
                packet.get("missing_files")
                if isinstance(packet.get("missing_files"), list)
                else summary_fragment.get("missing_files")
            ),
            "operator_report_status": _redact_route_task_rehearsal_text(
                packet.get("operator_report_status")
                or summary_fragment.get("operator_report_status")
                or "not_proven"
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                packet.get("next_required_evidence")
                if isinstance(packet.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "not_proven": _wave_rover_hil_packet_intake_not_proven(packet, summary_fragment),
            "boundary": WAVE_ROVER_HIL_PACKET_INTAKE_GATE,
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "real_wave_rover": False,
            "real_uart": False,
            "real_odom": False,
            "real_imu": False,
            "real_battery": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        WAVE_ROVER_HIL_PACKET_INTAKE_SCHEMA,
        WAVE_ROVER_HIL_PACKET_INTAKE_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != WAVE_ROVER_HIL_PACKET_INTAKE_GATE:
        summary.update(
            {
                "packet_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "WAVE ROVER HIL packet intake schema or evidence boundary is unsupported",
                },
                "required_files": [],
                "missing_files": [],
                "next_required_evidence": [],
            }
        )
        return summary

    if (
        not _wave_rover_hil_packet_intake_has_not_proven(packet, summary_fragment)
        or not _wave_rover_hil_packet_intake_has_disabled_actions(packet, summary_fragment)
        or not _wave_rover_hil_packet_intake_same_evidence_ref_ok(packet, summary_fragment)
        or _wave_rover_hil_packet_intake_has_unsafe_fields(packet)
    ):
        summary.update(
            {
                "packet_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "WAVE ROVER HIL packet intake contains unsafe fields, missing "
                        "not_proven, evidence_ref mismatch, or success/control claims"
                    ),
                },
                "required_files": [],
                "missing_files": [],
                "next_required_evidence": [],
            }
        )
        return summary

    return summary


def summarize_wave_rover_hil_packet_review_decision(source):
    """构建 WAVE ROVER HIL packet review decision 的 metadata-only diagnostics 摘要。"""
    # Robot 只读取 PC gate 的 review 结论；这里不打开 raw packet、不运行串口、不发布任何控制命令。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_wave_rover_hil_packet_review_decision_summary(
        source_path,
        read_error="WAVE ROVER HIL packet review decision summary is not configured",
    )
    if isinstance(source, dict):
        decision = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "WAVE ROVER HIL packet review decision artifact missing",
                    },
                    "read_error": "WAVE ROVER HIL packet review decision artifact missing",
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading WAVE ROVER HIL packet review decision summary: {exc}"
            )
            summary.update(
                {
                    "review_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                    },
                    "read_error": safe_error,
                }
            )
            return summary

    if not isinstance(decision, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "WAVE ROVER HIL packet review decision JSON must be an object",
                }
            }
        )
        return summary

    # 兼容 direct artifact、summary alias、Robot-compatible summary 和 nested diagnostics/summary。
    summary_fragment = {}
    for candidate in (
        decision.get("wave_rover_hil_packet_review_decision_summary"),
        decision.get("robot_diagnostics_summary"),
        decision.get("robot_diagnostics_wave_rover_hil_packet_review_decision_summary"),
        decision.get("diagnostics_summary"),
        decision.get("phone_safe_summary"),
        decision.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _wave_rover_hil_packet_review_decision_source_contract(decision)
    review_status = (
        decision.get("review_status")
        if isinstance(decision.get("review_status"), dict)
        else summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": decision.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "overall_status": "not_proven",
            "review_status": {
                "status": _redact_route_task_rehearsal_text(
                    review_status.get("status")
                    or summary_fragment.get("overall_status")
                    or decision.get("overall_status")
                    or "blocked"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    review_status.get("verdict")
                    or summary_fragment.get("verdict")
                    or decision.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    review_status.get("reason")
                    or summary_fragment.get("reason")
                    or decision.get("reason")
                    or "WAVE ROVER HIL packet review decision consumed without real HIL evidence"
                ),
            },
            "review_decision": _redact_route_task_rehearsal_text(
                summary_fragment.get("review_decision")
                or decision.get("review_decision")
                or "blocked_not_proven"
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or decision.get("safe_evidence_ref")
                or decision.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": True,
            "accepted_required_materials": _safe_route_task_rehearsal_list(
                decision.get("accepted_required_materials")
                if isinstance(decision.get("accepted_required_materials"), list)
                else summary_fragment.get("accepted_required_materials")
            ),
            "missing_required_materials": _safe_route_task_rehearsal_list(
                decision.get("missing_required_materials")
                if isinstance(decision.get("missing_required_materials"), list)
                else summary_fragment.get("missing_required_materials")
            ),
            "rejected_required_materials": _safe_route_task_rehearsal_list(
                decision.get("rejected_required_materials")
                if isinstance(decision.get("rejected_required_materials"), list)
                else summary_fragment.get("rejected_required_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                decision.get("next_required_evidence")
                if isinstance(decision.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_pc_route_debug_value(
                decision.get("owner_handoff")
                if isinstance(decision.get("owner_handoff"), dict)
                else summary_fragment.get("owner_handoff")
                if isinstance(summary_fragment.get("owner_handoff"), dict)
                else {}
            ),
            "rerun_commands": _safe_route_task_rehearsal_list(
                decision.get("rerun_commands")
                if isinstance(decision.get("rerun_commands"), list)
                else summary_fragment.get("rerun_commands")
            ),
            "not_proven": _wave_rover_hil_packet_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "boundary": WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_GATE,
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "real_wave_rover": False,
            "real_uart": False,
            "real_odom": False,
            "real_imu": False,
            "real_battery": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_SCHEMA,
        WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_GATE:
        summary.update(
            {
                "review_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "WAVE ROVER HIL packet review decision schema or evidence boundary is unsupported",
                },
                "review_decision": "blocked_unsupported_schema",
                "accepted_required_materials": [],
                "missing_required_materials": [],
                "rejected_required_materials": [],
                "next_required_evidence": [],
                "owner_handoff": {},
                "rerun_commands": [],
            }
        )
        return summary

    if (
        not _wave_rover_hil_packet_review_decision_has_not_proven(decision, summary_fragment)
        or not _wave_rover_hil_packet_review_decision_has_disabled_actions(decision, summary_fragment)
        or not _wave_rover_hil_packet_review_decision_same_evidence_ref_ok(
            decision,
            summary_fragment,
        )
        or _wave_rover_hil_packet_review_decision_has_unsafe_fields(decision)
    ):
        summary.update(
            {
                "review_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": (
                        "WAVE ROVER HIL packet review decision contains unsafe fields, "
                        "missing not_proven, evidence_ref mismatch, or success/control claims"
                    ),
                },
                "review_decision": "blocked_unsafe_fields",
                "accepted_required_materials": [],
                "missing_required_materials": [],
                "rejected_required_materials": [],
                "next_required_evidence": [],
                "owner_handoff": {},
                "rerun_commands": [],
            }
        )
        return summary

    return summary


def summarize_wave_rover_hil_packet_execution_pack(source):
    """构建 WAVE ROVER HIL packet execution pack 的 metadata-only diagnostics 摘要。"""
    # Robot diagnostics 只展示 Hardware worker 已消毒摘要；不得读取 raw packet、打开 UART 或触发主动作。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_wave_rover_hil_packet_execution_pack_summary(
        source_path,
        read_error="WAVE ROVER HIL packet execution pack is not configured",
    )
    if isinstance(source, dict):
        pack = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "execution_pack_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": "WAVE ROVER HIL packet execution pack artifact missing",
                    },
                    "read_error": "WAVE ROVER HIL packet execution pack artifact missing",
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                pack = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading WAVE ROVER HIL packet execution pack: {exc}"
            )
            summary.update(
                {
                    "execution_pack_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": safe_error,
                    },
                    "read_error": safe_error,
                }
            )
            return summary

    if not isinstance(pack, dict):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "WAVE ROVER HIL packet execution pack JSON must be an object",
                }
            }
        )
        return summary

    diagnostics = pack.get("diagnostics") if isinstance(pack.get("diagnostics"), dict) else {}
    # Hardware worker 可能给 direct artifact、summary alias 或 nested diagnostics；这里只复制白名单字段。
    summary_fragment = {}
    for candidate in (
        pack.get("wave_rover_hil_packet_execution_pack_summary"),
        pack.get("wave_rover_hil_packet_execution_pack"),
        pack.get("robot_diagnostics_summary"),
        pack.get("robot_diagnostics_wave_rover_hil_packet_execution_pack_summary"),
        pack.get("diagnostics_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("wave_rover_hil_packet_execution_pack_summary"),
        pack.get("phone_safe_summary"),
        pack.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _wave_rover_hil_packet_execution_pack_source_contract(
        pack
    )
    if not source_schema and summary_fragment:
        source_schema, source_boundary = _wave_rover_hil_packet_execution_pack_source_contract(
            summary_fragment
        )
    status_source = (
        pack.get("execution_pack_status")
        if isinstance(pack.get("execution_pack_status"), dict)
        else summary_fragment.get("execution_pack_status")
        if isinstance(summary_fragment.get("execution_pack_status"), dict)
        else {}
    )
    status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("execution_pack_status")
        or summary_fragment.get("overall_status")
        or pack.get("overall_status")
        or "blocked"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_robot_copy")
        or summary_fragment.get("safe_copy")
        or pack.get("safe_robot_copy")
        or pack.get("safe_copy")
        or (
            "WAVE ROVER HIL packet execution pack is metadata-only; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags"))
    if not boundary_flags and isinstance(pack.get("boundary_flags"), dict):
        boundary_flags = _safe_pc_route_debug_dict(pack.get("boundary_flags"))
    # 即便来源缺少部分 false 字段，Robot 输出也强制补齐完整 fail-closed 栅栏。
    boundary_flags.update(
        {
            "metadata_only": True,
            "real_hardware_observed": False,
            "real_wave_rover": False,
            "real_uart": False,
            "real_feedback_T1001": False,
            "real_odom": False,
            "real_imu": False,
            "real_battery": False,
            "hil_pass": False,
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
            "production_ready": False,
        }
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": pack.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "overall_status": "not_proven",
            "execution_pack_status": {
                "status": status or "blocked",
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or pack.get("verdict")
                    or "not_proven"
                ),
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or pack.get("reason")
                    or "WAVE ROVER HIL packet execution pack consumed without real HIL evidence"
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or pack.get("safe_evidence_ref")
                or pack.get("evidence_ref", "")
            ),
            "required_material_templates": _safe_pc_route_debug_value(
                pack.get("required_material_templates")
                if "required_material_templates" in pack
                else summary_fragment.get("required_material_templates")
            )
            or [],
            "collection_sequence": _safe_pc_route_debug_value(
                pack.get("collection_sequence")
                if "collection_sequence" in pack
                else summary_fragment.get("collection_sequence")
            )
            or [],
            "owner_handoff": _safe_pc_route_debug_value(
                pack.get("owner_handoff")
                if "owner_handoff" in pack
                else summary_fragment.get("owner_handoff")
            )
            or {},
            "rerun_commands": _safe_route_task_rehearsal_list(
                pack.get("rerun_commands")
                if isinstance(pack.get("rerun_commands"), list)
                else summary_fragment.get("rerun_commands")
            ),
            "boundary_flags": boundary_flags,
            "not_proven": _wave_rover_hil_packet_execution_pack_not_proven(
                pack,
                summary_fragment,
            ),
            "boundary": WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_GATE,
            "read_error": "",
            "safe_robot_copy": safe_copy,
            "metadata_only": True,
            "real_hardware_observed": False,
            "real_wave_rover": False,
            "real_uart": False,
            "real_feedback_T1001": False,
            "real_odom": False,
            "real_imu": False,
            "real_battery": False,
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
    )

    accepted_schemas = {
        WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_SCHEMA,
        WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_GATE:
        summary.update(
            {
                "execution_pack_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "WAVE ROVER HIL packet execution pack schema or evidence boundary is unsupported",
                },
                "required_material_templates": [],
                "collection_sequence": [],
                "owner_handoff": {},
                "rerun_commands": [],
                "safe_robot_copy": (
                    "WAVE ROVER HIL packet execution pack was blocked because the source "
                    "contained unsafe raw material, enabled actions, or success/HIL claims."
                ),
            }
        )
        return summary

    if (
        not _wave_rover_hil_packet_execution_pack_has_disabled_actions(
            pack,
            summary_fragment,
        )
        or _wave_rover_hil_packet_review_decision_has_unsafe_fields(pack)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": (
                        "WAVE ROVER HIL packet execution pack contains unsafe fields, "
                        "raw material, enabled actions, or success/HIL claims"
                    ),
                },
                "required_material_templates": [],
                "collection_sequence": [],
                "owner_handoff": {},
                "rerun_commands": [],
                "safe_robot_copy": (
                    "WAVE ROVER HIL packet execution pack was blocked because the source "
                    "contained unsafe raw material, enabled actions, or success/HIL claims."
                ),
            }
        )
        return summary

    return summary


def summarize_wave_rover_hil_packet_collection_drill(source):
    """构建 WAVE ROVER HIL packet collection drill 的 metadata-only diagnostics 摘要。"""
    # Robot 只复制 Hardware gate 的安全摘要；不得打开串口、发布 /cmd_vel 或发送 WAVE ROVER JSON。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_wave_rover_hil_packet_collection_drill_summary(
        source_path,
        read_error="WAVE ROVER HIL packet collection drill is not configured",
    )
    if isinstance(source, dict):
        drill = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "collection_drill_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": "WAVE ROVER HIL packet collection drill artifact missing",
                    },
                    "read_error": "WAVE ROVER HIL packet collection drill artifact missing",
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                drill = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading WAVE ROVER HIL packet collection drill: {exc}"
            )
            summary.update(
                {
                    "collection_drill_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": safe_error,
                    },
                    "read_error": safe_error,
                }
            )
            return summary

    if not isinstance(drill, dict):
        summary.update(
            {
                "collection_drill_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "WAVE ROVER HIL packet collection drill JSON must be an object",
                }
            }
        )
        return summary

    diagnostics = drill.get("diagnostics") if isinstance(drill.get("diagnostics"), dict) else {}
    # 支持 direct artifact、兼容 summary 和 diagnostics wrapper；输出仍只保留白名单字段。
    summary_fragment = {}
    for candidate in (
        drill.get("wave_rover_hil_packet_collection_drill_summary"),
        drill.get("wave_rover_hil_packet_collection_drill"),
        drill.get("robot_diagnostics_summary"),
        drill.get("robot_diagnostics_wave_rover_hil_packet_collection_drill_summary"),
        drill.get("diagnostics_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("wave_rover_hil_packet_collection_drill_summary"),
        drill.get("phone_safe_summary"),
        drill.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    source_schema, source_boundary = _wave_rover_hil_packet_collection_drill_source_contract(
        drill
    )
    if not source_schema and summary_fragment:
        source_schema, source_boundary = _wave_rover_hil_packet_collection_drill_source_contract(
            summary_fragment
        )
    status_source = (
        drill.get("collection_drill_status")
        if isinstance(drill.get("collection_drill_status"), dict)
        else summary_fragment.get("collection_drill_status")
        if isinstance(summary_fragment.get("collection_drill_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_robot_copy")
        or summary_fragment.get("safe_copy")
        or drill.get("safe_robot_copy")
        or drill.get("safe_copy")
        or (
            "WAVE ROVER HIL packet collection drill is metadata-only; "
            "delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
        )
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags"))
    if not boundary_flags and isinstance(drill.get("boundary_flags"), dict):
        boundary_flags = _safe_pc_route_debug_dict(drill.get("boundary_flags"))
    # 不信任来源的 flag 完整性；Robot alias 强制覆盖为只读、不可控、未证明。
    boundary_flags.update(
        {
            "metadata_only": True,
            "real_hardware_observed": False,
            "real_wave_rover": False,
            "real_uart": False,
            "real_feedback_T1001": False,
            "real_odom": False,
            "real_imu": False,
            "real_battery": False,
            "hil_pass": False,
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
            "production_ready": False,
        }
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": drill.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "overall_status": "not_proven",
            "collection_drill_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("collection_drill_status")
                    or summary_fragment.get("overall_status")
                    or drill.get("overall_status")
                    or "blocked"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or drill.get("verdict")
                    or "not_proven"
                ),
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or drill.get("reason")
                    or "WAVE ROVER HIL packet collection drill consumed without real HIL evidence"
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or drill.get("safe_evidence_ref")
                or drill.get("evidence_ref", "")
            ),
            "required_material_templates": _safe_pc_route_debug_value(
                drill.get("required_material_templates")
                if "required_material_templates" in drill
                else summary_fragment.get("required_material_templates")
            )
            or [],
            "preflight_checklist": _safe_pc_route_debug_value(
                drill.get("preflight_checklist")
                if "preflight_checklist" in drill
                else summary_fragment.get("preflight_checklist")
            )
            or [],
            "collection_sequence": _safe_pc_route_debug_value(
                drill.get("collection_sequence")
                if "collection_sequence" in drill
                else summary_fragment.get("collection_sequence")
            )
            or [],
            "backfill_commands": _safe_route_task_rehearsal_list(
                drill.get("backfill_commands")
                if isinstance(drill.get("backfill_commands"), list)
                else summary_fragment.get("backfill_commands")
            ),
            "owner_handoff": _safe_pc_route_debug_value(
                drill.get("owner_handoff")
                if "owner_handoff" in drill
                else summary_fragment.get("owner_handoff")
            )
            or {},
            "blocked_reasons": _safe_route_task_rehearsal_list(
                drill.get("blocked_reasons")
                if isinstance(drill.get("blocked_reasons"), list)
                else summary_fragment.get("blocked_reasons")
            ),
            "boundary_flags": boundary_flags,
            "not_proven": _wave_rover_hil_packet_collection_drill_not_proven(
                drill,
                summary_fragment,
            ),
            "boundary": WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_GATE,
            "read_error": "",
            "safe_robot_copy": safe_copy,
            "metadata_only": True,
            "real_hardware_observed": False,
            "real_wave_rover": False,
            "real_uart": False,
            "real_feedback_T1001": False,
            "real_odom": False,
            "real_imu": False,
            "real_battery": False,
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
        }
    )

    accepted_schemas = {
        WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_SCHEMA,
        WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_GATE:
        summary.update(
            {
                "collection_drill_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "WAVE ROVER HIL packet collection drill schema or evidence boundary is unsupported",
                },
                "required_material_templates": [],
                "preflight_checklist": [],
                "collection_sequence": [],
                "backfill_commands": [],
                "owner_handoff": {},
                "blocked_reasons": ["unsupported_schema_or_boundary"],
                "safe_robot_copy": (
                    "WAVE ROVER HIL packet collection drill was blocked because the source "
                    "schema or proof boundary was not diagnostics-safe."
                ),
            }
        )
        return summary

    if (
        not _wave_rover_hil_packet_collection_drill_has_not_proven(
            drill,
            summary_fragment,
        )
        or not _wave_rover_hil_packet_collection_drill_has_disabled_actions(
            drill,
            summary_fragment,
        )
        or _wave_rover_hil_packet_review_decision_has_unsafe_fields(drill)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "collection_drill_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": (
                        "WAVE ROVER HIL packet collection drill contains unsafe fields, "
                        "missing not_proven, enabled actions, or success/control/HIL claims"
                    ),
                },
                "required_material_templates": [],
                "preflight_checklist": [],
                "collection_sequence": [],
                "backfill_commands": [],
                "owner_handoff": {},
                "blocked_reasons": ["unsafe_fields_or_enabled_actions"],
                "safe_robot_copy": (
                    "WAVE ROVER HIL packet collection drill was blocked because the source "
                    "contained unsafe raw material, enabled actions, or success/HIL claims."
                ),
            }
        )
        return summary

    return summary


def summarize_hardware_baseline_review(source):
    """构建 hardware baseline review 的 metadata-only diagnostics 摘要。"""
    # 支持 explicit ref、env path 和 latest_status/diagnostics dict；所有来源都只能进入白名单摘要字段。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_baseline_review_summary(
        source_path,
        read_error="hardware baseline review is not configured",
    )
    if isinstance(source, dict):
        review = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": "hardware baseline review artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware baseline review is missing; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware baseline review is missing; hardware_material_pending remains true.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                review = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware baseline review: {exc}"
            )
            summary.update(
                {
                    "review_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": safe_error,
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware baseline review could not be read; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware baseline review could not be read; hardware_material_pending remains true.",
                    },
                }
            )
            return summary

    if not isinstance(review, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware baseline review JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware baseline review shape is invalid; hardware_material_pending remains true.",
                    "safe_phone_copy": "Hardware baseline review shape is invalid; hardware_material_pending remains true.",
                },
            }
        )
        return summary

    # Autonomy/Hardware 可以给完整 artifact 或 summary wrapper；diagnostics 只读取可展示给操作员的摘要。
    summary_fragment = {}
    for candidate in (
        review.get("hardware_baseline_review_summary"),
        review.get("robot_diagnostics_summary"),
        review.get("diagnostics_summary"),
        review.get("mobile_readonly_summary"),
        review.get("phone_safe_summary"),
        review.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _hardware_baseline_review_source_contract(review)
    status_source = (
        review.get("review_status")
        if isinstance(review.get("review_status"), dict)
        else summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or review.get("safe_copy")
        or review.get("safe_phone_copy")
        or "Hardware baseline review is metadata-only; software_proof only, delivery_success=false."
    )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    review_summary = (
        review.get("review_summary")
        if isinstance(review.get("review_summary"), dict)
        else summary_fragment.get("review_summary")
        if isinstance(summary_fragment.get("review_summary"), dict)
        else {"status": review.get("status") or summary_fragment.get("status") or "hardware_material_pending"}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": review.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or review.get("status")
                    or "hardware_material_pending"
                ),
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or review.get("reason")
                    or "hardware baseline review consumed without real hardware evidence"
                ),
            },
            "hardware_material_status": "hardware_material_pending",
            "blockers": _safe_route_task_rehearsal_list(
                review.get("blockers")
                if isinstance(review.get("blockers"), list)
                else summary_fragment.get("blockers")
            )
            or ["hardware_material_pending"],
            "next_required_evidence": _safe_route_task_rehearsal_list(
                review.get("next_required_evidence")
                if isinstance(review.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "review_summary": _safe_pc_route_debug_value(review_summary),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or review.get("safe_evidence_ref")
                or review.get("evidence_ref", "")
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                review.get("operator_next_steps")
                if isinstance(review.get("operator_next_steps"), list)
                else summary_fragment.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": robot_summary,
            "not_proven": _hardware_baseline_review_not_proven(review, summary_fragment),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {HARDWARE_BASELINE_REVIEW_SCHEMA, HARDWARE_BASELINE_REVIEW_SUMMARY_SCHEMA}
    if source_schema not in accepted_schemas or source_boundary != HARDWARE_BASELINE_REVIEW_GATE:
        summary.update(
            {
                "review_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware baseline review schema or evidence boundary is unsupported",
                },
                "blockers": ["hardware_material_pending"],
                "next_required_evidence": [],
                "review_summary": {"status": "hardware_material_pending"},
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware baseline review is not a supported diagnostics source; no hardware or delivery result is proven.",
                    "safe_phone_copy": "Hardware baseline review is not a supported diagnostics source; no hardware or delivery result is proven.",
                },
            }
        )
        return summary

    if _mobile_field_material_intake_has_unsafe_fields(review) or _route_task_field_run_readiness_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "review_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware baseline review contains unsafe fields or success/control claims",
                },
                "blockers": ["hardware_material_pending"],
                "next_required_evidence": [],
                "review_summary": {"status": "hardware_material_pending"},
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware baseline review was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Hardware baseline review was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_hardware_baseline_source_alignment(source):
    """构建 hardware baseline source alignment 的 metadata-only diagnostics 摘要。"""
    # Hardware PC gate 可能给 artifact、summary 或 diagnostics nested dict；Robot 侧只抽取白名单摘要。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_baseline_source_alignment_summary(
        source_path,
        read_error="hardware baseline source alignment is not configured",
    )
    if isinstance(source, dict):
        alignment = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "alignment_status": {
                        "status": "blocked_missing_hardware_baseline_source_alignment",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": "hardware baseline source alignment artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware baseline source alignment is missing; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware baseline source alignment is missing; hardware_material_pending remains true.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                alignment = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware baseline source alignment: {exc}"
            )
            summary.update(
                {
                    "alignment_status": {
                        "status": "blocked_missing_hardware_baseline_source_alignment",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": safe_error,
                    },
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware baseline source alignment could not be read; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware baseline source alignment could not be read; hardware_material_pending remains true.",
                    },
                }
            )
            return summary

    if not isinstance(alignment, dict):
        summary.update(
            {
                "alignment_status": {
                    "status": "blocked_missing_hardware_baseline_source_alignment",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware baseline source alignment JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware baseline source alignment shape is invalid; hardware_material_pending remains true.",
                    "safe_phone_copy": "Hardware baseline source alignment shape is invalid; hardware_material_pending remains true.",
                },
            }
        )
        return summary

    # summary wrapper 和直接 artifact 都允许；所有可见字段都经过脱敏并强制保持 not_proven。
    summary_fragment = {}
    for candidate in (
        alignment.get("hardware_baseline_source_alignment_summary"),
        alignment.get("review_summary"),
        alignment.get("robot_diagnostics_summary"),
        alignment.get("diagnostics_summary"),
        alignment.get("phone_safe_summary"),
        alignment.get("mobile_readonly_summary"),
        alignment.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _hardware_baseline_source_alignment_source_contract(alignment)
    status_source = (
        alignment.get("alignment_status")
        if isinstance(alignment.get("alignment_status"), dict)
        else summary_fragment.get("alignment_status")
        if isinstance(summary_fragment.get("alignment_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or alignment.get("safe_copy")
        or alignment.get("safe_phone_copy")
        or "Hardware baseline source alignment is metadata-only; software_proof only, delivery_success=false."
    )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    baseline_source_summary = (
        alignment.get("baseline_source_summary")
        if isinstance(alignment.get("baseline_source_summary"), dict)
        else summary_fragment.get("baseline_source_summary")
        if isinstance(summary_fragment.get("baseline_source_summary"), dict)
        else {"status": alignment.get("status") or summary_fragment.get("status") or "hardware_material_pending"}
    )
    source_alignment_status = _hardware_baseline_source_alignment_status(
        alignment, summary_fragment, status_source
    )
    default_hardware_set_summary = _hardware_baseline_source_alignment_field(
        alignment, summary_fragment, "default_hardware_set_summary", {}
    )
    target_sensor_baseline_summary = _hardware_baseline_source_alignment_field(
        alignment, summary_fragment, "target_sensor_baseline_summary", {}
    )
    vendor_source_boundary = _hardware_baseline_source_alignment_field(
        alignment, summary_fragment, "vendor_source_boundary", {}
    )
    missing_alignment_items = _hardware_baseline_source_alignment_field(
        alignment, summary_fragment, "missing_alignment_items", []
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": alignment.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "alignment_status": {
                "status": source_alignment_status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or alignment.get("reason")
                    or "hardware baseline source alignment consumed without real hardware evidence"
                ),
            },
            "hardware_material_status": "hardware_material_pending",
            "source_alignment_status": source_alignment_status,
            "blockers": _safe_route_task_rehearsal_list(
                alignment.get("blockers")
                if isinstance(alignment.get("blockers"), list)
                else summary_fragment.get("blockers")
            )
            or ["hardware_material_pending"],
            "baseline_source_summary": _safe_pc_route_debug_value(baseline_source_summary),
            "default_hardware_set_summary": _safe_pc_route_debug_value(
                default_hardware_set_summary
                if isinstance(default_hardware_set_summary, dict)
                else {}
            ),
            "target_sensor_baseline_summary": _safe_pc_route_debug_value(
                target_sensor_baseline_summary
                if isinstance(target_sensor_baseline_summary, dict)
                else {}
            ),
            "vendor_source_boundary": _safe_pc_route_debug_value(
                vendor_source_boundary if isinstance(vendor_source_boundary, dict) else {}
            ),
            "missing_alignment_items": _safe_route_task_rehearsal_list(
                missing_alignment_items if isinstance(missing_alignment_items, list) else []
            ),
            "source_inventory_summary": _safe_pc_route_debug_value(
                alignment.get("source_inventory_summary")
                if isinstance(alignment.get("source_inventory_summary"), list)
                else summary_fragment.get("source_inventory_summary", [])
            ),
            "unresolved_sources": _safe_route_task_rehearsal_list(
                alignment.get("unresolved_sources")
                if isinstance(alignment.get("unresolved_sources"), list)
                else summary_fragment.get("unresolved_sources")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                alignment.get("owner_handoff")
                if isinstance(alignment.get("owner_handoff"), list)
                else summary_fragment.get("owner_handoff")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                alignment.get("next_required_evidence")
                if isinstance(alignment.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or alignment.get("safe_evidence_ref")
                or alignment.get("evidence_ref", "")
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                alignment.get("operator_next_steps")
                if isinstance(alignment.get("operator_next_steps"), list)
                else summary_fragment.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": robot_summary,
            "not_proven": _hardware_baseline_source_alignment_not_proven(
                alignment, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "source_alignment_reviewed": False,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "sensor_wiring_verified": False,
            "sensor_power_budget_verified": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        HARDWARE_BASELINE_SOURCE_ALIGNMENT_SCHEMA,
        HARDWARE_BASELINE_SOURCE_ALIGNMENT_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != HARDWARE_BASELINE_SOURCE_ALIGNMENT_GATE:
        summary.update(
            {
                "alignment_status": {
                    "status": "blocked_missing_hardware_baseline_source_alignment",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware baseline source alignment schema or evidence boundary is unsupported",
                },
                "source_alignment_status": "blocked_missing_hardware_baseline_source_alignment",
                "blockers": ["blocked_missing_hardware_baseline_source_alignment"],
                "baseline_source_summary": {
                    "status": "blocked_missing_hardware_baseline_source_alignment"
                },
                "default_hardware_set_summary": {},
                "target_sensor_baseline_summary": {},
                "vendor_source_boundary": {},
                "missing_alignment_items": [],
                "source_inventory_summary": [],
                "unresolved_sources": [],
                "owner_handoff": [],
                "next_required_evidence": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware baseline source alignment is not a supported diagnostics source; no hardware or delivery result is proven.",
                    "safe_phone_copy": "Hardware baseline source alignment is not a supported diagnostics source; no hardware or delivery result is proven.",
                },
            }
        )
        return summary

    if (
        _hardware_baseline_source_alignment_has_unsafe_fields(alignment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "alignment_status": {
                    "status": "blocked_missing_hardware_baseline_source_alignment",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware baseline source alignment contains unsafe fields or success/control claims",
                },
                "source_alignment_status": "blocked_missing_hardware_baseline_source_alignment",
                "blockers": ["blocked_missing_hardware_baseline_source_alignment"],
                "baseline_source_summary": {
                    "status": "blocked_missing_hardware_baseline_source_alignment"
                },
                "default_hardware_set_summary": {},
                "target_sensor_baseline_summary": {},
                "vendor_source_boundary": {},
                "missing_alignment_items": [],
                "source_inventory_summary": [],
                "unresolved_sources": [],
                "owner_handoff": [],
                "next_required_evidence": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware baseline source alignment was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Hardware baseline source alignment was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary

