#!/usr/bin/env python3
"""生成 route/task field retest acceptance execution callback review handoff artifact。

该 PC-only gate 只读取上一轮 acceptance execution callback review decision 的 artifact、
summary 或 wrapper/nested JSON，把复核决策转成下一步 handoff package。它不读取真实
材料目录、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、外部云、4G、
OSS/CDN、DB/queue 或真实手机/browser，也不触发任何机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本 gate 是 acceptance execution callback review decision 后的新契约，不能复用旧 schema。
HANDOFF_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff.v1"
HANDOFF_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff_summary.v1"
SCHEMA_VERSION = 1
HANDOFF_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate"

# 只接受上一轮 review decision，避免跳过决策层直接包装 callback 或现场材料。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_acceptance_execution_callback_review_decision.v1",
    "trashbot.route_task_field_retest_acceptance_execution_callback_review_decision_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate"

# not_proven 固定覆盖真实路线、电梯、终态、手机、HIL 和 O5 外部证据缺口。
NOT_PROVEN = (
    "real_nav2_fixed_route_runtime",
    "real_fixed_route_field_rerun",
    "real_route_completion_signal",
    "real_task_record",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_record",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# rg 围栏依赖这些 literal，人工复盘也能快速识别本 gate 的边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_acceptance_execution_callback_review_handoff; "
    "software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false; "
    "ready_for_acceptance_execution_callback_review_handoff; needs_owner_follow_up; "
    "needs_acceptance_execution_callback_rerun; evidence_ref_mismatch_rerun; "
    "blocked_unsafe_review_handoff"
)

# 设计约束 01：本 gate 只消费 review decision，不读取材料目录。
# 设计约束 02：handoff_status 只表达交接状态，不证明现场结果。
# 设计约束 03：ready 分支仍保持 not_proven，不能改变 Robot/mobile action。
# 设计约束 04：source review_decision 是唯一映射来源，不重新解释材料内容。
# 设计约束 05：unsupported schema/boundary 或缺 decision 必须 fail closed。
# 设计约束 06：unsafe copy 与 success/control claim 必须阻断。
# 设计约束 07：same_evidence_ref_required 固定为 true，维持证据链主键。
# 设计约束 08：handoff package 是只读包，不执行 field rerun。
# 设计约束 09：summary 是 Robot/mobile 可消费面，只输出白名单字段。
# 设计约束 10：wrapper/nested JSON 只递归固定 key，避免采信 raw payload。
# 设计约束 11：缺 evidence_ref 不进入 ready，因为下游无法复账。
# 设计约束 12：owner_handoff 只透传安全摘要，不打开材料。
# 设计约束 13：rerun hint 只是 PC operator 提示，不访问 ROS 或硬件。
# 设计约束 14：输出递归脱敏，blocked artifact 也不泄漏 raw source。
# 设计约束 15：dependency-free，便于 macOS PC 与 Docker 本地验证。
# 设计约束 16：exit code 保持 0，让 blocked handoff 也能作为证据落盘。
# 设计约束 17：文档和单测同步覆盖所有 handoff status mapping。
# 设计约束 18：该 gate 不推进 Objective 5 external proof。
# 设计约束 19：该 gate 不替代真实 result review 或 route execution。
# 设计约束 20：该 gate 不触发 fixed-route、Nav2、dropoff 或 cancel 动作。
# 设计约束 21：ready 只代表 handoff package 可交接，不代表现场材料已经通过。
# 设计约束 22：needs_owner_follow_up 只要求 owner 回填，不授权任何自动驾驶动作。
# 设计约束 23：needs_acceptance_execution_callback_rerun 保留复跑路径。
# 设计约束 24：evidence_ref_mismatch_rerun 优先保护同一证据链主键。
# 设计约束 25：blocked_unsafe_review_handoff 统一覆盖敏感信息和控制声明。

DECISION_TO_HANDOFF = {
    "ready_for_controlled_field_rerun": "ready_for_acceptance_execution_callback_review_handoff",
    "needs_material_backfill": "needs_owner_follow_up",
    "evidence_ref_mismatch_rerun": "evidence_ref_mismatch_rerun",
    "rejected_unsafe_callback": "blocked_unsafe_review_handoff",
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

# 成功或动作授权不能通过 handoff 进入下游。
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
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action)\b"),
)

# 本机绝对路径不能进入 review handoff。
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
        return {}, "callback_review_decision_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "callback_review_decision_missing"
    except json.JSONDecodeError:
        return {}, "callback_review_decision_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "callback_review_decision_read_error"
    if not isinstance(payload, dict):
        return {}, "callback_review_decision_not_object"
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
        "route_task_field_retest_acceptance_execution_callback_review_decision",
        "route_task_field_retest_acceptance_execution_callback_review_decision_summary",
        "route_task_field_retest_acceptance_execution_callback_review_handoff",
        "route_task_field_retest_acceptance_execution_callback_review_handoff_summary",
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
    # 优先选择 schema 命中的 review decision 对象；否则保留顶层用于 unsupported 解释。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _list_items(value: Any, limit: int = 24) -> list[Any]:
    # owner follow-up 摘要只接受 list，避免弱类型字符串被当成材料列表。
    if not isinstance(value, list):
        return []
    return _safe_value(value[:limit])


def _list_text(value: Any, limit: int = 24) -> list[str]:
    # next evidence/rerun 摘要只输出扁平文本，避免复制完整 raw object。
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
    # safe evidence_ref 从顶层、summary 或 safe_copy 取，最终仍做路径收敛。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return _safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _same_ref_status(source: dict[str, Any]) -> dict[str, Any]:
    # same-evidence-ref 兼容 object 与字符串两种 summary 形态。
    safe_copy = _dict(source, "safe_copy")
    raw = source.get("same_evidence_ref_match", safe_copy.get("same_evidence_ref_match"))
    if isinstance(raw, dict):
        return _safe_value(raw)
    if isinstance(raw, str):
        return {"status": _safe_text(raw)}
    return {"status": "missing_evidence_ref"}


def _source_owner_handoff(source: dict[str, Any]) -> list[Any]:
    # owner handoff 可来自上游顶层或 safe_copy；这里只安全透传摘要。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        item = candidate.get("owner_handoff")
        if isinstance(item, dict):
            return [_safe_value(item)]
        items = _list_items(item)
        if items:
            return items
    return []


def _source_next_required(source: dict[str, Any]) -> list[str]:
    # next_required_evidence 是 handoff 前行动清单，不代表已完成。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        items = _list_text(candidate.get("next_required_evidence"))
        if items:
            return items
    return []


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止其它 gate JSON 混入。
    schema = str(source.get("schema", "")).strip()
    boundary = str(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    return schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY


def _handoff_status(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_decision: str,
    same_ref: dict[str, Any],
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 ready handoff。
    reasons: list[str] = []
    if load_issue:
        reasons.append(load_issue)
    if success_claim:
        return "blocked_unsafe_review_handoff", reasons + ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked_unsafe_review_handoff", reasons + ["unsafe_copy_detected"]
    if load_issue or not _schema_supported(source):
        return "needs_acceptance_execution_callback_rerun", reasons + ["unsupported_acceptance_execution_callback_review_decision_schema_or_boundary"]
    if source.get("same_evidence_ref_required") is not True:
        return "evidence_ref_mismatch_rerun", reasons + ["same_evidence_ref_required_not_true"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun", reasons + [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref.get("status") not in {"matched", "ready"}:
        return "evidence_ref_mismatch_rerun", reasons + [f"same_evidence_ref:{same_ref.get('status', 'missing')}"]
    if not source_ref:
        return "evidence_ref_mismatch_rerun", reasons + ["safe_evidence_ref_missing"]
    if not source_decision:
        return "needs_acceptance_execution_callback_rerun", reasons + ["source_review_decision_missing"]
    if source_decision not in DECISION_TO_HANDOFF:
        return "needs_acceptance_execution_callback_rerun", reasons + [f"unsupported_source_review_decision:{source_decision}"]
    return DECISION_TO_HANDOFF[source_decision], reasons


def _handoff_package(handoff_status: str, evidence_ref: str, source_decision: str) -> dict[str, Any]:
    # handoff package 是只读验收入口，不触发真正 field rerun。
    ready = handoff_status == "ready_for_acceptance_execution_callback_review_handoff"
    return {
        "ready": ready,
        "status": handoff_status,
        "source_review_decision": source_decision,
        "safe_evidence_ref": evidence_ref,
        "requirements": [
            "accepted_callback_review_decision",
            "same_evidence_ref_match",
            "owner_handoff_ready",
            "safe_next_required_evidence",
            "rerun_path_if_not_ready",
        ],
        "handoff_entry": "acceptance_execution_callback_review_handoff_ready" if ready else "acceptance_execution_callback_review_handoff_blocked",
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _owner_handoff(handoff_status: str, evidence_ref: str, source_decision: str, upstream_handoff: list[Any]) -> list[dict[str, Any]]:
    # owner handoff 只分派材料责任，不授权 Robot/mobile 任何动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == "ready_for_acceptance_execution_callback_review_handoff":
        action = "handoff_ready_package_before_acceptance_execution_callback_follow_up"
    elif handoff_status == "needs_owner_follow_up":
        action = "backfill_owner_material_before_acceptance_execution_callback_follow_up"
    elif handoff_status == "needs_acceptance_execution_callback_rerun":
        action = "repair_acceptance_execution_callback_review_decision_and_rerun_handoff"
    elif handoff_status == "evidence_ref_mismatch_rerun":
        action = "rerun_acceptance_execution_callback_review_decision_with_same_evidence_ref"
    else:
        action = "remove_unsafe_copy_or_control_claim_before_rerun"
    return [
        {
            "owner": "Autonomy Algorithm Engineer",
            "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
            "action": action,
            "safe_evidence_ref": ref,
            "source_review_decision": source_decision,
            "upstream_owner_handoff": upstream_handoff,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    ]


def _rerun_hint(handoff_status: str, evidence_ref: str) -> dict[str, Any]:
    # rerun hint 只给 PC operator 复跑，不访问 ROS graph、Nav2 或硬件。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "required": handoff_status != "ready_for_acceptance_execution_callback_review_handoff",
        "status": handoff_status,
        "safe_evidence_ref": ref,
        "commands": [
            "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_decision.py "
            f"--callback-intake-json <callback_intake.json> --evidence-ref {ref} --once-json",
            "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py "
            f"--callback-review-decision-json <callback_review_decision.json> --evidence-ref {ref} --once-json",
        ],
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(handoff_status: str, evidence_ref: str, upstream_next: list[str]) -> list[str]:
    # 下一步只列证据动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == "ready_for_acceptance_execution_callback_review_handoff":
        return upstream_next or [f"Prepare acceptance execution callback review handoff for evidence_ref={ref}."]
    if handoff_status == "needs_owner_follow_up":
        return upstream_next or [f"Backfill owner follow-up items for evidence_ref={ref} before handoff."]
    if handoff_status == "needs_acceptance_execution_callback_rerun":
        return [f"Regenerate supported acceptance execution callback review decision for evidence_ref={ref}."]
    if handoff_status == "evidence_ref_mismatch_rerun":
        return [f"Regenerate callback review decision and handoff with one evidence_ref={ref}."]
    return ["Regenerate callback review decision without raw paths, credentials, runtime topics, hardware transport detail, unsafe material identifiers, control claims, or success claims."]


def _safe_copy(
    handoff_status: str,
    evidence_ref: str,
    source_decision: str,
    handoff_package: dict[str, Any],
    next_required: list[str],
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料内容。
    return {
        "schema": f"{HANDOFF_SUMMARY_SCHEMA}.safe_copy",
        "handoff_status": handoff_status,
        "status": handoff_status,
        "source_review_decision": source_decision,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "handoff_ready": bool(handoff_package.get("ready")),
        "next_required_evidence": next_required,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_acceptance_execution_callback_review_handoff(
    callback_review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 acceptance execution callback review decision，生成 handoff artifact。"""
    payload, load_issue = _load_json(callback_review_decision_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    source_decision = _source_decision(source) if source else ""
    same_ref = _same_ref_status(source) if source else {"status": "missing_evidence_ref"}
    upstream_handoff = _source_owner_handoff(source) if source else []
    upstream_next = _source_next_required(source) if source else []
    unsafe = bool(payload) and _has_forbidden_copy(source)
    success_claim = bool(payload) and _has_success_claim(source)
    handoff_status, status_reasons = _handoff_status(
        load_issue,
        source,
        requested_ref,
        source_ref,
        source_decision,
        same_ref,
        unsafe,
        success_claim,
    )
    handoff_package = _handoff_package(handoff_status, evidence_ref_out, source_decision)
    owner_handoff = _owner_handoff(handoff_status, evidence_ref_out, source_decision, upstream_handoff)
    rerun_hint = _rerun_hint(handoff_status, evidence_ref_out)
    next_required = _next_required_evidence(handoff_status, evidence_ref_out, upstream_next)
    safe_copy = _safe_copy(handoff_status, evidence_ref_out, source_decision, handoff_package, next_required)
    summary = {
        "schema": HANDOFF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": status_reasons,
        "source_review_decision": source_decision,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_match": same_ref,
        "owner_handoff": owner_handoff,
        "handoff_package": handoff_package,
        "safe_rerun_hint": rerun_hint,
        "next_required_evidence": next_required,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This handoff is metadata-only and does not read field material directories.",
            "Keep not_proven, delivery_success=false, and primary_actions_enabled=false until real review evidence exists.",
        ],
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
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_match": same_ref,
        "source_acceptance_execution_callback_review_decision": {
            "load_issue": load_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "source_review_decision": source_decision,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "source_review_decision": source_decision,
        "owner_handoff": owner_handoff,
        "handoff_package": handoff_package,
        "safe_rerun_hint": rerun_hint,
        "next_required_evidence": next_required,
        "safe_copy": safe_copy,
        "route_task_field_retest_acceptance_execution_callback_review_handoff_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "raw_field_material_content",
            "ros_graph",
            "nav2_runtime",
            "fixed_route_runtime",
            "hardware_transport",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device",
            "robot_action",
            "field_rerun_execution",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_success_claim(artifact) or _has_success_claim(summary):
        # 最终防线只拦截动作/成功声明；禁词已在 source 入口 fail closed。
        artifact["status"] = "blocked_unsafe_review_handoff"
        artifact["handoff_status"] = "blocked_unsafe_review_handoff"
        summary["status"] = "blocked_unsafe_review_handoff"
        summary["handoff_status"] = "blocked_unsafe_review_handoff"
        artifact["route_task_field_retest_acceptance_execution_callback_review_handoff_summary"] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只打印 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，便于 PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate a route/task field retest acceptance execution callback review handoff artifact")
    parser.add_argument("--callback-review-decision-json", required=True, help="acceptance execution callback review decision artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review handoff")
    parser.add_argument("--output", default="", help="optional handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print handoff artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_acceptance_execution_callback_review_handoff(
        args.callback_review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_acceptance_execution_callback_review_handoff: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_execution_callback_review_handoff_summary_file: {_safe_ref(args.summary_output)}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
