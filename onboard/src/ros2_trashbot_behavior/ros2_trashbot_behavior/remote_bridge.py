import json
import os
import time
from pathlib import Path

try:
    import rclpy
    from rclpy.action import ActionClient
    from rclpy.executors import MultiThreadedExecutor
    from rclpy.node import Node
    from std_srvs.srv import SetBool
    from ros2_trashbot_interfaces.action import TrashCollection
except ModuleNotFoundError:
    rclpy = None
    ActionClient = None
    MultiThreadedExecutor = None
    Node = object
    SetBool = None
    TrashCollection = None

from ros2_trashbot_behavior.remote_bridge_protocol import (
    InvalidRemoteCommand,
    RemoteCloudError,
    RemoteCloudClient,
    command_expired,
    make_status,
    parse_bool,
)

if "threading" not in globals():
    import threading


CURSOR_PROTOCOL_VERSION = "trashbot.remote.cursor.v1"
CLOUD_ACK_OUTAGE_REPLAY_GUARD_BOUNDARY = "software_proof_docker_cloud_ack_outage_replay_guard"
CLOUD_PENDING_ACK_STATUS_GUARD_BOUNDARY = "software_proof_docker_cloud_pending_ack_status_guard"
CLOUD_COMMAND_EXPIRY_SAFETY_GUARD_BOUNDARY = "software_proof_docker_cloud_command_expiry_safety_guard"
CLOUD_COMMAND_IDEMPOTENCY_VISIBILITY_GUARD_BOUNDARY = (
    "software_proof_docker_cloud_command_idempotency_visibility_guard"
)
CLOUD_COMMAND_ID_CONFLICT_VISIBILITY_GUARD_BOUNDARY = (
    "software_proof_docker_cloud_command_id_conflict_visibility_guard"
)
PENDING_TERMINAL_ACK_KEY = "pending_terminal_ack"
SAFE_OPERATOR_STATUS_KEYS = {
    "protocol_version",
    "robot_id",
    "state",
    "message",
    "updated_at",
    "remote_ready",
    "cloud_reachable",
    "auth_state",
    "degradation_state",
    "retry_hint",
    "safe_phone_copy",
    "pending_terminal_ack_id",
    "expired_command_id",
    "duplicate_command_id",
    "conflict_command_id",
    "conflict_reason",
    "conflict_fields",
    "cached_ack_state",
    "ack_semantics",
    "primary_actions_enabled",
    "proof_boundary",
    "accepted",
    "service_accepted",
    "error_code",
    "final_state",
}
SENSITIVE_STATE_MARKERS = (
    "authorization",
    "bearer",
    "/cmd_vel",
    "wave rover",
    "serial",
    "baudrate",
    "traceback",
    "delivery_success=true",
)


def _snapshot_status(robot_id, snapshot):
    snapshot = dict(snapshot or {})
    state = snapshot.pop("state", "unknown")
    message = snapshot.pop("message", "")
    snapshot.pop("protocol_version", None)
    snapshot.pop("robot_id", None)
    snapshot.pop("updated_at", None)
    return make_status(robot_id, state, message, **snapshot)


def _phone_safe_degraded_status(robot_id, error):
    reason = getattr(error, "reason", "cloud_unreachable")
    retry_hint = getattr(error, "retry_hint", "retry_cloud")
    cloud_reachable = bool(getattr(error, "cloud_reachable", False))
    if reason == "auth_failed":
        auth_state = "auth_failed"
        safe_phone_copy = "远程鉴权失败，请检查登录或机器人云端授权。"
    elif reason == "malformed_response":
        auth_state = "unknown"
        safe_phone_copy = "远程服务响应异常，请稍后重试或联系支持。"
        cloud_reachable = True
    else:
        reason = "cloud_unreachable"
        auth_state = "unknown"
        safe_phone_copy = "远程服务暂时不可达，机器人会保留当前任务游标。"
    return make_status(
        robot_id,
        "remote_degraded",
        safe_phone_copy,
        remote_ready=False,
        cloud_reachable=cloud_reachable,
        auth_state=auth_state,
        degradation_state=reason,
        retry_hint=retry_hint,
        safe_phone_copy=safe_phone_copy,
    )


def _safe_state_text_value(value):
    text = str(value)
    lowered = text.lower()
    if any(marker in lowered for marker in SENSITIVE_STATE_MARKERS):
        return "[redacted]"
    return text[:240]


def _phone_safe_pending_ack_status(robot_id, command_id, error):
    safe_command_id = _safe_state_text_value(command_id)
    retry_hint = getattr(error, "retry_hint", "retry_cloud")
    safe_phone_copy = "本地命令已完成终态，但云端 ACK 还没确认，暂不能拉取新命令。"
    auth_state = "auth_failed" if getattr(error, "reason", "") == "auth_failed" else "unknown"
    return make_status(
        robot_id,
        "remote_degraded",
        safe_phone_copy,
        remote_ready=False,
        cloud_reachable=bool(getattr(error, "cloud_reachable", False)),
        auth_state=auth_state,
        degradation_state="command_pending",
        retry_hint=retry_hint,
        safe_phone_copy=safe_phone_copy,
        pending_terminal_ack_id=safe_command_id,
        primary_actions_enabled=False,
        proof_boundary=CLOUD_PENDING_ACK_STATUS_GUARD_BOUNDARY,
    )


def _phone_safe_expired_command_status(robot_id, command_id):
    safe_command_id = _safe_state_text_value(command_id)
    safe_phone_copy = "这条云端指令已经过期，机器人没有执行；请重新提交最新指令。"
    return make_status(
        robot_id,
        "remote_degraded",
        safe_phone_copy,
        remote_ready=False,
        cloud_reachable=True,
        auth_state="unknown",
        degradation_state="command_expired",
        retry_hint="resubmit_command",
        safe_phone_copy=safe_phone_copy,
        expired_command_id=safe_command_id,
        primary_actions_enabled=False,
        proof_boundary=CLOUD_COMMAND_EXPIRY_SAFETY_GUARD_BOUNDARY,
    )


def _phone_safe_duplicate_command_status(robot_id, command_id, ack_state):
    safe_command_id = _safe_state_text_value(command_id)
    safe_ack_state = str(ack_state or "unknown").strip() or "unknown"
    safe_phone_copy = "重复云指令已去重，机器人没有重复执行；cached ACK 不是送达成功。"
    return make_status(
        robot_id,
        "remote_degraded",
        safe_phone_copy,
        remote_ready=False,
        cloud_reachable=True,
        auth_state="unknown",
        degradation_state="command_duplicate_deduped",
        retry_hint="refresh_status",
        safe_phone_copy=safe_phone_copy,
        duplicate_command_id=safe_command_id,
        cached_ack_state=safe_ack_state,
        ack_semantics="duplicate_cached_ack_not_delivery_success",
        primary_actions_enabled=False,
        proof_boundary=CLOUD_COMMAND_IDEMPOTENCY_VISIBILITY_GUARD_BOUNDARY,
    )


def _phone_safe_command_conflict_status(robot_id, command_id, conflict_fields):
    safe_command_id = _safe_state_text_value(command_id)
    safe_fields = _safe_state_text_value(",".join(conflict_fields) or "type,payload")
    safe_phone_copy = "命令 ID 冲突：同一 ID 的 type/payload 不一致，机器人已拒绝执行；这不是送达成功。"
    return make_status(
        robot_id,
        "remote_degraded",
        safe_phone_copy,
        remote_ready=False,
        cloud_reachable=True,
        auth_state="unknown",
        degradation_state="command_id_conflict",
        retry_hint="contact_support",
        safe_phone_copy=safe_phone_copy,
        conflict_command_id=safe_command_id,
        conflict_reason="duplicate_id_mismatched_type_or_payload",
        conflict_fields=safe_fields,
        ack_semantics="conflict_rejected_not_delivery_success",
        primary_actions_enabled=False,
        proof_boundary=CLOUD_COMMAND_ID_CONFLICT_VISIBILITY_GUARD_BOUNDARY,
    )


def _canonical_command_identity(command):
    # canonical identity 只比较业务执行内容，不把 expires_at/created_at 等队列元数据纳入幂等判断。
    payload = command.get("payload") if isinstance(command.get("payload"), dict) else {}
    canonical_payload = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "type": str(command.get("type") or "").strip(),
        "payload": canonical_payload,
    }


def _command_identity_conflict_fields(previous_identity, current_identity):
    # 字段级差异用于手机端解释原因；不回显 raw payload，避免泄漏 JSON 细节或控制参数。
    fields = []
    for key in ("type", "payload"):
        if previous_identity.get(key) != current_identity.get(key):
            fields.append(key)
    return fields


class RemoteBridgeWorker:
    """Pure-Python HTTP polling worker for the outbound 4G bridge.

    The worker accepts only the behavior-level remote contract. It never exposes
    raw ROS topics such as /cmd_vel and never maps a cloud payload directly to
    wheel or base velocity commands.
    """

    def __init__(
        self,
        cloud_client,
        operator_backend,
        robot_id,
        max_command_results=200,
        last_ack_id="",
        cursor_state_path="",
    ):
        self.cloud = cloud_client
        self.operator_backend = operator_backend
        self.robot_id = robot_id
        self.cursor_state_path = str(cursor_state_path or "").strip()
        cursor_state = self._load_cursor_state(str(last_ack_id or ""))
        self.last_ack_id = cursor_state["last_terminal_ack_id"]
        self.pending_terminal_ack = cursor_state[PENDING_TERMINAL_ACK_KEY]
        self.command_results = {}
        self.command_identities = {}
        self.max_command_results = int(max_command_results)

    def poll_once(self):
        status = _snapshot_status(self.robot_id, self.operator_backend.snapshot())
        try:
            self.cloud.post_status(status)
        except RemoteCloudError as exc:
            # status 都提交不上时，本轮不能安全拉取新命令；保持游标不动，等下次轮询重试。
            if self.pending_terminal_ack:
                # 已有本地终态 ACK 时，手机侧必须看到 command_pending，而不是误以为可继续下发。
                self._record_pending_ack_degraded_status(self._pending_terminal_ack_id(), exc)
            else:
                self._record_degraded_status(exc)
            return False
        if self.pending_terminal_ack:
            # pending ACK 是已经执行过的本地终态；先补发它，才能避免重启后重复执行命令。
            return self._replay_pending_terminal_ack()
        try:
            command = self.cloud.get_next_command(self.last_ack_id)
        except RemoteCloudError as exc:
            # 云端响应不可信或鉴权失败时，不解析 payload、不提交本地 action、不推进 cursor。
            self._record_degraded_status(exc)
            self._post_degraded_status_best_effort(exc)
            return False
        except InvalidRemoteCommand as exc:
            command = exc.command if isinstance(exc.command, dict) else {}
            command_id = str(command.get("id") or "").strip()
            if not command_id:
                raise
            ack = self._make_ack("failed", f"malformed command: {exc}", status)
            self._post_terminal_ack(command_id, ack)
            return True
        if command is None:
            return False
        if command_expired(command):
            # 过期命令不能只回 ACK；手机首屏也必须看到 fail-closed 原因，避免用户误以为可继续发车。
            expired_status = self._record_expired_command_status(command["id"])
            ack = self._make_ack("ignored", "command expired before robot polling", expired_status)
            self._post_terminal_ack(command["id"], ack)
            return True
        if command["id"] in self.command_results:
            previous_identity = self.command_identities.get(command["id"], {})
            current_identity = _canonical_command_identity(command)
            conflict_fields = _command_identity_conflict_fields(previous_identity, current_identity)
            if conflict_fields:
                # 同 id 不同内容不能复用 cached ACK；这里直接拒绝执行并用独立 ACK 暴露冲突原因。
                conflict_status = self._record_command_conflict_status(command["id"], conflict_fields)
                conflict_ack = self._make_ack(
                    "ignored",
                    "command id conflict rejected before robot execution",
                    conflict_status,
                )
                self._post_terminal_ack(command["id"], conflict_ack, remember=False)
                return True
            # duplicate 只复用已有 terminal ACK envelope，不再提交本地 action；同时把“去重不是送达”
            # 写进 operator_status，避免手机端只看到 acked 就误判 delivery success。
            cached_ack = dict(self.command_results[command["id"]])
            duplicate_status = self._record_duplicate_command_status(
                command["id"],
                cached_ack.get("state"),
            )
            duplicate_ack = self._ack_with_operator_status(cached_ack, duplicate_status)
            self._post_terminal_ack(command["id"], duplicate_ack, remember=False)
            return True

        try:
            http_status, payload = self._execute_command(command)
            if command["type"] == "collect" and int(http_status) == 409:
                ack_state = "ignored"
            else:
                ack_state = "acked" if 200 <= int(http_status) < 300 else "failed"
            message = str((payload or {}).get("message") or command["type"])
            result = {
                "http_status": int(http_status),
                "operator_status": payload or {},
            }
            ack = {
                "state": ack_state,
                "message": message,
                "result": result,
            }
        except Exception as exc:  # noqa: BLE001 - command failures must reach the cloud.
            result = {"operator_status": status}
            ack = {
                "state": "failed",
                "message": f"command failed: {exc}",
                "result": result,
            }
        self.command_identities[command["id"]] = _canonical_command_identity(command)
        self._post_terminal_ack(command["id"], ack)
        return True

    def _make_ack(self, state, message, operator_status):
        return {
            "state": state,
            "message": message,
            "result": {"operator_status": operator_status},
        }

    def _post_terminal_ack(self, command_id, ack, remember=True):
        if remember:
            self._remember_command_result(command_id, ack)
        try:
            self.cloud.post_ack(command_id, ack["state"], ack["message"], ack["result"])
        except RemoteCloudError as exc:
            # ACK 未进入云端就不是 terminal ACK；先持久化 pending ACK，再暴露降级状态。
            self._persist_pending_terminal_ack(command_id, ack)
            status = self._record_pending_ack_degraded_status(command_id, exc)
            self._post_status_best_effort(status)
            return False
        self.last_ack_id = command_id
        self._persist_last_ack_id(command_id)
        self._post_status_from_ack(ack)
        return True

    def _replay_pending_terminal_ack(self):
        pending_ack = dict(self.pending_terminal_ack or {})
        command_id = str(pending_ack.get("command_id") or "").strip()
        ack = dict(pending_ack.get("ack") or {})
        if not command_id or ack.get("state") not in {"acked", "failed", "ignored"}:
            raise RuntimeError("remote bridge pending ACK state is malformed")
        try:
            self.cloud.post_ack(
                command_id,
                ack["state"],
                str(ack.get("message") or ""),
                ack.get("result") if isinstance(ack.get("result"), dict) else {},
            )
        except RemoteCloudError as exc:
            # 补发失败仍保持 pending ACK，不拉取新命令，避免本地行为被重复触发。
            status = self._record_pending_ack_degraded_status(command_id, exc)
            self._post_status_best_effort(status)
            return False
        self.last_ack_id = command_id
        self.pending_terminal_ack = None
        self._persist_last_ack_id(command_id)
        self._post_status_from_ack(ack)
        return True

    def _pending_terminal_ack_id(self):
        pending_ack = dict(self.pending_terminal_ack or {})
        return str(pending_ack.get("command_id") or "").strip()

    def _record_degraded_status(self, error):
        status = _phone_safe_degraded_status(self.robot_id, error)
        self._set_operator_status(status)
        return status

    def _record_pending_ack_degraded_status(self, command_id, error):
        status = _phone_safe_pending_ack_status(self.robot_id, command_id, error)
        self._set_operator_status(status)
        return status

    def _record_expired_command_status(self, command_id):
        status = _phone_safe_expired_command_status(self.robot_id, command_id)
        self._set_operator_status(status)
        return status

    def _record_duplicate_command_status(self, command_id, ack_state):
        status = _phone_safe_duplicate_command_status(self.robot_id, command_id, ack_state)
        self._set_operator_status(status)
        return status

    def _record_command_conflict_status(self, command_id, conflict_fields):
        status = _phone_safe_command_conflict_status(self.robot_id, command_id, conflict_fields)
        self._set_operator_status(status)
        return status

    def _ack_with_operator_status(self, ack, operator_status):
        duplicate_ack = dict(ack or {})
        result = duplicate_ack.get("result") if isinstance(duplicate_ack.get("result"), dict) else {}
        safe_result = dict(result)
        safe_result["operator_status"] = operator_status
        duplicate_ack["result"] = safe_result
        return duplicate_ack

    def _set_operator_status(self, status):
        if hasattr(self.operator_backend, "_set_status"):
            extra = {
                "remote_ready": status["remote_ready"],
                "cloud_reachable": status["cloud_reachable"],
                "auth_state": status["auth_state"],
                "degradation_state": status["degradation_state"],
                "retry_hint": status["retry_hint"],
                "safe_phone_copy": status["safe_phone_copy"],
            }
            for key in (
                "pending_terminal_ack_id",
                "expired_command_id",
                "duplicate_command_id",
                "conflict_command_id",
                "conflict_reason",
                "conflict_fields",
                "cached_ack_state",
                "ack_semantics",
                "primary_actions_enabled",
                "proof_boundary",
            ):
                if key in status:
                    extra[key] = status[key]
            self.operator_backend._set_status(  # noqa: SLF001 - worker 与 RemoteBridge 同模块协作。
                status["state"],
                status["message"],
                **extra,
            )
        elif hasattr(self.operator_backend, "last_status"):
            self.operator_backend.last_status = status

    def _post_degraded_status_best_effort(self, error):
        self._post_status_best_effort(_phone_safe_degraded_status(self.robot_id, error))

    def _post_status_best_effort(self, status):
        try:
            self.cloud.post_status(status)
        except Exception:
            # 降级状态本身也是 best-effort；失败时仍然以“不执行命令、不推进游标”为准。
            pass

    def _load_last_ack_id(self, fallback):
        return self._load_cursor_state(fallback)["last_terminal_ack_id"]

    def _load_cursor_state(self, fallback):
        state = {
            "last_terminal_ack_id": str(fallback or ""),
            PENDING_TERMINAL_ACK_KEY: None,
        }
        if not self.cursor_state_path:
            return state
        path = Path(self.cursor_state_path)
        if not path.exists():
            return state
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"remote bridge cursor state unreadable: {exc}") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("remote bridge cursor state must be a JSON object")
        # 状态文件只保存游标和安全 pending ACK，不写 token、URL 或硬件细节，避免把运行密钥落盘。
        # 状态文件里显式保存的空 cursor 代表 ACK 尚未入云，不能被启动参数 fallback 覆盖。
        if "last_terminal_ack_id" in payload:
            state["last_terminal_ack_id"] = str(payload.get("last_terminal_ack_id") or "")
        elif "last_ack_id" in payload:
            state["last_terminal_ack_id"] = str(payload.get("last_ack_id") or "")
        else:
            state["last_terminal_ack_id"] = str(fallback or "")
        pending_ack = payload.get(PENDING_TERMINAL_ACK_KEY)
        if pending_ack is not None:
            if not isinstance(pending_ack, dict):
                raise RuntimeError("remote bridge pending ACK state must be a JSON object")
            command_id = str(pending_ack.get("command_id") or "").strip()
            ack = pending_ack.get("ack")
            if not command_id or not isinstance(ack, dict):
                raise RuntimeError("remote bridge pending ACK state is malformed")
            state[PENDING_TERMINAL_ACK_KEY] = {
                "command_id": command_id,
                "ack": self._safe_ack_for_state(ack),
            }
        return state

    def _persist_last_ack_id(self, command_id):
        self._persist_cursor_state(str(command_id), None)

    def _persist_pending_terminal_ack(self, command_id, ack):
        self.pending_terminal_ack = {
            "command_id": str(command_id),
            "ack": self._safe_ack_for_state(ack),
        }
        self._persist_cursor_state(self.last_ack_id, self.pending_terminal_ack)

    def _persist_cursor_state(self, command_id, pending_terminal_ack):
        if not self.cursor_state_path:
            return
        path = Path(self.cursor_state_path)
        payload = {
            "protocol_version": CURSOR_PROTOCOL_VERSION,
            "robot_id": self.robot_id,
            "last_terminal_ack_id": str(command_id),
            "evidence_boundary": CLOUD_ACK_OUTAGE_REPLAY_GUARD_BOUNDARY,
            "updated_at": time.time(),
        }
        if pending_terminal_ack:
            safe_pending_ack = {
                "protocol_version": CURSOR_PROTOCOL_VERSION,
                "robot_id": self.robot_id,
                "command_id": str(pending_terminal_ack["command_id"]),
                "ack": self._safe_ack_for_state(pending_terminal_ack["ack"]),
                "evidence_boundary": CLOUD_ACK_OUTAGE_REPLAY_GUARD_BOUNDARY,
                "updated_at": time.time(),
            }
            payload[PENDING_TERMINAL_ACK_KEY] = safe_pending_ack
        # 先写同目录临时文件再原子替换，避免重启时读到半截 JSON 后误用旧游标。
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            tmp_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
            os.replace(tmp_path, path)
        finally:
            try:
                tmp_path.unlink()
            except FileNotFoundError:
                pass

    def _safe_ack_for_state(self, ack):
        result = ack.get("result") if isinstance(ack.get("result"), dict) else {}
        safe_result = {}
        if "http_status" in result:
            try:
                safe_result["http_status"] = int(result["http_status"])
            except (TypeError, ValueError):
                safe_result["http_status"] = 0
        operator_status = result.get("operator_status")
        if isinstance(operator_status, dict):
            safe_result["operator_status"] = self._safe_operator_status(operator_status)
        # pending ACK 只需要足够重放 terminal envelope，不能把完整后端 payload 当重启状态持久化。
        return {
            "state": str(ack.get("state") or "failed"),
            "message": self._safe_state_text(ack.get("message") or ""),
            "result": safe_result,
        }

    def _safe_operator_status(self, operator_status):
        safe_status = {}
        for key in SAFE_OPERATOR_STATUS_KEYS:
            if key not in operator_status:
                continue
            value = operator_status[key]
            if isinstance(value, str):
                safe_status[key] = self._safe_state_text(value)
            elif isinstance(value, (bool, int, float)) or value is None:
                safe_status[key] = value
        return safe_status

    def _safe_state_text(self, value):
        return _safe_state_text_value(value)

    def _post_status_from_ack(self, ack):
        status = (ack.get("result") or {}).get("operator_status")
        if not isinstance(status, dict):
            return
        try:
            self.cloud.post_status(_snapshot_status(self.robot_id, status))
        except Exception:
            # ACK 后的状态刷新只是辅助手机显示；失败不能反向影响已提交的本地任务。
            pass

    def _remember_command_result(self, command_id, ack):
        self.command_results[command_id] = ack
        while len(self.command_results) > max(1, self.max_command_results):
            evicted_command_id = next(iter(self.command_results))
            self.command_results.pop(evicted_command_id)
            self.command_identities.pop(evicted_command_id, None)

    def _execute_command(self, command):
        payload = command["payload"]
        if command["type"] == "collect":
            target = str(payload.get("target") or "").strip()
            if not target:
                raise ValueError("collect target is required")
            return self.operator_backend.start_collection(
                target,
                int(payload.get("trash_type", 0) or 0),
            )
        if command["type"] == "confirm_dropoff":
            return self.operator_backend.confirm_dropoff(parse_bool(payload.get("accepted"), default=True))
        if command["type"] == "cancel":
            return self.operator_backend.cancel_collection()
        raise ValueError(f"unsupported command: {command['type']}")


class RemoteBridge(Node):
    """Outbound 4G remote bridge using HTTP polling."""

    def __init__(self):
        if rclpy is None:
            raise RuntimeError("RemoteBridge ROS node requires rclpy")
        super().__init__("remote_bridge")
        self.declare_parameter("enabled", False)
        self.declare_parameter("cloud_base_url", "")
        self.declare_parameter("robot_id", "trashbot-001")
        self.declare_parameter("bearer_token", "")
        self.declare_parameter("auth_token", "")
        self.declare_parameter("poll_interval_sec", 2.0)
        self.declare_parameter("last_ack_id", "")
        self.declare_parameter("cursor_state_path", "")
        self.declare_parameter("request_timeout_sec", 5.0)
        self.declare_parameter("collect_action_name", "/trashbot/collect_trash")
        self.declare_parameter("dropoff_service_name", "/trashbot/confirm_dropoff")

        self.enabled = parse_bool(self.get_parameter("enabled").value, default=False)
        self.cloud_base_url = str(self.get_parameter("cloud_base_url").value).strip()
        self.robot_id = str(self.get_parameter("robot_id").value)
        self.poll_interval_sec = float(self.get_parameter("poll_interval_sec").value)
        bearer_token = str(self.get_parameter("bearer_token").value).strip()
        auth_token = str(self.get_parameter("auth_token").value).strip()
        token = bearer_token or auth_token
        self.last_status = make_status(self.robot_id, "offline", "remote bridge initializing")
        self.active_goal_handle = None
        self.collect_pending = False
        self.task_lock = threading.Lock()

        self.collect_client = ActionClient(
            self,
            TrashCollection,
            str(self.get_parameter("collect_action_name").value),
        )
        self.dropoff_client = self.create_client(
            SetBool,
            str(self.get_parameter("dropoff_service_name").value),
        )
        self.cloud = None
        self.worker = None
        if self.enabled and self.cloud_base_url:
            self.cloud = RemoteCloudClient(
                self.cloud_base_url,
                self.robot_id,
                token,
                float(self.get_parameter("request_timeout_sec").value),
            )
            self.worker = RemoteBridgeWorker(
                self.cloud,
                self,
                self.robot_id,
                last_ack_id=str(self.get_parameter("last_ack_id").value),
                cursor_state_path=str(self.get_parameter("cursor_state_path").value),
            )
        self.timer = self.create_timer(max(0.2, self.poll_interval_sec), self._poll_once)
        self.get_logger().info(
            f"RemoteBridge ready enabled={self.enabled} cloud={self.cloud_base_url or '<unset>'}"
        )

    def _poll_once(self):
        if not self.enabled:
            return
        if self.worker is None:
            self._set_status("needs_config", "remote bridge enabled without cloud_base_url")
            return
        try:
            self.worker.poll_once()
        except Exception as exc:  # noqa: BLE001 - keep bridge alive across 4G drops.
            self._set_status("offline", f"cloud unavailable: {exc}")

    def snapshot(self):
        return dict(self.last_status)

    def start_collection(self, target, trash_type=0):
        target = str(target or "").strip()
        trash_type = int(trash_type or 0)
        with self.task_lock:
            if self.collect_pending or self.active_goal_handle is not None:
                payload = make_status(
                    self.robot_id,
                    "busy",
                    "collect command ignored because a task is active",
                )
                return 409, payload
            self.collect_pending = True
        if not self.collect_client.wait_for_server(timeout_sec=1.0):
            payload = make_status(self.robot_id, "needs_human_help", "collect_trash action server unavailable")
            with self.task_lock:
                self.collect_pending = False
            self.last_status = payload
            return 503, payload
        goal = TrashCollection.Goal()
        goal.trash_goal_frame = target
        goal.trash_type = trash_type
        future = self.collect_client.send_goal_async(goal, feedback_callback=self._on_collect_feedback)
        future.add_done_callback(self._on_goal_response)
        self._set_status("delivering", f"remote collect command accepted for {target or '<default>'}")
        return 202, self.snapshot()

    def confirm_dropoff(self, accepted=True):
        if not self.dropoff_client.wait_for_service(timeout_sec=1.0):
            payload = make_status(self.robot_id, "needs_human_help", "confirm_dropoff service unavailable")
            self.last_status = payload
            return 503, payload
        request = SetBool.Request()
        request.data = parse_bool(accepted, default=True)
        future = self.dropoff_client.call_async(request)
        done = threading.Event()
        holder = {}

        def _done(result_future):
            try:
                holder["response"] = result_future.result()
            except Exception as exc:  # noqa: BLE001 - report async service failures to the cloud.
                holder["error"] = exc
            finally:
                done.set()

        future.add_done_callback(_done)
        if not done.wait(2.0):
            payload = make_status(self.robot_id, "needs_human_help", "confirm_dropoff service timed out")
            self.last_status = payload
            return 504, payload
        if "error" in holder:
            payload = make_status(self.robot_id, "needs_human_help", f"confirm_dropoff service failed: {holder['error']}")
            self.last_status = payload
            return 503, payload
        response = holder["response"]
        state = "returning" if request.data and response.success else "needs_human_help"
        payload = make_status(
            self.robot_id,
            state,
            response.message,
            accepted=request.data,
            service_accepted=bool(response.success),
        )
        self.last_status = payload
        return (200 if response.success else 409), payload

    def cancel_collection(self):
        with self.task_lock:
            goal_handle = self.active_goal_handle
            collect_pending = self.collect_pending
        if goal_handle is None:
            state = "busy" if collect_pending else "canceled"
            message = "collect goal is still pending; retry cancel after acceptance" if collect_pending else "no active task to cancel"
            self._set_status(state, message)
            return 409, self.snapshot()
        goal_handle.cancel_goal_async()
        self._set_status("canceled", "remote cancel requested")
        return 202, self.snapshot()

    def _on_goal_response(self, future):
        try:
            goal_handle = future.result()
        except Exception as exc:  # noqa: BLE001 - surface async action failures to the cloud.
            with self.task_lock:
                self.collect_pending = False
                self.active_goal_handle = None
            self._set_status("needs_human_help", f"collect goal failed: {exc}")
            return
        if not goal_handle.accepted:
            with self.task_lock:
                self.collect_pending = False
                self.active_goal_handle = None
            self._set_status("needs_human_help", "collect goal rejected")
            return
        with self.task_lock:
            self.collect_pending = False
            self.active_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_collect_result)

    def _on_collect_feedback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self._set_status(feedback.state or "delivering", feedback.message)

    def _on_collect_result(self, future):
        try:
            result = future.result().result
            self._set_status(
                "completed" if result.success else "failed",
                result.error_message or ("collection complete" if result.success else "collection failed"),
                task_record_path=result.task_record_path,
                error_code=result.error_code,
                final_state=result.final_state,
            )
        except Exception as exc:  # noqa: BLE001 - clear active state after async result failures.
            self._set_status("needs_human_help", f"collect result failed: {exc}")
        finally:
            with self.task_lock:
                self.active_goal_handle = None
                self.collect_pending = False

    def _set_status(self, state, message="", **extra):
        self.last_status = make_status(self.robot_id, state, message, **extra)


def main(args=None):
    if rclpy is None:
        raise RuntimeError("remote_bridge requires ROS2 rclpy")
    rclpy.init(args=args)
    node = RemoteBridge()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
