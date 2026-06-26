# PC 摄像头首帧 probe overlay 回填 summary

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - Robot Control summary 现在会消费最近一次只读首帧 probe overlay。
  - 当上车 `/api/camera/health` 仍停在旧的 `source_first_frame_failed`，但 PC Node 内存 overlay 明确 `probe_forwarded + open_ok=true + read_ok=true + visible_content_proven=true` 时，summary 将相机状态提升为 `ready`，`source_readiness=first_frame_observed`，`source_failure_reason=none`。
  - 失败或不可见的 probe 仍保持失败口径，不会把黑帧/无帧误报成可见画面。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 server 集成测试，锁定成功首帧 probe overlay 能覆盖 stale source failure，并保留 `first_frame_probe_*` 证据字段。
- `docs/product/pc_tools_workstation.md`
  - 同步记录只读首帧 probe overlay 的刷新后 WYSIWYG 行为和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "first-frame probe overlay"`
  - `Test Files 1 passed (1)`
  - `Tests 1 passed | 115 skipped (116)`
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 153 passed (153)`
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 116 passed (116)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 保留既有 chunk size warning，本轮无新增构建失败。
- 通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node` PID `84845` 监听 `TCP *:7001`。
  - `curl http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`、`safe_to_control=false`、`pc_only=true`。
- 通过：live 只读 camera first-frame probe
  - `POST /api/robot-control/camera/first-frame/probe?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=probe_failed`、`failure_reason=The operation was aborted due to timeout`、`robot_control_executed=false`、`safe_to_control=false`。
  - 随后 `GET /api/robot-control/summary` 返回 `first_frame_probe_status=blocked`、`first_frame_probe_failure_reason=The operation was aborted due to timeout`、`source_usage_owner_count=0`、`source_failure_reason=capture_read_returned_false`，证明失败 overlay 已回填 summary；live 仍是相机源无帧/超时，不是页面独占。

## 剩余风险

- 本轮修的是成功首帧 probe 后的 summary/首屏状态回填，不修复 live `/dev/video1` 当前首帧读取失败根因。
- live 如果 probe 仍失败，summary 会继续保持失败，这是预期 fail-closed 行为。
