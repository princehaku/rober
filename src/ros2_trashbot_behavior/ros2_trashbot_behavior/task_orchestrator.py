import json
import os
import threading
import time
from dataclasses import asdict, dataclass
from enum import Enum

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from std_srvs.srv import SetBool

from ros2_trashbot_interfaces.action import TrashCollection, Patrol
from ros2_trashbot_interfaces.msg import TrashStatus, WaypointList
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


class TaskOrchestrator(Node):
    """Main task coordinator. Manages the full lifecycle:
    Phase 1 (Learning): Drive around, build map, record waypoints
    Phase 2 (Autonomous): Patrol → detect trash → collect → deliver → repeat"""

    def __init__(self):
        super().__init__('task_orchestrator')

        # State machine
        self.state = RobotState.IDLE
        self.learn_count = 0
        self.trash_items = []        # detected trash positions
        self.bin_locations = []      # known bin positions
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
        self.trash_sub = self.create_subscription(
            TrashStatus, '/trashbot/vision/trash_detected',
            self._on_trash_detected, 10)

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
            f'trash_items={len(self.trash_items)} '
            f'collections={self.collection_count}')

    def _on_trash_detected(self, msg: TrashStatus):
        """Handle vision detection callback."""
        self.get_logger().info(
            f'Trash detected: type={msg.trash_type} conf={msg.confidence}% '
            f'is_bin={msg.is_bin} pos=({msg.x:.2f}, {msg.y:.2f})')

        if msg.is_bin:
            self.bin_locations.append({
                'x': msg.x, 'y': msg.y, 'z': msg.z,
                'type': msg.trash_type,
            })
        else:
            self.trash_items.append({
                'x': msg.x, 'y': msg.y, 'z': msg.z,
                'type': msg.trash_type,
                'confidence': msg.confidence,
            })

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

        feedback_msg = Patrol.Feedback()
        result = Patrol.Result()
        start_time = self.get_clock().now()
        new_points_recorded = 0

        # Phase 1: If not learning from saved map, do SLAM first
        if not goal_handle.request.use_saved_map:
            self.get_logger().info('No saved map - learning mode, driving to build map')
            self.state = RobotState.LEARNING
            # In real deployment, trigger SLAM here and drive around
            self.learn_count += 1
            self.get_logger().info(f'Learning drive #{self.learn_count} completed')

        # Phase 2: Patrol all waypoints
        # TODO: integrate with waypoint_manager to navigate each point
        # For now, simulate patrol
        waypoints_total = 5  # placeholder
        for i in range(waypoints_total):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.state = RobotState.IDLE
                result.success = False
                result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
                self.get_logger().info('Patrol canceled')
                return result

            feedback_msg.waypoints_visited = i + 1
            feedback_msg.waypoints_total = waypoints_total
            goal_handle.publish_feedback(feedback_msg)

            self.get_logger().info(f'  Visited waypoint {i+1}/{waypoints_total}')
            # Simulate delay for navigation
            await self._sleep_async(2.0)

            # Record new points if in learn mode
            if goal_handle.request.learn_mode and self.trash_items:
                new_points_recorded += len(self.trash_items)
                self.get_logger().info(f'  Recorded {len(self.trash_items)} new trash points')

        # Phase 3: Save map
        result.map_save_path = '~/.ros/trashbot_maps/trashbot_map.yaml'
        result.success = True
        result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
        result.new_points_recorded = new_points_recorded

        goal_handle.succeed()
        self.state = RobotState.IDLE
        self.get_logger().info(
            f'Patrol complete: {result.total_duration_sec:.1f}s, '
            f'{result.new_points_recorded} new points recorded')
        return result

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
        record_config = {
            "delivery_mode": self.delivery_mode,
            "navigation_timeout_sec": self.navigation_timeout_sec,
            "navigation_retry_limit": self.navigation_retry_limit,
            "dropoff_mode": self.dropoff_mode,
            "dropoff_timeout_sec": self.dropoff_timeout_sec,
            "fixed_route_status_file": self.fixed_route_status_file,
            "waypoint_file": self.waypoint_file,
        }

        try:
            machine.confirm_loaded(requested_target)
            if machine.error_message:
                raise ValueError(machine.error_message)
            self._publish_collection_feedback(
                goal_handle, machine, start_time, 0, 10.0, "loaded", "load confirmed"
            )

            if goal_handle.is_cancel_requested:
                return self._cancel_collection(goal_handle, result, machine, start_time, task_id)

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
                    goal_handle, result, machine, start_time, task_id, nav_attempts, nav_results
                )
            if not nav_result.success:
                if nav_result.result_code == "timeout":
                    machine.timed_out(nav_result.message)
                else:
                    machine.navigation_failed(nav_result.message)
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
                )
            if not dropoff_result["success"]:
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
                    )
                if not return_result.success:
                    if return_result.result_code == "timeout":
                        machine.timed_out(return_result.message)
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
                    record_config,
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
                    record_config,
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
        config,
    ):
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
            detection_snapshot_refs=[],
            config=config,
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
    ):
        machine.cancel("user canceled")
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
                {
                    "delivery_mode": self.delivery_mode,
                    "navigation_timeout_sec": self.navigation_timeout_sec,
                    "navigation_retry_limit": self.navigation_retry_limit,
                    "dropoff_mode": self.dropoff_mode,
                    "dropoff_timeout_sec": self.dropoff_timeout_sec,
                    "fixed_route_status_file": self.fixed_route_status_file,
                    "waypoint_file": self.waypoint_file,
                },
            )
        )
        self._clear_collection_active()
        return result

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
                return NavigationResult(False, "status_file_error", str(exc), time.monotonic() - start)
            status = str(payload.get("status", "")).lower()
            state = str(payload.get("state", "")).lower()
            if payload.get("success") is True or status in ("success", "succeeded", "completed") or state in ("success", "succeeded", "completed"):
                return NavigationResult(True, "fixed_route_completed", "fixed_route completed", time.monotonic() - start)
            if payload.get("success") is False or status in ("failed", "error") or state in ("failed", "error"):
                message = (
                    payload.get("message")
                    or payload.get("failure_reason")
                    or payload.get("last_error")
                    or "fixed_route failed"
                )
                return NavigationResult(False, "fixed_route_failed", message, time.monotonic() - start)
            time.sleep(0.1)
        return NavigationResult(
            False,
            "timeout",
            f"fixed_route status file did not report completion: {status_path}",
            time.monotonic() - start,
        )

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
                "source": "task_orchestrator",
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
