import json
import os
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from ros2_trashbot_behavior.remote_bridge_protocol import parse_bool


API_VERSION = "slice2.operator.v1"
REMOTE_PROTOCOL_VERSION = "trashbot.remote.v1"
PHONE_READINESS_SCHEMA = "trashbot.phone_readiness.v1"
PHONE_READINESS_EVIDENCE_BOUNDARY = "software_proof_docker_local_phone_ui_readiness_gate"
REMOTE_COMMAND_TYPES = {"collect", "confirm_dropoff", "cancel"}
REMOTE_STATUS_STALE_AFTER_SEC = 90.0
REMOTE_PERSISTENCE_SCHEMA = "trashbot.mock_cloud_store.v1"
ELEVATOR_ASSIST_SPEAKER_PROMPT = "你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,"
# mock cloud 不是生产账号系统，但 token gate 能提前固定手机/小车的鉴权契约。
REMOTE_AUTH_ENV_KEYS = ("TRASHBOT_MOCK_CLOUD_BEARER_TOKEN", "OPERATOR_GATEWAY_BEARER_TOKEN")
# retry_hint 只面向手机 UI，避免让普通用户看到 HTTP、ROS 或硬件内部细节。
REMOTE_RETRY_HINTS = {
    "ok",
    "wait_for_robot_status",
    "wait_for_command_ack",
    "check_auth",
    "retry_cloud",
    "contact_support",
}
# safe_phone_copy 是正式手机端可直接展示的中文文案，不能包含 raw JSON 或凭证。
REMOTE_DEGRADATION_COPY = {
    "ok": "手机远程控制通道可用，可以继续操作。",
    "status_stale": "正在等待小车上报最新状态，请稍后再试。",
    "command_pending": "指令已提交，正在等待小车确认。",
    "auth_failed": "手机登录已失效，请重新登录或检查访问凭证。",
    "cloud_unreachable": "远程控制通道暂不可用，请稍后重试。",
    "malformed_response": "远程控制返回异常，请联系支持人员。",
}

PHONE_READINESS_NOT_PROVEN = [
    "production_phone_app",
    "real_cloud_https_tls_public_ingress",
    "real_4g_sim_carrier_network",
    "oss_cdn_data_path",
    "nav2_or_fixed_route_delivery",
    "wave_rover_motion",
    "hil_pass",
]

PHONE_READINESS_NEXT_ACTION_COPY = {
    "continue_local_flow": "可以继续当前本地手机流程。",
    "continue_local_or_wait_remote_status": "本地可继续；远程流程请等待小车上报新状态。",
    "wait_for_robot_status": "等待小车上报最新状态后再继续。",
    "wait_for_command_ack": "等待小车确认上一条指令，避免重复发车。",
    "check_auth": "重新登录或检查访问码后再试。",
    "retry_cloud": "稍后重试远程通道，必要时切到本地 fallback。",
    "contact_support": "联系支持人员，并附带 diagnostics。",
    "manual_takeover": "保持现场安全，按提示人工接管。",
    "watch_progress": "继续观察任务状态，必要时取消。",
}

PHONE_READINESS_PRIMARY_COPY = {
    "ready": "手机可以继续操作。",
    "local_ready_remote_status_waiting": "本地可操作，远程状态仍在等待。",
    "waiting_for_robot_status": "正在等待小车状态。",
    "waiting_for_command_ack": "正在等待小车确认指令。",
    "login_required": "手机登录或访问码需要处理。",
    "remote_unreachable": "远程通道暂不可用。",
    "remote_response_invalid": "远程通道返回异常。",
    "manual_takeover_required": "需要人工接管。",
    "monitoring": "任务进行中，请继续观察。",
}

ELEVATOR_ASSIST_PHASES = {
    "approaching_elevator",
    "waiting_elevator_open",
    "entering_elevator",
    "requesting_floor_help",
    "waiting_target_floor",
    "exiting_elevator",
    "resume_delivery",
}

ELEVATOR_ASSIST_HELP_STATES = {
    "door_timeout",
    "door_closed_or_unknown",
    "target_floor_unconfirmed",
    "target_floor_evidence_unreliable",
    "unsafe_to_enter",
    "unsafe_to_exit",
    "manual_takeover_required",
}

ELEVATOR_ASSIST_COPY = {
    "approaching_elevator": {
        "phone_copy": "正在前往电梯厅。",
        "speaker_prompt": "前往电梯厅。",
    },
    "waiting_elevator_open": {
        "phone_copy": "已到电梯厅，等待电梯开门。",
        "speaker_prompt": "等待电梯开门。",
    },
    "entering_elevator": {
        "phone_copy": "正在进入电梯，请保持通道安全。",
        "speaker_prompt": "正在进入电梯。",
    },
    "requesting_floor_help": {
        "phone_copy": "已进入电梯，正在请求帮忙按楼层。",
        "speaker_prompt": ELEVATOR_ASSIST_SPEAKER_PROMPT,
    },
    "waiting_target_floor": {
        "phone_copy": "正在等待目标楼层，请保持通道安全。",
        "speaker_prompt": "正在等待目标楼层。",
    },
    "exiting_elevator": {
        "phone_copy": "已到目标楼层，准备驶出。",
        "speaker_prompt": "到达目标楼层，准备驶出。",
    },
    "resume_delivery": {
        "phone_copy": "已驶出电梯，继续送往垃圾站。",
        "speaker_prompt": "已驶出电梯，继续送垃圾。",
    },
    "door_timeout": {
        "phone_copy": "电梯未开门，需要人工协助。",
        "speaker_prompt": "需要人工协助。",
    },
    "door_closed_or_unknown": {
        "phone_copy": "电梯门未确认打开，需要人工协助。",
        "speaker_prompt": "需要人工协助。",
    },
    "target_floor_unconfirmed": {
        "phone_copy": "未确认目标楼层，请人工确认。",
        "speaker_prompt": "未确认目标楼层，需要人工协助。",
    },
    "target_floor_evidence_unreliable": {
        "phone_copy": "目标楼层证据不可靠，请人工确认。",
        "speaker_prompt": "未确认目标楼层，需要人工协助。",
    },
    "unsafe_to_exit": {
        "phone_copy": "目标楼层出口不安全，需要人工接管。",
        "speaker_prompt": "需要人工协助。",
    },
    "manual_takeover_required": {
        "phone_copy": "需要人工接管电梯段任务。",
        "speaker_prompt": "需要人工协助。",
    },
}

OPERATOR_PROMPTS = {
    "waiting_for_trash": {
        "phone_copy": "Waiting for trash. Place trash on the robot, then start delivery.",
        "speaker_prompt": "Please place trash on the robot.",
    },
    "loaded_and_ready": {
        "phone_copy": "Trash is loaded. Ready to deliver.",
        "speaker_prompt": "Trash loaded. Preparing to depart.",
    },
    "delivering": {
        "phone_copy": "Delivering to the selected trash station.",
        "speaker_prompt": "Delivering trash now.",
    },
    "arrived_at_station": {
        "phone_copy": "Arrived. Remove or dispose of the load, then confirm dropoff.",
        "speaker_prompt": "Arrived at the trash station. Please remove the trash.",
    },
    "returning": {
        "phone_copy": "Dropoff confirmed. Returning or waiting for the next task.",
        "speaker_prompt": "Dropoff confirmed. Returning now.",
    },
    "completed": {
        "phone_copy": "Task completed.",
        "speaker_prompt": "Task completed.",
    },
    "canceling": {
        "phone_copy": "Cancel request sent. Waiting for the robot to stop.",
        "speaker_prompt": "Cancel request sent.",
    },
    "canceled": {
        "phone_copy": "Task canceled. The robot is stopped or returning to standby.",
        "speaker_prompt": "Task canceled.",
    },
    "failed": {
        "phone_copy": "Task failed. Check diagnostics or request help.",
        "speaker_prompt": "Task failed. Please check the phone.",
    },
    "needs_human_help": {
        "phone_copy": "Human help is required. Follow the shown instruction.",
        "speaker_prompt": "Human help is required.",
    },
    "diagnostics_ready": {
        "phone_copy": "Diagnostics are ready. Share this support package if help is needed.",
        "speaker_prompt": "Diagnostics are ready.",
    },
}


def _elevator_copy_key(elevator_assist):
    if not isinstance(elevator_assist, dict):
        return ""
    for key in ("state", "phase", "reason"):
        value = str(elevator_assist.get(key) or "").strip()
        if value in ELEVATOR_ASSIST_COPY:
            return value
    return ""


def default_elevator_assist():
    return {
        "enabled": False,
        "mode": "",
        "state": "disabled",
        "phase": "",
        "requires_human_help": False,
        "reason": "",
        "target_floor": "",
        "phone_copy": "",
        "speaker_prompt": "",
        "evidence": {},
        "events": [],
    }


def normalize_elevator_assist(value=None, *, state="", message=""):
    """Return a stable, phone-safe elevator_assist object.

    The behavior layer owns the robot contract; this helper only keeps older
    status payloads compatible while letting new task records pass through the
    same machine-readable shape.
    """
    raw = dict(value) if isinstance(value, dict) else {}
    state_text = str(state or "").strip()
    inferred_phase = state_text if state_text in ELEVATOR_ASSIST_PHASES else ""
    inferred_state = state_text if state_text in ELEVATOR_ASSIST_HELP_STATES else ""

    normalized = default_elevator_assist()
    normalized.update(raw)
    phase = str(raw.get("phase") or inferred_phase or "").strip()
    assist_state = str(raw.get("state") or inferred_state or phase or "").strip()
    reason = str(raw.get("reason") or message or "").strip()
    enabled = bool(raw.get("enabled", False) or phase or assist_state in ELEVATOR_ASSIST_HELP_STATES)
    requires_human_help = bool(
        raw.get("requires_human_help", False)
        or assist_state in ELEVATOR_ASSIST_HELP_STATES
        or phase in ELEVATOR_ASSIST_HELP_STATES
    )

    normalized.update(
        {
            "enabled": enabled,
            "mode": str(raw.get("mode") or ("dry_run" if enabled else "")).strip(),
            "state": assist_state or ("active" if enabled else "disabled"),
            "phase": phase,
            "requires_human_help": requires_human_help,
            "reason": reason,
            "target_floor": str(raw.get("target_floor") or "").strip(),
            "evidence": raw.get("evidence") if isinstance(raw.get("evidence"), dict) else {},
            "events": raw.get("events") if isinstance(raw.get("events"), list) else [],
        }
    )

    copy_key = _elevator_copy_key(normalized)
    copy = dict(ELEVATOR_ASSIST_COPY.get(copy_key, {}))
    if not copy and enabled:
        copy = {
            "phone_copy": "电梯协助流程进行中，请在手机端关注下一步提示。",
            "speaker_prompt": "电梯协助流程进行中。",
        }
    normalized["phone_copy"] = str(raw.get("phone_copy") or copy.get("phone_copy", "")).strip()
    normalized["speaker_prompt"] = str(raw.get("speaker_prompt") or copy.get("speaker_prompt", "")).strip()
    return normalized


def operator_prompt_for_state(state, elevator_assist=None):
    elevator_assist = elevator_assist if isinstance(elevator_assist, dict) else {}
    if elevator_assist.get("enabled") and elevator_assist.get("phone_copy"):
        return {
            "phone_copy": elevator_assist.get("phone_copy", ""),
            "speaker_prompt": elevator_assist.get("speaker_prompt", ""),
        }
    return dict(OPERATOR_PROMPTS.get(str(state or ""), OPERATOR_PROMPTS["needs_human_help"]))


def remote_error(code, message, *, details=None):
    return {
        "ok": False,
        "error": {
            "code": str(code),
            "message": str(message),
            "details": details if isinstance(details, dict) else {},
        },
    }


def _remote_timestamp(value, field_name):
    try:
        timestamp = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a unix timestamp") from exc
    if timestamp <= 0:
        raise ValueError(f"{field_name} must be positive")
    return timestamp


def normalize_remote_command(robot_id, payload, *, now=None):
    """Normalize the cloud command contract without exposing robot internals.

    The phone/cloud surface deals only in behavior-level commands. It does not
    accept raw ROS topics, low-level transport settings, or velocity commands.
    """
    now = time.time() if now is None else float(now)
    payload = payload if isinstance(payload, dict) else {}
    command_type = str(payload.get("type") or "").strip()
    command_payload = payload.get("payload", {})
    command_id = str(payload.get("id") or f"cmd-{int(now * 1000)}-{uuid.uuid4().hex[:8]}").strip()
    protocol_version = str(payload.get("protocol_version") or REMOTE_PROTOCOL_VERSION).strip()
    expires_at = _remote_timestamp(payload.get("expires_at", now + 300.0), "expires_at")

    if protocol_version != REMOTE_PROTOCOL_VERSION:
        raise ValueError(f"protocol_version must be {REMOTE_PROTOCOL_VERSION}")
    if not command_id:
        raise ValueError("id is required")
    if command_type not in REMOTE_COMMAND_TYPES:
        raise ValueError("type must be one of cancel, collect, confirm_dropoff")
    if not isinstance(command_payload, dict):
        raise ValueError("payload must be an object")
    if command_type == "collect" and not str(command_payload.get("target") or "").strip():
        raise ValueError("collect payload.target is required")

    return {
        "protocol_version": REMOTE_PROTOCOL_VERSION,
        "id": command_id,
        "robot_id": str(robot_id or "").strip(),
        "type": command_type,
        "expires_at": expires_at,
        "payload": dict(command_payload),
        "created_at": now,
    }


def normalize_remote_status(robot_id, payload, *, now=None):
    now = time.time() if now is None else float(now)
    payload = payload if isinstance(payload, dict) else {}
    state = str(payload.get("state") or "").strip()
    protocol_version = str(payload.get("protocol_version") or REMOTE_PROTOCOL_VERSION)
    if protocol_version != REMOTE_PROTOCOL_VERSION:
        raise ValueError(f"protocol_version must be {REMOTE_PROTOCOL_VERSION}")
    if not state:
        raise ValueError("state is required")
    return {
        "protocol_version": protocol_version,
        "robot_id": str(robot_id or "").strip(),
        "state": state,
        "message": str(payload.get("message") or "").strip(),
        "updated_at": _remote_timestamp(payload.get("updated_at", now), "updated_at"),
        "diagnostics": payload.get("diagnostics") if isinstance(payload.get("diagnostics"), dict) else {},
    }


def normalize_remote_ack(robot_id, command_id, payload, *, now=None):
    now = time.time() if now is None else float(now)
    payload = payload if isinstance(payload, dict) else {}
    state = str(payload.get("state") or "").strip()
    protocol_version = str(payload.get("protocol_version") or REMOTE_PROTOCOL_VERSION)
    if protocol_version != REMOTE_PROTOCOL_VERSION:
        raise ValueError(f"protocol_version must be {REMOTE_PROTOCOL_VERSION}")
    if state not in {"acked", "failed", "ignored"}:
        raise ValueError("state must be one of acked, failed, ignored")
    return {
        "protocol_version": protocol_version,
        "robot_id": str(robot_id or "").strip(),
        "command_id": str(command_id or "").strip(),
        "state": state,
        "message": str(payload.get("message") or "").strip(),
        "updated_at": _remote_timestamp(payload.get("updated_at", now), "updated_at"),
        "result": payload.get("result") if isinstance(payload.get("result"), dict) else {},
    }


SENSITIVE_REMOTE_KEYS = {
    "token",
    "bearer",
    "authorization",
    "auth",
    "secret",
    "password",
    "serial",
    "serial_port",
    "baudrate",
    "ros_topic",
    "topic",
    "cmd_vel",
    "hardware",
    # URL 里可能带 userinfo 或临时凭证，mock proof 中一律不持久化。
    "url",
    "cloud_url",
}


def _remote_safe_value(value):
    # mock cloud 的持久化文件会被拿来做 proof，所以这里默认做白名单式降噪。
    if isinstance(value, dict):
        safe = {}
        for key, item in value.items():
            key_text = str(key)
            key_lc = key_text.lower()
            if any(sensitive in key_lc for sensitive in SENSITIVE_REMOTE_KEYS):
                continue
            safe[key_text] = _remote_safe_value(item)
        return safe
    if isinstance(value, list):
        return [_remote_safe_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _default_remote_status(robot_key):
    return {
        "protocol_version": REMOTE_PROTOCOL_VERSION,
        "robot_id": robot_key,
        "state": "unknown",
        "message": "robot has not posted status yet",
        "updated_at": time.time(),
        "diagnostics": {},
    }


class MockCloudStore:
    """Mock `trashbot.remote.v1` cloud control-plane store.

    默认仍是进程内存；传入 state_path 后才写本地 JSON proof。这个 proof
    只保存 command queue、status、ack 和统计字段，不保存 token、串口、ROS topic
    或硬件参数，避免把调试入口误当成生产云或硬件证据。
    """

    def __init__(self, state_path=None, auth_required=False):
        self._lock = threading.Lock()
        self._robots = {}
        self.state_path = os.path.expanduser(str(state_path or "")).strip()
        # auth_required 只影响 readiness 口径；真正的 header 校验在 HTTP handler 做。
        self.auth_required = bool(auth_required)
        if self.state_path:
            self._load()

    def _robot(self, robot_id):
        robot_key = str(robot_id or "").strip()
        if not robot_key:
            raise ValueError("robot_id is required")
        return self._robots.setdefault(
            robot_key,
            {
                "commands": [],
                "command_index": {},
                "acks": {},
                "status": _default_remote_status(robot_key),
                "stats": {
                    "created_at": time.time(),
                    "updated_at": time.time(),
                    "command_count": 0,
                    "ack_count": 0,
                    "status_count": 0,
                },
            },
        )

    def _load(self):
        if not os.path.exists(self.state_path):
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as state_file:
                payload = json.load(state_file)
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(payload, dict) or payload.get("schema") != REMOTE_PERSISTENCE_SCHEMA:
            return
        robots = payload.get("robots")
        if not isinstance(robots, dict):
            return
        for robot_id, robot_payload in robots.items():
            if not isinstance(robot_payload, dict):
                continue
            robot_key = str(robot_id or "").strip()
            commands = robot_payload.get("commands") if isinstance(robot_payload.get("commands"), list) else []
            acks = robot_payload.get("acks") if isinstance(robot_payload.get("acks"), dict) else {}
            status = robot_payload.get("status") if isinstance(robot_payload.get("status"), dict) else {}
            stats = robot_payload.get("stats") if isinstance(robot_payload.get("stats"), dict) else {}
            safe_commands = [
                dict(command)
                for command in commands
                if isinstance(command, dict) and str(command.get("id") or "").strip()
            ]
            self._robots[robot_key] = {
                "commands": safe_commands,
                "command_index": {str(command["id"]): command for command in safe_commands},
                "acks": {
                    str(command_id): dict(ack)
                    for command_id, ack in acks.items()
                    if isinstance(ack, dict)
                },
                "status": dict(status) if status else _default_remote_status(robot_key),
                "stats": {
                    "created_at": float(stats.get("created_at") or time.time()),
                    "updated_at": float(stats.get("updated_at") or time.time()),
                    "command_count": int(stats.get("command_count") or len(safe_commands)),
                    "ack_count": int(stats.get("ack_count") or len(acks)),
                    "status_count": int(stats.get("status_count") or 0),
                },
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
                "acks": robot.get("acks", {}),
                "status": robot.get("status", {}),
                "stats": robot.get("stats", {}),
            }
        payload = {
            "schema": REMOTE_PERSISTENCE_SCHEMA,
            "updated_at": time.time(),
            "robots": _remote_safe_value(robots),
        }
        fd, tmp_path = tempfile.mkstemp(prefix=".mock-cloud-", suffix=".json", dir=state_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(payload, tmp_file, ensure_ascii=False, sort_keys=True)
                tmp_file.write("\n")
            os.replace(tmp_path, self.state_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _touch_stats_locked(self, robot, field):
        # 统计只用于手机 readiness 和 proof 复盘，不参与机器人行为判定。
        stats = robot.setdefault("stats", {})
        stats["updated_at"] = time.time()
        stats[field] = int(stats.get(field, 0) or 0) + 1

    def _latest_ack_locked(self, robot):
        acks = [ack for ack in robot.get("acks", {}).values() if isinstance(ack, dict)]
        if not acks:
            return None
        return max(acks, key=lambda ack: float(ack.get("updated_at") or 0.0))

    def _readiness_locked(self, robot_id, robot):
        now = time.time()
        status = robot.get("status") if isinstance(robot.get("status"), dict) else _default_remote_status(robot_id)
        status_updated_at = float(status.get("updated_at") or 0.0)
        status_stale = status.get("state") == "unknown" or (now - status_updated_at) > REMOTE_STATUS_STALE_AFTER_SEC
        latest_ack = self._latest_ack_locked(robot)
        last_command_ack = ""
        if latest_ack:
            last_command_ack = str(latest_ack.get("command_id") or "")
        # command_pending 是手机侧降级态，不等同于任务失败或送达结果。
        pending_command_count = sum(
            1
            for command in robot.get("commands", [])
            if isinstance(command, dict) and str(command.get("id") or "") not in robot.get("acks", {})
        )
        retry_hint = "ok"
        degradation_state = "ok"
        # readiness 优先保护状态新鲜度；状态过旧时不让手机继续下发主流程。
        if status_stale:
            retry_hint = "wait_for_robot_status"
            degradation_state = "status_stale"
        elif pending_command_count:
            # 有未 ACK 指令时继续等待，避免手机重复发车或误判任务已经开始。
            retry_hint = "wait_for_command_ack"
            degradation_state = "command_pending"
        return {
            "remote_ready": bool(not status_stale),
            "cloud_reachable": True,
            "last_command_ack": last_command_ack,
            "status_stale": bool(status_stale),
            "retry_hint": retry_hint,
            # 无 token 时保持 mock_not_required，避免把本地 fallback 误说成生产鉴权。
            "auth_state": "required" if self.auth_required else "mock_not_required",
            "degradation_state": degradation_state,
            "safe_phone_copy": REMOTE_DEGRADATION_COPY[degradation_state],
            "status_age_sec": max(0.0, now - status_updated_at) if status_updated_at else None,
            "pending_command_count": pending_command_count,
            "queue_persisted": bool(self.state_path),
            "state_path_configured": bool(self.state_path),
            "proof_schema": REMOTE_PERSISTENCE_SCHEMA if self.state_path else "",
        }

    def submit_command(self, robot_id, payload):
        command = _remote_safe_value(normalize_remote_command(robot_id, payload))
        with self._lock:
            robot = self._robot(robot_id)
            existing = robot["command_index"].get(command["id"])
            if existing:
                # 幂等提交仍返回 readiness，手机端可同步刷新当前降级原因。
                readiness = self._readiness_locked(str(robot_id or "").strip(), robot)
                return 200, {
                    "ok": True,
                    "command": dict(existing),
                    "duplicate": True,
                    "remote_readiness": readiness,
                }
            robot["commands"].append(command)
            robot["command_index"][command["id"]] = command
            self._touch_stats_locked(robot, "command_count")
            # command 入队后立即计算 readiness，通常会进入 status_stale 或 command_pending。
            readiness = self._readiness_locked(str(robot_id or "").strip(), robot)
            self._persist_locked()
        return 201, {"ok": True, "command": dict(command), "duplicate": False, "remote_readiness": readiness}

    def next_command(self, robot_id, last_ack_id=""):
        now = time.time()
        last_ack_id = str(last_ack_id or "").strip()
        with self._lock:
            robot = self._robot(robot_id)
            commands = robot["commands"]
            start_index = 0
            if last_ack_id:
                for index, command in enumerate(commands):
                    if command["id"] == last_ack_id:
                        start_index = index + 1
                        break
            for command in commands[start_index:]:
                if command["id"] not in robot["acks"] and float(command["expires_at"]) >= now:
                    return {"ok": True, "command": dict(command)}
        return {"ok": True, "command": None}

    def post_status(self, robot_id, payload):
        status = normalize_remote_status(robot_id, payload)
        with self._lock:
            robot = self._robot(robot_id)
            robot["status"] = _remote_safe_value(status)
            self._touch_stats_locked(robot, "status_count")
            readiness = self._readiness_locked(str(robot_id or "").strip(), robot)
            self._persist_locked()
        phone_status = dict(_remote_safe_value(status))
        phone_status["remote_readiness"] = readiness
        return {"ok": True, "status": phone_status, "remote_readiness": readiness}

    def get_status(self, robot_id):
        with self._lock:
            robot = self._robot(robot_id)
            status = dict(robot["status"])
            readiness = self._readiness_locked(str(robot_id or "").strip(), robot)
        status["remote_readiness"] = readiness
        return {"ok": True, "status": status, "remote_readiness": readiness}

    def post_ack(self, robot_id, command_id, payload):
        ack = normalize_remote_ack(robot_id, command_id, payload)
        if not ack["command_id"]:
            raise ValueError("command_id is required")
        with self._lock:
            robot = self._robot(robot_id)
            robot["acks"][ack["command_id"]] = _remote_safe_value(ack)
            self._touch_stats_locked(robot, "ack_count")
            readiness = self._readiness_locked(str(robot_id or "").strip(), robot)
            self._persist_locked()
        return {"ok": True, "ack": dict(_remote_safe_value(ack)), "remote_readiness": readiness}

    def get_ack(self, robot_id, command_id):
        with self._lock:
            ack = self._robot(robot_id)["acks"].get(str(command_id or "").strip())
        if not ack:
            return 404, remote_error("ack_not_found", f"ack not found for command_id: {command_id}")
        return 200, {"ok": True, "ack": dict(ack)}

HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Trashbot Operator</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7f8;
      --panel: #ffffff;
      --ink: #172026;
      --muted: #60707c;
      --line: #d7dee3;
      --accent: #126b5f;
      --accent-ink: #ffffff;
      --danger: #b42318;
      --warn: #9a5b00;
      --ok: #1d7f4f;
    }
    * { box-sizing: border-box; }
    body {
      background: var(--bg);
      color: var(--ink);
      font-family: system-ui, -apple-system, Segoe UI, sans-serif;
      margin: 0;
    }
    main {
      display: grid;
      gap: 14px;
      margin: 0 auto;
      max-width: 860px;
      padding: 14px;
    }
    header {
      align-items: center;
      display: flex;
      justify-content: space-between;
      gap: 12px;
    }
    h1 { font-size: 22px; margin: 0; }
    h2 { font-size: 15px; margin: 0 0 10px; }
    button, input, select, textarea {
      border-radius: 8px;
      font: inherit;
      min-height: 44px;
      padding: 10px 12px;
    }
    button {
      background: #eef3f4;
      border: 1px solid var(--line);
      color: var(--ink);
      cursor: pointer;
      font-weight: 650;
    }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: var(--accent-ink);
    }
    button.danger { color: var(--danger); }
    button:disabled {
      color: #7b878f;
      cursor: not-allowed;
      opacity: 0.55;
    }
    label { color: var(--muted); display: grid; gap: 6px; font-size: 13px; }
    input, select, textarea { border: 1px solid var(--line); width: 100%; }
    textarea { min-height: 86px; resize: vertical; }
    canvas {
      background: #fbfcfc;
      border: 1px solid var(--line);
      border-radius: 8px;
      display: block;
      height: 260px;
      max-width: 100%;
      width: 100%;
    }
    pre {
      background: #111820;
      border-radius: 8px;
      color: #edf2f7;
      font-size: 12px;
      margin: 0;
      max-height: 280px;
      overflow: auto;
      padding: 12px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    .status {
      align-items: start;
      display: grid;
      gap: 10px;
      grid-template-columns: minmax(0, 1fr) auto;
    }
    .readinessHero {
      border-left: 5px solid var(--accent);
      display: grid;
      gap: 10px;
    }
    .readinessHero.blocked { border-left-color: var(--danger); }
    .readinessHero.waiting { border-left-color: var(--warn); }
    .readinessMain {
      align-items: center;
      display: flex;
      gap: 10px;
      justify-content: space-between;
    }
    .readinessHint {
      color: var(--ink);
      font-size: 15px;
      margin: 0;
    }
    .stateBadge {
      background: #edf7f5;
      border: 1px solid #c7e3dd;
      border-radius: 999px;
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
      padding: 6px 10px;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .stateBadge.problem {
      background: #fff4ef;
      border-color: #f3c8bb;
      color: var(--danger);
    }
    .message { color: var(--muted); margin: 4px 0 0; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
    .row button { flex: 1 1 150px; }
    .steps {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(5, minmax(0, 1fr));
    }
    .step {
      border-bottom: 3px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      min-height: 44px;
      padding: 4px 0 8px;
    }
    .step.active {
      border-color: var(--accent);
      color: var(--ink);
      font-weight: 750;
    }
    .step.done { border-color: var(--ok); color: var(--ink); }
    .telemetry, .diagnosticGrid {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin-top: 12px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
    }
    .metric span {
      color: var(--muted);
      display: block;
      font-size: 12px;
      margin-bottom: 3px;
    }
    .metric strong { overflow-wrap: anywhere; }
    .integrityCard {
      border: 1px solid var(--line);
      border-radius: 8px;
      margin-top: 12px;
      padding: 12px;
    }
    .integrityHeader {
      align-items: center;
      display: flex;
      gap: 10px;
      justify-content: space-between;
    }
    .integrityBadge {
      border: 1px solid var(--line);
      border-radius: 999px;
      font-size: 12px;
      font-weight: 750;
      padding: 5px 9px;
      text-transform: uppercase;
      white-space: nowrap;
    }
    .integrityBadge.ok {
      background: #edf7f0;
      border-color: #b7dfc4;
      color: var(--ok);
    }
    .integrityBadge.warning {
      background: #fff7e6;
      border-color: #f0cf8a;
      color: var(--warn);
    }
    .integrityBadge.error {
      background: #fff1ed;
      border-color: #efb7aa;
      color: var(--danger);
    }
    .integrityBadge.muted {
      background: #eef3f4;
      border-color: var(--line);
      color: var(--muted);
    }
    .integrityCard .supportList li {
      overflow-wrap: anywhere;
    }
    .supportList {
      color: var(--muted);
      font-size: 13px;
      margin: 8px 0 0;
      padding-left: 18px;
    }
    .reviewGrid {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin-top: 10px;
    }
    .reviewMeta {
      border: 1px solid var(--line);
      border-radius: 8px;
      margin-top: 10px;
      padding: 10px;
    }
    .reviewMeta code {
      color: var(--ink);
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    [hidden] { display: none; }
    @media (max-width: 560px) {
      main { padding: 10px; }
      header { align-items: start; flex-direction: column; }
      .status { grid-template-columns: 1fr; }
      .steps { grid-template-columns: 1fr; }
      .telemetry, .diagnosticGrid { grid-template-columns: 1fr; }
      .reviewGrid { grid-template-columns: 1fr; }
      canvas { height: 220px; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Trashbot Operator</h1>
        <p class="message">Phone control for trash delivery</p>
      </div>
      <span id="connectionState" class="stateBadge">loading</span>
    </header>
    <section id="phoneReadinessPanel" class="panel readinessHero waiting">
      <div class="readinessMain">
        <div>
          <span id="phoneReadinessBadge" class="stateBadge">checking</span>
          <h2 id="phoneReadinessTitle">Checking phone readiness</h2>
        </div>
        <span id="phoneReadinessBoundary" class="stateBadge">local proof</span>
      </div>
      <p id="phoneReadinessCopy" class="readinessHint">正在判断手机现在能不能继续。</p>
      <p class="message">Next: <strong id="phoneReadinessNext">等待状态刷新。</strong></p>
      <p class="message">Support: <strong id="phoneReadinessSupport">not reported</strong></p>
      <p class="message">Not proven: <strong id="phoneReadinessNotProven">real cloud, 4G, HIL</strong></p>
    </section>
    <section class="panel status">
      <div>
        <span id="stateBadge" class="stateBadge">waiting</span>
        <h2 id="stateTitle">Waiting for trash</h2>
        <p id="stateMessage" class="message">Place trash on the robot, then start delivery.</p>
        <p class="message">Speaker: <strong id="speakerPrompt">Please place trash on the robot.</strong></p>
      </div>
      <label>Trash station
        <input id="target" value="trash_station" autocomplete="off">
      </label>
    </section>
    <section class="panel">
      <div class="steps" id="journeySteps">
        <div class="step" data-step="waiting">1. Load trash</div>
        <div class="step" data-step="delivering">2. Deliver</div>
        <div class="step" data-step="dropoff">3. Dropoff</div>
        <div class="step" data-step="returning">4. Return</div>
        <div class="step" data-step="completed">5. Complete</div>
      </div>
      <div class="row">
        <button id="collectButton" class="primary" onclick="collect()">Start Delivery</button>
        <button id="dropoffButton" onclick="confirmDropoff()">Confirm Dropoff</button>
        <button id="cancelButton" class="danger" onclick="cancelTask()">Cancel</button>
        <button id="diagnosticsButton" onclick="diagnostics()">Diagnostics</button>
      </div>
    </section>
    <section class="panel">
      <h2>Robot Location</h2>
      <div id="locationPanel" class="telemetry" hidden>
        <div class="metric"><span>Frame</span><strong id="locationFrame">unknown</strong></div>
        <div class="metric"><span>Updated</span><strong id="poseAge">no pose</strong></div>
        <div class="metric"><span>X</span><strong id="locationX">-</strong></div>
        <div class="metric"><span>Y</span><strong id="locationY">-</strong></div>
        <div class="metric"><span>Yaw</span><strong id="locationYaw">-</strong></div>
        <div class="metric"><span>Path</span><strong id="pathCount">0 points</strong></div>
      </div>
      <canvas id="robotMap" width="640" height="260"></canvas>
    </section>
    <section id="diagnosticsPanel" class="panel" hidden>
      <h2>Support Diagnostics</h2>
      <div class="diagnosticGrid">
        <div class="metric"><span>Software</span><strong id="diagSoftware">-</strong></div>
        <div class="metric"><span>Map</span><strong id="diagMap">-</strong></div>
        <div class="metric"><span>Route</span><strong id="diagRoute">-</strong></div>
        <div class="metric"><span>Failure</span><strong id="diagFailure">-</strong></div>
        <div class="metric"><span>Source</span><strong id="diagSource">-</strong></div>
        <div class="metric"><span>Failure code</span><strong id="diagFailureCode">-</strong></div>
        <div class="metric"><span>Evidence ref</span><strong id="diagEvidenceRef">-</strong></div>
        <div class="metric"><span>Human takeover</span><strong id="diagHumanIntervention">-</strong></div>
        <div class="metric"><span>Task record</span><strong id="diagTask">-</strong></div>
        <div class="metric"><span>Status file</span><strong id="diagStatusFile">-</strong></div>
        <div class="metric"><span>State transitions</span><strong id="diagStateTransitionHistory">-</strong></div>
        <div class="metric"><span>Vision samples</span><strong id="diagVisionSamples">-</strong></div>
        <div class="metric"><span>Latest vision sample</span><strong id="diagLatestVisionSample">-</strong></div>
        <div class="metric"><span>Review queue</span><strong id="diagReviewQueue">-</strong></div>
        <div class="metric"><span>Next review sample</span><strong id="diagNextReviewSample">-</strong></div>
        <div class="metric"><span>Route proof state</span><strong id="diagRouteProofState">-</strong></div>
        <div class="metric"><span>Route proof summary</span><strong id="diagRouteProofSummary">-</strong></div>
        <div class="metric"><span>Route proof reason</span><strong id="diagRouteProofReason">-</strong></div>
        <div class="metric"><span>Route proof source</span><strong id="diagRouteProofSource">-</strong></div>
        <div class="metric"><span>Elevator assist</span><strong id="diagElevatorAssistState">-</strong></div>
        <div class="metric"><span>Elevator prompt</span><strong id="diagElevatorAssistPrompt">-</strong></div>
        <div class="metric"><span>Elevator evidence</span><strong id="diagElevatorAssistEvidence">-</strong></div>
        <div class="metric"><span>Elevator next step</span><strong id="diagElevatorAssistNextStep">-</strong></div>
      </div>
      <p id="diagRecoveryHint" class="message">No manual takeover required.</p>
      <ul id="diagStateTransitionHistoryList" class="supportList"></ul>
      <div id="diagVisionIntegrity" class="integrityCard">
        <div class="integrityHeader">
          <h2>Vision evidence chain</h2>
          <span id="diagVisionIntegrityBadge" class="integrityBadge muted">unknown</span>
        </div>
        <p id="diagVisionIntegritySummary" class="message">Diagnostics have not been loaded yet.</p>
        <ul id="diagVisionIntegrityReasons" class="supportList"></ul>
        <p class="message">Context coverage: <strong id="diagVisionContextCoverage">not reported</strong></p>
        <p class="message">File counts: <strong id="diagVisionFileCounts">not reported</strong></p>
        <p class="message">Next step: <strong id="diagVisionIntegrityAdvice">Refresh diagnostics after the robot publishes a support package.</strong></p>
      </div>
      <div id="diagHardwareProof" class="integrityCard">
        <div class="integrityHeader">
          <h2>Hardware proof</h2>
          <span id="diagHardwareProofBadge" class="integrityBadge muted">unknown</span>
        </div>
        <p id="diagHardwareProofSummary" class="message">Diagnostics have not been loaded yet.</p>
        <p class="message">Next step: <strong id="diagHardwareProofNextStep">Run software proof, then hardware-in-loop validation.</strong></p>
        <ul id="diagHardwareProofReasons" class="supportList"></ul>
      </div>
      <ul id="diagRefs" class="supportList"></ul>
    </section>
    <section class="panel">
      <h2>Vision Review Queue</h2>
      <p class="message">Select a sample and submit a manual review decision.</p>
      <div class="reviewGrid">
        <label>Sample
          <select id="reviewSampleSelect"></select>
        </label>
        <label>Decision
          <select id="reviewDecisionSelect">
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
            <option value="needs_retry">needs_retry</option>
          </select>
        </label>
      </div>
      <div class="reviewGrid">
        <label>Option (optional)
          <input id="reviewOptionInput" autocomplete="off" placeholder="e.g. route_keyframe_review">
        </label>
        <label>Operator (optional)
          <input id="reviewOperatorInput" autocomplete="off" placeholder="operator_id">
        </label>
      </div>
      <label>Comment (optional)
        <textarea id="reviewCommentInput" placeholder="why this sample was approved or rejected"></textarea>
      </label>
      <div class="row">
        <button id="reviewRefreshButton" onclick="loadReviewQueue()">Refresh Queue</button>
        <button id="reviewJumpPendingButton" onclick="jumpToNextPending()">Jump To Next Pending</button>
        <button id="reviewSubmitButton" class="primary" onclick="submitReviewDecision()">Submit Review Decision</button>
      </div>
      <div class="reviewMeta">
        <p class="message">Queue status: <strong id="reviewQueueStatus">not loaded</strong></p>
        <p class="message">Progress: <strong id="reviewProgressSummary">not loaded</strong></p>
        <p class="message">Decision distribution: <strong id="reviewDecisionDistribution">not loaded</strong></p>
        <p class="message">Next pending sample: <strong id="reviewNextPending">not loaded</strong></p>
        <p class="message">Selected summary: <code id="reviewSelectedSummary">none</code></p>
        <p class="message">Result: <strong id="reviewResultMessage">not submitted</strong></p>
      </div>
    </section>
    <section class="panel">
      <h2>Raw Status</h2>
      <pre id="status">loading...</pre>
    </section>
  </main>
<script>
const STATE_COPY = {
  waiting_for_trash: ['Waiting for trash', 'Place trash on the robot, then start delivery.', 'waiting'],
  loaded_and_ready: ['Trash loaded', 'Ready to deliver to the selected trash station.', 'waiting'],
  delivering: ['Delivering', 'The robot is moving to the trash station.', 'delivering'],
  navigating: ['Delivering', 'The robot is moving to the trash station.', 'delivering'],
  arrived_at_station: ['Arrived', 'Remove or dispose of the load, then confirm dropoff.', 'dropoff'],
  dropoff: ['Confirm dropoff', 'Remove or dispose of the load, then confirm dropoff.', 'dropoff'],
  returning: ['Returning', 'Dropoff is confirmed. The robot is returning or waiting.', 'returning'],
  completed: ['Task completed', 'The robot is ready for the next delivery.', 'completed'],
  canceling: ['Canceling', 'Cancel request sent. Waiting for the robot to stop.', 'returning'],
  canceled: ['Canceled', 'The robot is stopped or returning to standby.', 'completed'],
  failed: ['Needs help', 'Task failed. Open diagnostics or request help.', 'dropoff'],
  needs_human_help: ['Needs help', 'Human help is required. Follow the shown instruction.', 'dropoff'],
  approaching_elevator: ['Elevator assist', '正在前往电梯厅。', 'delivering'],
  waiting_elevator_open: ['Elevator assist', '已到电梯厅，等待电梯开门。', 'delivering'],
  entering_elevator: ['Elevator assist', '正在进入电梯，请保持通道安全。', 'delivering'],
  requesting_floor_help: ['Elevator assist', '已进入电梯，正在请求帮忙按楼层。', 'delivering'],
  waiting_target_floor: ['Elevator assist', '正在等待目标楼层，请保持通道安全。', 'delivering'],
  exiting_elevator: ['Elevator assist', '已到目标楼层，准备驶出。', 'delivering'],
  resume_delivery: ['Delivering', '已驶出电梯，继续送往垃圾站。', 'delivering'],
  network_error: ['Connection issue', 'The phone cannot reach the robot control page.', 'waiting']
};
const STEP_ORDER = ['waiting', 'delivering', 'dropoff', 'returning', 'completed'];
const ELEVATOR_ASSIST_SPEAKER_PROMPT = '你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,';
let reviewQueueSnapshot = null;
function fmt(value) {
  return Number.isFinite(value) ? value.toFixed(2) : '-';
}
function text(value, fallback) {
  const normalized = String(value || '').trim();
  return normalized || fallback;
}
function arrayText(value) {
  return Array.isArray(value) ? value.map(item => String(item || '').trim()).filter(Boolean) : [];
}
function countSummary(value) {
  if (!value || typeof value !== 'object') return 'not reported';
  return Object.keys(value).map((key) => {
    const counts = value[key] && typeof value[key] === 'object' ? value[key] : {};
    const parts = Object.keys(counts).map(countKey => `${countKey} ${counts[countKey]}`);
    return parts.length ? `${key}: ${parts.join(', ')}` : key;
  }).join('; ') || 'not reported';
}
function visionIntegrityView(visionSamples) {
  const summary = visionSamples.integrity_summary || {};
  const status = text(summary.status, 'unknown');
  const config = {
    ok: {
      label: 'Healthy',
      tone: 'ok',
      summary: 'Vision evidence chain is complete and ready for support review.',
      advice: 'Continue the task flow. Keep collecting samples during real runs.'
    },
    warning: {
      label: 'Needs review',
      tone: 'warning',
      summary: 'Vision evidence chain is usable, but some evidence should be reviewed first.',
      advice: 'Review the listed sample evidence before using it for route or anomaly decisions.'
    },
    error: {
      label: 'Broken',
      tone: 'error',
      summary: 'Vision evidence chain is not trustworthy until the reported issue is repaired.',
      advice: 'Recreate or repair the missing sample files, then rerun diagnostics.'
    },
    not_configured: {
      label: 'Not configured',
      tone: 'muted',
      summary: 'Vision sample evidence is not configured on this robot yet.',
      advice: 'Configure vision_sample_manifest_ref or run a learning route that writes a manifest.'
    },
    checker_unavailable: {
      label: 'Checker unavailable',
      tone: 'muted',
      summary: 'This software environment cannot run the vision sample checker.',
      advice: 'Install or source the vision package before relying on this support signal.'
    },
    checker_failed: {
      label: 'Checker failed',
      tone: 'error',
      summary: 'The vision sample checker failed, so the sample chain cannot be judged from the phone.',
      advice: 'Share the diagnostics package with support and inspect the checker error.'
    },
    unknown: {
      label: 'Unknown',
      tone: 'muted',
      summary: 'There is not enough diagnostics data to judge the vision evidence chain.',
      advice: 'Refresh diagnostics after the robot publishes a support package.'
    }
  };
  const view = config[status] || config.unknown;
  const missingRefs = Array.isArray(visionSamples.missing_file_refs) ? visionSamples.missing_file_refs : [];
  const reasons = [];
  missingRefs.forEach((item) => {
    if (!item || typeof item !== 'object') return;
    const field = text(item.field, 'file_ref');
    const detail = text(item.resolved_path, text(item.value, 'unresolved path'));
    reasons.push(`Missing ${field}: ${detail}`);
  });
  reasons.push(...arrayText(visionSamples.integrity_errors));
  reasons.push(...arrayText(visionSamples.integrity_warnings));
  if (text(visionSamples.read_error, '')) reasons.push(text(visionSamples.read_error, ''));
  return {
    status,
    label: view.label,
    tone: view.tone,
    summary: view.summary,
    reasons: reasons.slice(0, 3).length ? reasons.slice(0, 3) : ['No blocking evidence-chain issue reported.'],
    advice: view.advice,
    contextCoverage: countSummary(visionSamples.context_field_coverage),
    fileCounts: countSummary(visionSamples.file_counts)
  };
}
function renderVisionIntegrity(visionSamples) {
  const view = visionIntegrityView(visionSamples || {});
  const badge = document.getElementById('diagVisionIntegrityBadge');
  badge.textContent = view.label;
  badge.className = `integrityBadge ${view.tone}`;
  document.getElementById('diagVisionIntegritySummary').textContent = view.summary;
  document.getElementById('diagVisionIntegrityAdvice').textContent = view.advice;
  document.getElementById('diagVisionContextCoverage').textContent = view.contextCoverage;
  document.getElementById('diagVisionFileCounts').textContent = view.fileCounts;
  const reasonList = document.getElementById('diagVisionIntegrityReasons');
  reasonList.innerHTML = '';
  view.reasons.forEach((reason) => {
    const item = document.createElement('li');
    item.textContent = reason;
    reasonList.appendChild(item);
  });
}
function hardwareProofView(hardwareProof) {
  const status = text(hardwareProof.status, 'read_error');
  const config = {
    software_proof: {
      label: 'Software proof',
      tone: 'warning',
      summary: 'Software proof is ready only; it does not validate real hardware or HIL.',
      nextStep: 'Run WAVE ROVER hardware-in-loop validation before treating the robot as hardware-ready.'
    },
    needs_hil: {
      label: 'Needs HIL',
      tone: 'warning',
      summary: 'Software proof exists, hardware-in-loop still required before treating the robot as validated.',
      nextStep: 'Run the WAVE ROVER HIL recipe and capture UART, motion, IMU, and battery evidence.'
    },
    invalid_config: {
      label: 'Invalid config',
      tone: 'error',
      summary: 'The hardware proof artifact reports an invalid bridge configuration.',
      nextStep: 'Fix the bridge configuration, rerun software proof, then run HIL.'
    },
    read_error: {
      label: 'Read error',
      tone: 'error',
      summary: 'The hardware proof artifact cannot be read or trusted.',
      nextStep: 'Recreate the artifact and keep hardware status conservative until HIL passes.'
    }
  };
  const view = config[status] || config.read_error;
  const reasons = [];
  const readError = text(hardwareProof.read_error, '');
  if (readError) reasons.push(readError);
  const riskFlags = Array.isArray(hardwareProof.risk_flags) ? hardwareProof.risk_flags : [];
  riskFlags.slice(0, 3).forEach((flag) => {
    if (flag && typeof flag === 'object') {
      reasons.push(`${text(flag.id, 'risk')}: ${text(flag.detail, text(flag.severity, 'review required'))}`);
    } else {
      reasons.push(String(flag));
    }
  });
  if (text(hardwareProof.artifact_ref, '')) reasons.push(`Artifact: ${hardwareProof.artifact_ref}`);
  return {
    status,
    label: view.label,
    tone: view.tone,
    summary: text(hardwareProof.summary, view.summary),
    nextStep: text(hardwareProof.next_step, view.nextStep),
    reasons: reasons.length ? reasons.slice(0, 4) : ['No blocking hardware proof detail reported.']
  };
}
function renderHardwareProof(hardwareProof) {
  const view = hardwareProofView(hardwareProof || {});
  const badge = document.getElementById('diagHardwareProofBadge');
  badge.textContent = view.label;
  badge.className = `integrityBadge ${view.tone}`;
  document.getElementById('diagHardwareProofSummary').textContent = view.summary;
  document.getElementById('diagHardwareProofNextStep').textContent = view.nextStep;
  const reasonList = document.getElementById('diagHardwareProofReasons');
  reasonList.innerHTML = '';
  view.reasons.forEach((reason) => {
    const item = document.createElement('li');
    item.textContent = reason;
    reasonList.appendChild(item);
  });
}
function decisionSummaryText(item) {
  const status = text(item.review_status, 'pending');
  const reason = text(item.reason, 'unknown_reason');
  const last = item.last_decision && typeof item.last_decision === 'object' ? item.last_decision : null;
  if (!last) return `${status} | ${reason}`;
  return `${status} | ${reason} | ${text(last.decision, 'unknown')} @ ${text(last.timestamp, 'unknown time')}`;
}
function percent(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '0.0%';
  return `${(numeric * 100).toFixed(1)}%`;
}
function progressSummaryText(progressSummary) {
  if (!progressSummary || typeof progressSummary !== 'object') return 'not reported';
  const total = Number(progressSummary.total || 0);
  const decided = Number(progressSummary.decided || 0);
  const pending = Number(progressSummary.pending || 0);
  const coverageRate = percent(progressSummary.coverage_rate || 0);
  return `${decided}/${total} decided | ${pending} pending | coverage ${coverageRate}`;
}
function decisionDistributionText(distribution) {
  if (!distribution || typeof distribution !== 'object') return 'not reported';
  const entries = ['approved', 'rejected', 'needs_retry'].map((decision) => {
    const item = distribution[decision] && typeof distribution[decision] === 'object'
      ? distribution[decision]
      : {count: 0, ratio: 0};
    return `${decision} ${Number(item.count || 0)} (${percent(item.ratio || 0)})`;
  });
  return entries.join(' | ');
}
function nextPendingText(nextPendingSample) {
  if (!nextPendingSample || typeof nextPendingSample !== 'object') {
    return 'none';
  }
  return `${text(nextPendingSample.sample_id, 'unknown')} | ${text(nextPendingSample.reason, 'review')}`;
}
function routeProofSummaryText(routeProofSummary) {
  if (!routeProofSummary || typeof routeProofSummary !== 'object') return 'not reported';
  const coverageRate = Number(routeProofSummary.coverage_rate);
  const covered = Number(routeProofSummary.covered_checkpoints);
  const total = Number(routeProofSummary.total_checkpoints);
  const gateStatus = text(routeProofSummary.gate_status, 'unknown');
  const missing = Array.isArray(routeProofSummary.missing_checkpoints)
    ? routeProofSummary.missing_checkpoints.map((item) => String(item || '').trim()).filter(Boolean)
    : [];
  const coverageText = Number.isFinite(coverageRate) ? percent(coverageRate) : 'n/a';
  const countText = Number.isFinite(covered) && Number.isFinite(total) ? `${covered}/${total}` : 'n/a';
  const missingText = missing.length ? missing.join(', ') : 'none';
  return `coverage ${coverageText} | checkpoints ${countText} | gate ${gateStatus} | missing ${missingText}`;
}
function elevatorEvidenceText(elevatorAssist) {
  const evidence = elevatorAssist && typeof elevatorAssist.evidence === 'object' ? elevatorAssist.evidence : {};
  const keys = Object.keys(evidence);
  if (!keys.length) return 'not reported';
  return keys.map((key) => `${key}: ${JSON.stringify(evidence[key])}`).join(' | ');
}
function stateTransitionSummary(item) {
  if (!item || typeof item !== 'object') return 'unknown transition';
  return `${text(item.from_state, 'unknown')} -> ${text(item.to_state, 'unknown')} (${text(item.event, 'transition')}) @ ${text(item.timestamp, '-')}`;
}
function stateTransitionHistoryText(items) {
  const transitionHistory = Array.isArray(items) ? items : [];
  if (!transitionHistory.length) return 'no transition history';
  return `${Number(transitionHistory.length)} transition(s)`;
}
function applyReviewProgress(queuePayload) {
  const progressSummary = queuePayload && typeof queuePayload === 'object'
    ? queuePayload.progress_summary
    : null;
  const decisionDistribution = queuePayload && typeof queuePayload === 'object'
    ? queuePayload.decision_distribution
    : null;
  const nextPendingSample = queuePayload && typeof queuePayload === 'object'
    ? queuePayload.next_pending_sample
    : null;
  reviewQueueSnapshot = queuePayload && typeof queuePayload === 'object' ? queuePayload : null;
  document.getElementById('reviewProgressSummary').textContent = progressSummaryText(progressSummary);
  document.getElementById('reviewDecisionDistribution').textContent = decisionDistributionText(decisionDistribution);
  document.getElementById('reviewNextPending').textContent = nextPendingText(nextPendingSample);
  document.getElementById('reviewJumpPendingButton').disabled = !(
    nextPendingSample &&
    typeof nextPendingSample === 'object' &&
    text(nextPendingSample.sample_id, '')
  );
}
function updateSelectedReviewSummary() {
  const select = document.getElementById('reviewSampleSelect');
  const currentOption = select.options[select.selectedIndex];
  document.getElementById('reviewSelectedSummary').textContent = currentOption
    ? text(currentOption.dataset.summary, 'none')
    : 'none';
}
function renderReviewQueue(queuePayload) {
  applyReviewProgress(queuePayload);
  const queue = Array.isArray(queuePayload.review_queue) ? queuePayload.review_queue : [];
  const select = document.getElementById('reviewSampleSelect');
  select.innerHTML = '';
  if (!queue.length) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = 'No sample pending review';
    option.dataset.summary = 'queue empty';
    select.appendChild(option);
    select.disabled = true;
    document.getElementById('reviewSubmitButton').disabled = true;
    document.getElementById('reviewQueueStatus').textContent = `0 sample | ${text(queuePayload.manifest_read_error, 'queue empty')}`;
    updateSelectedReviewSummary();
    return;
  }
  queue.forEach((item) => {
    const option = document.createElement('option');
    option.value = text(item.sample_id, '');
    option.textContent = `${text(item.sample_id, 'unknown')} (${text(item.review_status, 'pending')})`;
    option.dataset.summary = decisionSummaryText(item);
    select.appendChild(option);
  });
  select.disabled = false;
  document.getElementById('reviewSubmitButton').disabled = false;
  document.getElementById('reviewQueueStatus').textContent = `${Number(queuePayload.review_queue_count || queue.length)} sample(s)`;
  updateSelectedReviewSummary();
}
function jumpToNextPending() {
  const nextPendingSample = reviewQueueSnapshot && typeof reviewQueueSnapshot === 'object'
    ? reviewQueueSnapshot.next_pending_sample
    : null;
  const sampleId = text((nextPendingSample || {}).sample_id, '');
  if (!sampleId) {
    document.getElementById('reviewResultMessage').textContent = 'No pending sample available.';
    return;
  }
  const select = document.getElementById('reviewSampleSelect');
  const option = Array.from(select.options).find((item) => item.value === sampleId);
  if (!option) {
    document.getElementById('reviewResultMessage').textContent = `Pending sample ${sampleId} is outside the current queue window.`;
    return;
  }
  select.value = sampleId;
  updateSelectedReviewSummary();
  document.getElementById('reviewResultMessage').textContent = `Focused pending sample ${sampleId}.`;
}
function drawMap(payload) {
  const canvas = document.getElementById('robotMap');
  const ctx = canvas.getContext('2d');
  const path = Array.isArray(payload.robot_path) ? payload.robot_path : [];
  const location = payload.robot_location || payload.location;
  const pose = payload.robot_pose || location || null;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#ddd';
  ctx.lineWidth = 1;
  for (let x = 0; x < canvas.width; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }
  if (!pose && path.length === 0) {
    ctx.fillStyle = '#666';
    ctx.fillText('waiting for /amcl_pose', 16, 24);
    return;
  }
  const points = path.length ? path : [pose];
  const xs = points.map(p => Number(p.x)).filter(Number.isFinite);
  const ys = points.map(p => Number(p.y)).filter(Number.isFinite);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const span = Math.max(maxX - minX, maxY - minY, 1);
  const pad = 24;
  const project = p => ({
    x: pad + ((Number(p.x) - minX) / span) * (canvas.width - pad * 2),
    y: canvas.height - pad - ((Number(p.y) - minY) / span) * (canvas.height - pad * 2)
  });
  ctx.strokeStyle = '#2364aa';
  ctx.lineWidth = 3;
  ctx.beginPath();
  points.forEach((p, index) => {
    const q = project(p);
    if (index === 0) ctx.moveTo(q.x, q.y);
    else ctx.lineTo(q.x, q.y);
  });
  ctx.stroke();
  if (pose) {
    const q = project(pose);
    ctx.fillStyle = '#d7263d';
    ctx.beginPath(); ctx.arc(q.x, q.y, 7, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#d7263d';
    ctx.beginPath();
    ctx.moveTo(q.x, q.y);
    ctx.lineTo(q.x + Math.cos(Number(pose.yaw || 0)) * 22, q.y - Math.sin(Number(pose.yaw || 0)) * 22);
    ctx.stroke();
  }
}
function updateJourney(payload) {
  const state = String(payload.state || 'waiting_for_trash');
  const copy = STATE_COPY[state] || [state.replaceAll('_', ' '), payload.message || '', 'waiting'];
  const step = copy[2];
  const activeIndex = STEP_ORDER.indexOf(step);
  const stateBadge = document.getElementById('stateBadge');
  stateBadge.textContent = state;
  stateBadge.classList.toggle('problem', state === 'failed' || state === 'needs_human_help' || state === 'network_error');
  document.getElementById('stateTitle').textContent = copy[0];
  document.getElementById('stateMessage').textContent = text(payload.phone_copy, text(payload.message, copy[1]));
  document.getElementById('speakerPrompt').textContent = text(payload.speaker_prompt, 'No speaker prompt.');
  document.getElementById('connectionState').textContent = state === 'network_error' ? 'offline' : 'online';
  document.querySelectorAll('#journeySteps .step').forEach((node) => {
    const index = STEP_ORDER.indexOf(node.dataset.step);
    node.classList.toggle('active', index === activeIndex);
    node.classList.toggle('done', activeIndex >= 0 && index < activeIndex);
  });
}
function readinessTone(phoneReadiness) {
  const primaryState = text(phoneReadiness.primary_state, 'waiting_for_robot_status');
  if (['login_required', 'remote_response_invalid', 'manual_takeover_required'].includes(primaryState)) return 'blocked';
  if (['waiting_for_command_ack', 'waiting_for_robot_status', 'local_ready_remote_status_waiting', 'remote_unreachable'].includes(primaryState)) return 'waiting';
  return 'ready';
}
function renderPhoneReadiness(phoneReadiness) {
  const panel = document.getElementById('phoneReadinessPanel');
  const readiness = phoneReadiness && typeof phoneReadiness === 'object' ? phoneReadiness : {};
  const primaryState = text(readiness.primary_state, 'waiting_for_robot_status');
  const tone = readinessTone(readiness);
  panel.classList.toggle('blocked', tone === 'blocked');
  panel.classList.toggle('waiting', tone === 'waiting');
  const badge = document.getElementById('phoneReadinessBadge');
  badge.textContent = readiness.can_continue ? 'can continue' : 'blocked';
  badge.classList.toggle('problem', !readiness.can_continue);
  document.getElementById('phoneReadinessTitle').textContent = primaryState.replaceAll('_', ' ');
  document.getElementById('phoneReadinessCopy').textContent = text(
    readiness.safe_phone_copy,
    '手机入口仍在等待可用状态。'
  );
  document.getElementById('phoneReadinessNext').textContent = text(
    readiness.recovery_hint,
    '等待状态刷新。'
  );
  document.getElementById('phoneReadinessSupport').textContent = text(
    readiness.support_level,
    'not reported'
  );
  document.getElementById('phoneReadinessBoundary').textContent = text(
    readiness.evidence_boundary,
    'local proof'
  );
  const notProven = Array.isArray(readiness.not_proven) ? readiness.not_proven.slice(0, 4) : [];
  document.getElementById('phoneReadinessNotProven').textContent = notProven.length
    ? notProven.join(', ')
    : 'not reported';
}
function showTelemetry(payload) {
  const location = payload.robot_location || payload.location;
  const pose = payload.robot_pose || location || null;
  const locationPanel = document.getElementById('locationPanel');
  locationPanel.hidden = !location;
  if (payload.robot_pose) {
    locationPanel.hidden = false;
  }
  document.getElementById('locationFrame').textContent = pose ? pose.frame_id : 'unknown';
  document.getElementById('locationX').textContent = pose ? fmt(Number(pose.x)) : '-';
  document.getElementById('locationY').textContent = pose ? fmt(Number(pose.y)) : '-';
  document.getElementById('locationYaw').textContent = pose ? fmt(Number(pose.yaw)) : '-';
  document.getElementById('pathCount').textContent = `${Array.isArray(payload.robot_path) ? payload.robot_path.length : 0} points`;
  document.getElementById('poseAge').textContent = pose ? new Date(Number(pose.updated_at || 0) * 1000).toLocaleTimeString() : 'no pose';
  drawMap(payload);
}
function showStatus(payload) {
  document.getElementById('status').textContent = JSON.stringify(payload, null, 2);
  renderPhoneReadiness(payload.phone_readiness);
  updateJourney(payload);
  showTelemetry(payload);
  const collectButton = document.getElementById('collectButton');
  const dropoffButton = document.getElementById('dropoffButton');
  const cancelButton = document.getElementById('cancelButton');
  collectButton.disabled = !Boolean(payload.can_collect);
  dropoffButton.disabled = !Boolean(payload.can_confirm_dropoff);
  cancelButton.disabled = !Boolean(payload.can_cancel);
}
function showDiagnostics(payload) {
  const panel = document.getElementById('diagnosticsPanel');
  panel.hidden = false;
  const failure = payload.failure || {};
  const latest = payload.latest_status || {};
  const visionSamples = payload.vision_samples || {};
  const routeProofSummary = payload.route_proof_summary || {};
  const routeProofStatus = payload.route_proof_status || {};
  const hardwareProof = payload.hardware_proof || {};
  const elevatorAssist = payload.elevator_assist || {};
  const elevatorAssistStatus = payload.elevator_assist_status || {};
  const refs = Array.isArray(payload.log_refs) ? payload.log_refs : [];
  const taskRecord = failure.task_record_path || (payload.last_task || {}).task_record_path || latest.task_record_path || '';
  const humanIntervention = Boolean(
    failure.human_intervention_required
    || payload.human_intervention_required
    || failure.message === 'manual takeover required'
  );
  const transitionHistory = Array.isArray(payload.state_transition_history)
    ? payload.state_transition_history
    : (Array.isArray(failure.state_transition_history) ? failure.state_transition_history : []);
  const source = text(
    failure.source || payload.source || (payload.last_task || {}).source || latest.source,
    'simulated'
  );
  renderVisionIntegrity(visionSamples);
  renderHardwareProof(hardwareProof);
  document.getElementById('diagSoftware').textContent = text(payload.software_version, 'not reported');
  document.getElementById('diagMap').textContent = text(payload.map_version, 'not reported');
  document.getElementById('diagRoute').textContent = text(payload.route_version, 'not reported');
  document.getElementById('diagFailure').textContent = text(failure.error_code || failure.message, 'none reported');
  document.getElementById('diagSource').textContent = source;
  document.getElementById('diagFailureCode').textContent = text(
    failure.failure_code || failure.error_code,
    'not reported'
  );
  document.getElementById('diagEvidenceRef').textContent = text(
    failure.evidence_ref || payload.evidence_ref || taskRecord,
    'not reported'
  );
  document.getElementById('diagHumanIntervention').textContent = humanIntervention ? 'Required' : 'No';
  document.getElementById('diagTask').textContent = text(taskRecord, 'not reported');
  document.getElementById('diagStatusFile').textContent = text(payload.operator_status_file, 'not reported');
  document.getElementById('diagStateTransitionHistory').textContent = stateTransitionHistoryText(transitionHistory);
  document.getElementById('diagVisionSamples').textContent = visionSamples.read_error
    ? visionSamples.read_error
    : `${Number(visionSamples.sample_count || 0)} samples`;
  document.getElementById('diagLatestVisionSample').textContent = text(
    visionSamples.latest_sample_ref,
    visionSamples.sample_count ? 'sample reference missing' : 'no samples'
  );
  const reviewQueue = Array.isArray(visionSamples.review_queue) ? visionSamples.review_queue : [];
  const progressSummary = visionSamples.progress_summary && typeof visionSamples.progress_summary === 'object'
    ? visionSamples.progress_summary
    : {};
  const nextReview = visionSamples.next_pending_sample && typeof visionSamples.next_pending_sample === 'object'
    ? visionSamples.next_pending_sample
    : null;
  document.getElementById('diagReviewQueue').textContent = `${Number(progressSummary.pending || 0)} pending / ${Number(progressSummary.total || 0)} total`;
  document.getElementById('diagNextReviewSample').textContent = nextReview
    ? `${text(nextReview.reason, 'review')} ${text(nextReview.sample_ref, text(nextReview.sample_id, 'unknown'))}`
    : 'no pending sample';
  document.getElementById('diagRouteProofState').textContent = text(routeProofStatus.state, 'unknown');
  document.getElementById('diagRouteProofSummary').textContent = routeProofSummaryText(routeProofSummary);
  document.getElementById('diagRouteProofReason').textContent = text(
    routeProofStatus.blocking_reason || routeProofStatus.reason,
    'not reported'
  );
  document.getElementById('diagRouteProofSource').textContent = text(routeProofStatus.source, 'not reported');
  document.getElementById('diagElevatorAssistState').textContent = text(
    `${text(elevatorAssistStatus.state, 'unknown')} / ${text(elevatorAssist.phase || elevatorAssist.state, 'none')}`,
    'unknown'
  );
  document.getElementById('diagElevatorAssistPrompt').textContent = text(
    elevatorAssist.speaker_prompt || elevatorAssist.phone_copy,
    'not reported'
  );
  document.getElementById('diagElevatorAssistEvidence').textContent = elevatorEvidenceText(elevatorAssist);
  document.getElementById('diagElevatorAssistNextStep').textContent = text(
    elevatorAssistStatus.next_step || elevatorAssistStatus.reason,
    'not reported'
  );
  document.getElementById('diagRecoveryHint').textContent = humanIntervention
    ? 'Manual takeover required: keep task in safe mode,复位现场阻塞后，可重新发起任务。'
    : 'No manual takeover required.';
  const transitionHistoryList = document.getElementById('diagStateTransitionHistoryList');
  transitionHistoryList.innerHTML = '';
  if (!transitionHistory.length) {
    const item = document.createElement('li');
    item.textContent = 'No transition history reported.';
    transitionHistoryList.appendChild(item);
  } else {
    transitionHistory.slice(-5).forEach((transition) => {
      const item = document.createElement('li');
      item.textContent = stateTransitionSummary(transition);
      transitionHistoryList.appendChild(item);
    });
  }
  renderReviewQueue({
    review_queue_count: visionSamples.review_queue_count,
    review_queue: reviewQueue,
    progress_summary: visionSamples.progress_summary,
    decision_distribution: visionSamples.decision_distribution,
    next_pending_sample: visionSamples.next_pending_sample,
    manifest_read_error: visionSamples.read_error,
  });
  const refList = document.getElementById('diagRefs');
  refList.innerHTML = '';
  [...refs, payload.vision_sample_manifest_ref, hardwareProof.artifact_ref].filter(Boolean).forEach((ref) => {
    const item = document.createElement('li');
    item.textContent = ref;
    refList.appendChild(item);
  });
}
async function api(path, options) {
  try {
    const response = await fetch(path, options || {});
    const payload = await response.json();
    showStatus(payload);
    return payload;
  } catch (error) {
    showStatus({
      state: 'network_error',
      message: String(error),
      can_collect: false,
      can_confirm_dropoff: false,
      can_cancel: false
    });
    return null;
  }
}
async function refresh() { await api('/api/status'); }
async function collect() {
  await api('/api/collect', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({target: document.getElementById('target').value})
  });
}
async function confirmDropoff() { await api('/api/dropoff/confirm', {method: 'POST'}); }
async function cancelTask() { await api('/api/cancel', {method: 'POST'}); }
async function loadReviewQueue() {
  try {
    const response = await fetch('/api/vision/review-queue');
    const payload = await response.json();
    renderReviewQueue(payload);
    if (!payload.ok && payload.error) {
      document.getElementById('reviewResultMessage').textContent = `${text(payload.error.code, 'error')}: ${text(payload.error.message, 'request failed')}`;
    }
  } catch (error) {
    document.getElementById('reviewQueueStatus').textContent = `queue load failed: ${String(error)}`;
  }
}
async function submitReviewDecision() {
  const sampleSelect = document.getElementById('reviewSampleSelect');
  const sampleId = text(sampleSelect.value, '');
  if (!sampleId) {
    document.getElementById('reviewResultMessage').textContent = 'sample_id is required';
    return;
  }
  const body = {
    sample_id: sampleId,
    decision: text(document.getElementById('reviewDecisionSelect').value, 'approved'),
    option: text(document.getElementById('reviewOptionInput').value, ''),
    operator: text(document.getElementById('reviewOperatorInput').value, ''),
    comment: text(document.getElementById('reviewCommentInput').value, '')
  };
  try {
    const response = await fetch('/api/vision/review-decisions', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    const payload = await response.json();
    if (response.ok && payload.ok) {
      document.getElementById('reviewResultMessage').textContent = `stored ${payload.decision} for ${payload.sample_id} at ${text(payload.stored_at, 'unknown time')}`;
      await loadReviewQueue();
      return;
    }
    const error = payload.error || {};
    document.getElementById('reviewResultMessage').textContent = `${text(error.code, 'error')}: ${text(error.message, 'request failed')}`;
  } catch (error) {
    document.getElementById('reviewResultMessage').textContent = `submit failed: ${String(error)}`;
  }
}
async function diagnostics() {
  const payload = await api('/api/diagnostics');
  if (payload) showDiagnostics(payload);
}
document.getElementById('reviewSampleSelect').addEventListener('change', updateSelectedReviewSummary);
setInterval(refresh, 1000);
refresh();
loadReviewQueue();
</script>
</body>
</html>"""


def status_payload(state, message="", **extra):
    elevator_assist = normalize_elevator_assist(
        extra.pop("elevator_assist", None),
        state=state,
        message=message,
    )
    prompt = operator_prompt_for_state(state, elevator_assist=elevator_assist)
    payload = {
        "api_version": API_VERSION,
        "state": state,
        "message": message,
        "phone_copy": prompt["phone_copy"],
        "speaker_prompt": prompt["speaker_prompt"],
        "elevator_assist": elevator_assist,
        "updated_at": time.time(),
    }
    payload.update(extra)
    if elevator_assist.get("enabled"):
        payload["phone_copy"] = elevator_assist.get("phone_copy") or payload["phone_copy"]
        payload["speaker_prompt"] = elevator_assist.get("speaker_prompt") or payload["speaker_prompt"]
    return payload


def parse_json_body(handler):
    try:
        length = int(handler.headers.get("Content-Length") or 0)
    except ValueError as exc:
        raise ValueError(f"invalid Content-Length: {exc}") from exc
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8") or "{}")


def _remote_route(path):
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


def _remote_auth_token(gateway):
    # 本地 mock cloud 允许用 gateway 属性或环境变量注入 token，避免把凭证写进仓库。
    for attr in ("mock_cloud_bearer_token", "remote_mock_cloud_bearer_token", "remote_bearer_token"):
        value = str(getattr(gateway, attr, "") or "").strip()
        if value:
            return value
    for key in REMOTE_AUTH_ENV_KEYS:
        value = str(os.environ.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _remote_auth_header(headers):
    # 只接受标准 Bearer 格式；错误格式按 auth_failed 处理，不回显原 header。
    value = str(headers.get("Authorization") or headers.get("authorization") or "").strip()
    if not value:
        return ""
    prefix = "Bearer "
    if not value.startswith(prefix):
        return ""
    return value[len(prefix):].strip()


def _remote_readiness_for_auth_failure():
    # 401 响应也返回 readiness，手机端不用解析底层错误就能给恢复建议。
    return {
        "remote_ready": False,
        "cloud_reachable": True,
        "last_command_ack": "",
        "status_stale": True,
        "retry_hint": "check_auth",
        "auth_state": "auth_failed",
        "degradation_state": "auth_failed",
        "safe_phone_copy": REMOTE_DEGRADATION_COPY["auth_failed"],
        "status_age_sec": None,
        "pending_command_count": 0,
        "queue_persisted": False,
        "state_path_configured": False,
        "proof_schema": "",
    }


def _remote_readiness_for_malformed_response():
    # malformed_response 是 phone-safe 分类，不把异常栈或原始报文暴露给用户。
    return {
        "remote_ready": False,
        "cloud_reachable": True,
        "last_command_ack": "",
        "status_stale": True,
        "retry_hint": "contact_support",
        "auth_state": "required",
        "degradation_state": "malformed_response",
        "safe_phone_copy": REMOTE_DEGRADATION_COPY["malformed_response"],
        "status_age_sec": None,
        "pending_command_count": 0,
        "queue_persisted": False,
        "state_path_configured": False,
        "proof_schema": "",
    }


def _with_remote_auth_state(payload, auth_state):
    # readiness 在成功请求里升级为 authorized；失败请求只给 phone-safe 原因。
    if not isinstance(payload, dict):
        return payload
    for container in (payload, payload.get("status")):
        if not isinstance(container, dict):
            continue
        readiness = container.get("remote_readiness")
        if not isinstance(readiness, dict):
            continue
        readiness["auth_state"] = auth_state
        if auth_state == "auth_failed":
            # 失败态统一降级，避免局部字段仍显示可继续操作。
            readiness["remote_ready"] = False
            readiness["degradation_state"] = "auth_failed"
            readiness["retry_hint"] = "check_auth"
            readiness["safe_phone_copy"] = REMOTE_DEGRADATION_COPY["auth_failed"]
    return payload


def _unknown_gate(name, *, status="unknown", retry_hint="contact_support"):
    # 这些 gate 在本地 operator 里可能没有产物；保守暴露 unknown/not_run，避免把缺证据写成通过。
    return {
        "name": name,
        "status": status,
        "retry_hint": retry_hint,
        "safe_phone_copy": "本地页面尚未收到该上线前检查结果。",
    }


def _copy_gate(value, name):
    # 只复制手机端需要的白名单字段，避免 preflight 或 drill 产物泄漏路径、凭证或栈信息。
    if not isinstance(value, dict):
        return _unknown_gate(name, status="not_run", retry_hint="contact_support")
    return {
        "name": name,
        "status": str(value.get("overall_status") or value.get("status") or "unknown"),
        "retry_hint": str(value.get("retry_hint") or "contact_support"),
        "safe_phone_copy": str(
            value.get("safe_summary")
            or value.get("safe_phone_copy")
            or value.get("summary")
            or "上线前检查需要继续确认。"
        ),
        "evidence_boundary": str(value.get("evidence_boundary") or ""),
        "not_proven": list(value.get("not_proven")) if isinstance(value.get("not_proven"), list) else [],
    }


def _remote_degradation(remote_readiness):
    if not isinstance(remote_readiness, dict):
        return "status_stale"
    return str(remote_readiness.get("degradation_state") or "status_stale").strip() or "status_stale"


def _local_action_permissions(status):
    # 聚合只读已有 action permissions；按钮能否点击仍由原字段决定，避免破坏旧客户端。
    status = status if isinstance(status, dict) else {}
    return {
        "can_collect": bool(status.get("can_collect")),
        "can_confirm_dropoff": bool(status.get("can_confirm_dropoff")),
        "can_cancel": bool(status.get("can_cancel")),
    }


def build_phone_readiness(status, *, remote_readiness=None, cloud_preflight=None, backup_restore=None):
    """Build the phone-first readiness summary used by `/api/status`.

    这个 helper 不创造机器人状态；它只把 local status、action permission、
    remote_readiness 和可选上线前 gate 归类成手机能直接显示的恢复路径。
    """
    status = status if isinstance(status, dict) else {}
    remote = remote_readiness if isinstance(remote_readiness, dict) else {}
    permissions = _local_action_permissions(status)
    state = str(status.get("state") or "unknown").strip() or "unknown"
    remote_state = _remote_degradation(remote)
    can_use_local_action = any(permissions.values())
    primary_state = "ready"
    next_action = "continue_local_flow"
    can_continue = bool(can_use_local_action)
    support_level = "local_fallback"

    if state in {"failed", "needs_human_help"} or bool(
        status.get("elevator_assist", {}).get("requires_human_help")
        if isinstance(status.get("elevator_assist"), dict)
        else False
    ):
        primary_state = "manual_takeover_required"
        next_action = "manual_takeover"
        can_continue = False
        support_level = "human_takeover_required"
    elif remote_state == "auth_failed":
        primary_state = "login_required"
        next_action = "check_auth"
        can_continue = False
        support_level = "remote_blocked_local_fallback_available" if can_use_local_action else "remote_blocked"
    elif remote_state == "cloud_unreachable":
        primary_state = "remote_unreachable"
        next_action = "retry_cloud"
        can_continue = bool(can_use_local_action)
        support_level = "local_fallback_only" if can_use_local_action else "remote_blocked"
    elif remote_state == "malformed_response":
        primary_state = "remote_response_invalid"
        next_action = "contact_support"
        can_continue = False
        support_level = "support_required"
    elif remote_state == "command_pending":
        primary_state = "waiting_for_command_ack"
        next_action = "wait_for_command_ack"
        can_continue = False
        support_level = "remote_waiting_ack"
    elif remote_state == "status_stale":
        if can_use_local_action:
            primary_state = "local_ready_remote_status_waiting"
            next_action = "continue_local_or_wait_remote_status"
            can_continue = True
            support_level = "local_fallback"
        else:
            primary_state = "waiting_for_robot_status"
            next_action = "wait_for_robot_status"
            can_continue = False
            support_level = "remote_waiting_status"
    elif not can_use_local_action:
        primary_state = "monitoring"
        next_action = "watch_progress"
        can_continue = True
        support_level = "monitoring_only"
    else:
        support_level = "phone_ready"

    recovery_hint = PHONE_READINESS_NEXT_ACTION_COPY[next_action]
    safe_phone_copy = PHONE_READINESS_PRIMARY_COPY[primary_state]
    if remote_state in REMOTE_DEGRADATION_COPY and remote_state != "ok":
        safe_phone_copy = REMOTE_DEGRADATION_COPY[remote_state]
    if primary_state == "local_ready_remote_status_waiting":
        safe_phone_copy = "本地手机入口可继续；远程状态仍在等待小车上报。"

    return {
        "schema": PHONE_READINESS_SCHEMA,
        "schema_version": 1,
        "api_version": API_VERSION,
        "evidence_boundary": PHONE_READINESS_EVIDENCE_BOUNDARY,
        "primary_state": primary_state,
        "can_continue": bool(can_continue),
        "next_action": next_action,
        "safe_phone_copy": safe_phone_copy,
        "recovery_hint": recovery_hint,
        "support_level": support_level,
        "local_delivery": {
            "state": state,
            "phone_copy": str(status.get("phone_copy") or ""),
            "speaker_prompt": str(status.get("speaker_prompt") or ""),
        },
        "action_permissions": permissions,
        "remote_readiness": dict(remote),
        "cloud_preflight": _copy_gate(cloud_preflight, "cloud_preflight"),
        "backup_restore": _copy_gate(backup_restore, "backup_restore"),
        "not_proven": list(PHONE_READINESS_NOT_PROVEN),
    }


def _robot_id_for_gateway(gateway):
    # operator_gateway 目前没有强制 robot_id 参数；本地 mock 与 remote_bridge 文档默认 trashbot-001。
    for attr in ("robot_id", "remote_robot_id", "mock_cloud_robot_id"):
        value = str(getattr(gateway, attr, "") or "").strip()
        if value:
            return value
    return "trashbot-001"


def _status_with_phone_readiness(gateway, mock_cloud):
    payload = dict(gateway.snapshot())
    remote_readiness = payload.get("remote_readiness")
    if not isinstance(remote_readiness, dict):
        try:
            remote_payload = mock_cloud.get_status(_robot_id_for_gateway(gateway))
            remote_readiness = remote_payload.get("remote_readiness", {})
        except ValueError:
            remote_readiness = {}
    # 可选 gate 字段只在调用方已提供时采纳；默认 not_run/unknown，不推断生产 readiness。
    payload["phone_readiness"] = build_phone_readiness(
        payload,
        remote_readiness=remote_readiness,
        cloud_preflight=payload.get("cloud_preflight") or payload.get("remote_preflight"),
        backup_restore=payload.get("backup_restore") or payload.get("backup_restore_drill"),
    )
    return payload


def make_handler(gateway):
    mock_cloud = getattr(gateway, "mock_cloud", None)
    if mock_cloud is None:
        state_path = (
            getattr(gateway, "mock_cloud_state_path", "")
            or getattr(gateway, "remote_mock_cloud_state_path", "")
            or ""
        )
        mock_cloud = MockCloudStore(state_path=state_path, auth_required=bool(_remote_auth_token(gateway)))
        setattr(gateway, "mock_cloud", mock_cloud)

    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, status, payload):
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _remote_authorized(self):
            expected_bearer_token = _remote_auth_token(gateway)
            if hasattr(mock_cloud, "auth_required"):
                mock_cloud.auth_required = bool(expected_bearer_token)
            if not expected_bearer_token:
                return True
            return _remote_auth_header(self.headers) == expected_bearer_token

        def _send_remote_unauthorized(self):
            readiness = _remote_readiness_for_auth_failure()
            payload = remote_error("unauthorized", "remote control authorization failed")
            payload["remote_readiness"] = readiness
            self._send_json(401, payload)

        def _remote_auth_state(self):
            return "authorized" if _remote_auth_token(gateway) else "mock_not_required"

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            if path == "/" or path == "/index.html":
                body = HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if path == "/api/status":
                self._send_json(200, _status_with_phone_readiness(gateway, mock_cloud))
                return
            if path == "/api/diagnostics":
                self._send_json(200, gateway.diagnostics())
                return
            if path == "/api/vision/review-queue":
                self._send_json(200, gateway.vision_review_queue())
                return
            remote_route = _remote_route(path)
            if remote_route:
                if not self._remote_authorized():
                    self._send_remote_unauthorized()
                    return
                route_name, robot_id, command_id = remote_route
                try:
                    if route_name == "commands_next":
                        payload = mock_cloud.next_command(
                            robot_id,
                            last_ack_id=next(iter(query.get("last_ack_id", [])), ""),
                        )
                        self._send_json(200, payload)
                        return
                    if route_name == "status":
                        payload = _with_remote_auth_state(
                            mock_cloud.get_status(robot_id),
                            self._remote_auth_state(),
                        )
                        self._send_json(200, payload)
                        return
                    if route_name == "ack":
                        status, payload = mock_cloud.get_ack(robot_id, command_id)
                        self._send_json(status, payload)
                        return
                except ValueError as exc:
                    self._send_json(400, remote_error("bad_request", str(exc)))
                    return
            self._send_json(404, status_payload("not_found", f"unknown path: {path}"))

        def do_POST(self):
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            try:
                body = parse_json_body(self)
            except (ValueError, json.JSONDecodeError) as exc:
                self._send_json(400, status_payload("bad_request", str(exc)))
                return
            if not isinstance(body, dict):
                self._send_json(400, status_payload("bad_request", "JSON body must be an object"))
                return
            remote_route = _remote_route(path)
            if remote_route:
                if not self._remote_authorized():
                    self._send_remote_unauthorized()
                    return
                route_name, robot_id, command_id = remote_route
                try:
                    if route_name == "commands":
                        status, payload = mock_cloud.submit_command(robot_id, body)
                        payload = _with_remote_auth_state(
                            payload,
                            self._remote_auth_state(),
                        )
                        self._send_json(status, payload)
                        return
                    if route_name == "status":
                        payload = _with_remote_auth_state(
                            mock_cloud.post_status(robot_id, body),
                            self._remote_auth_state(),
                        )
                        self._send_json(200, payload)
                        return
                    if route_name == "ack":
                        payload = _with_remote_auth_state(
                            mock_cloud.post_ack(robot_id, command_id, body),
                            self._remote_auth_state(),
                        )
                        self._send_json(200, payload)
                        return
                except ValueError as exc:
                    payload = remote_error("bad_request", str(exc))
                    payload["remote_readiness"] = _remote_readiness_for_malformed_response()
                    self._send_json(400, payload)
                    return
            if path == "/api/collect":
                target = body.get("target") or next(iter(query.get("target", [])), "")
                try:
                    trash_type = int(body.get("trash_type", 0) or 0)
                except (TypeError, ValueError) as exc:
                    self._send_json(400, status_payload("bad_request", f"invalid trash_type: {exc}"))
                    return
                status, payload = gateway.start_collection(target, trash_type)
                self._send_json(status, payload)
                return
            if path == "/api/dropoff/confirm":
                try:
                    accepted = parse_bool(body.get("accepted"), default=True)
                except ValueError as exc:
                    self._send_json(400, status_payload("bad_request", str(exc)))
                    return
                status, payload = gateway.confirm_dropoff(accepted)
                self._send_json(status, payload)
                return
            if path == "/api/cancel":
                status, payload = gateway.cancel_collection()
                self._send_json(status, payload)
                return
            if path == "/api/vision/review-decisions":
                status, payload = gateway.submit_review_decision(body)
                self._send_json(status, payload)
                return
            self._send_json(404, status_payload("not_found", f"unknown path: {path}"))

        def log_message(self, _format, *_args):
            return

    return Handler
