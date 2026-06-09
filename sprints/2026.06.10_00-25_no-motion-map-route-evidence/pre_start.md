# No-Motion Map Route Evidence Pre Start

## sprint_type: epic

## 背景

上一轮 `2026.06.09_23-20_board-bringup-blocker-fix` 已恢复实板 sensor-only evidence：

- `/scan`、`/camera/image_raw`、`/tf_static` 可同时采样；
- no-motion rosbag 和真实 keyframe fallback 已落地；
- `upper_robot_api` 完成一次 `forward speed=0.03 duration_ms=200` 低速点动并自动 stop；
- 但没有 `map.yaml`，`save_map` 返回 `No map data received`；
- 没有 `route.csv`，根因是板上缺 `cv_bridge` 且 no-motion stack 没有 `/odom`。

当前工作区已有未提交改动：

- `learn.launch.py` 已开始接入 camera/LiDAR/static TF/no-motion odom 参数；
- `route_data_recorder.py` 已开始把 `cv_bridge` 改成可选依赖并提供 numpy/cv2 fallback。

这些改动不能丢弃，必须在当前状态基础上验证、修补和上板。

## 本轮目标

1. 让 `learn.launch.py` 能在真实上位机以 no-motion 参数启动 sensor + SLAM + route recorder 组合。
2. 让 `route_data_recorder` 在板上缺 `cv_bridge` 时不崩溃，至少能消费 synthetic `/odom` 并写出 `route.csv`。
3. 尝试获取 `map.yaml`；若仍失败，保存 `slam_toolbox`、TF、scan、map service 失败证据。
4. 产出 no-motion route/keyframe/manifest 或明确降级原因。

## Owner

- 主责：`robot-algorithm-engineer`
- 协作边界：涉及 launch 和 route recorder 的软件胶水，但本轮文件强耦合，单 owner 闭环。

## 验收边界

- 禁止发布 `/cmd_vel`。
- synthetic `/odom` 只用于 no-motion route/keyframe/manifest 软件链路验证，不是运动、里程计标定或 HIL。
- `map.yaml` 只有真实 `/map` 数据保存成功才算通过；不能伪造地图。
- 当前实板参数继续显式传入：`camera_device:=/dev/video1`、`lidar_serial_port:=/dev/ttyACM0`。
