# 2026-06-23 12:15 本轮进度送达卡点直达

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 的 `去送达` 改为聚焦当前送达下一手动作。缺本轮行程时回到行程执行；缺行程材料或送达材料时优先聚焦 `准备送达材料` 或 `保存送达草稿（不确认）`；材料已齐但现场确认未完成时聚焦 `全部已确认`；全部确认项齐备后聚焦红色 `确认送达（不发车）`。
- `pc-tools/workstation/test/App.test.ts`：扩展普通送达流程测试，验证 `去送达` 在草稿保存后聚焦 `plain-delivery-mark-all-confirmed`，全项确认后聚焦 `plain-delivery-confirm-submit`，且不会自动调用 `delivery/complete`。
- `docs/product/pc_tools_workstation.md`：同步 `本轮进度 -> 去送达` 的直达规则和安全边界。

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

- 本轮只改善 PC 普通首屏送达卡点导航，不证明真实 wheel raw L/R 非零、完整 Nav2 路线本轮新执行、delivery success 或真实 PC 键盘连续手控。
- 真实送达完成仍需要现场 operator 明确确认到达、停止、材料核对和已投放/送达后，再点击 `确认送达（不发车）` 由上位机 gate 返回成功。
