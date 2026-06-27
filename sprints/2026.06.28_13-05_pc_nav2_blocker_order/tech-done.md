# 2026-06-28 13:05 PC Nav2 blocker order

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `sortNav2GoalBlockers()`，让 `safe_command_boundary.nav2_goal_blockers` 按普通首屏的真实操作顺序输出。
  - 当 Nav2 planner/controller inactive 且路线或 map pose 也未就绪时，结构化 blockers 先列
    `planner_server_inactive/controller_server_inactive`，再列路线生成、路径点和 robot map pose 缺口。
- `pc-tools/workstation/test/catalog.test.ts`
  - 将 live 形态和 partial readback 场景的 `nav2_goal_blockers` 断言收紧为精确顺序。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 blocker 顺序与 `nav2_goal_next_action` 一致：先恢复 Nav2 服务，再处理路线和定位读数。

## 验证结果

- `npm test -- test/catalog.test.ts -t "Robot Control summary exposes fail-closed safe command boundary|Robot Control summary returns partial readbacks when the HTTP first-screen budget is shorter than slow camera health|Robot Control summary tells the operator to rerun ROS Nav2 when PWM success lacks wheel raw L/R"`：通过，2 个匹配用例通过、144 个跳过。
- `npm test`：通过，2 个 test file、333 个测试全部通过。
- `npm run lint`：通过。
- `npm run build`：通过；首次 build 暴露 `Map` literal union 窄类型问题，修正为 `Map<string, number>` 后通过。Vite 仍提示单个 chunk 超过 500 kB，这是既有前端体积 warning。
- `git diff --check`：通过。
- 重启本机 PC Node 到 `0.0.0.0:7001`：通过，`lsof` 显示 `node` 监听 `TCP *:7001`。
- 只读检查 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，
  `nav2_goal_blockers=["planner_server_inactive","controller_server_inactive","path_generation_not_observed","path_point_count_not_positive","robot_map_pose_not_observed"]`，
  与 `nav2_goal_next_action` 的“先恢复 Nav2 planner/controller，再生成图上路线并读到小车地图位置”顺序一致。

## 剩余风险

- 本轮只调整 PC summary 的只读 blocker 顺序，不恢复真实 Nav2 planner/controller，不执行 Nav2 goal，不发送 `/cmd_vel` 或底盘 manual。
- live 完整路线仍需要现场安全确认后恢复 Nav2 服务、生成图上路线、读到小车 map 坐标，并用建议模式重跑后复验同窗口 wheel raw L/R 非零。
