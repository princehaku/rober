import re

from ros2_trashbot_behavior.operator_gateway_http import (
    CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_EVIDENCE_BOUNDARY,
    CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_FALSE_STATES,
    CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_NOT_PROVEN,
    CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_SCHEMA,
    PHONE_ACK_ACCEPTED_RESULT_PENDING_ACK_SEMANTICS,
    PHONE_ACK_ACCEPTED_RESULT_PENDING_CAPABILITY,
    PHONE_ACK_ACCEPTED_RESULT_PENDING_DEGRADATION_STATE,
    PHONE_ACK_ACCEPTED_RESULT_PENDING_GUARD_BOUNDARY,
    PHONE_ACK_ACCEPTED_RESULT_PENDING_SAFE_PHONE_COPY,
    PHONE_CANCEL_PENDING_ACK_SEMANTICS,
    PHONE_CANCEL_PENDING_COMMAND_SAFETY_CAPABILITY,
    PHONE_CANCEL_PENDING_COMMAND_SAFETY_GUARD_BOUNDARY,
    PHONE_CANCEL_PENDING_SAFE_PHONE_COPY,
    PHONE_TERMINAL_RESULT_PENDING_DEGRADATION_STATE,
    PHONE_TERMINAL_RESULT_PENDING_RETRY_HINT,
    PHONE_TERMINAL_RESULT_PENDING_SAFE_PHONE_COPY,
    PHONE_TERMINAL_RESULT_VERIFICATION_CAPABILITY,
    PHONE_TERMINAL_RESULT_VERIFICATION_GUARD_BOUNDARY,
)


# 本模块只处理云端降级 guard 的 Robot-safe 摘要；不能访问云端、ROS topic、串口或硬件。
CLOUD_UNREACHABLE_MALFORMED_RESPONSE_GUARD_BOUNDARY = (
    "software_proof_docker_cloud_unreachable_malformed_response_guard"
)
CLOUD_UNREACHABLE_MALFORMED_RESPONSE_GUARD_SCHEMA = (
    "trashbot.cloud_unreachable_malformed_response_guard_summary.v1"
)
CLOUD_UNREACHABLE_MALFORMED_RESPONSE_STATES = {"cloud_unreachable", "malformed_response"}
CLOUD_UNREACHABLE_MALFORMED_RESPONSE_FALSE_STATES = (
    "source=software_proof",
    "not_proven",
    "remote_ready=false",
    "safe_to_control=false",
    "delivery_success=false",
    "primary_actions_enabled=false",
)
CLOUD_UNREACHABLE_MALFORMED_RESPONSE_REQUIRED_NOT_PROVEN = (
    "real_public_https_tls",
    "real_4g_or_sim",
    "production_db_queue",
    "oss_cdn_live_traffic",
    "ack_cursor_fetch",
    "retry_replay_resubmit",
    "queue_advancement",
    "robot_command_side_effects",
    "dropoff_or_cancel_completion",
    "route_elevator_field_pass",
    "real_phone_device_or_browser",
    "hil_pass",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)
CLOUD_POLL_BACKOFF_RATE_LIMIT_GUARD_BOUNDARY = (
    "software_proof_docker_cloud_poll_backoff_rate_limit_guard"
)
CLOUD_POLL_BACKOFF_RATE_LIMIT_GUARD_SCHEMA = (
    "trashbot.cloud_poll_backoff_rate_limit_guard_summary.v1"
)
CLOUD_POLL_BACKOFF_FALSE_STATES = (
    "source=software_proof",
    "not_proven",
    "remote_ready=false",
    "safe_to_control=false",
    "delivery_success=false",
    "primary_actions_enabled=false",
)
CLOUD_POLL_BACKOFF_REQUIRED_NOT_PROVEN = (
    "real_public_https_tls",
    "real_4g_or_sim",
    "production_db_queue",
    "oss_cdn_live_traffic",
    "ack_cursor_fetch",
    "robot_command_side_effects",
    "dropoff_or_cancel_completion",
    "route_elevator_field_pass",
    "real_phone_device_or_browser",
    "hil_pass",
    "delivery_success",
)
CLOUD_ACK_LOOKUP_PENDING_STATUS_GUARD_BOUNDARY = (
    "software_proof_docker_cloud_ack_lookup_pending_status_guard"
)
CLOUD_ACK_LOOKUP_PENDING_STATUS_GUARD_SCHEMA = (
    "trashbot.robot_diagnostics_cloud_ack_lookup_pending_status_guard_summary.v1"
)
CLOUD_ACK_LOOKUP_PENDING_FALSE_STATES = (
    "source=software_proof",
    "not_proven",
    "remote_ready=false",
    "safe_to_control=false",
    "delivery_success=false",
    "primary_actions_enabled=false",
)
CLOUD_ACK_LOOKUP_PENDING_REQUIRED_NOT_PROVEN = (
    "real_public_https_tls",
    "real_4g_or_sim",
    "production_db_queue",
    "oss_cdn_live_traffic",
    "ack_completion",
    "ack_cursor_fetch",
    "cursor_update",
    "robot_command_side_effects",
    "dropoff_or_cancel_completion",
    "route_elevator_field_pass",
    "real_phone_device_or_browser",
    "hil_pass",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)
CLOUD_ACK_ACCEPTED_RESULT_PENDING_GUARD_SCHEMA = (
    "trashbot.robot_diagnostics_cloud_ack_accepted_result_pending_guard_summary.v1"
)
CLOUD_ACK_ACCEPTED_RESULT_PENDING_FALSE_STATES = (
    "source=software_proof",
    "not_proven",
    "remote_ready=false",
    "safe_to_control=false",
    "delivery_success=false",
    "primary_actions_enabled=false",
)
CLOUD_ACK_ACCEPTED_RESULT_PENDING_REQUIRED_NOT_PROVEN = (
    "real_public_https_tls",
    "real_4g_or_sim",
    "production_db_queue",
    "oss_cdn_live_traffic",
    "terminal_result",
    "delivery_result",
    "dropoff_completion",
    "cancel_completion",
    "route_elevator_field_pass",
    "real_phone_device_or_browser",
    "hil_pass",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)
CLOUD_TERMINAL_RESULT_VERIFICATION_GUARD_SCHEMA = (
    "trashbot.robot_diagnostics_cloud_terminal_result_verification_guard_summary.v1"
)
CLOUD_TERMINAL_RESULT_VERIFICATION_FALSE_STATES = (
    "source=software_proof",
    "not_proven",
    "remote_ready=false",
    "safe_to_control=false",
    "delivery_success=false",
    "primary_actions_enabled=false",
)
CLOUD_TERMINAL_RESULT_VERIFICATION_REQUIRED_NOT_PROVEN = (
    "real_public_https_tls",
    "real_4g_or_sim",
    "production_db_queue",
    "oss_cdn_live_traffic",
    "terminal_result",
    "delivery_result",
    "dropoff_completion",
    "cancel_completion",
    "route_elevator_field_pass",
    "real_phone_device_or_browser",
    "hil_pass",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)
CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_ROBOT_SCHEMA = (
    "trashbot.robot_diagnostics_cloud_support_handoff_safe_export_summary.v1"
)
CLOUD_CANCEL_PENDING_COMMAND_SAFETY_GUARD_SCHEMA = (
    "trashbot.robot_diagnostics_cloud_cancel_pending_command_safety_guard_summary.v1"
)
CLOUD_CANCEL_PENDING_FALSE_STATES = (
    "source=software_proof",
    "not_proven",
    "remote_ready=false",
    "safe_to_control=false",
    "delivery_success=false",
    "primary_actions_enabled=false",
)
CLOUD_CANCEL_PENDING_REQUIRED_NOT_PROVEN = (
    "real_public_https_tls",
    "real_4g_or_sim",
    "production_db_queue",
    "oss_cdn_live_traffic",
    "real_goal_acceptance",
    "cancel_completion",
    "dropoff_completion",
    "route_elevator_field_pass",
    "real_phone_device_or_browser",
    "hil_pass",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)

_TEXT_REDACTIONS = (
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


def _redact_text(value):
    # guard 摘要会被手机端展示，所以任何原始凭证、URL、串口和 traceback 都必须先脱敏。
    text = str(value or "")
    for pattern, replacement in _TEXT_REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def _cloud_guard_safe_text(value, fallback):
    # 短文案可以透传，但命中敏感材料或控制暗示时退回固定 fail-closed 文案。
    text = _redact_text(value).strip()
    if not text:
        return fallback
    lowered = text.lower()
    forbidden = (
        "[redacted_auth_header]",
        "bearer [redacted]",
        "[redacted_url]",
        "[redacted_traceback]",
        "[redacted_local_path]",
        "[redacted_serial]",
        "[redacted_baud]",
        "authorization",
        "bearer",
        "token",
        "credential",
        "raw response",
        "raw_response",
        "raw body",
        "raw_body",
        "ros topic",
        "/cmd_vel",
        "serial",
        "uart",
        "wave rover",
        "hil pass",
    )
    if any(marker in lowered for marker in forbidden):
        return fallback
    return text[:240]


def _cloud_guard_has_unsafe_material(value):
    # 任何控制成功布尔值、原始响应或硬件/凭证字段都让 summary 保持 blocked_not_proven。
    unsafe_true_keys = {
        "remote_ready",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "ack_cursor_fetch_allowed",
        "cursor_fetch_allowed",
        "retry_allowed",
        "replay_allowed",
        "resubmit_allowed",
        "queue_advancement_allowed",
        "robot_command_side_effects_allowed",
        "dropoff_completion",
        "cancel_completion",
        "hil_pass",
    }
    unsafe_key_fragments = (
        "authorization",
        "bearer",
        "token",
        "credential",
        "password",
        "secret",
        "access_key",
        "oss_ak",
        "oss_sk",
        "db_url",
        "database_url",
        "queue_url",
        "raw_response",
        "raw_body",
        "traceback",
        "local_path",
        "ros_topic",
        "cmd_vel",
        "serial",
        "uart",
        "wave_rover",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _cloud_guard_has_unsafe_material(item):
                return True
        return False
    if isinstance(value, list):
        return any(_cloud_guard_has_unsafe_material(item) for item in value)
    if isinstance(value, str):
        redacted = _redact_text(value)
        lowered = redacted.lower()
        guarded = lowered
        # fail-closed 文案会包含 false 状态；先剔除这些安全短语，避免误判。
        for phrase in (
            "not_delivery_success",
            "not delivery success",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            "not_proven",
            "not proven",
            "不证明",
            "不是送达成功",
        ):
            guarded = guarded.replace(phrase, "")
        return (
            "[redacted_auth_header]" in lowered
            or "bearer [redacted]" in lowered
            or "[redacted_url]" in lowered
            or "[redacted_traceback]" in lowered
            or "[redacted_local_path]" in lowered
            or "raw response" in guarded
            or "raw body" in guarded
            or "credential" in guarded
            or "ros topic" in guarded
            or "/cmd_vel" in guarded
            or "serial" in guarded
            or "uart" in guarded
            or "wave rover" in guarded
            or "hil pass" in guarded
            or "delivery success" in guarded
            or "primary actions enabled" in guarded
        )
    return False


def _dedupe_ordered(values):
    # not_proven 是前端解释顺序，去重时必须保留原顺序而不是转成 set。
    items = []
    for value in values:
        text = _redact_text(value)
        if text and text not in items:
            items.append(text)
    return items


def summarize_cloud_unreachable_malformed_response_guard(value):
    """为云端不可达/畸形响应构建 Robot diagnostics 安全摘要。"""
    source = value if isinstance(value, dict) else {}
    degradation_state = str(
        source.get("degradation_state")
        or source.get("state")
        or source.get("status")
        or ""
    ).strip()
    fallback_copy = {
        "cloud_unreachable": "云端暂时不可达；当前不能下发主操作，请刷新状态或联系支持。",
        "malformed_response": "云端响应格式异常；机器人没有确认执行，请刷新状态或联系支持。",
    }.get(degradation_state, "云端响应不可用；Robot/API 保持 fail-closed。")
    unsupported = degradation_state not in CLOUD_UNREACHABLE_MALFORMED_RESPONSE_STATES
    unsafe = _cloud_guard_has_unsafe_material(source)
    status = (
        "not_applicable"
        if unsupported and not source
        else "unsupported_degradation_not_proven"
        if unsupported
        else "blocked_unsafe_material_not_proven"
        if unsafe
        else f"{degradation_state}_not_proven"
    )
    safe_copy = _cloud_guard_safe_text(source.get("safe_phone_copy"), fallback_copy)
    return {
        "schema": CLOUD_UNREACHABLE_MALFORMED_RESPONSE_GUARD_SCHEMA,
        "schema_version": 1,
        "guard": "cloud_unreachable_malformed_response_guard",
        "source": "software_proof",
        "evidence_boundary": CLOUD_UNREACHABLE_MALFORMED_RESPONSE_GUARD_BOUNDARY,
        "status": status,
        "degradation_state": degradation_state if not unsupported else "not_applicable",
        "remote_ready": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_cursor_fetch_allowed": False,
        "retry_replay_resubmit_allowed": False,
        "queue_advancement_allowed": False,
        "robot_command_side_effects_allowed": False,
        "retry_hint": (
            str(source.get("retry_hint") or "contact_support").strip()
            if degradation_state == "malformed_response"
            else str(source.get("retry_hint") or "retry_cloud").strip()
        ),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "false_states": list(CLOUD_UNREACHABLE_MALFORMED_RESPONSE_FALSE_STATES),
        "not_proven": list(CLOUD_UNREACHABLE_MALFORMED_RESPONSE_REQUIRED_NOT_PROVEN),
        "raw_material_redacted": bool(unsafe),
    }


def _remote_readiness_for_cloud_guard(summary):
    # phone_readiness 仍需要 remote_readiness；这里只回填安全字段，不带 raw cloud body。
    if not isinstance(summary, dict):
        return {}
    degradation_state = str(summary.get("degradation_state") or "")
    if degradation_state not in CLOUD_UNREACHABLE_MALFORMED_RESPONSE_STATES:
        return {}
    return {
        "remote_ready": False,
        "cloud_reachable": degradation_state != "cloud_unreachable",
        "last_command_ack": "",
        "status_stale": True,
        "retry_hint": summary.get("retry_hint", "contact_support"),
        "auth_state": "required",
        "degradation_state": degradation_state,
        "safe_phone_copy": summary.get("safe_phone_copy", ""),
        "status_age_sec": None,
        "pending_command_count": 0,
        "queue_persisted": False,
        "state_path_configured": False,
        "proof_schema": "",
        "ack_semantics": "cloud_guard_not_delivery_success",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "proof_boundary": CLOUD_UNREACHABLE_MALFORMED_RESPONSE_GUARD_BOUNDARY,
    }


def summarize_cloud_poll_backoff_rate_limit_guard(value):
    """为 cloud poll backoff / rate-limit 构建 Robot diagnostics 安全摘要。"""
    source = value if isinstance(value, dict) else {}
    degradation_state = str(source.get("degradation_state") or source.get("state") or "").strip()
    applicable = degradation_state == "cloud_poll_backoff"
    unsafe = _cloud_guard_has_unsafe_material(source)
    fallback_copy = "远程轮询正在等待重试窗口，主操作保持不可用；这不是送达成功。"
    status = (
        "not_applicable"
        if not source
        else "unsupported_degradation_not_proven"
        if not applicable
        else "blocked_unsafe_material_not_proven"
        if unsafe
        else "cloud_poll_backoff_not_proven"
    )
    safe_copy = _cloud_guard_safe_text(source.get("safe_phone_copy"), fallback_copy)
    summary = {
        "schema": CLOUD_POLL_BACKOFF_RATE_LIMIT_GUARD_SCHEMA,
        "schema_version": 1,
        "guard": "cloud_poll_backoff_rate_limit_guard",
        "source": "software_proof",
        "evidence_boundary": CLOUD_POLL_BACKOFF_RATE_LIMIT_GUARD_BOUNDARY,
        "status": status,
        "degradation_state": "cloud_poll_backoff" if applicable else "not_applicable",
        "remote_ready": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_cursor_fetch_allowed": False,
        "retry_replay_resubmit_allowed": False,
        "queue_advancement_allowed": False,
        "robot_command_side_effects_allowed": False,
        "retry_hint": "wait_for_backoff_window",
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "false_states": list(CLOUD_POLL_BACKOFF_FALSE_STATES),
        "not_proven": list(CLOUD_POLL_BACKOFF_REQUIRED_NOT_PROVEN),
        "raw_material_redacted": bool(unsafe),
    }
    # backoff 时间只允许数值形态进入摘要，避免 URL/token 字符串混入。
    for key in ("backoff_until", "backoff_duration_sec"):
        if source.get(key) is None:
            continue
        try:
            summary[key] = float(source.get(key))
        except (TypeError, ValueError):
            pass
    return summary


def _remote_readiness_for_poll_backoff_guard(summary):
    # phone_readiness 只需要脱敏后的 backoff 元数据，不能带入 URL、token 或 traceback。
    if not isinstance(summary, dict) or summary.get("degradation_state") != "cloud_poll_backoff":
        return {}
    readiness = {
        "remote_ready": False,
        "cloud_reachable": True,
        "last_command_ack": "",
        "status_stale": True,
        "retry_hint": "wait_for_backoff_window",
        "auth_state": "required",
        "degradation_state": "cloud_poll_backoff",
        "safe_phone_copy": summary.get("safe_phone_copy", ""),
        "status_age_sec": None,
        "pending_command_count": 0,
        "queue_persisted": False,
        "state_path_configured": False,
        "proof_schema": "",
        "ack_semantics": "poll_backoff_not_delivery_success",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "proof_boundary": CLOUD_POLL_BACKOFF_RATE_LIMIT_GUARD_BOUNDARY,
    }
    for key in ("backoff_until", "backoff_duration_sec"):
        if summary.get(key) is not None:
            readiness[key] = summary[key]
    return readiness


def summarize_cloud_ack_lookup_pending_status_guard(value):
    """为 ACK 查询缺失构建 Robot diagnostics 安全摘要。"""
    source = value if isinstance(value, dict) else {}
    degradation_state = str(source.get("degradation_state") or source.get("state") or "").strip()
    applicable = degradation_state == "ack_lookup_pending"
    unsafe = _cloud_guard_has_unsafe_material(source)
    fallback_copy = "机器人尚未处理该命令，请继续等待或联系支持。"
    status = (
        "not_applicable"
        if not source
        else "unsupported_degradation_not_proven"
        if not applicable
        else "blocked_unsafe_material_not_proven"
        if unsafe
        else "ack_lookup_pending_not_proven"
    )
    safe_copy = _cloud_guard_safe_text(source.get("safe_phone_copy"), fallback_copy)
    return {
        "schema": CLOUD_ACK_LOOKUP_PENDING_STATUS_GUARD_SCHEMA,
        "schema_version": 1,
        "capability": "cloud_ack_lookup_pending_status_guard",
        "source": "software_proof",
        "evidence_boundary": CLOUD_ACK_LOOKUP_PENDING_STATUS_GUARD_BOUNDARY,
        "status": status,
        "degradation_state": "ack_lookup_pending" if applicable else "not_applicable",
        "remote_ready": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_completion_proven": False,
        "ack_cursor_fetch_allowed": False,
        "cursor_updates_allowed": False,
        "robot_command_side_effects_allowed": False,
        "retry_hint": "continue_polling_or_contact_support",
        "ack_semantics": "ack_lookup_pending_not_delivery_success",
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "false_states": list(CLOUD_ACK_LOOKUP_PENDING_FALSE_STATES),
        "not_proven": list(CLOUD_ACK_LOOKUP_PENDING_REQUIRED_NOT_PROVEN),
        "raw_material_redacted": bool(unsafe),
    }


def _remote_readiness_for_ack_lookup_pending_guard(summary):
    # diagnostics 只能回填 canonical pending，不带 command path、raw ACK body 或 traceback。
    if not isinstance(summary, dict) or summary.get("degradation_state") != "ack_lookup_pending":
        return {}
    return {
        "capability": "cloud_ack_lookup_pending_status_guard",
        "remote_ready": False,
        "cloud_reachable": True,
        "last_command_ack": "",
        "status_stale": False,
        "retry_hint": "continue_polling_or_contact_support",
        "auth_state": "required",
        "degradation_state": "ack_lookup_pending",
        "safe_phone_copy": summary.get(
            "safe_phone_copy",
            "机器人尚未处理该命令，请继续等待或联系支持。",
        ),
        "status_age_sec": None,
        "pending_command_count": 1,
        "queue_persisted": False,
        "state_path_configured": False,
        "proof_schema": "",
        "ack_semantics": "ack_lookup_pending_not_delivery_success",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "proof_boundary": CLOUD_ACK_LOOKUP_PENDING_STATUS_GUARD_BOUNDARY,
    }


def summarize_cloud_ack_accepted_result_pending_guard(value):
    """为 ACK accepted/processing 但缺少终态结果构建 Robot diagnostics 安全摘要。"""
    source = value if isinstance(value, dict) else {}
    degradation_state = str(source.get("degradation_state") or source.get("state") or "").strip()
    applicable = degradation_state == PHONE_ACK_ACCEPTED_RESULT_PENDING_DEGRADATION_STATE
    unsafe = _cloud_guard_has_unsafe_material(source)
    status = (
        "not_applicable"
        if not source
        else "unsupported_degradation_not_proven"
        if not applicable
        else "blocked_unsafe_material_not_proven"
        if unsafe
        else "ack_accepted_result_pending_not_proven"
    )
    safe_copy = _cloud_guard_safe_text(
        source.get("safe_phone_copy"),
        PHONE_ACK_ACCEPTED_RESULT_PENDING_SAFE_PHONE_COPY,
    )
    return {
        "schema": CLOUD_ACK_ACCEPTED_RESULT_PENDING_GUARD_SCHEMA,
        "schema_version": 1,
        "capability": PHONE_ACK_ACCEPTED_RESULT_PENDING_CAPABILITY,
        "source": "software_proof",
        "evidence_boundary": PHONE_ACK_ACCEPTED_RESULT_PENDING_GUARD_BOUNDARY,
        "status": status,
        "degradation_state": (
            PHONE_ACK_ACCEPTED_RESULT_PENDING_DEGRADATION_STATE
            if applicable
            else "not_applicable"
        ),
        "remote_ready": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "terminal_result_proven": False,
        "delivery_result_proven": False,
        "dropoff_completion_proven": False,
        "cancel_completion_proven": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "robot_command_side_effects_allowed": False,
        "retry_hint": "wait_for_delivery_result_or_contact_support",
        "ack_semantics": PHONE_ACK_ACCEPTED_RESULT_PENDING_ACK_SEMANTICS,
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "false_states": list(CLOUD_ACK_ACCEPTED_RESULT_PENDING_FALSE_STATES),
        "not_proven": list(CLOUD_ACK_ACCEPTED_RESULT_PENDING_REQUIRED_NOT_PROVEN),
        "raw_material_redacted": bool(unsafe),
    }


def _remote_readiness_for_ack_accepted_result_pending_guard(summary):
    # diagnostics 只回填 canonical O5 pending，不允许携带 terminal result 或 delivery 成功暗示。
    if (
        not isinstance(summary, dict)
        or summary.get("degradation_state")
        != PHONE_ACK_ACCEPTED_RESULT_PENDING_DEGRADATION_STATE
    ):
        return {}
    return {
        "capability": PHONE_ACK_ACCEPTED_RESULT_PENDING_CAPABILITY,
        "remote_ready": False,
        "cloud_reachable": True,
        "last_command_ack": "",
        "status_stale": False,
        "retry_hint": "wait_for_delivery_result_or_contact_support",
        "auth_state": "required",
        "degradation_state": PHONE_ACK_ACCEPTED_RESULT_PENDING_DEGRADATION_STATE,
        "safe_phone_copy": summary.get(
            "safe_phone_copy",
            PHONE_ACK_ACCEPTED_RESULT_PENDING_SAFE_PHONE_COPY,
        ),
        "status_age_sec": None,
        "pending_command_count": 0,
        "queue_persisted": False,
        "state_path_configured": False,
        "proof_schema": "",
        "ack_semantics": PHONE_ACK_ACCEPTED_RESULT_PENDING_ACK_SEMANTICS,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "proof_boundary": PHONE_ACK_ACCEPTED_RESULT_PENDING_GUARD_BOUNDARY,
    }


def summarize_cloud_terminal_result_verification_guard(value):
    """为非终态 terminal/delivery/dropoff/cancel 字段构建 Robot diagnostics 安全摘要。"""
    source = value if isinstance(value, dict) else {}
    degradation_state = str(source.get("degradation_state") or source.get("state") or "").strip()
    applicable = degradation_state == PHONE_TERMINAL_RESULT_PENDING_DEGRADATION_STATE
    unsafe = _cloud_guard_has_unsafe_material(source)
    status = (
        "not_applicable"
        if not source
        else "unsupported_degradation_not_proven"
        if not applicable
        else "blocked_unsafe_material_not_proven"
        if unsafe
        else "terminal_result_pending_not_proven"
    )
    safe_copy = _cloud_guard_safe_text(
        source.get("safe_phone_copy"),
        PHONE_TERMINAL_RESULT_PENDING_SAFE_PHONE_COPY,
    )
    return {
        "schema": CLOUD_TERMINAL_RESULT_VERIFICATION_GUARD_SCHEMA,
        "schema_version": 1,
        "capability": PHONE_TERMINAL_RESULT_VERIFICATION_CAPABILITY,
        "source": "software_proof",
        "evidence_boundary": PHONE_TERMINAL_RESULT_VERIFICATION_GUARD_BOUNDARY,
        "status": status,
        "degradation_state": (
            PHONE_TERMINAL_RESULT_PENDING_DEGRADATION_STATE
            if applicable
            else "not_applicable"
        ),
        "remote_ready": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "terminal_result_proven": False,
        "delivery_result_proven": False,
        "dropoff_completion_proven": False,
        "cancel_completion_proven": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "robot_command_side_effects_allowed": False,
        "retry_hint": PHONE_TERMINAL_RESULT_PENDING_RETRY_HINT,
        "ack_semantics": PHONE_ACK_ACCEPTED_RESULT_PENDING_ACK_SEMANTICS,
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "false_states": list(CLOUD_TERMINAL_RESULT_VERIFICATION_FALSE_STATES),
        "not_proven": list(CLOUD_TERMINAL_RESULT_VERIFICATION_REQUIRED_NOT_PROVEN),
        "raw_material_redacted": bool(unsafe),
    }


def _remote_readiness_for_terminal_result_verification_guard(summary):
    # diagnostics 只回填 canonical terminal_result_pending，不能沿用上游非终态字符串做成功依据。
    if (
        not isinstance(summary, dict)
        or summary.get("degradation_state")
        != PHONE_TERMINAL_RESULT_PENDING_DEGRADATION_STATE
    ):
        return {}
    return {
        "capability": PHONE_TERMINAL_RESULT_VERIFICATION_CAPABILITY,
        "remote_ready": False,
        "cloud_reachable": True,
        "last_command_ack": "",
        "status_stale": False,
        "retry_hint": PHONE_TERMINAL_RESULT_PENDING_RETRY_HINT,
        "auth_state": "required",
        "degradation_state": PHONE_TERMINAL_RESULT_PENDING_DEGRADATION_STATE,
        "safe_phone_copy": summary.get(
            "safe_phone_copy",
            PHONE_TERMINAL_RESULT_PENDING_SAFE_PHONE_COPY,
        ),
        "status_age_sec": None,
        "pending_command_count": 0,
        "queue_persisted": False,
        "state_path_configured": False,
        "proof_schema": "",
        "ack_semantics": PHONE_ACK_ACCEPTED_RESULT_PENDING_ACK_SEMANTICS,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "proof_boundary": PHONE_TERMINAL_RESULT_VERIFICATION_GUARD_BOUNDARY,
    }


def summarize_cloud_cancel_pending_command_safety_guard(value):
    """为 cancel pending goal acceptance 构建 Robot diagnostics 安全摘要。"""
    source = value if isinstance(value, dict) else {}
    degradation_state = str(source.get("degradation_state") or source.get("state") or "").strip()
    applicable = degradation_state == "cancel_pending_goal_acceptance"
    unsafe = _cloud_guard_has_unsafe_material(source)
    status = (
        "not_applicable"
        if not source
        else "unsupported_degradation_not_proven"
        if not applicable
        else "blocked_unsafe_material_not_proven"
        if unsafe
        else "cancel_pending_goal_acceptance_not_proven"
    )
    safe_copy = _cloud_guard_safe_text(
        source.get("safe_phone_copy"),
        PHONE_CANCEL_PENDING_SAFE_PHONE_COPY,
    )
    return {
        "schema": CLOUD_CANCEL_PENDING_COMMAND_SAFETY_GUARD_SCHEMA,
        "schema_version": 1,
        "capability": PHONE_CANCEL_PENDING_COMMAND_SAFETY_CAPABILITY,
        "source": "software_proof",
        "evidence_boundary": PHONE_CANCEL_PENDING_COMMAND_SAFETY_GUARD_BOUNDARY,
        "status": status,
        "degradation_state": "cancel_pending_goal_acceptance" if applicable else "not_applicable",
        "remote_ready": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "cancel_completion_proven": False,
        "retry_hint": "wait_for_goal_acceptance",
        "ack_semantics": PHONE_CANCEL_PENDING_ACK_SEMANTICS,
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "false_states": list(CLOUD_CANCEL_PENDING_FALSE_STATES),
        "not_proven": list(CLOUD_CANCEL_PENDING_REQUIRED_NOT_PROVEN),
        "raw_material_redacted": bool(unsafe),
    }


def _remote_readiness_for_cancel_pending_guard(summary):
    # diagnostics core 只回填安全 remote_readiness，避免 raw status 文案进入手机首屏。
    if not isinstance(summary, dict) or summary.get("degradation_state") != "cancel_pending_goal_acceptance":
        return {}
    return {
        "capability": PHONE_CANCEL_PENDING_COMMAND_SAFETY_CAPABILITY,
        "remote_ready": False,
        "cloud_reachable": True,
        "last_command_ack": "",
        "status_stale": False,
        "retry_hint": "wait_for_goal_acceptance",
        "auth_state": "required",
        "degradation_state": "cancel_pending_goal_acceptance",
        "safe_phone_copy": summary.get("safe_phone_copy", PHONE_CANCEL_PENDING_SAFE_PHONE_COPY),
        "status_age_sec": None,
        "pending_command_count": 0,
        "queue_persisted": False,
        "state_path_configured": False,
        "proof_schema": "",
        "ack_semantics": PHONE_CANCEL_PENDING_ACK_SEMANTICS,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "proof_boundary": PHONE_CANCEL_PENDING_COMMAND_SAFETY_GUARD_BOUNDARY,
    }


def summarize_cloud_support_handoff_safe_export(value):
    """为 cloud degraded-state 支持交接导出构建 Robot diagnostics 安全摘要。"""
    source = value if isinstance(value, dict) else {}
    unsupported = bool(source) and source.get("schema") not in {
        CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_SCHEMA,
        CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_ROBOT_SCHEMA,
    }
    unsafe = _cloud_guard_has_unsafe_material(source)
    status = (
        "missing_cloud_support_handoff_safe_export"
        if not source
        else "blocked_unsupported_cloud_support_handoff_safe_export"
        if unsupported
        else "blocked_unsafe_cloud_support_handoff_safe_export"
        if unsafe
        else str(source.get("status") or "ready_for_cloud_support_handoff_safe_export_not_proven")
    )
    # Robot alias 只镜像已经脱敏的 export 摘要，避免 diagnostics core 转发 raw body。
    safe_copy = _cloud_guard_safe_text(
        source.get("safe_copy") or source.get("safe_phone_copy"),
        (
            "cloud_support_handoff_safe_export is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
    )
    export_refs = source.get("export_refs") if isinstance(source.get("export_refs"), dict) else {}
    okr_context = source.get("okr_context") if isinstance(source.get("okr_context"), dict) else {}
    safe_refs = {
        str(key): _cloud_guard_safe_text(item, "")
        for key, item in export_refs.items()
        if _cloud_guard_safe_text(item, "")
    }
    safe_okr_context = {
        key: _cloud_guard_safe_text(
            okr_context.get(key),
            "",
        )
        for key in (
            "lowest_objective",
            "reference_objective",
            "pr5_thread_id",
            "pr5_reply_comment_id",
            "pr5_material_state",
        )
        if _cloud_guard_safe_text(okr_context.get(key), "")
    }
    source_not_proven = (
        list(source.get("not_proven"))
        if isinstance(source.get("not_proven"), list)
        else []
    )
    not_proven = _dedupe_ordered(
        source_not_proven + list(CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_NOT_PROVEN)
    )
    return {
        "schema": CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_ROBOT_SCHEMA,
        "source_schema": CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_SCHEMA,
        "schema_version": 1,
        "capability": "cloud_support_handoff_safe_export",
        "source": "software_proof",
        "evidence_boundary": CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_EVIDENCE_BOUNDARY,
        "status": status,
        "degradation_state": _cloud_guard_safe_text(source.get("degradation_state"), "status_stale"),
        "safe_phone_copy": _cloud_guard_safe_text(
            source.get("safe_phone_copy"),
            "云端降级支持交接包已生成；主操作保持不可用。",
        ),
        "safe_copy": safe_copy,
        "support_bundle_id": _cloud_guard_safe_text(source.get("support_bundle_id"), ""),
        "support_level": _cloud_guard_safe_text(source.get("support_level"), "support_required"),
        "next_action": _cloud_guard_safe_text(source.get("next_action"), "contact_support"),
        "export_refs": safe_refs,
        "okr_context": safe_okr_context,
        "false_states": list(CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_FALSE_STATES),
        "not_proven": not_proven,
        "remote_ready": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "raw_material_redacted": bool(unsafe),
    }
