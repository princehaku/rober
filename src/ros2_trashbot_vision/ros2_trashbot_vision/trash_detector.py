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


class TrashDetector(Node):
    """Camera-based trash and bin detection.
    Publishes detection results with position estimates."""

    def __init__(self):
        super().__init__('trash_detector')

        self.declare_parameter('camera_topic', '/camera/image_raw')
        camera_topic = self.get_parameter('camera_topic').value

        self.declare_parameter('detection_confidence', 70)
        self.min_confidence = int(self.get_parameter('detection_confidence').value)
        self.min_confidence = max(0, min(self.min_confidence, 100))

        self.declare_parameter('detect_bins', True)
        self.detect_bins = bool(self.get_parameter('detect_bins').value)

        self.declare_parameter('min_blob_area_ratio', 0.01)
        self.min_blob_area_ratio = float(self.get_parameter('min_blob_area_ratio').value)
        self.min_blob_area_ratio = max(0.0001, min(self.min_blob_area_ratio, 1.0))

        self.declare_parameter('max_publish_per_frame', 5)
        self.max_publish_per_frame = int(self.get_parameter('max_publish_per_frame').value)
        self.max_publish_per_frame = max(1, self.max_publish_per_frame)

        self.declare_parameter('roi_x', 0.0)
        self.declare_parameter('roi_y', 0.0)
        self.declare_parameter('roi_width', 1.0)
        self.declare_parameter('roi_height', 1.0)
        self.roi_x = max(0.0, min(float(self.get_parameter('roi_x').value), 1.0))
        self.roi_y = max(0.0, min(float(self.get_parameter('roi_y').value), 1.0))
        self.roi_width = max(0.01, min(float(self.get_parameter('roi_width').value), 1.0))
        self.roi_height = max(0.01, min(float(self.get_parameter('roi_height').value), 1.0))

        self.declare_parameter('debug_image_topic', '/trashbot/vision/debug_image')
        self.declare_parameter('sample_output_dir', '~/.ros/trashbot_vision_samples')
        self.declare_parameter('save_detection_samples', False)
        self.debug_image_topic = self.get_parameter('debug_image_topic').value
        self.sample_output_dir = os.path.expanduser(self.get_parameter('sample_output_dir').value)
        self.save_detection_samples = bool(self.get_parameter('save_detection_samples').value)

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
        self._publish_debug_image(msg, debug_frame)
        if self.save_detection_samples and detections:
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
        """Run object detection on the frame.

        Production: replace with YOLO/SSD model.
        Current: color-based heuristic detection as placeholder."""
        detections = []
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Detect common trash bag colors (dark gray/black)
        dark_lower = np.array([0, 0, 0])
        dark_upper = np.array([180, 255, 80])
        dark_mask = cv2.inRange(hsv, dark_lower, dark_upper)
        detections.extend(self._find_blobs(dark_mask, frame, trash_type=3, roi_offset=roi_offset, full_shape=full_shape))

        # Detect blue recycling bins
        if self.detect_bins:
            blue_lower = np.array([100, 50, 50])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            detections.extend(self._find_blobs(blue_mask, frame, trash_type=2, is_bin=True, roi_offset=roi_offset, full_shape=full_shape))

        # Detect green organic waste
        green_lower = np.array([35, 40, 40])
        green_upper = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        detections.extend(self._find_blobs(green_mask, frame, trash_type=1, roi_offset=roi_offset, full_shape=full_shape))

        return detections

    def _find_blobs(self, mask, frame, trash_type=0, is_bin=False, roi_offset=(0, 0), full_shape=None) -> List[Dict]:
        """Find connected blobs in mask and return detections above size threshold."""
        detections = []
        kernel = np.ones((5, 5), np.uint8)
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
            cx = (full_x + bw / 2 - full_w / 2) / full_w  # normalized center
            cy = (full_y + bh / 2 - full_h / 2) / full_h

            # Estimate depth from blob size (simple approximation)
            depth = min(bw, bh) / max(w, h) * 5.0  # crude meters estimate

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
            os.makedirs(self.sample_output_dir, exist_ok=True)
            stamp = source_msg.header.stamp.sec + source_msg.header.stamp.nanosec / 1e9
            sample_id = f'{int(time.time() * 1000)}'
            raw_path = os.path.join(self.sample_output_dir, f'{sample_id}_raw.jpg')
            annotated_path = os.path.join(self.sample_output_dir, f'{sample_id}_annotated.jpg')
            json_path = os.path.join(self.sample_output_dir, f'{sample_id}.json')
            cv2.imwrite(raw_path, frame)
            cv2.imwrite(annotated_path, debug_frame)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        'timestamp': stamp,
                        'frame_id': source_msg.header.frame_id,
                        'raw_image': raw_path,
                        'annotated_image': annotated_path,
                        'detections': detections,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except OSError as exc:
            self.get_logger().warn(f'Failed saving detection sample: {exc}')


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
