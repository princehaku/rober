# Live WYSIWYG Focused Refresh

sprint_type: micro

## 实际改动

- 先按当前 summary 的 no-motion `all_wysiwyg` 序列执行现场只读刷新：雷达 scan-proof refresh、雷达 status、map preview、相机 first-frame probe、相机 MJPEG status、summary。
- 只读刷新结果：雷达地图贴图从 `not_current` 恢复为 `loaded`，当前地图雷达点 43 个，WYSIWYG 缺口从 `camera + radar_map_points` 收敛为只剩 `camera`。
- 补齐 PC `GET /api/robot-control/summary` 顶层 `live_wysiwyg_focused_refresh_*` 字段，明确当前缺口的聚焦刷新序列；雷达贴图已当前后 focused mode 为 `camera_only`。
- 同步 TypeScript 合同、summary 单测和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts catalog.test.ts`：通过，3 个测试文件、428 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 保留既有 large chunk 提醒。
- `git diff --check`：通过。
- 已重启 PC Node，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` PID 40674 监听 `TCP *:7001`。
- 只读 smoke `GET http://127.0.0.1:7001/api/robot-control/summary`：`field_acceptance_wysiwyg_missing_surface_ids=["camera"]`，
  `live_wysiwyg_focused_refresh_mode=camera_only`，focused sequence 为 camera first-frame probe、MJPEG status、summary，
  雷达 refresh/map refresh flags 为 `false`，`live_wysiwyg_focused_refresh_sends_motion=false`。
- `/map` HTTP smoke：`200 text/html; charset=utf-8`。

## 剩余风险

- 相机 first-frame probe 仍返回 `probe_failed` / `remote_http_status=503` / `failure_reason=deadline_expired`，诊断仍为 USB 12M/full-speed；需要现场换高速 USB 后再复测。
- 本轮没有新的现场安全确认，因此没有执行 Nav2、键盘 manual、free-roam、delivery complete、stop 或 `/cmd_vel`。
