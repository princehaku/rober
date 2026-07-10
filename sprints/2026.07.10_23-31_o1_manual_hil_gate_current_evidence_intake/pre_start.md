# O1 Manual HIL Gate Current Evidence Intake Pre-start

## sprint_type

sprint_type: epic

## 本轮目标

本轮目标是推进 O1 硬件可信底盘证据链，但不重复上一轮 `bounded_motion_feedback_material`。本 sprint 消费 `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/` 与 `sprints/2026.06.11_06-05_pc_structured_hil_report_readback/` 中已经存在的真实 PC proxy / 上位机只读材料，把 manual HIL gate、stop safety smoke、non-stop manual local reject、T1001 feedback readback 和 operator structured report 缺口收束为当前 O1 bundle 的可复验 additive section。

证据边界必须保持保守：本轮只证明真实上位机/PC readback 材料已被当前软件安全 intake，不证明 current live HIL pass、safe-to-control、delivery success、wheel direction、IMU/battery calibration、Nav2 route execution success 或真实 production cloud。

## 上轮未完成项和 blocker 扫描

- O5 仍是 `OKR.md` 4.1 节最低 Objective，约 `~85%`。
- 最近 O5 sprint `2026.07.10_17-22_o5_production_cutover_readiness_packet` 已明确 `okr_credit_allowed=false`，原因是没有真实 external production evidence。
- 当前工作区没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 或真实 phone/browser 材料，因此本轮不继续消费 O5 support-only blocker。
- 上一轮 `2026.07.10_22-29_o1_bounded_motion_feedback_material` 已消费 2026-06-10 historical bounded motion / T1001 / IMU-battery / odom material；本轮不能再重复 bounded-motion historical intake。

## 选择 O1 的原因

O1 当前约 `~91%`，是 O5 之后的最低可推进 Objective。当前没有真实 live HIL 材料，但仓库中存在不同于上一轮的真实 PC proxy / 上位机 gate 材料：

- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/gate_decision_before.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/stop_safety_smoke.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/manual_forward_expected_reject.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/proxy_smoke_result.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/remote_readback/after_api_base_feedback-samples_latest.json`
- `sprints/2026.06.11_06-05_pc_structured_hil_report_readback/artifacts/real_board_operator_report_direct_192_168_1_11_8787.json`
- `sprints/2026.06.11_06-05_pc_structured_hil_report_readback/artifacts/real_board_robot_control_summary_192_168_1_11_8787.json`

这些材料能证明当前 manual HIL gate 是 fail-closed 的：stop 可经 PC proxy 转发，非 stop manual request 被本地拒绝且远端 `/api/base/manual` 未调用，T1001 feedback request 可读回，operator structured report 只作为材料 claim，不替代 HIL。

## Owner

- 主责 owner：`robot-hardware-engineer`
- Product closeout：`product-okr-owner`
- 主节点职责：拆解、派单、验收、必要汇总，不直接写产品代码或运行实现验证命令。

## 验收口径

- 新增或扩展 O1 bundle additive section，例如 `manual_hil_gate_current_evidence_material`。
- 正向 CLI 必须从默认 artifacts 输出 ready-not-HIL-pass 状态，并包含 manual gate blocked、missing fields、stop safety smoke forwarded、manual non-stop local reject、remote manual not called、T1001 feedback observed、operator structured report material-only 等摘要。
- 安全字段必须固定 false：`hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 任何 dangerous true、远端 manual 被调用、缺关键 artifact、unsafe path/url/token/raw 泄漏、试图把 `delivery_success` 或 `hil_pass` 提升为 true 时必须 fail closed。
- 同步更新硬件文档和本 sprint `tech-done.md`。

## 风险边界

- 本轮不发送 `/cmd_vel`、不调用 `/api/base/manual`、不写串口、不启动 Nav2。
- 本轮不证明真实 HIL pass 或安全可控，只证明已有 real-board/PC gate 材料被当前软件合同安全消费。
- 若正向材料中包含 `delivery_success=true` 这类 operator claim，只能作为 material-only claim 展示，顶层必须仍为 `delivery_success=false`。
