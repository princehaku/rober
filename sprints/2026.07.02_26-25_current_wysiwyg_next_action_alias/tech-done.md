# sprint_type: micro

## 实际改动

- PC summary 新增 `current_wysiwyg_next_action_*` 顶层短字段，用一句话把当前 WYSIWYG 下一步压平到现场可读结果。
- PC 普通首屏 `plain-current-wysiwyg-action` 同步暴露 `data-current-wysiwyg-next-action-*`，当雷达贴图已完成且只剩相机时，直接显示“雷达贴图已完成，只剩相机硬件处理/首帧复测；自由移动不受相机阻塞，建图仍等待相机首帧”。
- 更新 PC 工作站文档，明确这些 alias 只用于现场读回和 DOM smoke，不启动 Nav2/manual/keyboard/free-roam/建图/雷达 lifecycle，不提交送达，不发送 stop 或 `/cmd_vel`。

## 验证结果

- 变更前已按 no-motion 链路刷新现场读回：
  - `POST /api/robot-control/radar/scan-proof/refresh`：`readback_only=true`，`no_motion_refresh=true`，`starts_radar_lifecycle=false`。
  - `GET /api/robot-control/map/preview`：`radar_overlay_status=loaded`，当前地图雷达点 `162`，来源雷达点 `188`。
  - `POST /api/robot-control/camera/first-frame/probe`：`status=first_frame_timeout`，`failure_reason=deadline_expired`。
  - `GET /api/robot-control/camera/mjpeg/status`：`source_first_frame_failed`，`camera_usb_speed=12M`，`camera_hardware_action_required=true`。
  - `GET /api/robot-control/summary`：`live_wysiwyg_missing_reasons=["camera"]`，雷达贴图缺口已消除，剩余缺口为相机硬件/首帧。
- 代码验证：
  - `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed (2)`，`247 passed (247)`。
  - `cd pc-tools/workstation && npm run build`：通过，Vite/TypeScript 构建成功；仍有既有单 chunk 大小提示。
  - `cd pc-tools/workstation && npm run lint`：通过。
  - `git diff --check`：通过。
- Live 7001 验证：
  - 已重启 PC 服务，当前监听 `0.0.0.0:7001`，PID `82087`。
  - `GET /api/health`：`workstation_listen_address=http://0.0.0.0:7001`，`default_robot_api_base_url=http://192.168.1.11:8787`，`health_readback_only=true`。
  - `GET /api/robot-control/summary`：`current_wysiwyg_next_action_status=only_camera_hardware_action`，`current_wysiwyg_next_action_radar_overlay_complete=true`，`current_wysiwyg_next_action_only_camera_missing=true`，`current_wysiwyg_next_action_allows_free_move=true`，`current_wysiwyg_next_action_blocks_mapping_start=true`，`current_wysiwyg_next_action_hardware_action_required=true`，`current_wysiwyg_next_action_hardware_action_label=换高速USB后复测`。
  - `GET /api/robot-control/summary` 同时返回 `map_display_primary_url=/map` 和 `map_display_ros2_companion_plain=ROS2 配套：本地工程调试用 RViz2；远程浏览器观察用 Foxglove bridge + Foxglove Web；普通用户仍默认使用 PC 大地图和 /map。`

## 剩余风险

- 本轮未执行真实运动/HIL；所有新增字段和 DOM 只描述只读验收状态。
- 相机仍需要现场把 USB 摄像头换到高速 USB 口/线或带供电 Hub 后复测；当前软件读回显示 USB `12M` full-speed 和首帧超时。
