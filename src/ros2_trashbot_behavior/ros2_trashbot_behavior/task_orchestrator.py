import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from ros2_trashbot_interfaces.action import TrashCollection, Patrol
from ros2_trashbot_interfaces.msg import TrashStatus, WaypointList
from ros2_trashbot_interfaces.srv import RecordWaypoint

from enum import Enum


class RobotState(Enum):
    IDLE = 0
    LEARNING = 1
    PATROLLING = 2
    COLLECTING = 3
    DELIVERING = 4
    RETURNING = 5
    ERROR = 6


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

        # Services
        self.record_wp_client = self.create_client(
            RecordWaypoint, '/trashbot/record_waypoint')

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
                feedback_msg.new_points_recorded += len(self.trash_items)
                self.get_logger().info(f'  Recorded {len(self.trash_items)} new trash points')

        # Phase 3: Save map
        result.map_save_path = '~/.ros/trashbot_maps/trashbot_map.yaml'
        result.success = True
        result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
        result.new_points_recorded = feedback_msg.new_points_recorded

        goal_handle.succeed()
        self.state = RobotState.IDLE
        self.get_logger().info(
            f'Patrol complete: {result.total_duration_sec:.1f}s, '
            f'{result.new_points_recorded} new points recorded')
        return result

    async def _execute_collection(self, goal_handle):
        """TrashCollection action: navigate to trash → pick up → deliver to bin."""
        self.get_logger().info(f'Collection action: goal frame={goal_handle.request.trash_goal_frame}')
        self.state = RobotState.COLLECTING

        feedback = TrashCollection.Feedback()
        result = TrashCollection.Result()
        start_time = self.get_clock().now()

        try:
            # Step 1: Navigate to trash location
            self.get_logger().info('Step 1: Navigating to trash')
            feedback.status = 1  # navigating
            goal_handle.publish_feedback(feedback)

            # TODO: send goal to nav_to_goal node
            await self._sleep_async(3.0)
            feedback.arrived = True
            goal_handle.publish_feedback(feedback)

            # Step 2: Collect trash (manipulator action)
            self.get_logger().info('Step 2: Collecting trash')
            feedback.status = 2  # collecting

            # TODO: trigger manipulator/gripper
            await self._sleep_async(2.0)
            feedback.collected = True
            result.items_collected = 1
            goal_handle.publish_feedback(feedback)

            # Step 3: Navigate to nearest bin
            self.get_logger().info('Step 3: Delivering to trash bin')
            feedback.status = 3  # delivering

            # TODO: find nearest bin, navigate to it
            await self._sleep_async(3.0)

            # Step 4: Drop trash
            self.get_logger().info('Step 4: Dropping trash')
            feedback.delivered = True
            feedback.status = 4  # done
            result.items_disposed = 1
            goal_handle.publish_feedback(feedback)

            self.collection_count += 1
            result.success = True
            result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9

            goal_handle.succeed()
            self.state = RobotState.IDLE

            self.get_logger().info(
                f'Collection complete in {result.total_duration_sec:.1f}s, '
                f'total collections: {self.collection_count}')

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.total_duration_sec = (self.get_clock().now() - start_time).nanoseconds / 1e9
            goal_handle.abort()
            self.state = RobotState.ERROR
            self.get_logger().error(f'Collection failed: {e}')

        return result

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
