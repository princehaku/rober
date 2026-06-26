# PC 相机 probe 回写 summary

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：PC Node 新增按规范化小车 baseUrl 分组的最近一次 camera first-frame probe 短缓存；`POST /api/robot-control/camera/first-frame/probe` 完成后写入缓存，`GET /api/robot-control/summary` 构建时带入该缓存。
- `pc-tools/workstation/src/server/robotControlSummary.ts` 与 `pc-tools/workstation/src/shared/contracts.ts`：`readback_summary.camera` 新增 `first_frame_probe_status/failure_reason/open_ok/read_ok/visible_content_proven/checked_at_ms`；当 health 仍是 `source_selected_not_probed` 而最近 probe 已失败时，把相机 source 口径覆盖成 `first_frame_failed` 和实际失败原因。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏相机失败提示消费 summary 里的最近 probe 字段；`capture_read_call_timeout` 翻译为“能打开但读帧超时”，避免继续泛化成“没插线”。
- `pc-tools/workstation/test/catalog.test.ts`：扩展 quick probe 回归，断言 probe 后 summary 也能看到 `first_frame_failed` 和最近 probe 短字段，且仍保持 `safe_to_control=false`。

## 验证结果

- `cd pc-tools/workstation && npm test -- catalog.test.ts`：通过，105 tests。
- `cd pc-tools/workstation && npm run build`：通过；仅 Vite chunk size warning。
- 真实 PC 7001 smoke：重启 7001 后，初始 summary 为 `source_readiness=source_selected_not_probed`、`first_frame_probe_status=not_loaded`；触发 `POST /api/robot-control/camera/first-frame/probe` 后约 5 秒返回 `proxy_status=probe_failed`、`status=first_frame_timeout`、`failure_reason=capture_read_call_timeout`、`open_ok=true`、`read_ok=false`、`backend_smoke_status=not_requested`。随后 summary 返回 `source_readiness=first_frame_failed`、`source_failure_reason=capture_read_call_timeout`、`first_frame_probe_status=first_frame_timeout`、`first_frame_probe_open_ok=true`、`first_frame_probe_read_ok=false`、`first_frame_probe_visible_content_proven=false`，且 `safe_to_control=false`。

## 剩余风险

- 本轮修复的是 PC 侧“最近检查结果可见且可刷新保留”，不修复真实摄像头硬件读帧超时。
- PC Node 重启会清空最近 probe 缓存；真实长期状态仍应由上车 `/api/camera/health` 或后续持久 artifact 承担。
- 建图前置仍要求相机首帧真实可见；当前 `capture_read_call_timeout` 下不应开放自动扫图建图。
