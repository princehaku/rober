# 雷达贴图只读刷新实测闭环

sprint_type: micro

## 实际改动

- 通过 PC Node `0.0.0.0:7001` 执行只读雷达贴图恢复链路：先刷新 `radar/scan-proof/refresh`，再刷新 `map/preview`。
- 未执行 Nav2、manual、keyboard、free-roam、map start、delivery、stop 或 `/cmd_vel`；本轮只改变现场读回材料和 sprint 留档。
- 产品文档补充本轮已验证的只读刷新验收口径，方便后续现场复测同一链路。

## 验证结果

- 刷新前 `GET /api/robot-control/live-summary`：`radar_map_points_visible=false`、`radar_overlay_status=not_current`、`radar_overlay_current_point_count=0`、`radar_overlay_source_point_count=187`、`radar_overlay_primary_blocked_reason=runtime_scan_stale_for_map_radar_overlay`。
- `POST /api/robot-control/radar/scan-proof/refresh`：返回 `latest_scan_proof_fresh=true`、`robot_control_executed=false`。
- 随后 `GET /api/robot-control/map/preview`：返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=156`、`radar_overlay_source_point_count=186`、`radar_overlay_refresh_required=false`、`radar_overlay_primary_blocked_reason=none`。
- 最终 `GET /api/robot-control/live-summary`：返回 `radar_map_points_visible=true`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=156`、`radar_overlay_source_point_count=186`、`live_wysiwyg_missing_surface_ids=["camera"]`。
- `git diff --check`：通过。
- 复核 `GET /api/robot-control/live-summary`：保持 `radar_map_points_visible=true`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=156`、`radar_overlay_source_point_count=186`，当前所见缺口收敛为 `live_wysiwyg_missing_surface_ids=["camera"]`。

## 剩余风险

- 雷达贴图 WYSIWYG 已通过只读刷新闭环；当前所见即所得还剩相机首帧，现场读数仍显示 USB 12M full-speed 导致 `camera_current_visible=false`。
- 完整 Nav2 路线仍卡在同窗口轮速 L/R 非零复验，delivery success 也仍需现场安全确认后的执行闭环。
