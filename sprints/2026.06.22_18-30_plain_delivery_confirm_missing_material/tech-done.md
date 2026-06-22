# 2026-06-22 18:30 Plain Delivery Confirm Missing Material

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“最终确认”在送达材料未准备时也显示缺口清单，先提示“送达材料”，再提示 7 个现场确认项；材料准备后自动收敛为 7 个现场勾选项。
- `pc-tools/workstation/test/App.test.ts`：补默认首屏和送达收口流程断言，确认未准备材料时展示“还差 8 项”，准备材料后仍是“还差 7 项”。
- `docs/product/pc_tools_workstation.md`：同步记录该普通缺口提示不自动勾选、不提交 operator report、不调用 delivery complete。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 delivery success 的普通首屏引导；真实 delivery success 仍需要现场人员确认到达/停止/投放后显式提交。
- 本轮没有触发真实 delivery complete，也没有执行底盘运动。
