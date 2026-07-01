# PC 相机 USB full-speed 恢复证明

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainCameraUsbRecoveryProofSummary`，把相机 USB 12M full-speed、不是页面独占、换高速 USB 后复测、阻塞建图但不阻塞自由移动汇总成普通相机卡片内的一条可见证明。
  - 新增 `plain-camera-usb-recovery-proof` DOM，只读暴露 camera probe、MJPEG status、summary 复测链路，并声明不启动独占相机、建图 runtime、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 USB full-speed 相机恢复测试，锁定相机卡片内的新证明行、只读 endpoint 和 no-motion/no-runtime 边界。
- `docs/product/pc_tools_workstation.md`
  - 记录相机卡片 USB full-speed 硬件恢复证明合同。

## 现场 no-motion 复验证据

- `POST http://127.0.0.1:7001/api/robot-control/radar/scan-proof/refresh`
  - 返回 `status=loaded_fail_closed_summary`
  - 返回 `robot_control_executed=false`
- `GET http://127.0.0.1:7001/api/robot-control/map/preview`
  - `radar_overlay_status=loaded`
  - `radar_overlay_current_point_count=2`
  - `radar_overlay_source_point_count=2`
  - `radar_overlay_needs_refresh=false`
- `POST http://127.0.0.1:7001/api/robot-control/camera/first-frame/probe`
  - `status=first_frame_timeout`
  - `camera_first_frame_ready=false`
  - `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`
  - `source_diagnosis_not_exclusive=true`
  - `camera_usb_speed=12M`
  - `camera_hardware_action_required=true`
  - `camera_hardware_action_label=换高速USB后复测`
  - `camera_blocks_mapping_start=true`
  - `camera_blocks_free_move=false`
  - `robot_control_executed=false`
- `GET http://127.0.0.1:7001/api/robot-control/summary`
  - `live_wysiwyg_missing_surface_ids=["camera"]`
  - `radar_map_points_visible=true`
  - `mapping_lidar_fresh_readback_ready=true`
  - `mapping_start_missing_reasons=["camera_first_frame"]`

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 233 passed (233)`
- 已通过：`npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`
  - `Test Files 2 passed (2)`
  - `Tests 190 passed (190)`
- 已通过：`npm --prefix pc-tools/workstation run lint`
- 已通过：`npm --prefix pc-tools/workstation run build`
  - Vite 输出既有 chunk size warning；构建成功。
- 已通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Test Files 3 passed (3)`
  - `Tests 423 passed (423)`
- 已通过：重启 `0.0.0.0:7001`
  - 当前监听：`node` PID `89987`，`TCP *:7001 (LISTEN)`
  - `GET http://127.0.0.1:7001/` -> `200`
  - `GET http://127.0.0.1:7001/map` -> `200`
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 只读 smoke 读到：`live_wysiwyg_missing_surface_ids=["camera"]`、`camera_usb_speed=12M`、`camera_usb_full_speed_detected=true`、`camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`、`radar_map_points_visible=true`、`radar_overlay_status=loaded`、`mapping_lidar_fresh_readback_ready=true`、`mapping_start_missing_reasons=["camera_first_frame"]`。

## 剩余风险

- 本轮仍未执行任何运动控制；自由移动、Nav2、键盘 wheel L/R 非零和 delivery success 需要现场安全确认后另行实车验证。
- 当前真实 WYSIWYG 只剩相机首帧缺口；证据显示不是页面独占，而是 USB 12M full-speed/首帧 timeout，需要换高速 USB 口/线或带供电 Hub 后复测。
- 未触碰两份历史 dirty artifact：`sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`、`sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`。
