"""WAVE ROVER T=1001 反馈解析。

Vendor 来源：
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/IMU.cpp
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h

本模块只承认厂商 base feedback 中已经有出处的字段，不补造里程计事实。
"""

from __future__ import annotations

import json
import math
from typing import Optional

from ros2_trashbot_hardware.wave_rover_protocol import FEEDBACK_BASE_INFO


def vendor_degrees_to_ros_radians(value: float) -> float:
    """把 WAVE ROVER IMU 角度反馈从 degrees 转为 ROS radians。"""
    # IMU.cpp 用 57.3 生成 r/p/y，因此进入 ROS 四元数前必须显式转弧度。
    return math.radians(float(value))


def parse_feedback_line(line: bytes | str) -> Optional[dict[str, float]]:
    """解析 WAVE ROVER T=1001 底盘反馈，并忽略无关 UART 行。"""
    try:
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        data = json.loads(line.strip())
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return None

    # 只消费 FEEDBACK_BASE_INFO，避免把 echo、ESP-NOW 或其他扩展帧误发布为 ROS 话题。
    if data.get("T") != FEEDBACK_BASE_INFO:
        return None

    required = ("L", "R", "r", "p", "y", "v")
    if not all(key in data for key in required):
        return None

    try:
        feedback = {
            "left_speed": float(data["L"]),
            "right_speed": float(data["R"]),
            "roll": float(data["r"]),
            "pitch": float(data["p"]),
            "yaw": float(data["y"]),
            "voltage": float(data["v"]),
        }
    except (TypeError, ValueError):
        return None

    # 串口数据里一旦出现 NaN/Infinity，宁可丢弃也不污染 /imu/data 或 /battery。
    if not all(math.isfinite(value) for value in feedback.values()):
        return None

    return feedback
