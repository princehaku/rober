#!/usr/bin/env python3
"""生成 field_evidence_rerun_execution_callback_review_handoff 的 fail-closed PC gate。

该 gate 只读上一轮 field_evidence_rerun_execution_callback_review_decision artifact、
summary 或 wrapper/nested JSON，把 review decision、owner handoff、
next required evidence、rerun guidance 和 blocker summary 打包为下一步只读
handoff artifact/summary。它不读取真实材料目录、不访问 ROS graph、Nav2、
serial/UART、WAVE ROVER、外部云、4G、OSS/CDN、DB/queue、真实手机/browser
或机器人动作接口。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HANDOFF_SCHEMA = "trashbot.field_evidence_rerun_execution_callback_review_handoff.v1"
HANDOFF_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_callback_review_handoff_summary.v1"
SCHEMA_VERSION = 1
HANDOFF_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate"

SOURCE_SCHEMAS = {
    "trashbot.field_evidence_rerun_execution_callback_review_decision.v1",
    "trashbot.field_evidence_rerun_execution_callback_review_decision_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate"

REVIEW_DECISIONS = ("ready", "missing", "rejected", "blocked")
READY_STATUS = "ready_for_field_evidence_rerun_execution_callback_review_handoff"

DECISION_TO_HANDOFF = {
    "ready": READY_STATUS,
    "missing": "needs_owner_follow_up",
    "rejected": "needs_owner_follow_up",
    "blocked": "needs_field_evidence_rerun_execution_callback_rerun",
}

REVIEW_HANDOFF_REQUIREMENTS = (
    "supported_review_decision_schema",
    "same_evidence_ref_match",
    "source_software_proof_not_proven",
    "review_decision_present",
    "owner_handoff_sanitized",
    "next_required_evidence_sanitized",
    "rerun_guidance_sanitized",
    "blocker_summary_sanitized",
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
    "field_evidence_rerun_execution_callback_review_handoff; "
    "software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate; "
    "review_decision; owner_handoff; next_required_evidence; rerun_guidance; "
    "blocker_summary; source=software_proof; not_proven; "
    "safe_to_control=false; delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只消费 review decision，不重新读取现场材料。
# 设计约束 02：handoff_status 只表达交接状态，不证明真实现场复跑完成。
# 设计约束 03：ready 只映射为 handoff ready，不映射为 field pass。
# 设计约束 04：missing/rejected 保留 owner follow-up，不静默进入 ready。
# 设计约束 05：blocked review decision 必须要求复跑或修正上游 decision。
# 设计约束 06：unsupported schema/boundary 必须 fail closed 到复跑状态。
# 设计约束 07：safe_evidence_ref 是链路主键，缺失或不一致都不能 ready。
# 设计约束 08：same_evidence_ref_required 必须是真布尔 true。
# 设计约束 09：same_evidence_ref_status 只接受 matched 或 ready。
# 设计约束 10：source 必须保留 software_proof 和 not_proven。
# 设计约束 11：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 12：success/control claim 命中后直接 blocked_unsafe_review_handoff。
# 设计约束 13：raw path、credential、ROS topic、serial/UART 等 copy 命中后阻断。
# 设计约束 14：artifact 输入可能有 non_access_scope，安全扫描只看白名单字段。
# 设计约束 15：wrapper/nested JSON 只递归固定 key，避免误采信任意 raw payload。
# 设计约束 16：summary 是 Robot/mobile 推荐消费面，但本 worker 不改下游文件。
# 设计约束 17：owner_handoff 是人工责任摘要，不授权机器人动作。
# 设计约束 18：handoff_package 只是只读包，不执行 result review 或 field rerun。
# 设计约束 19：rerun_guidance 只给 PC operator 命令，不访问 ROS graph。
# 设计约束 20：blocker_summary 只输出短枚举和计数，不回显 raw source。
# 设计约束 21：输出递归脱敏，blocked artifact 也不能泄漏敏感文本。
# 设计约束 22：exit code 保持 0，让 blocked handoff 也能作为证据落盘。
# 设计约束 23：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 24：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 25：CLI 保持 output/summary-output/once-json 形态，方便自动化。
# 设计约束 26：non_access_scope 明确列出没有访问的系统面，便于评审。
# 设计约束 27：safe_copy 只放白名单字段，方便只读 UI/diagnostics 消费。
# 设计约束 28：source review decision 是唯一状态来源，不从材料列表推导通过。
# 设计约束 29：source blocker_summary 只作为上下文，不提升 handoff 状态。
# 设计约束 30：source owner_handoff 只安全透传，不扩大文件 owner 边界。
# 设计约束 31：source next_required_evidence 可透传，但 unsafe 输入先阻断。
# 设计约束 32：source rerun_guidance 只复制命令摘要，不执行命令。
# 设计约束 33：缺 input、坏 JSON、非 object JSON 都生成 blocked handoff。
# 设计约束 34：弱类型字符串 true 不能冒充 same_evidence_ref_required。
# 设计约束 35：evidence_ref 若被误填成本机路径，只保留 basename。
# 设计约束 36：status_reasons 使用短枚举，便于 sprint final 复盘。
# 设计约束 37：handoff_status 使用 snake_case，便于 rg 和下游解析。
# 设计约束 38：artifact 和 summary 同时输出 boundary/evidence_boundary。
# 设计约束 39：robot_diagnostics_summary 与 mobile_readonly_summary 同源。
# 设计约束 40：ready 仍输出 rerun_guidance，方便 reviewer 复现本地 gate。
# 设计约束 41：needs_owner_follow_up 不触发现场复跑，只说明人工补证。
# 设计约束 42：needs_field_evidence_rerun_execution_callback_rerun 保留上游修复路径。
# 设计约束 43：evidence_ref_mismatch_rerun 优先保护同一证据链。
# 设计约束 44：blocked_unsafe_review_handoff 统一覆盖敏感信息和控制声明。
# 设计约束 45：final self-check 只看成功/动作声明，避免 non_access_scope 自误伤。
# 设计约束 46：FORBIDDEN_COPY 专门约束输入文本，不约束内部 non_access_scope。
# 设计约束 47：SUCCESS_CLAIM_PATTERNS 覆盖 key=value 和自然语言。
# 设计约束 48：RAW_PATH_PATTERNS 覆盖 macOS/Linux/Windows 常见绝对路径。
# 设计约束 49：SENSITIVE_PATTERNS 不保留原 token，统一转为 redacted。
# 设计约束 50：_source_candidates 优先 summary，artifact nested summary 可直接消费。
# 设计约束 51：_source_copy_probe 只扫描可交接字段，避免 artifact 内部枚举误伤。
# 设计约束 52：_list_text 对非 list 返回单个安全文本，兼容旧 summary。
# 设计约束 53：_dict 只接受 object 嵌套字段，字符串 wrapper 不可信。
# 设计约束 54：_source_flags_ok 确认三个动作旗标没有被上游打开。
# 设计约束 55：_handoff_status 的 fail-closed 优先级固定，便于测试锁定。
# 设计约束 56：_handoff_package 的 ready 只由 handoff_status 推导。
# 设计约束 57：_owner_handoff 固定 Autonomy 主责，因为本 gate 属自主链路。
# 设计约束 58：supporting owners 仅为只读协作，不扩大本轮可改范围。
# 设计约束 59：_rerun_guidance 使用相对命令，不包含本机绝对路径。
# 设计约束 60：_safe_copy 不能包含 raw artifact、完整材料正文或 secret。
# 设计约束 61：build 函数只返回 artifact/summary/exit_code，不做副作用。
# 设计约束 62：write_json 是唯一文件写出口，便于 CLI 和测试隔离。
# 设计约束 63：main 只解析参数和输出 JSON，不嵌入业务分支。
# 设计约束 64：如果未来接入真实现场材料，必须新增独立 gate 而非放宽本 gate。

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
    re.compile(r"(?i)\btrue\s+field\s+pass\b"),
    re.compile(r"(?i)\bO5\s+external\s+proof\b"),
    re.compile(r"(?i)\bPR\s*#?5\s+(resolved|closed|complete|completed)\b"),
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


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都输出 blocked handoff，便于自动化留痕。
    if not path:
        return {}, "execution_callback_review_decision_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "execution_callback_review_decision_missing"
    except json.JSONDecodeError:
        return {}, "execution_callback_review_decision_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "execution_callback_review_decision_read_error"
    if not isinstance(payload, dict):
        return {}, "execution_callback_review_decision_not_object"
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


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 先找 summary，再找 artifact，避免 artifact 内部 non_access_scope 误伤。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_callback_review_handoff_summary",
        "field_evidence_rerun_execution_callback_review_decision_summary",
        "robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "summary",
        "payload",
        "data",
        "artifact",
        "field_evidence_rerun_execution_callback_review_handoff",
        "field_evidence_rerun_execution_callback_review_decision",
        "robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 review decision summary；找不到时才消费 artifact。
    candidates = _source_candidates(payload)
    for schema in (
        "trashbot.field_evidence_rerun_execution_callback_review_decision_summary.v1",
        "trashbot.field_evidence_rerun_execution_callback_review_decision.v1",
    ):
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


def _schema(source: dict[str, Any]) -> str:
    # schema 字段只用于契约判断和输出解释。
    return _safe_text(source.get("schema", "")).strip()


def _boundary(source: dict[str, Any]) -> str:
    # boundary 兼容 evidence_boundary / boundary 两种既有字段。
    return _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止旧 JSON 或其它 gate 混用。
    return _schema(source) in SOURCE_SCHEMAS and _boundary(source) == SOURCE_BOUNDARY


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层或 safe_copy/diagnostics/mobile 取。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return _safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            default="",
        )
    )


def _source_decision(source: dict[str, Any]) -> str:
    # review_decision 是上游主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(_first_text(source.get("review_decision"), source.get("status"), safe_copy.get("review_decision"), default="")).strip()


def _same_ref_status(source: dict[str, Any]) -> str:
    # same-evidence-ref 状态兼容字符串字段；非 matched 都保守要求复跑。
    safe_copy = _dict(source, "safe_copy")
    value = _first_text(source.get("same_evidence_ref_status"), safe_copy.get("same_evidence_ref_status"), default="")
    return _safe_text(value or "missing_evidence_ref").strip()


def _source_is_software_not_proven(source: dict[str, Any]) -> bool:
    # 上游必须明确 software_proof/not_proven，不能把真实通过口径塞进本 gate。
    encoded = _encoded(source)
    return source.get("source") == "software_proof" and "not_proven" in encoded


def _source_flags_ok(source: dict[str, Any]) -> bool:
    # 三个动作旗标必须显式保持关闭；缺字段按不合格处理。
    return (
        source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _source_owner_handoff(source: dict[str, Any]) -> dict[str, Any]:
    # 上游 owner_handoff 只保留脱敏摘要，供人工交接参考。
    value = source.get("owner_handoff")
    return _safe_value(value) if isinstance(value, dict) else {}


def _source_blocker_summary(source: dict[str, Any]) -> dict[str, Any]:
    # 上游 blocker_summary 只作为上下文，不提升 handoff 状态。
    value = source.get("blocker_summary")
    return _safe_value(value) if isinstance(value, dict) else {}


def _source_copy_probe(source: dict[str, Any]) -> dict[str, Any]:
    # 只扫描可能下放的字段，避免 artifact non_access_scope 枚举触发误伤。
    return {
        "owner_handoff": source.get("owner_handoff"),
        "next_required_evidence": source.get("next_required_evidence"),
        "rerun_guidance": source.get("rerun_guidance"),
        "blocker_summary": source.get("blocker_summary"),
        "safe_copy": source.get("safe_copy"),
        "status_reasons": source.get("status_reasons"),
        "accepted_materials": source.get("accepted_materials"),
        "missing_materials": source.get("missing_materials"),
        "rejected_materials": source.get("rejected_materials"),
        "blocked_materials": source.get("blocked_materials"),
    }


def _handoff_status(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_decision: str,
    same_ref_status: str,
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
        return "needs_field_evidence_rerun_execution_callback_rerun", reasons + ["unsupported_execution_callback_review_decision_schema_or_boundary"]
    if not _source_is_software_not_proven(source):
        return "needs_field_evidence_rerun_execution_callback_rerun", reasons + ["source_not_software_proof_or_missing_not_proven"]
    if not _source_flags_ok(source):
        return "blocked_unsafe_review_handoff", reasons + ["source_action_flags_not_false"]
    if source.get("same_evidence_ref_required") is not True:
        return "evidence_ref_mismatch_rerun", reasons + ["same_evidence_ref_required_not_true"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun", reasons + [f"requested_ref:{requested_ref}!={source_ref}"]
    if not source_ref:
        return "evidence_ref_mismatch_rerun", reasons + ["safe_evidence_ref_missing"]
    if same_ref_status not in {"matched", "ready"}:
        return "evidence_ref_mismatch_rerun", reasons + [f"same_evidence_ref:{same_ref_status}"]
    if not source_decision:
        return "needs_field_evidence_rerun_execution_callback_rerun", reasons + ["source_review_decision_missing"]
    if source_decision not in DECISION_TO_HANDOFF:
        return "needs_field_evidence_rerun_execution_callback_rerun", reasons + [f"unsupported_source_review_decision:{source_decision}"]
    return DECISION_TO_HANDOFF[source_decision], reasons


def _handoff_package(handoff_status: str, evidence_ref: str, source_decision: str, source_owner: dict[str, Any]) -> dict[str, Any]:
    # handoff package 是只读交接包，不触发真实复跑或 result review。
    ready = handoff_status == READY_STATUS
    return {
        "ready": ready,
        "status": handoff_status,
        "source_review_decision": source_decision,
        "safe_evidence_ref": evidence_ref,
        "requirements": list(REVIEW_HANDOFF_REQUIREMENTS),
        "review_entry": "field_evidence_review_handoff_ready" if ready else "field_evidence_review_handoff_blocked_until_follow_up",
        "source_owner_handoff": source_owner,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _owner_handoff(handoff_status: str, evidence_ref: str, source_decision: str, source_owner: dict[str, Any]) -> dict[str, Any]:
    # owner handoff 只分派人工材料责任，不授权 Robot/mobile 任何动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == READY_STATUS:
        action = "handoff_sanitized_review_decision_for_product_closeout"
    elif handoff_status == "needs_owner_follow_up":
        action = "backfill_or_correct_field_evidence_review_materials"
    elif handoff_status == "evidence_ref_mismatch_rerun":
        action = "rerun_execution_callback_review_decision_with_same_evidence_ref"
    elif handoff_status == "blocked_unsafe_review_handoff":
        action = "remove_unsafe_copy_or_control_claim_before_rerun"
    else:
        action = "regenerate_supported_execution_callback_review_decision"
    return {
        "owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "action": action,
        "handoff_status": handoff_status,
        "source_review_decision": source_decision,
        "safe_evidence_ref": ref,
        "source_owner_handoff": source_owner,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_guidance(handoff_status: str, evidence_ref: str, source_rerun: dict[str, Any]) -> dict[str, Any]:
    # rerun guidance 只给 PC operator 复跑，不访问 ROS graph 或硬件。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "required": handoff_status != READY_STATUS,
        "status": handoff_status,
        "safe_evidence_ref": ref,
        "source_rerun_guidance": _safe_value(source_rerun) if isinstance(source_rerun, dict) else {},
        "commands": [
            "python3 pc-tools/evidence/field_evidence_rerun_execution_callback_review_decision.py "
            f"--callback-intake-json <callback_intake.json> --evidence-ref {ref} --once-json",
            "python3 pc-tools/evidence/field_evidence_rerun_execution_callback_review_handoff.py "
            f"--execution-callback-decision-json <execution_callback_review_decision.json> --evidence-ref {ref} --once-json",
        ],
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(handoff_status: str, evidence_ref: str, source_next: list[str]) -> list[str]:
    # 下一步只列证据动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == READY_STATUS:
        return source_next or [f"Hand off sanitized execution callback review decision for evidence_ref={ref} to Product closeout."]
    if handoff_status == "needs_owner_follow_up":
        return source_next or [f"Backfill or correct execution callback review materials for evidence_ref={ref} before closeout."]
    if handoff_status == "evidence_ref_mismatch_rerun":
        return [f"Regenerate execution callback review decision and handoff with one evidence_ref={ref}."]
    if handoff_status == "blocked_unsafe_review_handoff":
        return ["Regenerate execution callback review decision without raw paths, credentials, ROS topics, serial/UART detail, checksums, control claims, or success claims."]
    return [f"Regenerate supported field evidence rerun execution callback review decision for evidence_ref={ref}."]


def _blocker_summary(
    handoff_status: str,
    status_reasons: list[str],
    source_decision: str,
    source_blocker: dict[str, Any],
) -> dict[str, Any]:
    # blocker summary 给 Product/Robot/mobile 看状态，不回显 raw input。
    return {
        "blocked": handoff_status != READY_STATUS,
        "handoff_status": handoff_status,
        "source_review_decision": source_decision,
        "status_reasons": status_reasons,
        "source_blocker_summary": source_blocker,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(
    handoff_status: str,
    evidence_ref: str,
    source_decision: str,
    next_required: list[str],
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料正文。
    return {
        "schema": f"{HANDOFF_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "handoff_status": handoff_status,
        "status": handoff_status,
        "source_review_decision": source_decision,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "next_required_evidence": next_required,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_callback_review_handoff(
    execution_callback_review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 execution callback review decision，生成 metadata-only handoff artifact。"""
    payload, load_issue = _load_json(execution_callback_review_decision_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    source_decision = _source_decision(source) if source else ""
    same_ref_status = _same_ref_status(source) if source else "missing_evidence_ref"
    source_owner = _source_owner_handoff(source) if source else {}
    source_next = _list_text(source.get("next_required_evidence")) if source else []
    source_rerun = _dict(source, "rerun_guidance") if source else {}
    source_blocker = _source_blocker_summary(source) if source else {}
    copy_probe = _source_copy_probe(source) if source else {}
    unsafe = bool(payload) and _has_forbidden_copy(copy_probe)
    success_claim = bool(payload) and (_has_success_claim(copy_probe) or _has_success_claim(source))
    handoff_status, status_reasons = _handoff_status(
        load_issue,
        source,
        requested_ref,
        source_ref,
        source_decision,
        same_ref_status,
        unsafe,
        success_claim,
    )
    handoff_package = _handoff_package(handoff_status, evidence_ref_out, source_decision, source_owner)
    owner_handoff = _owner_handoff(handoff_status, evidence_ref_out, source_decision, source_owner)
    rerun_guidance = _rerun_guidance(handoff_status, evidence_ref_out, source_rerun)
    next_required = _next_required_evidence(handoff_status, evidence_ref_out, source_next)
    blocker_summary = _blocker_summary(handoff_status, status_reasons, source_decision, source_blocker)
    safe_copy = _safe_copy(handoff_status, evidence_ref_out, source_decision, next_required)
    summary = {
        "schema": HANDOFF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": status_reasons,
        "source_review_decision": source_decision,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "owner_handoff": owner_handoff,
        "handoff_package": handoff_package,
        "next_required_evidence": next_required,
        "rerun_guidance": rerun_guidance,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This handoff is metadata-only and does not read field material directories.",
            "Keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": HANDOFF_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_execution_callback_review_decision": {
            "load_issue": load_issue,
            "schema": _schema(source) if source else "",
            "evidence_boundary": _boundary(source) if source else "",
            "source_review_decision": source_decision,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "source_review_decision": source_decision,
        "owner_handoff": owner_handoff,
        "handoff_package": handoff_package,
        "next_required_evidence": next_required,
        "rerun_guidance": rerun_guidance,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_callback_review_handoff_summary": summary,
        "robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary": summary,
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
        artifact["status"] = "blocked_unsafe_review_handoff"
        artifact["handoff_status"] = "blocked_unsafe_review_handoff"
        summary["status"] = "blocked_unsafe_review_handoff"
        summary["handoff_status"] = "blocked_unsafe_review_handoff"
        artifact["field_evidence_rerun_execution_callback_review_handoff_summary"] = summary
        artifact["robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun execution callback review handoff artifact")
    parser.add_argument("--execution-callback-decision-json", required=True, help="execution callback review decision artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review handoff")
    parser.add_argument("--output", default="", help="optional handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print handoff artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_callback_review_handoff(
        args.execution_callback_review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_callback_review_handoff: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"execution_callback_review_handoff_summary_file: {_safe_ref(args.summary_output)}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
