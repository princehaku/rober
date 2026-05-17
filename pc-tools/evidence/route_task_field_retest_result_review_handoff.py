#!/usr/bin/env python3
"""生成 route/task field retest result review handoff artifact。

该 dependency-free PC gate 只读取上一轮 result review decision 的 artifact、
summary 或 wrapper/nested JSON，把 decision status、accepted/blocked/rerun
reasons、owner handoff、safe evidence_ref、missing materials 和 rerun package
转成 owner 可执行 handoff package。它不读取真实材料目录，不访问 ROS graph、
Nav2 runtime、serial/UART、WAVE ROVER、外部云、4G、OSS/CDN、DB/queue 或
真实手机/browser，也不触发任何机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本 gate 是 result review decision 后的新契约，不能复用 decision schema。
HANDOFF_SCHEMA = "trashbot.route_task_field_retest_result_review_handoff.v1"
HANDOFF_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_result_review_handoff_summary.v1"
SCHEMA_VERSION = 1
HANDOFF_BOUNDARY = "software_proof_docker_route_task_field_retest_result_review_handoff_gate"

# 只接受上一轮 result review decision，避免跳过 decision 直接包装 intake。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_result_review_decision.v1",
    "trashbot.route_task_field_retest_result_review_decision_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_result_review_decision_gate"

# handoff package 只描述下一步人工补证/复跑，不证明真实现场结果。
NOT_PROVEN = (
    "real_nav2_fixed_route_runtime",
    "real_route_completion_signal",
    "real_task_record",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_record",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result_review",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 后续 owner callback 仍需这些材料类别；本 gate 只生成 checklist。
REQUIRED_RESULT_MATERIALS = (
    "elevator_door_state",
    "target_floor_confirmation",
    "human_assistance_record",
    "nav2_fixed_route_runtime_log",
    "route_completion_signal",
    "task_record",
    "dropoff_completion",
    "cancel_completion",
    "delivery_result",
)

# rg 围栏依赖这些 literal，人工复盘也能快速识别本 gate 的边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_result_review_handoff; "
    "software_proof_docker_route_task_field_retest_result_review_handoff_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false; "
    "ready_for_owner_result_callback_not_proven; "
    "needs_result_material_callback_not_proven; "
    "evidence_ref_mismatch_rerun_not_proven; "
    "blocked_missing_result_review_decision_not_proven; "
    "unsupported_result_review_decision_schema_not_proven"
)

# 设计约束 01：本 gate 只消费 result review decision，不读材料目录。
# 设计约束 02：handoff_status 只表达 owner 可执行交接，不证明现场通过。
# 设计约束 03：ready 分支仍保持 not_proven，不能改变 Robot/mobile action。
# 设计约束 04：source decision 是唯一映射来源，不重新解释 raw material。
# 设计约束 05：unsupported schema/boundary 或缺 decision 必须 fail closed。
# 设计约束 06：unsafe copy 与 success/control claim 必须阻断。
# 设计约束 07：same_evidence_ref_required 固定为 true，维持证据链主键。
# 设计约束 08：owner_work_orders 是只读人工清单，不执行 callback。
# 设计约束 09：summary 是 Robot/mobile 可消费面，只输出白名单字段。
# 设计约束 10：wrapper/nested JSON 只递归固定 key，避免采信 raw payload。
# 设计约束 11：缺 evidence_ref 不进入 ready，因为下游无法复账。
# 设计约束 12：accepted/blocked/rerun reasons 只做安全摘要，不打开材料。
# 设计约束 13：rerun_commands 只是 PC operator 提示，不访问 ROS 或硬件。
# 设计约束 14：输出递归脱敏，blocked artifact 也不泄漏 raw source。
# 设计约束 15：dependency-free，便于 macOS PC 与 Docker 本地验证。
# 设计约束 16：exit code 保持 0，让 blocked handoff 也能作为证据落盘。
# 设计约束 17：文档和单测同步覆盖所有 handoff status mapping。
# 设计约束 18：该 gate 不推进 Objective 5 external proof。
# 设计约束 19：该 gate 不替代真实 route/elevator result callback。
# 设计约束 20：该 gate 不触发 fixed-route、Nav2、dropoff 或 cancel 动作。
# 设计约束 21：ready 只代表 owner 可接手补证，不代表现场材料通过。
# 设计约束 22：needs callback 只要求 owner 回填，不授权自动驾驶动作。
# 设计约束 23：mismatch 优先保护同一证据链主键。
# 设计约束 24：missing decision 与 unsupported decision 分开，方便定位。
# 设计约束 25：source schema 不匹配时不尝试“尽力理解”，直接 unsupported。
# 设计约束 26：source boundary 不匹配时说明链路断裂，不能跨 gate 消费。
# 设计约束 27：缺 safe_evidence_ref 时下游无法复账，因此必须复跑。
# 设计约束 28：缺 decision_status 时不从 package 字段推导结论。
# 设计约束 29：safe_copy 只能给只读 UI/diagnostics 使用，不给控制路径使用。
# 设计约束 30：owner_work_orders 使用动词短语，避免被误读成机器指令。
# 设计约束 31：next_material_callback_requirements 只写证据动作。
# 设计约束 32：source_result_review_decision 只保留 schema/boundary/ref 摘要。
# 设计约束 33：robot_diagnostics_summary 与 summary 同源，避免口径漂移。
# 设计约束 34：mobile_readonly_summary 与 summary 同源，避免手机文案扩权。
# 设计约束 35：non_access_scope 明确本 gate 不访问运行时和硬件。
# 设计约束 36：not_proven 列表必须随 artifact 和 summary 同步输出。
# 设计约束 37：delivery_success 固定 false，不能被 source 覆盖。
# 设计约束 38：primary_actions_enabled 固定 false，不能被 source 覆盖。
# 设计约束 39：输入安全扫描发生在脱敏前，命中后不允许清洗成 ready。
# 设计约束 40：输出脱敏发生在落盘前，blocked 产物也不能泄漏敏感文本。
# 设计约束 41：FORBIDDEN_COPY 专门约束输入，不约束内部 non_access_scope。
# 设计约束 42：SUCCESS_CLAIM_PATTERNS 同时覆盖自由文案和 key=value 表达。
# 设计约束 43：RAW_PATH_PATTERNS 覆盖 macOS/Linux/Windows 常见绝对路径。
# 设计约束 44：SENSITIVE_PATTERNS 不保留原 token，统一转为 redacted 形态。
# 设计约束 45：wrapper 递归只走固定 key，避免任意 JSON 被误当 source。
# 设计约束 46：_safe_ref 对路径只保留 basename，避免证据号泄漏目录。
# 设计约束 47：_list_text 只保留可打印标量，避免复制 nested raw object。
# 设计约束 48：source boundary 为空不兼容；本 sprint 要求边界固定。
# 设计约束 49：safe_copy schema 带 `.safe_copy` 后缀，方便下游识别白名单面。
# 设计约束 50：rerun commands 不包含真实 dispatch/callback 材料路径。
# 设计约束 51：accepted_reasons 只是 decision 声明，不代表本 gate 验真。
# 设计约束 52：missing_materials 默认包含全部必需类，防止空输入误 ready。
# 设计约束 53：材料完整性只能来自白名单字段，不能解析自由文本。
# 设计约束 54：same_ref status 仅接受 matched/ready，其他状态都需复跑。
# 设计约束 55：decision package ready 必须是真布尔 true，字符串 true 不通过。
# 设计约束 56：source decision 非 ready 时进入材料 callback 或复跑路径。
# 设计约束 57：本 gate 不更新 OKR 或 sprint closeout，那是 Product 范围。
# 设计约束 58：本 gate 不更新 Robot/mobile 文件，那是并行 worker 范围。
# 设计约束 59：所有状态名使用 snake_case，便于 rg 和下游解析。
# 设计约束 60：所有 contract literal 与 tech-plan 保持一致。

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
    "baudrate",
    "baud_rate",
    "Traceback",
    "checksum",
    "complete artifact",
    "raw robot response",
)

HARDWARE_DETAIL_PATTERNS = (
    re.compile(r"(?i)\bserial\s*(port|device|log|transport)?\b"),
    re.compile(r"(?i)\bUART\b"),
    re.compile(r"(?i)\bWAVE\s+ROVER\b"),
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
    # forbidden copy 命中说明输入不适合进入 Robot/mobile 摘要。
    encoded = _encoded(value)
    return (
        any(token in encoded for token in FORBIDDEN_COPY)
        or any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)
        or any(pattern.search(encoded) for pattern in HARDWARE_DETAIL_PATTERNS)
    )


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
        return {}, "result_review_decision_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "result_review_decision_missing"
    except json.JSONDecodeError:
        return {}, "result_review_decision_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "result_review_decision_read_error"
    if not isinstance(payload, dict):
        return {}, "result_review_decision_not_object"
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
        "route_task_field_retest_result_review_decision",
        "route_task_field_retest_result_review_decision_summary",
        "route_task_field_retest_result_review_handoff",
        "route_task_field_retest_result_review_handoff_summary",
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
    # 优先选择 schema 命中的 decision 对象；否则保留顶层用于 unsupported 解释。
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
    # owner work order 只接受 list，避免字符串被当成结构化任务。
    if not isinstance(value, list):
        return []
    return _safe_value(value[:limit])


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


def _source_decision_status(source: dict[str, Any]) -> str:
    # decision_status 是上游主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    package = _dict(source, "result_review_decision_package")
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


def _same_ref_status(source: dict[str, Any]) -> dict[str, Any]:
    # same-evidence-ref 兼容 object 与字符串两种 summary 形态。
    safe_copy = _dict(source, "safe_copy")
    raw = source.get("same_evidence_ref_match", safe_copy.get("same_evidence_ref_match"))
    if isinstance(raw, dict):
        return _safe_value(raw)
    if isinstance(raw, str):
        return {"status": _safe_text(raw)}
    return {"status": "missing_evidence_ref"}


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止其它 gate JSON 混入。
    schema = str(source.get("schema", "")).strip()
    boundary = str(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    return schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY


def _same_ref_required_ok(source: dict[str, Any]) -> bool:
    # same_evidence_ref_required 必须是真布尔 true，弱类型字符串不能通过。
    return source.get("same_evidence_ref_required") is True


def _decision_package_ready(source: dict[str, Any]) -> bool:
    # ready 必须是真布尔值；字符串 true 不能提升为 handoff ready。
    package = _dict(source, "result_review_decision_package")
    safe_copy = _dict(source, "safe_copy")
    return package.get("ready") is True or safe_copy.get("result_acceptance_backfill_ready") is True


def _source_owner_handoff(source: dict[str, Any]) -> list[Any]:
    # owner handoff 可来自上游顶层或 safe_copy；这里只安全透传摘要。
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
    package = _dict(source, "rerun_package")
    for candidate in (source, package):
        items = _list_text(candidate.get("rerun_commands") or candidate.get("commands"))
        if items:
            return items
    return []


def _source_reasons(source: dict[str, Any], key: str) -> list[str]:
    # accepted/blocked/rerun reasons 兼容顶层、package 和 safe_copy。
    package = _dict(source, "result_review_decision_package")
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, package, safe_copy):
        items = _list_text(candidate.get(key))
        if items:
            return items
    return []


def _material_lists(source: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    # 材料字段只接受白名单结构；默认全部 missing，防止空输入误 ready。
    package = _dict(source, "result_review_decision_package")
    accepted = _list_text(source.get("accepted_materials") or package.get("accepted_materials"))
    rejected = _list_text(source.get("rejected_materials") or package.get("rejected_materials"))
    missing = _list_text(source.get("missing_materials") or package.get("missing_materials"))
    accepted_set = {item for item in accepted if item in REQUIRED_RESULT_MATERIALS}
    if not missing:
        missing = [item for item in REQUIRED_RESULT_MATERIALS if item not in accepted_set]
    return accepted, missing, rejected


def _handoff_status(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    decision_status: str,
    same_ref: dict[str, Any],
    package_ready: bool,
    missing_materials: list[str],
    rejected_materials: list[str],
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 owner callback ready。
    reasons: list[str] = []
    if load_issue:
        reasons.append(load_issue)
        return "blocked_missing_result_review_decision_not_proven", reasons
    if success_claim:
        return "unsupported_result_review_decision_schema_not_proven", ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "unsupported_result_review_decision_schema_not_proven", ["unsafe_copy_detected"]
    if not _schema_supported(source):
        return "unsupported_result_review_decision_schema_not_proven", ["unsupported_result_review_decision_schema_or_boundary"]
    if not _same_ref_required_ok(source):
        return "evidence_ref_mismatch_rerun_not_proven", ["same_evidence_ref_required_not_true"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun_not_proven", [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref.get("status") not in {"matched", "ready"}:
        return "evidence_ref_mismatch_rerun_not_proven", [f"same_evidence_ref:{same_ref.get('status', 'missing')}"]
    if not source_ref:
        return "evidence_ref_mismatch_rerun_not_proven", ["safe_evidence_ref_missing"]
    if decision_status == "ready_for_result_acceptance_backfill_not_proven" and package_ready and not missing_materials and not rejected_materials:
        return "ready_for_owner_result_callback_not_proven", []
    if decision_status == "needs_route_elevator_material_backfill_not_proven" or missing_materials or rejected_materials or not package_ready:
        return "needs_result_material_callback_not_proven", ["route_elevator_result_material_callback_required"]
    if decision_status in {
        "evidence_ref_mismatch_rerun_not_proven",
        "blocked_missing_result_review_intake_not_proven",
    }:
        return "evidence_ref_mismatch_rerun_not_proven", [f"source_decision_status:{decision_status}"]
    return "unsupported_result_review_decision_schema_not_proven", [f"unsupported_source_decision_status:{decision_status or 'missing'}"]


def _owner_work_orders(
    handoff_status: str,
    evidence_ref: str,
    missing_materials: list[str],
    upstream_handoff: list[Any],
) -> list[dict[str, Any]]:
    # owner work order 只描述人工补证/复跑责任，不给 Robot/mobile 控制指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == "ready_for_owner_result_callback_not_proven":
        action = "prepare_owner_result_callback_package_from_sanitized_review_decision"
    elif handoff_status == "needs_result_material_callback_not_proven":
        action = "collect_missing_route_elevator_result_materials_before_callback"
    elif handoff_status == "evidence_ref_mismatch_rerun_not_proven":
        action = "rerun_result_review_decision_with_same_evidence_ref"
    elif handoff_status == "blocked_missing_result_review_decision_not_proven":
        action = "provide_result_review_decision_artifact_or_summary"
    else:
        action = "regenerate_supported_result_review_decision_without_unsafe_copy"
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


def _same_evidence_ref_package(handoff_status: str, evidence_ref: str, same_ref: dict[str, Any]) -> dict[str, Any]:
    # same-ref package 固定给下游复账，不能作为现场通过依据。
    return {
        "required": True,
        "status": "matched" if handoff_status != "evidence_ref_mismatch_rerun_not_proven" else "rerun_required",
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "source_match": same_ref,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _callback_requirements(handoff_status: str, evidence_ref: str, missing_materials: list[str]) -> list[str]:
    # callback requirements 是 owner 补证 checklist，不读取真实材料。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == "ready_for_owner_result_callback_not_proven":
        return [f"Prepare owner result callback handoff for evidence_ref={ref} with sanitized decision summary."]
    needed = missing_materials or list(REQUIRED_RESULT_MATERIALS)
    return [f"Callback must provide {item} for evidence_ref={ref}." for item in needed]


def _rerun_commands(handoff_status: str, evidence_ref: str, upstream_commands: list[str]) -> list[str]:
    # rerun commands 使用占位路径，避免泄漏本机或真实材料路径。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = upstream_commands[:6] if upstream_commands else []
    commands.extend(
        [
            "python3 pc-tools/evidence/route_task_field_retest_result_review_decision.py "
            f"--result-review-intake-json <result_review_intake.json> --evidence-ref {ref} --once-json",
            "python3 pc-tools/evidence/route_task_field_retest_result_review_handoff.py "
            f"--result-review-decision-json <result_review_decision.json> --evidence-ref {ref} --once-json",
        ]
    )
    if handoff_status == "ready_for_owner_result_callback_not_proven":
        commands.append(
            "python3 pc-tools/evidence/route_task_field_retest_result_callback_intake.py "
            f"--result-review-handoff-json <result_review_handoff.json> --evidence-ref {ref} --once-json"
        )
    return commands


def _safe_copy(
    handoff_status: str,
    evidence_ref: str,
    owner_work_orders: list[dict[str, Any]],
    callback_requirements: list[str],
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料内容。
    return {
        "schema": f"{HANDOFF_SUMMARY_SCHEMA}.safe_copy",
        "handoff_status": handoff_status,
        "status": handoff_status,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "owner_work_orders": owner_work_orders,
        "next_material_callback_requirements": callback_requirements,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_result_review_handoff(
    result_review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 result review decision，生成 result review handoff artifact。"""
    payload, load_issue = _load_json(result_review_decision_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    decision_status = _source_decision_status(source) if source else ""
    same_ref = _same_ref_status(source) if source else {"status": "missing_evidence_ref"}
    package_ready = _decision_package_ready(source) if source else False
    upstream_handoff = _source_owner_handoff(source) if source else []
    upstream_next = _source_next_required(source) if source else []
    upstream_commands = _source_rerun_commands(source) if source else []
    accepted_materials, missing_materials, rejected_materials = _material_lists(source) if source else ([], list(REQUIRED_RESULT_MATERIALS), [])
    unsafe = bool(payload) and _has_forbidden_copy(source)
    success_claim = bool(payload) and _has_success_claim(source)
    handoff_status, status_reasons = _handoff_status(
        load_issue,
        source,
        requested_ref,
        source_ref,
        decision_status,
        same_ref,
        package_ready,
        missing_materials,
        rejected_materials,
        unsafe,
        success_claim,
    )
    accepted_reasons = _source_reasons(source, "accepted_reasons")
    blocked_reasons = status_reasons + _source_reasons(source, "blocked_reasons")
    rerun_reasons = _source_reasons(source, "rerun_reasons")
    owner_work_orders = _owner_work_orders(handoff_status, evidence_ref_out, missing_materials, upstream_handoff)
    same_ref_package = _same_evidence_ref_package(handoff_status, evidence_ref_out, same_ref)
    callback_requirements = _callback_requirements(handoff_status, evidence_ref_out, missing_materials)
    rerun_commands = _rerun_commands(handoff_status, evidence_ref_out, upstream_commands)
    next_required = upstream_next or callback_requirements
    safe_copy = _safe_copy(handoff_status, evidence_ref_out, owner_work_orders, callback_requirements)
    summary = {
        "schema": HANDOFF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": status_reasons,
        "source_decision_status": decision_status,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_package": same_ref_package,
        "owner_work_orders": owner_work_orders,
        "accepted_reasons": accepted_reasons,
        "blocked_reasons": blocked_reasons,
        "rerun_reasons": rerun_reasons,
        "accepted_materials": accepted_materials,
        "missing_materials": missing_materials,
        "rejected_materials": rejected_materials,
        "next_material_callback_requirements": callback_requirements,
        "rerun_commands": rerun_commands,
        "next_required_evidence": next_required,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This handoff is metadata-only and does not read field material directories.",
            "Keep not_proven, delivery_success=false, and primary_actions_enabled=false until real route/elevator result evidence exists.",
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
        "same_evidence_ref_package": same_ref_package,
        "source_result_review_decision": {
            "load_issue": load_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "decision_status": decision_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "owner_work_orders": owner_work_orders,
        "accepted_reasons": accepted_reasons,
        "blocked_reasons": blocked_reasons,
        "rerun_reasons": rerun_reasons,
        "accepted_materials": accepted_materials,
        "missing_materials": missing_materials,
        "rejected_materials": rejected_materials,
        "next_material_callback_requirements": callback_requirements,
        "rerun_commands": rerun_commands,
        "next_required_evidence": next_required,
        "safe_copy": safe_copy,
        "route_task_field_retest_result_review_handoff_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "raw_field_material_content",
            "ros_graph",
            "nav2_runtime",
            "fixed_route_runtime",
            "serial_uart",
            "wave_rover",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device",
            "robot_action",
            "result_callback_execution",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_success_claim(artifact) or _has_success_claim(summary):
        # 最终防线只拦截动作/成功声明；non_access_scope 名称不参与禁词降级。
        artifact["status"] = "unsupported_result_review_decision_schema_not_proven"
        artifact["handoff_status"] = "unsupported_result_review_decision_schema_not_proven"
        summary["status"] = "unsupported_result_review_decision_schema_not_proven"
        summary["handoff_status"] = "unsupported_result_review_decision_schema_not_proven"
        artifact["route_task_field_retest_result_review_handoff_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest result review handoff artifact")
    parser.add_argument("--result-review-decision-json", required=True, help="result review decision artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review handoff")
    parser.add_argument("--output", default="", help="optional handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print handoff artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_result_review_handoff(
        args.result_review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_result_review_handoff: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"result_review_handoff_summary_file: {_safe_ref(args.summary_output)}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
