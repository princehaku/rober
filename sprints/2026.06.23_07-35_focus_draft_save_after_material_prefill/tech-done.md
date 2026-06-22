# 2026.06.23 07:35 Focus Draft Save After Material Prefill

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `准备送达材料` 成功拿到视频和行程材料后，自动聚焦 `保存送达草稿（不确认）`。
  - 聚焦只改变页面焦点和滚动位置，不自动保存草稿、不提交 delivery complete、不执行 Nav2、manual、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展送达材料流程回归：预填成功后焦点落到草稿保存按钮；草稿保存成功后焦点继续落到最终确认区。
  - 继续断言预填阶段不触发 operator report、delivery complete、Nav2 execute、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏送达材料预填后的焦点引导和安全边界。

## 只读现场状态

- `GET http://192.168.1.11:8787/api/base/status` 可读，`T=1001` 在线，但当前静态读回 `L/R=0/0`。
- `GET http://192.168.1.11:8787/api/nav2/goal/execution/latest` 可读，latest artifact 为旧 `goal_succeeded`，`delivery_success=false`。
- `GET http://192.168.1.11:8787/api/delivery/latest` 可读，当前 `delivery_success=false`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 135 passed (135)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - `dist/assets/index-DYSVn13Y.js 402.95 kB`
- 通过：`git diff --check`
- 已恢复历史 smoke artifact 的 `checked_at` 测试副作用，未纳入本轮提交。

## 剩余风险

- 当前变更只推进 PC 普通首屏的 delivery success 操作衔接；真实 wheel raw L/R 非零、完整 Nav2 本轮复验、delivery success 和 PC 键盘连续手控仍未由本轮证明。
