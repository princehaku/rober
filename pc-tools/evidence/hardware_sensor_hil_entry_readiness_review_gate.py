#!/usr/bin/env python3
"""生成 hardware_sensor_hil_entry_readiness_review fail-closed 准入评审。"""

from __future__ import annotations

# 设计约束 01：本 gate 只合成上游 receipt intake 与 config precheck summary。
# 设计约束 02：本 gate 不读取真实硬件、传感器驱动、ROS graph、串口或网络。
# 设计约束 03：readiness review 只表示材料可进入人工评审，不代表 HIL pass。
# 设计约束 04：receipt intake 必须来自受支持 schema 和 evidence boundary。
# 设计约束 05：config precheck 必须来自受支持 schema 和 evidence boundary。
# 设计约束 06：任何上游 blocked 状态都让 readiness review fail closed。
# 设计约束 07：任何 success/control/HIL/field pass 文案都必须 fail closed。
# 设计约束 08：任何凭证、raw path、串口、topic、raw JSON copy 都必须 fail closed。
# 设计约束 09：所有输出保持 software_proof、not_proven。
# 设计约束 10：所有输出保持 delivery_success=false。
# 设计约束 11：所有输出保持 primary_actions_enabled=false。
# 设计约束 12：docs/vendor/VENDOR_INDEX.md 只作为资料边界，不证明 LiDAR/ToF 已履约。
# 设计约束 13：WAVE ROVER / Orange Pi vendor 资料只证明当前本地资料覆盖。
# 设计约束 14：上游 evidence_ref 不一致时 fail closed，避免材料链混号。
# 设计约束 15：summary 是 Robot/mobile 只读面，不复制完整 artifact。
# 设计约束 16：owner_handoff 只保留下一步人工履约动作，不给机器人控制建议。
# 设计约束 17：ready status 后缀必须带 not_proven，避免 closeout 误读。
# 设计约束 18：CLI --help 必须不依赖 ROS2、serial、yaml 或第三方包。
# 设计约束 19：默认缺输入是 blocked，不生成内置 ready 样例。
# 设计约束 20：技术注释使用中文，解释硬件证据边界和 fail-closed 原因。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.hardware_sensor_hil_entry_readiness_review.v1"
SUMMARY_SCHEMA = "trashbot.hardware_sensor_hil_entry_readiness_review_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate"

RECEIPT_SCHEMA = "trashbot.hardware_sensor_procurement_receipt_intake.v1"
RECEIPT_SUMMARY_SCHEMA = "trashbot.hardware_sensor_procurement_receipt_intake_summary.v1"
RECEIPT_BOUNDARY = "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate"
RECEIPT_READY = "ready_for_hardware_sensor_procurement_receipt_intake_not_proven"

CONFIG_SCHEMA = "trashbot.hardware_sensor_hil_entry_config_precheck.v1"
CONFIG_SUMMARY_SCHEMA = "trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1"
CONFIG_BOUNDARY = "software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate"
CONFIG_READY = "ready_for_hardware_sensor_hil_entry_config_precheck_not_proven"

READY_REVIEW = "ready_for_hardware_sensor_hil_entry_readiness_review_not_proven"
BLOCKED_MISSING_SOURCE = "blocked_missing_hardware_sensor_hil_entry_readiness_review_source"
BLOCKED_UNSUPPORTED_SOURCE = "blocked_unsupported_hardware_sensor_hil_entry_readiness_review_source"
BLOCKED_WEAK_CONTRACT = "blocked_weak_hardware_sensor_hil_entry_readiness_review_contract"
BLOCKED_UPSTREAM_NOT_READY = "blocked_upstream_hardware_sensor_hil_entry_not_ready"
BLOCKED_EVIDENCE_REF_MISMATCH = "blocked_hardware_sensor_hil_entry_readiness_review_evidence_ref_mismatch"
BLOCKED_UNSAFE_COPY = "blocked_unsafe_hardware_sensor_hil_entry_readiness_review_copy"

# repo 相对路径用于输出审计来源，避免把本机绝对路径扩散给下游。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

NOT_PROVEN = (
    "real_2d_lidar_procured",
    "real_2d_lidar_mounted_wired_calibrated",
    "real_tof_procured",
    "real_tof_channel_count_source_accepted",
    "real_tof_mounted_wired_calibrated",
    "real_sensor_config_loaded_on_robot",
    "real_sensor_driver_running",
    "real_sensor_hil_entry_pass",
    "real_nav2_slam_field_pass",
    "real_near_field_safety_gate_pass",
    "objective5_external_proof",
    "delivery_success",
)

NON_ACCESS_SCOPE = (
    "real_hardware",
    "serial_uart",
    "wave_rover_runtime",
    "orange_pi_runtime",
    "ros_graph",
    "sensor_driver_runtime",
    "nav2_runtime",
    "network",
    "hil",
    "field_pass",
    "delivery_execution",
    "objective5_external_cloud",
)

FORBIDDEN_TOKENS = (
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
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "/dev/cu.",
    "/dev/tty.",
    "raw JSON",
    "raw_json",
    "complete artifact",
    "Traceback",
    "checksum",
)

SUCCESS_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(real_)?sensor.{0,24}(hil|field).{0,24}(pass|passed|success|complete|done)\b"),
    re.compile(r"(?i)\b(readiness|hil|field|procurement|installation|calibration)\s+(pass|passed|complete|success|done)\b"),
    re.compile(r"(?i)(HIL|实测|现场|送达|安装|标定|采购|准入).{0,16}(通过|成功|完成|已验证)"),
)

SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "[REDACTED_AUTH_HEADER]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
)


def _utc_now() -> str:
    # UTC 时间让 macOS 与 Docker 生成的 evidence bundle 稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _encoded(value: Any) -> str:
    # 扫描输入键和值，避免危险字段藏在嵌套 summary 中。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 所有外发文本先脱敏，summary 不回显 raw 材料或本机细节。
    text = default if value is None else str(value).strip()
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text or default


def _safe_ref(value: Any, fallback: str = "missing") -> str:
    # evidence_ref 允许安全短引用；绝对路径只降级为文件名。
    text = _safe_text(value)
    if not text:
        return fallback
    path = Path(text)
    if path.is_absolute():
        return f"file:{path.name}"
    return text.replace("\\", "/")


def _repo_ref(path: Path) -> str:
    # vendor/source boundary 输出 repo 相对引用，便于审计和 rg 验收。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺输入是 blocked 状态，不能用异常栈替代 sprint 证据。
    if path is None:
        return {}, "missing"
    try:
        payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "missing"
    except json.JSONDecodeError:
        return {}, "invalid_json"
    except (OSError, UnicodeDecodeError):
        return {}, "read_error"
    if not isinstance(payload, dict):
        return {}, "invalid_json"
    return payload, ""


def _dict(value: Any) -> dict[str, Any]:
    # 只接受 object，避免 wrapper 弱类型绕过 schema 校验。
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    # 上游 summary 允许列表缺失，统一列表化便于白名单截断。
    return list(value) if isinstance(value, (list, tuple)) else []


def _safe_list(value: Any, limit: int = 10) -> list[str]:
    # compact summary 只保留短列表，不复制完整材料正文。
    items = []
    for item in _list(value)[:limit]:
        safe = _safe_text(item)
        if safe:
            items.append(safe[:180])
    return items


def _source_owner_handoff(value: Any) -> list[dict[str, str]]:
    # handoff 只保留 owner/action，不能夹带 raw evidence 或控制建议。
    handoff: list[dict[str, str]] = []
    for item in _list(value)[:8]:
        data = _dict(item)
        owner = _safe_text(data.get("owner"))
        action = _safe_text(data.get("action"))
        if owner and action:
            handoff.append({"owner": owner, "action": action[:220]})
    return handoff


def _has_unsafe_copy(value: Any) -> bool:
    # raw path、凭证、控制 topic、串口和完整 artifact 都不能进入 readiness review。
    encoded = _encoded(value)
    if any(token in encoded for token in FORBIDDEN_TOKENS):
        return True
    if re.search(r'(?i)"[^"]*(/Users/|/home/|/tmp/|/var/folders/)[^"]*"', encoded):
        return True
    return False


def _without_not_proven(value: Any) -> Any:
    # not_proven 列表会包含 pass 类 token；扫描成功文案时必须排除这个安全语义字段。
    if isinstance(value, dict):
        return {key: _without_not_proven(item) for key, item in value.items() if key != "not_proven"}
    if isinstance(value, list):
        return [_without_not_proven(item) for item in value]
    return value


def _has_success_claim(value: Any) -> bool:
    # 本 gate 只能表达 not_proven readiness review，任何成功断言都阻断。
    encoded = _encoded(_without_not_proven(value))
    return any(pattern.search(encoded) for pattern in SUCCESS_PATTERNS)


def _any_true_key(value: Any, key: str) -> bool:
    # 递归阻断嵌套 delivery_success 或 primary action 放行字段。
    if isinstance(value, dict):
        return any((k == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _source_payload(payload: dict[str, Any], schemas: set[str], nested_keys: tuple[str, ...]) -> dict[str, Any]:
    # 支持直接 artifact、直接 summary，以及 Robot/mobile wrapper 内嵌 summary。
    if payload.get("schema") in schemas:
        return payload
    if payload.get("schema"):
        return payload
    for key in nested_keys:
        nested = _dict(payload.get(key))
        if nested.get("schema") in schemas:
            return nested
    return payload


def _normalize_source(
    payload: dict[str, Any],
    schemas: set[str],
    nested_keys: tuple[str, ...],
    boundary: str,
    status_fields: tuple[str, ...],
    default_status: str,
) -> dict[str, Any]:
    # 只读取上游白名单字段，避免把完整材料包复制进本轮 artifact。
    source = _source_payload(payload, schemas, nested_keys)
    nested_summary = _dict(source.get("summary")) or _dict(source.get("receipt_intake_summary"))
    effective = nested_summary if nested_summary.get("schema") in schemas else source
    status = next((_safe_text(effective.get(field)) for field in status_fields if _safe_text(effective.get(field))), default_status)
    return {
        "schema": _safe_text(effective.get("schema") or source.get("schema")),
        "full_schema": _safe_text(source.get("schema")),
        "evidence_boundary": _safe_text(effective.get("evidence_boundary") or source.get("evidence_boundary")),
        "source": _safe_text(effective.get("source") or source.get("source"), "missing"),
        "status": status,
        "evidence_ref": _safe_ref(effective.get("evidence_ref") or source.get("evidence_ref"), "missing"),
        "next_required_evidence": _safe_list(effective.get("next_required_evidence") or source.get("next_required_evidence")),
        "owner_handoff": _source_owner_handoff(effective.get("owner_handoff") or source.get("owner_handoff")),
        "not_proven": _safe_list(effective.get("not_proven") or source.get("not_proven")),
        "delivery_success": effective.get("delivery_success", source.get("delivery_success")),
        "primary_actions_enabled": effective.get("primary_actions_enabled", source.get("primary_actions_enabled")),
        "hardware_material_pending": effective.get("hardware_material_pending", source.get("hardware_material_pending")),
        "hardware_material_status": _safe_text(effective.get("hardware_material_status") or source.get("hardware_material_status")),
        "boundary_supported": _safe_text(effective.get("evidence_boundary") or source.get("evidence_boundary")) == boundary,
    }


def _normalize_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    # receipt source 证明收货/来源/SKU 材料摘要形状，不证明硬件已采购或安装。
    return _normalize_source(
        payload,
        {RECEIPT_SCHEMA, RECEIPT_SUMMARY_SCHEMA},
        ("receipt_intake_summary", "hardware_sensor_procurement_receipt_intake_summary", "summary"),
        RECEIPT_BOUNDARY,
        ("receipt_intake_status", "hardware_sensor_procurement_receipt_intake", "status"),
        "missing_receipt_intake_status",
    )


def _normalize_config(payload: dict[str, Any]) -> dict[str, Any]:
    # config source 证明 future 参数化形状，不证明 sensor driver 或 TF 已运行。
    return _normalize_source(
        payload,
        {CONFIG_SCHEMA, CONFIG_SUMMARY_SCHEMA},
        ("summary", "hardware_sensor_hil_entry_config_precheck_summary"),
        CONFIG_BOUNDARY,
        ("hardware_sensor_hil_entry_config_precheck", "overall_status", "status"),
        "missing_config_precheck_status",
    )


def _source_schema_status(load_issue: str, source: dict[str, Any], schemas: set[str]) -> str:
    # schema 和 boundary 同时匹配才算 supported，避免跨 gate 误消费。
    if load_issue:
        return "not_loaded"
    schema_supported = source["schema"] in schemas
    full_schema_supported = source["full_schema"] in {"", *schemas}
    return "supported" if schema_supported and full_schema_supported and source["boundary_supported"] else "unsupported"


def _weak_contract(source: dict[str, Any], require_material_pending: bool) -> str:
    # bool 字段必须是真 bool；字符串 false 在下游容易被误判为 truthy。
    if source["source"] != SOURCE:
        return "source"
    for field in ("delivery_success", "primary_actions_enabled"):
        if not isinstance(source.get(field), bool):
            return field
    if source["delivery_success"] or source["primary_actions_enabled"]:
        return "unsafe_true_boolean"
    if require_material_pending:
        if source.get("hardware_material_pending") is not True:
            return "hardware_material_pending"
        if source.get("hardware_material_status") != "hardware_material_pending":
            return "hardware_material_status"
    return ""


def _readiness_status(
    receipt_issue: str,
    config_issue: str,
    receipt_schema_status: str,
    config_schema_status: str,
    weak_contract: str,
    unsafe_copy: bool,
    success_claim: bool,
    evidence_ref_mismatch: bool,
    receipt: dict[str, Any],
    config: dict[str, Any],
) -> str:
    # 决策顺序先检查输入合同和安全，再判断是否两个上游都 ready/not_proven。
    if receipt_issue or config_issue:
        return BLOCKED_MISSING_SOURCE
    if receipt_schema_status != "supported" or config_schema_status != "supported":
        return BLOCKED_UNSUPPORTED_SOURCE
    if weak_contract:
        return BLOCKED_WEAK_CONTRACT
    if unsafe_copy or success_claim:
        return BLOCKED_UNSAFE_COPY
    if evidence_ref_mismatch:
        return BLOCKED_EVIDENCE_REF_MISMATCH
    if receipt["status"] != RECEIPT_READY or config["status"] != CONFIG_READY:
        return BLOCKED_UPSTREAM_NOT_READY
    return READY_REVIEW


def _blocked_reason(status: str, receipt_issue: str, config_issue: str, weak_contract: str) -> str:
    # blocked_reason 保持短文本，避免复制原始材料内容。
    if status == READY_REVIEW:
        return ""
    if status == BLOCKED_MISSING_SOURCE:
        return f"missing or unreadable receipt/config source: receipt={receipt_issue or 'ok'} config={config_issue or 'ok'}"
    if status == BLOCKED_UNSUPPORTED_SOURCE:
        return "unsupported source schema or evidence boundary"
    if status == BLOCKED_WEAK_CONTRACT:
        return f"weak or unsafe upstream boolean/source contract: {weak_contract}"
    if status == BLOCKED_EVIDENCE_REF_MISMATCH:
        return "receipt intake and config precheck use different evidence_ref values"
    if status == BLOCKED_UPSTREAM_NOT_READY:
        return "receipt intake or config precheck is not ready_for_*_not_proven"
    return "source contains raw path, credential, control topic, serial device, raw JSON, HIL/field pass, delivery success, or action enablement claim"


def _next_required_evidence(status: str, receipt: dict[str, Any], config: dict[str, Any]) -> list[str]:
    # 下一步只描述人工补证据动作，不暗示启动 HIL 或机器人控制。
    if status == READY_REVIEW:
        return [
            "Run human HIL-entry material review over receipt/source/SKU, install-wiring, power, calibration, and config refs.",
            "Collect real bench/HIL-entry records before claiming sensor_hil_entry_pass or changing OKR evidence status.",
            "Keep Robot diagnostics and mobile UI read-only until real hardware evidence is reviewed.",
        ]
    required = receipt["next_required_evidence"][:4] + config["next_required_evidence"][:4]
    return required or [
        "Regenerate supported receipt intake and config precheck summaries with the same safe evidence_ref.",
        "Keep software_proof / not_proven until both upstream gates are ready.",
    ]


def _owner_handoff(status: str, receipt: dict[str, Any], config: dict[str, Any]) -> list[dict[str, str]]:
    # handoff 合并上游 owner，但追加本轮硬件履约动作。
    handoff = (receipt["owner_handoff"] + config["owner_handoff"])[:8]
    if status == READY_REVIEW:
        handoff.append(
            {
                "owner": "Hardware Infra Engineer",
                "action": "Perform human HIL-entry readiness review; do not mark HIL pass until real bench/HIL materials exist.",
            }
        )
    else:
        handoff.append(
            {
                "owner": "Hardware Infra Engineer",
                "action": "Repair supported receipt intake and config precheck inputs before any HIL-entry review.",
            }
        )
    return handoff[:10]


def _safe_copy(artifact: dict[str, Any]) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含上游完整 artifact 或硬件控制细节。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "status": artifact["readiness_review_status"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "evidence_ref": artifact["evidence_ref"],
        "receipt_intake_status": artifact["source_statuses"]["receipt_intake_status"],
        "config_precheck_status": artifact["source_statuses"]["config_precheck_status"],
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "copy_note": "software_proof only; delivery_success=false; primary_actions_enabled=false; not_proven",
    }


def _summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # summary 供 Robot/mobile/Product 只读消费，避免传播完整材料正文。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": artifact["readiness_review_status"],
        "hardware_sensor_hil_entry_readiness_review": artifact["readiness_review_status"],
        "evidence_ref": artifact["evidence_ref"],
        "source_statuses": artifact["source_statuses"],
        "schema_status": artifact["schema_status"],
        "blocked_reason": artifact["blocked_reason"],
        "next_required_evidence": artifact["next_required_evidence"],
        "owner_handoff": artifact["owner_handoff"],
        "vendor_source_boundary": artifact["vendor_source_boundary"],
        "safe_copy": artifact["safe_copy"],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "boundary_note": "software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate; delivery_success=false; primary_actions_enabled=false; not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_hardware_sensor_hil_entry_readiness_review(
    receipt_intake_json: str | Path | None = None,
    config_precheck_json: str | Path | None = None,
    evidence_ref: str = "",
    vendor_index: str | Path = DEFAULT_VENDOR_INDEX,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """合成 receipt intake 与 config precheck，生成 fail-closed readiness review。"""

    receipt_path = Path(receipt_intake_json) if receipt_intake_json else None
    config_path = Path(config_precheck_json) if config_precheck_json else None
    receipt_payload, receipt_issue = _read_json(receipt_path)
    config_payload, config_issue = _read_json(config_path)

    receipt = _normalize_receipt(receipt_payload) if receipt_payload else _normalize_receipt({})
    config = _normalize_config(config_payload) if config_payload else _normalize_config({})
    receipt_schema_status = _source_schema_status(receipt_issue, receipt, {RECEIPT_SCHEMA, RECEIPT_SUMMARY_SCHEMA})
    config_schema_status = _source_schema_status(config_issue, config, {CONFIG_SCHEMA, CONFIG_SUMMARY_SCHEMA})
    weak_receipt = "" if receipt_schema_status != "supported" else _weak_contract(receipt, require_material_pending=True)
    weak_config = "" if config_schema_status != "supported" else _weak_contract(config, require_material_pending=False)
    weak_contract = weak_receipt or weak_config
    unsafe_copy = bool((receipt_payload and _has_unsafe_copy(receipt_payload)) or (config_payload and _has_unsafe_copy(config_payload)))
    success_claim = bool(
        (receipt_payload and (_has_success_claim(receipt_payload) or _any_true_key(receipt_payload, "delivery_success") or _any_true_key(receipt_payload, "primary_actions_enabled")))
        or (config_payload and (_has_success_claim(config_payload) or _any_true_key(config_payload, "delivery_success") or _any_true_key(config_payload, "primary_actions_enabled")))
    )
    source_refs = [ref for ref in (receipt["evidence_ref"], config["evidence_ref"]) if ref and ref != "missing"]
    chosen_ref = _safe_ref(evidence_ref or (source_refs[0] if source_refs else "missing"), "missing")
    evidence_ref_mismatch = len(set(source_refs + ([chosen_ref] if evidence_ref else []))) > 1

    status = _readiness_status(
        receipt_issue,
        config_issue,
        receipt_schema_status,
        config_schema_status,
        weak_contract,
        unsafe_copy,
        success_claim,
        evidence_ref_mismatch,
        receipt,
        config,
    )

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "evidence_ref": chosen_ref,
        "source_refs": {
            "receipt_intake": _repo_ref(receipt_path) if receipt_path and receipt_path.exists() else _safe_ref(receipt_path, "missing"),
            "config_precheck": _repo_ref(config_path) if config_path and config_path.exists() else _safe_ref(config_path, "missing"),
        },
        "source_statuses": {
            "receipt_intake_status": receipt["status"],
            "config_precheck_status": config["status"],
            "receipt_evidence_ref": receipt["evidence_ref"],
            "config_evidence_ref": config["evidence_ref"],
        },
        "schema_status": {
            "receipt_intake": receipt_schema_status,
            "config_precheck": config_schema_status,
        },
        "readiness_review_status": status,
        "hardware_sensor_hil_entry_readiness_review": status,
        "blocked_reason": _blocked_reason(status, receipt_issue, config_issue, weak_contract),
        "next_required_evidence": _next_required_evidence(status, receipt, config),
        "owner_handoff": _owner_handoff(status, receipt, config),
        "vendor_source_boundary": {
            "source": _repo_ref(Path(vendor_index)),
            "checked_readable_local_sources": [
                "docs/vendor/VENDOR_INDEX.md",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
            ],
            "index_listed_hardware_sources": [
                "docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf",
                "docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf",
            ],
            "vendor_boundary": "Orange Pi Zero 3 / WAVE ROVER / UART JSON / firmware references only",
            "project_2d_lidar_tof_hil_entry_proof": "not_proven",
        },
        "readiness_review_scope": [
            "receipt_source_vendor_sku_material_summary",
            "install_wiring_power_calibration_hil_entry_refs",
            "sensor_count_tof_channel_threshold_frame_safety_policy_precheck",
        ],
        "safe_copy": {},
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": list(NON_ACCESS_SCOPE),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact["safe_copy"] = _safe_copy(artifact)
    summary = _summary(artifact)
    artifact["readiness_review_summary"] = summary
    return artifact, summary, 0 if status == READY_REVIEW else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出目录自动创建，便于 sprint evidence 收集。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只生成 software-proof artifact；--help 无需 ROS2 环境。
    parser = argparse.ArgumentParser(
        description=(
            "Generate trashbot.hardware_sensor_hil_entry_readiness_review.v1 "
            "software-proof artifact from receipt intake and HIL-entry config precheck summaries."
        )
    )
    parser.add_argument("--receipt-intake-json", default="", help="hardware_sensor_procurement_receipt_intake artifact or summary JSON.")
    parser.add_argument("--config-precheck-json", default="", help="hardware_sensor_hil_entry_config_precheck artifact or summary JSON.")
    parser.add_argument("--evidence-ref", default="", help="Optional safe evidence_ref override; must match both source refs when provided.")
    parser.add_argument("--vendor-index", default=str(DEFAULT_VENDOR_INDEX), help="Vendor index path used only to record source boundary.")
    parser.add_argument("--output", default="", help="Write full hardware sensor HIL-entry readiness review artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact hardware sensor HIL-entry readiness review summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_sensor_hil_entry_readiness_review(
        args.receipt_intake_json or None,
        args.config_precheck_json or None,
        evidence_ref=args.evidence_ref,
        vendor_index=args.vendor_index,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_sensor_hil_entry_readiness_review: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"readiness_review_status: {artifact['readiness_review_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
