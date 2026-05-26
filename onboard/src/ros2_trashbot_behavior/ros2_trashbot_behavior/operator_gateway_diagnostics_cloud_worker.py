import json
import os
import re


# 本模块只处理 cloud worker 演练类 metadata-only artifact；不访问 ROS、串口、云端或真实 worker。
CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA = "trashbot.cloud_worker_migration_rehearsal.v1"
CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA = (
    "trashbot.cloud_worker_migration_rehearsal_summary.v1"
)
CLOUD_WORKER_MIGRATION_REHEARSAL_GATE = (
    "software_proof_docker_cloud_worker_migration_rehearsal_gate"
)
CLOUD_WORKER_CUTOVER_DRAIN_SCHEMA = "trashbot.cloud_worker_cutover_drain.v1"
CLOUD_WORKER_CUTOVER_DRAIN_SUMMARY_SCHEMA = (
    "trashbot.cloud_worker_cutover_drain_summary.v1"
)
CLOUD_WORKER_CUTOVER_DRAIN_GATE = (
    "software_proof_docker_cloud_worker_cutover_drain_gate"
)
CLOUD_WORKER_MIGRATION_REHEARSAL_REQUIRED_NOT_PROVEN = (
    "real_production_db_queue",
    "real_cloud_worker",
    "real_cloud_migration",
    "external_cloud_probe",
    "real_4g_or_sim",
    "real_hil_pass",
    "delivery_success",
)
CLOUD_WORKER_CUTOVER_DRAIN_REQUIRED_NOT_PROVEN = (
    "real_production_db_queue",
    "real_cloud_worker_cutover",
    "real_cloud_drain",
    "external_cloud_probe",
    "real_4g_or_sim",
    "real_hil_pass",
    "robot_command",
    "ack_completion",
    "cursor_advance_or_persistence",
    "delivery_success",
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
    # worker artifact 可能来自支撑材料，进入手机端前必须屏蔽凭证、URL、串口和本地路径。
    text = str(value or "")
    for pattern, replacement in _TEXT_REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def _safe_artifact_ref(value):
    # artifact_ref 只保留可读引用；本地路径要降级成 basename，避免泄露操作者机器路径。
    text = str(value or "").strip()
    if not text:
        return ""
    redacted = _redact_text(text)
    if "[REDACTED_LOCAL_PATH]" in redacted:
        basename = os.path.basename(os.path.expanduser(text).rstrip(os.sep)) or "artifact"
        return f"local_path_redacted:{basename}"
    return redacted


def _dedupe_not_proven(source, required):
    # not_proven 是前端解释失败原因的顺序，去重时保持 source 在前、固定缺口在后。
    source = source if isinstance(source, dict) else {}
    values = []
    source_values = source.get("not_proven") if isinstance(source.get("not_proven"), list) else []
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _cloud_worker_migration_rehearsal_not_proven(source=None):
    # migration rehearsal 只是本地演练摘要，真实生产 worker 和交付闭环必须继续外部证明。
    return _dedupe_not_proven(source, CLOUD_WORKER_MIGRATION_REHEARSAL_REQUIRED_NOT_PROVEN)


def _cloud_worker_cutover_drain_not_proven(source=None):
    # cutover drain 只证明本地 drain 摘要，不证明真实 cursor、ACK、worker 切换或机器人动作。
    return _dedupe_not_proven(source, CLOUD_WORKER_CUTOVER_DRAIN_REQUIRED_NOT_PROVEN)


def _cloud_worker_migration_rehearsal_status(source, *keys):
    # 只读取状态枚举，不透传完整 artifact，避免 credential、路径或动作字段进入 diagnostics。
    if not isinstance(source, dict):
        return "not_proven"
    for key in keys:
        value = source.get(key)
        if isinstance(value, dict):
            for nested_key in ("status", "state", "overall_status"):
                nested = str(value.get(nested_key) or "").strip()
                if nested:
                    return _redact_text(nested)
        text = str(value or "").strip()
        if text:
            return _redact_text(text)
    return "not_proven"


def _cloud_worker_cutover_drain_status(source, *keys):
    # 这里只提取安全状态词，不把 command、ACK、cursor 或原始 drain artifact 带进 Robot diagnostics。
    if not isinstance(source, dict):
        return "not_proven"
    for key in keys:
        value = source.get(key)
        if isinstance(value, dict):
            for nested_key in ("status", "state", "overall_status", "summary"):
                nested = str(value.get(nested_key) or "").strip()
                if nested:
                    return _redact_text(nested)
        text = str(value or "").strip()
        if text:
            return _redact_text(text)
    return "not_proven"


def _default_cloud_worker_migration_rehearsal_summary(path, status="not_configured", read_error=""):
    # Robot diagnostics 对 cloud worker rehearsal 只做 metadata-only 展示，默认禁止动作和游标副作用。
    return {
        "schema": CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": CLOUD_WORKER_MIGRATION_REHEARSAL_GATE,
        "status": status,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "artifact_ref": _safe_artifact_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "migration_rehearsal_status": "not_proven",
        "worker_rehearsal_status": "not_proven",
        "retry_hint": "attach_cloud_worker_migration_rehearsal_artifact",
        "not_proven": _cloud_worker_migration_rehearsal_not_proven(),
        "read_error": _redact_text(read_error),
        "safe_summary": "Cloud worker migration rehearsal is not configured; metadata-only diagnostics keep robot actions disabled.",
        "safe_phone_copy": "Cloud worker migration rehearsal is not configured; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
        "production_ready": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _default_cloud_worker_cutover_drain_summary(path, status="not_configured", read_error=""):
    # Robot diagnostics 对 cutover drain 只读消费；默认值必须先阻断动作、ACK 和 cursor 推进。
    return {
        "schema": CLOUD_WORKER_CUTOVER_DRAIN_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": CLOUD_WORKER_CUTOVER_DRAIN_GATE,
        "status": status,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "artifact_ref": _safe_artifact_ref(path),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "drain_status": "not_proven",
        "cursor_summary": "not_proven",
        "terminal_ack_summary": "not_proven",
        "retry_hint": "attach_cloud_worker_cutover_drain_artifact",
        "not_proven": _cloud_worker_cutover_drain_not_proven(),
        "read_error": _redact_text(read_error),
        "safe_summary": "Cloud worker cutover drain is not configured; metadata-only diagnostics keep robot actions disabled.",
        "safe_phone_copy": "Cloud worker cutover drain is not configured; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
        "production_ready": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def summarize_cloud_worker_migration_rehearsal(path):
    """构建只读、metadata-only 的 cloud worker migration rehearsal summary。"""
    artifact_path = os.path.expanduser(str(path or ""))
    summary = _default_cloud_worker_migration_rehearsal_summary(
        artifact_path,
        read_error="cloud worker migration rehearsal artifact is not configured",
    )
    if not artifact_path:
        return summary
    if not os.path.exists(artifact_path):
        summary.update(
            {
                "status": "missing",
                "read_error": "cloud worker migration rehearsal artifact not found",
                "safe_summary": "Cloud worker migration rehearsal artifact is missing; robot command safety remains fail-closed.",
                "safe_phone_copy": "Cloud worker migration rehearsal artifact is missing; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
                "retry_hint": "regenerate_cloud_worker_migration_rehearsal_artifact",
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
                "status": "read_error",
                "read_error": _redact_text(
                    f"failed reading cloud worker migration rehearsal artifact: {exc}"
                ),
                "safe_summary": "Cloud worker migration rehearsal artifact could not be read; robot actions remain disabled.",
                "safe_phone_copy": "Cloud worker migration rehearsal artifact could not be read; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
                "retry_hint": "fix_cloud_worker_migration_rehearsal_json",
            }
        )
        return summary
    if not isinstance(artifact, dict):
        summary.update(
            {
                "status": "read_error",
                "read_error": "cloud worker migration rehearsal artifact JSON must be an object",
                "safe_summary": "Cloud worker migration rehearsal artifact shape is invalid; robot actions remain disabled.",
                "safe_phone_copy": "Cloud worker migration rehearsal artifact shape is invalid; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
                "retry_hint": "regenerate_cloud_worker_migration_rehearsal_artifact",
            }
        )
        return summary

    source_schema = str(artifact.get("schema") or "")
    source_boundary = str(artifact.get("evidence_boundary") or artifact.get("boundary") or "")
    summary.update(
        {
            "source_schema": _redact_text(source_schema),
            "source_schema_version": artifact.get("schema_version"),
            "source_evidence_boundary": _redact_text(source_boundary),
            "not_proven": _cloud_worker_migration_rehearsal_not_proven(artifact),
            "read_error": "",
        }
    )
    if (
        source_schema not in (CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA, CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA)
        or source_boundary != CLOUD_WORKER_MIGRATION_REHEARSAL_GATE
    ):
        summary.update(
            {
                "status": "unsupported_schema",
                "read_error": "cloud worker migration rehearsal schema or evidence boundary is unsupported",
                "safe_summary": "Cloud worker migration rehearsal source is unsupported; robot command safety remains fail-closed.",
                "safe_phone_copy": "Cloud worker migration rehearsal source is unsupported; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
                "retry_hint": "regenerate_with_supported_cloud_worker_migration_rehearsal_schema",
            }
        )
        return summary

    encoded_artifact = json.dumps(artifact, ensure_ascii=False)
    encoded_artifact_lower = encoded_artifact.lower()
    unsafe_patterns = (
        "authorization",
        "bearer ",
        "credential_url",
        "db_url",
        "database_url",
        "queue_url",
        "postgres://",
        "redis://",
        "/cmd_vel",
        "/dev/tty",
        "wave rover",
    )
    success_patterns = (
        "delivery success",
        "delivery_success\": true",
        "production_ready\": true",
        "primary_actions_enabled\": true",
    )
    if any(pattern in encoded_artifact_lower for pattern in unsafe_patterns + success_patterns):
        summary.update(
            {
                "status": "unsafe_copy",
                "read_error": "cloud worker migration rehearsal contains unsafe copy, credentials, success wording, or enabled action flags",
                "safe_summary": "Cloud worker migration rehearsal source was rejected by Robot diagnostics redaction checks.",
                "safe_phone_copy": "Cloud worker migration rehearsal source was rejected; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
                "retry_hint": "regenerate_redacted_metadata_only_rehearsal_artifact",
            }
        )
        return summary

    status = _cloud_worker_migration_rehearsal_status(
        artifact,
        "status",
        "overall_status",
        "rehearsal_status",
        "migration_rehearsal",
    )
    summary.update(
        {
            "status": status or "not_proven",
            "migration_rehearsal_status": _cloud_worker_migration_rehearsal_status(
                artifact,
                "migration_rehearsal_status",
                "migration_rehearsal",
                "migration",
            ),
            "worker_rehearsal_status": _cloud_worker_migration_rehearsal_status(
                artifact,
                "worker_rehearsal_status",
                "worker_rehearsal",
                "worker",
            ),
            "retry_hint": _redact_text(
                artifact.get("retry_hint") or "keep_metadata_only_until_external_cloud_worker_evidence_exists"
            ),
            "safe_summary": "Cloud worker migration rehearsal is metadata-only software proof; it cannot create robot commands, ACKs, cursor updates, or delivery success.",
            "safe_phone_copy": "Cloud worker migration rehearsal is metadata-only; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
            "production_ready": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    return summary


def summarize_cloud_worker_cutover_drain(path):
    """构建只读、metadata-only 的 cloud worker cutover drain summary。"""
    artifact_path = os.path.expanduser(str(path or ""))
    summary = _default_cloud_worker_cutover_drain_summary(
        artifact_path,
        read_error="cloud worker cutover drain artifact is not configured",
    )
    if not artifact_path:
        return summary
    if not os.path.exists(artifact_path):
        summary.update(
            {
                "status": "missing",
                "read_error": "cloud worker cutover drain artifact not found",
                "safe_summary": "Cloud worker cutover drain artifact is missing; robot command safety remains fail-closed.",
                "safe_phone_copy": "Cloud worker cutover drain artifact is missing; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
                "retry_hint": "regenerate_cloud_worker_cutover_drain_artifact",
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
                "status": "read_error",
                "read_error": _redact_text(f"failed reading cloud worker cutover drain artifact: {exc}"),
                "safe_summary": "Cloud worker cutover drain artifact could not be read; robot actions remain disabled.",
                "safe_phone_copy": "Cloud worker cutover drain artifact could not be read; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
                "retry_hint": "fix_cloud_worker_cutover_drain_json",
            }
        )
        return summary
    if not isinstance(artifact, dict):
        summary.update(
            {
                "status": "read_error",
                "read_error": "cloud worker cutover drain artifact JSON must be an object",
                "safe_summary": "Cloud worker cutover drain artifact shape is invalid; robot actions remain disabled.",
                "safe_phone_copy": "Cloud worker cutover drain artifact shape is invalid; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
                "retry_hint": "regenerate_cloud_worker_cutover_drain_artifact",
            }
        )
        return summary

    source_schema = str(artifact.get("schema") or "")
    source_boundary = str(artifact.get("evidence_boundary") or artifact.get("boundary") or "")
    summary.update(
        {
            "source_schema": _redact_text(source_schema),
            "source_schema_version": artifact.get("schema_version"),
            "source_evidence_boundary": _redact_text(source_boundary),
            "not_proven": _cloud_worker_cutover_drain_not_proven(artifact),
            "read_error": "",
        }
    )
    if source_schema not in (CLOUD_WORKER_CUTOVER_DRAIN_SCHEMA, CLOUD_WORKER_CUTOVER_DRAIN_SUMMARY_SCHEMA):
        summary.update(
            {
                "status": "unsupported_schema",
                "read_error": "cloud worker cutover drain schema is unsupported",
                "safe_summary": "Cloud worker cutover drain source schema is unsupported; robot command safety remains fail-closed.",
                "safe_phone_copy": "Cloud worker cutover drain source is unsupported; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
                "retry_hint": "regenerate_with_supported_cloud_worker_cutover_drain_schema",
            }
        )
        return summary
    if source_boundary != CLOUD_WORKER_CUTOVER_DRAIN_GATE:
        summary.update(
            {
                "status": "unsupported_boundary",
                "read_error": "cloud worker cutover drain evidence boundary is unsupported",
                "safe_summary": "Cloud worker cutover drain source boundary is unsupported; robot command safety remains fail-closed.",
                "safe_phone_copy": "Cloud worker cutover drain boundary is unsupported; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
                "retry_hint": "regenerate_with_supported_cloud_worker_cutover_drain_boundary",
            }
        )
        return summary

    encoded_artifact = json.dumps(artifact, ensure_ascii=False)
    encoded_artifact_lower = encoded_artifact.lower()
    unsafe_patterns = (
        "authorization",
        "bearer ",
        "credential_url",
        "db_url",
        "database_url",
        "queue_url",
        "postgres://",
        "redis://",
        "/cmd_vel",
        "/dev/tty",
        "wave rover",
    )
    success_patterns = (
        "delivery success",
        "delivery_success\": true",
        "production_ready\": true",
        "primary_actions_enabled\": true",
        "ack_semantics\": \"delivery_success",
    )
    if any(pattern in encoded_artifact_lower for pattern in unsafe_patterns + success_patterns):
        summary.update(
            {
                "status": "unsafe_copy",
                "read_error": "cloud worker cutover drain contains unsafe copy, credentials, success wording, or enabled action flags",
                "safe_summary": "Cloud worker cutover drain source was rejected by Robot diagnostics redaction checks.",
                "safe_phone_copy": "Cloud worker cutover drain source was rejected; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
                "retry_hint": "regenerate_redacted_metadata_only_cutover_drain_artifact",
            }
        )
        return summary

    summary.update(
        {
            "status": _cloud_worker_cutover_drain_status(
                artifact,
                "status",
                "overall_status",
                "drain_status",
                "cutover_drain",
            ),
            "drain_status": _cloud_worker_cutover_drain_status(
                artifact,
                "drain_status",
                "cutover_drain",
                "drain",
            ),
            "cursor_summary": _cloud_worker_cutover_drain_status(
                artifact,
                "cursor_summary",
                "cursor",
                "cursor_status",
            ),
            "terminal_ack_summary": _cloud_worker_cutover_drain_status(
                artifact,
                "terminal_ack_summary",
                "terminal_ack",
                "ack_summary",
            ),
            "retry_hint": _redact_text(
                artifact.get("retry_hint") or "keep_metadata_only_until_external_cutover_drain_evidence_exists"
            ),
            "safe_summary": "Cloud worker cutover drain is metadata-only software proof; it cannot create robot commands, ACKs, cursor updates, or delivery success.",
            "safe_phone_copy": "Cloud worker cutover drain is metadata-only; production_ready=false, delivery_success=false, primary_actions_enabled=false.",
            "production_ready": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    return summary
