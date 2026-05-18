#!/usr/bin/env python3
"""生成 acceptance execution rerun result review handoff artifact。

该 dependency-free PC gate 只读取上一轮 review decision 的 artifact、summary
或 wrapper/nested JSON，把 safe decision fields 转成 owner 可执行 handoff
package。它不读取真实材料目录、不解析 raw artifact、不访问 ROS graph、Nav2
runtime、serial/UART、外部云、DB/queue、真实手机/browser，也不触发机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本 gate 是 review decision 后的新契约，不能复用上游 decision schema。
HANDOFF_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff.v1"
HANDOFF_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary.v1"
SCHEMA_VERSION = 1
HANDOFF_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate"

# 只接受上一轮 acceptance execution rerun result review decision。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision.v1",
    "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate"

READY_DECISION_STATUS = "ready_for_acceptance_execution_rerun_result_handoff"
BACKFILL_DECISION_STATUS = "needs_acceptance_execution_rerun_result_backfill"
MISMATCH_DECISION_STATUS = "evidence_ref_mismatch_rerun_result"
UNSAFE_DECISION_STATUS = "blocked_unsafe_rerun_result"
UNSUPPORTED_DECISION_STATUS = "blocked_unsupported_rerun_result_intake"

# handoff 仍需这些材料类别；本 gate 只生成补证 checklist，不验真材料内容。
REQUIRED_RERUN_RESULT_MATERIALS = (
    "route_completion_signal",
    "task_record",
    "nav2_fixed_route_runtime_log",
    "dropoff_or_cancel_completion",
    "delivery_result",
    "elevator_door_state",
    "target_floor_confirmation",
    "human_assistance_record",
)

# not_proven 明确覆盖 route/elevator、HIL、手机和 O5 外部证据边界。
NOT_PROVEN = (
    "real_route_elevator_field_pass",
    "real_acceptance_execution_rerun_result_owner_handoff",
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
    "route_task_field_retest_acceptance_execution_rerun_result_review_handoff; "
    "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate; "
    "ready_for_acceptance_execution_rerun_result_owner_handoff; "
    "needs_acceptance_execution_rerun_result_material_backfill; "
    "evidence_ref_mismatch_rerun_result_handoff_blocked; "
    "blocked_unsafe_rerun_result_handoff_copy; "
    "blocked_unsupported_rerun_result_review_decision; "
    "source=software_proof; not_proven; delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只消费 review decision，不读材料目录。
# 设计约束 02：handoff_status 只表达 owner 可执行交接，不证明现场通过。
# 设计约束 03：ready 分支仍保持 not_proven，不能改变 Robot/mobile action。
# 设计约束 04：source decision 是唯一映射来源，不重新解释 raw material。
# 设计约束 05：unsupported schema/boundary 或缺 decision 必须 fail closed。
# 设计约束 06：unsafe copy、success claim 和 control claim 必须阻断。
# 设计约束 07：same_evidence_ref_required 固定为 true，维持证据链主键。
# 设计约束 08：owner_handoff 是只读人工清单，不执行现场回填。
# 设计约束 09：summary 是 Robot/mobile 可消费面，只输出白名单字段。
# 设计约束 10：wrapper/nested JSON 只递归固定 key，避免采信 raw payload。
# 设计约束 11：缺 evidence_ref 不进入 ready，因为下游无法复账。
# 设计约束 12：缺 route completion signal 必须进入 material backfill。
# 设计约束 13：缺 task record 必须进入 material backfill。
# 设计约束 14：缺 Nav2/fixed-route runtime log 必须进入 material backfill。
# 设计约束 15：缺 dropoff/cancel completion 必须进入 material backfill。
# 设计约束 16：缺 delivery result 必须进入 material backfill。
# 设计约束 17：缺 elevator door state 必须进入 material backfill。
# 设计约束 18：缺 target floor confirmation 必须进入 material backfill。
# 设计约束 19：缺 human assistance record 必须进入 material backfill。
# 设计约束 20：rerun commands 使用占位路径，避免泄漏本机路径。
# 设计约束 21：输出递归脱敏，blocked artifact 也不泄漏 raw material。
# 设计约束 22：exit code 保持 0，让 blocked handoff 也能落盘审计。
# 设计约束 23：该 gate 不改变 Start/Confirm/Cancel 或 Robot action gating。
# 设计约束 24：该 gate 不推进 Objective 5 external proof。
# 设计约束 25：该 gate 不证明 HIL、真实手机/browser 或真实 delivery result。
# 设计约束 26：safe_copy schema 带 `.safe_copy` 后缀，方便下游识别。
# 设计约束 27：blocked_unsupported 与 blocked_unsafe 分开，方便 owner 定位。
# 设计约束 28：材料完整性只来自白名单字段，不能解析自由文本。
# 设计约束 29：source review decision 只保留类别名和 ready 状态。
# 设计约束 30：文档和单测必须同步覆盖所有 handoff status mapping。
# 设计约束 31：本 gate 不更新 OKR 或 sprint closeout，那是 Product 范围。
# 设计约束 32：本 gate 不更新 Robot/mobile 文件，那是并行 worker 范围。
# 设计约束 33：PR #4 现场回填准备层只提供 owner package，不声明现场通过。
# 设计约束 34：所有状态名使用 snake_case，便于 rg 和下游解析。

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

RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

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
    # UTC 时间便于 Docker-only 主机和后续 sprint artifact 按时间线复盘。
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
    # forbidden copy 命中说明输入不适合进入 owner handoff。
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
    # 缺输入、坏 JSON、非 object 都输出 unsupported handoff，便于留痕。
    if not path:
        return {}, "rerun_result_review_decision_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "rerun_result_review_decision_missing"
    except json.JSONDecodeError:
        return {}, "rerun_result_review_decision_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "rerun_result_review_decision_read_error"
    if not isinstance(payload, dict):
        return {}, "rerun_result_review_decision_not_object"
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
        "route_task_field_retest_acceptance_execution_rerun_result_review_decision",
        "route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary",
        "route_task_field_retest_acceptance_execution_rerun_result_review_handoff",
        "route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary",
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


def _list_text(value: Any, limit: int = 32) -> list[str]:
    # 摘要只输出扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                label = _first_text(item.get("material"), item.get("name"), item.get("id"), item.get("action"), default="")
                if label:
                    items.append(_safe_text(label))
            elif isinstance(item, (str, int, float, bool)):
                items.append(_safe_text(item))
        return items
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _list_items(value: Any, limit: int = 24) -> list[Any]:
    # owner handoff 只接受 list，避免字符串被当成结构化任务。
    if not isinstance(value, list):
        return []
    return _safe_value(value[:limit])


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层、summary 或 safe_copy 取，最终仍做路径收敛。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    package = _dict(source, "review_decision_package")
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
            package.get("safe_evidence_ref"),
            package.get("evidence_ref"),
            default="",
        )
    )


def _source_decision_status(source: dict[str, Any]) -> str:
    # decision_status 是上游主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    package = _dict(source, "review_decision_package")
    return _safe_text(
        _first_text(
            source.get("decision_status"),
            source.get("status"),
            package.get("status"),
            safe_copy.get("decision_status"),
            safe_copy.get("status"),
            default="",
        )
    )


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止其它 gate JSON 混入。
    schema = str(source.get("schema", "")).strip()
    boundary = str(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    return schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY


def _same_ref_required_ok(source: dict[str, Any]) -> bool:
    # same_evidence_ref_required 必须是真布尔 true，弱类型字符串不能通过。
    return source.get("same_evidence_ref_required") is True


def _decision_package_ready(source: dict[str, Any]) -> bool:
    # ready 必须是真布尔值；字符串 true 不能提升为 owner handoff ready。
    package = _dict(source, "review_decision_package")
    safe_copy = _dict(source, "safe_copy")
    return package.get("ready") is True or safe_copy.get("handoff_ready") is True


def _source_owner_handoff(source: dict[str, Any]) -> list[Any]:
    # owner_handoff 可来自上游顶层或 safe_copy；这里只安全透传摘要。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        items = _list_items(candidate.get("owner_handoff") or candidate.get("owner_work_orders"))
        if items:
            return items
    return []


def _source_next_required(source: dict[str, Any]) -> list[str]:
    # next_required_evidence 是下一步行动清单，不代表已完成。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        items = _list_text(candidate.get("next_required_evidence"))
        if items:
            return items
    return []


def _source_rerun_commands(source: dict[str, Any]) -> list[str]:
    # 上游 rerun commands 只保留文本摘要；unsafe 输入会先 fail closed。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        items = _list_text(candidate.get("rerun_commands") or candidate.get("commands"))
        if items:
            return items
    return []


def _material_lists(source: dict[str, Any]) -> tuple[list[str], list[str]]:
    # 材料字段只接受白名单结构；默认全部 missing，防止空输入误 ready。
    package = _dict(source, "review_decision_package")
    provided = _list_text(source.get("provided_materials") or package.get("provided_materials"))
    missing = _list_text(source.get("missing_materials") or package.get("missing_materials"))
    provided_set = {item for item in provided if item in REQUIRED_RERUN_RESULT_MATERIALS}
    if not missing:
        missing = [item for item in REQUIRED_RERUN_RESULT_MATERIALS if item not in provided_set]
    return provided, [item for item in missing if item in REQUIRED_RERUN_RESULT_MATERIALS]


def _handoff_status(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    decision_status: str,
    package_ready: bool,
    missing_materials: list[str],
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 owner handoff ready。
    if success_claim:
        return "blocked_unsafe_rerun_result_handoff_copy", ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked_unsafe_rerun_result_handoff_copy", ["unsafe_copy_detected"]
    if load_issue:
        return "blocked_unsupported_rerun_result_review_decision", [load_issue]
    if not _schema_supported(source):
        return "blocked_unsupported_rerun_result_review_decision", ["unsupported_rerun_result_review_decision_schema_or_boundary"]
    if not _same_ref_required_ok(source):
        return "evidence_ref_mismatch_rerun_result_handoff_blocked", ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return "evidence_ref_mismatch_rerun_result_handoff_blocked", ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun_result_handoff_blocked", [f"requested_ref:{requested_ref}!={source_ref}"]
    if decision_status == MISMATCH_DECISION_STATUS:
        return "evidence_ref_mismatch_rerun_result_handoff_blocked", [f"source_decision_status:{decision_status}"]
    if decision_status == UNSAFE_DECISION_STATUS:
        return "blocked_unsafe_rerun_result_handoff_copy", [f"source_decision_status:{decision_status}"]
    if decision_status == UNSUPPORTED_DECISION_STATUS:
        return "blocked_unsupported_rerun_result_review_decision", [f"source_decision_status:{decision_status}"]
    if decision_status == BACKFILL_DECISION_STATUS or missing_materials or not package_ready:
        return "needs_acceptance_execution_rerun_result_material_backfill", ["acceptance_execution_rerun_result_material_backfill_required"]
    if decision_status == READY_DECISION_STATUS and package_ready:
        return "ready_for_acceptance_execution_rerun_result_owner_handoff", []
    return "blocked_unsupported_rerun_result_review_decision", [f"unsupported_source_decision_status:{decision_status or 'missing'}"]


def _owner_handoff(
    handoff_status: str,
    evidence_ref: str,
    missing_materials: list[str],
    upstream_handoff: list[Any],
) -> list[dict[str, Any]]:
    # owner handoff 只描述人工补证/交接责任，不给 Robot/mobile 控制指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == "ready_for_acceptance_execution_rerun_result_owner_handoff":
        action = "prepare_acceptance_execution_rerun_result_owner_handoff_from_sanitized_review_decision"
    elif handoff_status == "needs_acceptance_execution_rerun_result_material_backfill":
        action = "backfill_acceptance_execution_rerun_result_materials_before_owner_handoff"
    elif handoff_status == "evidence_ref_mismatch_rerun_result_handoff_blocked":
        action = "regenerate_rerun_result_review_decision_with_same_evidence_ref"
    elif handoff_status == "blocked_unsupported_rerun_result_review_decision":
        action = "provide_supported_rerun_result_review_decision_artifact_or_summary"
    else:
        action = "regenerate_review_decision_without_unsafe_copy_or_success_claim"
    return [
        {
            "owner": "Autonomy Algorithm Engineer",
            "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
            "action": action,
            "safe_evidence_ref": ref,
            "missing_materials": missing_materials,
            "upstream_owner_handoff": upstream_handoff,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    ]


def _next_required_evidence(handoff_status: str, evidence_ref: str, missing_materials: list[str], upstream_next: list[str]) -> list[str]:
    # 下一步只列证据动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == "ready_for_acceptance_execution_rerun_result_owner_handoff":
        return [f"Prepare PR #4 owner handoff package for evidence_ref={ref} from sanitized review decision."]
    if handoff_status == "needs_acceptance_execution_rerun_result_material_backfill":
        needed = ", ".join(missing_materials or REQUIRED_RERUN_RESULT_MATERIALS)
        return upstream_next or [f"Backfill acceptance execution rerun result materials for evidence_ref={ref}: {needed}."]
    if handoff_status == "evidence_ref_mismatch_rerun_result_handoff_blocked":
        return [f"Regenerate rerun result intake, review decision, and handoff with one evidence_ref={ref}."]
    if handoff_status == "blocked_unsupported_rerun_result_review_decision":
        return [f"Provide supported rerun result review decision artifact or summary for evidence_ref={ref}."]
    return ["Regenerate review decision without raw paths, credentials, runtime topics, hardware transport detail, control claims, or success claims."]


def _rerun_commands(handoff_status: str, evidence_ref: str, upstream_commands: list[str]) -> list[str]:
    # rerun commands 使用占位路径，避免泄漏本机或真实材料路径。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = upstream_commands[:6] if upstream_commands else []
    commands.append(
        "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py "
        f"--rerun-result-intake-json <rerun_result_intake.json> --evidence-ref {ref} --once-json"
    )
    commands.append(
        "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py "
        f"--rerun-result-review-decision-json <rerun_result_review_decision.json> --evidence-ref {ref} --once-json"
    )
    if handoff_status == "ready_for_acceptance_execution_rerun_result_owner_handoff":
        commands.append("PR #4 owner handoff: collect real route/elevator field callback evidence outside this software-proof gate.")
    return commands


def _safe_copy(
    handoff_status: str,
    evidence_ref: str,
    owner_handoff: list[dict[str, Any]],
    next_required: list[str],
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料内容。
    return {
        "schema": f"{HANDOFF_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "handoff_status": handoff_status,
        "status": handoff_status,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_acceptance_execution_rerun_result_review_handoff(
    rerun_result_review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 rerun result review decision，生成 owner handoff artifact。"""
    payload, load_issue = _load_json(rerun_result_review_decision_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    decision_status = _source_decision_status(source) if source else ""
    package_ready = _decision_package_ready(source) if source else False
    upstream_handoff = _source_owner_handoff(source) if source else []
    upstream_next = _source_next_required(source) if source else []
    upstream_commands = _source_rerun_commands(source) if source else []
    provided_materials, missing_materials = _material_lists(source) if source else ([], list(REQUIRED_RERUN_RESULT_MATERIALS))
    unsafe = bool(payload) and _has_forbidden_copy(source)
    success_claim = bool(payload) and _has_success_claim(source)
    handoff_status, status_reasons = _handoff_status(
        load_issue,
        source,
        requested_ref,
        source_ref,
        decision_status,
        package_ready,
        missing_materials,
        unsafe,
        success_claim,
    )
    owner_handoff = _owner_handoff(handoff_status, evidence_ref_out, missing_materials, upstream_handoff)
    next_required = _next_required_evidence(handoff_status, evidence_ref_out, missing_materials, upstream_next)
    rerun_commands = _rerun_commands(handoff_status, evidence_ref_out, upstream_commands)
    safe_copy = _safe_copy(handoff_status, evidence_ref_out, owner_handoff, next_required)
    rerun_summary = {
        "source_decision_status": decision_status,
        "provided_materials": provided_materials,
        "missing_materials": missing_materials,
        "package_ready": package_ready,
        "safe_evidence_ref": evidence_ref_out,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = {
        "schema": HANDOFF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": status_reasons,
        "source_decision_status": decision_status,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "owner_role": "Autonomy Algorithm Engineer",
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "rerun_summary": rerun_summary,
        "rerun_commands": rerun_commands,
        "provided_materials": provided_materials,
        "missing_materials": missing_materials,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This PR #4 handoff package is metadata-only and does not read field material directories.",
            "Keep not_proven, delivery_success=false, and primary_actions_enabled=false until real route/elevator evidence exists.",
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
        "source": "software_proof",
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "owner_role": "Autonomy Algorithm Engineer",
        "source_acceptance_execution_rerun_result_review_decision": {
            "load_issue": load_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "source_decision_status": decision_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "rerun_summary": rerun_summary,
        "rerun_commands": rerun_commands,
        "provided_materials": provided_materials,
        "missing_materials": missing_materials,
        "safe_copy": safe_copy,
        "route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "raw_artifact",
            "raw_field_material_content",
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
            "phone_device",
            "robot_action",
            "field_rerun_execution",
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
    parser = argparse.ArgumentParser(description="Generate an acceptance execution rerun result review handoff artifact")
    parser.add_argument("--rerun-result-review-decision-json", required=True, help="rerun result review decision artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review handoff")
    parser.add_argument("--output", default="", help="optional handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print handoff artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_acceptance_execution_rerun_result_review_handoff(
        args.rerun_result_review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_acceptance_execution_rerun_result_review_handoff: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_execution_rerun_result_review_handoff_summary_file: {_safe_ref(args.summary_output)}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
