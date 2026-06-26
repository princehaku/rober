# PC Nav2 Latest 执行证据显示修复

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 将 `RobotControlNavGoalExecutionLatestResponse.robot_control_executed` 从固定 `false` 调整为 `boolean`。
  - 原因：latest GET 是只读回放，不会发起 NavigateToPose，但应如实显示上位机 latest artifact 是否记录过真实 Nav2 执行。
- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/nav2/goal/execution/latest` 从远端 payload 或 nested `latest_result` 提取 `robot_control_executed=true`。
  - `goal_execution_key_values.robot_control_executed` 改为 nested latest artifact 优先，避免上位机只读 readback 顶层 guard `false` 覆盖真实执行证据。
  - 保留只读边界：该接口仍只 GET `/api/nav2/goal/execution/latest`，不调用 `/api/nav2/goal/execute`、`/api/base/manual` 或底盘命令。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 latest proxy 契约测试，固定“只读 latest 可展示历史执行证据，但不 replay navigation”的行为。

## 验证结果

- `npm test`：通过，2 个 test files，219 个 tests passed。
- `npm run build`：通过；Vite 仍提示单 chunk 大于 500 kB 的既有 warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 7001 真机只读 smoke：通过。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node ... TCP *:7001 (LISTEN)`。
  - `GET /api/robot-control/nav2/goal/execution/latest?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=latest_loaded`、`robot_control_executed=true`、`goal_execution_key_values.robot_control_executed=true`、`status=goal_succeeded`、`result_status=succeeded`、`feedback_sample_count=8`。
  - `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `free_roam_autonomy_start_ready=true`。

## 剩余风险

- 本轮修复 PC 对 latest artifact 的可见性，不等同证明本轮重新跑完整 Nav2 行程。
- 真机当前上位机 latest artifact 已有 `goal_succeeded` 和 `robot_control_executed=true`，但 delivery success 仍需要 operator report / 送达材料 gate，不应由 PC latest 自动置 true。
- PC API 已重启到 `0.0.0.0:7001` 并完成只读 smoke；本轮未触发新的 Nav2 发车。
