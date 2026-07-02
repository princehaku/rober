# Camera MJPEG first-frame aliases

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/camera/mjpeg/status` 补齐与 summary 同源的首帧失败直连 alias：
  - `first_frame_probe_status`
  - `first_frame_probe_failure_reason`
  - `first_frame_failure_reason`
  - `camera_first_frame_probe_status`
  - `camera_first_frame_failure_reason`
- 当共享预览未出帧且上车 camera health/source diagnosis 已证明 `first_frame_total_timeout` 等原因时，直连 MJPEG status 不再让现场脚本读到 null。
- 文档同步说明该端点仍只读共享预览和上车 camera health，不新建独占采集、不启动 Nav2/manual/keyboard/free-roam/建图 runtime、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `npm test -- test/catalog.test.ts`
  - 通过，`1 passed`，`183 passed`。
- `npm run build`
  - 通过；Vite 仍有既有大 chunk 警告。
- `git diff --check`
  - 通过，无空白错误。
- 重启 7001 后 live 只读验证：
  - `/api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
  - `/api/robot-control/camera/mjpeg/status` 返回 `first_frame_probe_status=source_first_frame_failed`、`first_frame_probe_failure_reason=first_frame_total_timeout`、`first_frame_failure_reason=first_frame_total_timeout`、`camera_first_frame_probe_status=source_first_frame_failed`、`camera_first_frame_failure_reason=first_frame_total_timeout`。
  - 同一回包固定 `readback_only=true`、`camera_status_readback_only=true`、`sends_motion_when_clicked=false`、`starts_camera_exclusive_capture=false`、`starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`submits_delivery=false`、`stops_motion=false`。
- live 当前读回基线：
  - summary：`live_wysiwyg_missing_surface_ids=["camera"]`
  - summary：`current_camera_wysiwyg_pack_status=needs_first_frame`
  - summary：`current_camera_wysiwyg_pack_first_frame_failure_reason=first_frame_total_timeout`
  - summary：`current_camera_wysiwyg_pack_usb_speed=12M`
  - summary：`current_camera_wysiwyg_pack_hardware_action_required=true`

## 剩余风险

- 本轮是只读 API/合同补强，没有改变上车相机取帧链路；真实画面仍未出首帧，当前硬件诊断仍指向 USB 12M full-speed。
- 建图启动仍被 `camera_first_frame` 阻塞；自由移动不被相机阻塞，但真实运动仍需现场安全确认后验证。
- 工作区仍保留既有未纳入本轮的 artifact dirty 文件，本轮不处理也不提交。
