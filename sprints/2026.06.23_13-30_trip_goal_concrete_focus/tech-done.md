# 2026-06-23 13:30 行程卡点直达具体控件

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 的 `去行程/去行程卡点` 不再只聚焦 `行程操作` 大面板。未勾选行程前确认时聚焦 checkbox，确认后聚焦红色 `执行行程`，已有本轮行程材料时聚焦只读重读按钮。
- `pc-tools/workstation/test/App.test.ts`：扩展普通进度快捷按钮测试，验证默认主按钮聚焦 `plainTripSafetyConfirmed` checkbox；扩展行程流程测试，验证勾选确认后 `去行程` 聚焦 `plain-trip-execute` 且不会自动调用 Nav2 execute。
- `docs/product/pc_tools_workstation.md`：同步 `去行程/去行程卡点` 的具体落点和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - 首轮失败：同一测试内重复声明 `focusSpy`，已修复后重跑。
  - 第二轮失败：旧断言仍期待聚焦 `plain-trip-run` 大面板，已更新为聚焦 `plainTripSafetyConfirmed` checkbox 后重跑。
  - 最终通过：`Test Files 2 passed (2)`、`Tests 137 passed (137)`。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
- 通过：`git diff --check`

## 真实只读状态

- `ssh root@192.168.1.11 -p 37878` 可读上位机 `127.0.0.1:8787`。
- `/api/radar/status` 显示 `lifecycle_status=lifecycle_not_running`、`lifecycle_running=false`，`/api/radar/scan-proof/latest` 为 404 missing。
- `/api/base/feedback-samples/latest` 仍显示 `wheel_feedback_summary.latest_pair.left_speed=0.0`、`right_speed=0.0`、`lr_nonzero_observed=false`。
- `/api/nav2/goal/execution/latest` 读到历史 `goal_succeeded`、`feedback_sample_count=8`、`evidence_ref=o11-nav2-goal-execution-1782099547218`。
- `/api/delivery/latest` 仍显示 `delivery_success=false`，缺现场确认和 `structured_hil_claims.delivery_success`。
- `0.0.0.0:7071` 仍被 Clash Verge `verge-mihomo` PID `2183` 占用，本轮未停止该进程。

## 剩余风险

- 本轮只改善 PC 普通首屏行程卡点的焦点路径，不证明真实 wheel raw L/R 非零、完整 Nav2 路线本轮新执行、delivery success 或真实 PC 键盘连续手控。
- 真正完整 Nav2 路线执行仍需要现场 operator 勾选安全确认后显式点击 `执行行程`，并由上位机返回本轮 `goal_succeeded` 与反馈样本。
