# 2026-06-22 18:03 Delivery Gap Check No Confirm Label

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `复查送达条件` 根据 delivery gate 缺口显示 `还差 N 项，不确认`；无缺口读回时显示 `不确认`。
- `pc-tools/workstation/test/App.test.ts`：覆盖默认无缺口读回、缺 2 项、缺 5 项三种文案，并改用 `plain-delivery-gap-check` 稳定定位按钮。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮只走固定 delivery check，后端 `confirm_delivery_completion=false`，不提交 operator report 或 delivery complete。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只降低复查送达条件被误解成确认送达的风险；真实 delivery success 仍需要现场最终确认并显式点击 `确认送达（不发车）` 后通过上位机 gate。
- 当前真实只读状态显示 Nav2 latest 已 `goal_succeeded`，delivery 仍为 false，operator report 仍是送达草稿。
- 当前真实 `/api/base/status` 仍只读到 T1001 在线、电压约 12.44V，但 wheel raw L/R 为 0/0；PC 键盘连续手控仍缺 wheel/LiDAR/现场材料 HIL 证明。
