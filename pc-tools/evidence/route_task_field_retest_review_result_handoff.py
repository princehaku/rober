#!/usr/bin/env python3
"""生成 route/task field retest review result handoff artifact。

该 gate 只读取上一轮 callback review decision 的 artifact、summary 或 wrapper/nested
JSON，把 review decision 映射成 result-intake 前交接状态。它不读取真实材料目录，
不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、cloud 或 phone，也不
触发 result intake 或任何机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# handoff 是 callback review decision 与 result intake 之间的新契约。
HANDOFF_SCHEMA = "trashbot.route_task_field_retest_review_result_handoff.v1"
HANDOFF_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_review_result_handoff_summary.v1"
SCHEMA_VERSION = 1
HANDOFF_BOUNDARY = "software_proof_docker_route_task_field_retest_review_result_handoff_gate"

# 只允许上一轮 callback review decision 进入本 gate，避免跳过 review。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_callback_review_decision.v1",
    "trashbot.route_task_field_retest_callback_review_decision_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_callback_review_decision_gate"

# 八类材料仍只是 result-intake 前的 metadata checklist。
REQUIRED_EVIDENCE_PACKET = (
    "nav2_or_fixed_route_runtime_log",
    "route_completion_signal",
    "task_record",
    "door_state",
    "target_floor_confirmation",
    "human_assistance_note",
    "dropoff_or_cancel_completion",
    "delivery_result",
)

# not_proven 固定覆盖真实路线、真实电梯、终态、手机、HIL 和 O5 外部证据缺口。
NOT_PROVEN = (
    "real_nav2_fixed_route_runtime_log_content",
    "real_route_completion_pass",
    "real_task_record_runtime",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_note",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result_reviewed_success",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

BOUNDARY_NOTE = (
    "software_proof_docker_route_task_field_retest_review_result_handoff_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只消费 callback review decision，不读材料目录。
# 设计约束 02：handoff_status 只表达下一步交接，不证明现场结果。
# 设计约束 03：ready 分支仍保持 not_proven，不能改变 Robot/mobile action。
# 设计约束 04：source decision 是唯一映射来源，不重新解释材料内容。
# 设计约束 05：unsupported schema/boundary 必须 fail closed。
# 设计约束 06：unsafe copy 与 success/control claim 必须阻断。
# 设计约束 07：same_evidence_ref_required 固定为 true，维持证据链主键。
# 设计约束 08：result_intake_readiness 是只读摘要，不执行 result intake。
# 设计约束 09：summary 是 Robot/mobile 可消费面，只输出白名单字段。
# 设计约束 10：wrapper/nested JSON 只递归固定 key，避免采信 raw payload。
# 设计约束 11：缺 evidence_ref 不进入 ready，因为下游无法复账。
# 设计约束 12：输入的 missing_materials 只透传 id，不打开材料。
# 设计约束 13：rerun command 只是 PC operator 提示，不访问 ROS 或硬件。
# 设计约束 14：输出递归脱敏，blocked artifact 也不泄漏 raw source。
# 设计约束 15：dependency-free，便于 macOS PC 与 Docker 本地验证。
# 设计约束 16：exit code 保持 0，让 blocked handoff 也能作为证据落盘。
# 设计约束 17：文档和单测同步覆盖所有 decision mapping。
# 设计约束 18：该 gate 不推进 Objective 5 external proof。
# 设计约束 19：该 gate 不替代 result intake 或 result reconciliation。
# 设计约束 20：该 gate 不触发 fixed-route、Nav2、dropoff 或 cancel 动作。

DECISION_MAPPING = {
    "ready_for_result_intake": ("ready_for_result_intake_handoff", "ready_for_result_material_intake"),
    "needs_material_backfill": ("blocked_until_material_backfill", "not_ready"),
    "evidence_ref_mismatch_rerun": ("blocked_until_same_evidence_ref_rerun", "not_ready"),
    "unsupported_callback_schema": ("blocked_unsupported_source_schema", "not_ready"),
    "blocked_unsafe_callback": ("blocked_unsafe_source_review", "not_ready"),
    "blocked_success_claim": ("blocked_unsafe_source_review", "not_ready"),
}

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

# 成功或动作授权不能通过 review handoff 进入 result intake 前置面。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bcancel\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
)

# 本机绝对路径不能进入 phone-safe handoff。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# blocked 输出也先脱敏，避免错误材料污染 sprint artifact。
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
    (re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"), r"\1[REDACTED_PATH]"),
    (re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 时间让不同 PC/Docker 主机产物可排序审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本先脱敏，再进入 artifact 或 summary。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 若被误填成本机路径，只保留 basename。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线，防止新增嵌套字段绕过 helper。
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
    # 安全扫描使用稳定 JSON，覆盖键名和值。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # forbidden copy 命中说明输入不适合进入 Robot/mobile 摘要。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY) or any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_claim(value: Any) -> bool:
    # 布尔字段和自由文案都检查，避免 success/control claim 穿透。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都输出 blocked handoff，便于留痕。
    if not path:
        return {}, "callback_review_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "callback_review_missing"
    except json.JSONDecodeError:
        return {}, "callback_review_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "callback_review_read_error"
    if not isinstance(payload, dict):
        return {}, "callback_review_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段；字符串 wrapper 不可信。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 字段位置不同，取首个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "route_task_field_retest_callback_review_decision",
        "route_task_field_retest_callback_review_decision_summary",
        "route_task_field_retest_review_result_handoff",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 schema 命中的 review 对象；否则保留顶层用于 unsupported 解释。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _list_text(value: Any, limit: int = 24) -> list[str]:
    # 下游摘要只接受扁平字符串列表，避免复制完整 raw object。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit] if isinstance(item, (str, int, float, bool))]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _source_decision(source: dict[str, Any]) -> str:
    # review_decision 是上游主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(_first_text(source.get("review_decision"), source.get("status"), safe_copy.get("review_decision"), default=""))


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层或 safe_copy 取，最终仍做路径收敛。
    safe_copy = _dict(source, "safe_copy")
    return _safe_ref(_first_text(source.get("safe_evidence_ref"), source.get("evidence_ref"), safe_copy.get("evidence_ref"), default=""))


def _missing_materials(source: dict[str, Any]) -> list[str]:
    # missing_materials 只作为 id 列表透传，不打开或读取材料。
    safe_copy = _dict(source, "safe_copy")
    return _list_text(source.get("missing_materials") or safe_copy.get("missing_materials"))


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止其它 gate JSON 混入。
    schema = str(source.get("schema", "")).strip()
    boundary = str(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    return schema in SOURCE_SCHEMAS and (not boundary or boundary == SOURCE_BOUNDARY)


def _handoff_decision(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_decision: str,
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 ready handoff。
    if load_issue or not _schema_supported(source):
        source_decision = "unsupported_callback_schema"
    if success_claim:
        source_decision = "blocked_success_claim"
    elif unsafe:
        source_decision = "blocked_unsafe_callback"
    elif requested_ref and source_ref and requested_ref != source_ref:
        source_decision = "evidence_ref_mismatch_rerun"
    elif source_decision not in DECISION_MAPPING:
        source_decision = "unsupported_callback_schema"
    handoff_status, readiness = DECISION_MAPPING[source_decision]
    reasons: list[str] = []
    if load_issue:
        reasons.append(load_issue)
    if requested_ref and source_ref and requested_ref != source_ref:
        reasons.append(f"requested_ref:{requested_ref}!={source_ref}")
    if unsafe:
        reasons.append("unsafe_copy_detected")
    if success_claim:
        reasons.append("success_or_primary_action_claim_detected")
    if not reasons and handoff_status != "ready_for_result_intake_handoff":
        reasons.append(source_decision)
    return handoff_status, readiness, reasons


def _result_intake_readiness(readiness: str, handoff_status: str) -> dict[str, Any]:
    # readiness 是只读状态，不会触发 result intake 或 Robot action。
    return {
        "state": readiness,
        "ready": readiness == "ready_for_result_material_intake",
        "blocked_by": "" if readiness == "ready_for_result_material_intake" else handoff_status,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _owner_handoff(handoff_status: str, evidence_ref: str, source_decision: str, missing: list[str]) -> dict[str, Any]:
    # owner handoff 只分配复账责任，不授权 Robot/mobile 任何主动作。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
        "handoff_status": handoff_status,
        "source_review_decision": source_decision,
        "handoff_note": f"Prepare result-intake handoff for evidence_ref={ref}; keep Robot/mobile read-only.",
        "missing_materials": missing,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(evidence_ref: str) -> dict[str, str]:
    # command labels 只给 PC operator 复跑，不访问 ROS graph、Nav2 或硬件。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "review_result_handoff": (
            "python3 pc-tools/evidence/route_task_field_retest_review_result_handoff.py "
            f"--callback-review-json /tmp/route_task_field_retest_callback_review_decision_summary.json --evidence-ref {ref} --once-json"
        ),
        "result_intake_next_manual": (
            "python3 pc-tools/evidence/route_task_field_retest_result_intake.py "
            f"--result-json /tmp/route_task_field_retest_result_materials_summary.json --evidence-ref {ref}"
        ),
    }


def _safe_copy(handoff_status: str, readiness: str, evidence_ref: str, source_decision: str, missing: list[str]) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料内容。
    return {
        "schema": f"{HANDOFF_SUMMARY_SCHEMA}.safe_copy",
        "handoff_status": handoff_status,
        "result_intake_readiness": readiness,
        "source_review_decision": source_decision,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "evidence_ref": evidence_ref,
        "missing_materials": missing,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_review_result_handoff(
    callback_review_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 callback review decision，生成 result-intake 前 handoff artifact。"""
    payload, load_issue = _load_json(callback_review_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    source_decision = _source_decision(source) if source else "unsupported_callback_schema"
    missing = _missing_materials(source) if source else []
    unsafe = bool(payload) and _has_forbidden_copy(source)
    success_claim = bool(payload) and _has_success_claim(source)
    handoff_status, readiness, status_reasons = _handoff_decision(
        load_issue,
        source,
        requested_ref,
        source_ref,
        source_decision,
        unsafe,
        success_claim,
    )
    safe_copy = _safe_copy(handoff_status, readiness, evidence_ref_out, source_decision, missing)
    owner_handoff = _owner_handoff(handoff_status, evidence_ref_out, source_decision, missing)
    summary = {
        "schema": HANDOFF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": status_reasons,
        "source_review_decision": source_decision,
        "result_intake_readiness": readiness,
        "result_intake_readiness_detail": _result_intake_readiness(readiness, handoff_status),
        "evidence_ref": evidence_ref_out,
        "safe_evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "missing_materials": missing,
        "required_evidence_packet": list(REQUIRED_EVIDENCE_PACKET),
        "owner_handoff": owner_handoff,
        "rerun_commands": _rerun_commands(evidence_ref_out),
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": HANDOFF_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": status_reasons,
        "source_callback_review": {
            "load_issue": load_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "source_review_decision": source_decision,
            "evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "source_review_decision": source_decision,
        "result_intake_readiness": readiness,
        "result_intake_readiness_detail": _result_intake_readiness(readiness, handoff_status),
        "evidence_ref": evidence_ref_out,
        "safe_evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "missing_materials": missing,
        "required_evidence_packet": list(REQUIRED_EVIDENCE_PACKET),
        "owner_handoff": owner_handoff,
        "rerun_commands": _rerun_commands(evidence_ref_out),
        "safe_copy": safe_copy,
        "route_task_field_retest_review_result_handoff_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "ros_graph",
            "nav2_runtime",
            "serial_uart",
            "wave_rover",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device",
            "robot_action",
            "result_intake_execution",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return _safe_value(artifact), _safe_value(summary), 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只打印 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，便于 PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate a route/task field retest review result handoff artifact")
    parser.add_argument("--callback-review-json", required=True, help="callback review decision artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this result handoff")
    parser.add_argument("--output", default="", help="optional handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print handoff artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_review_result_handoff(args.callback_review_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_review_result_handoff: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"review_result_handoff_summary_file: {_safe_ref(args.summary_output)}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
