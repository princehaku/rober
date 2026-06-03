# O1 Base Manual Turn Smoke Runbook

## 目标

现场反馈“左右转还不行”时，本 runbook 用来复核 WAVE ROVER `/api/base/manual` 左右转点动链路。当前结论不是改 PC UI，而是先确认 onboard `T=1` 左右轮速度映射、真实轮子方向、停车兜底和 `T=130 -> T=1001` 回读材料。

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
  - WAVE ROVER 上下位机链路是 UART newline-delimited JSON；Orange Pi 串口路径必须现场确认。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `base_speed_ctrl(input_left, input_right)` 发送 `{"T":1,"L":input_left,"R":input_right}`。
- `docs/vendor/waveshare_wave_rover/ugv_rpi/templates/control.js`
  - 官方 Web 控制纯左转使用 `L=-max_speed,R=+max_speed`，纯右转使用 `L=+max_speed,R=-max_speed`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `CMD_SPEED_CTRL=1`，`CMD_BASE_FEEDBACK=130`，`FEEDBACK_BASE_INFO=1001`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
  - `T=1` 要求 JSON 含 `L/R` 并调用 `setGoalSpeed(L,R)`；`T=130` 调用 `baseInfoFeedback()`。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
  - 固件注释写明 `A-left, B-right`，`setGoalSpeed()` 将左输入送入左侧 PID/电机控制，右输入送入右侧 PID/电机控制。
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
  - `baseInfoFeedback()` 输出 `T=1001`，字段包含 `L/R/r/p/y/v`。

## 已证实的硬件结论

- 当前 onboard manual `left/right` 映射符合 vendor 官方 Web 控制和差速转向常识：
  - `left` -> `{"T":1,"L":-speed,"R":+speed}`
  - `right` -> `{"T":1,"L":+speed,"R":-speed}`
- `T=130` 是非运动反馈请求；期望读取到的 `T=1001` 是 vendor 底盘反馈材料，不是项目 robot ACK、HIL pass 或 `safe_to_control=true`。
- 现场左右转不明显时，优先怀疑 pulse 太短/速度太低、地面摩擦或轮子方向观察不完整；本轮没有 vendor 证据支持把 onboard 左右映射反过来。

## 现场点动建议

前置条件：

- 机器人离墙、桌脚、线缆和人员至少留出安全净空。
- 操作员在车旁看护，急停/电源开关可立即触达。
- 先确认 `GET http://192.168.1.11:8787/api/status` 返回 base `/dev/ttyS5 @115200`，并且没有把状态接口当作运动准入。
- 先执行一次 `POST /api/base/stop`，确认 stop JSON 可写。

建议参数：

- 初始左右转 pulse 使用 `speed=0.08`、`duration_ms=350`。
- 不要同时改 PC UI、不要改 wheel mapping、不要直接发 ROS `/cmd_vel`。
- 每次只测一个方向：left -> stop -> feedback；right -> stop -> feedback。

推荐命令：

```bash
curl -sS -X POST http://192.168.1.11:8787/api/base/stop
curl -sS -X POST http://192.168.1.11:8787/api/base/manual \
  -H 'Content-Type: application/json' \
  -d '{"direction":"left","speed":0.08,"duration_ms":350,"read_timeout_s":0.2,"read_window_s":1.2}'
curl -sS -X POST http://192.168.1.11:8787/api/base/stop
curl -sS -X POST http://192.168.1.11:8787/api/base/manual \
  -H 'Content-Type: application/json' \
  -d '{"direction":"right","speed":0.08,"duration_ms":350,"read_timeout_s":0.2,"read_window_s":1.2}'
curl -sS -X POST http://192.168.1.11:8787/api/base/feedback-request
```

观察记录：

- left pulse 时，左轮应后退、右轮应前进，车体应原地左转。
- right pulse 时，左轮应前进、右轮应后退，车体应原地右转。
- stop 后轮子必须停止；若 stop 不生效，立即物理急停，不继续点动。
- `manual` 响应中的 `command_result.command`、`stop_result.command`、`t1001_feedback_status`、`feedback_evidence.observed_feedback_types` 要保存。
- 回读到 `T=1001` 只记录为 vendor feedback observed；不要把它写成 HIL pass。

## 判定

- `left/right` 轮向与上表一致，但车体不转：先提高地面净空或排查轮胎打滑、负载、卡滞和底盘模式，不改映射。
- `left/right` 轮向互换：记录视频、manual response、`T=1001` 中 `L/R`，再升级为硬件安装/电机线序或固件 `SET_MOTOR_DIR/mainType` 复核，不能仅凭 PC 按钮观感改 onboard。
- `command_result.ok=false` 或 `stop_result.ok=false`：先定位 `/dev/ttyS5`、pyserial、权限和 service 状态，不继续运动。
- 没有 `T=1001`：只能说明反馈材料缺失，不等于方向一定错误；复跑 `POST /api/base/feedback-request` 和 `POST /api/base/feedback-samples`。

## 证据边界

本 runbook 是受控现场 smoke，不是完整 HIL。完成一次 left/right pulse 并观察到 `T=1001` 后，仍需要独立补齐 ROS `/odom`、`/imu/data`、`/battery`、operator HIL report、急停演练和重复运行材料，才能把 O1 从 vendor feedback material 推进到真实 HIL。
