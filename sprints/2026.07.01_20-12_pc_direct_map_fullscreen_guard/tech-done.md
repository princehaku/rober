# PC 直达地图大屏稳定性

sprint_type: micro

## 实际改动

- `/map` 直达地图页在浏览器原生 fullscreen 不可用或收到 `fullscreenchange` 后，仍保持页面内 `fullscreen + 只看地图` 状态。
- `live_closure_summary` / `/api/robot-control/live-summary` 和普通首屏 DOM 增加直达地图大屏兜底字段，明确 `/map` 不依赖浏览器原生 fullscreen API。
- 产品文档同步说明该变化只影响显示，不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime 或任何运动入口。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts -t "minimal precheck fields for same-window wheel rerun"`：通过，1 passed。
- `npm test -- --run test/catalog.test.ts -t "workstation live-summary route exposes a flat read-only current card for field curl checks"`：通过，1 passed。
- `npm test -- --run test/App.test.ts -t "opens direct map view|renders Robot Control V1 by default"`：通过，2 passed。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仍提示既有 bundle size warning。
- `npm test`：通过，3 files / 418 tests passed。
- `git diff --check`：通过。
- 重启 PC Node 到 `0.0.0.0:7001` 后只读 curl `/api/robot-control/live-summary`：`map_display_primary_tool=pc_big_map`、`map_display_primary_url=/map`、`map_display_direct_map_keeps_page_fullscreen_without_browser_api=true`、`map_display_direct_map_browser_fullscreen_required=false`、`map_display_wysiwyg_overlays=["image","route","robot","radar"]`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`radar_overlay_status=loaded`、`free_move_start_ready=true`。

## 剩余风险

- 真实相机首帧仍是当前建图缺口：`mapping_start_ready=false` 且 `mapping_start_missing_reasons=["camera_first_frame"]`。自由移动已可先做，但建图需要换高速 USB 链路后 no-motion 复测相机首帧。
- 本轮未执行任何运动/control POST，也未触发 ROS2/RViz2/Foxglove、Nav2 或建图 runtime。
