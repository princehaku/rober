# Sprint 2026.05.19_08-09 Elevator Field Evidence Material Backfill Review Decision - Pre Start

## sprint_type: epic

启动时间：2026-05-19 08:09 Asia/Shanghai。

## 1. 用户价值和产品北极星

本轮用户价值是把上一轮 `elevator_field_evidence_trace_material_backfill_intake` 从“现场材料可安全回填”推进到“材料回填可被复核并形成下一步决策”。现场 owner 和后续 engineer 需要知道哪些材料已安全进入同一 safe `evidence_ref`，哪些材料仍缺失或被拒绝，以及是否可以进入下一层现场复核/执行交接。

产品北极星保持不变：面向普通手机用户的低成本、可解释跨楼层送垃圾机器人。本轮只规划 `elevator_field_evidence_trace_material_backfill_review_decision`，用于 review decision 的 fail-closed software-proof 链路；不声明真实 elevator field pass、真实 Nav2/fixed-route runtime、真实 WAVE ROVER/UART/HIL、真实手机/browser、Objective 5 external proof 或 delivery success。

## 2. 背景证据

- 当前主机没有真实硬件，只有 Docker；不能声明 HIL、真实电梯、真实 Nav2/fixed-route、真实手机/browser 或真实 Objective 5 external proof。
- `OKR.md` 4.1 当前最低 Objective 5 约 68%，但仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 等外部材料；按 stop rule 不继续堆本地 O5 wrapper。
- Objective 1 约 81%，仍缺真实 WAVE ROVER/UART/HIL，以及 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料；本轮不消费 O1 硬件 blocker。
- PR #4 要求电梯 assisted delivery 进入主链；近期 `07-08` final 明确建议下一步把 material backfill intake 推进到 material review decision。
- PR #5 review 证据仍需保留：P1 `docs/product/production_hardware_boundary.md` 默认硬件集合与 mandatory sensor baseline 曾矛盾；P2 `OKR.md` lowest-objective narrative/table 曾不一致；P2 mandatory sensor assumptions 需要 `docs/vendor/` 本地来源。`03-04_pr5-review-thread-closeout/final.md` 记录 P1/P2 docs ready_to_close_on_mainline_docs，但 mandatory sensor citation/material 仍 `blocked_pending_real_materials`。
- 上一轮 `07-08` final 的证据边界是 `software_proof_docker_elevator_field_evidence_trace_material_backfill_intake_gate`，并保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。本轮 review decision 必须继承这些边界，不得升级为真实通过。

## 3. 本轮核心抓手

核心抓手：`elevator_field_evidence_trace_material_backfill_review_decision`。

它应消费：

- 上一轮 `elevator_field_evidence_trace_material_backfill_intake` artifact / summary / Robot diagnostics safe alias。
- 同一 safe `evidence_ref`。
- intake summary 中的 accepted material refs、missing required materials、rejected materials、next required evidence 和 evidence boundary。

它应输出：

- Review decision：例如 `blocked_missing_material_backfill_intake_not_proven`、`blocked_unsupported_material_backfill_intake_not_proven`、`needs_required_material_backfill_not_proven`、`ready_for_field_evidence_material_review_handoff_not_proven`。
- 决策理由、缺失材料、被拒绝材料、下一步 required evidence、owner handoff。
- 供 Robot diagnostics 和 mobile/web 只读消费的 safe summary。

## 4. Sprint 类型与 owner

本轮是 Epic sprint，因为后续 implementation 会跨 Autonomy PC gate、Robot diagnostics safe alias、mobile/web 只读展示和 Product closeout，预计需要 3 个并行 engineer worker 才能形成可消费的端到端 software-proof chain。

Owner 拆分：

- Product Manager / OKR Owner：本轮只创建 `pre_start.md`、`prd.md`、`tech-plan.md`，明确用户价值、OKR 映射、验收口径和后续 owner/file scope。
- Autonomy Algorithm Engineer：后续实现 PC material backfill review decision gate、focused unittest、interface docs。
- Robot Platform Engineer：后续增加 diagnostics safe alias，只读消费 review decision summary，缺失/unsafe fail closed。
- User Touchpoint Full-Stack Engineer：后续增加 mobile/web 只读 material backfill review decision panel，保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。

## 5. 本轮不做

- 不修改产品代码、测试代码、硬件配置、launch 参数、`OKR.md`、`docs/process/okr_progress_log.md` 或其他 sprint 目录。
- 不创建 `tech-done.md`、`side2side_check.md`、`final.md`，直到后续 implementation worker 返回真实改动和验证结果。
- 不读取真实材料目录并声明通过；本轮只是规划 review decision。
- 不接触 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压、机械尺寸或真实 HIL 配置；若后续实现触及硬件事实，必须先按 AGENTS 要求读取 `docs/vendor/VENDOR_INDEX.md`。

## 6. 验收口径

Planning gate 通过条件：

- 新 sprint 三份前置文档存在。
- 文档包含 `sprint_type: epic`、`elevator_field_evidence_trace_material_backfill_review_decision`、Objective 5、Objective 1、Objective 2、Objective 3、Objective 4、PR #4、PR #5、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `tech-plan.md` 包含 `OKR 最低优先级核对`、3 个 implementation owners、owner/file scope、接口影响、围栏验收命令和风险边界。
- `git diff --check` 对本 sprint 目录通过。

## 7. 风险和阻塞

- Objective 5 仍被真实 external proof 阻塞，不能通过本轮提升。
- Objective 1 仍被真实 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 材料阻塞，不能通过本轮提升。
- Objective 2 / Objective 3 只能获得材料回填复核决策的 `software_proof` 进展；真实门状态、楼层确认、人工协助、Nav2/fixed-route runtime、task record、dropoff/cancel/result 仍需要现场 owner 后续提供。
- Objective 4 只能获得只读可解释 review decision panel，不能证明真实 iPhone/Android 或 production app 行为。
