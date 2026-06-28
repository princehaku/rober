# sprint_type: micro

## 实际改动

- PC 普通地图区新增 `plain-map-radar-next-action` 提示，专门解释地图雷达 overlay 的下一步动作。
- 当后端 `readback_summary.map.radar_overlay_next_action=start_radar_then_refresh_map_preview` 时，普通地图区显示：
  - `地图下一步：先启动雷达，再刷新地图画面；旧雷达点不会贴到当前地图。`
- 当后端要求先刷新定位或刷新地图预览时，也转成普通用户可执行文案。
- 本轮只改地图/雷达所见即所得提示，不自动启动雷达、不发底盘运动、不执行 Nav2、不确认送达。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "honors not-current map radar overlay summary"`：通过，1 passed。
- `npm --prefix pc-tools/workstation test`：通过，367 passed。
- `npm --prefix pc-tools/workstation run build`：通过，Vite 仍提示现有 chunk 大于 500 kB 的非阻塞 warning。
- 只读 live `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`：通过，返回 `radar_overlay_status=not_current`、`radar_overlay_plain_hint=已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。`、`radar_overlay_next_action=start_radar_then_refresh_map_preview`、`radar_overlay_scan_preview_point_count=0`、`radar_overlay_scan_preview_source_point_count=81`；同时 LiDAR 为 `lifecycle_running=false`、`lifecycle_state=stopped`、`runtime_scan_status=stale`，camera 为 `uvc_no_frame_not_exclusive` 且 `shared_preview_exclusive_camera_claim=false`。

## 剩余风险

- 本轮没有现场安全确认，因此没有启动雷达、没有移动小车、没有执行 Nav2；只是让普通 PC 地图区把 live 的下一步明确展示出来。
- live 当前雷达未运行，地图只允许显示“旧点不贴图”的事实；要看到实时雷达标记，需要现场启动雷达并刷新地图预览。
- live 当前相机仍是 UVC 无首帧且非独占；建图 ready 仍缺相机首帧、实时雷达、地图记录等现场证据。
