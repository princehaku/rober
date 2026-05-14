#!/usr/bin/env python3
"""生成 route/task field-run intake crosscheck artifact。

该工具只读取五份 JSON object 材料，做同一 evidence_ref 的软件复账。
它不 import ROS2、不访问 Nav2 runtime、不读取串口或硬件，也不证明真实送达。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema/boundary 是 diagnostics、mobile 和 sprint closeout 的稳定机器契约。
INTAKE_SCHEMA = "trashbot.route_task_field_run_intake_crosscheck.v1"
INTAKE_SCHEMA_VERSION = 1
INTAKE_BOUNDARY = "software_proof_docker_route_task_field_run_intake_crosscheck_gate"

# 五份输入材料允许新 schema，也允许上一轮已有 artifact 的兼容摘要字段。
SUPPORTED_SCHEMAS = {
    "route_status": {"trashbot.fixed_route_status.v1", "trashbot.pc_route_debug_console.v1"},
    "task_record": {"trashbot.task_record.v1", "trashbot.task_record"},
    "runtime_log": {"trashbot.nav2_fixed_route_runtime_log.v1", "trashbot.route_runtime_log.v1"},
    "robot_side_task_evidence": {"trashbot.robot_side_task_evidence.v1"},
    "support_safe_mobile_summary": {
        "trashbot.support_safe_mobile_summary.v1",
        "trashbot.mobile_support_safe_summary.v1",
    },
}

# not_proven 必须覆盖真实路线、硬件、HIL、投放/取消和 O5 外部材料，避免软件复账被误读。
NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "real_robot_base_motion",
    "real_hardware_feedback",
    "real_hil_pass",
    "dropoff_completion",
    "cancel_completion",
    "delivery_success",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# phone-safe copy 不能携带凭证、完整路径、ROS 控制 topic、硬件连接细节或 raw traceback。
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

# 脱敏规则先保护输出，再用 forbidden copy 检查确认摘要没有残留敏感材料。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\bOSS_[A-Z_]*(ACCESS|SECRET)[A-Z_]*\b\s*[:=]\s*[^,\s]+"), "OSS_KEY=[REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_RATE]"),
    (re.compile(r"(?i)WAVE\s+ROVER"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
)


def _utc_now() -> str:
    # UTC 时间让 Docker/local 多主机产物能按字符串稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本都先转字符串再脱敏，兼容旧 artifact 的任意字段类型。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 本机绝对路径不进入 phone/support 摘要；只保留 basename 作为同 run 引用。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏只用于有限摘要，避免把 raw artifact 原样复制到输出。
    if isinstance(value, dict):
        return {str(_safe_text(k)): _safe_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _encoded(value: Any) -> str:
    # json.dumps 失败时退回安全文本，保证坏材料不会变成未处理异常。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # phone-safe 检查使用原文和脱敏后摘要两层，命中时保守 blocked。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺失、坏 JSON、非 object 都进入 blocked 材料，不让 CLI 抛未处理异常。
    if not path:
        return {}, f"{label}_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, f"{label}_missing"
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}, f"{label}_read_error"
    if not isinstance(payload, dict):
        return {}, f"{label}_not_object"
    return payload, ""


def _first_text(*values: Any, default: str = "") -> str:
    # evidence_ref 兼容多个旧字段；空字符串保持空，交给 missing_materials 处理。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 旧 artifact 嵌套层级不完全一致，统一把非 dict 当空对象处理。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _extract_evidence_ref(payload: dict[str, Any]) -> str:
    # 同一 run 主键可能出现在顶层、route_progress、task/result 或 phone summary 内。
    route_progress = _dict(payload, "route_progress")
    diagnostics = _dict(payload, "diagnostics_summary")
    task = _dict(payload, "task")
    task_result = _dict(payload, "task_result")
    action_result = _dict(payload, "action_result")
    phone = _dict(payload, "phone_safe_summary") or _dict(payload, "support_safe_summary")
    return _first_text(
        payload.get("evidence_ref"),
        route_progress.get("evidence_ref"),
        diagnostics.get("evidence_ref"),
        task.get("evidence_ref"),
        task_result.get("evidence_ref"),
        action_result.get("evidence_ref"),
        phone.get("evidence_ref"),
        default="",
    )


def _schema_status(payload: dict[str, Any], label: str) -> str:
    # 有明确 schema 时必须匹配；无 schema 时只接受足够强的兼容字段组合。
    schema = str(payload.get("schema", "")).strip()
    if schema:
        return "supported" if schema in SUPPORTED_SCHEMAS[label] else "unsupported"
    if label == "route_status" and (_dict(payload, "route_progress") or payload.get("route_contract_version")):
        return "compatible_summary"
    if label == "task_record" and (_dict(payload, "route_progress") or payload.get("state_transition_history")):
        return "compatible_summary"
    if label == "runtime_log" and any(isinstance(payload.get(key), list) for key in ("events", "runtime_events", "entries")):
        return "compatible_summary"
    if label == "robot_side_task_evidence" and any(payload.get(key) is not None for key in ("task_result", "action_result", "route_progress")):
        return "compatible_summary"
    if label == "support_safe_mobile_summary" and any(
        isinstance(payload.get(key), dict) for key in ("phone_safe_summary", "support_safe_summary", "safe_copy")
    ):
        return "compatible_summary"
    return "unsupported"


def _material_status(load_issue: str, schema_status: str, evidence_ref: str, expected_ref: str) -> str:
    # source_materials 给 diagnostics/mobile 展示材料状态，不泄露 raw artifact 内容。
    if load_issue:
        return "missing"
    if schema_status == "unsupported":
        return "unsupported_schema"
    if not evidence_ref:
        return "missing_evidence_ref"
    if expected_ref and evidence_ref != expected_ref:
        return "mismatch"
    return "present"


def _source_material(label: str, path: str, payload: dict[str, Any], load_issue: str) -> dict[str, Any]:
    # 每个 source 只输出 schema、状态、safe ref 和 evidence_ref，不复制输入 JSON。
    schema_status = "" if load_issue else _schema_status(payload, label)
    evidence_ref = _safe_ref(_extract_evidence_ref(payload)) if payload else ""
    return {
        "name": label,
        "ref": _safe_ref(path),
        "load_status": "blocked" if load_issue else "loaded",
        "load_issue": load_issue,
        "schema": _safe_text(payload.get("schema", "")) if payload else "",
        "schema_status": schema_status,
        "evidence_ref": evidence_ref,
    }


def _requested_evidence_ref(explicit_ref: str, sources: list[dict[str, Any]]) -> str:
    # 显式参数优先；没有参数时取第一份可见 evidence_ref 作为本轮同 run 目标。
    return _safe_ref(explicit_ref) or _first_text(*(source.get("evidence_ref", "") for source in sources), default="")


def _missing_materials(sources: list[dict[str, Any]], expected_ref: str, unsafe_mobile: bool) -> list[str]:
    # missing_materials 只描述缺材料/坏材料；同 run 不一致另放 mismatch_reasons。
    missing: list[str] = []
    for source in sources:
        name = source["name"]
        if source["load_status"] != "loaded":
            missing.append(f"{name}:{source['load_issue']}")
            continue
        if source["schema_status"] == "unsupported":
            missing.append(f"{name}:unsupported_schema")
        if not source.get("evidence_ref"):
            missing.append(f"{name}:missing_evidence_ref")
    if expected_ref and all(source.get("evidence_ref") != expected_ref for source in sources):
        missing.append("evidence_ref:requested_ref_not_present")
    if unsafe_mobile:
        missing.append("support_safe_mobile_summary:unsafe_summary")
    return missing


def _mismatch_reasons(sources: list[dict[str, Any]], expected_ref: str) -> list[str]:
    # mismatch_reasons 指出哪份材料偏离同一 evidence_ref，便于现场重跑而不是猜成功。
    mismatches: list[str] = []
    loaded_refs = {source["evidence_ref"] for source in sources if source.get("evidence_ref")}
    if len(loaded_refs) > 1:
        mismatches.append("evidence_ref:sources_do_not_share_same_ref")
    for source in sources:
        ref = source.get("evidence_ref", "")
        if expected_ref and ref and ref != expected_ref:
            mismatches.append(f"{source['name']}:evidence_ref_mismatch:{ref}!={expected_ref}")
    return mismatches


def _commands_to_rerun(evidence_ref: str, missing: list[str], mismatches: list[str]) -> list[str]:
    # 命令清单只给操作形状，不包含本机绝对路径、凭证、topic 或硬件连接参数。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = [
        f"export route status JSON with evidence_ref={ref}",
        f"export task record JSON with evidence_ref={ref}",
        f"export Nav2/fixed-route runtime log with evidence_ref={ref}",
        f"export robot-side task evidence with evidence_ref={ref}",
        f"export support-safe mobile summary with evidence_ref={ref}",
        "rerun route_task_field_run_intake.py after all five materials exist",
    ]
    if missing:
        commands.append("repair missing_materials before any field-run claim")
    if mismatches:
        commands.append("rerun mismatched sources under one shared evidence_ref")
    return commands


def _phone_safe_summary(
    overall_status: str,
    evidence_ref: str,
    sources: list[dict[str, Any]],
    missing: list[str],
    mismatches: list[str],
    commands: list[str],
) -> dict[str, Any]:
    # 手机/售后摘要只保留状态、计数和重跑建议；不复制 raw JSON 或完整路径。
    material_status = {
        source["name"]: _material_status(
            source.get("load_issue", ""),
            source.get("schema_status", ""),
            source.get("evidence_ref", ""),
            evidence_ref,
        )
        for source in sources
    }
    return {
        "schema": INTAKE_SCHEMA,
        "evidence_boundary": INTAKE_BOUNDARY,
        "status": overall_status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "material_status": material_status,
        "missing_materials_count": len(missing),
        "mismatch_reasons_count": len(mismatches),
        "commands_to_rerun": commands[:],
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "accepted_or_processing_support_metadata_only_not_delivery_success",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _overall_status(load_issues: list[str], unsupported: bool, missing: list[str], mismatches: list[str], unsafe: bool) -> str:
    # 状态优先级保持保守：缺材料、schema、同 run 不一致、安全检查，全部过关才 ready。
    if load_issues or any("missing_evidence_ref" in item or "requested_ref" in item for item in missing):
        return "blocked_missing_material"
    if unsupported:
        return "blocked_unsupported_schema"
    if mismatches:
        return "blocked_mismatch"
    if unsafe:
        return "blocked_unsafe_summary"
    return "ready_for_review"


def build_intake_crosscheck(
    route_status_json: str,
    task_record_json: str,
    runtime_log_json: str,
    robot_side_task_evidence_json: str,
    support_safe_mobile_summary_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], int]:
    route_payload, route_issue = _load_json(route_status_json, "route_status")
    task_payload, task_issue = _load_json(task_record_json, "task_record")
    runtime_payload, runtime_issue = _load_json(runtime_log_json, "runtime_log")
    robot_payload, robot_issue = _load_json(robot_side_task_evidence_json, "robot_side_task_evidence")
    mobile_payload, mobile_issue = _load_json(support_safe_mobile_summary_json, "support_safe_mobile_summary")

    sources = [
        _source_material("route_status", route_status_json, route_payload, route_issue),
        _source_material("task_record", task_record_json, task_payload, task_issue),
        _source_material("runtime_log", runtime_log_json, runtime_payload, runtime_issue),
        _source_material("robot_side_task_evidence", robot_side_task_evidence_json, robot_payload, robot_issue),
        _source_material("support_safe_mobile_summary", support_safe_mobile_summary_json, mobile_payload, mobile_issue),
    ]
    requested_ref = _requested_evidence_ref(evidence_ref, sources)
    load_issues = [source["load_issue"] for source in sources if source.get("load_issue")]
    unsupported = any(source.get("schema_status") == "unsupported" for source in sources)

    # support-safe mobile summary 原文命中敏感词也要 blocked；输出仍保持脱敏摘要。
    unsafe_mobile = bool(mobile_payload and _has_forbidden_copy(mobile_payload))
    missing = _missing_materials(sources, requested_ref, unsafe_mobile)
    mismatches = _mismatch_reasons(sources, requested_ref)
    status = _overall_status(load_issues, unsupported, missing, mismatches, unsafe_mobile)
    commands = _commands_to_rerun(requested_ref, missing, mismatches)
    phone_summary = _phone_safe_summary(status, requested_ref, sources, missing, mismatches, commands)

    if _has_forbidden_copy(phone_summary):
        # phone summary 是对外材料，任何残留敏感词都降级为 unsafe，而不是试图证明可控。
        status = "blocked_unsafe_summary"
        if "support_safe_mobile_summary:unsafe_summary" not in missing:
            missing.append("support_safe_mobile_summary:unsafe_summary")
        phone_summary = _phone_safe_summary(status, requested_ref, sources, missing, mismatches, commands)

    intake = {
        "schema": INTAKE_SCHEMA,
        "schema_version": INTAKE_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": INTAKE_BOUNDARY,
        "overall_status": status,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_materials": sources,
        "missing_materials": missing,
        "mismatch_reasons": mismatches,
        "commands_to_rerun": commands,
        "phone_safe_summary": phone_summary,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return _safe_value(intake), 0


def write_intake(intake: dict[str, Any], output: str) -> None:
    # output 为空时仅 stdout；指定文件时自动建父目录，方便 /tmp 验收。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(intake, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只读五个 JSON object；--once-json 方便测试和 sprint 验收直接消费 stdout。
    parser = argparse.ArgumentParser(description="Generate route/task field-run intake crosscheck JSON")
    parser.add_argument("--route-status-json", required=True, help="route status JSON object")
    parser.add_argument("--task-record-json", required=True, help="task record JSON object")
    parser.add_argument("--runtime-log-json", required=True, help="Nav2/fixed-route runtime log JSON object")
    parser.add_argument("--robot-side-task-evidence-json", required=True, help="robot-side task evidence JSON object")
    parser.add_argument("--support-safe-mobile-summary-json", required=True, help="support-safe mobile summary JSON object")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for all source materials")
    parser.add_argument("--output", default="", help="optional output JSON path")
    parser.add_argument("--once-json", action="store_true", help="print intake crosscheck JSON to stdout and exit")
    args = parser.parse_args()

    intake, exit_code = build_intake_crosscheck(
        route_status_json=args.route_status_json,
        task_record_json=args.task_record_json,
        runtime_log_json=args.runtime_log_json,
        robot_side_task_evidence_json=args.robot_side_task_evidence_json,
        support_safe_mobile_summary_json=args.support_safe_mobile_summary_json,
        evidence_ref=args.evidence_ref,
    )
    write_intake(intake, args.output)
    if args.once_json or not args.output:
        print(json.dumps(intake, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field-run intake: intake_file:{_safe_ref(args.output)}")
        print(f"overall_status: {intake['overall_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
