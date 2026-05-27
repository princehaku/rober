# O7 RTC Signaling Contract API

## 定位

`GET /api/o7/rtc-signaling/contract` 是机器人/云 relay 侧的只读协议入口清单，schema 固定为 `trashbot.o7.rtc_signaling_contract.v1`。它用于让 PC 后续 probe 知道板端 RTC 与实时地图接入还缺哪些协议面，不代表 WebRTC、视频、音频、ROS2 `/tf`、实时 pose 或机器人控制已经跑通。

## Fail-Closed 字段

响应必须固定：

- `source=software_proof`
- `proof_status=not_proven`
- `network_probe_executed=false`
- `webrtc_session_created=false`
- `media_transport_connected=false`
- `video_track_received=false`
- `realtime_pose_stream_connected=false`
- `real_ros2_tf_connected=false`
- `safe_to_control=false`
- `sends_commands=false`
- `reads_hardware=false`
- `robot_control_executed=false`
- `delivery_success=false`

该 endpoint 不读取 env token、不执行网络探测、不创建 WebRTC session、不读取硬件、不下发命令、不写 relay state。

## 协议面清单

`protocol_surfaces` 保持稳定 JSON 字段，供 PC 和后续板端实现逐项 probe：

- `signaling_endpoint`：未来 signaling session 创建入口、HTTP 方法、路径模板和必填字段。
- `session_identity`：`session_id` 与 `idempotency_key` 必填，重放必须返回相同 receipt 或显式 conflict。
- `offer_answer`：未来 WebRTC offer/answer SDP 字段位置；当前 contract endpoint 禁止携带真实 SDP。
- `ice_candidates`：未来 trickle ICE candidate 字段和 timeout 语义。
- `media_tracks`：video 必选、audio 可选；当前 `received=false` 且 codec 未协商。
- `pose_realtime_events`：未来实时 pose event schema，并要求 ROS2 `/tf` bridge 证据。
- `elevator_realtime_events`：未来电梯 realtime event schema，并要求楼层 evidence ref。
- `credential_handling`：未来凭证传递策略，使用 `credential_transport_policy` 和 `credential_values_exposed`，字段名不包含 token/auth，响应永远不暴露凭证值。
- `observability_evidence_refs`：signaling trace、ICE trace、首帧视频、pose event、ROS2 `/tf` bridge 等证据引用。
- `failure_timeout_semantics`：signaling timeout、ICE failed、media timeout、pose stream timeout、auth failed、session conflict 等失败状态。
- `forbidden_actions`：禁止 command dispatch、manual control、navigate goal、keyboard control、hardware probe，以及从该 contract endpoint 发起网络 probe。

## 边界

该 API 是 O7 RTC/实时地图接入前置合同，不是 live endpoints manifest 的替代品，也不是真实连通性证明。真实打通仍需要独立证据：机器人侧 signaling client trace、offer/answer exchange trace、ICE selected pair trace、带时间戳首帧视频、pose event stream trace、ROS2 `/tf` bridge trace，以及超时和认证失败 trace。
