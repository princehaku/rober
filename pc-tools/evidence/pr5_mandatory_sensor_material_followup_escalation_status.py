#!/usr/bin/env python3
"""生成 PR #5 mandatory sensor material follow-up escalation status gate。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pr5_mandatory_sensor_source_alignment as source_alignment
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.pr5_mandatory_sensor_material_followup_escalation_status.v1"
SUMMARY_SCHEMA = "trashbot.pr5_mandatory_sensor_material_followup_escalation_status_summary.v1"
POLICY_SCHEMA = "trashbot.pr5_mandatory_sensor_material_followup_packet.v1"
ROBOT_ALIAS = "robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary"
SCHEMA_VERSION = 1
CAPABILITY = "pr5_mandatory_sensor_material_followup_escalation_status"
SOURCE_CAPABILITY = "pr5_mandatory_sensor_source_alignment"
BOUNDARY = "software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate"
SOURCE_BOUNDARY = "software_proof_docker_pr5_mandatory_sensor_source_alignment_gate"
THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"

ALLOWED_FOLLOWUP_STATUSES = (
    "pending",
    "overdue",
    "escalated",
    "blocked",
    "ready_for_reviewer_followup_not_proven",
)

REQUIRED_MATERIALS = (
    "2D LiDAR SKU/source/receipt/procurement material",
    "ToF SKU/source/receipt/procurement material",
    "mounting/installation material",
    "wiring and power-budget material",
    "calibration plan or calibration result",
    "HIL-entry material",
    "operator HIL report",
    "PR #5 reviewer follow-up or reviewer resolution evidence",
)

NOT_PROVEN = (
    "real_2d_lidar_material",
    "real_tof_material",
    "real_mounting_installation",
    "real_wiring_power_budget",
    "real_calibration",
    "real_sensor_hil_entry",
    "real_operator_hil_report",
    "pr5_review_thread_resolved",
    "objective_5_external_proof",
    "delivery_success",
)

SOURCE_SCHEMAS = {
    source_alignment.SCHEMA,
    source_alignment.SUMMARY_SCHEMA,
    "trashbot.robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary.v1",
}

# 设计约束 01：本 gate 只消费上一轮 source-alignment 的 safe 输出。
# 设计约束 02：safe material follow-up packet 只能表达跟进状态和材料类别。
# 设计约束 03：vendor/source refs 只证明来源上下文，不证明真实传感器材料。
# 设计约束 04：同一 safe evidence_ref 是跨 PC/Robot/mobile 复账主键。
# 设计约束 05：source=software_proof、not_proven 与三个 false flag 必须跨 gate 延续。
# 设计约束 06：pending/overdue/escalated/ready 仍不是采购、安装、HIL 或 resolved。
# 设计约束 07：blocked 是唯一 fail-closed 输出状态，所有输入异常都收敛到 blocked。
# 设计约束 08：缺 source alignment、缺 packet、缺 required material 都必须 blocked。
# 设计约束 09：success/control/HIL/installed-sensor/O5 external proof claim 都必须 blocked。
# 设计约束 10：PR #5 thread resolved claim 必须 blocked，除非 live reviewer material 另证。
# 设计约束 11：本 gate 不读取 ROS graph、GitHub 写接口、serial/UART、硬件或网络。
# 设计约束 12：输出 summary 只给 Robot/mobile/Product 白名单字段。
# 设计约束 13：自由文本必须先脱敏再输出，避免 raw artifact 或本机路径泄漏。
# 设计约束 14：代码注释保持中文，解释 fail-closed 原因和证据边界。
# 设计约束 15：CLI --help 不依赖 ROS2、Docker、硬件、网络或 GitHub。
# 设计约束 16：状态名固定为 tech-plan 枚举，避免 UI 和 rg 围栏漂移。
# 设计约束 17：required material acknowledgement 不是材料正文，不可作为真实 proof。
# 设计约束 18：ready_for_reviewer_followup_not_proven 只表示可给 reviewer 继续跟进。
# 设计约束 19：本 gate 不更新 OKR、sprint closeout、vendor 文件或 GitHub thread。
# 设计约束 20：最终 artifact 会再过一次输出安全扫描。

BOUNDARY_NOTE = (
    "pr5_mandatory_sensor_material_followup_escalation_status; "
    "software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate; "
    "pr5_mandatory_sensor_source_alignment; "
    "software_proof_docker_pr5_mandatory_sensor_source_alignment_gate; "
    "source=software_proof; software_proof; hardware_material_pending; not_proven; "
    "safe_to_control=false; delivery_success=false; primary_actions_enabled=false; "
    "pending; overdue; escalated; blocked; ready_for_reviewer_followup_not_proven; "
    "PRRT_kwDOSWB9286CJ3tX"
)

UNSAFE_COPY_PATTERNS = (
    re.compile(r"(?i)\bAuthorization\s*:"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._-]+"),
    re.compile(r"(?i)\b(OSS_ACCESS_KEY|AK/SK|access_key|secret|token|password|private_key)\b"),
    re.compile(r"(?i)\b/Users/[^\\s`]+"),
    re.compile(r"(?i)\b/dev/(tty|serial|cu\.)[^\\s`]*"),
    re.compile(r"(?i)\b/cmd_vel\b"),
    re.compile(r"(?i)\b(raw|complete)\s+artifact(s)?\b"),
    re.compile(r"(?i)\bchecksum\b"),
    re.compile(r"(?i)\bTraceback\b"),
    re.compile(r"(?i)\bpostgres(ql)?://|mysql://|redis://|amqp://|mongodb://"),
)

FORBIDDEN_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(control|primary actions?)\s+(enabled|allowed|authorized)\b"),
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|verified|proven)\b"),
    re.compile(r"(?i)\b(real\s+)?HIL\s+(pass|passed|complete|completed|verified|proven)\b"),
    re.compile(r"(?i)\b(2D\s+LiDAR|LiDAR|ToF).{0,64}\b(installed|wired|mounted|calibrated|procured|purchased|validated|proven)\b"),
    re.compile(r"(?i)\binstalled[-_ ]sensor\s+(proof|claim|material|evidence)\b"),
    re.compile(r"(?i)\b(Objective\s*5|O5)\s+external\s+proof\b"),
    re.compile(r"(?i)\bpublic\s+HTTPS/TLS\s+proof\b"),
    re.compile(r"(?i)\b4G/SIM\s+proof\b"),
    re.compile(r"(?i)\bOSS/CDN\s+live\s+traffic\b"),
    re.compile(r"(?i)\bPRRT_kwDOSWB9286CJ3tX.{0,48}\b(resolved|closed)\b"),
    re.compile(r"(?i)\bPR\s*#?5\s+(review\s+thread|reviewer)?.{0,48}\b(resolved|closed|resolution\s+complete)\b"),
)


def _utc_now() -> str:
    # UTC 时间方便不同 PC/Docker 主机按字面序复核 evidence。
    return datetime.now(timezone.utc).isoformat()


def _encoded(value: Any) -> str:
    # 安全扫描用稳定 JSON，覆盖嵌套字段和值。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 输入错误不抛 traceback 给用户，而是生成 blocked artifact。
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
    # 字符串化 JSON 不展开，避免 raw body 伪装成 safe wrapper。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # 多来源字段取第一个非空文本，再交给脱敏 helper。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 64) -> list[str]:
    # 列表字段只保留短文本，不复制完整材料对象。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                text = _first_text(item.get("name"), item.get("material"), item.get("id"), item.get("ref"), item.get("title"))
            else:
                text = _first_text(item)
            safe = material_pack._safe_text(text).strip()
            if safe:
                items.append(safe)
        return items
    if isinstance(value, dict):
        return [material_pack._safe_text(key) for key, item in value.items() if bool(item)]
    if value in (None, ""):
        return []
    safe = material_pack._safe_text(value).strip()
    return [safe] if safe else []


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归已知 safe key，不采信任意 raw diagnostics。
    candidates = [payload]
    for key in (
        "pr5_mandatory_sensor_source_alignment",
        "pr5_mandatory_sensor_source_alignment_summary",
        "robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "review_summary",
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
    # schema 命中时优先使用嵌套 source alignment safe object。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _packet_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # packet 只接受固定 wrapper，防止 raw material bundle 被误读。
    candidates = [payload]
    for key in (
        "pr5_mandatory_sensor_material_followup_packet",
        "material_followup_packet",
        "safe_material_followup_packet",
        "followup_packet",
        "follow_up_packet",
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
    # 有 policy schema 时优先；无 schema 时允许最小 safe packet 直传。
    for candidate in _packet_candidates(payload):
        if str(candidate.get("schema", "")).strip() == POLICY_SCHEMA:
            return candidate
    return payload


def _safe_ref_from(payload: dict[str, Any]) -> str:
    # evidence_ref 允许出现在 safe_copy / owner_handoff / nested summary 中。
    safe_copy = _dict(payload, "safe_copy")
    owner_handoff = _dict(payload, "owner_handoff")
    return material_pack._safe_ref(
        _first_text(
            payload.get("safe_evidence_ref"),
            payload.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            owner_handoff.get("safe_evidence_ref"),
            owner_handoff.get("evidence_ref"),
            default="",
        )
    )


def _source_status(source: dict[str, Any], load_issue: str) -> dict[str, str]:
    # 上游 schema、capability 和 boundary 必须同时匹配 source-alignment。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("proof_boundary"), source.get("boundary")))
    capability = material_pack._safe_text(_first_text(source.get("capability"), source.get("source_capability"), default=SOURCE_CAPABILITY))
    if schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY and capability == SOURCE_CAPABILITY:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_alignment_ready(source: dict[str, Any]) -> str:
    # source alignment 的 ready 状态来自 alignment_status/status/safe_copy。
    safe_copy = _dict(source, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            source.get("alignment_status"),
            source.get("status"),
            safe_copy.get("alignment_status"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _is_safe_surface(payload: dict[str, Any], require_hardware_pending: bool = True) -> bool:
    # 下游只接受 software_proof/not_proven/false flags，避免弱化边界。
    encoded = _encoded(payload)
    has_hardware_pending = ("hardware_material_pending" in encoded) if require_hardware_pending else True
    return (
        payload.get("source") == "software_proof"
        and "software_proof" in encoded
        and "not_proven" in encoded
        and has_hardware_pending
        and payload.get("safe_to_control") is False
        and payload.get("delivery_success") is False
        and payload.get("primary_actions_enabled") is False
    )


def _has_true_control_flag(value: Any) -> bool:
    # 布尔 true 比自由文本更危险，递归阻断。
    if isinstance(value, dict):
        if value.get("safe_to_control") is True or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
        return any(_has_true_control_flag(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_true_control_flag(item) for item in value)
    return False


def _has_unsafe_copy(value: Any) -> bool:
    # unsafe copy 阻断凭证、raw artifact、本机路径和低层控制暴露。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in UNSAFE_COPY_PATTERNS)


def _has_forbidden_claim(value: Any) -> bool:
    # checklist 允许材料类别名；这里阻断“已完成/已证明/已 resolved”语义。
    encoded = _encoded(value)
    return _has_true_control_flag(value) or any(pattern.search(encoded) for pattern in FORBIDDEN_CLAIM_PATTERNS)


def _material_key(value: str) -> str:
    # 类别匹配忽略大小写、空格、短横线和下划线，适配人工 packet。
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _packet_status(packet: dict[str, Any]) -> str:
    # status 是本 gate 主枚举，未知值进入 blocked。
    safe_copy = _dict(packet, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            packet.get("followup_status"),
            packet.get("status"),
            packet.get("due_state"),
            safe_copy.get("followup_status"),
            safe_copy.get("status"),
            safe_copy.get("due_state"),
            default="blocked",
        )
    )


def _packet_material_status(packet: dict[str, Any]) -> dict[str, Any]:
    # packet 只确认 required material 类别已纳入跟进，不承载真实材料正文。
    safe_copy = _dict(packet, "safe_copy")
    accepted: list[str] = []
    for key in (
        "accepted_materials",
        "accepted_material_refs",
        "required_materials_acknowledged",
        "followup_materials",
        "followup_material_refs",
        "safe_material_refs",
        "safe_required_materials",
    ):
        accepted.extend(_safe_list(packet.get(key) or safe_copy.get(key)))
    checklist = packet.get("followup_checklist") or packet.get("required_materials_checklist") or safe_copy.get("followup_checklist")
    if isinstance(checklist, list):
        for item in checklist:
            if isinstance(item, dict) and item.get("status") in {"accepted", "pending", "overdue", "escalated", "acknowledged", "accepted_not_proven", "ready"}:
                accepted.extend(_safe_list(item))
    accepted_keys = {_material_key(item) for item in accepted}
    required_by_key = {_material_key(item): item for item in REQUIRED_MATERIALS}
    accepted_required = [required for key, required in required_by_key.items() if key in accepted_keys]
    missing = _safe_list(packet.get("missing_materials") or safe_copy.get("missing_materials"))
    if not missing:
        missing = [required for key, required in required_by_key.items() if key not in accepted_keys]
    rejected = _safe_list(packet.get("rejected_materials") or safe_copy.get("rejected_materials") or packet.get("unsafe_material_refs"))
    return {
        "status": "accepted" if not missing and not rejected else ("rejected" if rejected else "missing"),
        "required_materials": list(REQUIRED_MATERIALS),
        "accepted_materials": accepted_required,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "accepted_count": len(accepted_required),
        "required_count": len(REQUIRED_MATERIALS),
        "is_complete": not missing and not rejected and len(accepted_required) == len(REQUIRED_MATERIALS),
    }


def _same_ref_required(source: dict[str, Any], packet: dict[str, Any]) -> Any:
    # 必须是真 JSON boolean true，字符串 true 不通过。
    source_safe = _dict(source, "safe_copy")
    packet_safe = _dict(packet, "safe_copy")
    source_value = source.get("same_evidence_ref_required", source_safe.get("same_evidence_ref_required", True))
    packet_value = packet.get("same_evidence_ref_required", packet_safe.get("same_evidence_ref_required", True))
    return source_value if source_value is not True else packet_value


def _decision(
    source_load_issue: str,
    packet_load_issue: str,
    source_state: dict[str, str],
    source_ready_status: str,
    packet_status: str,
    requested_ref: str,
    source_ref: str,
    packet_ref: str,
    same_ref_required: Any,
    source_safe: bool,
    packet_safe: bool,
    unsafe_copy: bool,
    forbidden_claim: bool,
    material_status: dict[str, Any],
) -> tuple[str, list[str], int]:
    # fail-closed 顺序固定，先来源，再证据主键、安全边界、材料完整性。
    if source_load_issue:
        return "blocked", [source_load_issue], 2
    if source_state["schema_status"] != "supported":
        return "blocked", ["missing_or_unsupported_pr5_mandatory_sensor_source_alignment"], 2
    if packet_load_issue:
        return "blocked", [packet_load_issue], 3
    if packet_status not in ALLOWED_FOLLOWUP_STATUSES or packet_status == "blocked":
        return "blocked", ["unsupported_or_blocked_followup_status"], 3
    if not (requested_ref or source_ref or packet_ref):
        return "blocked", ["missing_safe_evidence_ref"], 4
    refs = [ref for ref in (requested_ref, source_ref, packet_ref) if ref]
    if len(set(refs)) > 1:
        return "blocked", ["source_packet_evidence_ref_mismatch"], 4
    if same_ref_required is not True:
        return "blocked", ["same_evidence_ref_required_not_boolean_true"], 4
    if not source_safe:
        return "blocked", ["source_alignment_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if not packet_safe:
        return "blocked", ["material_followup_packet_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if unsafe_copy:
        return "blocked", ["unsafe_copy_detected"], 5
    if forbidden_claim:
        return "blocked", ["success_control_hil_installed_sensor_o5_or_pr_resolution_claim_detected"], 5
    if not source_ready_status.endswith("not_proven"):
        return "blocked", ["source_alignment_not_ready_not_proven"], 2
    if material_status["rejected_materials"]:
        return "blocked", ["material_followup_packet_contains_rejected_or_unsafe_material_refs"], 5
    if material_status["missing_materials"] or not material_status["is_complete"]:
        return "blocked", ["material_followup_packet_missing_required_materials"], 3
    return packet_status, [f"followup_status_{packet_status}_not_proven"], 0


def _next_required_evidence(state: str, evidence_ref: str, material_status: dict[str, Any], reasons: list[str]) -> list[str]:
    # 下一步是人工补真实材料，不是机器人控制命令。
    ref = evidence_ref or "<same_evidence_ref>"
    if state in {"pending", "overdue", "escalated", "ready_for_reviewer_followup_not_proven"}:
        return [
            f"keep PR #5 material follow-up state={state} for evidence_ref={ref} without enabling controls",
            "collect real 2D LiDAR SKU/source/receipt/procurement material",
            "collect real ToF SKU/source/receipt/procurement material",
            "collect mounting, wiring, power-budget, calibration, HIL-entry, operator HIL report, and reviewer follow-up material outside this gate",
            f"keep PR thread {THREAD_ID} hardware_material_pending until reviewer resolution evidence exists",
        ]
    missing = [f"provide safe material follow-up acknowledgement: {name} at evidence_ref={ref}" for name in material_status["missing_materials"]]
    return missing or [f"rerun {CAPABILITY} with safe source alignment and packet for evidence_ref={ref}", *reasons]


def _owner_escalation(state: str, evidence_ref: str, reasons: list[str], next_required_evidence: list[str]) -> dict[str, Any]:
    # escalation 只路由 Hardware/Product/reviewer，不给机器人控制建议。
    return {
        "primary_owner": "Hardware Infra Engineer",
        "supporting_owners": ["Product Manager / OKR Owner", "Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
        "followup_status": state,
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "evidence_ref": evidence_ref or "<same_evidence_ref>",
        "thread_id": THREAD_ID,
        "hardware_material_status": "hardware_material_pending",
        "escalate": state in {"overdue", "escalated"},
        "ready_for_reviewer_followup": state == "ready_for_reviewer_followup_not_proven",
        "blocked": state == "blocked",
        "reasons": reasons,
        "next_required_evidence": next_required_evidence,
        "source": "software_proof",
        "not_proven": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # commands 只覆盖 PC evidence gate，不包含 ROS、串口、GitHub 写接口或网络命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        "python3 pc-tools/evidence/pr5_mandatory_sensor_source_alignment.py --summary-output <source_alignment_summary.json>",
        f"python3 pc-tools/evidence/pr5_mandatory_sensor_material_followup_escalation_status.py --source-alignment-json <source_alignment_summary.json> --material-followup-json <safe_material_followup_packet.json> --evidence-ref {ref}",
        "keep source=software_proof, hardware_material_pending, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false",
    ]


def _non_access_scope() -> list[str]:
    # 明确不可访问范围，避免把本 gate 误读为现场 proof。
    return [
        "ros_graph",
        "github_write_or_thread_resolution",
        "serial_uart",
        "wave_rover_runtime",
        "real_2d_lidar",
        "real_tof",
        "sensor_driver_runtime",
        "hil",
        "field_run",
        "objective_5_external_infrastructure",
        "network",
        "delivery_execution",
        "raw_vendor_files",
    ]


def _lineage(source: dict[str, Any], packet: dict[str, Any]) -> dict[str, str]:
    # lineage 只复制短字段，不把完整 source/packet 搬进 summary。
    return {
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": material_pack._safe_text(source.get("schema", "")),
        "source_alignment_status": _source_alignment_ready(source),
        "source_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("proof_boundary"), source.get("boundary"))),
        "packet_schema": material_pack._safe_text(packet.get("schema", "")),
        "packet_status": _packet_status(packet),
    }


def _safe_copy(
    state: str,
    evidence_ref: str,
    reasons: list[str],
    source_summary: dict[str, Any],
    packet_summary: dict[str, Any],
    material_status: dict[str, Any],
    lineage: dict[str, str],
    owner_escalation: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，只保留状态和缺口摘要。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "capability": CAPABILITY,
        "status": state,
        "followup_status": state,
        "allowed_followup_statuses": list(ALLOWED_FOLLOWUP_STATUSES),
        "followup_reasons": reasons,
        "thread_id": THREAD_ID,
        "evidence_boundary": BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_alignment": source_summary,
        "safe_material_followup_packet": packet_summary,
        "required_materials": list(REQUIRED_MATERIALS),
        "material_status": material_status,
        "safe_lineage": lineage,
        "owner_escalation": owner_escalation,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "source_boundary": SOURCE_BOUNDARY,
        "hardware_material_status": "hardware_material_pending",
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
    packet_summary: dict[str, Any],
    material_status: dict[str, Any],
    lineage: dict[str, str],
    owner_escalation: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是跨 Robot/Full-stack/Product 的稳定只读合同。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "capability": CAPABILITY,
        "evidence_boundary": BOUNDARY,
        "boundary": BOUNDARY,
        "status": state,
        "followup_status": state,
        "allowed_followup_statuses": list(ALLOWED_FOLLOWUP_STATUSES),
        "followup_reasons": reasons,
        "thread_id": THREAD_ID,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_alignment": source_summary,
        "safe_material_followup_packet": packet_summary,
        "required_materials": list(REQUIRED_MATERIALS),
        "material_status": material_status,
        "safe_lineage": lineage,
        "owner_escalation": owner_escalation,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "hardware_material_status": "hardware_material_pending",
        "not_proven": list(NOT_PROVEN),
        "software_proof": True,
        "non_access_scope": _non_access_scope(),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_pr5_mandatory_sensor_material_followup_escalation_status(
    source_alignment_json: str,
    material_followup_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 source-alignment safe 输出与 material follow-up packet，生成状态 artifact。"""

    source_payload, source_load_issue = _load_json(source_alignment_json, "source_alignment")
    packet_payload, packet_load_issue = _load_json(material_followup_json, "material_followup")
    source = _find_source(source_payload) if source_payload else {}
    packet = _find_packet(packet_payload) if packet_payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref)
    source_ref = _safe_ref_from(source)
    packet_ref = _safe_ref_from(packet)
    effective_ref = requested_ref or source_ref or packet_ref
    source_state = _source_status(source, source_load_issue)
    source_ready_status = _source_alignment_ready(source) if source else "missing"
    followup_status = _packet_status(packet) if packet else "blocked"
    same_ref_required = _same_ref_required(source, packet) if (source or packet) else True
    source_safe = bool(source) and _is_safe_surface(source, require_hardware_pending=True)
    packet_safe = bool(packet) and _is_safe_surface(packet, require_hardware_pending=True)
    material_status = _packet_material_status(packet) if packet else {
        "status": "missing",
        "required_materials": list(REQUIRED_MATERIALS),
        "accepted_materials": [],
        "missing_materials": list(REQUIRED_MATERIALS),
        "rejected_materials": [],
        "accepted_count": 0,
        "required_count": len(REQUIRED_MATERIALS),
        "is_complete": False,
    }
    unsafe_copy = bool(source_payload or packet_payload) and (_has_unsafe_copy(source) or _has_unsafe_copy(packet))
    forbidden_claim = bool(source_payload or packet_payload) and (_has_forbidden_claim(source) or _has_forbidden_claim(packet))

    state, reasons, exit_code = _decision(
        source_load_issue,
        packet_load_issue,
        source_state,
        source_ready_status,
        followup_status,
        requested_ref,
        source_ref,
        packet_ref,
        same_ref_required,
        source_safe,
        packet_safe,
        unsafe_copy,
        forbidden_claim,
        material_status,
    )
    lineage = _lineage(source, packet)
    source_summary = {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "capability": SOURCE_CAPABILITY,
        "alignment_status": source_ready_status,
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("proof_boundary"), source.get("boundary"))),
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "source_is_software_proof_not_proven": bool(source_safe),
        "hardware_material_status": "hardware_material_pending",
    }
    packet_summary = {
        "load_status": "blocked" if packet_load_issue else "loaded",
        "load_issue": packet_load_issue,
        "schema": material_pack._safe_text(packet.get("schema", "")),
        "source": material_pack._safe_text(packet.get("source", "")),
        "followup_status": followup_status,
        "safe_evidence_ref": packet_ref,
        "evidence_ref": packet_ref,
        "packet_is_software_proof_not_proven": bool(packet_safe),
        "unsafe_copy": bool(unsafe_copy),
        "forbidden_claim": bool(forbidden_claim),
        "hardware_material_status": "hardware_material_pending",
    }
    next_required_evidence = _next_required_evidence(state, effective_ref, material_status, reasons)
    owner_escalation = _owner_escalation(state, effective_ref, reasons, next_required_evidence)
    rerun_commands = _rerun_commands(effective_ref)
    safe_copy = _safe_copy(
        state,
        effective_ref,
        reasons,
        source_summary,
        packet_summary,
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
        packet_summary,
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
        "followup_status": state,
        "allowed_followup_statuses": list(ALLOWED_FOLLOWUP_STATUSES),
        "followup_reasons": reasons,
        "thread_id": THREAD_ID,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "source_alignment": source_summary,
        "safe_material_followup_packet": packet_summary,
        "required_materials": list(REQUIRED_MATERIALS),
        "material_status": material_status,
        "safe_lineage": lineage,
        "owner_escalation": owner_escalation,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "pr5_mandatory_sensor_material_followup_escalation_status_summary": summary,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "hardware_material_status": "hardware_material_pending",
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
    if _has_unsafe_copy(artifact) or _has_unsafe_copy(summary) or _has_forbidden_claim(artifact) or _has_forbidden_claim(summary):
        # 最终防线：输出仍含禁词时强制 blocked，并保持所有控制旗标 false。
        artifact["status"] = "blocked"
        artifact["followup_status"] = "blocked"
        summary["status"] = "blocked"
        summary["followup_status"] = "blocked"
        artifact["followup_reasons"] = ["final_output_safety_scan_failed"]
        summary["followup_reasons"] = ["final_output_safety_scan_failed"]
        artifact["pr5_mandatory_sensor_material_followup_escalation_status_summary"] = summary
        artifact[ROBOT_ALIAS] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
        exit_code = 5
    return artifact, summary, exit_code


def write_json(payload: dict[str, Any], output: str) -> None:
    # 写文件只生成软件证明，不表示真实材料到位。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，便于 PC、Docker 和 focused unittest 复跑。
    parser = argparse.ArgumentParser(description="Generate PR #5 mandatory sensor material follow-up escalation status software-proof gate.")
    parser.add_argument("--source-alignment-json", required=True, help="previous pr5_mandatory_sensor_source_alignment artifact, summary, Robot alias, or wrapper JSON")
    parser.add_argument("--material-followup-json", required=True, help="safe material follow-up packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref shared by source alignment and follow-up packet")
    parser.add_argument("--output", default="", help="optional artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_pr5_mandatory_sensor_material_followup_escalation_status(
        args.source_alignment_json,
        args.material_followup_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pr5_mandatory_sensor_material_followup_escalation_status: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"followup_escalation_status_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"followup_status: {artifact['followup_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
