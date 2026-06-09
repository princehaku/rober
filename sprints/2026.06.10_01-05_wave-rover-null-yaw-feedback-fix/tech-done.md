# WAVE ROVER Null Yaw Feedback Fix Tech Done

## sprint_type: micro

## 目标

修复真实上车 feedback smoke 暴露的问题：WAVE ROVER raw UART 已连续返回 fresh `T=1001`，但 `y` 字段为字符串 `"null"`，当前 ROS2 feedback parser 把整帧丢弃，导致 `/battery`、`/imu/data` 都没有样本。

## Owner

- 主责：`robot-software-engineer`

## 允许改动范围

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`
- `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
- `docs/hardware/wave_rover_json_bridge.md`
- `sprints/2026.06.10_01-05_wave-rover-null-yaw-feedback-fix/tech-done.md`

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py
```

如环境允许，补充 Docker/Humble 或板上增量构建；如不运行，必须写明原因。

## 待完成

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback.py`
  - 将 `T=1001` 解析拆分为“必须 finite 的 `L/R/r/p/v`”与“允许 unavailable 的 `y`”两条路径。
  - 兼容 `y` 为 JSON `null` 或字符串 `"null"`，并把该语义显式转换为 `yaw=None`，避免因为姿态缺失丢掉整帧电压/轮速反馈。
  - 保持 `NaN/Infinity` 与坏字符串 fail-closed；只要 yaw 给了非空数值，就仍要求其是 finite。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`
  - 调整 feedback 发布逻辑：当 `yaw=None` 时仍发布 `/imu/data`，并设置 `orientation_covariance[0] = -1.0` 表示 orientation unavailable。
  - `/battery` 继续按 `T=1001.v` 发布，不再因为 yaw 缺失而被连带吞掉。
- `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
  - 补充 `y="null"` / `y=null` 解析测试。
  - 补充 yaw 非有限值与坏字符串拒收测试。
  - 补充 `_publish_feedback()` 在 yaw 缺失时仍发布 IMU/Battery 且带 orientation unavailable 语义的测试。
- `docs/hardware/wave_rover_json_bridge.md`
  - 记录真实板子可能返回 `y:"null"` / `y:null` 的集成事实，并说明这是 yaw unavailable，不是整帧无效。
  - 更新 `/imu/data` 与 `/battery` 的降级语义说明。

## 验证结果

- 已运行：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
  - `python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`
  - `bash onboard/scripts/docker_humble_build.sh`

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py
```

- 实际结果：
  - `Ran 16 tests in 0.011s`
  - `OK`
  - `py_compile` 无输出，表示语法检查通过。
  - Docker/Humble 输出 `Summary: 6 packages finished [55.4s]`。
  - Docker build 阶段出现 `InvalidBaseImagePlatform` warning：基础镜像为 `linux/amd64`，当前 Docker host 为 `linux/arm64/v8`；构建与 colcon 均已继续并通过，证据边界仍是 `software_proof_docker_only`。

## 硬件复测补充（2026-06-10）

- 依据资料来源：
  - `docs/vendor/VENDOR_INDEX.md`
  - `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- 远端连通与 API 基线：
  - `ssh root@192.168.1.11 -p 37878 'true'` 返回 `rc:0`，记录见 `artifacts/acceptance_ssh_true.log`。
  - `curl -sS http://127.0.0.1:8787/api/base/status` 可访问，记录见 `artifacts/acceptance_api_base_status.log`。
- 远端同步与增量构建：
  - 已同步 `wave_rover_feedback.py`、`esp32_bridge_node.py` 到 `/root/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/`。
  - 已在板上执行 `colcon build --symlink-install --packages-select ros2_trashbot_hardware`，结果为 `Summary: 1 package finished [7.80s]`，完整日志见 `artifacts/remote_colcon_build.log`。
- 串口占用切换：
  - 已停止 `upper_robot_api.py` 释放 `/dev/ttyS5`，记录见 `artifacts/remote_stop_upper_robot_api.log`。
  - 已启动 `ros2 run ros2_trashbot_hardware esp32_bridge --ros-args -p serial_port:=/dev/ttyS5 -p serial_baudrate:=115200 -p command_mode:=speed -p feedback_interval_ms:=100`。
  - bridge 启动日志显示已连接 `/dev/ttyS5 @ 115200`，记录见 `artifacts/remote_bridge_startup.log`。
- topic 复测结果：
  - `/battery` 已恢复发布，`voltage: 12.430290222167969`，`present: true`，记录见 `artifacts/topic_battery_once.log`。
  - `/imu/data` 已恢复发布，`orientation_covariance[0] = -1.0`，符合 yaw unavailable 的降级语义；记录见 `artifacts/topic_imu_once.log`。
  - `/odom` 已有首样本，`pose.pose.position` 与 `twist.twist` 均为零值，符合本轮未发送运动命令的安全边界；记录见 `artifacts/topic_odom_once.log`。
- 收尾恢复：
  - 已停止本轮 bridge，记录见 `artifacts/remote_stop_bridge.log`。
  - 已按原参数恢复 `upper_robot_api.py`，PID 记录见 `artifacts/remote_restore_upper_robot_api_pid.log`，进程检查见 `artifacts/remote_upper_robot_api_ps.log`。
  - 恢复后 `/api/base/status` 再次可访问，记录见 `artifacts/remote_api_status_after_restore.json`。

## 剩余风险

- 文档记录了真实板子会回 `y:"null"`，但该行为未在本地 vendor 源码中看到直接常量说明，当前仍属于 HIL 观察到的集成事实，后续应保留 raw UART 日志作为长期证据。
- `/imu/data` 在 yaw unavailable 时只声明 orientation 不可用，尚未引入角速度或线加速度字段；如果上层消费者假定 orientation 始终存在，仍需要一次联调复核。
- `/odom` 本轮只有静止首样本，仍是 ROS 侧命令积分语义的空载验证；尚未覆盖实车运动时的位置累计与方向一致性。
- `upper_robot_api` 的 `/api/base/status` 已恢复可访问，但其 `feedback_ack` 仍显示 `t1001_observed: false`，说明该 API 的主动读回链路与本轮 ROS bridge 被动订阅链路是两套证据面，后续若要把 API 状态也修到实时可信，还需单独排查。
