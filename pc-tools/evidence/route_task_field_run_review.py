#!/usr/bin/env python3
"""生成 route/task field-run review console report。

该工具只读取上一轮 intake/crosscheck JSON，把机器字段整理成 operator/support 可读决策。
它不访问 ROS graph、Nav2 runtime、硬件、串口、网络或云服务，也不证明真实送达。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# review schema 是给 diagnostics/mobile 消费的新契约，不能复用 intake schema 混淆阶段。
REVIEW_SCHEMA = "trashbot.route_task_field_run_review_console.v1"
REVIEW_SCHEMA_VERSION = 1
REVIEW_BOUNDARY = "software_proof_docker_route_task_field_run_review_console_gate"
INTAKE_SCHEMA = "trashbot.route_task_field_run_intake_crosscheck.v1"
INTAKE_BOUNDARY = "software_proof_docker_route_task_field_run_intake_crosscheck_gate"

# not_proven 覆盖真实路线、硬件、任务完成和 O5 外部材料，防止 support 报告被误读。
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

# phone/support 摘要是给非工程入口看的，命中这些词时保守 blocked。
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

# 输入可以来自手工 JSON，先脱敏再进入报告，避免把凭证或本机细节扩散出去。
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
    # UTC 让不同 PC/Docker 主机生成的 review 仍可按字符串稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本统一走脱敏；None 保持为空字符串便于下游显示。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # phone/support 不需要完整本机路径，只保留 basename 作为同 run 线索。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 兼容旧 artifact 可能给出单字符串或非 list；报告只输出有限数量。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 递归脱敏只用于 review 自身摘要，不复制 intake raw artifact。
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
    # 安全检查需要稳定编码；不可编码对象降级为脱敏字符串。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # forbidden 检查覆盖键和值，防止后续新增字段绕过白名单。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON、非 object 都产出 blocked report，而不是抛未处理异常。
    if not path:
        return {}, "intake_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "intake_missing"
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}, "intake_read_error"
    if not isinstance(payload, dict):
        return {}, "intake_not_object"
    return payload, ""


def _first_text(*values: Any, default: str = "") -> str:
    # 新旧 summary 字段可能略有差异；只取第一个非空值，不从状态猜证据。
    for value in values:
        text = _safe_text(value).strip()
        if text:
            return text
    return default


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # diagnostics/mobile 可能传嵌套 summary，非 dict 一律当缺失处理。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _normalize_intake(payload: dict[str, Any]) -> dict[str, Any]:
    # review 只消费白名单字段，避免把上一轮 intake 原样复制成新 artifact。
    phone = _dict(payload, "phone_safe_summary")
    nested = _dict(payload, "route_task_field_run_intake") or _dict(payload, "route_task_field_run_intake_summary")
    source = payload if payload.get("schema") == INTAKE_SCHEMA else nested or payload
    nested_phone = _dict(source, "phone_safe_summary")
    return {
        "schema": _safe_text(source.get("schema", payload.get("schema", ""))),
        "evidence_boundary": _safe_text(source.get("evidence_boundary", payload.get("evidence_boundary", ""))),
        "overall_status": _first_text(source.get("overall_status"), source.get("status"), default="missing"),
        "evidence_ref": _safe_ref(
            _first_text(
                source.get("evidence_ref"),
                nested_phone.get("evidence_ref"),
                phone.get("evidence_ref"),
                payload.get("evidence_ref"),
                default="",
            )
        ),
        "same_evidence_ref_required": bool(source.get("same_evidence_ref_required", True)),
        "missing_materials": _safe_list(source.get("missing_materials")),
        "mismatch_reasons": _safe_list(source.get("mismatch_reasons")),
        "commands_to_rerun": _safe_list(source.get("commands_to_rerun")),
        "not_proven": _safe_list(source.get("not_proven") or nested_phone.get("not_proven") or payload.get("not_proven")),
        "delivery_success": bool(source.get("delivery_success", False)),
        "primary_actions_enabled": bool(source.get("primary_actions_enabled", False)),
    }


def _source_status(load_issue: str, normalized: dict[str, Any]) -> dict[str, Any]:
    # source_status 给支持面说明“读到的是哪类 intake”，不暴露本机路径或 raw JSON。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    supported = normalized.get("schema") in (INTAKE_SCHEMA, "") and normalized.get("evidence_boundary") in (
        INTAKE_BOUNDARY,
        "",
    )
    if normalized.get("schema") == INTAKE_SCHEMA and normalized.get("evidence_boundary") == INTAKE_BOUNDARY:
        schema_status = "supported"
    elif supported and normalized.get("overall_status") != "missing":
        schema_status = "compatible_summary"
    else:
        schema_status = "unsupported"
    return {"load_status": "loaded", "load_issue": "", "schema_status": schema_status}


def _overall_status(load_issue: str, schema_status: str, intake_status: str, missing: list[str], mismatches: list[str]) -> str:
    # review 状态按材料可读性、schema、缺失、不一致依次保守判定。
    if load_issue == "intake_missing":
        return "blocked_missing_intake"
    if load_issue:
        return "blocked_read_error"
    if schema_status == "unsupported":
        return "blocked_unsupported_schema"
    if missing:
        if any("unsafe_summary" in item for item in missing):
            return "blocked_unsafe_summary"
        return "blocked_missing_material"
    if mismatches:
        return "blocked_mismatch"
    if intake_status.startswith("blocked_unsafe"):
        return "blocked_unsafe_summary"
    if intake_status.startswith("blocked_unsupported"):
        return "blocked_unsupported_schema"
    if intake_status.startswith("blocked_mismatch"):
        return "blocked_mismatch"
    if intake_status.startswith("blocked"):
        return "blocked_missing_material"
    return "ready_for_operator_review"


def _decision(status: str, missing: list[str], mismatches: list[str]) -> dict[str, str]:
    # 决策是本工具新增的用户价值：把机器状态变成下一步分支。
    if status in {"blocked_missing_intake", "blocked_read_error", "blocked_unsupported_schema"}:
        return {
            "decision": "regenerate_intake_crosscheck",
            "reason": "The intake/crosscheck report is missing, unreadable, or not a supported summary.",
            "operator_action": "Regenerate route_task_field_run_intake.py from the five field-run materials first.",
        }
    if status == "blocked_unsafe_summary":
        return {
            "decision": "fix_support_safe_summary_then_rerun_intake",
            "reason": "The support/mobile summary is not safe enough for phone or support review.",
            "operator_action": "Remove unsafe copy, regenerate the support-safe summary, then rerun intake and review.",
        }
    if status == "blocked_mismatch" or mismatches:
        return {
            "decision": "rerun_sources_under_same_evidence_ref",
            "reason": "The field-run materials do not share the same evidence_ref.",
            "operator_action": "Re-export mismatched sources under the same evidence_ref and rerun intake/review.",
        }
    if status == "blocked_missing_material" or missing:
        return {
            "decision": "collect_missing_materials_then_rerun_intake",
            "reason": "At least one required field-run material is missing or incomplete.",
            "operator_action": "Collect the missing material list, rerun intake, then regenerate this review.",
        }
    return {
        "decision": "ready_for_operator_review_not_delivery_claim",
        "reason": "All software intake materials align, but real run, HIL, and delivery remain not proven.",
        "operator_action": "Use this report for support review and prepare real route/task evidence before claims.",
    }


def _operator_next_steps(status: str, evidence_ref: str, missing: list[str], mismatches: list[str]) -> list[str]:
    # next_steps 面向现场操作员，避免他们在 JSON 字段间猜下一步。
    ref = evidence_ref or "<same_evidence_ref>"
    if status in {"blocked_missing_intake", "blocked_read_error", "blocked_unsupported_schema"}:
        return [
            "Regenerate the intake crosscheck from route status, task record, runtime log, robot-side evidence, and mobile summary.",
            f"Keep every source on evidence_ref={ref}.",
            "Run this review CLI again after the intake report exists.",
        ]
    if missing:
        return [
            f"Collect or repair missing materials for evidence_ref={ref}.",
            "Rerun route_task_field_run_intake.py after every material is present.",
            "Rerun this review CLI and keep delivery_success=false until real proof exists.",
        ]
    if mismatches:
        return [
            f"Re-export mismatched materials under one evidence_ref={ref}.",
            "Rerun route_task_field_run_intake.py to confirm mismatch_reasons is empty.",
            "Rerun this review CLI before sharing the support summary.",
        ]
    if status == "blocked_unsafe_summary":
        return [
            "Remove unsafe phone/support copy from the source summary.",
            "Regenerate intake and review after the summary passes whitelist checks.",
            "Do not share raw robot response, local paths, credentials, or control topics.",
        ]
    return [
        "Review the aligned software materials with support/operator.",
        "Plan the next real route/task field run using the same evidence_ref discipline.",
        "Do not claim Nav2/fixed-route, HIL, dropoff/cancel completion, or delivery success from this report.",
    ]


def _commands_to_rerun(
    status: str,
    evidence_ref: str,
    missing: list[str],
    mismatches: list[str],
    intake_commands: list[str],
) -> list[str]:
    # 这里重新归纳命令，不直接复制 intake_commands，保持 review 层有可执行顺序。
    ref = evidence_ref or "<same_evidence_ref>"
    commands: list[str] = []
    if status in {"blocked_missing_intake", "blocked_read_error", "blocked_unsupported_schema"}:
        commands.append(f"rerun route_task_field_run_intake.py with all five field-run materials and evidence_ref={ref}")
    if missing:
        commands.append(f"re-export missing field-run materials with evidence_ref={ref}")
    if mismatches:
        commands.append(f"re-export mismatched field-run materials under one evidence_ref={ref}")
    if intake_commands and (missing or mismatches):
        commands.append("use intake commands_to_rerun as source-specific repair hints")
    commands.append("rerun route_task_field_run_review.py --intake-json <intake_report.json> --once-json")
    if status == "ready_for_operator_review":
        commands.append("collect real route/task, HIL, and delivery evidence before any field claim")
    return commands


def _phone_safe_summary(
    status: str,
    decision: dict[str, str],
    evidence_ref: str,
    missing: list[str],
    mismatches: list[str],
    commands: list[str],
    next_steps: list[str],
) -> dict[str, Any]:
    # phone/support 摘要只放白名单状态、计数、决策和前几条下一步，不复制原始 intake。
    return {
        "schema": REVIEW_SCHEMA,
        "evidence_boundary": REVIEW_BOUNDARY,
        "status": status,
        "review_decision": decision["decision"],
        "evidence_ref": evidence_ref,
        "missing_materials_count": len(missing),
        "mismatch_reasons_count": len(mismatches),
        "operator_next_steps": next_steps[:3],
        "commands_to_rerun": commands[:4],
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "support_review_only_not_delivery_success",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_review(intake_json: str) -> tuple[dict[str, Any], int]:
    intake_payload, load_issue = _load_json(intake_json)
    normalized = _normalize_intake(intake_payload) if intake_payload else {
        "schema": "",
        "evidence_boundary": "",
        "overall_status": "missing",
        "evidence_ref": "",
        "missing_materials": [],
        "mismatch_reasons": [],
        "commands_to_rerun": [],
        "not_proven": [],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    source = _source_status(load_issue, normalized)
    missing = list(normalized["missing_materials"])
    mismatches = list(normalized["mismatch_reasons"])
    unsafe_input = bool(intake_payload and _has_forbidden_copy(intake_payload))
    if unsafe_input and "support_safe_mobile_summary:unsafe_summary" not in missing:
        missing.append("support_safe_mobile_summary:unsafe_summary")
    status = _overall_status(
        load_issue,
        source["schema_status"],
        str(normalized["overall_status"]),
        missing,
        mismatches,
    )
    decision = _decision(status, missing, mismatches)
    next_steps = _operator_next_steps(status, normalized["evidence_ref"], missing, mismatches)
    commands = _commands_to_rerun(
        status,
        normalized["evidence_ref"],
        missing,
        mismatches,
        normalized["commands_to_rerun"],
    )
    phone_summary = _phone_safe_summary(status, decision, normalized["evidence_ref"], missing, mismatches, commands, next_steps)

    if _has_forbidden_copy(phone_summary):
        # phone summary 是对外材料，任何残留敏感词都改为 unsafe 决策。
        status = "blocked_unsafe_summary"
        if "support_safe_mobile_summary:unsafe_summary" not in missing:
            missing.append("support_safe_mobile_summary:unsafe_summary")
        decision = _decision(status, missing, mismatches)
        next_steps = _operator_next_steps(status, normalized["evidence_ref"], missing, mismatches)
        commands = _commands_to_rerun(status, normalized["evidence_ref"], missing, mismatches, normalized["commands_to_rerun"])
        phone_summary = _phone_safe_summary(status, decision, normalized["evidence_ref"], missing, mismatches, commands, next_steps)

    review = {
        "schema": REVIEW_SCHEMA,
        "schema_version": REVIEW_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": REVIEW_BOUNDARY,
        "overall_status": status,
        "review_decision": decision,
        "evidence_ref": normalized["evidence_ref"],
        "same_evidence_ref_required": True,
        "source_intake": {
            "ref": _safe_ref(intake_json),
            "schema": normalized["schema"],
            "evidence_boundary": normalized["evidence_boundary"],
            **source,
            "overall_status": normalized["overall_status"],
        },
        "missing_materials": missing,
        "mismatch_reasons": mismatches,
        "commands_to_rerun": commands,
        "operator_next_steps": next_steps,
        "phone_safe_summary": phone_summary,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return _safe_value(review), 0


def write_review(review: dict[str, Any], output: str) -> None:
    # output 为空时只打印 stdout；指定路径时自动建父目录，方便临时验收。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 保持单输入、单输出，方便 operator 从 intake 结果直接生成 review report。
    parser = argparse.ArgumentParser(description="Generate a route/task field-run review console report")
    parser.add_argument("--intake-json", required=True, help="route_task_field_run_intake crosscheck JSON path")
    parser.add_argument("--output", default="", help="optional review report JSON path")
    parser.add_argument("--once-json", action="store_true", help="print review report JSON to stdout and exit")
    args = parser.parse_args()

    review, exit_code = build_review(args.intake_json)
    write_review(review, args.output)
    if args.once_json or not args.output:
        print(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field-run review: review_file:{_safe_ref(args.output)}")
        print(f"overall_status: {review['overall_status']}")
        print(f"review_decision: {review['review_decision']['decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
