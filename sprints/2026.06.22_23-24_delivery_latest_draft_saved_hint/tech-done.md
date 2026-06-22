# 2026-06-22 23:24 Delivery Latest Draft Saved Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏从 delivery latest 读到 `delivery_material_draft_not_operator_confirmed` 时，把送达材料和最终确认状态统一显示为“已保存/待确认”，不再只显示“已预填”。
- `pc-tools/workstation/test/App.test.ts`：更新 latest 草稿恢复用例，锁定“送达材料草稿已保存；请完成下方最终确认”和“现场逐项确认后再提交”的普通首屏提示。
- `docs/product/pc_tools_workstation.md`：同步记录该提示只消费 latest readback，不触发任何送达确认或运动接口。

## 验证结果

- 第一轮 `npm test`：失败，定位为旧 fixture 缺 `delivery_material_refs` 时 `deliveryLatestDraftMaterialPresent` 访问 `.site_state` 过硬。
- 修复后 `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 普通首屏对上位机已有送达草稿的解释；真实 delivery success 仍需要现场最终确认并显式点击 `确认送达（不发车）` 后通过上位机 gate。
- 当前真实只读状态显示 `/api/nav2/goal/execution/latest` 已 `goal_succeeded`，但 `/api/delivery/latest` 仍为 `delivery_success=false`，缺最终 operator report ready、到达/停止观察和投放/送达确认。
- 当前真实 `/api/base/status` 新鲜读回仍为 L/R=0/0，PC 键盘连续手控仍缺 wheel/LiDAR/现场材料 gate。
