# PC Summary 共享画面源无首帧 Overlay

sprint_type: micro

## 设计结论

- 上一轮让 `/api/robot-control/camera/mjpeg/status` 能显示 `camera_source_first_frame_failed`，但 live summary 仍显示 `shared_preview_last_failure_reason=none`。
- 普通首屏、status fallback 和只读 summary 必须对“不是独占，是相机源无首帧”给出一致结论。
- summary 已经读取 `/api/camera/health`，因此本轮不新增额外 Robot API 读取，只在 summary builder 里派生共享预览失败原因。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `cameraSummaryFromReadbacks` 在 MJPEG relay overlay 没有失败记录时，根据 camera health 的 `source_first_frame_failed`、`first_frame_failed`、`capture_read_returned_false`、`capture_read_call_timeout` 或 `first_frame_timeout` 派生 `shared_preview_last_failure_reason=camera_source_first_frame_failed`。
  - `shared_preview_last_remote_http_status` 使用 camera health readback 的 HTTP 状态；`shared_preview_last_failure_at_ms` 不伪造，仍为 `none`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 summary 只读回归，确认只看 `/api/robot-control/summary` 时也能看到 `camera_source_first_frame_failed`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 status polling 失败时的 fallback 回归，确认普通首屏从 summary 翻译源无首帧，不泄露内部 token。
- `docs/product/pc_tools_workstation.md`
  - 记录 summary 与 status 的共享画面失败原因口径一致。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "source first-frame failure"`
  - `Test Files 1 passed (1)`
  - `Tests 2 passed | 117 skipped (119)`
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "source first-frame failure"`
  - `Test Files 1 passed (1)`
  - `Tests 4 passed | 151 skipped (155)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 保留既有 chunk size warning，本轮无新增构建失败。
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 274 passed (274)`
- 通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node` PID `55670` 监听 `TCP *:7001`。
  - `curl http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`、`pc_only=true`、`safe_to_control=false`。
  - `curl /api/robot-control/summary` 返回 live camera：`status=source_first_frame_failed`、`shared_preview_last_failure_reason=camera_source_first_frame_failed`、`shared_preview_last_remote_http_status=200`、`shared_preview_last_failure_at_ms=none`、`source_failure_reason=capture_read_returned_false`、`source_usage_owner_count=0`。

## 剩余风险

- 本轮只修 summary/status/首屏状态一致性，不修复真实摄像头无首帧。
- 当前 `/dev/video1` 仍需要现场检查 DV20/UVC 输出、USB 线/供电、采集卡输入模式或替换 known-good UVC。
