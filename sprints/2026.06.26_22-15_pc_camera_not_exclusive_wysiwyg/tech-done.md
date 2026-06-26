# PC Camera Not-Exclusive WYSIWYG

sprint_type: micro

## 实际改动

- 普通首屏相机失败文案在 `source_usage_status=not_in_use` 时明确显示“不是页面独占”，并把 live `capture_read_returned_false` 翻译为“摄像头没有输出视频帧”。
- 新增 App 回归测试，覆盖 live 形状：`source_first_frame_failed + first_frame_failed + capture_read_returned_false + not_in_use + shared_preview_exclusive_camera_claim=false`。
- 更新 PC 工作站产品文档，记录该文案只修正 WYSIWYG 归因，不触发 camera offer/MJPEG/probe 或任何运动接口。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts`：通过，140 tests passed。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB 的既有体积 warning。
- `git diff --check`：通过。
- 真实 PC 7001 只读 smoke：summary 返回 `robot_api_connection.status=readable`、`safe_to_control=false`、
  `camera.status=source_first_frame_failed`、`source_readiness=first_frame_failed`、
  `source_failure_reason=capture_read_returned_false`、`source_usage_status=not_in_use`、
  `source_usage_owner_count=0`、`shared_preview_exclusive_camera_claim=false`、`dangerous_true_fields=[]`。
- PC Node 已重启并监听 `*:7001`，让前端新普通文案生效。

## 剩余风险

- 本轮只修正 PC 普通首屏归因文案，不修复真实 `/dev/video1` 无视频帧的硬件/驱动问题。
- 真实 smoke 证明当前摄像头不是 PC 页面独占；剩余问题是设备/输入没有输出可读视频帧。
