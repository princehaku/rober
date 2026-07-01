# 现场验收卡雷达贴图读回

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：在现场验收卡 `plain-field-acceptance-wysiwyg` 内新增 `plain-field-acceptance-radar-map-proof`。当当前所见缺口包含雷达地图点时，直接显示雷达 overlay 状态、当前地图点数、来源点数、旧来源点抑制状态和只读刷新下一步。
- `pc-tools/workstation/test/App.test.ts`：补充默认缺雷达点时的 DOM 合同断言，并保护 camera-only 场景不显示雷达贴图读回。
- `docs/product/pc_tools_workstation.md`：同步现场验收卡雷达贴图读回合同。

## 验证结果

- `npm --prefix pc-tools/workstation test -- --run test/App.test.ts`：通过，233 个用例通过。
- `npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`：通过，190 个用例通过。
- `git diff --check`：通过。
- `npm --prefix pc-tools/workstation run lint`：通过。
- `npm --prefix pc-tools/workstation run build`：通过；仅保留既有 Vite chunk size 警告。
- `npm --prefix pc-tools/workstation test -- --run`：通过，423 个用例通过。
- 无运动雷达贴图复验：`POST /api/robot-control/radar/scan-proof/refresh` 返回 `proxy_status=refresh_forwarded`、`robot_control_executed=false`；随后 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=147`、`radar_overlay_source_point_count=174`、`radar_overlay_needs_refresh=false`、`radar_overlay_blocks_wysiwyg=false`、`radar_overlay_blocks_free_move=false`、`robot_control_executed=false`。
- `GET /api/robot-control/summary` 读回 `status=needs_wheel_rerun`，雷达贴图已 loaded，`field_acceptance_wysiwyg_missing_surface_ids=[camera]`，WYSIWYG 只剩相机首帧缺口，刷新链路 `field_acceptance_wysiwyg_refresh_sends_motion=false`。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `57256`；`GET /` 返回 200，`GET /map` 返回 200。重启后 summary 仍读回 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=147`、`field_acceptance_wysiwyg_missing_surface_ids=[camera]`。

## 剩余风险

- 雷达贴图 WYSIWYG 已通过无运动刷新收口；相机仍无首帧，summary 当前仍显示 `needs_wheel_rerun`，完整 Nav2 同窗口 wheel L/R、delivery success、键盘按住轮速和自由移动 latest 仍需要现场安全确认后的真实运动验证。
