# 2026.06.26 04:12 PC 行程 latest 读取中地图 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `navGoalExecutionLatestPending` 期间，地图行程终点 marker 改为 `读取中`，不再继续显示旧的 `已到达/已送达/行程未通过` 作为当前结论。
  - 地图 caption 在 latest 请求未返回前显示 `行程执行：正在读取最近行程结果`。
  - 行程进度在 latest 请求未返回前提示旧结果暂不作为当前结论。
- `pc-tools/workstation/src/styles.css`
  - 补 `plain-map-route-goal-marker[data-state="读取中"]` 样式，复用警示色表达只读刷新中。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `shows a map-level pending state while rereading the latest Nav2 goal result`，模拟 initial latest 已到达后再次点击只读刷新，验证 pending 期间地图 marker/caption/progress 全部变为读取中，并断言不会调用 Nav2 execute、delivery complete、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 记录 latest 只读刷新 pending 的普通首屏 WYSIWYG 口径和控制边界。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- -t "map-level pending state"`
  - 结果：1 passed，190 skipped。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
- 已通过：`cd pc-tools/workstation && npm test`
  - 结果：2 files passed，191 tests passed。
- 已通过：`git diff --check`
- 已确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node` 正在监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮是 PC 前端 mock 验证，没有触发真实上位机 Nav2、manual、delivery 或 `/cmd_vel`。
- 没有做真实小车 HIL；真实上车最新行程读取延迟、网络失败和返回坏数据仍依赖现场 smoke 复核。
