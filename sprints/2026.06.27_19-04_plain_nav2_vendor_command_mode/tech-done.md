# 2026-06-27 19:04 普通首屏 Nav2 vendor 命令模式可见化

## sprint_type

micro

## 目标

- 继续推进 PC 易用性和完整 Nav2 路线执行排障：普通首屏不只显示“已发非零底盘命令”，还要说清这轮底盘入口是 `ROS/T=13`、`PWM/T=11` 还是 `speed/T=1`。
- 帮现场判断“自动驾驶为什么没法动”：若路线 action 成功但 wheel raw L/R 仍为 `0/0`，首屏直接指向底盘反馈闭环，不再让用户怀疑摄像头或雷达阻塞。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `summaryNav2ExecutionValues()` 接入 `goal_execution_base_command_latest_nonzero_mode` 和 `goal_execution_base_command_mode_counts`。
  - 新增普通首屏 vendor 命令模式标签：`ros -> ROS/T=13`、`pwm -> PWM/T=11`、`speed -> speed/T=1`。
  - 当前事实条、行程未闭环说明、自动驾驶诊断统一使用 vendor 命令入口文案，例如“已发 ROS/T=13 非零底盘命令 19 条，底盘反馈 L/R=0/0”。
  - 该改动只读 summary/latest 证据，不新增发车、手控、free-roam、送达或 `/cmd_vel` 调用。
- `pc-tools/workstation/test/App.test.ts`
  - 更新旧 PWM/T=11 未闭环用例断言。
  - 新增 ROS/T=13 已发出但 wheel raw L/R 仍为 0/0 的普通首屏回归测试。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏 vendor 命令模式可见化边界。

硬件资料依据：本轮复核 `docs/vendor/VENDOR_INDEX.md`，采用其 WAVE ROVER UART JSON 口径：`T=13` 为 ROS `X/Z` 控制入口，`T=11` 为 PWM 输入，`T=1` 为 speed 命令，`T=1001` 为 wheel raw L/R 反馈材料。

## 验证结果

- `npm test -- --run test/App.test.ts -t "keeps IMU-only route arrival visible while calling out zero wheel readback|explains Nav2 success with nonzero base commands but zero wheel feedback as a chassis feedback issue|shows ROS T13 command evidence"`
  - 通过：`3 passed | 173 skipped`
- `npm test -- --run test/App.test.ts -t "refreshes Robot Control summary after plain Nav2 execution latest is loaded|keeps the summary-requested ROS rerun visible"`
  - 通过：`2 passed | 174 skipped`
- `npm test -- --run`
  - 通过：`2 passed (2) / 305 passed (305)`
- `npm run build`
  - 通过：TypeScript、Vite client build、server TypeScript 均通过。
  - 剩余提示：Vite chunk size 超过 500 kB，为既有构建体积提示。
- `npm run lint`
  - 通过。
- `git diff --check`
  - 通过。

## 剩余风险

- 本轮没有触发真实 Nav2 execute、manual、keyboard、free-roam start、delivery、stop 或 `/cmd_vel`；实车自动驾驶仍需现场安全确认后重跑验证。
- 当前 live 只读状态仍显示摄像头 `source_first_frame_failed / uvc_no_frame_not_exclusive`，即非页面独占但 UVC 无首帧，需要现场检查摄像头链路。
- 当前 live Nav2 最近记录仍是旧 `base_command_mode=pwm`、wheel raw L/R 同窗口 `0/0`；本轮只是让下一次 ROS/T=13 复验结果在普通首屏可见，不等于 wheel 闭环已完成。
