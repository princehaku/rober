# PC Nav2 Execution Latest Summary

sprint_type: micro

## 实际改动

- PC summary 新增只读读取 `/api/nav2/goal/execution/latest`，并把最近图上路线执行状态、结果、反馈次数、目标坐标、evidence ref 和 `robot_control_executed` 压缩到 `readback_summary.nav2`。
- PC summary 对该 latest endpoint 只豁免历史证据路径上的 `robot_control_executed=true`；顶层 `safe_to_control`、`robot_control_executed`、`delivery_success` 仍 fail-closed，不因 summary 读取变成控制执行。
- 普通首屏行程/地图状态接入 summary 的 latest 执行摘要：当手动 latest key values 为空但 summary 已读到完整成功证据时，仍显示最近行程已到达并读到反馈。
- 更新 PC 工作站产品文档，记录 summary latest Nav2 执行证据的边界和普通 UI 行为。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts`：通过，139 tests passed。
- `cd pc-tools/workstation && npm test -- catalog.test.ts`：通过，106 tests passed。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB 的既有体积 warning。
- `git diff --check`：通过。
- 真实 PC 7001 只读 smoke：`HOST=0.0.0.0 PORT=7001 ./node_modules/.bin/tsx src/server/index.ts` 已监听 `*:7001`；
  `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `robot_api_connection.status=readable`、
  `console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`safe_command_boundary.robot_control_executed=false`、
  `dangerous_true_fields=[]`；`readback_summary.nav2.goal_execution_status=goal_succeeded`、
  `goal_execution_result_status=succeeded`、`goal_execution_robot_control_executed=true`、`goal_execution_feedback_sample_count=8`、
  `goal_execution_goal_frame_id=map`、`goal_execution_goal_x=0.8`、`goal_execution_goal_y=0`。

## 剩余风险

- 本轮只做 PC 侧只读摘要与普通 UI 呈现，不主动执行新的 NavigateToPose，也不代表新的 HIL 行程已经在本轮现场复跑。
- 真实 smoke 证明最近一次历史 Nav2 execution 已成功读入 PC summary；本轮仍未重新触发新的 NavigateToPose 或做现场 delivery success。
