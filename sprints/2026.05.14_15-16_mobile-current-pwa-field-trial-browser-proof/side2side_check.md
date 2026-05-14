# Sprint 2026.05.14_15-16 Mobile Current PWA Field Trial Browser Proof - Side2Side Check

sprint_type: epic

## PRD 对照

| PRD / Tech Plan 要求 | 验收结果 | 结论 |
| --- | --- | --- |
| current PWA browser proof 覆盖完整 field-trial 首屏组合 | 390x844 与 768x900 evidence 均 `passed=true`，summary 显示 field trial package/review/runbook/evidence record/verdict/retest execution 均 visible/copyable | 通过 |
| evidence boundary 使用 `software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate` | browser summary、mobile 文档、robot fence 和 OKR closeout 均使用该边界 | 通过 |
| 主操作保持 fail closed | summary 记录 `primary_actions_disabled=true`；Product 未发现本轮放行 Start/Confirm/Cancel 的证据 | 通过 |
| phone-safe 与 ACK 边界保持 | summary 记录 `phone_safe_status=passed`，文档保留 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven` | 通过 |
| Robot metadata-only fence 覆盖新 family | `mobile_current_pwa_field_trial_browser_proof*` tests/docs 已覆盖 metadata-only 与 mixed valid-command 场景 | 通过 |
| 不把 browser proof 冒充 O5、HIL 或 delivery success | sprint、OKR 和 progress log 均写明 local Chromium-family proof，不是真实外部、真实手机、HIL 或 delivery success | 通过 |

## 用户价值验收

本轮把当前 `mobile/web` PWA 的完整 field-trial 首屏组合重新落到本地浏览器可见证据。Product、Support 和后续真实设备验收可以用 390x844、768x900 的 JSON/PNG artifact 对照当前首屏，而不是只依赖单测或文档描述。

## OKR 最低优先级回顾

Objective 5 仍是当前最低完成度，约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料；tech-plan 中“不继续堆本地 O5 metadata，转向 O4 current PWA browser proof 缺口”的理由仍成立。

## 证据边界

- 可计入 Objective 4 的证据：`software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate`，即 local Chromium-family proof + robot metadata-only fence。
- 不可计入的证据：真实 iPhone/Android、production app、真实 PWA install prompt/user choice、O5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion、delivery success。

## 结论

验收通过。建议 Objective 4 从约 91% 谨慎上调到约 92%；Objective 5 保持约 68%；Objective 1/2/3 不调整。
