# Nav2 下一步文案 controller 事实修正

## Sprint 类型

sprint_type: micro

## 实际改动

- 修改 `pc-tools/workstation/src/server/robotControlSummary.ts`：
  - 修正 `safe_command_boundary.nav2_goal_next_action` 的旧执行运动材料文案。
  - 当当前 `controller_server_active=false` 时，不再写“主因不是 controller”。
  - 将“旧执行主因不是雷达或相机”和“当前 controller 未 active，重跑前需恢复 controller”拆开展示。
- 修改 `pc-tools/workstation/test/catalog.test.ts`：
  - 更新 wheel L/R 为 0 且 controller inactive 的 summary 断言。
  - 增加 IMU 姿态变化 + controller inactive 的 live-like 回归断言，防止再次输出“不是 controller”。
- 更新 `docs/product/pc_tools_workstation.md` 与 `docs/product/pc_free_roam_mapping_design.md`：
  - 同步记录新的 summary 文案边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "Nav2 wheel-zero|IMU motion material|goal_succeeded_but_wheel|ROS T13 Nav2 wheel-zero"`（2 tests）
- 通过：`cd pc-tools/workstation && npm test`（313 tests）
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - 保留既有 Vite chunk size warning：`Some chunks are larger than 500 kB after minification`。
- 通过：`git diff --check`

## 剩余风险

- 本轮只修只读 summary 与 PC 文案合同，没有发送真实 Nav2 execute、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- live 当前仍需要现场安全确认后恢复/重跑图上路线，并在同窗口证明 wheel raw L/R 非零。
