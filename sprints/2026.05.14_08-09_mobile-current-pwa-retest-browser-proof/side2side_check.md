# Sprint 2026.05.14_08-09 Mobile Current PWA Retest Browser Proof - Side-by-Side Check

## 对照结论

- sprint_type: epic
- 对照目标：把上一轮“真实设备复测请求”panel 纳入当前 `mobile/web` PWA 的本地 Chromium-family browser proof，并保持 Robot metadata-only 控制边界。
- 结论：Task A/B 均满足本轮验收口径；本轮可按 `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate` 收口。

## 用户价值和产品北极星

- 用户价值：支持/验收人员可以通过本轮截图与 JSON evidence 复查当前 PWA 首屏是否包含真实设备复测请求、关键 phone-safe 边界、ACK 非 delivery success、Diagnostics / Support Handoff 和 fail-closed 主操作。
- 产品北极星：手机仍是普通用户唯一入口；本轮只证明本地浏览器里当前 PWA 的可见性与边界，不把 browser proof、真实设备复测请求或 ACK 解释为真实送达。

## OKR 映射

- Objective 4：Task A 的两组 viewport browser proof 与 Task B 的 Robot metadata-only fence 支持 O4 从约 84% 保守上调到约 85%。
- Objective 5：仍是最低 Objective（约 68%），但本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 外部材料，因此保持不变。
- Objective 1/2/3：没有硬件、HIL、Nav2/fixed-route、task_orchestrator 或真实 delivery 新证据，因此保持不变。

## 验收对照

| 验收项 | 证据 | 结论 |
| --- | --- | --- |
| Browser gate 输出 390x844 和 768x900 截图/JSON/summary | `mobile_web_browser_390x844.json/png`、`mobile_web_browser_768x900.json/png`、`mobile_web_browser_acceptance_summary.json`；summary `ok=true`，两组 viewport `passed=true` | 通过 |
| Retest request panel 可见、可复制，并保留 boundary / `not_proven` | summary judgment 中 `real_device_retest_request_visible=true`、`real_device_retest_request_copyable=true`，evidence boundary 为 `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate` | 通过 |
| 主操作 fail closed，ACK 不是 delivery success | summary judgment 中 `primary_actions_disabled=true`、`ack_not_delivery_success=true`，Task A docs 与 gate 均保留该边界 | 通过 |
| Robot metadata-only fence 不触发控制语义 | Task B `Ran 153 tests in 78.872s OK`，证明 metadata 不触发 collect/dropoff/cancel、ACK、cursor、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success | 通过 |
| Product closeout 保守更新 OKR | `OKR.md` 和 `docs/process/okr_progress_log.md` 写明 O4 约 85%、O5 约 68%，Objective 1/2/3 不调整 | 通过 |

## 风险和证据边界

- 本轮是 Docker/local current PWA browser proof，不是真实 iPhone/Android、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery。
- 真实设备复测请求仍只是下一轮材料请求；browser proof、ACK、HTTP accepted、receipt、handoff session 和 install prompt evidence 都是 accepted/processing/support metadata，不是 delivery success。
