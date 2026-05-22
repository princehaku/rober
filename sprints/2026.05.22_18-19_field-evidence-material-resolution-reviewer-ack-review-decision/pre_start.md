# Field Evidence Material Resolution Reviewer ACK Review Decision Pre-Start

Run time: 2026-05-22 18:19 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_material_resolution_reviewer_ack_review_decision`

Evidence boundary: `software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate`

## User Value And Product North Star

普通手机用户的北极星仍是：不懂 ROS2、串口、硬件或云基础设施，也能从手机知道机器人是否可控、为什么不可控、下一步由谁补材料。这个 sprint 不直接让机器人送达垃圾，而是把 reviewer/support/field-owner ACK intake 之后的复核判断固化成可审计、可回放、可在 PC/Robot/mobile 三端一致展示的 fail-closed 决策点。

本轮价值是减少现场材料回补链路的歧义：当 ACK 到达后，系统必须能明确判断是可进入材料复核、需要转派、需要 field owner 补充，还是 ACK 本身不安全或缺失。所有状态都必须保持 `source=software_proof`、`not_proven`、`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`。

## Background Evidence

- `OKR.md` 4.1 显示 Objective 5 约 68%，仍是最低完成度，但本机只有 Docker，没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser 或 verified terminal result material。
- Objective 1 约 81%，仍缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF material、operator HIL report、PR #5 reviewer resolution。
- `sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/final.md` 已完成 `field_evidence_material_resolution_reviewer_ack_intake`，下一步应把 ACK intake 转成 reviewer ACK review decision。
- `sprints/2026.05.22_17-18_mobile-current-panel-browser-proof-refresh/final.md` 只证明本地 browser current panels；明确 `no OKR percentage lift`，不能作为 O5 或 O4 真实证据。

## Scope Decision

本轮不是再刷新 browser proof，也不是继续堆 Objective 5 本地 wrapper。方向锁定为 `field_evidence_material_resolution_reviewer_ack_review_decision`，把前置 ACK intake 的材料转成可复核决策，并同步 PC gate、Robot diagnostics safe alias、mobile/web read-only panel、相关 docs 和 sprint closeout。

允许 Engineer 在实现阶段设计的建议状态：

- `accepted_for_material_review_not_proven`
- `needs_reassignment_not_proven`
- `needs_field_owner_supplement_not_proven`
- `rejected_unsafe_ack_not_proven`
- `blocked_missing_reviewer_ack_intake_not_proven`

若现有项目命名风格已有更精确枚举，Engineer 可以微调，但必须保留 `not_proven` 后缀和 fail-closed 语义。

## Owner Split

- Autonomy owner: PC evidence gate, focused unittest, `pc-tools/README.md`, `docs/interfaces/evidence_contracts.md`。
- Robot owner: diagnostics safe alias `robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary`, focused diagnostics unittest, `docs/interfaces/operator_gateway_diagnostics.md`。
- Full-Stack owner: `mobile/web` read-only panel, fixture, focused mobile unittest, `docs/product/mobile_user_flow.md`。
- Product owner: closeout docs, side-by-side acceptance, final, conservative `OKR.md` and progress-log update after Engineer evidence lands。

## Explicit Non-Claims

This sprint is not O5 external proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not true phone/browser proof, not verified terminal result, not O1 HIL, not WAVE ROVER/UART proof, not PR #5 resolution, not route/elevator field pass, not dropoff/cancel completion, and not delivery success.

Expected OKR result: no OKR percentage lift.

## Required Sprint Documents

Planning phase creates:

- `sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/pre_start.md`
- `sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/prd.md`
- `sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/tech-plan.md`

Implementation closeout must later add:

- `sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/tech-done.md`
- `sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/side2side_check.md`
- `sprints/2026.05.22_18-19_field-evidence-material-resolution-reviewer-ack-review-decision/final.md`
