# O7 RTC Signaling Session Receipt API

## 定位

`POST /api/o7/rtc/signaling/sessions` 是 O7 RTC/实时地图真实链路前的受限收件入口，schema 固定为 `trashbot.o7.rtc_signaling_session_receipt.v1`。它只校验最小 signaling 字段并返回 fail-closed receipt，方便 PC probe 验证 relay 已有受控入口。

该 endpoint 不创建 WebRTC session、不生成 answer、不处理 ICE、不连接媒体、不读取硬件、不发送控制、不写 command store、不证明视频、实时 pose 或 ROS2 `/tf` 已通。

`GET /api/o7/rtc-signaling/contract` 会把该入口声明为 `receipt_only_implemented`，并把 `session_identity` 声明为 `receipt_only_validated`。这两个状态只覆盖本页描述的 bearer-gated 收件和字段校验，不代表真实 RTC session、answer、ICE 或媒体能力已经实现。

## Auth 策略

该入口接收 `offer.sdp` payload，因此默认走 bearer gate，与 `/api/commands/*` 一样检查 `Authorization: Bearer <token>`。如果 relay 启动时 expected token 为空，则本地开发和测试环境仍可不带 bearer 访问。

## 请求

请求 body 必须是 JSON object，最少字段：

```json
{
  "robot_id": "trashbot-001",
  "client_id": "pc-console",
  "session_id": "rtc-session-001",
  "idempotency_key": "rtc-session-001-create",
  "offer": {
    "sdp": "..."
  }
}
```

relay 只记录字段存在性、字符串长度和短 `sha256_prefix` 摘要。响应不得回显 SDP、token、Authorization、auth、URL、TURN/STUN credential、ROS topic、`/cmd_vel`、串口或硬件信息。

## 响应

字段完整时返回 HTTP 200；缺少必填字段时返回 HTTP 400，但仍使用结构化 receipt，方便 PC probe 读取 `missing_fields` 和固定 fail-closed 字段。坏 JSON 继续返回现有 `malformed_json` phone-safe error。

固定 fail-closed 字段：

- `source=software_proof`
- `proof_status=not_proven`
- `session_status=blocked_not_created`
- `validated_contract_fields=true|false`
- `webrtc_session_created=false`
- `answer_created=false`
- `ice_candidates_processed=false`
- `media_transport_connected=false`
- `video_track_received=false`
- `realtime_pose_stream_connected=false`
- `real_ros2_tf_connected=false`
- `safe_to_control=false`
- `sends_commands=false`
- `reads_hardware=false`
- `robot_control_executed=false`
- `delivery_success=false`

## 边界

该 receipt 只证明 relay HTTP 写入口和最小字段校验存在，不证明真实 RTC、媒体、实时地图、ROS2 `/tf` 或机器人控制链路。真实打通仍需要 offer/answer exchange trace、ICE selected pair trace、首帧视频证据、pose event stream trace、ROS2 `/tf` bridge trace、认证失败与超时路径证据。
