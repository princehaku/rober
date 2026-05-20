#!/usr/bin/env python3
"""生成 hardware_sensor_hil_entry_callback_review_handoff 交接 artifact。"""

from __future__ import annotations

# 设计约束 01：本 gate 只读取上一轮 callback review decision artifact/summary/wrapper。
# 设计约束 02：本 gate 不读取真实 2D LiDAR、ToF、ROS graph、Nav2、串口或 HIL。
# 设计约束 03：handoff 只把复核结果交给 owner，不代表材料、安装或 HIL 已通过。
# 设计约束 04：summary 只输出白名单字段，供 Robot/mobile/Product 只读消费。
# 设计约束 05：所有输出固定 source=software_proof、not_proven、safe_to_control=false。
# 设计约束 06：所有输出固定 delivery_success=false、primary_actions_enabled=false。
# 设计约束 07：raw UART/serial、路径、凭证、checksum、完整 artifact 都 fail closed。
# 设计约束 08：任何 HIL pass、field pass、delivery success 或控制放行文案都 fail closed。
# 设计约束 09：vendor 来源只证明本地资料边界，不证明真实 SKU/接线/电源/标定/HIL。
# 设计约束 10：CLI dependency-free，适合 PC-only/Docker-only evidence gate。

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.hardware_sensor_hil_entry_callback_review_handoff.v1"
SUMMARY_SCHEMA = "trashbot.hardware_sensor_hil_entry_callback_review_handoff_summary.v1"
SOURCE_SCHEMA = "trashbot.hardware_sensor_hil_entry_callback_review_decision.v1"
SOURCE_SUMMARY_SCHEMA = "trashbot.hardware_sensor_hil_entry_callback_review_decision_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate"
SOURCE_BOUNDARY = "software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate"

# repo 相对路径进入 artifact，避免把开发机绝对路径扩散到下游。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

REQUIRED_CALLBACK_MATERIALS = (
    "2d_lidar_sku_source_receipt",
    "tof_sku_source_receipt",
    "mounting",
    "wiring",
    "power",
    "calibration",
    "hil_entry_operator_result",
)

READY_SOURCE_DECISION = "ready_for_hardware_sensor_hil_entry_callback_owner_handoff_not_proven"
BACKFILL_SOURCE_DECISION = "needs_hardware_sensor_hil_entry_callback_material_backfill_not_proven"
REJECTED_SOURCE_DECISION = "blocked_rejected_hardware_sensor_hil_entry_callback_materials_not_proven"

ACCEPTED_HANDOFF = "accepted_ready_hardware_sensor_hil_entry_callback_review_handoff_not_proven"
BLOCKED_MISSING_HANDOFF = "blocked_missing_hardware_sensor_hil_entry_callback_handoff_materials_not_proven"
REJECTED_HANDOFF = "blocked_rejected_hardware_sensor_hil_entry_callback_source_decision_not_proven"
UNSAFE_HANDOFF = "blocked_unsafe_hardware_sensor_hil_entry_callback_review_handoff_input_not_proven"
MISMATCH_HANDOFF = "blocked_evidence_ref_mismatch_not_proven"
UNSUPPORTED_HANDOFF = "blocked_unsupported_hardware_sensor_hil_entry_callback_review_decision_not_proven"
MALFORMED_HANDOFF = "blocked_malformed_hardware_sensor_hil_entry_callback_review_decision_not_proven"

# not_proven 固定进入 artifact/summary，防止 handoff ready 被误读成真实 HIL。
NOT_PROVEN = (
    "real_2d_lidar_sku_source_receipt_accepted",
    "real_2d_lidar_mounted_wired_powered_calibrated",
    "real_tof_sku_source_receipt_accepted",
    "real_tof_mounted_wired_powered_calibrated",
    "real_hil_entry_operator_checklist_complete",
    "real_sensor_hil_entry_pass",
    "real_nav2_slam_field_pass",
    "real_near_field_safety_gate_pass",
    "real_route_or_elevator_field_pass",
    "pr5_review_thread_resolved",
    "objective5_external_proof",
    "delivery_success",
)

NON_CLAIM_FLAGS = {
    "source": SOURCE,
    "evidence_status": "not_proven",
    "safe_to_control": False,
    "delivery_success": False,
    "primary_actions_enabled": False,
    "pr5_review_thread": "PRRT_kwDOSWB9286CJ3tX_not_resolved_by_this_gate",
}

# 输入如果带 raw/secret/control/success 语义，交接层不能继续传播。
FORBIDDEN_COPY = (
    "Authorization",
    "Bearer ",
    "access_key",
    "accessKey",
    "secret",
    "token",
    "password",
    "AK=",
    "SK=",
    "oss://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "redis://",
    "amqp://",
    "mongodb://",
    "queue_url",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "/dev/cu.",
    "/dev/tty.",
    "raw UART",
    "raw serial",
    "raw JSON",
    "raw_json",
    "complete artifact",
    "complete_artifact",
    "Traceback",
    "checksum",
)

SUCCESS_OR_CONTROL_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bHIL\s+(passed|pass|success|complete|completed)\b"),
    re.compile(r"(?i)\bfield\s+(pass|passed|success|complete|completed)\b"),
    re.compile(r"(?i)\b(delivery|installed|wired|powered|calibrated)\s+(pass|passed|success|complete|completed|done)\b"),
    re.compile(r"(送达|交付|安装|接线|上电|电源|标定|HIL|现场).{0,16}(完成|通过|成功|已验证)"),
)

# blocked artifact 也要脱敏，避免错误输入被复制进 evidence bundle。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)raw[_ -]?(UART|serial|JSON)"), "[REDACTED_RAW_MATERIAL]"),
    (re.compile(r"(?i)complete[_ -]?artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"), r"\1[REDACTED_PATH]"),
)


def _utc_now() -> str:
    # UTC 时间让 macOS 与 Docker-only evidence 输出可稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, default: str = "") -> str:
    # 所有自由文本先脱敏，再进入 artifact/summary。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text or default


def _repo_ref(path: Path | None, fallback: str = "missing") -> str:
    # 文件引用只保留 repo 相对路径或 basename，不泄漏本机目录。
    if path is None:
        return fallback
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name or fallback


def _safe_ref(value: Any, fallback: str = "missing") -> str:
    # evidence_ref 不能像路径；像路径时降级 file:name 并由合同检查阻断。
    text = _safe_text(value)
    if not text:
        return fallback
    path = Path(text)
    if path.is_absolute() or "/" in text or "\\" in text:
        return f"file:{path.name}"
    return text


def _is_safe_ref(value: str) -> bool:
    # safe evidence_ref 要短、无路径、无 shell 空白，方便现场按号回填。
    if not value or value.startswith("file:") or value == "missing":
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{2,120}", value))


def _resolve_source_path(source: str | Path | None) -> tuple[Path | None, str]:
    # 支持 env: 和 file:，便于自动化传递上游 artifact 路径。
    text = str(source or "").strip()
    if not text:
        return None, "missing"
    if text.startswith("env:"):
        name = text.removeprefix("env:").strip()
        value = os.environ.get(name, "").strip()
        if not name or not value:
            return None, "missing"
        text = value
    if text.startswith("file:"):
        text = text.removeprefix("file:")
    return Path(text).expanduser(), "path"


def _read_json(source: str | Path | None) -> tuple[dict[str, Any], str, Path | None]:
    # 缺输入或坏 JSON 都转为 fail-closed artifact，不把 traceback 暴露给自动化。
    path, _style = _resolve_source_path(source)
    if path is None:
        return {}, "missing", None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "missing", path
    except json.JSONDecodeError:
        return {}, "malformed", path
    except (OSError, UnicodeDecodeError):
        return {}, "malformed", path
    if not isinstance(payload, dict):
        return {}, "malformed", path
    return payload, "", path


def _dict(value: Any) -> dict[str, Any]:
    # 只接受 object，避免字符串 wrapper 伪装可信 summary。
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    # 上游可能缺字段；统一列表化，方便白名单截断。
    return list(value) if isinstance(value, (list, tuple)) else []


def _encoded(value: Any) -> str:
    # JSON 编码用于统一扫描 key/value；不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _without_not_proven(value: Any) -> Any:
    # not_proven 会含 pass/success 目标名，成功扫描必须排除这个安全字段。
    if isinstance(value, dict):
        return {key: _without_not_proven(item) for key, item in value.items() if key != "not_proven"}
    if isinstance(value, list):
        return [_without_not_proven(item) for item in value]
    return value


def _has_success_or_control_claim(value: Any) -> bool:
    # 控制放行或成功文案只能来自真实验收；本 gate 看到即 blocked。
    encoded = _encoded(_without_not_proven(value))
    return any(pattern.search(encoded) for pattern in SUCCESS_OR_CONTROL_PATTERNS)


def _has_forbidden_copy(value: Any) -> bool:
    # raw material、凭证、完整路径、checksum 都不该进入 handoff。
    encoded = _encoded(value)
    if any(token in encoded for token in FORBIDDEN_COPY):
        return True
    return bool(re.search(r'(?i)"[^"]*(/Users/|/home/|/tmp/|/var/folders/)[^"]*"', encoded))


def _any_true_key(value: Any, key: str) -> bool:
    # 嵌套 true 字段同样会误导下游，必须递归阻断。
    if isinstance(value, dict):
        return any((k == key and item is True) or _any_true_key(item, key) for k, item in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "hardware_sensor_hil_entry_callback_review_decision_summary",
        "hardware_sensor_hil_entry_callback_review_decision",
        "callback_review_decision_summary",
        "robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary",
        "summary",
        "safe_copy",
        "artifact",
        "payload",
        "data",
    ):
        nested = _dict(payload.get(key))
        if nested:
            candidates.extend(_source_candidates(nested))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择上一轮 review decision schema；否则保留顶层用于 unsupported 诊断。
    for candidate in _source_candidates(payload):
        if _safe_text(candidate.get("schema")) in {SOURCE_SCHEMA, SOURCE_SUMMARY_SCHEMA}:
            return candidate
    return payload


def _schema_status(load_issue: str, source: dict[str, Any]) -> str:
    # 只接受上一轮 callback review decision artifact/summary，避免误吃其他 evidence。
    if load_issue == "malformed":
        return "malformed"
    if load_issue:
        return "not_loaded"
    schema = _safe_text(source.get("schema"))
    boundary = _safe_text(source.get("evidence_boundary") or source.get("source_evidence_boundary"))
    if schema not in {SOURCE_SCHEMA, SOURCE_SUMMARY_SCHEMA}:
        return "unsupported_schema"
    if boundary != SOURCE_BOUNDARY:
        return "unsupported_boundary"
    return "supported"


def _status(source: dict[str, Any]) -> str:
    # summary 与 artifact 字段名不同，这里统一成 source review decision status。
    return _safe_text(
        source.get("review_decision")
        or source.get("status")
        or source.get("hardware_sensor_hil_entry_callback_review_decision"),
        "missing_source_review_decision",
    )


def _material_names(value: Any) -> list[str]:
    # summary 可能只给 string list；artifact 可能给 object list。
    names: list[str] = []
    for item in _list(value):
        if isinstance(item, dict):
            name = _safe_text(item.get("material") or item.get("name"))
        else:
            name = _safe_text(item)
        if name and name not in names:
            names.append(name)
    return names


def _rejected_names(value: Any) -> list[str]:
    # rejected 只保留材料名，不复制原始 reject body。
    names: list[str] = []
    for item in _list(value):
        if isinstance(item, dict):
            name = _safe_text(item.get("material") or item.get("name"), "unknown")
        else:
            name = _safe_text(item, "unknown")
        if name and name not in names:
            names.append(name)
    return names


def _safe_list(value: Any, limit: int = 12) -> list[str]:
    # 下游列表统一截断，避免 summary 变成材料搬运层。
    items: list[str] = []
    for item in _list(value)[:limit]:
        text = _safe_text(item)
        if text:
            items.append(text[:240])
    return items


def _owner_handoff(value: Any) -> list[dict[str, str]]:
    # handoff 只保留 owner/action，不给 Robot 开任何控制动作。
    handoff: list[dict[str, str]] = []
    for item in _list(value)[:8]:
        data = _dict(item)
        owner = _safe_text(data.get("owner"), "Hardware Infra Engineer")
        action = _safe_text(data.get("action"), "Keep hardware_material_pending until real evidence lands.")
        handoff.append({"owner": owner[:80], "action": action[:260]})
    return handoff


def _normalize_source(source: dict[str, Any]) -> dict[str, Any]:
    # 归一化只提取白名单字段，避免把原 review artifact 复制到交接层。
    safe_copy = _dict(source.get("safe_copy"))
    accepted = _material_names(source.get("accepted_materials") or safe_copy.get("accepted_materials"))
    missing = _safe_list(source.get("missing_materials") or source.get("missing_required_materials") or safe_copy.get("missing_materials"))
    rejected = _rejected_names(source.get("rejected_materials") or safe_copy.get("rejected_materials"))
    return {
        "schema": _safe_text(source.get("schema")),
        "source": _safe_text(source.get("source"), "missing"),
        "status": _status(source),
        "evidence_ref": _safe_ref(source.get("evidence_ref") or source.get("safe_evidence_ref") or safe_copy.get("evidence_ref")),
        "accepted_materials": accepted,
        "missing_required_materials": missing,
        "rejected_materials": rejected,
        "owner_handoff": _owner_handoff(source.get("owner_handoff")),
        "next_required_evidence": _safe_list(source.get("next_required_evidence") or safe_copy.get("next_required_evidence"), 12),
        "evidence_status": _safe_text(source.get("evidence_status") or source.get("overall_status"), "not_proven"),
        "delivery_success": source.get("delivery_success", safe_copy.get("delivery_success")),
        "primary_actions_enabled": source.get("primary_actions_enabled", safe_copy.get("primary_actions_enabled")),
        "safe_to_control": source.get("safe_to_control", safe_copy.get("safe_to_control", False)),
    }


def _weak_contract(normalized: dict[str, Any], evidence_ref: str) -> str:
    # 上游 bool 必须是真 bool；字符串 false 在消费侧可能被当成 truthy。
    if normalized["source"] != SOURCE:
        return "source"
    if not _is_safe_ref(evidence_ref):
        return "evidence_ref"
    if normalized["evidence_status"] != "not_proven":
        return "evidence_status"
    for field in ("delivery_success", "primary_actions_enabled", "safe_to_control"):
        if normalized.get(field) is not False:
            return field
    return ""


def _handoff_status(
    load_issue: str,
    schema_status: str,
    weak_contract: str,
    unsafe_copy: bool,
    success_or_control: bool,
    evidence_ref_mismatch: bool,
    normalized: dict[str, Any],
) -> str:
    # 决策顺序先挡输入合同，再挡危险复制，最后映射 source review decision。
    if load_issue == "malformed" or schema_status == "malformed":
        return MALFORMED_HANDOFF
    if load_issue or schema_status != "supported":
        return UNSUPPORTED_HANDOFF
    if weak_contract or unsafe_copy or success_or_control:
        return UNSAFE_HANDOFF
    if evidence_ref_mismatch:
        return MISMATCH_HANDOFF
    if normalized["status"] == REJECTED_SOURCE_DECISION or normalized["rejected_materials"]:
        return REJECTED_HANDOFF
    if normalized["status"] == BACKFILL_SOURCE_DECISION or normalized["missing_required_materials"]:
        return BLOCKED_MISSING_HANDOFF
    if normalized["status"] != READY_SOURCE_DECISION:
        return REJECTED_HANDOFF
    accepted = set(normalized["accepted_materials"])
    if any(item not in accepted for item in REQUIRED_CALLBACK_MATERIALS):
        return BLOCKED_MISSING_HANDOFF
    return ACCEPTED_HANDOFF


def _status_reasons(status: str, normalized: dict[str, Any], details: dict[str, str]) -> list[str]:
    # reason 只说明交接依据，不扩大成真实硬件结论。
    if status == ACCEPTED_HANDOFF:
        return [
            "source review decision is ready_for_owner_handoff_not_proven",
            "accepted callback materials cover required sanitized categories",
            "handoff remains software_proof/not_proven with all control and delivery flags false",
        ]
    if status == BLOCKED_MISSING_HANDOFF:
        missing = normalized["missing_required_materials"] or [
            item for item in REQUIRED_CALLBACK_MATERIALS if item not in set(normalized["accepted_materials"])
        ]
        return [f"missing_required_materials: {', '.join(missing)}"]
    if status == REJECTED_HANDOFF:
        return [f"source_review_decision_rejected_or_not_ready: {normalized['status']}"]
    if status == MISMATCH_HANDOFF:
        return ["input evidence_ref does not match requested evidence_ref"]
    if status == UNSAFE_HANDOFF:
        return [f"unsafe_or_weak_source_contract: {details.get('weak_contract') or 'unsafe_copy_or_success_claim'}"]
    if status == MALFORMED_HANDOFF:
        return ["malformed review decision input JSON"]
    return [f"missing_or_unsupported_review_decision: {details.get('schema_status', 'not_loaded')}"]


def _next_required_evidence(status: str, normalized: dict[str, Any], evidence_ref: str) -> list[str]:
    # 下一步只要求人类补证据或复核，不触发 ROS、串口、HIL 或控制动作。
    if status == ACCEPTED_HANDOFF:
        return [
            f"Hardware Infra Engineer schedules real HIL-entry evidence collection under evidence_ref={evidence_ref}.",
            "Keep PRRT_kwDOSWB9286CJ3tX open until real 2D LiDAR / ToF materials and HIL evidence are reviewer-accepted.",
        ]
    if status == BLOCKED_MISSING_HANDOFF:
        missing = normalized["missing_required_materials"] or [
            item for item in REQUIRED_CALLBACK_MATERIALS if item not in set(normalized["accepted_materials"])
        ]
        return [f"Backfill sanitized {item} callback review material under the same evidence_ref." for item in missing]
    if status == REJECTED_HANDOFF:
        return ["Rerun hardware_sensor_hil_entry_callback_review_decision after replacing rejected source materials."]
    if status == MISMATCH_HANDOFF:
        return [f"Regenerate source review decision with the same safe evidence_ref={evidence_ref}."]
    return [
        "Regenerate a supported hardware_sensor_hil_entry_callback_review_decision summary.",
        "Remove raw credentials, full paths, serial/UART details, checksums, complete artifacts, success wording, and control claims.",
    ]


def _owner_handoff_for_status(status: str, normalized: dict[str, Any], evidence_ref: str) -> list[dict[str, str]]:
    # owner handoff 是责任分配，不是控制动作或验收通过。
    handoff = normalized["owner_handoff"][:5]
    if status == ACCEPTED_HANDOFF:
        handoff.extend(
            [
                {
                    "owner": "Hardware Infra Engineer",
                    "action": f"Prepare real HIL-entry collection checklist for evidence_ref={evidence_ref}; keep hardware_material_pending until real evidence lands.",
                },
                {
                    "owner": "Product Manager / OKR Owner",
                    "action": "Keep PRRT_kwDOSWB9286CJ3tX unresolved until real materials and reviewer acceptance exist.",
                },
            ]
        )
    elif status == BLOCKED_MISSING_HANDOFF:
        handoff.append(
            {
                "owner": "Hardware Infra Engineer",
                "action": "Request missing sanitized callback-review materials from field owner under the same evidence_ref.",
            }
        )
    else:
        handoff.append(
            {
                "owner": "Hardware Infra Engineer",
                "action": "Repair review decision schema, boundary, evidence_ref, or safety contract before handoff.",
            }
        )
    return handoff[:8]


def _safe_copy(summary: dict[str, Any]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 首选消费面，不包含 raw source 或完整 artifact。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "handoff_status": summary["handoff_status"],
        "status": summary["handoff_status"],
        "source_review_decision_status": summary["source_review_decision_status"],
        "safe_evidence_ref": summary["safe_evidence_ref"],
        "owner_handoff": summary["owner_handoff"],
        "missing_required_materials": summary["missing_required_materials"],
        "next_required_evidence": summary["next_required_evidence"],
        "evidence_boundary": summary["evidence_boundary"],
        "non_claim_flags": summary["non_claim_flags"],
    }


def build_hardware_sensor_hil_entry_callback_review_handoff(
    callback_review_decision_json: str | Path | None = None,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 callback review decision，生成 fail-closed handoff。"""

    payload, load_issue, source_path = _read_json(callback_review_decision_json)
    source = _find_source(payload) if payload else {}
    normalized = _normalize_source(source)
    safe_ref = _safe_ref(evidence_ref or normalized["evidence_ref"])
    schema_status = _schema_status(load_issue, source)
    weak_contract = "" if load_issue or schema_status != "supported" else _weak_contract(normalized, safe_ref)
    evidence_ref_mismatch = bool(evidence_ref and normalized["evidence_ref"] not in {"missing", safe_ref} and normalized["evidence_ref"] != safe_ref)
    unsafe_copy = bool(payload and _has_forbidden_copy(payload))
    success_or_control = bool(
        payload
        and (
            _has_success_or_control_claim(payload)
            or _any_true_key(payload, "delivery_success")
            or _any_true_key(payload, "primary_actions_enabled")
            or _any_true_key(payload, "safe_to_control")
        )
    )
    handoff_status = _handoff_status(
        load_issue,
        schema_status,
        weak_contract,
        unsafe_copy,
        success_or_control,
        evidence_ref_mismatch,
        normalized,
    )
    details = {"schema_status": schema_status, "weak_contract": weak_contract}
    owner_handoff = _owner_handoff_for_status(handoff_status, normalized, safe_ref)
    next_required = _next_required_evidence(handoff_status, normalized, safe_ref)

    summary: dict[str, Any] = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "handoff_status": handoff_status,
        "status": handoff_status,
        "source_review_decision_status": normalized["status"],
        "safe_evidence_ref": safe_ref,
        "evidence_ref": safe_ref,
        "owner_handoff": owner_handoff,
        "missing_required_materials": normalized["missing_required_materials"],
        "next_required_evidence": next_required,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "non_claim_flags": dict(NON_CLAIM_FLAGS),
        "boundary_note": "software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate; source=software_proof; not_proven; safe_to_control=false; delivery_success=false; primary_actions_enabled=false",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }
    summary["safe_copy"] = _safe_copy(summary)
    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "handoff_status": handoff_status,
        "status": handoff_status,
        "status_reasons": _status_reasons(handoff_status, normalized, details),
        "evidence_ref": safe_ref,
        "safe_evidence_ref": safe_ref,
        "source_callback_review_decision_ref": _repo_ref(source_path),
        "source_callback_review_decision_schema": normalized["schema"] or "missing",
        "source_callback_review_decision_boundary": _safe_text(source.get("evidence_boundary"), "missing") if source else "missing",
        "source_review_decision_status": normalized["status"],
        "schema_status": schema_status,
        "weak_contract": weak_contract,
        "accepted_materials": normalized["accepted_materials"],
        "missing_required_materials": normalized["missing_required_materials"],
        "rejected_materials": normalized["rejected_materials"],
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "vendor_source_boundary": {
            "source": _repo_ref(DEFAULT_VENDOR_INDEX),
            "checked_readable_local_sources": [
                "docs/vendor/VENDOR_INDEX.md",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h",
            ],
            "review_thread_context": "PRRT_kwDOSWB9286CJ3tX",
            "vendor_boundary": "Orange Pi Zero 3 / WAVE ROVER / UART JSON / firmware/vendor app source boundary only",
            "project_2d_lidar_tof_mounting_wiring_power_calibration_hil_proof": "not_proven",
        },
        "non_access_scope": [
            "physical_2d_lidar",
            "physical_tof",
            "wave_rover_runtime",
            "serial_uart",
            "ros_graph",
            "sensor_driver_runtime",
            "nav2_runtime",
            "hil_rig",
            "field_run",
            "delivery_execution",
            "objective5_external_cloud",
        ],
        "hardware_sensor_hil_entry_callback_review_handoff_summary": summary,
        "safe_copy": summary["safe_copy"],
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "non_claim_flags": dict(NON_CLAIM_FLAGS),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }
    return artifact, summary, 0 if handoff_status == ACCEPTED_HANDOFF else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出目录自动创建，便于 sprint evidence bundle 收集。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只生成 software-proof metadata，不访问真实硬件、串口或 HIL。
    parser = argparse.ArgumentParser(
        description="Generate trashbot.hardware_sensor_hil_entry_callback_review_handoff.v1 from a callback review decision artifact or summary."
    )
    parser.add_argument("--callback-review-decision-json", default="", help="Previous hardware_sensor_hil_entry_callback_review_decision artifact/summary/wrapper JSON.")
    parser.add_argument("--evidence-ref", default="", help="Optional safe evidence_ref override; mismatches fail closed.")
    parser.add_argument("--output", default="", help="Write full HIL-entry callback review handoff artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact HIL-entry callback review handoff summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_sensor_hil_entry_callback_review_handoff(
        args.callback_review_decision_json or None,
        evidence_ref=args.evidence_ref,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_sensor_hil_entry_callback_review_handoff: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
