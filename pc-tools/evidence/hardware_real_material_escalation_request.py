#!/usr/bin/env python3
"""生成 hardware_real_material_escalation_request fail-closed 升级请求。"""

from __future__ import annotations

# 设计约束 01：本 gate 只读 repo 文档，不读取真实硬件、串口、ROS graph 或传感器。
# 设计约束 02：升级请求是 summary-only，不承载原始 HIL packet、raw JSON 或本机路径。
# 设计约束 03：vendor 资料只能证明 source boundary，不能证明项目已采购或接线。
# 设计约束 04：WAVE ROVER/UART/HIL 与 PR #5 2D LiDAR / ToF 缺口必须同时列出。
# 设计约束 05：所有输出必须保持 software_proof、not_proven 和 hardware_material_pending。
# 设计约束 06：所有输出必须保持 delivery_success=false 和 primary_actions_enabled=false。
# 设计约束 07：任何 HIL passed、field pass、采购/接线/标定完成文案都必须 fail closed。
# 设计约束 08：CLI 必须 dependency-free，方便 PC/Docker-only 环境作为围栏命令运行。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.hardware_real_material_escalation_request.v1"
SUMMARY_SCHEMA = "trashbot.hardware_real_material_escalation_request_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_real_material_escalation_request_gate"

READY_STATUS = "ready_for_hardware_real_material_escalation_request_not_proven"
BLOCKED_MISSING_VENDOR = "blocked_missing_vendor_index"
BLOCKED_MISSING_PRODUCT_BOUNDARY = "blocked_missing_production_hardware_boundary"
BLOCKED_UNSAFE_COPY = "blocked_unsafe_hardware_real_material_escalation_request_copy"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"
DEFAULT_PRODUCT_BOUNDARY = REPO_ROOT / "docs" / "product" / "production_hardware_boundary.md"

# 这些本地 vendor 文件是事实边界；输出只放 repo 相对引用，不复制供应商原文。
VENDOR_SOURCE_REFS = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf",
    "docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf",
)

VERIFIED_VENDOR_CONCLUSIONS = (
    "docs/vendor/VENDOR_INDEX.md lists Orange Pi Zero 3, WAVE ROVER, ESP32 lower controller, and UART newline-delimited JSON as the local hardware/source boundary.",
    "WAVE ROVER local firmware/source references include json_cmd.h and uart_ctrl.h; they bound command IDs and JSON framing but do not prove this robot has live UART feedback.",
    "Waveshare Raspberry Pi upper-computer references show serial UART usage at 115200; Orange Pi runtime device name still requires target confirmation.",
    "docs/vendor/VENDOR_INDEX.md currently has no project 2D LiDAR / ToF SKU, receipt, install, wiring, power, calibration, or reviewed HIL evidence.",
)

WAVE_ROVER_MISSING_MATERIALS = (
    "real WAVE ROVER chassis powered bench evidence tied to one safe evidence_ref",
    "Orange Pi UART device confirmation and serial wiring/power review",
    "UART command/feedback capture showing newline-delimited JSON under operator control",
    "HIL packet with command, serial log, feedback_T1001, odom, imu, battery, and operator signoff",
)

PR5_SENSOR_MISSING_MATERIALS = (
    "PR #5 2D LiDAR SKU/source/receipt or purchase order",
    "PR #5 2D LiDAR mounting, wiring, power budget, frame, and calibration plan",
    "PR #5 ToF SKU/source/receipt plus channel-count source",
    "PR #5 ToF mounting, wiring, power, threshold, and HIL-entry material",
)

NEXT_REQUIRED_EVIDENCE = (
    "Provide real WAVE ROVER/UART/HIL packet materials before changing Objective 1 from not_proven.",
    "Provide PR #5 2D LiDAR / ToF SKU/source/receipt, install, wiring, power, calibration, and HIL-entry evidence.",
    "Keep phone/mobile consumers summary-only with delivery_success=false and primary_actions_enabled=false until human review accepts real materials.",
)

NOT_PROVEN = (
    "real_wave_rover_uart_feedback",
    "real_hil_packet_pass",
    "real_2d_lidar_sku_source_receipt",
    "real_2d_lidar_mounting_wiring_power_calibration",
    "real_tof_sku_source_receipt",
    "real_tof_mounting_wiring_power_calibration",
    "real_nav2_slam_field_pass",
    "real_near_field_safety_gate_pass",
    "objective_5_external_proof",
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
    "redis://",
    "amqp://",
    "mongodb://",
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
    (re.compile(r"(?i)\b(postgres|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
)


def _utc_now() -> str:
    # UTC 时间方便 Docker、CI 与本机输出稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _encoded(value: Any) -> str:
    # 统一编码后做安全扫描，避免嵌套字段漏检。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 外发 summary 先脱敏，避免手机端拿到 raw path、串口或凭证。
    text = default if value is None else str(value).strip()
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text or default


def _without_not_proven(value: Any) -> Any:
    # not_proven 字段可以安全包含 pass 语义，成功断言扫描需排除此字段。
    if isinstance(value, dict):
        return {key: _without_not_proven(item) for key, item in value.items() if key != "not_proven"}
    if isinstance(value, list):
        return [_without_not_proven(item) for item in value]
    return value


def _has_unsafe_copy(value: Any) -> bool:
    # raw 串口、凭证、完整 artifact、绝对本机路径都不能进入升级请求。
    encoded = _encoded(value)
    if any(token in encoded for token in FORBIDDEN_TOKENS):
        return True
    return bool(re.search(r'(?i)"[^"]*(/Users/|/home/|/tmp/|/var/folders/)[^"]*"', encoded))


def _has_success_claim(value: Any) -> bool:
    # 本 gate 只允许 request_not_proven；任何成功口径都必须阻断。
    encoded = _encoded(_without_not_proven(value))
    return any(pattern.search(encoded) for pattern in SUCCESS_PATTERNS)


def _source_state(path: Path) -> dict[str, Any]:
    # 只记录文件是否存在和 repo 引用，不把文档内容复制给 downstream。
    display_path = str(path)
    try:
        display_path = str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        display_path = path.name
    return {
        "path": display_path,
        "exists": path.exists(),
    }


def _base_artifact(status: str, vendor_index: Path, product_boundary: Path) -> dict[str, Any]:
    # 基础 artifact 永远 fail-closed，ready 也只是升级请求 ready，不是硬件 ready。
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": status,
        "hardware_real_material_escalation_request": status,
        "summary_only": True,
        "phone_safe": True,
        "source_files": {
            "vendor_index": _source_state(vendor_index),
            "production_hardware_boundary": _source_state(product_boundary),
        },
        "vendor_source_refs": list(VENDOR_SOURCE_REFS),
        "verified_hardware_conclusions": list(VERIFIED_VENDOR_CONCLUSIONS),
        "escalation_scope": {
            "objective_1": "WAVE ROVER/UART/HIL real-material gap remains blocked pending real evidence.",
            "pr_5": "2D LiDAR / ToF real-material gap remains blocked pending SKU/source/receipt/install/wiring/power/calibration/HIL-entry evidence.",
            "objective_5": "No external cloud/production proof is claimed by this hardware escalation request.",
        },
        "missing_real_materials": {
            "wave_rover_uart_hil": list(WAVE_ROVER_MISSING_MATERIALS),
            "pr5_2d_lidar_tof": list(PR5_SENSOR_MISSING_MATERIALS),
        },
        "next_required_evidence": list(NEXT_REQUIRED_EVIDENCE),
        "owner_handoff": [
            {
                "owner": "Hardware Infra Engineer",
                "action": "Collect WAVE ROVER/UART/HIL packet evidence and PR #5 2D LiDAR / ToF real materials before any hardware claim changes.",
            },
            {
                "owner": "Product Manager / OKR Owner",
                "action": "Keep Objective 1 material gap marked not_proven until real materials are reviewed.",
            },
        ],
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_from_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    # Robot/mobile 只需要安全摘要，不需要完整材料正文。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": artifact["schema"],
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": artifact["status"],
        "hardware_real_material_escalation_request": artifact["hardware_real_material_escalation_request"],
        "summary_only": True,
        "phone_safe": True,
        "materials_requested": [
            "WAVE ROVER/UART/HIL real-material packet",
            "PR #5 2D LiDAR SKU/source/receipt/install/wiring/power/calibration/HIL-entry material",
            "PR #5 ToF SKU/source/receipt/channel/install/wiring/power/calibration/HIL-entry material",
        ],
        "vendor_boundary": "docs/vendor/VENDOR_INDEX.md is cited as source boundary only; it is not real hardware proof.",
        "hardware_material_status": artifact["hardware_material_status"],
        "evidence_status": artifact["evidence_status"],
        "not_proven": artifact["not_proven"],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_hardware_real_material_escalation_request(
    vendor_index: Path = DEFAULT_VENDOR_INDEX,
    product_boundary: Path = DEFAULT_PRODUCT_BOUNDARY,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    # 缺 vendor 入口时 fail closed，因为硬件事实不能凭记忆生成。
    if not vendor_index.exists():
        artifact = _base_artifact(BLOCKED_MISSING_VENDOR, vendor_index, product_boundary)
        summary = _summary_from_artifact(artifact)
        return artifact, summary, 2

    # 缺产品边界时也 fail closed，避免升级请求脱离 PR #5 / OKR 语义。
    if not product_boundary.exists():
        artifact = _base_artifact(BLOCKED_MISSING_PRODUCT_BOUNDARY, vendor_index, product_boundary)
        summary = _summary_from_artifact(artifact)
        return artifact, summary, 2

    artifact = _base_artifact(READY_STATUS, vendor_index, product_boundary)
    if _has_unsafe_copy(artifact) or _has_success_claim(artifact):
        artifact["status"] = BLOCKED_UNSAFE_COPY
        artifact["hardware_real_material_escalation_request"] = BLOCKED_UNSAFE_COPY
        summary = _summary_from_artifact(artifact)
        return artifact, summary, 2

    summary = _summary_from_artifact(artifact)
    if _has_unsafe_copy(summary) or _has_success_claim(summary):
        artifact["status"] = BLOCKED_UNSAFE_COPY
        artifact["hardware_real_material_escalation_request"] = BLOCKED_UNSAFE_COPY
        summary = _summary_from_artifact(artifact)
        return artifact, summary, 2
    return artifact, summary, 0


def _write_json(path: Path | None, payload: dict[str, Any]) -> None:
    # 输出路径由 CLI 显式传入；默认 stdout 避免静默写入未知目录。
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor-index", type=Path, default=DEFAULT_VENDOR_INDEX)
    parser.add_argument("--product-boundary", type=Path, default=DEFAULT_PRODUCT_BOUNDARY)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_real_material_escalation_request(
        vendor_index=args.vendor_index,
        product_boundary=args.product_boundary,
    )
    _write_json(args.output, artifact)
    _write_json(args.summary_output, summary)
    print(json.dumps({"artifact": artifact, "summary": summary}, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
