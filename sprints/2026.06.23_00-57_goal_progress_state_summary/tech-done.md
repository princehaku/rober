# 2026-06-23 00:57 本轮进度当前状态摘要

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 新增 `当前状态` 单行摘要，把轮速记录、行程执行、送达确认、键盘手控四项的当前状态压成一句普通话。
- 摘要只消费页面已有只读 computed state，不刷新接口、不执行行程、不确认送达、不发送 manual、keyboard pulse、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`：补充默认首屏、行程成功送达未完成、键盘可使用三类状态摘要断言。
- `docs/product/pc_tools_workstation.md`：同步记录该只读摘要。

## 验证结果

- 只读真实上位机复核：`GET http://192.168.1.11:8787/api/base/status` 返回 `T=1001` 可读、`L/R=0/0`、`wheel_feedback_lr_nonzero_proven=false`、`sends_motion_commands=false`、`robot_control_executed=false`。
- 只读真实上位机复核：`GET http://192.168.1.11:8787/api/nav2/goal/execution/latest` 返回 latest `goal_succeeded`、`evidence_ref=o11-nav2-goal-execution-1782099547218`、`feedback_samples=8`、`delivery_success=false`。
- 只读真实上位机复核：`GET http://192.168.1.11:8787/api/delivery/latest` 返回 `delivery_success=false`、`robot_control_executed=false`。
- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善四个收口目标的首屏可读性；不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或 PC 键盘连续手控。
- 真实能力仍需要现场 operator 按安全口径显式执行并提供实车证据。
