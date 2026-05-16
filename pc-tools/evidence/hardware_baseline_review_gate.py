#!/usr/bin/env python3
"""把 production hardware boundary 转成 autonomy sensor responsibility summary。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema 单独命名，summary 必须沿用 Robot diagnostics 已公开的 handoff contract。
SCHEMA = "trashbot.hardware_baseline_review_gate.v1"
SUMMARY_SCHEMA = "trashbot.hardware_baseline_review_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_baseline_review_gate"
READY_STATUS = "hardware_baseline_review_not_proven"
BLOCKED_MISSING_BOUNDARY = "blocked_missing_production_hardware_boundary"
BLOCKED_INCOMPLETE_BASELINE = "blocked_incomplete_sensor_responsibility_baseline"
BLOCKED_SUCCESS_OR_CONTROL_CLAIM = "blocked_success_or_control_claim"

# 默认读取 product boundary，但 CLI 仍允许测试和 sprint evidence 指向临时副本。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOUNDARY_MD = REPO_ROOT / "docs" / "product" / "production_hardware_boundary.md"

# 这些规则来自 docs/product/production_hardware_boundary.md；允许 Markdown 换行和 target/pending 语义。
REQUIRED_BASELINE_RULES = (
    (
        "target baseline combo includes monocular camera, one 2D LiDAR, and ToF safety ring",
        re.compile(r"Target baseline combo:\s*monocular camera \+ one 2D LiDAR \+ ToF safety ring", re.I),
    ),
    (
        "2D LiDAR target primary SLAM/Nav2 mapping + localization input after procurement validation",
        re.compile(r"2D LiDAR:\s*target primary SLAM/Nav2 mapping \+ localization input", re.I),
    ),
    (
        "monocular camera elevator door/target-floor semantic evidence",
        re.compile(r"Monocular camera:\s*elevator door/target-floor semantic evidence", re.I),
    ),
    (
        "ToF target near-field collision safety gate and not primary SLAM source",
        re.compile(r"ToF:\s*target near-field collision safety.*?not a primary SLAM source", re.I | re.S),
    ),
    (
        "hardware_material_pending and not_proven evidence state",
        re.compile(r"hardware_material_pending.*?not_proven", re.I | re.S),
    ),
)

# 输出必须固定保守边界，任何现场通过或控制放行都不属于本 gate。
NOT_PROVEN = (
    "real_lidar_field_pass",
    "real_tof_field_pass",
    "real_monocular_elevator_semantic_pass",
    "real_slam_nav2_field_run",
    "real_near_field_safety_gate",
    "real_delivery_success",
    "real_hil_pass",
)

# 自由文本若携带成功或控制放行断言，宁可阻断，避免硬件责任表被当成验收证据。
SUCCESS_OR_CONTROL_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(lidar|2d lidar|tof)\s+field\s+pass(ed)?\b"),
    re.compile(r"(?i)\bslam/nav2\s+field\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
)


def _utc_now() -> str:
    # UTC 字符串便于不同 PC 或 Docker 主机产物按字面排序。
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: Path) -> tuple[str, str]:
    # 缺文件或编码错误都不抛异常，保证 CLI 能输出 blocked artifact 供 sprint 留档。
    try:
        return path.expanduser().read_text(encoding="utf-8"), ""
    except FileNotFoundError:
        return "", "missing"
    except (OSError, UnicodeDecodeError):
        return "", "read_error"


def _safe_ref(path: Path) -> str:
    # artifact 只暴露相对资料来源，避免把本机绝对路径传播到下游摘要。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _missing_rules(text: str) -> list[str]:
    # 用语义规则锁住 product target/pending material，不因 Markdown 换行误报。
    return [label for label, pattern in REQUIRED_BASELINE_RULES if not pattern.search(text)]


def _has_success_or_control_claim(text: str) -> bool:
    # 本 gate 允许讨论 delivery success rate 的产品收益，但不允许 true/pass 形式的验收断言。
    return any(pattern.search(text) for pattern in SUCCESS_OR_CONTROL_PATTERNS)


def _sensor_responsibilities() -> list[dict[str, Any]]:
    # 三类传感器职责显式分层，避免 ToF 被误接入主建图或相机语义被误当定位输入。
    return [
        {
            "sensor": "2D LiDAR",
            "product_baseline": True,
            "material_status": "hardware_material_pending",
            "autonomy_responsibility": "primary_slam_nav2_mapping_and_localization_input",
            "autonomy_chain": "SLAM/Nav2 main chain",
            "field_status": "not_proven",
            "evidence_boundary": EVIDENCE_BOUNDARY,
        },
        {
            "sensor": "monocular",
            "product_baseline": True,
            "material_status": "hardware_material_pending",
            "autonomy_responsibility": "elevator_door_and_target_floor_semantic_evidence",
            "autonomy_chain": "elevator/floor semantic evidence",
            "field_status": "not_proven",
            "evidence_boundary": EVIDENCE_BOUNDARY,
        },
        {
            "sensor": "ToF",
            "product_baseline": True,
            "material_status": "hardware_material_pending",
            "autonomy_responsibility": "near_field_collision_safety_and_enter_exit_gate",
            "autonomy_chain": "near-field safety gate",
            "not_primary_mapping_input": True,
            "field_status": "not_proven",
            "evidence_boundary": EVIDENCE_BOUNDARY,
        },
    ]


def _summary(status: str, source_ref: str, missing: list[str]) -> dict[str, Any]:
    # summary 面向 automation、PC evidence 和 sprint closeout，只保留责任摘要和 fail-closed 字段。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": status,
        "hardware_material_status": "hardware_material_pending",
        "source_boundary_doc": source_ref,
        "sensor_responsibility_summary": _sensor_responsibilities(),
        "missing_required_phrases": missing,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_hardware_baseline_review(boundary_md: str | Path = DEFAULT_BOUNDARY_MD) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取产品硬件边界文档，生成 autonomy sensor responsibility gate artifact。"""

    path = Path(boundary_md)
    text, load_issue = _read_text(path)
    source_ref = _safe_ref(path)
    missing = _missing_rules(text) if text else [label for label, _pattern in REQUIRED_BASELINE_RULES]
    if load_issue:
        status = BLOCKED_MISSING_BOUNDARY
    elif missing:
        status = BLOCKED_INCOMPLETE_BASELINE
    elif _has_success_or_control_claim(text):
        status = BLOCKED_SUCCESS_OR_CONTROL_CLAIM
    else:
        status = READY_STATUS

    summary = _summary(status, source_ref, missing)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": status,
        "hardware_baseline_review": status,
        "source_boundary_doc": source_ref,
        "source_boundary_status": "loaded" if not load_issue else load_issue,
        "required_baseline_rules": [label for label, _pattern in REQUIRED_BASELINE_RULES],
        "missing_required_phrases": missing,
        "sensor_responsibility_summary": _sensor_responsibilities(),
        "autonomy_responsibility_boundary": "2D LiDAR is the SLAM/Nav2 primary input; monocular is semantic evidence; ToF is near-field safety only.",
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "lidar_field_run",
            "tof_field_run",
            "camera_field_semantic_run",
            "serial_uart",
            "hil",
            "delivery_execution",
        ],
        "review_summary": summary,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return artifact, summary, 0 if status == READY_STATUS else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 指定输出路径时创建父目录，方便 sprint evidence bundle 直接落盘。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只读 Markdown，不访问硬件、ROS graph、Nav2 runtime 或任何现场传感器。
    parser = argparse.ArgumentParser(
        description="Generate hardware_baseline_review autonomy responsibility software-proof artifact."
    )
    parser.add_argument(
        "--boundary-md",
        default=str(DEFAULT_BOUNDARY_MD),
        help="production_hardware_boundary.md path to review.",
    )
    parser.add_argument("--output", default="", help="Write full hardware baseline review artifact JSON to this path.")
    parser.add_argument("--summary-output", default="", help="Write compact hardware baseline review summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_baseline_review(args.boundary_md)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_baseline_review: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"overall_status: {artifact['overall_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
