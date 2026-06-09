# Integrated Sensor Motion Capture Side-by-Side Check

## 目标对照

目标：同一轮在真实上位机上拉起底盘 bridge、LiDAR、camera、SLAM、route recorder，执行一次低速运动，保存 route/keyframes/map，并恢复 API。

## 对照结果

1. 底盘 bridge
   - 目标：`/dev/ttyS5 @ 115200 command_mode=speed`
   - 结果：通过。
   - 证据：`esp32_bridge.log` 明确显示 `Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200`。

2. LiDAR
   - 目标：`/dev/ttyACM0 @ 150000` 发布 `/scan`
   - 结果：通过。
   - 证据：`learn_launch.log` 显示 `LiDAR serial started: /dev/ttyACM0 @ 150000`；`topics/scan_once.txt` 有真实 LaserScan 样本。

3. camera
   - 目标：`/dev/video1` 发布 `/camera/image_raw`
   - 结果：通过。
   - 证据：`camera_publisher` 日志和 `topics/camera_once.txt`。

4. SLAM / map
   - 目标：`/map` 可保存为 YAML/PGM
   - 结果：通过。
   - 证据：`save_map_call.log` 返回 success；map 文件已生成。

5. route / keyframe
   - 目标：保存 `route.csv`、`manifest.json`、至少一个 keyframe
   - 结果：通过，且超过最低标准。
   - 证据：`route.csv` + `manifest.json` + `keyframes/001..010`。

6. motion / stop
   - 目标：发布低速 `/cmd_vel`，随后零速和 `/trashbot/stop`
   - 结果：通过。
   - 证据：`cmd_vel_info.txt` 有 subscriber；`odom_before_motion_once.txt` 到 `odom_after_motion_once.txt` 出现位移；`stop_service_call.log` success。

7. `/battery`
   - 目标：尽量拿到样本，拿不到也要保留超时证据
   - 结果：未通过，但有证据。
   - 证据：`topics/battery_once.txt` 为空。

8. `/imu/data`
   - 目标：尽量拿到样本，拿不到也要保留超时证据
   - 结果：未通过，但有证据。
   - 证据：`topics/imu_once.txt` 为空。

9. API 恢复
   - 目标：恢复 `upper_robot_api.py` 并验证 `/api/base/status`
   - 结果：通过。
   - 证据：`remote_cleanup_output.txt` 与 `upper_robot_api_restore.log`。

## 结论

- 本轮已经完成“雷达、摄像头、建图、运动都走一圈”的 integrated evidence capture。
- 未完成项只剩底盘 feedback 新鲜样本闭环，具体表现为 `/battery`、`/imu/data` 为空，且恢复后的 `/api/base/status` 仍未观测到本轮 `T=1001` 新鲜 ack。
- 本轮结果可作为 O6/O7 后续消费的真实 route/map/keyframe 素材包，但不能误标为动态 TF、实测轮速里程计或导航级 SLAM 通过。
