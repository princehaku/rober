import argparse
import json
import os
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


PROTOCOL_VERSION = "trashbot.remote.v1"
STORE_SCHEMA = "trashbot.remote_cloud_relay_store.v1"
COMMAND_TYPES = {"collect", "confirm_dropoff", "cancel"}
TERMINAL_ACK_STATES = {"acked", "failed", "ignored"}
STATUS_STALE_AFTER_SEC = 90.0

# 这些文案直接给手机 UI 使用，不能夹带 HTTP 栈、ROS 话题、串口或凭证细节。
PHONE_COPY = {
    "auth_failed": "手机登录已失效，请重新登录或检查访问凭证。",
    "bad_request": "请求内容有误，请返回上一步后重试。",
    "not_found": "没有找到对应记录，请稍后刷新或重新发起。",
    "status_missing": "小车尚未上报状态，请等待小车联网后再试。",
    "status_stale": "小车状态已过期，请等待小车重新联网或检查网络。",
    "malformed_json": "请求格式异常，请检查客户端版本后重试。",
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
    "://",
    "/cmd_vel",
    "cmd_vel",
    "ttyusb",
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


def build_server(host, port, state_path, bearer_token):
    store = FileBackedRelayStore(state_path)
    return ThreadingHTTPServer((host, int(port)), make_handler(store, bearer_token))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Trashbot independent remote cloud relay proof service")
    parser.add_argument("--host", default=os.environ.get("TRASHBOT_REMOTE_CLOUD_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("TRASHBOT_REMOTE_CLOUD_PORT", "8088")))
    parser.add_argument(
        "--state-path",
        default=os.environ.get("TRASHBOT_REMOTE_CLOUD_STATE", "remote_cloud_relay_state.json"),
    )
    parser.add_argument("--bearer-token", default=os.environ.get("TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN", ""))
    args = parser.parse_args(argv)
    server = build_server(args.host, args.port, args.state_path, args.bearer_token)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
