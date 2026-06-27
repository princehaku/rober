# PC camera MJPEG status source diagnosis

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/camera/mjpeg/status` 在不创建 MJPEG client、不打开额外相机 reader 的前提下，短读上车 `/api/camera/health`。
  - 当 health 已证明 `source_first_frame_failed` 时，status 回包追加 `source_diagnosis_status/plain_hint/next_action/not_exclusive`，让共享预览状态直接说明“不是页面独占，是 UVC 源无首帧”。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步扩展 `RobotControlCameraMjpegStatusResponse` 合同字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 共享预览状态优先使用 status 里的 `source_diagnosis_plain_hint` 翻译给普通用户，避免只显示内部失败 token。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 补充后端合同和前端文案测试。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`
  - 同步记录共享预览 status 诊断口径。

## 验证结果

- `npm test -- --run catalog.test.ts -t "workstation camera MJPEG status"`
  - 结果：通过，`3 passed | 121 skipped`。
- `npm test -- --run App.test.ts -t "translates camera source first-frame failure from shared MJPEG status"`
  - 结果：通过，`1 passed | 163 skipped`。
- `npm test`
  - 结果：通过，`2 passed`，`288 passed`。
- `npm run build`
  - 结果：通过，生成 `dist/`；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮 status 诊断。
- `curl -sS 'http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' | jq '{proxy_status, client_count, upstream_active, shared_capture, exclusive_camera_claim, last_failure_reason, last_remote_http_status, source_diagnosis_status, source_diagnosis_plain_hint, source_diagnosis_next_action, source_diagnosis_not_exclusive, robot_control_executed}'`
  - 结果：通过；`proxy_status=status_loaded`，`client_count=0`，`exclusive_camera_claim=false`，`source_diagnosis_status=uvc_no_frame_not_exclusive`，`source_diagnosis_plain_hint=不是页面独占：USB Composite Device: DV20 USB  (usb-5310000.usb-1) 当前没人占用，但 UVC 设备没有输出视频帧；检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测。`，`robot_control_executed=false`。

## 剩余风险

- 本轮只改 PC 只读 status 和文案，不修复真实 UVC 无首帧；live 仍需要检查 USB、摄像头输入或供电，必要时换 known-good UVC。
- 本轮不启动 free-roam、不刷新雷达、不执行 Nav2、不发送 manual/keyboard/delivery/stop 或 `/cmd_vel`。
