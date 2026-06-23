# 2026-06-23 16:40 Micro Sprint: 行程执行先卡雷达运行

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏新增行程雷达前置 gate：雷达未运行且本轮行程未完成时，行程状态显示 `待雷达`，`检查行程` / `执行行程` 禁用并显示 `先启动雷达`。
  - `本轮进度 -> 去行程` 在雷达未运行时只聚焦 `启动雷达` / `刷新雷达`，不自动启动雷达，也不执行 Nav2。
- `pc-tools/workstation/test/App.test.ts`
  - 新增普通首屏回归测试：模拟 LiDAR lifecycle stopped，确认行程按钮被禁用、进度跳转到雷达按钮，并且不会调用 radar start、Nav2 preflight/execute、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏行程操作的雷达前置行为和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "blocks plain trip actions on the first screen until radar is running|runs plain trip preflight"`：通过，1 个测试文件通过，2 个相关用例通过。
- `cd pc-tools/workstation && npm test`：通过，2 个测试文件通过，142 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite build 完成，server/app TypeScript 均通过。
- `git diff --check`：通过。
- `cd pc-tools/workstation && npm run api`：未启动，代码尝试监听 `0.0.0.0:7071`，但本机端口被 Clash Verge `verge-mihomo` PID 2183 占用，服务按预期输出端口冲突提示后退出。

## 剩余风险

- 当前是 PC 前端引导和 Node/Vue mock 回归验证，不等于真实 Nav2 路线已执行。
- 真实上位机当前雷达 lifecycle 仍显示未运行；需要现场 operator 明确确认后再启动雷达和继续完整路线。
- 若要从局域网访问 PC Node API 的固定 `7071` 端口，需要先释放 Clash Verge 当前占用的 `0.0.0.0:7071`。
