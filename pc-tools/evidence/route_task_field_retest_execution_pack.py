#!/usr/bin/env python3
"""生成 route/task field retest execution pack。

该工具只读取上一轮 route_task_terminal_review_decision artifact 或 summary，
把 review decision、owner handoff 和 field retest guidance 转成下一次真实
现场复测可用的 PC execution pack。它不访问 ROS graph、Nav2 runtime、硬件、
外部云、真实手机或任何现场材料。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# retest execution pack 是 terminal review decision 之后的新契约，不复用上游 schema。
PACK_SCHEMA = "trashbot.route_task_field_retest_execution_pack.v1"
PACK_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_execution_pack_summary.v1"
PACK_SCHEMA_VERSION = 1
PACK_BOUNDARY = "software_proof_docker_route_task_field_retest_execution_pack_gate"

# 只支持上一轮 terminal review decision 的 artifact 或 summary。
SOURCE_SCHEMAS = {
    "trashbot.route_task_terminal_review_decision.v1",
    "trashbot.route_task_terminal_review_decision_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_terminal_review_decision_gate"

# not_proven 明确把本地执行包和真实现场、HIL、手机、Objective 5 外部 proof 隔开。
NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_task_record",
    "real_operator_field_note",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_note",
    "real_dropoff_or_cancel_completion",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 输入出现这些内容时不能进入 phone/operator safe execution pack。
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

# 成功和控制授权词只允许来自真实验收；本 gate 看到就 fail closed。
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

# operator-facing 文本不能携带本机绝对路径或 Windows 路径。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# 所有自由文本都先脱敏，blocked artifact 也不能回显凭证或底层硬件细节。
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
    # UTC 字符串便于不同 PC/Docker 主机上的 pack 按生成时间排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，避免上一轮 review note 泄露到 operator handoff。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 只保留安全短引用；本机路径转 basename，供现场同 ref 对齐。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 最终 payload 递归脱敏一次，防止新增嵌套字段绕过局部 helper。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _safe_list(value: Any, limit: int = 12) -> list[str]:
    # 上游字段可能是字符串或 list；限制数量避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _encoded(value: Any) -> str:
    # 安全扫描使用稳定 JSON；不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # forbidden copy 命中说明输入不适合进入现场复测执行包。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_raw_path_copy(source: dict[str, Any]) -> bool:
    # 只扫描人读字段；evidence_ref 由 _safe_ref 单独收敛。
    encoded = "\n".join(
        [
            _encoded(source.get("owner_handoff", {})),
            _encoded(source.get("next_required_evidence", [])),
            _encoded(source.get("field_retest_request_guidance", [])),
        ]
    )
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(source: dict[str, Any]) -> bool:
    # 顶层或嵌套 summary 里的成功/控制授权都必须阻断。
    if source.get("delivery_success") is True or source.get("primary_actions_enabled") is True:
        return True
    encoded = _encoded(source)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺失、坏 JSON、非 object 都输出 blocked pack，便于自动化留痕。
    if not path:
        return {}, "review_decision_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "review_decision_missing"
    except json.JSONDecodeError:
        return {}, "review_decision_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "review_decision_read_error"
    if not isinstance(payload, dict):
        return {}, "review_decision_not_object"
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
        "route_task_terminal_review_decision",
        "route_task_terminal_review_decision_summary",
        "review_decision",
        "review_decision_summary",
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


def _source_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 同时白名单化，防止拿错上游材料。
    schema = str(source.get("schema", "")).strip()
    boundary = str(source.get("evidence_boundary", "")).strip()
    return schema in SOURCE_SCHEMAS and (not boundary or boundary == SOURCE_BOUNDARY)


def _normalise_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 只消费上游 review decision 的白名单字段，不复制 raw input。
    source = _find_source(payload)
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    handoff = source.get("owner_handoff") if isinstance(source.get("owner_handoff"), dict) else robot.get("owner_handoff", {})
    return {
        "schema": _safe_text(source.get("schema", "")),
        "evidence_boundary": _safe_text(source.get("evidence_boundary", "")),
        "status": _safe_text(_first_text(source.get("status"), robot.get("status"), mobile.get("status"), default="missing")),
        "review_decision": _safe_text(
            _first_text(source.get("review_decision"), robot.get("review_decision"), mobile.get("review_decision"), default="")
        ),
        "decision_reason": _safe_text(_first_text(source.get("decision_reason"), robot.get("decision_reason"), default="")),
        "evidence_ref": _safe_ref(_first_text(source.get("evidence_ref"), robot.get("evidence_ref"), mobile.get("evidence_ref"), default="")),
        "same_evidence_ref_required": bool(source.get("same_evidence_ref_required", robot.get("same_evidence_ref_required", True))),
        "owner_handoff": _safe_value(handoff if isinstance(handoff, dict) else {}),
        "next_required_evidence": _safe_list(source.get("next_required_evidence") or robot.get("next_required_evidence"), limit=8),
        "field_retest_request_guidance": _safe_list(
            source.get("field_retest_request_guidance") or robot.get("field_retest_request_guidance"),
            limit=8,
        ),
        "not_proven": _safe_list(source.get("not_proven") or robot.get("not_proven"), limit=16),
        "delivery_success": bool(source.get("delivery_success", robot.get("delivery_success", False))),
        "primary_actions_enabled": bool(source.get("primary_actions_enabled", robot.get("primary_actions_enabled", False))),
        "source_payload": source,
    }


def _mentions_elevator(value: Any) -> bool:
    # 上游只要提到 elevator，就追加门状态、目标楼层和人工协助材料。
    return "elevator" in _encoded(value).lower()


def _source_status(load_issue: str, normalized: dict[str, Any]) -> dict[str, Any]:
    # source_review_decision 说明输入可信度，不把 unsupported 材料伪装成可执行包。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    if normalized["schema"] in SOURCE_SCHEMAS and normalized["evidence_boundary"] in {"", SOURCE_BOUNDARY}:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _pack_status(
    load_issue: str,
    source_status: dict[str, Any],
    normalized: dict[str, Any],
    unsafe_copy: bool,
    success_or_control_claim: bool,
) -> str:
    # fail-closed 优先级固定，保证缺失和 unsafe 不会落到 ready 分支。
    if load_issue in {"review_decision_bad_json", "review_decision_read_error", "review_decision_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_route_task_terminal_review_decision"
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
    if str(normalized["status"]).startswith("blocked") or str(normalized["status"]).startswith("requires"):
        return "blocked_review_decision_not_ready"
    return "ready_for_field_retest_execution_pack_not_proven"


def _required_field_materials(evidence_ref: str, include_elevator: bool) -> list[dict[str, Any]]:
    # 材料清单描述下一次真实复测要回填什么，不读取或生成真实现场材料。
    ref = evidence_ref or "<same_evidence_ref>"
    materials = [
        {
            "name": "nav2_or_fixed_route_runtime_log",
            "required_fields": ["evidence_ref", "start_time", "end_time", "runtime_events", "failure_reason_or_result"],
            "capture_note": f"Collect real Nav2/fixed-route runtime log under evidence_ref={ref}; this pack does not prove it.",
        },
        {
            "name": "route_completion_signal",
            "required_fields": ["evidence_ref", "route_id", "completion_state", "failure_reason_or_result"],
            "capture_note": f"Attach route completion signal for evidence_ref={ref}; keep review artifacts not_proven until verified.",
        },
        {
            "name": "task_record",
            "required_fields": ["evidence_ref", "task_id", "state_transition_history", "terminal_action", "failure_reason_or_result"],
            "capture_note": f"Export task record for evidence_ref={ref}; include dropoff/cancel branch reason when blocked.",
        },
        {
            "name": "operator_field_note",
            "required_fields": ["evidence_ref", "operator", "observed_route_result", "observed_terminal_result", "open_issues"],
            "capture_note": "Record what happened in the field; do not write delivery_success=true into this software-proof pack.",
        },
        {
            "name": "mobile_diagnostics_safe_summary",
            "required_fields": ["schema", "evidence_ref", "status", "not_proven", "delivery_success", "primary_actions_enabled"],
            "capture_note": "Share only whitelist-safe summary fields for diagnostics/mobile; no raw controls, paths, credentials, or hardware detail.",
        },
    ]
    if include_elevator:
        materials.extend(
            [
                {
                    "name": "elevator_door_state",
                    "required_fields": ["evidence_ref", "door_state", "timestamp", "observer_note"],
                    "capture_note": f"Capture elevator door state under evidence_ref={ref}; software pack cannot infer it.",
                },
                {
                    "name": "target_floor_confirmation",
                    "required_fields": ["evidence_ref", "target_floor", "confirmed_by", "confirmation_state"],
                    "capture_note": f"Capture target floor confirmation under evidence_ref={ref}; keep same_evidence_ref_required=true.",
                },
                {
                    "name": "human_assistance_note",
                    "required_fields": ["evidence_ref", "assistant_role", "assistance_type", "safety_note"],
                    "capture_note": "Record human assistance separately; do not treat assistance as autonomous delivery success.",
                },
            ]
        )
    return materials


def _rerun_commands(evidence_ref: str, include_elevator: bool) -> list[str]:
    # 命令是现场复测顺序摘要，不包含设备、云、路径或凭证参数。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = [
        f"prepare real Nav2/fixed-route runtime log with evidence_ref={ref}",
        f"capture route completion signal with evidence_ref={ref}",
        f"export task record and operator field note with evidence_ref={ref}",
        f"export mobile/diagnostics safe summary with evidence_ref={ref}",
    ]
    if include_elevator:
        commands.extend(
            [
                f"capture elevator door state with evidence_ref={ref}",
                f"capture target floor confirmation with evidence_ref={ref}",
                f"capture human assistance note with evidence_ref={ref}",
            ]
        )
    commands.extend(
        [
            "rerun route_task_terminal_completion_rehearsal.py after field materials are attached",
            "rerun route_task_terminal_review_decision.py after terminal rehearsal is regenerated",
            "rerun route_task_field_retest_execution_pack.py --review-decision-json <review_decision.json> --once-json",
            "keep delivery_success=false and primary_actions_enabled=false until real field evidence is reviewed",
        ]
    )
    return commands


def _operator_handoff(status: str, evidence_ref: str, source_handoff: dict[str, Any]) -> dict[str, Any]:
    # handoff 明确 owner 和禁止动作，避免现场把 pack 当成自动发车许可。
    ref = evidence_ref or "<same_evidence_ref>"
    source_owner = _safe_text(source_handoff.get("owner", "Autonomy Algorithm Engineer")) if source_handoff else "Autonomy Algorithm Engineer"
    return {
        "owner": source_owner,
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
        "handoff_note": (
            f"Use this pack to prepare the next field retest for evidence_ref={ref}."
            if status == "ready_for_field_retest_execution_pack_not_proven"
            else f"Repair the terminal review decision source before field retest for evidence_ref={ref}."
        ),
        "operator_instruction": "Collect field facts and failure reasons; do not mark delivery as complete from this software proof.",
        "primary_actions_enabled": False,
    }


def _field_retest_checklist(evidence_ref: str, include_elevator: bool) -> list[str]:
    # checklist 是复测前/中/后的最小闭环，保持同一个 evidence_ref。
    ref = evidence_ref or "<same_evidence_ref>"
    checklist = [
        f"Confirm every field material uses evidence_ref={ref}.",
        "Collect real Nav2/fixed-route runtime log before review closeout.",
        "Collect route completion signal and task record from the same retest.",
        "Write operator field note with observed result and failure reason if blocked.",
        "Export diagnostics/mobile safe summary with delivery_success=false and primary_actions_enabled=false.",
    ]
    if include_elevator:
        checklist.extend(
            [
                "Attach elevator door state evidence from the retest.",
                "Attach target floor confirmation from the retest.",
                "Attach human assistance note when assistance occurs.",
            ]
        )
    checklist.append("Rerun terminal rehearsal and review decision before any product closeout.")
    return checklist


def _summary_payload(
    status: str,
    evidence_ref: str,
    required_materials: list[dict[str, Any]],
    rerun_commands: list[str],
    operator_handoff: dict[str, Any],
    checklist: list[str],
) -> dict[str, Any]:
    # summary 是 Robot/mobile 可消费白名单视图，不包含 raw source artifact。
    return {
        "schema": PACK_SUMMARY_SCHEMA,
        "schema_version": PACK_SCHEMA_VERSION,
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "status": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "required_field_materials": [item["name"] for item in required_materials],
        "rerun_commands": rerun_commands[:5],
        "operator_handoff": operator_handoff,
        "field_retest_checklist": checklist[:6],
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_execution_pack(
    review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    review_payload, load_issue = _load_json(review_decision_json)
    normalized = _normalise_source(review_payload) if review_payload else {
        "schema": "",
        "evidence_boundary": "",
        "status": "missing",
        "review_decision": "",
        "decision_reason": "",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "owner_handoff": {},
        "next_required_evidence": [],
        "field_retest_request_guidance": [],
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
    unsafe_copy = bool(review_payload) and (_has_forbidden_copy(source_for_scan) or _has_raw_path_copy(normalized))
    success_or_control_claim = bool(review_payload) and _has_success_or_control_claim(source_for_scan)
    status = _pack_status(load_issue, source_status, {**normalized, "evidence_ref": requested_ref}, unsafe_copy, success_or_control_claim)

    include_elevator = bool(review_payload) and _mentions_elevator(source_for_scan)
    required_materials = _required_field_materials(requested_ref, include_elevator)
    rerun_commands = _rerun_commands(requested_ref, include_elevator)
    operator_handoff = _operator_handoff(status, requested_ref, normalized["owner_handoff"])
    checklist = _field_retest_checklist(requested_ref, include_elevator)
    summary = _summary_payload(status, requested_ref, required_materials, rerun_commands, operator_handoff, checklist)

    artifact = {
        "schema": PACK_SCHEMA,
        "schema_version": PACK_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "status": status,
        "execution_pack_verdict": status,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": {
            **source_status,
            "schema": normalized["schema"],
            "evidence_boundary": normalized["evidence_boundary"],
            "status": normalized["status"],
            "review_decision": normalized["review_decision"],
            "decision_reason": normalized["decision_reason"],
            "evidence_ref": normalized["evidence_ref"],
            "same_evidence_ref_required": normalized["same_evidence_ref_required"],
            "unsafe_copy": bool(unsafe_copy),
            "success_or_control_claim": bool(success_or_control_claim),
        },
        "required_field_materials": required_materials,
        "rerun_commands": rerun_commands,
        "operator_handoff": operator_handoff,
        "field_retest_checklist": checklist,
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
            "route_task_field_retest_execution_pack is software_proof_docker only; "
            "not_proven; delivery_success=false; primary_actions_enabled=false"
        ),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_forbidden_copy(artifact) or _has_forbidden_copy(summary):
        # 最终防线只降级状态；测试会暴露具体词，避免误报 ready。
        artifact["status"] = "blocked_unsafe_copy"
        artifact["execution_pack_verdict"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_copy"
        summary["status"] = "blocked_unsafe_copy"
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest execution pack")
    parser.add_argument("--review-decision-json", required=True, help="route_task_terminal_review_decision artifact or summary JSON path")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this retest pack")
    parser.add_argument("--output", default="", help="optional execution pack artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional execution pack summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print execution pack artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_execution_pack(
        args.review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field retest execution pack: execution_pack_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"execution_pack_summary_file: {_safe_ref(args.summary_output)}")
        print(f"status: {artifact['status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
