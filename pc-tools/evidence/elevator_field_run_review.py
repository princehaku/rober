#!/usr/bin/env python3
"""生成 elevator assisted delivery 现场材料复核决策 artifact。

该 CLI 只读取上一轮 material validation artifact/summary，把机器状态整理成
operator 可执行的复核决策、复跑命令和采集清单。它不访问 ROS graph、Nav2
runtime、硬件传输、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# review schema 独立于 validation schema，避免下游把“校验通过”误读为“复核通过”。
REVIEW_SCHEMA = "trashbot.elevator_field_run_review.v1"
REVIEW_SUMMARY_SCHEMA = "trashbot.elevator_field_run_review_summary.v1"
REVIEW_SCHEMA_VERSION = 1
REVIEW_BOUNDARY = "software_proof_docker_elevator_field_review_decision_gate"

# 只支持上一轮 validation artifact 或 summary；其他输入都必须 fail closed。
VALIDATION_SCHEMA = "trashbot.elevator_field_run_material_validation.v1"
VALIDATION_SUMMARY_SCHEMA = "trashbot.elevator_field_run_material_validation_summary.v1"
VALIDATION_BOUNDARY = "software_proof_docker_elevator_field_material_validation_gate"

# 复核决策枚举是 Robot diagnostics/mobile 后续消费的稳定 contract。
READY_DECISION = "ready_for_controlled_elevator_field_rehearsal_not_proven"
DECISION_ORDER = (
    "blocked_invalid_validation",
    "blocked_success_claim",
    "blocked_unsafe_copy",
    "blocked_evidence_ref_mismatch",
    "blocked_missing_materials",
    "blocked_template_materials",
    READY_DECISION,
)

# 采集清单保持和 validation gate 的七类材料一致，保证 operator 看到同一套文件。
CAPTURE_ITEMS = (
    ("door_state.json", "door_state"),
    ("target_floor_confirmation.json", "target_floor_confirmation"),
    ("human_assistance_operator_note.md", "human_assistance"),
    ("nav2_fixed_route_runtime_log.json", "nav2_fixed_route_runtime"),
    ("task_record.json", "task_record"),
    ("completion_signal.json", "completion_signal"),
    ("diagnostics_mobile_safe_summary.json", "diagnostics_mobile_safe_summary"),
)

# not_proven 列表只使用产品能力词，避免把硬件/传输细节带进 phone-safe 输出。
NOT_PROVEN = (
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_record",
    "real_nav2_fixed_route_run",
    "real_robot_motion",
    "real_hardware_feedback",
    "real_hil_pass",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 验收命令会检索这两个 fail-closed 字符串；输出也用它们做 operator 提醒。
BOUNDARY_NOTE = (
    "Docker/local software proof only; delivery_success=false; "
    "primary_actions_enabled=false; elevator_field_review_decision_not_real_delivery=true"
)

# 对外 summary 不能出现这些敏感或容易越界的片段。
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

# 输入材料可能来自手写 JSON，先脱敏再进入决策，避免把 raw 文本扩散到 review。
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
    (re.compile(r"(?i)\bWAVE ROVER\b"), "[REDACTED_ROBOT_BASE]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 便于不同 PC/Docker 主机生成的 review artifact 按字符串排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本先做同一套脱敏，避免新增字段绕过安全出口。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # review 只需要 basename 作为线索，不暴露本机完整路径。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # validation 旧字段可能是字符串或缺失，统一转成有限列表供 summary 展示。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # artifact 最终写盘前递归脱敏，确保嵌套 summary 也走同一规则。
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
    # forbidden 检查用稳定 JSON 字符串，不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 检查键和值，防止把不该进入 support/mobile 的词放进 review。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _any_true_key(value: Any, key: str) -> bool:
    # 成功或控制放行声明可能藏在嵌套 dict/list/string，必须递归拦截。
    if isinstance(value, dict):
        return any((k == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON、非 object 都转成 blocked artifact，而不是未处理异常。
    if not path:
        return {}, "validation_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "validation_missing"
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}, "validation_read_error"
    if not isinstance(payload, dict):
        return {}, "validation_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 嵌套 summary 不一定存在；非 dict 一律当缺失，避免类型异常。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    # full validation artifact 里 summary 是后续消费面；优先读 summary 降低 raw 扩散。
    if payload.get("schema") == VALIDATION_SUMMARY_SCHEMA:
        return payload
    nested = _dict(payload, "material_validation_summary")
    if nested:
        return nested
    return payload


def _material_files(source: dict[str, Any]) -> list[dict[str, str]]:
    # capture checklist 只读取 name/category/status，不复制 validation 的 raw entry。
    files = source.get("material_files")
    if not isinstance(files, list):
        files = []
    entries: list[dict[str, str]] = []
    for name, category in CAPTURE_ITEMS:
        found = next((item for item in files if isinstance(item, dict) and item.get("name") == name), {})
        status = _safe_text(found.get("status", "unknown") if isinstance(found, dict) else "unknown")
        entries.append({"name": name, "category": category, "status": status or "unknown"})
    return entries


def _normalize_validation(payload: dict[str, Any]) -> dict[str, Any]:
    # 统一 full artifact 与 summary 的字段形状，后续决策只看白名单字段。
    source = _source_payload(payload)
    full_schema = _safe_text(payload.get("schema", ""))
    source_schema = _safe_text(source.get("schema", full_schema))
    source_boundary = _safe_text(source.get("evidence_boundary", payload.get("evidence_boundary", "")))
    verdict = _safe_text(
        source.get("material_validation_verdict")
        or source.get("status")
        or payload.get("material_validation_verdict")
        or "missing"
    )
    evidence_ref = _safe_ref(source.get("evidence_ref", payload.get("evidence_ref", "")))
    missing = _safe_list(source.get("missing_materials"))
    templates = _safe_list(source.get("placeholder_materials") or source.get("template_materials"))
    mismatches = _safe_list(source.get("mismatch_reasons"))
    unsafe = verdict == "blocked_unsafe_summary" or _has_forbidden_copy(source)
    success_claim = (
        verdict in {"blocked_delivery_success_claim", "blocked_primary_actions_claim"}
        or _any_true_key(source, "delivery_success")
        or _any_true_key(source, "primary_actions_enabled")
        or _any_true_key(payload, "delivery_success")
        or _any_true_key(payload, "primary_actions_enabled")
    )
    return {
        "schema": source_schema,
        "full_schema": full_schema,
        "evidence_boundary": source_boundary,
        "material_validation_verdict": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": bool(source.get("same_evidence_ref_required", True)),
        "missing_materials": missing,
        "template_materials": templates,
        "mismatch_reasons": mismatches,
        "operator_next_steps": _safe_list(source.get("operator_next_steps"), limit=5),
        "not_proven": _safe_list(source.get("not_proven") or payload.get("not_proven"), limit=20),
        "material_files": _material_files(source),
        "unsafe_copy_detected": unsafe,
        "success_claim_detected": success_claim,
    }


def _schema_status(load_issue: str, normalized: dict[str, Any]) -> str:
    # 只接受上一轮 validation schema/boundary；兼容 summary 但不兼容任意 JSON。
    if load_issue:
        return "not_loaded"
    schema = normalized["schema"]
    boundary = normalized["evidence_boundary"]
    if schema in {VALIDATION_SCHEMA, VALIDATION_SUMMARY_SCHEMA} and boundary == VALIDATION_BOUNDARY:
        return "supported"
    return "unsupported"


def _review_decision(load_issue: str, schema_status: str, normalized: dict[str, Any]) -> str:
    # 决策优先级：输入有效性 -> 越界成功/放行 -> 安全 -> 同 ref -> 材料完整性。
    if load_issue or schema_status != "supported":
        return "blocked_invalid_validation"
    verdict = normalized["material_validation_verdict"]
    if normalized["success_claim_detected"]:
        return "blocked_success_claim"
    if normalized["unsafe_copy_detected"]:
        return "blocked_unsafe_copy"
    if normalized["mismatch_reasons"] or verdict == "blocked_mismatch_evidence_ref":
        return "blocked_evidence_ref_mismatch"
    if normalized["missing_materials"] or verdict in {"blocked_missing_material_dir", "blocked_missing_materials"}:
        return "blocked_missing_materials"
    if normalized["template_materials"] or verdict == "blocked_placeholder_materials":
        return "blocked_template_materials"
    if verdict == "elevator_field_material_validation_ready_not_proven":
        return READY_DECISION
    return "blocked_invalid_validation"


def _blocked_categories(decision: str, normalized: dict[str, Any]) -> list[str]:
    # categories 是给 mobile/diagnostics 展示的紧凑原因，不展开 raw validation。
    categories: list[str] = []
    if decision == "blocked_invalid_validation":
        categories.append("invalid_validation")
    if decision == "blocked_success_claim":
        categories.append("success_or_control_claim")
    if decision == "blocked_unsafe_copy":
        categories.append("unsafe_copy")
    if decision == "blocked_evidence_ref_mismatch":
        categories.append("evidence_ref_mismatch")
    if decision == "blocked_missing_materials":
        categories.append("missing_materials")
    if decision == "blocked_template_materials":
        categories.append("template_materials")
    if normalized["missing_materials"]:
        categories.append("missing_count:%d" % len(normalized["missing_materials"]))
    if normalized["template_materials"]:
        categories.append("template_count:%d" % len(normalized["template_materials"]))
    if normalized["mismatch_reasons"]:
        categories.append("mismatch_count:%d" % len(normalized["mismatch_reasons"]))
    return categories


def _operator_next_steps(decision: str, evidence_ref: str, normalized: dict[str, Any]) -> list[str]:
    # next steps 只描述复核/补采动作，不给任何机器人控制动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == READY_DECISION:
        steps = [
            f"Review the aligned elevator materials under evidence_ref={ref}.",
            "Prepare a controlled elevator field rehearsal with a human observer and stop path.",
            "Keep delivery_success=false until real dropoff/cancel completion evidence exists.",
        ]
    elif decision == "blocked_missing_materials":
        names = normalized["missing_materials"] or [item["name"] for item in normalized["material_files"] if item["status"] in {"missing", "bad_json", "not_object", "read_error"}]
        steps = [
            f"Collect or repair missing elevator materials for evidence_ref={ref}.",
            f"Missing or invalid files: {', '.join(names[:5])}.",
            "Rerun validation, then rerun this review CLI.",
        ]
    elif decision == "blocked_template_materials":
        names = normalized["template_materials"] or [item["name"] for item in normalized["material_files"] if item["status"] == "placeholder_template"]
        steps = [
            f"Replace template elevator materials for evidence_ref={ref}.",
            f"Template files: {', '.join(names[:5])}.",
            "Rerun validation after field notes are filled by an operator.",
        ]
    elif decision == "blocked_evidence_ref_mismatch":
        steps = [
            f"Re-export all elevator, route, task, completion, and summary materials under the same evidence_ref={ref}.",
            "Do not combine materials from different runs.",
            "Rerun validation until mismatch_reasons is empty.",
        ]
    elif decision == "blocked_unsafe_copy":
        steps = [
            "Remove credentials, raw control topics, device paths, transport details, tracebacks, and raw robot responses from summaries.",
            f"Regenerate phone-safe summaries for evidence_ref={ref}.",
            "Rerun validation and this review before sharing to support/mobile.",
        ]
    elif decision == "blocked_success_claim":
        steps = [
            "Remove delivery or primary action claims from the material package.",
            f"Keep delivery_success=false and primary_actions_enabled=false for evidence_ref={ref}.",
            "Rerun validation before any operator review decision.",
        ]
    else:
        steps = [
            "Regenerate elevator_field_run_material_validation.py output from a supported validation artifact.",
            f"Keep every material on evidence_ref={ref}.",
            "Rerun this review CLI after validation is readable and supported.",
        ]
    return [_safe_text(step) for step in steps[:5]]


def _commands_to_rerun(decision: str, evidence_ref: str, normalized: dict[str, Any]) -> list[str]:
    # 命令使用占位符，不复制本机绝对路径，方便 operator 在 PC 上替换。
    ref = evidence_ref or "<same_evidence_ref>"
    commands: list[str] = []
    if decision in {"blocked_missing_materials", "blocked_template_materials"}:
        commands.append(f"collect elevator material files under evidence_ref={ref}")
    if decision == "blocked_evidence_ref_mismatch":
        commands.append(f"re-export elevator field materials so every file uses evidence_ref={ref}")
    if decision == "blocked_unsafe_copy":
        commands.append("regenerate diagnostics_mobile_safe_summary.json with whitelist-only copy")
    if decision == "blocked_success_claim":
        commands.append("remove delivery/control claims and keep fail-closed fields false")
    if decision == "blocked_invalid_validation":
        commands.append("regenerate elevator_field_run_material_validation.py output from the material directory")
    commands.append(
        "python3 pc-tools/evidence/elevator_field_run_material_validation.py "
        "--material-dir <elevator_material_dir> --evidence-ref %s --output <validation_json>" % ref
    )
    commands.append(
        "python3 pc-tools/evidence/elevator_field_run_review.py "
        "--validation-json <validation_json> --once-json"
    )
    if decision == READY_DECISION:
        commands.append("prepare controlled elevator rehearsal packet; keep not_proven until real field evidence is reviewed")
    if normalized["operator_next_steps"] and decision != READY_DECISION:
        commands.append("use validation operator_next_steps as source-specific repair hints")
    return [_safe_text(command) for command in commands[:6]]


def _capture_checklist(normalized: dict[str, Any], decision: str) -> list[dict[str, Any]]:
    # checklist 给现场人员逐项补材料；只保留状态、是否阻塞和补采提示。
    missing = set(normalized["missing_materials"])
    templates = set(normalized["template_materials"])
    checklist: list[dict[str, Any]] = []
    for item in normalized["material_files"]:
        name = item["name"]
        status = item["status"]
        blocked = name in missing or name in templates or status in {"missing", "bad_json", "not_object", "read_error", "placeholder_template"}
        checklist.append(
            {
                "name": name,
                "category": item["category"],
                "status": status,
                "operator_action": "collect_or_replace_material" if blocked else "keep_for_review",
                "blocks_review": bool(blocked or decision != READY_DECISION and decision != "blocked_invalid_validation"),
            }
        )
    return checklist


def _review_summary(
    decision: str,
    evidence_ref: str,
    categories: list[str],
    steps: list[str],
    commands: list[str],
    checklist: list[dict[str, Any]],
) -> dict[str, Any]:
    # summary 是 Robot diagnostics/mobile 只读消费面，必须短、白名单、fail closed。
    return {
        "schema": REVIEW_SUMMARY_SCHEMA,
        "schema_version": REVIEW_SCHEMA_VERSION,
        "evidence_boundary": REVIEW_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "evidence_ref": evidence_ref,
        "blocked_categories": categories,
        "operator_next_steps": steps[:4],
        "commands_to_rerun": commands[:4],
        "capture_checklist": checklist,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_review(validation_json: str) -> tuple[dict[str, Any], int]:
    # 测试和 CLI 共用入口，保证本地 Python 环境即可跑通。
    payload, load_issue = _load_json(validation_json)
    normalized = _normalize_validation(payload) if payload else {
        "schema": "",
        "full_schema": "",
        "evidence_boundary": "",
        "material_validation_verdict": "missing",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "missing_materials": [],
        "template_materials": [],
        "mismatch_reasons": [],
        "operator_next_steps": [],
        "not_proven": [],
        "material_files": [{"name": name, "category": category, "status": "unknown"} for name, category in CAPTURE_ITEMS],
        "unsafe_copy_detected": False,
        "success_claim_detected": False,
    }
    schema_status = _schema_status(load_issue, normalized)
    decision = _review_decision(load_issue, schema_status, normalized)
    categories = _blocked_categories(decision, normalized)
    steps = _operator_next_steps(decision, normalized["evidence_ref"], normalized)
    commands = _commands_to_rerun(decision, normalized["evidence_ref"], normalized)
    checklist = _capture_checklist(normalized, decision)
    summary = _review_summary(decision, normalized["evidence_ref"], categories, steps, commands, checklist)
    artifact = {
        "schema": REVIEW_SCHEMA,
        "schema_version": REVIEW_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": REVIEW_BOUNDARY,
        "same_evidence_ref_required": True,
        "evidence_ref": normalized["evidence_ref"],
        "review_decision": decision,
        "decision_order": list(DECISION_ORDER),
        "source_validation": {
            "ref": _safe_ref(validation_json),
            "load_issue": load_issue,
            "schema_status": schema_status,
            "schema": normalized["schema"],
            "full_schema": normalized["full_schema"],
            "evidence_boundary": normalized["evidence_boundary"],
            "material_validation_verdict": normalized["material_validation_verdict"],
        },
        "blocked_categories": categories,
        "missing_materials": normalized["missing_materials"],
        "template_materials": normalized["template_materials"],
        "mismatch_reasons": normalized["mismatch_reasons"],
        "capture_checklist": checklist,
        "operator_next_steps": steps,
        "commands_to_rerun": commands,
        "review_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "real_elevator",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    if _has_forbidden_copy(artifact):
        # 最后一层保险：若 summary 仍不安全，输出改为 blocked_unsafe_copy 但不泄露原文。
        artifact["review_decision"] = "blocked_unsafe_copy"
        artifact["blocked_categories"] = ["unsafe_copy"]
        artifact["review_summary"]["status"] = "blocked_unsafe_copy"
        artifact["review_summary"]["review_decision"] = "blocked_unsafe_copy"
        artifact["review_summary"]["blocked_categories"] = ["unsafe_copy"]
    return artifact, 0


def write_review(artifact: dict[str, Any], output: str) -> None:
    # output 为空时只打印 stdout；指定路径时自动建父目录用于 sprint 证据归档。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 单输入单输出，方便承接上一轮 validation artifact。
    parser = argparse.ArgumentParser(description="Generate elevator field-run operator review decision artifact")
    parser.add_argument("--validation-json", required=True, help="elevator field-run material validation JSON path")
    parser.add_argument("--output", default="", help="optional review artifact JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, exit_code = build_review(args.validation_json)
    write_review(artifact, args.output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"elevator field-run review: review_file:{_safe_ref(args.output)}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
