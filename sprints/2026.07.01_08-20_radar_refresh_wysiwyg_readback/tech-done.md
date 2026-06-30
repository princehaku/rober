# 雷达刷新回包与地图贴图所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 延长固定 no-motion radar proof refresh 后的 latest 复读窗口，避免上车 artifact 比 HTTP refresh 回包稍晚落盘时误报 stale。
  - `radarScanProofReadbackPayload()` 兼容上车 `/api/radar/scan-proof/latest` 的 `latest_result.proof` 嵌套结构，把 `scan_once_observed`、`scan_hz_observed`、`raw_packet_once_observed`、`tf_observed` 和 `latest_scan_proof_fresh` 提升到 refresh 回包顶层。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC radar refresh 代理合同：按钮回包要表达最新 proof readback，地图是否画点仍以同轮 `map/preview.radar_overlay_status` 和点数为准。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "radar.*refresh|scan-proof|reads fast endpoints|Robot Control summary proxies Robot API"`，1 file passed，5 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，PID `81483`。
- 通过：现场只读 `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=refresh_forwarded`、`remote_http_status=200`、`latest_scan_proof_fresh=true`、`scan_once_observed=true`、`scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`、`robot_control_executed=false`、`safe_to_control=false`。
- 通过：现场只读 summary 返回 `robot_api_connection.status=readable`，`radar_map_points.completed=true`，`radar_overlay_status=loaded`，地图当前显示雷达点 `72` 个，`radar.latest_scan_proof_fresh=true`。

## 剩余风险

- 本轮只刷新 no-motion 雷达 proof 和地图预览，不执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`。
- 相机首帧仍失败，建图启动仍缺 `camera_first_frame`。
- 完整 Nav2 行程仍待现场安全确认后重跑 ROS 模式，并复验同窗口 wheel L/R 非零和 delivery success。
