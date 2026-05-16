#!/usr/bin/env python3
"""生成 route/task field retest drill console artifact。

该 gate 只读取上一轮 route_task_field_retest_operator_drill 的 artifact、
summary 或 wrapper/nested JSON，把 material pack / result intake /
result reconciliation 的 PC 操作标签、safe checklist 和 operator callback
要求整理成 console artifact 与 summary。它不读取真实材料目录，不访问 ROS graph、
Nav2 runtime、serial/UART、硬件、真实电梯、外部云、真实手机/browser 或 4G。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_material_pack as pack
import route_task_field_retest_operator_drill as drill


# console 是 operator drill 后的 PC 侧汇总契约，不复用上一环 schema。
CONSOLE_SCHEMA = "trashbot.route_task_field_retest_drill_console.v1"
CONSOLE_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_drill_console_summary.v1"
SCHEMA_VERSION = 1
CONSOLE_BOUNDARY = "software_proof_docker_route_task_field_retest_drill_console_gate"

# 只接受 operator drill 的 artifact/summary，避免 material pack 被跳级解释成 console。
SOURCE_SCHEMAS = {drill.DRILL_SCHEMA, drill.DRILL_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {drill.DRILL_BOUNDARY, ""}

# rg 验收需要这些 literal；也给人工复盘一个短边界。
BOUNDARY_NOTE = (
    "software_proof_docker_route_task_field_retest_drill_console_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# console 只证明本地演练顺序和安全摘要可展示，不证明任何现场能力。
NOT_PROVEN = drill.NOT_PROVEN

# 成功文案或控制放行必须阻断，防止 console 被误读为可操作面。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\boperator\s+drill\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
)


def _utc_now() -> str:
    # UTC 时间便于 Docker-only artifact 跨机器按时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON 和非 object 都转成 blocked artifact，避免 console 无留痕。
    if not path:
        return {}, "operator_drill_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "operator_drill_json_missing"
    except json.JSONDecodeError:
        return {}, "operator_drill_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "operator_drill_json_read_error"
    if not isinstance(payload, dict):
        return {}, "operator_drill_json_not_object"
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
    # 下游只需要短 checklist；限长能避免复制完整上游 artifact。
    if isinstance(value, list):
        return [pack._safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [pack._safe_text(value)]


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免把任意 raw payload 当成 operator drill。
    candidates = [payload]
    for key in (
        "route_task_field_retest_drill_console",
        "route_task_field_retest_drill_console_summary",
        "route_task_field_retest_operator_drill",
        "route_task_field_retest_operator_drill_summary",
        "operator_drill",
        "operator_drill_summary",
        "drill",
        "drill_summary",
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
    # schema 与 boundary 必须同时支持，防止跨 gate 材料误入 console。
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
    summary = _dict(source, "operator_drill_summary")
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
    summary = _dict(source, "operator_drill_summary")
    return source.get(
        "same_evidence_ref_required",
        summary.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
    )


def _source_verdict(source: dict[str, Any]) -> str:
    # 上游 drill 状态只决定 console 是否 ready，不被当成真实证明。
    safe_copy = _dict(source, "safe_copy")
    summary = _dict(source, "operator_drill_summary")
    return pack._safe_text(
        _first_text(
            source.get("operator_drill_verdict"),
            source.get("status"),
            summary.get("operator_drill_verdict"),
            summary.get("status"),
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
    # 复用 material pack 的禁词/路径扫描，并补充 console 自身成功文案。
    return pack._has_forbidden_copy(value) or pack._has_raw_path_copy(value) or _has_success_or_control_claim(value)


def _command_chain(source: dict[str, Any], evidence_ref: str) -> list[dict[str, str]]:
    # 只消费 operator drill 已脱敏的命令标签；缺失时生成占位命令，不读真实目录。
    chain = source.get("command_chain")
    if not isinstance(chain, list):
        summary = _dict(source, "operator_drill_summary")
        chain = summary.get("command_chain")
    if isinstance(chain, list) and chain:
        labels = {"material_pack", "result_intake", "result_reconciliation"}
        normalized = []
        for item in chain:
            if not isinstance(item, dict):
                continue
            label = pack._safe_text(item.get("label", ""))
            command = pack._safe_text(item.get("command", ""))
            if label in labels and command:
                normalized.append({"label": label, "command": command})
        if [item["label"] for item in normalized] == ["material_pack", "result_intake", "result_reconciliation"]:
            return normalized
    return [
        {"label": "material_pack", "command": drill._material_pack_command(evidence_ref)},
        {"label": "result_intake", "command": drill._result_intake_command(evidence_ref)},
        {"label": "result_reconciliation", "command": drill._result_reconciliation_command(evidence_ref)},
    ]


def _missing_materials(source: dict[str, Any]) -> list[str]:
    # console 只沿用上游 summary 的缺失项提示，不读取真实材料目录补证据。
    summary = _dict(source, "operator_drill_summary")
    safe_copy = _dict(source, "safe_copy")
    raw = source.get("missing_materials") or summary.get("missing_materials") or safe_copy.get("missing_materials")
    names = []
    for item in _safe_list(raw, limit=len(pack.REQUIRED_MATERIALS)):
        name = pack._safe_text(item).strip()
        if name in pack.REQUIRED_MATERIALS and name not in names:
            names.append(name)
    return names


def _material_count(source: dict[str, Any], missing: list[str]) -> dict[str, Any]:
    # material count 只是上游摘要，不代表现场材料真实齐备。
    summary = _dict(source, "operator_drill_summary")
    count = _dict(source, "material_count") or _dict(summary, "material_count")
    accepted = count.get("accepted_count")
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


def _missing_material_prompts(source: dict[str, Any], missing: list[str], evidence_ref: str) -> list[str]:
    # 优先保留上游 safe prompts；缺失时生成最小补采提示。
    summary = _dict(source, "operator_drill_summary")
    prompts = _safe_list(source.get("missing_material_prompts") or summary.get("missing_material_prompts"), limit=12)
    if prompts:
        return prompts
    return drill._missing_material_prompts(missing, evidence_ref)


def _operator_callback_checklist(source: dict[str, Any], evidence_ref: str) -> list[str]:
    # callback checklist 只要求事实摘要和失败原因，不能要求宣称成功。
    summary = _dict(source, "operator_drill_summary")
    checklist = _safe_list(source.get("operator_callback_checklist") or summary.get("operator_callback_checklist"), limit=12)
    if checklist:
        return checklist
    return drill._operator_callback_checklist(evidence_ref)


def _safe_checklist(command_chain: list[dict[str, str]], missing: list[str], evidence_ref: str) -> list[str]:
    # console checklist 是 PC 操作顺序，不触发 ROS/Nav2/硬件动作。
    labels = ", ".join(item["label"] for item in command_chain)
    ref = evidence_ref or "<same_evidence_ref>"
    checklist = [
        f"Confirm command labels are ordered: {labels}.",
        f"Keep evidence_ref={ref} unchanged across every PC artifact.",
        "Use only sanitized summaries for Robot diagnostics and mobile read-only panels.",
        "Keep delivery_success=false and primary_actions_enabled=false until real review closes.",
    ]
    if missing:
        checklist.append("Repair missing materials before rerun: " + ", ".join(missing))
    return [pack._safe_text(item) for item in checklist]


def _rerun_notes(status: str, evidence_ref: str, source_verdict: str, missing: list[str]) -> list[str]:
    # rerun notes 把 blocked 原因转成下一步，不放现场通过措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    notes = [f"Rerun operator drill console with evidence_ref={ref} after source repair."]
    if source_verdict and source_verdict != "ready_for_operator_drill_not_proven":
        notes.append(f"Review source operator_drill_verdict={source_verdict} before console handoff.")
    if missing:
        notes.append("Keep missing material prompts visible for operator callback.")
    if status != "ready_for_drill_console_not_proven":
        notes.append("Fix source schema, boundary, same evidence_ref, and safe copy before reusing summary.")
    notes.append("This console remains not_proven and cannot enable primary actions.")
    return [pack._safe_text(note) for note in notes[:6]]


def _console_status(
    load_issue: str,
    source_status: dict[str, Any],
    evidence_ref: str,
    requested_ref: str,
    same_ref_required: Any,
    unsafe_copy: bool,
    source_verdict: str,
) -> str:
    # fail-closed 顺序固定，危险输入不会被普通缺失原因遮住。
    if load_issue in {"operator_drill_json_bad_json", "operator_drill_json_read_error", "operator_drill_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_operator_drill"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_schema"
    if not evidence_ref:
        return "blocked_missing_evidence_ref"
    if requested_ref and evidence_ref != requested_ref:
        return "blocked_same_evidence_ref_mismatch"
    if same_ref_required is not True:
        return "blocked_same_evidence_ref_not_required"
    if unsafe_copy:
        return "blocked_unsafe_operator_drill_copy"
    if source_verdict != "ready_for_operator_drill_not_proven":
        return "blocked_operator_drill_not_ready"
    return "ready_for_drill_console_not_proven"


def _safe_copy(status: str, evidence_ref: str, material_count: dict[str, Any], missing: list[str]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不包含 raw artifact 或本机路径。
    return {
        "schema": f"{CONSOLE_SUMMARY_SCHEMA}.safe_copy",
        "console_status": status,
        "evidence_boundary": CONSOLE_BOUNDARY,
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
    safe_checklist: list[str],
    missing_prompts: list[str],
    callback_checklist: list[str],
    rerun_notes: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是下游消费首选字段集，必须稳定且 phone-safe。
    return {
        "schema": CONSOLE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": CONSOLE_BOUNDARY,
        "boundary": CONSOLE_BOUNDARY,
        "status": status,
        "console_status": status,
        "source_operator_drill_verdict": source_verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "command_labels": [item["label"] for item in command_chain],
        "command_chain": command_chain,
        "material_count": material_count,
        "safe_checklist": safe_checklist,
        "missing_materials": missing,
        "missing_material_prompts": missing_prompts,
        "operator_callback_checklist": callback_checklist,
        "rerun_notes": rerun_notes,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def build_route_task_field_retest_drill_console(
    operator_drill_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    # 主构建函数保持 CLI/unittest 共用，便于离线验证同一逻辑。
    payload, load_issue = _load_json(operator_drill_json)
    source = _find_source(payload) if payload else {}
    source_status = _source_status(load_issue, source)
    requested_ref = pack._safe_ref(evidence_ref)
    source_ref = _source_evidence_ref(source)
    resolved_ref = requested_ref or source_ref
    same_ref_required = _same_ref_required(source)
    source_verdict = _source_verdict(source)
    missing = _missing_materials(source)
    material_count = _material_count(source, missing)
    unsafe = _unsafe_copy(source)
    status = _console_status(load_issue, source_status, source_ref, requested_ref, same_ref_required, unsafe, source_verdict)
    command_chain = _command_chain(source, resolved_ref)
    safe_checklist = _safe_checklist(command_chain, missing, resolved_ref)
    prompts = _missing_material_prompts(source, missing, resolved_ref)
    callback = _operator_callback_checklist(source, resolved_ref)
    rerun_notes = _rerun_notes(status, resolved_ref, source_verdict, missing)
    safe_copy = _safe_copy(status, resolved_ref, material_count, missing)
    summary = _summary_payload(
        status,
        resolved_ref,
        source_verdict,
        material_count,
        missing,
        command_chain,
        safe_checklist,
        prompts,
        callback,
        rerun_notes,
        safe_copy,
    )
    artifact = {
        "schema": CONSOLE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": CONSOLE_BOUNDARY,
        "boundary": CONSOLE_BOUNDARY,
        "console_status": status,
        "source_operator_drill": {
            "schema": pack._safe_text(source.get("schema", "")),
            "evidence_boundary": pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
            "load_status": source_status["load_status"],
            "schema_status": source_status["schema_status"],
            "operator_drill_verdict": source_verdict,
        },
        "same_evidence_ref_required": True,
        "evidence_ref": resolved_ref,
        "command_chain": command_chain,
        "safe_checklist": safe_checklist,
        "missing_material_prompts": prompts,
        "operator_callback_checklist": callback,
        "rerun_notes": rerun_notes,
        "drill_console_summary": summary,
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
        summary["status"] = "blocked_unsafe_drill_console_summary"
        summary["console_status"] = "blocked_unsafe_drill_console_summary"
        artifact["console_status"] = "blocked_unsafe_drill_console_summary"
        artifact["drill_console_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时创建父目录；不指定时由 --once-json/stdout 展示 artifact。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 不接触运行时系统，只把 operator drill JSON 转成 drill console。
    parser = argparse.ArgumentParser(description="Build route/task field retest drill console artifact")
    parser.add_argument("--operator-drill-json", required=True, help="operator drill artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for the drill console")
    parser.add_argument("--output", default="", help="optional drill console artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional drill console summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print drill console artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_drill_console(args.operator_drill_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_drill_console: artifact_file:{pack._safe_ref(args.output)}")
        print(f"console_status: {artifact['console_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
