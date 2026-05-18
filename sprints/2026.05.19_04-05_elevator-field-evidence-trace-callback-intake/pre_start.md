# Sprint 2026.05.19_04-05 Elevator Field Evidence Trace Callback Intake - Pre Start

## sprint_type: epic

Run start: 2026-05-19 Asia/Shanghai.

## 用户价值和产品北极星

用户价值：现场 owner 后续补真实 route/elevator field materials 时，不再靠聊天或散落截图人工判断；系统应能把安全 callback packet、`elevator_action_feedback_trace`、diagnostics/mobile summary、route/elevator required materials 放到同一 safe `evidence_ref` 下做只读 intake 判定。

产品北极星保持不变：普通手机用户把垃圾交给低成本 ROS2 小车后，小车能可解释、可恢复、可复盘地完成固定路线与电梯 assisted delivery。本 sprint 只推进“现场材料回填入口的可判定性”，不证明真实送达。

## OKR 映射

- Objective 5：当前 `OKR.md` 4.1 数字最低，约 68%。但本机没有真实外部云、4G、OSS/CDN、DB/queue、production worker/cutover、真实 phone/browser 证据；本轮不继续堆 O5 本地 wrapper。
- Objective 1：约 81%。PR #5 review 已暴露硬件边界冲突、OKR 最低项叙述不一致、强制 2D LiDAR/ToF 假设缺 vendor 来源；最新 `2026.05.19_03-04_pr5-review-thread-closeout` 已完成 closeout 可判定 gate，但真实 2D LiDAR / ToF 材料、WAVE ROVER/UART/HIL 仍不可用。
- Objective 2：约 99%。PR #4 已合并并把 elevator-assisted delivery 设为必达；`2026.05.19_00-01` 已补 `current_step=elevator:<phase>` action feedback，`2026.05.19_02-03` 已把 `elevator_action_feedback_trace` 对齐到 task record/diagnostics/mobile。下一步应补现场 owner 回填 callback intake。
- Objective 3：约 99%。仍缺真实 Nav2/fixed-route runtime、route completion signal、现场 task record 和同一 `evidence_ref` 的路线/电梯复账。本 sprint 把 O3 需要的 route evidence callback 纳入 intake 判定，但保持 `not_proven`。

## 近期 PR 和评审证据

- PR #4：已合并，明确 elevator assisted delivery 是主链必达，不应回退成可选 H2；因此下一步必须围绕真实 route/elevator field materials，而不是再做纯手机或云端本地包装。
- PR #5：review closeout 已把 P1/P2 文档问题转成可判定状态，但 mandatory sensor citation/material thread 仍是 `blocked_pending_real_materials`；本轮不假设 2D LiDAR/ToF 已采购、安装、接线或 HIL-entry。
- `2026.05.19_00-01_elevator-assist-action-feedback-mainline/final.md`：已有 elevator action feedback software proof，但明确不等于真实电梯、真实 Nav2/fixed-route、HIL 或 delivery success。
- `2026.05.19_02-03_elevator-feedback-task-record-trace/final.md`：已有 `elevator_action_feedback_trace`、`robot_diagnostics_elevator_action_feedback_trace_summary` 和 mobile/web 只读 panel，但 final 明确仍缺真实 route/elevator field materials。
- `2026.05.19_03-04_pr5-review-thread-closeout/final.md`：PR #5 thread closeout 只证明 mainline docs 可判定，不证明 reviewer 已关闭 thread，也不证明真实硬件材料已补齐。

## 本轮核心抓手

本轮创建 Epic 规划，后续实现目标命名为 `elevator_field_evidence_trace_callback_intake`。

该能力应只读消费：

- 现场 owner 未来回填的 safe callback packet。
- 现有 `elevator_action_feedback_trace`。
- `robot_diagnostics_elevator_action_feedback_trace_summary` 或等价 diagnostics/mobile summary。
- route/elevator required materials，包括真实门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、现场 task record、dropoff/cancel completion、delivery result。

所有输出必须保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 需要做什么

本规划阶段只创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现阶段由 3 个并行 owner 执行：

- Autonomy Algorithm Engineer：实现 PC evidence intake gate、fixtures/focused tests、schema/docs。
- Robot Platform Engineer：实现 diagnostics safe alias、fail-closed tests、Robot contract docs。
- User Touchpoint Full-Stack Engineer：实现 mobile/web 只读 panel、fixture、targeted tests、mobile flow docs。
- Product Manager / OKR Owner：实现后创建 `tech-done.md`、`side2side_check.md`、`final.md`，并按实际证据决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

## 优先级和验收口径

P0：safe `evidence_ref` 必须一致；不一致或缺失时 intake 输出 blocked / not proven。

P0：不得启用 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor、command 或任何 primary action。

P1：callback packet 只能接受 phone-safe / redacted / metadata-only 字段；不得暴露 raw ROS topic、本机路径、串口、波特率、凭证、traceback 或完整内部日志。

P1：缺真实材料时必须明确列出 `missing_required_materials`，不得补默认成功值。

P2：Robot/mobile 展示只读摘要，帮助现场 owner 复盘下一步材料回填动作。

## 风险、阻塞和需要补齐的证据链

- 本机只有 Docker，没有真实硬件；不能宣称 HIL、WAVE ROVER/UART、真实电梯、真实 Nav2/fixed-route、真实 phone/browser 或 O5 external proof。
- PR #4 仍缺真实 route/elevator field pass：真实电梯门状态、真实楼层确认、人工协助记录、真实路线运行、真实 completion signal、真实 dropoff/cancel completion、真实 delivery result。
- PR #5 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 本 sprint 若后续只完成 planning，不得上调 OKR 百分比，也不得创建虚假的 `tech-done.md` / `final.md` 收口。
