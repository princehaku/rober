# PC 打开即用大地图、图传与键盘准备

## sprint_type

micro

## 实际改动

- PC 普通首屏增加打开即用合同：地图每 2500ms 自动刷新 `/api/robot-control/map/preview`，雷达贴图每 5000ms 低频刷新 proof 后回写地图，图传每 2000ms 只读刷新共享 MJPEG status。
- 键盘连续手控改为页面打开、summary 到达或窗口重新聚焦后自动准备；准备不发车，只有按住 W/A/S/D 或方向键才通过固定 `/api/robot-control/base/manual` 发送低速 pulse，松开/失焦/切页/进入输入框仍走 stop/解除所有权。
- 修正键盘 DOM evidence 的 `manualCommandMode`，从 summary 的 `keyboard_manual_command_mode` 读取，默认兜底为 `pwm`，避免继续显示旧的 `ros`。
- 同步 `docs/product/pc_tools_workstation.md`、PC 前后端 summary 与 Vitest 期望，把 PC 特大地图、ROS2 观察配套、实时刷新和键盘自动准备合同固化。

## 验证结果

- 通过：`npm test -- App.test.ts catalog.test.ts robotControlSummary.test.ts`，3 个测试文件、431 个测试全部通过。
- 通过：`npm run build`，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成；仅保留 Vite chunk size warning。
- 通过：PC Node 已从当前代码重启到 `0.0.0.0:7001`，`GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：`GET /map` 返回 HTTP 200。
- 通过：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 为只读，返回 `map_display_primary_url=/map`、`map_display_default_zoom_percent=8000%`、`map_display_ros2_companion_tools=[rviz2,foxglove]`，键盘下一步为“页面自动准备键盘；准备本身不发车；按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页会停”。
- 通过：`GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 为只读，读到地图尺寸 `261x113`，当前雷达贴图状态 `not_current`、当前点数 `0`。
- 通过：`GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787` 为只读，返回 `status=idle_not_started`、`client_count=0`、`upstream_connected=false`。
- 通过：`POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787` 为只读，`sends_motion_when_clicked=false`、`starts_radar_lifecycle=false`。
- 现场连接复核：`ssh root@192.168.1.11 -p 7878` 仍拒绝连接；`ssh root@192.168.1.11 -p 37878` 成功，返回 `op-z3-b6.home` 和 `Thu Jul 2 09:50:01 PM CST 2026`。

## 剩余风险

- 真实摄像头是否出帧仍取决于上车 USB/UVC 源；本轮只让 PC 页面持续刷新共享预览状态，不把“可加入共享流”冒充为真实画面已可见。
- 真实小车运动仍需现场安全空间；本轮键盘自动准备不自动发车，但 WASD 长按会继续走已有低速 PWM bridge 手控链路。
- 自动驾驶完整 Nav2 路线、delivery success 与同窗口 wheel L/R 非零仍未在本轮重新做真实运动验收；summary 当前仍显示 `needs_wheel_rerun`，需要现场安全空间后单独执行。
- 用户本轮提到 `ssh root@192.168.1.11 -p 7878`；当前现场实测 `7878` 拒绝连接，`37878` 可连接，后续现场 smoke 临时沿用 `37878`。
