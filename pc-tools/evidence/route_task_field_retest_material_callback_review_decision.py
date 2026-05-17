#!/usr/bin/env python3
"""生成 route/task field retest material callback review decision artifact。

该 PC evidence gate 只消费上一轮
route_task_field_retest_material_callback_packet 的 artifact、summary、wrapper
或 nested diagnostics，把材料回执包转成可复核的 review decision artifact 和
summary。它不读取材料目录，不访问 ROS graph、Nav2/fixed-route runtime、
task record runtime、serial/UART、WAVE ROVER、外部云、4G、OSS/CDN、DB/queue
或真实手机/browser，也不触发任何机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# review decision 是 material callback packet 后的新契约，不能复用上游 schema。
DECISION_SCHEMA = "trashbot.route_task_field_retest_material_callback_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_material_callback_review_decision_summary.v1"
SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_route_task_field_retest_material_callback_review_decision_gate"

# 只接受上一轮 material callback packet，避免跳过 packet 模板直接解释 raw 材料。
SOURCE_PACKET_SCHEMA = "trashbot.route_task_field_retest_material_callback_packet.v1"
SOURCE_PACKET_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_material_callback_packet_summary.v1"
SOURCE_SCHEMAS = {SOURCE_PACKET_SCHEMA, SOURCE_PACKET_SUMMARY_SCHEMA}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_material_callback_packet_gate"

# 这些现场回执材料只作为 metadata 类别，不代表已经存在真实现场内容。
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

# not_proven 是本 gate 的负边界，防止 ready decision 被误读成实地通过。
NOT_PROVEN = (
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime",
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
    "route_task_field_retest_material_callback_review_decision; "
    "software_proof_docker_route_task_field_retest_material_callback_review_decision_gate; "
    "trashbot.route_task_field_retest_material_callback_review_decision.v1; "
    "trashbot.route_task_field_retest_material_callback_review_decision_summary.v1; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只读 material callback packet，不读取材料目录。
# 设计约束 02：review decision 只决定回执是否可复核，不证明现场执行。
# 设计约束 03：ready 状态仍保持 not_proven，不改变 Robot/mobile action。
# 设计约束 04：schema 和 boundary 必须同时命中 source family。
# 设计约束 05：safe_evidence_ref 是证据主键，弱值或路径必须 fail closed。
# 设计约束 06：same_evidence_ref_required 必须是真布尔 true。
# 设计约束 07：source delivery_success/primary_actions_enabled 只能为 false。
# 设计约束 08：raw path、credential、DB/queue/OSS token 和 success claim 必须拒绝。
# 设计约束 09：accepted/missing/rejected 只表达材料回执维度。
# 设计约束 10：owner_acknowledgement 是回执复核元数据，不是 Robot ACK。
# 设计约束 11：summary 是 Robot/mobile 首选消费面，只输出安全摘要。
# 设计约束 12：wrapper/nested 递归只走固定 key，避免 arbitrary JSON 被采信。
# 设计约束 13：rerun commands 只给 PC evidence gate，不包含硬件/ROS/云命令。
# 设计约束 14：safe_copy 不含完整 source、raw artifact 或材料路径。
# 设计约束 15：输出再次脱敏，blocked artifact 也不能泄漏敏感输入。
# 设计约束 16：exit code 保持 0，让 blocked decision 也能进入 sprint 证据。
# 设计约束 17：所有状态名保留 not_proven，方便下游 fail closed。
# 设计约束 18：本 gate 不更新 Robot/mobile 文件，那是并行 worker 范围。
# 设计约束 19：本 gate 不读取 vendor 硬件事实，不新增硬件假设。
# 设计约束 20：accepted 全覆盖且 owner ack 有效才进入 controlled rerun ready。
# 设计约束 21：missing/rejected 或 pending ack 都要求 backfill，不走 happy path。
# 设计约束 22：unsupported source 不做“尽力理解”，直接要求重跑 packet。
# 设计约束 23：review summary 不输出 raw local path 或 absolute path。
# 设计约束 24：review_decision 是唯一主状态，summary/status 与其同步。
# 设计约束 25：Robot/mobile 后续只能只读展示本 summary。

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
    "UART",
    "WAVE ROVER",
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

# 成功或动作授权只能来自真实验收；本 gate 看到即 unsafe_success_claim。
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

# 本机绝对路径或 Windows 路径不允许进入 phone-safe review summary。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

SAFE_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")

# blocked artifact 也要脱敏，避免把危险输入原样留在证据文件。
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
        return {}, "material_callback_packet_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "material_callback_packet_missing"
    except json.JSONDecodeError:
        return {}, "material_callback_packet_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "material_callback_packet_read_error"
    if not isinstance(payload, dict):
        return {}, "material_callback_packet_not_object"
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


def _valid_safe_ref(ref: str) -> bool:
    # 证据号必须是短安全 token，禁止空值、路径、空白和弱占位符。
    if not ref or "/" in ref or "\\" in ref or ref.startswith("file:"):
        return False
    return bool(SAFE_REF_PATTERN.match(ref))


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免任意 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "route_task_field_retest_material_callback_packet",
        "route_task_field_retest_material_callback_packet_summary",
        "material_callback_packet",
        "material_callback_packet_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "diagnostics",
        "nested_diagnostics",
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
    # schema 命中时优先返回嵌套 callback packet；否则保留顶层用于 unsupported 诊断。
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


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 弱类型字符串 true 不能通过，必须保持 JSON boolean true。
    for candidate in (source, _dict(source, "robot_diagnostics_summary"), _dict(source, "mobile_readonly_summary"), _dict(source, "safe_copy")):
        if "same_evidence_ref_required" in candidate:
            return candidate.get("same_evidence_ref_required")
    return None


def _source_packet_status(source: dict[str, Any]) -> str:
    # callback_packet_status 是上游主状态；status 仅做 summary 兼容。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("callback_packet_status"),
            source.get("status"),
            safe_copy.get("callback_packet_status"),
            safe_copy.get("status"),
            default="",
        )
    )


def _field_callback_items(source: dict[str, Any]) -> list[dict[str, Any]]:
    # field_callback_items 是权威回执项；summary/safe_copy 可作为兼容入口。
    raw = (
        source.get("field_callback_items")
        or _dict(source, "material_callback_summary").get("field_callback_items")
        or _dict(source, "safe_copy").get("field_callback_items")
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
                items.append({"material": _safe_text(entry), "accepted": False, "callback_status": "missing_callback"})
    return items


def _item_status_text(item: dict[str, Any]) -> str:
    # 多来源回执字段统一成短文本，不解释材料正文。
    return _safe_text(
        _first_text(
            item.get("review_status"),
            item.get("material_callback_status"),
            item.get("callback_status"),
            item.get("collection_status"),
            item.get("status"),
            default="",
        )
    ).lower()


def _source_material_lists(source: dict[str, Any], items: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str]]:
    # accepted/missing/rejected 是回执材料维度，不提升为 delivery result。
    safe_copy = _dict(source, "safe_copy")
    accepted = _list_text(source.get("accepted_materials") or safe_copy.get("accepted_materials"))
    missing = _list_text(source.get("missing_materials") or safe_copy.get("missing_materials"))
    rejected = _list_text(source.get("rejected_materials") or safe_copy.get("rejected_materials"))
    if not accepted and not missing and not rejected:
        for item in items:
            material = _safe_text(item.get("material", "")).strip()
            if not material:
                continue
            status = _item_status_text(item)
            if item.get("accepted") is True or status in {"accepted", "accepted_not_proven", "review_accepted_not_proven"}:
                accepted.append(material)
            elif item.get("rejected") is True or status in {"rejected", "rejected_not_proven", "review_rejected_not_proven"}:
                rejected.append(material)
            else:
                missing.append(material)
    item_names = [_safe_text(item.get("material", "")) for item in items if item.get("material")]
    if accepted and not missing:
        accepted_set = set(accepted)
        missing = [name for name in item_names if name and name not in accepted_set and name not in rejected]
    return accepted, missing, rejected


def _owner_acknowledgement(source: dict[str, Any]) -> dict[str, Any]:
    # acknowledgement 是人工回填元数据，不是 ACK 或控制命令。
    ack = source.get("owner_acknowledgement") or _dict(source, "safe_copy").get("owner_acknowledgement") or {}
    return _safe_value(ack) if isinstance(ack, dict) else {}


def _owner_ack_ok(ack: dict[str, Any]) -> bool:
    # pending/block 状态必须补回执；有必要字段时才可复核。
    if not ack:
        return False
    status = _safe_text(
        _first_text(
            ack.get("acknowledgement_status"),
            ack.get("material_callback_status"),
            ack.get("review_status"),
            ack.get("status"),
            default="",
        )
    ).lower()
    if status.startswith("pending") or status.startswith("blocked") or status.startswith("missing"):
        return False
    if status in {"acknowledged_not_proven", "owner_acknowledged_not_proven", "review_requested_not_proven", "material_callback_received_not_proven"}:
        return True
    return all(_safe_text(ack.get(key, "")).strip() for key in ("owner_id", "material_callback_status", "safe_note", "review_requested_at"))


def _review_decision(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_status: str,
    accepted: list[str],
    missing: list[str],
    rejected: list[str],
    owner_ack_ok: bool,
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 顺序固定：输入可信性优先于普通材料缺口。
    if load_issue:
        return "blocked_material_callback_review_not_proven", [load_issue]
    if success_claim:
        return "unsafe_success_claim_rejected_not_proven", ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked_material_callback_review_not_proven", ["unsafe_copy_detected"]
    if _source_schema(source) not in SOURCE_SCHEMAS:
        return "unsupported_material_callback_packet_schema_not_proven", ["unsupported_material_callback_packet_schema"]
    if _source_boundary(source) != SOURCE_BOUNDARY:
        return "unsupported_material_callback_packet_schema_not_proven", ["bad_material_callback_packet_boundary"]
    if _same_ref_required(source) is not True:
        return "evidence_ref_mismatch_rerun_not_proven", ["same_evidence_ref_required_not_true"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun_not_proven", [f"requested_ref:{requested_ref}!={source_ref}"]
    if not _valid_safe_ref(source_ref):
        return "evidence_ref_mismatch_rerun_not_proven", ["weak_or_missing_safe_evidence_ref"]
    if source_status != "ready_for_field_material_callback_not_proven":
        return "blocked_material_callback_review_not_proven", [f"source_callback_packet_status:{source_status or 'missing'}"]
    if rejected:
        return "needs_material_callback_backfill_not_proven", ["rejected_materials:" + ",".join(rejected[:12])]
    if missing or not accepted:
        return "needs_material_callback_backfill_not_proven", ["missing_materials:" + ",".join((missing or list(FIELD_CALLBACK_MATERIALS))[:12])]
    if not owner_ack_ok:
        return "needs_material_callback_backfill_not_proven", ["owner_acknowledgement_missing_or_pending"]
    return "ready_for_controlled_field_rerun_not_proven", []


def _material_callback_review_summary(accepted: list[str], missing: list[str], rejected: list[str], owner_ack_ok: bool) -> dict[str, Any]:
    # 该摘要只描述复核清单状态，不复制材料正文或现场结论。
    return {
        "accepted_count": len(accepted),
        "missing_count": len(missing),
        "rejected_count": len(rejected),
        "owner_acknowledgement_ok": owner_ack_ok,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(decision: str, evidence_ref: str, missing: list[str], rejected: list[str], owner_ack_ok: bool) -> list[str]:
    # 下一步只要求补安全回执和复跑 PC gate，不授权任何现场动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == "ready_for_controlled_field_rerun_not_proven":
        return [
            f"Prepare controlled field rerun review materials under evidence_ref={ref}.",
            "Keep the review decision as software_proof until real route/elevator field evidence is independently reviewed.",
        ]
    steps: list[str] = []
    if missing:
        steps.append("Backfill missing material callback classes: " + ", ".join(missing[:12]))
    if rejected:
        steps.append("Repair rejected material callback classes: " + ", ".join(rejected[:12]))
    if not owner_ack_ok:
        steps.append("Fill owner acknowledgement fields: owner_id, material_callback_status, safe_note, review_requested_at.")
    if not steps:
        steps.append(f"Regenerate a supported material callback packet on the same evidence_ref={ref}.")
    steps.append("Do not treat this review as route_elevator_field_pass, Nav2 proof, task completion, delivery_success, HIL, phone, or O5 external proof.")
    return [_safe_text(step) for step in steps[:5]]


def _rerun_commands(evidence_ref: str) -> list[str]:
    # commands 使用占位路径，避免泄漏本机路径、硬件命令或云凭证。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        "python3 pc-tools/evidence/route_task_field_retest_material_callback_packet.py "
        f"--material-pack-json <material_pack.json> --evidence-ref {ref} --once-json",
        "python3 pc-tools/evidence/route_task_field_retest_material_callback_review_decision.py "
        f"--material-callback-packet-json <material_callback_packet.json> --evidence-ref {ref} --once-json",
    ]


def _safe_copy(
    decision: str,
    evidence_ref: str,
    accepted: list[str],
    missing: list[str],
    rejected: list[str],
    owner_ack_ok: bool,
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 source payload 或材料正文。
    return {
        "schema": f"{DECISION_SUMMARY_SCHEMA}.safe_copy",
        "review_decision": decision,
        "status": decision,
        "evidence_boundary": DECISION_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "owner_acknowledgement_ok": owner_ack_ok,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    decision: str,
    status_reasons: list[str],
    evidence_ref: str,
    accepted: list[str],
    missing: list[str],
    rejected: list[str],
    owner_ack: dict[str, Any],
    owner_ack_ok: bool,
    next_required: list[str],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 Robot/mobile 可消费面，字段保持白名单且不含完整 artifact。
    return {
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": DECISION_SCHEMA,
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "material_callback_review_summary": _material_callback_review_summary(accepted, missing, rejected, owner_ack_ok),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "owner_acknowledgement": owner_ack,
        "owner_next_steps": next_required,
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_material_callback_review_decision(
    material_callback_packet_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 material callback packet，生成 metadata-only review decision artifact。"""
    payload, load_issue = _load_json(material_callback_packet_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref_raw = _source_ref_raw(source) if source else ""
    source_ref = _safe_ref(source_ref_raw)
    evidence_ref_out = requested_ref or source_ref
    source_status = _source_packet_status(source) if source else ""
    items = _field_callback_items(source) if source else []
    accepted, missing, rejected = _source_material_lists(source, items) if source else ([], list(FIELD_CALLBACK_MATERIALS), [])
    owner_ack = _owner_acknowledgement(source) if source else {}
    ack_ok = _owner_ack_ok(owner_ack)
    unsafe = bool(payload) and (_has_forbidden_copy(source) or _has_raw_path_copy(source_ref_raw))
    success_claim = bool(payload) and _has_success_or_control_claim(source)
    decision, status_reasons = _review_decision(
        load_issue,
        source,
        requested_ref,
        source_ref,
        source_status,
        accepted,
        missing,
        rejected,
        ack_ok,
        unsafe,
        success_claim,
    )
    next_required = _next_required_evidence(decision, evidence_ref_out, missing, rejected, ack_ok)
    rerun_commands = _rerun_commands(evidence_ref_out)
    safe_copy = _safe_copy(decision, evidence_ref_out, accepted, missing, rejected, ack_ok)
    summary = _summary_payload(
        decision,
        status_reasons,
        evidence_ref_out,
        accepted,
        missing,
        rejected,
        owner_ack,
        ack_ok,
        next_required,
        rerun_commands,
        safe_copy,
    )
    artifact = {
        "schema": DECISION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "status_reasons": status_reasons,
        "source_schema": _source_schema(source) if source else "",
        "source_boundary": _source_boundary(source) if source else "",
        "source_material_callback_packet": {
            "load_issue": load_issue,
            "schema": _source_schema(source) if source else "",
            "evidence_boundary": _source_boundary(source) if source else "",
            "callback_packet_status": source_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "owner_acknowledgement": owner_ack,
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "material_callback_review_summary": summary,
        "route_task_field_retest_material_callback_review_decision_summary": summary,
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
        artifact["review_decision"] = "unsafe_success_claim_rejected_not_proven"
        summary["status"] = "unsafe_success_claim_rejected_not_proven"
        summary["review_decision"] = "unsafe_success_claim_rejected_not_proven"
        artifact["route_task_field_retest_material_callback_review_decision_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest material callback review decision artifact")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--material-callback-packet-json", help="material callback packet artifact, summary, wrapper, or nested diagnostics JSON")
    source.add_argument("--material-callback-packet-summary", help="alias of --material-callback-packet-json for summary inputs")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review decision")
    parser.add_argument("--output", default="", help="optional review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    packet_json = args.material_callback_packet_json or args.material_callback_packet_summary or ""
    artifact, summary, exit_code = build_route_task_field_retest_material_callback_review_decision(
        packet_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_material_callback_review_decision: artifact_file:{_safe_text(args.output)}")
        if args.summary_output:
            print(f"material_callback_review_decision_summary_file: {_safe_text(args.summary_output)}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
