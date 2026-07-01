# PC 建图 lidar fresh gate alias

sprint_type: micro

## 实际改动

- `live_closure_summary` / `/api/robot-control/live-summary` 增加建图 `lidar_fresh` gate 诊断字段，用于区分“地图雷达贴图已 WYSIWYG”和“建图安全边界仍缺 lidar_fresh”。
- 普通首屏总卡、自由移动/建图提示和建图解锁卡同步暴露这些字段。
- 字段只给 no-motion 复核链路，不自动放行建图，不启动雷达 lifecycle 或任何运动入口。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts -t "separates free movement from mapping sensor readiness"`：通过，1 passed。
- `npm test -- --run test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，1 passed。
- `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 passed。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仍提示既有 bundle size warning。
- `npm test`：通过，3 files / 418 tests passed。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001` 后只读 curl `/api/robot-control/live-summary`：`mapping_lidar_fresh_readback_ready=true`、`mapping_lidar_fresh_gate_conflict=true`、`mapping_lidar_fresh_gate_status=readback_ready_boundary_missing`、`mapping_lidar_fresh_refresh_sequence=["/api/robot-control/radar/scan-proof/refresh","/api/robot-control/radar/status","/api/robot-control/summary"]`、`mapping_lidar_fresh_refresh_sends_motion=false`、`mapping_lidar_fresh_refresh_starts_radar_lifecycle=false`、`mapping_lidar_fresh_blocks_free_move=false`。

## 剩余风险

- 当前不直接把建图改为 ready：`mapping_start_ready=false` 且 `mapping_start_missing_reasons=["camera_first_frame","lidar_fresh"]` 仍来自上车 safe boundary。新字段只证明 PC 已识别“雷达读回 ready 但边界仍缺 lidar_fresh”的冲突。
- 画面仍未 WYSIWYG：`camera_current_visible=false`，相机首帧仍是建图硬缺口。
