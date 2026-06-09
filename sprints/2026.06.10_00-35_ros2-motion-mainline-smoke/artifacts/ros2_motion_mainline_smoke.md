# ROS2 Motion Mainline Smoke Artifact

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

## 采用的硬件事实

- WAVE ROVER 上下位机链路是 UTF-8、每行一个 JSON、以换行结尾。
- 当前真实上位机底盘串口路径是 `/dev/ttyS5`，目标波特率是 `115200`。
- 本轮按安全边界使用 `command_mode:=speed`，对应 `T=1` 左右轮速度控制；未启用 `T=13`。
- `/odom` 只作为 ROS-side command integration 证据，不能解释为真实轮速里程计。

## 实际执行摘要

1. SSH 连通 `root@192.168.1.11:37878`。
2. 记录基线：`upper_robot_api.py` 在运行，`/api/base/status` 可访问。
3. 停止 `upper_robot_api.py`，确认 `/dev/ttyS5` 已释放。
4. 启动 `bringup.launch.py` base-only：
   - `base_enabled:=true`
   - `serial_port:=/dev/ttyS5`
   - `serial_baudrate:=115200`
   - `command_mode:=speed`
   - `lidar_enabled:=false`
   - `camera_enabled:=false`
   - `operator_gateway:=false`
   - `remote_bridge:=false`
5. 验证 ROS2 图：
   - 节点存在 `/esp32_bridge`、`/waypoint_manager`、`/map_recorder`、`/task_orchestrator`
   - `/cmd_vel` 为 1 个订阅者
   - `/trashbot/stop` 服务存在
6. 发布一次低速短脉冲：
   - `linear.x=0.03`
   - 持续 `0.3s`
   - 随后发布零速并调用 `/trashbot/stop`
7. 观察到 `/trashbot/stop` 返回 `success=True, message='Motors stopped'`。
8. 观察到 `/odom` 从 `x=0.0` 变为 `x=0.15000877008`。
9. 收尾时发现 `esp32_bridge` 残留占用 `/dev/ttyS5`，已单独清理残留 ROS2 子进程并重新拉起 `upper_robot_api.py`。
10. 最终 `/api/base/status` 再次可访问，`upper_robot_api.py` 重新监听 `0.0.0.0:8787`。

## 关键日志文件

- `artifacts/ros2_motion_mainline_smoke_remote_summary.log`
- `artifacts/ros2_motion_mainline_smoke_bringup.log`
- `artifacts/ros2_motion_mainline_smoke_api_restore.log`

## 关键结果

- `esp32_bridge` 日志确认：`Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200`
- `esp32_bridge` 日志确认：`command_mode=speed`
- `/trashbot/stop` 调用成功
- `/odom` 前后样本存在，但仅代表命令积分链路

## 未拿到的新样本

- 本轮未拿到新的 `/battery` 样本
- 本轮未拿到新的 `/imu/data` 样本

## 收尾偏差

- 初次 cleanup 只杀了 launch 父进程，没有把 `esp32_bridge` 等子进程一起收掉。
- 已补做定点清理，未影响 camera/WebRTC 服务。

