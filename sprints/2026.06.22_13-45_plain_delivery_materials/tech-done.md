# Plain Delivery Materials

sprint_type: micro

## 实际改动

- PC 普通首屏 `任务收口` 区新增 `准备送达材料` 与 `保存送达草稿`。
- `准备送达材料` 复用既有固定代理链路：读取最近 Nav2 execution ref、必要时调用 camera first-frame probe 获取样张 ref，并刷新 delivery latest；不提交任何送达确认。
- `保存送达草稿` 只在视频材料和行程材料已预填后调用固定 `operator/report`，写入 `delivery_material_draft_not_operator_confirmed`、`observed_motion=false`、`observed_stop=false` 和 nested `delivery_success=false`。
- 普通首屏只显示 `可准备 / 已预填 / 已保存` 等短状态，不展示 ref、`delivery_success`、`/api/delivery` 或 blocked field name。
- 补充 Vue 测试，覆盖普通首屏准备材料、保存草稿、未调用 `delivery/complete`、Nav2 goal、manual 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md` 记录普通首屏送达材料草稿边界。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`113 passed (113)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 剩余风险

- 本轮只让普通用户更容易补齐送达草稿材料；仍不确认 delivery success。
- 最终送达仍需要现场逐项 checklist、真实 operator 确认和 delivery gate 通过。
