"""兼容入口：Waveshare WAVE ROVER JSON serial bridge.

Protocol source:
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h

历史测试和 console entry point 仍 import 本文件；实际实现已拆到同包子模块。
"""

from __future__ import annotations

import rclpy

from ros2_trashbot_hardware.bridge_config import validate_startup_config
from ros2_trashbot_hardware.esp32_bridge_node import ESP32Bridge
from ros2_trashbot_hardware.wave_rover_feedback import (
    parse_feedback_line,
    vendor_degrees_to_ros_radians,
)
from ros2_trashbot_hardware.wave_rover_protocol import (
    CMD_BASE_FEEDBACK_FLOW,
    CMD_FEEDBACK_FLOW_INTERVAL,
    CMD_PWM_INPUT,
    CMD_ROS_CTRL,
    CMD_SPEED_CTRL,
    CMD_UART_ECHO_MODE,
    FEEDBACK_BASE_INFO,
    VALID_COMMAND_MODES,
    build_cmd_vel_command,
    build_startup_config_commands,
    encode_json_command,
)


def main(args=None):
    """启动 ROS2 bridge node；保留原 console script 入口兼容。"""
    # 运行时层仍在 esp32_bridge_node，main 只负责 ROS lifecycle，降低入口文件复杂度。
    rclpy.init(args=args)
    node = ESP32Bridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


__all__ = [
    "CMD_BASE_FEEDBACK_FLOW",
    "CMD_FEEDBACK_FLOW_INTERVAL",
    "CMD_PWM_INPUT",
    "CMD_ROS_CTRL",
    "CMD_SPEED_CTRL",
    "CMD_UART_ECHO_MODE",
    "ESP32Bridge",
    "FEEDBACK_BASE_INFO",
    "VALID_COMMAND_MODES",
    "build_cmd_vel_command",
    "build_startup_config_commands",
    "encode_json_command",
    "main",
    "parse_feedback_line",
    "validate_startup_config",
    "vendor_degrees_to_ros_radians",
]


if __name__ == "__main__":
    main()
