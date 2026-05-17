#!/usr/bin/env python3
"""生成 route/task field retest material callback packet artifact。

该 dependency-free PC gate 只消费上一轮
route_task_field_retest_material_pack 的 artifact、summary、wrapper 或
nested diagnostics，把 callback skeleton 转成现场 owner 可填写、可回传、
可复核的安全 packet。它不读取材料目录，不访问 ROS graph、Nav2 runtime、
fixed-route runtime、serial/UART、WAVE ROVER、外部云、4G、OSS/CDN、DB/queue
或真实手机/browser，也不触发任何机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# callback packet 是 material pack 后的表单化回执契约，不能跨 family 消费。
PACKET_SCHEMA = "trashbot.route_task_field_retest_material_callback_packet.v1"
PACKET_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_material_callback_packet_summary.v1"
SCHEMA_VERSION = 1
PACKET_BOUNDARY = "software_proof_docker_route_task_field_retest_material_callback_packet_gate"

# 源头只允许上一轮 material pack artifact/summary，避免绕过材料包 skeleton。
SOURCE_PACK_SCHEMA = "trashbot.route_task_field_retest_material_pack.v1"
SOURCE_PACK_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_material_pack_summary.v1"
SOURCE_SCHEMAS = {SOURCE_PACK_SCHEMA, SOURCE_PACK_SUMMARY_SCHEMA}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_material_pack_gate"

# handoff-mode material pack 的固定现场材料清单；source 缺清单时用它 fail-safe。
FIELD_CALLBACK_MATERIALS = (
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

# material-dir 旧模式的八类材料仍可被 summary 包装成回执项。
LEGACY_RESULT_MATERIALS = (
    "nav2_or_fixed_route_runtime_log",
    "route_completion_signal",
    "task_record",
    "door_state",
    "target_floor_confirmation",
    "human_assistance_note",
    "dropoff_or_cancel_completion",
    "delivery_result",
)

# not_proven 明确本 gate 的负边界，避免 packet 被误读成现场通过。
NOT_PROVEN = (
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime",
    "real_route_completion_signal",
    "real_task_record_or_completion_signal",
    "real_dropoff_or_cancel_completion",
    "real_delivery_success",
    "real_hil_pass",
    "real_wave_rover_uart_or_serial_feedback",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# rg 围栏依赖这些 literal，人工复盘也能快速确认证据边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_material_callback_packet; "
    "software_proof_docker_route_task_field_retest_material_callback_packet_gate; "
    "trashbot.route_task_field_retest_material_callback_packet.v1; "
    "trashbot.route_task_field_retest_material_callback_packet_summary.v1; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只消费 material pack，不消费 raw material dir。
# 设计约束 02：callback packet 是可填写回执，不代表 field pass。
# 设计约束 03：ready 状态仍保持 not_proven，不改变 Robot/mobile action。
# 设计约束 04：schema 和 boundary 必须同时命中 source family。
# 设计约束 05：safe_evidence_ref 是证据主键，弱值或路径必须 fail closed。
# 设计约束 06：same_evidence_ref_required 必须是真布尔 true。
# 设计约束 07：source delivery_success/primary_actions_enabled 只能为 false。
# 设计约束 08：raw path、credential、DB/queue/OSS token 和 success claim 必须拒绝。
# 设计约束 09：field_callback_items 只列白名单材料类，不复制材料正文。
# 设计约束 10：owner_acknowledgement 是表单模板，不是 ACK 或控制命令。
# 设计约束 11：summary 是 Robot/mobile 首选消费面，只输出安全摘要。
# 设计约束 12：wrapper/nested 递归只走固定 key，避免 arbitrary JSON 被采信。
# 设计约束 13：rerun commands 只给 PC evidence gate，不包含硬件/ROS/云命令。
# 设计约束 14：safe_copy 不含完整 source、raw artifact 或材料路径。
# 设计约束 15：输出再次脱敏，blocked artifact 也不能泄漏敏感输入。
# 设计约束 16：exit code 保持 0，让 blocked packet 也能进入 sprint 证据。
# 设计约束 17：所有状态名保留 not_proven，方便下游 fail closed。
# 设计约束 18：本 gate 不更新 OKR 或 sprint closeout，那是 Product 范围。
# 设计约束 19：本 gate 不更新 Robot/mobile 文件，那是并行 worker 范围。
# 设计约束 20：本 gate 不读取 vendor 硬件事实，不新增硬件假设。
# 设计约束 21：accepted/missing/rejected 都是材料回执维度，不是交付结果。
# 设计约束 22：unsupported source 不做“尽力理解”，直接要求重跑 material pack。
# 设计约束 23：material callback summary 不输出 raw local path 或 absolute path。
# 设计约束 24：callback_packet_status 是唯一主状态，summary/status 与其同步。
# 设计约束 25：Robot/mobile 后续只能只读展示本 summary。

FORBIDDEN_COPY = (
    "Authorization",
    "OSS_ACCESS_KEY",
    "OSS_SECRET",
    "access_key",
    "secret",
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

# token/queue/OSS/DB 只按凭证或 URL 形态拦截，避免误伤 not_proven 边界文案。
SENSITIVE_CONTEXT_PATTERNS = (
    re.compile(r"(?i)\b(token|api[_-]?key|access[_-]?key|secret|password)\b\s*[:=]\s*[^,\s]+"),
    re.compile(r"(?i)\b(oss|db|database|queue)[_-]?(url|token|secret|key)\b\s*[:=]\s*[^,\s]+"),
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

SAFE_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")

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
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"), r"\1[REDACTED_PATH]"),
    (re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
)


def _utc_now() -> str:
    # UTC 时间便于 PC 和 Docker-only 证据按时间线复盘。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，确保 blocked 输出也不回显敏感材料。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_value(value: Any) -> Any:
    # 最终 payload 递归脱敏，避免 nested note 绕过字段级 helper。
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
    # 安全扫描覆盖键和值；不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_raw_path_copy(value: Any) -> bool:
    # 绝对路径会泄漏 host，也会诱导下游读取真实材料目录。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_forbidden_copy(value: Any) -> bool:
    # 凭证、ROS topic、硬件 transport 或外部服务 URL 不能进入 summary。
    encoded = _encoded(value)
    return (
        any(token in encoded for token in FORBIDDEN_COPY)
        or any(pattern.search(encoded) for pattern in SENSITIVE_CONTEXT_PATTERNS)
        or _has_raw_path_copy(value)
    )


def _has_success_or_control_claim(value: Any) -> bool:
    # 顶层布尔和自由文案都检查，防止动作放行语义穿透。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都输出 blocked shape，方便自动化复盘。
    if not path:
        return {}, "material_pack_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "material_pack_missing"
    except json.JSONDecodeError:
        return {}, "material_pack_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "material_pack_read_error"
    if not isinstance(payload, dict):
        return {}, "material_pack_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段，字符串 wrapper 不能伪装可信 JSON。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、diagnostics 和 safe_copy 字段位置不同，取首个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_ref(value: Any) -> str:
    # evidence_ref 不做 basename 降级；路径形态必须由 status 层拒绝。
    return _safe_text(value).strip()


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免任意 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "route_task_field_retest_material_pack",
        "route_task_field_retest_material_pack_summary",
        "route_task_field_retest_material_callback_packet",
        "route_task_field_retest_material_callback_packet_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "diagnostics",
        "nested_diagnostics",
        "source_material_pack",
        "material_pack_artifact",
        "material_pack_summary",
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
    # schema 命中时优先返回嵌套 material pack；否则保留顶层用于 unsupported 诊断。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _list_text(value: Any, limit: int = 64) -> list[str]:
    # 摘要只输出扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                label = _first_text(item.get("material"), item.get("name"), item.get("id"), item.get("key"), default="")
                if label:
                    items.append(_safe_text(label))
            elif isinstance(item, (str, int, float, bool)):
                items.append(_safe_text(item))
        return items
    if isinstance(value, dict):
        return [_safe_text(key) for key in list(value.keys())[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _source_boundary(source: dict[str, Any]) -> str:
    # boundary 兼容 evidence_boundary 和旧 boundary 字段。
    return _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()


def _source_schema(source: dict[str, Any]) -> str:
    # schema 单独 helper，方便 artifact/summary 保持同一口径。
    return _safe_text(source.get("schema", "")).strip()


def _source_ref_raw(source: dict[str, Any]) -> str:
    # safe_evidence_ref 优先，兼容 summary、diagnostics 和 safe_copy。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    diagnostics = _dict(source, "diagnostics") or _dict(source, "nested_diagnostics")
    safe_copy = _dict(source, "safe_copy")
    return _first_text(
        source.get("safe_evidence_ref"),
        source.get("evidence_ref"),
        robot.get("safe_evidence_ref"),
        robot.get("evidence_ref"),
        mobile.get("safe_evidence_ref"),
        mobile.get("evidence_ref"),
        diagnostics.get("safe_evidence_ref"),
        diagnostics.get("evidence_ref"),
        safe_copy.get("safe_evidence_ref"),
        safe_copy.get("evidence_ref"),
        default="",
    )


def _valid_safe_ref(ref: str) -> bool:
    # 证据号必须是短安全 token，禁止空值、路径、空白和弱占位符。
    if not ref or "/" in ref or "\\" in ref or ref.startswith("file:"):
        return False
    return bool(SAFE_REF_PATTERN.match(ref))


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 弱类型字符串 true 不能通过，必须保持 JSON boolean true。
    for candidate in (source, _dict(source, "robot_diagnostics_summary"), _dict(source, "mobile_readonly_summary"), _dict(source, "safe_copy")):
        if "same_evidence_ref_required" in candidate:
            return candidate.get("same_evidence_ref_required")
    return None


def _source_pack_status(source: dict[str, Any]) -> str:
    # material_pack_status 是上游主状态；status 仅做 summary 兼容。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("material_pack_status"),
            source.get("material_pack_verdict"),
            source.get("status"),
            safe_copy.get("material_pack_status"),
            safe_copy.get("status"),
            default="",
        )
    )


def _source_material_items(source: dict[str, Any]) -> list[dict[str, Any]]:
    # 优先使用 handoff-mode checklist；旧 material-dir mode 回落到 materials/manifest。
    raw = (
        source.get("field_capture_checklist")
        or source.get("materials")
        or source.get("material_manifest")
        or _dict(source, "safe_copy").get("required_materials")
        or []
    )
    items: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for entry in raw[:64]:
            if isinstance(entry, dict):
                material = _first_text(entry.get("material"), entry.get("name"), entry.get("id"), default="")
                if material:
                    items.append(_safe_value(entry | {"material": material}))
            elif isinstance(entry, str):
                items.append({"material": _safe_text(entry), "collection_status": "required_not_collected"})
    return items


def _source_material_lists(source: dict[str, Any], items: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str]]:
    # accepted/missing/rejected 是回执材料维度，不提升为 delivery result。
    accepted = _list_text(source.get("accepted_materials") or _dict(source, "safe_copy").get("accepted_materials"))
    missing = _list_text(source.get("missing_materials") or _dict(source, "safe_copy").get("missing_materials"))
    rejected = _list_text(source.get("rejected_materials") or _dict(source, "safe_copy").get("rejected_materials"))
    item_names = [_safe_text(item.get("material", "")) for item in items if item.get("material")]
    if not missing:
        accepted_set = set(accepted)
        missing = [name for name in item_names if name and name not in accepted_set]
    return accepted, missing, rejected


def _source_rerun_commands(source: dict[str, Any]) -> list[str]:
    # 上游命令只保留短文本；危险 copy 已在 status 层 fail closed。
    for candidate in (source, _dict(source, "safe_copy")):
        commands = _list_text(candidate.get("rerun_commands") or candidate.get("operator_next_steps") or candidate.get("commands"), limit=8)
        if commands:
            return commands
    return []


def _callback_status(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_status: str,
    item_count: int,
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 顺序固定：输入可信性优先于普通材料缺口。
    if load_issue:
        return "needs_material_pack_not_proven", [load_issue]
    if success_claim:
        return "unsafe_success_claim_rejected_not_proven", ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "unsupported_material_pack_schema_not_proven", ["unsafe_copy_detected"]
    if _source_schema(source) not in SOURCE_SCHEMAS:
        return "unsupported_material_pack_schema_not_proven", ["unsupported_material_pack_schema"]
    if _source_boundary(source) != SOURCE_BOUNDARY:
        return "unsupported_material_pack_schema_not_proven", ["bad_material_pack_boundary"]
    if _same_ref_required(source) is not True:
        return "evidence_ref_mismatch_rerun_not_proven", ["same_evidence_ref_required_not_true"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun_not_proven", [f"requested_ref:{requested_ref}!={source_ref}"]
    if not _valid_safe_ref(source_ref):
        return "evidence_ref_mismatch_rerun_not_proven", ["weak_or_missing_safe_evidence_ref"]
    if item_count <= 0:
        return "blocked_missing_callback_materials_not_proven", ["field_callback_items_missing"]
    if source_status in {
        "ready_for_field_retest_material_collection_not_proven",
        "ready_for_field_retest_material_pack_not_proven",
    }:
        return "ready_for_field_material_callback_not_proven", []
    if not source_status or source_status.startswith("blocked_") or source_status.startswith("needs_"):
        return "needs_material_pack_not_proven", [f"source_material_pack_status:{source_status or 'missing'}"]
    if source_status == "evidence_ref_mismatch_rerun_not_proven":
        return "evidence_ref_mismatch_rerun_not_proven", [f"source_material_pack_status:{source_status}"]
    return "unsupported_material_pack_schema_not_proven", [f"unsupported_material_pack_status:{source_status}"]


def _field_callback_items(status: str, evidence_ref: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # 表单项只说明 owner 应填写什么，不携带真实材料正文或路径。
    ref = evidence_ref or "<same_evidence_ref>"
    packet_items: list[dict[str, Any]] = []
    for item in items:
        material = _safe_text(item.get("material", "")).strip()
        if not material:
            continue
        packet_items.append(
            {
                "material": material,
                "safe_evidence_ref": ref,
                "callback_status": "pending_owner_callback",
                "accepted": False,
                "required_fields": ["collection_status", "safe_artifact_ref", "owner_note", "review_status"],
                "source_collection_status": _safe_text(item.get("collection_status", item.get("status", ""))),
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
        )
    if status != "ready_for_field_material_callback_not_proven":
        for item in packet_items:
            item["callback_status"] = "blocked_until_supported_material_pack"
    return packet_items


def _owner_acknowledgement(status: str, evidence_ref: str) -> dict[str, Any]:
    # acknowledgement 是人工回填模板，不是 robot ACK 或 task completion。
    return {
        "owner": "Autonomy Algorithm Engineer",
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "acknowledgement_status": "pending_owner_acknowledgement",
        "required_ack_fields": ["owner_id", "material_callback_status", "safe_note", "review_requested_at"],
        "blocked_until_status": "" if status == "ready_for_field_material_callback_not_proven" else status,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(status: str, missing: list[str], rejected: list[str], evidence_ref: str) -> list[str]:
    # 下一步只要求补材料回执和复跑 PC gate，不授权任何现场动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_field_material_callback_not_proven":
        return [
            f"Fill every field_callback_items entry with sanitized callback metadata for evidence_ref={ref}.",
            "Return the packet for review before result intake or mobile/diagnostics read-only display.",
            "Keep delivery_success=false and primary_actions_enabled=false until real field evidence is reviewed.",
        ]
    steps = [f"Regenerate a supported material pack on the same evidence_ref={ref} before callback packet reuse."]
    if missing:
        steps.append("Missing callback material classes: " + ", ".join(missing[:12]))
    if rejected:
        steps.append("Rejected callback material classes: " + ", ".join(rejected[:12]))
    steps.append("Do not treat this packet as route_elevator_field_pass, Nav2 proof, task_completion, or HIL.")
    return [_safe_text(step) for step in steps[:5]]


def _rerun_commands(status: str, evidence_ref: str, upstream_commands: list[str]) -> list[str]:
    # commands 使用占位路径，避免泄漏本机路径、硬件命令或云凭证。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = upstream_commands[:6] if upstream_commands else []
    commands.append(
        "python3 pc-tools/evidence/route_task_field_retest_material_pack.py "
        f"--result-review-handoff-json <result_review_handoff.json> --evidence-ref {ref} --once-json"
    )
    commands.append(
        "python3 pc-tools/evidence/route_task_field_retest_material_callback_packet.py "
        f"--material-pack-json <material_pack.json> --evidence-ref {ref} --once-json"
    )
    if status != "ready_for_field_material_callback_not_proven":
        commands.append("repair schema, boundary, safe evidence_ref, same_ref, and disabled action flags before reuse")
    return [_safe_text(command) for command in commands]


def _safe_copy(
    status: str,
    evidence_ref: str,
    field_items: list[dict[str, Any]],
    accepted: list[str],
    missing: list[str],
    rejected: list[str],
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 source payload 或材料正文。
    return {
        "schema": f"{PACKET_SUMMARY_SCHEMA}.safe_copy",
        "callback_packet_status": status,
        "status": status,
        "evidence_boundary": PACKET_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "field_callback_items": [
            {"material": item["material"], "callback_status": item["callback_status"]}
            for item in field_items
        ],
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    field_items: list[dict[str, Any]],
    accepted: list[str],
    missing: list[str],
    rejected: list[str],
    owner_ack: dict[str, Any],
    next_required: list[str],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 Robot/mobile 可消费面，字段保持白名单且不含完整 artifact。
    return {
        "schema": PACKET_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": PACKET_SCHEMA,
        "evidence_boundary": PACKET_BOUNDARY,
        "boundary": PACKET_BOUNDARY,
        "status": status,
        "callback_packet_status": status,
        "safe_evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "material_callback_summary": {
            "field_callback_count": len(field_items),
            "accepted_count": len(accepted),
            "missing_count": len(missing),
            "rejected_count": len(rejected),
            "not_proven": "not_proven",
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "field_callback_items": field_items,
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "owner_acknowledgement": owner_ack,
        "owner_next_steps": next_required,
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_material_callback_packet(
    material_pack_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 material pack，生成 field material callback packet artifact。"""
    payload, load_issue = _load_json(material_pack_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref_raw = _source_ref_raw(source) if source else ""
    source_ref = _safe_ref(source_ref_raw)
    evidence_ref_out = requested_ref or source_ref
    source_status = _source_pack_status(source) if source else ""
    items = _source_material_items(source) if source else []
    accepted, missing, rejected = _source_material_lists(source, items) if source else ([], list(FIELD_CALLBACK_MATERIALS), [])
    unsafe = bool(payload) and (_has_forbidden_copy(source) or _has_raw_path_copy(source_ref_raw))
    success_claim = bool(payload) and _has_success_or_control_claim(source)
    callback_status, status_reasons = _callback_status(
        load_issue,
        source,
        requested_ref,
        source_ref,
        source_status,
        len(items),
        unsafe,
        success_claim,
    )
    field_items = _field_callback_items(callback_status, evidence_ref_out, items)
    owner_ack = _owner_acknowledgement(callback_status, evidence_ref_out)
    next_required = _next_required_evidence(callback_status, missing, rejected, evidence_ref_out)
    rerun_commands = _rerun_commands(callback_status, evidence_ref_out, _source_rerun_commands(source) if source else [])
    safe_copy = _safe_copy(callback_status, evidence_ref_out, field_items, accepted, missing, rejected)
    summary = _summary_payload(
        callback_status,
        evidence_ref_out,
        field_items,
        accepted,
        missing,
        rejected,
        owner_ack,
        next_required,
        rerun_commands,
        safe_copy,
    )
    artifact = {
        "schema": PACKET_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": PACKET_BOUNDARY,
        "boundary": PACKET_BOUNDARY,
        "status": callback_status,
        "callback_packet_status": callback_status,
        "status_reasons": status_reasons,
        "source_schema": _source_schema(source) if source else "",
        "source_boundary": _source_boundary(source) if source else "",
        "source_material_pack": {
            "load_issue": load_issue,
            "schema": _source_schema(source) if source else "",
            "evidence_boundary": _source_boundary(source) if source else "",
            "material_pack_status": source_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "field_callback_items": field_items,
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "owner_acknowledgement": owner_ack,
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "material_callback_summary": summary,
        "route_task_field_retest_material_callback_packet_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "field_material_directory",
            "raw_field_material_content",
            "ros_graph",
            "nav2_runtime",
            "fixed_route_runtime",
            "task_record_runtime",
            "dropoff_or_cancel_runtime",
            "serial_uart",
            "wave_rover",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device",
            "browser",
            "robot_action",
            "field_retest_execution",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_success_or_control_claim(artifact) or _has_success_or_control_claim(summary):
        # 最终防线：任何动作/成功声明都降级为不安全拒绝。
        artifact["status"] = "unsafe_success_claim_rejected_not_proven"
        artifact["callback_packet_status"] = "unsafe_success_claim_rejected_not_proven"
        summary["status"] = "unsafe_success_claim_rejected_not_proven"
        summary["callback_packet_status"] = "unsafe_success_claim_rejected_not_proven"
        artifact["route_task_field_retest_material_callback_packet_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest material callback packet artifact")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--material-pack-json", help="material pack artifact, summary, wrapper, or nested diagnostics JSON")
    source.add_argument("--material-pack-summary", help="alias of --material-pack-json for summary inputs")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this callback packet")
    parser.add_argument("--output", default="", help="optional callback packet artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional callback packet summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print callback packet artifact JSON to stdout and exit")
    args = parser.parse_args()

    material_pack_json = args.material_pack_json or args.material_pack_summary or ""
    artifact, summary, exit_code = build_route_task_field_retest_material_callback_packet(
        material_pack_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_material_callback_packet: artifact_file:{_safe_text(args.output)}")
        if args.summary_output:
            print(f"material_callback_packet_summary_file: {_safe_text(args.summary_output)}")
        print(f"callback_packet_status: {artifact['callback_packet_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
