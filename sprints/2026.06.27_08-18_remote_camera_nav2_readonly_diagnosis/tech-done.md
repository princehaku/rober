# 上车摄像头与 Nav2 只读诊断

sprint_type: micro

## 实际改动

- 本轮不改产品代码，只做上车只读诊断和留档。
- 已确认 PC Node 仍监听 `0.0.0.0:7001`，本机健康状态为 `pc_only_readonly_workstation`、`safe_to_control=false`。
- 已确认 camera shared relay 不是独占失败：
  - PC MJPEG status 返回 `shared_capture=true`、`exclusive_camera_claim=false`、`client_count=0`、`upstream_active=false`。
  - 上车 camera health 返回 `/dev/video1` 为 DV20 UVC capture，`source_usage.status=not_in_use`、`owner_count=0`。
  - SSH 只读 `fuser -v /dev/video*` 无占用；`/dev/video0` 是 Cedrus decoder，`/dev/video2` 是 UVC metadata，只有 `/dev/video1` 是真实 capture 节点。
- 已确认当前摄像头不可见的根因是内核/UVC 设备枚举存在但不出帧：
  - `camera_first_frame_probe.py --include-backend-smoke` 返回 `open_ok=true`、`read_ok=false`、`failure_reason=capture_read_call_timeout`。
  - backend smoke 四路 `v4l2_mjpg_mmap`、`v4l2_yuyv_mmap`、`ffmpeg_mjpg`、`ffmpeg_yuyv` 均为 `no_frame_timeout`、`output_bytes=0`，总体 `backend_no_frame_observed` / `no_kernel_frame_observed`。
- 已确认 Nav2 不能动的当前证据边界：
  - 最新 `nav2/goal/execution/latest` 是旧 artifact，`base_command_mode=pwm`、`base_command_nonzero_observed=true`，但 `base_feedback_latest_left_speed=0`、`base_feedback_latest_right_speed=0`、`base_feedback_lr_nonzero_proven=false`。
  - 本地与上车端代码均支持 Nav2 `base_command_mode=ros`；PC 侧下一次执行已默认传 `ros`，但本轮未在没有现场安全确认时发起真实 Nav2 运动。

## 验证结果

- 通过：`curl http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status` 只读返回 `camera_source_first_frame_failed`，且 `exclusive_camera_claim=false`。
- 通过：`curl http://192.168.1.11:8787/api/camera/health` 只读返回 `source_readiness=first_frame_failed`、`source_failure_reason=capture_read_returned_false`、`source_usage.status=not_in_use`。
- 通过：`curl http://192.168.1.11:8787/api/camera/devices` 只读返回 `/dev/video1` 为 UVC capture，`/dev/video2` 为 metadata。
- 通过：`ssh root@192.168.1.11 -p 37878` 只读执行 `ls -l /dev/video*`、`fuser -v /dev/video*`、`v4l2-ctl --list-devices`，未发现占用。
- 通过：`python3 onboard/scripts/camera_first_frame_probe.py --device /dev/video1 --width 640 --height 480 --fps 15 --timeout-s 3 --include-backend-smoke` 在上车端返回 `backend_no_frame_observed`，证明不是 PC 页面或共享 relay 独占导致无画面。
- 通过：`curl http://127.0.0.1:7001/api/robot-control/nav2/goal/execution/latest` 只读返回旧 Nav2 artifact：`goal_succeeded` 但 `base_command_mode=pwm`、wheel raw L/R 仍为 0。
- 通过：SSH 只读导入上车端 `upper_robot_api.py`，确认 `DEFAULT_NAV2_BASE_COMMAND_MODE=ros`、`ALLOWED_NAV2_BASE_COMMAND_MODES=['pwm','ros','speed']`。

## 剩余风险

- 当前摄像头问题需要继续现场硬件/USB/UVC 链路处理，例如重新插拔/换 known-good UVC/检查供电或内核驱动；PC 代码无法在内核 0 bytes 的情况下生成真实实时预览。
- 本轮未执行真实 manual、keyboard、free-roam 或 Nav2 motion，因此不证明 wheel raw L/R 非零、完整 Nav2 路线执行或 delivery success。
- 下一次真实自动驾驶复验应在现场安全确认后，从 PC 触发 `base_command_mode=ros` 的 Nav2 执行，并以 wheel raw L/R 非零作为通过条件。
