# Tech Done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `canRunPlainTripExecution` 不再因为小车 map pose marker 未显示而禁用执行按钮。
  - 当前地图路线已显示且安全确认已勾选时，按钮可执行当前图上路线；位置未显示只作为普通首屏警告。
  - 行程状态、当前事实、最小预检、进度卡点文案统一改成“建议重新定位或刷新地图，但不是发车前硬挡”。
- `pc-tools/workstation/test/App.test.ts`
  - 更新“路线已显示但小车位置未显示”用例：按钮应启用，点击后应发送 `/api/robot-control/nav2/goal/execute`。
  - 断言执行 body 使用地图上可见路线终点 `goal_x=0.8, goal_y=0`，不发送 manual。
- `docs/product/pc_free_roam_mapping_design.md`
  - 补充 2026-06-28 08:25 的“位置 marker 缺失只警告、不硬挡当前图上路线执行”规则。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "Nav2|nav2|plain trip|行程|route|路线|定位|图上路线" --maxWorkers=1 --no-fileParallelism`
  - 结果：2 个 test files，72 passed，255 skipped。
- 已通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - 结果：2 个 test files，327 passed。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - 备注：Vite 输出既有 `Some chunks are larger than 500 kB` 警告；构建命令退出码为 0。
- 已通过：`git diff --check`

## 剩余风险

- 本轮只修 PC 前端行程按钮门禁和文案，没有在真实小车上执行 Nav2 路线。
- 真实完整路线仍依赖 Nav2 planner/controller、定位、底盘反馈和现场安全确认；后端 gate 若拒绝执行，PC 会按失败结果展示。
- 小车位置 marker 不显示时，页面会提示建议先重新定位或刷新地图；operator 仍需确认图上路线安全。
