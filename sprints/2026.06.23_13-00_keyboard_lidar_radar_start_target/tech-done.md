# 2026-06-23 13:00 键盘缺雷达时先指向启动雷达

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：键盘 gate 缺 `雷达移动记录` 且普通首屏判断雷达未运行时，下一步文案从 `试动读取雷达移动记录` 改为 `先启动雷达，再试动读取雷达移动记录`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`本轮进度 -> 去键盘` 与 `复查手控条件` 的聚焦目标在该状态下优先落到 `启动雷达`，启动返回后可落到 `刷新雷达`；仍不会自动点击或调用雷达/底盘/导航接口。
- `pc-tools/workstation/test/App.test.ts`：扩展“轮速已满足但雷达移动记录缺失”的键盘 gate 测试，覆盖雷达未运行时 `去键盘` 聚焦 `plain-radar-start`，并确认未调用 `/api/robot-control/radar/start` 或 manual。
- `docs/product/pc_tools_workstation.md`：同步键盘缺雷达时的启动雷达优先规则。

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
- `/api/delivery/latest` 仍显示 `delivery_success=false`，缺 `confirm_delivery_completion`、`operator_report_ready_for_review`、`operator_observed_motion`、`operator_observed_stop`、`structured_hil_claims.delivery_success`。
- `0.0.0.0:7071` 仍被 Clash Verge `verge-mihomo` PID `2183` 占用，本轮未停止该进程。

## 剩余风险

- 本轮只改善缺雷达移动记录时的操作路径，不证明真实 wheel raw L/R 非零、完整 Nav2 路线本轮新执行、delivery success 或真实 PC 键盘连续手控。
- 真正的 LiDAR motion delta 仍需要现场先启动/刷新雷达，再在安全确认后执行低速试动并由上位机返回可追溯材料。
