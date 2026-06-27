# PC 摄像头最近帧缓存所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - summary 的 MJPEG relay overlay 同步带出 `cached_frame_loaded/cached_frame_age_ms`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `readback_summary.camera` 新增 `shared_preview_cached_frame_loaded/shared_preview_cached_frame_age_ms`。
  - 默认 blocked/not-loaded summary 显式返回 `false/none`，避免普通首屏误报缓存帧。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 Robot Control summary camera 契约。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏“共享画面”行在上游已连接、已拿到视频边界且有缓存帧时，显示“已有最近帧缓存，后进页面会先显示最近帧”。
  - 该文案只说明 PC Node 共享预览的后进页面体验，不把缓存帧算作建图 camera ready，也不替代浏览器真实绘制帧证据。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定普通首屏缓存帧文案。
- `pc-tools/workstation/test/catalog.test.ts`
  - 锁定 summary 默认无缓存帧与 streaming 时缓存帧字段。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步共享画面缓存帧的产品口径与安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --testNamePattern "shared camera|MJPEG|camera MJPEG|共享画面" --maxWorkers=1 --no-fileParallelism`
  - `Test Files 2 passed (2)`，`Tests 14 passed | 309 skipped (323)`
- 通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - `Test Files 2 passed (2)`，`Tests 323 passed (323)`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite 仍提示单 chunk 超过 500 kB；本轮未改变该既有打包策略。
- 通过：`git diff --check`

## 剩余风险

- 本轮提升 PC 普通首屏的画面 WYSIWYG 解释；不证明真实 DV20/UVC 已经输出首帧。
- 当前 live 7001 只读状态仍显示 `uvc_no_frame_not_exclusive` 时，现场仍需检查 USB 摄像头输入、供电或替换 known-good UVC。
