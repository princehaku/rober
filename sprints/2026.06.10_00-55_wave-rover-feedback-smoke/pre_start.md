# WAVE ROVER Feedback Smoke Pre-Start

## sprint_type: epic

## 背景

上一轮 `2026.06.10_00-45_integrated-sensor-motion-capture` 已完成真实上位机同轮雷达、摄像头、建图、route/keyframe、ROS2 motion 和 stop 证据，但 `/battery`、`/imu/data` 仍为空，恢复后的 `/api/base/status` 也显示 `feedback_ack.t1001_observed=false`。

本轮专门定位 WAVE ROVER `T=1001` feedback 链路：先直接从 UART raw line 验证 `T=130/T=131` 是否能拿到底盘反馈，再判断 ROS2 bridge 是否能把 feedback 发布到 `/battery` 和 `/imu/data`。

## 本轮目标

在真实上位机 `root@192.168.1.11:37878` 上完成：

- 停止 `upper_robot_api.py`，释放 `/dev/ttyS5`。
- 用临时 pyserial raw probe 发送 vendor 命令：
  - `{"T":143,"cmd":0}`
  - `{"T":142,"cmd":100}`
  - `{"T":131,"cmd":1}`
  - `{"T":130}`
- 读取并保存至少 10 秒 raw UART lines。
- 如果出现 `T=1001` 且字段包含 `L/R/r/p/y/v`，再启动 ROS2 `esp32_bridge` 并采集 `/battery`、`/imu/data`。
- 结束后恢复 `upper_robot_api.py` 并验证 `/api/base/status`。

## Owner

- 主责：`robot-hardware-engineer`
- 如 raw 有 `T=1001` 但 ROS topic 无样本，再由主节点派 `robot-software-engineer` 修 bridge/parser；本轮硬件 agent 不改产品代码。

## 资料来源

必须引用：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

采用事实：

- UART 使用 UTF-8 newline-delimited JSON。
- `CMD_BASE_FEEDBACK = T=130`。
- `CMD_BASE_FEEDBACK_FLOW = T=131`。
- `CMD_FEEDBACK_FLOW_INTERVAL = T=142`。
- `CMD_UART_ECHO_MODE = T=143`。
- `FEEDBACK_BASE_INFO = T=1001`，字段应包含 `L/R/r/p/y/v`。

## 安全边界

- 本轮不发送运动命令，不发布 `/cmd_vel`。
- 只停止 `upper_robot_api.py` 释放 `/dev/ttyS5`。
- raw probe 只发送 feedback/echo/interval 命令。
- 结束必须恢复 `upper_robot_api.py`。

## 验收口径

通过条件：

- raw UART probe 捕获至少一条 `T=1001` 且包含 `L/R/r/p/y/v`。
- 若 raw feedback 通过，ROS2 `/battery` 和 `/imu/data` 至少各有一条样本。
- API 恢复成功。

部分完成：

- raw 无 `T=1001`：记录所有 raw line、serial open 状态、命令写入日志、超时结果，结论定位为下位机/串口 feedback 层未闭环。
- raw 有 `T=1001` 但 ROS topic 空：记录为 ROS bridge/parser 发布链问题，后续交给软件 owner。
