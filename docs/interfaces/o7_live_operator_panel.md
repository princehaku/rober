# O7 Live Operator Panel API

## Endpoint

`GET /api/o7/live-operator-panel`

返回 schema：`trashbot.o7.live_operator_panel.v1`。

该接口是 PC 首屏 live operator 的只读契约，用于展示上位机 SSH、camera LAN 入口、LiDAR/Radar 缺口和手控按钮的 blocked 状态。它不 SSH、不读取硬件、不 POST `/offer`、不发送底盘命令、不打开串口。camera 的实时 `/health` 与 `/devices` 结果以 `GET /api/o7/local-webrtc-camera` 为准。

## Response Contract

顶层固定继承 fail-closed 字段：

- `source="software_proof"`
- `proof_status="not_proven"`
- `pc_only=true`
- `safe_to_control=false`
- `sends_commands=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

主要字段：

- `ssh.host="192.168.1.11"`，`ssh.port=37878`，`ssh.reachable=true`，`ssh.workstation_api_8787_status="not_listening_observed"`。
- `lidar_radar.dev_lidar="missing"`，`lidar_radar.stc_by_id="unresolved"`，`lidar_radar.scan_status="not_proven"`，`lidar_radar.pointcloud_fabricated=false`。
- `camera.base_url="http://192.168.1.11:8088/"`，`camera.health_status="not_listening_observed"` 是兼容既有 live 面板合同的静态字段；本轮实时 health/devices 以 `GET /api/o7/local-webrtc-camera` 返回为准。`camera.video_source="/dev/video1"`，`camera.offer_auto_post_enabled=false`，`camera.lan_page_url` 指向同 LAN camera 页面。
- `control.visible_directions=["forward","back","left","right","stop"]`。
- `control.speed.default_value=0.2`，`min=0`，`max=0.5`，`step=0.05`，`unit="m/s"`。
- `control.command_dispatch_enabled=false`，`control.sends_commands=false`，`control.robot_ack_connected=false`。

## Blocked Reasons

当前固定 blocked reasons：

- `base_serial_identity_not_proven`
- `t1001_feedback_not_observed`
- `robot_ack_not_connected`

这些 blocker 表示当前只能展示按钮和速度 UI，不能开放真实控制。`/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ttyACM0` 不能证明底盘身份；`T=1001` 反馈未观测；robot ACK 未接入。

## UI Behavior

`O7LiveOperatorPanel.vue` 在 O7 首屏展示：

- `PC Live Operator`
- `LiDAR / Radar Signal`
- camera health 和 LAN page link
- `Forward` / `Back` / `Left` / `Right` / `Stop`
- speed slider 和数值

方向按钮点击只更新本地 blocked 文案，不调用控制 API，不发送 `/cmd_vel`、WAVE ROVER JSON、ROS2 action、云端 command 或任何底盘运动命令。

## Acceptance

本地验收：

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
```

渲染验收需确认页面包含 `PC Live Operator`、`LiDAR / Radar Signal`、`Forward`、`Stop`，点击方向按钮显示 blocked 原因，console 无 app error。

远端联调只允许只读确认 SSH、8088 camera health/devices 和 8787 API 监听状态。PC dev server 需要用 `ROBER_LOCAL_WEBRTC_CAMERA_BASE_URL=http://192.168.1.11:8088/` 启动，然后通过 `GET /api/o7/local-webrtc-camera` 读取上位机 `/health` 与 `/devices`。除非底盘身份、T1001 feedback 和 robot ACK 都被证明，否则不得发送控制命令。
