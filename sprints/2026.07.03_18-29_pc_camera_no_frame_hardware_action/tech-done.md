# PC 相机无帧硬件动作直显

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/camera/mjpeg/status` 与相机首帧 probe 代理在 `uvc_no_frame_not_exclusive`、无人占用且当前无帧时，返回 `camera_hardware_action_required=true`。
  - 对应动作标签改为 `检查摄像头输入/供电后复测`，不再只显示 `复测相机首帧`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 前端相机恢复卡增加同样的兜底判断：即使只读到 MJPEG status，也能显示硬件处理动作和复测链路。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`
  - 同步现场结论：USB 480M、非独占、采集栈 0 字节时，剩余动作是处理摄像头输入、USB 线/接口/供电或设备本体；该缺口不阻塞手控运动。

硬件协议复核来源：底盘手控证据仍按 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER UART JSON 资料解释，`T=11` 为 direct PWM input；本轮没有修改 WAVE ROVER 控制协议。

## 验证结果

- 通过：`npm test -- robotControlSummary.test.ts`，13 tests passed。
- 通过：`npm test -- App.test.ts`，239 tests passed。
- 通过：`npm run build`，TypeScript、Vite build、server TypeScript 均通过；Vite 仍提示既有 chunk 超过 500 kB。
- 通过：本地 7001 已重启并监听 `0.0.0.0:7001`。
- 通过：触发 `GET /api/robot-control/camera/mjpeg` 后，live `GET /api/robot-control/camera/mjpeg/status` 返回 `status=source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`camera_usb_speed=480M`、`camera_hardware_action_required=true`、`camera_hardware_action_label=检查摄像头输入/供电后复测`、`camera_reprobe_after_hardware_action_required=true`、`camera_blocks_free_move=false`。
- 通过：live `GET /api/robot-control/summary` 返回同源字段，并同时保持 `map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`。
- 通过：上位机停相机服务后直接验证 V4L2 mmap/userptr、ffmpeg、GStreamer 均 0 字节；临时把 `uvcvideo quirks` 从 `4294967295` 复位为 `0` 后仍无帧，当前服务已恢复 active。
- 通过：PC 7001 低速手控 `forward speed=0.06 duration_ms=360` 返回 `command_forwarded`；上位机 `wave_rover_command_debug.jsonl` 新增 `/cmd_vel -> esp32_bridge -> HTTP -> WAVE ROVER` 的 vendor `T=11,L=255,R=255` 与 stop `T=11,L=0,R=0`。

## 剩余风险

- 实时图传仍未可见：DV20 UVC 设备枚举正常且 USB 为 `480M`，但内核没有收到视频 buffer；需要现场检查摄像头输入、线/口/供电，或换 known-good UVC 后按复测链路重跑。
- `T=1001` wheel raw L/R 仍未证明非零；当前手控证据是命令到达和运动信号/命令日志，不等于 wheel raw 非零、完整 Nav2 路线执行或 delivery success。
- 本轮没有改变 `/map` 布局；地图目标当前仍由 PC 大地图和 `/map` 直达页覆盖，RViz2/Foxglove 只作为工程观察配套。
