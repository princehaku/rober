# Sprint 2026.05.14_01-02 Mobile PWA Install Prompt Evidence Gate - Side2Side Check

## 验收对象

- sprint_type: epic
- 功能名：`mobile-pwa-install-prompt-evidence`
- 证据边界：`software_proof_docker_mobile_pwa_install_prompt_evidence_gate`
- 目标 Objective：Objective 4 手机用户体验与低成本量产边界

## 用户价值对照

本轮产品北极星是让普通手机用户只通过手机入口理解任务状态和验收缺口。A/B 交付后，PWA install prompt 不再只存在于风险列表，而是在 `mobile/web/` 中成为可见、可复制、可交接的 evidence gate。

对照结果：

- 测试人员可以看到 install prompt capture status、user outcome、display-mode/installability/offline shell、manifest/service worker、production app readiness、safe-to-control 和 `not_proven`。
- 支持人员可以接收 phone-safe package，并从 evidence boundary、ACK 语义、recovery hint 和 not-proven 列表判断下一步需要真实手机设备、真实 iPhone/Android、production app、真实 PWA install prompt、云/4G 或 Robot 证据。
- Robot compatibility fence 已证明这些内容是 phone/support metadata，不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence 或 delivery success。

## P0 验收核对

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| PWA install prompt evidence 在手机验收区域可见 | 通过 | Task A 改动 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css` 并由 `mobile.test_mobile_web_entrypoint` 覆盖。 |
| 复制包 phone-safe 且保留 ACK 不是 delivery success | 通过 | Task A fixture/test/docs 覆盖；Task B docs/interfaces 明确 metadata-only。 |
| 缺真实 PWA install prompt 时显示 `not_proven` | 通过 | Task A package 与 docs 保留 `not_proven`，Product OKR 口径同步保留。 |
| Start/Confirm/Cancel 不因 install prompt evidence 启用 | 通过 | Task A fail-closed 断言；Task B metadata-only fence 不触发 robot action。 |
| Robot compatibility fence 证明 metadata-only | 通过 | Task B remote bridge/protocol targeted unittest `Ran 125 tests in 63.139s OK`。 |

## 边界核对

本轮只通过 `software_proof_docker_mobile_pwa_install_prompt_evidence_gate`。以下能力未证明：

- 真实手机设备。
- 真实 iPhone/Android device behavior。
- production app。
- 真实 PWA install prompt/user choice。
- 真实 public HTTPS/TLS。
- 4G/SIM。
- OSS/CDN live traffic。
- production DB/queue。
- Nav2/fixed-route。
- WAVE ROVER。
- HIL。
- 真实 dropoff/cancel completion。
- 真实 delivery。

ACK、HTTP accepted、receipt、evidence package、handoff 和 install prompt evidence 都仍是 accepted/processing/support metadata only，不是 delivery success。

## OKR 最低优先级回顾

计划阶段确认最低 Objective 是 Objective 5，约 68%。本 sprint 没有针对 Objective 5，因为继续上调 O5 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。A/B 结果没有产生这些材料，因此 Objective 5 保持约 68%。

本轮转向 Objective 4 的理由仍成立：它补齐了真实设备/PWA 验收前的 install prompt evidence gate，为后续真实手机设备和真实 PWA install prompt/user choice 验收提供可复制证据包。

## Product 验收结论

Product 接受本 sprint 作为 Objective 4 的软件证据推进。Objective 4 可从约 77% 谨慎上调到约 78%；Objective 5 不上调；Objective 1/2/3 不调整。

下一步优先级仍按 OKR 4.1 排序：若能拿到真实外部 O5 材料，优先推进 Objective 5；若没有，则继续推进 Objective 4 的真实 iPhone/Android 设备、production app 或真实 PWA install prompt/user choice 验收。
