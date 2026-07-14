# PRD - O7 Voice Runtime Offline Smoke

## 背景

O7 已经有 voice fixture preview、voice/TTS draft event-write、speaker ACK/failure event-write 和 voice runtime preflight。缺口不是再加一个只读按钮，而是把安全 preflight 结果消费为可复验的离线 runtime smoke trace，让后续真实 microphone/speaker/provider smoke 有明确输入、输出和 fail-closed 对照。

## 用户价值

普通用户和 operator 需要知道语音链路当前能否进入下一步验证。这个 smoke trace 不证明真实语音，但能把“配置可检查”推进到“同一任务下的离线语音 runtime 流程可复盘”，减少下一轮接真实设备或 provider 时的联调歧义。

## 需求

1. 新增 O7 本地 endpoint 或等价 Node-side builder，例如 `GET /api/o7/voice-runtime/offline-smoke`。
2. 输入只允许 safe local/offline mode 或本地 JSON fixture/config，不允许 URL、凭证、设备路径、音频 payload、生产云、ROS 控制字符串或危险 true claim。
3. 输出 schema 固定为 `trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_result.v1`。
4. 输出必须包含 selected task identity、proof boundary、preflight-derived status、smoke trace events、blocked reasons、not-proven list 和 next required evidence。
5. 固定 false fields 必须包含：
   - `real_voice_api_connected=false`
   - `real_asr_tts_runtime_connected=false`
   - `tts_send_enabled=false`
   - `speaker_dispatch_enabled=false`
   - `real_speaker_ack_proven=false`
   - `microphone_opened=false`
   - `speaker_playback_opened=false`
   - `safe_to_control=false`
   - `delivery_success=false`
   - `robot_control_executed=false`
   - `connects_cloud_production=false`
6. UI/API 文档必须说明它不重复 preflight，不发送 TTS，不播放音频，不写 O6 archive events，不能当作真实 runtime 证据。

## 非目标

- 不连接真实 ASR/TTS provider。
- 不打开麦克风或喇叭。
- 不发 TTS、不播放音频、不声明 real speaker ACK。
- 不访问生产云、OSS/CDN、DB/queue 或 4G。
- 不触发机器人控制、Nav2、WAVE ROVER UART、`/cmd_vel` 或 `/api/base/manual`。

## 验收口径

Product 只接受 deterministic local/offline smoke trace。任何真实能力字段被置 true、任何 URL/凭证/设备路径/音频 payload 被透出、或实现只是重复上一轮 preflight 而没有 trace 事件，都必须退回修复。
