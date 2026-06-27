# 2026.06.28 11:35 PC Nav2 基础下一步顺序统一

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当 Nav2 planner/controller inactive 且路线读数未 ready，但没有进入旧 action 成功分支时，`nav2_goal_next_action` 也统一改为“先恢复 Nav2 planner/controller，再生成图上路线并读到小车地图位置”。
  - 该改动只修正只读 summary 文案顺序，不自动启动 Nav2、不发送 goal、不发布 `/cmd_vel`、不调用底盘 manual。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新基础 Nav2 readiness 断言，锁定服务恢复优先于路线准备。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录基础分支的同序规则。

## 验证结果

- `npm test -- test/catalog.test.ts --testNamePattern "Nav2 readiness" --maxWorkers=1 --no-fileParallelism`：0 matched，1 file skipped；不作为覆盖证据。
- `npm test -- --maxWorkers=1 --no-fileParallelism`：2 files passed，331 tests passed，覆盖更新后的 catalog 断言。
- `npm run lint`：passed。
- `npm run build`：passed（Vite chunk-size warning 保持既有状态，不影响构建通过）。
- `git diff --check`：passed。
- 7001 已按 `HOST=0.0.0.0 PORT=7001 npm run api:public` 重启，`lsof` 显示 node 监听 `*:7001`。
- live summary `http://127.0.0.1:7001/api/robot-control/summary`：
  - `robot_api_connection.status=readable`。
  - 当前 live 仍走旧 action 成功但 wheel raw L/R 未证明分支，`nav2_goal_next_action` 保持“先恢复 Nav2 planner 和 Nav2 controller，再生成图上路线并读到小车地图位置”。
  - `planner_server_active=false`，`controller_server_active=false`，`path_generated=false`。
  - 相机仍是 `uvc_no_frame_not_exclusive`；自由移动仍是 `free_roam_motion_start_ready=true`。

## 剩余风险

- 本轮不触发真实 `/api/nav2/start`、NavigateToPose 或底盘命令；真实自动驾驶仍需要现场安全确认后恢复服务、生成图上路线并复验 wheel raw L/R 非零。
