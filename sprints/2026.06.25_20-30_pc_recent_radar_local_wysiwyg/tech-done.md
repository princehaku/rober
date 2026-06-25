# 2026.06.25 20:30 PC recent radar local WYSIWYG

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：地图缺少 map-frame 机器人位姿时，只要 summary 仍带最近 `scan_preview_points`，就显示局部雷达点小窗；当前雷达未运行时文案改为 `最近雷达局部点 N 个，雷达未运行，等待地图位置`，避免把历史/最近 scan 误读成实时贴图。
- `pc-tools/workstation/test/App.test.ts`：新增 LiDAR stopped + scan preview 回归，确认局部点可见、地图贴图关闭、坐标口径明确“不贴地图”，且不会自动调用 radar start、manual、Nav2 execute 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步最近雷达局部点 WYSIWYG 口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts -t "recent local radar scan"`：通过，`1 passed / 73 skipped`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test`：通过，`2` 个 test files，`165 passed`。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- PC 7001 只读 summary smoke：`node` 正在监听 `TCP *:7001`；`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `console_status=loaded_fail_closed_summary`、`connection=readable`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_pose=null`、`scan_preview_count=72`、`path_generated=true`、`path_point_count=36`、`path_preview_point_count=36`、`lidar_running=false`。

## 剩余风险

- 本轮只改善最近 scan artifact 在地图视口里的 WYSIWYG 解释，不触发真实雷达启动、NavigateToPose、manual、keyboard、delivery 或 `/cmd_vel`。
- 真实雷达点贴到地图仍需要 map-frame `robot_pose`；当前 7001 summary 仍显示 `robot_pose=null`，所以只能显示局部轮廓。
