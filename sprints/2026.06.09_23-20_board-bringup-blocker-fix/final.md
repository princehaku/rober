# Board Bringup Blocker Fix Final

## 收口状态

状态：部分完成，fail-closed。

本轮完成了实板 evidence capture 主链路的一次关键恢复：ROS2 bringup blocker 已修复，camera/LiDAR/static TF 可在同一 sensor-only bringup 中采样，no-motion rosbag 和真实相机 keyframe 已落地，底盘通过现有上位机 API 完成一次极低速点动并自动 stop。

本轮没有完成建图，也没有完成 ROS2 `/cmd_vel` 主链路/HIL。`safe_to_control=false`、`primary_actions_enabled=false`、`delivery_success=false` 必须继续保持。

## 实际交付

- 修复 `task_orchestrator` launch 参数类型，避免 `elevator_assist_target_floor` integer/string 崩溃。
- 修复 `waypoint_manager` 对 `nav2_simple_commander` 的硬依赖，缺包时仍允许学习/航点服务启动。
- 新增真实 `camera_publisher`，通过 OpenCV 读取实板 `/dev/video1` 并发布 `/camera/image_raw`。
- 将实板已验证的 `lidar_driver` 和 packet parser 同步回仓库，注册 `lidar_driver` console script。
- 扩展 `bringup.launch.py`：`base_enabled`、LiDAR 参数、camera 参数、smoke-only static TF 参数。
- 修复 SSH preflight 远端 ROS2 setup source 逻辑。
- 更新 navigation/hardware/vision 文档和 sprint artifacts。

## 验证证据

- 本地静态/单测：
  - `py_compile` 通过。
  - field preflight + waypoint 静态测试 `11` tests 通过。
  - LiDAR packet/driver 测试 `11` tests 通过。
  - bringup launch contract 测试 `14` tests 通过。
- Docker/Humble：
  - `bash onboard/scripts/docker_humble_build.sh` 通过，`Summary: 6 packages finished`。
- 实板：
  - SSH target `root@192.168.1.11 -p 37878` 可用。
  - `bringup.launch.py --show-args` 可见新增参数。
  - sensor-only smoke 同时看到 `/scan`、`/camera/image_raw`、`/tf_static`、`/map`、`/trashbot/waypoints`。
  - `/scan`、`/camera/image_raw`、`/tf_static` 均 `echo --once` 成功。
  - no-motion rosbag 录到 `/scan=1470`、`/camera/image_raw=2`、`/tf_static=1`。
  - `keyframe_sample.jpg` 和 `keyframe_sample.json` 已保存。
  - 低速运动 gate 通过 API 执行 `forward speed=0.03 duration_ms=200`，自动 stop 和显式 stop 均执行，前后反馈均观测 `T=1001`。

## 失败与根因

- 建图失败：`save_map` 返回 `success=False, message='No map data received'`。当前 sensor-only 组合没有稳定 `/map` 数据源，`map.yaml` 未产出。
- 路线失败：`route_data_recorder` 因 `ModuleNotFoundError: No module named 'cv_bridge'` 退出；同时 no-motion 组合没有 `/odom`，即使补依赖也不能生成真实 route.csv。
- 运动边界：这次是上位机 API `T=1` 极低速点动，不是 ROS2 `/cmd_vel` 主链路，不是 `/odom` before/after，不是 HIL。
- TF 边界：`base_link -> laser_frame` 是 `0/0/0` smoke-only 拓扑 TF，不是机械标定。

## OKR 影响

- O3 现场验证 lane 明显推进：真实雷达、摄像头、bag、keyframe、API 低速运动证据已落地。
- O7 可消费真实 sensor bag/keyframe 作为后续 route replay/labeling 输入，但仍缺 `route.csv` 和 map。
- O6 可消费 fail-closed artifacts 和 manifest 边界，产品/手机侧仍不得显示成功或可控。
- O1 获得 `/dev/ttyS5 @ 115200` API 点动证据，但仍不是 ROS2 HIL pass。

## 下一步

1. 把 `learn.launch.py`/`slam_toolbox` 纳入现场 sensor stack，专门解决 `/map` 持续发布和 `map.yaml` 保存。
2. 补板上 `cv_bridge` 或改 route recorder 的图像转换路径，解除 keyframe/route recorder 启动 blocker。
3. 在安全现场条件下推进 ROS2 `esp32_bridge serial_port:=/dev/ttyS5`、`/cmd_vel`、`/odom` before/after 的主链路 motion smoke。
4. 对 `base_link -> laser_frame` 做机械安装测量和标定，替换当前 smoke-only TF。

## 最终风险

本轮不是完整 autonomous 交付，不是建图完成，不是 HIL pass，不是 delivery success。已提交的证据应该被用于下一轮工程推进，而不是用于打开产品控制面。
