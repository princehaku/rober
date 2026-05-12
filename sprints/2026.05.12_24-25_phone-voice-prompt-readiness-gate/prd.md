# Sprint 2026.05.12_24-25 Phone Voice Prompt Readiness Gate - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 主线 Objective：O5 手机体验与量产边界
- Evidence boundary：`software_proof_docker_phone_voice_prompt_readiness_gate`

## 问题

O5 已有 phone readiness、command safety、PWA shell、task-flow readiness 和 support handoff。普通用户已经能从手机首屏理解连接、目的地、装载确认、发车、状态解释和失败交接。

剩余缺口是语音提示仍停留在散落字段：`docs/product/mobile_user_flow.md` 明确 `speaker_prompt` 是 future speaker/TTS layer 的 contract，local gateway does not play audio。用户在电梯求助、目标楼层未确认、失败或人工接管场景下，需要看到当前应该播报/朗读的中文提示、触发原因、是否需要人工接管，以及这不是实际喇叭/TTS 验证。

## 用户价值和产品北极星

用户价值：手机首屏直接告诉普通用户“小车现在应该说什么、为什么说、我是否要帮忙、这条提示是否已真实播放”。这降低跨楼层 assisted delivery 和异常处理的理解成本。

北极星：普通用户只用手机交付垃圾。语音/喇叭能力的产品路径应先有稳定提示 contract 和手机可见 readiness，再补真实喇叭/TTS、真实手机设备和用户实机验收。

## OKR 映射

- O5 / KR2：提示词和状态触发点从表格/字段推进到 `trashbot.voice_prompt_readiness.v1` readiness gate。
- O5 / KR6：电梯内求助按楼层、目标楼层未确认、出口不安全、需要人工接管等语音/手机体验进入首屏。
- O5 / KR7：本地 fallback 首屏中文优先、可直接理解，不暴露 raw JSON、ROS topic 或硬件参数。
- O6 / KR6：只复用 remote readiness/ACK/metadata 边界，验证 voice metadata 不影响 command/status/ack 语义。

## KR 拆解

- KR5.1：新增 `trashbot.voice_prompt_readiness.v1` schema，包含 `schema_version`、`evidence_boundary`、`current_prompt`、`prompt_language`、`trigger_state`、`trigger_reason`、`requires_human_help`、`playback_ready`、`safe_phone_copy`、`ack_semantics`、`not_proven`。
- KR5.2：`/api/status` 顶层与 `phone_readiness.voice_prompt_readiness` 暴露同一 voice prompt readiness summary；旧客户端可忽略。
- KR5.3：`/api/diagnostics.voice_prompt_readiness` 暴露同一摘要，便于 support handoff 和工程诊断复现提示语义。
- KR5.4：本地 fallback 首屏展示当前应播报/朗读的中文提示、触发状态、人工接管状态和未证明边界。
- KR5.5：覆盖常见状态：待装载、准备出发、行驶中、电梯等待开门、电梯求助按楼层、等待目标楼层、目标楼层未确认、出口不安全、到达、失败、需要人工接管。
- KR5.6：敏感字段过滤：不得暴露 token、Authorization、OSS AK/SK、DB/queue URL、raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、local path、traceback 或完整 artifact。
- KR5.7：ACK 文案保持保守：accepted/processing evidence only，不等于 delivery success，也不等于 prompt 已真实播放。

## 范围

### In Scope

- 本地 `operator_gateway` API 和静态 fallback 页面。
- 复用已有 `/api/status`、`/api/diagnostics`、`phone_readiness`、`phone_copy`、`speaker_prompt`、`elevator_assist`、`command_safety`、support handoff 和 ACK 语义。
- 更新 `docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md` 中 voice prompt readiness contract。
- 最小围栏测试、`py_compile` 和 scoped diff check。

### Out of Scope

- 真实喇叭播放、TTS engine、音频设备、麦克风唤醒或声学验收。
- 真实 production app 或 native app。
- 真实手机设备 Safari/Chrome 验收。
- 真实云、真实 4G/SIM、HTTPS/TLS 公网入口、真实 OSS/CDN 流量。
- 生产 DB/queue、多实例一致性、真实 production transaction isolation。
- Nav2/fixed-route 实跑、WAVE ROVER 运动、真实串口反馈、HIL 或真实送达。
- 新硬件、硬件参数、WAVE ROVER 协议改动。

## 优先级

- P0：voice prompt readiness schema/API/diagnostics/首屏入口落地，字段脱敏，ACK/not_proven 口径正确。
- P1：覆盖电梯 assisted delivery 和人工接管相关中文提示，且明确 `playback_ready=false` 或等价未证明边界。
- P2：support handoff 可以引用 voice prompt readiness，但不能把它写成真实售后系统、真实 TTS 或生产 app。

## 验收口径

本轮可接受的完成证据：

- API 返回 `trashbot.voice_prompt_readiness.v1`，并在 `/api/status`、`phone_readiness`、`/api/diagnostics` 三处保持一致。
- 首屏有 phone-safe voice prompt readiness 区域；用户能看到当前提示、触发状态、人工接管要求和未证明边界。
- 测试覆盖敏感字段过滤、ACK 不是送达成功、prompt readiness 不是真实播放、metadata 不触发 robot action、不污染 `trashbot.remote.v1` command/status/ack envelope。
- 文档同步更新 product/interface contract。
- Sprint closeout 更新 `tech-done.md`、`side2side_check.md`、`final.md`；若证据成立，`OKR.md` 只能保守记录 O5 software proof 进展。

## 责任 Engineer

- `full-stack-software-engineer`：Task A 主实现，负责 API、HTML、测试和 product/interface 文档。
- `robot-software-engineer`：Task B remote bridge/operator compatibility fence，负责 command envelope / ACK / cursor/action 不变性验证。
- `product-okr-owner`：Product closeout，负责 side2side、final、OKR 保守更新和证据边界核对。

## 风险和需要补齐的证据链

- voice prompt readiness 容易被误写成真实喇叭/TTS；closeout 必须明确它只是 local/Docker software proof。
- elevator assisted delivery 的语音提示容易被误读为真实电梯闭环；必须保留 no HIL、no real phone、no real audio playback 边界。
- diagnostics/support bundle 里可能泄露 local path、ROS topic 或硬件细节；Task A 必须只暴露 phone-safe refs 和摘要。
- ACK 文案容易被误读为任务成功或提示已播放；Task B 必须验证 ACK 仍只是 command envelope evidence。
- 当前没有真实手机设备和真实喇叭/TTS，不能补 O5 最关键的实机用户验收；本轮只能把提示语义做成可见、可测、可交接的 readiness gate。
