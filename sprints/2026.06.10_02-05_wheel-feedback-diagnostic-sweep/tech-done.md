# Wheel Feedback Diagnostic Sweep Tech Done

## sprint_type: micro

## 目标

上一轮 `feedback_debug_log_path` 已在真实上位机验证可用：`esp32_bridge` 成功写入 1592 行有效 vendor `T=1001` JSONL，且 bounded pulse 中 `/odom` 和 dynamic `/tf` 有非零 command integration。但 `T=1001.L/R` 在运动窗口仍全部为 `0.0/0.0`。

本轮目标：不新增功能代码，只做一次更有判别力的上车 wheel feedback diagnostic sweep，判断 vendor `T=1001.L/R` 全零的原因更接近：

1. 0.25s / `linear.x=0.03` 短脉冲太短或太低，采不到 encoder 速度；
2. 当前 WAVE ROVER 固件/底盘的 `speedGetA/B` 反馈不反映本项目使用的运动命令；
3. 编码器/主类型/接线/固件配置未形成可用轮速反馈。

本轮不宣称导航级 HIL，不证明真实里程计；只归档诊断证据并给下一步判断。

## Owner

- 主责：`robot-hardware-engineer`

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

采用的 vendor 事实：

- `T=1001.L/R` 来自 `ugv_advance.h::baseInfoFeedback()` 写出的 `speedGetA/speedGetB`。
- `speedGetA/speedGetB` 在 `movtion_module.h` 中由 encoder 采样或非 encoder 模式下的 `leftCtrl/rightCtrl` 赋值。
- `T=1` 是左右轮 speed control；`T=11` 是直接 PWM 输入（signed `+-255`）；`T=130` 请求 base feedback；`T=131` 控制 feedback flow。

## 允许改动范围

- `sprints/2026.06.10_02-05_wheel-feedback-diagnostic-sweep/tech-done.md`
- `sprints/2026.06.10_02-05_wheel-feedback-diagnostic-sweep/artifacts/`

范围外文件不得改动；本轮是纯证据 capture。

## 验收命令

```bash
ssh root@192.168.1.11 -p 37878 'python3 --version && test -e /dev/ttyS5'
ssh root@192.168.1.11 -p 37878 'curl -sS http://127.0.0.1:8787/api/base/status'
```

真实上位机 sweep 要求：

- 先记录 `status_before.json`。
- 只在接管 `/dev/ttyS5` 时停止 `upper_robot_api.py`；结束必须恢复并记录 `status_after.json`。
- 每段测试前启用 feedback flow，结束必须发送强制 stop：
  - `{"T":1,"L":0,"R":0}` 或 `/trashbot/stop`；
  - 如使用 direct UART，结束仍需恢复 API 并验证 fresh `T=1001` ACK。
- 建议按以下顺序执行，若现场风险不允许，写明跳过原因：
  1. `T=1` speed diagnostic：`L=0.03,R=0.03`，窗口 0.8s 以内。
  2. `T=1` speed diagnostic：`L=0.05,R=0.05`，窗口 0.8s 以内。
  3. `T=11` PWM diagnostic：`L=35,R=35`，窗口 0.25s 以内。
- 每段必须归档同一窗口的 `T=1001` JSONL/summary；如果使用 `esp32_bridge feedback_debug_log_path`，每段单独文件。
- 归档：
  - `artifacts/remote_capture/status_before.json`
  - `artifacts/remote_capture/sweep_commands.log`
  - `artifacts/remote_capture/speed_003_feedback.jsonl`
  - `artifacts/remote_capture/speed_005_feedback.jsonl`
  - `artifacts/remote_capture/pwm_35_feedback.jsonl`（如执行）
  - `artifacts/remote_capture/wheel_feedback_sweep_summary.json`
  - `artifacts/remote_capture/status_after.json`
  - `artifacts/remote_capture/upper_robot_api_restore.log`
- `wheel_feedback_sweep_summary.json` 必须写清每段 `record_count`、`nonzero_lr_count`、`max_abs_left_speed`、`max_abs_right_speed`、是否 stop 成功、是否 API restore 成功。

## 实际改动

本轮是纯证据 capture，未修改产品代码、固件、launch 参数或系统服务配置。

新增/更新证据文件：

- `artifacts/remote_capture/status_before.json`：接管 `/dev/ttyS5` 前的 `upper_robot_api` base status。
- `artifacts/remote_capture/sweep_commands.log`：远端直连串口命令、每段 motion/stop、feedback flow 开关和 restore 操作日志。
- `artifacts/remote_capture/speed_003_feedback.jsonl`：`T=1,L=0.03,R=0.03`，窗口 0.8s 内采集的 vendor `T=1001` 原始 JSONL。
- `artifacts/remote_capture/speed_005_feedback.jsonl`：`T=1,L=0.05,R=0.05`，窗口 0.8s 内采集的 vendor `T=1001` 原始 JSONL。
- `artifacts/remote_capture/pwm_35_feedback.jsonl`：`T=11,L=35,R=35`，窗口 0.25s 内采集的 vendor `T=1001` 原始 JSONL。
- `artifacts/remote_capture/wheel_feedback_sweep_summary.json`：三段统计汇总。
- `artifacts/remote_capture/status_after.json`：恢复 `upper_robot_api` 后的 base status。
- `artifacts/remote_capture/upper_robot_api_restore.log`：`trashbot-upper-robot-api.service` 恢复日志。

远端执行边界：

- 上位机：`root@192.168.1.11:37878`。
- 串口：`/dev/ttyS5`，`115200`。
- 只在 direct pyserial 接管 `/dev/ttyS5` 期间停止 `trashbot-upper-robot-api.service`。
- 每段 motion 后均发送 `{"T":1,"L":0,"R":0}` 强制 stop。
- 结束后发送 final stop，并发送 `{"T":131,"cmd":0}` 关闭 feedback flow。
- `trashbot-upper-robot-api.service` 已恢复为 `active (running)`，恢复后的 `/api/base/status` 重新观测到 vendor `T=1001`。

## 验证结果

已读 vendor 来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

已采用的 vendor 事实：

- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO=1001`、`CMD_SPEED_CTRL=1`、`CMD_PWM_INPUT=11`、`CMD_BASE_FEEDBACK=130`、`CMD_BASE_FEEDBACK_FLOW=131`。
- `uart_ctrl.h` 中 `T=1` 进入 `setGoalSpeed(L,R)`；`T=11` 关闭 PID 并调用 `leftCtrl(L)` / `rightCtrl(R)`；`T=130` 调用 `baseInfoFeedback()`；`T=131` 控制 `baseFeedbackFlow`。
- `ugv_advance.h::baseInfoFeedback()` 将 `speedGetA/speedGetB` 输出为 `T=1001.L/R`。
- `movtion_module.h` 中 `speedGetA/speedGetB` 来自 encoder 采样；非 encoder `mainType != 3` 时 direct control 会把 `leftCtrl/rightCtrl` 的 PWM 整数写入 `speedGetA/speedGetB`。

验收命令结果：

```text
$ ssh root@192.168.1.11 -p 37878 'python3 --version && test -e /dev/ttyS5'
Python 3.10.12
```

```json
// ssh root@192.168.1.11 -p 37878 'curl -sS http://127.0.0.1:8787/api/base/status'
{
  "port": "/dev/ttyS5",
  "baudrate": 115200,
  "port_info": {"exists": true, "realpath": "/dev/ttyS5"},
  "feedback_ack": {
    "t1001_observed": true,
    "source": "fresh_readback"
  }
}
```

Sweep summary：

```json
{
  "final_stop_success": true,
  "api_restore_success": true,
  "segments": [
    {
      "segment": "speed_003",
      "record_count": 97,
      "nonzero_lr_count": 0,
      "max_abs_left_speed": 0.0,
      "max_abs_right_speed": 0.0,
      "stop_success": true,
      "api_restore_success": true
    },
    {
      "segment": "speed_005",
      "record_count": 96,
      "nonzero_lr_count": 0,
      "max_abs_left_speed": 0.0,
      "max_abs_right_speed": 0.0,
      "stop_success": true,
      "api_restore_success": true
    },
    {
      "segment": "pwm_35",
      "record_count": 34,
      "nonzero_lr_count": 0,
      "max_abs_left_speed": 0.0,
      "max_abs_right_speed": 0.0,
      "stop_success": true,
      "api_restore_success": true
    }
  ]
}
```

JSONL 行数：

```text
 97 artifacts/remote_capture/speed_003_feedback.jsonl
 96 artifacts/remote_capture/speed_005_feedback.jsonl
 34 artifacts/remote_capture/pwm_35_feedback.jsonl
```

恢复证据：

```text
trashbot-upper-robot-api.service - Trashbot unified upper robot API
Active: active (running) since Wed 2026-06-10 02:06:16 CST
Main PID: 82072 (python3)
api_restore_success=True
```

硬件结论：

- 真实上位机 `/dev/ttyS5` 可打开，`upper_robot_api` 在接管前后均能通过 `T=130` fresh readback 观测到 vendor `T=1001`。
- `T=1,L=0.03/R=0.03` 0.8s、`T=1,L=0.05/R=0.05` 0.8s、`T=11,L=35/R=35` 0.25s 三段均有足够 `T=1001` 样本，且 `invalid_json_count=0`。
- 三段 `T=1001.L/R` 全部为 0，`nonzero_lr_count=0`，`max_abs_left_speed/max_abs_right_speed=0.0`。
- 相比上一轮 0.25s 低速 pulse，本轮 0.8s speed sweep 与 0.25s direct PWM sweep 仍全零，因此“只是短脉冲或 0.03 太低导致采不到”的解释不再成立。
- 当前证据更支持：现有真实板固件/底盘反馈路径下，vendor `T=1001.L/R` 尚不能作为可用轮速反馈；需要继续检查 encoder/mainType/运动执行/固件配置，而不能把 `/odom` 升级为实测里程计。

## 剩余风险

- 本轮通过远端 SSH direct pyserial 发出了低速/低 PWM 窗口命令，但没有摄像头画面、轮上标记、外部里程计或现场人员反馈证明物理轮子确实转动；因此不能区分“命令未导致电机实际转动”和“电机转动但 encoder 反馈路径为 0”。
- `T=1` / `T=11` 没有独立 ACK 字段；本轮只证明串口写入成功、`T=1001` 持续返回、强制 stop 写入成功和 API 恢复成功。
- `T=1001.L/R` 仍不可用于真实里程计闭环；ROS `/odom` 仍应保持命令积分或明确标注非实测来源，直到完成 encoder/mainType/实测位移交叉验证。
- 下一步履约动作：现场可视化确认轮子是否在 `T=11,L=35,R=35` 0.25s 内转动；如转动但 L/R 仍为 0，检查 WAVE ROVER 当前 `mainType`、encoder 接线/方向、固件分支和 `speedGetA/B` 更新条件；如未转动，先定位 motor power、driver enable、急停/心跳 stop 或 PWM 阈值。
