"""ROS2 real camera publisher backed by OpenCV VideoCapture."""

from __future__ import annotations

import os
from typing import Union

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class CameraPublisher(Node):
    """Publish frames from a real camera device to /camera/image_raw."""

    def __init__(self) -> None:
        super().__init__('camera_publisher')

        # 这些参数只描述采集入口，不改任何 vendor 串口或底盘默认值。
        self.declare_parameter('device', '/dev/video0')
        self.declare_parameter('topic', '/camera/image_raw')
        self.declare_parameter('frame_id', 'camera')
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 15.0)

        self.device = str(self.get_parameter('device').value)
        self.topic = str(self.get_parameter('topic').value)
        self.frame_id = str(self.get_parameter('frame_id').value)
        self.width = int(self.get_parameter('width').value)
        self.height = int(self.get_parameter('height').value)
        self.fps = float(self.get_parameter('fps').value)

        self.publisher = self.create_publisher(Image, self.topic, 10)
        self._warned_read_failure = False

        # vendor 参考只证明 Raspberry Pi app 可用 cv2.VideoCapture(0)；
        # rober 在 Orange Pi 上只把真实设备路径或索引作为参数输入，不猜测 CSI/Picamera2。
        self.capture = cv2.VideoCapture(self._device_argument(self.device))
        if not self.capture or not self.capture.isOpened():
            raise RuntimeError(
                f'Failed to open camera device {self.device}; '
                'camera_publisher fails closed and will not fabricate frames'
            )

        # 请求分辨率和帧率仅是软约束；真实生效值以驱动/设备返回为准。
        if self.width > 0:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(self.width))
        if self.height > 0:
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self.height))
        if self.fps > 0.0:
            self.capture.set(cv2.CAP_PROP_FPS, float(self.fps))

        publish_period_s = 1.0 / self.fps if self.fps > 0.0 else 0.1
        self.timer = self.create_timer(publish_period_s, self._publish_frame)
        self.get_logger().info(
            f'camera_publisher streaming {self.device} to {self.topic} '
            f'with frame_id={self.frame_id}, requested {self.width}x{self.height}@{self.fps:.2f}fps'
        )

    @staticmethod
    def _device_argument(raw_device: str) -> Union[int, str]:
        """Allow `/dev/video0` paths and simple numeric indices like `0`."""
        stripped = raw_device.strip()
        if stripped.isdigit():
            return int(stripped)
        return os.path.expanduser(stripped)

    def _publish_frame(self) -> None:
        # 采集失败时保持 fail closed：跳过本帧并给出可读日志，不补假图像。
        ok, frame = self.capture.read()
        if not ok or frame is None:
            if not self._warned_read_failure:
                self.get_logger().error(
                    f'Failed to read frame from {self.device}; no synthetic frame will be published'
                )
                self._warned_read_failure = True
            return

        self._warned_read_failure = False
        height, width = frame.shape[:2]
        msg = Image()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.height = height
        msg.width = width
        msg.encoding = 'bgr8'
        msg.is_bigendian = False
        msg.step = width * 3
        msg.data = frame.tobytes()
        self.publisher.publish(msg)

    def destroy_node(self) -> bool:
        # 关闭节点时释放相机，避免同机下一次 smoke 被设备占用卡住。
        capture = getattr(self, 'capture', None)
        if capture is not None:
            capture.release()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = CameraPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
