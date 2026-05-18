# Sprint 2026.05.19_07-08 Elevator Field Evidence Material Backfill Intake - Pre Start

## sprint_type: epic

启动时间：2026-05-19 07:08 Asia/Shanghai。

## 1. 用户价值和产品北极星

本轮用户价值是把 PR #4 route/elevator 现场材料从“交接给 owner”推进到“owner 可回填、系统可校验、下游可只读消费”的入口。现场 owner 可以提交上一轮 handoff summary 和 operator-provided material packet/file refs，系统按同一 safe `evidence_ref` 校验真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime、task record、dropoff/cancel/result 等必需材料是否齐全。

产品北极星保持不变：面向普通手机用户的低成本、可解释跨楼层送垃圾机器人。本轮只规划 `elevator_field_evidence_trace_material_backfill_intake`，为真实现场材料回填准备入口；不声称真实 elevator field pass、真实 Nav2/fixed-route runtime、WAVE ROVER/UART/HIL、真实手机/browser、Objective 5 external proof 或 delivery success。

## 2. 背景证据

- `OKR.md` 4.1 最新 sprint 是 `2026.05.19_06-07_elevator-field-evidence-trace-callback-review-handoff`。
- Objective 5 当前约 68%，但仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 等 external proof；本机只有 Docker，不能继续用本地 metadata 冒充 O5 completion。
- Objective 1 当前约 81%，但仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- PR #4 / 近期 sprint 已把 elevator field evidence trace 推进到 callback review handoff；上一轮 `final.md` 明确下一步应支持现场 owner 回填真实材料，而不是再包一层本地 metadata。
- 本机无真实硬件、只有 Docker；本轮只能规划 fail-closed software-proof intake，后续实现也不得升级为真实 field pass。

## 3. 本轮核心抓手

核心抓手：`elevator_field_evidence_trace_material_backfill_intake`。

它应消费：

- 上一轮 `elevator_field_evidence_trace_callback_review_handoff` artifact / summary / Robot diagnostics safe alias。
- operator-provided material packet 或 file refs 的安全摘要。
- 同一 safe `evidence_ref`。

它应校验：

- `source=software_proof`、`overall_status=not_proven`。
- `delivery_success=false`、`primary_actions_enabled=false`。
- same safe `evidence_ref` 不能缺失、不能不一致、不能弱化为非布尔 true。
- required materials 必须覆盖真实门状态、楼层确认、人工协助、Nav2/fixed-route runtime、route completion signal、field task record、dropoff/cancel completion、delivery result。
- raw path、credential、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER、checksum、完整 raw artifact、success/control claim 必须 fail closed。

## 4. Sprint 类型与 owner

本轮是 Epic sprint，因为后续实现会跨 Autonomy、Robot diagnostics、mobile/web 和产品文档，预计需要 3 个并行 engineer worker 才能形成可消费的端到端 software-proof chain。

Owner 拆分：

- Product Manager / OKR Owner：本轮只创建 `pre_start.md`、`prd.md`、`tech-plan.md`，明确用户价值、OKR 映射、验收口径和后续 owner/file scope。
- Autonomy Algorithm Engineer：后续实现 PC material backfill intake gate、focused unittest、interface docs。
- Robot Platform Engineer：后续增加 diagnostics safe alias，只读消费 summary，缺失/unsafe fail closed。
- User Touchpoint Full-Stack Engineer：后续增加 mobile/web 只读材料回填状态 panel，保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。

## 5. 本轮不做

- 不修改产品代码、测试代码、硬件配置、launch 参数或 `OKR.md`。
- 不创建 `tech-done.md`、`side2side_check.md`、`final.md`，直到后续 implementation worker 返回真实改动和验证结果。
- 不读取真实材料目录并声明通过；本轮只是规划入口。
- 不接触 WAVE ROVER、ESP32、Orange Pi、UART、波特率、引脚、电压、机械尺寸或真实 HIL 配置；若后续实现触及硬件事实，必须先按 AGENTS 要求读取 `docs/vendor/VENDOR_INDEX.md`。

## 6. 验收口径

Planning gate 通过条件：

- 新 sprint 三份前置文档存在。
- 文档包含 `sprint_type: epic`、`elevator_field_evidence_trace_material_backfill_intake`、Objective 5、Objective 1、PR #4、PR #5、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `tech-plan.md` 包含 `OKR 最低优先级核对`、owner/file scope、接口影响、验收命令和风险边界。
- `git diff --check` 对本 sprint 目录通过。

## 7. 风险和阻塞

- Objective 5 仍被真实 external proof 阻塞，不能通过本轮提升。
- Objective 1 仍被真实 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 材料阻塞，不能通过本轮提升。
- Objective 2 / Objective 3 只能获得材料回填入口的 `software_proof` 进展；真实门状态、楼层确认、人工协助、Nav2/fixed-route runtime、task record、dropoff/cancel/result 仍需要现场 owner 后续提供。
- Objective 4 只能获得只读可解释入口，不能证明真实 iPhone/Android 或 production app 行为。
