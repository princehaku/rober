# PC Nav2 请求模式与下一次复验事实对齐

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainTripRequestedBaseCommandMode()`，执行图上路线时优先采用 summary/latest 里的 `next_execution_base_command_mode`，仅在缺失或非法值时默认 `ros`。
  - 当前 live 形态 `pending_ros_rerun_after_pwm` 会继续显式发送 `base_command_mode=ros`，与首屏“用 ROS 重跑图上路线”的按钮和状态一致。
  - 该改动只调整 PC 请求体生成，不绕过安全确认，不新增 Nav2/manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel` 调用。
- `pc-tools/workstation/test/App.test.ts`
  - 在 summary-only 的旧 PWM 成功但 wheel raw L/R=0/0 场景中，点击 `用 ROS 重跑图上路线` 后断言 POST body 包含 `base_command_mode=ros` 与 `confirm_navigation_execution=true`。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录执行请求体现在跟随 `next_execution_base_command_mode`，当前现场策略为 ROS 重跑。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --run App.test.ts -t "summary-requested ROS rerun"`
  - 结果：`1 passed | 171 skipped`
- 已通过：`cd pc-tools/workstation && npm test -- --run`
  - 结果：`2 passed` test files，`301 passed`
- 已通过：`cd pc-tools/workstation && npm run build`
  - 结果：`tsc` 与 `vite build` 通过；仍有既有的 chunk size warning。
- 已通过：`cd pc-tools/workstation && npm run lint`
  - 结果：`eslint .` 通过。
- 已通过：`git diff --check`

## 剩余风险

- 本轮未发真实 Nav2 goal；真实完整路线执行仍需要现场勾选安全确认后点击 `用 ROS 重跑图上路线`，再检查同窗口 `wheel raw L/R` 是否非零。
- 只读 SSH/artifact 复核显示上一轮仍是 `base_command_mode=pwm`，且底盘命令有非零但 `T1001 L/R=0/0`；这轮代码只确保下一次 PC 请求体与 ROS 重跑策略一致，不证明电机使能、供电、底盘模式或反馈链路已经修复。
