# 雷达贴图 no-motion 刷新复验

sprint_type: micro

## 实际改动

- 本轮不改产品代码，只执行固定 no-motion 读回链路验证雷达贴图所见即所得：先 `POST /api/robot-control/radar/scan-proof/refresh`，再 `GET /api/robot-control/map/preview`，最后 `GET /api/robot-control/live-summary`。
- 验证链路只刷新雷达扫描证明和地图预览，不启动雷达 lifecycle、不执行 Nav2、不发送 manual/keyboard/free-roam/建图/delivery/stop 或 `/cmd_vel`。
- 运行后 `live-summary` 的 WYSIWYG 缺口从雷达/相机收敛为只剩相机，证明雷达开始后的地图 marker 可通过当前只读刷新链路恢复到当前地图。

## 验证结果

- 通过：`POST http://127.0.0.1:7001/api/robot-control/radar/scan-proof/refresh` 返回 `status=loaded_fail_closed_summary`、`latest_scan_proof_fresh=true`、`scan_once_observed=true`、`scan_hz_observed=true`、`raw_packet_once_observed=true`、`post_refresh_latest_readback_status=not_required`。
- 通过：顺序刷新后的 `GET http://127.0.0.1:7001/api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_primary_blocked_reason=none`、来源雷达点 `152`，文案显示当前地图雷达点 `122` 个。
- 通过：`GET http://127.0.0.1:7001/api/robot-control/live-summary` 返回 `radar_map_points_visible=true`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=122`、`radar_overlay_source_point_count=152`、`live_wysiwyg_missing_surface_ids=["camera"]`。
- 通过：PC Node 仍监听 `0.0.0.0:7001`。

## 剩余风险

- 雷达贴图当前已恢复，但 `camera_current_visible=false`，所见即所得目标仍剩画面首帧缺口。
- 完整 Nav2 路线闭环仍处于 `needs_wheel_rerun`；真实 wheel L/R 非零、键盘连续手控和 delivery success 仍需要现场安全确认后执行并读回。
