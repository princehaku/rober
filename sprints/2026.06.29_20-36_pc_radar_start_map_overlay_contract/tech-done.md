# PC radar start 后地图贴图验收合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：`POST /api/robot-control/radar/start|stop` 响应新增：
  - `sensor_lifecycle_only=true`
  - `map_preview_endpoint=/api/robot-control/map/preview`
  - `post_start_map_preview_required`
  - `radar_overlay_wysiwyg_status_plain`
  - `radar_overlay_wysiwyg_next_action_plain`
- `pc-tools/workstation/src/shared/contracts.ts`：同步固定 radar lifecycle response contract。
- `pc-tools/workstation/test/catalog.test.ts`：补充 radar start/stop 固定代理的地图贴图验收字段断言，确保启动雷达不会被误认为地图已出现雷达点。
- `docs/product/pc_free_roam_mapping_design.md`：记录 radar lifecycle 与地图 overlay 的验收边界：启动只证明传感器 lifecycle 请求已转发，地图雷达标记必须以后续 map preview 的 `radar_overlay_*` 字段为准。

## 验证结果

- `npm run build`：通过。
- `npm test -- catalog.test.ts`：通过，`167 passed`。
- `npm test -- App.test.ts`：通过，`218 passed`。
- `git diff --check`：通过。
- 重启 PC Node：`HOST=0.0.0.0 PORT=7001 ROBOT_CONTROL_DEFAULT_BASE_URL=http://192.168.1.11:8787 npm run api`，监听 `*:7001`，PID `62216`。
- live 非运动验证 `POST http://127.0.0.1:7001/api/robot-control/radar/start`：
  - `proxy_status=lifecycle_forwarded`
  - `command_result.executed=true`
  - `command_result.ok=true`
  - `sensor_lifecycle_only=true`
  - `post_start_map_preview_required=true`
  - `map_preview_endpoint=/api/robot-control/map/preview`
  - `robot_control_executed=false`
  - `safe_to_control=false`
  - `delivery_success=false`
- live 只读验证 `POST http://127.0.0.1:7001/api/robot-control/radar/scan-proof/refresh`：
  - `proxy_status=refresh_forwarded`
  - `last_result_status=refreshed`
  - `latest_proof_status=raw_packets_parsed`
  - `scan_once_observed=false`
  - `scan_hz_observed=false`
  - `raw_packet_once_observed=false`
  - `lifecycle_running=true`
  - `latest_scan_proof_fresh=false`
  - `robot_control_executed=false`
- live 只读验证 `GET http://127.0.0.1:7001/api/robot-control/map/preview`：
  - `path_preview_status=path_preview_observed`
  - `path_preview_point_count=18`
  - `robot_pose_status=map_pose_observed`
  - `radar_overlay_status=not_loaded`
  - `radar_overlay_point_count=0`
  - `radar_overlay_wysiwyg_status_plain=地图雷达点未加载：当前显示 0 个点；来源点 0 个。地图雷达层未加载：雷达扫描已过期、没有可贴图的新雷达点。`

## 剩余风险

- 雷达 lifecycle 已可启动，但当前 scan proof 仍缺 `scan_once/scan_hz/raw_packet_once`，所以地图雷达点仍不能显示为当前点。
- 本轮没有发送底盘、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；只启动传感器 lifecycle 并刷新非运动 proof。
- 目标里的“雷达开始后地图标记所见即所得”仍未完成为 `loaded`，但现在 start 响应和 map preview 都明确把验收口径固定到 `radar_overlay_status/point_count`，不会把 lifecycle success 冒充成地图有点。
