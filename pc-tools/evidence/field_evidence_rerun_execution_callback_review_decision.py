#!/usr/bin/env python3
"""生成 field_evidence_rerun_execution_callback_review_decision 的 fail-closed PC gate。

该 gate 只读上一轮 `field_evidence_rerun_execution_callback_intake`
artifact、summary、Robot safe alias 或 wrapper/nested JSON，把现场执行回执
分类转成 canonical review-decision artifact。它不读取真实材料目录、不访问 ROS
graph、Nav2/fixed-route runtime、serial/UART、WAVE ROVER、真实电梯、外部云、
真实手机/browser，也不调度机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DECISION_SCHEMA = "trashbot.field_evidence_rerun_execution_callback_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_callback_review_decision_summary.v1"
SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate"

SOURCE_SCHEMAS = {
    "trashbot.field_evidence_rerun_execution_callback_intake.v1",
    "trashbot.field_evidence_rerun_execution_callback_intake_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_callback_intake_gate"
SOURCE_READY_STATUS = "ready_for_field_evidence_rerun_execution_callback_intake_not_proven"

REVIEW_DECISIONS = (
    "ready",
    "missing",
    "rejected",
    "blocked",
    "unsupported",
    "unsafe",
    "evidence_ref_mismatch",
    "source_not_ready",
)
MATERIAL_CLASSIFICATIONS = ("accepted", "missing", "rejected", "blocked")
VALID_CLASSIFICATIONS = set(MATERIAL_CLASSIFICATIONS)

DECISION_STATUSES = {
    "ready": "ready_for_field_evidence_rerun_execution_callback_review_decision_not_proven",
    "missing": "needs_field_evidence_rerun_execution_callback_material_backfill_not_proven",
    "rejected": "rejected_field_evidence_rerun_execution_callback_materials_not_proven",
    "blocked": "blocked_field_evidence_rerun_execution_callback_review_decision_not_proven",
    "unsupported": "blocked_unsupported_field_evidence_rerun_execution_callback_review_decision_source",
    "unsafe": "blocked_unsafe_field_evidence_rerun_execution_callback_review_decision_copy",
    "evidence_ref_mismatch": "evidence_ref_mismatch_field_evidence_rerun_execution_callback_review_decision_blocked",
    "source_not_ready": "blocked_field_evidence_rerun_execution_callback_intake_not_ready",
}

REQUIRED_MATERIAL_CATEGORIES = (
    "task_record",
    "nav2_fixed_route_runtime_log",
    "route_completion_signal",
    "elevator_door_state",
    "target_floor_confirmation",
    "human_assistance_record",
    "dropoff_completion",
    "cancel_completion",
    "delivery_result",
    "phone_browser_evidence",
)

NOT_PROVEN = (
    "real_field_evidence_rerun_execution",
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_field_task_record",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_record",
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
    "field_evidence_rerun_execution_callback_review_decision; "
    "software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate; "
    "review_decision; decision_reasons; owner_handoff; next_required_evidence; rerun_guidance; "
    "accepted; missing; rejected; blocked; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 位于 execution callback intake 之后，只复核上游 safe summary。
# 设计约束 02：review_decision 使用小枚举，方便 Robot/mobile 只读消费。
# 设计约束 03：status 使用长状态名，方便 sprint/rg 证据定位。
# 设计约束 04：ready 只表示回执分类可交接，不表示真实现场复跑。
# 设计约束 05：missing 表示材料仍需回填，不能进入真实完成口径。
# 设计约束 06：rejected 表示材料不合格，需要替换或修正。
# 设计约束 07：blocked 表示上游材料或 owner 状态仍被阻断。
# 设计约束 08：unsupported 表示输入 schema、boundary 或类别不符合契约。
# 设计约束 09：unsafe 表示输入携带敏感、控制或成功声明，必须 fail closed。
# 设计约束 10：evidence_ref_mismatch 是独立状态，避免被误解为材料缺失。
# 设计约束 11：source_not_ready 明确要求先修复 callback-intake，不跳级复核。
# 设计约束 12：summary 是 canonical 下游消费面，不复制 raw artifact。
# 设计约束 13：Robot safe alias 可从输入读取，但输出仍生成 canonical summary。
# 设计约束 14：same_evidence_ref_required 必须是真布尔 true，字符串 true 不合格。
# 设计约束 15：同一 safe evidence_ref 是本链路主键，CLI 与 source 不一致即阻断。
# 设计约束 16：十类 required categories 固定，缺类默认 missing。
# 设计约束 17：未知 category 直接 unsupported，防止契约外材料绕过复核。
# 设计约束 18：同一 category 不能出现在多个状态组。
# 设计约束 19：accepted 只是 metadata 通过，不是真实 route/elevator pass。
# 设计约束 20：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 21：source=software_proof 与 not_proven 必须保留到 artifact/summary。
# 设计约束 22：只扫描可能进入 safe summary 的字段，避免 non_access_scope 自误伤。
# 设计约束 23：raw path、credential、ROS topic、serial/UART/WAVE ROVER 全阻断。
# 设计约束 24：checksum、traceback、complete/raw artifact 不能进入 safe copy。
# 设计约束 25：success/control wording 命中后不能“清洗后 ready”。
# 设计约束 26：owner_handoff 只表达材料责任，不授权机器人控制。
# 设计约束 27：rerun_guidance 只给 PC operator 复跑命令，不访问 ROS graph。
# 设计约束 28：exit code 保持 0，让 blocked artifact 也能被 CI 保存。
# 设计约束 29：--once-json 支持自动化线程直接捕获 artifact。
# 设计约束 30：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 31：CLI dependency-free，便于 macOS PC 和 Docker/local 直接复跑。
# 设计约束 32：输出的 non_access_scope 显式声明未访问真实系统面。

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
    re.compile(r"(?i)\bfield\s+rerun\s+(success|succeeded|complete|completed|passed)\b"),
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
    # UTC 便于 Docker/local artifact 和现场 callback packet 统一排序审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，blocked 分支也不回显敏感原文。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 被误填成本机路径时只保留 basename，避免路径扩散到 UI。
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
    # 安全扫描使用稳定 JSON，覆盖 key 和 value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 危险 token 或 raw path 出现时直接 fail closed。
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
    # 缺输入、坏 JSON、非 object 都输出 fail-closed artifact，便于自动化留痕。
    if not path:
        return {}, "callback_intake_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "callback_intake_missing"
    except json.JSONDecodeError:
        return {}, "callback_intake_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "callback_intake_read_error"
    if not isinstance(payload, dict):
        return {}, "callback_intake_not_object"
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
    # wrapper/nested JSON 只递归白名单 key，避免 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_callback_intake",
        "field_evidence_rerun_execution_callback_intake_summary",
        "robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary",
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
    # summary 优先；artifact 也可直接消费，但必须符合 schema/boundary。
    candidates = _source_candidates(payload)
    for candidate in candidates:
        if str(candidate.get("schema", "")).strip() == "trashbot.field_evidence_rerun_execution_callback_intake_summary.v1":
            return candidate
    for candidate in candidates:
        if str(candidate.get("schema", "")).strip() == "trashbot.field_evidence_rerun_execution_callback_intake.v1":
            return candidate
    return payload


def _schema(source: dict[str, Any]) -> str:
    # schema 字段只用于契约判断和输出解释。
    return _safe_text(source.get("schema", "")).strip()


def _boundary(source: dict[str, Any]) -> str:
    # boundary 兼容 evidence_boundary / boundary 两种既有字段。
    return _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止旧 JSON 或其它 gate 混用。
    return _schema(source) in SOURCE_SCHEMAS and _boundary(source) == SOURCE_BOUNDARY


def _source_is_software_not_proven(source: dict[str, Any]) -> bool:
    # 上游必须明确 software_proof/not_proven，不能把真实通过口径塞进本 gate。
    encoded = _encoded(source)
    return source.get("source") == "software_proof" and "not_proven" in encoded


def _flags_ok(source: dict[str, Any]) -> bool:
    # 三个动作旗标必须显式保持关闭；缺字段按不合格处理。
    return (
        source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


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


def _source_status(source: dict[str, Any]) -> str:
    # callback_intake_status 是上游状态主键；缺失时不能默认 ready。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("callback_intake_status"),
            source.get("status"),
            safe_copy.get("callback_intake_status"),
            safe_copy.get("status"),
            default="",
        )
    ).strip()


def _same_ref_status(source: dict[str, Any]) -> str:
    # same-evidence-ref 状态兼容字符串字段；非 matched/ready 都保守 blocked。
    safe_copy = _dict(source, "safe_copy")
    value = _first_text(source.get("same_evidence_ref_status"), safe_copy.get("same_evidence_ref_status"), default="")
    return _safe_text(value or "missing_evidence_ref").strip()


def _list_text(value: Any, limit: int = 64) -> list[str]:
    # 下游摘要只接受扁平字符串列表，避免复制完整 raw object。
    if isinstance(value, list):
        return [_safe_text(item).strip() for item in value[:limit] if isinstance(item, (str, int, float, bool)) and _safe_text(item).strip()]
    if value in (None, ""):
        return []
    if isinstance(value, (str, int, float, bool)):
        return [_safe_text(value).strip()]
    return []


def _material_groups(source: dict[str, Any]) -> tuple[dict[str, list[str]], list[str]]:
    # 优先消费上游 material_groups，也兼容 accepted_materials 等扁平字段。
    groups = {classification: [] for classification in MATERIAL_CLASSIFICATIONS}
    raw_groups = source.get("material_groups")
    if isinstance(raw_groups, dict):
        for classification in MATERIAL_CLASSIFICATIONS:
            groups[classification].extend(_list_text(raw_groups.get(classification)))
    for classification in MATERIAL_CLASSIFICATIONS:
        groups[classification].extend(_list_text(source.get(f"{classification}_materials")))
    classifications = source.get("material_classifications")
    if isinstance(classifications, list):
        for item in classifications:
            if not isinstance(item, dict):
                continue
            category = _safe_text(_first_text(item.get("category"), item.get("material_category"), item.get("name"), default="")).strip()
            status = _safe_text(_first_text(item.get("classification"), item.get("status"), default="")).strip().lower()
            if category and status in VALID_CLASSIFICATIONS:
                groups[status].append(category)
    normalized: dict[str, list[str]] = {classification: [] for classification in MATERIAL_CLASSIFICATIONS}
    issues: list[str] = []
    seen: dict[str, str] = {}
    for classification in MATERIAL_CLASSIFICATIONS:
        for category in groups[classification]:
            if category not in REQUIRED_MATERIAL_CATEGORIES:
                issues.append(f"unsupported_material_category:{category}")
                continue
            if category in seen and seen[category] != classification:
                issues.append(f"material_category_in_multiple_groups:{category}")
                continue
            seen[category] = classification
            if category not in normalized[classification]:
                normalized[classification].append(category)
    for category in REQUIRED_MATERIAL_CATEGORIES:
        if category not in seen:
            normalized["missing"].append(category)
    return normalized, issues


def _material_counts(groups: dict[str, list[str]]) -> dict[str, int]:
    # counts 只统计固定枚举，便于下游面板不解析材料列表。
    return {classification: len(groups.get(classification, [])) for classification in MATERIAL_CLASSIFICATIONS}


def _copy_probe(source: dict[str, Any]) -> dict[str, Any]:
    # 只扫描可能进入 safe summary 的字段，避免 artifact non_access_scope 枚举触发误伤。
    return {
        "owner_handoff": source.get("owner_handoff"),
        "next_required_evidence": source.get("next_required_evidence"),
        "blocker_summary": source.get("blocker_summary"),
        "safe_copy": source.get("safe_copy"),
        "material_classifications": source.get("material_classifications"),
        "accepted_materials": source.get("accepted_materials"),
        "missing_materials": source.get("missing_materials"),
        "rejected_materials": source.get("rejected_materials"),
        "blocked_materials": source.get("blocked_materials"),
        "status_reasons": source.get("status_reasons"),
    }


def _review_decision(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_status: str,
    same_ref_status: str,
    groups: dict[str, list[str]],
    material_issues: list[str],
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 ready。
    if success_claim:
        return "unsafe", ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "unsafe", ["unsafe_copy_detected"]
    if load_issue or not _schema_supported(source):
        return "unsupported", [load_issue or "unsupported_execution_callback_intake_schema_or_boundary"]
    if not _source_is_software_not_proven(source):
        return "unsupported", ["source_not_software_proof_or_missing_not_proven"]
    if not _flags_ok(source):
        return "unsafe", ["source_action_flags_not_false"]
    if source.get("same_evidence_ref_required", True) is not True:
        return "evidence_ref_mismatch", ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return "evidence_ref_mismatch", ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch", [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref_status not in {"matched", "ready"}:
        return "evidence_ref_mismatch", [f"same_evidence_ref:{same_ref_status}"]
    if source_status != SOURCE_READY_STATUS:
        return "source_not_ready", [f"source_callback_intake_status:{source_status or 'missing'}"]
    if material_issues:
        return "unsupported", material_issues
    if groups["blocked"]:
        return "blocked", ["blocked_materials:" + ",".join(groups["blocked"])]
    if groups["rejected"]:
        return "rejected", ["rejected_materials:" + ",".join(groups["rejected"])]
    if groups["missing"]:
        return "missing", ["missing_materials:" + ",".join(groups["missing"])]
    return "ready", []


def _next_required_evidence(decision: str, evidence_ref: str, groups: dict[str, list[str]]) -> list[str]:
    # 下一步只列材料动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == "ready":
        return [
            f"Hand off sanitized execution callback review summary for evidence_ref={ref} to Robot/mobile read-only consumers.",
            "Keep the follow-up as software_proof until real field materials are independently reviewed.",
        ]
    if decision == "missing":
        return [f"Backfill missing execution callback material metadata for evidence_ref={ref}: " + ", ".join(groups["missing"][:10])]
    if decision == "rejected":
        return [f"Replace or correct rejected execution callback material metadata for evidence_ref={ref}: " + ", ".join(groups["rejected"][:10])]
    if decision == "blocked":
        return [f"Clear blocked execution callback material metadata for evidence_ref={ref}: " + ", ".join(groups["blocked"][:10])]
    if decision == "evidence_ref_mismatch":
        return [f"Regenerate execution callback intake and review decision with one safe evidence_ref={ref}."]
    if decision == "source_not_ready":
        return [f"Rerun execution callback intake after accepted material categories are present for evidence_ref={ref}."]
    if decision == "unsafe":
        return ["Remove raw paths, credentials, ROS topics, serial/UART, WAVE ROVER detail, checksums, control claims, and success claims before rerun."]
    return [f"Provide a supported field_evidence_rerun_execution_callback_intake summary for evidence_ref={ref}."]


def _owner_handoff(decision: str, evidence_ref: str, groups: dict[str, list[str]]) -> dict[str, Any]:
    # handoff 是责任摘要，不授权 Robot/mobile 控制面。
    return {
        "owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "handoff_status": f"{decision}_field_evidence_rerun_execution_callback_review_not_proven",
        "handoff_note": f"Review execution callback-intake material groups for evidence_ref={evidence_ref or '<same_evidence_ref>'}; keep Robot/mobile read-only.",
        "accepted_materials": groups["accepted"],
        "missing_materials": groups["missing"],
        "rejected_materials": groups["rejected"],
        "blocked_materials": groups["blocked"],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_guidance(evidence_ref: str) -> dict[str, str]:
    # command labels 只给 PC operator 复跑，不访问 ROS graph 或硬件。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "execution_callback_intake": (
            "python3 pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py "
            f"--execution-pack-json /tmp/field_evidence_rerun_execution_pack_summary.json --callback-packet-json /tmp/field_execution_callback_packet.json --evidence-ref {ref}"
        ),
        "execution_callback_review_decision": (
            "python3 pc-tools/evidence/field_evidence_rerun_execution_callback_review_decision.py "
            f"--callback-intake-json /tmp/field_evidence_rerun_execution_callback_intake_summary.json --evidence-ref {ref} --once-json"
        ),
    }


def _safe_copy(
    decision: str,
    status: str,
    evidence_ref: str,
    groups: dict[str, list[str]],
    source_status: str,
    same_ref_status: str,
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料正文。
    return {
        "schema": f"{DECISION_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": status,
        "review_decision": decision,
        "evidence_boundary": DECISION_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "source_callback_intake_status": source_status,
        "same_evidence_ref_status": same_ref_status,
        "material_counts": _material_counts(groups),
        "accepted_materials": groups["accepted"],
        "missing_materials": groups["missing"],
        "rejected_materials": groups["rejected"],
        "blocked_materials": groups["blocked"],
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_callback_review_decision(
    callback_intake_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 execution callback-intake summary，生成 metadata-only review decision artifact。"""
    payload, load_issue = _load_json(callback_intake_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    source_status = _source_status(source) if source else ""
    same_ref_status = _same_ref_status(source) if source else "missing_evidence_ref"
    groups, material_issues = _material_groups(source) if source else ({classification: [] for classification in MATERIAL_CLASSIFICATIONS}, [])
    copy_probe = _copy_probe(source) if source else {}
    unsafe = bool(payload) and _has_forbidden_copy(copy_probe)
    success_claim = bool(payload) and (_has_success_claim(copy_probe) or _has_success_claim(source))
    decision, decision_reasons = _review_decision(
        load_issue,
        source,
        requested_ref,
        source_ref,
        source_status,
        same_ref_status,
        groups,
        material_issues,
        unsafe,
        success_claim,
    )
    status = DECISION_STATUSES[decision]
    next_required = _next_required_evidence(decision, evidence_ref_out, groups)
    owner_handoff = _owner_handoff(decision, evidence_ref_out, groups)
    rerun_guidance = _rerun_guidance(evidence_ref_out)
    safe_copy = _safe_copy(decision, status, evidence_ref_out, groups, source_status, same_ref_status)
    blocker_summary = {
        "blocked": decision != "ready",
        "review_decision": decision,
        "status": status,
        "decision_reasons": decision_reasons,
        "missing_count": len(groups["missing"]),
        "rejected_count": len(groups["rejected"]),
        "blocked_count": len(groups["blocked"]),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = {
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": status,
        "review_decision": decision,
        "decision_reasons": decision_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_callback_intake_status": source_status,
        "source_callback_intake_schema": _schema(source) if source else "",
        "accepted_materials": groups["accepted"],
        "missing_materials": groups["missing"],
        "rejected_materials": groups["rejected"],
        "blocked_materials": groups["blocked"],
        "material_counts": _material_counts(groups),
        "required_material_categories": list(REQUIRED_MATERIAL_CATEGORIES),
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "rerun_guidance": rerun_guidance,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This review decision is metadata-only and does not read field material directories.",
            "Keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": DECISION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": status,
        "review_decision": decision,
        "decision_reasons": decision_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_callback_intake": {
            "load_issue": load_issue,
            "schema": _schema(source) if source else "",
            "evidence_boundary": _boundary(source) if source else "",
            "source_callback_intake_status": source_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "accepted_materials": groups["accepted"],
        "missing_materials": groups["missing"],
        "rejected_materials": groups["rejected"],
        "blocked_materials": groups["blocked"],
        "material_counts": _material_counts(groups),
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "rerun_guidance": rerun_guidance,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_callback_review_decision_summary": summary,
        "robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "raw_field_material_content",
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
            "elevator_runtime",
            "external_cloud",
            "oss_cdn",
            "db_queue",
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
    return _safe_value(artifact), _safe_value(summary), 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只打印 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 保持 dependency-free，便于 PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun execution callback review decision artifact")
    parser.add_argument("--callback-intake-json", required=True, help="execution callback intake artifact, summary, Robot safe alias, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review decision")
    parser.add_argument("--output", default="", help="optional review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_callback_review_decision(args.callback_intake_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_callback_review_decision: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_rerun_execution_callback_review_decision_summary_file: {_safe_ref(args.summary_output)}")
        print(f"execution_callback_review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
