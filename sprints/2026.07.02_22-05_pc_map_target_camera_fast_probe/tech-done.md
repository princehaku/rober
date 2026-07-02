# 2026.07.02_22-05 PC 地图目标点与相机快速 probe

sprint_type: micro

## 实际改动

- PC 地图 WYSIWYG 图层条新增“目标点”层，路线终点和 Nav2 执行目标都会明确计入当前画布状态；`plain-map-wysiwyg-layer-strip` 新增 `data-goal-marker-visible`、`data-route-target-marker-visible`、`data-route-target-state`。
- PC `camera/first-frame/probe` 普通只读代理超时从 `60000ms` 收紧到 `12000ms`，显式 backend smoke 从 `75000ms` 收紧到 `45000ms`。
- 上车 `upper_robot_api.py` 的普通相机格式 fallback 增加总预算和单次短进程预算，避免 UVC 无帧时把 HTTP 请求拖到一分钟。
- 同步更新 PC 产品文档，说明 ROS2 配套仍是 RViz2/Foxglove 观察，普通用户默认使用 PC 大地图和 `/map`。

## 验证结果

- `npm test -- App.test.ts catalog.test.ts robotControlSummary.test.ts`：通过，3 个文件、431 个测试通过。
- `npm run build`：通过；保留 Vite chunk size warning。
- `python -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/camera_first_frame_probe.py onboard/scripts/local_webrtc_camera_smoke.py`：通过。
- `python -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_camera_first_frame_probe onboard.tests.test_local_webrtc_camera_smoke`：通过，146 个测试通过、1 个跳过；本机没有 `pytest` 模块，已用标准库 unittest 跑同组测试。
- PC 服务已重启到 `0.0.0.0:7001`，`/api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、默认小车地址 `http://192.168.1.11:8787`。
- 上车 `upper_robot_api.py` 已 scp 到 `/root/rober/onboard/scripts/upper_robot_api.py` 并重启，`ss -ltnp` 显示 `0.0.0.0:8787` 由新 `python3 scripts/upper_robot_api.py` 监听。
- 现场 `GET /api/robot-control/map/preview`：`preview_forwarded`，真实地图 `261x113`，Nav2 路线 `18` 点，机器人 `map` 位姿可见，雷达 overlay `loaded`，当前 `154` 点。
- 现场 `POST /api/robot-control/camera/first-frame/probe`：`12s` 内返回 `fetch_timeout_12000ms`，并带回 `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_usb_speed=12M`、`camera_first_frame_ready=false`。
- 现场 `POST /api/robot-control/base/manual` 低速 `forward` `0.08m/s` `240ms`：PC proxy `command_forwarded`，上车返回 `manual_command_executed=true`、`auto_stop_executed=true`；debug log 仍显示 wheel raw `L/R=0/0`，IMU pitch/roll 有变化。
- 现场 `GET /api/robot-control/summary`：`map_once_observed=true`，`path_preview_point_count=18`，`radar_overlay_status=loaded`，`radar_overlay_point_count=154`，`keyboard_control_mode=bounded_repeating_manual_pulse`，`keyboard_manual_proxy_endpoint=/api/robot-control/base/manual`。

## 剩余风险

- 现场摄像头仍然不是可见画面：USB `12M` full-speed 与 UVC 无帧问题仍在，本轮只把 PC 卡死改成 12 秒内结构化失败返回。
- WAVE ROVER feedback 的 wheel raw `L/R` 仍为 `0/0`，所以完整 wheel raw 非零验收未完成；本轮只证明 PWM manual 命令经 PC->上车固定链路执行并自动停车。
- 用户口径提到 SSH `7878`，现场当前证据仍是 `7878` refused、`37878` 可连；本轮部署使用 `37878`。
