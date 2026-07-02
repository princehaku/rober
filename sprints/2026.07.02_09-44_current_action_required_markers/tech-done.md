# Current Action Required Markers

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 修正 `current_motion_action_required_success_markers`：现在返回完整 Nav2 行程验收清单 `map_route_visible,nav2_goal_succeeded,same_window_wheel_lr_nonzero,delivery_success`，不再错误复用当前 missing evidence。
  - 修正 `current_keyboard_action_required_success_markers`、`current_free_move_action_required_success_markers`、`current_mapping_action_required_success_markers` 以及对应短 alias，让 required markers 表示完整验收标准，missing evidence 只表示当前缺口。
  - 当前 live 场景下 mapping required markers 保留 `camera_first_frame,lidar_fresh`，missing evidence 仍可只剩 `camera_first_frame`，避免把“雷达已完成”误读成建图验收标准降低。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 更新当前运动动作断言，确认 required markers 与 missing evidence 分离。
- `docs/product/pc_tools_workstation.md`
  - 同步产品合同：required success markers 是完整验收清单，missing evidence 才是当前缺口。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts`，1 个 test file、10 个测试通过。
- 先失败后修复：`cd pc-tools/workstation && npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts` 第一次失败于 `catalog.test.ts` 仍按旧合同断言 `current_motion_action_required_success_markers == trip_missing_evidence`；已改为对齐 `trip_execution_required_success_markers`。
- 通过：`cd pc-tools/workstation && npm test -- --run catalog.test.ts robotControlSummary.test.ts`，2 个 test files、191 个测试通过。
- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`，3 个 test files、428 个测试通过。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript 与 Vite build 通过，仅保留既有 Vite chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，listener PID `42391`。
- 通过：live `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `current_motion_action_required_success_markers=["map_route_visible","nav2_goal_succeeded","same_window_wheel_lr_nonzero","delivery_success"]`、`current_motion_action_missing_evidence=["same_window_wheel_lr_nonzero","delivery_success"]`、`current_mapping_action_required_success_markers=["camera_first_frame","lidar_fresh"]`、`current_mapping_action_missing_evidence=["camera_first_frame"]`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=6`。

## 剩余风险

- 本轮只修正 PC summary/DOM 可读合同，不执行 Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。
- 完整目标仍未完成：真实完整 Nav2 路线执行、wheel raw L/R 非零、delivery success、键盘连续手控、相机首帧和真实建图启动还需要继续现场验证。
