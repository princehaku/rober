# Sprint 2026.05.19_05-06 Elevator Field Evidence Trace Callback Review Decision - Pre Start

## sprint_type: epic

Start time: 2026-05-19 05:03 Asia/Shanghai.

## 1. 上轮状态

上一轮 `2026.05.19_04-05_elevator-field-evidence-trace-callback-intake` 已完成 `elevator_field_evidence_trace_callback_intake` software-proof chain：

- PC gate 输出 `trashbot.elevator_field_evidence_trace_callback_intake_summary.v1`。
- Robot diagnostics 输出 `robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary` safe alias。
- mobile/web 只读展示 callback intake status、missing materials 和 owner handoff。

上轮 final 明确：`callback_packet_intake_ready_for_review_not_proven` 只表示安全回执包进入下一步复核，不是真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、dropoff/cancel completion、delivery success、WAVE ROVER/UART/HIL、真实手机/browser 或 O5 external proof。

## 2. 近期 PR 和评审证据

- PR #4 `Add elevator-assisted delivery capability to agents, registry and OKR` 已把 elevator-assisted delivery 写成主链必达能力，但 PR 自身没有 runtime integration test；后续 sprint 必须把 route/elevator 证据链继续往可判定、可回填方向推进。
- PR #5 `Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline` 的 review thread 仍暴露硬件 baseline 与 vendor source 风险：默认硬件集合和 mandatory `monocular + 2D LiDAR + ToF` baseline 口径曾不一致，且 mandatory sensor assumptions 必须引用 `docs/vendor/` 本地来源。当前本机没有真实硬件，不能把 PR #5 材料缺口写成 O1 实机进展。
- Live `OKR.md` 4.1 显示 O5 约 68% 为数字最低，但继续提升需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 phone/browser proof；本机 Docker-only 无法提供这些材料。
- Live `OKR.md` 4.1 显示 O1 约 81%，但仍缺真实 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料；同一硬件 blocker 不应继续被本地 wrapper 重复消费。

## 3. 本轮目标

本轮继续 Objective 2 / Objective 3 的 PR #4 route/elevator 现场证据链，新增 `elevator_field_evidence_trace_callback_review_decision`：

- 只读消费上一轮 callback intake artifact/summary。
- 基于 safe `evidence_ref`、missing/rejected materials、same-ref 状态和 unsafe copy 状态生成复核决策。
- 输出 `review_decision`、`decision_reasons`、`next_required_evidence`、`owner_handoff` 和 `rerun_commands`。
- Robot diagnostics 和 mobile/web 只读消费复核 summary，不开启控制动作。

## 4. Owner

- Autonomy Algorithm Engineer：PC review-decision gate、focused tests、接口文档。
- Robot Platform Engineer：diagnostics safe alias 和只读 fail-closed consumer。
- User Touchpoint Full-Stack Engineer：mobile/web 只读复核 panel 和 fixture。
- Product Manager / OKR Owner：实现后 OKR/进展日志/side2side/final 收口。

## 5. 风险和边界

- 本轮只能形成 Docker/local `software_proof`，不证明真实现场通过。
- 不读取真实材料目录，不访问 ROS graph、Nav2/fixed-route runtime、serial/UART、WAVE ROVER、云服务、DB/queue、OSS/CDN、4G 或真实手机/browser。
- 必须保留 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 如果 input summary 携带 raw path、credential、ROS topic、serial/UART/WAVE ROVER、success/control claim、`delivery_success=true` 或 `primary_actions_enabled=true`，review decision 必须 fail closed。
