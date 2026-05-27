from ros2_trashbot_behavior.operator_media_preflight import build_o7_board_media_preflight


O7_BOARD_REALTIME_STATUS_SCHEMA = "trashbot.o7_board_realtime_status.v1"
O7_BOARD_REALTIME_STATUS_BOUNDARY = "software_proof_o7_board_realtime_status_contract"
O7_REALTIME_ELEVATOR_SNAPSHOT_SCHEMA = "trashbot.o7.realtime_elevator_snapshot.v1"
O7_REALTIME_ELEVATOR_SNAPSHOT_BOUNDARY = (
    "software_proof_operator_gateway_runtime_pose_snapshot"
)


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


def _safe_number(value):
    # 位姿来自 ROS runtime，但 HTTP contract 仍要防御 NaN/Infinity 或测试替身脏输入。
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


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


def _operator_pose_timestamp_ms(robot_pose):
    # operator_gateway 现有 updated_at 是秒级 runtime 时间；O7 snapshot 对外统一毫秒。
    timestamp_sec = _safe_number(robot_pose.get("updated_at"))
    if timestamp_sec is None:
        return None
    return timestamp_sec * 1000.0


def _operator_runtime_robot_pose(robot_pose):
    # 只把 /amcl_pose 的位置摘要暴露给 O7，不把它提升为 /tf 或自动驾驶通过证据。
    robot_pose = robot_pose if isinstance(robot_pose, dict) else {}
    x_m = _safe_number(robot_pose.get("x_m", robot_pose.get("x")))
    y_m = _safe_number(robot_pose.get("y_m", robot_pose.get("y")))
    yaw_rad = _safe_number(robot_pose.get("yaw_rad", robot_pose.get("yaw")))
    timestamp_ms = _operator_pose_timestamp_ms(robot_pose)
    if x_m is None or y_m is None or yaw_rad is None or timestamp_ms is None:
        return None
    return {
        "x_m": x_m,
        "y_m": y_m,
        "yaw_rad": yaw_rad,
        "timestamp_ms": timestamp_ms,
        "pose_source": "operator_gateway_pose_topic",
        "evidence_ref": "operator_gateway:/amcl_pose",
    }


def _operator_pose_freshness(robot_pose, now_ms):
    # age_ms 是单次 HTTP 观测的当前年龄；没有连续刷新证据时不能证明 <2s。
    timestamp_ms = _operator_pose_timestamp_ms(robot_pose if isinstance(robot_pose, dict) else {})
    age_ms = None
    if timestamp_ms is not None and now_ms is not None:
        age_ms = max(0.0, float(now_ms) - timestamp_ms)
    return {
        "timestamp_ms": timestamp_ms,
        "age_ms": age_ms,
        "latency_lt_2s_proven": False,
        "status": "operator_gateway_pose_observed" if timestamp_ms is not None else "blocked_not_proven",
        "evidence_ref": "operator_gateway:/amcl_pose" if timestamp_ms is not None else "missing_pose_freshness_trace",
    }


def _o7_realtime_elevator_empty_snapshot():
    # 无 runtime pose 时保持 fail-closed，避免 PC 把空 snapshot 当成真实 O7-KR1 进展。
    route_membership = {
        "route_id": "not_connected",
        "on_route": False,
        "in_elevator_zone": False,
        "status": "blocked_not_proven",
        "evidence_ref": "missing_route_membership_trace",
    }
    return {
        "schema": O7_REALTIME_ELEVATOR_SNAPSHOT_SCHEMA,
        "schema_version": 1,
        "source": "operator_gateway_runtime",
        "proof_status": "not_proven",
        "evidence_boundary": O7_REALTIME_ELEVATOR_SNAPSHOT_BOUNDARY,
        "contract_source": "onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py",
        "workstation_probe_endpoint": "/api/o7/realtime-elevator-probe",
        "realtime_status": "blocked_not_proven",
        "snapshot_status": "blocked_not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "pc_only": False,
        "robot_control_executed": False,
        "cloud_runtime_fixture_connected": False,
        "real_realtime_api_connected": False,
        "real_ros2_tf_connected": False,
        "local_ros_pose_topic_connected": False,
        "latency_lt_2s_proven": False,
        "real_elevator_state_chain_connected": False,
        "floor_recognition_proven": False,
        "human_takeover_proven": False,
        "map_ref": {
            "id": "not_connected",
            "uri": "",
            "status": "blocked_not_proven",
            "evidence_ref": "missing_real_map_artifact",
        },
        "map_frame": {
            "frame_id": "map",
            "source": "operator_gateway_pose_frame_not_tf",
            "status": "blocked_not_proven",
        },
        "robot_pose": None,
        "pose_freshness": {
            "timestamp_ms": None,
            "age_ms": None,
            "latency_lt_2s_proven": False,
            "status": "blocked_not_proven",
            "evidence_ref": "missing_pose_freshness_trace",
        },
        "route_membership": route_membership,
        "elevator_state_chain": {
            "status": "blocked_not_proven",
            "current_state": "not_connected",
            "sample_count": 0,
            "samples": [],
            "evidence_ref": "missing_elevator_state_chain",
        },
        "current_floor_evidence": {
            "floor_label": "not_connected",
            "confidence": None,
            "floor_recognition_proven": False,
            "status": "blocked_not_proven",
            "evidence_ref": "missing_current_floor_evidence",
        },
        "human_takeover": {
            "required": True,
            "human_takeover_proven": False,
            "reason": "real_elevator_state_chain_not_proven",
            "operator_action": "keep_observe_only_until_real_floor_and_state_chain_exist",
            "status": "blocked_not_proven",
            "evidence_ref": "missing_human_takeover_trace",
        },
        "blocked_reasons": [
            "operator_gateway_pose_not_observed",
            "real_realtime_api_not_connected",
            "ros2_tf_forwarding_not_proven",
            "robot_position_latency_lt_2s_not_proven",
            "route_membership_forced_false",
            "real_elevator_state_chain_not_connected",
            "floor_recognition_not_proven",
            "human_takeover_not_proven",
            "robot_control_disabled",
        ],
        "not_proven": [
            "real_o7_realtime_cloud_stream",
            "real_ros2_tf_forwarding",
            "real_map_artifact",
            "real_robot_pose",
            "robot_position_latency_lt_2s",
            "real_route_membership",
            "real_elevator_zone_membership",
            "real_elevator_state_chain",
            "real_current_floor_recognition",
            "real_human_takeover_reason",
            "delivery_success",
        ],
    }


def build_o7_realtime_elevator_snapshot_from_operator_status(latest_status=None, *, now_ms=None):
    """用 operator_gateway 当前 robot_pose 生成 O7 runtime pose snapshot；不打开控制链路。"""
    latest_status = latest_status if isinstance(latest_status, dict) else {}
    payload = _o7_realtime_elevator_empty_snapshot()
    robot_pose_source = latest_status.get("robot_pose") or latest_status.get("robot_location")
    runtime_pose = _operator_runtime_robot_pose(robot_pose_source)
    if runtime_pose is None:
        return payload
    frame_id = _safe_media_text(
        (robot_pose_source if isinstance(robot_pose_source, dict) else {}).get("frame_id"),
        default="map",
    )
    payload.update(
        {
            "realtime_status": "operator_gateway_pose_observed",
            "snapshot_status": "operator_gateway_pose_observed",
            "local_ros_pose_topic_connected": True,
            "map_frame": {
                "frame_id": frame_id,
                "source": "operator_gateway_pose_topic_not_tf",
                "status": "operator_gateway_pose_observed",
            },
            "robot_pose": runtime_pose,
            "pose_freshness": _operator_pose_freshness(robot_pose_source, now_ms),
            "blocked_reasons": [
                "real_realtime_api_not_connected",
                "ros2_tf_forwarding_not_proven",
                "robot_position_latency_lt_2s_not_proven",
                "route_membership_forced_false",
                "real_elevator_state_chain_not_connected",
                "floor_recognition_not_proven",
                "human_takeover_not_proven",
                "robot_control_disabled",
            ],
            "not_proven": [
                "real_o7_realtime_cloud_stream",
                "real_ros2_tf_forwarding",
                "real_map_artifact",
                "robot_position_latency_lt_2s",
                "real_route_membership",
                "real_elevator_zone_membership",
                "real_elevator_state_chain",
                "real_current_floor_recognition",
                "real_human_takeover_reason",
                "delivery_success",
            ],
        }
    )
    return payload


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
