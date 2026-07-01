# PC 大地图 WYSIWYG 四层状态条

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：在普通地图面板和 `/map` 大地图内新增 `plain-map-wysiwyg-layer-strip`，按当前 PC 画布实际显示拆出地图图像、图上路线、小车位置、雷达点四层状态；雷达旧点、局部点和只有点数都不会冒充“已贴当前图”。
- `pc-tools/workstation/src/styles.css`：新增四层状态条和 chip 样式，让大地图内第一眼能扫到哪些层是真正当前可见。
- `pc-tools/workstation/test/App.test.ts`：补充 DOM 和 CSS 测试，锁定四层状态、固定 no-motion endpoint，以及不启动雷达 lifecycle、建图 runtime、Nav2、manual、keyboard、free-roam 的边界。
- `docs/product/pc_tools_workstation.md`：同步记录大地图四层状态条合同。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，`1 passed | 230 skipped`。第一轮发现可见文案误用“图上路线”触发普通首屏禁词，已改为“图上行程”后复跑通过。
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，`7 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`，Vite 构建通过；仍有既有 chunk size warning。
- 通过：`npm test`，`3 passed / 417 passed`。
- 通过：`git diff --check`。
- 通过：PC Node 已重启并监听 `*:7001`，进程 `node ... src/server/index.ts` PID `75495`；只读 `GET http://127.0.0.1:7001/map` 返回 `200`，加载新 assets `index-DOVlr97a.js` / `index-DmFP1kOw.css`。
- 通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `primary=nav2_route_execution`、`map_current_visible=true`、`radar_map_points_visible=false`、`live_wysiwyg_radar_map_overlay_status=not_current`、`radar_current_points=0`、`radar_source_points=187`、下一步为刷新雷达扫描读数后刷新地图画面；`free_move_start_ready=true`、`mapping_start_ready=false`、`mapping_start_missing_reasons=[camera_first_frame]`。

## 剩余风险

- 本轮只提升地图大屏内的所见即所得读回，不发送任何运动/control POST；真实雷达点贴图仍依赖现场启动/刷新雷达 proof 和 map preview 后复验。
