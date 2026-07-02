# WYSIWYG 状态短别名

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- 时间：2026-07-02 17:40 CST

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `live_wysiwyg_status`、`live_wysiwyg_status_plain`、`camera_wysiwyg_status`、`camera_wysiwyg_next_action_plain`、`radar_map_wysiwyg_status`、`radar_map_wysiwyg_next_action_plain` 与 `wysiwyg_status_*` 只读边界短字段，全部复用既有 current WYSIWYG 包。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通 PC 的 `plain-current-wysiwyg-action` 同步暴露 `data-live-wysiwyg-*`、`data-camera-wysiwyg-*`、`data-radar-map-wysiwyg-*` 和 `data-wysiwyg-status-*`。
- `pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：补齐类型和合同测试。
- `docs/product/pc_tools_workstation.md`：同步记录 PC 短别名和只读边界。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，`1 passed`，`10 passed`。
- 通过：`npm test -- test/App.test.ts`，`1 passed`，`237 passed`。
- 通过：`npm run build`。Vite 仍提示既有大 chunk 警告，不影响构建产物。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001`，`/map` 返回 HTTP `200`。
- 通过：只读读取 `/api/robot-control/summary`，现场返回
  `live_wysiwyg_status=only_camera_hardware_action`、`camera_wysiwyg_status=needs_first_frame`、
  `radar_map_wysiwyg_status=loaded`、`current_radar_map_wysiwyg_pack_status=loaded`、
  `live_wysiwyg_missing_surface_ids=[camera]`、`current_wysiwyg_action_sends_motion=false`。
- 通过：只读执行雷达贴图刷新链路，回包保持 `robot_control_executed=false`、`safe_to_control=false`、
  `sends_motion_when_clicked=false`、`starts_nav2=false`、`starts_map_runtime=false`。

## 剩余风险

- 当前改动只增加 PC summary/DOM 别名，不会修复相机 USB `12M` full-speed 导致的首帧缺失；建图仍等待相机首帧。
- 雷达贴图已通过本轮只读刷新恢复为 `loaded`，但后续仍取决于现场最近一次读回结果；短字段不会自动启动雷达 lifecycle、Nav2、建图 runtime 或任何运动控制。
