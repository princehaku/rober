# O7 RTC Signaling Contract Probe API

## 定位

`GET /api/o7/rtc-signaling-contract-probe?baseUrl=<local-loopback-url>` 是 PC workstation 侧的只读 HTTP contract probe。它让 operator 从本机回环 relay 拉取机器人/relay 侧 `GET /api/o7/rtc-signaling/contract`，确认 RTC signaling/media 协议入口清单存在，但不证明真实 WebRTC、视频、media transport、实时 pose stream、ROS2 `/tf` 或机器人控制链路已通。

## 输入约束

- `baseUrl` 只允许 HTTP 本机回环：`127.0.0.1`、`localhost`、`[::1]`。
- 拒绝 HTTPS、WS/WSS、外网 host、credentials、query 和 hash。
- probe 固定拼接远端路径 `/api/o7/rtc-signaling/contract`，不接受 operator 指定任意 path。
- UI 不提供 bearer/token 输入，不提供 connect/start/video/send 按钮，不自动 probe。

## 响应摘要

响应 schema 为 `trashbot.pc_tools_workstation.o7_rtc_signaling_contract_probe.v1`，只返回脱敏摘要：

- `remote_schema`
- `contract_status`
- `key_false_fields`
- `protocol_surface_keys`
- `required_evidence_refs`
- `blocked_reasons`
- `not_proven`
- `dangerous_true_fields`
- `fail_closed_reason`

响应不得透传 token/auth/URL/credential-bearing payload。远端 `credential_handling` 只用于危险字段扫描和 protocol surface key 汇总，不展示具体策略值。

## Fail-Closed 规则

PC probe 固定：

- `network_probe_executed=false`
- `connects_cloud_production=false`
- `sends_commands=false`
- `reads_hardware=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

远端 schema 必须是 `trashbot.o7.rtc_signaling_contract.v1`。如果 schema 不匹配、HTTP 失败、JSON 不是 object，或任一危险字段为 `true`，probe 返回 `probe_status=fail_closed`。

危险字段包括但不限于：

- `network_probe_executed`
- `webrtc_session_created`
- `media_transport_connected`
- `video_track_received`
- `realtime_pose_stream_connected`
- `real_ros2_tf_connected`
- `safe_to_control`
- `sends_commands`
- `reads_hardware`
- `robot_control_executed`
- `delivery_success`
- `command_dispatch`
- `manual_control`
- `navigate_goal`
- `keyboard_control`
- `hardware_probe`
- `credential_values_exposed`

## 边界

该 probe 是 HTTP contract probe，不是 RTC probe。即使返回 `loaded_fail_closed_contract`，也只说明 PC 能从本机回环 relay 读取静态协议清单；真实 O7 仍需要独立证据：signaling session trace、offer/answer exchange、ICE selected pair、首帧视频、pose event stream、ROS2 `/tf` bridge、timeout/auth failure trace，以及硬件安全边界复核。
