# 雷达贴图 WYSIWYG no-motion 刷新

sprint_type: micro

## 实际改动

- 本轮未修改产品代码；通过 PC 固定代理执行一次 no-motion 雷达扫描 proof 刷新，并重新读取地图 preview 与 live-summary。
- 刷新目标是把“雷达开始后地图上的标记必须所见即所得”从当前 `not_current` 恢复为当前地图 overlay，而不启动雷达 lifecycle、不建图、不执行 Nav2/manual/keyboard/free-roam/delivery/stop，也不发送 `/cmd_vel`。

## 验证结果

- 通过：`POST http://127.0.0.1:7001/api/robot-control/radar/scan-proof/refresh?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 `proxy_status=refresh_forwarded`、`remote_http_status=200`、`robot_control_executed=false`、`hard_dangerous_true_fields=[]`。
- 通过：`GET http://127.0.0.1:7001/api/robot-control/map/preview?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=10`、`radar_overlay_source_point_count=10`、`radar_overlay_refresh_required=false`、`radar_overlay_primary_blocked_reason=none`，机器人地图位姿来自 `/amcl_pose`。
- 通过：`GET http://127.0.0.1:7001/api/robot-control/live-summary` 返回 `live_wysiwyg_missing_surface_ids=["camera"]`、`radar_map_points_visible=true`、`radar_overlay_status=loaded`、`map_current_visible=true`、`path_current_visible=true`、`free_move_start_ready=true`。

## 剩余风险

- 相机仍未所见即所得：`camera_current_visible=false`，建图启动仍缺 `camera_first_frame`。
- 轮速 L/R 非零、完整 Nav2 路线现场执行、delivery success 和 PC 键盘连续手控仍需要显式安全确认后的运动验收；本轮未发任何运动命令。
