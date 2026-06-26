"""WAVE ROVER UART JSON 协议纯函数。

Vendor 来源：
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h

本模块不打开串口、不 import ROS2；它只负责把项目参数转成厂商 JSON 帧。
"""

from __future__ import annotations

import json
import math
from typing import Any


CMD_SPEED_CTRL = 1
CMD_PWM_INPUT = 11
CMD_ROS_CTRL = 13
CMD_BASE_FEEDBACK_FLOW = 131
CMD_FEEDBACK_FLOW_INTERVAL = 142
CMD_UART_ECHO_MODE = 143
FEEDBACK_BASE_INFO = 1001
DEFAULT_PWM_MIN_ABS = 90
DEFAULT_PWM_MAX_ABS = 90
VALID_COMMAND_MODES = ("speed", "ros", "pwm")


def _clamp(value: float, low: float, high: float) -> float:
    """夹紧归一化轮速，避免离线计算把危险值直接写入 UART 帧。"""
    return max(low, min(high, value))


def _round_float(value: float) -> float:
    """固定小数输出，便于测试和 HIL 日志做逐帧对比。"""
    return round(float(value), 6)


def _pwm_from_wheel_speed(wheel_mps: float, max_wheel_speed_mps: float, pwm_min_abs: int, pwm_max_abs: int) -> int:
    """把轮速映射到 T=11 PWM；非零速度使用现场验证过的最小起步 PWM。"""
    if abs(wheel_mps) <= 1e-9:
        return 0
    scaled = round(abs(wheel_mps) / max_wheel_speed_mps * pwm_max_abs)
    pwm_abs = min(max(int(pwm_min_abs), scaled), int(pwm_max_abs))
    return pwm_abs if wheel_mps > 0 else -pwm_abs


def encode_json_command(command: dict[str, Any]) -> bytes:
    """把一条厂商 JSON 命令编码成 newline-delimited UART 帧。"""
    # 厂商 base_ctrl.py 使用 json.dumps(data) + '\n'，这里保留同样的一行一帧边界。
    return (json.dumps(command, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def build_cmd_vel_command(
    linear_x: float,
    angular_z: float,
    command_mode: str,
    track_width_m: float,
    max_wheel_speed_mps: float,
    pwm_min_abs: int = DEFAULT_PWM_MIN_ABS,
    pwm_max_abs: int = DEFAULT_PWM_MAX_ABS,
) -> dict[str, Any]:
    """把 ROS cmd_vel 参数转换为 WAVE ROVER JSON 命令。"""
    # T=13 在厂商固件存在，但本项目默认仍走 T=1；HIL 未通过前不把它当生产默认。
    mode = command_mode.lower()
    linear_x = float(linear_x)
    angular_z = float(angular_z)
    if not math.isfinite(linear_x) or not math.isfinite(angular_z):
        raise ValueError("cmd_vel values must be finite")

    if mode == "ros":
        return {"T": CMD_ROS_CTRL, "X": _round_float(linear_x), "Z": _round_float(angular_z)}

    if mode not in ("speed", "pwm"):
        raise ValueError(f"Unsupported command_mode: {command_mode}")

    if track_width_m <= 0:
        raise ValueError("track_width_m must be > 0")

    if max_wheel_speed_mps <= 0:
        raise ValueError("max_wheel_speed_mps must be > 0")

    # 速度模式按差速模型先算左右轮线速度，再除以项目参数 max_wheel_speed_mps。
    left_mps = linear_x - angular_z * track_width_m / 2.0
    right_mps = linear_x + angular_z * track_width_m / 2.0
    if mode == "pwm":
        if pwm_min_abs < 0 or pwm_max_abs <= 0 or pwm_min_abs > pwm_max_abs or pwm_max_abs > 255:
            raise ValueError("pwm_min_abs/pwm_max_abs must satisfy 0 <= min <= max <= 255")
        return {
            "T": CMD_PWM_INPUT,
            "L": _pwm_from_wheel_speed(left_mps, max_wheel_speed_mps, pwm_min_abs, pwm_max_abs),
            "R": _pwm_from_wheel_speed(right_mps, max_wheel_speed_mps, pwm_min_abs, pwm_max_abs),
        }
    left = _clamp(left_mps / max_wheel_speed_mps, -1.0, 1.0)
    right = _clamp(right_mps / max_wheel_speed_mps, -1.0, 1.0)
    return {"T": CMD_SPEED_CTRL, "L": _round_float(left), "R": _round_float(right)}


def build_startup_config_commands(feedback_interval_ms: int) -> list[dict[str, int]]:
    """生成厂商 UART 启动配置命令。"""
    # 启动顺序先关 echo，再设置 interval，最后打开反馈流，便于日志只保留真实反馈帧。
    return [
        {"T": CMD_UART_ECHO_MODE, "cmd": 0},
        {"T": CMD_FEEDBACK_FLOW_INTERVAL, "cmd": int(feedback_interval_ms)},
        {"T": CMD_BASE_FEEDBACK_FLOW, "cmd": 1},
    ]
