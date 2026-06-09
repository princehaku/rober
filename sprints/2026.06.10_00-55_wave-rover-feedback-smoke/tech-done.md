# WAVE ROVER Feedback Smoke Tech Done

## sprint_type: epic

## 实际改动

- 新增 `artifacts/raw_feedback_probe.log`，保存 raw UART 发送/接收全过程。
- 新增 `artifacts/esp32_bridge_feedback.log`，保存 ROS2 bridge 启动与 topic probe 结果。
- 新增 `artifacts/battery_once.txt`、`artifacts/imu_once.txt`、`artifacts/odom_once.txt`，分别保存单次 topic 采样结果。
- 新增 `artifacts/wave_rover_feedback_smoke.md`，汇总本轮硬件 smoke 结论。
- 本文件记录实际验证与失败定位。

## 验证结果

### 1. 基线

- `ssh root@192.168.1.11 -p 37878 'true'`：通过。
- `ssh root@192.168.1.11 -p 37878 'curl -sS http://127.0.0.1:8787/api/base/status || true'`：可访问，但 `feedback_ack.t1001_observed=false`。
- `ssh root@192.168.1.11 -p 37878 'fuser -v /dev/ttyS5 || true'`：本轮多次返回空输出，不能作为串口未使用证据；实际 `upper_robot_api.py` 进程存在。

### 2. raw UART probe

- 停止 `upper_robot_api.py` 后，成功打开 `/dev/ttyS5`。
- 成功发送：
  - `{"T":143,"cmd":0}`
  - `{"T":142,"cmd":100}`
  - `{"T":131,"cmd":1}`
  - `{"T":130}`
- 在 10 秒窗口内连续收到 `T=1001`。
- `T=1001` 字段检查：
  - `L/R/r/p/v`：存在。
  - `y`：字段存在，但返回字符串 `"null"`。

### 3. ROS2 topic probe

- `esp32_bridge` 启动成功，并打印：
  - `Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200`
  - `ESP32Bridge ready ...`
- 10 秒单次采样结果：
  - `/battery`：无样本。
  - `/imu/data`：无样本。
  - `/odom`：有样本，内容为零速度零位姿积分。

### 4. API 恢复

- `upper_robot_api.py` 已恢复并再次可访问 `/api/base/status`。
- 最终状态：
  - API 进程存在。
  - `/api/base/status` 仍显示 `feedback_ack.t1001_observed=false`。
  - `feedback_samples_latest.artifact.status=missing`。

## 失败定位

1. WAVE ROVER 下位机 raw feedback 已闭环，不是 `/dev/ttyS5` 无数据。
2. ROS2 `esp32_bridge` 没有把本轮 fresh `T=1001` 转成 `/battery`、`/imu/data` 样本。
3. `upper_robot_api.py` 恢复后也没有把本轮 fresh `T=1001` 计入 `base_status`，API readback/artifact 更新链仍不通。

## 剩余风险

- `y` 字段当前为 `"null"`，即便后续 topic 发布成功，yaw 语义也可能需要额外兼容。
- `/odom` 仍是命令积分输出，不代表实测底盘反馈里程计已接通。
- `/battery`、`/imu/data` 仍为空，O1 的真实反馈链不能算完成。

## 下一步履约动作

1. 交给 `robot-software-engineer` 排查 `esp32_bridge` 是否主动请求/消费 `T=1001`，以及 `/battery`、`/imu/data` publisher 触发条件。
2. 单独排查 `upper_robot_api.py` 为什么在 raw 已证实有 `T=1001` 的情况下仍报告 `t1001_observed=false`，并且重启后丢失 `feedback_samples_latest` artifact。
