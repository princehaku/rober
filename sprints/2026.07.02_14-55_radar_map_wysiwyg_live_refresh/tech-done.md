# Radar Map WYSIWYG Live Refresh

- sprint_type: micro
- 时间：2026-07-02 14:55 CST
- Owner：User Touchpoint Full-Stack Engineer

## 实际改动

- 本轮未改产品代码；执行 PC 现有 no-motion 读回链路，把雷达贴图从过期来源点刷新为当前地图画面。
- 更新 `docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md` 记录现场证据与剩余风险。

## 验证结果

- 刷新前 `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787`：`radar_overlay_status=not_current`，当前显示 `0` 个点，旧来源点 `188` 个，提示“雷达扫描已过期，所以当前不贴到地图”。
- 执行 `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787`：返回 `latest_scan_proof_fresh=true`，`robot_control_executed=false`，`safe_to_control=false`，且 `starts_nav2/manual/keyboard/free_roam/map_runtime=false`。
- 刷新后 `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787`：`radar_overlay_status=loaded`，当前显示 `129` 个点，来源 `135` 个点，文案为“雷达点已贴到当前地图”。
- 刷新后 `GET /api/robot-control/summary`：`current_radar_map_wysiwyg_pack_status=loaded`，`current_radar_map_wysiwyg_pack_needs_refresh=false`，`live_wysiwyg_missing_surface_ids=["camera"]`。

## 剩余风险

- 目标仍未完成：真实 Nav2 行程、键盘连续手控、自由自助移动都还缺现场安全确认后的运动证据。
- 相机仍缺首帧；`current_camera_wysiwyg_pack_status=needs_first_frame`，建图仍被 `camera_first_frame` 阻塞。
- 本轮没有发送任何运动、Nav2、manual、keyboard、free-roam、建图、delivery 或 stop 请求。
