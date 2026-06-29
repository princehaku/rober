# PC radar status overlay missing reasons

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlRadarStatusResponse` 新增雷达贴图前置缺口字段：
  `radar_scan_required_observations`、`radar_scan_observation_status`、
  `radar_scan_observation_missing_reasons`、`radar_scan_ready_for_map_overlay`、
  `radar_overlay_ready_for_map`、`radar_map_overlay_readiness_status` 和
  `radar_map_overlay_next_action_plain`。
- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/radar/status` 继续保持只读 GET，
  但会把 `scan_once/hz/raw_packet` 三项观测缺口转成顶层可读字段；当雷达 lifecycle running 但
  最新 proof 不 fresh 时，直接显示缺 `scan_once,scan_hz,raw_packet_once`。
- `pc-tools/workstation/test/catalog.test.ts`：补充停止态雷达和 running/incomplete 雷达的合同回归，
  确认 PC 不会把 radar status 误当成地图已贴点，且不会发送任何 POST 或运动请求。
- `docs/product/pc_free_roam_mapping_design.md`：同步记录该只读诊断口径，地图是否真的画点仍以
  `/api/robot-control/map/preview` 同轮 overlay 点数为准。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "radar status proxy"`，
  结果 `2 passed | 166 skipped`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，PID `70142`。
- 通过：只读 live `GET http://127.0.0.1:7001/api/robot-control/radar/status` 返回
  `lifecycle_running=true`、`latest_scan_proof_fresh=false`、
  `radar_scan_observation_status=missing_required_observations`、
  `radar_scan_observation_missing_reasons=scan_once,scan_hz,raw_packet_once`、
  `radar_map_overlay_readiness_status=blocked_missing_scan_observations`、
  `radar_overlay_ready_for_map=false`、`robot_control_executed=false`。
- 通过：只读 live `GET http://127.0.0.1:7001/api/robot-control/map/preview` 返回
  `proxy_status=preview_forwarded`、`radar_overlay_status=not_loaded`、
  `radar_overlay_point_count=0`，并说明没有 fresh 可贴图扫描；`robot_control_executed=false`。

## 剩余风险

- 本轮只增强 PC 只读状态解释，不修复上车端 LiDAR proof 本身。当前真实车仍可能保持
  `lifecycle_running=true` 但缺 `scan_once/hz/raw_packet`，地图 overlay 会继续不贴雷达点。
- 本轮不执行 manual、keyboard、Nav2、free-roam、delivery、stop 或 `/cmd_vel`，所以不提供真车运动证明。
