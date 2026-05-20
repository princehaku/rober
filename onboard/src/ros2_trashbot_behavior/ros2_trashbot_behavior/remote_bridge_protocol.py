import json
import time
import urllib.error
import urllib.parse
import urllib.request


PROTOCOL_VERSION = "trashbot.remote.v1"
COMMAND_TYPES = {"collect", "confirm_dropoff", "cancel"}
TERMINAL_COMMAND_STATES = {"acked", "failed", "ignored"}
TRUE_STRINGS = {"1", "true", "yes", "on"}
FALSE_STRINGS = {"0", "false", "no", "off"}


class InvalidRemoteCommand(ValueError):
    def __init__(self, message, command=None):
        super().__init__(message)
        self.command = command


class RemoteCloudError(RuntimeError):
    def __init__(self, reason, message, retry_hint="retry_cloud", cloud_reachable=False):
        super().__init__(message)
        self.reason = reason
        self.retry_hint = retry_hint
        self.cloud_reachable = bool(cloud_reachable)


def make_status(robot_id, state, message="", **extra):
    payload = {
        "protocol_version": PROTOCOL_VERSION,
        "robot_id": robot_id,
        "state": state,
        "message": message,
        "updated_at": time.time(),
    }
    payload.update(extra)
    return payload


def validate_command(command):
    if command is None:
        return None
    if not isinstance(command, dict):
        raise ValueError("command must be an object")
    command_id = str(command.get("id") or "").strip()
    command_type = str(command.get("type") or "").strip()
    if not command_id:
        raise ValueError("command.id is required")
    if command_type not in COMMAND_TYPES:
        raise ValueError(f"unsupported command.type: {command_type}")
    payload = command.get("payload")
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError("command.payload must be an object")
    expires_at = command.get("expires_at")
    if expires_at is not None:
        try:
            expires_at = float(expires_at)
        except (TypeError, ValueError) as exc:
            raise ValueError("command.expires_at must be a number") from exc
    queue_sequence = command.get("queue_sequence")
    if queue_sequence is not None:
        if isinstance(queue_sequence, bool):
            raise ValueError("command.queue_sequence must be an integer")
        if isinstance(queue_sequence, float) and not queue_sequence.is_integer():
            raise ValueError("command.queue_sequence must be an integer")
        try:
            queue_sequence = int(queue_sequence)
        except (TypeError, ValueError) as exc:
            raise ValueError("command.queue_sequence must be an integer") from exc
        if queue_sequence < 0:
            raise ValueError("command.queue_sequence must be non-negative")
    normalized = {
        "id": command_id,
        "type": command_type,
        "payload": payload,
        "expires_at": expires_at,
    }
    # queue_sequence 是云端队列的可选安全元数据；缺失时继续依赖 opaque ACK cursor。
    if queue_sequence is not None:
        normalized["queue_sequence"] = queue_sequence
    return normalized


def command_expired(command, now=None):
    expires_at = command.get("expires_at")
    if expires_at is None:
        return False
    return float(expires_at) < (time.time() if now is None else now)


def parse_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in TRUE_STRINGS:
            return True
        if normalized in FALSE_STRINGS:
            return False
    raise ValueError(f"invalid boolean value: {value!r}")


class RemoteCloudClient:
    """Small HTTP polling client for a 4G outbound robot connection."""

    def __init__(self, base_url, robot_id, token="", timeout_sec=5.0):
        self.base_url = base_url.rstrip("/")
        self.robot_id = robot_id
        self.robot_id_path = urllib.parse.quote(str(robot_id), safe="")
        self.token = token
        self.timeout_sec = float(timeout_sec)

    def get_next_command(self, last_ack_id=""):
        query = urllib.parse.urlencode({"last_ack_id": last_ack_id or ""})
        payload = self._request_json("GET", f"/robots/{self.robot_id_path}/commands/next?{query}")
        if not isinstance(payload, dict):
            raise RemoteCloudError(
                "malformed_response",
                "cloud response was not a JSON object",
                retry_hint="contact_support",
                cloud_reachable=True,
            )
        command = payload.get("command")
        try:
            return validate_command(command)
        except ValueError as exc:
            raise InvalidRemoteCommand(str(exc), command) from exc

    def post_status(self, status):
        return self._request_json("POST", f"/robots/{self.robot_id_path}/status", status)

    def post_ack(self, command_id, state, message="", result=None):
        if state not in TERMINAL_COMMAND_STATES:
            raise ValueError(f"unsupported ack state: {state}")
        command_id_path = urllib.parse.quote(str(command_id), safe="")
        return self._request_json(
            "POST",
            f"/robots/{self.robot_id_path}/commands/{command_id_path}/ack",
            {
                "protocol_version": PROTOCOL_VERSION,
                "robot_id": self.robot_id,
                "command_id": command_id,
                "state": state,
                "message": message,
                "result": result or {},
                "updated_at": time.time(),
            },
        )

    def _request_json(self, method, path, payload=None):
        data = None
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                raw = response.read().decode("utf-8") or "{}"
                try:
                    return json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise RemoteCloudError(
                        "malformed_response",
                        "cloud response was not valid JSON",
                        retry_hint="contact_support",
                        cloud_reachable=True,
                    ) from exc
        except urllib.error.HTTPError as exc:
            if int(exc.code) in (401, 403):
                raise RemoteCloudError(
                    "auth_failed",
                    "cloud authorization failed",
                    retry_hint="check_auth",
                    cloud_reachable=True,
                ) from exc
            raise RemoteCloudError(
                "cloud_unreachable",
                f"cloud service returned HTTP {exc.code}",
                retry_hint="retry_cloud",
                cloud_reachable=False,
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RemoteCloudError(
                "cloud_unreachable",
                "cloud request failed",
                retry_hint="retry_cloud",
                cloud_reachable=False,
            ) from exc
