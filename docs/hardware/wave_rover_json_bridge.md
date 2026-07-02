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
- `evidence_ref` 建议使用 `run_<YYYYMMDDTHHMMSS>Z_<serial>_hil_pass_speed<speed>_dur<duration>`，同一次实机 run 在 checklist、脚本输出与 task record 中保持一致。

- 阻塞标记（本轮）：
  - `run_20260511T093000Z_ttyUSB0_hil_pass_speed0p050_dur0p30` 因 `/dev/ttyUSB0` 不存在未能完成 `T=143/142/131` 与 `T=1001` 采样
  - `run_20260511T063559Z_-dev-ttyUSB0_hil_pass_speed0p050_dur0p30` required command set executed; `--move-test` blocked at serial open and未产出 run packet 文件

## UART Framing

官方 WAVE ROVER ESP32 固件使用一行 JSON（UTF-8）并以 `\n` 结束。

- 厂商 Raspberry Pi 示例设备路径：`/dev/ttyAMA0` / `/dev/serial0`
- Orange Pi 上下文必须以 `ls /dev/tty*` / `ls /dev/serial*` 现场确认 UART 路径；不得直接照抄 Raspberry Pi 示例路径。

## Command Table

| ROS bridge use | Vendor JSON | Direction | Source |
| --- | --- | --- | --- |
| Stop / left-right speed command | `{"T":1,"L":0.0,"R":0.0}` | ROS to ESP32 | `json_cmd.h` `CMD_SPEED_CTRL`, `base_ctrl.py` |
| PWM command mode (`T=11`) | `{"T":11,"L":164,"R":164}` | ROS to ESP32 | `json_cmd.h` `CMD_PWM_INPUT`, `uart_ctrl.h` |
| Velocity command mode (`T=13`) | `{"T":13,"X":0.1,"Z":0.3}` | ROS to ESP32 | `json_cmd.h` `CMD_ROS_CTRL`, `movtion_module.h` |
| One-shot base feedback request | `{"T":130}` | ROS to ESP32 | `json_cmd.h` `CMD_BASE_FEEDBACK` |
| Feedback stream on/off | `{"T":131,"cmd":1}` / `{"T":131,"cmd":0}` | ROS to ESP32 | `json_cmd.h`, `uart_ctrl.h` |
| Feedback interval set | `{"T":142,"cmd":100}` | ROS to ESP32 | `json_cmd.h`, `uart_ctrl.h`, `ugv_advance.h` |
| UART echo off/on | `{"T":143,"cmd":0}` / `{"T":143,"cmd":1}` | ROS to ESP32 | `json_cmd.h`, `uart_ctrl.h` |
| Base feedback frame | `{"T":1001,"L":...,"R":...,"r":...,"p":...,"y":...,"v":...}` | ESP32 to ROS | `json_cmd.h` `FEEDBACK_BASE_INFO`, `ugv_advance.h` |

### Feedback fields 与采样频率

- 关键字段：`L`,`R`,`r`,`p`,`y`,`v`（`T=1001`）需齐备。
- 真实上车 smoke 已观测到 `y` 可能返回 JSON `null` 或字符串 `"null"`；项目侧将其解释为 `yaw unavailable`，而不是整帧无效。
- `configure_feedback` 默认发送序列：`{"T":143,"cmd":0}` -> `{"T":142,"cmd":<interval_ms>}` -> `{"T":131,"cmd":1}`。
- 建议在 `source=hil_pass` 下采样至少 2 帧 `T=1001`，确认采样间隔接近 `feedback_interval_ms`（例如 100ms 时约 10Hz）。
- `v` 默认映射为电压；`r/p/y` 为欧拉角（厂商原始值按项目桥接代码按弧度发布 yaw）。

### Feedback debug JSONL

- `feedback_debug_log_path` 默认为空字符串，默认不写文件、不改变 `/imu/data`、`/battery`、`/odom` 或 `odom -> base_link` TF 行为。
- 当 `feedback_debug_log_path` 非空时，`esp32_bridge` 在每个已解析有效的 vendor `T=1001` 帧后追加一行 JSONL，用于上车 bounded motion evidence。
- 单行 schema 为 `trashbot.wave_rover.feedback_debug.v1`，字段包含 `observed_at_unix_s`、`source=wave_rover_uart_t1001`、`left_speed`、`right_speed`、`roll`、`pitch`、`yaw`、`yaw_available`、`voltage`。
- 2026-06-29 16:55 CST 起，debug 行同时保留 `vendor_frame={"T":1001,"L":...,"R":...,"r":...,"p":...,"y":...,"v":...}`。这是 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER `FEEDBACK_BASE_INFO` 原始字段快照，用于 Nav2/O11 复验时判断 `L/R=0` 是厂商帧真实返回还是项目别名解析问题；它不能替代同窗口 `left_speed/right_speed` 非零验收。
- 2026-06-29 17:05 CST 起，ROS 手控和 PC 键盘短 pulse 不再为了证明轮速另开 UART；若 `wave_rover_feedback_debug.jsonl` 仍 fresh 且包含 `T=1001`，上位机只把这些 bridge-owned 帧包装为 `base_feedback_samples_latest`。这样多人 PC 页面和 summary 能看到同一组 wheel raw `L/R`，但 `safe_to_control=false`、`delivery_success=false`、`hil_pass=false` 必须保持不变；`L/R=0/0` 也必须原样显示为“未证明非零”。
- 2026-07-03 CST 起，`/api/base/manual` 的 ROS/bridge_debug 手控路径会把 fresh bridge-owned `T=1001` 帧同时挂回本次 `feedback_during_motion`。这是为了让 PC first-jog/WASD 结果显示“运动窗口内读到了多少 T1001 帧”和最新 wheel raw `L/R`，避免串口由 `esp32_bridge` 持有时误报 0 帧；它仍不发送额外 `T=130`，也不把 `L/R=0/0`、IMU 姿态变化或命令到达升级成 wheel 非零、HIL pass、Nav2 成功或 delivery success。
- 该日志复用 bridge 已拥有的串口 owner 和解析结果，避免 direct raw UART 抢读造成 corrupted/incomplete JSON。
- 写入失败只记录 runtime warning；不得阻塞 `/imu/data`、`/battery` 或 `/trashbot/stop`。路径目录、权限和磁盘空间需在上车 run 前由 operator 确认。
- `left_speed/right_speed` 采用 vendor `T=1001.L/R` 原始反馈口径，只能作为 evidence/debug 材料；在缺少 HIL 对齐前，不代表导航级实测轮速里程计。

### Upper Robot API status feedback ack

- `onboard/scripts/upper_robot_api.py` 的 `/api/base/status.feedback_ack` 只表示 API 通过非运动 `{"T":130}` readback 或 fresh samples artifact 看到了 vendor `T=1001`。
- `/api/base/status` 允许发送 `T=130` 只读反馈请求；它不得发送 `T=1`、`T=13`、`T=131`、`/cmd_vel` 或 `/api/base/manual`，也不得把 `safe_to_control`、`primary_actions_enabled`、`robot_control_executed` 置为 true。
- `feedback_ack.t1001_observed=true` 的来源必须写入 `source`：`fresh_readback` 表示本次 status 调用短窗口读回，`fresh_artifact` 表示 samples artifact 未过期且包含 `T=1001`。stale artifact 只能作为历史材料摘要，不能抬高 ACK。
- ACK 识别只依赖 vendor `T=1001` 帧身份；`y` 为 JSON `null` 或字符串 `"null"` 只代表 yaw unavailable，不能导致整帧被丢弃。
- 该字段不是 ROS `/odom`、`/imu/data`、`/battery` 的对齐证明，也不是导航级 HIL pass；真实运动、轮向、里程计和电池/IMU 对齐仍按 run 级 HIL 证据归档。

### 2026-06-12 PC feedback samples proxy 实测

在真实上位机 `root@192.168.1.11:37878` 上，本轮通过 direct upper API 和 PC workstation proxy 各执行一次短批量 `T=130` 反馈采样：

- Direct upper：`POST /api/base/feedback-samples`，body 为 `sample_count=3`、`sample_interval_s=0.15`、`read_timeout_s=0.25`、`read_window_s=0.35`。
- PC proxy：`POST /api/robot-control/base/feedback-samples?baseUrl=http://192.168.1.11:8787`，浏览器侧 body 为空，固定 body 由 Node 后端生成。
- 两次结果均观察到 vendor `T=1001`，PC proxy 摘要为 `completed_sample_count=3`、`t1001_observed_count=3`、`feedback_ack_t1001_observed=true`、`observed_feedback_types=[1001]`。
- 该路径只发送 `T=130` 只读反馈请求，`sends_motion_commands=false`、`robot_control_executed=false`，不得作为轮速非零、真实运动、HIL pass 或手动点动放行证据。

### 2026-06-27 PC latest nonzero wheel readback boundary

本轮继续采用 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER 资料口径：
`T=1001.L/R` 是 vendor base feedback 原始轮速字段。PC Node 会把上位机
`/api/base/feedback-samples/latest.latest_result.wheel_feedback_summary.latest_nonzero_pair`
提升为 `readback_summary.base.wheel_feedback_latest_nonzero_left_speed/right_speed`，
用于解释“底盘只读链路曾出现非零 L/R”。该字段不得替代 Nav2 goal execution 同窗口内的
`base_feedback_summary.latest_nonzero_pair`，也不得单独推出路线到达、delivery success 或导航级 HIL pass。

### 2026-07-03 PWM164 default command mode boundary

本轮按 `docs/vendor/VENDOR_INDEX.md` 指向的本地资料复核：
`WAVE_ROVER_V0.9/json_cmd.h` 定义 `T=13` 为 `CMD_ROS_CTRL`，字段为 `X/Z`
并标注 `(m/s,rad/s)(Not for the products without encoders)`；`T=11` 定义为
`CMD_PWM_INPUT`，vendor 示例为 `{"T":11,"L":164,"R":164}`，`uart_ctrl.h`
在收到 `CMD_PWM_INPUT` 后关闭 PID compute 并直接调用左右电机控制。

2026-07-03 真机 smoke 复核：`ros/T=13` 路径能收到 `/cmd_vel`，但 vendor
`T=1001.L/R` 持续 `0/0`；同一底盘改用 `T=11`、`PWM164` 后，`T=1001.L/R`
仍可能为 `0/0`，但同窗口 `T=1001.r/p` 姿态出现明显变化，证明底盘存在运动信号。
因此当前 bringup/autonomous、硬件 bridge 和 O11 Nav2 helper 默认使用
`command_mode=pwm`、`pwm_min_abs/max_abs=164`，仍以 ROS `/cmd_vel` 作为上层控制面，
只在落到 WAVE ROVER 串口时映射为 vendor `T=11`。

`ros/T=13` 和 `speed/T=1` 仍保留为白名单诊断模式；如果后续固件/编码器状态修复并通过
HIL 证明 `T=13` 可产生可靠 wheel raw L/R，再重新评估默认值。

该改动只改变上位机托管 `esp32_bridge` 的命令模式选择和 launch 默认参数，不降低验收标准：
Nav2 goal 只有在同一 execution artifact 内同时满足 action succeeded 和可复核的底盘运动材料时，
才能被 PC/上位机视为路线执行证明；wheel raw `T=1001.L/R` 非零仍作为独立字段展示，不能被
IMU 姿态变化伪装。

### 2026-07-03 runtime tuning and zero-wheel boundary

`esp32_bridge` 支持运行中用 ROS 参数调整 `command_mode`、`track_width_m`、
`max_wheel_speed_mps`、`pwm_min_abs`、`pwm_max_abs`、`feedback_debug_log_path`
和 `command_debug_log_path`。参数回调先复用启动参数校验，非法 `pwm_min_abs/pwm_max_abs`
会拒绝并保持旧值；合法调参会写入 `wave_rover_command_debug.jsonl`，其中
`source=esp32_bridge_runtime_parameter_callback` 且 `sends_motion=false`，用于把现场
PWM 试跑和后续 wheel 反馈对齐。

2026-07-03 04:05 CST 上位机实测：

- `ros2 param set /esp32_bridge pwm_min_abs 260` 被拒绝，当前值保持 `164`。
- `pwm_min_abs/max_abs=220` 后，PC first-jog 通过 `/cmd_vel` 发送多帧
  `{"T":11,"L":220,"R":220}` 并自动 stop，`T=1001.L/R` 仍为 `0/0`。
- `pwm_min_abs/max_abs=255` 后，PC first-jog 发送多帧 `{"T":11,"L":255,"R":255}`
  并自动 stop，`T=1001.L/R` 仍为 `0/0`。
- `command_mode=speed` 后，PC first-jog 发送 `{"T":1,"L":0.061538,"R":0.061538}`，
  `T=1001.L/R` 仍为 `0/0`。
- `command_mode=ros` 后，PC first-jog 发送 `{"T":13,"X":0.08,"Z":0.0}`，
  `T=1001.L/R` 仍为 `0/0`。

因此当前证据只证明 PC/Robot API/ROS `/cmd_vel`/bridge/UART JSON 命令链路和自动
stop 链路可用；不能证明 wheel raw 非零或真实物理移动。后续排障应优先检查 WAVE ROVER
电机使能、底盘模式、下位机固件状态、驱动供电和反馈字段语义，而不是继续把 PC 键盘或
ROS 发布链路当成首要 blocker。

### 2026-07-03 HTTP command transport and speed-rate reset

按 `docs/vendor/VENDOR_INDEX.md`、`ugv_rpi/config.yaml`、`json_cmd.h`、`uart_ctrl.h`
和 `movtion_module.h` 复核，厂商固件提供 `T=138` 设置左右速度倍率、`T=139` 读取速度倍率、
`T=140` 保存速度倍率；`T=1` 和部分电机控制路径会受该倍率影响。现场 ESP32 HTTP
`/js?json=...` 已可访问，`T=139` 一度返回 `{"T":139,"L":0,"R":0}`，说明速度倍率被置为
0。执行 `{"T":138,"L":1,"R":1}` 后，`T=139` 返回 `L=1,R=1`。

因此 `esp32_bridge` startup config 现在在 `T=900 main/module` 后追加非运动
`{"T":138,"L":1,"R":1}`，再执行 `T=143/T=142/T=131`。这条配置只恢复厂商速度倍率，不发车，
也不能替代电机/轮速验收。

同轮现场把 `esp32_bridge` 切到 `command_transport=http`、`wave_rover_http_base_url=http://192.168.1.3`
后，PC 手控经 `/cmd_vel` 产生多帧 `T=11 L/R=255`，command debug 记录
`command_transport=http`、`http_write_returned=true`、`transport_write_returned=true`。direct HTTP
`T=1 L/R=0.39` 和 bridge HTTP PWM pulse 均能观察到 IMU roll/pitch 明显变化，但
`T=1001.L/R` 仍保持 `0/0`。当前证据只能说明 ESP32 HTTP 命令链路和运动扰动存在，不能升级为
wheel raw 非零、编码器 HIL pass、Nav2 路线成功或 delivery success；后续仍需复核电机使能、
底盘模式、固件版本、驱动供电和 `T=1001` 反馈语义。

### HIL 运行参数留存模板（与 run 级证据绑定）

- 每次 `source=hil_pass` 运行前需记录参数快照：
  - `serial_port`
  - `baudrate`
  - `feedback_interval_ms`
  - `test_speed`
  - `test_duration_s`
  - `ros_angular_z`
  - `turn_angular_z`
  - `run_flags`
- 同步写入脚本输出里的 `evidence_ref` 字段，作为该 run 的唯一入口。

## Command Modes

- `ros`：将 `/cmd_vel` 映射为 vendor `T=13` 的 `X/Z`，当前仅作为显式诊断 override。
- `speed`：将 `/cmd_vel` 映射为 `T=1` 的 `L/R`，仅作为显式诊断 override。
- `pwm`：将 `/cmd_vel` 映射为 `T=11` 的 `L/R`，当前 bringup/autonomous、硬件 bridge 与 O11 helper 默认值为 `PWM164`。

默认切到 `pwm` 的原因是 Nav2、键盘连续手控和自由移动仍以 ROS `/cmd_vel` 为同一上层控制面，
但当前 WAVE ROVER 固件/硬件组合对 `T=13` 的 wheel raw 反馈持续为零；vendor `T=11/PWM164`
已在 2026-07-03 现场烟测中产生同窗口 IMU 运动信号。真实路线执行仍必须保存 action、命令、
feedback 与运动材料，且 wheel raw `T=1001.L/R` 非零状态必须单独展示。

对于 `speed` 模式，差速关系：

```text
left_mps = linear.x - angular.z * track_width_m / 2
right_mps = linear.x + angular.z * track_width_m / 2
```

`speed` 诊断模式在项目侧将 `T=1` 值按 `max_wheel_speed_mps` 归一化并夹到 `[-1,1]`，该参数是可调的项目参数，不能当作硬件标称校准值。

### 2026-06-10 低速起动阈值边界

真实上位机 `root@192.168.1.11:37878` 的 bounded probe 已通过 ROS2
`esp32_bridge` + `/cmd_vel` 路径发送 `linear.x=0.03/0.05/0.07/0.09m/s`，
每步 publish window 均小于 `0.18s`，且每步 `/trashbot/stop` 成功。

2026-06-27 真机 smoke 曾单独观测到 `T=11 L=90/R=90` 回 `T=1001 L/R=90/90`，
但同轮 Nav2 托管执行里 `T=11 L=90/R=-90` 仍未形成非零轮速闭环。2026-07-03 复测后，
当前默认不再使用 vendor ROS/T=13 控制路径，而是保留 ROS `/cmd_vel` 上层控制面并由
bridge 落成 `T=11/PWM164`；`command_mode=ros` 与 `command_mode=speed` 只作为显式
HIL/诊断 override。在 `command_mode=speed` 诊断模式下，
`max_wheel_speed_mps=1.3`
对应 expected command：

- `0.03m/s -> {"T":1,"L":0.023077,"R":0.023077}`
- `0.05m/s -> {"T":1,"L":0.038462,"R":0.038462}`
- `0.07m/s -> {"T":1,"L":0.053846,"R":0.053846}`
- `0.09m/s -> {"T":1,"L":0.069231,"R":0.069231}`

这些值只代表项目公式计算出的 expected JSON，不是 WAVE ROVER 反馈。该 probe 的
WAVE ROVER `T=1001` feedback debug 仍未观测到 `left_speed/right_speed` 非零，
LiDAR median delta 也低于 `0.03m` 证明阈值。因此截至本记录，`T=1 L/R<=0.069231`
不能写成已证明的物理起动区间；后续需人工在场复核电机供电、急停、模式、底盘架空状态，
再决定是否做更高 PWM/速度的受控 HIL。

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
- `publish_odom_tf`
- `feedback_debug_log_path`

参数校验要求：`track_width_m > 0`、`max_wheel_speed_mps > 0`、`feedback_interval_ms >= 0`、`odom_publish_hz > 0`。`publish_odom_tf` 是布尔开关，默认 `true`，仅控制是否把同源 command integration `/odom` 同步广播为 `odom -> base_link` TF。
`feedback_debug_log_path` 是默认关闭的 evidence/debug 文件路径；非空时追加 JSONL，写入失败仅 warning。

## Code Structure

本轮 hardware 包已按“协议纯函数 / 反馈解析 / 参数处理 / ROS glue / 兼容入口”拆分：

- `ros2_trashbot_hardware/wave_rover_protocol.py`
  - 负责 WAVE ROVER JSON command ID、newline-delimited UART frame 编码、`/cmd_vel` 到 `T=1` / `T=11` / `T=13` 的命令构造，以及 `T=143 -> T=142 -> T=131` 的启动配置帧。
  - 只采用 `base_ctrl.py`、`json_cmd.h`、`uart_ctrl.h`、`movtion_module.h` 中已有的协议事实，不打开串口、不 import ROS2。
- `ros2_trashbot_hardware/wave_rover_feedback.py`
  - 负责 `T=1001` feedback parser 与 IMU degrees-to-radians 转换。
  - `r/p/y` 角度单位来自 `IMU.cpp` 中 `57.3` multiplier；进入 ROS yaw 四元数前必须转为 radians。
- `ros2_trashbot_hardware/bridge_config.py`
  - 负责声明和校验 `serial_port`、`serial_baudrate`、`command_mode`、`track_width_m`、`max_wheel_speed_mps`、`feedback_interval_ms`、`odom_publish_hz`。
  - `port` / `baudrate` 只保留兼容别名；Orange Pi 真实串口路径仍需现场确认。
- `ros2_trashbot_hardware/esp32_bridge_node.py`
  - 唯一负责打开 UART、订阅 `/cmd_vel`、发布 `/odom`、`/imu/data`、`/battery`、提供 stop/reset/beep service 的 ROS runtime 层。
  - `/odom` 仍是 command integration；`/imu/data` 仍只发布 `T=1001.y` 对应 yaw；`/battery` 仍只发布 `T=1001.v` 电压。
- `ros2_trashbot_hardware/esp32_bridge.py`
  - 保留原 console script 和历史测试 import 入口，只 re-export 上述模块能力并启动 ROS lifecycle。

这个拆分只提升代码结构和证据可读性，不新增 `source=hil_pass`。真实 WAVE ROVER、真实 UART、轮向、速度单位、反馈频率、IMU/Battery 对齐仍必须通过 HIL packet 与 operator report 补齐。

## Published ROS Contracts

### `/odom`

当前实现基于最近一次 `/cmd_vel` 的指令积分计算（未使用轮速闭环），未经过独立编码器融合校验。故 `/odom` 在证据上应标注 `source=command_integration` 并由 HIL 的第一轮 run 带 `source=hil_pass` 重验。

### `odom -> base_link` TF

当前 bridge 可选发布动态 `odom -> base_link` TF，内容与同周期 `/odom` 的 pose 完全一致，默认由 `publish_odom_tf=true` 开启。这个 TF 仅用于补齐 ROS 拓扑和下一轮 integrated capture 对 `no_motion_static_odom_tf` 的依赖解除，不代表实测轮速、编码器或导航级里程计；真实上车时仍必须把 `/odom` topic 与 TF 一起按 `source=command_integration` 口径留证。

### `/imu/data`

当前仅发布 yaw 四元数（`T=1001` 的 `y`），`r/p` 虽在反馈帧内但未进入 ROS 消息。
若真实反馈里的 `y` 为 JSON `null` 或字符串 `"null"`，bridge 仍发布 IMU 样本，但设置 `orientation_covariance[0] = -1.0`，明确表示 orientation unavailable，避免伪造 yaw。
HIL run 必须在报告中说明：`/imu/data` 与 `T=1001.y` 一一对应（以 `evidence_ref` 绑定）。

### `/battery`

当前仅发布电压（来自 `T=1001.v`）。只要 `v` 存在且是 finite 数值，即使 `y` unavailable，也必须继续发布 `/battery`。不提供当前、SOC、容量与电芯信息。
HIL run 需记录 `T=1001.v` 与 `/battery` 取样对齐证据。

## 2026-06-22 first-jog in-motion feedback boundary

本轮按 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER 本地资料复核协议来源：
`ugv_rpi/base_ctrl.py`、`WAVE_ROVER_V0.9/json_cmd.h`、`movtion_module.h`、
`uart_ctrl.h`。采用的协议边界仍是 newline JSON UART，项目现场串口为
`/dev/ttyS5 @ 115200`；vendor Raspberry Pi 示例里的 `/dev/ttyAMA0` 只作为资料来源，
不能直接写成 Orange Pi 现场路径。

上位机 `/api/base/manual` 现在在非 stop 点动命令写入成功后，会在运动窗口内发送一次
`T=130` feedback request 并读取 `T=1001`，再执行 `{"T":1,"L":0,"R":0}` stop，
最后保留停车后反馈。`manual_wheel_feedback_summary` 会合并运动窗口和停车后帧，
只有同一 `T=1001` 帧内 `L/R` 都是 finite 且非零时，才把
`wheel_feedback_lr_nonzero_proven=true`。

真实上位机 `root@192.168.1.11:37878`、Robot API `http://192.168.1.11:8787`
本轮诊断结果：

- PC first-jog `speed=0.04,duration_ms=800`：命令转发成功，运动窗口反馈已尝试，但
  `T=1001 L/R=0/0`。
- 直连上位机 `T=1` speed command：`{"T":1,"L":0.12,"R":0.12}` 写入成功并 stop，
  运动窗口内与停车后 `T=1001 L/R=0/0`。
- 直连 UART `T=13` ROS command：`{"T":13,"X":0.1,"Z":0}` 与 `{"T":130}` 写入成功，
  `T=1001 L/R=0/0`。
- 直连 UART `T=11` PWM command：`{"T":11,"L":60,"R":60}` 与 `{"T":130}` 写入成功，
  `T=1001 L/R=0/0`。

这些结果说明软件侧已经覆盖“运动窗口内采样”这一证据缺口，但尚未证明真实 wheel raw
L/R 非零。下一步必须在人工在场条件下检查电机供电、急停、底盘模式、轮子是否离地、
固件是否需要额外使能，以及 `T=1001 L/R` 是否在当前固件中代表实时轮速。

## 2026-06-22 same-session manual transaction proof

继续依据 `docs/vendor/VENDOR_INDEX.md`、`ugv_rpi/base_ctrl.py`、`json_cmd.h`、
`uart_ctrl.h`、`movtion_module.h` 和 `ugv_advance.h` 复核：vendor `baseInfoFeedback()`
返回的 `T=1001 L/R` 来自 `speedGetA/speedGetB`。因此运动窗口内读到同帧非零 `L/R`
可以作为 wheel raw feedback material；停车后读到 `0/0` 只说明 stop 后轮速清零，
不能覆盖运动窗口内的非零帧。

上位机 `/api/base/manual` 已改成同一个串口会话内完成点动事务，避免打开/关闭串口或独立
`T=130` 会话造成读窗错位。真实上位机 `root@192.168.1.11:37878` 验证：

- 直连 `/api/base/manual`，`speed=0.12,duration_ms=800`：
  - command compact frame：`{"T":1,"L":0.12,"R":0.12}`
  - motion feedback：`{"T":1001,"L":61,"R":61,...}`
  - stop compact frame：`{"T":1,"L":0,"R":0}`
  - after-stop feedback：`{"T":1001,"L":0,"R":0,...}`
- PC first-jog，`speed=0.04,duration_ms=800`：
  - `remote_motion_key_values.wheel_feedback_lr_nonzero_proven=true`
  - `wheel_feedback_latest_left_speed=20`
  - `wheel_feedback_latest_right_speed=20`

这个证据把上一节“wheel raw L/R 非零未证明”更新为：在受控 first-jog/manual 点动中，
WAVE ROVER `T=1001 L/R` 非零已经可被上位机和 PC proxy 读取。它仍不是完整 HIL 通过：
本轮没有证明 Nav2 NavigateToPose 真实执行、路线到达、垃圾投放或 delivery success。

## 2026-07-03 PC manual speed alias and PWM255 recheck

本轮继续按 `docs/vendor/VENDOR_INDEX.md`、
`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py` 与
`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h` 复核 WAVE ROVER 控制协议。
底盘运动命令仍采用 vendor newline JSON；现场串口仍是 `/dev/ttyS5 @ 115200`。`T=11`
是 PWM 输入，`T=13` 在 vendor 文件中标注为不适用于无编码器产品，因此当前 PC/WASD
默认通过 ROS `/cmd_vel` 到常驻 `esp32_bridge`，再由 bridge 输出 `T=11` PWM。

PC 固定代理 `/api/robot-control/base/manual` 现在同时接受 `speed` 与 `speed_mps`。
兼容 `speed_mps` 是为了外部脚本按响应字段名调用时不再被判成
`manual_request_invalid_numbers`；转给上位机 `/api/base/manual` 的 body 仍保持
`speed`，避免改变上位机合同。

2026-07-03 05:32 CST 真实上位机 `root@192.168.1.11:7878`、PC Node
`0.0.0.0:7001` 复测：

- PC 手控 body `{"direction":"forward","speed_mps":0.05,"duration_ms":500,
  "command_mode":"ros","feedback_mode":"realtime","confirm_hil_checklist":true}` 返回
  `proxy_status=command_forwarded`、`remote_http_status=200`、`requested_speed_mps=0.05`
  和 `clamped_speed_mps=0.05`。上位机 `remote_motion_key_values` 中
  `manual_command_executed=true`、`auto_stop_executed=true`。
- 常驻 `esp32_bridge` 命令日志写出多帧 `{"T":11,"L":255,"R":255}`，随后写出
  `{"T":11,"L":0,"R":0}` stop。
- 同窗口与后续 `T=1001` 反馈仍为 `L/R=0/0`。因此本轮证明 PC/API/ROS
  `/cmd_vel`/bridge/UART 命令链路和自动停车链路可达，但不能把 wheel raw 非零、
  物理移动、HIL pass、Nav2 成功或 delivery success 标记为完成。

## Run-time Validation Checklist

- 确认 Orange Pi 串口与波特率（不要复用 Raspberry Pi 示例路径）。
- 停止命令 `T=1,L=0,R=0` 生效且运动停止。
- 启动前确认已下发 `T=143`、`T=142`、`T=131`。
- 低速 `T=1` 前进、倒退、转向方向验证通过（由 HIL 填写）。
- 采集至少两帧 `T=1001` 并核对 `L/R/r/p/y/v`。
- 只在停稳和 `T=1` 安全后再尝试 `T=13`。
- 下发顺序与间隔复验通过后，才允许把 run 标记为 `hil_pass`。

## 2026-07-03 UART TX receive probe tool

本轮继续采用 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER
`json_cmd.h`、`uart_ctrl.h` 与 `movtion_module.h`。Vendor 固件只在 `Serial`
收到以 `\n` 结尾的 JSON 后才会进入 `jsonCmdReceiveHandler()`；其中 `T=143`
可打开命令回显，`T=139` 会返回速度倍率，`T=131` 控制 `T=1001` 连续反馈。

新增 `onboard/scripts/wave_rover_uart_tx_probe.py`，用于现场把“上位机 write 返回成功”和
“ESP32 确实解析命令”分开验证：

- 默认先用 `lsof` 检查 `/dev/ttyS5` 是否被常驻 `esp32_bridge` 占用；占用时返回
  `status=port_held`，不抢串口。
- 串口空闲时只发送非运动 `T=143/T=139/T=900/T=131`，并读取同窗口反馈；只有看到
  `T=139` 查询响应才设置 `esp32_receive_confirmed=true`。
- 只有显式传 `--motion-test` 才会发送短 `T=11` PWM 脉冲，`finally` 中固定发送
  `T=11/T=1/T=13` 三类 stop。

2026-07-03 07:30 CST 真机复测：停掉 `esp32_bridge` 后运行该 probe，可连续读到
`T=1001`，但 `after_T_143`、`after_T_139`、`after_T_900`、`after_T_131` 窗口均没有
查询响应，也没有 wheel L/R 非零，因此 `status=no_command_response`、
`esp32_receive_confirmed=false`。这说明当前 blocker 不是 PC/ROS2 没发，而是
上位机 TX 到 ESP32 RX 接线、pinmux 或固件 UART receive 路径尚未打通。
