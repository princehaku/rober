# Field Evidence Rerun Acceptance Owner Response Reviewer ACK Intake PRD

Run time: 2026-05-23 08:09 Asia/Shanghai

## 用户价值和产品北极星

北极星：普通手机用户最终能完成可验证的垃圾投递闭环，support、field owner 和 reviewer 能在失败或缺材料时快速知道下一步该补什么，而不是从 raw logs、ROS topics、手机 fixture 或 GitHub thread 里猜。

本 sprint 的用户价值不是新增真实控制能力，而是把 owner-response review handoff 加 reviewer ACK packet 变成 reviewer ACK intake：当现场材料还不能证明真实 delivery、dropoff、cancel、route/elevator 或 phone/browser pass 时，系统仍能给出安全、可读、可复核的 reviewer ACK 入口状态。

## 问题陈述

当前最低 Objective 5 仍约 68%，但 Docker-only 环境没有真实 external cloud proof。Objective 1 仍约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`，没有真实传感器和 HIL 材料。

上一轮完成了 `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff`，证明 safe owner-response review decision 可以被转成 owner/support/reviewer handoff metadata。本轮要把这个 handoff 和 reviewer ACK packet 转成 intake metadata，让后续 reviewer ACK review decision 能按同一 safe `evidence_ref` 做接受、重分配、补材料或拒绝判断。

## OKR 映射

- Objective 5：最低但当前不可做真实 proof。本轮只做 software-proof reviewer ACK intake，不提高 68%。
- Objective 1：保留 PR #5 X thread unresolved 事实。本轮不提高 81%。
- Objective 2：不证明真实送达、电梯、dropoff/cancel completion 或 delivery result。
- Objective 3：不证明 Nav2/fixed-route runtime pass、route completion signal 或 field pass。
- Objective 4：提供手机 read-only 可见性，但不证明 true phone/browser proof，也不启用主操作。

## KR 拆解或更新

本轮不改 KR 文本、不新增百分比，只要求实现以下交付物：

- Capability: `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake`
- Boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_gate`
- Summary: Robot/mobile 可消费的 safe reviewer ACK intake metadata。
- Product closeout: `OKR.md` 与 `docs/process/okr_progress_log.md` 保持 no OKR percentage lift，并说明真实证据缺口。

## 本轮核心抓手

建立一条 read-only reviewer ACK intake contract：

- 输入：上一轮 owner-response review handoff safe summary + reviewer ACK packet。
- 输出：reviewer ACK intake status、safe `evidence_ref`、source handoff status、ACK reasons、required follow-up evidence、owner/support/reviewer next step。
- 默认安全：任何缺 source、缺 safe evidence_ref、unsafe ACK material、success/control wording、O5 external proof、O1 HIL、PR #5 resolution claim 都 fail closed。

## 范围内

- PC-only reviewer ACK intake evidence gate。
- Operator gateway diagnostics safe alias。
- `mobile/web` read-only reviewer ACK intake panel、fixture、focused tests 和 `docs/product/mobile_user_flow.md` 同步。
- Product closeout docs、`OKR.md`、`docs/process/okr_progress_log.md` 在实现后更新。
- Fenced validation commands only。

## 范围外

- 真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- 真实 WAVE ROVER/UART/HIL、2D LiDAR / ToF 安装、接线、电源、标定或 PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution。
- 真实 route/elevator field pass、Nav2/fixed-route runtime pass、route completion signal、真实电梯门状态、目标楼层确认、人工协助记录。
- 真实 dropoff/cancel completion、verified terminal delivery/dropoff/cancel result、delivery_success=true。
- true phone/browser proof、production app、真实 PWA prompt/userChoice。
- 新增控制 API、ACK/cursor/material/review/handoff/follow-up/owner-response routes 或任何 primary action enablement。

## 优先级和验收口径

- P0：所有输出必须包含 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 和 no OKR percentage lift。
- P0：Robot/mobile 不暴露 raw ROS topics、`/cmd_vel`、serial/UART details、baudrate、WAVE ROVER parameters、credentials、DB/queue URLs、raw artifacts、complete artifacts、checksums、tracebacks。
- P1：Task A/B/C 并行范围互不重叠，Task D 只在 A/B/C 完成后 closeout。
- P1：围栏验收通过，包括 py_compile、focused unittest、node/json checks、rg proof-boundary checks 和 scoped `git diff --check`。
- P2：实现后 docs under `docs/interfaces/` 和 `docs/product/` 同步，sprint `tech-done.md`、`side2side_check.md`、`final.md` 完整记录。

## 对应责任 Engineer

- `autonomy-engineer`：PC-only reviewer ACK intake gate。
- `robot-software-engineer`：operator gateway diagnostics safe alias。
- `full-stack-software-engineer`：mobile read-only panel、fixture、focused tests/docs。
- `product-okr-owner`：closeout docs、OKR/progress log、集成验证和 commit/push 交接。

## 风险、阻塞和证据链

- 当前环境只有 Docker，不能产出真实 O5/O1/O2/O3/O4 completion proof。
- 本 sprint 若顺利完成，也只能证明 safe metadata intake 可生成、可诊断、可读，不证明现场材料真实有效。
- `OKR.md` 不得提高百分比，除非 implementation 阶段实际拿到独立真实证据；按当前任务边界不预期发生。
- 后续仍需真实外部云材料、真实硬件材料、真实 route/elevator 材料、真实 terminal result 和真实手机/browser evidence 才能进入 OKR completion lift。

## 需要创建或更新的 sprint 文档

- 已创建/计划创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- implementation closeout 必须更新：`tech-done.md`、`side2side_check.md`、`final.md`。
