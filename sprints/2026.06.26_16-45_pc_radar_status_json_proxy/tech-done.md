# PC 雷达状态只读 JSON 代理

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 新增 `GET /api/robot-control/radar/status` 固定只读代理。
  - 该入口只转发到上位机 `/api/radar/status`，不调用雷达 start/stop、不触发底盘或建图动作。
  - 返回 `radar_key_values` 短摘要，并保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
  - `radar_key_values` 覆盖 `scan_status`、`continuous_scan_status`、`continuity_window_status`、`latest_scan_proof_fresh` 等雷达 WYSIWYG 所需关键字段。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlRadarStatusResponse` contract，并把新入口加入 `API_ROUTES`。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 `getRobotControlRadarStatus` typed helper，给后续地图雷达 marker 接入复用。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新默认只读小车地址测试，确保不传 `baseUrl` 时也会固定读取 `http://192.168.1.11:8787/api/radar/status`。

## 验证结果

- `npm test`：通过，2 个 test files，219 个 tests passed。
- `npm run build`：通过；Vite 仍提示单 chunk 大于 500 kB 的既有 warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 7001 真机只读 smoke：通过。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node ... TCP *:7001 (LISTEN)`。
  - `GET /api/robot-control/radar/status?baseUrl=http://192.168.1.11:8787` 返回 `Content-Type: application/json; charset=utf-8`、`proxy_status=status_loaded`、`remote_http_status=200`。
  - 同一响应返回 `scan_status=fresh_scan_proof_observed`、`continuous_scan_status=latest_proof_stale_while_lifecycle_running`、`continuity_window_status=latest_proof_stale_while_lifecycle_running`、`latest_scan_proof_fresh=false`、`robot_control_executed=false`。
  - `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `free_roam_autonomy_start_ready=true`、`keyboard_control_mode=bounded_repeating_manual_pulse`，且 lidar readback 与 radar status 的 stale 状态一致。

## 剩余风险

- 本轮只补 PC 雷达状态 JSON 入口，尚未把该入口直接接入地图上的实时雷达 marker。
- 真机当前雷达 lifecycle 在跑，但 continuous/latest proof 显示 stale；下一轮地图 marker 应该直接显示这个 stale 口径，而不是误报“实时贴图”。
