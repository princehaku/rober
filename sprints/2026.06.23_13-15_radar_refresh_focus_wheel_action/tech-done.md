# 2026-06-23 13:15 雷达刷新后直达轮速动作

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `刷新雷达` 确认雷达已运行后，不再只聚焦 `轮速记录` 大面板，而是复用轮速目标的具体下一手动作。根据当前状态落到 `已检查轮速卡点`、`检查后重试读非零 L/R`、`恢复试动确认` 或 `试动一下`。
- `pc-tools/workstation/test/App.test.ts`：更新雷达刷新 smoke，验证雷达刷新后焦点落到 `plain-wheel-trial`，并继续确认没有调用 first-jog/manual/Nav2/delivery 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步雷达刷新后直达轮速动作的规则和安全边界。

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
- `/api/radar/status` 显示 `lifecycle_status=lifecycle_not_running`、`lifecycle_running=false`，`/api/radar/scan-proof/latest` 为 404 missing。
- `/api/base/feedback-samples/latest` 仍显示 `wheel_feedback_summary.latest_pair.left_speed=0.0`、`right_speed=0.0`、`lr_nonzero_observed=false`。
- `/api/delivery/latest` 仍显示 `delivery_success=false`，缺现场确认和 `structured_hil_claims.delivery_success`。
- `0.0.0.0:7071` 仍被 Clash Verge `verge-mihomo` PID `2183` 占用，本轮未停止该进程。

## 剩余风险

- 本轮只改善雷达刷新后的 PC 焦点路径，不证明真实 wheel raw L/R 非零、完整 Nav2 路线本轮新执行、delivery success 或真实 PC 键盘连续手控。
- 真实轮速和 LiDAR delta 仍需要现场安全确认后显式点击低速试动并由上位机返回 during-motion 证据。
