import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ros2_trashbot_interfaces.msg import TrashStatus

import numpy as np
import cv2
from cv_bridge import CvBridge, CvBridgeError


class TrashDetector(Node):
    """Camera-based trash and bin detection.
    Publishes detection results with position estimates."""

    def __init__(self):
        super().__init__('trash_detector')

        self.declare_parameter('camera_topic', '/camera/image_raw')
        camera_topic = self.get_parameter('camera_topic').value

        self.declare_parameter('detection_confidence', 70)
        self.min_confidence = self.get_parameter('detection_confidence').value

        self.declare_parameter('detect_bins', True)
        self.detect_bins = self.get_parameter('detect_bins').value

        self.bridge = CvBridge()

        # Publish detections
        self.status_pub = self.create_publisher(
            TrashStatus, '/trashbot/vision/trash_detected', 10)

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

        # Detection pipeline
        detections = self._detect_objects(frame)

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

    def _detect_objects(self, frame) -> list[dict]:
        """Run object detection on the frame.

        Production: replace with YOLO/SSD model.
        Current: color-based heuristic detection as placeholder."""
        detections = []
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Detect common trash bag colors (dark gray/black)
        dark_lower = np.array([0, 0, 0])
        dark_upper = np.array([180, 255, 80])
        dark_mask = cv2.inRange(hsv, dark_lower, dark_upper)
        detections.extend(self._find_blobs(dark_mask, frame, trash_type=3))

        # Detect blue recycling bins
        blue_lower = np.array([100, 50, 50])
        blue_upper = np.array([130, 255, 255])
        blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
        detections.extend(self._find_blobs(blue_mask, frame, trash_type=2, is_bin=True))

        # Detect green organic waste
        green_lower = np.array([35, 40, 40])
        green_upper = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        detections.extend(self._find_blobs(green_mask, frame, trash_type=1))

        return detections

    def _find_blobs(self, mask, frame, trash_type=0, is_bin=False) -> list[dict]:
        """Find connected blobs in mask and return detections above size threshold."""
        detections = []
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        h, w = frame.shape[:2]
        min_area = (h * w) * 0.01  # at least 1% of image

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue

            x, y, bw, bh = cv2.boundingRect(cnt)
            cx = (x + bw / 2 - w / 2) / w  # normalized center
            cy = (y + bh / 2 - h / 2) / h

            # Estimate depth from blob size (simple approximation)
            depth = min(bw, bh) / max(w, h) * 5.0  # crude meters estimate

            confidence = min(int(area / (h * w) * 200), 100)
            if confidence < self.min_confidence:
                continue

            detections.append({
                'x': cx,
                'y': cy,
                'z': depth,
                'confidence': confidence,
                'trash_type': trash_type,
                'is_bin': is_bin,
            })

        return detections


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
