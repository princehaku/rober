#!/usr/bin/env python3
"""生成 field_evidence_rerun_execution_callback_intake 的 fail-closed PC gate。

该 gate 只读上一轮 field_evidence_rerun_execution_pack artifact/summary，
以及现场 owner 回填的 execution callback packet。它把十类 required
field materials 归类为 accepted/missing/rejected/blocked，但不读取材料
目录、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、
外部云、真实手机/browser，也不执行或调度任何机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.field_evidence_rerun_execution_callback_intake.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_callback_intake_summary.v1"
PACKET_SCHEMA = "trashbot.field_evidence_rerun_execution_callback_packet.v1"
PACKET_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_callback_packet_summary.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_callback_intake_gate"

SOURCE_SCHEMAS = {
    "trashbot.field_evidence_rerun_execution_pack.v1",
    "trashbot.field_evidence_rerun_execution_pack_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_pack_gate"
SOURCE_READY_STATUS = "ready_for_field_evidence_rerun_execution_pack_not_proven"

CALLBACK_SCHEMAS = {"", PACKET_SCHEMA, PACKET_SUMMARY_SCHEMA}
CALLBACK_BOUNDARIES = {"", EVIDENCE_BOUNDARY, SOURCE_BOUNDARY}

READY_STATUS = "ready_for_field_evidence_rerun_execution_callback_intake_not_proven"
UNSUPPORTED_STATUS = "blocked_unsupported_field_evidence_rerun_execution_callback_intake_source"
UNSAFE_STATUS = "blocked_unsafe_field_evidence_rerun_execution_callback_intake_copy"
MISMATCH_STATUS = "evidence_ref_mismatch_field_evidence_rerun_execution_callback_intake_blocked"
MATERIAL_STATUS = "blocked_field_evidence_rerun_execution_callback_materials_not_ready"
SOURCE_NOT_READY_STATUS = "blocked_field_evidence_rerun_execution_pack_not_ready"

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

VALID_CLASSIFICATIONS = {"accepted", "missing", "rejected", "blocked"}

SOURCE_TEMPLATE_CATEGORY_ALIASES = {
    "field_task_record": {"task_record"},
    "real_field_task_record": {"task_record"},
    "nav2_fixed_route_runtime_log": {"nav2_fixed_route_runtime_log"},
    "real_nav2_fixed_route_runtime_log": {"nav2_fixed_route_runtime_log"},
    "route_completion_signal": {"route_completion_signal"},
    "real_route_completion_signal": {"route_completion_signal"},
    "elevator_door_floor_human_assist": {"elevator_door_state", "target_floor_confirmation", "human_assistance_record"},
    "elevator_context": {"elevator_door_state", "target_floor_confirmation", "human_assistance_record"},
    "dropoff_cancel_completion": {"dropoff_completion", "cancel_completion"},
    "terminal_completion": {"dropoff_completion", "cancel_completion"},
    "delivery_result": {"delivery_result"},
    "real_delivery_result": {"delivery_result"},
    "real_phone_browser_evidence": {"phone_browser_evidence"},
    "phone_browser_evidence": {"phone_browser_evidence"},
}

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
    "field_evidence_rerun_execution_callback_intake; "
    "software_proof_docker_field_evidence_rerun_execution_callback_intake_gate; "
    "field_evidence_rerun_execution_pack; accepted; missing; rejected; blocked; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 位于 execution pack 之后，只复账现场 owner 的回执 packet。
# 设计约束 02：ready 只表示回执材料分类齐全，不代表现场复跑或 route/elevator pass。
# 设计约束 03：source execution pack 必须是上一轮固定 schema 和 boundary。
# 设计约束 04：source execution pack 必须 ready；backfill pack 不能被本 gate 提升。
# 设计约束 05：callback packet 可无 schema，以兼容人工表单导出的简化 JSON。
# 设计约束 06：callback packet 若带 schema/boundary，必须落在本链路白名单。
# 设计约束 07：same evidence_ref 是材料链主键，CLI、source、packet 必须一致。
# 设计约束 08：same_evidence_ref_required 必须是真布尔 true，字符串 true 不合格。
# 设计约束 09：十类 required categories 固定，缺类默认 missing，不能静默省略。
# 设计约束 10：每类只能是 accepted、missing、rejected、blocked 四种状态。
# 设计约束 11：accepted 只是后续 review eligibility，不是真实完成或成功。
# 设计约束 12：missing 表示现场材料未补齐，后续必须继续催收。
# 设计约束 13：rejected 表示材料不合格，不能进入成功口径。
# 设计约束 14：blocked 表示材料仍受环境、权限或 owner 信息阻断。
# 设计约束 15：unknown category 直接 fail closed，避免新材料绕过契约。
# 设计约束 16：非法 classification 直接 fail closed，避免表单拼写造成误判。
# 设计约束 17：source template 可是上一轮 7 个模板组，本 gate 需映射为 10 个细分类。
# 设计约束 18：source 和 packet 都必须保留 source=software_proof/not_proven。
# 设计约束 19：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 20：raw path、credential、ROS topic、/cmd_vel、serial/UART/WAVE ROVER 全阻断。
# 设计约束 21：checksum、complete/raw artifact、traceback 都不能进入 safe summary。
# 设计约束 22：success/control wording 命中后直接 blocked_unsafe。
# 设计约束 23：summary 是 Robot/mobile 推荐消费面，不包含 raw source 或 packet。
# 设计约束 24：safe_copy 只放白名单字段，方便只读 UI/diagnostics 消费。
# 设计约束 25：owner_handoff 只表达材料归属，不授权机器人控制。
# 设计约束 26：next_required_evidence 从 missing/rejected/blocked 分类生成。
# 设计约束 27：accepted 全部齐全也必须保持 not_proven 和三个动作旗标 false。
# 设计约束 28：输出 exit code 保持 0，让 blocked artifact 可被 CI 保存。
# 设计约束 29：--once-json 支持自动化线程直接捕获 artifact。
# 设计约束 30：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 31：wrapper/nested JSON 只递归固定 key，不采信任意 raw payload。
# 设计约束 32：non_access_scope 显式列出本 gate 未访问的真实系统面。
# 设计约束 33：状态名带 not_proven 或 blocked，避免被下游误判为实测通过。
# 设计约束 34：缺输入、坏 JSON、非 object JSON 都生成 fail-closed artifact。
# 设计约束 35：evidence_ref 若被误填成本机路径，只保留 basename。
# 设计约束 36：material detail 仅保留 category/classification/reason/ref/source。
# 设计约束 37：final self-check 只看成功/动作声明，避免 not_proven 枚举自误伤。
# 设计约束 38：如果未来要读取真实材料，应新增独立 material review gate。
# 设计约束 39：如果未来要控制机器人，应走 Robot action contract 和真实授权。
# 设计约束 40：如果未来要证明手机/browser，应使用真实设备或外部浏览器证据。
# 设计约束 41：如果未来要提升 O5，应使用公网/4G/OSS/CDN/DB/queue 材料。

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
    # 自由文本先脱敏，blocked 分支也不回显敏感原文。
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


def _list_text(value: Any, limit: int = 24) -> list[str]:
    # 下游摘要只接受扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        return [_safe_text(item).strip() for item in value[:limit] if isinstance(item, (str, int, float, bool)) and _safe_text(item).strip()]
    if value in (None, ""):
        return []
    if isinstance(value, (str, int, float, bool)):
        return [_safe_text(value).strip()]
    return []


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 wrapper key，避免任意 raw payload 被当成可消费来源。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_pack",
        "field_evidence_rerun_execution_pack_summary",
        "field_evidence_rerun_execution_callback_packet",
        "field_evidence_rerun_execution_callback_packet_summary",
        "field_evidence_rerun_execution_callback_intake",
        "field_evidence_rerun_execution_callback_intake_summary",
        "robot_diagnostics_field_evidence_rerun_execution_pack_summary",
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


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # summary 优先，找不到时保留 artifact 或顶层用于 unsupported 解释。
    for schema in (
        "trashbot.field_evidence_rerun_execution_pack_summary.v1",
        "trashbot.field_evidence_rerun_execution_pack.v1",
    ):
        for candidate in _candidates(payload):
            if str(candidate.get("schema", "")).strip() == schema:
                return candidate
    return payload


def _find_callback(payload: dict[str, Any]) -> dict[str, Any]:
    # callback 可以是无 schema 表单，但必须至少包含材料状态或 evidence_ref。
    for candidate in _candidates(payload):
        schema = str(candidate.get("schema", "")).strip()
        if schema in CALLBACK_SCHEMAS and (
            "material_classifications" in candidate
            or "material_statuses" in candidate
            or "materials" in candidate
            or "accepted_materials" in candidate
            or "missing_materials" in candidate
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


def _source_supported(source: dict[str, Any]) -> bool:
    # source schema 和 boundary 必须双重匹配，防止错误 JSON 混入。
    return _schema(source) in SOURCE_SCHEMAS and _boundary(source) == SOURCE_BOUNDARY


def _callback_supported(callback: dict[str, Any]) -> bool:
    # callback 可无 boundary；若填写 boundary，必须属于本链路白名单。
    return _schema(callback) in CALLBACK_SCHEMAS and _boundary(callback) in CALLBACK_BOUNDARIES


def _ref(payload: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层、safe_copy、diagnostics 或 mobile summary 取。
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
            payload.get("execution_pack_status"),
            payload.get("callback_intake_status"),
            payload.get("status"),
            safe_copy.get("execution_pack_status"),
            safe_copy.get("status"),
            default="",
        )
    ).strip()


def _same_ref_status(payload: dict[str, Any]) -> str:
    # same-evidence-ref 状态兼容字符串字段；非 matched/ready 都保守阻断。
    safe_copy = _dict(payload, "safe_copy")
    return _safe_text(_first_text(payload.get("same_evidence_ref_status"), safe_copy.get("same_evidence_ref_status"), default="missing_evidence_ref")).strip()


def _source_is_software_not_proven(payload: dict[str, Any]) -> bool:
    # 上游和 callback 都必须明确 software_proof/not_proven 边界。
    encoded = _encoded(payload)
    return payload.get("source") == "software_proof" and "not_proven" in encoded


def _flags_ok(payload: dict[str, Any]) -> bool:
    # 三个动作旗标必须显式保持关闭；缺字段按不合格处理。
    return (
        payload.get("safe_to_control") is False
        and payload.get("delivery_success") is False
        and payload.get("primary_actions_enabled") is False
    )


def _same_ref_required_ok(*payloads: dict[str, Any]) -> bool:
    # 缺字段时默认要求 same ref；显式 false 或字符串 true 都不能通过。
    return all(payload.get("same_evidence_ref_required", True) is True for payload in payloads)


def _source_required_categories(source: dict[str, Any]) -> set[str]:
    # execution pack 的模板组需要映射成回执细分类，兼容上一轮 7 个模板。
    names: set[str] = set()
    templates = source.get("material_templates")
    if isinstance(templates, list):
        for item in templates:
            if isinstance(item, dict):
                raw_name = _safe_text(_first_text(item.get("material_category"), item.get("material_type"), item.get("name"), default="")).strip()
                if raw_name in REQUIRED_MATERIAL_CATEGORIES:
                    names.add(raw_name)
                names.update(SOURCE_TEMPLATE_CATEGORY_ALIASES.get(raw_name, set()))
    return names


def _material_entries(callback: dict[str, Any]) -> list[dict[str, Any]]:
    # 支持 dict/list/form-style groups，统一成 category/classification/reason。
    source = callback.get("material_classifications")
    if source is None:
        source = callback.get("material_statuses")
    if source is None:
        source = callback.get("materials")
    entries: list[dict[str, Any]] = []
    if isinstance(source, dict):
        for category, raw in source.items():
            if isinstance(raw, dict):
                classification = raw.get("classification", raw.get("status", raw.get("material_status", "")))
                reason = raw.get("reason", raw.get("note", raw.get("owner_note", "")))
            else:
                classification = raw
                reason = ""
            entries.append({"category": category, "classification": classification, "reason": reason})
    elif isinstance(source, list):
        for raw in source:
            if isinstance(raw, dict):
                entries.append(
                    {
                        "category": _first_text(raw.get("category"), raw.get("material_category"), raw.get("material_class"), raw.get("name"), default=""),
                        "classification": _first_text(raw.get("classification"), raw.get("status"), raw.get("material_status"), default=""),
                        "reason": _first_text(raw.get("reason"), raw.get("note"), raw.get("owner_note"), default=""),
                    }
                )
    for status in VALID_CLASSIFICATIONS:
        grouped = callback.get(f"{status}_materials")
        if isinstance(grouped, list):
            for item in grouped:
                category = item.get("category", item.get("material_category", item.get("name", ""))) if isinstance(item, dict) else item
                reason = item.get("reason", item.get("note", "")) if isinstance(item, dict) else ""
                entries.append({"category": category, "classification": status, "reason": reason})
    return entries


def _classify_materials(callback: dict[str, Any], evidence_ref: str) -> tuple[list[dict[str, Any]], list[str], dict[str, int], dict[str, list[str]]]:
    # 缺省类默认 missing；未知类或非法状态作为 parse issue 触发 blocked。
    results = {
        category: {
            "category": category,
            "classification": "missing",
            "reason": "execution_callback_packet_missing_material_category",
            "safe_evidence_ref": evidence_ref,
            "source": "execution_callback_packet",
            "not_proven": "not_proven",
        }
        for category in REQUIRED_MATERIAL_CATEGORIES
    }
    parse_issues: list[str] = []
    for entry in _material_entries(callback):
        category = _safe_text(entry.get("category", "")).strip()
        classification = _safe_text(entry.get("classification", "")).strip().lower()
        reason = _safe_text(entry.get("reason", "")).strip()
        if category not in results:
            parse_issues.append(f"unsupported_material_category:{category}")
            continue
        if classification not in VALID_CLASSIFICATIONS:
            parse_issues.append(f"unsupported_classification:{category}:{classification or '<empty>'}")
            continue
        results[category] = {
            "category": category,
            "classification": classification,
            "reason": reason or f"execution_callback_packet_marked_{classification}",
            "safe_evidence_ref": evidence_ref,
            "source": "execution_callback_packet",
            "not_proven": "not_proven",
        }
    ordered = [results[category] for category in REQUIRED_MATERIAL_CATEGORIES]
    counts = {status: 0 for status in sorted(VALID_CLASSIFICATIONS)}
    groups = {status: [] for status in sorted(VALID_CLASSIFICATIONS)}
    for item in ordered:
        classification = item["classification"]
        counts[classification] += 1
        groups[classification].append(item["category"])
    return ordered, parse_issues, counts, groups


def _next_required_evidence(classifications: list[dict[str, Any]], status: str, evidence_ref: str) -> list[str]:
    # 下一步只列证据动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    pending = [item["category"] for item in classifications if item["classification"] in {"missing", "rejected", "blocked"}]
    if pending:
        return [f"Backfill or repair {category} for evidence_ref={ref} before review." for category in pending]
    if status == READY_STATUS:
        return [f"Run callback review on accepted categories for evidence_ref={ref}; keep not_proven until real review and field evidence exist."]
    return [f"Provide supported execution pack and owner-safe callback packet for one evidence_ref={ref}."]


def _owner_handoff(status: str, evidence_ref: str, counts: dict[str, int]) -> dict[str, Any]:
    # owner_handoff 只表达人工材料归属，不授权 Robot/mobile 控制。
    return {
        "owner": "Autonomy Algorithm Engineer",
        "field_owner": "field_rerun_owner",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "action": "review_accepted_execution_callback_materials" if status == READY_STATUS else "repair_execution_callback_materials_before_review",
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "material_counts": counts,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(status: str, evidence_ref: str, counts: dict[str, int], groups: dict[str, list[str]], next_required: list[str]) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 source、packet 或完整材料正文。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": status,
        "callback_intake_status": status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "accepted_materials": groups["accepted"],
        "missing_materials": groups["missing"],
        "rejected_materials": groups["rejected"],
        "blocked_materials": groups["blocked"],
        "material_counts": counts,
        "next_required_evidence": next_required,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _copy_probe(source: dict[str, Any], callback: dict[str, Any]) -> dict[str, Any]:
    # 只扫描可能下放的字段，避免 artifact non_access_scope 枚举触发误伤。
    return {
        "source_owner_handoff": source.get("owner_handoff"),
        "source_next_required_evidence": source.get("next_required_evidence"),
        "source_backfill_instructions": source.get("backfill_instructions"),
        "source_blocker_summary": source.get("blocker_summary"),
        "source_safe_copy": source.get("safe_copy"),
        "callback_materials": callback.get("materials"),
        "callback_material_statuses": callback.get("material_statuses"),
        "callback_material_classifications": callback.get("material_classifications"),
        "callback_accepted_materials": callback.get("accepted_materials"),
        "callback_missing_materials": callback.get("missing_materials"),
        "callback_rejected_materials": callback.get("rejected_materials"),
        "callback_blocked_materials": callback.get("blocked_materials"),
        "callback_notes": callback.get("notes", callback.get("owner_notes")),
        "callback_safe_copy": callback.get("safe_copy"),
    }


def _intake_status(
    source_issue: str,
    callback_issue: str,
    source: dict[str, Any],
    callback: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    callback_ref: str,
    source_status: str,
    same_ref_status: str,
    unsafe: bool,
    success_claim: bool,
    parse_issues: list[str],
    counts: dict[str, int],
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入被后续材料分类覆盖。
    reasons: list[str] = []
    if source_issue:
        reasons.append(source_issue)
    if callback_issue:
        reasons.append(callback_issue)
    if success_claim:
        return UNSAFE_STATUS, reasons + ["success_or_primary_action_claim_detected"]
    if unsafe:
        return UNSAFE_STATUS, reasons + ["unsafe_copy_detected"]
    if source_issue or not _source_supported(source):
        return UNSUPPORTED_STATUS, reasons + ["unsupported_execution_pack_schema_or_boundary"]
    if callback_issue or not _callback_supported(callback):
        return UNSUPPORTED_STATUS, reasons + ["unsupported_or_missing_execution_callback_packet"]
    if not _source_is_software_not_proven(source) or not _source_is_software_not_proven(callback):
        return UNSUPPORTED_STATUS, reasons + ["source_or_packet_not_software_proof_or_missing_not_proven"]
    if not _flags_ok(source) or not _flags_ok(callback):
        return UNSAFE_STATUS, reasons + ["source_or_packet_action_flags_not_false"]
    if not _same_ref_required_ok(source, callback):
        return MISMATCH_STATUS, reasons + ["same_evidence_ref_required_not_true"]
    if not source_ref or not callback_ref:
        return MISMATCH_STATUS, reasons + ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref not in {source_ref, callback_ref}:
        return MISMATCH_STATUS, reasons + [f"requested_ref:{requested_ref}!={source_ref}|{callback_ref}"]
    if source_ref != callback_ref:
        return MISMATCH_STATUS, reasons + [f"source_ref:{source_ref}!=callback_ref:{callback_ref}"]
    if same_ref_status not in {"matched", "ready"}:
        return MISMATCH_STATUS, reasons + [f"same_evidence_ref:{same_ref_status}"]
    if source_status != SOURCE_READY_STATUS:
        return SOURCE_NOT_READY_STATUS, reasons + [f"source_execution_pack_status:{source_status or 'missing'}"]
    source_categories = _source_required_categories(source)
    if source_categories and not set(REQUIRED_MATERIAL_CATEGORIES).issubset(source_categories):
        return UNSUPPORTED_STATUS, reasons + ["execution_pack_missing_required_material_categories"]
    if parse_issues:
        return MATERIAL_STATUS, reasons + parse_issues
    if counts.get("missing", 0) or counts.get("rejected", 0) or counts.get("blocked", 0):
        return MATERIAL_STATUS, reasons + ["execution_callback_materials_missing_rejected_or_blocked"]
    return READY_STATUS, reasons


def build_field_evidence_rerun_execution_callback_intake(
    execution_pack_json: str,
    callback_packet_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 execution pack 和 owner callback packet，生成 metadata-only intake artifact。"""
    source_payload, source_issue = _load_json(execution_pack_json, "execution_pack_json")
    callback_payload, callback_issue = _load_json(callback_packet_json, "callback_packet_json")
    source = _find_source(source_payload) if source_payload else {}
    callback = _find_callback(callback_payload) if callback_payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _ref(source) if source else ""
    callback_ref = _ref(callback) if callback else ""
    evidence_ref_out = requested_ref or source_ref or callback_ref
    source_status = _status(source) if source else ""
    same_ref_status = _same_ref_status(source) if source else "missing_evidence_ref"
    classifications, parse_issues, counts, groups = _classify_materials(callback, evidence_ref_out) if callback else (
        [],
        [],
        {status: 0 for status in sorted(VALID_CLASSIFICATIONS)},
        {status: [] for status in sorted(VALID_CLASSIFICATIONS)},
    )
    copy_probe = _copy_probe(source, callback) if source or callback else {}
    unsafe = bool(source_payload or callback_payload) and _has_forbidden_copy(copy_probe)
    success_claim = bool(source_payload or callback_payload) and (_has_success_claim(copy_probe) or _has_success_claim(source) or _has_success_claim(callback))
    status, status_reasons = _intake_status(
        source_issue,
        callback_issue,
        source,
        callback,
        requested_ref,
        source_ref,
        callback_ref,
        source_status,
        same_ref_status,
        unsafe,
        success_claim,
        parse_issues,
        counts,
    )
    next_required_evidence = _next_required_evidence(classifications, status, evidence_ref_out)
    owner_handoff = _owner_handoff(status, evidence_ref_out, counts)
    safe_copy = _safe_copy(status, evidence_ref_out, counts, groups, next_required_evidence)
    same_ref_out = "matched" if source_ref and callback_ref and source_ref == callback_ref and (not requested_ref or requested_ref == source_ref) and same_ref_status in {"matched", "ready"} else "blocked_or_unverified"
    source_execution_pack = {
        "load_issue": source_issue,
        "schema": _schema(source) if source else "",
        "evidence_boundary": _boundary(source) if source else "",
        "source_execution_pack_status": source_status,
        "safe_evidence_ref": source_ref,
    }
    callback_packet = {
        "load_issue": callback_issue,
        "schema": _schema(callback) if callback else "",
        "evidence_boundary": _boundary(callback) if callback else "",
        "safe_evidence_ref": callback_ref,
    }
    blocker_summary = {
        "blocked": status != READY_STATUS,
        "callback_intake_status": status,
        "source_execution_pack_status": source_status,
        "same_evidence_ref_status": same_ref_out,
        "status_reasons": status_reasons,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
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
        "source_execution_pack_schema": source_execution_pack["schema"],
        "source_execution_pack_status": source_status,
        "callback_packet_schema": callback_packet["schema"],
        "callback_packet_status": status,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_out,
        "required_material_categories": list(REQUIRED_MATERIAL_CATEGORIES),
        "material_classifications": classifications,
        "accepted_materials": groups["accepted"],
        "missing_materials": groups["missing"],
        "rejected_materials": groups["rejected"],
        "blocked_materials": groups["blocked"],
        "material_counts": counts,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
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
        "same_evidence_ref_status": same_ref_out,
        "source_execution_pack": source_execution_pack,
        "callback_packet": callback_packet,
        "material_classifications": classifications,
        "accepted_materials": groups["accepted"],
        "missing_materials": groups["missing"],
        "rejected_materials": groups["rejected"],
        "blocked_materials": groups["blocked"],
        "material_counts": counts,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "blocker_summary": blocker_summary,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_callback_intake_summary": summary,
        "robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary": summary,
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
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_success_claim(artifact) or _has_success_claim(summary):
        # 最终防线只拦截动作/成功声明；敏感信息已在入口 fail closed。
        artifact["status"] = UNSAFE_STATUS
        artifact["callback_intake_status"] = UNSAFE_STATUS
        summary["status"] = UNSAFE_STATUS
        summary["callback_intake_status"] = UNSAFE_STATUS
        artifact["field_evidence_rerun_execution_callback_intake_summary"] = summary
        artifact["robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary"] = summary
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
    # CLI 保持 dependency-free，便于 PC、Docker 和 unittest 直接复跑。
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun execution callback intake artifact")
    parser.add_argument("--execution-pack-json", required=True, help="field_evidence_rerun_execution_pack artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--callback-packet-json", required=True, help="safe field-owner execution callback packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this callback intake")
    parser.add_argument("--output", default="", help="optional callback intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional callback intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print callback intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_callback_intake(
        args.execution_pack_json,
        args.callback_packet_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_callback_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_rerun_execution_callback_intake_summary_file: {_safe_ref(args.summary_output)}")
        print(f"callback_intake_status: {artifact['callback_intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
