# 2026-06-23 17:00 Micro Sprint: 行程进度卡点直指雷达

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `本轮进度` 的行程项在雷达未运行时显示 `去雷达`，总按钮显示 `去启动雷达`。
  - 行程项 hint、总下一步和验收卡点统一提示先启动雷达，再检查或执行完整行程。
  - 行为仍只做本页 scroll/focus；不会自动启动雷达、刷新雷达、执行 Nav2、提交送达或发送底盘手控。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展雷达未运行时的普通首屏回归测试，覆盖总按钮、行程行按钮、总下一步、验收卡点和零控制 API 调用。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏 `本轮进度` 在行程雷达卡点下的用户引导和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "blocks plain trip actions on the first screen until radar is running"`：通过，1 个测试文件通过，1 个相关用例通过。
- `cd pc-tools/workstation && npm test`：通过，2 个测试文件通过，142 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite build 完成，server/app TypeScript 均通过。
- `git diff --check`：通过。

## 剩余风险

- 当前仍是 PC 前端引导和 mock 回归验证，不等于真实雷达已启动、Nav2 路线已执行或 delivery success 已完成。
- 真实上位机只读状态仍显示雷达 lifecycle 未运行、wheel raw L/R 非零未证明、Nav2 latest 未证明、delivery 未成功；继续执行真实动作前需要现场 operator 明确确认。
