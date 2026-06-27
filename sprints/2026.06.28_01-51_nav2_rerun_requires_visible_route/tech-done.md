# Nav2 重跑前必须先有图上路线

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当旧 Nav2 action succeeded 但 wheel raw L/R 仍为 `0/0` 时，`nav2_goal_next_action` 会先检查当前 `nav2_goal_ready`。
  - 如果当前图上路线未就绪，下一步改为先生成图上路线、读到小车 map 坐标，并恢复 inactive 的 planner/controller，再安全确认后重跑。
  - 如果图上路线已就绪但 Nav2 服务未 active，下一步只提示先恢复服务，再重跑复验 wheel。
- `pc-tools/workstation/test/catalog.test.ts`
  - 将旧 PWM succeeded / wheel zero 测试改成 live 形态：planner/controller inactive、无图上路线、无 map pose。
  - 更新 IMU-only wheel-zero 测试，要求当前路线未就绪时不再直接提示发车。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 Nav2 重跑提示的 WYSIWYG 口径：图上路线和服务 ready 前不提示直接重跑。

## 验证结果

- `npm test -- --testNamePattern "Nav2|nav2|wheel raw|visible route|route execution" --maxWorkers=1 --no-fileParallelism`
  - 通过：52 passed, 278 skipped。
- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：330 passed。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；仍有既有 Vite chunk size warning。
- `git diff --check`
  - 通过。
- `HOST=0.0.0.0 PORT=7001 npm run api:public`
  - 已重新启动，`node` 监听 `*:7001`。
- `curl -sS --max-time 5 http://127.0.0.1:7001/api/robot-control/summary`
  - 只读复验通过：`nav2_goal_ready=false`、`nav2_goal_label=图上路线未就绪`。
  - 只读复验通过：blockers 为 `path_generation_not_observed,path_point_count_not_positive,robot_map_pose_not_observed,planner_server_inactive,controller_server_inactive`。
  - 只读复验通过：`nav2_goal_next_action` 先提示生成图上路线、读到小车 map 坐标并恢复 Nav2 planner/controller，再安全确认后用 ROS 重跑并复验 wheel raw L/R。
  - 只读复验通过：旧执行仍是 `goal_execution_status=goal_succeeded`，但 `goal_execution_base_feedback_lr_nonzero_proven=false` 且 wheel raw L/R 为 `0/0`。

## 剩余风险

- 本轮不发送真实 Nav2 goal、manual/free-roam、stop 或 `/cmd_vel`。
- 当前 live 仍显示 path/pose 缺失、planner/controller inactive、wheel raw L/R 为 `0/0`；本轮修正的是普通首屏下一步不会误导 operator 直接发车。
- 真正完成 Nav2 路线执行仍需要现场安全确认后恢复 Nav2 stack、生成图上路线并执行复验。
