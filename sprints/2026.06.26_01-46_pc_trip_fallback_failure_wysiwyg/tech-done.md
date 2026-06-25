# 2026.06.26 01:46 PC 行程 Fallback 失败地图 WYSIWYG

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增直接 Nav2 执行失败的 UI fallback 读数：当 `执行图上路线` 返回 `execution_failed` / `execution_rejected` 且 `goal_execution_key_values` 为空时，使用本次点击的图上终点和 `failure_reason` 生成仅供首屏展示的 `goal_failed`。
  - `directNav2ExecutionValues()`、行程未通过判断和行程证据列表都消费该 fallback，避免失败后地图 caption、行程进度或本轮进度退回空白/旧记录。
  - fallback 不包含 `evidence_ref`，也不把任何字段标记为到达或 delivery success。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `keeps failed plain trip visible when execution fallback has no key values`，覆盖空 key-values 失败响应仍显示地图终点、失败原因、caption 和行程进度。
- `docs/product/pc_tools_workstation.md`
  - 同步记录该 UI fallback 的边界：只做所见即所得展示，不重试 Nav2、不提交送达、不发送 manual/keyboard/stop 或 `/cmd_vel`。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "keeps failed plain trip visible|keeps the attempted visible route goal"`
  - 结果：通过，`2 passed | 178 skipped (180)`。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过，`eslint .` 无报错。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `cd pc-tools/workstation && npm test`
  - 结果：通过，`2 passed (2)`，`180 passed (180)`。
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

- 本轮只做 PC mock/DOM 验证，没有触发真实 Nav2 execute，也不构成真实完整路线 HIL 通过。
- 该 fallback 只保证失败状态在 PC 地图上持续可见；真实失败根因仍需上位机 Nav2 日志和现场状态定位。
