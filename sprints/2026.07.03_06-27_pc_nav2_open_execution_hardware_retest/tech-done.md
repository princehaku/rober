# PC Nav2 打开即用与硬件链路复测

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`POST /api/robot-control/nav2/goal/execute` 后端固定代理自动写入 `confirm_navigation_execution=true`，不再要求普通用户或现场脚本额外传确认字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：Nav2 执行 blocking requirements 移除 `confirm_navigation_execution`，普通首屏文案改为“执行图上路线打开即用”。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：更新 Nav2 执行合同测试，覆盖请求未传 `confirm_navigation_execution` 时仍由 PC 代理转发上车并自动补兼容字段。

## 现场验证结果

- PC Node 已重启并绑定 `0.0.0.0:7001`；本机读回 `GET /` 正常返回页面，`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `map_display_default_zoom_percent=45%`、`nav2_goal_ready=true`。
- 上车相机复测：停止 `trashbot-local-webrtc-camera.service` 后 `/dev/video1` 无 holder；对 USB `6-1` 执行 reauthorize 后仍枚举在 Bus 06 `12M` full-speed；最低带宽 `YUYV 320x240@20` 直接 `VIDIOC_STREAMON returned -1 (Input/output error)` 且输出 0 字节；服务已重启为 active，`/api/camera/first-frame/probe` 仍 `first_frame_timeout`。结论仍是 USB/full-speed 物理链路或设备输出问题，不是 PC 页面独占。
- PC WASD/手控复测：`forward/back` 通过 PC 代理返回 `proxy_status=command_forwarded`、`manual_command_executed=true`、`auto_stop_executed=true`，bridge command log 观察到 `T=11 L/R=255`、`T=11 L/R=-255` 和 stop `0/0`。
- 底盘模式对照：临时切 `command_mode=speed` 观察到 `T=1 L/R=±0.092308`；再临时把 `max_wheel_speed_mps=0.24` 观察到 `T=1 L/R=±0.5`；两组均自动 stop，`T=1001 L/R` 仍为 `0/0`。已恢复 `command_mode=pwm`、`max_wheel_speed_mps=1.3`。
- Nav2 lifecycle 复测：实时 lifecycle 读回 `map_server`、`amcl`、`planner_server`、`controller_server` active；手动激活 `bt_navigator`、`behavior_server`、`waypoint_follower`、`velocity_smoother` 后均 active。
- PC Nav2 执行复测：请求不带 `confirm_navigation_execution`，`POST /api/robot-control/nav2/goal/execute?baseUrl=http://192.168.1.11:8787` 使用目标 `(0.8, 0.05, 0)`、`base_command_mode=pwm` 返回 `proxy_status=execution_forwarded`、`remote_http_status=200`、`goal_accepted=true`、`result_received=true`、`result_status=succeeded`；随后 PC stop 代理返回 `status=stopped`。
- PC 回归测试：`cd pc-tools/workstation && npm test -- --run test/App.test.ts test/robotControlSummary.test.ts test/catalog.test.ts` 通过，`3` 个测试文件、`433` 个测试全部通过。
- PC 生产构建：`cd pc-tools/workstation && npm run build` 通过，Vite 输出 `dist/index.html` 与主 JS/CSS 产物；仍保留既有单 chunk 超过 500 kB 的 Vite 体积警告。

## 剩余风险

- 实时图传仍未可见：硬件枚举为 USB `12M`，最低带宽 V4L2 stream 失败。需要把摄像头换到 480M high-speed USB 口/线/供电 Hub，或换 known-good UVC 摄像头后复测。
- PC/WASD 到 bridge/UART 的前进、后退、stop 命令链路已证明，但 `T=1001 L/R` 在 PWM 和 T=1 强对照下均保持 `0/0`；不能宣称 wheel raw 非零、真实物理移动或 HIL pass。下一步应检查 WAVE ROVER 电机使能、底盘模式、下位机固件状态或电机电源。
- Nav2 goal 已能 accepted/succeeded，但本次 `base_command_nonzero_observed=false`，更像目标太近或 controller 未产生非零速度；完整“路线驱动底盘运动”仍未证明。
- delivery success 未收口：上车 gate 要求 Nav2 succeeded、operator report、observed motion/stop、delivery_success claim 和外部视频或可见相机材料；当前不能伪造这些材料。
