#!/usr/bin/env python3
"""生成 route/task terminal review decision artifact。

该工具只读取上一轮 terminal completion rehearsal artifact/summary，并把
operator review decision、owner handoff、next required evidence 和 field retest
request guidance 写成 dependency-free PC evidence。它不访问 ROS graph、Nav2、
硬件、外部云、手机或真实现场材料。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# review decision 是 terminal rehearsal 的下一层证据，不复用上游 schema。
DECISION_SCHEMA = "trashbot.route_task_terminal_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.route_task_terminal_review_decision_summary.v1"
DECISION_SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_route_task_terminal_review_decision_gate"

# 只接受上一轮 terminal completion rehearsal 的 artifact 或 summary。
REHEARSAL_SCHEMAS = {
    "trashbot.route_task_terminal_completion_rehearsal.v1",
    "trashbot.route_task_terminal_completion_rehearsal_summary.v1",
}
REHEARSAL_BOUNDARY = "software_proof_docker_route_task_terminal_completion_rehearsal_gate"

# not_proven 只写抽象能力缺口，避免把硬件型号或现场成功词扩散给下游。
NOT_PROVEN = (
    "real_delivery",
    "real_terminal_completion",
    "real_dropoff_completion",
    "real_cancel_completion",
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "real_elevator_field_pass",
    "real_phone_device_or_browser",
    "real_hardware_feedback",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 输入材料里出现这些词说明不是 phone/support safe summary，必须 fail closed。
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
    "HIL",
)

# 成功或授权动作只能来自真实现场验收，本 gate 看到就转 blocked。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bterminal\s+completion\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\broute/elevator\s+field\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
)

# 本机绝对路径、Windows 路径不能进入 operator guidance。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# 先脱敏再输出，blocked artifact 也不能泄露原始敏感文本。
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
    (re.compile(r"(?i)\bHIL\b"), "[REDACTED_FIELD_PROOF]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 让不同 PC/Docker 产物按字符串稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏；blocked 分支也不能把原文写入 artifact。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 只保留安全短引用，避免把本机路径给 diagnostics/mobile。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归处理新增嵌套字段，降低后续字段扩展时的泄露风险。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _safe_list(value: Any, limit: int = 12) -> list[str]:
    # 上游字段可能是字符串或 list；限制数量避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _encoded(value: Any) -> str:
    # 稳定 JSON 字符串用于安全扫描；失败时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # forbidden copy 命中表示该输入不适合进入 operator review。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_raw_path_copy(payload: dict[str, Any]) -> bool:
    # 只扫描人读摘要字段，避免原始 evidence_ref 被误判。
    fragments = [
        _encoded(_dict(payload, "robot_diagnostics_summary")),
        _encoded(_dict(payload, "mobile_readonly_summary")),
    ]
    fragments.extend(_safe_list(payload.get("operator_next_steps"), limit=8))
    encoded = "\n".join(fragments)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(payload: dict[str, Any]) -> bool:
    # delivery_success=true 或 primary_actions_enabled=true 直接阻断。
    for source in (payload, _dict(payload, "robot_diagnostics_summary"), _dict(payload, "mobile_readonly_summary")):
        if source.get("delivery_success") is True or source.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(payload)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺失或坏 JSON 仍输出 blocked artifact，便于自动化记录失败原因。
    if not path:
        return {}, "terminal_rehearsal_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "terminal_rehearsal_missing"
    except json.JSONDecodeError:
        return {}, "terminal_rehearsal_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "terminal_rehearsal_read_error"
    if not isinstance(payload, dict):
        return {}, "terminal_rehearsal_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 上游 summary 字段可能缺失；非 object 统一按空对象处理。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # 兼容 artifact/summary 两种输入，取第一个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _schema_supported(payload: dict[str, Any]) -> bool:
    # schema 和 boundary 同时白名单化，防止拿错上游材料。
    schema = str(payload.get("schema", "")).strip()
    boundary = str(payload.get("evidence_boundary", "")).strip()
    return schema in REHEARSAL_SCHEMAS and (not boundary or boundary == REHEARSAL_BOUNDARY)


def _extract_evidence_ref(payload: dict[str, Any]) -> str:
    # 同一证据主键可能在顶层、diagnostics summary 或 mobile summary。
    robot = _dict(payload, "robot_diagnostics_summary")
    mobile = _dict(payload, "mobile_readonly_summary")
    return _safe_ref(
        _first_text(
            payload.get("evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("evidence_ref"),
            default="",
        )
    )


def _terminal_verdict(payload: dict[str, Any]) -> str:
    # terminal verdict 只作为 review 输入状态，不等于现场完成状态。
    robot = _dict(payload, "robot_diagnostics_summary")
    mobile = _dict(payload, "mobile_readonly_summary")
    return _safe_text(
        _first_text(
            payload.get("terminal_verdict"),
            payload.get("status"),
            robot.get("terminal_verdict"),
            robot.get("status"),
            mobile.get("terminal_verdict"),
            mobile.get("status"),
            default="",
        )
    )


def _rehearsal_status(payload: dict[str, Any], load_issue: str) -> dict[str, Any]:
    # source 摘要只暴露材料元数据，不复制 raw input。
    return {
        "load_status": "blocked" if load_issue else "loaded",
        "load_issue": load_issue,
        "schema": _safe_text(payload.get("schema", "")) if payload else "",
        "schema_status": "supported" if payload and _schema_supported(payload) else ("unsupported" if payload else ""),
        "evidence_boundary": _safe_text(payload.get("evidence_boundary", "")) if payload else "",
        "evidence_ref": _extract_evidence_ref(payload) if payload else "",
        "terminal_verdict": _terminal_verdict(payload) if payload else "",
    }


def _review_status(
    load_issue: str,
    source: dict[str, Any],
    mismatches: list[str],
    unsafe: bool,
    success_or_control_claim: bool,
) -> str:
    # fail-closed 优先级固定，避免把不可读材料转成 field retest 请求。
    if load_issue.endswith("_bad_json") or load_issue.endswith("_not_object") or load_issue.endswith("_read_error"):
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_route_task_terminal_review_decision"
    if source.get("schema_status") == "unsupported":
        return "blocked_unsupported_schema"
    if mismatches:
        return "blocked_mismatch_evidence_ref"
    if unsafe:
        return "blocked_unsafe_copy"
    if success_or_control_claim:
        return "blocked_success_or_control_claim"
    terminal_verdict = str(source.get("terminal_verdict", ""))
    if not terminal_verdict:
        return "blocked_missing_route_task_terminal_review_decision"
    if terminal_verdict.startswith("blocked_"):
        return "requires_rehearsal_repair_before_field_retest"
    if terminal_verdict == "blocked_missing_recovery_reason":
        return "requires_recovery_reason_before_field_retest"
    if terminal_verdict == "failed_with_recovery_reason_not_proven":
        return "review_failed_terminal_recovery_before_field_retest"
    return "ready_for_operator_terminal_review_not_proven"


def _decision(status: str, terminal_verdict: str) -> tuple[str, str]:
    # decision 只决定下一步材料动作，不授权机器人控制。
    if status.startswith("blocked_bad_json") or status.startswith("blocked_missing"):
        return (
            "regenerate_terminal_completion_rehearsal",
            "Terminal rehearsal input is missing, unreadable, or incomplete.",
        )
    if status == "blocked_unsupported_schema":
        return (
            "rerun_supported_terminal_completion_rehearsal",
            "Terminal rehearsal input does not match the supported schema or boundary.",
        )
    if status == "blocked_mismatch_evidence_ref":
        return (
            "realign_same_evidence_ref_then_rerun",
            "Terminal rehearsal evidence_ref does not match the requested review evidence_ref.",
        )
    if status == "blocked_unsafe_copy":
        return (
            "repair_safe_summary_before_review",
            "Terminal rehearsal contains unsafe operator or support copy.",
        )
    if status == "blocked_success_or_control_claim":
        return (
            "remove_success_or_control_claims_before_review",
            "Terminal rehearsal contains a success or primary-action claim that this software gate cannot accept.",
        )
    if status == "requires_recovery_reason_before_field_retest":
        return (
            "add_recovery_reason_before_retest_request",
            "Failure branch is missing recovery context, so field retest guidance would be ambiguous.",
        )
    if status == "review_failed_terminal_recovery_before_field_retest":
        return (
            "request_field_retest_after_recovery_review",
            "Terminal rehearsal captured a failure with recovery reason and needs operator review before retest.",
        )
    if status == "requires_rehearsal_repair_before_field_retest":
        return (
            "repair_terminal_rehearsal_before_retest_request",
            f"Terminal rehearsal is still blocked ({terminal_verdict}) and cannot support a retest request.",
        )
    return (
        "request_field_retest_materials_not_proven",
        "Terminal rehearsal is internally consistent enough for operator review, but it remains software proof only.",
    )


def _owner_handoff(status: str, evidence_ref: str) -> dict[str, Any]:
    # owner handoff 显式拆分责任，避免现场人员把 review 当成自动发车许可。
    ref = evidence_ref or "<same_evidence_ref>"
    if status.startswith("blocked_") or status.startswith("requires_"):
        action_owner = "Autonomy Algorithm Engineer"
        handoff_note = f"Repair terminal rehearsal materials for evidence_ref={ref} before requesting field retest."
    else:
        action_owner = "Autonomy Algorithm Engineer + operator"
        handoff_note = f"Prepare field retest materials for evidence_ref={ref}; keep Robot/mobile consumers read-only."
    return {
        "owner": action_owner,
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
        "handoff_note": handoff_note,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(status: str, evidence_ref: str, source: dict[str, Any]) -> list[str]:
    # 只列下一步要采集的材料，不声明任何真实完成。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "blocked_mismatch_evidence_ref":
        return [f"Re-export terminal rehearsal under one evidence_ref={ref}.", "Rerun route_task_terminal_review_decision after refs align."]
    if status in {"blocked_bad_json", "blocked_missing_route_task_terminal_review_decision", "blocked_unsupported_schema"}:
        return [
            f"Generate a supported route_task_terminal_completion_rehearsal artifact or summary for evidence_ref={ref}.",
            "Include route status, task record, completion signal, and required dropoff/cancel material summaries.",
        ]
    if status == "blocked_unsafe_copy":
        return ["Regenerate terminal rehearsal without credentials, raw paths, ROS topics, transport details, field-proof wording, or success copy."]
    if status == "blocked_success_or_control_claim":
        return ["Remove delivery_success=true, primary_actions_enabled=true, field pass, or completion success claims from software-proof input."]
    if status == "requires_recovery_reason_before_field_retest":
        return [f"Add failure_reason and recovery_reason to the task record for evidence_ref={ref}.", "Rerun terminal completion rehearsal before review decision."]
    if status == "review_failed_terminal_recovery_before_field_retest":
        return [
            f"Collect operator review notes for the failed terminal recovery on evidence_ref={ref}.",
            "Prepare the next field retest request with route status, task record, and completion signal refs.",
        ]
    terminal_verdict = source.get("terminal_verdict", "terminal_verdict_missing")
    return [
        f"Run a real controlled route/task field retest using the same evidence_ref={ref}.",
        f"Bring runtime route log, task record, terminal completion signal, and operator notes back to PC review; current terminal_verdict={terminal_verdict}.",
        "Keep this review decision as software_proof until real field materials are attached.",
    ]


def _field_retest_request_guidance(status: str, evidence_ref: str) -> list[str]:
    # field retest guidance 是请求清单，不是通过结论或控制授权。
    ref = evidence_ref or "<same_evidence_ref>"
    if status.startswith("blocked_") or status.startswith("requires_"):
        return [
            f"Do not request field retest yet for evidence_ref={ref}.",
            "First repair the blocked terminal rehearsal material and rerun this review decision gate.",
        ]
    return [
        f"Request field retest package for evidence_ref={ref} with route status, task record, terminal completion signal, operator note, and failure/recovery context.",
        "Ask the field operator to record what happened, not to mark delivery as complete from this software proof.",
        "After the retest, rerun terminal completion rehearsal and this review decision gate before product closeout.",
    ]


def _summary_payload(
    status: str,
    decision: str,
    reason: str,
    evidence_ref: str,
    owner_handoff: dict[str, Any],
    next_required_evidence: list[str],
    field_retest_request_guidance: list[str],
) -> dict[str, Any]:
    # summary 是 Robot/mobile 可消费的白名单视图，不包含 raw artifact。
    return {
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": DECISION_SCHEMA_VERSION,
        "evidence_boundary": DECISION_BOUNDARY,
        "status": status,
        "review_decision": decision,
        "decision_reason": reason,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence[:4],
        "field_retest_request_guidance": field_retest_request_guidance[:4],
        "software_proof": "software_proof",
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_terminal_review_decision(
    terminal_rehearsal_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    rehearsal_payload, load_issue = _load_json(terminal_rehearsal_json)
    source = _rehearsal_status(rehearsal_payload, load_issue)
    requested_ref = _safe_ref(evidence_ref) or source.get("evidence_ref", "")
    mismatches: list[str] = []
    if requested_ref and source.get("evidence_ref") and requested_ref != source.get("evidence_ref"):
        mismatches.append(f"terminal_rehearsal:evidence_ref_mismatch:{source.get('evidence_ref')}!={requested_ref}")

    unsafe = bool(rehearsal_payload) and (_has_forbidden_copy(rehearsal_payload) or _has_raw_path_copy(rehearsal_payload))
    success_or_control_claim = bool(rehearsal_payload) and _has_success_or_control_claim(rehearsal_payload)
    status = _review_status(load_issue, source, mismatches, unsafe, success_or_control_claim)
    review_decision, decision_reason = _decision(status, str(source.get("terminal_verdict", "")))
    owner_handoff = _owner_handoff(status, requested_ref)
    next_required_evidence = _next_required_evidence(status, requested_ref, source)
    field_retest_request_guidance = _field_retest_request_guidance(status, requested_ref)
    summary = _summary_payload(
        status,
        review_decision,
        decision_reason,
        requested_ref,
        owner_handoff,
        next_required_evidence,
        field_retest_request_guidance,
    )

    artifact = {
        "schema": DECISION_SCHEMA,
        "schema_version": DECISION_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": DECISION_BOUNDARY,
        "same_evidence_ref_required": True,
        "evidence_ref": requested_ref,
        "source_terminal_rehearsal": source,
        "status": status,
        "review_decision": review_decision,
        "decision_reason": decision_reason,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "field_retest_request_guidance": field_retest_request_guidance,
        "materials_status": {
            "load_issue": load_issue,
            "mismatch_reasons": mismatches,
            "unsafe_copy": bool(unsafe),
            "success_or_control_claim": bool(success_or_control_claim),
        },
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "software_proof": "software_proof",
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "hardware",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "real_phone",
        ],
        "boundary_note": (
            "route_task_terminal_review_decision is software_proof only; "
            "not_proven; delivery_success=false; primary_actions_enabled=false"
        ),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只打印 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 保持 dependency-free，便于 PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate a route/task terminal review decision artifact")
    parser.add_argument("--terminal-rehearsal-json", required=True, help="terminal completion rehearsal artifact or summary JSON path")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for the review decision")
    parser.add_argument("--output", default="", help="optional review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_terminal_review_decision(
        args.terminal_rehearsal_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task terminal review decision: review_decision_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"review_decision_summary_file: {_safe_ref(args.summary_output)}")
        print(f"status: {artifact['status']}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
