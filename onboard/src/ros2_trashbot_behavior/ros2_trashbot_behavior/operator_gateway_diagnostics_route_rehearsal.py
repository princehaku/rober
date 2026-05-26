import json
import os
import re


def safe_int(value, default=0):
    # review artifact 里的计数字段可能来自 JSON/表单文本；失败时保持调用方传入的保守默认值。
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


ROUTE_TASK_REHEARSAL_SCHEMA = "trashbot.route_task_rehearsal_artifact"

ROUTE_TASK_REHEARSAL_DIAGNOSTICS_SCHEMA = "trashbot.route_task_rehearsal_diagnostics_summary.v1"

ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_SCHEMA = "trashbot.route_task_rehearsal_execution_bundle"

ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_SUMMARY_SCHEMA = (
    "trashbot.route_task_rehearsal_execution_bundle_summary.v1"
)

ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_SCHEMA = "trashbot.route_task_rehearsal_operator_review.v1"

ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_SUMMARY_SCHEMA = (
    "trashbot.route_task_rehearsal_operator_review_summary.v1"
)

ROUTE_TASK_REHEARSAL_ARTIFACT_GATE = "software_proof_docker_route_task_rehearsal_artifact_gate"

ROUTE_TASK_REHEARSAL_DIAGNOSTICS_GATE = "software_proof_docker_route_task_rehearsal_diagnostics_gate"

ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_GATE = (
    "software_proof_docker_route_task_rehearsal_execution_bundle_gate"
)

ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_GATE = (
    "software_proof_docker_route_task_rehearsal_operator_review_gate"
)

PC_ROUTE_DEBUG_CONSOLE_SCHEMA = "trashbot.pc_route_debug_console.v1"

PC_ROUTE_DEBUG_CONSOLE_SUMMARY_SCHEMA = "trashbot.pc_route_debug_console_summary.v1"

PC_ROUTE_DEBUG_CONSOLE_GATE = "software_proof_docker_pc_route_debug_console_gate"

PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_SUMMARY_SCHEMA = (
    "trashbot.pc_route_elevator_console_integration_summary.v1"
)

PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_GATE = (
    "software_proof_docker_pc_route_elevator_console_integration_gate"
)

ROUTE_TASK_REHEARSAL_REQUIRED_NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "wave_rover_motion",
    "real_serial_or_uart_feedback",
    "real_hil_pass",
    "delivery_success",
)

ROUTE_TASK_REHEARSAL_TEXT_REDACTIONS = (
    (re.compile(r"(?i)\bAuthorization\s*:\s*(?:Bearer\s+)?[^,\s]+"), "[REDACTED_AUTH_HEADER]"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\b(oss[_-]?secret|access[_-]?key[_-]?secret|ak|sk|root[_-]?password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_SERIAL]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_BAUD]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?<![\w:])(?:~|/Users|/tmp|/var|/private|/ws|/home|/root|/mnt/[A-Za-z])/[^\s,;}\\\"]+"), "[REDACTED_LOCAL_PATH]"),
)

def _redact_route_task_rehearsal_text(value):
    text = str(value or "")
    for pattern, replacement in ROUTE_TASK_REHEARSAL_TEXT_REDACTIONS:
        text = pattern.sub(replacement, text)
    return text

def _safe_route_task_rehearsal_ref(value):
    text = str(value or "").strip()
    if not text:
        return ""
    redacted = _redact_route_task_rehearsal_text(text)
    if "[REDACTED_LOCAL_PATH]" in redacted:
        basename = os.path.basename(os.path.expanduser(text).rstrip(os.sep)) or "artifact"
        return f"local_path_redacted:{basename}"
    return redacted

def _safe_route_task_rehearsal_list(value, limit=8):
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        items.append(_redact_route_task_rehearsal_text(item))
        if len(items) >= limit:
            break
    return items

def _route_task_rehearsal_not_proven(artifact=None):
    artifact = artifact if isinstance(artifact, dict) else {}
    values = []
    source_values = artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else []
    for item in list(source_values) + list(ROUTE_TASK_REHEARSAL_REQUIRED_NOT_PROVEN):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values

def _pc_route_debug_not_proven(console=None):
    # PC 调试台只能提供软件侧可读性材料，真实路线、硬件和交付结论必须显式保持未证明。
    console = console if isinstance(console, dict) else {}
    values = []
    source_values = console.get("not_proven") if isinstance(console.get("not_proven"), list) else []
    required = (
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_or_cancel_completion",
        "delivery_success",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values

def _pc_route_elevator_reconciliation_not_proven(reconciliation=None):
    # PC console 的电梯/路线对账只保留软件侧嵌套摘要；动作面和真实交付证据必须继续外部采集。
    reconciliation = reconciliation if isinstance(reconciliation, dict) else {}
    values = []
    source_values = (
        reconciliation.get("not_proven") if isinstance(reconciliation.get("not_proven"), list) else []
    )
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "terminal_ack",
        "cursor_advance_or_persistence",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "real_elevator_operation",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_or_cancel_completion",
        "delivery_success",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values

def _first_route_task_rehearsal_value(*values):
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""

def _default_route_task_rehearsal_summary(path, state="not_configured", read_error=""):
    # diagnostics 只读消费 artifact；默认状态必须保守，不能把缺文件解释成路线或任务通过。
    return {
        "schema": ROUTE_TASK_REHEARSAL_DIAGNOSTICS_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_REHEARSAL_DIAGNOSTICS_GATE,
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "artifact_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "crosscheck_status": {
            "status": "",
            "scope": "status/replay/task_record software alignment only",
            "software_mismatch_count": 0,
            "software_mismatches": [],
        },
        "hil_alignment_status": {
            "status": "",
            "alignment_status": "not_proven",
            "evidence_ref_match": False,
            "not_real_hil_when_status_is_missing_blocked_or_software_proof": True,
            "detail": "not real HIL; route/task rehearsal diagnostics were not configured",
            "mismatch_count": 0,
        },
        "not_proven": _route_task_rehearsal_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_phone_copy": "Route/task rehearsal diagnostics are not configured; this is not delivery success.",
        "next_step": "Attach a route/task rehearsal artifact from evidence_crosscheck before using diagnostics for route/task replay support.",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }

def _default_pc_route_debug_console_summary(path, state="not_configured", read_error=""):
    # diagnostics 默认 fail-closed：没配置 PC console artifact 时不能推断路线可用或控制可执行。
    return {
        "schema": PC_ROUTE_DEBUG_CONSOLE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PC_ROUTE_DEBUG_CONSOLE_GATE,
        "overall_status": "blocked",
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "console_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "availability": {
            "status": "blocked",
            "reason": "pc route debug console summary is not configured",
        },
        "route_debug_status": {
            "status": "not_proven",
            "current_checkpoint": "",
            "target": "",
            "matching_status": "",
            "failure_reason": "",
        },
        "route_progress": {},
        "keyframe_preflight": {},
        "recent_task_summary": {},
        "route_elevator_reconciliation": _default_pc_route_elevator_reconciliation_summary(),
        "not_proven": _pc_route_debug_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "PC route debug console is not configured; this is not delivery success.",
        "safe_phone_copy": "PC route debug console is not configured; this is not delivery success.",
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
    }

def _default_pc_route_elevator_reconciliation_summary(state="not_configured", read_error=""):
    # 嵌套 summary 有自己的软件证明边界，但不能提升父级 PC console 的控制能力。
    return {
        "schema": PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_GATE,
        "overall_status": "blocked",
        "state": state,
        "source_evidence_boundary": "",
        "availability": {
            "status": "blocked",
            "reason": "route elevator reconciliation summary is not configured",
        },
        "reconciliation_status": {
            "status": "not_proven",
            "reason": read_error or "route elevator reconciliation summary is not configured",
        },
        "elevator_assist_status": {},
        "route_completion_status": {},
        "operator_next_steps": [],
        "not_proven": _pc_route_elevator_reconciliation_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route elevator reconciliation is not configured; this is not delivery success.",
        "safe_phone_copy": "Route elevator reconciliation is not configured; this is not delivery success.",
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
    }

def _safe_pc_route_debug_value(value, depth=0):
    # 递归脱敏只保留支撑人员可读摘要；深层或大列表会截断，避免把完整 artifact 泄露给 phone/support。
    if depth > 3:
        return "[REDACTED_NESTED_VALUE]"
    if isinstance(value, dict):
        safe = {}
        for key, item in list(value.items())[:20]:
            safe_key = _redact_route_task_rehearsal_text(key)
            safe[safe_key] = _safe_pc_route_debug_value(item, depth=depth + 1)
        return safe
    if isinstance(value, list):
        return [_safe_pc_route_debug_value(item, depth=depth + 1) for item in value[:8]]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _redact_route_task_rehearsal_text(value)

def _safe_pc_route_debug_dict(value):
    return _safe_pc_route_debug_value(value if isinstance(value, dict) else {})

def _pc_route_debug_safe_copy_is_unsafe(value):
    # 支持 copy 允许解释“未证明”，但不能暗示 Start/ACK/HIL/交付已经成立。
    text = _redact_route_task_rehearsal_text(value).strip().lower()
    if not text:
        return True
    guarded_phrases = (
        "not delivery success",
        "not a delivery success",
        "no delivery success",
        "never delivery success",
        "not real hil",
        "not hil",
        "not a hil",
        "not start",
        "not confirm",
        "not cancel",
        "must not",
        "metadata-only",
    )
    unsafe_phrases = (
        "delivery success",
        "hil pass",
        "real hil",
        "start delivery enabled",
        "confirm dropoff enabled",
        "cancel enabled",
        "ack posted",
        "cursor advanced",
        "nav2 started",
        "dropoff complete",
        "cancel complete",
    )
    guarded_text = text
    for guard in guarded_phrases:
        guarded_text = guarded_text.replace(guard, "")
    for phrase in unsafe_phrases:
        if phrase in guarded_text:
            return True
    return False

def _pc_route_elevator_reconciliation_has_unsafe_control_claims(value):
    # 嵌套对账摘要来自 PC console artifact，任何成功/控制布尔为真都必须让嵌套摘要 fail-closed。
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "nav2_triggered",
        "hil_pass",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "dropoff_completion",
        "cancel_completion",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text in unsafe_true_keys and bool(item):
                return True
            if _pc_route_elevator_reconciliation_has_unsafe_control_claims(item):
                return True
        return False
    if isinstance(value, list):
        return any(_pc_route_elevator_reconciliation_has_unsafe_control_claims(item) for item in value)
    return False

def _pc_route_elevator_reconciliation_safe_copy_is_unsafe(value):
    # 与父级 PC console copy 一致：允许说明 metadata-only，不允许暗示 ACK、Nav2、HIL 或交付成功。
    return _pc_route_debug_safe_copy_is_unsafe(value)

def _summarize_pc_route_elevator_reconciliation(value, source_boundary):
    """把 PC console 内嵌 route/elevator 对账片段收敛成只读、fail-closed summary。"""
    summary = _default_pc_route_elevator_reconciliation_summary(
        read_error="route elevator reconciliation summary is not configured",
    )
    if not isinstance(value, dict):
        return summary

    safe_copy = _redact_route_task_rehearsal_text(
        value.get("safe_copy")
        or value.get("safe_phone_copy")
        or "Route elevator reconciliation is metadata-only; not delivery success."
    )
    nested_boundary = str(value.get("evidence_boundary") or PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_GATE)
    availability = value.get("availability") if isinstance(value.get("availability"), dict) else {}
    reconciliation_status = (
        value.get("reconciliation_status")
        if isinstance(value.get("reconciliation_status"), dict)
        else {}
    )
    status_text = str(
        reconciliation_status.get("status")
        or availability.get("status")
        or value.get("status")
        or ""
    ).strip().lower()
    summary.update(
        {
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "availability": _safe_pc_route_debug_dict(availability),
            "reconciliation_status": _safe_pc_route_debug_dict(reconciliation_status),
            "elevator_assist_status": _safe_pc_route_debug_dict(value.get("elevator_assist_status")),
            "route_completion_status": _safe_pc_route_debug_dict(value.get("route_completion_status")),
            "operator_next_steps": _safe_route_task_rehearsal_list(value.get("operator_next_steps")),
            "not_proven": _pc_route_elevator_reconciliation_not_proven(value),
            "read_error": "",
        }
    )
    if nested_boundary != PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_boundary",
                "read_error": "route elevator reconciliation evidence boundary is unsupported",
                "availability": {
                    "status": "blocked",
                    "reason": "unsupported route elevator reconciliation boundary",
                },
                "safe_copy": "Route elevator reconciliation source boundary is unsupported; no delivery result is proven.",
                "safe_phone_copy": "Route elevator reconciliation source boundary is unsupported; no delivery result is proven.",
            }
        )
        return summary

    if (
        _pc_route_elevator_reconciliation_has_unsafe_control_claims(value)
        or _pc_route_elevator_reconciliation_safe_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_fields",
                "read_error": "route elevator reconciliation contains unsafe control or success claims",
                "availability": {
                    "status": "blocked",
                    "reason": "unsafe route elevator reconciliation fields",
                },
                "safe_copy": "Route elevator reconciliation was blocked because it could imply control or delivery success.",
                "safe_phone_copy": "Route elevator reconciliation was blocked because it could imply control or delivery success.",
            }
        )
        return summary

    summary["safe_copy"] = safe_copy
    summary["safe_phone_copy"] = safe_copy
    blocked_statuses = {"", "blocked", "missing", "read_error", "unsupported_schema", "unsafe_copy", "unsafe_fields"}
    if status_text in blocked_statuses:
        summary.update(
            {
                "overall_status": "blocked",
                "state": status_text or "blocked",
            }
        )
        return summary

    summary.update(
        {
            "overall_status": "degraded",
            "state": "available",
        }
    )
    return summary

def _default_route_task_rehearsal_execution_bundle_summary(path, state="not_configured", read_error=""):
    # bundle 是比旧 artifact 更上层的只读 manifest；默认必须 fail-closed，避免 diagnostics 被误当成控制入口。
    return {
        "schema": ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_GATE,
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "bundle_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "artifact_ref": "",
        "artifact_state": "",
        "crosscheck_status": {
            "status": "",
            "scope": "status/replay/task_record software alignment only",
            "software_mismatch_count": 0,
            "software_mismatches": [],
        },
        "hil_alignment_status": {
            "status": "",
            "alignment_status": "not_proven",
            "evidence_ref_match": False,
            "not_real_hil_when_status_is_missing_blocked_or_software_proof": True,
            "detail": "not real HIL; route/task rehearsal execution bundle was not configured",
            "mismatch_count": 0,
        },
        "not_proven": _route_task_rehearsal_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_phone_copy": "Route/task rehearsal execution bundle is not configured; this is not delivery success.",
        "next_step": "Attach a route/task rehearsal execution bundle manifest before using diagnostics for execution rehearsal support.",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
    }

def _default_route_task_rehearsal_operator_review_summary(path, state="not_configured", read_error=""):
    # review package 面向人工复核和手机支持，只能作为 diagnostics metadata，不能触发机器人动作。
    return {
        "schema": ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_GATE,
        "overall_status": "blocked",
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "review_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "crosscheck_status": {
            "status": "",
            "scope": "status/replay/task_record software alignment only",
            "software_mismatch_count": 0,
        },
        "hil_alignment_status": {
            "status": "",
            "alignment_status": "not_proven",
            "evidence_ref_match": False,
            "not_real_hil_when_status_is_missing_blocked_or_software_proof": True,
        },
        "mismatch_summary": {
            "software_mismatch_count": 0,
            "hil_mismatch_count": 0,
            "items": [],
        },
        "next_rehearsal_decision": "attach_route_task_rehearsal_operator_review",
        "not_proven": _route_task_rehearsal_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route/task rehearsal operator review is not configured; this is not delivery success.",
        "safe_phone_copy": "Route/task rehearsal operator review is not configured; this is not delivery success.",
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "delivery_success": False,
    }

def _route_task_rehearsal_review_dict(*values):
    for value in values:
        if isinstance(value, dict):
            return value
    return {}

def _route_task_rehearsal_review_safe_copy_is_unsafe(value):
    # 手机端 copy 允许说“不是成功”，但不能把 review package 包装成动作、ACK 或真实 HIL 结论。
    text = _redact_route_task_rehearsal_text(value).strip().lower()
    if not text:
        return True
    guarded_phrases = (
        "not delivery success",
        "not a delivery success",
        "no delivery success",
        "never delivery success",
        "not real hil",
        "not hil",
        "not a hil",
        "not start",
        "not confirm",
        "not cancel",
        "must not",
    )
    unsafe_phrases = (
        "delivery success",
        "hil pass",
        "real hil",
        "start delivery enabled",
        "confirm dropoff enabled",
        "cancel enabled",
        "ack posted",
        "dropoff complete",
        "cancel complete",
    )
    guarded_text = text
    for guard in guarded_phrases:
        guarded_text = guarded_text.replace(guard, "")
    for phrase in unsafe_phrases:
        if phrase in guarded_text:
            return True
    return False

def _route_task_rehearsal_review_mismatch_summary(review, crosscheck, hil_alignment):
    source = review.get("mismatch_summary") if isinstance(review.get("mismatch_summary"), dict) else {}
    software_mismatches = crosscheck.get("software_mismatches")
    hil_mismatches = hil_alignment.get("mismatches")
    source_items = source.get("items") if isinstance(source.get("items"), list) else []
    items = source_items or (software_mismatches if isinstance(software_mismatches, list) else [])
    return {
        "software_mismatch_count": safe_int(
            source.get("software_mismatch_count"),
            default=len(software_mismatches) if isinstance(software_mismatches, list) else 0,
        ),
        "hil_mismatch_count": safe_int(
            source.get("hil_mismatch_count"),
            default=len(hil_mismatches) if isinstance(hil_mismatches, list) else 0,
        ),
        "items": _safe_route_task_rehearsal_list(items),
    }

def summarize_route_task_rehearsal_artifact(path):
    """构建只读、phone-safe 的 route/task rehearsal diagnostics summary。"""
    artifact_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_rehearsal_summary(
        artifact_path,
        read_error="route/task rehearsal artifact is not configured",
    )
    if not artifact_path:
        return summary
    if not os.path.exists(artifact_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route/task rehearsal artifact not found",
                "safe_phone_copy": "Route/task rehearsal artifact is missing; this is not delivery success.",
                "next_step": "Regenerate the route/task rehearsal artifact, then reopen diagnostics.",
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(artifact_path, "r", encoding="utf-8") as f:
            artifact = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(f"failed reading route/task rehearsal artifact: {exc}"),
                "safe_phone_copy": "Route/task rehearsal artifact could not be read; keep treating route/task proof as not_proven.",
                "next_step": "Fix the artifact JSON and rerun the diagnostics summary.",
            }
        )
        return summary

    if not isinstance(artifact, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route/task rehearsal artifact JSON must be an object",
                "safe_phone_copy": "Route/task rehearsal artifact shape is invalid; route/task proof remains not_proven.",
                "next_step": "Regenerate a JSON object artifact from evidence_crosscheck.",
            }
        )
        return summary

    source_schema = str(artifact.get("schema") or "")
    source_boundary = str(artifact.get("evidence_boundary") or "")
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": artifact.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "evidence_ref": _safe_route_task_rehearsal_ref(artifact.get("evidence_ref", "")),
            "not_proven": _route_task_rehearsal_not_proven(artifact),
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_REHEARSAL_SCHEMA or source_boundary != ROUTE_TASK_REHEARSAL_ARTIFACT_GATE:
        summary.update(
            {
                "state": "unsupported_schema",
                "read_error": "route/task rehearsal artifact schema or evidence boundary is unsupported",
                "safe_phone_copy": "Route/task rehearsal artifact is not a supported diagnostics source; no delivery result is proven.",
                "next_step": "Regenerate the artifact with the supported route/task rehearsal schema and boundary.",
            }
        )
        return summary

    crosscheck = artifact.get("crosscheck_status") if isinstance(artifact.get("crosscheck_status"), dict) else {}
    hil_alignment = artifact.get("hil_alignment_status") if isinstance(artifact.get("hil_alignment_status"), dict) else {}
    crosscheck_status = str(crosscheck.get("status") or "").strip().lower()
    software_mismatches = crosscheck.get("software_mismatches")
    hil_mismatches = hil_alignment.get("mismatches")
    summary["crosscheck_status"] = {
        "status": _redact_route_task_rehearsal_text(crosscheck_status),
        "scope": _redact_route_task_rehearsal_text(
            crosscheck.get("scope") or "status/replay/task_record software alignment only"
        ),
        "software_mismatch_count": len(software_mismatches) if isinstance(software_mismatches, list) else 0,
        "software_mismatches": _safe_route_task_rehearsal_list(software_mismatches),
    }
    alignment_status = str(hil_alignment.get("alignment_status") or "not_proven").strip()
    summary["hil_alignment_status"] = {
        "status": _redact_route_task_rehearsal_text(hil_alignment.get("status", "")),
        "alignment_status": _redact_route_task_rehearsal_text(alignment_status or "not_proven"),
        "evidence_ref_match": bool(hil_alignment.get("evidence_ref_match", False)),
        "not_real_hil_when_status_is_missing_blocked_or_software_proof": bool(
            hil_alignment.get("not_real_hil_when_status_is_missing_blocked_or_software_proof", True)
        ),
        "detail": _redact_route_task_rehearsal_text(
            hil_alignment.get("detail") or "not real HIL; route/task rehearsal remains software proof"
        ),
        "mismatch_count": len(hil_mismatches) if isinstance(hil_mismatches, list) else 0,
    }

    if crosscheck_status == "pass":
        summary.update(
            {
                "state": "crosscheck_pass",
                "safe_phone_copy": "Route/task rehearsal crosscheck passed as Docker/local software proof only; it is not delivery success.",
                "next_step": "Use the shared evidence_ref for support/replay, then collect real Nav2/fixed-route and HIL evidence before claiming delivery.",
            }
        )
        return summary
    if crosscheck_status == "fail":
        summary.update(
            {
                "state": "crosscheck_fail",
                "safe_phone_copy": "Route/task rehearsal crosscheck failed; keep route/task proof blocked and not_proven.",
                "next_step": "Inspect the sanitized software mismatches, fix the source artifact, and rerun evidence_crosscheck.",
            }
        )
        return summary

    summary.update(
        {
            "state": "unsupported_status",
            "read_error": "route/task rehearsal artifact crosscheck status is missing or unsupported",
            "safe_phone_copy": "Route/task rehearsal artifact has no supported crosscheck result; no route or delivery pass is proven.",
            "next_step": "Regenerate the artifact with crosscheck_status.status pass or fail.",
        }
    )
    return summary

def summarize_route_task_rehearsal_operator_review(path):
    """构建只读、phone/support-safe 的 operator review package 摘要。"""
    review_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_rehearsal_operator_review_summary(
        review_path,
        read_error="route/task rehearsal operator review package is not configured",
    )
    if not review_path:
        return summary
    if not os.path.exists(review_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route/task rehearsal operator review package not found",
                "safe_copy": "Route/task rehearsal operator review is missing; this is not delivery success.",
                "safe_phone_copy": "Route/task rehearsal operator review is missing; this is not delivery success.",
                "next_rehearsal_decision": "regenerate_operator_review_package",
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(review_path, "r", encoding="utf-8") as f:
            review = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading route/task rehearsal operator review package: {exc}"
                ),
                "safe_copy": "Route/task rehearsal operator review could not be read; keep proof blocked.",
                "safe_phone_copy": "Route/task rehearsal operator review could not be read; keep proof blocked.",
                "next_rehearsal_decision": "fix_operator_review_json",
            }
        )
        return summary

    if not isinstance(review, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route/task rehearsal operator review JSON must be an object",
                "safe_copy": "Route/task rehearsal operator review shape is invalid; proof remains blocked.",
                "safe_phone_copy": "Route/task rehearsal operator review shape is invalid; proof remains blocked.",
                "next_rehearsal_decision": "regenerate_operator_review_json_object",
            }
        )
        return summary

    source_schema = str(review.get("schema") or "")
    source_boundary = str(review.get("evidence_boundary") or "")
    crosscheck = _route_task_rehearsal_review_dict(
        review.get("crosscheck_status"),
        review.get("crosscheck"),
    )
    hil_alignment = _route_task_rehearsal_review_dict(
        review.get("hil_alignment_status"),
        review.get("hil_alignment"),
    )
    crosscheck_status = str(crosscheck.get("status") or "").strip().lower()
    safe_copy = _redact_route_task_rehearsal_text(
        review.get("safe_copy") or review.get("safe_phone_copy") or ""
    )
    next_decision = _redact_route_task_rehearsal_text(
        review.get("next_rehearsal_decision") or review.get("next_step") or ""
    )
    mismatch_summary = _route_task_rehearsal_review_mismatch_summary(
        review,
        crosscheck,
        hil_alignment,
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": review.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "evidence_ref": _safe_route_task_rehearsal_ref(review.get("evidence_ref", "")),
            "crosscheck_status": {
                "status": _redact_route_task_rehearsal_text(crosscheck_status),
                "scope": _redact_route_task_rehearsal_text(
                    crosscheck.get("scope") or "status/replay/task_record software alignment only"
                ),
                "software_mismatch_count": mismatch_summary["software_mismatch_count"],
            },
            "hil_alignment_status": {
                "status": _redact_route_task_rehearsal_text(hil_alignment.get("status", "")),
                "alignment_status": _redact_route_task_rehearsal_text(
                    hil_alignment.get("alignment_status") or "not_proven"
                ),
                "evidence_ref_match": bool(hil_alignment.get("evidence_ref_match", False)),
                "not_real_hil_when_status_is_missing_blocked_or_software_proof": bool(
                    hil_alignment.get("not_real_hil_when_status_is_missing_blocked_or_software_proof", True)
                ),
            },
            "mismatch_summary": mismatch_summary,
            "next_rehearsal_decision": next_decision or "continue_operator_review",
            "not_proven": _route_task_rehearsal_not_proven(review),
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_SCHEMA or source_boundary != ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_schema",
                "read_error": "route/task rehearsal operator review schema or evidence boundary is unsupported",
                "safe_copy": "Route/task rehearsal operator review is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "Route/task rehearsal operator review is not a supported diagnostics source; no delivery result is proven.",
                "next_rehearsal_decision": "regenerate_supported_operator_review_package",
            }
        )
        return summary

    if _route_task_rehearsal_review_safe_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_copy",
                "read_error": "route/task rehearsal operator review safe_copy is missing or unsafe",
                "safe_copy": "Route/task rehearsal operator review copy was blocked because it could imply control or delivery success.",
                "safe_phone_copy": "Route/task rehearsal operator review copy was blocked because it could imply control or delivery success.",
                "next_rehearsal_decision": "rewrite_phone_safe_operator_review_copy",
            }
        )
        return summary

    summary["safe_copy"] = safe_copy
    summary["safe_phone_copy"] = safe_copy
    if crosscheck_status == "pass":
        summary.update(
            {
                "overall_status": "degraded",
                "state": "crosscheck_pass",
                "next_rehearsal_decision": next_decision or "continue_rehearsal_review_without_control_actions",
            }
        )
        return summary
    if crosscheck_status == "fail":
        summary.update(
            {
                "overall_status": "blocked",
                "state": "crosscheck_fail",
                "safe_copy": "Route/task rehearsal operator review found mismatches; keep proof blocked and not_proven.",
                "safe_phone_copy": "Route/task rehearsal operator review found mismatches; keep proof blocked and not_proven.",
                "next_rehearsal_decision": next_decision or "fix_mismatches_and_regenerate_review_package",
            }
        )
        return summary

    summary.update(
        {
            "overall_status": "blocked",
            "state": "unsupported_status",
            "read_error": "route/task rehearsal operator review crosscheck status is missing or unsupported",
            "safe_copy": "Route/task rehearsal operator review has no supported crosscheck result; proof remains blocked.",
            "safe_phone_copy": "Route/task rehearsal operator review has no supported crosscheck result; proof remains blocked.",
            "next_rehearsal_decision": "regenerate_review_with_crosscheck_pass_or_fail",
        }
    )
    return summary

def summarize_pc_route_debug_console(path):
    """构建 PC route debug console 的 metadata-only diagnostics 摘要。"""
    console_path = os.path.expanduser(str(path or ""))
    summary = _default_pc_route_debug_console_summary(
        console_path,
        read_error="pc route debug console summary is not configured",
    )
    if not console_path:
        return summary
    if not os.path.exists(console_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "pc route debug console summary not found",
                "safe_copy": "PC route debug console summary is missing; this is not delivery success.",
                "safe_phone_copy": "PC route debug console summary is missing; this is not delivery success.",
                "availability": {
                    "status": "blocked",
                    "reason": "summary file missing",
                },
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(console_path, "r", encoding="utf-8") as f:
            console = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading pc route debug console summary: {exc}"
                ),
                "safe_copy": "PC route debug console summary could not be read; keep proof blocked.",
                "safe_phone_copy": "PC route debug console summary could not be read; keep proof blocked.",
                "availability": {
                    "status": "blocked",
                    "reason": "summary JSON read error",
                },
            }
        )
        return summary

    if not isinstance(console, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "pc route debug console JSON must be an object",
                "safe_copy": "PC route debug console summary shape is invalid; proof remains blocked.",
                "safe_phone_copy": "PC route debug console summary shape is invalid; proof remains blocked.",
            }
        )
        return summary

    source_schema = str(console.get("schema") or "")
    source_boundary = str(console.get("evidence_boundary") or "")
    safe_copy = _redact_route_task_rehearsal_text(
        console.get("safe_copy") or console.get("safe_phone_copy") or ""
    )
    availability = console.get("availability") if isinstance(console.get("availability"), dict) else {}
    route_debug_status = (
        console.get("route_debug_status")
        if isinstance(console.get("route_debug_status"), dict)
        else {}
    )
    route_elevator_reconciliation = _summarize_pc_route_elevator_reconciliation(
        console.get("route_elevator_reconciliation"),
        source_boundary,
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": console.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "availability": _safe_pc_route_debug_dict(availability),
            "route_debug_status": _safe_pc_route_debug_dict(route_debug_status),
            "route_progress": _safe_pc_route_debug_dict(console.get("route_progress")),
            "keyframe_preflight": _safe_pc_route_debug_dict(console.get("keyframe_preflight")),
            "recent_task_summary": _safe_pc_route_debug_dict(
                console.get("recent_task_summary") or console.get("recent_task")
            ),
            "route_elevator_reconciliation": route_elevator_reconciliation,
            "not_proven": _pc_route_debug_not_proven(console),
            "read_error": "",
        }
    )
    if source_schema != PC_ROUTE_DEBUG_CONSOLE_SCHEMA or source_boundary != PC_ROUTE_DEBUG_CONSOLE_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_schema",
                "read_error": "pc route debug console schema or evidence boundary is unsupported",
                "safe_copy": "PC route debug console summary is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "PC route debug console summary is not a supported diagnostics source; no delivery result is proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary

    if _pc_route_debug_safe_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_copy",
                "read_error": "pc route debug console safe_copy is missing or unsafe",
                "safe_copy": "PC route debug console copy was blocked because it could imply control or delivery success.",
                "safe_phone_copy": "PC route debug console copy was blocked because it could imply control or delivery success.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsafe support copy",
                },
            }
        )
        return summary

    availability_status = str(availability.get("status") or console.get("status") or "").strip().lower()
    blocked_statuses = {"", "blocked", "missing", "read_error", "unsupported_schema", "unsafe_copy"}
    summary["safe_copy"] = safe_copy
    summary["safe_phone_copy"] = safe_copy
    if availability_status in blocked_statuses:
        summary.update(
            {
                "overall_status": "blocked",
                "state": availability_status or "blocked",
            }
        )
        return summary

    summary.update(
        {
            "overall_status": "degraded",
            "state": "available",
        }
    )
    return summary

def summarize_route_task_rehearsal_execution_bundle(path):
    """构建只读、仅元数据的 route/task rehearsal execution bundle 摘要。"""
    bundle_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_rehearsal_execution_bundle_summary(
        bundle_path,
        read_error="route/task rehearsal execution bundle is not configured",
    )
    if not bundle_path:
        return summary
    if not os.path.exists(bundle_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route/task rehearsal execution bundle not found",
                "safe_phone_copy": "Route/task rehearsal execution bundle is missing; this is not delivery success.",
                "next_step": "Regenerate the execution bundle manifest, then reopen diagnostics.",
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(bundle_path, "r", encoding="utf-8") as f:
            bundle = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading route/task rehearsal execution bundle: {exc}"
                ),
                "safe_phone_copy": "Route/task rehearsal execution bundle could not be read; keep proof not_proven.",
                "next_step": "Fix the manifest JSON and rerun the bundle generator.",
            }
        )
        return summary

    if not isinstance(bundle, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route/task rehearsal execution bundle JSON must be an object",
                "safe_phone_copy": "Route/task rehearsal execution bundle shape is invalid; proof remains not_proven.",
                "next_step": "Regenerate a JSON object manifest from route_task_rehearsal_bundle.",
            }
        )
        return summary

    source_schema = str(bundle.get("schema") or "")
    source_boundary = str(bundle.get("evidence_boundary") or "")
    diagnostics_summary = bundle.get("diagnostics_summary") if isinstance(bundle.get("diagnostics_summary"), dict) else {}
    artifact_summary = bundle.get("artifact_summary") if isinstance(bundle.get("artifact_summary"), dict) else {}
    artifacts = bundle.get("artifacts") if isinstance(bundle.get("artifacts"), dict) else {}
    not_proven_source = bundle.get("not_proven")
    if not isinstance(not_proven_source, list):
        not_proven_source = diagnostics_summary.get("not_proven")
    if not isinstance(not_proven_source, list):
        not_proven_source = artifact_summary.get("not_proven")
    if not isinstance(not_proven_source, list):
        not_proven_source = []
    artifact_ref = _first_route_task_rehearsal_value(
        bundle.get("route_task_rehearsal_artifact_ref"),
        bundle.get("rehearsal_artifact_ref"),
        bundle.get("artifact_ref"),
        bundle.get("artifact_path"),
        artifacts.get("route_task_rehearsal_artifact"),
        artifacts.get("rehearsal_artifact"),
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": bundle.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "evidence_ref": _safe_route_task_rehearsal_ref(
                _first_route_task_rehearsal_value(
                    bundle.get("evidence_ref"),
                    diagnostics_summary.get("evidence_ref"),
                    artifact_summary.get("evidence_ref"),
                )
            ),
            "artifact_ref": _safe_route_task_rehearsal_ref(artifact_ref),
            "artifact_state": _redact_route_task_rehearsal_text(
                _first_route_task_rehearsal_value(
                    diagnostics_summary.get("state"),
                    artifact_summary.get("state"),
                    bundle.get("artifact_state"),
                )
            ),
            "not_proven": _route_task_rehearsal_not_proven({"not_proven": not_proven_source}),
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_SCHEMA or source_boundary != ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_GATE:
        summary.update(
            {
                "state": "unsupported_schema",
                "read_error": "route/task rehearsal execution bundle schema or evidence boundary is unsupported",
                "safe_phone_copy": "Route/task rehearsal execution bundle is not a supported diagnostics source; no delivery result is proven.",
                "next_step": "Regenerate the manifest with the supported execution bundle schema and boundary.",
            }
        )
        return summary

    # 新旧生成器可能把 crosscheck/HIL 摘要放在 manifest 顶层、diagnostics_summary 或 artifact_summary；只读合并即可。
    crosscheck = bundle.get("crosscheck_status") if isinstance(bundle.get("crosscheck_status"), dict) else {}
    if not crosscheck:
        crosscheck = (
            diagnostics_summary.get("crosscheck_status")
            if isinstance(diagnostics_summary.get("crosscheck_status"), dict)
            else {}
        )
    if not crosscheck:
        crosscheck = (
            artifact_summary.get("crosscheck_status")
            if isinstance(artifact_summary.get("crosscheck_status"), dict)
            else {}
        )
    hil_alignment = bundle.get("hil_alignment_status") if isinstance(bundle.get("hil_alignment_status"), dict) else {}
    if not hil_alignment:
        hil_alignment = (
            diagnostics_summary.get("hil_alignment_status")
            if isinstance(diagnostics_summary.get("hil_alignment_status"), dict)
            else {}
        )
    if not hil_alignment:
        hil_alignment = (
            artifact_summary.get("hil_alignment_status")
            if isinstance(artifact_summary.get("hil_alignment_status"), dict)
            else {}
        )
    crosscheck_status = str(crosscheck.get("status") or "").strip().lower()
    software_mismatches = crosscheck.get("software_mismatches")
    hil_mismatches = hil_alignment.get("mismatches")
    summary["crosscheck_status"] = {
        "status": _redact_route_task_rehearsal_text(crosscheck_status),
        "scope": _redact_route_task_rehearsal_text(
            crosscheck.get("scope") or "status/replay/task_record software alignment only"
        ),
        "software_mismatch_count": len(software_mismatches) if isinstance(software_mismatches, list) else 0,
        "software_mismatches": _safe_route_task_rehearsal_list(software_mismatches),
    }
    alignment_status = str(hil_alignment.get("alignment_status") or "not_proven").strip()
    summary["hil_alignment_status"] = {
        "status": _redact_route_task_rehearsal_text(hil_alignment.get("status", "")),
        "alignment_status": _redact_route_task_rehearsal_text(alignment_status or "not_proven"),
        "evidence_ref_match": bool(hil_alignment.get("evidence_ref_match", False)),
        "not_real_hil_when_status_is_missing_blocked_or_software_proof": bool(
            hil_alignment.get("not_real_hil_when_status_is_missing_blocked_or_software_proof", True)
        ),
        "detail": _redact_route_task_rehearsal_text(
            hil_alignment.get("detail") or "not real HIL; execution bundle remains software proof"
        ),
        "mismatch_count": len(hil_mismatches) if isinstance(hil_mismatches, list) else 0,
    }

    if crosscheck_status == "pass":
        summary.update(
            {
                "state": "crosscheck_pass",
                "safe_phone_copy": "Route/task rehearsal execution bundle crosscheck passed as Docker/local software proof only; it is not delivery success.",
                "next_step": "Use the bundle for support/replay handoff, then collect real Nav2/fixed-route and HIL evidence before claiming delivery.",
            }
        )
        return summary
    if crosscheck_status == "fail":
        summary.update(
            {
                "state": "crosscheck_fail",
                "safe_phone_copy": "Route/task rehearsal execution bundle crosscheck failed; keep route/task proof blocked and not_proven.",
                "next_step": "Inspect sanitized software mismatches, fix source inputs, and regenerate the execution bundle.",
            }
        )
        return summary

    summary.update(
        {
            "state": "unsupported_status",
            "read_error": "route/task rehearsal execution bundle crosscheck status is missing or unsupported",
            "safe_phone_copy": "Route/task rehearsal execution bundle has no supported crosscheck result; no route or delivery pass is proven.",
            "next_step": "Regenerate the manifest with crosscheck_status.status pass or fail.",
        }
    )
    return summary

