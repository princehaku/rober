# WAVE ROVER Current Stop Path Readiness

本页记录 `current stop path` 的离线 readiness 合同。它服务于 O1/O3 下一步真实
HIL 前的停车链路准备，不等于真实上车停车、safe-to-control、route execution 或 delivery。

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`

## 已证实的本地资料事实

- UART/JSON framing：vendor `base_ctrl.py` 使用 `json.dumps(data) + "\n"` 写入 UTF-8 bytes，固件 `uart_ctrl.h` 在收到 `\n` 后解析完整 JSON。
- Vendor RPi 示例串口：`base_ctrl.py` 示例为 `/dev/ttyAMA0` at `115200`，并注释 `/dev/serial0` at `115200`；Orange Pi 真实设备名本轮不硬编码。
- `T=1` 是 `CMD_SPEED_CTRL`，zero-stop 形态为 `{"T":1,"L":0,"R":0}`。
- `T=11` 是 `CMD_PWM_INPUT`，zero-stop 形态为 `{"T":11,"L":0,"R":0}`。
- `T=13` 是 `CMD_ROS_CTRL`，zero-stop 形态为 `{"T":13,"X":0,"Z":0}`。
- heartbeat 来源：`uart_ctrl.h/json_cmd.h` 对 `T=1`、`T=11`、`T=13` 会刷新 `lastCmdRecvTime`；`ugv_config.h` 默认 `HEART_BEAT_DELAY=3000`；`movtion_module.h` 的 `heartBeatCtrl()` 超时后调用 `setGoalSpeed(0,0)`。

## 离线 readiness 合同

生成工具：

```bash
python3 -m ros2_trashbot_hardware.wave_rover_stop_path_readiness \
  --output sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json
```

artifact schema：

- `trashbot.o1.current_stop_path_readiness.v1`

必须固定的 endpoint / guard：

- stop endpoint：`/api/base/stop`
- no `/api/base/manual`
- no `/cmd_vel`
- no NavigateToPose
- no Nav2 controller/BT
- no real UART
- no nonzero motion

必须固定的 safety/control fields：

- `safe_to_control=false`
- `hil_pass=false`
- `route_execution_success=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `nonzero_motion_command_sent=false`
- `uses_real_uart=false`

## 证据边界

本轮只证明：

- `/api/base/stop` 的 stop-only 合同可以离线表达；
- WAVE ROVER vendor 三类 zero-stop command plan 可编码成 newline-delimited UTF-8 JSON；
- mock/虚拟串口回放能验证每条 frame 是 JSON object、以 `\n` 结尾，且 `L/R/X/Z` 全为 0；
- artifact 可由程序读取并被验收脚本检查。

本轮不证明：

- 真实 UART 已打开或被 WAVE ROVER ESP32 接收；
- 真实 heartbeat 已触发；
- 真实 `/api/base/stop` 已在上车环境执行；
- current live HIL pass；
- safe-to-control；
- NavigateToPose/Nav2 controller route execution；
- delivery/operator acceptance。

## 下一步履约动作

1. 现场 explicit operator approval 后，记录 current live `/api/base/stop` 调用和同窗口 UART frame capture。
2. 在真实 WAVE ROVER 上采集 stop 前后 `T=1001` feedback，证明 stop 后 wheel feedback 归零。
3. 与同窗口 `/scan`、`/amcl_pose`、`/tf`、`/map` readiness 一起形成 HIL 准入记录。
4. 只有 HIL 准入、stop path、Nav2/controller result 和 operator acceptance 同时存在后，才能推进 route execution 或 delivery 证据。
