# Camera Status Readback Flags Micro Sprint

sprint_type: micro

## 实际改动

- 按 summary 声明的 camera-only no-motion 链路复验当前画面缺口：
  - `POST /api/robot-control/camera/first-frame/probe`
  - `GET /api/robot-control/camera/mjpeg/status`
  - `GET /api/robot-control/summary`
- PC `GET /api/robot-control/camera/mjpeg/status` 回包补齐只读边界字段：
  - `readback_only=true`
  - `camera_status_readback_only=true`
  - `sends_motion_when_clicked=false`
  - `starts_camera_exclusive_capture=false`
  - `starts_radar_lifecycle=false`
  - `starts_nav2=false`
  - `starts_manual=false`
  - `starts_keyboard=false`
  - `starts_free_roam=false`
  - `starts_map_runtime=false`
  - `submits_delivery=false`
  - `stops_motion=false`
- 更新 shared contract、server response、catalog/App tests、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 个测试通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；仅保留 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `1997`。
- 真实 camera first-frame probe 返回 HTTP 502，本体显示远端 probe HTTP 503、`status=first_frame_timeout`、`device=/dev/video1`、`open_ok=true`、`read_ok=false`、`failure_reason=deadline_expired`、`source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_usb_speed=12M`、`camera_hardware_action_required=true`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`、`robot_control_executed=false`。
- 真实 camera MJPEG status smoke：

```json
{
  "proxy_status": "status_loaded",
  "status": "idle_not_started",
  "readback_only": true,
  "camera_status_readback_only": true,
  "sends_motion_when_clicked": false,
  "starts_camera_exclusive_capture": false,
  "starts_radar_lifecycle": false,
  "starts_nav2": false,
  "starts_manual": false,
  "starts_keyboard": false,
  "starts_free_roam": false,
  "starts_map_runtime": false,
  "submits_delivery": false,
  "stops_motion": false,
  "robot_control_executed": false,
  "source_diagnosis_status": "uvc_full_speed_usb_not_exclusive",
  "source_readiness": "first_frame_failed",
  "source_failure_reason": "first_frame_total_timeout",
  "camera_hardware_action_required": true,
  "camera_blocks_mapping_start": true,
  "camera_blocks_free_move": false
}
```

- 真实 summary smoke：

```json
{
  "status": "needs_wheel_rerun",
  "objective_missing_ids": ["motion", "wysiwyg", "mapping"],
  "live_wysiwyg_missing_reasons": ["camera"],
  "camera_current_visible": false,
  "camera_wysiwyg_recovery_requires_usb_fix": true,
  "radar_overlay_wysiwyg_complete": true,
  "mapping_start_missing_evidence": ["camera_first_frame"]
}
```

## 剩余风险

- 相机 WYSIWYG 未完成，真实根因仍是 `/dev/video1` USB 12M full-speed / 首帧读不到；需要换高速 USB 口/线或带供电 USB Hub 后复测。
- 建图仍缺 `camera_first_frame`；该相机缺口阻塞建图启动，但不阻塞安全确认后的低速自由移动。
- Motion 仍缺同窗口 wheel raw L/R 非零、delivery success、键盘连续手控和自由移动运行读回；本轮未执行任何运动控制。
