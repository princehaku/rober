from ros2_trashbot_behavior.operator_media_preflight import build_o7_board_media_preflight


O7_BOARD_REALTIME_STATUS_SCHEMA = "trashbot.o7_board_realtime_status.v1"
O7_BOARD_REALTIME_STATUS_BOUNDARY = "software_proof_o7_board_realtime_status_contract"


O7_BOARD_REALTIME_UNSAFE_TEXT_MARKERS = (
    "/cmd_vel",
    "/dev/ttyusb",
    "authorization",
    "bearer",
    "token",
    "secret",
    "password",
)


O7_BOARD_REALTIME_UNSAFE_BOOL_KEYS = {
    "enabled",
    "safe_to_control",
    "primary_actions_enabled",
    "delivery_success",
}


O7_BOARD_REALTIME_REQUIRED_NOT_PROVEN = [
    "real_rtc_session",
    "real_camera_video_source",
    "real_asr_stream",
    "real_tts_playback",
    "manual_control_hil",
    "nav_goal_hil",
]


O7_BOARD_REALTIME_NEXT_REQUIRED_EVIDENCE = [
    "cloud_relay_consumes_o7_board_realtime_status",
    "pc_tools_consumes_o7_board_realtime_status",
    "real_rtc_offer_answer_and_media_trace",
    "camera_frame_evidence_with_timestamp",
    "asr_partial_and_final_transcript_trace",
    "tts_audio_playback_trace",
    "manual_control_hil_with_safe_stop",
    "nav_goal_hil_with_cancel_and_timeout",
]


O7_BOARD_REALTIME_SAFE_STATES = {
    "not_configured",
    "not_proven",
    "software_contract_ready",
    "degraded",
    "blocked",
}


O7_BOARD_REALTIME_POLICY_FIELDS = (
    "state",
    "enabled",
    "safe_to_control",
    "reason",
    "accepted_commands",
    "not_proven",
    "next_required_evidence",
)


def _safe_string(value, default):
    # 状态字段会被 cloud-relay/PC 直接展示，统一去空白避免脏输入扩散。
    text = str(value or "").strip()
    return text if text else default


def _safe_state(value, default="not_proven"):
    # O7 当前只有软件契约证据，未知状态必须降级为 not_proven。
    state = _safe_string(value, default)
    return state if state in O7_BOARD_REALTIME_SAFE_STATES else default


def _safe_list(value, default=None):
    # 只接受显式 list/tuple，避免字符串被拆成逐字符证据项。
    if not isinstance(value, (list, tuple)):
        return list(default or [])
    return [str(item).strip() for item in value if str(item).strip()]


def _safe_media_text(value, default=""):
    # 外部 media source 可能来自 status 文件或 cloud mock，进入 realtime 前必须再次清洗。
    text = str(value or "").strip()
    if not text:
        return default
    lower = text.lower()
    if any(marker in lower for marker in O7_BOARD_REALTIME_UNSAFE_TEXT_MARKERS):
        return "redacted_unsafe_input"
    return text[:160]


def _sanitize_media_source_value(value):
    # 递归清洗外部 summary，避免 path_checks/capabilities 里的原始危险字段透传给 PC/cloud。
    redacted = False
    if isinstance(value, dict):
        result = {}
        for raw_key, raw_item in value.items():
            safe_key = _safe_media_text(raw_key, default="field")
            redacted = redacted or safe_key == "redacted_unsafe_input"
            if safe_key in O7_BOARD_REALTIME_UNSAFE_BOOL_KEYS:
                result[safe_key] = False
                redacted = redacted or bool(raw_item)
                continue
            if safe_key == "accepted_commands":
                result[safe_key] = []
                redacted = redacted or bool(raw_item)
                continue
            safe_item, item_redacted = _sanitize_media_source_value(raw_item)
            redacted = redacted or item_redacted
            result[safe_key] = safe_item
        return result, redacted
    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            safe_item, item_redacted = _sanitize_media_source_value(item)
            redacted = redacted or item_redacted
            result.append(safe_item)
        return result, redacted
    if isinstance(value, str):
        safe_value = _safe_media_text(value)
        return safe_value, safe_value == "redacted_unsafe_input"
    if isinstance(value, (bool, int, float)) or value is None:
        return value, False
    return _safe_media_text(value), False


def _safe_policy(value, *, reason):
    # 控制策略必须 fail-closed：外部 status 文件不能把手控或导航目标打开。
    source = value if isinstance(value, dict) else {}
    policy = {key: source.get(key) for key in O7_BOARD_REALTIME_POLICY_FIELDS}
    policy["state"] = _safe_state(policy.get("state"), default="blocked")
    policy["enabled"] = False
    policy["safe_to_control"] = False
    policy["reason"] = _safe_string(policy.get("reason"), reason)
    policy["accepted_commands"] = []
    policy["not_proven"] = _safe_list(
        policy.get("not_proven"),
        default=["manual_control_hil", "nav_goal_hil"],
    )
    policy["next_required_evidence"] = _safe_list(
        policy.get("next_required_evidence"),
        default=["hil_with_safe_stop_and_timeout"],
    )
    return policy


def _source_realtime_status(latest_status):
    # 兼容未来生产者写入 board_realtime_status 或 o7_board_realtime_status。
    latest_status = latest_status if isinstance(latest_status, dict) else {}
    for key in ("o7_board_realtime_status", "board_realtime_status"):
        value = latest_status.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _source_media_preflight(latest_status, realtime_source):
    # preflight 可来自顶层，也可嵌在 realtime status；两种来源都不能直接打开设备。
    latest_status = latest_status if isinstance(latest_status, dict) else {}
    realtime_source = realtime_source if isinstance(realtime_source, dict) else {}
    for source in (realtime_source, latest_status):
        for key in ("o7_board_media_preflight", "media_preflight"):
            value = source.get(key)
            if isinstance(value, dict):
                return value
    return {}


def _normalize_media_preflight(source):
    # 已有 summary 只作为输入事实；缺字段时用本地默认 preflight contract 补齐。
    source = source if isinstance(source, dict) else {}
    source, source_redacted = _sanitize_media_source_value(source)
    summary = build_o7_board_media_preflight()
    for key in (
        "overall_state",
        "device_probe_allowed",
        "device_probe_attempted",
        "capabilities",
        "path_checks",
        "blocked",
        "not_proven",
        "next_required_evidence",
    ):
        if key in source:
            summary[key] = source[key]
    summary["schema"] = "trashbot.o7_board_media_preflight.v1"
    summary["schema_version"] = 1
    summary["overall_state"] = _safe_state(summary.get("overall_state"), default="blocked")
    summary["safe_to_control"] = False
    summary["primary_actions_enabled"] = False
    summary["software_proof_only"] = True
    if source_redacted:
        # redaction 本身也是 blocked 证据，消费者需要知道 source 被降级处理过。
        summary["overall_state"] = "blocked"
        summary["source_safety"] = "redacted_unsafe_input"
        summary["blocked"] = _safe_list(summary.get("blocked"))
        if "unsafe_media_preflight_source_redacted" not in summary["blocked"]:
            summary["blocked"].append("unsafe_media_preflight_source_redacted")
        summary["not_proven"] = _safe_list(summary.get("not_proven"))
        if "safe_media_preflight_source" not in summary["not_proven"]:
            summary["not_proven"].append("safe_media_preflight_source")
        summary["next_required_evidence"] = _safe_list(summary.get("next_required_evidence"))
        if "provide_redacted_media_preflight_source" not in summary["next_required_evidence"]:
            summary["next_required_evidence"].insert(0, "provide_redacted_media_preflight_source")
    return summary


def build_o7_board_realtime_status(latest_status=None):
    """构建板端 O7 实时能力状态摘要；只报告 readiness，不启动 RTC 或控制链路。"""
    source = _source_realtime_status(latest_status)
    media_preflight = _normalize_media_preflight(_source_media_preflight(latest_status, source))
    not_proven = _safe_list(source.get("not_proven"), default=O7_BOARD_REALTIME_REQUIRED_NOT_PROVEN)
    for item in _safe_list(media_preflight.get("not_proven")):
        if item not in not_proven:
            not_proven.append(item)
    next_required_evidence = _safe_list(
        source.get("next_required_evidence"),
        default=O7_BOARD_REALTIME_NEXT_REQUIRED_EVIDENCE,
    )
    for item in _safe_list(media_preflight.get("next_required_evidence")):
        if item not in next_required_evidence:
            next_required_evidence.append(item)
    status = {
        "schema": O7_BOARD_REALTIME_STATUS_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": O7_BOARD_REALTIME_STATUS_BOUNDARY,
        "source": "operator_gateway_status_contract",
        # media_agent_state 表示本地契约可被消费，不表示真实 RTC 已启动。
        "media_agent_state": _safe_state(
            source.get("media_agent_state"),
            default="software_contract_ready",
        ),
        # video/asr/tts 默认仍缺真实媒体证据，避免 PC 误判可用。
        "video_source_state": _safe_state(source.get("video_source_state")),
        "asr_stream_state": _safe_state(source.get("asr_stream_state")),
        "tts_playback_state": _safe_state(source.get("tts_playback_state")),
        "media_preflight": media_preflight,
        "manual_control_policy": _safe_policy(
            source.get("manual_control_policy"),
            reason="manual control is disabled until HIL proves safe stop and timeout behavior",
        ),
        "nav_goal_policy": _safe_policy(
            source.get("nav_goal_policy"),
            reason="nav goal dispatch is disabled until HIL proves goal, cancel, and timeout behavior",
        ),
        "not_proven": not_proven,
        "next_required_evidence": next_required_evidence,
    }
    # 顶层 ready 只代表 contract 存在；具体能力必须看各子状态和 not_proven。
    status["ready_for_consumers"] = True
    status["primary_actions_enabled"] = False
    status["software_proof_only"] = True
    return status
