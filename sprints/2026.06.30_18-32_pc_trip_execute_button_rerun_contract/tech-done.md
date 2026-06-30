# PC Trip Execute Button Rerun Contract Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `plain-trip-execute` 发车按钮新增按钮级 wheel rerun 执行合同：
    `data-requested-base-command-mode`、`data-last-base-command-mode`、`data-next-base-command-mode`、`data-wheel-feedback-status`、`data-wheel-lr-nonzero-proven`。
  - 同一按钮新增执行后复验合同：
    `data-post-execute-latest-refresh-required=true`、`data-post-execute-summary-refresh-required=true`、`data-fixed-execution-latest-endpoint=/api/robot-control/nav2/goal/execution/latest`、`data-fixed-wheel-feedback-readback-endpoint=/api/robot-control/base/feedback-samples`。
  - 同一按钮固定最小预检边界：
    `data-camera-preflight-required=false`、`data-radar-preflight-required=false`、`data-route-wysiwyg-preflight-required=false`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖默认未勾安全确认状态和旧 PWM 成功但 wheel L/R=0/0 的 ROS 重跑状态。
  - 确认按钮会提交 `base_command_mode=ros`，且不调用 manual 或 `/cmd_vel`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步按钮级执行合同和最小预检口径。

## 验证结果

- `npm test -- App.test.ts`：通过，1 个测试文件、225 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、402 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-C2Jg9_fp.js` 与 `dist/assets/index-BCQK7HRw.css`。
- `git diff --check`：通过。
- 7001 重启：旧监听 `node` PID `70095` 已停止，新监听为 `node` PID `84751`，地址 `TCP *:7001`，日志显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- live bundle 检查：`http://127.0.0.1:7001/` 已引用 `assets/index-C2Jg9_fp.js` 和 `assets/index-BCQK7HRw.css`；JS bundle 命中 `data-requested-base-command-mode`、`data-post-execute-latest-refresh-required`、`data-fixed-execution-latest-endpoint`、`data-fixed-wheel-feedback-readback-endpoint`、`data-camera-preflight-required`、`data-radar-preflight-required`、`data-route-wysiwyg-preflight-required`。
- live summary 只读检查：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `status=needs_wheel_rerun`、`route_ready=true`、`nav2_success=true`、`wheel_nonzero=false`、`wheel_rerun_command_mode=ros`、`nav2_goal_wheel_feedback_status=goal_succeeded_but_wheel_lr_zero`。

## 剩余风险

- 本轮只补 PC 发车按钮的 DOM 合同和测试，不在 live 环境点击真实 `plain-trip-execute`，不发送 Nav2/manual/keyboard/free-roam/stop 或 `/cmd_vel`。
- 真实 wheel raw L/R 非零闭环仍需要现场安全确认后执行 ROS 重跑并读取同窗口上车反馈。
