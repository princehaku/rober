import os
import csv
import json
import yaml
from typing import List, Dict

import cv2
from cv_bridge import CvBridge, CvBridgeError
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped


class FixedRouteAutonomy(Node):
    """Route runner for neighborhood fixed-path trash collection.

    Uses prerecorded route waypoints and optional camera keyframe matching.
    """

    def __init__(self):
        super().__init__('fixed_route_autonomy')
        self.declare_parameter('route_file', '~/.ros/trashbot_maps/fixed_route.yaml')
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('enable_visual_gate', True)
        self.declare_parameter('visual_match_threshold', 25)
        self.declare_parameter('keyframe_dir', '~/.ros/trashbot_maps/keyframes')
        self.declare_parameter('dry_run', False)
        self.declare_parameter('debug_status_file', '/tmp/trashbot_fixed_route_status.json')

        self.route_file = os.path.expanduser(self.get_parameter('route_file').value)
        self.camera_topic = self.get_parameter('camera_topic').value
        self.enable_visual_gate = bool(self.get_parameter('enable_visual_gate').value)
        self.visual_match_threshold = int(self.get_parameter('visual_match_threshold').value)
        self.keyframe_dir = os.path.expanduser(self.get_parameter('keyframe_dir').value)
        self.dry_run = bool(self.get_parameter('dry_run').value)
        self.debug_status_file = self.get_parameter('debug_status_file').value

        self.bridge = CvBridge()
        self.navigator = None if self.dry_run else BasicNavigator()
        self.orb = cv2.ORB_create(600)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.latest_frame = None
        self.current_index = 0
        self.route_poses = self._load_route(self.route_file)
        self.keyframes = self._load_keyframes(len(self.route_poses))

        self.create_subscription(Image, self.camera_topic, self._on_image, 10)
        self.runner_timer = self.create_timer(0.5, self._run_route)
        self.busy = False
        self.task_in_progress = False

        self.get_logger().info(
            f'FixedRouteAutonomy loaded {len(self.route_poses)} poses from {self.route_file}, dry_run={self.dry_run}')
        self._write_debug_status('ready')

    def _load_route(self, path: str) -> List[PoseStamped]:
        if not os.path.exists(path):
            self.get_logger().error(f'Route file not found: {path}')
            return []
        if path.endswith('.csv'):
            return self._load_route_csv(path)
        return self._load_route_yaml(path)

    def _load_route_yaml(self, path: str) -> List[PoseStamped]:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        return [self._row_to_pose(item) for item in data.get('waypoints', [])]

    def _load_route_csv(self, path: str) -> List[PoseStamped]:
        poses = []
        with open(path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                poses.append(self._row_to_pose(row))
        return poses

    def _row_to_pose(self, row: Dict) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = row.get('frame_id', 'map')
        pose.pose.position.x = float(row.get('x', 0.0))
        pose.pose.position.y = float(row.get('y', 0.0))
        pose.pose.position.z = float(row.get('z', 0.0))
        pose.pose.orientation.x = float(row.get('qx', 0.0))
        pose.pose.orientation.y = float(row.get('qy', 0.0))
        pose.pose.orientation.z = float(row.get('qz', 0.0))
        pose.pose.orientation.w = float(row.get('qw', 1.0))
        return pose

    def _load_keyframes(self, count: int):
        keyframes = {}
        for idx in range(count):
            keyframe_path = os.path.join(self.keyframe_dir, f'{idx:03d}.jpg')
            if not os.path.exists(keyframe_path):
                continue
            img = cv2.imread(keyframe_path)
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            kp, des = self.orb.detectAndCompute(gray, None)
            if des is not None and len(kp) > 0:
                keyframes[idx] = des
        return keyframes

    def _on_image(self, msg: Image):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as exc:
            self.get_logger().warn(f'image convert failed: {exc}')

    def _visual_gate_pass(self, idx: int) -> bool:
        if not self.enable_visual_gate:
            return True
        if idx not in self.keyframes or self.latest_frame is None:
            return False
        gray = cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2GRAY)
        _, live_des = self.orb.detectAndCompute(gray, None)
        if live_des is None:
            return False
        matches = self.matcher.match(self.keyframes[idx], live_des)
        return len(matches) >= self.visual_match_threshold

    def _run_route(self):
        if self.current_index >= len(self.route_poses):
            self._write_debug_status('completed')
            return
        if self.task_in_progress:
            self._poll_nav_result()
            return
        if self.busy:
            return
        if not self._visual_gate_pass(self.current_index):
            self._write_debug_status('waiting_visual_gate')
            return
        self.busy = True
        self._write_debug_status('running')
        if self.dry_run:
            self.current_index += 1
            self.get_logger().info(f'[DRY_RUN] checkpoint passed -> next {self.current_index}')
        else:
            target = self.route_poses[self.current_index]
            target.header.stamp = self.get_clock().now().to_msg()
            self.get_logger().info(f'Navigate to checkpoint #{self.current_index}')
            self.navigator.goToPose(target)
            self.task_in_progress = True
        state = 'completed' if self.current_index >= len(self.route_poses) else 'ready'
        self._write_debug_status(state)
        self.busy = False

    def _poll_nav_result(self):
        if not self.navigator.isTaskComplete():
            return
        result = self.navigator.getResult()
        if result == 0:
            self.current_index += 1
            self.get_logger().info(f'checkpoint reached -> next {self.current_index}')
        else:
            self.get_logger().warn(f'checkpoint {self.current_index} failed, retrying')
        self.task_in_progress = False
        state = 'completed' if self.current_index >= len(self.route_poses) else 'ready'
        self._write_debug_status(state)

    def _write_debug_status(self, state: str):
        payload = {
            'state': state,
            'route_file': self.route_file,
            'keyframe_dir': self.keyframe_dir,
            'current_index': self.current_index,
            'total': len(self.route_poses),
            'dry_run': self.dry_run,
            'enable_visual_gate': self.enable_visual_gate,
        }
        try:
            with open(self.debug_status_file, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            self.get_logger().warn(f'Failed writing debug status: {exc}')


def main(args=None):
    rclpy.init(args=args)
    node = FixedRouteAutonomy()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
