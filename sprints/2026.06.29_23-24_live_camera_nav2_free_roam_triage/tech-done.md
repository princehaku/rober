# 真实相机/Nav2/自由移动现场收口

sprint_type: micro

## 实际改动

- 本轮没有改产品代码；现有 PC summary/首屏已经能正确表达三个现场事实。
- `docs/process/okr_progress_log.md`
  - 新增真实上位机只读排查结论：摄像头不是独占，当前是 DV20 UVC 无首帧；自由移动不依赖雷达/相机；Nav2 服务已非发车恢复。
- `docs/product/pc_tools_workstation.md`
  - 同步普通用户口径：共享预览多人复用成立，但当前设备源头无帧；Nav2 已恢复到可重跑路线，下一步需要现场安全确认后执行。

## 验证结果

- 通过：`curl http://127.0.0.1:7001/api/robot-control/summary` 只读显示：
  - `camera.status=source_first_frame_failed`
  - `source_diagnosis_status=uvc_no_frame_not_exclusive`
  - `preview_visible_plain` 明确“不是页面独占，UVC 没有输出视频帧”
  - `free_roam.motion_start_ready=true`
  - `free_roam.mapping_start_ready=false`，缺口为画面首帧
  - `nav2.status=goal_succeeded_wheel_feedback_not_proven`
  - `safe_command_boundary.nav2_goal_ready=true`
- 通过：SSH 到真实上位机 `root@192.168.1.11 -p 37878` 后只读验证：
  - `/dev/video1` 为 `USB Composite Device: DV20 USB`，`fuser` 未显示占用者。
  - `v4l2-ctl -d /dev/video1 --list-formats-ext` 可列出 MJPG/YUYV 格式。
  - `8088 /api/camera/health` 返回 `source_first_frame_failed`、`first_frame_total_timeout`、`source_usage.status=not_in_use`、`source_diagnosis.not_exclusive=true`。
  - `v4l2-ctl --stream-mmap --stream-count=3 --stream-to=/tmp/rober_v4l2_frame.mjpg` 生成 0 字节文件，说明设备层也没有吐帧。
  - 内核日志存在 UVC reset、`cannot get freq at ep 0x82`、`Failed to resubmit video URB` 线索。
- 通过：只读 `8787 /api/free-roam/autonomy/latest` 显示 `motion_start_ready=true`、`motion_without_radar_allowed=true`、`free_move_without_camera_allowed=true`，当前 `external_stop_requested=true`，需要现场安全确认后 start 才清除停止请求。
- 通过：非发车调用 `POST 8787 /api/nav2/start`，返回 `command_result.ok=true`，并明确 `blocked_commands_not_sent_by_start` 包含 `/cmd_vel`、`NavigateToPose goal`、`/api/base/manual`、`T=1`、`T=11`、`T=13`。
- 通过：Nav2 start 后 PC 7001 summary 显示 `readback_summary.nav2.current_blocker_reasons=none`、`safe_command_boundary.nav2_goal_ready=true`，下一步为现场安全确认后用 ROS 模式重跑图上路线并复验同窗口 wheel L/R 非零。

## 剩余风险

- 摄像头仍无画面；根因已经收窄到 UVC 设备/输入/USB/供电层，软件共享预览不能凭空生成真实帧。
- 本轮没有发送 Nav2 goal、manual、keyboard、free-roam start、delivery、stop 或 `/cmd_vel`；真实移动、完整路线闭环和 wheel L/R 非零仍需现场安全确认后执行。
- 自由移动可启动不等于建图可验收；建图启动仍需要画面首帧，建图验收还要地图记录和地图画面。
