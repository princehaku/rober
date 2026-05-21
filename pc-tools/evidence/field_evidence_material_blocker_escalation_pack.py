#!/usr/bin/env python3
"""生成 field evidence material blocker escalation pack artifact。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_real_material_followup_escalation_status as followup
import field_evidence_real_material_owner_ack_review_decision as owner_ack
import field_evidence_real_material_response_review_handoff as handoff
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.field_evidence_material_blocker_escalation_pack.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_material_blocker_escalation_pack_summary.v1"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_material_blocker_escalation_pack"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_material_blocker_escalation_pack_gate"

# 只接受上一轮人工复核/升级链路的 safe surface，禁止越级读取 raw field files。
SOURCE_SCHEMAS = {
    owner_ack.SCHEMA,
    owner_ack.SUMMARY_SCHEMA,
    followup.SCHEMA,
    followup.SUMMARY_SCHEMA,
    handoff.HANDOFF_SCHEMA,
    handoff.HANDOFF_SUMMARY_SCHEMA,
}
SOURCE_BOUNDARIES = {
    owner_ack.EVIDENCE_BOUNDARY,
    followup.EVIDENCE_BOUNDARY,
    handoff.HANDOFF_BOUNDARY,
}

READY_STATUS = "blocked_materials_escalation_pack_ready_not_proven"
MISSING_STATUS = "blocked_missing_safe_material_blocker_source_not_proven"
UNSUPPORTED_STATUS = "blocked_unsupported_material_blocker_escalation_source"
UNSAFE_STATUS = "blocked_unsafe_or_success_control_claim_material_blocker_escalation_not_proven"
MISMATCH_STATUS = "blocked_evidence_ref_mismatch_material_blocker_escalation_not_proven"

DEFAULT_EVIDENCE_REF = "field-material-blocker-escalation-2026-05-22T02-00Z"
PR5_REVIEW_THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"

DEFAULT_NEXT_REQUIRED_EVIDENCE = [
    "real public HTTPS/TLS or 4G/SIM external proof",
    "real OSS/CDN live traffic or production DB/queue connectivity proof",
    "real 2D LiDAR / ToF SKU/source/receipt/procurement/installation/calibration material",
    "real Nav2/fixed-route runtime log under the same safe evidence_ref",
    "real route completion signal and field task record under the same safe evidence_ref",
    "real elevator door state and target floor confirmation material",
    "real dropoff/cancel completion material and verified terminal delivery result",
    "real iPhone/Android browser/device evidence",
]

BOUNDARY_NOTE = (
    "field_evidence_material_blocker_escalation_pack; "
    "software_proof_docker_field_evidence_material_blocker_escalation_pack_gate; "
    "schema=trashbot.field_evidence_material_blocker_escalation_pack.v1; "
    "summary=trashbot.field_evidence_material_blocker_escalation_pack_summary.v1; "
    "source=software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; "
    "next_required_evidence; owner_escalation_level; blocked_reason; target_owner"
)

# 设计约束 01：本 gate 只读 safe summary/wrapper，不读取 raw 现场文件。
# 设计约束 02：schema 与 evidence_boundary 必须双白名单命中。
# 设计约束 03：source=software_proof、not_proven 与三个 false flag 不可放松。
# 设计约束 04：blocked artifact 仍 exit 0，便于 Docker-only sprint 留痕。
# 设计约束 05：输出只生成升级包，不触发 ROS graph、Nav2 runtime 或控制动作。
# 设计约束 06：PR #5 thread id 只能作为待升级线索，不代表 reviewer resolved。
# 设计约束 07：owner_escalation_level 是人工组织升级等级，不是机器人权限等级。
# 设计约束 08：field_safe_copy 是唯一建议给下游复制的短字段面。
# 设计约束 09：unsupported、missing、unsafe、success/control claim 都 fail closed。
# 设计约束 10：不输出 raw ROS topic、serial/UART、WAVE ROVER、凭证或本机路径。
# 设计约束 11：same_evidence_ref_required 必须保持 JSON boolean true。
# 设计约束 12：所有技术注释使用中文，说明保守边界和为什么这样做。


def _utc_now() -> str:
    # UTC 便于 Docker artifact 与 sprint 记录跨时区排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每层重复 false flags，避免下游只消费局部对象时误启主操作。
    return {
        "source": "software_proof",
        "status": "not_proven",
        "software_proof": True,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _encoded(value: Any) -> str:
    # 安全扫描使用稳定 JSON，覆盖所有嵌套 key/value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any) -> str:
    # 统一沿用现有材料 gate 的短文本脱敏策略。
    return material_pack._safe_text(value).strip()


def _safe_list(value: Any, limit: int = 24) -> list[str]:
    # escalation pack 只保留短列表，避免搬运完整上游 artifact。
    if isinstance(value, list):
        result: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                text = _first_text(item.get("material"), item.get("name"), item.get("action"), item.get("blocked_reason"))
            else:
                text = str(item if item is not None else "")
            safe = _safe_text(text)
            if safe:
                result.append(safe)
        return result
    if value in (None, ""):
        return []
    text = _safe_text(value)
    return [text] if text else []


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只信任 object wrapper，字符串化 JSON 不作为可信 safe source。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # 同族 artifact、summary、safe_copy 的字段位置不完全一致。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺 source 时必须输出 blocked，而不是构造 ready pack。
    if not path:
        return {}, "material_blocker_source_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "material_blocker_source_json_missing"
    except json.JSONDecodeError:
        return {}, "material_blocker_source_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "material_blocker_source_json_read_error"
    if not isinstance(payload, dict):
        return {}, "material_blocker_source_json_not_object"
    return payload, ""


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 递归仅走已知 safe wrapper key，避免 raw materials 被误当 source。
    candidates = [payload]
    for key in (
        "field_evidence_material_blocker_escalation_pack",
        "field_evidence_material_blocker_escalation_pack_summary",
        "field_evidence_real_material_owner_ack_review_decision",
        "field_evidence_real_material_owner_ack_review_decision_summary",
        "field_evidence_real_material_followup_escalation_status",
        "field_evidence_real_material_followup_escalation_status_summary",
        "field_evidence_real_material_response_review_handoff",
        "field_evidence_real_material_response_review_handoff_summary",
        "robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary",
        "robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "field_safe_copy",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
        "diagnostics",
        "latest_status",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中安全来源时才可信；否则保留顶层用于 unsupported 解释。
    for candidate in _candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_schema(source: dict[str, Any]) -> str:
    # schema 单独抽取，便于 summary 写明 blocked reason。
    return _safe_text(source.get("schema", ""))


def _source_boundary(source: dict[str, Any]) -> str:
    # 兼容 evidence_boundary / boundary 两种同族字段。
    return _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 同时命中，防止其他 safe copy 越权升级。
    return _source_schema(source) in SOURCE_SCHEMAS and _source_boundary(source) in SOURCE_BOUNDARIES


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 是从 review/ack/followup 到 escalation 的唯一串联主键。
    safe_copy = _dict(source, "safe_copy")
    field_safe = _dict(source, "field_safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return material_pack._safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            field_safe.get("safe_evidence_ref"),
            field_safe.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            default="",
        )
    )


def _requested_ref(value: str, source_ref: str) -> str:
    # CLI evidence_ref 为空时沿用 source；仍用 safe_ref 防止路径进入输出。
    return material_pack._safe_ref(value or source_ref or DEFAULT_EVIDENCE_REF)


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 字符串 true 不接受，避免弱 typing 绕过同证据号要求。
    safe_copy = _dict(source, "safe_copy")
    field_safe = _dict(source, "field_safe_copy")
    return source.get(
        "same_evidence_ref_required",
        safe_copy.get("same_evidence_ref_required", field_safe.get("same_evidence_ref_required", True)),
    )


def _software_not_proven(source: dict[str, Any]) -> bool:
    # 五个边界字段必须同时满足，不能只靠 schema 判断安全。
    safe_copy = _dict(source, "safe_copy")
    field_safe = _dict(source, "field_safe_copy")
    encoded = _encoded(source)
    source_text = _first_text(source.get("source"), safe_copy.get("source"), field_safe.get("source"), default="")
    return (
        source_text == "software_proof"
        and "not_proven" in encoded
        and source.get("safe_to_control", safe_copy.get("safe_to_control", field_safe.get("safe_to_control"))) is False
        and source.get("delivery_success", safe_copy.get("delivery_success", field_safe.get("delivery_success"))) is False
        and source.get("primary_actions_enabled", safe_copy.get("primary_actions_enabled", field_safe.get("primary_actions_enabled"))) is False
    )


def _has_unsafe_copy(value: Any) -> bool:
    # 成功/控制、路径、凭证、raw 细节一律阻断，防止升级包被误当 proof。
    return (
        material_pack._has_forbidden_copy(value)
        or material_pack._has_raw_path_copy(value)
        or material_pack._has_success_or_control_claim(value)
    )


def _source_blocked_reason(source: dict[str, Any], load_issue: str, reasons: list[str]) -> str:
    # blocked_reason 优先取上游短字段；缺失时给可执行阻塞原因。
    if load_issue:
        return load_issue
    safe_copy = _dict(source, "safe_copy")
    field_safe = _dict(source, "field_safe_copy")
    reason = _first_text(
        source.get("blocked_reason"),
        safe_copy.get("blocked_reason"),
        field_safe.get("blocked_reason"),
        source.get("decision_status"),
        source.get("followup_status"),
        default="",
    )
    return _safe_text(reason or ";".join(reasons) or "real_materials_missing_for_field_delivery_and_external_proof")


def _source_next_required_evidence(source: dict[str, Any]) -> list[str]:
    # 只从 safe summary 抽取下一材料清单，缺失则回落稳定缺口集。
    safe_copy = _dict(source, "safe_copy")
    field_safe = _dict(source, "field_safe_copy")
    for holder in (source, safe_copy, field_safe):
        for key in ("next_required_evidence", "missing_evidence", "not_proven_items"):
            items = _safe_list(holder.get(key))
            if items:
                return items
    return list(DEFAULT_NEXT_REQUIRED_EVIDENCE)


def _status_for_source(
    load_issue: str,
    source: dict[str, Any],
    source_ref: str,
    requested_ref: str,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，任何不确定输入都不能落入 ready pack。
    if load_issue:
        return MISSING_STATUS, [load_issue]
    if not _schema_supported(source):
        return UNSUPPORTED_STATUS, ["unsupported_safe_summary_schema_or_boundary"]
    if _has_unsafe_copy(source):
        return UNSAFE_STATUS, ["unsafe_or_success_control_claim_in_safe_source"]
    if not _software_not_proven(source):
        return UNSUPPORTED_STATUS, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if _same_ref_required(source) is not True:
        return MISMATCH_STATUS, ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return MISMATCH_STATUS, ["safe_evidence_ref_missing"]
    if requested_ref != source_ref:
        return MISMATCH_STATUS, [f"requested_ref:{requested_ref}!={source_ref}"]
    return READY_STATUS, ["safe_source_consumed_for_owner_escalation_pack_only"]


def _target_owner(source_schema: str, status: str) -> str:
    # owner 用于组织升级，不代表该 owner 已完成真实材料采集。
    if status != READY_STATUS:
        return "field-owner"
    if source_schema in (owner_ack.SCHEMA, owner_ack.SUMMARY_SCHEMA):
        return "Product Manager / OKR Owner"
    if source_schema in (followup.SCHEMA, followup.SUMMARY_SCHEMA):
        return "field-owner + Product Manager / OKR Owner"
    return "field-owner"


def _owner_escalation_level(status: str, source_schema: str) -> str:
    # 第三次材料 blocker 后必须升级为 owner/CEO 可决策事项。
    if status != READY_STATUS:
        return "blocked_safe_source_repair_required"
    if source_schema in (followup.SCHEMA, followup.SUMMARY_SCHEMA):
        return "owner_followup_overdue_escalate_to_product_owner_and_ceo_decision"
    return "owner_ack_review_ready_escalate_for_real_materials_before_more_wrappers"


def _field_safe_copy(
    status: str,
    reasons: list[str],
    evidence_ref: str,
    source_summary: dict[str, Any],
    next_required_evidence: list[str],
    blocked_reason: str,
    target_owner: str,
    owner_escalation_level: str,
) -> dict[str, Any]:
    # field_safe_copy 是唯一给 Robot/mobile/closeout 复制的短字段面。
    return {
        "schema": f"{SUMMARY_SCHEMA}.field_safe_copy",
        **_safe_flags(),
        "capability": CAPABILITY,
        "field_evidence_material_blocker_escalation_pack_status": status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_summary": source_summary,
        "next_required_evidence": next_required_evidence,
        "owner_escalation_level": owner_escalation_level,
        "blocked_reason": blocked_reason,
        "target_owner": target_owner,
        "decision_reasons": reasons,
        "review_refs": {"pr5_thread_id": PR5_REVIEW_THREAD_ID, "thread_state": "unresolved_material_pending_not_proven"},
        "message": "该升级包只把真实材料缺口转成 owner 可执行事项，不能作为 route/elevator、cloud、phone、HIL 或 delivery_success 证明。",
        "boundary_note": BOUNDARY_NOTE,
    }


def _summary_payload(
    status: str,
    reasons: list[str],
    evidence_ref: str,
    source_summary: dict[str, Any],
    next_required_evidence: list[str],
    blocked_reason: str,
    target_owner: str,
    owner_escalation_level: str,
    field_safe_copy: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    # summary 镜像 artifact 的稳定消费字段，供 Robot alias 和 mobile 只读展示。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        **_safe_flags(),
        "capability": CAPABILITY,
        "field_evidence_material_blocker_escalation_pack_status": status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_summary": source_summary,
        "next_required_evidence": next_required_evidence,
        "owner_escalation_level": owner_escalation_level,
        "blocked_reason": blocked_reason,
        "target_owner": target_owner,
        "field_safe_copy": field_safe_copy,
        "decision_reasons": reasons,
        "review_refs": {"pr5_thread_id": PR5_REVIEW_THREAD_ID, "thread_state": "unresolved_material_pending_not_proven"},
        "boundary_note": BOUNDARY_NOTE,
    }


def build_field_evidence_material_blocker_escalation_pack(
    material_blocker_source_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 safe summary/wrapper，生成 fail-closed blocker escalation pack。"""
    payload, load_issue = _load_json(material_blocker_source_json)
    source = _find_source(payload) if payload else {}
    source_ref = _source_ref(source) if source else ""
    requested_ref = _requested_ref(evidence_ref, source_ref)
    status, reasons = _status_for_source(load_issue, source, source_ref, requested_ref)
    source_summary = {
        "schema": _source_schema(source),
        "evidence_boundary": _source_boundary(source),
        "safe_evidence_ref": source_ref,
        "same_evidence_ref_required": _same_ref_required(source) if source else True,
        "source_is_software_proof_not_proven": _software_not_proven(source) if source else False,
        "unsafe_copy": bool(source) and _has_unsafe_copy(source),
    }
    next_required_evidence = _source_next_required_evidence(source)
    blocked_reason = _source_blocked_reason(source, load_issue, reasons)
    target_owner = _target_owner(source_summary["schema"], status)
    owner_escalation_level = _owner_escalation_level(status, source_summary["schema"])
    generated_at = _utc_now()
    field_safe_copy = _field_safe_copy(
        status,
        reasons,
        requested_ref,
        source_summary,
        next_required_evidence,
        blocked_reason,
        target_owner,
        owner_escalation_level,
    )
    summary = _summary_payload(
        status,
        reasons,
        requested_ref,
        source_summary,
        next_required_evidence,
        blocked_reason,
        target_owner,
        owner_escalation_level,
        field_safe_copy,
        generated_at,
    )
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        **_safe_flags(),
        "capability": CAPABILITY,
        "field_evidence_material_blocker_escalation_pack_status": status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_summary": source_summary,
        "next_required_evidence": next_required_evidence,
        "owner_escalation_level": owner_escalation_level,
        "blocked_reason": blocked_reason,
        "target_owner": target_owner,
        "field_safe_copy": field_safe_copy,
        "field_evidence_material_blocker_escalation_pack_summary": summary,
        "robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "decision_reasons": reasons,
        "review_refs": {"pr5_thread_id": PR5_REVIEW_THREAD_ID, "thread_state": "unresolved_material_pending_not_proven"},
        "non_access_scope": [
            "raw_field_materials",
            "ROS graph",
            "Nav2 runtime",
            "hardware transport runtime",
            "real cloud or OSS/CDN/DB/queue",
            "real phone/browser runtime",
            "robot control channels",
        ],
        "boundary_note": BOUNDARY_NOTE,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if _has_unsafe_copy(artifact) or _has_unsafe_copy(summary):
        # 最后一层防线：脱敏后仍不安全时保留 false flags 并切到 unsafe blocked。
        for output in (artifact, summary):
            output["field_evidence_material_blocker_escalation_pack_status"] = UNSAFE_STATUS
            output["blocked_reason"] = "unsafe_copy_after_sanitization"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 输出路径只用于落盘，不写入 payload，避免泄露本机路径。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，可在 PC/Docker-only 环境重复生成 blocked artifact。
    parser = argparse.ArgumentParser(
        description=(
            "Generate field_evidence_material_blocker_escalation_pack software_proof gate; "
            "keeps not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false."
        )
    )
    parser.add_argument("--material-blocker-source-json", required=True, help="safe summary/wrapper JSON from owner ack or material followup/review chain")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref for escalation pack")
    parser.add_argument("--output", default="", help="optional escalation pack artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional escalation pack summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print escalation pack artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_material_blocker_escalation_pack(
        args.material_blocker_source_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_material_blocker_escalation_pack: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_material_blocker_escalation_pack_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"field_evidence_material_blocker_escalation_pack_status: {artifact['field_evidence_material_blocker_escalation_pack_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
