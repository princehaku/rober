# PC 雷达卡承接地图雷达下一步

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 中新增雷达卡下一步提示。
- 当地图雷达 overlay 为 `not_current`，且后端给出 `start_radar_then_refresh_map_preview` 时，雷达卡直接显示“雷达下一步：先点启动雷达，再刷新地图画面；旧雷达点不会贴到当前地图”。
- 保持该提示为只读说明，不自动启动雷达、不刷新地图、不发送任何底盘或 Nav2 控制。
- 在 `pc-tools/workstation/test/App.test.ts` 的 stopped/stale 雷达 overlay 场景中补断言，确保地图卡、建图事实行和雷达卡使用一致的下一步口径。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "honors not-current map radar overlay summary"` 通过：1 test passed。
- `npm --prefix pc-tools/workstation test` 通过：2 files passed, 368 tests passed。
- `npm --prefix pc-tools/workstation run build` 通过；仅保留 Vite chunk size 既有警告。
- 只读查询 `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 通过，现场为 `lidar.lifecycle=stopped`、`lidar.runtime_scan_status=stale`、`lidar.radar_start_configured=true`、`map.radar_overlay_status=not_current`、`map.radar_overlay_next_action=start_radar_then_refresh_map_preview`。

## 剩余风险

- 本轮没有现场安全确认，也没有执行雷达启动、地图刷新、自由移动、键盘手控、底盘手控或 Nav2 执行。
- 雷达点仍需要现场触发启动并刷新地图画面后，才能完成“雷达开始后地图标记所见即所得”的真实闭环。
- 摄像头首帧仍为 `uvc_no_frame_not_exclusive`，建图验收仍缺画面首帧、雷达新鲜、地图记录和新鲜地图画面。
