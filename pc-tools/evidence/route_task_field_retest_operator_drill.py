#!/usr/bin/env python3
"""生成 route/task field retest operator drill artifact。

该 gate 只读取上一轮 material pack artifact / summary / wrapper JSON，把
material pack -> result intake -> result reconciliation 的 PC 操作顺序整理成
operator drill artifact 与 summary。它不访问 ROS graph、Nav2 runtime、硬件、
外部云、真实手机/browser 或真实现场文件内容。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_material_pack as pack


# operator drill 是 material pack 之后的 PC 侧演练契约。
DRILL_SCHEMA = "trashbot.route_task_field_retest_operator_drill.v1"
DRILL_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_operator_drill_summary.v1"
SCHEMA_VERSION = 1
DRILL_BOUNDARY = "software_proof_docker_route_task_field_retest_operator_drill_gate"

# 只允许 material pack 产物作为输入，避免其它 gate 的状态被误解为 drill。
SOURCE_SCHEMAS = {pack.PACK_SCHEMA, pack.PACK_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {pack.PACK_BOUNDARY, ""}

# rg 验收会检查这些 literal；也给人工复盘一个短边界。
BOUNDARY_NOTE = (
    "software_proof_docker_route_task_field_retest_operator_drill_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# operator drill 仍然只证明命令链可复账，不证明任何现场能力已经通过。
NOT_PROVEN = (
    "real_nav2_fixed_route_runtime",
    "real_route_completion_pass",
    "real_task_record_runtime",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_note",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result_reviewed_success",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 成功或动作放行文案一律阻断，防止 drill 被误当作现场 pass。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bresult\s+reconciliation\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
)


def _utc_now() -> str:
    # UTC 时间让 Docker-only artifact 能跨机器按生成顺序审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # wrapper 可能给字符串或数组；输出限长，避免复制完整上游材料。
    if isinstance(value, list):
        return [pack._safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [pack._safe_text(value)]


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 所有读失败都转成 blocked artifact，避免 operator drill 没有留痕。
    if not path:
        return {}, "material_pack_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "material_pack_json_missing"
    except json.JSONDecodeError:
        return {}, "material_pack_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "material_pack_json_read_error"
    if not isinstance(payload, dict):
        return {}, "material_pack_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段，字符串 wrapper 不能伪装可信 JSON。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # 兼容 artifact、summary、safe_copy、wrapper 的字段名差异。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免把 raw artifact 或任意 payload 当成 material pack。
    candidates = [payload]
    for key in (
        "route_task_field_retest_material_pack",
        "route_task_field_retest_material_pack_summary",
        "material_pack",
        "material_pack_summary",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 schema 命中的嵌套对象；没有命中时保留顶层解释 unsupported。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, Any]:
    # schema 与 boundary 必须同时受支持，防止跨 gate 材料误入 drill。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = pack._safe_text(source.get("schema", ""))
    boundary = pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # same evidence_ref 是 material pack、intake、reconciliation 串联主键。
    safe_copy = _dict(source, "safe_copy")
    material_summary = _dict(source, "material_pack_summary")
    return pack._safe_ref(
        _first_text(
            source.get("evidence_ref"),
            safe_copy.get("evidence_ref"),
            material_summary.get("evidence_ref"),
            default="",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 弱类型字符串必须 fail closed；这里要求 JSON boolean true。
    safe_copy = _dict(source, "safe_copy")
    material_summary = _dict(source, "material_pack_summary")
    return source.get(
        "same_evidence_ref_required",
        material_summary.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
    )


def _missing_materials(source: dict[str, Any]) -> list[str]:
    # material pack 可能在 summary 或 completeness 中表达缺失项，统一取白名单。
    completeness = _dict(source, "material_completeness")
    material_summary = _dict(source, "material_pack_summary")
    summary_completeness = _dict(material_summary, "material_completeness")
    raw = source.get("missing_materials") or completeness.get("missing_materials") or material_summary.get("missing_materials")
    if raw in (None, ""):
        raw = summary_completeness.get("missing_materials")
    names = []
    for item in _safe_list(raw, limit=len(pack.REQUIRED_MATERIALS)):
        name = pack._safe_text(item).strip()
        if name in pack.REQUIRED_MATERIALS and name not in names:
            names.append(name)
    return names


def _material_count(source: dict[str, Any], missing: list[str]) -> dict[str, Any]:
    # completeness 只是输入材料状态，不代表现场复测成功。
    completeness = _dict(source, "material_completeness")
    material_summary = _dict(source, "material_pack_summary")
    summary_completeness = _dict(material_summary, "material_completeness")
    accepted = completeness.get("accepted_count", summary_completeness.get("accepted_count"))
    try:
        accepted_count = int(accepted)
    except (TypeError, ValueError):
        accepted_count = len(pack.REQUIRED_MATERIALS) - len(missing)
    return {
        "required_count": len(pack.REQUIRED_MATERIALS),
        "accepted_count": max(0, min(len(pack.REQUIRED_MATERIALS), accepted_count)),
        "missing_count": len(missing),
        "is_complete": len(missing) == 0 and accepted_count == len(pack.REQUIRED_MATERIALS),
    }


def _has_success_or_control_claim(value: Any) -> bool:
    # 顶层布尔字段和自由文本都检查，避免 wrapper 越界放行动作。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = pack._encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _unsafe_copy(value: Any) -> bool:
    # 复用 material pack 的禁词和路径检测，额外阻断 drill 自己的成功文案。
    return pack._has_forbidden_copy(value) or pack._has_raw_path_copy(value) or _has_success_or_control_claim(value)


def _source_verdict(source: dict[str, Any]) -> str:
    # 上游 material pack 的 verdict 只影响 drill 状态，不被当成真实证明。
    safe_copy = _dict(source, "safe_copy")
    material_summary = _dict(source, "material_pack_summary")
    return pack._safe_text(
        _first_text(
            source.get("material_pack_verdict"),
            source.get("status"),
            material_summary.get("material_pack_verdict"),
            material_summary.get("status"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _drill_status(
    load_issue: str,
    source_status: dict[str, Any],
    evidence_ref: str,
    requested_ref: str,
    same_ref_required: Any,
    unsafe_copy: bool,
) -> str:
    # fail-closed 优先级固定，便于 Robot/mobile 后续稳定消费。
    if load_issue in {"material_pack_json_bad_json", "material_pack_json_read_error", "material_pack_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_material_pack"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_schema"
    if not evidence_ref:
        return "blocked_missing_evidence_ref"
    if requested_ref and evidence_ref != requested_ref:
        return "blocked_same_evidence_ref_mismatch"
    if same_ref_required is not True:
        return "blocked_same_evidence_ref_not_required"
    if unsafe_copy:
        return "blocked_unsafe_material_pack_copy"
    return "ready_for_operator_drill_not_proven"


def _material_pack_command(evidence_ref: str) -> str:
    # 命令用占位符而非真实路径，避免把本机目录写入 phone-safe summary。
    ref = evidence_ref or "<same_evidence_ref>"
    return (
        "python3 pc-tools/evidence/route_task_field_retest_material_pack.py "
        f"--material-dir <material_dir> --evidence-ref {ref} "
        "--output <material_pack.json> --summary-output <material_pack_summary.json>"
    )


def _result_intake_command(evidence_ref: str) -> str:
    # intake 读取 drill 前一环的 material pack summary，不触发 ROS 或硬件动作。
    ref = evidence_ref or "<same_evidence_ref>"
    return (
        "python3 pc-tools/evidence/route_task_field_retest_result_intake.py "
        f"--result-json <material_pack_summary.json> --evidence-ref {ref} "
        "--output <result_intake.json> --summary-output <result_intake_summary.json>"
    )


def _result_reconciliation_command(evidence_ref: str) -> str:
    # reconciliation 必须在 intake 后运行，保持同一 evidence_ref 复账。
    ref = evidence_ref or "<same_evidence_ref>"
    return (
        "python3 pc-tools/evidence/route_task_field_retest_result_reconciliation.py "
        f"--result-json <result_intake.json> --evidence-ref {ref} "
        "--output <result_reconciliation.json> --summary-output <result_reconciliation_summary.json>"
    )


def _required_outputs() -> list[dict[str, str]]:
    # 输出清单只列相对占位文件名，不复制任何真实绝对路径。
    return [
        {"label": "material_pack_artifact", "file": "<material_pack.json>"},
        {"label": "material_pack_summary", "file": "<material_pack_summary.json>"},
        {"label": "result_intake_artifact", "file": "<result_intake.json>"},
        {"label": "result_intake_summary", "file": "<result_intake_summary.json>"},
        {"label": "result_reconciliation_artifact", "file": "<result_reconciliation.json>"},
        {"label": "result_reconciliation_summary", "file": "<result_reconciliation_summary.json>"},
    ]


def _missing_material_prompts(missing: list[str], evidence_ref: str) -> list[str]:
    # prompts 是现场补采清单，不能包含成功判断或硬件细节。
    ref = evidence_ref or "<same_evidence_ref>"
    if not missing:
        return [f"Confirm all eight material summaries keep evidence_ref={ref} before intake."]
    return [f"Collect {name} metadata on evidence_ref={ref} before rerun." for name in missing]


def _operator_callback_checklist(evidence_ref: str) -> list[str]:
    # callback 只要求事实摘要、失败原因和同证据号，不要求 operator 宣称成功。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"Confirm every returned material keeps evidence_ref={ref}.",
        "Record Nav2/fixed-route runtime metadata without copying raw logs.",
        "Record route completion signal and task record terminal branch with failure reason.",
        "Record door state, target floor confirmation, and human assistance note for elevator flow.",
        "Record dropoff or cancel completion branch plus delivery result review input without success wording.",
        "Run result intake first, then result reconciliation; keep diagnostics and mobile read-only.",
    ]


def _rerun_notes(status: str, evidence_ref: str, missing: list[str], source_verdict: str) -> list[str]:
    # rerun notes 把 blocked 原因转成下一步，不放现场通过措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    notes = [f"Keep evidence_ref={ref} unchanged across material pack, result intake, and result reconciliation."]
    if missing:
        notes.append("Repair missing materials before rerun: " + ", ".join(missing))
    if source_verdict and source_verdict != "ready_for_field_retest_material_pack_not_proven":
        notes.append(f"Review source material_pack_verdict={source_verdict} before intake.")
    if status != "ready_for_operator_drill_not_proven":
        notes.append("Rerun operator drill after source schema, boundary, and safe copy are repaired.")
    notes.append("Keep delivery_success=false and primary_actions_enabled=false until real review closes.")
    return [pack._safe_text(note) for note in notes[:6]]


def _safe_copy(status: str, evidence_ref: str, material_count: dict[str, Any], missing: list[str]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不包含 raw artifact 或本机路径。
    return {
        "schema": f"{DRILL_SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "evidence_boundary": DRILL_BOUNDARY,
        "evidence_ref": evidence_ref,
        "material_complete": material_count["is_complete"],
        "missing_materials": missing,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    source_verdict: str,
    material_count: dict[str, Any],
    missing: list[str],
    command_chain: list[dict[str, str]],
    required_outputs: list[dict[str, str]],
    missing_prompts: list[str],
    callback_checklist: list[str],
    rerun_notes: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是下游消费首选字段集，必须稳定且 phone-safe。
    return {
        "schema": DRILL_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": DRILL_BOUNDARY,
        "boundary": DRILL_BOUNDARY,
        "status": status,
        "operator_drill_verdict": status,
        "source_material_pack_verdict": source_verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "material_count": material_count,
        "missing_materials": missing,
        "command_chain": command_chain,
        "required_outputs": required_outputs,
        "missing_material_prompts": missing_prompts,
        "operator_callback_checklist": callback_checklist,
        "rerun_notes": rerun_notes,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def build_route_task_field_retest_operator_drill(
    material_pack_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    # 主构建函数保持 CLI/unittest 共用，便于离线验证同一逻辑。
    payload, load_issue = _load_json(material_pack_json)
    source = _find_source(payload) if payload else {}
    source_status = _source_status(load_issue, source)
    requested_ref = pack._safe_ref(evidence_ref)
    source_ref = _source_evidence_ref(source)
    resolved_ref = requested_ref or source_ref
    same_ref_required = _same_ref_required(source)
    missing = _missing_materials(source)
    material_count = _material_count(source, missing)
    source_verdict = _source_verdict(source)
    unsafe = _unsafe_copy(source)
    status = _drill_status(load_issue, source_status, source_ref, requested_ref, same_ref_required, unsafe)
    command_chain = [
        {"label": "material_pack", "command": _material_pack_command(resolved_ref)},
        {"label": "result_intake", "command": _result_intake_command(resolved_ref)},
        {"label": "result_reconciliation", "command": _result_reconciliation_command(resolved_ref)},
    ]
    outputs = _required_outputs()
    prompts = _missing_material_prompts(missing, resolved_ref)
    checklist = _operator_callback_checklist(resolved_ref)
    rerun_notes = _rerun_notes(status, resolved_ref, missing, source_verdict)
    safe_copy = _safe_copy(status, resolved_ref, material_count, missing)
    summary = _summary_payload(
        status,
        resolved_ref,
        source_verdict,
        material_count,
        missing,
        command_chain,
        outputs,
        prompts,
        checklist,
        rerun_notes,
        safe_copy,
    )
    artifact = {
        "schema": DRILL_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": DRILL_BOUNDARY,
        "boundary": DRILL_BOUNDARY,
        "operator_drill_verdict": status,
        "source_material_pack": {
            "schema": pack._safe_text(source.get("schema", "")),
            "evidence_boundary": pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
            "load_status": source_status["load_status"],
            "schema_status": source_status["schema_status"],
            "material_pack_verdict": source_verdict,
        },
        "same_evidence_ref_required": True,
        "evidence_ref": resolved_ref,
        "material_pack_command": command_chain[0],
        "result_intake_command": command_chain[1],
        "result_reconciliation_command": command_chain[2],
        "required_outputs": outputs,
        "missing_material_prompts": prompts,
        "operator_callback_checklist": checklist,
        "rerun_notes": rerun_notes,
        "operator_drill_summary": summary,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "hardware",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device_or_browser",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "primary_actions_enabled": False,
        "delivery_success": False,
    }
    artifact = pack._safe_value(artifact)
    summary = pack._safe_value(summary)
    if _unsafe_copy(summary):
        # 最终防线：summary 不安全时只保留 blocked 状态和安全边界字段。
        summary["status"] = "blocked_unsafe_operator_drill_summary"
        summary["operator_drill_verdict"] = "blocked_unsafe_operator_drill_summary"
        artifact["operator_drill_verdict"] = "blocked_unsafe_operator_drill_summary"
        artifact["operator_drill_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时创建父目录；不指定时由 --once-json/stdout 展示 artifact。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 不接触运行时系统，只把 material pack JSON 转成 operator drill。
    parser = argparse.ArgumentParser(description="Build route/task field retest operator drill artifact")
    parser.add_argument("--material-pack-json", required=True, help="material pack artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for the drill chain")
    parser.add_argument("--output", default="", help="optional operator drill artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional operator drill summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print operator drill artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_operator_drill(args.material_pack_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_operator_drill: artifact_file:{pack._safe_ref(args.output)}")
        print(f"operator_drill_verdict: {artifact['operator_drill_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
