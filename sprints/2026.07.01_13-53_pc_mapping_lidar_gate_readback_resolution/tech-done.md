# PC Mapping Lidar Gate Readback Resolution

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`live_closure_summary` 现在区分 raw free-roam boundary 和当前 readback 有效缺口；当 raw boundary 仍含 `lidar_fresh`，但当前 summary 已证明雷达 fresh 且地图雷达 overlay 已加载时，live 的 `mapping_start_missing_reasons` / `free_roam_mapping_start_missing_reasons` 会移除 `lidar_fresh`，同时保留 `mapping_lidar_fresh_gate_conflict=true` 解释原始 gate 尚未同步。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：新增 raw boundary stale、readback fresh 的测试，锁定 live 只剩 `camera_first_frame` 缺口，不再把已满足的雷达新鲜度写进建图启动缺口。
- `docs/product/pc_tools_workstation.md`：同步 live 建图 gate readback 消解合同和 no-motion 边界。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，结果 `1 passed`、`8 passed`。
- 通过：`git diff --check`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 仍提示主 chunk 超过 500 kB，这是既有体积警告，不影响本轮 live gate 消解。
- 通过：`npm test`，结果 `3 passed`、`420 passed`。
- 通过：重启 `HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 Node `*:7001`，日志显示 `pc-tools workstation API listening on http://0.0.0.0:7001`。
- 通过：真实只读 `GET /api/robot-control/live-summary` 返回 `mapping_start_missing_reasons=["camera_first_frame"]`、`free_roam_mapping_start_missing_reasons=["camera_first_frame"]`、`mapping_lidar_blocks_start=false`、`mapping_lidar_fresh_readback_ready=true`、`mapping_lidar_fresh_gate_status=ready`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=34`、`starts_free_roam=false`、`starts_map_runtime=false`、`publishes_cmd_vel=false`。

## 剩余风险

- 本轮只修 PC live 当前事实表达，不执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。
- 如果真实相机仍无首帧，建图启动仍应被 `camera_first_frame` 阻塞；本轮不宣称相机硬件链路恢复。
