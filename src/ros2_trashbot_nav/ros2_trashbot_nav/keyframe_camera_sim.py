import os
import glob

import cv2
from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class KeyframeCameraSim(Node):
    """Publish keyframe images as a fake camera stream for simulation tests."""

    def __init__(self):
        super().__init__('keyframe_camera_sim')
        self.declare_parameter('keyframe_dir', '~/.ros/trashbot_runs/run_001/keyframes')
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('fps', 2.0)

        self.keyframe_dir = os.path.expanduser(self.get_parameter('keyframe_dir').value)
        self.camera_topic = self.get_parameter('camera_topic').value
        self.fps = float(self.get_parameter('fps').value)

        self.bridge = CvBridge()
        self.pub = self.create_publisher(Image, self.camera_topic, 10)
        self.files = sorted(glob.glob(os.path.join(self.keyframe_dir, '*.jpg')))
        self.index = 0

        period = 1.0 / max(self.fps, 0.1)
        self.create_timer(period, self._tick)
        self.get_logger().info(f'Loaded {len(self.files)} keyframes from {self.keyframe_dir}')

    def _tick(self):
        if not self.files:
            return
        img = cv2.imread(self.files[self.index])
        if img is None:
            self.index = (self.index + 1) % len(self.files)
            return
        msg = self.bridge.cv2_to_imgmsg(img, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera'
        self.pub.publish(msg)
        self.index = (self.index + 1) % len(self.files)


def main(args=None):
    rclpy.init(args=args)
    node = KeyframeCameraSim()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

