#!/usr/bin/env python3
"""生成 PR #5 vendor/source review reply 的 fail-closed dispatch 产物。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 这些字段是 Robot/mobile/Product 并行消费的契约，不随 GitHub 文案微调漂移。
SCHEMA = "trashbot.pr5_vendor_source_review_reply_dispatch.v1"
SUMMARY_SCHEMA = "trashbot.pr5_vendor_source_review_reply_dispatch_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"
EVIDENCE_BOUNDARY = "software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate"

# 输入 summary 来自上一轮 packet gate；本脚本只做 reply dispatch，不重新定义硬件事实。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKET_SUMMARY = (
    REPO_ROOT
    / "sprints"
    / "2026.05.20_03-04_pr5-vendor-source-review-packet"
    / "evidence"
    / "pr5_vendor_source_review_packet_summary.json"
)

# Fail-closed 状态必须细分，便于 reviewer 和自动化知道是输入缺失、边界漂移还是文案不安全。
READY_STATUS = "ready_for_manual_github_review_reply_not_proven"
BLOCKED_MISSING_PACKET = "blocked_missing_pr5_vendor_source_review_packet_summary"
BLOCKED_UNSUPPORTED_PACKET = "blocked_unsupported_pr5_vendor_source_review_packet_summary"
BLOCKED_UNSAFE_REPLY = "blocked_unsafe_pr5_vendor_source_review_reply"

# Reply-ready 仍不能当硬件证明；这些缺口必须继续出现在 artifact、summary 和 Markdown 中。
REQUIRED_MISSING_MATERIALS = (
    "real_2d_lidar_sku_source_receipt",
    "real_tof_sku_source_receipt",
    "real_mounting_wiring_power_plan",
    "real_calibration_material",
    "real_sensor_hil_entry",
    "real_nav2_slam_field_pass",
)
REQUIRED_NOT_PROVEN = (
    "2d_lidar_procurement",
    "tof_procurement",
    "2d_lidar_installation_wiring_power",
    "tof_installation_wiring_power",
    "sensor_calibration",
    "sensor_hil_entry",
    "wave_rover_uart_hil",
    "delivery_success",
)

# 这些输入字段如果漂移，说明上一轮 packet 不能支撑安全 reply，必须阻断。
EXPECTED_PACKET_SCHEMA = "trashbot.pr5_vendor_source_review_packet_summary.v1"
EXPECTED_PACKET_BOUNDARY = "software_proof_docker_pr5_vendor_source_review_packet_gate"
EXPECTED_LIDAR_TOF_BOUNDARY = "hardware_material_pending_not_proven"
EXPECTED_VENDOR_ENTRYPOINT = "docs/vendor/VENDOR_INDEX.md"

# 安全扫描只拦截肯定式成功/控制/凭证/本机路径；否定句通过上下文 guard 保护。
STRICT_TRUE_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(hil_pass|field_pass|control_enabled)\s*[:=]\s*true\b"),
)
UNSAFE_PATTERNS = STRICT_TRUE_PATTERNS + (
    re.compile(r"(?i)\b(2D LiDAR|LiDAR|ToF).{0,48}\b(procured|installed|wired|calibrated|HIL passed|field passed)\b"),
    re.compile(r"(?i)\b(procurement|installation|wiring|calibration|HIL|field).{0,36}\b(complete|passed|proven|validated)\b"),
    re.compile(r"(?i)\b(OSS_ACCESS_KEY_SECRET|bearer\s+token|password|private_key)\b"),
    re.compile(r"(?i)\b/Users/[^\s`]+"),
    re.compile(r"(?i)\b/dev/(tty|serial)[^\s`]*"),
)


def _utc_now() -> str:
    # UTC 字符串让多机生成的 evidence 可排序，避免本地时区影响审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_ref(path: Path) -> str:
    # 产物不泄漏本机绝对路径，只保留 repo 相对路径给 review 人工发布使用。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    # 输入缺失也要生成 blocked dispatch，避免自动化只得到 traceback 而没有复核材料。
    try:
        return json.loads(path.expanduser().read_text(encoding="utf-8")), ""
    except FileNotFoundError:
        return {}, "missing"
    except json.JSONDecodeError:
        return {}, "invalid_json"
    except (OSError, UnicodeDecodeError):
        return {}, "read_error"


def _contains_unsafe_claim(text: str) -> bool:
    # 允许“not_proven / pending / must not”这类否定上下文，拦截真正的成功或控制声明。
    guard_words = (
        "fail closed",
        "must fail",
        "must remain",
        "must not",
        "does not prove",
        "do not prove",
        "not proof",
        "not_proven",
        "pending",
        "hardware_material_pending",
        "不证明",
        "不得",
        "不是",
        "未验证",
    )
    for pattern in STRICT_TRUE_PATTERNS:
        for match in pattern.finditer(text):
            context = text[max(0, match.start() - 140) : min(len(text), match.end() + 140)].lower()
            if any(word in context for word in guard_words):
                continue
            return True
    for pattern in UNSAFE_PATTERNS[len(STRICT_TRUE_PATTERNS) :]:
        for match in pattern.finditer(text):
            context = text[max(0, match.start() - 260) : min(len(text), match.end() + 180)].lower()
            if any(word in context for word in guard_words):
                continue
            return True
    return False


def _packet_errors(packet: dict[str, Any]) -> list[str]:
    # 这里逐项验证上一轮 packet，防止 reply 把漂移的输入包装成安全结论。
    errors: list[str] = []
    if packet.get("schema") != EXPECTED_PACKET_SCHEMA:
        errors.append("schema.unsupported")
    if packet.get("thread_id") != THREAD_ID:
        errors.append("thread_id.mismatch")
    if packet.get("source") != SOURCE:
        errors.append("source.not_software_proof")
    if packet.get("proof_boundary") != EXPECTED_PACKET_BOUNDARY:
        errors.append("proof_boundary.unsupported")
    if packet.get("overall_status") != "not_proven":
        errors.append("overall_status.not_not_proven")
    if packet.get("hardware_material_status") != "hardware_material_pending":
        errors.append("hardware_material_status.not_pending")
    if packet.get("delivery_success") is not False:
        errors.append("delivery_success.not_false")
    if packet.get("primary_actions_enabled") is not False:
        errors.append("primary_actions_enabled.not_false")

    boundary = packet.get("vendor_source_boundary") if isinstance(packet.get("vendor_source_boundary"), dict) else {}
    if boundary.get("entrypoint") != EXPECTED_VENDOR_ENTRYPOINT:
        errors.append("vendor_source_boundary.entrypoint_missing")
    if boundary.get("lidar_tof_boundary") != EXPECTED_LIDAR_TOF_BOUNDARY:
        errors.append("vendor_source_boundary.lidar_tof_boundary_unsafe")
    refs = boundary.get("source_refs") if isinstance(boundary.get("source_refs"), list) else []
    if EXPECTED_VENDOR_ENTRYPOINT not in refs:
        errors.append("vendor_source_boundary.vendor_index_ref_missing")

    missing_materials = set(packet.get("missing_materials") or [])
    for item in REQUIRED_MISSING_MATERIALS:
        if item not in missing_materials:
            errors.append(f"missing_materials.{item}.missing")
    not_proven = set(packet.get("not_proven") or [])
    for item in REQUIRED_NOT_PROVEN:
        if item not in not_proven:
            errors.append(f"not_proven.{item}.missing")
    return errors


def _safe_copy(status: str) -> dict[str, str]:
    # safe_copy 可被 UI 或 closeout 复用，但它只描述人工 reply-ready，不描述硬件完成。
    return {
        "status": status,
        "zh": (
            f"PR #5 线程 {THREAD_ID} 已生成可人工发布的 vendor/source review reply。"
            "该 reply 只说明 docs/vendor/VENDOR_INDEX.md 与本地 vendor 文件的 source boundary；"
            "2D LiDAR / ToF 仍是 hardware_material_pending / not_proven，不是采购、安装、标定、HIL 或送达证明。"
        ),
        "en": (
            f"PR #5 thread {THREAD_ID} has a manual vendor/source review reply ready. "
            "The reply only cites docs/vendor/VENDOR_INDEX.md and local vendor source-boundary material; "
            "2D LiDAR and ToF remain hardware_material_pending / not_proven, not procurement, installation, "
            "calibration, HIL, or delivery proof."
        ),
    }


def _markdown_reply(packet: dict[str, Any], status: str) -> str:
    # Markdown 是给人工复制到 GitHub 的内容；明确禁止把 reply-ready 当作 resolved 证据。
    boundary = packet.get("vendor_source_boundary") if isinstance(packet.get("vendor_source_boundary"), dict) else {}
    source_refs = boundary.get("source_refs") if isinstance(boundary.get("source_refs"), list) else []
    refs = "\n".join(f"- `{ref}`" for ref in source_refs)
    missing = "\n".join(f"- `{item}`" for item in REQUIRED_MISSING_MATERIALS)
    next_required = "\n".join(f"- {item}" for item in packet.get("next_required_evidence", []))
    return (
        f"## PR #5 vendor/source reply for `{THREAD_ID}`\n\n"
        "Status: `reply-ready`, `software_proof`, `not_proven`, "
        "`hardware_material_pending`, `delivery_success=false`, "
        "`primary_actions_enabled=false`.\n\n"
        "I checked the local vendor/source boundary for this thread. The repo-local source "
        "entrypoint remains `docs/vendor/VENDOR_INDEX.md`; it points to Orange Pi Zero 3 "
        "references plus WAVE ROVER firmware/vendor-app UART JSON references. Those files "
        "support source attribution only. They do **not** prove project 2D LiDAR / ToF SKU, "
        "purchase, install, wiring, power, calibration, HIL entry, Nav2/SLAM field pass, "
        "or delivery success.\n\n"
        "Source refs used:\n"
        f"{refs}\n\n"
        "Still missing real hardware materials:\n"
        f"{missing}\n\n"
        "Next required evidence before this can become hardware proof:\n"
        f"{next_required}\n\n"
        "This reply is safe to publish manually as a review-thread response, but it is not "
        "an automatic GitHub write, not a request to resolve the thread, and not a real "
        "hardware-material or HIL pass.\n\n"
        f"Dispatch gate: `{EVIDENCE_BOUNDARY}`; reply status: `{status}`.\n"
    )


def _summary(packet: dict[str, Any], status: str, errors: list[str], markdown_file: str) -> dict[str, Any]:
    # Summary 是下游机器复核入口，固定保留 fail-closed 控制字段。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source_schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "thread_id": THREAD_ID,
        "proof_boundary": EVIDENCE_BOUNDARY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_packet_schema": packet.get("schema", ""),
        "source_packet_boundary": packet.get("proof_boundary", ""),
        "reply_status": status,
        "overall_status": "not_proven",
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "vendor_source_boundary": packet.get("vendor_source_boundary", {}),
        "missing_materials": list(REQUIRED_MISSING_MATERIALS),
        "not_proven": list(REQUIRED_NOT_PROVEN),
        "next_required_evidence": packet.get("next_required_evidence", []),
        "safe_copy": _safe_copy(status),
        "markdown_file": markdown_file,
        "blocked_reasons": errors,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def build_pr5_vendor_source_review_reply_dispatch(
    packet_summary: str | Path = DEFAULT_PACKET_SUMMARY,
    markdown_output: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str, int]:
    """把上一轮 packet summary 转为可人工发布的 fail-closed review reply。"""

    packet_path = Path(packet_summary)
    packet, read_issue = _read_json(packet_path)
    packet_errors = [f"packet_summary.{read_issue}"] if read_issue else _packet_errors(packet)
    if read_issue:
        status = BLOCKED_MISSING_PACKET
        exit_code = 2
    elif packet_errors:
        status = BLOCKED_UNSUPPORTED_PACKET
        exit_code = 2
    else:
        status = READY_STATUS
        exit_code = 0

    markdown = _markdown_reply(packet, status)
    # Markdown 自身也要扫描，因为最终发布材料就是这段文本，而不是 JSON 字段。
    if _contains_unsafe_claim(markdown):
        status = BLOCKED_UNSAFE_REPLY
        packet_errors = packet_errors + ["markdown_reply.unsafe_claim"]
        exit_code = 2
        markdown = _markdown_reply(packet, status)

    markdown_file = _safe_ref(Path(markdown_output)) if markdown_output else ""
    summary = _summary(packet, status, packet_errors, markdown_file)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "thread_id": THREAD_ID,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "proof_boundary": EVIDENCE_BOUNDARY,
        "reply_status": status,
        "overall_status": "not_proven",
        "hardware_material_status": "hardware_material_pending",
        "evidence_status": "not_proven",
        "source_packet_summary": _safe_ref(packet_path),
        "source_packet_schema": packet.get("schema", ""),
        "source_packet_boundary": packet.get("proof_boundary", ""),
        "vendor_source_boundary": packet.get("vendor_source_boundary", {}),
        "missing_materials": list(REQUIRED_MISSING_MATERIALS),
        "not_proven": list(REQUIRED_NOT_PROVEN),
        "next_required_evidence": packet.get("next_required_evidence", []),
        "safe_copy": summary["safe_copy"],
        "markdown_reply": markdown,
        "markdown_file": markdown_file,
        "blocked_reasons": packet_errors,
        "non_access_scope": [
            "github_write_api",
            "github_review_thread_mutation",
            "serial_uart",
            "ros_graph",
            "hardware_bus",
            "procurement_system",
            "real_2d_lidar",
            "real_tof",
            "hil",
            "cloud_resource",
            "delivery_execution",
        ],
        "review_summary": summary,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }
    return artifact, summary, markdown, exit_code


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 写 evidence 目录只是生成软件证明产物，不表示真实传感器材料已经到位。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    # Markdown 仅用于人工发布前复核；脚本不调用 GitHub API，也不解析 raw review token。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 是 PC-only generator；没有硬件、网络、ROS 或 GitHub 写副作用。
    parser = argparse.ArgumentParser(description="Generate PR #5 vendor/source review reply dispatch artifacts.")
    parser.add_argument("--packet-summary", default=str(DEFAULT_PACKET_SUMMARY), help="Input packet summary JSON.")
    parser.add_argument("--output", default="", help="Write full dispatch artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact dispatch summary JSON.")
    parser.add_argument("--markdown-output", default="", help="Write manual GitHub review reply Markdown.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, markdown, exit_code = build_pr5_vendor_source_review_reply_dispatch(
        args.packet_summary,
        args.markdown_output or None,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.markdown_output:
        _write_text(args.markdown_output, markdown)
    if args.once_json or not (args.output or args.summary_output or args.markdown_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pr5_vendor_source_review_reply_dispatch: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"summary_file: {Path(args.summary_output).name if args.summary_output else ''}")
        print(f"markdown_file: {Path(args.markdown_output).name if args.markdown_output else ''}")
        print(f"overall_status: {artifact['overall_status']}")
        print(f"reply_status: {artifact['reply_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
