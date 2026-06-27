"""离线 WAVE ROVER 硬件诊断 proof 构建器。

厂商来源：
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h

本模块刻意保持离线：不打开串口、不创建 ROS2 node、不发布或订阅 topic。
它复用 runtime 同源的协议纯函数，让 proof artifact 和真实 driver 的命令编码、
反馈解析逻辑保持一致。
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from ros2_trashbot_hardware.bridge_config import validate_startup_config
from ros2_trashbot_hardware.wave_rover_feedback import parse_feedback_line
from ros2_trashbot_hardware.wave_rover_protocol import (
    build_cmd_vel_command,
    build_startup_config_commands,
    encode_json_command,
)


VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h",
]
PROOF_SOURCE = "software_proof"
ASSUMPTIONS = {
    "serial_port": "Orange Pi 串口路径需由现场确认，不使用 Raspberry Pi 示例路径代替",
    "feedback_interval_validation": "feedback_interval_ms 为目标上报周期参数；实际采样频率需通过 HIL 多帧 T=1001 样本确认",
}

DEFAULT_CONFIG = {
    "serial_port": "/dev/ttyUSB0",
    "serial_baudrate": 115200,
    "command_mode": "ros",
    "track_width_m": 0.172,
    "max_wheel_speed_mps": 1.3,
    "pwm_min_abs": 164,
    "pwm_max_abs": 164,
    "feedback_interval_ms": 100,
    "odom_publish_hz": 20.0,
}

DEFAULT_FEEDBACK_SAMPLE = {
    "T": 1001,
    "L": 0.2,
    "R": 0.3,
    "r": 1.0,
    "p": 2.0,
    "y": 3.0,
    "v": 11.7,
}

ODOM_SOURCE = "ROS-side command integration until measured wheel odometry is validated"


def _json_frame(command: dict[str, Any]) -> str:
    """在不打开 UART 的前提下输出完整 JSON line。"""
    # 离线 proof 必须复用 runtime 的编码函数，避免文档示例和真实发送帧分叉。
    return encode_json_command(command).decode("utf-8")


def _merge_config(config: dict[str, Any] | None) -> dict[str, Any]:
    # 先复制默认值再覆盖，保证输出 artifact 总是包含完整参数快照。
    merged = dict(DEFAULT_CONFIG)
    if config:
        merged.update(config)
    merged["command_mode"] = str(merged["command_mode"]).lower()
    merged["odom_source"] = ODOM_SOURCE
    return merged


def _coerce_int_config(config: dict[str, Any], key: str) -> int:
    try:
        value = int(config[key])
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{key} must be an integer") from exc
    return value


def _coerce_float_config(config: dict[str, Any], key: str) -> float:
    try:
        value = float(config[key])
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{key} must be a number") from exc
    if not math.isfinite(value):
        raise ValueError(f"{key} must be finite")
    return value


def _validate_config(config: dict[str, Any]) -> dict[str, Any]:
    try:
        # 命令行输入先统一强转类型，再走和 runtime 一致的启动参数校验。
        config["serial_baudrate"] = _coerce_int_config(config, "serial_baudrate")
        config["track_width_m"] = _coerce_float_config(config, "track_width_m")
        config["max_wheel_speed_mps"] = _coerce_float_config(config, "max_wheel_speed_mps")
        config["pwm_min_abs"] = _coerce_int_config(config, "pwm_min_abs")
        config["pwm_max_abs"] = _coerce_int_config(config, "pwm_max_abs")
        config["feedback_interval_ms"] = _coerce_int_config(config, "feedback_interval_ms")
        config["odom_publish_hz"] = _coerce_float_config(config, "odom_publish_hz")
        if config["serial_baudrate"] <= 0:
            raise ValueError("serial_baudrate must be > 0")
        validate_startup_config(
            command_mode=config["command_mode"],
            track_width_m=config["track_width_m"],
            max_wheel_speed_mps=config["max_wheel_speed_mps"],
            pwm_min_abs=config["pwm_min_abs"],
            pwm_max_abs=config["pwm_max_abs"],
            feedback_interval_ms=config["feedback_interval_ms"],
            odom_publish_hz=config["odom_publish_hz"],
        )
    except (TypeError, ValueError) as exc:
        return {"status": "invalid_config", "error": str(exc)}
    return {"status": "valid"}


def _sample_to_line(feedback_sample: dict[str, Any] | str | bytes | None) -> tuple[Any, str | bytes]:
    if feedback_sample is None:
        # 默认样本只是 parser contract proof，不代表真实 WAVE ROVER 已经上报。
        raw: Any = dict(DEFAULT_FEEDBACK_SAMPLE)
        return raw, _json_frame(raw)
    if isinstance(feedback_sample, dict):
        return dict(feedback_sample), _json_frame(feedback_sample)
    return feedback_sample, feedback_sample


def _build_feedback_section(feedback_sample: dict[str, Any] | str | bytes | None) -> dict[str, Any]:
    raw, line = _sample_to_line(feedback_sample)
    # 反馈解析函数只接受 T=1001，proof 因此不会把任意 JSON 包装成硬件反馈。
    parsed = parse_feedback_line(line)
    if parsed is None:
        return {
            "raw": raw,
            "parsed": None,
            "status": "feedback_parse_failed",
            "detail": "Sample did not parse as vendor T=1001 base feedback.",
        }
    return {"raw": raw, "parsed": parsed, "status": "parsed"}


def _build_cmd_vel_examples(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    # 同时输出 speed/T=1 和 ros/T=13，但 T=13 明确标为未验证路径。
    speed_forward = build_cmd_vel_command(
        linear_x=0.65,
        angular_z=0.0,
        command_mode="speed",
        track_width_m=config["track_width_m"],
        max_wheel_speed_mps=config["max_wheel_speed_mps"],
    )
    speed_turn = build_cmd_vel_command(
        linear_x=0.2,
        angular_z=0.5,
        command_mode="speed",
        track_width_m=config["track_width_m"],
        max_wheel_speed_mps=config["max_wheel_speed_mps"],
    )
    ros_forward = build_cmd_vel_command(
        linear_x=0.1,
        angular_z=0.0,
        command_mode="ros",
        track_width_m=config["track_width_m"],
        max_wheel_speed_mps=config["max_wheel_speed_mps"],
    )
    pwm_forward = build_cmd_vel_command(
        linear_x=0.12,
        angular_z=0.0,
        command_mode="pwm",
        track_width_m=config["track_width_m"],
        max_wheel_speed_mps=config["max_wheel_speed_mps"],
        pwm_min_abs=config["pwm_min_abs"],
        pwm_max_abs=config["pwm_max_abs"],
    )
    return {
        "speed_mode_forward": {"command": speed_forward, "uart_frame": _json_frame(speed_forward)},
        "speed_mode_turn": {"command": speed_turn, "uart_frame": _json_frame(speed_turn)},
        "pwm_mode_forward_vendor_sample": {"command": pwm_forward, "uart_frame": _json_frame(pwm_forward)},
        "ros_mode_forward_unverified": {
            "command": ros_forward,
            "uart_frame": _json_frame(ros_forward),
        },
    }


def _risk_flags(config: dict[str, Any]) -> list[dict[str, str]]:
    # 风险字段给下游 UI/文档消费，防止 software proof 被误读为 HIL pass。
    flags = [
        {
            "id": "hil_required",
            "severity": "high",
            "detail": "Offline proof does not validate real UART, wheel direction, feedback frequency, IMU, battery, or motion.",
        },
        {
            "id": "orange_pi_uart_unconfirmed",
            "severity": "high",
            "detail": "Vendor Raspberry Pi UART paths are not Orange Pi facts; target serial device must be confirmed on the robot.",
        },
        {
            "id": "ros_mode_t13_unverified",
            "severity": "medium",
            "detail": "Vendor firmware defines T=13 as ROS X/Z control, but this project keeps it out of the default path until WAVE ROVER HIL passes.",
        },
        {
            "id": "odom_is_command_integration",
            "severity": "medium",
            "detail": ODOM_SOURCE,
        },
    ]
    if config["command_mode"] == "ros":
        flags.append(
            {
                "id": "command_mode_ros_requires_hil",
                "severity": "high",
                "detail": "The selected command_mode is ros/T=13; do not treat it as production-ready before hardware validation.",
            }
        )
    if config["command_mode"] == "pwm":
        flags.append(
            {
                "id": "command_mode_pwm_vendor_sample",
                "severity": "medium",
                "detail": "Vendor T=11 PWM sample uses 164; current field feedback may keep T1001 L/R at 0, so keep short pulses and stop fallback.",
            }
        )
    return flags


def _hil_recipe(config: dict[str, Any]) -> dict[str, Any]:
    # 履约 recipe 只给动作，不在离线 artifact 中声明真实串口或真实速度已通过。
    return {
        "purpose": "Run only on a prepared robot with wheels clear or a safe low-speed test area.",
        "vendor_basis": [
            "UART newline-delimited JSON commands from base_ctrl.py/json_cmd.h.",
            "T=1001 feedback parser expects L/R/r/p/y/v fields.",
        ],
        "no_motion": (
            "python3 onboard/scripts/hardware_smoke_wave_rover.py "
            f"--serial-port {config['serial_port']} --baudrate {config['serial_baudrate']} "
            f"--feedback-interval-ms {config['feedback_interval_ms']}"
        ),
        "low_speed_t1": (
            "python3 onboard/scripts/hardware_smoke_wave_rover.py "
            f"--serial-port {config['serial_port']} --baudrate {config['serial_baudrate']} "
            "--move-test --reverse-test --test-speed 0.08 --test-duration-s 0.5"
        ),
        "t13_ros_mode": (
            "python3 onboard/scripts/hardware_smoke_wave_rover.py "
            f"--serial-port {config['serial_port']} --baudrate {config['serial_baudrate']} "
            "--ros-mode-test --turn-test --test-speed 0.08 --test-duration-s 0.5"
        ),
        "do_not_claim": [
            "real UART connected",
            "wheel direction verified",
            "velocity units verified",
            "feedback frequency measured",
            "IMU/battery calibrated",
        ],
    }


def build_hardware_diagnostics_proof(
    config: dict[str, Any] | None = None,
    feedback_sample: dict[str, Any] | str | bytes | None = None,
    output_file: str | Path | None = None,
) -> dict[str, Any]:
    """构建 WAVE ROVER bridge 的离线 diagnostics proof artifact。"""
    # 生成顺序固定：参数、反馈、命令、风险，便于 sprint 证据人工复核。
    proof_config = _merge_config(config)
    config_validation = _validate_config(proof_config)
    feedback = _build_feedback_section(feedback_sample)

    status = "software_proof_ready"
    startup_commands: list[dict[str, Any]] = []
    cmd_vel_examples: dict[str, dict[str, Any]] = {}
    if config_validation["status"] == "invalid_config":
        status = "invalid_config"
    else:
        commands = build_startup_config_commands(proof_config["feedback_interval_ms"])
        startup_commands = [
            {"command": command, "uart_frame": _json_frame(command)} for command in commands
        ]
        cmd_vel_examples = _build_cmd_vel_examples(proof_config)
        if feedback["status"] == "feedback_parse_failed":
            status = "feedback_parse_failed"

    proof = {
        "source": PROOF_SOURCE,
        "status": status,
        "vendor_sources": list(VENDOR_SOURCES),
        "config": proof_config,
        "config_validation": config_validation,
        "startup_commands": startup_commands,
        "cmd_vel_examples": cmd_vel_examples,
        "feedback_sample": feedback,
        "assumptions": ASSUMPTIONS,
        "risk_flags": _risk_flags(proof_config),
        "hil_recipe": _hil_recipe(proof_config),
    }

    if output_file is not None:
        # 输出文件是离线证据，不含 credential、真实串口原始日志或 HIL 成功断言。
        Path(output_file).write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return proof


def _parse_feedback_sample(value: str | None) -> dict[str, Any] | str | None:
    if value is None:
        return None
    try:
        # 能解析成 JSON 就按样本对象处理；否则保留原字符串，让 parser 给出失败边界。
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value
    return parsed


def main(argv: list[str] | None = None) -> int:
    # 命令行入口是 PC 侧 proof builder，不打开 UART；真实 HIL 仍要走 hardware smoke 流程。
    parser = argparse.ArgumentParser(description="Build offline WAVE ROVER hardware proof JSON.")
    parser.add_argument("--serial-port", default=DEFAULT_CONFIG["serial_port"])
    parser.add_argument("--serial-baudrate", type=int, default=DEFAULT_CONFIG["serial_baudrate"])
    parser.add_argument("--command-mode", default=DEFAULT_CONFIG["command_mode"])
    parser.add_argument("--track-width-m", type=float, default=DEFAULT_CONFIG["track_width_m"])
    parser.add_argument(
        "--max-wheel-speed-mps", type=float, default=DEFAULT_CONFIG["max_wheel_speed_mps"]
    )
    parser.add_argument("--pwm-min-abs", type=int, default=DEFAULT_CONFIG["pwm_min_abs"])
    parser.add_argument("--pwm-max-abs", type=int, default=DEFAULT_CONFIG["pwm_max_abs"])
    parser.add_argument(
        "--feedback-interval-ms", type=int, default=DEFAULT_CONFIG["feedback_interval_ms"]
    )
    parser.add_argument("--feedback-sample-json")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    config = {
        "serial_port": args.serial_port,
        "serial_baudrate": args.serial_baudrate,
        "command_mode": args.command_mode,
        "track_width_m": args.track_width_m,
        "max_wheel_speed_mps": args.max_wheel_speed_mps,
        "pwm_min_abs": args.pwm_min_abs,
        "pwm_max_abs": args.pwm_max_abs,
        "feedback_interval_ms": args.feedback_interval_ms,
    }
    proof = build_hardware_diagnostics_proof(
        config=config,
        feedback_sample=_parse_feedback_sample(args.feedback_sample_json),
        output_file=args.output,
    )
    output = json.dumps(proof, indent=2, sort_keys=True) + "\n"
    if args.output:
        print(args.output)
    else:
        print(output, end="")

    if proof["status"] == "invalid_config":
        return 2
    if proof["status"] == "feedback_parse_failed":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
