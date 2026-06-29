# PC Map Card Radar Action Split

## sprint_type

micro

## 实际改动

- 修正 `pc-tools/workstation/src/server/robotControlSummary.ts` 的首屏动作卡：地图画面已显示时，`map_preview.next_action_plain` 不再把“启动雷达/刷新雷达点”当成地图下一步，而是提示继续确认图上路线和小车位置。
- 保留 `radar_map_points` 卡片与 `readback_summary.map.radar_overlay_*` 作为雷达启动、新扫描、贴图 WYSIWYG 的唯一入口，旧雷达来源点仍不会冒充当前地图标记。
- 扩展 `pc-tools/workstation/test/catalog.test.ts`，覆盖地图已显示但雷达点未贴当前图时，地图卡片和雷达卡片的下一步分离。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- Pass: `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "proxies Robot API readback"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "stale stopped radar proof"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test`，2 files passed，379 tests passed。
- Pass: `npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 通过；Vite 仍提示既有 chunk size warning。
- Pass: PC API 已重启到 `0.0.0.0:7001`，监听 PID 69937。
- Pass: 只读 curl `http://127.0.0.1:7001/api/robot-control/summary` 返回 `robot_api_connection.status=readable`、`loaded_count=15`、`failed_count=0`，`map_preview.next_action_plain=地图画面已显示；继续确认图上路线和小车位置，雷达点另看“地图雷达点”。`，`radar_map_points.next_action_plain=先启动雷达并等待新扫描，再刷新地图画面确认雷达点`。
- Pass: 只读 7071 诊断仍返回 `robot_api_port_7071_mismatch_use_8787` 作为首位 blocker，并保持 `safe_to_control=false`、`primary_actions_enabled=false`。

## 剩余风险

- 本轮只修正只读 summary 文案；不启动雷达、不刷新地图、不执行 Nav2、不调用 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 现场仍显示雷达 `radar_stopped`、相机 `source_first_frame_failed`；雷达贴图和建图仍需先补新雷达扫描与相机首帧。
