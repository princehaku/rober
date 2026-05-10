# WAVE ROVER JSON Bridge

## Sources

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/IMU_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/battery_ctrl.h`

本文件用于定义桥接协议与证据来源边界。本轮默认离线核查结果标记为 `source=software_proof`；真实机器人实测通过的证据标记为 `source=hil_pass`，并在产测文档中补齐。

## Evidence Source Boundary

- `source=software_proof`：命令拼接、参数边界、文档与风险声明，仅作为实现前置依据。
- `source=hil_pass`：真实串口上车验证，需补齐方向、反馈、IMU/Battery、`/odom` 声明及安全验证。

## UART Framing

官方 WAVE ROVER ESP32 固件使用一行 JSON（UTF-8）并以 `\n` 结束。

- 厂商 Raspberry Pi 示例设备路径：`/dev/ttyAMA0` / `/dev/serial0`
- Orange Pi 上下文必须以 `ls /dev/tty*` / `ls /dev/serial*` 现场确认 UART 路径；不得直接照抄 Raspberry Pi 示例路径。

## Command Table

| ROS bridge use | Vendor JSON | Direction | Source |
| --- | --- | --- | --- |
| Stop / left-right speed command | `{"T":1,"L":0.0,"R":0.0}` | ROS to ESP32 | `json_cmd.h` `CMD_SPEED_CTRL`, `base_ctrl.py` |
| Velocity command mode (`T=13`) | `{"T":13,"X":0.1,"Z":0.3}` | ROS to ESP32 | `json_cmd.h` `CMD_ROS_CTRL`, `movtion_module.h` |
| One-shot base feedback request | `{"T":130}` | ROS to ESP32 | `json_cmd.h` `CMD_BASE_FEEDBACK` |
| Feedback stream on/off | `{"T":131,"cmd":1}` / `{"T":131,"cmd":0}` | ROS to ESP32 | `json_cmd.h`, `uart_ctrl.h` |
| Feedback interval set | `{"T":142,"cmd":100}` | ROS to ESP32 | `json_cmd.h`, `uart_ctrl.h`, `ugv_advance.h` |
| UART echo off/on | `{"T":143,"cmd":0}` / `{"T":143,"cmd":1}` | ROS to ESP32 | `json_cmd.h`, `uart_ctrl.h` |
| Base feedback frame | `{"T":1001,"L":...,"R":...,"r":...,"p":...,"y":...,"v":...}` | ESP32 to ROS | `json_cmd.h` `FEEDBACK_BASE_INFO`, `ugv_advance.h` |

### Feedback fields 与采样频率

- 关键字段：`L`,`R`,`r`,`p`,`y`,`v`（`T=1001`）需齐备。
- `configure_feedback` 默认发送序列：`{"T":143,"cmd":0}` -> `{"T":142,"cmd":<interval_ms>}` -> `{"T":131,"cmd":1}`。
- 建议在 `source=hil_pass` 下采样至少 2 帧 `T=1001`，确认采样间隔接近 `feedback_interval_ms`（例如 100ms 时约 10Hz）。
- `v` 默认映射为电压；`r/p/y` 为欧拉角（厂商原始值按项目桥接代码按弧度发布 yaw）。

## Command Modes

- `speed`：将 `/cmd_vel` 映射为 `T=1` 的 `L/R`，当前项目默认。
- `ros`：将 `/cmd_vel` 映射为 `T=13` 的 `X/Z`。仅在 `source=hil_pass` 的方向与安全验证后使用。

对于 `speed` 模式，差速关系：

```text
left_mps = linear.x - angular.z * track_width_m / 2
right_mps = linear.x + angular.z * track_width_m / 2
```

当前桥接在项目侧默认将 `T=1` 值按 `max_wheel_speed_mps` 归一化并夹到 `[-1,1]`，该参数是可调的项目参数，不能当作硬件标称校准值。

## Configurable Parameters

- `serial_port`
- `serial_baudrate`
- `port`（已废弃，保留兼容别名）
- `baudrate`（已废弃，保留兼容别名）
- `command_mode`
- `track_width_m`
- `max_wheel_speed_mps`
- `feedback_interval_ms`
- `odom_publish_hz`

参数校验要求：`track_width_m > 0`、`max_wheel_speed_mps > 0`、`feedback_interval_ms >= 0`、`odom_publish_hz > 0`。

## Published ROS Contracts

### `/odom`

当前实现基于最近一次 `/cmd_vel` 的指令积分计算（未使用轮速闭环），未经过独立编码器融合校验。故 `/odom` 在证据上应标注 `source=command_integration` 并由 HIL 的第一轮 run 带 `source=hil_pass` 重验。

### `/imu/data`

当前仅发布 yaw 四元数（`T=1001` 的 `y`），`r/p` 虽在反馈帧内但未进入 ROS 消息。
HIL run 必须在报告中说明：`/imu/data` 与 `T=1001.y` 一一对应（以 `evidence_ref` 绑定）。

### `/battery`

当前仅发布电压（来自 `T=1001.v`）。不提供当前、SOC、容量与电芯信息。
HIL run 需记录 `T=1001.v` 与 `/battery` 取样对齐证据。

## Run-time Validation Checklist

- 确认 Orange Pi 串口与波特率（不要复用 Raspberry Pi 示例路径）。
- 停止命令 `T=1,L=0,R=0` 生效且运动停止。
- 启动前确认已下发 `T=143`、`T=142`、`T=131`。
- 低速 `T=1` 前进、倒退、转向方向验证通过（由 HIL 填写）。
- 采集至少两帧 `T=1001` 并核对 `L/R/r/p/y/v`。
- 只在停稳和 `T=1` 安全后再尝试 `T=13`。
- 下发顺序与间隔复验通过后，才允许把 run 标记为 `hil_pass`。
