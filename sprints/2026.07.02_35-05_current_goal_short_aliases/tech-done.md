# 当前目标进度短字段

sprint_type: micro

## 实际改动

- 在 PC workstation summary 顶层新增 `current_goal_*` 短字段，直接暴露本轮目标状态、完成数、剩余数、进度、下一步动作、ready/blocked action id 列表和 no-motion 边界。
- 在普通 PC `plain-objective-overview` DOM 同步暴露 `data-current-goal-*`，旧 summary 缺字段时从 `goal_checklist_summary` 兼容回退。
- 更新 TypeScript contract、App DOM 测试、catalog summary 测试和 PC 产品文档，确保现场脚本不再读到 `current_goal_done_count/current_goal_next_action_id` 为空。

## 验证结果

- 通过：`npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 passed / 236 skipped。
- 通过：`npm test -- test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`，1 passed / 182 skipped。
- 通过：`npm test -- test/catalog.test.ts`，183 passed。
- 通过：`npm run build`。Vite 仍提示已有 bundle size warning，但 TypeScript 和构建均通过。
- 通过：`git diff --check`。
- 通过：重启本地 workstation 到 `0.0.0.0:7001`，PID `68332` 监听 `*:7001`。
- 通过：只读 `curl http://127.0.0.1:7001/api/robot-control/summary` 显示：
  - `current_goal_status=in_progress`
  - 初次读回 `current_goal_done_count=1`、`current_goal_remaining_count=6`
  - `current_goal_next_action_id=nav2_route_execution`
  - `current_goal_ready_action_ids=[nav2_route_execution, keyboard_continuous_control, free_move]`
  - `current_goal_blocked_action_ids=[camera_wysiwyg, radar_map_points_wysiwyg, mapping_start]`
  - `current_goal_sends_motion_when_clicked=false`
- 通过：只读执行 `POST /api/robot-control/radar/scan-proof/refresh`，响应边界保持 `robot_control_executed=false`、`safe_to_control=false`、`sends_motion_when_clicked=false`、`starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、`starts_map_runtime=false`。
- 通过：雷达刷新后 summary 显示 `current_radar_map_wysiwyg_pack_status=loaded`、`current_radar_map_wysiwyg_pack_missing_evidence=[]`、当前雷达地图点 `5` 个、来源点 `6` 个；`live_wysiwyg_missing_surface_ids=[camera]`，目标进度更新为 `current_goal_done_count=2`、`current_goal_remaining_count=5`。

## 剩余风险

- 本轮只补目标进度读回和页面 DOM，不执行真实运动；Nav2 路线、键盘连续手控、自由移动仍需要现场安全确认后的 HIL 验收。
- 当前 WYSIWYG/建图仍受相机首帧缺口影响；雷达贴图已通过只读刷新恢复为 loaded。
