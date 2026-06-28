# PC camera auto shared MJPEG readback

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 的 camera idle readback 从“点击打开后才会接入共享预览”改为：
  `preview_next_action=auto_join_shared_mjpeg_preview`。
- `GET /api/robot-control/camera/mjpeg/status` 同步采用同一口径：打开页面会自动接入共享 MJPEG，多个页面复用同一条上游流。
- 前端普通首屏补齐该 token 的中文翻译，避免把已存在的默认 MJPEG `<img>` 兜底解释成必须手动打开。
- `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md` 已同步更新。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "camera MJPEG|Robot Control summary"`
  - `Test Files 1 passed (1)`
  - `Tests 47 passed | 111 skipped (158)`
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "camera"`
  - `Test Files 1 passed (1)`
  - `Tests 32 passed | 183 skipped (215)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 373 passed (373)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仅输出 chunk size warning，构建成功。
- 通过：7001 只读 status/summary 验证。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001 (LISTEN)`。
  - `GET /api/robot-control/summary` 显示 `shared_preview_exclusive_camera_claim=false`、`safe_to_control=false`、`robot_control_executed=false`。
  - live summary 当前由相机源无帧诊断覆盖 idle 状态：`preview_next_action=check_usb_camera_input_power_or_known_good_uvc`，中文提示为“检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。”
  - `GET /api/robot-control/camera/mjpeg/status` 显示 `preview_status=source_first_frame_failed`、`shared_preview_contract=single_shared_capture_for_multiple_clients`、`shared_preview_exclusive_camera_claim=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只改 PC 只读 readback 和普通首屏文案；不打开新的独占相机采集，不重启上车 camera service。
- 未获得本轮现场安全确认前，不做真实运动、Nav2 execute、free-roam start、keyboard pulse、delivery complete 或 `/cmd_vel`。
