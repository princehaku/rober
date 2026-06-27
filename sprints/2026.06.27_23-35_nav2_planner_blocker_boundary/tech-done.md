# Nav2 Planner Blocker Boundary

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `planner_server_active=false` 现在进入 `safe_command_boundary.nav2_goal_blockers=planner_server_inactive`。
  - 当路线还未 ready 时，`nav2_goal_next_action` 会保留“先生成图上路线并读到小车地图位置”，同时追加恢复 Nav2 planner/controller。
  - 当路线已 ready 但 planner/controller 未 active 时，label 可显示 `Nav2 planner 未就绪` 或 `Nav2 planner/controller 未就绪`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `nav2_goal_label` 类型，覆盖 planner 和 planner/controller 未就绪。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 Robot Control summary 断言，覆盖 `planner_server_inactive` 和恢复 planner 的 next action。
- `docs/product/pc_tools_workstation.md`
  - 记录 planner inactive blocker 的 PC/API 口径。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录该变更只影响只读 readiness，不触发 Nav2 或底盘命令。

## 验证结果

- `npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback|PWM Nav2|IMU|controller 未就绪|controller inactive" --maxWorkers=1 --no-fileParallelism`
  - 通过：1 个测试文件，2 个相关用例通过。
- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：2 个测试文件，318 个用例通过。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示 bundle 超过 500 kB，这是既有体积 warning。

## 剩余风险

- 本轮只增加只读 readiness 证据，不恢复真实 Nav2 planner/controller，不生成路线，也不执行 Nav2。
- live 当前仍需要恢复 planner/controller、生成图上路线、读到 robot map pose，并在现场安全确认后重跑完整路线复验 wheel raw L/R。
