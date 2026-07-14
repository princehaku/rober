# Pre Start - O7 Voice Runtime Offline Smoke

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke/`
- Started at: 2026-07-14 12:35 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o7_voice_runtime_offline_smoke_only`
- Target OKR: O7/O6 voice touchpoint evidence, while O5 remains the lowest blocked Objective.

## 上轮未完成项和 Blocker

上轮 `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/` 已完成 `GET /api/o7/voice-runtime/preflight`，并明确下一步不能重复包装 preflight。可计分的下一跳仍需要 success-class O5 production/cloud evidence，或 explicit same-window live route/HIL/delivery/operator evidence，或授权真实 voice runtime smoke。

本轮主节点只读检查发现当前环境没有 `ROBER_CDN_PROBE_BASE_URL`、`O7_VOICE_RUNTIME_CONFIG_JSON` 或 `O7_VOICE_RUNTIME_MODE`，因此不能声称生产云、真实 voice provider、真实麦克风或真实喇叭证据已经存在。

## 本轮目标

在不访问生产云、不打开麦克风/喇叭、不发送 TTS、不控制机器人的前提下，把上一轮 preflight 推进为 O7 本地离线 voice runtime smoke trace：

- 用安全 local/offline 配置或 fixture 驱动 smoke。
- 产出同一 selected task 的 runtime trace summary。
- 明确关联 voice/TTS draft 与 speaker ACK/failure 的下一步证据需求。
- 保持所有真实能力字段为 false。

## Owner 和边界

- `full-stack-software-engineer` 负责实现、验证、修复和 `tech-done.md`。
- 主节点只做计划、派单、验收和最终汇总。
- 不涉及 WAVE ROVER、UART、Nav2、`/cmd_vel`、`/api/base/manual`、NavigateToPose、生产云或真实音频设备。

## 预期收口

本轮如果成功，只接受为 `software_proof_o7_voice_runtime_offline_smoke_only`。O5 继续约 `85%`，O1 继续约 `94%`，O6/O7 继续约 `93%`，主百分比不调整，KR `不归档`。
