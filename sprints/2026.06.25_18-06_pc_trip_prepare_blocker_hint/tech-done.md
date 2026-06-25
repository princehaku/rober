# PC Trip Prepare Blocker Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`准备行程（不发车）` 返回 no-motion planner root cause 时，把 `planner_server_not_active` 翻译成普通提示 `行程服务还没准备好，先点重新定位，或稍后再准备一次。`；普通首屏不暴露 root cause 字段名。
- `pc-tools/workstation/test/App.test.ts`：新增回归测试，确认失败准备只调用 `/api/robot-control/nav2/proof/refresh`，不会执行 Nav2 goal、manual 或 `/cmd_vel`，且普通首屏不出现 `planner_server_not_active/root_causes`。
- `docs/product/pc_tools_workstation.md`：同步记录真实 7001 no-motion 行程准备结果和普通提示边界。

## 验证结果

- 真实 PC 7001 no-motion 行程准备：`POST /api/robot-control/nav2/proof/refresh?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=refresh_forwarded`、`remote_http_status=200`、`robot_control_executed=false`、`hard_dangerous_true_fields=[]`、`non_motion_evidence_actions_observed=["starts_ros2"]`、`path_generated=false`、`path_generation_succeeded=false`、`path_point_count=0`、`root_causes=[planner_server_not_active]`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm test -- App.test.ts -t "translates plain trip preparation planner blocker"`：通过，1 passed / 69 skipped。
- `cd pc-tools/workstation && npm test`：通过，161 tests。
- `cd pc-tools/workstation && npm run build`：通过。
- PC 7001 只读 summary smoke：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`keyboard_control_mode=bounded_repeating_manual_pulse`、`free_roam_autonomy=locked`、`path_generated=false`、`path_generation_succeeded=false`、`path_point_count=0`、`pose=null`。

## 剩余风险

- 真实 no-motion 行程准备仍 blocked 在上位机 planner 服务未 active；完整 Nav2 路线执行未完成。
- 本轮只改善普通首屏对该 blocker 的解释，不自动重新定位、不执行 Nav2 goal、不发手控。
