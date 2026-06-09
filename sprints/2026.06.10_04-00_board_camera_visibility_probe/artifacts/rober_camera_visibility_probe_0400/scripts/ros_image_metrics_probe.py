#!/usr/bin/env python3
"""订阅 /camera/image_raw 一帧并输出与 OpenCV 直接采样一致的指标。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


def luma_metrics(frame: np.ndarray) -> dict[str, object]:
    """计算亮度和纹理指标，避免只凭肉眼判断黑场。"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    luma = gray.astype(np.float32)
    mean_luma = float(np.mean(luma))
    min_luma = float(np.min(luma))
    max_luma = float(np.max(luma))
    dynamic_range = max_luma - min_luma
    non_black_ratio = float(np.count_nonzero(luma > 10.0) / luma.size)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    edges = cv2.Canny(gray, 50, 150)
    edge_count = int(np.count_nonzero(edges))
    edge_ratio = float(edge_count / luma.size)
    # 均匀亮帧不能支撑路线/定位；必须同时有亮度和纹理。
    visible_content_candidate = (
        mean_luma >= 35.0
        and non_black_ratio >= 0.10
        and (dynamic_range >= 15.0 or laplacian_var >= 5.0 or edge_ratio >= 0.002)
    )
    return {
        "mean_luma": round(mean_luma, 6),
        "min_luma": round(min_luma, 6),
        "max_luma": round(max_luma, 6),
        "dynamic_range_luma": round(dynamic_range, 6),
        "non_black_ratio": round(non_black_ratio, 9),
        "laplacian_var": round(laplacian_var, 6),
        "edge_count": edge_count,
        "edge_ratio": round(edge_ratio, 9),
        "visible_content_candidate": visible_content_candidate,
    }


class OneImageSubscriber(Node):
    """只收一帧就退出，减少对现场 ROS graph 的扰动。"""

    def __init__(self, topic: str) -> None:
        super().__init__("camera_visibility_one_image_probe")
        self.message: Image | None = None
        self.subscription = self.create_subscription(Image, topic, self._on_image, 10)

    def _on_image(self, message: Image) -> None:
        """收到第一帧后缓存，主循环会立即退出。"""
        if self.message is None:
            self.message = message


def decode_bgr8(message: Image) -> np.ndarray:
    """把 ROS Image 的 bgr8 字节流转成 OpenCV frame。"""
    if message.encoding != "bgr8":
        raise ValueError(f"unsupported encoding: {message.encoding}")
    expected_len = int(message.height) * int(message.step)
    if len(message.data) < expected_len:
        raise ValueError(f"image data too short: {len(message.data)} < {expected_len}")
    raw = np.frombuffer(message.data, dtype=np.uint8)[:expected_len]
    rows = raw.reshape((int(message.height), int(message.step)))
    frame = rows[:, : int(message.width) * 3].reshape((int(message.height), int(message.width), 3))
    return frame.copy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="/camera/image_raw")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--timeout-sec", type=float, default=8.0)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rclpy.init()
    node = OneImageSubscriber(args.topic)
    deadline = node.get_clock().now().nanoseconds + int(args.timeout_sec * 1_000_000_000)
    try:
        while rclpy.ok() and node.message is None and node.get_clock().now().nanoseconds < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
        if node.message is None:
            summary = {
                "schema": "trashbot.ros_camera_image_metrics.v1",
                "topic": args.topic,
                "image_message_observed": False,
                "visible_content_candidate": False,
            }
        else:
            frame = decode_bgr8(node.message)
            image_path = output_dir / "ros_camera_image_raw_sample.jpg"
            cv2.imwrite(str(image_path), frame)
            summary = {
                "schema": "trashbot.ros_camera_image_metrics.v1",
                "topic": args.topic,
                "image_message_observed": True,
                "height": int(node.message.height),
                "width": int(node.message.width),
                "encoding": node.message.encoding,
                "step": int(node.message.step),
                "data_len": len(node.message.data),
                "frame_path": str(image_path),
                **luma_metrics(frame),
            }
        (output_dir / "ros_image_metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
