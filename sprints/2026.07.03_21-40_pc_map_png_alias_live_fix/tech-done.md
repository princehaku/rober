# PC map PNG alias live fix

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlMapPreviewResponse` 新增 `map_png_data_url` 字段，作为 `image_data_url` 的同值别名。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：`/api/robot-control/map/preview` 在成功和 fail-closed 响应中都返回 `map_png_data_url`；成功时与 `image_data_url` 完全相同。
- `pc-tools/workstation/test/catalog.test.ts`：增加 map preview alias 断言，防止现场脚本再次因为只检查 `map_png_data_url` 误判地图 PNG 不存在。
- `docs/process/okr_progress_log.md`、`docs/product/pc_tools_workstation.md`：同步记录本轮 live 事实和字段口径。

## 验证结果

- `npm test -- test/catalog.test.ts -t "map preview|map lifecycle" --run`
  - 通过：1 个 test file，7 tests passed / 181 skipped。
- `npm run build`
  - 通过；仅保留既有 Vite chunk size warning。
- 7001 live：
  - 已重启为 `HOST=0.0.0.0 PORT=7001 DEFAULT_ROBOT_API_BASE_URL=http://192.168.1.11:8787 npm run api`，监听 `TCP *:7001`。
  - `GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、默认小车地址 `http://192.168.1.11:8787`。
  - `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=preview_forwarded`、`width=261`、`height=113`、`image_data_url_present=true`、`map_png_data_url_present=true`、`aliases_equal=true`。
  - 同一响应返回 `robot_pose_status=map_pose_observed`、`path_preview_point_count=18`、`route_target_visible=true`、`route_target={x:0.8,y:0.05,frame_id:map,source:path_preview_points,source_index:17}`。
  - `GET http://127.0.0.1:7001/map` 返回 `HTTP 200`。

## 剩余风险

- 当前地图 PNG、机器人位置、Nav2 路线和目标点已经能在 PC map preview 合同中直接证明；本轮没有改变 UI 布局。
- 雷达 overlay 仍为 `radar_overlay_status=not_current`、当前点数 `0`；旧来源点因 runtime scan stale 被抑制。下一步需要刷新雷达扫描后再刷新地图画面，确认雷达点贴到当前地图。
- 本轮没有执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
