# 2026-06-22 17:14 Delivery Next Action Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `任务收口` 增加 `下一步` 提示，并把同一句追加到 `本轮进度 / 送达确认`，让现场在 delivery gate 缺项很多时先做一个明确动作。
- `pc-tools/workstation/test/App.test.ts`：补充缺送达材料、材料已预填两种状态下的下一步提示断言，确认该提示不会触发 operator report、delivery complete、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录该提示只基于已读材料和本地勾选，不自动勾选或提交送达。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 delivery success 卡点的普通首屏引导；真实 delivery success 仍需要现场完成最终确认并通过上位机 gate。
- 真实上位机当前只读证据显示 Nav2 latest 已 `goal_succeeded`，但 delivery latest 仍缺人工确认、报告 ready、observed motion/stop 和 delivery_success claim。
