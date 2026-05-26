import json
import os
import re


ROUTE_TASK_FIELD_RUN_READINESS_SCHEMA = "trashbot.route_task_field_run_readiness.v1"
ROUTE_TASK_FIELD_RUN_READINESS_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_readiness_summary.v1"
)
ROUTE_TASK_FIELD_RUN_READINESS_GATE = (
    "software_proof_docker_route_task_field_run_readiness_gate"
)
ROUTE_TASK_FIELD_RUN_INTAKE_SCHEMA = "trashbot.route_task_field_run_intake_crosscheck.v1"
ROUTE_TASK_FIELD_RUN_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_intake_summary.v1"
)
ROUTE_TASK_FIELD_RUN_INTAKE_GATE = (
    "software_proof_docker_route_task_field_run_intake_crosscheck_gate"
)
ROUTE_TASK_FIELD_RUN_REVIEW_SCHEMA = "trashbot.route_task_field_run_review_console.v1"
ROUTE_TASK_FIELD_RUN_REVIEW_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_review_summary.v1"
)
ROUTE_TASK_FIELD_RUN_REVIEW_GATE = (
    "software_proof_docker_route_task_field_run_review_console_gate"
)
ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_SCHEMA = "trashbot.route_task_field_run_execution_pack.v1"
ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_SUMMARY_SCHEMA = (
    "trashbot.route_task_field_run_execution_pack_summary.v1"
)
ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_GATE = (
    "software_proof_docker_route_task_field_run_execution_pack_gate"
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
    # field-run artifact 可能由人工复制，统一先脱敏再进入 diagnostics，避免路径、凭证或串口细节泄露。
    text = str(value or "")
    for pattern, replacement in ROUTE_TASK_REHEARSAL_TEXT_REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def _safe_route_task_rehearsal_ref(value):
    # evidence_ref 可以给 support 看，但本地文件路径只能保留 basename，防止把开发机目录暴露到 API。
    text = str(value or "").strip()
    if not text:
        return ""
    redacted = _redact_route_task_rehearsal_text(text)
    if "[REDACTED_LOCAL_PATH]" in redacted:
        basename = os.path.basename(os.path.expanduser(text).rstrip(os.sep)) or "artifact"
        return f"local_path_redacted:{basename}"
    return redacted


def _safe_route_task_rehearsal_list(value, limit=8):
    # 列表字段只展示前几项摘要，避免把完整现场材料或 raw artifact 带入手机/diagnostics。
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        items.append(_redact_route_task_rehearsal_text(item))
        if len(items) >= limit:
            break
    return items


def _safe_pc_route_debug_value(value, depth=0):
    # 递归脱敏只服务本模块的 phone-safe summary；深度和数量都有限制，避免原始材料外泄。
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
    # 调用方只关心 dict 摘要；非 dict 一律降级为空，防止类型漂移进入 API payload。
    return _safe_pc_route_debug_value(value if isinstance(value, dict) else {})


def _route_task_field_run_readiness_not_proven(readiness=None):
    # field-run readiness 只做下一次上车前材料交接，真实路线、HIL 和交付结论必须始终保留未证明项。
    readiness = readiness if isinstance(readiness, dict) else {}
    values = []
    source_values = readiness.get("not_proven") if isinstance(readiness.get("not_proven"), list) else []
    required = (
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_or_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _route_task_field_run_intake_not_proven(intake=None):
    # intake/crosscheck 只证明材料接收和同 evidence_ref 软件复核；真实运行结论必须单独采集。
    intake = intake if isinstance(intake, dict) else {}
    values = []
    source_values = intake.get("not_proven") if isinstance(intake.get("not_proven"), list) else []
    required = (
        "collect_dropoff_cancel_control",
        "ack_post",
        "cursor_advance_or_persistence",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_or_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _route_task_field_run_review_not_proven(review=None, phone_summary=None):
    # review console 是人工复核摘要，不参与控制面；所有真实动作、ACK、HIL 和交付结论都必须保留未证明。
    review = review if isinstance(review, dict) else {}
    phone_summary = phone_summary if isinstance(phone_summary, dict) else {}
    values = []
    source_values = []
    if isinstance(review.get("not_proven"), list):
        source_values.extend(review.get("not_proven"))
    if isinstance(phone_summary.get("not_proven"), list):
        source_values.extend(phone_summary.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "ack_post",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "production_readiness",
        "dropoff_or_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _route_task_field_run_execution_pack_not_proven(pack=None, phone_summary=None):
    # execution pack 只把现场执行包的材料状态投到 diagnostics；控制面、ACK、HIL 和交付结论都必须显式未证明。
    pack = pack if isinstance(pack, dict) else {}
    phone_summary = phone_summary if isinstance(phone_summary, dict) else {}
    values = []
    source_values = []
    if isinstance(pack.get("not_proven"), list):
        source_values.extend(pack.get("not_proven"))
    if isinstance(phone_summary.get("not_proven"), list):
        source_values.extend(phone_summary.get("not_proven"))
    required = (
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_nav2_fixed_route_run",
        "real_fixed_route_collection",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "production_readiness",
        "dropoff_or_cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _default_route_task_field_run_readiness_summary(path, state="not_configured", read_error=""):
    # readiness artifact 不是控制面状态；默认 blocked 防止缺配置时被手机端误读为可执行路线任务。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_READINESS_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_READINESS_GATE,
        "overall_status": "blocked",
        "availability": {
            "status": "blocked",
            "reason": "route-task field-run readiness artifact is not configured",
        },
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "readiness_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "next_evidence": {
            "summary": "Attach the route-task field-run readiness handoff before planning a real run.",
            "missing_materials": [],
            "required_field_run_materials": [],
        },
        "commands_summary": [],
        "not_proven": _route_task_field_run_readiness_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field-run readiness is not configured; this is metadata-only and not delivery success.",
        "safe_phone_copy": "Route-task field-run readiness is not configured; this is metadata-only and not delivery success.",
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_run_intake_summary(path, state="not_configured", read_error=""):
    # intake/crosscheck 只能作为 diagnostics 元数据；默认 blocked，避免缺 artifact 时误放行手机控制。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_INTAKE_GATE,
        "overall_status": "blocked",
        "availability": {
            "status": "blocked",
            "reason": "route-task field-run intake artifact is not configured",
        },
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "intake_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "crosscheck": {
            "status": "not_proven",
            "missing_materials": [],
            "mismatch_reasons": [],
            "commands_to_rerun": [],
        },
        "not_proven": _route_task_field_run_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field-run intake is not configured; this is metadata-only and not delivery success.",
        "safe_phone_copy": "Route-task field-run intake is not configured; this is metadata-only and not delivery success.",
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_run_review_summary(path, state="not_configured", read_error=""):
    # review console 只把 Autonomy 产出的人工复核报告变成 diagnostics 摘要；默认必须保持控制面全关。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_REVIEW_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_REVIEW_GATE,
        "overall_status": "blocked",
        "availability": {
            "status": "blocked",
            "reason": "route-task field-run review report is not configured",
        },
        "state": state,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "review_ref": _safe_route_task_rehearsal_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "review": {
            "decision": "not_proven",
            "missing_materials": [],
            "mismatch_reasons": [],
            "commands_to_rerun": [],
            "operator_next_steps": [],
        },
        "phone_safe_summary": {},
        "not_proven": _route_task_field_run_review_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field-run review is not configured; this is metadata-only and not delivery success.",
        "safe_phone_copy": "Route-task field-run review is not configured; this is metadata-only and not delivery success.",
        "metadata_only": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_route_task_field_run_execution_pack_summary(path, status="not_configured", read_error=""):
    # execution pack 是现场执行材料的只读摘要，不暴露 artifact 路径，避免 diagnostics 被误当成执行入口。
    return {
        "schema": ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_GATE,
        "status": status,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "materials_status": {
            "status": "blocked",
            "reason": "route-task field-run execution pack is not configured",
        },
        "command_summary": [],
        "not_proven": _route_task_field_run_execution_pack_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": "Route-task field-run execution pack is metadata-only; not delivery success.",
        "safe_phone_copy": "Route-task field-run execution pack is metadata-only; not delivery success.",
        "metadata_only": True,
    }


def _route_task_field_run_readiness_has_unsafe_fields(value, key_path=""):
    # source artifact 可能来自人工拷贝；一旦出现控制/凭证/硬件 raw 字段或成功布尔值，整份 summary 降级。
    unsafe_key_fragments = (
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "credential",
        "checksum",
        "traceback",
        "raw_artifact",
        "raw_json",
        "raw_payload",
        "raw_response",
        "raw_robot",
        "ros_graph",
        "ros_topic",
        "topic_name",
        "serial",
        "uart",
        "baud",
        "cmd_vel",
        "wave_rover",
        "ack_payload",
        "command_envelope",
        "status_envelope",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "ack_post_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "nav2_triggered",
        "hil_pass",
        "production_ready",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "dropoff_completion",
        "cancel_completion",
        "safe_to_control",
        "control_grant",
        "robot_command_allowed",
        "commands_enabled",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            nested_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _route_task_field_run_readiness_has_unsafe_fields(item, nested_path):
                return True
        return False
    if isinstance(value, list):
        return any(_route_task_field_run_readiness_has_unsafe_fields(item, key_path) for item in value)
    if isinstance(value, str):
        redacted = _redact_route_task_rehearsal_text(value)
        return any(marker in redacted for marker in (
            "[REDACTED_AUTH_HEADER]",
            "Bearer [REDACTED]",
            "[REDACTED_URL]",
            "/dev/[REDACTED_SERIAL]",
            "[REDACTED_BAUD]",
            "[REDACTED_TRACEBACK]",
            "[REDACTED_LOCAL_PATH]",
        ))
    return False


def _route_task_field_run_readiness_copy_is_unsafe(value):
    # 支持 copy 可以说 blocked/not_proven，但不能暗示控制动作、HIL 或交付成功已经发生。
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
        "not proven",
        "not_proven",
        "metadata-only",
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


def _route_task_field_run_intake_has_unsafe_control_claims(value):
    # raw 材料可能存在于 source artifact 中，但 diagnostics 只白名单读取摘要；真实控制成功布尔值必须拦截。
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "ack_post_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "nav2_triggered",
        "hil_pass",
        "production_ready",
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
            if _route_task_field_run_intake_has_unsafe_control_claims(item):
                return True
        return False
    if isinstance(value, list):
        return any(_route_task_field_run_intake_has_unsafe_control_claims(item) for item in value)
    return False


def summarize_route_task_field_run_readiness(path):
    """构建 route-task field-run readiness 的 phone/support-safe 摘要。"""
    readiness_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_readiness_summary(
        readiness_path,
        read_error="route-task field-run readiness artifact is not configured",
    )
    if not readiness_path:
        return summary
    if not os.path.exists(readiness_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route-task field-run readiness artifact not found",
                "safe_copy": "Route-task field-run readiness artifact is missing; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run readiness artifact is missing; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "readiness artifact missing",
                },
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(readiness_path, "r", encoding="utf-8") as f:
            readiness = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading route-task field-run readiness artifact: {exc}"
                ),
                "safe_copy": "Route-task field-run readiness artifact could not be read; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run readiness artifact could not be read; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "readiness JSON read error",
                },
            }
        )
        return summary

    if not isinstance(readiness, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route-task field-run readiness JSON must be an object",
                "safe_copy": "Route-task field-run readiness shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run readiness shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    source_schema = str(readiness.get("schema") or "")
    source_boundary = str(readiness.get("evidence_boundary") or "")
    phone_summary = (
        readiness.get("phone_support_safe_summary")
        if isinstance(readiness.get("phone_support_safe_summary"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or readiness.get("safe_copy")
        or readiness.get("safe_phone_copy")
        or "Route-task field-run readiness is metadata-only; not delivery success."
    )
    availability = (
        phone_summary.get("availability")
        if isinstance(phone_summary.get("availability"), dict)
        else readiness.get("availability") if isinstance(readiness.get("availability"), dict) else {}
    )
    missing_materials = _safe_route_task_rehearsal_list(
        phone_summary.get("missing_materials")
        if isinstance(phone_summary.get("missing_materials"), list)
        else readiness.get("missing_materials")
    )
    required_materials = _safe_route_task_rehearsal_list(
        phone_summary.get("required_field_run_materials")
        if isinstance(phone_summary.get("required_field_run_materials"), list)
        else readiness.get("required_field_run_materials")
    )
    commands_summary = _safe_route_task_rehearsal_list(
        phone_summary.get("commands_summary")
        if isinstance(phone_summary.get("commands_summary"), list)
        else readiness.get("commands_to_run")
    )
    next_evidence_summary = _redact_route_task_rehearsal_text(
        phone_summary.get("next_evidence_summary")
        or readiness.get("next_evidence_summary")
        or readiness.get("next_step")
        or "Collect the listed field-run materials with the same evidence_ref before claiming route/task execution."
    )
    overall_status = _redact_route_task_rehearsal_text(
        phone_summary.get("overall_status") or readiness.get("overall_status") or "blocked"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": readiness.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "overall_status": overall_status or "blocked",
            "availability": _safe_pc_route_debug_dict(availability)
            or {
                "status": overall_status or "blocked",
                "reason": "readiness summary consumed without explicit availability",
            },
            "evidence_ref": _safe_route_task_rehearsal_ref(readiness.get("evidence_ref", "")),
            "same_evidence_ref_required": bool(readiness.get("same_evidence_ref_required", True)),
            "next_evidence": {
                "summary": next_evidence_summary,
                "missing_materials": missing_materials,
                "required_field_run_materials": required_materials,
            },
            "commands_summary": commands_summary,
            "not_proven": _route_task_field_run_readiness_not_proven(readiness),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_READINESS_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_READINESS_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_schema",
                "read_error": "route-task field-run readiness schema or evidence boundary is unsupported",
                "safe_copy": "Route-task field-run readiness is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "Route-task field-run readiness is not a supported diagnostics source; no delivery result is proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary

    if _route_task_field_run_readiness_has_unsafe_fields(readiness) or _route_task_field_run_readiness_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_fields",
                "read_error": "route-task field-run readiness contains unsafe fields or copy",
                "safe_copy": "Route-task field-run readiness was blocked because it could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Route-task field-run readiness was blocked because it could expose raw/control data or imply delivery success.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsafe readiness fields",
                },
            }
        )
        return summary

    blocked_statuses = {"", "blocked", "blocked_missing_material", "blocked_unsupported_schema", "missing", "read_error"}
    status_text = str(overall_status or "").strip().lower()
    summary["state"] = "blocked" if status_text in blocked_statuses else "available"
    return summary


def summarize_route_task_field_run_intake(path):
    """构建 route-task field-run intake/crosscheck 的 phone/support-safe 摘要。"""
    intake_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_intake_summary(
        intake_path,
        read_error="route-task field-run intake artifact is not configured",
    )
    if not intake_path:
        return summary
    if not os.path.exists(intake_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route-task field-run intake artifact not found",
                "safe_copy": "Route-task field-run intake artifact is missing; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run intake artifact is missing; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "intake artifact missing",
                },
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(intake_path, "r", encoding="utf-8") as f:
            intake = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "state": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading route-task field-run intake artifact: {exc}"
                ),
                "safe_copy": "Route-task field-run intake artifact could not be read; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run intake artifact could not be read; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "intake JSON read error",
                },
            }
        )
        return summary

    if not isinstance(intake, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route-task field-run intake JSON must be an object",
                "safe_copy": "Route-task field-run intake shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run intake shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    # 支持 Task A 直接输出 phone-safe summary，也支持顶层 artifact 暴露同名摘要别名。
    phone_summary = {}
    for candidate in (
        intake.get("phone_support_safe_summary"),
        intake.get("route_task_field_run_intake_summary"),
        intake.get("route_task_field_run_intake"),
    ):
        if isinstance(candidate, dict):
            phone_summary = candidate
            break
    source_schema = str(intake.get("schema") or "")
    source_boundary = str(intake.get("evidence_boundary") or "")
    overall_status = _redact_route_task_rehearsal_text(
        phone_summary.get("overall_status") or intake.get("overall_status") or "blocked"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or intake.get("safe_copy")
        or intake.get("safe_phone_copy")
        or "Route-task field-run intake is metadata-only; not delivery success."
    )
    availability = (
        phone_summary.get("availability")
        if isinstance(phone_summary.get("availability"), dict)
        else intake.get("availability") if isinstance(intake.get("availability"), dict) else {}
    )
    missing_materials = _safe_route_task_rehearsal_list(
        phone_summary.get("missing_materials")
        if isinstance(phone_summary.get("missing_materials"), list)
        else intake.get("missing_materials")
    )
    mismatch_reasons = _safe_route_task_rehearsal_list(
        phone_summary.get("mismatch_reasons")
        if isinstance(phone_summary.get("mismatch_reasons"), list)
        else intake.get("mismatch_reasons")
    )
    commands_to_rerun = _safe_route_task_rehearsal_list(
        phone_summary.get("commands_to_rerun")
        if isinstance(phone_summary.get("commands_to_rerun"), list)
        else intake.get("commands_to_rerun")
    )
    crosscheck_status = _redact_route_task_rehearsal_text(
        phone_summary.get("crosscheck_status")
        or phone_summary.get("status")
        or intake.get("crosscheck_status")
        or overall_status
        or "not_proven"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": intake.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "overall_status": overall_status or "blocked",
            "availability": _safe_pc_route_debug_dict(availability)
            or {
                "status": overall_status or "blocked",
                "reason": "intake summary consumed without explicit availability",
            },
            "evidence_ref": _safe_route_task_rehearsal_ref(
                phone_summary.get("evidence_ref") or intake.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                phone_summary.get(
                    "same_evidence_ref_required",
                    intake.get("same_evidence_ref_required", True),
                )
            ),
            "crosscheck": {
                "status": crosscheck_status or "not_proven",
                "missing_materials": missing_materials,
                "mismatch_reasons": mismatch_reasons,
                "commands_to_rerun": commands_to_rerun,
            },
            "not_proven": _route_task_field_run_intake_not_proven(intake),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_INTAKE_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_INTAKE_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_schema",
                "read_error": "route-task field-run intake schema or evidence boundary is unsupported",
                "safe_copy": "Route-task field-run intake is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "Route-task field-run intake is not a supported diagnostics source; no delivery result is proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary

    if (
        _route_task_field_run_readiness_has_unsafe_fields(phone_summary)
        or _route_task_field_run_intake_has_unsafe_control_claims(intake)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_fields",
                "read_error": "route-task field-run intake contains unsafe summary fields or control claims",
                "safe_copy": "Route-task field-run intake was blocked because summary fields could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Route-task field-run intake was blocked because summary fields could expose raw/control data or imply delivery success.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsafe intake summary fields",
                },
            }
        )
        return summary

    blocked_statuses = {
        "",
        "blocked",
        "blocked_missing_material",
        "blocked_mismatch",
        "missing",
        "mismatch",
        "read_error",
        "not_proven",
    }
    status_text = str(overall_status or "").strip().lower()
    summary["state"] = "blocked" if status_text in blocked_statuses else "available"
    return summary


def summarize_route_task_field_run_review(path):
    """构建 route-task field-run review console 的 phone/support-safe 摘要。"""
    review_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_review_summary(
        review_path,
        read_error="route-task field-run review report is not configured",
    )
    if not review_path:
        return summary
    if not os.path.exists(review_path):
        summary.update(
            {
                "state": "missing",
                "read_error": "route-task field-run review report not found",
                "safe_copy": "Route-task field-run review report is missing; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run review report is missing; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "review report missing",
                },
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
                    f"failed reading route-task field-run review report: {exc}"
                ),
                "safe_copy": "Route-task field-run review report could not be read; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run review report could not be read; metadata remains blocked/not_proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "review JSON read error",
                },
            }
        )
        return summary

    if not isinstance(review, dict):
        summary.update(
            {
                "state": "read_error",
                "read_error": "route-task field-run review JSON must be an object",
                "safe_copy": "Route-task field-run review shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run review shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    # Task A 可能输出 phone_safe_summary，也可能为了兼容使用既有 phone_support_safe_summary 或同名 summary。
    phone_summary = {}
    for candidate in (
        review.get("phone_safe_summary"),
        review.get("phone_support_safe_summary"),
        review.get("route_task_field_run_review_summary"),
        review.get("route_task_field_run_review"),
    ):
        if isinstance(candidate, dict):
            phone_summary = candidate
            break
    source_schema = str(review.get("schema") or "")
    source_boundary = str(review.get("evidence_boundary") or "")
    overall_status = _redact_route_task_rehearsal_text(
        phone_summary.get("overall_status") or review.get("overall_status") or "blocked"
    )
    review_decision = _redact_route_task_rehearsal_text(
        phone_summary.get("review_decision") or review.get("review_decision") or "not_proven"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or review.get("safe_copy")
        or review.get("safe_phone_copy")
        or "Route-task field-run review is metadata-only; not delivery success."
    )
    availability = (
        phone_summary.get("availability")
        if isinstance(phone_summary.get("availability"), dict)
        else review.get("availability") if isinstance(review.get("availability"), dict) else {}
    )
    missing_materials = _safe_route_task_rehearsal_list(
        phone_summary.get("missing_materials")
        if isinstance(phone_summary.get("missing_materials"), list)
        else review.get("missing_materials")
    )
    mismatch_reasons = _safe_route_task_rehearsal_list(
        phone_summary.get("mismatch_reasons")
        if isinstance(phone_summary.get("mismatch_reasons"), list)
        else review.get("mismatch_reasons")
    )
    commands_to_rerun = _safe_route_task_rehearsal_list(
        phone_summary.get("commands_to_rerun")
        if isinstance(phone_summary.get("commands_to_rerun"), list)
        else review.get("commands_to_rerun")
    )
    operator_next_steps = _safe_route_task_rehearsal_list(
        phone_summary.get("operator_next_steps")
        if isinstance(phone_summary.get("operator_next_steps"), list)
        else review.get("operator_next_steps")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": review.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "overall_status": overall_status or "blocked",
            "availability": _safe_pc_route_debug_dict(availability)
            or {
                "status": overall_status or "blocked",
                "reason": "review summary consumed without explicit availability",
            },
            "evidence_ref": _safe_route_task_rehearsal_ref(
                phone_summary.get("evidence_ref") or review.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                phone_summary.get(
                    "same_evidence_ref_required",
                    review.get("same_evidence_ref_required", True),
                )
            ),
            "review": {
                "decision": review_decision or "not_proven",
                "missing_materials": missing_materials,
                "mismatch_reasons": mismatch_reasons,
                "commands_to_rerun": commands_to_rerun,
                "operator_next_steps": operator_next_steps,
            },
            "phone_safe_summary": _safe_pc_route_debug_dict(phone_summary),
            "not_proven": _route_task_field_run_review_not_proven(review, phone_summary),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_REVIEW_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_REVIEW_GATE:
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsupported_schema",
                "read_error": "route-task field-run review schema or evidence boundary is unsupported",
                "safe_copy": "Route-task field-run review is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "Route-task field-run review is not a supported diagnostics source; no delivery result is proven.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary

    if (
        _route_task_field_run_readiness_has_unsafe_fields(phone_summary)
        or _route_task_field_run_intake_has_unsafe_control_claims(review)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "overall_status": "blocked",
                "state": "unsafe_fields",
                "read_error": "route-task field-run review contains unsafe summary fields or control claims",
                "safe_copy": "Route-task field-run review was blocked because summary fields could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Route-task field-run review was blocked because summary fields could expose raw/control data or imply delivery success.",
                "availability": {
                    "status": "blocked",
                    "reason": "unsafe review summary fields",
                },
            }
        )
        return summary

    blocked_statuses = {
        "",
        "blocked",
        "blocked_missing_material",
        "blocked_mismatch",
        "missing",
        "mismatch",
        "read_error",
        "not_proven",
    }
    status_text = str(overall_status or "").strip().lower()
    summary["state"] = "blocked" if status_text in blocked_statuses else "available"
    return summary


def summarize_route_task_field_run_execution_pack(path):
    """构建 route-task field-run execution pack 的 metadata-only diagnostics 摘要。"""
    pack_path = os.path.expanduser(str(path or ""))
    summary = _default_route_task_field_run_execution_pack_summary(
        pack_path,
        read_error="route-task field-run execution pack is not configured",
    )
    if not pack_path:
        return summary
    if not os.path.exists(pack_path):
        summary.update(
            {
                "status": "missing",
                "read_error": "route-task field-run execution pack not found",
                "materials_status": {
                    "status": "blocked",
                    "reason": "execution pack artifact missing",
                },
                "safe_copy": "Route-task field-run execution pack is missing; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run execution pack is missing; metadata remains blocked/not_proven.",
            }
        )
        return summary

    summary["exists"] = True
    try:
        with open(pack_path, "r", encoding="utf-8") as f:
            pack = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        summary.update(
            {
                "status": "read_error",
                "read_error": _redact_route_task_rehearsal_text(
                    f"failed reading route-task field-run execution pack: {exc}"
                ),
                "materials_status": {
                    "status": "blocked",
                    "reason": "execution pack JSON read error",
                },
                "safe_copy": "Route-task field-run execution pack could not be read; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run execution pack could not be read; metadata remains blocked/not_proven.",
            }
        )
        return summary

    if not isinstance(pack, dict):
        summary.update(
            {
                "status": "read_error",
                "read_error": "route-task field-run execution pack JSON must be an object",
                "materials_status": {
                    "status": "blocked",
                    "reason": "execution pack JSON shape is invalid",
                },
                "safe_copy": "Route-task field-run execution pack shape is invalid; metadata remains blocked/not_proven.",
                "safe_phone_copy": "Route-task field-run execution pack shape is invalid; metadata remains blocked/not_proven.",
            }
        )
        return summary

    # 兼容 artifact 顶层摘要、phone-safe 摘要和同名 summary；只白名单读取可给 diagnostics 的字段。
    phone_summary = {}
    for candidate in (
        pack.get("phone_safe_summary"),
        pack.get("phone_support_safe_summary"),
        pack.get("route_task_field_run_execution_pack_summary"),
        pack.get("route_task_field_run_execution_pack"),
    ):
        if isinstance(candidate, dict):
            phone_summary = candidate
            break
    source_schema = str(pack.get("schema") or "")
    source_boundary = str(pack.get("evidence_boundary") or "")
    status = _redact_route_task_rehearsal_text(
        phone_summary.get("status")
        or phone_summary.get("overall_status")
        or pack.get("status")
        or pack.get("overall_status")
        or "blocked"
    )
    materials_status = (
        phone_summary.get("materials_status")
        if isinstance(phone_summary.get("materials_status"), dict)
        else pack.get("materials_status") if isinstance(pack.get("materials_status"), dict) else {}
    )
    command_source = (
        phone_summary.get("command_summary")
        if "command_summary" in phone_summary
        else phone_summary.get("commands_summary")
        if "commands_summary" in phone_summary
        else pack.get("command_summary")
        if "command_summary" in pack
        else pack.get("commands_summary")
    )
    if isinstance(command_source, list):
        command_summary = _safe_route_task_rehearsal_list(command_source)
    elif isinstance(command_source, dict):
        command_summary = _safe_pc_route_debug_value(command_source)
    elif str(command_source or "").strip():
        command_summary = [_redact_route_task_rehearsal_text(command_source)]
    else:
        command_summary = []
    safe_copy = _redact_route_task_rehearsal_text(
        phone_summary.get("safe_copy")
        or phone_summary.get("safe_phone_copy")
        or pack.get("safe_copy")
        or pack.get("safe_phone_copy")
        or "Route-task field-run execution pack is metadata-only; not delivery success."
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": pack.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "status": status or "blocked",
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                phone_summary.get("evidence_ref")
                or phone_summary.get("safe_evidence_ref")
                or pack.get("evidence_ref", "")
            ),
            "same_evidence_ref_required": bool(
                phone_summary.get(
                    "same_evidence_ref_required",
                    pack.get("same_evidence_ref_required", True),
                )
            ),
            "materials_status": _safe_pc_route_debug_dict(materials_status)
            or {
                "status": status or "blocked",
                "reason": "execution pack consumed without explicit materials status",
            },
            "command_summary": command_summary,
            "not_proven": _route_task_field_run_execution_pack_not_proven(pack, phone_summary),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "read_error": "",
        }
    )
    if source_schema != ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_SCHEMA or source_boundary != ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_GATE:
        summary.update(
            {
                "status": "unsupported_schema",
                "read_error": "route-task field-run execution pack schema or evidence boundary is unsupported",
                "materials_status": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
                "safe_copy": "Route-task field-run execution pack is not a supported diagnostics source; no delivery result is proven.",
                "safe_phone_copy": "Route-task field-run execution pack is not a supported diagnostics source; no delivery result is proven.",
            }
        )
        return summary

    if (
        _route_task_field_run_readiness_has_unsafe_fields(phone_summary)
        or _route_task_field_run_intake_has_unsafe_control_claims(pack)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "status": "unsafe_fields",
                "read_error": "route-task field-run execution pack contains unsafe summary fields or control claims",
                "materials_status": {
                    "status": "blocked",
                    "reason": "unsafe execution pack summary fields",
                },
                "safe_copy": "Route-task field-run execution pack was blocked because summary fields could expose control data or imply delivery success.",
                "safe_phone_copy": "Route-task field-run execution pack was blocked because summary fields could expose control data or imply delivery success.",
            }
        )
        return summary

    return summary
