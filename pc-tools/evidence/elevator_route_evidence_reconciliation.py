#!/usr/bin/env python3
"""复账 elevator rehearsal evidence 与 route/task completion signal。

该 gate 只在 Docker/local PC 上读取 JSON artifact 或 summary，按同一
`evidence_ref` 检查电梯阶段证据和路线任务完成信号是否能进入人工复核。
它不访问 ROS graph、Nav2 runtime、serial/UART、真实电梯、硬件、外部云、
OSS/CDN、DB/queue 或 4G 网络。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 顶层 schema/boundary 是 Robot diagnostics 与 mobile/web 后续只读消费的契约。
RECONCILIATION_SCHEMA = "trashbot.elevator_route_evidence_reconciliation.v1"
SUMMARY_SCHEMA = "trashbot.elevator_route_evidence_reconciliation_summary.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_elevator_route_evidence_reconciliation_gate"
SOURCE = "software_proof"

# 只接受上一轮已经固化的电梯 rehearsal evidence artifact 或其 phone-safe summary。
ELEVATOR_SCHEMAS = {
    "trashbot.elevator_assist_rehearsal_evidence.v1",
    "trashbot.elevator_assist_rehearsal_evidence_summary.v1",
}
ELEVATOR_BOUNDARY = "software_proof_docker_elevator_evidence_driven_mainline_gate"

# route completion signal 的 phone_safe_summary 当前沿用 artifact schema；同时预留 summary 名。
ROUTE_COMPLETION_SCHEMAS = {
    "trashbot.route_task_completion_signal.v1",
    "trashbot.route_task_completion_signal_summary.v1",
}
ROUTE_COMPLETION_BOUNDARY = "software_proof_docker_route_task_completion_signal_gate"

# not_proven 是本 gate 的证据边界，不允许被 ready/reconciled 语义冲淡。
NOT_PROVEN = (
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_record",
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

# 输出摘要必须保持 phone-safe，不携带凭证、控制 topic、设备路径或 raw 材料。
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

# 脱敏规则先缩小输出，再由 forbidden/success 检查决定是否 fail closed。
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

# 自由文本中出现完成/成功声明时必须 blocked，避免复账报告被误读为实机闭环。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(completed|complete|success|succeeded)\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
)


def _utc_now() -> str:
    # UTC 让不同 PC/Docker 主机生成的材料可稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有进入 artifact 的自由文本先脱敏，避免 summary 承载敏感材料。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 本机绝对路径不进入手机摘要，只保留 basename 作为同 run 线索。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 兼容上游字符串/list 形态，并限制数量避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 最终输出递归脱敏一次，防止新增字段绕过局部 helper。
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
    # 安全检查要覆盖键和值；不可编码对象按脱敏文本处理。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 命中任一禁词都 fail closed，而不是继续展示可疑摘要。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_success_claim(value: Any) -> bool:
    # `delivery_success=false` 是允许字段；这里拦截自由文本完成声明和 hil_pass=true。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 上游 artifact 的 summary 可能缺失或为非 object，统一按空对象处理。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # evidence_ref/status 可来自 artifact 顶层或 summary；只取第一个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON、非 object 都生成 blocked artifact，保证 CLI 可复现。
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
    # 支持调用方直接传 summary，也支持传 artifact 后读取 phone_safe_summary。
    phone = _dict(payload, "phone_safe_summary")
    payload_schema = str(payload.get("schema", "")).strip()
    if payload_schema in {SUMMARY_SCHEMA, "trashbot.elevator_assist_rehearsal_evidence_summary.v1", "trashbot.route_task_completion_signal_summary.v1"}:
        return payload
    return phone


def _source_state(label: str, path: str, payload: dict[str, Any], load_issue: str) -> dict[str, Any]:
    # source_state 只暴露白名单元数据，不复制输入 JSON。
    if load_issue:
        return {
            "name": label,
            "ref": _safe_ref(path),
            "load_status": "blocked",
            "load_issue": load_issue,
            "schema": "",
            "schema_status": "not_loaded",
            "boundary_status": "not_loaded",
            "source_status": "not_loaded",
            "evidence_ref": "",
            "status": "missing",
        }

    summary = _source_summary(payload)
    schema = _safe_text(_first_text(payload.get("schema"), summary.get("schema"), default=""))
    boundary = _safe_text(_first_text(payload.get("evidence_boundary"), summary.get("evidence_boundary"), default=""))
    source = _safe_text(_first_text(payload.get("source"), summary.get("source"), default=""))
    if label == "elevator_rehearsal":
        expected_schemas = ELEVATOR_SCHEMAS
        expected_boundary = ELEVATOR_BOUNDARY
    else:
        expected_schemas = ROUTE_COMPLETION_SCHEMAS
        expected_boundary = ROUTE_COMPLETION_BOUNDARY

    return {
        "name": label,
        "ref": _safe_ref(path),
        "load_status": "loaded",
        "load_issue": "",
        "schema": schema,
        "schema_status": "supported" if schema in expected_schemas else "unsupported",
        "evidence_boundary": boundary,
        "boundary_status": "supported" if boundary == expected_boundary else "unsupported",
        "source": source,
        "source_status": "supported" if label != "elevator_rehearsal" or source == SOURCE else "unsupported",
        "evidence_ref": _safe_ref(
            _first_text(payload.get("evidence_ref"), summary.get("evidence_ref"), default="")
        ),
        "status": _safe_text(
            _first_text(
                payload.get("rehearsal_evidence_verdict"),
                payload.get("completion_verdict"),
                payload.get("overall_status"),
                summary.get("status"),
                default="missing",
            )
        ),
    }


def _elevator_summary(payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # 电梯摘要只保留阶段、failure 和目标楼层，不复制 phase_evidence 全量 raw。
    summary = _source_summary(payload)
    phases = payload.get("phase_evidence", {})
    phase_names = list(phases.keys()) if isinstance(phases, dict) else _safe_list(summary.get("phase_names"))
    failure = _dict(payload, "failure") or _dict(summary, "failure")
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "status": source.get("status", ""),
        "target_floor": _safe_text(_first_text(payload.get("target_floor"), summary.get("target_floor"), default="")),
        "phase_names": [_safe_text(phase) for phase in phase_names[:12]],
        "failure": {
            "phase": _safe_text(failure.get("phase", "")),
            "reason": _safe_text(failure.get("reason", "")),
            "manual_takeover_reason": _safe_text(failure.get("manual_takeover_reason", "")),
        },
        "source_delivery_success": bool(payload.get("delivery_success", False) or summary.get("delivery_success", False)),
        "source_primary_actions_enabled": bool(
            payload.get("primary_actions_enabled", False) or summary.get("primary_actions_enabled", False)
        ),
    }


def _route_summary(payload: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    # 路线完成摘要只保留 verdict、dropoff/cancel 材料状态和失败恢复线索。
    summary = _source_summary(payload)
    dropoff = _dict(payload, "dropoff_completion") or _dict(summary, "dropoff_completion")
    cancel = _dict(payload, "cancel_completion") or _dict(summary, "cancel_completion")
    fixed_route = _dict(payload, "fixed_route_summary")
    task_record = _dict(payload, "task_record_summary")
    return {
        "schema": source.get("schema", ""),
        "schema_status": source.get("schema_status", ""),
        "evidence_ref": source.get("evidence_ref", ""),
        "status": source.get("status", ""),
        "completion_verdict": _safe_text(_first_text(payload.get("completion_verdict"), summary.get("completion_verdict"), default="")),
        "route_status": _safe_text(fixed_route.get("route_status", "")),
        "task_status": _safe_text(task_record.get("task_status", "")),
        "dropoff_completion": {
            "material_status": _safe_text(dropoff.get("material_status", "")),
            "completion_claimed": bool(dropoff.get("completion_claimed", False)),
        },
        "cancel_completion": {
            "material_status": _safe_text(cancel.get("material_status", "")),
            "completion_claimed": bool(cancel.get("completion_claimed", False)),
        },
        "failure_reason": _safe_text(_first_text(payload.get("failure_reason"), summary.get("failure_reason"), default="")),
        "recovery_reason": _safe_text(_first_text(payload.get("recovery_reason"), summary.get("recovery_reason"), default="")),
        "source_delivery_success": bool(payload.get("delivery_success", False) or summary.get("delivery_success", False)),
        "source_primary_actions_enabled": bool(
            payload.get("primary_actions_enabled", False) or summary.get("primary_actions_enabled", False)
        ),
    }


def _missing_materials(sources: list[dict[str, Any]]) -> list[str]:
    # required source 的加载、schema、boundary、source 与 ref 问题全部进入 missing/material 阻断。
    missing: list[str] = []
    for source in sources:
        if source["load_status"] != "loaded":
            missing.append(f"{source['name']}:{source['load_issue']}")
            continue
        if source["schema_status"] == "unsupported":
            missing.append(f"{source['name']}:unsupported_schema")
        if source["boundary_status"] == "unsupported":
            missing.append(f"{source['name']}:unsupported_boundary")
        if source["source_status"] == "unsupported":
            missing.append(f"{source['name']}:unsupported_source")
        if not source["evidence_ref"]:
            missing.append(f"{source['name']}:missing_evidence_ref")
    return missing


def _same_ref_status(sources: list[dict[str, Any]], expected_ref: str) -> tuple[str, list[str], str]:
    # 同一 evidence_ref 是本 gate 的核心约束；显式 --evidence-ref 也必须参与对齐。
    refs = [source.get("evidence_ref", "") for source in sources if source.get("evidence_ref")]
    target_ref = _safe_ref(expected_ref) or (refs[0] if refs else "")
    mismatches: list[str] = []
    if not target_ref:
        return "blocked_missing_evidence_ref", ["evidence_ref:missing"], ""
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
    # Docker/local source 不允许声明 delivery success 或放行 primary actions。
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


def _verdict(
    sources: list[dict[str, Any]],
    same_ref_status: str,
    missing: list[str],
    mismatches: list[str],
    unsafe: bool,
    success_claimed: bool,
    control_claimed: bool,
) -> str:
    # verdict 优先级按“可读 -> schema/boundary/source -> ref -> 安全 -> 边界 -> ready”判定。
    load_issues = {source["load_issue"] for source in sources if source.get("load_issue")}
    if any(issue.endswith("_bad_json") or issue.endswith("_not_object") or issue.endswith("_read_error") for issue in load_issues):
        return "blocked_bad_json"
    if any("unsupported_schema" in item for item in missing):
        return "blocked_unsupported_schema"
    if any("unsupported_boundary" in item for item in missing):
        return "blocked_unsupported_boundary"
    if any("unsupported_source" in item for item in missing):
        return "blocked_unsupported_source"
    if same_ref_status == "blocked_missing_evidence_ref":
        return "blocked_missing_evidence_ref"
    if mismatches:
        return "blocked_evidence_ref_mismatch"
    if unsafe:
        return "blocked_unsafe_copy"
    if success_claimed:
        return "blocked_success_claim"
    if control_claimed:
        return "blocked_control_claim"
    if missing:
        return "blocked_missing_materials"
    return "reconciled_not_proven"


def _operator_next_steps(verdict: str, evidence_ref: str, missing: list[str], mismatches: list[str]) -> list[str]:
    # operator_next_steps 把 verdict 转成下一步动作，避免现场同学从 JSON 猜分支。
    ref = evidence_ref or "<same_evidence_ref>"
    if verdict in {"blocked_missing_materials", "blocked_bad_json", "blocked_unsupported_schema", "blocked_unsupported_boundary"}:
        steps = [
            f"Regenerate elevator rehearsal evidence and route completion signal for evidence_ref={ref}.",
            "Rerun this reconciliation gate after missing, bad, or unsupported JSON is repaired.",
            "Keep delivery_success=false until real elevator, route, HIL, and completion evidence exists.",
        ]
    elif verdict in {"blocked_missing_evidence_ref", "blocked_evidence_ref_mismatch"}:
        steps = [
            f"Re-export both source materials under one evidence_ref={ref}.",
            "Do not combine elevator rehearsal evidence and route completion signal from different runs.",
            "Rerun elevator rehearsal, route completion signal, then this reconciliation gate.",
        ]
    elif verdict == "blocked_unsafe_copy":
        steps = [
            "Remove unsafe phone/support copy from source summaries.",
            "Regenerate artifacts without credentials, raw robot response, control topics, hardware transport, or local paths.",
            "Rerun this gate before diagnostics or mobile display.",
        ]
    elif verdict in {"blocked_success_claim", "blocked_control_claim", "blocked_unsupported_source"}:
        steps = [
            "Remove success, HIL, or control-action claims from Docker/local source materials.",
            "Use this gate only as software-proof reconciliation metadata.",
            "Collect real elevator, route, HIL, dropoff/cancel, and delivery evidence before any success claim.",
        ]
    else:
        steps = [
            f"Preserve evidence_ref={ref} across the next controlled field-run materials.",
            "Compare this reconciliation with Robot diagnostics and mobile read-only summary.",
            "Do not claim real elevator, Nav2/fixed-route, HIL, dropoff/cancel completion, or delivery success from this gate.",
        ]
    if missing:
        steps.append(f"Missing or blocked materials: {', '.join(missing[:3])}")
    if mismatches:
        steps.append(f"Evidence mismatch: {', '.join(mismatches[:2])}")

    # 去重和限长让 mobile/diagnostics 直接展示时仍可读。
    result: list[str] = []
    for step in steps:
        clean = _safe_text(step)
        if clean and clean not in result:
            result.append(clean)
    return result[:5]


def _phone_safe_summary(
    verdict: str,
    evidence_ref: str,
    same_ref_status: str,
    elevator: dict[str, Any],
    route: dict[str, Any],
    missing: list[str],
    mismatches: list[str],
    steps: list[str],
) -> dict[str, Any]:
    # summary 是 Robot diagnostics/mobile 的只读面，不能带 raw artifact 或控制细节。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": verdict,
        "reconciliation_verdict": verdict,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "evidence_ref": evidence_ref,
        "source_states": {
            "elevator_status": elevator.get("status", ""),
            "route_completion_verdict": route.get("completion_verdict", ""),
        },
        "missing_materials_count": len(missing),
        "mismatch_reasons_count": len(mismatches),
        "operator_next_steps": steps[:3],
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "elevator_route_reconciliation_metadata_only_not_delivery_success",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_reconciliation(elevator_json: str, route_completion_json: str, evidence_ref: str = "") -> tuple[dict[str, Any], int]:
    elevator_payload, elevator_issue = _load_json(elevator_json, "elevator")
    route_payload, route_issue = _load_json(route_completion_json, "route_completion")

    elevator_source = _source_state("elevator_rehearsal", elevator_json, elevator_payload, elevator_issue)
    route_source = _source_state("route_completion", route_completion_json, route_payload, route_issue)
    sources = [elevator_source, route_source]
    same_ref_status, mismatches, reconciled_ref = _same_ref_status(sources, evidence_ref)
    missing = _missing_materials(sources)

    elevator_summary = _elevator_summary(elevator_payload, elevator_source) if elevator_payload else {}
    route_summary = _route_summary(route_payload, route_source) if route_payload else {}
    loaded_payloads = [payload for payload in (elevator_payload, route_payload) if payload]
    unsafe = any(_has_forbidden_copy(payload) for payload in loaded_payloads)
    success_claimed, control_claimed = _input_claims_success_or_control(loaded_payloads)
    verdict = _verdict(sources, same_ref_status, missing, mismatches, unsafe, success_claimed, control_claimed)
    steps = _operator_next_steps(verdict, reconciled_ref, missing, mismatches)
    phone_summary = _phone_safe_summary(
        verdict,
        reconciled_ref,
        same_ref_status,
        elevator_summary,
        route_summary,
        missing,
        mismatches,
        steps,
    )

    artifact = {
        "schema": RECONCILIATION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "evidence_ref": reconciled_ref,
        "reconciliation_verdict": verdict,
        "source_states": {
            "elevator_rehearsal": elevator_source,
            "route_completion": route_source,
        },
        "elevator_rehearsal_summary": elevator_summary,
        "route_completion_summary": route_summary,
        "materials_status": {
            "missing_materials": missing,
            "mismatch_reasons": mismatches,
            "unsafe_copy_detected": bool(unsafe),
            "success_claimed_by_input": bool(success_claimed),
            "control_claimed_by_input": bool(control_claimed),
        },
        "operator_next_steps": steps,
        "phone_safe_summary": phone_summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "wave_rover",
            "real_elevator",
            "hardware_runtime",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
        ],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    if _has_forbidden_copy(artifact):
        # 最终防线只降级状态，不把 unsafe 内容伪装成可展示材料。
        artifact["reconciliation_verdict"] = "blocked_unsafe_copy"
        artifact["phone_safe_summary"]["status"] = "blocked_unsafe_copy"
        artifact["phone_safe_summary"]["reconciliation_verdict"] = "blocked_unsafe_copy"
    return artifact, 0


def write_reconciliation(artifact: dict[str, Any], output: str) -> None:
    # output 为空时只打印 stdout；指定路径时自动建父目录方便 sprint 验收。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只读本地 JSON，不推断 ROS/Nav2/电梯/硬件运行状态。
    parser = argparse.ArgumentParser(description="Reconcile elevator rehearsal evidence with route completion signal")
    parser.add_argument("--elevator-json", required=True, help="elevator rehearsal evidence artifact or summary JSON path")
    parser.add_argument("--route-completion-json", required=True, help="route/task completion signal artifact or summary JSON path")
    parser.add_argument("--output", default="", help="optional reconciliation JSON output path")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for both source materials")
    parser.add_argument("--once-json", action="store_true", help="print reconciliation JSON to stdout and exit")
    args = parser.parse_args()

    artifact, exit_code = build_reconciliation(args.elevator_json, args.route_completion_json, args.evidence_ref)
    write_reconciliation(artifact, args.output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"elevator route evidence reconciliation: reconciliation_file:{_safe_ref(args.output)}")
        print(f"reconciliation_verdict: {artifact['reconciliation_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
