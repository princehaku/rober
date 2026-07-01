# Camera Shared Preview Top Aliases

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增共享相机预览 alias：`camera_shared_preview_endpoint`、`camera_shared_preview_status_endpoint`、`camera_shared_preview_single_upstream`、`camera_shared_preview_auto_joins`、`camera_shared_preview_shared_capture`、`camera_shared_preview_exclusive_camera_claim`、`camera_shared_preview_contract`、`camera_shared_preview_multi_viewer_status`、`camera_shared_preview_multi_viewer_plain`、`camera_shared_preview_access_plain` 和 `camera_shared_preview_realtime_plain`。
- 普通首屏 `plain-live-closure-summary` DOM 同步暴露 `data-camera-shared-preview-*`，现场 DOM smoke 不必钻 `readback_summary.camera` 就能确认“谁打开页面都接同一条共享预览，不是页面独占”。
- App/summary 回归测试覆盖新增 alias，USB full-speed 场景继续保留“当前没有实时画面”的硬件恢复提示。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`，明确这些字段只读，不打开独占相机、不创建第二条上游、不启动建图或运动命令。

## 验证结果

- `git diff --check`：通过。
- `npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件、427 个用例通过。
- `npm run lint`：通过。
- `npm run build`：通过，Vite 仅保留既有大 chunk warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `92414`。
- 真实 `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787`：
  - `proxy_status=status_loaded`
  - `workstation_endpoint=/api/robot-control/camera/mjpeg/status`
  - `shared_preview_client_count=0`
  - `shared_preview_upstream_active=false`
  - `shared_preview_shared_capture=true`
  - `shared_preview_exclusive_camera_claim=false`
  - `shared_preview_contract=single_shared_capture_for_multiple_clients`
  - `shared_preview_multi_viewer_status=single_upstream_multi_viewer`
  - `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`
  - `sends_motion_when_clicked=false`
  - `starts_nav2/manual/keyboard/free_roam/map_runtime=false`
  - `robot_control_executed=false`
- 真实 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 读回新增 alias：
  - `camera_shared_preview_endpoint=/api/robot-control/camera/mjpeg`
  - `camera_shared_preview_status_endpoint=/api/robot-control/camera/mjpeg/status`
  - `camera_shared_preview_single_upstream=true`
  - `camera_shared_preview_auto_joins=true`
  - `camera_shared_preview_shared_capture=true`
  - `camera_shared_preview_exclusive_camera_claim=false`
  - `camera_shared_preview_contract=single_shared_capture_for_multiple_clients`
  - `camera_shared_preview_multi_viewer_status=single_upstream_multi_viewer`
  - `camera_shared_preview_multi_viewer_plain` 包含“谁打开页面都接入同一个共享 relay”
  - `camera_shared_preview_access_plain` 包含“不是页面独占”
  - `camera_shared_preview_realtime_plain` 仍提示 USB 12M full-speed 需要换高速 USB/线/供电后复测。
- 重启后 summary 一度显示 `radar_map_points` stale；按既有 no-motion 雷达恢复链路执行 `POST /api/robot-control/radar/scan-proof/refresh`、读 `radar/status`、读 `map/preview`、再读 summary 后恢复：
  - `live_wysiwyg_missing_surface_ids=["camera"]`
  - `radar_overlay_wysiwyg_complete=true`
  - `radar_map_points_visible=true`
  - `mapping_lidar_fresh_gate_status=ready`
  - `mapping_lidar_fresh_readback_ready=true`
  - 雷达 refresh 回包 `readback_only=true`、`no_motion_refresh=true`、`sends_motion_when_clicked=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只补共享预览可观测字段，没有主动打开 `/api/robot-control/camera/mjpeg`，避免为了 smoke 新增 MJPEG client。
- 当前真实相机首帧仍可能因 USB 12M full-speed / 供电 / 线缆 / 采集链路而不可见；共享 relay 解决“多人打开同一条流”的合同，不等于已经恢复相机首帧。
- 本轮没有安全确认，未执行任何 motion/control POST；Nav2 wheel raw L/R 非零、delivery success、PC 键盘连续手控和自由移动真实运动仍待现场安全确认后验收。
