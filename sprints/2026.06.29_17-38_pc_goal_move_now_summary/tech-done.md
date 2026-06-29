# PC 本轮目标可先动摘要

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 `goal_summary` / `goal_checklist_summary` 增加只读字段：`ready_action_count`、`blocked_action_count`、`motion_ready_count`、`sensor_blocker_count`、`move_now_status_plain`、`mapping_blockers_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：按现有 action/checklist 结构化事实推导“当前能不能先动”和“建图缺口”，明确相机和雷达只影响建图验收，不阻止自由移动、键盘连续手控或可重跑的图上行程。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“本轮目标检查”直接显示可先动摘要和建图缺口摘要。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖新增 API 字段和首屏文案。
- `pc-tools/README.md`：同步记录只读合同变化。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`，`166 passed`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`，`217 passed`。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript 与 Vite build 成功，仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：PC Node 重启到 `0.0.0.0:7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`。
- 通过：live 只读 summary 返回 `goal.ready_action_count=3`、`goal.motion_ready_count=3`、`goal.sensor_blocker_count=3`、`ready_action_ids=free_move,keyboard_continuous_control,nav2_route_execution`、`blocked_action_ids=camera_wysiwyg,radar_map_points_wysiwyg,mapping_start`。
- 通过：live 只读 summary 返回 `move_now_status_plain=可先动：自由自助移动、键盘连续手控、完整行程执行；发车前只需现场安全确认；相机和雷达只影响建图验收。`
- 通过：live 只读 summary 返回 `mapping_blockers_plain=建图缺口：画面所见即所得、雷达点贴到地图、传感器就绪后建图；这些缺口不阻止先低速自由移动。`

## 剩余风险

- 本轮只改只读 summary 和普通首屏展示，不触发 manual/keyboard/Nav2/free-roam/delivery/stop 或 `/cmd_vel`，因此不证明真实运动。
- 现场摄像头仍需硬件排查，雷达仍需启动并刷新后才能证明地图雷达点所见即所得。
- 自动驾驶真实移动仍需要现场勾选安全确认后显式执行复验；本轮只证明 PC 摘要不再把相机/雷达误写成移动前置。
