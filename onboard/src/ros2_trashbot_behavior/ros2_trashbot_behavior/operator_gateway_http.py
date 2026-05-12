import json
import os
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from ros2_trashbot_behavior.remote_cloud_relay import (
    build_phone_credential_rotation_summary,
    build_phone_network_recovery_summary,
    build_phone_oss_cdn_manifest_summary,
    build_phone_production_store_queue_summary,
    build_phone_production_recovery_summary,
    build_phone_provisioning_audit_summary,
    build_phone_queue_ordering_drill_summary,
    build_phone_transaction_isolation_summary,
)
from ros2_trashbot_behavior.remote_bridge_protocol import parse_bool


API_VERSION = "slice2.operator.v1"
REMOTE_PROTOCOL_VERSION = "trashbot.remote.v1"
PHONE_READINESS_SCHEMA = "trashbot.phone_readiness.v1"
PHONE_READINESS_EVIDENCE_BOUNDARY = "software_proof_docker_phone_task_flow_readiness_gate"
PHONE_COMMAND_SAFETY_EVIDENCE_BOUNDARY = "software_proof_docker_phone_command_safety_browser_gate"
PHONE_TASK_FLOW_SCHEMA = "trashbot.phone_task_flow_readiness.v1"
PHONE_SUPPORT_BUNDLE_SCHEMA = "trashbot.phone_support_bundle.v1"
PHONE_SUPPORT_BUNDLE_EVIDENCE_BOUNDARY = "software_proof_docker_phone_support_bundle_gate"
VOICE_PROMPT_READINESS_SCHEMA = "trashbot.voice_prompt_readiness.v1"
VOICE_PROMPT_READINESS_EVIDENCE_BOUNDARY = "software_proof_docker_phone_voice_prompt_readiness_gate"
PHONE_OFFLINE_RESUME_READINESS_SCHEMA = "trashbot.phone_offline_resume_readiness.v1"
PHONE_OFFLINE_RESUME_READINESS_EVIDENCE_BOUNDARY = "software_proof_docker_phone_offline_resume_gate"
PHONE_PWA_EVIDENCE_BOUNDARY = "software_proof_docker_phone_pwa_installability_gate"
COMMAND_SAFETY_SCHEMA = "trashbot.command_safety.v1"
REMOTE_COMMAND_TYPES = {"collect", "confirm_dropoff", "cancel"}
REMOTE_STATUS_STALE_AFTER_SEC = 90.0
REMOTE_PERSISTENCE_SCHEMA = "trashbot.mock_cloud_store.v1"
PWA_THEME_COLOR = "#126b5f"
PWA_BACKGROUND_COLOR = "#f5f7f8"
PWA_ICON_SIZES = ("192x192", "512x512")
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
    "real_phone_device_browser",
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
    "refresh_diagnostics_ref": "刷新状态；如果仍不可用，请重新生成诊断引用。",
}

COMMAND_SAFETY_ACK_COPY = (
    "ACK 只表示指令已被小车侧 bridge 受理或处理，不能代表送达成功、真实运动、HIL 或真实云成功。"
)

COMMAND_SAFETY_BLOCK_COPY = {
    "allowed": "当前状态允许这个操作。",
    "not_permitted_by_local_state": "当前机器人状态不允许这个操作。",
    "status_stale": "正在等待小车上报最新状态，主操作暂不可用。",
    "command_pending": "上一条指令仍在等待 ACK，暂不重复下发。",
    "auth_failed": "手机登录或访问码未通过，主操作暂不可用。",
    "cloud_unreachable": "远程控制通道暂不可用，主操作暂不可用。",
    "malformed_response": "远程控制返回异常，主操作暂不可用。",
    "diagnostic_refs_missing": "诊断对象引用缺失，主操作暂不可用。",
    "diagnostic_refs_invalid": "诊断对象引用损坏，主操作暂不可用。",
    "diagnostic_refs_stale": "诊断对象引用已过期，主操作暂不可用。",
    "manual_takeover_required": "当前需要人工接管，主操作暂不可用。",
    "monitoring_only": "任务正在进行，请继续观察或按需取消。",
}

PHONE_TASK_FLOW_STEPS = (
    "connection_ready",
    "destination_confirmed",
    "trash_loaded",
    "start_delivery",
    "status_explained",
    "help_or_diagnostics",
)

PHONE_TASK_FLOW_LABELS = {
    "connection_ready": "连接/就绪",
    "destination_confirmed": "目的地",
    "trash_loaded": "装载确认",
    "start_delivery": "一键发车",
    "status_explained": "状态解释",
    "help_or_diagnostics": "求助/诊断",
}

PHONE_TASK_FLOW_FORBIDDEN_COPY_MARKERS = (
    "ros topic",
    "/cmd_vel",
    "serial",
    "baudrate",
    "json payload",
    "token",
    "authorization",
    "cloud secret",
    "wave rover",
)

PHONE_SUPPORT_BUNDLE_FORBIDDEN_MARKERS = (
    "token",
    "authorization",
    "bearer",
    "oss ak",
    "oss sk",
    "access_key",
    "secret",
    "password",
    "root password",
    "database url",
    "db url",
    "queue url",
    "ros topic",
    "/cmd_vel",
    "serial",
    "baudrate",
    "wave rover",
    "traceback",
    "checksum",
    "artifact",
    "/tmp/",
    "/users/",
    "/home/",
    "http://",
    "https://",
)

VOICE_PROMPT_FORBIDDEN_MARKERS = (
    # voice prompt 会出现在首屏和 diagnostics，必须比普通状态文本更严格地过滤。
    "token",
    "authorization",
    "bearer",
    "oss ak",
    "oss sk",
    "access_key",
    "secret",
    "password",
    "root password",
    "database url",
    "db url",
    "queue url",
    "ros topic",
    "/cmd_vel",
    "serial",
    "baudrate",
    "wave rover",
    "traceback",
    "checksum",
    "artifact",
    "/tmp/",
    "/users/",
    "/home/",
    "http://",
    "https://",
)

PHONE_OFFLINE_RESUME_FORBIDDEN_MARKERS = (
    # offline/resume copy 会出现在 service worker 离线壳层，过滤范围必须覆盖支持交接和接口文档的红线。
    "token",
    "authorization",
    "bearer",
    "oss ak",
    "oss sk",
    "access_key",
    "secret",
    "password",
    "root password",
    "database url",
    "db url",
    "queue url",
    "ros topic",
    "/cmd_vel",
    "serial",
    "baudrate",
    "wave rover",
    "traceback",
    "checksum",
    "artifact",
    "complete artifact",
    "/tmp/",
    "/users/",
    "/home/",
    "http://",
    "https://",
)

VOICE_PROMPT_TRIGGER_REASONS = {
    "waiting_for_trash": "等待用户放入垃圾并在手机上确认。",
    "loaded_and_ready": "垃圾已确认放入，等待用户发车。",
    "delivering": "小车正在送往垃圾站。",
    "navigating": "小车正在导航或沿路线移动。",
    "waiting_elevator_open": "小车已到电梯厅，正在等待电梯开门。",
    "requesting_floor_help": "小车已进入电梯，需要旁人帮忙按目标楼层。",
    "waiting_target_floor": "小车正在等待目标楼层。",
    "target_floor_unconfirmed": "目标楼层尚未确认，需要人工确认。",
    "unsafe_to_exit": "目标楼层出口不安全，需要人工接管。",
    "arrived_at_station": "小车已到垃圾站，等待用户确认投放。",
    "returning": "投放确认后，小车正在返回或等待下一次任务。",
    "completed": "任务已完成。",
    "failed": "任务失败，需要查看诊断或请求帮助。",
    "needs_human_help": "当前流程需要人工接管。",
}

PHONE_SUPPORT_BUNDLE_SAFE_KEYS = {
    "schema",
    "schema_version",
    "api_version",
    "state",
    "primary_state",
    "next_action",
    "support_level",
    "failure_code",
    "error_code",
    "final_state",
    "source",
    "map_version",
    "route_version",
    "software_version",
    "task_id",
    "status",
    "overall_status",
    "evidence_boundary",
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
    "diagnostic_refs_missing": "诊断对象引用缺失。",
    "diagnostic_refs_invalid": "诊断对象引用损坏。",
    "diagnostic_refs_stale": "诊断对象引用已过期。",
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


def build_pwa_manifest():
    # manifest 只描述本地 operator shell；start_url/scope 不允许落到 API 或远程命令面。
    return {
        "name": "Trashbot Operator Local Fallback",
        "short_name": "Trashbot",
        "description": "Local phone fallback for checking robot status and safe command gates.",
        "start_url": "/?source=pwa",
        "scope": "/",
        "display": "standalone",
        "theme_color": PWA_THEME_COLOR,
        "background_color": PWA_BACKGROUND_COLOR,
        "icons": [
            {
                "src": f"/pwa-icon-{size}.svg",
                "sizes": size,
                "type": "image/svg+xml",
                "purpose": "any maskable",
            }
            for size in PWA_ICON_SIZES
        ],
        "evidence_boundary": PHONE_PWA_EVIDENCE_BOUNDARY,
    }


def build_pwa_icon(size):
    # SVG 图标没有机器人硬件细节，只提供 installability gate 所需的安全 shell 图标。
    try:
        side = int(str(size).split("x", 1)[0])
    except (TypeError, ValueError):
        side = 192
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{side}" height="{side}" viewBox="0 0 192 192" role="img" aria-label="Trashbot">
  <rect width="192" height="192" rx="32" fill="{PWA_THEME_COLOR}"/>
  <rect x="46" y="64" width="100" height="82" rx="18" fill="#ffffff"/>
  <circle cx="76" cy="100" r="10" fill="{PWA_THEME_COLOR}"/>
  <circle cx="116" cy="100" r="10" fill="{PWA_THEME_COLOR}"/>
  <path d="M72 128h48" stroke="{PWA_THEME_COLOR}" stroke-width="10" stroke-linecap="round"/>
</svg>"""


OFFLINE_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#126b5f">
  <meta name="description" content="Trashbot offline fallback shell.">
  <title>Trashbot Offline</title>
  <style>
    :root { color-scheme: light; --bg: #f5f7f8; --ink: #172026; --muted: #60707c; --line: #d7dee3; --accent: #126b5f; }
    * { box-sizing: border-box; }
    body { background: var(--bg); color: var(--ink); font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 0; }
    main { display: grid; gap: 14px; margin: 0 auto; max-width: 640px; padding: 16px; }
    h1 { font-size: 22px; margin: 0; }
    p { color: var(--muted); line-height: 1.45; margin: 0; }
    .panel { background: #fff; border: 1px solid var(--line); border-radius: 8px; display: grid; gap: 12px; padding: 16px; }
    .badge { background: #fff7e6; border: 1px solid #f0cf8a; border-radius: 999px; color: #9a5b00; font-size: 12px; font-weight: 700; padding: 6px 10px; width: fit-content; }
    .row { display: flex; flex-wrap: wrap; gap: 8px; }
    button { border: 1px solid var(--line); border-radius: 8px; font: inherit; font-weight: 650; min-height: 44px; padding: 10px 12px; }
    button:disabled { color: #7b878f; cursor: not-allowed; opacity: 0.55; }
  </style>
</head>
<body>
  <main>
    <section class="panel">
      <span class="badge">offline shell</span>
      <h1>手机已断开，需要重新连接</h1>
      <p>当前只能查看离线壳层。重新连接到机器人本地页面后，才能刷新状态或下发控制指令。</p>
      <p>为避免误操作，Start、Confirm Dropoff 和 Cancel 在离线状态保持不可用。</p>
      <p>恢复提示：网络恢复后请刷新状态；若仍显示 stale 或 pending ACK，请打开 Diagnostics 或 Support Handoff。</p>
      <p>ACK 语义：ACK 只代表 command accepted/processing evidence，不代表送达成功。</p>
      <p>边界：software_proof_docker_phone_offline_resume_gate，不证明真实手机、production app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。</p>
      <div class="row">
        <button id="offlineStartButton" disabled>Start Delivery</button>
        <button id="offlineDropoffButton" disabled>Confirm Dropoff</button>
        <button id="offlineCancelButton" disabled>Cancel</button>
        <button id="offlineRefreshButton" onclick="location.reload()">Reconnect</button>
      </div>
    </section>
  </main>
</body>
</html>"""


SERVICE_WORKER_JS = """const CACHE_NAME = 'trashbot-operator-shell-v1';
const SHELL_URLS = ['/', '/index.html', '/offline.html', '/manifest.webmanifest'];
const API_PREFIXES = ['/api/', '/robots/'];

function isDynamicControlRequest(request) {
  const url = new URL(request.url);
  if (request.method !== 'GET') return true;
  if (API_PREFIXES.some(prefix => url.pathname.startsWith(prefix))) return true;
  if (url.pathname.includes('/commands') || url.pathname.endsWith('/ack')) return true;
  return false;
}

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(SHELL_URLS)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (isDynamicControlRequest(event.request)) {
    event.respondWith(fetch(event.request, {cache: 'no-store'}));
    return;
  }
  if (event.request.mode === 'navigate') {
    event.respondWith(fetch(event.request).catch(() => caches.match('/offline.html')));
    return;
  }
  event.respondWith(caches.match(event.request).then(response => response || fetch(event.request)));
});"""

HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#126b5f">
  <meta name="description" content="Trashbot local phone fallback for status, diagnostics, and safe command gates.">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="Trashbot">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <link rel="manifest" href="/manifest.webmanifest">
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
    .message strong { overflow-wrap: anywhere; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
    .row button { flex: 1 1 150px; }
    .steps {
      display: grid;
      gap: 8px;
      grid-template-columns: repeat(6, minmax(0, 1fr));
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
    .step.blocked { border-color: var(--danger); color: var(--danger); font-weight: 750; }
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
      main { gap: 10px; padding: 10px; }
      header { align-items: start; flex-direction: column; }
      h1 { font-size: 20px; }
      .panel { padding: 10px; }
      .readinessMain { align-items: start; flex-direction: column; }
      .readinessMeta { display: none; }
      #phoneReadinessBoundary {
        font-size: 10px;
        max-width: 100%;
        overflow-wrap: anywhere;
        white-space: normal;
      }
      .status { grid-template-columns: 1fr; }
      .steps { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .step { font-size: 11px; min-height: 36px; overflow-wrap: anywhere; }
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
      <p class="message readinessMeta">诊断引用: <strong id="phoneManifestCopy">诊断对象引用缺失。</strong></p>
      <p class="message readinessMeta">诊断建议: <strong id="phoneManifestRetry">请刷新状态。</strong></p>
      <p class="message readinessMeta">Support: <strong id="phoneReadinessSupport">not reported</strong></p>
      <p class="message readinessMeta">Not proven: <strong id="phoneReadinessNotProven">real cloud, 4G, HIL</strong></p>
    </section>
    <section id="offlineResumeReadinessPanel" class="panel">
      <h2>Offline Resume</h2>
      <p class="message">Connection: <strong id="offlineResumeConnection">checking</strong></p>
      <p class="message">Resume: <strong id="offlineResumeCanResume">false</strong></p>
      <p class="message">Next: <strong id="offlineResumeNext">等待状态刷新。</strong></p>
      <p class="message">Recovery: <strong id="offlineResumeHint">恢复连接后刷新状态。</strong></p>
      <p class="message">ACK: <strong id="offlineResumeAck">ACK 只代表 accepted/processing evidence。</strong></p>
      <p class="message">Boundary: <strong id="offlineResumeBoundary">software_proof_docker_phone_offline_resume_gate</strong></p>
      <p class="message">Not proven: <strong id="offlineResumeNotProven">real phone, cloud, HIL</strong></p>
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
    <section id="voicePromptReadinessPanel" class="panel">
      <h2>Voice Prompt Readiness</h2>
      <p class="message">Current prompt: <strong id="voicePromptCurrent">等待提示计算。</strong></p>
      <p class="message">Trigger: <strong id="voicePromptTrigger">not reported</strong></p>
      <p class="message">Human help: <strong id="voicePromptHumanHelp">not reported</strong></p>
      <p class="message">Playback ready: <strong id="voicePromptPlayback">false</strong></p>
      <p class="message">Copy: <strong id="voicePromptSafeCopy">voice prompt readiness 不是实际播放证明。</strong></p>
      <p class="message">Not proven: <strong id="voicePromptNotProven">real speaker, TTS, HIL</strong></p>
    </section>
    <section class="panel">
      <div class="steps" id="journeySteps">
        <div class="step" data-step="connection_ready">1. 连接就绪</div>
        <div class="step" data-step="destination_confirmed">2. 目的地</div>
        <div class="step" data-step="trash_loaded">3. 已放入垃圾</div>
        <div class="step" data-step="start_delivery">4. 一键发车</div>
        <div class="step" data-step="status_explained">5. 状态解释</div>
        <div class="step" data-step="help_or_diagnostics">6. 求助诊断</div>
      </div>
      <p class="message">Task flow: <strong id="taskFlowNext">等待任务步骤计算。</strong></p>
      <p class="message">Block reason: <strong id="taskFlowBlock">none</strong></p>
      <div class="row">
        <button id="collectButton" class="primary" onclick="collect()">Start Delivery</button>
        <button id="dropoffButton" onclick="confirmDropoff()">Confirm Dropoff</button>
        <button id="cancelButton" class="danger" onclick="cancelTask()">Cancel</button>
        <button id="diagnosticsButton" onclick="diagnostics()">Diagnostics</button>
        <button id="supportHandoffButton" onclick="openSupportHandoff()">Support Handoff</button>
      </div>
      <p class="message">Command gate: <strong id="commandSafetyCopy">等待 command safety 计算。</strong></p>
      <p class="message">ACK: <strong id="commandSafetyAck">ACK 只表示指令已被小车侧 bridge 受理或处理。</strong></p>
      <p class="message">Diagnostics: <strong id="diagnosticsGateCopy">Diagnostics 可进入，但不代表主操作可用。</strong></p>
      <p class="message">Support handoff: <strong id="supportHandoffCopy">失败或 blocked 时可复制脱敏摘要。</strong></p>
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
        <div class="metric"><span>Phone task flow</span><strong id="diagPhoneTaskFlow">-</strong></div>
        <div class="metric"><span>Phone next step</span><strong id="diagPhoneTaskFlowNext">-</strong></div>
        <div class="metric"><span>Voice prompt</span><strong id="diagVoicePromptCurrent">-</strong></div>
        <div class="metric"><span>Voice trigger</span><strong id="diagVoicePromptTrigger">-</strong></div>
        <div class="metric"><span>Support bundle</span><strong id="diagSupportBundleId">-</strong></div>
        <div class="metric"><span>Support level</span><strong id="diagSupportLevel">-</strong></div>
      </div>
      <p id="diagRecoveryHint" class="message">No manual takeover required.</p>
      <div id="supportBundlePanel" class="integrityCard">
        <div class="integrityHeader">
          <h3>Support Handoff</h3>
          <span id="supportBundleBadge" class="integrityBadge muted">not loaded</span>
        </div>
        <p id="supportBundleSummary" class="message">失败或 blocked 时，可复制这段中文摘要给家人、售后或工程支持。</p>
        <textarea id="supportBundleSafeCopy" rows="8" readonly></textarea>
        <div class="row">
          <button id="supportCopyButton" onclick="copySupportBundle()">Copy Summary</button>
          <button id="supportRefreshButton" onclick="diagnostics()">Refresh Support</button>
        </div>
        <p class="message">ACK: <strong id="supportBundleAck">ACK 只表示指令被受理或处理，不代表送达成功。</strong></p>
      </div>
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
      <div id="diagOssCdnManifest" class="integrityCard">
        <div class="integrityHeader">
          <h2>Diagnostic object references</h2>
          <span id="diagOssCdnManifestBadge" class="integrityBadge muted">unknown</span>
        </div>
        <p id="diagOssCdnManifestSummary" class="message">Diagnostics have not been loaded yet.</p>
        <p class="message">Next step: <strong id="diagOssCdnManifestNextStep">Refresh status or regenerate references.</strong></p>
        <p class="message">Boundary: <strong id="diagOssCdnManifestBoundary">software proof only</strong></p>
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
    <section id="rawStatusPanel" class="panel" hidden>
      <h2>Support Snapshot</h2>
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
const TASK_FLOW_STEP_ORDER = [
  'connection_ready',
  'destination_confirmed',
  'trash_loaded',
  'start_delivery',
  'status_explained',
  'help_or_diagnostics'
];
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
function renderOssCdnManifest(manifest) {
  const summary = manifest && typeof manifest === 'object' ? manifest : {};
  const state = text(summary.state, 'missing');
  const badge = document.getElementById('diagOssCdnManifestBadge');
  badge.textContent = state;
  badge.className = `integrityBadge ${state === 'ready' ? 'ready' : 'blocked'}`;
  document.getElementById('diagOssCdnManifestSummary').textContent = text(
    summary.safe_summary,
    '诊断对象引用缺失。'
  );
  document.getElementById('diagOssCdnManifestNextStep').textContent = text(
    summary.retry_hint,
    '请刷新状态；如果仍不可用，请重新生成诊断引用。'
  );
  document.getElementById('diagOssCdnManifestBoundary').textContent = text(
    summary.evidence_boundary,
    'software proof only'
  );
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
function taskFlowFromPayload(payload) {
  if (payload.phone_task_flow_readiness && typeof payload.phone_task_flow_readiness === 'object') {
    return payload.phone_task_flow_readiness;
  }
  const readiness = payload.phone_readiness && typeof payload.phone_readiness === 'object'
    ? payload.phone_readiness
    : {};
  return readiness.phone_task_flow_readiness && typeof readiness.phone_task_flow_readiness === 'object'
    ? readiness.phone_task_flow_readiness
    : {};
}
function renderTaskFlow(taskFlow) {
  const flow = taskFlow && typeof taskFlow === 'object' ? taskFlow : {};
  const steps = Array.isArray(flow.steps) ? flow.steps : [];
  const byId = {};
  steps.forEach((step) => {
    if (step && typeof step === 'object') byId[text(step.id, '')] = step;
  });
  document.querySelectorAll('#journeySteps .step').forEach((node) => {
    const step = byId[node.dataset.step] || {};
    const state = text(step.state, 'waiting');
    node.classList.toggle('active', state === 'current');
    node.classList.toggle('done', state === 'done' || state === 'ready');
    node.classList.toggle('blocked', state === 'blocked');
    node.title = text(step.safe_phone_copy, '等待任务步骤更新。');
  });
  document.getElementById('taskFlowNext').textContent = text(
    flow.next_action,
    text(flow.current_step, '等待任务步骤更新。')
  );
  const reasons = Array.isArray(flow.blocking_reasons)
    ? flow.blocking_reasons.map(item => String(item || '').trim()).filter(Boolean)
    : [];
  document.getElementById('taskFlowBlock').textContent = reasons.length ? reasons.join(', ') : 'none';
}
function readinessTone(phoneReadiness) {
  const primaryState = text(phoneReadiness.primary_state, 'waiting_for_robot_status');
  if (primaryState.startsWith('diagnostic_refs_')) return 'blocked';
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
  const manifest = readiness.oss_cdn_manifest && typeof readiness.oss_cdn_manifest === 'object'
    ? readiness.oss_cdn_manifest
    : {};
  document.getElementById('phoneManifestCopy').textContent = text(
    manifest.safe_summary,
    '诊断对象引用缺失。'
  );
  document.getElementById('phoneManifestRetry').textContent = text(
    manifest.retry_hint,
    '请刷新状态。'
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
  const supportBundle = readiness.phone_support_bundle && typeof readiness.phone_support_bundle === 'object'
    ? readiness.phone_support_bundle
    : {};
  renderSupportBundleSummary(supportBundle);
}
function offlineResumeFromPayload(payload) {
  if (payload.phone_offline_resume_readiness && typeof payload.phone_offline_resume_readiness === 'object') {
    return payload.phone_offline_resume_readiness;
  }
  const readiness = payload.phone_readiness && typeof payload.phone_readiness === 'object'
    ? payload.phone_readiness
    : {};
  return readiness.phone_offline_resume_readiness && typeof readiness.phone_offline_resume_readiness === 'object'
    ? readiness.phone_offline_resume_readiness
    : {};
}
function renderOfflineResumeReadiness(offlineResume) {
  const summary = offlineResume && typeof offlineResume === 'object' ? offlineResume : {};
  document.getElementById('offlineResumeConnection').textContent = text(summary.connection_state, 'unknown');
  document.getElementById('offlineResumeCanResume').textContent = String(Boolean(summary.can_resume));
  document.getElementById('offlineResumeNext').textContent = text(
    summary.safe_phone_copy,
    '手机恢复路径仍在等待状态刷新。'
  );
  document.getElementById('offlineResumeHint').textContent = text(
    summary.recovery_hint,
    '恢复连接后刷新状态；如仍被阻断，请打开 Diagnostics。'
  );
  document.getElementById('offlineResumeAck').textContent = text(
    summary.ack_semantics,
    'ACK 只代表 accepted/processing evidence，不代表送达成功。'
  );
  document.getElementById('offlineResumeBoundary').textContent = text(
    summary.evidence_boundary,
    'software_proof_docker_phone_offline_resume_gate'
  );
  const notProven = Array.isArray(summary.not_proven) ? summary.not_proven.slice(0, 6) : [];
  document.getElementById('offlineResumeNotProven').textContent = notProven.length
    ? notProven.join(', ')
    : 'real phone, production app, cloud, HIL';
}
function voicePromptFromPayload(payload) {
  if (payload.voice_prompt_readiness && typeof payload.voice_prompt_readiness === 'object') {
    return payload.voice_prompt_readiness;
  }
  const readiness = payload.phone_readiness && typeof payload.phone_readiness === 'object'
    ? payload.phone_readiness
    : {};
  return readiness.voice_prompt_readiness && typeof readiness.voice_prompt_readiness === 'object'
    ? readiness.voice_prompt_readiness
    : {};
}
function renderVoicePromptReadiness(voicePrompt) {
  const prompt = voicePrompt && typeof voicePrompt === 'object' ? voicePrompt : {};
  document.getElementById('voicePromptCurrent').textContent = text(
    prompt.current_prompt,
    '请查看手机状态，需要时请求人工帮助。'
  );
  document.getElementById('voicePromptTrigger').textContent = text(prompt.trigger_state, 'not reported');
  document.getElementById('voicePromptHumanHelp').textContent = String(Boolean(prompt.requires_human_help));
  document.getElementById('voicePromptPlayback').textContent = String(Boolean(prompt.playback_ready));
  document.getElementById('voicePromptSafeCopy').textContent = text(
    prompt.safe_phone_copy,
    'voice prompt readiness 不是实际播放证明。'
  );
  const notProven = Array.isArray(prompt.not_proven) ? prompt.not_proven.slice(0, 5) : [];
  document.getElementById('voicePromptNotProven').textContent = notProven.length
    ? notProven.join(', ')
    : 'real speaker, TTS, HIL';
}
function commandAction(commandSafety, actionName) {
  const safety = commandSafety && typeof commandSafety === 'object' ? commandSafety : {};
  const actions = safety.actions && typeof safety.actions === 'object' ? safety.actions : {};
  const action = actions[actionName] && typeof actions[actionName] === 'object' ? actions[actionName] : {};
  return action;
}
function applyCommandSafety(payload) {
  const readiness = payload.phone_readiness && typeof payload.phone_readiness === 'object'
    ? payload.phone_readiness
    : {};
  const commandSafety = readiness.command_safety && typeof readiness.command_safety === 'object'
    ? readiness.command_safety
    : {};
  const startAction = commandAction(commandSafety, 'start');
  const dropoffAction = commandAction(commandSafety, 'confirm_dropoff');
  const cancelAction = commandAction(commandSafety, 'cancel');
  const diagnosticsAction = commandAction(commandSafety, 'diagnostics');
  const collectButton = document.getElementById('collectButton');
  const dropoffButton = document.getElementById('dropoffButton');
  const cancelButton = document.getElementById('cancelButton');
  const diagnosticsButton = document.getElementById('diagnosticsButton');
  const supportHandoffButton = document.getElementById('supportHandoffButton');
  // 浏览器按钮只消费后端派生出的 command_safety；raw can_* 只是后端 gate 的输入。
  collectButton.disabled = !Boolean(startAction.enabled);
  dropoffButton.disabled = !Boolean(dropoffAction.enabled);
  cancelButton.disabled = !Boolean(cancelAction.enabled);
  diagnosticsButton.disabled = !Boolean(diagnosticsAction.enabled);
  // support/handoff 只读脱敏摘要；主操作 blocked 时也必须可打开，方便复现问题。
  supportHandoffButton.disabled = false;
  collectButton.title = text(startAction.safe_phone_copy, '当前不能开始任务。');
  dropoffButton.title = text(dropoffAction.safe_phone_copy, '当前不能确认投放。');
  cancelButton.title = text(cancelAction.safe_phone_copy, '当前不能取消任务。');
  diagnosticsButton.title = text(diagnosticsAction.safe_phone_copy, 'Diagnostics 可进入。');
  supportHandoffButton.title = '复制脱敏支持摘要；ACK 不代表送达成功。';
  document.getElementById('commandSafetyCopy').textContent = text(
    commandSafety.safe_phone_copy,
    '主操作暂不可用。'
  );
  document.getElementById('commandSafetyAck').textContent = text(
    commandSafety.ack_semantics,
    'ACK 只表示指令已被受理，不代表送达成功。'
  );
  document.getElementById('diagnosticsGateCopy').textContent = text(
    diagnosticsAction.safe_phone_copy,
    'Diagnostics 可进入，但不代表主操作可用。'
  );
}
function renderSupportBundleSummary(bundle) {
  const supportBundle = bundle && typeof bundle === 'object' ? bundle : {};
  document.getElementById('supportHandoffCopy').textContent = text(
    supportBundle.status_summary || supportBundle.failure_summary,
    '失败或 blocked 时可复制脱敏摘要。'
  );
}
function renderSupportBundle(bundle) {
  const supportBundle = bundle && typeof bundle === 'object' ? bundle : {};
  const badge = document.getElementById('supportBundleBadge');
  badge.textContent = text(supportBundle.support_level, 'not loaded');
  badge.className = `integrityBadge ${supportBundle.support_level ? 'blocked' : 'muted'}`;
  document.getElementById('supportBundleSummary').textContent = text(
    supportBundle.status_summary,
    '失败或 blocked 时，可复制这段中文摘要给家人、售后或工程支持。'
  );
  document.getElementById('supportBundleSafeCopy').value = text(
    supportBundle.safe_copy,
    '支持交接摘要尚未生成；请刷新状态或打开 Diagnostics。'
  );
  document.getElementById('supportBundleAck').textContent = text(
    supportBundle.ack_semantics,
    'ACK 只表示指令被受理或处理，不代表送达成功。'
  );
  document.getElementById('diagSupportBundleId').textContent = text(supportBundle.bundle_id, 'not reported');
  document.getElementById('diagSupportLevel').textContent = text(supportBundle.support_level, 'not reported');
}
async function copySupportBundle() {
  const textArea = document.getElementById('supportBundleSafeCopy');
  const value = text(textArea.value, '支持交接摘要尚未生成；请先刷新 Diagnostics。');
  try {
    await navigator.clipboard.writeText(value);
    document.getElementById('supportBundleSummary').textContent = '已复制脱敏支持摘要；ACK 不代表送达成功。';
  } catch (error) {
    textArea.focus();
    textArea.select();
    document.getElementById('supportBundleSummary').textContent = '无法自动复制，请手动选择摘要文本。';
  }
}
async function openSupportHandoff() {
  const payload = await api('/api/diagnostics', {}, false);
  if (payload) showDiagnostics(payload);
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
  // raw status 只保留给开发者临时排障，默认隐藏，避免手机用户看到 JSON/ROS 内部字段。
  document.getElementById('status').textContent = JSON.stringify(payload, null, 2);
  renderPhoneReadiness(payload.phone_readiness);
  renderOfflineResumeReadiness(offlineResumeFromPayload(payload));
  renderVoicePromptReadiness(voicePromptFromPayload(payload));
  updateJourney(payload);
  renderTaskFlow(taskFlowFromPayload(payload));
  showTelemetry(payload);
  applyCommandSafety(payload);
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
  const ossCdnManifest = payload.oss_cdn_manifest || {};
  const phoneSupportBundle = payload.phone_support_bundle || {};
  const voicePromptReadiness = payload.voice_prompt_readiness || voicePromptFromPayload(latest);
  const offlineResumeReadiness = payload.phone_offline_resume_readiness || offlineResumeFromPayload(latest);
  const phoneTaskFlow = payload.phone_task_flow_readiness && typeof payload.phone_task_flow_readiness === 'object'
    ? payload.phone_task_flow_readiness
    : taskFlowFromPayload(latest);
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
  renderOssCdnManifest(ossCdnManifest);
  renderSupportBundle(phoneSupportBundle);
  renderOfflineResumeReadiness(offlineResumeReadiness);
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
  document.getElementById('diagPhoneTaskFlow').textContent = text(
    phoneTaskFlow.current_step,
    'not reported'
  );
  document.getElementById('diagPhoneTaskFlowNext').textContent = text(
    phoneTaskFlow.next_action,
    'not reported'
  );
  document.getElementById('diagVoicePromptCurrent').textContent = text(
    voicePromptReadiness.current_prompt,
    'not reported'
  );
  document.getElementById('diagVoicePromptTrigger').textContent = text(
    voicePromptReadiness.trigger_state,
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
async function api(path, options, updateStatus = true) {
  try {
    const response = await fetch(path, options || {});
    const payload = await response.json();
    // diagnostics payload 不是任务状态；避免支持入口覆盖首屏 command safety 文案。
    if (updateStatus) showStatus(payload);
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
  const target = text(document.getElementById('target').value, '');
  if (!target) {
    document.getElementById('taskFlowBlock').textContent = 'destination_needs_confirmation';
    document.getElementById('taskFlowNext').textContent = '请先确认目的地。';
    return;
  }
  await api('/api/collect', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({target})
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
  const payload = await api('/api/diagnostics', {}, false);
  if (payload) showDiagnostics(payload);
}
document.getElementById('reviewSampleSelect').addEventListener('change', updateSelectedReviewSummary);
if ('serviceWorker' in navigator) {
  // service worker 只负责静态 shell；API、commands 和 ACK 由脚本内部 network-only bypass。
  navigator.serviceWorker.register('/service-worker.js', {scope: '/'})
    .catch(() => {});
}
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


def _command_safety_block_reason(primary_state, remote_state, manifest_state):
    # command_safety 是浏览器按钮 gate；它比 phone_readiness.can_continue 更严格。
    # 例如本地 fallback 可以继续看状态，但主操作仍要等待新状态，避免 stale/pending 时重复发车。
    if primary_state == "manual_takeover_required":
        return "manual_takeover_required"
    if remote_state in {
        "status_stale",
        "command_pending",
        "auth_failed",
        "cloud_unreachable",
        "malformed_response",
    }:
        return remote_state
    if manifest_state != "ready":
        return {
            "invalid": "diagnostic_refs_invalid",
            "stale": "diagnostic_refs_stale",
        }.get(manifest_state, "diagnostic_refs_missing")
    if primary_state == "monitoring":
        return "monitoring_only"
    return "allowed"


def _command_safety_action(name, permitted, blocking_reason):
    # 每个按钮都同时消费 local permission 和全局安全阻断原因；旧 can_* 字段只作为输入。
    if not permitted:
        reason = "not_permitted_by_local_state"
    elif blocking_reason != "allowed":
        reason = blocking_reason
    else:
        reason = "allowed"
    return {
        "name": name,
        "enabled": bool(reason == "allowed"),
        "reason": reason,
        "safe_phone_copy": COMMAND_SAFETY_BLOCK_COPY.get(reason, COMMAND_SAFETY_BLOCK_COPY["not_permitted_by_local_state"]),
    }


def build_command_safety(permissions, *, primary_state, remote_state, manifest_state):
    """Return the browser command gate consumed by the first-screen buttons.

    这里不判断任务是否真的送达成功；ACK 只是 command accepted/processing 证据。
    local permission、remote readiness 和 manifest summary 都通过后，主操作才会变为可点。
    diagnostics 始终可进入，但会带上阻断解释，方便用户把错误原因交给支持人员复现。
    """
    permissions = permissions if isinstance(permissions, dict) else {}
    blocking_reason = _command_safety_block_reason(primary_state, remote_state, manifest_state)
    actions = {
        "start": _command_safety_action("start", permissions.get("can_collect"), blocking_reason),
        "confirm_dropoff": _command_safety_action(
            "confirm_dropoff",
            permissions.get("can_confirm_dropoff"),
            blocking_reason,
        ),
        "cancel": _command_safety_action("cancel", permissions.get("can_cancel"), blocking_reason),
        "diagnostics": {
            "name": "diagnostics",
            "enabled": True,
            "reason": blocking_reason,
            "safe_phone_copy": (
                "Diagnostics 可进入；请先处理阻断原因。"
                if blocking_reason != "allowed"
                else "Diagnostics 可进入，用于复查当前软件证据。"
            ),
        },
    }
    return {
        "schema": COMMAND_SAFETY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PHONE_COMMAND_SAFETY_EVIDENCE_BOUNDARY,
        "global_block_reason": blocking_reason,
        "safe_phone_copy": COMMAND_SAFETY_BLOCK_COPY.get(blocking_reason, "主操作暂不可用。"),
        "ack_semantics": COMMAND_SAFETY_ACK_COPY,
        "actions": actions,
    }


def _phone_safe_user_text(value, fallback):
    # 用户可见文案走最小清洗，避免状态文件里的工程词被直接带到手机首屏。
    text_value = str(value or "").strip()
    if not text_value:
        return fallback
    lowered = text_value.lower()
    if any(marker in lowered for marker in PHONE_TASK_FLOW_FORBIDDEN_COPY_MARKERS):
        return fallback
    return text_value


def _task_flow_destination(status):
    # 目的地只取业务字段；没有字段时使用本地页面默认垃圾站口径，而不是暴露内部参数名。
    status = status if isinstance(status, dict) else {}
    for key in ("destination", "target", "station", "trash_station", "selected_destination"):
        value = _phone_safe_user_text(status.get(key), "")
        if value:
            return value, "confirmed"
    return "默认垃圾站", "needs_confirmation"


def _task_flow_step(step_id, state, copy, *, blocking_reason="", next_action=""):
    # step 对象只给手机 UI 消费，字段保持普通用户语言和可测状态。
    return {
        "id": step_id,
        "label": PHONE_TASK_FLOW_LABELS[step_id],
        "state": state,
        "safe_phone_copy": copy,
        "blocking_reason": blocking_reason,
        "next_action": next_action,
    }


def build_phone_task_flow_readiness(
    status,
    *,
    primary_state,
    next_action,
    support_level,
    permissions,
    command_safety,
    manifest_state,
):
    """Return task-step metadata for the local phone first screen.

    这个对象不发明机器人能力，只把现有 status、action permission 和 command_safety
    组织成普通用户能理解的任务步骤；真实手机、真实送达和 HIL 仍在 not_proven 中。
    """
    status = status if isinstance(status, dict) else {}
    permissions = permissions if isinstance(permissions, dict) else {}
    command_safety = command_safety if isinstance(command_safety, dict) else {}
    actions = command_safety.get("actions") if isinstance(command_safety.get("actions"), dict) else {}
    state = str(status.get("state") or "unknown").strip() or "unknown"
    destination, destination_state = _task_flow_destination(status)
    blocking_reason = str(command_safety.get("global_block_reason") or "allowed")
    start_enabled = bool((actions.get("start") or {}).get("enabled"))
    diagnostics_enabled = bool((actions.get("diagnostics") or {}).get("enabled", True))
    task_active_states = {
        "delivering",
        "navigating",
        "approaching_elevator",
        "waiting_elevator_open",
        "entering_elevator",
        "requesting_floor_help",
        "waiting_target_floor",
        "exiting_elevator",
        "resume_delivery",
        "arrived_at_station",
        "returning",
        "completed",
        "failed",
        "needs_human_help",
    }
    needs_help = primary_state == "manual_takeover_required" or state in {"failed", "needs_human_help"}

    connection_state = "ready" if primary_state not in {
        "waiting_for_robot_status",
        "login_required",
        "remote_response_invalid",
        "diagnostic_refs_missing",
        "diagnostic_refs_invalid",
        "diagnostic_refs_stale",
    } else "blocked"
    destination_step_state = "ready" if destination_state == "confirmed" else "current"
    load_step_state = "done" if state in task_active_states or bool(permissions.get("can_cancel")) else "current"
    start_step_state = "ready" if start_enabled else ("done" if state in task_active_states else "blocked")
    status_step_state = "current" if state in task_active_states else "waiting"
    if state == "completed":
        status_step_state = "done"
    help_step_state = "current" if needs_help else ("ready" if diagnostics_enabled else "blocked")

    steps = [
        _task_flow_step(
            "connection_ready",
            connection_state,
            "手机已连接到本地控制入口。" if connection_state == "ready" else "手机入口仍有阻塞，请先按提示处理。",
            blocking_reason="" if connection_state == "ready" else primary_state,
            next_action=next_action,
        ),
        _task_flow_step(
            "destination_confirmed",
            destination_step_state,
            f"目的地：{destination}。请在发车前确认无误。",
            blocking_reason="" if destination_step_state == "ready" else "destination_needs_confirmation",
            next_action="confirm_destination",
        ),
        _task_flow_step(
            "trash_loaded",
            load_step_state,
            "请确认垃圾已经放稳，再点击发车。" if load_step_state == "current" else "装载确认已进入任务流程。",
            blocking_reason="" if load_step_state != "blocked" else "load_not_confirmed",
            next_action="confirm_load",
        ),
        _task_flow_step(
            "start_delivery",
            start_step_state,
            (actions.get("start") or {}).get("safe_phone_copy") or "发车按钮受安全 gate 控制。",
            blocking_reason="" if start_step_state in {"ready", "done"} else blocking_reason,
            next_action="start_delivery",
        ),
        _task_flow_step(
            "status_explained",
            status_step_state,
            _phone_safe_user_text(status.get("phone_copy"), "继续观察任务状态。"),
            blocking_reason="manual_takeover_required" if needs_help else "",
            next_action="watch_progress",
        ),
        _task_flow_step(
            "help_or_diagnostics",
            help_step_state,
            (actions.get("diagnostics") or {}).get("safe_phone_copy") or "诊断入口可用于求助和复现问题。",
            blocking_reason="" if diagnostics_enabled else blocking_reason,
            next_action="open_diagnostics",
        ),
    ]

    current_step = next((step["id"] for step in steps if step["state"] in {"current", "blocked"}), steps[-1]["id"])
    blocking_reasons = [
        step["blocking_reason"]
        for step in steps
        if step.get("blocking_reason")
    ]
    return {
        "schema": PHONE_TASK_FLOW_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PHONE_READINESS_EVIDENCE_BOUNDARY,
        "current_step": current_step,
        "next_action": next_action,
        "support_level": support_level,
        "destination": {
            "label": destination,
            "state": destination_state,
            "safe_phone_copy": f"当前目的地是 {destination}。",
        },
        "load_confirmation": {
            "required": True,
            "state": "confirmed" if load_step_state in {"done", "ready"} else "needs_user_confirmation",
            "safe_phone_copy": "本轮不使用自动装载检测；需要用户在手机上确认垃圾已放入。",
        },
        "start_gate": {
            "enabled": start_enabled,
            "reason": (actions.get("start") or {}).get("reason") or blocking_reason,
            "safe_phone_copy": (actions.get("start") or {}).get("safe_phone_copy") or "发车按钮暂不可用。",
        },
        "status_explanation": {
            "state": state,
            "safe_phone_copy": _phone_safe_user_text(status.get("phone_copy"), "继续观察任务状态。"),
            "speaker_prompt": _phone_safe_user_text(status.get("speaker_prompt"), "请查看手机状态。"),
        },
        "help_entry": {
            "diagnostics_enabled": diagnostics_enabled,
            "manual_takeover_required": bool(needs_help),
            "safe_phone_copy": (actions.get("diagnostics") or {}).get("safe_phone_copy") or "诊断入口可用于求助。",
        },
        "steps": steps,
        "blocking_reasons": blocking_reasons,
        "ack_semantics": COMMAND_SAFETY_ACK_COPY,
        "not_proven": list(PHONE_READINESS_NOT_PROVEN),
        "manifest_state": manifest_state,
    }


def _support_safe_text(value, fallback="not_reported"):
    # support bundle 会被复制给家人或售后，所有自由文本先走脱敏过滤。
    text_value = str(value or "").strip()
    if not text_value:
        return fallback
    lowered = text_value.lower()
    if any(marker in lowered for marker in PHONE_SUPPORT_BUNDLE_FORBIDDEN_MARKERS):
        return fallback
    return text_value


def _support_safe_mapping(value):
    # 只保留可解释的短字段；路径、URL、topic、凭证和完整 artifact 一律不进入 handoff。
    if not isinstance(value, dict):
        return {}
    safe = {}
    for key, item in value.items():
        key_text = str(key)
        key_lc = key_text.lower()
        if key_text not in PHONE_SUPPORT_BUNDLE_SAFE_KEYS:
            continue
        if any(marker in key_lc for marker in PHONE_SUPPORT_BUNDLE_FORBIDDEN_MARKERS):
            continue
        if isinstance(item, (str, int, float, bool)) or item is None:
            safe[key_text] = _support_safe_text(item, "")
    return safe


def _support_failure_summary(status, diagnostics):
    # failure 摘要优先读 diagnostics 的 terminal failure，再回退到 status，避免展示 raw task record。
    status = status if isinstance(status, dict) else {}
    diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
    failure = diagnostics.get("failure") if isinstance(diagnostics.get("failure"), dict) else {}
    last_task = diagnostics.get("last_task") if isinstance(diagnostics.get("last_task"), dict) else {}
    for source in (failure, last_task, diagnostics, status):
        code = _support_safe_text(
            source.get("failure_code") or source.get("error_code") or source.get("final_state"),
            "",
        )
        message = _support_safe_text(source.get("message") or source.get("error_message"), "")
        if code or message:
            return " / ".join(part for part in (code, message) if part)
    return "当前没有 terminal failure；请继续观察状态或刷新诊断。"


def _support_refs(status, phone_readiness, diagnostics):
    # 引用只给排障定位，不给本地路径、完整 artifact、checksum 或硬件/串口细节。
    refs = {}
    for source in (status, phone_readiness, diagnostics):
        refs.update(_support_safe_mapping(source))
    task_flow = phone_readiness.get("phone_task_flow_readiness") if isinstance(phone_readiness, dict) else {}
    if isinstance(task_flow, dict):
        refs["current_step"] = _support_safe_text(task_flow.get("current_step"), "")
    command_safety = phone_readiness.get("command_safety") if isinstance(phone_readiness, dict) else {}
    if isinstance(command_safety, dict):
        refs["command_block_reason"] = _support_safe_text(command_safety.get("global_block_reason"), "")
    return {key: value for key, value in refs.items() if value not in ("", None)}


def build_phone_support_bundle(status, phone_readiness=None, diagnostics=None, *, now=None):
    """Build a phone-safe support handoff package.

    这个对象只复用现有 status、phone_readiness 和 diagnostics 摘要；它不读取硬件、
    不下发命令，也不把 ACK、artifact 或本地路径解释成送达成功。
    """
    status = status if isinstance(status, dict) else {}
    phone_readiness = phone_readiness if isinstance(phone_readiness, dict) else {}
    diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
    generated_at = float(now if now is not None else time.time())
    state = _support_safe_text(status.get("state"), "unknown")
    primary_state = _support_safe_text(phone_readiness.get("primary_state"), state)
    support_level = _support_safe_text(phone_readiness.get("support_level"), "support_required")
    failure_summary = _support_failure_summary(status, diagnostics)
    status_summary = _support_safe_text(
        phone_readiness.get("safe_phone_copy") or status.get("phone_copy") or status.get("message"),
        "手机入口正在等待可用状态。",
    )
    next_hint = _support_safe_text(
        phone_readiness.get("recovery_hint") or phone_readiness.get("next_action"),
        "刷新状态；如果仍被阻断，请打开诊断并复制支持交接包。",
    )
    bundle_id = f"support-{int(generated_at)}-{state.replace('_', '-')[:24]}"
    support_refs = _support_refs(status, phone_readiness, diagnostics)
    not_proven = list(PHONE_READINESS_NOT_PROVEN)
    not_proven.extend(
        [
            "delivery_success",
            "ack_as_delivery_success",
            "complete_raw_evidence",
            "hardware_or_serial_details",
        ]
    )
    safe_copy_lines = [
        "Trashbot 支持交接摘要",
        f"状态：{status_summary}",
        f"阻塞/失败：{failure_summary}",
        f"下一步：{next_hint}",
        f"支持等级：{support_level}",
        f"引用：{json.dumps(support_refs, ensure_ascii=False, sort_keys=True)}",
        f"ACK 语义：{COMMAND_SAFETY_ACK_COPY}",
        "未证明：真实手机设备、真实云/4G、Nav2/fixed-route、底盘实机、HIL、送达成功。",
    ]
    safe_copy = "\n".join(_support_safe_text(line, "已过滤敏感内容。") for line in safe_copy_lines)
    return {
        "schema": PHONE_SUPPORT_BUNDLE_SCHEMA,
        "schema_version": 1,
        "api_version": API_VERSION,
        "evidence_boundary": PHONE_SUPPORT_BUNDLE_EVIDENCE_BOUNDARY,
        "bundle_id": bundle_id,
        "generated_at": generated_at,
        "support_level": support_level,
        "status_summary": status_summary,
        "failure_summary": failure_summary,
        "next_steps": {
            "user": next_hint,
            "support": "请按 support_refs 复查软件证据；不要把 ACK 当成送达成功。",
        },
        "ack_semantics": COMMAND_SAFETY_ACK_COPY,
        "support_refs": support_refs,
        "safe_copy": safe_copy,
        "not_proven": not_proven,
        "source": "phone_readiness_and_diagnostics_summary",
    }


def _voice_prompt_safe_text(value, fallback):
    # 提示词可能来自 status 文件或 task record；自由文本进入手机前必须脱敏。
    text_value = str(value or "").strip()
    if not text_value:
        return fallback
    lowered = text_value.lower()
    if any(marker in lowered for marker in VOICE_PROMPT_FORBIDDEN_MARKERS):
        return fallback
    return text_value


def _voice_prompt_trigger(status):
    # 电梯 assist 是跨楼层提示的更精确来源；普通状态只作为回退。
    status = status if isinstance(status, dict) else {}
    elevator_assist = status.get("elevator_assist") if isinstance(status.get("elevator_assist"), dict) else {}
    if elevator_assist.get("enabled"):
        for key in ("phase", "state", "reason"):
            value = str(elevator_assist.get(key) or "").strip()
            if value and value != "active":
                return value
    return str(status.get("state") or "unknown").strip() or "unknown"


def _voice_prompt_requires_help(status, trigger_state):
    # 人工接管判定复用已有状态和 elevator_assist，避免 UI 自己发明机器人语义。
    status = status if isinstance(status, dict) else {}
    elevator_assist = status.get("elevator_assist") if isinstance(status.get("elevator_assist"), dict) else {}
    return bool(
        status.get("human_intervention_required")
        or status.get("requires_human_help")
        or status.get("state") in {"failed", "needs_human_help"}
        or elevator_assist.get("requires_human_help")
        or trigger_state in ELEVATOR_ASSIST_HELP_STATES
    )


def _voice_prompt_support_refs(status, command_safety=None, phone_support_bundle=None):
    # support_refs 只保留短枚举和业务状态，禁止把路径、topic、checksum 或完整 artifact 带给用户。
    status = status if isinstance(status, dict) else {}
    command_safety = command_safety if isinstance(command_safety, dict) else {}
    phone_support_bundle = phone_support_bundle if isinstance(phone_support_bundle, dict) else {}
    refs = {
        "state": _voice_prompt_safe_text(status.get("state"), ""),
        "failure_code": _voice_prompt_safe_text(status.get("failure_code") or status.get("error_code"), ""),
        "command_block_reason": _voice_prompt_safe_text(command_safety.get("global_block_reason"), ""),
        "support_level": _voice_prompt_safe_text(phone_support_bundle.get("support_level"), ""),
    }
    return {key: value for key, value in refs.items() if value}


def build_voice_prompt_readiness(status, phone_readiness=None, phone_support_bundle=None):
    """Build the phone-safe voice prompt readiness summary.

    这个 gate 只证明提示语义可被手机/API 复现；本地 operator 不播放音频，
    所以 playback_ready 固定为 false，不能被上层解读为真实喇叭或 TTS 证明。
    """
    status = status if isinstance(status, dict) else {}
    phone_readiness = phone_readiness if isinstance(phone_readiness, dict) else {}
    phone_support_bundle = phone_support_bundle if isinstance(phone_support_bundle, dict) else {}
    command_safety = phone_readiness.get("command_safety") if isinstance(phone_readiness.get("command_safety"), dict) else {}
    trigger_state = _voice_prompt_trigger(status)
    current_prompt = _voice_prompt_safe_text(
        status.get("speaker_prompt"),
        "请查看手机状态，需要时请求人工帮助。",
    )
    trigger_reason = VOICE_PROMPT_TRIGGER_REASONS.get(
        trigger_state,
        _voice_prompt_safe_text(status.get("phone_copy") or status.get("message"), "当前状态需要查看手机提示。"),
    )
    requires_human_help = _voice_prompt_requires_help(status, trigger_state)
    safe_phone_copy = (
        f"当前应播报：{current_prompt} 触发原因：{trigger_reason} "
        "ACK 只代表指令 accepted/processing evidence，不是送达成功；"
        "voice prompt readiness 不是实际喇叭或 TTS 播放证明。"
    )
    return {
        "schema": VOICE_PROMPT_READINESS_SCHEMA,
        "schema_version": 1,
        "api_version": API_VERSION,
        "evidence_boundary": VOICE_PROMPT_READINESS_EVIDENCE_BOUNDARY,
        "current_prompt": current_prompt,
        "prompt_language": "zh-CN" if any("\u4e00" <= char <= "\u9fff" for char in current_prompt) else "en-US",
        "trigger_state": trigger_state,
        "trigger_reason": trigger_reason,
        "requires_human_help": requires_human_help,
        "playback_ready": False,
        "safe_phone_copy": _voice_prompt_safe_text(safe_phone_copy, "当前提示已过滤；请打开 Diagnostics 请求支持。"),
        "ack_semantics": COMMAND_SAFETY_ACK_COPY + " voice prompt readiness 也不代表提示已真实播放。",
        "support_refs": _voice_prompt_support_refs(status, command_safety, phone_support_bundle),
        "not_proven": [
            "real_speaker_playback",
            "tts_playback",
            "microphone_wake_word",
            "real_phone_device_browser",
            "production_phone_app",
            "real_cloud_4g",
            "oss_cdn_live_traffic",
            "nav2_or_fixed_route_delivery",
            "wave_rover_motion",
            "hil_pass",
            "delivery_success",
        ],
    }


def _offline_resume_safe_text(value, fallback):
    # offline/resume summary 是首屏和离线壳层共同使用的用户文案，必须先过滤敏感工程细节。
    text_value = str(value or "").strip()
    if not text_value:
        return fallback
    lowered = text_value.lower()
    if any(marker in lowered for marker in PHONE_OFFLINE_RESUME_FORBIDDEN_MARKERS):
        return fallback
    return text_value


def _offline_resume_connection_state(primary_state, remote_state, command_safety):
    # connection_state 只描述手机恢复路径，不把本地 mock 或 ACK 状态升级成真实云/4G。
    if remote_state == "cloud_unreachable":
        return "offline"
    if remote_state == "status_stale":
        return "status_stale"
    if remote_state == "command_pending":
        return "pending_ack"
    if primary_state in {"login_required", "remote_response_invalid"}:
        return "blocked"
    if primary_state == "manual_takeover_required":
        return "manual_takeover"
    if str(command_safety.get("global_block_reason") or "") == "allowed":
        return "online"
    return "recovering"


def build_phone_offline_resume_readiness(
    status,
    phone_readiness=None,
    phone_support_bundle=None,
    voice_prompt_readiness=None,
):
    """Build one phone-safe offline/resume gate from existing readiness objects.

    这个 gate 只汇总 offline shell、恢复连接、stale status、pending ACK、command safety、
    support handoff 和 voice/ACK 文案；它不缓存、不伪造、不发送控制请求。
    """
    status = status if isinstance(status, dict) else {}
    phone_readiness = phone_readiness if isinstance(phone_readiness, dict) else {}
    phone_support_bundle = phone_support_bundle if isinstance(phone_support_bundle, dict) else {}
    voice_prompt_readiness = voice_prompt_readiness if isinstance(voice_prompt_readiness, dict) else {}
    command_safety = (
        phone_readiness.get("command_safety")
        if isinstance(phone_readiness.get("command_safety"), dict)
        else {}
    )
    actions = command_safety.get("actions") if isinstance(command_safety.get("actions"), dict) else {}
    remote_readiness = (
        phone_readiness.get("remote_readiness")
        if isinstance(phone_readiness.get("remote_readiness"), dict)
        else {}
    )
    primary_state = str(phone_readiness.get("primary_state") or "waiting_for_robot_status")
    remote_state = _remote_degradation(remote_readiness)
    connection_state = _offline_resume_connection_state(primary_state, remote_state, command_safety)
    primary_actions_enabled = any(
        bool((actions.get(name) or {}).get("enabled"))
        for name in ("start", "confirm_dropoff", "cancel")
    )
    support_entry_enabled = bool(
        (actions.get("diagnostics") or {}).get("enabled", True)
        or phone_support_bundle.get("schema") == PHONE_SUPPORT_BUNDLE_SCHEMA
    )
    next_action = str(phone_readiness.get("next_action") or "wait_reconnect")
    can_resume = bool(
        connection_state == "online"
        and primary_actions_enabled
        and str(command_safety.get("global_block_reason") or "allowed") == "allowed"
    )
    if connection_state == "offline":
        next_action = "wait_reconnect"
        recovery_hint = "恢复网络后刷新状态；在状态更新前不要发车、确认投放或取消。"
        safe_phone_copy = "手机当前离线，只能查看离线壳层，主操作保持不可用。"
    elif connection_state == "status_stale":
        recovery_hint = "等待小车上报最新状态；如持续 stale，请打开 Diagnostics 或 Support Handoff。"
        safe_phone_copy = "状态已过期，Start/Confirm/Cancel 继续由 command safety 阻断。"
    elif connection_state == "pending_ack":
        recovery_hint = "等待上一条指令 ACK；不要重复发车，必要时复制支持交接摘要。"
        safe_phone_copy = "指令正在等待 ACK，主操作暂不可用。"
    elif connection_state == "manual_takeover":
        recovery_hint = "保持现场安全，按手机提示人工接管，并打开 Support Handoff。"
        safe_phone_copy = "当前需要人工接管，不能通过离线恢复直接继续任务。"
    elif can_resume:
        recovery_hint = _offline_resume_safe_text(
            phone_readiness.get("recovery_hint"),
            "连接已恢复；仍需按当前按钮状态继续。",
        )
        safe_phone_copy = "连接和 command safety 允许继续当前本地手机流程。"
    else:
        recovery_hint = _offline_resume_safe_text(
            phone_readiness.get("recovery_hint") or (actions.get("diagnostics") or {}).get("safe_phone_copy"),
            "恢复连接后刷新状态；如仍被阻断，请打开 Diagnostics。",
        )
        safe_phone_copy = _offline_resume_safe_text(
            phone_readiness.get("safe_phone_copy"),
            "手机恢复路径仍被阻断，主操作保持不可用。",
        )

    support_copy = _offline_resume_safe_text(
        phone_support_bundle.get("status_summary") or phone_support_bundle.get("failure_summary"),
        "Support Handoff 可复制脱敏摘要。",
    )
    voice_copy = _offline_resume_safe_text(
        voice_prompt_readiness.get("safe_phone_copy"),
        "voice prompt readiness 只是提示 contract，不证明真实播放。",
    )
    return {
        "schema": PHONE_OFFLINE_RESUME_READINESS_SCHEMA,
        "schema_version": 1,
        "api_version": API_VERSION,
        "evidence_boundary": PHONE_OFFLINE_RESUME_READINESS_EVIDENCE_BOUNDARY,
        "connection_state": connection_state,
        "can_resume": bool(can_resume),
        "primary_actions_enabled": bool(primary_actions_enabled),
        "support_entry_enabled": bool(support_entry_enabled),
        "next_action": next_action,
        "safe_phone_copy": _offline_resume_safe_text(safe_phone_copy, "手机恢复路径仍在等待状态刷新。"),
        "recovery_hint": _offline_resume_safe_text(recovery_hint, "恢复连接后刷新状态；如仍被阻断，请打开 Diagnostics。"),
        "ack_semantics": _offline_resume_safe_text(command_safety.get("ack_semantics"), COMMAND_SAFETY_ACK_COPY),
        "support_handoff": {
            "enabled": bool(support_entry_enabled),
            "safe_phone_copy": support_copy,
        },
        "voice_prompt": {
            "playback_ready": bool(voice_prompt_readiness.get("playback_ready")),
            "safe_phone_copy": voice_copy,
        },
        "command_safety": {
            "schema": COMMAND_SAFETY_SCHEMA,
            "global_block_reason": str(command_safety.get("global_block_reason") or "allowed"),
            "primary_actions_enabled": bool(primary_actions_enabled),
            "diagnostics_enabled": bool((actions.get("diagnostics") or {}).get("enabled", True)),
        },
        "offline_shell": {
            "primary_actions_disabled": True,
            "control_request_cache": "disabled",
            "safe_phone_copy": "离线壳层不缓存、不伪造、不发送 Start/Confirm/Cancel 控制请求。",
        },
        "not_proven": [
            "real_phone_device_browser",
            "production_phone_app",
            "real_cloud_https_tls_public_ingress",
            "real_4g_sim_carrier_network",
            "oss_cdn_live_traffic",
            "nav2_or_fixed_route_delivery",
            "wave_rover_motion",
            "hil_pass",
            "delivery_success",
        ],
    }


def build_phone_readiness(
    status,
    *,
    remote_readiness=None,
    cloud_preflight=None,
    backup_restore=None,
    oss_cdn_manifest=None,
    network_recovery=None,
    credential_rotation=None,
    provisioning_audit=None,
    production_store_queue=None,
    queue_ordering_drill=None,
    transaction_isolation=None,
    production_recovery=None,
):
    """Build the phone-first readiness summary used by `/api/status`.

    这个 helper 不创造机器人状态；它只把 local status、action permission、
    remote_readiness 和可选上线前 gate 归类成手机能直接显示的恢复路径。
    """
    status = status if isinstance(status, dict) else {}
    remote = remote_readiness if isinstance(remote_readiness, dict) else {}
    # manifest gate 是诊断引用是否能被手机消费的独立约束；它不创造机器人状态。
    manifest_gate = (
        dict(oss_cdn_manifest)
        if isinstance(oss_cdn_manifest, dict)
        else build_phone_oss_cdn_manifest_summary("")
    )
    # network recovery 是远程弱网恢复的软件证明摘要；它不直接创造本地任务权限。
    recovery_gate = (
        dict(network_recovery)
        if isinstance(network_recovery, dict)
        else build_phone_network_recovery_summary("")
    )
    # credential rotation 是 O6 上线前凭证边界摘要；它不改变机器人运动状态或本地任务权限。
    credential_gate = (
        dict(credential_rotation)
        if isinstance(credential_rotation, dict)
        else build_phone_credential_rotation_summary("")
    )
    # provisioning audit 是生产账号发放、STS 边界和审计日志的摘要，不改变运动权限。
    provisioning_gate = (
        dict(provisioning_audit)
        if isinstance(provisioning_audit, dict)
        else build_phone_provisioning_audit_summary("")
    )
    # production store/queue 是 O6 生产持久化/队列边界摘要，不改变运动权限。
    store_queue_gate = (
        dict(production_store_queue)
        if isinstance(production_store_queue, dict)
        else build_phone_production_store_queue_summary("")
    )
    # queue ordering drill 是 O6 软件证明摘要；不能改变本地机器人状态或动作权限。
    queue_ordering_gate = (
        dict(queue_ordering_drill)
        if isinstance(queue_ordering_drill, dict)
        else build_phone_queue_ordering_drill_summary("")
    )
    # transaction isolation 是 O6 并发/ACK cursor 摘要；不能把本地 proof 提升成本地动作权限。
    transaction_isolation_gate = (
        dict(transaction_isolation)
        if isinstance(transaction_isolation, dict)
        else build_phone_transaction_isolation_summary("")
    )
    # production recovery 是 O6 上线前灾备缺口摘要；本地 artifact 不能改变任何动作权限。
    production_recovery_gate = (
        dict(production_recovery)
        if isinstance(production_recovery, dict)
        else build_phone_production_recovery_summary("")
    )
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

    manifest_state = str(manifest_gate.get("state") or "missing").strip() or "missing"
    if manifest_state != "ready":
        # 诊断引用不可消费时，首屏不能显示 green；用户需要先刷新或重建诊断引用。
        primary_state = {
            "invalid": "diagnostic_refs_invalid",
            "stale": "diagnostic_refs_stale",
        }.get(manifest_state, "diagnostic_refs_missing")
        next_action = "refresh_diagnostics_ref"
        can_continue = False
        support_level = "diagnostic_refs_blocked"
        safe_phone_copy = str(
            manifest_gate.get("safe_summary")
            or PHONE_READINESS_PRIMARY_COPY[primary_state]
        )
        recovery_hint = str(
            manifest_gate.get("retry_hint")
            or PHONE_READINESS_NEXT_ACTION_COPY[next_action]
        )

    command_safety = build_command_safety(
        permissions,
        primary_state=primary_state,
        remote_state=remote_state,
        manifest_state=manifest_state,
    )
    phone_task_flow_readiness = build_phone_task_flow_readiness(
        status,
        primary_state=primary_state,
        next_action=next_action,
        support_level=support_level,
        permissions=permissions,
        command_safety=command_safety,
        manifest_state=manifest_state,
    )

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
        "phone_task_flow_readiness": phone_task_flow_readiness,
        "action_permissions": permissions,
        "command_safety": command_safety,
        "remote_readiness": dict(remote),
        "cloud_preflight": _copy_gate(cloud_preflight, "cloud_preflight"),
        "backup_restore": _copy_gate(backup_restore, "backup_restore"),
        "oss_cdn_manifest": dict(manifest_gate),
        "network_recovery": dict(recovery_gate),
        "credential_rotation": dict(credential_gate),
        "provisioning_audit": dict(provisioning_gate),
        "production_store_queue": dict(store_queue_gate),
        "queue_ordering_drill": dict(queue_ordering_gate),
        "transaction_isolation": dict(transaction_isolation_gate),
        "production_recovery": dict(production_recovery_gate),
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
    # status 与 diagnostics 共用同一个 helper；只输出摘要，不把 manifest artifact 原文透给手机。
    oss_cdn_manifest = build_phone_oss_cdn_manifest_summary(
        getattr(gateway, "oss_cdn_manifest_artifact_ref", "")
    )
    network_recovery = build_phone_network_recovery_summary(
        getattr(gateway, "network_recovery_artifact_ref", "")
        or os.environ.get("TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT", "")
    )
    credential_rotation = build_phone_credential_rotation_summary(
        getattr(gateway, "credential_rotation_artifact_ref", "")
        or os.environ.get("TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT", "")
    )
    provisioning_audit = build_phone_provisioning_audit_summary(
        getattr(gateway, "provisioning_audit_artifact_ref", "")
        or os.environ.get("TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT", "")
    )
    production_store_queue = build_phone_production_store_queue_summary(
        getattr(gateway, "production_store_queue_artifact_ref", "")
        or os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT", "")
    )
    queue_ordering_drill = build_phone_queue_ordering_drill_summary(
        getattr(gateway, "queue_ordering_drill_artifact_ref", "")
        or os.environ.get("TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT", "")
    )
    transaction_isolation = build_phone_transaction_isolation_summary(
        getattr(gateway, "transaction_isolation_artifact_ref", "")
        or os.environ.get("TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT", "")
    )
    production_recovery = build_phone_production_recovery_summary(
        getattr(gateway, "production_recovery_artifact_ref", "")
        or os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT", "")
    )
    # 可选 gate 字段只在调用方已提供时采纳；默认 not_run/unknown，不推断生产 readiness。
    payload["phone_readiness"] = build_phone_readiness(
        payload,
        remote_readiness=remote_readiness,
        cloud_preflight=payload.get("cloud_preflight") or payload.get("remote_preflight"),
        backup_restore=payload.get("backup_restore") or payload.get("backup_restore_drill"),
        oss_cdn_manifest=oss_cdn_manifest,
        network_recovery=network_recovery,
        credential_rotation=credential_rotation,
        provisioning_audit=provisioning_audit,
        production_store_queue=production_store_queue,
        queue_ordering_drill=queue_ordering_drill,
        transaction_isolation=transaction_isolation,
        production_recovery=production_recovery,
    )
    phone_support_bundle = build_phone_support_bundle(payload, payload["phone_readiness"])
    voice_prompt_readiness = build_voice_prompt_readiness(
        payload,
        payload["phone_readiness"],
        phone_support_bundle,
    )
    payload["phone_support_bundle"] = phone_support_bundle
    payload["phone_readiness"]["phone_support_bundle"] = dict(phone_support_bundle)
    payload["voice_prompt_readiness"] = voice_prompt_readiness
    payload["phone_readiness"]["voice_prompt_readiness"] = dict(voice_prompt_readiness)
    offline_resume_readiness = build_phone_offline_resume_readiness(
        payload,
        payload["phone_readiness"],
        phone_support_bundle,
        voice_prompt_readiness,
    )
    payload["phone_offline_resume_readiness"] = offline_resume_readiness
    payload["phone_readiness"]["phone_offline_resume_readiness"] = dict(offline_resume_readiness)
    payload["phone_task_flow_readiness"] = dict(payload["phone_readiness"]["phone_task_flow_readiness"])
    return payload


def _diagnostics_with_phone_task_flow(gateway, mock_cloud):
    # diagnostics 是支持入口；补同一份 task-flow 和 handoff 摘要，便于复现首屏阻塞但不改变任务状态。
    diagnostics_payload = dict(gateway.diagnostics())
    status = _status_with_phone_readiness(gateway, mock_cloud)
    task_flow = dict(status.get("phone_task_flow_readiness", {}))
    phone_readiness = status.get("phone_readiness") if isinstance(status.get("phone_readiness"), dict) else {}
    phone_support_bundle = build_phone_support_bundle(status, phone_readiness, diagnostics_payload)
    voice_prompt_readiness = build_voice_prompt_readiness(status, phone_readiness, phone_support_bundle)
    offline_resume_readiness = build_phone_offline_resume_readiness(
        status,
        phone_readiness,
        phone_support_bundle,
        voice_prompt_readiness,
    )
    diagnostics_payload["phone_task_flow_readiness"] = task_flow
    diagnostics_payload["phone_support_bundle"] = phone_support_bundle
    diagnostics_payload["voice_prompt_readiness"] = voice_prompt_readiness
    diagnostics_payload["phone_offline_resume_readiness"] = offline_resume_readiness
    # HTTP diagnostics 复用 status 里的同一份摘要，避免 status/diagnostics 对 transaction gate 给出两套口径。
    if isinstance(phone_readiness.get("transaction_isolation"), dict):
        diagnostics_payload["transaction_isolation"] = dict(phone_readiness["transaction_isolation"])
    if isinstance(phone_readiness.get("production_recovery"), dict):
        diagnostics_payload["production_recovery"] = dict(phone_readiness["production_recovery"])
    latest_status = diagnostics_payload.get("latest_status")
    if isinstance(latest_status, dict):
        # diagnostics 不能信任 status 文件内预置的 phone metadata；这里统一覆盖成现算的脱敏摘要。
        latest_status["phone_task_flow_readiness"] = task_flow
        latest_status["phone_support_bundle"] = phone_support_bundle
        latest_status["voice_prompt_readiness"] = voice_prompt_readiness
        latest_status["phone_offline_resume_readiness"] = offline_resume_readiness
    return diagnostics_payload


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

        def _send_text(self, status, body, content_type):
            data = str(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
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
                self._send_text(200, HTML, "text/html; charset=utf-8")
                return
            if path == "/offline.html":
                self._send_text(200, OFFLINE_HTML, "text/html; charset=utf-8")
                return
            if path == "/service-worker.js":
                self._send_text(200, SERVICE_WORKER_JS, "application/javascript; charset=utf-8")
                return
            if path == "/manifest.webmanifest":
                self._send_json(200, build_pwa_manifest())
                return
            if path in {"/pwa-icon-192x192.svg", "/pwa-icon-512x512.svg"}:
                icon_size = path.removeprefix("/pwa-icon-").removesuffix(".svg")
                self._send_text(200, build_pwa_icon(icon_size), "image/svg+xml; charset=utf-8")
                return
            if path == "/api/status":
                self._send_json(200, _status_with_phone_readiness(gateway, mock_cloud))
                return
            if path == "/api/diagnostics":
                self._send_json(200, _diagnostics_with_phone_task_flow(gateway, mock_cloud))
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
