# Plain Goal Progress Shortcuts

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- date: 2026-06-22

## 实际改动

- 普通首屏“本轮进度”四项新增 `去处理` 按钮，分别定位到轮速记录、行程操作、任务收口和键盘手控面板。
- 定位动作只做本页 `scrollIntoView` 与 `focus`，不调用行程执行、送达确认、材料保存、底盘手控或 `/cmd_vel`。
- 给行程、轮速、送达面板补 `tabindex="-1"`，确保快捷定位可聚焦；键盘手控继续复用原有可聚焦面板。
- 更新 Vue/Vitest 回归，覆盖 4 个快捷按钮存在、目标面板可聚焦、点击后 fetch 调用数不变。
- 更新 `docs/product/pc_tools_workstation.md`，记录普通首屏快捷定位的行为边界。

## 验证结果

- `npm test`：通过，2 个测试文件、116 个用例。
- `npm run lint`：通过。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过。

## 剩余风险

- 本轮只降低普通用户从状态跳转到操作区的成本，不新增真实运动或送达确认能力。
- wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 和真实键盘连续手控仍需要现场安全确认后继续产生 HIL 证据。
