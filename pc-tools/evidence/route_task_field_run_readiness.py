#!/usr/bin/env python3
"""生成 route/task field-run readiness handoff。

该工具只聚合 PC route debug console、operator review 和 execution bundle 的摘要。
它不 import ROS2 包、不读取硬件、不触发 Nav2，也不把软件材料升级成真实路线或交付证明。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema/boundary 是 diagnostics、mobile 和 sprint closeout 的稳定机器契约。
READINESS_SCHEMA = "trashbot.route_task_field_run_readiness.v1"
READINESS_SCHEMA_VERSION = 1
READINESS_BOUNDARY = "software_proof_docker_route_task_field_run_readiness_gate"

# 上游三个材料来自不同 sprint gate；这里同时接受旧 execution bundle 无 v1 后缀的 schema。
PC_ROUTE_DEBUG_SCHEMA = "trashbot.pc_route_debug_console.v1"
OPERATOR_REVIEW_SCHEMA = "trashbot.route_task_rehearsal_operator_review.v1"
EXECUTION_BUNDLE_SCHEMA = "trashbot.route_task_rehearsal_execution_bundle"

# not_proven 必须覆盖真实路线、硬件、HIL、投放/取消和 O5 外部材料，避免 handoff 被误读。
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

# field-run 下一轮必须围绕同一 evidence_ref 收集；本工具只列清单，不声称这些材料已存在。
FIELD_RUN_MATERIALS = (
    "route_status_json",
    "task_record_json",
    "pc_route_debug_console_summary",
    "route_task_operator_review",
    "route_task_execution_bundle",
    "nav2_or_fixed_route_runtime_log",
    "robot_side_task_evidence",
    "support_safe_mobile_summary",
)

# phone/support safe 摘要不能携带凭证、完整路径、ROS 控制 topic、串口和硬件参数。
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

# 脱敏规则覆盖 token、AK/SK、DB/queue URL、topic、串口、波特率、硬件名、traceback 和校验值。
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
    # UTC 让不同 PC/Docker 主机生成的 handoff 可以按字符串稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有输出文本都先统一转字符串再脱敏，避免兼容旧字段时泄露现场材料。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 本机完整路径不应进入 handoff；路径类输入只保留文件名作为可交流引用。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 嵌套摘要递归脱敏，防止 route_progress 或 review decision 中夹带敏感片段。
    if isinstance(value, dict):
        return {str(_safe_text(k)): _safe_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON 和非 object 都转换为 blocked 材料，而不是让 CLI 直接抛异常。
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
    # 兼容字段只取第一个非空文本；没有材料时保持空值，后续状态再保守 blocked。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _has_forbidden_copy(value: Any) -> bool:
    # 对最终输出全文做白名单外关键词检查，比只查 phone summary 更能捕捉新增字段回归。
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _schema_status(payload: dict[str, Any], label: str) -> str:
    # 新 schema 精确匹配；兼容旧 summary 时要求存在核心字段，不能只靠名字猜。
    schema = str(payload.get("schema", "")).strip()
    if label == "pc_route_debug":
        if schema == PC_ROUTE_DEBUG_SCHEMA:
            return "supported"
        if isinstance(payload.get("route_progress"), dict) and "not_proven" in payload:
            return "compatible_summary"
    if label == "operator_review":
        if schema == OPERATOR_REVIEW_SCHEMA:
            return "supported"
        if isinstance(payload.get("next_rehearsal_decision"), dict) and "safe_copy" in payload:
            return "compatible_summary"
    if label == "execution_bundle":
        if schema == EXECUTION_BUNDLE_SCHEMA:
            return "supported"
        if isinstance(payload.get("crosscheck_status"), dict) and "diagnostics_summary" in payload:
            return "compatible_summary"
    return "unsupported"


def _extract_evidence_ref(payload: dict[str, Any]) -> str:
    # evidence_ref 可能在顶层、route_progress 或 diagnostics_summary；只用于同 run 对齐判断。
    route_progress = payload.get("route_progress") if isinstance(payload.get("route_progress"), dict) else {}
    diagnostics = payload.get("diagnostics_summary") if isinstance(payload.get("diagnostics_summary"), dict) else {}
    return _first_text(
        payload.get("evidence_ref"),
        route_progress.get("evidence_ref"),
        diagnostics.get("evidence_ref"),
        default="",
    )


def _source_material(label: str, path: str, payload: dict[str, Any], load_issue: str) -> dict[str, Any]:
    # source_materials 只暴露 schema/status/basename/evidence_ref，不复制 raw artifact。
    schema_status = "" if load_issue else _schema_status(payload, label)
    return {
        "name": label,
        "ref": _safe_ref(path),
        "load_status": "blocked" if load_issue else "loaded",
        "load_issue": load_issue,
        "schema": _safe_text(payload.get("schema", "")) if payload else "",
        "schema_status": schema_status,
        "evidence_ref": _safe_ref(_extract_evidence_ref(payload)) if payload else "",
    }


def _missing_materials(sources: list[dict[str, Any]], expected_ref: str, unsafe_copy: bool) -> list[str]:
    # missing_materials 是 handoff 自身的阻塞项；真实现场材料则放在 required_field_run_materials。
    missing: list[str] = []
    for source in sources:
        name = source["name"]
        if source["load_status"] != "loaded":
            missing.append(f"{name}:{source['load_issue']}")
        elif source["schema_status"] == "unsupported":
            missing.append(f"{name}:unsupported_schema")
        if source["load_status"] == "loaded" and not source.get("evidence_ref"):
            missing.append(f"{name}:missing_evidence_ref")
    loaded_refs = {source["evidence_ref"] for source in sources if source.get("evidence_ref")}
    if expected_ref and _safe_ref(expected_ref) not in loaded_refs:
        missing.append("evidence_ref:requested_ref_not_present_in_sources")
    if len(loaded_refs) > 1:
        missing.append("evidence_ref:sources_do_not_share_same_ref")
    if unsafe_copy:
        missing.append("phone_support_safe_summary:unsafe_material")
    return missing


def _field_run_materials(source_names: set[str]) -> list[dict[str, Any]]:
    # 三个输入材料标记为 prepared，真实现场材料标记 required_next，防止误写成已采集。
    prepared = {
        "pc_route_debug_console_summary": "pc_route_debug" in source_names,
        "route_task_operator_review": "operator_review" in source_names,
        "route_task_execution_bundle": "execution_bundle" in source_names,
    }
    result: list[dict[str, Any]] = []
    for name in FIELD_RUN_MATERIALS:
        state = "prepared_handoff_source" if prepared.get(name, False) else "required_for_next_field_run"
        result.append({"name": name, "state": state})
    return result


def _commands_to_run(evidence_ref: str) -> list[str]:
    # 命令清单只给可执行形状，不包含完整本机路径、串口、token 或机器人 raw response。
    ref = _safe_ref(evidence_ref) or "<same_evidence_ref>"
    return [
        f"rerun PC route debug console summary with evidence_ref={ref}",
        f"rerun route task operator review with evidence_ref={ref}",
        f"collect fixed-route/Nav2 runtime log under evidence_ref={ref}",
        f"collect robot-side task evidence and support-safe mobile summary under evidence_ref={ref}",
        "rerun this readiness gate before any field-run claim",
    ]


def _phone_summary(overall_status: str, evidence_ref: str, missing: list[str]) -> dict[str, Any]:
    # phone_support_safe_summary 只包含固定摘要和计数，不复制路径、topic、串口或 artifact 内容。
    return {
        "title": "Route task field-run readiness",
        "status": overall_status,
        "evidence_ref": _safe_ref(evidence_ref),
        "source_chain": "pc_route_debug + operator_review + execution_bundle",
        "same_evidence_ref_required": True,
        "missing_count": len(missing),
        "next_step": "Collect same evidence_ref field-run materials before claims.",
    }


def _overall_status(load_issues: list[str], unsupported: bool, unsafe: bool, missing: list[str]) -> str:
    # 状态优先级从材料缺失到 schema 不支持，再到输出安全；全部通过才进入 ready handoff。
    if load_issues or any("missing_evidence_ref" in item or "requested_ref" in item or "same_ref" in item for item in missing):
        return "blocked_missing_material"
    if unsupported:
        return "blocked_unsupported_schema"
    if unsafe:
        return "blocked_unsafe_material"
    return "ready_for_field_run_materials"


def build_readiness(
    pc_route_debug: str,
    operator_review: str,
    execution_bundle: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], int]:
    pc_payload, pc_issue = _load_json(pc_route_debug, "pc_route_debug")
    review_payload, review_issue = _load_json(operator_review, "operator_review")
    bundle_payload, bundle_issue = _load_json(execution_bundle, "execution_bundle")

    sources = [
        _source_material("pc_route_debug", pc_route_debug, pc_payload, pc_issue),
        _source_material("operator_review", operator_review, review_payload, review_issue),
        _source_material("execution_bundle", execution_bundle, bundle_payload, bundle_issue),
    ]
    requested_ref = evidence_ref or _first_text(*(source.get("evidence_ref", "") for source in sources), default="")
    schema_unsupported = any(source.get("schema_status") == "unsupported" for source in sources)
    load_issues = [source["load_issue"] for source in sources if source["load_issue"]]

    # 先构造一个不含 phone summary 的骨架，用它检查 source 摘要是否已经有敏感残留。
    source_names = {source["name"] for source in sources if source.get("load_status") == "loaded"}
    preliminary_missing = _missing_materials(sources, requested_ref, False)
    preliminary = {
        "source_materials": sources,
        "required_field_run_materials": _field_run_materials(source_names),
        "missing_materials": preliminary_missing,
        "commands_to_run": _commands_to_run(requested_ref),
    }
    unsafe = _has_forbidden_copy(preliminary)
    missing = _missing_materials(sources, requested_ref, unsafe)
    status = _overall_status(load_issues, schema_unsupported, unsafe, missing)
    phone_summary = _phone_summary(status, requested_ref, missing)
    if _has_forbidden_copy(phone_summary):
        status = "blocked_unsafe_material"
        missing = _missing_materials(sources, requested_ref, True)
        phone_summary = _phone_summary(status, requested_ref, missing)

    readiness = {
        "schema": READINESS_SCHEMA,
        "schema_version": READINESS_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": READINESS_BOUNDARY,
        "overall_status": status,
        "evidence_ref": _safe_ref(requested_ref),
        "same_evidence_ref_required": True,
        "source_materials": sources,
        "required_field_run_materials": _field_run_materials(source_names),
        "missing_materials": missing,
        "commands_to_run": _commands_to_run(requested_ref),
        "phone_support_safe_summary": phone_summary,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    if _has_forbidden_copy(readiness):
        # 二次全文检查是最后防线；命中时不删除字段，而是保守 blocked 并让测试暴露原因。
        readiness["overall_status"] = "blocked_unsafe_material"
        readiness["phone_support_safe_summary"]["status"] = "blocked_unsafe_material"
        if "phone_support_safe_summary:unsafe_material" not in readiness["missing_materials"]:
            readiness["missing_materials"].append("phone_support_safe_summary:unsafe_material")
    return readiness, 0


def write_readiness(readiness: dict[str, Any], output: str) -> None:
    # output 为空时由 --once-json 打 stdout；指定文件时自动建父目录，便于 /tmp 验收。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(readiness, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-light，只读三个 JSON 输入；--once-json 方便验收命令直接检查 stdout。
    parser = argparse.ArgumentParser(description="Generate route/task field-run readiness handoff JSON")
    parser.add_argument("--pc-route-debug", required=True, help="pc_route_debug_console summary JSON")
    parser.add_argument("--operator-review", required=True, help="route_task_rehearsal_operator_review JSON")
    parser.add_argument("--execution-bundle", required=True, help="route_task_rehearsal_execution_bundle JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for all source materials")
    parser.add_argument("--output", default="", help="optional output JSON path")
    parser.add_argument("--once-json", action="store_true", help="print readiness JSON to stdout and exit")
    args = parser.parse_args()

    readiness, exit_code = build_readiness(
        pc_route_debug=args.pc_route_debug,
        operator_review=args.operator_review,
        execution_bundle=args.execution_bundle,
        evidence_ref=args.evidence_ref,
    )
    write_readiness(readiness, args.output)
    if args.once_json or not args.output:
        print(json.dumps(readiness, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field-run readiness: readiness_file:{_safe_ref(args.output)}")
        print(f"overall_status: {readiness['overall_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
