#!/usr/bin/env python3
"""生成 field_evidence_rerun_material_dispatch 的 fail-closed PC gate。

该 gate 只读 route/elevator rerun review handoff、真实材料 followup/status
或兼容 summary，把现场复跑所需真实材料整理为 owner 可执行派发包。它不读取
材料目录、不解析 raw artifact、不访问 ROS graph、Nav2 runtime、serial/UART、
外部云、DB/queue、真实手机/browser，也不触发机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.field_evidence_rerun_material_dispatch.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_material_dispatch_summary.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_material_dispatch_gate"

# 只接受上游 software-proof/not_proven 安全摘要，避免把 raw 现场材料误当证明。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff.v1",
    "trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary.v1",
    "trashbot.real_material_followup_escalation_status.v1",
    "trashbot.real_material_followup_escalation_status_summary.v1",
    "trashbot.real_material_evidence_intake.v1",
    "trashbot.real_material_evidence_intake_summary.v1",
    "trashbot.real_material_manifest_template.v1",
    "trashbot.real_material_manifest_template_summary.v1",
}

SOURCE_BOUNDARIES = {
    "software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate",
    "software_proof_docker_real_material_followup_escalation_status_gate",
    "software_proof_docker_real_material_evidence_intake_gate",
    "software_proof_docker_real_material_manifest_template_gate",
}

READY_STATUS = "ready_for_field_evidence_rerun_material_dispatch_not_proven"
UNSUPPORTED_STATUS = "blocked_unsupported_field_evidence_rerun_material_dispatch_source"
UNSAFE_STATUS = "blocked_unsafe_field_evidence_rerun_material_dispatch_copy"
MISMATCH_STATUS = "evidence_ref_mismatch_field_evidence_rerun_material_dispatch_blocked"

# required material groups 使用 tech-plan 中的现场 owner 可读名称。
REQUIRED_MATERIAL_GROUPS = (
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

# rg 围栏依赖这些 literal，人工审计也能快速确认 fail-closed 边界。
BOUNDARY_NOTE = (
    "field_evidence_rerun_material_dispatch; "
    "software_proof_docker_field_evidence_rerun_material_dispatch_gate; "
    "real route completion signal; real field task record; "
    "real Nav2/fixed-route runtime log; real phone/browser evidence; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只做材料派发，不证明真实现场结果。
# 设计约束 02：source 必须是 software_proof，且包含 not_proven 语义。
# 设计约束 03：schema/boundary 双重白名单，防止其它 JSON 混入。
# 设计约束 04：safe evidence_ref 是派发包主键，不能被 CLI 静默改写。
# 设计约束 05：required material groups 固定为现场 owner 可执行清单。
# 设计约束 06：owner work orders 只写人工动作，不给 Robot 控制动作。
# 设计约束 07：rerun commands 使用占位路径，避免泄漏本机路径。
# 设计约束 08：callback packet requirements 只描述字段要求，不收 raw artifact。
# 设计约束 09：safe_copy 是下游唯一可复制面，不能包含完整 artifact。
# 设计约束 10：unsafe copy、raw path、credential、ROS topic 必须 blocked。
# 设计约束 11：serial/UART/WAVE ROVER 细节属于硬件事实，不在本 gate 透出。
# 设计约束 12：checksum 和完整 artifact 文案不允许进入派发包。
# 设计约束 13：success/control claim 直接 fail closed。
# 设计约束 14：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 15：wrapper/nested JSON 只递归白名单 key，避免采信 raw payload。
# 设计约束 16：blocked 输出也必须脱敏，便于 CI artifact 留档。
# 设计约束 17：缺输入、坏 JSON 和非 object JSON 均输出 unsupported 状态。
# 设计约束 18：real-material summary 只能作为派发线索，不作为材料已真证明。
# 设计约束 19：route/elevator handoff ready 也只代表上游 metadata ready。
# 设计约束 20：该 gate 不更新 OKR，不声明 PR #5 resolved。
# 设计约束 21：Robot 和 mobile 由并行 worker 只读消费 summary。
# 设计约束 22：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 23：输出字段优先扁平化，方便 Robot/mobile safe alias 消费。
# 设计约束 24：source_status 仅用于解释派发来源，不提升 proof 等级。
# 设计约束 25：not_proven 明确覆盖 phone/browser、HIL、O5 external proof。

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
    # UTC 时间便于 Docker-only 主机和后续 sprint artifact 对齐。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本必须先脱敏，避免 blocked artifact 反向泄漏敏感信息。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 误填路径时只保留 basename，防止本机路径进入下游 UI。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线，覆盖新增嵌套字段。
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
    # 命中 forbidden copy 表示输入不适合被派发到现场 owner。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY) or any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_claim(value: Any) -> bool:
    # 布尔字段和文案都检查，避免 true/control claim 穿透。
    if isinstance(value, dict):
        if value.get("safe_to_control") is True or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都保守落入 unsupported，CLI exit 仍可留档。
    if not path:
        return {}, "field_evidence_source_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "field_evidence_source_missing"
    except json.JSONDecodeError:
        return {}, "field_evidence_source_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "field_evidence_source_read_error"
    if not isinstance(payload, dict):
        return {}, "field_evidence_source_not_object"
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


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_material_dispatch",
        "field_evidence_rerun_material_dispatch_summary",
        "route_task_field_retest_acceptance_execution_rerun_result_review_handoff",
        "route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary",
        "real_material_followup_escalation_status",
        "real_material_followup_escalation_status_summary",
        "real_material_evidence_intake",
        "real_material_evidence_intake_summary",
        "real_material_manifest_template",
        "real_material_manifest_template_summary",
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
    # 优先选择 schema 命中的 source 对象；否则保留顶层用于 unsupported 解释。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _list_text(value: Any, limit: int = 48) -> list[str]:
    # summary 只输出扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                label = _first_text(item.get("material_group"), item.get("material"), item.get("name"), item.get("id"), item.get("action"))
                if label:
                    items.append(_safe_text(label))
            elif isinstance(item, (str, int, float, bool)):
                items.append(_safe_text(item))
        return items
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _source_schema(source: dict[str, Any]) -> str:
    # schema 单独抽取，便于 artifact 解释 blocked 原因。
    return _safe_text(source.get("schema", "")).strip()


def _source_boundary(source: dict[str, Any]) -> str:
    # boundary 兼容 evidence_boundary / boundary 两种既有字段。
    return _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 必须同时在白名单内。
    return _source_schema(source) in SOURCE_SCHEMAS and _source_boundary(source) in SOURCE_BOUNDARIES


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层、diagnostics、mobile 或 safe_copy 取。
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


def _source_status(source: dict[str, Any]) -> str:
    # 不同上游使用 status/handoff_status/intake/status 字段；这里只做解释。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("dispatch_status"),
            source.get("handoff_status"),
            source.get("real_material_followup_escalation_status"),
            source.get("real_material_evidence_intake"),
            source.get("status"),
            safe_copy.get("status"),
            default="",
        )
    )


def _source_is_software_not_proven(source: dict[str, Any]) -> bool:
    # source 必须明确是 software_proof，且带 not_proven 防止 proof 等级漂移。
    encoded = _encoded(source)
    return source.get("source") == "software_proof" and "not_proven" in encoded


def _same_ref_required_ok(source: dict[str, Any]) -> bool:
    # 缺字段时默认要求 same ref；若上游显式 false，必须 blocked。
    return source.get("same_evidence_ref_required", True) is True


def _source_rerun_commands(source: dict[str, Any]) -> list[str]:
    # 上游命令只作为线索；unsafe 输入会在前面 fail closed。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        items = _list_text(candidate.get("rerun_commands") or candidate.get("commands"))
        if items:
            return items[:6]
    return []


def _dispatch_status(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 dispatch ready。
    if success_claim:
        return UNSAFE_STATUS, ["success_or_primary_action_claim_detected"]
    if unsafe:
        return UNSAFE_STATUS, ["unsafe_copy_detected"]
    if load_issue:
        return UNSUPPORTED_STATUS, [load_issue]
    if not _schema_supported(source):
        return UNSUPPORTED_STATUS, ["unsupported_source_schema_or_boundary"]
    if not _source_is_software_not_proven(source):
        return UNSUPPORTED_STATUS, ["source_not_software_proof_or_missing_not_proven"]
    if not _same_ref_required_ok(source):
        return MISMATCH_STATUS, ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return MISMATCH_STATUS, ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref != source_ref:
        return MISMATCH_STATUS, [f"requested_ref:{requested_ref}!={source_ref}"]
    return READY_STATUS, []


def _required_material_groups() -> list[dict[str, Any]]:
    # 每组都要求真实现场材料；gate 只生成采集要求，不验真。
    return [
        {
            "material_group": group,
            "required": True,
            "collection_status": "required_from_field_owner_not_proven",
            "same_evidence_ref_required": True,
            "accepted_placeholder": False,
        }
        for group in REQUIRED_MATERIAL_GROUPS
    ]


def _owner_work_orders(evidence_ref: str) -> list[dict[str, Any]]:
    # work orders 按 owner 拆分，避免一个人漏补手机或 Robot 侧证据。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        {
            "owner": "Autonomy Algorithm Engineer",
            "work_order": "collect_route_and_elevator_rerun_materials",
            "safe_evidence_ref": ref,
            "required_material_groups": list(REQUIRED_MATERIAL_GROUPS[:6]),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        {
            "owner": "Robot Platform Engineer",
            "work_order": "provide_readonly_task_record_dropoff_cancel_delivery_result_materials",
            "safe_evidence_ref": ref,
            "required_material_groups": list(REQUIRED_MATERIAL_GROUPS[1:2] + REQUIRED_MATERIAL_GROUPS[6:9]),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        {
            "owner": "User Touchpoint Full-Stack Engineer",
            "work_order": "provide_real_phone_browser_evidence_for_same_evidence_ref",
            "safe_evidence_ref": ref,
            "required_material_groups": [REQUIRED_MATERIAL_GROUPS[9]],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
    ]


def _rerun_commands(evidence_ref: str, upstream_commands: list[str]) -> list[str]:
    # commands 使用占位输入，告诉现场 owner 怎么复跑链路而不暴露本机路径。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = list(upstream_commands[:4])
    commands.extend(
        [
            "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_intake.py "
            f"--rerun-queue-json <rerun_queue_summary.json> --rerun-result-json <field_rerun_result_packet.json> --evidence-ref {ref} --once-json",
            "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py "
            f"--rerun-result-intake-json <rerun_result_intake.json> --evidence-ref {ref} --once-json",
            "python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py "
            f"--rerun-result-review-decision-json <rerun_result_review_decision.json> --evidence-ref {ref} --once-json",
            "python3 pc-tools/evidence/field_evidence_rerun_material_dispatch.py "
            f"--source-json <supported_review_handoff_or_real_material_summary.json> --evidence-ref {ref} --once-json",
        ]
    )
    return commands


def _callback_packet_requirements(evidence_ref: str) -> dict[str, Any]:
    # callback packet 只描述白名单字段，禁止 raw artifact / checksum / path。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "schema_hint": "trashbot.field_evidence_rerun_callback_packet.v1",
        "safe_evidence_ref": ref,
        "same_evidence_ref_required": True,
        "required_material_groups": list(REQUIRED_MATERIAL_GROUPS),
        "forbidden_fields": [
            "raw_artifact",
            "complete_artifact",
            "local_path",
            "checksum",
            "credential",
            "ros_topic",
            "serial_uart_wave_rover_detail",
            "success_or_control_claim",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(dispatch_status: str, evidence_ref: str, source_status: str) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 可复制面；不包含 source payload 或完整 artifact。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": dispatch_status,
        "dispatch_status": dispatch_status,
        "source_status": source_status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "required_material_groups": list(REQUIRED_MATERIAL_GROUPS),
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_material_dispatch(source_json: str, evidence_ref: str = "") -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 supported source summary，生成现场复跑材料派发 artifact。"""
    payload, load_issue = _load_json(source_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    source_status = _source_status(source) if source else ""
    upstream_commands = _source_rerun_commands(source) if source else []
    unsafe = bool(payload) and _has_forbidden_copy(payload)
    success_claim = bool(payload) and _has_success_claim(payload)
    dispatch_status, status_reasons = _dispatch_status(load_issue, source, requested_ref, source_ref, unsafe, success_claim)
    required_groups = _required_material_groups()
    owner_orders = _owner_work_orders(evidence_ref_out)
    commands = _rerun_commands(evidence_ref_out, upstream_commands)
    callback_requirements = _callback_packet_requirements(evidence_ref_out)
    safe_copy = _safe_copy(dispatch_status, evidence_ref_out, source_status)
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "status": dispatch_status,
        "dispatch_status": dispatch_status,
        "status_reasons": status_reasons,
        "source_schema": _source_schema(source) if source else "",
        "source_boundary": _source_boundary(source) if source else "",
        "source_status": source_status,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "required_material_groups": required_groups,
        "owner_work_orders": owner_orders,
        "rerun_commands": commands,
        "callback_packet_requirements": callback_requirements,
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
        "status": dispatch_status,
        "dispatch_status": dispatch_status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "source_field_evidence_summary": {
            "load_issue": load_issue,
            "schema": _source_schema(source) if source else "",
            "evidence_boundary": _source_boundary(source) if source else "",
            "source_status": source_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "required_material_groups": required_groups,
        "owner_work_orders": owner_orders,
        "rerun_commands": commands,
        "callback_packet_requirements": callback_requirements,
        "safe_copy": safe_copy,
        "field_evidence_rerun_material_dispatch_summary": summary,
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
            "pr_5_resolution",
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
    # CLI dependency-free，便于 PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun material dispatch artifact")
    parser.add_argument("--source-json", required=True, help="supported review handoff, real-material status, or compatible summary JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this material dispatch")
    parser.add_argument("--output", default="", help="optional dispatch artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional dispatch summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print dispatch artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_material_dispatch(args.source_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_material_dispatch: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_rerun_material_dispatch_summary_file: {_safe_ref(args.summary_output)}")
        print(f"dispatch_status: {artifact['dispatch_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
