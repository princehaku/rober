# Board Bringup Blocker Fix Side-by-Side Check

## 验收口径

本轮验收对象是实板 evidence capture 主链路的恢复，不把单项 smoke 夸大成完整自主闭环。对照用户目标“雷达、摄像头、建图、运动都走一圈”，本轮按 evidence 粒度拆成四格验收：

| 项目 | 结果 | 证据 | 边界 |
|---|---|---|---|
| 雷达 | pass | `sensor_stack_smoke.md` 与 `no_motion_mapping_capture.md` 记录 `/scan` echo once，bag 中 `/scan=1470` 条。 | 仅证明 LiDAR topic 和 driver 链路，不证明定位/导航可用。 |
| 摄像头 | pass | `/dev/video1` 被确认为 DV20 USB 图像节点；`/camera/image_raw` echo once；保存 `keyframe_sample.jpg`。 | `camera_device:=/dev/video1` 是当前实板参数，不写成通用默认。 |
| 建图 | fail-closed | `save_map` 重试返回 `success=False, message='No map data received'`。 | 没有 `map.yaml`，不能宣称建图完成。 |
| 运动 | limited pass | `motion_gate.md` 记录 `POST /api/base/manual` 执行 `forward speed=0.03 duration_ms=200`，自动 stop 与显式 stop 均执行，前后反馈均观测 `T=1001`。 | 不是 ROS2 `/cmd_vel`、不是 `/odom` 主链路、不是 HIL；`safe_to_control=false` 仍保持。 |

## 已修复的启动阻塞

- `task_orchestrator` 不再因 `elevator_assist_target_floor` 被解析成 integer 崩溃。
- `waypoint_manager` 在缺 `nav2_simple_commander` 时降级启动，不再阻断学习/航点服务。
- SSH preflight 不再因未 source ROS setup 误判 `blocked_ros2_cli_missing`。
- `bringup.launch.py` 已支持 `base_enabled:=false`，避免 sensor-only smoke 抢占 `/dev/ttyS5`。
- `bringup.launch.py` 已能显式启动 `lidar_driver`、`camera_publisher` 和 smoke-only `tf_static`。

## 现场事实核对

- 相机：`/dev/video0` 是 Orange Pi `cedrus` M2M 编解码节点；当前真实图像节点是 `/dev/video1`。
- LiDAR：`/dev/ttyACM0 @ 150000` 单独和在 sensor-only bringup 中均能产出 `/scan`。
- 底盘：`upper_robot_api.py` 常驻占用 `/dev/ttyS5 @ 115200`，低速 API 点动可执行并自动 stop。
- 安全：API 和产品证据仍保持 `safe_to_control=false`、`primary_actions_enabled=false`、`delivery_success=false`。

## 未通过项

1. `map.yaml` 未产出，根因是当前 no-motion sensor-only 组合没有稳定 `/map` 数据源。
2. `route.csv` 未产出，根因首先是板上缺 `cv_bridge`，其次是 no-motion 组合没有 `/odom`。
3. 运动只完成 API 低速点动，没有完成 ROS2 `/cmd_vel`、`/odom` before/after 或完整 HIL。

## 验收结论

本轮把“真实上位机只能 SSH / 业务节点崩溃 / 相机缺 topic / LiDAR 不在 bringup / 运动未触碰”推进到“传感器栈可同时采样、bag 和 keyframe 已落地、运动 API 点动有 stop 证据”。建图和 ROS2 主运动链路仍 fail-closed，需要下一轮分别处理 `slam_toolbox`/`/map` 与 `cv_bridge`/`/odom`/`cmd_vel`。
