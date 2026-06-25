# 2026.06.26 07:30 PC radar start marker style

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`
  - 为地图雷达 marker 的 `data-state="雷达启动中"` 增加待确认样式，并让雷达 sweep 的 `雷达启动中` 也使用 pending 扫描配色。
  - 为 `data-state="雷达启动失败"` 增加失败样式，避免失败状态落回默认白底 marker。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展雷达启动失败用例，断言 `雷达启动失败` marker 样式选择器存在。
  - 扩展雷达启动 pending 用例，断言 `雷达启动中` marker/sweep 样式选择器存在。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-26 07:30 起雷达启动中/启动失败 marker 独立样式口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "shows plain radar start only when the readback says lidar is stopped|shows a map radar-starting marker while the plain radar start request is in flight"`，2 passed / 190 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 files / 192 passed。
- 通过：`git diff --check`。
- 已确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN || true` 输出 `node ... TCP *:7001 (LISTEN)`。
- 已处理：完整 `npm test` 只改动两个 2026-06-11 旧 DOM smoke artifact 的 `checked_at`，已恢复到原始基线时间戳，未纳入提交。

## 剩余风险

- 本轮只验证 PC 端 CSS/DOM 口径，不触发真实 `/api/radar/start` 或真实雷达 HIL。
- 样式只表达雷达 lifecycle 请求状态，不证明真实 scan 已运行；最终仍以后端 radar proof refresh 为准。
- 本轮没有改 Clash、系统代理或上车端端口配置。
