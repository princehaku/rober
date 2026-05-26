import json
import os
import re


# 本模块只负责 cloud external evidence 的 Robot-safe diagnostics 摘要；不访问 ROS、串口、云端或 GitHub。
EVIDENCE_SOURCE_SOFTWARE = "software_proof"

CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA = (
    "trashbot.cloud_external_evidence_review_decision.v1"
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.cloud_external_evidence_review_decision_summary.v1"
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_cloud_external_evidence_review_decision_summary.v1"
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE = (
    "software_proof_docker_cloud_external_evidence_review_decision_gate"
)
CLOUD_EXTERNAL_EVIDENCE_INTAKE_SCHEMA = "trashbot.external_evidence_intake"
CLOUD_EXTERNAL_EVIDENCE_INTAKE_GATE = "software_proof_docker_external_evidence_intake_gate"
CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_STATUSES = (
    "accepted_external_evidence_not_proven",
    "needs_external_evidence_backfill_not_proven",
    "rejected_unsafe_external_evidence_not_proven",
    "blocked_missing_external_evidence_intake_not_proven",
    "external_evidence_ref_mismatch_not_proven",
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_NOT_PROVEN = (
    "cloud_external_evidence_review_decision_only",
    "source_external_evidence_intake_not_proven",
    "production_ready",
    "external_evidence_complete",
    "real_public_https_tls",
    "real_4g_or_sim",
    "oss_cdn_live_traffic",
    "production_db_queue",
    "worker_cutover_or_migration",
    "verified_terminal_result",
    "true_phone_browser_proof",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
    "okr_percentage_lift",
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.cloud_external_evidence_review_handoff.v1"
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.cloud_external_evidence_review_handoff_summary.v1"
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_cloud_external_evidence_review_handoff_summary.v1"
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_cloud_external_evidence_review_handoff_gate"
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_STATUSES = (
    "ready_for_owner_support_reviewer_handoff_not_proven",
    "needs_external_evidence_backfill_handoff_not_proven",
    "rejected_unsafe_external_evidence_handoff_not_proven",
    "blocked_missing_external_evidence_handoff_not_proven",
    "external_evidence_ref_mismatch_handoff_not_proven",
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_NOT_PROVEN = (
    "cloud_external_evidence_review_handoff_only",
    "source_cloud_external_evidence_review_decision_not_proven",
    "production_ready",
    "external_evidence_complete",
    "real_public_https_tls",
    "real_4g_or_sim",
    "oss_cdn_live_traffic",
    "production_db_queue",
    "worker_cutover_or_migration",
    "verified_terminal_result",
    "true_phone_browser_proof",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
    "okr_percentage_lift",
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SCHEMA = (
    "trashbot.cloud_external_evidence_review_handoff_followup_escalation_status.v1"
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.cloud_external_evidence_review_handoff_followup_escalation_status_summary.v1"
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary.v1"
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_GATE = (
    "software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate"
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_STATUSES = (
    "followup_pending_not_proven",
    "followup_due_soon_not_proven",
    "followup_overdue_not_proven",
    "followup_blocked_missing_external_evidence_not_proven",
    "followup_escalated_to_ceo_not_proven",
    "ready_for_real_external_evidence_followup_not_proven",
    "followup_evidence_ref_mismatch_not_proven",
    "followup_rejected_unsafe_material_not_proven",
)
CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_NOT_PROVEN = (
    "cloud_external_evidence_review_handoff_followup_escalation_status_only",
    "source_cloud_external_evidence_review_handoff_not_proven",
    "upstream_cloud_external_evidence_review_decision_not_proven",
    "production_ready",
    "external_evidence_complete",
    "real_public_https_tls",
    "real_4g_or_sim",
    "oss_cdn_live_traffic",
    "production_db_queue",
    "worker_cutover_or_migration",
    "verified_terminal_result",
    "true_phone_browser_proof",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
    "okr_percentage_lift",
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


def _dedupe_ordered(values):
    # diagnostics 摘要要保持 Hardware gate 的顺序，同时避免重复 not_proven / missing material 文案刷屏。
    items = []
    for value in values:
        text = _redact_route_task_rehearsal_text(value)
        if text and text not in items:
            items.append(text)
    return items


def _cloud_guard_safe_text(value, fallback):
    # 云端异常会进入 diagnostics 和手机摘要；命中敏感信息时用固定文案替代，不回显原始响应。
    text = _redact_route_task_rehearsal_text(value).strip()
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
        redacted = _redact_route_task_rehearsal_text(value)
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
    # external evidence alias 只需要 Robot-safe dict；非 dict 输入按空对象处理，避免 raw artifact 透传。
    return _safe_pc_route_debug_value(value if isinstance(value, dict) else {})


def _real_material_evidence_ref_is_unsafe(value):
    # evidence_ref 只允许短逻辑引用；本地路径、脱敏标记、空白或 shell 字符都不能进入 diagnostics。
    text = str(value or "").strip()
    if (
        not text
        or text.startswith("local_path_redacted:")
        or "[REDACTED" in text
        or not re.fullmatch(r"(?:evidence://)?[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}", text)
    ):
        return True
    return False


def _cloud_external_evidence_review_decision_copy():
    # 这段固定文案是 Robot/API/mobile 的共同边界，避免任一上游缺字段时被误读成可控状态。
    return (
        "cloud_external_evidence_review_decision is metadata-only; "
        "source=software_proof; not_proven; production_ready=false; "
        "overall_status=blocked; external_evidence_complete=false; "
        "delivery_success=false; primary_actions_enabled=false; "
        "safe_to_control=false; not true phone/browser proof; "
        "no OKR percentage lift; PR #5 PRRT_kwDOSWB9286CJ3tX "
        "hardware_material_pending."
    )


def _default_cloud_external_evidence_review_decision_summary(
    status="blocked_missing_external_evidence_intake_not_proven",
    read_error="",
):
    # 缺 Task A 产物时也返回完整 false flags，前端和 Robot 不能把空对象当成已复核。
    safe_copy = _cloud_external_evidence_review_decision_copy()
    reason = read_error or (
        "cloud_external_evidence_review_decision summary is not configured"
    )
    return {
        "schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "cloud_external_evidence_review_decision",
        "source_schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA,
        "source_evidence_boundary": CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE,
        "upstream_source_schema": CLOUD_EXTERNAL_EVIDENCE_INTAKE_SCHEMA,
        "upstream_source_evidence_boundary": CLOUD_EXTERNAL_EVIDENCE_INTAKE_GATE,
        "evidence_boundary": CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE,
        "configured": False,
        "exists": False,
        "status": status,
        "overall_status": "blocked",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "review_decision": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_external_evidence_intake_status": "",
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "material_statuses": {},
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "unsafe_materials": [],
        "decision_reasons": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "operator_support_handoff": [],
        "reviewer_route": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {"safe_copy": safe_copy, "status": status},
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_material_state": "hardware_material_pending",
        "pr5_resolution_claim": "not_pr5_resolution",
        "phone_browser_proof": "not true phone/browser proof",
        "okr_progress_effect": "no OKR percentage lift",
        "not_proven": list(CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_NOT_PROVEN),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
        "production_ready": False,
        "external_evidence_complete": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "true_phone_browser_proof": False,
        "robot_control_allowed": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "cursor_mutation_allowed": False,
        "github_mutation_allowed": False,
        "raw_diagnostics_fetch_allowed": False,
        "material_upload_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "delivery_result_verified": False,
        "okr_percentage_lift": False,
        "pr5_resolved": False,
        "hardware_material_pending": True,
    }


def _cloud_external_evidence_review_decision_summary_fragment(value):
    # 只接受 Task A 的清洗后 summary 或 Robot 自己的 alias；raw artifact 必须留在 PC gate。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SUMMARY_SCHEMA,
    ):
        return value
    for key in (
        "robot_diagnostics_cloud_external_evidence_review_decision_summary",
        "cloud_external_evidence_review_decision_summary",
        "cloud_external_evidence_review_decision",
        "diagnostics_summary",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "summary",
    ):
        candidate = value.get(key)
        nested = _cloud_external_evidence_review_decision_summary_fragment(candidate)
        if nested:
            return nested
    for key in ("diagnostics", "status", "latest_status"):
        nested = _cloud_external_evidence_review_decision_summary_fragment(value.get(key))
        if nested:
            return nested
    return {}


def _cloud_external_evidence_safe_list(value, limit=8):
    # Robot diagnostics 只展示枚举化材料名；任何 raw/path/credential 字样直接丢弃。
    items = []
    for item in value if isinstance(value, list) else []:
        text = _cloud_guard_safe_text(item, "")
        lowered = text.lower()
        if not text or any(
            marker in lowered
            for marker in (
                "raw",
                "credential",
                "authorization",
                "bearer",
                "token",
                "secret",
                "url",
                "endpoint",
                "traceback",
                "checksum",
                "/cmd_vel",
                "serial",
                "uart",
                "wave rover",
            )
        ):
            continue
        items.append(text)
        if len(items) >= limit:
            break
    return items


def _cloud_external_evidence_material_statuses(value):
    # material_statuses 仅保留 family/status/safe_summary，避免把完整材料或外部端点带进 Robot。
    source = value if isinstance(value, dict) else {}
    result = {}
    for name, item in source.items():
        safe_name = _cloud_guard_safe_text(name, "")
        if not safe_name:
            continue
        if isinstance(item, dict):
            safe_item = {
                "status": _cloud_guard_safe_text(item.get("status"), "missing"),
                "safe_summary": _cloud_guard_safe_text(
                    item.get("safe_summary") or item.get("summary"),
                    "metadata-only material status",
                ),
                "redaction_status": _cloud_guard_safe_text(
                    item.get("redaction_status"), "redacted"
                ),
            }
        else:
            safe_item = {"status": _cloud_guard_safe_text(item, "missing")}
        if _cloud_external_evidence_review_decision_has_unsafe_fields(safe_item):
            continue
        result[safe_name[:80]] = safe_item
    return result


def _cloud_external_evidence_review_decision_has_unsafe_fields(value, key_path=""):
    # 上游如果夹带原始 artifact、控制语义、凭证或成功声明，整份 alias 降级为 blocked。
    unsafe_true_keys = {
        "production_ready",
        "external_evidence_complete",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
        "true_phone_browser_proof",
        "robot_control_allowed",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "cursor_mutation_allowed",
        "ack_cursor_mutation_allowed",
        "github_mutation_allowed",
        "raw_diagnostics_fetch_allowed",
        "followup_mutation_allowed",
        "material_upload_allowed",
        "replay_allowed",
        "resubmit_allowed",
        "production_endpoint_allowed",
        "signed_url_allowed",
        "nav2_triggered",
        "hil_pass",
        "delivery_result_verified",
        "okr_percentage_lift",
        "pr5_resolved",
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
        "endpoint",
        "signed_url",
        "raw_",
        "rawartifact",
        "complete_artifact",
        "complete_json",
        "traceback",
        "local_path",
        "checksum",
        "ros_topic",
        "cmd_vel",
        "serial",
        "uart",
        "wave_rover",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if key_text in unsafe_true_keys and item is False:
                continue
            if key_text == "hardware_material_pending" and item is True:
                continue
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _cloud_external_evidence_review_decision_has_unsafe_fields(
                item, f"{key_path}.{key_text}" if key_path else key_text
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _cloud_external_evidence_review_decision_has_unsafe_fields(item, key_path)
            for item in value
        )
    if isinstance(value, str):
        redacted = _redact_route_task_rehearsal_text(value)
        lowered = redacted.lower()
        guarded = lowered
        for phrase in (
            "not true phone/browser proof",
            "no okr percentage lift",
            "not_delivery_success",
            "not delivery success",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            "production_ready=false",
            "external_evidence_complete=false",
            "overall_status=blocked",
            "not_proven",
            "not proven",
            "metadata-only",
            "software_proof",
            "hardware_material_pending",
        ):
            guarded = guarded.replace(phrase, "")
        return any(
            marker in guarded
            for marker in (
                "[redacted_auth_header]",
                "bearer [redacted]",
                "[redacted_url]",
                "[redacted_traceback]",
                "[redacted_local_path]",
                "authorization",
                "bearer",
                "credential",
                "token",
                "secret",
                "raw artifact",
                "raw diagnostics",
                "raw response",
                "raw body",
                "endpoint",
                "url",
                "traceback",
                "checksum",
                "/cmd_vel",
                "ros topic",
                "serial",
                "uart",
                "wave rover",
                "hil pass",
                "delivery success",
                "production ready",
                "external proof passed",
                "true phone",
                "true browser",
                "control enabled",
                "start delivery enabled",
                "confirm dropoff enabled",
                "cancel enabled",
                "okr percentage lift",
                "pr #5 resolved",
                "thread resolved",
            )
        )
    return False


def _cloud_external_evidence_not_proven(summary_fragment):
    values = list(CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_NOT_PROVEN)
    for item in summary_fragment.get("not_proven", []):
        text = _cloud_guard_safe_text(item, "")
        if text and text not in values:
            values.append(text)
    return values


def summarize_cloud_external_evidence_review_decision(source):
    """构建 cloud external evidence review decision 的只读 Robot diagnostics 摘要。"""
    # 该 alias 只转发 Task A 的 safe review summary；Robot 端不读取原始材料也不触发云/机器人动作。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_cloud_external_evidence_review_decision_summary(
        read_error="cloud_external_evidence_review_decision summary is not configured"
    )
    if isinstance(source, dict):
        response = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = "cloud_external_evidence_review_decision summary artifact missing"
            summary["review_decision"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading cloud_external_evidence_review_decision summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_decision"]["reason"] = safe_error
            return summary
    if not isinstance(response, dict):
        summary["review_decision"]["reason"] = (
            "cloud_external_evidence_review_decision JSON must be an object"
        )
        return summary

    summary_fragment = _cloud_external_evidence_review_decision_summary_fragment(response)
    if not summary_fragment:
        summary["review_decision"]["reason"] = (
            "cloud_external_evidence_review_decision input is missing sanitized summary"
        )
        return summary

    decision_doc = (
        summary_fragment.get("review_decision")
        if isinstance(summary_fragment.get("review_decision"), dict)
        else {}
    )
    status = _cloud_guard_safe_text(
        decision_doc.get("status")
        or summary_fragment.get("review_decision_status")
        or summary_fragment.get("decision_status")
        or summary_fragment.get("status"),
        "blocked_missing_external_evidence_intake_not_proven",
    )
    if status not in CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_STATUSES:
        status = "blocked_missing_external_evidence_intake_not_proven"

    safe_copy = _cloud_guard_safe_text(
        summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy"),
        _cloud_external_evidence_review_decision_copy(),
    )
    required_copy = _cloud_external_evidence_review_decision_copy()
    for marker in (
        "source=software_proof",
        "not_proven",
        "production_ready=false",
        "overall_status=blocked",
        "external_evidence_complete=false",
        "delivery_success=false",
        "primary_actions_enabled=false",
        "safe_to_control=false",
        "not true phone/browser proof",
        "no OKR percentage lift",
        "PRRT_kwDOSWB9286CJ3tX",
        "hardware_material_pending",
    ):
        if marker not in safe_copy:
            safe_copy = required_copy
            break

    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    material_statuses = _cloud_external_evidence_material_statuses(
        summary_fragment.get("material_statuses")
    )
    summary.update(
        {
            "configured": True,
            "exists": True,
            "status": status,
            "overall_status": "blocked",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "source_schema_version": summary_fragment.get("source_schema_version")
            or summary_fragment.get("schema_version"),
            "source_schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA,
            "source_evidence_boundary": CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE,
            "upstream_source_schema": _cloud_guard_safe_text(
                summary_fragment.get("upstream_source_schema")
                or summary_fragment.get("source_intake_schema"),
                CLOUD_EXTERNAL_EVIDENCE_INTAKE_SCHEMA,
            ),
            "upstream_source_evidence_boundary": _cloud_guard_safe_text(
                summary_fragment.get("upstream_source_evidence_boundary")
                or summary_fragment.get("source_intake_evidence_boundary"),
                CLOUD_EXTERNAL_EVIDENCE_INTAKE_GATE,
            ),
            "review_decision": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _cloud_guard_safe_text(
                    decision_doc.get("reason") or summary_fragment.get("reason"),
                    "cloud external evidence review decision remains software_proof only",
                ),
            },
            "source_external_evidence_intake_status": _cloud_guard_safe_text(
                summary_fragment.get("source_external_evidence_intake_status")
                or summary_fragment.get("external_evidence_intake_status"),
                "blocked_missing_external_evidence_intake_not_proven",
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or response.get("safe_evidence_ref")
                or response.get("evidence_ref")
                or ""
            ),
            "safe_command_id": _cloud_guard_safe_text(
                summary_fragment.get("safe_command_id")
                or summary_fragment.get("command_id")
                or response.get("safe_command_id")
                or response.get("command_id"),
                "",
            ),
            "material_statuses": material_statuses,
            "accepted_materials": _cloud_external_evidence_safe_list(
                summary_fragment.get("accepted_materials")
                or summary_fragment.get("accepted_materials_summary")
            ),
            "missing_materials": _cloud_external_evidence_safe_list(
                summary_fragment.get("missing_materials")
                or summary_fragment.get("missing_materials_summary")
            ),
            "rejected_materials": _cloud_external_evidence_safe_list(
                summary_fragment.get("rejected_materials")
                or summary_fragment.get("rejected_materials_summary")
            ),
            "unsafe_materials": _cloud_external_evidence_safe_list(
                summary_fragment.get("unsafe_materials")
                or summary_fragment.get("unsafe_materials_summary")
            ),
            "decision_reasons": _cloud_external_evidence_safe_list(
                summary_fragment.get("decision_reasons")
            ),
            "next_required_evidence": _cloud_external_evidence_safe_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _cloud_external_evidence_safe_list(
                summary_fragment.get("owner_handoff")
            ),
            "operator_support_handoff": _cloud_external_evidence_safe_list(
                summary_fragment.get("operator_support_handoff")
                or summary_fragment.get("support_handoff")
            ),
            "reviewer_route": _cloud_external_evidence_safe_list(
                summary_fragment.get("reviewer_route")
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {"safe_copy": safe_copy, "status": status},
            "pr5_thread_id": _cloud_guard_safe_text(
                summary_fragment.get("pr5_thread_id"), "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_material_state": _cloud_guard_safe_text(
                summary_fragment.get("pr5_material_state"), "hardware_material_pending"
            ),
            "pr5_resolution_claim": _cloud_guard_safe_text(
                summary_fragment.get("pr5_resolution_claim"), "not_pr5_resolution"
            ),
            "phone_browser_proof": "not true phone/browser proof",
            "okr_progress_effect": "no OKR percentage lift",
            "not_proven": _cloud_external_evidence_not_proven(summary_fragment),
            "read_error": "",
        }
    )

    required_safe_metadata = (
        str(summary_fragment.get("schema") or "")
        in (
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SUMMARY_SCHEMA,
        ),
        summary["source"] == EVIDENCE_SOURCE_SOFTWARE,
        summary["overall_status"] == "blocked",
        summary_fragment.get("production_ready") is False,
        summary_fragment.get("external_evidence_complete") is False,
        summary_fragment.get("delivery_success") is False,
        summary_fragment.get("primary_actions_enabled") is False,
        summary_fragment.get("safe_to_control") is False,
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_resolution_claim"] == "not_pr5_resolution",
        summary["upstream_source_schema"] == CLOUD_EXTERNAL_EVIDENCE_INTAKE_SCHEMA,
        summary["upstream_source_evidence_boundary"] == CLOUD_EXTERNAL_EVIDENCE_INTAKE_GATE,
        bool(summary["next_required_evidence"]),
    )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or _cloud_external_evidence_review_decision_has_unsafe_fields(response)
        or _cloud_external_evidence_review_decision_has_unsafe_fields(summary_fragment)
        or _cloud_external_evidence_review_decision_has_unsafe_fields(robot_summary)
        or _cloud_external_evidence_review_decision_has_unsafe_fields(safe_copy)
    )
    if unsafe_payload:
        blocked_copy = _cloud_external_evidence_review_decision_copy()
        summary.update(
            {
                "status": "rejected_unsafe_external_evidence_not_proven",
                "review_decision": {
                    "status": "rejected_unsafe_external_evidence_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "cloud external evidence review decision summary contains unsafe fields or missing false-state metadata",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "material_statuses": {},
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "unsafe_materials": [],
                "decision_reasons": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "operator_support_handoff": [],
                "reviewer_route": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
            }
        )
    return summary


def _cloud_external_evidence_review_handoff_copy():
    # handoff 是 review decision 的责任链摘要，不允许被前端或 Robot 误读成外部证据闭环。
    return (
        "cloud_external_evidence_review_handoff is metadata-only; "
        "source=software_proof; not_proven; source_capability="
        "cloud_external_evidence_review_decision; production_ready=false; "
        "overall_status=blocked; external_evidence_complete=false; "
        "delivery_success=false; primary_actions_enabled=false; "
        "safe_to_control=false; not true phone/browser proof; "
        "no OKR percentage lift; PR #5 PRRT_kwDOSWB9286CJ3tX "
        "hardware_material_pending."
    )


def _default_cloud_external_evidence_review_handoff_summary(
    status="blocked_missing_external_evidence_handoff_not_proven",
    read_error="",
):
    # 缺上游 handoff summary 时仍输出完整 false flags，避免 diagnostics 空洞导致按钮误启用。
    safe_copy = _cloud_external_evidence_review_handoff_copy()
    reason = read_error or "cloud_external_evidence_review_handoff summary is not configured"
    return {
        "schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "cloud_external_evidence_review_handoff",
        "source_capability": "cloud_external_evidence_review_decision",
        "source_schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SCHEMA,
        "source_summary_schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        "source_decision_schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA,
        "source_decision_summary_schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        "source_evidence_boundary": CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE,
        "evidence_boundary": CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_GATE,
        "configured": False,
        "exists": False,
        "status": status,
        "overall_status": "blocked",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "handoff_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_review_decision_status": "",
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "owner_route": [],
        "support_route": [],
        "reviewer_route": [],
        "handoff_reasons": [],
        "next_required_evidence": [],
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "unsafe_materials": [],
        "blocked_materials": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {"safe_copy": safe_copy, "status": status},
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_status": "hardware_material_pending",
        "pr5_material_state": "hardware_material_pending",
        "pr5_resolution_claim": "not_pr5_resolution",
        "phone_browser_proof": "not true phone/browser proof",
        "okr_progress_effect": "no OKR percentage lift",
        "not_proven": list(CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_NOT_PROVEN),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
        "production_ready": False,
        "external_evidence_complete": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "true_phone_browser_proof": False,
        "robot_control_allowed": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "cursor_mutation_allowed": False,
        "github_mutation_allowed": False,
        "raw_diagnostics_fetch_allowed": False,
        "handoff_mutation_allowed": False,
        "material_upload_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "delivery_result_verified": False,
        "okr_percentage_lift": False,
        "pr5_resolved": False,
        "hardware_material_pending": True,
    }


def _cloud_external_evidence_review_handoff_summary_fragment(value):
    # Robot 只接受 Task A/PC gate 产出的 safe handoff summary；raw artifact 只可作为被拒输入。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    ):
        return value
    for key in (
        "robot_diagnostics_cloud_external_evidence_review_handoff_summary",
        "cloud_external_evidence_review_handoff_summary",
        "cloud_external_evidence_review_handoff",
        "diagnostics_summary",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "summary",
    ):
        nested = _cloud_external_evidence_review_handoff_summary_fragment(value.get(key))
        if nested:
            return nested
    for key in ("diagnostics", "status", "latest_status"):
        nested = _cloud_external_evidence_review_handoff_summary_fragment(value.get(key))
        if nested:
            return nested
    return {}


def _cloud_external_evidence_handoff_not_proven(summary_fragment):
    # 继承上游附加的 not_proven 项，但固定保留本 rung 的核心边界项。
    values = list(CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_NOT_PROVEN)
    for item in summary_fragment.get("not_proven", []):
        text = _cloud_guard_safe_text(item, "")
        if text and text not in values:
            values.append(text)
    return values


def summarize_cloud_external_evidence_review_handoff(source):
    """构建 cloud external evidence review handoff 的只读 Robot diagnostics 摘要。"""
    # handoff 只把 review decision 后续责任链暴露给 diagnostics，不产生 ACK、GitHub 或机器人控制副作用。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_cloud_external_evidence_review_handoff_summary(
        read_error="cloud_external_evidence_review_handoff summary is not configured"
    )
    if isinstance(source, dict):
        response = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = "cloud_external_evidence_review_handoff summary artifact missing"
            summary["handoff_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading cloud_external_evidence_review_handoff summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["handoff_status"]["reason"] = safe_error
            return summary
    if not isinstance(response, dict):
        summary["handoff_status"]["reason"] = (
            "cloud_external_evidence_review_handoff JSON must be an object"
        )
        return summary

    summary_fragment = _cloud_external_evidence_review_handoff_summary_fragment(response)
    if not summary_fragment:
        summary["handoff_status"]["reason"] = (
            "cloud_external_evidence_review_handoff input is missing sanitized summary"
        )
        return summary

    handoff_doc = (
        summary_fragment.get("handoff_status")
        if isinstance(summary_fragment.get("handoff_status"), dict)
        else {}
    )
    status = _cloud_guard_safe_text(
        handoff_doc.get("status")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status"),
        "blocked_missing_external_evidence_handoff_not_proven",
    )
    if status not in CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_STATUSES:
        status = "blocked_missing_external_evidence_handoff_not_proven"

    safe_copy = _cloud_guard_safe_text(
        summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy"),
        _cloud_external_evidence_review_handoff_copy(),
    )
    required_copy = _cloud_external_evidence_review_handoff_copy()
    for marker in (
        "source=software_proof",
        "not_proven",
        "source_capability=cloud_external_evidence_review_decision",
        "production_ready=false",
        "overall_status=blocked",
        "external_evidence_complete=false",
        "delivery_success=false",
        "primary_actions_enabled=false",
        "safe_to_control=false",
        "not true phone/browser proof",
        "no OKR percentage lift",
        "PRRT_kwDOSWB9286CJ3tX",
        "hardware_material_pending",
    ):
        if marker not in safe_copy:
            safe_copy = required_copy
            break

    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    source_review_decision_status = _cloud_guard_safe_text(
        summary_fragment.get("source_review_decision_status")
        or summary_fragment.get("source_decision_status")
        or summary_fragment.get("review_decision_status"),
        "",
    )
    summary.update(
        {
            "configured": True,
            "exists": True,
            "status": status,
            "overall_status": "blocked",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "source_schema_version": summary_fragment.get("source_schema_version")
            or summary_fragment.get("schema_version"),
            "source_schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SCHEMA,
            "source_summary_schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
            "source_capability": _cloud_guard_safe_text(
                summary_fragment.get("source_capability"),
                "cloud_external_evidence_review_decision",
            ),
            "source_decision_schema": _cloud_guard_safe_text(
                summary_fragment.get("source_decision_schema"),
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA,
            ),
            "source_decision_summary_schema": _cloud_guard_safe_text(
                summary_fragment.get("source_decision_summary_schema"),
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
            ),
            "source_evidence_boundary": _cloud_guard_safe_text(
                summary_fragment.get("source_evidence_boundary")
                or summary_fragment.get("source_proof_boundary"),
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE,
            ),
            "evidence_boundary": CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_GATE,
            "handoff_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _cloud_guard_safe_text(
                    handoff_doc.get("reason") or summary_fragment.get("reason"),
                    "cloud external evidence review handoff remains software_proof only",
                ),
            },
            "source_review_decision_status": source_review_decision_status,
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or response.get("safe_evidence_ref")
                or response.get("evidence_ref")
                or ""
            ),
            "safe_command_id": _cloud_guard_safe_text(
                summary_fragment.get("safe_command_id")
                or summary_fragment.get("command_id")
                or response.get("safe_command_id")
                or response.get("command_id"),
                "",
            ),
            "owner_route": _cloud_external_evidence_safe_list(
                summary_fragment.get("owner_route") or summary_fragment.get("owner_handoff")
            ),
            "support_route": _cloud_external_evidence_safe_list(
                summary_fragment.get("support_route")
                or summary_fragment.get("operator_support_handoff")
                or summary_fragment.get("support_handoff")
            ),
            "reviewer_route": _cloud_external_evidence_safe_list(
                summary_fragment.get("reviewer_route")
            ),
            "handoff_reasons": _cloud_external_evidence_safe_list(
                summary_fragment.get("handoff_reasons")
                or summary_fragment.get("decision_reasons")
            ),
            "next_required_evidence": _cloud_external_evidence_safe_list(
                summary_fragment.get("next_required_evidence")
            ),
            "accepted_materials": _cloud_external_evidence_safe_list(
                summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _cloud_external_evidence_safe_list(
                summary_fragment.get("missing_materials")
            ),
            "rejected_materials": _cloud_external_evidence_safe_list(
                summary_fragment.get("rejected_materials")
            ),
            "unsafe_materials": _cloud_external_evidence_safe_list(
                summary_fragment.get("unsafe_materials")
            ),
            "blocked_materials": _cloud_external_evidence_safe_list(
                summary_fragment.get("blocked_materials")
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {"safe_copy": safe_copy, "status": status},
            "pr5_thread_id": _cloud_guard_safe_text(
                summary_fragment.get("pr5_thread_id"), "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_status": _cloud_guard_safe_text(
                summary_fragment.get("pr5_status"), "hardware_material_pending"
            ),
            "pr5_material_state": _cloud_guard_safe_text(
                summary_fragment.get("pr5_material_state"), "hardware_material_pending"
            ),
            "pr5_resolution_claim": _cloud_guard_safe_text(
                summary_fragment.get("pr5_resolution_claim"), "not_pr5_resolution"
            ),
            "phone_browser_proof": "not true phone/browser proof",
            "okr_progress_effect": "no OKR percentage lift",
            "not_proven": _cloud_external_evidence_handoff_not_proven(summary_fragment),
            "read_error": "",
        }
    )

    required_safe_metadata = (
        str(summary_fragment.get("schema") or "")
        in (
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        ),
        summary["source"] == EVIDENCE_SOURCE_SOFTWARE,
        summary["source_capability"] == "cloud_external_evidence_review_decision",
        summary["source_decision_schema"] == CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA,
        summary["source_evidence_boundary"] == CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE,
        summary["overall_status"] == "blocked",
        summary_fragment.get("production_ready") is False,
        summary_fragment.get("external_evidence_complete") is False,
        summary_fragment.get("delivery_success") is False,
        summary_fragment.get("primary_actions_enabled") is False,
        summary_fragment.get("safe_to_control") is False,
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_status"] == "hardware_material_pending",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_resolution_claim"] == "not_pr5_resolution",
        bool(summary["next_required_evidence"]),
    )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or _cloud_external_evidence_review_decision_has_unsafe_fields(response)
        or _cloud_external_evidence_review_decision_has_unsafe_fields(summary_fragment)
        or _cloud_external_evidence_review_decision_has_unsafe_fields(robot_summary)
        or _cloud_external_evidence_review_decision_has_unsafe_fields(safe_copy)
    )
    if unsafe_payload:
        blocked_copy = _cloud_external_evidence_review_handoff_copy()
        summary.update(
            {
                "status": "rejected_unsafe_external_evidence_handoff_not_proven",
                "handoff_status": {
                    "status": "rejected_unsafe_external_evidence_handoff_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "cloud external evidence review handoff summary contains unsafe fields or missing false-state metadata",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "owner_route": [],
                "support_route": [],
                "reviewer_route": [],
                "handoff_reasons": [],
                "next_required_evidence": [],
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "unsafe_materials": [],
                "blocked_materials": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
            }
        )
    return summary


def _cloud_external_evidence_review_handoff_followup_copy():
    # follow-up escalation 只是 handoff 后的追踪状态，必须把来源链路和 false flags 写在固定文案里。
    return (
        "cloud_external_evidence_review_handoff_followup_escalation_status is "
        "metadata-only; source=software_proof; not_proven; source_capability="
        "cloud_external_evidence_review_handoff; upstream_capability="
        "cloud_external_evidence_review_decision; delivery_success=false; "
        "primary_actions_enabled=false; safe_to_control=false; "
        "not true phone/browser proof; no OKR percentage lift; PR #5 "
        "PRRT_kwDOSWB9286CJ3tX hardware_material_pending."
    )


def _default_cloud_external_evidence_review_handoff_followup_summary(
    status="followup_blocked_missing_external_evidence_not_proven",
    read_error="",
):
    # 缺 PC gate summary 时也返回 Robot-safe alias，避免 diagnostics 使用 raw handoff 或控制字段兜底。
    safe_copy = _cloud_external_evidence_review_handoff_followup_copy()
    reason = read_error or (
        "cloud_external_evidence_review_handoff_followup_escalation_status "
        "summary is not configured"
    )
    return {
        "schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": (
            "cloud_external_evidence_review_handoff_followup_escalation_status"
        ),
        "source_capability": "cloud_external_evidence_review_handoff",
        "upstream_capability": "cloud_external_evidence_review_decision",
        "source_schema": (
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        ),
        "source_summary_schema": (
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA
        ),
        "source_handoff_schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SCHEMA,
        "source_handoff_summary_schema": (
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA
        ),
        "upstream_decision_schema": CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA,
        "upstream_decision_summary_schema": (
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA
        ),
        "source_evidence_boundary": CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_GATE,
        "upstream_evidence_boundary": CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE,
        "evidence_boundary": (
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_GATE
        ),
        "configured": False,
        "exists": False,
        "status": status,
        "overall_status": "blocked",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "followup_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_handoff_status": "",
        "upstream_review_decision_status": "",
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "due_status": "blocked",
        "blocked_reason": "missing sanitized follow-up escalation status summary",
        "owner_action": "",
        "support_action": "",
        "reviewer_action": "",
        "ceo_escalation_recommendation": "blocked_missing_external_evidence",
        "next_required_evidence": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {"safe_copy": safe_copy, "status": status},
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_status": "hardware_material_pending",
        "pr5_material_state": "hardware_material_pending",
        "pr5_resolution_claim": "not_pr5_resolution",
        "phone_browser_proof": "not true phone/browser proof",
        "okr_progress_effect": "no OKR percentage lift",
        "not_proven": list(
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_NOT_PROVEN
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
        "production_ready": False,
        "external_evidence_complete": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "true_phone_browser_proof": False,
        "robot_control_allowed": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "cursor_mutation_allowed": False,
        "ack_cursor_mutation_allowed": False,
        "github_mutation_allowed": False,
        "raw_diagnostics_fetch_allowed": False,
        "handoff_mutation_allowed": False,
        "followup_mutation_allowed": False,
        "material_upload_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "production_endpoint_allowed": False,
        "signed_url_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "delivery_result_verified": False,
        "okr_percentage_lift": False,
        "pr5_resolved": False,
        "hardware_material_pending": True,
    }


def _cloud_external_evidence_review_handoff_followup_summary_fragment(value):
    # 只接受清洗后的 follow-up summary 或 Robot alias；raw command/control payload 必须被拒绝。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    ):
        return value
    for key in (
        "robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary",
        "cloud_external_evidence_review_handoff_followup_escalation_status_summary",
        "cloud_external_evidence_review_handoff_followup_escalation_status",
        "diagnostics_summary",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "summary",
    ):
        nested = _cloud_external_evidence_review_handoff_followup_summary_fragment(
            value.get(key)
        )
        if nested:
            return nested
    for key in ("diagnostics", "status", "latest_status"):
        nested = _cloud_external_evidence_review_handoff_followup_summary_fragment(
            value.get(key)
        )
        if nested:
            return nested
    return {}


def _cloud_external_evidence_review_handoff_followup_not_proven(summary_fragment):
    # 继承 PC gate 的 not_proven 补充项，但核心 Docker/local 证据边界不可被覆盖。
    values = list(
        CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_NOT_PROVEN
    )
    for item in summary_fragment.get("not_proven", []):
        text = _cloud_guard_safe_text(item, "")
        if text and text not in values:
            values.append(text)
    return values


def summarize_cloud_external_evidence_review_handoff_followup_escalation_status(source):
    """构建 handoff follow-up escalation status 的只读 Robot diagnostics 摘要。"""
    # Robot diagnostics 只展示追踪状态，不接受 ACK/cursor、GitHub、endpoint 或机器人控制副作用。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_cloud_external_evidence_review_handoff_followup_summary(
        read_error=(
            "cloud_external_evidence_review_handoff_followup_escalation_status "
            "summary is not configured"
        )
    )
    if isinstance(source, dict):
        response = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "cloud_external_evidence_review_handoff_followup_escalation_status "
                "summary artifact missing"
            )
            summary["followup_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading cloud_external_evidence_review_handoff_followup_"
                f"escalation_status summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["followup_status"]["reason"] = safe_error
            return summary
    if not isinstance(response, dict):
        summary["followup_status"]["reason"] = (
            "cloud_external_evidence_review_handoff_followup_escalation_status JSON "
            "must be an object"
        )
        return summary

    summary_fragment = (
        _cloud_external_evidence_review_handoff_followup_summary_fragment(response)
    )
    if not summary_fragment:
        summary["followup_status"]["reason"] = (
            "cloud_external_evidence_review_handoff_followup_escalation_status input "
            "is missing sanitized summary"
        )
        return summary

    followup_doc = (
        summary_fragment.get("followup_status")
        if isinstance(summary_fragment.get("followup_status"), dict)
        else {}
    )
    status = _cloud_guard_safe_text(
        followup_doc.get("status")
        or summary_fragment.get("followup_status")
        or summary_fragment.get("status"),
        "followup_blocked_missing_external_evidence_not_proven",
    )
    if (
        status
        not in CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_STATUSES
    ):
        status = "followup_blocked_missing_external_evidence_not_proven"

    safe_copy = _cloud_guard_safe_text(
        summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy"),
        _cloud_external_evidence_review_handoff_followup_copy(),
    )
    required_copy = _cloud_external_evidence_review_handoff_followup_copy()
    for marker in (
        "source=software_proof",
        "not_proven",
        "source_capability=cloud_external_evidence_review_handoff",
        "upstream_capability=cloud_external_evidence_review_decision",
        "delivery_success=false",
        "primary_actions_enabled=false",
        "safe_to_control=false",
        "not true phone/browser proof",
        "no OKR percentage lift",
        "PRRT_kwDOSWB9286CJ3tX",
        "hardware_material_pending",
    ):
        if marker not in safe_copy:
            safe_copy = required_copy
            break

    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    summary.update(
        {
            "configured": True,
            "exists": True,
            "status": status,
            "overall_status": "blocked",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "source_schema_version": summary_fragment.get("source_schema_version")
            or summary_fragment.get("schema_version"),
            "source_schema": (
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SCHEMA
            ),
            "source_summary_schema": (
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA
            ),
            "source_capability": _cloud_guard_safe_text(
                summary_fragment.get("source_capability"),
                "cloud_external_evidence_review_handoff",
            ),
            "upstream_capability": _cloud_guard_safe_text(
                summary_fragment.get("upstream_capability"),
                "cloud_external_evidence_review_decision",
            ),
            "source_handoff_schema": _cloud_guard_safe_text(
                summary_fragment.get("source_handoff_schema"),
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SCHEMA,
            ),
            "source_handoff_summary_schema": _cloud_guard_safe_text(
                summary_fragment.get("source_handoff_summary_schema"),
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
            ),
            "upstream_decision_schema": _cloud_guard_safe_text(
                summary_fragment.get("upstream_decision_schema"),
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA,
            ),
            "upstream_decision_summary_schema": _cloud_guard_safe_text(
                summary_fragment.get("upstream_decision_summary_schema"),
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
            ),
            "source_evidence_boundary": _cloud_guard_safe_text(
                summary_fragment.get("source_evidence_boundary")
                or summary_fragment.get("source_proof_boundary"),
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_GATE,
            ),
            "upstream_evidence_boundary": _cloud_guard_safe_text(
                summary_fragment.get("upstream_evidence_boundary"),
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE,
            ),
            "evidence_boundary": (
                CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_GATE
            ),
            "followup_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _cloud_guard_safe_text(
                    followup_doc.get("reason") or summary_fragment.get("reason"),
                    "cloud external evidence review handoff follow-up remains software_proof only",
                ),
            },
            "source_handoff_status": _cloud_guard_safe_text(
                summary_fragment.get("source_handoff_status"), ""
            ),
            "upstream_review_decision_status": _cloud_guard_safe_text(
                summary_fragment.get("upstream_review_decision_status"), ""
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or response.get("safe_evidence_ref")
                or response.get("evidence_ref")
                or ""
            ),
            "safe_command_id": _cloud_guard_safe_text(
                summary_fragment.get("safe_command_id")
                or summary_fragment.get("command_id")
                or response.get("safe_command_id")
                or response.get("command_id"),
                "",
            ),
            "due_status": _cloud_guard_safe_text(
                summary_fragment.get("due_status"), "blocked"
            ),
            "blocked_reason": _cloud_guard_safe_text(
                summary_fragment.get("blocked_reason"), "hardware_material_pending"
            ),
            "owner_action": _cloud_guard_safe_text(
                summary_fragment.get("owner_action"), ""
            ),
            "support_action": _cloud_guard_safe_text(
                summary_fragment.get("support_action"), ""
            ),
            "reviewer_action": _cloud_guard_safe_text(
                summary_fragment.get("reviewer_action"), ""
            ),
            "ceo_escalation_recommendation": _cloud_guard_safe_text(
                summary_fragment.get("ceo_escalation_recommendation"),
                "blocked_missing_external_evidence",
            ),
            "next_required_evidence": _cloud_external_evidence_safe_list(
                summary_fragment.get("next_required_evidence")
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {"safe_copy": safe_copy, "status": status},
            "pr5_thread_id": _cloud_guard_safe_text(
                summary_fragment.get("pr5_thread_id"), "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_status": _cloud_guard_safe_text(
                summary_fragment.get("pr5_status"), "hardware_material_pending"
            ),
            "pr5_material_state": _cloud_guard_safe_text(
                summary_fragment.get("pr5_material_state"), "hardware_material_pending"
            ),
            "pr5_resolution_claim": _cloud_guard_safe_text(
                summary_fragment.get("pr5_resolution_claim"), "not_pr5_resolution"
            ),
            "phone_browser_proof": "not true phone/browser proof",
            "okr_progress_effect": "no OKR percentage lift",
            "not_proven": (
                _cloud_external_evidence_review_handoff_followup_not_proven(
                    summary_fragment
                )
            ),
            "read_error": "",
        }
    )

    required_safe_metadata = (
        str(summary_fragment.get("schema") or "")
        in (
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
            CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
        ),
        summary["source"] == EVIDENCE_SOURCE_SOFTWARE,
        summary["source_capability"] == "cloud_external_evidence_review_handoff",
        summary["upstream_capability"] == "cloud_external_evidence_review_decision",
        summary["source_handoff_schema"] == CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SCHEMA,
        summary["source_evidence_boundary"] == CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_GATE,
        summary["upstream_decision_schema"] == CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA,
        summary["upstream_evidence_boundary"] == CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE,
        summary["overall_status"] == "blocked",
        summary_fragment.get("delivery_success") is False,
        summary_fragment.get("primary_actions_enabled") is False,
        summary_fragment.get("safe_to_control") is False,
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_status"] == "hardware_material_pending",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_resolution_claim"] == "not_pr5_resolution",
        bool(summary["next_required_evidence"]),
    )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or _cloud_external_evidence_review_decision_has_unsafe_fields(response)
        or _cloud_external_evidence_review_decision_has_unsafe_fields(summary_fragment)
        or _cloud_external_evidence_review_decision_has_unsafe_fields(robot_summary)
        or _cloud_external_evidence_review_decision_has_unsafe_fields(safe_copy)
    )
    if unsafe_payload:
        blocked_copy = _cloud_external_evidence_review_handoff_followup_copy()
        summary.update(
            {
                "status": "followup_rejected_unsafe_material_not_proven",
                "followup_status": {
                    "status": "followup_rejected_unsafe_material_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "cloud external evidence review handoff follow-up summary contains unsafe fields or missing false-state metadata",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "due_status": "blocked",
                "blocked_reason": "unsafe or incomplete follow-up escalation status summary",
                "owner_action": "",
                "support_action": "",
                "reviewer_action": "",
                "ceo_escalation_recommendation": "blocked_missing_external_evidence",
                "next_required_evidence": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
            }
        )
    return summary



__all__ = [
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SUMMARY_SCHEMA",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE",
    "CLOUD_EXTERNAL_EVIDENCE_INTAKE_SCHEMA",
    "CLOUD_EXTERNAL_EVIDENCE_INTAKE_GATE",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_STATUSES",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_NOT_PROVEN",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SCHEMA",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_GATE",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_STATUSES",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_NOT_PROVEN",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SCHEMA",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_GATE",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_STATUSES",
    "CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_NOT_PROVEN",
    "summarize_cloud_external_evidence_review_decision",
    "summarize_cloud_external_evidence_review_handoff",
    "summarize_cloud_external_evidence_review_handoff_followup_escalation_status",
]
