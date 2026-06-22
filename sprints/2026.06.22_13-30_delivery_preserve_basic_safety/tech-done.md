# Delivery Preserve Basic Safety

sprint_type: micro

## 实际改动

- PC 送达草稿会保留已有 basic safety 三项：`operator_present`、`physical_clearance_confirmed`、`emergency_stop_ready`。
- 只有 Robot Control summary 已经读到对应字段为 true 时才继承；否则仍写 false，不伪造现场人在场、安全清场或急停就绪。
- 草稿仍不会写 `observed_motion=true`、`observed_stop=true` 或 `delivery_success=true`。
- 补充 Vue 测试，覆盖送达草稿保留已有 basic safety，同时不提交 delivery complete。
- 更新 `docs/product/pc_tools_workstation.md` 记录继承边界。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`112 passed (112)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修复 PC 草稿继承逻辑；当前真实上位机 latest operator report 已经是 `operator_present=false` 的 delivery draft，需要现场重新确认或使用恢复入口才能恢复 first-jog 前置材料。
- 真实 wheel raw L/R 非零和 delivery success 仍未完成。
