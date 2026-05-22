#!/usr/bin/env python3
"""生成 field evidence rerun execution result acceptance handoff intake。

该 PC-only gate 接在
`field_evidence_rerun_execution_result_acceptance_review_handoff` 后面，只读取
上一轮 handoff artifact / summary / Robot diagnostics safe alias 或 wrapper JSON，
并读取 field owner/support 提交的脱敏 intake packet。输出只表示 owner intake
材料入口已被软件围栏复账，不读取真实 ROS/Nav2 runtime、硬件、真实电梯、外部云
或真实手机/browser，也不触发机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_acceptance_review_handoff as review_handoff
import route_task_field_retest_material_pack as material_pack


INTAKE_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake.v1"
INTAKE_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_summary.v1"
OWNER_INTAKE_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_owner_intake.v1"
SCHEMA_VERSION = 1
INTAKE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_gate"

# 上游只能是上一轮 acceptance review handoff，防止跳过人工交接阶段。
SOURCE_SCHEMAS = {review_handoff.HANDOFF_SCHEMA, review_handoff.HANDOFF_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {review_handoff.HANDOFF_BOUNDARY}
READY_SOURCE_HANDOFF = review_handoff.READY_HANDOFF

# intake state 表示本 gate 的独立判断，不复用上游 handoff_status。
READY_INTAKE = "ready_for_acceptance_handoff_owner_intake_not_proven"
INTAKE_NEEDS_MORE_MATERIAL = "intake_needs_more_material"
INTAKE_EVIDENCE_REF_MISMATCH = "intake_evidence_ref_mismatch"
INTAKE_UNSAFE_REJECTED = "intake_unsafe_rejected"
BLOCKED_MISSING_REVIEW_HANDOFF = "blocked_missing_review_handoff"
ALLOWED_INTAKE_STATES = (
    READY_INTAKE,
    INTAKE_NEEDS_MORE_MATERIAL,
    INTAKE_EVIDENCE_REF_MISMATCH,
    INTAKE_UNSAFE_REJECTED,
    BLOCKED_MISSING_REVIEW_HANDOFF,
)

# checklist 只表达后续真实材料类别；本 gate 不读取或验证真实材料正文。
REQUIRED_OWNER_INTAKE_MATERIALS = (
    "true task record",
    "true Nav2/fixed-route runtime log",
    "route completion signal",
    "true elevator door state",
    "target floor confirmation",
    "human assistance record",
    "dropoff/cancel completion or delivery result",
    "true phone/browser evidence",
)

NOT_PROVEN = review_handoff.NOT_PROVEN

# rg 围栏依赖这些 literal；同时给人工复核一个压缩边界说明。
BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_gate; "
    "field_evidence_rerun_execution_result_acceptance_review_handoff; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false; "
    "ready_for_acceptance_handoff_owner_intake_not_proven; "
    "intake_needs_more_material; intake_evidence_ref_mismatch; "
    "intake_unsafe_rejected; blocked_missing_review_handoff"
)

# 设计约束 01：本 gate 只消费上一轮 review handoff safe output。
# 设计约束 02：owner/support packet 只能是脱敏 metadata，不读取 raw material。
# 设计约束 03：ready 只表示 intake 入口可交给 owner，不证明现场材料为真。
# 设计约束 04：source=software_proof 与 not_proven 必须跨 gate 延续。
# 设计约束 05：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 06：same evidence_ref 是现场复账主键，不一致必须 fail closed。
# 设计约束 07：弱类型 same_evidence_ref_required 不能通过，必须是 JSON boolean true。
# 设计约束 08：owner packet 只接受 checklist 类别确认，不接受成功或控制文案。
# 设计约束 09：缺任一 required checklist 类别只能进入 needs_more_material。
# 设计约束 10：unsafe copy、credentials、raw path、ROS topic 和硬件细节必须拒绝。
# 设计约束 11：HIL、外部云、真实手机、verified terminal 或 PR #5 resolution 必须拒绝。
# 设计约束 12：summary 是 Robot/mobile 只读 safe alias，不携带 raw artifact。
# 设计约束 13：wrapper/nested JSON 只递归固定 key，避免采信任意 payload。
# 设计约束 14：非 ready 状态返回非零，方便调用方阻断发布链路。
# 设计约束 15：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 16：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 17：输出最终递归脱敏，防止新增字段绕过安全扫描。
# 设计约束 18：所有技术注释使用中文，解释 fail-closed 取舍。
# 设计约束 19：本 gate 不更新 Robot/mobile/OKR/sprint closeout 文件。
# 设计约束 20：状态名保持 snake_case，便于 rg 和下游解析。
# 设计约束 21：owner intake schema 只用于本地约定，不代表现场来源可信。
# 设计约束 22：accepted_material_refs 只列安全类别名，不复制完整材料。
# 设计约束 23：rejected_materials 优先视为 unsafe，防止坏材料进入 ready。
# 设计约束 24：上游 handoff 未 ready 时不能从 owner packet 推导 ready。
# 设计约束 25：最终 artifact 和 summary 都包含 hard boundary flags。

RAW_OR_EXTERNAL_CLAIM_PATTERNS = (
    re.compile(r"(?i)\braw\s+artifact(s)?\b"),
    re.compile(r"(?i)\bcomplete\s+artifact(s)?\b"),
    re.compile(r"(?i)\braw\s+ros\s+topic(s)?\b"),
    re.compile(r"(?i)\btrue\s+phone/browser\s+proof\b"),
    re.compile(r"(?i)\breal\s+phone/browser\s+proof\b"),
    re.compile(r"(?i)\breal\s+route/elevator\s+field\s+pass\b"),
    re.compile(r"(?i)\broute/elevator\s+field\s+pass\b"),
    re.compile(r"(?i)\bverified\s+terminal\s+result\b"),
    re.compile(r"(?i)\bobjective\s*5\s+external\s+proof\b"),
    re.compile(r"(?i)\bo5\s+external\s+proof\b"),
    re.compile(r"(?i)\bexternal\s+proof\b"),
    re.compile(r"(?i)\breal\s+hil\b"),
    re.compile(r"(?i)\bhil\s+(pass|passed|complete|completed|verified)\b"),
    re.compile(r"(?i)\bpr\s*#?5\s+(reviewer\s+)?(resolved|resolution|closed)\b"),
    re.compile(r"(?i)\bdropoff\s+(complete|completed|success|succeeded|verified)\b"),
    re.compile(r"(?i)\bcancel\s+(complete|completed|success|succeeded|verified)\b"),
)


def _utc_now() -> str:
    # UTC 字符串方便不同 Docker/PC 主机按文本排序审计。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 输入异常也生成 fail-closed artifact，避免证据链路静默中断。
    if not path:
        return {}, f"{label}_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, f"{label}_json_missing"
    except json.JSONDecodeError:
        return {}, f"{label}_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, f"{label}_json_read_error"
    if not isinstance(payload, dict):
        return {}, f"{label}_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # wrapper 字段必须是 object；字符串化 JSON 不作为可信 safe alias。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 Robot alias 字段位置可能不同。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 64) -> list[str]:
    # 输出清单只保留短字符串，避免复制完整上游 nested artifact。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                text = _first_text(item.get("name"), item.get("material"), item.get("id"), item.get("ref"), default="")
            else:
                text = _first_text(item, default="")
            if text:
                items.append(material_pack._safe_text(text))
        return items
    if isinstance(value, dict):
        return [material_pack._safe_text(key) for key, item in value.items() if bool(item)]
    if value in (None, ""):
        return []
    return [material_pack._safe_text(value)]


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归已知 safe wrapper key，避免 raw diagnostics 或 material body 混入。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_acceptance_review_handoff",
        "field_evidence_rerun_execution_result_acceptance_review_handoff_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary",
        "acceptance_review_handoff",
        "acceptance_review_handoff_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
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
    # schema 命中时优先返回嵌套对象；否则保留顶层用于 blocked 诊断。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _owner_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # owner/support packet 只从固定 wrapper key 递归，避免 raw callback body 被误采信。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_acceptance_handoff_owner_intake",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake",
        "owner_intake",
        "owner_support_packet",
        "field_owner_support_packet",
        "owner_acknowledgement",
        "support_packet",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_owner_candidates(value))
    return candidates


def _find_owner_packet(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中优先；没有 schema 时使用顶层，便于现场 owner 提交最小 JSON。
    for candidate in _owner_candidates(payload):
        schema = str(candidate.get("schema", "")).strip()
        if schema in {OWNER_INTAKE_SCHEMA, INTAKE_SCHEMA, INTAKE_SUMMARY_SCHEMA}:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, Any]:
    # schema 和 boundary 必须同时白名单化，不能跨 gate 消费。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 可来自顶层、safe_copy、owner_handoff 或下游只读摘要。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    owner_handoff = _dict(source, "owner_handoff")
    return material_pack._safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            owner_handoff.get("safe_evidence_ref"),
            owner_handoff.get("evidence_ref"),
            default="",
        )
    )


def _source_handoff_status(source: dict[str, Any]) -> str:
    # 上游 ready handoff 是进入 owner intake 的必要条件，不能从材料数量推断。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            source.get("handoff_status"),
            source.get("status"),
            robot.get("handoff_status"),
            robot.get("status"),
            mobile.get("handoff_status"),
            mobile.get("status"),
            safe_copy.get("handoff_status"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _same_ref_required(source: dict[str, Any], owner_packet: dict[str, Any]) -> Any:
    # 两侧都必须保持 JSON boolean true；字符串 true 会在多语言端产生歧义。
    source_safe = _dict(source, "safe_copy")
    owner_safe = _dict(owner_packet, "safe_copy")
    source_value = source.get("same_evidence_ref_required", source_safe.get("same_evidence_ref_required", True))
    owner_value = owner_packet.get("same_evidence_ref_required", owner_safe.get("same_evidence_ref_required", True))
    return source_value if source_value is not True else owner_value


def _source_is_safe(source: dict[str, Any]) -> bool:
    # software_proof、not_proven 和三个 false flag 是 handoff 的最低安全边界。
    encoded = material_pack._encoded(source)
    return (
        source.get("source") == "software_proof"
        and "not_proven" in encoded
        and source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _owner_is_safe(owner_packet: dict[str, Any]) -> bool:
    # owner packet 也必须显式 fail-closed，避免现场回执绕过边界。
    encoded = material_pack._encoded(owner_packet)
    return (
        owner_packet.get("source") == "software_proof"
        and "not_proven" in encoded
        and owner_packet.get("safe_to_control") is False
        and owner_packet.get("delivery_success") is False
        and owner_packet.get("primary_actions_enabled") is False
    )


def _owner_evidence_ref(owner_packet: dict[str, Any]) -> str:
    # owner/support packet 的 evidence_ref 可以在 safe_copy 内部，最终仍脱敏为 safe ref。
    safe_copy = _dict(owner_packet, "safe_copy")
    return material_pack._safe_ref(
        _first_text(
            owner_packet.get("safe_evidence_ref"),
            owner_packet.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _has_true_control_flag(value: Any) -> bool:
    # JSON boolean true 比自由文本更危险，必须递归阻断。
    if isinstance(value, dict):
        if value.get("safe_to_control") is True or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
        return any(_has_true_control_flag(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_true_control_flag(item) for item in value)
    return False


def _has_forbidden_proof_claim(value: Any) -> bool:
    # 额外阻断高风险自由文本；checklist 类别名本身仍允许出现在输出中。
    encoded = material_pack._encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_OR_EXTERNAL_CLAIM_PATTERNS)


def _material_key(value: str) -> str:
    # 大小写、空白、短横线和下划线不应影响 checklist 类别匹配。
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _owner_material_status(owner_packet: dict[str, Any]) -> dict[str, Any]:
    # owner packet 可以用几种安全字段表达同一 checklist acknowledgement。
    safe_copy = _dict(owner_packet, "safe_copy")
    acknowledged = []
    for key in (
        "acknowledged_materials",
        "accepted_materials",
        "accepted_material_refs",
        "safe_material_refs",
        "required_materials_acknowledged",
        "owner_intake_materials",
        "handoff_checklist_acknowledged",
    ):
        acknowledged.extend(_safe_list(owner_packet.get(key) or safe_copy.get(key)))
    checklist = owner_packet.get("handoff_checklist") or safe_copy.get("handoff_checklist")
    if isinstance(checklist, list):
        for item in checklist:
            if isinstance(item, dict) and item.get("status") in {"accepted", "acknowledged", "provided_not_proven", "ready_not_proven"}:
                acknowledged.extend(_safe_list(item))
    accepted_keys = {_material_key(item) for item in acknowledged}
    required_keys = {_material_key(item): item for item in REQUIRED_OWNER_INTAKE_MATERIALS}
    accepted_required = [required for key, required in required_keys.items() if key in accepted_keys]
    missing = [required for key, required in required_keys.items() if key not in accepted_keys]
    rejected = _safe_list(owner_packet.get("rejected_materials") or safe_copy.get("rejected_materials") or owner_packet.get("unsafe_material_refs"))
    return {
        "status": "accepted" if not missing and not rejected else ("rejected" if rejected else "missing"),
        "required_materials": list(REQUIRED_OWNER_INTAKE_MATERIALS),
        "accepted_materials": accepted_required,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "accepted_count": len(accepted_required),
        "required_count": len(REQUIRED_OWNER_INTAKE_MATERIALS),
        "is_complete": not missing and not rejected and len(accepted_required) == len(REQUIRED_OWNER_INTAKE_MATERIALS),
    }


def _source_lineage(source: dict[str, Any], owner_packet: dict[str, Any]) -> dict[str, str]:
    # lineage 只复制短字段，避免复制完整上游 artifact 或 owner packet。
    lineage = {
        "source_review_handoff_schema": material_pack._safe_text(source.get("schema", "")),
        "source_review_handoff_status": _source_handoff_status(source),
        "owner_intake_schema": material_pack._safe_text(owner_packet.get("schema", "")),
    }
    safe_lineage = source.get("safe_lineage")
    if isinstance(safe_lineage, dict):
        for key, value in safe_lineage.items():
            text = material_pack._safe_text(value)
            if text:
                lineage[f"review_handoff_{material_pack._safe_text(key)}"] = text
    return lineage


def _intake_decision(
    review_load_issue: str,
    owner_load_issue: str,
    source_state: dict[str, Any],
    source_handoff_status: str,
    requested_ref: str,
    source_ref: str,
    owner_ref: str,
    same_ref_required: Any,
    source_safe: bool,
    owner_safe: bool,
    unsafe_source_or_owner: bool,
    success_or_control_claim: bool,
    material_status: dict[str, Any],
) -> tuple[str, list[str], int]:
    # fail-closed 顺序固定：输入可信性和安全边界优先于材料缺口。
    if review_load_issue:
        return BLOCKED_MISSING_REVIEW_HANDOFF, [review_load_issue], 2
    if source_state["schema_status"] != "supported":
        return BLOCKED_MISSING_REVIEW_HANDOFF, ["unsupported_review_handoff_schema_or_boundary"], 2
    if owner_load_issue:
        return INTAKE_NEEDS_MORE_MATERIAL, [owner_load_issue], 3
    if not (requested_ref or source_ref or owner_ref):
        return BLOCKED_MISSING_REVIEW_HANDOFF, ["missing_safe_evidence_ref"], 2
    refs = [ref for ref in (requested_ref, source_ref, owner_ref) if ref]
    if len(set(refs)) > 1:
        return INTAKE_EVIDENCE_REF_MISMATCH, ["requested_source_owner_evidence_ref_mismatch"], 4
    if same_ref_required is not True:
        return INTAKE_EVIDENCE_REF_MISMATCH, ["same_evidence_ref_required_not_boolean_true"], 4
    if not source_safe:
        return INTAKE_UNSAFE_REJECTED, ["source_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if not owner_safe:
        return INTAKE_UNSAFE_REJECTED, ["owner_packet_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if unsafe_source_or_owner:
        return INTAKE_UNSAFE_REJECTED, ["unsafe_or_raw_copy_detected"], 5
    if success_or_control_claim:
        return INTAKE_UNSAFE_REJECTED, ["success_or_control_or_forbidden_proof_claim_detected"], 5
    if source_handoff_status != READY_SOURCE_HANDOFF:
        return INTAKE_NEEDS_MORE_MATERIAL, ["review_handoff_not_ready_for_owner_intake"], 3
    if material_status["rejected_materials"]:
        return INTAKE_UNSAFE_REJECTED, ["owner_packet_contains_rejected_or_unsafe_material_refs"], 5
    if material_status["missing_materials"] or not material_status["is_complete"]:
        return INTAKE_NEEDS_MORE_MATERIAL, ["owner_intake_missing_required_material_acknowledgement"], 3
    return READY_INTAKE, ["review_handoff_and_owner_support_intake_ready_not_proven"], 0


def _intake_checklist(evidence_ref: str, material_status: dict[str, Any]) -> list[dict[str, Any]]:
    # checklist 明确 intake 对每类材料的状态，但仍不验证真实材料正文。
    accepted = set(material_status["accepted_materials"])
    rejected = set(material_status["rejected_materials"])
    checklist = []
    for item in REQUIRED_OWNER_INTAKE_MATERIALS:
        status = "accepted_not_proven" if item in accepted else "missing_not_proven"
        if item in rejected:
            status = "rejected_unsafe"
        checklist.append(
            {
                "name": item,
                "evidence_ref": evidence_ref or "<same_evidence_ref>",
                "required_for_real_acceptance": True,
                "status": status,
            }
        )
    return checklist


def _next_required_evidence(state: str, evidence_ref: str, material_status: dict[str, Any], reasons: list[str]) -> list[str]:
    # next evidence 是 owner/support 补证清单，不是机器人动作指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if state == READY_INTAKE:
        return [
            f"handoff owner/support intake for evidence_ref={ref} to Product closeout without enabling controls",
            "keep collecting true task record, true Nav2/fixed-route runtime log, route completion signal, elevator/floor/human assistance evidence, dropoff/cancel or delivery result, and true phone/browser evidence as real materials outside this gate",
            "keep Robot/mobile primary actions disabled until real reviewed material exists",
        ]
    if state == INTAKE_NEEDS_MORE_MATERIAL:
        required = [f"provide safe owner/support acknowledgement for material: {name} at evidence_ref={ref}" for name in material_status["missing_materials"]]
        return required or [f"rerun owner/support intake packet after previous handoff emits {READY_SOURCE_HANDOFF} for evidence_ref={ref}", *reasons]
    if state == INTAKE_EVIDENCE_REF_MISMATCH:
        return [f"rerun acceptance review handoff and owner/support packet so all summaries share evidence_ref={ref}"]
    if state == INTAKE_UNSAFE_REJECTED:
        return ["remove unsafe/raw/success/control/external-proof/HIL/verified-terminal/PR-resolution claims and rerun the PC-only intake gate"]
    return [f"provide supported acceptance review handoff artifact or summary for evidence_ref={ref}", *reasons]


def _owner_intake(state: str, evidence_ref: str, checklist: list[dict[str, Any]], next_required_evidence: list[str]) -> dict[str, Any]:
    # owner_intake 只授权人工复核和补证，不给 Robot/mobile 开控制权限。
    return {
        "primary_owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "intake_status": state,
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "evidence_ref": evidence_ref or "<same_evidence_ref>",
        "intake_checklist": checklist,
        "next_required_evidence": next_required_evidence,
        "reviewer_boundary": "owner_support_intake_only_not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC evidence gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_review_handoff.py --review-decision-json <review_decision.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake.py --review-handoff-json <review_handoff.json> --owner-intake-json <owner_intake.json> --evidence-ref {ref}",
        "keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false",
    ]


def _safe_copy(
    state: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    owner_summary: dict[str, Any],
    lineage: dict[str, str],
    material_status: dict[str, Any],
    checklist: list[dict[str, Any]],
    reasons: list[str],
    owner_intake: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或本机路径。
    return {
        "schema": f"{INTAKE_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": state,
        "intake_status": state,
        "allowed_intake_states": list(ALLOWED_INTAKE_STATES),
        "intake_reasons": reasons,
        "evidence_boundary": INTAKE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review_handoff": source_summary,
        "owner_support_packet": owner_summary,
        "safe_lineage": lineage,
        "material_status": material_status,
        "intake_checklist": checklist,
        "owner_intake": owner_intake,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    state: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    owner_summary: dict[str, Any],
    lineage: dict[str, str],
    material_status: dict[str, Any],
    checklist: list[dict[str, Any]],
    reasons: list[str],
    owner_intake: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是跨 Robot/Full-stack 的只读对接面，字段稳定且默认 fail-closed。
    return {
        "schema": INTAKE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": state,
        "intake_status": state,
        "allowed_intake_states": list(ALLOWED_INTAKE_STATES),
        "intake_reasons": reasons,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review_handoff": source_summary,
        "owner_support_packet": owner_summary,
        "safe_lineage": lineage,
        "required_materials": list(REQUIRED_OWNER_INTAKE_MATERIALS),
        "material_status": material_status,
        "intake_checklist": checklist,
        "owner_intake": owner_intake,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_result_acceptance_handoff_intake(
    review_handoff_json: str,
    owner_intake_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 review handoff 与 owner/support packet，生成 fail-closed intake。"""
    review_payload, review_load_issue = _load_json(review_handoff_json, "review_handoff")
    owner_payload, owner_load_issue = _load_json(owner_intake_json, "owner_intake")
    source = _find_source(review_payload) if review_payload else {}
    owner_packet = _find_owner_packet(owner_payload) if owner_payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref)
    source_ref = _source_evidence_ref(source)
    owner_ref = _owner_evidence_ref(owner_packet)
    effective_ref = requested_ref or source_ref or owner_ref
    source_state = _source_status(review_load_issue, source)
    source_handoff_status = _source_handoff_status(source) if source else "missing"
    same_ref_required = _same_ref_required(source, owner_packet) if (source or owner_packet) else True
    source_safe = bool(source) and _source_is_safe(source)
    owner_safe = bool(owner_packet) and _owner_is_safe(owner_packet)
    unsafe_source_or_owner = bool(review_payload or owner_payload) and (
        material_pack._has_forbidden_copy(source)
        or material_pack._has_raw_path_copy(source)
        or material_pack._has_forbidden_copy(owner_packet)
        or material_pack._has_raw_path_copy(owner_packet)
    )
    success_or_control_claim = bool(review_payload or owner_payload) and (
        material_pack._has_success_or_control_claim(source)
        or material_pack._has_success_or_control_claim(owner_packet)
        or _has_true_control_flag(source)
        or _has_true_control_flag(owner_packet)
        or _has_forbidden_proof_claim(source)
        or _has_forbidden_proof_claim(owner_packet)
    )
    material_status = _owner_material_status(owner_packet) if owner_packet else {
        "status": "missing",
        "required_materials": list(REQUIRED_OWNER_INTAKE_MATERIALS),
        "accepted_materials": [],
        "missing_materials": list(REQUIRED_OWNER_INTAKE_MATERIALS),
        "rejected_materials": [],
        "accepted_count": 0,
        "required_count": len(REQUIRED_OWNER_INTAKE_MATERIALS),
        "is_complete": False,
    }

    state, reasons, exit_code = _intake_decision(
        review_load_issue,
        owner_load_issue,
        source_state,
        source_handoff_status,
        requested_ref,
        source_ref,
        owner_ref,
        same_ref_required,
        source_safe,
        owner_safe,
        unsafe_source_or_owner,
        success_or_control_claim,
        material_status,
    )
    lineage = _source_lineage(source, owner_packet)
    checklist = _intake_checklist(effective_ref, material_status)
    next_required_evidence = _next_required_evidence(state, effective_ref, material_status, reasons)
    owner_intake = _owner_intake(state, effective_ref, checklist, next_required_evidence)
    rerun_commands = _rerun_commands(effective_ref)
    source_summary = {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "handoff_status": source_handoff_status,
        "status": source_handoff_status,
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "source_is_software_proof_not_proven": bool(source_safe),
    }
    owner_summary = {
        "load_status": "blocked" if owner_load_issue else "loaded",
        "load_issue": owner_load_issue,
        "schema": material_pack._safe_text(owner_packet.get("schema", "")),
        "source": material_pack._safe_text(owner_packet.get("source", "")),
        "safe_evidence_ref": owner_ref,
        "evidence_ref": owner_ref,
        "owner_packet_is_software_proof_not_proven": bool(owner_safe),
        "unsafe_copy": bool(unsafe_source_or_owner),
        "success_or_control_claim": bool(success_or_control_claim),
    }
    safe_copy = _safe_copy(
        state,
        effective_ref,
        source_summary,
        owner_summary,
        lineage,
        material_status,
        checklist,
        reasons,
        owner_intake,
        next_required_evidence,
        rerun_commands,
    )
    summary = _summary_payload(
        state,
        effective_ref,
        source_summary,
        owner_summary,
        lineage,
        material_status,
        checklist,
        reasons,
        owner_intake,
        next_required_evidence,
        rerun_commands,
        safe_copy,
    )
    artifact = {
        "schema": INTAKE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": state,
        "intake_status": state,
        "allowed_intake_states": list(ALLOWED_INTAKE_STATES),
        "intake_reasons": reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "source_review_handoff": source_summary,
        "owner_support_packet": owner_summary,
        "safe_lineage": lineage,
        "required_materials": list(REQUIRED_OWNER_INTAKE_MATERIALS),
        "material_status": material_status,
        "intake_checklist": checklist,
        "owner_intake": owner_intake,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "raw_task_record",
            "raw_nav2_runtime_log",
            "raw_fixed_route_runtime_log",
            "raw_route_completion_signal",
            "raw_elevator_door_state",
            "raw_target_floor_confirmation",
            "raw_human_assistance_record",
            "raw_dropoff_cancel_material",
            "raw_delivery_result",
            "raw_true_phone_browser_evidence",
            "raw_diagnostics",
            "material_dir_scan",
            "ros_graph",
            "real_elevator",
            "external_cloud",
            "real_phone_or_browser",
            "robot_action",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if material_pack._has_forbidden_copy(artifact) or material_pack._has_forbidden_copy(summary):
        # 最终防线：输出仍含禁词时强制降级，且不改变 fail-closed flags。
        artifact["status"] = INTAKE_UNSAFE_REJECTED
        artifact["intake_status"] = INTAKE_UNSAFE_REJECTED
        artifact["robot_diagnostics_summary"]["status"] = INTAKE_UNSAFE_REJECTED
        artifact["robot_diagnostics_summary"]["intake_status"] = INTAKE_UNSAFE_REJECTED
        artifact["mobile_readonly_summary"]["status"] = INTAKE_UNSAFE_REJECTED
        artifact["mobile_readonly_summary"]["intake_status"] = INTAKE_UNSAFE_REJECTED
        summary["status"] = INTAKE_UNSAFE_REJECTED
        summary["intake_status"] = INTAKE_UNSAFE_REJECTED
        exit_code = 5
    return artifact, summary, exit_code


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；未指定时由 CLI 打印到 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，方便 PC、Docker 和 focused unittest 共用。
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun acceptance handoff intake artifact")
    parser.add_argument("--review-handoff-json", required=True, help="acceptance review handoff artifact, summary, or wrapper JSON")
    parser.add_argument("--owner-intake-json", required=True, help="owner/support safe intake packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this intake gate")
    parser.add_argument("--output", default="", help="optional intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_acceptance_handoff_intake(
        args.review_handoff_json,
        args.owner_intake_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_acceptance_handoff_intake: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_handoff_intake_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"intake_status: {artifact['intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
