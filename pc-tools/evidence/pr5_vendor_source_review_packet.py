#!/usr/bin/env python3
"""生成 PR #5 vendor/source review thread 的 fail-closed 软件证明 packet。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 这些常量是 Robot/mobile 只读消费面的稳定契约，不能随文案调整随意改名。
SCHEMA = "trashbot.pr5_vendor_source_review_packet.v1"
SUMMARY_SCHEMA = "trashbot.pr5_vendor_source_review_packet_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_pr5_vendor_source_review_packet_gate"
THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"

# 本 gate 只读 repo 内 source，不访问 GitHub、串口、ROS graph、HIL rig 或采购系统。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOUNDARY_MD = REPO_ROOT / "docs" / "product" / "production_hardware_boundary.md"
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"
DEFAULT_VENDOR_REFS = (
    REPO_ROOT / "docs" / "vendor" / "waveshare_wave_rover" / "ugv_rpi" / "base_ctrl.py",
    REPO_ROOT / "docs" / "vendor" / "waveshare_wave_rover" / "ugv_rpi" / "config.yaml",
    REPO_ROOT / "docs" / "vendor" / "waveshare_wave_rover" / "WAVE_ROVER_V0.9" / "json_cmd.h",
)

READY_STATUS = "ready_for_pr5_vendor_source_review_packet_not_proven"
BLOCKED_MISSING_SOURCE = "blocked_missing_pr5_vendor_source_review_packet_source"
BLOCKED_MISSING_REVIEW_CONTEXT = "blocked_missing_pr5_vendor_source_review_context"
BLOCKED_UNSAFE_CLAIM = "blocked_unsafe_pr5_vendor_source_review_packet_claim"

# PR #5 X 线程要求的是 source citation；这些材料仍必须等待真实硬件回填。
MISSING_MATERIALS = (
    "real_2d_lidar_sku_source_receipt",
    "real_tof_sku_source_receipt",
    "real_mounting_wiring_power_plan",
    "real_calibration_material",
    "real_sensor_hil_entry",
    "real_nav2_slam_field_pass",
)

# not_proven 是防误读栏位，避免 summary 被当成采购、安装或 HIL 证明。
NOT_PROVEN = (
    "2d_lidar_procurement",
    "tof_procurement",
    "2d_lidar_installation_wiring_power",
    "tof_installation_wiring_power",
    "sensor_calibration",
    "sensor_hil_entry",
    "wave_rover_uart_hil",
    "delivery_success",
)

SOURCE_RULES = (
    (
        "vendor_index_entrypoint",
        DEFAULT_VENDOR_INDEX,
        (r"## Source Of Truth Order", r"Orange Pi Zero 3", r"WAVE ROVER", r"UART.*?newline-delimited JSON"),
    ),
    (
        "wave_rover_base_ctrl_uart_json_reference",
        DEFAULT_VENDOR_REFS[0],
        (r"serial\.Serial", r"json\.loads", r"json\.dumps", r"/dev/ttyACM\*", r"lidar_ser"),
    ),
    (
        "wave_rover_config_source_boundary",
        DEFAULT_VENDOR_REFS[1],
        (r"use_lidar:\s*false", r"cmd_movition_ctrl:\s*1", r"cmd_pwm_ctrl:\s*11"),
    ),
    (
        "wave_rover_json_cmd_firmware_reference",
        DEFAULT_VENDOR_REFS[2],
        (r"#define CMD_SPEED_CTRL\s+1", r"#define CMD_ROS_CTRL\s+13", r"#define CMD_BASE_FEEDBACK\s+130"),
    ),
)

BOUNDARY_RULES = (
    ("boundary_cites_vendor_index", r"docs/vendor/VENDOR_INDEX\.md"),
    ("lidar_tof_not_vendor_proven", r"local vendor tree does not prove.*?2D LiDAR or ToF"),
    ("hardware_material_pending_not_proven", r"hardware_material_pending.*?not_proven"),
    ("target_combo_declared_pending", r"monocular camera \+ one 2D LiDAR \+ ToF safety ring"),
    ("tof_is_product_target", r"ToF product target:.*?product acceptance targets"),
    ("acceptance_requires_sku_source_hil", r"Acceptance rule: do not treat 2D LiDAR or ToF.*?SKU.*?vendor/source.*?HIL"),
)

STRICT_TRUE_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(hil_pass|field_pass|control_enabled)\s*[:=]\s*true\b"),
)

UNSAFE_PATTERNS = STRICT_TRUE_PATTERNS + (
    re.compile(r"(?i)\b(2D LiDAR|LiDAR|ToF).{0,40}\b(procured|installed|wired|calibrated|HIL passed|field passed)\b"),
    re.compile(r"(?i)\b(procurement|installation|wiring|calibration|HIL|field).{0,32}\b(complete|passed|proven|validated)\b"),
    re.compile(r"(?i)\b(OSS_ACCESS_KEY_SECRET|bearer\s+token|password|private_key)\b"),
    re.compile(r"(?i)\b/Users/[^\\s`]+"),
    re.compile(r"(?i)\b/dev/(tty|serial)[^\\s`]*"),
)


def _utc_now() -> str:
    # UTC 时间让多台 PC/Docker 产生的 evidence packet 可按字面排序。
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: Path) -> tuple[str, str]:
    # 缺文件也要生成 blocked packet，review 线程不能因为 traceback 失去复核材料。
    try:
        return path.expanduser().read_text(encoding="utf-8"), ""
    except FileNotFoundError:
        return "", "missing"
    except (OSError, UnicodeDecodeError):
        return "", "read_error"


def _safe_ref(path: Path) -> str:
    # artifact 不泄漏本机绝对路径，只保留 repo 相对 source ref 给 reviewer。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _has(text: str, pattern: str) -> bool:
    # Markdown 和 vendor 源注释会轻微变化，所以只做语义 pattern gate。
    return re.search(pattern, text, re.I | re.S) is not None


def _contains_unsafe_claim(text: str) -> bool:
    # 安全扫描拦截肯定式成功声明；否定句和 not_proven 边界说明不应被误伤。
    guard_words = (
        "fail closed",
        "must fail",
        "must remain",
        "must not",
        "does not prove",
        "do not prove",
        "not prove",
        "not a claim",
        "not local",
        "not local vendor",
        "not hardware",
        "not proof",
        "not_proven",
        "pending",
        "hardware_material_pending",
        "claims",
        "不证明",
        "不得",
        "不是",
        "未验证",
    )
    for pattern in STRICT_TRUE_PATTERNS:
        for match in pattern.finditer(text):
            context = text[max(0, match.start() - 120) : min(len(text), match.end() + 120)].lower()
            if any(word in context for word in guard_words):
                continue
            return True
    for pattern in UNSAFE_PATTERNS[len(STRICT_TRUE_PATTERNS) :]:
        for match in pattern.finditer(text):
            context = text[max(0, match.start() - 260) : min(len(text), match.end() + 160)].lower()
            if any(word in context for word in guard_words):
                continue
            return True
    return False


def _source_rule_results() -> tuple[list[dict[str, Any]], list[str], str]:
    # 每个 source ref 独立判定，便于 reviewer 看到是哪个本地 vendor 文件缺失或漂移。
    results: list[dict[str, Any]] = []
    missing: list[str] = []
    combined_text: list[str] = []
    for rule_id, path, patterns in SOURCE_RULES:
        text, issue = _read_text(path)
        combined_text.append(text)
        checks = {pattern: _has(text, pattern) for pattern in patterns} if text else {}
        missing_patterns = [pattern for pattern, ok in checks.items() if not ok]
        if issue:
            missing.append(f"{rule_id}.{issue}")
        missing.extend(f"{rule_id}.missing_pattern:{pattern}" for pattern in missing_patterns)
        results.append(
            {
                "rule_id": rule_id,
                "source_ref": _safe_ref(path),
                "load_status": "loaded" if not issue else issue,
                "matched_patterns": [pattern for pattern, ok in checks.items() if ok],
                "missing_patterns": missing_patterns,
                "status": "covered_not_proven" if text and not missing_patterns else "missing_or_drifted",
            }
        )
    return results, missing, "\n".join(combined_text)


def _boundary_rule_results(boundary_text: str) -> tuple[list[dict[str, Any]], list[str]]:
    # Product boundary 是 LiDAR/ToF 语义来源；缺任何一条都不能说 thread packet ready。
    results: list[dict[str, Any]] = []
    missing: list[str] = []
    for rule_id, pattern in BOUNDARY_RULES:
        matched = _has(boundary_text, pattern)
        if not matched:
            missing.append(f"{rule_id}.missing")
        results.append({"rule_id": rule_id, "pattern": pattern, "matched": matched})
    return results, missing


def _vendor_source_boundary(source_refs: list[dict[str, Any]]) -> dict[str, Any]:
    # 这里明确“有 vendor/source 覆盖”和“真实 LiDAR/ToF 材料已证明”不是一回事。
    return {
        "entrypoint": "docs/vendor/VENDOR_INDEX.md",
        "review_thread_id": THREAD_ID,
        "source_refs": [item["source_ref"] for item in source_refs],
        "covered_domains": [
            "Orange Pi Zero 3 docs listed in vendor index",
            "WAVE ROVER docs and firmware listed in vendor index",
            "WAVE ROVER UART newline-delimited JSON source references",
            "Waveshare vendor app config and optional lidar parser reference",
        ],
        "lidar_tof_boundary": "hardware_material_pending_not_proven",
        "source_note": "docs/vendor references support source attribution context only; they do not prove project 2D LiDAR/ToF SKU, purchase, install, wiring, calibration, HIL, field pass, or delivery success.",
    }


def _safe_copy(status: str) -> dict[str, str]:
    # safe_copy 是给 review response / diagnostics / mobile 的短文案，避免传播 raw review body。
    return {
        "zh": (
            f"PR #5 线程 {THREAD_ID} 已整理为 vendor/source review packet："
            "本地 docs/vendor 只能证明 Orange Pi、WAVE ROVER、UART/JSON、firmware/vendor app 的资料边界；"
            "2D LiDAR / ToF 仍是 hardware_material_pending、not_proven，不能当作真实采购、安装、标定或 HIL 证据。"
        ),
        "en": (
            f"PR #5 thread {THREAD_ID} is packaged as a vendor/source review packet. "
            "Local docs/vendor material establishes source-boundary context only; 2D LiDAR and ToF remain "
            "hardware_material_pending and not_proven, not procurement, installation, calibration, HIL, or delivery proof."
        ),
        "status": status,
    }


def _next_required_evidence() -> list[str]:
    # 下一步履约动作必须指向真实材料，而不是再堆一层本地 metadata。
    return [
        "Provide reviewed 2D LiDAR SKU/source/receipt or purchase-order material.",
        "Provide reviewed ToF SKU/source/channel-count material.",
        "Link mounting, wiring, power-budget, and calibration plans.",
        "Run a separate HIL-entry review after real materials exist.",
        "Only then request reviewer resolution for hardware-material obligations.",
    ]


def _summary(status: str, source_refs: list[dict[str, Any]], source_missing: list[str], boundary_missing: list[str]) -> dict[str, Any]:
    # summary 是下游首选消费形态，保留固定 fail-closed 控制字段。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source_schema_version": SCHEMA_VERSION,
        "thread_id": THREAD_ID,
        "source": SOURCE,
        "proof_boundary": EVIDENCE_BOUNDARY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": "not_proven",
        "review_packet_status": status,
        "vendor_source_boundary": _vendor_source_boundary(source_refs),
        "missing_source_items": source_missing,
        "missing_review_context": boundary_missing,
        "missing_materials": list(MISSING_MATERIALS),
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "next_required_evidence": _next_required_evidence(),
        "safe_copy": _safe_copy(status),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_pr5_vendor_source_review_packet(
    boundary_md: str | Path = DEFAULT_BOUNDARY_MD,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 product boundary 与本地 vendor refs，生成 thread-specific packet。"""

    boundary_path = Path(boundary_md)
    boundary_text, boundary_issue = _read_text(boundary_path)
    source_refs, source_missing, vendor_text = _source_rule_results()
    boundary_rules, boundary_missing = _boundary_rule_results(boundary_text) if boundary_text else ([], ["production_hardware_boundary.missing"])

    # vendor 源文件会合法包含 /dev/tty* 示例；安全扫描只审 product/review copy，
    # 避免把“读取了 vendor source”误判成 artifact 泄漏 raw serial path。
    all_text = boundary_text
    if boundary_issue:
        status = BLOCKED_MISSING_SOURCE
        boundary_missing.append(f"production_hardware_boundary.{boundary_issue}")
        exit_code = 2
    elif source_missing:
        status = BLOCKED_MISSING_SOURCE
        exit_code = 2
    elif boundary_missing:
        status = BLOCKED_MISSING_REVIEW_CONTEXT
        exit_code = 2
    elif _contains_unsafe_claim(all_text):
        status = BLOCKED_UNSAFE_CLAIM
        exit_code = 2
    else:
        status = READY_STATUS
        exit_code = 0

    summary = _summary(status, source_refs, source_missing, boundary_missing)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "thread_id": THREAD_ID,
        "thread_topic": "2D LiDAR / ToF mandatory assumptions require docs/vendor source evidence",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "proof_boundary": EVIDENCE_BOUNDARY,
        "overall_status": "not_proven",
        "review_packet_status": status,
        "source_docs": {
            "production_hardware_boundary": _safe_ref(boundary_path),
            "vendor_index": _safe_ref(DEFAULT_VENDOR_INDEX),
            "vendor_refs": [_safe_ref(path) for path in DEFAULT_VENDOR_REFS],
        },
        "source_ref_checks": source_refs,
        "boundary_rule_checks": boundary_rules,
        "vendor_source_boundary": summary["vendor_source_boundary"],
        "missing_source_items": source_missing,
        "missing_review_context": boundary_missing,
        "missing_materials": list(MISSING_MATERIALS),
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "next_required_evidence": _next_required_evidence(),
        "safe_copy": summary["safe_copy"],
        "non_access_scope": [
            "github_api_raw_review_body",
            "ros_graph",
            "serial_uart",
            "hardware_bus",
            "procurement_system",
            "sensor_driver_runtime",
            "hil",
            "field_run",
            "objective_5_external_infrastructure",
            "delivery_execution",
        ],
        "review_summary": summary,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return artifact, summary, exit_code


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 创建 evidence 目录只是写软件证明产物，不代表真实硬件材料已存在。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 是 repo-local gate；没有任何硬件、网络或 GitHub 写 side effect。
    parser = argparse.ArgumentParser(description="Generate PR #5 vendor/source review packet software-proof artifact.")
    parser.add_argument("--boundary-md", default=str(DEFAULT_BOUNDARY_MD), help="production_hardware_boundary.md path.")
    parser.add_argument("--output", default="", help="Write full review packet artifact JSON to this path.")
    parser.add_argument("--summary-output", default="", help="Write compact review packet summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_pr5_vendor_source_review_packet(args.boundary_md)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pr5_vendor_source_review_packet: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"summary_file: {Path(args.summary_output).name if args.summary_output else ''}")
        print(f"overall_status: {artifact['overall_status']}")
        print(f"review_packet_status: {artifact['review_packet_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
