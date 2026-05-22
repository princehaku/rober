# Field Evidence Rerun Acceptance Backfill Review Decision PRD

Run time: 2026-05-22 22:23 Asia/Shanghai

## 用户价值和产品北极星

普通用户价值不是看到更多内部材料名，而是在现场复跑材料不足时，手机端和支持人员能准确知道“还差什么、为什么不能继续控制、下一步由谁补齐”。现场 owner 价值是把八类材料从 acceptance backfill 阶段推进到 review decision 阶段，明确能否进入 result acceptance review handoff。

产品北极星保持不变：`rober` 是低成本 ROS2 垃圾投递机器人，核心是可验证地完成送垃圾和电梯 assisted delivery，而不是把 Docker/local artifact 写成真实送达。任何 `field_evidence_rerun_execution_result_acceptance_backfill_review_decision` 输出都必须是 `software_proof`，并保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 问题陈述

已有 `field_evidence_rerun_execution_result_acceptance_packet` 和 `field_evidence_rerun_execution_result_acceptance_backfill`。上一轮 acceptance backfill 能把材料缺口变成可回填入口，但还没有一个 follow-on 把回填结果判定为：

- 可以进入 field rerun result acceptance review handoff。
- 仍缺材料，需要 owner 继续补齐。
- 同一 safe `evidence_ref` 不一致。
- 材料含 unsafe copy、success claim、控制启用或敏感信息，需要拒绝。
- acceptance backfill artifact/summary/Robot alias 缺失或不可消费。

没有这个 review decision，后续 Autonomy、Robot、Full-Stack worker 容易重复消费 backfill blocker，或者在 mobile/web 上只展示“已回填”而没有明确下一步。

## OKR 映射

### Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环

本轮服务送达任务的现场结果验收链路：task record、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 或 delivery result 必须在同一 safe `evidence_ref` 下进入 review decision。它不证明真实投递、不证明真实电梯通行、不证明 delivery success。

### Objective 3：可验证导航与固定路线能力

本轮把 Nav2/fixed-route runtime log 和 route completion signal 纳入 acceptance backfill review decision 的必检材料。它只验证材料 shape 和安全摘要，不证明真实 Nav2/fixed-route runtime pass。

### Objective 4：手机用户体验与低成本量产边界

本轮需要 mobile/web 展示只读 review decision panel，中文优先解释缺口、owner next step 和安全边界。Start Delivery、Confirm Dropoff、Cancel 必须保持 disabled；`primary_actions_enabled=false` 是验收硬门槛。

### Objective 5：云中转 + OSS/CDN 数据通路产品化

Objective 5 当前约 68% 且最低，但没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result。本轮不继续 O5 metadata depth，不产生 O5 completion lift。

### Objective 1：硬件协议可信底盘

Objective 1 当前约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 `is_resolved=false` / `hardware_material_pending`，本机也没有真实 WAVE ROVER/UART/HIL 或 2D LiDAR/ToF source/receipt。本轮不声明 O1 HIL、不声明 PR #5 resolution。

## KR 拆解

KR-A Autonomy PC gate:

- 输入：上一轮 acceptance backfill artifact/summary/Robot safe alias，以及可选 field owner material refs。
- 输出：`field_evidence_rerun_execution_result_acceptance_backfill_review_decision` artifact/summary。
- 判定：`ready_for_field_rerun_result_acceptance_review_handoff`、`needs_more_material`、`evidence_ref_mismatch`、`unsafe_rejected`、`blocked_missing_backfill`。
- 验收：focused py_compile、unit tests、CLI help、required `rg`、scoped `git diff --check`。

KR-B Robot diagnostics safe alias:

- 输入：PC gate safe summary。
- 输出：`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary`。
- 要求：只暴露 safe metadata，不暴露 raw artifacts、local paths、checksums、tracebacks、ROS topics、`/cmd_vel`、serial/UART、WAVE ROVER details、credentials、DB/queue URLs。
- 验收：diagnostics py_compile、focused unittest、required `rg`、scoped `git diff --check`。

KR-C Full-Stack mobile/web read-only panel:

- 输入：Robot diagnostics safe alias 或兼容 summary fixture。
- 输出：只读“现场证据复跑执行结果验收回填复核决策”panel。
- 要求：展示 decision、safe evidence_ref、missing/rejected categories、owner next step、evidence boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`；不得启用主操作。
- 验收：`node --check`、fixture JSON validation、focused mobile unittest、required `rg`、scoped `git diff --check`。

KR-D Product closeout:

- 输入：A/B/C worker reports。
- 输出：`tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 的保守收口。
- 要求：只在真实证据出现时更新 OKR percentage；否则写清 no OKR lift。
- 验收：closeout files exist、required `rg`、scoped `git diff --check`。

## 本轮核心抓手

把“材料回填”升级为“回填复核决策”，并且把 PC、Robot、mobile/web 三个消费面统一到同一边界：

- `source=software_proof`
- `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## 需要做什么

1. Autonomy worker 新增 PC gate，消费 acceptance backfill，并输出 review decision。
2. Robot worker 新增 diagnostics safe alias，让 operator gateway 只读暴露安全摘要。
3. Full-Stack worker 新增 mobile/web panel 和 fixture，用户只能看到安全状态和缺口。
4. Product worker 在 A/B/C 完成后收口 sprint，并保守更新 OKR/progress log。

## 优先级和验收口径

P0:

- 所有输出必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 缺 acceptance backfill、缺八类材料、同一 `evidence_ref` 不一致、unsafe copy、success claim、control enable、敏感信息均 fail closed。
- mobile/web 不得启用 Start Delivery、Confirm Dropoff、Cancel。

P1:

- Summary 字段要足够让支持人员知道 owner next step。
- Robot/mobile 只消费 safe summary，不读取 raw material 或 raw artifact。
- docs 同步更新，明确本轮不是真实 field pass。

P2:

- 保持测试围栏：focused unit tests、py_compile、node check、json.tool、required `rg`、scoped diff check；不扩大到无关 broad regression。

## 对应责任 Engineer

- A：Autonomy Algorithm Engineer，负责 PC gate、tests、`pc-tools/README.md` 和 `docs/interfaces/evidence_contracts.md`。
- B：Robot Platform Engineer，负责 diagnostics alias、tests、`docs/interfaces/ros_runtime_contracts.md`。
- C：User Touchpoint Full-Stack Engineer，负责 `mobile/web` panel/fixture/tests、`docs/product/mobile_user_flow.md`。
- D：Product Manager / OKR Owner，负责 A/B/C 后的 sprint closeout、OKR/progress log。

## 风险、阻塞和需要补齐的证据链

- 当前没有真实 field owner backfill materials；本轮只能验证 review decision gate 的 fail-closed 行为。
- 当前没有真实 route/elevator pass、真实 Nav2/fixed-route runtime、真实手机/browser、dropoff/cancel completion、delivery result；不得提升 Objective 2/3/4 真实完成度。
- 当前没有 O5 外部材料；不得继续 O5 metadata depth 或写成 external proof。
- 当前没有 O1 硬件材料和 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution；不得写成 HIL 或 reviewer closure。

## 非目标

- 不新增硬件假设，不改 WAVE ROVER、UART、引脚、电压、波特率、速度映射或底盘协议。
- 不新增 robot command endpoint。
- 不读取真实外部云、OSS/CDN、DB/queue、4G 或 GitHub reviewer state。
- 不提交 git；主会话负责集成提交。
