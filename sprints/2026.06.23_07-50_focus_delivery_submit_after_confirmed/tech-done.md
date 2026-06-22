# 2026.06.23 07:50 Focus Delivery Submit After Confirmed

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏最终确认区在 `全部已确认` 或最后一步 `确认投放/送达` 后，如果送达提交 gate 已满足，会自动聚焦红色 `确认送达（不发车）` 按钮。
  - 聚焦只改变页面焦点和滚动位置，不自动提交 operator report、不调用 delivery complete、不执行 Nav2、manual、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展送达收口回归：一键全部确认和逐步确认到最后一项后，焦点都会落到 `plain-delivery-confirm-submit`。
  - 继续断言本地确认快捷按钮不触发任何 Robot API 请求。
- `docs/product/pc_tools_workstation.md`
  - 同步记录最终确认满足后的红色提交按钮聚焦行为和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 135 passed (135)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - `dist/assets/index-DMzVZR9K.js 403.22 kB`
- 通过：`git diff --check`
- 已恢复历史 smoke artifact 的 `checked_at` 测试副作用，未纳入本轮提交。

## 剩余风险

- 当前变更只推进 PC 普通首屏 delivery success 的最后一步操作衔接；真实 delivery success 仍必须由现场人员显式点击红色按钮并通过上位机 gate。
- 真实 wheel raw L/R 非零、完整 Nav2 本轮复验和 PC 键盘连续手控仍未由本轮证明。
