#!/usr/bin/env python3
"""生成 real_material_followup_escalation_status 的 fail-closed PC gate。"""

from __future__ import annotations

# 设计约束 01：本 gate 只生成追责状态，不读取真实硬件、公网、手机或 ROS graph。
# 设计约束 02：本 gate 是 follow-up escalation，不是 readiness/intake/template 的重复包装。
# 设计约束 03：四类真实材料缺口必须共用清晰 owner、due_status 和 escalation_level。
# 设计约束 04：O1 / PR #5 必须保留 PRRT_kwDOSWB9286CJ3tX 与 blocked_pending_real_materials。
# 设计约束 05：mandatory sensor baseline 只能要求 docs/vendor/ source citation，不能宣称已验证。
# 设计约束 06：vendor 来源只证明本地资料边界，不证明真实采购、接线、标定或 HIL。
# 设计约束 07：rerun command 只能是下一步履约提示，不能暗示真实材料已经到位。
# 设计约束 08：输出必须保持 software_proof、not_proven 与 summary-only。
# 设计约束 09：输出必须保持 delivery_success=false。
# 设计约束 10：输出必须保持 primary_actions_enabled=false 和 safe_to_control=false。
# 设计约束 11：任何 success/control claim、凭证、绝对路径或串口路径都必须 fail closed。
# 设计约束 12：CLI dependency-free，便于 Docker-only PC gate 复跑。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.real_material_followup_escalation_status.v1"
SUMMARY_SCHEMA = "trashbot.real_material_followup_escalation_status_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
STATUS = "not_proven"
FOLLOWUP_STATUS = "blocked_pending_real_materials"
EVIDENCE_BOUNDARY = "software_proof_docker_real_material_followup_escalation_status_gate"
PR5_REVIEW_THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"
DEFAULT_EVIDENCE_REF = "real-material-followup-2026-05-19T23-24Z"

BLOCKED_MISSING_VENDOR = "blocked_missing_vendor_index"
BLOCKED_UNSAFE_OUTPUT = "blocked_unsafe_real_material_followup_escalation_status"
BLOCKED_UNSAFE_EVIDENCE_REF = "blocked_unsafe_real_material_followup_evidence_ref"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

# 已读 vendor 来源；artifact 只写 repo 相对引用，避免复制供应商正文或本机路径。
VENDOR_SOURCE_REFS = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
)

# 这些结论来自本地 vendor 文件，只能作为硬件事实边界，不能作为履约证据。
VERIFIED_VENDOR_CONCLUSIONS = (
    "docs/vendor/VENDOR_INDEX.md is the required local hardware source entry point.",
    "WAVE ROVER upper/lower controller communication is UART newline-delimited JSON in the local vendor sources.",
    "WAVE ROVER command IDs and feedback IDs are bounded by json_cmd.h and uart_ctrl.h.",
    "Vendor references do not prove project 2D LiDAR / ToF procurement, installation, wiring, calibration, or HIL.",
)

SOURCE_TEMPLATE_STATUS = "ready_for_field_owner_submission_pack_not_proven"
SOURCE_INTAKE_STATUS = "blocked_missing_real_material_items"
DUE_STATUS = "overdue_pending_real_materials"

SAFE_EVIDENCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,80}$")
TOKEN_OR_PATH_RE = re.compile(r"(?i)(token|secret|password|authorization|bearer|access[_-]?key|file://|^/|[A-Za-z]:\\)")
UNSAFE_OUTPUT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(hil_pass|field_pass|control_enabled)\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?<![A-Za-z0-9_.-])/(Users|tmp|var|etc|home|run|private|Volumes|ws)\b"),
    re.compile(r"/dev/(ttyUSB|ttyACM|serial|cu\.|tty\.)[A-Za-z0-9._-]*"),
)


def _utc_now() -> str:
    # UTC 时间让不同机器生成的 evidence artifact 可按字面排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每层重复安全字段，避免 Robot/mobile 只读局部对象时误启控制。
    return {
        "source": SOURCE,
        "status": STATUS,
        "software_proof": True,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _repo_ref(path: Path) -> str:
    # 输出只使用 repo 相对路径，不能把开发机绝对路径泄漏到摘要。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _encoded(value: Any) -> str:
    # 统一扫描嵌套结构，避免未来字段绕过 success/control 围栏。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_evidence_ref(value: str) -> tuple[str, str]:
    # evidence_ref 是现场材料追踪键，必须短、可读、不可路径化或 token 化。
    ref = str(value).strip()
    if not ref:
        return "", "missing_evidence_ref"
    if not SAFE_EVIDENCE_REF_RE.fullmatch(ref):
        return "", "unsafe_evidence_ref_format"
    if TOKEN_OR_PATH_RE.search(ref):
        return "", "unsafe_evidence_ref_token_or_path"
    return ref, ""


def _has_unsafe_output(value: Any) -> bool:
    # 最后一层闸只查 true claim、凭证和路径；false 安全标记必须允许存在。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in UNSAFE_OUTPUT_PATTERNS)


def _safety_markers() -> list[str]:
    # 字符串标记方便 rg 和下游白名单检查固定边界。
    return [
        "software_proof",
        "not_proven",
        "delivery_success=false",
        "primary_actions_enabled=false",
        "safe_to_control=false",
    ]


def _required_group_specs() -> list[dict[str, Any]]:
    # group spec 直接沉淀 follow-up 责任人、逾期状态和下一份真实材料。
    return [
        {
            "material_group": "o5_external",
            "objective_ref": "Objective 5",
            "field_owner": "product-okr-owner",
            "owner_handoff": "Product Manager / OKR Owner",
            "due_status": DUE_STATUS,
            "blocked_reason": "Objective 5 still lacks real external HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker migration/cutover, and external proof.",
            "next_required_evidence": [
                "real public HTTPS/TLS ingress proof",
                "real 4G/SIM network material",
                "real OSS/CDN live traffic material",
                "real production DB/queue connectivity material",
                "real worker migration/cutover material",
            ],
            "escalation_level": "ceo_decision_required_after_repeated_real_material_blocker",
            "review_route": "Objective 5 external material follow-up",
            "rerun_command": (
                "python3 pc-tools/evidence/real_material_evidence_intake.py "
                "--manifest FIELD_OWNER_MANIFEST.json "
                "--output real_material_evidence_intake.json "
                "--summary-output real_material_evidence_intake_summary.json"
            ),
        },
        {
            "material_group": "o1_pr5_hardware",
            "objective_ref": "Objective 1 / PR #5",
            "field_owner": "hardware-engineer",
            "owner_handoff": "Hardware Infra Engineer",
            "due_status": DUE_STATUS,
            "blocked_reason": (
                "PR #5 thread PRRT_kwDOSWB9286CJ3tX remains blocked_pending_real_materials; "
                "mandatory sensor baseline still needs docs/vendor source citation plus real 2D LiDAR / ToF / WAVE ROVER HIL material."
            ),
            "next_required_evidence": [
                "mandatory sensor baseline citation to docs/vendor/VENDOR_INDEX.md and referenced local vendor files",
                "real 2D LiDAR SKU/source/receipt or purchase order",
                "real ToF SKU/source/receipt and channel/source evidence",
                "real mounting, wiring, power, calibration, and HIL-entry material",
                "real WAVE ROVER UART/HIL packet with feedback_T1001, odom, imu, battery, and operator signoff",
            ],
            "escalation_level": "hardware_real_material_owner_followup_required",
            "review_route": "PR #5 mandatory sensor baseline review thread",
            "rerun_command": (
                "python3 pc-tools/evidence/real_material_evidence_intake.py "
                "--manifest HARDWARE_FIELD_OWNER_MANIFEST.json "
                "--output real_material_evidence_intake.json "
                "--summary-output real_material_evidence_intake_summary.json"
            ),
            "review_thread_id": PR5_REVIEW_THREAD_ID,
            "review_thread_state": "blocked_pending_real_materials",
        },
        {
            "material_group": "pr4_route_elevator",
            "objective_ref": "PR #4 / Objective 2 / Objective 3",
            "field_owner": "autonomy-engineer",
            "owner_handoff": "Autonomy Algorithm Engineer",
            "due_status": DUE_STATUS,
            "blocked_reason": "PR #4 route/elevator remains missing real field material and cannot be inferred from Docker-only software proof.",
            "next_required_evidence": [
                "real Nav2 fixed-route runtime log",
                "real route completion signal",
                "real field task record",
                "real elevator door state and target floor confirmation",
                "real human assistance record, dropoff/cancel material, and delivery_result",
            ],
            "escalation_level": "field_owner_followup_required_before_route_elevator_claim",
            "review_route": "PR #4 route/elevator field-material review",
            "rerun_command": (
                "python3 pc-tools/evidence/real_material_evidence_intake.py "
                "--manifest ROUTE_ELEVATOR_FIELD_OWNER_MANIFEST.json "
                "--output real_material_evidence_intake.json "
                "--summary-output real_material_evidence_intake_summary.json"
            ),
        },
        {
            "material_group": "o4_real_phone",
            "objective_ref": "Objective 4",
            "field_owner": "full-stack-software-engineer",
            "owner_handoff": "User Touchpoint Full-Stack Engineer",
            "due_status": DUE_STATUS,
            "blocked_reason": "Objective 4 still lacks real phone/browser material; local browser or fixture proof is not a real device pass.",
            "next_required_evidence": [
                "real iPhone or Android browser session material",
                "real production app/PWA install or prompt material",
                "real user choice material for PWA prompt",
                "true phone browser acceptance material",
            ],
            "escalation_level": "device_owner_followup_required_before_real_phone_claim",
            "review_route": "Objective 4 real phone acceptance follow-up",
            "rerun_command": (
                "python3 pc-tools/evidence/real_material_evidence_intake.py "
                "--manifest REAL_PHONE_FIELD_OWNER_MANIFEST.json "
                "--output real_material_evidence_intake.json "
                "--summary-output real_material_evidence_intake_summary.json"
            ),
        },
    ]


def _build_group(spec: dict[str, Any], safe_evidence_ref: str) -> dict[str, Any]:
    # group 只暴露可追责字段；真实材料正文必须留在后续 owner manifest 中。
    group = {
        **_safe_flags(),
        "material_group": spec["material_group"],
        "objective_ref": spec["objective_ref"],
        "safe_evidence_ref": safe_evidence_ref,
        "field_owner": spec["field_owner"],
        "owner_handoff": spec["owner_handoff"],
        "due_status": spec["due_status"],
        "blocked_reason": spec["blocked_reason"],
        "next_required_evidence": list(spec["next_required_evidence"]),
        "escalation_level": spec["escalation_level"],
        "rerun_command": spec["rerun_command"],
        "rerun_status_summary": "rerun_pending_real_materials; current status is software_proof follow-up only",
        "source_template_status": SOURCE_TEMPLATE_STATUS,
        "source_intake_status": SOURCE_INTAKE_STATUS,
        "review_route": spec["review_route"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safety_markers": _safety_markers(),
    }
    if spec["material_group"] == "o1_pr5_hardware":
        # PR #5 信息必须在硬件 group 内部出现，方便 reviewer 直接定位 unresolved thread。
        group.update(
            {
                "review_thread_id": PR5_REVIEW_THREAD_ID,
                "review_thread_state": spec["review_thread_state"],
                "mandatory_sensor_baseline_citation": "docs/vendor/VENDOR_INDEX.md plus referenced docs/vendor sources required before review can move.",
                "vendor_source_refs": list(VENDOR_SOURCE_REFS),
            }
        )
    return group


def _summary_group(group: dict[str, Any]) -> dict[str, Any]:
    # summary 只保留 phone/Robot 可渲染字段，不带原始材料正文。
    return {
        **_safe_flags(),
        "material_group": group["material_group"],
        "objective_ref": group["objective_ref"],
        "safe_evidence_ref": group["safe_evidence_ref"],
        "field_owner": group["field_owner"],
        "due_status": group["due_status"],
        "blocked_reason": group["blocked_reason"],
        "next_required_evidence": group["next_required_evidence"],
        "escalation_level": group["escalation_level"],
        "rerun_command": group["rerun_command"],
        "rerun_status_summary": group["rerun_status_summary"],
        "source_template_status": group["source_template_status"],
        "source_intake_status": group["source_intake_status"],
        "review_route": group["review_route"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safety_markers": _safety_markers(),
    }


def build_real_material_followup_escalation_status(
    *,
    vendor_index: Path = DEFAULT_VENDOR_INDEX,
    evidence_ref: str = DEFAULT_EVIDENCE_REF,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 artifact 和 summary；返回码 0 只代表本地 gate 成功生成 fail-closed 状态。"""
    safe_evidence_ref, ref_error = _safe_evidence_ref(evidence_ref)
    exit_code = 0
    status = FOLLOWUP_STATUS
    if ref_error:
        # 不安全 evidence_ref 直接 fail closed，避免跨系统追踪键携带路径或凭证。
        safe_evidence_ref = ""
        status = BLOCKED_UNSAFE_EVIDENCE_REF
        exit_code = 2
    elif not vendor_index.exists():
        # 缺 vendor 入口时不能输出硬件事实结论，只能保守阻断。
        status = BLOCKED_MISSING_VENDOR
        exit_code = 2

    material_groups = [_build_group(spec, safe_evidence_ref) for spec in _required_group_specs()]
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        **_safe_flags(),
        "real_material_followup_escalation_status": status,
        "followup_status": status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        "safe_evidence_ref": safe_evidence_ref,
        "same_evidence_ref_required": True,
        "source_template_status": SOURCE_TEMPLATE_STATUS,
        "source_intake_status": SOURCE_INTAKE_STATUS,
        "vendor_source_boundary": {
            "vendor_index": _repo_ref(vendor_index),
            "vendor_index_exists": vendor_index.exists(),
            "source_refs": list(VENDOR_SOURCE_REFS),
            "verified_hardware_conclusions": list(VERIFIED_VENDOR_CONCLUSIONS),
            "hardware_conclusion": (
                "docs/vendor sources define the local source boundary only; "
                "they do not prove real external cloud, HIL, phone, route/elevator field pass, or delivery success"
            ),
        },
        "review_refs": {
            "objective_5": "Objective 5 remains blocked pending real external proof",
            "objective_1": "Objective 1 remains blocked pending real hardware/HIL material",
            "objective_4": "Objective 4 remains blocked pending real phone material",
            "pr5_thread_id": PR5_REVIEW_THREAD_ID,
            "pr5_state": "blocked_pending_real_materials",
            "pr4_state": "blocked_pending_real_route_elevator_materials",
        },
        "material_groups": material_groups,
        "group_count": len(material_groups),
        "blocked_group_count": len(material_groups),
        "escalation_required_count": len(material_groups),
        "next_action": "field_owners_provide_real_materials_then_rerun_real_material_evidence_intake",
        "not_proven_items": [
            "real_external_cloud_proof",
            "real_wave_rover_uart_hil",
            "real_2d_lidar_tof_procurement_install_calibration",
            "real_route_elevator_field_pass",
            "real_phone_browser_acceptance",
            "delivery_success",
        ],
        "boundary_note": (
            "software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false; safe_to_control=false"
        ),
    }
    summary_groups = [_summary_group(group) for group in material_groups]
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": artifact["generated_at"],
        **_safe_flags(),
        "real_material_followup_escalation_status": status,
        "followup_status": status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        "safe_evidence_ref": safe_evidence_ref,
        "source_template_status": SOURCE_TEMPLATE_STATUS,
        "source_intake_status": SOURCE_INTAKE_STATUS,
        "material_groups": summary_groups,
        "group_count": len(summary_groups),
        "blocked_group_count": len(summary_groups),
        "escalation_required_count": len(summary_groups),
        "next_action": artifact["next_action"],
        "review_refs": artifact["review_refs"],
        "boundary_note": artifact["boundary_note"],
    }

    if _has_unsafe_output(artifact) or _has_unsafe_output(summary):
        # 理论上不会触发；保留兜底，防止未来字段把 gate 写成 proof。
        artifact["real_material_followup_escalation_status"] = BLOCKED_UNSAFE_OUTPUT
        artifact["followup_status"] = BLOCKED_UNSAFE_OUTPUT
        summary["real_material_followup_escalation_status"] = BLOCKED_UNSAFE_OUTPUT
        summary["followup_status"] = BLOCKED_UNSAFE_OUTPUT
        exit_code = 2
    return artifact, summary, exit_code


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # gate 负责创建 evidence 目录，但 payload 不写绝对路径或凭证。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.real_material_followup_escalation_status.v1 software_proof artifact; "
            "keeps not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false."
        )
    )
    parser.add_argument("--vendor-index", type=Path, default=DEFAULT_VENDOR_INDEX)
    parser.add_argument("--evidence-ref", default=DEFAULT_EVIDENCE_REF)
    parser.add_argument("--output", type=Path, default=Path("real_material_followup_escalation_status.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("real_material_followup_escalation_status_summary.json"))
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_real_material_followup_escalation_status(
        vendor_index=args.vendor_index,
        evidence_ref=args.evidence_ref,
    )
    _write_json(args.output, artifact)
    _write_json(args.summary_output, summary)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
