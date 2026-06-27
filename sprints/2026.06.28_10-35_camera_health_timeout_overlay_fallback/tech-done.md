# Camera Health 超时保留共享预览诊断

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - summary handler 构造 `mjpegRelayOverlay` 时，透传 source diagnosis 字段：
    `source_diagnosis_status/plain_hint/next_action/not_exclusive`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `RobotControlCameraMjpegRelayOverlay` 类型增加 source diagnosis 字段。
  - 当 `/api/camera/health` 在 summary 短预算内 timeout，但共享预览覆盖已证明 `camera_source_first_frame_failed` 时，
    `readback_summary.camera.status` 继续显示 `source_first_frame_failed`。
  - 当 health payload 没有 source diagnosis 时，使用共享预览覆盖的 `uvc_no_frame_not_exclusive` 诊断。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增测试覆盖 `camera_health=fetch_timeout` 但 overlay 仍有“不是独占、UVC 无帧”诊断的 live 形态。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 camera health 超时时 summary 不退回 `fetch_failed/not_loaded` 的 WYSIWYG 口径。

## 验证结果

- `npm test -- --testNamePattern "camera health times out|first-screen budget|Camera|camera" --maxWorkers=1 --no-fileParallelism`
  - 通过：47 passed, 283 skipped。
- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：330 passed。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；仍有既有 Vite chunk size warning。
- `git diff --check`
  - 通过。
- `HOST=0.0.0.0 PORT=7001 npm run api:public`
  - 已重新启动 PC Node，`node` 监听 `*:7001`。
- `curl -sS --max-time 5 http://127.0.0.1:7001/api/robot-control/summary`
  - 只读复验通过：`camera.status=source_first_frame_failed`。
  - 只读复验通过：`camera.shared_preview_last_failure_reason=camera_source_first_frame_failed`。
  - 只读复验通过：`camera.source_diagnosis_status=uvc_no_frame_not_exclusive`。
  - 只读复验通过：`camera.source_diagnosis_plain_hint` 明确写明“不是页面独占”，下一步是检查 USB、摄像头输入/供电或换 known-good UVC。
  - 现场状态仍显示 `radar.lifecycle_state=stopped`、`radar.runtime_scan_status=stale`、`map.radar_overlay_status=not_current`。

## 剩余风险

- 本轮只复用 PC Node 已有只读诊断，不创建新的 camera reader。
- 摄像头真实首帧仍需现场检查 USB、摄像头输入/供电或换 known-good UVC。
- 当前只读 summary 还显示 `status`、`camera_health`、`camera_devices` 有 `fetch_timeout_2400ms`；本轮修的是首屏诊断不丢失，不等于上位机摄像头源端已恢复出图。
- 当前只读 summary 仍显示雷达 stopped/stale，地图雷达叠加保持 `not_current` 是预期保护，不代表雷达已 ready。
- 本轮不发送真实运动、Nav2、free-roam、delivery、stop 或 `/cmd_vel` 命令。
