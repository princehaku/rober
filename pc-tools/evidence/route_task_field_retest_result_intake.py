#!/usr/bin/env python3
"""生成 route/task field retest result intake artifact。

该 gate 只处理现场复测回填后的 JSON 元数据，验证八类结果材料是否沿用同一
evidence_ref，并生成给 Robot diagnostics / mobile 只读消费的 fail-closed summary。
它不读取 ROS graph、Nav2 runtime、硬件、外部云、真实手机或真实现场文件内容。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# result intake 是上一轮 session handoff 之后的材料入口契约。
INTAKE_SCHEMA = "trashbot.route_task_field_retest_result_intake.v1"
INTAKE_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_result_intake_summary.v1"
SCHEMA_VERSION = 1
INTAKE_BOUNDARY = "software_proof_docker_route_task_field_retest_result_intake_gate"

# 输入优先支持 session handoff，也允许已经聚合好的 result artifact / summary。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_session_handoff.v1",
    "trashbot.route_task_field_retest_session_handoff_summary.v1",
    "trashbot.route_task_field_retest_result.v1",
    "trashbot.route_task_field_retest_result_summary.v1",
    INTAKE_SCHEMA,
    INTAKE_SUMMARY_SCHEMA,
}
HANDOFF_BOUNDARY = "software_proof_docker_route_task_field_retest_session_handoff_gate"
SOURCE_BOUNDARIES = {HANDOFF_BOUNDARY, INTAKE_BOUNDARY, ""}

# 八类现场复测结果材料是本 gate 的固定验收清单，不能由输入裁剪。
REQUIRED_RESULT_MATERIALS = (
    "nav2_or_fixed_route_runtime_log",
    "route_completion_signal",
    "task_record",
    "door_state",
    "target_floor_confirmation",
    "human_assistance_note",
    "dropoff_or_cancel_completion",
    "delivery_result",
)

# not_proven 固定说明本 gate 仍是 Docker/local 元数据入口，不是实机结论。
NOT_PROVEN = (
    "real_nav2_fixed_route_runtime_log_content",
    "real_route_completion_pass",
    "real_task_record_runtime",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_note",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result_reviewed_success",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# unsafe copy 在进入输出前必须 blocked，避免把底层工程细节泄漏到手机侧。
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
    "field pass",
    "HIL pass",
)

# 成功文案和动作放行不能通过材料入口进入 ready 分支。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\broute\s+completion\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
)

# 原始本机路径不允许进入 phone-safe summary；材料只记录元数据短名。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# 只有 placeholder/TBD/sample 的材料不能被当成现场回填结果。
PLACEHOLDER_PATTERNS = (
    re.compile(r"(?i)\b(tbd|todo|placeholder|example|sample|dummy|not_collected)\b"),
    re.compile(r"^<[^>]+>$"),
)

# 脱敏规则覆盖凭证、topic、串口和底层硬件字样；输出不回显 raw input。
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
    (re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws)/[^\s,;]+"), r"\1[REDACTED_PATH]"),
    (re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 时间保证不同 Docker/PC 主机产物能按时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本先统一脱敏，再进入 artifact 或 summary。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 允许文件形态输入，但输出只保留 basename，避免泄漏本机路径。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线，防止新增嵌套字段绕过 helper。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 上游可能给字符串或数组；限长避免复制完整现场材料。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _encoded(value: Any) -> str:
    # 安全扫描使用稳定 JSON，覆盖键名和值。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 禁词必须在脱敏前检查，命中后 fail closed。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_raw_path_copy(value: Any) -> bool:
    # 本 gate 只处理元数据，不接受真实文件内容或绝对路径 copy。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(source: dict[str, Any]) -> bool:
    # 顶层布尔和自由文本都检查，避免 summary 偷放成功或放行动作。
    if source.get("delivery_success") is True or source.get("primary_actions_enabled") is True:
        return True
    encoded = _encoded(source)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺失、坏 JSON、非 object 都输出 blocked，便于自动化留痕。
    if not path:
        return {}, "result_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "result_json_missing"
    except json.JSONDecodeError:
        return {}, "result_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "result_json_read_error"
    if not isinstance(payload, dict):
        return {}, "result_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段；其它形态按空对象处理。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # 兼容 artifact、summary、wrapper 三种输入形态，取第一个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 常把结果材料包在这些字段下，按白名单递归找。
    candidates = [payload]
    for key in (
        "route_task_field_retest_result_intake",
        "route_task_field_retest_result_intake_summary",
        "route_task_field_retest_result",
        "route_task_field_retest_result_summary",
        "route_task_field_retest_session_handoff",
        "route_task_field_retest_session_handoff_summary",
        "result_artifact",
        "result_summary",
        "field_result",
        "field_result_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
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
    # 优先选择 schema 命中的对象；没有 schema 时保留顶层供 fail-closed 解释。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _canonical_material(name: str) -> str:
    # 宽松映射允许 handoff/result summary 使用不同命名，但输出保持固定八类。
    text = name.lower().replace("-", "_").replace(" ", "_")
    if ("nav2" in text or "fixed_route" in text or "runtime_log" in text) and "log" in text:
        return "nav2_or_fixed_route_runtime_log"
    if "route_completion" in text or "completion_signal" in text:
        return "route_completion_signal"
    if "task_record" in text:
        return "task_record"
    if "door_state" in text or "elevator_door" in text:
        return "door_state"
    if "target_floor" in text or "floor_confirmation" in text:
        return "target_floor_confirmation"
    if "human_assistance" in text or "assistance_note" in text:
        return "human_assistance_note"
    if "dropoff" in text or "cancel" in text:
        return "dropoff_or_cancel_completion"
    if "delivery_result" in text or "delivery_outcome" in text:
        return "delivery_result"
    return text


def _material_name(value: Any, fallback_key: str = "") -> str:
    # 材料可用 dict 或字符串表达；dict 只取白名单短字段。
    if isinstance(value, dict):
        return _safe_text(
            _first_text(
                value.get("name"),
                value.get("material"),
                value.get("material_name"),
                value.get("type"),
                value.get("label"),
                fallback_key,
                default="",
            )
        )
    return _safe_text(_first_text(value, fallback_key, default=""))


def _material_status(value: Any) -> str:
    # 状态只用于判断材料是否真实回填，不读取材料文件内容。
    if isinstance(value, dict):
        return _safe_text(
            _first_text(
                value.get("status"),
                value.get("material_status"),
                value.get("collection_status"),
                value.get("presence"),
                value.get("state"),
                default="provided",
            )
        )
    text = _safe_text(value).strip()
    return "provided" if text else "missing"


def _material_ref(value: Any, source_ref: str) -> str:
    # 每个材料必须显式或继承同一 evidence_ref；不接受不同证据号混入。
    if isinstance(value, dict):
        return _safe_ref(_first_text(value.get("evidence_ref"), value.get("ref"), default=source_ref))
    return source_ref


def _placeholder_material(value: Any) -> bool:
    # placeholder/TBD/sample 不能被算作现场复测结果材料。
    encoded = _encoded(value)
    if any(pattern.search(encoded.strip()) for pattern in PLACEHOLDER_PATTERNS):
        return True
    status = _material_status(value).lower().replace("-", "_")
    return status in {"placeholder", "not_collected", "missing", "required_not_collected", "placeholder_required_not_collected_by_this_gate"}


def _iter_material_entries(value: Any) -> list[tuple[str, Any]]:
    # 支持 dict、list[dict]、list[str] 和单字符串四种材料形态。
    if isinstance(value, dict):
        return [(str(key), item) for key, item in value.items()]
    if isinstance(value, list):
        return [("", item) for item in value]
    if value in (None, ""):
        return []
    return [("", value)]


def _extract_materials(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    # 从 artifact/summary/wrapper 的多个常见字段中聚合八类材料摘要。
    material_sources = []
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    for holder in (source, robot, mobile, _dict(source, "field_callback"), _dict(source, "result_materials_summary")):
        for key in (
            "result_materials",
            "field_result_materials",
            "returned_materials",
            "collected_materials",
            "material_summaries",
            "materials",
            "material_completeness",
        ):
            if key in holder:
                material_sources.append(holder.get(key))

    materials: dict[str, dict[str, Any]] = {}
    source_ref = _safe_ref(_first_text(source.get("evidence_ref"), robot.get("evidence_ref"), mobile.get("evidence_ref"), default=""))
    for material_source in material_sources:
        for fallback_key, raw_material in _iter_material_entries(material_source):
            name = _canonical_material(_material_name(raw_material, fallback_key))
            if name not in REQUIRED_RESULT_MATERIALS:
                continue
            # 后出现的真实材料可以覆盖 handoff placeholder，方便 wrapper 带回填结果。
            placeholder = _placeholder_material(raw_material)
            existing = materials.get(name)
            if existing and not existing["placeholder"]:
                continue
            materials[name] = {
                "name": name,
                "status": _material_status(raw_material),
                "evidence_ref": _material_ref(raw_material, source_ref),
                "placeholder": placeholder,
                "metadata": _safe_value(_material_metadata(raw_material)),
            }
    return materials


def _material_metadata(value: Any) -> dict[str, Any]:
    # 输出材料元数据摘要，不读取 path 指向的真实文件。
    if not isinstance(value, dict):
        return {"summary": _safe_text(value)}
    metadata: dict[str, Any] = {}
    for key in ("name", "status", "material_status", "collection_status", "state", "review_note", "failure_reason", "observer_note"):
        if key in value:
            metadata[key] = _safe_text(value[key])
    if "path" in value or "expected_relative_path" in value:
        metadata["path_hint"] = _safe_ref(_first_text(value.get("path"), value.get("expected_relative_path"), default=""))
    return metadata


def _missing_materials(materials: dict[str, dict[str, Any]]) -> list[str]:
    # 缺失或 placeholder 材料都不能算 complete。
    missing = []
    for name in REQUIRED_RESULT_MATERIALS:
        material = materials.get(name)
        if not material or material["placeholder"]:
            missing.append(name)
    return missing


def _mismatched_refs(materials: dict[str, dict[str, Any]], evidence_ref: str) -> list[str]:
    # same evidence_ref 是 Robot/mobile 后续复账的硬约束。
    mismatches = []
    for name, material in materials.items():
        ref = material.get("evidence_ref", "")
        if evidence_ref and ref and ref != evidence_ref:
            mismatches.append(name)
    return mismatches


def _placeholder_only(materials: dict[str, dict[str, Any]]) -> bool:
    # 只有 placeholder 的输入通常来自 handoff 原样回传，必须阻断。
    return bool(materials) and all(material["placeholder"] for material in materials.values())


def _normalise_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 只消费白名单字段，不复制 raw input 到输出。
    source = _find_source(payload)
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return {
        "schema": _safe_text(source.get("schema", "")),
        "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "status": _safe_text(_first_text(source.get("status"), robot.get("status"), mobile.get("status"), default="missing")),
        "evidence_ref": _safe_ref(_first_text(source.get("evidence_ref"), robot.get("evidence_ref"), mobile.get("evidence_ref"), default="")),
        "same_evidence_ref_required": source.get(
            "same_evidence_ref_required",
            robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", True)),
        ),
        "operator_next_steps": _safe_list(source.get("operator_next_steps") or robot.get("operator_next_steps"), limit=10),
        "field_callback_checklist": _safe_list(source.get("field_callback_checklist") or robot.get("field_callback_checklist"), limit=10),
        "rerun_commands": _safe_list(source.get("rerun_commands") or robot.get("rerun_commands"), limit=10),
        "delivery_success": bool(source.get("delivery_success", robot.get("delivery_success", False))),
        "primary_actions_enabled": bool(source.get("primary_actions_enabled", robot.get("primary_actions_enabled", False))),
        "materials": _extract_materials(source),
        "source_payload": source,
    }


def _source_status(load_issue: str, normalized: dict[str, Any]) -> dict[str, Any]:
    # source_result 说明输入可信度，不把 unsupported 材料伪装成 intake。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = normalized["schema"]
    boundary = normalized["evidence_boundary"]
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _intake_status(
    load_issue: str,
    source_status: dict[str, Any],
    normalized: dict[str, Any],
    missing: list[str],
    mismatched_refs: list[str],
    placeholder_only: bool,
    unsafe_copy: bool,
    success_or_control_claim: bool,
) -> str:
    # fail-closed 优先级固定，保证 unsafe、证据号错误和缺材料不会落到 ready。
    if load_issue in {"result_json_bad_json", "result_json_read_error", "result_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_route_task_field_retest_result"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_schema"
    if not normalized["evidence_ref"]:
        return "blocked_missing_evidence_ref"
    if normalized["same_evidence_ref_required"] is not True:
        return "blocked_same_evidence_ref_not_required"
    if unsafe_copy:
        return "blocked_unsafe_copy"
    if success_or_control_claim:
        return "blocked_success_or_control_claim"
    if mismatched_refs:
        return "blocked_same_evidence_ref_mismatch"
    if placeholder_only:
        return "blocked_placeholder_only_materials"
    if missing:
        return "blocked_missing_result_materials"
    return "ready_for_field_retest_result_intake_not_proven"


def _material_completeness(materials: dict[str, dict[str, Any]], missing: list[str], mismatched_refs: list[str]) -> dict[str, Any]:
    # completeness 是摘要，不证明材料内容真实或现场通过。
    present = [name for name in REQUIRED_RESULT_MATERIALS if name in materials and not materials[name]["placeholder"]]
    return {
        "required_count": len(REQUIRED_RESULT_MATERIALS),
        "present_count": len(present),
        "is_complete": not missing and not mismatched_refs,
        "present_materials": present,
        "missing_materials": missing,
        "same_evidence_ref_mismatches": mismatched_refs,
    }


def _operator_next_steps(status: str, evidence_ref: str, missing: list[str], mismatched_refs: list[str]) -> list[str]:
    # 下一步只要求补材料或复跑 gate，不能给出现场成功结论。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_field_retest_result_intake_not_proven":
        return [
            f"Review all eight result materials for evidence_ref={ref} in the terminal review gate.",
            "Keep phone and diagnostics read-only until terminal review returns a conservative decision.",
            "Do not mark delivery complete from this intake artifact.",
        ]
    steps = [f"Keep evidence_ref={ref} aligned before rerun."]
    if missing:
        steps.append("Attach missing result materials: " + ", ".join(missing))
    if mismatched_refs:
        steps.append("Re-collect mismatched materials on the same evidence_ref: " + ", ".join(mismatched_refs))
    steps.append("Rerun route_task_field_retest_result_intake.py after metadata is repaired.")
    return steps


def _field_callback_checklist(evidence_ref: str) -> list[str]:
    # callback/checklist 约束现场只回填事实、失败原因和同证据号摘要。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"Confirm every material summary uses evidence_ref={ref}.",
        "Summarize Nav2/fixed-route runtime log metadata without copying raw log content.",
        "Include route completion signal and task record terminal branch with failure reason when blocked.",
        "Include door state, target floor confirmation, and human assistance note for elevator flow.",
        "Include dropoff/cancel completion branch and delivery result review input without success wording.",
        "Run terminal review after this intake; do not enable primary actions here.",
    ]


def _rerun_summary(evidence_ref: str, source_commands: list[str]) -> dict[str, Any]:
    # rerun summary 保留 PC gate 顺序，不包含设备、云、凭证或绝对路径。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = [
        f"rerun route_task_field_retest_result_intake.py --evidence-ref {ref}",
        "rerun route_task_terminal_completion_rehearsal.py after result materials are accepted",
        "rerun route_task_terminal_review_decision.py after terminal rehearsal is regenerated",
        "keep delivery_success=false and primary_actions_enabled=false until real review closes",
    ]
    for command in source_commands[:4]:
        if command and command not in commands:
            commands.append(command)
    return {"evidence_ref": ref, "commands": [_safe_text(command) for command in commands[:8]]}


def _safe_copy(status: str, evidence_ref: str, completeness: dict[str, Any]) -> dict[str, Any]:
    # safe_copy 是 mobile/diagnostics 白名单，不包含 raw artifact 或材料内容。
    return {
        "schema": f"{INTAKE_SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "evidence_boundary": INTAKE_BOUNDARY,
        "evidence_ref": evidence_ref,
        "material_complete": completeness["is_complete"],
        "missing_materials": completeness["missing_materials"],
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    completeness: dict[str, Any],
    operator_next_steps: list[str],
    field_callback_checklist: list[str],
    rerun_summary: dict[str, Any],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 Robot/mobile 首选消费面，字段保持稳定且 fail-closed。
    return {
        "schema": INTAKE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": status,
        "intake_verdict": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "required_result_materials": list(REQUIRED_RESULT_MATERIALS),
        "material_completeness": completeness,
        "missing_materials": completeness["missing_materials"],
        "operator_next_steps": operator_next_steps,
        "field_callback_checklist": field_callback_checklist,
        "rerun_summary": rerun_summary,
        "safe_copy": safe_copy,
        "fail_closed_phone_safe_summary": {
            "not_proven": "not_proven",
            "delivery_success": False,
            "primary_actions_enabled": False,
            "evidence_boundary": INTAKE_BOUNDARY,
        },
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_result_intake(
    result_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 result/handoff JSON，生成 fail-closed result intake artifact 与 summary。"""
    payload, load_issue = _load_json(result_json)
    normalized = _normalise_source(payload) if payload else {
        "schema": "",
        "evidence_boundary": "",
        "status": "missing",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "operator_next_steps": [],
        "field_callback_checklist": [],
        "rerun_commands": [],
        "delivery_success": False,
        "primary_actions_enabled": False,
        "materials": {},
        "source_payload": {},
    }
    requested_ref = _safe_ref(evidence_ref) or normalized["evidence_ref"]
    if evidence_ref and normalized["evidence_ref"] and requested_ref != normalized["evidence_ref"]:
        normalized["same_evidence_ref_required"] = False
    normalized_for_status = {**normalized, "evidence_ref": requested_ref}

    source_status = _source_status(load_issue, normalized)
    source_for_scan = normalized.get("source_payload", {})
    materials = normalized["materials"]
    missing = _missing_materials(materials)
    mismatches = _mismatched_refs(materials, requested_ref)
    placeholder_only = _placeholder_only(materials)
    unsafe_copy = bool(payload) and (_has_forbidden_copy(source_for_scan) or _has_raw_path_copy(source_for_scan))
    success_or_control_claim = bool(payload) and _has_success_or_control_claim(source_for_scan)
    status = _intake_status(
        load_issue,
        source_status,
        normalized_for_status,
        missing,
        mismatches,
        placeholder_only,
        unsafe_copy,
        success_or_control_claim,
    )

    completeness = _material_completeness(materials, missing, mismatches)
    next_steps = _operator_next_steps(status, requested_ref, missing, mismatches)
    callback = _field_callback_checklist(requested_ref)
    rerun_summary = _rerun_summary(requested_ref, normalized["rerun_commands"])
    safe_copy = _safe_copy(status, requested_ref, completeness)
    summary = _summary_payload(status, requested_ref, completeness, next_steps, callback, rerun_summary, safe_copy)

    artifact = {
        "schema": INTAKE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": INTAKE_BOUNDARY,
        "boundary": INTAKE_BOUNDARY,
        "status": status,
        "intake_verdict": status,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_result": {
            **source_status,
            "schema": normalized["schema"],
            "evidence_boundary": normalized["evidence_boundary"],
            "status": normalized["status"],
            "evidence_ref": normalized["evidence_ref"],
            "same_evidence_ref_required": normalized["same_evidence_ref_required"],
            "unsafe_copy": bool(unsafe_copy),
            "success_or_control_claim": bool(success_or_control_claim),
        },
        "result_materials": {
            name: {
                "status": material["status"],
                "evidence_ref": material["evidence_ref"],
                "placeholder": material["placeholder"],
                "metadata": material["metadata"],
            }
            for name, material in sorted(materials.items())
        },
        "material_completeness": completeness,
        "missing_materials": missing,
        "operator_next_steps": next_steps,
        "field_callback_checklist": callback,
        "rerun_summary": rerun_summary,
        "safe_copy": safe_copy,
        "fail_closed_phone_safe_summary": summary["fail_closed_phone_safe_summary"],
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "hardware_feedback",
            "real_phone_or_browser",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "real_field_file_content",
        ],
        "boundary_note": (
            "route_task_field_retest_result_intake is software_proof_docker only; "
            "not_proven; delivery_success=false; primary_actions_enabled=false"
        ),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_forbidden_copy(artifact) or _has_forbidden_copy(summary):
        # 最终防线只降级状态；不回显原始 source，避免敏感 copy 写入 ready 输出。
        artifact["status"] = "blocked_unsafe_copy"
        artifact["intake_verdict"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["intake_verdict"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["intake_verdict"] = "blocked_unsafe_copy"
        summary["status"] = "blocked_unsafe_copy"
        summary["intake_verdict"] = "blocked_unsafe_copy"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只走 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，便于 PC、Docker、unittest 和后续 diagnostics fixture 复用。
    parser = argparse.ArgumentParser(description="Generate a route/task field retest result intake artifact")
    parser.add_argument("--result-json", required=True, help="result artifact, summary, session handoff, or wrapper JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this result intake")
    parser.add_argument("--output", default="", help="optional result intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional result intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print result intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_result_intake(args.result_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field retest result intake: intake_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"intake_summary_file: {_safe_ref(args.summary_output)}")
        print(f"intake_verdict: {artifact['intake_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
