# Sprint 2026.05.16_05-06 Mobile Route Elevator Handoff Browser Proof - Pre Start

sprint_type: epic

## 1. 启动原因

本轮按当前 `OKR.md` 4.1 重排。Objective 5 数值最低，约 66%，但剩余推进需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部材料；本机只有 Docker，继续堆本地 O5 metadata 会重复消费同一 blocker。

Objective 1 约 73%，但仍缺真实 WAVE ROVER、UART、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 与 HIL。当前主机无真实硬件，不能把 software proof 写成 `hil_pass`。

Objective 4 约 75%，是当前最低可行动作。近期 route/elevator sprint 已把 `route_elevator_field_session_handoff` 接到 mobile/web 只读 panel，但 `pc-tools/evidence/phone_browser_acceptance_gate.py` 的当前浏览器证明清单尚未覆盖该最新 panel。下一步应把这个 panel 纳入本地 Chromium-family 浏览器证明，输出 screenshot + JSON evidence，并继续写明不是真实手机、production app、真实 PWA prompt 或真实送达。

## 2. 证据来源

- `OKR.md` 4.1：Objective 5 约 66%，但需要真实外部云/4G/OSS/CDN/DB/queue 材料；Objective 4 约 75%，仍缺真实手机/browser、production app、PWA prompt/user choice。
- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/final.md`：mobile/web 已新增只读“路线电梯现场交接” panel，但本轮不证明真实手机/browser。
- `pc-tools/evidence/phone_browser_acceptance_gate.py`：当前 `KEY_ELEMENT_IDS` 与 `CURRENT_PANEL_EXPECTATIONS` 覆盖 field-trial/acceptance chain，但未覆盖 `routeElevatorFieldSessionHandoffTitle`、handoff materials、next steps、boundary 等最新 DOM。
- `docs/product/mobile_user_flow.md`：当前 browser proof 说明仍只列 field-trial chain 和 browser acceptance bundle，未说明 route/elevator handoff panel 的本地浏览器证明。
- `gh` CLI 本机不可用，无法直接拉取远端 PR review；本轮 PR/评审证据采用本地 merge commit、最新 sprint final/tech-done、OKR 与 docs review/closeout 条目。

## 3. Owner 和边界

- `full-stack-software-engineer`：主责更新 mobile browser proof gate、mobile smoke、产品文档，并运行 fenced validation。
- `robot-software-engineer`：复核 diagnostics metadata-only contract，必要时只在接口文档或诊断测试内补围栏；不得触发控制、ACK、Nav2、HIL、dropoff/cancel 或 delivery success。
- `product-okr-owner`：收口 sprint 文档、OKR 和 progress log，确保只保守推动 Objective 4。

## 4. 风险

- 若本机没有 Chromium-family browser，本轮只能记录 browser proof 运行阻塞，但仍可完成 gate 覆盖与静态围栏。
- 本轮不能提高 Objective 5，也不能声称真实手机、真实 PWA prompt、真实路线、电梯、HIL、dropoff/cancel completion 或 delivery success。
