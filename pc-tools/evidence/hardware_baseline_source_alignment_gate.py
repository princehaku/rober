#!/usr/bin/env python3
"""核对 production hardware boundary 与本地 vendor/source coverage 是否对齐。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema/boundary 是下游 Robot diagnostics、mobile/web 和 sprint closeout 的稳定契约。
SCHEMA = "trashbot.hardware_baseline_source_alignment.v1"
SUMMARY_SCHEMA = "trashbot.hardware_baseline_source_alignment_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_baseline_source_alignment_gate"

# 默认只读仓库内 Markdown；CLI 参数只用于测试或 sprint evidence 临时副本。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOUNDARY_MD = REPO_ROOT / "docs" / "product" / "production_hardware_boundary.md"
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

READY_STATUS = "hardware_baseline_source_aligned_not_proven"
BLOCKED_MISSING_SOURCE = "blocked_missing_hardware_baseline_source"
BLOCKED_MISSING_ALIGNMENT = "blocked_missing_hardware_baseline_source_alignment"
BLOCKED_SUCCESS_OR_CONTROL_CLAIM = "blocked_success_or_control_claim"

# 默认硬件集来自 product boundary；它必须和 LiDAR/ToF target baseline 分开。
DEFAULT_HARDWARE_RULES = (
    ("default includes WAVE ROVER mobile chassis", re.compile(r"WAVE ROVER mobile chassis", re.I)),
    ("default includes Orange Pi Zero 3 upper computer", re.compile(r"Orange Pi Zero 3 upper computer", re.I)),
    ("default includes monocular 1080p camera", re.compile(r"Monocular 1080p camera", re.I)),
    ("default includes microphone", re.compile(r"Microphone", re.I)),
    ("default includes speaker or buzzer", re.compile(r"Speaker or buzzer", re.I)),
)

# target baseline 只允许保持 product target / pending 语义，不能升级成采购或 HIL 事实。
TARGET_BASELINE_RULES = (
    (
        "target baseline combo is monocular camera plus one 2D LiDAR plus ToF safety ring",
        re.compile(r"Target baseline combo:\s*monocular camera \+ one 2D LiDAR \+ ToF safety ring", re.I),
    ),
    (
        "2D LiDAR and ToF are pending procurement/source attribution and HIL evidence",
        re.compile(r"2D\s+LiDAR and ToF ring are target hardware pending procurement/source\s+attribution.*?HIL evidence", re.I | re.S),
    ),
    (
        "ToF channel counts are product acceptance targets not vendor or HIL proven facts",
        re.compile(r"ToF product target:.*?not local vendor or HIL-proven facts", re.I | re.S),
    ),
    (
        "2D LiDAR is target SLAM/Nav2 input after validation",
        re.compile(r"2D LiDAR:\s*target primary SLAM/Nav2 mapping \+ localization input after\s+procurement validation", re.I | re.S),
    ),
    (
        "ToF is target near-field safety and not primary SLAM source",
        re.compile(r"ToF:\s*target near-field collision safety.*?not a primary SLAM source", re.I | re.S),
    ),
)

# vendor/source boundary 同时要求 product 文档和 vendor index 都说清楚 coverage 与缺口。
SOURCE_ALIGNMENT_RULES = (
    ("product boundary cites docs/vendor/VENDOR_INDEX.md", re.compile(r"docs/vendor/VENDOR_INDEX\.md"), "boundary"),
    (
        "product boundary says local vendor tree does not prove project 2D LiDAR or ToF",
        re.compile(r"local vendor tree does not prove.*?2D LiDAR or ToF", re.I | re.S),
        "boundary",
    ),
    (
        "product boundary keeps hardware_material_pending and not_proven",
        re.compile(r"hardware_material_pending.*?not_proven", re.I | re.S),
        "boundary",
    ),
    ("vendor index covers Orange Pi Zero 3", re.compile(r"Orange Pi Zero 3"), "vendor"),
    ("vendor index covers WAVE ROVER", re.compile(r"WAVE ROVER"), "vendor"),
    ("vendor index covers UART newline-delimited JSON", re.compile(r"UART.*?newline-delimited JSON", re.I | re.S), "vendor"),
    ("vendor index lists Complete Material Coverage", re.compile(r"Complete Material Coverage", re.I), "vendor"),
)

# not_proven 明确列出本 gate 没有证明的硬件、现场和交付能力。
NOT_PROVEN = (
    "real_2d_lidar_procured_or_installed",
    "real_tof_procured_or_installed",
    "real_lidar_tof_vendor_source_accepted",
    "real_mounting_wiring_calibration",
    "real_sensor_hil_entry_pass",
    "real_slam_nav2_field_pass",
    "real_near_field_safety_pass",
    "real_delivery_success",
)

# 只拦截肯定式成功/控制/HIL/field pass 断言；否定句里的 not proven 缺口允许存在。
SUCCESS_OR_CONTROL_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(field_pass|hil_pass|control_enabled)\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(has|have|is|are|was|were)\s+(passed|proven|validated)\s+(HIL|field)\b"),
    re.compile(r"(?i)\b(2D LiDAR|LiDAR|ToF).{0,32}\b(field|HIL)\s+pass(?:ed)?\s+(confirmed|complete|done|true)\b"),
)


def _utc_now() -> str:
    # UTC 时间戳便于不同 PC/Docker 主机产物按字面排序。
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: Path) -> tuple[str, str]:
    # 缺文件也输出 blocked artifact，避免 sprint closeout 只剩 traceback。
    try:
        return path.expanduser().read_text(encoding="utf-8"), ""
    except FileNotFoundError:
        return "", "missing"
    except (OSError, UnicodeDecodeError):
        return "", "read_error"


def _safe_ref(path: Path) -> str:
    # 下游 summary 不传播开发机绝对路径，只保留 repo 相对路径或文件名。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _section(text: str, heading: str) -> str:
    # Markdown section 提取只服务摘要；校验仍靠语义 regex 防止标题小改导致误报。
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.I | re.M)
    match = pattern.search(text)
    if not match:
        return ""
    next_heading = re.search(r"^##\s+", text[match.end() :], re.M)
    end = match.end() + next_heading.start() if next_heading else len(text)
    return text[match.end() : end].strip()


def _bullet_lines(section_text: str) -> list[str]:
    # 摘要只保留 Markdown bullet 的干净文本，避免把完整文档复制进 artifact。
    items: list[str] = []
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
    return items


def _missing_rules(boundary_text: str, vendor_text: str) -> list[str]:
    # 三组规则分别覆盖默认硬件、target baseline、vendor/source 对齐。
    missing = [label for label, pattern in DEFAULT_HARDWARE_RULES if not pattern.search(boundary_text)]
    missing.extend(label for label, pattern in TARGET_BASELINE_RULES if not pattern.search(boundary_text))
    for label, pattern, source in SOURCE_ALIGNMENT_RULES:
        haystack = boundary_text if source == "boundary" else vendor_text
        if not pattern.search(haystack):
            missing.append(label)
    return missing


def _has_success_or_control_claim(boundary_text: str, vendor_text: str) -> bool:
    # 同时扫 product boundary 和 vendor index；vendor/source 对齐 gate 不能吞掉成功断言。
    text = f"{boundary_text}\n{vendor_text}"
    return any(pattern.search(text) for pattern in SUCCESS_OR_CONTROL_PATTERNS)


def _default_hardware_summary(boundary_text: str) -> dict[str, Any]:
    # default set 只描述当前产品边界，不把 target 传感器混入默认已具备硬件。
    items = _bullet_lines(_section(boundary_text, "Default Hardware Set"))
    return {
        "source_section": "Default Hardware Set",
        "items": items,
        "default_lidar_or_tof_included": any(re.search(r"\b(2D LiDAR|LiDAR|ToF)\b", item, re.I) for item in items),
        "status": "loaded_not_proven" if items else "missing",
    }


def _target_sensor_baseline_summary(boundary_text: str) -> dict[str, Any]:
    # target baseline 保留 product target/pending 语义，供 diagnostics/mobile 只读展示。
    section_text = _section(boundary_text, "Navigation/Sensing Baseline (Product Target, Procurement Validation Pending)")
    return {
        "source_section": "Navigation/Sensing Baseline (Product Target, Procurement Validation Pending)",
        "target_combo": "monocular camera + one 2D LiDAR + ToF safety ring",
        "tof_target": "2 channels minimum, 4 channels recommended; product target pending source validation",
        "sensor_roles": {
            "2D LiDAR": "target primary SLAM/Nav2 mapping + localization after procurement validation",
            "monocular": "current semantic evidence sensor for elevator door/target-floor diagnostics",
            "ToF": "target near-field collision safety and enter/exit gate; not primary SLAM source",
        },
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "status": "loaded_not_proven" if section_text else "missing",
    }


def _vendor_source_boundary(vendor_index: Path, boundary_md: Path, vendor_text: str, boundary_text: str) -> dict[str, Any]:
    # vendor coverage 是资料边界，不是 LiDAR/ToF 的采购、安装或 HIL 证明。
    return {
        "source_docs": {"boundary_doc": _safe_ref(boundary_md), "vendor_index": _safe_ref(vendor_index)},
        "vendor_coverage": {
            "orange_pi_zero_3": "covered_by_docs_vendor_index" if "Orange Pi Zero 3" in vendor_text else "missing",
            "wave_rover": "covered_by_docs_vendor_index" if "WAVE ROVER" in vendor_text else "missing",
            "uart_json": "covered_by_docs_vendor_index" if re.search(r"UART.*?JSON", vendor_text, re.I | re.S) else "missing",
            "camera_material": "covered_by_docs_vendor_index" if re.search(r"camera", vendor_text, re.I) else "missing",
        },
        "lidar_tof_source_boundary": (
            "hardware_material_pending_not_proven"
            if re.search(r"local vendor tree does not prove.*?2D LiDAR or ToF", boundary_text, re.I | re.S)
            else "missing_alignment_statement"
        ),
        "vendor_source_boundary": "docs/vendor/VENDOR_INDEX.md plus local vendor coverage only; no project 2D LiDAR/ToF purchase/install/HIL proof",
    }


def _summary(
    status: str,
    boundary_md: Path,
    vendor_index: Path,
    boundary_text: str,
    vendor_text: str,
    missing_items: list[str],
) -> dict[str, Any]:
    # summary 是下游应优先消费的紧凑结构，固定 fail-closed 控制字段。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source_schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": status,
        "hardware_baseline_source_alignment": status,
        "default_hardware_set_summary": _default_hardware_summary(boundary_text),
        "target_sensor_baseline_summary": _target_sensor_baseline_summary(boundary_text),
        "vendor_source_boundary": _vendor_source_boundary(vendor_index, boundary_md, vendor_text, boundary_text),
        "missing_alignment_items": missing_items,
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_hardware_baseline_source_alignment(
    boundary_md: str | Path = DEFAULT_BOUNDARY_MD,
    vendor_index: str | Path = DEFAULT_VENDOR_INDEX,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 product boundary 和 vendor index，生成 fail-closed source alignment artifact。"""

    boundary_path = Path(boundary_md)
    vendor_path = Path(vendor_index)
    boundary_text, boundary_issue = _read_text(boundary_path)
    vendor_text, vendor_issue = _read_text(vendor_path)

    missing_items = _missing_rules(boundary_text, vendor_text) if boundary_text and vendor_text else []
    if boundary_issue or vendor_issue:
        status = BLOCKED_MISSING_SOURCE
        if boundary_issue:
            missing_items.append(f"boundary_doc.{boundary_issue}")
        if vendor_issue:
            missing_items.append(f"vendor_index.{vendor_issue}")
    elif _has_success_or_control_claim(boundary_text, vendor_text):
        status = BLOCKED_SUCCESS_OR_CONTROL_CLAIM
    elif missing_items:
        status = BLOCKED_MISSING_ALIGNMENT
    else:
        status = READY_STATUS

    summary = _summary(status, boundary_path, vendor_path, boundary_text, vendor_text, missing_items)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": status,
        "hardware_baseline_source_alignment": status,
        "source_docs": {"boundary_doc": _safe_ref(boundary_path), "vendor_index": _safe_ref(vendor_path)},
        "source_load_status": {
            "boundary_doc": "loaded" if not boundary_issue else boundary_issue,
            "vendor_index": "loaded" if not vendor_issue else vendor_issue,
        },
        "required_alignment_rules": {
            "default_hardware_set": [label for label, _pattern in DEFAULT_HARDWARE_RULES],
            "target_sensor_baseline": [label for label, _pattern in TARGET_BASELINE_RULES],
            "vendor_source_boundary": [label for label, _pattern, _source in SOURCE_ALIGNMENT_RULES],
        },
        "default_hardware_set_summary": summary["default_hardware_set_summary"],
        "target_sensor_baseline_summary": summary["target_sensor_baseline_summary"],
        "vendor_source_boundary": summary["vendor_source_boundary"],
        "missing_alignment_items": missing_items,
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "serial_uart",
            "hardware_bus",
            "sensor_driver_runtime",
            "nav2_runtime",
            "hil",
            "field_run",
            "delivery_execution",
        ],
        "review_summary": summary,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return artifact, summary, 0 if status == READY_STATUS else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出目录按需创建，方便 sprint evidence bundle 直接指定 /tmp 或 artifacts 目录。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只读 Markdown，不访问真实硬件、ROS、serial/UART 或现场传感器。
    parser = argparse.ArgumentParser(description="Generate hardware baseline source-alignment software-proof artifact.")
    parser.add_argument("--boundary-md", default=str(DEFAULT_BOUNDARY_MD), help="production_hardware_boundary.md path to review.")
    parser.add_argument("--vendor-index", default=str(DEFAULT_VENDOR_INDEX), help="docs/vendor/VENDOR_INDEX.md path used as local vendor/source boundary.")
    parser.add_argument("--output", default="", help="Write full source-alignment artifact JSON to this path.")
    parser.add_argument("--summary-output", default="", help="Write compact source-alignment summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_baseline_source_alignment(args.boundary_md, args.vendor_index)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_baseline_source_alignment: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"overall_status: {artifact['overall_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
