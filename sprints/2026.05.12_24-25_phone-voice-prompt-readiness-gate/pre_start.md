# Sprint 2026.05.12_24-25 Phone Voice Prompt Readiness Gate - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 24:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主线 Objective：O5 手机体验与量产边界
- 目标 evidence boundary：`software_proof_docker_phone_voice_prompt_readiness_gate`
- 当前主机约束：macOS + Docker-only；无真实手机设备、无 production app、无真实喇叭/TTS、无真实云/4G、无真实 WAVE ROVER/HIL。

## 开工依据

- 用户要求“开始下一轮迭代，根据近期 PR 和评审，建议下一步应深入的OKR”，每条建议必须基于具体证据，并且“用team继续完成OKR，重新在功能往前走”。
- `OKR.md` 当前 live 快照显示 O5 约 50%、O6 约 51%，O1/O2/O3/O4 约 74-76%；本轮最低且 Docker-only 可推进的是 O5。
- `sprints/2026.05.12_22-23_phone-support-bundle-gate/final.md` 已完成 O5 phone support handoff，剩余缺口仍是无真实手机设备、无 production app、无普通用户实机验收。
- `sprints/2026.05.12_23-24_remote-transaction-isolation-gate/final.md` 只完成 O6 metadata summary 和 remote bridge 兼容围栏，不能替代 O5 手机体验进展。
- `docs/product/mobile_user_flow.md` 写明 `speaker_prompt` 仍是 future speaker/TTS layer 的 contract，local gateway does not play audio；因此本轮不做真实播放，只把提示词 readiness 变成 phone-safe gate。

## 用户价值和产品北极星

用户价值：普通用户在手机首屏能看懂“小车现在应该说什么、为什么要说、是否需要人工接管、哪些播放能力还没证明”。特别是跨楼层 assisted delivery 中，用户不应该只看到散落的 `speaker_prompt` 字段，而应该看到可执行的中文提示和状态解释。

北极星：普通用户只用手机完成垃圾交付；当小车需要通过语音请求旁人帮忙按电梯、提示失败或提示人工接管时，手机端先把提示语义讲清楚，再等待未来真实喇叭/TTS 和真实手机验收补证。

## OKR 映射

- O5 / KR2：语音/喇叭提示词和状态触发点。本轮把待装载、准备出发、行驶中、到达、失败、需要人工接管、电梯求助等提示词整理成 `trashbot.voice_prompt_readiness.v1`。
- O5 / KR6：跨楼层 trash delivery 的手机/语音体验。本轮把电梯内求助按楼层、目标楼层未确认、需要人工接管等提示在手机首屏可见，并明确是否需要人工介入。
- O5 / KR7：手机端 UI 美观且能直接使用。本轮要求 fallback 首屏显示 voice prompt readiness，中文优先，不暴露 raw JSON、ROS topic 或硬件细节。
- O6：只作为 remote bridge/operator compatibility fence，确认新增 voice metadata 不污染 command/status/ack envelope，不触发 robot action、不 ACK、不推进 cursor；不提升真实云或 4G 证据。

## 本轮核心抓手

创建 `trashbot.voice_prompt_readiness.v1` software proof：

- 从现有 `phone_copy`、`speaker_prompt`、`elevator_assist`、`phone_readiness`、`command_safety` 和 support handoff 语义中生成 phone-safe voice prompt readiness。
- 在 `/api/status`、`phone_readiness.voice_prompt_readiness` 和 `/api/diagnostics.voice_prompt_readiness` 暴露同口径摘要。
- 在本地 fallback 首屏展示当前应播报/朗读的中文提示、触发状态、人工接管要求、ACK 边界和 not_proven。
- 明确过滤 raw ROS topic、串口、baudrate、WAVE ROVER 参数、token、Authorization、OSS/DB/queue URL、local path、traceback 和完整 artifact。

## 阻塞和边界

- 本轮不能证明真实喇叭、真实 TTS、真实麦克风、真实手机设备或 production app。
- 本轮不能证明真实云、真实 4G/SIM、HTTPS/TLS 公网入口、真实 OSS/CDN 流量、生产 DB/queue 或生产 transaction isolation。
- 本轮不能证明 Nav2/fixed-route 实跑、WAVE ROVER 运动、真实串口反馈、HIL 或真实垃圾送达。
- ACK 仍只表示 command accepted/processing evidence，不表示送达成功。

## Owner

- Task A 主实现：`full-stack-software-engineer`
- Task B robot compatibility fence：`robot-software-engineer`
- Product closeout：`product-okr-owner`

## Sprint 文档计划

本阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现完成后再由对应 owner 更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
