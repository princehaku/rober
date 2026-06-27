# 上车端相机服务 systemd 托管恢复

sprint_type: micro

## 实际改动

- 通过 `ssh root@192.168.1.11 -p 37878` 做只读诊断，确认 8088 camera smoke 与 8787 upper API 都存在端口残留/服务托管漂移。
- 停掉占用 8787 的旧 upper API 监听 PID，并重启 `trashbot-upper-robot-api.service`，使 8787 回到 systemd 管理进程。
- 8088 camera service 已恢复为 `trashbot-local-webrtc-camera.service=active`，监听进程为 `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`。
- 更新 `docs/vision/board_camera_publisher.md`，记录当前实板结论：多人共享预览服务托管已恢复，但 `/dev/video1` 首帧仍失败，根因不是 PC 页面独占。

## 验证结果

- `systemctl is-active trashbot-upper-robot-api.service trashbot-local-webrtc-camera.service`：两个服务均为 `active`。
- `ss -ltnp`：`0.0.0.0:8088` 由 `local_webrtc_camera_smoke.py` 监听，`0.0.0.0:8787` 由 `upper_robot_api.py` 监听。
- PC 7001 live summary：
  - camera：`source_first_frame_failed`、`shared_preview_exclusive_camera_claim=false`、`source_usage_status=not_in_use`。
  - first-frame probe：`open_ok=true`、`read_ok=false`、`failure_reason=capture_read_call_timeout`、`backend_smoke_status=backend_no_frame_observed`。
  - free_roam：`start_ready=true`、`mapping_missing=camera_first_frame,mapping_active,fresh_map_preview`、`cmd_vel_publish_enabled=false`。

## 剩余风险

- 本轮只恢复 camera/upper API 服务托管，不修复 DV20 `/dev/video1` 无帧根因。
- 当前结论仍是：相机失败不是独占；服务支持共享预览 fanout，但底层摄像头首帧没有产出，必须检查 DV20 输入源、USB 供电/线缆或替换 known-good UVC。
- 没有执行任何 Nav2、`/cmd_vel`、串口或底盘运动命令。
