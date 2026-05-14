#!/usr/bin/env python3
"""生成 route/task completion signal artifact。

该工具只读取 PC/Docker 本地 JSON 材料，给 diagnostics/mobile 提供只读完成信号。
它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件或外部云。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 顶层 schema/boundary 是 Robot diagnostics 与 mobile/web 的稳定机器契约。
COMPLETION_SCHEMA = "trashbot.route_task_completion_signal.v1"
COMPLETION_SCHEMA_VERSION = 1
COMPLETION_BOUNDARY = "software_proof_docker_route_task_completion_signal_gate"

# 上游 route/task 形态必须白名单化；未知 schema 宁可 blocked，不猜字段语义。
ROUTE_SCHEMAS = {
    "trashbot.fixed_route_status.v1",
    "trashbot.fixed_route_replay.v1",
    "trashbot.pc_route_debug_console.v1",
}
TASK_RECORD_SCHEMAS = {"trashbot.task_record.v1", "trashbot.task_record"}
SUMMARY_SCHEMAS = {
    "trashbot.route_task_field_run_reconciliation.v1",
    "trashbot.route_task_field_run_review_console.v1",
    "trashbot.route_task_field_run_intake_crosscheck.v1",
}
SUMMARY_BOUNDARIES = {
    "software_proof_docker_route_task_field_run_reconciliation_gate",
    "software_proof_docker_route_task_field_run_review_console_gate",
    "software_proof_docker_route_task_field_run_intake_crosscheck_gate",
}
DROP_COMPLETION_SCHEMAS = {
    "trashbot.dropoff_completion.v1",
    "trashbot.route_task_dropoff_completion.v1",
    "trashbot.route_task_completion_material.v1",
}
CANCEL_COMPLETION_SCHEMAS = {
    "trashbot.cancel_completion.v1",
    "trashbot.route_task_cancel_completion.v1",
    "trashbot.route_task_completion_material.v1",
}

# not_proven 明确写出所有真实能力缺口，避免 completed_not_proven 被误读为上车成功。
NOT_PROVEN = (
    "real_delivery",
    "real_dropoff_completion",
    "real_cancel_completion",
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "wave_rover_motion",
    "real_uart_feedback",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# phone-safe 摘要不得携带凭证、控制 topic、硬件传输细节、本机路径或 raw 调试材料。
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

# 脱敏先保护输出，再由 forbidden copy 检查决定是否 fail closed。
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
    (re.compile(r"(?i)\bserial\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bUART\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)WAVE\s+ROVER"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 字符串让不同 Docker/PC 主机产物能稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，避免 summary 成为凭证或硬件细节扩散渠道。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 本机绝对路径不能进入手机摘要；只保留 basename 作为同 run 线索。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 兼容旧 artifact 的字符串/list 形态，并限制输出规模。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 最终 artifact 再递归脱敏一遍，防止新增字段绕过 helper。
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
    # 安全检查需要稳定字符串；不可编码对象按脱敏文本处理。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 命中禁词时必须 fail closed，而不是尝试继续展示可疑摘要。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON、非 object 都变成 blocked artifact，不让 CLI 抛未处理异常。
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


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 旧材料嵌套层级会漂移，非 object 字段统一按空对象处理。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # evidence_ref、失败原因等字段有多个来源，只取第一个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _extract_evidence_ref(payload: dict[str, Any]) -> str:
    # 同一 run 主键可能在顶层、route_progress、task/result 或 phone summary 内。
    route_progress = _dict(payload, "route_progress")
    diagnostics = _dict(payload, "diagnostics_summary")
    task = _dict(payload, "task")
    task_result = _dict(payload, "task_result")
    action_result = _dict(payload, "action_result")
    phone = _dict(payload, "phone_safe_summary") or _dict(payload, "support_safe_summary")
    return _safe_ref(
        _first_text(
            payload.get("evidence_ref"),
            route_progress.get("evidence_ref"),
            diagnostics.get("evidence_ref"),
            task.get("evidence_ref"),
            task_result.get("evidence_ref"),
            action_result.get("evidence_ref"),
            phone.get("evidence_ref"),
            default="",
        )
    )


def _schema_status(payload: dict[str, Any], label: str) -> str:
    # 有 schema 时必须匹配；无 schema 只接受足够明确的兼容摘要字段。
    schema = str(payload.get("schema", "")).strip()
    if label == "route_status":
        if schema:
            return "supported" if schema in ROUTE_SCHEMAS else "unsupported"
        return "compatible_summary" if (_dict(payload, "route_progress") or payload.get("software_proof")) else "unsupported"
    if label == "task_record":
        if schema:
            return "supported" if schema in TASK_RECORD_SCHEMAS else "unsupported"
        return "compatible_summary" if (_dict(payload, "route_progress") or payload.get("state_transition_history")) else "unsupported"
    if label == "completion_summary":
        if schema:
            boundary = str(payload.get("evidence_boundary", "")).strip()
            schema_ok = schema in SUMMARY_SCHEMAS
            boundary_ok = not boundary or boundary in SUMMARY_BOUNDARIES
            return "supported" if schema_ok and boundary_ok else "unsupported"
        return "compatible_summary" if any(key in payload for key in ("reconciliation_verdict", "review_decision", "missing_materials")) else "unsupported"
    if label == "dropoff_completion":
        if schema:
            return "supported" if schema in DROP_COMPLETION_SCHEMAS else "unsupported"
        return "compatible_summary" if any(key in payload for key in ("dropoff_completed", "completion_status", "completed")) else "unsupported"
    if label == "cancel_completion":
        if schema:
            return "supported" if schema in CANCEL_COMPLETION_SCHEMAS else "unsupported"
        return "compatible_summary" if any(key in payload for key in ("cancel_completed", "completion_status", "completed")) else "unsupported"
    return "unsupported"


def _source_state(label: str, path: str, payload: dict[str, Any], load_issue: str, required: bool) -> dict[str, Any]:
    # source_state 只暴露白名单元数据，不复制输入 JSON，保护 raw artifact 边界。
    schema_status = "" if load_issue else _schema_status(payload, label)
    return {
        "name": label,
        "ref": _safe_ref(path),
        "required": required,
        "load_status": "blocked" if load_issue else "loaded",
        "load_issue": load_issue,
        "schema": _safe_text(payload.get("schema", "")) if payload else "",
        "schema_status": schema_status,
        "evidence_boundary": _safe_text(payload.get("evidence_boundary", "")) if payload else "",
        "evidence_ref": _extract_evidence_ref(payload) if payload else "",
    }


def _route_summary(payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # route summary 聚焦 fixed-route/replay 关键字段，避免输出完整 status。
    route_progress = _dict(payload, "route_progress")
    replay = _dict(payload, "software_proof") or _dict(payload, "replay")
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "route_status": _safe_text(_first_text(payload.get("status"), route_progress.get("status"), payload.get("overall_status"), default="")),
        "checkpoint": _safe_text(_first_text(payload.get("checkpoint"), route_progress.get("checkpoint"), route_progress.get("checkpoint_id"), default="")),
        "current_index": route_progress.get("current_index", payload.get("current_index", "")),
        "target": _safe_text(_first_text(payload.get("target"), route_progress.get("target"), route_progress.get("target_id"), default="")),
        "failure_code": _safe_text(_first_text(payload.get("failure_code"), route_progress.get("failure_code"), default="")),
        "replay_status": _safe_text(_first_text(replay.get("status"), replay.get("overall_status"), default="")),
    }


def _state_history(payload: dict[str, Any]) -> list[str]:
    # state_transition_history 可能是字符串或 dict；统一压成短文本状态序列。
    raw = payload.get("state_transition_history") or payload.get("state_transitions") or []
    if not isinstance(raw, list):
        return []
    states: list[str] = []
    for item in raw[:30]:
        if isinstance(item, dict):
            states.append(_safe_text(_first_text(item.get("state"), item.get("to_state"), item.get("status"), default="")))
        else:
            states.append(_safe_text(item))
    return [state for state in states if state]


def _task_record_summary(payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # task record summary 只提取状态机、失败/恢复和 result 线索，避免复制完整任务记录。
    route_progress = _dict(payload, "route_progress")
    result = _dict(payload, "task_result") or _dict(payload, "action_result") or _dict(payload, "result")
    states = _state_history(payload)
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "task_id": _safe_text(payload.get("task_id", "")),
        "task_status": _safe_text(_first_text(payload.get("status"), payload.get("overall_status"), result.get("status"), default="")),
        "result_code": _safe_text(_first_text(result.get("code"), result.get("result_code"), payload.get("result_code"), default="")),
        "failure_reason": _safe_text(_first_text(payload.get("failure_reason"), result.get("failure_reason"), result.get("error_message"), default="")),
        "recovery_reason": _safe_text(_first_text(payload.get("recovery_reason"), result.get("recovery_reason"), result.get("recovery_action"), default="")),
        "route_progress_present": bool(route_progress),
        "state_transition_count": len(states),
        "last_state": states[-1] if states else "",
    }


def _state_transition_summary(payload: dict[str, Any]) -> dict[str, Any]:
    # 状态机摘要让 completion signal 能判断 dropoff/cancel 材料是否应出现。
    states = _state_history(payload)
    upper = [state.upper() for state in states]
    return {
        "states": states[:12],
        "state_transition_count": len(states),
        "last_state": states[-1] if states else "",
        "has_dropoff_state": any("DROPOFF" in state or "DELIVERED" in state for state in upper),
        "has_cancel_state": any("CANCEL" in state for state in upper),
        "has_failure_state": any("ERROR" in state or "FAIL" in state for state in upper),
    }


def _completion_bool(payload: dict[str, Any], kind: str) -> bool:
    # 完成材料只证明“声明存在”，本 gate 仍把真实完成列入 not_proven。
    keys = (f"{kind}_completed", "completed", "completion_confirmed")
    for key in keys:
        if payload.get(key) is True:
            return True
    status = str(payload.get("completion_status", payload.get("status", ""))).lower()
    return status in {"completed", "confirmed", "done", f"{kind}_completed"}


def _completion_summary(kind: str, payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # dropoff/cancel completion 是可选材料；存在也只能记为 present_not_proven。
    if source["load_issue"].endswith("_not_provided"):
        status = "not_provided"
    elif source["load_status"] != "loaded":
        status = "blocked_not_loaded"
    elif source["schema_status"] == "unsupported":
        status = "blocked_unsupported_schema"
    else:
        status = "material_present_not_proven"
    return {
        "material_status": status,
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "completion_claimed": _completion_bool(payload, kind) if payload else False,
        "completion_evidence_boundary": "software_material_only_not_real_completion",
        "delivery_success": False,
    }


def _completion_source_material_status(source_payload: dict[str, Any]) -> dict[str, Any]:
    # 上一轮 reconciliation/review/intake 的材料状态只保留计数和 verdict。
    phone = _dict(source_payload, "phone_safe_summary")
    return {
        "schema": _safe_text(source_payload.get("schema", "")),
        "evidence_boundary": _safe_text(source_payload.get("evidence_boundary", "")),
        "status": _safe_text(_first_text(source_payload.get("reconciliation_verdict"), source_payload.get("overall_status"), phone.get("status"), default="")),
        "missing_materials_count": len(_safe_list(source_payload.get("missing_materials"))),
        "mismatch_reasons_count": len(_safe_list(source_payload.get("mismatch_reasons"))),
        "source_phone_status": _safe_text(phone.get("status", "")),
        "source_delivery_success": bool(source_payload.get("delivery_success", False) or phone.get("delivery_success", False)),
    }


def _source_steps(*payloads: dict[str, Any]) -> list[str]:
    # operator_next_steps 继承上游安全摘要，并由本 gate 追加 completion 边界。
    steps: list[str] = []
    for payload in payloads:
        phone = _dict(payload, "phone_safe_summary")
        for item in _safe_list(payload.get("operator_next_steps") or phone.get("operator_next_steps"), limit=4):
            if item and item not in steps:
                steps.append(item)
    return steps


def _required_missing(sources: list[dict[str, Any]]) -> list[str]:
    # required source 缺失、坏 JSON、unsupported schema 或缺 evidence_ref 都是硬阻断。
    missing: list[str] = []
    for source in sources:
        if not source["required"]:
            continue
        if source["load_status"] != "loaded":
            missing.append(f"{source['name']}:{source['load_issue']}")
            continue
        if source["schema_status"] == "unsupported":
            missing.append(f"{source['name']}:unsupported_schema")
        if not source["evidence_ref"]:
            missing.append(f"{source['name']}:missing_evidence_ref")
    return missing


def _mismatch_reasons(sources: list[dict[str, Any]], expected_ref: str) -> list[str]:
    # 同一 evidence_ref 是 completion signal 的核心约束，optional 材料存在也必须对齐。
    mismatches: list[str] = []
    for source in sources:
        if source["load_status"] != "loaded":
            continue
        ref = source.get("evidence_ref", "")
        if expected_ref and ref and ref != expected_ref:
            mismatches.append(f"{source['name']}:evidence_ref_mismatch:{ref}!={expected_ref}")
    loaded_refs = {source.get("evidence_ref", "") for source in sources if source["load_status"] == "loaded" and source.get("evidence_ref")}
    if len(loaded_refs) > 1:
        mismatches.append("evidence_ref:sources_do_not_share_same_ref")
    return mismatches


def _needs_completion_material(state_summary: dict[str, Any], kind: str) -> bool:
    # 状态机进入 dropoff/cancel 分支时，缺对应 completion material 必须 fail closed。
    if kind == "dropoff":
        return bool(state_summary.get("has_dropoff_state"))
    return bool(state_summary.get("has_cancel_state"))


def _input_claims_delivery_success(payloads: list[dict[str, Any]]) -> bool:
    # 任何上游 delivery_success=true 都视为越界成功声明，必须 blocked。
    for payload in payloads:
        phone = _dict(payload, "phone_safe_summary")
        if payload.get("delivery_success") is True or phone.get("delivery_success") is True:
            return True
    return False


def _operator_next_steps(
    verdict: str,
    evidence_ref: str,
    source_steps: list[str],
    missing: list[str],
    mismatches: list[str],
) -> list[str]:
    # 操作建议必须指向下一步材料修复，而不是让用户从 JSON 猜原因。
    ref = evidence_ref or "<same_evidence_ref>"
    if verdict in {"blocked_missing_completion_materials", "blocked_bad_json", "blocked_unsupported_schema"}:
        steps = [
            f"Collect route status/replay, task record, completion summary, and required completion material for evidence_ref={ref}.",
            "Rerun this completion signal gate after missing or unsupported JSON is repaired.",
            "Keep delivery_success=false until real field evidence exists.",
        ]
    elif verdict == "blocked_mismatch_evidence_ref":
        steps = [
            f"Re-export all route/task/completion materials under one evidence_ref={ref}.",
            "Do not combine route status, task record, reconciliation, dropoff, or cancel materials from different runs.",
            "Rerun this gate after evidence_ref mismatch is cleared.",
        ]
    elif verdict == "blocked_unsafe_phone_summary":
        steps = [
            "Remove unsafe phone/support copy from source materials.",
            "Regenerate summaries without credentials, raw robot response, ROS topics, serial/UART, WAVE ROVER, paths, or tracebacks.",
            "Rerun this gate before mobile/diagnostics display.",
        ]
    elif verdict == "blocked_delivery_success_claim":
        steps = [
            "Remove delivery_success=true from Docker/local source materials.",
            "Use this gate only for software-proof completion signal review.",
            "Collect real Nav2/fixed-route, dropoff/cancel, HIL, and delivery evidence before any success claim.",
        ]
    elif verdict == "failed_with_recovery_reason":
        steps = source_steps[:2] + [
            f"Review failure/recovery reason for evidence_ref={ref} before another route/task run.",
            "Keep this as a failed software completion signal, not delivery success.",
        ]
    else:
        steps = source_steps[:2] + [
            f"Preserve evidence_ref={ref} across the next real route/task review.",
            "Treat completed_not_proven as Docker/local material shape only, not real delivery.",
        ]
    if missing:
        steps.append(f"Missing or blocked materials: {', '.join(missing[:3])}")
    if mismatches:
        steps.append(f"Evidence mismatch: {', '.join(mismatches[:2])}")

    # 去重后限长，保证手机面板可读。
    result: list[str] = []
    for item in steps:
        if item and item not in result:
            result.append(_safe_text(item))
    return result[:5]


def _verdict(
    sources: list[dict[str, Any]],
    state_summary: dict[str, Any],
    dropoff: dict[str, Any],
    cancel: dict[str, Any],
    missing: list[str],
    mismatches: list[str],
    unsafe: bool,
    delivery_success_claimed: bool,
    failure_reason: str,
    recovery_reason: str,
) -> str:
    # verdict 优先级保持 fail-closed：可读性、schema、同 ref、安全、越界成功声明、材料完整性。
    load_issues = {source["load_issue"] for source in sources if source["load_issue"]}
    if any(issue.endswith("_bad_json") or issue.endswith("_not_object") or issue.endswith("_read_error") for issue in load_issues):
        return "blocked_bad_json"
    if any(source["schema_status"] == "unsupported" for source in sources if source["load_status"] == "loaded"):
        return "blocked_unsupported_schema"
    if mismatches:
        return "blocked_mismatch_evidence_ref"
    if unsafe:
        return "blocked_unsafe_phone_summary"
    if delivery_success_claimed:
        return "blocked_delivery_success_claim"
    if _needs_completion_material(state_summary, "dropoff") and dropoff["material_status"] == "not_provided":
        missing.append("dropoff_completion:not_provided")
    if _needs_completion_material(state_summary, "cancel") and cancel["material_status"] == "not_provided":
        missing.append("cancel_completion:not_provided")
    if missing:
        return "blocked_missing_completion_materials"
    if failure_reason:
        return "failed_with_recovery_reason" if recovery_reason else "blocked_missing_completion_materials"
    return "completed_not_proven"


def _phone_safe_summary(
    verdict: str,
    evidence_ref: str,
    dropoff: dict[str, Any],
    cancel: dict[str, Any],
    failure_reason: str,
    recovery_reason: str,
    steps: list[str],
) -> dict[str, Any]:
    # 手机摘要只输出 completion signal 必要字段，不包含 raw artifact 或控制细节。
    return {
        "schema": COMPLETION_SCHEMA,
        "evidence_boundary": COMPLETION_BOUNDARY,
        "status": verdict,
        "completion_verdict": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "dropoff_completion": {
            "material_status": dropoff.get("material_status", ""),
            "completion_claimed": bool(dropoff.get("completion_claimed", False)),
        },
        "cancel_completion": {
            "material_status": cancel.get("material_status", ""),
            "completion_claimed": bool(cancel.get("completion_claimed", False)),
        },
        "failure_reason": failure_reason,
        "recovery_reason": recovery_reason,
        "operator_next_steps": steps[:3],
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "completion_signal_metadata_only_not_delivery_success",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_completion_signal(
    route_status_json: str,
    task_record_json: str,
    completion_summary_json: str,
    dropoff_completion_json: str = "",
    cancel_completion_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], int]:
    route_payload, route_issue = _load_json(route_status_json, "route_status")
    task_payload, task_issue = _load_json(task_record_json, "task_record")
    summary_payload, summary_issue = _load_json(completion_summary_json, "completion_summary")
    dropoff_payload, dropoff_issue = _load_json(dropoff_completion_json, "dropoff_completion")
    cancel_payload, cancel_issue = _load_json(cancel_completion_json, "cancel_completion")

    route_source = _source_state("route_status", route_status_json, route_payload, route_issue, True)
    task_source = _source_state("task_record", task_record_json, task_payload, task_issue, True)
    summary_source = _source_state("completion_summary", completion_summary_json, summary_payload, summary_issue, True)
    dropoff_source = _source_state("dropoff_completion", dropoff_completion_json, dropoff_payload, dropoff_issue, False)
    cancel_source = _source_state("cancel_completion", cancel_completion_json, cancel_payload, cancel_issue, False)
    sources = [route_source, task_source, summary_source, dropoff_source, cancel_source]

    requested_ref = _safe_ref(evidence_ref) or _first_text(
        route_source.get("evidence_ref"),
        task_source.get("evidence_ref"),
        summary_source.get("evidence_ref"),
        dropoff_source.get("evidence_ref"),
        cancel_source.get("evidence_ref"),
        default="",
    )
    fixed_route_summary = _route_summary(route_payload, route_source)
    task_record_summary = _task_record_summary(task_payload, task_source)
    state_transition_summary = _state_transition_summary(task_payload)
    dropoff_completion = _completion_summary("dropoff", dropoff_payload, dropoff_source)
    cancel_completion = _completion_summary("cancel", cancel_payload, cancel_source)
    missing = _required_missing(sources)
    mismatches = _mismatch_reasons(sources, requested_ref)
    unsafe = any(_has_forbidden_copy(payload) for payload in (route_payload, task_payload, summary_payload, dropoff_payload, cancel_payload) if payload)
    delivery_success_claimed = _input_claims_delivery_success([route_payload, task_payload, summary_payload, dropoff_payload, cancel_payload])
    failure_reason = _safe_text(_first_text(task_record_summary.get("failure_reason"), fixed_route_summary.get("failure_code"), default=""))
    recovery_reason = _safe_text(task_record_summary.get("recovery_reason", ""))
    completion_verdict = _verdict(
        sources,
        state_transition_summary,
        dropoff_completion,
        cancel_completion,
        missing,
        mismatches,
        unsafe,
        delivery_success_claimed,
        failure_reason,
        recovery_reason,
    )
    source_steps = _source_steps(summary_payload, task_payload)
    operator_next_steps = _operator_next_steps(completion_verdict, requested_ref, source_steps, missing, mismatches)
    phone_summary = _phone_safe_summary(
        completion_verdict,
        requested_ref,
        dropoff_completion,
        cancel_completion,
        failure_reason,
        recovery_reason,
        operator_next_steps,
    )
    if _has_forbidden_copy(phone_summary):
        completion_verdict = "blocked_unsafe_phone_summary"
        operator_next_steps = _operator_next_steps(completion_verdict, requested_ref, [], missing, mismatches)
        phone_summary = _phone_safe_summary(
            completion_verdict,
            requested_ref,
            dropoff_completion,
            cancel_completion,
            failure_reason,
            recovery_reason,
            operator_next_steps,
        )

    artifact = {
        "schema": COMPLETION_SCHEMA,
        "schema_version": COMPLETION_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": COMPLETION_BOUNDARY,
        "same_evidence_ref_required": True,
        "evidence_ref": requested_ref,
        "completion_verdict": completion_verdict,
        "fixed_route_summary": fixed_route_summary,
        "task_record_summary": task_record_summary,
        "state_transition_summary": state_transition_summary,
        "dropoff_completion": dropoff_completion,
        "cancel_completion": cancel_completion,
        "failure_reason": failure_reason,
        "recovery_reason": recovery_reason,
        "materials_status": {
            "source_materials": sources,
            "completion_source_material_status": _completion_source_material_status(summary_payload),
            "missing_materials": missing,
            "mismatch_reasons": mismatches,
            "unsafe_phone_summary": bool(unsafe),
            "delivery_success_claimed_by_input": bool(delivery_success_claimed),
        },
        "operator_next_steps": operator_next_steps,
        "phone_safe_summary": phone_summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "wave_rover",
            "hardware",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
        ],
        "primary_actions_enabled": False,
        "delivery_success": False,
    }
    artifact = _safe_value(artifact)
    if _has_forbidden_copy(artifact):
        artifact["completion_verdict"] = "blocked_unsafe_phone_summary"
        artifact["phone_safe_summary"]["status"] = "blocked_unsafe_phone_summary"
        artifact["phone_safe_summary"]["completion_verdict"] = "blocked_unsafe_phone_summary"
    return artifact, 0


def write_completion_signal(artifact: dict[str, Any], output: str) -> None:
    # output 为空时只打印 stdout；指定路径时自动建目录方便 sprint 验收。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只读 JSON 文件；--once-json 便于 Robot/Full-stack worker 直接拿 fixture。
    parser = argparse.ArgumentParser(description="Generate a route/task completion signal artifact")
    parser.add_argument("--route-status-json", required=True, help="fixed-route status or replay JSON path")
    parser.add_argument("--task-record-json", required=True, help="task record JSON path")
    parser.add_argument(
        "--completion-summary-json",
        required=True,
        help="route_task_field_run_reconciliation, review, or intake summary JSON path",
    )
    parser.add_argument("--dropoff-completion-json", default="", help="optional dropoff completion material JSON path")
    parser.add_argument("--cancel-completion-json", default="", help="optional cancel completion material JSON path")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for all loaded materials")
    parser.add_argument("--output", default="", help="optional completion signal JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print completion signal JSON to stdout and exit")
    args = parser.parse_args()

    artifact, exit_code = build_completion_signal(
        args.route_status_json,
        args.task_record_json,
        args.completion_summary_json,
        args.dropoff_completion_json,
        args.cancel_completion_json,
        args.evidence_ref,
    )
    write_completion_signal(artifact, args.output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task completion signal: completion_signal_file:{_safe_ref(args.output)}")
        print(f"completion_verdict: {artifact['completion_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
