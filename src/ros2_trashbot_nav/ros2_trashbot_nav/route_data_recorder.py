import csv
import os
from math import hypot

import cv2
from cv_bridge import CvBridge, CvBridgeError
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image


class RouteDataRecorder(Node):
    """Record early manual-driving data for fixed route autonomy."""

    def __init__(self):
        super().__init__('route_data_recorder')
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('output_dir', '~/.ros/trashbot_runs/run_001')
        self.declare_parameter('min_distance_m', 0.8)
        self.declare_parameter('route_frame_id', 'map')

        self.camera_topic = self.get_parameter('camera_topic').value
        self.odom_topic = self.get_parameter('odom_topic').value
        self.output_dir = os.path.expanduser(self.get_parameter('output_dir').value)
        self.min_distance_m = max(0.0, float(self.get_parameter('min_distance_m').value))
        self.route_frame_id = self.get_parameter('route_frame_id').value

        self.keyframe_dir = os.path.join(self.output_dir, 'keyframes')
        os.makedirs(self.keyframe_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        self.route_csv = os.path.join(self.output_dir, 'route.csv')

        self.bridge = CvBridge()
        self.latest_frame = None
        self.last_x = None
        self.last_y = None
        self.index = 0
        self.csv_file = open(self.route_csv, 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.csv_file)
        self.writer.writerow(['index', 'sec', 'nanosec', 'frame_id', 'x', 'y', 'z', 'qx', 'qy', 'qz', 'qw', 'frame'])

        self.create_subscription(Image, self.camera_topic, self._on_image, 10)
        self.create_subscription(Odometry, self.odom_topic, self._on_odom, 50)

        self.get_logger().info(f'Recording route data to {self.output_dir}')

    def _on_image(self, msg: Image):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as exc:
            self.get_logger().warn(f'Image conversion failed: {exc}')

    def _on_odom(self, msg: Odometry):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        if self.last_x is not None:
            if hypot(x - self.last_x, y - self.last_y) < self.min_distance_m:
                return
        frame_name = f'{self.index:03d}.jpg'
        frame_path = os.path.join(self.keyframe_dir, frame_name)
        if self.latest_frame is not None:
            if not cv2.imwrite(frame_path, self.latest_frame):
                self.get_logger().warn(f'Failed writing keyframe: {frame_path}')
        self.writer.writerow([
            self.index,
            msg.header.stamp.sec,
            msg.header.stamp.nanosec,
            self.route_frame_id,
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z,
            msg.pose.pose.orientation.x,
            msg.pose.pose.orientation.y,
            msg.pose.pose.orientation.z,
            msg.pose.pose.orientation.w,
            frame_name,
        ])
        self.csv_file.flush()
        self.last_x, self.last_y = x, y
        self.index += 1
        self.get_logger().info(f'Saved waypoint #{self.index} at ({x:.2f}, {y:.2f})')

    def destroy_node(self):
        try:
            self.csv_file.close()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RouteDataRecorder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

