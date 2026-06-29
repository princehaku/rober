# LiDAR STC 协议与波特率对齐

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py`：保留旧 `0xAA55` mock/回放解析，新增 WAVE ROVER/STC `0x54` 固定 47 字节、12 点帧解析和 mock 构造；资料来源为 `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`：LiDAR 默认波特率改为 230400；真实串口启动注释明确采用 WAVE ROVER vendor 口径。
- `onboard/scripts/o1_lidar_lifecycle.sh`、`onboard/scripts/o1_lidar_ros2_scan_smoke.sh`、`onboard/scripts/o11_nav2_lifecycle.sh`、`onboard/scripts/o10_amcl_nav2_runtime_proof.py`、`onboard/scripts/o3_map_lifecycle_proof.py`、`onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`、`bringup.launch.py`、`autonomous.launch.py`、`onboard/scripts/upper_robot_api.py`：LiDAR lifecycle、smoke、Nav2/map proof、launch 默认值、Nav2 默认启动参数和雷达状态展示统一改为 `/dev/ttyACM0 @ 230400`。
- `onboard/scripts/o1_lidar_scan_proof_collector.py`：纳入仓库并修复 proof 读取路径，`scan/raw_packet` echo 使用 `--no-daemon` 和显式消息类型，默认只读观察窗口提升到 12 秒，规避现场 ROS daemon `rclpy.ok()` 异常和 DDS discovery 慢导致的误报。
- `onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py`、`onboard/tests/test_lidar_lifecycle_script.py`、`onboard/tests/test_lidar_scan_proof_collector.py`、`onboard/tests/test_upper_robot_api.py`：补 STC 帧解析/串口读取/collector 命令回归，并把默认命令断言同步到 230400。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`：记录真实雷达协议、波特率来源和边界。

## 验证结果

- 通过：`python3 -m unittest onboard.src.ros2_trashbot_hardware.test.test_lidar_driver_stubs`，14 tests OK。
- 通过：`python3 -m unittest onboard.tests.test_lidar_lifecycle_script`，3 tests OK。
- 通过：`python3 -m unittest onboard.tests.test_lidar_scan_proof_collector`，2 tests OK。
- 通过：`python3 -m unittest onboard.tests.test_upper_robot_api`，88 tests OK，1 skipped。
- 通过：`python3 -m unittest onboard.tests.test_lidar_scan_proof_collector onboard.src.ros2_trashbot_hardware.test.test_lidar_driver_stubs onboard.tests.test_lidar_lifecycle_script onboard.tests.test_upper_robot_api`，107 tests OK，1 skipped。
- 通过：`python3 -m py_compile onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/o3_map_lifecycle_proof.py`。
- 通过：`bash -n onboard/scripts/o1_lidar_ros2_scan_smoke.sh onboard/scripts/o1_lidar_lifecycle.sh onboard/scripts/o11_nav2_lifecycle.sh`。
- 通过：`git diff --check`。
- 通过：`bash onboard/scripts/docker_humble_build.sh`，Docker/Humble `colcon build --symlink-install` 输出 `Summary: 6 packages finished [43.2s]`；构建过程中仅保留既有 amd64 ROS 镜像运行在 arm64 Docker Desktop 上的平台 warning。
- 通过：上位机 sensor-only 部署和 proof 刷新；默认 `/api/radar/scan-proof/refresh` 已是只读观察模式，12 秒窗口返回 `proof_state=scan_once_hz_raw_packet_tf_observed`、`scan_hz_average_rate_hz=17.355`，`blocked_commands_not_sent` 包含 `A5 60/T=1/T=13/T=130/T=131//cmd_vel//api/base/manual`。
- 通过：上位机 `GET /api/radar/status` 返回 `scan_status=fresh_scan_proof_observed`、`continuous_scan_status=latest_proof_fresh_while_lifecycle_running`、`blocked_reasons=[]`、`baudrate=230400`。
- 通过：上位机 `GET /api/nav2/status` 的默认 start command 已显示 `--lidar-serial-baudrate 230400`，`lifecycle_manager.latest_result.lidar_serial_baudrate=230400`；该读取仍保持 `sends_motion_commands=false`、`robot_control_executed=false`。
- 通过：本机 PC 7001 `GET /api/robot-control/summary` 返回 `radar_status=radar_ready`、`latest_scan_proof_fresh=true`、`radar_overlay_status=loaded`、`map_wysiwyg_status_plain=地图画面、图上路线、小车位置和雷达标记都已按当前读数显示。`
- 待补：PC 端地图刷新后雷达点贴到当前地图 overlay 的最终视觉确认。

## 剩余风险

- 真机已证明 `/scan`、`/lidar/raw_packet` 和 TF 可读；当前 API 进程已显式去掉旧 `ROBER_LIDAR_SCAN_PROOF_RUNTIME_COMMAND=...150000`，默认 proof refresh 不再启动旧 smoke。
- 摄像头当前仍是 `uvc_no_frame_not_exclusive`，不是独占导致；本轮未修复摄像头硬件/输入无首帧。
- 自动驾驶能否真实带轮速执行，仍需要在雷达 fresh、现场安全确认后重跑路线，并在同窗口读取 wheel raw L/R 非零。
