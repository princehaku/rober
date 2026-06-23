# 启动雷达后的下一步

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏点击 `启动雷达` 返回后，雷达卡片提示 `雷达启动已返回，请点刷新雷达确认状态`，并把焦点带回 `刷新雷达`。该流程不自动刷新 scan proof，避免在 operator 未确认时追加第二个请求。
- `pc-tools/workstation/test/App.test.ts`：扩展 stopped LiDAR 场景，验证点击 `启动雷达` 后聚焦 `刷新雷达`，不自动调用 `/api/robot-control/radar/scan-proof/refresh`，也不调用 manual、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步普通首屏启动雷达后的下一步提示与安全边界。

## 真实上位机只读证据

- `ssh root@192.168.1.11 -p 37878` 可连接，`/api/status` 返回 LiDAR `lifecycle_running=false`、`lifecycle_state=stopped`、`latest_scan_proof_fresh=false`、`continuous_scan_status=lifecycle_not_running`。
- `/api/radar/status` 返回 `lifecycle_status=lifecycle_not_running`，`/api/radar/scan-proof/latest` 当前 404。
- `/api/base/feedback-samples/latest` 仍显示 `latest_pair.left_speed=0.0`、`right_speed=0.0`、`lr_nonzero_observed=false`。
- `/api/delivery/latest` 仍显示 `delivery_success=false`，缺 `confirm_delivery_completion`、`operator_report_ready_for_review`、`operator_observed_motion`、`operator_observed_stop` 和 `structured_hil_claims.delivery_success`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`，2 个测试文件、137 个用例通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，完成 app/server TypeScript 与 Vite production build。
- 通过：`git diff --check`。
- 已恢复 `npm test` 改写的历史 smoke JSON `checked_at` 副作用，提交范围不包含旧 artifacts 噪声。

## 剩余风险

- 本轮只改善 LiDAR stopped 卡点后的 PC 引导，不证明 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或真实 PC 键盘连续手控。
- 未自动触发真实 radar scan-proof refresh；现场仍需 operator 点 `刷新雷达` 来确认 LiDAR scan proof。
