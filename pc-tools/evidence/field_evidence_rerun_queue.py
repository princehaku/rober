#!/usr/bin/env python3
"""生成 field_evidence_rerun_queue 的 fail-closed PC gate。

该 gate 只读上一轮 field_evidence_rerun_handoff_intake artifact/summary
或 wrapper/nested summary，以及可选 owner-safe queue request JSON。输出
只表示受控现场复跑队列候选的 metadata-only software proof；不读取真实
材料目录、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、
外部云、真实手机/browser 或机器人动作接口。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


QUEUE_SCHEMA = "trashbot.field_evidence_rerun_queue.v1"
QUEUE_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_queue_summary.v1"
SCHEMA_VERSION = 1
QUEUE_BOUNDARY = "software_proof_docker_field_evidence_rerun_queue_gate"

SOURCE_SCHEMAS = {
    "trashbot.field_evidence_rerun_handoff_intake.v1",
    "trashbot.field_evidence_rerun_handoff_intake_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_handoff_intake_gate"
READY_SOURCE_STATUS = "ready_for_field_evidence_rerun_handoff_intake_not_proven"

ACK_TRUE_VALUES = {"ack", "acked", "acknowledged", "accepted", "ready", "received", "confirmed", "approved"}
ACK_FALSE_VALUES = {"", "missing", "none", "pending", "needs_owner_ack", "rejected", "blocked"}

NOT_PROVEN = (
    "real_controlled_field_rerun_execution",
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_field_task_record",
    "real_elevator_door_summary",
    "real_target_floor_or_floor_arrival_summary",
    "real_human_assistance_summary",
    "real_dropoff_completion",
    "real_cancel_completion",
    "real_delivery_result",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_browser_evidence",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
    "pr_5_resolved",
)

BOUNDARY_NOTE = (
    "field_evidence_rerun_queue; "
    "software_proof_docker_field_evidence_rerun_queue_gate; "
    "queued_for_controlled_field_rerun_not_proven; "
    "needs_owner_safe_queue_request_before_rerun_queue; "
    "needs_field_evidence_rerun_queue_backfill; evidence_ref_mismatch_field_evidence_rerun_queue; "
    "blocked_unsafe_field_evidence_rerun_queue; blocked_unsupported_field_evidence_rerun_handoff_intake; "
    "not_proven; safe_to_control=false; delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 位于 handoff intake 之后，不能跳过 owner-safe intake。
# 设计约束 02：queued 只表示 metadata queue candidate，不代表现场复跑执行。
# 设计约束 03：缺 queue request 只能 blocked/not_proven，不能从 source 自行 ready。
# 设计约束 04：source schema 和 boundary 必须双重匹配，避免误消费其它 gate。
# 设计约束 05：source intake 必须 ready，否则进入 backfill 而非 queue。
# 设计约束 06：source、CLI、request 必须共享同一个 safe evidence_ref。
# 设计约束 07：same_evidence_ref_required 必须是真布尔 true。
# 设计约束 08：same_evidence_ref_status 只接受 matched/ready。
# 设计约束 09：request ack 必须显式 acknowledged，字符串随意文案不算。
# 设计约束 10：request 只能携带 owner-safe metadata 和下一步证据说明。
# 设计约束 11：source 和 request 都不能包含成功、控制或动作授权声明。
# 设计约束 12：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 13：raw path、credential、ROS topic、serial/UART/WAVE ROVER 全部阻断。
# 设计约束 14：checksum、Traceback、complete/raw artifact 全部阻断。
# 设计约束 15：wrapper/nested JSON 只递归固定 key，不采信任意 raw payload。
# 设计约束 16：summary 是 Robot/mobile 推荐消费面，但本 worker 不改下游。
# 设计约束 17：owner_handoff 只表达下一步归属，不授权机器人执行。
# 设计约束 18：safe_rerun_hint 只给 PC operator 复跑本 gate，不访问硬件。
# 设计约束 19：blocker_summary 只输出枚举和短原因，不回显 raw input。
# 设计约束 20：safe_copy 只放白名单字段，方便只读 UI/diagnostics 消费。
# 设计约束 21：输出递归脱敏，blocked artifact 也不能泄漏敏感文本。
# 设计约束 22：exit code 保持 0，让 blocked queue 也能作为证据落盘。
# 设计约束 23：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 24：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 25：non_access_scope 明确列出没有访问的系统面，便于评审。
# 设计约束 26：request schema 可为空以兼容手工 JSON，但未知 schema 会阻断。
# 设计约束 27：request boundary 可为空或本 gate boundary，未知 boundary 会阻断。
# 设计约束 28：blocked queue 仍输出 next_required_evidence 便于下一轮补证。
# 设计约束 29：FORBIDDEN_COPY 只约束输入文本，不约束内部 non_access_scope。
# 设计约束 30：最终自检只拦截动作/成功声明，避免安全枚举自误伤。

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
    "db_url",
    "database_url",
    "queue_url",
    "ROS topic",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "serial",
    "UART",
    "baudrate",
    "baud_rate",
    "WAVE ROVER",
    "low-level control",
    "low_level_control",
    "motor command",
    "Traceback",
    "checksum",
    "complete artifact",
    "raw artifact",
    "raw robot response",
)

SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bphone/browser\s+(success|succeeded|passed|validated)\b"),
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action)\b"),
    re.compile(r"(?i)\bcontrol\s+(enabled|allowed|granted|authorized)\b"),
)

RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"(?i)\bROS\s+topic\b"), "[REDACTED_ROS_TOPIC]"),
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
    (re.compile(r"(?i)raw artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 时间让不同 PC/Docker 主机产物按字符串排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本先脱敏，再进入 artifact 或 summary。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 被误填成本机路径时只保留 basename，避免路径扩散。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线，防止新增嵌套字段绕过局部 helper。
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
        if value.get("safe_to_control") is True or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # queue request 是可选 CLI 参数，但缺失时仍必须 fail closed。
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
    # 只接受 object 嵌套字段，字符串 wrapper 不可信。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 字段位置不同，取首个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _candidates(payload: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只沿固定 key 递归，避免采信任意 raw payload。
    candidates = [payload]
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_candidates(value, keys))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 handoff intake summary；找不到时保留顶层用于 unsupported 解释。
    keys = (
        "field_evidence_rerun_handoff_intake",
        "field_evidence_rerun_handoff_intake_summary",
        "field_evidence_rerun_queue",
        "field_evidence_rerun_queue_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    )
    for candidate in _candidates(payload, keys):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _find_queue_request(payload: dict[str, Any]) -> dict[str, Any]:
    # request 支持常见 wrapper，但只提取 owner-safe 字段。
    keys = (
        "queue_request",
        "rerun_queue_request",
        "owner_queue_request",
        "owner_acknowledgement",
        "owner_acknowledgment",
        "field_evidence_rerun_queue_request",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    )
    for candidate in _candidates(payload, keys):
        if _owner_ack_state(candidate) != "missing" or _request_ref(candidate):
            return candidate
    return payload


def _list_text(value: Any, limit: int = 24) -> list[str]:
    # 下游摘要只接受扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        return [_safe_text(item).strip() for item in value[:limit] if isinstance(item, (str, int, float, bool)) and _safe_text(item).strip()]
    if value in (None, ""):
        return []
    if isinstance(value, (str, int, float, bool)):
        return [_safe_text(value).strip()]
    return []


def _schema(payload: dict[str, Any]) -> str:
    # schema 字段只用于契约判断和输出解释。
    return _safe_text(payload.get("schema", "")).strip()


def _boundary(payload: dict[str, Any]) -> str:
    # boundary 兼容 evidence_boundary / boundary 两种既有字段。
    return _safe_text(_first_text(payload.get("evidence_boundary"), payload.get("boundary"), default="")).strip()


def _source_supported(source: dict[str, Any]) -> bool:
    # 上游 handoff intake 必须来自上一轮固定 boundary。
    return _schema(source) in SOURCE_SCHEMAS and _boundary(source) == SOURCE_BOUNDARY


def _request_supported(request: dict[str, Any]) -> bool:
    # 手工 request 可不带 schema/boundary，但不能带未知 schema 或未知 boundary。
    schema = _schema(request)
    boundary = _boundary(request)
    return schema in {"", "trashbot.field_evidence_rerun_queue_request.v1", "trashbot.field_evidence_rerun_queue_request_summary.v1"} and boundary in {"", QUEUE_BOUNDARY, SOURCE_BOUNDARY}


def _source_status(source: dict[str, Any]) -> str:
    # intake_status 是上游主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(_first_text(source.get("intake_status"), source.get("status"), safe_copy.get("intake_status"), default="")).strip()


def _ref(payload: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层、diagnostics、mobile 或 safe_copy 取。
    safe_copy = _dict(payload, "safe_copy")
    robot = _dict(payload, "robot_diagnostics_summary")
    mobile = _dict(payload, "mobile_readonly_summary")
    return _safe_ref(
        _first_text(
            payload.get("safe_evidence_ref"),
            payload.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            default="",
        )
    )


def _same_ref_status(source: dict[str, Any]) -> str:
    # 非 matched/ready 都按证据链不稳定处理。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(_first_text(source.get("same_evidence_ref_status"), safe_copy.get("same_evidence_ref_status"), default="missing_evidence_ref")).strip()


def _is_software_not_proven(payload: dict[str, Any]) -> bool:
    # 输入必须明确 software_proof/not_proven，不能把真实通过口径塞进本 gate。
    encoded = _encoded(payload)
    return payload.get("source") == "software_proof" and "not_proven" in encoded


def _flags_ok(payload: dict[str, Any]) -> bool:
    # 三个动作旗标必须显式保持关闭；缺字段按不合格处理。
    return (
        payload.get("safe_to_control") is False
        and payload.get("delivery_success") is False
        and payload.get("primary_actions_enabled") is False
    )


def _owner_ack_state(payload: dict[str, Any]) -> str:
    # 多字段兼容 owner-safe request，但只有显式 ack 才进入 queue。
    if not payload:
        return "missing"
    for key in (
        "owner_acknowledgement_state",
        "owner_acknowledgment_state",
        "queue_acknowledgement_state",
        "queue_acknowledgment_state",
        "acknowledgement_state",
        "acknowledgment_state",
        "ack_state",
        "state",
        "status",
    ):
        # 缺字段不能提前返回 missing，否则后面的 owner_ack=true 永远读不到。
        if key not in payload:
            continue
        value = _safe_text(payload.get(key)).strip().lower()
        if value in ACK_TRUE_VALUES:
            return "acknowledged"
        if value in ACK_FALSE_VALUES:
            return "missing" if value in {"", "missing", "none"} else value
    for key in ("owner_ack", "queue_owner_ack", "ack", "acknowledged", "accepted", "received", "confirmed"):
        value = payload.get(key)
        if value is True:
            return "acknowledged"
        if isinstance(value, str) and value.strip().lower() in ACK_TRUE_VALUES:
            return "acknowledged"
    return "missing"


def _request_ref(request: dict[str, Any]) -> str:
    # queue request 也必须绑定同一个 safe evidence_ref。
    safe_copy = _dict(request, "safe_copy")
    return _safe_ref(
        _first_text(
            request.get("safe_evidence_ref"),
            request.get("evidence_ref"),
            request.get("queue_evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _request_reason(request: dict[str, Any]) -> str:
    # reason 只保留短文本，不能承载 raw artifact 或成功声明。
    return _safe_text(_first_text(request.get("requested_rerun_reason"), request.get("rerun_reason"), request.get("reason"), default=""))[:240]


def _request_next_required(request: dict[str, Any]) -> list[str]:
    # request 可补充 next-required evidence，但仍只输出扁平白名单文本。
    safe_copy = _dict(request, "safe_copy")
    return _list_text(request.get("next_required_evidence")) or _list_text(safe_copy.get("next_required_evidence"))


def _source_next_required(source: dict[str, Any]) -> list[str]:
    # 上游 intake 的 next_required_evidence 可用于 backfill 解释。
    safe_copy = _dict(source, "safe_copy")
    return _list_text(source.get("next_required_evidence")) or _list_text(safe_copy.get("next_required_evidence"))


def _copy_probe(source: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    # 只扫描可能下放的字段，避免 artifact 内部枚举误伤。
    return {
        "source_owner_handoff": source.get("owner_handoff"),
        "source_next_required_evidence": source.get("next_required_evidence"),
        "source_rerun_guidance": source.get("rerun_guidance"),
        "source_blocker_summary": source.get("blocker_summary"),
        "source_safe_copy": source.get("safe_copy"),
        "request_owner": request.get("owner"),
        "request_reason": _request_reason(request),
        "request_next_required_evidence": request.get("next_required_evidence"),
        "request_safe_copy": request.get("safe_copy"),
    }


def _queue_request_summary(request: dict[str, Any], ack_state: str, evidence_ref: str) -> dict[str, Any]:
    # request summary 不复制完整 request，只保留 owner-safe 元数据。
    return {
        "owner": _safe_text(_first_text(request.get("owner"), request.get("request_owner"), default="field_owner")),
        "owner_acknowledgement_state": ack_state,
        "safe_evidence_ref": evidence_ref,
        "requested_rerun_reason": _request_reason(request),
        "next_required_evidence": _request_next_required(request),
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _queue_status(
    source_issue: str,
    request_issue: str,
    source: dict[str, Any],
    request: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    request_ref: str,
    source_status: str,
    same_ref_status: str,
    request_ack: str,
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 queued。
    reasons: list[str] = []
    if source_issue:
        reasons.append(source_issue)
    if request_issue:
        reasons.append(request_issue)
    if success_claim:
        return "blocked_unsafe_field_evidence_rerun_queue", reasons + ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked_unsafe_field_evidence_rerun_queue", reasons + ["unsafe_copy_detected"]
    if source_issue or not _source_supported(source):
        return "blocked_unsupported_field_evidence_rerun_handoff_intake", reasons + ["unsupported_handoff_intake_schema_or_boundary"]
    if request_issue or not request or not _request_supported(request):
        return "needs_owner_safe_queue_request_before_rerun_queue", reasons + ["owner_safe_queue_request_missing_or_unsupported"]
    if not _is_software_not_proven(source) or not _is_software_not_proven(request):
        return "blocked_unsupported_field_evidence_rerun_handoff_intake", reasons + ["source_or_request_not_software_proof_or_missing_not_proven"]
    if not _flags_ok(source) or not _flags_ok(request):
        return "blocked_unsafe_field_evidence_rerun_queue", reasons + ["source_or_request_action_flags_not_false"]
    if source.get("same_evidence_ref_required") is not True or request.get("same_evidence_ref_required") is not True:
        return "evidence_ref_mismatch_field_evidence_rerun_queue", reasons + ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return "evidence_ref_mismatch_field_evidence_rerun_queue", reasons + ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_field_evidence_rerun_queue", reasons + [f"requested_ref:{requested_ref}!={source_ref}"]
    if request_ref and request_ref != source_ref:
        return "evidence_ref_mismatch_field_evidence_rerun_queue", reasons + [f"queue_request_ref:{request_ref}!={source_ref}"]
    if not request_ref:
        return "evidence_ref_mismatch_field_evidence_rerun_queue", reasons + ["queue_request_safe_evidence_ref_missing"]
    if same_ref_status not in {"matched", "ready"}:
        return "evidence_ref_mismatch_field_evidence_rerun_queue", reasons + [f"same_evidence_ref:{same_ref_status}"]
    if source_status != READY_SOURCE_STATUS:
        return "needs_field_evidence_rerun_queue_backfill", reasons + [f"source_handoff_intake_status:{source_status or 'missing'}"]
    if request_ack != "acknowledged":
        return "needs_owner_safe_queue_request_before_rerun_queue", reasons + ["owner_queue_acknowledgement_missing_before_queue"]
    return "queued_for_controlled_field_rerun_not_proven", reasons


def _next_required_evidence(status: str, evidence_ref: str, upstream_next: list[str], request_next: list[str]) -> list[str]:
    # 下一步只列证据动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "queued_for_controlled_field_rerun_not_proven":
        return request_next or [f"Hold metadata-only controlled field rerun queue candidate pending real materials for evidence_ref={ref}."]
    if status == "needs_owner_safe_queue_request_before_rerun_queue":
        return [f"Provide owner-safe queue request JSON for evidence_ref={ref} with acknowledged owner queue state before queueing."]
    if status == "needs_field_evidence_rerun_queue_backfill":
        return upstream_next or [f"Backfill ready field_evidence_rerun_handoff_intake for evidence_ref={ref} before queueing."]
    if status == "evidence_ref_mismatch_field_evidence_rerun_queue":
        return [f"Regenerate handoff intake and queue request with one evidence_ref={ref}."]
    if status == "blocked_unsupported_field_evidence_rerun_handoff_intake":
        return [f"Provide supported field_evidence_rerun_handoff_intake artifact or summary for evidence_ref={ref}."]
    return ["Regenerate queue input without raw paths, credentials, ROS topics, serial/UART detail, WAVE ROVER fields, checksums, complete/raw artifacts, tracebacks, control claims, or success claims."]


def _safe_rerun_hint(status: str, evidence_ref: str) -> dict[str, Any]:
    # rerun hint 只给 PC operator 复跑，不访问 ROS graph、Nav2 或硬件。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "required": status != "queued_for_controlled_field_rerun_not_proven",
        "status": status,
        "safe_evidence_ref": ref,
        "commands": [
            "python3 pc-tools/evidence/field_evidence_rerun_handoff_intake.py "
            f"--callback-review-handoff-json <callback_review_handoff.json> --handoff-intake-packet-json <handoff_intake_packet.json> --evidence-ref {ref} --once-json",
            "python3 pc-tools/evidence/field_evidence_rerun_queue.py "
            f"--handoff-intake-json <handoff_intake.json> --queue-request-json <queue_request.json> --evidence-ref {ref} --once-json",
        ],
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _owner_handoff(status: str, evidence_ref: str, source_status: str, ack_state: str, request: dict[str, Any]) -> dict[str, Any]:
    # owner_handoff 只表达下一步处理人和动作，不授权 Robot/mobile 控制。
    return {
        "owner": "Autonomy Algorithm Engineer",
        "request_owner": _safe_text(_first_text(request.get("owner"), request.get("request_owner"), default="field_owner")),
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "action": "hold_queue_until_real_controlled_field_materials_arrive" if status == "queued_for_controlled_field_rerun_not_proven" else "repair_field_evidence_rerun_queue_inputs_before_queueing",
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "source_handoff_intake_status": source_status,
        "owner_acknowledgement_state": ack_state,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(status: str, evidence_ref: str, source_status: str, ack_state: str, next_required: list[str]) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料正文。
    return {
        "schema": f"{QUEUE_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": status,
        "queue_status": status,
        "source_handoff_intake_status": source_status,
        "owner_acknowledgement_state": ack_state,
        "evidence_boundary": QUEUE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "next_required_evidence": next_required,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_queue(
    handoff_intake_json: str,
    queue_request_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 handoff intake 和 owner-safe request，生成 metadata-only queue artifact。"""
    source_payload, source_issue = _load_json(handoff_intake_json, "handoff_intake_json")
    request_payload, request_issue = _load_json(queue_request_json, "queue_request")
    source = _find_source(source_payload) if source_payload else {}
    request = _find_queue_request(request_payload) if request_payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _ref(source) if source else ""
    request_ref = _request_ref(request) if request else ""
    evidence_ref_out = requested_ref or source_ref or request_ref
    source_status = _source_status(source) if source else ""
    same_ref_status = _same_ref_status(source) if source else "missing_evidence_ref"
    request_ack = _owner_ack_state(request) if request else "missing"
    upstream_next = _source_next_required(source) if source else []
    request_next = _request_next_required(request) if request else []
    copy_probe = _copy_probe(source, request) if source or request else {}
    unsafe = bool(source_payload or request_payload) and _has_forbidden_copy(copy_probe)
    success_claim = bool(source_payload or request_payload) and (_has_success_claim(copy_probe) or _has_success_claim(source) or _has_success_claim(request))
    status, reasons = _queue_status(
        source_issue,
        request_issue,
        source,
        request,
        requested_ref,
        source_ref,
        request_ref,
        source_status,
        same_ref_status,
        request_ack,
        unsafe,
        success_claim,
    )
    next_required = _next_required_evidence(status, evidence_ref_out, upstream_next, request_next)
    safe_rerun_hint = _safe_rerun_hint(status, evidence_ref_out)
    request_summary = _queue_request_summary(request, request_ack, evidence_ref_out)
    owner_handoff = _owner_handoff(status, evidence_ref_out, source_status, request_ack, request)
    safe_copy = _safe_copy(status, evidence_ref_out, source_status, request_ack, next_required)
    blocker_summary = {
        "blocked": status != "queued_for_controlled_field_rerun_not_proven",
        "queue_status": status,
        "source_handoff_intake_status": source_status,
        "same_evidence_ref_status": same_ref_status,
        "status_reasons": reasons,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = {
        "schema": QUEUE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": QUEUE_BOUNDARY,
        "boundary": QUEUE_BOUNDARY,
        "status": status,
        "queue_status": status,
        "status_reasons": reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "source_handoff_intake_schema": _safe_text(source.get("schema", "")) if source else "",
        "source_handoff_intake_status": source_status,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "owner_safe_queue_request": request_summary,
        "owner_handoff": owner_handoff,
        "blocker_summary": blocker_summary,
        "next_required_evidence": next_required,
        "safe_rerun_hint": safe_rerun_hint,
        "rerun_guidance": safe_rerun_hint,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This rerun queue is metadata-only and does not execute a field rerun.",
            "Queue status is not real route/elevator field validation, HIL, delivery_result, or delivery_success.",
            "Keep not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false until real evidence exists.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": QUEUE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": QUEUE_BOUNDARY,
        "boundary": QUEUE_BOUNDARY,
        "status": status,
        "queue_status": status,
        "status_reasons": reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_handoff_intake": {
            "load_issue": source_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "source_handoff_intake_status": source_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(bool(source_payload) and _has_forbidden_copy(source)),
            "success_claim": bool(bool(source_payload) and _has_success_claim(source)),
        },
        "owner_safe_queue_request": {
            "load_issue": request_issue,
            "owner_acknowledgement_state": request_ack,
            "safe_evidence_ref": request_ref,
            "requested_rerun_reason": _request_reason(request) if request else "",
            "unsafe_copy": bool(bool(request_payload) and _has_forbidden_copy(request)),
            "success_claim": bool(bool(request_payload) and _has_success_claim(request)),
        },
        "owner_safe_queue_request_summary": request_summary,
        "owner_handoff": owner_handoff,
        "blocker_summary": blocker_summary,
        "next_required_evidence": next_required,
        "safe_rerun_hint": safe_rerun_hint,
        "rerun_guidance": safe_rerun_hint,
        "safe_copy": safe_copy,
        "field_evidence_rerun_queue_summary": summary,
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
            "mobile_runtime",
            "robot_action",
            "field_rerun_execution",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_success_claim(artifact) or _has_success_claim(summary):
        # 最终防线只拦截动作/成功声明；敏感信息已在入口 fail closed。
        artifact["status"] = "blocked_unsafe_field_evidence_rerun_queue"
        artifact["queue_status"] = "blocked_unsafe_field_evidence_rerun_queue"
        summary["status"] = "blocked_unsafe_field_evidence_rerun_queue"
        summary["queue_status"] = "blocked_unsafe_field_evidence_rerun_queue"
        artifact["field_evidence_rerun_queue_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun queue artifact")
    parser.add_argument("--handoff-intake-json", required=True, help="handoff intake artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--queue-request-json", default="", help="optional owner-safe queue request JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this rerun queue")
    parser.add_argument("--output", default="", help="optional rerun queue artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional rerun queue summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print rerun queue artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_queue(
        args.handoff_intake_json,
        args.queue_request_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_queue: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_rerun_queue_summary_file: {_safe_ref(args.summary_output)}")
        print(f"queue_status: {artifact['queue_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
