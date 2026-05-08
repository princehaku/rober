import json
import threading
from http.server import ThreadingHTTPServer

import rclpy
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_srvs.srv import SetBool

from ros2_trashbot_interfaces.action import TrashCollection
from ros2_trashbot_behavior.operator_gateway_http import make_handler, status_payload


TERMINAL_STATES = {"completed", "failed", "canceled", "rejected"}


class OperatorGateway(Node):
    """Small local HTTP gateway for operator/mobile control."""

    def __init__(self):
        super().__init__("operator_gateway")
        self.declare_parameter("host", "0.0.0.0")
        self.declare_parameter("port", 8766)
        self.declare_parameter("default_target", "trash_station")
        self.declare_parameter("collect_action_name", "/trashbot/collect_trash")
        self.declare_parameter("dropoff_service_name", "/trashbot/confirm_dropoff")
        self.declare_parameter("status_file", "/tmp/trashbot_operator_status.json")

        self.host = str(self.get_parameter("host").value)
        self.port = int(self.get_parameter("port").value)
        self.default_target = str(self.get_parameter("default_target").value)
        self.collect_action_name = str(self.get_parameter("collect_action_name").value)
        self.dropoff_service_name = str(self.get_parameter("dropoff_service_name").value)
        self.status_file = str(self.get_parameter("status_file").value)

        self._lock = threading.Lock()
        self._goal_handle = None
        self._latest_status = status_payload(
            "waiting_for_trash",
            "Waiting for trash.",
            can_collect=True,
            can_confirm_dropoff=False,
            can_cancel=False,
            ros={"collect_action_ready": False, "dropoff_service_ready": False},
            active_task=None,
            last_task=None,
            target=self.default_target,
        )

        self.collect_client = ActionClient(self, TrashCollection, self.collect_action_name)
        self.dropoff_client = self.create_client(SetBool, self.dropoff_service_name)
        self.server = ThreadingHTTPServer((self.host, self.port), make_handler(self))
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self._write_status()
        self.get_logger().info(f"Operator gateway listening on http://{self.host}:{self.port}")

    def destroy_node(self):
        self.server.shutdown()
        self.server.server_close()
        return super().destroy_node()

    def snapshot(self):
        with self._lock:
            payload = dict(self._latest_status)
        self._write_status(payload)
        return payload

    def start_collection(self, target, trash_type=0):
        target = (target or self.default_target).strip()
        if not target:
            return 400, status_payload("bad_request", "target is required")
        with self._lock:
            if self._goal_handle is not None and self._latest_status.get("state") not in TERMINAL_STATES:
                return 409, status_payload("busy", "collection already running")
            self._latest_status = status_payload(
                "loaded_and_ready",
                "Sending collect_trash goal.",
                target=target,
                can_collect=False,
                can_confirm_dropoff=False,
                can_cancel=True,
            )
            self._goal_handle = None
            self._write_status(self._latest_status)

        if not self.collect_client.wait_for_server(timeout_sec=1.0):
            payload = status_payload("needs_human_help", "collect_trash action server is unavailable", target=target)
            self._set_status(payload)
            return 503, payload

        goal = TrashCollection.Goal()
        goal.trash_goal_frame = target
        goal.trash_type = int(trash_type)
        future = self.collect_client.send_goal_async(goal, feedback_callback=self._on_collect_feedback)
        future.add_done_callback(self._on_goal_response)
        return 202, self.snapshot()

    def confirm_dropoff(self, accepted=True):
        if not self.dropoff_client.wait_for_service(timeout_sec=1.0):
            payload = status_payload("needs_human_help", "confirm_dropoff service is unavailable")
            self._set_status(payload)
            return 503, payload
        request = SetBool.Request()
        request.data = bool(accepted)
        future = self.dropoff_client.call_async(request)
        done = threading.Event()
        holder = {}

        def _done(result_future):
            holder["response"] = result_future.result()
            done.set()

        future.add_done_callback(_done)
        if not done.wait(2.0):
            payload = status_payload("needs_human_help", "confirm_dropoff service timed out")
            self._set_status(payload)
            return 504, payload
        response = holder["response"]
        state = "returning" if accepted and response.success else "needs_human_help"
        payload = status_payload(state, response.message, accepted=accepted, service_accepted=response.success)
        self._set_status(payload)
        return 200 if response.success else 409, payload

    def cancel_collection(self):
        with self._lock:
            goal_handle = self._goal_handle
        if goal_handle is None:
            return 409, status_payload("canceled", "no active collection goal")
        future = goal_handle.cancel_goal_async()
        future.add_done_callback(lambda _future: self._set_status(status_payload("canceled", "cancel requested")))
        return 202, status_payload("canceling", "cancel requested")

    def _on_goal_response(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self._set_status(status_payload("rejected", "collect_trash goal rejected"))
            return
        with self._lock:
            self._goal_handle = goal_handle
        self._set_status(status_payload("delivering", "collect_trash goal accepted", can_cancel=True))
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._on_collect_result)

    def _on_collect_feedback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self._set_status(status_payload(
            self._operator_state(feedback.state, feedback.current_step),
            feedback.message,
            event=feedback.event,
            current_step=feedback.current_step,
            percent_complete=float(feedback.percent_complete),
            elapsed_sec=float(feedback.elapsed_sec),
            can_collect=False,
            can_confirm_dropoff=feedback.current_step == "dropoff",
            can_cancel=True,
        ))

    def _on_collect_result(self, future):
        result = future.result().result
        state = "completed" if result.success else "failed"
        self._set_status(status_payload(
            state,
            result.error_message or ("collection complete" if result.success else "collection failed"),
            task_record_path=result.task_record_path,
            total_duration_sec=float(result.total_duration_sec),
            can_collect=True,
            can_confirm_dropoff=False,
            can_cancel=False,
            last_task={"task_record_path": result.task_record_path, "success": bool(result.success)},
        ))
        with self._lock:
            self._goal_handle = None

    def _set_status(self, payload):
        with self._lock:
            self._latest_status = payload
        self._write_status(payload)

    def _write_status(self, payload=None):
        payload = payload or self._latest_status
        try:
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            self.get_logger().warn(f"failed writing operator status: {exc}")

    def _operator_state(self, feedback_state, current_step):
        if current_step == "dropoff" or feedback_state == "dropoff":
            return "arrived_at_station"
        if feedback_state in ("loaded", "idle"):
            return "loaded_and_ready"
        if feedback_state in ("delivering", "returning", "completed", "canceled"):
            return feedback_state
        if feedback_state in ("error", "failed"):
            return "needs_human_help"
        return feedback_state or "delivering"


def main(args=None):
    rclpy.init(args=args)
    node = OperatorGateway()
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
