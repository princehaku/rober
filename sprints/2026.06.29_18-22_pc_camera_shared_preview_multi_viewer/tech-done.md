# PC Camera Shared Preview Multi Viewer Readback

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：MJPEG status 响应新增 `shared_preview_multi_viewer_status` 和 `shared_preview_multi_viewer_plain`，把单上游、多页面共享、非独占摄像头口径变成稳定只读字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：`readback_summary.camera` 同步新增多人共享预览字段，并在 fail-closed 默认相机摘要中保留该合同。
- `pc-tools/workstation/src/shared/contracts.ts`：补充 camera summary 和 MJPEG status 的字段类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏实时画面卡新增“多人预览”行，高级诊断同步显示新字段。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：覆盖首屏多人预览、summary 字段、MJPEG status 字段和单上游多客户端共享证据。
- `pc-tools/README.md`：记录 PC camera 共享预览多人只读合同和风险边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`
  - `Test Files 1 passed (1)`，`Tests 166 passed (166)`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`，`Tests 218 passed (218)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过；保留既有 Vite chunk 大小提示。
- 通过：`git diff --check`
  - 无输出。
- 通过：重启 `HOST=0.0.0.0 PORT=7001 npm run api` 后只读验证。
  - `lsof` 显示 `node` 监听 `TCP *:7001 (LISTEN)`，日志显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
  - MJPEG status 只读返回 `shared_preview_multi_viewer_status=single_upstream_multi_viewer`、`client_count=0`、`upstream_active=false`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`robot_control_executed=false`。
  - summary 只读返回 `camera_status=source_first_frame_failed`、`preview_visible_status=not_visible_source_first_frame_failed`、`shared_preview_multi_viewer_status=single_upstream_multi_viewer`、`source_usage_owner_count=0`。

## 剩余风险

- 本轮证明“多人页面接入同一个 PC 共享 relay，不是页面独占”，不证明摄像头源已经出帧。
- live 仍显示 `source_first_frame_failed` 和 `uvc_no_frame_not_exclusive`，且 `source_usage_owner_count=0`；下一步应继续排查 USB、摄像头输入/供电或用 known-good UVC 复测。
- 本轮不打开 MJPEG 流、不启动 first-frame probe、不发送 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`。
