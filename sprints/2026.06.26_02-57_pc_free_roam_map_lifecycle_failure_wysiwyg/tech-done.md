# 2026.06.26 02:57 PC 扫图地图 Lifecycle 失败 WYSIWYG

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `mapLifecycleFailed()` 与 `mapLifecycleFailureText()`，把地图记录/保存失败翻译成普通首屏短原因。
  - 普通首屏地图流程 marker 在 map start/save 失败后显示 `地图记录启动失败：<短原因>` 或 `地图保存失败：<短原因>`，不再消失或回落成待开始状态。
  - `扫图状态` 与扫地式建图卡片 hint 同步显示同一失败原因，避免地图和卡片说法不一致。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `keeps failed free-roam map lifecycle visible on the map`，覆盖 map start `fetch_timeout` 时 marker、ARIA、扫图状态和 hint 均保留失败原因。
- `docs/product/pc_tools_workstation.md`
  - 同步记录地图 lifecycle 失败态贴回地图和状态行的产品口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "keeps failed free-roam map lifecycle visible on the map"`
  - 结果：通过，`1 passed | 182 skipped (183)`。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过，`eslint .` 无报错。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `cd pc-tools/workstation && npm test`
  - 结果：通过，`2 passed (2)`，`183 passed (183)`。
- `git diff --check`
  - 结果：通过，无空白错误。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node` 正在监听 `TCP *:7001 (LISTEN)`。

## 验证副作用处理

- 全量 Vitest 会刷新旧 DOM smoke artifact 的 `checked_at` 字段；本轮已将
  `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`
  和
  `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`
  恢复到原始时间戳，避免旧证据被误记为本轮产物。

## 剩余风险

- 本轮只做 PC mock/DOM 验证，没有真实调用上位机 map start/save。
- 该改动只让失败状态可见，不修复真实上位机地图 lifecycle、SLAM 或保存命令问题。
