# PC Nav2 执行后 latest/summary 自动刷新

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏执行图上 Nav2 路线后，在 `execute -> map preview -> execution latest` 后追加一次只读 `summary` 刷新，让首页事实条、地图行程 marker 和送达 gate 看到同一轮执行证据。
  - 新增 `preferredNav2ExecutionValues()`：当本次 execute 回包和 latest 的 `evidence_ref` 一致时，优先使用 latest 里更完整的 wheel raw L/R 与反馈样本字段；若 latest 是旧记录，则继续使用本次 execute 回包。
- `pc-tools/workstation/test/App.test.ts`
  - 新增回归用例覆盖普通首屏执行后自动读取 latest、再刷新 summary，并断言请求体仍固定 `base_command_mode=ros`、`confirm_navigation_execution=true`，且不调用 manual 或 `/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 Nav2 执行后的刷新顺序和证据优先级。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "refreshes Robot Control summary after plain Nav2 execution latest is loaded"`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。Vite 仍提示既有单 chunk 大于 500 kB warning，不影响本轮改动。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed / 280 passed`。
- 通过：`git diff --check`。
- 通过：PC Node 继续监听 `0.0.0.0:7001`，`lsof` 显示 PID `69539` 监听 `TCP *:7001`。
- live 只读确认：当前 Nav2 仍是旧 `goal_execution_base_command_mode=pwm`，`next_execution_base_command_mode=ros`，
  同窗口 `goal_execution_base_feedback_lr_nonzero_proven=false`、`L/R=0/0`；本轮没有触发真实发车。

## 剩余风险

- 本轮不实际触发真车 Nav2 发车；真实完整路线仍需要现场 operator 勾选安全确认后执行。
- 当前 live 上一次 Nav2 仍是旧 `pwm` 结果且 wheel raw L/R 为 `0/0`；本轮修的是下一次 ROS 执行后的 PC 证据闭环。
