# 2026.06.27 16:51 PC 共享画面 summary 诊断兜底

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 共享画面状态在 MJPEG status 轮询失败、只能使用 Robot Control summary 时，也把 `readback_summary.camera.source_diagnosis_plain_hint` 传入失败文案。
  - 当 summary 已证明 `uvc_no_frame_not_exclusive` 时，普通首屏继续显示“不是页面独占、UVC 设备没有输出视频帧”等具体诊断，不退回内部 token 或泛化失败。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 status 端点失败、summary 带 `source_diagnosis_plain_hint` 的分支。
  - 继续断言不会自动请求 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md`
  - 记录共享画面 WYSIWYG fallback 口径。

## 验证结果

- `npm test -- --run test/App.test.ts -t "shared camera|source first-frame|MJPEG status|shared preview"`：通过，8 passed。
- `npm test -- --run`：通过，2 files / 298 tests passed。
- `npm run build`：通过，生成新前端 bundle `/assets/index-Cmlq3fJ_.js`。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 7001 live 只读 HTTP 验证：
  - `GET /` 返回新 bundle `/assets/index-Cmlq3fJ_.js`。
  - `GET /api/robot-control/camera/mjpeg/status` 返回 `last_failure_reason=camera_source_first_frame_failed`，并包含 `source_diagnosis_plain_hint=不是页面独占：USB Composite Device: DV20 USB ... UVC 设备没有输出视频帧`。

## 剩余风险

- 本轮只修正 PC 画面失败归因展示，不修复 DV20 UVC 实际无首帧；摄像头仍需硬件/输入/供电或 known-good UVC 复测。
- 本轮未发起 camera offer、manual、keyboard、free-roam start/stop、Nav2、delivery、stop 或 `/cmd_vel`，不声称真实画面已恢复或小车已移动。
