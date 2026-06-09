# Integrated Sensor Motion Capture Tech Done

## sprint_type: epic

## 实际改动

- 新增 `artifacts/run_integrated_capture.sh`，用于本轮真实上位机 integrated capture。
- 新增 `artifacts/remote_cleanup.sh`，用于手工收尾并恢复 API。
- 新增 `artifacts/integrated_sensor_motion_capture.md`，汇总本轮硬件证据。
- 新增并回收本轮真实产物：
  - `artifacts/remote_capture_run_20260610_004611/**`
  - `artifacts/remote_cleanup_output.txt`
  - `artifacts/upper_robot_api_restore.log`
  - `artifacts/api_status_before.json`
  - `artifacts/learn_show_args.txt`
  - `artifacts/esp32_bridge_help.txt`

## 执行与验证结果

### 验收命令

1. `ssh root@192.168.1.11 -p 37878 'true'`
   - 结果：通过。
2. `ssh root@192.168.1.11 -p 37878 'curl -sS http://127.0.0.1:8787/api/base/status || true'`
   - 结果：通过。
   - 关键事实：`port=/dev/ttyS5`、`baudrate=115200`、`safe_to_control=false`、`feedback_ack.t1001_observed=false`。
3. `ssh root@192.168.1.11 -p 37878 'bash -lc '\''source /opt/ros/humble/setup.bash && source /root/rober/onboard/install/setup.bash && ros2 launch ros2_trashbot_bringup learn.launch.py --show-args'\'''`
   - 结果：通过。
   - 关键事实：`learn.launch.py` 支持 `lidar_serial_port`、`lidar_serial_baudrate`、`camera_device`、`route_output_dir`、`map_dir`、`no_motion_static_odom_tf`、`no_motion_mock_odom_enabled` 等参数。
4. `ssh root@192.168.1.11 -p 37878 'bash -lc '\''source /opt/ros/humble/setup.bash && source /root/rober/onboard/install/setup.bash && ros2 run ros2_trashbot_hardware esp32_bridge --ros-args --help'\'''`
   - 结果：失败，但已记录。
   - 失败定位：程序把 `--help` 当作未知 ROS 参数，抛出 `UnknownROSArgsError: ['--help']`；这不影响本轮用实际参数启动 bridge。

### integrated capture

- `upper_robot_api.py` 初始占用 `/dev/ttyS5`，停止后 `fuser_after_api_stop.txt` 为空，说明底盘串口已释放。
- `esp32_bridge.log` 关键日志：
  - `Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200`
  - `command_mode=speed`
- `learn_launch.log` 关键日志：
  - `lidar_driver`: `LiDAR serial started: /dev/ttyACM0 @ 150000`
  - `camera_publisher`: `/dev/video1` -> `/camera/image_raw`
  - `route_data_recorder`: `Saved waypoint #1` 到 `Saved waypoint #11`
  - `map_recorder`: `Map saved to /tmp/trashbot_integrated_sensor_motion_maps/trashbot_integrated_sensor_motion_map.pgm`
- `cmd_vel_info.txt`：
  - `Type: geometry_msgs/msg/Twist`
  - `Subscription count: 1`
- `stop_service_call.log`：
  - `success=True, message='Motors stopped'`
- `save_map_call.log`：
  - `success=True, message='Map saved to /tmp/trashbot_integrated_sensor_motion_maps/trashbot_integrated_sensor_motion_map.pgm'`

### topic / artifact 逐项结论

- LiDAR：通过。
  - `topics/scan_once.txt` 有 `frame_id: laser_frame` 和真实 ranges/intensities。
- camera：通过。
  - `topics/camera_once.txt` 有 `frame_id: camera`、`width: 640`、`height: 480`、`encoding: bgr8`。
- 建图：通过。
  - map 文件已生成：`trashbot_integrated_sensor_motion_map.yaml`、`trashbot_integrated_sensor_motion_map.pgm`。
- 运动：通过。
  - `topics/odom_before_motion_once.txt` 为 `x: 0.0`。
  - `topics/odom_after_motion_once.txt` 为 `x: 0.10949261345999997`。
- route / keyframe：通过。
  - `route.csv` 保存 11 条记录（起点 + 10 个增量 checkpoint）。
  - `manifest.json` 记录 10 个 `route_keyframe_*`。
- stop：通过。
  - `/trashbot/stop` 成功返回。
- `/battery`：未通过。
  - `topics/battery_once.txt` 为空。
- `/imu/data`：未通过。
  - `topics/imu_once.txt` 为空。
- API 恢复：通过。
  - `remote_cleanup_output.txt` 再次返回 `/api/base/status` JSON。
  - `upper_robot_api_restore.log` 有 `upper_robot_api_started`。

## 偏差与修复

- 本轮只允许修改 sprint 目录，因此没有修产品代码。
- `run_integrated_capture.sh` 首次执行暴露两个脚本问题：
  1. `scp` 端口参数误用 `-p`。
  2. `set -u` 与 `/opt/ros/humble/setup.bash` 冲突。
- 以上问题均在 sprint artifact 脚本内修复，不涉及产品代码。
- capture 主逻辑完成后，远端 shell 没有自动收尾后台 ROS 进程；已通过 `remote_cleanup.sh` 手工 kill orphan 进程并恢复 API。

## 剩余风险

- `/battery`、`/imu/data` 没有新鲜样本，当前仍无法证明 `T=1001/T=1002` 在本轮 integrated capture 中闭环。
- `/api/base/status` 恢复后虽然可访问，但 `feedback_ack.t1001_observed=false`，且 `feedback_samples_latest` 指向旧 artifact，不代表本轮新鲜 feedback。
- `no_motion_static_odom_tf:=true` 只是 smoke-only TF；不能把本轮结果视为动态 TF、真实轮速里程计或导航级 SLAM 已完成。
- `/odom` 增量来自 ROS-side command integration，不是实测编码器里程计。
