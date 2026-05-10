import json
import math
import os
import threading
import time
import uuid
from importlib.metadata import PackageNotFoundError, version
from http.server import ThreadingHTTPServer

import rclpy
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_srvs.srv import SetBool

from ros2_trashbot_interfaces.action import TrashCollection
from ros2_trashbot_behavior.operator_gateway_diagnostics import (
    REVIEW_DECISION_VALUES,
    build_diagnostics_payload,
    load_review_decision_log,
    normalize_log_refs,
    summarize_vision_manifest,
)
from ros2_trashbot_behavior.operator_gateway_http import make_handler, status_payload


TERMINAL_STATES = {"completed", "failed", "canceled", "rejected"}


def _installed_version(package_name, fallback="0.1.0"):
    try:
        return version(package_name)
    except (PackageNotFoundError, ValueError):
        return fallback


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
        self.declare_parameter("pose_topic", "/amcl_pose")
        self.declare_parameter("software_version", _installed_version("ros2_trashbot_behavior"))
        self.declare_parameter("map_version", "")
        self.declare_parameter("route_version", "")
        self.declare_parameter("log_refs", [])
        self.declare_parameter("vision_sample_manifest_ref", "~/.ros/trashbot_vision_samples/manifest.json")
        self.declare_parameter(
            "review_decision_log_ref",
            "~/.ros/trashbot_vision_samples/review_decisions.jsonl",
        )

        self.host = str(self.get_parameter("host").value)
        self.port = int(self.get_parameter("port").value)
        self.default_target = str(self.get_parameter("default_target").value)
        self.collect_action_name = str(self.get_parameter("collect_action_name").value)
        self.dropoff_service_name = str(self.get_parameter("dropoff_service_name").value)
        self.status_file = str(self.get_parameter("status_file").value)
        self.pose_topic = str(self.get_parameter("pose_topic").value)
        self.software_version = str(self.get_parameter("software_version").value)
        self.map_version = str(self.get_parameter("map_version").value)
        self.route_version = str(self.get_parameter("route_version").value)
        self.log_refs = normalize_log_refs(self.get_parameter("log_refs").value)
        self.vision_sample_manifest_ref = os.path.expanduser(
            str(self.get_parameter("vision_sample_manifest_ref").value)
        )
        self.review_decision_log_ref = os.path.expanduser(
            str(self.get_parameter("review_decision_log_ref").value)
        )

        self._lock = threading.Lock()
        self._goal_handle = None
        self._collect_pending = False
        self._robot_pose = None
        self._robot_path = []
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
            robot_pose=None,
            robot_path=[],
        )

        self.collect_client = ActionClient(self, TrashCollection, self.collect_action_name)
        self.dropoff_client = self.create_client(SetBool, self.dropoff_service_name)
        self.pose_subscription = self.create_subscription(
            PoseWithCovarianceStamped,
            self.pose_topic,
            self._on_pose,
            10,
        )
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
            payload["robot_pose"] = dict(self._robot_pose) if self._robot_pose else None
            payload["robot_location"] = dict(self._robot_pose) if self._robot_pose else None
            payload["robot_path"] = list(self._robot_path)
        self._write_status(payload)
        return payload

    def diagnostics(self):
        latest_status = self.snapshot()
        return build_diagnostics_payload(
            latest_status,
            software_version=self.software_version,
            map_version=self.map_version,
            route_version=self.route_version,
            log_refs=self.log_refs,
            vision_sample_manifest_ref=self.vision_sample_manifest_ref,
            review_decision_log_ref=self.review_decision_log_ref,
            operator_status_file=self.status_file,
        )

    def vision_review_queue(self):
        review_decision_log, decision_index = load_review_decision_log(self.review_decision_log_ref)
        vision_samples = summarize_vision_manifest(
            self.vision_sample_manifest_ref,
            decision_index=decision_index,
        )
        return {
            "ok": True,
            "review_decision_log_ref": self.review_decision_log_ref,
            "review_decision_log": review_decision_log,
            "review_queue_count": int(vision_samples.get("review_queue_count", 0)),
            "review_queue": list(vision_samples.get("review_queue", [])),
            "manifest_ref": vision_samples.get("manifest_ref", self.vision_sample_manifest_ref),
            "manifest_read_error": vision_samples.get("read_error", ""),
        }

    def submit_review_decision(self, payload):
        payload = dict(payload or {})
        sample_id = str(payload.get("sample_id", "")).strip()
        decision = str(payload.get("decision", "")).strip().lower()
        comment = str(payload.get("comment", "")).strip()
        option = str(payload.get("option", "")).strip()
        operator = str(payload.get("operator", "")).strip()
        if not sample_id:
            return 400, self._review_error(
                "bad_request",
                "sample_id is required",
                details={"field": "sample_id"},
            )
        if decision not in REVIEW_DECISION_VALUES:
            return 400, self._review_error(
                "bad_request",
                "decision must be one of approved, rejected, needs_retry",
                details={"field": "decision", "allowed_values": sorted(REVIEW_DECISION_VALUES)},
            )

        sample_ref_map, sample_error = self._vision_sample_refs()
        if sample_error:
            return 503, self._review_error(
                "review_queue_unavailable",
                sample_error,
                details={"vision_sample_manifest_ref": self.vision_sample_manifest_ref},
            )
        if sample_id not in sample_ref_map:
            return 404, self._review_error(
                "sample_not_found",
                f"sample_id not found in vision manifest: {sample_id}",
                details={"sample_id": sample_id, "vision_sample_manifest_ref": self.vision_sample_manifest_ref},
            )

        ts = time.time()
        decision_record = {
            "decision_id": f"review-{int(ts * 1000)}-{uuid.uuid4().hex[:8]}",
            "sample_id": sample_id,
            "sample_ref": sample_ref_map[sample_id],
            "decision": decision,
            "option": option,
            "comment": comment,
            "operator": operator,
            "timestamp": ts,
            "stored_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)),
            "source_ref": self.review_decision_log_ref,
        }
        write_error = self._append_review_decision(decision_record)
        if write_error:
            return 503, self._review_error(
                "decision_store_write_failed",
                write_error,
                details={"review_decision_log_ref": self.review_decision_log_ref},
            )

        return 201, {
            "ok": True,
            "decision_id": decision_record["decision_id"],
            "sample_id": sample_id,
            "decision": decision,
            "option": option,
            "comment": comment,
            "operator": operator,
            "stored_at": decision_record["stored_at"],
            "review_decision_log_ref": self.review_decision_log_ref,
            "last_decision": {
                "decision_id": decision_record["decision_id"],
                "decision": decision,
                "option": option,
                "comment": comment,
                "operator": operator,
                "timestamp": ts,
            },
        }

    def start_collection(self, target, trash_type=0):
        target = (target or self.default_target).strip()
        if not target:
            return 400, status_payload("bad_request", "target is required")
        with self._lock:
            task_active = self._collect_pending or (
                self._goal_handle is not None and self._latest_status.get("state") not in TERMINAL_STATES
            )
            if task_active:
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
            self._collect_pending = True
            self._write_status(self._latest_status)

        if not self.collect_client.wait_for_server(timeout_sec=1.0):
            payload = status_payload("needs_human_help", "collect_trash action server is unavailable", target=target)
            with self._lock:
                self._collect_pending = False
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
            try:
                holder["response"] = result_future.result()
            except Exception as exc:  # noqa: BLE001 - report async service failures to the operator.
                holder["error"] = exc
            finally:
                done.set()

        future.add_done_callback(_done)
        if not done.wait(2.0):
            payload = status_payload("needs_human_help", "confirm_dropoff service timed out")
            self._set_status(payload)
            return 504, payload
        if "error" in holder:
            payload = status_payload("needs_human_help", f"confirm_dropoff service failed: {holder['error']}")
            self._set_status(payload)
            return 503, payload
        response = holder["response"]
        state = "returning" if accepted and response.success else "needs_human_help"
        payload = status_payload(state, response.message, accepted=accepted, service_accepted=response.success)
        self._set_status(payload)
        return 200 if response.success else 409, payload

    def cancel_collection(self):
        with self._lock:
            goal_handle = self._goal_handle
            collect_pending = self._collect_pending
        if goal_handle is None:
            if collect_pending:
                return 409, status_payload("busy", "collect goal is still pending; retry cancel after acceptance")
            return 409, status_payload("canceled", "no active collection goal")
        future = goal_handle.cancel_goal_async()
        future.add_done_callback(lambda _future: self._set_status(status_payload("canceled", "cancel requested")))
        return 202, status_payload("canceling", "cancel requested")

    def _on_goal_response(self, future):
        try:
            goal_handle = future.result()
        except Exception as exc:  # noqa: BLE001 - surface async action failures to the operator.
            with self._lock:
                self._collect_pending = False
                self._goal_handle = None
            self._set_status(status_payload("needs_human_help", f"collect_trash goal failed: {exc}"))
            return
        if not goal_handle.accepted:
            with self._lock:
                self._collect_pending = False
                self._goal_handle = None
            self._set_status(status_payload("rejected", "collect_trash goal rejected"))
            return
        with self._lock:
            self._collect_pending = False
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
        try:
            result = future.result().result
            state = "completed" if result.success else "failed"
            self._set_status(status_payload(
                state,
                result.error_message or ("collection complete" if result.success else "collection failed"),
                task_record_path=result.task_record_path,
                total_duration_sec=float(result.total_duration_sec),
                error_code=result.error_code,
                final_state=result.final_state,
                can_collect=True,
                can_confirm_dropoff=False,
                can_cancel=False,
                last_task={
                    "task_record_path": result.task_record_path,
                    "success": bool(result.success),
                    "error_code": result.error_code,
                    "final_state": result.final_state,
                },
            ))
        except Exception as exc:  # noqa: BLE001 - keep operator UI usable after async result failures.
            self._set_status(status_payload(
                "needs_human_help",
                f"collect_trash result failed: {exc}",
                can_collect=True,
                can_confirm_dropoff=False,
                can_cancel=False,
            ))
        finally:
            with self._lock:
                self._goal_handle = None
                self._collect_pending = False

    def _set_status(self, payload):
        with self._lock:
            payload["robot_pose"] = dict(self._robot_pose) if self._robot_pose else None
            payload["robot_location"] = dict(self._robot_pose) if self._robot_pose else None
            payload["robot_path"] = list(self._robot_path)
            self._latest_status = payload
        self._write_status(payload)

    def _on_pose(self, msg):
        pose = msg.pose.pose
        yaw = self._yaw_from_quaternion(pose.orientation)
        robot_pose = {
            "frame_id": msg.header.frame_id or "map",
            "x": float(pose.position.x),
            "y": float(pose.position.y),
            "yaw": yaw,
            "updated_at": self.get_clock().now().nanoseconds / 1e9,
        }
        with self._lock:
            self._robot_pose = robot_pose
            self._robot_path.append({
                "x": robot_pose["x"],
                "y": robot_pose["y"],
                "yaw": robot_pose["yaw"],
                "updated_at": robot_pose["updated_at"],
            })
            self._robot_path = self._robot_path[-200:]
            self._latest_status["robot_pose"] = dict(robot_pose)
            self._latest_status["robot_location"] = dict(robot_pose)
            self._latest_status["robot_path"] = list(self._robot_path)
        self._write_status()

    def _yaw_from_quaternion(self, orientation):
        siny_cosp = 2.0 * (orientation.w * orientation.z + orientation.x * orientation.y)
        cosy_cosp = 1.0 - 2.0 * (orientation.y * orientation.y + orientation.z * orientation.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def _write_status(self, payload=None):
        payload = payload or self._latest_status
        try:
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            self.get_logger().warn(f"failed writing operator status: {exc}")

    def _append_review_decision(self, record):
        decision_log_dir = os.path.dirname(self.review_decision_log_ref)
        try:
            if decision_log_dir:
                os.makedirs(decision_log_dir, exist_ok=True)
            with self._lock:
                with open(self.review_decision_log_ref, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return ""
        except OSError as exc:
            return f"failed writing review decision log: {exc}"

    def _vision_sample_refs(self):
        if not self.vision_sample_manifest_ref:
            return None, "vision sample manifest is not configured"
        if not os.path.exists(self.vision_sample_manifest_ref):
            return None, f"vision sample manifest not found: {self.vision_sample_manifest_ref}"
        try:
            with open(self.vision_sample_manifest_ref, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            return None, f"failed reading vision sample manifest: {exc}"

        samples = manifest.get("samples") if isinstance(manifest, dict) else None
        if not isinstance(samples, list):
            return None, "vision sample manifest has no samples list"
        refs = {}
        for sample in samples:
            if not isinstance(sample, dict):
                continue
            sample_id = str(sample.get("sample_id", "")).strip()
            if not sample_id:
                continue
            refs[sample_id] = str(sample.get("sample_ref", "")).strip()
        if not refs:
            return None, "vision sample manifest has no valid sample_id entries"
        return refs, ""

    def _review_error(self, code, message, details=None):
        return {
            "ok": False,
            "error": {
                "code": str(code),
                "message": str(message),
                "details": details if isinstance(details, dict) else {},
            },
        }

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
