#!/usr/bin/env python3
"""生成 field_evidence_rerun_handoff_intake 的 fail-closed PC gate。

该 gate 只读上一轮 field_evidence_rerun_callback_review_handoff 的
artifact/summary/wrapper JSON，以及现场 owner 回填的 handoff intake packet。
它把“交接包已被 owner 安全接收”复账为 metadata-only artifact/summary；
不读取真实材料目录、不访问 ROS graph、Nav2 runtime、serial/UART、
WAVE ROVER、外部云、真实手机/browser 或机器人动作接口。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INTAKE_SCHEMA = "trashbot.field_evidence_rerun_handoff_intake.v1"
INTAKE_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_handoff_intake_summary.v1"
PACKET_SCHEMA = "trashbot.field_evidence_rerun_handoff_intake_packet.v1"
PACKET_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_handoff_intake_packet_summary.v1"
SCHEMA_VERSION = 1
INTAKE_BOUNDARY = "software_proof_docker_field_evidence_rerun_handoff_intake_gate"

SOURCE_SCHEMAS = {
    "trashbot.field_evidence_rerun_callback_review_handoff.v1",
    "trashbot.field_evidence_rerun_callback_review_handoff_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_callback_review_handoff_gate"

PACKET_SCHEMAS = {"", PACKET_SCHEMA, PACKET_SUMMARY_SCHEMA}
PACKET_BOUNDARIES = {"", INTAKE_BOUNDARY, SOURCE_BOUNDARY}
SOURCE_READY_STATUS = "ready_for_field_evidence_rerun_callback_review_handoff"
READY_STATUS = "ready_for_field_evidence_rerun_handoff_intake_not_proven"

REQUIRED_PACKET_FIELDS = (
    "owner",
    "handoff_received",
    "intake_notes",
    "next_required_evidence",
)

NOT_PROVEN = (
    "real_route_elevator_field_pass",
    "real_field_evidence_rerun_execution",
    "real_route_completion_signal",
    "real_field_task_record",
    "real_nav2_fixed_route_runtime_log",
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
    "field_evidence_rerun_handoff_intake; "
    "software_proof_docker_field_evidence_rerun_handoff_intake_gate; "
    "owner_safe_handoff_intake_packet; callback_review_handoff; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 位于 callback review handoff 之后，只做 owner 接收复账。
# 设计约束 02：ready 只代表 safe handoff packet 被消费，不代表现场复跑完成。
# 设计约束 03：source handoff 必须是上一轮 supported schema 和 boundary。
# 设计约束 04：source handoff 必须已经 ready，否则本轮不能 ready。
# 设计约束 05：packet schema 可为空以兼容手工导出 JSON，但字段必须齐全。
# 设计约束 06：same evidence_ref 是主键，CLI、source、packet 必须一致。
# 设计约束 07：same_evidence_ref_required 必须是真布尔 true，字符串 true 不合格。
# 设计约束 08：packet 的 handoff_received 必须是真布尔 true。
# 设计约束 09：owner / intake_notes / next_required_evidence 缺失必须 fail closed。
# 设计约束 10：next_required_evidence 只允许扁平文本，不复制完整 artifact。
# 设计约束 11：source 和 packet 都必须保留 source=software_proof/not_proven。
# 设计约束 12：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 13：success/control claim 命中后直接 blocked_unsafe。
# 设计约束 14：raw path、credential、ROS topic、serial/UART/WAVE ROVER 细节全部阻断。
# 设计约束 15：wrapper/nested JSON 只递归固定 key，不采信任意 raw payload。
# 设计约束 16：summary 是 Robot/mobile 推荐消费面，但本 worker 不改下游文件。
# 设计约束 17：owner_intake 只表示人工交接状态，不授权机器人动作。
# 设计约束 18：rerun_guidance 只给 PC operator 命令，不访问 ROS graph。
# 设计约束 19：blocker_summary 只输出短枚举和计数，不回显 raw source。
# 设计约束 20：输出递归脱敏，blocked artifact 也不能泄漏敏感文本。
# 设计约束 21：exit code 保持 0，让 blocked intake 也能作为证据落盘。
# 设计约束 22：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 23：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 24：CLI 保持 output/summary-output/once-json 形态，方便自动化。
# 设计约束 25：non_access_scope 明确列出没有访问的系统面，便于评审。
# 设计约束 26：safe_copy 只放白名单字段，方便只读 UI/diagnostics 消费。
# 设计约束 27：source handoff 是唯一 ready 来源，不从 packet 自行推导通过。
# 设计约束 28：packet blocker_summary 只作为上下文，不提升 intake 状态。
# 设计约束 29：packet owner 只安全透传，不扩大本轮 owner 边界。
# 设计约束 30：packet next_required_evidence 可透传，但 unsafe 输入先阻断。
# 设计约束 31：缺 input、坏 JSON、非 object JSON 都生成 blocked intake。
# 设计约束 32：evidence_ref 若被误填成本机路径，只保留 basename。
# 设计约束 33：status_reasons 使用短枚举，便于 sprint final 复盘。
# 设计约束 34：intake_status 使用 snake_case，便于 rg 和下游解析。
# 设计约束 35：artifact 和 summary 同时输出 boundary/evidence_boundary。
# 设计约束 36：robot_diagnostics_summary 与 mobile_readonly_summary 同源。
# 设计约束 37：ready 仍输出 rerun_guidance，方便 reviewer 复现本地 gate。
# 设计约束 38：missing packet 不触发现场复跑，只要求 owner 回填安全 packet。
# 设计约束 39：source not ready 要回到上一轮 handoff，不绕过 review chain。
# 设计约束 40：unsafe 状态统一覆盖敏感信息和控制声明。
# 设计约束 41：final self-check 只看成功/动作声明，避免 non_access_scope 自误伤。
# 设计约束 42：FORBIDDEN_COPY 专门约束输入文本，不约束内部 non_access_scope。
# 设计约束 43：SUCCESS_CLAIM_PATTERNS 覆盖 key=value 和自然语言。
# 设计约束 44：RAW_PATH_PATTERNS 覆盖 macOS/Linux/Windows 常见绝对路径。
# 设计约束 45：SENSITIVE_PATTERNS 不保留原 token，统一转为 redacted。
# 设计约束 46：_source_candidates 优先 summary，artifact nested summary 可直接消费。
# 设计约束 47：_copy_probe 只扫描可交接字段，避免 artifact 内部枚举误伤。
# 设计约束 48：_list_text 对非 list 返回单个安全文本，兼容手工 packet。
# 设计约束 49：_dict 只接受 object 嵌套字段，字符串 wrapper 不可信。
# 设计约束 50：_flags_ok 确认三个动作旗标没有被上游或 packet 打开。
# 设计约束 51：_intake_status 的 fail-closed 优先级固定，便于测试锁定。
# 设计约束 52：_owner_intake 固定 Autonomy 主责，因为本 gate 属自主链路。
# 设计约束 53：supporting owners 仅为只读协作，不扩大本轮可改范围。
# 设计约束 54：_safe_copy 不能包含 raw artifact、完整材料正文或 secret。
# 设计约束 55：build 函数只返回 artifact/summary/exit_code，不做副作用。
# 设计约束 56：write_json 是唯一文件写出口，便于 CLI 和测试隔离。
# 设计约束 57：main 只解析参数和输出 JSON，不嵌入业务分支。
# 设计约束 58：如果未来接入真实现场材料，必须新增独立 gate 而非放宽本 gate。

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
    # UTC 时间方便不同 PC/Docker 主机产物按字符串排序。
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
    # 最终输出递归脱敏，防止新增嵌套字段绕过局部 helper。
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
    # 安全扫描用稳定 JSON，无法编码时退回脱敏文本。
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
    # 缺输入、坏 JSON、非 object 都输出 blocked intake，便于自动化留痕。
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


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只沿固定 key 递归，避免采信任意 raw payload。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_handoff_intake_summary",
        "field_evidence_rerun_callback_review_handoff_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "summary",
        "payload",
        "data",
        "artifact",
        "field_evidence_rerun_handoff_intake",
        "field_evidence_rerun_callback_review_handoff",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 handoff summary；找不到时才消费 artifact。
    candidates = _candidates(payload)
    for schema in (
        "trashbot.field_evidence_rerun_callback_review_handoff_summary.v1",
        "trashbot.field_evidence_rerun_callback_review_handoff.v1",
    ):
        for candidate in candidates:
            if str(candidate.get("schema", "")).strip() == schema:
                return candidate
    return payload


def _find_packet(payload: dict[str, Any]) -> dict[str, Any]:
    # packet 可以是顶层，也可以包在常见 wrapper key 里。
    candidates = _candidates(payload)
    for schema in (PACKET_SCHEMA, PACKET_SUMMARY_SCHEMA):
        for candidate in candidates:
            if str(candidate.get("schema", "")).strip() == schema:
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
    # 上游 handoff 必须来自上一轮固定 boundary。
    return _schema(source) in SOURCE_SCHEMAS and _boundary(source) == SOURCE_BOUNDARY


def _packet_supported(packet: dict[str, Any]) -> bool:
    # 手工 packet 可不带 schema/boundary，但不能带未知 schema 或未知 boundary。
    return _schema(packet) in PACKET_SCHEMAS and _boundary(packet) in PACKET_BOUNDARIES


def _ref(payload: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层或 safe_copy/diagnostics/mobile 取。
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


def _status(payload: dict[str, Any]) -> str:
    # handoff_status/intake_status/status 兼容不同摘要命名。
    safe_copy = _dict(payload, "safe_copy")
    return _safe_text(_first_text(payload.get("handoff_status"), payload.get("intake_status"), payload.get("status"), safe_copy.get("status"), default="")).strip()


def _same_ref_status(payload: dict[str, Any]) -> str:
    # same-evidence-ref 状态兼容字符串字段；非 matched 都保守要求复跑。
    safe_copy = _dict(payload, "safe_copy")
    value = _first_text(payload.get("same_evidence_ref_status"), safe_copy.get("same_evidence_ref_status"), default="")
    return _safe_text(value or "missing_evidence_ref").strip()


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


def _packet_fields_ok(packet: dict[str, Any]) -> tuple[bool, list[str]]:
    # packet 必须由 owner 显式接收，并携带下一步只读证据说明。
    missing = [field for field in REQUIRED_PACKET_FIELDS if field not in packet]
    if packet.get("handoff_received") is not True:
        missing.append("handoff_received_not_true")
    if not _safe_text(packet.get("owner", "")).strip():
        missing.append("owner_empty")
    if not _list_text(packet.get("intake_notes")):
        missing.append("intake_notes_empty")
    if not _list_text(packet.get("next_required_evidence")):
        missing.append("next_required_evidence_empty")
    return not missing, missing


def _copy_probe(source: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    # 只扫描可能下放的字段，避免 artifact non_access_scope 枚举触发误伤。
    return {
        "source_owner_handoff": source.get("owner_handoff"),
        "source_handoff_package": source.get("handoff_package"),
        "source_next_required_evidence": source.get("next_required_evidence"),
        "source_rerun_guidance": source.get("rerun_guidance"),
        "source_blocker_summary": source.get("blocker_summary"),
        "source_safe_copy": source.get("safe_copy"),
        "packet_owner": packet.get("owner"),
        "packet_intake_notes": packet.get("intake_notes"),
        "packet_next_required_evidence": packet.get("next_required_evidence"),
        "packet_blocker_summary": packet.get("blocker_summary"),
        "packet_safe_copy": packet.get("safe_copy"),
    }


def _intake_status(
    source_issue: str,
    packet_issue: str,
    source: dict[str, Any],
    packet: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    packet_ref: str,
    source_status: str,
    same_ref_status: str,
    packet_missing_fields: list[str],
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 ready intake。
    reasons: list[str] = []
    if source_issue:
        reasons.append(source_issue)
    if packet_issue:
        reasons.append(packet_issue)
    if success_claim:
        return "blocked_unsafe_field_evidence_rerun_handoff_intake_copy", reasons + ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked_unsafe_field_evidence_rerun_handoff_intake_copy", reasons + ["unsafe_copy_detected"]
    if source_issue or not _source_supported(source):
        return "blocked_unsupported_field_evidence_rerun_handoff_intake_source", reasons + ["unsupported_callback_review_handoff_schema_or_boundary"]
    if packet_issue or not _packet_supported(packet):
        return "blocked_missing_field_evidence_rerun_handoff_intake_packet", reasons + ["unsupported_or_missing_handoff_intake_packet"]
    if not _is_software_not_proven(source) or not _is_software_not_proven(packet):
        return "blocked_unsupported_field_evidence_rerun_handoff_intake_source", reasons + ["source_or_packet_not_software_proof_or_missing_not_proven"]
    if not _flags_ok(source) or not _flags_ok(packet):
        return "blocked_unsafe_field_evidence_rerun_handoff_intake_copy", reasons + ["source_or_packet_action_flags_not_false"]
    if source.get("same_evidence_ref_required") is not True or packet.get("same_evidence_ref_required") is not True:
        return "evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked", reasons + ["same_evidence_ref_required_not_true"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked", reasons + [f"requested_ref:{requested_ref}!={source_ref}"]
    if source_ref and packet_ref and source_ref != packet_ref:
        return "evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked", reasons + [f"packet_ref:{packet_ref}!={source_ref}"]
    if requested_ref and packet_ref and requested_ref != packet_ref:
        return "evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked", reasons + [f"requested_ref:{requested_ref}!={packet_ref}"]
    if not (source_ref or packet_ref or requested_ref):
        return "evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked", reasons + ["safe_evidence_ref_missing"]
    if same_ref_status not in {"matched", "ready"}:
        return "evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked", reasons + [f"same_evidence_ref:{same_ref_status}"]
    if source_status != SOURCE_READY_STATUS:
        return "blocked_field_evidence_rerun_review_handoff_not_ready", reasons + [f"source_handoff_status:{source_status or 'missing'}"]
    if packet_missing_fields:
        return "blocked_missing_field_evidence_rerun_handoff_intake_packet", reasons + packet_missing_fields
    return READY_STATUS, reasons


def _owner_intake(intake_status: str, evidence_ref: str, packet: dict[str, Any]) -> dict[str, Any]:
    # owner_intake 只表达人工交接接收状态，不授权 Robot/mobile 任何动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if intake_status == READY_STATUS:
        action = "handoff_intake_recorded_for_product_closeout"
    elif intake_status == "evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked":
        action = "rerun_handoff_intake_with_same_evidence_ref"
    elif intake_status == "blocked_unsafe_field_evidence_rerun_handoff_intake_copy":
        action = "remove_unsafe_copy_or_control_claim_before_rerun"
    elif intake_status == "blocked_field_evidence_rerun_review_handoff_not_ready":
        action = "regenerate_ready_callback_review_handoff_before_intake"
    else:
        action = "provide_supported_owner_safe_handoff_intake_packet"
    return {
        "owner": _safe_text(packet.get("owner", "Autonomy Algorithm Engineer")).strip() or "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "action": action,
        "intake_status": intake_status,
        "safe_evidence_ref": ref,
        "intake_notes": _list_text(packet.get("intake_notes")),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_guidance(intake_status: str, evidence_ref: str) -> dict[str, Any]:
    # rerun guidance 只给 PC operator 复跑，不访问 ROS graph 或硬件。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "required": intake_status != READY_STATUS,
        "status": intake_status,
        "safe_evidence_ref": ref,
        "commands": [
            "python3 pc-tools/evidence/field_evidence_rerun_callback_review_handoff.py "
            f"--callback-review-decision-json <callback_review_decision.json> --evidence-ref {ref} --once-json",
            "python3 pc-tools/evidence/field_evidence_rerun_handoff_intake.py "
            f"--callback-review-handoff-json <callback_review_handoff.json> --handoff-intake-packet-json <handoff_intake_packet.json> --evidence-ref {ref} --once-json",
        ],
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(intake_status: str, evidence_ref: str, packet_next: list[str]) -> list[str]:
    # 下一步只列证据动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if intake_status == READY_STATUS:
        return packet_next or [f"Record owner-safe handoff intake for evidence_ref={ref} in Product closeout."]
    if intake_status == "blocked_missing_field_evidence_rerun_handoff_intake_packet":
        return [f"Provide owner-safe handoff intake packet for evidence_ref={ref} with owner, handoff_received=true, intake_notes, and next_required_evidence."]
    if intake_status == "evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked":
        return [f"Regenerate callback review handoff and handoff intake packet with one evidence_ref={ref}."]
    if intake_status == "blocked_unsafe_field_evidence_rerun_handoff_intake_copy":
        return ["Regenerate handoff intake packet without raw paths, credentials, ROS topics, serial/UART detail, WAVE ROVER fields, checksums, control claims, or success claims."]
    return [f"Regenerate supported callback review handoff and owner-safe intake packet for evidence_ref={ref}."]


def _blocker_summary(intake_status: str, reasons: list[str], source_status: str) -> dict[str, Any]:
    # blocker summary 给 Product/Robot/mobile 看状态，不回显 raw input。
    return {
        "blocked": intake_status != READY_STATUS,
        "intake_status": intake_status,
        "source_handoff_status": source_status,
        "status_reasons": reasons,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(intake_status: str, evidence_ref: str, next_required: list[str]) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料正文。
    return {
        "schema": f"{INTAKE_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "intake_status": intake_status,
        "status": intake_status,
        "evidence_boundary": INTAKE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "next_required_evidence": next_required,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_handoff_intake(
    callback_review_handoff_json: str,
    handoff_intake_packet_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 callback review handoff 和 owner packet，生成 metadata-only intake artifact。"""
    source_payload, source_issue = _load_json(callback_review_handoff_json, "callback_review_handoff")
    packet_payload, packet_issue = _load_json(handoff_intake_packet_json, "handoff_intake_packet")
    source = _find_source(source_payload) if source_payload else {}
    packet = _find_packet(packet_payload) if packet_payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _ref(source) if source else ""
    packet_ref = _ref(packet) if packet else ""
    evidence_ref_out = requested_ref or source_ref or packet_ref
    source_status = _status(source) if source else ""
    same_ref_status = _same_ref_status(source) if source else "missing_evidence_ref"
    packet_ok, packet_missing = _packet_fields_ok(packet) if packet else (False, ["handoff_intake_packet_missing"])
    copy_probe = _copy_probe(source, packet) if source or packet else {}
    unsafe = bool(source_payload or packet_payload) and _has_forbidden_copy(copy_probe)
    success_claim = bool(source_payload or packet_payload) and (_has_success_claim(copy_probe) or _has_success_claim(source) or _has_success_claim(packet))
    intake_status, status_reasons = _intake_status(
        source_issue,
        packet_issue,
        source,
        packet,
        requested_ref,
        source_ref,
        packet_ref,
        source_status,
        same_ref_status,
        packet_missing if not packet_ok else [],
        unsafe,
        success_claim,
    )
    owner_intake = _owner_intake(intake_status, evidence_ref_out, packet)
    next_required = _next_required_evidence(intake_status, evidence_ref_out, _list_text(packet.get("next_required_evidence")) if packet else [])
    rerun_guidance = _rerun_guidance(intake_status, evidence_ref_out)
    blocker_summary = _blocker_summary(intake_status, status_reasons, source_status)
    safe_copy = _safe_copy(intake_status, evidence_ref_out, next_required)
    summary = {
        "schema": INTAKE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": intake_status,
        "intake_status": intake_status,
        "status_reasons": status_reasons,
        "source_handoff_status": source_status,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "owner_intake": owner_intake,
        "next_required_evidence": next_required,
        "rerun_guidance": rerun_guidance,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This handoff intake is metadata-only and does not read field material directories.",
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
        "status": intake_status,
        "intake_status": intake_status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_callback_review_handoff": {
            "load_issue": source_issue,
            "schema": _schema(source) if source else "",
            "evidence_boundary": _boundary(source) if source else "",
            "handoff_status": source_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "source_handoff_intake_packet": {
            "load_issue": packet_issue,
            "schema": _schema(packet) if packet else "",
            "evidence_boundary": _boundary(packet) if packet else "",
            "safe_evidence_ref": packet_ref,
            "required_fields_present": packet_ok,
        },
        "owner_intake": owner_intake,
        "next_required_evidence": next_required,
        "rerun_guidance": rerun_guidance,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "field_evidence_rerun_handoff_intake_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "raw_artifact",
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
        artifact["status"] = "blocked_unsafe_field_evidence_rerun_handoff_intake_copy"
        artifact["intake_status"] = "blocked_unsafe_field_evidence_rerun_handoff_intake_copy"
        summary["status"] = "blocked_unsafe_field_evidence_rerun_handoff_intake_copy"
        summary["intake_status"] = "blocked_unsafe_field_evidence_rerun_handoff_intake_copy"
        artifact["field_evidence_rerun_handoff_intake_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun handoff intake artifact")
    parser.add_argument("--callback-review-handoff-json", required=True, help="callback review handoff artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--handoff-intake-packet-json", required=True, help="owner-safe handoff intake packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this handoff intake")
    parser.add_argument("--output", default="", help="optional handoff intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print handoff intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_handoff_intake(
        args.callback_review_handoff_json,
        args.handoff_intake_packet_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_handoff_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"handoff_intake_summary_file: {_safe_ref(args.summary_output)}")
        print(f"intake_status: {artifact['intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
