# 2026-06-27 18:58 Nav2 ROS 命令模式证据补强

## sprint_type

micro

## 目标

- 面向本轮用户反馈“自动驾驶是什么问题没法动，需要修好”，补齐下一次真实 Nav2 ROS/T=13 重跑时的排障证据。
- 让 PC summary 能区分“Nav2/bridge 已发出 ROS/T=13 非零底盘命令”和“同窗口 wheel raw L/R 仍未非零”。
- 保持普通用户简洁界面和现有安全边界：本轮不自动发车、不绕过安全确认、不把 action success 或命令非零写成 delivery success。

## 实际改动

- `onboard/scripts/o11_nav2_goal_execution_proof.py`
  - `summarize_command_debug_log()` 新增 `command_mode_counts` 和 `latest_nonzero_command_mode`。
  - 兼容历史 command debug log：没有 `command_mode` 时按 WAVE ROVER vendor JSON `T` 值推断，`T=13 -> ros`、`T=11 -> pwm`、`T=1 -> speed`。
  - 非零判断继续覆盖 `L/R` 和 `X/Z`，因此 ROS/T=13 的 `X/Z` 非零会被计入“底盘命令已到 bridge”证据。
- `pc-tools/workstation/src/server/index.ts`
  - Nav2 execute proxy 的 key values 新增 `base_command_latest_nonzero_mode` 和 `base_command_mode_counts`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `readback_summary.nav2` 新增 `goal_execution_base_command_latest_nonzero_mode` 和 `goal_execution_base_command_mode_counts`。
  - 未加载兜底结构同步补齐新字段，避免 UI/合同出现 `undefined`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步扩展 `RobotControlSummaryResponse.readback_summary.nav2` 合同字段。
- `pc-tools/workstation/test/App.test.ts`
  - 更新默认 summary fixture。
- `pc-tools/workstation/test/catalog.test.ts`
  - 锁定 summary 和 execute proxy 对 ROS/T=13 命令模式证据的透出。
- `onboard/tests/test_o11_nav2_goal_execution_proof.py`
  - 增加 ROS/T=13 `X/Z` 非零统计测试，并扩展 PWM/T=11 兼容测试。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 PC/Nav2 命令模式证据边界。

硬件资料依据：本轮涉及 WAVE ROVER vendor JSON 指令语义，已复核 `docs/vendor/VENDOR_INDEX.md`。采用其索引的 WAVE ROVER 资料口径：`T=13` 为 ROS `X/Z` 控制入口，`T=11` 为 PWM 诊断入口，`T=1` 为 speed 命令，`T=1001` 为底盘反馈。

## 验证结果

- `python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof`
  - 通过：`Ran 8 tests in 0.003s OK`
- `python3 -m unittest onboard.tests.test_upper_robot_api`
  - 通过：`Ran 64 tests in 0.156s OK`
- `npm test -- --run test/catalog.test.ts -t "Robot Control summary derives Nav2 execution proof from live execution facts"`
  - 通过：`1 passed | 128 skipped`
- `npm test -- --run test/catalog.test.ts -t "Nav2 execution proxy allows real base feedback evidence but still blocks delivery success"`
  - 通过：`1 passed | 128 skipped`
- `npm test -- --run`
  - 通过：`2 passed (2) / 304 passed (304)`
- `npm run build`
  - 通过：TypeScript、Vite client build、server TypeScript 均通过。
  - 剩余提示：Vite chunk size 超过 500 kB，为既有构建体积提示，不影响本轮功能。
- `npm run lint`
  - 通过。
- `git diff --check`
  - 通过。

## 剩余风险

- 本轮没有触发真实 Nav2 execute、manual、keyboard、free-roam start、delivery、stop 或 `/cmd_vel`；真实行程仍需要现场操作者确认安全后重跑。
- 当前 live 只读状态显示相机是 `source_first_frame_failed / uvc_no_frame_not_exclusive`，不是 PC 页面独占导致；还需要现场检查 `/dev/video1`、摄像头供电/线缆/格式/驱动。
- 当前 live 雷达 lifecycle 虽运行，但 latest proof 仍不完整、scan preview 点数为 0；小车低速运动不依赖雷达，但建图/避障验收仍需要刷新出可用雷达材料。
- 最近 Nav2 action 曾成功，但 wheel raw L/R 同窗口仍为 `0/0`；本轮补强的是 ROS/T=13 命令排障可见性，不等于完整自动驾驶已修好。
