# PC live-summary 画面 WYSIWYG 短 alias

sprint_type: micro

## 实际改动

- 对相机首帧执行只读 `POST /api/robot-control/camera/first-frame/probe` 复测，确认未执行机器人运动，首帧仍 blocked。
- `live_closure_summary` 和 `/api/robot-control/live-summary` 新增 `camera_*` 短 alias，直接暴露首帧 probe 状态、失败原因、是否页面独占、USB 速度、下一步恢复动作和固定只读复测端点。
- 普通首屏 WYSIWYG 诊断 DOM 增加对应 `data-camera-*` 字段，现场 DOM smoke 可以直接判断“画面未显示是 USB full-speed/无首帧，不是页面独占”。

## 验证结果

- 只读相机首帧复测：`POST /api/robot-control/camera/first-frame/probe` 返回 `status=blocked`、`robot_control_executed=false`，未触发运动入口；随后 summary 显示 `first_frame_probe_status=blocked`、`source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`source_diagnosis_not_exclusive=true`、`shared_preview_exclusive_camera_claim=false`、`uvc_usb_topology_video_usb_speed=12M`。
- `cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "minimal precheck fields for same-window wheel rerun"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，1 passed。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单包 chunk 超过 500 kB，这是既有体积提醒，不影响本轮功能。
- `cd pc-tools/workstation && npm test`：通过，3 files / 418 tests。
- `git diff --check`：通过。
- 运行态只读确认：PC API 已重启到 `0.0.0.0:7001`，`GET /api/robot-control/live-summary` 返回 `camera_current_visible=false`、`camera_first_frame_probe_status=source_first_frame_failed`、`camera_first_frame_failure_reason=first_frame_total_timeout`、`camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_source_diagnosis_not_exclusive=true`、`camera_shared_preview_exclusive_camera_claim=false`、`camera_usb_speed=12M`、`camera_recovery_sends_motion=false`、`camera_recovery_starts_map_runtime=false`，同时 `radar_map_points_visible=true`。

## 剩余风险

- 当前相机真实状态仍是 `camera_current_visible=false`，现场读数指向 USB 12M full-speed 首帧失败；需要换高速 USB 口/线或带供电 USB Hub 后再次复测。
- 完整 Nav2 路线仍卡在同窗口轮速 L/R 非零复验，delivery success 仍需现场安全确认后的执行闭环。
