#!/usr/bin/env python3
"""生成 field_evidence_rerun_execution_result_intake 的 fail-closed PC gate。

该 gate 只读上一轮 field_evidence_rerun_execution_callback_review_handoff
artifact、summary、Robot safe alias 或 wrapper/nested JSON，并可选读取 field
owner 提交的 execution result packet。输出只表达 result packet 是否进入
review intake：missing / accepted / rejected / blocked。accepted 不是现场通过、
不是 delivery success，也不授权任何机器人或手机主动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INTAKE_SCHEMA = "trashbot.field_evidence_rerun_execution_result_intake.v1"
INTAKE_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_intake_summary.v1"
SCHEMA_VERSION = 1
INTAKE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_intake_gate"

SOURCE_SCHEMAS = {
    "trashbot.field_evidence_rerun_execution_callback_review_handoff.v1",
    "trashbot.field_evidence_rerun_execution_callback_review_handoff_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate"
READY_HANDOFF_STATUS = "ready_for_field_evidence_rerun_execution_callback_review_handoff"

RESULT_PACKET_SCHEMAS = {
    "trashbot.field_evidence_rerun_execution_result_packet.v1",
    "trashbot.field_evidence_rerun_execution_result_packet_summary.v1",
}
RESULT_STATUSES = ("missing", "accepted", "rejected", "blocked")

REQUIRED_PACKET_FIELDS = (
    "packet_status",
    "safe_evidence_ref",
    "material_summary",
    "result_reasons",
    "owner_handoff",
)

NOT_PROVEN = (
    "real_field_evidence_rerun_execution",
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
    "pr_6_runtime_proof",
)

BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_intake; "
    "software_proof_docker_field_evidence_rerun_execution_result_intake_gate; "
    "missing; accepted; rejected; blocked; accepted_for_review_intake_only; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 位于 execution callback review handoff 之后。
# 设计约束 02：accepted 只表示 result packet 可进入 review intake。
# 设计约束 03：missing 表示没有 owner-safe result packet 或 packet 声明 missing。
# 设计约束 04：rejected 表示 packet 被人工/规则拒绝，不能转成 blocked。
# 设计约束 05：blocked 表示 source、证据链或安全边界不满足。
# 设计约束 06：source handoff 必须 ready，否则结果包不能被采信。
# 设计约束 07：source schema 和 boundary 必须双重匹配。
# 设计约束 08：result packet schema 可缺省，但若声明必须属于白名单。
# 设计约束 09：result packet state 只能是 missing/accepted/rejected/blocked。
# 设计约束 10：source、packet、CLI 三处 evidence_ref 必须一致。
# 设计约束 11：same_evidence_ref_required 必须是真布尔 true。
# 设计约束 12：same_evidence_ref_status 只接受 matched 或 ready。
# 设计约束 13：source 与 packet 都必须保留 software_proof/not_proven。
# 设计约束 14：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 15：输入出现成功、通过、控制授权或主动作文案必须 blocked。
# 设计约束 16：raw path、credential、DB/queue URL、ROS topic、串口和硬件细节必须阻断。
# 设计约束 17：result packet 只允许 sanitized material summary，不复制 raw artifact。
# 设计约束 18：wrapper/nested JSON 只沿白名单 key 递归，避免采信 raw payload。
# 设计约束 19：Robot/mobile 推荐消费 summary 或 safe_copy，不消费 raw packet。
# 设计约束 20：owner_handoff 只表达人工责任，不授权现场动作。
# 设计约束 21：next_required_evidence 只列补证动作，不写现场通过。
# 设计约束 22：reconciliation_hint 只说明下一轮 review 入口，不做自动合并。
# 设计约束 23：blocked 也返回 exit code 0，方便把阻断证据落盘。
# 设计约束 24：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 25：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 26：non_access_scope 明确列出未访问系统面，便于验收边界检查。
# 设计约束 27：safe_copy 保持白名单，不包含完整 artifact、材料正文或 secret。
# 设计约束 28：PR #5 resolved 或 PR #6 runtime proof 文案必须 blocked。
# 设计约束 29：O5 external proof 文案必须 blocked，避免混淆 Objective 边界。
# 设计约束 30：最终自检只拦截动作/成功声明，避免 non_access_scope 自误伤。
# 设计约束 31：FORBIDDEN_COPY 只约束输入可下放字段，不约束内部非访问枚举。
# 设计约束 32：状态名保持短枚举，方便 Product closeout 和移动端渲染。
# 设计约束 33：缺 handoff input 是 blocked，缺 result packet 是 missing。
# 设计约束 34：bad JSON 的 result packet 是 blocked，因为无法判断是否安全。
# 设计约束 35：unsupported source 是 blocked，不能用 result packet 绕过上游。
# 设计约束 36：unsupported packet schema 是 blocked，避免假 packet 进入 intake。
# 设计约束 37：packet_status 缺失按 missing 处理，保持 owner 可补证。
# 设计约束 38：packet accepted 仍输出 accepted_for_review_intake_only。
# 设计约束 39：material_summary 只允许 dict/list/str 的安全摘要。
# 设计约束 40：source handoff blocker 只作为上下文，不提升 result 状态。
# 设计约束 41：result_reasons 使用短文本数组，便于 rg 和 sprint final 引用。
# 设计约束 42：source owner_handoff 与 packet owner_handoff 都先脱敏再输出。
# 设计约束 43：CLI output/summary-output/once-json 与既有 PC gate 保持一致。
# 设计约束 44：如果未来接入真实现场材料，必须新增独立 review gate。

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
    re.compile(r"(?i)\btrue\s+field\s+pass\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bphone/browser\s+(success|succeeded|passed|validated)\b"),
    re.compile(r"(?i)\bcontrol\s+(enabled|allowed|granted|authorized)\b"),
    re.compile(r"(?i)\bO5\s+external\s+proof\b"),
    re.compile(r"(?i)\bPR\s*#?5\s+(resolved|closed|complete|completed)\b"),
    re.compile(r"(?i)\bPR\s*#?6\s+runtime\s+proof\b"),
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
    # UTC 时间让不同 PC/Docker 主机产物可按字符串排序审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，blocked 分支也不回显敏感原文。
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


def _load_json(path: str, missing_issue: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转成明确 issue，由状态机决定 missing/blocked。
    if not path:
        return {}, missing_issue
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, f"{missing_issue}_missing_file"
    except json.JSONDecodeError:
        return {}, f"{missing_issue}_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, f"{missing_issue}_read_error"
    if not isinstance(payload, dict):
        return {}, f"{missing_issue}_not_object"
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


def _list_text(value: Any, limit: int = 24) -> list[str]:
    # 下游摘要只接受扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        return [_safe_text(item).strip() for item in value[:limit] if isinstance(item, (str, int, float, bool)) and _safe_text(item).strip()]
    if value in (None, ""):
        return []
    if isinstance(value, (str, int, float, bool)):
        return [_safe_text(value).strip()]
    return []


def _candidates(payload: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只沿固定 key 递归，避免采信任意 raw payload。
    candidates = [payload]
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_candidates(value, keys))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 handoff summary；找不到时才消费 artifact。
    keys = (
        "field_evidence_rerun_execution_callback_review_handoff",
        "field_evidence_rerun_execution_callback_review_handoff_summary",
        "robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary",
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


def _find_packet(payload: dict[str, Any]) -> dict[str, Any]:
    # result packet 允许 wrapper/nested summary，但不扫描任意 raw material body。
    keys = (
        "field_evidence_rerun_execution_result_packet",
        "field_evidence_rerun_execution_result_packet_summary",
        "result_packet",
        "result_packet_summary",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    )
    for candidate in _candidates(payload, keys):
        if str(candidate.get("schema", "")).strip() in RESULT_PACKET_SCHEMAS:
            return candidate
    return payload


def _schema(payload: dict[str, Any]) -> str:
    # schema 字段只用于契约判断和输出解释。
    return _safe_text(payload.get("schema", "")).strip()


def _boundary(payload: dict[str, Any]) -> str:
    # boundary 兼容 evidence_boundary / boundary 两种既有字段。
    return _safe_text(_first_text(payload.get("evidence_boundary"), payload.get("boundary"), default="")).strip()


def _source_supported(source: dict[str, Any]) -> bool:
    # 上游 handoff 必须来自上一轮固定 boundary。
    return _schema(source) in SOURCE_SCHEMAS and _boundary(source) == SOURCE_BOUNDARY


def _packet_supported(packet: dict[str, Any]) -> bool:
    # packet 可不声明 schema；一旦声明 schema，就必须属于 owner-safe result packet。
    schema = _schema(packet)
    if not schema:
        return True
    return schema in RESULT_PACKET_SCHEMAS


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


def _same_ref_status(payload: dict[str, Any]) -> str:
    # same-ref 状态兼容 safe_copy；非 matched/ready 都按证据链不稳定处理。
    safe_copy = _dict(payload, "safe_copy")
    return _safe_text(_first_text(payload.get("same_evidence_ref_status"), safe_copy.get("same_evidence_ref_status"), default="missing_evidence_ref")).strip()


def _source_status(source: dict[str, Any]) -> str:
    # handoff_status 是上游主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(_first_text(source.get("handoff_status"), source.get("status"), safe_copy.get("handoff_status"), safe_copy.get("status"), default="")).strip()


def _packet_status(packet: dict[str, Any]) -> str:
    # packet_status 是 owner-safe result packet 的唯一状态输入。
    safe_copy = _dict(packet, "safe_copy")
    return _safe_text(_first_text(packet.get("result_packet_status"), packet.get("packet_status"), packet.get("status"), safe_copy.get("packet_status"), safe_copy.get("status"), default="missing")).strip()


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


def _source_copy_probe(source: dict[str, Any]) -> dict[str, Any]:
    # 只扫描可能下放的字段，避免 artifact non_access_scope 枚举触发误伤。
    return {
        "owner_handoff": source.get("owner_handoff"),
        "handoff_package": source.get("handoff_package"),
        "next_required_evidence": source.get("next_required_evidence"),
        "rerun_guidance": source.get("rerun_guidance"),
        "blocker_summary": source.get("blocker_summary"),
        "safe_copy": source.get("safe_copy"),
    }


def _packet_copy_probe(packet: dict[str, Any]) -> dict[str, Any]:
    # packet 只允许 sanitized summary 字段进入扫描和输出。
    return {
        "packet_status": _packet_status(packet),
        "material_summary": packet.get("material_summary"),
        "result_material_summary": packet.get("result_material_summary"),
        "result_reasons": packet.get("result_reasons"),
        "missing_reasons": packet.get("missing_reasons"),
        "rejected_reasons": packet.get("rejected_reasons"),
        "blocked_reasons": packet.get("blocked_reasons"),
        "owner_handoff": packet.get("owner_handoff"),
        "safe_copy": packet.get("safe_copy"),
    }


def _material_summary(packet: dict[str, Any]) -> Any:
    # material summary 可以是 object/list/text，但会在输出前递归脱敏。
    value = packet.get("material_summary", packet.get("result_material_summary", {}))
    if isinstance(value, (dict, list, str, int, float, bool)):
        return _safe_value(value)
    return {}


def _result_reasons(packet: dict[str, Any], status: str) -> list[str]:
    # reason 字段按状态选择，缺省也输出可追踪的短原因。
    if status == "missing":
        reasons = _list_text(packet.get("missing_reasons") or packet.get("result_reasons"))
        return reasons or ["owner_safe_execution_result_packet_missing_or_marked_missing"]
    if status == "rejected":
        reasons = _list_text(packet.get("rejected_reasons") or packet.get("result_reasons"))
        return reasons or ["owner_safe_execution_result_packet_rejected"]
    if status == "blocked":
        reasons = _list_text(packet.get("blocked_reasons") or packet.get("result_reasons"))
        return reasons or ["owner_safe_execution_result_packet_blocked"]
    reasons = _list_text(packet.get("result_reasons"))
    return reasons or ["owner_safe_execution_result_packet_accepted_for_review_intake_only"]


def _intake_status(
    source_issue: str,
    packet_issue: str,
    source: dict[str, Any],
    packet: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    packet_ref: str,
    source_status: str,
    packet_status: str,
    same_ref_status: str,
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 accepted。
    reasons: list[str] = []
    if source_issue:
        reasons.append(source_issue)
    if packet_issue and packet_issue != "execution_result_packet_not_provided":
        reasons.append(packet_issue)
    if success_claim:
        return "blocked", reasons + ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked", reasons + ["unsafe_copy_detected"]
    if source_issue or not _source_supported(source):
        return "blocked", reasons + ["unsupported_execution_callback_review_handoff_schema_or_boundary"]
    if not _is_software_not_proven(source):
        return "blocked", reasons + ["source_not_software_proof_or_missing_not_proven"]
    if not _flags_ok(source):
        return "blocked", reasons + ["source_action_flags_not_false"]
    if source.get("same_evidence_ref_required") is not True:
        return "blocked", reasons + ["source_same_evidence_ref_required_not_true"]
    if not source_ref:
        return "blocked", reasons + ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref != source_ref:
        return "blocked", reasons + [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref_status not in {"matched", "ready"}:
        return "blocked", reasons + [f"source_same_evidence_ref:{same_ref_status}"]
    if source_status != READY_HANDOFF_STATUS:
        return "blocked", reasons + [f"source_handoff_status:{source_status or 'missing'}"]
    if packet_issue == "execution_result_packet_not_provided":
        return "missing", reasons + ["execution_result_packet_not_provided"]
    if packet_issue:
        return "blocked", reasons + [packet_issue]
    if not _packet_supported(packet):
        return "blocked", reasons + ["unsupported_execution_result_packet_schema"]
    if not _is_software_not_proven(packet):
        return "blocked", reasons + ["packet_not_software_proof_or_missing_not_proven"]
    if not _flags_ok(packet):
        return "blocked", reasons + ["packet_action_flags_not_false"]
    if packet.get("same_evidence_ref_required", True) is not True:
        return "blocked", reasons + ["packet_same_evidence_ref_required_not_true"]
    if packet_ref and packet_ref != source_ref:
        return "blocked", reasons + [f"packet_ref:{packet_ref}!={source_ref}"]
    if packet_status not in RESULT_STATUSES:
        return "blocked", reasons + [f"unsupported_result_packet_status:{packet_status or 'missing'}"]
    return packet_status, reasons


def _owner_handoff(status: str, evidence_ref: str, source_owner: dict[str, Any], packet_owner: dict[str, Any]) -> dict[str, Any]:
    # owner_handoff 只分派人工 review/intake 责任，不授权 Robot/mobile 动作。
    ref = evidence_ref or "<same_evidence_ref>"
    actions = {
        "accepted": "route_execution_result_packet_to_review_intake",
        "missing": "request_owner_safe_execution_result_packet",
        "rejected": "return_execution_result_packet_for_owner_correction",
        "blocked": "repair_result_intake_source_or_remove_unsafe_copy",
    }
    return {
        "owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "action": actions.get(status, "repair_result_intake_source_or_remove_unsafe_copy"),
        "result_intake_status": status,
        "accepted_meaning": "accepted_for_review_intake_only_not_field_pass" if status == "accepted" else "",
        "safe_evidence_ref": ref,
        "source_owner_handoff": _safe_value(source_owner),
        "packet_owner_handoff": _safe_value(packet_owner),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(status: str, evidence_ref: str, reasons: list[str]) -> list[str]:
    # 下一步只列补证或 review intake 动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "accepted":
        return [
            f"Route the accepted-for-review-intake result packet for evidence_ref={ref} into the next review decision gate.",
            "Keep not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false until real review evidence exists.",
        ]
    if status == "missing":
        return [f"Submit an owner-safe execution result packet with packet_status accepted/rejected/blocked for evidence_ref={ref}."]
    if status == "rejected":
        return [f"Correct rejected result packet fields and resubmit with the same safe evidence_ref={ref}."]
    return [
        f"Regenerate supported execution callback review handoff and sanitized result packet for evidence_ref={ref}.",
        "Remove raw paths, credentials, ROS topics, serial/UART detail, WAVE ROVER fields, checksums, raw artifacts, tracebacks, control claims, or success claims.",
        *reasons[:4],
    ]


def _reconciliation_hint(status: str, evidence_ref: str) -> dict[str, Any]:
    # reconciliation hint 只描述人工 review 入口，不做自动状态合并。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "status": status,
        "safe_evidence_ref": ref,
        "next_gate": "field_evidence_rerun_execution_result_review_decision" if status == "accepted" else "field_evidence_rerun_execution_result_intake",
        "accepted_is_field_pass": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(status: str, evidence_ref: str, source_status: str, packet_status: str, next_required: list[str]) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料正文。
    return {
        "schema": f"{INTAKE_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": status,
        "result_intake_status": status,
        "accepted_meaning": "accepted_for_review_intake_only_not_field_pass" if status == "accepted" else "",
        "source_handoff_status": source_status,
        "result_packet_status": packet_status,
        "evidence_boundary": INTAKE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "next_required_evidence": next_required,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_result_intake(
    execution_callback_handoff_json: str,
    result_packet_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 handoff 与可选 result packet，生成 metadata-only result intake。"""
    source_payload, source_issue = _load_json(execution_callback_handoff_json, "execution_callback_review_handoff_not_provided")
    packet_payload, packet_issue = _load_json(result_packet_json, "execution_result_packet_not_provided")
    source = _find_source(source_payload) if source_payload else {}
    packet = _find_packet(packet_payload) if packet_payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _ref(source) if source else ""
    packet_ref = _ref(packet) if packet else ""
    evidence_ref_out = requested_ref or source_ref or packet_ref
    source_status = _source_status(source) if source else ""
    packet_status = _packet_status(packet) if packet else "missing"
    same_ref_status = _same_ref_status(source) if source else "missing_evidence_ref"
    source_owner = _dict(source, "owner_handoff") if source else {}
    packet_owner = _dict(packet, "owner_handoff") if packet else {}
    source_probe = _source_copy_probe(source) if source else {}
    packet_probe = _packet_copy_probe(packet) if packet else {}
    unsafe = bool(source_payload) and _has_forbidden_copy(source_probe)
    unsafe = unsafe or (bool(packet_payload) and _has_forbidden_copy(packet_probe))
    success_claim = bool(source_payload) and (_has_success_claim(source_probe) or _has_success_claim(source))
    success_claim = success_claim or (bool(packet_payload) and (_has_success_claim(packet_probe) or _has_success_claim(packet)))
    status, status_reasons = _intake_status(
        source_issue,
        packet_issue,
        source,
        packet,
        requested_ref,
        source_ref,
        packet_ref,
        source_status,
        packet_status,
        same_ref_status,
        unsafe,
        success_claim,
    )
    packet_reasons = _result_reasons(packet, status) if packet else ["execution_result_packet_not_provided"]
    material_summary = _material_summary(packet) if packet else {}
    owner_handoff = _owner_handoff(status, evidence_ref_out, source_owner, packet_owner)
    all_reasons = status_reasons + [reason for reason in packet_reasons if reason not in status_reasons]
    next_required = _next_required_evidence(status, evidence_ref_out, all_reasons)
    reconciliation_hint = _reconciliation_hint(status, evidence_ref_out)
    safe_copy = _safe_copy(status, evidence_ref_out, source_status, packet_status, next_required)
    blocker_summary = {
        "blocked": status == "blocked",
        "result_intake_status": status,
        "source_handoff_status": source_status,
        "result_packet_status": packet_status,
        "status_reasons": all_reasons,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = {
        "schema": INTAKE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": status,
        "result_intake_status": status,
        "accepted_meaning": "accepted_for_review_intake_only_not_field_pass" if status == "accepted" else "",
        "status_reasons": all_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "source_handoff_schema": _schema(source) if source else "",
        "source_handoff_status": source_status,
        "result_packet_schema": _schema(packet) if packet else "",
        "result_packet_status": packet_status,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "material_summary": material_summary,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "reconciliation_hint": reconciliation_hint,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "accepted only means accepted_for_review_intake_only_not_field_pass.",
            "This result intake does not prove real route/elevator field execution, Nav2 runtime, HIL, phone/browser proof, delivery_result, or delivery_success.",
            "Keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": INTAKE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": status,
        "result_intake_status": status,
        "accepted_meaning": "accepted_for_review_intake_only_not_field_pass" if status == "accepted" else "",
        "status_reasons": all_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_execution_callback_review_handoff": {
            "load_issue": source_issue,
            "schema": _schema(source) if source else "",
            "evidence_boundary": _boundary(source) if source else "",
            "source_handoff_status": source_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(bool(source_payload) and _has_forbidden_copy(source_probe)),
            "success_claim": bool(bool(source_payload) and (_has_success_claim(source_probe) or _has_success_claim(source))),
        },
        "owner_safe_execution_result_packet": {
            "load_issue": packet_issue,
            "schema": _schema(packet) if packet else "",
            "result_packet_status": packet_status,
            "safe_evidence_ref": packet_ref,
            "required_fields": list(REQUIRED_PACKET_FIELDS),
            "unsafe_copy": bool(bool(packet_payload) and _has_forbidden_copy(packet_probe)),
            "success_claim": bool(bool(packet_payload) and (_has_success_claim(packet_probe) or _has_success_claim(packet))),
        },
        "material_summary": material_summary,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "reconciliation_hint": reconciliation_hint,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_result_intake_summary": summary,
        "robot_diagnostics_field_evidence_rerun_execution_result_intake_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "raw_field_material_content",
            "complete_artifact",
            "local_path",
            "checksum",
            "credentials",
            "db_queue_url",
            "ros_topic",
            "ros_graph",
            "nav2_runtime",
            "fixed_route_runtime",
            "serial_uart",
            "wave_rover",
            "external_cloud",
            "oss_cdn",
            "4g_network",
            "phone_device_browser_runtime",
            "robot_action",
            "field_rerun_execution",
            "field_pass_claim",
            "pr5_resolution",
            "pr6_runtime_proof",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_success_claim(artifact) or _has_success_claim(summary):
        # 最终防线只拦截动作/成功声明；non_access_scope 不能因此自我降级。
        artifact["status"] = "blocked"
        artifact["result_intake_status"] = "blocked"
        summary["status"] = "blocked"
        summary["result_intake_status"] = "blocked"
        artifact["field_evidence_rerun_execution_result_intake_summary"] = summary
        artifact["robot_diagnostics_field_evidence_rerun_execution_result_intake_summary"] = summary
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
    # CLI 保持 dependency-free，便于 PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun execution result intake artifact")
    parser.add_argument("--execution-callback-handoff-json", required=True, help="execution callback review handoff artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--result-packet-json", default="", help="optional owner-safe execution result packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this result intake")
    parser.add_argument("--output", default="", help="optional result intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional result intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print result intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_intake(
        args.execution_callback_handoff_json,
        args.result_packet_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_rerun_execution_result_intake_summary_file: {_safe_ref(args.summary_output)}")
        print(f"result_intake_status: {artifact['result_intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
