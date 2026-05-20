#!/usr/bin/env python3
"""生成 field_evidence_rerun_callback_intake 的 fail-closed PC gate。

该 gate 只读上一轮 field_evidence_rerun_material_dispatch 摘要/产物和现场
owner 回执 packet，把十类真实材料的回填状态整理成 accepted/missing/rejected/
blocked 四类。它不读取材料目录、不解析 raw artifact、不访问 ROS graph、Nav2
runtime、serial/UART、WAVE ROVER、真实电梯、外部云或真实手机/browser。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.field_evidence_rerun_callback_intake.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_callback_intake_summary.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_callback_intake_gate"

DISPATCH_SCHEMAS = {
    "trashbot.field_evidence_rerun_material_dispatch.v1",
    "trashbot.field_evidence_rerun_material_dispatch_summary.v1",
}
DISPATCH_BOUNDARY = "software_proof_docker_field_evidence_rerun_material_dispatch_gate"

CALLBACK_SCHEMAS = {
    "",
    "trashbot.field_evidence_rerun_callback_packet.v1",
    "trashbot.field_evidence_rerun_callback_packet_summary.v1",
}
CALLBACK_BOUNDARIES = {"", EVIDENCE_BOUNDARY, DISPATCH_BOUNDARY}

READY_STATUS = "ready_for_field_evidence_rerun_callback_intake_not_proven"
UNSUPPORTED_STATUS = "blocked_unsupported_field_evidence_rerun_callback_intake_source"
UNSAFE_STATUS = "blocked_unsafe_field_evidence_rerun_callback_intake_copy"
MISMATCH_STATUS = "evidence_ref_mismatch_field_evidence_rerun_callback_intake_blocked"
MATERIAL_STATUS = "blocked_field_evidence_rerun_callback_materials_not_ready"

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

VALID_CLASSIFICATIONS = {"accepted", "missing", "rejected", "blocked"}

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
    "field_evidence_rerun_callback_intake; "
    "software_proof_docker_field_evidence_rerun_callback_intake_gate; "
    "accepted; missing; rejected; blocked; "
    "real route completion signal; real field task record; "
    "real Nav2/fixed-route runtime log; real phone/browser evidence; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 位于 material dispatch 之后，只接收 safe callback packet。
# 设计约束 02：dispatch 必须是上一轮 software-proof 派发产物，不能跳层消费 raw 材料。
# 设计约束 03：callback packet 允许无 schema，是为了兼容现场表单导出的简单 JSON。
# 设计约束 04：callback packet 仍必须只含白名单语义，不能塞完整 artifact。
# 设计约束 05：same evidence_ref 是材料链主键，CLI、dispatch、callback 必须一致。
# 设计约束 06：十类 required material classes 固定，避免现场只回传 happy path。
# 设计约束 07：每类只能是 accepted、missing、rejected、blocked 四种状态。
# 设计约束 08：accepted 只是 owner 回执状态，不是真实验收通过。
# 设计约束 09：missing 表示现场未补齐，后续必须继续补材料。
# 设计约束 10：rejected 表示材料回执不合格，不能进入成功口径。
# 设计约束 11：blocked 表示材料仍被环境、权限或 owner 信息阻断。
# 设计约束 12：缺任一 required class 默认 missing，不允许静默省略。
# 设计约束 13：unknown class 直接 fail closed，避免新材料绕过合同评审。
# 设计约束 14：unsafe copy 在脱敏前检查，命中后不能“清洗后 ready”。
# 设计约束 15：raw path 阻断，避免本机路径进入 Robot/mobile。
# 设计约束 16：credential 阻断，保护 OSS、DB、queue、bearer 等密钥。
# 设计约束 17：ROS topic、/cmd_vel、serial/UART/WAVE ROVER 细节全部阻断。
# 设计约束 18：checksum、complete artifact、traceback 不是 safe callback 字段。
# 设计约束 19：success/control wording 阻断，真实通过只能来自后续复核/实测。
# 设计约束 20：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 21：source=software_proof 和 not_proven 必须保留到 artifact/summary。
# 设计约束 22：summary 是 Robot/mobile 唯一推荐消费面，不包含 raw source。
# 设计约束 23：safe_copy 只含白名单字段，方便 UI 或 diagnostics 只读展示。
# 设计约束 24：next_required_evidence 从 missing/rejected/blocked 分类生成。
# 设计约束 25：accepted 全部齐全也只表示回执齐全，不表示 field pass。
# 设计约束 26：输出 exit code 保持 0，blocked artifact 可被 CI 保存为证据。
# 设计约束 27：--once-json 支持自动化线程直接捕获 artifact。
# 设计约束 28：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 29：本 gate 不导入 dispatch 模块，避免旧 gate 副作用影响独立 CLI。
# 设计约束 30：测试必须覆盖 ready、缺输入、坏 JSON、mismatch、unsafe、unknown class。
# 设计约束 31：文档必须说明本 gate 不是 result intake 或真实 field pass。
# 设计约束 32：后续如果需要打开真实材料，应新增独立 material review gate。
# 设计约束 33：后续如果要控制机器人，应走 Robot action contract 和真实授权。
# 设计约束 34：后续如果要证明手机/browser，应使用真实设备或外部浏览器证据。
# 设计约束 35：后续如果要提升 O5，应使用公网/4G/OSS/CDN/DB/queue 材料。

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
    # UTC 便于 Docker-only artifact 和后续现场材料按时间排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本先脱敏，blocked 输出也不能泄漏敏感材料。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 误填路径时只保留 basename，避免路径扩散到 UI。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线，不替代 fail-closed 判断。
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
    # 安全扫描使用稳定 JSON，同时覆盖 key 和 value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 危险 token 或 raw path 出现时直接 fail closed。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY) or any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_claim(value: Any) -> bool:
    # 布尔字段和自然语言同时检查，防止 callback 声称已成功或可控制。
    if isinstance(value, dict):
        if value.get("safe_to_control") is True or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都保守输出 blocked artifact。
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
    # artifact、summary、safe_copy 和 diagnostics 字段位置不同，取首个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 wrapper key，避免任意 raw payload 被当成可消费来源。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_material_dispatch",
        "field_evidence_rerun_material_dispatch_summary",
        "field_evidence_rerun_callback_packet",
        "field_evidence_rerun_callback_packet_summary",
        "field_evidence_rerun_callback_intake",
        "field_evidence_rerun_callback_intake_summary",
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
            candidates.extend(_candidates(value))
    return candidates


def _find_dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中的 dispatch 优先；否则保留顶层用于 unsupported 解释。
    for candidate in _candidates(payload):
        if str(candidate.get("schema", "")).strip() in DISPATCH_SCHEMAS:
            return candidate
    return payload


def _find_callback(payload: dict[str, Any]) -> dict[str, Any]:
    # callback 可以是无 schema 表单，但必须至少包含材料状态或 evidence_ref。
    for candidate in _candidates(payload):
        schema = str(candidate.get("schema", "")).strip()
        if schema in CALLBACK_SCHEMAS and (
            "material_classifications" in candidate
            or "materials" in candidate
            or "material_statuses" in candidate
            or "safe_evidence_ref" in candidate
            or "evidence_ref" in candidate
        ):
            return candidate
    return payload


def _schema(payload: dict[str, Any]) -> str:
    # schema 字段只用于契约判断和输出解释。
    return _safe_text(payload.get("schema", "")).strip()


def _boundary(payload: dict[str, Any]) -> str:
    # boundary 兼容 evidence_boundary / boundary 两种既有字段。
    return _safe_text(_first_text(payload.get("evidence_boundary"), payload.get("boundary"), default="")).strip()


def _dispatch_supported(dispatch: dict[str, Any]) -> bool:
    # dispatch schema 和 boundary 必须双重匹配，防止错误 JSON 混入。
    return _schema(dispatch) in DISPATCH_SCHEMAS and _boundary(dispatch) == DISPATCH_BOUNDARY


def _callback_supported(callback: dict[str, Any]) -> bool:
    # callback 可无 boundary；若填写 boundary，必须属于本链路白名单。
    return _schema(callback) in CALLBACK_SCHEMAS and _boundary(callback) in CALLBACK_BOUNDARIES


def _source_ref(payload: dict[str, Any]) -> str:
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
    # 状态字段只解释来源，不提升 proof 等级。
    safe_copy = _dict(payload, "safe_copy")
    return _safe_text(
        _first_text(
            payload.get("callback_intake_status"),
            payload.get("dispatch_status"),
            payload.get("status"),
            safe_copy.get("status"),
            default="",
        )
    )


def _source_is_software_not_proven(payload: dict[str, Any]) -> bool:
    # 上游和 callback 都必须明确 software_proof/not_proven 边界。
    encoded = _encoded(payload)
    return payload.get("source") == "software_proof" and "not_proven" in encoded


def _same_ref_required_ok(*payloads: dict[str, Any]) -> bool:
    # 缺字段时默认要求 same ref；显式 false 或字符串 true 都不能通过。
    return all(payload.get("same_evidence_ref_required", True) is True for payload in payloads)


def _dispatch_required_classes(dispatch: dict[str, Any]) -> set[str]:
    # dispatch 若输出 required groups，就必须覆盖本 gate 固定十类。
    groups = dispatch.get("required_material_groups")
    names: set[str] = set()
    if isinstance(groups, list):
        for item in groups:
            if isinstance(item, dict):
                names.add(_safe_text(_first_text(item.get("material_group"), item.get("material_class"), item.get("name"), default="")).strip())
            elif isinstance(item, str):
                names.add(_safe_text(item).strip())
    return names


def _material_entries(callback: dict[str, Any]) -> list[dict[str, Any]]:
    # 支持 dict 和 list 两种现场表单格式，但统一成 class/status/reason。
    source = callback.get("material_classifications")
    if source is None:
        source = callback.get("material_statuses")
    if source is None:
        source = callback.get("materials")
    entries: list[dict[str, Any]] = []
    if isinstance(source, dict):
        for material_class, raw in source.items():
            if isinstance(raw, dict):
                status = raw.get("classification", raw.get("status", raw.get("material_status", "")))
                reason = raw.get("reason", raw.get("note", raw.get("owner_note", "")))
            else:
                status = raw
                reason = ""
            entries.append({"material_class": material_class, "classification": status, "reason": reason})
    elif isinstance(source, list):
        for raw in source:
            if isinstance(raw, dict):
                entries.append(
                    {
                        "material_class": _first_text(raw.get("material_class"), raw.get("material_group"), raw.get("name"), default=""),
                        "classification": _first_text(raw.get("classification"), raw.get("status"), raw.get("material_status"), default=""),
                        "reason": _first_text(raw.get("reason"), raw.get("note"), raw.get("owner_note"), default=""),
                    }
                )
    return entries


def _classify_materials(callback: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], dict[str, int]]:
    # 缺省类默认 missing；未知类或非法状态作为 parse issue 触发 blocked。
    results = {
        material_class: {"material_class": material_class, "classification": "missing", "reason": "callback_packet_missing_material_class"}
        for material_class in REQUIRED_MATERIAL_CLASSES
    }
    parse_issues: list[str] = []
    for entry in _material_entries(callback):
        material_class = _safe_text(entry.get("material_class", "")).strip()
        classification = _safe_text(entry.get("classification", "")).strip().lower()
        reason = _safe_text(entry.get("reason", "")).strip()
        if material_class not in results:
            parse_issues.append(f"unsupported_material_class:{material_class}")
            continue
        if classification not in VALID_CLASSIFICATIONS:
            parse_issues.append(f"unsupported_classification:{material_class}:{classification or '<empty>'}")
            continue
        results[material_class] = {
            "material_class": material_class,
            "classification": classification,
            "reason": reason or f"callback_packet_marked_{classification}",
        }
    ordered = [results[material_class] for material_class in REQUIRED_MATERIAL_CLASSES]
    counts = {status: 0 for status in sorted(VALID_CLASSIFICATIONS)}
    for item in ordered:
        counts[item["classification"]] += 1
    return ordered, parse_issues, counts


def _group_materials(classifications: list[dict[str, Any]]) -> dict[str, list[str]]:
    # 下游 UI/diagnostics 只需要分类名称列表，不需要 raw packet。
    groups = {status: [] for status in sorted(VALID_CLASSIFICATIONS)}
    for item in classifications:
        groups[item["classification"]].append(item["material_class"])
    return groups


def _next_required_evidence(classifications: list[dict[str, Any]], status: str) -> list[str]:
    # ready 也保留 review 建议；非 ready 优先提示修 blocked 原因。
    next_items = [
        item["material_class"]
        for item in classifications
        if item["classification"] in {"missing", "rejected", "blocked"}
    ]
    if next_items:
        return next_items
    if status == READY_STATUS:
        return ["product_closeout_review_before_any_field_pass_or_result_claim"]
    return ["provide_supported_dispatch_and_safe_callback_packet_for_same_evidence_ref"]


def _intake_status(
    dispatch_issue: str,
    callback_issue: str,
    dispatch: dict[str, Any],
    callback: dict[str, Any],
    requested_ref: str,
    dispatch_ref: str,
    callback_ref: str,
    unsafe: bool,
    success_claim: bool,
    parse_issues: list[str],
    counts: dict[str, int],
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入被后续材料分类覆盖。
    if success_claim:
        return UNSAFE_STATUS, ["success_or_primary_action_claim_detected"]
    if unsafe:
        return UNSAFE_STATUS, ["unsafe_copy_detected"]
    if dispatch_issue:
        return UNSUPPORTED_STATUS, [dispatch_issue]
    if callback_issue:
        return UNSUPPORTED_STATUS, [callback_issue]
    if not _dispatch_supported(dispatch):
        return UNSUPPORTED_STATUS, ["unsupported_dispatch_schema_or_boundary"]
    if not _callback_supported(callback):
        return UNSUPPORTED_STATUS, ["unsupported_callback_schema_or_boundary"]
    if not _source_is_software_not_proven(dispatch) or not _source_is_software_not_proven(callback):
        return UNSUPPORTED_STATUS, ["source_not_software_proof_or_missing_not_proven"]
    if not _same_ref_required_ok(dispatch, callback):
        return MISMATCH_STATUS, ["same_evidence_ref_required_not_true"]
    if not dispatch_ref or not callback_ref:
        return MISMATCH_STATUS, ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref not in {dispatch_ref, callback_ref}:
        return MISMATCH_STATUS, [f"requested_ref:{requested_ref}!={dispatch_ref}|{callback_ref}"]
    if dispatch_ref != callback_ref:
        return MISMATCH_STATUS, [f"dispatch_ref:{dispatch_ref}!=callback_ref:{callback_ref}"]
    required_from_dispatch = _dispatch_required_classes(dispatch)
    if required_from_dispatch and not set(REQUIRED_MATERIAL_CLASSES).issubset(required_from_dispatch):
        return UNSUPPORTED_STATUS, ["dispatch_missing_required_material_classes"]
    if parse_issues:
        return MATERIAL_STATUS, parse_issues
    if counts.get("rejected", 0) or counts.get("blocked", 0) or counts.get("missing", 0):
        return MATERIAL_STATUS, ["callback_materials_missing_rejected_or_blocked"]
    return READY_STATUS, []


def _safe_copy(status: str, evidence_ref: str, counts: dict[str, int], groups: dict[str, list[str]]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 可复制面；不包含 dispatch 或 callback 原文。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": status,
        "callback_intake_status": status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "material_counts": counts,
        "material_groups": groups,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_callback_intake(
    dispatch_json: str,
    callback_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 dispatch 和 safe callback packet，生成 callback intake artifact。"""
    dispatch_payload, dispatch_issue = _load_json(dispatch_json, "dispatch_json")
    callback_payload, callback_issue = _load_json(callback_json, "callback_json")
    dispatch = _find_dispatch(dispatch_payload) if dispatch_payload else {}
    callback = _find_callback(callback_payload) if callback_payload else {}
    requested_ref = _safe_ref(evidence_ref)
    dispatch_ref = _source_ref(dispatch) if dispatch else ""
    callback_ref = _source_ref(callback) if callback else ""
    evidence_ref_out = requested_ref or dispatch_ref or callback_ref
    unsafe = (bool(dispatch_payload) and _has_forbidden_copy(dispatch_payload)) or (bool(callback_payload) and _has_forbidden_copy(callback_payload))
    success_claim = (bool(dispatch_payload) and _has_success_claim(dispatch_payload)) or (bool(callback_payload) and _has_success_claim(callback_payload))
    classifications, parse_issues, counts = _classify_materials(callback) if callback else ([], [], {status: 0 for status in sorted(VALID_CLASSIFICATIONS)})
    groups = _group_materials(classifications)
    status, status_reasons = _intake_status(
        dispatch_issue,
        callback_issue,
        dispatch,
        callback,
        requested_ref,
        dispatch_ref,
        callback_ref,
        unsafe,
        success_claim,
        parse_issues,
        counts,
    )
    next_required_evidence = _next_required_evidence(classifications, status)
    safe_copy = _safe_copy(status, evidence_ref_out, counts, groups)
    source_dispatch = {
        "schema": _schema(dispatch) if dispatch else "",
        "evidence_boundary": _boundary(dispatch) if dispatch else "",
        "status": _status(dispatch) if dispatch else "",
        "safe_evidence_ref": dispatch_ref,
    }
    source_callback = {
        "schema": _schema(callback) if callback else "",
        "evidence_boundary": _boundary(callback) if callback else "",
        "status": _status(callback) if callback else "",
        "safe_evidence_ref": callback_ref,
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "status": status,
        "callback_intake_status": status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": "matched" if dispatch_ref and dispatch_ref == callback_ref and (not requested_ref or requested_ref == dispatch_ref) else "blocked_or_unverified",
        "source_dispatch": source_dispatch,
        "source_callback": source_callback,
        "required_material_classes": list(REQUIRED_MATERIAL_CLASSES),
        "material_classifications": classifications,
        "accepted_materials": groups["accepted"],
        "missing_materials": groups["missing"],
        "rejected_materials": groups["rejected"],
        "blocked_materials": groups["blocked"],
        "material_counts": counts,
        "next_required_evidence": next_required_evidence,
        "safe_copy": safe_copy,
        "fail_closed_status": {
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "status": status,
        "callback_intake_status": status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "source_dispatch": source_dispatch,
        "source_callback": source_callback,
        "material_classifications": classifications,
        "material_counts": counts,
        "next_required_evidence": next_required_evidence,
        "safe_copy": safe_copy,
        "field_evidence_rerun_callback_intake_summary": summary,
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
    # CLI 保持 dependency-free，便于 PC、Docker 和 unittest 直接复跑。
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun callback intake artifact")
    parser.add_argument("--dispatch-json", required=True, help="field_evidence_rerun_material_dispatch artifact or summary JSON")
    parser.add_argument("--callback-json", required=True, help="safe field-owner callback packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this callback intake")
    parser.add_argument("--output", default="", help="optional callback intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional callback intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print callback intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_callback_intake(args.dispatch_json, args.callback_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_callback_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_rerun_callback_intake_summary_file: {_safe_ref(args.summary_output)}")
        print(f"callback_intake_status: {artifact['callback_intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
