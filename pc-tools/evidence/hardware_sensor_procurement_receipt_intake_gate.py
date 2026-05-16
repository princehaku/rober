#!/usr/bin/env python3
"""生成 hardware_sensor_procurement_receipt_intake fail-closed 收货回填入口。"""

from __future__ import annotations

# 设计约束 01：本文件只做 PC metadata gate，不连接真实采购系统。
# 设计约束 02：本文件只做 PC metadata gate，不读取真实仓储或物流系统。
# 设计约束 03：本文件只做 PC metadata gate，不打开传感器驱动或 ROS graph。
# 设计约束 04：本文件只做 PC metadata gate，不访问串口、UART 或 WAVE ROVER 下位机。
# 设计约束 05：本文件只接收脱敏 receipt/source/vendor/SKU 等材料摘要或引用。
# 设计约束 06：receipt intake ready 只表示材料形状可继续人工评审。
# 设计约束 07：receipt intake ready 不代表真实采购完成。
# 设计约束 08：receipt intake ready 不代表真实安装、接线、电源或标定完成。
# 设计约束 09：receipt intake ready 不代表真实 HIL entry、route pass 或 delivery success。
# 设计约束 10：缺 execution pack 时必须 fail closed。
# 设计约束 11：unsupported execution pack schema 必须 fail closed。
# 设计约束 12：unsupported execution pack boundary 必须 fail closed。
# 设计约束 13：缺 receipt/source/vendor/SKU 任一关键材料必须 fail closed。
# 设计约束 14：输入出现 success/control/HIL/O5 外部 proof 断言必须 fail closed。
# 设计约束 15：输入出现凭证、token、OSS AK/SK、DB/queue URL 必须 fail closed。
# 设计约束 16：输入出现 raw serial/UART path 或完整本机路径必须 fail closed。
# 设计约束 17：输入出现 checksum、raw JSON 或 complete artifact copy 必须 fail closed。
# 设计约束 18：输出 accepted_materials 只保留字段名、状态和安全引用。
# 设计约束 19：输出 rejected_materials 只保留字段名和拒绝原因。
# 设计约束 20：summary 是 Robot/mobile 消费面，不能复制完整 receipt 材料。
# 设计约束 21：vendor_source_boundary 只说明资料来源，不扩大为传感器采购证据。
# 设计约束 22：docs/vendor/VENDOR_INDEX.md 必须进入输出和 rg 验收面。
# 设计约束 23：Orange Pi / WAVE ROVER 资料不证明项目 2D LiDAR 或 ToF 已采购。
# 设计约束 24：所有状态必须保持 software_proof、not_proven。
# 设计约束 25：所有状态必须保持 delivery_success=false。
# 设计约束 26：所有状态必须保持 primary_actions_enabled=false。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema 常量明确区分上游 execution pack 与本轮 receipt intake 输出。
SCHEMA = "trashbot.hardware_sensor_procurement_receipt_intake.v1"
SUMMARY_SCHEMA = "trashbot.hardware_sensor_procurement_receipt_intake_summary.v1"
EXECUTION_PACK_SCHEMA = "trashbot.hardware_sensor_procurement_execution_pack.v1"
EXECUTION_PACK_SUMMARY_SCHEMA = "trashbot.hardware_sensor_procurement_execution_pack_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_sensor_procurement_receipt_intake_gate"
EXECUTION_PACK_BOUNDARY = "software_proof_docker_hardware_sensor_procurement_execution_pack_gate"

# repo 相对路径用于输出来源，不让本机绝对路径进入 artifact/summary。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

READY_RECEIPT_INTAKE = "ready_for_hardware_sensor_procurement_receipt_intake_not_proven"
BLOCKED_MISSING_EXECUTION_PACK = "blocked_missing_hardware_sensor_procurement_execution_pack"
BLOCKED_UNSUPPORTED_EXECUTION_PACK = "blocked_unsupported_hardware_sensor_procurement_execution_pack"
BLOCKED_EXECUTION_PACK_NOT_READY = "blocked_hardware_sensor_procurement_execution_pack_not_ready"
BLOCKED_MISSING_RECEIPT_MATERIALS = "blocked_missing_hardware_sensor_procurement_receipt_materials"
BLOCKED_UNSAFE_RECEIPT_COPY = "blocked_unsafe_hardware_sensor_procurement_receipt_intake_copy"
BLOCKED_WEAK_CONTRACT = "blocked_weak_hardware_sensor_procurement_execution_pack_contract"

# 关键材料是 receipt intake 的最低入口；其余材料可缺失但必须进入 missing_materials。
REQUIRED_MATERIALS = ("receipt", "source", "vendor", "sku")
OPTIONAL_MATERIALS = ("cost", "install", "wiring", "power", "calibration", "hil_entry")
ALL_MATERIALS = REQUIRED_MATERIALS + OPTIONAL_MATERIALS

# not_proven 列表让下游不会把材料回填误读成硬件履约完成。
NOT_PROVEN = (
    "real_receipt_accepted_by_procurement_system",
    "real_vendor_source_accepted",
    "real_2d_lidar_procured",
    "real_tof_procured",
    "real_installation",
    "real_wiring",
    "real_power_budget_verified",
    "real_calibration",
    "real_sensor_hil_entry_pass",
    "real_nav2_slam_field_pass",
    "real_route_or_elevator_field_pass",
    "objective5_external_proof",
    "delivery_success",
)

# forbidden token 扫描原始输入；命中后 fail closed，而不是仅靠输出脱敏兜底。
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
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "/dev/cu.",
    "/dev/tty.",
    "checksum",
    "raw JSON",
    "raw_json",
    "complete artifact",
    "Traceback",
)

# 成功文案必须阻断，因为本 gate 只能表达材料回填形状，不表达履约成功。
UNSAFE_SUCCESS_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bo5.{0,24}(external|公网|oss|cdn|db|queue).{0,24}(proof|pass|ready|完成)\b"),
    re.compile(r"(?i)\b(receipt|procurement|purchased|installed|wired|calibrated|hil|field)\s+(pass|passed|complete|completed|success|done)\b"),
    re.compile(r"(?i)(采购|收货|安装|接线|电源|标定|HIL|公网|外部云).{0,16}(完成|通过|成功|已验证)"),
)

# 脱敏规则只服务输出白名单；输入安全仍由 forbidden/success 扫描决定。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "[REDACTED_AUTH_HEADER]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)raw[_ -]?json"), "[REDACTED_RAW_JSON]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
)


def _utc_now() -> str:
    # UTC 时间让 Docker 与 macOS 生成的 evidence bundle 稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, default: str = "") -> str:
    # 所有外发文本都先脱敏，再进入白名单字段。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text or default


def _safe_ref(value: Any, fallback: str = "missing") -> str:
    # 允许材料引用，但完整路径只降级为文件名级别引用。
    text = _safe_text(value)
    if not text:
        return fallback
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _repo_ref(path: Path) -> str:
    # vendor/source boundary 固定输出 repo 相对路径，便于审计。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺文件是 blocked 状态，不让 JSON 异常中断 Product closeout。
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
    # 只接受 object，避免弱类型 wrapper 绕过 schema/boundary 校验。
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    # 上游字段允许缺失，统一列表化便于白名单截断。
    return list(value) if isinstance(value, (list, tuple)) else []


def _safe_list(value: Any, limit: int = 12) -> list[str]:
    # summary 只保留短列表，避免复制完整材料包。
    return [_safe_text(item) for item in _list(value)[:limit] if _safe_text(item)]


def _encoded(value: Any) -> str:
    # JSON 编码同时扫描键和值，捕获嵌套危险字段。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _string_values(value: Any) -> list[str]:
    # raw JSON 泄漏通常藏在字符串字段里，不能用整体 JSON 编码误伤正常结构。
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for item in value.values():
            strings.extend(_string_values(item))
        return strings
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(_string_values(item))
        return strings
    return []


def _has_raw_json_string(value: Any) -> bool:
    # 字符串中出现 JSON object 片段说明材料没有先做脱敏摘要化。
    return any(re.search(r"\{\s*['\"][A-Za-z0-9_ -]+['\"]\s*:", item) for item in _string_values(value))


def _has_forbidden_copy(value: Any) -> bool:
    # raw JSON 字符串、完整路径、凭证和设备路径不允许进入本 gate。
    encoded = _encoded(value)
    if any(token in encoded for token in FORBIDDEN_COPY):
        return True
    if re.search(r'(?i)"[^"]*(/Users/|/home/|/tmp/|/var/folders/)[^"]*"', encoded):
        return True
    return _has_raw_json_string(value)


def _has_success_claim(value: Any) -> bool:
    # 成功断言可能藏在 note、owner_handoff 或 receipt 摘要里。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in UNSAFE_SUCCESS_PATTERNS)


def _any_true_key(value: Any, key: str) -> bool:
    # 递归挡住下游动作或成功字段被嵌套放行。
    if isinstance(value, dict):
        return any((k == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    # 支持直接 artifact、直接 summary，以及 diagnostics wrapper 内嵌 summary。
    if payload.get("schema") in {EXECUTION_PACK_SCHEMA, EXECUTION_PACK_SUMMARY_SCHEMA}:
        return payload
    if payload.get("schema"):
        return payload
    for key in ("execution_pack_summary", "hardware_sensor_procurement_execution_pack_summary", "summary"):
        nested = _dict(payload.get(key))
        if nested.get("schema") == EXECUTION_PACK_SUMMARY_SCHEMA:
            return nested
    return payload


def _normalize_execution_pack(payload: dict[str, Any]) -> dict[str, Any]:
    # 上游 execution pack 只读取白名单字段，不复制 material_templates 的完整正文。
    source = _source_payload(payload)
    nested_summary = _dict(source.get("execution_pack_summary"))
    effective = nested_summary if nested_summary.get("schema") == EXECUTION_PACK_SUMMARY_SCHEMA else source
    status = _safe_text(
        effective.get("status")
        or effective.get("execution_pack_status")
        or effective.get("hardware_sensor_procurement_execution_pack")
        or source.get("execution_pack_status"),
        "missing_execution_pack_status",
    )
    return {
        "schema": _safe_text(effective.get("schema") or source.get("schema")),
        "full_schema": _safe_text(source.get("schema")),
        "evidence_boundary": _safe_text(effective.get("evidence_boundary") or source.get("evidence_boundary")),
        "status": status,
        "execution_pack_status": status,
        "evidence_ref": _safe_ref(effective.get("evidence_ref") or source.get("evidence_ref"), "missing_execution_pack"),
        "next_required_evidence": _safe_list(effective.get("next_required_evidence") or source.get("next_required_evidence")),
        "owner_handoff": _owner_handoff(effective.get("owner_handoff") or source.get("owner_handoff")),
        "hardware_material_status": _safe_text(
            effective.get("hardware_material_status") or source.get("hardware_material_status"),
            "hardware_material_pending",
        ),
        "hardware_material_pending": effective.get("hardware_material_pending", source.get("hardware_material_pending")),
        "delivery_success": effective.get("delivery_success", source.get("delivery_success")),
        "primary_actions_enabled": effective.get("primary_actions_enabled", source.get("primary_actions_enabled")),
    }


def _owner_handoff(value: Any) -> list[dict[str, str]]:
    # handoff 只保留 owner/action，避免把 raw 材料说明扩散到 Robot/mobile。
    handoff: list[dict[str, str]] = []
    for item in _list(value)[:8]:
        if not isinstance(item, dict):
            continue
        handoff.append(
            {
                "owner": _safe_text(item.get("owner"), "Hardware Infra Engineer"),
                "action": _safe_text(item.get("action"), "Keep hardware_material_pending until real evidence is accepted."),
            }
        )
    return handoff


def _schema_status(load_issue: str, execution_pack: dict[str, Any]) -> str:
    # artifact/summary 都支持，但证据边界必须来自上一轮 execution_pack gate。
    if load_issue:
        return "not_loaded"
    schema_supported = execution_pack["schema"] in {EXECUTION_PACK_SCHEMA, EXECUTION_PACK_SUMMARY_SCHEMA}
    full_schema_supported = execution_pack["full_schema"] in {"", EXECUTION_PACK_SCHEMA, EXECUTION_PACK_SUMMARY_SCHEMA}
    boundary_supported = execution_pack["evidence_boundary"] == EXECUTION_PACK_BOUNDARY
    return "supported" if schema_supported and full_schema_supported and boundary_supported else "unsupported"


def _weak_contract_status(execution_pack: dict[str, Any]) -> str:
    # bool 字段必须是真 bool，防止字符串 false 在 JS/Python 消费时被误判。
    for field in ("hardware_material_pending", "delivery_success", "primary_actions_enabled"):
        if not isinstance(execution_pack.get(field), bool):
            return field
    if execution_pack["delivery_success"] or execution_pack["primary_actions_enabled"]:
        return "unsafe_true_boolean"
    if execution_pack["hardware_material_pending"] is not True:
        return "hardware_material_pending_false"
    if execution_pack["hardware_material_status"] != "hardware_material_pending":
        return "hardware_material_status"
    return ""


def _material_entry(name: str, value: Any) -> dict[str, str]:
    # 材料 entry 只输出 summary/ref，不承诺真实性或验收完成。
    if isinstance(value, dict):
        ref = value.get("ref") or value.get("reference") or value.get("source_ref") or value.get("summary")
        summary = value.get("summary") or value.get("status") or ref
    else:
        ref = value
        summary = value
    return {
        "material": name,
        "status": "accepted_sanitized_reference",
        "summary": _safe_text(summary, "provided_sanitized_reference")[:160],
        "ref": _safe_ref(ref, f"{name}_material_ref"),
    }


def _material_lists(materials: dict[str, Any]) -> tuple[list[dict[str, str]], list[str], list[dict[str, str]]]:
    # required 与 optional 分开判定，让关键材料缺失时 fail closed，辅助材料继续列入待补。
    accepted: list[dict[str, str]] = []
    missing: list[str] = []
    rejected: list[dict[str, str]] = []
    for name in ALL_MATERIALS:
        value = materials.get(name)
        if value in (None, "", [], {}):
            missing.append(name)
            continue
        if _has_forbidden_copy({name: value}) or _has_success_claim({name: value}):
            rejected.append({"material": name, "reason": "unsafe_raw_or_success_claim"})
            continue
        accepted.append(_material_entry(name, value))
    return accepted, missing, rejected


def _receipt_status(
    load_issue: str,
    schema_status: str,
    weak_contract: str,
    unsafe_copy: bool,
    success_claim: bool,
    execution_pack: dict[str, Any],
    missing: list[str],
    rejected: list[dict[str, str]],
) -> str:
    # 决策顺序先校验上游执行包，再校验 receipt 材料安全和关键字段。
    if load_issue:
        return BLOCKED_MISSING_EXECUTION_PACK if load_issue == "missing" else BLOCKED_UNSUPPORTED_EXECUTION_PACK
    if schema_status != "supported":
        return BLOCKED_UNSUPPORTED_EXECUTION_PACK
    if weak_contract:
        return BLOCKED_WEAK_CONTRACT
    if unsafe_copy or success_claim or rejected:
        return BLOCKED_UNSAFE_RECEIPT_COPY
    if execution_pack["execution_pack_status"] != "ready_for_hardware_sensor_procurement_execution_pack_not_proven":
        return BLOCKED_EXECUTION_PACK_NOT_READY
    if any(name in missing for name in REQUIRED_MATERIALS):
        return BLOCKED_MISSING_RECEIPT_MATERIALS
    return READY_RECEIPT_INTAKE


def _blocked_reason(status: str, load_issue: str, schema_status: str, weak_contract: str, missing: list[str]) -> str:
    # blocked_reason 保持短文本，避免 closeout 复制 raw 材料。
    if status == READY_RECEIPT_INTAKE:
        return ""
    if status == BLOCKED_MISSING_EXECUTION_PACK:
        return "missing hardware_sensor_procurement_execution_pack artifact or summary"
    if status == BLOCKED_UNSUPPORTED_EXECUTION_PACK:
        return f"unsupported execution pack contract: load_issue={load_issue or 'none'} schema_status={schema_status}"
    if status == BLOCKED_WEAK_CONTRACT:
        return f"weak or unsafe execution pack boolean contract: {weak_contract}"
    if status == BLOCKED_EXECUTION_PACK_NOT_READY:
        return "source execution pack is not ready_for_hardware_sensor_procurement_execution_pack_not_proven"
    if status == BLOCKED_MISSING_RECEIPT_MATERIALS:
        return f"missing required receipt materials: {', '.join([item for item in missing if item in REQUIRED_MATERIALS])}"
    return "receipt intake contains raw path, credential, control topic, checksum, raw JSON, success claim, or unsafe hardware proof claim"


def _next_required_evidence(status: str, missing: list[str], execution_pack: dict[str, Any]) -> list[str]:
    # next_required_evidence 是人工履约材料，不是机器人控制动作。
    if status == BLOCKED_MISSING_EXECUTION_PACK:
        return [
            "Generate hardware_sensor_procurement_execution_pack artifact or summary first.",
            "Keep hardware_material_pending until a supported execution pack exists.",
        ]
    if status in {BLOCKED_UNSUPPORTED_EXECUTION_PACK, BLOCKED_WEAK_CONTRACT, BLOCKED_UNSAFE_RECEIPT_COPY}:
        return [
            "Regenerate supported execution pack and sanitized receipt materials without credentials, raw paths, raw JSON, or success/control claims.",
            "Use software_proof_docker_hardware_sensor_procurement_execution_pack_gate as the only accepted source boundary.",
        ]
    if status == BLOCKED_EXECUTION_PACK_NOT_READY:
        return execution_pack["next_required_evidence"] or [
            "Resolve execution pack blockers before accepting receipt intake materials.",
        ]
    if status == BLOCKED_MISSING_RECEIPT_MATERIALS:
        return [f"Provide sanitized {item} summary or reference." for item in missing]
    return [
        "Run procurement review over accepted receipt/source/vendor/SKU materials before changing hardware boundary.",
        "Fill install, wiring, power, calibration, and HIL-entry evidence before any installation or HIL claim.",
        "Keep Product OKR wording at software_proof / not_proven until real materials are independently reviewed.",
    ]


def _owner_handoff_for_status(status: str, execution_pack: dict[str, Any]) -> list[dict[str, str]]:
    # owner handoff 明确下一步是材料审核，不是触发 ROS、HIL 或 mobile control。
    base = execution_pack["owner_handoff"][:6]
    if status == READY_RECEIPT_INTAKE:
        return base + [
            {
                "owner": "Hardware Infra Engineer",
                "action": "Review accepted receipt/source/vendor/SKU references and request missing install/wiring/power/calibration/HIL-entry materials.",
            },
            {
                "owner": "Product Manager / OKR Owner",
                "action": "Keep OKR and sprint closeout at software_proof / not_proven until real receipt, install, calibration, and HIL evidence is reviewed.",
            },
        ]
    return base or [
        {
            "owner": "Hardware Infra Engineer",
            "action": "Repair execution pack or sanitized receipt materials before hardware status changes.",
        },
        {
            "owner": "Product Manager / OKR Owner",
            "action": "Do not count this blocked receipt intake as procurement, installation, calibration, HIL, O5 external proof, or delivery progress.",
        },
    ]


def _summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # summary 是 Robot/mobile 的最小只读面，不包含完整材料或 raw receipt。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": artifact["receipt_intake_status"],
        "receipt_intake_status": artifact["receipt_intake_status"],
        "hardware_sensor_procurement_receipt_intake": artifact["receipt_intake_status"],
        "source_execution_pack_schema": artifact["source_execution_pack_schema"],
        "source_execution_pack_status": artifact["source_execution_pack_status"],
        "evidence_ref": artifact["evidence_ref"],
        "blocked_reason": artifact["blocked_reason"],
        "accepted_materials": [item["material"] for item in artifact["accepted_materials"]],
        "missing_materials": artifact["missing_materials"],
        "rejected_materials": artifact["rejected_materials"],
        "next_required_evidence": artifact["next_required_evidence"],
        "owner_handoff": artifact["owner_handoff"],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "boundary_note": "software_proof only; delivery_success=false; primary_actions_enabled=false; not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_hardware_sensor_procurement_receipt_intake(
    execution_pack_json: str | Path | None = None,
    receipt_json: str | Path | None = None,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 execution pack 与脱敏 receipt materials，生成 fail-closed receipt intake。"""

    pack_path = Path(execution_pack_json) if execution_pack_json else None
    materials_path = Path(receipt_json) if receipt_json else None
    pack_payload, load_issue = _read_json(pack_path)
    materials_payload, materials_issue = _read_json(materials_path)
    execution_pack = (
        _normalize_execution_pack(pack_payload)
        if pack_payload
        else {
            "schema": "",
            "full_schema": "",
            "evidence_boundary": "",
            "status": "missing",
            "execution_pack_status": "missing_execution_pack",
            "evidence_ref": "missing_execution_pack",
            "next_required_evidence": [],
            "owner_handoff": [],
            "hardware_material_status": "hardware_material_pending",
            "hardware_material_pending": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    schema_status = _schema_status(load_issue, execution_pack)
    weak_contract = "" if load_issue or schema_status != "supported" else _weak_contract_status(execution_pack)
    accepted, missing, rejected = _material_lists(materials_payload)
    unsafe_copy = bool((pack_payload and _has_forbidden_copy(pack_payload)) or (materials_payload and _has_forbidden_copy(materials_payload)))
    success_claim = bool(
        (pack_payload and (_has_success_claim(pack_payload) or _any_true_key(pack_payload, "delivery_success") or _any_true_key(pack_payload, "primary_actions_enabled")))
        or (materials_payload and (_has_success_claim(materials_payload) or _any_true_key(materials_payload, "delivery_success") or _any_true_key(materials_payload, "primary_actions_enabled")))
    )
    if materials_issue and not materials_payload:
        missing = list(ALL_MATERIALS)
    status = _receipt_status(load_issue, schema_status, weak_contract, unsafe_copy, success_claim, execution_pack, missing, rejected)
    safe_ref = _safe_ref(evidence_ref or execution_pack["evidence_ref"], "missing_execution_pack")

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "evidence_ref": safe_ref,
        "source_execution_pack_ref": _repo_ref(pack_path) if pack_path and pack_path.exists() else _safe_ref(pack_path, "missing"),
        "source_execution_pack_schema": execution_pack["schema"] or "missing",
        "source_execution_pack_boundary": execution_pack["evidence_boundary"] or "missing",
        "source_execution_pack_status": execution_pack["execution_pack_status"],
        "receipt_material_ref": _repo_ref(materials_path) if materials_path and materials_path.exists() else _safe_ref(materials_path, "missing"),
        "schema_status": schema_status,
        "weak_contract": weak_contract,
        "receipt_intake_status": status,
        "hardware_sensor_procurement_receipt_intake": status,
        "blocked_reason": _blocked_reason(status, load_issue, schema_status, weak_contract, missing),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "next_required_evidence": _next_required_evidence(status, missing, execution_pack),
        "owner_handoff": _owner_handoff_for_status(status, execution_pack),
        "vendor_source_boundary": {
            "source": _repo_ref(DEFAULT_VENDOR_INDEX),
            "checked_readable_local_sources": [
                "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
            ],
            "index_listed_hardware_sources": [
                "docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf",
                "docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf",
            ],
            "project_2d_lidar_tof_procurement_proof": "not_proven",
        },
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "procurement_system",
            "warehouse_or_shipping",
            "physical_installation",
            "sensor_driver_runtime",
            "ros_graph",
            "serial_uart",
            "hardware_bus",
            "nav2_runtime",
            "hil",
            "objective5_external_cloud",
            "delivery_execution",
        ],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = _summary(artifact)
    artifact["receipt_intake_summary"] = summary
    return artifact, summary, 0 if status == READY_RECEIPT_INTAKE else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出目录自动创建，便于 sprint evidence 收集。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只生成 software-proof artifact，不访问真实硬件或外部系统。
    parser = argparse.ArgumentParser(
        description="Generate hardware_sensor_procurement_receipt_intake fail-closed software-proof artifact."
    )
    parser.add_argument("--execution-pack-json", default="", help="Previous hardware_sensor_procurement_execution_pack artifact or summary JSON.")
    parser.add_argument("--receipt-json", default="", help="Sanitized receipt/source/vendor/SKU/cost/install/wiring/power/calibration/HIL-entry material JSON.")
    parser.add_argument("--evidence-ref", default="", help="Optional safe evidence_ref override for downstream summaries.")
    parser.add_argument("--output", default="", help="Write full hardware sensor procurement receipt intake artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact hardware sensor procurement receipt intake summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_sensor_procurement_receipt_intake(
        args.execution_pack_json or None,
        args.receipt_json or None,
        evidence_ref=args.evidence_ref,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_sensor_procurement_receipt_intake: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"receipt_intake_status: {artifact['receipt_intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
