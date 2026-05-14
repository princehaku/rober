# Sprint 2026.05.14_13-14 Mobile Field Trial Evidence Verdict - Side2Side Check

sprint_type: epic

## 对照基线

上轮 `2026.05.14_12-13_mobile-field-trial-evidence-recorder` 已能填写、展示、复制、归档 `mobile_real_device_field_trial_evidence_record*`，但仍需要人工判断哪些材料缺失、是否可进入复核、下一轮应补什么。

本轮目标是把 record package 推进成 `mobile_real_device_field_trial_evidence_verdict*`，让现场证据从“记录材料”进入“复核结论 + retest/material request”阶段，同时保持 fail-closed 和 metadata-only 边界。

## 用户价值核对

- 普通手机用户与现场支持人员现在可以围绕同一份 phone-safe verdict package 对齐缺口和下一步补证材料。
- Product/Support 不再只拿到散落记录字段，而是能看到 verdict status、missing evidence、retest request、material redaction status 和 `not_proven` 边界。
- 主操作仍不因 verdict package 放行；`safe_to_control=false` 与 `accepted_processing_only_not_delivery_success` 防止把材料复核误读成 delivery success。

## OKR 映射

- Objective 4：本轮推进真实手机验收材料链路，从 evidence record 进入 evidence verdict / retest / material request package。可谨慎上调到约 90%。
- Objective 5：仍最低约 68%，但本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；不调整。
- Objective 1/2/3：未新增真实硬件、HIL、Nav2/fixed-route、delivery action 或任务复盘证据；不调整。

## 验收口径核对

通过项：

- `mobile_real_device_field_trial_evidence_verdict*` 首屏 panel 和 copy package 已由 Full-stack worker 验证。
- Robot metadata-only fence 已覆盖 verdict family，证明不触发 command、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- 文档和 OKR 使用统一 evidence boundary：`software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate`。
- Copy / verdict 口径包含 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`。

未通过或不在本轮范围：

- 未做真实手机设备验收。
- 未做 production app 验收。
- 未做真实 PWA install prompt / user choice 验收。
- 未做真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 验收。
- 未做 Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success 验收。

## 阶段结论

本轮满足 PRD 与 tech-plan 的产品验收口径：verdict package 已把现场材料复核链路向前推进一小步，且没有扩大控制语义或证据声明。Objective 4 可从约 89% 谨慎上调到约 90%；Objective 5 仍按外部材料缺口保持约 68%。
