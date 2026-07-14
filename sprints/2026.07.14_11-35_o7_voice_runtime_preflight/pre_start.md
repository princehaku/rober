# Pre Start - O7 Voice Runtime Preflight

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/`
- Created at: 2026-07-14 11:35 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Target Objective: O7 PC 端运营调试与数据训练平台；同时避免继续重复消费 O5 support-only blocker。
- Proof boundary: `software_proof_o7_voice_runtime_preflight_only`
- Product direction: continue with a bounded O7 voice runtime preflight plan, with no OKR percentage lift unless implementation later proves a materially stronger current-run or production evidence class.

## 背景和上轮输入

最新收口 `sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write/final.md` 已接受 voice speaker ACK/failure event-write 为 local/mock software proof only。该轮明确说明下一轮不能重复 voice speaker ACK/failure、本地 event-write、operator/browser artifact、terminal-result wrapper、readback/export wrapper、CDN/TLS 4xx 或 O5 operator gate。

O5 当前约 `85%`，仍是 `OKR.md` 4.1 中最低 Objective；主要缺口是真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 和真实手机/browser 证据。当前环境没有真实生产云或硬件授权，继续 O5 support-only 包装会重复消费同一 blocker。

因此本轮选择一个不同的、更靠近用户触点能力的 O7 real voice runtime preflight 软件证明：只检查 PC/Node 环境、配置读取、运行时 preflight 状态和 fail-closed 输出，不调用真实云，不打开麦克风或喇叭，不发送 TTS，不控制机器人。

## 用户价值和产品北极星

用户价值：普通用户最终需要用手机、语音和喇叭理解小车状态并完成送垃圾闭环。本轮不交付真实语音能力，但它把 PC/O7 的 voice runtime 前置检查变成可复验的软件证据，减少后续接入真实 ASR/TTS、speaker dispatch 或现场语音提示时的盲试。

产品北极星：让 rober 从工程 demo 走向普通用户可理解、可操作、可复盘的送垃圾机器人。voice runtime preflight 只有在后续接上真实运行时、现场任务和送达证据后才可能贡献主闭环；本轮仅铺好 fail-closed 的运行时准入检查。

## OKR 映射和方向判断

- O5：继续约 `85%`。本轮不针对 success-class production/cloud evidence，因此不提升、不归档。
- O6/O7：继续约 `93%`。本轮面向 O7 PC voice runtime preflight，但计划阶段不实施、不计进度。
- O1：继续约 `94%`。本轮不涉及 WAVE ROVER、HIL、route execution 或 safe-to-control。
- Direction judgment: `调整`。在最低 O5 被真实生产云/硬件授权 blocker 锁住且近几轮已连续 support-only 后，短期从 O5 包装切到 O7 voice runtime preflight；这不是替换 O5 目标，而是避免重复消费 blocker。

## KR 拆解、更新和历史归档

- 当前 KR 更新：本轮只创建 epic sprint 计划，不更新 `OKR.md`，不移动当前 KR。
- 已完成 KR 历史归档：无。本轮没有可归档 KR；原因是证据边界固定为 `software_proof_o7_voice_runtime_preflight_only`，且尚未产生实现、测试、真实 runtime、生产云、HIL、route execution 或 delivery/operator 证据。
- 历史记录位置：待实现和验收完成后，若仍为 software proof，应在本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md` 记录 `KR 不归档`；如未来接入真实 voice runtime 和现场任务 evidence，再由 `OKR.md` 对应 Objective 历史区承接。

## 本轮核心抓手

为 `full-stack-software-engineer` 准备一个单 owner 实施计划：增加 O7 PC/Node voice runtime preflight 软件证明，产出可由测试复验的安全摘要字段，并把所有真实能力声明固定为 false。

本轮计划必须要求实现侧输出这些边界字段：

- `real_voice_api_connected=false`
- `real_asr_tts_runtime_connected=false`
- `tts_send_enabled=false`
- `speaker_dispatch_enabled=false`
- `safe_to_control=false`
- `delivery_success=false`

## 需要做什么

1. Product Owner 创建本轮 epic sprint 计划文档：`pre_start.md`、`prd.md`、`tech-plan.md`。
2. 下一阶段由 `full-stack-software-engineer` 单线闭环实现、测试、修复，并创建 `tech-done.md`。
3. 实现不得触碰真实云、真实音频输入输出、TTS 发送、speaker dispatch、机器人控制或硬件路径。
4. 验收只能接受 software preflight evidence，不能接受 real voice runtime、audio playback、delivery success、safe-to-control 或 O5 production claim。

## 优先级和验收口径

- Priority: P0 for the next implementation sprint because it is the selected non-repeating O7 lane after O5 support-only blockers.
- Acceptance summary: preflight can read bounded config/env state, report explicit readiness/fail-closed status, expose the fixed false fields, and pass targeted unit/build/lint checks.
- Rejection summary: any implementation that calls real ASR/TTS/cloud APIs, opens microphone/speaker devices, sends TTS, dispatches speaker output, sends robot commands, or marks delivery/safety/runtime true must be rejected.

## 对应责任 Engineer

- Primary owner: `full-stack-software-engineer`
- Product owner: `product-okr-owner`
- Consulting owners: none for this plan. Hardware, Robot Software, and Algorithm should not be pulled in unless implementation later crosses into audio hardware, robot control, ROS2 runtime, route execution, or HIL.

## 风险、阻塞和证据链缺口

- Main blocker: no real production cloud or hardware authorization in this environment.
- Evidence gap: no real ASR/TTS provider connection, no microphone input, no speaker playback, no TTS dispatch, no real speaker ACK, no delivery/operator acceptance, no route execution, no HIL.
- Scoring risk: this sprint can only be support/software proof. It must not raise O5/O6/O7 percentages by itself.
- Repeat-consumption guard: do not implement another voice speaker ACK event write, TTS draft event write, operator dropoff artifact, bounded-route terminal-result wrapper, or O5 support-only readiness packet.

## Sprint 文档要求

This epic sprint starts with:

- `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/pre_start.md`
- `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/prd.md`
- `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/tech-plan.md`

Do not pre-generate:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
