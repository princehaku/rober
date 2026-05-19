#!/usr/bin/env python3
"""生成 hardware_sensor_hil_entry_callback_intake fail-closed 回调材料入口。"""

from __future__ import annotations

# 设计约束 01：本 gate 只读 execution pack 和脱敏 callback material。
# 设计约束 02：本 gate 不读取真实传感器、ROS graph、Nav2 runtime 或串口。
# 设计约束 03：callback intake 只接受 summary/ref，不接受完整 artifact 复制。
# 设计约束 04：execution pack artifact、summary、nested wrapper 都只白名单消费。
# 设计约束 05：callback evidence_ref 必须与 execution pack 保持一致。
# 设计约束 06：vendor 资料只记录 source boundary，不证明真实采购或 HIL。
# 设计约束 07：输出必须保持 software_proof、hardware_material_pending。
# 设计约束 08：输出必须保持 not_proven、delivery_success=false。
# 设计约束 09：输出必须保持 primary_actions_enabled=false。
# 设计约束 10：任何 HIL pass、field pass、delivery success 文案都 fail closed。
# 设计约束 11：凭证、raw UART/serial、完整本机路径、checksum 都 fail closed。
# 设计约束 12：CLI --help 必须 dependency-free，适合 PC/Docker-only 环境。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.hardware_sensor_hil_entry_callback_intake.v1"
SUMMARY_SCHEMA = "trashbot.hardware_sensor_hil_entry_callback_intake_summary.v1"
EXECUTION_PACK_SCHEMA = "trashbot.hardware_sensor_hil_entry_execution_pack.v1"
EXECUTION_PACK_SUMMARY_SCHEMA = "trashbot.hardware_sensor_hil_entry_execution_pack_summary.v1"
CALLBACK_MATERIAL_SCHEMA = "trashbot.hardware_sensor_hil_entry_callback_materials.v1"
OPERATOR_RESULT_SCHEMA = "trashbot.hardware_sensor_hil_entry_operator_result.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate"
EXECUTION_PACK_BOUNDARY = "software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate"

READY_EXECUTION_PACK = "ready_for_hardware_sensor_hil_entry_execution_pack_not_proven"
READY_CALLBACK_INTAKE = "ready_for_hardware_sensor_hil_entry_callback_intake_not_proven"
BLOCKED_MISSING_EXECUTION_PACK = "blocked_missing_hardware_sensor_hil_entry_execution_pack"
BLOCKED_MISSING_CALLBACK_MATERIALS = "blocked_missing_hardware_sensor_hil_entry_callback_materials"
BLOCKED_EVIDENCE_REF_MISMATCH = "blocked_evidence_ref_mismatch"
BLOCKED_UNSUPPORTED_CALLBACK_INTAKE = "blocked_unsupported_hardware_sensor_hil_entry_callback_intake"
BLOCKED_UNSAFE_CALLBACK_COPY = "blocked_unsafe_hardware_sensor_hil_entry_callback_intake_copy"
BLOCKED_WEAK_EXECUTION_PACK_CONTRACT = "blocked_weak_hardware_sensor_hil_entry_execution_pack_contract"

# repo 相对路径进入 artifact，避免把开发机绝对路径扩散给 Robot/mobile。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

# callback material 使用固定类别，避免 field owner 随意扩展成 raw artifact。
REQUIRED_CALLBACK_MATERIALS = (
    "2d_lidar_sku_source_receipt",
    "tof_sku_source_receipt",
    "mounting",
    "wiring",
    "power",
    "calibration",
    "hil_entry_operator_result",
)

MATERIAL_ALIASES = {
    "lidar": "2d_lidar_sku_source_receipt",
    "2d_lidar": "2d_lidar_sku_source_receipt",
    "two_d_lidar": "2d_lidar_sku_source_receipt",
    "tof": "tof_sku_source_receipt",
    "operator_result": "hil_entry_operator_result",
    "hil_operator_result": "hil_entry_operator_result",
    "hil_entry_result": "hil_entry_operator_result",
}

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
    "objective5_external_proof",
    "delivery_success",
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

UNSAFE_SUCCESS_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bHIL\s+(passed|pass|success|complete|completed)\b"),
    re.compile(r"(?i)\bfield\s+(pass|passed|success|complete|completed)\b"),
    re.compile(r"(?i)\b(delivery|installed|wired|powered|calibrated)\s+(pass|passed|success|complete|completed|done)\b"),
    re.compile(r"(送达|交付|安装|接线|上电|电源|标定|HIL|现场).{0,16}(完成|通过|成功|已验证)"),
)

SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "[REDACTED_AUTH_HEADER]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)raw[_ -]?(UART|serial|JSON)"), "[REDACTED_RAW_MATERIAL]"),
    (re.compile(r"(?i)complete[_ -]?artifact"), "[REDACTED_ARTIFACT]"),
)


def _utc_now() -> str:
    # UTC 时间让 macOS 与 Docker-only evidence 输出可稳定比对。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, default: str = "") -> str:
    # 所有外发文本都脱敏，避免 summary 成为 raw material 搬运层。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text or default


def _repo_ref(path: Path) -> str:
    # source boundary 只输出 repo 相对路径，便于审计且不泄漏本机路径。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _safe_ref(value: Any, fallback: str = "missing") -> str:
    # evidence/material ref 必须是短引用；像路径时降级为 file:name 供后续阻断。
    text = _safe_text(value)
    if not text:
        return fallback
    path = Path(text)
    if path.is_absolute() or "/" in text or "\\" in text:
        return f"file:{path.name}"
    return text


def _is_safe_ref(value: str) -> bool:
    # safe evidence_ref 不能缺失、不能像路径、不能包含空白或 shell 片段。
    if not value or value.startswith("file:") or value in {"missing", "missing_execution_pack"}:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{2,120}", value))


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺输入返回 load_issue，让上层生成 blocked artifact 而不是抛异常。
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
    # 只接受 object，防止弱类型 wrapper 绕过 schema/boundary。
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    # 统一列表化，便于白名单截断和 summary 输出。
    return list(value) if isinstance(value, (list, tuple)) else []


def _safe_list(value: Any, limit: int = 12) -> list[str]:
    # summary 列表只保留短文本，不复制完整材料。
    items: list[str] = []
    for item in _list(value)[:limit]:
        safe = _safe_text(item)
        if safe:
            items.append(safe[:220])
    return items


def _encoded(value: Any) -> str:
    # JSON 编码同时扫描 key/value，捕获嵌套危险字段。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _string_values(value: Any) -> list[str]:
    # raw JSON 常藏在字符串字段里，必须单独扫描。
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_string_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_string_values(item))
        return values
    return []


def _has_raw_json_string(value: Any) -> bool:
    # callback 只能交 summary/ref，字符串里塞 JSON object 视为 raw copy。
    return any(re.search(r"\{\s*['\"][A-Za-z0-9_ -]+['\"]\s*:", item) for item in _string_values(value))


def _has_unsafe_copy(value: Any) -> bool:
    # 凭证、设备路径、本机完整路径、checksum、raw artifact 都阻断。
    encoded = _encoded(value)
    if any(token in encoded for token in FORBIDDEN_TOKENS):
        return True
    if re.search(r'(?i)"[^"]*(/Users/|/home/|/tmp/|/var/folders/)[^"]*"', encoded):
        return True
    return _has_raw_json_string(value)


def _has_success_claim(value: Any) -> bool:
    # 本 gate 是 callback intake，不允许把任何 pass/success 语义带入 ready。
    encoded = _encoded(_without_not_proven(value))
    return any(pattern.search(encoded) for pattern in UNSAFE_SUCCESS_PATTERNS)


def _without_not_proven(value: Any) -> Any:
    # not_proven 内会出现 pass 字样；成功扫描需排除这个安全字段。
    if isinstance(value, dict):
        return {key: _without_not_proven(item) for key, item in value.items() if key != "not_proven"}
    if isinstance(value, list):
        return [_without_not_proven(item) for item in value]
    return value


def _any_true_key(value: Any, key: str) -> bool:
    # 嵌套 true 字段同样会误导下游，必须递归阻断。
    if isinstance(value, dict):
        return any((k == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _source_execution_pack(payload: dict[str, Any]) -> dict[str, Any]:
    # 支持 artifact、summary，以及 Robot/mobile wrapper 内嵌 summary。
    if payload.get("schema") in {EXECUTION_PACK_SCHEMA, EXECUTION_PACK_SUMMARY_SCHEMA}:
        return payload
    if payload.get("schema"):
        return payload
    for key in ("execution_pack_summary", "hardware_sensor_hil_entry_execution_pack_summary", "summary"):
        nested = _dict(payload.get(key))
        if nested.get("schema") == EXECUTION_PACK_SUMMARY_SCHEMA:
            return nested
    return payload


def _normalize_execution_pack(payload: dict[str, Any]) -> dict[str, Any]:
    # 上游只读取合同字段，不复制 material_templates 的原始内容。
    source = _source_execution_pack(payload)
    nested = _dict(source.get("execution_pack_summary"))
    effective = nested if nested.get("schema") == EXECUTION_PACK_SUMMARY_SCHEMA else source
    status = _safe_text(
        effective.get("status")
        or effective.get("execution_pack_status")
        or effective.get("hardware_sensor_hil_entry_execution_pack")
        or source.get("execution_pack_status"),
        "missing_execution_pack_status",
    )
    return {
        "schema": _safe_text(effective.get("schema") or source.get("schema")),
        "full_schema": _safe_text(source.get("schema")),
        "evidence_boundary": _safe_text(effective.get("evidence_boundary") or source.get("evidence_boundary")),
        "source": _safe_text(effective.get("source") or source.get("source"), "missing"),
        "status": status,
        "evidence_ref": _safe_ref(effective.get("evidence_ref") or source.get("evidence_ref"), "missing_execution_pack"),
        "next_required_evidence": _safe_list(effective.get("next_required_evidence") or source.get("next_required_evidence"), 12),
        "owner_handoff": _owner_handoff(effective.get("owner_handoff") or source.get("owner_handoff")),
        "hardware_material_status": _safe_text(
            effective.get("hardware_material_status") or source.get("hardware_material_status"),
            "hardware_material_pending",
        ),
        "hardware_material_pending": effective.get("hardware_material_pending", source.get("hardware_material_pending")),
        "evidence_status": _safe_text(effective.get("evidence_status") or source.get("evidence_status"), "not_proven"),
        "delivery_success": effective.get("delivery_success", source.get("delivery_success")),
        "primary_actions_enabled": effective.get("primary_actions_enabled", source.get("primary_actions_enabled")),
    }


def _owner_handoff(value: Any) -> list[dict[str, str]]:
    # handoff 只保留人类 owner/action，不给 Robot 开任何动作口。
    handoff: list[dict[str, str]] = []
    for item in _list(value)[:8]:
        data = _dict(item)
        owner = _safe_text(data.get("owner"), "Hardware Infra Engineer")
        action = _safe_text(data.get("action"), "Keep hardware_material_pending until real HIL-entry evidence lands.")
        handoff.append({"owner": owner[:80], "action": action[:240]})
    return handoff


def _schema_status(load_issue: str, execution_pack: dict[str, Any]) -> str:
    # artifact/summary 都支持，但边界必须来自上一轮 execution_pack gate。
    if load_issue:
        return "not_loaded"
    schema_supported = execution_pack["schema"] in {EXECUTION_PACK_SCHEMA, EXECUTION_PACK_SUMMARY_SCHEMA}
    full_schema_supported = execution_pack["full_schema"] in {"", EXECUTION_PACK_SCHEMA, EXECUTION_PACK_SUMMARY_SCHEMA}
    boundary_supported = execution_pack["evidence_boundary"] == EXECUTION_PACK_BOUNDARY
    return "supported" if schema_supported and full_schema_supported and boundary_supported else "unsupported"


def _weak_contract_status(execution_pack: dict[str, Any], evidence_ref: str) -> str:
    # bool 必须是真 bool，字符串 false 在消费侧容易变成 truthy。
    if execution_pack["source"] != SOURCE:
        return "source"
    if not _is_safe_ref(evidence_ref):
        return "evidence_ref"
    for field in ("hardware_material_pending", "delivery_success", "primary_actions_enabled"):
        if not isinstance(execution_pack.get(field), bool):
            return field
    if execution_pack["delivery_success"] or execution_pack["primary_actions_enabled"]:
        return "unsafe_true_boolean"
    if execution_pack["hardware_material_pending"] is not True:
        return "hardware_material_pending_false"
    if execution_pack["hardware_material_status"] != "hardware_material_pending":
        return "hardware_material_status"
    if execution_pack["evidence_status"] != "not_proven":
        return "evidence_status"
    return ""


def _callback_source(payload: dict[str, Any]) -> dict[str, Any]:
    # callback 可直接给 materials，也可用固定 summary/materials wrapper。
    if "callback_materials" in payload:
        return payload
    if "materials" in payload:
        return payload
    for key in ("hardware_sensor_hil_entry_callback_materials", "callback_summary", "summary"):
        nested = _dict(payload.get(key))
        if nested:
            return nested
    return payload


def _callback_schema_status(load_issue: str, payload: dict[str, Any]) -> str:
    # callback 没有 schema 时按材料 map 处理；有 schema 时必须受支持。
    if load_issue:
        return "not_loaded"
    source = _callback_source(payload)
    schema = _safe_text(source.get("schema"))
    if not schema:
        return "supported"
    return "supported" if schema in {CALLBACK_MATERIAL_SCHEMA, OPERATOR_RESULT_SCHEMA} else "unsupported"


def _callback_evidence_refs(payload: dict[str, Any]) -> list[str]:
    # callback 里出现的 evidence_ref 都必须与 execution pack 一致。
    refs: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "evidence_ref":
                    refs.append(_safe_ref(item, "missing"))
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return refs


def _material_payload(payload: dict[str, Any]) -> dict[str, Any]:
    # 兼容 materials/callback_materials 两种轻量封装。
    source = _callback_source(payload)
    materials = _dict(source.get("callback_materials") or source.get("materials"))
    return materials or source


def _canonical_material_name(name: str) -> str:
    # 别名只映射到固定白名单，避免材料名扩散。
    return MATERIAL_ALIASES.get(name, name)


def _material_entry(name: str, value: Any) -> dict[str, str]:
    # accepted entry 只保留 category/ref/summary/status，不保留完整材料。
    data = _dict(value)
    if data:
        ref = data.get("ref") or data.get("reference") or data.get("source_ref") or data.get("receipt_ref") or data.get("summary")
        summary = data.get("summary") or data.get("status") or ref
    else:
        ref = value
        summary = value
    return {
        "material": name,
        "status": "accepted_sanitized_reference",
        "summary": _safe_text(summary, "provided_sanitized_reference")[:180],
        "ref": _safe_ref(ref, f"{name}_callback_ref"),
    }


def _material_lists(callback_payload: dict[str, Any]) -> tuple[list[dict[str, str]], list[str], list[dict[str, str]]]:
    # required material 缺失会 fail closed，但已给材料仍列出接受或拒绝原因。
    materials = _material_payload(callback_payload)
    normalized = {_canonical_material_name(str(key)): value for key, value in materials.items()}
    accepted: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    for name, value in normalized.items():
        if name not in REQUIRED_CALLBACK_MATERIALS:
            continue
        if value in (None, "", [], {}):
            continue
        if _has_unsafe_copy({name: value}) or _has_success_claim({name: value}):
            rejected.append({"material": name, "reason": "unsafe_raw_or_success_claim"})
            continue
        accepted.append(_material_entry(name, value))
    accepted_names = {item["material"] for item in accepted}
    rejected_names = {item["material"] for item in rejected}
    missing = [name for name in REQUIRED_CALLBACK_MATERIALS if name not in accepted_names and name not in rejected_names]
    return accepted, missing, rejected


def _operator_result_summary(callback_payload: dict[str, Any]) -> dict[str, str]:
    # operator result 只做摘要，不把现场日志、截图路径或完整 artifact 带出来。
    materials = _material_payload(callback_payload)
    value = materials.get("hil_entry_operator_result") or materials.get("operator_result") or materials.get("hil_operator_result")
    data = _dict(value)
    if not data:
        return {
            "status": "missing_hil_entry_operator_result",
            "summary": _safe_text(value, "No sanitized HIL-entry operator result callback material."),
        }
    return {
        "status": _safe_text(data.get("status"), "provided_sanitized_reference")[:120],
        "summary": _safe_text(data.get("summary") or data.get("ref"), "provided_sanitized_reference")[:240],
    }


def _callback_status(
    pack_load_issue: str,
    callback_load_issue: str,
    schema_status: str,
    callback_schema_status: str,
    weak_contract: str,
    pack_unsafe: bool,
    callback_unsafe: bool,
    success_claim: bool,
    evidence_ref_mismatch: bool,
    execution_pack: dict[str, Any],
    missing: list[str],
    rejected: list[dict[str, str]],
) -> str:
    # 决策顺序先挡上游合同，再挡 callback 材料，再看 ready 与缺口。
    if pack_load_issue:
        return BLOCKED_MISSING_EXECUTION_PACK
    if schema_status != "supported" or callback_schema_status == "unsupported":
        return BLOCKED_UNSUPPORTED_CALLBACK_INTAKE
    if weak_contract:
        return BLOCKED_WEAK_EXECUTION_PACK_CONTRACT
    if pack_unsafe or callback_unsafe or success_claim or rejected:
        return BLOCKED_UNSAFE_CALLBACK_COPY
    if evidence_ref_mismatch:
        return BLOCKED_EVIDENCE_REF_MISMATCH
    if execution_pack["status"] != READY_EXECUTION_PACK:
        return BLOCKED_WEAK_EXECUTION_PACK_CONTRACT
    if callback_load_issue or missing:
        return BLOCKED_MISSING_CALLBACK_MATERIALS
    return READY_CALLBACK_INTAKE


def _blocked_reason(status: str, details: dict[str, Any]) -> str:
    # blocked_reason 是短文本，便于 sprint closeout 和 Robot summary 引用。
    if status == READY_CALLBACK_INTAKE:
        return ""
    if status == BLOCKED_MISSING_EXECUTION_PACK:
        return "missing hardware_sensor_hil_entry_execution_pack artifact or summary"
    if status == BLOCKED_MISSING_CALLBACK_MATERIALS:
        return f"missing required callback materials: {', '.join(details['missing'])}"
    if status == BLOCKED_EVIDENCE_REF_MISMATCH:
        return "callback evidence_ref does not match execution pack evidence_ref"
    if status == BLOCKED_UNSUPPORTED_CALLBACK_INTAKE:
        return f"unsupported execution pack or callback schema/boundary: {details['schema_status']} / {details['callback_schema_status']}"
    if status == BLOCKED_WEAK_EXECUTION_PACK_CONTRACT:
        return f"weak or unsafe execution pack contract: {details['weak_contract'] or details['source_status']}"
    return "callback intake contains raw path, credential, raw serial/UART, checksum, complete artifact, success claim, or unsafe hardware proof copy"


def _next_required_evidence(status: str, missing: list[str], execution_pack: dict[str, Any]) -> list[str]:
    # 下一步只要求人类补材料，不触发 ROS、serial 或真实 HIL。
    if status == READY_CALLBACK_INTAKE:
        return [
            "Run hardware_sensor_hil_entry_callback_review_decision over this sanitized callback intake summary.",
            "Keep real HIL-entry, Nav2/SLAM field, near-field safety, and delivery claims blocked until reviewed evidence exists.",
        ]
    if missing:
        return [f"Provide sanitized {item} callback summary or reference under the same evidence_ref." for item in missing]
    return execution_pack["next_required_evidence"] or [
        "Regenerate a supported hardware_sensor_hil_entry_execution_pack summary before callback intake.",
        "Remove raw credentials, full paths, raw serial/UART, checksum, complete artifact copy, and pass/success wording.",
    ]


def _owner_handoff_for_status(status: str, execution_pack: dict[str, Any]) -> list[dict[str, str]]:
    # owner handoff 明确这是人工 review 阶段，不是 HIL 通过或控制放行。
    handoff = execution_pack["owner_handoff"][:5]
    if status == READY_CALLBACK_INTAKE:
        handoff.extend(
            [
                {
                    "owner": "Hardware Infra Engineer",
                    "action": "Review accepted callback materials for SKU/source/receipt, mounting, wiring, power, calibration, and operator-result sufficiency.",
                },
                {
                    "owner": "Product Manager / OKR Owner",
                    "action": "Keep PRRT_kwDOSWB9286CJ3tX and OKR wording blocked on real materials until review decision accepts them.",
                },
            ]
        )
    elif not handoff:
        handoff.append(
            {
                "owner": "Hardware Infra Engineer",
                "action": "Repair execution pack or sanitized callback material before any HIL-entry review decision.",
            }
        )
    return handoff[:8]


def _rerun_commands(pack_ref: str, callback_ref: str) -> list[str]:
    # rerun command 只包含 PC evidence gate，不包含真实串口、ROS 或 HIL 操作。
    pack_arg = pack_ref or "<hardware_sensor_hil_entry_execution_pack_json>"
    callback_arg = callback_ref or "<hardware_sensor_hil_entry_callback_material_json>"
    return [
        f"python3 pc-tools/evidence/hardware_sensor_hil_entry_callback_intake_gate.py --execution-pack-json {pack_arg} --callback-json {callback_arg} --summary-output <callback_intake_summary_json>",
        "python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_callback_intake_gate.py",
        'rg -n "hardware_sensor_hil_entry_callback_intake|software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate|hardware_material_pending|not_proven" pc-tools/evidence docs/product',
    ]


def _safe_copy(artifact: dict[str, Any]) -> dict[str, Any]:
    # safe_copy 是给下游展示的白名单摘要，不包含完整材料正文。
    return {
        "schema": SUMMARY_SCHEMA,
        "status": artifact["callback_intake_status"],
        "evidence_ref": artifact["evidence_ref"],
        "accepted_callback_materials": [item["material"] for item in artifact["accepted_callback_materials"]],
        "missing_required_materials": artifact["missing_required_materials"],
        "rejected_callback_materials": artifact["rejected_callback_materials"],
        "operator_result_summary": artifact["operator_result_summary"],
        "source": SOURCE,
        "evidence_status": "not_proven",
        "hardware_material_status": "hardware_material_pending",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # summary 是 Robot/mobile 只读消费面，字段必须短且 fail-closed。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": artifact["callback_intake_status"],
        "hardware_sensor_hil_entry_callback_intake": artifact["callback_intake_status"],
        "source_execution_pack_schema": artifact["source_execution_pack_schema"],
        "source_execution_pack_status": artifact["source_execution_pack_status"],
        "evidence_ref": artifact["evidence_ref"],
        "blocked_reason": artifact["blocked_reason"],
        "accepted_callback_materials": [item["material"] for item in artifact["accepted_callback_materials"]],
        "missing_required_materials": artifact["missing_required_materials"],
        "rejected_callback_materials": artifact["rejected_callback_materials"],
        "operator_result_summary": artifact["operator_result_summary"],
        "owner_handoff": artifact["owner_handoff"],
        "next_required_evidence": artifact["next_required_evidence"],
        "rerun_commands": artifact["rerun_commands"],
        "safe_copy": artifact["safe_copy"],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "boundary_note": "software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate; delivery_success=false; primary_actions_enabled=false; not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_hardware_sensor_hil_entry_callback_intake(
    execution_pack_json: str | Path | None = None,
    callback_json: str | Path | None = None,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 execution pack 与脱敏 callback material，生成 fail-closed intake。"""

    pack_path = Path(execution_pack_json) if execution_pack_json else None
    callback_path = Path(callback_json) if callback_json else None
    pack_payload, pack_load_issue = _read_json(pack_path)
    callback_payload, callback_load_issue = _read_json(callback_path)
    execution_pack = _normalize_execution_pack(pack_payload) if pack_payload else _normalize_execution_pack({})
    safe_ref = _safe_ref(evidence_ref or execution_pack["evidence_ref"], "missing_execution_pack")
    schema_status = _schema_status(pack_load_issue, execution_pack)
    callback_schema_status = _callback_schema_status(callback_load_issue, callback_payload)
    weak_contract = "" if pack_load_issue or schema_status != "supported" else _weak_contract_status(execution_pack, safe_ref)
    accepted, missing, rejected = _material_lists(callback_payload)
    callback_refs = [ref for ref in _callback_evidence_refs(callback_payload) if ref != "missing"]
    evidence_ref_mismatch = bool(callback_refs and any(ref != safe_ref for ref in callback_refs))
    pack_unsafe = bool(pack_payload and _has_unsafe_copy(pack_payload))
    callback_unsafe = bool(callback_payload and _has_unsafe_copy(callback_payload))
    success_claim = bool(
        (pack_payload and (_has_success_claim(pack_payload) or _any_true_key(pack_payload, "delivery_success") or _any_true_key(pack_payload, "primary_actions_enabled")))
        or (callback_payload and (_has_success_claim(callback_payload) or _any_true_key(callback_payload, "delivery_success") or _any_true_key(callback_payload, "primary_actions_enabled")))
    )
    status = _callback_status(
        pack_load_issue,
        callback_load_issue,
        schema_status,
        callback_schema_status,
        weak_contract,
        pack_unsafe,
        callback_unsafe,
        success_claim,
        evidence_ref_mismatch,
        execution_pack,
        missing,
        rejected,
    )
    source_pack_ref = _repo_ref(pack_path) if pack_path and pack_path.exists() else _safe_ref(pack_path, "missing")
    callback_ref = _repo_ref(callback_path) if callback_path and callback_path.exists() else _safe_ref(callback_path, "missing")
    details = {
        "missing": missing,
        "schema_status": schema_status,
        "callback_schema_status": callback_schema_status,
        "weak_contract": weak_contract,
        "source_status": execution_pack["status"],
    }

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "evidence_ref": safe_ref,
        "source_execution_pack_ref": source_pack_ref,
        "source_execution_pack_schema": execution_pack["schema"] or "missing",
        "source_execution_pack_boundary": execution_pack["evidence_boundary"] or "missing",
        "source_execution_pack_status": execution_pack["status"],
        "callback_material_ref": callback_ref,
        "schema_status": schema_status,
        "callback_schema_status": callback_schema_status,
        "weak_contract": weak_contract,
        "callback_intake_status": status,
        "hardware_sensor_hil_entry_callback_intake": status,
        "blocked_reason": _blocked_reason(status, details),
        "accepted_callback_materials": accepted,
        "missing_required_materials": missing,
        "rejected_callback_materials": rejected,
        "operator_result_summary": _operator_result_summary(callback_payload),
        "owner_handoff": _owner_handoff_for_status(status, execution_pack),
        "next_required_evidence": _next_required_evidence(status, missing, execution_pack),
        "rerun_commands": _rerun_commands(source_pack_ref, callback_ref),
        "vendor_source_boundary": {
            "source": _repo_ref(DEFAULT_VENDOR_INDEX),
            "checked_readable_local_sources": [
                "docs/vendor/VENDOR_INDEX.md",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
            ],
            "review_thread_context": "PRRT_kwDOSWB9286CJ3tX",
            "vendor_boundary": "Orange Pi Zero 3 / WAVE ROVER / UART JSON / firmware/vendor app source boundary only",
            "project_2d_lidar_tof_mounting_wiring_power_calibration_hil_proof": "not_proven",
        },
        "non_access_scope": [
            "physical_installation",
            "sensor_driver_runtime",
            "ros_graph",
            "serial_uart",
            "hardware_bus",
            "nav2_runtime",
            "hil_rig",
            "field_run",
            "delivery_execution",
            "objective5_external_cloud",
        ],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact["safe_copy"] = _safe_copy(artifact)
    summary = _summary(artifact)
    artifact["callback_intake_summary"] = summary
    return artifact, summary, 0 if status == READY_CALLBACK_INTAKE else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出目录自动创建，方便 sprint evidence bundle 收集。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只生成 software-proof metadata，不访问真实硬件或 HIL。
    parser = argparse.ArgumentParser(
        description="Generate trashbot.hardware_sensor_hil_entry_callback_intake.v1 from an execution pack and sanitized callback materials."
    )
    parser.add_argument("--execution-pack-json", default="", help="Previous hardware_sensor_hil_entry_execution_pack artifact/summary/wrapper JSON.")
    parser.add_argument("--callback-json", default="", help="Sanitized callback material JSON with refs/summaries only.")
    parser.add_argument("--evidence-ref", default="", help="Optional safe evidence_ref override.")
    parser.add_argument("--output", default="", help="Write full HIL-entry callback intake artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact HIL-entry callback intake summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_sensor_hil_entry_callback_intake(
        args.execution_pack_json or None,
        args.callback_json or None,
        evidence_ref=args.evidence_ref,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_sensor_hil_entry_callback_intake: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"callback_intake_status: {artifact['callback_intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
