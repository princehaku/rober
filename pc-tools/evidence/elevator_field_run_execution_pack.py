#!/usr/bin/env python3
"""生成 elevator assisted delivery 受控现场演练 execution pack。

该工具只读取上一轮 elevator field-run review artifact/summary，把复核决策转换
为现场演练材料包。它不访问 ROS graph、Nav2 runtime、串口、真实硬件、电梯、
外部云、OSS/CDN、DB/queue 或 4G 网络。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# execution pack 是 review 之后的现场执行契约，独立 schema 防止下游误读输入层级。
PACK_SCHEMA = "trashbot.elevator_field_run_execution_pack.v1"
PACK_SUMMARY_SCHEMA = "trashbot.elevator_field_run_execution_pack_summary.v1"
PACK_SCHEMA_VERSION = 1
PACK_BOUNDARY = "software_proof_docker_elevator_field_rehearsal_execution_pack_gate"

# 只支持上一轮 review artifact/summary；其它 JSON 必须 fail closed。
REVIEW_SCHEMA = "trashbot.elevator_field_run_review.v1"
REVIEW_SUMMARY_SCHEMA = "trashbot.elevator_field_run_review_summary.v1"
REVIEW_BOUNDARY = "software_proof_docker_elevator_field_review_decision_gate"
READY_REVIEW_DECISION = "ready_for_controlled_elevator_field_rehearsal_not_proven"

# 受控电梯演练仍围绕同一 evidence_ref 收集七类材料，和 validation/review gate 保持一致。
CONTROLLED_REHEARSAL_MATERIALS = (
    ("door_state.json", "door_state"),
    ("target_floor_confirmation.json", "target_floor_confirmation"),
    ("human_assistance_operator_note.md", "human_assistance"),
    ("nav2_fixed_route_runtime_log.json", "nav2_fixed_route_runtime"),
    ("task_record.json", "task_record"),
    ("completion_signal.json", "completion_signal"),
    ("diagnostics_mobile_safe_summary.json", "diagnostics_mobile_safe_summary"),
)

# not_proven 明确隔开 execution pack 与真实电梯、真实导航、硬件和送达成功证据。
NOT_PROVEN = (
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_record",
    "real_nav2_fixed_route_run",
    "real_robot_motion",
    "real_hardware_feedback",
    "real_hil_pass",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 验收会检索这两个 fail-closed 字符串；人工读日志时也能直接看到边界。
BOUNDARY_NOTE = (
    "Docker/local software proof only; delivery_success=false; "
    "primary_actions_enabled=false; elevator_field_rehearsal_execution_pack_not_real_delivery=true"
)

# 对外 artifact/summary 不能携带 raw 控制、设备、平台、凭证或完整本机材料。
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

# delivery/dropoff/cancel 成功类自由文本不能进入执行包；但保留字段
# `delivery_success=false`，因为它是下游 fail-closed contract 的必要证据。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(completed|complete|success|succeeded)\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
)

# 脱敏规则先处理输入自由文本，再由 forbidden copy 做最终围栏。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "[REDACTED_AUTH_HEADER]"),
    (re.compile(r"(?i)\bOSS_[A-Z_]*(ACCESS|SECRET)[A-Z_]*\b\s*[:=]\s*[^,\s]+"), "OSS_KEY=[REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_RATE]"),
    (re.compile(r"(?i)\bserial\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bUART\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bWAVE ROVER\b"), "[REDACTED_ROBOT_BASE]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 字符串便于 Docker/local 多主机材料按时间排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有进入 pack 的文本统一脱敏，避免 review 中的现场描述扩散敏感信息。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 或路径引用只保留 basename，避免把本机绝对路径交给手机/支持面。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 上游可能给字符串或数组；这里限制数量，避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 最终写盘前递归脱敏一次，防止新增嵌套字段绕过局部 helper。
    if isinstance(value, dict):
        return {str(_safe_text(k)): _safe_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _encoded(value: Any) -> str:
    # forbidden 检查使用稳定 JSON 字符串；不可编码时退回安全文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 同时查键和值，保证 summary 白名单不会带出控制 topic、设备或凭证。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_success_claim_copy(value: Any) -> bool:
    # 字段 true 和自由文本成功文案都必须拦截，避免 pack 被误读成现场已完成。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _any_true_key(value: Any, key: str) -> bool:
    # 成功或放行动作可能藏在嵌套字段或字符串里，必须递归拦截。
    if isinstance(value, dict):
        return any((k == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON、非 object 都生成 blocked pack，避免现场只有异常没有材料。
    if not path:
        return {}, "review_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "review_missing"
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}, "review_read_error"
    if not isinstance(payload, dict):
        return {}, "review_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object summary；其它形态不参与白名单消费。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # review artifact/summary 字段位置不同，缺失时不猜测 ready。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    # 支持 full review artifact、summary，以及 diagnostics 嵌套的只读 summary。
    if payload.get("schema") in {REVIEW_SCHEMA, REVIEW_SUMMARY_SCHEMA}:
        return payload
    nested_summary = _dict(payload, "elevator_field_run_review_summary")
    if nested_summary:
        return nested_summary
    nested_artifact = _dict(payload, "elevator_field_run_review")
    if nested_artifact:
        return nested_artifact
    return payload


def _normalize_review(payload: dict[str, Any]) -> dict[str, Any]:
    # execution pack 只消费 review 的白名单字段，不复制 raw validation 或本机路径。
    source = _source_payload(payload)
    summary = _dict(source, "review_summary")
    effective = summary if summary.get("schema") == REVIEW_SUMMARY_SCHEMA else source
    return {
        "schema": _safe_text(effective.get("schema", source.get("schema", ""))),
        "full_schema": _safe_text(source.get("schema", "")),
        "evidence_boundary": _safe_text(effective.get("evidence_boundary", source.get("evidence_boundary", ""))),
        "status": _safe_text(effective.get("status", source.get("review_decision", "missing_review"))),
        "review_decision": _safe_text(
            effective.get("review_decision") or source.get("review_decision") or "missing_review_decision"
        ),
        "evidence_ref": _safe_ref(effective.get("evidence_ref", source.get("evidence_ref", ""))),
        "same_evidence_ref_required": bool(effective.get("same_evidence_ref_required", source.get("same_evidence_ref_required", True))),
        "blocked_categories": _safe_list(effective.get("blocked_categories", source.get("blocked_categories", []))),
        "operator_next_steps": _safe_list(effective.get("operator_next_steps", source.get("operator_next_steps", [])), limit=8),
        "commands_to_rerun": _safe_list(effective.get("commands_to_rerun", source.get("commands_to_rerun", [])), limit=8),
        "capture_checklist": _capture_checklist(effective.get("capture_checklist", source.get("capture_checklist", []))),
        "not_proven": _safe_list(effective.get("not_proven", source.get("not_proven", [])), limit=20),
        "delivery_success": _any_true_key(source, "delivery_success") or _any_true_key(effective, "delivery_success"),
        "primary_actions_enabled": _any_true_key(source, "primary_actions_enabled") or _any_true_key(effective, "primary_actions_enabled"),
        "success_claim_copy": _has_success_claim_copy(source) or _has_success_claim_copy(effective),
    }


def _capture_checklist(value: Any) -> list[dict[str, Any]]:
    # 上游 checklist 只保留 name/category/status/operator_action，不复制其它 raw 字段。
    if not isinstance(value, list):
        value = []
    entries: list[dict[str, Any]] = []
    for name, category in CONTROLLED_REHEARSAL_MATERIALS:
        found = next((item for item in value if isinstance(item, dict) and item.get("name") == name), {})
        status = _safe_text(found.get("status", "unknown") if isinstance(found, dict) else "unknown") or "unknown"
        operator_action = _safe_text(found.get("operator_action", "") if isinstance(found, dict) else "")
        entries.append(
            {
                "name": name,
                "category": category,
                "status": status,
                "operator_action": operator_action or "collect_or_keep_material_for_rehearsal",
            }
        )
    return entries


def _schema_status(load_issue: str, review: dict[str, Any]) -> str:
    # artifact 和 summary 都支持，但 boundary 必须是上一轮 review decision gate。
    if load_issue:
        return "not_loaded"
    schema_supported = review["schema"] in {REVIEW_SCHEMA, REVIEW_SUMMARY_SCHEMA}
    full_schema_supported = review["full_schema"] in {"", REVIEW_SCHEMA, REVIEW_SUMMARY_SCHEMA}
    boundary_supported = review["evidence_boundary"] == REVIEW_BOUNDARY
    return "supported" if schema_supported and full_schema_supported and boundary_supported else "unsupported"


def _execution_pack_verdict(load_issue: str, schema_status: str, review: dict[str, Any], unsafe: bool) -> str:
    # 决策顺序必须先看输入有效性和安全，再看 review 是否允许进入受控演练准备。
    if load_issue == "review_missing":
        return "blocked_missing_review"
    if load_issue:
        return "blocked_read_error"
    if schema_status != "supported":
        return "blocked_unsupported_schema"
    if review["delivery_success"] or review["primary_actions_enabled"] or review["success_claim_copy"]:
        return "blocked_success_or_control_claim"
    if unsafe:
        return "blocked_unsafe_copy"
    if review["review_decision"] == READY_REVIEW_DECISION:
        return "ready_for_controlled_elevator_field_rehearsal_execution_pack_not_proven"
    return "blocked_review_not_ready"


def _required_material_templates(evidence_ref: str) -> list[dict[str, Any]]:
    # 模板只说明现场要补什么，不生成或读取任何真实演练材料。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        {
            "name": "door_state.json",
            "category": "door_state",
            "required_fields": ["schema", "evidence_ref", "door_state", "observed_at", "operator_or_sensor_note"],
            "capture_note": f"Record elevator door state for evidence_ref={ref}; this pack does not confirm a real door.",
        },
        {
            "name": "target_floor_confirmation.json",
            "category": "target_floor_confirmation",
            "required_fields": ["schema", "evidence_ref", "target_floor", "confirmation_source", "confirmed"],
            "capture_note": f"Record target-floor evidence for evidence_ref={ref}; keep unconfirmed runs explicit.",
        },
        {
            "name": "human_assistance_operator_note.md",
            "category": "human_assistance",
            "required_fields": ["evidence_ref", "observer", "assistance_note", "stop_path"],
            "capture_note": f"Record human observer assistance and stop path for evidence_ref={ref}.",
        },
        {
            "name": "nav2_fixed_route_runtime_log.json",
            "category": "nav2_fixed_route_runtime",
            "required_fields": ["evidence_ref", "runtime_events", "failure_reason", "route_or_waypoint_state"],
            "capture_note": f"Collect Nav2/fixed-route runtime log for evidence_ref={ref}; this CLI does not read ROS graph.",
        },
        {
            "name": "task_record.json",
            "category": "task_record",
            "required_fields": ["schema", "evidence_ref", "state_transition_history", "result_or_failure_code"],
            "capture_note": f"Export task record under evidence_ref={ref}; include timeout/cancel/failure reason.",
        },
        {
            "name": "completion_signal.json",
            "category": "completion_signal",
            "required_fields": ["schema", "evidence_ref", "dropoff_completion", "cancel_completion", "delivery_success"],
            "capture_note": "Record completion materials separately; this pack keeps delivery_success=false.",
        },
        {
            "name": "diagnostics_mobile_safe_summary.json",
            "category": "diagnostics_mobile_safe_summary",
            "required_fields": ["status", "evidence_ref", "not_proven", "delivery_success", "primary_actions_enabled"],
            "capture_note": "Share only whitelist summary fields; no raw controls, devices, credentials, or full artifacts.",
        },
    ]


def _first_run_commands(evidence_ref: str) -> list[str]:
    # 命令以人工可执行步骤为主，不包含串口、控制 topic、云凭证或本机绝对路径。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"assign one controlled rehearsal run evidence_ref={ref}",
        f"collect door_state.json under evidence_ref={ref}",
        f"collect target_floor_confirmation.json under evidence_ref={ref}",
        f"collect human_assistance_operator_note.md under evidence_ref={ref}",
        f"collect nav2_fixed_route_runtime_log.json under evidence_ref={ref}",
        f"collect task_record.json and completion_signal.json under evidence_ref={ref}",
        f"collect diagnostics_mobile_safe_summary.json under evidence_ref={ref}",
        "run elevator_field_run_material_validation.py, then elevator_field_run_review.py, then elevator_field_run_execution_pack.py --once-json",
    ]


def _rerun_commands(evidence_ref: str, review_commands: list[str]) -> list[str]:
    # 先保留 review 层修复提示，再追加本 gate 的重生成命令。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = list(review_commands[:5])
    commands.extend(
        [
            f"rerun all controlled rehearsal materials under the same evidence_ref={ref} when any source changes",
            "python3 pc-tools/evidence/elevator_field_run_material_validation.py --material-dir <elevator_material_dir> --evidence-ref %s --output <validation_json>" % ref,
            "python3 pc-tools/evidence/elevator_field_run_review.py --validation-json <validation_json> --output <review_json>",
            "python3 pc-tools/evidence/elevator_field_run_execution_pack.py --review-json <review_json> --once-json",
            "keep delivery_success=false and primary_actions_enabled=false until separate real field evidence passes",
        ]
    )
    return [_safe_text(command) for command in commands[:9]]


def _controlled_manifest(verdict: str, evidence_ref: str, review: dict[str, Any], schema_status: str, load_issue: str) -> dict[str, Any]:
    # manifest 是现场人员的总目录，明确需要观察员、停止路径和同一 evidence_ref。
    ready = verdict == "ready_for_controlled_elevator_field_rehearsal_execution_pack_not_proven"
    return {
        "name": "elevator_field_rehearsal_execution_pack",
        "execution_state": "prepared_for_controlled_rehearsal" if ready else "blocked_until_review_repaired",
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "human_observer_required": True,
        "stop_path_required": True,
        "source_review": {
            "load_issue": load_issue,
            "schema_status": schema_status,
            "schema": review["schema"],
            "full_schema": review["full_schema"],
            "evidence_boundary": review["evidence_boundary"],
            "review_decision": review["review_decision"],
        },
        "required_material_names": [name for name, _category in CONTROLLED_REHEARSAL_MATERIALS],
        "boundary_note": BOUNDARY_NOTE,
    }


def _operator_handoff(verdict: str, review: dict[str, Any]) -> dict[str, Any]:
    # handoff 只描述 operator/support 下一步，不提供任何机器人动作放行。
    return {
        "execution_pack_verdict": verdict,
        "review_decision": review["review_decision"],
        "blocked_categories": review["blocked_categories"],
        "operator_next_steps": review["operator_next_steps"][:5],
        "commands_to_rerun": review["commands_to_rerun"][:5],
        "capture_checklist": review["capture_checklist"],
        "safe_to_enable_primary_actions": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _pack_summary(verdict: str, evidence_ref: str, review: dict[str, Any]) -> dict[str, Any]:
    # summary 是 Robot diagnostics/mobile 的只读消费面，保持短字段和 fail-closed。
    return {
        "schema": PACK_SUMMARY_SCHEMA,
        "schema_version": PACK_SCHEMA_VERSION,
        "evidence_boundary": PACK_BOUNDARY,
        "status": verdict,
        "execution_pack_verdict": verdict,
        "review_decision": review["review_decision"],
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "controlled_rehearsal_manifest": {
            "execution_state": "prepared_for_controlled_rehearsal"
            if verdict == "ready_for_controlled_elevator_field_rehearsal_execution_pack_not_proven"
            else "blocked_until_review_repaired",
            "human_observer_required": True,
            "stop_path_required": True,
            "required_material_names": [name for name, _category in CONTROLLED_REHEARSAL_MATERIALS],
        },
        "required_material_templates": [name for name, _category in CONTROLLED_REHEARSAL_MATERIALS],
        "first_run_commands": _first_run_commands(evidence_ref)[:4],
        "rerun_commands": _rerun_commands(evidence_ref, review["commands_to_rerun"])[:4],
        "operator_handoff": {
            "blocked_categories": review["blocked_categories"],
            "operator_next_steps": review["operator_next_steps"][:4],
        },
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "elevator_field_rehearsal_execution_pack_metadata_only_not_delivery_success",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_execution_pack(review_json: str) -> tuple[dict[str, Any], int]:
    # 测试和 CLI 共用入口，保证本地 Python 环境即可验证 gate contract。
    payload, load_issue = _load_json(review_json)
    review = _normalize_review(payload) if payload else {
        "schema": "",
        "full_schema": "",
        "evidence_boundary": "",
        "status": "missing",
        "review_decision": "missing_review",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "blocked_categories": [],
        "operator_next_steps": [],
        "commands_to_rerun": [],
        "capture_checklist": _capture_checklist([]),
        "not_proven": [],
        "delivery_success": False,
        "primary_actions_enabled": False,
        "success_claim_copy": False,
    }
    schema_status = _schema_status(load_issue, review)
    unsafe = bool(payload and _has_forbidden_copy(payload))
    verdict = _execution_pack_verdict(load_issue, schema_status, review, unsafe)
    first_run = _first_run_commands(review["evidence_ref"])
    rerun = _rerun_commands(review["evidence_ref"], review["commands_to_rerun"])
    summary = _pack_summary(verdict, review["evidence_ref"], review)
    artifact = {
        "schema": PACK_SCHEMA,
        "schema_version": PACK_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": PACK_BOUNDARY,
        "execution_pack_verdict": verdict,
        "overall_status": verdict,
        "evidence_ref": review["evidence_ref"],
        "same_evidence_ref_required": True,
        "controlled_rehearsal_manifest": _controlled_manifest(verdict, review["evidence_ref"], review, schema_status, load_issue),
        "required_material_templates": _required_material_templates(review["evidence_ref"]),
        "first_run_commands": first_run,
        "rerun_commands": rerun,
        "operator_handoff": _operator_handoff(verdict, review),
        "execution_pack_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "real_elevator",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    if _has_forbidden_copy(artifact):
        # 最后一层保险：若仍不安全，只改状态并保持 fail-closed 字段。
        artifact["execution_pack_verdict"] = "blocked_unsafe_copy"
        artifact["overall_status"] = "blocked_unsafe_copy"
        artifact["controlled_rehearsal_manifest"]["execution_state"] = "blocked_until_review_repaired"
        artifact["execution_pack_summary"]["status"] = "blocked_unsafe_copy"
        artifact["execution_pack_summary"]["execution_pack_verdict"] = "blocked_unsafe_copy"
    return artifact, 0


def write_execution_pack(artifact: dict[str, Any], output: str) -> None:
    # output 为空时只打印 stdout；指定路径时自动建父目录用于 sprint 证据归档。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 单输入单输出，方便承接上一轮 review artifact 或 summary。
    parser = argparse.ArgumentParser(description="Generate elevator field-run controlled rehearsal execution pack")
    parser.add_argument("--review-json", required=True, help="elevator field-run review artifact or summary JSON path")
    parser.add_argument("--output", default="", help="optional execution pack JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print execution pack JSON to stdout and exit")
    args = parser.parse_args()

    artifact, exit_code = build_execution_pack(args.review_json)
    write_execution_pack(artifact, args.output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"elevator field-run execution pack: pack_file:{_safe_ref(args.output)}")
        print(f"execution_pack_verdict: {artifact['execution_pack_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
