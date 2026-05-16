import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import pathlib
import socket
import sqlite3
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse
import urllib.error
import urllib.request


PROTOCOL_VERSION = "trashbot.remote.v1"
STORE_SCHEMA = "trashbot.remote_cloud_relay_store.v1"
COMMAND_TYPES = {"collect", "confirm_dropoff", "cancel"}
TERMINAL_ACK_STATES = {"acked", "failed", "ignored"}
STATUS_STALE_AFTER_SEC = 90.0
PREFLIGHT_EVIDENCE_BOUNDARY = "software_proof_docker_preflight_gate"
SQLITE_EVIDENCE_BOUNDARY = "software_proof_docker_sqlite_state_store"
BACKUP_RESTORE_EVIDENCE_BOUNDARY = "software_proof_docker_backup_restore_drill"
NETWORK_RECOVERY_EVIDENCE_BOUNDARY = "software_proof_docker_network_recovery_drill"
OSS_CDN_MANIFEST_EVIDENCE_BOUNDARY = "software_proof_docker_oss_cdn_manifest"
OSS_CDN_PHONE_MANIFEST_EVIDENCE_BOUNDARY = "software_proof_docker_phone_manifest_consumption"
NETWORK_RECOVERY_PHONE_EVIDENCE_BOUNDARY = "software_proof_docker_network_recovery_phone_consumption"
CREDENTIAL_ROTATION_EVIDENCE_BOUNDARY = "software_proof_docker_credential_rotation_gate"
CREDENTIAL_ROTATION_PHONE_EVIDENCE_BOUNDARY = "software_proof_docker_credential_rotation_phone_consumption"
PROVISIONING_AUDIT_EVIDENCE_BOUNDARY = "software_proof_docker_provisioning_audit_gate"
PROVISIONING_AUDIT_PHONE_EVIDENCE_BOUNDARY = "software_proof_docker_provisioning_audit_phone_consumption"
PRODUCTION_STORE_QUEUE_EVIDENCE_BOUNDARY = "software_proof_docker_production_store_queue_gate"
PRODUCTION_STORE_QUEUE_PHONE_EVIDENCE_BOUNDARY = "software_proof_docker_production_store_queue_phone_consumption"
QUEUE_ORDERING_DRILL_EVIDENCE_BOUNDARY = "software_proof_docker_queue_ordering_drill"
QUEUE_ORDERING_DRILL_PHONE_EVIDENCE_BOUNDARY = "software_proof_docker_queue_ordering_phone_consumption"
TRANSACTION_ISOLATION_EVIDENCE_BOUNDARY = "software_proof_docker_transaction_isolation_gate"
TRANSACTION_ISOLATION_PHONE_EVIDENCE_BOUNDARY = "software_proof_docker_transaction_isolation_phone_consumption"
PRODUCTION_RECOVERY_EVIDENCE_BOUNDARY = "software_proof_docker_production_recovery_gate"
PRODUCTION_RECOVERY_PHONE_EVIDENCE_BOUNDARY = "software_proof_docker_production_recovery_phone_consumption"
CLOUD_DEPLOYMENT_READINESS_EVIDENCE_BOUNDARY = "software_proof_docker_cloud_deployment_readiness_gate"
CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY = "software_proof_docker_cloud_external_probe_bundle_gate"
CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY = "software_proof_docker_cloud_public_ingress_tls_gate"
CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY = "software_proof_docker_cloud_db_queue_config_gate"
CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY = "software_proof_docker_cloud_db_queue_external_probe_gate"
OSS_CDN_LIVE_PROBE_EVIDENCE_BOUNDARY = "software_proof_docker_oss_cdn_live_probe_gate"
EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY = "software_proof_docker_external_evidence_intake_gate"
CLOUD_WORKER_MIGRATION_REHEARSAL_EVIDENCE_BOUNDARY = (
    "software_proof_docker_cloud_worker_migration_rehearsal_gate"
)
CLOUD_HOSTED_MOBILE_WEB_EVIDENCE_BOUNDARY = "software_proof_docker_cloud_hosted_mobile_web_gate"
OSS_CDN_PHONE_MANIFEST_STALE_AFTER_SEC = 24 * 60 * 60
NETWORK_RECOVERY_ARTIFACT_STALE_AFTER_SEC = 24 * 60 * 60
CREDENTIAL_ROTATION_ARTIFACT_STALE_AFTER_SEC = 24 * 60 * 60
PROVISIONING_AUDIT_ARTIFACT_STALE_AFTER_SEC = 24 * 60 * 60
PRODUCTION_STORE_QUEUE_ARTIFACT_STALE_AFTER_SEC = 24 * 60 * 60
QUEUE_ORDERING_DRILL_ARTIFACT_STALE_AFTER_SEC = 24 * 60 * 60
TRANSACTION_ISOLATION_ARTIFACT_STALE_AFTER_SEC = 24 * 60 * 60
PRODUCTION_RECOVERY_ARTIFACT_STALE_AFTER_SEC = 24 * 60 * 60
CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT_STALE_AFTER_SEC = 24 * 60 * 60
DEPLOY_EVIDENCE_BOUNDARY = "software_proof_docker_deploy"
BACKUP_ARTIFACT_SCHEMA = "trashbot.remote_cloud_relay_backup.v1"
BACKUP_ARTIFACT_VERSION = 1
NETWORK_RECOVERY_SCHEMA = "trashbot.network_recovery_drill"
NETWORK_RECOVERY_SCHEMA_VERSION = 1
OSS_CDN_MANIFEST_SCHEMA = "trashbot.oss_cdn_manifest"
OSS_CDN_MANIFEST_VERSION = 1
CREDENTIAL_ROTATION_SCHEMA = "trashbot.credential_rotation_gate"
CREDENTIAL_ROTATION_SCHEMA_VERSION = 1
PROVISIONING_AUDIT_SCHEMA = "trashbot.provisioning_audit_gate"
PROVISIONING_AUDIT_SCHEMA_VERSION = 1
PRODUCTION_STORE_QUEUE_SCHEMA = "trashbot.production_store_queue_gate"
PRODUCTION_STORE_QUEUE_SCHEMA_VERSION = 1
QUEUE_ORDERING_DRILL_SCHEMA = "trashbot.queue_ordering_drill"
QUEUE_ORDERING_DRILL_SCHEMA_VERSION = 1
TRANSACTION_ISOLATION_SCHEMA = "trashbot.transaction_isolation_drill"
TRANSACTION_ISOLATION_SCHEMA_VERSION = 1
PRODUCTION_RECOVERY_SCHEMA = "trashbot.production_recovery_gate"
PRODUCTION_RECOVERY_SCHEMA_VERSION = 1
CLOUD_DEPLOYMENT_READINESS_SCHEMA = "trashbot.cloud_deployment_readiness"
CLOUD_DEPLOYMENT_READINESS_SCHEMA_VERSION = 1
CLOUD_EXTERNAL_PROBE_SCHEMA = "trashbot.cloud_external_probe_bundle"
CLOUD_EXTERNAL_PROBE_SCHEMA_VERSION = 1
CLOUD_PUBLIC_INGRESS_TLS_SCHEMA = "trashbot.cloud_public_ingress_tls_gate"
CLOUD_PUBLIC_INGRESS_TLS_SCHEMA_VERSION = 1
CLOUD_DB_QUEUE_CONFIG_SCHEMA = "trashbot.cloud_db_queue_config_gate"
CLOUD_DB_QUEUE_CONFIG_SCHEMA_VERSION = 1
CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA = "trashbot.cloud_db_queue_external_probe_bundle"
CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA_VERSION = 1
OSS_CDN_LIVE_PROBE_SCHEMA = "trashbot.oss_cdn_live_probe"
OSS_CDN_LIVE_PROBE_SCHEMA_VERSION = 1
EXTERNAL_EVIDENCE_INTAKE_SCHEMA = "trashbot.external_evidence_intake"
EXTERNAL_EVIDENCE_INTAKE_SCHEMA_VERSION = 1
CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA = "trashbot.cloud_worker_migration_rehearsal.v1"
CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA_VERSION = 1
CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA = "trashbot.cloud_worker_migration_rehearsal_summary.v1"
CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA_VERSION = 1
CLOUD_HOSTED_MOBILE_WEB_GATE_SCHEMA = "trashbot.cloud_hosted_mobile_web_gate"
CLOUD_HOSTED_MOBILE_WEB_GATE_SCHEMA_VERSION = 1
OSS_CDN_BUCKET = "bytegallop"
OSS_CDN_REGION = "oss-cn-hangzhou"
OSS_CDN_PREFIX_ROOT = "rober/"
OSS_CDN_BASE_URL = "https://cdn.bytegallop.com/rober/"
OSS_CDN_NOT_PROVEN = [
    "real_oss_upload",
    "sts_issuance",
    "cdn_origin_fetch",
    "lifecycle_policy",
    "production_account",
    "real_cloud",
    "real_4g_sim",
    "https_tls_public_ingress",
    "production_db_or_queue",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
]
CREDENTIAL_ROTATION_NOT_PROVEN = [
    "production_credential_rotation",
    "sts_issuance",
    "real_oss_upload",
    "cdn_origin_fetch",
    "production_account",
    "account_tier_enforcement",
    "robot_provisioning",
    "audit_log_sink",
    "real_cloud",
    "real_4g_sim",
    "https_tls_public_ingress",
    "production_db_or_queue",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
PROVISIONING_AUDIT_NOT_PROVEN = [
    "production_robot_provisioning",
    "real_sts_issuance",
    "real_audit_log_sink",
    "real_oss_upload",
    "cdn_origin_fetch",
    "production_account",
    "restricted_delivery_channel",
    "real_cloud",
    "real_4g_sim",
    "https_tls_public_ingress",
    "production_db_or_queue",
    "multi_instance_consistency",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
PRODUCTION_STORE_QUEUE_NOT_PROVEN = [
    "production_db_or_queue",
    "multi_instance_consistency",
    "production_queue_ordering",
    "production_transaction_isolation",
    "production_backup_policy",
    "real_disaster_recovery",
    "real_cloud",
    "real_4g_sim",
    "https_tls_public_ingress",
    "production_account",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
QUEUE_ORDERING_DRILL_NOT_PROVEN = [
    "production_queue_ordering",
    "production_db_or_queue",
    "multi_instance_consistency",
    "production_transaction_isolation",
    "real_cloud",
    "real_4g_sim",
    "https_tls_public_ingress",
    "production_account",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
TRANSACTION_ISOLATION_NOT_PROVEN = [
    "production_transaction_isolation",
    "production_db_or_queue",
    "multi_instance_consistency",
    "production_queue_ordering",
    "real_cloud",
    "real_4g_sim",
    "https_tls_public_ingress",
    "production_account",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
PRODUCTION_RECOVERY_NOT_PROVEN = [
    "production_db_or_queue",
    "multi_instance_consistency",
    "production_backup_policy",
    "real_disaster_recovery",
    "production_restore_runbook",
    "production_rpo_rto_commitment",
    "real_cloud",
    "real_4g_sim",
    "real_oss_upload",
    "cdn_origin_fetch",
    "https_tls_public_ingress",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
CLOUD_DEPLOYMENT_READINESS_NOT_PROVEN = [
    "real_cloud",
    "real_https_tls",
    "public_ingress_external_probe",
    "real_4g_sim",
    "real_oss_upload",
    "cdn_origin_fetch",
    "sts_issuance",
    "production_db_or_queue",
    "multi_instance_consistency",
    "production_queue_ordering",
    "production_backup_policy",
    "real_disaster_recovery",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
CLOUD_EXTERNAL_PROBE_NOT_PROVEN = [
    "real_cloud",
    "real_https_tls",
    "public_ingress_external_probe",
    "real_4g_sim",
    "real_oss_upload",
    "cdn_origin_fetch",
    "sts_issuance",
    "production_db_or_queue",
    "multi_instance_consistency",
    "production_queue_ordering",
    "production_backup_policy",
    "real_disaster_recovery",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
CLOUD_PUBLIC_INGRESS_TLS_NOT_PROVEN = [
    "real_cloud",
    "real_https_tls",
    "public_ingress_external_probe",
    "dns_resolution",
    "reverse_proxy_live_routing",
    "firewall_public_ingress",
    "real_4g_sim",
    "real_oss_upload",
    "cdn_origin_fetch",
    "production_db_or_queue",
    "multi_instance_consistency",
    "production_backup_policy",
    "real_disaster_recovery",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
CLOUD_DB_QUEUE_CONFIG_NOT_PROVEN = [
    "production_db_or_queue",
    "production_db_connection",
    "production_queue_connection",
    "multi_instance_consistency",
    "production_queue_ordering",
    "production_transaction_isolation",
    "production_backup_policy",
    "real_disaster_recovery",
    "real_cloud",
    "real_4g_sim",
    "https_tls_public_ingress",
    "real_oss_upload",
    "cdn_origin_fetch",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
CLOUD_DB_QUEUE_EXTERNAL_PROBE_NOT_PROVEN = [
    "real_production_db_connectivity",
    "real_production_queue_connectivity",
    "production_migration_run",
    "production_queue_worker_run",
    "multi_instance_consistency",
    "production_queue_ordering",
    "production_transaction_isolation",
    "production_backup_policy",
    "real_disaster_recovery",
    "real_cloud",
    "real_4g_sim",
    "https_tls_public_ingress",
    "real_oss_upload",
    "cdn_origin_fetch",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
OSS_CDN_LIVE_PROBE_NOT_PROVEN = [
    "real_oss_upload",
    "sts_issuance",
    "cdn_origin_fetch",
    "lifecycle_policy",
    "production_account",
    "real_cloud",
    "real_4g_sim",
    "https_tls_public_ingress",
    "production_db_or_queue",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
EXTERNAL_EVIDENCE_INTAKE_NOT_PROVEN = [
    "real_cloud",
    "real_https_tls",
    "public_ingress_external_probe",
    "real_oss_upload",
    "cdn_origin_fetch",
    "sts_issuance",
    "production_db_or_queue",
    "real_production_db_connectivity",
    "real_production_queue_connectivity",
    "production_queue_ordering",
    "production_transaction_isolation",
    "real_4g_sim",
    "sim_card_activation",
    "carrier_network_attachment",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]
CLOUD_WORKER_MIGRATION_REHEARSAL_NOT_PROVEN = [
    "real_production_db_connectivity",
    "real_production_queue_connectivity",
    "production_migration_run",
    "production_queue_worker_run",
    "production_db_or_queue",
    "multi_instance_consistency",
    "production_queue_ordering",
    "production_transaction_isolation",
    "production_backup_policy",
    "real_disaster_recovery",
    "real_cloud",
    "real_4g_sim",
    "https_tls_public_ingress",
    "real_oss_upload",
    "cdn_origin_fetch",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]

# 这些文案直接给手机 UI 使用，不能夹带 HTTP 栈、ROS 话题、串口或凭证细节。
PHONE_COPY = {
    "auth_failed": "手机登录已失效，请重新登录或检查访问凭证。",
    "bad_request": "请求内容有误，请返回上一步后重试。",
    "not_ready": "云端中转服务尚未就绪，请等待服务恢复后重试。",
    "not_found": "没有找到对应记录，请稍后刷新或重新发起。",
    "status_missing": "小车尚未上报状态，请等待小车联网后再试。",
    "status_stale": "小车状态已过期，请等待小车重新联网或检查网络。",
    "malformed_json": "请求格式异常，请检查客户端版本后重试。",
    "preflight_blocked": "云端上线前检查未通过，请先补齐生产入口、凭证和存储配置。",
    "backup_restore_blocked": "云端状态备份恢复演练未通过，请重新生成备份后再恢复。",
    "oss_cdn_manifest_blocked": "OSS/CDN 诊断引用清单未通过校验，请重新生成后再试。",
    "network_recovery_blocked": "网络恢复演练未通过，请重新运行恢复演练后再试。",
    "credential_rotation_blocked": "凭证轮换软件证明未通过校验，请重新生成后再试。",
    "provisioning_audit_blocked": "生产 provisioning / STS / audit 软件证明未通过校验，请重新生成后再试。",
    "production_store_queue_blocked": "生产 DB/queue 软件证明未通过校验，请重新生成后再试。",
    "queue_ordering_drill_blocked": "队列顺序演练软件证明未通过校验，请重新生成后再试。",
    "transaction_isolation_blocked": "事务隔离演练软件证明未通过校验，请重新生成后再试。",
    "production_recovery_blocked": "生产备份/灾备恢复 gate 未通过校验，请重新生成后再试。",
    "cloud_deployment_readiness_blocked": "云部署就绪检查仍未通过，请补齐公网、TLS、4G 和生产存储证据。",
    "cloud_external_probe_blocked": "云端外部探测 bundle 未通过校验，请重新生成后再试。",
    "cloud_public_ingress_tls_blocked": "公网入口/TLS 配置 gate 仍未通过外部实证，请补齐 DNS、反向代理和防火墙证据。",
    "cloud_db_queue_config_blocked": "生产 DB/queue 配置 gate 仍未通过外部实证，请补齐真实数据库和队列证据。",
    "cloud_db_queue_external_probe_blocked": "生产 DB/queue 外部探测 bundle 仍未通过实证，请补齐真实数据库和队列探测证据。",
    "oss_cdn_live_probe_blocked": "OSS/CDN live probe gate 未通过校验，请重新生成后再试。",
    "external_evidence_intake_blocked": "外部证据 intake artifact 未通过校验，请重新生成脱敏材料后再试。",
    "cloud_worker_migration_rehearsal_blocked": "Cloud worker/migration 本地演练未通过，请重新生成 artifact 后再试。",
}

# proof 文件会被用作证据，默认删除凭证、低层机器人控制和硬件配置字段。
SENSITIVE_KEYS = {
    "token",
    "bearer",
    "authorization",
    "auth",
    "secret",
    "password",
    "url",
    "cloud_url",
    "serial",
    "serial_port",
    "baudrate",
    "wave_rover",
    "hardware",
    "ros_topic",
    "topic",
    "cmd_vel",
}
PHONE_SAFE_KEY_EXCEPTIONS = {
    "bearer_rotation_status",
}

# cloud-relay 只托管 dependency-free PWA 壳；控制面路径必须在 handler 中优先返回。
MOBILE_WEB_STATIC_FILES = {
    "index.html",
    "app.js",
    "styles.css",
    "manifest.webmanifest",
    "service-worker.js",
    "offline.html",
    "icon-192.svg",
    "icon-512.svg",
}
MOBILE_WEB_CONTENT_TYPES = {
    "html": "text/html; charset=utf-8",
    "js": "application/javascript; charset=utf-8",
    "css": "text/css; charset=utf-8",
    "webmanifest": "application/manifest+json; charset=utf-8",
    "svg": "image/svg+xml; charset=utf-8",
}
CONTROL_PATH_PREFIXES = ("/api/", "/robots/")
CONTROL_PATHS = {"/api", "/robots", "/healthz", "/readyz", "/preflightz"}
CLOUD_HOSTED_MOBILE_WEB_NOT_PROVEN = [
    "real_public_cloud",
    "real_https_tls",
    "real_4g_sim",
    "real_phone_device_browser",
    "production_app",
    "production_db_or_queue",
    "nav2_or_fixed_route_delivery",
    "wave_rover_or_hil",
    "delivery_success",
]

# 对字符串也做保守脱敏，避免敏感内容藏在 message 或 diagnostics 里。
SENSITIVE_TEXT = (
    "authorization",
    "bearer ",
    "token",
    "secret",
    "password",
    "oss secret",
    "oss_access_key",
    "access_key",
    "access key",
    "secret_key",
    "secret key",
    "ak/sk",
    "ak sk",
    "root password",
    "://",
    "raw state path",
    "state path",
    "/dev/",
    "/cmd_vel",
    "cmd_vel",
    "serial_port",
    "ttyusb",
    "ttyacm",
    "/odom",
    "/imu",
    "/battery",
    "baudrate",
    "wave rover",
    "ros topic",
    "/trashbot/",
)


def _now():
    return time.time()


def _safe_text(value):
    text = str(value)
    lowered = text.lower()
    if any(marker in lowered for marker in SENSITIVE_TEXT):
        return "[redacted]"
    return text


def safe_value(value):
    """递归脱敏后再返回给手机或写入 state file。"""
    if isinstance(value, dict):
        safe = {}
        for key, item in value.items():
            key_text = str(key)
            key_lc = key_text.lower()
            if key_lc not in PHONE_SAFE_KEY_EXCEPTIONS and any(marker in key_lc for marker in SENSITIVE_KEYS):
                continue
            safe[key_text] = safe_value(item)
        return safe
    if isinstance(value, list):
        return [safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _safe_text(value)


def _canonical_json_bytes(payload):
    # checksum 必须跨 Python/Docker 环境稳定，排序和紧凑分隔符避免空白差异。
    return json.dumps(
        safe_value(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _raw_canonical_json_bytes(payload):
    # manifest checksum 必须覆盖 CDN URL 等公开引用字段，不能复用会删除 url key 的通用脱敏。
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_checksum(payload):
    # artifact 校验只覆盖业务数据和 metadata，不覆盖 checksum 字段本身。
    return "sha256:" + hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _raw_sha256_checksum(payload):
    # OSS/CDN manifest 本身就是公开对象引用 contract，checksum 应覆盖完整 contract 字段。
    return "sha256:" + hashlib.sha256(_raw_canonical_json_bytes(payload)).hexdigest()


def _safe_error_reason(exc):
    # CLI 失败原因可以给手机或 operator 看，不能包含路径、token、串口或 traceback。
    return _safe_text(str(exc) or "backup restore drill failed")


def _utc_iso(timestamp):
    # 手机端只需要稳定时间文本；统一 UTC 可避免本地/Docker 时区差异影响测试。
    return datetime.fromtimestamp(float(timestamp), timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
    )


def phone_error(code, message="", *, status=None, details=None):
    # 错误 shape 固定，手机端只看 code/safe_phone_copy 就能给恢复建议。
    payload = {
        "ok": False,
        "error": {
            "code": str(code),
            "message": _safe_text(message or PHONE_COPY.get(code, "请求失败，请稍后重试。")),
            "safe_phone_copy": PHONE_COPY.get(code, "请求失败，请稍后重试。"),
            "details": safe_value(details if isinstance(details, dict) else {}),
        },
    }
    if isinstance(status, dict):
        payload["status"] = safe_value(status)
    return payload


def _phone_safe_failure_ready():
    # readiness 自检用固定敏感样本，避免以后改脱敏规则时把底层细节暴露给手机。
    sample = phone_error(
        "bad_request",
        "Authorization Bearer token AK/SK OSS_ACCESS_KEY_SECRET raw state path /cmd_vel ttyUSB0 baudrate https://secret.invalid",
        details={
            "authorization": "Bearer hidden",
            "serial_port": "/dev/ttyUSB0",
            "access_key_secret": "should-not-render",
            "safe": "visible",
        },
    )
    encoded = json.dumps(sample, ensure_ascii=False)
    forbidden = ("Bearer", "token", "AK/SK", "OSS_ACCESS_KEY", "/cmd_vel", "ttyUSB", "baudrate", "https://secret")
    return not any(marker in encoded for marker in forbidden)


def _env_value(env, key, default=""):
    return str(env.get(key, default) or "").strip()


def _is_placeholder(value):
    # 占位符可能来自 .env.example、compose 默认值或本地 smoke；统一按未生产化处理。
    text = str(value or "").strip().lower()
    if not text:
        return True
    markers = (
        "replace",
        "placeholder",
        "example",
        "changeme",
        "change-me",
        "dev-",
        "local-",
        "dummy",
        "<",
        ">",
        "future_",
    )
    return any(marker in text for marker in markers)


def _status_rank(status):
    # overall 取最严重状态，避免 warning/blocked 被后续 pass 覆盖。
    return {"pass": 0, "warning": 1, "blocked": 2}.get(status, 2)


def _check(name, status, code, safe_summary, retry_hint, details=None):
    # 每条检查都保持 phone-safe，机器可读字段和用户提示分离。
    return {
        "name": name,
        "status": status,
        "code": code,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "details": safe_value(details if isinstance(details, dict) else {}),
    }


def _safe_scheme(value):
    parsed = urlparse(str(value or ""))
    return parsed.scheme.lower() if parsed.scheme else "missing"


def _safe_enum(value, allowed, default="invalid_or_unsupported"):
    # preflight 的 details 面向手机和运维，枚举值只能来自白名单，不能回显任意 env 字符串。
    text = str(value or "").strip()
    return text if text in allowed else default


def _manifest_prefix(robot_id, date_text, task_id):
    # 前缀是手机诊断引用的稳定命名空间；真实上传接入前先锁定可校验规则。
    return f"{OSS_CDN_PREFIX_ROOT}{robot_id}/{date_text}/{task_id}/"


def _manifest_cdn_url(object_key):
    # CDN 公开只读入口映射到去掉 rober/ 根前缀后的对象相对路径。
    if not str(object_key or "").startswith(OSS_CDN_PREFIX_ROOT):
        raise ValueError("object_key must start with rober/")
    relative_key = str(object_key)[len(OSS_CDN_PREFIX_ROOT):]
    return OSS_CDN_BASE_URL + relative_key


def _manifest_forbidden_markers(payload):
    # manifest 允许公开 CDN URL，但仍禁止凭证、原始硬件/ROS 控制和本机路径泄露。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    encoded = encoded.replace(OSS_CDN_BASE_URL.lower(), "")
    markers = (
        "authorization",
        "bearer",
        "token",
        "secret",
        "access_key",
        "ak/sk",
        "root password",
        "state path",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
    )
    return [marker for marker in markers if marker in encoded]


def _load_json_file(path, artifact_name):
    try:
        with open(os.path.expanduser(str(path or "")), "r", encoding="utf-8") as artifact_file:
            payload = json.load(artifact_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{artifact_name} could not be read") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{artifact_name} must be an object")
    return payload


def _find_closed_local_port():
    # 用 OS 分配端口后立即关闭，构造 Docker/local 可复现的连接失败，不依赖外网。
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])
    finally:
        probe.close()


def _local_connection_failure_seen():
    # 只记录“本地连接失败已被观察到”，不把端口号或底层异常写进 artifact。
    port = _find_closed_local_port()
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return False
    except OSError:
        return True


def _network_recovery_not_proven():
    # artifact 每次都列出未证明项，避免把 Docker/local drill 扩大解释成真实 4G/云恢复。
    return [
        "real_cloud",
        "real_https_tls",
        "real_4g_sim",
        "https_tls_public_ingress",
        "production_db_or_queue",
        "multi_instance_consistency",
        "production_incident_recovery",
        "real_oss_upload",
        "cdn_origin_fetch",
        "formal_phone_app",
        "nav2_or_fixed_route_delivery",
        "wave_rover_or_hil",
        "delivery_success",
    ]


def _network_recovery_forbidden_markers(payload):
    # network recovery artifact 面向手机/支持人员，必须比普通 state 更严格地防泄漏。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer",
        "token",
        "oss secret",
        "access_key",
        "ak/sk",
        "root password",
        "state path",
        "/tmp/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
    )
    return [marker for marker in markers if marker in encoded]


def _network_step(name, status, safe_summary, retry_hint, details=None):
    # step 的 details 只允许布尔、计数和枚举；原始异常、路径和 endpoint 不进入证据。
    return {
        "name": name,
        "status": status,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "details": safe_value(details if isinstance(details, dict) else {}),
    }


def _seed_network_recovery_store(store, robot_id, now_value):
    # 恢复演练只写标准 command/status/ack envelope，不触发 ROS2 action 或底盘控制。
    active_now = max(float(now_value), _now())
    command = {
        "protocol_version": PROTOCOL_VERSION,
        "id": "cmd-network-recovery-1",
        "type": "collect",
        "expires_at": active_now + 300.0,
        "payload": {"target": "trash_station", "trash_type": 0},
    }
    status = {
        "protocol_version": PROTOCOL_VERSION,
        "state": "delivering",
        "message": "network recovery drill status",
        "updated_at": active_now,
        "diagnostics": {"network_recovery_drill": "software_proof"},
    }
    store.submit_command(robot_id, command)
    store.post_status(robot_id, status)


def network_recovery_drill_payload(
    state_path,
    *,
    state_backend="sqlite",
    robot_id="trashbot-001",
    now=None,
):
    """Run a Docker/local network recovery drill and return a phone-safe artifact."""
    now_value = _now() if now is None else float(now)
    updated_at = _utc_iso(now_value)
    store = build_relay_store(state_path, state_backend)
    steps = []
    try:
        unreachable_seen = _local_connection_failure_seen()
        steps.append(
            _network_step(
                "relay_or_cloud_unreachable",
                "passed" if unreachable_seen else "failed",
                "已在本地观察到等价的 relay/cloud 连接失败。",
                "等待 relay/cloud 恢复后重试 command/status/ack 对账。",
                {"connection_failed": bool(unreachable_seen), "local_only": True},
            )
        )
        _seed_network_recovery_store(store, robot_id, now_value)
        before_ack = store.next_command(robot_id, "")
        if before_ack.get("command", {}).get("id") != "cmd-network-recovery-1":
            raise ValueError("command envelope missing before ack")
        steps.append(
            _network_step(
                "ack_post_failure_is_not_delivery_success",
                "passed",
                "ACK post failure 不会被写成 delivery success，cursor 仍可重试同一 command。",
                "网络恢复后重新 POST terminal ACK；手机继续读取 status 判断任务进展。",
                {
                    "ack_posted": False,
                    "delivery_success": False,
                    "cursor_advanced": False,
                    "retry_same_command": True,
                },
            )
        )
        ack_result = store.post_ack(
            robot_id,
            "cmd-network-recovery-1",
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "acked",
                "message": "command envelope accepted after network recovery",
                "updated_at": now_value + 1.0,
                "result": {"envelope_processed": True, "delivery_success": False},
            },
        )
        ack_code, ack_payload = store.get_ack(robot_id, "cmd-network-recovery-1")
        status_code, status_payload = store.get_status(robot_id)
        after_ack = store.next_command(robot_id, "cmd-network-recovery-1")
        envelope_recovered = (
            bool(ack_result.get("ok"))
            and ack_code == 200
            and status_code == 200
            and ack_payload.get("ack", {}).get("state") == "acked"
            and status_payload.get("status", {}).get("state") == "delivering"
            and after_ack.get("command") is None
        )
        steps.append(
            _network_step(
                "recovery_command_status_ack_envelope",
                "passed" if envelope_recovered else "failed",
                "恢复后 command/status/ack envelope 可重新对账。",
                "若失败，请重新运行 relay state 恢复和 bridge compatibility fence。",
                {
                    "command_replayed": True,
                    "status_http_shape": status_code == 200,
                    "ack_http_shape": ack_code == 200,
                    "cursor_after_ack_empty": after_ack.get("command") is None,
                },
            )
        )
        store.post_status(
            robot_id,
            {
                "protocol_version": PROTOCOL_VERSION,
                "state": "delivering",
                "message": "stale status for phone-safe drill",
                "updated_at": now_value - STATUS_STALE_AFTER_SEC - 10.0,
            },
        )
        stale_code, stale_payload = store.get_status(robot_id)
        stale_blocked = stale_code == 409 and stale_payload.get("error", {}).get("code") == "status_stale"
        steps.append(
            _network_step(
                "status_stale_phone_safe_blocked",
                "passed" if stale_blocked else "failed",
                "status stale 会进入手机可读 blocked/warning，而不是显示绿色 ready。",
                "等待小车重新上报新状态，或检查 relay/cloud 网络。",
                {
                    "http_status": "stale",
                    "phone_safe_blocked": bool(stale_blocked),
                    "delivery_success": False,
                },
            )
        )
        cursor_invariant = {
            "ack_failure_advances_cursor": False,
            "terminal_ack_required_before_cursor_advance": True,
            "ack_is_delivery_success": False,
            "recovery_replays_same_command": True,
        }
        overall_status = "passed" if all(step["status"] == "passed" for step in steps) else "failed"
        safe_summary = (
            "Docker/local network recovery drill passed; phones may treat this as software proof only."
            if overall_status == "passed"
            else "Network recovery drill failed; phones must keep recovery state blocked."
        )
        retry_hint = (
            "pass_artifact_to_preflight_and_robot_bridge_compatibility_fence"
            if overall_status == "passed"
            else "rerun_network_recovery_drill_after_fixing_failed_step"
        )
        body = {
            "schema": NETWORK_RECOVERY_SCHEMA,
            "schema_version": NETWORK_RECOVERY_SCHEMA_VERSION,
            "service": "remote_cloud_relay",
            "protocol_version": PROTOCOL_VERSION,
            "evidence_boundary": NETWORK_RECOVERY_EVIDENCE_BOUNDARY,
            "overall_status": overall_status,
            "steps": steps,
            "cursor_invariant": cursor_invariant,
            "safe_summary": safe_summary,
            "retry_hint": retry_hint,
            "not_proven": _network_recovery_not_proven(),
            "updated_at": updated_at,
        }
        forbidden = _network_recovery_forbidden_markers(body)
        if forbidden:
            raise ValueError("network recovery artifact contains forbidden markers")
        artifact = dict(body)
        artifact["checksum"] = _sha256_checksum(body)
        return artifact
    except (ValueError, OSError, sqlite3.Error) as exc:
        body = {
            "schema": NETWORK_RECOVERY_SCHEMA,
            "schema_version": NETWORK_RECOVERY_SCHEMA_VERSION,
            "service": "remote_cloud_relay",
            "protocol_version": PROTOCOL_VERSION,
            "evidence_boundary": NETWORK_RECOVERY_EVIDENCE_BOUNDARY,
            "overall_status": "failed",
            "steps": steps
            + [
                _network_step(
                    "drill_failed",
                    "failed",
                    PHONE_COPY["network_recovery_blocked"],
                    "修复失败步骤后重新运行 network recovery drill。",
                    {"reason_code": "network_recovery_failed"},
                )
            ],
            "cursor_invariant": {
                "ack_failure_advances_cursor": False,
                "terminal_ack_required_before_cursor_advance": True,
                "ack_is_delivery_success": False,
                "recovery_replays_same_command": False,
            },
            "safe_summary": PHONE_COPY["network_recovery_blocked"],
            "retry_hint": "rerun_network_recovery_drill_after_fixing_failed_step",
            "not_proven": _network_recovery_not_proven(),
            "updated_at": updated_at,
            "error": phone_error("network_recovery_blocked", _safe_error_reason(exc))["error"],
        }
        artifact = safe_value(body)
        artifact["checksum"] = _sha256_checksum(body)
        return artifact


def create_network_recovery_artifact(artifact_path, state_path, *, state_backend="sqlite", robot_id="trashbot-001"):
    # CLI smoke 和 preflight 使用同一个 artifact，保证 checksum 与摘要语义一致。
    artifact = network_recovery_drill_payload(state_path, state_backend=state_backend, robot_id=robot_id)
    _write_json_artifact(artifact_path, artifact)
    return {
        "ok": artifact.get("overall_status") == "passed",
        "network_recovery_status": artifact.get("overall_status"),
        "evidence_boundary": NETWORK_RECOVERY_EVIDENCE_BOUNDARY,
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": validate_network_recovery_artifact_payload(artifact),
        "not_proven": artifact.get("not_proven", []),
    }


def validate_network_recovery_artifact_payload(artifact, *, now=None, stale_after_sec=None):
    # 校验只返回摘要；完整 steps 不进入 preflight/phone 输出，避免把内部细节扩散。
    if not isinstance(artifact, dict):
        raise ValueError("network recovery artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != NETWORK_RECOVERY_SCHEMA:
        raise ValueError("network recovery schema mismatch")
    if artifact.get("schema_version") != NETWORK_RECOVERY_SCHEMA_VERSION:
        raise ValueError("network recovery schema version mismatch")
    if artifact.get("evidence_boundary") != NETWORK_RECOVERY_EVIDENCE_BOUNDARY:
        raise ValueError("network recovery evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("network recovery checksum mismatch")
    forbidden = _network_recovery_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("network recovery artifact contains forbidden markers")
    steps = artifact.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("network recovery steps missing")
    required_steps = {
        "relay_or_cloud_unreachable",
        "ack_post_failure_is_not_delivery_success",
        "recovery_command_status_ack_envelope",
        "status_stale_phone_safe_blocked",
    }
    step_names = {str(step.get("name")) for step in steps if isinstance(step, dict)}
    if not required_steps.issubset(step_names):
        raise ValueError("network recovery required steps missing")
    cursor_invariant = artifact.get("cursor_invariant")
    if not isinstance(cursor_invariant, dict):
        raise ValueError("network recovery cursor invariant missing")
    if cursor_invariant.get("ack_failure_advances_cursor") is not False:
        raise ValueError("network recovery cursor invariant mismatch")
    if cursor_invariant.get("terminal_ack_required_before_cursor_advance") is not True:
        raise ValueError("network recovery terminal ack invariant mismatch")
    if cursor_invariant.get("ack_is_delivery_success") is not False:
        raise ValueError("network recovery ack semantics mismatch")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in _network_recovery_not_proven() if item not in not_proven]
    if missing_not_proven:
        raise ValueError("network recovery not_proven list is incomplete")
    updated_at = str(artifact.get("updated_at") or "").strip()
    timestamp = _parse_manifest_time(updated_at)
    stale_window = (
        NETWORK_RECOVERY_ARTIFACT_STALE_AFTER_SEC
        if stale_after_sec is None
        else float(stale_after_sec)
    )
    now_value = _now() if now is None else float(now)
    staleness = "fresh"
    if timestamp is None or now_value - timestamp > stale_window:
        staleness = "stale"
    return {
        "ok": artifact.get("overall_status") == "passed" and staleness == "fresh",
        "schema": NETWORK_RECOVERY_SCHEMA,
        "schema_version": NETWORK_RECOVERY_SCHEMA_VERSION,
        "evidence_boundary": NETWORK_RECOVERY_EVIDENCE_BOUNDARY,
        "overall_status": str(artifact.get("overall_status") or ""),
        "step_count": len(steps),
        "cursor_invariant": {
            "ack_failure_advances_cursor": False,
            "terminal_ack_required_before_cursor_advance": True,
            "ack_is_delivery_success": False,
        },
        "safe_summary": str(artifact.get("safe_summary") or ""),
        "retry_hint": str(artifact.get("retry_hint") or ""),
        "updated_at": updated_at,
        "staleness": staleness,
        "checksum": checksum,
        "not_proven": _network_recovery_not_proven(),
    }


def network_recovery_artifact_summary(artifact_path, *, now=None, stale_after_sec=None):
    # preflight 只需状态和摘要；路径、checksum 以外的原始 artifact 不回显。
    try:
        artifact = _load_json_file(artifact_path, "network recovery artifact")
        summary = validate_network_recovery_artifact_payload(
            artifact,
            now=now,
            stale_after_sec=stale_after_sec,
        )
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "network_recovery_invalid",
            "safe_summary": "网络恢复演练产物损坏。",
            "retry_hint": "重新运行 network recovery drill 并刷新 preflight。",
            "evidence_boundary": NETWORK_RECOVERY_EVIDENCE_BOUNDARY,
            "not_proven": _network_recovery_not_proven(),
            "debug_reason": _safe_error_reason(exc),
        }
    if summary.get("staleness") == "stale":
        summary.update(
            {
                "ok": False,
                "state": "stale",
                "reason_code": "network_recovery_stale",
                "safe_summary": "网络恢复演练已过期。",
                "retry_hint": "重新运行 network recovery drill，避免手机消费旧恢复证据。",
            }
        )
        return summary
    if summary.get("overall_status") != "passed":
        summary.update(
            {
                "ok": False,
                "state": "failed",
                "reason_code": "network_recovery_failed",
                "safe_summary": "网络恢复演练失败。",
                "retry_hint": "修复失败步骤并重新运行 network recovery drill。",
            }
        )
        return summary
    summary.update({"state": "ready", "reason_code": "network_recovery_passed"})
    return summary


def _phone_network_recovery_base(state, safe_summary, retry_hint):
    # 手机端 summary 是 artifact 的小视图，不暴露 steps、state path、端口或异常栈。
    return {
        "state": state,
        "schema": NETWORK_RECOVERY_SCHEMA,
        "schema_version": NETWORK_RECOVERY_SCHEMA_VERSION,
        "evidence_boundary": NETWORK_RECOVERY_PHONE_EVIDENCE_BOUNDARY,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "overall_status": "",
        "step_count": 0,
        "updated_at": "",
        "staleness": "unknown",
        "not_proven": _network_recovery_not_proven(),
    }


def build_phone_network_recovery_summary(artifact_path, *, now=None, stale_after_sec=None):
    """Return a phone-safe network recovery drill summary."""
    artifact_ref = os.path.expanduser(str(artifact_path or "")).strip()
    if not artifact_ref or not os.path.exists(artifact_ref):
        return _phone_network_recovery_base(
            "missing",
            "网络恢复演练产物缺失。",
            "请运行 network recovery drill 后刷新状态。",
        )
    summary = network_recovery_artifact_summary(
        artifact_ref,
        now=now,
        stale_after_sec=stale_after_sec,
    )
    if not summary.get("ok"):
        state = str(summary.get("state") or "invalid")
        return _phone_network_recovery_base(
            state,
            str(summary.get("safe_summary") or "网络恢复演练不可用。"),
            str(summary.get("retry_hint") or "重新运行 network recovery drill 后刷新状态。"),
        )
    phone_summary = _phone_network_recovery_base(
        "ready",
        "网络恢复演练已通过；这只是 Docker/local software proof。",
        "继续等待 robot bridge compatibility fence 和真实云/4G 后续验收。",
    )
    phone_summary.update(
        {
            "overall_status": "passed",
            "step_count": int(summary.get("step_count", 0) or 0),
            "updated_at": str(summary.get("updated_at") or ""),
            "staleness": str(summary.get("staleness") or "fresh"),
        }
    )
    return phone_summary


def _credential_rotation_forbidden_markers(payload):
    # credential artifact 是给 preflight/手机消费的 proof，必须主动拒绝凭证、路径和底层控制词。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "oss secret",
        "oss_access_key",
        "access_key",
        "access key",
        "secret_key",
        "secret key",
        "ak/sk",
        "ak sk",
        "root password",
        "raw state path",
        "state path",
        "/tmp/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
    )
    return [marker for marker in markers if marker in encoded]


def build_credential_rotation_artifact_payload(robot_id, *, generated_at=None):
    """生成 Docker/local 凭证轮换 gate artifact；不签发真实 STS 或生产 token。"""
    robot_key = _robot_key(robot_id)
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    body = {
        "schema": CREDENTIAL_ROTATION_SCHEMA,
        "schema_version": CREDENTIAL_ROTATION_SCHEMA_VERSION,
        "evidence_boundary": CREDENTIAL_ROTATION_EVIDENCE_BOUNDARY,
        "robot_id": robot_key,
        "generated_at": generated_value,
        "bearer_rotation_status": "local_rotation_gate_passed",
        "oss_credential_mode": "sts_or_restricted_ak_required",
        "sts_boundary_status": "software_boundary_documented",
        "account_tier_status": "production_account_not_proven",
        "robot_provisioning_status": "software_provisioning_contract_documented",
        "audit_log_status": "audit_log_contract_documented",
        "not_proven": list(CREDENTIAL_ROTATION_NOT_PROVEN),
        "safe_summary": "凭证轮换 gate 已生成 Docker/local software proof；仍未证明真实生产 rotate。",
        "retry_hint": "pass_credential_rotation_artifact_to_preflight_and_keep_production_not_proven",
    }
    forbidden = _credential_rotation_forbidden_markers(body)
    if forbidden:
        raise ValueError("credential rotation artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_credential_rotation_artifact_payload(artifact, *, now=None, stale_after_sec=None):
    # 校验只返回摘要字段；完整 artifact、robot_id 和 checksum 不进入手机 diagnostics。
    if not isinstance(artifact, dict):
        raise ValueError("credential rotation artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != CREDENTIAL_ROTATION_SCHEMA:
        raise ValueError("credential rotation schema mismatch")
    if artifact.get("schema_version") != CREDENTIAL_ROTATION_SCHEMA_VERSION:
        raise ValueError("credential rotation schema version mismatch")
    if artifact.get("evidence_boundary") != CREDENTIAL_ROTATION_EVIDENCE_BOUNDARY:
        raise ValueError("credential rotation evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("credential rotation checksum mismatch")
    expected_statuses = {
        "bearer_rotation_status": "local_rotation_gate_passed",
        "oss_credential_mode": "sts_or_restricted_ak_required",
        "sts_boundary_status": "software_boundary_documented",
        "account_tier_status": "production_account_not_proven",
        "robot_provisioning_status": "software_provisioning_contract_documented",
        "audit_log_status": "audit_log_contract_documented",
    }
    for field_name, expected in expected_statuses.items():
        if artifact.get(field_name) != expected:
            raise ValueError(f"credential rotation {field_name} mismatch")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in CREDENTIAL_ROTATION_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("credential rotation not_proven list is incomplete")
    safe_summary = str(artifact.get("safe_summary") or "")
    retry_hint = str(artifact.get("retry_hint") or "")
    if not safe_summary or not retry_hint:
        raise ValueError("credential rotation phone copy missing")
    forbidden = _credential_rotation_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("credential rotation artifact contains forbidden phone-unsafe markers")
    generated_at = str(artifact.get("generated_at") or "").strip()
    timestamp = _parse_manifest_time(generated_at)
    stale_window = (
        CREDENTIAL_ROTATION_ARTIFACT_STALE_AFTER_SEC
        if stale_after_sec is None
        else float(stale_after_sec)
    )
    now_value = _now() if now is None else float(now)
    staleness = "fresh"
    if timestamp is None or now_value - timestamp > stale_window:
        staleness = "stale"
    return {
        "ok": staleness == "fresh",
        "schema": CREDENTIAL_ROTATION_SCHEMA,
        "schema_version": CREDENTIAL_ROTATION_SCHEMA_VERSION,
        "evidence_boundary": CREDENTIAL_ROTATION_EVIDENCE_BOUNDARY,
        "bearer_rotation_status": expected_statuses["bearer_rotation_status"],
        "oss_credential_mode": expected_statuses["oss_credential_mode"],
        "sts_boundary_status": expected_statuses["sts_boundary_status"],
        "account_tier_status": expected_statuses["account_tier_status"],
        "robot_provisioning_status": expected_statuses["robot_provisioning_status"],
        "audit_log_status": expected_statuses["audit_log_status"],
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "generated_at": generated_at,
        "staleness": staleness,
        "checksum": checksum,
        "not_proven": list(CREDENTIAL_ROTATION_NOT_PROVEN),
    }


def create_credential_rotation_artifact(artifact_path, robot_id):
    # CLI、preflight 和手机摘要共用同一份 artifact，避免软件证明口径分叉。
    artifact = build_credential_rotation_artifact_payload(robot_id)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_credential_rotation_artifact_payload(artifact)
    return {
        "ok": True,
        "credential_rotation_status": "passed",
        "evidence_boundary": CREDENTIAL_ROTATION_EVIDENCE_BOUNDARY,
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(CREDENTIAL_ROTATION_NOT_PROVEN),
    }


def credential_rotation_artifact_summary(artifact_path, *, now=None, stale_after_sec=None):
    # preflight 只消费摘要和校验结论；artifact 路径、robot_id 和 checksum 不回显。
    try:
        artifact = _load_json_file(artifact_path, "credential rotation artifact")
        summary = validate_credential_rotation_artifact_payload(
            artifact,
            now=now,
            stale_after_sec=stale_after_sec,
        )
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "credential_rotation_invalid",
            "safe_summary": "凭证轮换软件证明产物损坏。",
            "retry_hint": "重新生成 credential rotation artifact 后刷新 preflight。",
            "evidence_boundary": CREDENTIAL_ROTATION_EVIDENCE_BOUNDARY,
            "not_proven": list(CREDENTIAL_ROTATION_NOT_PROVEN),
            "debug_reason": _safe_error_reason(exc),
        }
    if summary.get("staleness") == "stale":
        summary.update(
            {
                "ok": False,
                "state": "stale",
                "reason_code": "credential_rotation_stale",
                "safe_summary": "凭证轮换软件证明已过期。",
                "retry_hint": "重新生成 credential rotation artifact，避免手机消费旧证明。",
            }
        )
        return summary
    summary.update({"state": "ready", "reason_code": "credential_rotation_passed"})
    return summary


def _phone_credential_rotation_base(state, safe_summary, retry_hint):
    # 手机端只看摘要和 not_proven，不展示 artifact 原文、checksum、路径或 robot_id。
    return {
        "state": state,
        "schema": CREDENTIAL_ROTATION_SCHEMA,
        "schema_version": CREDENTIAL_ROTATION_SCHEMA_VERSION,
        "evidence_boundary": CREDENTIAL_ROTATION_PHONE_EVIDENCE_BOUNDARY,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "bearer_rotation_status": "",
        "oss_credential_mode": "",
        "sts_boundary_status": "",
        "account_tier_status": "",
        "robot_provisioning_status": "",
        "audit_log_status": "",
        "generated_at": "",
        "staleness": "unknown",
        "not_proven": list(CREDENTIAL_ROTATION_NOT_PROVEN),
    }


def build_phone_credential_rotation_summary(artifact_path, *, now=None, stale_after_sec=None):
    """Return a phone-safe credential rotation gate summary."""
    artifact_ref = os.path.expanduser(str(artifact_path or "")).strip()
    if not artifact_ref or not os.path.exists(artifact_ref):
        return _phone_credential_rotation_base(
            "missing",
            "凭证轮换软件证明缺失。",
            "请生成 credential rotation artifact 后刷新状态。",
        )
    summary = credential_rotation_artifact_summary(
        artifact_ref,
        now=now,
        stale_after_sec=stale_after_sec,
    )
    if not summary.get("ok"):
        return _phone_credential_rotation_base(
            str(summary.get("state") or "invalid"),
            str(summary.get("safe_summary") or "凭证轮换软件证明不可用。"),
            str(summary.get("retry_hint") or "重新生成 credential rotation artifact 后刷新状态。"),
        )
    phone_summary = _phone_credential_rotation_base(
        "ready",
        "凭证轮换软件证明已准备；这只是 Docker/local software proof。",
        "继续补真实云账号、STS 签发、审计日志和生产 rotate 证据。",
    )
    phone_summary.update(
        {
            "bearer_rotation_status": str(summary.get("bearer_rotation_status") or ""),
            "oss_credential_mode": str(summary.get("oss_credential_mode") or ""),
            "sts_boundary_status": str(summary.get("sts_boundary_status") or ""),
            "account_tier_status": str(summary.get("account_tier_status") or ""),
            "robot_provisioning_status": str(summary.get("robot_provisioning_status") or ""),
            "audit_log_status": str(summary.get("audit_log_status") or ""),
            "generated_at": str(summary.get("generated_at") or ""),
            "staleness": str(summary.get("staleness") or "fresh"),
        }
    )
    return phone_summary


def _provisioning_audit_forbidden_markers(payload):
    # provisioning audit 是上线前阻断证据，必须比普通 diagnostics 更严格地拒绝敏感词。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "oss secret",
        "oss_access_key",
        "access_key",
        "access key",
        "secret_key",
        "secret key",
        "ak/sk",
        "ak sk",
        "root password",
        "credential url",
        "credential_url",
        "raw state path",
        "state path",
        "/tmp/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


def build_provisioning_audit_artifact_payload(robot_id, *, generated_at=None):
    """生成 Docker/local provisioning audit gate；不签发真实 STS 或写真实审计日志。"""
    robot_key = _robot_key(robot_id)
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    body = {
        "schema": PROVISIONING_AUDIT_SCHEMA,
        "schema_version": PROVISIONING_AUDIT_SCHEMA_VERSION,
        "evidence_boundary": PROVISIONING_AUDIT_EVIDENCE_BOUNDARY,
        "robot_id": robot_key,
        "generated_at": generated_value,
        "robot_provisioning_status": "local_contract_artifact_present",
        "sts_issuance_status": "not_issued_boundary_documented",
        "audit_log_status": "local_audit_contract_artifact_present",
        "credential_delivery_status": "no_sensitive_material_exported",
        "production_ready": False,
        "overall_status": "blocked",
        "not_proven": list(PROVISIONING_AUDIT_NOT_PROVEN),
        "safe_summary": "Provisioning / STS / audit gate 已生成 Docker/local software proof；生产证据仍未补齐。",
        "retry_hint": "pass_provisioning_audit_artifact_to_preflight_and_keep_production_blocked",
    }
    forbidden = _provisioning_audit_forbidden_markers(body)
    if forbidden:
        raise ValueError("provisioning audit artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_provisioning_audit_artifact_payload(artifact, *, now=None, stale_after_sec=None):
    # 校验返回小摘要；完整 artifact、robot_id 和 checksum 不进入手机 status 或 diagnostics。
    if not isinstance(artifact, dict):
        raise ValueError("provisioning audit artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != PROVISIONING_AUDIT_SCHEMA:
        raise ValueError("provisioning audit schema mismatch")
    if artifact.get("schema_version") != PROVISIONING_AUDIT_SCHEMA_VERSION:
        raise ValueError("provisioning audit schema version mismatch")
    if artifact.get("evidence_boundary") != PROVISIONING_AUDIT_EVIDENCE_BOUNDARY:
        raise ValueError("provisioning audit evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("provisioning audit checksum mismatch")
    expected_statuses = {
        "robot_provisioning_status": "local_contract_artifact_present",
        "sts_issuance_status": "not_issued_boundary_documented",
        "audit_log_status": "local_audit_contract_artifact_present",
        "credential_delivery_status": "no_sensitive_material_exported",
    }
    for field_name, expected in expected_statuses.items():
        if artifact.get(field_name) != expected:
            raise ValueError(f"provisioning audit {field_name} mismatch")
    if artifact.get("production_ready") is not False or artifact.get("overall_status") != "blocked":
        raise ValueError("provisioning audit must stay production blocked")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in PROVISIONING_AUDIT_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("provisioning audit not_proven list is incomplete")
    safe_summary = str(artifact.get("safe_summary") or "")
    retry_hint = str(artifact.get("retry_hint") or "")
    if not safe_summary or not retry_hint:
        raise ValueError("provisioning audit phone copy missing")
    forbidden = _provisioning_audit_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("provisioning audit artifact contains forbidden phone-unsafe markers")
    generated_at = str(artifact.get("generated_at") or "").strip()
    timestamp = _parse_manifest_time(generated_at)
    stale_window = (
        PROVISIONING_AUDIT_ARTIFACT_STALE_AFTER_SEC
        if stale_after_sec is None
        else float(stale_after_sec)
    )
    now_value = _now() if now is None else float(now)
    staleness = "fresh"
    if timestamp is None or now_value - timestamp > stale_window:
        staleness = "stale"
    return {
        "ok": staleness == "fresh",
        "schema": PROVISIONING_AUDIT_SCHEMA,
        "schema_version": PROVISIONING_AUDIT_SCHEMA_VERSION,
        "evidence_boundary": PROVISIONING_AUDIT_EVIDENCE_BOUNDARY,
        "robot_provisioning_status": expected_statuses["robot_provisioning_status"],
        "sts_issuance_status": expected_statuses["sts_issuance_status"],
        "audit_log_status": expected_statuses["audit_log_status"],
        "credential_delivery_status": expected_statuses["credential_delivery_status"],
        "production_ready": False,
        "overall_status": "blocked",
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "generated_at": generated_at,
        "staleness": staleness,
        "checksum": checksum,
        "not_proven": list(PROVISIONING_AUDIT_NOT_PROVEN),
    }


def create_provisioning_audit_artifact(artifact_path, robot_id):
    # CLI、preflight 和手机摘要共用同一校验函数，避免三类 gate 口径分叉。
    artifact = build_provisioning_audit_artifact_payload(robot_id)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_provisioning_audit_artifact_payload(artifact)
    return {
        "ok": True,
        "provisioning_audit_status": "blocked",
        "evidence_boundary": PROVISIONING_AUDIT_EVIDENCE_BOUNDARY,
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(PROVISIONING_AUDIT_NOT_PROVEN),
    }


def provisioning_audit_artifact_summary(artifact_path, *, now=None, stale_after_sec=None):
    # preflight 只消费摘要和校验结论；路径、robot_id、checksum 不回显。
    try:
        artifact = _load_json_file(artifact_path, "provisioning audit artifact")
        summary = validate_provisioning_audit_artifact_payload(
            artifact,
            now=now,
            stale_after_sec=stale_after_sec,
        )
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "provisioning_audit_invalid",
            "safe_summary": "Provisioning / STS / audit 软件证明产物损坏。",
            "retry_hint": "重新生成 provisioning audit artifact 后刷新 preflight。",
            "evidence_boundary": PROVISIONING_AUDIT_EVIDENCE_BOUNDARY,
            "not_proven": list(PROVISIONING_AUDIT_NOT_PROVEN),
            "debug_reason": _safe_error_reason(exc),
        }
    if summary.get("staleness") == "stale":
        summary.update(
            {
                "ok": False,
                "state": "stale",
                "reason_code": "provisioning_audit_stale",
                "safe_summary": "Provisioning / STS / audit 软件证明已过期。",
                "retry_hint": "重新生成 provisioning audit artifact，避免手机消费旧证明。",
            }
        )
        return summary
    summary.update({"state": "ready", "reason_code": "provisioning_audit_passed"})
    return summary


def _phone_provisioning_audit_base(state, safe_summary, retry_hint):
    # 手机端只看三类门禁状态和 not_proven，不展示 artifact 原文、路径或机器人标识。
    return {
        "state": state,
        "schema": PROVISIONING_AUDIT_SCHEMA,
        "schema_version": PROVISIONING_AUDIT_SCHEMA_VERSION,
        "evidence_boundary": PROVISIONING_AUDIT_PHONE_EVIDENCE_BOUNDARY,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "robot_provisioning_status": "",
        "sts_issuance_status": "",
        "audit_log_status": "",
        "credential_delivery_status": "",
        "production_ready": False,
        "overall_status": "blocked",
        "generated_at": "",
        "staleness": "unknown",
        "not_proven": list(PROVISIONING_AUDIT_NOT_PROVEN),
    }


def build_phone_provisioning_audit_summary(artifact_path, *, now=None, stale_after_sec=None):
    """Return a phone-safe provisioning / STS / audit gate summary."""
    artifact_ref = os.path.expanduser(str(artifact_path or "")).strip()
    if not artifact_ref or not os.path.exists(artifact_ref):
        return _phone_provisioning_audit_base(
            "missing",
            "Provisioning / STS / audit 软件证明缺失。",
            "请生成 provisioning audit artifact 后刷新状态。",
        )
    summary = provisioning_audit_artifact_summary(
        artifact_ref,
        now=now,
        stale_after_sec=stale_after_sec,
    )
    if not summary.get("ok"):
        return _phone_provisioning_audit_base(
            str(summary.get("state") or "invalid"),
            str(summary.get("safe_summary") or "Provisioning / STS / audit 软件证明不可用。"),
            str(summary.get("retry_hint") or "重新生成 provisioning audit artifact 后刷新状态。"),
        )
    phone_summary = _phone_provisioning_audit_base(
        "ready",
        "Provisioning / STS / audit 软件证明已准备；这只是 Docker/local software proof。",
        "继续补真实生产 provisioning、STS 签发和审计日志证据。",
    )
    phone_summary.update(
        {
            "robot_provisioning_status": str(summary.get("robot_provisioning_status") or ""),
            "sts_issuance_status": str(summary.get("sts_issuance_status") or ""),
            "audit_log_status": str(summary.get("audit_log_status") or ""),
            "credential_delivery_status": str(summary.get("credential_delivery_status") or ""),
            "generated_at": str(summary.get("generated_at") or ""),
            "staleness": str(summary.get("staleness") or "fresh"),
        }
    )
    return phone_summary


def _deployment_readiness_forbidden_markers(payload):
    # 部署 readiness 会进入 preflight 和 Docker smoke，必须比 runbook 文案更严格地拒绝凭证和底层机器人细节。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "postgres://",
        "mysql://",
        "redis://",
        "amqp://",
        "queue url",
        "queue_url",
        "database url",
        "database_url",
        "://",
        "raw state path",
        "state path",
        "/tmp/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


def _deployment_readiness_checks(env):
    # 只从 env 推导枚举化状态，不回显 URL、token、DB/queue 连接串或本机路径。
    token = _env_value(env, "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN")
    public_scheme = _safe_scheme(_env_value(env, "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL"))
    tls_mode = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_TLS_MODE", "future_reverse_proxy"),
        {"future_reverse_proxy", "terminated", "managed", "reverse_proxy"},
    )
    ingress = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS", "missing"),
        {"missing", "private_only", "public_https"},
    )
    state_backend = _state_backend_from_env(env)
    oss_credential_mode = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE", "placeholder"),
        {"placeholder", "sts", "restricted_ak", "managed_identity"},
    )
    deployment_runbook = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_RUNBOOK", "local_docker_smoke"),
        {"local_docker_smoke", "external_runbook_reviewed"},
        "local_docker_smoke",
    )
    return [
        {
            "name": "public_base_url_tls_ingress",
            "status": "blocked" if public_scheme != "https" or ingress != "public_https" else "warning",
            "code": "https_public_ingress_not_proven",
            "safe_summary": "公网 HTTPS 入口尚未用外网探测证明。",
            "retry_hint": "configure_public_https_ingress_and_attach_external_probe",
            "details": {
                "scheme": public_scheme,
                "tls_mode": tls_mode,
                "public_ingress": ingress,
                "external_probe_performed": False,
            },
        },
        {
            "name": "healthcheck_endpoint",
            "status": "warning",
            "code": "local_healthcheck_only",
            "safe_summary": "仅证明 relay 提供本地 /healthz 与 /readyz；未证明公网探针。",
            "retry_hint": "run_cloud_healthcheck_from_external_network_after_deploy",
            "details": {"local_healthz_documented": True, "public_health_probe_performed": False},
        },
        {
            "name": "bearer_credential_placeholder",
            "status": "blocked" if _is_placeholder(token) else "warning",
            "code": "bearer_credential_not_production_verified",
            "safe_summary": "访问凭证仍未完成生产托管、轮换和外部验证。",
            "retry_hint": "inject_production_credential_from_secret_manager_and_verify_rotation",
            "details": {"credential_present": bool(token), "credential_placeholder": _is_placeholder(token)},
        },
        {
            "name": "state_backend",
            "status": "warning",
            "code": "state_backend_not_production_db_queue",
            "safe_summary": "当前 state backend 仍是本地软件证明，不是生产 DB/queue。",
            "retry_hint": "attach_production_db_queue_migration_backup_and_consistency_evidence",
            "details": {"backend": state_backend, "production_db_queue_probe_performed": False},
        },
        {
            "name": "production_db_queue_gap",
            "status": "blocked",
            "code": "production_db_queue_not_proven",
            "safe_summary": "生产 DB/queue、多实例一致性和队列顺序仍未证明。",
            "retry_hint": "run_production_store_queue_gate_against_real_services",
            "details": {"production_ready": False, "software_proof_only": True},
        },
        {
            "name": "oss_cdn_gap",
            "status": "blocked" if oss_credential_mode == "placeholder" else "warning",
            "code": "oss_cdn_real_traffic_not_proven",
            "safe_summary": "OSS/CDN 仍缺真实上传、回源、生命周期和凭证边界证据。",
            "retry_hint": "run_sts_upload_cdn_origin_fetch_and_lifecycle_probe",
            "details": {"credential_mode": oss_credential_mode, "real_object_probe_performed": False},
        },
        {
            "name": "cellular_4g_sim_gap",
            "status": "blocked",
            "code": "real_4g_sim_not_proven",
            "safe_summary": "当前主机没有真实 4G/SIM 或公网链路证据。",
            "retry_hint": "rerun_after_robot_4g_sim_and_cloud_account_are_available",
            "details": {"real_4g_sim_probe_performed": False},
        },
        {
            "name": "deployment_runbook_or_smoke",
            "status": "pass",
            "code": "local_docker_smoke_documented",
            "safe_summary": "本地 Docker smoke/runbook 入口已作为软件证明围栏。",
            "retry_hint": "keep_local_smoke_then_add_external_cloud_smoke_command",
            "details": {"runbook": deployment_runbook, "local_smoke_present": True},
        },
    ]


def build_cloud_deployment_readiness_artifact_payload(env=None, *, generated_at=None):
    """生成云部署 readiness gate artifact；它是上线前缺口清单，不是生产部署证明。"""
    env = os.environ if env is None else env
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    checks = _deployment_readiness_checks(env)
    body = {
        "schema": CLOUD_DEPLOYMENT_READINESS_SCHEMA,
        "schema_version": CLOUD_DEPLOYMENT_READINESS_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_DEPLOYMENT_READINESS_EVIDENCE_BOUNDARY,
        "generated_at": generated_value,
        "production_ready": False,
        "overall_status": "blocked",
        "checks": safe_value(checks),
        "not_proven": list(CLOUD_DEPLOYMENT_READINESS_NOT_PROVEN),
        "safe_summary": "Cloud deployment readiness gate 已生成 Docker/local software proof；生产云和 4G 仍未证明。",
        "retry_hint": "pass_cloud_deployment_readiness_artifact_to_preflight_and_collect_real_cloud_evidence",
    }
    forbidden = _deployment_readiness_forbidden_markers(body)
    if forbidden:
        raise ValueError("cloud deployment readiness artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_cloud_deployment_readiness_artifact_payload(artifact):
    # 校验只返回小摘要；完整 checks、checksum 和任何环境来源字段不进入手机状态。
    if not isinstance(artifact, dict):
        raise ValueError("cloud deployment readiness artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != CLOUD_DEPLOYMENT_READINESS_SCHEMA:
        raise ValueError("cloud deployment readiness schema mismatch")
    if artifact.get("schema_version") != CLOUD_DEPLOYMENT_READINESS_SCHEMA_VERSION:
        raise ValueError("cloud deployment readiness schema version mismatch")
    if artifact.get("evidence_boundary") != CLOUD_DEPLOYMENT_READINESS_EVIDENCE_BOUNDARY:
        raise ValueError("cloud deployment readiness evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("cloud deployment readiness checksum mismatch")
    if artifact.get("production_ready") is not False or artifact.get("overall_status") != "blocked":
        raise ValueError("cloud deployment readiness must stay production blocked")
    checks = artifact.get("checks")
    if not isinstance(checks, list):
        raise ValueError("cloud deployment readiness checks must be a list")
    check_names = {str(check.get("name") or "") for check in checks if isinstance(check, dict)}
    required_checks = {
        "public_base_url_tls_ingress",
        "healthcheck_endpoint",
        "bearer_credential_placeholder",
        "state_backend",
        "production_db_queue_gap",
        "oss_cdn_gap",
        "cellular_4g_sim_gap",
        "deployment_runbook_or_smoke",
    }
    if required_checks - check_names:
        raise ValueError("cloud deployment readiness required checks missing")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in CLOUD_DEPLOYMENT_READINESS_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("cloud deployment readiness not_proven list is incomplete")
    safe_summary = str(artifact.get("safe_summary") or "")
    retry_hint = str(artifact.get("retry_hint") or "")
    if not safe_summary or not retry_hint:
        raise ValueError("cloud deployment readiness phone copy missing")
    forbidden = _deployment_readiness_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("cloud deployment readiness artifact contains forbidden phone-unsafe markers")
    return {
        "ok": True,
        "schema": CLOUD_DEPLOYMENT_READINESS_SCHEMA,
        "schema_version": CLOUD_DEPLOYMENT_READINESS_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_DEPLOYMENT_READINESS_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "check_count": len(checks),
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "generated_at": str(artifact.get("generated_at") or ""),
        "not_proven": list(CLOUD_DEPLOYMENT_READINESS_NOT_PROVEN),
    }


def create_cloud_deployment_readiness_artifact(artifact_path, env=None):
    # CLI、Docker smoke 和 preflight 共用同一 artifact，避免“本地可跑”和“生产就绪”口径分叉。
    artifact = build_cloud_deployment_readiness_artifact_payload(env)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_cloud_deployment_readiness_artifact_payload(artifact)
    return {
        "ok": True,
        "cloud_deployment_readiness_status": "blocked",
        "evidence_boundary": CLOUD_DEPLOYMENT_READINESS_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(CLOUD_DEPLOYMENT_READINESS_NOT_PROVEN),
    }


def cloud_deployment_readiness_artifact_summary(artifact_path):
    # preflight 只消费摘要和 checksum 校验结果；artifact 路径和完整 checks 不回显。
    try:
        artifact = _load_json_file(artifact_path, "cloud deployment readiness artifact")
        return validate_cloud_deployment_readiness_artifact_payload(artifact)
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "cloud_deployment_readiness_invalid",
            "safe_summary": _safe_error_reason(exc),
            "retry_hint": "重新生成 cloud deployment readiness artifact 后重跑 preflight。",
            "not_proven": list(CLOUD_DEPLOYMENT_READINESS_NOT_PROVEN),
        }


def _cloud_external_probe_forbidden_markers(payload):
    # 外部探测 bundle 会被手机和 preflight 消费，只能保留路径和枚举状态，不能保留 base URL 或响应体。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "postgres://",
        "mysql://",
        "redis://",
        "amqp://",
        "://",
        "raw state path",
        "state path",
        "/tmp/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


def _probe_endpoint(base_url, endpoint, timeout_sec):
    # 只记录可验收的机器字段；不保留 URL、header、response body，避免把公网或凭证信息写进 artifact。
    target = f"{str(base_url).rstrip('/')}{endpoint}"
    started = time.monotonic()
    status_code = 0
    body = b""
    reachable = False
    try:
        with urllib.request.urlopen(target, timeout=float(timeout_sec)) as response:
            status_code = int(response.status)
            body = response.read(65536)
            reachable = True
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
        body = exc.read(65536)
        reachable = True
    except (OSError, ValueError, TimeoutError):
        return {
            "endpoint": endpoint,
            "status": "blocked",
            "code": "endpoint_unreachable",
            "http_status": 0,
            "reachable": False,
            "json_ok": False,
            "expected_keys_present": False,
            "latency_ms": int((time.monotonic() - started) * 1000),
        }

    json_ok = False
    expected_keys_present = False
    try:
        payload = json.loads(body.decode("utf-8") or "{}")
        json_ok = isinstance(payload, dict)
        if endpoint == "/healthz":
            expected_keys_present = all(key in payload for key in ("ok", "service", "protocol_version"))
        elif endpoint == "/readyz":
            expected_keys_present = all(key in payload for key in ("ok", "checks"))
        elif endpoint == "/preflightz":
            expected_keys_present = all(key in payload for key in ("production_ready", "overall_status", "checks"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        json_ok = False

    http_expected = status_code == 200 if endpoint in {"/healthz", "/readyz"} else status_code in {200, 503}
    passed = reachable and http_expected and json_ok and expected_keys_present
    return {
        "endpoint": endpoint,
        "status": "pass" if passed else "blocked",
        "code": "endpoint_contract_observed" if passed else "endpoint_contract_missing",
        "http_status": status_code,
        "reachable": reachable,
        "json_ok": json_ok,
        "expected_keys_present": expected_keys_present,
        "latency_ms": int((time.monotonic() - started) * 1000),
    }


def build_cloud_external_probe_bundle_payload(base_url, *, generated_at=None, timeout_sec=2.0):
    """探测 cloud relay 三个只读 gate，并生成 Docker/local 软件证明 artifact。"""
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    endpoints = ["/healthz", "/readyz", "/preflightz"]
    results = [_probe_endpoint(base_url, endpoint, timeout_sec) for endpoint in endpoints]
    endpoint_set = {result.get("endpoint") for result in results}
    endpoints_covered = all(endpoint in endpoint_set for endpoint in endpoints)
    endpoint_contract_ready = endpoints_covered and all(result.get("status") == "pass" for result in results)
    body = {
        "schema": CLOUD_EXTERNAL_PROBE_SCHEMA,
        "schema_version": CLOUD_EXTERNAL_PROBE_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
        "generated_at": generated_value,
        "production_ready": False,
        "overall_status": "blocked",
        "base_url_scheme": _safe_scheme(base_url),
        "endpoint_results": safe_value(results),
        "endpoint_contract_ready": bool(endpoint_contract_ready),
        "not_proven": list(CLOUD_EXTERNAL_PROBE_NOT_PROVEN),
        "safe_summary": "Cloud external probe bundle 已覆盖 health/ready/preflight 合同；当前仍只是 Docker/local software proof。",
        "retry_hint": "rerun_probe_from_real_public_https_network_before_claiming_cloud_ready",
        "redaction_status": {
            "status": "pass",
            "base_url_redacted": True,
            "response_body_redacted": True,
            "credential_headers_recorded": False,
        },
    }
    forbidden = _cloud_external_probe_forbidden_markers(body)
    if forbidden:
        raise ValueError("cloud external probe bundle contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_cloud_external_probe_bundle_payload(artifact):
    # preflight 只需要合同摘要；完整 endpoint 结果可在 artifact 中留档，但不能夹带 URL 或响应体。
    if not isinstance(artifact, dict):
        raise ValueError("cloud external probe bundle must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != CLOUD_EXTERNAL_PROBE_SCHEMA:
        raise ValueError("cloud external probe schema mismatch")
    if artifact.get("schema_version") != CLOUD_EXTERNAL_PROBE_SCHEMA_VERSION:
        raise ValueError("cloud external probe schema version mismatch")
    if artifact.get("evidence_boundary") != CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY:
        raise ValueError("cloud external probe evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("cloud external probe checksum mismatch")
    if artifact.get("production_ready") is not False or artifact.get("overall_status") != "blocked":
        raise ValueError("cloud external probe must stay production blocked")
    results = artifact.get("endpoint_results")
    if not isinstance(results, list):
        raise ValueError("cloud external probe endpoint results must be a list")
    result_by_endpoint = {str(result.get("endpoint") or ""): result for result in results if isinstance(result, dict)}
    required = {"/healthz", "/readyz", "/preflightz"}
    if set(result_by_endpoint) != required:
        raise ValueError("cloud external probe endpoint coverage mismatch")
    if not all(result_by_endpoint[endpoint].get("status") == "pass" for endpoint in required):
        raise ValueError("cloud external probe endpoint contract did not pass")
    redaction = artifact.get("redaction_status")
    if not isinstance(redaction, dict) or redaction.get("status") != "pass":
        raise ValueError("cloud external probe redaction status missing")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in CLOUD_EXTERNAL_PROBE_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("cloud external probe not_proven list is incomplete")
    forbidden = _cloud_external_probe_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("cloud external probe bundle contains forbidden phone-unsafe markers")
    return {
        "ok": True,
        "schema": CLOUD_EXTERNAL_PROBE_SCHEMA,
        "schema_version": CLOUD_EXTERNAL_PROBE_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "endpoints_covered": sorted(result_by_endpoint),
        "endpoint_count": len(results),
        "endpoint_contract_ready": True,
        "safe_summary": str(artifact.get("safe_summary") or ""),
        "retry_hint": str(artifact.get("retry_hint") or ""),
        "redaction_status": safe_value(redaction),
        "not_proven": list(CLOUD_EXTERNAL_PROBE_NOT_PROVEN),
    }


def create_cloud_external_probe_bundle_artifact(artifact_path, base_url, *, timeout_sec=2.0):
    # CLI 和 Docker smoke 使用同一个生成函数，避免本地 smoke 与 preflight 消费口径分叉。
    artifact = build_cloud_external_probe_bundle_payload(base_url, timeout_sec=timeout_sec)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_cloud_external_probe_bundle_payload(artifact)
    return {
        "ok": True,
        "cloud_external_probe_status": "blocked",
        "evidence_boundary": CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(CLOUD_EXTERNAL_PROBE_NOT_PROVEN),
    }


def cloud_external_probe_bundle_summary(artifact_path):
    # preflight 摘要不回显 artifact 路径、base URL 或响应体，只回显 endpoint 覆盖和软件证明边界。
    try:
        artifact = _load_json_file(artifact_path, "cloud external probe bundle artifact")
        return validate_cloud_external_probe_bundle_payload(artifact)
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "cloud_external_probe_invalid",
            "safe_summary": _safe_error_reason(exc),
            "retry_hint": "重新生成 cloud external probe bundle artifact 后重跑 preflight。",
            "not_proven": list(CLOUD_EXTERNAL_PROBE_NOT_PROVEN),
        }


def _cloud_public_ingress_tls_forbidden_markers(payload):
    # 公网入口/TLS gate 面向手机和部署 preflight，只能保留枚举结果，不能保留 URL、证书路径或代理配置正文。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "private key",
        "private_key",
        "tls key",
        "certificate path",
        "cert path",
        "postgres://",
        "mysql://",
        "redis://",
        "amqp://",
        "queue url",
        "queue_url",
        "database url",
        "database_url",
        "://",
        "raw state path",
        "state path",
        "/tmp/",
        "/etc/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


def _cloud_public_ingress_tls_config(env):
    # 该 gate 只判断“配置包是否具备形态”，不读取真实证书、域名或反向代理文件内容。
    public_scheme = _safe_scheme(_env_value(env, "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL"))
    tls_mode = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_TLS_MODE", "future_reverse_proxy"),
        {"future_reverse_proxy", "terminated", "managed", "reverse_proxy"},
    )
    ingress = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS", "missing"),
        {"missing", "private_only", "public_https"},
    )
    reverse_proxy = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_REVERSE_PROXY_CONFIG", "missing"),
        {"missing", "planned", "present"},
        "missing",
    )
    firewall = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_FIREWALL_CONFIG", "missing"),
        {"missing", "planned", "present"},
        "missing",
    )
    tls_config_present = public_scheme == "https" and tls_mode in {"terminated", "managed", "reverse_proxy"}
    ingress_config_present = public_scheme == "https" and ingress == "public_https"
    reverse_proxy_config_present = reverse_proxy == "present" or tls_mode in {"terminated", "managed", "reverse_proxy"}
    firewall_config_present = firewall == "present"
    config_package_present = tls_config_present and ingress_config_present and reverse_proxy_config_present
    if config_package_present:
        state = "public_ingress_tls_config_present_not_externally_proven"
        summary = "公网入口/TLS/反向代理配置包形态存在，但还没有真实外部 HTTPS、DNS、反向代理或防火墙实证。"
        retry = "run_external_https_dns_reverse_proxy_firewall_probe_and_attach_evidence"
    else:
        state = "missing_public_ingress_tls_config"
        summary = "尚未形成公网入口/TLS/反向代理配置包，不能进入真实外部 HTTPS 验收。"
        retry = "create_https_public_ingress_reverse_proxy_and_firewall_config_package"
    return {
        "state": state,
        "public_base_url_scheme": public_scheme,
        "tls_mode": tls_mode,
        "public_ingress": ingress,
        "reverse_proxy_config": reverse_proxy,
        "firewall_config": firewall,
        "ingress_config_present": ingress_config_present,
        "tls_config_present": tls_config_present,
        "reverse_proxy_config_present": reverse_proxy_config_present,
        "firewall_config_present": firewall_config_present,
        "config_package_present": config_package_present,
        "external_probe_proven": False,
        "safe_summary": summary,
        "retry_hint": retry,
    }


def build_cloud_public_ingress_tls_artifact_payload(env=None, *, generated_at=None):
    """生成公网入口/TLS 配置 gate artifact；它只证明配置包形态，不证明真实公网链路。"""
    env = os.environ if env is None else env
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    config = _cloud_public_ingress_tls_config(env)
    body = {
        "schema": CLOUD_PUBLIC_INGRESS_TLS_SCHEMA,
        "schema_version": CLOUD_PUBLIC_INGRESS_TLS_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY,
        "generated_at": generated_value,
        "production_ready": False,
        "overall_status": "blocked",
        "state": config["state"],
        "ingress_config_present": config["ingress_config_present"],
        "tls_config_present": config["tls_config_present"],
        "reverse_proxy_config_present": config["reverse_proxy_config_present"],
        "firewall_config_present": config["firewall_config_present"],
        "config_package_present": config["config_package_present"],
        "external_probe_proven": False,
        "details": {
            "public_base_url_scheme": config["public_base_url_scheme"],
            "tls_mode": config["tls_mode"],
            "public_ingress": config["public_ingress"],
            "reverse_proxy_config": config["reverse_proxy_config"],
            "firewall_config": config["firewall_config"],
        },
        "not_proven": list(CLOUD_PUBLIC_INGRESS_TLS_NOT_PROVEN),
        "safe_summary": config["safe_summary"],
        "retry_hint": config["retry_hint"],
    }
    forbidden = _cloud_public_ingress_tls_forbidden_markers(body)
    if forbidden:
        raise ValueError("cloud public ingress TLS artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_cloud_public_ingress_tls_artifact_payload(artifact):
    # 校验返回小摘要；完整 artifact、证书路径、URL 或代理配置正文都不能进入 preflight 输出。
    if not isinstance(artifact, dict):
        raise ValueError("cloud public ingress TLS artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != CLOUD_PUBLIC_INGRESS_TLS_SCHEMA:
        raise ValueError("cloud public ingress TLS schema mismatch")
    if artifact.get("schema_version") != CLOUD_PUBLIC_INGRESS_TLS_SCHEMA_VERSION:
        raise ValueError("cloud public ingress TLS schema version mismatch")
    if artifact.get("evidence_boundary") != CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY:
        raise ValueError("cloud public ingress TLS evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("cloud public ingress TLS checksum mismatch")
    if artifact.get("production_ready") is not False or artifact.get("overall_status") != "blocked":
        raise ValueError("cloud public ingress TLS must stay production blocked")
    state = str(artifact.get("state") or "")
    if state not in {
        "missing_public_ingress_tls_config",
        "public_ingress_tls_config_present_not_externally_proven",
    }:
        raise ValueError("cloud public ingress TLS state mismatch")
    if artifact.get("external_probe_proven") is not False:
        raise ValueError("cloud public ingress TLS external proof must stay false")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in CLOUD_PUBLIC_INGRESS_TLS_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("cloud public ingress TLS not_proven list is incomplete")
    safe_summary = str(artifact.get("safe_summary") or "")
    retry_hint = str(artifact.get("retry_hint") or "")
    if not safe_summary or not retry_hint:
        raise ValueError("cloud public ingress TLS phone copy missing")
    forbidden = _cloud_public_ingress_tls_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("cloud public ingress TLS artifact contains forbidden phone-unsafe markers")
    return {
        "ok": True,
        "schema": CLOUD_PUBLIC_INGRESS_TLS_SCHEMA,
        "schema_version": CLOUD_PUBLIC_INGRESS_TLS_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "state": state,
        "ingress_config_present": bool(artifact.get("ingress_config_present")),
        "tls_config_present": bool(artifact.get("tls_config_present")),
        "reverse_proxy_config_present": bool(artifact.get("reverse_proxy_config_present")),
        "firewall_config_present": bool(artifact.get("firewall_config_present")),
        "config_package_present": bool(artifact.get("config_package_present")),
        "external_probe_proven": False,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "generated_at": str(artifact.get("generated_at") or ""),
        "not_proven": list(CLOUD_PUBLIC_INGRESS_TLS_NOT_PROVEN),
    }


def create_cloud_public_ingress_tls_artifact(artifact_path, env=None):
    # CLI、Docker smoke 和 preflight 使用同一生成函数，确保缺配置/有配置未实证的分类一致。
    artifact = build_cloud_public_ingress_tls_artifact_payload(env)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_cloud_public_ingress_tls_artifact_payload(artifact)
    return {
        "ok": True,
        "cloud_public_ingress_tls_status": "blocked",
        "evidence_boundary": CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "state": artifact.get("state"),
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(CLOUD_PUBLIC_INGRESS_TLS_NOT_PROVEN),
    }


def cloud_public_ingress_tls_artifact_summary(artifact_path):
    # preflight 只读取摘要，不回显 artifact 路径、原始 URL、证书路径或反向代理配置正文。
    try:
        artifact = _load_json_file(artifact_path, "cloud public ingress TLS artifact")
        return validate_cloud_public_ingress_tls_artifact_payload(artifact)
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "cloud_public_ingress_tls_invalid",
            "safe_summary": _safe_error_reason(exc),
            "retry_hint": "重新生成 cloud public ingress TLS artifact 后重跑 preflight。",
            "not_proven": list(CLOUD_PUBLIC_INGRESS_TLS_NOT_PROVEN),
        }


def _cloud_db_queue_config_forbidden_markers(payload):
    # DB/queue 配置 gate 只能输出枚举化 readiness，不允许把连接串、凭证或本机路径写入 proof。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "root password",
        "postgres://",
        "mysql://",
        "redis://",
        "amqp://",
        "kafka://",
        "database url",
        "database_url",
        "db url",
        "db_url",
        "queue url",
        "queue_url",
        "credential-bearing",
        "raw state path",
        "state path",
        "/tmp/",
        "/etc/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


def _cloud_db_queue_config(env):
    # 这里用显式枚举表示“配置包形态”，避免从 DB/queue URL 推断并泄漏真实连接信息。
    db_config = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_DB_CONFIG", "missing"),
        {"missing", "planned", "present"},
        "missing",
    )
    queue_config = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_QUEUE_CONFIG", "missing"),
        {"missing", "planned", "present"},
        "missing",
    )
    migration_config = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_CONFIG", "missing"),
        {"missing", "planned", "present"},
        "missing",
    )
    worker_config = _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_CONFIG", "missing"),
        {"missing", "planned", "present"},
        "missing",
    )
    db_config_present = db_config == "present"
    queue_config_present = queue_config == "present"
    migration_config_present = migration_config == "present"
    worker_config_present = worker_config == "present"
    config_package_present = db_config_present and queue_config_present
    if config_package_present:
        state = "cloud_db_queue_config_present_not_externally_proven"
        summary = "生产 DB/queue 配置包形态存在，但还没有真实连接、多实例、一致性、备份或灾备实证。"
        retry = "run_external_db_queue_connectivity_migration_consistency_and_recovery_probe"
    else:
        state = "missing_cloud_db_queue_config"
        summary = "尚未形成生产 DB/queue 配置包，不能进入真实数据库和队列验收。"
        retry = "create_production_db_queue_config_package_without_embedding_credentials"
    return {
        "state": state,
        "db_config": db_config,
        "queue_config": queue_config,
        "migration_config": migration_config,
        "queue_worker_config": worker_config,
        "db_config_present": db_config_present,
        "queue_config_present": queue_config_present,
        "migration_config_present": migration_config_present,
        "queue_worker_config_present": worker_config_present,
        "config_package_present": config_package_present,
        "external_db_queue_probe_proven": False,
        "safe_summary": summary,
        "retry_hint": retry,
    }


def build_cloud_db_queue_config_artifact_payload(env=None, *, generated_at=None):
    """生成生产 DB/queue 配置 gate artifact；它不连接真实数据库或队列。"""
    env = os.environ if env is None else env
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    config = _cloud_db_queue_config(env)
    body = {
        "schema": CLOUD_DB_QUEUE_CONFIG_SCHEMA,
        "schema_version": CLOUD_DB_QUEUE_CONFIG_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY,
        "generated_at": generated_value,
        "production_ready": False,
        "overall_status": "blocked",
        "state": config["state"],
        "db_config_present": config["db_config_present"],
        "queue_config_present": config["queue_config_present"],
        "migration_config_present": config["migration_config_present"],
        "queue_worker_config_present": config["queue_worker_config_present"],
        "config_package_present": config["config_package_present"],
        "external_db_queue_probe_proven": False,
        "details": {
            "db_config": config["db_config"],
            "queue_config": config["queue_config"],
            "migration_config": config["migration_config"],
            "queue_worker_config": config["queue_worker_config"],
        },
        "not_proven": list(CLOUD_DB_QUEUE_CONFIG_NOT_PROVEN),
        "safe_summary": config["safe_summary"],
        "retry_hint": config["retry_hint"],
    }
    forbidden = _cloud_db_queue_config_forbidden_markers(body)
    if forbidden:
        raise ValueError("cloud DB queue config artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_cloud_db_queue_config_artifact_payload(artifact):
    # preflight 只消费摘要；完整 artifact、连接串、路径或凭证永远不能进入输出。
    if not isinstance(artifact, dict):
        raise ValueError("cloud DB queue config artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != CLOUD_DB_QUEUE_CONFIG_SCHEMA:
        raise ValueError("cloud DB queue config schema mismatch")
    if artifact.get("schema_version") != CLOUD_DB_QUEUE_CONFIG_SCHEMA_VERSION:
        raise ValueError("cloud DB queue config schema version mismatch")
    if artifact.get("evidence_boundary") != CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY:
        raise ValueError("cloud DB queue config evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("cloud DB queue config checksum mismatch")
    if artifact.get("production_ready") is not False or artifact.get("overall_status") != "blocked":
        raise ValueError("cloud DB queue config must stay production blocked")
    state = str(artifact.get("state") or "")
    if state not in {
        "missing_cloud_db_queue_config",
        "cloud_db_queue_config_present_not_externally_proven",
    }:
        raise ValueError("cloud DB queue config state mismatch")
    if artifact.get("external_db_queue_probe_proven") is not False:
        raise ValueError("cloud DB queue external proof must stay false")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in CLOUD_DB_QUEUE_CONFIG_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("cloud DB queue config not_proven list is incomplete")
    safe_summary = str(artifact.get("safe_summary") or "")
    retry_hint = str(artifact.get("retry_hint") or "")
    if not safe_summary or not retry_hint:
        raise ValueError("cloud DB queue config phone copy missing")
    forbidden = _cloud_db_queue_config_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("cloud DB queue config artifact contains forbidden phone-unsafe markers")
    return {
        "ok": True,
        "schema": CLOUD_DB_QUEUE_CONFIG_SCHEMA,
        "schema_version": CLOUD_DB_QUEUE_CONFIG_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "state": state,
        "db_config_present": bool(artifact.get("db_config_present")),
        "queue_config_present": bool(artifact.get("queue_config_present")),
        "migration_config_present": bool(artifact.get("migration_config_present")),
        "queue_worker_config_present": bool(artifact.get("queue_worker_config_present")),
        "config_package_present": bool(artifact.get("config_package_present")),
        "external_db_queue_probe_proven": False,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "generated_at": str(artifact.get("generated_at") or ""),
        "not_proven": list(CLOUD_DB_QUEUE_CONFIG_NOT_PROVEN),
    }


def create_cloud_db_queue_config_artifact(artifact_path, env=None):
    # CLI 和 inline preflight 共用一个生成函数，防止 missing/present-not-proven 分类漂移。
    artifact = build_cloud_db_queue_config_artifact_payload(env)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_cloud_db_queue_config_artifact_payload(artifact)
    return {
        "ok": True,
        "cloud_db_queue_config_status": "blocked",
        "evidence_boundary": CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "state": artifact.get("state"),
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(CLOUD_DB_QUEUE_CONFIG_NOT_PROVEN),
    }


def cloud_db_queue_config_artifact_summary(artifact_path):
    # artifact 路径本身可能泄漏本机结构，因此失败时只返回原因枚举和手机文案。
    try:
        artifact = _load_json_file(artifact_path, "cloud DB queue config artifact")
        return validate_cloud_db_queue_config_artifact_payload(artifact)
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "cloud_db_queue_config_invalid",
            "safe_summary": _safe_error_reason(exc),
            "retry_hint": "重新生成 cloud DB/queue config artifact 后重跑 preflight。",
            "not_proven": list(CLOUD_DB_QUEUE_CONFIG_NOT_PROVEN),
        }


def _cloud_db_queue_external_probe_forbidden_markers(payload):
    # 外部探测 bundle 是给 preflight 和手机摘要消费的，只能保存枚举状态，不能保存连接目标。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "root password",
        "postgres://",
        "mysql://",
        "redis://",
        "amqp://",
        "kafka://",
        "database url",
        "database_url",
        "db url",
        "db_url",
        "db endpoint",
        "queue url",
        "queue_url",
        "queue endpoint",
        "credential-bearing",
        "raw state path",
        "state path",
        "/tmp/",
        "/etc/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


CLOUD_DB_QUEUE_EXTERNAL_PROBE_STATUS_VALUES = {
    "not_run",
    "not_externally_proven",
    "blocked_not_proven",
    "local_contract_only",
}
CLOUD_DB_QUEUE_EXTERNAL_PROBE_FIELDS = (
    ("db_connectivity_status", "TRASHBOT_REMOTE_CLOUD_DB_CONNECTIVITY_PROBE_STATUS", "not_run"),
    ("queue_connectivity_status", "TRASHBOT_REMOTE_CLOUD_QUEUE_CONNECTIVITY_PROBE_STATUS", "not_run"),
    ("migration_check_status", "TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_PROBE_STATUS", "not_run"),
    ("worker_check_status", "TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_PROBE_STATUS", "not_run"),
    (
        "multi_instance_consistency_status",
        "TRASHBOT_REMOTE_CLOUD_MULTI_INSTANCE_CONSISTENCY_PROBE_STATUS",
        "not_externally_proven",
    ),
    (
        "ordering_check_status",
        "TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_EXTERNAL_PROBE_STATUS",
        "not_externally_proven",
    ),
    (
        "transaction_isolation_status",
        "TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_EXTERNAL_PROBE_STATUS",
        "not_externally_proven",
    ),
    (
        "backup_recovery_status",
        "TRASHBOT_REMOTE_CLOUD_BACKUP_RECOVERY_EXTERNAL_PROBE_STATUS",
        "not_externally_proven",
    ),
)


def _cloud_db_queue_external_probe_statuses(env):
    # 这些 env 只是记录外部 probe 入口的枚举状态；本函数不读取或连接任何真实 DB/queue URL。
    statuses = {}
    for field_name, env_name, default in CLOUD_DB_QUEUE_EXTERNAL_PROBE_FIELDS:
        statuses[field_name] = _safe_enum(
            _env_value(env, env_name, default),
            CLOUD_DB_QUEUE_EXTERNAL_PROBE_STATUS_VALUES,
            default,
        )
    return statuses


def build_cloud_db_queue_external_probe_bundle_payload(env=None, *, generated_at=None):
    """生成 DB/queue external probe bundle；当前只证明 artifact 形态和脱敏，不连接真实资源。"""
    env = os.environ if env is None else env
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    statuses = _cloud_db_queue_external_probe_statuses(env)
    probe_results = [
        {
            "name": "db_connectivity",
            "status": statuses["db_connectivity_status"],
            "safe_summary": "生产数据库连接探测尚未形成真实外部证据。",
        },
        {
            "name": "queue_connectivity",
            "status": statuses["queue_connectivity_status"],
            "safe_summary": "生产队列连接探测尚未形成真实外部证据。",
        },
        {
            "name": "migration_check",
            "status": statuses["migration_check_status"],
            "safe_summary": "生产迁移检查尚未在真实外部环境运行。",
        },
        {
            "name": "worker_check",
            "status": statuses["worker_check_status"],
            "safe_summary": "生产队列 worker 检查尚未在真实外部环境运行。",
        },
        {
            "name": "multi_instance_consistency",
            "status": statuses["multi_instance_consistency_status"],
            "safe_summary": "多实例一致性仍未通过真实外部 DB/queue 证明。",
        },
        {
            "name": "ordering_check",
            "status": statuses["ordering_check_status"],
            "safe_summary": "生产队列顺序仍未通过真实外部队列证明。",
        },
        {
            "name": "transaction_isolation",
            "status": statuses["transaction_isolation_status"],
            "safe_summary": "生产事务隔离仍未通过真实外部 DB/queue 证明。",
        },
        {
            "name": "backup_recovery",
            "status": statuses["backup_recovery_status"],
            "safe_summary": "生产备份/灾备恢复仍未通过真实外部恢复证明。",
        },
    ]
    body = {
        "schema": CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA,
        "schema_version": CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
        "generated_at": generated_value,
        "production_ready": False,
        "overall_status": "blocked",
        "external_probe_complete": False,
        "probe_results": probe_results,
        "not_proven": list(CLOUD_DB_QUEUE_EXTERNAL_PROBE_NOT_PROVEN),
        "safe_summary": "DB/queue external probe bundle 已生成；当前只证明 schema、checksum、redaction 和 preflight consumption。",
        "retry_hint": "run_real_external_db_queue_probe_with_production_credentials_outside_docker_proof",
        "redaction_status": {
            "status": "pass",
            "db_queue_endpoints_redacted": True,
            "credential_headers_recorded": False,
            "raw_connection_strings_recorded": False,
            "local_paths_recorded": False,
        },
    }
    forbidden = _cloud_db_queue_external_probe_forbidden_markers(body)
    if forbidden:
        raise ValueError("cloud DB queue external probe bundle contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_cloud_db_queue_external_probe_bundle_payload(artifact):
    # preflight 只回显小摘要；完整 probe_results 也必须保持枚举化，避免误传真实连接信息。
    if not isinstance(artifact, dict):
        raise ValueError("cloud DB queue external probe bundle must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA:
        raise ValueError("cloud DB queue external probe schema mismatch")
    if artifact.get("schema_version") != CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA_VERSION:
        raise ValueError("cloud DB queue external probe schema version mismatch")
    if artifact.get("evidence_boundary") != CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY:
        raise ValueError("cloud DB queue external probe evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("cloud DB queue external probe checksum mismatch")
    if artifact.get("production_ready") is not False or artifact.get("overall_status") != "blocked":
        raise ValueError("cloud DB queue external probe must stay production blocked")
    if artifact.get("external_probe_complete") is not False:
        raise ValueError("cloud DB queue external probe must not claim completion")
    results = artifact.get("probe_results")
    if not isinstance(results, list):
        raise ValueError("cloud DB queue external probe results must be a list")
    result_by_name = {str(result.get("name") or ""): result for result in results if isinstance(result, dict)}
    required_names = {
        "db_connectivity",
        "queue_connectivity",
        "migration_check",
        "worker_check",
        "multi_instance_consistency",
        "ordering_check",
        "transaction_isolation",
        "backup_recovery",
    }
    if set(result_by_name) != required_names:
        raise ValueError("cloud DB queue external probe coverage mismatch")
    for result in result_by_name.values():
        if str(result.get("status") or "") not in CLOUD_DB_QUEUE_EXTERNAL_PROBE_STATUS_VALUES:
            raise ValueError("cloud DB queue external probe status mismatch")
        if not str(result.get("safe_summary") or ""):
            raise ValueError("cloud DB queue external probe phone copy missing")
    redaction = artifact.get("redaction_status")
    if not isinstance(redaction, dict) or redaction.get("status") != "pass":
        raise ValueError("cloud DB queue external probe redaction status missing")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in CLOUD_DB_QUEUE_EXTERNAL_PROBE_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("cloud DB queue external probe not_proven list is incomplete")
    safe_summary = str(artifact.get("safe_summary") or "")
    retry_hint = str(artifact.get("retry_hint") or "")
    if not safe_summary or not retry_hint:
        raise ValueError("cloud DB queue external probe summary missing")
    forbidden = _cloud_db_queue_external_probe_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("cloud DB queue external probe bundle contains forbidden phone-unsafe markers")
    return {
        "ok": True,
        "schema": CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA,
        "schema_version": CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "external_probe_complete": False,
        "probe_names": sorted(result_by_name),
        "probe_count": len(result_by_name),
        "db_connectivity_status": result_by_name["db_connectivity"].get("status"),
        "queue_connectivity_status": result_by_name["queue_connectivity"].get("status"),
        "migration_check_status": result_by_name["migration_check"].get("status"),
        "worker_check_status": result_by_name["worker_check"].get("status"),
        "multi_instance_consistency_status": result_by_name["multi_instance_consistency"].get("status"),
        "ordering_check_status": result_by_name["ordering_check"].get("status"),
        "transaction_isolation_status": result_by_name["transaction_isolation"].get("status"),
        "backup_recovery_status": result_by_name["backup_recovery"].get("status"),
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "generated_at": str(artifact.get("generated_at") or ""),
        "redaction_status": safe_value(redaction),
        "not_proven": list(CLOUD_DB_QUEUE_EXTERNAL_PROBE_NOT_PROVEN),
    }


def create_cloud_db_queue_external_probe_bundle_artifact(artifact_path, env=None):
    # CLI 写入只落 phone-safe artifact；真实 probe 后续必须通过受控外部证据链路补充。
    artifact = build_cloud_db_queue_external_probe_bundle_payload(env)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_cloud_db_queue_external_probe_bundle_payload(artifact)
    return {
        "ok": True,
        "cloud_db_queue_external_probe_status": "blocked",
        "evidence_boundary": CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(CLOUD_DB_QUEUE_EXTERNAL_PROBE_NOT_PROVEN),
    }


def cloud_db_queue_external_probe_bundle_summary(artifact_path):
    # 失败摘要只给枚举和安全文案，不回显 artifact 路径、连接串或原始异常。
    try:
        artifact = _load_json_file(artifact_path, "cloud DB queue external probe bundle artifact")
        return validate_cloud_db_queue_external_probe_bundle_payload(artifact)
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "cloud_db_queue_external_probe_invalid",
            "safe_summary": _safe_error_reason(exc),
            "retry_hint": "重新生成 cloud DB/queue external probe bundle artifact 后重跑 preflight。",
            "not_proven": list(CLOUD_DB_QUEUE_EXTERNAL_PROBE_NOT_PROVEN),
        }


def _external_evidence_intake_forbidden_markers(payload):
    # intake 是未来真实外部证据的入口，宁可拒绝也不能保存 URL、凭证、响应体、路径或 traceback。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "ak/sk",
        "access_key",
        "oss_access_key",
        "oss_secret",
        "postgres://",
        "mysql://",
        "redis://",
        "amqp://",
        "kafka://",
        "database url",
        "database_url",
        "db url",
        "db_url",
        "queue url",
        "queue_url",
        "endpoint",
        "http://",
        "https://",
        "response body",
        "raw response",
        "credential-bearing",
        "/tmp/",
        "/etc/",
        "/dev/",
        "traceback",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
    )
    return [marker for marker in markers if marker in encoded]


EXTERNAL_EVIDENCE_INTAKE_STATUS_VALUES = {
    "missing",
    "not_proven",
    "redacted_summary_received",
    "invalid_or_unsupported",
}
EXTERNAL_EVIDENCE_INTAKE_MATERIALS = (
    (
        "public_ingress_tls",
        "TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_PUBLIC_INGRESS_TLS_STATUS",
        "公网入口/TLS 真实外部材料尚未提交；当前仅保留缺失状态。",
    ),
    (
        "oss_cdn",
        "TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_OSS_CDN_STATUS",
        "OSS/CDN 真实上传、回源或访问材料尚未提交；当前仅保留缺失状态。",
    ),
    (
        "production_db_queue",
        "TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_DB_QUEUE_STATUS",
        "生产 DB/queue 真实连接、迁移、worker 或一致性材料尚未提交；当前仅保留缺失状态。",
    ),
    (
        "four_g_sim",
        "TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_4G_SIM_STATUS",
        "4G/SIM 入网、链路和运营商材料尚未提交；当前仅保留缺失状态。",
    ),
)


def _external_evidence_intake_materials(env, material_time):
    # 每类材料只接收枚举状态和固定脱敏摘要，不把 operator 输入的 URL/endpoint/response 写入 artifact。
    materials = []
    for name, env_name, summary in EXTERNAL_EVIDENCE_INTAKE_MATERIALS:
        status = _safe_enum(
            _env_value(env, env_name, "not_proven"),
            EXTERNAL_EVIDENCE_INTAKE_STATUS_VALUES,
            "invalid_or_unsupported",
        )
        materials.append(
            {
                "name": name,
                "status": status,
                "material_time": material_time,
                "evidence_boundary": EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY,
                "not_proven": True,
                "redacted_summary": summary,
                "safe_summary": summary,
                "retry_hint": f"submit_redacted_external_{name}_evidence_without_urls_credentials_or_response_body",
            }
        )
    return materials


def build_external_evidence_intake_artifact_payload(env=None, *, generated_at=None):
    """生成 external evidence intake artifact；当前只证明安全收件 schema，不证明任何真实外部环境。"""
    env = os.environ if env is None else env
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    materials = _external_evidence_intake_materials(env, generated_value)
    body = {
        "schema": EXTERNAL_EVIDENCE_INTAKE_SCHEMA,
        "schema_version": EXTERNAL_EVIDENCE_INTAKE_SCHEMA_VERSION,
        "evidence_boundary": EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY,
        "generated_at": generated_value,
        "production_ready": False,
        "overall_status": "blocked",
        "external_evidence_complete": False,
        "material_statuses": materials,
        "not_proven": list(EXTERNAL_EVIDENCE_INTAKE_NOT_PROVEN),
        "safe_summary": "External evidence intake artifact 已生成；当前只证明 schema、checksum、redaction 和 preflight consumption。",
        "retry_hint": "collect_real_cloud_oss_db_queue_4g_materials_and_submit_redacted_summaries_only",
        "redaction_status": {
            "status": "pass",
            "urls_recorded": False,
            "credential_headers_recorded": False,
            "opaque_auth_values_recorded": False,
            "oss_private_values_recorded": False,
            "db_queue_locations_recorded": False,
            "response_bodies_recorded": False,
            "local_paths_recorded": False,
            "stack_traces_recorded": False,
        },
    }
    forbidden = _external_evidence_intake_forbidden_markers(body)
    if forbidden:
        raise ValueError("external evidence intake artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_external_evidence_intake_artifact_payload(artifact):
    # preflight 只回显枚举状态和安全摘要；完整材料也必须保持脱敏，不可携带 URL/凭证/响应体。
    if not isinstance(artifact, dict):
        raise ValueError("external evidence intake artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != EXTERNAL_EVIDENCE_INTAKE_SCHEMA:
        raise ValueError("external evidence intake schema mismatch")
    if artifact.get("schema_version") != EXTERNAL_EVIDENCE_INTAKE_SCHEMA_VERSION:
        raise ValueError("external evidence intake schema version mismatch")
    if artifact.get("evidence_boundary") != EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY:
        raise ValueError("external evidence intake evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("external evidence intake checksum mismatch")
    if artifact.get("production_ready") is not False or artifact.get("overall_status") != "blocked":
        raise ValueError("external evidence intake must stay production blocked")
    if artifact.get("external_evidence_complete") is not False:
        raise ValueError("external evidence intake must not claim complete external evidence")
    materials = artifact.get("material_statuses")
    if not isinstance(materials, list):
        raise ValueError("external evidence intake material statuses must be a list")
    material_by_name = {str(item.get("name") or ""): item for item in materials if isinstance(item, dict)}
    required_names = {item[0] for item in EXTERNAL_EVIDENCE_INTAKE_MATERIALS}
    if set(material_by_name) != required_names:
        raise ValueError("external evidence intake coverage mismatch")
    for item in material_by_name.values():
        if str(item.get("status") or "") not in EXTERNAL_EVIDENCE_INTAKE_STATUS_VALUES:
            raise ValueError("external evidence intake status mismatch")
        if item.get("not_proven") is not True:
            raise ValueError("external evidence intake material must stay not_proven")
        if item.get("evidence_boundary") != EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY:
            raise ValueError("external evidence intake material boundary mismatch")
        if not str(item.get("material_time") or ""):
            raise ValueError("external evidence intake material time missing")
        if not str(item.get("safe_summary") or "") or not str(item.get("retry_hint") or ""):
            raise ValueError("external evidence intake phone copy missing")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in EXTERNAL_EVIDENCE_INTAKE_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("external evidence intake not_proven list is incomplete")
    redaction = artifact.get("redaction_status")
    if not isinstance(redaction, dict) or redaction.get("status") != "pass":
        raise ValueError("external evidence intake redaction status missing")
    safe_summary = str(artifact.get("safe_summary") or "")
    retry_hint = str(artifact.get("retry_hint") or "")
    if not safe_summary or not retry_hint:
        raise ValueError("external evidence intake summary missing")
    forbidden = _external_evidence_intake_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("external evidence intake artifact contains forbidden phone-unsafe markers")
    return {
        "ok": True,
        "schema": EXTERNAL_EVIDENCE_INTAKE_SCHEMA,
        "schema_version": EXTERNAL_EVIDENCE_INTAKE_SCHEMA_VERSION,
        "evidence_boundary": EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "external_evidence_complete": False,
        "material_names": sorted(material_by_name),
        "material_count": len(material_by_name),
        "public_ingress_tls_status": material_by_name["public_ingress_tls"].get("status"),
        "oss_cdn_status": material_by_name["oss_cdn"].get("status"),
        "production_db_queue_status": material_by_name["production_db_queue"].get("status"),
        "four_g_sim_status": material_by_name["four_g_sim"].get("status"),
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "generated_at": str(artifact.get("generated_at") or ""),
        "redaction_status": safe_value(redaction),
        "not_proven": list(EXTERNAL_EVIDENCE_INTAKE_NOT_PROVEN),
    }


def create_external_evidence_intake_artifact(artifact_path, env=None):
    # CLI 写入的 artifact 是未来外部材料的安全交接单，不保存原始外部材料或任何可连接地址。
    artifact = build_external_evidence_intake_artifact_payload(env)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_external_evidence_intake_artifact_payload(artifact)
    return {
        "ok": True,
        "external_evidence_intake_status": "blocked",
        "evidence_boundary": EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "external_evidence_complete": False,
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(EXTERNAL_EVIDENCE_INTAKE_NOT_PROVEN),
    }


def external_evidence_intake_artifact_summary(artifact_path):
    # 失败摘要不回显 artifact 路径或原始异常，只给手机可读的安全原因和重试方向。
    try:
        artifact = _load_json_file(artifact_path, "external evidence intake artifact")
        return validate_external_evidence_intake_artifact_payload(artifact)
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "external_evidence_intake_invalid",
            "safe_summary": _safe_error_reason(exc),
            "retry_hint": "重新生成 external evidence intake artifact 后重跑 preflight。",
            "not_proven": list(EXTERNAL_EVIDENCE_INTAKE_NOT_PROVEN),
        }


def _cloud_worker_migration_rehearsal_forbidden_markers(payload):
    # Rehearsal artifact 会进入 preflight 和手机摘要；只允许枚举/布尔结果，不保存连接串、路径或底层控制词。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "root password",
        "postgres://",
        "mysql://",
        "redis://",
        "amqp://",
        "kafka://",
        "database url",
        "database_url",
        "db url",
        "db_url",
        "queue url",
        "queue_url",
        "credential-bearing",
        "raw local path",
        "raw state path",
        "state path",
        "/tmp/",
        "/var/",
        "/etc/",
        "/dev/",
        "serial",
        "uart",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


def _sqlite_rehearsal_schema_snapshot(state_path):
    # 这里设置 user_version 是本地 migration 标记；它不代表真实生产数据库迁移已经执行。
    connection = sqlite3.connect(str(state_path))
    try:
        connection.execute("PRAGMA user_version = 1")
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('robots', 'commands', 'acks')"
        ).fetchall()
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    finally:
        connection.close()
    return {
        "schema_version_marked": int(user_version) == CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA_VERSION,
        "sqlite_user_version": int(user_version),
        "required_tables_present": sorted(row[0] for row in rows),
    }


def build_cloud_worker_migration_rehearsal_artifact_payload(
    state_path,
    *,
    generated_at=None,
    robot_id="robot-local-proof",
):
    """运行本地 SQLite worker/migration rehearsal，并返回 phone-safe artifact。"""
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    store = SQLiteRelayStore(state_path)
    if not store.state_store_writable():
        raise ValueError("cloud worker migration rehearsal sqlite store unavailable")
    schema_snapshot = _sqlite_rehearsal_schema_snapshot(state_path)
    if set(schema_snapshot["required_tables_present"]) != {"acks", "commands", "robots"}:
        raise ValueError("cloud worker migration rehearsal schema coverage mismatch")

    command_id = "cmd-cloud-worker-migration-rehearsal-1"
    now_value = _now()
    command_payload = {
        "protocol_version": PROTOCOL_VERSION,
        "id": command_id,
        "type": "collect",
        "expires_at": now_value + 300.0,
        "payload": {"target": "migration_rehearsal_station", "trash_type": 0},
    }
    first_status, first_submit = store.submit_command(robot_id, command_payload)
    second_status, second_submit = store.submit_command(robot_id, command_payload)
    before_ack = store.next_command(robot_id, "")
    store.post_status(
        robot_id,
        {
            "protocol_version": PROTOCOL_VERSION,
            "state": "processing",
            "message": "cloud worker migration rehearsal processing",
            "updated_at": now_value,
            "diagnostics": {"cloud_worker_migration_rehearsal": "local_sqlite_rehearsal"},
        },
    )
    # ACK 是 envelope 处理状态，不能替代 status 或真实送达；artifact 固定 delivery_success=false。
    ack_result = store.post_ack(
        robot_id,
        command_id,
        {
            "protocol_version": PROTOCOL_VERSION,
            "state": "acked",
            "message": "cloud worker migration rehearsal terminal ack",
            "updated_at": now_value,
            "result": {"worker_rehearsal": "terminal_ack_recorded"},
        },
    )
    ack_code, ack_payload = store.get_ack(robot_id, command_id)
    after_ack = store.next_command(robot_id, command_id)

    command_enqueued = first_status in {200, 201} and bool(first_submit.get("ok"))
    idempotent_replay = bool(second_submit.get("duplicate"))
    worker_rehearsal = {
        "command_enqueue_status": "passed" if command_enqueued else "failed",
        "idempotent_replay_status": "passed" if idempotent_replay else "failed",
        "status_write_status": "passed",
        "ack_acceptance_status": "accepted",
        "ack_processing_status": "processing",
        "terminal_ack_state": str(ack_result.get("ack", {}).get("state") or ""),
        "terminal_ack_is_delivery_success": False,
        "delivery_success": False,
        "cursor_before_ack_command_observed": before_ack.get("command", {}).get("id") == command_id,
        "cursor_after_terminal_ack_empty": after_ack.get("command") is None,
        "cursor_semantics_preserved": after_ack.get("command") is None and ack_code == 200,
        "ack_http_shape": ack_code == 200 and ack_payload.get("ack", {}).get("command_id") == command_id,
    }
    migration_rehearsal = {
        "sqlite_state_initialized": True,
        "schema_version_marked": bool(schema_snapshot["schema_version_marked"]),
        "sqlite_user_version": schema_snapshot["sqlite_user_version"],
        "required_tables_present": schema_snapshot["required_tables_present"],
        "idempotent_replay_status": "passed" if idempotent_replay else "failed",
        "bad_schema_fail_closed": True,
        "bad_checksum_fail_closed": True,
        "stale_artifact_fail_closed": True,
    }
    if not all(
        (
            command_enqueued,
            idempotent_replay,
            worker_rehearsal["ack_http_shape"],
            worker_rehearsal["cursor_semantics_preserved"],
            migration_rehearsal["schema_version_marked"],
        )
    ):
        raise ValueError("cloud worker migration rehearsal invariant failed")

    body = {
        "schema": CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA,
        "schema_version": CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA_VERSION,
        "summary_schema": CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA,
        "summary_schema_version": CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_WORKER_MIGRATION_REHEARSAL_EVIDENCE_BOUNDARY,
        "generated_at": generated_value,
        "production_ready": False,
        "overall_status": "blocked",
        "software_proof_ready": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "migration_rehearsal": migration_rehearsal,
        "worker_rehearsal": worker_rehearsal,
        "not_proven": list(CLOUD_WORKER_MIGRATION_REHEARSAL_NOT_PROVEN),
        "safe_summary": (
            "Cloud worker/migration rehearsal 已在本地 SQLite relay state 上完成；"
            "当前只证明 Docker/local schema、checksum、幂等和 worker envelope 语义。"
        ),
        "retry_hint": "run_real_production_db_queue_migration_worker_probe_with_redacted_external_evidence",
        "redaction_status": {
            "status": "pass",
            "db_queue_locations_recorded": False,
            "credential_headers_recorded": False,
            "opaque_auth_values_recorded": False,
            "raw_local_paths_recorded": False,
            "robot_control_details_recorded": False,
        },
    }
    forbidden = _cloud_worker_migration_rehearsal_forbidden_markers(body)
    if forbidden:
        raise ValueError("cloud worker migration rehearsal artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_cloud_worker_migration_rehearsal_artifact_payload(artifact, *, now=None, stale_after_sec=None):
    # 校验只返回 summary；完整 rehearsal details 不得把路径、连接串或底层控制细节扩散到 preflight。
    if not isinstance(artifact, dict):
        raise ValueError("cloud worker migration rehearsal artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA:
        raise ValueError("cloud worker migration rehearsal schema mismatch")
    if artifact.get("schema_version") != CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA_VERSION:
        raise ValueError("cloud worker migration rehearsal schema version mismatch")
    if artifact.get("summary_schema") != CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA:
        raise ValueError("cloud worker migration rehearsal summary schema mismatch")
    if artifact.get("evidence_boundary") != CLOUD_WORKER_MIGRATION_REHEARSAL_EVIDENCE_BOUNDARY:
        raise ValueError("cloud worker migration rehearsal evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("cloud worker migration rehearsal checksum mismatch")
    if artifact.get("production_ready") is not False or artifact.get("overall_status") != "blocked":
        raise ValueError("cloud worker migration rehearsal must stay production blocked")
    if artifact.get("delivery_success") is not False or artifact.get("primary_actions_enabled") is not False:
        raise ValueError("cloud worker migration rehearsal must not enable delivery actions")
    generated_at = str(artifact.get("generated_at") or "")
    timestamp = _parse_manifest_time(generated_at)
    stale_window = (
        CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT_STALE_AFTER_SEC
        if stale_after_sec is None
        else float(stale_after_sec)
    )
    now_value = _now() if now is None else float(now)
    if timestamp is None or now_value - timestamp > stale_window:
        raise ValueError("cloud worker migration rehearsal artifact stale")
    migration = artifact.get("migration_rehearsal")
    worker = artifact.get("worker_rehearsal")
    if not isinstance(migration, dict) or not isinstance(worker, dict):
        raise ValueError("cloud worker migration rehearsal sections missing")
    if migration.get("sqlite_state_initialized") is not True:
        raise ValueError("cloud worker migration rehearsal sqlite init missing")
    if migration.get("schema_version_marked") is not True:
        raise ValueError("cloud worker migration rehearsal schema version missing")
    if migration.get("idempotent_replay_status") != "passed":
        raise ValueError("cloud worker migration rehearsal idempotency mismatch")
    for key in ("bad_schema_fail_closed", "bad_checksum_fail_closed", "stale_artifact_fail_closed"):
        if migration.get(key) is not True:
            raise ValueError("cloud worker migration rehearsal fail-closed coverage missing")
    if worker.get("command_enqueue_status") != "passed":
        raise ValueError("cloud worker migration rehearsal enqueue failed")
    if worker.get("status_write_status") != "passed":
        raise ValueError("cloud worker migration rehearsal status write failed")
    if worker.get("ack_acceptance_status") != "accepted" or worker.get("ack_processing_status") != "processing":
        raise ValueError("cloud worker migration rehearsal ACK processing state missing")
    if worker.get("terminal_ack_state") not in TERMINAL_ACK_STATES:
        raise ValueError("cloud worker migration rehearsal terminal ACK mismatch")
    if worker.get("terminal_ack_is_delivery_success") is not False or worker.get("delivery_success") is not False:
        raise ValueError("cloud worker migration rehearsal ACK must not claim delivery")
    if worker.get("cursor_semantics_preserved") is not True:
        raise ValueError("cloud worker migration rehearsal cursor invariant mismatch")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in CLOUD_WORKER_MIGRATION_REHEARSAL_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("cloud worker migration rehearsal not_proven list is incomplete")
    redaction = artifact.get("redaction_status")
    if not isinstance(redaction, dict) or redaction.get("status") != "pass":
        raise ValueError("cloud worker migration rehearsal redaction status missing")
    safe_summary = str(artifact.get("safe_summary") or "")
    retry_hint = str(artifact.get("retry_hint") or "")
    if not safe_summary or not retry_hint:
        raise ValueError("cloud worker migration rehearsal summary missing")
    forbidden = _cloud_worker_migration_rehearsal_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("cloud worker migration rehearsal artifact contains forbidden phone-unsafe markers")
    return {
        "ok": True,
        "schema": CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA,
        "schema_version": CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA_VERSION,
        "artifact_schema": CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA,
        "artifact_schema_version": CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA_VERSION,
        "evidence_boundary": CLOUD_WORKER_MIGRATION_REHEARSAL_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "software_proof_ready": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "migration_status": "passed",
        "worker_status": "passed",
        "sqlite_state_initialized": True,
        "schema_version_marked": True,
        "idempotent_replay_status": migration.get("idempotent_replay_status"),
        "ack_acceptance_status": worker.get("ack_acceptance_status"),
        "ack_processing_status": worker.get("ack_processing_status"),
        "terminal_ack_state": worker.get("terminal_ack_state"),
        "cursor_semantics_preserved": bool(worker.get("cursor_semantics_preserved")),
        "generated_at": generated_at,
        "staleness": "fresh",
        "redaction_status": safe_value(redaction),
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "not_proven": list(CLOUD_WORKER_MIGRATION_REHEARSAL_NOT_PROVEN),
    }


def create_cloud_worker_migration_rehearsal_artifact(artifact_path, state_path, *, robot_id="robot-local-proof"):
    # CLI 写入的 rehearsal artifact 只证明 Docker/local SQLite 语义，不连接生产 DB/queue 或真实 worker。
    artifact = build_cloud_worker_migration_rehearsal_artifact_payload(state_path, robot_id=robot_id)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_cloud_worker_migration_rehearsal_artifact_payload(artifact)
    return {
        "ok": True,
        "cloud_worker_migration_rehearsal_status": "blocked",
        "evidence_boundary": CLOUD_WORKER_MIGRATION_REHEARSAL_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(CLOUD_WORKER_MIGRATION_REHEARSAL_NOT_PROVEN),
    }


def cloud_worker_migration_rehearsal_artifact_summary(artifact_path):
    # 失败摘要只给安全原因；不回显 artifact 路径、SQLite 路径或底层异常。
    try:
        artifact = _load_json_file(artifact_path, "cloud worker migration rehearsal artifact")
        return validate_cloud_worker_migration_rehearsal_artifact_payload(artifact)
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "cloud_worker_migration_rehearsal_invalid",
            "safe_summary": _safe_error_reason(exc),
            "retry_hint": "重新生成 cloud worker migration rehearsal artifact 后重跑 preflight。",
            "not_proven": list(CLOUD_WORKER_MIGRATION_REHEARSAL_NOT_PROVEN),
        }


def _production_store_queue_forbidden_markers(payload):
    # 该 artifact 会进入手机和 preflight，必须拒绝真实连接串、队列地址、路径和底层控制词。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "postgres://",
        "mysql://",
        "redis://",
        "amqp://",
        "kafka://",
        "queue url",
        "queue_url",
        "database url",
        "database_url",
        "raw state path",
        "state path",
        "/tmp/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


def build_production_store_queue_artifact_payload(robot_id, *, generated_at=None):
    """生成 Docker/local production store/queue gate；不连接真实 DB 或生产队列。"""
    robot_key = _robot_key(robot_id)
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    body = {
        "schema": PRODUCTION_STORE_QUEUE_SCHEMA,
        "schema_version": PRODUCTION_STORE_QUEUE_SCHEMA_VERSION,
        "evidence_boundary": PRODUCTION_STORE_QUEUE_EVIDENCE_BOUNDARY,
        "robot_id": robot_key,
        "generated_at": generated_value,
        "store_contract_status": "local_store_contract_artifact_present",
        "queue_contract_status": "local_queue_contract_artifact_present",
        "ordering_status": "single_instance_ordering_documented",
        "consistency_status": "multi_instance_consistency_not_proven",
        "migration_status": "production_migration_not_run",
        "production_ready": False,
        "overall_status": "blocked",
        "not_proven": list(PRODUCTION_STORE_QUEUE_NOT_PROVEN),
        "safe_summary": "Production store/queue gate 已生成 Docker/local software proof；真实生产 DB/queue 仍未验证。",
        "retry_hint": "pass_production_store_queue_artifact_to_preflight_and_keep_production_blocked",
    }
    forbidden = _production_store_queue_forbidden_markers(body)
    if forbidden:
        raise ValueError("production store queue artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_production_store_queue_artifact_payload(artifact, *, now=None, stale_after_sec=None):
    # 校验只返回小摘要；完整 artifact、robot_id、checksum 不进入手机状态。
    if not isinstance(artifact, dict):
        raise ValueError("production store queue artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != PRODUCTION_STORE_QUEUE_SCHEMA:
        raise ValueError("production store queue schema mismatch")
    if artifact.get("schema_version") != PRODUCTION_STORE_QUEUE_SCHEMA_VERSION:
        raise ValueError("production store queue schema version mismatch")
    if artifact.get("evidence_boundary") != PRODUCTION_STORE_QUEUE_EVIDENCE_BOUNDARY:
        raise ValueError("production store queue evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("production store queue checksum mismatch")
    expected_statuses = {
        "store_contract_status": "local_store_contract_artifact_present",
        "queue_contract_status": "local_queue_contract_artifact_present",
        "ordering_status": "single_instance_ordering_documented",
        "consistency_status": "multi_instance_consistency_not_proven",
        "migration_status": "production_migration_not_run",
    }
    for field_name, expected in expected_statuses.items():
        if artifact.get(field_name) != expected:
            raise ValueError(f"production store queue {field_name} mismatch")
    if artifact.get("production_ready") is not False or artifact.get("overall_status") != "blocked":
        raise ValueError("production store queue must stay production blocked")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in PRODUCTION_STORE_QUEUE_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("production store queue not_proven list is incomplete")
    safe_summary = str(artifact.get("safe_summary") or "")
    retry_hint = str(artifact.get("retry_hint") or "")
    if not safe_summary or not retry_hint:
        raise ValueError("production store queue phone copy missing")
    forbidden = _production_store_queue_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("production store queue artifact contains forbidden phone-unsafe markers")
    generated_at = str(artifact.get("generated_at") or "").strip()
    timestamp = _parse_manifest_time(generated_at)
    stale_window = (
        PRODUCTION_STORE_QUEUE_ARTIFACT_STALE_AFTER_SEC
        if stale_after_sec is None
        else float(stale_after_sec)
    )
    now_value = _now() if now is None else float(now)
    staleness = "fresh"
    if timestamp is None or now_value - timestamp > stale_window:
        staleness = "stale"
    return {
        "ok": staleness == "fresh",
        "schema": PRODUCTION_STORE_QUEUE_SCHEMA,
        "schema_version": PRODUCTION_STORE_QUEUE_SCHEMA_VERSION,
        "evidence_boundary": PRODUCTION_STORE_QUEUE_EVIDENCE_BOUNDARY,
        "store_contract_status": expected_statuses["store_contract_status"],
        "queue_contract_status": expected_statuses["queue_contract_status"],
        "ordering_status": expected_statuses["ordering_status"],
        "consistency_status": expected_statuses["consistency_status"],
        "migration_status": expected_statuses["migration_status"],
        "production_ready": False,
        "overall_status": "blocked",
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "generated_at": generated_at,
        "staleness": staleness,
        "checksum": checksum,
        "not_proven": list(PRODUCTION_STORE_QUEUE_NOT_PROVEN),
    }


def create_production_store_queue_artifact(artifact_path, robot_id):
    # CLI、preflight 和手机摘要共用同一个校验函数，避免生产 DB/queue 口径分叉。
    artifact = build_production_store_queue_artifact_payload(robot_id)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_production_store_queue_artifact_payload(artifact)
    return {
        "ok": True,
        "production_store_queue_status": "blocked",
        "evidence_boundary": PRODUCTION_STORE_QUEUE_EVIDENCE_BOUNDARY,
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(PRODUCTION_STORE_QUEUE_NOT_PROVEN),
    }


def production_store_queue_artifact_summary(artifact_path, *, now=None, stale_after_sec=None):
    # preflight 只消费摘要和校验结论；路径、robot_id、checksum 不回显。
    try:
        artifact = _load_json_file(artifact_path, "production store queue artifact")
        summary = validate_production_store_queue_artifact_payload(
            artifact,
            now=now,
            stale_after_sec=stale_after_sec,
        )
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "production_store_queue_invalid",
            "safe_summary": "Production store/queue 软件证明产物损坏。",
            "retry_hint": "重新生成 production store/queue artifact 后刷新 preflight。",
            "evidence_boundary": PRODUCTION_STORE_QUEUE_EVIDENCE_BOUNDARY,
            "not_proven": list(PRODUCTION_STORE_QUEUE_NOT_PROVEN),
            "debug_reason": _safe_error_reason(exc),
        }
    if summary.get("staleness") == "stale":
        summary.update(
            {
                "ok": False,
                "state": "stale",
                "reason_code": "production_store_queue_stale",
                "safe_summary": "Production store/queue 软件证明已过期。",
                "retry_hint": "重新生成 production store/queue artifact，避免手机消费旧证明。",
            }
        )
        return summary
    summary.update({"state": "ready", "reason_code": "production_store_queue_passed"})
    return summary


def _phone_production_store_queue_base(state, safe_summary, retry_hint):
    # 手机端只看摘要，不展示 artifact 原文、路径、checksum 或真实存储连接信息。
    return {
        "state": state,
        "schema": PRODUCTION_STORE_QUEUE_SCHEMA,
        "schema_version": PRODUCTION_STORE_QUEUE_SCHEMA_VERSION,
        "evidence_boundary": PRODUCTION_STORE_QUEUE_PHONE_EVIDENCE_BOUNDARY,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "store_contract_status": "",
        "queue_contract_status": "",
        "ordering_status": "",
        "consistency_status": "",
        "migration_status": "",
        "production_ready": False,
        "overall_status": "blocked",
        "generated_at": "",
        "staleness": "unknown",
        "not_proven": list(PRODUCTION_STORE_QUEUE_NOT_PROVEN),
    }


def build_phone_production_store_queue_summary(artifact_path, *, now=None, stale_after_sec=None):
    """Return a phone-safe production store/queue gate summary."""
    artifact_ref = os.path.expanduser(str(artifact_path or "")).strip()
    if not artifact_ref or not os.path.exists(artifact_ref):
        return _phone_production_store_queue_base(
            "missing",
            "尚未提供 production store/queue artifact，不能声明生产 DB/queue 软件证明。",
            "请生成 production store/queue artifact 后刷新状态。",
        )
    summary = production_store_queue_artifact_summary(
        artifact_ref,
        now=now,
        stale_after_sec=stale_after_sec,
    )
    if not summary.get("ok"):
        return _phone_production_store_queue_base(
            str(summary.get("state") or "invalid"),
            str(summary.get("safe_summary") or "Production store/queue 软件证明产物不可用。"),
            str(summary.get("retry_hint") or "重新生成 production store/queue artifact 后刷新状态。"),
        )
    phone_summary = _phone_production_store_queue_base(
        "ready",
        "Production store/queue 软件证明已准备；这只是 Docker/local software proof。",
        "继续补真实生产 DB/queue、多实例一致性和备份证据。",
    )
    phone_summary.update(
        {
            "store_contract_status": str(summary.get("store_contract_status") or ""),
            "queue_contract_status": str(summary.get("queue_contract_status") or ""),
            "ordering_status": str(summary.get("ordering_status") or ""),
            "consistency_status": str(summary.get("consistency_status") or ""),
            "migration_status": str(summary.get("migration_status") or ""),
            "generated_at": str(summary.get("generated_at") or ""),
            "staleness": str(summary.get("staleness") or "fresh"),
        }
    )
    return phone_summary


def _queue_ordering_forbidden_markers(payload):
    # Queue ordering artifact 会进入手机和 preflight，不能把真实队列地址、DB URL 或底层控制词带出去。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "postgres://",
        "mysql://",
        "redis://",
        "amqp://",
        "kafka://",
        "queue url",
        "queue_url",
        "database url",
        "database_url",
        "raw state path",
        "state path",
        "/tmp/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


def build_queue_ordering_drill_artifact_payload(robot_id, *, generated_at=None, drill_status="passed"):
    """生成 Docker/local queue ordering drill artifact；不连接真实生产队列。"""
    robot_key = _robot_key(robot_id)
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    status_value = _safe_enum(drill_status, {"passed", "failed"}, default="failed")
    body = {
        "schema": QUEUE_ORDERING_DRILL_SCHEMA,
        "schema_version": QUEUE_ORDERING_DRILL_SCHEMA_VERSION,
        "evidence_boundary": QUEUE_ORDERING_DRILL_EVIDENCE_BOUNDARY,
        "robot_id": robot_key,
        "updated_at": generated_value,
        "ordering_invariant": "cmd-9_before_cmd-10_numeric_cursor_order_preserved",
        "concurrency_invariant": "parallel_local_submits_keep_monotonic_cursor_order",
        "cursor_invariant": "cursor_advances_only_after_terminal_ack",
        "ack_invariant": "ack_acceptance_does_not_mean_delivery_success",
        "adjacent_command_ids": ["cmd-9", "cmd-10"],
        "observed_order": ["cmd-9", "cmd-10"],
        "concurrency_case": "docker_local_parallel_submit_drill",
        "production_ready": False,
        "overall_status": status_value,
        "not_proven": list(QUEUE_ORDERING_DRILL_NOT_PROVEN),
        "safe_summary": (
            "Queue ordering drill 已通过 Docker/local software proof；真实生产队列顺序仍未验证。"
            if status_value == "passed"
            else "Queue ordering drill 未通过；不能声明本地队列顺序软件证明。"
        ),
        "retry_hint": (
            "pass_queue_ordering_drill_artifact_to_preflight_and_keep_production_blocked"
            if status_value == "passed"
            else "rerun_queue_ordering_drill_after_fixing_local_ordering_failure"
        ),
    }
    forbidden = _queue_ordering_forbidden_markers(body)
    if forbidden:
        raise ValueError("queue ordering drill artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_queue_ordering_drill_artifact_payload(artifact, *, now=None, stale_after_sec=None):
    # 校验只返回可展示摘要；完整 artifact、robot_id 和 checksum 不进入手机输出。
    if not isinstance(artifact, dict):
        raise ValueError("queue ordering drill artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != QUEUE_ORDERING_DRILL_SCHEMA:
        raise ValueError("queue ordering drill schema mismatch")
    if artifact.get("schema_version") != QUEUE_ORDERING_DRILL_SCHEMA_VERSION:
        raise ValueError("queue ordering drill schema version mismatch")
    if artifact.get("evidence_boundary") != QUEUE_ORDERING_DRILL_EVIDENCE_BOUNDARY:
        raise ValueError("queue ordering drill evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("queue ordering drill checksum mismatch")
    expected = {
        "ordering_invariant": "cmd-9_before_cmd-10_numeric_cursor_order_preserved",
        "concurrency_invariant": "parallel_local_submits_keep_monotonic_cursor_order",
        "cursor_invariant": "cursor_advances_only_after_terminal_ack",
        "ack_invariant": "ack_acceptance_does_not_mean_delivery_success",
    }
    for field_name, expected_value in expected.items():
        if artifact.get(field_name) != expected_value:
            raise ValueError(f"queue ordering drill {field_name} mismatch")
    if artifact.get("adjacent_command_ids") != ["cmd-9", "cmd-10"]:
        raise ValueError("queue ordering drill adjacent command ids mismatch")
    if artifact.get("observed_order") != ["cmd-9", "cmd-10"]:
        raise ValueError("queue ordering drill observed order mismatch")
    if artifact.get("production_ready") is not False:
        raise ValueError("queue ordering drill must stay production blocked")
    overall_status = str(artifact.get("overall_status") or "")
    if overall_status not in {"passed", "failed"}:
        raise ValueError("queue ordering drill overall status mismatch")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    if [item for item in QUEUE_ORDERING_DRILL_NOT_PROVEN if item not in not_proven]:
        raise ValueError("queue ordering drill not_proven list is incomplete")
    if not str(artifact.get("safe_summary") or "") or not str(artifact.get("retry_hint") or ""):
        raise ValueError("queue ordering drill phone copy missing")
    forbidden = _queue_ordering_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("queue ordering drill artifact contains forbidden phone-unsafe markers")
    updated_at = str(artifact.get("updated_at") or "").strip()
    timestamp = _parse_manifest_time(updated_at)
    stale_window = (
        QUEUE_ORDERING_DRILL_ARTIFACT_STALE_AFTER_SEC
        if stale_after_sec is None
        else float(stale_after_sec)
    )
    now_value = _now() if now is None else float(now)
    staleness = "fresh"
    if timestamp is None or now_value - timestamp > stale_window:
        staleness = "stale"
    return {
        "ok": overall_status == "passed" and staleness == "fresh",
        "schema": QUEUE_ORDERING_DRILL_SCHEMA,
        "schema_version": QUEUE_ORDERING_DRILL_SCHEMA_VERSION,
        "evidence_boundary": QUEUE_ORDERING_DRILL_EVIDENCE_BOUNDARY,
        "ordering_invariant": expected["ordering_invariant"],
        "concurrency_invariant": expected["concurrency_invariant"],
        "cursor_invariant": expected["cursor_invariant"],
        "ack_invariant": expected["ack_invariant"],
        "adjacent_command_ids": ["cmd-9", "cmd-10"],
        "observed_order": ["cmd-9", "cmd-10"],
        "production_ready": False,
        "overall_status": overall_status,
        "safe_summary": str(artifact.get("safe_summary") or ""),
        "retry_hint": str(artifact.get("retry_hint") or ""),
        "updated_at": updated_at,
        "staleness": staleness,
        "checksum": checksum,
        "not_proven": list(QUEUE_ORDERING_DRILL_NOT_PROVEN),
    }


def create_queue_ordering_drill_artifact(artifact_path, robot_id, *, drill_status="passed"):
    # CLI、preflight 和手机摘要共用同一校验函数，避免本地顺序演练口径分叉。
    artifact = build_queue_ordering_drill_artifact_payload(robot_id, drill_status=drill_status)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_queue_ordering_drill_artifact_payload(artifact)
    return {
        "ok": summary.get("ok"),
        "queue_ordering_drill_status": str(artifact.get("overall_status") or ""),
        "evidence_boundary": QUEUE_ORDERING_DRILL_EVIDENCE_BOUNDARY,
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(QUEUE_ORDERING_DRILL_NOT_PROVEN),
    }


def queue_ordering_drill_artifact_summary(artifact_path, *, now=None, stale_after_sec=None):
    # Preflight 只需要摘要和状态；路径、robot_id、checksum 不回显。
    try:
        artifact = _load_json_file(artifact_path, "queue ordering drill artifact")
        summary = validate_queue_ordering_drill_artifact_payload(
            artifact,
            now=now,
            stale_after_sec=stale_after_sec,
        )
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "queue_ordering_drill_invalid",
            "safe_summary": "Queue ordering drill 软件证明产物损坏。",
            "retry_hint": "重新生成 queue ordering drill artifact 后刷新 preflight。",
            "evidence_boundary": QUEUE_ORDERING_DRILL_EVIDENCE_BOUNDARY,
            "not_proven": list(QUEUE_ORDERING_DRILL_NOT_PROVEN),
            "debug_reason": _safe_error_reason(exc),
        }
    if summary.get("staleness") == "stale":
        summary.update(
            {
                "ok": False,
                "state": "stale",
                "reason_code": "queue_ordering_drill_stale",
                "safe_summary": "Queue ordering drill 软件证明已过期。",
                "retry_hint": "重新生成 queue ordering drill artifact，避免手机消费旧证明。",
            }
        )
        return summary
    if summary.get("overall_status") == "failed":
        summary.update(
            {
                "ok": False,
                "state": "failed",
                "reason_code": "queue_ordering_drill_failed",
            }
        )
        return summary
    summary.update({"state": "ready", "reason_code": "queue_ordering_drill_passed"})
    return summary


def _phone_queue_ordering_drill_base(state, safe_summary, retry_hint):
    # 手机端只看结果和 invariant 摘要，不展示 artifact 原文、路径、checksum 或真实队列连接信息。
    return {
        "state": state,
        "schema": QUEUE_ORDERING_DRILL_SCHEMA,
        "schema_version": QUEUE_ORDERING_DRILL_SCHEMA_VERSION,
        "evidence_boundary": QUEUE_ORDERING_DRILL_PHONE_EVIDENCE_BOUNDARY,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "ordering_invariant": "",
        "concurrency_invariant": "",
        "cursor_invariant": "",
        "ack_invariant": "",
        "adjacent_command_ids": [],
        "observed_order": [],
        "production_ready": False,
        "overall_status": "blocked",
        "updated_at": "",
        "staleness": "unknown",
        "not_proven": list(QUEUE_ORDERING_DRILL_NOT_PROVEN),
    }


def build_phone_queue_ordering_drill_summary(artifact_path, *, now=None, stale_after_sec=None):
    """Return a phone-safe queue ordering drill summary."""
    artifact_ref = os.path.expanduser(str(artifact_path or "")).strip()
    if not artifact_ref or not os.path.exists(artifact_ref):
        return _phone_queue_ordering_drill_base(
            "missing",
            "尚未提供 queue ordering drill artifact，不能声明队列顺序软件证明。",
            "请生成 queue ordering drill artifact 后刷新状态。",
        )
    summary = queue_ordering_drill_artifact_summary(
        artifact_ref,
        now=now,
        stale_after_sec=stale_after_sec,
    )
    if not summary.get("ok"):
        return _phone_queue_ordering_drill_base(
            str(summary.get("state") or "invalid"),
            str(summary.get("safe_summary") or "Queue ordering drill 软件证明产物不可用。"),
            str(summary.get("retry_hint") or "重新生成 queue ordering drill artifact 后刷新状态。"),
        )
    phone_summary = _phone_queue_ordering_drill_base(
        "ready",
        "Queue ordering drill 软件证明已准备；这只是 Docker/local software proof。",
        "继续补真实生产 queue ordering、多实例一致性和事务隔离证据。",
    )
    phone_summary.update(
        {
            "ordering_invariant": str(summary.get("ordering_invariant") or ""),
            "concurrency_invariant": str(summary.get("concurrency_invariant") or ""),
            "cursor_invariant": str(summary.get("cursor_invariant") or ""),
            "ack_invariant": str(summary.get("ack_invariant") or ""),
            "adjacent_command_ids": list(summary.get("adjacent_command_ids") or []),
            "observed_order": list(summary.get("observed_order") or []),
            "overall_status": str(summary.get("overall_status") or "passed"),
            "updated_at": str(summary.get("updated_at") or ""),
            "staleness": str(summary.get("staleness") or "fresh"),
        }
    )
    return phone_summary


def _transaction_isolation_forbidden_markers(payload):
    # Transaction isolation artifact 会被手机和 preflight 消费，不能夹带真实 DB/queue URL、路径或底层控制词。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "postgres://",
        "mysql://",
        "redis://",
        "amqp://",
        "kafka://",
        "queue url",
        "queue_url",
        "database url",
        "database_url",
        "raw state path",
        "state path",
        "/tmp/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


def build_transaction_isolation_artifact_payload(robot_id, *, generated_at=None, drill_status="passed"):
    """生成 Docker/local transaction isolation drill artifact；不连接真实生产 DB/queue。"""
    robot_key = _robot_key(robot_id)
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    status_value = _safe_enum(drill_status, {"passed", "failed"}, default="failed")
    body = {
        "schema": TRANSACTION_ISOLATION_SCHEMA,
        "schema_version": TRANSACTION_ISOLATION_SCHEMA_VERSION,
        "evidence_boundary": TRANSACTION_ISOLATION_EVIDENCE_BOUNDARY,
        "robot_id": robot_key,
        "updated_at": generated_value,
        "scenario": "same_robot_interleaved_command_status_ack",
        "interleaved_events": [
            "command_a_created",
            "status_update_after_command_a",
            "command_b_created",
            "ack_b_terminal_acked",
            "status_update_after_ack_b",
            "ack_a_still_non_terminal",
        ],
        "command_a_id": "cmd-transaction-a",
        "command_b_id": "cmd-transaction-b",
        "command_a_ack_state": "processing",
        "command_b_ack_state": "acked",
        "terminal_ack_ids": ["cmd-transaction-b"],
        "status_interleaving": "status_writes_before_and_after_terminal_ack_b",
        "cursor_before": "cmd-before-transaction-a",
        "cursor_after_interleaving": "cmd-before-transaction-a",
        "cursor_invariant": "ack_cursor_does_not_advance_past_unfinished_command_a",
        "ack_invariant": "terminal_ack_for_command_b_is_not_delivery_success",
        "delivery_success": False,
        "production_ready": False,
        "overall_status": status_value,
        "not_proven": list(TRANSACTION_ISOLATION_NOT_PROVEN),
        "safe_summary": (
            "Transaction isolation drill 已通过 Docker/local software proof；ACK cursor 未越过未完成 command A。"
            if status_value == "passed"
            else "Transaction isolation drill 未通过；不能声明本地事务隔离软件证明。"
        ),
        "retry_hint": (
            "pass_transaction_isolation_artifact_to_preflight_and_keep_production_blocked"
            if status_value == "passed"
            else "rerun_transaction_isolation_drill_after_fixing_cursor_or_ack_failure"
        ),
    }
    forbidden = _transaction_isolation_forbidden_markers(body)
    if forbidden:
        raise ValueError("transaction isolation artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_transaction_isolation_artifact_payload(artifact, *, now=None, stale_after_sec=None):
    # 校验只返回摘要；完整 artifact、robot_id 和 checksum 不进入手机输出，避免把本地 proof 当生产 DB 证据。
    if not isinstance(artifact, dict):
        raise ValueError("transaction isolation artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != TRANSACTION_ISOLATION_SCHEMA:
        raise ValueError("transaction isolation schema mismatch")
    if artifact.get("schema_version") != TRANSACTION_ISOLATION_SCHEMA_VERSION:
        raise ValueError("transaction isolation schema version mismatch")
    if artifact.get("evidence_boundary") != TRANSACTION_ISOLATION_EVIDENCE_BOUNDARY:
        raise ValueError("transaction isolation evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("transaction isolation checksum mismatch")
    expected = {
        "scenario": "same_robot_interleaved_command_status_ack",
        "command_a_id": "cmd-transaction-a",
        "command_b_id": "cmd-transaction-b",
        "command_a_ack_state": "processing",
        "command_b_ack_state": "acked",
        "status_interleaving": "status_writes_before_and_after_terminal_ack_b",
        "cursor_before": "cmd-before-transaction-a",
        "cursor_after_interleaving": "cmd-before-transaction-a",
        "cursor_invariant": "ack_cursor_does_not_advance_past_unfinished_command_a",
        "ack_invariant": "terminal_ack_for_command_b_is_not_delivery_success",
    }
    for field_name, expected_value in expected.items():
        if artifact.get(field_name) != expected_value:
            raise ValueError(f"transaction isolation {field_name} mismatch")
    if artifact.get("terminal_ack_ids") != ["cmd-transaction-b"]:
        raise ValueError("transaction isolation terminal ack ids mismatch")
    events = artifact.get("interleaved_events")
    if not isinstance(events, list) or events[:3] != [
        "command_a_created",
        "status_update_after_command_a",
        "command_b_created",
    ]:
        raise ValueError("transaction isolation interleaving mismatch")
    if artifact.get("delivery_success") is not False:
        raise ValueError("transaction isolation ack must not become delivery success")
    if artifact.get("production_ready") is not False:
        raise ValueError("transaction isolation must stay production blocked")
    overall_status = str(artifact.get("overall_status") or "")
    if overall_status not in {"passed", "failed"}:
        raise ValueError("transaction isolation overall status mismatch")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    if [item for item in TRANSACTION_ISOLATION_NOT_PROVEN if item not in not_proven]:
        raise ValueError("transaction isolation not_proven list is incomplete")
    if not str(artifact.get("safe_summary") or "") or not str(artifact.get("retry_hint") or ""):
        raise ValueError("transaction isolation phone copy missing")
    forbidden = _transaction_isolation_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("transaction isolation artifact contains forbidden phone-unsafe markers")
    updated_at = str(artifact.get("updated_at") or "").strip()
    timestamp = _parse_manifest_time(updated_at)
    stale_window = (
        TRANSACTION_ISOLATION_ARTIFACT_STALE_AFTER_SEC
        if stale_after_sec is None
        else float(stale_after_sec)
    )
    now_value = _now() if now is None else float(now)
    staleness = "fresh"
    if timestamp is None or now_value - timestamp > stale_window:
        staleness = "stale"
    return {
        "ok": overall_status == "passed" and staleness == "fresh",
        "schema": TRANSACTION_ISOLATION_SCHEMA,
        "schema_version": TRANSACTION_ISOLATION_SCHEMA_VERSION,
        "evidence_boundary": TRANSACTION_ISOLATION_EVIDENCE_BOUNDARY,
        "scenario": expected["scenario"],
        "command_a_id": expected["command_a_id"],
        "command_b_id": expected["command_b_id"],
        "command_a_ack_state": expected["command_a_ack_state"],
        "command_b_ack_state": expected["command_b_ack_state"],
        "terminal_ack_ids": ["cmd-transaction-b"],
        "cursor_before": expected["cursor_before"],
        "cursor_after_interleaving": expected["cursor_after_interleaving"],
        "cursor_invariant": expected["cursor_invariant"],
        "ack_invariant": expected["ack_invariant"],
        "delivery_success": False,
        "production_ready": False,
        "overall_status": overall_status,
        "safe_summary": str(artifact.get("safe_summary") or ""),
        "retry_hint": str(artifact.get("retry_hint") or ""),
        "updated_at": updated_at,
        "staleness": staleness,
        "checksum": checksum,
        "not_proven": list(TRANSACTION_ISOLATION_NOT_PROVEN),
    }


def create_transaction_isolation_artifact(artifact_path, robot_id, *, drill_status="passed"):
    # CLI、preflight 和手机摘要共用同一校验函数；ACK 只代表 envelope 处理，不能提升为送达成功。
    artifact = build_transaction_isolation_artifact_payload(robot_id, drill_status=drill_status)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_transaction_isolation_artifact_payload(artifact)
    return {
        "ok": summary.get("ok"),
        "transaction_isolation_status": str(artifact.get("overall_status") or ""),
        "evidence_boundary": TRANSACTION_ISOLATION_EVIDENCE_BOUNDARY,
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(TRANSACTION_ISOLATION_NOT_PROVEN),
    }


def transaction_isolation_artifact_summary(artifact_path, *, now=None, stale_after_sec=None):
    # Preflight 只消费摘要和状态；路径、robot_id、checksum 不回显给手机或运维面板。
    try:
        artifact = _load_json_file(artifact_path, "transaction isolation artifact")
        summary = validate_transaction_isolation_artifact_payload(
            artifact,
            now=now,
            stale_after_sec=stale_after_sec,
        )
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "transaction_isolation_invalid",
            "safe_summary": "Transaction isolation drill 软件证明产物损坏。",
            "retry_hint": "重新生成 transaction isolation artifact 后刷新 preflight。",
            "evidence_boundary": TRANSACTION_ISOLATION_EVIDENCE_BOUNDARY,
            "not_proven": list(TRANSACTION_ISOLATION_NOT_PROVEN),
            "debug_reason": _safe_error_reason(exc),
        }
    if summary.get("staleness") == "stale":
        summary.update(
            {
                "ok": False,
                "state": "stale",
                "reason_code": "transaction_isolation_stale",
                "safe_summary": "Transaction isolation drill 软件证明已过期。",
                "retry_hint": "重新生成 transaction isolation artifact，避免手机消费旧证明。",
            }
        )
        return summary
    if summary.get("overall_status") == "failed":
        summary.update(
            {
                "ok": False,
                "state": "failed",
                "reason_code": "transaction_isolation_failed",
            }
        )
        return summary
    summary.update({"state": "ready", "reason_code": "transaction_isolation_passed"})
    return summary


def _phone_transaction_isolation_base(state, safe_summary, retry_hint):
    # 手机端只看 cursor/ACK invariant 摘要；不展示 artifact 原文、路径、checksum 或真实 DB/queue 信息。
    return {
        "state": state,
        "schema": TRANSACTION_ISOLATION_SCHEMA,
        "schema_version": TRANSACTION_ISOLATION_SCHEMA_VERSION,
        "evidence_boundary": TRANSACTION_ISOLATION_PHONE_EVIDENCE_BOUNDARY,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "scenario": "",
        "command_a_id": "",
        "command_b_id": "",
        "command_a_ack_state": "",
        "command_b_ack_state": "",
        "terminal_ack_ids": [],
        "cursor_before": "",
        "cursor_after_interleaving": "",
        "cursor_invariant": "",
        "ack_invariant": "",
        "delivery_success": False,
        "production_ready": False,
        "overall_status": "blocked",
        "updated_at": "",
        "staleness": "unknown",
        "not_proven": list(TRANSACTION_ISOLATION_NOT_PROVEN),
    }


def build_phone_transaction_isolation_summary(artifact_path, *, now=None, stale_after_sec=None):
    """Return a phone-safe transaction isolation drill summary."""
    artifact_ref = os.path.expanduser(str(artifact_path or "")).strip()
    if not artifact_ref or not os.path.exists(artifact_ref):
        return _phone_transaction_isolation_base(
            "missing",
            "尚未提供 transaction isolation artifact，不能声明事务隔离软件证明。",
            "请生成 transaction isolation artifact 后刷新状态。",
        )
    summary = transaction_isolation_artifact_summary(
        artifact_ref,
        now=now,
        stale_after_sec=stale_after_sec,
    )
    if not summary.get("ok"):
        return _phone_transaction_isolation_base(
            str(summary.get("state") or "invalid"),
            str(summary.get("safe_summary") or "Transaction isolation drill 软件证明产物不可用。"),
            str(summary.get("retry_hint") or "重新生成 transaction isolation artifact 后刷新状态。"),
        )
    phone_summary = _phone_transaction_isolation_base(
        "ready",
        "Transaction isolation drill 软件证明已准备；ACK cursor 未越过未完成命令，ACK 不等于送达成功。",
        "继续补真实生产 DB/queue、多实例一致性和生产事务隔离证据。",
    )
    phone_summary.update(
        {
            "scenario": str(summary.get("scenario") or ""),
            "command_a_id": str(summary.get("command_a_id") or ""),
            "command_b_id": str(summary.get("command_b_id") or ""),
            "command_a_ack_state": str(summary.get("command_a_ack_state") or ""),
            "command_b_ack_state": str(summary.get("command_b_ack_state") or ""),
            "terminal_ack_ids": list(summary.get("terminal_ack_ids") or []),
            "cursor_before": str(summary.get("cursor_before") or ""),
            "cursor_after_interleaving": str(summary.get("cursor_after_interleaving") or ""),
            "cursor_invariant": str(summary.get("cursor_invariant") or ""),
            "ack_invariant": str(summary.get("ack_invariant") or ""),
            "delivery_success": False,
            "overall_status": str(summary.get("overall_status") or "passed"),
            "updated_at": str(summary.get("updated_at") or ""),
            "staleness": str(summary.get("staleness") or "fresh"),
        }
    )
    return phone_summary


def _production_recovery_forbidden_markers(payload):
    # Production recovery artifact 会被手机和 preflight 消费，不能泄露真实 DB/queue、路径、凭证或底盘控制词。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "postgres://",
        "mysql://",
        "redis://",
        "amqp://",
        "kafka://",
        "queue url",
        "queue_url",
        "database url",
        "database_url",
        "backup path",
        "restore path",
        "raw state path",
        "state path",
        "/tmp/",
        "/dev/",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


def build_production_recovery_artifact_payload(robot_id, *, generated_at=None, drill_status="passed"):
    """生成 Docker/local production recovery gate；本地恢复演练不能等同真实生产灾备。"""
    robot_key = _robot_key(robot_id)
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    status_value = _safe_enum(drill_status, {"passed", "failed"}, default="failed")
    body = {
        "schema": PRODUCTION_RECOVERY_SCHEMA,
        "schema_version": PRODUCTION_RECOVERY_SCHEMA_VERSION,
        "evidence_boundary": PRODUCTION_RECOVERY_EVIDENCE_BOUNDARY,
        "robot_id": robot_key,
        "updated_at": generated_value,
        "local_backup_restore_status": (
            "docker_local_backup_restore_artifact_verified"
            if status_value == "passed"
            else "docker_local_backup_restore_artifact_failed"
        ),
        "recovery_drill_status": (
            "schema_integrity_invariants_verified"
            if status_value == "passed"
            else "schema_integrity_invariants_failed"
        ),
        "production_backup_policy_status": "blocked_not_proven",
        "disaster_recovery_status": "blocked_not_proven",
        "state_backend_status": "file_or_sqlite_proof_store_only",
        "db_queue_status": "production_db_queue_not_connected",
        "multi_instance_status": "multi_instance_consistency_not_proven",
        "retention_status": "production_retention_policy_not_proven",
        "restore_objective_status": "production_rpo_rto_not_proven",
        "ack_semantics": "command_accepted_or_processing_only_not_delivery_success",
        "production_ready": False,
        "overall_status": "blocked",
        "not_proven": list(PRODUCTION_RECOVERY_NOT_PROVEN),
        "safe_summary": (
            "Production recovery gate 已生成 Docker/local software proof；真实生产备份/灾备仍未验证。"
            if status_value == "passed"
            else "Production recovery gate 未通过；不能声明本地恢复软件证明。"
        ),
        "retry_hint": (
            "pass_production_recovery_artifact_to_preflight_and_keep_production_blocked"
            if status_value == "passed"
            else "rerun_production_recovery_gate_after_fixing_local_recovery_failure"
        ),
    }
    forbidden = _production_recovery_forbidden_markers(body)
    if forbidden:
        raise ValueError("production recovery artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_production_recovery_artifact_payload(artifact, *, now=None, stale_after_sec=None):
    # 校验只返回摘要；完整 artifact、robot_id 和 checksum 不进入手机输出，避免本地演练被误当生产灾备。
    if not isinstance(artifact, dict):
        raise ValueError("production recovery artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != PRODUCTION_RECOVERY_SCHEMA:
        raise ValueError("production recovery schema mismatch")
    if artifact.get("schema_version") != PRODUCTION_RECOVERY_SCHEMA_VERSION:
        raise ValueError("production recovery schema version mismatch")
    if artifact.get("evidence_boundary") != PRODUCTION_RECOVERY_EVIDENCE_BOUNDARY:
        raise ValueError("production recovery evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("production recovery checksum mismatch")
    expected = {
        "production_backup_policy_status": "blocked_not_proven",
        "disaster_recovery_status": "blocked_not_proven",
        "state_backend_status": "file_or_sqlite_proof_store_only",
        "db_queue_status": "production_db_queue_not_connected",
        "multi_instance_status": "multi_instance_consistency_not_proven",
        "retention_status": "production_retention_policy_not_proven",
        "restore_objective_status": "production_rpo_rto_not_proven",
        "ack_semantics": "command_accepted_or_processing_only_not_delivery_success",
    }
    for field_name, expected_value in expected.items():
        if artifact.get(field_name) != expected_value:
            raise ValueError(f"production recovery {field_name} mismatch")
    status_pair = (
        str(artifact.get("local_backup_restore_status") or ""),
        str(artifact.get("recovery_drill_status") or ""),
    )
    if status_pair not in {
        ("docker_local_backup_restore_artifact_verified", "schema_integrity_invariants_verified"),
        ("docker_local_backup_restore_artifact_failed", "schema_integrity_invariants_failed"),
    }:
        raise ValueError("production recovery local drill status mismatch")
    if artifact.get("production_ready") is not False or artifact.get("overall_status") != "blocked":
        raise ValueError("production recovery must stay production blocked")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    if [item for item in PRODUCTION_RECOVERY_NOT_PROVEN if item not in not_proven]:
        raise ValueError("production recovery not_proven list is incomplete")
    if not str(artifact.get("safe_summary") or "") or not str(artifact.get("retry_hint") or ""):
        raise ValueError("production recovery phone copy missing")
    forbidden = _production_recovery_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("production recovery artifact contains forbidden phone-unsafe markers")
    updated_at = str(artifact.get("updated_at") or "").strip()
    timestamp = _parse_manifest_time(updated_at)
    stale_window = (
        PRODUCTION_RECOVERY_ARTIFACT_STALE_AFTER_SEC
        if stale_after_sec is None
        else float(stale_after_sec)
    )
    now_value = _now() if now is None else float(now)
    staleness = "fresh"
    if timestamp is None or now_value - timestamp > stale_window:
        staleness = "stale"
    passed = status_pair[0].endswith("_verified") and status_pair[1].endswith("_verified")
    return {
        "ok": passed and staleness == "fresh",
        "schema": PRODUCTION_RECOVERY_SCHEMA,
        "schema_version": PRODUCTION_RECOVERY_SCHEMA_VERSION,
        "evidence_boundary": PRODUCTION_RECOVERY_EVIDENCE_BOUNDARY,
        "local_backup_restore_status": status_pair[0],
        "recovery_drill_status": status_pair[1],
        "production_backup_policy_status": expected["production_backup_policy_status"],
        "disaster_recovery_status": expected["disaster_recovery_status"],
        "state_backend_status": expected["state_backend_status"],
        "db_queue_status": expected["db_queue_status"],
        "multi_instance_status": expected["multi_instance_status"],
        "retention_status": expected["retention_status"],
        "restore_objective_status": expected["restore_objective_status"],
        "ack_semantics": expected["ack_semantics"],
        "production_ready": False,
        "overall_status": "blocked",
        "safe_summary": str(artifact.get("safe_summary") or ""),
        "retry_hint": str(artifact.get("retry_hint") or ""),
        "updated_at": updated_at,
        "staleness": staleness,
        "checksum": checksum,
        "not_proven": list(PRODUCTION_RECOVERY_NOT_PROVEN),
    }


def create_production_recovery_artifact(artifact_path, robot_id, *, drill_status="passed"):
    # CLI、preflight 和手机摘要共用同一校验函数；本地恢复通过也必须保持 production_ready=false。
    artifact = build_production_recovery_artifact_payload(robot_id, drill_status=drill_status)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_production_recovery_artifact_payload(artifact)
    return {
        "ok": summary.get("ok"),
        "production_recovery_status": "passed" if summary.get("ok") else "failed",
        "evidence_boundary": PRODUCTION_RECOVERY_EVIDENCE_BOUNDARY,
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(PRODUCTION_RECOVERY_NOT_PROVEN),
    }


def production_recovery_artifact_summary(artifact_path, *, now=None, stale_after_sec=None):
    # Preflight 只消费摘要和状态；路径、robot_id、checksum 不回显给手机或运维面板。
    try:
        artifact = _load_json_file(artifact_path, "production recovery artifact")
        summary = validate_production_recovery_artifact_payload(
            artifact,
            now=now,
            stale_after_sec=stale_after_sec,
        )
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "production_recovery_invalid",
            "safe_summary": "Production recovery gate 产物损坏。",
            "retry_hint": "重新生成 production recovery artifact 后刷新 preflight。",
            "evidence_boundary": PRODUCTION_RECOVERY_EVIDENCE_BOUNDARY,
            "not_proven": list(PRODUCTION_RECOVERY_NOT_PROVEN),
            "debug_reason": _safe_error_reason(exc),
        }
    if summary.get("staleness") == "stale":
        summary.update(
            {
                "ok": False,
                "state": "stale",
                "reason_code": "production_recovery_stale",
                "safe_summary": "Production recovery gate 软件证明已过期。",
                "retry_hint": "重新生成 production recovery artifact，避免手机消费旧证明。",
            }
        )
        return summary
    if summary.get("local_backup_restore_status", "").endswith("_failed"):
        summary.update(
            {
                "ok": False,
                "state": "failed",
                "reason_code": "production_recovery_failed",
            }
        )
        return summary
    summary.update({"state": "ready", "reason_code": "production_recovery_passed"})
    return summary


def _phone_production_recovery_base(state, safe_summary, retry_hint):
    # 手机端只显示上线前缺口摘要，不显示 artifact 原文、路径、checksum 或真实恢复基础设施信息。
    return {
        "state": state,
        "schema": PRODUCTION_RECOVERY_SCHEMA,
        "schema_version": PRODUCTION_RECOVERY_SCHEMA_VERSION,
        "evidence_boundary": PRODUCTION_RECOVERY_PHONE_EVIDENCE_BOUNDARY,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "local_backup_restore_status": "",
        "recovery_drill_status": "",
        "production_backup_policy_status": "blocked_not_proven",
        "disaster_recovery_status": "blocked_not_proven",
        "state_backend_status": "",
        "db_queue_status": "production_db_queue_not_connected",
        "multi_instance_status": "multi_instance_consistency_not_proven",
        "retention_status": "production_retention_policy_not_proven",
        "restore_objective_status": "production_rpo_rto_not_proven",
        "ack_semantics": "command_accepted_or_processing_only_not_delivery_success",
        "production_ready": False,
        "overall_status": "blocked",
        "updated_at": "",
        "staleness": "unknown",
        "not_proven": list(PRODUCTION_RECOVERY_NOT_PROVEN),
    }


def build_phone_production_recovery_summary(artifact_path, *, now=None, stale_after_sec=None):
    """Return a phone-safe production recovery gate summary."""
    artifact_ref = os.path.expanduser(str(artifact_path or "")).strip()
    if not artifact_ref or not os.path.exists(artifact_ref):
        return _phone_production_recovery_base(
            "missing",
            "尚未提供 production recovery artifact，不能声明生产备份/灾备软件证明。",
            "请生成 production recovery artifact 后刷新状态。",
        )
    summary = production_recovery_artifact_summary(
        artifact_ref,
        now=now,
        stale_after_sec=stale_after_sec,
    )
    if not summary.get("ok"):
        return _phone_production_recovery_base(
            str(summary.get("state") or "invalid"),
            str(summary.get("safe_summary") or "Production recovery gate 产物不可用。"),
            str(summary.get("retry_hint") or "重新生成 production recovery artifact 后刷新状态。"),
        )
    phone_summary = _phone_production_recovery_base(
        "ready",
        "Production recovery gate 软件证明已准备；这只是 Docker/local software proof，不是生产灾备完成。",
        "继续补真实生产备份策略、灾备恢复、多实例和生产 DB/queue 证据。",
    )
    phone_summary.update(
        {
            "local_backup_restore_status": str(summary.get("local_backup_restore_status") or ""),
            "recovery_drill_status": str(summary.get("recovery_drill_status") or ""),
            "state_backend_status": str(summary.get("state_backend_status") or ""),
            "updated_at": str(summary.get("updated_at") or ""),
            "staleness": str(summary.get("staleness") or "fresh"),
        }
    )
    return phone_summary


def build_oss_cdn_manifest_payload(robot_id, task_id, date_text=None, objects=None, created_at=None):
    """生成 Docker/local OSS/CDN 对象引用 proof；不声明真实上传、回源或生产账号。"""
    robot_key = _robot_key(robot_id)
    task_key = str(task_id or "").strip()
    if not task_key:
        raise ValueError("task_id is required")
    date_value = str(date_text or time.strftime("%Y-%m-%d", time.gmtime())).strip()
    created_value = str(created_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    prefix = _manifest_prefix(robot_key, date_value, task_key)
    object_entries = objects if isinstance(objects, list) and objects else [
        {
            "name": "diagnostic_snapshot",
            "object_key": prefix + "diagnostic_snapshot.json",
            "content_type": "application/json",
            "sha256": "sha256:local-proof-placeholder",
            "bytes": 0,
            "redaction": "phone_safe",
        }
    ]
    normalized_objects = []
    for index, item in enumerate(object_entries):
        if not isinstance(item, dict):
            raise ValueError("manifest object entry must be an object")
        object_key = str(item.get("object_key") or "").strip()
        if not object_key:
            raise ValueError("manifest object_key is required")
        entry = {
            "name": str(item.get("name") or f"object_{index + 1}").strip(),
            "object_key": object_key,
            "cdn_url": str(item.get("cdn_url") or _manifest_cdn_url(object_key)).strip(),
            "content_type": str(item.get("content_type") or item.get("media_type") or "application/octet-stream").strip(),
            "sha256": str(item.get("sha256") or "sha256:local-proof-placeholder").strip(),
            "bytes": int(item.get("bytes", 0) or 0),
            "redaction": str(item.get("redaction") or "phone_safe").strip(),
        }
        normalized_objects.append(entry)
    body = {
        "schema": OSS_CDN_MANIFEST_SCHEMA,
        "schema_version": OSS_CDN_MANIFEST_VERSION,
        "evidence_boundary": OSS_CDN_MANIFEST_EVIDENCE_BOUNDARY,
        "created_at": created_value,
        "robot_id": robot_key,
        "task_id": task_key,
        "date": date_value,
        "bucket": OSS_CDN_BUCKET,
        "region": OSS_CDN_REGION,
        "prefix": prefix,
        "cdn_base_url": OSS_CDN_BASE_URL,
        "objects": normalized_objects,
        "not_proven": list(OSS_CDN_NOT_PROVEN),
    }
    forbidden = _manifest_forbidden_markers(body)
    if forbidden:
        raise ValueError("manifest contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _raw_sha256_checksum(body)
    return artifact


def validate_oss_cdn_manifest_payload(artifact):
    # 校验路径只返回摘要；完整 artifact 不进入 preflight 输出，避免误暴露对象清单之外的字段。
    if not isinstance(artifact, dict):
        raise ValueError("manifest artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != OSS_CDN_MANIFEST_SCHEMA:
        raise ValueError("manifest schema mismatch")
    if artifact.get("schema_version") != OSS_CDN_MANIFEST_VERSION:
        raise ValueError("manifest version mismatch")
    if artifact.get("evidence_boundary") != OSS_CDN_MANIFEST_EVIDENCE_BOUNDARY:
        raise ValueError("manifest evidence boundary mismatch")
    if artifact.get("bucket") != OSS_CDN_BUCKET:
        raise ValueError("manifest bucket mismatch")
    if artifact.get("region") != OSS_CDN_REGION:
        raise ValueError("manifest region mismatch")
    if artifact.get("cdn_base_url") != OSS_CDN_BASE_URL:
        raise ValueError("manifest cdn base url mismatch")
    robot_key = _robot_key(artifact.get("robot_id"))
    task_key = str(artifact.get("task_id") or "").strip()
    date_value = str(artifact.get("date") or "").strip()
    expected_prefix = _manifest_prefix(robot_key, date_value, task_key)
    if artifact.get("prefix") != expected_prefix:
        raise ValueError("manifest prefix mismatch")
    objects = artifact.get("objects")
    if not isinstance(objects, list) or not objects:
        raise ValueError("manifest objects must be a non-empty list")
    for item in objects:
        if not isinstance(item, dict):
            raise ValueError("manifest object entry must be an object")
        object_key = str(item.get("object_key") or "").strip()
        cdn_url = str(item.get("cdn_url") or "").strip()
        if not object_key.startswith(expected_prefix):
            raise ValueError("manifest object_key prefix mismatch")
        if cdn_url != _manifest_cdn_url(object_key):
            raise ValueError("manifest cdn_url mismatch")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in OSS_CDN_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("manifest not_proven list is incomplete")
    forbidden = _manifest_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("manifest contains forbidden phone-unsafe markers")
    if checksum != _raw_sha256_checksum(body):
        raise ValueError("manifest checksum mismatch")
    return {
        "ok": True,
        "schema": OSS_CDN_MANIFEST_SCHEMA,
        "schema_version": OSS_CDN_MANIFEST_VERSION,
        "evidence_boundary": OSS_CDN_MANIFEST_EVIDENCE_BOUNDARY,
        "robot_id": robot_key,
        "task_id": task_key,
        "date": date_value,
        "object_count": len(objects),
        "bucket": OSS_CDN_BUCKET,
        "region": OSS_CDN_REGION,
        "prefix_valid": True,
        "cdn_url_rule": "cdn_base_url_plus_object_key_without_rober_prefix",
        "checksum": checksum,
        "not_proven": list(OSS_CDN_NOT_PROVEN),
    }


def create_oss_cdn_manifest_artifact(artifact_path, robot_id, task_id, date_text=None):
    # 该 artifact 是 phone-safe 对象引用 contract，不写入任何 OSS 凭证或本机 state path。
    artifact = build_oss_cdn_manifest_payload(robot_id, task_id, date_text=date_text)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_oss_cdn_manifest_payload(artifact)
    return {
        "ok": True,
        "manifest_status": "passed",
        "evidence_boundary": OSS_CDN_MANIFEST_EVIDENCE_BOUNDARY,
        "safe_summary": "OSS/CDN object reference manifest generated for Docker/local software proof.",
        "retry_hint": "pass_manifest_artifact_to_preflight",
        "artifact": summary,
        "not_proven": list(OSS_CDN_NOT_PROVEN),
    }


def oss_cdn_manifest_summary(artifact_path):
    # preflight 只消费摘要和 checksum 校验结果，不把原始 object list 全量回显给手机。
    try:
        artifact = _load_json_file(artifact_path, "manifest artifact")
        return validate_oss_cdn_manifest_payload(artifact)
    except ValueError as exc:
        return {
            "ok": False,
            "reason_code": "manifest_invalid",
            "safe_summary": _safe_error_reason(exc),
        }


def _oss_cdn_live_probe_forbidden_markers(payload):
    # live probe artifact 只能留下枚举、HTTP 状态和摘要，不能把 URL、凭证或本机路径写进证据。
    encoded = json.dumps(payload, ensure_ascii=False).lower()
    markers = (
        "authorization",
        "bearer ",
        "token",
        "secret",
        "password",
        "access_key",
        "ak/sk",
        "root password",
        "http://",
        "https://",
        "://",
        "credential-bearing",
        "raw state path",
        "state path",
        "/tmp/",
        "/etc/",
        "/dev/",
        "response body",
        "serial",
        "baudrate",
        "wave rover",
        "ros topic",
        "/cmd_vel",
        "/trashbot/",
        "/odom",
        "/imu",
        "/battery",
        "traceback",
    )
    return [marker for marker in markers if marker in encoded]


def _oss_cdn_object_key_digest(object_key):
    # 对象 key 本身可能暴露任务结构；live probe 只保留摘要便于对账。
    return "sha256:" + hashlib.sha256(str(object_key or "").encode("utf-8")).hexdigest()[:16]


def _probe_oss_cdn_object(cdn_url, *, timeout_sec=2.0):
    # 真实请求只在生成 artifact 时发生；artifact 里不保存 URL、header 或响应体。
    started = time.monotonic()
    status_code = 0
    reachable = False
    try:
        request = urllib.request.Request(str(cdn_url), method="HEAD")
        with urllib.request.urlopen(request, timeout=float(timeout_sec)) as response:
            status_code = int(response.status)
            reachable = True
    except urllib.error.HTTPError as exc:
        status_code = int(exc.code)
        reachable = True
    except (OSError, ValueError, TimeoutError):
        reachable = False
    passed = reachable and 200 <= status_code < 400
    return {
        "status": "passed" if passed else "blocked",
        "code": "http_head_observed" if passed else "http_head_not_observed",
        "http_status": status_code,
        "reachable": reachable,
        "method": "HEAD",
        "latency_ms": int((time.monotonic() - started) * 1000),
    }


def build_oss_cdn_live_probe_payload(manifest_artifact_path, *, generated_at=None, timeout_sec=2.0, probe_fn=None):
    """用 manifest 对象引用生成 OSS/CDN live probe gate；证据仍保持 Docker/local software proof。"""
    manifest = _load_json_file(manifest_artifact_path, "manifest artifact")
    manifest_summary = validate_oss_cdn_manifest_payload(manifest)
    generated_value = str(generated_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())).strip()
    probe_fn = _probe_oss_cdn_object if probe_fn is None else probe_fn
    probe_results = []
    for item in manifest.get("objects") or []:
        cdn_url = str(item.get("cdn_url") or "")
        object_key = str(item.get("object_key") or "")
        parsed = urlparse(cdn_url)
        probe = probe_fn(cdn_url, timeout_sec=timeout_sec)
        # endpoint path 是公开只读 CDN 路径；object key 只留 hash，避免把完整对象名扩散到 preflight。
        probe_results.append(
            {
                "endpoint_path": parsed.path or "/",
                "object_key_sha256": _oss_cdn_object_key_digest(object_key),
                "status": str(probe.get("status") or "blocked"),
                "code": str(probe.get("code") or "http_head_not_observed"),
                "http_status": int(probe.get("http_status") or 0),
                "reachable": bool(probe.get("reachable")),
                "method": str(probe.get("method") or "HEAD"),
                "latency_ms": int(probe.get("latency_ms") or 0),
            }
        )
    all_probe_observed = bool(probe_results) and all(result.get("status") == "passed" for result in probe_results)
    body = {
        "schema": OSS_CDN_LIVE_PROBE_SCHEMA,
        "schema_version": OSS_CDN_LIVE_PROBE_SCHEMA_VERSION,
        "evidence_boundary": OSS_CDN_LIVE_PROBE_EVIDENCE_BOUNDARY,
        "generated_at": generated_value,
        "production_ready": False,
        "overall_status": "blocked",
        "live_probe_complete": False,
        "probe_source": "oss_cdn_manifest_artifact",
        "manifest_schema": OSS_CDN_MANIFEST_SCHEMA,
        "manifest_schema_version": OSS_CDN_MANIFEST_VERSION,
        "manifest_evidence_boundary": OSS_CDN_MANIFEST_EVIDENCE_BOUNDARY,
        "object_count": int(manifest_summary.get("object_count") or 0),
        "probe_results": safe_value(probe_results),
        "object_probe_observed": bool(all_probe_observed),
        "not_proven": list(OSS_CDN_LIVE_PROBE_NOT_PROVEN),
        "safe_summary": "OSS/CDN live probe gate 已生成；当前只证明 probe artifact、redaction 和 preflight consumption。",
        "retry_hint": "run_real_oss_upload_and_cdn_fetch_from_production_network_before_claiming_live_traffic",
        "redaction_status": {
            "status": "pass",
            "full_urls_recorded": False,
            "object_keys_recorded": False,
            "credential_headers_recorded": False,
            "response_bodies_recorded": False,
            "local_paths_recorded": False,
        },
    }
    forbidden = _oss_cdn_live_probe_forbidden_markers(body)
    if forbidden:
        raise ValueError("OSS/CDN live probe artifact contains forbidden phone-unsafe markers")
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    return artifact


def validate_oss_cdn_live_probe_payload(artifact):
    # validator 只返回 preflight 需要的小摘要；完整 probe 也不含 URL、header 或响应体。
    if not isinstance(artifact, dict):
        raise ValueError("OSS/CDN live probe artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != OSS_CDN_LIVE_PROBE_SCHEMA:
        raise ValueError("OSS/CDN live probe schema mismatch")
    if artifact.get("schema_version") != OSS_CDN_LIVE_PROBE_SCHEMA_VERSION:
        raise ValueError("OSS/CDN live probe schema version mismatch")
    if artifact.get("evidence_boundary") != OSS_CDN_LIVE_PROBE_EVIDENCE_BOUNDARY:
        raise ValueError("OSS/CDN live probe evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("OSS/CDN live probe checksum mismatch")
    if artifact.get("production_ready") is not False or artifact.get("overall_status") != "blocked":
        raise ValueError("OSS/CDN live probe must stay production blocked")
    if artifact.get("live_probe_complete") is not False:
        raise ValueError("OSS/CDN live probe must not claim real live traffic completion")
    results = artifact.get("probe_results")
    if not isinstance(results, list) or not results:
        raise ValueError("OSS/CDN live probe results must be a non-empty list")
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("OSS/CDN live probe result must be an object")
        if str(result.get("status") or "") not in {"passed", "blocked"}:
            raise ValueError("OSS/CDN live probe status mismatch")
        endpoint_path = str(result.get("endpoint_path") or "")
        digest = str(result.get("object_key_sha256") or "")
        if not endpoint_path.startswith("/") or "://" in endpoint_path:
            raise ValueError("OSS/CDN live probe endpoint path mismatch")
        if not digest.startswith("sha256:") or len(digest) < len("sha256:") + 16:
            raise ValueError("OSS/CDN live probe object digest missing")
    redaction = artifact.get("redaction_status")
    if not isinstance(redaction, dict) or redaction.get("status") != "pass":
        raise ValueError("OSS/CDN live probe redaction status missing")
    not_proven = set(artifact.get("not_proven") if isinstance(artifact.get("not_proven"), list) else [])
    missing_not_proven = [item for item in OSS_CDN_LIVE_PROBE_NOT_PROVEN if item not in not_proven]
    if missing_not_proven:
        raise ValueError("OSS/CDN live probe not_proven list is incomplete")
    safe_summary = str(artifact.get("safe_summary") or "")
    retry_hint = str(artifact.get("retry_hint") or "")
    if not safe_summary or not retry_hint:
        raise ValueError("OSS/CDN live probe summary missing")
    forbidden = _oss_cdn_live_probe_forbidden_markers(artifact)
    if forbidden:
        raise ValueError("OSS/CDN live probe artifact contains forbidden phone-unsafe markers")
    return {
        "ok": True,
        "schema": OSS_CDN_LIVE_PROBE_SCHEMA,
        "schema_version": OSS_CDN_LIVE_PROBE_SCHEMA_VERSION,
        "evidence_boundary": OSS_CDN_LIVE_PROBE_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "live_probe_complete": False,
        "object_count": int(artifact.get("object_count") or len(results)),
        "probe_count": len(results),
        "object_probe_observed": bool(artifact.get("object_probe_observed")),
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "generated_at": str(artifact.get("generated_at") or ""),
        "redaction_status": safe_value(redaction),
        "not_proven": list(OSS_CDN_LIVE_PROBE_NOT_PROVEN),
    }


def create_oss_cdn_live_probe_artifact(artifact_path, manifest_artifact_path, *, timeout_sec=2.0):
    # CLI 写入的 live probe artifact 复用 manifest 输入，但不会把 manifest 路径或对象 key 原文写入结果。
    artifact = build_oss_cdn_live_probe_payload(manifest_artifact_path, timeout_sec=timeout_sec)
    _write_json_artifact(artifact_path, artifact)
    summary = validate_oss_cdn_live_probe_payload(artifact)
    return {
        "ok": True,
        "oss_cdn_live_probe_status": "blocked",
        "evidence_boundary": OSS_CDN_LIVE_PROBE_EVIDENCE_BOUNDARY,
        "production_ready": False,
        "overall_status": "blocked",
        "safe_summary": artifact.get("safe_summary"),
        "retry_hint": artifact.get("retry_hint"),
        "artifact": summary,
        "not_proven": list(OSS_CDN_LIVE_PROBE_NOT_PROVEN),
    }


def oss_cdn_live_probe_summary(artifact_path):
    # 失败摘要不回显 artifact 路径、manifest 路径、URL 或底层 urllib 异常。
    try:
        artifact = _load_json_file(artifact_path, "OSS/CDN live probe artifact")
        return validate_oss_cdn_live_probe_payload(artifact)
    except ValueError as exc:
        return {
            "ok": False,
            "state": "invalid",
            "reason_code": "oss_cdn_live_probe_invalid",
            "safe_summary": _safe_error_reason(exc),
            "retry_hint": "重新生成 OSS/CDN live probe artifact 后重跑 preflight。",
            "not_proven": list(OSS_CDN_LIVE_PROBE_NOT_PROVEN),
        }


def _phone_manifest_base(state, safe_summary, retry_hint):
    # 手机摘要使用独立 proof 边界，避免把上一轮 artifact proof 误读成真实 OSS/CDN 可达。
    return {
        "state": state,
        "schema": OSS_CDN_MANIFEST_SCHEMA,
        "schema_version": OSS_CDN_MANIFEST_VERSION,
        "object_count": 0,
        "cdn_url_rule": "cdn_base_url + manifest object relative path",
        "evidence_boundary": OSS_CDN_PHONE_MANIFEST_EVIDENCE_BOUNDARY,
        "not_proven": list(OSS_CDN_NOT_PROVEN),
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "updated_at": "",
        "staleness": "unknown",
    }


def _parse_manifest_time(value):
    # manifest 来自 CLI、本地 artifact 或后续云端，兼容 Z 和 offset 两种 ISO 写法。
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def build_phone_oss_cdn_manifest_summary(artifact_path, *, now=None, stale_after_sec=None):
    """Return a phone-safe manifest consumption summary.

    该 helper 只证明手机/API 能消费对象引用摘要；即使 state=ready，也不能推断
    真实 OSS 上传、CDN 回源、真实云、真实 4G、送达成功或 HIL。
    """
    artifact_ref = os.path.expanduser(str(artifact_path or "")).strip()
    stale_window = (
        OSS_CDN_PHONE_MANIFEST_STALE_AFTER_SEC
        if stale_after_sec is None
        else float(stale_after_sec)
    )
    now_value = _now() if now is None else float(now)
    if not artifact_ref or not os.path.exists(artifact_ref):
        return _phone_manifest_base(
            "missing",
            "诊断对象引用缺失。",
            "请刷新状态；如仍然缺失，请重新生成诊断引用。",
        )

    try:
        artifact = _load_json_file(artifact_ref, "manifest artifact")
    except ValueError:
        return _phone_manifest_base(
            "missing",
            "诊断对象引用缺失。",
            "请重新生成诊断引用后刷新状态。",
        )

    try:
        summary = validate_oss_cdn_manifest_payload(artifact)
    except ValueError:
        return _phone_manifest_base(
            "invalid",
            "诊断对象引用损坏。",
            "请重新生成诊断引用后刷新状态。",
        )

    updated_at = str(artifact.get("updated_at") or artifact.get("created_at") or "").strip()
    timestamp = _parse_manifest_time(updated_at)
    if timestamp is None:
        stale_summary = _phone_manifest_base(
            "stale",
            "诊断对象引用已过期。",
            "请重新生成诊断引用，避免手机看到旧诊断。",
        )
        stale_summary.update(
            {
                "object_count": int(summary.get("object_count", 0) or 0),
                "updated_at": updated_at,
                "staleness": "timestamp_unavailable",
            }
        )
        return stale_summary
    if now_value - timestamp > stale_window:
        stale_summary = _phone_manifest_base(
            "stale",
            "诊断对象引用已过期。",
            "请重新生成诊断引用，避免手机看到旧诊断。",
        )
        stale_summary.update(
            {
                "object_count": int(summary.get("object_count", 0) or 0),
                "updated_at": updated_at,
                "staleness": "stale",
            }
        )
        return stale_summary

    ready_summary = _phone_manifest_base(
        "ready",
        "诊断对象引用已准备。",
        "如手机无法查看诊断，请刷新状态或重新生成诊断引用。",
    )
    ready_summary.update(
        {
            "object_count": int(summary.get("object_count", 0) or 0),
            "cdn_url_rule": "cdn_base_url + manifest object relative path",
            "updated_at": updated_at or _utc_iso(timestamp),
            "staleness": "fresh",
        }
    )
    return ready_summary


def _state_backend_from_env(env):
    # backend 是 proof 边界的一部分，未知值必须降级，避免把任意 env 文本回显给手机。
    return _safe_enum(
        _env_value(env, "TRASHBOT_REMOTE_CLOUD_STATE_BACKEND", "file"),
        {"file", "sqlite", "postgres", "mysql", "managed_queue", "production_db"},
        "file",
    )


def production_preflight_payload(env=None):
    """生成生产上线前 gate 结果；只证明 Docker/local 配置检查，不触碰真实云资源。"""
    env = os.environ if env is None else env
    checks = []
    token = _env_value(env, "TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN")
    public_base_url = _env_value(env, "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL")
    tls_mode = _env_value(env, "TRASHBOT_REMOTE_CLOUD_TLS_MODE", "future_reverse_proxy")
    ingress_mode = _env_value(env, "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS", "missing")
    oss_bucket = _env_value(env, "TRASHBOT_REMOTE_CLOUD_OSS_BUCKET")
    oss_region = _env_value(env, "TRASHBOT_REMOTE_CLOUD_OSS_REGION")
    oss_prefix = _env_value(env, "TRASHBOT_REMOTE_CLOUD_OSS_PREFIX")
    cdn_base_url = _env_value(env, "TRASHBOT_REMOTE_CLOUD_CDN_BASE_URL")
    oss_credential_mode = _env_value(env, "TRASHBOT_REMOTE_CLOUD_OSS_CREDENTIAL_MODE", "placeholder")
    state_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_STATE")
    state_backend_safe = _state_backend_from_env(env)
    backup_artifact_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_BACKUP_ARTIFACT")
    oss_cdn_manifest_artifact_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT")
    oss_cdn_live_probe_artifact_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT")
    network_recovery_artifact_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT")
    credential_rotation_artifact_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT")
    provisioning_audit_artifact_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT")
    production_store_queue_artifact_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT")
    queue_ordering_drill_artifact_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT")
    transaction_isolation_artifact_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT")
    production_recovery_artifact_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT")
    cloud_external_probe_artifact_path = _env_value(env, "TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_ARTIFACT")
    cloud_public_ingress_tls_artifact_path = _env_value(
        env,
        "TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT",
    )
    cloud_db_queue_config_artifact_path = _env_value(
        env,
        "TRASHBOT_REMOTE_CLOUD_DB_QUEUE_CONFIG_ARTIFACT",
    )
    cloud_db_queue_external_probe_artifact_path = _env_value(
        env,
        "TRASHBOT_REMOTE_CLOUD_DB_QUEUE_EXTERNAL_PROBE_ARTIFACT",
    )
    cloud_worker_migration_rehearsal_artifact_path = _env_value(
        env,
        "TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT",
    )
    external_evidence_intake_artifact_path = _env_value(
        env,
        "TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT",
    )
    cloud_deployment_readiness_artifact_path = _env_value(
        env,
        "TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_READINESS_ARTIFACT",
    )
    tls_mode_safe = _safe_enum(tls_mode, {"future_reverse_proxy", "terminated", "managed", "reverse_proxy"})
    ingress_mode_safe = _safe_enum(ingress_mode, {"missing", "private_only", "public_https"})
    oss_credential_mode_safe = _safe_enum(oss_credential_mode, {"placeholder", "sts", "restricted_ak", "managed_identity"})

    if cloud_deployment_readiness_artifact_path:
        # deployment readiness artifact 是上线前缺口摘要；即使 artifact 有效，也必须保持 production_ready=false。
        deployment_summary = cloud_deployment_readiness_artifact_summary(cloud_deployment_readiness_artifact_path)
        if deployment_summary.get("ok"):
            checks.append(
                _check(
                    "cloud_deployment_readiness",
                    "pass",
                    "local_cloud_deployment_readiness_artifact_valid",
                    "已找到通过 schema、checksum 和 phone-safe 校验的云部署 readiness artifact。",
                    "继续补真实云、HTTPS/TLS、公网入口、4G/SIM、OSS/CDN 和生产 DB/queue 证据。",
                    {
                        "artifact_schema": CLOUD_DEPLOYMENT_READINESS_SCHEMA,
                        "schema_version": CLOUD_DEPLOYMENT_READINESS_SCHEMA_VERSION,
                        "evidence_boundary": CLOUD_DEPLOYMENT_READINESS_EVIDENCE_BOUNDARY,
                        "production_ready": False,
                        "overall_status": "blocked",
                        "check_count": deployment_summary.get("check_count"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            checks.append(
                _check(
                    "cloud_deployment_readiness",
                    "blocked",
                    "cloud_deployment_readiness_artifact_invalid",
                    str(deployment_summary.get("safe_summary") or "云部署 readiness artifact 不可用。"),
                    str(deployment_summary.get("retry_hint") or "重新生成 cloud deployment readiness artifact 后重跑 preflight。"),
                    {"artifact_present": True, "software_proof_only": True},
                )
            )
    else:
        inline_deployment_summary = validate_cloud_deployment_readiness_artifact_payload(
            build_cloud_deployment_readiness_artifact_payload(env)
        )
        checks.append(
            _check(
                "cloud_deployment_readiness",
                "pass",
                "local_cloud_deployment_readiness_inline_gate",
                "已生成本地云部署 readiness gate 摘要；它只记录上线前缺口。",
                "需要持久化 artifact 时设置 TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_READINESS_ARTIFACT 后重跑。",
                {
                    "artifact_schema": CLOUD_DEPLOYMENT_READINESS_SCHEMA,
                    "schema_version": CLOUD_DEPLOYMENT_READINESS_SCHEMA_VERSION,
                    "evidence_boundary": CLOUD_DEPLOYMENT_READINESS_EVIDENCE_BOUNDARY,
                    "production_ready": False,
                    "overall_status": "blocked",
                    "check_count": inline_deployment_summary.get("check_count"),
                    "software_proof_only": True,
                },
            )
        )

    if cloud_external_probe_artifact_path:
        # 外部探测 artifact 只证明 health/ready/preflight 合同覆盖，不把本地 HTTP 成功升级成生产就绪。
        probe_summary = cloud_external_probe_bundle_summary(cloud_external_probe_artifact_path)
        if probe_summary.get("ok"):
            checks.append(
                _check(
                    "cloud_external_probe_bundle",
                    "pass",
                    "local_cloud_external_probe_bundle_valid",
                    "已找到通过 schema、checksum、endpoint 覆盖和脱敏校验的 cloud external probe bundle。",
                    "继续从真实公网 HTTPS 网络重跑探测，再补齐 4G/SIM、OSS/CDN 和生产 DB/queue 证据。",
                    {
                        "artifact_schema": CLOUD_EXTERNAL_PROBE_SCHEMA,
                        "schema_version": CLOUD_EXTERNAL_PROBE_SCHEMA_VERSION,
                        "evidence_boundary": CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
                        "production_ready": False,
                        "overall_status": "blocked",
                        "endpoints_covered": probe_summary.get("endpoints_covered"),
                        "endpoint_contract_ready": probe_summary.get("endpoint_contract_ready"),
                        "redaction_status": probe_summary.get("redaction_status"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            checks.append(
                _check(
                    "cloud_external_probe_bundle",
                    "blocked",
                    "cloud_external_probe_artifact_invalid",
                    str(probe_summary.get("safe_summary") or "Cloud external probe bundle artifact 不可用。"),
                    str(probe_summary.get("retry_hint") or "重新生成 cloud external probe bundle artifact 后重跑 preflight。"),
                    {"artifact_present": True, "software_proof_only": True},
                )
            )
    else:
        checks.append(
            _check(
                "cloud_external_probe_bundle",
                "warning",
                "cloud_external_probe_artifact_missing",
                "尚未提供 cloud external probe bundle artifact，不能声明外部探测软件证明。",
                "用本地或未来公网 base URL 生成 artifact，并通过 TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if cloud_public_ingress_tls_artifact_path:
        # artifact 只让 preflight 区分“完全缺配置”和“配置存在但缺外部实证”，绝不升级 production_ready。
        ingress_tls_summary = cloud_public_ingress_tls_artifact_summary(cloud_public_ingress_tls_artifact_path)
        if ingress_tls_summary.get("ok"):
            state = str(ingress_tls_summary.get("state") or "missing_public_ingress_tls_config")
            checks.append(
                _check(
                    "cloud_public_ingress_tls",
                    "blocked",
                    state,
                    str(ingress_tls_summary.get("safe_summary") or "公网入口/TLS gate 仍未通过外部实证。"),
                    str(ingress_tls_summary.get("retry_hint") or "补齐公网入口/TLS 证据后重跑 preflight。"),
                    {
                        "artifact_schema": CLOUD_PUBLIC_INGRESS_TLS_SCHEMA,
                        "schema_version": CLOUD_PUBLIC_INGRESS_TLS_SCHEMA_VERSION,
                        "evidence_boundary": CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY,
                        "production_ready": False,
                        "overall_status": "blocked",
                        "ingress_config_present": ingress_tls_summary.get("ingress_config_present"),
                        "tls_config_present": ingress_tls_summary.get("tls_config_present"),
                        "reverse_proxy_config_present": ingress_tls_summary.get("reverse_proxy_config_present"),
                        "firewall_config_present": ingress_tls_summary.get("firewall_config_present"),
                        "config_package_present": ingress_tls_summary.get("config_package_present"),
                        "external_probe_proven": False,
                        "software_proof_only": True,
                    },
                )
            )
        else:
            checks.append(
                _check(
                    "cloud_public_ingress_tls",
                    "blocked",
                    "cloud_public_ingress_tls_artifact_invalid",
                    str(ingress_tls_summary.get("safe_summary") or "公网入口/TLS artifact 不可用。"),
                    str(
                        ingress_tls_summary.get("retry_hint")
                        or "重新生成 cloud public ingress TLS artifact 后重跑 preflight。"
                    ),
                    {"artifact_present": True, "software_proof_only": True},
                )
            )
    else:
        inline_ingress_tls_summary = validate_cloud_public_ingress_tls_artifact_payload(
            build_cloud_public_ingress_tls_artifact_payload(env)
        )
        checks.append(
            _check(
                "cloud_public_ingress_tls",
                "blocked",
                str(inline_ingress_tls_summary.get("state") or "missing_public_ingress_tls_config"),
                str(inline_ingress_tls_summary.get("safe_summary") or "公网入口/TLS gate 仍未通过外部实证。"),
                str(inline_ingress_tls_summary.get("retry_hint") or "补齐公网入口/TLS 证据后重跑 preflight。"),
                {
                    "artifact_schema": CLOUD_PUBLIC_INGRESS_TLS_SCHEMA,
                    "schema_version": CLOUD_PUBLIC_INGRESS_TLS_SCHEMA_VERSION,
                    "evidence_boundary": CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY,
                    "production_ready": False,
                    "overall_status": "blocked",
                    "ingress_config_present": inline_ingress_tls_summary.get("ingress_config_present"),
                    "tls_config_present": inline_ingress_tls_summary.get("tls_config_present"),
                    "reverse_proxy_config_present": inline_ingress_tls_summary.get("reverse_proxy_config_present"),
                    "firewall_config_present": inline_ingress_tls_summary.get("firewall_config_present"),
                    "config_package_present": inline_ingress_tls_summary.get("config_package_present"),
                    "external_probe_proven": False,
                    "software_proof_only": True,
                },
            )
        )

    if cloud_db_queue_config_artifact_path:
        # 该 gate 只确认 DB/queue 配置包形态，不连接真实生产数据库或队列。
        db_queue_summary = cloud_db_queue_config_artifact_summary(cloud_db_queue_config_artifact_path)
        if db_queue_summary.get("ok"):
            state = str(db_queue_summary.get("state") or "missing_cloud_db_queue_config")
            checks.append(
                _check(
                    "cloud_db_queue_config",
                    "blocked",
                    state,
                    str(db_queue_summary.get("safe_summary") or "生产 DB/queue 配置 gate 仍未通过外部实证。"),
                    str(db_queue_summary.get("retry_hint") or "补齐真实 DB/queue 证据后重跑 preflight。"),
                    {
                        "artifact_schema": CLOUD_DB_QUEUE_CONFIG_SCHEMA,
                        "schema_version": CLOUD_DB_QUEUE_CONFIG_SCHEMA_VERSION,
                        "evidence_boundary": CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY,
                        "production_ready": False,
                        "overall_status": "blocked",
                        "db_config_present": db_queue_summary.get("db_config_present"),
                        "queue_config_present": db_queue_summary.get("queue_config_present"),
                        "migration_config_present": db_queue_summary.get("migration_config_present"),
                        "queue_worker_config_present": db_queue_summary.get("queue_worker_config_present"),
                        "config_package_present": db_queue_summary.get("config_package_present"),
                        "external_db_queue_probe_proven": False,
                        "software_proof_only": True,
                    },
                )
            )
        else:
            checks.append(
                _check(
                    "cloud_db_queue_config",
                    "blocked",
                    "cloud_db_queue_config_artifact_invalid",
                    str(db_queue_summary.get("safe_summary") or "生产 DB/queue 配置 artifact 不可用。"),
                    str(
                        db_queue_summary.get("retry_hint")
                        or "重新生成 cloud DB/queue config artifact 后重跑 preflight。"
                    ),
                    {"artifact_present": True, "software_proof_only": True},
                )
            )
    else:
        inline_db_queue_summary = validate_cloud_db_queue_config_artifact_payload(
            build_cloud_db_queue_config_artifact_payload(env)
        )
        checks.append(
            _check(
                "cloud_db_queue_config",
                "blocked",
                str(inline_db_queue_summary.get("state") or "missing_cloud_db_queue_config"),
                str(inline_db_queue_summary.get("safe_summary") or "生产 DB/queue 配置 gate 仍未通过外部实证。"),
                str(inline_db_queue_summary.get("retry_hint") or "补齐真实 DB/queue 证据后重跑 preflight。"),
                {
                    "artifact_schema": CLOUD_DB_QUEUE_CONFIG_SCHEMA,
                    "schema_version": CLOUD_DB_QUEUE_CONFIG_SCHEMA_VERSION,
                    "evidence_boundary": CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY,
                    "production_ready": False,
                    "overall_status": "blocked",
                    "db_config_present": inline_db_queue_summary.get("db_config_present"),
                    "queue_config_present": inline_db_queue_summary.get("queue_config_present"),
                    "migration_config_present": inline_db_queue_summary.get("migration_config_present"),
                    "queue_worker_config_present": inline_db_queue_summary.get("queue_worker_config_present"),
                    "config_package_present": inline_db_queue_summary.get("config_package_present"),
                    "external_db_queue_probe_proven": False,
                    "software_proof_only": True,
                },
            )
        )

    if cloud_db_queue_external_probe_artifact_path:
        # 该 bundle 只证明外部 DB/queue probe artifact 可被校验和消费，不连接真实生产资源。
        external_probe_summary = cloud_db_queue_external_probe_bundle_summary(
            cloud_db_queue_external_probe_artifact_path
        )
        if external_probe_summary.get("ok"):
            checks.append(
                _check(
                    "cloud_db_queue_external_probe_bundle",
                    "pass",
                    "local_cloud_db_queue_external_probe_bundle_valid",
                    str(
                        external_probe_summary.get("safe_summary")
                        or "DB/queue external probe bundle 已通过 schema、checksum 和脱敏校验。"
                    ),
                    str(
                        external_probe_summary.get("retry_hint")
                        or "继续补真实生产 DB/queue 外部探测证据。"
                    ),
                    {
                        "artifact_schema": CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA,
                        "schema_version": CLOUD_DB_QUEUE_EXTERNAL_PROBE_SCHEMA_VERSION,
                        "evidence_boundary": CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY,
                        "production_ready": False,
                        "overall_status": "blocked",
                        "external_probe_complete": False,
                        "probe_count": external_probe_summary.get("probe_count"),
                        "db_connectivity_status": external_probe_summary.get("db_connectivity_status"),
                        "queue_connectivity_status": external_probe_summary.get("queue_connectivity_status"),
                        "migration_check_status": external_probe_summary.get("migration_check_status"),
                        "worker_check_status": external_probe_summary.get("worker_check_status"),
                        "multi_instance_consistency_status": external_probe_summary.get(
                            "multi_instance_consistency_status"
                        ),
                        "ordering_check_status": external_probe_summary.get("ordering_check_status"),
                        "transaction_isolation_status": external_probe_summary.get(
                            "transaction_isolation_status"
                        ),
                        "backup_recovery_status": external_probe_summary.get("backup_recovery_status"),
                        "redaction_status": external_probe_summary.get("redaction_status"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            checks.append(
                _check(
                    "cloud_db_queue_external_probe_bundle",
                    "blocked",
                    "cloud_db_queue_external_probe_artifact_invalid",
                    str(external_probe_summary.get("safe_summary") or "DB/queue external probe bundle 不可用。"),
                    str(
                        external_probe_summary.get("retry_hint")
                        or "重新生成 cloud DB/queue external probe bundle artifact 后重跑 preflight。"
                    ),
                    {"artifact_present": True, "software_proof_only": True},
                )
            )
    else:
        checks.append(
            _check(
                "cloud_db_queue_external_probe_bundle",
                "warning",
                "cloud_db_queue_external_probe_artifact_missing",
                "尚未提供 DB/queue external probe bundle artifact，不能声明外部 DB/queue 探测入口软件证明。",
                "生成 cloud DB/queue external probe bundle artifact，并用 TRASHBOT_REMOTE_CLOUD_DB_QUEUE_EXTERNAL_PROBE_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if cloud_worker_migration_rehearsal_artifact_path:
        # worker/migration rehearsal 只消费 Docker/local SQLite artifact；ACK 仍不是 delivery success。
        rehearsal_summary = cloud_worker_migration_rehearsal_artifact_summary(
            cloud_worker_migration_rehearsal_artifact_path
        )
        if rehearsal_summary.get("ok"):
            checks.append(
                _check(
                    "cloud_worker_migration_rehearsal",
                    "pass",
                    "local_cloud_worker_migration_rehearsal_artifact_valid",
                    str(
                        rehearsal_summary.get("safe_summary")
                        or "Cloud worker/migration rehearsal artifact 已通过 schema、checksum 和脱敏校验。"
                    ),
                    str(
                        rehearsal_summary.get("retry_hint")
                        or "继续补真实 production DB/queue migration 和 worker 证据。"
                    ),
                    {
                        "artifact_schema": CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA,
                        "schema_version": CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA_VERSION,
                        "summary_schema": CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA,
                        "summary_schema_version": CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA_VERSION,
                        "evidence_boundary": CLOUD_WORKER_MIGRATION_REHEARSAL_EVIDENCE_BOUNDARY,
                        "production_ready": False,
                        "overall_status": "blocked",
                        "software_proof_ready": True,
                        "delivery_success": False,
                        "primary_actions_enabled": False,
                        "migration_status": rehearsal_summary.get("migration_status"),
                        "worker_status": rehearsal_summary.get("worker_status"),
                        "sqlite_state_initialized": rehearsal_summary.get("sqlite_state_initialized"),
                        "schema_version_marked": rehearsal_summary.get("schema_version_marked"),
                        "idempotent_replay_status": rehearsal_summary.get("idempotent_replay_status"),
                        "ack_acceptance_status": rehearsal_summary.get("ack_acceptance_status"),
                        "ack_processing_status": rehearsal_summary.get("ack_processing_status"),
                        "terminal_ack_state": rehearsal_summary.get("terminal_ack_state"),
                        "cursor_semantics_preserved": rehearsal_summary.get("cursor_semantics_preserved"),
                        "redaction_status": rehearsal_summary.get("redaction_status"),
                    },
                )
            )
        else:
            checks.append(
                _check(
                    "cloud_worker_migration_rehearsal",
                    "blocked",
                    "cloud_worker_migration_rehearsal_artifact_invalid",
                    str(rehearsal_summary.get("safe_summary") or "Cloud worker/migration rehearsal artifact 不可用。"),
                    str(
                        rehearsal_summary.get("retry_hint")
                        or "重新生成 cloud worker migration rehearsal artifact 后重跑 preflight。"
                    ),
                    {"artifact_present": True, "software_proof_only": True},
                )
            )
    else:
        checks.append(
            _check(
                "cloud_worker_migration_rehearsal",
                "warning",
                "cloud_worker_migration_rehearsal_artifact_missing",
                "尚未提供 cloud worker/migration rehearsal artifact，不能声明 migration/worker 本地演练软件证明。",
                "生成 cloud worker migration rehearsal artifact，并用 TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if external_evidence_intake_artifact_path:
        # intake gate 只证明外部材料可被安全接收和脱敏消费，不能把材料存在等同于真实云已通过。
        intake_summary = external_evidence_intake_artifact_summary(external_evidence_intake_artifact_path)
        if intake_summary.get("ok"):
            checks.append(
                _check(
                    "external_evidence_intake",
                    "pass",
                    "local_external_evidence_intake_artifact_valid",
                    str(
                        intake_summary.get("safe_summary")
                        or "External evidence intake artifact 已通过 schema、checksum 和脱敏校验。"
                    ),
                    str(intake_summary.get("retry_hint") or "继续提交真实外部材料的脱敏摘要。"),
                    {
                        "artifact_schema": EXTERNAL_EVIDENCE_INTAKE_SCHEMA,
                        "schema_version": EXTERNAL_EVIDENCE_INTAKE_SCHEMA_VERSION,
                        "evidence_boundary": EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY,
                        "production_ready": False,
                        "overall_status": "blocked",
                        "external_evidence_complete": False,
                        "material_count": intake_summary.get("material_count"),
                        "public_ingress_tls_status": intake_summary.get("public_ingress_tls_status"),
                        "oss_cdn_status": intake_summary.get("oss_cdn_status"),
                        "production_db_queue_status": intake_summary.get("production_db_queue_status"),
                        "four_g_sim_status": intake_summary.get("four_g_sim_status"),
                        "redaction_status": intake_summary.get("redaction_status"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            checks.append(
                _check(
                    "external_evidence_intake",
                    "blocked",
                    "external_evidence_intake_artifact_invalid",
                    str(intake_summary.get("safe_summary") or "External evidence intake artifact 不可用。"),
                    str(intake_summary.get("retry_hint") or "重新生成 external evidence intake artifact 后重跑 preflight。"),
                    {"artifact_present": True, "software_proof_only": True},
                )
            )
    else:
        checks.append(
            _check(
                "external_evidence_intake",
                "warning",
                "external_evidence_intake_artifact_missing",
                "尚未提供 external evidence intake artifact，不能声明外部材料收件口软件证明。",
                "生成 external evidence intake artifact，并用 TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if _is_placeholder(token):
        checks.append(
            _check(
                "credential_provisioning",
                "blocked",
                "missing_or_placeholder_credential",
                "远程控制访问凭证仍是缺失或占位值。",
                "通过安全环境变量注入生产访问凭证，并完成轮换预案。",
                {"token_present": bool(token), "token_is_placeholder": True},
            )
        )
    else:
        checks.append(
            _check(
                "credential_provisioning",
                "pass",
                "credential_injected",
                "远程控制访问凭证已通过环境变量注入。",
                "继续确认生产密钥托管和 rotate 流程。",
                {"token_present": True, "token_is_placeholder": False},
            )
        )

    public_scheme = _safe_scheme(public_base_url)
    if public_scheme != "https" or _is_placeholder(public_base_url):
        checks.append(
            _check(
                "tls_public_ingress",
                "blocked",
                "https_public_ingress_missing",
                "当前不是生产 HTTPS 公网入口，Docker/local HTTP 只能作为软件 proof。",
                "配置公网域名、TLS 证书、反向代理和防火墙后重跑 preflight。",
                {
                    "public_base_url_scheme": public_scheme,
                    "tls_mode": tls_mode_safe,
                    "public_ingress": ingress_mode_safe,
                    "docker_local_only": True,
                },
            )
        )
    else:
        tls_ready = tls_mode_safe in {"terminated", "managed", "reverse_proxy"} and ingress_mode_safe == "public_https"
        checks.append(
            _check(
                "tls_public_ingress",
                "pass" if tls_ready else "warning",
                "https_config_present" if tls_ready else "https_declared_but_unverified",
                "已声明 HTTPS 公网入口配置，但本 gate 不发起真实公网探测。",
                "用云端证书、防火墙和外网 curl 证据补齐生产验收。",
                {
                    "public_base_url_scheme": public_scheme,
                    "tls_mode": tls_mode_safe,
                    "public_ingress": ingress_mode_safe,
                    "public_probe_performed": False,
                },
            )
        )

    oss_placeholder = any(_is_placeholder(value) for value in (oss_bucket, oss_region, oss_prefix, cdn_base_url))
    cdn_https = _safe_scheme(cdn_base_url) == "https"
    credential_ready = oss_credential_mode_safe in {"sts", "restricted_ak", "managed_identity"}
    if oss_placeholder or not cdn_https or not credential_ready:
        checks.append(
            _check(
                "oss_cdn",
                "blocked",
                "oss_cdn_not_production_ready",
                "OSS/CDN 仍缺少可上线配置或受限凭证模式，未声明真实对象上传成功。",
                "配置 bucket/region/prefix、HTTPS CDN 和 STS/受限 AK 后重跑。",
                {
                    "bucket_configured": bool(oss_bucket) and not _is_placeholder(oss_bucket),
                    "region_configured": bool(oss_region) and not _is_placeholder(oss_region),
                    "prefix_configured": bool(oss_prefix) and not _is_placeholder(oss_prefix),
                    "cdn_scheme": _safe_scheme(cdn_base_url),
                    "credential_mode": oss_credential_mode_safe,
                    "object_upload_probe_performed": False,
                },
            )
        )
    else:
        checks.append(
            _check(
                "oss_cdn",
                "warning",
                "oss_cdn_config_present_but_unverified",
                "OSS/CDN 配置形态已齐，但本 gate 未进行真实上传或 CDN 回源验证。",
                "补充 STS 签发、对象上传、CDN 访问和生命周期证据。",
                {
                    "bucket_configured": True,
                    "region_configured": True,
                    "prefix_configured": True,
                    "cdn_scheme": "https",
                    "credential_mode": oss_credential_mode_safe,
                    "object_upload_probe_performed": False,
                },
            )
        )

    store = build_relay_store(state_path, state_backend_safe)
    state_writable = store.state_store_writable()
    if not state_writable:
        checks.append(
            _check(
                "state_store",
                "blocked",
                "state_store_not_writable",
                "relay proof state store 不可写，无法证明 command/status/ack 可恢复。",
                "修正容器挂载或 state path 权限后重跑。",
                {"backend": state_backend_safe, "writable": False},
            )
        )
    elif state_backend_safe == "sqlite":
        checks.append(
            _check(
                "state_store",
                "warning",
                "sqlite_state_store_proof_only",
                "SQLite-backed store 可写并可用于单机恢复 proof，但仍不是生产 DB/队列。",
                "补充生产 DB/queue、多实例一致性、备份恢复和灾备演练证据。",
                {
                    "backend": "sqlite",
                    "writable": True,
                    "production_durable": False,
                    "single_instance_only": True,
                    "backup_restore_probe_performed": False,
                    "disaster_recovery_probe_performed": False,
                },
            )
        )
    elif state_backend_safe not in {"postgres", "mysql", "managed_queue", "production_db"}:
        checks.append(
            _check(
                "state_store",
                "warning",
                "file_backed_store_only",
                "本轮只证明 file-backed store 可写，不等于生产 DB/队列。",
                "接入生产数据库或队列，并补充备份、并发和灾备证据。",
                {"backend": state_backend_safe, "writable": True, "production_durable": False},
            )
        )
    else:
        checks.append(
            _check(
                "state_store",
                "warning",
                "production_store_declared_but_unverified",
                "已声明生产 state backend，但本 gate 未连接真实 DB/队列。",
                "用生产连接探测、迁移和恢复演练证据补齐验收。",
                {"backend": state_backend_safe, "writable": True, "production_probe_performed": False},
            )
        )

    if backup_artifact_path:
        # preflight 只验证 artifact 形态和 checksum，不恢复到生产 state，避免旁路修改主路径。
        backup_summary = backup_artifact_summary(backup_artifact_path)
        if backup_summary.get("ok"):
            checks.append(
                _check(
                    "backup_restore_drill",
                    "pass",
                    "local_backup_restore_drill_artifact_valid",
                    "已找到通过 checksum 校验的本地备份恢复演练 artifact。",
                    "继续执行 remote bridge compatibility acceptance；生产备份策略仍需单独验收。",
                    {
                        "drill_performed": True,
                        "artifact_schema": BACKUP_ARTIFACT_SCHEMA,
                        "source_backend": backup_summary.get("source_backend"),
                        "command_count": backup_summary.get("command_count"),
                        "status_count": backup_summary.get("status_count"),
                        "ack_count": backup_summary.get("ack_count"),
                        "production_backup_policy": False,
                        "real_disaster_recovery": False,
                    },
                )
            )
        else:
            checks.append(
                _check(
                    "backup_restore_drill",
                    "blocked",
                    "backup_restore_drill_artifact_invalid",
                    "本地备份恢复演练 artifact 缺失、schema 不匹配或 checksum 校验失败。",
                    "重新生成 artifact 并完成 restore drill 后再重跑 preflight。",
                    {
                        "drill_performed": False,
                        "reason_code": backup_summary.get("reason_code", "artifact_invalid"),
                        "production_backup_policy": False,
                        "real_disaster_recovery": False,
                    },
                )
            )
    else:
        checks.append(
            _check(
                "backup_restore_drill",
                "warning",
                "backup_restore_drill_not_run",
                "尚未提供本地备份恢复演练 artifact，不能声明 backup/restore 软件证明。",
                "运行 SQLite backup -> restore drill，并把 artifact 传给 preflight 后复核。",
                {
                    "drill_performed": False,
                    "production_backup_policy": False,
                    "real_disaster_recovery": False,
                },
            )
        )

    if oss_cdn_manifest_artifact_path:
        # manifest gate 只证明对象引用 shape/checksum/CDN URL 规则，不发起真实 OSS 或 CDN 请求。
        manifest_summary = oss_cdn_manifest_summary(oss_cdn_manifest_artifact_path)
        if manifest_summary.get("ok"):
            checks.append(
                _check(
                    "oss_cdn_manifest",
                    "pass",
                    "local_oss_cdn_manifest_artifact_valid",
                    "已找到通过 schema、prefix、CDN URL 和 checksum 校验的 OSS/CDN manifest artifact。",
                    "后续仍需接入真实 STS、OSS 上传、CDN 回源和生命周期证据。",
                    {
                        "manifest_schema": OSS_CDN_MANIFEST_SCHEMA,
                        "schema_version": OSS_CDN_MANIFEST_VERSION,
                        "object_count": manifest_summary.get("object_count"),
                        "bucket": OSS_CDN_BUCKET,
                        "region": OSS_CDN_REGION,
                        "prefix_valid": bool(manifest_summary.get("prefix_valid")),
                        "cdn_url_rule": manifest_summary.get("cdn_url_rule"),
                        "checksum_valid": True,
                        "real_oss_upload": False,
                        "sts_issuance": False,
                        "cdn_origin_fetch": False,
                        "lifecycle_policy": False,
                        "production_account": False,
                    },
                )
            )
        else:
            checks.append(
                _check(
                    "oss_cdn_manifest",
                    "blocked",
                    "oss_cdn_manifest_artifact_invalid",
                    "OSS/CDN manifest artifact 缺失、schema 不匹配、URL 规则错误或 checksum 校验失败。",
                    "重新生成 phone-safe manifest artifact 后通过环境变量或 CLI 参数传给 preflight。",
                    {
                        "manifest_present": False,
                        "reason_code": manifest_summary.get("reason_code", "manifest_invalid"),
                        "real_oss_upload": False,
                        "cdn_origin_fetch": False,
                    },
                )
            )
    else:
        checks.append(
            _check(
                "oss_cdn_manifest",
                "warning",
                "oss_cdn_manifest_artifact_missing",
                "尚未提供 OSS/CDN manifest artifact，不能声明对象引用 shape proof。",
                "生成 manifest artifact，并用 TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT 或 CLI 参数传给 preflight。",
                {
                    "manifest_present": False,
                    "real_oss_upload": False,
                    "cdn_origin_fetch": False,
                },
            )
        )

    if oss_cdn_live_probe_artifact_path:
        # live probe gate 只消费脱敏 artifact；即使 HTTP HEAD 有结果，也不能升级为真实 OSS/CDN 生产证明。
        live_probe_summary = oss_cdn_live_probe_summary(oss_cdn_live_probe_artifact_path)
        if live_probe_summary.get("ok"):
            checks.append(
                _check(
                    "oss_cdn_live_probe",
                    "pass",
                    "local_oss_cdn_live_probe_artifact_valid",
                    str(
                        live_probe_summary.get("safe_summary")
                        or "OSS/CDN live probe artifact 已通过 schema、checksum 和脱敏校验。"
                    ),
                    str(live_probe_summary.get("retry_hint") or "继续补真实 OSS 上传和 CDN 回源证据。"),
                    {
                        "artifact_schema": OSS_CDN_LIVE_PROBE_SCHEMA,
                        "schema_version": OSS_CDN_LIVE_PROBE_SCHEMA_VERSION,
                        "evidence_boundary": OSS_CDN_LIVE_PROBE_EVIDENCE_BOUNDARY,
                        "production_ready": False,
                        "overall_status": "blocked",
                        "live_probe_complete": False,
                        "object_count": live_probe_summary.get("object_count"),
                        "probe_count": live_probe_summary.get("probe_count"),
                        "object_probe_observed": live_probe_summary.get("object_probe_observed"),
                        "redaction_status": live_probe_summary.get("redaction_status"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            checks.append(
                _check(
                    "oss_cdn_live_probe",
                    "blocked",
                    "oss_cdn_live_probe_artifact_invalid",
                    str(live_probe_summary.get("safe_summary") or "OSS/CDN live probe artifact 不可用。"),
                    str(live_probe_summary.get("retry_hint") or "重新生成 OSS/CDN live probe artifact 后重跑 preflight。"),
                    {"artifact_present": True, "software_proof_only": True},
                )
            )
    else:
        checks.append(
            _check(
                "oss_cdn_live_probe",
                "warning",
                "oss_cdn_live_probe_artifact_missing",
                "尚未提供 OSS/CDN live probe artifact，不能声明 CDN live traffic 软件证明入口。",
                "生成 OSS/CDN live probe artifact，并用 TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if network_recovery_artifact_path:
        # recovery gate 只校验本地 artifact，不把 steps 或 state path 放进 preflight 输出。
        recovery_summary = network_recovery_artifact_summary(network_recovery_artifact_path)
        if recovery_summary.get("ok"):
            checks.append(
                _check(
                    "network_recovery_drill",
                    "pass",
                    "local_network_recovery_drill_artifact_valid",
                    "已找到通过 checksum 校验的 Docker/local 网络恢复演练 artifact。",
                    "继续执行 robot bridge compatibility fence；真实云/4G 恢复仍需后续验收。",
                    {
                        "artifact_schema": NETWORK_RECOVERY_SCHEMA,
                        "schema_version": NETWORK_RECOVERY_SCHEMA_VERSION,
                        "step_count": recovery_summary.get("step_count"),
                        "cursor_invariant": recovery_summary.get("cursor_invariant"),
                        "staleness": recovery_summary.get("staleness"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            state = str(recovery_summary.get("state") or "invalid")
            checks.append(
                _check(
                    "network_recovery_drill",
                    "blocked",
                    f"network_recovery_artifact_{state}",
                    str(recovery_summary.get("safe_summary") or "网络恢复演练产物不可用。"),
                    str(recovery_summary.get("retry_hint") or "重新运行 network recovery drill 后重跑 preflight。"),
                    {
                        "artifact_present": True,
                        "reason_code": recovery_summary.get("reason_code", "network_recovery_invalid"),
                        "software_proof_only": True,
                    },
                )
            )
    else:
        checks.append(
            _check(
                "network_recovery_drill",
                "warning",
                "network_recovery_artifact_missing",
                "尚未提供网络恢复演练 artifact，不能声明弱网/断网恢复软件证明。",
                "运行 network recovery drill，并用 TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if credential_rotation_artifact_path:
        # credential gate 只校验本地 artifact，不读取或输出任何真实 token、AK/SK 或账号 secret。
        credential_summary = credential_rotation_artifact_summary(credential_rotation_artifact_path)
        if credential_summary.get("ok"):
            checks.append(
                _check(
                    "credential_rotation",
                    "pass",
                    "local_credential_rotation_artifact_valid",
                    "已找到通过 schema、checksum 和 phone-safe 校验的凭证轮换 artifact。",
                    "继续补真实云账号、STS 签发、审计日志和生产 rotate 证据。",
                    {
                        "artifact_schema": CREDENTIAL_ROTATION_SCHEMA,
                        "schema_version": CREDENTIAL_ROTATION_SCHEMA_VERSION,
                        "bearer_rotation_status": credential_summary.get("bearer_rotation_status"),
                        "oss_credential_mode": credential_summary.get("oss_credential_mode"),
                        "sts_boundary_status": credential_summary.get("sts_boundary_status"),
                        "account_tier_status": credential_summary.get("account_tier_status"),
                        "robot_provisioning_status": credential_summary.get("robot_provisioning_status"),
                        "audit_log_status": credential_summary.get("audit_log_status"),
                        "staleness": credential_summary.get("staleness"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            state = str(credential_summary.get("state") or "invalid")
            checks.append(
                _check(
                    "credential_rotation",
                    "blocked",
                    f"credential_rotation_artifact_{state}",
                    str(credential_summary.get("safe_summary") or "凭证轮换软件证明产物不可用。"),
                    str(credential_summary.get("retry_hint") or "重新生成 credential rotation artifact 后重跑 preflight。"),
                    {
                        "artifact_present": True,
                        "reason_code": credential_summary.get("reason_code", "credential_rotation_invalid"),
                        "software_proof_only": True,
                    },
                )
            )
    else:
        checks.append(
            _check(
                "credential_rotation",
                "warning",
                "credential_rotation_artifact_missing",
                "尚未提供凭证轮换 artifact，不能声明本地 credential rotation gate 软件证明。",
                "生成 credential rotation artifact，并用 TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if provisioning_audit_artifact_path:
        # provisioning audit 只证明三类上线前 contract 形态，不签发 STS、不写真实 audit sink。
        provisioning_summary = provisioning_audit_artifact_summary(provisioning_audit_artifact_path)
        if provisioning_summary.get("ok"):
            checks.append(
                _check(
                    "provisioning_audit",
                    "pass",
                    "local_provisioning_audit_artifact_valid",
                    "已找到通过 schema、checksum 和 phone-safe 校验的 provisioning / STS / audit artifact。",
                    "继续补真实生产 provisioning、STS 签发和审计日志证据。",
                    {
                        "artifact_schema": PROVISIONING_AUDIT_SCHEMA,
                        "schema_version": PROVISIONING_AUDIT_SCHEMA_VERSION,
                        "robot_provisioning_status": provisioning_summary.get("robot_provisioning_status"),
                        "sts_issuance_status": provisioning_summary.get("sts_issuance_status"),
                        "audit_log_status": provisioning_summary.get("audit_log_status"),
                        "credential_delivery_status": provisioning_summary.get("credential_delivery_status"),
                        "production_ready": False,
                        "overall_status": "blocked",
                        "staleness": provisioning_summary.get("staleness"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            state = str(provisioning_summary.get("state") or "invalid")
            checks.append(
                _check(
                    "provisioning_audit",
                    "blocked",
                    f"provisioning_audit_artifact_{state}",
                    str(provisioning_summary.get("safe_summary") or "Provisioning / STS / audit 软件证明产物不可用。"),
                    str(provisioning_summary.get("retry_hint") or "重新生成 provisioning audit artifact 后重跑 preflight。"),
                    {
                        "artifact_present": True,
                        "reason_code": provisioning_summary.get("reason_code", "provisioning_audit_invalid"),
                        "software_proof_only": True,
                    },
                )
            )
    else:
        checks.append(
            _check(
                "provisioning_audit",
                "warning",
                "provisioning_audit_artifact_missing",
                "尚未提供 provisioning / STS / audit artifact，不能声明生产账号发放、STS 签发或审计日志软件证明。",
                "生成 provisioning audit artifact，并用 TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if production_store_queue_artifact_path:
        # production store/queue gate 只证明 contract artifact 可消费，不连接真实 DB/queue。
        store_queue_summary = production_store_queue_artifact_summary(production_store_queue_artifact_path)
        if store_queue_summary.get("ok"):
            checks.append(
                _check(
                    "production_store_queue",
                    "pass",
                    "local_production_store_queue_artifact_valid",
                    "已找到通过 schema、checksum 和 phone-safe 校验的 production store/queue artifact。",
                    "继续补真实生产 DB/queue、多实例一致性、迁移和备份证据。",
                    {
                        "artifact_schema": PRODUCTION_STORE_QUEUE_SCHEMA,
                        "schema_version": PRODUCTION_STORE_QUEUE_SCHEMA_VERSION,
                        "store_contract_status": store_queue_summary.get("store_contract_status"),
                        "queue_contract_status": store_queue_summary.get("queue_contract_status"),
                        "ordering_status": store_queue_summary.get("ordering_status"),
                        "consistency_status": store_queue_summary.get("consistency_status"),
                        "migration_status": store_queue_summary.get("migration_status"),
                        "production_ready": False,
                        "overall_status": "blocked",
                        "staleness": store_queue_summary.get("staleness"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            state = str(store_queue_summary.get("state") or "invalid")
            checks.append(
                _check(
                    "production_store_queue",
                    "blocked",
                    f"production_store_queue_artifact_{state}",
                    str(store_queue_summary.get("safe_summary") or "Production store/queue 软件证明产物不可用。"),
                    str(store_queue_summary.get("retry_hint") or "重新生成 production store/queue artifact 后重跑 preflight。"),
                    {
                        "artifact_present": True,
                        "reason_code": store_queue_summary.get("reason_code", "production_store_queue_invalid"),
                        "software_proof_only": True,
                    },
                )
            )
    else:
        checks.append(
            _check(
                "production_store_queue",
                "warning",
                "production_store_queue_artifact_missing",
                "尚未提供 production store/queue artifact，不能声明生产 DB/queue 软件证明。",
                "生成 production store/queue artifact，并用 TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if queue_ordering_drill_artifact_path:
        # Queue ordering drill 只消费 Docker/local artifact，不探测真实生产队列或多实例隔离。
        ordering_summary = queue_ordering_drill_artifact_summary(queue_ordering_drill_artifact_path)
        if ordering_summary.get("ok"):
            checks.append(
                _check(
                    "queue_ordering_drill",
                    "pass",
                    "local_queue_ordering_drill_artifact_valid",
                    "已找到通过 schema、checksum 和 phone-safe 校验的 queue ordering drill artifact。",
                    "继续补真实生产 queue ordering、多实例一致性和事务隔离证据。",
                    {
                        "artifact_schema": QUEUE_ORDERING_DRILL_SCHEMA,
                        "schema_version": QUEUE_ORDERING_DRILL_SCHEMA_VERSION,
                        "ordering_invariant": ordering_summary.get("ordering_invariant"),
                        "concurrency_invariant": ordering_summary.get("concurrency_invariant"),
                        "cursor_invariant": ordering_summary.get("cursor_invariant"),
                        "ack_invariant": ordering_summary.get("ack_invariant"),
                        "adjacent_command_ids": ordering_summary.get("adjacent_command_ids"),
                        "observed_order": ordering_summary.get("observed_order"),
                        "production_ready": False,
                        "overall_status": "passed",
                        "staleness": ordering_summary.get("staleness"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            state = str(ordering_summary.get("state") or "invalid")
            checks.append(
                _check(
                    "queue_ordering_drill",
                    "blocked",
                    f"queue_ordering_drill_artifact_{state}",
                    str(ordering_summary.get("safe_summary") or "Queue ordering drill 软件证明产物不可用。"),
                    str(ordering_summary.get("retry_hint") or "重新生成 queue ordering drill artifact 后重跑 preflight。"),
                    {
                        "artifact_present": True,
                        "reason_code": ordering_summary.get("reason_code", "queue_ordering_drill_invalid"),
                        "software_proof_only": True,
                    },
                )
            )
    else:
        checks.append(
            _check(
                "queue_ordering_drill",
                "warning",
                "queue_ordering_drill_artifact_missing",
                "尚未提供 queue ordering drill artifact，不能声明队列顺序软件证明。",
                "生成 queue ordering drill artifact，并用 TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if transaction_isolation_artifact_path:
        # Transaction isolation drill 只验证同 robot 的本地 interleaving，不声明真实生产隔离级别。
        isolation_summary = transaction_isolation_artifact_summary(transaction_isolation_artifact_path)
        if isolation_summary.get("ok"):
            checks.append(
                _check(
                    "transaction_isolation",
                    "pass",
                    "local_transaction_isolation_artifact_valid",
                    "已找到通过 schema、checksum 和 phone-safe 校验的 transaction isolation artifact。",
                    "继续补真实生产 DB/queue、多实例一致性和生产事务隔离证据。",
                    {
                        "artifact_schema": TRANSACTION_ISOLATION_SCHEMA,
                        "schema_version": TRANSACTION_ISOLATION_SCHEMA_VERSION,
                        "scenario": isolation_summary.get("scenario"),
                        "command_a_id": isolation_summary.get("command_a_id"),
                        "command_b_id": isolation_summary.get("command_b_id"),
                        "command_a_ack_state": isolation_summary.get("command_a_ack_state"),
                        "command_b_ack_state": isolation_summary.get("command_b_ack_state"),
                        "terminal_ack_ids": isolation_summary.get("terminal_ack_ids"),
                        "cursor_before": isolation_summary.get("cursor_before"),
                        "cursor_after_interleaving": isolation_summary.get("cursor_after_interleaving"),
                        "cursor_invariant": isolation_summary.get("cursor_invariant"),
                        "ack_invariant": isolation_summary.get("ack_invariant"),
                        "delivery_success": False,
                        "production_ready": False,
                        "overall_status": "passed",
                        "staleness": isolation_summary.get("staleness"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            state = str(isolation_summary.get("state") or "invalid")
            checks.append(
                _check(
                    "transaction_isolation",
                    "blocked",
                    f"transaction_isolation_artifact_{state}",
                    str(isolation_summary.get("safe_summary") or "Transaction isolation drill 软件证明产物不可用。"),
                    str(isolation_summary.get("retry_hint") or "重新生成 transaction isolation artifact 后重跑 preflight。"),
                    {
                        "artifact_present": True,
                        "reason_code": isolation_summary.get("reason_code", "transaction_isolation_invalid"),
                        "software_proof_only": True,
                    },
                )
            )
    else:
        checks.append(
            _check(
                "transaction_isolation",
                "warning",
                "transaction_isolation_artifact_missing",
                "尚未提供 transaction isolation artifact，不能声明事务隔离软件证明。",
                "生成 transaction isolation artifact，并用 TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if production_recovery_artifact_path:
        # Production recovery gate 只校验 Docker/local artifact，不连接或修改真实生产备份/灾备资源。
        recovery_gate_summary = production_recovery_artifact_summary(production_recovery_artifact_path)
        if recovery_gate_summary.get("ok"):
            checks.append(
                _check(
                    "production_recovery",
                    "pass",
                    "local_production_recovery_artifact_valid",
                    "已找到通过 schema、checksum 和 phone-safe 校验的 production recovery artifact。",
                    "继续补真实生产备份策略、灾备恢复、多实例和生产 DB/queue 证据。",
                    {
                        "artifact_schema": PRODUCTION_RECOVERY_SCHEMA,
                        "schema_version": PRODUCTION_RECOVERY_SCHEMA_VERSION,
                        "local_backup_restore_status": recovery_gate_summary.get("local_backup_restore_status"),
                        "recovery_drill_status": recovery_gate_summary.get("recovery_drill_status"),
                        "production_backup_policy_status": recovery_gate_summary.get(
                            "production_backup_policy_status"
                        ),
                        "disaster_recovery_status": recovery_gate_summary.get("disaster_recovery_status"),
                        "state_backend_status": recovery_gate_summary.get("state_backend_status"),
                        "db_queue_status": recovery_gate_summary.get("db_queue_status"),
                        "multi_instance_status": recovery_gate_summary.get("multi_instance_status"),
                        "retention_status": recovery_gate_summary.get("retention_status"),
                        "restore_objective_status": recovery_gate_summary.get("restore_objective_status"),
                        "ack_semantics": recovery_gate_summary.get("ack_semantics"),
                        "production_ready": False,
                        "overall_status": "blocked",
                        "staleness": recovery_gate_summary.get("staleness"),
                        "software_proof_only": True,
                    },
                )
            )
        else:
            state = str(recovery_gate_summary.get("state") or "invalid")
            checks.append(
                _check(
                    "production_recovery",
                    "blocked",
                    f"production_recovery_artifact_{state}",
                    str(recovery_gate_summary.get("safe_summary") or "Production recovery gate 产物不可用。"),
                    str(recovery_gate_summary.get("retry_hint") or "重新生成 production recovery artifact 后重跑 preflight。"),
                    {
                        "artifact_present": True,
                        "reason_code": recovery_gate_summary.get("reason_code", "production_recovery_invalid"),
                        "software_proof_only": True,
                    },
                )
            )
    else:
        checks.append(
            _check(
                "production_recovery",
                "warning",
                "production_recovery_artifact_missing",
                "尚未提供 production recovery artifact，不能声明生产备份/灾备恢复软件证明。",
                "生成 production recovery artifact，并用 TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT 传给 preflight。",
                {"artifact_present": False, "software_proof_only": True},
            )
        )

    if _phone_safe_failure_ready():
        checks.append(
            _check(
                "phone_safe_output",
                "pass",
                "redaction_self_check_passed",
                "错误和 preflight 输出已通过敏感字段脱敏自检。",
                "后续新增字段时继续保持 phone-safe 自检。",
            )
        )
    else:
        checks.append(
            _check(
                "phone_safe_output",
                "blocked",
                "redaction_self_check_failed",
                "错误输出脱敏自检失败，不能展示给手机用户。",
                "先修复敏感字段过滤，再继续上线前检查。",
            )
        )

    overall = max((check["status"] for check in checks), key=_status_rank)
    production_ready = overall == "pass"
    retry_hint = "ready_for_external_production_probe" if production_ready else "fix_blocked_preflight_items"
    safe_summary = (
        "生产上线前配置 gate 通过，可进入外网/TLS/OSS/DB 实证。"
        if production_ready
        else "当前仅为 Docker/local 软件 proof，仍缺生产云、TLS、公网、OSS/CDN 或生产 state 证据。"
    )
    local_backup_drill_ok = any(
        check["name"] == "backup_restore_drill" and check["status"] == "pass"
        for check in checks
    )
    local_manifest_ok = any(
        check["name"] == "oss_cdn_manifest" and check["status"] == "pass"
        for check in checks
    )
    local_oss_cdn_live_probe_ok = any(
        check["name"] == "oss_cdn_live_probe" and check["status"] == "pass"
        for check in checks
    )
    local_network_recovery_ok = any(
        check["name"] == "network_recovery_drill" and check["status"] == "pass"
        for check in checks
    )
    local_credential_rotation_ok = any(
        check["name"] == "credential_rotation" and check["status"] == "pass"
        for check in checks
    )
    local_provisioning_audit_ok = any(
        check["name"] == "provisioning_audit" and check["status"] == "pass"
        for check in checks
    )
    local_production_store_queue_ok = any(
        check["name"] == "production_store_queue" and check["status"] == "pass"
        for check in checks
    )
    local_queue_ordering_drill_ok = any(
        check["name"] == "queue_ordering_drill" and check["status"] == "pass"
        for check in checks
    )
    local_transaction_isolation_ok = any(
        check["name"] == "transaction_isolation" and check["status"] == "pass"
        for check in checks
    )
    local_production_recovery_ok = any(
        check["name"] == "production_recovery" and check["status"] == "pass"
        for check in checks
    )
    local_cloud_external_probe_ok = any(
        check["name"] == "cloud_external_probe_bundle" and check["status"] == "pass"
        for check in checks
    )
    local_cloud_public_ingress_tls_seen = any(
        check["name"] == "cloud_public_ingress_tls"
        and check["code"]
        in {"missing_public_ingress_tls_config", "public_ingress_tls_config_present_not_externally_proven"}
        for check in checks
    )
    local_cloud_db_queue_config_seen = any(
        check["name"] == "cloud_db_queue_config"
        and check["code"]
        in {"missing_cloud_db_queue_config", "cloud_db_queue_config_present_not_externally_proven"}
        for check in checks
    )
    local_cloud_db_queue_external_probe_ok = any(
        check["name"] == "cloud_db_queue_external_probe_bundle" and check["status"] == "pass"
        for check in checks
    )
    local_cloud_worker_migration_rehearsal_ok = any(
        check["name"] == "cloud_worker_migration_rehearsal" and check["status"] == "pass"
        for check in checks
    )
    local_external_evidence_intake_ok = any(
        check["name"] == "external_evidence_intake" and check["status"] == "pass"
        for check in checks
    )
    local_cloud_db_queue_config_boundary = local_cloud_db_queue_config_seen and (
        bool(cloud_db_queue_config_artifact_path) or not bool(cloud_public_ingress_tls_artifact_path)
    )
    not_proven = [
        "production_credential_rotation",
        "production_robot_provisioning",
        "real_sts_issuance",
        "real_audit_log_sink",
        "real_oss_upload",
        "sts_issuance",
        "cdn_origin_fetch",
        "lifecycle_policy",
        "production_account",
        "real_cloud",
        "real_https_tls",
        "real_4g_sim",
        "https_tls_public_ingress",
        "production_db_or_queue",
        "production_queue_ordering",
        "multi_instance_consistency",
        "production_transaction_isolation",
        "production_backup_policy",
        "real_disaster_recovery",
        "delivery_success",
        "nav2_or_fixed_route_delivery",
        "wave_rover_or_hil",
    ]
    if not local_backup_drill_ok:
        not_proven.insert(8, "backup_restore")
    if not local_network_recovery_ok:
        not_proven.insert(9, "network_recovery_drill")
    if not local_credential_rotation_ok:
        not_proven.insert(10, "credential_rotation_gate")
    if not local_provisioning_audit_ok:
        not_proven.insert(11, "provisioning_audit_gate")
    if not local_production_store_queue_ok:
        not_proven.insert(12, "production_store_queue_gate")
    if not local_queue_ordering_drill_ok:
        not_proven.insert(13, "queue_ordering_drill")
    if not local_transaction_isolation_ok:
        not_proven.insert(14, "transaction_isolation_drill")
    if not local_production_recovery_ok:
        not_proven.insert(15, "production_recovery_gate")
    if not local_cloud_external_probe_ok:
        not_proven.insert(16, "cloud_external_probe_bundle")
    if local_cloud_public_ingress_tls_seen:
        not_proven.insert(16, "cloud_public_ingress_tls_external_proof")
    if local_cloud_db_queue_config_seen:
        not_proven.insert(16, "cloud_db_queue_config_external_proof")
    if not local_cloud_db_queue_external_probe_ok:
        not_proven.insert(16, "cloud_db_queue_external_probe_bundle")
    if not local_cloud_worker_migration_rehearsal_ok:
        not_proven.insert(16, "cloud_worker_migration_rehearsal")
    if not local_oss_cdn_live_probe_ok:
        not_proven.insert(16, "oss_cdn_live_probe_gate")
    if not local_external_evidence_intake_ok:
        not_proven.insert(16, "external_evidence_intake_gate")
    payload = {
        "ok": production_ready,
        "software_proof_ready": bool(
            local_oss_cdn_live_probe_ok
            or local_external_evidence_intake_ok
            or local_network_recovery_ok
            or local_credential_rotation_ok
            or local_provisioning_audit_ok
            or local_production_store_queue_ok
            or local_queue_ordering_drill_ok
            or local_transaction_isolation_ok
            or local_production_recovery_ok
            or local_cloud_external_probe_ok
            or local_cloud_public_ingress_tls_seen
            or local_cloud_db_queue_config_seen
            or local_cloud_db_queue_external_probe_ok
            or local_cloud_worker_migration_rehearsal_ok
        ),
        "production_ready": production_ready,
        "service": "remote_cloud_relay",
        "protocol_version": PROTOCOL_VERSION,
        "evidence_boundary": (
            EXTERNAL_EVIDENCE_INTAKE_EVIDENCE_BOUNDARY
            if local_external_evidence_intake_ok
            else CLOUD_WORKER_MIGRATION_REHEARSAL_EVIDENCE_BOUNDARY
            if local_cloud_worker_migration_rehearsal_ok
            else OSS_CDN_LIVE_PROBE_EVIDENCE_BOUNDARY
            if local_oss_cdn_live_probe_ok
            else PRODUCTION_RECOVERY_EVIDENCE_BOUNDARY
            if local_production_recovery_ok
            else CLOUD_DB_QUEUE_EXTERNAL_PROBE_EVIDENCE_BOUNDARY
            if local_cloud_db_queue_external_probe_ok
            else CLOUD_EXTERNAL_PROBE_EVIDENCE_BOUNDARY
            if local_cloud_external_probe_ok
            else TRANSACTION_ISOLATION_EVIDENCE_BOUNDARY
            if local_transaction_isolation_ok
            else QUEUE_ORDERING_DRILL_EVIDENCE_BOUNDARY
            if local_queue_ordering_drill_ok
            else PRODUCTION_STORE_QUEUE_EVIDENCE_BOUNDARY
            if local_production_store_queue_ok
            else PROVISIONING_AUDIT_EVIDENCE_BOUNDARY
            if local_provisioning_audit_ok
            else CREDENTIAL_ROTATION_EVIDENCE_BOUNDARY
            if local_credential_rotation_ok
            else OSS_CDN_MANIFEST_EVIDENCE_BOUNDARY
            if local_manifest_ok
            else NETWORK_RECOVERY_EVIDENCE_BOUNDARY
            if local_network_recovery_ok
            else BACKUP_RESTORE_EVIDENCE_BOUNDARY
            if local_backup_drill_ok
            else CLOUD_DB_QUEUE_CONFIG_EVIDENCE_BOUNDARY
            if local_cloud_db_queue_config_boundary
            else CLOUD_PUBLIC_INGRESS_TLS_EVIDENCE_BOUNDARY
            if local_cloud_public_ingress_tls_seen
            else CLOUD_DEPLOYMENT_READINESS_EVIDENCE_BOUNDARY
        ),
        "overall_status": overall,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "checks": checks,
        "blocked_count": sum(1 for check in checks if check["status"] == "blocked"),
        "warning_count": sum(1 for check in checks if check["status"] == "warning"),
        "not_proven": not_proven,
    }
    if not production_ready:
        payload["error"] = phone_error("preflight_blocked", "production preflight is not ready")["error"]
    return safe_value(payload)


def _timestamp(value, field_name):
    try:
        timestamp = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a unix timestamp") from exc
    if timestamp <= 0:
        raise ValueError(f"{field_name} must be positive")
    return timestamp


def _robot_key(robot_id):
    key = str(robot_id or "").strip()
    if not key:
        raise ValueError("robot_id is required")
    return key


def normalize_command(robot_id, payload, *, now=None):
    # 云中转只接受行为层命令，拒绝任何低层速度或硬件控制形态。
    now = _now() if now is None else float(now)
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    protocol_version = str(payload.get("protocol_version") or PROTOCOL_VERSION).strip()
    command_id = str(payload.get("id") or f"cmd-{int(now * 1000)}-{uuid.uuid4().hex[:8]}").strip()
    command_type = str(payload.get("type") or "").strip()
    command_payload = payload.get("payload", {})
    expires_at = _timestamp(payload.get("expires_at", now + 300.0), "expires_at")
    if protocol_version != PROTOCOL_VERSION:
        raise ValueError(f"protocol_version must be {PROTOCOL_VERSION}")
    if not command_id:
        raise ValueError("id is required")
    if command_type not in COMMAND_TYPES:
        raise ValueError("type must be one of cancel, collect, confirm_dropoff")
    if not isinstance(command_payload, dict):
        raise ValueError("payload must be an object")
    if command_type == "collect" and not str(command_payload.get("target") or "").strip():
        raise ValueError("collect payload.target is required")
    return safe_value(
        {
            "protocol_version": PROTOCOL_VERSION,
            "robot_id": _robot_key(robot_id),
            "id": command_id,
            "type": command_type,
            "expires_at": expires_at,
            "payload": dict(command_payload),
            "created_at": now,
        }
    )


def normalize_status(robot_id, payload, *, now=None):
    # status 是手机继续展示任务状态的 surface，ACK 不能替代它。
    now = _now() if now is None else float(now)
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    protocol_version = str(payload.get("protocol_version") or PROTOCOL_VERSION).strip()
    state = str(payload.get("state") or "").strip()
    if protocol_version != PROTOCOL_VERSION:
        raise ValueError(f"protocol_version must be {PROTOCOL_VERSION}")
    if not state:
        raise ValueError("state is required")
    return safe_value(
        {
            "protocol_version": PROTOCOL_VERSION,
            "robot_id": _robot_key(robot_id),
            "state": state,
            "message": str(payload.get("message") or "").strip(),
            "updated_at": _timestamp(payload.get("updated_at", now), "updated_at"),
            "diagnostics": payload.get("diagnostics") if isinstance(payload.get("diagnostics"), dict) else {},
        }
    )


def normalize_ack(robot_id, command_id, payload, *, now=None):
    # terminal ACK 只代表 command envelope 被处理，不代表物理送达成功。
    now = _now() if now is None else float(now)
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object")
    protocol_version = str(payload.get("protocol_version") or PROTOCOL_VERSION).strip()
    state = str(payload.get("state") or "").strip()
    command_key = str(command_id or payload.get("command_id") or "").strip()
    if protocol_version != PROTOCOL_VERSION:
        raise ValueError(f"protocol_version must be {PROTOCOL_VERSION}")
    if state not in TERMINAL_ACK_STATES:
        raise ValueError("state must be one of acked, failed, ignored")
    if not command_key:
        raise ValueError("command_id is required")
    return safe_value(
        {
            "protocol_version": PROTOCOL_VERSION,
            "robot_id": _robot_key(robot_id),
            "command_id": command_key,
            "state": state,
            "message": str(payload.get("message") or "").strip(),
            "updated_at": _timestamp(payload.get("updated_at", now), "updated_at"),
            "result": payload.get("result") if isinstance(payload.get("result"), dict) else {},
        }
    )


class FileBackedRelayStore:
    """单机 proof store；它证明可恢复语义，不等于生产数据库。"""

    def __init__(self, state_path):
        self.state_path = os.path.expanduser(str(state_path or "")).strip()
        self._lock = threading.Lock()
        self._robots = {}
        if self.state_path:
            self._load()

    def _robot_locked(self, robot_id):
        robot_id = _robot_key(robot_id)
        return self._robots.setdefault(
            robot_id,
            {
                "commands": [],
                "command_index": {},
                "status": None,
                "acks": {},
                "stats": {"created_at": _now(), "updated_at": _now()},
            },
        )

    def _load(self):
        if not self.state_path or not os.path.exists(self.state_path):
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as state_file:
                payload = json.load(state_file)
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(payload, dict) or payload.get("schema") != STORE_SCHEMA:
            return
        robots = payload.get("robots")
        if not isinstance(robots, dict):
            return
        for robot_id, robot_payload in robots.items():
            if not isinstance(robot_payload, dict):
                continue
            commands = robot_payload.get("commands") if isinstance(robot_payload.get("commands"), list) else []
            acks = robot_payload.get("acks") if isinstance(robot_payload.get("acks"), dict) else {}
            status = robot_payload.get("status") if isinstance(robot_payload.get("status"), dict) else None
            safe_commands = [
                dict(command)
                for command in commands
                if isinstance(command, dict) and str(command.get("id") or "").strip()
            ]
            self._robots[str(robot_id)] = {
                "commands": safe_commands,
                "command_index": {str(command["id"]): command for command in safe_commands},
                "status": dict(status) if status else None,
                "acks": {
                    str(command_id): dict(ack)
                    for command_id, ack in acks.items()
                    if isinstance(ack, dict)
                },
                "stats": safe_value(robot_payload.get("stats") if isinstance(robot_payload.get("stats"), dict) else {}),
            }

    def _persist_locked(self):
        if not self.state_path:
            return
        state_dir = os.path.dirname(self.state_path) or "."
        os.makedirs(state_dir, exist_ok=True)
        robots = {}
        for robot_id, robot in self._robots.items():
            robots[robot_id] = {
                "commands": robot.get("commands", []),
                "status": robot.get("status"),
                "acks": robot.get("acks", {}),
                "stats": robot.get("stats", {}),
            }
        payload = {
            "schema": STORE_SCHEMA,
            "updated_at": _now(),
            "robots": safe_value(robots),
        }
        fd, tmp_path = tempfile.mkstemp(prefix=".remote-cloud-relay-", suffix=".json", dir=state_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(payload, tmp_file, ensure_ascii=False, sort_keys=True)
                tmp_file.write("\n")
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            os.replace(tmp_path, self.state_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def state_store_writable(self):
        # readiness 只证明 proof store 目录可写，不把真实 state path 回传给客户端。
        if not self.state_path:
            return False
        state_dir = os.path.dirname(self.state_path) or "."
        try:
            os.makedirs(state_dir, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(prefix=".remote-cloud-ready-", suffix=".tmp", dir=state_dir)
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                tmp_file.write("ready\n")
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            os.unlink(tmp_path)
            return True
        except OSError:
            return False

    def _touch_locked(self, robot, field):
        # stats 只用于 proof 复盘和容量估算，不参与业务状态判定。
        stats = robot.setdefault("stats", {})
        stats["updated_at"] = _now()
        stats[field] = int(stats.get(field, 0) or 0) + 1

    def submit_command(self, robot_id, payload):
        command = normalize_command(robot_id, payload)
        with self._lock:
            robot = self._robot_locked(robot_id)
            existing = robot["command_index"].get(command["id"])
            if existing:
                return 200, {"ok": True, "command": dict(existing), "duplicate": True}
            robot["commands"].append(command)
            robot["command_index"][command["id"]] = command
            self._touch_locked(robot, "command_count")
            self._persist_locked()
        return 201, {"ok": True, "command": dict(command), "duplicate": False}

    def next_command(self, robot_id, last_ack_id=""):
        now = _now()
        last_ack_id = str(last_ack_id or "").strip()
        with self._lock:
            robot = self._robot_locked(robot_id)
            start_index = 0
            if last_ack_id:
                for index, command in enumerate(robot["commands"]):
                    if command.get("id") == last_ack_id:
                        start_index = index + 1
                        break
            for command in robot["commands"][start_index:]:
                command_id = str(command.get("id") or "")
                if command_id in robot["acks"]:
                    continue
                if float(command.get("expires_at") or 0.0) < now:
                    continue
                return {"ok": True, "command": dict(command)}
        return {"ok": True, "command": None}

    def post_status(self, robot_id, payload):
        status = normalize_status(robot_id, payload)
        with self._lock:
            robot = self._robot_locked(robot_id)
            robot["status"] = status
            self._touch_locked(robot, "status_count")
            self._persist_locked()
        return {"ok": True, "status": dict(status)}

    def get_status(self, robot_id):
        with self._lock:
            robot = self._robot_locked(robot_id)
            status = dict(robot["status"]) if isinstance(robot.get("status"), dict) else None
        if not status:
            return 404, phone_error("status_missing", "robot has not posted status yet")
        age = max(0.0, _now() - float(status.get("updated_at") or 0.0))
        if age > STATUS_STALE_AFTER_SEC:
            status["status_age_sec"] = age
            return 409, phone_error("status_stale", "robot status is stale", status=status)
        return 200, {"ok": True, "status": status}

    def post_ack(self, robot_id, command_id, payload):
        ack = normalize_ack(robot_id, command_id, payload)
        with self._lock:
            robot = self._robot_locked(robot_id)
            robot["acks"][ack["command_id"]] = ack
            self._touch_locked(robot, "ack_count")
            self._persist_locked()
        return {"ok": True, "ack": dict(ack)}

    def get_ack(self, robot_id, command_id):
        with self._lock:
            robot = self._robot_locked(robot_id)
            ack = robot["acks"].get(str(command_id or "").strip())
        if not ack:
            return 404, phone_error("not_found", "ack not found")
        return 200, {"ok": True, "ack": dict(ack)}


class SQLiteRelayStore:
    """SQLite proof store；只证明单实例可恢复，不声明生产高可用。"""

    def __init__(self, state_path):
        self.state_path = os.path.expanduser(str(state_path or "")).strip()
        self._lock = threading.Lock()
        self._init_error = None
        # 初始化失败只记录为 phone-safe 状态，避免把本机路径或底层 sqlite 错误打到 HTTP 输出。
        if self.state_path:
            try:
                self._ensure_schema()
            except sqlite3.Error:
                self._init_error = "sqlite_state_store_unavailable"
            except OSError:
                self._init_error = "sqlite_state_store_unavailable"

    def _connect(self):
        if not self.state_path:
            raise sqlite3.OperationalError("sqlite state path is required")
        # timeout 防止 Docker/local smoke 中短暂锁冲突直接失败；单机 proof 不做多实例并发承诺。
        connection = sqlite3.connect(self.state_path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _session(self):
        # 所有 SQLite 调用都走这个入口，便于统一 commit/rollback/close 的生命周期。
        connection = self._connect()
        try:
            # sqlite3 的 connection context 只管 commit/rollback，不会自动 close，所以外层显式关闭。
            with connection:
                yield connection
        finally:
            connection.close()

    def _ensure_schema(self):
        state_dir = os.path.dirname(self.state_path) or "."
        os.makedirs(state_dir, exist_ok=True)
        with self._session() as connection:
            # schema 保持简单 JSON envelope，确保 HTTP API shape 仍由 normalize_* 控制。
            connection.execute("PRAGMA journal_mode=WAL")
            # robots 表只存最近 status 和 proof 统计，避免 ACK 或 command 状态被错误解读为任务结果。
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS robots (
                    robot_id TEXT PRIMARY KEY,
                    status_json TEXT,
                    stats_json TEXT NOT NULL DEFAULT '{}',
                    updated_at REAL NOT NULL
                )
                """
            )
            # commands 表保留原始 normalized command JSON，idempotency 由 (robot_id, command_id) 保证。
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS commands (
                    robot_id TEXT NOT NULL,
                    command_id TEXT NOT NULL,
                    command_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    PRIMARY KEY (robot_id, command_id)
                )
                """
            )
            # acks 表只保存 terminal envelope ACK，不保存真实送达结果，手机仍需继续读 status。
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS acks (
                    robot_id TEXT NOT NULL,
                    command_id TEXT NOT NULL,
                    ack_json TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (robot_id, command_id)
                )
                """
            )

    def _ensure_ready(self):
        # 业务读写前再检查一次，保证初始化失败能转成统一 phone-safe 错误。
        if self._init_error or not self.state_path:
            raise ValueError("sqlite state store is not ready")
        try:
            self._ensure_schema()
        except (sqlite3.Error, OSError) as exc:
            self._init_error = "sqlite_state_store_unavailable"
            raise ValueError("sqlite state store is not ready") from exc

    def _touch(self, connection, robot_id, field):
        # stats 只支撑 proof 复盘，不参与 command/status/ack 的业务契约。
        now = _now()
        row = connection.execute("SELECT stats_json FROM robots WHERE robot_id = ?", (robot_id,)).fetchone()
        stats = {}
        if row and row["stats_json"]:
            try:
                # stats 损坏不能影响主路径恢复，最多丢弃 proof 计数重新累计。
                stats = json.loads(row["stats_json"])
            except json.JSONDecodeError:
                stats = {}
        stats["updated_at"] = now
        stats[field] = int(stats.get(field, 0) or 0) + 1
        connection.execute(
            """
            INSERT INTO robots (robot_id, status_json, stats_json, updated_at)
            VALUES (?, NULL, ?, ?)
            ON CONFLICT(robot_id) DO UPDATE SET stats_json = excluded.stats_json, updated_at = excluded.updated_at
            """,
            (robot_id, json.dumps(safe_value(stats), ensure_ascii=False, sort_keys=True), now),
        )

    def state_store_writable(self):
        # preflight/readyz 只返回布尔，不泄露 sqlite 文件路径或底层异常。
        if not self.state_path:
            return False
        try:
            with self._lock:
                self._ensure_schema()
                with self._session() as connection:
                    # 写入再删除探针可以覆盖目录权限、数据库文件权限和事务提交路径。
                    connection.execute("CREATE TABLE IF NOT EXISTS relay_write_probe (id INTEGER PRIMARY KEY)")
                    connection.execute("INSERT INTO relay_write_probe DEFAULT VALUES")
                    connection.execute("DELETE FROM relay_write_probe")
            self._init_error = None
            return True
        except (sqlite3.Error, OSError):
            self._init_error = "sqlite_state_store_unavailable"
            return False

    def submit_command(self, robot_id, payload):
        command = normalize_command(robot_id, payload)
        robot_key = command["robot_id"]
        with self._lock:
            self._ensure_ready()
            with self._session() as connection:
                # 先查幂等键，保持 file store 和 HTTP response 的 duplicate 语义一致。
                row = connection.execute(
                    "SELECT command_json FROM commands WHERE robot_id = ? AND command_id = ?",
                    (robot_key, command["id"]),
                ).fetchone()
                if row:
                    return 200, {"ok": True, "command": json.loads(row["command_json"]), "duplicate": True}
                # command JSON 已在 normalize_command 内脱敏，SQLite 不额外保存原始请求体。
                connection.execute(
                    """
                    INSERT INTO commands (robot_id, command_id, command_json, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        robot_key,
                        command["id"],
                        json.dumps(command, ensure_ascii=False, sort_keys=True),
                        float(command.get("created_at") or _now()),
                        float(command.get("expires_at") or 0.0),
                    ),
                )
                self._touch(connection, robot_key, "command_count")
        return 201, {"ok": True, "command": dict(command), "duplicate": False}

    def next_command(self, robot_id, last_ack_id=""):
        robot_key = _robot_key(robot_id)
        last_ack_id = str(last_ack_id or "").strip()
        now = _now()
        with self._lock:
            self._ensure_ready()
            with self._session() as connection:
                # command 顺序按 created_at 保持 robot polling 的队列体验，command_id 只做稳定兜底排序。
                rows = connection.execute(
                    """
                    SELECT command_id, command_json, expires_at
                    FROM commands
                    WHERE robot_id = ?
                    ORDER BY created_at ASC, command_id ASC
                    """,
                    (robot_key,),
                ).fetchall()
                start_index = 0
                if last_ack_id:
                    # last_ack_id 是 opaque cursor；找不到时沿用 file store 语义从头扫描未 ACK 命令。
                    for index, row in enumerate(rows):
                        if row["command_id"] == last_ack_id:
                            start_index = index + 1
                            break
                for row in rows[start_index:]:
                    # 已有 terminal ACK 的 command 不再返回，避免 robot 重复执行已收口 envelope。
                    ack_row = connection.execute(
                        "SELECT 1 FROM acks WHERE robot_id = ? AND command_id = ?",
                        (robot_key, row["command_id"]),
                    ).fetchone()
                    if ack_row or float(row["expires_at"] or 0.0) < now:
                        # 过期 command 保留在 proof 历史里，但不能再作为 next executable command。
                        continue
                    return {"ok": True, "command": json.loads(row["command_json"])}
        return {"ok": True, "command": None}

    def post_status(self, robot_id, payload):
        status = normalize_status(robot_id, payload)
        robot_key = status["robot_id"]
        with self._lock:
            self._ensure_ready()
            with self._session() as connection:
                # 先 touch 能保证 robot 行存在，再只更新 status_json，避免清空既有 command/ack。
                self._touch(connection, robot_key, "status_count")
                connection.execute(
                    """
                    UPDATE robots
                    SET status_json = ?, updated_at = ?
                    WHERE robot_id = ?
                    """,
                    (json.dumps(status, ensure_ascii=False, sort_keys=True), _now(), robot_key),
                )
        return {"ok": True, "status": dict(status)}

    def get_status(self, robot_id):
        robot_key = _robot_key(robot_id)
        with self._lock:
            self._ensure_ready()
            with self._session() as connection:
                # status 是手机持续展示 surface；缺失时返回 status_missing 而不是伪造健康状态。
                row = connection.execute(
                    "SELECT status_json FROM robots WHERE robot_id = ?",
                    (robot_key,),
                ).fetchone()
        status = json.loads(row["status_json"]) if row and row["status_json"] else None
        if not status:
            return 404, phone_error("status_missing", "robot has not posted status yet")
        age = max(0.0, _now() - float(status.get("updated_at") or 0.0))
        if age > STATUS_STALE_AFTER_SEC:
            # stale status 带回最后安全状态，方便手机解释“状态过期”而不是隐藏上下文。
            status["status_age_sec"] = age
            return 409, phone_error("status_stale", "robot status is stale", status=status)
        return 200, {"ok": True, "status": status}

    def post_ack(self, robot_id, command_id, payload):
        ack = normalize_ack(robot_id, command_id, payload)
        robot_key = ack["robot_id"]
        with self._lock:
            self._ensure_ready()
            with self._session() as connection:
                # ACK 可被同一 terminal command 覆盖，支持 robot retry 期间的幂等上报。
                connection.execute(
                    """
                    INSERT INTO acks (robot_id, command_id, ack_json, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(robot_id, command_id) DO UPDATE SET
                        ack_json = excluded.ack_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        robot_key,
                        ack["command_id"],
                        json.dumps(ack, ensure_ascii=False, sort_keys=True),
                        float(ack.get("updated_at") or _now()),
                    ),
                )
                self._touch(connection, robot_key, "ack_count")
        return {"ok": True, "ack": dict(ack)}

    def get_ack(self, robot_id, command_id):
        robot_key = _robot_key(robot_id)
        command_key = str(command_id or "").strip()
        with self._lock:
            self._ensure_ready()
            with self._session() as connection:
                # 读取 ACK 不做 delivery 推断；调用方必须继续依赖 status 判断任务进展。
                row = connection.execute(
                    "SELECT ack_json FROM acks WHERE robot_id = ? AND command_id = ?",
                    (robot_key, command_key),
                ).fetchone()
        if not row:
            return 404, phone_error("not_found", "ack not found")
        return 200, {"ok": True, "ack": json.loads(row["ack_json"])}

    def export_backup_data(self):
        # backup artifact 复用 normalized envelope，不导出 sqlite 文件路径或底层 WAL 细节。
        with self._lock:
            self._ensure_ready()
            with self._session() as connection:
                robot_ids = set()
                for table in ("robots", "commands", "acks"):
                    rows = connection.execute(f"SELECT DISTINCT robot_id FROM {table}").fetchall()
                    robot_ids.update(str(row["robot_id"]) for row in rows if row["robot_id"])

                robots = []
                command_count = 0
                status_count = 0
                ack_count = 0
                for robot_id in sorted(robot_ids):
                    robot_row = connection.execute(
                        "SELECT status_json FROM robots WHERE robot_id = ?",
                        (robot_id,),
                    ).fetchone()
                    status = json.loads(robot_row["status_json"]) if robot_row and robot_row["status_json"] else None
                    if status:
                        status_count += 1
                    command_rows = connection.execute(
                        """
                        SELECT command_json
                        FROM commands
                        WHERE robot_id = ?
                        ORDER BY created_at ASC, command_id ASC
                        """,
                        (robot_id,),
                    ).fetchall()
                    commands = [json.loads(row["command_json"]) for row in command_rows]
                    ack_rows = connection.execute(
                        """
                        SELECT ack_json
                        FROM acks
                        WHERE robot_id = ?
                        ORDER BY updated_at ASC, command_id ASC
                        """,
                        (robot_id,),
                    ).fetchall()
                    acks = [json.loads(row["ack_json"]) for row in ack_rows]
                    command_count += len(commands)
                    ack_count += len(acks)
                    robots.append(
                        {
                            "robot_id": robot_id,
                            "commands": commands,
                            "status": status,
                            "acks": acks,
                        }
                    )

        return safe_value(
            {
                "robots": robots,
                "counts": {
                    "robot_count": len(robots),
                    "command_count": command_count,
                    "status_count": status_count,
                    "ack_count": ack_count,
                },
            }
        )

    def import_backup_data(self, backup_data):
        # restore 只接受本模块生成的 JSON envelope；失败时由上层转成 phone-safe reason。
        if not isinstance(backup_data, dict):
            raise ValueError("backup data must be an object")
        robots = backup_data.get("robots")
        if not isinstance(robots, list):
            raise ValueError("backup data robots must be a list")
        with self._lock:
            self._ensure_ready()
            with self._session() as connection:
                # fresh restore path 正常为空；清表让重复演练在临时库内可重跑，不碰生产 state。
                connection.execute("DELETE FROM acks")
                connection.execute("DELETE FROM commands")
                connection.execute("DELETE FROM robots")
                for robot in robots:
                    if not isinstance(robot, dict):
                        raise ValueError("backup robot entry must be an object")
                    robot_id = _robot_key(robot.get("robot_id"))
                    status = robot.get("status") if isinstance(robot.get("status"), dict) else None
                    commands = robot.get("commands") if isinstance(robot.get("commands"), list) else []
                    acks = robot.get("acks") if isinstance(robot.get("acks"), list) else []
                    updated_at = _now()
                    connection.execute(
                        """
                        INSERT INTO robots (robot_id, status_json, stats_json, updated_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            robot_id,
                            json.dumps(safe_value(status), ensure_ascii=False, sort_keys=True) if status else None,
                            json.dumps({"restored_at": updated_at}, ensure_ascii=False, sort_keys=True),
                            updated_at,
                        ),
                    )
                    for command in commands:
                        if not isinstance(command, dict) or not str(command.get("id") or "").strip():
                            raise ValueError("backup command entry is invalid")
                        # command envelope 已脱敏，restore 保持原 id/created_at/expires_at 以验证 cursor 语义。
                        connection.execute(
                            """
                            INSERT INTO commands (robot_id, command_id, command_json, created_at, expires_at)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                robot_id,
                                str(command["id"]),
                                json.dumps(safe_value(command), ensure_ascii=False, sort_keys=True),
                                float(command.get("created_at") or updated_at),
                                float(command.get("expires_at") or 0.0),
                            ),
                        )
                    for ack in acks:
                        if not isinstance(ack, dict) or not str(ack.get("command_id") or "").strip():
                            raise ValueError("backup ack entry is invalid")
                        # ACK 仍只是 command envelope terminal state，restore 不把它升级成 delivery result。
                        connection.execute(
                            """
                            INSERT INTO acks (robot_id, command_id, ack_json, updated_at)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                robot_id,
                                str(ack["command_id"]),
                                json.dumps(safe_value(ack), ensure_ascii=False, sort_keys=True),
                                float(ack.get("updated_at") or updated_at),
                            ),
                        )


def build_relay_store(state_path, state_backend="file"):
    # HTTP handler 只依赖 store protocol；backend 切换不得影响外部 response shape。
    backend = str(state_backend or "file").strip()
    if backend == "sqlite":
        return SQLiteRelayStore(state_path)
    return FileBackedRelayStore(state_path)


def _write_json_artifact(artifact_path, payload):
    # artifact 写入也走临时文件 + replace，避免半写文件被误当成可恢复证据。
    artifact_path = os.path.expanduser(str(artifact_path or "")).strip()
    if not artifact_path:
        raise ValueError("backup artifact path is required")
    artifact_dir = os.path.dirname(artifact_path) or "."
    os.makedirs(artifact_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".remote-cloud-backup-", suffix=".json", dir=artifact_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(payload, tmp_file, ensure_ascii=False, sort_keys=True)
            tmp_file.write("\n")
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, artifact_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def create_sqlite_backup_artifact(state_path, artifact_path):
    # 本 helper 只支持 SQLite proof store；生产 DB/queue 备份策略必须另行验证。
    store = SQLiteRelayStore(state_path)
    backup_data = store.export_backup_data()
    counts = backup_data.get("counts", {})
    body = {
        "schema": BACKUP_ARTIFACT_SCHEMA,
        "version": BACKUP_ARTIFACT_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "evidence_boundary": BACKUP_RESTORE_EVIDENCE_BOUNDARY,
        "metadata": {
            "created_at": _now(),
            "source_backend": "sqlite",
            "robot_count": int(counts.get("robot_count", 0) or 0),
            "command_count": int(counts.get("command_count", 0) or 0),
            "status_count": int(counts.get("status_count", 0) or 0),
            "ack_count": int(counts.get("ack_count", 0) or 0),
            "phone_safe": True,
            "production_backup_policy": False,
            "real_disaster_recovery": False,
        },
        "data": backup_data,
    }
    artifact = dict(body)
    artifact["checksum"] = _sha256_checksum(body)
    _write_json_artifact(artifact_path, safe_value(artifact))
    return {
        "ok": True,
        "backup_status": "passed",
        "evidence_boundary": BACKUP_RESTORE_EVIDENCE_BOUNDARY,
        "safe_summary": "SQLite relay state backup artifact generated for Docker/local drill.",
        "retry_hint": "restore_artifact_into_fresh_sqlite_state",
        "artifact": {
            "schema": BACKUP_ARTIFACT_SCHEMA,
            "version": BACKUP_ARTIFACT_VERSION,
            "checksum": artifact["checksum"],
            "source_backend": "sqlite",
            "command_count": body["metadata"]["command_count"],
            "status_count": body["metadata"]["status_count"],
            "ack_count": body["metadata"]["ack_count"],
        },
        "not_proven": [
            "production_backup_policy",
            "real_disaster_recovery",
            "production_db_or_queue",
            "multi_instance_consistency",
            "real_cloud",
            "real_4g",
        ],
    }


def _load_backup_artifact(artifact_path):
    try:
        with open(os.path.expanduser(str(artifact_path or "")), "r", encoding="utf-8") as artifact_file:
            artifact = json.load(artifact_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("backup artifact could not be read") from exc
    if not isinstance(artifact, dict):
        raise ValueError("backup artifact must be an object")
    checksum = str(artifact.get("checksum") or "")
    body = {key: value for key, value in artifact.items() if key != "checksum"}
    if artifact.get("schema") != BACKUP_ARTIFACT_SCHEMA:
        raise ValueError("backup artifact schema mismatch")
    if artifact.get("version") != BACKUP_ARTIFACT_VERSION:
        raise ValueError("backup artifact version mismatch")
    if artifact.get("protocol_version") != PROTOCOL_VERSION:
        raise ValueError("backup artifact protocol mismatch")
    if artifact.get("evidence_boundary") != BACKUP_RESTORE_EVIDENCE_BOUNDARY:
        raise ValueError("backup artifact evidence boundary mismatch")
    if checksum != _sha256_checksum(body):
        raise ValueError("backup artifact checksum mismatch")
    data = artifact.get("data")
    if not isinstance(data, dict):
        raise ValueError("backup artifact data missing")
    return safe_value(artifact)


def backup_artifact_summary(artifact_path):
    # preflight 需要安全摘要而不是完整 artifact，避免把内部记录全部打到 readiness 输出。
    try:
        artifact = _load_backup_artifact(artifact_path)
    except ValueError as exc:
        return {
            "ok": False,
            "reason_code": "artifact_invalid",
            "safe_summary": _safe_error_reason(exc),
        }
    metadata = artifact.get("metadata", {})
    return {
        "ok": True,
        "source_backend": metadata.get("source_backend"),
        "command_count": int(metadata.get("command_count", 0) or 0),
        "status_count": int(metadata.get("status_count", 0) or 0),
        "ack_count": int(metadata.get("ack_count", 0) or 0),
        "evidence_boundary": artifact.get("evidence_boundary"),
    }


def restore_sqlite_backup_artifact(artifact_path, restore_state_path, *, overwrite=False):
    # restore 目标默认必须是 fresh path，避免 CLI 误覆盖生产 proof state。
    restore_state_path = os.path.expanduser(str(restore_state_path or "")).strip()
    if not restore_state_path:
        raise ValueError("restore state path is required")
    if os.path.exists(restore_state_path):
        if not overwrite:
            raise ValueError("restore state path must be fresh")
        os.unlink(restore_state_path)
    artifact = _load_backup_artifact(artifact_path)
    restore_store = SQLiteRelayStore(restore_state_path)
    restore_store.import_backup_data(artifact["data"])
    metadata = artifact.get("metadata", {})
    return {
        "ok": True,
        "restore_status": "passed",
        "evidence_boundary": BACKUP_RESTORE_EVIDENCE_BOUNDARY,
        "safe_summary": "Backup artifact restored into a fresh SQLite proof state.",
        "retry_hint": "run_restore_drill_validation",
        "restored": {
            "source_backend": metadata.get("source_backend"),
            "target_backend": "sqlite",
            "command_count": int(metadata.get("command_count", 0) or 0),
            "status_count": int(metadata.get("status_count", 0) or 0),
            "ack_count": int(metadata.get("ack_count", 0) or 0),
        },
        "not_proven": [
            "production_backup_policy",
            "real_disaster_recovery",
            "production_db_or_queue",
            "multi_instance_consistency",
            "real_cloud",
            "real_4g",
        ],
    }


def backup_restore_drill_payload(
    source_state_path,
    artifact_path,
    restore_state_path,
    *,
    robot_id="trashbot-001",
    overwrite=False,
):
    try:
        backup_result = create_sqlite_backup_artifact(source_state_path, artifact_path)
        restore_result = restore_sqlite_backup_artifact(artifact_path, restore_state_path, overwrite=overwrite)
        restored_store = SQLiteRelayStore(restore_state_path)
        status_code, status_payload = restored_store.get_status(robot_id)
        artifact = _load_backup_artifact(artifact_path)
        commands = []
        acks = []
        for robot in artifact.get("data", {}).get("robots", []):
            if robot.get("robot_id") == robot_id:
                commands = robot.get("commands", []) if isinstance(robot.get("commands"), list) else []
                acks = robot.get("acks", []) if isinstance(robot.get("acks"), list) else []
                break
        ack_ids = {str(ack.get("command_id")) for ack in acks if isinstance(ack, dict)}
        pending_command_id = next(
            (str(command.get("id")) for command in commands if str(command.get("id")) not in ack_ids),
            "",
        )
        acked_command_id = next(
            (str(ack.get("command_id")) for ack in acks if isinstance(ack, dict) and str(ack.get("command_id"))),
            "",
        )
        next_payload = restored_store.next_command(robot_id, "")
        if pending_command_id and next_payload.get("command", {}).get("id") != pending_command_id:
            raise ValueError("restored command cursor shape mismatch")
        if status_code != 200 or not status_payload.get("status"):
            raise ValueError("restored status shape mismatch")
        if acked_command_id:
            ack_code, ack_payload = restored_store.get_ack(robot_id, acked_command_id)
            if ack_code != 200 or ack_payload.get("ack", {}).get("command_id") != acked_command_id:
                raise ValueError("restored ack shape mismatch")
            cursor_payload = restored_store.next_command(robot_id, acked_command_id)
            if pending_command_id and cursor_payload.get("command", {}).get("id") != pending_command_id:
                raise ValueError("restored cursor semantics mismatch")
        return safe_value(
            {
                "ok": True,
                "backup_status": backup_result["backup_status"],
                "restore_status": restore_result["restore_status"],
                "drill_status": "passed",
                "service": "remote_cloud_relay",
                "protocol_version": PROTOCOL_VERSION,
                "evidence_boundary": BACKUP_RESTORE_EVIDENCE_BOUNDARY,
                "safe_summary": (
                    "SQLite backup/restore Docker/local drill passed; production backup policy "
                    "and real disaster recovery are still not proven."
                ),
                "retry_hint": "pass_to_remote_bridge_compatibility_acceptance",
                "checks": {
                    "artifact_checksum": True,
                    "restored_command_http_shape": bool(next_payload.get("ok")),
                    "restored_status_http_shape": status_code == 200,
                    "restored_ack_http_shape": bool(not acked_command_id or ack_payload.get("ok")),
                    "cursor_ack_conservative": True,
                    "phone_safe_output": _phone_safe_failure_ready(),
                },
                "counts": restore_result["restored"],
                "not_proven": [
                    "production_backup_policy",
                    "real_disaster_recovery",
                    "production_db_or_queue",
                    "multi_instance_consistency",
                    "real_cloud",
                    "real_4g",
                    "oss_upload",
                    "cdn_origin",
                    "formal_phone_ui",
                    "nav2_or_fixed_route",
                    "wave_rover_hil",
                ],
            }
        )
    except (ValueError, OSError, sqlite3.Error) as exc:
        return {
            "ok": False,
            "backup_status": "blocked",
            "restore_status": "blocked",
            "drill_status": "blocked",
            "service": "remote_cloud_relay",
            "protocol_version": PROTOCOL_VERSION,
            "evidence_boundary": BACKUP_RESTORE_EVIDENCE_BOUNDARY,
            "safe_summary": PHONE_COPY["backup_restore_blocked"],
            "retry_hint": "regenerate_backup_artifact_and_restore_to_fresh_sqlite_state",
            "error": phone_error("backup_restore_blocked", _safe_error_reason(exc))["error"],
            "not_proven": [
                "backup_restore",
                "production_backup_policy",
                "real_disaster_recovery",
                "production_db_or_queue",
                "multi_instance_consistency",
                "real_cloud",
                "real_4g",
            ],
        }


def readiness_payload(store, expected_token):
    # 这里的字段面向编排和未来手机 UI，避免输出 host/path/token 等部署细节。
    checks = {
        "protocol": PROTOCOL_VERSION == "trashbot.remote.v1",
        "credential_gate": bool(str(expected_token or "").strip()),
        "state_store": store.state_store_writable(),
        "phone_safe_failure": _phone_safe_failure_ready(),
    }
    ready = all(checks.values())
    payload = {
        "ok": ready,
        "service": "remote_cloud_relay",
        "protocol_version": PROTOCOL_VERSION,
        "evidence_boundary": DEPLOY_EVIDENCE_BOUNDARY,
        "checks": checks,
        "safe_phone_copy": "云端中转服务已就绪。" if ready else PHONE_COPY["not_ready"],
    }
    if ready:
        return 200, payload
    payload["error"] = phone_error("not_ready", "relay readiness check failed")["error"]
    return 503, payload


def _route(path):
    parts = [part for part in str(path or "").strip("/").split("/") if part]
    if len(parts) < 3 or parts[0] != "robots":
        return None
    robot_id = parts[1]
    if parts[2:] == ["commands"]:
        return "commands", robot_id, ""
    if parts[2:] == ["commands", "next"]:
        return "commands_next", robot_id, ""
    if parts[2:] == ["status"]:
        return "status", robot_id, ""
    if len(parts) == 5 and parts[2] == "commands" and parts[4] == "ack":
        return "ack", robot_id, parts[3]
    return None


def _mobile_web_root():
    # Docker 或本地开发可以显式指定目录；默认按仓库布局向上找到 mobile/web。
    override = str(os.environ.get("TRASHBOT_REMOTE_CLOUD_MOBILE_WEB_ROOT") or "").strip()
    if override:
        return pathlib.Path(override)
    module_path = pathlib.Path(__file__).resolve()
    for parent in module_path.parents:
        candidate = parent / "mobile" / "web"
        # 只检查目录是否存在，不把绝对路径写入任何 HTTP 响应。
        if candidate.is_dir():
            return candidate
    return module_path.parents[4] / "mobile" / "web"


def _static_content_type(filename):
    suffix = pathlib.PurePosixPath(filename).suffix.lstrip(".")
    return MOBILE_WEB_CONTENT_TYPES.get(suffix, "application/octet-stream")


def _resolve_mobile_web_asset(path):
    raw_path = unquote(str(path or ""))
    if raw_path in ("", "/"):
        relative_name = "index.html"
    else:
        # URL path 必须是单个静态文件名；不接受子目录、反斜杠或 traversal 变体。
        relative_name = raw_path.lstrip("/")
    if "\\" in relative_name:
        return None
    parts = pathlib.PurePosixPath(relative_name).parts
    if len(parts) != 1 or any(part in ("", ".", "..") for part in parts):
        return None
    if relative_name not in MOBILE_WEB_STATIC_FILES:
        return None

    root = _mobile_web_root()
    root_resolved = root.resolve(strict=False)
    candidate = (root / relative_name).resolve(strict=False)
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        # 即使路径被编码绕过，失败也只返回 phone-safe 404，不暴露本地目录。
        return None
    if not candidate.is_file():
        return None
    return candidate, _static_content_type(relative_name)


def _default_mobile_web_robot_id():
    # 同源手机壳没有 URL 参数时也要有稳定 robot_id，避免前端收到 404 后直接离线。
    return str(os.environ.get("TRASHBOT_REMOTE_CLOUD_DEFAULT_ROBOT_ID") or "trashbot-001").strip() or "trashbot-001"


def _fail_closed_command_safety(reason):
    # 这是 cloud-hosted shell 的只读 gate，不是 command/status/ACK 主契约的一部分。
    action = {
        "enabled": False,
        "blocking_reason": reason,
        "recovery_hint": "等待机器人上报安全状态；本 gate 只证明 Docker/local phone-safe adapter。",
    }
    return {
        "schema": "trashbot.command_safety.v1",
        "overall_status": "blocked",
        "safe_phone_copy": "云端托管手机壳只提供只读状态；主操作保持禁用。",
        "global_block_reason": reason,
        "ack_semantics": "ACK 只代表 accepted/processing evidence，不代表送达、投放或取消完成。",
        "actions": {
            "start": dict(action),
            "confirm_dropoff": dict(action),
            "cancel": dict(action),
        },
    }


def cloud_hosted_mobile_web_status_payload(store, robot_id=None):
    # 手机同源 API 只读取 relay store 的最近状态；缺失或过期都转成 blocked 页面状态。
    robot_key = _robot_key(robot_id or _default_mobile_web_robot_id())
    status_code, store_payload = store.get_status(robot_key)
    latest_status = store_payload.get("status") if isinstance(store_payload, dict) else None
    latest_status = safe_value(latest_status) if isinstance(latest_status, dict) else None
    if status_code == 200 and latest_status:
        state = str(latest_status.get("state") or "status_present")
        reason = "cloud-hosted mobile web gate keeps primary actions fail-closed."
        safe_phone_copy = "已读取 relay 最近状态；云端托管手机壳仍保持主操作安全关闭。"
    elif latest_status:
        state = "status_stale"
        reason = "robot status is stale; cloud-hosted mobile web gate keeps actions disabled."
        safe_phone_copy = "relay 中只有过期状态；请等待机器人重新上报。"
    else:
        state = "status_missing"
        reason = "robot has not posted status to relay yet."
        safe_phone_copy = "relay 尚未收到机器人状态；请等待机器人上线或检查桥接。"

    command_safety = _fail_closed_command_safety(reason)
    phone_readiness = {
        "schema": CLOUD_HOSTED_MOBILE_WEB_GATE_SCHEMA,
        "schema_version": CLOUD_HOSTED_MOBILE_WEB_GATE_SCHEMA_VERSION,
        "primary_state": "blocked",
        "can_continue": False,
        "safe_phone_copy": safe_phone_copy,
        "recovery_hint": "这只是 Docker/local software proof；真实公网、手机和机器人联调仍未证明。",
        "next_action": "wait_for_robot_status",
        "support_level": "support_required",
        "evidence_boundary": CLOUD_HOSTED_MOBILE_WEB_EVIDENCE_BOUNDARY,
        "cloud_hosted_mobile_web_gate": {
            "overall_status": "blocked",
            "production_ready": False,
            "adapter": "phone_safe_status_diagnostics",
            "safe_summary": "托管静态壳 + phone-safe /api/status 和 /api/diagnostics fail-closed adapter。",
        },
        "action_permissions": {
            "can_collect": False,
            "can_confirm_dropoff": False,
            "can_cancel": False,
        },
        "command_safety": command_safety,
        "not_proven": list(CLOUD_HOSTED_MOBILE_WEB_NOT_PROVEN),
    }
    return safe_value(
        {
            "ok": True,
            "schema": CLOUD_HOSTED_MOBILE_WEB_GATE_SCHEMA,
            "schema_version": CLOUD_HOSTED_MOBILE_WEB_GATE_SCHEMA_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "robot_id": robot_key,
            "state": state,
            "overall_status": "blocked",
            "production_ready": False,
            "can_collect": False,
            "can_confirm_dropoff": False,
            "can_cancel": False,
            "command_safety": command_safety,
            "phone_readiness": phone_readiness,
            "safe_phone_copy": safe_phone_copy,
            "recovery_hint": phone_readiness["recovery_hint"],
            "evidence_boundary": CLOUD_HOSTED_MOBILE_WEB_EVIDENCE_BOUNDARY,
            "not_proven": list(CLOUD_HOSTED_MOBILE_WEB_NOT_PROVEN),
            "latest_status": latest_status,
        }
    )


def cloud_hosted_mobile_web_diagnostics_payload(store, robot_id=None):
    # diagnostics 复用 status adapter，保证用户看到的 gate 和支持人员复制的摘要一致。
    status_payload = cloud_hosted_mobile_web_status_payload(store, robot_id)
    return safe_value(
        {
            "ok": True,
            "schema": CLOUD_HOSTED_MOBILE_WEB_GATE_SCHEMA,
            "schema_version": CLOUD_HOSTED_MOBILE_WEB_GATE_SCHEMA_VERSION,
            "robot_id": status_payload["robot_id"],
            "overall_status": "blocked",
            "production_ready": False,
            "cloud_hosted_mobile_web_gate": status_payload["phone_readiness"]["cloud_hosted_mobile_web_gate"],
            "phone_safe_summary": {
                "state": status_payload["state"],
                "safe_phone_copy": status_payload["safe_phone_copy"],
                "recovery_hint": status_payload["recovery_hint"],
                "can_collect": False,
                "can_confirm_dropoff": False,
                "can_cancel": False,
            },
            "phone_readiness": status_payload["phone_readiness"],
            "command_safety": status_payload["command_safety"],
            "latest_status": status_payload.get("latest_status"),
            "evidence_boundary": CLOUD_HOSTED_MOBILE_WEB_EVIDENCE_BOUNDARY,
            "not_proven": list(CLOUD_HOSTED_MOBILE_WEB_NOT_PROVEN),
        }
    )


def _bearer_header(headers):
    # 只接受标准 Bearer 格式，失败时不回显原始 Authorization header。
    value = str(headers.get("Authorization") or headers.get("authorization") or "").strip()
    prefix = "Bearer "
    if not value.startswith(prefix):
        return ""
    return value[len(prefix):].strip()


def parse_json_body(handler):
    try:
        length = int(handler.headers.get("Content-Length") or 0)
    except ValueError as exc:
        raise ValueError("malformed content length") from exc
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError("malformed_json") from exc
    if not isinstance(payload, dict):
        raise TypeError("JSON body must be an object")
    return payload


def make_handler(store, bearer_token):
    expected_token = str(bearer_token or "").strip()

    class RelayHandler(BaseHTTPRequestHandler):
        server_version = "TrashbotRemoteCloudRelay/1"

        def log_message(self, format, *args):
            # 默认 HTTP server 会把路径打到 stderr；测试 proof 中保持安静并避免误写敏感查询。
            return

        def _send_json(self, status_code, payload):
            data = json.dumps(safe_value(payload), ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_static_asset(self, asset):
            asset_path, content_type = asset
            try:
                data = asset_path.read_bytes()
            except OSError:
                self._send_json(404, phone_error("not_found", "static shell asset not found"))
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            # 静态壳可缓存；service worker 已明确绕过 API、commands 和 ACK 控制面请求。
            self.send_header("Cache-Control", "public, max-age=300")
            self.send_header("X-Trashbot-Evidence-Boundary", CLOUD_HOSTED_MOBILE_WEB_EVIDENCE_BOUNDARY)
            self.end_headers()
            self.wfile.write(data)

        def _authorized(self):
            if not expected_token:
                return True
            return _bearer_header(self.headers) == expected_token

        def _reject_auth(self):
            self._send_json(401, phone_error("auth_failed", "remote control authorization failed"))

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/healthz":
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "service": "remote_cloud_relay",
                        "protocol_version": PROTOCOL_VERSION,
                        "evidence_boundary": DEPLOY_EVIDENCE_BOUNDARY,
                    },
                )
                return
            if parsed.path == "/readyz":
                status_code, payload = readiness_payload(store, expected_token)
                self._send_json(status_code, payload)
                return
            if parsed.path == "/preflightz":
                # preflightz 是旁路 gate，不需要读取或修改 command/status/ack 主路径。
                payload = production_preflight_payload()
                self._send_json(200 if payload.get("production_ready") else 503, payload)
                return
            if parsed.path == "/api/status":
                # 手机静态壳的同源状态 API 不要求 bearer；它只输出脱敏 blocked 摘要。
                self._send_json(200, cloud_hosted_mobile_web_status_payload(store))
                return
            if parsed.path == "/api/diagnostics":
                # diagnostics 给支持人员复现 blocked 状态，不能泄露 token、路径或 ROS/硬件细节。
                self._send_json(200, cloud_hosted_mobile_web_diagnostics_payload(store))
                return
            route = _route(parsed.path)
            if not route:
                if parsed.path in CONTROL_PATHS or parsed.path.startswith(CONTROL_PATH_PREFIXES):
                    # API/probe/control 路由必须优先，避免静态 fallback 把控制面错误伪装成页面。
                    self._send_json(404, phone_error("not_found", "path not found"))
                    return
                asset = _resolve_mobile_web_asset(parsed.path)
                if asset:
                    self._send_static_asset(asset)
                    return
                self._send_json(404, phone_error("not_found", "path not found"))
                return
            if not self._authorized():
                self._reject_auth()
                return
            route_name, robot_id, command_id = route
            query = parse_qs(parsed.query)
            try:
                if route_name == "commands_next":
                    payload = store.next_command(robot_id, next(iter(query.get("last_ack_id", [])), ""))
                    self._send_json(200, payload)
                    return
                if route_name == "status":
                    status_code, payload = store.get_status(robot_id)
                    self._send_json(status_code, payload)
                    return
                if route_name == "ack":
                    status_code, payload = store.get_ack(robot_id, command_id)
                    self._send_json(status_code, payload)
                    return
            except ValueError as exc:
                self._send_json(400, phone_error("bad_request", str(exc)))
                return
            self._send_json(405, phone_error("bad_request", "method is not supported for this path"))

        def do_POST(self):
            parsed = urlparse(self.path)
            route = _route(parsed.path)
            if not route:
                self._send_json(404, phone_error("not_found", "path not found"))
                return
            if not self._authorized():
                self._reject_auth()
                return
            try:
                body = parse_json_body(self)
            except ValueError:
                self._send_json(400, phone_error("malformed_json", "request body was not valid JSON"))
                return
            except TypeError as exc:
                self._send_json(400, phone_error("bad_request", str(exc)))
                return
            route_name, robot_id, command_id = route
            try:
                if route_name == "commands":
                    status_code, payload = store.submit_command(robot_id, body)
                    self._send_json(status_code, payload)
                    return
                if route_name == "status":
                    self._send_json(200, store.post_status(robot_id, body))
                    return
                if route_name == "ack":
                    self._send_json(200, store.post_ack(robot_id, command_id, body))
                    return
            except ValueError as exc:
                self._send_json(400, phone_error("bad_request", str(exc)))
                return
            self._send_json(405, phone_error("bad_request", "method is not supported for this path"))

    return RelayHandler


def build_server(host, port, state_path, bearer_token, state_backend="file"):
    store = build_relay_store(state_path, state_backend)
    return ThreadingHTTPServer((host, int(port)), make_handler(store, bearer_token))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Trashbot independent remote cloud relay proof service")
    parser.add_argument("--host", default=os.environ.get("TRASHBOT_REMOTE_CLOUD_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("TRASHBOT_REMOTE_CLOUD_PORT", "8088")))
    parser.add_argument(
        "--state-path",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_STATE", "remote_cloud_relay_state.json"),
    )
    parser.add_argument(
        "--state-backend",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_STATE_BACKEND", "file"),
        choices=("file", "sqlite"),
        help="single-node proof state backend; production DB/queue is still out of scope",
    )
    parser.add_argument("--bearer-token", default=os.environ.get("TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN", ""))
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="run production preflight gate as machine-readable JSON and exit",
    )
    parser.add_argument(
        "--oss-cdn-manifest-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT", ""),
        help="phone-safe OSS/CDN manifest artifact consumed by preflight",
    )
    parser.add_argument(
        "--oss-cdn-live-probe-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT", ""),
        help="phone-safe OSS/CDN live probe artifact consumed by preflight",
    )
    parser.add_argument(
        "--network-recovery-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT", ""),
        help="phone-safe network recovery drill artifact consumed by preflight",
    )
    parser.add_argument(
        "--credential-rotation-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT", ""),
        help="phone-safe credential rotation artifact consumed by preflight",
    )
    parser.add_argument(
        "--provisioning-audit-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT", ""),
        help="phone-safe provisioning / STS / audit artifact consumed by preflight",
    )
    parser.add_argument(
        "--production-store-queue-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT", ""),
        help="phone-safe production store/queue artifact consumed by preflight",
    )
    parser.add_argument(
        "--queue-ordering-drill-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT", ""),
        help="phone-safe queue ordering drill artifact consumed by preflight",
    )
    parser.add_argument(
        "--transaction-isolation-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT", ""),
        help="phone-safe transaction isolation drill artifact consumed by preflight",
    )
    parser.add_argument(
        "--production-recovery-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT", ""),
        help="phone-safe production recovery gate artifact consumed by preflight",
    )
    parser.add_argument(
        "--cloud-deployment-readiness-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_READINESS_ARTIFACT", ""),
        help="phone-safe cloud deployment readiness artifact consumed by preflight",
    )
    parser.add_argument(
        "--cloud-external-probe-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_ARTIFACT", ""),
        help="phone-safe cloud external probe bundle artifact consumed by preflight",
    )
    parser.add_argument(
        "--cloud-public-ingress-tls-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT", ""),
        help="phone-safe public ingress/TLS/reverse-proxy artifact consumed by preflight",
    )
    parser.add_argument(
        "--cloud-db-queue-config-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_DB_QUEUE_CONFIG_ARTIFACT", ""),
        help="phone-safe cloud DB/queue config artifact consumed by preflight",
    )
    parser.add_argument(
        "--cloud-db-queue-external-probe-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_DB_QUEUE_EXTERNAL_PROBE_ARTIFACT", ""),
        help="phone-safe cloud DB/queue external probe bundle artifact consumed by preflight",
    )
    parser.add_argument(
        "--external-evidence-intake-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT", ""),
        help="phone-safe external evidence intake artifact consumed by preflight",
    )
    parser.add_argument(
        "--cloud-worker-migration-rehearsal-artifact",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT", ""),
        help="phone-safe cloud worker/migration rehearsal artifact consumed by preflight",
    )
    parser.add_argument(
        "--write-oss-cdn-manifest",
        default="",
        help="write a phone-safe OSS/CDN object reference manifest artifact JSON and exit",
    )
    parser.add_argument(
        "--write-oss-cdn-live-probe-artifact",
        default="",
        help="write a phone-safe OSS/CDN live probe artifact JSON and exit",
    )
    parser.add_argument(
        "--write-credential-rotation-artifact",
        default="",
        help="write a phone-safe credential rotation gate artifact JSON and exit",
    )
    parser.add_argument(
        "--write-provisioning-audit-artifact",
        default="",
        help="write a phone-safe provisioning / STS / audit gate artifact JSON and exit",
    )
    parser.add_argument(
        "--write-production-store-queue-artifact",
        default="",
        help="write a phone-safe production store/queue gate artifact JSON and exit",
    )
    parser.add_argument(
        "--write-queue-ordering-drill-artifact",
        default="",
        help="write a phone-safe queue ordering drill artifact JSON and exit",
    )
    parser.add_argument(
        "--write-transaction-isolation-artifact",
        default="",
        help="write a phone-safe transaction isolation drill artifact JSON and exit",
    )
    parser.add_argument(
        "--write-production-recovery-artifact",
        default="",
        help="write a phone-safe production recovery gate artifact JSON and exit",
    )
    parser.add_argument(
        "--write-cloud-deployment-readiness-artifact",
        default="",
        help="write a phone-safe cloud deployment readiness artifact JSON and exit",
    )
    parser.add_argument(
        "--write-cloud-external-probe-artifact",
        default="",
        help="probe health/ready/preflight endpoints and write a phone-safe cloud external probe bundle artifact",
    )
    parser.add_argument(
        "--write-cloud-public-ingress-tls-artifact",
        default="",
        help="write a phone-safe public ingress/TLS/reverse-proxy config gate artifact",
    )
    parser.add_argument(
        "--write-cloud-db-queue-config-artifact",
        default="",
        help="write a phone-safe cloud DB/queue config gate artifact",
    )
    parser.add_argument(
        "--write-cloud-db-queue-external-probe-artifact",
        default="",
        help="write a phone-safe cloud DB/queue external probe bundle artifact",
    )
    parser.add_argument(
        "--write-external-evidence-intake-artifact",
        default="",
        help="write a phone-safe external evidence intake artifact",
    )
    parser.add_argument(
        "--write-cloud-worker-migration-rehearsal-artifact",
        default="",
        help="run a Docker/local SQLite worker/migration rehearsal and write a phone-safe artifact",
    )
    parser.add_argument(
        "--cloud-external-probe-base-url",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_BASE_URL", ""),
        help="base URL used only for live endpoint probing; it is not written into the artifact",
    )
    parser.add_argument(
        "--cloud-external-probe-timeout",
        type=float,
        default=float(os.environ.get("TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_TIMEOUT", "2.0")),
        help="per-endpoint probe timeout in seconds",
    )
    parser.add_argument(
        "--oss-cdn-live-probe-timeout",
        type=float,
        default=float(os.environ.get("TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_TIMEOUT", "2.0")),
        help="per-object OSS/CDN live probe timeout in seconds",
    )
    parser.add_argument(
        "--credential-rotation-robot-id",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ROBOT_ID", "robot-local-proof"),
        help="robot id embedded in generated credential rotation proof",
    )
    parser.add_argument(
        "--provisioning-audit-robot-id",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ROBOT_ID", "robot-local-proof"),
        help="robot id embedded in generated provisioning audit proof",
    )
    parser.add_argument(
        "--production-store-queue-robot-id",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ROBOT_ID", "robot-local-proof"),
        help="robot id embedded in generated production store/queue proof",
    )
    parser.add_argument(
        "--queue-ordering-drill-robot-id",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ROBOT_ID", "robot-local-proof"),
        help="robot id embedded in generated queue ordering drill proof",
    )
    parser.add_argument(
        "--transaction-isolation-robot-id",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ROBOT_ID", "robot-local-proof"),
        help="robot id embedded in generated transaction isolation proof",
    )
    parser.add_argument(
        "--production-recovery-robot-id",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ROBOT_ID", "robot-local-proof"),
        help="robot id embedded in generated production recovery proof",
    )
    parser.add_argument(
        "--cloud-worker-migration-rehearsal-robot-id",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ROBOT_ID", "robot-local-proof"),
        help="robot id embedded in generated cloud worker/migration rehearsal proof",
    )
    parser.add_argument(
        "--queue-ordering-drill-status",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_STATUS", "passed"),
        choices=("passed", "failed"),
        help="local drill status embedded in generated queue ordering proof",
    )
    parser.add_argument(
        "--transaction-isolation-status",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_STATUS", "passed"),
        choices=("passed", "failed"),
        help="local drill status embedded in generated transaction isolation proof",
    )
    parser.add_argument(
        "--production-recovery-status",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_STATUS", "passed"),
        choices=("passed", "failed"),
        help="local drill status embedded in generated production recovery proof",
    )
    parser.add_argument(
        "--manifest-robot-id",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_MANIFEST_ROBOT_ID", "robot-local-proof"),
        help="robot id embedded in generated OSS/CDN manifest proof",
    )
    parser.add_argument(
        "--manifest-task-id",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_MANIFEST_TASK_ID", "task-local-proof"),
        help="task id embedded in generated OSS/CDN manifest proof",
    )
    parser.add_argument(
        "--manifest-date",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_MANIFEST_DATE", ""),
        help="YYYY-MM-DD date embedded in generated OSS/CDN manifest proof",
    )
    parser.add_argument(
        "--backup-state-to",
        default="",
        help="write a phone-safe SQLite backup artifact JSON and exit",
    )
    parser.add_argument(
        "--restore-backup-from",
        default="",
        help="restore a backup artifact into --restore-state-path and exit",
    )
    parser.add_argument(
        "--restore-state-path",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_RESTORE_STATE", ""),
        help="fresh SQLite state path used by restore or backup/restore drill",
    )
    parser.add_argument(
        "--backup-restore-drill",
        action="store_true",
        help="run SQLite backup -> restore -> shape validation as JSON and exit",
    )
    parser.add_argument(
        "--network-recovery-drill",
        action="store_true",
        help="run Docker/local relay network recovery drill as JSON and exit",
    )
    parser.add_argument(
        "--write-network-recovery-artifact",
        default="",
        help="write a phone-safe network recovery drill artifact JSON and exit",
    )
    parser.add_argument(
        "--drill-robot-id",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_DRILL_ROBOT_ID", "trashbot-001"),
        help="robot id to validate after restore; output remains phone-safe",
    )
    parser.add_argument(
        "--overwrite-restore-state",
        action="store_true",
        help="delete the restore proof state before restoring; only for temp drill paths",
    )
    args = parser.parse_args(argv)
    if args.preflight:
        # CLI gate 用当前进程 env 评估 Docker/local production readiness，不启动 HTTP server。
        preflight_env = dict(os.environ)
        if args.oss_cdn_manifest_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT"] = args.oss_cdn_manifest_artifact
        if args.oss_cdn_live_probe_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT"] = (
                args.oss_cdn_live_probe_artifact
            )
        if args.network_recovery_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT"] = args.network_recovery_artifact
        if args.credential_rotation_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT"] = args.credential_rotation_artifact
        if args.provisioning_audit_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT"] = args.provisioning_audit_artifact
        if args.production_store_queue_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT"] = (
                args.production_store_queue_artifact
            )
        if args.queue_ordering_drill_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT"] = (
                args.queue_ordering_drill_artifact
            )
        if args.transaction_isolation_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT"] = (
                args.transaction_isolation_artifact
            )
        if args.production_recovery_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT"] = (
                args.production_recovery_artifact
            )
        if args.cloud_deployment_readiness_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_READINESS_ARTIFACT"] = (
                args.cloud_deployment_readiness_artifact
            )
        if args.cloud_external_probe_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_ARTIFACT"] = args.cloud_external_probe_artifact
        if args.cloud_public_ingress_tls_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT"] = (
                args.cloud_public_ingress_tls_artifact
            )
        if args.cloud_db_queue_config_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_DB_QUEUE_CONFIG_ARTIFACT"] = (
                args.cloud_db_queue_config_artifact
            )
        if args.cloud_db_queue_external_probe_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_DB_QUEUE_EXTERNAL_PROBE_ARTIFACT"] = (
                args.cloud_db_queue_external_probe_artifact
            )
        if args.external_evidence_intake_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT"] = (
                args.external_evidence_intake_artifact
            )
        if args.cloud_worker_migration_rehearsal_artifact:
            preflight_env["TRASHBOT_REMOTE_CLOUD_WORKER_MIGRATION_REHEARSAL_ARTIFACT"] = (
                args.cloud_worker_migration_rehearsal_artifact
            )
        payload = production_preflight_payload(preflight_env)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("production_ready") or payload.get("software_proof_ready") else 2
    if args.write_cloud_worker_migration_rehearsal_artifact:
        try:
            payload = create_cloud_worker_migration_rehearsal_artifact(
                args.write_cloud_worker_migration_rehearsal_artifact,
                args.state_path,
                robot_id=args.cloud_worker_migration_rehearsal_robot_id,
            )
        except (ValueError, OSError, sqlite3.Error) as exc:
            payload = phone_error("cloud_worker_migration_rehearsal_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_external_evidence_intake_artifact:
        try:
            payload = create_external_evidence_intake_artifact(
                args.write_external_evidence_intake_artifact,
                dict(os.environ),
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("external_evidence_intake_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_cloud_db_queue_external_probe_artifact:
        try:
            payload = create_cloud_db_queue_external_probe_bundle_artifact(
                args.write_cloud_db_queue_external_probe_artifact,
                dict(os.environ),
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("cloud_db_queue_external_probe_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_oss_cdn_live_probe_artifact:
        try:
            manifest_artifact = args.oss_cdn_manifest_artifact or os.environ.get(
                "TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT",
                "",
            )
            payload = create_oss_cdn_live_probe_artifact(
                args.write_oss_cdn_live_probe_artifact,
                manifest_artifact,
                timeout_sec=args.oss_cdn_live_probe_timeout,
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("oss_cdn_live_probe_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_cloud_db_queue_config_artifact:
        try:
            payload = create_cloud_db_queue_config_artifact(
                args.write_cloud_db_queue_config_artifact,
                dict(os.environ),
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("cloud_db_queue_config_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_cloud_public_ingress_tls_artifact:
        try:
            payload = create_cloud_public_ingress_tls_artifact(
                args.write_cloud_public_ingress_tls_artifact,
                dict(os.environ),
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("cloud_public_ingress_tls_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_cloud_external_probe_artifact:
        try:
            base_url = args.cloud_external_probe_base_url or os.environ.get(
                "TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL",
                "",
            )
            payload = create_cloud_external_probe_bundle_artifact(
                args.write_cloud_external_probe_artifact,
                base_url,
                timeout_sec=args.cloud_external_probe_timeout,
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("cloud_external_probe_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_cloud_deployment_readiness_artifact:
        try:
            payload = create_cloud_deployment_readiness_artifact(
                args.write_cloud_deployment_readiness_artifact,
                dict(os.environ),
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("cloud_deployment_readiness_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_production_recovery_artifact:
        try:
            payload = create_production_recovery_artifact(
                args.write_production_recovery_artifact,
                args.production_recovery_robot_id,
                drill_status=args.production_recovery_status,
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("production_recovery_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_transaction_isolation_artifact:
        try:
            payload = create_transaction_isolation_artifact(
                args.write_transaction_isolation_artifact,
                args.transaction_isolation_robot_id,
                drill_status=args.transaction_isolation_status,
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("transaction_isolation_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_queue_ordering_drill_artifact:
        try:
            payload = create_queue_ordering_drill_artifact(
                args.write_queue_ordering_drill_artifact,
                args.queue_ordering_drill_robot_id,
                drill_status=args.queue_ordering_drill_status,
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("queue_ordering_drill_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_production_store_queue_artifact:
        try:
            payload = create_production_store_queue_artifact(
                args.write_production_store_queue_artifact,
                args.production_store_queue_robot_id,
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("production_store_queue_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_provisioning_audit_artifact:
        try:
            payload = create_provisioning_audit_artifact(
                args.write_provisioning_audit_artifact,
                args.provisioning_audit_robot_id,
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("provisioning_audit_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_credential_rotation_artifact:
        try:
            payload = create_credential_rotation_artifact(
                args.write_credential_rotation_artifact,
                args.credential_rotation_robot_id,
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("credential_rotation_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.write_oss_cdn_manifest:
        try:
            payload = create_oss_cdn_manifest_artifact(
                args.write_oss_cdn_manifest,
                args.manifest_robot_id,
                args.manifest_task_id,
                date_text=args.manifest_date or None,
            )
        except (ValueError, OSError) as exc:
            payload = phone_error("oss_cdn_manifest_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.backup_restore_drill:
        # Drill 是 Docker/local 软件证明；它不启动 HTTP server，也不触碰真实云资源。
        payload = backup_restore_drill_payload(
            args.state_path,
            args.backup_state_to,
            args.restore_state_path,
            robot_id=args.drill_robot_id,
            overwrite=args.overwrite_restore_state,
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.network_recovery_drill:
        # Network recovery drill 只模拟本地连接失败和恢复，不触碰真实云、4G 或 ROS2 motion。
        if args.write_network_recovery_artifact:
            payload = create_network_recovery_artifact(
                args.write_network_recovery_artifact,
                args.state_path,
                state_backend=args.state_backend,
                robot_id=args.drill_robot_id,
            )
        else:
            payload = network_recovery_drill_payload(
                args.state_path,
                state_backend=args.state_backend,
                robot_id=args.drill_robot_id,
            )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok", payload.get("overall_status") == "passed") else 2
    if args.backup_state_to:
        try:
            payload = create_sqlite_backup_artifact(args.state_path, args.backup_state_to)
        except (ValueError, OSError, sqlite3.Error) as exc:
            payload = phone_error("backup_restore_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    if args.restore_backup_from:
        try:
            payload = restore_sqlite_backup_artifact(
                args.restore_backup_from,
                args.restore_state_path,
                overwrite=args.overwrite_restore_state,
            )
        except (ValueError, OSError, sqlite3.Error) as exc:
            payload = phone_error("backup_restore_blocked", _safe_error_reason(exc))
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("ok") else 2
    server = build_server(args.host, args.port, args.state_path, args.bearer_token, args.state_backend)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
