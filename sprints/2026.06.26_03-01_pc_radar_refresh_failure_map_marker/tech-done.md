# 2026.06.26 03:01 PC 雷达刷新失败地图 Marker WYSIWYG

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `radarRefreshFailed()` 与 `radarRefreshFailureLabel()`，复用 radar refresh proxy 的失败状态判断。
  - 普通首屏地图雷达 marker 在 `刷新雷达` 失败后显示 `雷达刷新失败：<failure_reason>`，`data-state=雷达刷新失败`。
  - 雷达 freshness 在刷新失败时显示 `雷达点口径：雷达刷新失败，未显示新点位。`，并隐藏扫描范围占位。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `shows plain radar refresh failure reason on the map`，覆盖 `fetch_timeout` 刷新失败时地图 marker、ARIA、freshness 和无运动调用约束。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏 radar refresh 失败贴回地图 marker 的产品口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "shows plain radar refresh failure reason on the map"`
  - 结果：通过，`1 passed | 183 skipped (184)`。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过，`eslint .` 无报错。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `cd pc-tools/workstation && npm test`
  - 结果：通过，`2 passed (2)`，`184 passed (184)`。
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

- 本轮只做 PC mock/DOM 验证，没有真实调用上位机 radar proof refresh。
- 该改动只让刷新失败在地图上可见，不修复真实 LiDAR lifecycle、scan proof 或网络超时问题。
