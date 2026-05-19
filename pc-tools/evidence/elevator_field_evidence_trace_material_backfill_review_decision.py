#!/usr/bin/env python3
"""生成 elevator field evidence trace material backfill review decision artifact。

该 PC-only gate 只消费上一轮 material backfill intake 的 artifact、summary 或
Robot diagnostics safe alias，并把 accepted / missing / rejected 材料状态转换成
可供后续 handoff 使用的 review decision。它不读取 raw material、不访问 ROS/Nav2、
硬件、云或真实手机/browser，也不证明真实 route/elevator field pass。
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_SCHEMA = "trashbot.elevator_field_evidence_trace_material_backfill_review_decision.v1"
SUMMARY_SCHEMA = "trashbot.elevator_field_evidence_trace_material_backfill_review_decision_summary.v1"
SOURCE_ARTIFACT_SCHEMA = "trashbot.elevator_field_evidence_trace_material_backfill_intake.v1"
SOURCE_SUMMARY_SCHEMA = "trashbot.elevator_field_evidence_trace_material_backfill_intake_summary.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_elevator_field_evidence_trace_material_backfill_review_decision_gate"
SOURCE_BOUNDARY = "software_proof_docker_elevator_field_evidence_trace_material_backfill_intake_gate"

# rg 围栏依赖这些 literal；也让人工复核能一眼看到边界没有变宽。
BOUNDARY_NOTE = (
    "elevator_field_evidence_trace_material_backfill_review_decision; "
    "elevator_field_evidence_trace_material_backfill_intake; safe_evidence_ref; "
    "same_evidence_ref_required; source=software_proof; not_proven; "
    "delivery_success=false; primary_actions_enabled=false; "
    "needs_required_material_backfill_not_proven; "
    "ready_for_field_evidence_material_review_handoff_not_proven; "
    "real_elevator_door_state; real_delivery_result"
)

# required materials 沿用上一轮 intake；本 gate 只复核安全引用状态。
REQUIRED_ROUTE_ELEVATOR_MATERIALS = (
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_record",
    "real_nav2_or_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_field_task_record",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result",
)

# not_proven 清单必须覆盖真实现场、硬件、手机和外部云证明边界。
NOT_PROVEN = (
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime",
    "real_fixed_route_runtime",
    "real_field_task_record",
    "real_dropoff_or_cancel_completion",
    "real_delivery_success",
    "real_waverover_uart_hil",
    "real_phone_browser",
    "objective_5_external_proof",
    "delivery_success",
)

SOURCE_SCHEMAS = {SOURCE_ARTIFACT_SCHEMA, SOURCE_SUMMARY_SCHEMA}
SUPPORTED_INTAKE_STATUSES = {
    "needs_required_material_backfill_not_proven",
    "ready_for_material_review_not_proven",
}

# safe evidence_ref 是跨 artifact 对账主键，禁止路径、空白和弱占位符。
SAFE_REF_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
PLACEHOLDER_PATTERNS = (
    re.compile(r"(?i)\b(todo|tbd|placeholder|sample|example|dummy|fake|null|none)\b"),
    re.compile(r"^<[^>]+>$"),
)

# 输入里出现 raw path、凭证、控制 topic、transport 或 traceback 都必须 fail closed。
FORBIDDEN_COPY = (
    "Authorization",
    "OSS_ACCESS_KEY",
    "OSS_SECRET",
    "access_key",
    "secret",
    "token",
    "password",
    "postgres://",
    "postgresql://",
    "mysql://",
    "redis://",
    "amqp://",
    "mongodb://",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "serial",
    "UART",
    "baudrate",
    "baud_rate",
    "WAVE ROVER",
    "Traceback",
    "checksum",
    "complete artifact",
    "raw robot response",
)

# 成功和控制动作语义只能来自真实验收；本 gate 看到即阻断。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\b(real_)?route[_ -]?elevator[_ -]?field[_ -]?pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(real_)?route[_ -]?elevator[_ -]?field\s+passed\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bcancel\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action)\b"),
)

RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# blocked artifact 也要脱敏，避免“失败证据”复制敏感输入。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\bOSS_[A-Z_]*(ACCESS|SECRET)[A-Z_]*\b\s*[:=]\s*[^,\s]+"), "OSS_KEY=[REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_RATE]"),
    (re.compile(r"(?i)\bserial\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bUART\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bWAVE\s+ROVER\b"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"), r"\1[REDACTED_PATH]"),
    (re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 便于 PC 与 Docker-only 证据按时间线排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，summary 不回显危险原文。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线；前置 unsafe 判定仍负责 fail closed。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _encoded(value: Any) -> str:
    # unsafe 扫描覆盖嵌套键和值；不可编码时退回安全文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _unsafe_copy(value: Any) -> bool:
    # 禁止词和成功/控制语义必须在脱敏前阻断，不能清洗后放行。
    encoded = _encoded(value)
    forbidden = any(token in encoded for token in FORBIDDEN_COPY)
    raw_path = any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)
    success = any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)
    if isinstance(value, dict):
        success = success or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True
    return forbidden or raw_path or success


def _resolve_source_path(source: str) -> tuple[str, str]:
    # 支持 file:/env: 包装；source path 只用于读取，不进入 summary。
    text = str(source or "").strip()
    if text.startswith("file:"):
        return text.removeprefix("file:"), "file_source"
    if text.startswith("env:"):
        name = text.removeprefix("env:").strip()
        if not name:
            return "", "env_source_name_missing"
        value = os.environ.get(name, "").strip()
        if not value:
            return "", "env_source_missing"
        return value.removeprefix("file:"), "env_source"
    return text, "path_source"


def _load_json(source: str) -> tuple[dict[str, Any], str, str]:
    # 缺输入、坏 JSON、非 object 都落成 blocked artifact，便于自动化复盘。
    path, source_style = _resolve_source_path(source)
    if not path:
        return {}, "material_backfill_intake_not_provided", source_style
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "material_backfill_intake_missing", source_style
    except json.JSONDecodeError:
        return {}, "material_backfill_intake_bad_json", source_style
    except (OSError, UnicodeDecodeError):
        return {}, "material_backfill_intake_read_error", source_style
    if not isinstance(payload, dict):
        return {}, "material_backfill_intake_not_object", source_style
    return payload, "", source_style


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # wrapper 字段必须是 object；字符串化 JSON 不能伪装可信 summary。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、diagnostics 和 safe_copy 字段位置不同，取首个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 wrapper，避免任意 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "elevator_field_evidence_trace_material_backfill_intake",
        "elevator_field_evidence_trace_material_backfill_intake_summary",
        "robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary",
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


def _find_source_intake(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中时优先返回上一轮 intake；否则保留顶层用于 unsupported 诊断。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _safe_ref(value: Any) -> str:
    # review decision 不做 basename 降级；路径形态必须在安全状态中拒绝。
    return _safe_text(value).strip()


def _valid_safe_ref(ref: str) -> bool:
    # safe_evidence_ref 必须是短 token，不能是路径、URL、空白或占位。
    if not ref or "/" in ref or "\\" in ref or ref.startswith(("file:", "env:")):
        return False
    if any(pattern.search(ref) for pattern in PLACEHOLDER_PATTERNS):
        return False
    return bool(SAFE_REF_PATTERN.match(ref))


def _source_ref(source: dict[str, Any]) -> str:
    # safe_copy 和 diagnostics wrapper 都可能承载同一个 evidence_ref。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return _safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _source_status_text(source: dict[str, Any]) -> str:
    # intake_status 是上游主状态；status 仅用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("intake_status"),
            source.get("status"),
            safe_copy.get("intake_status"),
            safe_copy.get("status"),
            default="",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 弱类型字符串 true 不能通过，必须保持 JSON boolean true。
    for candidate in (source, _dict(source, "safe_copy"), _dict(source, "robot_diagnostics_summary"), _dict(source, "mobile_readonly_summary")):
        if "same_evidence_ref_required" in candidate:
            return candidate.get("same_evidence_ref_required")
    return None


def _same_ref_match(requested_ref: str, source_ref: str, same_ref_required: Any) -> dict[str, Any]:
    # CLI 和 source ref 都存在时必须一致；source ref 自身也必须安全。
    mismatches = []
    if requested_ref and source_ref and requested_ref != source_ref:
        mismatches.append(source_ref)
    if same_ref_required is not True:
        status = "weak_same_evidence_ref_required"
    elif not _valid_safe_ref(source_ref):
        status = "unsafe_or_missing_source_evidence_ref"
    elif requested_ref and not _valid_safe_ref(requested_ref):
        status = "unsafe_requested_evidence_ref"
    elif mismatches:
        status = "mismatch"
    else:
        status = "matched"
    return {
        "status": status,
        "expected_evidence_ref": requested_ref or source_ref,
        "refs": {"requested": requested_ref, "material_backfill_intake": source_ref},
        "mismatched_evidence_refs": mismatches,
        "same_evidence_ref_required": same_ref_required,
    }


def _list_material_entries(value: Any, *, names_only: bool = False) -> list[dict[str, Any]]:
    # 上游可能给字符串或 object；输出统一成 material/safe_ref 小对象。
    entries: list[dict[str, Any]] = []
    if not isinstance(value, list):
        return entries
    for item in value[:64]:
        if isinstance(item, dict):
            material = _safe_text(_first_text(item.get("material"), item.get("name"), item.get("category"), default="")).strip()
            safe_ref = _safe_text(_first_text(item.get("safe_ref"), item.get("ref"), item.get("evidence_ref"), item.get("safe_note"), default="")).strip()
        else:
            material = _safe_text(item).strip()
            safe_ref = "" if names_only else material
        if material:
            entries.append({"material": material, "safe_ref": safe_ref, "required": material in REQUIRED_ROUTE_ELEVATOR_MATERIALS})
    return entries


def _accepted_material_refs(source: dict[str, Any]) -> list[dict[str, Any]]:
    # accepted_material_refs 是上游 intake 的安全引用清单，不读取材料正文。
    safe_copy = _dict(source, "safe_copy")
    entries = _list_material_entries(source.get("accepted_material_refs") or safe_copy.get("accepted_material_refs"))
    by_material: dict[str, dict[str, Any]] = {}
    for entry in entries:
        material = entry["material"]
        if material not in by_material:
            by_material[material] = entry
    return [by_material[name] for name in REQUIRED_ROUTE_ELEVATOR_MATERIALS if name in by_material]


def _missing_materials(source: dict[str, Any]) -> list[dict[str, Any]]:
    # missing/rejected 只影响 review decision，不代表现场失败结论。
    safe_copy = _dict(source, "safe_copy")
    return _list_material_entries(source.get("missing_required_materials") or safe_copy.get("missing_required_materials"), names_only=True)


def _rejected_materials(source: dict[str, Any]) -> list[dict[str, Any]]:
    # rejected_material_refs 仍按安全摘要处理，不回显 raw artifact。
    safe_copy = _dict(source, "safe_copy")
    return _list_material_entries(source.get("rejected_material_refs") or safe_copy.get("rejected_material_refs"), names_only=True)


def _material_review_state(
    accepted: list[dict[str, Any]],
    missing: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
) -> dict[str, Any]:
    # 如果上游漏报 missing，这里按八类 required materials 再补一次缺口。
    accepted_names = {entry["material"] for entry in accepted if entry.get("safe_ref") and not _unsafe_copy(entry)}
    missing_by_name = {entry["material"]: entry for entry in missing if entry.get("material")}
    rejected_by_name = {entry["material"]: entry for entry in rejected if entry.get("material")}
    for material in REQUIRED_ROUTE_ELEVATOR_MATERIALS:
        if material not in accepted_names and material not in missing_by_name and material not in rejected_by_name:
            missing_by_name[material] = {"material": material, "safe_ref": "", "required": True, "reason": "source_intake_material_ref_missing"}
    return {
        "accepted_material_refs": accepted,
        "missing_required_materials": [missing_by_name[name] for name in REQUIRED_ROUTE_ELEVATOR_MATERIALS if name in missing_by_name],
        "rejected_material_refs": [rejected_by_name[name] for name in REQUIRED_ROUTE_ELEVATOR_MATERIALS if name in rejected_by_name],
        "accepted_count": len(accepted_names),
        "required_count": len(REQUIRED_ROUTE_ELEVATOR_MATERIALS),
        "all_required_materials_accepted": len(accepted_names) == len(REQUIRED_ROUTE_ELEVATOR_MATERIALS) and not missing_by_name and not rejected_by_name,
    }


def _source_contract(load_issue: str, source: dict[str, Any], source_style: str) -> dict[str, Any]:
    # 上游 intake 必须保持 schema、boundary、software_proof、not_proven 和 false flags。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded", "source_style": source_style}
    schema = _safe_text(source.get("schema", "")).strip()
    boundary = _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    source_kind = _safe_text(source.get("source", "")).strip()
    overall = _safe_text(source.get("overall_status", "")).strip()
    intake_status = _source_status_text(source)
    supported = (
        schema in SOURCE_SCHEMAS
        and boundary == SOURCE_BOUNDARY
        and source_kind == "software_proof"
        and overall == "not_proven"
        and intake_status in SUPPORTED_INTAKE_STATUSES
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )
    return {
        "load_status": "loaded",
        "load_issue": "",
        "schema_status": "supported" if supported else "unsupported",
        "source_style": source_style,
        "schema": schema,
        "evidence_boundary": boundary,
        "source": source_kind,
        "overall_status": overall,
        "intake_status": intake_status,
        "safe_evidence_ref": _source_ref(source),
        "unsafe_copy": bool(_unsafe_copy(source)) if source else False,
    }


def _review_decision_status(
    load_issue: str,
    source_contract: dict[str, Any],
    same_ref: dict[str, Any],
    unsafe: bool,
    material_state: dict[str, Any],
) -> tuple[str, list[str]]:
    # fail-closed 顺序固定：可读性、契约、安全、same-ref，再处理材料缺口。
    if load_issue:
        return "blocked_missing_material_backfill_intake_not_proven", [load_issue]
    if unsafe:
        return "blocked_unsafe_material_review_decision_not_proven", ["unsafe_material_review_decision_copy_detected"]
    if source_contract["schema_status"] != "supported":
        return "blocked_unsupported_material_backfill_intake_not_proven", ["unsupported_material_backfill_intake_contract"]
    if same_ref["status"] != "matched":
        return "blocked_evidence_ref_mismatch_not_proven", [same_ref["status"]]
    if material_state["missing_required_materials"] or material_state["rejected_material_refs"]:
        return "needs_required_material_backfill_not_proven", ["missing_or_rejected_required_materials_remain"]
    if not material_state["all_required_materials_accepted"]:
        return "needs_required_material_backfill_not_proven", ["required_material_acceptance_incomplete"]
    return "ready_for_field_evidence_material_review_handoff_not_proven", ["all_required_material_refs_ready_for_handoff"]


def _next_required_evidence(status: str, evidence_ref: str, material_state: dict[str, Any]) -> list[str]:
    # 下一步只描述 PC/owner handoff，不授权 Robot/mobile 控制动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_field_evidence_material_review_handoff_not_proven":
        return [
            f"prepare_field_evidence_material_review_handoff:{ref}",
            "keep software_proof/not_proven until real field materials are independently reviewed",
        ]
    if status == "needs_required_material_backfill_not_proven":
        names = [item["material"] for item in material_state["missing_required_materials"] + material_state["rejected_material_refs"]]
        return [f"backfill_or_repair_required_material_refs:{ref}:{','.join(names[:12])}"]
    if status == "blocked_evidence_ref_mismatch_not_proven":
        return [f"rerun_material_backfill_intake_with_same_safe_evidence_ref:{ref}"]
    if status == "blocked_unsafe_material_review_decision_not_proven":
        return ["regenerate_intake_summary_without_raw_paths_credentials_topics_transport_checksums_tracebacks_or_success_claims"]
    return [f"provide_supported_material_backfill_intake_summary:{ref}"]


def _owner_handoff(status: str, evidence_ref: str, material_state: dict[str, Any], next_required: list[str]) -> list[dict[str, Any]]:
    # owner_handoff 是人工复核元数据，不是机器人动作或现场执行指令。
    return [
        {
            "owner": "Autonomy Algorithm Engineer",
            "action": "prepare_material_review_handoff" if status == "ready_for_field_evidence_material_review_handoff_not_proven" else "repair_material_backfill_intake",
            "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
            "accepted_count": material_state["accepted_count"],
            "required_count": material_state["required_count"],
            "next_required_evidence": next_required,
            "status": "not_proven",
        }
    ]


def _rerun_commands(evidence_ref: str) -> list[str]:
    # commands 只包含 PC evidence gate，不包含 ROS、Nav2、硬件、云或手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/elevator_field_evidence_trace_material_backfill_intake.py --handoff-json <callback_review_handoff_summary.json> --material-packet-json <safe_material_packet.json> --evidence-ref {ref} --once-json",
        f"python3 pc-tools/evidence/elevator_field_evidence_trace_material_backfill_review_decision.py --material-backfill-intake-json <material_backfill_intake_summary.json> --evidence-ref {ref} --once-json",
        "keep source=software_proof, overall_status=not_proven, delivery_success=false, primary_actions_enabled=false",
    ]


def _safe_copy(
    status: str,
    evidence_ref: str,
    material_state: dict[str, Any],
    next_required: list[str],
    owner_handoff: list[dict[str, Any]],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不包含完整 source intake。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "review_decision": status,
        "source": "software_proof",
        "overall_status": "not_proven",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "accepted_material_refs": material_state["accepted_material_refs"],
        "missing_required_materials": material_state["missing_required_materials"],
        "rejected_material_refs": material_state["rejected_material_refs"],
        "next_required_evidence": next_required,
        "owner_handoff": owner_handoff,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_elevator_field_evidence_trace_material_backfill_review_decision(
    material_backfill_intake_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 material backfill intake，生成 metadata-only review decision。"""
    payload, load_issue, source_style = _load_json(material_backfill_intake_json)
    source = _find_source_intake(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    effective_ref = requested_ref or source_ref
    same_ref_required = _same_ref_required(source) if source else None
    same_ref = _same_ref_match(requested_ref, source_ref, same_ref_required)
    source_contract = _source_contract(load_issue, source, source_style)
    accepted = _accepted_material_refs(source) if source else []
    missing = _missing_materials(source) if source else []
    rejected = _rejected_materials(source) if source else []
    material_state = _material_review_state(accepted, missing, rejected)
    unsafe = bool(payload) and (_unsafe_copy(source) or _unsafe_copy(requested_ref) or any(_unsafe_copy(item) for item in accepted + missing + rejected))
    status, decision_reasons = _review_decision_status(load_issue, source_contract, same_ref, unsafe, material_state)
    next_required = _safe_value(_next_required_evidence(status, effective_ref, material_state))
    owner_handoff = _safe_value(_owner_handoff(status, effective_ref, material_state, next_required))
    rerun_commands = _safe_value(_rerun_commands(effective_ref))
    safe_copy = _safe_copy(status, effective_ref, material_state, next_required, owner_handoff)

    source_intake = {
        **source_contract,
        "schema": _safe_text(source.get("schema", "")),
        "intake_status": _source_status_text(source) if source else "",
        "safe_evidence_ref": source_ref,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "overall_status": "not_proven",
        "status": status,
        "review_decision": status,
        "decision_reasons": decision_reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref,
        "source_intake": source_intake,
        "required_materials": list(REQUIRED_ROUTE_ELEVATOR_MATERIALS),
        "required_route_elevator_materials": list(REQUIRED_ROUTE_ELEVATOR_MATERIALS),
        "accepted_material_refs": material_state["accepted_material_refs"],
        "missing_required_materials": material_state["missing_required_materials"],
        "rejected_material_refs": material_state["rejected_material_refs"],
        "material_review_state": {
            "accepted_count": material_state["accepted_count"],
            "required_count": material_state["required_count"],
            "all_required_materials_accepted": material_state["all_required_materials_accepted"],
        },
        "next_required_evidence": next_required,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "overall_status": "not_proven",
        "status": status,
        "review_decision": status,
        "decision_reasons": decision_reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref,
        "source_intake": source_intake,
        "required_materials": list(REQUIRED_ROUTE_ELEVATOR_MATERIALS),
        "required_route_elevator_materials": list(REQUIRED_ROUTE_ELEVATOR_MATERIALS),
        "accepted_material_refs": material_state["accepted_material_refs"],
        "missing_required_materials": material_state["missing_required_materials"],
        "rejected_material_refs": material_state["rejected_material_refs"],
        "next_required_evidence": next_required,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "elevator_field_evidence_trace_material_backfill_review_decision_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "raw_material_body",
            "raw_material_directory",
            "raw_source_intake_body",
            "ros_graph",
            "real_nav_runtime",
            "real_route_runtime",
            "real_field_pass",
            "hardware_transport",
            "hardware_feedback",
            "external_cloud",
            "real_phone_or_browser",
            "robot_action",
        ],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _unsafe_copy(summary):
        # 最终输出若仍不安全，强制降级且不改变 false flags。
        status = "blocked_unsafe_material_review_decision_not_proven"
        for target in (artifact, summary):
            target["status"] = status
            target["review_decision"] = status
        artifact["elevator_field_evidence_trace_material_backfill_review_decision_summary"] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只打印 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，便于 macOS PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate elevator field evidence trace material backfill review decision artifact")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--material-backfill-intake-json", help="material backfill intake artifact, summary, wrapper, file:<path>, or env:<VAR>")
    source.add_argument("--material-backfill-intake-summary", help="alias of --material-backfill-intake-json for summary inputs")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this review decision")
    parser.add_argument("--output", default="", help="optional review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional sanitized summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout and exit")
    args = parser.parse_args()

    intake_json = args.material_backfill_intake_json or args.material_backfill_intake_summary or ""
    artifact, summary, exit_code = build_elevator_field_evidence_trace_material_backfill_review_decision(
        intake_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"elevator_field_evidence_trace_material_backfill_review_decision: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"elevator_field_evidence_trace_material_backfill_review_decision_summary_file:{_safe_ref(args.summary_output)}")
        print(f"elevator_field_evidence_trace_material_backfill_review_decision_status:{artifact['status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
