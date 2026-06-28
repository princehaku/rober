# 2026.06.28 12:12 PC Nav2 ready after runtime cleanup

sprint_type: micro

## 实际改动

- PC `Robot Control summary` 的 Nav2 gate 不再把 no-motion proof 清理后的 `nav2_stack_running=false` 当作已生成路线的硬 blocker。
- 当 `path_generated=true` 且 path points 为正时，`controller_server_active=false/controller_server_requested=false` 不再阻止普通首屏执行入口；真正 controller 执行栈由 `/api/nav2/goal/execute` 的 bounded runtime 启动。
- 如果路线未生成，仍保持 `nav2_stack_not_running/path_generation_not_observed/path_point_count_not_positive` 等 blocker；如果 controller 明确 `requested=true` 但 inactive，仍保持 `controller_server_inactive` blocker。
- 新增 Vitest 覆盖真实形态：lifecycle stopped、controller 未请求、status/proof latest 有 18 点 no-motion route 时，PC summary 必须显示 `nav2_goal_ready=true`、blockers 为空、下一步为勾安全确认后执行路线并复验 wheel raw L/R。
- 同步更新 PC 和 fixed-route 文档，明确这是 PC gate 修复，不自动发车。

## 验证结果

- `cd pc-tools/workstation && npm run test -- catalog.test.ts` 通过：152 tests。
- `cd pc-tools/workstation && npm run test -- App.test.ts` 通过：210 tests。
- `cd pc-tools/workstation && npm run test` 通过：2 files / 362 tests。
- `cd pc-tools/workstation && npm run build` 通过；Vite 仍提示单 chunk 大于 500 kB，这是既有体积 warning。
- 临时 `127.0.0.1:7011` 当前代码 API 连接真实上位机后，summary 显示 `nav2_stack_running=false`、`controller_server_requested=false`、`path_generated=true`、`path_point_count=18`、`robot_pose` 已读到、`nav2_goal_ready=true`、`nav2_goal_blockers=[]`，下一步为安全确认后用 ROS 重跑并复验 wheel raw L/R。

## 剩余风险

- 本轮没有执行 `/api/nav2/goal/execute`、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；真实完整路线执行和 wheel raw L/R 非零仍待现场安全确认后验证。
- 当前摄像头仍是 `uvc_no_frame_not_exclusive`，雷达 latest 仍不新鲜；它们不再阻止路线执行 gate，但仍影响实时画面和建图验收。
