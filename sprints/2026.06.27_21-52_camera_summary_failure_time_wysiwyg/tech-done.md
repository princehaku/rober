# Camera Summary Failure Time WYSIWYG

sprint_type: micro

## 实际改动

- 修正 PC `GET /api/robot-control/summary` 的相机共享预览 overlay：没有 MJPEG relay failure 时，也短读 camera health 并复用 `camera_source_first_frame_failed` source-failure overlay。
- summary 现在会与 `/api/robot-control/camera/mjpeg/status` 一致展示 `shared_preview_last_failure_reason`、`shared_preview_last_remote_http_status` 和 `shared_preview_last_failure_at_ms`。
- 扩展 catalog 测试，覆盖只访问 summary、不打开 MJPEG 流时仍能看到相机源首帧失败时间，同时确认没有请求 `/api/camera/mjpeg`。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "source first-frame failure"`，1 个文件通过，2 个命中测试通过。
- 通过：`cd pc-tools/workstation && npm test`，2 个文件通过，315 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示单 chunk 超过 500 kB 的既有体积提醒。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只同步画面失败时间的只读显示，不修复 UVC 无首帧硬件问题，不创建 MJPEG client，不发送 manual/free-roam/Nav2/stop 或 `/cmd_vel`。
