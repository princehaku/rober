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
from typing import Any, Optional

from ros2_trashbot_hardware.wave_rover_protocol import FEEDBACK_BASE_INFO


def vendor_degrees_to_ros_radians(value: float) -> float:
    """把 WAVE ROVER IMU 角度反馈从 degrees 转为 ROS radians。"""
    # IMU.cpp 用 57.3 生成 r/p/y，因此进入 ROS 四元数前必须显式转弧度。
    return math.radians(float(value))


def _parse_required_finite_float(data: dict[str, object], key: str) -> float:
    """解析必须存在且必须是有限数值的字段。"""
    # L/R/r/p/v 一旦出现坏值，就说明这帧的速度或电压事实不可信，必须整帧 fail-closed。
    value = float(data[key])
    if not math.isfinite(value):
        raise ValueError(f"{key} must be finite")
    return value


def _parse_optional_yaw(data: dict[str, object]) -> float | None:
    """解析允许缺失语义的 yaw 字段。"""
    raw_value = data["y"]
    # 真实上车 smoke 已观测到 y 可能是 JSON null 或字符串 "null"；这表示姿态不可用，不代表整帧无效。
    if raw_value is None:
        return None
    if isinstance(raw_value, str) and raw_value.strip().lower() == "null":
        return None

    yaw = float(raw_value)
    # yaw 如果给了数值，就必须是有限值；否则宁可丢弃，避免把坏姿态扩散到 /imu/data。
    if not math.isfinite(yaw):
        raise ValueError("y must be finite when present")
    return yaw


def parse_feedback_line(line: bytes | str) -> Optional[dict[str, Any]]:
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
            "left_speed": _parse_required_finite_float(data, "L"),
            "right_speed": _parse_required_finite_float(data, "R"),
            "roll": _parse_required_finite_float(data, "r"),
            "pitch": _parse_required_finite_float(data, "p"),
            "yaw": _parse_optional_yaw(data),
            "voltage": _parse_required_finite_float(data, "v"),
            # O11 现场复验必须能追到 vendor 原始 T=1001 字段，避免 L/R=0 时分不清是固件反馈还是解析别名问题。
            "vendor_frame": {key: data.get(key) for key in ("T", "L", "R", "r", "p", "y", "v")},
        }
    except (TypeError, ValueError):
        return None

    return feedback
