# Integrated Sensor Motion Capture Artifact Summary

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

采用事实：

- 底盘链路是 UTF-8 newline-delimited JSON UART。
- 厂商默认底盘 UART 波特率为 `115200`。
- 本轮继续使用 `T=1` speed control，对应 `command_mode:=speed`。
- `T=130/131/142/143` 属于底盘反馈与反馈流控制指令；本轮尝试读取 `/battery`、`/imu/data`，但未取得新鲜样本。

## 远端对象

- 主机：`root@192.168.1.11:37878`
- 底盘串口：`/dev/ttyS5 @ 115200`
- LiDAR：`/dev/ttyACM0 @ 150000`
- camera：`/dev/video1`

## 执行摘要

1. 先读取基线 API 状态，并确认 `upper_robot_api.py` 占用 `/dev/ttyS5`。
2. 停止 `upper_robot_api.py`，确认 `/dev/ttyS5` 释放。
3. 单独启动 `esp32_bridge`：
   - 证据：`esp32_bridge.log` 显示 `Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200`。
4. 启动 `learn.launch.py` 联跑 LiDAR、camera、SLAM、map recorder、route recorder。
5. 抓取 `/scan`、`/camera/image_raw`、`/odom`、`/cmd_vel` subscriber、`/trashbot/stop` 服务样本。
6. 发布一次低速脉冲 `linear.x=0.03`，随后零速并调用 `/trashbot/stop`。
7. 调用 `/trashbot/save_map`，保存 map；回收 `route.csv`、`manifest.json` 与 keyframes。
8. 手工执行 cleanup，杀掉 orphan 的 `learn.launch` / `esp32_bridge` 子进程，恢复 `upper_robot_api.py`。

## 关键产物

- 远端执行日志：
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_capture_20260610_004611/learn_launch.log`
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_capture_20260610_004611/esp32_bridge.log`
- topic 样本：
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_capture_20260610_004611/topics/scan_once.txt`
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_capture_20260610_004611/topics/camera_once.txt`
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_capture_20260610_004611/topics/odom_before_motion_once.txt`
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_capture_20260610_004611/topics/odom_after_motion_once.txt`
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_capture_20260610_004611/topics/battery_once.txt`
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_capture_20260610_004611/topics/imu_once.txt`
- route / keyframe：
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_sensor_motion_route/route.csv`
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_sensor_motion_route/manifest.json`
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_sensor_motion_route/keyframes/*.jpg`
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_sensor_motion_route/keyframes/*.json`
- map：
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_sensor_motion_maps/trashbot_integrated_sensor_motion_map.yaml`
  - `artifacts/remote_capture_run_20260610_004611/trashbot_integrated_sensor_motion_maps/trashbot_integrated_sensor_motion_map.pgm`
- API 恢复：
  - `artifacts/remote_cleanup_output.txt`
  - `artifacts/upper_robot_api_restore.log`

## 关键结论

- LiDAR 同轮成功：`/scan` 有真实 `laser_frame` 样本。
- camera 同轮成功：`/camera/image_raw` 有 `640x480 bgr8` 样本。
- motion 同轮成功：`/cmd_vel` 有 1 个 subscriber，`/odom` 从 `x=0.0` 增长到 `x=0.10949261345999997`。
- stop 同轮成功：`/trashbot/stop` 返回 `success=True, message='Motors stopped'`。
- map 同轮成功：`/trashbot/save_map` 返回 success，并保存 YAML/PGM。
- route / keyframe 同轮成功：`route.csv` 保存 11 行（含 index 0 起点），`manifest.json` 保存 10 个 keyframe 样本。
- `/battery`、`/imu/data` 未取得样本：对应 topic 输出文件为空。
- API 已恢复：`/api/base/status` 再次可访问，但返回的 feedback 仍指向旧样本，`t1001_observed=false`。

## 已知偏差

- 自动化执行脚本第一次在 `scp -p` / `scp -P` 选项差异上失败，第二次又因 `set -u` 与 ROS setup 脚本冲突中断，随后手工完成 cleanup 与 artifact 拉取。
- 远端 capture 脚本退出前没有自动 kill 掉 `learn.launch` / `esp32_bridge` 子进程；本轮已通过 `remote_cleanup.sh` 手工清理并恢复 API。
- `no_motion_static_odom_tf:=true` 只证明 smoke 级 TF 拓扑存在，不代表动态 `odom -> base_link` TF 与导航级 SLAM 标定完成。
- 当前 `/odom` 仍是 `esp32_bridge` 的 ROS-side command integration，不是实测编码器里程计。

## 下一步履约动作

1. 让 `esp32_bridge` 或上位机工具链显式触发并记录 `T=130/T=131`，补齐底盘 feedback 新鲜样本。
2. 定位 `/battery`、`/imu/data` 未出样本的根因，是 bridge 未发布、下位机未回、还是话题名不匹配。
3. 修正本 sprint 的远端 capture 脚本收尾逻辑，避免下一轮再出现 orphan 进程。
