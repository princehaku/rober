# 2026-06-27 19:11 Nav2 旧 artifact 命令模式 fallback

## sprint_type

micro

## 目标

- 推进完整 Nav2 路线执行排障：旧 O11 artifact 已经记录 `base_command_mode` 和非零底盘命令数时，PC summary 也要能显示最近非零命令模式。
- 避免现场旧 PWM 成功但 wheel raw L/R=0/0 的记录在普通首屏继续缺 `PWM/T=11` 入口提示。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当 `base_command_summary.latest_nonzero_command_mode` 缺失、但 `nonzero_command_count>0` 且 `base_command_mode` 为 `ros|pwm|speed` 时，自动补出 `goal_execution_base_command_latest_nonzero_mode`。
  - 当 `command_mode_counts` 缺失时，同步补出 `{ "<base_command_mode>": nonzero_command_count }`。
  - 该逻辑只读同一个 Nav2 execution artifact，不改变 execution proof、HIL proof 或任何控制门禁。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增旧 O11 artifact 回归测试：`base_command_mode=pwm`、`nonzero_command_count=49`、无 latest mode 字段时，summary 返回 `pwm` 和 `{"pwm":49}`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录旧 artifact 命令模式 fallback 边界。

## 验证结果

- `npm test -- --run test/catalog.test.ts -t "Robot Control summary infers latest Nav2 command mode for older execution artifacts|Robot Control summary derives Nav2 execution proof from live execution facts"`
  - 通过：`2 passed | 128 skipped`
- `npm test -- --run test/App.test.ts -t "shows ROS T13 command evidence|explains Nav2 success with nonzero base commands"`
  - 通过：`2 passed | 174 skipped`
- `npm test -- --run`
  - 通过：`2 passed (2) / 306 passed (306)`
- `npm run build`
  - 通过；保留既有 Vite chunk size warning，不影响产物生成。
- `npm run lint`
  - 通过。
- `git diff --check`
  - 通过，无空白错误。

## 剩余风险

- 本轮没有触发真实 Nav2 execute、manual、keyboard、free-roam start、delivery、stop 或 `/cmd_vel`。
- fallback 只能在旧 artifact 已有 `base_command_mode` 和 `nonzero_command_count>0` 时生效；没有非零命令数的 artifact 仍保持 `not_loaded`。
- 完整自动驾驶仍需现场安全确认后用 ROS/T=13 重跑，并证明同窗口 wheel raw L/R 非零。
