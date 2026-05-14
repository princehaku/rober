# Sprint 2026.05.14_14-15 Mobile Field Trial Retest Execution Gate - Pre Start

sprint_type: epic

## 上轮状态

上一轮 `2026.05.14_13-14_mobile-field-trial-evidence-verdict` 已完成 `software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate`。证据显示：

- `OKR.md` 4.1 中 Objective 5 仍最低，约 68%，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration 等外部材料。
- 上轮 `final.md` 明确 verdict / retest / material request package 只是 Docker/local mobile software proof，不是真实手机验收、production app、真实 PWA prompt、O5 external proof、HIL 或 delivery success。
- 当前主机没有真实硬件，只有 Docker，不能补 O1 HIL，也不能补 O5 真实外部证据。

## 本轮目标

按 stop rule，不继续堆 O5 本地 metadata；本轮转向 Objective 4 的下一段可执行链路：把 `mobile_real_device_field_trial_evidence_verdict*` 的 `retest_request` 与 `material_request` 推进为可填写、可复制、可被机器人侧忽略的 `mobile_real_device_field_trial_retest_execution*` 复测执行结果包。

本轮只声明 `software_proof_docker_mobile_real_device_field_trial_retest_execution_gate`，不声明真实设备验收、production app readiness、真实 PWA install prompt/user choice、真实云/4G、OSS/CDN、DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success。

## Owner

- Product Manager / OKR Owner：维护本轮 OKR 口径、验收边界和 closeout。
- User Touchpoint Full-Stack Engineer：实现手机首屏复测执行结果 panel、summary 与 whitelist-only copy。
- Robot Platform Engineer：补 robot metadata-only fence，证明该 family 不触发 command、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。

## 验收口径

- Full-stack 能在 `mobile/web` 首屏展示并复制 `mobile_real_device_field_trial_retest_execution*` family。
- 该 family 从 verdict 的 retest/material request 派生或消费，不绕过 `safe_to_control=false`、ACK 非 delivery success、`not_proven` 和 whitelist-only copy。
- Robot fence 证明 retest execution metadata 不改变 `trashbot.remote.v1` command envelope，也不推进 ACK/cursor。
- 文档和 OKR 明确 O5 仍最低但外部材料缺失，本轮是 O4 软件证明。

## 风险

- 这不是新的真实手机验收；如果没有真实 iPhone/Android、production app、真实 PWA prompt/user choice 或现场材料，本轮不能把 O4 说成真实通过。
- 这也不是 O5 外部云证明；不能上调 O5。
- 验证只跑围栏命令，不做广泛测试扩张。
