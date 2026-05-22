# Field Evidence Material Resolution Reviewer ACK Review Decision PRD

Run time: 2026-05-22 18:19 Asia/Shanghai

## User Value And Product North Star

用户价值不是让现场人员再读一堆原始 ACK 材料，而是让 support、reviewer、field owner 和手机端支持视图都能看到同一个安全结论：ACK 是否足够进入材料复核，还是必须转派、补充、拒绝或等待前置 intake。

产品北极星保持不变：普通用户只用手机理解机器人当前是否可控、为什么不可控、下一步谁处理；工程侧用 PC/Robot diagnostics/mobile 三端一致的 evidence summary 支撑售后和现场材料闭环。

## Problem

前置 sprint 已经交付 `field_evidence_material_resolution_reviewer_ack_intake`，但 intake 只说明 ACK 是否进入系统，不能替代复核决策。若缺少 reviewer ACK review-decision rung，现场材料链路会停在“收到了 ACK”而不是“ACK 是否足以进入下一步材料复核”。

当前不能通过 Objective 5 本地 wrapper 提升完成度，因为真实外部证据仍缺失；也不能通过 Objective 1 提升完成度，因为真实硬件材料仍缺失。因此本轮只推进不依赖真实外部/硬件环境的材料治理闭环，并保持 `no OKR percentage lift`。

## OKR Mapping

- Objective 5: 当前约 68%，最低。此 sprint 只提供 `software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate`，不证明 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、verified terminal result 或 delivery success；no OKR percentage lift。
- Objective 1: 当前约 81%。此 sprint 不提供 WAVE ROVER/UART/HIL、2D LiDAR/ToF、operator HIL report 或 PR #5 reviewer resolution；no OKR percentage lift。
- Objective 2/3/4: 当前约 99%。此 sprint 不证明 route/elevator field pass、Nav2/fixed-route runtime、dropoff/cancel completion、real phone/browser 或 delivery result；no OKR percentage lift。

## KR Breakdown

- KR-A: PC gate 能读取 reviewer ACK intake safe summary，并输出 reviewer ACK review-decision artifact。
- KR-B: Robot diagnostics 能以 phone-safe alias 暴露 review decision summary，不泄露 raw artifacts、路径、凭证、ROS topic、低层控制或硬件细节。
- KR-C: `mobile/web` 能只读展示 reviewer ACK review-decision，且 Start Delivery、Confirm Dropoff、Cancel 继续 fail closed。
- KR-D: 文档同步更新 `pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`、`docs/interfaces/operator_gateway_diagnostics.md`、`docs/product/mobile_user_flow.md`。
- KR-E: Product closeout 在 Engineer 完成后只保守更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，记录 no OKR percentage lift。

## Core Grab

本轮核心抓手是把“ACK 已摄取”升级为“ACK 可复核决策”，让后续材料复核或补件请求不再靠口头判断。它是现场材料证据链治理，不是交付成功或真实云/硬件证明。

## Required Product Behavior

状态建议：

- `accepted_for_material_review_not_proven`: ACK 足够进入下一步材料复核，但仍不是真实现场成功。
- `needs_reassignment_not_proven`: ACK 指向 owner/责任不匹配，需要转派。
- `needs_field_owner_supplement_not_proven`: ACK 存在但缺少 field owner 必要补充。
- `rejected_unsafe_ack_not_proven`: ACK 含 unsafe copy、成功断言、敏感信息或越权控制语义，必须拒绝。
- `blocked_missing_reviewer_ack_intake_not_proven`: 前置 ACK intake 缺失或不可用，不能做复核决策。

所有输出必须保留：

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `evidence_boundary=software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate`

## Priority And Acceptance

P0:

- PC gate、Robot diagnostics safe alias、mobile/web panel 三端消费同一决策语义。
- 所有 controls fail closed，不新增控制 API 或自动重放/重提交流程。
- focused tests 证明 accepted、reassignment、supplement、unsafe、missing intake 关键分支。

P1:

- docs 同步更新并清楚区分 software proof、not_proven、no OKR percentage lift。
- Product closeout 完成六文档链路并保守更新 OKR/progress log。

Acceptance:

- Engineer verification 命令全部通过。
- `rg` 可定位 capability、evidence boundary、Objective 5、no OKR percentage lift。
- `git diff --check` 对触达文件通过。

## Responsible Engineers

- `autonomy-engineer`: PC gate + PC/docs evidence contract。
- `robot-software-engineer`: diagnostics safe alias + diagnostics docs。
- `full-stack-software-engineer`: mobile/web panel + fixture + mobile flow docs。
- `product-okr-owner`: closeout docs、side-by-side acceptance、final、OKR/progress log conservative update。

## Risks And Evidence Gaps

- Objective 5 仍缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser、verified terminal result。
- Objective 1 仍缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF material、operator HIL report、PR #5 reviewer resolution。
- Objective 2/3/4 仍缺真实 route/elevator field pass、Nav2/fixed-route runtime、真实手机/browser、dropoff/cancel completion、delivery result。
- 本轮若 Engineer 只能证明 fixture/software path，必须在 closeout 中明确不是 OKR percentage lift。

## Required Sprint Docs

本 planning 任务创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Engineer 完成后 Product 必须补：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
