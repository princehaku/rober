import csv
import json
import os
import time
from math import hypot

# cv_bridge 在现场 Orange Pi 镜像里可能缺失；这里必须把它做成可选依赖，避免节点在订阅 /odom 前崩溃。
try:
    from cv_bridge import CvBridge, CvBridgeError
except ImportError:
    CvBridge = None
    CvBridgeError = Exception

# OpenCV 仍用于写 keyframe；若运行环境缺失，route.csv 仍应继续记录，不能因为图片链路拖垮路线链路。
try:
    import cv2
except ImportError:
    cv2 = None

# numpy 是 cv_bridge 缺失时解析 sensor_msgs/Image 原始 buffer 的最小依赖，缺失时只记录原因并保持节点存活。
try:
    import numpy as np
except ImportError:
    np = None

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

        # 优先使用 cv_bridge，保证桌面/容器环境和历史 keyframe 输出保持一致。
        self.bridge = CvBridge() if CvBridge is not None else None
        self.latest_frame = None
        self.last_image_conversion_error = ''
        self.last_x = None
        self.last_y = None
        self.index = 0
        self.csv_file = open(self.route_csv, 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.csv_file)
        self.writer.writerow(['index', 'sec', 'nanosec', 'frame_id', 'x', 'y', 'z', 'qx', 'qy', 'qz', 'qw', 'frame'])

        self.create_subscription(Image, self.camera_topic, self._on_image, 10)
        self.create_subscription(Odometry, self.odom_topic, self._on_odom, 50)

        self.get_logger().info(f'Recording route data to {self.output_dir}')
        if self.bridge is None:
            self.get_logger().warn('cv_bridge unavailable; using numpy/cv2 image fallback for common encodings')
        if cv2 is None:
            self._record_image_conversion_failure('cv2 unavailable; keyframe image writing disabled')
        elif np is None and self.bridge is None:
            self._record_image_conversion_failure('numpy unavailable; cv_bridge fallback disabled')

    def _on_image(self, msg: Image):
        frame, failure_reason = convert_image_msg_to_bgr8(msg, bridge=self.bridge)
        if failure_reason:
            # 转换失败时清空旧帧，避免把过期 keyframe 写到新的 odom checkpoint 上。
            self.latest_frame = None
            self._record_image_conversion_failure(failure_reason)
            self.get_logger().warn(f'Image conversion failed: {failure_reason}')
            return
        self.latest_frame = frame

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
            if cv2 is None:
                self._record_image_conversion_failure('cv2 unavailable; keyframe image writing disabled')
            elif not cv2.imwrite(frame_path, self.latest_frame):
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

    def _record_image_conversion_failure(self, reason: str):
        if reason == self.last_image_conversion_error:
            return
        self.last_image_conversion_error = reason
        status_path = os.path.join(self.output_dir, 'image_conversion_status.json')
        payload = {
            'schema': 'trashbot.route_data_recorder.image_conversion.v1',
            'updated_at': time.time(),
            'status': 'degraded',
            'reason': reason,
            'cv_bridge_available': self.bridge is not None,
            'cv2_available': cv2 is not None,
            'numpy_available': np is not None,
        }
        try:
            write_json_file(status_path, payload)
        except OSError as exc:
            self.get_logger().warn(f'Failed writing image conversion status: {exc}')

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


def convert_image_msg_to_bgr8(msg: Image, bridge=None):
    if bridge is not None:
        try:
            return bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8'), ''
        except CvBridgeError as exc:
            # cv_bridge 已安装但当前编码或数据仍失败时，再尝试 raw buffer fallback，避免单帧异常拖垮整条路线采集。
            fallback_frame, fallback_reason = convert_image_msg_to_bgr8_without_cv_bridge(msg)
            if not fallback_reason:
                return fallback_frame, ''
            return None, f'{exc}; fallback={fallback_reason}'
    return convert_image_msg_to_bgr8_without_cv_bridge(msg)


def convert_image_msg_to_bgr8_without_cv_bridge(msg: Image):
    if np is None:
        return None, 'numpy unavailable; cannot convert Image without cv_bridge'
    if cv2 is None:
        return None, 'cv2 unavailable; cannot convert Image without cv_bridge'

    encoding = str(getattr(msg, 'encoding', '') or '').lower()
    converters = {
        'bgr8': (3, None),
        'rgb8': (3, cv2.COLOR_RGB2BGR),
        'mono8': (1, cv2.COLOR_GRAY2BGR),
        'bgra8': (4, cv2.COLOR_BGRA2BGR),
        'rgba8': (4, cv2.COLOR_RGBA2BGR),
    }
    if encoding not in converters:
        return None, f'unsupported image encoding: {encoding or "<empty>"}'

    height = int(getattr(msg, 'height', 0) or 0)
    width = int(getattr(msg, 'width', 0) or 0)
    channels, color_code = converters[encoding]
    minimum_step = width * channels
    step = int(getattr(msg, 'step', 0) or minimum_step)
    if height <= 0 or width <= 0:
        return None, f'invalid image shape: height={height}, width={width}'
    if step < minimum_step:
        return None, f'invalid image step: step={step}, expected_at_least={minimum_step}'

    # sensor_msgs/Image 的每行可能有 padding；先按 step 切行，再只取真实像素区域。
    buffer = np.frombuffer(bytes(getattr(msg, 'data', b'')), dtype=np.uint8)
    required_bytes = height * step
    if buffer.size < required_bytes:
        return None, f'image data too short: bytes={buffer.size}, expected_at_least={required_bytes}'

    rows = buffer[:required_bytes].reshape((height, step))
    pixel_bytes = rows[:, :minimum_step]
    if channels == 1:
        image = pixel_bytes.reshape((height, width))
    else:
        image = pixel_bytes.reshape((height, width, channels))

    # OpenCV 写 jpg 需要 BGR 排列；bgr8 直接 copy，其他常见编码显式转成 BGR，避免颜色通道反转。
    if color_code is None:
        return image.copy(), ''
    return cv2.cvtColor(image, color_code), ''


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

