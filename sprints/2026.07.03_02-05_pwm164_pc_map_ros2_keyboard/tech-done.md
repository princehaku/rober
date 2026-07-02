# tech-done

sprint_type: micro

## 实际改动

- 地图易用性：PC summary 保持普通用户优先的 `/map` 大地图，默认 `300%` 细节大图；ROS2 配套只作为工程观察，口径为本地 RViz2、远程 Foxglove bridge + Foxglove Web，不替代普通 PC 页面，不发送控制命令。
- 底盘默认链路：根据 `docs/vendor/VENDOR_INDEX.md` 指向的 Waveshare `json_cmd.h`，`T=13 CMD_ROS_CTRL` 标注不适合无编码器产品；因此 `esp32_bridge`、bringup/autonomous launch、O11 Nav2 helper 默认从 ROS/T=13 改为 `/cmd_vel -> T=11/PWM164`，`pwm_min_abs/max_abs=164`。
- PC/上位机手控：PC 仍对用户暴露 `command_mode=ros`，上车端用进程内 `rclpy` burst 发布 `/cmd_vel`；`onboard/scripts/upper_robot_api.sh` 现在 source ROS2/overlay 环境并固定 `RMW_FASTRTPS_USE_SHM=0`，避免 systemd 裸环境退回慢 CLI。
- PC summary：补齐 `motion_signal_observed`、`motion_signal_source`、`imu_attitude_delta_observed` 合同；当当前 idle=false 但 latest 手控窗口 artifact=true 时，PC 仍展示同窗口运动信号，同时继续显示 wheel raw L/R 为 0/0、`wheel_feedback_lr_nonzero_proven=false`。
- 文档同步：更新 `docs/product/pc_tools_workstation.md` 与 `docs/hardware/wave_rover_json_bridge.md`，记录 PC 大地图/RViz2/Foxglove 分层、PWM164 默认链路、systemd wrapper 和 vendor 依据。

## 验证结果

- 本地 Python：`python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests onboard.tests.test_o11_nav2_goal_execution_proof.O11Nav2GoalExecutionProofTests` 通过，108 tests，1 skipped。
- 本地硬件/bringup：`python3 -m unittest discover onboard/src/ros2_trashbot_hardware/test` 通过，57 tests；`python3 -m unittest onboard.src.ros2_trashbot_bringup.test.test_launch_contract_static.LaunchContractStaticTest` 通过，23 tests。
- PC：`npm test -- --run test/catalog.test.ts test/App.test.ts test/robotControlSummary.test.ts` 通过，432 tests；`npm run build` 通过，仅 Vite chunk size warning。
- Docker/Humble：`bash onboard/scripts/docker_humble_build.sh` 通过，`Summary: 6 packages finished [51.1s]`。
- 上车部署：同步 `upper_robot_api.py`、`upper_robot_api.sh` 等到 `root@192.168.1.11:37878`，`trashbot-upper-robot-api.service=active`；主进程环境已含 `ROS_DISTRO=humble`、`LD_LIBRARY_PATH`、`PYTHONPATH`、`RMW_FASTRTPS_USE_SHM=0`。
- 真实低速手控 smoke：`POST /api/base/manual`，`direction=forward`、`speed=0.06`、`duration_ms=150`、`command_mode=ros`，热路径 HTTP `200`、`TIME_TOTAL=0.350828`；`command_result/stop_result.publish_backend=rclpy_inprocess_burst`，bridge command log 显示 `T=11 L/R=164` 后立即 `T=11 L/R=0`。
- PC 7001：已重启为 `0.0.0.0:7001`，`/api/health` 默认小车地址为 `http://192.168.1.11:8787`，7071 未监听；`/api/robot-control/summary` 读到 `map_display_primary_url=/map`、`map_display_default_zoom_percent=300%`、`map_display_ros2_companion_answer_plain=RViz2/Foxglove`、`keyboard_motion_verified=true`。

## 剩余风险

- 摄像头仍不是浏览器独占问题：当前上车诊断仍指向 UVC 设备在 USB `12M` full-speed 拓扑、首帧读取失败；需要更换高速 USB 口/线或带供电 Hub 后复测。
- WAVE ROVER `T=1001 L/R` 仍为 `0/0`，本轮只证明 `T=11/PWM164` 有 IMU 姿态变化和底盘运动信号，没有证明编码器轮速非零。
- Nav2 完整路线执行和 delivery success 仍需下一轮在新的 PWM164 默认链路上重跑 HIL 采集，当前不能声明送达闭环完成。
