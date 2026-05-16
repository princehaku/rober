#!/usr/bin/env python3
"""生成 hardware_sensor_procurement_review_decision fail-closed 证据 artifact。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema 名称是 Robot diagnostics / mobile 只读接入的稳定 contract。
SCHEMA = "trashbot.hardware_sensor_procurement_review_decision.v1"
SUMMARY_SCHEMA = "trashbot.hardware_sensor_procurement_review_decision_summary.v1"
INTAKE_SCHEMA = "trashbot.hardware_sensor_procurement_intake_gate.v1"
INTAKE_SUMMARY_SCHEMA = "trashbot.hardware_sensor_procurement_intake_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_sensor_procurement_review_decision_gate"
INTAKE_BOUNDARY = "software_proof_docker_hardware_sensor_procurement_intake_gate"

# repo 相对路径用于生成安全 evidence_ref，避免 summary 泄漏本机绝对路径。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

BLOCKED_MISSING_INTAKE = "blocked_missing_hardware_sensor_procurement_intake"
BLOCKED_UNSUPPORTED_INTAKE = "blocked_unsupported_hardware_sensor_procurement_intake"
BLOCKED_MISSING_PROCUREMENT = "blocked_missing_procurement_materials"
BLOCKED_MISSING_INSTALLATION = "blocked_missing_mounting_wiring_calibration"
READY_DECISION = "ready_for_procurement_review_not_proven"

PROCUREMENT_FIELD_HINTS = (
    "sku",
    "vendor",
    "source_document",
    "vendor_source",
    "procurement_status",
    "channel_count",
    "channel_count_source",
    "sensor_material",
)
INSTALLATION_FIELD_HINTS = (
    "mounting_plan",
    "mounting",
    "wiring_plan",
    "wiring",
    "power_budget",
    "power",
    "calibration_plan",
    "calibration",
    "hil_entry_material",
    "hil_entry",
)
REQUIRED_SAFE_TERMS = (
    "hardware_sensor_procurement_intake",
    "2D LiDAR",
    "ToF",
    "docs/vendor/VENDOR_INDEX.md",
    "hardware_material_pending",
    "not_proven",
)

# 这些字段必须一直保守输出，review decision 不是采购完成或 HIL 通过。
NOT_PROVEN = (
    "real_2d_lidar_procured",
    "real_2d_lidar_vendor_source_accepted",
    "real_2d_lidar_mounted_wired_calibrated",
    "real_tof_procured",
    "real_tof_channel_count_source_accepted",
    "real_tof_mounted_wired_calibrated",
    "real_sensor_hil_entry_pass",
    "real_nav2_slam_field_pass",
    "real_near_field_safety_gate_pass",
    "delivery_success",
)

# 只要上游材料里出现控制放行或成功断言，本 gate 必须 fail closed。
UNSAFE_SUCCESS_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(2d lidar|lidar|tof).{0,24}(field|hil|calibration).{0,12}pass(ed)?\b"),
)


def _utc_now() -> str:
    # UTC 时间让不同 Docker / macOS 主机生成的 artifact 可直接排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, default: str = "") -> str:
    # 所有下游输出先转字符串，避免把复杂对象或 None 原样泄漏给 mobile。
    if value is None:
        return default
    if isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    return text or default


def _safe_ref(path: Path | None, fallback: str = "missing") -> str:
    # evidence_ref 只保留 repo 相对路径或文件名；这也是 phone-safe 的最小引用。
    if path is None:
        return fallback
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺 intake 是正常 blocked 状态，返回结构化原因而不是 traceback。
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
    # 兼容 artifact 内嵌 summary、diagnostics wrapper 和直接 summary 输入。
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    # 上游可能输出 tuple/list，也可能缺字段；统一成 list 便于 blocker 分类。
    return list(value) if isinstance(value, (list, tuple)) else []


def _has_success_claim(payload: dict[str, Any]) -> bool:
    # 序列化扫描能覆盖嵌套 note 中的危险成功文案。
    text = json.dumps(payload, ensure_ascii=False)
    return any(pattern.search(text) for pattern in UNSAFE_SUCCESS_PATTERNS)


def _effective_intake(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先读取 summary，因为 Robot/mobile 也应只消费 sanitized summary。
    nested = (
        _dict(payload.get("review_summary"))
        or _dict(payload.get("hardware_sensor_procurement_intake_summary"))
        or _dict(payload.get("summary"))
    )
    if nested.get("schema") == INTAKE_SUMMARY_SCHEMA:
        return nested
    return payload


def _schema_status(payload: dict[str, Any], effective: dict[str, Any]) -> str:
    # 只接受上一轮 intake gate 的 artifact 或 summary，避免误吃其他 evidence。
    top_schema = _safe_text(payload.get("schema"))
    schema = _safe_text(effective.get("schema") or top_schema)
    boundary = _safe_text(effective.get("evidence_boundary") or payload.get("evidence_boundary"))
    source_boundary = _safe_text(effective.get("source_evidence_boundary") or payload.get("source_evidence_boundary"))
    if top_schema and top_schema not in {INTAKE_SCHEMA, INTAKE_SUMMARY_SCHEMA}:
        return "unsupported_schema"
    if schema not in {INTAKE_SCHEMA, INTAKE_SUMMARY_SCHEMA}:
        return "unsupported_schema"
    if boundary != INTAKE_BOUNDARY and source_boundary != INTAKE_BOUNDARY:
        return "unsupported_boundary"
    return "supported"


def _source_status(payload: dict[str, Any], effective: dict[str, Any]) -> str:
    # 上游 intake artifact/summary 的状态决定 review 是否进入 ready。
    return _safe_text(
        effective.get("status")
        or effective.get("hardware_sensor_procurement_intake")
        or payload.get("overall_status")
        or payload.get("hardware_sensor_procurement_intake"),
        default="missing_source_status",
    )


def _all_missing_fields(payload: dict[str, Any], effective: dict[str, Any]) -> tuple[list[str], list[str]]:
    # missing 与 placeholder 都会转成 blocker；placeholder 不应该被当成可采购材料。
    missing = [_safe_text(item) for item in _list(effective.get("missing_materials") or payload.get("missing_materials"))]
    placeholders = [
        _safe_text(item) for item in _list(effective.get("placeholder_materials") or payload.get("placeholder_materials"))
    ]
    return [item for item in missing if item], [item for item in placeholders if item]


def _sensor_gaps_from_summary(effective: dict[str, Any]) -> tuple[list[str], list[str]]:
    # 直接 summary 可能只给 sensor_materials 状态，这里补成字段级缺口。
    procurement: list[str] = []
    installation: list[str] = []
    for sensor in _list(effective.get("sensor_materials")):
        if not isinstance(sensor, dict):
            continue
        name = _safe_text(sensor.get("sensor"), "sensor")
        if sensor.get("sku_status") == "missing":
            procurement.append(f"{name}.sku")
        if sensor.get("vendor_source_status") == "missing":
            procurement.append(f"{name}.source_document")
        if _safe_text(sensor.get("procurement_status")) == "missing":
            procurement.append(f"{name}.procurement_status")
        if sensor.get("mounting_status") == "missing":
            installation.append(f"{name}.mounting_plan")
        if sensor.get("wiring_status") == "missing":
            installation.append(f"{name}.wiring_plan")
        if sensor.get("calibration_status") == "missing":
            installation.append(f"{name}.calibration_plan")
        if sensor.get("hil_entry_status") == "missing":
            installation.append(f"{name}.hil_entry_material")
        if name == "ToF" and sensor.get("channel_count_source_status") == "missing":
            procurement.append("ToF.channel_count_source")
    return procurement, installation


def _field_bucket(field: str) -> str:
    # 字段名驱动 owner handoff，比解析自然语言 note 更稳定。
    lowered = field.lower()
    if any(hint in lowered for hint in INSTALLATION_FIELD_HINTS):
        return "installation"
    if any(hint in lowered for hint in PROCUREMENT_FIELD_HINTS):
        return "procurement"
    return "procurement"


def _blockers(
    source_status: str,
    missing: list[str],
    placeholders: list[str],
    effective: dict[str, Any],
) -> list[dict[str, Any]]:
    # blocker 只描述补材料，不给任何机器人动作或硬件控制命令。
    procurement_fields: list[str] = []
    installation_fields: list[str] = []
    summary_procurement, summary_installation = _sensor_gaps_from_summary(effective)
    for field in missing + placeholders + summary_procurement + summary_installation:
        target = installation_fields if _field_bucket(field) == "installation" else procurement_fields
        if field not in target:
            target.append(field)

    blockers: list[dict[str, Any]] = []
    if source_status != "ready_for_hardware_sensor_procurement_review_not_proven" and not procurement_fields and not installation_fields:
        procurement_fields.append(source_status)
    if procurement_fields:
        blockers.append(
            {
                "category": "procurement_source_material",
                "status": "hardware_material_pending",
                "fields": procurement_fields,
                "owner": "Hardware Infra Engineer",
            }
        )
    if installation_fields:
        blockers.append(
            {
                "category": "mounting_wiring_power_calibration_hil_entry",
                "status": "hardware_material_pending",
                "fields": installation_fields,
                "owner": "Hardware Infra Engineer",
            }
        )
    return blockers


def _decision(load_issue: str, schema_status: str, blockers: list[dict[str, Any]]) -> str:
    # 决策枚举保持窄集合，方便 Robot diagnostics / mobile fail-closed 消费。
    if load_issue:
        return BLOCKED_MISSING_INTAKE if load_issue == "missing" else BLOCKED_UNSUPPORTED_INTAKE
    if schema_status != "supported":
        return BLOCKED_UNSUPPORTED_INTAKE
    categories = {blocker["category"] for blocker in blockers}
    if "procurement_source_material" in categories:
        return BLOCKED_MISSING_PROCUREMENT
    if "mounting_wiring_power_calibration_hil_entry" in categories:
        return BLOCKED_MISSING_INSTALLATION
    return READY_DECISION


def _next_required_evidence(decision: str, blockers: list[dict[str, Any]]) -> list[str]:
    # next_required_evidence 是下一轮履约清单，不是控制建议。
    if decision == BLOCKED_MISSING_INTAKE:
        return [
            "Run hardware_sensor_procurement_intake_gate.py with real 2D LiDAR and ToF SKU/source/procurement/install/calibration/HIL-entry materials.",
            "Attach source documents outside docs/vendor/VENDOR_INDEX.md because the current vendor index does not prove project 2D LiDAR or ToF procurement.",
        ]
    if decision == BLOCKED_UNSUPPORTED_INTAKE:
        return [
            "Regenerate a supported hardware_sensor_procurement_intake artifact or summary with schema trashbot.hardware_sensor_procurement_intake_gate.v1 or trashbot.hardware_sensor_procurement_intake_summary.v1.",
            "Remove delivery_success=true, primary_actions_enabled=true, HIL pass, or field pass claims before review.",
        ]
    items: list[str] = []
    for blocker in blockers:
        fields = ", ".join(blocker.get("fields", []))
        if blocker["category"] == "procurement_source_material":
            items.append(f"Provide concrete 2D LiDAR / ToF procurement/source material for: {fields}.")
        else:
            items.append(f"Provide mounting, wiring, power budget, calibration, and HIL entry material for: {fields}.")
    if not items:
        items.append("Product closeout may review the intake material shape, but hardware remains not_proven until real field/HIL evidence exists.")
    return items


def _owner_handoff(decision: str, blockers: list[dict[str, Any]]) -> list[dict[str, str]]:
    # handoff 明确 owner，不让 Product 或 mobile 误以为可以发起机器人动作。
    if decision == READY_DECISION:
        return [
            {
                "owner": "Product Manager / OKR Owner",
                "action": "Review procurement decision artifact and keep hardware_material_pending until real evidence lands.",
            },
            {
                "owner": "Hardware Infra Engineer",
                "action": "Prepare bench/HIL entry plan after source, mounting, wiring, power, and calibration materials are accepted.",
            },
        ]
    handoff: list[dict[str, str]] = []
    for blocker in blockers or [{"category": "intake_regeneration", "fields": [decision]}]:
        handoff.append(
            {
                "owner": "Hardware Infra Engineer",
                "action": f"Resolve {blocker['category']} fields: {', '.join(blocker.get('fields', []))}.",
            }
        )
    handoff.append(
        {
            "owner": "Product Manager / OKR Owner",
            "action": "Keep OKR and sprint closeout wording at software_proof / not_proven until the blockers are resolved.",
        }
    )
    return handoff


def _rerun_commands(intake_path: Path | None) -> list[str]:
    # 这些命令只重跑 PC gate 和围栏验证，不包含 ROS /cmd_vel、串口或 HIL 控制。
    intake_arg = _safe_ref(intake_path, "/tmp/hardware_sensor_procurement_intake.json")
    return [
        f"python3 pc-tools/evidence/hardware_sensor_procurement_intake_gate.py --intake-json {intake_arg} --summary-output /tmp/hardware_sensor_procurement_intake_summary.json",
        f"python3 pc-tools/evidence/hardware_sensor_procurement_review_decision_gate.py --intake-json {intake_arg} --summary-output /tmp/hardware_sensor_procurement_review_decision_summary.json",
        "python3 pc-tools/evidence/test_hardware_sensor_procurement_review_decision_gate.py",
        'rg -n "hardware_sensor_procurement_review_decision|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools docs/product',
        "git diff --check -- pc-tools/evidence pc-tools/README.md docs/product/production_hardware_boundary.md",
    ]


def _summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # summary 是下游唯一应该长期消费的结构，避免 raw intake 泄漏到 phone。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source_schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": artifact["review_decision"],
        "hardware_sensor_procurement_review_decision": artifact["review_decision"],
        "source_intake_schema": artifact["source_intake_schema"],
        "source_intake_status": artifact["source_intake_status"],
        "evidence_ref": artifact["evidence_ref"],
        "review_decision": artifact["review_decision"],
        "blockers": artifact["blockers"],
        "next_required_evidence": artifact["next_required_evidence"],
        "owner_handoff": artifact["owner_handoff"],
        "rerun_commands": artifact["rerun_commands"],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "boundary_note": "software_proof only; delivery_success=false; primary_actions_enabled=false; not_proven",
    }


def build_hardware_sensor_procurement_review_decision(
    intake_json: str | Path | None = None,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取上一轮 intake artifact/summary，生成 fail-closed review decision。"""

    intake_path = Path(intake_json) if intake_json else None
    payload, load_issue = _read_json(intake_path)
    effective = _effective_intake(payload)
    schema_status = "missing" if load_issue else _schema_status(payload, effective)
    if not load_issue and _has_success_claim(payload):
        schema_status = "unsafe_success_or_control_claim"
    source_status = _source_status(payload, effective) if not load_issue else BLOCKED_MISSING_INTAKE
    missing, placeholders = _all_missing_fields(payload, effective) if not load_issue else ([], [])
    blockers = [] if load_issue or schema_status != "supported" else _blockers(source_status, missing, placeholders, effective)
    decision = _decision(load_issue, schema_status, blockers)
    safe_ref = _safe_text(evidence_ref) or _safe_ref(intake_path, "missing_hardware_sensor_procurement_intake")

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "evidence_ref": safe_ref,
        "source_intake_ref": _safe_ref(intake_path),
        "source_intake_schema": _safe_text(effective.get("schema") or payload.get("schema"), "missing"),
        "source_intake_boundary": _safe_text(effective.get("evidence_boundary") or payload.get("evidence_boundary"), "missing"),
        "source_intake_status": source_status,
        "schema_status": schema_status,
        "review_decision": decision,
        "hardware_sensor_procurement_review_decision": decision,
        "blockers": blockers,
        "next_required_evidence": _next_required_evidence(decision, blockers),
        "owner_handoff": _owner_handoff(decision, blockers),
        "rerun_commands": _rerun_commands(intake_path),
        "vendor_source_boundary": {
            "source": _safe_ref(DEFAULT_VENDOR_INDEX),
            "coverage": "Orange Pi/WAVE ROVER/UART/camera only; no verified project 2D LiDAR or ToF source",
            "lidar_tof_vendor_proof": "not_proven",
        },
        "required_safe_terms": list(REQUIRED_SAFE_TERMS),
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "serial_uart",
            "hardware_bus",
            "sensor_driver_runtime",
            "nav2_runtime",
            "hil",
            "delivery_execution",
        ],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = _summary(artifact)
    artifact["review_summary"] = summary
    return artifact, summary, 0 if decision == READY_DECISION else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出路径自动创建，便于 sprint evidence bundle 一次性落盘。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只做材料复核，不访问真实 UART、传感器、Nav2 或 HIL。
    parser = argparse.ArgumentParser(
        description="Generate hardware_sensor_procurement_review_decision fail-closed software-proof artifact."
    )
    parser.add_argument("--intake-json", default="", help="Previous hardware_sensor_procurement_intake artifact or summary JSON.")
    parser.add_argument("--evidence-ref", default="", help="Optional safe evidence_ref override for downstream summaries.")
    parser.add_argument("--output", default="", help="Write full hardware sensor procurement review decision artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact hardware sensor procurement review decision summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_sensor_procurement_review_decision(
        args.intake_json or None,
        evidence_ref=args.evidence_ref,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_sensor_procurement_review_decision: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
