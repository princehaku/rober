# PC Nav2 Execution Window Action Card Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 在 `RobotControlActionStatusCard.evidence` 中补齐 Nav2 路线执行窗口证据字段：执行是否 proven/HIL、非零底盘命令、底盘反馈样本、执行窗口 wheel raw L/R、IMU 姿态变化。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `nav2_route` action card 直接消费 `readback_summary.nav2.goal_execution_*` 字段，避免普通首屏只显示“需要重跑”但缺少为什么重跑的机器可读证据。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-action-status-card-nav2_route` DOM 暴露 `data-goal-execution-proven`、`data-base-command-nonzero-count`、`data-base-feedback-latest-raw-left/right`、`data-imu-attitude-delta-observed` 等字段。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 锁定默认空读数下的 fail-closed 字段，确保旧 summary 不会被误判为完整路线执行成功。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 Nav2 路线 action card 的执行窗口证据合同；地图工具口径保持为普通用户用 PC 大地图，工程调试用 RViz2/Foxglove。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过。
- `npm test -- test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints"`：通过。
- `npm test -- --run`：通过，2 个测试文件、396 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-BM6t7hsI.js` 与 `dist/assets/index-1TFDR4Wy.css`。
- `git diff --check`：通过。
- 7001 重启：旧 `node` PID `96707` 已停止，新监听进程为 `node` PID `10319`，地址 `TCP *:7001`。
- live bundle 只读检查：`http://127.0.0.1:7001/` 已引用 `index-BM6t7hsI.js` 和 `index-1TFDR4Wy.css`；包内命中 `data-base-command-nonzero-count`、`data-imu-attitude-delta-observed`、`?view=map`、`只看地图`、`rviz2`、`foxglove`、`2600px`、`1040px` 和 `calc(100vh - 8px)`。
- live summary 只读检查：`plain-action-status-card-nav2_route` 当前为 `ready_needs_wheel_rerun`，证据为 `base_command_nonzero_count=49`、`base_feedback_sample_count=239`、`base_feedback_nonzero_sample_count=0`、`base_feedback_latest_raw_left/right=0/0`、`imu_attitude_delta_observed=true`、`imu_roll_delta=4.387221`、`imu_pitch_delta=24.210531`、`next_base_command_mode=ros`。

## 剩余风险

- 本轮只补 PC Web 只读 summary/DOM 合同，没有执行真实 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 完整路线执行仍需要现场安全确认后重跑并复验同窗口 wheel raw L/R 非零；当前 live 形态已知存在 action 成功但 wheel raw L/R 仍为 0/0 的缺口。
- 当前地图已经按 PC 主视图放大，并保留 `?view=map`、只看地图、RViz2/Foxglove 工程配套口径；如果现场仍觉得小，下一轮应改成地图独占默认首页或增加浏览器第二屏自动打开，而不是把 RViz2 当普通用户主界面。
