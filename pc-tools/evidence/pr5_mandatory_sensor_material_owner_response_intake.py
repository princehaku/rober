#!/usr/bin/env python3
"""生成 PR #5 mandatory sensor material owner-response intake gate。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pr5_mandatory_sensor_material_followup_escalation_status as followup_gate
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.pr5_mandatory_sensor_material_owner_response_intake.v1"
SUMMARY_SCHEMA = "trashbot.pr5_mandatory_sensor_material_owner_response_intake_summary.v1"
RESPONSE_SCHEMA = "trashbot.pr5_mandatory_sensor_material_owner_response_packet.v1"
ROBOT_ALIAS = "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary"
SCHEMA_VERSION = 1
CAPABILITY = "pr5_mandatory_sensor_material_owner_response_intake"
SOURCE_CAPABILITY = followup_gate.CAPABILITY
BOUNDARY = "software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate"
SOURCE_BOUNDARY = followup_gate.BOUNDARY
THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"

DECISIONS = ("accepted", "missing", "rejected", "unsafe", "blocked")

REQUIRED_RESPONSE_REFS = (
    "2D LiDAR SKU/source/receipt/procurement material owner response",
    "ToF SKU/source/receipt/procurement material owner response",
    "mounting/installation material owner response",
    "wiring and power-budget material owner response",
    "calibration plan or calibration result owner response",
    "HIL-entry material owner response",
    "operator HIL report owner response",
    "PR #5 reviewer follow-up or reviewer resolution owner response",
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
    followup_gate.SCHEMA,
    followup_gate.SUMMARY_SCHEMA,
    "trashbot.robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary.v1",
}

# 设计约束 01：本 gate 只消费上一轮 follow-up escalation safe summary。
# 设计约束 02：owner response packet 只允许 safe refs 和状态，不允许 raw artifact body。
# 设计约束 03：accepted 只表示 owner response 元数据齐全，不证明材料真实存在。
# 设计约束 04：missing/rejected/unsafe/blocked 都保留 hardware_material_pending。
# 设计约束 05：同一 safe evidence_ref 是 PC/Robot/mobile 复账主键。
# 设计约束 06：raw body、凭证、URL、路径、ROS/control/serial/UART/HIL/pass 文案都 fail closed。
# 设计约束 07：PRRT_kwDOSWB9286CJ3tX resolved/closed 文案必须 fail closed。
# 设计约束 08：本 gate 不读 ROS graph、串口、WAVE ROVER runtime、GitHub 写接口或网络。
# 设计约束 09：输出 summary 只给 Robot/mobile/Product 白名单字段。
# 设计约束 10：技术注释保持中文，说明证据边界而不是重复代码含义。
# 设计约束 11：vendor 文件只作为来源边界，不作为本 gate 的真实材料输入。
# 设计约束 12：所有 true 控制/成功旗标都递归阻断。
# 设计约束 13：最终 artifact 再做一次安全扫描，避免新增字段穿透。
# 设计约束 14：CLI --help 不依赖 ROS2、Docker、硬件、网络或 GitHub。
# 设计约束 15：决策枚举固定为 accepted/missing/rejected/unsafe/blocked。
# 设计约束 16：safe notes 允许短文本，但先脱敏并禁止底层参数。
# 设计约束 17：material refs 是引用标签，不是采购、安装、接线、标定或 HIL proof。
# 设计约束 18：reviewer next step 是人工路由，不是 PR resolved claim。
# 设计约束 19：本 gate 不更新 OKR、sprint closeout、vendor 文件或 GitHub thread。
# 设计约束 20：缺上一轮 safe summary 时不降级使用 raw owner packet。

BOUNDARY_NOTE = (
    "pr5_mandatory_sensor_material_owner_response_intake; "
    "software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate; "
    "pr5_mandatory_sensor_material_followup_escalation_status; "
    "software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate; "
    "source=software_proof; software_proof; hardware_material_pending; not_proven; "
    "safe_to_control=false; delivery_success=false; primary_actions_enabled=false; "
    "accepted; missing; rejected; unsafe; blocked; PRRT_kwDOSWB9286CJ3tX; "
    "docs/vendor/VENDOR_INDEX.md"
)

RAW_BODY_KEYS = {
    "raw_artifact",
    "raw_artifacts",
    "raw_body",
    "artifact_body",
    "artifact_bodies",
    "complete_artifact",
    "complete_artifacts",
    "full_artifact",
    "raw_payload",
    "raw_log",
    "raw_logs",
    "raw_review_body",
}

UNSAFE_COPY_PATTERNS = (
    re.compile(r"(?i)\bAuthorization\s*:"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._-]+"),
    re.compile(r"(?i)\b(OSS_ACCESS_KEY|AK/SK|access_key|secret|token|password|private_key)\b"),
    re.compile(r"(?i)\bhttps?://[^\\s`]+(?:signature|expires|X-Amz|token|OSSAccessKeyId)[^\\s`]*"),
    re.compile(r"(?i)\b/Users/[^\\s`]+"),
    re.compile(r"(?i)\b/(private|var|tmp|Volumes)/[^\\s`]+"),
    re.compile(r"(?i)\b/dev/(tty|serial|cu\.)[^\\s`]*"),
    re.compile(r"(?i)\b(cmd_vel|/cmd_vel|/odom|/imu/data|/battery)\b"),
    re.compile(r"(?i)\b(serial|uart)\s*(port|path|device)?\s*[:=]\s*[^,;}\\s]+"),
    re.compile(r"(?i)\b(baud|baudrate|baud_rate)\s*[:=]\s*[0-9]{4,6}\b"),
    re.compile(r"(?i)\b(115200|230400|921600)\b"),
    re.compile(r"(?i)\b(WAVE\s*ROVER).{0,80}\b(wheel|track|diameter|wheelbase|pid|pwm|encoder|parameter|param)\b"),
    re.compile(r"(?i)\b(raw|complete|full)\s+artifact(s)?\b"),
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
    re.compile(r"(?i)\b(hil_pass|pass_copy|HIL\s+copy)\b"),
    re.compile(r"(?i)\b(2D\s+LiDAR|LiDAR|ToF).{0,64}\b(installed|wired|mounted|calibrated|procured|purchased|validated|proven)\b"),
    re.compile(r"(?i)\binstalled[-_ ]sensor\s+(proof|claim|material|evidence)\b"),
    re.compile(r"(?i)\b(Objective\s*5|O5)\s+external\s+proof\b"),
    re.compile(r"(?i)\bpublic\s+HTTPS/TLS\s+proof\b"),
    re.compile(r"(?i)\b4G/SIM\s+proof\b"),
    re.compile(r"(?i)\bOSS/CDN\s+live\s+traffic\b"),
    re.compile(r"(?i)\bPRRT_kwDOSWB9286CJ3tX.{0,64}\b(resolved|closed)\b"),
    re.compile(r"(?i)\bPR\s*#?5\s+(review\s+thread|reviewer)?.{0,64}\b(resolved|closed|resolution\s+complete)\b"),
)


def _utc_now() -> str:
    # UTC 让不同 Docker-only 主机生成的 artifact 能按字面时间复账。
    return datetime.now(timezone.utc).isoformat()


def _encoded(value: Any) -> str:
    # 安全扫描使用稳定 JSON，覆盖嵌套字段和值。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 输入不可读时生成 blocked artifact，而不是把 traceback 泄漏到 summary。
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
    # 多来源字段取第一个非空文本，再由 safe helper 处理。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 64) -> list[str]:
    # 列表只保留短标签；dict 只读 name/ref/status 这类元数据字段。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                text = _first_text(item.get("name"), item.get("material"), item.get("id"), item.get("ref"), item.get("title"), item.get("status"))
            else:
                text = _first_text(item)
            safe = material_pack._safe_text(text).strip()
            if safe:
                items.append(safe)
        return items
    if isinstance(value, dict):
        return [material_pack._safe_text(str(key)) for key, item in value.items() if bool(item)]
    if value in (None, ""):
        return []
    safe = material_pack._safe_text(value).strip()
    return [safe] if safe else []


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归已知 safe wrapper key，避免任意 raw diagnostics 被采信。
    candidates = [payload]
    for key in (
        "pr5_mandatory_sensor_material_followup_escalation_status",
        "pr5_mandatory_sensor_material_followup_escalation_status_summary",
        "robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary",
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
    # schema 命中时优先使用嵌套 follow-up safe object。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _response_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # owner response 只接受固定 wrapper，避免直接吞 raw material bundle。
    candidates = [payload]
    for key in (
        "pr5_mandatory_sensor_material_owner_response_packet",
        "owner_response_packet",
        "safe_owner_response_packet",
        "owner_response",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_response_candidates(value))
    return candidates


def _find_response(payload: dict[str, Any]) -> dict[str, Any]:
    # 有 response schema 时优先；无 schema 时允许最小 safe packet 直传。
    for candidate in _response_candidates(payload):
        if str(candidate.get("schema", "")).strip() == RESPONSE_SCHEMA:
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
    # 上游 schema、capability 和 boundary 必须同时匹配上一 rung。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("proof_boundary"), source.get("boundary")))
    capability = material_pack._safe_text(_first_text(source.get("capability"), source.get("source_capability"), default=SOURCE_CAPABILITY))
    if schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY and capability == SOURCE_CAPABILITY:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_followup_status(source: dict[str, Any]) -> str:
    # 上一 rung 必须不是 blocked，且仍是 not_proven 的 safe 跟进状态。
    safe_copy = _dict(source, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            source.get("followup_status"),
            source.get("status"),
            safe_copy.get("followup_status"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _is_safe_surface(payload: dict[str, Any], require_hardware_pending: bool = True) -> bool:
    # 下游只接受 software_proof/not_proven/false flags，避免弱化证据边界。
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


def _has_raw_body_key(value: Any) -> bool:
    # raw body key 一旦出现就说明输入不是 sanitized owner response packet。
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in RAW_BODY_KEYS:
                return True
            if _has_raw_body_key(item):
                return True
    if isinstance(value, list):
        return any(_has_raw_body_key(item) for item in value)
    return False


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
    # unsafe copy 阻断凭证、raw artifact、本机路径、ROS/control 和底层硬件细节。
    encoded = _encoded(value)
    return _has_raw_body_key(value) or any(pattern.search(encoded) for pattern in UNSAFE_COPY_PATTERNS)


def _has_forbidden_claim(value: Any) -> bool:
    # checklist 允许材料类别名；这里阻断“已完成/已证明/已 resolved”语义。
    encoded = _encoded(value)
    return _has_true_control_flag(value) or any(pattern.search(encoded) for pattern in FORBIDDEN_CLAIM_PATTERNS)


def _material_key(value: str) -> str:
    # 类别匹配忽略大小写、空格、短横线和下划线，适配人工 packet。
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _response_status(response: dict[str, Any]) -> str:
    # response status 是 owner 自报状态；未知值进入 blocked。
    safe_copy = _dict(response, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            response.get("response_status"),
            response.get("owner_response_status"),
            response.get("status"),
            safe_copy.get("response_status"),
            safe_copy.get("owner_response_status"),
            safe_copy.get("status"),
            default="blocked",
        )
    )


def _owner_identity(response: dict[str, Any]) -> dict[str, str]:
    # owner id/role 只作为路由元数据，不参与权限或验收证明。
    safe_copy = _dict(response, "safe_copy")
    return {
        "owner_id": material_pack._safe_text(_first_text(response.get("owner_id"), safe_copy.get("owner_id"), default="unknown_owner")),
        "owner_role": material_pack._safe_text(_first_text(response.get("owner_role"), response.get("role"), safe_copy.get("owner_role"), safe_copy.get("role"), default="unknown_role")),
    }


def _response_material_status(response: dict[str, Any]) -> dict[str, Any]:
    # material refs 是 safe 引用标签；missing/rejected 会决定输出枚举。
    safe_copy = _dict(response, "safe_copy")
    material_refs: list[str] = []
    for key in (
        "material_refs",
        "accepted_material_refs",
        "accepted_refs",
        "owner_material_refs",
        "safe_material_refs",
        "reviewer_material_refs",
    ):
        material_refs.extend(_safe_list(response.get(key) or safe_copy.get(key)))
    missing_refs = _safe_list(response.get("missing_refs") or response.get("missing_material_refs") or safe_copy.get("missing_refs"))
    rejected_refs = _safe_list(response.get("rejected_refs") or response.get("rejected_material_refs") or safe_copy.get("rejected_refs"))
    accepted_keys = {_material_key(item) for item in material_refs}
    required_by_key = {_material_key(item): item for item in REQUIRED_RESPONSE_REFS}
    accepted_required = [required for key, required in required_by_key.items() if key in accepted_keys]
    if not missing_refs:
        missing_refs = [required for key, required in required_by_key.items() if key not in accepted_keys]
    return {
        "required_refs": list(REQUIRED_RESPONSE_REFS),
        "material_refs": accepted_required,
        "missing_refs": missing_refs,
        "rejected_refs": rejected_refs,
        "accepted_count": len(accepted_required),
        "required_count": len(REQUIRED_RESPONSE_REFS),
        "is_complete": not missing_refs and not rejected_refs and len(accepted_required) == len(REQUIRED_RESPONSE_REFS),
    }


def _reviewer_next_step(response: dict[str, Any]) -> str:
    # reviewer next step 是人工提示，不允许携带 resolved/closed 结论。
    safe_copy = _dict(response, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            response.get("reviewer_next_step"),
            response.get("next_reviewer_step"),
            safe_copy.get("reviewer_next_step"),
            safe_copy.get("next_reviewer_step"),
            default="collect_missing_owner_response_refs_not_proven",
        )
    )


def _safe_notes(response: dict[str, Any]) -> list[str]:
    # safe notes 只输出短文本；原始长材料正文应由安全扫描阻断。
    safe_copy = _dict(response, "safe_copy")
    notes = _safe_list(response.get("safe_notes") or response.get("notes") or safe_copy.get("safe_notes"), limit=16)
    return notes[:16]


def _same_ref_required(source: dict[str, Any], response: dict[str, Any]) -> Any:
    # 必须是真 JSON boolean true，字符串 true 不通过。
    source_safe = _dict(source, "safe_copy")
    response_safe = _dict(response, "safe_copy")
    source_value = source.get("same_evidence_ref_required", source_safe.get("same_evidence_ref_required", True))
    response_value = response.get("same_evidence_ref_required", response_safe.get("same_evidence_ref_required", True))
    return source_value if source_value is not True else response_value


def _decision(
    source_load_issue: str,
    response_load_issue: str,
    source_state: dict[str, str],
    source_followup_status: str,
    response_status: str,
    requested_ref: str,
    source_ref: str,
    response_ref: str,
    same_ref_required: Any,
    source_safe: bool,
    response_safe: bool,
    unsafe_copy: bool,
    forbidden_claim: bool,
    material_status: dict[str, Any],
) -> tuple[str, list[str], int]:
    # fail-closed 顺序固定，先上一 rung，再证据主键、安全边界、owner response 完整性。
    if source_load_issue:
        return "blocked", [source_load_issue], 2
    if source_state["schema_status"] != "supported":
        return "blocked", ["missing_or_unsupported_pr5_mandatory_sensor_material_followup_escalation_status"], 2
    if source_followup_status in {"blocked", "missing"}:
        return "blocked", ["source_followup_escalation_status_not_ready"], 2
    if response_load_issue:
        return "blocked", [response_load_issue], 3
    if response_status not in DECISIONS or response_status == "blocked":
        return "blocked", ["unsupported_or_blocked_owner_response_status"], 3
    if not (requested_ref or source_ref or response_ref):
        return "blocked", ["missing_safe_evidence_ref"], 4
    refs = [ref for ref in (requested_ref, source_ref, response_ref) if ref]
    if len(set(refs)) > 1:
        return "blocked", ["source_response_evidence_ref_mismatch"], 4
    if same_ref_required is not True:
        return "blocked", ["same_evidence_ref_required_not_boolean_true"], 4
    if not source_safe:
        return "blocked", ["source_followup_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if not response_safe:
        return "blocked", ["owner_response_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if unsafe_copy:
        return "unsafe", ["unsafe_copy_detected"], 5
    if forbidden_claim:
        return "unsafe", ["success_control_hil_installed_sensor_delivery_or_pr_resolution_claim_detected"], 5
    if response_status == "rejected" or material_status["rejected_refs"]:
        return "rejected", ["owner_response_contains_rejected_material_refs"], 5
    if response_status == "missing" or material_status["missing_refs"] or not material_status["is_complete"]:
        return "missing", ["owner_response_missing_required_material_refs"], 3
    return "accepted", ["owner_response_refs_accepted_not_proven"], 0


def _next_required_evidence(state: str, evidence_ref: str, material_status: dict[str, Any], reasons: list[str]) -> list[str]:
    # 下一步仍是人工补真实材料，不是机器人控制命令。
    ref = evidence_ref or "<same_evidence_ref>"
    if state == "accepted":
        return [
            f"review accepted owner-response refs for evidence_ref={ref} without claiming installed sensors",
            "collect real 2D LiDAR and ToF source, receipt, install, wiring, power, calibration, HIL-entry, and operator HIL materials outside this gate",
            f"keep PR thread {THREAD_ID} hardware_material_pending until reviewer resolution evidence exists",
        ]
    if state == "missing":
        return [f"provide missing safe owner response ref: {name} at evidence_ref={ref}" for name in material_status["missing_refs"]]
    if state == "rejected":
        return [f"replace rejected safe owner response ref: {name} at evidence_ref={ref}" for name in material_status["rejected_refs"]]
    if state == "unsafe":
        return [f"remove raw/control/hardware/success/resolution material from owner response packet for evidence_ref={ref}"]
    return [f"rerun {CAPABILITY} with follow-up summary and sanitized owner response packet for evidence_ref={ref}", *reasons]


def _owner_handoff(
    state: str,
    evidence_ref: str,
    owner_identity: dict[str, str],
    reviewer_next_step: str,
    reasons: list[str],
    next_required_evidence: list[str],
) -> dict[str, Any]:
    # handoff 只路由 Hardware/Product/reviewer，不给机器人控制建议。
    return {
        "primary_owner": "Hardware Infra Engineer",
        "supporting_owners": ["Product Manager / OKR Owner", "Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
        "owner_id": owner_identity["owner_id"],
        "owner_role": owner_identity["owner_role"],
        "decision": state,
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "evidence_ref": evidence_ref or "<same_evidence_ref>",
        "thread_id": THREAD_ID,
        "reviewer_next_step": reviewer_next_step,
        "hardware_material_status": "hardware_material_pending",
        "ready_for_review": state == "accepted",
        "blocked": state in {"blocked", "unsafe"},
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
        "python3 pc-tools/evidence/pr5_mandatory_sensor_material_followup_escalation_status.py --source-alignment-json <source_alignment_summary.json> --material-followup-json <safe_material_followup_packet.json>",
        f"python3 pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_intake.py --followup-summary-json <followup_escalation_status_summary.json> --owner-response-json <safe_owner_response_packet.json> --evidence-ref {ref}",
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
        "raw_artifact_bodies",
    ]


def _lineage(source: dict[str, Any], response: dict[str, Any]) -> dict[str, str]:
    # lineage 只复制短字段，不把完整 source/response 搬进 summary。
    return {
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": material_pack._safe_text(source.get("schema", "")),
        "source_followup_status": _source_followup_status(source),
        "source_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("proof_boundary"), source.get("boundary"))),
        "response_schema": material_pack._safe_text(response.get("schema", "")),
        "response_status": _response_status(response),
    }


def _safe_copy(
    state: str,
    evidence_ref: str,
    reasons: list[str],
    source_summary: dict[str, Any],
    response_summary: dict[str, Any],
    material_status: dict[str, Any],
    lineage: dict[str, str],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，只保留状态和缺口摘要。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "capability": CAPABILITY,
        "status": state,
        "decision": state,
        "allowed_decisions": list(DECISIONS),
        "decision_reasons": reasons,
        "thread_id": THREAD_ID,
        "evidence_boundary": BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "followup_escalation_status": source_summary,
        "safe_owner_response_packet": response_summary,
        "required_owner_response_refs": list(REQUIRED_RESPONSE_REFS),
        "material_status": material_status,
        "safe_lineage": lineage,
        "owner_handoff": owner_handoff,
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
    response_summary: dict[str, Any],
    material_status: dict[str, Any],
    lineage: dict[str, str],
    owner_handoff: dict[str, Any],
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
        "decision": state,
        "allowed_decisions": list(DECISIONS),
        "decision_reasons": reasons,
        "thread_id": THREAD_ID,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "followup_escalation_status": source_summary,
        "safe_owner_response_packet": response_summary,
        "required_owner_response_refs": list(REQUIRED_RESPONSE_REFS),
        "material_status": material_status,
        "safe_lineage": lineage,
        "owner_handoff": owner_handoff,
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


def build_pr5_mandatory_sensor_material_owner_response_intake(
    followup_summary_json: str,
    owner_response_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 follow-up safe summary 与 owner response packet，生成 intake artifact。"""

    source_payload, source_load_issue = _load_json(followup_summary_json, "followup_summary")
    response_payload, response_load_issue = _load_json(owner_response_json, "owner_response")
    source = _find_source(source_payload) if source_payload else {}
    response = _find_response(response_payload) if response_payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref)
    source_ref = _safe_ref_from(source)
    response_ref = _safe_ref_from(response)
    effective_ref = requested_ref or source_ref or response_ref
    source_state = _source_status(source, source_load_issue)
    source_followup_status = _source_followup_status(source) if source else "missing"
    response_status = _response_status(response) if response else "blocked"
    same_ref_required = _same_ref_required(source, response) if (source or response) else True
    source_safe = bool(source) and _is_safe_surface(source, require_hardware_pending=True)
    response_safe = bool(response) and _is_safe_surface(response, require_hardware_pending=True)
    material_status = _response_material_status(response) if response else {
        "required_refs": list(REQUIRED_RESPONSE_REFS),
        "material_refs": [],
        "missing_refs": list(REQUIRED_RESPONSE_REFS),
        "rejected_refs": [],
        "accepted_count": 0,
        "required_count": len(REQUIRED_RESPONSE_REFS),
        "is_complete": False,
    }
    owner_identity = _owner_identity(response) if response else {"owner_id": "unknown_owner", "owner_role": "unknown_role"}
    reviewer_next_step = _reviewer_next_step(response) if response else "collect_missing_owner_response_refs_not_proven"
    notes = _safe_notes(response) if response else []
    unsafe_copy = bool(source_payload or response_payload) and (_has_unsafe_copy(source_payload) or _has_unsafe_copy(response_payload))
    forbidden_claim = bool(source_payload or response_payload) and (_has_forbidden_claim(source_payload) or _has_forbidden_claim(response_payload))

    state, reasons, exit_code = _decision(
        source_load_issue,
        response_load_issue,
        source_state,
        source_followup_status,
        response_status,
        requested_ref,
        source_ref,
        response_ref,
        same_ref_required,
        source_safe,
        response_safe,
        unsafe_copy,
        forbidden_claim,
        material_status,
    )
    safe_response_notes = [] if (unsafe_copy or forbidden_claim) else notes
    safe_reviewer_next_step = "resubmit_sanitized_owner_response_refs_not_proven" if (unsafe_copy or forbidden_claim) else reviewer_next_step
    lineage = _lineage(source, response)
    source_summary = {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "capability": SOURCE_CAPABILITY,
        "followup_status": source_followup_status,
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("proof_boundary"), source.get("boundary"))),
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "source_is_software_proof_not_proven": bool(source_safe),
        "hardware_material_status": "hardware_material_pending",
    }
    response_summary = {
        "load_status": "blocked" if response_load_issue else "loaded",
        "load_issue": response_load_issue,
        "schema": material_pack._safe_text(response.get("schema", "")),
        "source": material_pack._safe_text(response.get("source", "")),
        "response_status": response_status,
        "safe_evidence_ref": response_ref,
        "evidence_ref": response_ref,
        "owner_id": owner_identity["owner_id"],
        "owner_role": owner_identity["owner_role"],
        "reviewer_next_step": safe_reviewer_next_step,
        "safe_notes": safe_response_notes,
        "packet_is_software_proof_not_proven": bool(response_safe),
        "unsafe_copy": bool(unsafe_copy),
        "forbidden_claim": bool(forbidden_claim),
        "hardware_material_status": "hardware_material_pending",
    }
    next_required_evidence = _next_required_evidence(state, effective_ref, material_status, reasons)
    owner_handoff = _owner_handoff(state, effective_ref, owner_identity, safe_reviewer_next_step, reasons, next_required_evidence)
    rerun_commands = _rerun_commands(effective_ref)
    safe_copy = _safe_copy(
        state,
        effective_ref,
        reasons,
        source_summary,
        response_summary,
        material_status,
        lineage,
        owner_handoff,
        next_required_evidence,
        rerun_commands,
    )
    summary = _summary_payload(
        state,
        effective_ref,
        reasons,
        source_summary,
        response_summary,
        material_status,
        lineage,
        owner_handoff,
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
        "decision": state,
        "allowed_decisions": list(DECISIONS),
        "decision_reasons": reasons,
        "thread_id": THREAD_ID,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "followup_escalation_status": source_summary,
        "safe_owner_response_packet": response_summary,
        "required_owner_response_refs": list(REQUIRED_RESPONSE_REFS),
        "material_status": material_status,
        "safe_lineage": lineage,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "pr5_mandatory_sensor_material_owner_response_intake_summary": summary,
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
        # 最终防线：输出仍含禁词时强制 unsafe，并保持所有控制旗标 false。
        artifact["status"] = "unsafe"
        artifact["decision"] = "unsafe"
        summary["status"] = "unsafe"
        summary["decision"] = "unsafe"
        artifact["decision_reasons"] = ["final_output_safety_scan_failed"]
        summary["decision_reasons"] = ["final_output_safety_scan_failed"]
        artifact["pr5_mandatory_sensor_material_owner_response_intake_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate PR #5 mandatory sensor material owner-response intake software-proof gate.")
    parser.add_argument("--followup-summary-json", required=True, help="previous pr5_mandatory_sensor_material_followup_escalation_status artifact, summary, Robot alias, or wrapper JSON")
    parser.add_argument("--owner-response-json", required=True, help="sanitized owner response packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref shared by follow-up summary and owner response packet")
    parser.add_argument("--output", default="", help="optional artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_pr5_mandatory_sensor_material_owner_response_intake(
        args.followup_summary_json,
        args.owner_response_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pr5_mandatory_sensor_material_owner_response_intake: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"owner_response_intake_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"decision: {artifact['decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
