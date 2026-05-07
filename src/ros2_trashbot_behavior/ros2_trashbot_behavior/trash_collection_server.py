import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from geometry_msgs.msg import Twist
from ros2_trashbot_interfaces.action import TrashCollection


class TrashCollectionServer(Node):
    """Standalone trash collection action server.
    Handles the full pipeline: nav → collect → deliver."""

    def __init__(self):
        super().__init__('trash_collection_server')

        # Cmd vel publisher for base movement
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Action server
        self.action_server = ActionServer(
            self, TrashCollection, '/trashbot/collect_trash',
            self._execute_callback)

        self.get_logger().info('TrashCollectionServer ready')

    async def _execute_callback(self, goal_handle):
        """Execute the full trash collection sequence."""
        feedback = TrashCollection.Feedback()
        result = TrashCollection.Result()

        self.get_logger().info(f'Executing collection for frame: {goal_handle.request.trash_goal_frame}')

        # Step 1: Navigate to trash
        feedback.status = 1
        self.get_logger().info('  -> Navigating to trash location')
        await self._navigate_to_trash(goal_handle.request.trash_goal_frame)
        feedback.arrived = True
        goal_handle.publish_feedback(feedback)

        # Step 2: Collect
        feedback.status = 2
        self.get_logger().info('  -> Collecting trash')
        await self._collect_trash()
        feedback.collected = True
        result.items_collected = 1
        goal_handle.publish_feedback(feedback)

        # Step 3: Deliver to bin
        feedback.status = 3
        self.get_logger().info('  -> Delivering to bin')
        await self._deliver_to_bin()
        feedback.delivered = True
        result.items_disposed = 1
        goal_handle.publish_feedback(feedback)

        feedback.status = 4
        result.success = True
        goal_handle.succeed()

        self.get_logger().info('Collection successful')
        return result

    async def _navigate_to_trash(self, target_frame: str):
        """Navigate to the trash location."""
        # TODO: integrate with Nav2
        # Send goal to /navigate_to_pose action
        await self._sleep(3.0)

    async def _collect_trash(self):
        """Activate manipulator to collect trash."""
        # TODO: trigger manipulator/gripper
        await self._sleep(2.0)

    async def _deliver_to_bin(self):
        """Navigate to nearest bin and drop."""
        # TODO: query bin locations, navigate to nearest, drop
        await self._sleep(3.0)

    async def _sleep(self, seconds: float):
        import asyncio
        await asyncio.sleep(seconds)


def main(args=None):
    rclpy.init(args=args)
    node = TrashCollectionServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
