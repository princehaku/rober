# Safety Confirm Queue Focus

## sprint_type

micro

## 实际改动

- 在 PC workstation summary 的 `current_safety_confirm_queue_*` 中新增 primary focus 字段：`primary_focus_source_card_id`、`primary_focus_kind`、`primary_focus_button_label` 和 `next_action_plain`。
- 在普通用户 PC 首页 `plain-current-safety-confirm-queue` 上新增对应 DOM 属性和 `plain-current-safety-confirm-queue-go-primary` 按钮。
- 该按钮只聚焦第一项动作卡片（当前为 Nav2 行程安全确认），固定不发车、不启动 Nav2/manual/keyboard/free-roam/建图/delivery/stop。
- 更新 summary 与 App 单测，固定该按钮的 focus-only/no-motion 边界。
- 更新 `docs/product/pc_tools_workstation.md`，同步说明队列按钮只跳转到第一项动作卡片。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，10 tests passed。
- 通过：`npm test -- test/App.test.ts`，237 tests passed。
- 通过：`npm run build`，TypeScript 与 Vite build 均完成；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001`，新 PID `76934`。
- 通过：只读读取 `/api/robot-control/summary`，现场返回 `current_safety_confirm_queue_status=ready_for_safety_confirm`、`current_safety_confirm_queue_primary_action_id=run_nav2_route`、`current_safety_confirm_queue_primary_focus_source_card_id=nav2_route`、`current_safety_confirm_queue_primary_focus_kind=trip_safety_confirm`、`current_safety_confirm_queue_primary_focus_button_label=去勾行程安全确认`、`current_safety_confirm_queue_sends_motion_when_clicked=false`、`current_safety_confirm_queue_auto_runs=false`、`current_radar_map_wysiwyg_pack_status=loaded`、`current_goal_free_move_allowed_while_mapping_blocked=true`。

## 剩余风险

- 本轮不发送真实运动命令；Nav2、键盘连续手控、自由移动仍需现场人员勾安全确认后手动执行并读回复验。
- 建图仍受相机首帧阻塞；自由移动仍可先做。
