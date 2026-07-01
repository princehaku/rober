# Radar Status Readback Flags Micro Sprint

sprint_type: micro

## 实际改动

- 真实执行固定 no-motion 雷达贴图复验链路后，雷达贴图从过期状态恢复为 WYSIWYG：
  - `/api/robot-control/radar/scan-proof/refresh`
  - `/api/robot-control/radar/status`
  - `/api/robot-control/map/preview`
  - `/api/robot-control/summary`
- PC `GET /api/robot-control/radar/status` 回包补齐只读边界字段：
  - `readback_only=true`
  - `radar_status_readback_only=true`
  - `sends_motion_when_clicked=false`
  - `starts_radar_lifecycle=false`
  - `starts_nav2=false`
  - `starts_manual=false`
  - `starts_keyboard=false`
  - `starts_free_roam=false`
  - `starts_map_runtime=false`
  - `submits_delivery=false`
  - `stops_motion=false`
- 更新 shared contract、server fallback/success/error 回包、catalog/App tests、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 个测试通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；仅保留 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `89927`。
- 真实 radar status smoke：

```json
{
  "proxy_status": "status_loaded",
  "status": "loaded_fail_closed_summary",
  "readback_only": true,
  "radar_status_readback_only": true,
  "sends_motion_when_clicked": false,
  "starts_radar_lifecycle": false,
  "starts_nav2": false,
  "starts_manual": false,
  "starts_keyboard": false,
  "starts_free_roam": false,
  "starts_map_runtime": false,
  "submits_delivery": false,
  "stops_motion": false,
  "robot_control_executed": false
}
```

- 真实 summary smoke：

```json
{
  "status": "needs_wheel_rerun",
  "objective_missing_ids": ["motion", "wysiwyg", "mapping"],
  "live_wysiwyg_missing_reasons": ["camera"],
  "radar_overlay_wysiwyg_complete": true,
  "radar_overlay_needs_refresh": false,
  "radar_overlay_status": "loaded",
  "radar_overlay_current_point_count": "138",
  "mapping_start_missing_evidence": ["camera_first_frame"],
  "field_acceptance_primary_no_motion_readback_action_id": "refresh_camera_first_frame"
}
```

## 剩余风险

- 本轮只执行 no-motion 雷达贴图复验和只读合同修复，没有现场安全确认，因此未执行 Nav2 路线、键盘连续手控或自由移动运动验收。
- WYSIWYG 当前只剩相机首帧缺口；建图仍缺 `camera_first_frame`。
- Motion 仍缺同窗口 wheel raw L/R 非零、delivery success、键盘按住轮速非零/松开停稳、自由移动启动读回。
