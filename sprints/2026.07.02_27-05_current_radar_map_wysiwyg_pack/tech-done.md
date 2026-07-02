# 2026.07.02 27-05 Current Radar Map WYSIWYG Pack

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：新增 `current_radar_map_wysiwyg_pack_*` summary 合同，压平雷达贴图 loaded/needs_readback_refresh、点数、恢复端点和完整 no-motion 边界。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从既有 `liveClosureSummary.radar_overlay_*` 生成当前雷达地图 WYSIWYG 包。loaded 时直接说明当前地图雷达点数；未贴图时固定提示只读链路：刷新雷达扫描、读取雷达状态、刷新地图画面、刷新总览。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏新增 `plain-current-radar-map-wysiwyg-pack`，不管雷达贴图已完成还是需要刷新，都能直接读到状态、点数、端点和不会发车/不会启动 runtime 的边界。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖雷达贴图缺失和 loaded 两种状态，锁定只读链路、DOM data 属性和 motion/runtime 边界。
- `docs/product/pc_tools_workstation.md`：同步说明 PC `/map` 大屏、RViz2/Foxglove 工程观察与当前雷达地图 WYSIWYG 包的边界。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed`，`247 passed`。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功；Vite 仍提示既有 chunk size warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 重启 `0.0.0.0:7001` 后只读检查 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，返回 `current_radar_map_wysiwyg_pack_status=loaded`、`current_radar_map_wysiwyg_pack_current_point_count=139`、`current_radar_map_wysiwyg_pack_source_point_count=147`、`current_radar_map_wysiwyg_pack_readback_only=true`、`current_radar_map_wysiwyg_pack_sends_motion_when_clicked=false`、`current_radar_map_wysiwyg_pack_starts_radar_lifecycle=false`、`current_radar_map_wysiwyg_pack_starts_nav2=false`、`current_radar_map_wysiwyg_pack_starts_map_runtime=false`。

## 剩余风险

- 本轮只补 PC 读回与展示，不执行真实 Nav2、manual、keyboard、free-roam、建图、delivery 或 stop。
- 真实摄像头仍需换高速 USB/带供电 Hub 后复测；雷达贴图本轮只验证软件合同和只读现场读回，不替代 HIL 行驶验收。
