# 2026-06-28 02:36 PC Nav2 恢复按钮焦点目标

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 给普通行程区的“恢复自动驾驶服务（不发车）”按钮增加 `ref`。
  - 当 Nav2 planner/controller inactive 且安全确认已勾选时，目标进度“去行程”直接聚焦恢复按钮，而不是落到禁用的执行/准备按钮或行程面板。
  - 该改动只移动页面焦点，不调用 Nav2 start、proof refresh、goal execute、manual、free-roam、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 Nav2 服务未 active 的普通首屏测试，断言“去行程”聚焦恢复按钮且不产生任何 robot API 调用。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 Nav2 恢复焦点目标的普通用户引导口径。

## 验证结果

- `npm test -- -t "shows a no-motion Nav2 restore action when planner or controller is inactive"`：通过，1 passed / 331 skipped。
- `npm test -- --maxWorkers=1 --no-fileParallelism`：通过，2 files passed / 332 tests passed。
- `npm run lint`：通过。首次运行发现 Vue 属性顺序 warning，已修复后重跑通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001`：通过，`node` 监听 `*:7001`。
- 只读检查 `/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，live summary 为 `nav2_goal_ready=false`，blockers 包含 `path_generation_not_observed`、`path_point_count_not_positive`、`robot_map_pose_not_observed`、`planner_server_inactive`、`controller_server_inactive`，`planner_server_active=false`、`controller_server_active=false`、`path_generated=false`。这正是本轮“已勾安全确认后去行程应聚焦恢复按钮”的覆盖形态。

## 剩余风险

- 本轮只修复 PC 焦点引导，不实际恢复 live Nav2 planner/controller；真实自动驾驶仍需要现场 operator 明确点击恢复服务和后续安全确认执行。
- live Nav2 仍需 planner/controller active、图上路线和小车 map 坐标 ready，并复验同窗口 wheel raw L/R 非零。
