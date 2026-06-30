# 2026.07.01 00:46 LiDAR diagnostics 地图 WYSIWYG 刷新

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`
  - LiDAR driver 在每次发布 `/scan` 后，把同一帧 LaserScan 抽样为最多 240 个结构化 `scan_preview_points`。
  - 每秒 diagnostics 写入 `scan_preview`，供 PC 地图和上位机 API 使用真实当前点位，不再依赖额外 ROS2 CLI 采样。
- `onboard/scripts/upper_robot_api.py`
  - `/api/radar/scan-proof/refresh` 默认切为 `collector_mode=driver_diagnostics`，只读 LiDAR lifecycle diagnostics 并写入 latest proof。
  - 旧 `ros2 topic echo/hz` collector 保留为显式 `collector_mode=legacy_ros2_cli` 工程模式。
  - latest proof readback 支持直接读取 artifact 内结构化 `scan_preview_points`。
- `onboard/scripts/test_upper_robot_api_free_roam.py`
  - 增加 diagnostics refresh 单测，证明默认模式不会走 legacy collector，且能写出结构化地图点。
- `onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py`
  - 增加 scan preview 纯函数单测，证明 mock packet 能产生 PC 地图可消费的真实点字段。
- `onboard/README.md`
  - 记录 2026-07-01 起 `/api/radar/scan-proof/refresh` 默认走 diagnostics，不触碰底盘 UART 或运动命令。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步 PC 地图 WYSIWYG 雷达刷新口径和上车验证证据。

## 验证结果

- 本地静态/单测：
  - `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py` 通过。
  - `python3 -m unittest onboard.scripts.test_upper_robot_api_free_roam` 通过，`Ran 7 tests`。
  - `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_lidar_driver_stubs.py'` 通过，`Ran 17 tests`。
  - `npm run build` 在 `pc-tools/workstation` 通过；仅保留既有 Vite bundle size warning。
  - `bash onboard/scripts/docker_humble_build.sh` 通过，`Summary: 6 packages finished [44.6s]`。
- 上车 no-motion 验证：
  - 已同步 `upper_robot_api.py` 和 `lidar_driver.py` 到 `root@192.168.1.11:/root/rober/onboard`。
  - 板端 `python3 -m py_compile` 通过。
  - 重启 LiDAR lifecycle 后，`/tmp/rober_lidar_lifecycle/lidar_driver_diagnostics.json` 出现 `scan_preview`，现场读到 `point_count=152`。
  - 重启 `trashbot-upper-robot-api.service` 后，8787 监听 `0.0.0.0:8787`，服务 active。
  - `POST http://127.0.0.1:8787/api/radar/scan-proof/refresh` 返回：
    - `request.mode=driver_diagnostics`
    - `runtime_requested=false`
    - `command_result.mode=lidar_driver_diagnostics_refresh`
    - `collector.script_path=null`
    - `status=refreshed`
    - `proof_state=scan_once_hz_raw_packet_tf_observed`
  - `GET /api/radar/status` 返回：
    - `latest_scan_proof_fresh=true`
    - `continuous_window_observed=true`
    - `scan_preview_point_count=108`
    - `driver_diagnostics_status=scan_published`
    - `sends_motion_commands=false`
  - `GET /api/map/preview` 返回：
    - `status=loaded`
    - `radar_overlay_status=loaded`
    - `radar_overlay_point_count=108`
    - `blocked_reasons=[]`
    - `sends_motion_commands=false`
  - 上车服务日志 3 分钟内未出现 OOM，`systemctl is-active trashbot-upper-robot-api.service` 为 `active`。

## 剩余风险

- 本轮没有执行底盘运动、Nav2 goal、键盘连续手控、free-roam start/stop 或 delivery success；这些仍需在现场安全确认后单独复验 wheel raw L/R 非零和完整路线执行。
- 摄像头首帧链路仍未在本轮恢复；本轮只修复雷达点位和地图 overlay 的 WYSIWYG 刷新链路。
- `collector_mode=legacy_ros2_cli` 仍保留为工程深采样入口；普通 PC 刷新不再默认使用它。
