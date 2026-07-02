# Tech Done

sprint_type: micro

## 实际改动

- `GET /api/robot-control/map/preview` 顶层新增 `radar_overlay_wysiwyg_complete`，由同源 `radar_overlay_status/count` 派生；现场脚本可以直接判断雷达点是否贴到当前地图，不再把缺失字段读成 `null`。
- `POST /api/robot-control/radar/scan-proof/refresh` 新增 `next_action_plain`，只指向固定读回链路 `radar/status -> map/preview`，明确 refresh 本身不启动雷达 lifecycle、不发车、不启动 Nav2/建图。
- 更新契约、builder、回归测试和产品文档，保持地图雷达 WYSIWYG 直连读回与 summary 口径一致。

## 验证结果

- `npm test -- test/catalog.test.ts`：通过，`183 passed`。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过，无空白错误。
- 已重启 PC 服务到 `0.0.0.0:7001`，进程 PID `69283`。
- Live 只读复验：
  - `GET /api/robot-control/map/preview` 返回 `proxy_status=preview_forwarded`、`radar_overlay_status=loaded`、`radar_overlay_wysiwyg_complete=true`、`radar_overlay_blocks_wysiwyg=false`、当前雷达点 `128`、来源点 `150`、`robot_control_executed=false`。
  - `POST /api/robot-control/radar/scan-proof/refresh` 返回 `proxy_status=refresh_forwarded`、`readback_only=true`、`no_motion_refresh=true`、`next_action_plain=雷达扫描只读刷新完成；继续读取雷达状态和地图画面，确认雷达点已贴到当前地图。`、`starts_radar_lifecycle=false`、`starts_nav2=false`、`starts_map_runtime=false`、`robot_control_executed=false`。
  - `GET /api/robot-control/summary` 返回 `live_wysiwyg_missing_surface_ids=["camera"]`、`radar_overlay_wysiwyg_complete=true`、`current_radar_map_wysiwyg_pack_status=loaded`，雷达地图标记已从 WYSIWYG 缺口中移除。

## 剩余风险

- 摄像头仍缺首帧，当前原因是 `first_frame_total_timeout` 且 USB speed 为 `12M`；这仍阻塞建图验收。
- motion、完整 Nav2 行程、键盘连续控制和自由移动都还需要现场勾安全确认后的真实 HIL 证据；本轮没有发送任何运动指令。
