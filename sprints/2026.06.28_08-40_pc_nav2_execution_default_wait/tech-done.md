# Tech Done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通 PC 行程执行默认 `navGoalExecutionTimeoutS` 从 8 秒改为 20 秒。
  - 执行请求仍只在用户点击并勾选安全确认后发送，仍使用当前图上路线目标和 ROS base command mode。
- `pc-tools/workstation/test/App.test.ts`
  - 更新行程执行 fixture/断言里的 `result_timeout_s` 默认值为 20 秒。
- `docs/product/pc_free_roam_mapping_design.md`
  - 补充 2026-06-28 08:40 的 Nav2 执行默认等待窗口规则。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "Nav2|nav2|plain trip|行程|execute|执行|timeout" --maxWorkers=1 --no-fileParallelism`
  - 结果：2 个 test files，59 passed，268 skipped。
- 已通过：`cd pc-tools/workstation && npm test -- --maxWorkers=1 --no-fileParallelism`
  - 结果：2 个 test files，327 passed。
- 已通过：`cd pc-tools/workstation && npm run lint`
- 已通过：`cd pc-tools/workstation && npm run build`
  - 备注：Vite 输出既有 `Some chunks are larger than 500 kB` 警告；构建命令退出码为 0。
- 已通过：`git diff --check`

## 剩余风险

- 本轮只增加 PC 等待 Nav2 执行结果的默认时间，没有真实跑路线。
- 若 Nav2 planner/controller、定位或底盘 bridge 仍异常，20s 只会更完整地返回失败，不等于执行成功。
- 真实完整路线、wheel raw L/R 非零和送达闭环仍需要现场安全确认后的硬件验证。
