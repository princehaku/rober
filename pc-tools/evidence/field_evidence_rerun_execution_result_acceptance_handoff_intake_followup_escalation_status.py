#!/usr/bin/env python3
"""生成 acceptance handoff intake follow-up escalation status。

该 PC-only gate 接在
`field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff`
之后，只读取上一轮 review-handoff artifact / summary / Robot safe alias 或
wrapper/nested JSON，并读取 owner/support/reviewer 的安全 follow-up policy。
输出只表达同一 safe evidence_ref 的跟进到期状态，不读取 raw field material、
ROS/Nav2 runtime、硬件、外部云、真实手机/browser，也不触发机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff as review_handoff
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary.v1"
POLICY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_policy.v1"
ROBOT_ALIAS = "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status"
SOURCE_CAPABILITY = "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff"
BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate"
SOURCE_BOUNDARY = review_handoff.HANDOFF_BOUNDARY
SOURCE_READY = review_handoff.READY_HANDOFF

ALLOWED_DUE_STATES = ("pending", "overdue", "escalated", "blocked")
REQUIRED_FOLLOWUP_MATERIALS = (
    "true task record",
    "true Nav2/fixed-route runtime log",
    "route completion signal",
    "true elevator door state",
    "target floor confirmation",
    "human assistance record",
    "dropoff/cancel completion or delivery result",
    "true route/elevator field pass",
    "true phone/browser evidence",
    "PR #5 hardware material remains pending unless PRRT_kwDOSWB9286CJ3tX is live resolved",
)
NOT_PROVEN = review_handoff.NOT_PROVEN
SOURCE_SCHEMAS = {review_handoff.HANDOFF_SCHEMA, review_handoff.HANDOFF_SUMMARY_SCHEMA}

# 设计约束 01：只消费上一轮 review-handoff safe surface，不读取 raw artifact。
# 设计约束 02：follow-up policy 只能表达 due state 与安全材料类别，不是证明材料。
# 设计约束 03：pending / overdue / escalated 仍然是 software_proof 和 not_proven。
# 设计约束 04：blocked 是唯一 fail-closed 状态，任何输入异常都映射到 blocked。
# 设计约束 05：same evidence_ref 是复账主键，source 与 policy 不一致必须 blocked。
# 设计约束 06：source=software_proof、not_proven 与三个 false flag 必须跨 gate 延续。
# 设计约束 07：source review-handoff 未 ready 时不能从 policy 推导可跟进。
# 设计约束 08：缺任一 required material category acknowledgement 必须 blocked。
# 设计约束 09：PR #5 unresolved / hardware_material_pending 只能作为缺口，不可宣称 resolved。
# 设计约束 10：unsafe copy、credential、本机路径、ROS topic、串口和 WAVE ROVER 文案必须拒绝。
# 设计约束 11：外部证明、HIL、field pass、verified terminal、success/control claim 必须拒绝。
# 设计约束 12：输出 summary 是 Robot/mobile 只读面，不携带 raw source 或 raw policy。
# 设计约束 13：wrapper/nested JSON 只递归固定 key，避免误采信任意 payload。
# 设计约束 14：CLI 只在 pending/overdue/escalated 安全状态返回 0，blocked 返回非 0。
# 设计约束 15：dependency-free，方便 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 16：本文件不查 vendor，因为不新增硬件参数、串口、波特率或协议假设。
# 设计约束 17：artifact 与 summary 最后递归脱敏，防止新字段绕过安全扫描。
# 设计约束 18：所有技术注释使用中文，解释为什么 fail-closed。
# 设计约束 19：本 gate 不更新 Robot/mobile/OKR/sprint closeout 文件。
# 设计约束 20：状态名保持 plan 中的四个短枚举，便于 UI 和 rg 围栏复用。
# 设计约束 21：required materials 是安全类别名，不代表真实材料正文已存在。
# 设计约束 22：policy due_state 不支持任意扩展，未知值直接 blocked。
# 设计约束 23：source safe alias 可嵌套在 Robot/mobile wrapper，但只读白名单 key。
# 设计约束 24：输出不包含真实控制、dispatch、callback、ACK、串口或 ROS 命令。

BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate; "
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate; "
    "source=software_proof; software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false; pending; overdue; escalated; blocked"
)

FORBIDDEN_PROOF_CLAIM_PATTERNS = (
    re.compile(r"(?i)\braw\s+artifact(s)?\b"),
    re.compile(r"(?i)\bcomplete\s+artifact(s)?\b"),
    re.compile(r"(?i)\btrue\s+phone/browser\s+proof\b"),
    re.compile(r"(?i)\breal\s+phone/browser\s+proof\b"),
    re.compile(r"(?i)\breal\s+nav2/fixed-route\s+(runtime\s+)?pass\b"),
    re.compile(r"(?i)\breal\s+route/elevator\s+field\s+pass\b"),
    re.compile(r"(?i)\bverified\s+terminal\s+result\b"),
    re.compile(r"(?i)\bobjective\s*5\s+external\s+proof\b"),
    re.compile(r"(?i)\bo5\s+external\s+proof\b"),
    re.compile(r"(?i)\bexternal\s+proof\b"),
    re.compile(r"(?i)\bwave\s+rover\b"),
    re.compile(r"(?i)\buart\b"),
    re.compile(r"(?i)\bserial\s+(device|path|port)\b"),
    re.compile(r"(?i)\breal\s+hil\b"),
    re.compile(r"(?i)\bhil\s+(pass|passed|complete|completed|verified)\b"),
    re.compile(r"(?i)\bpr\s*#?5\s+(reviewer\s+)?(resolved|resolution|closed)\b"),
    re.compile(r"(?i)\bPRRT_kwDOSWB9286CJ3tX\s+(resolved|closed)\b"),
    re.compile(r"(?i)\bdropoff\s+(complete|completed|success|succeeded|verified)\b"),
    re.compile(r"(?i)\bcancel\s+(complete|completed|success|succeeded|verified)\b"),
    re.compile(r"(?i)\bdelivery\s+(complete|completed|success|succeeded|verified)\b"),
)

SUCCESS_OR_CONTROL_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed|verified)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|complete|completed|passed|verified)\b"),
    re.compile(r"(?i)\bcancel\s+(success|succeeded|complete|completed|passed|verified)\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed|verified)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed|verified)\b"),
    re.compile(r"(?i)\bfield\s+pass\s+(success|succeeded|complete|completed|passed|verified|proven)\b"),
    re.compile(r"(?i)\bfield\s+pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action)\b"),
)


def _utc_now() -> str:
    # UTC 文本便于不同 PC/Docker 主机按字典序审计产物。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 输入错误必须变成 blocked artifact，不能让调用方误以为无事发生。
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
    # 字符串化 JSON 不展开，避免把 raw body 伪装成 safe wrapper。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # 多来源字段只取第一个非空短文本，统一由 material_pack 脱敏。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 64) -> list[str]:
    # 列表字段只保留短字符串或 dict 的 name/material/ref，禁止复制完整对象。
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
    # 只递归 known safe keys，避免 raw diagnostics 或 raw material 进入 source。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary",
        "acceptance_handoff_intake_review_handoff",
        "acceptance_handoff_intake_review_handoff_summary",
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
    # schema 命中时优先取嵌套 safe object，否则保留顶层用于 blocked 诊断。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _policy_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # policy 也只接受固定 wrapper，防止 raw callback body 被误当安全策略。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_policy",
        "followup_escalation_policy",
        "follow_up_policy",
        "safe_followup_policy",
        "owner_support_reviewer_followup_policy",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_policy_candidates(value))
    return candidates


def _find_policy(payload: dict[str, Any]) -> dict[str, Any]:
    # 有 schema 时优先；无 schema 时允许最小 policy JSON 直传。
    for candidate in _policy_candidates(payload):
        if str(candidate.get("schema", "")).strip() == POLICY_SCHEMA:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, Any]:
    # schema 与 boundary 必须同时匹配，不能跨 gate 消费旧 artifact。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _evidence_ref_from(payload: dict[str, Any]) -> str:
    # safe ref 可出现在顶层或常见 safe wrapper 内，最终统一脱敏。
    robot = _dict(payload, "robot_diagnostics_summary")
    mobile = _dict(payload, "mobile_readonly_summary")
    safe_copy = _dict(payload, "safe_copy")
    owner_handoff = _dict(payload, "owner_handoff")
    return material_pack._safe_ref(
        _first_text(
            payload.get("safe_evidence_ref"),
            payload.get("evidence_ref"),
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
    # 只有上游 ready review-handoff 才能进入 follow-up due 状态。
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


def _same_ref_required(source: dict[str, Any], policy: dict[str, Any]) -> Any:
    # 两侧都必须是 JSON boolean true；字符串 true 不通过。
    source_safe = _dict(source, "safe_copy")
    policy_safe = _dict(policy, "safe_copy")
    source_value = source.get("same_evidence_ref_required", source_safe.get("same_evidence_ref_required", True))
    policy_value = policy.get("same_evidence_ref_required", policy_safe.get("same_evidence_ref_required", True))
    return source_value if source_value is not True else policy_value


def _is_safe_surface(payload: dict[str, Any]) -> bool:
    # software_proof、not_proven 和三个 false flag 是跨团队消费的最低边界。
    encoded = material_pack._encoded(payload)
    return (
        payload.get("source") == "software_proof"
        and "not_proven" in encoded
        and payload.get("safe_to_control") is False
        and payload.get("delivery_success") is False
        and payload.get("primary_actions_enabled") is False
    )


def _has_true_control_flag(value: Any) -> bool:
    # 递归阻断布尔 true，因为它比自由文本更容易被下游误用。
    if isinstance(value, dict):
        if value.get("safe_to_control") is True or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
        return any(_has_true_control_flag(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_true_control_flag(item) for item in value)
    return False


def _has_forbidden_proof_claim(value: Any) -> bool:
    # checklist 中允许材料类别名；这里阻断的是“已证明/已完成/已 resolved”语义。
    encoded = material_pack._encoded(value)
    return any(pattern.search(encoded) for pattern in FORBIDDEN_PROOF_CLAIM_PATTERNS)


def _has_success_or_control_claim(value: Any) -> bool:
    # 本 gate 允许 checklist 里出现 field pass 类别名，但不允许成功/控制语义。
    encoded = material_pack._encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_OR_CONTROL_PATTERNS)


def _material_key(value: str) -> str:
    # 类别匹配忽略大小写、空格、短横线和下划线，便于人工 policy 输入。
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _policy_due_state(policy: dict[str, Any]) -> str:
    # due_state 是本 gate 的主枚举；未知值必须 blocked。
    safe_copy = _dict(policy, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            policy.get("due_state"),
            policy.get("followup_due_state"),
            policy.get("followup_status"),
            policy.get("status"),
            safe_copy.get("due_state"),
            safe_copy.get("followup_due_state"),
            safe_copy.get("followup_status"),
            safe_copy.get("status"),
            default="blocked",
        )
    )


def _policy_material_status(policy: dict[str, Any]) -> dict[str, Any]:
    # policy 只确认“类别已纳入跟进”，不接收真实材料正文。
    safe_copy = _dict(policy, "safe_copy")
    accepted: list[str] = []
    for key in (
        "accepted_materials",
        "accepted_material_refs",
        "required_materials_acknowledged",
        "followup_materials",
        "followup_material_refs",
        "safe_material_refs",
        "owner_support_reviewer_followup_materials",
    ):
        accepted.extend(_safe_list(policy.get(key) or safe_copy.get(key)))
    checklist = policy.get("followup_checklist") or policy.get("required_materials_checklist") or safe_copy.get("followup_checklist")
    if isinstance(checklist, list):
        for item in checklist:
            if isinstance(item, dict) and item.get("status") in {"accepted", "pending", "overdue", "escalated", "acknowledged", "accepted_not_proven"}:
                accepted.extend(_safe_list(item))
    accepted_keys = {_material_key(item) for item in accepted}
    required_by_key = {_material_key(item): item for item in REQUIRED_FOLLOWUP_MATERIALS}
    accepted_required = [required for key, required in required_by_key.items() if key in accepted_keys]
    missing = _safe_list(policy.get("missing_materials") or safe_copy.get("missing_materials"))
    if not missing:
        missing = [required for key, required in required_by_key.items() if key not in accepted_keys]
    rejected = _safe_list(policy.get("rejected_materials") or safe_copy.get("rejected_materials") or policy.get("unsafe_material_refs"))
    return {
        "status": "accepted" if not missing and not rejected else ("rejected" if rejected else "missing"),
        "required_materials": list(REQUIRED_FOLLOWUP_MATERIALS),
        "accepted_materials": accepted_required,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "accepted_count": len(accepted_required),
        "required_count": len(REQUIRED_FOLLOWUP_MATERIALS),
        "is_complete": not missing and not rejected and len(accepted_required) == len(REQUIRED_FOLLOWUP_MATERIALS),
    }


def _lineage(source: dict[str, Any], policy: dict[str, Any]) -> dict[str, str]:
    # lineage 只复制短字段，避免完整 source/policy 进入输出。
    return {
        "source_capability": SOURCE_CAPABILITY,
        "source_review_handoff_schema": material_pack._safe_text(source.get("schema", "")),
        "source_review_handoff_status": _source_handoff_status(source),
        "source_review_handoff_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "policy_schema": material_pack._safe_text(policy.get("schema", "")),
    }


def _decision(
    source_load_issue: str,
    policy_load_issue: str,
    source_state: dict[str, Any],
    source_handoff_status: str,
    due_state: str,
    requested_ref: str,
    source_ref: str,
    policy_ref: str,
    same_ref_required: Any,
    source_safe: bool,
    policy_safe: bool,
    unsafe_source_or_policy: bool,
    success_or_control_claim: bool,
    material_status: dict[str, Any],
) -> tuple[str, list[str], int]:
    # fail-closed 顺序固定：来源可信、证据主键、安全边界、材料缺口。
    if source_load_issue:
        return "blocked", [source_load_issue], 2
    if source_state["schema_status"] != "supported":
        return "blocked", ["unsupported_review_handoff_schema_or_boundary"], 2
    if policy_load_issue:
        return "blocked", [policy_load_issue], 3
    if due_state not in ALLOWED_DUE_STATES or due_state == "blocked":
        return "blocked", ["unsupported_or_blocked_due_state"], 3
    if not (requested_ref or source_ref or policy_ref):
        return "blocked", ["missing_safe_evidence_ref"], 4
    refs = [ref for ref in (requested_ref, source_ref, policy_ref) if ref]
    if len(set(refs)) > 1:
        return "blocked", ["requested_source_policy_evidence_ref_mismatch"], 4
    if same_ref_required is not True:
        return "blocked", ["same_evidence_ref_required_not_boolean_true"], 4
    if not source_safe:
        return "blocked", ["source_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if not policy_safe:
        return "blocked", ["policy_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if unsafe_source_or_policy:
        return "blocked", ["unsafe_or_raw_copy_detected"], 5
    if success_or_control_claim:
        return "blocked", ["success_or_control_or_forbidden_proof_claim_detected"], 5
    if source_handoff_status != SOURCE_READY:
        return "blocked", ["source_review_handoff_not_ready"], 2
    if material_status["rejected_materials"]:
        return "blocked", ["followup_policy_contains_rejected_or_unsafe_material_refs"], 5
    if material_status["missing_materials"] or not material_status["is_complete"]:
        return "blocked", ["followup_policy_missing_required_material_categories"], 3
    return due_state, [f"followup_due_state_{due_state}_not_proven"], 0


def _next_required_evidence(state: str, evidence_ref: str, material_status: dict[str, Any], reasons: list[str]) -> list[str]:
    # next evidence 是人工补证/升级清单，不是 Robot action 指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if state in {"pending", "overdue", "escalated"}:
        return [
            f"keep owner/support/reviewer follow-up state={state} for evidence_ref={ref} without enabling controls",
            "collect true task record, true Nav2/fixed-route runtime log, route completion signal, elevator/floor/human assistance evidence, dropoff/cancel or delivery result, true route/elevator field pass, true phone/browser evidence, and live PR #5 hardware material resolution outside this gate",
            "keep Robot/mobile primary actions disabled until real reviewed material exists",
        ]
    missing = [f"provide safe follow-up material category acknowledgement: {name} at evidence_ref={ref}" for name in material_status["missing_materials"]]
    return missing or [f"rerun follow-up escalation status inputs for evidence_ref={ref}", *reasons]


def _owner_escalation(state: str, evidence_ref: str, reasons: list[str], next_required_evidence: list[str]) -> dict[str, Any]:
    # escalation 只路由人工 owner，不赋予自动驾驶或远程控制权限。
    return {
        "primary_owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "due_state": state,
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "evidence_ref": evidence_ref or "<same_evidence_ref>",
        "escalate": state in {"overdue", "escalated"},
        "blocked": state == "blocked",
        "reasons": reasons,
        "next_required_evidence": next_required_evidence,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # commands 只覆盖 PC evidence gate，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff.py --review-decision-json <review_decision.json> --handoff-packet-json <handoff_packet.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.py --review-handoff-json <review_handoff.json> --followup-policy-json <followup_policy.json> --evidence-ref {ref}",
        "keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false",
    ]


def _non_access_scope() -> list[str]:
    # 明确不可访问范围，避免后续把本 gate 误解为现场 proof。
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
        "raw_route_elevator_field_pass",
        "raw_true_phone_browser_evidence",
        "raw_diagnostics",
        "ros_graph",
        "serial_uart",
        "wave_rover",
        "real_elevator",
        "external_cloud",
        "real_phone_or_browser",
        "verified_terminal_result",
        "pr5_resolution",
        "robot_action",
    ]


def _safe_copy(
    state: str,
    evidence_ref: str,
    reasons: list[str],
    source_summary: dict[str, Any],
    policy_summary: dict[str, Any],
    material_status: dict[str, Any],
    lineage: dict[str, str],
    owner_escalation: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，只保留跟进状态与缺口摘要。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "capability": CAPABILITY,
        "status": state,
        "due_state": state,
        "followup_status": state,
        "allowed_due_states": list(ALLOWED_DUE_STATES),
        "followup_reasons": reasons,
        "evidence_boundary": BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review_handoff": source_summary,
        "safe_followup_policy": policy_summary,
        "material_status": material_status,
        "safe_lineage": lineage,
        "owner_escalation": owner_escalation,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "source_boundary": SOURCE_BOUNDARY,
        "not_proven": "not_proven",
        "software_proof": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    state: str,
    evidence_ref: str,
    reasons: list[str],
    source_summary: dict[str, Any],
    policy_summary: dict[str, Any],
    material_status: dict[str, Any],
    lineage: dict[str, str],
    owner_escalation: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是跨 Robot/Full-stack 的稳定只读对接面。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "capability": CAPABILITY,
        "evidence_boundary": BOUNDARY,
        "boundary": BOUNDARY,
        "status": state,
        "due_state": state,
        "followup_status": state,
        "allowed_due_states": list(ALLOWED_DUE_STATES),
        "followup_reasons": reasons,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review_handoff": source_summary,
        "safe_followup_policy": policy_summary,
        "required_materials": list(REQUIRED_FOLLOWUP_MATERIALS),
        "material_status": material_status,
        "safe_lineage": lineage,
        "owner_escalation": owner_escalation,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "software_proof": True,
        "non_access_scope": _non_access_scope(),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status(
    review_handoff_json: str,
    followup_policy_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 review-handoff 与 follow-up policy，生成 fail-closed due status。"""
    source_payload, source_load_issue = _load_json(review_handoff_json, "review_handoff")
    policy_payload, policy_load_issue = _load_json(followup_policy_json, "followup_policy")
    source = _find_source(source_payload) if source_payload else {}
    policy = _find_policy(policy_payload) if policy_payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref)
    source_ref = _evidence_ref_from(source)
    policy_ref = _evidence_ref_from(policy)
    effective_ref = requested_ref or source_ref or policy_ref
    source_state = _source_status(source_load_issue, source)
    source_handoff_status = _source_handoff_status(source) if source else "missing"
    due_state = _policy_due_state(policy) if policy else "blocked"
    same_ref_required = _same_ref_required(source, policy) if (source or policy) else True
    source_safe = bool(source) and _is_safe_surface(source)
    policy_safe = bool(policy) and _is_safe_surface(policy)
    unsafe_source_or_policy = bool(source_payload or policy_payload) and (
        material_pack._has_forbidden_copy(source)
        or material_pack._has_raw_path_copy(source)
        or material_pack._has_forbidden_copy(policy)
        or material_pack._has_raw_path_copy(policy)
    )
    success_or_control_claim = bool(source_payload or policy_payload) and (
        _has_success_or_control_claim(source)
        or _has_success_or_control_claim(policy)
        or _has_true_control_flag(source)
        or _has_true_control_flag(policy)
        or _has_forbidden_proof_claim(source)
        or _has_forbidden_proof_claim(policy)
    )
    material_status = _policy_material_status(policy) if policy else {
        "status": "missing",
        "required_materials": list(REQUIRED_FOLLOWUP_MATERIALS),
        "accepted_materials": [],
        "missing_materials": list(REQUIRED_FOLLOWUP_MATERIALS),
        "rejected_materials": [],
        "accepted_count": 0,
        "required_count": len(REQUIRED_FOLLOWUP_MATERIALS),
        "is_complete": False,
    }

    state, reasons, exit_code = _decision(
        source_load_issue,
        policy_load_issue,
        source_state,
        source_handoff_status,
        due_state,
        requested_ref,
        source_ref,
        policy_ref,
        same_ref_required,
        source_safe,
        policy_safe,
        unsafe_source_or_policy,
        success_or_control_claim,
        material_status,
    )
    lineage = _lineage(source, policy)
    source_summary = {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "source_capability": SOURCE_CAPABILITY,
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "handoff_status": source_handoff_status,
        "status": source_handoff_status,
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "source_is_software_proof_not_proven": bool(source_safe),
    }
    policy_summary = {
        "load_status": "blocked" if policy_load_issue else "loaded",
        "load_issue": policy_load_issue,
        "schema": material_pack._safe_text(policy.get("schema", "")),
        "source": material_pack._safe_text(policy.get("source", "")),
        "due_state": due_state,
        "safe_evidence_ref": policy_ref,
        "evidence_ref": policy_ref,
        "policy_is_software_proof_not_proven": bool(policy_safe),
        "unsafe_copy": bool(unsafe_source_or_policy),
        "success_or_control_claim": bool(success_or_control_claim),
    }
    next_required_evidence = _next_required_evidence(state, effective_ref, material_status, reasons)
    owner_escalation = _owner_escalation(state, effective_ref, reasons, next_required_evidence)
    rerun_commands = _rerun_commands(effective_ref)
    safe_copy = _safe_copy(
        state,
        effective_ref,
        reasons,
        source_summary,
        policy_summary,
        material_status,
        lineage,
        owner_escalation,
        next_required_evidence,
        rerun_commands,
    )
    summary = _summary_payload(
        state,
        effective_ref,
        reasons,
        source_summary,
        policy_summary,
        material_status,
        lineage,
        owner_escalation,
        next_required_evidence,
        rerun_commands,
        safe_copy,
    )
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "capability": CAPABILITY,
        "evidence_boundary": BOUNDARY,
        "boundary": BOUNDARY,
        "status": state,
        "due_state": state,
        "followup_status": state,
        "allowed_due_states": list(ALLOWED_DUE_STATES),
        "followup_reasons": reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "source_review_handoff": source_summary,
        "safe_followup_policy": policy_summary,
        "required_materials": list(REQUIRED_FOLLOWUP_MATERIALS),
        "material_status": material_status,
        "safe_lineage": lineage,
        "owner_escalation": owner_escalation,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary": summary,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "software_proof": True,
        "non_access_scope": _non_access_scope(),
        "boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if material_pack._has_forbidden_copy(artifact) or material_pack._has_forbidden_copy(summary):
        # 最终防线：输出仍含禁词时强制 blocked，且保持所有控制旗标 false。
        artifact["status"] = "blocked"
        artifact["due_state"] = "blocked"
        artifact["followup_status"] = "blocked"
        summary["status"] = "blocked"
        summary["due_state"] = "blocked"
        summary["followup_status"] = "blocked"
        artifact["field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary"] = summary
        artifact[ROBOT_ALIAS] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate field evidence rerun acceptance handoff intake follow-up escalation status")
    parser.add_argument("--review-handoff-json", required=True, help="acceptance handoff intake review-handoff artifact, summary, Robot alias, or wrapper JSON")
    parser.add_argument("--followup-policy-json", required=True, help="safe follow-up policy JSON with pending/overdue/escalated/blocked due_state")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this follow-up escalation status gate")
    parser.add_argument("--output", default="", help="optional follow-up escalation status artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional follow-up escalation status summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status(
        args.review_handoff_json,
        args.followup_policy_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"followup_escalation_status_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"due_state: {artifact['due_state']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
