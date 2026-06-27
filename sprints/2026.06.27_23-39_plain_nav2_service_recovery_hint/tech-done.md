# Plain Nav2 Service Recovery Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏自动驾驶诊断现在同时消费 `planner_server_inactive` 和 `controller_server_inactive`。
  - 当旧 Nav2 action 已发底盘命令但 wheel raw L/R 未闭环，且 planner/controller 当前 inactive 时，文案显示 `Nav2 planner 和 Nav2 controller 未 active，重跑前先恢复`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 ROS/T=13 和 PWM/IMU 两个旧行程成功但轮速未闭环场景，覆盖 planner/controller 双服务恢复提示。
- `docs/product/pc_tools_workstation.md`
  - 记录普通首屏自动驾驶诊断与 summary blocker 对齐。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录该提示只影响 PC 文案，不改变发车安全确认或 Nav2 服务状态。

## 验证结果

- `npm test -- test/App.test.ts -t "ROS T13 command evidence" --maxWorkers=1 --no-fileParallelism`
  - 通过：1 个相关用例通过。
- `npm test -- test/App.test.ts -t "IMU-only route arrival|ROS T13 command evidence" --maxWorkers=1 --no-fileParallelism`
  - 通过：2 个相关用例通过。
- `npm test -- --maxWorkers=1 --no-fileParallelism`
  - 通过：2 个测试文件，318 个用例通过。
- `npm run lint`
  - 通过。
- `npm run build`
  - 通过；Vite 仍提示 bundle 超过 500 kB，这是既有体积 warning。
- `git diff --check`
  - 通过。

## 剩余风险

- 本轮只修正普通首屏文案，不恢复 Nav2 planner/controller，不执行路线。
- live 当前仍需恢复 Nav2 服务、生成路线、读到 robot map pose，并在现场安全确认后重跑完整路线复验 wheel raw L/R。
