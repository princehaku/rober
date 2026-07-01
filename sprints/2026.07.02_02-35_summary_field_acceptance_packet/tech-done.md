# 2026.07.02 02:35 Summary 现场验收包

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlFieldAcceptancePacket` 和 `RobotControlFieldAcceptanceStep`。
  - `RobotControlSummaryResponse` 顶层新增 `field_acceptance_packet` 以及现场脚本常用短 alias。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 从既有 `live_motion_runbook_items`、objective audit、WYSIWYG 和 mapping readback 派生 `field_acceptance_packet`。
  - 包内直接暴露下一步步骤、是否会发车、是否需要现场安全确认、验收端点、缺失证据、WYSIWYG 缺口和建图缺口。
  - 包自身固定 `sends_motion_when_clicked=false`、`starts_nav2_when_clicked=false`、`starts_manual_when_clicked=false`、`starts_free_roam_when_clicked=false`、`starts_map_runtime_when_clicked=false`，只读聚合，不新增控制路径。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖主推荐步骤、ready/blocked step、motion step、验收端点、缺失证据和只读 flags。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 live-summary API 暴露现场验收包 alias。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 summary 顶层 `field_acceptance_*` 合同。

## 验证结果

- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`
  - `Test Files 1 passed (1)`，`Tests 9 passed (9)`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "live-summary"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 180 skipped (181)`。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 3 passed (3)`，`Tests 421 passed (421)`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，新监听 PID 为 `7243`。
- 通过：只读请求 `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`。
  - `field_acceptance_status=needs_wheel_rerun`。
  - `field_acceptance_next_step_id=run_nav2_route`。
  - `field_acceptance_next_step_start_endpoint=/api/robot-control/nav2/goal/execute`。
  - `field_acceptance_next_step_sends_motion=true`。
  - `field_acceptance_next_step_requires_safety_confirm=true`。
  - `field_acceptance_ready_step_ids=run_nav2_route,hold_keyboard,start_free_move`。
  - `field_acceptance_blocked_step_ids=start_mapping_when_sensors_ready`。
  - `field_acceptance_packet.sends_motion_when_clicked=false`、`starts_nav2_when_clicked=false`。
- 通过：无运动雷达贴图刷新复核。
  - `POST /api/robot-control/radar/scan-proof/refresh` 返回 `robot_control_executed=false`、`remote_endpoint=/api/radar/scan-proof/refresh`、`latest_scan_proof_fresh=true`。
  - 首次地图预览仍拒绝旧点：`radar_overlay_status=not_current`、`runtime_scan_stale_for_map_radar_overlay`。
  - 等待 summary 聚合后，雷达 WYSIWYG 恢复：`radar_map_points_visible=true`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=145`，`live_wysiwyg_missing_surface_ids=["camera"]`。

## 剩余风险

- 本轮只增加只读聚合字段，没有执行真实 Nav2、manual、keyboard、free-roam 或建图动作。
- 完整目标仍需现场安全确认后复验：同窗口 wheel raw L/R 非零、delivery success、键盘按住轮速非零、松开停稳、自由移动 latest motion ready。
- 摄像头仍显示 `12M` full-speed/UVC 无帧；建图启动继续被相机首帧阻塞，但不阻塞低速自由移动。
