#!/usr/bin/env python3
"""生成 PR #5 review thread closeout 的软件证明 artifact。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 下游 Robot/mobile 只消费 schema 和 summary；这里固定契约避免 review closeout 被口头解释放宽。
SCHEMA = "trashbot.pr5_review_thread_closeout.v1"
SUMMARY_SCHEMA = "trashbot.pr5_review_thread_closeout_summary.v1"
THREAD_SUMMARY_SCHEMA = "trashbot.pr5_review_thread_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_pr5_review_thread_closeout_gate"

# 本 gate 只读 repo 文档；不会读取 GitHub token、真实串口、ROS graph 或硬件总线。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BOUNDARY_MD = REPO_ROOT / "docs" / "product" / "production_hardware_boundary.md"
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"
DEFAULT_OKR = REPO_ROOT / "OKR.md"

CLOSEOUT_NOT_PROVEN = "pr5_review_thread_closeout_not_proven"
BLOCKED_MISSING_REPO_EVIDENCE = "blocked_missing_pr5_review_thread_closeout_repo_evidence"
BLOCKED_UNSUPPORTED_THREAD_SUMMARY = "blocked_unsupported_pr5_review_thread_summary"
BLOCKED_UNSAFE_CLAIM = "blocked_unsafe_pr5_review_thread_closeout_claim"

READY_TO_CLOSE = "ready_to_close_on_mainline_docs"
BLOCKED_PENDING_REAL_MATERIALS = "blocked_pending_real_materials"
STILL_OPEN = "still_open_missing_current_evidence"

# 只保留 thread 的安全元数据，避免把 GitHub 原始 review 文本或 token 类内容写入 artifact。
DEFAULT_THREAD_SUMMARY: dict[str, Any] = {
    "schema": THREAD_SUMMARY_SCHEMA,
    "schema_version": SCHEMA_VERSION,
    "source": SOURCE,
    "pr": {
        "number": 5,
        "title": "Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline",
    },
    "threads": [
        {
            "thread_key": "p1_production_hardware_boundary_default_vs_mandatory_sensor_baseline",
            "severity": "P1",
            "topic": "production_hardware_boundary default hardware set vs mandatory sensor baseline",
        },
        {
            "thread_key": "p2_okr_lowest_objective_narrative_vs_table",
            "severity": "P2",
            "topic": "OKR lowest objective narrative must match progress table",
        },
        {
            "thread_key": "p2_mandatory_sensor_assumptions_missing_vendor_citation",
            "severity": "P2",
            "topic": "mandatory sensor assumptions require docs/vendor citation and real material boundary",
        },
    ],
}

REQUIRED_THREAD_KEYS = tuple(thread["thread_key"] for thread in DEFAULT_THREAD_SUMMARY["threads"])

# not_proven 列表是显式边界，不允许 ready_to_close 被误读成硬件或现场通过。
NOT_PROVEN = (
    "real_2d_lidar_sku_source_receipt",
    "real_tof_sku_source_receipt",
    "real_install_wiring_power_calibration",
    "real_sensor_hil_entry",
    "real_wave_rover_uart_hil",
    "route_elevator_field_pass",
    "objective_5_external_proof",
    "delivery_success",
)

MISSING_REAL_MATERIALS = (
    "real_2d_lidar_sku_source_receipt",
    "real_tof_sku_source_receipt",
    "real_install_wiring_power_calibration",
    "real_hil_entry",
)

STRICT_TRUE_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(hil_pass|field_pass|control_enabled)\s*[:=]\s*true\b"),
)

UNSAFE_PATTERNS = STRICT_TRUE_PATTERNS + (
    re.compile(r"(?i)\b(procurement|installation|wiring|calibration|field|HIL).{0,32}\b(complete|passed|proven|validated)\b"),
    re.compile(r"(?i)\b(OSS_ACCESS_KEY_SECRET|bearer\s+token|password|private_key)\b"),
    re.compile(r"(?i)\b/Users/[^\\s`]+"),
    re.compile(r"(?i)\b/dev/(tty|serial)[^\\s`]*"),
)


def _utc_now() -> str:
    # UTC 便于 Docker-only evidence bundle 在不同机器上按字面排序。
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: Path) -> tuple[str, str]:
    # 缺文件也返回 artifact，而不是 traceback；review closeout 必须可解释地 fail closed。
    try:
        return path.expanduser().read_text(encoding="utf-8"), ""
    except FileNotFoundError:
        return "", "missing"
    except (OSError, UnicodeDecodeError):
        return "", "read_error"


def _safe_ref(path: Path) -> str:
    # artifact 不泄漏开发机绝对路径，只保留 repo 相对引用供 reviewer 定位。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _has(text: str, pattern: str, flags: int = re.I | re.S) -> bool:
    # 文档措辞会轻微变化，所以规则用语义 regex，而不是脆弱的整句匹配。
    return re.search(pattern, text, flags) is not None


def _read_thread_summary(path: str | Path | None) -> tuple[dict[str, Any], list[str]]:
    # 默认 summary 来自本 sprint 安全摘要；外部 JSON 只用于后续复核，不接受任意 schema。
    if not path:
        return DEFAULT_THREAD_SUMMARY, []
    payload_text, issue = _read_text(Path(path))
    if issue:
        return {"schema": "missing"}, [f"thread_summary.{issue}"]
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        return {"schema": "bad_json"}, ["thread_summary.bad_json"]
    issues = _validate_thread_summary(payload)
    return payload, issues


def _validate_thread_summary(payload: dict[str, Any]) -> list[str]:
    # thread summary 只允许白名单字段；避免把原始 review body、token 或本机路径传播出去。
    issues: list[str] = []
    if payload.get("schema") != THREAD_SUMMARY_SCHEMA:
        issues.append("thread_summary.unsupported_schema")
    if payload.get("source") != SOURCE:
        issues.append("thread_summary.unsupported_source")
    threads = payload.get("threads")
    if not isinstance(threads, list):
        return issues + ["thread_summary.missing_threads"]
    keys = {thread.get("thread_key") for thread in threads if isinstance(thread, dict)}
    for key in REQUIRED_THREAD_KEYS:
        if key not in keys:
            issues.append(f"thread_summary.missing.{key}")
    if _contains_unsafe_claim(json.dumps(payload, ensure_ascii=False)):
        issues.append("thread_summary.unsafe_claim")
    return issues


def _contains_unsafe_claim(text: str) -> bool:
    # 文档会列出“哪些成功断言必须 fail closed”；这些禁止样例不是成功声明本身。
    guard_words = (
        "fail closed",
        "must fail",
        "must remain",
        "must not",
        "does not prove",
        "do not treat",
        "do not prove",
        "not prove",
        "not a claim",
        "not a ",
        "not local",
        "not_proven",
        "pending",
        "material_status",
        "not prove a real",
        "不证明",
        "不得",
        "不是",
        "不进入",
        "不暴露",
        "敏感凭证",
    )
    for pattern in STRICT_TRUE_PATTERNS:
        for match in pattern.finditer(text):
            # true 型控制字段只看局部行窗；大段 not_proven 上下文不能掩盖同一行危险断言。
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.end())
            local = text[line_start : min(len(text), (line_end if line_end != -1 else len(text)) + 100)].lower()
            if "fail closed" in local or "must fail" in local or "every output must remain" in local:
                continue
            return True
    for pattern in UNSAFE_PATTERNS[len(STRICT_TRUE_PATTERNS) :]:
        for match in pattern.finditer(text):
            context = text[max(0, match.start() - 320) : min(len(text), match.end() + 180)].lower()
            if any(word in context for word in guard_words):
                continue
            return True
    return False


def _source_load_status(boundary_issue: str, vendor_issue: str, okr_issue: str, summary_issues: list[str]) -> dict[str, str]:
    return {
        "production_hardware_boundary": "loaded" if not boundary_issue else boundary_issue,
        "vendor_index": "loaded" if not vendor_issue else vendor_issue,
        "okr": "loaded" if not okr_issue else okr_issue,
        "thread_summary": "loaded" if not summary_issues else "blocked",
    }


def _evidence_checks(boundary_text: str, vendor_text: str, okr_text: str) -> dict[str, bool]:
    # 这些检查对应 PR #5 三条 unresolved thread 的最小 repo-local 证据。
    default_section_separates_target = (
        _has(boundary_text, r"## Default Hardware Set")
        and not _has(_default_hardware_section(boundary_text), r"\b(2D LiDAR|LiDAR|ToF)\b")
        and _has(boundary_text, r"Navigation/Sensing Baseline .*?Procurement Validation Pending")
    )
    target_baseline_pending = (
        _has(boundary_text, r"monocular camera \+ one 2D LiDAR \+ ToF safety ring")
        and _has(boundary_text, r"2D\s+LiDAR and ToF ring are target hardware pending procurement/source\s+attribution.*?HIL evidence")
        and _has(boundary_text, r"Acceptance rule: do not treat 2D LiDAR or ToF as part of the Default Hardware\s+Set")
    )
    vendor_citation_boundary = (
        _has(boundary_text, r"docs/vendor/VENDOR_INDEX\.md")
        and _has(boundary_text, r"local vendor tree does not prove.*?2D LiDAR or ToF")
        and _has(vendor_text, r"## Complete Material Coverage")
        and _has(vendor_text, r"Orange Pi Zero 3")
        and _has(vendor_text, r"WAVE ROVER")
        and _has(vendor_text, r"UART.*?newline-delimited JSON")
    )
    okr_lowest_consistent = _okr_lowest_objective_is_consistent(okr_text)
    return {
        "default_section_separates_target": default_section_separates_target,
        "target_baseline_pending": target_baseline_pending,
        "vendor_citation_boundary": vendor_citation_boundary,
        "okr_lowest_consistent": okr_lowest_consistent,
    }


def _default_hardware_section(boundary_text: str) -> str:
    # 只检查 Default Hardware Set 的 bullet，防止后续 target baseline 的 LiDAR/ToF 误伤默认集。
    match = re.search(r"^## Default Hardware Set\s*$", boundary_text, re.I | re.M)
    if not match:
        return ""
    next_heading = re.search(r"^##\s+", boundary_text[match.end() :], re.M)
    end = match.end() + next_heading.start() if next_heading else len(boundary_text)
    return boundary_text[match.end() : end]


def _okr_lowest_objective_is_consistent(okr_text: str) -> bool:
    # PR #5 的 P2 不是重新计算 OKR，只核对表格最低项与叙述是否同指 Objective 5。
    table_match = re.search(r"\|\s*Objective 5[^|]*\|\s*约\s*68%\s*\|", okr_text)
    narrative_match = re.search(r"当前数值最低完成度仍是 Objective 5（约 68%）", okr_text)
    stop_rule_match = re.search(r"真实外部材料.*?O5 completion", okr_text, re.S)
    return bool(table_match and narrative_match and stop_rule_match)


def _thread_decisions(checks: dict[str, bool], forced_decision: str | None = None) -> list[dict[str, Any]]:
    # forced_decision 只用于源文件缺失或 unsafe 输入时统一 fail closed。
    decisions: list[dict[str, Any]] = []
    for thread in DEFAULT_THREAD_SUMMARY["threads"]:
        key = thread["thread_key"]
        decision, reasons, evidence_refs = _decision_for_thread(key, checks, forced_decision)
        decisions.append(
            {
                "thread_key": key,
                "severity": thread["severity"],
                "topic": thread["topic"],
                "decision": decision,
                "current_evidence_refs": evidence_refs,
                "decision_reasons": reasons,
                "missing_real_materials": list(MISSING_REAL_MATERIALS),
                "owner_handoff": _owner_handoff(decision),
            }
        )
    return decisions


def _decision_for_thread(
    thread_key: str,
    checks: dict[str, bool],
    forced_decision: str | None,
) -> tuple[str, list[str], list[str]]:
    # 每条 thread 独立判定，避免一个文档 ready 掩盖另一个 thread 仍缺证据。
    if forced_decision:
        return forced_decision, ["forced_fail_closed_due_to_missing_or_unsafe_input"], []
    if thread_key == "p1_production_hardware_boundary_default_vs_mandatory_sensor_baseline":
        ready = checks["default_section_separates_target"] and checks["target_baseline_pending"] and checks["vendor_citation_boundary"]
        return (
            READY_TO_CLOSE if ready else STILL_OPEN,
            ["default_hardware_set_separated_from_lidar_tof_target", "lidar_tof_target_marked_pending_not_proven"] if ready else ["missing_default_vs_target_boundary_evidence"],
            [
                "docs/product/production_hardware_boundary.md#Default Hardware Set",
                "docs/product/production_hardware_boundary.md#Vendor/Source Attribution Boundary",
                "docs/product/production_hardware_boundary.md#Navigation/Sensing Baseline (Product Target, Procurement Validation Pending)",
                "docs/vendor/VENDOR_INDEX.md#Complete Material Coverage",
            ],
        )
    if thread_key == "p2_okr_lowest_objective_narrative_vs_table":
        return (
            READY_TO_CLOSE if checks["okr_lowest_consistent"] else STILL_OPEN,
            ["okr_table_and_priority_narrative_both_identify_objective_5_as_lowest"] if checks["okr_lowest_consistent"] else ["okr_lowest_objective_table_or_narrative_mismatch"],
            ["OKR.md#4.1 当前 OKR 进度快照", "OKR.md#6. 当前最高优先级"],
        )
    if thread_key == "p2_mandatory_sensor_assumptions_missing_vendor_citation":
        if checks["vendor_citation_boundary"] and checks["target_baseline_pending"]:
            return (
                BLOCKED_PENDING_REAL_MATERIALS,
                ["vendor_boundary_is_cited_but_real_lidar_tof_materials_are_still_missing"],
                [
                    "docs/product/production_hardware_boundary.md#Vendor/Source Attribution Boundary",
                    "docs/product/production_hardware_boundary.md#Navigation/Sensing Baseline (Product Target, Procurement Validation Pending)",
                    "docs/vendor/VENDOR_INDEX.md#Complete Material Coverage",
                ],
            )
        return STILL_OPEN, ["missing_vendor_citation_or_pending_material_boundary"], []
    return STILL_OPEN, ["unknown_thread_key"], []


def _owner_handoff(decision: str) -> str:
    # Handoff 文案明确 reviewer closeout 与真实履约材料是两件事。
    if decision == READY_TO_CLOSE:
        return "Hardware can ask reviewer to close this docs-only thread; real hardware materials stay not_proven."
    if decision == BLOCKED_PENDING_REAL_MATERIALS:
        return "Hardware cannot claim closure of real material obligations until SKU/source/receipt/install/wiring/calibration/HIL-entry evidence exists."
    return "Keep thread open; update mainline docs or evidence before requesting closeout."


def _summary(
    status: str,
    thread_decisions: list[dict[str, Any]],
    source_status: dict[str, str],
    checks: dict[str, bool],
    thread_summary: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 Robot diagnostics/mobile 的首选消费面，保持字段短且 fail-closed。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source_schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": "not_proven",
        "closeout_status": status,
        "pr": thread_summary.get("pr", DEFAULT_THREAD_SUMMARY["pr"]),
        "source_load_status": source_status,
        "evidence_checks": checks,
        "thread_decisions": thread_decisions,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_pr5_review_thread_closeout(
    boundary_md: str | Path = DEFAULT_BOUNDARY_MD,
    vendor_index: str | Path = DEFAULT_VENDOR_INDEX,
    okr_md: str | Path = DEFAULT_OKR,
    thread_summary: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 mainline 文档，生成 PR #5 review thread closeout artifact。"""

    boundary_path = Path(boundary_md)
    vendor_path = Path(vendor_index)
    okr_path = Path(okr_md)
    boundary_text, boundary_issue = _read_text(boundary_path)
    vendor_text, vendor_issue = _read_text(vendor_path)
    okr_text, okr_issue = _read_text(okr_path)
    safe_thread_summary, summary_issues = _read_thread_summary(thread_summary)
    source_status = _source_load_status(boundary_issue, vendor_issue, okr_issue, summary_issues)

    all_text = "\n".join([boundary_text, vendor_text, okr_text, json.dumps(safe_thread_summary, ensure_ascii=False)])
    checks = _evidence_checks(boundary_text, vendor_text, okr_text) if boundary_text and vendor_text and okr_text else {
        "default_section_separates_target": False,
        "target_baseline_pending": False,
        "vendor_citation_boundary": False,
        "okr_lowest_consistent": False,
    }

    if boundary_issue or vendor_issue or okr_issue:
        status = BLOCKED_MISSING_REPO_EVIDENCE
        forced_decision = STILL_OPEN
        exit_code = 2
    elif summary_issues:
        status = BLOCKED_UNSUPPORTED_THREAD_SUMMARY
        forced_decision = STILL_OPEN
        exit_code = 2
    elif _contains_unsafe_claim(all_text):
        status = BLOCKED_UNSAFE_CLAIM
        forced_decision = STILL_OPEN
        exit_code = 2
    else:
        status = CLOSEOUT_NOT_PROVEN
        forced_decision = None
        exit_code = 0

    decisions = _thread_decisions(checks, forced_decision)
    if any(item["decision"] == STILL_OPEN for item in decisions):
        exit_code = 2
    summary = _summary(status, decisions, source_status, checks, safe_thread_summary)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": "not_proven",
        "closeout_status": status,
        "pr": safe_thread_summary.get("pr", DEFAULT_THREAD_SUMMARY["pr"]),
        "source_docs": {
            "production_hardware_boundary": _safe_ref(boundary_path),
            "vendor_index": _safe_ref(vendor_path),
            "okr": _safe_ref(okr_path),
        },
        "source_load_status": source_status,
        "thread_summary_schema": safe_thread_summary.get("schema"),
        "thread_summary_issues": summary_issues,
        "evidence_checks": checks,
        "thread_decisions": decisions,
        "missing_real_materials": list(MISSING_REAL_MATERIALS),
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "github_api_raw_review_body",
            "ros_graph",
            "serial_uart",
            "hardware_bus",
            "sensor_driver_runtime",
            "procurement_system",
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
    # CLI 输出用于 sprint evidence；创建目录不代表创建真实硬件证据。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _resolve_output_paths(output_dir: str, output: str, summary_output: str) -> tuple[str, str]:
    # --output-dir 是 sprint 计划里的兼容入口；显式文件路径仍保留最高优先级，便于旧脚本无感运行。
    if not output_dir:
        return output, summary_output
    target_dir = Path(output_dir).expanduser()
    return (
        output or str(target_dir / "pr5_review_thread_closeout.json"),
        summary_output or str(target_dir / "pr5_review_thread_closeout_summary.json"),
    )


def main(argv: list[str] | None = None) -> int:
    # CLI 是 Docker-only repo-local gate，不访问 GitHub、硬件、ROS 或外部云。
    parser = argparse.ArgumentParser(description="Generate PR #5 review thread closeout software-proof artifact.")
    parser.add_argument("--boundary-md", default=str(DEFAULT_BOUNDARY_MD), help="production_hardware_boundary.md path.")
    parser.add_argument("--vendor-index", default=str(DEFAULT_VENDOR_INDEX), help="docs/vendor/VENDOR_INDEX.md path.")
    parser.add_argument("--okr-md", default=str(DEFAULT_OKR), help="OKR.md path.")
    parser.add_argument("--thread-summary", default="", help="Optional safe PR #5 thread summary JSON.")
    parser.add_argument(
        "--output-dir",
        default="",
        help="Write pr5_review_thread_closeout.json and pr5_review_thread_closeout_summary.json under this directory.",
    )
    parser.add_argument("--output", default="", help="Write full closeout artifact JSON to this path.")
    parser.add_argument("--summary-output", default="", help="Write compact closeout summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_pr5_review_thread_closeout(
        args.boundary_md,
        args.vendor_index,
        args.okr_md,
        args.thread_summary or None,
    )
    output_path, summary_output_path = _resolve_output_paths(args.output_dir, args.output, args.summary_output)
    if output_path:
        _write_json(output_path, artifact)
    if summary_output_path:
        _write_json(summary_output_path, summary)
    if args.once_json or not (output_path or summary_output_path):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pr5_review_thread_closeout: artifact_file:{Path(output_path).name if output_path else ''}")
        print(f"summary_file: {Path(summary_output_path).name if summary_output_path else ''}")
        print(f"overall_status: {artifact['overall_status']}")
        print(f"closeout_status: {artifact['closeout_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
