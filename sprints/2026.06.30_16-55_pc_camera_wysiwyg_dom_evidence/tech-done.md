# 2026.06.30 16:55 PC camera WYSIWYG DOM evidence

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainCameraSharedPreviewDomEvidence`，把 summary 和 MJPEG status 的共享预览事实合并为结构化 DOM 证据。
  - 普通首屏实时画面卡新增 `data-shared-preview-status-source`、`data-shared-preview-client-count`、`data-shared-preview-upstream-active`、`data-shared-preview-content-type-loaded`、`data-shared-preview-cached-frame-loaded`、`data-shared-preview-exclusive-camera-claim`、`data-shared-preview-shared-capture`、`data-shared-preview-single-upstream`、`data-shared-preview-auto-joins`。
  - 实时画面卡、预览框和 MJPEG 图像元素新增 `data-current-frame-visible`、`data-current-mjpeg-frame-visible`、`data-current-video-frame-visible`，让脚本能直接区分“共享流有状态”和“本页真的显示了 MJPEG/视频帧”。
  - 实时画面卡新增固定只读入口 DOM 证据：`data-fixed-shared-preview-endpoint=/api/robot-control/camera/mjpeg` 与 `data-fixed-shared-preview-status-endpoint=/api/robot-control/camera/mjpeg/status`。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定默认首屏未出帧时 `data-current-frame-visible=false`，共享预览仍是单上游且非独占。
  - 锁定 MJPEG `load` 后本页 `data-current-frame-visible=true` / `data-current-mjpeg-frame-visible=true`。
  - 锁定 WebRTC 视频帧绘制后 `data-current-video-frame-visible=true`。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步普通首屏实时画面 WYSIWYG DOM 证据边界。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`。
- 已通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "auto connects shared Camera Preview when the page opens and camera source is ready"`。
- `cd pc-tools/workstation && npm test -- --run`
  - 通过：`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `cd pc-tools/workstation && npm run build`
  - 通过：Vite build 成功；保留既有 `Some chunks are larger than 500 kB after minification` warning。
- `git diff --check`
  - 通过：无 whitespace error。
- 7001 live 只读 HTTP smoke
  - 已重启：`npm run api -- --host 0.0.0.0 --port 7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`。
  - `GET http://127.0.0.1:7001/` 返回当前构建产物：`index-Bzkd1Lvx.js` 与 `index-BZI7zFw0.css`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 HTTP 200，`schema=trashbot.pc_tools_workstation.robot_control_summary.v1`，`camera_status=not_visible`，`camera_wysiwyg=no_current_frame`，`card_count=7`。
  - 当前 JS 产物可匹配 `data-current-frame-visible`、`data-current-mjpeg-frame-visible`、`data-current-video-frame-visible`、`data-shared-preview-status-source` 和 `data-fixed-shared-preview-endpoint`。

## 剩余风险

- 本轮只补 PC Web DOM 证据，不新开相机 capture、不重启相机、不启动 ROS2 runtime、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实画面可见性仍需要现场浏览器或真实 MJPEG/WebRTC 帧验证；本轮测试覆盖的是前端状态转换和 DOM 合同。
