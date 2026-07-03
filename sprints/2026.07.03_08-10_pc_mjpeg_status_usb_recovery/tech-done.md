# PC MJPEG Status USB Recovery Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通 PC 相机卡新增 MJPEG status 兜底读回，把 `/api/robot-control/camera/mjpeg/status` 中的 `uvc_full_speed_usb_not_exclusive`、`12M`、硬件动作和非独占状态合并到首屏事实条、相机状态摘要和 `plain-camera-usb-recovery-proof`。
- `pc-tools/workstation/test/App.test.ts`：新增 DOM 回归用例，覆盖 summary camera 字段 stale/fetch_failed、但 MJPEG status 已经给出 USB 12M full-speed 诊断时，普通界面必须显示“不是页面独占、USB=12M、换高速 USB 口/线或带供电 Hub 后复测”。
- `docs/product/pc_tools_workstation.md`：同步记录 PC 相机卡的 MJPEG status 兜底诊断合同。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts -t "full-speed USB camera recovery|MJPEG status USB diagnosis"`，2 个目标用例通过。
- 已通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "camera MJPEG status|robot control summary exposes live closure"`，9 个目标用例通过。
- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`，238 个用例通过。
- 已通过：`npm --prefix pc-tools/workstation run build`，生成 `dist/assets/index-Bg9Z-Y_W.js` 和 `dist/assets/index-vN5WgCcr.css`。
- 已通过：重启 PC Node 到 `0.0.0.0:7001`，`lsof` 显示 `node` PID `42127` 监听 `TCP *:7001`；`GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、默认小车地址 `http://192.168.1.11:8787`。
- 已通过：`GET /` 返回新 bundle `index-Bg9Z-Y_W.js`。
- 已通过：只读 `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=status_loaded`、`source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`source_diagnosis_not_exclusive=true`、`uvc_usb_topology_video_usb_speed=12M`、`camera_usb_speed=12M`、`camera_usb_full_speed_detected=true`、`camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`。
- 已通过：只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回地图当前可见、路线当前可见、雷达 overlay 当前可见，`path_preview_point_count=18`、`radar_overlay_point_count=189`、`robot_pose_status=map_pose_observed`；同一响应的 camera summary 仍是 `fetch_failed/not_loaded`，正好覆盖本轮 MJPEG status 兜底场景。
- 已通过：短脉冲 `POST /api/robot-control/base/manual` 返回 `proxy_status=command_forwarded`、上位机 HTTP 200；上位机 `wave_rover_command_debug.jsonl` 出现新时间戳 `T=11 L=255/R=255`，随后 stop `T=11 L=0/R=0`。
- 已确认未通过：`GET /api/robot-control/base/feedback-samples` 和上位机 `wave_rover_feedback_debug.jsonl` 仍显示 `T=1001 L/R=0/0`，不能声明 wheel raw 非零。

## 剩余风险

- 真实 DV20 摄像头现场仍停在 USB `12M` full-speed，直接 V4L2 STREAMON 失败；这是物理 USB 链路/供电/接口问题，不是 PC 页面独占问题。
- 当前 PC 手控命令链路已证明到 Robot API/bridge/vendor `T=11`，但 `T=1001` wheel raw L/R 仍为 `0/0`，不能声明 wheel raw 非零、物理移动、Nav2 自动驾驶完成或 delivery success。
- 旧的两个 2026.06.11 artifact 脏文件不是本轮改动，未纳入本轮提交范围。
