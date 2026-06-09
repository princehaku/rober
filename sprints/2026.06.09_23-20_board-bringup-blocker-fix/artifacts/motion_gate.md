# Motion Gate 低速运动 Gate

更新时间：2026-06-10 CST

## 已读 vendor 来源

1. `docs/vendor/VENDOR_INDEX.md`
   - 明确 WAVE ROVER 上下位机链路是 UART + UTF-8 JSON + `\n`，并要求串口设备名、波特率、命令字都以本地 vendor 资料为准。
2. `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
   - vendor 上位机参考控制使用 `{"T":1,"L":...,"R":...}` 发送左右轮速度。
3. `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
   - `T=1` 是 `CMD_SPEED_CTRL`，`T=13` 是 `CMD_ROS_CTRL`，`T=130` 是 `CMD_BASE_FEEDBACK`，`T=131` 是反馈流开关。
4. 远端现场实现：`/root/rober/onboard/scripts/upper_robot_api.py`
   - API 自声明 vendor 来源就是上述三个文件；`DEFAULT_BASE_PORT="/dev/ttyS5"`、`DEFAULT_BASE_BAUDRATE=115200`。

## API endpoint 与 safe gate 结论

### endpoint

- `GET /`
- `GET /api/base/status`
- `POST /api/base/feedback-request`
- `POST /api/base/feedback-samples`
- `POST /api/base/manual`
- `POST /api/base/stop`

### safe gate

1. `GET /` 与 `GET /api/base/status` 都返回：
   - `safe_to_control=false`
   - `primary_actions_enabled=false`
2. 但远端 `upper_robot_api.py` 的 `manual_control()` 实现**没有**按 `safe_to_control` 或 `primary_actions_enabled` 拒绝 `POST /api/base/manual`。
3. `manual_control()` 的真实行为是：
   - 把 `direction` 转成 vendor `T=1` 左右轮命令；
   - 把 `speed` 限幅到 `self.max_speed`（当前 status 暴露 `max_speed=0.12`）；
   - 把 `duration_ms` 限幅到 `MAX_PULSE_MS=800`；
   - 等待短窗口后，在同一请求里无条件补一条 `{"T":1,"L":0,"R":0}` 自动停车；
   - 停车后再发送 `T=130` 采集 `T=1001` 反馈材料。
4. 因此本轮结论是：
   - **API 路由层明确允许低速 manual motion 请求进入**；
   - **但 API 回包仍固定宣告 `safe_to_control=false`，不能把这次点动视为安全放行、HIL 通过或主链路 ready。**

## 实际命令与关键输出

### 1. 查询 API root 与 base status

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "curl -s http://127.0.0.1:8787/; echo; curl -s http://127.0.0.1:8787/api/base/status; echo"'
```

关键输出摘录：

- root:
  - `safe_to_control: false`
  - `primary_actions_enabled: false`
  - `routes.base_manual: /api/base/manual`
  - `routes.base_stop: /api/base/stop`
- base status:
  - `port: /dev/ttyS5`
  - `baudrate: 115200`
  - `control_policy.mode: low_speed_pulse_with_auto_stop`
  - `control_policy.max_speed: 0.12`
  - `control_policy.max_pulse_ms: 800`
  - `control_policy.stop_command: {"T":1,"L":0,"R":0}`

### 2. 读取远端 API 源码

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "sed -n \"1,340p\" /root/rober/onboard/scripts/upper_robot_api.py"'
ssh -p 37878 root@192.168.1.11 'bash -lc "sed -n \"3388,3498p\" /root/rober/onboard/scripts/upper_robot_api.py"'
ssh -p 37878 root@192.168.1.11 'bash -lc "sed -n \"2528,2578p\" /root/rober/onboard/scripts/upper_robot_api.py"'
ssh -p 37878 root@192.168.1.11 'bash -lc "sed -n \"3720,3785p\" /root/rober/onboard/scripts/upper_robot_api.py"'
```

关键源码结论：

- `manual_control()` 会执行 `wheel_command_for_direction()`，对 `speed` 和 `duration_ms` 做限幅，然后发送 `T=1` 并自动 stop。
- `build_stop_payload()` 直接发送 `{"T":1,"L":0,"R":0}`。
- `aiohttp` router 已显式注册 `POST /api/base/manual` 与 `POST /api/base/stop`。

### 3. feedback before

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "curl -s -X POST -H \"Content-Type: application/json\" -d '\''{\"sample_count\":2,\"read_timeout_s\":0.2,\"read_window_s\":0.8,\"sample_interval_s\":0.2}'\'' http://127.0.0.1:8787/api/base/feedback-samples; echo"'
```

关键输出摘录：

- `port: /dev/ttyS5`
- `baudrate: 115200`
- `t1001_observed_count: 2`
- `all_samples_observed_t1001: true`
- `blocked_commands_not_sent: ["T=1","T=13","T=131","cmd_vel","/api/base/manual"]`

### 4. 低速点动 manual

执行条件：

- 不绕过 API；
- 不发送裸串口 `T=1/T=13`；
- `speed=0.03`，低于 status 暴露的 `max_speed=0.12`；
- `duration_ms=200`，低于 `max_pulse_ms=800`。

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "curl -s -X POST -H \"Content-Type: application/json\" -d '\''{\"direction\":\"forward\",\"speed\":0.03,\"duration_ms\":200,\"read_timeout_s\":0.2,\"read_window_s\":0.8}'\'' http://127.0.0.1:8787/api/base/manual; echo"'
```

关键输出摘录：

- `accepted: true`
- `direction: forward`
- `speed: 0.03`
- `duration_ms: 200`
- `command_result.command: {"T":1,"L":0.03,"R":0.03}`
- `stop_result.command: {"T":1,"L":0,"R":0}`
- `auto_stop_attempted: true`
- `auto_stop_executed: true`
- `manual_command_executed: true`
- `feedback_after_stop_attempted: true`
- `t1001_feedback_status: observed`
- `safe_to_control: false`
- `primary_actions_enabled: false`

说明：

- 该请求内部已经包含一次自动 stop，所以这次点动具备 API 自带停车兜底。
- 虽然 `manual_command_executed=true`，但 API 仍显式返回 `safe_to_control=false`，因此这里只能视作**受限低速点动证据**。

### 5. 显式 stop 与 feedback after

为把证据链固定在 motion 之后，本轮又顺序补了一次显式 stop 和 after feedback：

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "curl -s -X POST http://127.0.0.1:8787/api/base/stop; echo"'
ssh -p 37878 root@192.168.1.11 'bash -lc "sleep 1; curl -s -X POST -H \"Content-Type: application/json\" -d '\''{\"sample_count\":2,\"read_timeout_s\":0.2,\"read_window_s\":0.8,\"sample_interval_s\":0.2}'\'' http://127.0.0.1:8787/api/base/feedback-samples; echo"'
```

关键输出摘录：

- stop:
  - `stop_result.command: {"T":1,"L":0,"R":0}`
  - `robot_control_executed: true`
- feedback after:
  - `t1001_observed_count: 2`
  - `all_samples_observed_t1001: true`
  - `observed_feedback_types: [1001]`
  - `safe_to_control: false`
  - `primary_actions_enabled: false`

## 是否执行 motion

- **已执行**
- 方式：`POST /api/base/manual`
- 参数：`direction=forward speed=0.03 duration_ms=200`
- auto-stop：已由 `manual_control()` 内部执行
- 显式 stop：已追加执行一次 `POST /api/base/stop`
- feedback before：`2/2` 采样观测到 `T=1001`
- feedback after：`2/2` 采样观测到 `T=1001`

## blocked 根因（本轮不是 blocked，但仍有未解 gate）

1. `safe_to_control=false` 与 `primary_actions_enabled=false` 仍然存在；
2. `manual` endpoint 当前是“可调用但不宣告安全放行”的实现；
3. API 返回的 `T=1001` 证据仍被源码明确标注为：
   - vendor feedback material
   - not project robot ACK
   - not HIL proof

## 剩余风险

1. 本轮只有一次极低速、200ms 的 API 点动证据，**不等于**底盘主链路 HIL 通过。
2. `safe_to_control=false` 说明现场安全判据还没有被上位机 API 正式提升到可控态；后续 PC/手机侧仍应继续 fail-closed。
3. 这次 manual 走的是 `T=1` 左右轮速度脉冲，不是 ROS `/cmd_vel` 主链路，也不是 `T=13` 线速度/角速度映射验证。
4. 当前只证明 `/dev/ttyS5 @ 115200` 上 API 能发低速点动并在 stop 后继续读到 `T=1001`；没有同步证明 `/odom`、`/imu/data`、`/battery` 的 ROS2 发布质量。
