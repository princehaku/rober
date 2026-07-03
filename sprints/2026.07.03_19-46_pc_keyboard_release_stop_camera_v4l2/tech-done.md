# PC Keyboard Release Stop + Camera V4L2 Evidence

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/client/workstationApi.ts`：`GET /api/robot-control/summary` 支持携带当前浏览器键盘 hold 证据 query，包括连续 pulse 数、阈值、当前方向和松开后 stop 是否落稳。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：PC 普通页刷新 summary 时同步本地 WASD/方向键按住窗口证据；只有本次连续 pulse 达到阈值、release stop 已转发成功，且最近 keyboard manual 回包有运动信号/IMU/轮速证据时，才上报 `keyboard_motion_verified=true`。
- `pc-tools/workstation/src/server/index.ts` 与 `pc-tools/workstation/src/server/robotControlSummary.ts`：Node summary/live-summary 解析键盘本地证据；`stop_after_release` 只由本地 release stop 证据清除，`same_hold_window_wheel_lr_nonzero` 仍要求已有后端运动信号或本地 `keyboard_motion_verified=true`，默认无证据仍保持 false。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：新增回归测试，覆盖默认 summary 不清键盘 stop 缺口、带足本地 pulse+stop 证据后 `keyboard_continuous_motion_verified=true`。
- `docs/product/pc_tools_workstation.md`：同步当前产品口径；记录键盘本地 evidence query 合同，以及现场相机复核结论：停止 8088 后无 owner 直连 V4L2 仍 0 字节无帧，当前图传缺口不是页面独占。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/robotControlSummary.test.ts -t "keyboard stop-after-release"`，`1 passed | 13 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- test/robotControlSummary.test.ts test/App.test.ts -t "keyboard"`，`24 passed | 229 skipped`。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript + Vite + server 编译通过。
- 通过：本机 PC Node 已重启并监听 `0.0.0.0:7001`；`GET /api/health` 返回 `default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787&keyboard_*...` 在带本地 keyboard hold 证据时返回 `keyboard_stop_after_release=true`、`keyboard_stop_settled_after_pulse=true`、`current_keyboard_control_pack_missing_evidence=[]`；不带 `keyboard_*` query 时仍保守返回 `keyboard_stop_after_release=false`、缺口包含 `stop_after_release`。
- 现场相机只读复核：上位机停止 `trashbot-local-webrtc-camera.service` 后 `/dev/video1`/`/dev/video2` 无占用；`v4l2-ctl` 直连 `MJPG@640x480@30` 与 `YUYV@320x240` 都能 `STREAMON`，但 10 秒超时且输出 0 字节；服务恢复后 `/api/camera/mjpeg/status` 仍为 `source_first_frame_failed`、`uvc_no_frame_not_exclusive`、`exclusive_camera_claim=false`、`source_usage_owner_count=0`。

## 剩余风险

- 键盘证据来自当前浏览器会话，不是服务端持久状态；直接 curl summary 若不带 `keyboard_*` query，仍会按保守默认返回键盘 stop 未验证。
- 摄像头仍无真实首帧，剩余风险在 DV20 摄像头输入、USB 线/接口/供电或设备本体；需要线下处理或换 known-good UVC 后再复测。
- 本轮没有修复 wheel raw `L/R` 非零、delivery success 或真实 Nav2 复跑。
