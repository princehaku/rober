#!/usr/bin/env python3
"""生成或校验 route+elevator+device 现场前检查 summary。

该 gate 只读取本地 JSON summary/artifact，把 route/elevator handoff 与真实设备
观察清单整理成 phone-safe precheck。它不访问 ROS graph、Nav2 runtime、
serial/UART、真实电梯、真实手机、外部云、OSS/CDN、DB/queue 或 4G。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema/boundary 是 mobile、Robot diagnostics 和 sprint closeout 的稳定锚点。
SCHEMA = "trashbot.mobile_route_elevator_field_device_precheck.v1"
SUMMARY_SCHEMA = "trashbot.mobile_route_elevator_field_device_precheck_summary.v1"
COPY_SCHEMA = "trashbot.mobile_route_elevator_field_device_precheck_copy.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_mobile_route_elevator_field_device_precheck_gate"

# 当前 precheck 只接受上一轮 route/elevator field-session handoff 输出。
HANDOFF_SCHEMAS = {
    "trashbot.route_elevator_field_session_handoff.v1",
    "trashbot.route_elevator_field_session_handoff_summary.v1",
}
HANDOFF_BOUNDARY = "software_proof_docker_route_elevator_field_session_handoff_gate"

# 现场 route/elevator 材料必须同 evidence_ref 回填；这里仅生成检查清单。
REQUIRED_ROUTE_ELEVATOR_MATERIALS = (
    "nav2_fixed_route_runtime_log.json",
    "route_status.json",
    "route_completion_signal.json",
    "task_record.json",
    "door_state.json",
    "target_floor_confirmation.json",
    "human_assistance_operator_note.md",
    "dropoff_completion.json_or_cancel_completion.json",
    "delivery_result.json",
    "diagnostics_mobile_safe_summary.json",
)

# 真实设备/PWA 观察项需要现场人员回填；默认全部 not observed。
DEVICE_PWA_OBSERVATION_CHECKLIST = (
    "real_device_browser_loaded_current_mobile_web",
    "real_device_viewport_and_touch_targets_observed",
    "pwa_install_prompt_observed_or_not_available_recorded",
    "pwa_install_user_choice_recorded",
    "route_elevator_precheck_panel_visible",
    "copy_export_whitelist_checked",
    "primary_actions_remain_disabled",
)

# not_proven 覆盖手机、路线、电梯、完成信号、HIL 和 O5 外部材料。
NOT_PROVEN = (
    "real_phone_device_or_browser",
    "real_pwa_install_prompt_user_choice",
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_record",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "real_hil_pass",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# phone-safe copy 不能带凭证、控制 topic、串口/硬件细节、路径或完整 artifact。
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

# 先做脱敏，再做禁词检测，避免输入中的现场笔记污染手机导出包。
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

# false 布尔字段允许出现；自由文本完成声明或 true 旗标必须 fail closed。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\broute/elevator\s+field\s+pass(ed)?\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(completed|complete|success|succeeded)\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
)


def _utc_now() -> str:
    # UTC 时间便于不同 PC 主机生成的 summary 稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本进入输出前先脱敏，后续再做白名单检查。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 本机完整路径不能进 phone copy，只保留 basename 作为 run 线索。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏避免新增上游字段绕过局部 helper。
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


def _has_forbidden_copy(value: Any) -> bool:
    # 命中禁词时直接 blocked，避免把敏感细节继续传给 mobile/export。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_success_claim(value: Any) -> bool:
    # true 旗标和完成文案都会把软件 precheck 误读为现场成功，必须拦截。
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
            ("dropoff_completion",),
            ("cancel_completion",),
            ("hil_pass",),
        )
    )


def _bool_at_path(value: Any, path: tuple[str, ...]) -> bool:
    # 只拦截显式 true；false 是本 gate 的固定安全字段。
    current = value
    for key in path:
        if not isinstance(current, dict):
            return False
        current = current.get(key)
    return current is True


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只消费 object summary；其它形态按空对象处理，避免复制 raw artifact。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # evidence_ref/status 可能在顶层或嵌套 summary；取第一个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都返回 blocked reason，不抛未处理异常。
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


def _extract_evidence_ref(payload: dict[str, Any]) -> str:
    # handoff summary 可能把 ref 放在 mobile/diagnostics 摘要或 manifest 中。
    mobile = _dict(payload, "mobile_readonly_summary")
    diagnostics = _dict(payload, "robot_diagnostics_summary")
    manifest = _dict(payload, "field_session_manifest")
    return _safe_ref(
        _first_text(
            payload.get("evidence_ref"),
            mobile.get("evidence_ref"),
            diagnostics.get("evidence_ref"),
            manifest.get("evidence_ref"),
        )
    )


def _handoff_summary(payload: dict[str, Any], error: str) -> dict[str, Any]:
    # source summary 只保留 contract/ref/verdict，不复制完整上游 artifact。
    if error:
        return {
            "present": False,
            "schema_status": "missing_or_unreadable",
            "boundary_status": "not_checked",
            "evidence_ref": "",
            "handoff_verdict": "missing",
            "error": error,
        }

    schema = _safe_text(payload.get("schema")).strip()
    boundary = _safe_text(payload.get("evidence_boundary")).strip()
    source = _safe_text(payload.get("source") or SOURCE).strip()
    schema_status = "supported" if schema in HANDOFF_SCHEMAS else "unsupported"
    boundary_status = "supported" if boundary == HANDOFF_BOUNDARY else "unsupported"
    source_status = "supported" if source in ("", SOURCE) else "unsupported"
    mobile = _dict(payload, "mobile_readonly_summary")

    return {
        "present": True,
        "schema": schema,
        "schema_status": schema_status,
        "evidence_boundary": boundary,
        "boundary_status": boundary_status,
        "source": source or SOURCE,
        "source_status": source_status,
        "evidence_ref": _extract_evidence_ref(payload),
        "handoff_verdict": _safe_text(
            _first_text(payload.get("handoff_verdict"), mobile.get("handoff_verdict"), payload.get("status"))
        ),
        "delivery_success": bool(payload.get("delivery_success", False) or mobile.get("delivery_success", False)),
        "primary_actions_enabled": bool(
            payload.get("primary_actions_enabled", False) or mobile.get("primary_actions_enabled", False)
        ),
    }


def _material_checklist() -> list[dict[str, Any]]:
    # 每个材料都标记 required/pending，避免 checklist 被误解为已采集。
    return [
        {
            "name": name,
            "required": True,
            "same_evidence_ref_required": True,
            "status": "pending_field_material_not_proven",
        }
        for name in REQUIRED_ROUTE_ELEVATOR_MATERIALS
    ]


def _device_checklist() -> list[dict[str, Any]]:
    # 真实设备观察默认 not_observed，后续必须由现场材料显式回填。
    return [
        {
            "name": name,
            "required": True,
            "observed": False,
            "status": "not_observed_not_proven",
        }
        for name in DEVICE_PWA_OBSERVATION_CHECKLIST
    ]


def _copy_summary(evidence_ref: str, precheck_verdict: str) -> dict[str, Any]:
    # copy/export 只包含白名单字段，不包含 raw artifact 或本机路径。
    return {
        "schema": COPY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": precheck_verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "device_pwa_observation_required": list(DEVICE_PWA_OBSERVATION_CHECKLIST),
        "route_elevator_field_materials_required": list(REQUIRED_ROUTE_ELEVATOR_MATERIALS),
        "real_device_observed": False,
        "pwa_install_prompt_observed": False,
        "route_elevator_field_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "not_proven": list(NOT_PROVEN),
        "safe_copy_note": "software_proof only; route/elevator and 真实设备 field evidence remains 不证明",
    }


def _decide_verdict(
    handoff: dict[str, Any],
    target_ref: str,
    handoff_payload: dict[str, Any],
    precheck_payload: dict[str, Any] | None = None,
) -> tuple[str, list[str], str]:
    # verdict 保守分层：输入缺失/contract 错误/ref 错误/unsafe/success claim 都 blocked。
    missing: list[str] = []
    if not handoff.get("present"):
        missing.append("route_elevator_field_session_handoff")
        return "blocked_missing_inputs", missing, "missing_route_elevator_handoff"

    if handoff.get("schema_status") != "supported":
        missing.append("route_elevator_field_session_handoff:unsupported_schema")
    if handoff.get("boundary_status") != "supported":
        missing.append("route_elevator_field_session_handoff:unsupported_boundary")
    if handoff.get("source_status") != "supported":
        missing.append("route_elevator_field_session_handoff:unsupported_source")
    if missing:
        return "blocked_invalid_input", missing, "unsupported_handoff_contract"

    ref = _safe_ref(target_ref or handoff.get("evidence_ref"))
    if not ref:
        return "blocked_missing_evidence_ref", ["evidence_ref"], "missing_same_evidence_ref"
    if handoff.get("evidence_ref") and handoff.get("evidence_ref") != ref:
        return "blocked_evidence_ref_mismatch", ["route_elevator_field_session_handoff:evidence_ref"], "same_evidence_ref_mismatch"

    safety_target: Any = {"handoff": handoff_payload, "precheck": precheck_payload or {}}
    if _has_forbidden_copy(safety_target):
        return "blocked_unsafe_copy", ["phone_safe_copy"], "unsafe_copy"
    if _has_success_claim(safety_target) or handoff.get("delivery_success") or handoff.get("primary_actions_enabled"):
        return "blocked_success_or_control_claim", ["success_or_control_claim"], "success_or_control_claim"

    return "ready_for_field_device_precheck_not_proven", [], "software_precheck_ready_not_proven"


def build_precheck(route_elevator_handoff_json: str = "", evidence_ref: str = "") -> tuple[dict[str, Any], dict[str, Any], int]:
    """从 route/elevator handoff 生成现场前检查 artifact 与 summary。"""

    handoff_payload, handoff_error = _load_json(route_elevator_handoff_json, "route_elevator_handoff")
    handoff = _handoff_summary(handoff_payload, handoff_error)
    target_ref = _safe_ref(evidence_ref or handoff.get("evidence_ref"))
    verdict, missing, reason = _decide_verdict(handoff, target_ref, handoff_payload)
    safe_ref = target_ref or handoff.get("evidence_ref") or "<same_evidence_ref>"

    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "precheck_verdict": verdict,
        "precheck_reason": reason,
        "evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": "matched_same_evidence_ref" if not missing and safe_ref else "not_proven",
        "route_elevator_handoff_summary": handoff,
        "required_route_elevator_field_materials": _material_checklist(),
        "device_pwa_observation_checklist": _device_checklist(),
        "mobile_copy_summary": _copy_summary(safe_ref, verdict),
        "missing_or_blocked": missing,
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "field_device_precheck_only_not_delivery_success",
        "real_device_observed": False,
        "pwa_install_prompt_observed": False,
        "route_elevator_field_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)

    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": artifact["generated_at"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": verdict,
        "precheck_verdict": verdict,
        "evidence_ref": artifact["evidence_ref"],
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": artifact["same_evidence_ref_status"],
        "route_elevator_handoff_summary": handoff,
        "required_route_elevator_field_material_names": list(REQUIRED_ROUTE_ELEVATOR_MATERIALS),
        "device_pwa_observation_checklist_names": list(DEVICE_PWA_OBSERVATION_CHECKLIST),
        "mobile_copy_summary": artifact["mobile_copy_summary"],
        "not_proven": list(NOT_PROVEN),
        "real_device_observed": False,
        "pwa_install_prompt_observed": False,
        "route_elevator_field_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return artifact, _safe_value(summary), 0 if verdict == "ready_for_field_device_precheck_not_proven" else 2


def validate_precheck(precheck_json: str, evidence_ref: str = "") -> tuple[dict[str, Any], dict[str, Any], int]:
    """校验已有 precheck summary/artifact 是否仍保持 software proof 边界。"""

    payload, error = _load_json(precheck_json, "precheck")
    if error:
        handoff = _handoff_summary({}, "route_elevator_handoff_not_provided")
        verdict, missing, reason = "blocked_missing_inputs", ["precheck"], error
        safe_ref = _safe_ref(evidence_ref) or "<same_evidence_ref>"
    else:
        schema = _safe_text(payload.get("schema")).strip()
        boundary = _safe_text(payload.get("evidence_boundary")).strip()
        handoff = _dict(payload, "route_elevator_handoff_summary")
        safe_ref = _safe_ref(evidence_ref or payload.get("evidence_ref")) or "<same_evidence_ref>"
        missing = []
        if schema not in {SCHEMA, SUMMARY_SCHEMA}:
            missing.append("precheck:unsupported_schema")
        if boundary != EVIDENCE_BOUNDARY:
            missing.append("precheck:unsupported_boundary")
        if evidence_ref and _safe_ref(payload.get("evidence_ref")) != safe_ref:
            missing.append("precheck:evidence_ref")
        if _has_forbidden_copy(payload):
            missing.append("phone_safe_copy")
        if _has_success_claim(payload):
            missing.append("success_or_control_claim")
        verdict = "validated_field_device_precheck_not_proven" if not missing else "blocked_invalid_precheck"
        reason = "software_precheck_validated_not_proven" if not missing else "precheck_contract_or_safety_failed"

    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "precheck_verdict": verdict,
        "precheck_reason": reason,
        "evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": "matched_same_evidence_ref" if verdict.startswith("validated") else "not_proven",
        "route_elevator_handoff_summary": handoff,
        "required_route_elevator_field_materials": _material_checklist(),
        "device_pwa_observation_checklist": _device_checklist(),
        "mobile_copy_summary": _copy_summary(safe_ref, verdict),
        "missing_or_blocked": missing,
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "field_device_precheck_validation_only_not_delivery_success",
        "real_device_observed": False,
        "pwa_install_prompt_observed": False,
        "route_elevator_field_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": artifact["generated_at"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": verdict,
        "precheck_verdict": verdict,
        "evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": artifact["same_evidence_ref_status"],
        "not_proven": list(NOT_PROVEN),
        "real_device_observed": False,
        "pwa_install_prompt_observed": False,
        "route_elevator_field_pass": False,
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
        description="Generate or validate mobile route/elevator field-device precheck software-proof summary."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--route-elevator-handoff-json", default="", help="Route/elevator field-session handoff JSON.")
    mode.add_argument("--precheck-json", default="", help="Existing precheck summary/artifact JSON to validate.")
    parser.add_argument("--evidence-ref", default="", help="Expected same evidence_ref for this field-device precheck.")
    parser.add_argument("--output", default="", help="Write full precheck artifact JSON to this path.")
    parser.add_argument("--summary-output", default="", help="Write summary JSON to this path.")
    parser.add_argument("--once-json", action="store_true", help="Print summary JSON to stdout.")
    args = parser.parse_args(argv)

    if args.precheck_json:
        artifact, summary, exit_code = validate_precheck(args.precheck_json, args.evidence_ref)
    else:
        artifact, summary, exit_code = build_precheck(args.route_elevator_handoff_json, args.evidence_ref)

    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
