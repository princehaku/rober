# Sprint 2026.05.20_09-10 Mobile Real Device Acceptance Handoff Intake - Pre Start

## 1. Sprint 类型

sprint_type: epic

本轮主题：`mobile_real_device_acceptance_handoff_intake`。

本轮是 Objective 4 的真实手机验收链后续：把 `mobile_real_device_field_trial_acceptance_execution_callback_review_handoff` 后的现场 owner 回执 / ack intake 做成 PC / Robot / mobile 都能消费的 fail-closed 状态。目标不是提高 OKR 百分比，而是在 Docker-only 主机上继续把真实手机验收材料链路推进到可回执、可复核、可交接。

## 2. 用户价值和产品北极星

产品北极星仍是：普通手机用户不需要 SSH、ROS2、串口、云凭证或硬件调试，也能完成送垃圾任务，并在失败或材料不足时看懂下一步由谁补证据。

本轮用户价值是让现场 owner 在接到上一轮 handoff 后，能回传“已收到 / 缺材料 / 需重跑 / 拒绝当前材料”等 ack/intake 状态；PC、Robot diagnostics 和手机端都只读显示同一 safe `evidence_ref` 下的回执结果、缺失材料、下一步 owner 和复跑提示，避免把 handoff 或 ack 误读成真实手机验收通过、真实 route/elevator field pass、HIL、dropoff/cancel completion 或 delivery success。

## 3. 开工证据

- `OKR.md` 4.1 更新时间为 2026-05-20 08:58 Asia/Shanghai；最新 sprint 是 `2026.05.20_08-09_cloud-command-id-conflict-visibility-guard`。
- Objective 5 当前约 68%，是数字最低项；但最新 final 明确下一步有效提升需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 或真实手机/browser。当前主机只有 Docker，不能继续堆本地 O5 metadata depth。
- Objective 1 当前约 81%；GitHub PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved，已有 reply comment `3269642220` 但真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍缺，不能写成 resolved 或 O1 提升。
- Objective 2 / Objective 3 / Objective 4 的真实材料仍缺。route/elevator blocker 与 O5/O1 blocker 已被多轮 software-proof wrapper 消费；本轮不再重复包同一 blocker。
- 最新 O4 链路已到 `mobile_real_device_field_trial_acceptance_execution_callback_review_handoff`。下一步最可执行的功能抓手是回收现场 owner 对该 handoff 的 ack/intake 状态。

## 4. Rerank 决策

本轮不选择 Objective 5 completion：它虽然最低，但当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 证据。继续增加本地 cloud metadata 只会重复消费同一外部 blocker。

本轮不选择 Objective 1 completion：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；真实 2D LiDAR / ToF 材料与 WAVE ROVER/UART/HIL 证据仍缺。没有真实 source/material 或 reviewer resolve 前，不得提升 O1。

本轮选择 Objective 4 的后续回执入口：`mobile_real_device_field_trial_acceptance_execution_callback_review_handoff` 已给出现场交接，下一步需要 owner ack/intake，以确认现场是否收到、是否缺材料、是否需要复跑、是否进入下一轮 review。该工作能推动功能链条继续前进，同时保持 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 本轮核心抓手

把 `mobile_real_device_field_trial_acceptance_execution_handoff_intake` 做成三个交付面：

- Robot Platform Engineer：产出 Robot diagnostics safe summary，让 PC/operator gateway 与 diagnostics consumer 能读取 handoff ack/intake 状态。
- User Touchpoint Full-Stack Engineer：在 `mobile/web` 增加只读回执入口 / 状态 panel，让现场 owner 看到已收到、缺材料、需要复跑、下一步 evidence checklist。
- Product Owner：实现后负责 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 progress log 的保守 closeout，确认没有把 software-proof 写成真实手机或 delivery success。

## 6. Owner 和并行规则

本轮实现阶段必须并行启动 2 个工程 worker，文件范围互不重叠；Product Owner 在 closeout 阶段单独更新 sprint 与 OKR 文档。

- Robot Platform Engineer：负责 ROS2 behavior diagnostics summary、safe alias、fail-closed schema handling 和接口文档。
- User Touchpoint Full-Stack Engineer：负责手机端 panel、fixture、前端测试和产品文档。
- Product Owner：负责阶段验收、OKR 边界和 sprint 收口；不写产品代码和测试代码。

## 7. 风险、阻塞和证据链缺口

- 真实手机验收仍缺：真实 iPhone/Android device behavior、production app、真实 PWA prompt/userChoice、true phone/browser acceptance。
- Objective 5 仍缺：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover。
- Objective 1 / PR #5 仍缺：真实 WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；`PRRT_kwDOSWB9286CJ3tX` 仍不能写成 resolved。
- Objective 2 / Objective 3 仍缺：真实 route/elevator field pass、Nav2/fixed-route runtime log、route completion signal、现场 task record、dropoff/cancel completion、delivery result。
- 本轮所有新增状态必须保留 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 8. 需要创建或更新的 sprint 文档

本规划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现完成后必须继续更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

closeout 阶段才允许更新 `OKR.md` 和 `docs/process/okr_progress_log.md`；若仍无真实外部/硬件/手机材料，OKR 百分比保守不提高。
