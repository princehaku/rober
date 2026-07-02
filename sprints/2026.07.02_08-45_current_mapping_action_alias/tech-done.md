# Current Mapping Action Alias

## sprint_type

micro

## 实际改动

- 在 `GET /api/robot-control/summary` 顶层新增 `current_mapping_action_*` 短字段，直接承接 runbook 里的 `start_mapping_when_sensors_ready`。
- 字段固定暴露建图 start/stop/preview/readback/acceptance endpoint、缺口、相机/雷达 ready、是否只差相机、雷达贴图是否所见即所得、是否阻塞自由移动、安全确认与 map runtime 边界。
- 普通首屏“传感器就绪后建图”区域新增 `plain-current-mapping-action` 只读说明：当前建图动作是可启动、只差画面还是待补条件，并明确自由移动不受建图缺口影响。
- 同步更新 TypeScript 合同、PC DOM 测试、catalog summary 测试和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`，3 个 test files、428 个测试通过。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留 Vite chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，PID `5045`；`lsof` 显示 `TCP *:7001 (LISTEN)`。
- 通过：`curl -fsSI http://127.0.0.1:7001/` 和 `/map` 均返回 `200 text/html; charset=utf-8`。
- 通过：重启后 live summary 首轮显示建图缺口为 `camera_first_frame,lidar_fresh`，`current_mapping_action_blocks_free_move=false` 且 `current_mapping_action_free_move_allowed_while_blocked=true`。
- 通过：执行 no-motion 雷达 proof refresh 后，`POST /api/robot-control/radar/scan-proof/refresh` 回包 `readback_only=true`、`no_motion_refresh=true`、`sends_motion_when_clicked=false`、`starts_radar_lifecycle=false`、`starts_map_runtime=false`、`latest_scan_proof_fresh=true`。
- 通过：随后 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、当前雷达点 `155`、来源点 `183`、`radar_overlay_primary_blocked_reason=none`。
- 通过：最终 `GET /api/robot-control/summary` 读回 `current_mapping_action_missing_evidence=["camera_first_frame"]`、`current_mapping_action_camera_ready=false`、`current_mapping_action_radar_ready=true`、`current_mapping_action_only_camera_missing=true`、`current_mapping_action_radar_overlay_wysiwyg_complete=true`、`current_mapping_action_blocks_free_move=false`、`current_mapping_action_free_move_allowed_while_blocked=true`、`radar_overlay_wysiwyg_complete=true`、`live_wysiwyg_missing_surface_ids=["camera"]`。

## 剩余风险

- 本轮只新增当前建图动作的只读合同和 UI 说明，不启动建图、不启动 free-roam、不执行 Nav2/manual/keyboard/delivery/stop，也不发送 `/cmd_vel`。
- live 现场当前相机首帧仍未出图；建图启动仍需相机首帧恢复后再做真实安全确认和 HIL 验证。
