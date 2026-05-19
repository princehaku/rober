#!/usr/bin/env python3
"""生成 real_material_readiness_board 的软件证明 artifact。"""

from __future__ import annotations

# 约束 01：本 gate 只读 repo-local vendor 边界，不读取真实硬件、串口或 ROS graph。
# 约束 02：四类材料组必须统一 fail-closed，避免下游误读为真实 proof。
# 约束 03：PR #5 thread ID 与 blocked_pending_real_materials 必须原样进入输出。
# 约束 04：硬件事实只引用 docs/vendor 本地来源边界，不写未经实测的 SKU 或电气细节。
# 约束 05：summary 给 Robot/mobile 只读消费，不能承载控制启用信号。
# 约束 06：所有输出必须保留 delivery_success=false、primary_actions_enabled=false。
# 约束 07：所有输出必须保留 safe_to_control=false，不允许形成上车控制许可。
# 约束 08：CLI 保持 dependency-free，方便 Docker-only 主机作为 evidence gate 运行。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.real_material_readiness_board.v1"
SUMMARY_SCHEMA = "trashbot.real_material_readiness_board_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_real_material_readiness_board_gate"
BOARD_STATE = "blocked_pending_real_materials"
PR5_REVIEW_THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

# 这些是已读 vendor 来源边界；输出只引用路径，不复制供应商长文本。
VENDOR_SOURCE_REFS = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
)

# 硬件结论保持在 source boundary 层级，避免把资料存在误写成实物到位。
VERIFIED_HARDWARE_CONCLUSIONS = (
    "docs/vendor/VENDOR_INDEX.md is the required local entry point for WAVE ROVER, Orange Pi Zero 3, ESP32 lower controller, UART, firmware, and mechanical references.",
    "The local vendor boundary includes WAVE ROVER upper-computer UART references and ESP32 JSON command source files, but this board does not prove live robot UART feedback.",
    "The local vendor boundary does not prove project 2D LiDAR / ToF SKU, receipt, installation, wiring, power, calibration, or HIL-entry evidence.",
)

SAFETY_MARKERS = (
    "software_proof",
    "not_proven",
    "delivery_success=false",
    "primary_actions_enabled=false",
    "safe_to_control=false",
)

UNSAFE_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(hil_pass|field_pass|control_enabled)\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(procurement|installation|wiring|calibration|HIL|field).{0,32}\b(complete|passed|proven|validated)\b"),
    re.compile(r"(?i)\b(Bearer\s+token|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b/dev/(tty|serial|cu\.)[A-Za-z0-9._-]*"),
)


def _utc_now() -> str:
    # UTC 便于不同 worker、Docker 和本机输出按字面排序。
    return datetime.now(timezone.utc).isoformat()


def _repo_ref(path: Path) -> str:
    # artifact 不泄漏开发机绝对路径，只保留 repo 相对引用。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _source_state(path: Path) -> dict[str, Any]:
    # 只记录本地来源是否存在，不把 vendor 资料内容嵌入 board。
    return {
        "path": _repo_ref(path),
        "exists": path.exists(),
    }


def _safe_flags() -> dict[str, Any]:
    # 每层都显式写安全旗标，避免 downstream 只读局部字段时误启用控制。
    return {
        "source": SOURCE,
        "status": STATUS,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _group(
    *,
    group_id: str,
    title: str,
    owner: str,
    objective_ref: str,
    review_refs: list[str],
    blocking_reason: str,
    group_status: str,
    next_required_evidence: list[str],
    source_refs: list[str],
    missing_material_categories: list[str],
) -> dict[str, Any]:
    # group 与 board 使用同一套 fail-closed 字段，方便 Robot/mobile 逐组渲染。
    return {
        **_safe_flags(),
        "group_id": group_id,
        "title": title,
        "owner": owner,
        "objective_ref": objective_ref,
        "review_refs": review_refs,
        "blocking_reason": blocking_reason,
        "group_status": group_status,
        "material_status": BOARD_STATE,
        "proof_boundary": "routing_readiness_only_not_real_material_proof",
        "missing_material_categories": missing_material_categories,
        "next_required_evidence": next_required_evidence,
        "source_refs": source_refs,
        "safety_markers": list(SAFETY_MARKERS),
    }


def _material_groups() -> list[dict[str, Any]]:
    # 四类材料组来自 tech-plan；这里只做路由看板，不生成新控制路径。
    return [
        _group(
            group_id="o5_external",
            title="Objective 5 external real-material readiness",
            owner="product-okr-owner",
            objective_ref="Objective 5",
            review_refs=["OKR.md 4.1"],
            blocking_reason="missing_real_external_proof",
            group_status=STATUS,
            missing_material_categories=[
                "public_https_tls",
                "4g_sim",
                "oss_cdn_live_traffic",
                "production_db_queue",
            ],
            next_required_evidence=[
                "public HTTPS/TLS ingress proof",
                "4G/SIM or equivalent real network material",
                "OSS/CDN live traffic evidence",
                "production DB/queue connectivity and worker/migration/cutover proof",
            ],
            source_refs=["Objective 5", "OKR.md 4.1", "software_proof O5 blocker history"],
        ),
        _group(
            group_id="objective_1_pr5_hardware",
            title="Objective 1 / PR #5 hardware real-material readiness",
            owner="hardware-engineer",
            objective_ref="Objective 1",
            review_refs=["PR #5", PR5_REVIEW_THREAD_ID, "unresolved", BOARD_STATE],
            blocking_reason="missing_wave_rover_uart_hil_and_pr5_sensor_materials",
            group_status=BOARD_STATE,
            missing_material_categories=[
                "real_wave_rover_uart_feedback",
                "real_hil_packet",
                "real_2d_lidar_sku_source_receipt",
                "real_tof_sku_source_receipt",
                "install_wiring_power_calibration_materials",
            ],
            next_required_evidence=[
                "real WAVE ROVER powered bench evidence tied to one safe evidence_ref",
                "Orange Pi runtime UART device confirmation plus wiring and power review",
                "newline-delimited JSON UART command/feedback capture under operator control",
                "HIL packet with feedback, odom, imu, battery, and operator signoff",
                "PR #5 2D LiDAR / ToF SKU, source, receipt, install, wiring, power, calibration, and HIL-entry material",
            ],
            source_refs=["PR #5", PR5_REVIEW_THREAD_ID, *VENDOR_SOURCE_REFS],
        ),
        _group(
            group_id="pr4_route_elevator",
            title="PR #4 route/elevator real-material readiness",
            owner="autonomy-engineer",
            objective_ref="PR #4",
            review_refs=["PR #4", "route/elevator field material blocked"],
            blocking_reason="missing_real_route_elevator_field_materials",
            group_status="blocked_missing_pr4_route_elevator_real_materials",
            missing_material_categories=[
                "real_elevator_door_state",
                "target_floor_confirmation",
                "human_assistance_record",
                "nav2_fixed_route_runtime_log",
                "field_task_record",
                "route_completion_signal",
                "dropoff_completion_material",
                "cancel_completion_material",
                "delivery_result",
            ],
            next_required_evidence=[
                "same safe evidence_ref field task record",
                "real Nav2/fixed-route runtime log",
                "route completion signal",
                "real elevator door state",
                "target floor confirmation",
                "human assistance record",
                "dropoff/cancel completion materials",
                "delivery_result",
                "field operator callback packet reviewed as accepted rather than synthetic fixture",
            ],
            source_refs=["PR #4", "Objective 2", "Objective 3", "route_task_field_retest software_proof chain"],
        ),
        _group(
            group_id="objective_4_real_phone",
            title="Objective 4 real phone readiness",
            owner="full-stack-software-engineer",
            objective_ref="Objective 4",
            review_refs=["Objective 4", "mobile/web software proof"],
            blocking_reason="missing_real_phone_device_acceptance_materials",
            group_status=STATUS,
            missing_material_categories=[
                "real_phone_browser_session",
                "real_device_pwa_installability",
                "real_network_device_capture",
                "operator_reviewed_real_device_material",
            ],
            next_required_evidence=[
                "real phone browser session evidence",
                "PWA/installability evidence from a target device",
                "real network/device capture proving status panel consumption",
                "operator-visible screenshots or recording reviewed as real-device material",
            ],
            source_refs=["Objective 4", "mobile/web local Chromium proof boundary"],
        ),
    ]


def _encoded(value: Any) -> str:
    # 对完整嵌套结构做扫描，避免局部 summary 漏掉危险成功口径。
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _has_unsafe_claim(value: Any) -> bool:
    # 任何成功、控制或敏感材料信号都必须阻断输出。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in UNSAFE_PATTERNS)


def _base_artifact(status: str, vendor_index: Path) -> dict[str, Any]:
    # ready 只表示 board 生成成功，不表示任何 Objective 或 PR 已实证通过。
    groups = _material_groups()
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        **_safe_flags(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "real_material_readiness_board": status,
        "material_status": BOARD_STATE,
        "summary_only": False,
        "routing_surface_only": True,
        "safe_to_render_on_phone": True,
        "review_threads": {
            "pr5_thread_id": PR5_REVIEW_THREAD_ID,
            "pr5_review_state": "unresolved",
            "pr5_material_state": BOARD_STATE,
        },
        "source_files": {
            "vendor_index": _source_state(vendor_index),
        },
        "vendor_source_refs": list(VENDOR_SOURCE_REFS),
        "verified_hardware_conclusions": list(VERIFIED_HARDWARE_CONCLUSIONS),
        "material_groups": groups,
        "not_proven": [
            "Objective 5 external proof",
            "Objective 1 WAVE ROVER/UART/HIL",
            "PR #5 2D LiDAR / ToF real materials",
            "PR #4 route/elevator real materials",
            "Objective 4 real phone acceptance",
            "delivery_success",
            "primary_actions_enabled",
            "safe_to_control",
        ],
        "safety_markers": list(SAFETY_MARKERS),
    }


def _summary_from_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    # summary 只保留跨端需要的只读字段，不传递完整材料正文。
    groups = artifact.get("material_groups", [])
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": artifact["schema"],
        **_safe_flags(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "real_material_readiness_board": artifact["real_material_readiness_board"],
        "material_status": artifact["material_status"],
        "summary_only": True,
        "routing_surface_only": True,
        "safe_to_render_on_phone": True,
        "review_threads": artifact["review_threads"],
        "group_count": len(groups),
        "material_groups": [
            {
                **_safe_flags(),
                "group_id": group["group_id"],
                "title": group["title"],
                "owner": group["owner"],
                "objective_ref": group["objective_ref"],
                "review_refs": group["review_refs"],
                "blocking_reason": group["blocking_reason"],
                "group_status": group["group_status"],
                "material_status": group["material_status"],
                "missing_material_categories": group["missing_material_categories"],
                "next_required_evidence": group["next_required_evidence"],
                "safety_markers": list(SAFETY_MARKERS),
            }
            for group in groups
        ],
        "vendor_boundary": "docs/vendor/VENDOR_INDEX.md and referenced local vendor files are source boundary only; they are not real hardware proof.",
        "not_proven": artifact["not_proven"],
        "safety_markers": list(SAFETY_MARKERS),
    }


def build_real_material_readiness_board(
    vendor_index: str | Path = DEFAULT_VENDOR_INDEX,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    # 缺 vendor index 时也输出可解释 artifact，供 sprint evidence 记录 blocked 原因。
    vendor_path = Path(vendor_index)
    status = "ready_for_real_material_readiness_board_not_proven"
    exit_code = 0
    if not vendor_path.exists():
        status = "blocked_missing_vendor_index"
        exit_code = 2

    artifact = _base_artifact(status, vendor_path)
    summary = _summary_from_artifact(artifact)

    if _has_unsafe_claim({"artifact": artifact, "summary": summary}):
        # unsafe claim 比缺资料更严重；它会阻止 downstream 误消费成功口径。
        artifact["real_material_readiness_board"] = "blocked_unsafe_real_material_readiness_board_claim"
        summary["real_material_readiness_board"] = artifact["real_material_readiness_board"]
        return artifact, summary, 2

    return artifact, summary, exit_code


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # 统一缩进和排序，减少并行 worker 后续 diff 噪音。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor-index", default=str(DEFAULT_VENDOR_INDEX))
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary-output", required=True)
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_real_material_readiness_board(args.vendor_index)
    _write_json(Path(args.output), artifact)
    _write_json(Path(args.summary_output), summary)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
