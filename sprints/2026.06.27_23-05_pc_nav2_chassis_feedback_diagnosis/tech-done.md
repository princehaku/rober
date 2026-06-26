# 2026-06-27 23:05 PC Nav2 chassis feedback diagnosis

## sprint_type: micro

本轮继续推进“完整 Nav2 路线执行”和“自动驾驶为什么没法动”的普通用户可解释性。设计先行结论：雷达 freshness 不能再作为本轮“车不动”的主解释；当前现场材料显示 Nav2/bridge 已发非零底盘命令，但 WAVE ROVER `T=1001 L/R` 仍为 `0/0`，因此 PC 首屏必须把问题指向底盘反馈闭环/执行链。

## 现场只读证据

- SSH：`ssh root@192.168.1.11 -p 37878` 成功，主机 `op-z3-b6.home`。
- 服务：`trashbot-upper-robot-api` active，`trashbot-local-webrtc-camera` active。
- 相机：`/dev/video1` 为 `source_first_frame_failed`，`source_usage.status=not_in_use`，继续证明不是 PC 页面独占，而是 UVC 首帧读不到。
- 底盘：`/api/base/status` 可读 `/dev/ttyS5 @ 115200`，本次只读 `T=130` 后收到 13 帧 `T=1001`，电压约 `12.41V`，但 `L/R=0/0`。
- Nav2 latest：`goal_succeeded`，`base_command_nonzero_count=49`，latest nonzero vendor command 为 `{"T":11,"L":90,"R":-90}`；`base_feedback_sample_count=216`，`base_feedback_lr_nonzero_proven=false`。

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 把 O11/Nav2 latest 的 `base_command_summary` 与 `base_feedback_summary` 提升到 summary 的 `readback_summary.nav2.goal_execution_base_*` 字段。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `RobotControlSummaryResponse.readback_summary.nav2`，声明 base command / base feedback 摘要字段。
  - 补齐 Nav2 execution response 的 `server_timeout_s` 字段，修复构建时发现的 contract 漂移。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏从 summary 继承 base command / feedback 字段。
  - 当 `goal_succeeded` 且已发非零底盘命令，但 `base_feedback_lr_nonzero_proven=false` 时，行程摘要、执行进度和地图 caption 改为说明：Nav2 已发非零底盘命令，但底盘反馈 L/R 仍未非零；优先查电机使能、供电、底盘模式和控制模式，不再误导为雷达阻塞。
- `pc-tools/workstation/test/App.test.ts`
  - 新增现场形态回归测试：`goal_succeeded + base_command_nonzero_count=49 + base_feedback_sample_count=216 + L/R=0/0 + hil_pass=false`。
- `docs/product/pc_tools_workstation.md`
  - 记录本轮只读 SSH 证据和 PC 普通首屏新解释口径。
- `docs/interfaces/ros_runtime_contracts.md`
  - 记录 `goal_execution_base_*` summary contract 和排障边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "Nav2 action success|nonzero base commands|latest Nav2 not-proven"`
  - 通过，`Test Files 2 passed (2)`，`Tests 4 passed | 249 skipped (253)`。
- `cd pc-tools/workstation && npm test`
  - 通过，`Test Files 2 passed (2)`，`Tests 253 passed (253)`。
- `cd pc-tools/workstation && npm run lint`
  - 通过，ESLint 无报错。
- `cd pc-tools/workstation && npm run build`
  - 通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
  - 保留既有 Vite chunk size warning。
- `git diff --check`
  - 通过，无 whitespace error。

## 剩余风险

- 本轮没有执行新的运动命令，只做 SSH 只读复核和 PC 可解释性修正。
- 当前仍未证明真实轮速非零、外部视频位移、LiDAR delta 或 delivery success。
- 相机仍需现场检查 UVC 输入、线材/供电、采集卡模式或替换 known-good UVC。
- 自动驾驶下一步应优先查 WAVE ROVER 电机使能、供电、底盘模式、PWM/speed 控制模式和真实执行链，而不是继续把“不能动”归因到雷达。
