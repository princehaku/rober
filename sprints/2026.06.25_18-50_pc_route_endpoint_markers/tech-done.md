# 2026.06.25 18:50 PC route endpoint markers

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏地图把 no-motion planner `path_preview_points` 的首尾点显示成路线端点 marker。有真实执行目标 marker 时只显示 `起点`，没有执行目标时显示 `起点/终点`；端点只代表规划路线首尾，不冒充机器人当前位置。
- `pc-tools/workstation/src/styles.css`：新增路线端点 marker 样式，和既有路线 polyline、目标点、机器人/雷达 marker 同层展示但不参与交互。
- `pc-tools/workstation/test/App.test.ts`：补充两种回归场景，确认有 execution latest 时不重复显示终点，无 execution latest 时显示 no-motion 路线首尾；同时断言不触发 Nav2 execute 或 manual。
- `docs/product/pc_tools_workstation.md`、`docs/navigation/fixed_route_workflow.md`：同步路线端点 WYSIWYG 口径和安全边界。
- `sprints/2026.06.25_18-40_pc_route_path_caption/tech-done.md`：修正上一轮记录中“无路线时显示路线未准备”的描述，当前实现是无路线时不额外显示路线文案。

## 验证结果

- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test -- App.test.ts -t "route"`：通过，`8 passed / 63 skipped`。
- `cd pc-tools/workstation && npm test`：通过，`2 passed` test files，`162 passed` tests。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`path_generated=true`、`path_generation_succeeded=true`、`path_point_count=36`、`path_preview_point_count=36`、`path_preview_source_point_count=36`、`path_preview_frame_id=map`、`robot_pose=null`。

## 剩余风险

- 本轮只做路线端点可视化，不执行 NavigateToPose，不证明真实路线执行、delivery success、底盘运动或 HIL。当前真实 summary 仍是 `robot_pose=null`，因此端点 marker 只表示规划路线首尾，不能作为机器人当前位置。
