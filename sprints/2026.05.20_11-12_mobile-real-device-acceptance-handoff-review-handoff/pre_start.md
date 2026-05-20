# Sprint 2026.05.20_11-12 Mobile Real Device Acceptance Handoff Review Handoff - Pre Start

sprint_type: epic

## 1. 启动背景

本轮 fresh Epic sprint 主题为 `mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff`。

CEO 要求 automation `skill-progression-map` 继续根据近期 PR 和评审证据推进 OKR：优先低完成度、用 team、功能往前走、测试只围栏、本机只有 Docker、最后由后续实现轮提交并推送。本轮 Product 只负责 planning docs，不提交 git，不修改工程代码、`OKR.md` 或 `docs/process/okr_progress_log.md`。

关键证据：

- `OKR.md` 4.1 当前最低 Objective 5 约 68%，但只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 证据才能提升；当前 Docker-only 主机不能继续堆 O5 metadata depth。
- 下一低项 Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry、真实 WAVE ROVER/UART/HIL 均缺失。
- GitHub live PR #5 证据：PR #5 已 merged；`PRRT_kwDOSWB9286CJ3tQ`、`PRRT_kwDOSWB9286CJ3tU` 已 resolved；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，review 要求 mandatory sensor assumptions 必须有本地 `docs/vendor/` source attribution。
- 最新 sprint `sprints/2026.05.20_10-11_mobile-real-device-acceptance-handoff-review-decision/final.md` 已完成 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision`，边界为 `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_gate`，并明确不能声称真实手机/browser 或 OKR 百分比提升。

## 2. 用户价值和产品北极星

用户价值：现场 owner 在复核 accepted / missing / rejected / blocked 后，需要看到下一步交接包：当前决策、谁接、为什么接、缺什么证据、如何重跑、哪些材料已接受或被拒，避免把 review decision 停留在“结论可见”而没有“下一步归属可执行”。

产品北极星：手机端是普通用户唯一入口；所有现场验收状态必须中文优先、可解释、可复跑、可售后诊断，并在证据不足时 fail closed。

## 3. OKR 映射

主受益 Objective：Objective 4 手机用户体验与低成本量产边界。

本轮不提高 OKR 百分比，原因：

- Objective 5 仍缺真实 external proof，不能用本地 handoff metadata 提升。
- Objective 1 仍缺 PR #5 `PRRT_kwDOSWB9286CJ3tX` 所需 vendor/source/material evidence，不能写成硬件或 HIL 进展。
- Objective 2 / Objective 3 仍缺真实 route/elevator field pass、Nav2/fixed-route runtime、dropoff/cancel completion 和 delivery result。
- Objective 4 本轮只计划 software-proof Docker/local phone-safe handoff package；不是真实手机/browser、production app 或真实 PWA prompt/userChoice。

## 4. 本轮核心抓手

把上一轮 handoff review decision 的复核结果转成下一步现场 owner handoff package，让 Robot diagnostics 与 mobile/web 只读展示“现场验收交接复核交接”。

必须展示：

- current decision
- handoff owner
- handoff reason
- accepted / missing / rejected / blocked summaries
- next required evidence
- rerun guidance
- same safe `evidence_ref`
- evidence boundary

必须保持：

- `software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate`

禁止写成：

- 真实手机/browser
- O5 external proof
- O1 hardware/HIL
- route/elevator field pass
- dropoff/cancel completion
- delivery success
- Start / Confirm Dropoff / Cancel 可用

## 5. Owner 与并行方式

本轮是跨 owner Epic sprint，必须并行派发 2 个 engineering owner：

1. Robot Platform Engineer：负责 Robot diagnostics safe summary 与接口文档。
2. User Touchpoint Full-Stack Engineer：负责 mobile/web 只读 panel、fixture、entrypoint test 与产品流程文档。

两者文件范围互不重叠，但必须对齐同一个 schema 名称、evidence boundary、safe `evidence_ref`、fail-closed 字段和 forbidden claims。

Product closeout 只在实现完成后更新新 sprint `tech-done.md`、`side2side_check.md`、`final.md`，并按证据决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。本轮 planning 阶段不改这些文件。

## 6. 风险、阻塞和证据链

- O5 blocked：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser。
- O1 blocked：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；真实 2D LiDAR / ToF source/material 和 WAVE ROVER/UART/HIL 缺失。
- O2/O3 field proof blocked：缺真实 Nav2/fixed-route runtime log、route completion signal、field task record、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 和 delivery result。
- 本轮只能提供 `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate`，不能作为 OKR 百分比提升或真实验收通过。

## 7. 需要创建或更新的 sprint 文档

Planning 阶段创建：

- `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/pre_start.md`
- `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/prd.md`
- `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/tech-plan.md`

实现和 closeout 阶段后续更新：

- `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/tech-done.md`
- `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/side2side_check.md`
- `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
