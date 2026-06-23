# 2026-06-23 12:45 本轮进度逐项下一步

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 的四个目标行新增逐项 `下一步` 文案。轮速、行程、送达和键盘都能在同一块里看到下一手动作；主按钮仍只指向第一处未完成卡点。
- `pc-tools/workstation/src/styles.css`：进度行从 4 列调整为 5 列，并在窄屏回落为单列，避免新增下一步文案挤压按钮。
- `pc-tools/workstation/test/App.test.ts`：覆盖默认首屏的四项下一步，以及 L/R=`0/0` 时轮速行显示 `下一步：检查轮速卡点。`
- `docs/product/pc_tools_workstation.md`：同步逐项目标下一步的展示规则和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 137 passed (137)`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
- 通过：`git diff --check`

## 真实只读状态

- `ssh root@192.168.1.11 -p 37878` 可读上位机 `127.0.0.1:8787`。
- `/api/base/feedback-samples/latest` 仍显示 `wheel_feedback_summary.latest_pair.left_speed=0.0`、`right_speed=0.0`、`lr_nonzero_observed=false`。
- `/api/nav2/goal/execution/latest` 读到历史 `goal_succeeded`、`feedback_sample_count=8`、`evidence_ref=o11-nav2-goal-execution-1782099547218`。
- `/api/delivery/latest` 仍显示 `delivery_success=false`，缺 `confirm_delivery_completion`、`operator_report_ready_for_review`、`operator_observed_motion`、`operator_observed_stop`、`structured_hil_claims.delivery_success`。
- `/api/operator/report` latest 是 `delivery-draft-smoke-1782102952`，视频和路线 ref 存在，但 operator safety、observed motion/stop 与 delivery success 仍为 false。
- `0.0.0.0:7071` 仍被 Clash Verge `verge-mihomo` PID `2183` 占用，本轮未停止该进程。

## 剩余风险

- 本轮只改善 PC 普通首屏四项目标的扫读效率，不证明真实 wheel raw L/R 非零、完整 Nav2 路线本轮新执行、delivery success 或真实 PC 键盘连续手控。
- 真实闭环仍需要现场 operator 按当前下一步逐项执行并采集成功证据。
