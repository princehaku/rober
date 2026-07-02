# Radar status map preview aliases

## sprint_type

micro

## 实际改动

- 先执行 no-motion 雷达贴图恢复链路：
  - `POST /api/robot-control/radar/scan-proof/refresh`
  - `GET /api/robot-control/radar/status`
  - `GET /api/robot-control/map/preview`
  - `GET /api/robot-control/summary`
- 刷新后 live summary 的 `current_radar_map_wysiwyg_pack_status` 从 `needs_readback_refresh` 变为 `loaded`，`live_wysiwyg_missing_surface_ids` 从 `camera,radar_map_points` 变为只剩 `camera`。
- `GET /api/robot-control/radar/status` 增加固定 `/api/map/preview` 只读聚合，把地图雷达贴图结果直接暴露到同一回包：
  - `radar_status_map_preview_*`
  - `radar_overlay_status`
  - `radar_overlay_current_point_count`
  - `radar_overlay_source_point_count`
  - `radar_overlay_wysiwyg_complete`
  - `radar_overlay_primary_blocked_reason`
  - `radar_overlay_current_vs_source_plain`
- 文档同步说明该聚合仍是 no-motion readback，不启动雷达 lifecycle、Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `POST /api/robot-control/radar/scan-proof/refresh`
  - 返回 `readback_only=true`、`no_motion_refresh=true`、`sends_motion_when_clicked=false`。
  - `latest_readback_key_values.status=refreshed`，`scan_once_observed=true`、`scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`、`latest_scan_proof_fresh=true`。
- `GET /api/robot-control/radar/status`
  - 最终读回 `radar_status_map_preview_radar_overlay_status=loaded`、`radar_status_map_preview_radar_overlay_current_point_count=155`、`radar_status_map_preview_radar_overlay_source_point_count=186`、`radar_status_map_preview_radar_overlay_wysiwyg_complete=true`。
  - 同一回包 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=155`、`radar_overlay_source_point_count=186`、`radar_overlay_primary_blocked_reason=none`。
- `GET /api/robot-control/summary`
  - `current_radar_map_wysiwyg_pack_status=loaded`
  - `current_radar_map_wysiwyg_pack_current_point_count=155`
  - `radar_overlay_wysiwyg_complete=true`
  - `live_wysiwyg_missing_surface_ids=["camera"]`
- `npm test -- test/catalog.test.ts`
  - 通过，`1 passed`，`183 passed`。
- `npm run build`
  - 通过；Vite 仍有既有大 chunk 警告。
- `git diff --check`
  - 通过，无空白错误。

## 剩余风险

- 本轮没有发送运动命令；完整 Nav2 路线执行、PC 键盘连续手控、自由自助移动真实运行、wheel raw L/R 非零和 delivery success 仍需现场安全确认后 HIL 验证。
- 摄像头首帧仍未完成，当前 WYSIWYG 缺口只剩 `camera`，建图启动仍被 `camera_first_frame` 阻塞。
- 工作区仍保留既有未纳入本轮的 artifact dirty 文件，本轮不处理也不提交。
