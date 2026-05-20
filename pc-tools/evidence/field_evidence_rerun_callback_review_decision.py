#!/usr/bin/env python3
"""生成 field_evidence_rerun_callback_review_decision 的 fail-closed PC gate。

该 gate 只读上一轮 field_evidence_rerun_callback_intake artifact、summary
或 wrapper/nested JSON，把 accepted/missing/rejected/blocked material groups
转成下一步复核决策。它不读取真实材料目录、不访问 ROS graph、Nav2 runtime、
serial/UART、WAVE ROVER、外部云、真实手机/browser 或机器人动作接口。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DECISION_SCHEMA = "trashbot.field_evidence_rerun_callback_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_callback_review_decision_summary.v1"
SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_field_evidence_rerun_callback_review_decision_gate"

SOURCE_SCHEMAS = {
    "trashbot.field_evidence_rerun_callback_intake.v1",
    "trashbot.field_evidence_rerun_callback_intake_summary.v1",
}
SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_callback_intake_summary.v1"
SOURCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_callback_intake_gate"

REVIEW_DECISIONS = ("accepted", "missing", "rejected", "blocked")
VALID_CLASSIFICATIONS = set(REVIEW_DECISIONS)

REQUIRED_MATERIAL_CLASSES = (
    "real route completion signal",
    "real field task record",
    "real Nav2/fixed-route runtime log",
    "real elevator door summary",
    "real target floor / floor arrival summary",
    "real human-assistance summary",
    "real dropoff completion",
    "real cancel completion",
    "real delivery result",
    "real phone/browser evidence",
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
    "field_evidence_rerun_callback_review_decision; "
    "software_proof_docker_field_evidence_rerun_callback_review_decision_gate; "
    "review_decision; owner_handoff; next_required_evidence; rerun_guidance; "
    "accepted; missing; rejected; blocked; "
    "real route completion signal; real field task record; "
    "real Nav2/fixed-route runtime log; real phone/browser evidence; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只读 callback intake summary，不读取真实材料目录。
# 设计约束 02：artifact 输入必须带 nested summary；缺 summary 直接 blocked。
# 设计约束 03：review_decision 枚举只能是 accepted/missing/rejected/blocked。
# 设计约束 04：accepted 只表示回执材料组齐全，不是真实 field pass。
# 设计约束 05：missing 表示现场 owner 仍需回填同一 evidence_ref 材料。
# 设计约束 06：rejected 表示回执材料不合格，不能进入 result/delivery 口径。
# 设计约束 07：blocked 表示输入、主键、安全 copy 或上游状态不可用。
# 设计约束 08：same evidence_ref 是本链路主键，显式 ref 不一致必须 blocked。
# 设计约束 09：十类 material class 固定，避免只复核 happy path 材料。
# 设计约束 10：缺任一 material class 默认 missing，而不是静默 accepted。
# 设计约束 11：未知 material class 直接 blocked，避免契约外材料绕过评审。
# 设计约束 12：summary 是 Robot/mobile 推荐消费面，不复制完整 artifact。
# 设计约束 13：owner_handoff 只说明责任和下一步，不授权任何机器人动作。
# 设计约束 14：rerun_guidance 只给 PC operator 命令，不触发 ROS graph。
# 设计约束 15：unsafe copy 在脱敏前检查，命中后不能“清洗后 accepted”。
# 设计约束 16：raw path 阻断，避免本机文件路径进入 phone-safe summary。
# 设计约束 17：credential 阻断，保护 OSS、DB、queue、bearer 等密钥。
# 设计约束 18：ROS topic、/cmd_vel、serial/UART/WAVE ROVER 细节全部阻断。
# 设计约束 19：checksum、complete artifact、traceback 不是 safe review 字段。
# 设计约束 20：success/control wording 阻断，真实通过只能来自实测复核。
# 设计约束 21：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 22：source=software_proof 和 not_proven 必须保留到 artifact/summary。
# 设计约束 23：最终输出递归脱敏，blocked artifact 也不能泄漏输入。
# 设计约束 24：exit code 保持 0，让 blocked decision 也能作为证据落盘。
# 设计约束 25：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 26：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 27：safe_copy 只放白名单字段，方便 Robot/mobile 只读展示。
# 设计约束 28：non_access_scope 明确列出没有访问的系统面，便于评审。
# 设计约束 29：CLI 保持 output/summary-output/once-json 形态，方便自动化。
# 设计约束 30：本 gate 前进复账链路，不改变自主控制闭环状态机。

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
    # UTC 时间方便 Docker-only artifact 和现场材料按字符串排序。
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
    # 缺输入、坏 JSON、非 object 都输出 blocked decision，便于自动化留痕。
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
        "field_evidence_rerun_callback_intake",
        "field_evidence_rerun_callback_intake_summary",
        "field_evidence_rerun_callback_review_decision",
        "field_evidence_rerun_callback_review_decision_summary",
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


def _find_summary_source(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    # summary 是本 gate 的权威输入；artifact 只有嵌套 summary 时才可消费。
    candidates = _source_candidates(payload)
    for candidate in candidates:
        if str(candidate.get("schema", "")).strip() == SUMMARY_SCHEMA:
            return candidate, ""
    for candidate in candidates:
        if str(candidate.get("schema", "")).strip() == "trashbot.field_evidence_rerun_callback_intake.v1":
            return candidate, "callback_intake_summary_missing"
    return payload, "unsupported_callback_intake_schema"


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
    # callback_intake_status 是上游状态主键；缺失时不能默认 accepted。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("callback_intake_status"),
            source.get("status"),
            safe_copy.get("callback_intake_status"),
            safe_copy.get("status"),
            default="",
        )
    )


def _same_ref_status(source: dict[str, Any]) -> str:
    # same-evidence-ref 状态兼容字符串字段；非 matched 都保守 blocked。
    value = _first_text(
        source.get("same_evidence_ref_status"),
        _dict(source, "safe_copy").get("same_evidence_ref_status"),
        default="",
    )
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
    groups = {decision: [] for decision in REVIEW_DECISIONS}
    raw_groups = source.get("material_groups")
    if isinstance(raw_groups, dict):
        for decision in REVIEW_DECISIONS:
            groups[decision].extend(_list_text(raw_groups.get(decision)))
    aliases = {
        "accepted": "accepted_materials",
        "missing": "missing_materials",
        "rejected": "rejected_materials",
        "blocked": "blocked_materials",
    }
    for decision, key in aliases.items():
        groups[decision].extend(_list_text(source.get(key)))
    classifications = source.get("material_classifications")
    if isinstance(classifications, list):
        for item in classifications:
            if not isinstance(item, dict):
                continue
            material_class = _safe_text(_first_text(item.get("material_class"), item.get("material_group"), item.get("name"), default="")).strip()
            classification = _safe_text(_first_text(item.get("classification"), item.get("status"), default="")).strip().lower()
            if material_class and classification in VALID_CLASSIFICATIONS:
                groups[classification].append(material_class)
    normalized: dict[str, list[str]] = {}
    issues: list[str] = []
    seen: dict[str, str] = {}
    for decision in REVIEW_DECISIONS:
        normalized[decision] = []
        for material_class in groups[decision]:
            if material_class not in REQUIRED_MATERIAL_CLASSES:
                issues.append(f"unsupported_material_class:{material_class}")
                continue
            if material_class in seen and seen[material_class] != decision:
                issues.append(f"material_class_in_multiple_groups:{material_class}")
                continue
            seen[material_class] = decision
            if material_class not in normalized[decision]:
                normalized[decision].append(material_class)
    for material_class in REQUIRED_MATERIAL_CLASSES:
        if material_class not in seen:
            normalized["missing"].append(material_class)
    return normalized, issues


def _material_counts(groups: dict[str, list[str]]) -> dict[str, int]:
    # counts 只统计固定枚举，便于下游面板不解析材料列表。
    return {decision: len(groups.get(decision, [])) for decision in REVIEW_DECISIONS}


def _decision(
    load_issue: str,
    source_issue: str,
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
    # fail-closed 优先级固定，避免坏输入落入 accepted。
    if load_issue or source_issue or not _schema_supported(source):
        return "blocked", [load_issue or source_issue or "unsupported_callback_intake_schema_or_boundary"]
    if success_claim:
        return "blocked", ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked", ["unsafe_copy_detected"]
    if not _source_is_software_not_proven(source):
        return "blocked", ["source_not_software_proof_or_missing_not_proven"]
    if source.get("same_evidence_ref_required", True) is not True:
        return "blocked", ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return "blocked", ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref != source_ref:
        return "blocked", [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref_status not in {"matched", "ready"}:
        return "blocked", [f"same_evidence_ref:{same_ref_status}"]
    if material_issues:
        return "blocked", material_issues
    if source_status != "ready_for_field_evidence_rerun_callback_intake_not_proven":
        return "blocked", [f"source_callback_intake_status:{source_status or 'missing'}"]
    if groups["blocked"]:
        return "blocked", ["blocked_materials:" + ",".join(groups["blocked"])]
    if groups["rejected"]:
        return "rejected", ["rejected_materials:" + ",".join(groups["rejected"])]
    if groups["missing"]:
        return "missing", ["missing_materials:" + ",".join(groups["missing"])]
    return "accepted", []


def _next_required_evidence(decision: str, evidence_ref: str, groups: dict[str, list[str]]) -> list[str]:
    # 下一步只列材料动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == "accepted":
        return [
            f"Hand off sanitized callback review summary for evidence_ref={ref} to Product closeout.",
            "Keep the next result or field review as software_proof until real materials are independently reviewed.",
        ]
    if decision == "missing":
        return [f"Backfill missing callback material metadata for evidence_ref={ref}: " + ", ".join(groups["missing"][:10])]
    if decision == "rejected":
        return [f"Replace or correct rejected callback material metadata for evidence_ref={ref}: " + ", ".join(groups["rejected"][:10])]
    blocked_items = groups["blocked"] or list(REQUIRED_MATERIAL_CLASSES)
    return [f"Clear blocked callback material or source issues for evidence_ref={ref}: " + ", ".join(blocked_items[:10])]


def _owner_handoff(decision: str, evidence_ref: str, groups: dict[str, list[str]]) -> dict[str, Any]:
    # handoff 是责任摘要，不授权 Robot/mobile 控制面。
    return {
        "owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "handoff_status": f"{decision}_field_evidence_rerun_callback_review_not_proven",
        "handoff_note": f"Review callback-intake material groups for evidence_ref={evidence_ref or '<same_evidence_ref>'}; keep Robot/mobile read-only.",
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
        "callback_intake": (
            "python3 pc-tools/evidence/field_evidence_rerun_callback_intake.py "
            f"--dispatch-json /tmp/field_evidence_rerun_material_dispatch_summary.json --callback-json /tmp/field_callback_packet.json --evidence-ref {ref}"
        ),
        "review_decision": (
            "python3 pc-tools/evidence/field_evidence_rerun_callback_review_decision.py "
            f"--callback-intake-json /tmp/field_evidence_rerun_callback_intake_summary.json --evidence-ref {ref} --once-json"
        ),
    }


def _blocker_summary(decision: str, reasons: list[str], groups: dict[str, list[str]]) -> dict[str, Any]:
    # blocker summary 给 Product/Robot/mobile 看状态，不回显 raw input。
    return {
        "blocked": decision in {"missing", "rejected", "blocked"},
        "decision": decision,
        "status_reasons": reasons,
        "missing_count": len(groups["missing"]),
        "rejected_count": len(groups["rejected"]),
        "blocked_count": len(groups["blocked"]),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(decision: str, evidence_ref: str, groups: dict[str, list[str]], source_status: str, same_ref_status: str) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料内容。
    return {
        "schema": f"{DECISION_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "review_decision": decision,
        "status": decision,
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


def build_field_evidence_rerun_callback_review_decision(
    callback_intake_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 callback-intake summary，生成 metadata-only review decision artifact。"""
    payload, load_issue = _load_json(callback_intake_json)
    source, source_issue = _find_summary_source(payload) if payload else ({}, "")
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    source_status = _source_status(source) if source else ""
    same_ref_status = _same_ref_status(source) if source else "missing_evidence_ref"
    groups, material_issues = _material_groups(source) if source else ({decision: [] for decision in REVIEW_DECISIONS}, [])
    unsafe = bool(payload) and _has_forbidden_copy(payload)
    success_claim = bool(payload) and _has_success_claim(payload)
    decision, status_reasons = _decision(
        load_issue,
        source_issue,
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
    next_required = _next_required_evidence(decision, evidence_ref_out, groups)
    owner_handoff = _owner_handoff(decision, evidence_ref_out, groups)
    rerun_guidance = _rerun_guidance(evidence_ref_out)
    blocker_summary = _blocker_summary(decision, status_reasons, groups)
    safe_copy = _safe_copy(decision, evidence_ref_out, groups, source_status, same_ref_status)
    summary = {
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_callback_intake_status": source_status,
        "accepted_materials": groups["accepted"],
        "missing_materials": groups["missing"],
        "rejected_materials": groups["rejected"],
        "blocked_materials": groups["blocked"],
        "material_counts": _material_counts(groups),
        "required_material_classes": list(REQUIRED_MATERIAL_CLASSES),
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
        "status": decision,
        "review_decision": decision,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_callback_intake": {
            "load_issue": load_issue,
            "source_issue": source_issue,
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
        "field_evidence_rerun_callback_review_decision_summary": summary,
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
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun callback review decision artifact")
    parser.add_argument("--callback-intake-json", required=True, help="callback intake artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review decision")
    parser.add_argument("--output", default="", help="optional review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_callback_review_decision(args.callback_intake_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_callback_review_decision: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"callback_review_decision_summary_file: {_safe_ref(args.summary_output)}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
