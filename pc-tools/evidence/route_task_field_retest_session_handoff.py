#!/usr/bin/env python3
"""生成 route/task field retest session handoff artifact。

该 gate 只读取上一轮 route_task_field_retest_execution_pack artifact 或 summary，
把复测执行包转换成下一次现场 session 的交接材料。它不访问 ROS graph、
Nav2 runtime、硬件、外部云、真实手机或真实现场材料。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# handoff schema 是 Robot diagnostics 和 mobile 只读消费的新契约。
HANDOFF_SCHEMA = "trashbot.route_task_field_retest_session_handoff.v1"
HANDOFF_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_session_handoff_summary.v1"
SCHEMA_VERSION = 1
HANDOFF_BOUNDARY = "software_proof_docker_route_task_field_retest_session_handoff_gate"

# 只支持上一轮 route/task field retest execution pack 的 artifact 或 summary。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_execution_pack.v1",
    "trashbot.route_task_field_retest_execution_pack_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_execution_pack_gate"

# 本 gate 必须要求下一次真实现场回填这些材料，但自身不证明材料已经存在。
REQUIRED_MATERIAL_NAMES = (
    "nav2_fixed_route_runtime_log",
    "route_completion_signal",
    "task_record",
    "door_state",
    "target_floor_confirmation",
    "human_assistance_note",
    "dropoff_or_cancel_completion",
    "delivery_result",
)

# not_proven 固定隔离 Docker/local handoff 与真实路线、电梯、手机、HIL 和 O5 证据。
NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_task_record",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_note",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 输入或 operator copy 命中这些词时必须 blocked，避免泄露原始控制/凭证/硬件细节。
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

# 成功或动作放行只能来自真实验收；本 handoff 看到就 fail closed。
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

# raw 本机路径不能进入现场交接 copy；输出只使用相对 placeholder path。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# placeholder-only source material 说明 execution pack 没有给出可复测的材料名。
PLACEHOLDER_PATTERNS = (
    re.compile(r"(?i)\b(tbd|todo|placeholder|example|sample|dummy)\b"),
    re.compile(r"^<[^>]+>$"),
)

# 所有自由文本进入输出前先脱敏；blocked artifact 也不能回显敏感输入。
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
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 时间让不同 PC/Docker 主机的 artifact 可以按生成顺序审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，避免 source execution pack 泄露到底层摘要。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 只保留 safe 引用；本机路径转 basename 供同 ref 对齐。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 最终 payload 递归脱敏一次，防止新增嵌套字段绕过 helper。
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
    # 上游可能给字符串或 list；限长避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _encoded(value: Any) -> str:
    # 安全扫描用稳定 JSON 覆盖键和值；不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 禁词在脱敏前检查，命中就不允许进入 ready handoff。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_raw_path_copy(value: Any) -> bool:
    # source copy 中出现本机完整路径要 blocked；evidence_ref 另走 _safe_ref。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(source: dict[str, Any]) -> bool:
    # 顶层布尔和自由文本同时检查，避免 source summary 偷放行动作。
    if source.get("delivery_success") is True or source.get("primary_actions_enabled") is True:
        return True
    encoded = _encoded(source)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺失、坏 JSON、非 object 都输出 blocked handoff，便于自动化留痕。
    if not path:
        return {}, "execution_pack_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "execution_pack_missing"
    except json.JSONDecodeError:
        return {}, "execution_pack_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "execution_pack_read_error"
    if not isinstance(payload, dict):
        return {}, "execution_pack_not_object"
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
    # wrapper/nested JSON 常把 artifact 或 summary 包在这些字段下，按白名单递归找。
    candidates = [payload]
    for key in (
        "route_task_field_retest_execution_pack",
        "route_task_field_retest_execution_pack_summary",
        "execution_pack",
        "execution_pack_summary",
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


def _material_name(value: Any) -> str:
    # source material 可能是 dict 或字符串；只取 name/path/label 的安全短名。
    if isinstance(value, dict):
        return _safe_text(
            _first_text(
                value.get("name"),
                value.get("material"),
                value.get("path"),
                value.get("expected_path"),
                value.get("filename"),
                default="",
            )
        )
    return _safe_text(value)


def _material_names_from(value: Any) -> list[str]:
    # required_field_materials 支持 list[dict]、list[str] 或单个字符串。
    if isinstance(value, list):
        return [_material_name(item) for item in value if _material_name(item)]
    if value in (None, ""):
        return []
    return [_material_name(value)]


def _canonical_material(name: str) -> str:
    # 用宽松匹配把 source 的不同命名映射成本 gate 的八类必需材料。
    text = name.lower().replace("-", "_").replace(" ", "_")
    if ("nav2" in text or "fixed_route" in text or "runtime_log" in text) and "log" in text:
        return "nav2_fixed_route_runtime_log"
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


def _missing_required_materials(material_names: list[str]) -> list[str]:
    # handoff 要求 source 已列出八类下一次现场真实材料，不接受漏项。
    canonical = {_canonical_material(name) for name in material_names}
    return [name for name in REQUIRED_MATERIAL_NAMES if name not in canonical]


def _placeholder_only_materials(material_names: list[str]) -> bool:
    # 全是 TBD/sample/placeholder 说明 source 不是可交接的 execution pack。
    if not material_names:
        return False
    return all(any(pattern.search(name.strip()) for pattern in PLACEHOLDER_PATTERNS) for name in material_names)


def _normalise_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 只消费 source execution pack 的白名单字段，不复制 raw input。
    source = _find_source(payload)
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    handoff = source.get("operator_handoff") if isinstance(source.get("operator_handoff"), dict) else {}
    material_names = _material_names_from(
        source.get("required_field_materials")
        or source.get("required_materials")
        or source.get("required_material_names")
        or robot.get("required_field_materials")
        or robot.get("required_materials")
        or mobile.get("required_field_materials")
    )
    return {
        "schema": _safe_text(source.get("schema", "")),
        "evidence_boundary": _safe_text(source.get("evidence_boundary", "")),
        "status": _safe_text(_first_text(source.get("status"), robot.get("status"), mobile.get("status"), default="missing")),
        "execution_pack_verdict": _safe_text(
            _first_text(source.get("execution_pack_verdict"), robot.get("execution_pack_verdict"), default="")
        ),
        "evidence_ref": _safe_ref(_first_text(source.get("evidence_ref"), robot.get("evidence_ref"), mobile.get("evidence_ref"), default="")),
        "same_evidence_ref_required": source.get(
            "same_evidence_ref_required",
            robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", True)),
        ),
        "required_field_materials": material_names,
        "rerun_commands": _safe_list(source.get("rerun_commands") or robot.get("rerun_commands"), limit=10),
        "operator_handoff": _safe_value(handoff),
        "field_retest_checklist": _safe_list(source.get("field_retest_checklist") or robot.get("field_retest_checklist"), limit=10),
        "not_proven": _safe_list(source.get("not_proven") or robot.get("not_proven"), limit=20),
        "delivery_success": bool(source.get("delivery_success", robot.get("delivery_success", False))),
        "primary_actions_enabled": bool(source.get("primary_actions_enabled", robot.get("primary_actions_enabled", False))),
        "source_payload": source,
    }


def _source_status(load_issue: str, normalized: dict[str, Any]) -> dict[str, Any]:
    # source_execution_pack 说明输入可信度，不把 unsupported 材料伪装成 handoff。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = normalized["schema"]
    boundary = normalized["evidence_boundary"]
    if schema in SOURCE_SCHEMAS and (not boundary or boundary == SOURCE_BOUNDARY):
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _handoff_status(
    load_issue: str,
    source_status: dict[str, Any],
    normalized: dict[str, Any],
    missing_required: list[str],
    placeholder_only: bool,
    unsafe_copy: bool,
    success_or_control_claim: bool,
) -> str:
    # fail-closed 优先级固定，保证缺失、unsafe 和漏材料不会落到 ready 分支。
    if load_issue in {"execution_pack_bad_json", "execution_pack_read_error", "execution_pack_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_route_task_field_retest_execution_pack"
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
    if placeholder_only:
        return "blocked_placeholder_only_materials"
    if missing_required:
        return "blocked_missing_required_materials"
    source_verdict = normalized["execution_pack_verdict"] or normalized["status"]
    if str(source_verdict).startswith("blocked") or str(source_verdict).startswith("requires"):
        return "blocked_execution_pack_not_ready"
    return "ready_for_field_retest_session_handoff_not_proven"


def _material_placeholders(evidence_ref: str) -> list[dict[str, Any]]:
    # placeholder path 是相对路径约定，不泄露本机绝对路径，也不表示文件已存在。
    ref = evidence_ref or "<same_evidence_ref>"
    specs = {
        "nav2_fixed_route_runtime_log": ["evidence_ref", "start_time", "end_time", "runtime_events", "failure_reason_or_result"],
        "route_completion_signal": ["evidence_ref", "route_id", "completion_state", "failure_reason_or_result"],
        "task_record": ["evidence_ref", "task_id", "state_transition_history", "terminal_action", "failure_reason_or_result"],
        "door_state": ["evidence_ref", "door_state", "timestamp", "observer_note"],
        "target_floor_confirmation": ["evidence_ref", "target_floor", "confirmed_by", "confirmation_state"],
        "human_assistance_note": ["evidence_ref", "assistant_role", "assistance_type", "safety_note"],
        "dropoff_or_cancel_completion": ["evidence_ref", "terminal_action", "completion_state", "failure_reason_or_result"],
        "delivery_result": ["evidence_ref", "delivery_result", "reviewed_by", "review_decision"],
    }
    return [
        {
            "name": name,
            "expected_relative_path": f"field_materials/{ref}/{name}.json",
            "required_fields": fields,
            "material_status": "placeholder_required_not_collected_by_this_gate",
            "same_evidence_ref_required": True,
            "delivery_success": False,
        }
        for name, fields in specs.items()
    ]


def _rerun_commands(evidence_ref: str, source_commands: list[str]) -> list[str]:
    # 命令只描述 PC gate 重跑顺序，不包含设备、云、路径或凭证参数。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = [
        f"collect field materials with evidence_ref={ref}",
        "rerun route_task_terminal_completion_rehearsal.py after field materials are attached",
        "rerun route_task_terminal_review_decision.py after terminal rehearsal is regenerated",
        "rerun route_task_field_retest_execution_pack.py --review-decision-json <review_decision.json> --once-json",
        "rerun route_task_field_retest_session_handoff.py --execution-pack-json <execution_pack.json> --once-json",
        "keep delivery_success=false and primary_actions_enabled=false until real field evidence is reviewed",
    ]
    for command in source_commands[:4]:
        if command and command not in commands:
            commands.append(command)
    return [_safe_text(command) for command in commands[:8]]


def _field_callback_checklist(evidence_ref: str) -> list[str]:
    # callback/checklist 明确现场要回填事实和失败原因，不能回填成功口号。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"Confirm every returned material uses evidence_ref={ref}.",
        "Attach Nav2/fixed-route runtime log and route completion signal from the same retest.",
        "Attach task record with terminal action branch and failure reason when blocked.",
        "Attach door state, target floor confirmation, and human assistance note when elevator flow is involved.",
        "Attach dropoff/cancel completion material and delivery result only after real review.",
        "Re-run terminal rehearsal, review decision, execution pack, and this session handoff gate.",
    ]


def _operator_handoff(status: str, evidence_ref: str, source_handoff: dict[str, Any], session_owner: str) -> dict[str, Any]:
    # operator handoff 固定 owner、禁止动作和下一步，避免现场把 handoff 当发车许可。
    ref = evidence_ref or "<same_evidence_ref>"
    owner = _safe_text(session_owner or source_handoff.get("owner") or "Autonomy Algorithm Engineer")
    return {
        "session_owner": owner,
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "handoff_note": (
            f"Prepare the controlled field retest session for evidence_ref={ref}."
            if status == "ready_for_field_retest_session_handoff_not_proven"
            else f"Repair the route/task field retest execution pack before session handoff for evidence_ref={ref}."
        ),
        "operator_instruction": "Collect field facts, material refs, and failure reasons; do not mark delivery complete from this handoff.",
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def _safe_copy(status: str, evidence_ref: str, session_owner: str, material_names: list[str]) -> dict[str, Any]:
    # safe_copy 是 diagnostics/mobile 白名单摘要，不复制 raw artifact、路径或底层工程细节。
    return {
        "schema": f"{HANDOFF_SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "evidence_ref": evidence_ref,
        "session_owner": _safe_text(session_owner or "Autonomy Algorithm Engineer"),
        "required_materials_count": len(REQUIRED_MATERIAL_NAMES),
        "source_materials_count": len(material_names),
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    session_owner: str,
    missing_required: list[str],
    material_placeholders: list[dict[str, Any]],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 Robot/mobile 首选消费面，保持字段少且稳定。
    return {
        "schema": HANDOFF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": status,
        "handoff_verdict": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "session_owner": _safe_text(session_owner or "Autonomy Algorithm Engineer"),
        "required_field_materials": list(REQUIRED_MATERIAL_NAMES),
        "missing_required_materials": missing_required,
        "material_placeholders": [item["name"] for item in material_placeholders],
        "rerun_commands": rerun_commands[:5],
        "safe_copy": safe_copy,
        "fail_closed_summary": {
            "not_proven": "not_proven",
            "delivery_success": False,
            "primary_actions_enabled": False,
            "evidence_boundary": HANDOFF_BOUNDARY,
        },
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_session_handoff(
    execution_pack_json: str,
    evidence_ref: str = "",
    session_owner: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 execution pack，生成 fail-closed session handoff artifact 与 summary。"""
    pack_payload, load_issue = _load_json(execution_pack_json)
    normalized = _normalise_source(pack_payload) if pack_payload else {
        "schema": "",
        "evidence_boundary": "",
        "status": "missing",
        "execution_pack_verdict": "",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "required_field_materials": [],
        "rerun_commands": [],
        "operator_handoff": {},
        "field_retest_checklist": [],
        "not_proven": [],
        "delivery_success": False,
        "primary_actions_enabled": False,
        "source_payload": {},
    }
    requested_ref = _safe_ref(evidence_ref) or normalized["evidence_ref"]
    if evidence_ref and normalized["evidence_ref"] and requested_ref != normalized["evidence_ref"]:
        normalized["same_evidence_ref_required"] = False

    source_status = _source_status(load_issue, normalized)
    source_for_scan = normalized.get("source_payload", {})
    material_names = normalized["required_field_materials"]
    missing_required = _missing_required_materials(material_names)
    placeholder_only = _placeholder_only_materials(material_names)
    unsafe_copy = bool(pack_payload) and (_has_forbidden_copy(source_for_scan) or _has_raw_path_copy(source_for_scan))
    success_or_control_claim = bool(pack_payload) and _has_success_or_control_claim(source_for_scan)
    normalized_for_status = {**normalized, "evidence_ref": requested_ref}
    status = _handoff_status(
        load_issue,
        source_status,
        normalized_for_status,
        missing_required,
        placeholder_only,
        unsafe_copy,
        success_or_control_claim,
    )

    material_placeholders = _material_placeholders(requested_ref)
    rerun_commands = _rerun_commands(requested_ref, normalized["rerun_commands"])
    checklist = _field_callback_checklist(requested_ref)
    operator_handoff = _operator_handoff(status, requested_ref, normalized["operator_handoff"], session_owner)
    safe_copy = _safe_copy(status, requested_ref, operator_handoff["session_owner"], material_names)
    summary = _summary_payload(
        status,
        requested_ref,
        operator_handoff["session_owner"],
        missing_required,
        material_placeholders,
        rerun_commands,
        safe_copy,
    )

    artifact = {
        "schema": HANDOFF_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": status,
        "handoff_verdict": status,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_execution_pack": {
            **source_status,
            "schema": normalized["schema"],
            "evidence_boundary": normalized["evidence_boundary"],
            "status": normalized["status"],
            "execution_pack_verdict": normalized["execution_pack_verdict"],
            "evidence_ref": normalized["evidence_ref"],
            "same_evidence_ref_required": normalized["same_evidence_ref_required"],
            "source_required_field_materials": material_names,
            "missing_required_materials": missing_required,
            "placeholder_only_materials": bool(placeholder_only),
            "unsafe_copy": bool(unsafe_copy),
            "success_or_control_claim": bool(success_or_control_claim),
        },
        "session_handoff": {
            "session_owner": operator_handoff["session_owner"],
            "handoff_status": status,
            "evidence_ref": requested_ref,
            "same_evidence_ref_required": True,
            "material_placeholders_count": len(material_placeholders),
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "operator_handoff": operator_handoff,
        "material_placeholders": material_placeholders,
        "material_paths": [item["expected_relative_path"] for item in material_placeholders],
        "rerun_commands": rerun_commands,
        "field_callback_checklist": checklist,
        "safe_copy": safe_copy,
        "fail_closed_summary": summary["fail_closed_summary"],
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
        ],
        "boundary_note": (
            "route_task_field_retest_session_handoff is software_proof_docker only; "
            "not_proven; delivery_success=false; primary_actions_enabled=false"
        ),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_forbidden_copy(artifact) or _has_forbidden_copy(summary):
        # 最终防线只降级状态；不回显原始 source，避免把敏感 copy 写入 ready 输出。
        artifact["status"] = "blocked_unsafe_copy"
        artifact["handoff_verdict"] = "blocked_unsafe_copy"
        artifact["session_handoff"]["handoff_status"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["handoff_verdict"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["handoff_verdict"] = "blocked_unsafe_copy"
        summary["status"] = "blocked_unsafe_copy"
        summary["handoff_verdict"] = "blocked_unsafe_copy"
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest session handoff artifact")
    parser.add_argument("--execution-pack-json", required=True, help="route_task_field_retest_execution_pack artifact or summary JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this handoff")
    parser.add_argument("--session-owner", default="", help="optional safe session owner label")
    parser.add_argument("--output", default="", help="optional handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print handoff artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_session_handoff(
        args.execution_pack_json,
        args.evidence_ref,
        args.session_owner,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field retest session handoff: handoff_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"handoff_summary_file: {_safe_ref(args.summary_output)}")
        print(f"handoff_verdict: {artifact['handoff_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
