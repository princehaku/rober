# Sprint 2026.05.13_17-18 O5 External Evidence Intake Gate - Pre Start

## Sprint Meta

- sprint_type: epic
- Objective: Objective 5 云中转 + OSS/CDN 数据通路产品化
- 主目标：把 O5 从“本地 probe artifact 已就绪”推进到“真实外部证据材料可被安全接收、脱敏、汇总和交接”的 intake gate。
- 证据边界：默认 `software_proof_docker_external_evidence_intake_gate`；只有真实云/OSS/CDN/DB/queue/4G 外部材料存在且通过脱敏校验时，才允许记录为外部材料已接入，但仍不得等同真实送达、HIL 或生产完成。

## 上轮证据

- `OKR.md` 4.1 当前最低 Objective 是 Objective 5，约 67%；Objective 4 已在 `2026.05.13_16-17_mobile-web-browser-proof-gate` 上调到约 70%。
- `sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/final.md` 说明 O4 已完成本地 Chromium-family browser proof，并明确下一轮若继续 O5，必须引入真实 OSS/CDN、4G/SIM、云账号或 production DB/queue 外部证据，避免继续只增加本地 metadata 深度。
- `sprints/2026.05.13_12-13_cloud-db-queue-external-probe-gate/final.md` 已完成 DB/queue external probe bundle，但没有真实 DB/queue/cloud 连接证据。
- `sprints/2026.05.13_14-15_oss-cdn-live-probe-gate/final.md` 已完成 OSS/CDN live probe artifact、validator、preflight consumption、CLI/env 支持，但没有真实 OSS/CDN 凭证、真实云、4G/SIM 或公网 CDN 回源证据。

## 本轮进入条件

- 本机没有真实硬件，只有 Docker；本轮不碰 O1/HIL、WAVE ROVER、Nav2 实跑或真实送达。
- O5 是当前最低完成度 Objective，但外部凭证/云/4G/DB/queue 条件可能仍不可用，因此本轮需要先形成安全 intake gate，避免后续真实材料靠聊天或人工散落记录。
- 本轮如果没有真实外部材料，只能形成 blocked software proof，不上调 OKR。

## Owner

- Product Manager / OKR Owner：目标、验收口径和收口。
- User Touchpoint Full-Stack Engineer：external evidence intake artifact、CLI/preflight、phone-safe summary 和产品文档。
- Robot Platform Engineer：metadata-only compatibility fence，确保 intake metadata 不触发 robot command/status/ACK 行为。

## 风险

- 继续 O5 但仍无真实外部环境时，不能把本地 intake gate 写成真实云、真实 OSS/CDN、真实 DB/queue 或真实 4G/SIM。
- Intake bundle 不得泄漏 token、Authorization、OSS AK/SK、DB/queue URL、credential-bearing URL、root password、traceback、本地路径、ROS topic、`/cmd_vel`、串口或 WAVE ROVER 参数。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。
