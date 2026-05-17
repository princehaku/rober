#!/usr/bin/env python3
"""生成 route/task field retest result acceptance packet artifact。

该 gate 只读取上一轮 route_task_field_retest_result_reconciliation 的 artifact、
summary 或 wrapper/nested JSON，把复账结果整理成现场验收包。它不读取 raw
handoff artifact，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、
真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_result_intake as intake
import route_task_field_retest_result_reconciliation as reconciliation


# acceptance packet 是 result reconciliation 之后的 PC 侧验收包契约。
PACKET_SCHEMA = "trashbot.route_task_field_retest_result_acceptance_packet.v1"
PACKET_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_result_acceptance_packet_summary.v1"
SCHEMA_VERSION = 1
PACKET_BOUNDARY = "software_proof_docker_route_task_field_retest_result_acceptance_packet_gate"

# 只允许 reconciliation 产物作为输入，避免跳过复账直接生成验收包。
SOURCE_SCHEMAS = {reconciliation.RECONCILIATION_SCHEMA, reconciliation.RECONCILIATION_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {reconciliation.RECONCILIATION_BOUNDARY, ""}
READY_RECONCILIATION_STATUS = "ready_for_field_retest_result_reconciliation_not_proven"

# rg 围栏和人工复盘都依赖这些 literal 明确边界。
BOUNDARY_NOTE = (
    "software_proof_docker_route_task_field_retest_result_acceptance_packet_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false; "
    "pass/fail criteria; rerun commands"
)

# 八类材料沿用 reconciliation 的 fixed list，不允许输入裁剪。
REQUIRED_RESULT_MATERIALS = reconciliation.REQUIRED_RESULT_MATERIALS
NOT_PROVEN = reconciliation.NOT_PROVEN


def _utc_now() -> str:
    # UTC 时间便于 Docker/local 主机之间按时间线复盘 artifact。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入异常统一转为 blocked packet，避免验收包悄悄缺席。
    if not path:
        return {}, "reconciliation_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "reconciliation_json_missing"
    except json.JSONDecodeError:
        return {}, "reconciliation_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "reconciliation_json_read_error"
    if not isinstance(payload, dict):
        return {}, "reconciliation_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # wrapper 字段必须是 object，字符串形式的 JSON 不能被当作可信输入。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 diagnostics 的字段位置可能不同。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # acceptance packet 只需要短清单，限长避免复制完整上游材料。
    if isinstance(value, list):
        return [intake._safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [intake._safe_text(value)]


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免把 raw handoff 或任意 payload 当成 reconciliation。
    candidates = [payload]
    for key in (
        "route_task_field_retest_result_acceptance_packet",
        "route_task_field_retest_result_acceptance_packet_summary",
        "route_task_field_retest_result_reconciliation",
        "route_task_field_retest_result_reconciliation_summary",
        "result_reconciliation",
        "result_reconciliation_summary",
        "reconciliation",
        "reconciliation_summary",
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
    # 优先消费 schema 命中的嵌套对象；未命中时保留顶层用于 unsupported 解释。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, Any]:
    # schema 与 boundary 必须同时受支持，防止跨 gate 结果误入验收包。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = intake._safe_text(source.get("schema", ""))
    boundary = intake._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 是 acceptance packet 串联现场材料的唯一主键。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    phone_safe = _dict(source, "fail_closed_phone_safe_summary")
    return intake._safe_ref(
        _first_text(
            source.get("evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("evidence_ref"),
            safe_copy.get("evidence_ref"),
            phone_safe.get("evidence_ref"),
            default="",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 弱类型字符串不能通过；必须保持 JSON boolean true。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return source.get(
        "same_evidence_ref_required",
        robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True))),
    )


def _source_reconciliation_status(source: dict[str, Any]) -> str:
    # 上游 reconciliation 只有 ready_not_proven 才能转成 ready packet。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "fail_closed_phone_safe_summary") or _dict(source, "safe_copy")
    return intake._safe_text(
        _first_text(
            source.get("reconciliation_verdict"),
            source.get("status"),
            robot.get("reconciliation_verdict"),
            robot.get("status"),
            mobile.get("reconciliation_verdict"),
            mobile.get("status"),
            safe_copy.get("reconciliation_verdict"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _safe_lineage(source: dict[str, Any]) -> dict[str, str]:
    # lineage 只取 reconciliation 已经白名单化的四个字段，不追 raw handoff。
    lineage: dict[str, str] = {}
    for key in (
        "source_result_intake_schema",
        "source_result_intake_status",
        "source_review_result_handoff_schema",
        "source_review_result_handoff_status",
    ):
        value = intake._safe_text(source.get(key, ""))
        if value:
            lineage[key] = value
    return lineage


def _material_statuses(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    # 只汇总材料摘要状态，不打开真实日志、task record 或现场文件。
    raw_materials = source.get("result_materials")
    if not isinstance(raw_materials, dict):
        raw_materials = {}
    materials: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_RESULT_MATERIALS:
        raw = raw_materials.get(name)
        raw = raw if isinstance(raw, dict) else {}
        materials[name] = {
            "status": intake._safe_text(raw.get("status", "missing")) or "missing",
            "evidence_ref": intake._safe_ref(raw.get("evidence_ref", "")),
            "placeholder": bool(raw.get("placeholder", False)),
        }
    return materials


def _missing_materials(source: dict[str, Any], materials: dict[str, dict[str, Any]]) -> list[str]:
    # reconciliation 的 missing_materials 是主来源；缺字段时按 material status 补算。
    missing = []
    for item in _safe_list(source.get("missing_materials"), limit=len(REQUIRED_RESULT_MATERIALS)):
        if item in REQUIRED_RESULT_MATERIALS and item not in missing:
            missing.append(item)
    for name, material in materials.items():
        if (not material["status"] or material["status"] == "missing" or material["placeholder"]) and name not in missing:
            missing.append(name)
    return missing


def _mismatch_reasons(source: dict[str, Any], missing: list[str]) -> list[str]:
    # mismatch reasons 只复制上游短原因并补足缺材料提示，不复制材料正文。
    reasons = _safe_list(source.get("mismatch_reasons"), limit=12)
    if missing and not any(reason.startswith("missing result materials:") for reason in reasons):
        reasons.append("missing result materials: " + ", ".join(missing))
    return reasons


def _same_ref_status(source: dict[str, Any], evidence_ref: str, missing: list[str], same_ref_required: Any) -> dict[str, Any]:
    # 如果上游已有同证据号摘要，保留其安全字段；否则生成 blocked 摘要。
    raw = source.get("same_evidence_ref_status")
    raw = raw if isinstance(raw, dict) else {}
    mismatched = _safe_list(raw.get("mismatched_materials"), limit=len(REQUIRED_RESULT_MATERIALS))
    return {
        "required": True,
        "input_required_value": same_ref_required,
        "evidence_ref": evidence_ref,
        "status": "aligned" if evidence_ref and same_ref_required is True and not missing and not mismatched else "blocked",
        "missing_materials": missing,
        "mismatched_materials": [item for item in mismatched if item in REQUIRED_RESULT_MATERIALS],
    }


def _status(
    load_issue: str,
    source_status: dict[str, Any],
    source_reconciliation_status: str,
    evidence_ref: str,
    same_ref_required: Any,
    same_ref_status: dict[str, Any],
    missing: list[str],
    unsafe_copy: bool,
    success_or_control_claim: bool,
) -> str:
    # fail closed 顺序固定，危险输入优先于普通缺材料。
    if load_issue in {"reconciliation_json_bad_json", "reconciliation_json_read_error", "reconciliation_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_route_task_field_retest_result_reconciliation"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_schema"
    if not evidence_ref:
        return "blocked_missing_evidence_ref"
    if same_ref_required is not True:
        return "blocked_same_evidence_ref_not_required"
    if unsafe_copy:
        return "blocked_unsafe_material_copy"
    if success_or_control_claim:
        return "blocked_success_or_control_claim"
    if same_ref_status["mismatched_materials"]:
        return "blocked_same_evidence_ref_mismatch"
    if source_reconciliation_status != READY_RECONCILIATION_STATUS:
        return "blocked_reconciliation_not_ready"
    if missing:
        return "blocked_missing_result_materials"
    return "ready_for_field_retest_result_acceptance_packet_not_proven"


def _acceptance_gap_summary(missing: list[str], mismatch_reasons: list[str]) -> dict[str, Any]:
    # gap summary 是支持侧优先看的修复入口，不证明现场结果。
    return {
        "missing_materials": missing,
        "mismatch_reasons": mismatch_reasons,
        "gap_count": len(missing) + len(mismatch_reasons),
        "gap_policy": "fail_closed_until_all_required_result_materials_are_reconciled",
    }


def _owner_handoff(status: str, evidence_ref: str, missing: list[str]) -> dict[str, Any]:
    # owner handoff 把下一步责任写清楚，但不指示任何机器人动作。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "primary_owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "handoff_status": status,
        "evidence_ref": ref,
        "next_action": (
            "review packet with Robot/mobile read-only consumers"
            if status == "ready_for_field_retest_result_acceptance_packet_not_proven"
            else "repair reconciliation input before acceptance packet review"
        ),
        "missing_owner_focus": missing,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/route_task_field_retest_result_reconciliation.py --result-json <result_intake_or_wrapper.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py --reconciliation-json <reconciliation.json> --evidence-ref {ref}",
        "keep delivery_success=false and primary_actions_enabled=false until real field review closes",
    ]


def _pass_fail_criteria(evidence_ref: str) -> dict[str, list[str]]:
    # pass/fail criteria 是下一次现场复测验收口径，不是本轮通过结论。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "pass": [
            f"all eight required result materials use evidence_ref={ref}",
            "reconciliation status is ready_for_field_retest_result_reconciliation_not_proven",
            "missing_materials and mismatch_reasons are empty",
            "delivery_success remains false and primary_actions_enabled remains false in this packet",
        ],
        "fail": [
            "any required result material is missing, placeholder, or uses another evidence_ref",
            "input schema or evidence_boundary is unsupported",
            "unsafe copy, raw path, credential, ROS topic, hardware transport detail, or success/control claim appears",
            "real Nav2/fixed-route, elevator, dropoff/cancel, phone/browser, HIL, or cloud proof is absent",
        ],
    }


def _safe_copy(
    status: str,
    evidence_ref: str,
    lineage: dict[str, str],
    missing: list[str],
    mismatch_reasons: list[str],
    owner_handoff: dict[str, Any],
    rerun_commands: list[str],
    pass_fail_criteria: dict[str, list[str]],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或本机路径。
    return {
        "schema": f"{PACKET_SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "acceptance_packet_status": status,
        "evidence_boundary": PACKET_BOUNDARY,
        "evidence_ref": evidence_ref,
        "safe_lineage": lineage,
        "required_result_materials": list(REQUIRED_RESULT_MATERIALS),
        "missing_materials": missing,
        "mismatch_reasons": mismatch_reasons,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "pass_fail_criteria": pass_fail_criteria,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    lineage: dict[str, str],
    materials: dict[str, dict[str, Any]],
    missing: list[str],
    mismatch_reasons: list[str],
    same_ref_status: dict[str, Any],
    gap_summary: dict[str, Any],
    owner_handoff: dict[str, Any],
    rerun_commands: list[str],
    pass_fail_criteria: dict[str, list[str]],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 Robot/Full-stack 只读对接面，字段稳定且默认 fail-closed。
    return {
        "schema": PACKET_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": PACKET_BOUNDARY,
        "boundary": PACKET_BOUNDARY,
        "status": status,
        "acceptance_packet_status": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "safe_lineage": lineage,
        "required_result_materials": list(REQUIRED_RESULT_MATERIALS),
        "result_material_statuses": materials,
        "missing_materials": missing,
        "mismatch_reasons": mismatch_reasons,
        "acceptance_gap_summary": gap_summary,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "pass_fail_criteria": pass_fail_criteria,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_result_acceptance_packet(
    reconciliation_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 reconciliation JSON，生成 fail-closed result acceptance packet。"""
    payload, load_issue = _load_json(reconciliation_json)
    source = _find_source(payload) if payload else {}
    requested_ref = intake._safe_ref(evidence_ref) or _source_evidence_ref(source)
    source_ref = _source_evidence_ref(source)
    same_ref_required = _same_ref_required(source) if source else True
    if evidence_ref and source_ref and requested_ref != source_ref:
        # CLI 指定证据号与输入不一致时，按同证据号硬约束失败。
        same_ref_required = False

    source_status = _source_status(load_issue, source)
    materials = _material_statuses(source) if source else {name: {"status": "missing", "evidence_ref": "", "placeholder": False} for name in REQUIRED_RESULT_MATERIALS}
    missing = _missing_materials(source, materials) if source else list(REQUIRED_RESULT_MATERIALS)
    mismatch_reasons = _mismatch_reasons(source, missing) if source else ["missing result reconciliation input"]
    same_ref_status = _same_ref_status(source, requested_ref, missing, same_ref_required)
    unsafe_copy = bool(payload) and (intake._has_forbidden_copy(source) or intake._has_raw_path_copy(source))
    success_or_control_claim = bool(payload) and intake._has_success_or_control_claim(source)
    source_reconciliation_status = _source_reconciliation_status(source) if source else "missing"
    status = _status(
        load_issue,
        source_status,
        source_reconciliation_status,
        requested_ref,
        same_ref_required,
        same_ref_status,
        missing,
        unsafe_copy,
        success_or_control_claim,
    )

    lineage = _safe_lineage(source)
    gap_summary = _acceptance_gap_summary(missing, mismatch_reasons)
    owner_handoff = _owner_handoff(status, requested_ref, missing)
    rerun_commands = _rerun_commands(requested_ref)
    pass_fail_criteria = _pass_fail_criteria(requested_ref)
    safe_copy = _safe_copy(status, requested_ref, lineage, missing, mismatch_reasons, owner_handoff, rerun_commands, pass_fail_criteria)
    summary = _summary_payload(
        status,
        requested_ref,
        lineage,
        materials,
        missing,
        mismatch_reasons,
        same_ref_status,
        gap_summary,
        owner_handoff,
        rerun_commands,
        pass_fail_criteria,
        safe_copy,
    )

    artifact = {
        "schema": PACKET_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": PACKET_BOUNDARY,
        "boundary": PACKET_BOUNDARY,
        "status": status,
        "acceptance_packet_status": status,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_reconciliation": {
            **source_status,
            "schema": intake._safe_text(source.get("schema", "")),
            "evidence_boundary": intake._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
            "status": source_reconciliation_status,
            "evidence_ref": source_ref,
            "same_evidence_ref_required": same_ref_required,
            "unsafe_copy": bool(unsafe_copy),
            "success_or_control_claim": bool(success_or_control_claim),
        },
        "safe_lineage": lineage,
        "required_result_materials": list(REQUIRED_RESULT_MATERIALS),
        "result_material_statuses": materials,
        "missing_materials": missing,
        "mismatch_reasons": mismatch_reasons,
        "acceptance_gap_summary": gap_summary,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "pass_fail_criteria": pass_fail_criteria,
        "safe_copy": safe_copy,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "raw_handoff_artifact",
            "ros_graph",
            "nav2_runtime",
            "fixed_route_runtime",
            "hardware_transport",
            "hardware_feedback",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "real_phone_or_browser",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = intake._safe_value(artifact)
    summary = intake._safe_value(summary)
    if intake._has_forbidden_copy(artifact) or intake._has_forbidden_copy(summary):
        # 最终防线：输出仍含禁词时强制降级，且不改变 fail-closed flags。
        artifact["status"] = "blocked_unsafe_material_copy"
        artifact["acceptance_packet_status"] = "blocked_unsafe_material_copy"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_material_copy"
        artifact["robot_diagnostics_summary"]["acceptance_packet_status"] = "blocked_unsafe_material_copy"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_material_copy"
        artifact["mobile_readonly_summary"]["acceptance_packet_status"] = "blocked_unsafe_material_copy"
        summary["status"] = "blocked_unsafe_material_copy"
        summary["acceptance_packet_status"] = "blocked_unsafe_material_copy"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；未指定时由 CLI 打印到 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，方便 PC、Docker 和 focused unittest 共用。
    parser = argparse.ArgumentParser(description="Generate a route/task field retest result acceptance packet artifact")
    parser.add_argument("--reconciliation-json", required=True, help="result reconciliation artifact, summary, or wrapper JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this acceptance packet")
    parser.add_argument("--output", default="", help="optional acceptance packet artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional acceptance packet summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print acceptance packet artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_result_acceptance_packet(
        args.reconciliation_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field retest result acceptance packet: packet_file:{intake._safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_packet_summary_file: {intake._safe_ref(args.summary_output)}")
        print(f"acceptance_packet_status: {artifact['acceptance_packet_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
