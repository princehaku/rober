#!/usr/bin/env python3
"""生成 route/elevator field-session handoff artifact。

该 gate 只读取 PC/Docker 本地 JSON artifact 或 summary，把 PC route debug
console、route completion signal 和 elevator-route reconciliation 汇总成下一次
现场 session 的同一 evidence_ref 交接材料。它不访问 ROS graph、Nav2 runtime、
serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 顶层 schema/boundary 是 Robot diagnostics 和 mobile/web 只读消费的稳定契约。
ARTIFACT_SCHEMA = "trashbot.route_elevator_field_session_handoff.v1"
SUMMARY_SCHEMA = "trashbot.route_elevator_field_session_handoff_summary.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_route_elevator_field_session_handoff_gate"
SOURCE = "software_proof"

# 上游三个材料来自上一轮 PC console、completion signal 和 elevator route 复账。
PC_ROUTE_DEBUG_SCHEMAS = {
    "trashbot.pc_route_debug_console.v1",
    "trashbot.pc_route_debug_console_summary.v1",
}
PC_ROUTE_DEBUG_BOUNDARY = "software_proof_docker_pc_route_debug_console_gate"
ROUTE_COMPLETION_SCHEMAS = {
    "trashbot.route_task_completion_signal.v1",
    "trashbot.route_task_completion_signal_summary.v1",
}
ROUTE_COMPLETION_BOUNDARY = "software_proof_docker_route_task_completion_signal_gate"
ELEVATOR_RECONCILIATION_SCHEMAS = {
    "trashbot.elevator_route_evidence_reconciliation.v1",
    "trashbot.elevator_route_evidence_reconciliation_summary.v1",
}
ELEVATOR_RECONCILIATION_BOUNDARY = "software_proof_docker_elevator_route_evidence_reconciliation_gate"

# 现场 session 必须补齐这些材料；本 CLI 只生成 checklist，不证明材料存在。
REQUIRED_MATERIALS = (
    "nav2_fixed_route_runtime_log.json",
    "route_completion_signal.json",
    "task_record.json",
    "door_state.json",
    "target_floor_confirmation.json",
    "human_assistance_operator_note.md",
    "dropoff_or_cancel_completion.json",
    "delivery_result.json",
    "diagnostics_mobile_safe_summary.json",
)

# not_proven 固定覆盖真实路线、电梯、硬件、手机和 O5 外部材料，防止 handoff 被误读。
NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_record",
    "wave_rover_motion",
    "real_uart_feedback",
    "real_hil_pass",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 任何 phone/operator 摘要命中这些词都必须 blocked，不能把敏感或硬件细节带下游。
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

# 先做脱敏，再用 FORBIDDEN_COPY 和 success claim 检查做最终围栏。
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

# `delivery_success=false` 是允许字段；自由文本或 hil_pass=true 才算越界成功声明。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(completed|complete|success|succeeded)\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
)


def _utc_now() -> str:
    # UTC 时间便于不同 PC/Docker 主机生成的 handoff artifact 稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 输入 JSON 可来自现场电脑；所有自由文本进入输出前都必须先脱敏。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 本机完整路径不进入 diagnostics/mobile，只保留 basename 作为 run 线索。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 兼容字符串/list 两种上游形态，并限长避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 最终输出再递归脱敏一次，防止新增字段绕过局部 helper。
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
    # 安全检查必须覆盖键和值；不可编码对象退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 命中禁词就 fail closed，而不是继续生成可展示摘要。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_success_claim(value: Any) -> bool:
    # 防止 “not_proven handoff” 被自由文本升级成完成/成功/HIL 通过。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只消费 object summary；其它形态按空对象处理，避免复制 raw 字段。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # schema/status/evidence_ref 可能在顶层或 summary；取第一个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都生成 blocked handoff，不抛未处理异常。
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


def _source_summary(payload: dict[str, Any]) -> dict[str, Any]:
    # 支持直接传 summary，也支持 artifact 内嵌 phone/mobile/diagnostics 摘要。
    if not payload:
        return {}
    schema = str(payload.get("schema", "")).strip()
    if schema in PC_ROUTE_DEBUG_SCHEMAS | ROUTE_COMPLETION_SCHEMAS | ELEVATOR_RECONCILIATION_SCHEMAS:
        return payload
    for key in ("phone_safe_summary", "mobile_readonly_summary", "robot_diagnostics_summary"):
        summary = _dict(payload, key)
        if summary:
            return summary
    return payload


def _expected_contract(label: str) -> tuple[set[str], str]:
    # 每个 source 的 schema/boundary 白名单不同；不要在调用处分散硬编码。
    if label == "pc_route_debug_console":
        return PC_ROUTE_DEBUG_SCHEMAS, PC_ROUTE_DEBUG_BOUNDARY
    if label == "route_completion_signal":
        return ROUTE_COMPLETION_SCHEMAS, ROUTE_COMPLETION_BOUNDARY
    return ELEVATOR_RECONCILIATION_SCHEMAS, ELEVATOR_RECONCILIATION_BOUNDARY


def _extract_evidence_ref(payload: dict[str, Any], summary: dict[str, Any]) -> str:
    # evidence_ref 可能藏在 route_progress、manifest 或 summary；统一转 safe ref。
    route_progress = _dict(payload, "route_progress")
    manifest = _dict(payload, "field_session_manifest") or _dict(payload, "field_run_manifest")
    return _safe_ref(
        _first_text(
            payload.get("evidence_ref"),
            summary.get("evidence_ref"),
            route_progress.get("evidence_ref"),
            manifest.get("evidence_ref"),
            default="",
        )
    )


def _source_state(label: str, path: str, payload: dict[str, Any], load_issue: str) -> dict[str, Any]:
    # source_state 只暴露白名单元数据，不复制 raw artifact。
    if load_issue:
        return {
            "name": label,
            "ref": _safe_ref(path),
            "load_status": "blocked",
            "load_issue": load_issue,
            "schema": "",
            "schema_status": "not_loaded",
            "evidence_boundary": "",
            "boundary_status": "not_loaded",
            "source": "",
            "source_status": "not_loaded",
            "evidence_ref": "",
            "status": "missing",
        }

    summary = _source_summary(payload)
    schemas, boundary = _expected_contract(label)
    schema = _safe_text(_first_text(payload.get("schema"), summary.get("schema"), default=""))
    evidence_boundary = _safe_text(_first_text(payload.get("evidence_boundary"), summary.get("evidence_boundary"), default=""))
    source = _safe_text(_first_text(payload.get("source"), summary.get("source"), default=""))
    return {
        "name": label,
        "ref": _safe_ref(path),
        "load_status": "loaded",
        "load_issue": "",
        "schema": schema,
        "schema_status": "supported" if schema in schemas else "unsupported",
        "evidence_boundary": evidence_boundary,
        "boundary_status": "supported" if evidence_boundary == boundary else "unsupported",
        "source": source,
        "source_status": "supported" if source in ("", SOURCE) else "unsupported",
        "evidence_ref": _extract_evidence_ref(payload, summary),
        "status": _safe_text(
            _first_text(
                payload.get("status"),
                payload.get("console_verdict"),
                payload.get("completion_verdict"),
                payload.get("reconciliation_verdict"),
                summary.get("status"),
                summary.get("console_verdict"),
                summary.get("completion_verdict"),
                summary.get("reconciliation_verdict"),
                default="missing",
            )
        ),
    }


def _source_brief(payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # source_summaries 只保留状态、计数、下一步和同 ref 线索，不复制 full payload。
    summary = _source_summary(payload)
    materials = _dict(payload, "materials_status") or _dict(summary, "materials_status")
    route_progress = _dict(payload, "route_progress")
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_boundary": source.get("evidence_boundary", ""),
        "boundary_status": source.get("boundary_status", ""),
        "source_status": source.get("source_status", ""),
        "status": source.get("status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "same_evidence_ref_status": _safe_text(
            _first_text(payload.get("same_evidence_ref_status"), summary.get("same_evidence_ref_status"), default="")
        ),
        "route_checkpoint": _safe_text(_first_text(route_progress.get("checkpoint_id"), route_progress.get("checkpoint"), default="")),
        "missing_materials_count": len(_safe_list(materials.get("missing_materials"))),
        "mismatch_reasons_count": len(_safe_list(materials.get("mismatch_reasons"))),
        "operator_next_steps": _safe_list(payload.get("operator_next_steps") or summary.get("operator_next_steps"), limit=4),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _missing_inputs(sources: list[dict[str, Any]]) -> list[str]:
    # 缺失、unsupported schema/boundary/source 和缺 evidence_ref 都阻断 handoff。
    missing: list[str] = []
    for source in sources:
        name = source["name"]
        if source["load_status"] != "loaded":
            missing.append(f"{name}:{source['load_issue']}")
            continue
        if source["schema_status"] == "unsupported":
            missing.append(f"{name}:unsupported_schema")
        if source["boundary_status"] == "unsupported":
            missing.append(f"{name}:unsupported_boundary")
        if source["source_status"] == "unsupported":
            missing.append(f"{name}:unsupported_source")
        if not source["evidence_ref"]:
            missing.append(f"{name}:missing_evidence_ref")
    return missing


def _same_ref_status(sources: list[dict[str, Any]], expected_ref: str) -> tuple[str, list[str], str]:
    # 现场回填必须围绕同一 evidence_ref；显式参数优先参与校验。
    refs = [source["evidence_ref"] for source in sources if source.get("evidence_ref")]
    target_ref = _safe_ref(expected_ref) or (refs[0] if refs else "")
    if not target_ref:
        return "blocked_missing_evidence_ref", ["evidence_ref:missing"], ""
    mismatches: list[str] = []
    for source in sources:
        ref = source.get("evidence_ref", "")
        if source.get("load_status") == "loaded" and ref and ref != target_ref:
            mismatches.append(f"{source['name']}:evidence_ref_mismatch:{ref}!={target_ref}")
    if len(set(refs)) > 1:
        mismatches.append("evidence_ref:sources_do_not_share_same_ref")
    if mismatches:
        return "blocked_evidence_ref_mismatch", mismatches, target_ref
    return "matched_same_evidence_ref", [], target_ref


def _input_claims_success_or_control(payloads: list[dict[str, Any]]) -> tuple[bool, bool]:
    # Docker/local handoff 不允许上游声明 delivery success 或放行动作。
    success = False
    control = False
    for payload in payloads:
        summary = _source_summary(payload)
        if payload.get("delivery_success") is True or summary.get("delivery_success") is True:
            success = True
        if payload.get("primary_actions_enabled") is True or summary.get("primary_actions_enabled") is True:
            control = True
        if _has_success_claim(payload):
            success = True
    return success, control


def _handoff_verdict(
    sources: list[dict[str, Any]],
    missing: list[str],
    mismatches: list[str],
    unsafe: bool,
    success_claimed: bool,
    control_claimed: bool,
) -> str:
    # verdict 优先级保持 fail-closed：可读性、契约、同 ref、安全、越界成功/控制声明。
    load_issues = {source["load_issue"] for source in sources if source.get("load_issue")}
    if any(issue.endswith("_not_provided") or issue.endswith("_missing") for issue in load_issues):
        return "blocked_missing_inputs"
    if any(issue.endswith("_bad_json") or issue.endswith("_not_object") or issue.endswith("_read_error") for issue in load_issues):
        return "blocked_invalid_input"
    if missing:
        return "blocked_invalid_input"
    if mismatches:
        return "blocked_evidence_ref_mismatch"
    if unsafe:
        return "blocked_unsafe_copy"
    if success_claimed or control_claimed:
        return "blocked_success_claim"
    return "ready_for_field_session_handoff_not_proven"


def _required_materials(evidence_ref: str) -> list[dict[str, Any]]:
    # 清单描述现场应补采什么；它不是材料存在证明。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        {
            "name": name,
            "same_evidence_ref_required": True,
            "expected_evidence_ref": ref,
            "material_status": "required_not_collected_by_this_gate",
            "delivery_success": False,
        }
        for name in REQUIRED_MATERIALS
    ]


def _operator_next_steps(verdict: str, evidence_ref: str, missing: list[str], mismatches: list[str]) -> list[str]:
    # 操作员步骤直接描述补采/重跑，不让现场人员从内部字段猜分支。
    ref = evidence_ref or "<same_evidence_ref>"
    if verdict == "blocked_missing_inputs":
        steps = [
            f"Regenerate PC route debug console, route completion signal, and elevator-route reconciliation under evidence_ref={ref}.",
            "Rerun route_elevator_field_session_handoff.py after all three source JSON files exist.",
            "Keep delivery_success=false and primary_actions_enabled=false until real field evidence exists.",
        ]
    elif verdict in {"blocked_invalid_input", "blocked_unsafe_copy"}:
        steps = [
            "Repair unsupported schema, boundary, source, bad JSON, or unsafe copy in source summaries.",
            "Regenerate only phone-safe summaries without credentials, raw artifacts, ROS topics, hardware transport, local paths, or tracebacks.",
            f"Rerun this handoff gate with the same evidence_ref={ref}.",
        ]
    elif verdict == "blocked_evidence_ref_mismatch":
        steps = [
            f"Re-export all three source materials under one evidence_ref={ref}.",
            "Do not combine PC route, completion signal, and elevator reconciliation from different runs.",
            "Rerun PC console, completion signal, elevator reconciliation, then this handoff gate.",
        ]
    elif verdict == "blocked_success_claim":
        steps = [
            "Remove delivery success, dropoff/cancel completion, HIL, or primary action claims from Docker/local materials.",
            "Use this artifact only as field-session handoff metadata.",
            "Collect real route, elevator, dropoff/cancel, HIL, phone, and delivery materials before any success claim.",
        ]
    else:
        steps = [
            f"Preserve evidence_ref={ref} across the controlled field session.",
            "Collect the required materials listed in field_session_manifest before claiming field pass.",
            "Use Robot diagnostics and mobile panels as read-only handoff summaries only.",
        ]
    if missing:
        steps.append(f"Missing or invalid inputs: {', '.join(missing[:4])}")
    if mismatches:
        steps.append(f"Evidence mismatch: {', '.join(mismatches[:2])}")
    return [_safe_text(step) for step in steps[:5]]


def _field_session_manifest(
    verdict: str,
    evidence_ref: str,
    session_id: str,
    operator: str,
    location: str,
    time_window: str,
    required_materials: list[dict[str, Any]],
) -> dict[str, Any]:
    # manifest 是现场 session 总目录，明确本 gate 只准备回填入口。
    return {
        "session_id": _safe_text(session_id),
        "operator": _safe_text(operator),
        "location": _safe_text(location),
        "time_window": _safe_text(time_window),
        "session_state": "ready_for_field_session_handoff_not_proven"
        if verdict == "ready_for_field_session_handoff_not_proven"
        else "blocked_until_source_materials_repaired",
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "required_material_names": list(REQUIRED_MATERIALS),
        "required_materials_count": len(required_materials),
        "boundary_note": "software_proof_docker_route_elevator_field_session_handoff_gate; not delivery success or Objective 5 external proof.",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary(
    verdict: str,
    evidence_ref: str,
    same_ref_status: str,
    required_materials: list[dict[str, Any]],
    operator_steps: list[str],
) -> dict[str, Any]:
    # summary 是下游首选消费面，字段必须少且稳定。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": verdict,
        "handoff_verdict": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "required_materials_summary": {
            "required_count": len(required_materials),
            "required_names": [item["name"] for item in required_materials],
            "material_status": "checklist_only_not_collected_by_this_gate",
        },
        "operator_next_steps": operator_steps[:4],
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def _robot_diagnostics_summary(summary: dict[str, Any], missing: list[str], mismatches: list[str]) -> dict[str, Any]:
    # diagnostics 只拿白名单摘要；不复制 raw artifact、checksum、路径、topic 或硬件参数。
    return {
        "schema": SUMMARY_SCHEMA,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": summary["status"],
        "handoff_verdict": summary["handoff_verdict"],
        "evidence_ref": summary["evidence_ref"],
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": summary["same_evidence_ref_status"],
        "required_materials_count": summary["required_materials_summary"]["required_count"],
        "missing_inputs": missing[:8],
        "mismatch_reasons": mismatches[:8],
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "route_elevator_field_session_handoff_metadata_only_not_delivery_success",
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def _mobile_readonly_summary(summary: dict[str, Any]) -> dict[str, Any]:
    # mobile 摘要只说明 handoff 状态和下一步，不包含 raw artifact 或底层工程细节。
    return {
        "schema": SUMMARY_SCHEMA,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": summary["status"],
        "handoff_verdict": summary["handoff_verdict"],
        "evidence_ref": summary["evidence_ref"],
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": summary["same_evidence_ref_status"],
        "required_materials_summary": summary["required_materials_summary"],
        "operator_next_steps": summary["operator_next_steps"][:3],
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def build_handoff(
    pc_route_debug_json: str,
    route_completion_json: str,
    elevator_route_reconciliation_json: str,
    evidence_ref: str = "",
    session_id: str = "",
    operator: str = "",
    location: str = "",
    time_window: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    # build 函数保持 dependency-free，测试可以直接覆盖 fail-closed 分支。
    pc_payload, pc_issue = _load_json(pc_route_debug_json, "pc_route_debug_console")
    completion_payload, completion_issue = _load_json(route_completion_json, "route_completion_signal")
    reconciliation_payload, reconciliation_issue = _load_json(
        elevator_route_reconciliation_json,
        "elevator_route_reconciliation",
    )

    pc_source = _source_state("pc_route_debug_console", pc_route_debug_json, pc_payload, pc_issue)
    completion_source = _source_state("route_completion_signal", route_completion_json, completion_payload, completion_issue)
    reconciliation_source = _source_state(
        "elevator_route_reconciliation",
        elevator_route_reconciliation_json,
        reconciliation_payload,
        reconciliation_issue,
    )
    sources = [pc_source, completion_source, reconciliation_source]
    missing = _missing_inputs(sources)
    same_ref_status, mismatches, handoff_ref = _same_ref_status(sources, evidence_ref)
    payloads = [payload for payload in (pc_payload, completion_payload, reconciliation_payload) if payload]
    unsafe = any(_has_forbidden_copy(payload) for payload in payloads)
    success_claimed, control_claimed = _input_claims_success_or_control(payloads)
    verdict = _handoff_verdict(sources, missing, mismatches, unsafe, success_claimed, control_claimed)
    materials = _required_materials(handoff_ref)
    steps = _operator_next_steps(verdict, handoff_ref, missing, mismatches)
    summary = _summary(verdict, handoff_ref, same_ref_status, materials, steps)

    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "evidence_ref": handoff_ref,
        "handoff_verdict": verdict,
        "source_summaries": {
            "pc_route_debug_console": _source_brief(pc_payload, pc_source) if pc_payload else pc_source,
            "route_completion_signal": _source_brief(completion_payload, completion_source) if completion_payload else completion_source,
            "elevator_route_reconciliation": _source_brief(reconciliation_payload, reconciliation_source)
            if reconciliation_payload
            else reconciliation_source,
        },
        "field_session_manifest": _field_session_manifest(
            verdict,
            handoff_ref,
            session_id,
            operator,
            location,
            time_window,
            materials,
        ),
        "required_materials": materials,
        "operator_handoff": {
            "session_id": _safe_text(session_id),
            "operator": _safe_text(operator),
            "location": _safe_text(location),
            "time_window": _safe_text(time_window),
            "operator_next_steps": steps,
            "same_evidence_ref_required": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "robot_diagnostics_summary": _robot_diagnostics_summary(summary, missing, mismatches),
        "mobile_readonly_summary": _mobile_readonly_summary(summary),
        "materials_status": {
            "source_materials": sources,
            "missing_inputs": missing,
            "mismatch_reasons": mismatches,
            "unsafe_copy_detected": bool(unsafe),
            "success_claimed_by_input": bool(success_claimed),
            "control_claimed_by_input": bool(control_claimed),
        },
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "wave_rover",
            "real_elevator",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
        ],
        "primary_actions_enabled": False,
        "delivery_success": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_forbidden_copy(artifact) or _has_forbidden_copy(summary):
        # 最终防线保证输出本身也不携带禁词；状态回落到 unsafe。
        artifact["handoff_verdict"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["handoff_verdict"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["handoff_verdict"] = "blocked_unsafe_copy"
        summary["status"] = "blocked_unsafe_copy"
        summary["handoff_verdict"] = "blocked_unsafe_copy"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出路径时自动建目录；未指定 summary-output 时只写 artifact。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只做本地 JSON handoff，不触发任何现场控制或外部证明动作。
    parser = argparse.ArgumentParser(description="Generate a route/elevator field-session handoff artifact")
    parser.add_argument("--pc-route-debug-json", required=True, help="PC route debug console artifact or summary JSON")
    parser.add_argument("--route-completion-json", required=True, help="route completion signal artifact or summary JSON")
    parser.add_argument(
        "--elevator-route-reconciliation-json",
        required=True,
        help="elevator route reconciliation artifact or summary JSON",
    )
    parser.add_argument("--evidence-ref", required=True, help="expected same evidence_ref for the handoff session")
    parser.add_argument("--output", required=True, help="handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff summary JSON output path")
    parser.add_argument("--session-id", default="", help="optional field session id")
    parser.add_argument("--operator", default="", help="optional operator name or role")
    parser.add_argument("--location", default="", help="optional safe location label")
    parser.add_argument("--time-window", default="", help="optional safe field session time window")
    args = parser.parse_args()

    artifact, summary, exit_code = build_handoff(
        args.pc_route_debug_json,
        args.route_completion_json,
        args.elevator_route_reconciliation_json,
        args.evidence_ref,
        args.session_id,
        args.operator,
        args.location,
        args.time_window,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    print(f"route/elevator field-session handoff: handoff_file:{_safe_ref(args.output)}")
    if args.summary_output:
        print(f"handoff_summary_file: {_safe_ref(args.summary_output)}")
    print(f"handoff_verdict: {artifact['handoff_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
