import re

from ros2_trashbot_behavior.operator_gateway_http import (
    CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_EVIDENCE_BOUNDARY,
    CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_FALSE_STATES,
    CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_NOT_PROVEN,
    CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_SCHEMA,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_EVIDENCE_BOUNDARY,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_FALSE_STATES,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_NOT_PROVEN,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_SCHEMA,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_EVIDENCE_BOUNDARY,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_FALSE_STATES,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_NOT_PROVEN,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_SCHEMA,
    build_cloud_command_lifecycle_replay_acceptance_packet,
    build_cloud_command_lifecycle_replay_drill,
)


# lifecycle 子模块只处理手机可读的安全摘要，不访问 ROS topic、串口或真实云端副作用。
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
    # 与 diagnostics facade 保持同一类敏感字段屏蔽，避免拆分后出现 payload 差异。
    text = str(value or "")
    for pattern, replacement in _TEXT_REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def _dedupe_ordered(values):
    # not_proven 顺序本身是前端解释顺序，去重时不能改成 set。
    items = []
    for value in values:
        text = _redact_text(value)
        if text and text not in items:
            items.append(text)
    return items


def _safe_text(value, fallback):
    # 手机端只展示短安全文案；命中 token、路径、串口等材料时退回固定说明。
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


def _has_unsafe_material(value):
    # 任何成功控制位或原始材料字段都使 summary fail-closed，不能被解释为 proven。
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
            if _has_unsafe_material(item):
                return True
        return False
    if isinstance(value, list):
        return any(_has_unsafe_material(item) for item in value)
    if isinstance(value, str):
        # false-state 文案里会出现 delivery_success=false，先剔除后再判断成功暗示。
        redacted = _redact_text(value)
        lowered = redacted.lower()
        guarded = lowered
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


def summarize_cloud_command_lifecycle_audit_export(value):
    """为 command lifecycle audit/export 构建 Robot diagnostics 安全摘要。"""
    source = value if isinstance(value, dict) else {}
    unsupported = bool(source) and source.get("schema") != CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_SCHEMA
    unsafe = _has_unsafe_material(source)
    command_id = _safe_text(source.get("command_id"), "")
    evidence_ref = _safe_text(source.get("evidence_ref"), "")
    missing_lifecycle_state = bool(
        source.get("missing_lifecycle_state") or not command_id or not evidence_ref
    )
    conflicting_lifecycle_state = bool(source.get("conflicting_lifecycle_state"))
    status = (
        "missing_cloud_command_lifecycle_audit_export"
        if not source
        else "blocked_unsupported_cloud_command_lifecycle_audit_export"
        if unsupported
        else "blocked_unsafe_cloud_command_lifecycle_audit_export"
        if unsafe
        else "blocked_conflicting_lifecycle_state_not_proven"
        if conflicting_lifecycle_state
        else "blocked_missing_lifecycle_state_not_proven"
        if missing_lifecycle_state
        else str(source.get("status") or "ready_for_cloud_command_lifecycle_audit_export_not_proven")
    )
    safe_timeline = []
    # timeline 只保留短字段，避免 raw ACK、cursor 或 command body 进入手机端。
    for item in source.get("lifecycle_timeline") if isinstance(source.get("lifecycle_timeline"), list) else []:
        if not isinstance(item, dict):
            continue
        safe_item = {
            "stage": _safe_text(item.get("stage"), ""),
            "status": _safe_text(item.get("status"), "not_proven"),
            "safe_copy": _safe_text(item.get("safe_copy"), "lifecycle stage remains not_proven."),
        }
        if safe_item["stage"]:
            safe_timeline.append(safe_item)
    source_next_required = (
        source.get("next_required_evidence")
        if isinstance(source.get("next_required_evidence"), list)
        else []
    )
    next_required_evidence = [_safe_text(item, "") for item in source_next_required]
    next_required_evidence = [item for item in next_required_evidence if item]
    if not next_required_evidence:
        next_required_evidence = [
            "same_safe_command_id",
            "same_safe_evidence_ref",
            "verified_terminal_delivery_dropoff_or_cancel_result",
        ]
    source_not_proven = list(source.get("not_proven")) if isinstance(source.get("not_proven"), list) else []
    not_proven = _dedupe_ordered(source_not_proven + list(CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_NOT_PROVEN))
    fallback_copy = (
        "cloud_command_lifecycle_audit_export is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    safe_copy = _safe_text(
        source.get("copy_export_text") or source.get("safe_copy") or source.get("safe_phone_copy"),
        fallback_copy,
    )
    if (
        "safe_to_control=false" not in safe_copy
        or "delivery_success=false" not in safe_copy
        or "primary_actions_enabled=false" not in safe_copy
    ):
        safe_copy = fallback_copy
    return {
        "schema": CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_SCHEMA,
        "schema_version": 1,
        "capability": "cloud_command_lifecycle_audit_export",
        "source": "software_proof",
        "evidence_boundary": CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_EVIDENCE_BOUNDARY,
        "status": status,
        "command_id": command_id,
        "evidence_ref": evidence_ref,
        "lifecycle_state": _safe_text(source.get("lifecycle_state"), "not_proven"),
        "lifecycle_timeline": safe_timeline,
        "terminal_result_status": _safe_text(source.get("terminal_result_status"), "verified_terminal_result_not_proven"),
        "next_required_evidence": next_required_evidence,
        "copy_export_text": safe_copy,
        "safe_copy": safe_copy,
        "safe_phone_copy": _safe_text(source.get("safe_phone_copy"), "命令 lifecycle audit 仍为 software proof；主操作保持不可用。"),
        "false_states": list(CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_FALSE_STATES),
        "not_proven": not_proven,
        "remote_ready": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "robot_command_side_effects_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "missing_lifecycle_state": bool(missing_lifecycle_state),
        "conflicting_lifecycle_state": bool(conflicting_lifecycle_state),
        "raw_material_redacted": bool(unsafe),
    }


def summarize_cloud_command_lifecycle_replay_drill(value):
    """从 audit/export 安全摘要派生只读 command lifecycle replay drill。"""
    audit_summary = summarize_cloud_command_lifecycle_audit_export(value)
    replay_drill = build_cloud_command_lifecycle_replay_drill(audit_summary)
    source = value if isinstance(value, dict) else {}
    unsafe = bool(audit_summary.get("raw_material_redacted")) or _has_unsafe_material(source)
    support_drill_copy = _safe_text(
        replay_drill.get("support_drill_copy") or replay_drill.get("safe_copy"),
        (
            "cloud_command_lifecycle_replay_drill: source=software_proof; "
            "not_proven; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        ),
    )
    if (
        "safe_to_control=false" not in support_drill_copy
        or "delivery_success=false" not in support_drill_copy
        or "primary_actions_enabled=false" not in support_drill_copy
    ):
        support_drill_copy = (
            "cloud_command_lifecycle_replay_drill: source=software_proof; "
            "not_proven; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    status = str(replay_drill.get("status") or "")
    if unsafe and not status.startswith("blocked_unsafe"):
        status = "blocked_unsafe_cloud_command_lifecycle_replay_drill_not_proven"
    replay_timeline = []
    # drill 只读展示阶段状态，不能变成 replay script 或控制入口。
    for item in replay_drill.get("replay_timeline") if isinstance(replay_drill.get("replay_timeline"), list) else []:
        if not isinstance(item, dict):
            continue
        stage = _safe_text(item.get("stage"), "")
        if not stage:
            unsafe = True
            continue
        replay_timeline.append(
            {
                "stage": stage,
                "status": _safe_text(item.get("status"), "not_proven"),
                "safe_copy": _safe_text(item.get("safe_copy"), "lifecycle stage remains not_proven."),
            }
        )
    source_next_required = (
        replay_drill.get("next_required_evidence")
        if isinstance(replay_drill.get("next_required_evidence"), list)
        else []
    )
    source_not_proven = list(replay_drill.get("not_proven")) if isinstance(replay_drill.get("not_proven"), list) else []
    return {
        "schema": CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_SCHEMA,
        "source_schema": CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_SCHEMA,
        "schema_version": 1,
        "capability": "cloud_command_lifecycle_replay_drill",
        "source": "software_proof",
        "evidence_boundary": CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_EVIDENCE_BOUNDARY,
        "status": status or "missing_cloud_command_lifecycle_audit_export",
        "command_id": _safe_text(replay_drill.get("command_id"), ""),
        "evidence_ref": _safe_text(replay_drill.get("evidence_ref"), ""),
        "lifecycle_state": _safe_text(replay_drill.get("lifecycle_state"), "not_proven"),
        "replay_timeline": replay_timeline,
        "lifecycle_timeline": replay_timeline,
        "ack_semantics": _safe_text(replay_drill.get("ack_semantics"), "accepted_processing_only_not_delivery_success"),
        "terminal_result_status": _safe_text(replay_drill.get("terminal_result_status"), "verified_terminal_result_not_proven"),
        "next_required_evidence": [_safe_text(item, "") for item in source_next_required if _safe_text(item, "")],
        "support_drill_copy": support_drill_copy,
        "safe_copy": support_drill_copy,
        "safe_phone_copy": _safe_text(replay_drill.get("safe_phone_copy"), "云命令生命周期复演演练仅为 support drill；主操作保持不可用。"),
        "false_states": list(CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_FALSE_STATES),
        "not_proven": _dedupe_ordered(source_not_proven + list(CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_NOT_PROVEN)),
        "remote_ready": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "command_replay_allowed": False,
        "robot_command_side_effects_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "missing_lifecycle_state": bool(replay_drill.get("missing_lifecycle_state")),
        "conflicting_lifecycle_state": bool(replay_drill.get("conflicting_lifecycle_state")),
        "raw_material_redacted": bool(unsafe),
    }


def _acceptance_packet_has_unsafe_material(value):
    # acceptance packet 比 drill 更靠近验收动作，额外屏蔽 cursor、ACK payload 和 review/GitHub 字段。
    unsafe_true_keys = {
        "remote_ready",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "ack_post_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "command_replay_allowed",
        "command_resubmit_allowed",
        "material_upload_allowed",
        "review_action_allowed",
        "github_action_allowed",
        "robot_command_side_effects_allowed",
        "nav2_triggered",
        "hil_pass",
    }
    unsafe_key_fragments = (
        "authorization",
        "bearer",
        "token",
        "credential",
        "password",
        "secret",
        "signed_url",
        "url_with_secret",
        "raw_path",
        "local_path",
        "raw_response",
        "raw_body",
        "ack_payload",
        "cursor",
        "checksum",
        "complete_artifact",
        "artifact_body",
        "ros_topic",
        "cmd_vel",
        "serial",
        "uart",
        "wave_rover",
        "traceback",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text in unsafe_true_keys:
                if bool(item):
                    return True
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _acceptance_packet_has_unsafe_material(item):
                return True
        return False
    if isinstance(value, list):
        return any(_acceptance_packet_has_unsafe_material(item) for item in value)
    if isinstance(value, str):
        safe_text = _safe_text(value, "")
        guarded = safe_text.lower()
        for phrase in (
            "not_delivery_success",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            "cursor_mutation",
            "not_proven",
            "not proven",
            "不是送达成功",
        ):
            guarded = guarded.replace(phrase, "")
        return (
            safe_text == ""
            and bool(str(value or "").strip())
            or "ack payload" in guarded
            or "cursor" in guarded
            or "checksum" in guarded
            or "complete artifact" in guarded
            or "delivery success" in guarded
            or "safe to control" in guarded
            or "primary actions enabled" in guarded
        )
    return False


def summarize_cloud_command_lifecycle_replay_acceptance_packet(value):
    """从 replay drill 安全摘要派生 owner 验收包，不创建任何控制副作用。"""
    source = value if isinstance(value, dict) else {}
    # 已是 drill summary 时直接使用；否则从 audit/export 安全摘要派生。
    replay_summary = (
        source
        if source.get("schema") == CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_SCHEMA
        else summarize_cloud_command_lifecycle_replay_drill(value)
    )
    packet = build_cloud_command_lifecycle_replay_acceptance_packet(replay_summary)
    unsafe = bool(replay_summary.get("raw_material_redacted")) or _acceptance_packet_has_unsafe_material(source)
    support_acceptance_copy = _safe_text(
        packet.get("support_acceptance_copy") or packet.get("safe_copy"),
        (
            "cloud_command_lifecycle_replay_acceptance_packet: source=software_proof; "
            "not_proven; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        ),
    )
    if (
        "safe_to_control=false" not in support_acceptance_copy
        or "delivery_success=false" not in support_acceptance_copy
        or "primary_actions_enabled=false" not in support_acceptance_copy
    ):
        support_acceptance_copy = (
            "cloud_command_lifecycle_replay_acceptance_packet: source=software_proof; "
            "not_proven; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    status = str(packet.get("status") or "")
    if unsafe and not status.startswith("blocked_unsafe"):
        status = "blocked_unsafe_cloud_command_lifecycle_replay_acceptance_packet_not_proven"
    replay_timeline = []
    # owner 只需要复核阶段和安全文案，不能看到 raw ACK payload 或 cursor。
    for item in packet.get("replay_timeline") if isinstance(packet.get("replay_timeline"), list) else []:
        if not isinstance(item, dict):
            continue
        stage = _safe_text(item.get("stage"), "")
        if not stage:
            unsafe = True
            continue
        replay_timeline.append(
            {
                "stage": stage,
                "status": _safe_text(item.get("status"), "not_proven"),
                "safe_copy": _safe_text(item.get("safe_copy"), "lifecycle stage remains not_proven."),
            }
        )
    source_next_required = packet.get("next_required_evidence") if isinstance(packet.get("next_required_evidence"), list) else []
    source_not_proven = list(packet.get("not_proven")) if isinstance(packet.get("not_proven"), list) else []
    owner_handoff = packet.get("owner_handoff") if isinstance(packet.get("owner_handoff"), dict) else {}
    return {
        "schema": CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_SCHEMA,
        "source_schema": CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_SCHEMA,
        "schema_version": 1,
        "capability": "cloud_command_lifecycle_replay_acceptance_packet",
        "source": "software_proof",
        "evidence_boundary": CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_EVIDENCE_BOUNDARY,
        "status": status or "missing_cloud_command_lifecycle_replay_drill",
        "acceptance_packet_status": status or "missing_cloud_command_lifecycle_replay_drill",
        "command_id": _safe_text(packet.get("command_id"), ""),
        "evidence_ref": _safe_text(packet.get("evidence_ref"), ""),
        "lifecycle_state": _safe_text(packet.get("lifecycle_state"), "not_proven"),
        "replay_timeline": replay_timeline,
        "lifecycle_timeline": replay_timeline,
        "ack_semantics": _safe_text(packet.get("ack_semantics"), "accepted_processing_only_not_delivery_success"),
        "terminal_result_status": _safe_text(packet.get("terminal_result_status"), "pending"),
        "owner_handoff": {
            "handoff_status": _safe_text(owner_handoff.get("handoff_status"), "hardware_material_pending_not_proven"),
            "review_owner": _safe_text(owner_handoff.get("review_owner"), "field_owner"),
            "next_action": _safe_text(owner_handoff.get("next_action"), "collect_same_safe_evidence_ref_terminal_result_material"),
            "pr5_thread_status": _safe_text(owner_handoff.get("pr5_thread_status"), "hardware_material_pending"),
        },
        "next_required_evidence": [_safe_text(item, "") for item in source_next_required if _safe_text(item, "")],
        "support_acceptance_copy": support_acceptance_copy,
        "safe_copy": support_acceptance_copy,
        "safe_phone_copy": _safe_text(packet.get("safe_phone_copy"), "云命令生命周期验收包仅供 owner 复核；主操作保持不可用。"),
        "false_states": list(CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_FALSE_STATES),
        "not_proven": _dedupe_ordered(source_not_proven + list(CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_NOT_PROVEN)),
        "remote_ready": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "command_replay_allowed": False,
        "command_resubmit_allowed": False,
        "material_upload_allowed": False,
        "review_action_allowed": False,
        "github_action_allowed": False,
        "robot_command_side_effects_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "missing_safe_ids": bool(packet.get("missing_safe_ids")),
        "conflicting_lifecycle_state": bool(packet.get("conflicting_lifecycle_state")),
        "raw_material_redacted": bool(unsafe),
    }
