#!/usr/bin/env python3
"""生成 route/task rehearsal operator review package。

该工具只读取 execution bundle JSON，并把操作员下一轮复盘决策写成独立材料。
它不访问硬件、不触发 ROS graph/Nav2、不读取网络，也不扩大 execution bundle 的证据边界。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# review schema 带 v1 后缀，便于 diagnostics/产品侧把它和旧 artifact/bundle 区分开。
REVIEW_SCHEMA = "trashbot.route_task_rehearsal_operator_review.v1"
REVIEW_SCHEMA_VERSION = 1
# evidence boundary 必须单独固定，防止 operator review 被误当成真实上车或 delivery proof。
REVIEW_EVIDENCE_BOUNDARY = "software_proof_docker_route_task_rehearsal_operator_review_gate"
EXECUTION_BUNDLE_SCHEMA = "trashbot.route_task_rehearsal_execution_bundle"
EXECUTION_BUNDLE_BOUNDARY = "software_proof_docker_route_task_rehearsal_execution_bundle_gate"
DEFAULT_OUTPUT_NAME = "route_task_rehearsal_operator_review.json"

# not_proven 保持机器可读枚举；safe_copy 不复制这些枚举，避免手机/支持面出现硬件敏感词。
REVIEW_NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "wave_rover_motion",
    "real_serial_or_uart_feedback",
    "real_hil_pass",
    "same_evidence_ref_hil_reconciliation",
    "dropoff_completion",
    "cancel_completion",
    "delivery_success",
)

# safe_copy 是白名单输出；这些词一旦出现在 safe_copy，说明有人把原始材料或硬件细节泄露进摘要。
SAFE_COPY_FORBIDDEN = (
    "Authorization",
    "OSS_ACCESS_KEY",
    "/cmd_vel",
    "serial",
    "UART",
    "baudrate",
    "WAVE ROVER",
    "traceback",
    "checksum",
    "complete artifact",
)

# 普通字段仍做保守脱敏；review 不需要保留本机绝对路径、凭证、ROS topic 或 raw traceback。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\bOSS_ACCESS_KEY[A-Z_]*\b\s*[:=]\s*[^,\s]+"), "OSS_ACCESS_KEY=[REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_RATE]"),
    (re.compile(r"(?i)WAVE\s+ROVER"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
)


def _utc_now() -> str:
    # UTC 时间让不同机器生成的 review 可以按字符串稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _output_path(output: str, output_dir: str) -> Path:
    # output 优先级高于 output-dir，方便 sprint 验收命令直接指定临时文件。
    if output:
        return Path(output).expanduser()
    if output_dir:
        return Path(output_dir).expanduser() / DEFAULT_OUTPUT_NAME
    return Path(DEFAULT_OUTPUT_NAME)


def _safe_text(value: Any) -> str:
    # review 顶层字段可能来自旧 bundle 或手工 JSON；统一过滤后再写入包。
    text = str(value)
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_value(value: Any) -> Any:
    # 嵌套结构也可能夹带路径或 token，因此递归过滤而不是只处理顶层字段。
    if isinstance(value, dict):
        return {str(_safe_text(k)): _safe_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_safe_value(item) for item in value)
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _safe_ref(path: str) -> str:
    # review 只需要证明“看过哪个 bundle 文件名”，不需要扩散本机绝对路径。
    name = Path(path).name if path else ""
    if not name:
        return "execution_bundle_ref_unavailable"
    return f"execution_bundle_file:{_safe_text(name)}"


def _load_execution_bundle(path: str) -> tuple[dict[str, Any], str]:
    # 缺失或坏 JSON 也要产出 blocked package，所以这里返回 error code 而不是直接退出。
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "missing"
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}, "read_error"
    if not isinstance(payload, dict):
        return {}, "read_error"
    return payload, ""


def _first_text(*values: Any, default: str = "") -> str:
    # 新旧 bundle 字段可能略有差异；只取第一个非空文本，避免猜测业务状态。
    for value in values:
        text = str(value or "").strip()
        if text:
            return _safe_text(text)
    return default


def _normalize_crosscheck_status(bundle: dict[str, Any]) -> dict[str, Any]:
    # crosscheck_status 是 operator review 的主判定源；缺失时保持 missing，而不是从 status 猜。
    source = bundle.get("crosscheck_status")
    if not isinstance(source, dict):
        artifact_status = bundle.get("artifact_status")
        if isinstance(artifact_status, dict) and isinstance(artifact_status.get("crosscheck_status"), dict):
            source = artifact_status.get("crosscheck_status")
    if not isinstance(source, dict):
        return {"status": "missing", "software_mismatches": []}
    mismatches = source.get("software_mismatches")
    if not isinstance(mismatches, list):
        mismatches = source.get("mismatches") if isinstance(source.get("mismatches"), list) else []
    return {
        "status": _first_text(source.get("status"), default="missing"),
        "scope": _first_text(source.get("scope"), default="route_status_task_record"),
        "software_mismatches": [_safe_text(item) for item in mismatches[:12]],
    }


def _normalize_hil_alignment_status(bundle: dict[str, Any]) -> dict[str, Any]:
    # HIL alignment 单独归一化，避免 software crosscheck pass 被误读成真实 HIL pass。
    source = bundle.get("hil_alignment_status")
    if not isinstance(source, dict):
        artifact_status = bundle.get("artifact_status")
        if isinstance(artifact_status, dict) and isinstance(artifact_status.get("hil_alignment_status"), dict):
            source = artifact_status.get("hil_alignment_status")
    if not isinstance(source, dict):
        source = {}
    return {
        "provided": bool(source.get("provided", False)),
        "status": _first_text(source.get("status"), default="not_provided"),
        "alignment_status": _first_text(source.get("alignment_status"), default="not_proven"),
        "evidence_ref_match": bool(source.get("evidence_ref_match", False)),
        "detail": _first_text(source.get("detail"), default="HIL evidence is not proven by this review package."),
    }


def _mismatch_summary(load_issue: str, crosscheck_status: dict[str, Any]) -> dict[str, Any]:
    # mismatch_summary 保留数量和脱敏列表，方便 operator 判断是否先修软件材料。
    if load_issue:
        return {"status": load_issue, "count": 1, "items": [load_issue]}
    items = crosscheck_status.get("software_mismatches")
    if not isinstance(items, list):
        items = []
    return {
        "status": "none" if crosscheck_status.get("status") == "pass" and not items else "present",
        "count": len(items),
        "items": [_safe_text(item) for item in items],
    }


def _decision(
    load_issue: str,
    unsupported_schema: bool,
    unsafe_safe_copy: bool,
    crosscheck_status: dict[str, Any],
    hil_alignment_status: dict[str, Any],
) -> dict[str, Any]:
    # 决策顺序从“材料是否可读”到“安全摘要是否可分享”，再到软件/HIL 状态。
    if load_issue or unsupported_schema:
        return {
            "decision": "regenerate_execution_bundle",
            "reason": "Execution bundle is missing, unreadable, or has an unsupported schema.",
            "operator_action": "Rebuild the execution bundle from route status, replay evidence, and task record JSON.",
        }
    if unsafe_safe_copy:
        return {
            "decision": "fix_safe_copy_whitelist",
            "reason": "Review safe_copy contains text outside the allowed phone-safe whitelist.",
            "operator_action": "Remove unsafe copy fields, regenerate the review, then rerun the gate.",
        }
    if crosscheck_status.get("status") != "pass":
        return {
            "decision": "fix_route_status_task_record_mismatch_then_rerun",
            "reason": "Route status, software replay, or task record do not align.",
            "operator_action": "Fix the route status/task record mismatch and rerun route_task_rehearsal_bundle first.",
        }
    if hil_alignment_status.get("alignment_status") == "not_proven":
        return {
            "decision": "prepare_real_route_task_materials_or_real_hil_reconciliation",
            "reason": "Software crosscheck passed, but real HIL is still not proven.",
            "operator_action": "Prepare real route/task materials or run a same evidence_ref HIL reconciliation before claims.",
        }
    return {
        "decision": "review_aligned_hil_materials_before_claims",
        "reason": "Software crosscheck passed and HIL alignment is present, but delivery remains a separate claim.",
        "operator_action": "Review the aligned materials and keep delivery completion separate from this package.",
    }


def _safe_copy(overall_status: str, crosscheck_status: str, hil_alignment: str, decision: str) -> dict[str, str]:
    # safe_copy 只放固定白名单词汇和归一化状态，不复制 not_proven、路径、错误堆栈或硬件名。
    return {
        "title": "Route task rehearsal review",
        "status": overall_status,
        "crosscheck": crosscheck_status,
        "hil_alignment": hil_alignment,
        "decision": decision,
        "operator_note": "Software review only. Keep real run evidence separate before field claims.",
    }


def _safe_copy_has_forbidden_text(safe_copy: dict[str, str]) -> bool:
    # 这里检查 JSON 编码后的 safe_copy，覆盖键和值，防止后续加字段时绕过白名单。
    encoded = json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
    return any(token in encoded for token in SAFE_COPY_FORBIDDEN)


def _overall_status(load_issue: str, unsupported_schema: bool, crosscheck_status: str, hil_alignment_status: str) -> str:
    # overall_status 是 review 包状态，不是机器人动作状态或 delivery 结果。
    if load_issue == "missing":
        return "blocked_missing_execution_bundle"
    if load_issue == "read_error":
        return "blocked_read_error"
    if unsupported_schema:
        return "blocked_unsupported_schema"
    if crosscheck_status != "pass":
        return "blocked_crosscheck_mismatch"
    if hil_alignment_status == "not_proven":
        return "ready_for_real_route_task_or_hil_reconciliation"
    return "ready_for_operator_review"


def build_review(execution_bundle_path: str) -> tuple[dict[str, Any], int]:
    bundle, load_issue = _load_execution_bundle(execution_bundle_path)
    unsupported_schema = False
    if not load_issue:
        unsupported_schema = (
            bundle.get("schema") != EXECUTION_BUNDLE_SCHEMA
            or bundle.get("evidence_boundary") != EXECUTION_BUNDLE_BOUNDARY
        )

    crosscheck = _normalize_crosscheck_status(bundle)
    hil_alignment = _normalize_hil_alignment_status(bundle)
    status = _overall_status(
        load_issue,
        unsupported_schema,
        str(crosscheck.get("status", "missing")),
        str(hil_alignment.get("alignment_status", "not_proven")),
    )
    safe_copy = _safe_copy(
        status,
        str(crosscheck.get("status", "missing")),
        str(hil_alignment.get("alignment_status", "not_proven")),
        "pending",
    )
    unsafe_safe_copy = _safe_copy_has_forbidden_text(safe_copy)
    decision = _decision(load_issue, unsupported_schema, unsafe_safe_copy, crosscheck, hil_alignment)
    safe_copy["decision"] = decision["decision"]
    unsafe_safe_copy = _safe_copy_has_forbidden_text(safe_copy)
    if unsafe_safe_copy:
        status = "blocked_unsafe_safe_copy"
        decision = _decision(load_issue, unsupported_schema, unsafe_safe_copy, crosscheck, hil_alignment)
        safe_copy["status"] = status
        safe_copy["decision"] = decision["decision"]

    review = {
        "schema": REVIEW_SCHEMA,
        "schema_version": REVIEW_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "overall_status": status,
        "evidence_boundary": REVIEW_EVIDENCE_BOUNDARY,
        "evidence_ref": _first_text(bundle.get("evidence_ref"), default=""),
        "route_task_rehearsal_bundle_ref": _safe_ref(execution_bundle_path),
        "source_bundle": {
            "schema": _safe_text(bundle.get("schema", "")) if bundle else "",
            "evidence_boundary": _safe_text(bundle.get("evidence_boundary", "")) if bundle else "",
            "load_status": "error" if load_issue else ("unsupported_schema" if unsupported_schema else "loaded"),
            "load_issue": load_issue,
        },
        "crosscheck_status": _safe_value(crosscheck),
        "hil_alignment_status": _safe_value(hil_alignment),
        "mismatch_summary": _mismatch_summary(load_issue or ("unsupported_schema" if unsupported_schema else ""), crosscheck),
        "next_rehearsal_decision": decision,
        "not_proven": list(REVIEW_NOT_PROVEN),
        "safe_copy": safe_copy,
        "primary_actions_enabled": False,
        "delivery_success": False,
    }
    # blocked review 也返回 0，调用方能拿到材料；unsafe schema/read_error 状态由 JSON 字段表达。
    return review, 0


def write_review(execution_bundle_path: str, output: str = "", output_dir: str = "") -> Path:
    review, _ = build_review(execution_bundle_path)
    target = _output_path(output, output_dir)
    # 父目录自动创建，方便 /tmp 围栏和 CI 临时目录直接使用。
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # stdout 只打印输出文件名，避免把本机绝对路径扩散到日志或聊天记录。
    print(f"route/task rehearsal operator review: review_file:{_safe_text(target.name)}")
    print(f"overall_status: {review['overall_status']}")
    print(f"next_rehearsal_decision: {review['next_rehearsal_decision']['decision']}")
    return target


def main() -> int:
    # CLI 只接收 execution bundle JSON 和输出位置，保持只读、离线、无硬件依赖。
    parser = argparse.ArgumentParser(description="Generate a route/task rehearsal operator review package")
    parser.add_argument("--execution-bundle", required=True, help="route_task_rehearsal_execution_bundle JSON path")
    parser.add_argument("--output", default="", help="review JSON output path")
    parser.add_argument("--output-dir", default="", help="directory for route_task_rehearsal_operator_review.json")
    args = parser.parse_args()
    write_review(args.execution_bundle, args.output, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
