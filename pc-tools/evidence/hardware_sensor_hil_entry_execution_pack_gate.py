#!/usr/bin/env python3
"""生成 hardware_sensor_hil_entry_execution_pack fail-closed 执行包。"""

from __future__ import annotations

# 设计约束 01：本 gate 只读上一轮 readiness review，不读取真实硬件。
# 设计约束 02：本 gate 不打开串口、不访问 ROS graph、不访问 sensor driver。
# 设计约束 03：execution pack 只是材料模板，不代表采购、接线、标定或 HIL 通过。
# 设计约束 04：readiness review 必须来自受支持 schema 和 evidence boundary。
# 设计约束 05：summary / wrapper 输入只能白名单消费，不能复制 raw artifact。
# 设计约束 06：vendor 资料只作为 source boundary，不证明真实采购或安装。
# 设计约束 07：输出必须保持 software_proof、hardware_material_pending 和 not_proven。
# 设计约束 08：输出必须保持 delivery_success=false 和 primary_actions_enabled=false。
# 设计约束 09：任何 success/HIL passed/field pass/采购完成/接线完成文案都 fail closed。
# 设计约束 10：任何凭证、本机路径、raw serial/UART path、raw JSON copy 都 fail closed。
# 设计约束 11：safe evidence_ref 缺失或像路径时 fail closed，避免证据串线。
# 设计约束 12：CLI --help 必须 dependency-free，可在 PC/Docker-only 环境运行。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.hardware_sensor_hil_entry_execution_pack.v1"
SUMMARY_SCHEMA = "trashbot.hardware_sensor_hil_entry_execution_pack_summary.v1"
READINESS_SCHEMA = "trashbot.hardware_sensor_hil_entry_readiness_review.v1"
READINESS_SUMMARY_SCHEMA = "trashbot.hardware_sensor_hil_entry_readiness_review_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate"
READINESS_BOUNDARY = "software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate"

READY_READINESS = "ready_for_hardware_sensor_hil_entry_readiness_review_not_proven"
READY_EXECUTION_PACK = "ready_for_hardware_sensor_hil_entry_execution_pack_not_proven"
BLOCKED_MISSING_READINESS = "blocked_missing_hardware_sensor_hil_entry_readiness_review"
BLOCKED_UNSUPPORTED_READINESS = "blocked_unsupported_hardware_sensor_hil_entry_readiness_review"
BLOCKED_READINESS_NOT_READY = "blocked_hardware_sensor_hil_entry_readiness_not_ready"
BLOCKED_UNSAFE_COPY = "blocked_unsafe_hardware_sensor_hil_entry_execution_pack_copy"
BLOCKED_WEAK_CONTRACT = "blocked_weak_hardware_sensor_hil_entry_readiness_contract"

# repo 相对引用用于审计资料来源，避免绝对路径扩散给 Robot/mobile。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

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
    "delivery_success",
)

MATERIAL_TEMPLATES = (
    {
        "name": "2d_lidar_sku_source_receipt.md",
        "category": "2d_lidar_sku_source_receipt",
        "required_fields": ["sku", "vendor_source", "receipt_or_po_ref", "acceptance_owner"],
    },
    {
        "name": "tof_sku_source_receipt.md",
        "category": "tof_sku_source_receipt",
        "required_fields": ["sku", "vendor_source", "receipt_or_po_ref", "channel_count_source"],
    },
    {
        "name": "mounting_plan.md",
        "category": "mounting_plan",
        "required_fields": ["2d_lidar_mount", "tof_mount", "mechanical_clearance_ref", "review_owner"],
    },
    {
        "name": "wiring_power_plan.md",
        "category": "wiring_power_plan",
        "required_fields": ["power_budget", "wire_route", "fuse_or_protection", "orange_pi_wave_rover_boundary"],
    },
    {
        "name": "calibration_plan.md",
        "category": "calibration_plan",
        "required_fields": ["2d_lidar_calibration_steps", "tof_calibration_steps", "frame_id_checks", "threshold_checks"],
    },
    {
        "name": "hil_entry_operator_checklist.md",
        "category": "hil_entry_operator_checklist",
        "required_fields": ["bench_check", "install_check", "calibration_check", "stop_condition", "owner_signoff"],
    },
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
    re.compile(r"(?i)\bHIL\s+(passed|pass|success|complete|completed)\b"),
    re.compile(r"(?i)\bfield\s+(pass|passed|success|complete|completed)\b"),
    re.compile(r"(?i)\b(procurement|purchase|installed|wired|calibrated)\s+(done|success|complete|completed)\b"),
    re.compile(r"(采购|接线|安装|标定|HIL|现场).{0,12}(完成|通过|成功|已验证)"),
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
    # UTC 时间让 macOS 与 Docker 输出可以稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _encoded(value: Any) -> str:
    # JSON 编码同时覆盖 key/value，便于统一做安全扫描。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 外发文本全部脱敏，summary 不承载 raw artifact 或本机信息。
    text = default if value is None else str(value).strip()
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text or default


def _repo_ref(path: Path) -> str:
    # 文档和 vendor 来源输出 repo 相对路径，避免泄漏开发机绝对路径。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _safe_ref(value: Any, fallback: str = "missing") -> str:
    # evidence_ref 必须是短引用；像路径的值降级后会被 safe-ref 检查阻断。
    text = _safe_text(value)
    if not text:
        return fallback
    path = Path(text)
    if path.is_absolute() or "/" in text or "\\" in text:
        return f"file:{path.name}"
    return text


def _is_safe_ref(value: str) -> bool:
    # safe evidence_ref 不能缺失、不能像路径、不能包含凭证或空白。
    if not value or value.startswith("file:") or value == "missing":
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{2,120}", value))


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺输入是 blocked 状态，不能把异常栈传播给手机端。
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
    # 只接受 object summary，避免弱类型绕过 schema/boundary。
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    # 输入缺数组时统一成空数组，便于白名单截断。
    return list(value) if isinstance(value, (list, tuple)) else []


def _safe_list(value: Any, limit: int = 10) -> list[str]:
    # summary 只保留短文本，不复制完整上游材料。
    items: list[str] = []
    for item in _list(value)[:limit]:
        safe = _safe_text(item)
        if safe:
            items.append(safe[:220])
    return items


def _owner_handoff(value: Any) -> list[dict[str, str]]:
    # handoff 只保留 owner/action，不变成机器人动作或原始证据复制。
    handoff: list[dict[str, str]] = []
    for item in _list(value)[:8]:
        data = _dict(item)
        owner = _safe_text(data.get("owner"), "Hardware Infra Engineer")
        action = _safe_text(data.get("action"), "Keep hardware_material_pending until real evidence lands.")
        handoff.append({"owner": owner[:80], "action": action[:240]})
    return handoff


def _without_not_proven(value: Any) -> Any:
    # not_proven 内会出现 pass 字样；扫描成功断言时排除这个安全语义字段。
    if isinstance(value, dict):
        return {key: _without_not_proven(item) for key, item in value.items() if key != "not_proven"}
    if isinstance(value, list):
        return [_without_not_proven(item) for item in value]
    return value


def _has_unsafe_copy(value: Any) -> bool:
    # raw path、凭证、控制 topic、串口路径和完整 artifact 都必须阻断。
    encoded = _encoded(value)
    if any(token in encoded for token in FORBIDDEN_TOKENS):
        return True
    return bool(re.search(r'(?i)"[^"]*(/Users/|/home/|/tmp/|/var/folders/)[^"]*"', encoded))


def _has_success_claim(value: Any) -> bool:
    # 本 gate 只能输出 not_proven execution pack，任何成功断言都阻断。
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


def _source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    # 支持直接 artifact、直接 summary，以及 Robot/mobile wrapper 内嵌 summary。
    if payload.get("schema") in {READINESS_SCHEMA, READINESS_SUMMARY_SCHEMA}:
        return payload
    if payload.get("schema"):
        return payload
    for key in ("readiness_review_summary", "hardware_sensor_hil_entry_readiness_review_summary", "summary"):
        nested = _dict(payload.get(key))
        if nested.get("schema") == READINESS_SUMMARY_SCHEMA:
            return nested
    return payload


def _normalize_readiness(payload: dict[str, Any]) -> dict[str, Any]:
    # 只消费上一轮 readiness review 白名单字段，不传递 raw source artifact。
    source = _source_payload(payload)
    nested = _dict(source.get("readiness_review_summary"))
    effective = nested if nested.get("schema") == READINESS_SUMMARY_SCHEMA else source
    status = _safe_text(
        effective.get("status")
        or effective.get("readiness_review_status")
        or effective.get("hardware_sensor_hil_entry_readiness_review")
        or source.get("readiness_review_status")
        or source.get("hardware_sensor_hil_entry_readiness_review"),
        "missing_readiness_review_status",
    )
    return {
        "schema": _safe_text(effective.get("schema") or source.get("schema")),
        "full_schema": _safe_text(source.get("schema")),
        "evidence_boundary": _safe_text(effective.get("evidence_boundary") or source.get("evidence_boundary")),
        "source": _safe_text(effective.get("source") or source.get("source"), "missing"),
        "status": status,
        "evidence_ref": _safe_ref(effective.get("evidence_ref") or source.get("evidence_ref"), "missing"),
        "source_statuses": _dict(effective.get("source_statuses") or source.get("source_statuses")),
        "next_required_evidence": _safe_list(effective.get("next_required_evidence") or source.get("next_required_evidence"), 12),
        "owner_handoff": _owner_handoff(effective.get("owner_handoff") or source.get("owner_handoff")),
        "not_proven": _safe_list(effective.get("not_proven") or source.get("not_proven"), 20),
        "hardware_material_pending": effective.get("hardware_material_pending", source.get("hardware_material_pending")),
        "hardware_material_status": _safe_text(
            effective.get("hardware_material_status") or source.get("hardware_material_status"),
            "hardware_material_pending",
        ),
        "delivery_success": effective.get("delivery_success", source.get("delivery_success")),
        "primary_actions_enabled": effective.get("primary_actions_enabled", source.get("primary_actions_enabled")),
    }


def _schema_status(load_issue: str, review: dict[str, Any]) -> str:
    # 顶层 schema 和 summary schema 都必须受支持，避免 unsupported wrapper bypass。
    if load_issue:
        return "not_loaded"
    schema_supported = review["schema"] in {READINESS_SCHEMA, READINESS_SUMMARY_SCHEMA}
    full_schema_supported = review["full_schema"] in {"", READINESS_SCHEMA, READINESS_SUMMARY_SCHEMA}
    boundary_supported = review["evidence_boundary"] == READINESS_BOUNDARY
    return "supported" if schema_supported and full_schema_supported and boundary_supported else "unsupported"


def _weak_contract(review: dict[str, Any], safe_ref: str) -> str:
    # bool 字段必须是真 bool；字符串 false 在下游容易变成 truthy。
    if review["source"] != SOURCE:
        return "source"
    if not _is_safe_ref(safe_ref):
        return "evidence_ref"
    for field in ("hardware_material_pending", "delivery_success", "primary_actions_enabled"):
        if not isinstance(review.get(field), bool):
            return field
    if review["delivery_success"] or review["primary_actions_enabled"]:
        return "unsafe_true_boolean"
    if review["hardware_material_pending"] is not True:
        return "hardware_material_pending"
    if review["hardware_material_status"] != "hardware_material_pending":
        return "hardware_material_status"
    return ""


def _execution_status(
    load_issue: str,
    schema_status: str,
    weak_contract: str,
    unsafe_copy: bool,
    success_claim: bool,
    review: dict[str, Any],
) -> str:
    # 决策顺序先挡输入合同和安全，再看 readiness 是否 ready/not_proven。
    if load_issue:
        return BLOCKED_MISSING_READINESS if load_issue == "missing" else BLOCKED_UNSUPPORTED_READINESS
    if schema_status != "supported":
        return BLOCKED_UNSUPPORTED_READINESS
    if unsafe_copy or success_claim:
        return BLOCKED_UNSAFE_COPY
    if weak_contract:
        return BLOCKED_WEAK_CONTRACT
    if review["status"] != READY_READINESS:
        return BLOCKED_READINESS_NOT_READY
    return READY_EXECUTION_PACK


def _blocked_reason(status: str, load_issue: str, schema_status: str, weak_contract: str, review: dict[str, Any]) -> str:
    # blocked_reason 保持短文本，方便 sprint closeout 引用。
    if status == READY_EXECUTION_PACK:
        return ""
    if status == BLOCKED_MISSING_READINESS:
        return "missing hardware_sensor_hil_entry_readiness_review artifact or summary"
    if status == BLOCKED_UNSUPPORTED_READINESS:
        return f"unsupported readiness review contract: load_issue={load_issue or 'none'} schema_status={schema_status}"
    if status == BLOCKED_WEAK_CONTRACT:
        return f"weak or unsafe readiness boolean/source contract: {weak_contract}"
    if status == BLOCKED_UNSAFE_COPY:
        return "source readiness review contains raw path, credential, control topic, raw serial/UART path, raw JSON, or success claim"
    return f"source readiness review is not ready: {review['status']}"


def _material_templates(evidence_ref: str) -> list[dict[str, Any]]:
    # 模板继承同一 evidence_ref，但不填充真实 SKU、receipt、接线或 HIL 结论。
    return [
        {
            "name": item["name"],
            "category": item["category"],
            "required_fields": list(item["required_fields"]),
            "evidence_ref": evidence_ref,
            "status": "template_pending_real_hardware_material",
        }
        for item in MATERIAL_TEMPLATES
    ]


def _next_required_evidence(status: str, review: dict[str, Any]) -> list[str]:
    # 下一步只描述人工补证据动作，不暗示机器人控制或 HIL pass。
    if status == READY_EXECUTION_PACK:
        return [
            "Fill 2D LiDAR SKU/source/receipt material under the same safe evidence_ref.",
            "Fill ToF SKU/source/receipt material under the same safe evidence_ref.",
            "Attach mounting plan, wiring/power plan, calibration plan, and HIL-entry operator checklist before any HIL claim.",
            "Re-run readiness review and execution pack gates after real material changes.",
        ]
    return review["next_required_evidence"] or [
        "Regenerate a supported hardware_sensor_hil_entry_readiness_review summary before creating an execution pack.",
        "Keep software_proof / hardware_material_pending / not_proven until readiness review is ready.",
    ]


def _owner_handoff_for_status(status: str, review: dict[str, Any]) -> list[dict[str, str]]:
    # owner handoff 是人类履约分工，不给 Robot/mobile 开控制口。
    handoff = review["owner_handoff"][:6]
    if status == READY_EXECUTION_PACK:
        handoff.extend(
            [
                {
                    "owner": "Hardware Infra Engineer",
                    "action": "Collect 2D LiDAR and ToF SKU/source/receipt, mounting, wiring/power, calibration, and HIL-entry checklist evidence.",
                },
                {
                    "owner": "Product Manager / OKR Owner",
                    "action": "Keep closeout wording at software_proof/not_proven until real procurement, installation, calibration, and HIL evidence exists.",
                },
            ]
        )
    elif not handoff:
        handoff.append(
            {
                "owner": "Hardware Infra Engineer",
                "action": "Repair the readiness review source before using this execution pack.",
            }
        )
    return handoff[:8]


def _rerun_commands(source_ref: str) -> list[str]:
    # 命令只重跑 PC evidence gate，不包含串口调试、ROS 控制或真实采购系统操作。
    review_arg = source_ref or "<hardware_sensor_hil_entry_readiness_review_json>"
    return [
        "python3 pc-tools/evidence/hardware_sensor_hil_entry_readiness_review_gate.py --receipt-intake-json <receipt_json> --config-precheck-json <config_json> --summary-output <readiness_summary_json>",
        f"python3 pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py --readiness-review-json {review_arg} --summary-output <execution_pack_summary_json>",
        "python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_execution_pack_gate.py",
        'rg -n "hardware_sensor_hil_entry_execution_pack|software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate|hardware_material_pending|not_proven" pc-tools/evidence docs/product',
    ]


def _summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # summary 是 Robot/mobile phone-safe 只读面，不复制完整 artifact。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": artifact["execution_pack_status"],
        "hardware_sensor_hil_entry_execution_pack": artifact["execution_pack_status"],
        "source_readiness_schema": artifact["source_readiness_schema"],
        "source_readiness_status": artifact["source_readiness_status"],
        "evidence_ref": artifact["evidence_ref"],
        "blocked_reason": artifact["blocked_reason"],
        "material_templates": [item["name"] for item in artifact["material_templates"]],
        "next_required_evidence": artifact["next_required_evidence"],
        "owner_handoff": artifact["owner_handoff"],
        "rerun_commands": artifact["rerun_commands"][:4],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "boundary_note": "software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate; delivery_success=false; primary_actions_enabled=false; not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_hardware_sensor_hil_entry_execution_pack(
    readiness_review_json: str | Path | None = None,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 readiness review artifact/summary，生成 fail-closed HIL-entry execution pack。"""

    review_path = Path(readiness_review_json) if readiness_review_json else None
    payload, load_issue = _read_json(review_path)
    review = _normalize_readiness(payload) if payload else _normalize_readiness({})
    safe_ref = _safe_ref(evidence_ref or review["evidence_ref"], "missing")
    schema_status = _schema_status(load_issue, review)
    weak_contract = "" if load_issue or schema_status != "supported" else _weak_contract(review, safe_ref)
    unsafe_copy = bool(payload and _has_unsafe_copy(payload))
    success_claim = bool(
        payload
        and (
            _has_success_claim(payload)
            or _any_true_key(payload, "delivery_success")
            or _any_true_key(payload, "primary_actions_enabled")
        )
    )
    status = _execution_status(load_issue, schema_status, weak_contract, unsafe_copy, success_claim, review)
    source_ref = _repo_ref(review_path) if review_path and review_path.exists() else _safe_ref(review_path, "missing")

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "evidence_ref": safe_ref,
        "source_readiness_ref": source_ref,
        "source_readiness_schema": review["schema"] or "missing",
        "source_readiness_boundary": review["evidence_boundary"] or "missing",
        "source_readiness_status": review["status"],
        "source_statuses": review["source_statuses"],
        "schema_status": schema_status,
        "weak_contract": weak_contract,
        "execution_pack_status": status,
        "hardware_sensor_hil_entry_execution_pack": status,
        "blocked_reason": _blocked_reason(status, load_issue, schema_status, weak_contract, review),
        "material_templates": _material_templates(safe_ref),
        "next_required_evidence": _next_required_evidence(status, review),
        "owner_handoff": _owner_handoff_for_status(status, review),
        "rerun_commands": _rerun_commands(source_ref),
        "vendor_source_boundary": {
            "source": _repo_ref(DEFAULT_VENDOR_INDEX),
            "checked_readable_local_sources": [
                "docs/vendor/VENDOR_INDEX.md",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
            ],
            "vendor_boundary": "Orange Pi Zero 3 / WAVE ROVER / UART JSON / firmware/vendor app source boundary only",
            "project_2d_lidar_tof_procurement_install_calibration_hil_proof": "not_proven",
        },
        "non_access_scope": [
            "procurement_system",
            "physical_installation",
            "sensor_driver_runtime",
            "ros_graph",
            "serial_uart",
            "hardware_bus",
            "nav2_runtime",
            "hil",
            "field_run",
            "delivery_execution",
        ],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = _summary(artifact)
    artifact["execution_pack_summary"] = summary
    return artifact, summary, 0 if status == READY_EXECUTION_PACK else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出目录自动创建，便于 sprint evidence bundle 收集。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只生成 software-proof metadata，不访问真实硬件或 HIL。
    parser = argparse.ArgumentParser(
        description="Generate trashbot.hardware_sensor_hil_entry_execution_pack.v1 from a readiness review JSON."
    )
    parser.add_argument("--readiness-review-json", default="", help="Previous hardware_sensor_hil_entry_readiness_review artifact/summary/wrapper JSON.")
    parser.add_argument("--evidence-ref", default="", help="Optional safe evidence_ref override.")
    parser.add_argument("--output", default="", help="Write full HIL-entry execution pack artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact HIL-entry execution pack summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_sensor_hil_entry_execution_pack(
        args.readiness_review_json or None,
        evidence_ref=args.evidence_ref,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_sensor_hil_entry_execution_pack: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"execution_pack_status: {artifact['execution_pack_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
