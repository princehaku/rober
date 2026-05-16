#!/usr/bin/env python3
"""生成 route/task terminal completion rehearsal artifact。

该工具只读取 PC/Docker 本地 JSON 材料，把 route status、task record、
既有 route_task_completion_signal 以及可选 dropoff/cancel material summary
复账成终态 rehearsal。它不访问 ROS graph、Nav2 runtime、硬件、外部云或手机。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本轮新增独立 contract，避免下游把 completion signal 误当成终态复账。
REHEARSAL_SCHEMA = "trashbot.route_task_terminal_completion_rehearsal.v1"
REHEARSAL_SUMMARY_SCHEMA = "trashbot.route_task_terminal_completion_rehearsal_summary.v1"
REHEARSAL_SCHEMA_VERSION = 1
REHEARSAL_BOUNDARY = "software_proof_docker_route_task_terminal_completion_rehearsal_gate"

# 上游只接受已知 route/task/completion signal 形态；未知 schema 一律 blocked。
ROUTE_SCHEMAS = {
    "trashbot.fixed_route_status.v1",
    "trashbot.fixed_route_replay.v1",
    "trashbot.pc_route_debug_console.v1",
}
TASK_SCHEMAS = {"trashbot.task_record.v1", "trashbot.task_record"}
COMPLETION_SIGNAL_SCHEMAS = {
    "trashbot.route_task_completion_signal.v1",
    "trashbot.route_task_completion_signal_summary.v1",
}
COMPLETION_SIGNAL_BOUNDARY = "software_proof_docker_route_task_completion_signal_gate"
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

# not_proven 是产品边界字段，不允许被上游材料覆盖成真实成功。
NOT_PROVEN = (
    "real_delivery",
    "real_terminal_completion",
    "real_dropoff_completion",
    "real_cancel_completion",
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "real_elevator_field_pass",
    "real_phone_device_or_browser",
    "real_wave_rover_or_uart_feedback",
    "real_hil_pass",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 输出白名单之外的敏感/控制/硬件词必须触发 fail closed。
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

# 成功文案不能进入 rehearsal；但 delivery_success=false 是 contract 字段，不能误拦。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bterminal\s+completion\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\broute/elevator\s+field\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bhil[_ -]?pass\s*[:=]\s*true\b"),
)

# phone/support 文本中的完整本机路径会泄露环境；route evidence_ref 会单独 safe_ref。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# 先脱敏再输出，随后再扫描 forbidden copy 判断是否需要 blocked。
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
    (re.compile(r"(?i)\bWAVE\s+ROVER\b"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 让多台 PC/Docker 产物能稳定排序，不依赖本机时区。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本先脱敏，防止 operator note 绕过输出白名单。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref/路径只保留 basename，避免把本机目录暴露给 diagnostics/mobile。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 上游字段可能是字符串或 list；限制数量避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 最终写盘前递归脱敏，防止新增嵌套字段遗漏处理。
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
    # 稳定 JSON 字符串用于安全扫描；不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # forbidden copy 命中表示不能安全展示，必须 blocked。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_success_or_control_claim(payloads: list[dict[str, Any]]) -> bool:
    # 任意上游打开动作或声明成功，都不能被 rehearsal 继续放大。
    for payload in payloads:
        phone = _dict(payload, "phone_safe_summary")
        if payload.get("delivery_success") is True or phone.get("delivery_success") is True:
            return True
        if payload.get("primary_actions_enabled") is True or phone.get("primary_actions_enabled") is True:
            return True
        encoded = _encoded(payload)
        if any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS):
            return True
    return False


def _has_raw_path_copy(payloads: list[dict[str, Any]]) -> bool:
    # 只扫描 phone/support/operator 文本，避免 route status 的原始 evidence_ref 被误拦。
    text_fragments: list[str] = []
    for payload in payloads:
        phone = _dict(payload, "phone_safe_summary") or _dict(payload, "support_safe_summary")
        text_fragments.append(_encoded(phone))
        text_fragments.extend(_safe_list(payload.get("operator_next_steps"), limit=8))
        text_fragments.extend(_safe_list(payload.get("safe_copy"), limit=8))
    encoded = "\n".join(text_fragments)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 读取失败转成材料状态，不让 CLI 抛异常中断批处理。
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
    # 上游 JSON 层级会漂移；非 object 字段统一按空对象处理。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # 多源字段取第一个非空值，保留旧 artifact 兼容性。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _extract_evidence_ref(payload: dict[str, Any]) -> str:
    # 同一 run 主键可能来自顶层、route_progress、result 或手机摘要。
    route_progress = _dict(payload, "route_progress")
    task = _dict(payload, "task")
    result = _dict(payload, "task_result") or _dict(payload, "action_result") or _dict(payload, "result")
    phone = _dict(payload, "phone_safe_summary") or _dict(payload, "mobile_readonly_summary")
    return _safe_ref(
        _first_text(
            payload.get("evidence_ref"),
            route_progress.get("evidence_ref"),
            task.get("evidence_ref"),
            result.get("evidence_ref"),
            phone.get("evidence_ref"),
            default="",
        )
    )


def _schema_status(payload: dict[str, Any], label: str) -> str:
    # required/optional source 都必须白名单化；兼容无 schema 的旧摘要只接受明确字段。
    schema = str(payload.get("schema", "")).strip()
    boundary = str(payload.get("evidence_boundary", "")).strip()
    if label == "route_status":
        if schema:
            return "supported" if schema in ROUTE_SCHEMAS else "unsupported"
        return "compatible_summary" if (_dict(payload, "route_progress") or payload.get("software_proof")) else "unsupported"
    if label == "task_record":
        if schema:
            return "supported" if schema in TASK_SCHEMAS else "unsupported"
        return "compatible_summary" if (_dict(payload, "route_progress") or payload.get("state_transition_history")) else "unsupported"
    if label == "completion_signal":
        if schema:
            schema_ok = schema in COMPLETION_SIGNAL_SCHEMAS
            boundary_ok = not boundary or boundary == COMPLETION_SIGNAL_BOUNDARY
            return "supported" if schema_ok and boundary_ok else "unsupported"
        return "compatible_summary" if any(key in payload for key in ("completion_verdict", "terminal_verdict")) else "unsupported"
    if label == "dropoff_material":
        if schema:
            return "supported" if schema in DROP_COMPLETION_SCHEMAS else "unsupported"
        return "compatible_summary" if any(key in payload for key in ("dropoff_completed", "completion_status", "completed")) else "unsupported"
    if label == "cancel_material":
        if schema:
            return "supported" if schema in CANCEL_COMPLETION_SCHEMAS else "unsupported"
        return "compatible_summary" if any(key in payload for key in ("cancel_completed", "completion_status", "completed")) else "unsupported"
    return "unsupported"


def _source_state(label: str, path: str, payload: dict[str, Any], load_issue: str, required: bool) -> dict[str, Any]:
    # source_state 只暴露材料元数据，不复制 raw JSON。
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


def _state_history(payload: dict[str, Any]) -> list[str]:
    # 状态机历史可能是字符串或 dict；统一压成短状态序列。
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


def _route_summary(payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # route 摘要只保留复账字段，防止完整 status 扩散到手机侧。
    route_progress = _dict(payload, "route_progress")
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "route_status": _safe_text(_first_text(payload.get("status"), route_progress.get("status"), payload.get("overall_status"), default="")),
        "checkpoint": _safe_text(_first_text(payload.get("checkpoint"), route_progress.get("checkpoint"), route_progress.get("checkpoint_id"), default="")),
        "current_index": route_progress.get("current_index", payload.get("current_index", "")),
        "target": _safe_text(_first_text(payload.get("target"), route_progress.get("target"), route_progress.get("target_id"), default="")),
        "failure_code": _safe_text(_first_text(payload.get("failure_code"), route_progress.get("failure_code"), default="")),
    }


def _task_summary(payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # task 摘要聚焦终态、失败和恢复，避免复制完整 task record。
    result = _dict(payload, "task_result") or _dict(payload, "action_result") or _dict(payload, "result")
    states = _state_history(payload)
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "task_id": _safe_text(payload.get("task_id", "")),
        "task_status": _safe_text(_first_text(payload.get("status"), payload.get("overall_status"), result.get("status"), default="")),
        "final_state": _safe_text(_first_text(payload.get("final_state"), result.get("final_state"), states[-1] if states else "", default="")),
        "failure_reason": _safe_text(_first_text(payload.get("failure_reason"), result.get("failure_reason"), result.get("error_message"), default="")),
        "recovery_reason": _safe_text(_first_text(payload.get("recovery_reason"), result.get("recovery_reason"), result.get("recovery_action"), default="")),
        "state_transition_count": len(states),
        "route_progress_present": bool(_dict(payload, "route_progress")),
    }


def _state_transition_summary(payload: dict[str, Any]) -> dict[str, Any]:
    # dropoff/cancel 分支决定 optional 材料是否升级成 required missing。
    states = _state_history(payload)
    upper = [state.upper() for state in states]
    return {
        "states": states[:12],
        "state_transition_count": len(states),
        "final_state": states[-1] if states else "",
        "has_dropoff_state": any("DROPOFF" in state or "DELIVERED" in state for state in upper),
        "has_cancel_state": any("CANCEL" in state for state in upper),
        "has_failure_state": any("ERROR" in state or "FAIL" in state for state in upper),
    }


def _completion_bool(payload: dict[str, Any], kind: str) -> bool:
    # completion material 只记录声明存在；真实完成仍在 not_proven。
    for key in (f"{kind}_completed", "completed", "completion_confirmed"):
        if payload.get(key) is True:
            return True
    status = str(payload.get("completion_status", payload.get("status", ""))).lower()
    return status in {"completed", "confirmed", "done", f"{kind}_completed"}


def _material_summary(kind: str, payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # optional material 存在时也只能是 material_present_not_proven。
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
        "delivery_success": False,
    }


def _completion_signal_summary(payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # 既有 completion signal 是必需上游，但本 gate 不信任其成功声明。
    phone = _dict(payload, "phone_safe_summary")
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_boundary": source.get("evidence_boundary", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "completion_verdict": _safe_text(_first_text(payload.get("completion_verdict"), phone.get("completion_verdict"), phone.get("status"), default="")),
        "dropoff_material_status": _safe_text(
            _first_text(
                _dict(payload, "dropoff_completion").get("material_status"),
                _dict(phone, "dropoff_completion").get("material_status"),
                default="",
            )
        ),
        "cancel_material_status": _safe_text(
            _first_text(
                _dict(payload, "cancel_completion").get("material_status"),
                _dict(phone, "cancel_completion").get("material_status"),
                default="",
            )
        ),
        "source_delivery_success": bool(payload.get("delivery_success", False) or phone.get("delivery_success", False)),
        "source_primary_actions_enabled": bool(payload.get("primary_actions_enabled", False) or phone.get("primary_actions_enabled", False)),
    }


def _source_steps(*payloads: dict[str, Any]) -> list[str]:
    # 继承上游 operator steps，但仍经过脱敏和限长。
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
    # 所有已加载材料必须共享同一 safe evidence_ref。
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


def _append_required_completion_materials(
    state_summary: dict[str, Any],
    dropoff: dict[str, Any],
    cancel: dict[str, Any],
    missing: list[str],
) -> None:
    # 状态机进入 dropoff/cancel 分支时，缺对应材料必须 fail closed。
    if state_summary.get("has_dropoff_state") and dropoff["material_status"] == "not_provided":
        missing.append("dropoff:not_provided")
    if state_summary.get("has_cancel_state") and cancel["material_status"] == "not_provided":
        missing.append("cancel:not_provided")


def _terminal_verdict(
    sources: list[dict[str, Any]],
    missing: list[str],
    mismatches: list[str],
    unsafe: bool,
    success_or_control_claim: bool,
    failure_reason: str,
    recovery_reason: str,
) -> str:
    # verdict 优先级保持 fail-closed，先拦不可读/不可信，再判断材料完整性。
    load_issues = {source["load_issue"] for source in sources if source["load_issue"]}
    if any(issue.endswith("_bad_json") or issue.endswith("_not_object") or issue.endswith("_read_error") for issue in load_issues):
        return "blocked_bad_json"
    if any(source["schema_status"] == "unsupported" for source in sources if source["load_status"] == "loaded"):
        return "blocked_unsupported_schema"
    if mismatches:
        return "blocked_mismatch_evidence_ref"
    if unsafe:
        return "blocked_unsafe_copy"
    if success_or_control_claim:
        return "blocked_success_or_control_claim"
    if missing:
        return "blocked_missing_route_task_terminal_completion_rehearsal"
    if failure_reason:
        return "failed_with_recovery_reason_not_proven" if recovery_reason else "blocked_missing_recovery_reason"
    return "ready_for_terminal_completion_rehearsal_not_proven"


def _operator_next_steps(
    verdict: str,
    evidence_ref: str,
    source_steps: list[str],
    missing: list[str],
    mismatches: list[str],
) -> list[str]:
    # 每个 blocked 分支给出下一步材料动作，避免现场人员从 JSON 猜原因。
    ref = evidence_ref or "<same_evidence_ref>"
    if verdict in {"blocked_missing_route_task_terminal_completion_rehearsal", "blocked_bad_json", "blocked_unsupported_schema"}:
        steps = [
            f"Collect route status, task record, route_task_completion_signal, and required dropoff/cancel materials for evidence_ref={ref}.",
            "Repair missing, bad JSON, or unsupported schemas before rerunning this rehearsal gate.",
            "Keep delivery_success=false and primary_actions_enabled=false until real field evidence exists.",
        ]
    elif verdict == "blocked_mismatch_evidence_ref":
        steps = [
            f"Re-export all route/task/completion/dropoff/cancel materials under one evidence_ref={ref}.",
            "Do not combine terminal materials from different runs.",
            "Rerun this gate after evidence_ref mismatch is cleared.",
        ]
    elif verdict == "blocked_unsafe_copy":
        steps = [
            "Regenerate source summaries without credentials, raw paths, ROS topics, serial/UART, WAVE ROVER, HIL, tracebacks, or success wording.",
            "Only pass phone/support safe JSON into terminal completion rehearsal.",
        ]
    elif verdict == "blocked_success_or_control_claim":
        steps = [
            "Remove delivery_success=true, primary_actions_enabled=true, HIL pass, or success wording from Docker/local source materials.",
            "Use this gate only for software-proof terminal rehearsal.",
        ]
    elif verdict == "blocked_missing_recovery_reason":
        steps = [
            f"Add failure and recovery reason to the task record for evidence_ref={ref}.",
            "Rerun this gate before field-session closeout.",
        ]
    elif verdict == "failed_with_recovery_reason_not_proven":
        steps = source_steps[:2] + [
            f"Review failure/recovery reason for evidence_ref={ref} before another route/task run.",
            "Keep this as failed terminal rehearsal, not delivery success.",
        ]
    else:
        steps = source_steps[:2] + [
            f"Preserve evidence_ref={ref} for the next real route/task/dropoff/cancel field material review.",
            "Treat ready_for_terminal_completion_rehearsal_not_proven as Docker/local contract readiness only.",
        ]
    if missing:
        steps.append(f"Missing or blocked materials: {', '.join(missing[:3])}")
    if mismatches:
        steps.append(f"Evidence mismatch: {', '.join(mismatches[:2])}")

    result: list[str] = []
    for item in steps:
        if item and item not in result:
            result.append(_safe_text(item))
    return result[:5]


def _summary(
    terminal_verdict: str,
    evidence_ref: str,
    dropoff: dict[str, Any],
    cancel: dict[str, Any],
    failure_reason: str,
    recovery_reason: str,
    operator_next_steps: list[str],
) -> dict[str, Any]:
    # summary 是 Robot/mobile 可消费的白名单视图，不包含 raw 输入。
    return {
        "schema": REHEARSAL_SUMMARY_SCHEMA,
        "schema_version": REHEARSAL_SCHEMA_VERSION,
        "evidence_boundary": REHEARSAL_BOUNDARY,
        "terminal_verdict": terminal_verdict,
        "status": terminal_verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "dropoff": {
            "material_status": dropoff.get("material_status", ""),
            "completion_claimed": bool(dropoff.get("completion_claimed", False)),
        },
        "cancel": {
            "material_status": cancel.get("material_status", ""),
            "completion_claimed": bool(cancel.get("completion_claimed", False)),
        },
        "failure_reason": failure_reason,
        "recovery_reason": recovery_reason,
        "operator_next_steps": operator_next_steps[:3],
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_terminal_completion_rehearsal(
    route_status_json: str,
    task_record_json: str,
    completion_signal_json: str,
    dropoff_material_json: str = "",
    cancel_material_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    route_payload, route_issue = _load_json(route_status_json, "route_status")
    task_payload, task_issue = _load_json(task_record_json, "task_record")
    completion_payload, completion_issue = _load_json(completion_signal_json, "completion_signal")
    dropoff_payload, dropoff_issue = _load_json(dropoff_material_json, "dropoff_material")
    cancel_payload, cancel_issue = _load_json(cancel_material_json, "cancel_material")

    route_source = _source_state("route_status", route_status_json, route_payload, route_issue, True)
    task_source = _source_state("task_record", task_record_json, task_payload, task_issue, True)
    completion_source = _source_state("completion_signal", completion_signal_json, completion_payload, completion_issue, True)
    dropoff_source = _source_state("dropoff_material", dropoff_material_json, dropoff_payload, dropoff_issue, False)
    cancel_source = _source_state("cancel_material", cancel_material_json, cancel_payload, cancel_issue, False)
    sources = [route_source, task_source, completion_source, dropoff_source, cancel_source]

    requested_ref = _safe_ref(evidence_ref) or _first_text(
        route_source.get("evidence_ref"),
        task_source.get("evidence_ref"),
        completion_source.get("evidence_ref"),
        dropoff_source.get("evidence_ref"),
        cancel_source.get("evidence_ref"),
        default="",
    )
    route = _route_summary(route_payload, route_source)
    task = _task_summary(task_payload, task_source)
    state = _state_transition_summary(task_payload)
    completion_signal = _completion_signal_summary(completion_payload, completion_source)
    dropoff = _material_summary("dropoff", dropoff_payload, dropoff_source)
    cancel = _material_summary("cancel", cancel_payload, cancel_source)
    missing = _required_missing(sources)
    _append_required_completion_materials(state, dropoff, cancel, missing)
    mismatches = _mismatch_reasons(sources, requested_ref)
    payloads = [payload for payload in (route_payload, task_payload, completion_payload, dropoff_payload, cancel_payload) if payload]
    unsafe = any(_has_forbidden_copy(payload) for payload in payloads) or _has_raw_path_copy(payloads)
    success_or_control_claim = _has_success_or_control_claim(payloads)
    failure_reason = _safe_text(_first_text(task.get("failure_reason"), route.get("failure_code"), default=""))
    recovery_reason = _safe_text(task.get("recovery_reason", ""))
    terminal_verdict = _terminal_verdict(
        sources,
        missing,
        mismatches,
        unsafe,
        success_or_control_claim,
        failure_reason,
        recovery_reason,
    )
    operator_next_steps = _operator_next_steps(
        terminal_verdict,
        requested_ref,
        _source_steps(completion_payload, task_payload),
        missing,
        mismatches,
    )
    summary = _summary(terminal_verdict, requested_ref, dropoff, cancel, failure_reason, recovery_reason, operator_next_steps)

    artifact = {
        "schema": REHEARSAL_SCHEMA,
        "schema_version": REHEARSAL_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": REHEARSAL_BOUNDARY,
        "same_evidence_ref_required": True,
        "evidence_ref": requested_ref,
        "terminal_verdict": terminal_verdict,
        "route_status_summary": route,
        "task_record_summary": task,
        "state_transition_summary": state,
        "completion_signal_summary": completion_signal,
        "dropoff": dropoff,
        "cancel": cancel,
        "failure_reason": failure_reason,
        "recovery_reason": recovery_reason,
        "materials_status": {
            "source_materials": sources,
            "missing_materials": missing,
            "mismatch_reasons": mismatches,
            "unsafe_copy": bool(unsafe),
            "success_or_control_claim": bool(success_or_control_claim),
        },
        "operator_next_steps": operator_next_steps,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
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
            "real_phone",
        ],
        "boundary_note": (
            "route_task_terminal_completion_rehearsal is software proof only; "
            "delivery_success=false; primary_actions_enabled=false; not_proven"
        ),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_forbidden_copy(artifact) or _has_forbidden_copy(summary):
        artifact["terminal_verdict"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["terminal_verdict"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["terminal_verdict"] = "blocked_unsafe_copy"
        summary["terminal_verdict"] = "blocked_unsafe_copy"
        summary["status"] = "blocked_unsafe_copy"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出路径时自动建目录；空路径表示只打印 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只读 JSON 文件；--once-json 便于 Robot/Full-stack 直接拿 fixture。
    parser = argparse.ArgumentParser(description="Generate a route/task terminal completion rehearsal artifact")
    parser.add_argument("--route-status-json", required=True, help="fixed-route status or replay JSON path")
    parser.add_argument("--task-record-json", required=True, help="task record JSON path")
    parser.add_argument("--completion-signal-json", required=True, help="route_task_completion_signal artifact or summary JSON path")
    parser.add_argument("--dropoff-material-json", default="", help="optional dropoff completion material summary JSON path")
    parser.add_argument("--cancel-material-json", default="", help="optional cancel completion material summary JSON path")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for all loaded materials")
    parser.add_argument("--output", default="", help="optional rehearsal artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional rehearsal summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print rehearsal artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_terminal_completion_rehearsal(
        args.route_status_json,
        args.task_record_json,
        args.completion_signal_json,
        args.dropoff_material_json,
        args.cancel_material_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task terminal completion rehearsal: rehearsal_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"rehearsal_summary_file: {_safe_ref(args.summary_output)}")
        print(f"terminal_verdict: {artifact['terminal_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
