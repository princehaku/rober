# PC 雷达贴图 overlay 状态读回

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`live_closure_summary` 新增 `live_wysiwyg_radar_map_overlay_status` 和 `live_wysiwyg_radar_map_current_vs_source_plain`，让当前地图雷达状态不再只靠点数推断。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 聚合从 map/radar readback 读取 `radar_overlay_status`，生成“当前点 / 来源点 / 状态 / 下一步”的普通用户文案。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏当前卡点和 `plain-live-radar-map-readback` 暴露 `data-radar-map-overlay-status`、`data-radar-map-current-vs-source-plain`，可见文案直接显示 `状态=not_current`。
- `pc-tools/workstation/test/App.test.ts`：补充 DOM 合同断言，覆盖状态、当前/来源点数对照和 no-motion 边界。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`：同步记录雷达贴图 WYSIWYG 读回口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，7 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 仍提示既有 bundle size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，PID `94230`；`HEAD http://127.0.0.1:7001/map` 返回 `200`。
- 通过：只读 live summary `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `live_wysiwyg_radar_map_overlay_status=not_current`、`live_wysiwyg_radar_map_current_point_count=0`、`live_wysiwyg_radar_map_source_point_count=187`、`live_wysiwyg_radar_map_stale_source_points_suppressed=true`，`live_wysiwyg_radar_map_current_vs_source_plain` 明确写出“当前 0 个，来源 187 个；状态=not_current，旧来源点已抑制，未贴到当前地图”。

## 剩余风险

- 本轮只改 PC 只读读回和 DOM 合同，不启动真实雷达、不发车、不执行 Nav2、不验证真实传感器贴图恢复。
- live 当前地图可见但雷达点仍未贴到当前地图；要完成真实 WYSIWYG 雷达闭环，仍需现场启动/刷新雷达后刷新地图画面。
