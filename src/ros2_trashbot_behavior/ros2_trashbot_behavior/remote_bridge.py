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
    RemoteCloudClient,
    command_expired,
    make_status,
    parse_bool,
)

if "threading" not in globals():
    import threading


def _snapshot_status(robot_id, snapshot):
    snapshot = dict(snapshot or {})
    state = snapshot.pop("state", "unknown")
    message = snapshot.pop("message", "")
    snapshot.pop("protocol_version", None)
    snapshot.pop("robot_id", None)
    snapshot.pop("updated_at", None)
    return make_status(robot_id, state, message, **snapshot)


class RemoteBridgeWorker:
    """Pure-Python HTTP polling worker for the outbound 4G bridge."""

    def __init__(self, cloud_client, operator_backend, robot_id, max_command_results=200):
        self.cloud = cloud_client
        self.operator_backend = operator_backend
        self.robot_id = robot_id
        self.last_ack_id = ""
        self.command_results = {}
        self.max_command_results = int(max_command_results)

    def poll_once(self):
        status = _snapshot_status(self.robot_id, self.operator_backend.snapshot())
        self.cloud.post_status(status)
        try:
            command = self.cloud.get_next_command(self.last_ack_id)
        except InvalidRemoteCommand as exc:
            command = exc.command if isinstance(exc.command, dict) else {}
            command_id = str(command.get("id") or "").strip()
            if not command_id:
                raise
            ack = {
                "state": "failed",
                "message": str(exc),
                "result": {"operator_status": status},
            }
            self._remember_command_result(command_id, ack)
            self.cloud.post_ack(command_id, ack["state"], ack["message"], ack["result"])
            self.last_ack_id = command_id
            return True
        if command is None:
            return False
        if command["id"] in self.command_results:
            ack = self.command_results[command["id"]]
            self.cloud.post_ack(command["id"], ack["state"], ack["message"], ack["result"])
            self.last_ack_id = command["id"]
            return True
        if command_expired(command):
            ack = {
                "state": "ignored",
                "message": "command expired",
                "result": {"operator_status": status},
            }
            self._remember_command_result(command["id"], ack)
            self.cloud.post_ack(command["id"], ack["state"], ack["message"], ack["result"])
            self.last_ack_id = command["id"]
            return True

        try:
            http_status, payload = self._execute_command(command)
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
                "message": str(exc),
                "result": result,
            }
        self._remember_command_result(command["id"], ack)
        self.cloud.post_ack(command["id"], ack["state"], ack["message"], ack["result"])
        self.last_ack_id = command["id"]
        return True

    def _remember_command_result(self, command_id, ack):
        self.command_results[command_id] = ack
        while len(self.command_results) > max(1, self.max_command_results):
            self.command_results.pop(next(iter(self.command_results)))

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
        self.declare_parameter("auth_token", "")
        self.declare_parameter("poll_interval_sec", 2.0)
        self.declare_parameter("request_timeout_sec", 5.0)
        self.declare_parameter("collect_action_name", "/trashbot/collect_trash")
        self.declare_parameter("dropoff_service_name", "/trashbot/confirm_dropoff")

        self.enabled = parse_bool(self.get_parameter("enabled").value, default=False)
        self.cloud_base_url = str(self.get_parameter("cloud_base_url").value).strip()
        self.robot_id = str(self.get_parameter("robot_id").value)
        self.poll_interval_sec = float(self.get_parameter("poll_interval_sec").value)
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
                str(self.get_parameter("auth_token").value),
                float(self.get_parameter("request_timeout_sec").value),
            )
            self.worker = RemoteBridgeWorker(self.cloud, self, self.robot_id)
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
                "completed" if result.success else "needs_human_help",
                result.error_message or ("collection complete" if result.success else "collection failed"),
                task_record_path=result.task_record_path,
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
