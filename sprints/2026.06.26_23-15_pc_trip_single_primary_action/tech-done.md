# PC Trip Single Primary Action

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `行程操作` 文案收敛为“主按钮准备或执行图上路线”，避免把 no-motion planner refresh 误呈现成额外发车前预检。
- 将单独的 `准备行程（不发车）` 按钮改为 `可选刷新路线`；pending 文案改为 `刷新路线中（不发车）`，强调它只是只读刷新兜底。
- 同步 `plain-goal-progress`、路线 WYSIWYG、最小预检提示：未确认时统一提示勾选现场安全确认；确认后提示点主按钮准备/执行。
- 更新 `pc-tools/workstation/test/App.test.ts` 覆盖新文案，继续验证主按钮准备路线不会调用 Nav2 execute、base manual 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md` 记录 2026-06-26 23:15 起普通首屏行程主路径。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts`：通过，`141 passed`。
- `cd pc-tools/workstation && npm run build`：通过，仅保留既有 Vite chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮只改善 PC 首屏普通用户主路径和测试证据，没有执行真实 Nav2 HIL 发车。
- 完整路线再次真实执行仍依赖现场安全确认、当前路线在地图上可见、小车位置可见，以及上车端 `/api/nav2/goal/execute` 的后端复查通过。
