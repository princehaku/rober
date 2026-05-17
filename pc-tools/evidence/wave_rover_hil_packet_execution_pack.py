#!/usr/bin/env python3
"""生成 WAVE ROVER HIL packet execution pack。

该工具只消费上一轮 wave_rover_hil_packet_review_decision artifact 或 summary，
把 review decision 转成真实硬件环境可执行的材料模板和采集顺序。它不打开
串口、不探测 /dev、不调用 ROS graph，也不把 execution pack 升级成 hil_pass。
Vendor 来源见 docs/vendor/VENDOR_INDEX.md、json_cmd.h、uart_ctrl.h、
ugv_rpi/base_ctrl.py 与 ugv_rpi/config.yaml。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.wave_rover_hil_packet_execution_pack.v1"
SUMMARY_SCHEMA = "trashbot.wave_rover_hil_packet_execution_pack_summary.v1"
REVIEW_SCHEMA = "trashbot.wave_rover_hil_packet_review_decision.v1"
REVIEW_SUMMARY_SCHEMA = "trashbot.wave_rover_hil_packet_review_decision_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_wave_rover_hil_packet_execution_pack_gate"
REVIEW_BOUNDARY = "software_proof_docker_wave_rover_hil_packet_review_decision_gate"

# evidence_ref 只允许安全短 token，避免本机路径、串口名或人工说明进入下游。
SAFE_EVIDENCE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")

REQUIRED_REVIEW_NEXT_EVIDENCE = (
    "real WAVE ROVER HIL run",
    "same evidence_ref HIL packet",
    "real feedback_T1001.log",
    "real odom_once.jsonl",
    "real imu_once.jsonl",
    "real battery_once.jsonl",
    "operator_hil_report",
)

REQUIRED_MATERIAL_FILES = (
    "feedback_T1001.log",
    "odom_once.jsonl",
    "imu_once.jsonl",
    "battery_once.jsonl",
    "operator_hil_report",
)

NOT_PROVEN = (
    "real_wave_rover",
    "real_uart",
    "hil_pass",
    "real_odom",
    "real_imu",
    "real_battery",
    "delivery_success",
)

VENDOR_SOURCES = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
)

# 输入摘要不能携带本机路径、串口值、凭证、traceback 或成功/授权断言。
UNSAFE_INPUT_PATTERNS = (
    re.compile(r"/dev/[A-Za-z0-9_.\-/]+"),
    re.compile(r"/Users/[A-Za-z0-9_.\-/]+"),
    re.compile(r"/tmp/[A-Za-z0-9_.\-/]+"),
    re.compile(r"\bserial_(port|device|path)\b", re.IGNORECASE),
    re.compile(r"\bbaud(rate)?\b\s*[:=]\s*\d+", re.IGNORECASE),
    re.compile(r"\braw_(path|packet|feedback)\b", re.IGNORECASE),
    re.compile(r"\b(checksum|traceback)\b", re.IGNORECASE),
    re.compile(r"\b(password|passwd|secret|token|credential|authorization)\b", re.IGNORECASE),
    re.compile(r'"delivery_success"\s*:\s*true', re.IGNORECASE),
    re.compile(r"\bdelivery_success\s*=\s*true\b", re.IGNORECASE),
    re.compile(r'"primary_actions_enabled"\s*:\s*true', re.IGNORECASE),
    re.compile(r"\bprimary_actions_enabled\s*=\s*true\b", re.IGNORECASE),
    re.compile(r"\bhil_pass\s*[:=]\s*(true|pass|passed|success|ok)\b", re.IGNORECASE),
    re.compile(r"\b(hil_passed|hil pass(ed)?|hil success)\b", re.IGNORECASE),
)


def _utc_now() -> str:
    # UTC 只用于 artifact 排序，不代表真实上车采集时间。
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺 review summary 是可预期 blocked 状态，不把异常栈带入 artifact。
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
    # wrapper 输入只接受 object；其它形态按空对象 fail-closed。
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    # 上游字段可能缺失；缺失按空列表进入 contract 检查。
    return list(value) if isinstance(value, (list, tuple)) else []


def _text(value: Any, default: str = "") -> str:
    # 所有下游可见字段先收窄为短字符串，避免复制对象 repr。
    if value is None:
        return default
    text = value.strip() if isinstance(value, str) else str(value).strip()
    return text or default


def _safe_ref(value: str) -> bool:
    # evidence_ref 是唯一允许跨 PC、Robot、mobile 展示的关联键。
    return bool(value and SAFE_EVIDENCE_REF.match(value))


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 兼容 artifact、summary、diagnostics wrapper 和通用 envelope。
    candidates = [payload]
    for key in (
        "wave_rover_hil_packet_review_decision",
        "wave_rover_hil_packet_review_decision_summary",
        "review_decision",
        "review_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        nested = payload.get(key)
        if isinstance(nested, dict):
            candidates.extend(_source_candidates(nested))
    return candidates


def _effective_review(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选 schema 命中的 review decision；否则保留顶层用于解释 fail-closed。
    for candidate in _source_candidates(payload):
        schema = _text(candidate.get("schema"))
        summary_schema = _text(candidate.get("summary_schema"))
        if schema in {REVIEW_SCHEMA, REVIEW_SUMMARY_SCHEMA} or summary_schema == REVIEW_SUMMARY_SCHEMA:
            return candidate
    return payload


def _scan_unsafe_input(payload: dict[str, Any]) -> list[str]:
    # 扫描完整序列化输入可覆盖嵌套 note 里的危险成功文案。
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return [f"unsafe_input:{pattern.pattern}" for pattern in UNSAFE_INPUT_PATTERNS if pattern.search(encoded)]


def _schema_status(payload: dict[str, Any], review: dict[str, Any]) -> str:
    # 只消费上一轮 review-decision gate，避免误把 intake 或 Robot summary 当源。
    schema = _text(review.get("schema") or payload.get("schema"))
    summary_schema = _text(review.get("summary_schema") or payload.get("summary_schema"))
    boundary = _text(review.get("evidence_boundary") or payload.get("evidence_boundary"))
    source = _text(review.get("source") or payload.get("source"))
    if schema and schema not in {REVIEW_SCHEMA, REVIEW_SUMMARY_SCHEMA}:
        return "unsupported_schema"
    if not schema and summary_schema != REVIEW_SUMMARY_SCHEMA:
        return "unsupported_schema"
    if boundary != REVIEW_BOUNDARY:
        return "unsupported_boundary"
    if source != SOURCE:
        return "unsupported_source"
    return "supported"


def _flag_status(review: dict[str, Any]) -> list[str]:
    # 三个边界 flag 是真实 HIL 前的硬门槛，缺失即 fail closed。
    issues: list[str] = []
    if review.get("delivery_success") is not False:
        issues.append("delivery_success_not_false")
    if review.get("primary_actions_enabled") is not False:
        issues.append("primary_actions_enabled_not_false")
    if review.get("same_evidence_ref_required") is not True:
        issues.append("same_evidence_ref_required_not_true")
    not_proven = {str(item) for item in _list(review.get("not_proven"))}
    missing_not_proven = [item for item in NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        issues.append("not_proven_missing:" + ",".join(missing_not_proven))
    return issues


def _evidence_ref_status(review: dict[str, Any], expected_ref: str) -> tuple[str, list[str]]:
    # CLI 指定 ref 时必须与 review decision 完全一致。
    observed = _text(review.get("evidence_ref"))
    issues: list[str] = []
    if not _safe_ref(observed):
        issues.append("review_evidence_ref_missing_or_unsafe")
    if expected_ref and not _safe_ref(expected_ref):
        issues.append("requested_evidence_ref_unsafe")
    if expected_ref and observed and expected_ref != observed:
        issues.append("requested_evidence_ref_mismatch")
    return observed if _safe_ref(observed) else "", issues


def _review_material_issues(review: dict[str, Any]) -> list[str]:
    # review decision 必须继续要求真实材料，execution pack 才能有明确采集目标。
    issues: list[str] = []
    next_required = {str(item) for item in _list(review.get("next_required_evidence"))}
    missing_next = [item for item in REQUIRED_REVIEW_NEXT_EVIDENCE if item not in next_required]
    if missing_next:
        issues.append("next_required_evidence_missing:" + ",".join(missing_next))
    missing_required = {str(item) for item in _list(review.get("missing_required_materials"))}
    for name in REQUIRED_MATERIAL_FILES:
        if not any(name in item for item in missing_required):
            issues.append(f"missing_required_material_not_declared:{name}")
    return issues


def _execution_status(load_issue: str, schema_status: str, review: dict[str, Any], issues: list[str]) -> str:
    # blocked_pending_real_hil_packet 是本 gate 的可执行源状态，不代表 HIL 已通过。
    if load_issue:
        return "blocked_missing_wave_rover_hil_packet_review_decision"
    if schema_status != "supported":
        return "blocked_unsupported_wave_rover_hil_packet_review_decision"
    if any(issue.startswith("unsafe_input") for issue in issues):
        return "blocked_unsafe_wave_rover_hil_packet_claim"
    if "requested_evidence_ref_mismatch" in issues or "review_evidence_ref_missing_or_unsafe" in issues:
        return "blocked_wave_rover_hil_packet_evidence_ref_mismatch"
    if _text(review.get("review_decision") or review.get("status")) != "blocked_pending_real_hil_packet":
        return "blocked_review_decision_not_ready"
    if issues:
        return "blocked_wave_rover_hil_packet_execution_pack_contract"
    return "ready_for_real_hil_collection_not_proven"


def _required_material_templates(evidence_ref: str) -> list[dict[str, Any]]:
    # 模板只描述真实硬件环境要带回的材料，不生成任何实测数据。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        {
            "file": "feedback_T1001.log",
            "vendor_basis": "json_cmd.h FEEDBACK_BASE_INFO 1001; base_ctrl.py newline JSON read",
            "required_fields": ["evidence_ref", "timestamp", "raw_line", "T=1001"],
            "collection_note": f"Collect real base feedback line under evidence_ref={ref}.",
        },
        {
            "file": "odom_once.jsonl",
            "vendor_basis": "uart_ctrl.h dispatch plus vendor UART JSON feedback; project odom must be real runtime output",
            "required_fields": ["evidence_ref", "stamp", "frame_id", "child_frame_id", "pose", "twist"],
            "collection_note": f"Capture one real /odom sample linked to evidence_ref={ref}.",
        },
        {
            "file": "imu_once.jsonl",
            "vendor_basis": "json_cmd.h CMD_GET_IMU_DATA / IMU feedback family",
            "required_fields": ["evidence_ref", "stamp", "orientation_or_status", "angular_velocity_or_status"],
            "collection_note": f"Capture one real /imu/data sample linked to evidence_ref={ref}.",
        },
        {
            "file": "battery_once.jsonl",
            "vendor_basis": "config.yaml fb.base_voltage and WAVE ROVER feedback contract",
            "required_fields": ["evidence_ref", "stamp", "voltage_or_percentage", "source"],
            "collection_note": f"Capture one real /battery sample linked to evidence_ref={ref}.",
        },
        {
            "file": "operator_hil_report",
            "vendor_basis": "VENDOR_INDEX.md requires local vendor source and real hardware evidence separation",
            "required_fields": ["evidence_ref", "operator", "host", "serial_confirmed", "observed_result", "open_risks"],
            "collection_note": "Write operator report after real collection; do not mark hil_pass inside this software-proof pack.",
        },
    ]


def _collection_sequence(evidence_ref: str) -> list[str]:
    # 顺序先确认环境再采集材料，避免先跑 gate 后补事实的证据倒置。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        "confirm WAVE ROVER UART access on target host",
        f"collect same evidence_ref feedback_T1001.log with evidence_ref={ref}",
        f"capture odom_once.jsonl with evidence_ref={ref}",
        f"capture imu_once.jsonl with evidence_ref={ref}",
        f"capture battery_once.jsonl with evidence_ref={ref}",
        f"write operator_hil_report with evidence_ref={ref}",
        "rerun packet intake and review decision gates before claiming any HIL result",
    ]


def _owner_handoff() -> dict[str, str]:
    # handoff 只描述补证动作，不给机器人下发控制许可。
    return {
        "hardware-engineer": "run real HIL collection on WAVE ROVER host and keep one evidence_ref across all packet files",
        "robot-software-engineer": "consume only accepted review-decision summaries until real packet exists",
        "full-stack-software-engineer": "keep mobile execution pack read-only and actions disabled",
    }


def _backfill_guidance(evidence_ref: str) -> list[str]:
    # backfill guidance 用来补真实材料，不允许反写成功状态到本 pack。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"Use evidence_ref={ref} for every file in the real HIL packet.",
        "Backfill missing packet files into a single material directory before rerunning intake.",
        "If any file is synthetic, mismatched, or placeholder-only, keep review_decision blocked.",
        "Do not change delivery_success=false or primary_actions_enabled=false from this execution pack.",
    ]


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只调用 PC evidence gates；真实串口采集由 operator 在硬件主机完成。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/wave_rover_hil_packet_intake.py --packet-dir <real_packet_dir> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/wave_rover_hil_packet_review_decision.py --intake-summary <summary.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/wave_rover_hil_packet_execution_pack.py --review-summary <summary.json> --evidence-ref {ref} --once-json",
        "keep delivery_success=false and primary_actions_enabled=false until real HIL packet is reviewed",
    ]


def _summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # summary 是 Robot/mobile 的稳定白名单视图，不包含 raw source artifact。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": "not_proven",
        "status": artifact["execution_pack_status"],
        "execution_pack_status": artifact["execution_pack_status"],
        "wave_rover_hil_packet_execution_pack": artifact["execution_pack_status"],
        "evidence_ref": artifact["evidence_ref"],
        "same_evidence_ref_required": True,
        "required_material_templates": [item["file"] for item in artifact["required_material_templates"]],
        "collection_sequence": artifact["collection_sequence"],
        "owner_handoff": artifact["owner_handoff"],
        "backfill_guidance": artifact["backfill_guidance"],
        "rerun_commands": artifact["rerun_commands"],
        "vendor_sources": list(VENDOR_SOURCES),
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "boundary_note": "software_proof only; not_proven; delivery_success=false; primary_actions_enabled=false",
    }


def build_execution_pack(
    review_summary: str | Path | None = None,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 review decision artifact/summary，生成 WAVE ROVER HIL packet execution pack。"""

    path = Path(review_summary) if review_summary else None
    payload, load_issue = _read_json(path)
    review = _effective_review(payload)
    schema_status = "missing" if load_issue else _schema_status(payload, review)
    observed_ref, ref_issues = _evidence_ref_status(review, evidence_ref.strip()) if not load_issue else ("", ["review_evidence_ref_missing_or_unsafe"])
    issues = sorted(
        set(
            ([] if not load_issue else [f"review_summary:{load_issue}"])
            + ([] if schema_status in {"supported", "missing"} else [schema_status])
            + _scan_unsafe_input(payload)
            + _flag_status(review)
            + ref_issues
            + _review_material_issues(review)
        )
    )
    status = _execution_status(load_issue, schema_status, review, issues)

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "summary_schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": "not_proven",
        "execution_pack_status": status,
        "wave_rover_hil_packet_execution_pack": status,
        "source_review_schema": _text(review.get("schema") or payload.get("schema"), "missing"),
        "source_review_summary_schema": _text(review.get("summary_schema") or payload.get("summary_schema"), "missing"),
        "source_review_boundary": _text(review.get("evidence_boundary") or payload.get("evidence_boundary"), "missing"),
        "source_review_decision": _text(review.get("review_decision") or review.get("status"), "missing"),
        "schema_status": schema_status,
        "same_evidence_ref_required": True,
        "evidence_ref": observed_ref,
        "required_material_templates": _required_material_templates(observed_ref),
        "collection_sequence": _collection_sequence(observed_ref),
        "owner_handoff": _owner_handoff(),
        "backfill_guidance": _backfill_guidance(observed_ref),
        "rerun_commands": _rerun_commands(observed_ref),
        "issues": issues,
        "vendor_sources": list(VENDOR_SOURCES),
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "non_access_scope": [
            "serial_uart",
            "dev_device_probe",
            "ros_graph",
            "cmd_vel",
            "hardware_bus",
            "hil_runtime",
            "delivery_execution",
        ],
        "boundary_note": "software_proof only; not_proven; delivery_success=false; primary_actions_enabled=false",
    }
    summary = _summary(artifact)
    artifact["execution_pack_summary"] = summary
    exit_code = 0 if status == "ready_for_real_hil_collection_not_proven" else 2
    return artifact, summary, exit_code


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出路径只用于写文件，不进入 artifact，避免本机路径泄漏给下游。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI dependency-free，可在 PC/Docker/unittest 中运行，不依赖 ROS2 或真实硬件。
    parser = argparse.ArgumentParser(
        description="Generate WAVE ROVER HIL packet execution-pack software-proof artifact."
    )
    parser.add_argument("--review-summary", default="", help="Previous wave_rover_hil_packet_review_decision artifact or summary JSON.")
    parser.add_argument("--evidence-ref", default="", help="Optional expected safe evidence_ref shared with the review summary.")
    parser.add_argument("--output", default="", help="Write full execution-pack artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact execution-pack summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_execution_pack(args.review_summary or None, args.evidence_ref)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("wave_rover_hil_packet_execution_pack: artifact_file:" + (Path(args.output).name if args.output else ""))
        print(f"execution_pack_status: {artifact['execution_pack_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
