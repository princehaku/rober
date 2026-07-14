"""WAVE ROVER motion-map HIL material bundle。

Vendor 来源：
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml

本模块只消费历史现场 run 的安全投影：
- first jog command 摘要；
- feedback samples 摘要；
- scan delta metrics；
- operator structured claims；
- field/manual map yaml + pgm header + pixel review。

模块不会读取或回显 raw endpoint、source_base_url、/root/...、token 或 traceback。
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import re
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.wave_rover_motion_map_hil_material_bundle.v1"
PROOF_SCOPE = "software_proof_o1_motion_map_hil_material_bundle_only"
READY_STATUS = "motion_map_hil_material_bundle_ready_not_hil_pass"
BLOCKED_STATUS = "blocked_invalid_motion_map_hil_material_bundle"
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_ARTIFACT_DIR = (
    REPO_ROOT / "sprints/2026.06.22_01-35_motion_map_runtime_probe/artifacts"
)
CLEAN_BASELINE_ARTIFACT_DIR = (
    REPO_ROOT / "sprints/2026.06.11_11-15_clean_baseline_nav2_path_refresh/artifacts"
)
BOUNDED_MOTION_ARTIFACT_DIR = (
    REPO_ROOT / "sprints/2026.06.10_01-35_motion-feedback-alignment/artifacts/remote_capture"
)
PC_REAL_ROBOT_API_READBACK_ARTIFACT_DIR = (
    REPO_ROOT / "sprints/2026.06.10_22-40_pc_real_robot_api_readback/artifacts"
)
WHEEL_FEEDBACK_DIAGNOSTIC_ARTIFACT_DIR = (
    REPO_ROOT / "sprints/2026.06.10_02-05_wheel-feedback-diagnostic-sweep/artifacts/remote_capture"
)
MANUAL_HIL_GATE_ARTIFACT_DIR = (
    REPO_ROOT / "sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts"
)
STRUCTURED_HIL_REPORT_ARTIFACT_DIR = (
    REPO_ROOT / "sprints/2026.06.11_06-05_pc_structured_hil_report_readback/artifacts"
)
SAME_SESSION_WHEEL_FEEDBACK_ARTIFACT_DIR = (
    REPO_ROOT / "sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts"
)
DEFAULT_PATHS = {
    "first_jog_json": DEFAULT_ARTIFACT_DIR / "10_pc_first_jog_for_scan_delta.json",
    "feedback_samples_json": DEFAULT_ARTIFACT_DIR / "12_pc_feedback_samples_after_scan_delta_jog.json",
    "scan_delta_json": DEFAULT_ARTIFACT_DIR / "14_scan_delta_metrics.json",
    "operator_report_json": DEFAULT_ARTIFACT_DIR / "18_operator_report_lidar_delta_response.json",
    "field_map_yaml": DEFAULT_ARTIFACT_DIR / "22_field_first_jog_map.yaml",
    "field_map_pgm": DEFAULT_ARTIFACT_DIR / "23_field_first_jog_map.pgm",
    "field_pixel_review_json": DEFAULT_ARTIFACT_DIR / "24_field_first_jog_map_pixel_review.json",
    "manual_map_yaml": DEFAULT_ARTIFACT_DIR / "30_manual_motion_map.yaml",
    "manual_map_pgm": DEFAULT_ARTIFACT_DIR / "31_manual_motion_map.pgm",
    "manual_pixel_review_json": DEFAULT_ARTIFACT_DIR / "32_manual_motion_map_pixel_review.json",
    "free_cell_map_start_json": DEFAULT_ARTIFACT_DIR / "33_pc_map_start_after_free_pixel_fix.json",
    "free_cell_map_list_json": DEFAULT_ARTIFACT_DIR / "34_pc_map_list_after_free_pixel_fix.json",
    "free_cell_map_yaml": DEFAULT_ARTIFACT_DIR / "35_fixed_free_cells_map.yaml",
    "free_cell_map_pgm": DEFAULT_ARTIFACT_DIR / "36_fixed_free_cells_map.pgm",
    "free_cell_pixel_review_json": DEFAULT_ARTIFACT_DIR / "37_fixed_free_cells_map_pixel_review.json",
    "free_cell_pc_summary_json": DEFAULT_ARTIFACT_DIR / "38_pc_summary_after_map_fix.json",
    "clean_baseline_nav2_path_latest_json": CLEAN_BASELINE_ARTIFACT_DIR / "nav2_latest_after_success.json",
    "clean_baseline_nav2_path_retry_summary_json": CLEAN_BASELINE_ARTIFACT_DIR / "nav2_retry_summary.json",
    "bounded_motion_feedback_summary_json": BOUNDED_MOTION_ARTIFACT_DIR / "feedback_motion_summary.json",
    "bounded_motion_pulse_and_stop_log": BOUNDED_MOTION_ARTIFACT_DIR / "pulse_and_stop.log",
    "bounded_motion_odom_after_motion_txt": BOUNDED_MOTION_ARTIFACT_DIR / "odom_after_motion.txt",
    "bounded_motion_imu_once_txt": BOUNDED_MOTION_ARTIFACT_DIR / "imu_once.txt",
    "pc_real_robot_api_readback_summary_json": PC_REAL_ROBOT_API_READBACK_ARTIFACT_DIR / "readback_summary.json",
    "base_feedback_samples_latest_json": PC_REAL_ROBOT_API_READBACK_ARTIFACT_DIR / "base_feedback_samples_latest.json",
    "wheel_feedback_diagnostic_sweep_summary_json": WHEEL_FEEDBACK_DIAGNOSTIC_ARTIFACT_DIR
    / "wheel_feedback_sweep_summary.json",
    "manual_hil_gate_decision_json": MANUAL_HIL_GATE_ARTIFACT_DIR / "pc_proxy/gate_decision_before.json",
    "manual_hil_gate_stop_safety_json": MANUAL_HIL_GATE_ARTIFACT_DIR / "pc_proxy/stop_safety_smoke.json",
    "manual_hil_gate_manual_reject_json": MANUAL_HIL_GATE_ARTIFACT_DIR / "pc_proxy/manual_forward_expected_reject.json",
    "manual_hil_gate_proxy_smoke_json": MANUAL_HIL_GATE_ARTIFACT_DIR / "pc_proxy/proxy_smoke_result.json",
    "manual_hil_gate_feedback_samples_latest_json": MANUAL_HIL_GATE_ARTIFACT_DIR
    / "remote_readback/after_api_base_feedback-samples_latest.json",
    "manual_hil_gate_operator_report_latest_json": STRUCTURED_HIL_REPORT_ARTIFACT_DIR
    / "real_board_operator_report_direct_192_168_1_11_8787.json",
    "manual_hil_gate_robot_control_summary_json": STRUCTURED_HIL_REPORT_ARTIFACT_DIR
    / "real_board_robot_control_summary_192_168_1_11_8787.json",
    "same_session_wheel_feedback_json": SAME_SESSION_WHEEL_FEEDBACK_ARTIFACT_DIR
    / "01_upper_manual_samesession_012.json",
    "same_session_pc_first_jog_json": SAME_SESSION_WHEEL_FEEDBACK_ARTIFACT_DIR
    / "02_pc_first_jog_samesession_timeoutfix.json",
    "same_session_pc_after_jog_base_status_json": SAME_SESSION_WHEEL_FEEDBACK_ARTIFACT_DIR
    / "03_base_status_after_pc_jog.json",
}
VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
]
NEXT_REQUIRED_EVIDENCE = [
    "current_live_same_run_feedback_T1001_log",
    "current_live_same_run_motion_command_record",
    "current_live_same_run_operator_or_external_motion_observation",
    "current_live_same_run_hil_acceptance_record",
    "current_live_route_map_with_free_cells",
    "current_live_same_run_nav2_path_generation_success",
    "current_live_same_run_nav2_route_execution_success",
    "current_live_same_run_bounded_motion_T1001_LR_nonzero_feedback",
    "current_live_same_run_wheel_direction_confirmation",
    "current_live_same_run_imu_battery_calibration_record",
]
FALSE_SAFETY_FIELDS = {
    "hil_pass": False,
    "safe_to_control": False,
    "delivery_success": False,
    "primary_actions_enabled": False,
    "robot_control_executed": False,
    "nav2_route_execution_success": False,
    "bounded_motion_lr_nonzero_proven": False,
    "wheel_direction_proven": False,
    "imu_battery_calibration_proven": False,
    "sends_motion_commands": False,
}
# 顶层和 operator claims 中的这些 true 会误导成现场履约已通过，必须 fail-closed。
DANGEROUS_TRUE_FIELDS = frozenset(
    {
        "hil_pass",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "robot_control_executed",
        "nav2_route_execution_success",
        "same_run_path_proven",
        "wheel_feedback_lr_nonzero_proven",
        "bounded_motion_lr_nonzero_proven",
        "wheel_direction_proven",
        "imu_battery_calibration_proven",
        "real_route_map_proven",
        "sends_motion_commands",
        "readback_sends_commands",
    }
)
# 只对“被消费进摘要”的字符串做安全检查，避免正例因为原始 wrapper 自带 URL/path 而误杀。
UNSAFE_VALUE_PATTERN = re.compile(
    r"(https?://|/root/|/Users/|/dev/tty|Traceback \(most recent call last\)|"
    r"bearer\s+|token|secret|password|baudrate|115200|[A-Za-z0-9+/]{80,}={0,2})",
    re.IGNORECASE,
)
RUN_TOKEN_PATTERN = re.compile(r"(20\d{6}_\d{4})")
EXPECTED_SCHEMAS = {
    "first_jog": "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
    "feedback_samples": "trashbot.pc_tools_workstation.robot_control_base_feedback_samples_proxy.v1",
    "scan_delta": "trashbot.scan_delta_review.v1",
    "operator_report": "trashbot.pc_tools_workstation.robot_control_operator_report_proxy.v1",
    "pixel_review": "trashbot.map_pgm_pixel_review.v1",
    "map_lifecycle": "trashbot.pc_tools_workstation.robot_control_map_lifecycle_proxy.v1",
    "pc_summary": "trashbot.pc_tools_workstation.robot_control_summary.v1",
    "nav2_latest": "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest",
    "nav2_retry_summary": "trashbot.upper_robot_api.v1.nav2_runtime_proof_refresh_result",
    "bounded_motion_feedback": "rober.motion_feedback_alignment.v1",
    "pc_real_robot_readback": "trashbot.sprint.pc_real_robot_api_readback.summary.v1",
    "base_feedback_samples_latest": "trashbot.upper_robot_api.v1.base_feedback_samples_latest_result",
    "base_feedback_samples_result": "trashbot.upper_robot_api.v1.base_feedback_samples_result",
    "base_feedback_request_result": "trashbot.upper_robot_api.v1.base_feedback_request_result",
    "wheel_feedback_diagnostic_sweep": "rober.wheel_feedback_sweep.v1",
    "manual_hil_gate_current_decision": "trashbot.pc_manual_hil_gate.current_decision.v1",
    "manual_hil_gate_proxy_smoke_result": "trashbot.pc_manual_hil_gate.proxy_smoke_result.v1",
    "robot_control_base_command_proxy": "trashbot.pc_tools_workstation.robot_control_base_command_proxy.v1",
    "operator_report_latest_result": "trashbot.upper_robot_api.v1.operator_report_latest_result",
    "robot_control_summary": "trashbot.pc_tools_workstation.robot_control_summary.v1",
    "same_session_manual_result": "trashbot.upper_robot_api.v1.base_manual_result",
    "base_status": "trashbot.upper_robot_api.v1.base_status",
}
MANUAL_HIL_GATE_REQUIRED_MISSING_FIELDS = [
    "external_video_recorded",
    "visible_content_proven",
    "wheel_feedback_lr_nonzero_proven",
    "physical_motion_lidar_delta_proven",
]
SAME_SESSION_HIL_ACCEPTANCE_MISSING_FIELDS = [
    "external_video_recorded",
    "physical_motion_lidar_delta_proven",
    "current_live_hil_acceptance_record",
    "current_live_nav2_route_execution_success",
]
SAME_SESSION_WHEEL_FEEDBACK_READY_STATUS = "same_session_wheel_feedback_material_ready_not_hil_pass"
SAME_SESSION_WHEEL_FEEDBACK_BLOCKED_STATUS = "same_session_wheel_feedback_material_blocked_not_hil_pass"
SAME_SESSION_HIL_ACCEPTANCE_STATUS = "blocked_missing_current_live_acceptance"
SAME_SESSION_PC_COMMAND_READY_STATUS = "same_session_pc_command_material_ready_not_hil_pass"
SAME_SESSION_PC_COMMAND_BLOCKED_STATUS = "same_session_pc_command_material_blocked_not_hil_pass"
EXPECTED_FREE_CELL_PIXEL_COUNT = 394
REQUIRED_LOCALIZATION_FALSE_FIELDS = (
    "safe_to_control",
    "delivery_success",
    "primary_actions_enabled",
)
OPTIONAL_LOCALIZATION_FALSE_FIELDS = (
    "robot_control_executed",
    "hil_pass",
    "nav2_route_execution_success",
    "same_run_path_proven",
    "wheel_feedback_lr_nonzero_proven",
    "real_route_map_proven",
)
REQUIRED_LOCALIZATION_ENDPOINTS = {
    "status": ("/api/status", "trashbot.upper_robot_api.v1.status"),
    "map_proof_latest": ("/api/map/proof/latest", "trashbot.upper_robot_api.v1.map_lifecycle_proof_latest"),
    "localize_proof_latest": ("/api/localize/proof/latest", "trashbot.upper_robot_api.v1.localization_proof_latest"),
    "nav2_status": ("/api/nav2/status", "trashbot.upper_robot_api.v1.nav2_lifecycle_status"),
    "nav2_proof_latest": ("/api/nav2/proof/latest", "trashbot.upper_robot_api.v1.nav2_runtime_proof_latest"),
}


def _dedupe(items: list[str]) -> list[str]:
    """保持 blocked reason 顺序，避免重复噪声。"""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _is_finite_number(value: Any) -> bool:
    """所有数值在进入摘要前都要求是有限值。"""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(parsed)


def _safe_string(value: Any, reason: str, blocked_reasons: list[str]) -> str | None:
    """只让输出 intend-to-show 的字符串通过 allowlist。"""
    if not isinstance(value, str):
        blocked_reasons.append(reason)
        return None
    stripped = value.strip()
    if not stripped or UNSAFE_VALUE_PATTERN.search(stripped):
        blocked_reasons.append(reason)
        return None
    return stripped


def _safe_bool(value: Any, reason: str, blocked_reasons: list[str]) -> bool | None:
    """bool 字段既要存在，也要避免被字符串/数字伪装。"""
    if isinstance(value, bool):
        return value
    blocked_reasons.append(reason)
    return None


def _safe_string_bool(value: Any, reason: str, blocked_reasons: list[str]) -> bool | None:
    """PC summary 中部分布尔值以字符串承载，进入摘要前显式归一。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if UNSAFE_VALUE_PATTERN.search(value):
            blocked_reasons.append(reason)
            return None
        stripped = value.strip().lower()
        if stripped in {"true", "false"}:
            return stripped == "true"
    blocked_reasons.append(reason)
    return None


def _safe_prefixed_false(value: Any, reason: str, blocked_reasons: list[str]) -> bool | None:
    """处理 `false; ref=not_loaded` 这类安全 material 字段。"""
    if not isinstance(value, str):
        blocked_reasons.append(reason)
        return None
    if UNSAFE_VALUE_PATTERN.search(value):
        blocked_reasons.append(reason)
        return None
    return value.strip().lower().startswith("false")


def _safe_required_false(value: Any, reason: str, blocked_reasons: list[str]) -> bool | None:
    """安全字段必须显式为 false；缺失或 true 都不能进入 ready 摘要。"""
    parsed = _safe_string_bool(value, reason, blocked_reasons)
    if parsed is not False:
        blocked_reasons.append(reason)
    return parsed


def _safe_float(value: Any, reason: str, blocked_reasons: list[str]) -> float | None:
    """float 字段进入摘要前要显式校验有限性。"""
    if not _is_finite_number(value):
        blocked_reasons.append(reason)
        return None
    return float(value)


def _safe_int(value: Any, reason: str, blocked_reasons: list[str]) -> int | None:
    """int 字段只接受有限数值，并转成离散计数。"""
    if not _is_finite_number(value):
        blocked_reasons.append(reason)
        return None
    return int(float(value))


def _extract_run_token(text: str | None) -> str | None:
    """从文件名或安全路径片段里提取历史 run token。"""
    if not text:
        return None
    match = RUN_TOKEN_PATTERN.search(text)
    if match is None:
        return None
    return match.group(1)


def _append_dangerous_true(payload: dict[str, Any], label: str, blocked_reasons: list[str]) -> None:
    """任何会被误读成可上车/可控制/已送达的 true 都必须锁死。"""
    for field in DANGEROUS_TRUE_FIELDS:
        if payload.get(field) is True:
            blocked_reasons.append(f"{label}_dangerous_true_{field}")
    hard_dangerous = payload.get("hard_dangerous_true_fields")
    if isinstance(hard_dangerous, list):
        if hard_dangerous:
            blocked_reasons.append(f"{label}_hard_dangerous_true_fields_present")
        for item in hard_dangerous:
            if not isinstance(item, str) or UNSAFE_VALUE_PATTERN.search(item):
                blocked_reasons.append(f"{label}_hard_dangerous_true_fields_invalid")
    elif hard_dangerous is not None:
        blocked_reasons.append(f"{label}_hard_dangerous_true_fields_invalid")


def _path_ref(path: Path | str) -> str:
    """source_refs 只输出仓库相对路径，不输出本机绝对路径。"""
    candidate = Path(path)
    try:
        return str(candidate.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return candidate.name


def _safe_base_summary(status: str, source_refs: dict[str, str], blocked_reasons: list[str]) -> dict[str, Any]:
    """构造固定 false、可安全回显的 bundle 骨架。"""
    return {
        "schema": SCHEMA,
        "status": status,
        "proof_scope": PROOF_SCOPE,
        "source_refs": source_refs,
        "vendor_sources": list(VENDOR_SOURCES),
        "same_run_material_present": False,
        "run_token": None,
        "first_jog_command_present": False,
        "first_jog_command_summary": None,
        "feedback_sample_present": False,
        "feedback_sample_summary": None,
        "scan_delta_present": False,
        "scan_delta_summary": None,
        "operator_report_present": False,
        "operator_claim_summary": None,
        "field_first_jog_map_present": False,
        "field_first_jog_map_summary": None,
        "manual_motion_map_present": False,
        "manual_motion_map_summary": None,
        "pixel_review_summary": {
            "field_first_jog_map": None,
            "manual_motion_map": None,
        },
        "map_output_present": False,
        # 像素 review 已知没有 free cells，因此 bundle 只能承认“有 map artifact”，不能承认“可导航”。
        "map_navigation_ready": False,
        "free_cell_map_material_present": False,
        "free_cell_map_lifecycle_present": False,
        "free_cell_map_list_present": False,
        "free_cell_map_yaml_present": False,
        "free_cell_map_pgm_present": False,
        "free_cell_pixel_review_present": False,
        "free_cell_pc_summary_present": False,
        "free_cell_map_summary": None,
        "free_cell_pixel_review_summary": None,
        "free_cell_pc_summary": None,
        "free_cell_pixel_count": None,
        "free_cell_has_free_cells": False,
        "free_cell_usable_map_count": None,
        "map_navigation_material_ready": False,
        "localization_path_material_bridge_present": False,
        "same_run_localization_material_present": False,
        "same_run_map_once_observed": False,
        "same_run_amcl_pose_observed": False,
        "same_run_localization_tf_map_to_odom": False,
        "same_run_localization_tf_map_to_base_link": False,
        "same_run_planner_server_active": False,
        "same_run_path_generation_requested": False,
        "same_run_path_generation_succeeded": False,
        "same_run_path_generated": False,
        "same_run_path_point_count": None,
        "same_run_path_proven": False,
        "localization_path_bridge_ready_not_route_execution_proof": False,
        "localization_path_material_bridge_summary": None,
        "cross_run_clean_baseline_path_comparator_present": False,
        "cross_run_clean_baseline_path_comparator_blocked_reasons": [],
        "cross_run_clean_baseline_path_summary": None,
        "bounded_motion_feedback_material_present": False,
        "bounded_motion_feedback_present": False,
        "bounded_motion_feedback_material_status": None,
        "feedback_motion_summary_present": False,
        "feedback_motion_summary": None,
        "bounded_motion_command_observed": False,
        "bounded_motion_duration_lte_0_3s": False,
        "bounded_motion_stop_observed": False,
        "t1001_feedback_before_after_observed": False,
        "t1001_feedback_sample_count": None,
        "t1001_observed_count": None,
        "readback_summary_present": False,
        "readback_summary": None,
        "base_feedback_samples_latest_present": False,
        "base_feedback_samples_latest_summary": None,
        "feedback_request_observed": False,
        "feedback_request_t130_observed": False,
        "odom_readback_sample_present": False,
        "odom_readback_frame_id": None,
        "odom_readback_child_frame_id": None,
        "imu_sample_present": False,
        "imu_frame_id": None,
        "battery_sample_present": False,
        "ros_sample_readback_summary": None,
        "wheel_feedback_diagnostic_context_present": False,
        "wheel_feedback_sweep_all_nonzero_lr_count_zero": False,
        "wheel_feedback_diagnostic_summary": None,
        "bounded_motion_feedback_ready_not_hil_pass": False,
        "manual_hil_gate_current_evidence_material_present": False,
        "manual_hil_gate_current_evidence_material_status": None,
        "manual_hil_gate_status": None,
        "manual_hil_gate_missing_fields": [],
        "visible_content_proven_blocks_motion": False,
        "manual_nonzero_policy": None,
        "stop_safety_smoke_forwarded": False,
        "stop_remote_http_status": None,
        "manual_nonstop_local_reject_present": False,
        "manual_nonstop_remote_base_manual_called": False,
        "manual_nonstop_failure_reason": None,
        "proxy_remote_base_manual_not_called_by_local_reject": False,
        "manual_gate_t1001_observed_count": None,
        "manual_gate_all_samples_observed_t1001": False,
        "manual_gate_feedback_request_t130_observed": False,
        "operator_structured_report_material_only": False,
        "operator_structured_report_status": None,
        "operator_structured_delivery_claim_material_only": False,
        "manual_hil_gate_ready_not_hil_pass": False,
        "manual_hil_gate_current_evidence_summary": None,
        "same_session_wheel_feedback_material_present": False,
        "same_session_wheel_feedback_material_status": None,
        "same_session_wheel_feedback_lr_nonzero_material_present": False,
        "same_session_wheel_feedback_latest_nonzero_pair": None,
        "same_session_wheel_feedback_motion_window_nonzero_pair_count": None,
        "same_session_wheel_feedback_motion_window_t1001_count": None,
        "same_session_wheel_feedback_feedback_request_t130_observed": False,
        "same_session_wheel_feedback_current_live_rerun": False,
        "same_session_wheel_feedback_summary": None,
        "same_session_hil_acceptance_status": None,
        "same_session_hil_acceptance_missing_fields": [],
        "same_session_hil_acceptance_ready_not_hil_pass": False,
        "same_session_pc_command_material_present": False,
        "same_session_pc_command_material_status": None,
        "same_session_pc_command_requested_direction": None,
        "same_session_pc_command_applied_direction": None,
        "same_session_pc_command_clamped_speed_mps": None,
        "same_session_pc_command_clamped_duration_ms": None,
        "same_session_pc_command_checklist_confirmed": False,
        "same_session_pc_command_evidence_capture_status": None,
        "same_session_pc_command_wheel_feedback_lr_nonzero_material_present": False,
        "same_session_pc_command_motion_window_nonzero_frame_count": None,
        "same_session_pc_command_latest_nonzero_pair": None,
        "same_session_pc_command_feedback_during_motion_attempted": False,
        "same_session_pc_command_feedback_after_stop_attempted": False,
        "same_session_pc_command_manual_command_executed": False,
        "same_session_pc_command_auto_stop_executed": False,
        "same_session_pc_command_after_jog_t1001_observed": False,
        "same_session_pc_command_after_jog_feedback_source": None,
        "same_session_pc_command_after_jog_latest_pair": None,
        "same_session_pc_command_after_jog_wheel_feedback_lr_zero_readback": False,
        "same_session_pc_command_after_jog_feedback_samples_freshness_status": None,
        "same_session_pc_command_after_jog_readback_sends_commands": False,
        "same_session_pc_command_readback_summary": None,
        "same_session_pc_command_summary": None,
        "blocked_reasons": blocked_reasons,
        "next_required_evidence": list(NEXT_REQUIRED_EVIDENCE),
        **FALSE_SAFETY_FIELDS,
    }


def _blocked(blocked_reasons: list[str], source_refs: dict[str, str]) -> dict[str, Any]:
    """所有失败都降级为安全枚举 reason。"""
    summary = _safe_base_summary(BLOCKED_STATUS, source_refs, _dedupe(blocked_reasons))
    _ensure_summary_is_safe(summary)
    return summary


def _ensure_summary_is_safe(summary: dict[str, Any]) -> None:
    """输出层做最终保险，防止实现回归把敏感上下文塞进合同。"""
    rendered = json.dumps(summary, sort_keys=True, ensure_ascii=False)
    forbidden_patterns = [
        r"https?://",
        r"/root/",
        r"/Users/",
        r"/dev/tty",
        r"Traceback \(most recent call last\)",
        r"bearer\s+",
        r"source_base_url",
        r"normalized_base_url",
        r"remote_endpoint",
        r"source_endpoint_id",
        r"camera_artifacts_ref",
        r"camera_visible",
        r"raw_runtime_context",
        r"safe_command_boundary",
        r"manual_endpoint",
        r"stop_endpoint",
        r'"(token|secret|password)"\s*:',
        r"baudrate",
        r"\b115200\b",
        r"[A-Za-z0-9+/]{80,}={0,2}",
    ]
    for pattern in forbidden_patterns:
        if re.search(pattern, rendered, re.IGNORECASE):
            raise ValueError("unsafe summary leakage detected")


def _load_json_object(path: Path) -> dict[str, Any]:
    """JSON 输入必须是 object，不能是 list/string wrapper。"""
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("json_root_not_object")
    return payload


def _load_map_yaml(path: Path) -> dict[str, Any]:
    """用最小 YAML 解析支持 map_server 产物，避免依赖外部库。"""
    result: dict[str, Any] = {}
    origin: list[float] = []
    in_origin = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "origin:":
            in_origin = True
            origin = []
            continue
        if in_origin and line.startswith("- "):
            origin.append(float(line[2:].strip()))
            continue
        in_origin = False
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if key == "image":
            result[key] = value
        elif key in {"resolution", "free_thresh", "occupied_thresh"}:
            result[key] = float(value)
        elif key == "negate":
            result[key] = int(float(value))
        else:
            result[key] = value
    if origin:
        result["origin"] = origin
    return result


def _read_pgm_header(path: Path) -> dict[str, int | str]:
    """只读 PGM header，验证 map artifact 基本结构。"""
    tokens: list[str] = []
    with path.open("rb") as handle:
        while len(tokens) < 4:
            line = handle.readline()
            if line == b"":
                break
            if line.startswith(b"#"):
                continue
            tokens.extend(line.decode("ascii", errors="strict").split())
    if len(tokens) < 4:
        raise ValueError("pgm_header_incomplete")
    magic, width, height, max_value = tokens[:4]
    if magic != "P5":
        raise ValueError("pgm_magic_mismatch")
    return {
        "magic": magic,
        "width": int(width),
        "height": int(height),
        "max_value": int(max_value),
    }


def _parse_feedback_types(raw_value: Any, blocked_reasons: list[str]) -> list[int]:
    """反馈类型在历史材料里是字符串化数组，这里做安全解析。"""
    if not isinstance(raw_value, str):
        blocked_reasons.append("feedback_types_invalid")
        return []
    if UNSAFE_VALUE_PATTERN.search(raw_value):
        blocked_reasons.append("feedback_types_invalid")
        return []
    try:
        parsed = ast.literal_eval(raw_value)
    except (ValueError, SyntaxError):
        blocked_reasons.append("feedback_types_invalid")
        return []
    if not isinstance(parsed, list):
        blocked_reasons.append("feedback_types_invalid")
        return []
    result: list[int] = []
    for item in parsed:
        if not _is_finite_number(item):
            blocked_reasons.append("feedback_types_invalid")
            return []
        result.append(int(float(item)))
    return result


def _parse_feedback_type_list(raw_value: Any, reason: str, blocked_reasons: list[str]) -> list[int]:
    """新版上位机材料用结构化 list 承载反馈类型，仍需逐项校验。"""
    if not isinstance(raw_value, list):
        blocked_reasons.append(reason)
        return []
    parsed: list[int] = []
    for item in raw_value:
        if not _is_finite_number(item):
            blocked_reasons.append(reason)
            return []
        parsed.append(int(float(item)))
    return parsed


def _append_optional_false_fields(
    payload: dict[str, Any],
    label: str,
    fields: tuple[str, ...],
    blocked_reasons: list[str],
) -> None:
    """历史材料可缺少部分 safety 字段；一旦出现 true 就 fail-closed。"""
    for field in fields:
        if field not in payload:
            continue
        parsed = _safe_string_bool(
            payload.get(field),
            f"{label}_{field}_invalid",
            blocked_reasons,
        )
        if parsed is not False:
            blocked_reasons.append(f"{label}_{field}_not_false")


def _wheel_sign_pattern(left: float, right: float) -> str:
    """只描述同帧 L/R 符号，不把它升级成轮向标定结论。"""
    if left > 0 and right > 0:
        return "both_positive"
    if left < 0 and right < 0:
        return "both_negative"
    if left > 0 and right < 0:
        return "left_positive_right_negative"
    if left < 0 and right > 0:
        return "left_negative_right_positive"
    if left == 0 and right == 0:
        return "both_zero"
    if left == 0:
        return "left_zero_right_nonzero"
    return "left_nonzero_right_zero"


def _collect_source_refs(paths: dict[str, Path]) -> dict[str, str]:
    """source_refs 固定输出相对路径，便于复验。"""
    return {name: _path_ref(path) for name, path in paths.items()}


def _parse_first_jog(first_jog: dict[str, Any], blocked_reasons: list[str]) -> tuple[bool, dict[str, Any] | None]:
    """消费 first jog 摘要，只取安全且对 bundle 有意义的字段。"""
    if first_jog.get("schema") != EXPECTED_SCHEMAS["first_jog"]:
        blocked_reasons.append("first_jog_schema_mismatch")
        return False, None
    if first_jog.get("proxy_status") != "command_forwarded" or first_jog.get("status") != "loaded":
        blocked_reasons.append("first_jog_not_forwarded")
        return False, None
    for field in ("safe_to_control", "delivery_success", "primary_actions_enabled", "robot_control_executed"):
        if first_jog.get(field) is True:
            blocked_reasons.append(f"dangerous_true_{field}")
    requested_direction = _safe_string(
        first_jog.get("requested_direction"),
        "first_jog_requested_direction_invalid",
        blocked_reasons,
    )
    applied_direction = _safe_string(
        first_jog.get("applied_direction"),
        "first_jog_applied_direction_invalid",
        blocked_reasons,
    )
    gate_status = _safe_string(
        first_jog.get("hil_checklist_gate_status"),
        "first_jog_gate_status_invalid",
        blocked_reasons,
    )
    speed = _safe_float(first_jog.get("clamped_speed_mps"), "first_jog_speed_invalid", blocked_reasons)
    duration = _safe_int(first_jog.get("clamped_duration_ms"), "first_jog_duration_invalid", blocked_reasons)
    checklist_confirmed = _safe_bool(
        first_jog.get("confirm_hil_checklist"),
        "first_jog_confirm_hil_checklist_invalid",
        blocked_reasons,
    )
    if speed is not None and speed <= 0:
        blocked_reasons.append("first_jog_speed_nonpositive")
    if duration is not None and duration <= 0:
        blocked_reasons.append("first_jog_duration_nonpositive")
    if applied_direction not in {"forward", "back", "left", "right", "stop"}:
        blocked_reasons.append("first_jog_applied_direction_unexpected")
    if checklist_confirmed is False:
        blocked_reasons.append("first_jog_confirm_hil_checklist_false")
    if gate_status is not None and gate_status != "manual_allowed":
        blocked_reasons.append("first_jog_gate_status_not_manual_allowed")
    summary = None
    if (
        requested_direction is not None
        and applied_direction is not None
        and gate_status is not None
        and speed is not None
        and duration is not None
        and checklist_confirmed is True
        and gate_status == "manual_allowed"
    ):
        summary = {
            "proxy_status": "command_forwarded",
            "requested_direction": requested_direction,
            "applied_direction": applied_direction,
            "clamped_speed_mps": speed,
            "clamped_duration_ms": duration,
            "hil_checklist_gate_status": gate_status,
            "confirm_hil_checklist": checklist_confirmed,
        }
        return True, summary
    return False, summary


def _parse_feedback_samples(feedback_samples: dict[str, Any], blocked_reasons: list[str]) -> tuple[bool, dict[str, Any] | None]:
    """消费 feedback sample 摘要，验证 130/1001 观察链。"""
    if feedback_samples.get("schema") != EXPECTED_SCHEMAS["feedback_samples"]:
        blocked_reasons.append("feedback_samples_schema_mismatch")
        return False, None
    if feedback_samples.get("proxy_status") != "samples_forwarded" or feedback_samples.get("status") != "loaded":
        blocked_reasons.append("feedback_samples_not_forwarded")
        return False, None
    if feedback_samples.get("safe_to_control") is True:
        blocked_reasons.append("dangerous_true_safe_to_control")
    if feedback_samples.get("delivery_success") is True:
        blocked_reasons.append("dangerous_true_delivery_success")
    sample_key_values = feedback_samples.get("sample_key_values")
    if not isinstance(sample_key_values, dict):
        blocked_reasons.append("feedback_sample_key_values_missing")
        return False, None
    requested_count = _safe_int(
        sample_key_values.get("requested_sample_count"),
        "feedback_requested_sample_count_invalid",
        blocked_reasons,
    )
    completed_count = _safe_int(
        sample_key_values.get("completed_sample_count"),
        "feedback_completed_sample_count_invalid",
        blocked_reasons,
    )
    t1001_count = _safe_int(
        sample_key_values.get("t1001_observed_count"),
        "feedback_t1001_observed_count_invalid",
        blocked_reasons,
    )
    all_samples_observed = _safe_bool(
        sample_key_values.get("all_samples_observed_t1001") == "true",
        "feedback_all_samples_observed_invalid",
        blocked_reasons,
    )
    feedback_ack_observed = _safe_bool(
        sample_key_values.get("feedback_ack_t1001_observed") == "true",
        "feedback_ack_observed_invalid",
        blocked_reasons,
    )
    observed_types = _parse_feedback_types(sample_key_values.get("observed_feedback_types"), blocked_reasons)
    if requested_count is not None and completed_count is not None and completed_count < requested_count:
        blocked_reasons.append("feedback_sample_count_incomplete")
    if t1001_count is not None and t1001_count <= 0:
        blocked_reasons.append("feedback_t1001_missing")
    if all_samples_observed is False:
        blocked_reasons.append("feedback_all_samples_not_t1001")
    if feedback_ack_observed is False:
        blocked_reasons.append("feedback_ack_t1001_not_observed")
    if 130 not in observed_types or 1001 not in observed_types:
        blocked_reasons.append("feedback_types_missing_130_or_1001")
    present = (
        requested_count is not None
        and completed_count is not None
        and t1001_count is not None
        and all_samples_observed is True
        and feedback_ack_observed is True
        and requested_count > 0
        and completed_count >= requested_count
        and t1001_count > 0
        and 130 in observed_types
        and 1001 in observed_types
    )
    summary = None
    if requested_count is not None and completed_count is not None and t1001_count is not None:
        summary = {
            "proxy_status": "samples_forwarded",
            "requested_sample_count": requested_count,
            "completed_sample_count": completed_count,
            "t1001_observed_count": t1001_count,
            "observed_feedback_types": observed_types,
            "all_samples_observed_t1001": bool(all_samples_observed),
            "feedback_ack_t1001_observed": bool(feedback_ack_observed),
        }
    return present, summary


def _parse_scan_delta(scan_delta: dict[str, Any], blocked_reasons: list[str]) -> tuple[bool, dict[str, Any] | None]:
    """消费 scan delta 数值摘要，不回显 before/after raw refs。"""
    if scan_delta.get("schema") != EXPECTED_SCHEMAS["scan_delta"]:
        blocked_reasons.append("scan_delta_schema_mismatch")
        return False, None
    paired_bins = _safe_int(scan_delta.get("paired_bins"), "scan_delta_paired_bins_invalid", blocked_reasons)
    valid_beam_count = _safe_int(
        scan_delta.get("valid_beam_count"),
        "scan_delta_valid_beam_count_invalid",
        blocked_reasons,
    )
    average_abs_delta_m = _safe_float(
        scan_delta.get("average_abs_delta_m"),
        "scan_delta_average_abs_delta_invalid",
        blocked_reasons,
    )
    median_abs_diff_m = _safe_float(
        scan_delta.get("median_abs_diff_m"),
        "scan_delta_median_abs_diff_invalid",
        blocked_reasons,
    )
    max_abs_delta_m = _safe_float(
        scan_delta.get("max_abs_delta_m"),
        "scan_delta_max_abs_delta_invalid",
        blocked_reasons,
    )
    changed_bin_ratio = _safe_float(
        scan_delta.get("changed_bin_ratio"),
        "scan_delta_changed_bin_ratio_invalid",
        blocked_reasons,
    )
    field_pack_pass = _safe_bool(scan_delta.get("field_pack_pass"), "scan_delta_field_pack_pass_invalid", blocked_reasons)
    review_script_pass = _safe_bool(
        scan_delta.get("review_script_pass"),
        "scan_delta_review_script_pass_invalid",
        blocked_reasons,
    )
    thresholds = scan_delta.get("thresholds")
    if not isinstance(thresholds, dict):
        blocked_reasons.append("scan_delta_thresholds_missing")
        thresholds = {}
    paired_bins_min = _safe_int(thresholds.get("paired_bins_min"), "scan_delta_threshold_paired_bins_invalid", blocked_reasons)
    median_min = _safe_float(
        thresholds.get("median_abs_diff_min_m"),
        "scan_delta_threshold_median_invalid",
        blocked_reasons,
    )
    changed_ratio_min = _safe_float(
        thresholds.get("changed_bin_ratio_min"),
        "scan_delta_threshold_changed_ratio_invalid",
        blocked_reasons,
    )
    present = (
        paired_bins is not None
        and valid_beam_count is not None
        and average_abs_delta_m is not None
        and median_abs_diff_m is not None
        and max_abs_delta_m is not None
        and changed_bin_ratio is not None
        and field_pack_pass is True
        and review_script_pass is True
        and paired_bins_min is not None
        and median_min is not None
        and changed_ratio_min is not None
        and paired_bins >= paired_bins_min
        and median_abs_diff_m >= median_min
        and changed_bin_ratio >= changed_ratio_min
    )
    if not present:
        blocked_reasons.append("scan_delta_not_proven")
    summary = None
    if (
        paired_bins is not None
        and valid_beam_count is not None
        and average_abs_delta_m is not None
        and median_abs_diff_m is not None
        and max_abs_delta_m is not None
        and changed_bin_ratio is not None
        and paired_bins_min is not None
        and median_min is not None
        and changed_ratio_min is not None
    ):
        summary = {
            "paired_bins": paired_bins,
            "valid_beam_count": valid_beam_count,
            "average_abs_delta_m": average_abs_delta_m,
            "median_abs_diff_m": median_abs_diff_m,
            "max_abs_delta_m": max_abs_delta_m,
            "changed_bin_ratio": changed_bin_ratio,
            "field_pack_pass": bool(field_pack_pass),
            "review_script_pass": bool(review_script_pass),
            "thresholds": {
                "paired_bins_min": paired_bins_min,
                "median_abs_diff_min_m": median_min,
                "changed_bin_ratio_min": changed_ratio_min,
            },
        }
    return present, summary


def _operator_claims_source(operator_report: dict[str, Any]) -> dict[str, Any] | None:
    """优先读顶层 structured_hil_claims，必要时回退 request_body。"""
    claims = operator_report.get("structured_hil_claims")
    if isinstance(claims, dict):
        return claims
    request_body = operator_report.get("request_body")
    if isinstance(request_body, dict) and isinstance(request_body.get("structured_hil_claims"), dict):
        return request_body["structured_hil_claims"]
    return None


def _project_run_token_from_text(value: Any) -> str | None:
    """从原始路径或 ref 中提取 run token，但不把原文带入输出。"""
    if not isinstance(value, str):
        return None
    return _extract_run_token(value)


def _parse_operator_report(
    operator_report: dict[str, Any],
    scan_delta_present: bool,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None, str | None]:
    """消费 operator claims，只保留现场判断布尔值和安全 site_state。"""
    if operator_report.get("schema") != EXPECTED_SCHEMAS["operator_report"]:
        blocked_reasons.append("operator_report_schema_mismatch")
        return False, None, None
    if str(operator_report.get("status", "")).startswith("loaded") is False:
        blocked_reasons.append("operator_report_status_invalid")
    claims = _operator_claims_source(operator_report)
    request_body = operator_report.get("request_body")
    if not isinstance(claims, dict) or not isinstance(request_body, dict):
        blocked_reasons.append("operator_claims_missing")
        return False, None, None
    operator_present = _safe_bool(
        request_body.get("operator_present"),
        "operator_present_invalid",
        blocked_reasons,
    )
    physical_clearance = _safe_bool(
        request_body.get("physical_clearance_confirmed"),
        "operator_physical_clearance_invalid",
        blocked_reasons,
    )
    emergency_stop_ready = _safe_bool(
        request_body.get("emergency_stop_ready"),
        "operator_emergency_stop_ready_invalid",
        blocked_reasons,
    )
    observed_stop = _safe_bool(request_body.get("observed_stop"), "operator_observed_stop_invalid", blocked_reasons)
    visible_content = _safe_bool(
        claims.get("visible_content_proven"),
        "operator_visible_content_invalid",
        blocked_reasons,
    )
    external_video_recorded = _safe_bool(
        claims.get("external_video_recorded"),
        "operator_external_video_invalid",
        blocked_reasons,
    )
    wheel_feedback_nonzero = _safe_bool(
        claims.get("wheel_feedback_lr_nonzero_proven"),
        "operator_wheel_feedback_invalid",
        blocked_reasons,
    )
    physical_motion_lidar_delta = _safe_bool(
        claims.get("physical_motion_lidar_delta_proven"),
        "operator_lidar_delta_invalid",
        blocked_reasons,
    )
    real_route_map_proven = _safe_bool(
        claims.get("real_route_map_proven"),
        "operator_real_route_map_invalid",
        blocked_reasons,
    )
    delivery_success = _safe_bool(
        claims.get("delivery_success"),
        "operator_delivery_success_invalid",
        blocked_reasons,
    )
    site_state = _safe_string(claims.get("site_state"), "operator_site_state_invalid", blocked_reasons)
    scan_delta_ref = claims.get("scan_delta_ref")
    if wheel_feedback_nonzero is True:
        blocked_reasons.append("dangerous_true_wheel_feedback_lr_nonzero_proven")
    if operator_present is False:
        blocked_reasons.append("operator_present_false")
    if physical_clearance is False:
        blocked_reasons.append("operator_physical_clearance_false")
    if emergency_stop_ready is False:
        blocked_reasons.append("operator_emergency_stop_ready_false")
    if observed_stop is False:
        blocked_reasons.append("operator_observed_stop_false")
    if visible_content is False:
        blocked_reasons.append("operator_visible_content_false")
    if external_video_recorded is True:
        blocked_reasons.append("operator_external_video_recorded_true")
    if real_route_map_proven is True:
        blocked_reasons.append("dangerous_true_real_route_map_proven")
    if delivery_success is True:
        blocked_reasons.append("dangerous_true_delivery_success")
    if physical_motion_lidar_delta is True and scan_delta_present is not True:
        blocked_reasons.append("operator_scan_delta_claim_mismatch")
    if physical_motion_lidar_delta is not True:
        blocked_reasons.append("operator_scan_delta_claim_missing")
    run_token = _project_run_token_from_text(scan_delta_ref)
    present = (
        operator_present is True
        and physical_clearance is True
        and emergency_stop_ready is True
        and observed_stop is True
        and visible_content is True
        and external_video_recorded is False
        and wheel_feedback_nonzero is False
        and physical_motion_lidar_delta is True
        and real_route_map_proven is False
        and delivery_success is False
        and site_state is not None
        and run_token is not None
    )
    summary = None
    if site_state is not None:
        summary = {
            "operator_present": bool(operator_present),
            "physical_clearance_confirmed": bool(physical_clearance),
            "emergency_stop_ready": bool(emergency_stop_ready),
            "observed_stop": bool(observed_stop),
            "external_video_recorded": bool(external_video_recorded),
            "visible_content_proven": bool(visible_content),
            "wheel_feedback_lr_nonzero_proven": bool(wheel_feedback_nonzero),
            "physical_motion_lidar_delta_proven": bool(physical_motion_lidar_delta),
            "real_route_map_proven": bool(real_route_map_proven),
            "site_state": site_state,
        }
    return present, summary, run_token


def _parse_pixel_review(
    review: dict[str, Any],
    pgm_path: Path,
    label: str,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """像素 review 只承认结构化统计，不回显 raw path。"""
    if review.get("schema") != EXPECTED_SCHEMAS["pixel_review"]:
        blocked_reasons.append(f"{label}_pixel_review_schema_mismatch")
        return False, None
    file_ref = _safe_string(review.get("file"), f"{label}_pixel_review_file_invalid", blocked_reasons)
    mismatch_found = False
    if file_ref is not None and Path(file_ref).name != pgm_path.name:
        blocked_reasons.append(f"{label}_pixel_review_file_mismatch")
        mismatch_found = True
    magic = _safe_string(review.get("magic"), f"{label}_pixel_review_magic_invalid", blocked_reasons)
    width = _safe_int(review.get("width"), f"{label}_pixel_review_width_invalid", blocked_reasons)
    height = _safe_int(review.get("height"), f"{label}_pixel_review_height_invalid", blocked_reasons)
    max_value = _safe_int(review.get("max_value"), f"{label}_pixel_review_max_value_invalid", blocked_reasons)
    total_pixels = _safe_int(review.get("total_pixels"), f"{label}_pixel_review_total_pixels_invalid", blocked_reasons)
    free_pixel_count = _safe_int(
        review.get("free_pixel_count"),
        f"{label}_pixel_review_free_pixel_count_invalid",
        blocked_reasons,
    )
    unknown_pixel_count = _safe_int(
        review.get("unknown_pixel_count"),
        f"{label}_pixel_review_unknown_pixel_count_invalid",
        blocked_reasons,
    )
    occupied_pixel_count = _safe_int(
        review.get("occupied_pixel_count"),
        f"{label}_pixel_review_occupied_pixel_count_invalid",
        blocked_reasons,
    )
    has_free_cells = _safe_bool(
        review.get("has_free_cells"),
        f"{label}_pixel_review_has_free_cells_invalid",
        blocked_reasons,
    )
    pgm_header = _read_pgm_header(pgm_path)
    if magic is not None and magic != pgm_header["magic"]:
        blocked_reasons.append(f"{label}_pixel_review_magic_mismatch")
        mismatch_found = True
    if width is not None and width != pgm_header["width"]:
        blocked_reasons.append(f"{label}_pixel_review_width_mismatch")
        mismatch_found = True
    if height is not None and height != pgm_header["height"]:
        blocked_reasons.append(f"{label}_pixel_review_height_mismatch")
        mismatch_found = True
    if max_value is not None and max_value != pgm_header["max_value"]:
        blocked_reasons.append(f"{label}_pixel_review_max_value_mismatch")
        mismatch_found = True
    if (
        width is not None
        and height is not None
        and total_pixels is not None
        and total_pixels != width * height
    ):
        blocked_reasons.append(f"{label}_pixel_review_total_pixels_mismatch")
        mismatch_found = True
    if (
        free_pixel_count is not None
        and unknown_pixel_count is not None
        and occupied_pixel_count is not None
        and total_pixels is not None
        and free_pixel_count + unknown_pixel_count + occupied_pixel_count != total_pixels
    ):
        blocked_reasons.append(f"{label}_pixel_review_count_sum_mismatch")
        mismatch_found = True
    if has_free_cells is not False:
        blocked_reasons.append(f"{label}_pixel_review_has_free_cells_not_false")
        mismatch_found = True
    present = (
        magic is not None
        and width is not None
        and height is not None
        and max_value is not None
        and total_pixels is not None
        and free_pixel_count is not None
        and unknown_pixel_count is not None
        and occupied_pixel_count is not None
        and has_free_cells is False
        and mismatch_found is False
    )
    summary = None
    if width is not None and height is not None and total_pixels is not None:
        summary = {
            "pgm_artifact_name": pgm_path.name,
            "magic": magic,
            "width": width,
            "height": height,
            "max_value": max_value,
            "total_pixels": total_pixels,
            "free_pixel_count": free_pixel_count,
            "unknown_pixel_count": unknown_pixel_count,
            "occupied_pixel_count": occupied_pixel_count,
            "has_free_cells": bool(has_free_cells),
        }
    return present, summary


def _parse_map_group(
    label: str,
    yaml_data: dict[str, Any],
    pgm_path: Path,
    pixel_review: dict[str, Any],
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None, dict[str, Any] | None, str | None]:
    """把单个 map 组三件套压缩成只读摘要。"""
    image_name = _safe_string(yaml_data.get("image"), f"{label}_map_image_invalid", blocked_reasons)
    resolution = _safe_float(yaml_data.get("resolution"), f"{label}_map_resolution_invalid", blocked_reasons)
    free_thresh = _safe_float(yaml_data.get("free_thresh"), f"{label}_map_free_thresh_invalid", blocked_reasons)
    occupied_thresh = _safe_float(
        yaml_data.get("occupied_thresh"),
        f"{label}_map_occupied_thresh_invalid",
        blocked_reasons,
    )
    negate = _safe_int(yaml_data.get("negate"), f"{label}_map_negate_invalid", blocked_reasons)
    origin = yaml_data.get("origin")
    if not isinstance(origin, list) or len(origin) != 3 or not all(_is_finite_number(item) for item in origin):
        blocked_reasons.append(f"{label}_map_origin_invalid")
        origin = None
    pixel_present, pixel_summary = _parse_pixel_review(pixel_review, pgm_path, label, blocked_reasons)
    run_token = _extract_run_token(image_name)
    if run_token is None:
        blocked_reasons.append(f"{label}_map_run_token_missing")
    present = (
        image_name is not None
        and resolution is not None
        and free_thresh is not None
        and occupied_thresh is not None
        and negate is not None
        and origin is not None
        and pixel_present is True
        and run_token is not None
    )
    summary = None
    if image_name is not None and resolution is not None and free_thresh is not None and occupied_thresh is not None and negate is not None and origin is not None:
        summary = {
            "map_yaml_name": image_name,
            "pgm_artifact_name": pgm_path.name,
            "resolution": resolution,
            "free_thresh": free_thresh,
            "occupied_thresh": occupied_thresh,
            "negate": negate,
            "origin": [float(item) for item in origin],
        }
    return present, summary, pixel_summary, run_token


def _parse_free_cell_lifecycle_start(
    lifecycle: dict[str, Any],
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None, str | None]:
    """消费 map start material，只保留生命周期状态和安全 map name。"""
    _append_dangerous_true(lifecycle, "free_cell_lifecycle", blocked_reasons)
    if lifecycle.get("schema") != EXPECTED_SCHEMAS["map_lifecycle"]:
        blocked_reasons.append("free_cell_lifecycle_schema_mismatch")
        return False, None, None
    action = _safe_string(lifecycle.get("action"), "free_cell_lifecycle_action_invalid", blocked_reasons)
    proxy_status = _safe_string(
        lifecycle.get("proxy_status"),
        "free_cell_lifecycle_proxy_status_invalid",
        blocked_reasons,
    )
    status = _safe_string(lifecycle.get("status"), "free_cell_lifecycle_status_invalid", blocked_reasons)
    source = _safe_string(lifecycle.get("source"), "free_cell_lifecycle_source_invalid", blocked_reasons)
    proof_status = _safe_string(
        lifecycle.get("proof_status"),
        "free_cell_lifecycle_proof_status_invalid",
        blocked_reasons,
    )
    pc_only = _safe_bool(lifecycle.get("pc_only"), "free_cell_lifecycle_pc_only_invalid", blocked_reasons)
    remote_method = _safe_string(
        lifecycle.get("remote_method"),
        "free_cell_lifecycle_remote_method_invalid",
        blocked_reasons,
    )
    remote_status = _safe_int(
        lifecycle.get("remote_http_status"),
        "free_cell_lifecycle_remote_status_invalid",
        blocked_reasons,
    )
    map_needs_rebuild = _safe_bool(
        lifecycle.get("map_needs_rebuild"),
        "free_cell_lifecycle_map_needs_rebuild_invalid",
        blocked_reasons,
    )
    command_result = lifecycle.get("command_result")
    request_body = lifecycle.get("request_body")
    if not isinstance(command_result, dict):
        blocked_reasons.append("free_cell_lifecycle_command_result_missing")
        command_result = {}
    if not isinstance(request_body, dict):
        blocked_reasons.append("free_cell_lifecycle_request_body_missing")
        request_body = {}
    command_mode = _safe_string(
        command_result.get("mode"),
        "free_cell_lifecycle_command_mode_invalid",
        blocked_reasons,
    )
    command_executed = _safe_bool(
        command_result.get("executed"),
        "free_cell_lifecycle_command_executed_invalid",
        blocked_reasons,
    )
    command_ok = _safe_bool(
        command_result.get("ok"),
        "free_cell_lifecycle_command_ok_invalid",
        blocked_reasons,
    )
    map_name = _safe_string(
        request_body.get("map_name"),
        "free_cell_lifecycle_map_name_invalid",
        blocked_reasons,
    )
    present = (
        action == "start"
        and proxy_status == "lifecycle_forwarded"
        and status == "loaded_fail_closed_summary"
        and source == "software_proof"
        and proof_status == "not_proven"
        and pc_only is True
        and remote_method == "POST"
        and remote_status == 200
        and map_needs_rebuild is False
        and command_mode == "map_lifecycle_proof_helper"
        and command_executed is True
        and command_ok is True
        and map_name is not None
    )
    if not present:
        blocked_reasons.append("free_cell_lifecycle_not_ready")
    summary = None
    if map_name is not None:
        summary = {
            "action": action,
            "proxy_status": proxy_status,
            "status": status,
            "remote_method": remote_method,
            "remote_http_status": remote_status,
            "map_name": map_name,
            "command_mode": command_mode,
            "command_executed": bool(command_executed),
            "command_ok": bool(command_ok),
        }
    return present, summary, map_name


def _parse_free_cell_map_list(
    map_list: dict[str, Any],
    expected_map_name: str | None,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """消费 map list material，确认 free-cell map 已成为唯一 usable map。"""
    _append_dangerous_true(map_list, "free_cell_map_list", blocked_reasons)
    if map_list.get("schema") != EXPECTED_SCHEMAS["map_lifecycle"]:
        blocked_reasons.append("free_cell_map_list_schema_mismatch")
        return False, None
    action = _safe_string(map_list.get("action"), "free_cell_map_list_action_invalid", blocked_reasons)
    proxy_status = _safe_string(
        map_list.get("proxy_status"),
        "free_cell_map_list_proxy_status_invalid",
        blocked_reasons,
    )
    status = _safe_string(map_list.get("status"), "free_cell_map_list_status_invalid", blocked_reasons)
    source = _safe_string(map_list.get("source"), "free_cell_map_list_source_invalid", blocked_reasons)
    proof_status = _safe_string(
        map_list.get("proof_status"),
        "free_cell_map_list_proof_status_invalid",
        blocked_reasons,
    )
    pc_only = _safe_bool(map_list.get("pc_only"), "free_cell_map_list_pc_only_invalid", blocked_reasons)
    remote_method = _safe_string(
        map_list.get("remote_method"),
        "free_cell_map_list_remote_method_invalid",
        blocked_reasons,
    )
    remote_status = _safe_int(
        map_list.get("remote_http_status"),
        "free_cell_map_list_remote_status_invalid",
        blocked_reasons,
    )
    map_usable_for_navigation = _safe_bool(
        map_list.get("map_usable_for_navigation"),
        "free_cell_map_list_navigation_flag_invalid",
        blocked_reasons,
    )
    map_quality = map_list.get("map_quality_summary")
    command_result = map_list.get("command_result")
    if not isinstance(map_quality, dict):
        blocked_reasons.append("free_cell_map_quality_summary_missing")
        map_quality = {}
    if not isinstance(command_result, dict):
        blocked_reasons.append("free_cell_map_list_command_result_missing")
        command_result = {}
    quality_status = _safe_string(
        map_quality.get("status"),
        "free_cell_map_quality_status_invalid",
        blocked_reasons,
    )
    checked_yaml_count = _safe_int(
        map_quality.get("checked_yaml_count"),
        "free_cell_map_checked_yaml_count_invalid",
        blocked_reasons,
    )
    usable_map_count = _safe_int(
        map_quality.get("usable_map_count"),
        "free_cell_map_usable_map_count_invalid",
        blocked_reasons,
    )
    no_free_cell_map_count = _safe_int(
        map_quality.get("no_free_cell_map_count"),
        "free_cell_map_no_free_cell_count_invalid",
        blocked_reasons,
    )
    analysis_failed_count = _safe_int(
        map_quality.get("analysis_failed_count"),
        "free_cell_map_analysis_failed_count_invalid",
        blocked_reasons,
    )
    command_mode = _safe_string(
        command_result.get("mode"),
        "free_cell_map_list_command_mode_invalid",
        blocked_reasons,
    )
    command_executed = _safe_bool(
        command_result.get("executed"),
        "free_cell_map_list_command_executed_invalid",
        blocked_reasons,
    )
    command_ok = _safe_bool(command_result.get("ok"), "free_cell_map_list_command_ok_invalid", blocked_reasons)
    map_names = map_list.get("map_names")
    matched_map_yaml_name = None
    if not isinstance(map_names, list):
        blocked_reasons.append("free_cell_map_names_invalid")
    else:
        for index, item in enumerate(map_names):
            safe_item = _safe_string(item, f"free_cell_map_name_{index}_invalid", blocked_reasons)
            if expected_map_name is not None and safe_item == f"{expected_map_name}.yaml":
                matched_map_yaml_name = safe_item
    if expected_map_name is not None and matched_map_yaml_name is None:
        blocked_reasons.append("free_cell_map_name_not_listed")
    if quality_status != "has_usable_map":
        blocked_reasons.append("free_cell_map_list_not_has_usable_map")
    if usable_map_count != 1:
        blocked_reasons.append("free_cell_usable_map_count_not_one")
    if map_usable_for_navigation is not True:
        blocked_reasons.append("free_cell_map_not_usable_for_navigation")
    present = (
        action == "list"
        and proxy_status == "lifecycle_forwarded"
        and status == "loaded_fail_closed_summary"
        and source == "software_proof"
        and proof_status == "not_proven"
        and pc_only is True
        and remote_method == "GET"
        and remote_status == 200
        and quality_status == "has_usable_map"
        and checked_yaml_count is not None
        and usable_map_count == 1
        and no_free_cell_map_count is not None
        and analysis_failed_count == 0
        and map_usable_for_navigation is True
        and command_mode == "read_only_local_files"
        and command_executed is False
        and command_ok is True
        and matched_map_yaml_name is not None
    )
    summary = None
    if usable_map_count is not None:
        summary = {
            "action": action,
            "proxy_status": proxy_status,
            "status": status,
            "remote_method": remote_method,
            "remote_http_status": remote_status,
            "map_quality_status": quality_status,
            "checked_yaml_count": checked_yaml_count,
            "usable_map_count": usable_map_count,
            "no_free_cell_map_count": no_free_cell_map_count,
            "analysis_failed_count": analysis_failed_count,
            "map_usable_for_navigation": bool(map_usable_for_navigation),
            "matched_map_yaml_name": matched_map_yaml_name,
            "command_mode": command_mode,
            "command_executed": bool(command_executed),
            "command_ok": bool(command_ok),
        }
    return present, summary


def _parse_free_cell_pixel_review(
    review: dict[str, Any],
    pgm_path: Path,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """free-cell review 必须和 PGM header 匹配，且 free count 固定为 394。"""
    if review.get("schema") != EXPECTED_SCHEMAS["pixel_review"]:
        blocked_reasons.append("free_cell_pixel_review_schema_mismatch")
        return False, None
    file_ref = _safe_string(review.get("file"), "free_cell_pixel_review_file_invalid", blocked_reasons)
    mismatch_found = False
    if file_ref is not None and Path(file_ref).name != pgm_path.name:
        blocked_reasons.append("free_cell_pixel_review_file_mismatch")
        mismatch_found = True
    magic = _safe_string(review.get("magic"), "free_cell_pixel_review_magic_invalid", blocked_reasons)
    width = _safe_int(review.get("width"), "free_cell_pixel_review_width_invalid", blocked_reasons)
    height = _safe_int(review.get("height"), "free_cell_pixel_review_height_invalid", blocked_reasons)
    max_value = _safe_int(review.get("max_value"), "free_cell_pixel_review_max_value_invalid", blocked_reasons)
    total_pixels = _safe_int(review.get("total_pixels"), "free_cell_pixel_review_total_pixels_invalid", blocked_reasons)
    free_pixel_count = _safe_int(
        review.get("free_pixel_count"),
        "free_cell_pixel_review_free_pixel_count_invalid",
        blocked_reasons,
    )
    unknown_pixel_count = _safe_int(
        review.get("unknown_pixel_count"),
        "free_cell_pixel_review_unknown_pixel_count_invalid",
        blocked_reasons,
    )
    occupied_pixel_count = _safe_int(
        review.get("occupied_pixel_count"),
        "free_cell_pixel_review_occupied_pixel_count_invalid",
        blocked_reasons,
    )
    has_free_cells = _safe_bool(
        review.get("has_free_cells"),
        "free_cell_pixel_review_has_free_cells_invalid",
        blocked_reasons,
    )
    counts = review.get("counts")
    counts_free = None
    if not isinstance(counts, dict):
        blocked_reasons.append("free_cell_pixel_review_counts_invalid")
    else:
        counts_free = _safe_int(
            counts.get("254"),
            "free_cell_pixel_review_counts_free_invalid",
            blocked_reasons,
        )
    pgm_header = _read_pgm_header(pgm_path)
    if magic is not None and magic != pgm_header["magic"]:
        blocked_reasons.append("free_cell_pixel_review_magic_mismatch")
        mismatch_found = True
    if width is not None and width != pgm_header["width"]:
        blocked_reasons.append("free_cell_pixel_review_width_mismatch")
        mismatch_found = True
    if height is not None and height != pgm_header["height"]:
        blocked_reasons.append("free_cell_pixel_review_height_mismatch")
        mismatch_found = True
    if max_value is not None and max_value != pgm_header["max_value"]:
        blocked_reasons.append("free_cell_pixel_review_max_value_mismatch")
        mismatch_found = True
    if width is not None and height is not None and total_pixels is not None and total_pixels != width * height:
        blocked_reasons.append("free_cell_pixel_review_total_pixels_mismatch")
        mismatch_found = True
    if (
        free_pixel_count is not None
        and unknown_pixel_count is not None
        and occupied_pixel_count is not None
        and total_pixels is not None
        and free_pixel_count + unknown_pixel_count + occupied_pixel_count != total_pixels
    ):
        blocked_reasons.append("free_cell_pixel_review_count_sum_mismatch")
        mismatch_found = True
    if free_pixel_count != EXPECTED_FREE_CELL_PIXEL_COUNT:
        blocked_reasons.append("free_cell_pixel_count_not_394")
        mismatch_found = True
    if counts_free != EXPECTED_FREE_CELL_PIXEL_COUNT:
        blocked_reasons.append("free_cell_pixel_review_counts_free_not_394")
        mismatch_found = True
    if has_free_cells is not True:
        blocked_reasons.append("free_cell_has_free_cells_not_true")
        mismatch_found = True
    present = (
        magic is not None
        and width is not None
        and height is not None
        and max_value is not None
        and total_pixels is not None
        and free_pixel_count == EXPECTED_FREE_CELL_PIXEL_COUNT
        and unknown_pixel_count is not None
        and occupied_pixel_count is not None
        and counts_free == EXPECTED_FREE_CELL_PIXEL_COUNT
        and has_free_cells is True
        and mismatch_found is False
    )
    summary = None
    if width is not None and height is not None and total_pixels is not None:
        summary = {
            "pgm_artifact_name": pgm_path.name,
            "magic": magic,
            "width": width,
            "height": height,
            "max_value": max_value,
            "total_pixels": total_pixels,
            "free_pixel_count": free_pixel_count,
            "unknown_pixel_count": unknown_pixel_count,
            "occupied_pixel_count": occupied_pixel_count,
            "has_free_cells": bool(has_free_cells),
        }
    return present, summary


def _parse_free_cell_map_group(
    yaml_data: dict[str, Any],
    pgm_path: Path,
    pixel_review: dict[str, Any],
    expected_map_name: str | None,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None, dict[str, Any] | None, str | None]:
    """确认 YAML 指向的 map basename、PGM header 和 pixel review 是同一组材料。"""
    image_name = _safe_string(yaml_data.get("image"), "free_cell_map_image_invalid", blocked_reasons)
    expected_image_name = f"{expected_map_name}.pgm" if expected_map_name else None
    if image_name is not None and expected_image_name is not None and image_name != expected_image_name:
        blocked_reasons.append("free_cell_yaml_pgm_basename_mismatch")
    resolution = _safe_float(yaml_data.get("resolution"), "free_cell_map_resolution_invalid", blocked_reasons)
    free_thresh = _safe_float(yaml_data.get("free_thresh"), "free_cell_map_free_thresh_invalid", blocked_reasons)
    occupied_thresh = _safe_float(
        yaml_data.get("occupied_thresh"),
        "free_cell_map_occupied_thresh_invalid",
        blocked_reasons,
    )
    negate = _safe_int(yaml_data.get("negate"), "free_cell_map_negate_invalid", blocked_reasons)
    origin = yaml_data.get("origin")
    if not isinstance(origin, list) or len(origin) != 3 or not all(_is_finite_number(item) for item in origin):
        blocked_reasons.append("free_cell_map_origin_invalid")
        origin = None
    pixel_present, pixel_summary = _parse_free_cell_pixel_review(pixel_review, pgm_path, blocked_reasons)
    run_token = _extract_run_token(image_name)
    if run_token is None:
        blocked_reasons.append("free_cell_map_run_token_missing")
    present = (
        image_name is not None
        and expected_image_name is not None
        and image_name == expected_image_name
        and resolution is not None
        and free_thresh is not None
        and occupied_thresh is not None
        and negate is not None
        and origin is not None
        and pixel_present is True
        and run_token is not None
    )
    summary = None
    if image_name is not None and resolution is not None and free_thresh is not None and occupied_thresh is not None and negate is not None and origin is not None:
        summary = {
            "map_yaml_image": image_name,
            "pgm_artifact_name": pgm_path.name,
            "map_basename": expected_map_name,
            "resolution": resolution,
            "free_thresh": free_thresh,
            "occupied_thresh": occupied_thresh,
            "negate": negate,
            "origin": [float(item) for item in origin],
        }
    return present, summary, pixel_summary, run_token


def _parse_free_cell_pc_summary(
    pc_summary: dict[str, Any],
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """PC summary 只投影 allowlisted 状态，不消费 endpoint/camera/raw refs。"""
    _append_dangerous_true(pc_summary, "free_cell_pc_summary", blocked_reasons)
    if pc_summary.get("schema") != EXPECTED_SCHEMAS["pc_summary"]:
        blocked_reasons.append("free_cell_pc_summary_schema_mismatch")
        return False, None
    console_status = _safe_string(
        pc_summary.get("console_status"),
        "free_cell_pc_summary_console_status_invalid",
        blocked_reasons,
    )
    source = _safe_string(pc_summary.get("source"), "free_cell_pc_summary_source_invalid", blocked_reasons)
    proof_status = _safe_string(
        pc_summary.get("proof_status"),
        "free_cell_pc_summary_proof_status_invalid",
        blocked_reasons,
    )
    pc_only = _safe_bool(pc_summary.get("pc_only"), "free_cell_pc_summary_pc_only_invalid", blocked_reasons)
    readiness = pc_summary.get("first_jog_readiness_summary")
    operator_material = pc_summary.get("operator_hil_material_summary")
    o3_summary = pc_summary.get("o3_proof_summary")
    if not isinstance(readiness, dict):
        blocked_reasons.append("free_cell_pc_readiness_summary_missing")
        readiness = {}
    if not isinstance(operator_material, dict):
        blocked_reasons.append("free_cell_pc_operator_material_missing")
        operator_material = {}
    if not isinstance(o3_summary, dict):
        blocked_reasons.append("free_cell_pc_o3_summary_missing")
        o3_summary = {}
    readiness_status = _safe_string(
        readiness.get("status"),
        "free_cell_pc_readiness_status_invalid",
        blocked_reasons,
    )
    basic_safety_ready = _safe_bool(
        readiness.get("basic_safety_ready"),
        "free_cell_pc_basic_safety_ready_invalid",
        blocked_reasons,
    )
    visual_material_ready = _safe_bool(
        readiness.get("visual_material_ready"),
        "free_cell_pc_visual_material_ready_invalid",
        blocked_reasons,
    )
    next_action = _safe_string(
        readiness.get("next_action"),
        "free_cell_pc_next_action_invalid",
        blocked_reasons,
    )
    missing_fields = readiness.get("missing_fields")
    if not isinstance(missing_fields, list):
        blocked_reasons.append("free_cell_pc_missing_fields_invalid")
        missing_fields_count = None
    else:
        missing_fields_count = len(missing_fields)
        for index, item in enumerate(missing_fields):
            _safe_string(item, f"free_cell_pc_missing_field_{index}_invalid", blocked_reasons)
    operator_status = _safe_string(
        operator_material.get("status"),
        "free_cell_pc_operator_status_invalid",
        blocked_reasons,
    )
    report_status = _safe_string(
        operator_material.get("report_status"),
        "free_cell_pc_operator_report_status_invalid",
        blocked_reasons,
    )
    operator_present = _safe_string_bool(
        operator_material.get("operator_present"),
        "free_cell_pc_operator_present_invalid",
        blocked_reasons,
    )
    physical_clearance = _safe_string_bool(
        operator_material.get("physical_clearance"),
        "free_cell_pc_physical_clearance_invalid",
        blocked_reasons,
    )
    emergency_stop = _safe_string_bool(
        operator_material.get("emergency_stop"),
        "free_cell_pc_emergency_stop_invalid",
        blocked_reasons,
    )
    external_video_false = _safe_prefixed_false(
        operator_material.get("external_video"),
        "free_cell_pc_external_video_invalid",
        blocked_reasons,
    )
    wheel_feedback_false = _safe_prefixed_false(
        operator_material.get("wheel_feedback"),
        "free_cell_pc_wheel_feedback_invalid",
        blocked_reasons,
    )
    route_map_false = _safe_prefixed_false(
        operator_material.get("route_map"),
        "free_cell_pc_route_map_invalid",
        blocked_reasons,
    )
    delivery_claim = _safe_string_bool(
        operator_material.get("delivery_claim"),
        "free_cell_pc_delivery_claim_invalid",
        blocked_reasons,
    )
    site_state = _safe_string(
        operator_material.get("site_state"),
        "free_cell_pc_site_state_invalid",
        blocked_reasons,
    )
    managed_runtime_started = _safe_bool(
        o3_summary.get("managed_runtime_started"),
        "free_cell_pc_managed_runtime_started_invalid",
        blocked_reasons,
    )
    map_once_observed = _safe_bool(
        o3_summary.get("map_once_observed"),
        "free_cell_pc_map_once_observed_invalid",
        blocked_reasons,
    )
    amcl_pose_observed = _safe_bool(
        o3_summary.get("amcl_pose_observed"),
        "free_cell_pc_amcl_pose_observed_invalid",
        blocked_reasons,
    )
    path_point_count = _safe_int(
        o3_summary.get("path_point_count"),
        "free_cell_pc_path_point_count_invalid",
        blocked_reasons,
    )
    present = (
        console_status == "loaded_fail_closed_summary"
        and source == "software_proof"
        and proof_status == "not_proven"
        and pc_only is True
        and readiness_status == "ready_for_first_jog"
        and basic_safety_ready is True
        and visual_material_ready is True
        and next_action == "press_try_move"
        and missing_fields_count == 0
        and operator_status == "loaded"
        and report_status == "ready_for_execution"
        and operator_present is True
        and physical_clearance is True
        and emergency_stop is True
        and external_video_false is True
        and wheel_feedback_false is True
        and route_map_false is True
        and delivery_claim is False
        and site_state is not None
        and managed_runtime_started is True
        and map_once_observed is True
        and amcl_pose_observed is True
        and path_point_count == 0
    )
    if not present:
        blocked_reasons.append("free_cell_pc_summary_not_ready")
    summary = None
    if site_state is not None:
        summary = {
            "console_status": console_status,
            "readiness_status": readiness_status,
            "basic_safety_ready": bool(basic_safety_ready),
            "visual_material_ready": bool(visual_material_ready),
            "missing_fields_count": missing_fields_count,
            "next_action": next_action,
            "operator_status": operator_status,
            "operator_report_status": report_status,
            "operator_present": bool(operator_present),
            "physical_clearance": bool(physical_clearance),
            "emergency_stop": bool(emergency_stop),
            "external_video_recorded": False,
            "wheel_feedback_lr_nonzero_proven": False,
            "route_map_proven": False,
            "delivery_claim": False,
            "site_state": site_state,
            "managed_runtime_started": bool(managed_runtime_started),
            "map_once_observed": bool(map_once_observed),
            "amcl_pose_observed": bool(amcl_pose_observed),
            "path_point_count": path_point_count,
        }
    return present, summary


def _parse_localization_tf_observed(
    value: Any,
    label: str,
    blocked_reasons: list[str],
) -> tuple[bool, bool, dict[str, bool] | None]:
    """TF 字段必须结构化解析；字符串包含判断不够安全。"""
    parsed = value
    if isinstance(value, str):
        if UNSAFE_VALUE_PATTERN.search(value):
            blocked_reasons.append(f"{label}_tf_json_invalid")
            return False, False, None
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            blocked_reasons.append(f"{label}_tf_json_invalid")
            return False, False, None
    if not isinstance(parsed, dict):
        blocked_reasons.append(f"{label}_tf_missing")
        return False, False, None
    map_to_odom = _safe_bool(parsed.get("map_to_odom"), f"{label}_tf_map_to_odom_invalid", blocked_reasons)
    map_to_base_link = _safe_bool(
        parsed.get("map_to_base_link"),
        f"{label}_tf_map_to_base_link_invalid",
        blocked_reasons,
    )
    if map_to_odom is not True:
        blocked_reasons.append(f"{label}_tf_map_to_odom_not_true")
    if map_to_base_link is not True:
        blocked_reasons.append(f"{label}_tf_map_to_base_link_not_true")
    summary = None
    if map_to_odom is not None and map_to_base_link is not None:
        summary = {
            "map_to_odom": bool(map_to_odom),
            "map_to_base_link": bool(map_to_base_link),
        }
    return map_to_odom is True, map_to_base_link is True, summary


def _endpoint_key_values(endpoint: dict[str, Any], endpoint_id: str, blocked_reasons: list[str]) -> dict[str, Any]:
    """只返回 endpoint 的 key_values；其他 raw context 一律不进入摘要。"""
    key_values = endpoint.get("key_values")
    if not isinstance(key_values, dict):
        blocked_reasons.append(f"localization_path_key_values_missing_{endpoint_id}")
        return {}
    for field in REQUIRED_LOCALIZATION_FALSE_FIELDS:
        parsed = _safe_string_bool(
            key_values.get(field),
            f"localization_path_{endpoint_id}_{field}_invalid",
            blocked_reasons,
        )
        if parsed is not False:
            blocked_reasons.append(f"localization_path_{endpoint_id}_dangerous_true_{field}")
    for field in OPTIONAL_LOCALIZATION_FALSE_FIELDS:
        if field not in key_values:
            continue
        parsed = _safe_string_bool(
            key_values.get(field),
            f"localization_path_{endpoint_id}_{field}_invalid",
            blocked_reasons,
        )
        if parsed is not False:
            blocked_reasons.append(f"localization_path_{endpoint_id}_dangerous_true_{field}")
    return key_values


def _validate_endpoint_status(
    endpoint: dict[str, Any],
    endpoint_id: str,
    expected_path: str,
    expected_schema: str,
    blocked_reasons: list[str],
) -> None:
    """endpoint 只用于校验，不回显，避免把 /api/... 泄露到 positive 输出。"""
    if endpoint.get("endpoint") != expected_path:
        blocked_reasons.append(f"localization_path_endpoint_mismatch_{endpoint_id}")
    request_status = _safe_string(
        endpoint.get("request_status"),
        f"localization_path_request_status_invalid_{endpoint_id}",
        blocked_reasons,
    )
    http_status = _safe_int(
        endpoint.get("http_status"),
        f"localization_path_http_status_invalid_{endpoint_id}",
        blocked_reasons,
    )
    schema = _safe_string(
        endpoint.get("schema"),
        f"localization_path_endpoint_schema_invalid_{endpoint_id}",
        blocked_reasons,
    )
    if request_status != "loaded":
        blocked_reasons.append(f"localization_path_request_not_loaded_{endpoint_id}")
    if http_status != 200:
        blocked_reasons.append(f"localization_path_http_not_200_{endpoint_id}")
    if schema != expected_schema:
        blocked_reasons.append(f"localization_path_endpoint_schema_mismatch_{endpoint_id}")
    endpoint_blocked_reasons = endpoint.get("blocked_reasons")
    if not isinstance(endpoint_blocked_reasons, list):
        blocked_reasons.append(f"localization_path_endpoint_blocked_reasons_invalid_{endpoint_id}")
    else:
        for index, item in enumerate(endpoint_blocked_reasons):
            _safe_string(
                item,
                f"localization_path_endpoint_blocked_reason_{endpoint_id}_{index}_invalid",
                blocked_reasons,
            )
        if endpoint_blocked_reasons:
            blocked_reasons.append(f"localization_path_endpoint_blocked_reasons_present_{endpoint_id}")
    dangerous_true_fields = endpoint.get("dangerous_true_fields")
    if not isinstance(dangerous_true_fields, list):
        blocked_reasons.append(f"localization_path_dangerous_true_fields_invalid_{endpoint_id}")
    else:
        for index, item in enumerate(dangerous_true_fields):
            _safe_string(
                item,
                f"localization_path_dangerous_true_field_{endpoint_id}_{index}_invalid",
                blocked_reasons,
            )
        if dangerous_true_fields:
            blocked_reasons.append(f"localization_path_dangerous_true_fields_present_{endpoint_id}")


def _collect_required_localization_endpoints(
    pc_summary: dict[str, Any],
    blocked_reasons: list[str],
) -> dict[str, dict[str, Any]]:
    """按固定 id 收集 readback；缺任何 required endpoint 都 fail-closed。"""
    read_endpoints = pc_summary.get("read_endpoints")
    if not isinstance(read_endpoints, list):
        blocked_reasons.append("localization_path_read_endpoints_missing")
        return {}
    endpoint_map: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(read_endpoints):
        if not isinstance(entry, dict):
            blocked_reasons.append(f"localization_path_read_endpoint_{index}_invalid")
            continue
        endpoint_id = entry.get("id")
        if endpoint_id in REQUIRED_LOCALIZATION_ENDPOINTS:
            endpoint_map[str(endpoint_id)] = entry
    for endpoint_id, (expected_path, expected_schema) in REQUIRED_LOCALIZATION_ENDPOINTS.items():
        endpoint = endpoint_map.get(endpoint_id)
        if endpoint is None:
            blocked_reasons.append(f"localization_path_required_endpoint_missing_{endpoint_id}")
            continue
        _validate_endpoint_status(endpoint, endpoint_id, expected_path, expected_schema, blocked_reasons)
    return endpoint_map


def _append_same_run_path_tamper_reasons(
    endpoint_id: str,
    key_values: dict[str, Any],
    blocked_reasons: list[str],
) -> None:
    """same-run path 当前必须失败；任何成功形态都要锁成 blocked。"""
    for field in ("path_generation_succeeded", "path_generated", "latest_path_generated"):
        if field not in key_values:
            continue
        parsed = _safe_string_bool(
            key_values.get(field),
            f"same_run_{endpoint_id}_{field}_invalid",
            blocked_reasons,
        )
        if parsed is True:
            blocked_reasons.append(f"same_run_{endpoint_id}_{field}_unexpected_true")
    if "path_point_count" in key_values:
        point_count = _safe_int(
            key_values.get("path_point_count"),
            f"same_run_{endpoint_id}_path_point_count_invalid",
            blocked_reasons,
        )
        if point_count is not None and point_count > 0:
            blocked_reasons.append(f"same_run_{endpoint_id}_path_point_count_unexpected_positive")


def _parse_localization_path_material_bridge(
    pc_summary: dict[str, Any],
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """消费 38 的同 run localization/path readback，且固定 path not proven。"""
    local_reasons: list[str] = []
    _append_dangerous_true(pc_summary, "localization_path_pc_summary", local_reasons)
    if pc_summary.get("schema") != EXPECTED_SCHEMAS["pc_summary"]:
        local_reasons.append("localization_path_pc_summary_schema_mismatch")
        blocked_reasons.extend(local_reasons)
        return False, None
    endpoint_map = _collect_required_localization_endpoints(pc_summary, local_reasons)
    key_values_by_id: dict[str, dict[str, Any]] = {}
    for endpoint_id in REQUIRED_LOCALIZATION_ENDPOINTS:
        endpoint = endpoint_map.get(endpoint_id)
        if endpoint is None:
            key_values_by_id[endpoint_id] = {}
            continue
        key_values = _endpoint_key_values(endpoint, endpoint_id, local_reasons)
        _append_same_run_path_tamper_reasons(endpoint_id, key_values, local_reasons)
        key_values_by_id[endpoint_id] = key_values

    status_values = key_values_by_id.get("status", {})
    map_values = key_values_by_id.get("map_proof_latest", {})
    localize_values = key_values_by_id.get("localize_proof_latest", {})
    nav2_status_values = key_values_by_id.get("nav2_status", {})
    nav2_proof_values = key_values_by_id.get("nav2_proof_latest", {})

    map_observed_checks = [
        _safe_string_bool(status_values.get("map_once_observed"), "same_run_status_map_once_invalid", local_reasons),
        _safe_string_bool(map_values.get("map_once_observed"), "same_run_map_proof_map_once_invalid", local_reasons),
        _safe_string_bool(localize_values.get("map_once_observed"), "same_run_localize_map_once_invalid", local_reasons),
        _safe_string_bool(nav2_status_values.get("map_once_observed"), "same_run_nav2_status_map_once_invalid", local_reasons),
        _safe_string_bool(nav2_proof_values.get("map_once_observed"), "same_run_nav2_proof_map_once_invalid", local_reasons),
    ]
    amcl_observed_checks = [
        _safe_string_bool(status_values.get("amcl_pose_observed"), "same_run_status_amcl_pose_invalid", local_reasons),
        _safe_string_bool(localize_values.get("amcl_pose_observed"), "same_run_localize_amcl_pose_invalid", local_reasons),
        _safe_string_bool(nav2_proof_values.get("amcl_pose_observed"), "same_run_nav2_proof_amcl_pose_invalid", local_reasons),
    ]
    if not all(item is True for item in map_observed_checks):
        local_reasons.append("same_run_map_once_not_observed")
    if not all(item is True for item in amcl_observed_checks):
        local_reasons.append("same_run_amcl_pose_not_observed")

    tf_results = [
        _parse_localization_tf_observed(
            status_values.get("localization_tf_observed"),
            "same_run_status",
            local_reasons,
        ),
        _parse_localization_tf_observed(
            localize_values.get("localization_tf_observed"),
            "same_run_localize",
            local_reasons,
        ),
        _parse_localization_tf_observed(
            nav2_proof_values.get("localization_tf_observed"),
            "same_run_nav2_proof",
            local_reasons,
        ),
    ]
    same_run_tf_map_to_odom = all(result[0] is True for result in tf_results)
    same_run_tf_map_to_base_link = all(result[1] is True for result in tf_results)
    path_requested = _safe_string_bool(
        nav2_proof_values.get("path_generation_requested"),
        "same_run_path_generation_requested_invalid",
        local_reasons,
    )
    path_succeeded = _safe_string_bool(
        nav2_proof_values.get("path_generation_succeeded"),
        "same_run_path_generation_succeeded_invalid",
        local_reasons,
    )
    path_generated = _safe_string_bool(
        nav2_proof_values.get("path_generated"),
        "same_run_path_generated_invalid",
        local_reasons,
    )
    path_point_count = _safe_int(
        nav2_proof_values.get("path_point_count"),
        "same_run_path_point_count_invalid",
        local_reasons,
    )
    planner_server_active = _safe_string_bool(
        nav2_proof_values.get("planner_server_active"),
        "same_run_planner_server_active_invalid",
        local_reasons,
    )
    latest_path_generated = _safe_string_bool(
        nav2_status_values.get("latest_path_generated"),
        "same_run_nav2_status_latest_path_generated_invalid",
        local_reasons,
    )
    if path_requested is not True:
        local_reasons.append("same_run_path_generation_not_requested")
    if path_succeeded is not False:
        local_reasons.append("same_run_path_generation_succeeded_not_false")
    if path_generated is not False:
        local_reasons.append("same_run_path_generated_not_false")
    if path_point_count != 0:
        local_reasons.append("same_run_path_point_count_not_zero")
    if planner_server_active is not True:
        local_reasons.append("same_run_planner_server_not_active")
    if latest_path_generated is not False:
        local_reasons.append("same_run_nav2_status_latest_path_generated_not_false")

    present = (
        not local_reasons
        and all(item is True for item in map_observed_checks)
        and all(item is True for item in amcl_observed_checks)
        and same_run_tf_map_to_odom is True
        and same_run_tf_map_to_base_link is True
        and path_requested is True
        and path_succeeded is False
        and path_generated is False
        and path_point_count == 0
        and planner_server_active is True
        and latest_path_generated is False
    )
    if local_reasons:
        blocked_reasons.extend(local_reasons)
    summary = None
    if path_point_count is not None:
        summary = {
            "readback_ids": sorted(REQUIRED_LOCALIZATION_ENDPOINTS),
            "same_run_map_once_observed": all(item is True for item in map_observed_checks),
            "same_run_amcl_pose_observed": all(item is True for item in amcl_observed_checks),
            "same_run_localization_tf_map_to_odom": same_run_tf_map_to_odom,
            "same_run_localization_tf_map_to_base_link": same_run_tf_map_to_base_link,
            "same_run_path_generation_requested": bool(path_requested),
            "same_run_path_generation_succeeded": False,
            "same_run_path_generated": False,
            "same_run_path_point_count": path_point_count,
            "same_run_planner_server_active": bool(planner_server_active),
            "same_run_path_proven": False,
            "nav2_route_execution_success": False,
        }
    return present, summary


def _parse_cross_run_clean_baseline_path_comparator(
    latest: dict[str, Any] | None,
    retry_summary: dict[str, Any] | None,
    load_reasons: list[str] | None = None,
) -> tuple[bool, dict[str, Any] | None, list[str]]:
    """June 11 成功路径只能做 cross-run comparator，不能覆盖 same-run 结论。"""
    local_reasons: list[str] = list(load_reasons or [])
    if latest is None:
        local_reasons.append("cross_run_clean_baseline_latest_missing")
        return False, None, _dedupe(local_reasons)
    _append_dangerous_true(latest, "cross_run_clean_baseline_latest", local_reasons)
    if latest.get("schema") != EXPECTED_SCHEMAS["nav2_latest"]:
        local_reasons.append("cross_run_clean_baseline_latest_schema_mismatch")
    _safe_required_false(latest.get("safe_to_control"), "cross_run_clean_baseline_safe_to_control_not_false", local_reasons)
    _safe_required_false(latest.get("delivery_success"), "cross_run_clean_baseline_delivery_success_not_false", local_reasons)
    _safe_required_false(
        latest.get("primary_actions_enabled"),
        "cross_run_clean_baseline_primary_actions_enabled_not_false",
        local_reasons,
    )
    latest_result = latest.get("latest_result")
    if not isinstance(latest_result, dict):
        local_reasons.append("cross_run_clean_baseline_latest_result_missing")
        latest_result = {}
    _safe_required_false(
        latest_result.get("safe_to_control"),
        "cross_run_clean_baseline_latest_result_safe_to_control_not_false",
        local_reasons,
    )
    _safe_required_false(
        latest_result.get("delivery_success"),
        "cross_run_clean_baseline_latest_result_delivery_success_not_false",
        local_reasons,
    )
    _safe_required_false(
        latest_result.get("hil_pass"),
        "cross_run_clean_baseline_latest_result_hil_pass_not_false",
        local_reasons,
    )
    _safe_required_false(
        latest_result.get("robot_control_executed"),
        "cross_run_clean_baseline_latest_result_robot_control_executed_not_false",
        local_reasons,
    )
    if "primary_actions_enabled" in latest_result:
        latest_result_primary_actions_enabled = _safe_string_bool(
            latest_result.get("primary_actions_enabled"),
            "cross_run_clean_baseline_latest_result_primary_actions_enabled_invalid",
            local_reasons,
        )
        if latest_result_primary_actions_enabled is not False:
            local_reasons.append("cross_run_clean_baseline_latest_result_primary_actions_enabled_not_false")
    if latest_result.get("nav2_route_execution_success") is True:
        local_reasons.append("cross_run_clean_baseline_nav2_route_execution_success_true")
    proof = latest_result.get("proof")
    if not isinstance(proof, dict):
        local_reasons.append("cross_run_clean_baseline_proof_missing")
        proof = {}
    status = _safe_string(
        proof.get("status") or latest_result.get("status") or latest.get("status"),
        "cross_run_clean_baseline_status_invalid",
        local_reasons,
    )
    evidence_ref = _safe_string(
        proof.get("evidence_ref") or "not_loaded",
        "cross_run_clean_baseline_evidence_ref_invalid",
        local_reasons,
    )
    map_once_observed = _safe_bool(
        proof.get("map_once_observed"),
        "cross_run_clean_baseline_map_once_invalid",
        local_reasons,
    )
    amcl_pose_observed = _safe_bool(
        proof.get("amcl_pose_observed"),
        "cross_run_clean_baseline_amcl_pose_invalid",
        local_reasons,
    )
    tf_map_to_odom, tf_map_to_base_link, _ = _parse_localization_tf_observed(
        proof.get("localization_tf_observed"),
        "cross_run_clean_baseline",
        local_reasons,
    )
    path_requested = _safe_bool(
        proof.get("path_generation_requested"),
        "cross_run_clean_baseline_path_requested_invalid",
        local_reasons,
    )
    path_succeeded = _safe_bool(
        proof.get("path_generation_succeeded"),
        "cross_run_clean_baseline_path_succeeded_invalid",
        local_reasons,
    )
    path_generated = _safe_bool(
        proof.get("path_generated"),
        "cross_run_clean_baseline_path_generated_invalid",
        local_reasons,
    )
    path_point_count = _safe_int(
        proof.get("path_point_count"),
        "cross_run_clean_baseline_path_point_count_invalid",
        local_reasons,
    )
    if map_once_observed is not True:
        local_reasons.append("cross_run_clean_baseline_map_once_not_true")
    if amcl_pose_observed is not True:
        local_reasons.append("cross_run_clean_baseline_amcl_pose_not_true")
    if path_requested is not True:
        local_reasons.append("cross_run_clean_baseline_path_not_requested")
    if path_succeeded is not True:
        local_reasons.append("cross_run_clean_baseline_path_succeeded_not_true")
    if path_generated is not True:
        local_reasons.append("cross_run_clean_baseline_path_generated_not_true")
    if path_point_count != 31:
        local_reasons.append("cross_run_clean_baseline_path_point_count_not_31")

    if retry_summary is not None:
        if retry_summary.get("schema") != EXPECTED_SCHEMAS["nav2_retry_summary"]:
            local_reasons.append("cross_run_clean_baseline_retry_schema_mismatch")
        _safe_required_false(
            retry_summary.get("safe_to_control"),
            "cross_run_clean_baseline_retry_safe_to_control_not_false",
            local_reasons,
        )
        _safe_required_false(
            retry_summary.get("delivery_success"),
            "cross_run_clean_baseline_retry_delivery_success_not_false",
            local_reasons,
        )
        _safe_required_false(
            retry_summary.get("primary_actions_enabled"),
            "cross_run_clean_baseline_retry_primary_actions_enabled_not_false",
            local_reasons,
        )
        _safe_required_false(
            retry_summary.get("robot_control_executed"),
            "cross_run_clean_baseline_retry_robot_control_executed_not_false",
            local_reasons,
        )
        retry_path_succeeded = _safe_bool(
            retry_summary.get("path_generation_succeeded"),
            "cross_run_clean_baseline_retry_path_succeeded_invalid",
            local_reasons,
        )
        retry_path_generated = _safe_bool(
            retry_summary.get("path_generated"),
            "cross_run_clean_baseline_retry_path_generated_invalid",
            local_reasons,
        )
        retry_path_point_count = _safe_int(
            retry_summary.get("path_point_count"),
            "cross_run_clean_baseline_retry_path_point_count_invalid",
            local_reasons,
        )
        if retry_path_succeeded is not True:
            local_reasons.append("cross_run_clean_baseline_retry_path_succeeded_not_true")
        if retry_path_generated is not True:
            local_reasons.append("cross_run_clean_baseline_retry_path_generated_not_true")
        if retry_path_point_count != 31:
            local_reasons.append("cross_run_clean_baseline_retry_path_point_count_not_31")

    present = not local_reasons
    summary = None
    if path_point_count is not None:
        summary = {
            "source_schema": EXPECTED_SCHEMAS["nav2_latest"],
            "status": status,
            "evidence_ref": evidence_ref,
            "path_generation_requested": bool(path_requested),
            "path_generation_succeeded": bool(path_succeeded),
            "path_generated": bool(path_generated),
            "path_point_count": path_point_count,
            "map_once_observed": bool(map_once_observed),
            "amcl_pose_observed": bool(amcl_pose_observed),
            "localization_tf_map_to_odom": tf_map_to_odom,
            "localization_tf_map_to_base_link": tf_map_to_base_link,
            "safety_fields_fixed_false": True,
            "same_run_override_allowed": False,
        }
    return present, summary, _dedupe(local_reasons)


def _text_material_is_safe(text: Any, reason: str, blocked_reasons: list[str]) -> bool:
    """文本 artifact 只作为存在性/readback 判断来源，仍要先过泄露防线。"""
    if not isinstance(text, str) or not text.strip():
        blocked_reasons.append(reason)
        return False
    if UNSAFE_VALUE_PATTERN.search(text):
        blocked_reasons.append(reason)
        return False
    return True


def _first_yaml_scalar(text: str, key: str) -> str | None:
    """用最小正则读取 ROS 文本 dump 的简单 scalar，避免引入 YAML 依赖。"""
    match = re.search(rf"(?m)^\s*{re.escape(key)}:\s*(.*?)\s*$", text)
    if match is None:
        return None
    value = match.group(1).strip().strip("'\"")
    return value


def _first_float_after(text: str, label: str) -> float | None:
    """从 ROS 文本 sample 中提取一个数值，只用于判定 sample 存在。"""
    match = re.search(rf"(?m)^\s*{re.escape(label)}:\s*([-+]?\d+(?:\.\d+)?)\s*$", text)
    if match is None:
        return None
    value = float(match.group(1))
    if not math.isfinite(value):
        return None
    return value


def _parse_bounded_motion_feedback_summary(
    feedback_summary: dict[str, Any] | None,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """消费 2026-06-10 bounded motion 摘要，但不把它升级成 HIL pass。"""
    if feedback_summary is None:
        blocked_reasons.append("bounded_motion_feedback_summary_missing")
        return False, None
    _append_dangerous_true(feedback_summary, "bounded_motion_feedback_summary", blocked_reasons)
    if feedback_summary.get("schema") != EXPECTED_SCHEMAS["bounded_motion_feedback"]:
        blocked_reasons.append("bounded_motion_feedback_summary_schema_mismatch")
        return False, None
    motion_command = feedback_summary.get("motion_command")
    observed = feedback_summary.get("observed")
    lr_window = feedback_summary.get("t1001_lr_motion_window")
    if not isinstance(motion_command, dict):
        blocked_reasons.append("bounded_motion_command_missing")
        motion_command = {}
    if not isinstance(observed, dict):
        blocked_reasons.append("bounded_motion_observed_missing")
        observed = {}
    if not isinstance(lr_window, dict):
        blocked_reasons.append("bounded_motion_lr_window_missing")
        lr_window = {}

    linear_x = _safe_float(
        motion_command.get("linear_x_mps"),
        "bounded_motion_linear_x_invalid",
        blocked_reasons,
    )
    target_duration = _safe_float(
        motion_command.get("nonzero_duration_target_s"),
        "bounded_motion_target_duration_invalid",
        blocked_reasons,
    )
    zero_command_sent = _safe_bool(
        motion_command.get("zero_command_sent"),
        "bounded_motion_zero_command_invalid",
        blocked_reasons,
    )
    trashbot_stop_called = _safe_bool(
        motion_command.get("trashbot_stop_called"),
        "bounded_motion_stop_call_invalid",
        blocked_reasons,
    )
    subscription_count = _safe_int(
        observed.get("subscription_count_before_pulse"),
        "bounded_motion_subscription_count_invalid",
        blocked_reasons,
    )
    duration = _safe_float(
        observed.get("nonzero_duration_s"),
        "bounded_motion_duration_invalid",
        blocked_reasons,
    )
    duration_lte = _safe_bool(
        observed.get("nonzero_duration_lte_0_3s"),
        "bounded_motion_duration_lte_invalid",
        blocked_reasons,
    )
    stop_success = _safe_bool(
        observed.get("stop_service_success_text"),
        "bounded_motion_stop_success_invalid",
        blocked_reasons,
    )
    battery_topic_present = _safe_bool(
        observed.get("battery_topic_sample_present"),
        "bounded_motion_battery_topic_invalid",
        blocked_reasons,
    )
    imu_topic_present = _safe_bool(
        observed.get("imu_topic_sample_present"),
        "bounded_motion_imu_topic_invalid",
        blocked_reasons,
    )
    status_before = observed.get("status_before.json")
    status_after = observed.get("status_after.json")
    if not isinstance(status_before, dict):
        blocked_reasons.append("bounded_motion_status_before_missing")
        status_before = {}
    if not isinstance(status_after, dict):
        blocked_reasons.append("bounded_motion_status_after_missing")
        status_after = {}
    before_t1001 = _safe_bool(
        status_before.get("feedback_ack_t1001_observed"),
        "bounded_motion_status_before_t1001_invalid",
        blocked_reasons,
    )
    after_t1001 = _safe_bool(
        status_after.get("feedback_ack_t1001_observed"),
        "bounded_motion_status_after_t1001_invalid",
        blocked_reasons,
    )
    left_nonzero = _safe_bool(
        lr_window.get("left_nonzero_proven"),
        "bounded_motion_left_nonzero_invalid",
        blocked_reasons,
    )
    right_nonzero = _safe_bool(
        lr_window.get("right_nonzero_proven"),
        "bounded_motion_right_nonzero_invalid",
        blocked_reasons,
    )
    raw_t1001_lines_available = _safe_bool(
        lr_window.get("raw_t1001_lines_available"),
        "bounded_motion_raw_t1001_lines_invalid",
        blocked_reasons,
    )
    if linear_x != 0.03:
        blocked_reasons.append("bounded_motion_linear_x_not_0_03")
    if target_duration != 0.25:
        blocked_reasons.append("bounded_motion_target_duration_not_0_25")
    if zero_command_sent is not True:
        blocked_reasons.append("bounded_motion_zero_command_not_sent")
    if trashbot_stop_called is not True or stop_success is not True:
        blocked_reasons.append("bounded_motion_stop_not_observed")
    if subscription_count != 1:
        blocked_reasons.append("bounded_motion_subscription_count_not_one")
    if duration is None or duration <= 0:
        blocked_reasons.append("bounded_motion_duration_nonpositive")
    if duration is not None and duration > 0.3:
        blocked_reasons.append("bounded_motion_duration_over_0_3s")
    if duration_lte is not True:
        blocked_reasons.append("bounded_motion_duration_lte_not_true")
    if battery_topic_present is not True:
        blocked_reasons.append("bounded_motion_battery_topic_missing")
    if imu_topic_present is not True:
        blocked_reasons.append("bounded_motion_imu_topic_missing")
    if before_t1001 is not True or after_t1001 is not True:
        blocked_reasons.append("bounded_motion_t1001_before_after_missing")
    if left_nonzero is not False or right_nonzero is not False:
        blocked_reasons.append("bounded_motion_lr_nonzero_unexpected_true")
    if raw_t1001_lines_available is not False:
        blocked_reasons.append("bounded_motion_raw_t1001_lines_unexpected")

    present = (
        linear_x == 0.03
        and target_duration == 0.25
        and zero_command_sent is True
        and trashbot_stop_called is True
        and subscription_count == 1
        and duration is not None
        and 0 < duration <= 0.3
        and duration_lte is True
        and stop_success is True
        and battery_topic_present is True
        and imu_topic_present is True
        and before_t1001 is True
        and after_t1001 is True
        and left_nonzero is False
        and right_nonzero is False
        and raw_t1001_lines_available is False
    )
    summary = {
        "source_schema": EXPECTED_SCHEMAS["bounded_motion_feedback"],
        "linear_x_mps": linear_x,
        "nonzero_duration_target_s": target_duration,
        "nonzero_duration_s": duration,
        "nonzero_duration_lte_0_3s": duration_lte is True,
        "zero_command_sent": zero_command_sent is True,
        "trashbot_stop_called": trashbot_stop_called is True,
        "stop_service_success_text": stop_success is True,
        "subscription_count_before_pulse": subscription_count,
        "battery_topic_sample_present": battery_topic_present is True,
        "imu_topic_sample_present": imu_topic_present is True,
        "t1001_feedback_before_after_observed": before_t1001 is True and after_t1001 is True,
        "bounded_motion_lr_nonzero_proven": False,
        "wheel_direction_proven": False,
        "imu_battery_calibration_proven": False,
    }
    return present, summary


def _parse_bounded_motion_ros_readbacks(
    pulse_log_text: str | None,
    odom_text: str | None,
    imu_text: str | None,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """消费 topic/sample 文本，只确认 readback 存在，不确认动态里程计或标定。"""
    if not (
        _text_material_is_safe(pulse_log_text, "bounded_motion_pulse_log_invalid", blocked_reasons)
        and _text_material_is_safe(odom_text, "bounded_motion_odom_text_invalid", blocked_reasons)
        and _text_material_is_safe(imu_text, "bounded_motion_imu_text_invalid", blocked_reasons)
    ):
        return False, None
    assert isinstance(pulse_log_text, str)
    assert isinstance(odom_text, str)
    assert isinstance(imu_text, str)

    node_present = "node_list_before_pulse:" in pulse_log_text and "/esp32_bridge" in pulse_log_text
    topic_battery_present = "/battery" in pulse_log_text
    topic_imu_present = "/imu/data" in pulse_log_text
    topic_odom_present = "/odom" in pulse_log_text
    bounded_pulse_present = "rclpy_pulse_with_discovery_wait:" in pulse_log_text
    stop_success = "stop_success=True" in pulse_log_text
    battery_section_present = "battery_once_after_motion:" in pulse_log_text and "present: true" in pulse_log_text
    pulse_odom_section_present = "odom_after_motion:" in pulse_log_text
    pulse_imu_section_present = "imu_once_after_motion:" in pulse_log_text
    if not node_present:
        blocked_reasons.append("bounded_motion_bridge_node_missing")
    if not (topic_battery_present and topic_imu_present and topic_odom_present):
        blocked_reasons.append("bounded_motion_required_topics_missing")
    if not bounded_pulse_present:
        blocked_reasons.append("bounded_motion_pulse_section_missing")
    if not stop_success:
        blocked_reasons.append("bounded_motion_pulse_stop_success_missing")
    if not battery_section_present:
        blocked_reasons.append("bounded_motion_battery_sample_missing")
    if not pulse_odom_section_present:
        blocked_reasons.append("bounded_motion_pulse_odom_section_missing")
    if not pulse_imu_section_present:
        blocked_reasons.append("bounded_motion_pulse_imu_section_missing")

    odom_frame_id = _first_yaml_scalar(odom_text, "frame_id")
    odom_child_frame_id = _first_yaml_scalar(odom_text, "child_frame_id")
    odom_x = _first_float_after(odom_text, "x")
    imu_frame_id = _first_yaml_scalar(imu_text, "frame_id")
    imu_orientation_present = "orientation:" in imu_text and _first_float_after(imu_text, "w") is not None
    imu_velocity_present = "angular_velocity:" in imu_text
    imu_acceleration_present = "linear_acceleration:" in imu_text
    odom_frame_id = _safe_string(
        odom_frame_id,
        "bounded_motion_odom_frame_id_invalid",
        blocked_reasons,
    )
    odom_child_frame_id = _safe_string(
        odom_child_frame_id,
        "bounded_motion_odom_child_frame_id_invalid",
        blocked_reasons,
    )
    imu_frame_id = _safe_string(
        imu_frame_id,
        "bounded_motion_imu_frame_id_invalid",
        blocked_reasons,
    )
    if odom_frame_id != "odom":
        blocked_reasons.append("bounded_motion_odom_frame_id_not_odom")
    if odom_child_frame_id != "base_link":
        blocked_reasons.append("bounded_motion_odom_child_frame_id_not_base_link")
    if odom_x is None:
        blocked_reasons.append("bounded_motion_odom_pose_sample_missing")
    if imu_frame_id != "imu_link":
        blocked_reasons.append("bounded_motion_imu_frame_id_not_imu_link")
    if not (imu_orientation_present and imu_velocity_present and imu_acceleration_present):
        blocked_reasons.append("bounded_motion_imu_sample_incomplete")

    present = (
        node_present
        and topic_battery_present
        and topic_imu_present
        and topic_odom_present
        and bounded_pulse_present
        and stop_success
        and battery_section_present
        and pulse_odom_section_present
        and pulse_imu_section_present
        and odom_frame_id == "odom"
        and odom_child_frame_id == "base_link"
        and odom_x is not None
        and imu_frame_id == "imu_link"
        and imu_orientation_present
        and imu_velocity_present
        and imu_acceleration_present
    )
    summary = {
        "bridge_node_observed": node_present,
        "required_topic_samples_present": (
            topic_battery_present and topic_imu_present and topic_odom_present
        ),
        "bounded_pulse_observed": bounded_pulse_present,
        "stop_success_observed": stop_success,
        "battery_sample_present": battery_section_present,
        "odom_readback_sample_present": odom_frame_id == "odom" and odom_child_frame_id == "base_link" and odom_x is not None,
        "odom_readback_frame_id": odom_frame_id,
        "odom_readback_child_frame_id": odom_child_frame_id,
        "imu_sample_present": (
            imu_frame_id == "imu_link" and imu_orientation_present and imu_velocity_present and imu_acceleration_present
        ),
        "imu_frame_id": imu_frame_id,
        "imu_battery_calibration_proven": False,
    }
    return present, summary


def _parse_pc_real_robot_api_readback_summary(
    readback_summary: dict[str, Any] | None,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """消费 PC readback summary，只提取 base/T1001 fail-closed 状态。"""
    if readback_summary is None:
        blocked_reasons.append("pc_real_robot_api_readback_summary_missing")
        return False, None
    _append_dangerous_true(readback_summary, "pc_real_robot_api_readback", blocked_reasons)
    if readback_summary.get("schema") != EXPECTED_SCHEMAS["pc_real_robot_readback"]:
        blocked_reasons.append("pc_real_robot_api_readback_schema_mismatch")
        return False, None
    proof_boundary = readback_summary.get("proof_boundary")
    base = readback_summary.get("base")
    if not isinstance(proof_boundary, dict):
        blocked_reasons.append("pc_real_robot_api_readback_proof_boundary_missing")
        proof_boundary = {}
    if not isinstance(base, dict):
        blocked_reasons.append("pc_real_robot_api_readback_base_missing")
        base = {}
    for field in ("safe_to_control", "delivery_success", "primary_actions_enabled"):
        _safe_required_false(
            proof_boundary.get(field),
            f"pc_real_robot_api_readback_{field}_not_false",
            blocked_reasons,
        )
    source = _safe_string(
        proof_boundary.get("source"),
        "pc_real_robot_api_readback_source_invalid",
        blocked_reasons,
    )
    direct_status = _safe_string(
        base.get("direct_status"),
        "pc_real_robot_api_readback_direct_status_invalid",
        blocked_reasons,
    )
    workstation_status = _safe_string(
        base.get("workstation_status"),
        "pc_real_robot_api_readback_workstation_status_invalid",
        blocked_reasons,
    )
    t1001_observed = _safe_bool(
        base.get("t1001_observed"),
        "pc_real_robot_api_readback_t1001_invalid",
        blocked_reasons,
    )
    workstation_blockers = base.get("workstation_blockers")
    if isinstance(workstation_blockers, list):
        workstation_blocker_count = len(workstation_blockers)
    else:
        blocked_reasons.append("pc_real_robot_api_readback_workstation_blockers_invalid")
        workstation_blocker_count = None
    if source != "software_proof":
        blocked_reasons.append("pc_real_robot_api_readback_source_not_software_proof")
    if direct_status != "loaded":
        blocked_reasons.append("pc_real_robot_api_readback_direct_status_not_loaded")
    if workstation_status != "blocked":
        blocked_reasons.append("pc_real_robot_api_readback_workstation_status_not_blocked")
    if t1001_observed is not True:
        blocked_reasons.append("pc_real_robot_api_readback_t1001_not_observed")
    present = (
        source == "software_proof"
        and direct_status == "loaded"
        and workstation_status == "blocked"
        and t1001_observed is True
        and workstation_blocker_count is not None
    )
    summary = {
        "source_schema": EXPECTED_SCHEMAS["pc_real_robot_readback"],
        "source": source,
        "base_direct_status": direct_status,
        "base_t1001_observed": t1001_observed is True,
        "workstation_status": workstation_status,
        "workstation_blocker_count": workstation_blocker_count,
    }
    return present, summary


def _parse_base_feedback_samples_latest(
    base_feedback: dict[str, Any] | None,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """消费 T=130 feedback request 结果，明确它不是 motion command。"""
    if base_feedback is None:
        blocked_reasons.append("base_feedback_samples_latest_missing")
        return False, None
    _append_dangerous_true(base_feedback, "base_feedback_samples_latest", blocked_reasons)
    if base_feedback.get("schema") != EXPECTED_SCHEMAS["base_feedback_samples_latest"]:
        blocked_reasons.append("base_feedback_samples_latest_schema_mismatch")
        return False, None
    for field in (
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "robot_control_executed",
        "hil_pass",
        "readback_sends_commands",
        "sends_motion_commands",
    ):
        _safe_required_false(
            base_feedback.get(field),
            f"base_feedback_samples_latest_{field}_not_false",
            blocked_reasons,
        )
    latest_result = base_feedback.get("latest_result")
    if not isinstance(latest_result, dict):
        blocked_reasons.append("base_feedback_samples_latest_result_missing")
        latest_result = {}
    _append_dangerous_true(latest_result, "base_feedback_latest_result", blocked_reasons)
    if latest_result.get("schema") != EXPECTED_SCHEMAS["base_feedback_samples_result"]:
        blocked_reasons.append("base_feedback_latest_result_schema_mismatch")
    requested_count = _safe_int(
        latest_result.get("requested_sample_count"),
        "base_feedback_requested_sample_count_invalid",
        blocked_reasons,
    )
    completed_count = _safe_int(
        latest_result.get("completed_sample_count"),
        "base_feedback_completed_sample_count_invalid",
        blocked_reasons,
    )
    t1001_count = _safe_int(
        latest_result.get("t1001_observed_count"),
        "base_feedback_t1001_count_invalid",
        blocked_reasons,
    )
    all_samples_observed = _safe_bool(
        latest_result.get("all_samples_observed_t1001"),
        "base_feedback_all_samples_observed_invalid",
        blocked_reasons,
    )
    observed_types = _parse_feedback_type_list(
        latest_result.get("observed_feedback_types"),
        "base_feedback_observed_types_invalid",
        blocked_reasons,
    )
    latest_sends_commands = _safe_bool(
        latest_result.get("sends_commands"),
        "base_feedback_request_context_invalid",
        blocked_reasons,
    )
    latest_sends_motion_commands = _safe_bool(
        latest_result.get("sends_motion_commands"),
        "base_feedback_sends_motion_commands_invalid",
        blocked_reasons,
    )
    for field in ("safe_to_control", "delivery_success", "primary_actions_enabled", "robot_control_executed", "hil_pass"):
        _safe_required_false(
            latest_result.get(field),
            f"base_feedback_latest_result_{field}_not_false",
            blocked_reasons,
        )
    request = latest_result.get("request")
    if not isinstance(request, dict):
        blocked_reasons.append("base_feedback_request_missing")
        request = {}
    request_command = request.get("command")
    if not isinstance(request_command, dict):
        blocked_reasons.append("base_feedback_request_command_missing")
        request_command = {}
    request_command_type = _safe_int(
        request_command.get("T"),
        "base_feedback_request_command_type_invalid",
        blocked_reasons,
    )
    if request_command_type != 130:
        blocked_reasons.append("base_feedback_request_not_T130")
    if latest_sends_commands is not True:
        blocked_reasons.append("base_feedback_request_context_not_observed")
    if latest_sends_motion_commands is not False:
        blocked_reasons.append("base_feedback_sends_motion_commands_not_false")
    if requested_count != 2 or completed_count != 2 or t1001_count != 2:
        blocked_reasons.append("base_feedback_t1001_sample_count_not_two")
    if all_samples_observed is not True:
        blocked_reasons.append("base_feedback_samples_not_all_t1001")
    if observed_types != [1001]:
        blocked_reasons.append("base_feedback_observed_types_not_t1001_only")
    samples = latest_result.get("samples")
    samples_present = isinstance(samples, list) and len(samples) == 2
    if not samples_present:
        blocked_reasons.append("base_feedback_samples_list_not_two")
        samples = []
    for index, sample in enumerate(samples if isinstance(samples, list) else []):
        if not isinstance(sample, dict):
            blocked_reasons.append(f"base_feedback_sample_{index}_invalid")
            continue
        _append_dangerous_true(sample, f"base_feedback_sample_{index}", blocked_reasons)
        if sample.get("schema") != EXPECTED_SCHEMAS["base_feedback_request_result"]:
            blocked_reasons.append(f"base_feedback_sample_{index}_schema_mismatch")
        if _safe_string(sample.get("t1001_feedback_status"), f"base_feedback_sample_{index}_status_invalid", blocked_reasons) != "observed":
            blocked_reasons.append(f"base_feedback_sample_{index}_t1001_not_observed")
        if _parse_feedback_type_list(
            sample.get("observed_feedback_types"),
            f"base_feedback_sample_{index}_observed_types_invalid",
            blocked_reasons,
        ) != [1001]:
            blocked_reasons.append(f"base_feedback_sample_{index}_observed_types_not_t1001_only")
        for field in ("safe_to_control", "delivery_success", "robot_control_executed", "hil_pass", "sends_motion_commands"):
            _safe_required_false(
                sample.get(field),
                f"base_feedback_sample_{index}_{field}_not_false",
                blocked_reasons,
            )
    present = (
        requested_count == 2
        and completed_count == 2
        and t1001_count == 2
        and all_samples_observed is True
        and observed_types == [1001]
        and latest_sends_commands is True
        and latest_sends_motion_commands is False
        and request_command_type == 130
        and samples_present
    )
    summary = {
        "source_schema": EXPECTED_SCHEMAS["base_feedback_samples_latest"],
        "latest_result_schema": latest_result.get("schema"),
        "requested_sample_count": requested_count,
        "completed_sample_count": completed_count,
        "t1001_observed_count": t1001_count,
        "observed_feedback_types": observed_types,
        "all_samples_observed_t1001": all_samples_observed is True,
        "feedback_request_observed": latest_sends_commands is True and request_command_type == 130,
        "feedback_request_t130_observed": request_command_type == 130,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "safe_to_control": False,
        "delivery_success": False,
        "hil_pass": False,
    }
    return present, summary


def _parse_wheel_feedback_diagnostic_sweep(
    diagnostic_summary: dict[str, Any] | None,
    blocked_reasons: list[str],
    load_reasons: list[str] | None = None,
) -> tuple[bool, dict[str, Any] | None]:
    """可选 sweep 只能作为 diagnostic context；非零 L/R 会阻塞本 bundle。"""
    if diagnostic_summary is None:
        return False, None
    _append_dangerous_true(diagnostic_summary, "wheel_feedback_diagnostic", blocked_reasons)
    if diagnostic_summary.get("schema") != EXPECTED_SCHEMAS["wheel_feedback_diagnostic_sweep"]:
        blocked_reasons.append("wheel_feedback_diagnostic_schema_mismatch")
        return False, None
    segments = diagnostic_summary.get("segments")
    if not isinstance(segments, list) or not segments:
        blocked_reasons.append("wheel_feedback_diagnostic_segments_missing")
        return False, None
    total_record_count = 0
    all_nonzero_zero = True
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            blocked_reasons.append(f"wheel_feedback_diagnostic_segment_{index}_invalid")
            all_nonzero_zero = False
            continue
        nonzero_count = _safe_int(
            segment.get("nonzero_lr_count"),
            f"wheel_feedback_diagnostic_segment_{index}_nonzero_count_invalid",
            blocked_reasons,
        )
        record_count = _safe_int(
            segment.get("record_count"),
            f"wheel_feedback_diagnostic_segment_{index}_record_count_invalid",
            blocked_reasons,
        )
        stop_success = _safe_bool(
            segment.get("stop_success"),
            f"wheel_feedback_diagnostic_segment_{index}_stop_success_invalid",
            blocked_reasons,
        )
        if record_count is not None:
            total_record_count += record_count
        if nonzero_count != 0:
            blocked_reasons.append("wheel_feedback_diagnostic_nonzero_lr_unexpected")
            all_nonzero_zero = False
        if stop_success is not True:
            blocked_reasons.append(f"wheel_feedback_diagnostic_segment_{index}_stop_not_success")
    if load_reasons:
        # missing/disabled diagnostic 不阻塞；可读 diagnostic 内部篡改才阻塞。
        for reason in load_reasons:
            if "unreadable_or_invalid" in reason:
                blocked_reasons.append(reason)
    present = all_nonzero_zero and not any(reason == "wheel_feedback_diagnostic_nonzero_lr_unexpected" for reason in blocked_reasons)
    summary = {
        "source_schema": EXPECTED_SCHEMAS["wheel_feedback_diagnostic_sweep"],
        "segment_count": len(segments),
        "total_record_count": total_record_count,
        "all_nonzero_lr_count_zero": all_nonzero_zero,
        "bounded_motion_lr_nonzero_proven": False,
        "wheel_direction_proven": False,
    }
    return present, summary


def _parse_same_session_wheel_feedback_material(
    same_session_artifact: dict[str, Any] | None,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """消费同会话轮速材料，只输出 prefix 化摘要和 HIL acceptance 缺口。"""
    if same_session_artifact is None:
        blocked_reasons.append("same_session_wheel_feedback_artifact_missing")
        return False, None
    if same_session_artifact.get("schema") != EXPECTED_SCHEMAS["same_session_manual_result"]:
        blocked_reasons.append("same_session_wheel_feedback_schema_mismatch")
        return False, None

    # 顶层 robot_control_executed=true 是历史人工点动事实，不能拿来抬升本 bundle 的控制许可。
    _append_optional_false_fields(
        same_session_artifact,
        "same_session_wheel_feedback_top_level",
        (
            "hil_pass",
            "safe_to_control",
            "delivery_success",
            "primary_actions_enabled",
            "nav2_route_execution_success",
        ),
        blocked_reasons,
    )
    accepted = _safe_bool(
        same_session_artifact.get("accepted"),
        "same_session_wheel_feedback_accepted_invalid",
        blocked_reasons,
    )
    manual_executed = _safe_bool(
        same_session_artifact.get("manual_command_executed"),
        "same_session_wheel_feedback_manual_executed_invalid",
        blocked_reasons,
    )
    auto_stop_executed = _safe_bool(
        same_session_artifact.get("auto_stop_executed"),
        "same_session_wheel_feedback_auto_stop_invalid",
        blocked_reasons,
    )
    feedback_attempted = _safe_bool(
        same_session_artifact.get("feedback_during_motion_attempted"),
        "same_session_wheel_feedback_attempted_invalid",
        blocked_reasons,
    )
    if accepted is not True:
        blocked_reasons.append("same_session_wheel_feedback_not_accepted")
    if manual_executed is not True:
        blocked_reasons.append("same_session_wheel_feedback_manual_not_executed")
    if auto_stop_executed is not True:
        blocked_reasons.append("same_session_wheel_feedback_auto_stop_not_executed")
    if feedback_attempted is not True:
        blocked_reasons.append("same_session_wheel_feedback_attempt_not_true")

    feedback = same_session_artifact.get("feedback_during_motion")
    if not isinstance(feedback, dict):
        blocked_reasons.append("same_session_wheel_feedback_motion_section_missing")
        return False, None
    if feedback.get("schema") != EXPECTED_SCHEMAS["base_feedback_request_result"]:
        blocked_reasons.append("same_session_wheel_feedback_motion_schema_mismatch")
    _append_optional_false_fields(
        feedback,
        "same_session_wheel_feedback_motion",
        (
            "hil_pass",
            "safe_to_control",
            "delivery_success",
            "primary_actions_enabled",
            "robot_control_executed",
            "sends_motion_commands",
            "nav2_route_execution_success",
        ),
        blocked_reasons,
    )

    request = feedback.get("request")
    request_command = request.get("command") if isinstance(request, dict) else None
    if not isinstance(request_command, dict):
        blocked_reasons.append("same_session_wheel_feedback_request_command_missing")
        request_command = {}
    request_t = _safe_int(
        request_command.get("T"),
        "same_session_wheel_feedback_request_t_invalid",
        blocked_reasons,
    )
    if request_t != 130:
        blocked_reasons.append("same_session_wheel_feedback_request_not_t130")

    t1001_status = _safe_string(
        feedback.get("t1001_feedback_status"),
        "same_session_wheel_feedback_t1001_status_invalid",
        blocked_reasons,
    )
    observed_types = _parse_feedback_type_list(
        feedback.get("observed_feedback_types"),
        "same_session_wheel_feedback_observed_types_invalid",
        blocked_reasons,
    )
    if t1001_status != "observed":
        blocked_reasons.append("same_session_wheel_feedback_t1001_not_observed")
    if 1001 not in observed_types:
        blocked_reasons.append("same_session_wheel_feedback_observed_types_missing_t1001")

    wheel_summary = feedback.get("wheel_feedback_summary")
    if not isinstance(wheel_summary, dict):
        blocked_reasons.append("same_session_wheel_feedback_summary_missing")
        return False, None
    source = _safe_string(
        wheel_summary.get("source"),
        "same_session_wheel_feedback_source_invalid",
        blocked_reasons,
    )
    if source != "vendor_t1001_L_R":
        blocked_reasons.append("same_session_wheel_feedback_source_mismatch")
    frame_count = _safe_int(
        wheel_summary.get("frame_count"),
        "same_session_wheel_feedback_frame_count_invalid",
        blocked_reasons,
    )
    matched_frame_count = _safe_int(
        wheel_summary.get("matched_frame_count"),
        "same_session_wheel_feedback_matched_count_invalid",
        blocked_reasons,
    )
    nonzero_frame_count = _safe_int(
        wheel_summary.get("nonzero_frame_count"),
        "same_session_wheel_feedback_nonzero_count_invalid",
        blocked_reasons,
    )
    lr_nonzero_observed = _safe_bool(
        wheel_summary.get("lr_nonzero_observed"),
        "same_session_wheel_feedback_lr_nonzero_invalid",
        blocked_reasons,
    )
    if frame_count is None or frame_count <= 0:
        blocked_reasons.append("same_session_wheel_feedback_frame_count_missing")
    if matched_frame_count is None or matched_frame_count <= 0:
        blocked_reasons.append("same_session_wheel_feedback_matched_count_missing")
    if nonzero_frame_count is None or nonzero_frame_count <= 0:
        blocked_reasons.append("same_session_wheel_feedback_nonzero_count_missing")
    if lr_nonzero_observed is not True:
        blocked_reasons.append("same_session_wheel_feedback_lr_nonzero_not_true")

    latest_pair = wheel_summary.get("latest_nonzero_pair")
    if not isinstance(latest_pair, dict):
        blocked_reasons.append("same_session_wheel_feedback_latest_pair_missing")
        latest_pair = {}
    pair_source = _safe_string(
        latest_pair.get("source"),
        "same_session_wheel_feedback_latest_pair_source_invalid",
        blocked_reasons,
    )
    left_speed = _safe_float(
        latest_pair.get("left_speed"),
        "same_session_wheel_feedback_latest_pair_left_invalid",
        blocked_reasons,
    )
    right_speed = _safe_float(
        latest_pair.get("right_speed"),
        "same_session_wheel_feedback_latest_pair_right_invalid",
        blocked_reasons,
    )
    if pair_source != "vendor_t1001_L_R":
        blocked_reasons.append("same_session_wheel_feedback_latest_pair_source_mismatch")
    if left_speed is None or left_speed == 0.0:
        blocked_reasons.append("same_session_wheel_feedback_latest_pair_left_zero_or_missing")
    if right_speed is None or right_speed == 0.0:
        blocked_reasons.append("same_session_wheel_feedback_latest_pair_right_zero_or_missing")

    present = (
        accepted is True
        and manual_executed is True
        and auto_stop_executed is True
        and feedback_attempted is True
        and request_t == 130
        and t1001_status == "observed"
        and 1001 in observed_types
        and source == "vendor_t1001_L_R"
        and frame_count is not None
        and frame_count > 0
        and matched_frame_count is not None
        and matched_frame_count > 0
        and nonzero_frame_count is not None
        and nonzero_frame_count > 0
        and lr_nonzero_observed is True
        and pair_source == "vendor_t1001_L_R"
        and left_speed is not None
        and left_speed != 0.0
        and right_speed is not None
        and right_speed != 0.0
    )
    pair_summary = None
    if left_speed is not None and right_speed is not None:
        pair_summary = {
            "phase": "motion_window",
            "left_speed": left_speed,
            "right_speed": right_speed,
            "sign_pattern": _wheel_sign_pattern(left_speed, right_speed),
        }
    summary = {
        "source_schema": EXPECTED_SCHEMAS["same_session_manual_result"],
        "feedback_source_schema": EXPECTED_SCHEMAS["base_feedback_request_result"],
        "historical_same_session_material": True,
        "current_live_rerun": False,
        "accepted": accepted is True,
        "manual_command_executed": manual_executed is True,
        "auto_stop_executed": auto_stop_executed is True,
        "feedback_during_motion_attempted": feedback_attempted is True,
        "feedback_request_t130_observed": request_t == 130,
        "t1001_feedback_status": t1001_status,
        "observed_feedback_types": observed_types,
        "frame_count": frame_count,
        "matched_frame_count": matched_frame_count,
        "nonzero_frame_count": nonzero_frame_count,
        "lr_nonzero_observed": lr_nonzero_observed is True,
        "latest_nonzero_pair": pair_summary,
        "material_ready_not_hil_pass": present,
        "hil_acceptance_status": SAME_SESSION_HIL_ACCEPTANCE_STATUS,
        "hil_acceptance_missing_fields": list(SAME_SESSION_HIL_ACCEPTANCE_MISSING_FIELDS),
    }
    return present, summary


def _parse_same_session_pc_command_material(
    pc_first_jog_artifact: dict[str, Any] | None,
    after_jog_base_status: dict[str, Any] | None,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """消费同会话 PC first-jog 与 after-jog base status，只输出 prefix 化 material 摘要。"""
    if pc_first_jog_artifact is None:
        blocked_reasons.append("same_session_pc_command_artifact_missing")
        return False, None
    if after_jog_base_status is None:
        blocked_reasons.append("same_session_pc_command_after_jog_base_status_missing")
        return False, None
    if pc_first_jog_artifact.get("schema") != EXPECTED_SCHEMAS["robot_control_base_command_proxy"]:
        blocked_reasons.append("same_session_pc_command_schema_mismatch")
        return False, None
    if after_jog_base_status.get("schema") != EXPECTED_SCHEMAS["base_status"]:
        blocked_reasons.append("same_session_pc_command_after_jog_schema_mismatch")
        return False, None

    _append_optional_false_fields(
        pc_first_jog_artifact,
        "same_session_pc_command_top_level",
        (
            "safe_to_control",
            "delivery_success",
            "primary_actions_enabled",
            "robot_control_executed",
            "hil_pass",
            "nav2_route_execution_success",
        ),
        blocked_reasons,
    )
    _append_optional_false_fields(
        after_jog_base_status,
        "same_session_pc_command_after_jog_top_level",
        (
            "safe_to_control",
            "delivery_success",
            "primary_actions_enabled",
            "robot_control_executed",
            "hil_pass",
            "sends_motion_commands",
        ),
        blocked_reasons,
    )

    requested_direction = _safe_string(
        pc_first_jog_artifact.get("requested_direction"),
        "same_session_pc_command_requested_direction_invalid",
        blocked_reasons,
    )
    applied_direction = _safe_string(
        pc_first_jog_artifact.get("applied_direction"),
        "same_session_pc_command_applied_direction_invalid",
        blocked_reasons,
    )
    clamped_speed = _safe_float(
        pc_first_jog_artifact.get("clamped_speed_mps"),
        "same_session_pc_command_clamped_speed_invalid",
        blocked_reasons,
    )
    clamped_duration = _safe_int(
        pc_first_jog_artifact.get("clamped_duration_ms"),
        "same_session_pc_command_clamped_duration_invalid",
        blocked_reasons,
    )
    checklist_confirmed = _safe_bool(
        pc_first_jog_artifact.get("confirm_hil_checklist"),
        "same_session_pc_command_checklist_invalid",
        blocked_reasons,
    )
    evidence_capture_status = _safe_string(
        pc_first_jog_artifact.get("evidence_capture_status"),
        "same_session_pc_command_evidence_capture_status_invalid",
        blocked_reasons,
    )
    if requested_direction not in {"forward", "back", "left", "right", "stop"}:
        blocked_reasons.append("same_session_pc_command_requested_direction_unexpected")
    if applied_direction not in {"forward", "back", "left", "right", "stop"}:
        blocked_reasons.append("same_session_pc_command_applied_direction_unexpected")
    if clamped_speed is None or clamped_speed <= 0.0:
        blocked_reasons.append("same_session_pc_command_clamped_speed_not_positive")
    if clamped_duration is None or clamped_duration <= 0:
        blocked_reasons.append("same_session_pc_command_clamped_duration_missing")
    if checklist_confirmed is not True:
        blocked_reasons.append("same_session_pc_command_checklist_not_confirmed")
    if evidence_capture_status != "captured":
        blocked_reasons.append("same_session_pc_command_evidence_not_captured")

    remote_motion_key_values = pc_first_jog_artifact.get("remote_motion_key_values")
    if not isinstance(remote_motion_key_values, dict):
        blocked_reasons.append("same_session_pc_command_remote_motion_key_values_missing")
        remote_motion_key_values = {}
    remote_lr_nonzero = _safe_string_bool(
        remote_motion_key_values.get("wheel_feedback_lr_nonzero_proven"),
        "same_session_pc_command_remote_lr_nonzero_invalid",
        blocked_reasons,
    )
    nonzero_frame_count = _safe_int(
        remote_motion_key_values.get("wheel_feedback_nonzero_frame_count"),
        "same_session_pc_command_nonzero_frame_count_invalid",
        blocked_reasons,
    )
    latest_left = _safe_float(
        remote_motion_key_values.get("wheel_feedback_latest_left_speed"),
        "same_session_pc_command_latest_left_invalid",
        blocked_reasons,
    )
    latest_right = _safe_float(
        remote_motion_key_values.get("wheel_feedback_latest_right_speed"),
        "same_session_pc_command_latest_right_invalid",
        blocked_reasons,
    )
    feedback_during_motion_attempted = _safe_string_bool(
        remote_motion_key_values.get("feedback_during_motion_attempted"),
        "same_session_pc_command_feedback_during_motion_attempted_invalid",
        blocked_reasons,
    )
    feedback_after_stop_attempted = _safe_string_bool(
        remote_motion_key_values.get("feedback_after_stop_attempted"),
        "same_session_pc_command_feedback_after_stop_attempted_invalid",
        blocked_reasons,
    )
    manual_command_executed = _safe_string_bool(
        remote_motion_key_values.get("manual_command_executed"),
        "same_session_pc_command_manual_command_executed_invalid",
        blocked_reasons,
    )
    auto_stop_executed = _safe_string_bool(
        remote_motion_key_values.get("auto_stop_executed"),
        "same_session_pc_command_auto_stop_executed_invalid",
        blocked_reasons,
    )
    if remote_lr_nonzero is not True:
        blocked_reasons.append("same_session_pc_command_remote_lr_nonzero_not_true")
    if nonzero_frame_count is None or nonzero_frame_count <= 0:
        blocked_reasons.append("same_session_pc_command_nonzero_frame_count_missing")
    if latest_left is None or latest_left == 0.0:
        blocked_reasons.append("same_session_pc_command_latest_left_zero_or_missing")
    if latest_right is None or latest_right == 0.0:
        blocked_reasons.append("same_session_pc_command_latest_right_zero_or_missing")
    if feedback_during_motion_attempted is not True:
        blocked_reasons.append("same_session_pc_command_feedback_during_motion_not_true")
    if feedback_after_stop_attempted is not True:
        blocked_reasons.append("same_session_pc_command_feedback_after_stop_not_true")
    if manual_command_executed is not True:
        blocked_reasons.append("same_session_pc_command_manual_command_not_executed")
    if auto_stop_executed is not True:
        blocked_reasons.append("same_session_pc_command_auto_stop_not_executed")

    feedback_ack = after_jog_base_status.get("feedback_ack")
    feedback_readback = after_jog_base_status.get("feedback_readback")
    feedback_samples_latest = after_jog_base_status.get("feedback_samples_latest")
    if not isinstance(feedback_ack, dict):
        blocked_reasons.append("same_session_pc_command_after_jog_feedback_ack_missing")
        feedback_ack = {}
    if not isinstance(feedback_readback, dict):
        blocked_reasons.append("same_session_pc_command_after_jog_feedback_readback_missing")
        feedback_readback = {}
    if not isinstance(feedback_samples_latest, dict):
        blocked_reasons.append("same_session_pc_command_after_jog_feedback_samples_latest_missing")
        feedback_samples_latest = {}
    _append_optional_false_fields(
        feedback_readback,
        "same_session_pc_command_after_jog_feedback_readback",
        (
            "safe_to_control",
            "delivery_success",
            "primary_actions_enabled",
            "robot_control_executed",
            "hil_pass",
            "sends_motion_commands",
        ),
        blocked_reasons,
    )
    _append_optional_false_fields(
        feedback_samples_latest,
        "same_session_pc_command_after_jog_feedback_samples_latest",
        (
            "safe_to_control",
            "delivery_success",
            "primary_actions_enabled",
            "robot_control_executed",
            "hil_pass",
            "sends_motion_commands",
        ),
        blocked_reasons,
    )
    ack_t1001_observed = _safe_bool(
        feedback_ack.get("t1001_observed"),
        "same_session_pc_command_after_jog_t1001_observed_invalid",
        blocked_reasons,
    )
    ack_source = _safe_string(
        feedback_ack.get("source"),
        "same_session_pc_command_after_jog_feedback_source_invalid",
        blocked_reasons,
    )
    if ack_t1001_observed is not True:
        blocked_reasons.append("same_session_pc_command_after_jog_t1001_not_observed")
    if ack_source != "fresh_readback":
        blocked_reasons.append("same_session_pc_command_after_jog_feedback_source_not_fresh_readback")

    readback_status = _safe_string(
        feedback_readback.get("t1001_feedback_status"),
        "same_session_pc_command_after_jog_feedback_status_invalid",
        blocked_reasons,
    )
    readback_lr_nonzero = _safe_bool(
        feedback_readback.get("wheel_feedback_lr_nonzero_proven"),
        "same_session_pc_command_after_jog_lr_nonzero_invalid",
        blocked_reasons,
    )
    readback_sends_commands = _safe_bool(
        after_jog_base_status.get("readback_sends_commands"),
        "same_session_pc_command_after_jog_readback_sends_commands_invalid",
        blocked_reasons,
    )
    latest_pair = None
    wheel_feedback_summary = feedback_readback.get("wheel_feedback_summary")
    if isinstance(wheel_feedback_summary, dict):
        latest_pair = wheel_feedback_summary.get("latest_pair")
    if not isinstance(latest_pair, dict):
        blocked_reasons.append("same_session_pc_command_after_jog_latest_pair_missing")
        latest_pair = {}
    pair_source = _safe_string(
        latest_pair.get("source"),
        "same_session_pc_command_after_jog_latest_pair_source_invalid",
        blocked_reasons,
    )
    after_left = _safe_float(
        latest_pair.get("left_speed"),
        "same_session_pc_command_after_jog_latest_pair_left_invalid",
        blocked_reasons,
    )
    after_right = _safe_float(
        latest_pair.get("right_speed"),
        "same_session_pc_command_after_jog_latest_pair_right_invalid",
        blocked_reasons,
    )
    if readback_status != "observed":
        blocked_reasons.append("same_session_pc_command_after_jog_feedback_status_not_observed")
    if readback_lr_nonzero is not False:
        blocked_reasons.append("same_session_pc_command_after_jog_lr_nonzero_not_false")
    if readback_sends_commands is not True:
        blocked_reasons.append("same_session_pc_command_after_jog_readback_sends_commands_not_true")
    if pair_source != "vendor_t1001_L_R":
        blocked_reasons.append("same_session_pc_command_after_jog_latest_pair_source_mismatch")
    if after_left is None or after_left != 0.0:
        blocked_reasons.append("same_session_pc_command_after_jog_latest_pair_left_not_zero")
    if after_right is None or after_right != 0.0:
        blocked_reasons.append("same_session_pc_command_after_jog_latest_pair_right_not_zero")

    freshness = feedback_samples_latest.get("freshness")
    if not isinstance(freshness, dict):
        blocked_reasons.append("same_session_pc_command_after_jog_freshness_missing")
        freshness = {}
    freshness_status = _safe_string(
        freshness.get("status"),
        "same_session_pc_command_after_jog_freshness_status_invalid",
        blocked_reasons,
    )
    latest_summary_sends_commands = _safe_bool(
        feedback_samples_latest.get("readback_sends_commands"),
        "same_session_pc_command_after_jog_feedback_samples_readback_sends_commands_invalid",
        blocked_reasons,
    )
    if freshness_status not in {"fresh", "stale"}:
        blocked_reasons.append("same_session_pc_command_after_jog_freshness_status_unexpected")
    if latest_summary_sends_commands is not False:
        blocked_reasons.append("same_session_pc_command_after_jog_feedback_samples_readback_sends_commands_not_false")

    latest_nonzero_pair = None
    if latest_left is not None and latest_right is not None:
        latest_nonzero_pair = {
            "phase": "motion_window",
            "left_speed": latest_left,
            "right_speed": latest_right,
            "sign_pattern": _wheel_sign_pattern(latest_left, latest_right),
        }
    after_jog_pair_summary = None
    if after_left is not None and after_right is not None:
        after_jog_pair_summary = {
            "phase": "after_jog_readback_latest",
            "left_speed": after_left,
            "right_speed": after_right,
            "sign_pattern": _wheel_sign_pattern(after_left, after_right),
        }
    present = (
        requested_direction in {"forward", "back", "left", "right", "stop"}
        and applied_direction in {"forward", "back", "left", "right", "stop"}
        and clamped_speed is not None
        and clamped_speed > 0.0
        and clamped_duration is not None
        and clamped_duration > 0
        and checklist_confirmed is True
        and evidence_capture_status == "captured"
        and remote_lr_nonzero is True
        and nonzero_frame_count is not None
        and nonzero_frame_count > 0
        and latest_left is not None
        and latest_left != 0.0
        and latest_right is not None
        and latest_right != 0.0
        and feedback_during_motion_attempted is True
        and feedback_after_stop_attempted is True
        and manual_command_executed is True
        and auto_stop_executed is True
        and ack_t1001_observed is True
        and ack_source == "fresh_readback"
        and readback_status == "observed"
        and readback_lr_nonzero is False
        and readback_sends_commands is True
        and pair_source == "vendor_t1001_L_R"
        and after_left == 0.0
        and after_right == 0.0
        and freshness_status in {"fresh", "stale"}
        and latest_summary_sends_commands is False
    )
    summary = {
        "source_schema": EXPECTED_SCHEMAS["robot_control_base_command_proxy"],
        "after_jog_source_schema": EXPECTED_SCHEMAS["base_status"],
        "historical_same_session_material": True,
        "current_live_rerun": False,
        "requested_direction": requested_direction,
        "applied_direction": applied_direction,
        "clamped_speed_mps": clamped_speed,
        "clamped_duration_ms": clamped_duration,
        "checklist_confirmed": checklist_confirmed is True,
        "evidence_capture_status": evidence_capture_status,
        "wheel_feedback_lr_nonzero_material_present": remote_lr_nonzero is True,
        "motion_window_nonzero_frame_count": nonzero_frame_count,
        "latest_nonzero_pair": latest_nonzero_pair,
        "feedback_during_motion_attempted": feedback_during_motion_attempted is True,
        "feedback_after_stop_attempted": feedback_after_stop_attempted is True,
        "manual_command_executed": manual_command_executed is True,
        "auto_stop_executed": auto_stop_executed is True,
        "after_jog_t1001_observed": ack_t1001_observed is True,
        "after_jog_feedback_source": ack_source,
        "after_jog_latest_pair": after_jog_pair_summary,
        "after_jog_wheel_feedback_lr_zero_readback": (
            readback_lr_nonzero is False and after_left == 0.0 and after_right == 0.0
        ),
        "after_jog_feedback_samples_freshness_status": freshness_status,
        "after_jog_readback_sends_commands": readback_sends_commands is True,
        "after_jog_feedback_samples_latest_readback_sends_commands": latest_summary_sends_commands,
        "material_ready_not_hil_pass": present,
    }
    return present, summary


def _parse_manual_hil_gate_current_evidence(
    gate_decision: dict[str, Any] | None,
    stop_safety_smoke: dict[str, Any] | None,
    manual_reject: dict[str, Any] | None,
    proxy_smoke: dict[str, Any] | None,
    feedback_samples_latest: dict[str, Any] | None,
    operator_report_latest: dict[str, Any] | None,
    robot_control_summary: dict[str, Any] | None,
    blocked_reasons: list[str],
) -> tuple[bool, dict[str, Any] | None]:
    """消费 manual HIL gate 只读材料，并把“不能动”原因固定成安全摘要。"""
    if any(
        item is None
        for item in (
            gate_decision,
            stop_safety_smoke,
            manual_reject,
            proxy_smoke,
            feedback_samples_latest,
            operator_report_latest,
            robot_control_summary,
        )
    ):
        blocked_reasons.append("manual_hil_gate_core_artifact_missing")
        return False, None

    assert gate_decision is not None
    assert stop_safety_smoke is not None
    assert manual_reject is not None
    assert proxy_smoke is not None
    assert feedback_samples_latest is not None
    assert operator_report_latest is not None
    assert robot_control_summary is not None

    if gate_decision.get("schema") != EXPECTED_SCHEMAS["manual_hil_gate_current_decision"]:
        blocked_reasons.append("manual_hil_gate_decision_schema_mismatch")
    if proxy_smoke.get("schema") != EXPECTED_SCHEMAS["manual_hil_gate_proxy_smoke_result"]:
        blocked_reasons.append("manual_hil_gate_proxy_smoke_schema_mismatch")
    if operator_report_latest.get("schema") != EXPECTED_SCHEMAS["operator_report_latest_result"]:
        blocked_reasons.append("manual_hil_gate_operator_report_schema_mismatch")
    if robot_control_summary.get("schema") != EXPECTED_SCHEMAS["robot_control_summary"]:
        blocked_reasons.append("manual_hil_gate_robot_control_summary_schema_mismatch")

    operator_gate = gate_decision.get("operator_gate")
    if not isinstance(operator_gate, dict):
        blocked_reasons.append("manual_hil_gate_operator_gate_missing")
        operator_gate = {}
    operator_gate_status = _safe_string(
        operator_gate.get("status"),
        "manual_hil_gate_status_invalid",
        blocked_reasons,
    )
    if operator_gate_status != "blocked":
        blocked_reasons.append("manual_hil_gate_status_not_blocked")
    missing_fields = operator_gate.get("missing_fields")
    safe_missing_fields: list[str] = []
    if not isinstance(missing_fields, list):
        blocked_reasons.append("manual_hil_gate_missing_fields_invalid")
    else:
        for index, item in enumerate(missing_fields):
            safe_item = _safe_string(item, f"manual_hil_gate_missing_field_{index}_invalid", blocked_reasons)
            if safe_item is not None:
                safe_missing_fields.append(safe_item)
    if safe_missing_fields != MANUAL_HIL_GATE_REQUIRED_MISSING_FIELDS:
        blocked_reasons.append("manual_hil_gate_missing_fields_mismatch")
    visible_blocks_motion = _safe_bool(
        gate_decision.get("visible_content_proven_blocks_motion"),
        "manual_hil_gate_visible_blocks_motion_invalid",
        blocked_reasons,
    )
    if visible_blocks_motion is not True:
        blocked_reasons.append("manual_hil_gate_visible_blocks_motion_not_true")
    manual_nonzero_policy = _safe_string(
        gate_decision.get("manual_nonzero_policy"),
        "manual_hil_gate_nonzero_policy_invalid",
        blocked_reasons,
    )
    if manual_nonzero_policy != "do_not_send_nonzero_expect_pc_local_reject":
        blocked_reasons.append("manual_hil_gate_nonzero_policy_unexpected")

    stop_ok = _safe_bool(stop_safety_smoke.get("ok"), "manual_hil_gate_stop_ok_invalid", blocked_reasons)
    stop_http_status = _safe_int(
        stop_safety_smoke.get("http_status"),
        "manual_hil_gate_stop_http_status_invalid",
        blocked_reasons,
    )
    stop_body = stop_safety_smoke.get("body")
    if not isinstance(stop_body, dict):
        blocked_reasons.append("manual_hil_gate_stop_body_missing")
        stop_body = {}
    _append_dangerous_true(stop_body, "manual_hil_gate_stop_body", blocked_reasons)
    if stop_body.get("schema") != EXPECTED_SCHEMAS["robot_control_base_command_proxy"]:
        blocked_reasons.append("manual_hil_gate_stop_body_schema_mismatch")
    stop_command_kind = _safe_string(
        stop_body.get("command_kind"),
        "manual_hil_gate_stop_command_kind_invalid",
        blocked_reasons,
    )
    stop_proxy_status = _safe_string(
        stop_body.get("proxy_status"),
        "manual_hil_gate_stop_proxy_status_invalid",
        blocked_reasons,
    )
    stop_remote_http_status = _safe_int(
        stop_body.get("remote_http_status"),
        "manual_hil_gate_stop_remote_http_status_invalid",
        blocked_reasons,
    )
    stop_status = _safe_string(
        stop_body.get("status"),
        "manual_hil_gate_stop_status_invalid",
        blocked_reasons,
    )
    stop_evidence_capture = _safe_string(
        stop_body.get("evidence_capture_status"),
        "manual_hil_gate_stop_evidence_capture_invalid",
        blocked_reasons,
    )
    stop_robot_control_executed = _safe_bool(
        stop_body.get("robot_control_executed"),
        "manual_hil_gate_stop_robot_control_executed_invalid",
        blocked_reasons,
    )
    if stop_ok is not True or stop_http_status != 200:
        blocked_reasons.append("manual_hil_gate_stop_smoke_http_not_200")
    if stop_command_kind != "stop":
        blocked_reasons.append("manual_hil_gate_stop_command_kind_not_stop")
    if stop_proxy_status != "command_forwarded":
        blocked_reasons.append("manual_hil_gate_stop_not_forwarded")
    if stop_remote_http_status != 200:
        blocked_reasons.append("manual_hil_gate_stop_remote_http_not_200")
    if stop_status != "stopped":
        blocked_reasons.append("manual_hil_gate_stop_status_not_stopped")
    if stop_evidence_capture != "captured":
        blocked_reasons.append("manual_hil_gate_stop_evidence_not_captured")
    if stop_robot_control_executed is not False:
        blocked_reasons.append("manual_hil_gate_stop_robot_control_executed_not_false")

    manual_http_status = _safe_int(
        manual_reject.get("http_status"),
        "manual_hil_gate_manual_http_status_invalid",
        blocked_reasons,
    )
    manual_body = manual_reject.get("body")
    if not isinstance(manual_body, dict):
        blocked_reasons.append("manual_hil_gate_manual_body_missing")
        manual_body = {}
    _append_dangerous_true(manual_body, "manual_hil_gate_manual_body", blocked_reasons)
    if manual_body.get("schema") != EXPECTED_SCHEMAS["robot_control_base_command_proxy"]:
        blocked_reasons.append("manual_hil_gate_manual_body_schema_mismatch")
    manual_command_kind = _safe_string(
        manual_body.get("command_kind"),
        "manual_hil_gate_manual_command_kind_invalid",
        blocked_reasons,
    )
    manual_proxy_status = _safe_string(
        manual_body.get("proxy_status"),
        "manual_hil_gate_manual_proxy_status_invalid",
        blocked_reasons,
    )
    manual_status = _safe_string(
        manual_body.get("status"),
        "manual_hil_gate_manual_status_invalid",
        blocked_reasons,
    )
    manual_gate_status = _safe_string(
        manual_body.get("hil_checklist_gate_status"),
        "manual_hil_gate_manual_gate_status_invalid",
        blocked_reasons,
    )
    manual_robot_control_executed = _safe_bool(
        manual_body.get("robot_control_executed"),
        "manual_hil_gate_manual_robot_control_executed_invalid",
        blocked_reasons,
    )
    manual_evidence_capture = _safe_string(
        manual_body.get("evidence_capture_status"),
        "manual_hil_gate_manual_evidence_capture_invalid",
        blocked_reasons,
    )
    preflight = manual_body.get("operator_report_preflight")
    if not isinstance(preflight, dict):
        blocked_reasons.append("manual_hil_gate_manual_preflight_missing")
        preflight = {}
    preflight_status = _safe_string(
        preflight.get("status"),
        "manual_hil_gate_manual_preflight_status_invalid",
        blocked_reasons,
    )
    preflight_failure_reason = _safe_string(
        preflight.get("failure_reason"),
        "manual_hil_gate_manual_preflight_failure_reason_invalid",
        blocked_reasons,
    )
    preflight_missing_fields = preflight.get("missing_fields")
    safe_preflight_missing_fields: list[str] = []
    if not isinstance(preflight_missing_fields, list):
        blocked_reasons.append("manual_hil_gate_manual_preflight_missing_fields_invalid")
    else:
        for index, item in enumerate(preflight_missing_fields):
            safe_item = _safe_string(
                item,
                f"manual_hil_gate_manual_preflight_missing_field_{index}_invalid",
                blocked_reasons,
            )
            if safe_item is not None:
                safe_preflight_missing_fields.append(safe_item)
    if manual_http_status != 400:
        blocked_reasons.append("manual_hil_gate_manual_http_status_not_400")
    if manual_command_kind != "manual":
        blocked_reasons.append("manual_hil_gate_manual_command_kind_not_manual")
    if manual_proxy_status != "command_rejected":
        blocked_reasons.append("manual_hil_gate_manual_proxy_status_not_rejected")
    if manual_status != "blocked":
        blocked_reasons.append("manual_hil_gate_manual_status_not_blocked")
    if manual_gate_status != "manual_allowed":
        blocked_reasons.append("manual_hil_gate_manual_gate_status_not_manual_allowed")
    if manual_body.get("remote_http_status") is not None:
        blocked_reasons.append("manual_hil_gate_manual_remote_http_status_not_null")
    if manual_robot_control_executed is not False:
        blocked_reasons.append("manual_hil_gate_manual_robot_control_executed_not_false")
    if manual_evidence_capture != "captured":
        blocked_reasons.append("manual_hil_gate_manual_evidence_not_captured")
    if preflight_status != "blocked":
        blocked_reasons.append("manual_hil_gate_manual_preflight_status_not_blocked")
    if preflight_failure_reason != "operator_report_preflight_required":
        blocked_reasons.append("manual_hil_gate_manual_preflight_failure_reason_unexpected")
    if safe_preflight_missing_fields != MANUAL_HIL_GATE_REQUIRED_MISSING_FIELDS:
        blocked_reasons.append("manual_hil_gate_manual_preflight_missing_fields_mismatch")

    stop_section = proxy_smoke.get("stop")
    manual_section = proxy_smoke.get("manual")
    if not isinstance(stop_section, dict):
        blocked_reasons.append("manual_hil_gate_proxy_stop_missing")
        stop_section = {}
    if not isinstance(manual_section, dict):
        blocked_reasons.append("manual_hil_gate_proxy_manual_missing")
        manual_section = {}
    proxy_stop_status = _safe_string(
        stop_section.get("proxy_status"),
        "manual_hil_gate_proxy_stop_status_invalid",
        blocked_reasons,
    )
    proxy_stop_http_status = _safe_int(
        stop_section.get("remote_http_status"),
        "manual_hil_gate_proxy_stop_http_status_invalid",
        blocked_reasons,
    )
    proxy_manual_status = _safe_string(
        manual_section.get("proxy_status"),
        "manual_hil_gate_proxy_manual_status_invalid",
        blocked_reasons,
    )
    proxy_manual_failure_reason = _safe_string(
        manual_section.get("failure_reason"),
        "manual_hil_gate_proxy_manual_failure_reason_invalid",
        blocked_reasons,
    )
    proxy_manual_not_called = _safe_bool(
        manual_section.get("remote_base_manual_not_called_by_local_reject"),
        "manual_hil_gate_proxy_manual_not_called_invalid",
        blocked_reasons,
    )
    if proxy_stop_status != "command_forwarded" or proxy_stop_http_status != 200:
        blocked_reasons.append("manual_hil_gate_proxy_stop_mismatch")
    if proxy_manual_status != "command_rejected":
        blocked_reasons.append("manual_hil_gate_proxy_manual_status_not_rejected")
    if proxy_manual_failure_reason != "operator_report_preflight_required":
        blocked_reasons.append("manual_hil_gate_proxy_manual_failure_reason_unexpected")
    if proxy_manual_not_called is not True:
        blocked_reasons.append("manual_hil_gate_remote_base_manual_called")

    feedback_body = feedback_samples_latest.get("body")
    if not isinstance(feedback_body, dict):
        blocked_reasons.append("manual_hil_gate_feedback_body_missing")
        feedback_body = {}
    _append_dangerous_true(feedback_body, "manual_hil_gate_feedback_body", blocked_reasons)
    if feedback_body.get("schema") != EXPECTED_SCHEMAS["base_feedback_samples_latest"]:
        blocked_reasons.append("manual_hil_gate_feedback_schema_mismatch")
    latest_result = feedback_body.get("latest_result")
    if not isinstance(latest_result, dict):
        blocked_reasons.append("manual_hil_gate_feedback_latest_result_missing")
        latest_result = {}
    _append_dangerous_true(latest_result, "manual_hil_gate_feedback_latest_result", blocked_reasons)
    latest_request = latest_result.get("request")
    if not isinstance(latest_request, dict):
        blocked_reasons.append("manual_hil_gate_feedback_request_missing")
        latest_request = {}
    latest_command = latest_request.get("command")
    if not isinstance(latest_command, dict):
        blocked_reasons.append("manual_hil_gate_feedback_request_command_missing")
        latest_command = {}
    request_t = _safe_int(
        latest_command.get("T"),
        "manual_hil_gate_feedback_request_t_invalid",
        blocked_reasons,
    )
    t1001_count = _safe_int(
        latest_result.get("t1001_observed_count"),
        "manual_hil_gate_t1001_observed_count_invalid",
        blocked_reasons,
    )
    all_samples_observed_t1001 = _safe_bool(
        latest_result.get("all_samples_observed_t1001"),
        "manual_hil_gate_all_samples_observed_t1001_invalid",
        blocked_reasons,
    )
    sends_motion_commands = _safe_bool(
        latest_result.get("sends_motion_commands"),
        "manual_hil_gate_sends_motion_commands_invalid",
        blocked_reasons,
    )
    feedback_robot_control_executed = _safe_bool(
        latest_result.get("robot_control_executed"),
        "manual_hil_gate_feedback_robot_control_executed_invalid",
        blocked_reasons,
    )
    feedback_safe_to_control = _safe_bool(
        latest_result.get("safe_to_control"),
        "manual_hil_gate_feedback_safe_to_control_invalid",
        blocked_reasons,
    )
    feedback_delivery_success = _safe_bool(
        latest_result.get("delivery_success"),
        "manual_hil_gate_feedback_delivery_success_invalid",
        blocked_reasons,
    )
    feedback_primary_actions_enabled = _safe_bool(
        latest_result.get("primary_actions_enabled"),
        "manual_hil_gate_feedback_primary_actions_enabled_invalid",
        blocked_reasons,
    )
    observed_feedback_types = _parse_feedback_type_list(
        latest_result.get("observed_feedback_types"),
        "manual_hil_gate_feedback_observed_types_invalid",
        blocked_reasons,
    )
    if request_t != 130:
        blocked_reasons.append("manual_hil_gate_feedback_request_not_t130")
    if t1001_count != 2:
        blocked_reasons.append("manual_hil_gate_t1001_observed_count_not_two")
    if all_samples_observed_t1001 is not True:
        blocked_reasons.append("manual_hil_gate_all_samples_observed_t1001_not_true")
    if observed_feedback_types != [1001]:
        blocked_reasons.append("manual_hil_gate_feedback_observed_types_not_t1001_only")
    if sends_motion_commands is not False:
        blocked_reasons.append("manual_hil_gate_feedback_sends_motion_commands_not_false")
    if feedback_robot_control_executed is not False:
        blocked_reasons.append("manual_hil_gate_feedback_robot_control_executed_not_false")
    if feedback_safe_to_control is not False:
        blocked_reasons.append("manual_hil_gate_feedback_safe_to_control_not_false")
    if feedback_delivery_success is not False:
        blocked_reasons.append("manual_hil_gate_feedback_delivery_success_not_false")
    if feedback_primary_actions_enabled is not False:
        blocked_reasons.append("manual_hil_gate_feedback_primary_actions_enabled_not_false")

    operator_material_only = _safe_bool(
        operator_report_latest.get("operator_report_material_only"),
        "manual_hil_gate_operator_material_only_invalid",
        blocked_reasons,
    )
    operator_structured_claims = operator_report_latest.get("structured_hil_claims")
    if not isinstance(operator_structured_claims, dict):
        blocked_reasons.append("manual_hil_gate_operator_structured_claims_missing")
        operator_structured_claims = {}
    operator_claim_normalization = operator_structured_claims.get("normalization")
    if not isinstance(operator_claim_normalization, dict):
        blocked_reasons.append("manual_hil_gate_operator_claim_normalization_missing")
        operator_claim_normalization = {}
    operator_claim_material_only = _safe_bool(
        operator_claim_normalization.get("material_only"),
        "manual_hil_gate_operator_claim_material_only_invalid",
        blocked_reasons,
    )
    operator_top_level_delivery_success = _safe_bool(
        operator_report_latest.get("delivery_success"),
        "manual_hil_gate_operator_top_level_delivery_success_invalid",
        blocked_reasons,
    )
    operator_nested_delivery_claim = _safe_bool(
        operator_structured_claims.get("delivery_success"),
        "manual_hil_gate_operator_nested_delivery_claim_invalid",
        blocked_reasons,
    )
    delivery_forced_false = _safe_bool(
        operator_claim_normalization.get("top_level_delivery_success_forced_false"),
        "manual_hil_gate_operator_delivery_forced_false_invalid",
        blocked_reasons,
    )
    if operator_material_only is not True:
        blocked_reasons.append("manual_hil_gate_operator_material_only_not_true")
    if operator_claim_material_only is not True:
        blocked_reasons.append("manual_hil_gate_operator_claim_material_only_not_true")
    if operator_top_level_delivery_success is not False:
        blocked_reasons.append("manual_hil_gate_operator_top_level_delivery_success_not_false")
    if operator_nested_delivery_claim is not True:
        blocked_reasons.append("manual_hil_gate_operator_nested_delivery_claim_not_true")
    if delivery_forced_false is not True:
        blocked_reasons.append("manual_hil_gate_operator_delivery_forced_false_not_true")

    console_status = _safe_string(
        robot_control_summary.get("console_status"),
        "manual_hil_gate_console_status_invalid",
        blocked_reasons,
    )
    if console_status != "blocked":
        blocked_reasons.append("manual_hil_gate_console_status_not_blocked")
    operator_hil_material_summary = robot_control_summary.get("operator_hil_material_summary")
    if not isinstance(operator_hil_material_summary, dict):
        blocked_reasons.append("manual_hil_gate_operator_hil_material_summary_missing")
        operator_hil_material_summary = {}
    operator_report_status = _safe_string(
        operator_hil_material_summary.get("report_status"),
        "manual_hil_gate_operator_report_status_invalid",
        blocked_reasons,
    )
    operator_delivery_claim = _safe_string(
        operator_hil_material_summary.get("delivery_claim"),
        "manual_hil_gate_operator_delivery_claim_invalid",
        blocked_reasons,
    )
    safe_command_boundary = robot_control_summary.get("safe_command_boundary")
    if not isinstance(safe_command_boundary, dict):
        blocked_reasons.append("manual_hil_gate_safe_command_boundary_missing")
        safe_command_boundary = {}
    non_stop_requires_checklist = _safe_bool(
        safe_command_boundary.get("non_stop_requires_confirm_hil_checklist"),
        "manual_hil_gate_non_stop_requires_checklist_invalid",
        blocked_reasons,
    )
    safe_boundary_robot_control_executed = _safe_bool(
        safe_command_boundary.get("robot_control_executed"),
        "manual_hil_gate_safe_boundary_robot_control_executed_invalid",
        blocked_reasons,
    )
    robot_api_connection = robot_control_summary.get("robot_api_connection")
    if not isinstance(robot_api_connection, dict):
        blocked_reasons.append("manual_hil_gate_robot_api_connection_missing")
        robot_api_connection = {}
    robot_api_status = _safe_string(
        robot_api_connection.get("status"),
        "manual_hil_gate_robot_api_connection_status_invalid",
        blocked_reasons,
    )
    if operator_report_status != "ready_for_execution":
        blocked_reasons.append("manual_hil_gate_operator_report_status_unexpected")
    if operator_delivery_claim != "true":
        blocked_reasons.append("manual_hil_gate_operator_delivery_claim_not_material_true")
    if non_stop_requires_checklist is not True:
        blocked_reasons.append("manual_hil_gate_non_stop_requires_checklist_not_true")
    if safe_boundary_robot_control_executed is not False:
        blocked_reasons.append("manual_hil_gate_safe_boundary_robot_control_executed_not_false")
    if robot_api_status != "blocked":
        blocked_reasons.append("manual_hil_gate_robot_api_connection_status_not_blocked")

    present = not any(reason.startswith("manual_hil_gate_") for reason in blocked_reasons)
    summary = {
        "manual_hil_gate_status": operator_gate_status,
        "manual_hil_gate_missing_fields": safe_missing_fields,
        "visible_content_proven_blocks_motion": visible_blocks_motion is True,
        "manual_nonzero_policy": manual_nonzero_policy,
        "stop_safety_smoke_forwarded": (
            stop_ok is True
            and stop_http_status == 200
            and stop_command_kind == "stop"
            and stop_proxy_status == "command_forwarded"
            and stop_remote_http_status == 200
            and stop_status == "stopped"
            and stop_evidence_capture == "captured"
        ),
        "stop_remote_http_status": stop_remote_http_status,
        "manual_nonstop_local_reject_present": (
            manual_http_status == 400
            and manual_command_kind == "manual"
            and manual_proxy_status == "command_rejected"
            and manual_status == "blocked"
            and preflight_status == "blocked"
        ),
        "manual_nonstop_remote_base_manual_called": False,
        "manual_nonstop_failure_reason": preflight_failure_reason,
        "proxy_remote_base_manual_not_called_by_local_reject": proxy_manual_not_called is True,
        "manual_gate_t1001_observed_count": t1001_count,
        "manual_gate_all_samples_observed_t1001": all_samples_observed_t1001 is True,
        "manual_gate_feedback_request_t130_observed": request_t == 130,
        "operator_structured_report_material_only": operator_material_only is True,
        "operator_structured_report_status": operator_report_status,
        "operator_structured_delivery_claim_material_only": (
            operator_claim_material_only is True
            and operator_nested_delivery_claim is True
            and operator_top_level_delivery_success is False
            and delivery_forced_false is True
            and operator_delivery_claim == "true"
        ),
        "manual_hil_gate_ready_not_hil_pass": present,
    }
    return present, summary


def build_motion_map_hil_material_bundle(
    first_jog: dict[str, Any],
    feedback_samples: dict[str, Any],
    scan_delta: dict[str, Any],
    operator_report: dict[str, Any],
    field_map_yaml: dict[str, Any],
    field_map_pgm_path: Path,
    field_pixel_review: dict[str, Any],
    manual_map_yaml: dict[str, Any],
    manual_map_pgm_path: Path,
    manual_pixel_review: dict[str, Any],
    source_refs: dict[str, str],
    free_cell_map_start: dict[str, Any] | None = None,
    free_cell_map_list: dict[str, Any] | None = None,
    free_cell_map_yaml: dict[str, Any] | None = None,
    free_cell_map_pgm_path: Path | None = None,
    free_cell_pixel_review: dict[str, Any] | None = None,
    free_cell_pc_summary: dict[str, Any] | None = None,
    clean_baseline_nav2_latest: dict[str, Any] | None = None,
    clean_baseline_nav2_retry_summary: dict[str, Any] | None = None,
    clean_baseline_comparator_load_reasons: list[str] | None = None,
    bounded_motion_feedback_summary: dict[str, Any] | None = None,
    bounded_motion_pulse_and_stop_log: str | None = None,
    bounded_motion_odom_after_motion_text: str | None = None,
    bounded_motion_imu_once_text: str | None = None,
    pc_real_robot_api_readback_summary: dict[str, Any] | None = None,
    base_feedback_samples_latest: dict[str, Any] | None = None,
    wheel_feedback_diagnostic_sweep_summary: dict[str, Any] | None = None,
    wheel_feedback_diagnostic_load_reasons: list[str] | None = None,
    manual_hil_gate_decision: dict[str, Any] | None = None,
    manual_hil_gate_stop_safety_smoke: dict[str, Any] | None = None,
    manual_hil_gate_manual_reject: dict[str, Any] | None = None,
    manual_hil_gate_proxy_smoke: dict[str, Any] | None = None,
    manual_hil_gate_feedback_samples_latest: dict[str, Any] | None = None,
    manual_hil_gate_operator_report_latest: dict[str, Any] | None = None,
    manual_hil_gate_robot_control_summary: dict[str, Any] | None = None,
    same_session_wheel_feedback: dict[str, Any] | None = None,
    same_session_pc_first_jog: dict[str, Any] | None = None,
    same_session_pc_after_jog_base_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """把历史 motion+map 材料压成可回归的安全 bundle。"""
    blocked_reasons: list[str] = []

    first_jog_present, first_jog_summary = _parse_first_jog(first_jog, blocked_reasons)
    feedback_present, feedback_summary = _parse_feedback_samples(feedback_samples, blocked_reasons)
    scan_delta_present, scan_delta_summary = _parse_scan_delta(scan_delta, blocked_reasons)
    operator_present, operator_summary, operator_run_token = _parse_operator_report(
        operator_report, scan_delta_present, blocked_reasons
    )
    field_map_present, field_map_summary, field_pixel_summary, field_run_token = _parse_map_group(
        "field_first_jog",
        field_map_yaml,
        field_map_pgm_path,
        field_pixel_review,
        blocked_reasons,
    )
    manual_map_present, manual_map_summary, manual_pixel_summary, manual_run_token = _parse_map_group(
        "manual_motion",
        manual_map_yaml,
        manual_map_pgm_path,
        manual_pixel_review,
        blocked_reasons,
    )
    if (
        free_cell_map_start is None
        or free_cell_map_list is None
        or free_cell_map_yaml is None
        or free_cell_map_pgm_path is None
        or free_cell_pixel_review is None
        or free_cell_pc_summary is None
    ):
        blocked_reasons.append("free_cell_material_artifact_missing")
        free_cell_lifecycle_present = False
        free_cell_lifecycle_summary = None
        free_cell_list_present = False
        free_cell_list_summary = None
        free_cell_yaml_present = False
        free_cell_map_summary = None
        free_cell_pixel_present = False
        free_cell_pixel_summary = None
        free_cell_pc_present = False
        free_cell_pc_summary_out = None
        free_cell_map_token = None
    else:
        free_cell_lifecycle_present, free_cell_lifecycle_summary, free_cell_map_name = _parse_free_cell_lifecycle_start(
            free_cell_map_start,
            blocked_reasons,
        )
        free_cell_list_present, free_cell_list_summary = _parse_free_cell_map_list(
            free_cell_map_list,
            free_cell_map_name,
            blocked_reasons,
        )
        free_cell_yaml_present, free_cell_map_summary, free_cell_pixel_summary, free_cell_map_token = _parse_free_cell_map_group(
            free_cell_map_yaml,
            free_cell_map_pgm_path,
            free_cell_pixel_review,
            free_cell_map_name,
            blocked_reasons,
        )
        free_cell_pixel_present = free_cell_pixel_summary is not None and not any(
            reason.startswith("free_cell_pixel_") or reason.startswith("free_cell_has_")
            for reason in blocked_reasons
        )
        free_cell_pc_present, free_cell_pc_summary_out = _parse_free_cell_pc_summary(
            free_cell_pc_summary,
            blocked_reasons,
        )
    localization_path_present, localization_path_summary = _parse_localization_path_material_bridge(
        free_cell_pc_summary or {},
        blocked_reasons,
    )
    comparator_present, comparator_summary, comparator_blocked_reasons = _parse_cross_run_clean_baseline_path_comparator(
        clean_baseline_nav2_latest,
        clean_baseline_nav2_retry_summary,
        clean_baseline_comparator_load_reasons,
    )
    bounded_feedback_present, bounded_feedback_summary = _parse_bounded_motion_feedback_summary(
        bounded_motion_feedback_summary,
        blocked_reasons,
    )
    ros_readback_present, ros_readback_summary = _parse_bounded_motion_ros_readbacks(
        bounded_motion_pulse_and_stop_log,
        bounded_motion_odom_after_motion_text,
        bounded_motion_imu_once_text,
        blocked_reasons,
    )
    pc_readback_present, pc_readback_summary = _parse_pc_real_robot_api_readback_summary(
        pc_real_robot_api_readback_summary,
        blocked_reasons,
    )
    base_feedback_latest_present, base_feedback_latest_summary = _parse_base_feedback_samples_latest(
        base_feedback_samples_latest,
        blocked_reasons,
    )
    diagnostic_present, diagnostic_summary = _parse_wheel_feedback_diagnostic_sweep(
        wheel_feedback_diagnostic_sweep_summary,
        blocked_reasons,
        wheel_feedback_diagnostic_load_reasons,
    )
    manual_hil_gate_present, manual_hil_gate_summary = _parse_manual_hil_gate_current_evidence(
        manual_hil_gate_decision,
        manual_hil_gate_stop_safety_smoke,
        manual_hil_gate_manual_reject,
        manual_hil_gate_proxy_smoke,
        manual_hil_gate_feedback_samples_latest,
        manual_hil_gate_operator_report_latest,
        manual_hil_gate_robot_control_summary,
        blocked_reasons,
    )
    same_session_wheel_feedback_present, same_session_wheel_feedback_summary = (
        _parse_same_session_wheel_feedback_material(
            same_session_wheel_feedback,
            blocked_reasons,
        )
    )
    same_session_pc_command_present, same_session_pc_command_summary = (
        _parse_same_session_pc_command_material(
            same_session_pc_first_jog,
            same_session_pc_after_jog_base_status,
            blocked_reasons,
        )
    )

    run_tokens = {token for token in (operator_run_token, field_run_token, manual_run_token) if token is not None}
    if len(run_tokens) != 1:
        blocked_reasons.append("same_run_token_not_proven")
        run_token = None
    else:
        run_token = next(iter(run_tokens))

    # 该 bundle 明确承认“没有 free cells”，因此 real_route_map_proven 必须仍是 false。
    if operator_summary is not None and operator_summary.get("real_route_map_proven") is not False:
        blocked_reasons.append("operator_route_map_claim_mismatch")

    status = READY_STATUS if not blocked_reasons else BLOCKED_STATUS
    summary = _safe_base_summary(status, source_refs, _dedupe(blocked_reasons))
    bounded_motion_ready = (
        bounded_feedback_present
        and ros_readback_present
        and pc_readback_present
        and base_feedback_latest_present
        and status == READY_STATUS
    )
    same_session_wheel_feedback_ready = same_session_wheel_feedback_present and status == READY_STATUS
    same_session_pc_command_ready = same_session_pc_command_present and status == READY_STATUS
    summary.update(
        {
            "same_run_material_present": status == READY_STATUS,
            "run_token": run_token,
            "first_jog_command_present": first_jog_present,
            "first_jog_command_summary": first_jog_summary,
            "feedback_sample_present": feedback_present,
            "feedback_sample_summary": feedback_summary,
            "scan_delta_present": scan_delta_present,
            "scan_delta_summary": scan_delta_summary,
            "operator_report_present": operator_present,
            "operator_claim_summary": operator_summary,
            "field_first_jog_map_present": field_map_present,
            "field_first_jog_map_summary": field_map_summary,
            "manual_motion_map_present": manual_map_present,
            "manual_motion_map_summary": manual_map_summary,
            "pixel_review_summary": {
                "field_first_jog_map": field_pixel_summary,
                "manual_motion_map": manual_pixel_summary,
            },
            "map_output_present": field_map_present and manual_map_present,
            "map_navigation_ready": False,
            "free_cell_map_material_present": (
                free_cell_lifecycle_present
                and free_cell_list_present
                and free_cell_yaml_present
                and free_cell_pixel_present
                and free_cell_pc_present
                and status == READY_STATUS
            ),
            "free_cell_map_lifecycle_present": free_cell_lifecycle_present,
            "free_cell_map_list_present": free_cell_list_present,
            "free_cell_map_yaml_present": free_cell_yaml_present,
            "free_cell_map_pgm_present": free_cell_yaml_present,
            "free_cell_pixel_review_present": free_cell_pixel_present,
            "free_cell_pc_summary_present": free_cell_pc_present,
            "free_cell_map_summary": {
                "lifecycle": free_cell_lifecycle_summary,
                "map_list": free_cell_list_summary,
                "map": free_cell_map_summary,
                "map_token": free_cell_map_token,
            },
            "free_cell_pixel_review_summary": free_cell_pixel_summary,
            "free_cell_pc_summary": free_cell_pc_summary_out,
            "free_cell_pixel_count": (
                free_cell_pixel_summary.get("free_pixel_count")
                if free_cell_pixel_present and isinstance(free_cell_pixel_summary, dict)
                else None
            ),
            "free_cell_has_free_cells": (
                free_cell_pixel_summary.get("has_free_cells") is True
                if free_cell_pixel_present and isinstance(free_cell_pixel_summary, dict)
                else False
            ),
            "free_cell_usable_map_count": (
                free_cell_list_summary.get("usable_map_count")
                if free_cell_list_present and isinstance(free_cell_list_summary, dict)
                else None
            ),
            "map_navigation_material_ready": (
                free_cell_lifecycle_present
                and free_cell_list_present
                and free_cell_yaml_present
                and free_cell_pixel_present
                and free_cell_pc_present
                and status == READY_STATUS
            ),
            "localization_path_material_bridge_present": localization_path_present and status == READY_STATUS,
            "same_run_localization_material_present": (
                localization_path_summary is not None
                and localization_path_summary.get("same_run_map_once_observed") is True
                and localization_path_summary.get("same_run_amcl_pose_observed") is True
                and localization_path_summary.get("same_run_localization_tf_map_to_odom") is True
                and localization_path_summary.get("same_run_localization_tf_map_to_base_link") is True
                and status == READY_STATUS
            ),
            "same_run_map_once_observed": (
                localization_path_summary.get("same_run_map_once_observed") is True
                if isinstance(localization_path_summary, dict)
                else False
            ),
            "same_run_amcl_pose_observed": (
                localization_path_summary.get("same_run_amcl_pose_observed") is True
                if isinstance(localization_path_summary, dict)
                else False
            ),
            "same_run_localization_tf_map_to_odom": (
                localization_path_summary.get("same_run_localization_tf_map_to_odom") is True
                if isinstance(localization_path_summary, dict)
                else False
            ),
            "same_run_localization_tf_map_to_base_link": (
                localization_path_summary.get("same_run_localization_tf_map_to_base_link") is True
                if isinstance(localization_path_summary, dict)
                else False
            ),
            "same_run_planner_server_active": (
                localization_path_summary.get("same_run_planner_server_active") is True
                if isinstance(localization_path_summary, dict)
                else False
            ),
            "same_run_path_generation_requested": (
                localization_path_summary.get("same_run_path_generation_requested") is True
                if isinstance(localization_path_summary, dict)
                else False
            ),
            "same_run_path_generation_succeeded": False,
            "same_run_path_generated": False,
            "same_run_path_point_count": (
                localization_path_summary.get("same_run_path_point_count")
                if isinstance(localization_path_summary, dict)
                else None
            ),
            "same_run_path_proven": False,
            "localization_path_bridge_ready_not_route_execution_proof": (
                localization_path_present and status == READY_STATUS
            ),
            "localization_path_material_bridge_summary": localization_path_summary,
            "cross_run_clean_baseline_path_comparator_present": comparator_present,
            "cross_run_clean_baseline_path_comparator_blocked_reasons": comparator_blocked_reasons,
            "cross_run_clean_baseline_path_summary": comparator_summary,
            "bounded_motion_feedback_material_present": bounded_motion_ready,
            "bounded_motion_feedback_present": bounded_motion_ready,
            "bounded_motion_feedback_material_status": (
                "bounded_motion_feedback_material_ready_not_hil_pass"
                if bounded_motion_ready
                else "bounded_motion_feedback_material_blocked_not_hil_pass"
            ),
            "feedback_motion_summary_present": bounded_feedback_present,
            "feedback_motion_summary": bounded_feedback_summary,
            "bounded_motion_command_observed": (
                bounded_feedback_summary.get("linear_x_mps") == 0.03
                if isinstance(bounded_feedback_summary, dict)
                else False
            ),
            "bounded_motion_duration_lte_0_3s": (
                bounded_feedback_summary.get("nonzero_duration_lte_0_3s") is True
                if isinstance(bounded_feedback_summary, dict)
                else False
            ),
            "bounded_motion_stop_observed": (
                bounded_feedback_summary.get("stop_service_success_text") is True
                and ros_readback_summary.get("stop_success_observed") is True
                if isinstance(bounded_feedback_summary, dict) and isinstance(ros_readback_summary, dict)
                else False
            ),
            "t1001_feedback_before_after_observed": (
                bounded_feedback_summary.get("t1001_feedback_before_after_observed") is True
                if isinstance(bounded_feedback_summary, dict)
                else False
            ),
            "t1001_feedback_sample_count": (
                base_feedback_latest_summary.get("completed_sample_count")
                if isinstance(base_feedback_latest_summary, dict)
                else None
            ),
            "t1001_observed_count": (
                base_feedback_latest_summary.get("t1001_observed_count")
                if isinstance(base_feedback_latest_summary, dict)
                else None
            ),
            "readback_summary_present": pc_readback_present,
            "readback_summary": pc_readback_summary,
            "base_feedback_samples_latest_present": base_feedback_latest_present,
            "base_feedback_samples_latest_summary": base_feedback_latest_summary,
            "feedback_request_observed": (
                base_feedback_latest_summary.get("feedback_request_observed") is True
                if isinstance(base_feedback_latest_summary, dict)
                else False
            ),
            "feedback_request_t130_observed": (
                base_feedback_latest_summary.get("feedback_request_t130_observed") is True
                if isinstance(base_feedback_latest_summary, dict)
                else False
            ),
            "odom_readback_sample_present": (
                ros_readback_summary.get("odom_readback_sample_present") is True
                if isinstance(ros_readback_summary, dict)
                else False
            ),
            "odom_readback_frame_id": (
                ros_readback_summary.get("odom_readback_frame_id")
                if isinstance(ros_readback_summary, dict)
                else None
            ),
            "odom_readback_child_frame_id": (
                ros_readback_summary.get("odom_readback_child_frame_id")
                if isinstance(ros_readback_summary, dict)
                else None
            ),
            "imu_sample_present": (
                ros_readback_summary.get("imu_sample_present") is True
                if isinstance(ros_readback_summary, dict)
                else False
            ),
            "imu_frame_id": (
                ros_readback_summary.get("imu_frame_id")
                if isinstance(ros_readback_summary, dict)
                else None
            ),
            "battery_sample_present": (
                ros_readback_summary.get("battery_sample_present") is True
                if isinstance(ros_readback_summary, dict)
                else False
            ),
            "ros_sample_readback_summary": ros_readback_summary,
            "wheel_feedback_diagnostic_context_present": diagnostic_present,
            "wheel_feedback_sweep_all_nonzero_lr_count_zero": (
                diagnostic_summary.get("all_nonzero_lr_count_zero") is True
                if isinstance(diagnostic_summary, dict)
                else False
            ),
            "wheel_feedback_diagnostic_summary": diagnostic_summary,
            "bounded_motion_feedback_ready_not_hil_pass": bounded_motion_ready,
            "manual_hil_gate_current_evidence_material_present": (
                manual_hil_gate_present and status == READY_STATUS
            ),
            "manual_hil_gate_current_evidence_material_status": (
                "manual_hil_gate_current_evidence_material_ready_not_hil_pass"
                if manual_hil_gate_present and status == READY_STATUS
                else "manual_hil_gate_current_evidence_material_blocked_not_hil_pass"
            ),
            "manual_hil_gate_status": (
                manual_hil_gate_summary.get("manual_hil_gate_status")
                if isinstance(manual_hil_gate_summary, dict)
                else None
            ),
            "manual_hil_gate_missing_fields": (
                manual_hil_gate_summary.get("manual_hil_gate_missing_fields")
                if isinstance(manual_hil_gate_summary, dict)
                else []
            ),
            "visible_content_proven_blocks_motion": (
                manual_hil_gate_summary.get("visible_content_proven_blocks_motion") is True
                if isinstance(manual_hil_gate_summary, dict)
                else False
            ),
            "manual_nonzero_policy": (
                manual_hil_gate_summary.get("manual_nonzero_policy")
                if isinstance(manual_hil_gate_summary, dict)
                else None
            ),
            "stop_safety_smoke_forwarded": (
                manual_hil_gate_summary.get("stop_safety_smoke_forwarded") is True
                if isinstance(manual_hil_gate_summary, dict)
                else False
            ),
            "stop_remote_http_status": (
                manual_hil_gate_summary.get("stop_remote_http_status")
                if isinstance(manual_hil_gate_summary, dict)
                else None
            ),
            "manual_nonstop_local_reject_present": (
                manual_hil_gate_summary.get("manual_nonstop_local_reject_present") is True
                if isinstance(manual_hil_gate_summary, dict)
                else False
            ),
            "manual_nonstop_remote_base_manual_called": False,
            "manual_nonstop_failure_reason": (
                manual_hil_gate_summary.get("manual_nonstop_failure_reason")
                if isinstance(manual_hil_gate_summary, dict)
                else None
            ),
            "proxy_remote_base_manual_not_called_by_local_reject": (
                manual_hil_gate_summary.get("proxy_remote_base_manual_not_called_by_local_reject") is True
                if isinstance(manual_hil_gate_summary, dict)
                else False
            ),
            "manual_gate_t1001_observed_count": (
                manual_hil_gate_summary.get("manual_gate_t1001_observed_count")
                if isinstance(manual_hil_gate_summary, dict)
                else None
            ),
            "manual_gate_all_samples_observed_t1001": (
                manual_hil_gate_summary.get("manual_gate_all_samples_observed_t1001") is True
                if isinstance(manual_hil_gate_summary, dict)
                else False
            ),
            "manual_gate_feedback_request_t130_observed": (
                manual_hil_gate_summary.get("manual_gate_feedback_request_t130_observed") is True
                if isinstance(manual_hil_gate_summary, dict)
                else False
            ),
            "operator_structured_report_material_only": (
                manual_hil_gate_summary.get("operator_structured_report_material_only") is True
                if isinstance(manual_hil_gate_summary, dict)
                else False
            ),
            "operator_structured_report_status": (
                manual_hil_gate_summary.get("operator_structured_report_status")
                if isinstance(manual_hil_gate_summary, dict)
                else None
            ),
            "operator_structured_delivery_claim_material_only": (
                manual_hil_gate_summary.get("operator_structured_delivery_claim_material_only") is True
                if isinstance(manual_hil_gate_summary, dict)
                else False
            ),
            "manual_hil_gate_ready_not_hil_pass": (
                manual_hil_gate_present and status == READY_STATUS
            ),
            "manual_hil_gate_current_evidence_summary": manual_hil_gate_summary,
            "same_session_wheel_feedback_material_present": same_session_wheel_feedback_ready,
            "same_session_wheel_feedback_material_status": (
                SAME_SESSION_WHEEL_FEEDBACK_READY_STATUS
                if same_session_wheel_feedback_ready
                else SAME_SESSION_WHEEL_FEEDBACK_BLOCKED_STATUS
            ),
            "same_session_wheel_feedback_lr_nonzero_material_present": (
                same_session_wheel_feedback_ready
                and isinstance(same_session_wheel_feedback_summary, dict)
                and same_session_wheel_feedback_summary.get("latest_nonzero_pair") is not None
            ),
            "same_session_wheel_feedback_latest_nonzero_pair": (
                same_session_wheel_feedback_summary.get("latest_nonzero_pair")
                if isinstance(same_session_wheel_feedback_summary, dict)
                else None
            ),
            "same_session_wheel_feedback_motion_window_nonzero_pair_count": (
                same_session_wheel_feedback_summary.get("nonzero_frame_count")
                if isinstance(same_session_wheel_feedback_summary, dict)
                else None
            ),
            "same_session_wheel_feedback_motion_window_t1001_count": (
                same_session_wheel_feedback_summary.get("frame_count")
                if isinstance(same_session_wheel_feedback_summary, dict)
                else None
            ),
            "same_session_wheel_feedback_feedback_request_t130_observed": (
                same_session_wheel_feedback_summary.get("feedback_request_t130_observed") is True
                if isinstance(same_session_wheel_feedback_summary, dict)
                else False
            ),
            "same_session_wheel_feedback_current_live_rerun": False,
            "same_session_wheel_feedback_summary": same_session_wheel_feedback_summary,
            "same_session_hil_acceptance_status": (
                SAME_SESSION_HIL_ACCEPTANCE_STATUS if same_session_wheel_feedback_ready else None
            ),
            "same_session_hil_acceptance_missing_fields": (
                list(SAME_SESSION_HIL_ACCEPTANCE_MISSING_FIELDS)
                if same_session_wheel_feedback_ready
                else []
            ),
            "same_session_hil_acceptance_ready_not_hil_pass": same_session_wheel_feedback_ready,
            "same_session_pc_command_material_present": same_session_pc_command_ready,
            "same_session_pc_command_material_status": (
                SAME_SESSION_PC_COMMAND_READY_STATUS
                if same_session_pc_command_ready
                else SAME_SESSION_PC_COMMAND_BLOCKED_STATUS
            ),
            "same_session_pc_command_requested_direction": (
                same_session_pc_command_summary.get("requested_direction")
                if isinstance(same_session_pc_command_summary, dict)
                else None
            ),
            "same_session_pc_command_applied_direction": (
                same_session_pc_command_summary.get("applied_direction")
                if isinstance(same_session_pc_command_summary, dict)
                else None
            ),
            "same_session_pc_command_clamped_speed_mps": (
                same_session_pc_command_summary.get("clamped_speed_mps")
                if isinstance(same_session_pc_command_summary, dict)
                else None
            ),
            "same_session_pc_command_clamped_duration_ms": (
                same_session_pc_command_summary.get("clamped_duration_ms")
                if isinstance(same_session_pc_command_summary, dict)
                else None
            ),
            "same_session_pc_command_checklist_confirmed": (
                same_session_pc_command_summary.get("checklist_confirmed") is True
                if isinstance(same_session_pc_command_summary, dict)
                else False
            ),
            "same_session_pc_command_evidence_capture_status": (
                same_session_pc_command_summary.get("evidence_capture_status")
                if isinstance(same_session_pc_command_summary, dict)
                else None
            ),
            "same_session_pc_command_wheel_feedback_lr_nonzero_material_present": (
                same_session_pc_command_ready
                and isinstance(same_session_pc_command_summary, dict)
                and same_session_pc_command_summary.get("wheel_feedback_lr_nonzero_material_present") is True
            ),
            "same_session_pc_command_motion_window_nonzero_frame_count": (
                same_session_pc_command_summary.get("motion_window_nonzero_frame_count")
                if isinstance(same_session_pc_command_summary, dict)
                else None
            ),
            "same_session_pc_command_latest_nonzero_pair": (
                same_session_pc_command_summary.get("latest_nonzero_pair")
                if isinstance(same_session_pc_command_summary, dict)
                else None
            ),
            "same_session_pc_command_feedback_during_motion_attempted": (
                same_session_pc_command_summary.get("feedback_during_motion_attempted") is True
                if isinstance(same_session_pc_command_summary, dict)
                else False
            ),
            "same_session_pc_command_feedback_after_stop_attempted": (
                same_session_pc_command_summary.get("feedback_after_stop_attempted") is True
                if isinstance(same_session_pc_command_summary, dict)
                else False
            ),
            "same_session_pc_command_manual_command_executed": (
                same_session_pc_command_summary.get("manual_command_executed") is True
                if isinstance(same_session_pc_command_summary, dict)
                else False
            ),
            "same_session_pc_command_auto_stop_executed": (
                same_session_pc_command_summary.get("auto_stop_executed") is True
                if isinstance(same_session_pc_command_summary, dict)
                else False
            ),
            "same_session_pc_command_after_jog_t1001_observed": (
                same_session_pc_command_summary.get("after_jog_t1001_observed") is True
                if isinstance(same_session_pc_command_summary, dict)
                else False
            ),
            "same_session_pc_command_after_jog_feedback_source": (
                same_session_pc_command_summary.get("after_jog_feedback_source")
                if isinstance(same_session_pc_command_summary, dict)
                else None
            ),
            "same_session_pc_command_after_jog_latest_pair": (
                same_session_pc_command_summary.get("after_jog_latest_pair")
                if isinstance(same_session_pc_command_summary, dict)
                else None
            ),
            "same_session_pc_command_after_jog_wheel_feedback_lr_zero_readback": (
                same_session_pc_command_summary.get("after_jog_wheel_feedback_lr_zero_readback") is True
                if isinstance(same_session_pc_command_summary, dict)
                else False
            ),
            "same_session_pc_command_after_jog_feedback_samples_freshness_status": (
                same_session_pc_command_summary.get("after_jog_feedback_samples_freshness_status")
                if isinstance(same_session_pc_command_summary, dict)
                else None
            ),
            "same_session_pc_command_after_jog_readback_sends_commands": (
                same_session_pc_command_summary.get("after_jog_readback_sends_commands") is True
                if isinstance(same_session_pc_command_summary, dict)
                else False
            ),
            "same_session_pc_command_readback_summary": (
                {
                    "after_jog_t1001_observed": same_session_pc_command_summary.get("after_jog_t1001_observed"),
                    "after_jog_feedback_source": same_session_pc_command_summary.get("after_jog_feedback_source"),
                    "after_jog_latest_pair": same_session_pc_command_summary.get("after_jog_latest_pair"),
                    "after_jog_wheel_feedback_lr_zero_readback": (
                        same_session_pc_command_summary.get("after_jog_wheel_feedback_lr_zero_readback")
                    ),
                    "after_jog_feedback_samples_freshness_status": (
                        same_session_pc_command_summary.get("after_jog_feedback_samples_freshness_status")
                    ),
                    "after_jog_readback_sends_commands": (
                        same_session_pc_command_summary.get("after_jog_readback_sends_commands")
                    ),
                }
                if isinstance(same_session_pc_command_summary, dict)
                else None
            ),
            "same_session_pc_command_summary": same_session_pc_command_summary,
        }
    )
    _ensure_summary_is_safe(summary)
    return summary


def build_motion_map_hil_material_bundle_from_files(paths: dict[str, Path]) -> dict[str, Any]:
    """从文件读取 bundle 输入；任何读失败都 fail-closed。"""
    source_refs = _collect_source_refs(paths)
    clean_baseline_latest = None
    clean_baseline_retry_summary = None
    clean_baseline_load_reasons: list[str] = []
    wheel_feedback_diagnostic_sweep = None
    wheel_feedback_diagnostic_load_reasons: list[str] = []
    try:
        first_jog = _load_json_object(paths["first_jog_json"])
        feedback_samples = _load_json_object(paths["feedback_samples_json"])
        scan_delta = _load_json_object(paths["scan_delta_json"])
        operator_report = _load_json_object(paths["operator_report_json"])
        field_map_yaml = _load_map_yaml(paths["field_map_yaml"])
        field_pixel_review = _load_json_object(paths["field_pixel_review_json"])
        manual_map_yaml = _load_map_yaml(paths["manual_map_yaml"])
        manual_pixel_review = _load_json_object(paths["manual_pixel_review_json"])
        free_cell_map_start = _load_json_object(paths["free_cell_map_start_json"])
        free_cell_map_list = _load_json_object(paths["free_cell_map_list_json"])
        free_cell_map_yaml = _load_map_yaml(paths["free_cell_map_yaml"])
        free_cell_pixel_review = _load_json_object(paths["free_cell_pixel_review_json"])
        free_cell_pc_summary = _load_json_object(paths["free_cell_pc_summary_json"])
        bounded_motion_feedback_summary = _load_json_object(paths["bounded_motion_feedback_summary_json"])
        bounded_motion_pulse_and_stop_log = paths["bounded_motion_pulse_and_stop_log"].read_text(
            encoding="utf-8"
        )
        bounded_motion_odom_after_motion_text = paths["bounded_motion_odom_after_motion_txt"].read_text(
            encoding="utf-8"
        )
        bounded_motion_imu_once_text = paths["bounded_motion_imu_once_txt"].read_text(
            encoding="utf-8"
        )
        pc_real_robot_api_readback_summary = _load_json_object(paths["pc_real_robot_api_readback_summary_json"])
        base_feedback_samples_latest = _load_json_object(paths["base_feedback_samples_latest_json"])
        manual_hil_gate_decision = _load_json_object(paths["manual_hil_gate_decision_json"])
        manual_hil_gate_stop_safety_smoke = _load_json_object(paths["manual_hil_gate_stop_safety_json"])
        manual_hil_gate_manual_reject = _load_json_object(paths["manual_hil_gate_manual_reject_json"])
        manual_hil_gate_proxy_smoke = _load_json_object(paths["manual_hil_gate_proxy_smoke_json"])
        manual_hil_gate_feedback_samples_latest = _load_json_object(
            paths["manual_hil_gate_feedback_samples_latest_json"]
        )
        manual_hil_gate_operator_report_latest = _load_json_object(
            paths["manual_hil_gate_operator_report_latest_json"]
        )
        manual_hil_gate_robot_control_summary = _load_json_object(
            paths["manual_hil_gate_robot_control_summary_json"]
        )
        same_session_wheel_feedback = _load_json_object(paths["same_session_wheel_feedback_json"])
        same_session_pc_first_jog = _load_json_object(paths["same_session_pc_first_jog_json"])
        same_session_pc_after_jog_base_status = _load_json_object(
            paths["same_session_pc_after_jog_base_status_json"]
        )
        # 这里显式探测 PGM 文件存在与 header，可把 map 配对缺口尽早转成 blocked。
        _read_pgm_header(paths["field_map_pgm"])
        _read_pgm_header(paths["manual_map_pgm"])
        _read_pgm_header(paths["free_cell_map_pgm"])
    except (OSError, ValueError, json.JSONDecodeError):
        return _blocked(["artifact_bundle_unreadable_or_invalid"], source_refs)
    try:
        clean_baseline_latest_path = paths.get("clean_baseline_nav2_path_latest_json")
        if clean_baseline_latest_path is not None and clean_baseline_latest_path.exists():
            clean_baseline_latest = _load_json_object(clean_baseline_latest_path)
        else:
            clean_baseline_load_reasons.append("cross_run_clean_baseline_latest_unreadable_or_missing")
    except (OSError, ValueError, json.JSONDecodeError):
        clean_baseline_load_reasons.append("cross_run_clean_baseline_latest_unreadable_or_invalid")
    try:
        clean_baseline_retry_path = paths.get("clean_baseline_nav2_path_retry_summary_json")
        if clean_baseline_retry_path is not None and clean_baseline_retry_path.exists():
            clean_baseline_retry_summary = _load_json_object(clean_baseline_retry_path)
        else:
            clean_baseline_load_reasons.append("cross_run_clean_baseline_retry_unreadable_or_missing")
    except (OSError, ValueError, json.JSONDecodeError):
        clean_baseline_load_reasons.append("cross_run_clean_baseline_retry_unreadable_or_invalid")
    try:
        diagnostic_path = paths.get("wheel_feedback_diagnostic_sweep_summary_json")
        if diagnostic_path is not None and diagnostic_path.exists():
            wheel_feedback_diagnostic_sweep = _load_json_object(diagnostic_path)
        else:
            wheel_feedback_diagnostic_load_reasons.append("wheel_feedback_diagnostic_sweep_missing_or_disabled")
    except (OSError, ValueError, json.JSONDecodeError):
        wheel_feedback_diagnostic_load_reasons.append("wheel_feedback_diagnostic_sweep_unreadable_or_invalid")
    return build_motion_map_hil_material_bundle(
        first_jog,
        feedback_samples,
        scan_delta,
        operator_report,
        field_map_yaml,
        paths["field_map_pgm"],
        field_pixel_review,
        manual_map_yaml,
        paths["manual_map_pgm"],
        manual_pixel_review,
        source_refs,
        free_cell_map_start=free_cell_map_start,
        free_cell_map_list=free_cell_map_list,
        free_cell_map_yaml=free_cell_map_yaml,
        free_cell_map_pgm_path=paths["free_cell_map_pgm"],
        free_cell_pixel_review=free_cell_pixel_review,
        free_cell_pc_summary=free_cell_pc_summary,
        clean_baseline_nav2_latest=clean_baseline_latest,
        clean_baseline_nav2_retry_summary=clean_baseline_retry_summary,
        clean_baseline_comparator_load_reasons=clean_baseline_load_reasons,
        bounded_motion_feedback_summary=bounded_motion_feedback_summary,
        bounded_motion_pulse_and_stop_log=bounded_motion_pulse_and_stop_log,
        bounded_motion_odom_after_motion_text=bounded_motion_odom_after_motion_text,
        bounded_motion_imu_once_text=bounded_motion_imu_once_text,
        pc_real_robot_api_readback_summary=pc_real_robot_api_readback_summary,
        base_feedback_samples_latest=base_feedback_samples_latest,
        wheel_feedback_diagnostic_sweep_summary=wheel_feedback_diagnostic_sweep,
        wheel_feedback_diagnostic_load_reasons=wheel_feedback_diagnostic_load_reasons,
        manual_hil_gate_decision=manual_hil_gate_decision,
        manual_hil_gate_stop_safety_smoke=manual_hil_gate_stop_safety_smoke,
        manual_hil_gate_manual_reject=manual_hil_gate_manual_reject,
        manual_hil_gate_proxy_smoke=manual_hil_gate_proxy_smoke,
        manual_hil_gate_feedback_samples_latest=manual_hil_gate_feedback_samples_latest,
        manual_hil_gate_operator_report_latest=manual_hil_gate_operator_report_latest,
        manual_hil_gate_robot_control_summary=manual_hil_gate_robot_control_summary,
        same_session_wheel_feedback=same_session_wheel_feedback,
        same_session_pc_first_jog=same_session_pc_first_jog,
        same_session_pc_after_jog_base_status=same_session_pc_after_jog_base_status,
    )


def _resolve_paths(args: argparse.Namespace) -> dict[str, Path]:
    """CLI 默认消费历史 inputs，也允许逐项覆盖做负向 smoke。"""
    resolved: dict[str, Path] = {}
    for name, default_path in DEFAULT_PATHS.items():
        value = getattr(args, name)
        resolved[name] = Path(value) if value is not None else Path(default_path)
    return resolved


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：默认读取历史 artifacts，打印安全 JSON bundle。"""
    parser = argparse.ArgumentParser(
        description="Build a sanitized WAVE ROVER motion-map HIL material bundle."
    )
    for name, default_path in DEFAULT_PATHS.items():
        parser.add_argument(f"--{name.replace('_', '-')}", dest=name, default=str(default_path))
    parser.add_argument("--output", help="Optional output file for the sanitized summary.")
    args = parser.parse_args(argv)

    summary = build_motion_map_hil_material_bundle_from_files(_resolve_paths(args))
    payload = json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
        print(Path(args.output).name)
    else:
        print(payload, end="")
    return 0 if summary["status"] == READY_STATUS else 4


if __name__ == "__main__":
    raise SystemExit(main())
