"""ESP32 bridge 参数读取与校验。

Vendor 来源：
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h

参数层只做可配置性和边界检查，不把现场 Orange Pi 串口路径写成已验证事实。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ros2_trashbot_hardware.wave_rover_protocol import VALID_COMMAND_MODES


@dataclass(frozen=True)
class BridgeConfig:
    """运行时配置快照，方便 ROS glue 与离线 proof 共用同一套校验语义。"""

    port: str
    baudrate: int
    command_mode: str
    track_width_m: float
    max_wheel_speed_mps: float
    pwm_min_abs: int
    pwm_max_abs: int
    feedback_interval_ms: int
    odom_publish_hz: float
    publish_odom_tf: bool
    feedback_debug_log_path: str = ""
    alias_port_used: bool = False
    alias_baudrate_used: bool = False


def validate_startup_config(
    command_mode: str,
    track_width_m: float,
    max_wheel_speed_mps: float,
    pwm_min_abs: int,
    pwm_max_abs: int,
    feedback_interval_ms: int,
    odom_publish_hz: float,
) -> None:
    """打开 UART 或移动底盘前校验 driver 参数。"""
    if command_mode.lower() not in VALID_COMMAND_MODES:
        raise ValueError(f"command_mode must be one of {VALID_COMMAND_MODES}")
    if track_width_m <= 0:
        raise ValueError("track_width_m must be > 0")
    if max_wheel_speed_mps <= 0:
        raise ValueError("max_wheel_speed_mps must be > 0")
    if pwm_min_abs < 0 or pwm_max_abs <= 0 or pwm_min_abs > pwm_max_abs or pwm_max_abs > 255:
        raise ValueError("pwm_min_abs/pwm_max_abs must satisfy 0 <= min <= max <= 255")
    if feedback_interval_ms < 0:
        raise ValueError("feedback_interval_ms must be >= 0")
    if odom_publish_hz <= 0:
        raise ValueError("odom_publish_hz must be > 0")


def declare_bridge_parameters(node: Any) -> None:
    """声明 ROS 参数，同时保留旧 launch 别名。"""
    # 串口参数 serial_port 是项目规范参数；port/baudrate 仅为历史兼容，避免旧 launch 直接断掉。
    node.declare_parameter("serial_port", "/dev/ttyUSB0")
    node.declare_parameter("serial_baudrate", 115200)
    node.declare_parameter("port", "")
    node.declare_parameter("baudrate", 0)
    node.declare_parameter("command_mode", "speed")
    node.declare_parameter("track_width_m", 0.172)
    node.declare_parameter("max_wheel_speed_mps", 1.3)
    node.declare_parameter("pwm_min_abs", 90)
    node.declare_parameter("pwm_max_abs", 90)
    node.declare_parameter("feedback_interval_ms", 100)
    node.declare_parameter("odom_publish_hz", 20.0)
    # 动态 odom TF 默认开启，便于下一轮 smoke 直接复用；但它仍只代表命令积分，不是实测编码器。
    node.declare_parameter("publish_odom_tf", True)
    # 默认关闭 raw feedback 证据落盘，避免常规 bringup 产生额外 IO 或误把调试文件当作导航里程计。
    node.declare_parameter("feedback_debug_log_path", "")


def load_bridge_config(node: Any) -> BridgeConfig:
    """从 ROS node 读取并校验 bridge 参数。"""
    canonical_port = str(node.get_parameter("serial_port").value)
    alias_port = str(node.get_parameter("port").value)
    canonical_baudrate = int(node.get_parameter("serial_baudrate").value)
    alias_baudrate = int(node.get_parameter("baudrate").value)

    # 别名参数非空时继续生效，但 runtime 会打 warning，推动后续 launch 迁移到规范字段。
    config = BridgeConfig(
        port=alias_port or canonical_port,
        baudrate=alias_baudrate or canonical_baudrate,
        command_mode=str(node.get_parameter("command_mode").value).lower(),
        track_width_m=float(node.get_parameter("track_width_m").value),
        max_wheel_speed_mps=float(node.get_parameter("max_wheel_speed_mps").value),
        pwm_min_abs=int(node.get_parameter("pwm_min_abs").value),
        pwm_max_abs=int(node.get_parameter("pwm_max_abs").value),
        feedback_interval_ms=int(node.get_parameter("feedback_interval_ms").value),
        odom_publish_hz=float(node.get_parameter("odom_publish_hz").value),
        publish_odom_tf=bool(node.get_parameter("publish_odom_tf").value),
        feedback_debug_log_path=str(node.get_parameter("feedback_debug_log_path").value),
        alias_port_used=bool(alias_port),
        alias_baudrate_used=bool(alias_baudrate),
    )
    validate_startup_config(
        config.command_mode,
        config.track_width_m,
        config.max_wheel_speed_mps,
        config.pwm_min_abs,
        config.pwm_max_abs,
        config.feedback_interval_ms,
        config.odom_publish_hz,
    )
    return config
