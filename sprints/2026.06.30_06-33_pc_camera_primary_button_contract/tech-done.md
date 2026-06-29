# PC 实时画面主按钮 WYSIWYG 合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainCameraPrimaryActionEvidence`，把实时画面主按钮的点击语义结构化为 `open_shared_preview`、`retry_shared_preview` 或 `retry_camera_preview`。
  - `plain-camera-start` 按钮新增 DOM 合同：`data-primary-action-kind`、`data-target-source=shared_camera_preview`、`data-sends-motion-when-clicked=false`、共享预览单上游/自动接入、当前帧可见性和固定 MJPEG/status 入口。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖初始首屏按钮不发车、只接入共享预览。
  - 覆盖 MJPEG 实际出帧后按钮 `data-current-frame-visible=true`。
  - 覆盖相机非独占无帧时按钮语义为 `retry_shared_preview`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录实时画面主按钮的所见即所得和 no-motion 边界。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|renders cached MJPEG frame as current visible frame|turns camera source first-frame failure into a plain first-screen hint"`：通过，`2 passed | 217 skipped`；其中 `renders cached...` 标题未命中，已改跑准确用例名。
- `npm test -- test/App.test.ts -t "auto connects shared Camera Preview when the page opens and camera source is ready"`：通过，`1 passed | 218 skipped`。
- `npm test -- --run`：通过，`2 passed`，`389 passed`。
- `npm run build`：通过，生成 `dist/assets/index-BEa3Q8yb.js` 与 `dist/assets/index-BmaNglvi.css`。
- `git diff --check`：通过，无空白错误。
- 7001 smoke：重启 PC 工作站后，`node` PID `45487` 监听 `*:7001`；`curl -fsS http://127.0.0.1:7001/` 返回当前 `index-BEa3Q8yb.js` / `index-BmaNglvi.css`；dist 可检出 `primary-action-kind`、`retry_shared_preview`、`shared_camera_preview`、`sends-motion-when-clicked` 和 `fixed-shared-preview-endpoint`。

## 剩余风险

- 本轮只补 PC Web DOM 合同和测试，不重启相机、不独占摄像头、不启动 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实摄像头首帧、真实共享 MJPEG 画面质量和多人同时观看仍需要现场硬件验证。
