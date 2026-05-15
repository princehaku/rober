# Sprint 2026.05.16_05-06 Mobile Route Elevator Handoff Browser Proof - PRD

sprint_type: epic

## 1. 用户价值

现场操作者和普通手机用户已经能在 mobile/web 看到 route/elevator field-session handoff 的只读摘要。现在缺的是：这个最新关键面板是否在当前 PWA 的本地 Chromium-family 浏览器证明里可见、phone-safe、布局可用、主操作仍 fail-closed。

本轮把“路线电梯现场交接”纳入 browser proof gate，让后续现场 session 前可以用同一套本地浏览器证据确认：handoff verdict、safe `evidence_ref`、same-evidence-ref、required materials、operator next steps、boundary、`delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven` 都能在手机尺寸和宽屏尺寸上展示。

## 2. OKR 映射

- Objective 4：主目标。补齐最新 route/elevator handoff panel 的本地 browser proof 覆盖，推进手机用户体验与可验收边界。
- Objective 2 / Objective 3：只作为支撑。browser proof 能让 route/elevator 现场交接摘要在手机端可读，但不证明真实电梯、真实 route run 或 task record。
- Objective 5：不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。
- Objective 1：不推进。没有真实 WAVE ROVER、UART、`T=1001` feedback 或 HIL。

## 3. 验收口径

必须满足：

- `phone_browser_acceptance_gate.py` 覆盖 route/elevator field-session handoff panel 的关键 DOM、标题和 evidence boundary。
- 生成的 browser evidence summary 能反映该 panel 可见或明确 blocked，不把缺失当通过。
- `mobile/test_mobile_web_entrypoint.py` 能围栏这个浏览器证明覆盖，不新增广泛测试套件。
- `docs/product/mobile_user_flow.md` 说明该 browser proof 覆盖最新 route/elevator handoff panel，并保持 local Chromium proof only。
- Start / Confirm Dropoff / Cancel gating 不改变。

不得声称：

- 真实 iPhone/Android device behavior。
- production app 或真实 PWA prompt/user choice。
- 真实 route/elevator field pass。
- WAVE ROVER/UART/HIL。
- dropoff/cancel completion 或 delivery success。
- Objective 5 external proof。

## 4. 分工

- Task A `full-stack-software-engineer`：实现 browser proof 覆盖、mobile smoke 更新、产品文档更新和 fenced validation。
- Task B `robot-software-engineer`：复核 diagnostics contract 与 route/elevator handoff summary 的 metadata-only 边界，必要时补接口文档围栏。
- Task C `product-okr-owner`：在工程结果后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md`。
