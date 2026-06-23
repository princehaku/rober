# 2026-06-23 18:20 Micro Sprint: Nav2 收口显示雷达前置

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 高级 `目标收口进度` 的 `完整 Nav2 路线执行` 未完成项在雷达未运行时，显示 `雷达未运行，先启动雷达，再检查或执行完整行程`。
  - 只调整只读验收提示，不自动启动雷达、不执行 Nav2、不提交送达、不发送 manual 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展雷达未运行时的普通首屏回归测试，确认高级 Nav2 收口项保持 `data-ready=false` 并显示雷达前置提示。
- `docs/product/pc_tools_workstation.md`
  - 同步记录高级 `目标收口进度` 的 Nav2 雷达前置提示。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "blocks plain trip actions on the first screen until radar is running"`：通过，1 个测试文件通过，1 个相关用例通过。
- `cd pc-tools/workstation && npm test`：通过，2 个测试文件通过，142 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite build 完成，server/app TypeScript 均通过。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只修正 PC 只读收口提示，不证明完整 Nav2 路线执行、wheel raw L/R 非零、delivery success 或 PC 键盘连续手控。
- 真实上位机仍显示雷达 lifecycle 未运行、当前 wheel L/R 为 `0/0`、Nav2 latest 未证明、delivery 未成功；真实动作仍需现场 operator 明确确认。
