# 2026.06.28 11:20 PC Nav2 下一步顺序修正

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当旧 Nav2 action 成功但 wheel raw L/R 未非零，且当前 planner/controller inactive、图上路线也未就绪时，`nav2_goal_next_action` 改为先提示恢复 Nav2 planner/controller，再生成图上路线和读取小车地图位置。
  - 该改动只修正只读 summary 文案顺序，不自动启动 Nav2、不发送 goal、不发布 `/cmd_vel`、不调用底盘 manual。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 planner/controller inactive 与 controller inactive 的 summary 断言，锁定“先恢复服务，再准备路线”的顺序。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 live 根因下的自动驾驶排障顺序。

## 验证结果

- `npm test -- test/catalog.test.ts --testNamePattern "wheel raw|wheel feedback|controller inactive|planner" --maxWorkers=1 --no-fileParallelism`：1 passed，143 skipped。
- `npm test -- --maxWorkers=1 --no-fileParallelism`：2 files passed，331 tests passed。
- `npm run lint`：passed。
- `npm run build`：passed（Vite chunk-size warning 保持既有状态，不影响构建通过）。
- `git diff --check`：passed。
- 7001 已按 `HOST=0.0.0.0 PORT=7001 npm run api:public` 重启，`lsof` 显示 node 监听 `*:7001`。
- live summary `http://127.0.0.1:7001/api/robot-control/summary`：
  - `robot_api_connection.status=readable`。
  - `nav2_goal_ready=false`，`planner_server_active=false`，`controller_server_active=false`，`path_generated=false`。
  - `nav2_goal_next_action` 已变为“当前图上路线未就绪，先恢复 Nav2 planner 和 Nav2 controller，再生成图上路线并读到小车地图位置，再勾选行程前安全确认后用 ROS 重跑并复验 wheel raw L/R”。
  - 相机仍是 `uvc_no_frame_not_exclusive`；自由移动仍是 `free_roam_motion_start_ready=true`。

## 剩余风险

- 本轮不触发真实 `/api/nav2/start`、NavigateToPose 或底盘命令；真实自动驾驶仍需要现场安全确认后恢复服务、生成图上路线并复验 wheel raw L/R 非零。
