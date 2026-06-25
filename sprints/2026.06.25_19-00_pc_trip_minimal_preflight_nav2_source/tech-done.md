# 2026.06.25 19:00 PC trip minimal preflight Nav2 source

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：PC 后端固定 `nav2/goal/preflight` 不再只依赖 `/api/localize/proof/latest` 判断定位；现在合并 `/api/localize/proof/latest`、`/api/nav2/proof/latest`、`/api/nav2/status`，允许 Nav2 proof/status 中的 AMCL pose、`map_to_base_link` 和路径点证据修正 stale localize latest 的旧失败。
- `pc-tools/workstation/src/shared/contracts.ts`：给 `localization_summary` 增加可选 `source` 字段，便于测试和高级诊断说明定位证据来自 localize 或 Nav2 readback。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `行程操作` 改成最小现场安全确认；雷达状态继续在雷达卡片、地图扫描点和提示里显示，但不再作为 `检查行程` / `执行行程` 的前端硬挡。真正执行仍要求用户勾选安全确认，并由后端 execute gate 复查定位和路线。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：更新回归用例，覆盖 LiDAR 停止、雷达待刷新、雷达未配置时行程按钮仍按安全确认放行；覆盖 localize latest stale 但 Nav2 proof/status 完整时 preflight 通过。
- `docs/product/pc_tools_workstation.md`、`docs/navigation/fixed_route_workflow.md`：同步 PC 普通首屏最小行程确认、Nav2 readback 合并来源和安全边界。

## 验证结果

- `cd pc-tools/workstation && npm test -- App.test.ts -t "lidar"`：通过，`5 passed / 66 skipped`。
- `cd pc-tools/workstation && npm test -- App.test.ts -t "radar"`：通过，`8 passed / 63 skipped`。
- `cd pc-tools/workstation && npm test -- App.test.ts -t "trip"`：通过，`7 passed / 64 skipped`。
- `cd pc-tools/workstation && npm test -- catalog.test.ts -t "Nav2 goal preflight"`：通过，`2 passed / 89 skipped`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test`：通过，`2 passed` test files，`162 passed` tests。
- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
- PC 7001 已重启为本轮代码并监听 `http://0.0.0.0:7001`；`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 只读 smoke 返回 `console_status=loaded_fail_closed_summary`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`lidar_lifecycle_running=false`、`lidar_lifecycle_state=stopped`、`latest_scan_proof_fresh=false`。
- PC 7001 固定 no-motion 预检：`POST /api/robot-control/nav2/goal/preflight?baseUrl=http://192.168.1.11:8787`，body 为 `goal_frame_id=map,x=0.8,y=0,yaw=0,confirm_navigation_preflight=true`，返回 `proxy_status=preflight_passed`、`robot_control_executed=false`、`missing_requirements=[]`、`localization_summary.source=localize_or_nav2_proof_latest`、`localization_reset_observed=false`、`nav2_no_motion_localization_runtime_observed=true`、`map_to_base_link=true`、`path_generated=true`、`path_generation_succeeded=true`、`path_point_count=36`，并声明未调用 `/api/nav2/start`、`NavigateToPose`、`/cmd_vel`、`/api/base/manual`。

## 剩余风险

- 本轮只改 PC UI/后端 gate 和本地测试；没有触发真实 NavigateToPose、`/api/base/manual`、keyboard pulse、delivery complete 或 `/cmd_vel`。
- PC 7001 已证明固定预检通过，但这不是完整路线执行；真实发车仍需 operator 在 PC 首屏显式点击 `执行行程`，并由后端 execute gate 再次复查定位和路线。
