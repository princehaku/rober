# 2026.06.29 16:50 PC Nav2 托管 runtime 行程状态提示

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当图上路线已可执行、`nav2_goal_ready=true`，但 Nav2 runtime 当前未运行时，普通首屏行程卡摘要和 `行程状态` 直接显示“执行会自动启动自动驾驶 runtime”。
  - 保持原有门禁不变：仍需勾选现场安全确认并显式点击执行按钮；不会因为页面刷新、状态显示或路线可见就自动执行 Nav2。
- `pc-tools/workstation/test/App.test.ts`
  - 加强 managed Nav2 runtime 用例，精确锁定行程卡摘要和行程状态都说明 execute 会托管启动 runtime。
  - 继续断言首屏展示阶段不会调用 `/api/robot-control/nav2/start`、`/api/robot-control/nav2/goal/execute`、manual 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录该 PC 普通首屏行为：这是既有 managed execute 合同的可见化，不是新增预检或自动发车。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- -t "managed Nav2 runtime|ready route execute|current route from map preview|visible route endpoint"`
  - 结果：1 个测试文件通过，4 个相关用例通过。
- 已通过：`npm --prefix pc-tools/workstation test`
  - 结果：2 个测试文件通过，368 个用例通过。
- 已通过：`npm --prefix pc-tools/workstation run build`
  - 结果：TypeScript 与 Vite build 通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积提示。

## 剩余风险

- 本轮只改 PC 前端可见状态和文档；未获得本轮现场安全确认，因此没有对真实小车执行 Nav2 goal、manual、keyboard、free-roam、stop 或 `/cmd_vel`。
- 现场完整 Nav2 路线验收仍需要 operator 勾安全确认后执行图上路线，并在同一执行窗口读到 wheel raw L/R 非零。
