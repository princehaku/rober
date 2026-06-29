# 2026.06.30 11:35 PC Mapping Lidar Lifecycle Gate

sprint_type: micro

## 实际改动

- 修正 `pc-tools/workstation/src/server/robotControlSummary.ts`：建图启动的 `lidar_fresh` gate 不再接受雷达停止前遗留的 free-roam runtime snapshot。
- 当 `/api/radar/status` 明确 `lifecycle_running=false`、`lifecycle_state=stopped` 或 `continuous_scan_status=lifecycle_not_running` 时，即使 runtime snapshot 仍带旧 `lidar_age_s/lidar_min_distance_m`，`free_roam_mapping_start_ready` 也会降为 `false`，缺口为 `lidar_fresh`。
- 保留原有正向能力：雷达 lifecycle 仍在 running 时，free-roam runtime `/scan` 新鲜快照仍可覆盖过期 proof artifact。
- 补充 catalog 回归测试，覆盖 stopped lifecycle + stale runtime snapshot 的 live 形态。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "uses fresh free-roam runtime scan for mapping lidar readiness when proof latest is stale"`，1 passed。
- 通过：`cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "does not treat stale runtime scan as mapping-start lidar readiness when radar lifecycle is stopped"`，1 passed。
- 通过：`cd pc-tools/workstation && npm test -- --run`，2 files / 388 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc` 与 `vite build` 通过；保留既有 bundle size warning。
- 通过：`git diff --check`。
- 通过：PC Node 已重启并监听 `*:7001`。只读 live summary 返回 `radar.status=radar_stopped`、`lidar.lifecycle_running=false`、`lidar.runtime_scan_status=fresh`、`free_roam.mapping_start_ready=false`、`mapping_start_missing=lidar_fresh`、`safe_command_boundary.free_roam_mapping_start_ready=false`、`free_roam_motion_start_ready=true`；`mapping_start` action card 为 `not_ready` 且不发送运动，`free_move` action card 仍为 `start_ready`。

## 剩余风险

- 本轮只修 PC summary 的只读 readiness 口径；真实雷达启动、建图启动和车体自由移动仍需要现场安全确认后由用户显式触发。
