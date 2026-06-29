# 2026.06.29 16:40 PC Nav2 O11 控制服务证据合并

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts` 从 O11 `nav2_goal_execution_latest.latest_result.managed_runtime.lifecycle_ready` 派生 `planner_server_active`、`controller_server_requested` 和 `controller_server_active`。
- 修正完整 NavigateToPose 执行 artifact 已经证明 controller 在本轮托管 runtime 中 active 时，summary 仍被 O10 planner-only proof 或旧 lifecycle 读数覆盖成 `controller_server_active=false` 的问题。
- `pc-tools/workstation/test/catalog.test.ts` 增加回归测试：当 Nav2 status/proof 旧读数为 controller false，但 O11 managed runtime 四个执行节点 active 时，Robot Control summary 必须输出 controller requested/active，并且不再把 `controller_server_inactive` 放入发车 blocker。
- `pc-tools/README.md` 同步记录该只读证据合并规则。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "prefers O11 managed execution lifecycle"`，结果 `1 passed | 165 skipped`。
- 已通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`，结果 `43 passed | 123 skipped`。
- 已通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed / 383 tests passed`。
- 已通过：`npm --prefix pc-tools/workstation run build`，Vite 构建成功；仍有既有 chunk size warning。
- 已通过：`git diff --check`。
- 已通过：重启 PC Node 到 `0.0.0.0:7001` 后只读 live summary 返回 `planner=true`、`controller_requested=true`、`controller=true`、`goal_status=goal_succeeded`、`last_mode=pwm`、`next_mode=ros`、`nonzero_cmd=true/count=49`、`wheel=false/L=0/R=0`、`nav2_goal_blockers=[]`。
- live 下一步已收敛为：旧 PWM 路线 action 成功但执行窗口轮速 L/R=0/0 未非零；主因不是雷达、相机或控制服务；勾安全确认后用 ROS 模式重跑并复验执行窗口轮速 L/R。

## 剩余风险

- 本轮修复的是 PC summary 对 O11 执行 runtime controller 事实的合并，不直接触发真实发车。
- 现场最新 O11 旧 artifact 仍显示：PWM 模式 NavigateToPose action 成功、非零底盘命令和 IMU 姿态变化已出现，但执行窗口轮速 L/R 仍为 `0/0`，完整自动驾驶仍需在安全确认后用 ROS 模式重跑并复验轮速 L/R 非零。
