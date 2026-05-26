"""Hardware sensor procurement and HIL-entry diagnostics metadata helpers.

本模块只迁移 operator gateway 的 hardware sensor procurement / HIL-entry
metadata-only 摘要逻辑。它不新增传感器选型、电压、引脚、UART、波特率、
底盘协议、固件、机械尺寸或真实 HIL 结论；硬件事实仍以 docs/vendor/
VENDOR_INDEX.md 指向的本地资料和后续实测 artifact 为准。
"""

import json
import os

from ros2_trashbot_behavior.operator_gateway_diagnostics_route_rehearsal import (
    _redact_route_task_rehearsal_text,
    _safe_pc_route_debug_dict,
    _safe_pc_route_debug_value,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_mobile_field import (
    _mobile_field_material_intake_has_unsafe_fields,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_task_field_retest import (
    _route_task_field_retest_execution_pack_has_success_wording,
)


def _diagnostics():
    # 延迟访问 facade 中尚未独立拆出的跨域守卫，避免模块初始化时形成循环导入。
    from ros2_trashbot_behavior import operator_gateway_diagnostics

    return operator_gateway_diagnostics


def _route_task_field_run_intake_has_unsafe_control_claims(value):
    # 控制授权判定继续复用 facade 的既有实现，保证 unsafe-control 语义不漂移。
    return _diagnostics()._route_task_field_run_intake_has_unsafe_control_claims(value)


def _route_task_field_run_readiness_copy_is_unsafe(value):
    # safe copy 敏感词规则是跨域契约，迁移本域时只委托，不复制第二份规则。
    return _diagnostics()._route_task_field_run_readiness_copy_is_unsafe(value)

__all__ = [
    "HARDWARE_SENSOR_PROCUREMENT_INTAKE_SCHEMA",
    "HARDWARE_SENSOR_PROCUREMENT_INTAKE_LEGACY_SCHEMA",
    "HARDWARE_SENSOR_PROCUREMENT_INTAKE_SUMMARY_SCHEMA",
    "HARDWARE_SENSOR_PROCUREMENT_INTAKE_GATE",
    "HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SCHEMA",
    "HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SUMMARY_SCHEMA",
    "HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_GATE",
    "HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SCHEMA",
    "HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SUMMARY_SCHEMA",
    "HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_GATE",
    "HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SCHEMA",
    "HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SUMMARY_SCHEMA",
    "HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_GATE",
    "HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SUMMARY_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_GATE",
    "HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_SUMMARY_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_GATE",
    "HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_SUMMARY_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_GATE",
    "HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_SUMMARY_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_GATE",
    "HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_GATE",
    "HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_GATE",
    "_hardware_sensor_procurement_intake_not_proven",
    "_hardware_sensor_procurement_review_decision_not_proven",
    "_hardware_sensor_procurement_execution_pack_not_proven",
    "_hardware_sensor_procurement_receipt_intake_not_proven",
    "_hardware_sensor_hil_entry_config_precheck_not_proven",
    "_hardware_sensor_hil_entry_readiness_review_not_proven",
    "_hardware_sensor_hil_entry_execution_pack_not_proven",
    "_hardware_sensor_hil_entry_callback_intake_not_proven",
    "_hardware_sensor_hil_entry_callback_review_decision_not_proven",
    "_hardware_sensor_hil_entry_callback_review_handoff_not_proven",
    "_default_hardware_sensor_procurement_intake_summary",
    "_default_hardware_sensor_procurement_review_decision_summary",
    "_default_hardware_sensor_procurement_execution_pack_summary",
    "_default_hardware_sensor_procurement_receipt_intake_summary",
    "_default_hardware_sensor_hil_entry_config_precheck_summary",
    "_default_hardware_sensor_hil_entry_readiness_review_summary",
    "_default_hardware_sensor_hil_entry_execution_pack_summary",
    "_default_hardware_sensor_hil_entry_callback_intake_summary",
    "_default_hardware_sensor_hil_entry_callback_review_decision_summary",
    "_default_hardware_sensor_hil_entry_callback_review_handoff_summary",
    "_hardware_sensor_procurement_intake_source_contract",
    "_hardware_sensor_procurement_review_decision_source_contract",
    "_hardware_sensor_procurement_execution_pack_source_contract",
    "_hardware_sensor_procurement_receipt_intake_source_contract",
    "_hardware_sensor_hil_entry_config_precheck_source_contract",
    "_hardware_sensor_hil_entry_readiness_review_source_contract",
    "_hardware_sensor_hil_entry_execution_pack_source_contract",
    "_hardware_sensor_hil_entry_callback_intake_source_contract",
    "_hardware_sensor_hil_entry_callback_review_decision_source_contract",
    "_hardware_sensor_hil_entry_callback_review_handoff_source_contract",
    "summarize_hardware_sensor_procurement_intake",
    "summarize_hardware_sensor_procurement_review_decision",
    "summarize_hardware_sensor_procurement_execution_pack",
    "summarize_hardware_sensor_procurement_receipt_intake",
    "summarize_hardware_sensor_hil_entry_config_precheck",
    "summarize_hardware_sensor_hil_entry_readiness_review",
    "summarize_hardware_sensor_hil_entry_execution_pack",
    "summarize_hardware_sensor_hil_entry_callback_intake",
    "summarize_hardware_sensor_hil_entry_callback_review_decision",
    "summarize_hardware_sensor_hil_entry_callback_review_handoff",
]

HARDWARE_SENSOR_PROCUREMENT_INTAKE_SCHEMA = "trashbot.hardware_sensor_procurement_intake_gate.v1"
HARDWARE_SENSOR_PROCUREMENT_INTAKE_LEGACY_SCHEMA = "trashbot.hardware_sensor_procurement_intake.v1"
HARDWARE_SENSOR_PROCUREMENT_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.hardware_sensor_procurement_intake_summary.v1"
)
HARDWARE_SENSOR_PROCUREMENT_INTAKE_GATE = (
    "software_proof_docker_hardware_sensor_procurement_intake_gate"
)
HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SCHEMA = (
    "trashbot.hardware_sensor_procurement_review_decision.v1"
)
HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.hardware_sensor_procurement_review_decision_summary.v1"
)
HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_GATE = (
    "software_proof_docker_hardware_sensor_procurement_review_decision_gate"
)
HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SCHEMA = (
    "trashbot.hardware_sensor_procurement_execution_pack.v1"
)
HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SUMMARY_SCHEMA = (
    "trashbot.hardware_sensor_procurement_execution_pack_summary.v1"
)
HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_GATE = (
    "software_proof_docker_hardware_sensor_procurement_execution_pack_gate"
)
HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SCHEMA = (
    "trashbot.hardware_sensor_procurement_receipt_intake.v1"
)
HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.hardware_sensor_procurement_receipt_intake_summary.v1"
)
HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_GATE = (
    "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate"
)
HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_config_precheck.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SUMMARY_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_GATE = (
    "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate"
)
HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_readiness_review.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_SUMMARY_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_readiness_review_summary.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_GATE = (
    "software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate"
)
HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_execution_pack.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_SUMMARY_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_execution_pack_summary.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_GATE = (
    "software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate"
)
HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_callback_intake.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_callback_intake_summary.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_GATE = (
    "software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate"
)
HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_callback_review_decision.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_callback_review_decision_summary.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate"
)
HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_callback_review_handoff.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.hardware_sensor_hil_entry_callback_review_handoff_summary.v1"
)
HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate"
)


def _hardware_sensor_procurement_intake_not_proven(intake=None, summary_fragment=None):
    # 采购 intake 只说明候选传感器材料仍在软件门禁内；真实采购、装机、Nav2 和 HIL 必须另有证据。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(intake.get("not_proven"), list):
        source_values.extend(intake.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
        "real_sensor_device_proof",
        "sensor_procurement_completed",
        "sensor_installed_on_robot",
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


def _hardware_sensor_procurement_review_decision_not_proven(review=None, summary_fragment=None):
    # review decision 只把采购评审结论带进 Robot diagnostics；不能把批准/驳回误读成真实采购或装机完成。
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
        "sensor_procurement_completed",
        "sensor_installed_on_robot",
        "real_sensor_device_proof",
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


def _hardware_sensor_procurement_execution_pack_not_proven(pack=None, summary_fragment=None):
    # execution pack 只能证明执行材料已被整理；不能证明 SKU 采购、传感器装机、校准或机器人闭环。
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
        "software_proof",
        "hardware_material_pending",
        "sensor_procurement_completed",
        "sensor_installed_on_robot",
        "sensor_calibrated_on_robot",
        "real_sensor_device_proof",
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


def _hardware_sensor_procurement_receipt_intake_not_proven(receipt=None, summary_fragment=None):
    # receipt intake 只把收货回填材料带到 Robot diagnostics；真实采购、收货、装机、校准和 HIL 仍必须另证。
    receipt = receipt if isinstance(receipt, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(receipt.get("not_proven"), list):
        source_values.extend(receipt.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
        "sensor_receipt_verified",
        "sensor_procurement_completed",
        "sensor_installed_on_robot",
        "sensor_wiring_verified",
        "sensor_power_budget_verified",
        "sensor_calibrated_on_robot",
        "real_sensor_device_proof",
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


def _hardware_sensor_hil_entry_config_precheck_not_proven(precheck=None, summary_fragment=None):
    # HIL-entry config precheck 只证明未来上车配置材料的参数化完整性，不能证明传感器、接线、校准或 HIL。
    precheck = precheck if isinstance(precheck, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(precheck.get("not_proven"), list):
        source_values.extend(precheck.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
        "sensor_config_precheck_only",
        "real_sensor_device_proof",
        "sensor_procurement_completed",
        "sensor_installed_on_robot",
        "sensor_wiring_verified",
        "sensor_power_budget_verified",
        "sensor_calibrated_on_robot",
        "real_nav2_fixed_route_run",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _hardware_sensor_hil_entry_readiness_review_not_proven(review=None, summary_fragment=None):
    # HIL-entry readiness review 只消费 Hardware 的评审摘要；真实装机、接线、校准和 HIL 必须另有现场证据。
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
        "sensor_hil_entry_readiness_review_only",
        "real_sensor_device_proof",
        "sensor_procurement_completed",
        "sensor_installed_on_robot",
        "sensor_wiring_verified",
        "sensor_power_budget_verified",
        "sensor_calibrated_on_robot",
        "real_nav2_fixed_route_run",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _hardware_sensor_hil_entry_execution_pack_not_proven(pack=None, summary_fragment=None):
    # HIL-entry execution pack 只把下一次实机准入执行材料带到 diagnostics；不能升级成 HIL pass 或控制授权。
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
        "software_proof",
        "hardware_material_pending",
        "sensor_hil_entry_execution_pack_only",
        "real_sensor_device_proof",
        "sensor_procurement_completed",
        "sensor_installed_on_robot",
        "sensor_wiring_verified",
        "sensor_power_budget_verified",
        "sensor_calibrated_on_robot",
        "hil_entry_execution_completed",
        "real_nav2_fixed_route_run",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _hardware_sensor_hil_entry_callback_intake_not_proven(intake=None, summary_fragment=None):
    # 回调 intake 只是 Hardware 现场回填后的安全摘要入口；Robot 不能据此打开动作或认定 HIL。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(intake.get("not_proven"), list):
        source_values.extend(intake.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
        "sensor_hil_entry_callback_intake_only",
        "real_sensor_device_proof",
        "sensor_procurement_completed",
        "sensor_installed_on_robot",
        "sensor_wiring_verified",
        "sensor_power_budget_verified",
        "sensor_calibrated_on_robot",
        "hil_entry_execution_completed",
        "real_nav2_fixed_route_run",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _hardware_sensor_hil_entry_callback_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # 回调复核决策只说明材料复核状态；accepted/missing/rejected 都不能升级为真实 HIL 或控制授权。
    decision = decision if isinstance(decision, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for source in (decision, summary_fragment):
        if isinstance(source.get("not_proven"), list):
            source_values.extend(source.get("not_proven"))
        for key in ("missing_materials", "rejected_materials", "next_required_evidence"):
            if isinstance(source.get(key), list):
                source_values.extend(source.get(key))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
        "sensor_hil_entry_callback_review_decision_only",
        "real_sensor_device_proof",
        "sensor_procurement_completed",
        "sensor_installed_on_robot",
        "sensor_wiring_verified",
        "sensor_power_budget_verified",
        "sensor_calibrated_on_robot",
        "hil_entry_execution_completed",
        "real_nav2_fixed_route_run",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _hardware_sensor_hil_entry_callback_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # 交接摘要只说明 owner 后续材料动作；Robot 不能把交接状态解释成 HIL、实物或控制已通过。
    handoff = handoff if isinstance(handoff, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for source in (handoff, summary_fragment):
        if isinstance(source.get("not_proven"), list):
            source_values.extend(source.get("not_proven"))
        for key in ("missing_materials", "next_required_evidence", "owner_handoff"):
            if isinstance(source.get(key), list):
                source_values.extend(source.get(key))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
        "sensor_hil_entry_callback_review_handoff_only",
        "real_sensor_device_proof",
        "sensor_procurement_completed",
        "sensor_installed_on_robot",
        "sensor_wiring_verified",
        "sensor_power_budget_verified",
        "sensor_calibrated_on_robot",
        "real_hil_pass",
        "route_elevator_field_pass",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _default_hardware_sensor_procurement_intake_summary(
    path,
    status="not_configured",
    read_error="",
):
    # procurement intake 是硬件采购材料的只读入口；默认必须封死动作、ACK、Nav2、HIL 和交付结论。
    return {
        "schema": HARDWARE_SENSOR_PROCUREMENT_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_SENSOR_PROCUREMENT_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "hardware sensor procurement intake is not configured",
        },
        "hardware_material_status": "hardware_material_pending",
        "blockers": ["hardware_material_pending"],
        "next_required_evidence": [],
        "procurement_summary": {
            "status": "hardware_material_pending",
            "reason": "hardware sensor procurement intake is not configured",
        },
        "sensor_responsibility_summary": [],
        "safe_evidence_ref": "",
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Hardware sensor procurement intake is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
            "safe_phone_copy": (
                "Hardware sensor procurement intake is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
        },
        "not_proven": _hardware_sensor_procurement_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
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


def _default_hardware_sensor_procurement_review_decision_summary(
    path,
    status="blocked_missing_hardware_sensor_procurement_review_decision",
    read_error="",
):
    # 缺失 review decision 时必须用明确 blocker fail closed，避免 Robot 侧把 intake 材料当成采购评审完成。
    return {
        "schema": HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_decision_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "hardware sensor procurement review decision is not configured",
        },
        "hardware_material_status": "hardware_material_pending",
        "blockers": ["blocked_missing_hardware_sensor_procurement_review_decision"],
        "next_required_evidence": [],
        "review_decision_summary": {
            "status": "blocked_missing_hardware_sensor_procurement_review_decision",
            "reason": "hardware sensor procurement review decision is not configured",
        },
        "owner_handoff": [],
        "rerun_commands": [],
        "safe_evidence_ref": "",
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Hardware sensor procurement review decision is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
            "safe_phone_copy": (
                "Hardware sensor procurement review decision is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
        },
        "not_proven": _hardware_sensor_procurement_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
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


def _default_hardware_sensor_procurement_execution_pack_summary(
    path,
    status="blocked_missing_hardware_sensor_procurement_execution_pack",
    read_error="",
):
    # 缺失 execution pack 时必须显式 fail closed；Robot 侧不能把 review decision 当成执行材料包。
    return {
        "schema": HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "execution_pack_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "hardware sensor procurement execution pack is not configured",
        },
        "hardware_material_status": "hardware_material_pending",
        "blockers": ["blocked_missing_hardware_sensor_procurement_execution_pack"],
        "material_templates": [],
        "owner_handoff": [],
        "rerun_commands": [],
        "blocked_reason": "hardware sensor procurement execution pack is not configured",
        "next_required_evidence": [],
        "safe_evidence_ref": "",
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Hardware sensor procurement execution pack is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
            "safe_phone_copy": (
                "Hardware sensor procurement execution pack is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
        },
        "not_proven": _hardware_sensor_procurement_execution_pack_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
        "sensor_calibrated_on_robot": False,
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


def _default_hardware_sensor_procurement_receipt_intake_summary(
    path,
    status="blocked_missing_hardware_sensor_procurement_receipt_intake",
    read_error="",
):
    # 缺失 receipt intake 时必须明确 fail closed；Robot 侧不能把执行包或收货回填入口误读成真实硬件到货。
    return {
        "schema": HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "receipt_intake_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "hardware sensor procurement receipt intake is not configured",
        },
        "hardware_material_status": "hardware_material_pending",
        "material_status": "hardware_material_pending",
        "blockers": ["blocked_missing_hardware_sensor_procurement_receipt_intake"],
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "owner_handoff": [],
        "next_required_evidence": [],
        "safe_evidence_ref": "",
        "operator_next_steps": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Hardware sensor procurement receipt intake is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
            "safe_phone_copy": (
                "Hardware sensor procurement receipt intake is metadata-only; "
                "software_proof only, delivery_success=false."
            ),
        },
        "not_proven": _hardware_sensor_procurement_receipt_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "sensor_receipt_verified": False,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
        "sensor_wiring_verified": False,
        "sensor_power_budget_verified": False,
        "sensor_calibrated_on_robot": False,
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


def _default_hardware_sensor_hil_entry_config_precheck_summary(
    path,
    status="blocked_missing_hardware_sensor_hil_entry_config_precheck",
    read_error="",
):
    # 缺失 config precheck 时必须 fail closed；Robot diagnostics 不能把未来 HIL 配置当成已验证硬件。
    return {
        "schema": HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {
            "schema": "",
            "evidence_boundary": "",
            "metadata_only": True,
        },
        "precheck_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "hardware sensor HIL-entry config precheck is not configured",
        },
        "hardware_material_status": "hardware_material_pending",
        "config_precheck_status": status,
        "blockers": ["blocked_missing_hardware_sensor_hil_entry_config_precheck"],
        "sensor_config_summary": {},
        "missing_config_categories": [],
        "missing_material_categories": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "safe_copy": (
            "Hardware sensor HIL-entry config precheck is metadata-only; "
            "software_proof only, delivery_success=false and primary_actions_enabled=false."
        ),
        "safe_evidence_ref": "",
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Hardware sensor HIL-entry config precheck is metadata-only; "
                "software_proof only, delivery_success=false and primary_actions_enabled=false."
            ),
            "safe_phone_copy": (
                "Hardware sensor HIL-entry config precheck is metadata-only; "
                "software_proof only, delivery_success=false and primary_actions_enabled=false."
            ),
        },
        "not_proven": _hardware_sensor_hil_entry_config_precheck_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "sensor_config_precheck_only": True,
        "sensor_config_validated_for_hil_entry": False,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
        "sensor_wiring_verified": False,
        "sensor_power_budget_verified": False,
        "sensor_calibrated_on_robot": False,
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


def _default_hardware_sensor_hil_entry_readiness_review_summary(
    path,
    status="blocked_missing_hardware_sensor_hil_entry_readiness_review",
    read_error="",
):
    # 缺失 readiness review 时必须 fail closed；Robot diagnostics 不能把评审入口误当成真实 HIL 入场通过。
    return {
        "schema": HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {
            "schema": "",
            "evidence_boundary": "",
            "metadata_only": True,
        },
        "readiness_review_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "hardware sensor HIL-entry readiness review is not configured",
        },
        "hardware_material_status": "hardware_material_pending",
        "review_status": status,
        "blockers": ["blocked_missing_hardware_sensor_hil_entry_readiness_review"],
        "readiness_gates": {},
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "rerun_commands": [],
        "safe_copy": (
            "Hardware sensor HIL-entry readiness review is metadata-only; "
            "software_proof only, delivery_success=false and primary_actions_enabled=false."
        ),
        "safe_evidence_ref": "",
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Hardware sensor HIL-entry readiness review is metadata-only; "
                "software_proof only, delivery_success=false and primary_actions_enabled=false."
            ),
            "safe_phone_copy": (
                "Hardware sensor HIL-entry readiness review is metadata-only; "
                "software_proof only, delivery_success=false and primary_actions_enabled=false."
            ),
        },
        "not_proven": _hardware_sensor_hil_entry_readiness_review_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "sensor_hil_entry_readiness_review_only": True,
        "sensor_hil_entry_ready": False,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
        "sensor_wiring_verified": False,
        "sensor_power_budget_verified": False,
        "sensor_calibrated_on_robot": False,
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


def _default_hardware_sensor_hil_entry_execution_pack_summary(
    path,
    status="blocked_missing_hardware_sensor_hil_entry_execution_pack",
    read_error="",
):
    # 缺失 execution pack 时必须 fail closed；Robot diagnostics 不能把准入执行包误当成真实 HIL 通过。
    return {
        "schema": HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {
            "schema": "",
            "evidence_boundary": "",
            "metadata_only": True,
        },
        "execution_pack_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "hardware sensor HIL-entry execution pack is not configured",
        },
        "hardware_material_status": "hardware_material_pending",
        "status": status,
        "required_materials": [],
        "missing_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "rerun_commands": [],
        "boundary": HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_GATE,
        "safe_copy": (
            "Hardware sensor HIL-entry execution pack is metadata-only; "
            "software_proof only, delivery_success=false and primary_actions_enabled=false."
        ),
        "safe_evidence_ref": "",
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Hardware sensor HIL-entry execution pack is metadata-only; "
                "software_proof only, delivery_success=false and primary_actions_enabled=false."
            ),
            "safe_phone_copy": (
                "Hardware sensor HIL-entry execution pack is metadata-only; "
                "software_proof only, delivery_success=false and primary_actions_enabled=false."
            ),
        },
        "not_proven": _hardware_sensor_hil_entry_execution_pack_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "sensor_hil_entry_execution_pack_only": True,
        "sensor_hil_entry_ready": False,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
        "sensor_wiring_verified": False,
        "sensor_power_budget_verified": False,
        "sensor_calibrated_on_robot": False,
        "hil_entry_execution_completed": False,
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


def _default_hardware_sensor_hil_entry_callback_intake_summary(
    path,
    status="blocked_missing_hardware_sensor_hil_entry_callback_intake",
    read_error="",
):
    # 缺少安全摘要时必须保守失败；callback intake 不能让 Robot 读取原始现场回调包。
    safe_copy = (
        "Hardware sensor HIL-entry callback intake is metadata-only; "
        "source=software_proof, hardware_material_pending, not_proven, "
        "delivery_success=false and primary_actions_enabled=false."
    )
    return {
        "schema": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {
            "schema": "",
            "evidence_boundary": "",
            "metadata_only": True,
        },
        "callback_intake_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "hardware sensor HIL-entry callback intake summary is not configured",
        },
        "source": "software_proof",
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "status": status,
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "rerun_commands": [],
        "boundary": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_GATE,
        "safe_copy": safe_copy,
        "safe_evidence_ref": "",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _hardware_sensor_hil_entry_callback_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "sensor_hil_entry_callback_intake_only": True,
        "sensor_hil_entry_ready": False,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
        "sensor_wiring_verified": False,
        "sensor_power_budget_verified": False,
        "sensor_calibrated_on_robot": False,
        "hil_entry_execution_completed": False,
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


def _default_hardware_sensor_hil_entry_callback_review_decision_summary(
    path,
    status="blocked_missing_hardware_sensor_hil_entry_callback_review_decision",
    read_error="",
):
    # 缺少复核决策时保持 blocked；Robot diagnostics 只能展示安全复核摘要，不能猜测材料已满足。
    reason = read_error or "hardware sensor HIL-entry callback review decision summary is not configured"
    safe_copy = (
        "Hardware sensor HIL-entry callback review decision is metadata-only; "
        "source=software_proof, hardware_material_pending, not_proven, "
        "delivery_success=false and primary_actions_enabled=false."
    )
    return {
        "schema": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {"schema": "", "evidence_boundary": "", "metadata_only": True},
        "review_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": reason,
        },
        "source": "software_proof",
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "status": status,
        "review_decision": "blocked",
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "decision_reasons": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "rerun_commands": [],
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "boundary": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_GATE,
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "safe_evidence_ref": "",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "status": "blocked",
            "reason": reason,
        },
        "not_proven": _hardware_sensor_hil_entry_callback_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "sensor_hil_entry_callback_review_decision_only": True,
        "sensor_hil_entry_ready": False,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
        "sensor_wiring_verified": False,
        "sensor_power_budget_verified": False,
        "sensor_calibrated_on_robot": False,
        "hil_entry_execution_completed": False,
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


def _default_hardware_sensor_hil_entry_callback_review_handoff_summary(
    path,
    status="blocked_missing_hardware_sensor_hil_entry_callback_review_handoff",
    read_error="",
):
    # 缺省状态必须 fail closed；没有 Hardware PC safe summary 时不暴露任何原始材料或控制入口。
    reason = read_error or "hardware sensor HIL-entry callback review handoff summary is not configured"
    safe_copy = (
        "Hardware sensor HIL-entry callback review handoff is metadata-only; "
        "source=software_proof, hardware_material_pending, not_proven, "
        "safe_to_control=false, delivery_success=false and primary_actions_enabled=false."
    )
    return {
        "schema": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {"schema": "", "evidence_boundary": "", "metadata_only": True},
        "handoff_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": reason,
        },
        "source_review_decision_status": {
            "status": "blocked",
            "verdict": "not_proven",
        },
        "source": "software_proof",
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "status": status,
        "handoff_decision": "blocked",
        "missing_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "rerun_guidance": [],
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "boundary": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_GATE,
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "safe_evidence_ref": "",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "status": "blocked",
            "reason": reason,
        },
        "not_proven": _hardware_sensor_hil_entry_callback_review_handoff_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_hardware_observed": False,
        "hardware_material_pending": True,
        "sensor_hil_entry_callback_review_handoff_only": True,
        "sensor_hil_entry_ready": False,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
        "sensor_wiring_verified": False,
        "sensor_power_budget_verified": False,
        "sensor_calibrated_on_robot": False,
        "hil_entry_execution_completed": False,
        "route_elevator_field_pass": False,
        "nav2_fixed_route_run": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "safe_to_control": False,
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


def _hardware_sensor_procurement_intake_source_contract(value):
    # 支持直接消费 PC gate artifact 或 summary；summary wrapper 仍必须落在同一 procurement intake boundary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_SENSOR_PROCUREMENT_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_sensor_procurement_review_decision_source_contract(value):
    # 支持直接 review decision artifact 或已消毒 summary；summary wrapper 仍必须保持同一 review boundary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_sensor_procurement_execution_pack_source_contract(value):
    # 支持直接 execution pack artifact 或 Robot diagnostics summary；wrapper 必须回指同一执行包 boundary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_sensor_procurement_receipt_intake_source_contract(value):
    # 支持直接 receipt intake artifact 或已消毒 summary；summary wrapper 必须回指同一 receipt intake gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_sensor_hil_entry_config_precheck_source_contract(value):
    # 支持直接 PC gate artifact 或已消毒 summary；summary wrapper 必须回指同一个 HIL-entry config precheck gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_sensor_hil_entry_readiness_review_source_contract(value):
    # 支持直接 readiness review artifact 或已消毒 summary；summary wrapper 必须回指同一 review gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_sensor_hil_entry_execution_pack_source_contract(value):
    # 支持直接 execution pack artifact 或已消毒 summary；wrapper 必须回指同一执行包 boundary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_sensor_hil_entry_callback_intake_source_contract(value):
    # 只接受回调 intake 的安全摘要或回指同一 boundary 的 wrapper，避免 Robot 读取原始现场材料。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_sensor_hil_entry_callback_review_decision_source_contract(value):
    # review-decision wrapper 必须回指同一 gate；Robot 不能把 callback intake 包装成复核结论。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _hardware_sensor_hil_entry_callback_review_handoff_source_contract(value):
    # handoff wrapper 必须回指 handoff gate；Robot 只消费 PC 侧消毒摘要，不接收 raw review/callback。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def summarize_hardware_sensor_procurement_intake(source):
    """构建 hardware sensor procurement intake 的 metadata-only diagnostics 摘要。"""
    # 这里只消费 Hardware gate 的白名单摘要；采购材料本体、vendor/source doc 和硬件路径不能进入 Robot diagnostics。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_sensor_procurement_intake_summary(
        source_path,
        read_error="hardware sensor procurement intake is not configured",
    )
    if isinstance(source, dict):
        intake = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "intake_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": "hardware sensor procurement intake artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor procurement intake is missing; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor procurement intake is missing; hardware_material_pending remains true.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware sensor procurement intake: {exc}"
            )
            summary.update(
                {
                    "intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": safe_error,
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor procurement intake could not be read; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor procurement intake could not be read; hardware_material_pending remains true.",
                    },
                }
            )
            return summary

    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor procurement intake JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement intake shape is invalid; hardware_material_pending remains true.",
                    "safe_phone_copy": "Hardware sensor procurement intake shape is invalid; hardware_material_pending remains true.",
                },
            }
        )
        return summary

    summary_fragment = {}
    for candidate in (
        intake.get("hardware_sensor_procurement_intake_summary"),
        intake.get("robot_diagnostics_summary"),
        intake.get("diagnostics_summary"),
        intake.get("phone_safe_summary"),
        intake.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _hardware_sensor_procurement_intake_source_contract(intake)
    status_source = (
        intake.get("intake_status")
        if isinstance(intake.get("intake_status"), dict)
        else summary_fragment.get("intake_status")
        if isinstance(summary_fragment.get("intake_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or intake.get("safe_copy")
        or intake.get("safe_phone_copy")
        or "Hardware sensor procurement intake is metadata-only; software_proof only, delivery_success=false."
    )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    procurement_summary = (
        intake.get("procurement_summary")
        if isinstance(intake.get("procurement_summary"), dict)
        else summary_fragment.get("procurement_summary")
        if isinstance(summary_fragment.get("procurement_summary"), dict)
        else {"status": intake.get("status") or summary_fragment.get("status") or "hardware_material_pending"}
    )
    sensor_rows = (
        intake.get("sensor_responsibility_summary")
        if isinstance(intake.get("sensor_responsibility_summary"), list)
        else summary_fragment.get("sensor_responsibility_summary")
        if isinstance(summary_fragment.get("sensor_responsibility_summary"), list)
        else []
    )
    safe_sensor_rows = []
    # 只保留采购/责任边界摘要字段；完整 vendor/source doc、硬件路径和原始配置由 Hardware gate 保管。
    for item in sensor_rows[:10]:
        if not isinstance(item, dict):
            continue
        safe_sensor_rows.append(
            {
                "sensor": _redact_route_task_rehearsal_text(item.get("sensor", "")),
                "material_status": _redact_route_task_rehearsal_text(
                    item.get("material_status") or item.get("status") or "hardware_material_pending"
                ),
                "field_status": _redact_route_task_rehearsal_text(
                    item.get("field_status") or "not_proven"
                ),
                "evidence_boundary": _redact_route_task_rehearsal_text(
                    item.get("evidence_boundary") or source_boundary
                ),
            }
        )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": intake.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "intake_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or intake.get("status")
                    or "hardware_material_pending"
                ),
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or intake.get("reason")
                    or "hardware sensor procurement intake consumed without real hardware evidence"
                ),
            },
            "hardware_material_status": "hardware_material_pending",
            "blockers": _safe_route_task_rehearsal_list(
                intake.get("blockers")
                if isinstance(intake.get("blockers"), list)
                else summary_fragment.get("blockers")
            )
            or ["hardware_material_pending"],
            "next_required_evidence": _safe_route_task_rehearsal_list(
                intake.get("next_required_evidence")
                if isinstance(intake.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "procurement_summary": _safe_pc_route_debug_value(procurement_summary),
            "sensor_responsibility_summary": safe_sensor_rows,
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or intake.get("safe_evidence_ref")
                or intake.get("evidence_ref", "")
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                intake.get("operator_next_steps")
                if isinstance(intake.get("operator_next_steps"), list)
                else summary_fragment.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": robot_summary,
            "not_proven": _hardware_sensor_procurement_intake_not_proven(intake, summary_fragment),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        HARDWARE_SENSOR_PROCUREMENT_INTAKE_SCHEMA,
        HARDWARE_SENSOR_PROCUREMENT_INTAKE_LEGACY_SCHEMA,
        HARDWARE_SENSOR_PROCUREMENT_INTAKE_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != HARDWARE_SENSOR_PROCUREMENT_INTAKE_GATE:
        summary.update(
            {
                "intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor procurement intake schema or evidence boundary is unsupported",
                },
                "blockers": ["hardware_material_pending"],
                "next_required_evidence": [],
                "procurement_summary": {"status": "hardware_material_pending"},
                "sensor_responsibility_summary": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement intake is not a supported diagnostics source; no hardware or delivery result is proven.",
                    "safe_phone_copy": "Hardware sensor procurement intake is not a supported diagnostics source; no hardware or delivery result is proven.",
                },
            }
        )
        return summary

    if _mobile_field_material_intake_has_unsafe_fields(intake) or _route_task_field_run_readiness_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "intake_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor procurement intake contains unsafe fields or success/control claims",
                },
                "blockers": ["hardware_material_pending"],
                "next_required_evidence": [],
                "procurement_summary": {"status": "hardware_material_pending"},
                "sensor_responsibility_summary": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement intake was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Hardware sensor procurement intake was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_hardware_sensor_procurement_review_decision(source):
    """构建 hardware sensor procurement review decision 的 metadata-only diagnostics 摘要。"""
    # Robot diagnostics 只读评审结论摘要；采购执行、装机、Nav2 和 HIL 仍必须由后续真实证据闭环。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_sensor_procurement_review_decision_summary(
        source_path,
        read_error="hardware sensor procurement review decision is not configured",
    )
    if isinstance(source, dict):
        review = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_decision_status": {
                        "status": "blocked_missing_hardware_sensor_procurement_review_decision",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": "hardware sensor procurement review decision artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor procurement review decision is missing; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor procurement review decision is missing; hardware_material_pending remains true.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                review = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware sensor procurement review decision: {exc}"
            )
            summary.update(
                {
                    "review_decision_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": safe_error,
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor procurement review decision could not be read; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor procurement review decision could not be read; hardware_material_pending remains true.",
                    },
                }
            )
            return summary

    if not isinstance(review, dict):
        summary.update(
            {
                "review_decision_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor procurement review decision JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement review decision shape is invalid; hardware_material_pending remains true.",
                    "safe_phone_copy": "Hardware sensor procurement review decision shape is invalid; hardware_material_pending remains true.",
                },
            }
        )
        return summary

    summary_fragment = {}
    for candidate in (
        review.get("hardware_sensor_procurement_review_decision_summary"),
        review.get("robot_diagnostics_summary"),
        review.get("diagnostics_summary"),
        review.get("phone_safe_summary"),
        review.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _hardware_sensor_procurement_review_decision_source_contract(review)
    status_source = (
        review.get("review_decision_status")
        if isinstance(review.get("review_decision_status"), dict)
        else summary_fragment.get("review_decision_status")
        if isinstance(summary_fragment.get("review_decision_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or review.get("safe_copy")
        or review.get("safe_phone_copy")
        or "Hardware sensor procurement review decision is metadata-only; software_proof only, delivery_success=false."
    )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    review_decision_summary = (
        review.get("review_decision_summary")
        if isinstance(review.get("review_decision_summary"), dict)
        else summary_fragment.get("review_decision_summary")
        if isinstance(summary_fragment.get("review_decision_summary"), dict)
        else {"status": review.get("status") or summary_fragment.get("status") or "hardware_material_pending"}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": review.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_decision_status": {
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
                    or "hardware sensor procurement review decision consumed without real hardware evidence"
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
            "review_decision_summary": _safe_pc_route_debug_value(review_decision_summary),
            "owner_handoff": _safe_route_task_rehearsal_list(
                review.get("owner_handoff")
                if isinstance(review.get("owner_handoff"), list)
                else summary_fragment.get("owner_handoff")
            ),
            "rerun_commands": _safe_route_task_rehearsal_list(
                review.get("rerun_commands")
                if isinstance(review.get("rerun_commands"), list)
                else summary_fragment.get("rerun_commands")
            ),
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
            "not_proven": _hardware_sensor_procurement_review_decision_not_proven(
                review, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SCHEMA,
        HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_GATE:
        summary.update(
            {
                "review_decision_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor procurement review decision schema or evidence boundary is unsupported",
                },
                "blockers": ["blocked_missing_hardware_sensor_procurement_review_decision"],
                "next_required_evidence": [],
                "review_decision_summary": {
                    "status": "blocked_missing_hardware_sensor_procurement_review_decision"
                },
                "owner_handoff": [],
                "rerun_commands": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement review decision is not a supported diagnostics source; no hardware or delivery result is proven.",
                    "safe_phone_copy": "Hardware sensor procurement review decision is not a supported diagnostics source; no hardware or delivery result is proven.",
                },
            }
        )
        return summary

    if _mobile_field_material_intake_has_unsafe_fields(review) or _route_task_field_run_readiness_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "review_decision_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor procurement review decision contains unsafe fields or success/control claims",
                },
                "blockers": ["blocked_missing_hardware_sensor_procurement_review_decision"],
                "next_required_evidence": [],
                "review_decision_summary": {
                    "status": "blocked_missing_hardware_sensor_procurement_review_decision"
                },
                "owner_handoff": [],
                "rerun_commands": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement review decision was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Hardware sensor procurement review decision was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_hardware_sensor_procurement_execution_pack(source):
    """构建 hardware sensor procurement execution pack 的 metadata-only diagnostics 摘要。"""
    # Robot diagnostics 只消费执行包的安全摘要；采购、装机、校准、Nav2 和 HIL 都必须继续保持 not_proven。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_sensor_procurement_execution_pack_summary(
        source_path,
        read_error="hardware sensor procurement execution pack is not configured",
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
                        "status": "blocked_missing_hardware_sensor_procurement_execution_pack",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": "hardware sensor procurement execution pack artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor procurement execution pack is missing; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor procurement execution pack is missing; hardware_material_pending remains true.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                pack = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware sensor procurement execution pack: {exc}"
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
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor procurement execution pack could not be read; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor procurement execution pack could not be read; hardware_material_pending remains true.",
                    },
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
                    "reason": "hardware sensor procurement execution pack JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement execution pack shape is invalid; hardware_material_pending remains true.",
                    "safe_phone_copy": "Hardware sensor procurement execution pack shape is invalid; hardware_material_pending remains true.",
                },
            }
        )
        return summary

    summary_fragment = {}
    for candidate in (
        pack.get("hardware_sensor_procurement_execution_pack_summary"),
        pack.get("robot_diagnostics_summary"),
        pack.get("diagnostics_summary"),
        pack.get("phone_safe_summary"),
        pack.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _hardware_sensor_procurement_execution_pack_source_contract(pack)
    status_source = (
        pack.get("execution_pack_status")
        if isinstance(pack.get("execution_pack_status"), dict)
        else summary_fragment.get("execution_pack_status")
        if isinstance(summary_fragment.get("execution_pack_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or pack.get("safe_copy")
        or pack.get("safe_phone_copy")
        or "Hardware sensor procurement execution pack is metadata-only; software_proof only, delivery_success=false."
    )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": pack.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "execution_pack_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or pack.get("status")
                    or "hardware_material_pending"
                ),
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or pack.get("reason")
                    or "hardware sensor procurement execution pack consumed without real hardware evidence"
                ),
            },
            "hardware_material_status": "hardware_material_pending",
            "blockers": _safe_route_task_rehearsal_list(
                pack.get("blockers")
                if isinstance(pack.get("blockers"), list)
                else summary_fragment.get("blockers")
            )
            or ["hardware_material_pending"],
            "material_templates": _safe_pc_route_debug_value(
                pack.get("material_templates")
                if isinstance(pack.get("material_templates"), list)
                else summary_fragment.get("material_templates", [])
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                pack.get("owner_handoff")
                if isinstance(pack.get("owner_handoff"), list)
                else summary_fragment.get("owner_handoff")
            ),
            "rerun_commands": _safe_route_task_rehearsal_list(
                pack.get("rerun_commands")
                if isinstance(pack.get("rerun_commands"), list)
                else summary_fragment.get("rerun_commands")
            ),
            "blocked_reason": _redact_route_task_rehearsal_text(
                pack.get("blocked_reason")
                or summary_fragment.get("blocked_reason")
                or status_source.get("reason")
                or "hardware sensor procurement execution pack remains not_proven"
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                pack.get("next_required_evidence")
                if isinstance(pack.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or pack.get("safe_evidence_ref")
                or pack.get("evidence_ref", "")
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                pack.get("operator_next_steps")
                if isinstance(pack.get("operator_next_steps"), list)
                else summary_fragment.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": robot_summary,
            "not_proven": _hardware_sensor_procurement_execution_pack_not_proven(
                pack, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "sensor_calibrated_on_robot": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SCHEMA,
        HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_GATE:
        summary.update(
            {
                "execution_pack_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor procurement execution pack schema or evidence boundary is unsupported",
                },
                "blockers": ["blocked_missing_hardware_sensor_procurement_execution_pack"],
                "material_templates": [],
                "owner_handoff": [],
                "rerun_commands": [],
                "blocked_reason": "blocked_missing_hardware_sensor_procurement_execution_pack",
                "next_required_evidence": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement execution pack is not a supported diagnostics source; no hardware or delivery result is proven.",
                    "safe_phone_copy": "Hardware sensor procurement execution pack is not a supported diagnostics source; no hardware or delivery result is proven.",
                },
            }
        )
        return summary

    if _mobile_field_material_intake_has_unsafe_fields(pack) or _route_task_field_run_readiness_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor procurement execution pack contains unsafe fields or success/control claims",
                },
                "blockers": ["blocked_missing_hardware_sensor_procurement_execution_pack"],
                "material_templates": [],
                "owner_handoff": [],
                "rerun_commands": [],
                "blocked_reason": "blocked_missing_hardware_sensor_procurement_execution_pack",
                "next_required_evidence": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement execution pack was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Hardware sensor procurement execution pack was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_hardware_sensor_procurement_receipt_intake(source):
    """构建 hardware sensor procurement receipt intake 的 metadata-only diagnostics 摘要。"""
    # Robot diagnostics 只消费 Hardware PC gate 的安全摘要；真实 receipt、装机、接线、电源、校准和 HIL 都保持 not_proven。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_sensor_procurement_receipt_intake_summary(
        source_path,
        read_error="hardware sensor procurement receipt intake is not configured",
    )
    if isinstance(source, dict):
        receipt = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "receipt_intake_status": {
                        "status": "blocked_missing_hardware_sensor_procurement_receipt_intake",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": "hardware sensor procurement receipt intake artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor procurement receipt intake is missing; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor procurement receipt intake is missing; hardware_material_pending remains true.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                receipt = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware sensor procurement receipt intake: {exc}"
            )
            summary.update(
                {
                    "receipt_intake_status": {
                        "status": "blocked_missing_hardware_sensor_procurement_receipt_intake",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": safe_error,
                    },
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor procurement receipt intake could not be read; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor procurement receipt intake could not be read; hardware_material_pending remains true.",
                    },
                }
            )
            return summary

    if not isinstance(receipt, dict):
        summary.update(
            {
                "receipt_intake_status": {
                    "status": "blocked_missing_hardware_sensor_procurement_receipt_intake",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor procurement receipt intake JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement receipt intake shape is invalid; hardware_material_pending remains true.",
                    "safe_phone_copy": "Hardware sensor procurement receipt intake shape is invalid; hardware_material_pending remains true.",
                },
            }
        )
        return summary

    # Hardware gate 可以给完整 artifact 或 summary wrapper；Robot 侧只抽取白名单给 diagnostics/mobile 使用。
    summary_fragment = {}
    for candidate in (
        receipt.get("hardware_sensor_procurement_receipt_intake_summary"),
        receipt.get("robot_diagnostics_summary"),
        receipt.get("diagnostics_summary"),
        receipt.get("phone_safe_summary"),
        receipt.get("mobile_readonly_summary"),
        receipt.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _hardware_sensor_procurement_receipt_intake_source_contract(receipt)
    status_source = (
        receipt.get("receipt_intake_status")
        if isinstance(receipt.get("receipt_intake_status"), dict)
        else summary_fragment.get("receipt_intake_status")
        if isinstance(summary_fragment.get("receipt_intake_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or receipt.get("safe_copy")
        or receipt.get("safe_phone_copy")
        or "Hardware sensor procurement receipt intake is metadata-only; software_proof only, delivery_success=false."
    )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    material_status = _redact_route_task_rehearsal_text(
        receipt.get("material_status")
        or summary_fragment.get("material_status")
        or receipt.get("hardware_material_status")
        or summary_fragment.get("hardware_material_status")
        or "hardware_material_pending"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": receipt.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "receipt_intake_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or receipt.get("status")
                    or "hardware_material_pending"
                ),
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or receipt.get("reason")
                    or "hardware sensor procurement receipt intake consumed without real hardware evidence"
                ),
            },
            "hardware_material_status": "hardware_material_pending",
            "material_status": material_status or "hardware_material_pending",
            "blockers": _safe_route_task_rehearsal_list(
                receipt.get("blockers")
                if isinstance(receipt.get("blockers"), list)
                else summary_fragment.get("blockers")
            )
            or ["hardware_material_pending"],
            "accepted_materials": _safe_pc_route_debug_value(
                receipt.get("accepted_materials")
                if isinstance(receipt.get("accepted_materials"), list)
                else summary_fragment.get("accepted_materials", [])
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                receipt.get("missing_materials")
                if isinstance(receipt.get("missing_materials"), list)
                else summary_fragment.get("missing_materials")
            ),
            "rejected_materials": _safe_pc_route_debug_value(
                receipt.get("rejected_materials")
                if isinstance(receipt.get("rejected_materials"), list)
                else summary_fragment.get("rejected_materials", [])
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                receipt.get("owner_handoff")
                if isinstance(receipt.get("owner_handoff"), list)
                else summary_fragment.get("owner_handoff")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                receipt.get("next_required_evidence")
                if isinstance(receipt.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or receipt.get("safe_evidence_ref")
                or receipt.get("evidence_ref", "")
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                receipt.get("operator_next_steps")
                if isinstance(receipt.get("operator_next_steps"), list)
                else summary_fragment.get("operator_next_steps")
            ),
            "robot_diagnostics_summary": robot_summary,
            "not_proven": _hardware_sensor_procurement_receipt_intake_not_proven(
                receipt, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "sensor_receipt_verified": False,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "sensor_wiring_verified": False,
            "sensor_power_budget_verified": False,
            "sensor_calibrated_on_robot": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SCHEMA,
        HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_GATE:
        summary.update(
            {
                "receipt_intake_status": {
                    "status": "blocked_missing_hardware_sensor_procurement_receipt_intake",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor procurement receipt intake schema or evidence boundary is unsupported",
                },
                "blockers": ["blocked_missing_hardware_sensor_procurement_receipt_intake"],
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_handoff": [],
                "next_required_evidence": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement receipt intake is not a supported diagnostics source; no hardware or delivery result is proven.",
                    "safe_phone_copy": "Hardware sensor procurement receipt intake is not a supported diagnostics source; no hardware or delivery result is proven.",
                },
            }
        )
        return summary

    if _mobile_field_material_intake_has_unsafe_fields(receipt) or _route_task_field_run_readiness_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "receipt_intake_status": {
                    "status": "blocked_missing_hardware_sensor_procurement_receipt_intake",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor procurement receipt intake contains unsafe fields or success/control claims",
                },
                "blockers": ["blocked_missing_hardware_sensor_procurement_receipt_intake"],
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "owner_handoff": [],
                "next_required_evidence": [],
                "operator_next_steps": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor procurement receipt intake was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Hardware sensor procurement receipt intake was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_hardware_sensor_hil_entry_config_precheck(source):
    """构建 hardware sensor HIL-entry config precheck 的 metadata-only diagnostics 摘要。"""
    # Robot 侧只消费 Hardware gate 产出的安全摘要；raw artifact、硬件路径、串口和控制语义都必须被拒绝。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_sensor_hil_entry_config_precheck_summary(
        source_path,
        read_error="hardware sensor HIL-entry config precheck is not configured",
    )
    if isinstance(source, dict):
        precheck = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "precheck_status": {
                        "status": "blocked_missing_hardware_sensor_hil_entry_config_precheck",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": "hardware sensor HIL-entry config precheck artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor HIL-entry config precheck is missing; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor HIL-entry config precheck is missing; hardware_material_pending remains true.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                precheck = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware sensor HIL-entry config precheck: {exc}"
            )
            summary.update(
                {
                    "precheck_status": {
                        "status": "blocked_missing_hardware_sensor_hil_entry_config_precheck",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": safe_error,
                    },
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor HIL-entry config precheck could not be read; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor HIL-entry config precheck could not be read; hardware_material_pending remains true.",
                    },
                }
            )
            return summary

    if not isinstance(precheck, dict):
        summary.update(
            {
                "precheck_status": {
                    "status": "blocked_missing_hardware_sensor_hil_entry_config_precheck",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry config precheck JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor HIL-entry config precheck shape is invalid; hardware_material_pending remains true.",
                    "safe_phone_copy": "Hardware sensor HIL-entry config precheck shape is invalid; hardware_material_pending remains true.",
                },
            }
        )
        return summary

    # Hardware gate 可以把白名单字段放在 artifact、summary 或 diagnostics wrapper；Robot 统一从这些位置抽取。
    summary_fragment = {}
    for candidate in (
        precheck.get("hardware_sensor_hil_entry_config_precheck_summary"),
        precheck.get("robot_diagnostics_summary"),
        precheck.get("diagnostics_summary"),
        precheck.get("phone_safe_summary"),
        precheck.get("mobile_readonly_summary"),
        precheck.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _hardware_sensor_hil_entry_config_precheck_source_contract(
        precheck
    )
    status_source = (
        precheck.get("precheck_status")
        if isinstance(precheck.get("precheck_status"), dict)
        else precheck.get("config_precheck_status")
        if isinstance(precheck.get("config_precheck_status"), dict)
        else summary_fragment.get("precheck_status")
        if isinstance(summary_fragment.get("precheck_status"), dict)
        else summary_fragment.get("config_precheck_status")
        if isinstance(summary_fragment.get("config_precheck_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or precheck.get("safe_copy")
        or precheck.get("safe_phone_copy")
        or (
            "Hardware sensor HIL-entry config precheck is metadata-only; "
            "software_proof only, delivery_success=false and primary_actions_enabled=false."
        )
    )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    sensor_config_summary = (
        precheck.get("sensor_config_summary")
        if isinstance(precheck.get("sensor_config_summary"), dict)
        else summary_fragment.get("sensor_config_summary")
        if isinstance(summary_fragment.get("sensor_config_summary"), dict)
        else {}
    )
    config_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or precheck.get("status")
        or summary_fragment.get("status")
        or "hardware_material_pending"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": precheck.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "precheck_status": {
                "status": config_status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or precheck.get("reason")
                    or "hardware sensor HIL-entry config precheck consumed without real HIL evidence"
                ),
            },
            "hardware_material_status": "hardware_material_pending",
            "config_precheck_status": config_status,
            "blockers": _safe_route_task_rehearsal_list(
                precheck.get("blockers")
                if isinstance(precheck.get("blockers"), list)
                else summary_fragment.get("blockers")
            )
            or ["hardware_material_pending"],
            "sensor_config_summary": _safe_pc_route_debug_value(sensor_config_summary),
            "missing_config_categories": _safe_route_task_rehearsal_list(
                precheck.get("missing_config_categories")
                if isinstance(precheck.get("missing_config_categories"), list)
                else summary_fragment.get("missing_config_categories")
            ),
            "missing_material_categories": _safe_route_task_rehearsal_list(
                precheck.get("missing_material_categories")
                if isinstance(precheck.get("missing_material_categories"), list)
                else summary_fragment.get("missing_material_categories")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                precheck.get("next_required_evidence")
                if isinstance(precheck.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                precheck.get("owner_handoff")
                if isinstance(precheck.get("owner_handoff"), list)
                else summary_fragment.get("owner_handoff")
            ),
            "safe_copy": safe_copy,
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or precheck.get("safe_evidence_ref")
                or precheck.get("evidence_ref", "")
            ),
            "robot_diagnostics_summary": robot_summary,
            "not_proven": _hardware_sensor_hil_entry_config_precheck_not_proven(
                precheck, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "sensor_config_precheck_only": True,
            "sensor_config_validated_for_hil_entry": False,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "sensor_wiring_verified": False,
            "sensor_power_budget_verified": False,
            "sensor_calibrated_on_robot": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SCHEMA,
        HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_GATE:
        summary.update(
            {
                "precheck_status": {
                    "status": "blocked_missing_hardware_sensor_hil_entry_config_precheck",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry config precheck schema or evidence boundary is unsupported",
                },
                "config_precheck_status": "blocked_missing_hardware_sensor_hil_entry_config_precheck",
                "blockers": ["blocked_missing_hardware_sensor_hil_entry_config_precheck"],
                "sensor_config_summary": {},
                "missing_config_categories": [],
                "missing_material_categories": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "safe_copy": "Hardware sensor HIL-entry config precheck is not a supported diagnostics source; no hardware or delivery result is proven.",
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor HIL-entry config precheck is not a supported diagnostics source; no hardware or delivery result is proven.",
                    "safe_phone_copy": "Hardware sensor HIL-entry config precheck is not a supported diagnostics source; no hardware or delivery result is proven.",
                },
            }
        )
        return summary

    if (
        _mobile_field_material_intake_has_unsafe_fields(precheck)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or str(source_boundary or "").strip() != HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_GATE
    ):
        summary.update(
            {
                "precheck_status": {
                    "status": "blocked_missing_hardware_sensor_hil_entry_config_precheck",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry config precheck contains unsafe fields, weak evidence boundary, or success/control claims",
                },
                "config_precheck_status": "blocked_missing_hardware_sensor_hil_entry_config_precheck",
                "blockers": ["blocked_missing_hardware_sensor_hil_entry_config_precheck"],
                "sensor_config_summary": {},
                "missing_config_categories": [],
                "missing_material_categories": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "safe_copy": "Hardware sensor HIL-entry config precheck was blocked because fields could expose control data or imply HIL/delivery success.",
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor HIL-entry config precheck was blocked because fields could expose control data or imply HIL/delivery success.",
                    "safe_phone_copy": "Hardware sensor HIL-entry config precheck was blocked because fields could expose control data or imply HIL/delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_hardware_sensor_hil_entry_readiness_review(source):
    """构建 hardware sensor HIL-entry readiness review 的 metadata-only diagnostics 摘要。"""
    # Robot 侧只读取 Hardware worker 的安全 artifact/summary；任何 raw 控制、串口、ACK 或成功 claim 都必须拒绝。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_sensor_hil_entry_readiness_review_summary(
        source_path,
        read_error="hardware sensor HIL-entry readiness review is not configured",
    )
    if isinstance(source, dict):
        review = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "readiness_review_status": {
                        "status": "blocked_missing_hardware_sensor_hil_entry_readiness_review",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": "hardware sensor HIL-entry readiness review artifact missing",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor HIL-entry readiness review is missing; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor HIL-entry readiness review is missing; hardware_material_pending remains true.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                review = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware sensor HIL-entry readiness review: {exc}"
            )
            summary.update(
                {
                    "readiness_review_status": {
                        "status": "blocked_missing_hardware_sensor_hil_entry_readiness_review",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": safe_error,
                    },
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Hardware sensor HIL-entry readiness review could not be read; hardware_material_pending remains true.",
                        "safe_phone_copy": "Hardware sensor HIL-entry readiness review could not be read; hardware_material_pending remains true.",
                    },
                }
            )
            return summary

    if not isinstance(review, dict):
        summary.update(
            {
                "readiness_review_status": {
                    "status": "blocked_missing_hardware_sensor_hil_entry_readiness_review",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry readiness review JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor HIL-entry readiness review shape is invalid; hardware_material_pending remains true.",
                    "safe_phone_copy": "Hardware sensor HIL-entry readiness review shape is invalid; hardware_material_pending remains true.",
                },
            }
        )
        return summary

    # Hardware gate 的直接 artifact、summary-output 和 diagnostics wrapper 都可作为来源；Robot 只复制白名单字段。
    summary_fragment = {}
    for candidate in (
        review.get("hardware_sensor_hil_entry_readiness_review_summary"),
        review.get("robot_diagnostics_summary"),
        review.get("diagnostics_summary"),
        review.get("phone_safe_summary"),
        review.get("mobile_readonly_summary"),
        review.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _hardware_sensor_hil_entry_readiness_review_source_contract(
        review
    )
    status_source = (
        review.get("readiness_review_status")
        if isinstance(review.get("readiness_review_status"), dict)
        else review.get("review_status")
        if isinstance(review.get("review_status"), dict)
        else summary_fragment.get("readiness_review_status")
        if isinstance(summary_fragment.get("readiness_review_status"), dict)
        else summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or review.get("safe_copy")
        or review.get("safe_phone_copy")
        or (
            "Hardware sensor HIL-entry readiness review is metadata-only; "
            "software_proof only, delivery_success=false and primary_actions_enabled=false."
        )
    )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    review_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or review.get("status")
        or summary_fragment.get("status")
        or "hardware_material_pending"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": review.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "readiness_review_status": {
                "status": review_status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or review.get("reason")
                    or "hardware sensor HIL-entry readiness review consumed without real HIL evidence"
                ),
            },
            "hardware_material_status": "hardware_material_pending",
            "review_status": review_status,
            "blockers": _safe_route_task_rehearsal_list(
                review.get("blockers")
                if isinstance(review.get("blockers"), list)
                else summary_fragment.get("blockers")
            )
            or ["hardware_material_pending"],
            "readiness_gates": _safe_pc_route_debug_value(
                review.get("readiness_gates")
                if isinstance(review.get("readiness_gates"), dict)
                else summary_fragment.get("readiness_gates")
                if isinstance(summary_fragment.get("readiness_gates"), dict)
                else {}
            ),
            "accepted_materials": _safe_route_task_rehearsal_list(
                review.get("accepted_materials")
                if isinstance(review.get("accepted_materials"), list)
                else summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                review.get("missing_materials")
                if isinstance(review.get("missing_materials"), list)
                else summary_fragment.get("missing_materials")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                review.get("rejected_materials")
                if isinstance(review.get("rejected_materials"), list)
                else summary_fragment.get("rejected_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                review.get("next_required_evidence")
                if isinstance(review.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                review.get("owner_handoff")
                if isinstance(review.get("owner_handoff"), list)
                else summary_fragment.get("owner_handoff")
            ),
            "rerun_commands": _safe_route_task_rehearsal_list(
                review.get("rerun_commands")
                if isinstance(review.get("rerun_commands"), list)
                else summary_fragment.get("rerun_commands")
            ),
            "safe_copy": safe_copy,
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or review.get("safe_evidence_ref")
                or review.get("evidence_ref", "")
            ),
            "robot_diagnostics_summary": robot_summary,
            "not_proven": _hardware_sensor_hil_entry_readiness_review_not_proven(
                review, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "sensor_hil_entry_readiness_review_only": True,
            "sensor_hil_entry_ready": False,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "sensor_wiring_verified": False,
            "sensor_power_budget_verified": False,
            "sensor_calibrated_on_robot": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_SCHEMA,
        HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_GATE:
        summary.update(
            {
                "readiness_review_status": {
                    "status": "blocked_missing_hardware_sensor_hil_entry_readiness_review",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry readiness review schema or evidence boundary is unsupported",
                },
                "review_status": "blocked_missing_hardware_sensor_hil_entry_readiness_review",
                "blockers": ["blocked_missing_hardware_sensor_hil_entry_readiness_review"],
                "readiness_gates": {},
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_commands": [],
                "safe_copy": "Hardware sensor HIL-entry readiness review is not a supported diagnostics source; no hardware or delivery result is proven.",
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor HIL-entry readiness review is not a supported diagnostics source; no hardware or delivery result is proven.",
                    "safe_phone_copy": "Hardware sensor HIL-entry readiness review is not a supported diagnostics source; no hardware or delivery result is proven.",
                },
            }
        )
        return summary

    if (
        _mobile_field_material_intake_has_unsafe_fields(review)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or str(source_boundary or "").strip() != HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_GATE
    ):
        summary.update(
            {
                "readiness_review_status": {
                    "status": "blocked_missing_hardware_sensor_hil_entry_readiness_review",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry readiness review contains unsafe fields, weak evidence boundary, or success/control claims",
                },
                "review_status": "blocked_missing_hardware_sensor_hil_entry_readiness_review",
                "blockers": ["blocked_missing_hardware_sensor_hil_entry_readiness_review"],
                "readiness_gates": {},
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_commands": [],
                "safe_copy": "Hardware sensor HIL-entry readiness review was blocked because fields could expose control data or imply HIL/delivery success.",
                "robot_diagnostics_summary": {
                    "safe_copy": "Hardware sensor HIL-entry readiness review was blocked because fields could expose control data or imply HIL/delivery success.",
                    "safe_phone_copy": "Hardware sensor HIL-entry readiness review was blocked because fields could expose control data or imply HIL/delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_hardware_sensor_hil_entry_execution_pack(source):
    """构建 hardware sensor HIL-entry execution pack 的 metadata-only diagnostics 摘要。"""
    # execution pack 只给 Robot diagnostics 展示下一步补料入口；任何控制、串口、ACK 或 HIL 成功语义都必须拒绝。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_sensor_hil_entry_execution_pack_summary(
        source_path,
        read_error="hardware sensor HIL-entry execution pack is not configured",
    )
    if isinstance(source, dict):
        pack = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "status": "blocked_missing_hardware_sensor_hil_entry_execution_pack",
                    "execution_pack_status": {
                        "status": "blocked_missing_hardware_sensor_hil_entry_execution_pack",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": "hardware sensor HIL-entry execution pack artifact missing",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                pack = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware sensor HIL-entry execution pack: {exc}"
            )
            summary.update(
                {
                    "status": "blocked_missing_hardware_sensor_hil_entry_execution_pack",
                    "execution_pack_status": {
                        "status": "blocked_missing_hardware_sensor_hil_entry_execution_pack",
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
                "status": "blocked_missing_hardware_sensor_hil_entry_execution_pack",
                "execution_pack_status": {
                    "status": "blocked_missing_hardware_sensor_hil_entry_execution_pack",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry execution pack JSON must be an object",
                },
            }
        )
        return summary

    # 兼容 Hardware worker 的 direct artifact、summary output、diagnostics wrapper 和 nested JSON；最终只复制白名单摘要字段。
    summary_fragment = {}
    for candidate in (
        pack.get("hardware_sensor_hil_entry_execution_pack_summary"),
        pack.get("hardware_sensor_hil_entry_execution_pack"),
        pack.get("robot_diagnostics_summary"),
        pack.get("diagnostics_summary"),
        pack.get("phone_safe_summary"),
        pack.get("mobile_readonly_summary"),
        pack.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _hardware_sensor_hil_entry_execution_pack_source_contract(
        pack
    )
    if not source_schema and isinstance(summary_fragment, dict):
        source_schema, source_boundary = _hardware_sensor_hil_entry_execution_pack_source_contract(
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
        or pack.get("status")
        or summary_fragment.get("status")
        or "hardware_material_pending"
    )
    safe_copy_source = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or pack.get("safe_copy")
        or pack.get("safe_phone_copy")
        or (
            "Hardware sensor HIL-entry execution pack is metadata-only; "
            "software_proof only, delivery_success=false and primary_actions_enabled=false."
        )
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or pack.get("safe_evidence_ref")
        or pack.get("evidence_ref", "")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": pack.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "status": status,
            "execution_pack_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or pack.get("reason")
                    or "hardware sensor HIL-entry execution pack consumed without real HIL evidence"
                ),
            },
            "hardware_material_status": "hardware_material_pending",
            "required_materials": _safe_route_task_rehearsal_list(
                pack.get("required_materials")
                if isinstance(pack.get("required_materials"), list)
                else summary_fragment.get("required_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                pack.get("missing_materials")
                if isinstance(pack.get("missing_materials"), list)
                else summary_fragment.get("missing_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                pack.get("next_required_evidence")
                if isinstance(pack.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                pack.get("owner_handoff")
                if isinstance(pack.get("owner_handoff"), list)
                else summary_fragment.get("owner_handoff")
            ),
            "rerun_commands": _safe_route_task_rehearsal_list(
                pack.get("rerun_commands")
                if isinstance(pack.get("rerun_commands"), list)
                else summary_fragment.get("rerun_commands")
            ),
            "boundary": HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_GATE,
            "safe_evidence_ref": safe_evidence_ref,
            "not_proven": _hardware_sensor_hil_entry_execution_pack_not_proven(
                pack, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "sensor_hil_entry_execution_pack_only": True,
            "sensor_hil_entry_ready": False,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "sensor_wiring_verified": False,
            "sensor_power_budget_verified": False,
            "sensor_calibrated_on_robot": False,
            "hil_entry_execution_completed": False,
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
    )
    accepted_schemas = {
        HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_SCHEMA,
        HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_SUMMARY_SCHEMA,
    }
    weak_evidence_ref = (
        not safe_evidence_ref
        or safe_evidence_ref.startswith("local_path_redacted:")
        or "[REDACTED" in safe_evidence_ref
    )
    if source_schema not in accepted_schemas or source_boundary != HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_GATE:
        summary.update(
            {
                "status": "unsupported_schema",
                "execution_pack_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry execution pack schema or evidence boundary is unsupported",
                },
                "required_materials": [],
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_commands": [],
                "safe_evidence_ref": "",
            }
        )
        return summary

    if (
        weak_evidence_ref
        or _mobile_field_material_intake_has_unsafe_fields(pack)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_source)
        or str(source_boundary or "").strip() != HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_GATE
    ):
        summary.update(
            {
                "status": "blocked_missing_hardware_sensor_hil_entry_execution_pack",
                "execution_pack_status": {
                    "status": "blocked_missing_hardware_sensor_hil_entry_execution_pack",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry execution pack contains unsafe fields, weak evidence_ref, bad boundary, or success/control claims",
                },
                "required_materials": [],
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_commands": [],
                "safe_evidence_ref": "",
            }
        )
        return summary

    return summary


def summarize_hardware_sensor_hil_entry_callback_intake(source):
    """构建 hardware sensor HIL-entry callback intake 的 metadata-only diagnostics 摘要。"""
    # Robot 只消费 Hardware 产出的消毒 summary；原始 callback material、串口、ROS graph 和凭证一律不进入摘要。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_sensor_hil_entry_callback_intake_summary(
        source_path,
        read_error="hardware sensor HIL-entry callback intake summary is not configured",
    )
    if isinstance(source, dict):
        intake = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["callback_intake_status"]["reason"] = (
                "hardware sensor HIL-entry callback intake summary artifact missing"
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware sensor HIL-entry callback intake summary: {exc}"
            )
            summary["callback_intake_status"]["reason"] = safe_error
            summary["read_error"] = safe_error
            return summary

    if not isinstance(intake, dict):
        summary["callback_intake_status"]["reason"] = (
            "hardware sensor HIL-entry callback intake JSON must be an object"
        )
        return summary

    summary_fragment = {}
    for candidate in (
        intake.get("hardware_sensor_hil_entry_callback_intake_summary"),
        intake.get("robot_diagnostics_summary"),
        intake.get("diagnostics_summary"),
        intake.get("phone_safe_summary"),
        intake.get("mobile_readonly_summary"),
        intake.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    if not summary_fragment and intake.get("schema") == HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_SUMMARY_SCHEMA:
        summary_fragment = intake

    source_schema, source_boundary = _hardware_sensor_hil_entry_callback_intake_source_contract(
        summary_fragment if summary_fragment else intake
    )
    status_source = (
        summary_fragment.get("callback_intake_status")
        if isinstance(summary_fragment.get("callback_intake_status"), dict)
        else {}
    )
    status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("status")
        or "ready_for_hardware_sensor_hil_entry_callback_intake_not_proven"
    )
    safe_copy_source = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Hardware sensor HIL-entry callback intake is metadata-only; "
            "source=software_proof; hardware_material_pending; not_proven; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": summary_fragment.get("source_schema_version")
            or summary_fragment.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "callback_intake_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or "hardware sensor HIL-entry callback intake consumed without real HIL evidence"
                ),
            },
            "status": status,
            "source": "software_proof",
            "hardware_material_status": "hardware_material_pending",
            "evidence_status": "not_proven",
            "accepted_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
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
            "rerun_commands": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_commands")
            ),
            "boundary": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_GATE,
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy_source),
            "safe_evidence_ref": safe_evidence_ref,
            "robot_diagnostics_summary": {
                "safe_copy": _redact_route_task_rehearsal_text(safe_copy_source),
                "safe_phone_copy": _redact_route_task_rehearsal_text(safe_copy_source),
            },
            "not_proven": _hardware_sensor_hil_entry_callback_intake_not_proven(
                intake, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "sensor_hil_entry_callback_intake_only": True,
            "sensor_hil_entry_ready": False,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "sensor_wiring_verified": False,
            "sensor_power_budget_verified": False,
            "sensor_calibrated_on_robot": False,
            "hil_entry_execution_completed": False,
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
    )

    accepted_schemas = {
        HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_SCHEMA,
        HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_SUMMARY_SCHEMA,
    }
    weak_evidence_ref = (
        not safe_evidence_ref
        or safe_evidence_ref.startswith("local_path_redacted:")
        or "[REDACTED" in safe_evidence_ref
    )
    unsafe_payload = (
        not summary_fragment
        or source_schema not in accepted_schemas
        or source_boundary != HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_GATE
        or str(summary_fragment.get("source") or "software_proof") != "software_proof"
        or str(summary_fragment.get("hardware_material_status") or "hardware_material_pending")
        != "hardware_material_pending"
        or str(summary_fragment.get("evidence_status") or "not_proven") != "not_proven"
        or _mobile_field_material_intake_has_unsafe_fields(intake)
        or _mobile_field_material_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_source)
        or bool(summary_fragment.get("delivery_success"))
        or bool(summary_fragment.get("primary_actions_enabled"))
    )
    if source_schema not in accepted_schemas or source_boundary != HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_GATE:
        summary.update(
            {
                "status": "blocked_unsupported_hardware_sensor_hil_entry_callback_intake",
                "callback_intake_status": {
                    "status": "blocked_unsupported_hardware_sensor_hil_entry_callback_intake",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry callback intake schema or evidence boundary is unsupported",
                },
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_commands": [],
                "safe_evidence_ref": "",
            }
        )
        return summary
    if weak_evidence_ref or unsafe_payload:
        blocked_copy = (
            "Hardware sensor HIL-entry callback intake is metadata-only; "
            "source=software_proof; hardware_material_pending; not_proven; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_hardware_sensor_hil_entry_callback_intake_copy",
                "callback_intake_status": {
                    "status": "blocked_unsafe_hardware_sensor_hil_entry_callback_intake_copy",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry callback intake contains missing summary, unsafe fields, weak evidence_ref, or success/control claims",
                },
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_commands": [],
                "safe_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
                "safe_evidence_ref": "",
            }
        )
        return summary

    return summary


def summarize_hardware_sensor_hil_entry_callback_review_decision(source):
    """构建 hardware sensor HIL-entry callback review decision 的 Robot-safe 只读摘要。"""
    # Robot 只消费 Hardware gate 的 sanitized summary；artifact 只能作为 wrapper，不能泄漏 raw callback/review。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_sensor_hil_entry_callback_review_decision_summary(
        source_path,
        read_error="hardware sensor HIL-entry callback review decision summary is not configured",
    )
    if isinstance(source, dict):
        decision = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["review_status"]["reason"] = (
                "hardware sensor HIL-entry callback review decision summary artifact missing"
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware sensor HIL-entry callback review decision summary: {exc}"
            )
            summary["review_status"]["reason"] = safe_error
            summary["read_error"] = safe_error
            return summary

    if not isinstance(decision, dict):
        summary["review_status"]["reason"] = (
            "hardware sensor HIL-entry callback review decision JSON must be an object"
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    summary_fragment = (
        decision
        if decision.get("schema") == HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    for candidate in (
        decision.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary"),
        decision.get("hardware_sensor_hil_entry_callback_review_decision_summary"),
        decision.get("robot_diagnostics_summary"),
        decision.get("robot_compatible_summary"),
        decision.get("diagnostics_summary"),
        decision.get("mobile_readonly_summary"),
        decision.get("phone_safe_summary"),
        decision.get("summary"),
        diagnostics.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary"),
        diagnostics.get("hardware_sensor_hil_entry_callback_review_decision_summary"),
        diagnostics.get("robot_diagnostics_summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("summary"),
    ):
        if summary_fragment:
            break
        if isinstance(candidate, dict) and candidate:
            summary_fragment = candidate
            break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _hardware_sensor_hil_entry_callback_review_decision_source_contract(contract_source)
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "review_status": {
                    "status": "blocked_missing_hardware_sensor_hil_entry_callback_review_decision_summary",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry callback review decision lacks a sanitized summary",
                },
                "status": "blocked_missing_hardware_sensor_hil_entry_callback_review_decision_summary",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized hardware sensor HIL-entry callback review decision summary",
                },
            }
        )
        return summary

    status_source = (
        summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else summary_fragment.get("decision_status")
        if isinstance(summary_fragment.get("decision_status"), dict)
        else {}
    )
    status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("status")
        or "blocked_hardware_material_pending_not_proven"
    )
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or "blocked"
    )
    if review_decision not in ("accepted", "missing", "rejected", "blocked"):
        review_decision = "blocked"
    safe_copy_source = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Hardware sensor HIL-entry callback review decision is metadata-only; "
            "source=software_proof; hardware_material_pending; not_proven; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy = _redact_route_task_rehearsal_text(safe_copy_source)
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    )
    same_ref_status = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": summary_fragment.get("source_schema_version")
            or summary_fragment.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "review_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or "hardware sensor HIL-entry callback review decision consumed without real HIL evidence"
                ),
            },
            "status": status,
            "review_decision": review_decision,
            "source": "software_proof",
            "hardware_material_status": "hardware_material_pending",
            "evidence_status": "not_proven",
            "accepted_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials")
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "rerun_commands": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_commands")
            ),
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_status)
            or {"status": "blocked", "verdict": "not_proven"},
            "boundary": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_GATE,
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "safe_evidence_ref": safe_evidence_ref,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {"safe_copy": safe_copy, "safe_phone_copy": safe_copy, "status": status},
            "not_proven": _hardware_sensor_hil_entry_callback_review_decision_not_proven(
                decision, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "sensor_hil_entry_callback_review_decision_only": True,
            "sensor_hil_entry_ready": False,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "sensor_wiring_verified": False,
            "sensor_power_budget_verified": False,
            "sensor_calibrated_on_robot": False,
            "hil_entry_execution_completed": False,
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
    )

    accepted_schemas = {
        HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_SCHEMA,
        HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    }
    weak_contract = (
        not safe_evidence_ref
        or safe_evidence_ref.startswith("local_path_redacted:")
        or "[REDACTED" in safe_evidence_ref
        or summary["same_evidence_ref_required"] is not True
        or str(summary_fragment.get("source") or "software_proof") != "software_proof"
        or str(summary_fragment.get("hardware_material_status") or "hardware_material_pending")
        != "hardware_material_pending"
        or str(summary_fragment.get("evidence_status") or "not_proven") != "not_proven"
    )
    unsafe_payload = (
        _mobile_field_material_intake_has_unsafe_fields(decision)
        or _mobile_field_material_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_intake_has_unsafe_control_claims(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_source)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or bool(summary_fragment.get("delivery_success"))
        or bool(summary_fragment.get("primary_actions_enabled"))
        or bool(summary_fragment.get("safe_to_control"))
    )
    if (
        source_schema not in accepted_schemas
        or source_boundary != HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "status": "blocked_unsupported_hardware_sensor_hil_entry_callback_review_decision",
                "review_status": {
                    "status": "blocked_unsupported_hardware_sensor_hil_entry_callback_review_decision",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry callback review decision schema or evidence boundary is unsupported",
                },
                "review_decision": "blocked",
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "decision_reasons": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_commands": [],
                "safe_evidence_ref": "",
            }
        )
        return summary
    if weak_contract or unsafe_payload:
        blocked_copy = (
            "Hardware sensor HIL-entry callback review decision is metadata-only; "
            "source=software_proof; hardware_material_pending; not_proven; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_hardware_sensor_hil_entry_callback_review_decision",
                "review_status": {
                    "status": "blocked_unsafe_hardware_sensor_hil_entry_callback_review_decision",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry callback review decision contains unsafe fields, weak contract, or success/control claims",
                },
                "review_decision": "blocked",
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "decision_reasons": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_commands": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
                "safe_evidence_ref": "",
            }
        )
        return summary

    return summary


def summarize_hardware_sensor_hil_entry_callback_review_handoff(source):
    """构建 hardware sensor HIL-entry callback review handoff 的 Robot-safe 只读摘要。"""
    # Robot 只消费 Hardware PC gate 的 safe summary；handoff 不能反向触发 ACK、Nav2、HIL 或控制链路。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_hardware_sensor_hil_entry_callback_review_handoff_summary(
        source_path,
        read_error="hardware sensor HIL-entry callback review handoff summary is not configured",
    )
    if isinstance(source, dict):
        handoff = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["handoff_status"]["reason"] = (
                "hardware sensor HIL-entry callback review handoff summary artifact missing"
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading hardware sensor HIL-entry callback review handoff summary: {exc}"
            )
            summary.update(
                {
                    "status": "blocked_malformed_hardware_sensor_hil_entry_callback_review_handoff",
                    "handoff_status": {
                        "status": "blocked_malformed_hardware_sensor_hil_entry_callback_review_handoff",
                        "verdict": "not_proven",
                        "evidence_source": "software_proof",
                        "reason": safe_error,
                    },
                    "read_error": safe_error,
                }
            )
            return summary

    if not isinstance(handoff, dict):
        summary.update(
            {
                "status": "blocked_malformed_hardware_sensor_hil_entry_callback_review_handoff",
                "handoff_status": {
                    "status": "blocked_malformed_hardware_sensor_hil_entry_callback_review_handoff",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry callback review handoff JSON must be an object",
                },
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    summary_fragment = (
        handoff
        if handoff.get("schema") == HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {}
    )
    for candidate in (
        handoff.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary"),
        handoff.get("hardware_sensor_hil_entry_callback_review_handoff_summary"),
        handoff.get("robot_diagnostics_summary"),
        handoff.get("robot_compatible_summary"),
        handoff.get("diagnostics_summary"),
        handoff.get("mobile_readonly_summary"),
        handoff.get("phone_safe_summary"),
        handoff.get("summary"),
        diagnostics.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary"),
        diagnostics.get("hardware_sensor_hil_entry_callback_review_handoff_summary"),
        diagnostics.get("robot_diagnostics_summary"),
        diagnostics.get("diagnostics_summary"),
        diagnostics.get("summary"),
    ):
        if summary_fragment:
            break
        if isinstance(candidate, dict) and candidate:
            summary_fragment = candidate
            break

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = (
        _hardware_sensor_hil_entry_callback_review_handoff_source_contract(contract_source)
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": handoff.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "handoff_status": {
                    "status": "blocked_missing_hardware_sensor_hil_entry_callback_review_handoff_summary",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry callback review handoff lacks a sanitized summary",
                },
                "status": "blocked_missing_hardware_sensor_hil_entry_callback_review_handoff_summary",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized hardware sensor HIL-entry callback review handoff summary",
                },
            }
        )
        return summary

    status_source = (
        summary_fragment.get("handoff_status")
        if isinstance(summary_fragment.get("handoff_status"), dict)
        else summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else {}
    )
    source_review_status = (
        summary_fragment.get("source_review_decision_status")
        if isinstance(summary_fragment.get("source_review_decision_status"), dict)
        else summary_fragment.get("source_review_status")
        if isinstance(summary_fragment.get("source_review_status"), dict)
        else {}
    )
    status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("status")
        or "blocked_hardware_sensor_hil_entry_callback_review_handoff_not_proven"
    )
    handoff_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("handoff_decision")
        or summary_fragment.get("handoff")
        or summary_fragment.get("decision")
        or "blocked"
    )
    if handoff_decision not in ("accepted", "missing", "rejected", "blocked"):
        handoff_decision = "blocked"
    safe_copy_source = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Hardware sensor HIL-entry callback review handoff is metadata-only; "
            "source=software_proof; hardware_material_pending; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy = _redact_route_task_rehearsal_text(safe_copy_source)
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    )
    same_ref_status = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": summary_fragment.get("source_schema_version")
            or summary_fragment.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "handoff_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or "hardware sensor HIL-entry callback review handoff consumed without real HIL evidence"
                ),
            },
            "source_review_decision_status": _safe_pc_route_debug_dict(source_review_status)
            or {"status": "blocked", "verdict": "not_proven"},
            "status": status,
            "handoff_decision": handoff_decision,
            "source": "software_proof",
            "hardware_material_status": "hardware_material_pending",
            "evidence_status": "not_proven",
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "rerun_guidance": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_guidance") or summary_fragment.get("rerun_commands")
            ),
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_status)
            or {"status": "blocked", "verdict": "not_proven"},
            "boundary": HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_GATE,
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "safe_evidence_ref": safe_evidence_ref,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {"safe_copy": safe_copy, "safe_phone_copy": safe_copy, "status": status},
            "not_proven": _hardware_sensor_hil_entry_callback_review_handoff_not_proven(
                handoff, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "real_hardware_observed": False,
            "hardware_material_pending": True,
            "sensor_hil_entry_callback_review_handoff_only": True,
            "sensor_hil_entry_ready": False,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "sensor_wiring_verified": False,
            "sensor_power_budget_verified": False,
            "sensor_calibrated_on_robot": False,
            "hil_entry_execution_completed": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "safe_to_control": False,
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
        HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_SCHEMA,
        HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }
    weak_contract = (
        not safe_evidence_ref
        or safe_evidence_ref.startswith("local_path_redacted:")
        or "[REDACTED" in safe_evidence_ref
        or summary["same_evidence_ref_required"] is not True
        or str(summary_fragment.get("source") or "software_proof") != "software_proof"
        or str(summary_fragment.get("hardware_material_status") or "hardware_material_pending")
        != "hardware_material_pending"
        or str(summary_fragment.get("evidence_status") or "not_proven") != "not_proven"
    )
    unsafe_payload = (
        _mobile_field_material_intake_has_unsafe_fields(handoff)
        or _mobile_field_material_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_intake_has_unsafe_control_claims(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_source)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or bool(summary_fragment.get("delivery_success"))
        or bool(summary_fragment.get("primary_actions_enabled"))
        or bool(summary_fragment.get("safe_to_control"))
    )
    if (
        source_schema not in accepted_schemas
        or source_boundary != HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_GATE
    ):
        summary.update(
            {
                "status": "blocked_unsupported_hardware_sensor_hil_entry_callback_review_handoff",
                "handoff_status": {
                    "status": "blocked_unsupported_hardware_sensor_hil_entry_callback_review_handoff",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry callback review handoff schema or evidence boundary is unsupported",
                },
                "handoff_decision": "blocked",
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_guidance": [],
                "safe_evidence_ref": "",
            }
        )
        return summary
    if weak_contract or unsafe_payload:
        blocked_copy = (
            "Hardware sensor HIL-entry callback review handoff is metadata-only; "
            "source=software_proof; hardware_material_pending; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_hardware_sensor_hil_entry_callback_review_handoff",
                "handoff_status": {
                    "status": "blocked_unsafe_hardware_sensor_hil_entry_callback_review_handoff",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "hardware sensor HIL-entry callback review handoff contains unsafe fields, weak contract, wrong source, or success/control claims",
                },
                "handoff_decision": "blocked",
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_guidance": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
                "safe_evidence_ref": "",
            }
        )
        return summary

    return summary
