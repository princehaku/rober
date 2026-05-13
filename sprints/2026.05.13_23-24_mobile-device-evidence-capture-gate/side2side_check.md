# Sprint 2026.05.13_23-24 Mobile Device Evidence Capture Gate - Side2Side Check

## 验收结论

Product 验收通过，证据边界保持为 `software_proof_docker_mobile_device_evidence_capture_gate`。A/B 输出符合 `prd.md` 和 `tech-plan.md`：前端新增 phone-safe 手机设备证据采集与复制入口，Robot 侧只补 metadata-only fence，生产 robot runtime 未扩大。

## 对照检查

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 首屏存在“手机设备证据采集”面板 | 通过 | Task A 更新 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`，unittest 覆盖 `mobileDeviceEvidenceTitle`、copy button、schema 和 boundary。 |
| evidence package 字段 phone-safe | 通过 | Task A 覆盖 viewport、touch target、display-mode/PWA、service worker/offline shell、client timestamp、ACK 语义、safe copy、`not_proven`；`mobile/README.md` 和 `docs/product/mobile_user_flow.md` 写明白名单与禁入字段。 |
| 主操作不因设备证据包自动放开 | 通过 | Task A 文档与实现保持 Start/Confirm/Cancel 依赖既有 readiness、acceptance bundle 和 command_safety；证据包本身只是 support metadata。 |
| Robot metadata-only fence | 通过 | Task B tests 证明 `mobile_device_evidence_capture`、summary、package 不触发 collect/confirm_dropoff/cancel、不 POST ACK、不推进或持久化 cursor。 |
| valid command mixed metadata 语义 | 通过 | Task B tests 证明混入 metadata 时只执行 `trashbot.remote.v1` command envelope，不把 metadata 写入 ACK/status/cursor。 |
| not-proven 文案 | 通过 | OKR、progress log 和本 sprint 文档均明确真实 iPhone/Android、production app、真实 PWA install prompt、真实云/4G、Nav2/fixed-route、WAVE ROVER、HIL、真实 delivery 未证明。 |

## 证据边界

本轮只证明 Docker/local mobile software proof 与 robot metadata-only fence。

不证明：

- 真实 iPhone/Android device behavior。
- production app。
- 真实 PWA install prompt。
- 真实公网 HTTPS/TLS。
- 4G/SIM。
- OSS/CDN live traffic。
- production DB/queue。
- production worker/migration。
- Nav2/fixed-route。
- WAVE ROVER。
- HIL。
- 真实 dropoff/cancel completion。
- 真实 delivery。

ACK、HTTP accepted、receipt、terminal confirmation 和 evidence package 仍只是 accepted/processing/support metadata，不是 delivery success。

## 收口判断

Objective 4 可从约 75% 谨慎上调到约 76%。Objective 5 因没有真实外部 O5 材料，保持约 68%。Objective 1/2/3 不调整。
