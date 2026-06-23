# 2026-06-23 12:30 本轮进度键盘卡点直达

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 的 `去键盘` 不再只聚焦键盘面板，而是复用键盘 gate 的下一步目标。条件满足时聚焦 `启用键盘（按键才动）`；缺恢复确认、轮速记录或雷达移动记录时聚焦对应补证动作；其它缺项聚焦 `复查手控条件`。
- `pc-tools/workstation/test/App.test.ts`：扩展 `本轮进度` 快捷按钮测试，验证默认缺项状态下 `去键盘` 聚焦 `keyboard-control-recheck`，且不调用 Nav2、delivery complete、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步 `本轮进度 -> 去键盘` 的直达规则和安全边界。

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
- `0.0.0.0:7071` 仍被 Clash Verge `verge-mihomo` PID `2183` 占用，本轮未停止该进程。

## 剩余风险

- 本轮只改善 PC 普通首屏键盘卡点导航，不证明真实 wheel raw L/R 非零、完整 Nav2 路线本轮新执行、delivery success 或真实 PC 键盘连续手控。
- 真实键盘连续手控仍要求现场材料完整后，operator 显式点击 `启用键盘（按键才动）`，再按住方向键/WASD 至少连续成功转发 2 个 bounded manual pulse。
