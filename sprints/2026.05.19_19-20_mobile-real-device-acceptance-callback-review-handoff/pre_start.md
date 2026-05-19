# Sprint 2026.05.19_19-20 Mobile Real Device Acceptance Callback Review Handoff - Pre Start

## 1. Sprint 类型

sprint_type: epic

本轮是跨 owner 的 Objective 4 functional rung：把上一轮 `mobile_real_device_field_trial_acceptance_execution_callback_review_decision` 转成 Robot diagnostics 与手机端都能读取的 owner handoff package。目标不是提高 OKR 百分比，而是在没有真实外部材料的 Docker-only 环境中，继续把真实手机验收材料链路往可执行、可复跑、可交接方向推进。

## 2. 用户价值和产品北极星

北极星仍是：普通手机用户不需要 SSH、ROS2、串口或硬件知识，也能知道一次送垃圾任务为什么不能发车、缺什么现场证据、下一步由谁补材料。

本轮用户价值是把复核决策从“工程人员可读的 review result”翻译成“现场 owner 可执行的 handoff”：手机端和 Robot 侧都应展示同一 safe `evidence_ref` 下的 owner handoff、rerun guidance、next required evidence、剩余 blocker 和 fail-closed 控制状态，避免把 callback review decision 误读成真实手机通过、真实 route/elevator field pass、HIL 或 delivery success。

## 3. 开工证据

- `OKR.md` 4.1 最新 sprint 是 `2026.05.19_18-19_mobile-real-device-acceptance-callback-review-decision`。
- Objective 5 仍约 68%，是数字最低项，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 和 external proof；不得继续本地 O5 metadata depth 来冒充完成度提升。
- Objective 1 仍约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `blocked_pending_real_materials`，缺真实 WAVE ROVER/UART/HIL，也缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；不得声称 Objective 1 提升。
- PR #5 live threads 当前按 repo closeout 证据处理：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` unresolved，因为 mandatory sensor assumptions 仍需本地 vendor/source 或真实材料证据。
- 最新 18-19 sprint 已完成 Objective 4 `mobile_real_device_field_trial_acceptance_execution_callback_review_decision`，且明确边界为 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 4. Rerank 决策

本轮不选择 Objective 5：它虽然最低，但下一步有效进展依赖真实公网入口、4G/SIM、OSS/CDN live traffic、production DB/queue 或 cutover/worker 证据，当前 Docker-only 主机无法补齐。继续增加本地 O5 metadata 只会重复消费同一外部 blocker。

本轮不选择 Objective 1 完成度提升：PR #5 的 `PRRT_kwDOSWB9286CJ3tX` 仍需真实 sensor material 或本地 vendor/source 证据；WAVE ROVER/UART/HIL 也没有真实设备与日志。没有这些材料时，任何 O1 文档或 UI wrapper 都不能算硬件协议可信度提升。

本轮选择 Objective 4：上一轮已经形成 callback review decision，下一步最可执行的 functional rung 是 `mobile_real_device_field_trial_acceptance_execution_callback_review_handoff`。它能把复核结论转成现场 owner 可执行的 handoff、rerun guidance 和 next evidence checklist，同时继续保持 fail-closed 和 software-proof 边界。

## 5. 本轮核心抓手

把 `mobile_real_device_field_trial_acceptance_execution_callback_review_handoff` 做成两个并行、互不重叠的交付面：

- Robot Platform Engineer：产出 Robot diagnostics safe summary，让 `/api/status` / diagnostics 消费方能读取 callback review handoff 的 owner、rerun、next evidence 和 blocker 状态。
- User Touchpoint Full-Stack Engineer：在 `mobile/web` 增加只读 handoff panel 和 copy/export 入口，让现场 owner 在手机上看到可执行的补材料动作，并确认 Start Delivery、Confirm Dropoff、Cancel 仍不被启用。

## 6. Owner 和并行规则

本轮必须 2 个 owner 并行执行，文件范围互不重叠：

- Robot Platform Engineer：负责 ROS2 behavior diagnostics summary、safe alias、fail-closed schema handling 和接口文档。
- User Touchpoint Full-Stack Engineer：负责手机端 panel、fixture、前端测试和产品文档。

Product Owner 只负责本 pre_start / prd / tech-plan 规划，不修改产品代码、测试代码、`OKR.md` 或 `docs/process/okr_progress_log.md`。实现完成后再进入 `tech-done.md`、`side2side_check.md`、`final.md` 和 OKR closeout。

## 7. 风险、阻塞和证据链缺口

- 真实手机验收仍缺：真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、true phone/browser acceptance。
- Objective 5 仍缺：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration/cutover。
- Objective 1 / PR #5 仍缺：真实 WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- Objective 2 / Objective 3 仍缺：真实 route/elevator field pass、Nav2/fixed-route runtime log、route completion signal、现场 task record、dropoff/cancel completion、delivery result。
- 本轮所有新增 summary、panel、copy/export 都必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 8. 需要创建或更新的 sprint 文档

本规划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现完成后必须继续更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

closeout 阶段才允许更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
