import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import tf_transformations
from typing import List


class NavToGoal(Node):
    """Simple navigation to a goal pose. Used by behavior system."""

    def __init__(self):
        super().__init__('nav_to_goal')
        self.navigator = BasicNavigator()
        self._nav_done = False
        self._nav_success = False

    def go_to(self, pose: PoseStamped) -> bool:
        """Navigate to a pose synchronously. Returns True on success."""
        self.get_logger().info(f'Navigating to ({pose.pose.position.x:.2f}, {pose.pose.position.y:.2f})')
        self.navigator.goToPose(pose)

        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback:
                self.get_logger().info(f'  Distance remaining: {feedback.remaining_distance:.2f}m')

        result = self.navigator.getResult()
        success = result == 0  # TaskStatus.SUCCEEDED
        self.get_logger().info(f'Navigation {"succeeded" if success else "failed"}')
        return success

    def go_through_poses(self, poses: List[PoseStamped]) -> bool:
        """Follow a sequence of poses."""
        self.navigator.followWaypoints(poses)

        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback:
                self.get_logger().info(f'  On waypoint {feedback.current_waypoint + 1}/{len(poses)}')

        return self.navigator.getResult() == 0


def main(args=None):
    rclpy.init(args=args)
    node = NavToGoal()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
