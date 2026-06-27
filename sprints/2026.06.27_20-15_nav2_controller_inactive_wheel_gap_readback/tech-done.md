# Nav2 Controller Inactive Wheel Gap Readback

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 PC summary 的 Nav2 摘要合同中增加 `controller_server_active` 和 `controller_server_requested`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从固定只读 Nav2 status/proof readback 提升 controller 状态；当上次 action 成功但 wheel raw L/R 未非零且 controller inactive 时，下一步文案明确提示 controller 未 active。
- `pc-tools/workstation/test/catalog.test.ts`：覆盖旧 PWM artifact + controller inactive 的现场形态，确认 PC summary 不把 action succeeded 误报成完整自动驾驶。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录自动驾驶诊断口径。

## 验证结果

- `npm test -- test/catalog.test.ts --testNamePattern "Nav2|nav2|Robot Control summary"`：通过，36 个相关测试通过。
- `npm test`：通过，309 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积提示。
- `git diff --check`：通过。
- live 读回 `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：`controller_server_active=false`，`controller_server_requested=false`，`goal_execution_status=goal_succeeded`，wheel raw `L/R=0/0`，下一步文案提示 controller inactive 并要求用 ROS 重跑图上路线。

## 剩余风险

- 本轮不发送真实 Nav2 goal、不启动 controller、不发布 `/cmd_vel`；真实“自动驾驶动起来”仍需要现场勾选安全确认后按 PC 建议用 ROS/T13 重跑，并观察同窗口 wheel raw L/R 是否非零。
