#!/usr/bin/env python3
"""生成 route/task field-run console artifact。

该工具只读取 PC/Docker 本地 JSON 材料，把 execution pack、route status、
task record 和 completion signal 汇总成操作员现场运行准备 console。它不访问
ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、云、OSS/CDN、
DB/queue 或 4G。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 顶层 schema/boundary 是 diagnostics/mobile 后续只读消费的稳定契约。
CONSOLE_SCHEMA = "trashbot.route_task_field_run_console.v1"
CONSOLE_SCHEMA_VERSION = 1
CONSOLE_BOUNDARY = "software_proof_docker_route_task_field_run_console_gate"

# 上游材料必须来自明确的白名单；未知 schema 宁可 blocked，不猜字段语义。
PACK_SCHEMA = "trashbot.route_task_field_run_execution_pack.v1"
PACK_BOUNDARY = "software_proof_docker_route_task_field_run_execution_pack_gate"
ROUTE_SCHEMAS = {
    "trashbot.fixed_route_status.v1",
    "trashbot.fixed_route_replay.v1",
    "trashbot.pc_route_debug_console.v1",
}
TASK_RECORD_SCHEMAS = {"trashbot.task_record.v1", "trashbot.task_record"}
COMPLETION_SCHEMA = "trashbot.route_task_completion_signal.v1"
COMPLETION_BOUNDARY = "software_proof_docker_route_task_completion_signal_gate"

# not_proven 固定列出真实能力缺口，避免 console 被误读为上车结果。
NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "wave_rover_motion",
    "real_uart_feedback",
    "real_hil_pass",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# rg 验收会查 delivery_success=false；这里也作为人工阅读边界提示。
BOUNDARY_NOTE = "Docker/local software proof only; delivery_success=false; primary_actions_enabled=false"

# phone/operator 摘要不能带凭证、控制 topic、硬件链路或 raw 调试材料。
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

# 脱敏覆盖凭证、DB/queue URL、控制 topic、设备路径、平台名和 raw 文本。
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
    # UTC 时间戳让不同 PC/Docker 主机生成的 artifact 可以稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本统一脱敏，避免 console 成为敏感材料扩散渠道。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 本机绝对路径不应进入 operator/mobile 摘要，只保留 basename 作为 run 线索。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 兼容上游字符串/list 两种形态，并限制条数，防止复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 最终输出递归脱敏，防止新增字段绕过局部 helper。
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
    # forbidden copy 检查需要稳定字符串，不可编码对象按脱敏文本处理。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 命中禁词时必须 fail closed，而不是继续展示可疑摘要。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON、非 object 都转成 blocked console，不抛未处理异常。
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
    # 上游 nested summary 只有 object 才可信，其它形态按缺失处理。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # 同一字段可能在顶层、route_progress 或 phone summary；取第一个非空值。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _extract_evidence_ref(payload: dict[str, Any]) -> str:
    # same evidence_ref 是本 gate 的核心约束，尽量兼容既有 artifact 形态。
    route_progress = _dict(payload, "route_progress")
    phone = _dict(payload, "phone_safe_summary") or _dict(payload, "mobile_readonly_summary")
    task_result = _dict(payload, "task_result") or _dict(payload, "action_result")
    manifest = _dict(payload, "field_run_manifest")
    return _safe_ref(
        _first_text(
            payload.get("evidence_ref"),
            route_progress.get("evidence_ref"),
            phone.get("evidence_ref"),
            task_result.get("evidence_ref"),
            manifest.get("evidence_ref"),
            default="",
        )
    )


def _schema_status(payload: dict[str, Any], label: str) -> str:
    # 有 schema 时必须命中白名单；无 schema 只接受足够明确的兼容摘要。
    schema = str(payload.get("schema", "")).strip()
    boundary = str(payload.get("evidence_boundary", "")).strip()
    if label == "execution_pack":
        return "supported" if schema == PACK_SCHEMA and boundary == PACK_BOUNDARY else "unsupported"
    if label == "route_status":
        if schema:
            return "supported" if schema in ROUTE_SCHEMAS else "unsupported"
        return "compatible_summary" if (_dict(payload, "route_progress") or payload.get("software_proof")) else "unsupported"
    if label == "task_record":
        if schema:
            return "supported" if schema in TASK_RECORD_SCHEMAS else "unsupported"
        return "compatible_summary" if (_dict(payload, "route_progress") or payload.get("state_transition_history")) else "unsupported"
    if label == "completion_signal":
        return "supported" if schema == COMPLETION_SCHEMA and boundary == COMPLETION_BOUNDARY else "unsupported"
    return "unsupported"


def _source_state(label: str, path: str, payload: dict[str, Any], load_issue: str) -> dict[str, Any]:
    # source_state 只暴露白名单元数据，不复制 raw JSON。
    schema_status = "" if load_issue else _schema_status(payload, label)
    return {
        "name": label,
        "ref": _safe_ref(path),
        "load_status": "blocked" if load_issue else "loaded",
        "load_issue": load_issue,
        "schema": _safe_text(payload.get("schema", "")) if payload else "",
        "schema_status": schema_status,
        "evidence_boundary": _safe_text(payload.get("evidence_boundary", "")) if payload else "",
        "evidence_ref": _extract_evidence_ref(payload) if payload else "",
    }


def _execution_pack_summary(payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # execution pack 摘要只取现场执行目录与命令计数，不复制完整清单。
    manifest = _dict(payload, "field_run_manifest")
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "overall_status": _safe_text(payload.get("overall_status", "")),
        "execution_state": _safe_text(manifest.get("execution_state", "")),
        "required_material_count": len(_safe_list(manifest.get("required_material_names"))),
        "first_run_command_count": len(_safe_list(payload.get("first_run_commands"))),
        "rerun_command_count": len(_safe_list(payload.get("rerun_commands"))),
    }


def _route_status_summary(payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # route summary 聚焦 fixed-route/replay 关键字段，避免输出完整 status。
    route_progress = _dict(payload, "route_progress")
    proof = _dict(payload, "software_proof") or _dict(payload, "replay")
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "route_status": _safe_text(_first_text(payload.get("status"), payload.get("state"), route_progress.get("status"), default="")),
        "checkpoint": _safe_text(_first_text(payload.get("checkpoint"), route_progress.get("checkpoint"), route_progress.get("checkpoint_id"), default="")),
        "current_index": route_progress.get("current_index", payload.get("current_index", "")),
        "target": _safe_text(_first_text(payload.get("target"), route_progress.get("target"), route_progress.get("target_id"), default="")),
        "failure_code": _safe_text(_first_text(payload.get("failure_code"), route_progress.get("failure_code"), default="")),
        "replay_status": _safe_text(_first_text(proof.get("status"), proof.get("overall_status"), default="")),
    }


def _state_history(payload: dict[str, Any]) -> list[str]:
    # 状态历史压成短文本序列，console 只需要判断路径是否进入关键分支。
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
    # task summary 保留状态机和失败/恢复线索，不把 action raw payload 展示给操作员。
    result = _dict(payload, "task_result") or _dict(payload, "action_result") or _dict(payload, "result")
    states = _state_history(payload)
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "task_id": _safe_text(payload.get("task_id", "")),
        "task_status": _safe_text(_first_text(payload.get("status"), payload.get("overall_status"), result.get("status"), default="")),
        "failure_reason": _safe_text(_first_text(payload.get("failure_reason"), result.get("failure_reason"), result.get("error_message"), default="")),
        "recovery_reason": _safe_text(_first_text(payload.get("recovery_reason"), result.get("recovery_reason"), result.get("recovery_action"), default="")),
        "state_transition_count": len(states),
        "last_state": states[-1] if states else "",
    }


def _completion_signal_summary(payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # completion signal 是只读完成信号；console 只能复述 verdict 和材料状态。
    materials = _dict(payload, "materials_status")
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "completion_verdict": _safe_text(payload.get("completion_verdict", "")),
        "missing_materials_count": len(_safe_list(materials.get("missing_materials"))),
        "mismatch_reasons_count": len(_safe_list(materials.get("mismatch_reasons"))),
        "failure_reason": _safe_text(payload.get("failure_reason", "")),
        "recovery_reason": _safe_text(payload.get("recovery_reason", "")),
    }


def _completion_material(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # dropoff/cancel 即使 claimed，也只能是 material_present_not_proven。
    material = _dict(payload, key)
    return {
        "material_status": _safe_text(material.get("material_status", "not_provided")),
        "completion_claimed": bool(material.get("completion_claimed", False)),
        "completion_evidence_boundary": "software_material_only_not_real_completion",
        "delivery_success": False,
    }


def _required_missing(sources: list[dict[str, Any]]) -> list[str]:
    # required source 缺失、坏 JSON、unsupported schema 或缺 ref 都是硬阻断。
    missing: list[str] = []
    for source in sources:
        if source["load_status"] != "loaded":
            missing.append(f"{source['name']}:{source['load_issue']}")
            continue
        if source["schema_status"] == "unsupported":
            missing.append(f"{source['name']}:unsupported_schema")
        if not source["evidence_ref"]:
            missing.append(f"{source['name']}:missing_evidence_ref")
    return missing


def _mismatch_reasons(sources: list[dict[str, Any]], expected_ref: str) -> list[str]:
    # 所有材料必须属于同一个 run；不同 evidence_ref 不能拼成现场成功证据。
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


def _input_claims_delivery_success(payloads: list[dict[str, Any]]) -> bool:
    # 任何上游 delivery_success=true 都是越界成功声明，必须 fail closed。
    for payload in payloads:
        phone = _dict(payload, "phone_safe_summary") or _dict(payload, "mobile_readonly_summary")
        if payload.get("delivery_success") is True or phone.get("delivery_success") is True:
            return True
    return False


def _input_enables_primary_actions(payloads: list[dict[str, Any]]) -> bool:
    # console 是 PC 只读 artifact；上游若放行动作，不能继续展示为 ready。
    for payload in payloads:
        phone = _dict(payload, "phone_safe_summary") or _dict(payload, "mobile_readonly_summary")
        if payload.get("primary_actions_enabled") is True or phone.get("primary_actions_enabled") is True:
            return True
    return False


def _field_run_plan(verdict: str, evidence_ref: str, pack_payload: dict[str, Any]) -> list[dict[str, Any]]:
    # field_run_plan 面向操作员，描述下一步该准备什么，不触发任何控制动作。
    ref = evidence_ref or "<same_evidence_ref>"
    source_commands = _safe_list(pack_payload.get("first_run_commands"), limit=4)
    if not source_commands:
        source_commands = [
            f"Prepare route status JSON for evidence_ref={ref}.",
            f"Prepare task record JSON for evidence_ref={ref}.",
            f"Prepare completion signal JSON for evidence_ref={ref}.",
        ]
    return [
        {
            "step": "verify_same_evidence_ref",
            "status": "ready" if verdict == "field_run_materials_prepared_not_proven" else "blocked",
            "instruction": f"Keep execution pack, route status, task record, and completion signal under evidence_ref={ref}.",
        },
        {
            "step": "prepare_field_run_materials",
            "status": "planned_not_executed",
            "instruction": "Use the execution pack ordering to prepare local JSON materials before any real field run.",
            "source_commands": source_commands[:4],
        },
        {
            "step": "operator_review_before_real_run",
            "status": "manual_review_required",
            "instruction": "Review blocked/not_proven items before collecting real Nav2/fixed-route, dropoff/cancel, HIL, or delivery evidence.",
        },
    ]


def _capture_checklist(evidence_ref: str) -> list[dict[str, Any]]:
    # capture_checklist 是采集模板，不读取 ROS/Nav2/硬件；现场后续按同 ref 补真实材料。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        {
            "name": "route_status_json",
            "required": True,
            "same_evidence_ref_required": True,
            "capture_note": f"Collect fixed-route status/replay JSON for evidence_ref={ref}; do not mark delivery_success=true.",
        },
        {
            "name": "task_record_json",
            "required": True,
            "same_evidence_ref_required": True,
            "capture_note": f"Collect task state transitions and failure/recovery reason for evidence_ref={ref}.",
        },
        {
            "name": "completion_signal_json",
            "required": True,
            "same_evidence_ref_required": True,
            "capture_note": f"Collect completion signal under evidence_ref={ref}; dropoff/cancel completion remains not_proven here.",
        },
        {
            "name": "operator_notes",
            "required": True,
            "same_evidence_ref_required": True,
            "capture_note": "Record only phone-safe notes; omit credentials, local device paths, raw robot response, ROS topics, and complete artifacts.",
        },
    ]


def _operator_next_steps(verdict: str, evidence_ref: str, missing: list[str], mismatches: list[str]) -> list[str]:
    # next steps 直接指向修复动作，避免操作员从 JSON 细节猜 blocked 原因。
    ref = evidence_ref or "<same_evidence_ref>"
    if verdict.startswith("blocked_missing") or verdict == "blocked_bad_json":
        steps = [
            f"Rebuild all required route/task field-run console inputs under evidence_ref={ref}.",
            "Rerun the console after missing, unreadable, or bad JSON materials are repaired.",
            "Keep delivery_success=false until real field evidence exists.",
        ]
    elif verdict == "blocked_mismatch_evidence_ref":
        steps = [
            f"Re-export execution pack, route status, task record, and completion signal under one evidence_ref={ref}.",
            "Do not combine materials from different route/task runs.",
            "Rerun this console after same evidence_ref alignment is restored.",
        ]
    elif verdict == "blocked_unsafe_summary":
        steps = [
            "Remove unsafe summary text from source materials.",
            "Regenerate summaries without credentials, raw robot response, ROS topics, serial/UART, WAVE ROVER, paths, tracebacks, or checksums.",
            "Rerun this console before diagnostics or mobile display.",
        ]
    elif verdict == "blocked_delivery_success_claim":
        steps = [
            "Remove delivery_success=true from Docker/local source materials.",
            "Use this console only for software-proof field-run preparation.",
            "Collect real field, dropoff/cancel, HIL, and delivery evidence before any success claim.",
        ]
    else:
        steps = [
            f"Use this console as the PC/operator field-run preparation artifact for evidence_ref={ref}.",
            "Collect real route/task materials separately before claiming Nav2/fixed-route, dropoff/cancel, HIL, or delivery success.",
            "Keep mobile and diagnostics panels read-only until a separate real evidence gate passes.",
        ]
    if missing:
        steps.append(f"Missing or blocked materials: {', '.join(missing[:4])}")
    if mismatches:
        steps.append(f"Evidence mismatch: {', '.join(mismatches[:2])}")
    return [_safe_text(step) for step in steps[:5]]


def _console_verdict(
    sources: list[dict[str, Any]],
    missing: list[str],
    mismatches: list[str],
    unsafe: bool,
    delivery_success_claimed: bool,
    primary_actions_enabled: bool,
) -> str:
    # verdict 优先级保持 fail-closed：可读性、schema、同 ref、安全、越界成功声明。
    load_issues = {source["load_issue"] for source in sources if source["load_issue"]}
    if any(issue.endswith("_bad_json") or issue.endswith("_not_object") or issue.endswith("_read_error") for issue in load_issues):
        return "blocked_bad_json"
    if missing:
        for label in ("execution_pack", "route_status", "task_record", "completion_signal"):
            if any(item.startswith(f"{label}:") for item in missing):
                return f"blocked_missing_{label}"
    if mismatches:
        return "blocked_mismatch_evidence_ref"
    if unsafe or primary_actions_enabled:
        return "blocked_unsafe_summary"
    if delivery_success_claimed:
        return "blocked_delivery_success_claim"
    return "field_run_materials_prepared_not_proven"


def _robot_diagnostics_summary(verdict: str, evidence_ref: str, missing: list[str], mismatches: list[str]) -> dict[str, Any]:
    # diagnostics summary 是只读元数据，不是 command/status/ACK envelope。
    return {
        "schema": CONSOLE_SCHEMA,
        "evidence_boundary": CONSOLE_BOUNDARY,
        "status": verdict,
        "console_verdict": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "missing_materials": missing[:8],
        "mismatch_reasons": mismatches[:8],
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "field_run_console_metadata_only_not_delivery_success",
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def _mobile_readonly_summary(verdict: str, evidence_ref: str, steps: list[str]) -> dict[str, Any]:
    # mobile 只显示白名单摘要；不能复制 raw artifact 或放行任何动作。
    return {
        "schema": CONSOLE_SCHEMA,
        "evidence_boundary": CONSOLE_BOUNDARY,
        "status": verdict,
        "console_verdict": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "operator_next_steps": steps[:3],
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def build_field_run_console(
    execution_pack_json: str,
    route_status_json: str,
    task_record_json: str,
    completion_signal_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], int]:
    pack_payload, pack_issue = _load_json(execution_pack_json, "execution_pack")
    route_payload, route_issue = _load_json(route_status_json, "route_status")
    task_payload, task_issue = _load_json(task_record_json, "task_record")
    completion_payload, completion_issue = _load_json(completion_signal_json, "completion_signal")

    pack_source = _source_state("execution_pack", execution_pack_json, pack_payload, pack_issue)
    route_source = _source_state("route_status", route_status_json, route_payload, route_issue)
    task_source = _source_state("task_record", task_record_json, task_payload, task_issue)
    completion_source = _source_state("completion_signal", completion_signal_json, completion_payload, completion_issue)
    sources = [pack_source, route_source, task_source, completion_source]

    requested_ref = _safe_ref(evidence_ref) or _first_text(
        pack_source.get("evidence_ref"),
        route_source.get("evidence_ref"),
        task_source.get("evidence_ref"),
        completion_source.get("evidence_ref"),
        default="",
    )
    missing = _required_missing(sources)
    mismatches = _mismatch_reasons(sources, requested_ref)
    payloads = [pack_payload, route_payload, task_payload, completion_payload]
    unsafe = any(_has_forbidden_copy(payload) for payload in payloads if payload)
    delivery_success_claimed = _input_claims_delivery_success(payloads)
    primary_actions_enabled = _input_enables_primary_actions(payloads)
    console_verdict = _console_verdict(
        sources,
        missing,
        mismatches,
        unsafe,
        delivery_success_claimed,
        primary_actions_enabled,
    )

    operator_next_steps = _operator_next_steps(console_verdict, requested_ref, missing, mismatches)
    dropoff_completion = _completion_material(completion_payload, "dropoff_completion")
    cancel_completion = _completion_material(completion_payload, "cancel_completion")
    robot_summary = _robot_diagnostics_summary(console_verdict, requested_ref, missing, mismatches)
    mobile_summary = _mobile_readonly_summary(console_verdict, requested_ref, operator_next_steps)

    artifact = {
        "schema": CONSOLE_SCHEMA,
        "schema_version": CONSOLE_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": CONSOLE_BOUNDARY,
        "same_evidence_ref_required": True,
        "evidence_ref": requested_ref,
        "console_verdict": console_verdict,
        "field_run_plan": _field_run_plan(console_verdict, requested_ref, pack_payload),
        "capture_checklist": _capture_checklist(requested_ref),
        "execution_pack_summary": _execution_pack_summary(pack_payload, pack_source),
        "route_status_summary": _route_status_summary(route_payload, route_source),
        "task_record_summary": _task_record_summary(task_payload, task_source),
        "completion_signal_summary": _completion_signal_summary(completion_payload, completion_source),
        "dropoff_completion": dropoff_completion,
        "cancel_completion": cancel_completion,
        "operator_next_steps": operator_next_steps,
        "robot_diagnostics_summary": robot_summary,
        "mobile_readonly_summary": mobile_summary,
        "materials_status": {
            "source_materials": sources,
            "missing_materials": missing,
            "mismatch_reasons": mismatches,
            "unsafe_summary": bool(unsafe),
            "delivery_success_claimed_by_input": bool(delivery_success_claimed),
            "primary_actions_enabled_by_input": bool(primary_actions_enabled),
        },
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
        "boundary_note": BOUNDARY_NOTE,
        "primary_actions_enabled": False,
        "delivery_success": False,
    }
    artifact = _safe_value(artifact)
    if _has_forbidden_copy(artifact):
        # 最终防线保证输出不会带敏感 copy；状态也必须回落到 blocked。
        artifact["console_verdict"] = "blocked_unsafe_summary"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_summary"
        artifact["robot_diagnostics_summary"]["console_verdict"] = "blocked_unsafe_summary"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_summary"
        artifact["mobile_readonly_summary"]["console_verdict"] = "blocked_unsafe_summary"
    return artifact, 0


def write_field_run_console(artifact: dict[str, Any], output: str) -> None:
    # output 为空时只走 stdout；指定路径时创建父目录，方便 sprint 验收。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只读四份 JSON；--once-json 用于 sprint 验收或 downstream fixture 直接消费。
    parser = argparse.ArgumentParser(description="Generate a route/task field-run console artifact")
    parser.add_argument("--execution-pack-json", required=True, help="route_task_field_run_execution_pack JSON path")
    parser.add_argument("--route-status-json", required=True, help="fixed-route status or replay JSON path")
    parser.add_argument("--task-record-json", required=True, help="task record JSON path")
    parser.add_argument("--completion-signal-json", required=True, help="route_task_completion_signal JSON path")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for all loaded materials")
    parser.add_argument("--output", default="", help="optional field-run console JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print field-run console JSON to stdout and exit")
    args = parser.parse_args()

    artifact, exit_code = build_field_run_console(
        args.execution_pack_json,
        args.route_status_json,
        args.task_record_json,
        args.completion_signal_json,
        args.evidence_ref,
    )
    write_field_run_console(artifact, args.output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field-run console: console_file:{_safe_ref(args.output)}")
        print(f"console_verdict: {artifact['console_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
