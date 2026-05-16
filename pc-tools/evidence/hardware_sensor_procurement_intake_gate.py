#!/usr/bin/env python3
"""生成 hardware_sensor_procurement_intake fail-closed 证据 artifact。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema 名称作为 Robot diagnostics / mobile 后续只读消费的稳定入口。
SCHEMA = "trashbot.hardware_sensor_procurement_intake_gate.v1"
SUMMARY_SCHEMA = "trashbot.hardware_sensor_procurement_intake_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_sensor_procurement_intake_gate"

# 当前 vendor index 是硬件事实入口，但不包含项目 2D LiDAR / ToF 的实测来源。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"
DEFAULT_BOUNDARY_MD = REPO_ROOT / "docs" / "product" / "production_hardware_boundary.md"

READY_STATUS = "ready_for_hardware_sensor_procurement_review_not_proven"
BLOCKED_MISSING_INTAKE = "blocked_missing_hardware_sensor_procurement_intake"
BLOCKED_INVALID_JSON = "blocked_invalid_hardware_sensor_procurement_intake_json"
BLOCKED_MISSING_VENDOR_BOUNDARY = "blocked_missing_vendor_boundary"
BLOCKED_MISSING_REQUIRED_MATERIALS = "blocked_missing_required_sensor_materials"
BLOCKED_PLACEHOLDER_MATERIALS = "blocked_placeholder_sensor_materials"
BLOCKED_SUCCESS_OR_CONTROL_CLAIM = "blocked_success_or_control_claim"

# gate 只处理 LiDAR / ToF 采购材料，monocular camera 继续由 product boundary 说明。
REQUIRED_SENSORS = ("2D LiDAR", "ToF")
COMMON_REQUIRED_FIELDS = (
    "sku",
    "vendor",
    "source_document",
    "procurement_status",
    "mounting_plan",
    "wiring_plan",
    "power_budget",
    "calibration_plan",
    "hil_entry_material",
)
TOF_REQUIRED_FIELDS = ("channel_count",)

# 这些字段必须保守输出，避免 intake 被误读成真实采购、安装或 HIL 通过。
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

# placeholder 清单偏保守；硬件 intake 宁可 blocked，也不能把草稿当履约材料。
PLACEHOLDER_PATTERNS = (
    re.compile(r"^\s*$"),
    re.compile(r"(?i)\b(tbd|todo|placeholder|unknown|n/a|na|pending source|待定|占位|未知|后补)\b"),
    re.compile(r"(?i)\bexample(\.com|/|$)"),
)

# product 文档允许讨论 success rate，但本 gate 不允许出现 true/pass 型验收断言。
SUCCESS_OR_CONTROL_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(2d lidar|lidar|tof).{0,24}(field|hil|calibration).{0,12}pass(ed)?\b"),
)

VENDOR_BOUNDARY_PHRASES = (
    "docs/vendor/VENDOR_INDEX.md",
    "Orange Pi Zero 3",
    "WAVE ROVER",
    "UART",
    "camera",
)


def _utc_now() -> str:
    # UTC 时间戳让不同开发机和 Docker 主机生成的证据可以直接排序。
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: Path) -> tuple[str, str]:
    # 读失败不抛异常；fail-closed artifact 比 traceback 更适合 sprint 留档。
    try:
        return path.expanduser().read_text(encoding="utf-8"), ""
    except FileNotFoundError:
        return "", "missing"
    except (OSError, UnicodeDecodeError):
        return "", "read_error"


def _safe_ref(path: Path) -> str:
    # 下游 summary 不传播本机绝对路径，只保留 repo 相对路径或文件名。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _safe_string(value: Any) -> str:
    # 所有人工填报字段统一转成字符串，便于做占位符和成功断言扫描。
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _is_placeholder(value: Any) -> bool:
    # 数字 0 不能直接按空字符串处理；ToF channel_count 会单独做范围校验。
    text = _safe_string(value)
    return any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS)


def _has_success_or_control_claim(payload: Any) -> bool:
    # 扫描序列化后的 payload，可以覆盖嵌套 note 中的危险成功文案。
    text = json.dumps(payload, ensure_ascii=False)
    return any(pattern.search(text) for pattern in SUCCESS_OR_CONTROL_PATTERNS)


def _load_intake(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺 intake 是当前预期状态：必须 blocked，等待真实 SKU/source/procurement 材料。
    if path is None:
        return {}, "missing"
    text, issue = _read_text(path)
    if issue:
        return {}, issue
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}, "invalid_json"
    if not isinstance(payload, dict):
        return {}, "invalid_json"
    return payload, ""


def _sensor_payload(payload: dict[str, Any], sensor: str) -> dict[str, Any]:
    # 兼容 sensors list 和 sensors mapping，方便后续采购表按不同工具导出。
    sensors = payload.get("sensors", {})
    if isinstance(sensors, dict):
        item = sensors.get(sensor, {})
        return item if isinstance(item, dict) else {}
    if isinstance(sensors, list):
        for item in sensors:
            if isinstance(item, dict) and item.get("sensor") == sensor:
                return item
    return {}


def _required_fields(sensor: str) -> tuple[str, ...]:
    # ToF 比 LiDAR 多 channel_count，因为 PR #5 P2 明确要求 ToF channel count 来源。
    if sensor == "ToF":
        return COMMON_REQUIRED_FIELDS + TOF_REQUIRED_FIELDS
    return COMMON_REQUIRED_FIELDS


def _validate_channel_count(sensor_data: dict[str, Any]) -> list[str]:
    # channel_count 可先标记 product target pending，但不能伪装成 vendor-proven 事实。
    issues: list[str] = []
    raw_count = sensor_data.get("channel_count")
    try:
        count = int(raw_count)
    except (TypeError, ValueError):
        issues.append("ToF.channel_count must be an integer")
        return issues
    if count < 1:
        issues.append("ToF.channel_count must be >= 1")

    source = _safe_string(sensor_data.get("channel_count_source"))
    pending = sensor_data.get("channel_count_product_target_pending_validation") is True
    if not source and not pending:
        issues.append("ToF.channel_count requires channel_count_source or product target pending validation flag")
    if source and _is_placeholder(source):
        issues.append("ToF.channel_count_source is placeholder")
    return issues


def _validate_required_materials(payload: dict[str, Any]) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    missing: list[str] = []
    placeholders: list[str] = []
    sanitized: list[dict[str, Any]] = []

    for sensor in REQUIRED_SENSORS:
        sensor_data = _sensor_payload(payload, sensor)
        if not sensor_data:
            missing.append(f"{sensor}.sensor_material")
            sanitized.append(_sanitized_sensor(sensor, {}, "missing"))
            continue

        for field in _required_fields(sensor):
            value = sensor_data.get(field)
            if field not in sensor_data or value is None or _safe_string(value) == "":
                missing.append(f"{sensor}.{field}")
            elif field != "channel_count" and _is_placeholder(value):
                placeholders.append(f"{sensor}.{field}")

        if sensor == "ToF":
            for issue in _validate_channel_count(sensor_data):
                if "placeholder" in issue:
                    placeholders.append(issue)
                else:
                    missing.append(issue)
        sanitized.append(_sanitized_sensor(sensor, sensor_data, "present_not_proven"))

    return missing, placeholders, sanitized


def _vendor_boundary_status(vendor_index: Path, boundary_md: Path) -> tuple[str, list[str], dict[str, str]]:
    # 这里核对的是资料覆盖边界，不把 vendor index 解读成 LiDAR/ToF source proof。
    vendor_text, vendor_issue = _read_text(vendor_index)
    boundary_text, boundary_issue = _read_text(boundary_md)
    combined = f"{vendor_text}\n{boundary_text}"
    missing = [phrase for phrase in VENDOR_BOUNDARY_PHRASES if phrase not in combined]
    status = "loaded"
    if vendor_issue or boundary_issue:
        status = "missing_or_unreadable"
    elif missing:
        status = "incomplete_boundary_text"
    return status, missing, {"vendor_index": _safe_ref(vendor_index), "boundary_doc": _safe_ref(boundary_md)}


def _sanitized_sensor(sensor: str, sensor_data: dict[str, Any], material_status: str) -> dict[str, Any]:
    # summary 只暴露状态和引用摘要，不输出完整 vendor/source 文档正文或本地绝对路径。
    output: dict[str, Any] = {
        "sensor": sensor,
        "material_status": material_status,
        "sku_status": "present_not_proven" if _safe_string(sensor_data.get("sku")) else "missing",
        "vendor_source_status": "present_not_proven" if _safe_string(sensor_data.get("source_document")) else "missing",
        "procurement_status": _safe_string(sensor_data.get("procurement_status")) or "missing",
        "mounting_status": "present_not_proven" if _safe_string(sensor_data.get("mounting_plan")) else "missing",
        "wiring_status": "present_not_proven" if _safe_string(sensor_data.get("wiring_plan")) else "missing",
        "calibration_status": "present_not_proven" if _safe_string(sensor_data.get("calibration_plan")) else "missing",
        "hil_entry_status": "present_not_proven" if _safe_string(sensor_data.get("hil_entry_material")) else "missing",
        "field_status": "not_proven",
        "evidence_boundary": EVIDENCE_BOUNDARY,
    }
    if sensor == "ToF":
        output["channel_count"] = sensor_data.get("channel_count")
        output["channel_count_source_status"] = (
            "present_not_proven"
            if _safe_string(sensor_data.get("channel_count_source"))
            else "product_target_pending_validation"
            if sensor_data.get("channel_count_product_target_pending_validation") is True
            else "missing"
        )
    return output


def _summary(
    status: str,
    vendor_refs: dict[str, str],
    missing: list[str],
    placeholders: list[str],
    sensors: list[dict[str, Any]],
) -> dict[str, Any]:
    # summary 是下游唯一应该消费的结构；真实控制和 HIL 字段固定 fail-closed。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source_schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_evidence_boundary": EVIDENCE_BOUNDARY,
        "status": status,
        "hardware_sensor_procurement_intake": status,
        "vendor_boundary": {
            "source": vendor_refs,
            "coverage": "Orange Pi/WAVE ROVER/UART/camera only; no verified project 2D LiDAR or ToF source",
            "lidar_tof_vendor_proof": "not_proven",
        },
        "hardware_material_status": "hardware_material_pending",
        "sensor_materials": sensors,
        "missing_materials": missing,
        "placeholder_materials": placeholders,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "boundary_note": "software proof only; delivery_success=false; primary_actions_enabled=false; not_proven",
    }


def build_hardware_sensor_procurement_intake(
    intake_json: str | Path | None = None,
    vendor_index: str | Path = DEFAULT_VENDOR_INDEX,
    boundary_md: str | Path = DEFAULT_BOUNDARY_MD,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取采购 intake JSON，生成 fail-closed hardware_sensor_procurement_intake artifact。"""

    intake_path = Path(intake_json) if intake_json else None
    vendor_path = Path(vendor_index)
    boundary_path = Path(boundary_md)
    intake_payload, intake_issue = _load_intake(intake_path)
    vendor_status, missing_vendor_phrases, vendor_refs = _vendor_boundary_status(vendor_path, boundary_path)
    missing, placeholders, sensors = _validate_required_materials(intake_payload) if not intake_issue else ([], [], [])

    if vendor_status != "loaded":
        status = BLOCKED_MISSING_VENDOR_BOUNDARY
        missing.extend([f"vendor_boundary.{item}" for item in missing_vendor_phrases])
    elif intake_issue == "missing":
        status = BLOCKED_MISSING_INTAKE
    elif intake_issue == "invalid_json":
        status = BLOCKED_INVALID_JSON
    elif _has_success_or_control_claim(intake_payload):
        status = BLOCKED_SUCCESS_OR_CONTROL_CLAIM
    elif placeholders:
        status = BLOCKED_PLACEHOLDER_MATERIALS
    elif missing:
        status = BLOCKED_MISSING_REQUIRED_MATERIALS
    else:
        status = READY_STATUS

    if not sensors:
        sensors = [_sanitized_sensor(sensor, {}, "missing") for sensor in REQUIRED_SENSORS]
    summary = _summary(status, vendor_refs, missing, placeholders, sensors)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": status,
        "hardware_sensor_procurement_intake": status,
        "intake_source": _safe_ref(intake_path) if intake_path else "missing",
        "intake_status": "loaded" if not intake_issue else intake_issue,
        "vendor_boundary_status": vendor_status,
        "vendor_boundary_sources": vendor_refs,
        "vendor_boundary_note": (
            "docs/vendor/VENDOR_INDEX.md covers Orange Pi/WAVE ROVER/UART/camera references; "
            "it does not prove project 2D LiDAR or ToF SKU/source/procurement/HIL."
        ),
        "required_sensors": list(REQUIRED_SENSORS),
        "required_material_fields": {
            "common": list(COMMON_REQUIRED_FIELDS),
            "ToF": list(TOF_REQUIRED_FIELDS) + ["channel_count_source or channel_count_product_target_pending_validation=true"],
        },
        "sensor_materials": sensors,
        "missing_materials": missing,
        "placeholder_materials": placeholders,
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "review_summary": summary,
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
    return artifact, summary, 0 if status == READY_STATUS else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出路径显式创建父目录，支持 sprint evidence bundle 一次性落盘。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 不访问硬件；它只把人工采购材料校验成 machine-readable blocked/ready artifact。
    parser = argparse.ArgumentParser(
        description="Generate hardware_sensor_procurement_intake fail-closed software-proof artifact."
    )
    parser.add_argument("--intake-json", default="", help="JSON file with 2D LiDAR and ToF procurement materials.")
    parser.add_argument(
        "--vendor-index",
        default=str(DEFAULT_VENDOR_INDEX),
        help="Vendor index path used only to record current source boundary.",
    )
    parser.add_argument(
        "--boundary-md",
        default=str(DEFAULT_BOUNDARY_MD),
        help="Production hardware boundary markdown path.",
    )
    parser.add_argument("--output", default="", help="Write full hardware sensor procurement intake artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact hardware sensor procurement intake summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_sensor_procurement_intake(
        args.intake_json or None,
        vendor_index=args.vendor_index,
        boundary_md=args.boundary_md,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_sensor_procurement_intake: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"overall_status: {artifact['overall_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
