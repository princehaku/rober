# Plain Keyboard Missing Hint

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- 普通首屏键盘手控禁用时新增缺项提示，显示还差：小车连接、移动前检查、现场画面、轮速记录、雷达移动记录等普通步骤。
- 缺项提示只由现有 `canSendManualMotion` gate、移动前 checklist 和 operator material summary 只读计算。
- 条件满足后缺项提示消失；仍需点击 `启用键盘` 并聚焦键盘面板才会响应按键。
- 更新 Vue/Vitest 回归，覆盖默认缺项提示和满足条件后不显示 `还差`。
- 更新 `docs/product/pc_tools_workstation.md`，记录该提示不展示 HIL/operator report 字段名、不放开 manual。

## 验证结果

- `npm test`：通过，2 个测试文件、117 个用例。
- `npm run lint`：通过。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过。

## 剩余风险

- 本轮只提升键盘手控 gate 的普通可读性，不触发真实键盘手控。
- 真实 PC 键盘连续手控仍需要现场安全确认、完整材料和人工聚焦面板后验证。
