#!/usr/bin/env python3
"""生成 route/task field retest acceptance brief artifact。

该 gate 只读取上一轮 route_task_field_retest_drill_console 的 artifact、
summary 或 wrapper/nested JSON，把 PC 演练控制台摘要转成现场验收简报。
它不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、
硬件、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_drill_console as console
import route_task_field_retest_material_pack as pack


# acceptance brief 是 drill console 后的 PC 侧验收简报契约。
BRIEF_SCHEMA = "trashbot.route_task_field_retest_acceptance_brief.v1"
BRIEF_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_acceptance_brief_summary.v1"
SCHEMA_VERSION = 1
BRIEF_BOUNDARY = "software_proof_docker_route_task_field_retest_acceptance_brief_gate"

# 只允许 drill console 产物作为输入，防止 operator drill 被跳级解释成验收简报。
SOURCE_SCHEMAS = {console.CONSOLE_SCHEMA, console.CONSOLE_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {console.CONSOLE_BOUNDARY, ""}

# rg 验收需要这些 literal；人工复盘也能直接看到安全边界。
BOUNDARY_NOTE = (
    "software_proof_docker_route_task_field_retest_acceptance_brief_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# acceptance brief 仍然只证明本地简报可复账，不证明任何现场能力。
NOT_PROVEN = console.NOT_PROVEN

# 必需证据包沿用 material pack 的八类现场材料，名称对齐下游 gates。
REQUIRED_EVIDENCE_PACKET = pack.REQUIRED_MATERIALS

# 成功文案或动作放行必须阻断，避免验收简报被误读为现场通过。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bacceptance\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
)


def _utc_now() -> str:
    # UTC 时间便于 Docker/local artifact 跨机器按时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON 和非 object 都转成 blocked artifact，避免验收简报无留痕。
    if not path:
        return {}, "drill_console_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "drill_console_json_missing"
    except json.JSONDecodeError:
        return {}, "drill_console_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "drill_console_json_read_error"
    if not isinstance(payload, dict):
        return {}, "drill_console_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段，字符串 wrapper 不能伪装可信 JSON。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 的字段位置不同，取首个非空值。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 下游只需要短简报清单；限长能避免复制完整上游 artifact。
    if isinstance(value, list):
        return [pack._safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [pack._safe_text(value)]


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免把任意 raw payload 当成 drill console。
    candidates = [payload]
    for key in (
        "route_task_field_retest_acceptance_brief",
        "route_task_field_retest_acceptance_brief_summary",
        "route_task_field_retest_drill_console",
        "route_task_field_retest_drill_console_summary",
        "drill_console",
        "drill_console_summary",
        "console",
        "console_summary",
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
    # 优先消费 schema 命中的嵌套对象；没有命中时保留顶层解释 unsupported。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, Any]:
    # schema 与 boundary 必须同时支持，防止跨 gate 材料误入验收简报。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = pack._safe_text(source.get("schema", ""))
    boundary = pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # same evidence_ref 是 material pack、console、brief 串联主键。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "drill_console_summary")
    return pack._safe_ref(
        _first_text(
            source.get("evidence_ref"),
            summary.get("evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 弱类型字符串必须 fail closed；这里要求 JSON boolean true。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "drill_console_summary")
    return source.get(
        "same_evidence_ref_required",
        summary.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
    )


def _source_console_status(source: dict[str, Any]) -> str:
    # 上游 console 状态只决定 brief 是否 ready，不被当成真实证明。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "drill_console_summary")
    return pack._safe_text(
        _first_text(
            source.get("console_status"),
            source.get("status"),
            summary.get("console_status"),
            summary.get("status"),
            safe_copy.get("console_status"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _has_success_or_control_claim(value: Any) -> bool:
    # 顶层布尔字段和自由文本都检查，避免 wrapper 越界放行动作。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = pack._encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _unsafe_copy(value: Any) -> bool:
    # 复用 material pack 的禁词/路径扫描，并补充 brief 自身成功文案。
    return pack._has_forbidden_copy(value) or pack._has_raw_path_copy(value) or _has_success_or_control_claim(value)


def _missing_materials(source: dict[str, Any]) -> list[str]:
    # brief 只沿用上游 summary 的缺失项提示，不读取真实材料目录补证据。
    summary = _dict(source, "drill_console_summary")
    safe_copy = _dict(source, "safe_copy")
    raw = source.get("missing_materials") or summary.get("missing_materials") or safe_copy.get("missing_materials")
    names = []
    for item in _safe_list(raw, limit=len(REQUIRED_EVIDENCE_PACKET)):
        name = pack._safe_text(item).strip()
        if name in REQUIRED_EVIDENCE_PACKET and name not in names:
            names.append(name)
    return names


def _command_labels(source: dict[str, Any]) -> list[str]:
    # command labels 来自 drill console，不复制 raw command 或真实路径。
    summary = _dict(source, "drill_console_summary")
    labels = _safe_list(source.get("command_labels") or summary.get("command_labels"), limit=6)
    filtered = [label for label in labels if label in {"material_pack", "result_intake", "result_reconciliation"}]
    return filtered or ["material_pack", "result_intake", "result_reconciliation"]


def _field_entry_prerequisites(evidence_ref: str, missing: list[str]) -> list[str]:
    # 前置条件强调现场入口，不把本地 brief 当作发车许可。
    ref = evidence_ref or "<same_evidence_ref>"
    prerequisites = [
        f"Use one safe evidence_ref={ref} across material pack, result intake, and reconciliation.",
        "Prepare Nav2/fixed-route runtime capture plan before field entry.",
        "Prepare elevator door_state, target_floor_confirmation, and human assistance note templates.",
        "Keep Robot diagnostics and mobile panels read-only until real evidence is reviewed.",
    ]
    if missing:
        prerequisites.append("Repair missing evidence packet items before field entry: " + ", ".join(missing))
    return [pack._safe_text(item) for item in prerequisites]


def _execution_checklist(command_labels: list[str], evidence_ref: str) -> list[str]:
    # 执行清单只描述 PC 复账顺序，不触发 ROS/Nav2/硬件动作。
    ref = evidence_ref or "<same_evidence_ref>"
    labels = ", ".join(command_labels)
    return [
        f"Confirm drill console command labels stay ordered: {labels}.",
        f"Collect field materials against evidence_ref={ref}; do not change this evidence id mid-run.",
        "Run result intake and reconciliation only after field material summaries exist.",
        "Record blocked reason when any required packet item is missing or rejected.",
        "Keep delivery_success=false and primary_actions_enabled=false in this brief.",
    ]


def _pass_fail_criteria(missing: list[str]) -> dict[str, list[str]]:
    # pass/fail criteria 是未来现场评审口径，不是当前 Docker proof 结论。
    fail_items = [
        "Any required evidence packet item is missing, unsafe, placeholder, or mismatched.",
        "Any source summary changes evidence_ref or weakens same_evidence_ref_required=true.",
        "Any copy claims field_pass, hil_pass, delivery_success, or enables primary actions.",
    ]
    if missing:
        fail_items.append("Current known missing packet items: " + ", ".join(missing))
    return {
        "pass_ready_when": [
            "All required evidence packet items are present as sanitized summaries.",
            "Result intake and reconciliation agree on one safe evidence_ref.",
            "Operator review explicitly records dropoff/cancel completion and delivery_result outcome.",
        ],
        "fail_closed_when": fail_items,
    }


def _required_evidence_packet(missing: list[str]) -> list[dict[str, str]]:
    # 固定八类材料便于现场 owner 对照补采，仍不读取真实材料目录。
    missing_set = set(missing)
    labels = {
        "nav2_or_fixed_route_runtime_log": "Nav2/fixed-route runtime log",
        "route_completion_signal": "route completion signal",
        "task_record": "task record",
        "door_state": "door_state",
        "target_floor_confirmation": "target_floor_confirmation",
        "human_assistance_note": "human_assistance_note",
        "dropoff_or_cancel_completion": "dropoff_or_cancel_completion",
        "delivery_result": "delivery_result",
    }
    packet = []
    for name in REQUIRED_EVIDENCE_PACKET:
        packet.append(
            {
                "name": name,
                "label": labels[name],
                "required": "true",
                "current_status": "missing_in_source_summary" if name in missing_set else "required_for_field_review",
            }
        )
    return packet


def _owner_handoff(evidence_ref: str) -> dict[str, list[str] | str]:
    # owner handoff 把 Autonomy 输出交给 Robot/mobile 只读消费，不改变动作语义。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "autonomy_owner": f"Keep acceptance brief and evidence packet aligned on evidence_ref={ref}.",
        "robot_owner": "Consume only summary/safe_copy as metadata; do not enable collect/dropoff/cancel/ACK.",
        "full_stack_owner": "Render only whitelisted fields; do not expose raw JSON, paths, topics, or credentials.",
        "product_owner": "Close OKR as software_proof only unless real field materials are attached.",
        "handoff_checks": [
            "same_evidence_ref_required remains true.",
            "delivery_success=false remains visible.",
            "primary_actions_enabled=false remains visible.",
        ],
    }


def _rerun_notes(status: str, evidence_ref: str, source_console_status: str, missing: list[str]) -> list[str]:
    # rerun notes 把 blocked 原因转成下一步，不放现场通过措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    notes = [f"Rerun acceptance brief with evidence_ref={ref} after drill console repair."]
    if source_console_status and source_console_status != "ready_for_drill_console_not_proven":
        notes.append(f"Review source console_status={source_console_status} before owner handoff.")
    if missing:
        notes.append("Keep missing packet items visible in field entry prerequisites.")
    if status != "ready_for_field_retest_acceptance_brief_not_proven":
        notes.append("Fix source schema, boundary, same evidence_ref, and safe copy before reusing summary.")
    notes.append("This brief remains not_proven and cannot enable primary actions.")
    return [pack._safe_text(note) for note in notes[:6]]


def _acceptance_status(
    load_issue: str,
    source_status: dict[str, Any],
    evidence_ref: str,
    requested_ref: str,
    same_ref_required: Any,
    unsafe_copy: bool,
    source_console_status: str,
) -> str:
    # fail-closed 顺序固定，危险输入不会被普通缺失原因遮住。
    if load_issue in {"drill_console_json_bad_json", "drill_console_json_read_error", "drill_console_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_drill_console"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_schema"
    if not evidence_ref:
        return "blocked_missing_evidence_ref"
    if requested_ref and evidence_ref != requested_ref:
        return "blocked_same_evidence_ref_mismatch"
    if same_ref_required is not True:
        return "blocked_same_evidence_ref_not_required"
    if unsafe_copy:
        return "blocked_unsafe_drill_console_copy"
    if source_console_status != "ready_for_drill_console_not_proven":
        return "blocked_drill_console_not_ready"
    return "ready_for_field_retest_acceptance_brief_not_proven"


def _safe_copy(status: str, evidence_ref: str, missing: list[str]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不包含 raw artifact 或本机路径。
    return {
        "schema": f"{BRIEF_SUMMARY_SCHEMA}.safe_copy",
        "acceptance_status": status,
        "evidence_boundary": BRIEF_BOUNDARY,
        "evidence_ref": evidence_ref,
        "required_evidence_packet": list(REQUIRED_EVIDENCE_PACKET),
        "missing_evidence_packet": missing,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    source_console_status: str,
    field_entry_prerequisites: list[str],
    execution_checklist: list[str],
    pass_fail_criteria: dict[str, list[str]],
    required_packet: list[dict[str, str]],
    owner_handoff: dict[str, Any],
    rerun_notes: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是下游消费首选字段集，必须稳定且 phone-safe。
    return {
        "schema": BRIEF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": BRIEF_BOUNDARY,
        "boundary": BRIEF_BOUNDARY,
        "status": status,
        "acceptance_status": status,
        "source_console_status": source_console_status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "field_entry_prerequisites": field_entry_prerequisites,
        "execution_checklist": execution_checklist,
        "pass_fail_criteria": pass_fail_criteria,
        "required_evidence_packet": required_packet,
        "owner_handoff": owner_handoff,
        "rerun_notes": rerun_notes,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def build_route_task_field_retest_acceptance_brief(
    drill_console_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    # 主构建函数保持 CLI/unittest 共用，便于离线验证同一逻辑。
    payload, load_issue = _load_json(drill_console_json)
    source = _find_source(payload) if payload else {}
    source_status = _source_status(load_issue, source)
    requested_ref = pack._safe_ref(evidence_ref)
    source_ref = _source_evidence_ref(source)
    resolved_ref = requested_ref or source_ref
    same_ref_required = _same_ref_required(source)
    source_console_status = _source_console_status(source)
    missing = _missing_materials(source)
    unsafe = _unsafe_copy(source)
    status = _acceptance_status(
        load_issue,
        source_status,
        source_ref,
        requested_ref,
        same_ref_required,
        unsafe,
        source_console_status,
    )
    command_labels = _command_labels(source)
    prerequisites = _field_entry_prerequisites(resolved_ref, missing)
    checklist = _execution_checklist(command_labels, resolved_ref)
    criteria = _pass_fail_criteria(missing)
    required_packet = _required_evidence_packet(missing)
    handoff = _owner_handoff(resolved_ref)
    rerun_notes = _rerun_notes(status, resolved_ref, source_console_status, missing)
    safe_copy = _safe_copy(status, resolved_ref, missing)
    summary = _summary_payload(
        status,
        resolved_ref,
        source_console_status,
        prerequisites,
        checklist,
        criteria,
        required_packet,
        handoff,
        rerun_notes,
        safe_copy,
    )
    artifact = {
        "schema": BRIEF_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": BRIEF_BOUNDARY,
        "boundary": BRIEF_BOUNDARY,
        "acceptance_status": status,
        "source_drill_console": {
            "schema": pack._safe_text(source.get("schema", "")),
            "evidence_boundary": pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
            "load_status": source_status["load_status"],
            "schema_status": source_status["schema_status"],
            "console_status": source_console_status,
        },
        "same_evidence_ref_required": True,
        "evidence_ref": resolved_ref,
        "field_entry_prerequisites": prerequisites,
        "execution_checklist": checklist,
        "pass_fail_criteria": criteria,
        "required_evidence_packet": required_packet,
        "owner_handoff": handoff,
        "rerun_notes": rerun_notes,
        "acceptance_brief_summary": summary,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "ros_graph",
            "nav2_runtime",
            "serial_uart",
            "wave_rover",
            "real_elevator",
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
        summary["status"] = "blocked_unsafe_acceptance_brief_summary"
        summary["acceptance_status"] = "blocked_unsafe_acceptance_brief_summary"
        artifact["acceptance_status"] = "blocked_unsafe_acceptance_brief_summary"
        artifact["acceptance_brief_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时创建父目录；不指定时由 --once-json/stdout 展示 artifact。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 不接触运行时系统，只把 drill console JSON 转成 acceptance brief。
    parser = argparse.ArgumentParser(description="Build route/task field retest acceptance brief artifact")
    parser.add_argument("--drill-console-json", required=True, help="drill console artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for the acceptance brief")
    parser.add_argument("--output", default="", help="optional acceptance brief artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional acceptance brief summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print acceptance brief artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_acceptance_brief(args.drill_console_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_acceptance_brief: artifact_file:{pack._safe_ref(args.output)}")
        print(f"acceptance_status: {artifact['acceptance_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
