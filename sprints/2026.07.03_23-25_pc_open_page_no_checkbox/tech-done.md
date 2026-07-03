# 2026.07.03 23:25 PC Open Page No Checkbox

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `.simple-user-console` 新增打开即用 DOM 合同：
    `data-open-page-motion-ready=true`、`data-open-page-no-visible-safety-checkbox=true`、
    `data-open-page-safety-mode=site_safe_by_default`、`data-visible-safety-checkbox-count=0`。
  - 移动/导航卡同步暴露 `data-open-page-motion-ready=true` 与
    `data-open-page-no-visible-safety-checkbox=true`。
  - 可见文案从“现场安全已确认”收敛为“打开即用”，兼容旧脚本的隐藏 input 仍保持 checked。
- `pc-tools/workstation/test/App.test.ts`
  - 回归普通首屏打开即用合同和无可见 safety checkbox。
- `pc-tools/workstation/test/catalog.test.ts`
  - 回归源码合同，防止后续删掉打开即用 DOM 字段。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步 PC 普通首屏无可见安全勾选框口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "reuses one plain safety confirmation for trip, keyboard, and free-roam mapping"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "keeps the open PC page live and keyboard-ready without changing motion gates"`：通过，1 passed。
- `cd pc-tools/workstation && npm run build`：通过，`tsc` + `vite build` + server `tsc` 均成功。
- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`：通过，190 passed。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts`：通过，240 passed。
- `git diff --check`：通过。
- PC Node 已重启为 `HOST=0.0.0.0 PORT=7001 npm run api`，监听 `*:7001`。
- 静态 bundle 验证：
  - `data-open-page-motion-ready` 出现 3 处。
  - `data-open-page-no-visible-safety-checkbox` 出现 3 处。
  - `data-open-page-safety-mode` 与 `data-visible-safety-checkbox-count` 各 1 处。
  - 可见文案包含 `打开即用；可直接试动`。
- 现场上位机验证：
  - `trashbot-upper-robot-api.service` 与 `trashbot-local-webrtc-camera.service` 均为 `active`，`uvcvideo quirks=0`。
  - 触发共享 MJPEG 后返回 `first_frame_total_timeout`，没有执行运动控制。
  - 雷达贴图 no-motion refresh 后 summary：`map_preview_status=loaded`、`path_preview_point_count=18`、
    `route_target_visible=true`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、
    `radar_overlay_current_point_count=103`。
  - 相机 summary：`camera_first_frame_probe_status=source_first_frame_failed`、
    `camera_first_frame_failure_reason=first_frame_total_timeout`、
    `camera_input_signal_check_required=true`、`camera_hardware_action_label=检查摄像头输入/供电后复测`。
  - PC manual forward/back 短脉冲均 `proxy_status=command_forwarded`、`base_command_mode=ros`、
    `feedback_mode=realtime`、`command_result_ok=true`、`stop_result_ok=true`、
    `motion_signal_observed=true`、`imu_attitude_delta_observed=true`。
  - stop 代理返回 `proxy_status=command_forwarded`、`status=stopped`。
  - stop 后 summary：`keyboard_continuous_motion_verified=true`、`keyboard_stop_after_release=true`、
    `keyboard_wheel_lr_nonzero=false`。
- 低层相机复核：
  - `v4l2-ctl --all` 显示 DV20 `/dev/video1` input 为 `Input 1: ok`。
  - 该设备不支持 DV timings 查询，`--query-dv-timings` / `--get-dv-timings` 返回 inappropriate ioctl。
  - 停相机服务后 `MJPG@1280x720` 使用 `--stream-skip=30 --stream-count=1` 仍输出 0 字节；服务恢复 active。

## 剩余风险

- 相机实时图传仍无真实首帧；当前证据继续指向摄像头输入、USB 线/接口/供电或 DV20/采集设备本体，而不是 PC 页面独占或 safety gate。
- WAVE ROVER wheel raw L/R 非零仍未证明，manual 回包仍为 `wheel_feedback_latest_raw_left/right=0/0`；本轮只证明 PC 打开即用、命令转发、自动 stop 和 IMU/运动信号。
- 完整 Nav2 `nav2_goal_succeeded`、同窗口 wheel raw 非零和 `delivery_success` 仍未完成。
