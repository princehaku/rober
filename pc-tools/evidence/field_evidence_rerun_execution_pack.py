#!/usr/bin/env python3
"""生成 field_evidence_rerun_execution_pack 的 fail-closed PC gate。

该 gate 只读上一轮 field_evidence_rerun_queue artifact、summary 或
wrapper/nested summary，把 metadata-only queue candidate 转成现场 owner
可执行的材料模板和步骤包。它不访问 ROS graph、Nav2 runtime、真实材料目录、
硬件、外部云、真实手机/browser，也不调度或执行现场复跑。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACK_SCHEMA = "trashbot.field_evidence_rerun_execution_pack.v1"
PACK_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_pack_summary.v1"
SCHEMA_VERSION = 1
PACK_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_pack_gate"

SOURCE_SCHEMAS = {
    "trashbot.field_evidence_rerun_queue.v1",
    "trashbot.field_evidence_rerun_queue_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_queue_gate"
READY_QUEUE_STATUS = "queued_for_controlled_field_rerun_not_proven"

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
    "field_evidence_rerun_execution_pack; "
    "software_proof_docker_field_evidence_rerun_execution_pack_gate; "
    "ready_for_field_evidence_rerun_execution_pack_not_proven; "
    "needs_field_evidence_rerun_execution_pack_backfill; "
    "evidence_ref_mismatch_field_evidence_rerun_execution_pack; "
    "blocked_unsafe_field_evidence_rerun_execution_pack; "
    "blocked_unsupported_field_evidence_rerun_queue; "
    "not_proven; safe_to_control=false; delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 位于 queue 之后，不能跳过 owner-safe queue candidate。
# 设计约束 02：execution pack 只让现场 owner 知道如何收集材料，不代表复跑已发生。
# 设计约束 03：queue status 必须 ready，否则只能生成 backfill 指令。
# 设计约束 04：source schema 和 boundary 必须双重匹配，避免误消费其它 artifact。
# 设计约束 05：CLI evidence_ref、source evidence_ref 和 safe_copy 必须保持同一引用。
# 设计约束 06：same_evidence_ref_required 固定为 true，保护现场材料主键。
# 设计约束 07：same_evidence_ref_status 只接受 matched/ready。
# 设计约束 08：source 必须显式 source=software_proof 且包含 not_proven。
# 设计约束 09：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 10：输入出现成功、控制授权或动作文案必须 fail closed。
# 设计约束 11：输入出现 raw path、凭证、ROS topic、串口、WAVE ROVER、checksum 必须阻断。
# 设计约束 12：输出只包含模板和步骤，不复制完整 source artifact。
# 设计约束 13：wrapper/nested JSON 只递归白名单 key，避免采信 raw payload。
# 设计约束 14：material_templates 是现场 owner 填写模板，不读取材料目录。
# 设计约束 15：pass_thresholds 是“可提交给 review”的阈值，不是通过结果。
# 设计约束 16：fail_thresholds 优先描述何时停止提交，避免 happy path 误导。
# 设计约束 17：backfill_instructions 必须保留同一 safe evidence_ref 规则。
# 设计约束 18：safe_copy 是 Robot/mobile 推荐消费面，不含 raw source。
# 设计约束 19：exit code 保持 0，让 blocked execution pack 也能落盘审计。
# 设计约束 20：本文件不访问 docs/vendor，因为不新增硬件协议或参数假设。
# 设计约束 21：non_access_scope 明确列出没有访问的系统面，便于验收边界检查。
# 设计约束 22：最终自检只拦截动作/成功声明，避免 not_proven 枚举自误伤。
# 设计约束 23：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 24：状态名带 not_proven，让下游面板不能误判为现场成功。

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
    # UTC 时间让不同 PC/Docker 主机产物可排序审计。
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


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺失、坏 JSON、非 object 都输出 blocked pack，便于自动化留痕。
    if not path:
        return {}, "queue_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "queue_json_missing"
    except json.JSONDecodeError:
        return {}, "queue_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "queue_json_read_error"
    if not isinstance(payload, dict):
        return {}, "queue_json_not_object"
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
    # 优先选择 field_evidence_rerun_queue summary；找不到时保留顶层解释失败。
    keys = (
        "field_evidence_rerun_queue",
        "field_evidence_rerun_queue_summary",
        "robot_diagnostics_field_evidence_rerun_queue_summary",
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


def _schema(payload: dict[str, Any]) -> str:
    # schema 字段只用于契约判断和输出解释。
    return _safe_text(payload.get("schema", "")).strip()


def _boundary(payload: dict[str, Any]) -> str:
    # boundary 兼容 evidence_boundary / boundary 两种既有字段。
    return _safe_text(_first_text(payload.get("evidence_boundary"), payload.get("boundary"), default="")).strip()


def _source_supported(source: dict[str, Any]) -> bool:
    # 上游 queue 必须来自上一轮固定 boundary。
    return _schema(source) in SOURCE_SCHEMAS and _boundary(source) == SOURCE_BOUNDARY


def _queue_status(source: dict[str, Any]) -> str:
    # queue_status 是上游主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(_first_text(source.get("queue_status"), source.get("status"), safe_copy.get("queue_status"), safe_copy.get("status"), default="")).strip()


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


def _copy_probe(source: dict[str, Any]) -> dict[str, Any]:
    # 只扫描可能下放的字段，避免 artifact 内部枚举误伤。
    return {
        "source_owner_handoff": source.get("owner_handoff"),
        "source_next_required_evidence": source.get("next_required_evidence"),
        "source_safe_rerun_hint": source.get("safe_rerun_hint"),
        "source_rerun_guidance": source.get("rerun_guidance"),
        "source_blocker_summary": source.get("blocker_summary"),
        "source_safe_copy": source.get("safe_copy"),
    }


def _pack_status(
    source_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    queue_status: str,
    same_ref_status: str,
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 ready pack。
    reasons: list[str] = []
    if source_issue:
        reasons.append(source_issue)
    if success_claim:
        return "blocked_unsafe_field_evidence_rerun_execution_pack", reasons + ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked_unsafe_field_evidence_rerun_execution_pack", reasons + ["unsafe_copy_detected"]
    if source_issue or not _source_supported(source):
        return "blocked_unsupported_field_evidence_rerun_queue", reasons + ["unsupported_field_evidence_rerun_queue_schema_or_boundary"]
    if not _is_software_not_proven(source):
        return "blocked_unsupported_field_evidence_rerun_queue", reasons + ["source_not_software_proof_or_missing_not_proven"]
    if not _flags_ok(source):
        return "blocked_unsafe_field_evidence_rerun_execution_pack", reasons + ["source_action_flags_not_false"]
    if source.get("same_evidence_ref_required") is not True:
        return "evidence_ref_mismatch_field_evidence_rerun_execution_pack", reasons + ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return "evidence_ref_mismatch_field_evidence_rerun_execution_pack", reasons + ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_field_evidence_rerun_execution_pack", reasons + [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref_status not in {"matched", "ready"}:
        return "evidence_ref_mismatch_field_evidence_rerun_execution_pack", reasons + [f"same_evidence_ref:{same_ref_status}"]
    if queue_status != READY_QUEUE_STATUS:
        return "needs_field_evidence_rerun_execution_pack_backfill", reasons + [f"source_queue_status:{queue_status or 'missing'}"]
    return "ready_for_field_evidence_rerun_execution_pack_not_proven", reasons


def _execution_steps(evidence_ref: str) -> list[dict[str, Any]]:
    # 步骤只描述现场 owner 要收集的材料顺序，不包含机器人控制命令。
    ref = evidence_ref or "<same_evidence_ref>"
    names = [
        ("owner_ack", "确认本次执行包只用于 evidence_ref 同步和材料采集，不能触发机器人动作。"),
        ("task_record", "采集真实 task record，记录任务 id、目标、时间窗和失败原因字段。"),
        ("nav2_or_fixed_route_log", "采集 Nav2 或 fixed-route runtime log，并标注该 log 对应同一 evidence_ref。"),
        ("route_completion_signal", "采集路线完成信号或未完成原因，禁止用口头成功替代材料。"),
        ("elevator_context", "采集电梯门、目标楼层、到达楼层和人工协助记录。"),
        ("terminal_completion", "采集 dropoff 或 cancel completion 材料；缺任一项时保持 not_proven。"),
        ("delivery_result", "采集 delivery result 或失败分类，不能把 queued/pack ready 当 delivery result。"),
        ("phone_browser_evidence", "采集真实 phone/browser 只读证据截图或日志，保持主动作禁用。"),
        ("review_backfill", "把所有材料按同一 safe evidence_ref 回填给下一轮 review/intake。"),
    ]
    return [
        {
            "order": index,
            "step_id": step_id,
            "safe_evidence_ref": ref,
            "instruction": instruction,
            "not_proven": "not_proven",
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        for index, (step_id, instruction) in enumerate(names, start=1)
    ]


def _material_templates(evidence_ref: str) -> list[dict[str, Any]]:
    # 模板固定覆盖 plan 要求的七类真实现场材料，但这里只输出字段骨架。
    ref = evidence_ref or "<same_evidence_ref>"
    templates = [
        ("task_record.json", "field_task_record", ["evidence_ref", "task_id", "mission_goal", "timestamps", "failure_reason"]),
        ("nav2_fixed_route_runtime_log.json", "nav2_fixed_route_runtime_log", ["evidence_ref", "route_id", "runtime_window", "planner_or_controller_status", "failure_reason"]),
        ("route_completion_signal.json", "route_completion_signal", ["evidence_ref", "completion_state", "completion_timestamp", "incomplete_reason"]),
        ("elevator_context.json", "elevator_door_floor_human_assist", ["evidence_ref", "door_state", "target_floor", "arrival_floor", "human_assistance_note"]),
        ("terminal_completion.json", "dropoff_cancel_completion", ["evidence_ref", "dropoff_state", "cancel_state", "terminal_failure_reason"]),
        ("delivery_result.json", "delivery_result", ["evidence_ref", "delivery_result_state", "result_reason", "review_owner"]),
        ("phone_browser_evidence.json", "real_phone_browser_evidence", ["evidence_ref", "device_or_browser", "capture_time", "readonly_panel_state", "redaction_note"]),
    ]
    return [
        {
            "template_file": template_file,
            "material_type": material_type,
            "safe_evidence_ref": ref,
            "required_fields": required_fields,
            "redaction_required": True,
            "not_proven_until_backfilled": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        for template_file, material_type, required_fields in templates
    ]


def _fail_thresholds(evidence_ref: str) -> list[str]:
    # fail threshold 让现场 owner 知道何时停止提交而不是编造 happy path。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"Any material missing evidence_ref={ref} or using a different evidence_ref must fail review.",
        "Any raw credential, local path, ROS topic, serial/UART detail, checksum, or raw artifact copy must fail review.",
        "Any delivery-success, field-validation, HIL-validation, real Nav2 proof, or enabled-primary-action claim must fail review.",
        "Missing task record, runtime log, route completion signal, elevator context, terminal completion, delivery result, or real phone/browser evidence keeps not_proven.",
    ]


def _pass_thresholds(evidence_ref: str) -> list[str]:
    # pass threshold 只表示“可进入下一轮人工 review”，不表示现场结果通过。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"All required material templates are filled with the same safe evidence_ref={ref}.",
        "Every material is redacted and contains no credentials, raw runtime topics, hardware transport detail, or raw artifact dumps.",
        "Task record, route/runtime log, completion signal, elevator context, terminal completion, delivery result, and phone/browser evidence are all present for review.",
        "Reviewer can classify accepted/missing/rejected materials without enabling robot control or primary mobile actions.",
    ]


def _backfill_instructions(status: str, evidence_ref: str, source_next: list[str]) -> list[str]:
    # backfill 指令只补材料和上游 gate，不声称真实执行完成。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_field_evidence_rerun_execution_pack_not_proven":
        return [f"After field owner captures materials, submit redacted packet with the same safe evidence_ref={ref} for result review."]
    if status == "needs_field_evidence_rerun_execution_pack_backfill":
        return source_next or [f"Regenerate field_evidence_rerun_queue in queued state for evidence_ref={ref} before creating the execution pack."]
    if status == "evidence_ref_mismatch_field_evidence_rerun_execution_pack":
        return [f"Regenerate queue and execution pack request with one evidence_ref={ref}."]
    if status == "blocked_unsupported_field_evidence_rerun_queue":
        return [f"Provide supported field_evidence_rerun_queue artifact or summary for evidence_ref={ref}."]
    return ["Regenerate queue input without raw paths, credentials, ROS topics, serial/UART detail, WAVE ROVER fields, checksums, complete/raw artifacts, tracebacks, control claims, or success claims."]


def _owner_handoff(status: str, evidence_ref: str, queue_status: str) -> dict[str, Any]:
    # owner_handoff 只表达人工材料归属，不授权 Robot/mobile 控制。
    return {
        "owner": "Autonomy Algorithm Engineer",
        "field_owner": "field_rerun_owner",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "action": "collect_same_evidence_ref_field_materials" if status == "ready_for_field_evidence_rerun_execution_pack_not_proven" else "repair_queue_before_field_material_collection",
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "source_queue_status": queue_status,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(status: str, evidence_ref: str, queue_status: str, next_required: list[str]) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料正文。
    return {
        "schema": f"{PACK_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": status,
        "execution_pack_status": status,
        "source_queue_status": queue_status,
        "evidence_boundary": PACK_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "next_required_evidence": next_required,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_pack(queue_json: str, evidence_ref: str = "") -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 queue artifact/summary，生成 metadata-only execution pack。"""
    source_payload, source_issue = _load_json(queue_json)
    source = _find_source(source_payload) if source_payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    queue_status = _queue_status(source) if source else ""
    same_ref_status = _same_ref_status(source) if source else "missing_evidence_ref"
    source_next = _list_text(source.get("next_required_evidence")) if source else []
    copy_probe = _copy_probe(source) if source else {}
    unsafe = bool(source_payload) and _has_forbidden_copy(copy_probe)
    success_claim = bool(source_payload) and (_has_success_claim(copy_probe) or _has_success_claim(source))
    status, reasons = _pack_status(source_issue, source, requested_ref, source_ref, queue_status, same_ref_status, unsafe, success_claim)
    execution_steps = _execution_steps(evidence_ref_out)
    material_templates = _material_templates(evidence_ref_out)
    fail_thresholds = _fail_thresholds(evidence_ref_out)
    pass_thresholds = _pass_thresholds(evidence_ref_out)
    backfill_instructions = _backfill_instructions(status, evidence_ref_out, source_next)
    owner_handoff = _owner_handoff(status, evidence_ref_out, queue_status)
    safe_copy = _safe_copy(status, evidence_ref_out, queue_status, backfill_instructions)
    blocker_summary = {
        "blocked": status != "ready_for_field_evidence_rerun_execution_pack_not_proven",
        "execution_pack_status": status,
        "source_queue_status": queue_status,
        "same_evidence_ref_status": same_ref_status,
        "status_reasons": reasons,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = {
        "schema": PACK_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "status": status,
        "execution_pack_status": status,
        "status_reasons": reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "source_queue_schema": _safe_text(source.get("schema", "")) if source else "",
        "source_queue_status": queue_status,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "execution_steps": execution_steps,
        "material_templates": material_templates,
        "owner_handoff": owner_handoff,
        "fail_thresholds": fail_thresholds,
        "pass_thresholds": pass_thresholds,
        "backfill_instructions": backfill_instructions,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This execution pack is metadata-only and does not execute a field rerun.",
            "Pack readiness is not real Nav2, route/elevator field validation, HIL validation, phone/browser proof, delivery_result, or delivery_success.",
            "Keep not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false until real evidence exists.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": PACK_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "status": status,
        "execution_pack_status": status,
        "status_reasons": reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_queue": {
            "load_issue": source_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "source_queue_status": queue_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(bool(source_payload) and _has_forbidden_copy(source)),
            "success_claim": bool(bool(source_payload) and _has_success_claim(source)),
        },
        "execution_steps": execution_steps,
        "material_templates": material_templates,
        "owner_handoff": owner_handoff,
        "fail_thresholds": fail_thresholds,
        "pass_thresholds": pass_thresholds,
        "backfill_instructions": backfill_instructions,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_pack_summary": summary,
        "robot_diagnostics_field_evidence_rerun_execution_pack_summary": summary,
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
        artifact["status"] = "blocked_unsafe_field_evidence_rerun_execution_pack"
        artifact["execution_pack_status"] = "blocked_unsafe_field_evidence_rerun_execution_pack"
        summary["status"] = "blocked_unsafe_field_evidence_rerun_execution_pack"
        summary["execution_pack_status"] = "blocked_unsafe_field_evidence_rerun_execution_pack"
        artifact["field_evidence_rerun_execution_pack_summary"] = summary
        artifact["robot_diagnostics_field_evidence_rerun_execution_pack_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun execution pack artifact")
    parser.add_argument("--queue-json", required=True, help="field evidence rerun queue artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this execution pack")
    parser.add_argument("--output", default="", help="optional execution pack artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional execution pack summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print execution pack artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_pack(args.queue_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_pack: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_rerun_execution_pack_summary_file: {_safe_ref(args.summary_output)}")
        print(f"execution_pack_status: {artifact['execution_pack_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
