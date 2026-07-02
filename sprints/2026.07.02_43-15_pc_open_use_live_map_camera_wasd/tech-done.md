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

## 2026-07-02 23:30 追加收口

### 实际改动

- PC 首页真实地图改为高度优先撑满主画布，宽地图允许横向滚动，`data-real-map-fit-mode` 改为 `height-first-preserve-aspect-scroll-x`。
- PC summary、runbook、验收包和代理回包统一改成打开即用口径：手控、键盘、自由移动、Nav2 图上路线不再要求普通用户额外勾选安全确认；后端仍自动带固定 confirm 兼容字段并保留 stop/按住才动/失焦停。
- 普通用户地图入口明确为 PC 首页和 `/map` 大屏；ROS2 配套只作为工程观察，RViz2/Foxglove 观察地图、雷达、TF、路线、定位和 costmap，不替代 PC 简易操作页。
- 同步 `docs/product/pc_tools_workstation.md` 和 `docs/product/pc_free_roam_mapping_design.md`，记录 7001 绑定、默认小车地址、地图大屏、ROS2 工具分层和相机/雷达不阻塞运动的最新口径。

### 验证结果

- 通过：`npm test -- App.test.ts robotControlSummary.test.ts`，2 个测试文件、247 个测试全部通过。
- 通过：`npm test`，3 个测试文件、431 个测试全部通过。
- 通过：`npm run build`，客户端和 server TypeScript 构建通过；仅保留 Vite chunk size warning。
- 通过：PC Node 用当前代码重启到 `0.0.0.0:7001`；`GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：`GET /map` 返回 HTTP 200。
- 通过：`GET /api/robot-control/summary` 返回 `current_trip_execution_pack_status=ready_to_use`、`current_move_now_status=ready_to_use`、`current_keyboard_control_pack_status=ready_to_use`、`current_free_move_control_pack_status=ready_to_use`，且 `keyboard/free_move/trip/live_motion_runbook/field_acceptance` 的 safety required 均为 `false`。
- 通过：`GET /api/robot-control/map/preview` 读到真实地图 `261x113`、雷达贴图 `loaded`、当前雷达点 `153`、source 点 `179`、robot pose `map_pose_observed`、路径 `path_preview_observed` 且路径点 `18`。
- 通过：`POST /api/robot-control/base/manual` 发送 `forward/speed=0.05/duration_ms=250`，代理返回 `proxy_status=command_forwarded`、`remote_http_status=200`、`non_stop_requires_confirm_hil_checklist=false`，随后 `POST /api/robot-control/base/stop` 返回 `command_forwarded`。
- 受限：`POST /api/robot-control/base/feedback-samples` 和 summary 仍显示 wheel raw 未非零，summary 为 `L/R=0/0`、非零样本 `0/239`，缺口仍是 `same_window_wheel_lr_nonzero` 与 `delivery_success`。
- 受限：`GET /api/robot-control/camera/mjpeg/status` 返回 `status=idle_not_started`、`usb_speed=12M`、`usb_full_speed_detected=true`、`hardware_action_required=true`；`GET /api/robot-control/camera/mjpeg` 在 3 秒 smoke 内未拿到帧。

### 剩余风险

- PC 地图和路线/雷达/pose 显示已可用，但当前原始地图尺寸仍是 `261x113`；本轮通过 PC CSS 放大显示，不改变上车地图源分辨率。
- 低速手控请求能成功转发并自动 stop，但 WAVE ROVER wheel raw 仍未给出非零证明，真实轮速反馈闭环未完成。
- 相机仍需要处理 USB 12M/full-speed 或供电/线缆/端口问题；PC 共享预览不会把无帧冒充成可见画面。
- Nav2 完整路线、同窗口 wheel L/R 非零和 delivery success 仍需现场安全空间下再跑一轮真实行程验收。

## 2026-07-03 00:05 地图太小与 ROS2 配套收口

### 实际改动

- PC 首页和 `/map` 直达大屏默认缩放从 `100%` 全图适配改为 `200%` 细节大图；`适配` 按钮仍回到 `100%` 全图，最高细节放大保持 `800%`。
- 前端 DOM、Node summary、共享合同类型和 Vitest 期望同步 `map_display_default_zoom_percent=200%`，避免页面与 `curl /summary` 口径不一致。
- 文档同步：`docs/product/pc_tools_workstation.md` 和 `docs/navigation/fixed_route_workflow.md` 明确普通用户优先用 PC 大地图/`/map`，ROS2 配套只作为工程观察；本地用 RViz2，远程浏览器观察用 Foxglove bridge + Foxglove Web。

### 验证结果

- 通过：`npm test`，3 个测试文件、431 个测试全部通过。
- 通过：`npm run build`，客户端和 server TypeScript 构建通过；仅保留 Vite chunk size warning。
- 通过：PC Node 用当前代码重启到 `0.0.0.0:7001`；`GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：`GET /api/robot-control/summary` 返回 `map_display_default_zoom_percent=200%`、`live_closure_summary.map_display_default_zoom_percent=200%`、`map_display_primary_url=/map`。
- 通过：`GET /api/robot-control/map/preview` 读到真实地图 `261x113`、`robot_pose_status=map_pose_observed`、`path_preview_status=path_preview_observed`、路径点 `18`、雷达贴图 `loaded`、当前雷达点 `145`。

### 剩余风险

- 这次只修 PC 地图显示和 ROS2 配套说明，不改变上车地图源分辨率 `261x113`。
- RViz2/Foxglove 是工程观察入口，不自动启动 ROS2 runtime，也不替代普通 PC 简易操作页。
- 摄像头无帧、wheel raw L/R 非零、完整 Nav2 路线和 delivery success 仍按上一节风险继续跟进。
