# Summary 顶层建图启动与验收 Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增建图启动/验收 alias，全部与 `live_closure_summary` 同源：
  - `mapping_acceptance_missing_reasons`
  - `mapping_start_requires_camera_first_frame=true`
  - `mapping_start_requires_lidar_fresh=true`
  - `mapping_start_unblock_plain`
  - `mapping_camera_blocks_start`
  - `mapping_lidar_blocks_start`
  - `mapping_lidar_fresh_readback_ready`
  - `mapping_lidar_fresh_gate_conflict`
  - `mapping_lidar_fresh_gate_status`
  - `mapping_lidar_fresh_next_action_plain`
  - `mapping_lidar_fresh_refresh_sequence`
  - `mapping_lidar_fresh_refresh_sends_motion=false`
  - `mapping_lidar_fresh_refresh_starts_radar_lifecycle=false`
  - `mapping_lidar_fresh_blocks_free_move=false`
  - `mapping_unblock_allows_free_move=true`
  - `fixed_mapping_start_endpoint=/api/robot-control/map/start`
  - `fixed_mapping_preview_endpoint=/api/robot-control/map/preview`
- 同步更新 `RobotControlSummaryResponse` contract、`robotControlSummary.test.ts`、`catalog.test.ts` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts -t "map"`：通过，1 个 test file，5 passed，4 skipped。
- `npm test -- --run test/catalog.test.ts -t "live-summary"`：通过，1 个 test file，1 passed，180 skipped。
- `npm test`：通过，3 个 test files，421 passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，当前监听 PID `21369`。
- 真实只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 顶层读回：
  - `mapping_start_ready=false`
  - `mapping_start_missing_reasons=["camera_first_frame","lidar_fresh"]`
  - `mapping_acceptance_missing_reasons=["camera_first_frame","lidar_fresh","mapping_active","fresh_map_preview"]`
  - `mapping_start_requires_camera_first_frame=true`
  - `mapping_start_requires_lidar_fresh=true`
  - `mapping_camera_blocks_start=true`
  - `mapping_lidar_blocks_start=true`
  - `mapping_lidar_fresh_readback_ready=false`
  - `mapping_lidar_fresh_gate_status=missing`
  - `mapping_lidar_fresh_refresh_sends_motion=false`
  - `mapping_lidar_fresh_refresh_starts_radar_lifecycle=false`
  - `mapping_lidar_fresh_blocks_free_move=false`
  - `mapping_unblock_allows_free_move=true`
  - `fixed_mapping_start_endpoint=/api/robot-control/map/start`
  - `fixed_mapping_preview_endpoint=/api/robot-control/map/preview`

## 剩余风险

- 本轮只修 summary 顶层读数，不启动建图 runtime。
- 当前真实建图仍缺相机首帧；雷达 gate 可能随 live 读回变化，但建图 start 仍需 camera 和 lidar ready 后再由 operator 确认。
- 本轮不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop，也不发布 `/cmd_vel`。
