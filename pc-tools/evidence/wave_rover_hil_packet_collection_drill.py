#!/usr/bin/env python3
"""生成 WAVE ROVER HIL packet collection drill gate。

该工具只消费上一轮 wave_rover_hil_packet_execution_pack artifact 或 summary，
把材料模板、采集顺序和 handoff 收窄成现场可执行的 collection drill。
它不打开串口、不读取 /dev、不 import ROS2、不发送 WAVE ROVER 命令，也不
把 Docker-only drill 升级成真实 HIL 或 reviewer resolved。
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


SCHEMA = "trashbot.wave_rover_hil_packet_collection_drill.v1"
SUMMARY_SCHEMA = "trashbot.wave_rover_hil_packet_collection_drill_summary.v1"
EXECUTION_PACK_SCHEMA = "trashbot.wave_rover_hil_packet_execution_pack.v1"
EXECUTION_PACK_SUMMARY_SCHEMA = "trashbot.wave_rover_hil_packet_execution_pack_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_wave_rover_hil_packet_collection_drill_gate"
EXECUTION_PACK_BOUNDARY = "software_proof_docker_wave_rover_hil_packet_execution_pack_gate"

# evidence_ref 只能是跨 PC、Robot、mobile 展示的短 token，不能夹带路径或设备值。
SAFE_EVIDENCE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")

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
    "real_2d_lidar",
    "real_tof",
    "delivery_success",
    "pr5_reviewer_resolved",
)

VENDOR_SOURCES = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
)

# 输入扫描只拦截运行时敏感值和成功断言；vendor 文件名里的 uart_ctrl.h 是允许来源。
UNSAFE_INPUT_PATTERNS = (
    re.compile(r"/dev/[A-Za-z0-9_.\-/]+"),
    re.compile(r"/Users/[A-Za-z0-9_.\-/]+"),
    re.compile(r"/tmp/[A-Za-z0-9_.\-/]+"),
    re.compile(r"\btty[A-Za-z0-9_.-]*\b", re.IGNORECASE),
    re.compile(r"\bserial_(port|device|path)\b", re.IGNORECASE),
    re.compile(r"\buart_(port|device|path)\b", re.IGNORECASE),
    re.compile(r"\bbaud(rate)?\b\s*[:=]\s*\d+", re.IGNORECASE),
    re.compile(r"\braw_(path|packet|feedback)\b", re.IGNORECASE),
    re.compile(r"\b(checksum|traceback)\b", re.IGNORECASE),
    re.compile(r"\b(password|passwd|secret|token|credential|authorization)\b", re.IGNORECASE),
    re.compile(r"/cmd_vel\b"),
    re.compile(r'"delivery_success"\s*:\s*true', re.IGNORECASE),
    re.compile(r"\bdelivery_success\s*=\s*true\b", re.IGNORECASE),
    re.compile(r'"primary_actions_enabled"\s*:\s*true', re.IGNORECASE),
    re.compile(r"\bprimary_actions_enabled\s*=\s*true\b", re.IGNORECASE),
    re.compile(r'"safe_to_control"\s*:\s*true', re.IGNORECASE),
    re.compile(r"\bsafe_to_control\s*=\s*true\b", re.IGNORECASE),
    re.compile(r"\bhil_pass\s*[:=]\s*(true|pass|passed|success|ok)\b", re.IGNORECASE),
    re.compile(r"\b(hil_passed|hil pass(ed)?|hil success)\b", re.IGNORECASE),
)


def _utc_now() -> str:
    # UTC 只用于 artifact 排序，不代表真实上车采集时间。
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺 execution pack 是 blocked 输入，不把异常栈或本机路径写入输出。
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


def _list(value: Any) -> list[Any]:
    # 上游字段缺失时按空列表处理，让 contract 检查统一 fail-closed。
    return list(value) if isinstance(value, (list, tuple)) else []


def _text(value: Any, default: str = "") -> str:
    # 输出可见字段统一收窄成短字符串，避免对象 repr 泄漏。
    if value is None:
        return default
    text = value.strip() if isinstance(value, str) else str(value).strip()
    return text or default


def _safe_ref(value: str) -> bool:
    # evidence_ref 是唯一允许跨系统传播的关联键。
    return bool(value and SAFE_EVIDENCE_REF.match(value))


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 兼容 artifact、summary、Robot diagnostics wrapper 和 mobile wrapper。
    candidates = [payload]
    for key in (
        "wave_rover_hil_packet_execution_pack",
        "wave_rover_hil_packet_execution_pack_summary",
        "execution_pack",
        "execution_pack_summary",
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


def _effective_execution_pack(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 schema 命中的 execution pack，避免误消费 intake/review 输入。
    for candidate in _source_candidates(payload):
        schema = _text(candidate.get("schema"))
        summary_schema = _text(candidate.get("summary_schema"))
        if schema in {EXECUTION_PACK_SCHEMA, EXECUTION_PACK_SUMMARY_SCHEMA}:
            return candidate
        if summary_schema == EXECUTION_PACK_SUMMARY_SCHEMA:
            return candidate
    return payload


def _scan_unsafe_input(payload: dict[str, Any]) -> list[str]:
    # 扫描完整输入，拦截嵌套 note 中的设备、路径、成功和控制授权文案。
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return [f"unsafe_input:{pattern.pattern}" for pattern in UNSAFE_INPUT_PATTERNS if pattern.search(encoded)]


def _schema_status(payload: dict[str, Any], execution_pack: dict[str, Any]) -> str:
    # 只接受上一轮 execution-pack gate，避免跳过审查链路。
    schema = _text(execution_pack.get("schema") or payload.get("schema"))
    summary_schema = _text(execution_pack.get("summary_schema") or payload.get("summary_schema"))
    boundary = _text(execution_pack.get("evidence_boundary") or payload.get("evidence_boundary"))
    source = _text(execution_pack.get("source") or payload.get("source"))
    if schema and schema not in {EXECUTION_PACK_SCHEMA, EXECUTION_PACK_SUMMARY_SCHEMA}:
        return "unsupported_schema"
    if not schema and summary_schema != EXECUTION_PACK_SUMMARY_SCHEMA:
        return "unsupported_schema"
    if boundary != EXECUTION_PACK_BOUNDARY:
        return "unsupported_boundary"
    if source != SOURCE:
        return "unsupported_source"
    return "supported"


def _flag_status(execution_pack: dict[str, Any]) -> list[str]:
    # 输出 gate 必须继承 false 控制位；safe_to_control 缺失按旧 pack 兼容，true 必拦截。
    issues: list[str] = []
    if execution_pack.get("delivery_success") is not False:
        issues.append("delivery_success_not_false")
    if execution_pack.get("primary_actions_enabled") is not False:
        issues.append("primary_actions_enabled_not_false")
    if execution_pack.get("safe_to_control") is True:
        issues.append("safe_to_control_true")
    if execution_pack.get("same_evidence_ref_required") is not True:
        issues.append("same_evidence_ref_required_not_true")
    not_proven = {str(item) for item in _list(execution_pack.get("not_proven"))}
    required_not_proven = {"real_wave_rover", "real_uart", "hil_pass", "real_odom", "real_imu", "real_battery", "delivery_success"}
    missing_not_proven = sorted(required_not_proven - not_proven)
    if missing_not_proven:
        issues.append("not_proven_missing:" + ",".join(missing_not_proven))
    return issues


def _evidence_ref_status(execution_pack: dict[str, Any], expected_ref: str) -> tuple[str, list[str]]:
    # CLI 指定 ref 时必须与 execution pack 完全一致。
    observed = _text(execution_pack.get("evidence_ref"))
    issues: list[str] = []
    if not _safe_ref(observed):
        issues.append("execution_pack_evidence_ref_missing_or_unsafe")
    if expected_ref and not _safe_ref(expected_ref):
        issues.append("requested_evidence_ref_unsafe")
    if expected_ref and observed and expected_ref != observed:
        issues.append("requested_evidence_ref_mismatch")
    return observed if _safe_ref(observed) else "", issues


def _material_file_names(execution_pack: dict[str, Any]) -> set[str]:
    # artifact 使用 dict 模板，summary 可能只给文件名；两种都只提取白名单文件名。
    names: set[str] = set()
    for item in _list(execution_pack.get("required_material_templates")):
        if isinstance(item, dict):
            names.add(_text(item.get("file") or item.get("name")))
        else:
            names.add(_text(item))
    return {name for name in names if name}


def _execution_pack_status(execution_pack: dict[str, Any]) -> str:
    # 不同上游 view 字段名不同，这里统一读取可验证状态。
    return _text(
        execution_pack.get("execution_pack_status")
        or execution_pack.get("wave_rover_hil_packet_execution_pack")
        or execution_pack.get("status")
    )


def _execution_material_issues(execution_pack: dict[str, Any]) -> list[str]:
    # drill 的材料包必须覆盖真实采集所需五件套。
    names = _material_file_names(execution_pack)
    missing = [name for name in REQUIRED_MATERIAL_FILES if name not in names]
    if missing:
        return ["required_material_template_missing:" + ",".join(missing)]
    return []


def _collection_drill_status(load_issue: str, schema_status: str, execution_pack: dict[str, Any], issues: list[str]) -> str:
    # ready 状态只表示 drill 可执行，不代表任何真实硬件结果。
    if load_issue:
        return "blocked_missing_wave_rover_hil_packet_execution_pack"
    if schema_status != "supported":
        return "blocked_unsupported_wave_rover_hil_packet_execution_pack"
    if any(issue.startswith("unsafe_input") for issue in issues):
        return "blocked_unsafe_wave_rover_hil_packet_collection_drill_claim"
    if "requested_evidence_ref_mismatch" in issues or "execution_pack_evidence_ref_missing_or_unsafe" in issues:
        return "blocked_wave_rover_hil_packet_collection_drill_evidence_ref_mismatch"
    if _execution_pack_status(execution_pack) != "ready_for_real_hil_collection_not_proven":
        return "blocked_execution_pack_not_ready"
    if issues:
        return "blocked_wave_rover_hil_packet_collection_drill_contract"
    return "ready_for_real_hil_collection_drill_not_proven"


def _required_material_templates(evidence_ref: str) -> list[dict[str, str]]:
    # 模板是现场采集 checklist，不生成或伪造任何真实 packet。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        {
            "file": "feedback_T1001.log",
            "vendor_basis": "json_cmd.h FEEDBACK_BASE_INFO 1001; base_ctrl.py newline JSON read",
            "required_fields": "evidence_ref,timestamp,raw_line,T=1001",
            "drill_action": f"collect real base feedback line under evidence_ref={ref}",
        },
        {
            "file": "odom_once.jsonl",
            "vendor_basis": "project runtime odom sample after WAVE ROVER packet run",
            "required_fields": "evidence_ref,stamp,frame_id,child_frame_id,pose,twist",
            "drill_action": f"capture one real odom sample under evidence_ref={ref}",
        },
        {
            "file": "imu_once.jsonl",
            "vendor_basis": "json_cmd.h IMU command family and project runtime IMU topic",
            "required_fields": "evidence_ref,stamp,orientation_or_status,angular_velocity_or_status",
            "drill_action": f"capture one real IMU sample under evidence_ref={ref}",
        },
        {
            "file": "battery_once.jsonl",
            "vendor_basis": "config.yaml fb.base_voltage and WAVE ROVER feedback contract",
            "required_fields": "evidence_ref,stamp,voltage_or_percentage,source",
            "drill_action": f"capture one real battery sample under evidence_ref={ref}",
        },
        {
            "file": "operator_hil_report",
            "vendor_basis": "VENDOR_INDEX.md requires local vendor source and real hardware evidence separation",
            "required_fields": "evidence_ref,operator,host,hardware_seen,observed_result,open_risks",
            "drill_action": "write the operator report after collection; keep this gate not_proven",
        },
    ]


def _preflight_checklist(evidence_ref: str) -> list[str]:
    # preflight 只列收集前的人工核对，不暴露设备路径、波特率或命令细节。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"lock safe evidence_ref={ref} before collecting any material",
        "read docs/vendor/VENDOR_INDEX.md and listed WAVE ROVER vendor files on the hardware host",
        "confirm the hardware host can collect the five required materials without writing device details into this artifact",
        "keep delivery_success=false, primary_actions_enabled=false, and safe_to_control=false during the drill",
        "rerun intake, review-decision, execution-pack, then this collection-drill gate after packet files are staged",
    ]


def _collection_sequence(evidence_ref: str) -> list[str]:
    # 顺序先锁证据引用再采集五件套，避免事后拼接材料。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"start drill with evidence_ref={ref} and no control action enabled",
        "collect feedback_T1001.log from real base feedback using the same evidence_ref",
        "capture odom_once.jsonl using the same evidence_ref",
        "capture imu_once.jsonl using the same evidence_ref",
        "capture battery_once.jsonl using the same evidence_ref",
        "write operator_hil_report using the same evidence_ref",
        "rerun packet intake and review gates before making any HIL claim",
    ]


def _backfill_commands(evidence_ref: str) -> list[str]:
    # commands 只用于文件 gate backfill，不包含硬件控制命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/wave_rover_hil_packet_intake.py --packet-dir <real_packet_dir> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/wave_rover_hil_packet_review_decision.py --intake-summary <summary.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/wave_rover_hil_packet_execution_pack.py --review-summary <summary.json> --evidence-ref {ref} --once-json",
        f"python3 pc-tools/evidence/wave_rover_hil_packet_collection_drill.py --execution-pack <summary.json> --evidence-ref {ref} --once-json",
    ]


def _owner_handoff() -> dict[str, str]:
    # handoff 明确谁补真实材料，同时保持 Robot/mobile 不获得控制授权。
    return {
        "hardware-engineer": "collect the five real packet materials under one safe evidence_ref on the WAVE ROVER host",
        "robot-software-engineer": "consume only sanitized collection-drill summary until real packet review changes state",
        "full-stack-software-engineer": "render read-only drill status and keep primary actions disabled",
    }


def _summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # summary 是下游白名单视图，不能包含 raw artifact 或敏感输入。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": "not_proven",
        "status": artifact["collection_drill_status"],
        "collection_drill_status": artifact["collection_drill_status"],
        "wave_rover_hil_packet_collection_drill": artifact["collection_drill_status"],
        "evidence_ref": artifact["evidence_ref"],
        "same_evidence_ref_required": True,
        "required_material_templates": [item["file"] for item in artifact["required_material_templates"]],
        "preflight_checklist": artifact["preflight_checklist"],
        "collection_sequence": artifact["collection_sequence"],
        "backfill_commands": artifact["backfill_commands"],
        "owner_handoff": artifact["owner_handoff"],
        "blocked_reasons": artifact["blocked_reasons"],
        "vendor_sources": list(VENDOR_SOURCES),
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "boundary_note": "software_proof only; not_proven; delivery_success=false; primary_actions_enabled=false; safe_to_control=false",
    }


def build_collection_drill(
    execution_pack: str | Path | None = None,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 execution pack artifact/summary，生成 collection drill artifact。"""

    path = Path(execution_pack) if execution_pack else None
    payload, load_issue = _read_json(path)
    pack = _effective_execution_pack(payload)
    schema_status = "missing" if load_issue else _schema_status(payload, pack)
    observed_ref, ref_issues = _evidence_ref_status(pack, evidence_ref.strip()) if not load_issue else ("", ["execution_pack_evidence_ref_missing_or_unsafe"])
    issues = sorted(
        set(
            ([] if not load_issue else [f"execution_pack:{load_issue}"])
            + ([] if schema_status in {"supported", "missing"} else [schema_status])
            + _scan_unsafe_input(payload)
            + _flag_status(pack)
            + ref_issues
            + _execution_material_issues(pack)
        )
    )
    status = _collection_drill_status(load_issue, schema_status, pack, issues)

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "summary_schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": "not_proven",
        "collection_drill_status": status,
        "wave_rover_hil_packet_collection_drill": status,
        "source_execution_pack_schema": _text(pack.get("schema") or payload.get("schema"), "missing"),
        "source_execution_pack_summary_schema": _text(pack.get("summary_schema") or payload.get("summary_schema"), "missing"),
        "source_execution_pack_boundary": _text(pack.get("evidence_boundary") or payload.get("evidence_boundary"), "missing"),
        "source_execution_pack_status": _execution_pack_status(pack) or "missing",
        "schema_status": schema_status,
        "same_evidence_ref_required": True,
        "evidence_ref": observed_ref,
        "required_material_templates": _required_material_templates(observed_ref),
        "preflight_checklist": _preflight_checklist(observed_ref),
        "collection_sequence": _collection_sequence(observed_ref),
        "backfill_commands": _backfill_commands(observed_ref),
        "owner_handoff": _owner_handoff(),
        "blocked_reasons": issues,
        "vendor_sources": list(VENDOR_SOURCES),
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "non_access_scope": [
            "dev_device_probe",
            "ros_graph",
            "cmd_vel",
            "hardware_bus",
            "hil_runtime",
            "delivery_execution",
            "pr5_review_resolution",
        ],
        "boundary_note": "software_proof only; not_proven; delivery_success=false; primary_actions_enabled=false; safe_to_control=false",
    }
    summary = _summary(artifact)
    artifact["collection_drill_summary"] = summary
    exit_code = 0 if status == "ready_for_real_hil_collection_drill_not_proven" else 2
    return artifact, summary, exit_code


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出路径只作为写入目标，不进入 artifact，避免本机路径泄漏。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI dependency-free，可在 Docker 和真实硬件主机上做同一份文件 gate。
    parser = argparse.ArgumentParser(
        description="Generate WAVE ROVER HIL packet collection-drill software-proof artifact."
    )
    parser.add_argument("--execution-pack", default="", help="Previous wave_rover_hil_packet_execution_pack artifact or summary JSON.")
    parser.add_argument("--evidence-ref", default="", help="Optional expected safe evidence_ref shared with the execution pack.")
    parser.add_argument("--output", default="", help="Write full collection-drill artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact collection-drill summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_collection_drill(args.execution_pack or None, args.evidence_ref)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("wave_rover_hil_packet_collection_drill: artifact_file:" + (Path(args.output).name if args.output else ""))
        print(f"collection_drill_status: {artifact['collection_drill_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
