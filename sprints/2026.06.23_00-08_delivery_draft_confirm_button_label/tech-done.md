# 2026-06-23 00:08 Delivery Draft Confirm Button Label

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：抽出 `deliveryDraftMaterialPresent()`，统一识别本页刚保存或上位机 latest 读回的送达材料草稿；草稿存在且最终确认未完成时，`确认送达` 按钮显示 `确认送达（先确认 N 项）`。
- `pc-tools/workstation/test/App.test.ts`：覆盖本页保存草稿后还差 1 项、以及页面刷新从 latest 恢复草稿后还差 7 项的按钮文案。
- `docs/product/pc_tools_workstation.md`：同步记录该文案只提示现场最终确认，不触发任何送达确认或运动接口。

## 验证结果

- `npm test`：通过，2 个 test files，124 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 delivery success 收口路径的普通首屏文案；真实 delivery success 仍需要现场最终确认并显式点击 `确认送达（不发车）` 后通过上位机 gate。
- 当前真实只读状态显示 Nav2 latest 已 `goal_succeeded`，delivery latest 仍为 `delivery_success=false`，operator report 仍是送达草稿。
- 当前真实 `/api/base/status` 新鲜读回 T1001 在线但 L/R=0/0；PC 键盘连续手控仍缺 wheel/LiDAR/现场材料 gate。
