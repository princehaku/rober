# Sprint 2026.05.19_09-10 Elevator Field Evidence Material Backfill Review Handoff - Pre Start

## sprint_type: epic

启动时间：2026-05-19 09:10 Asia/Shanghai。

## 1. 用户价值和产品北极星

本轮用户价值是把上一轮 `elevator_field_evidence_trace_material_backfill_review_decision` 从“材料回填可复核”推进到“现场 owner 可以安全接手补证据”。现场 owner、Robot diagnostics 和手机端需要看到同一 safe `evidence_ref` 下哪些真实材料还缺、下一步由谁补、哪些 rerun hint 安全可执行，以及哪些文案只能作为 phone-safe copy 展示。

产品北极星保持不变：面向普通手机用户的低成本、可解释跨楼层送垃圾机器人。本轮只规划 `elevator_field_evidence_trace_material_backfill_review_handoff`，用于把 material backfill review decision 转换为现场 handoff package；不证明真实 field pass、真实电梯、真实 Nav2/fixed-route、真实 WAVE ROVER/UART/HIL、真实手机/browser、Objective 5 external proof 或 delivery success。

## 2. 背景证据

- 当前主机没有真实硬件，只有 Docker；不能声明 HIL、真实电梯、真实 Nav2/fixed-route、真实手机/browser 或真实 Objective 5 external proof。
- `OKR.md` 4.1 最新 sprint 是 `2026.05.19_08-09_elevator-field-evidence-material-backfill-review-decision`。Objective 5 约 68%，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 等 external proof；本轮不继续做本地 O5 metadata depth。
- Objective 1 约 81%，仍缺真实 WAVE ROVER/UART/HIL，以及 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料；本轮不消费 O1 硬件 blocker。
- PR #4 已合并并把 elevator-assisted delivery 固化为主链路；PR #5 已合并并固化电梯主线、硬件边界和 2D LiDAR / ToF 材料缺口。
- 最近两轮 `07-08` 和 `08-09` 已完成 material backfill intake -> material backfill review decision，均为 DONE，且边界保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 上一轮 `08-09` final 明确剩余风险：真实电梯、真实 Nav2/fixed-route、真实 task record、真实 dropoff/cancel completion、真实 delivery success、真实手机/browser、WAVE ROVER/UART/HIL、PR #5 真实材料和 O5 external proof 均未完成。

## 3. 本轮核心抓手

核心抓手：`elevator_field_evidence_trace_material_backfill_review_handoff`。

它应消费：

- 上一轮 `elevator_field_evidence_trace_material_backfill_review_decision` artifact / summary / Robot diagnostics safe alias。
- 同一 safe `evidence_ref`。
- review decision 中的 decision reasons、missing/rejected materials、next required evidence、owner handoff 和 evidence boundary。

它应输出：

- 现场 owner handoff package：owner、下一步真实材料、safe rerun hints、phone-safe copy、blocked reason 和 evidence boundary。
- Robot diagnostics safe alias，用于只读展示 handoff readiness。
- mobile/web 只读 panel，用中文解释下一步真实材料，不改变 Start Delivery、Confirm Dropoff、Cancel gating。

## 4. Sprint 类型与 owner

本轮是 Epic sprint，因为后续 implementation 会跨 Autonomy PC gate、Robot diagnostics safe alias、mobile/web 只读展示和 Product closeout，预计需要 3 个并行 engineer worker 才能形成端到端 software-proof handoff chain。

Owner 拆分：

- Product Manager / OKR Owner：本轮只创建 `pre_start.md`、`prd.md`、`tech-plan.md`，明确用户价值、OKR 映射、验收口径和后续 owner/file scope。
- Autonomy Algorithm Engineer：后续实现 PC review handoff gate、focused unittest、interface docs。
- Robot Platform Engineer：后续增加 diagnostics safe alias，只读消费 handoff summary，缺失/unsafe fail closed。
- User Touchpoint Full-Stack Engineer：后续增加 mobile/web 只读 review handoff panel，保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。

## 5. 本轮不做

- 不修改产品代码、测试代码、硬件配置、launch 参数、`OKR.md`、`docs/process/okr_progress_log.md` 或其他 sprint 目录。
- 不创建 `tech-done.md`、`side2side_check.md`、`final.md`，直到后续 implementation worker 返回真实改动和验证结果。
- 不声明真实现场通过、真实材料已到位、真实手机通过、真实 HIL 或 delivery success。
- 不接触 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压、机械尺寸或真实 HIL 配置；若后续实现触及硬件事实，必须先按 AGENTS 要求读取 `docs/vendor/VENDOR_INDEX.md`。

## 6. 验收口径

Planning gate 通过条件：

- 新 sprint 三份前置文档存在。
- 文档包含 `sprint_type: epic`、`elevator_field_evidence_trace_material_backfill_review_handoff`、Objective 5、Objective 1、PR #4、PR #5、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `tech-plan.md` 包含 `OKR 最低优先级核对`、3 个 implementation owners、owner/file scope、接口影响、围栏验收命令和风险边界。
- `git diff --check` 对本 sprint 目录通过。

## 7. 风险和阻塞

- Objective 5 仍被真实 external proof 阻塞，不能通过本轮提升。
- Objective 1 仍被真实 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 材料阻塞，不能通过本轮提升。
- Objective 2 / Objective 3 只能获得现场材料 handoff 可执行性的 `software_proof` 进展；真实门状态、楼层确认、人工协助、Nav2/fixed-route runtime、task record、dropoff/cancel/result 仍需要现场 owner 后续提供。
- Objective 4 只能获得只读可解释 handoff panel，不能证明真实 iPhone/Android 或 production app 行为。
