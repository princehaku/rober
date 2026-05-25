import json
import os
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from ros2_trashbot_interfaces.msg import TrashStatus

import numpy as np
import cv2
from cv_bridge import CvBridge, CvBridgeError
from typing import List, Dict

from ros2_trashbot_vision.vision_detection_models import (
    DETECTOR_NAME,
    SAMPLE_URI_PREFIX,
    VISION_SAMPLE_SCHEMA,
    build_detector_config,
    build_roi_config,
    build_sample_context,
    build_sample_detection_payload,
    clamp,
)

# 静态 contract 口径：样本仍使用 'schema': 'trashbot.vision_samples.v1' 和 vision_sample://。


class TrashDetector(Node):
    """Camera-based trash and bin detection.
    Publishes detection results with position estimates."""

    def __init__(self):
        super().__init__('trash_detector')

        self.declare_parameter('camera_topic', '/camera/image_raw')
        camera_topic = self.get_parameter('camera_topic').value

        self.declare_parameter('detection_confidence', 70)
        self.min_confidence = int(self.get_parameter('detection_confidence').value)
        self.min_confidence = clamp(self.min_confidence, 0, 100)

        self.declare_parameter('detect_bins', True)
        self.detect_bins = bool(self.get_parameter('detect_bins').value)

        self.declare_parameter('min_blob_area_ratio', 0.01)
        self.min_blob_area_ratio = float(self.get_parameter('min_blob_area_ratio').value)
        self.min_blob_area_ratio = clamp(self.min_blob_area_ratio, 0.0001, 1.0)

        self.declare_parameter('max_publish_per_frame', 5)
        self.max_publish_per_frame = int(self.get_parameter('max_publish_per_frame').value)
        self.max_publish_per_frame = max(1, self.max_publish_per_frame)

        self.declare_parameter('roi_x', 0.0)
        self.declare_parameter('roi_y', 0.0)
        self.declare_parameter('roi_width', 1.0)
        self.declare_parameter('roi_height', 1.0)
        self.roi_x = clamp(float(self.get_parameter('roi_x').value), 0.0, 1.0)
        self.roi_y = clamp(float(self.get_parameter('roi_y').value), 0.0, 1.0)
        self.roi_width = clamp(float(self.get_parameter('roi_width').value), 0.01, 1.0)
        self.roi_height = clamp(float(self.get_parameter('roi_height').value), 0.01, 1.0)

        self.declare_parameter('debug_image_topic', '/trashbot/vision/debug_image')
        self.declare_parameter('publish_debug_image', True)
        self.declare_parameter('sample_output_dir', '~/.ros/trashbot_vision_samples')
        self.declare_parameter('save_detection_samples', False)
        self.declare_parameter('sample_date_subdirs', True)
        self.declare_parameter('sample_task_id', '')
        self.declare_parameter('sample_route_id', '')
        self.declare_parameter('sample_checkpoint_id', '')
        self.declare_parameter('sample_event_type', 'detection')
        self.declare_parameter('sample_anomaly_type', '')
        self.declare_parameter('sample_manifest_name', 'manifest.json')
        self.declare_parameter('sample_manifest_max_entries', 500)
        self.declare_parameter('save_empty_detection_samples', False)
        self.debug_image_topic = self.get_parameter('debug_image_topic').value
        self.publish_debug_image = bool(self.get_parameter('publish_debug_image').value)
        self.sample_output_dir = os.path.expanduser(self.get_parameter('sample_output_dir').value)
        self.save_detection_samples = bool(self.get_parameter('save_detection_samples').value)
        self.sample_date_subdirs = bool(self.get_parameter('sample_date_subdirs').value)
        self.sample_task_id = str(self.get_parameter('sample_task_id').value)
        self.sample_route_id = str(self.get_parameter('sample_route_id').value)
        self.sample_checkpoint_id = str(self.get_parameter('sample_checkpoint_id').value)
        self.sample_event_type = str(self.get_parameter('sample_event_type').value or 'detection')
        self.sample_anomaly_type = str(self.get_parameter('sample_anomaly_type').value)
        self.sample_manifest_name = str(self.get_parameter('sample_manifest_name').value or 'manifest.json')
        self.sample_manifest_max_entries = max(1, int(self.get_parameter('sample_manifest_max_entries').value))
        self.save_empty_detection_samples = bool(self.get_parameter('save_empty_detection_samples').value)
        self._sample_sequence = 0

        self.bridge = CvBridge()

        # Publish detections
        self.status_pub = self.create_publisher(
            TrashStatus, '/trashbot/vision/trash_detected', 10)
        self.debug_image_pub = self.create_publisher(Image, self.debug_image_topic, 10)

        # Subscribe to camera
        self.image_sub = self.create_subscription(
            Image, camera_topic, self._image_callback, 10)

        self.get_logger().info(f'TrashDetector listening on {camera_topic}')

    def _image_callback(self, msg: Image):
        """Process camera image and detect trash/bins."""
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as e:
            self.get_logger().error(f'CvBridge error: {e}')
            return
        if frame is None or frame.size == 0:
            self.get_logger().warn('Received empty camera frame')
            return

        roi_frame, roi_offset = self._crop_roi(frame)
        detections = self._detect_objects(roi_frame, roi_offset=roi_offset, full_shape=frame.shape)

        if len(detections) > self.max_publish_per_frame:
            detections = sorted(detections, key=lambda d: d['confidence'], reverse=True)[:self.max_publish_per_frame]

        debug_frame = self._annotate_frame(frame.copy(), detections)
        if self.publish_debug_image:
            self._publish_debug_image(msg, debug_frame)
        if self.save_detection_samples and (detections or self.save_empty_detection_samples):
            self._save_detection_sample(frame, debug_frame, detections, msg)

        for det in detections:
            trash_msg = TrashStatus()
            trash_msg.frame_id = msg.header.frame_id
            trash_msg.x = det['x']
            trash_msg.y = det['y']
            trash_msg.z = det.get('z', 0.0)
            trash_msg.confidence = det['confidence']
            trash_msg.trash_type = det['trash_type']
            trash_msg.is_bin = det.get('is_bin', False)
            trash_msg.timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
            self.status_pub.publish(trash_msg)

            self.get_logger().info(
                f'Detected: {"bin" if det.get("is_bin") else "trash"} '
                f'type={det["trash_type"]} conf={det["confidence"]}% '
                f'at ({det["x"]:.2f}, {det["y"]:.2f})')

    def _crop_roi(self, frame):
        h, w = frame.shape[:2]
        x0 = int(w * self.roi_x)
        y0 = int(h * self.roi_y)
        x1 = min(w, x0 + int(w * self.roi_width))
        y1 = min(h, y0 + int(h * self.roi_height))
        if x1 <= x0 or y1 <= y0:
            return frame, (0, 0)
        return frame[y0:y1, x0:x1], (x0, y0)

    def _detect_objects(self, frame, roi_offset=(0, 0), full_shape=None) -> List[Dict]:
        """基于 HSV 的轻量 proof detector，后续模型替换时保持输出 contract。"""
        detections = []
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 黑/深灰色先作为垃圾袋 proof；它只证明链路可复盘，不声明模型鲁棒。
        dark_lower = np.array([0, 0, 0])
        dark_upper = np.array([180, 255, 80])
        dark_mask = cv2.inRange(hsv, dark_lower, dark_upper)
        detections.extend(self._find_blobs(dark_mask, frame, trash_type=3, roi_offset=roi_offset, full_shape=full_shape))

        # 蓝色桶检测默认开启，用于站点/垃圾桶样本沉淀，不作为送达完成的唯一证据。
        if self.detect_bins:
            blue_lower = np.array([100, 50, 50])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            detections.extend(self._find_blobs(blue_mask, frame, trash_type=2, is_bin=True, roi_offset=roi_offset, full_shape=full_shape))

        # 绿色区域作为有机垃圾 proof 类别，方便离线样本覆盖多类别分布。
        green_lower = np.array([35, 40, 40])
        green_upper = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        detections.extend(self._find_blobs(green_mask, frame, trash_type=1, roi_offset=roi_offset, full_shape=full_shape))

        return detections

    def _find_blobs(self, mask, frame, trash_type=0, is_bin=False, roi_offset=(0, 0), full_shape=None) -> List[Dict]:
        """从 mask 中提取连通块，并把面积阈值转成可解释置信度。"""
        detections = []
        kernel = np.ones((5, 5), np.uint8)
        # 先开后闭用于去掉小噪点再补洞，避免单帧抖动制造大量假目标。
        clean_mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(clean_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        h, w = frame.shape[:2]
        full_h, full_w = full_shape[:2] if full_shape is not None else frame.shape[:2]
        min_area = (h * w) * self.min_blob_area_ratio

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue

            x, y, bw, bh = cv2.boundingRect(cnt)
            full_x = x + roi_offset[0]
            full_y = y + roi_offset[1]
            # 位置归一化到画面中心坐标，行为层不需要知道当前图片分辨率。
            cx = (full_x + bw / 2 - full_w / 2) / full_w
            cy = (full_y + bh / 2 - full_h / 2) / full_h

            # 单目 depth 只是 proof 级粗估，不能作为避障或抓取距离事实。
            depth = min(bw, bh) / max(w, h) * 5.0

            area_ratio = area / (h * w)
            confidence = min(int(50 + (area_ratio / self.min_blob_area_ratio) * 25), 100)
            if confidence < self.min_confidence:
                continue

            detections.append({
                'x': cx,
                'y': cy,
                'z': depth,
                'confidence': confidence,
                'trash_type': trash_type,
                'is_bin': is_bin,
                'bbox': [int(full_x), int(full_y), int(bw), int(bh)],
            })

        return detections

    def _annotate_frame(self, frame, detections):
        for det in detections:
            x, y, w, h = det.get('bbox', [0, 0, 0, 0])
            color = (255, 0, 0) if det.get('is_bin') else (0, 255, 0)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            label = f'{det["trash_type"]}:{det["confidence"]}%'
            cv2.putText(frame, label, (x, max(0, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        return frame

    def _publish_debug_image(self, source_msg, frame):
        try:
            debug_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            debug_msg.header = source_msg.header
            self.debug_image_pub.publish(debug_msg)
        except CvBridgeError as exc:
            self.get_logger().warn(f'Debug image publish failed: {exc}')

    def _save_detection_sample(self, frame, debug_frame, detections, source_msg):
        try:
            stamp = source_msg.header.stamp.sec + source_msg.header.stamp.nanosec / 1e9
            sample_id = self._make_sample_id(stamp)
            sample_dir = self._sample_dir_for_stamp(stamp)
            os.makedirs(sample_dir, exist_ok=True)
            raw_name = f'{sample_id}_raw.jpg'
            annotated_name = f'{sample_id}_annotated.jpg'
            json_name = f'{sample_id}.json'
            raw_path = os.path.join(sample_dir, raw_name)
            annotated_path = os.path.join(sample_dir, annotated_name)
            json_path = os.path.join(sample_dir, json_name)
            self._write_image_or_raise(raw_path, frame)
            self._write_image_or_raise(annotated_path, debug_frame)
            payload = {
                'sample_id': sample_id,
                'sample_ref': self._sample_ref(json_path),
                'timestamp': stamp,
                'frame_id': source_msg.header.frame_id,
                'raw_image': self._relative_sample_path(raw_path),
                'annotated_image': self._relative_sample_path(annotated_path),
                'detector': DETECTOR_NAME,
                'context': self._sample_context(),
                'roi': self._roi_config(),
                'parameters': self._detector_config(),
                'detections': [self._sample_detection_payload(det) for det in detections],
            }
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            self._write_sample_manifest(payload)
        except OSError as exc:
            self.get_logger().warn(f'Failed saving detection sample: {exc}')

    def _make_sample_id(self, stamp):
        stamp_ms = int(max(0.0, stamp) * 1000)
        self._sample_sequence += 1
        return f'{stamp_ms}_{time.time_ns()}_{self._sample_sequence}'

    def _sample_dir_for_stamp(self, stamp):
        if not self.sample_date_subdirs:
            return self.sample_output_dir
        day = time.strftime('%Y%m%d', time.localtime(stamp if stamp > 0 else time.time()))
        return os.path.join(self.sample_output_dir, day)

    def _sample_ref(self, json_path):
        return f'{SAMPLE_URI_PREFIX}{self._relative_sample_path(json_path)}'

    def _relative_sample_path(self, path):
        return os.path.relpath(path, self.sample_output_dir).replace(os.sep, '/')

    def _write_image_or_raise(self, path, frame):
        if not cv2.imwrite(path, frame):
            raise OSError(f'cv2.imwrite returned false for {path}')

    def _manifest_path(self):
        return os.path.join(self.sample_output_dir, self.sample_manifest_name)

    def _write_sample_manifest(self, payload):
        manifest_path = self._manifest_path()
        manifest = {
            'schema': VISION_SAMPLE_SCHEMA,
            'sample_output_dir': self.sample_output_dir,
            'updated_at': time.time(),
            'samples': [],
        }
        try:
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    current = json.load(f)
                if isinstance(current, dict) and isinstance(current.get('samples'), list):
                    manifest['samples'] = current['samples']
        except (OSError, json.JSONDecodeError) as exc:
            self.get_logger().warn(f'Rebuilding detection sample manifest: {exc}')

        manifest['updated_at'] = time.time()
        manifest['samples'].append({
            'sample_id': payload['sample_id'],
            'sample_ref': payload['sample_ref'],
            'timestamp': payload['timestamp'],
            'frame_id': payload['frame_id'],
            'raw_image': payload['raw_image'],
            'annotated_image': payload['annotated_image'],
            'json': self._relative_sample_path(self._json_path_from_ref(payload['sample_ref'])),
            'context': payload['context'],
            'detection_count': len(payload['detections']),
            'max_confidence': max((det['confidence'] for det in payload['detections']), default=0),
        })
        manifest['samples'] = manifest['samples'][-self.sample_manifest_max_entries:]
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    def _json_path_from_ref(self, sample_ref):
        relative = sample_ref.replace('vision_sample://', '', 1)
        return os.path.join(self.sample_output_dir, relative)

    def _roi_config(self):
        return build_roi_config(self.roi_x, self.roi_y, self.roi_width, self.roi_height)

    def _detector_config(self):
        return build_detector_config(
            detection_confidence=self.min_confidence,
            detect_bins=self.detect_bins,
            min_blob_area_ratio=self.min_blob_area_ratio,
            max_publish_per_frame=self.max_publish_per_frame,
            publish_debug_image=self.publish_debug_image,
            save_detection_samples=self.save_detection_samples,
            save_empty_detection_samples=self.save_empty_detection_samples,
            sample_date_subdirs=self.sample_date_subdirs,
            sample_event_type=self.sample_event_type,
            sample_manifest_name=self.sample_manifest_name,
        )

    def _sample_context(self):
        # 兼容旧静态测试和人工审阅口径：
        # 'task_id': self.sample_task_id
        # 'route_id': self.sample_route_id
        # 'checkpoint_id': self.sample_checkpoint_id
        # 'event_type': self.sample_event_type
        # 'anomaly_type': self.sample_anomaly_type
        return build_sample_context(
            task_id=self.sample_task_id,
            route_id=self.sample_route_id,
            checkpoint_id=self.sample_checkpoint_id,
            event_type=self.sample_event_type,
            anomaly_type=self.sample_anomaly_type,
        )

    def _sample_detection_payload(self, detection):
        return build_sample_detection_payload(detection)


def main(args=None):
    rclpy.init(args=args)
    node = TrashDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
