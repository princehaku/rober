import csv
import json
import os
import time
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
        self.declare_parameter('route_id', '')
        self.declare_parameter('sample_manifest_name', 'manifest.json')
        self.declare_parameter('sample_manifest_max_entries', 500)

        self.camera_topic = self.get_parameter('camera_topic').value
        self.odom_topic = self.get_parameter('odom_topic').value
        self.output_dir = os.path.expanduser(self.get_parameter('output_dir').value)
        self.min_distance_m = max(0.0, float(self.get_parameter('min_distance_m').value))
        self.route_frame_id = self.get_parameter('route_frame_id').value
        self.route_id = str(self.get_parameter('route_id').value)
        self.sample_manifest_name = str(self.get_parameter('sample_manifest_name').value or 'manifest.json')
        self.sample_manifest_max_entries = max(1, int(self.get_parameter('sample_manifest_max_entries').value))

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
        wrote_keyframe = False
        if self.latest_frame is not None:
            if not cv2.imwrite(frame_path, self.latest_frame):
                self.get_logger().warn(f'Failed writing keyframe: {frame_path}')
            else:
                wrote_keyframe = True
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
        if wrote_keyframe:
            try:
                self._write_route_keyframe_sample(msg, frame_name, frame_path)
            except OSError as exc:
                self.get_logger().warn(f'Failed writing keyframe manifest sample: {exc}')
        self.last_x, self.last_y = x, y
        self.index += 1
        self.get_logger().info(f'Saved waypoint #{self.index} at ({x:.2f}, {y:.2f})')

    def _write_route_keyframe_sample(self, msg: Odometry, frame_name: str, frame_path: str):
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        json_path = os.path.join(self.keyframe_dir, f'{self.index:03d}.json')
        payload = build_route_keyframe_sample_payload(
            sample_id=f'route_keyframe_{self.index:03d}',
            output_dir=self.output_dir,
            json_path=json_path,
            frame_path=frame_path,
            stamp=stamp,
            frame_id=self.route_frame_id,
            route_id=self.route_id,
            checkpoint_id=str(self.index),
            pose={
                'x': msg.pose.pose.position.x,
                'y': msg.pose.pose.position.y,
                'z': msg.pose.pose.position.z,
                'qx': msg.pose.pose.orientation.x,
                'qy': msg.pose.pose.orientation.y,
                'qz': msg.pose.pose.orientation.z,
                'qw': msg.pose.pose.orientation.w,
            },
        )
        write_json_file(json_path, payload)
        append_vision_sample_manifest(
            manifest_path=os.path.join(self.output_dir, self.sample_manifest_name),
            output_dir=self.output_dir,
            entry=route_keyframe_manifest_entry(payload),
            max_entries=self.sample_manifest_max_entries,
        )

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


def relative_sample_path(path: str, output_dir: str) -> str:
    return os.path.relpath(path, output_dir).replace(os.sep, '/')


def sample_ref_for_json(json_path: str, output_dir: str) -> str:
    return f'vision_sample://{relative_sample_path(json_path, output_dir)}'


def build_route_keyframe_sample_payload(
    *,
    sample_id: str,
    output_dir: str,
    json_path: str,
    frame_path: str,
    stamp: float,
    frame_id: str,
    route_id: str,
    checkpoint_id: str,
    pose: dict,
) -> dict:
    return {
        'sample_id': sample_id,
        'sample_ref': sample_ref_for_json(json_path, output_dir),
        'timestamp': stamp,
        'frame_id': frame_id,
        'raw_image': relative_sample_path(frame_path, output_dir),
        'annotated_image': '',
        'detector': 'route_data_recorder',
        'context': {
            'task_id': '',
            'route_id': route_id,
            'checkpoint_id': checkpoint_id,
            'event_type': 'route_keyframe',
            'anomaly_type': '',
        },
        'route_pose': pose,
        'detections': [],
    }


def route_keyframe_manifest_entry(payload: dict) -> dict:
    return {
        'sample_id': payload['sample_id'],
        'sample_ref': payload['sample_ref'],
        'timestamp': payload['timestamp'],
        'frame_id': payload['frame_id'],
        'raw_image': payload['raw_image'],
        'annotated_image': payload['annotated_image'],
        'json': payload['sample_ref'].replace('vision_sample://', '', 1),
        'context': payload['context'],
        'detection_count': 0,
        'max_confidence': 0,
    }


def append_vision_sample_manifest(
    *,
    manifest_path: str,
    output_dir: str,
    entry: dict,
    max_entries: int,
):
    manifest = {
        'schema': 'trashbot.vision_samples.v1',
        'sample_output_dir': output_dir,
        'updated_at': time.time(),
        'samples': [],
    }
    try:
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                current = json.load(f)
            if isinstance(current, dict) and isinstance(current.get('samples'), list):
                manifest['samples'] = current['samples']
    except (OSError, json.JSONDecodeError):
        manifest['samples'] = []

    manifest['updated_at'] = time.time()
    manifest['samples'].append(entry)
    manifest['samples'] = manifest['samples'][-max(1, int(max_entries)):]
    write_json_file(manifest_path, manifest)


def write_json_file(path: str, payload: dict):
    temp_path = f'{path}.tmp'
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)

