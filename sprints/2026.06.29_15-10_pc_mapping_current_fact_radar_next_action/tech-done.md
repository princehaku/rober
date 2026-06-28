# PC 建图当前事实雷达下一步提示

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 中把地图雷达 overlay 的 `not_current` 下一步同步到首屏“当前事实”的建图行。
- 当雷达旧点不贴当前地图，且后端给出 `start_radar_then_refresh_map_preview` 时，首屏当前事实会直接显示“自由移动不受影响；建图下一步：先启动雷达，再刷新地图画面”。
- 在 `pc-tools/workstation/test/App.test.ts` 的 stopped/stale 雷达 overlay 场景中补断言，确保当前事实行和建图 readiness 卡使用同一下一步口径，并继续不触发雷达启动、底盘手控、Nav2 或 `cmd_vel`。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "honors not-current map radar overlay summary|live stale scan age"` 通过：1 test passed。
- `npm --prefix pc-tools/workstation test` 通过：2 files passed, 368 tests passed。
- `npm --prefix pc-tools/workstation run build` 通过；仅保留 Vite chunk size 既有警告。
- 只读查询 `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 通过，现场为 `map.radar_overlay_status=not_current`、`map.radar_overlay_next_action=start_radar_then_refresh_map_preview`、`free_roam.status=start_ready`、`free_roam.mapping_ready=false`。

## 剩余风险

- 本轮没有现场安全确认，因此没有启动雷达、自由移动、键盘手控、底盘手控或 Nav2 执行。
- 当前建图仍缺相机首帧、雷达新鲜、地图记录和新鲜地图画面；本轮只把下一步在首屏当前事实里显式前置。
- 摄像头源仍需 USB、输入、供电或 known-good UVC 复测；雷达需要现场确认后启动并刷新地图画面。
