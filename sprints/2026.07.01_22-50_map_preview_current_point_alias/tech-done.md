# Map Preview 雷达当前点数 Alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `GET /api/robot-control/map/preview` 顶层新增 `radar_overlay_current_point_count`。
  - 该字段与 `radar_overlay_point_count` / `radar_overlay.count` 同源，表示当前地图画布实际贴出的雷达点数。
- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlMapPreviewResponse` 同步新增 `radar_overlay_current_point_count: number`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 stale overlay 场景：当前点数为 `0`，旧 source 点数仍保留。
  - 覆盖 loaded overlay 场景：当前点数为 `1`，与地图实际贴图点数一致。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 map preview 直连响应也暴露 `radar_overlay_current_point_count`。

## 验证结果

- 已通过：`npm test -- --run test/catalog.test.ts -t "map preview"`，1 file passed，3 tests passed / 178 skipped。
- 已通过：`npm test`，3 files passed，421 tests passed。
- 已通过：`npm run lint`。
- 已通过：`npm run build`，Vite 仍提示单 chunk 超过 500 kB 的既有 warning，构建成功。
- 已通过：`git diff --check`。
- 已重启 PC Node：`http://0.0.0.0:7001`，PID `17821`。
- 已通过只读 live GET：
  - `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回 `radar_overlay_status=not_current`、`radar_overlay_point_count=0`、`radar_overlay_current_point_count=0`、`radar_overlay_source_point_count=181`、`radar_overlay_needs_refresh=true`、`radar_overlay_blocks_wysiwyg=true`、`radar_overlay_blocks_free_move=false`、`robot_control_executed=false`。
  - `GET /api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787` 返回同源 `radar_overlay_current_point_count="0"`、`radar_overlay_source_point_count="181"`，并保持 `free_move_start_ready=true`、地图默认缩放 `150%`。

## 剩余风险

- 本轮只补 map preview 只读字段，不自动刷新雷达、不启动雷达 lifecycle、不执行 Nav2/manual/keyboard/free-roam/建图/delivery/stop，也不发布 `/cmd_vel`。
- 当前 live 雷达贴图仍为 `not_current` 时，需要 operator 手动走 no-motion 刷新链路后再验收地图雷达点所见即所得。
