#!/usr/bin/env python3
"""生成 acceptance handoff intake review-handoff。

该 PC-only gate 接在
`field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision`
之后，只读取上一轮 review-decision artifact / summary / Robot diagnostics safe
alias 或 wrapper/nested JSON，并读取 field owner/support/reviewer 的 safe handoff
packet。输出只表示 review-decision metadata 可交给下一步人工复核交接，不读取真实
ROS/Nav2 runtime、硬件、真实电梯、外部云、真实手机/browser 或 raw artifact，也不
触发机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision as review_decision
import route_task_field_retest_material_pack as material_pack


HANDOFF_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff.v1"
HANDOFF_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary.v1"
HANDOFF_PACKET_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_support_reviewer_handoff_packet.v1"
SCHEMA_VERSION = 1
HANDOFF_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate"

# 上游必须是上一轮 handoff-intake review-decision，不能跳过人工复核决策阶段。
SOURCE_SCHEMAS = {review_decision.DECISION_SCHEMA, review_decision.DECISION_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {review_decision.DECISION_BOUNDARY}
READY_SOURCE_DECISION = review_decision.READY_DECISION

READY_HANDOFF = "ready_for_acceptance_review_handoff_not_proven"
HANDOFF_NEEDS_OWNER_REWORK = "handoff_needs_owner_rework"
HANDOFF_EVIDENCE_REF_MISMATCH = "handoff_evidence_ref_mismatch"
HANDOFF_UNSAFE_REJECTED = "handoff_unsafe_rejected"
BLOCKED_MISSING_REVIEW_DECISION = "blocked_missing_review_decision"
ALLOWED_HANDOFF_STATES = (
    READY_HANDOFF,
    HANDOFF_NEEDS_OWNER_REWORK,
    HANDOFF_EVIDENCE_REF_MISMATCH,
    HANDOFF_UNSAFE_REJECTED,
    BLOCKED_MISSING_REVIEW_DECISION,
)

# checklist 只是后续真实验收材料名，本 gate 不读取这些材料正文。
HANDOFF_CHECKLIST = review_decision.REQUIRED_REVIEW_MATERIALS
NOT_PROVEN = review_decision.NOT_PROVEN

# rg 围栏依赖这些 literal；同时给人工复核一个压缩边界说明。
BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate; "
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_gate; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false; "
    "ready_for_acceptance_review_handoff_not_proven; handoff_needs_owner_rework; "
    "handoff_evidence_ref_mismatch; handoff_unsafe_rejected; blocked_missing_review_decision"
)

# 设计约束 01：本 gate 只消费上一轮 review-decision safe output。
# 设计约束 02：handoff packet 只能是脱敏 checklist metadata，不读取 raw material。
# 设计约束 03：ready 只表示可交给 owner/support/reviewer，不证明现场材料为真。
# 设计约束 04：source=software_proof 与 not_proven 必须跨 gate 延续。
# 设计约束 05：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 06：same evidence_ref 是现场复账主键，不一致必须 fail closed。
# 设计约束 07：弱类型 same_evidence_ref_required 不能通过，必须是 JSON boolean true。
# 设计约束 08：handoff packet 只接受 checklist 类别确认，不接受成功或控制文案。
# 设计约束 09：缺任一 handoff 类别只能进入 owner rework。
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
# 设计约束 21：accepted_material_refs 只列安全类别名，不复制完整材料。
# 设计约束 22：rejected_materials 优先视为 unsafe，防止坏材料进入 ready。
# 设计约束 23：上游 review decision 未 ready 时不能从 packet 推导 ready。
# 设计约束 24：最终 artifact 和 summary 都包含 hard boundary flags。

FORBIDDEN_PROOF_CLAIM_PATTERNS = (
    re.compile(r"(?i)\braw\s+artifact(s)?\b"),
    re.compile(r"(?i)\bcomplete\s+artifact(s)?\b"),
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
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary",
        "acceptance_handoff_intake_review_decision",
        "acceptance_handoff_intake_review_decision_summary",
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


def _packet_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # handoff packet 只从固定 wrapper key 递归，避免 raw callback body 被误采信。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_packet",
        "owner_support_reviewer_handoff_packet",
        "review_handoff_packet",
        "handoff_packet",
        "owner_handoff_packet",
        "support_handoff_packet",
        "reviewer_handoff_packet",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_packet_candidates(value))
    return candidates


def _find_packet(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中优先；没有 schema 时使用顶层，便于现场 owner 提交最小 JSON。
    for candidate in _packet_candidates(payload):
        if str(candidate.get("schema", "")).strip() == HANDOFF_PACKET_SCHEMA:
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


def _packet_evidence_ref(packet: dict[str, Any]) -> str:
    # handoff packet 的 evidence_ref 可以在 safe_copy 内部，最终仍脱敏为 safe ref。
    safe_copy = _dict(packet, "safe_copy")
    return material_pack._safe_ref(
        _first_text(
            packet.get("safe_evidence_ref"),
            packet.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _source_review_decision(source: dict[str, Any]) -> str:
    # 上游 ready decision 是进入 handoff 的必要条件，不能从 packet 推断。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            source.get("review_decision"),
            source.get("status"),
            robot.get("review_decision"),
            robot.get("status"),
            mobile.get("review_decision"),
            mobile.get("status"),
            safe_copy.get("review_decision"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _same_ref_required(source: dict[str, Any], packet: dict[str, Any]) -> Any:
    # 两侧都必须保持 JSON boolean true；字符串 true 会在多语言端产生歧义。
    source_safe = _dict(source, "safe_copy")
    packet_safe = _dict(packet, "safe_copy")
    source_value = source.get("same_evidence_ref_required", source_safe.get("same_evidence_ref_required", True))
    packet_value = packet.get("same_evidence_ref_required", packet_safe.get("same_evidence_ref_required", True))
    return source_value if source_value is not True else packet_value


def _source_is_safe(source: dict[str, Any]) -> bool:
    # software_proof、not_proven 和三个 false flag 是 source 的最低安全边界。
    encoded = material_pack._encoded(source)
    return (
        source.get("source") == "software_proof"
        and "not_proven" in encoded
        and source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _packet_is_safe(packet: dict[str, Any]) -> bool:
    # handoff packet 也必须显式 fail-closed，避免人工交接绕过边界。
    encoded = material_pack._encoded(packet)
    return (
        packet.get("source") == "software_proof"
        and "not_proven" in encoded
        and packet.get("safe_to_control") is False
        and packet.get("delivery_success") is False
        and packet.get("primary_actions_enabled") is False
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
    return any(pattern.search(encoded) for pattern in FORBIDDEN_PROOF_CLAIM_PATTERNS)


def _material_key(value: str) -> str:
    # 大小写、空白、短横线和下划线不应影响 checklist 类别匹配。
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _packet_material_status(packet: dict[str, Any]) -> dict[str, Any]:
    # packet 可以用几种安全字段表达同一 owner/support/reviewer handoff。
    safe_copy = _dict(packet, "safe_copy")
    accepted = []
    for key in (
        "accepted_materials",
        "accepted_material_refs",
        "handoff_materials",
        "handoff_material_refs",
        "safe_material_refs",
        "review_handoff_checklist_accepted",
        "owner_support_reviewer_handoff_materials",
    ):
        accepted.extend(_safe_list(packet.get(key) or safe_copy.get(key)))
    checklist = packet.get("handoff_checklist") or packet.get("review_handoff_checklist") or safe_copy.get("handoff_checklist")
    if isinstance(checklist, list):
        for item in checklist:
            if isinstance(item, dict) and item.get("status") in {"accepted", "reviewed", "accepted_not_proven", "ready_not_proven", "handoff_ready_not_proven"}:
                accepted.extend(_safe_list(item))
    accepted_keys = {_material_key(item) for item in accepted}
    required_keys = {_material_key(item): item for item in HANDOFF_CHECKLIST}
    accepted_required = [required for key, required in required_keys.items() if key in accepted_keys]
    missing = _safe_list(packet.get("missing_materials") or safe_copy.get("missing_materials"))
    if not missing:
        missing = [required for key, required in required_keys.items() if key not in accepted_keys]
    rejected = _safe_list(packet.get("rejected_materials") or safe_copy.get("rejected_materials") or packet.get("unsafe_material_refs"))
    rework = _safe_list(packet.get("rework_reasons") or safe_copy.get("rework_reasons") or packet.get("owner_rework_reasons"))
    return {
        "status": "accepted" if not missing and not rejected and not rework else ("rejected" if rejected else "missing"),
        "required_materials": list(HANDOFF_CHECKLIST),
        "accepted_materials": accepted_required,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "owner_rework_reasons": rework,
        "accepted_count": len(accepted_required),
        "required_count": len(HANDOFF_CHECKLIST),
        "is_complete": not missing and not rejected and not rework and len(accepted_required) == len(HANDOFF_CHECKLIST),
    }


def _packet_status(packet: dict[str, Any]) -> str:
    # 显式 packet 状态可让 owner/support/reviewer 主动要求 rework；不能覆盖 unsafe 检查。
    safe_copy = _dict(packet, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            packet.get("handoff_status"),
            packet.get("review_handoff_status"),
            packet.get("status"),
            safe_copy.get("handoff_status"),
            safe_copy.get("review_handoff_status"),
            safe_copy.get("status"),
            default="ready_not_proven",
        )
    )


def _source_lineage(source: dict[str, Any], packet: dict[str, Any]) -> dict[str, str]:
    # lineage 只复制短字段，避免复制完整上游 artifact 或 handoff packet。
    lineage = {
        "source_review_decision_schema": material_pack._safe_text(source.get("schema", "")),
        "source_review_decision_status": _source_review_decision(source),
        "owner_support_reviewer_handoff_packet_schema": material_pack._safe_text(packet.get("schema", "")),
    }
    safe_lineage = source.get("safe_lineage")
    if isinstance(safe_lineage, dict):
        for key, value in safe_lineage.items():
            text = material_pack._safe_text(value)
            if text:
                lineage[f"review_decision_{material_pack._safe_text(key)}"] = text
    return lineage


def _handoff_decision(
    source_load_issue: str,
    packet_load_issue: str,
    source_state: dict[str, Any],
    source_review_status: str,
    packet_status: str,
    requested_ref: str,
    source_ref: str,
    packet_ref: str,
    same_ref_required: Any,
    source_safe: bool,
    packet_safe: bool,
    unsafe_source_or_packet: bool,
    success_or_control_claim: bool,
    material_status: dict[str, Any],
) -> tuple[str, list[str], int]:
    # fail-closed 顺序固定：输入可信性和安全边界优先于材料缺口。
    if source_load_issue:
        return BLOCKED_MISSING_REVIEW_DECISION, [source_load_issue], 2
    if source_state["schema_status"] != "supported":
        return BLOCKED_MISSING_REVIEW_DECISION, ["unsupported_review_decision_schema_or_boundary"], 2
    if packet_load_issue:
        return HANDOFF_NEEDS_OWNER_REWORK, [packet_load_issue], 3
    if not (requested_ref or source_ref or packet_ref):
        return BLOCKED_MISSING_REVIEW_DECISION, ["missing_safe_evidence_ref"], 2
    refs = [ref for ref in (requested_ref, source_ref, packet_ref) if ref]
    if len(set(refs)) > 1:
        return HANDOFF_EVIDENCE_REF_MISMATCH, ["requested_source_handoff_evidence_ref_mismatch"], 4
    if same_ref_required is not True:
        return HANDOFF_EVIDENCE_REF_MISMATCH, ["same_evidence_ref_required_not_boolean_true"], 4
    if not source_safe:
        return HANDOFF_UNSAFE_REJECTED, ["source_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if not packet_safe:
        return HANDOFF_UNSAFE_REJECTED, ["handoff_packet_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if unsafe_source_or_packet:
        return HANDOFF_UNSAFE_REJECTED, ["unsafe_or_raw_copy_detected"], 5
    if success_or_control_claim:
        return HANDOFF_UNSAFE_REJECTED, ["success_or_control_or_forbidden_proof_claim_detected"], 5
    if source_review_status != READY_SOURCE_DECISION:
        return HANDOFF_NEEDS_OWNER_REWORK, ["review_decision_not_ready_for_review_handoff"], 3
    if packet_status in {"unsafe", "rejected", "handoff_unsafe_rejected", "review_unsafe_rejected"}:
        return HANDOFF_UNSAFE_REJECTED, ["owner_support_reviewer_handoff_packet_rejected_unsafe"], 5
    if packet_status in {"needs_rework", "missing", "handoff_needs_owner_rework", "review_needs_owner_rework"}:
        return HANDOFF_NEEDS_OWNER_REWORK, ["owner_support_reviewer_handoff_packet_requests_rework"], 3
    if material_status["rejected_materials"]:
        return HANDOFF_UNSAFE_REJECTED, ["handoff_packet_contains_rejected_or_unsafe_material_refs"], 5
    if material_status["missing_materials"] or material_status["owner_rework_reasons"] or not material_status["is_complete"]:
        return HANDOFF_NEEDS_OWNER_REWORK, ["handoff_packet_missing_required_review_handoff_material"], 3
    return READY_HANDOFF, ["review_decision_and_owner_support_reviewer_handoff_packet_ready_not_proven"], 0


def _handoff_checklist(evidence_ref: str, material_status: dict[str, Any]) -> list[dict[str, Any]]:
    # checklist 明确 handoff 对每类材料的状态，但仍不验证真实材料正文。
    accepted = set(material_status["accepted_materials"])
    rejected = set(material_status["rejected_materials"])
    checklist = []
    for item in HANDOFF_CHECKLIST:
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
    # next evidence 是 owner/support/reviewer 补证清单，不是机器人动作指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if state == READY_HANDOFF:
        return [
            f"handoff review-handoff packet for evidence_ref={ref} to field owner/support/reviewer without enabling controls",
            "keep collecting true task record, true Nav2/fixed-route runtime log, route completion signal, elevator/floor/human assistance evidence, dropoff/cancel or delivery result, and true phone/browser evidence as real materials outside this gate",
            "keep Robot/mobile primary actions disabled until real reviewed material exists",
        ]
    if state == HANDOFF_NEEDS_OWNER_REWORK:
        required = [f"handoff or rework safe material: {name} at evidence_ref={ref}" for name in material_status["missing_materials"]]
        required.extend([f"resolve owner rework reason: {reason}" for reason in material_status["owner_rework_reasons"]])
        return required or [f"rerun owner/support/reviewer handoff packet after previous review decision emits {READY_SOURCE_DECISION} for evidence_ref={ref}", *reasons]
    if state == HANDOFF_EVIDENCE_REF_MISMATCH:
        return [f"rerun review decision and handoff packet so all summaries share evidence_ref={ref}"]
    if state == HANDOFF_UNSAFE_REJECTED:
        return ["remove unsafe/raw/success/control/external-proof/HIL/verified-terminal/PR-resolution claims and rerun the PC-only review-handoff gate"]
    return [f"provide supported acceptance handoff intake review-decision artifact or summary for evidence_ref={ref}", *reasons]


def _owner_handoff(state: str, evidence_ref: str, checklist: list[dict[str, Any]], next_required_evidence: list[str]) -> dict[str, Any]:
    # owner_handoff 只授权人工复核和补证，不给 Robot/mobile 开控制权限。
    return {
        "primary_owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "handoff_status": state,
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "evidence_ref": evidence_ref or "<same_evidence_ref>",
        "handoff_checklist": checklist,
        "next_required_evidence": next_required_evidence,
        "reviewer_boundary": "acceptance_handoff_intake_review_handoff_only_not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC evidence gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision.py --handoff-intake-json <handoff_intake.json> --review-packet-json <review_packet.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff.py --review-decision-json <review_decision.json> --handoff-packet-json <handoff_packet.json> --evidence-ref {ref}",
        "keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false",
    ]


def _safe_copy(
    state: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    lineage: dict[str, str],
    material_status: dict[str, Any],
    checklist: list[dict[str, Any]],
    reasons: list[str],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或本机路径。
    return {
        "schema": f"{HANDOFF_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": state,
        "handoff_status": state,
        "allowed_handoff_states": list(ALLOWED_HANDOFF_STATES),
        "handoff_reasons": reasons,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": source_summary,
        "owner_support_reviewer_handoff_packet": packet_summary,
        "safe_lineage": lineage,
        "material_status": material_status,
        "handoff_checklist": checklist,
        "owner_handoff": owner_handoff,
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
    packet_summary: dict[str, Any],
    lineage: dict[str, str],
    material_status: dict[str, Any],
    checklist: list[dict[str, Any]],
    reasons: list[str],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是跨 Robot/Full-stack 的只读对接面，字段稳定且默认 fail-closed。
    return {
        "schema": HANDOFF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": state,
        "handoff_status": state,
        "allowed_handoff_states": list(ALLOWED_HANDOFF_STATES),
        "handoff_reasons": reasons,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": source_summary,
        "owner_support_reviewer_handoff_packet": packet_summary,
        "safe_lineage": lineage,
        "required_materials": list(HANDOFF_CHECKLIST),
        "material_status": material_status,
        "handoff_checklist": checklist,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": _non_access_scope(),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _non_access_scope() -> list[str]:
    # non_access_scope 固定声明本 gate 不碰真实材料、控制链路或外部系统。
    return [
        "raw_task_record",
        "raw_nav2_runtime_log",
        "raw_fixed_route_runtime_log",
        "raw_route_completion_signal",
        "raw_elevator_door_state",
        "raw_target_floor_confirmation",
        "raw_human_assistance_record",
        "raw_dropoff_cancel_completion",
        "raw_delivery_result",
        "raw_true_phone_browser_evidence",
        "raw_diagnostics",
        "material_dir_scan",
        "ros_graph",
        "real_elevator",
        "external_cloud",
        "real_phone_or_browser",
        "verified_terminal_result",
        "pr5_resolution",
        "robot_action",
    ]


def build_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff(
    review_decision_json: str,
    handoff_packet_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 review decision 与 handoff packet，生成 fail-closed review handoff。"""
    source_payload, source_load_issue = _load_json(review_decision_json, "review_decision")
    packet_payload, packet_load_issue = _load_json(handoff_packet_json, "handoff_packet")
    source = _find_source(source_payload) if source_payload else {}
    packet = _find_packet(packet_payload) if packet_payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref)
    source_ref = _source_evidence_ref(source)
    packet_ref = _packet_evidence_ref(packet)
    effective_ref = requested_ref or source_ref or packet_ref
    source_state = _source_status(source_load_issue, source)
    source_review_status = _source_review_decision(source) if source else "missing"
    packet_status = _packet_status(packet) if packet else "missing"
    same_ref_required = _same_ref_required(source, packet) if (source or packet) else True
    source_safe = bool(source) and _source_is_safe(source)
    packet_safe = bool(packet) and _packet_is_safe(packet)
    unsafe_source_or_packet = bool(source_payload or packet_payload) and (
        material_pack._has_forbidden_copy(source)
        or material_pack._has_raw_path_copy(source)
        or material_pack._has_forbidden_copy(packet)
        or material_pack._has_raw_path_copy(packet)
    )
    success_or_control_claim = bool(source_payload or packet_payload) and (
        material_pack._has_success_or_control_claim(source)
        or material_pack._has_success_or_control_claim(packet)
        or _has_true_control_flag(source)
        or _has_true_control_flag(packet)
        or _has_forbidden_proof_claim(source)
        or _has_forbidden_proof_claim(packet)
    )
    material_status = _packet_material_status(packet) if packet else {
        "status": "missing",
        "required_materials": list(HANDOFF_CHECKLIST),
        "accepted_materials": [],
        "missing_materials": list(HANDOFF_CHECKLIST),
        "rejected_materials": [],
        "owner_rework_reasons": [],
        "accepted_count": 0,
        "required_count": len(HANDOFF_CHECKLIST),
        "is_complete": False,
    }

    state, reasons, exit_code = _handoff_decision(
        source_load_issue,
        packet_load_issue,
        source_state,
        source_review_status,
        packet_status,
        requested_ref,
        source_ref,
        packet_ref,
        same_ref_required,
        source_safe,
        packet_safe,
        unsafe_source_or_packet,
        success_or_control_claim,
        material_status,
    )
    lineage = _source_lineage(source, packet)
    checklist = _handoff_checklist(effective_ref, material_status)
    next_required_evidence = _next_required_evidence(state, effective_ref, material_status, reasons)
    owner_handoff = _owner_handoff(state, effective_ref, checklist, next_required_evidence)
    rerun_commands = _rerun_commands(effective_ref)
    source_summary = {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "review_decision": source_review_status,
        "status": source_review_status,
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "source_is_software_proof_not_proven": bool(source_safe),
    }
    packet_summary = {
        "load_status": "blocked" if packet_load_issue else "loaded",
        "load_issue": packet_load_issue,
        "schema": material_pack._safe_text(packet.get("schema", "")),
        "source": material_pack._safe_text(packet.get("source", "")),
        "handoff_packet_status": packet_status,
        "safe_evidence_ref": packet_ref,
        "evidence_ref": packet_ref,
        "handoff_packet_is_software_proof_not_proven": bool(packet_safe),
        "unsafe_copy": bool(unsafe_source_or_packet),
        "success_or_control_claim": bool(success_or_control_claim),
    }
    safe_copy = _safe_copy(
        state,
        effective_ref,
        source_summary,
        packet_summary,
        lineage,
        material_status,
        checklist,
        reasons,
        owner_handoff,
        next_required_evidence,
        rerun_commands,
    )
    summary = _summary_payload(
        state,
        effective_ref,
        source_summary,
        packet_summary,
        lineage,
        material_status,
        checklist,
        reasons,
        owner_handoff,
        next_required_evidence,
        rerun_commands,
        safe_copy,
    )
    artifact = {
        "schema": HANDOFF_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": state,
        "handoff_status": state,
        "allowed_handoff_states": list(ALLOWED_HANDOFF_STATES),
        "handoff_reasons": reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": source_summary,
        "owner_support_reviewer_handoff_packet": packet_summary,
        "safe_lineage": lineage,
        "required_materials": list(HANDOFF_CHECKLIST),
        "material_status": material_status,
        "handoff_checklist": checklist,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": _non_access_scope(),
        "boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if material_pack._has_forbidden_copy(artifact) or material_pack._has_forbidden_copy(summary):
        # 最终防线：输出仍含禁词时强制降级，且不改变 fail-closed flags。
        artifact["status"] = HANDOFF_UNSAFE_REJECTED
        artifact["handoff_status"] = HANDOFF_UNSAFE_REJECTED
        artifact["robot_diagnostics_summary"]["status"] = HANDOFF_UNSAFE_REJECTED
        artifact["robot_diagnostics_summary"]["handoff_status"] = HANDOFF_UNSAFE_REJECTED
        artifact["mobile_readonly_summary"]["status"] = HANDOFF_UNSAFE_REJECTED
        artifact["mobile_readonly_summary"]["handoff_status"] = HANDOFF_UNSAFE_REJECTED
        summary["status"] = HANDOFF_UNSAFE_REJECTED
        summary["handoff_status"] = HANDOFF_UNSAFE_REJECTED
        artifact["field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun acceptance handoff intake review-handoff artifact")
    parser.add_argument("--review-decision-json", required=True, help="acceptance handoff intake review-decision artifact, summary, or wrapper JSON")
    parser.add_argument("--handoff-packet-json", required=True, help="owner/support/reviewer safe handoff packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this review-handoff gate")
    parser.add_argument("--output", default="", help="optional review-handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review-handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review-handoff artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff(
        args.review_decision_json,
        args.handoff_packet_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_handoff_intake_review_handoff_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
