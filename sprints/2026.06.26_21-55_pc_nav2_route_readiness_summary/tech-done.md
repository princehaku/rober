# PC Nav2 Route Readiness Summary

- sprint_type: micro

## 实际改动

- PC Robot Control summary 的 `safe_command_boundary` 新增 `nav2_goal_ready`、`nav2_goal_label`、`nav2_goal_blockers`，从只读 Nav2 proof 的路线生成、路线点数量和 map-frame 机器人位姿判断“图上路线可执行/未就绪”。
- 保留 `nav2_goal: "Nav2 NavigateToPose locked"`、`safe_to_control=false`、`primary_actions_enabled=false` 和 `robot_control_executed=false` 的 fail-closed 边界；真正执行图上路线仍必须走固定 Nav2 execute 代理并重新跑 preflight。
- 补充 PC workstation catalog 测试，覆盖默认路线未就绪和 Nav2 proof 已有路线 + AMCL 位姿时的 ready 摘要。
- 同步更新 `docs/product/pc_tools_workstation.md`，说明该字段只改善 PC 端可解释性，不绕过发车前复查。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 105 passed (105)`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍有既有 `Some chunks are larger than 500 kB` warning，本轮无新增构建失败。
- 通过：`git diff --check`
- 通过：PC Node 已重启到 `0.0.0.0:7001`，真实上位机 summary smoke：
  - `robot_api_connection.status=readable`
  - `safe_command_boundary.nav2_goal_ready=true`
  - `safe_command_boundary.nav2_goal_label=图上路线可执行`
  - `safe_command_boundary.nav2_goal_blockers=[]`
  - `safe_to_control=false`
  - `safe_command_boundary.robot_control_executed=false`
  - `readback_summary.nav2.path_generated=true`
  - `readback_summary.nav2.path_point_count=36`
  - `readback_summary.localization.robot_pose_status=map_pose_observed`

## 剩余风险

- 本 micro sprint 只修复 PC summary/诊断可读性，没有真实发送 NavigateToPose；完整路线执行仍需现场确认后用固定 Nav2 execute 代理做 HIL 验证。
- 当前判断依赖上位机只读 proof 已正确暴露 path 和 map-frame robot pose；如果上位机 proof 停留在旧 artifact，PC 端会继续显示对应 blocker。
