# Summary Motion Runbook Top Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增运动 runbook alias：`live_motion_runbook_items`、action ids、ready/blocked action ids、primary action、start endpoints、acceptance endpoints 和 runbook 白话摘要。
- 顶层新增键盘连续手控验收短 alias：`keyboard_wheel_lr_nonzero` 和 `keyboard_stop_after_release`。
- `keyboard_wheel_lr_nonzero` 镜像 `keyboard_continuous_motion_verified`；`keyboard_stop_after_release` 从 `hold_keyboard` runbook 是否仍缺 `stop_after_release` 推导，缺失或没有 runbook 时 fail-closed 为 `false`。
- 更新 summary 合同、服务端返回、定向测试、catalog live-summary 合同测试和 PC 工作站产品文档，现场可以一条 `curl | jq` 看完整行程、键盘、自由移动、建图四项验收证据，不必展开 `live_closure_summary`。

## 验证结果

- 通过：`git diff --check`
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，结果 `1 passed / 9 passed`。
- 通过：`npm test -- --run test/catalog.test.ts -t "live-summary"`，结果 `1 passed / 1 passed / 180 skipped`。
- 通过：`npm test`，结果 `3 passed / 421 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`；仅保留 Vite 既有 chunk size warning。
- 通过：重启 `0.0.0.0:7001` 后，用只读 `GET /api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 确认 runbook 和键盘验收短 alias 不再为 `null`：`keyboard_wheel_lr_nonzero=false`、`keyboard_stop_after_release=false`、`live_motion_runbook_primary_action_id=run_nav2_route`、`live_motion_runbook_items_count=4`，ready action 为 `run_nav2_route,hold_keyboard,start_free_move`，blocked action 为 `start_mapping_when_sensors_ready`。

## 剩余风险

- 本轮只增加只读 alias，不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 当前真实 motion 仍未完成；`keyboard_wheel_lr_nonzero=false`、`keyboard_stop_after_release=false` 表示键盘按住窗口轮速和松开停止验收仍需要现场安全确认后的实测读回。
