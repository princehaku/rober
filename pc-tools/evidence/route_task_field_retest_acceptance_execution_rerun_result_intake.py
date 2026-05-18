#!/usr/bin/env python3
"""生成 route/task field retest acceptance execution rerun result intake artifact。

该 PC-only gate 只读取上一轮 acceptance execution rerun queue artifact、
summary 或 wrapper/nested JSON，并可选读取 safe rerun result packet。输出只
代表 Docker/local software proof 的 result-review intake，不读取真实材料目录、
不触发复跑、不访问 ROS graph、Nav2、硬件、外部云或手机运行时。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本 gate 是 rerun queue 后的新契约，不能复用 queue schema。
INTAKE_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake.v1"
INTAKE_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake_summary.v1"
SCHEMA_VERSION = 1
INTAKE_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate"

# 上游只接受 rerun queue artifact/summary，避免绕过受控复跑队列。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1",
    "trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate"
READY_QUEUE_STATUS = "queued_for_controlled_field_rerun_not_proven"

# result packet 是 owner-safe 回填材料，不是现场通过证明。
RESULT_PACKET_READY_VALUES = {
    "ready",
    "submitted",
    "received",
    "collected",
    "packet_ready",
    "rerun_result_packet_ready",
}

# not_proven 固定覆盖真实路线、电梯、终态、手机、HIL 和 O5 外部证据缺口。
NOT_PROVEN = (
    "real_acceptance_execution_rerun_result",
    "real_controlled_field_rerun_execution",
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

# rg 围栏依赖这些 literal；人工审计也能快速确认证据边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_acceptance_execution_rerun_result_intake; "
    "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate; "
    "ready_for_acceptance_execution_rerun_result_review_not_proven; "
    "needs_acceptance_execution_rerun_result_backfill; "
    "evidence_ref_mismatch_rerun_result; blocked_unsafe_rerun_result; "
    "blocked_unsupported_rerun_queue; not_proven; delivery_success=false; "
    "primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只消费 rerun queue，不读取现场材料目录。
# 设计约束 02：result intake 只表示可进入人工复核，不证明现场复跑通过。
# 设计约束 03：ready 状态仍保持 not_proven 和动作禁用。
# 设计约束 04：source schema/boundary 不匹配必须 fail closed。
# 设计约束 05：缺 safe evidence_ref 不能进入 result review。
# 设计约束 06：same_evidence_ref_required 固定为 true，保护证据链主键。
# 设计约束 07：CLI/source/result evidence_ref 任一不一致都必须重跑。
# 设计约束 08：safe rerun result packet 可选；缺失时进入 backfill。
# 设计约束 09：unsafe copy、凭证、runtime topic、硬件 transport 和路径必须阻断。
# 设计约束 10：success/control claim 必须阻断，不能进入 Robot/mobile。
# 设计约束 11：summary 是下游白名单，不复制完整 source 或 result packet。
# 设计约束 12：wrapper/nested JSON 只递归白名单 key，避免 raw payload 误采信。
# 设计约束 13：source queue 非 queued 时进入 result backfill。
# 设计约束 14：result packet 只允许 owner-safe metadata 和材料类别摘要。
# 设计约束 15：review hint 只给 PC operator，不访问 ROS graph 或硬件。
# 设计约束 16：输出递归脱敏，blocked artifact 也不泄漏 raw material。
# 设计约束 17：exit code 保持 0，让 blocked intake 也能落盘审计。
# 设计约束 18：该 gate 不改变 Start/Confirm/Cancel 或 Robot action gating。
# 设计约束 19：该 gate 不推进 Objective 5 external proof。
# 设计约束 20：新增状态必须同步 tests 和 evidence contract 文档。
# 设计约束 21：该 gate 不替代真实 result review、delivery result 或 HIL。
# 设计约束 22：ready 只代表安全材料足够进入复核，不代表材料真实。
# 设计约束 23：backfill 状态必须说明缺 queue 或 result packet 材料。
# 设计约束 24：mismatch 状态优先保护同一 evidence_ref。
# 设计约束 25：blocked 状态统一覆盖敏感信息、raw artifact 和动作声明。
# 设计约束 26：result packet 的 ready 状态必须是显式白名单值。
# 设计约束 27：unsupported queue 与 unsafe result 分开，方便 owner 定位。
# 设计约束 28：source queue 的 owner handoff 只做安全摘要，不重新判真。
# 设计约束 29：result material categories 只做类别名，不复制文件或 checksum。
# 设计约束 30：safe_copy schema 带 `.safe_copy` 后缀，方便下游识别。
# 设计约束 31：本 gate 不更新 OKR 或 sprint closeout，那是 Product 范围。
# 设计约束 32：本 gate 不更新 Robot/mobile 文件，那是并行 worker 范围。

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

# 成功或动作授权不能通过 result packet 进入下游。
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
    re.compile(r"(?i)\bcontrol\s+(enabled|allowed|granted|authorized)\b"),
)

# 本机绝对路径不能进入 result intake summary。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# 所有自由文本输出前先脱敏，保证 blocked case 也可保存。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\bOSS_[A-Z_]*(ACCESS|SECRET)[A-Z_]*\b\s*[:=]\s*[^,\s]+"), "OSS_KEY=[REDACTED]"),
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


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # result packet 是可选输入；queue 缺失则 fail closed。
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


def _candidates(payload: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免 raw payload 被误采信。
    candidates = [payload]
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_candidates(value, keys))
    return candidates


def _find_queue(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 schema 命中的 rerun queue 对象；否则保留顶层用于 unsupported 解释。
    keys = (
        "route_task_field_retest_acceptance_execution_rerun_queue",
        "route_task_field_retest_acceptance_execution_rerun_queue_summary",
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


def _find_result_packet(payload: dict[str, Any]) -> dict[str, Any]:
    # result packet 支持常见 wrapper，但只提取 owner-safe 字段。
    keys = (
        "rerun_result_packet",
        "safe_rerun_result_packet",
        "result_packet",
        "owner_result_packet",
        "acceptance_execution_rerun_result",
        "route_task_field_retest_acceptance_execution_rerun_result_intake",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    )
    for candidate in _candidates(payload, keys):
        if _result_ref(candidate) or _result_packet_state(candidate) != "missing":
            return candidate
    return payload


def _list_text(value: Any, limit: int = 24) -> list[str]:
    # 摘要只输出扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit] if isinstance(item, (str, int, float, bool))]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _queue_status(source: dict[str, Any]) -> str:
    # rerun_queue_status 是上游主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(_first_text(source.get("rerun_queue_status"), source.get("status"), safe_copy.get("rerun_queue_status"), default=""))


def _queue_ref(source: dict[str, Any]) -> str:
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


def _queue_owner_handoff(source: dict[str, Any]) -> list[Any]:
    # owner handoff 可来自上游顶层或 safe_copy；这里只安全透传摘要。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        item = candidate.get("owner_handoff")
        if isinstance(item, dict):
            return [_safe_value(item)]
        if isinstance(item, list):
            return _safe_value(item[:24])
    return []


def _queue_next_required(source: dict[str, Any]) -> list[str]:
    # next_required_evidence 是交接后的行动清单，不代表已完成。
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


def _result_packet_state(packet: dict[str, Any]) -> str:
    # result packet 必须显式标记已提交/可复核，不能从文案推断。
    if not packet:
        return "missing"
    safe_copy = _dict(packet, "safe_copy")
    for candidate in (packet, safe_copy):
        for key in (
            "rerun_result_packet_status",
            "result_packet_status",
            "acceptance_execution_rerun_result_status",
            "packet_status",
            "state",
            "status",
        ):
            value = _safe_text(candidate.get(key)).strip().lower()
            if value:
                return "ready" if value in RESULT_PACKET_READY_VALUES else value
    return "missing"


def _result_ref(packet: dict[str, Any]) -> str:
    # result packet 也必须绑定同一个 safe evidence_ref。
    safe_copy = _dict(packet, "safe_copy")
    return _safe_ref(
        _first_text(
            packet.get("safe_evidence_ref"),
            packet.get("evidence_ref"),
            packet.get("rerun_evidence_ref"),
            packet.get("result_evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _result_material_categories(packet: dict[str, Any]) -> list[str]:
    # 只保留类别名，不复制材料路径、checksum 或 raw payload。
    safe_copy = _dict(packet, "safe_copy")
    for candidate in (packet, safe_copy):
        for key in ("result_material_categories", "material_categories", "evidence_categories", "provided_materials"):
            items = _list_text(candidate.get(key))
            if items:
                return items
    return []


def _result_summary(packet: dict[str, Any], state: str, evidence_ref: str) -> dict[str, Any]:
    # result packet summary 不复制完整 packet，只保留 owner-safe 元数据。
    return {
        "owner": _safe_text(_first_text(packet.get("owner"), packet.get("result_owner"), default="field_owner")),
        "rerun_result_packet_status": state,
        "safe_evidence_ref": evidence_ref,
        "result_material_categories": _result_material_categories(packet),
        "operator_note": _safe_text(_first_text(packet.get("operator_note"), packet.get("note"), default=""))[:240],
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _intake_status(
    queue_load_issue: str,
    result_load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_status: str,
    result_ref: str,
    result_state: str,
    result_categories: list[str],
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 ready。
    reasons: list[str] = []
    if queue_load_issue:
        reasons.append(queue_load_issue)
    if result_load_issue and result_load_issue != "rerun_result_not_provided":
        reasons.append(result_load_issue)
    if success_claim:
        return "blocked_unsafe_rerun_result", reasons + ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked_unsafe_rerun_result", reasons + ["unsafe_copy_detected"]
    if queue_load_issue or not _schema_supported(source):
        return "blocked_unsupported_rerun_queue", reasons + ["unsupported_acceptance_execution_rerun_queue_schema_or_boundary"]
    if source.get("same_evidence_ref_required") is not True:
        return "evidence_ref_mismatch_rerun_result", reasons + ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return "evidence_ref_mismatch_rerun_result", reasons + ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun_result", reasons + [f"requested_ref:{requested_ref}!={source_ref}"]
    if result_ref and result_ref != source_ref:
        return "evidence_ref_mismatch_rerun_result", reasons + [f"rerun_result_ref:{result_ref}!={source_ref}"]
    if source_status != READY_QUEUE_STATUS:
        return "needs_acceptance_execution_rerun_result_backfill", reasons + [f"source_rerun_queue_status:{source_status or 'missing'}"]
    if result_load_issue or not result_ref:
        return "needs_acceptance_execution_rerun_result_backfill", reasons + ["rerun_result_packet_missing_or_unbound"]
    if result_state != "ready":
        return "needs_acceptance_execution_rerun_result_backfill", reasons + [f"rerun_result_packet_status:{result_state or 'missing'}"]
    if not result_categories:
        return "needs_acceptance_execution_rerun_result_backfill", reasons + ["rerun_result_material_categories_missing"]
    return "ready_for_acceptance_execution_rerun_result_review_not_proven", reasons


def _next_required_evidence(status: str, evidence_ref: str, upstream_next: list[str]) -> list[str]:
    # 下一步只列证据动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_acceptance_execution_rerun_result_review_not_proven":
        return [f"Run acceptance execution rerun result review with safe result packet for evidence_ref={ref}."]
    if status == "needs_acceptance_execution_rerun_result_backfill":
        return upstream_next or [f"Backfill safe rerun result packet for evidence_ref={ref} before result review."]
    if status == "evidence_ref_mismatch_rerun_result":
        return [f"Regenerate rerun queue and result packet with one evidence_ref={ref}."]
    if status == "blocked_unsupported_rerun_queue":
        return [f"Provide a supported rerun queue artifact or summary for evidence_ref={ref}."]
    return ["Regenerate rerun result input without raw paths, credentials, runtime topics, hardware transport detail, unsafe material identifiers, control claims, or success claims."]


def _review_hint(status: str, evidence_ref: str) -> dict[str, Any]:
    # review hint 只给 PC operator 复核，不访问 ROS graph、Nav2 或硬件。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "required": status != "ready_for_acceptance_execution_rerun_result_review_not_proven",
        "status": status,
        "safe_evidence_ref": ref,
        "commands": [
            "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py "
            f"--handoff-intake-json <handoff_intake.json> --queue-request-json <queue_request.json> --evidence-ref {ref} --once-json",
            "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_intake.py "
            f"--rerun-queue-json <rerun_queue.json> --rerun-result-json <safe_rerun_result_packet.json> --evidence-ref {ref} --once-json",
        ],
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(status: str, evidence_ref: str, source_status: str, result_state: str, next_required: list[str]) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料内容。
    return {
        "schema": f"{INTAKE_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": status,
        "rerun_result_intake_status": status,
        "source_rerun_queue_status": source_status,
        "rerun_result_packet_status": result_state,
        "evidence_boundary": INTAKE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "next_required_evidence": next_required,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_acceptance_execution_rerun_result_intake(
    rerun_queue_json: str,
    rerun_result_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 rerun queue 和可选 result packet，生成 result intake artifact。"""
    queue_payload, queue_load_issue = _load_json(rerun_queue_json, "rerun_queue_json")
    result_payload, result_load_issue = _load_json(rerun_result_json, "rerun_result")
    source = _find_queue(queue_payload) if queue_payload else {}
    result_packet = _find_result_packet(result_payload) if result_payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _queue_ref(source) if source else ""
    result_ref = _result_ref(result_packet) if result_packet else ""
    evidence_ref_out = requested_ref or source_ref or result_ref
    source_status = _queue_status(source) if source else ""
    result_state = _result_packet_state(result_packet) if result_packet else "missing"
    upstream_handoff = _queue_owner_handoff(source) if source else []
    upstream_next = _queue_next_required(source) if source else []
    result_categories = _result_material_categories(result_packet) if result_packet else []
    unsafe = (bool(queue_payload) and _has_forbidden_copy(source)) or (bool(result_payload) and _has_forbidden_copy(result_packet))
    success_claim = (bool(queue_payload) and _has_success_claim(source)) or (bool(result_payload) and _has_success_claim(result_packet))
    status, status_reasons = _intake_status(
        queue_load_issue,
        result_load_issue,
        source,
        requested_ref,
        source_ref,
        source_status,
        result_ref,
        result_state,
        result_categories,
        unsafe,
        success_claim,
    )
    next_required = _next_required_evidence(status, evidence_ref_out, upstream_next)
    review_hint = _review_hint(status, evidence_ref_out)
    result_packet_summary = _result_summary(result_packet, result_state, evidence_ref_out)
    owner_handoff = [
        {
            "owner": "Autonomy Algorithm Engineer",
            "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
            "action": "prepare_rerun_result_review" if status == "ready_for_acceptance_execution_rerun_result_review_not_proven" else "repair_rerun_result_inputs_before_review",
            "safe_evidence_ref": evidence_ref_out or "<same_evidence_ref>",
            "source_rerun_queue_status": source_status,
            "rerun_result_packet_status": result_state,
            "upstream_owner_handoff": upstream_handoff,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    ]
    safe_copy = _safe_copy(status, evidence_ref_out, source_status, result_state, next_required)
    summary = {
        "schema": INTAKE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": status,
        "rerun_result_intake_status": status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "source_rerun_queue_schema": _safe_text(source.get("schema", "")) if source else "",
        "source_rerun_queue_status": source_status,
        "rerun_result_packet": result_packet_summary,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "safe_review_hint": review_hint,
        "same_evidence_ref_required": True,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This rerun result intake is metadata-only and does not verify a field rerun result.",
            "Result packet readiness is not real route/elevator field validation, HIL, delivery_result, or delivery_success.",
            "Keep not_proven, delivery_success=false, and primary_actions_enabled=false until real evidence exists.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
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
        "rerun_result_intake_status": status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "source_acceptance_execution_rerun_queue": {
            "load_issue": queue_load_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "source_rerun_queue_status": source_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(bool(queue_payload) and _has_forbidden_copy(source)),
            "success_claim": bool(bool(queue_payload) and _has_success_claim(source)),
        },
        "rerun_result_packet": {
            "load_issue": result_load_issue,
            "state": result_state,
            "safe_evidence_ref": result_ref,
            "result_material_categories": result_categories,
            "unsafe_copy": bool(bool(result_payload) and _has_forbidden_copy(result_packet)),
            "success_claim": bool(bool(result_payload) and _has_success_claim(result_packet)),
        },
        "rerun_result_packet_summary": result_packet_summary,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "safe_review_hint": review_hint,
        "safe_copy": safe_copy,
        "route_task_field_retest_acceptance_execution_rerun_result_intake_summary": summary,
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
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_success_claim(artifact) or _has_success_claim(summary):
        # 最终防线只拦截动作/成功声明；敏感信息已在入口 fail closed。
        artifact["status"] = "blocked_unsafe_rerun_result"
        artifact["rerun_result_intake_status"] = "blocked_unsafe_rerun_result"
        summary["status"] = "blocked_unsafe_rerun_result"
        summary["rerun_result_intake_status"] = "blocked_unsafe_rerun_result"
        artifact["route_task_field_retest_acceptance_execution_rerun_result_intake_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest acceptance execution rerun result intake artifact")
    parser.add_argument("--rerun-queue-json", required=True, help="rerun queue artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--rerun-result-json", default="", help="optional owner-safe rerun result packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this rerun result intake")
    parser.add_argument("--output", default="", help="optional rerun result intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional rerun result intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print rerun result intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_acceptance_execution_rerun_result_intake(
        args.rerun_queue_json,
        args.rerun_result_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_acceptance_execution_rerun_result_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_execution_rerun_result_intake_summary_file: {_safe_ref(args.summary_output)}")
        print(f"rerun_result_intake_status: {artifact['rerun_result_intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
