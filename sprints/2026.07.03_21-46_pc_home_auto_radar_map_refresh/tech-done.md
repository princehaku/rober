# PC 首页自动雷达贴图刷新

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通 PC 首页打开后新增 `900ms` 短延迟只读刷新：`radar_scan_proof -> radar_status -> map_preview`。
  - 该链路复用现有 `refreshLiveMapSnapshot()`，不启动雷达 lifecycle、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
  - DOM 合同新增 `data-initial-radar-map-refresh-delay-ms=900`、`data-initial-radar-map-refresh-sequence=radar_scan_proof,radar_status,map_preview`、`data-initial-radar-map-refresh-starts-radar-lifecycle=false`、`data-initial-radar-map-refresh-sends-motion=false`。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖普通首页短延迟雷达贴图刷新合同，避免后续把普通首页退回只读旧 map preview。
- `docs/process/okr_progress_log.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录本轮 live 结果：地图 PNG、机器人位置、Nav2 路线、目标点和雷达点已同轮读回。

## 验证结果

- `npm test -- test/App.test.ts -t "direct map|map display|radar|initial live|plain map|camera" --run`
  - 通过：1 个 test file，81 tests passed / 159 skipped。
- `npm run build`
  - 通过；仅保留既有 Vite chunk size warning。
- 7001 live：
  - 已重启为 `HOST=0.0.0.0 PORT=7001 DEFAULT_ROBOT_API_BASE_URL=http://192.168.1.11:8787 npm run api`，监听 `TCP *:7001`。
  - `GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、默认小车地址 `http://192.168.1.11:8787`。
  - `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=preview_forwarded`、`map_png_data_url_present=true`、`robot_pose_status=map_pose_observed`、`path_preview_point_count=18`、`route_target_visible=true`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=43`、`radar_overlay_source_point_count=43`、`radar_overlay_primary_blocked_reason=none`。
  - `GET /` 和 `GET /map` 均返回 `HTTP 200`。

## 剩余风险

- 地图链路本轮已能证明 PC 端同屏显示地图 PNG、机器人位置、Nav2 路线、目标点和当前雷达点。
- 实时图传仍受 `/dev/video1` DV20 无首帧影响；PC 页面有共享预览和自动 USB recovery，但真实画面仍需摄像头输入/线口/供电或 known-good UVC 复测。
- WASD/底盘仍只证明 motion signal；vendor `T=1001` wheel raw L/R 非零仍未完成。
- 本轮没有执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
