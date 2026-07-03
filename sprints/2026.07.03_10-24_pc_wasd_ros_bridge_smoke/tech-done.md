# PC WASD ROS Bridge Smoke

## sprint_type

micro

## 目标

- PC 端键盘/WASD 和低速点动默认走上位机 ROS `/cmd_vel` 手控路径，避免 PC API 抢占 `/esp32_bridge` 正在持有的 `/dev/ttyS5`。
- 保持 PC 端简易普通用户风格，继续绑定 `0.0.0.0:7001`，不调用 subagent，不改 Clash。
- 现场复测相机是否为页面独占问题、底盘是否依赖雷达、自动驾驶/手控命令链是否能到 bridge。

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - PC `/api/robot-control/base/manual` 和 `/api/robot-control/base/first-jog` 不再硬编码 `command_mode=pwm`，改为共享默认 `command_mode=ros`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 `ROBOT_CONTROL_KEYBOARD_MANUAL_COMMAND_MODE="ros"`，summary/readback/action card 同步暴露 ROS 手控合同。
  - 键盘连续手控文案从 PWM 快速短脉冲改为 ROS `/cmd_vel` 低速短脉冲。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - WASD、屏幕方向键、普通低速点动请求体统一从 summary 边界读取手控模式，默认 `ros`。
  - 继续保持页面打开即准备键盘，按住才发低速 pulse，松开/失焦/切页 stop。
- `pc-tools/workstation/src/shared/contracts.ts`
  - `safe_command_boundary.keyboard_manual_command_mode` 类型从固定 `"pwm"` 放开为 `"ros" | "speed" | "pwm"`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 PC 手控代理、summary 和文案断言，覆盖 `command_mode=ros` 转发。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步 PC 手控默认入口为 `command_mode=ros`，底层由 bridge 按现场参数落到 WAVE ROVER PWM。
- `docs/product/pc_tools_workstation.md`
  - 同步地图 100% 默认/45% 适应全图口径。
  - 记录 2026-07-03 10:24 现场手控、HTTP/serial A/B 和相机状态复核。

## 验证结果

- PC 测试：
  - `npm test -- catalog.test.ts`：185 passed。
  - `npm test -- App.test.ts`：238 passed。
  - `npm test -- robotControlSummary.test.ts`：12 passed。
  - `npm test -- --maxWorkers=1 App.test.ts catalog.test.ts robotControlSummary.test.ts`：435 passed。
- PC build：
  - `npm run build`：通过；仅保留既有 Vite chunk size warning。
- PC 运行态：
  - 7001 新进程命令：`node ... tsx ... src/server/index.ts`。
  - `GET http://127.0.0.1:7001/api/health`：`workstation_host=0.0.0.0`、`workstation_port=7001`、默认上车 API `http://192.168.1.11:8787`。
  - `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：`safe_command_boundary.keyboard_manual_command_mode=ros`、`readback_summary.keyboard.manual_command_mode=ros`。
- 现场手控 smoke：
  - PC `POST /api/robot-control/base/manual`，`direction=forward`、`speed=0.04`、`duration_ms=300`：`proxy_status=command_forwarded`、`remote_http_status=200`。
  - 同次返回 `manual_command_executed=true`、`auto_stop_executed=true`、`feedback_during_motion_t1001_frame_count=80`。
  - `/esp32_bridge` HTTP 路径日志出现新鲜非零命令：`command_transport=http`、`http_write_returned=true`、`T=11,L=255,R=255`。
  - 临时把 `/esp32_bridge command_transport` 切到 `serial` 后复测，日志出现 `command_transport=serial`、`serial_write_returned=true`、`T=11,L=255,R=255`；随后已恢复 `command_transport=http`。
  - HTTP 与 serial 两条路径的同窗口 `T=1001 L/R` 仍为 `0/0`，`wheel_feedback_lr_nonzero_proven=false`。
- 相机 smoke：
  - `/api/camera/mjpeg/status`：`shared_capture=true`、`exclusive_camera_claim=false`、`source_diagnosis_status=uvc_full_speed_usb_not_exclusive`。
  - `lsusb -t`：DV20 UVC 摄像头仍挂在 `Bus 06` 的 `12M` full-speed OHCI。
  - `/dev/video1`、`/dev/video2` 均为 `USB Composite Device: DV20 USB`，`/dev/video0` 是 `cedrus`。

## 剩余风险

- wheel raw L/R 非零尚未完成：PC/API/ROS `/cmd_vel`/bridge/HTTP/serial 传输层均已证明能发非零底盘命令，但 WAVE ROVER `T=1001 L/R` 仍返回 `0/0`。剩余风险集中在电机使能、底盘模式、下位机固件状态、反馈链路或实体运动/编码器能力，不是雷达、相机或 PC 页面 gate。
- 相机实时预览尚未恢复：PC 共享 MJPEG 不是独占问题；当前 blocker 是 DV20 UVC 仍在 12M full-speed USB 链路。需要把摄像头换到 480M USB 口/线或带供电 Hub 后再复测。
- Nav2/送达闭环未升级：本轮只证明 PC 手控默认入口和 bridge 命令链，不把命令到达升级成完整 Nav2 路线 HIL、wheel raw 非零或 delivery success。

## OKR 备注

本轮提升 PC 端“打开即可 WASD/低速点动”的软件链路，并把硬件 blocker 从 PC/ROS2/雷达依赖中剥离到 WAVE ROVER 底盘反馈与 USB 相机物理链路。
