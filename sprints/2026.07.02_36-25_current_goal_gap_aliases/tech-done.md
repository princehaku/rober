# 当前目标缺口短字段

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增当前目标只读短字段：
  - `current_goal_incomplete_item_ids`
  - `current_goal_incomplete_labels`
  - `current_goal_missing_ids`
  - `current_goal_missing_labels`
  - `current_goal_ready_action_labels`
  - `current_goal_blocked_ids`
  - `current_goal_blocked_labels`
  - `current_goal_mapping_blocked_only_by_camera`
  - `current_goal_free_move_allowed_while_mapping_blocked`
  - `current_goal_camera_only_blocks_mapping_plain`
- 字段全部从 `goal_checklist`、`goal_checklist_summary` 和 `live_closure_summary` 派生，不新增动作、不新增门禁、不自动勾安全确认。
- 同步更新 `RobotControlSummaryResponse` 类型合同和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- test/robotControlSummary.test.ts`
  - 结果：通过，`10 passed`。
- `npm test -- test/catalog.test.ts`
  - 结果：通过，`183 passed`。
- `npm run build`
  - 结果：通过；Vite 仍提示单 chunk 大于 500 kB，这是既有体积警告。
- `git diff --check`
  - 结果：通过，无空白错误。
- 7001 live 只读 summary 验证：
  - Node 监听 `*:7001`，PID `25548`。
  - `current_goal_missing_ids=["camera_wysiwyg","nav2_route_execution","keyboard_continuous_control","free_move","mapping_start"]`。
  - `current_goal_blocked_ids=["camera_wysiwyg","mapping_start"]`。
  - `current_goal_ready_action_labels=["重跑图上行程并复验轮速","键盘连续手控","自由自助移动"]`。
  - `current_goal_mapping_blocked_only_by_camera=true`。
  - `current_goal_free_move_allowed_while_mapping_blocked=true`。
  - `current_goal_camera_only_blocks_mapping_plain="当前建图只差画面首帧；自由移动仍可在安全确认后先做，画面恢复后再启动建图。"`。
  - `sends_motion_when_clicked=false`。

## 剩余风险

- 本轮只补 PC/API 只读字段，不发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实完成完整目标仍需要现场安全确认后的运动验证：Nav2 完整路线、键盘连续手控、自由移动、wheel L/R 非零和 delivery success。
