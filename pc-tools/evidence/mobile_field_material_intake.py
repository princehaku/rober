#!/usr/bin/env python3
"""生成或校验 mobile field material intake summary。

该 gate 只读取本地 JSON 材料，用同一个 safe evidence_ref 检查现场回填是否
足够进入人工复核。它不访问 ROS graph、Nav2 runtime、serial/UART、真实手机、
真实电梯、外部云、OSS/CDN、DB/queue 或 4G。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema 名称是 mobile/diagnostics/sprint closeout 之间的稳定锚点。
SCHEMA = "trashbot.mobile_field_material_intake.v1"
SUMMARY_SCHEMA = "trashbot.mobile_field_material_intake_summary.v1"
COPY_SCHEMA = "trashbot.mobile_field_material_intake_copy.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_mobile_field_material_intake_gate"

# intake 必须接在上一轮手机现场前检查之后，避免绕过 phone-safe precheck。
PRECHECK_SCHEMAS = {
    "trashbot.mobile_route_elevator_field_device_precheck.v1",
    "trashbot.mobile_route_elevator_field_device_precheck_summary.v1",
}
PRECHECK_BOUNDARY = "software_proof_docker_mobile_route_elevator_field_device_precheck_gate"

# 这些材料代表现场前/后回填的最小闭环；缺任何一个都不能进入 ready。
MATERIAL_INPUTS = (
    ("device_pwa_observation", "device_pwa_observation.json"),
    ("route_elevator_field_materials", "route_elevator_field_materials.json"),
    ("nav2_fixed_route_runtime_log", "nav2_fixed_route_runtime_log.json"),
    ("task_record", "task_record.json"),
    ("completion_signal", "completion_signal.json"),
    ("dropoff_cancel_material_status", "dropoff_cancel_material_status.json"),
)

# 输出 checklist 明确 route/elevator、Nav2、任务记录和投放/取消材料都需同 ref。
REQUIRED_ROUTE_ELEVATOR_FIELD_MATERIALS = (
    "route_status.json",
    "door_state.json",
    "target_floor_confirmation.json",
    "human_assistance_operator_note.md",
    "diagnostics_mobile_safe_summary.json",
)
DEVICE_PWA_OBSERVATION_CHECKLIST = (
    "real_device_browser_loaded_current_mobile_web",
    "real_device_viewport_and_touch_targets_observed",
    "pwa_install_prompt_observed_or_not_available_recorded",
    "pwa_install_user_choice_recorded",
    "mobile_field_material_intake_panel_visible",
    "copy_export_whitelist_checked",
    "primary_actions_remain_disabled",
)

# not_proven 是防误读字段，不随材料 present 而自动变成现场成功。
NOT_PROVEN = (
    "real_phone_device_or_browser",
    "real_pwa_install_prompt_user_choice",
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_run",
    "real_fixed_route_completion",
    "real_task_record_acceptance",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "real_hil_pass",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# phone-safe copy 不能带控制、凭证、硬件、路径、trace 或完整 artifact 内容。
FORBIDDEN_COPY = (
    "Authorization",
    "OSS_ACCESS_KEY",
    "OSS_SECRET",
    "access_key",
    "secret",
    "token",
    "password",
    "postgres://",
    "postgresql://",
    "mysql://",
    "redis://",
    "amqp://",
    "mongodb://",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "serial",
    "UART",
    "baudrate",
    "baud_rate",
    "WAVE ROVER",
    "Traceback",
    "checksum",
    "complete artifact",
    "raw robot response",
)

# 占位符会让现场材料看似 present 但不可复核，因此一律 fail closed。
PLACEHOLDER_PATTERNS = (
    re.compile(r"(?i)<[^>]*(todo|placeholder|same_evidence_ref|fill|tbd)[^>]*>"),
    re.compile(r"(?i)\b(todo|tbd|placeholder|replace_me|sample_only|example_only)\b"),
)

# true 旗标和完成文案都可能被误读为真实送达成功，必须在 gate 层阻断。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\broute/elevator\s+field\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(completed|complete|success|succeeded)\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
)

# 脱敏先于禁词检查，避免现场笔记污染后续 mobile/export 摘要。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_RATE]"),
    (re.compile(r"(?i)\bserial\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bUART\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)WAVE\s+ROVER"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 让不同 PC 生成的 summary 容易按时间排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本进入输出前先脱敏，后续再做 fail-closed 检查。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 本地完整路径不进入 phone-safe 摘要，只保留 basename 作为线索。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏，防止新增上游字段绕过局部 helper。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _encoded(value: Any) -> str:
    # 安全检查覆盖 key/value；不可编码对象退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都返回 reason，不抛未处理异常。
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


def _bool_at_path(value: Any, path: tuple[str, ...]) -> bool:
    # 只拦截显式 true；false 是本 gate 的固定安全字段。
    current = value
    for key in path:
        if not isinstance(current, dict):
            return False
        current = current.get(key)
    return current is True


def _has_forbidden_copy(value: Any) -> bool:
    # 命中禁词时 blocked，避免把敏感细节传给手机导出包。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_placeholder(value: Any) -> bool:
    # 占位材料不能作为现场回填证据，因为无法追溯真实 run。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in PLACEHOLDER_PATTERNS)


def _has_success_claim(value: Any) -> bool:
    # 完成文案、true 旗标和 HIL claim 都会把 software proof 误读为现场成功。
    encoded = _encoded(value)
    if any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS):
        return True
    return any(
        _bool_at_path(value, path)
        for path in (
            ("delivery_success",),
            ("primary_actions_enabled",),
            ("real_device_observed",),
            ("pwa_install_prompt_observed",),
            ("route_elevator_field_pass",),
            ("nav2_fixed_route_completed",),
            ("dropoff_completion",),
            ("cancel_completion",),
            ("hil_pass",),
        )
    )


def _first_text(*values: Any, default: str = "") -> str:
    # evidence_ref 可能在顶层、summary、manifest 或 phone-safe 摘要中。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只消费 object summary；其它形态按空对象处理，避免复制 raw artifact。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _extract_evidence_ref(payload: dict[str, Any]) -> str:
    # 兼容 route/task/mobile 多种 summary 形态，但输出只保留 safe ref。
    mobile = _dict(payload, "mobile_copy_summary")
    phone = _dict(payload, "phone_safe_summary")
    manifest = _dict(payload, "field_run_manifest")
    return _safe_ref(
        _first_text(
            payload.get("evidence_ref"),
            mobile.get("evidence_ref"),
            phone.get("evidence_ref"),
            manifest.get("evidence_ref"),
        )
    )


def _precheck_summary(payload: dict[str, Any], error: str) -> dict[str, Any]:
    # precheck 只保留 contract/ref/verdict，不复制完整上游 artifact。
    if error:
        return {
            "present": False,
            "schema_status": "missing_or_unreadable",
            "boundary_status": "not_checked",
            "evidence_ref": "",
            "precheck_verdict": "missing",
            "error": error,
        }
    schema = _safe_text(payload.get("schema")).strip()
    boundary = _safe_text(payload.get("evidence_boundary")).strip()
    source = _safe_text(payload.get("source") or SOURCE).strip()
    return {
        "present": True,
        "schema": schema,
        "schema_status": "supported" if schema in PRECHECK_SCHEMAS else "unsupported",
        "evidence_boundary": boundary,
        "boundary_status": "supported" if boundary == PRECHECK_BOUNDARY else "unsupported",
        "source": source or SOURCE,
        "source_status": "supported" if source in ("", SOURCE) else "unsupported",
        "evidence_ref": _extract_evidence_ref(payload),
        "precheck_verdict": _safe_text(_first_text(payload.get("precheck_verdict"), payload.get("status"))),
        "delivery_success": bool(payload.get("delivery_success", False)),
        "primary_actions_enabled": bool(payload.get("primary_actions_enabled", False)),
    }


def _material_summary(label: str, payload: dict[str, Any], error: str, expected_ref: str) -> dict[str, Any]:
    # 每份材料独立给出状态，便于现场补采而不是只看到总失败。
    ref = _extract_evidence_ref(payload) if payload else ""
    missing_or_blocked: list[str] = []
    status = "present_not_proven"
    if error:
        status = "missing_or_unreadable"
        missing_or_blocked.append(error)
    elif not ref:
        status = "blocked_missing_evidence_ref"
        missing_or_blocked.append(f"{label}:evidence_ref")
    elif expected_ref and ref != expected_ref:
        status = "blocked_evidence_ref_mismatch"
        missing_or_blocked.append(f"{label}:evidence_ref")
    elif _has_placeholder(payload):
        status = "blocked_placeholder"
        missing_or_blocked.append(f"{label}:placeholder")
    elif _has_forbidden_copy(payload):
        status = "blocked_unsafe_copy"
        missing_or_blocked.append(f"{label}:unsafe_copy")
    elif _has_success_claim(payload):
        status = "blocked_success_or_control_claim"
        missing_or_blocked.append(f"{label}:success_or_control_claim")

    return {
        "name": label,
        "required": True,
        "present": not bool(error),
        "same_evidence_ref_required": True,
        "evidence_ref": ref,
        "status": status,
        "missing_or_blocked": missing_or_blocked,
    }


def _copy_summary(evidence_ref: str, verdict: str, material_statuses: list[dict[str, Any]]) -> dict[str, Any]:
    # copy/export 只包含白名单摘要，不包含 raw artifact、本机路径或现场完整材料。
    missing = [item["name"] for item in material_statuses if item.get("status") != "present_not_proven"]
    return {
        "schema": COPY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "missing_or_blocked_materials": missing,
        "device_pwa_observation_checklist": list(DEVICE_PWA_OBSERVATION_CHECKLIST),
        "required_route_elevator_field_materials": list(REQUIRED_ROUTE_ELEVATOR_FIELD_MATERIALS),
        "nav2_fixed_route_runtime_log_required": True,
        "task_record_required": True,
        "completion_signal_required": True,
        "dropoff_cancel_material_status_required": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "not_proven": list(NOT_PROVEN),
        "safe_copy_note": "software_proof only; route/elevator、真实手机、Nav2/fixed-route 和 delivery 仍不证明",
    }


def _decide_verdict(
    precheck: dict[str, Any],
    material_statuses: list[dict[str, Any]],
    precheck_payload: dict[str, Any],
    target_ref: str,
) -> tuple[str, list[str], str]:
    # verdict 保守分层：precheck 错、材料缺、placeholder、mismatch、unsafe、success claim 都 blocked。
    missing: list[str] = []
    if not precheck.get("present"):
        return "blocked_missing_inputs", ["mobile_route_elevator_field_device_precheck"], "missing_precheck"
    if precheck.get("schema_status") != "supported":
        missing.append("mobile_route_elevator_field_device_precheck:unsupported_schema")
    if precheck.get("boundary_status") != "supported":
        missing.append("mobile_route_elevator_field_device_precheck:unsupported_boundary")
    if precheck.get("source_status") != "supported":
        missing.append("mobile_route_elevator_field_device_precheck:unsupported_source")
    if not precheck.get("evidence_ref"):
        missing.append("mobile_route_elevator_field_device_precheck:evidence_ref")
    if target_ref and precheck.get("evidence_ref") and precheck.get("evidence_ref") != target_ref:
        missing.append("mobile_route_elevator_field_device_precheck:evidence_ref")
    if _has_forbidden_copy(precheck_payload):
        missing.append("mobile_route_elevator_field_device_precheck:unsafe_copy")
    if _has_success_claim(precheck_payload) or precheck.get("delivery_success") or precheck.get("primary_actions_enabled"):
        missing.append("mobile_route_elevator_field_device_precheck:success_or_control_claim")
    if missing:
        return "blocked_invalid_precheck", missing, "precheck_contract_or_safety_failed"

    for item in material_statuses:
        missing.extend(item.get("missing_or_blocked", []))
    if missing:
        return "blocked_invalid_or_missing_field_materials", missing, "field_materials_missing_or_failed"

    return "ready_for_mobile_field_material_review_not_proven", [], "software_material_intake_ready_not_proven"


def build_intake(
    precheck_json: str = "",
    evidence_ref: str = "",
    material_paths: dict[str, str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """从 precheck 与现场材料生成 mobile_field_material_intake artifact/summary。"""

    precheck_payload, precheck_error = _load_json(precheck_json, "precheck")
    precheck = _precheck_summary(precheck_payload, precheck_error)
    target_ref = _safe_ref(evidence_ref or precheck.get("evidence_ref"))
    material_paths = material_paths or {}

    material_statuses: list[dict[str, Any]] = []
    for label, _default_name in MATERIAL_INPUTS:
        payload, error = _load_json(material_paths.get(label, ""), label)
        material_statuses.append(_material_summary(label, payload, error, target_ref))

    verdict, missing, reason = _decide_verdict(precheck, material_statuses, precheck_payload, target_ref)
    safe_ref = target_ref or precheck.get("evidence_ref") or "<same_evidence_ref>"
    generated_at = _utc_now()
    same_ref_ready = not missing and bool(target_ref)

    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": generated_at,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "intake_verdict": verdict,
        "intake_reason": reason,
        "evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": "matched_same_evidence_ref" if same_ref_ready else "not_proven",
        "precheck_summary": precheck,
        "material_statuses": material_statuses,
        "required_route_elevator_field_materials": list(REQUIRED_ROUTE_ELEVATOR_FIELD_MATERIALS),
        "device_pwa_observation_checklist": list(DEVICE_PWA_OBSERVATION_CHECKLIST),
        "mobile_copy_summary": _copy_summary(safe_ref, verdict, material_statuses),
        "missing_or_blocked": missing,
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "field_material_intake_only_not_delivery_success",
        "real_device_observed": False,
        "pwa_install_prompt_observed": False,
        "route_elevator_field_pass": False,
        "nav2_fixed_route_completed": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }

    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": generated_at,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": verdict,
        "intake_verdict": verdict,
        "evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": artifact["same_evidence_ref_status"],
        "material_statuses": material_statuses,
        "required_route_elevator_field_material_names": list(REQUIRED_ROUTE_ELEVATOR_FIELD_MATERIALS),
        "device_pwa_observation_checklist_names": list(DEVICE_PWA_OBSERVATION_CHECKLIST),
        "mobile_copy_summary": artifact["mobile_copy_summary"],
        "missing_or_blocked": missing,
        "not_proven": list(NOT_PROVEN),
        "real_device_observed": False,
        "pwa_install_prompt_observed": False,
        "route_elevator_field_pass": False,
        "nav2_fixed_route_completed": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return _safe_value(artifact), _safe_value(summary), 0 if verdict.startswith("ready") else 2


def validate_intake(intake_json: str, evidence_ref: str = "") -> tuple[dict[str, Any], dict[str, Any], int]:
    """校验已有 intake summary/artifact 是否仍保持 software proof/not_proven 边界。"""

    payload, error = _load_json(intake_json, "intake")
    missing: list[str] = []
    if error:
        verdict = "blocked_missing_inputs"
        reason = error
        safe_ref = _safe_ref(evidence_ref) or "<same_evidence_ref>"
    else:
        schema = _safe_text(payload.get("schema")).strip()
        boundary = _safe_text(payload.get("evidence_boundary")).strip()
        safe_ref = _safe_ref(evidence_ref or payload.get("evidence_ref")) or "<same_evidence_ref>"
        if schema not in {SCHEMA, SUMMARY_SCHEMA}:
            missing.append("intake:unsupported_schema")
        if boundary != EVIDENCE_BOUNDARY:
            missing.append("intake:unsupported_boundary")
        if evidence_ref and _safe_ref(payload.get("evidence_ref")) != safe_ref:
            missing.append("intake:evidence_ref")
        if _has_placeholder(payload):
            missing.append("intake:placeholder")
        if _has_forbidden_copy(payload):
            missing.append("intake:unsafe_copy")
        if _has_success_claim(payload):
            missing.append("intake:success_or_control_claim")
        verdict = "validated_mobile_field_material_intake_not_proven" if not missing else "blocked_invalid_intake"
        reason = "software_material_intake_validated_not_proven" if not missing else "intake_contract_or_safety_failed"

    generated_at = _utc_now()
    material_statuses = payload.get("material_statuses", []) if not error and isinstance(payload.get("material_statuses"), list) else []
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": generated_at,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "intake_verdict": verdict,
        "intake_reason": reason,
        "evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": "matched_same_evidence_ref" if verdict.startswith("validated") else "not_proven",
        "material_statuses": material_statuses,
        "mobile_copy_summary": _copy_summary(safe_ref, verdict, material_statuses if isinstance(material_statuses, list) else []),
        "missing_or_blocked": missing or ([error] if error else []),
        "not_proven": list(NOT_PROVEN),
        "real_device_observed": False,
        "pwa_install_prompt_observed": False,
        "route_elevator_field_pass": False,
        "nav2_fixed_route_completed": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": generated_at,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": verdict,
        "intake_verdict": verdict,
        "evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": artifact["same_evidence_ref_status"],
        "material_statuses": material_statuses,
        "missing_or_blocked": artifact["missing_or_blocked"],
        "not_proven": list(NOT_PROVEN),
        "real_device_observed": False,
        "pwa_install_prompt_observed": False,
        "route_elevator_field_pass": False,
        "nav2_fixed_route_completed": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return _safe_value(artifact), _safe_value(summary), 0 if verdict.startswith("validated") else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # CLI 输出目录不存在时自动创建，便于 sprint gate 一条命令落盘。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate or validate mobile_field_material_intake software-proof summary."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--precheck-json", default="", help="mobile route/elevator field-device precheck JSON.")
    mode.add_argument("--intake-json", default="", help="Existing mobile_field_material_intake summary/artifact JSON.")
    parser.add_argument("--device-pwa-observation-json", default="", help="Real device/PWA observation checklist JSON.")
    parser.add_argument("--route-elevator-field-materials-json", default="", help="Route/elevator field materials status JSON.")
    parser.add_argument("--nav2-fixed-route-runtime-log-json", default="", help="Nav2/fixed-route runtime log JSON.")
    parser.add_argument("--task-record-json", default="", help="Task record JSON for the same evidence_ref.")
    parser.add_argument("--completion-signal-json", default="", help="Completion signal JSON for the same evidence_ref.")
    parser.add_argument("--dropoff-cancel-material-status-json", default="", help="Dropoff/cancel material status JSON.")
    parser.add_argument("--evidence-ref", default="", help="Expected same evidence_ref for this material intake.")
    parser.add_argument("--output", default="", help="Write full intake artifact JSON to this path.")
    parser.add_argument("--summary-output", default="", help="Write summary JSON to this path.")
    parser.add_argument("--once-json", action="store_true", help="Print summary JSON to stdout.")
    args = parser.parse_args(argv)

    if args.intake_json:
        artifact, summary, exit_code = validate_intake(args.intake_json, args.evidence_ref)
    else:
        material_paths = {
            "device_pwa_observation": args.device_pwa_observation_json,
            "route_elevator_field_materials": args.route_elevator_field_materials_json,
            "nav2_fixed_route_runtime_log": args.nav2_fixed_route_runtime_log_json,
            "task_record": args.task_record_json,
            "completion_signal": args.completion_signal_json,
            "dropoff_cancel_material_status": args.dropoff_cancel_material_status_json,
        }
        artifact, summary, exit_code = build_intake(args.precheck_json, args.evidence_ref, material_paths)

    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
