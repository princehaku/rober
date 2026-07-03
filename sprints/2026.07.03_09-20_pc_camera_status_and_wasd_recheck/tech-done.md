# 2026-07-03 09:20 PC 相机状态与 WASD 复核

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 修正 `/api/robot-control/camera/mjpeg/status` 的 `preview_status` 判定：当上车 health 已给出 `source_readiness=first_frame_failed`、已知首帧失败 reason，或 `source_diagnosis_status=uvc_full_speed_usb_not_exclusive` 时，PC 共享预览 status 直接返回 `source_first_frame_failed`，不再误报 `idle_not_started`。
  - 该端点仍只读 health/relay 状态，不创建额外 MJPEG client，不发送 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 补充 2026-07-03 现场口径：普通用户继续用 PC 大地图页；RViz2/Foxglove 只作为 ROS2 工程观察工具。
  - 记录相机真实 blocker 是 DV20 摄像头挂在 USB 12M full-speed 后首帧失败，不是页面独占。
  - 记录本轮手控与 wheel raw 证据边界：命令非零已证明，`T=1001` wheel raw L/R 非零仍未证明。

## 验证结果

- 本地自动化：
  - `npm test -- catalog.test.ts` 通过：1 file，185 tests。
  - `npm test -- App.test.ts robotControlSummary.test.ts` 通过：2 files，250 tests。
  - `npm run build` 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- 本机服务：
  - 已重启 PC workstation API：`HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 确认 `node` 监听 `*:7001`。
- 真实上位机读回：
  - `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 返回
    `status=source_first_frame_failed`、`preview_status=source_first_frame_failed`、
    `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`source_readiness=first_frame_failed`、
    `source_failure_reason=first_frame_total_timeout`、`camera_usb_speed=12M`、
    `shared_preview_everyone_can_join=true`、`source_usage_scope=free`。
  - `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回
    `proxy_status=preview_forwarded`、`robot_pose_status=map_pose_observed`、`route_target_visible=true`、
    `path_preview_point_count=18`、`radar_overlay_status=loaded`、`radar_overlay_point_count=75`。
  - PC manual WASD 快路径按 `forward/back/left/right` 各发低速短脉冲，均返回
    `proxy_status=command_forwarded`，单次约 `0.176s-0.186s`。
  - PC `/api/robot-control/base/manual` 对 `back` 返回 `remote_motion_key_values.manual_command_executed=true`、
    `auto_stop_executed=true`；`first-jog` 证据路径也返回 80 帧 bridge feedback，但 wheel raw L/R 非零未证明。
  - 上位机 ROS `/cmd_vel -> esp32_bridge` 路径直接 smoke：`direction=back`、`speed=0.04`、`duration_ms=300` 返回
    `manual_command_executed=true`、`auto_stop_executed=true`，command debug 记录
    `vendor_command {"T":11,"L":-255,"R":-255}`，随后 stop `{"T":11,"L":0,"R":0}`。

## 剩余风险

- 摄像头还没有真实画面：`/dev/video1` 当前在 USB 12M full-speed，V4L2/ffmpeg STREAMON/首帧仍失败；需要把 DV20 摄像头换到高速 USB 口/线或带供电 Hub 后复测。
- wheel raw L/R 非零仍未证明：真实 `wave_rover_feedback_debug.jsonl` 的 `T=1001` 帧仍为 `L=0,R=0`，即使命令窗口内已经证明 `T=11` 非零命令。下一轮应继续定位 ESP32/WAVE ROVER feedback 字段、反馈节奏或底盘固件是否实际上报轮速。
- PC manual 快路径为低延迟继续使用 `command_mode=pwm + feedback_mode=realtime`；这条路径不会刷新 `esp32_bridge` command debug。需要命令日志证据时，应走上位机 ROS `/cmd_vel` 或 first-jog/bridge_debug 证据路径。
