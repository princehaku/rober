import copy
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

from ros2_trashbot_interfaces.srv import RecordWaypoint
from ros2_trashbot_interfaces.msg import Waypoint, WaypointList
import yaml
import os
from typing import List, Optional


class WaypointManager(Node):
    """Manages waypoints learned from manual driving or saved maps.
    Provides waypoint recording, loading, and autonomous patrol."""

    def __init__(self):
        super().__init__('waypoint_manager')

        self.declare_parameter('map_storage_path', '~/.ros/trashbot_maps')
        self.map_storage_path = os.path.expanduser(self.get_parameter('map_storage_path').value)
        os.makedirs(self.map_storage_path, exist_ok=True)

        self.declare_parameter('waypoint_file', os.path.join(self.map_storage_path, 'waypoints.yaml'))
        self.waypoint_file = os.path.expanduser(self.get_parameter('waypoint_file').value)
        self.declare_parameter('pose_topic', '/amcl_pose')
        self.pose_topic = self.get_parameter('pose_topic').value
        self.declare_parameter('learn_mode', False)
        self.learn_mode = self.get_parameter('learn_mode').value
        self.declare_parameter('record_interval', 5.0)
        self.record_interval = float(self.get_parameter('record_interval').value)

        # Waypoint storage
        self.waypoints: List[Waypoint] = []
        self.current_map_name = ''
        self.latest_pose: Optional[PoseWithCovarianceStamped] = None
        self._auto_record_count = 0
        self._warned_missing_pose = False

        # Services
        self.record_wp_srv = self.create_service(
            RecordWaypoint, '/trashbot/record_waypoint', self._record_waypoint)

        # Publishers
        self.waypoint_list_pub = self.create_publisher(
            WaypointList, '/trashbot/waypoints', 10)

        # Pose source for recording waypoints. In learn mode this can be
        # remapped to slam_toolbox's pose topic; in autonomous mode AMCL is the default.
        self.pose_sub = self.create_subscription(
            PoseWithCovarianceStamped, self.pose_topic, self._on_pose, 10)
        self.auto_record_timer = None
        if self.learn_mode:
            if self.record_interval > 0.0:
                self.auto_record_timer = self.create_timer(
                    self.record_interval, self._record_learn_mode_waypoint)
            else:
                self.get_logger().warn(
                    f'learn_mode enabled but record_interval={self.record_interval}; automatic recording disabled')

        # Nav2 navigator (for autonomous driving)
        self.navigator = BasicNavigator()

        self._load_waypoints()
        self.get_logger().info(f'WaypointManager ready. Loaded {len(self.waypoints)} waypoints.')

    def _on_pose(self, msg: PoseWithCovarianceStamped):
        """Store the latest localized robot pose for waypoint recording."""
        self.latest_pose = msg

    def _record_waypoint(self, request, response):
        """Record current robot pose as a waypoint."""
        success, message, waypoint_id = self._append_waypoint(
            request.name, request.type, request.comment)
        response.success = success
        response.message = message
        response.waypoint_id = waypoint_id
        return response

    def _record_learn_mode_waypoint(self):
        """Automatically record the latest pose during the learning phase."""
        name = f'auto_{self._auto_record_count:04d}'
        success, message, _ = self._append_waypoint(
            name, 0, 'auto-recorded during learn mode', warn_on_missing_pose=False)
        if success:
            self._auto_record_count += 1
        elif not self._warned_missing_pose:
            self.get_logger().warn(message)
            self._warned_missing_pose = True

    def _append_waypoint(self, name: str, waypoint_type: int, comment: str, warn_on_missing_pose: bool = True):
        """Append the latest robot pose as a waypoint."""
        pose = self._get_current_pose()
        if pose is None:
            message = f'Cannot get current pose from {self.pose_topic}'
            if warn_on_missing_pose:
                self.get_logger().warn(message)
            return False, message, -1

        self._warned_missing_pose = False

        wp = Waypoint()
        wp.name = name
        wp.pose = pose
        wp.type = waypoint_type
        wp.visited = False
        wp.last_visit_time = 0.0
        wp.comment = comment

        self.waypoints.append(wp)
        self._save_waypoints()

        message = f'Recorded waypoint "{name}" at ({pose.pose.position.x:.2f}, {pose.pose.position.y:.2f})'
        waypoint_id = len(self.waypoints) - 1

        self._publish_waypoint_list()
        self.get_logger().info(message)
        return True, message, waypoint_id

    def _get_current_pose(self) -> Optional[PoseStamped]:
        """Get current pose from robot localization."""
        if self.latest_pose is None:
            return None

        pose = PoseStamped()
        pose.header = copy.deepcopy(self.latest_pose.header)
        pose.pose = copy.deepcopy(self.latest_pose.pose.pose)
        return pose

    def _load_waypoints(self):
        """Load waypoints from YAML file."""
        if not os.path.exists(self.waypoint_file):
            self.get_logger().warn(f'No waypoint file at {self.waypoint_file}, starting fresh')
            return

        try:
            with open(self.waypoint_file, 'r') as f:
                data = yaml.safe_load(f)

            if data and 'waypoints' in data:
                for wp_data in data['waypoints']:
                    wp = Waypoint()
                    wp.name = wp_data.get('name', '')
                    wp.type = wp_data.get('type', 0)
                    wp.visited = wp_data.get('visited', False)
                    wp.last_visit_time = wp_data.get('last_visit_time', 0.0)
                    wp.comment = wp_data.get('comment', '')
                    # Pose reconstruction from stored coordinates
                    pose = PoseStamped()
                    pose.header.frame_id = 'map'
                    pose.header.stamp = self.get_clock().now().to_msg()
                    pose.pose.position.x = wp_data.get('x', 0.0)
                    pose.pose.position.y = wp_data.get('y', 0.0)
                    pose.pose.position.z = wp_data.get('z', 0.0)
                    pose.pose.orientation.z = wp_data.get('orientation_z', 0.0)
                    pose.pose.orientation.w = wp_data.get('orientation_w', 1.0)
                    wp.pose = pose
                    self.waypoints.append(wp)

                self.current_map_name = data.get('map_name', '')
                self.get_logger().info(f'Loaded {len(self.waypoints)} waypoints from {self.waypoint_file}')
        except Exception as e:
            self.get_logger().error(f'Failed to load waypoints: {e}')

    def _save_waypoints(self):
        """Save waypoints to YAML file."""
        waypoint_dir = os.path.dirname(self.waypoint_file)
        if waypoint_dir:
            os.makedirs(waypoint_dir, exist_ok=True)
        data = {
            'map_name': self.current_map_name,
            'waypoints': [],
        }
        for wp in self.waypoints:
            data['waypoints'].append({
                'name': wp.name,
                'type': wp.type,
                'x': wp.pose.pose.position.x,
                'y': wp.pose.pose.position.y,
                'z': wp.pose.pose.position.z,
                'orientation_z': wp.pose.pose.orientation.z,
                'orientation_w': wp.pose.pose.orientation.w,
                'visited': wp.visited,
                'last_visit_time': wp.last_visit_time,
                'comment': wp.comment,
            })

        with open(self.waypoint_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    def _publish_waypoint_list(self):
        """Publish current waypoint list."""
        msg = WaypointList()
        msg.map_name = self.current_map_name
        msg.waypoints = self.waypoints
        msg.total_trash_bins = sum(1 for wp in self.waypoints if wp.type == 2)
        msg.total_pickup_points = sum(1 for wp in self.waypoints if wp.type == 1)
        msg.last_updated = self.get_clock().now().nanoseconds / 1e9
        self.waypoint_list_pub.publish(msg)

    def navigate_to_waypoint(self, index: int) -> bool:
        """Navigate to a specific waypoint index."""
        if index < 0 or index >= len(self.waypoints):
            self.get_logger().error(f'Invalid waypoint index: {index}')
            return False

        wp = self.waypoints[index]
        self.get_logger().info(f'Navigating to waypoint "{wp.name}"')

        self.navigator.goToPose(wp.pose)
        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback and (self.get_clock().now().nanoseconds % 1_000_000_000) < 500_000_000:
                self.get_logger().info(f'  Remaining: {feedback.remaining_distance:.2f}m')

        result = self.navigator.getResult()
        success = result == TaskResult.SUCCEEDED
        if success:
            self.waypoints[index].visited = True
            self.waypoints[index].last_visit_time = self.get_clock().now().nanoseconds / 1e9
            self._save_waypoints()
        return success

    def patrol_all(self) -> List[bool]:
        """Navigate to all waypoints in order. Returns list of success flags."""
        results = []
        for i, wp in enumerate(self.waypoints):
            self.get_logger().info(f'Patrol: waypoint {i}/{len(self.waypoints)} - "{wp.name}"')
            success = self.navigate_to_waypoint(i)
            results.append(success)
            if not success:
                self.get_logger().warn(f'Failed to reach waypoint {i}, continuing...')
        return results


def main(args=None):
    rclpy.init(args=args)
    node = WaypointManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
