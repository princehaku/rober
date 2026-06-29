# PC Nav2 发车标签对齐地图所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`safe_command_boundary.nav2_goal_label` 不再一律显示“路线读数已准备，等待地图画面确认”。当路线已经画到地图上时显示“图上路线已显示，等待安全确认”；当路线和小车位置都可见时显示“图上路线和小车位置已显示，等待安全确认”。
- `pc-tools/workstation/src/shared/contracts.ts`：同步扩展 `nav2_goal_label` 类型，保证 server build 覆盖新增标签。
- `pc-tools/workstation/test/catalog.test.ts`：更新对应 summary 回归，区分“路线 overlay 可见”和“路线 + 小车位置都可见”两种所见即所得状态。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明 Nav2 发车标签的最小预检口径。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Nav2"`：通过，`29 passed | 131 skipped`。
- `npm --prefix pc-tools/workstation test`：通过，`2 passed (2)`、`375 passed (375)`。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 仍提示现有单 chunk 大于 500 kB。
- 重启本机 `0.0.0.0:7001` workstation API 后，只读 `GET /api/robot-control/summary`：`safe_command_boundary.nav2_goal_label=图上路线和小车位置已显示，等待安全确认`、`nav2_goal_ready=true`、`nav2_goal_blockers=[]`、`map.path_preview_status=path_preview_observed`、`map.robot_pose_status=map_pose_observed`。

## 剩余风险

- 本轮只修只读 summary label，不执行 Nav2 路线、不发 `/cmd_vel`、不证明真实移动。
- live 当前仍显示上次路线结果成功但执行窗口轮速 L/R=`0/0` 未非零；真实完整路线执行需要现场安全确认后显式执行 ROS 模式重跑。
