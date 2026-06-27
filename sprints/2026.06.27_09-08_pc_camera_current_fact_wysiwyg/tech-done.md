# PC 摄像头当前事实所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainCurrentCameraFactText()`，让普通首屏“当前事实”直接区分摄像头首帧失败是占用问题、非独占无帧，还是 backend smoke 多方式无帧。
  - live 形态 `source_first_frame_failed + source_usage_status=not_in_use + capture_read_returned_false` 会显示“不是独占，摄像头没人占用但没有输出视频帧”。
- `pc-tools/workstation/test/App.test.ts`
  - 加强摄像头共享预览失败用例，覆盖“当前事实”文案，同时保持不泄露 `capture_read_returned_false` / `camera_mjpeg_proxy_failed` 等工程 token。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录摄像头当前事实条的 WYSIWYG 口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "uses camera health first-frame failure|explains a live not-in-use camera first-frame failure"`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。Vite 仍提示既有单 chunk 大于 500 kB warning，不影响本轮改动。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed / 280 passed`。
- 通过：`git diff --check`。
- 通过：PC Node 继续监听 `0.0.0.0:7001`，`lsof` 显示 PID `69539` 监听 `TCP *:7001`。
- live 只读确认：`readback_summary.camera.status=source_first_frame_failed`、
  `source_usage_status=not_in_use`、`source_failure_reason=capture_read_returned_false`、
  `shared_preview_exclusive_camera_claim=false`，与本轮 WYSIWYG 文案覆盖场景一致。

## 剩余风险

- 本轮只修普通首屏摄像头失败归因展示，不修复真实 UVC/USB 摄像头无首帧问题。
- 当前 live camera 仍是 `source_first_frame_failed`，摄像头读到真实帧之前不能按可建图验收。
