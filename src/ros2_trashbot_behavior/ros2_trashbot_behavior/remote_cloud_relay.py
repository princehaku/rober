import argparse
import json
import os
import sqlite3
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


PROTOCOL_VERSION = "trashbot.remote.v1"
STORE_SCHEMA = "trashbot.remote_cloud_relay_store.v1"
COMMAND_TYPES = {"collect", "confirm_dropoff", "cancel"}
TERMINAL_ACK_STATES = {"acked", "failed", "ignored"}
STATUS_STALE_AFTER_SEC = 90.0
PREFLIGHT_EVIDENCE_BOUNDARY = "software_proof_docker_preflight_gate"
SQLITE_EVIDENCE_BOUNDARY = "software_proof_docker_sqlite_state_store"
DEPLOY_EVIDENCE_BOUNDARY = "software_proof_docker_deploy"

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

# 对字符串也做保守脱敏，避免敏感内容藏在 message 或 diagnostics 里。
SENSITIVE_TEXT = (
    "authorization",
    "bearer ",
    "token",
    "secret",
    "password",
    "oss secret",
    "root password",
    "://",
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
            if any(marker in key_lc for marker in SENSITIVE_KEYS):
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
        "Authorization Bearer token leaked /cmd_vel ttyUSB0 baudrate https://secret.invalid",
        details={
            "authorization": "Bearer hidden",
            "serial_port": "/dev/ttyUSB0",
            "safe": "visible",
        },
    )
    encoded = json.dumps(sample, ensure_ascii=False)
    forbidden = ("Bearer", "token", "/cmd_vel", "ttyUSB", "baudrate", "https://secret")
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
    tls_mode_safe = _safe_enum(tls_mode, {"future_reverse_proxy", "terminated", "managed", "reverse_proxy"})
    ingress_mode_safe = _safe_enum(ingress_mode, {"missing", "private_only", "public_https"})
    oss_credential_mode_safe = _safe_enum(oss_credential_mode, {"placeholder", "sts", "restricted_ak", "managed_identity"})

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
    payload = {
        "ok": production_ready,
        "production_ready": production_ready,
        "service": "remote_cloud_relay",
        "protocol_version": PROTOCOL_VERSION,
        "evidence_boundary": SQLITE_EVIDENCE_BOUNDARY if state_backend_safe == "sqlite" else PREFLIGHT_EVIDENCE_BOUNDARY,
        "overall_status": overall,
        "safe_summary": safe_summary,
        "retry_hint": retry_hint,
        "checks": checks,
        "blocked_count": sum(1 for check in checks if check["status"] == "blocked"),
        "warning_count": sum(1 for check in checks if check["status"] == "warning"),
        "not_proven": [
            "real_cloud",
            "real_4g",
            "external_tls",
            "public_ingress",
            "oss_upload",
            "cdn_origin",
            "production_db_or_queue",
            "multi_instance_consistency",
            "backup_restore",
            "disaster_recovery",
            "nav2_or_fixed_route",
            "wave_rover_hil",
        ],
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


def build_relay_store(state_path, state_backend="file"):
    # HTTP handler 只依赖 store protocol；backend 切换不得影响外部 response shape。
    backend = str(state_backend or "file").strip()
    if backend == "sqlite":
        return SQLiteRelayStore(state_path)
    return FileBackedRelayStore(state_path)


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
            route = _route(parsed.path)
            if not route:
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
    args = parser.parse_args(argv)
    if args.preflight:
        # CLI gate 用当前进程 env 评估 Docker/local production readiness，不启动 HTTP server。
        payload = production_preflight_payload()
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("production_ready") else 2
    server = build_server(args.host, args.port, args.state_path, args.bearer_token, args.state_backend)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
