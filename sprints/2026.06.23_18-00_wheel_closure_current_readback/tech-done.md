# 2026-06-23 18:00 Micro Sprint: wheel 收口显示当前只读 L/R

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `目标收口进度` 的 `wheel raw L/R 非零` 未完成项在已有只读 T1001 当前读回时，显示当前 `L/R` 和帧数。
  - 该提示仍保持 `ready=false`；只读 T1001、停车 `0/0` 或帧数不会被外推为 wheel raw L/R 非零证明。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展普通首屏轮速测试，确认高级目标收口 checklist 显示当前只读 `L/R=0/0` 和 12 帧，同时 `data-ready=false`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 `目标收口进度` 的 wheel readback 展示口径和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "shows current wheel L/R and frame count in plain goal progress from summary"`：通过，1 个测试文件通过，1 个相关用例通过。
- `cd pc-tools/workstation && npm test`：通过，2 个测试文件通过，142 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite build 完成，server/app TypeScript 均通过。
- `git diff --check`：通过。

## 剩余风险

- 当前改动只修正 PC 目标收口展示，不证明 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或 PC 键盘连续手控。
- 真实上位机仍显示雷达 lifecycle 未运行、当前 wheel L/R 为 `0/0`、Nav2 latest 未证明、delivery 未成功；真实动作仍需现场 operator 明确确认。
