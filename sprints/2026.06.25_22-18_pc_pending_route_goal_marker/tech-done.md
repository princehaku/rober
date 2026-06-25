# PC 行程执行中目标标记

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `navGoalExecutionPendingGoal`，普通或高级 Nav2 执行请求 pending 时记录当前 map-frame 目标。
  - 地图 overlay 在 pending 期间优先显示 `行程中` 目标标记，后端返回后再回到真实执行结果/latest 标记。
  - pending 标记只做 WYSIWYG 读图提示，不证明到达，不提交送达，不新增控制 endpoint。
- `pc-tools/workstation/src/styles.css`
  - 为地图目标标记的 `执行中` 状态补充绿色活动态样式。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 deferred execute 测试，验证点击 `执行图上路线` 后地图立即标出 `行程中`，请求体仍绑定图上路线终点，且不调用 manual/delivery/cmd_vel。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 pending route goal marker 的用户口径和安全边界。

## 验证结果

- 通过：`npm test -- --testNamePattern "marks the visible route goal as executing while the plain trip request is pending"`
  - 结果：`Test Files 1 passed | 1 skipped (2)`，`Tests 1 passed | 169 skipped (170)`。
- 通过：`npm run lint`
  - 结果：`eslint .` 无报错。
- 通过：`npm test`
  - 结果：`Test Files 2 passed (2)`，`Tests 170 passed (170)`。
- 通过：`npm run build`
  - 结果：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过，Vite 输出 `✓ built`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮只增强 PC 地图上的 Nav2 执行中视觉反馈；真实完整 Nav2 路线、delivery success 和真车自动扫图仍需继续用上车端/HIL 证据闭环。
- pending 标记只说明“请求已发出且目标是这个图上终点”，不代表机器人已移动、已到达或已送达。
