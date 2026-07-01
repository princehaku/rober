# PC 建图相机阻塞快捷卡

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainLiveMappingUnblockActionCards`，当建图未 ready 且 `mapping_camera_blocks_start=true` 时，在当前卡点区展示 `plain-live-mapping-unblock-actions`。
  - 新卡 `plain-live-mapping-unblock-action-camera_first_frame` 只复用相机首帧 probe、共享 MJPEG 状态和 summary 刷新，帮助现场快速解除“建图只差相机首帧”的阻塞。
  - 按钮 `plain-live-mapping-unblock-action-run-camera_first_frame` 固定走 `refreshMappingCameraRecovery`，不启动建图、不启动自由移动、不执行 Nav2、不发 manual/keyboard/delivery/stop。
- `pc-tools/workstation/src/styles.css`
  - 新增 `plain-live-mapping-unblock-actions` / `plain-live-mapping-unblock-action` 样式，和 ready motion 卡保持相邻但视觉区分。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖新快捷卡的 DOM 合同和点击行为，确认只调用 camera first-frame probe、camera MJPEG status、summary，不调用运动或建图接口。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-07-01 11:45 CST 起的建图相机阻塞快捷卡合同。

## 验证结果

- `npm test -- --run test/App.test.ts -t "rechecks mapping camera recovery without starting motion or map runtime"`：通过，`1 passed | 230 skipped`。
- `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，`1 passed | 230 skipped`。
- `npm run lint`：通过。
- `npm run build`：通过；仍有既有 Vite chunk size warning。
- `npm test`：通过，`3 passed / 417 tests passed`。
- `git diff --check`：通过。
- `GET http://127.0.0.1:7001/api/robot-control/summary` no-motion smoke：通过。当前 live summary 显示 `mapping_start_ready=false`、`mapping_start_missing_reasons=["camera_first_frame"]`、`mapping_camera_blocks_start=true`，recovery sequence 为 `/api/robot-control/camera/first-frame/probe,/api/robot-control/camera/mjpeg/status,/api/robot-control/summary`，`mapping_unblock_sends_motion_when_clicked=false`。
- `GET http://127.0.0.1:7001/`：通过，HTTP 200，返回当前构建资源 `index-Ca7yck5c.js` / `index-B5oXWzbx.css`。

## 剩余风险

- 本轮只改善 PC 端建图相机阻塞的发现和复测入口。
- 真实摄像头首帧是否恢复、wheel raw L/R 非零、delivery success、真实建图启动仍需要现场/上车证据继续闭环。
