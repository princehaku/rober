#!/usr/bin/env python3
"""生成 field evidence rerun acceptance handoff intake review decision。

该 PC-only gate 接在
`field_evidence_rerun_execution_result_acceptance_handoff_intake` 后面，只读取
上一轮 safe intake artifact / summary / Robot diagnostics safe alias 或 wrapper JSON，
并读取 field owner/support 提交的脱敏 review packet。输出只表示 owner/support
intake 是否足够进入下一步 review handoff 或返工，不读取真实 ROS/Nav2 runtime、
硬件、真实电梯、外部云或真实手机/browser，也不触发机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_acceptance_handoff_intake as intake
import route_task_field_retest_material_pack as material_pack


DECISION_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary.v1"
REVIEW_PACKET_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_support_review_packet.v1"
SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_gate"

# 上游必须是上一轮 handoff intake；不能跳过 owner/support intake 直接做 review decision。
SOURCE_SCHEMAS = {intake.INTAKE_SCHEMA, intake.INTAKE_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {intake.INTAKE_BOUNDARY}
READY_SOURCE_INTAKE = intake.READY_INTAKE

READY_DECISION = "ready_for_acceptance_handoff_review_handoff_not_proven"
REVIEW_NEEDS_OWNER_REWORK = "review_needs_owner_rework"
REVIEW_EVIDENCE_REF_MISMATCH = "review_evidence_ref_mismatch"
REVIEW_UNSAFE_REJECTED = "review_unsafe_rejected"
BLOCKED_MISSING_HANDOFF_INTAKE = "blocked_missing_handoff_intake"
ALLOWED_REVIEW_DECISIONS = (
    READY_DECISION,
    REVIEW_NEEDS_OWNER_REWORK,
    REVIEW_EVIDENCE_REF_MISMATCH,
    REVIEW_UNSAFE_REJECTED,
    BLOCKED_MISSING_HANDOFF_INTAKE,
)

# 本 gate 只复核这些材料类别的 safe refs，不读取或验证真实材料正文。
REQUIRED_REVIEW_MATERIALS = intake.REQUIRED_OWNER_INTAKE_MATERIALS
NOT_PROVEN = intake.NOT_PROVEN

# rg 围栏依赖这些 literal；也给人工复盘一个压缩边界说明。
BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_gate; "
    "field_evidence_rerun_execution_result_acceptance_handoff_intake; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_gate; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false; "
    "ready_for_acceptance_handoff_review_handoff_not_proven; "
    "review_needs_owner_rework; review_evidence_ref_mismatch; "
    "review_unsafe_rejected; blocked_missing_handoff_intake"
)

# 设计约束 01：本 gate 只消费上一轮 handoff intake safe output。
# 设计约束 02：review packet 只能是脱敏 metadata，不读取 raw material。
# 设计约束 03：ready 只表示可进入下一步 review handoff，不证明现场材料为真。
# 设计约束 04：source=software_proof 与 not_proven 必须跨 gate 延续。
# 设计约束 05：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 06：same evidence_ref 是现场复账主键，不一致必须 fail closed。
# 设计约束 07：弱类型 same_evidence_ref_required 不能通过，必须是 JSON boolean true。
# 设计约束 08：review packet 只接受 checklist 类别确认，不接受成功或控制文案。
# 设计约束 09：缺任一 required review 类别只能进入 owner rework。
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
# 设计约束 21：review packet schema 只用于本地约定，不代表现场来源可信。
# 设计约束 22：accepted_material_refs 只列安全类别名，不复制完整材料。
# 设计约束 23：rejected_materials 优先视为 unsafe，防止坏材料进入 ready。
# 设计约束 24：上游 intake 未 ready 时不能从 review packet 推导 ready。
# 设计约束 25：最终 artifact 和 summary 都包含 hard boundary flags。

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
        "field_evidence_rerun_execution_result_acceptance_handoff_intake",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary",
        "acceptance_handoff_intake",
        "acceptance_handoff_intake_summary",
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


def _review_packet_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # review packet 只从固定 wrapper key 递归，避免 raw callback body 被误采信。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_packet",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_packet",
        "owner_support_review_packet",
        "review_packet",
        "owner_review_packet",
        "support_review_packet",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_review_packet_candidates(value))
    return candidates


def _find_review_packet(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中优先；没有 schema 时使用顶层，便于现场 owner 提交最小 JSON。
    for candidate in _review_packet_candidates(payload):
        if str(candidate.get("schema", "")).strip() == REVIEW_PACKET_SCHEMA:
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
    # safe evidence_ref 可来自顶层、safe_copy、owner_intake 或下游只读摘要。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    owner_intake = _dict(source, "owner_intake")
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
            owner_intake.get("safe_evidence_ref"),
            owner_intake.get("evidence_ref"),
            default="",
        )
    )


def _source_intake_status(source: dict[str, Any]) -> str:
    # 上游 ready intake 是进入 review decision 的必要条件，不能从材料数量推断。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            source.get("intake_status"),
            source.get("status"),
            robot.get("intake_status"),
            robot.get("status"),
            mobile.get("intake_status"),
            mobile.get("status"),
            safe_copy.get("intake_status"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _same_ref_required(source: dict[str, Any], review_packet: dict[str, Any]) -> Any:
    # 两侧都必须保持 JSON boolean true；字符串 true 会在多语言端产生歧义。
    source_safe = _dict(source, "safe_copy")
    review_safe = _dict(review_packet, "safe_copy")
    source_value = source.get("same_evidence_ref_required", source_safe.get("same_evidence_ref_required", True))
    review_value = review_packet.get("same_evidence_ref_required", review_safe.get("same_evidence_ref_required", True))
    return source_value if source_value is not True else review_value


def _source_is_safe(source: dict[str, Any]) -> bool:
    # software_proof、not_proven 和三个 false flag 是 intake 的最低安全边界。
    encoded = material_pack._encoded(source)
    return (
        source.get("source") == "software_proof"
        and "not_proven" in encoded
        and source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _review_packet_is_safe(review_packet: dict[str, Any]) -> bool:
    # review packet 也必须显式 fail-closed，避免人工复核绕过边界。
    encoded = material_pack._encoded(review_packet)
    return (
        review_packet.get("source") == "software_proof"
        and "not_proven" in encoded
        and review_packet.get("safe_to_control") is False
        and review_packet.get("delivery_success") is False
        and review_packet.get("primary_actions_enabled") is False
    )


def _review_packet_evidence_ref(review_packet: dict[str, Any]) -> str:
    # owner/support review packet 的 evidence_ref 可以在 safe_copy 内部，最终仍脱敏为 safe ref。
    safe_copy = _dict(review_packet, "safe_copy")
    return material_pack._safe_ref(
        _first_text(
            review_packet.get("safe_evidence_ref"),
            review_packet.get("evidence_ref"),
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
    return any(pattern.search(encoded) for pattern in FORBIDDEN_PROOF_CLAIM_PATTERNS)


def _material_key(value: str) -> str:
    # 大小写、空白、短横线和下划线不应影响 checklist 类别匹配。
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _review_material_status(review_packet: dict[str, Any]) -> dict[str, Any]:
    # review packet 可以用几种安全字段表达同一 checklist review。
    safe_copy = _dict(review_packet, "safe_copy")
    accepted = []
    for key in (
        "accepted_materials",
        "accepted_material_refs",
        "reviewed_materials",
        "reviewed_material_refs",
        "safe_material_refs",
        "review_checklist_accepted",
        "handoff_review_materials",
    ):
        accepted.extend(_safe_list(review_packet.get(key) or safe_copy.get(key)))
    checklist = review_packet.get("review_checklist") or safe_copy.get("review_checklist")
    if isinstance(checklist, list):
        for item in checklist:
            if isinstance(item, dict) and item.get("status") in {"accepted", "reviewed", "accepted_not_proven", "ready_not_proven"}:
                accepted.extend(_safe_list(item))
    accepted_keys = {_material_key(item) for item in accepted}
    required_keys = {_material_key(item): item for item in REQUIRED_REVIEW_MATERIALS}
    accepted_required = [required for key, required in required_keys.items() if key in accepted_keys]
    missing = _safe_list(review_packet.get("missing_materials") or safe_copy.get("missing_materials"))
    if not missing:
        missing = [required for key, required in required_keys.items() if key not in accepted_keys]
    rejected = _safe_list(review_packet.get("rejected_materials") or safe_copy.get("rejected_materials") or review_packet.get("unsafe_material_refs"))
    rework = _safe_list(review_packet.get("rework_reasons") or safe_copy.get("rework_reasons") or review_packet.get("owner_rework_reasons"))
    return {
        "status": "accepted" if not missing and not rejected and not rework else ("rejected" if rejected else "missing"),
        "required_materials": list(REQUIRED_REVIEW_MATERIALS),
        "accepted_materials": accepted_required,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "owner_rework_reasons": rework,
        "accepted_count": len(accepted_required),
        "required_count": len(REQUIRED_REVIEW_MATERIALS),
        "is_complete": not missing and not rejected and not rework and len(accepted_required) == len(REQUIRED_REVIEW_MATERIALS),
    }


def _review_packet_status(review_packet: dict[str, Any]) -> str:
    # 显式 packet 状态可让 owner/support 主动要求 rework；不能覆盖 unsafe 检查。
    safe_copy = _dict(review_packet, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            review_packet.get("review_status"),
            review_packet.get("status"),
            safe_copy.get("review_status"),
            safe_copy.get("status"),
            default="ready_not_proven",
        )
    )


def _source_lineage(source: dict[str, Any], review_packet: dict[str, Any]) -> dict[str, str]:
    # lineage 只复制短字段，避免复制完整上游 artifact 或 review packet。
    lineage = {
        "source_handoff_intake_schema": material_pack._safe_text(source.get("schema", "")),
        "source_handoff_intake_status": _source_intake_status(source),
        "owner_support_review_packet_schema": material_pack._safe_text(review_packet.get("schema", "")),
    }
    safe_lineage = source.get("safe_lineage")
    if isinstance(safe_lineage, dict):
        for key, value in safe_lineage.items():
            text = material_pack._safe_text(value)
            if text:
                lineage[f"handoff_intake_{material_pack._safe_text(key)}"] = text
    return lineage


def _review_decision(
    intake_load_issue: str,
    review_packet_load_issue: str,
    source_state: dict[str, Any],
    source_intake_status: str,
    review_packet_status: str,
    requested_ref: str,
    source_ref: str,
    review_ref: str,
    same_ref_required: Any,
    source_safe: bool,
    review_packet_safe: bool,
    unsafe_source_or_review: bool,
    success_or_control_claim: bool,
    material_status: dict[str, Any],
) -> tuple[str, list[str], int]:
    # fail-closed 顺序固定：输入可信性和安全边界优先于材料缺口。
    if intake_load_issue:
        return BLOCKED_MISSING_HANDOFF_INTAKE, [intake_load_issue], 2
    if source_state["schema_status"] != "supported":
        return BLOCKED_MISSING_HANDOFF_INTAKE, ["unsupported_handoff_intake_schema_or_boundary"], 2
    if review_packet_load_issue:
        return REVIEW_NEEDS_OWNER_REWORK, [review_packet_load_issue], 3
    if not (requested_ref or source_ref or review_ref):
        return BLOCKED_MISSING_HANDOFF_INTAKE, ["missing_safe_evidence_ref"], 2
    refs = [ref for ref in (requested_ref, source_ref, review_ref) if ref]
    if len(set(refs)) > 1:
        return REVIEW_EVIDENCE_REF_MISMATCH, ["requested_source_review_evidence_ref_mismatch"], 4
    if same_ref_required is not True:
        return REVIEW_EVIDENCE_REF_MISMATCH, ["same_evidence_ref_required_not_boolean_true"], 4
    if not source_safe:
        return REVIEW_UNSAFE_REJECTED, ["source_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if not review_packet_safe:
        return REVIEW_UNSAFE_REJECTED, ["review_packet_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if unsafe_source_or_review:
        return REVIEW_UNSAFE_REJECTED, ["unsafe_or_raw_copy_detected"], 5
    if success_or_control_claim:
        return REVIEW_UNSAFE_REJECTED, ["success_or_control_or_forbidden_proof_claim_detected"], 5
    if source_intake_status != READY_SOURCE_INTAKE:
        return REVIEW_NEEDS_OWNER_REWORK, ["handoff_intake_not_ready_for_review_decision"], 3
    if review_packet_status in {"unsafe", "rejected", "review_unsafe_rejected"}:
        return REVIEW_UNSAFE_REJECTED, ["owner_support_review_packet_rejected_unsafe"], 5
    if review_packet_status in {"needs_rework", "missing", "review_needs_owner_rework"}:
        return REVIEW_NEEDS_OWNER_REWORK, ["owner_support_review_packet_requests_rework"], 3
    if material_status["rejected_materials"]:
        return REVIEW_UNSAFE_REJECTED, ["review_packet_contains_rejected_or_unsafe_material_refs"], 5
    if material_status["missing_materials"] or material_status["owner_rework_reasons"] or not material_status["is_complete"]:
        return REVIEW_NEEDS_OWNER_REWORK, ["review_packet_missing_required_material_review"], 3
    return READY_DECISION, ["handoff_intake_and_owner_support_review_packet_ready_not_proven"], 0


def _review_checklist(evidence_ref: str, material_status: dict[str, Any]) -> list[dict[str, Any]]:
    # checklist 明确 review 对每类材料的状态，但仍不验证真实材料正文。
    accepted = set(material_status["accepted_materials"])
    rejected = set(material_status["rejected_materials"])
    checklist = []
    for item in REQUIRED_REVIEW_MATERIALS:
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
    if state == READY_DECISION:
        return [
            f"handoff review decision for evidence_ref={ref} to field owner/support review handoff without enabling controls",
            "keep collecting true task record, true Nav2/fixed-route runtime log, route completion signal, elevator/floor/human assistance evidence, dropoff/cancel or delivery result, and true phone/browser evidence as real materials outside this gate",
            "keep Robot/mobile primary actions disabled until real reviewed material exists",
        ]
    if state == REVIEW_NEEDS_OWNER_REWORK:
        required = [f"review or rework safe material: {name} at evidence_ref={ref}" for name in material_status["missing_materials"]]
        required.extend([f"resolve owner rework reason: {reason}" for reason in material_status["owner_rework_reasons"]])
        return required or [f"rerun owner/support review packet after previous intake emits {READY_SOURCE_INTAKE} for evidence_ref={ref}", *reasons]
    if state == REVIEW_EVIDENCE_REF_MISMATCH:
        return [f"rerun acceptance handoff intake and review packet so all summaries share evidence_ref={ref}"]
    if state == REVIEW_UNSAFE_REJECTED:
        return ["remove unsafe/raw/success/control/external-proof/HIL/verified-terminal/PR-resolution claims and rerun the PC-only review decision gate"]
    return [f"provide supported acceptance handoff intake artifact or summary for evidence_ref={ref}", *reasons]


def _owner_handoff(state: str, evidence_ref: str, checklist: list[dict[str, Any]], next_required_evidence: list[str]) -> dict[str, Any]:
    # owner_handoff 只授权人工复核和补证，不给 Robot/mobile 开控制权限。
    return {
        "primary_owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "handoff_status": state,
        "review_decision": state,
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "evidence_ref": evidence_ref or "<same_evidence_ref>",
        "review_checklist": checklist,
        "next_required_evidence": next_required_evidence,
        "reviewer_boundary": "acceptance_handoff_intake_review_decision_only_not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC evidence gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake.py --review-handoff-json <review_handoff.json> --owner-intake-json <owner_intake.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision.py --handoff-intake-json <handoff_intake.json> --review-packet-json <review_packet.json> --evidence-ref {ref}",
        "keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false",
    ]


def _safe_copy(
    state: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    review_packet_summary: dict[str, Any],
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
        "schema": f"{DECISION_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": state,
        "review_decision": state,
        "allowed_review_decisions": list(ALLOWED_REVIEW_DECISIONS),
        "decision_reasons": reasons,
        "evidence_boundary": DECISION_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_handoff_intake": source_summary,
        "owner_support_review_packet": review_packet_summary,
        "safe_lineage": lineage,
        "material_status": material_status,
        "review_checklist": checklist,
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
    review_packet_summary: dict[str, Any],
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
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": state,
        "review_decision": state,
        "allowed_review_decisions": list(ALLOWED_REVIEW_DECISIONS),
        "decision_reasons": reasons,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_handoff_intake": source_summary,
        "owner_support_review_packet": review_packet_summary,
        "safe_lineage": lineage,
        "required_materials": list(REQUIRED_REVIEW_MATERIALS),
        "material_status": material_status,
        "review_checklist": checklist,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision(
    handoff_intake_json: str,
    review_packet_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 handoff intake 与 owner/support review packet，生成 fail-closed review decision。"""
    source_payload, source_load_issue = _load_json(handoff_intake_json, "handoff_intake")
    review_payload, review_load_issue = _load_json(review_packet_json, "review_packet")
    source = _find_source(source_payload) if source_payload else {}
    review_packet = _find_review_packet(review_payload) if review_payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref)
    source_ref = _source_evidence_ref(source)
    review_ref = _review_packet_evidence_ref(review_packet)
    effective_ref = requested_ref or source_ref or review_ref
    source_state = _source_status(source_load_issue, source)
    source_intake_status = _source_intake_status(source) if source else "missing"
    review_packet_status = _review_packet_status(review_packet) if review_packet else "missing"
    same_ref_required = _same_ref_required(source, review_packet) if (source or review_packet) else True
    source_safe = bool(source) and _source_is_safe(source)
    review_packet_safe = bool(review_packet) and _review_packet_is_safe(review_packet)
    unsafe_source_or_review = bool(source_payload or review_payload) and (
        material_pack._has_forbidden_copy(source)
        or material_pack._has_raw_path_copy(source)
        or material_pack._has_forbidden_copy(review_packet)
        or material_pack._has_raw_path_copy(review_packet)
    )
    success_or_control_claim = bool(source_payload or review_payload) and (
        material_pack._has_success_or_control_claim(source)
        or material_pack._has_success_or_control_claim(review_packet)
        or _has_true_control_flag(source)
        or _has_true_control_flag(review_packet)
        or _has_forbidden_proof_claim(source)
        or _has_forbidden_proof_claim(review_packet)
    )
    material_status = _review_material_status(review_packet) if review_packet else {
        "status": "missing",
        "required_materials": list(REQUIRED_REVIEW_MATERIALS),
        "accepted_materials": [],
        "missing_materials": list(REQUIRED_REVIEW_MATERIALS),
        "rejected_materials": [],
        "owner_rework_reasons": [],
        "accepted_count": 0,
        "required_count": len(REQUIRED_REVIEW_MATERIALS),
        "is_complete": False,
    }

    state, reasons, exit_code = _review_decision(
        source_load_issue,
        review_load_issue,
        source_state,
        source_intake_status,
        review_packet_status,
        requested_ref,
        source_ref,
        review_ref,
        same_ref_required,
        source_safe,
        review_packet_safe,
        unsafe_source_or_review,
        success_or_control_claim,
        material_status,
    )
    lineage = _source_lineage(source, review_packet)
    checklist = _review_checklist(effective_ref, material_status)
    next_required_evidence = _next_required_evidence(state, effective_ref, material_status, reasons)
    owner_handoff = _owner_handoff(state, effective_ref, checklist, next_required_evidence)
    rerun_commands = _rerun_commands(effective_ref)
    source_summary = {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "intake_status": source_intake_status,
        "status": source_intake_status,
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "source_is_software_proof_not_proven": bool(source_safe),
    }
    review_packet_summary = {
        "load_status": "blocked" if review_load_issue else "loaded",
        "load_issue": review_load_issue,
        "schema": material_pack._safe_text(review_packet.get("schema", "")),
        "source": material_pack._safe_text(review_packet.get("source", "")),
        "review_packet_status": review_packet_status,
        "safe_evidence_ref": review_ref,
        "evidence_ref": review_ref,
        "review_packet_is_software_proof_not_proven": bool(review_packet_safe),
        "unsafe_copy": bool(unsafe_source_or_review),
        "success_or_control_claim": bool(success_or_control_claim),
    }
    safe_copy = _safe_copy(
        state,
        effective_ref,
        source_summary,
        review_packet_summary,
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
        review_packet_summary,
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
        "schema": DECISION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": state,
        "review_decision": state,
        "allowed_review_decisions": list(ALLOWED_REVIEW_DECISIONS),
        "decision_reasons": reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "source_handoff_intake": source_summary,
        "owner_support_review_packet": review_packet_summary,
        "safe_lineage": lineage,
        "required_materials": list(REQUIRED_REVIEW_MATERIALS),
        "material_status": material_status,
        "review_checklist": checklist,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary": summary,
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
        artifact["status"] = REVIEW_UNSAFE_REJECTED
        artifact["review_decision"] = REVIEW_UNSAFE_REJECTED
        artifact["robot_diagnostics_summary"]["status"] = REVIEW_UNSAFE_REJECTED
        artifact["robot_diagnostics_summary"]["review_decision"] = REVIEW_UNSAFE_REJECTED
        artifact["mobile_readonly_summary"]["status"] = REVIEW_UNSAFE_REJECTED
        artifact["mobile_readonly_summary"]["review_decision"] = REVIEW_UNSAFE_REJECTED
        summary["status"] = REVIEW_UNSAFE_REJECTED
        summary["review_decision"] = REVIEW_UNSAFE_REJECTED
        artifact["field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun acceptance handoff intake review decision artifact")
    parser.add_argument("--handoff-intake-json", required=True, help="acceptance handoff intake artifact, summary, or wrapper JSON")
    parser.add_argument("--review-packet-json", required=True, help="owner/support safe review packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this review decision gate")
    parser.add_argument("--output", default="", help="optional review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision(
        args.handoff_intake_json,
        args.review_packet_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_handoff_intake_review_decision_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
