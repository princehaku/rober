# 2026.06.30 17:10 PC radar map DOM evidence

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图视图新增雷达贴图结构化 DOM 证据：`data-radar-map-points-visible`、`data-radar-map-point-count`、`data-radar-map-source-point-count`、`data-radar-map-frame-id`、`data-radar-map-source`、`data-radar-map-overlay-status`、`data-radar-local-point-count`、`data-radar-not-current-source-point-count`、`data-radar-count-only-point-count` 和 `data-fixed-radar-map-preview-endpoint`。
  - 同一组关键贴图事实同步绑定到地图雷达 marker、地图雷达点 SVG 和局部雷达点 SVG，避免脚本只能解析中文 caption。
  - `data-radar-map-points-visible=true` 只在当前地图实际画出地图雷达点时出现；旧来源点、仅点数、局部轮廓或距离读数仍保持 false。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定默认首屏没有地图雷达点时 `data-radar-map-points-visible=false`、点数为 0、frame 为 `not_loaded`。
  - 锁定雷达启动后同轮地图预览返回 2 个地图雷达点时，地图卡、marker 和 SVG 都暴露 `data-radar-map-points-visible=true`、点数 2、source `map_preview`、frame `laser_frame`。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步地图雷达贴图 DOM 验收口径。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`。
- 已通过：`cd pc-tools/workstation && npm test -- test/App.test.ts -t "auto-refreshes radar proof after plain radar start reports ok"`。
- `cd pc-tools/workstation && npm test -- --run`
  - 通过：`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `cd pc-tools/workstation && npm run build`
  - 通过：Vite build 成功；保留既有 `Some chunks are larger than 500 kB after minification` warning。
- `git diff --check`
  - 通过：无 whitespace error。
- 7001 live 只读 HTTP smoke
  - 已重启：`npm run api -- --host 0.0.0.0 --port 7001`，`lsof` 显示 `TCP *:7001 (LISTEN)`。
  - `GET http://127.0.0.1:7001/` 返回当前构建产物：`index-BwAtAbmx.js` 与 `index-BZI7zFw0.css`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 HTTP 200，`schema=trashbot.pc_tools_workstation.robot_control_summary.v1`，`radar_status=not_current`，`radar_wysiwyg=old_or_missing_points_not_drawn`，`card_count=7`。
  - 当前 JS 产物可匹配 `data-radar-map-points-visible`、`data-radar-map-point-count`、`data-radar-map-frame-id`、`data-radar-not-current-source-point-count` 和 `data-fixed-radar-map-preview-endpoint`。

## 剩余风险

- 本轮只补 PC Web DOM 证据，不启动雷达、不刷新地图、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实雷达贴图仍需要现场上位机返回同轮 `/api/robot-control/map/preview` 雷达点才能证明；本轮验证覆盖的是前端消费和 DOM 合同。
