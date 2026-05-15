import json
import os
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from enum import Enum

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from std_srvs.srv import SetBool

from ros2_trashbot_interfaces.action import TrashCollection, Patrol
from ros2_trashbot_interfaces.msg import Waypoint, WaypointList
from ros2_trashbot_interfaces.srv import RecordWaypoint

from ros2_trashbot_behavior.delivery_navigation import find_waypoint_pose, load_waypoint_file
from ros2_trashbot_behavior.delivery_state_machine import DeliveryStateMachine
from ros2_trashbot_behavior.dropoff_confirmation import DropoffConfirmationGate
from ros2_trashbot_behavior.task_record import write_task_record


class RobotState(Enum):
    IDLE = 0
    LEARNING = 1
    PATROLLING = 2
    COLLECTING = 3
    DELIVERING = 4
    RETURNING = 5
    ERROR = 6
    LOADED = 7
    DROPOFF = 8


@dataclass
class NavigationResult:
    success: bool
    result_code: str
    message: str
    elapsed_sec: float
    evidence: dict = field(default_factory=dict)


FIXED_ROUTE_PROGRESS_FIELDS = (
    "source",
    "route_contract_version",
    "route_file",
    "route_id",
    "route_file_basename",
    "checkpoint",
    "checkpoint_id",
    "current_index",
    "target",
    "current_target",
    "total",
    "total_checkpoints",
    "evidence_ref",
    "failure_code",
)


ELEVATOR_ASSIST_PROMPT = "你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,"
ELEVATOR_ASSIST_PROOF_GATE = "software_proof_docker_elevator_assist_default_mainline_gate"
ELEVATOR_ASSIST_REHEARSAL_SCHEMA = "trashbot.elevator_assist_rehearsal_evidence.v1"
ELEVATOR_ASSIST_REHEARSAL_PROOF_GATE = "software_proof_docker_elevator_evidence_driven_mainline_gate"
ELEVATOR_ASSIST_BOUNDARY = (
    "software proof dry-run only; not real elevator, not real speaker/TTS, "
    "not real Nav2/fixed-route, not HIL; 不证明真实电梯、真实喇叭、真实 Nav2、HIL 或送达成功"
)
ELEVATOR_ASSIST_NOT_PROVEN = (
    "real_elevator",
    "real_speaker_tts",
    "real_nav2_or_fixed_route",
    "hil",
    "delivery_success",
)
ELEVATOR_ASSIST_RERUN_GUIDANCE = (
    "Keep elevator_assist_enabled=true with elevator_assist_mode=dry_run for the "
    "default software proof gate; only disable it with an operator-visible reason."
)
ELEVATOR_ASSIST_DRY_RUN_PHASES = (
    "approaching_elevator",
    "waiting_elevator_open",
    "entering_elevator",
    "requesting_floor_help",
    "waiting_target_floor",
    "exiting_elevator",
    "resume_delivery",
)
ELEVATOR_ASSIST_REHEARSAL_REQUIRED_PHASES = (
    "waiting_elevator_open",
    "entering_elevator",
    "requesting_floor_help",
    "waiting_target_floor",
    "exiting_elevator",
)
ELEVATOR_ASSIST_REHEARSAL_REQUIRED_NOT_PROVEN = (
    "real_elevator",
    "hil",
    "delivery_success",
)
ELEVATOR_ASSIST_REHEARSAL_EVIDENCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")
ELEVATOR_ASSIST_DRY_RUN_EVIDENCE = {
    "approaching_elevator": "door_closed_or_unknown",
    "waiting_elevator_open": "door_open",
    "entering_elevator": "inside_elevator",
    "requesting_floor_help": "inside_elevator",
    "waiting_target_floor": "target_floor_confirmed",
    "exiting_elevator": "safe_to_exit",
    "resume_delivery": "safe_to_exit",
}
ELEVATOR_ASSIST_FAILURES = {
    "door_timeout": {
        "phase": "waiting_elevator_open",
        "evidence": "door_closed_or_unknown",
        "reason": "elevator door did not open before dry-run timeout",
    },
    "target_floor_unconfirmed": {
        "phase": "waiting_target_floor",
        "evidence": "target_floor_unconfirmed",
        "reason": "target floor was not confirmed by dry-run evidence",
    },
    "unsafe_to_exit": {
        "phase": "exiting_elevator",
        "evidence": "unsafe_to_exit",
        "reason": "dry-run evidence marked elevator exit unsafe",
    },
}


class TaskOrchestrator(Node):
    """Main task coordinator. Manages the full lifecycle:
    Phase 1 (Learning): Drive around, build map, record waypoints
    Phase 2 (Autonomous): Patrol → detect trash → collect → deliver → repeat"""

    def __init__(self):
        super().__init__('task_orchestrator')

        # State machine
        self.state = RobotState.IDLE
        self.learn_count = 0
        self.collection_count = 0
        self.declare_parameter("task_record_dir", "~/.ros/trashbot_tasks")
        self.declare_parameter("delivery_target", "trash_station")
        self.declare_parameter("delivery_dry_run", False)
        self.declare_parameter("delivery_mode", "dry_run")
        self.declare_parameter("waypoint_file", "~/.ros/trashbot_maps/waypoints.yaml")
        self.declare_parameter("return_target", "")
        self.declare_parameter("navigation_timeout_sec", 120.0)
        self.declare_parameter("navigation_retry_limit", 0)
        self.declare_parameter("dropoff_mode", "dry_run")
        self.declare_parameter("dropoff_timeout_sec", 30.0)
        self.declare_parameter("fixed_route_status_file", "~/.ros/trashbot_fixed_route/status.json")
        self.declare_parameter("elevator_assist_enabled", True)
        self.declare_parameter("elevator_assist_mode", "dry_run")
        self.declare_parameter("elevator_assist_target_floor", "1")
        self.declare_parameter("elevator_assist_dry_run_failure", "")
        self.declare_parameter("elevator_assist_evidence_file", "")
        self.task_record_dir = os.path.expanduser(self.get_parameter("task_record_dir").value)
        self.delivery_target = str(self.get_parameter("delivery_target").value)
        self.delivery_mode = str(self.get_parameter("delivery_mode").value).lower()
        self.delivery_dry_run = bool(self.get_parameter("delivery_dry_run").value)
        self.waypoint_file = os.path.expanduser(self.get_parameter("waypoint_file").value)
        self.return_target = str(self.get_parameter("return_target").value)
        self.navigation_timeout_sec = float(self.get_parameter("navigation_timeout_sec").value)
        self.navigation_retry_limit = int(self.get_parameter("navigation_retry_limit").value)
        self.dropoff_mode = str(self.get_parameter("dropoff_mode").value).lower()
        self.dropoff_timeout_sec = float(self.get_parameter("dropoff_timeout_sec").value)
        self.fixed_route_status_file = os.path.expanduser(
            self.get_parameter("fixed_route_status_file").value
        )
        self.elevator_assist_enabled = bool(self.get_parameter("elevator_assist_enabled").value)
        self.elevator_assist_mode = str(self.get_parameter("elevator_assist_mode").value).lower()
        self.elevator_assist_target_floor = str(
            self.get_parameter("elevator_assist_target_floor").value
        )
        self.elevator_assist_dry_run_failure = str(
            self.get_parameter("elevator_assist_dry_run_failure").value
        ).strip().lower()
        self.elevator_assist_evidence_file = os.path.expanduser(
            str(self.get_parameter("elevator_assist_evidence_file").value).strip()
        )
        if self.delivery_dry_run:
            self.delivery_mode = "dry_run"
        self.navigator = None
        self.dropoff_gate = DropoffConfirmationGate()
        self.collection_lock = threading.Lock()
        self.collection_active = False

        # Services
        self.record_wp_client = self.create_client(
            RecordWaypoint, '/trashbot/record_waypoint')
        self.confirm_dropoff_service = self.create_service(
            SetBool, '/trashbot/confirm_dropoff', self._confirm_dropoff_callback)

        # Subscriptions
        self.waypoint_sub = self.create_subscription(
            WaypointList, '/trashbot/waypoints',
            self._on_waypoint_list, 10)

        # Action servers (use separate callback group to avoid blocking)
        cb_group = MutuallyExclusiveCallbackGroup()

        self.patrol_server = ActionServer(
            self, Patrol, '/trashbot/patrol',
            execute_callback=self._execute_patrol,
            cancel_callback=self._cancel_callback,
            callback_group=cb_group)

        self.collection_server = ActionServer(
            self, TrashCollection, '/trashbot/collect_trash',
            goal_callback=self._collection_goal_callback,
            execute_callback=self._execute_collection,
            cancel_callback=self._cancel_callback,
            callback_group=cb_group)

        # Timer for state monitoring
        self.state_timer = self.create_timer(1.0, self._state_monitor)

        self.get_logger().info('TaskOrchestrator ready. Awaiting learning or patrol command.')

    def _state_monitor(self):
        """Periodic state logging."""
        state_names = {s: s.name for s in RobotState}
        self.get_logger().debug(
            f'State={state_names[self.state]} '
            f'learn_count={self.learn_count} '
            f'collections={self.collection_count}')

    def _on_waypoint_list(self, msg: WaypointList):
        """Update when waypoint list changes."""
        self.get_logger().info(
            f'Waypoint list updated: {len(msg.waypoints)} waypoints, '
            f'{msg.total_trash_bins} bins, {msg.total_pickup_points} pickup points')

    async def _execute_patrol(self, goal_handle):
        """Patrol action: navigate waypoints, detect trash along the way.
        If learn_mode=True, record new trash/bin locations as waypoints."""
        self.get_logger().info('Patrol action started')
        self.state = RobotState.PATROLLING

        result = Patrol.Result()
        start_time = self.get_clock().now()
        new_points_recorded = 0
        distance_traveled = 0.0

        try:
            waypoint_data = load_waypoint_file(self.waypoint_file)
            patrol_waypoints = waypoint_data.get("waypoints") or []
            if not patrol_waypoints:
                raise ValueError(f"patrol waypoint file has no waypoints: {self.waypoint_file}")
            if not goal_handle.request.use_saved_map:
                self.state = RobotState.LEARNING
                self.learn_count += 1
                self.get_logger().info(
                    f'Learning proof accepted from {self.waypoint_file}: '
                    f'{len(patrol_waypoints)} waypoint(s)'
                )
        except Exception as exc:
            result.success = False
            result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
            result.new_points_recorded = 0
            result.map_save_path = self.waypoint_file
            goal_handle.abort()
            self.state = RobotState.ERROR
            if goal_handle.request.use_saved_map:
                self.get_logger().error(f'Patrol failed before navigation: {exc}')
            else:
                self.get_logger().error(f'Patrol learning proof missing or invalid: {exc}')
            return result

        self.state = RobotState.PATROLLING
        waypoints_total = len(patrol_waypoints)
        for i, waypoint in enumerate(patrol_waypoints):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.state = RobotState.IDLE
                result.success = False
                result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
                self.get_logger().info('Patrol canceled')
                return result

            waypoint_name = waypoint.get("name") or f"waypoint_{i}"
            self.get_logger().info(f'Patrol navigating to waypoint {i + 1}/{waypoints_total}: {waypoint_name}')
            feedback_msg = Patrol.Feedback()
            feedback_msg.waypoints_visited = i
            feedback_msg.waypoints_total = waypoints_total
            feedback_msg.distance_traveled = distance_traveled
            feedback_msg.current_waypoint = self._waypoint_msg_from_data(waypoint)
            goal_handle.publish_feedback(feedback_msg)

            nav_result = self._navigate_patrol_waypoint(waypoint, goal_handle)
            distance_traveled += max(0.0, nav_result.elapsed_sec)
            if not nav_result.success:
                result.success = False
                result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
                result.new_points_recorded = new_points_recorded
                result.map_save_path = self.waypoint_file
                if nav_result.result_code == "canceled":
                    goal_handle.canceled()
                    self.state = RobotState.IDLE
                else:
                    goal_handle.abort()
                    self.state = RobotState.ERROR
                self.get_logger().error(f'Patrol failed at {waypoint_name}: {nav_result.message}')
                return result

            feedback_msg = Patrol.Feedback()
            feedback_msg.waypoints_visited = i + 1
            feedback_msg.waypoints_total = waypoints_total
            feedback_msg.distance_traveled = distance_traveled
            feedback_msg.current_waypoint = self._waypoint_msg_from_data(waypoint)
            goal_handle.publish_feedback(feedback_msg)

        result.map_save_path = self.waypoint_file
        result.success = True
        result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
        result.new_points_recorded = new_points_recorded

        goal_handle.succeed()
        self.state = RobotState.IDLE
        self.get_logger().info(
            f'Patrol complete: {result.total_duration_sec:.1f}s, '
            f'{result.new_points_recorded} new points recorded')
        return result

    def _waypoint_msg_from_data(self, waypoint_data):
        waypoint = Waypoint()
        waypoint.name = str(waypoint_data.get("name") or "")
        waypoint.type = int(waypoint_data.get("type", 0) or 0)
        waypoint.visited = bool(waypoint_data.get("visited", False))
        waypoint.last_visit_time = float(waypoint_data.get("last_visit_time", 0.0) or 0.0)
        waypoint.comment = str(waypoint_data.get("comment") or "")
        waypoint.pose = self._pose_stamped_from_data(
            {
                "frame_id": waypoint_data.get("frame_id") or "map",
                "x": float(waypoint_data.get("x") or 0.0),
                "y": float(waypoint_data.get("y") or 0.0),
                "z": float(waypoint_data.get("z") or 0.0),
                "qx": float(waypoint_data.get("orientation_x") or waypoint_data.get("qx") or 0.0),
                "qy": float(waypoint_data.get("orientation_y") or waypoint_data.get("qy") or 0.0),
                "qz": float(waypoint_data.get("orientation_z") or waypoint_data.get("qz") or 0.0),
                "qw": float(waypoint_data.get("orientation_w") or waypoint_data.get("qw") or 1.0),
            }
        )
        return waypoint

    def _navigate_patrol_waypoint(self, waypoint_data, goal_handle):
        started = time.monotonic()
        pose = self._waypoint_msg_from_data(waypoint_data).pose
        navigator = self._get_navigator()
        navigator.goToPose(pose)
        while not navigator.isTaskComplete():
            if goal_handle.is_cancel_requested:
                navigator.cancelTask()
                return NavigationResult(False, "canceled", "patrol navigation canceled", time.monotonic() - started)
            if time.monotonic() - started > self.navigation_timeout_sec:
                navigator.cancelTask()
                return NavigationResult(False, "timeout", "patrol navigation timed out", time.monotonic() - started)
        if self._nav_task_succeeded(navigator):
            waypoint_name = waypoint_data.get("name") or "unnamed waypoint"
            return NavigationResult(True, "succeeded", f"reached patrol waypoint {waypoint_name}", time.monotonic() - started)
        waypoint_name = waypoint_data.get("name") or "unnamed waypoint"
        return NavigationResult(False, "failed", f"failed to reach patrol waypoint {waypoint_name}", time.monotonic() - started)

    async def _execute_collection(self, goal_handle):
        """TrashCollection action for the user-loaded trash delivery MVP."""
        requested_target = (goal_handle.request.trash_goal_frame or self.delivery_target).strip()
        self.get_logger().info(f'Collection action: delivery target={requested_target}')
        self.state = RobotState.LOADED

        machine = DeliveryStateMachine()
        result = TrashCollection.Result()
        start_time = self.get_clock().now()
        task_id = f"delivery-{int(time.time())}"
        nav_attempts = 0
        nav_results = []
        dropoff_result = {}
        elevator_assist = self._elevator_assist_disabled_status()
        task_source = "software_proof"
        record_config = {
            "delivery_mode": self.delivery_mode,
            "navigation_timeout_sec": self.navigation_timeout_sec,
            "navigation_retry_limit": self.navigation_retry_limit,
            "dropoff_mode": self.dropoff_mode,
            "dropoff_timeout_sec": self.dropoff_timeout_sec,
            "fixed_route_status_file": self.fixed_route_status_file,
            "waypoint_file": self.waypoint_file,
            "elevator_assist_enabled": self.elevator_assist_enabled,
            "elevator_assist_mode": self.elevator_assist_mode,
            "elevator_assist_target_floor": self.elevator_assist_target_floor,
            "elevator_assist_dry_run_failure": self.elevator_assist_dry_run_failure,
            "elevator_assist_evidence_file": self.elevator_assist_evidence_file,
        }

        try:
            machine.confirm_loaded(requested_target)
            if machine.error_message:
                raise ValueError(machine.error_message)
            self._publish_collection_feedback(
                goal_handle, machine, start_time, 0, 10.0, "loaded", "load confirmed"
            )

            if goal_handle.is_cancel_requested:
                return self._cancel_collection(
                    goal_handle,
                    result,
                    machine,
                    start_time,
                    task_id,
                    elevator_assist=elevator_assist,
                )

            machine.start_delivery()
            if machine.error_message:
                raise RuntimeError(machine.error_message)
            self.state = RobotState.DELIVERING
            self._publish_collection_feedback(
                goal_handle, machine, start_time, 1, 25.0, "delivering", "delivery started"
            )

            nav_attempts, nav_results, nav_result = self._navigate_delivery_target(
                requested_target, goal_handle
            )
            if goal_handle.is_cancel_requested:
                return self._cancel_collection(
                    goal_handle,
                    result,
                    machine,
                    start_time,
                    task_id,
                    nav_attempts,
                    nav_results,
                    dropoff_result,
                    elevator_assist,
                )
            if not nav_result.success:
                if nav_result.result_code == "timeout":
                    machine.timed_out(nav_result.message, "NAV_TIMEOUT")
                else:
                    machine.navigation_failed(nav_result.message, "NAV_FAIL")
                raise RuntimeError(machine.error_message)

            elevator_assist = self._perform_elevator_assist(machine)
            if not elevator_assist["success"]:
                machine.elevator_failed(elevator_assist["reason"])
                raise RuntimeError(machine.error_message)

            machine.navigation_succeeded()
            self.state = RobotState.DROPOFF
            self._publish_collection_feedback(
                goal_handle,
                machine,
                start_time,
                3,
                60.0,
                "dropoff",
                nav_result.message,
                arrived=True,
            )

            dropoff_result = self._perform_dropoff(goal_handle, task_id)
            if goal_handle.is_cancel_requested:
                return self._cancel_collection(
                    goal_handle,
                    result,
                    machine,
                    start_time,
                    task_id,
                    nav_attempts,
                    nav_results,
                    dropoff_result,
                    elevator_assist,
                )
            if not dropoff_result["success"]:
                if dropoff_result.get("result_code") == "manual_confirm_timeout":
                    machine.timed_out(dropoff_result["message"])
                else:
                    machine.dropoff_failed(dropoff_result["message"])
                raise RuntimeError(machine.error_message)

            machine.dropoff_confirmed()
            self.state = RobotState.RETURNING
            self._publish_collection_feedback(
                goal_handle,
                machine,
                start_time,
                3,
                80.0,
                "returning",
                dropoff_result["message"],
                arrived=True,
                collected=True,
                delivered=True,
            )

            if self.return_target:
                return_attempts, return_results, return_result = self._navigate_return_target(goal_handle)
                nav_attempts += return_attempts
                nav_results.extend(return_results)
                if goal_handle.is_cancel_requested:
                    return self._cancel_collection(
                        goal_handle,
                        result,
                        machine,
                        start_time,
                        task_id,
                        nav_attempts,
                        nav_results,
                        dropoff_result,
                        elevator_assist,
                    )
                if not return_result.success:
                    if return_result.result_code == "timeout":
                        machine.timed_out(return_result.message, "NAV_TIMEOUT")
                    else:
                        machine.return_failed(return_result.message)
                    raise RuntimeError(machine.error_message)

            machine.return_succeeded()

            self.collection_count += 1
            result.success = True
            result.items_collected = 1
            result.items_disposed = 1
            result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
            result.error_code = ""
            result.final_state = machine.state.value
            result.task_record_path = str(
                self._write_collection_record(
                    task_id,
                    machine,
                    "success",
                    "",
                    requested_target,
                    nav_attempts,
                    nav_results,
                    dropoff_result,
                    elevator_assist,
                    record_config,
                    source=task_source,
                )
            )

            self._publish_collection_feedback(
                goal_handle,
                machine,
                start_time,
                4,
                100.0,
                "done",
                "collection complete",
                arrived=True,
                collected=True,
                delivered=True,
            )
            goal_handle.succeed()
            self.state = RobotState.IDLE

            self.get_logger().info(
                f'Collection complete in {result.total_duration_sec:.1f}s, '
                f'total collections: {self.collection_count}, record={result.task_record_path}')

        except Exception as e:
            if not machine.error_message:
                if machine.state.value == "delivering":
                    machine.navigation_failed(str(e))
                elif machine.state.value == "dropoff":
                    machine.dropoff_failed(str(e))
                elif machine.state.value == "returning":
                    machine.return_failed(str(e))
            result.success = False
            result.error_code = machine.events[-1].event.value if machine.events else "failed"
            result.error_message = machine.error_message or str(e)
            result.final_state = machine.state.value
            result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
            result.task_record_path = str(
                self._write_collection_record(
                    task_id,
                    machine,
                    "failed",
                    result.error_message,
                    requested_target,
                    nav_attempts,
                    nav_results,
                    dropoff_result,
                    elevator_assist,
                    record_config,
                    source=task_source,
                )
            )
            self._publish_collection_feedback(
                goal_handle,
                machine,
                start_time,
                0,
                0.0,
                "failed",
                result.error_message,
            )
            goal_handle.abort()
            self.state = RobotState.ERROR
            self.get_logger().error(f'Collection failed: {e}, record={result.task_record_path}')
        finally:
            self._clear_collection_active()
        return result

    def _collection_goal_callback(self, goal_request):
        """Allow one behavior collection at a time across local and remote gateways."""
        del goal_request
        with self.collection_lock:
            if self.collection_active:
                self.get_logger().warn("Rejecting collection goal because another collection is active")
                return GoalResponse.REJECT
            self.collection_active = True
        return GoalResponse.ACCEPT

    def _clear_collection_active(self):
        with self.collection_lock:
            self.collection_active = False

    def _publish_collection_feedback(
        self,
        goal_handle,
        machine,
        start_time,
        status,
        percent_complete,
        current_step,
        message,
        *,
        arrived=False,
        collected=False,
        delivered=False,
    ):
        feedback = TrashCollection.Feedback()
        feedback.arrived = arrived
        feedback.collected = collected
        feedback.delivered = delivered
        feedback.status = status
        feedback.percent_complete = float(percent_complete)
        feedback.current_step = current_step
        feedback.state = machine.state.value
        feedback.event = machine.events[-1].event.value if machine.events else ""
        feedback.message = message
        feedback.elapsed_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
        goal_handle.publish_feedback(feedback)

    def _write_collection_record(
        self,
        task_id,
        machine,
        final_status,
        error_message,
        target,
        nav_attempts,
        nav_results,
        dropoff_result,
        elevator_assist,
        config,
        *,
        source="software_proof",
    ):
        failure_code = "" if final_status == "success" else self._derive_failure_code(machine)
        result_path = self._derive_elevator_assist_ref(elevator_assist) or self._derive_result_path(nav_results)
        evidence_ref = self._derive_elevator_assist_ref(elevator_assist) or self._derive_evidence_ref(nav_results) or result_path
        human_intervention_required = bool(
            failure_code in ("NAV_FAIL", "NAV_TIMEOUT", "TASK_CANCEL")
            or (dropoff_result or {}).get("result_code") in ("manual_confirm_timeout", "unsupported_dropoff_mode")
            or (elevator_assist or {}).get("requires_human_help")
        )
        return write_task_record(
            self.task_record_dir,
            task_id,
            machine,
            final_status,
            error_message,
            delivery_mode=self.delivery_mode,
            target=target,
            return_target=self.return_target,
            nav_attempts=nav_attempts,
            nav_results=[asdict(item) if isinstance(item, NavigationResult) else item for item in nav_results],
            dropoff_result=dropoff_result,
            elevator_assist=elevator_assist,
            detection_snapshot_refs=[],
            config=config,
            error_code="" if final_status == "success" else (
                machine.events[-1].event.value if machine.events else ""
            ),
            final_state=machine.state.value,
            source=source,
            result_path=result_path,
            evidence_ref=evidence_ref,
            failure_code=failure_code,
            human_intervention_required=human_intervention_required,
        )

    def _cancel_collection(
        self,
        goal_handle,
        result,
        machine,
        start_time,
        task_id,
        nav_attempts=0,
        nav_results=None,
        dropoff_result=None,
        elevator_assist=None,
    ):
        if elevator_assist is None:
            elevator_assist = self._elevator_assist_disabled_status()
        machine.cancel("user canceled", "TASK_CANCEL")
        goal_handle.canceled()
        self.state = RobotState.IDLE
        result.success = False
        result.error_code = "canceled"
        result.error_message = "user canceled"
        result.final_state = machine.state.value
        result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
        result.task_record_path = str(
            self._write_collection_record(
                task_id,
                machine,
                "canceled",
                result.error_message,
                machine.target,
                nav_attempts,
                nav_results or [],
                dropoff_result or {},
                elevator_assist,
                {
                    "delivery_mode": self.delivery_mode,
                    "navigation_timeout_sec": self.navigation_timeout_sec,
                    "navigation_retry_limit": self.navigation_retry_limit,
                    "dropoff_mode": self.dropoff_mode,
                    "dropoff_timeout_sec": self.dropoff_timeout_sec,
                    "fixed_route_status_file": self.fixed_route_status_file,
                    "waypoint_file": self.waypoint_file,
                    "elevator_assist_enabled": self.elevator_assist_enabled,
                    "elevator_assist_mode": self.elevator_assist_mode,
                    "elevator_assist_target_floor": self.elevator_assist_target_floor,
                    "elevator_assist_dry_run_failure": self.elevator_assist_dry_run_failure,
                    "elevator_assist_evidence_file": self.elevator_assist_evidence_file,
                },
                source="software_proof",
            )
        )
        self._clear_collection_active()
        return result

    def _derive_result_path(self, nav_results):
        return self._derive_evidence_ref(nav_results)

    def _derive_evidence_ref(self, nav_results):
        for item in nav_results or []:
            evidence = item.evidence if isinstance(item, NavigationResult) else item.get("evidence", {})
            if not isinstance(evidence, dict):
                continue
            candidate = evidence.get("evidence_ref")
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
            route_progress = evidence.get("route_progress")
            if isinstance(route_progress, dict):
                for key in ("evidence_ref", "route_file"):
                    candidate = route_progress.get(key)
                    if isinstance(candidate, str) and candidate.strip():
                        return candidate.strip()
            # status/replay 证据缺少 evidence_ref 时才退回文件路径。
            # 这样可以防止 fixed_route_status_file 抢占 route_progress 的 run 级锚点。
            for key in ("fixed_route_status_file", "route_file"):
                candidate = evidence.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
        return ""

    def _derive_elevator_assist_ref(self, elevator_assist):
        if not isinstance(elevator_assist, dict):
            return ""
        # rehearsal artifact 的 evidence_ref 是本轮同证据链锚点。
        # 它只作为 software_proof 记录引用，不代表真实电梯或 HIL 成功。
        for key in ("evidence_ref", "result_path"):
            candidate = elevator_assist.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        return ""

    def _derive_failure_code(self, machine):
        if getattr(machine, "failure_code", ""):
            return str(machine.failure_code)
        if not machine.events:
            return ""
        event = machine.events[-1].event.value
        if event == "canceled":
            return "TASK_CANCEL"
        if event == "timed_out":
            return "NAV_TIMEOUT"
        if event in ("navigation_failed", "return_failed"):
            return "NAV_FAIL"
        return event

    def _navigate_delivery_target(self, target_name: str, goal_handle):
        if self.delivery_mode not in ("dry_run", "waypoint", "fixed_route"):
            raise ValueError(f"Unsupported delivery_mode: {self.delivery_mode}")
        return self._navigate_with_retries(target_name, goal_handle, self.delivery_mode)

    def _navigate_return_target(self, goal_handle):
        mode = "waypoint" if self.delivery_mode == "waypoint" else "dry_run"
        return self._navigate_with_retries(self.return_target, goal_handle, mode)

    def _navigate_with_retries(self, target_name: str, goal_handle, mode: str):
        attempts = []
        for attempt in range(max(0, self.navigation_retry_limit) + 1):
            try:
                if mode == "dry_run":
                    nav_result = NavigationResult(True, "dry_run", f"dry-run reached {target_name}", 0.0)
                elif mode == "fixed_route":
                    nav_result = self._navigate_fixed_route_status(target_name, goal_handle)
                else:
                    nav_result = self._navigate_to_waypoint_target(target_name, goal_handle)
            except Exception as exc:
                nav_result = NavigationResult(False, "exception", str(exc), 0.0)
            attempts.append(nav_result)
            if nav_result.success or goal_handle.is_cancel_requested:
                break
            self.get_logger().warn(
                f'Navigation attempt {attempt + 1} failed: '
                f'{nav_result.result_code} {nav_result.message}'
            )
        return len(attempts), attempts, attempts[-1]

    def _navigate_fixed_route_status(self, target_name: str, goal_handle):
        start = time.monotonic()
        status_path = os.path.expanduser(self.fixed_route_status_file)

        while time.monotonic() - start <= self.navigation_timeout_sec:
            if goal_handle.is_cancel_requested:
                return NavigationResult(False, "canceled", "navigation canceled", time.monotonic() - start)
            if not os.path.exists(status_path):
                time.sleep(0.1)
                continue
            try:
                with open(status_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                return NavigationResult(
                    False,
                    "status_file_error",
                    str(exc),
                    time.monotonic() - start,
                    self._fixed_route_status_evidence(status_path),
                )
            evidence = self._fixed_route_status_evidence(status_path, payload)
            status = str(payload.get("status", "")).lower()
            state = str(payload.get("state", "")).lower()
            if payload.get("success") is True or status in ("success", "succeeded", "completed") or state in ("success", "succeeded", "completed"):
                return NavigationResult(
                    True,
                    "fixed_route_completed",
                    "fixed_route completed",
                    time.monotonic() - start,
                    evidence,
                )
            if payload.get("success") is False or status in ("failed", "error") or state in ("failed", "error"):
                message = (
                    payload.get("message")
                    or payload.get("failure_reason")
                    or payload.get("last_error")
                    or "fixed_route failed"
                )
                return NavigationResult(
                    False,
                    "fixed_route_failed",
                    message,
                    time.monotonic() - start,
                    evidence,
                )
            time.sleep(0.1)
        return NavigationResult(
            False,
            "timeout",
            f"fixed_route status file did not report completion: {status_path}",
            time.monotonic() - start,
            self._fixed_route_status_evidence(status_path),
        )

    def _fixed_route_status_evidence(self, status_path, payload=None):
        evidence = {"fixed_route_status_file": status_path}
        if not isinstance(payload, dict):
            return evidence
        for key in (
            "state",
            "status",
            "success",
            "mode",
            "route_contract_version",
            "source",
            "route_file",
            "route_id",
            "route_file_basename",
            "keyframe_dir",
            "checkpoint",
            "checkpoint_id",
            "current_index",
            "target",
            "current_target",
            "total",
            "total_checkpoints",
            "evidence_ref",
            "failure_code",
            "route_progress",
            "dry_run",
            "enable_visual_gate",
            "keyframe_preflight",
            "visual_gate_status",
            "visual_gate_detail",
            "visual_gate_checkpoint",
            "last_error",
            "failure_reason",
            "message",
            "last_transition",
            "last_nav_result",
            "updated_at",
        ):
            if key in payload:
                evidence[key] = payload[key]
        route_progress = payload.get("route_progress")
        if isinstance(route_progress, dict) and route_progress:
            evidence["route_progress"] = dict(route_progress)
            for key in FIXED_ROUTE_PROGRESS_FIELDS:
                value = route_progress.get(key)
                existing = evidence.get(key)
                if (key not in evidence or existing is None or existing == "") and value is not None:
                    # 空字符串不能遮蔽 route_progress 里的有效字段。
                    # 这只补齐软件证据追踪，不把 fixed-route 状态升级为 HIL 或真实送达。
                    evidence[key] = value
        else:
            progress = {
                key: payload[key]
                for key in FIXED_ROUTE_PROGRESS_FIELDS
                if key in payload
            }
            if progress:
                evidence["route_progress"] = progress
        return evidence

    def _perform_dropoff(self, goal_handle, task_id):
        start = time.monotonic()
        if self.dropoff_mode == "dry_run":
            return {
                "success": True,
                "result_code": "dry_run",
                "message": "dropoff confirmed by dry-run mode",
                "source": "dry_run",
                "elapsed_sec": 0.0,
            }
        if self.dropoff_mode != "manual_confirm":
            return {
                "success": False,
                "result_code": "unsupported_dropoff_mode",
                "message": f"Unsupported dropoff_mode: {self.dropoff_mode}",
                "source": "software_proof",
                "elapsed_sec": 0.0,
            }
        self.dropoff_gate.begin(task_id)
        try:
            return self.dropoff_gate.wait(
                self.dropoff_timeout_sec,
                lambda: bool(goal_handle.is_cancel_requested),
            )
        finally:
            self.dropoff_gate.clear()

    def _elevator_assist_disabled_status(self):
        status = {
            "enabled": False,
            "mode": getattr(self, "elevator_assist_mode", ""),
            "state": "disabled",
            "phase": "disabled",
            "requires_human_help": False,
            "reason": "disabled_by_operator",
            "warning": "elevator assist default mainline was explicitly disabled by operator config",
            "target_floor": "",
            "speaker_prompt": "",
            "evidence": {},
            "events": [],
            "success": True,
        }
        # 显式关闭仍允许非跨楼层 dry-run 继续，但必须把恢复建议和证据边界写进记录。
        return self._with_elevator_assist_boundary(
            status,
            phone_copy=(
                "电梯辅助流程已被操作员关闭；本次记录只证明软件 dry-run 可继续，"
                "不证明真实电梯、真实喇叭、真实 Nav2、HIL 或送达成功。"
            ),
        )

    def _with_elevator_assist_boundary(self, payload, *, phone_copy):
        payload.update(
            {
                "proof_gate": payload.get("proof_gate") or ELEVATOR_ASSIST_PROOF_GATE,
                "evidence_boundary": payload.get("evidence_boundary") or ELEVATOR_ASSIST_PROOF_GATE,
                "boundary": ELEVATOR_ASSIST_BOUNDARY,
                "not_proven": list(ELEVATOR_ASSIST_NOT_PROVEN),
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_phone_copy": phone_copy,
                "rerun_guidance": ELEVATOR_ASSIST_RERUN_GUIDANCE,
            }
        )
        # 这些字段面向 mobile/diagnostics 消费方，防止把 software proof 误渲染成真实送达。
        return payload

    def _perform_elevator_assist(self, machine):
        if not self.elevator_assist_enabled:
            return self._elevator_assist_disabled_status()
        if self.elevator_assist_mode != "dry_run":
            return self._with_elevator_assist_boundary({
                "enabled": True,
                "mode": self.elevator_assist_mode,
                "state": "failed",
                "phase": "unsupported_mode",
                "requires_human_help": True,
                "reason": f"Unsupported elevator_assist_mode: {self.elevator_assist_mode}",
                "failure_reason": f"Unsupported elevator_assist_mode: {self.elevator_assist_mode}",
                "manual_takeover_reason": "unsupported_elevator_assist_mode",
                "target_floor": self.elevator_assist_target_floor,
                "speaker_prompt": ELEVATOR_ASSIST_PROMPT,
                "evidence": {},
                "events": [],
                "success": False,
            }, phone_copy="电梯辅助模式不是 dry_run，已保持失败关闭；不证明真实电梯、真实喇叭、真实 Nav2、HIL 或送达成功。")

        artifact_status = self._perform_rehearsal_artifact_elevator_assist(machine)
        if artifact_status is not None:
            return artifact_status

        events = []
        evidence = {}
        failure = ELEVATOR_ASSIST_FAILURES.get(self.elevator_assist_dry_run_failure)
        for phase in ELEVATOR_ASSIST_DRY_RUN_PHASES:
            evidence_key = ELEVATOR_ASSIST_DRY_RUN_EVIDENCE[phase]
            event = {
                "phase": phase,
                "state": phase,
                "evidence": evidence_key,
                "requires_human_help": phase in (
                    "requesting_floor_help",
                    "waiting_target_floor",
                ),
                "speaker_prompt": ELEVATOR_ASSIST_PROMPT
                if phase == "requesting_floor_help"
                else "",
            }
            events.append(event)
            evidence[phase] = evidence_key
            machine.elevator_phase(phase, json.dumps(event, ensure_ascii=False, sort_keys=True))
            if failure and failure["phase"] == phase:
                return self._with_elevator_assist_boundary({
                    "enabled": True,
                    "mode": "dry_run",
                    "state": "failed",
                    "phase": phase,
                    "requires_human_help": True,
                    "reason": failure["reason"],
                    "failure_reason": failure["reason"],
                    "manual_takeover_reason": failure["evidence"],
                    "target_floor": self.elevator_assist_target_floor,
                    "speaker_prompt": ELEVATOR_ASSIST_PROMPT,
                    "evidence": {**evidence, "failure": failure["evidence"]},
                    "events": events,
                    "success": False,
                }, phone_copy="电梯辅助 dry-run 需要人工接管；不证明真实电梯、真实喇叭、真实 Nav2、HIL 或送达成功。")

        machine.elevator_completed("elevator assist dry-run complete; resume delivery")
        return self._with_elevator_assist_boundary({
            "enabled": True,
            "mode": "dry_run",
            "state": "resume_delivery",
            "phase": "resume_delivery",
            "requires_human_help": False,
            "reason": "elevator assist dry-run complete",
            "failure_reason": "",
            "manual_takeover_reason": "",
            "target_floor": self.elevator_assist_target_floor,
            "speaker_prompt": ELEVATOR_ASSIST_PROMPT,
            "evidence": evidence,
            "events": events,
            "success": True,
        }, phone_copy="电梯辅助 dry-run 已走完默认软件主链路；不证明真实电梯、真实喇叭、真实 Nav2、HIL 或送达成功。")

    def _perform_rehearsal_artifact_elevator_assist(self, machine):
        artifact_path = str(getattr(self, "elevator_assist_evidence_file", "") or "").strip()
        if not artifact_path:
            return None
        if not os.path.exists(artifact_path):
            # 缺失或空文件按计划保持旧 dry-run fallback，方便 Docker 本地先跑通主链路。
            return None
        try:
            if os.path.getsize(artifact_path) == 0:
                # 缺失或空文件按计划保持旧 dry-run fallback，方便 Docker 本地先跑通主链路。
                return None
        except OSError as exc:
            return self._rehearsal_artifact_failed_status(
                machine,
                f"invalid elevator rehearsal evidence file: {exc}",
                "invalid_rehearsal_evidence_file",
            )
        try:
            with open(artifact_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            return self._rehearsal_artifact_failed_status(
                machine,
                f"invalid elevator rehearsal evidence file: {exc}",
                "invalid_rehearsal_evidence_file",
            )

        validation_error = self._validate_rehearsal_artifact(payload)
        if validation_error:
            return self._rehearsal_artifact_failed_status(
                machine,
                validation_error,
                "invalid_rehearsal_evidence_artifact",
                payload if isinstance(payload, dict) else {},
            )

        phase_evidence = payload["phase_evidence"]
        events = []
        evidence = {}
        for phase in ELEVATOR_ASSIST_REHEARSAL_REQUIRED_PHASES:
            phase_payload = phase_evidence[phase]
            event = {
                "phase": phase,
                "state": phase,
                "evidence": phase_payload,
                "requires_human_help": phase in (
                    "requesting_floor_help",
                    "waiting_target_floor",
                ),
                "speaker_prompt": ELEVATOR_ASSIST_PROMPT
                if phase == "requesting_floor_help"
                else "",
            }
            events.append(event)
            evidence[phase] = phase_payload
            # machine 只记录可回放摘要，artifact 原文仍保存在文件侧，避免 state transition 膨胀。
            machine.elevator_phase(phase, json.dumps(event, ensure_ascii=False, sort_keys=True))

        failure = payload.get("failure")
        if isinstance(failure, dict) and failure:
            phase = str(failure.get("phase") or "").strip() or events[-1]["phase"]
            reason = str(failure.get("reason") or "elevator rehearsal evidence requested manual takeover")
            manual_reason = str(failure.get("manual_takeover_reason") or reason)
            return self._with_elevator_assist_boundary({
                "enabled": True,
                "mode": "dry_run",
                "state": "failed",
                "phase": phase,
                "requires_human_help": True,
                "reason": reason,
                "failure_reason": reason,
                "manual_takeover_reason": manual_reason,
                "target_floor": str(payload.get("target_floor") or self.elevator_assist_target_floor),
                "speaker_prompt": ELEVATOR_ASSIST_PROMPT,
                "evidence": {**evidence, "failure": failure},
                "events": events,
                "success": False,
                "schema": ELEVATOR_ASSIST_REHEARSAL_SCHEMA,
                "source": "software_proof",
                "evidence_ref": payload["evidence_ref"],
                "result_path": payload["evidence_ref"],
                "proof_gate": ELEVATOR_ASSIST_REHEARSAL_PROOF_GATE,
                "evidence_boundary": ELEVATOR_ASSIST_REHEARSAL_PROOF_GATE,
                "same_evidence_ref_required": True,
            }, phone_copy="电梯演练 artifact 要求人工接管，行为主链路已失败关闭；不证明真实电梯、真实喇叭、真实 Nav2、HIL 或送达成功。")

        machine.elevator_completed("elevator assist rehearsal artifact complete; resume delivery")
        return self._with_elevator_assist_boundary({
            "enabled": True,
            "mode": "dry_run",
            "state": "resume_delivery",
            "phase": "resume_delivery",
            "requires_human_help": False,
            "reason": "elevator rehearsal evidence artifact accepted",
            "failure_reason": "",
            "manual_takeover_reason": "",
            "target_floor": str(payload.get("target_floor") or self.elevator_assist_target_floor),
            "speaker_prompt": ELEVATOR_ASSIST_PROMPT,
            "evidence": evidence,
            "events": events,
            "success": True,
            "schema": ELEVATOR_ASSIST_REHEARSAL_SCHEMA,
            "source": "software_proof",
            "evidence_ref": payload["evidence_ref"],
            "result_path": payload["evidence_ref"],
            "proof_gate": ELEVATOR_ASSIST_REHEARSAL_PROOF_GATE,
            "evidence_boundary": ELEVATOR_ASSIST_REHEARSAL_PROOF_GATE,
            "same_evidence_ref_required": True,
        }, phone_copy="电梯演练 artifact 已驱动 dry-run 主链路；不证明真实电梯、真实喇叭、真实 Nav2、HIL 或送达成功。")

    def _validate_rehearsal_artifact(self, payload):
        if not isinstance(payload, dict):
            return "elevator rehearsal evidence artifact must be a JSON object"
        if payload.get("schema") != ELEVATOR_ASSIST_REHEARSAL_SCHEMA:
            return "elevator rehearsal evidence artifact schema mismatch"
        if payload.get("evidence_boundary") != ELEVATOR_ASSIST_REHEARSAL_PROOF_GATE:
            return "elevator rehearsal evidence artifact boundary mismatch"
        if payload.get("source") != "software_proof":
            return "elevator rehearsal evidence artifact source must be software_proof"
        if payload.get("delivery_success") is not False:
            return "elevator rehearsal evidence artifact must keep delivery_success=false"
        if payload.get("primary_actions_enabled") is not False:
            return "elevator rehearsal evidence artifact must keep primary_actions_enabled=false"
        if payload.get("same_evidence_ref_required") is not True:
            return "elevator rehearsal evidence artifact must keep same_evidence_ref_required=true"
        evidence_ref = payload.get("evidence_ref")
        if not self._is_safe_elevator_evidence_ref(evidence_ref):
            return "elevator rehearsal evidence artifact evidence_ref must be a non-empty safe string"
        phase_evidence = payload.get("phase_evidence")
        if not isinstance(phase_evidence, dict):
            return "elevator rehearsal evidence artifact phase_evidence must be an object"
        for phase in ELEVATOR_ASSIST_REHEARSAL_REQUIRED_PHASES:
            if phase not in phase_evidence:
                return f"elevator rehearsal evidence artifact missing phase_evidence.{phase}"
        not_proven = payload.get("not_proven")
        normalized = {
            str(item).strip().lower().replace(" ", "_")
            for item in not_proven
        } if isinstance(not_proven, list) else set()
        for required in ELEVATOR_ASSIST_REHEARSAL_REQUIRED_NOT_PROVEN:
            if required not in normalized:
                return f"elevator rehearsal evidence artifact not_proven missing {required}"
        return ""

    def _is_safe_elevator_evidence_ref(self, value):
        if not isinstance(value, str):
            return False
        value = value.strip()
        # 与 Task A artifact 生成器保持同一安全 token 语义：
        # 允许 run id 中的 ":"，但不允许路径分隔符、空白或凭证类字符进入 task_record 顶层。
        return ELEVATOR_ASSIST_REHEARSAL_EVIDENCE_REF_RE.fullmatch(value) is not None

    def _rehearsal_artifact_failed_status(self, machine, reason, manual_takeover_reason, payload=None):
        machine.elevator_phase(
            "elevator_rehearsal_evidence_validation",
            json.dumps({"reason": reason}, ensure_ascii=False, sort_keys=True),
        )
        evidence_ref = ""
        if isinstance(payload, dict) and self._is_safe_elevator_evidence_ref(payload.get("evidence_ref")):
            evidence_ref = payload["evidence_ref"].strip()
        return self._with_elevator_assist_boundary({
            "enabled": True,
            "mode": "dry_run",
            "state": "failed",
            "phase": "elevator_rehearsal_evidence_validation",
            "requires_human_help": True,
            "reason": reason,
            "failure_reason": reason,
            "manual_takeover_reason": manual_takeover_reason,
            "target_floor": self.elevator_assist_target_floor,
            "speaker_prompt": ELEVATOR_ASSIST_PROMPT,
            "evidence": {},
            "events": [],
            "success": False,
            "schema": ELEVATOR_ASSIST_REHEARSAL_SCHEMA,
            "source": "software_proof",
            "evidence_ref": evidence_ref,
            "result_path": evidence_ref,
            "proof_gate": ELEVATOR_ASSIST_REHEARSAL_PROOF_GATE,
            "evidence_boundary": ELEVATOR_ASSIST_REHEARSAL_PROOF_GATE,
            "same_evidence_ref_required": True,
        }, phone_copy="电梯演练 artifact 未通过校验，行为主链路已失败关闭；不证明真实电梯、真实喇叭、真实 Nav2、HIL 或送达成功。")

    def _confirm_dropoff_callback(self, request, response):
        accepted, message = self.dropoff_gate.confirm(
            bool(request.data),
            "/trashbot/confirm_dropoff",
            "dropoff confirmed" if request.data else "dropoff rejected",
        )
        response.success = accepted
        response.message = message
        return response

    def _navigate_to_waypoint_target(self, target_name: str, goal_handle) -> NavigationResult:
        started = time.monotonic()
        waypoint_data = load_waypoint_file(self.waypoint_file)
        pose_data = find_waypoint_pose(waypoint_data, target_name)
        pose = self._pose_stamped_from_data(pose_data)
        navigator = self._get_navigator()
        self.get_logger().info(
            f'Navigating to waypoint "{pose_data["name"]}" '
            f'({pose.pose.position.x:.2f}, {pose.pose.position.y:.2f})')
        navigator.goToPose(pose)
        while not navigator.isTaskComplete():
            if goal_handle.is_cancel_requested:
                navigator.cancelTask()
                return NavigationResult(False, "canceled", "navigation canceled", time.monotonic() - started)
            if time.monotonic() - started > self.navigation_timeout_sec:
                navigator.cancelTask()
                return NavigationResult(False, "timeout", "navigation timed out", time.monotonic() - started)
        if self._nav_task_succeeded(navigator):
            return NavigationResult(True, "succeeded", f"reached waypoint {pose_data['name']}", time.monotonic() - started)
        return NavigationResult(False, "failed", f"failed to reach waypoint {pose_data['name']}", time.monotonic() - started)

    def _pose_stamped_from_data(self, pose_data):
        from geometry_msgs.msg import PoseStamped

        pose = PoseStamped()
        pose.header.frame_id = pose_data["frame_id"]
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = pose_data["x"]
        pose.pose.position.y = pose_data["y"]
        pose.pose.position.z = pose_data["z"]
        pose.pose.orientation.x = pose_data["qx"]
        pose.pose.orientation.y = pose_data["qy"]
        pose.pose.orientation.z = pose_data["qz"]
        pose.pose.orientation.w = pose_data["qw"]
        return pose

    def _get_navigator(self):
        if self.navigator is None:
            from nav2_simple_commander.robot_navigator import BasicNavigator

            self.navigator = BasicNavigator()
        return self.navigator

    def _nav_task_succeeded(self, navigator) -> bool:
        from nav2_simple_commander.robot_navigator import TaskResult

        return navigator.getResult() == TaskResult.SUCCEEDED

    def _cancel_callback(self, goal_handle):
        """Accept cancel requests."""
        self.get_logger().info('Cancel requested')
        return CancelResponse.ACCEPT

    async def _sleep_async(self, seconds: float):
        """Non-blocking sleep for ROS2 async callback."""
        from asyncio import sleep
        await sleep(seconds)


def main(args=None):
    rclpy.init(args=args)
    node = TaskOrchestrator()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
