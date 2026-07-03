# PC live-summary 地图别名、ROS2 配套复核、相机/WASD 现场证据

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/live-summary` 增加 `route_target_current_visible`、`radar_map_points_current_visible`，PC summary 顶层同步增加相同别名，便于现场脚本直接验收地图、Nav2 路线、目标点和雷达点是否都在当前画布。
- 更新 `RobotControlSummaryResponse` / `RobotControlLiveSummaryResponse` 类型和 `robotControlSummary` 单元测试，锁定上述别名。
- 更新 `docs/product/pc_tools_workstation.md` 与 `docs/product/pc_free_roam_mapping_design.md`：记录 2026-07-04 02:50 CST 的真实地图、ROS2 配套、相机和 WASD 证据。
- 2026-07-04 03:05 CST 追加修复 `GET /api/robot-control/base/status` 独立只读代理：允许
  `bridge_command_debug.robot_control_executed=true` 作为历史命令 debug 材料，不再让当前只读 GET 返回 502；
  新增 catalog 路由级回归测试。
- 同步更新产品文档：记录本轮 `base/status` live 200、PC 手控命令 raw 非零、IMU 动作信号可见，以及
  `T=1001 L/R=0/0` 和 DV20 V4L2 0 字节的剩余风险。
- 2026-07-04 03:20 CST 追加 PC 地图易用性修正：普通首页和 `/map` 默认缩放从 `150%` 提升到
  `200%`，地图面板和内层 WYSIWYG 画布增高，顶栏入口改为 `地图大屏 /map`；ROS2 配套继续只作为
  `工程观察：RViz2 / Foxglove`，不替代普通用户简易控制台。

## 验证结果

- 已通过：`npm test -- --run test/robotControlSummary.test.ts`，`16 passed`。
- 已通过：`npm test -- --run test/App.test.ts -t "map"`，`70 passed`。
- 已通过：`npm test`，`3 passed`、`447 passed`。
- 已通过：`npm run build`；仅有既有 Vite chunk size warning。
- 上位机 ROS2 配套复核已通过：`ros2 pkg prefix ros2_trashbot_bringup` 返回 `/root/rober/onboard/install/ros2_trashbot_bringup`；`foxglove_bridge.launch.py --show-args` 返回 `address=0.0.0.0`、`port=8765`、`use_sim_time=false`、`sysinfo=true`；`rviz.launch.py --show-args` 返回 `rviz/trashbot_nav.rviz`。
- live 读回：`map_current_visible=true`、`path_current_visible=true`、`route_target_visible=true`、`route_target_current_visible=true`、`radar_map_points_current_visible=true`、`radar_overlay_current_point_count=190`、`map_display_default_zoom_percent=150%`、`map_display_direct_map_default_zoom_percent=150%`。
- WASD/方向键链路复验：PC 发前进、停止、后退、停止后，`live-summary` 读回 `keyboard_motion_verified=true`、`keyboard_stop_settled_after_pulse=true`、`keyboard_command_raw_lr_nonzero_proven=true`、`keyboard_motion_evidence_complete=true`。
- 相机复验：PC 共享 MJPEG 返回 502；首帧探针返回 `open_failed`/503；USB recovery 返回 `stream_failure_class=high_speed_zero_byte_no_frame`；上位机直接 `v4l2-ctl` 对 `/dev/video1` 的 MJPG/YUYV 采帧均 `select timeout` 且输出 0 字节。
- 已通过：`npm test -- --run test/catalog.test.ts -t "base status proxy"`，`1 passed`。
- 已通过：`npm test -- --run test/App.test.ts -t "map"`，`70 passed`，确认当前默认地图缩放和
  `/map` 直达页合同均为 `200%`。
- 已通过：`npm test -- --run test/robotControlSummary.test.ts`，`16 passed`。
- 已通过：`npm test -- --run test/catalog.test.ts -t "live-summary"`，`1 passed`。
- 已通过：`npm test`，`3 passed`、`448 passed`。
- 已通过：`npm run build`；仍只有既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，PID `64214`；实际 `summary` / `live-summary`
  读回 `map_display_default_zoom_percent=200%`、`map_display_direct_map_default_zoom_percent=200%`，
  且 `map_display_starts_ros2=false`、`map_display_starts_nav2=false`、`map_display_sends_motion_when_clicked=false`。
  当前 live 仍显示地图、路线、目标点和雷达点可见，相机首帧仍不可见。
- live 修复复验：PC Node PID `42460` 监听 `0.0.0.0:7001`；`GET /api/robot-control/base/status`
  返回 HTTP 200、`proxy_status=status_loaded`、`blocked_reasons=[]`、`hard_dangerous_true_fields=[]`、
  `wheel_feedback_lr_nonzero_proven=false`，且当前采样窗口已读到 `T=1001`。
- 同轮手控复验：PC `POST /api/robot-control/base/manual` 前进/后退返回 HTTP 200、`proxy_status=command_forwarded`、
  `command_raw_lr_nonzero_proven=true`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`，
  但 `wheel_feedback_lr_nonzero_proven=false`、`wheel_feedback_latest_raw_left/right=0/0`。
- Vendor 反馈复核：依据 `docs/vendor/VENDOR_INDEX.md`、`json_cmd.h`、`movtion_module.h` 与 `ugv_advance.h`，
  `T=1001.L/R` 来自固件 `speedGetA/B`；现场发 `{"T":900,"main":1,"module":0}` 后，PC 低速 PWM 手控仍未读到非零 L/R。
- 相机补充复验：`/dev/video1` 无 owner、USB 为 `480M`，但直连 `v4l2-ctl` 的 MJPG/YUYV 仍 `select timeout` 且 0 字节；
  `8088/mjpeg` 多格式返回 `opencv_capture_not_opened`。

## 剩余风险

- 实时图传仍未出首帧。当前证据排除了 PC 页面、多人预览独占和 Node relay，剩余指向 DV20 摄像头输入、USB 线/接口/供电或设备本体；需要现场硬件动作后复测。
- Vendor `T=1001 L/R` 仍为 `0/0`，wheel raw L/R 非零闭环未完成。当前只能证明 PC 键盘命令已发出、stop 已落稳、命令 raw 非零和 IMU/运动信号存在，不能宣称完整 wheel raw 或完整自动驾驶闭环完成。
- 裸串口并发读 `/dev/ttyS5` 会撞到 `device disconnected or multiple access on port?`；后续复验应继续走
  bridge/API 的固定读回链路，不绕开现有串口 owner 抢读。
