# Sprint 2026.05.12_24-25 Phone Voice Prompt Readiness Gate - Final

## 状态

- 阶段：final
- 收口时间：2026-05-12 24:50 Asia/Shanghai
- 主线 Objective：O5 手机体验与量产边界
- Evidence boundary：`software_proof_docker_phone_voice_prompt_readiness_gate`
- 结论：本轮完成 local/Docker phone voice prompt readiness gate，按保守口径更新 O5。

## 用户价值和产品北极星

用户价值：普通用户在手机首屏能看到当前应播报/朗读的提示词、触发状态、是否需要人工帮助、播放能力是否已证明，以及 ACK 不是送达成功的边界。

产品北极星：普通用户只用手机完成垃圾交付；本轮把语音提示从散落字段推进为可见、可测、可交接的 readiness gate，但不冒充真实喇叭/TTS 或真实手机验收。

## OKR 映射和 KR 更新

- O5 / KR2：提示词与状态触发点落地为 `trashbot.voice_prompt_readiness.v1`。
- O5 / KR6：跨楼层 assisted delivery 的 `requesting_floor_help` 中文求助提示进入首屏/API/diagnostics。
- O5 / KR7：fallback 手机首屏以 phone-safe 文案展示 prompt readiness、human help、not_proven，不暴露 raw ROS/hardware/credential 细节。
- O6：只保留 compatibility fence 价值，不提升真实云/4G 进度。

OKR 进度建议：

- O5：约 50% -> 约 52%，证据边界 `software_proof_docker_phone_voice_prompt_readiness_gate`。
- O6：保持约 51%。
- O1/O2/O3/O4：不提升。

## 本轮核心抓手

- Task A 完成 `trashbot.voice_prompt_readiness.v1`，并在 `/api/status.voice_prompt_readiness`、`/api/status.phone_readiness.voice_prompt_readiness`、`/api/diagnostics.voice_prompt_readiness` 同口径暴露。
- fallback HTML 首屏展示 current prompt、trigger、human help、`playback_ready=false`、safe copy 和 not_proven。
- Task B 完成 remote bridge/operator compatibility fence，确认 metadata 不污染 command/status/ACK envelope，不触发 robot action、不 ACK、不推进 cursor。

## 实际改动

- `OKR.md`
- `sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/tech-done.md`
- `sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/side2side_check.md`
- `sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/final.md`

Task A/Task B 的工程改动由对应 Engineer 完成，详见 `tech-done.md`。

## 验证结果

Engineer 已完成：

- Task A：HTTP/static unittest `Ran 50 tests in 21.150s OK`；`py_compile` exit 0；scoped diff check exit 0。
- Task B：remote bridge/diagnostics unittest `Ran 82 tests in 20.943s OK`；`py_compile` exit 0；scoped diff check exit 0。

Product closeout 验收：

- `test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md`
  - exit 0
- `git diff --check -- OKR.md sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/tech-done.md sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/side2side_check.md sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/final.md`
  - exit 0

## 剩余风险和未完成事项

- 没有真实喇叭/TTS、麦克风或真实播放证据。
- 没有真实手机设备、production app、真实用户实机验收。
- 没有真实云/4G、HTTPS/TLS 公网入口、production account、OSS/CDN 实流量。
- 没有 Nav2/fixed-route 实跑、WAVE ROVER、真实串口反馈、HIL 或真实送达。
- ACK 仍只表示 accepted/processing evidence，不等于 delivery success，也不等于 prompt 已真实播放。

## 下一步建议

- 若仍是 Docker-only 环境，下一轮按 live `OKR.md` 重排；O5 已约 52%、O6 约 51%，可优先补 O6 生产化缺口或继续 O5 真实设备前置 gate，但必须保持 software proof 边界。
- 若具备真实手机设备或音频硬件，优先补 O5 真实手机浏览器 + speaker/TTS playback 验收。
- 若具备真实云/4G 条件，优先补 O6 真实公网入口、生产 DB/queue、4G/SIM 和 OSS/CDN 实流量证据。
