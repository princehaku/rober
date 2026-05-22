# Field Evidence Rerun Acceptance Handoff Intake PRD

Run time: 2026-05-23 00:01 Asia/Shanghai

## 用户价值和产品北极星

普通用户价值不是看到更多内部证据名称，而是在现场 owner/support 回执仍未形成真实验收材料时，手机端明确显示“当前只是交接回执入口，不可控制、不可声明送达”。field owner / support / reviewer 的价值是拿到一条安全 intake 链路，能确认上一轮 handoff 已被收到、哪些 safe material refs 被接收、哪些真实材料仍缺、哪些 unsafe 或 success claim 被拒绝。

产品北极星保持不变：`rober` 是面向普通手机用户的低成本 ROS2 垃圾投递机器人，核心是可验证地完成送垃圾、电梯 assisted delivery 和安全回退。`field_evidence_rerun_execution_result_acceptance_handoff_intake` 只能把上一轮 safe review handoff 转成 field owner/support acknowledgement intake，不能把 Docker/local artifact 写成真实送达、真实手机/browser、Objective 5 external proof、Objective 1 HIL 或 PR #5 resolution。

## 问题陈述

上一轮 `field_evidence_rerun_execution_result_acceptance_review_handoff` 已经能输出安全的 handoff summary，但还缺一层接收 field owner/support 回执与 safe material refs 的 intake artifact。

如果没有这一层：

- owner 只能看到 handoff package，但没有安全入口说明“我收到交接，并将按同一 safe `evidence_ref` 补材料”。
- support 不能区分“已收到回执但仍缺材料”与“真实材料已验收通过”。
- reviewer 可能把 acknowledgement 当作 PR #5 thread resolved 或 route/elevator field pass。
- mobile/web 可能只显示交接状态，而没有明确 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## OKR 映射

### Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环

本轮服务送达任务和电梯 assisted delivery 的真实材料回填入口：intake artifact 必须列出真实 task record、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 或 delivery result 等后续验收材料。它不证明真实投递、不证明真实电梯通行、不证明 delivery success。

### Objective 3：可验证导航与固定路线能力

本轮把真实 Nav2/fixed-route runtime log 和 route completion signal 明确为 acceptance handoff intake 的 required material。它只证明 intake checklist 和 fail-closed 消费链路，不证明真实 Nav2/fixed-route runtime pass。

### Objective 4：手机用户体验与低成本量产边界

本轮需要 mobile/web 展示只读 intake panel，中文优先解释 intake status、缺口、owner/support next step 和安全边界。Start Delivery、Confirm Dropoff、Cancel 必须保持 disabled；`primary_actions_enabled=false` 是验收硬门槛。

### Objective 5：云中转 + OSS/CDN 数据通路产品化

Objective 5 当前约 68% 且最低，但没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result materials。本轮不继续 O5 metadata depth，不产生 O5 completion lift。

### Objective 1：硬件协议可信底盘

Objective 1 当前约 81%。PR #5 live evidence：`PRRT_kwDOSWB9286CJ3tQ` resolved、`PRRT_kwDOSWB9286CJ3tU` resolved、`PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`。本机没有真实 WAVE ROVER/UART/HIL 或 2D LiDAR/ToF material。本轮不声明 O1 HIL、不声明 PR #5 resolution。

## KR 拆解或更新

KR-A Autonomy PC handoff intake gate:

- 输入：上一轮 acceptance review handoff safe output、Robot safe alias 或 field owner/support safe acknowledgement packet。
- 输出：`field_evidence_rerun_execution_result_acceptance_handoff_intake` artifact/summary。
- 判定：`ready_for_acceptance_handoff_owner_intake_not_proven`、`intake_needs_more_material`、`intake_evidence_ref_mismatch`、`intake_unsafe_rejected`、`blocked_missing_review_handoff`。
- 验收：focused py_compile、unit tests、CLI help、required `rg`、scoped `git diff --check`。

KR-B Robot diagnostics safe alias:

- 输入：PC handoff intake gate safe summary。
- 输出：`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary`。
- 要求：只暴露 safe metadata，不暴露 raw artifacts、local paths、checksums、tracebacks、ROS topics、`/cmd_vel`、serial/UART、WAVE ROVER details、credentials、DB/queue URLs。
- 验收：diagnostics py_compile、focused unittest、required `rg`、scoped `git diff --check`。

KR-C Full-Stack mobile/web read-only panel:

- 输入：Robot diagnostics safe alias 或兼容 safe summary fixture。
- 输出：只读“现场证据复跑执行结果验收交接回执入口”panel。
- 要求：展示 intake status、safe evidence_ref、accepted safe material refs、missing required materials、owner/support next step、evidence boundary、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`；不得启用主操作。
- 验收：`node --check`、fixture JSON validation、focused mobile unittest、required `rg`、scoped `git diff --check`。

KR-D Product closeout:

- 输入：A/B/C worker reports。
- 输出：`tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 的保守收口。
- 要求：只在真实证据出现时更新 OKR percentage；否则写清 no OKR lift。
- 验收：closeout files exist、required `rg`、scoped `git diff --check`。

## 本轮核心抓手

把“acceptance review handoff 已交出”升级为“field owner/support safe acknowledgement 已可接收并 fail closed 消费”，统一 PC、Robot、mobile/web 三个消费面的硬边界：

- `source=software_proof`
- `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## 需要做什么

1. Autonomy worker 新增 PC-only handoff intake gate，消费上一轮 review handoff safe output 和 owner/support safe acknowledgement packet，并输出 intake artifact/summary。
2. Robot worker 新增 diagnostics safe alias，让 operator gateway 只读暴露安全摘要。
3. Full-Stack worker 新增 mobile/web read-only panel 和 fixture，用户只能看到安全状态、缺口和下一步。
4. Product worker 在 A/B/C 完成后收口 sprint，并保守更新 OKR/progress log。

## 优先级和验收口径

P0:

- 所有输出必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 缺上一轮 review handoff、缺 owner/support acknowledgement、缺 required material、同一 `evidence_ref` 不一致、unsafe copy、success claim、control enable、敏感信息均 fail closed。
- mobile/web 不得启用 Start Delivery、Confirm Dropoff、Cancel。

P1:

- Intake artifact 必须清楚区分 accepted safe material refs、missing required materials、rejected unsafe material refs 和 next required evidence。
- Robot/mobile 只消费 safe summary，不读取 raw material 或 raw artifact。
- docs 同步更新，明确本轮不是真实 field pass。

P2:

- 保持测试围栏：focused unit tests、py_compile、node check、json.tool、required `rg`、scoped diff check；不扩大到无关 broad regression。

## 对应责任 Engineer

- A：Autonomy Algorithm Engineer，负责 PC-only handoff intake gate、tests、`pc-tools/README.md` 和 `docs/interfaces/evidence_contracts.md`。
- B：Robot Platform Engineer，负责 diagnostics alias、tests、`docs/interfaces/ros_runtime_contracts.md`。
- C：User Touchpoint Full-Stack Engineer，负责 `mobile/web` panel/fixture/tests、`docs/product/mobile_user_flow.md`。
- D：Product Manager / OKR Owner，负责 A/B/C 后的 sprint closeout、OKR/progress log。

## 风险、阻塞和需要补齐的证据链

- 当前没有真实 field owner material packet；本轮只能验证 owner/support acknowledgement intake 的 fail-closed 行为。
- 当前没有真实 route/elevator pass、真实 Nav2/fixed-route runtime、真实手机/browser、dropoff/cancel completion、delivery result；不得提升 Objective 2/3/4 真实完成度。
- 当前没有 O5 external proof；不得继续 O5 metadata depth 或写成 external proof。
- 当前没有 O1 硬件材料和 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution；不得写成 HIL 或 reviewer closure。

## 非目标

- 不新增硬件假设，不改 WAVE ROVER、UART、引脚、电压、波特率、速度映射或底盘协议。
- 不新增 robot command endpoint。
- 不读取真实外部云、OSS/CDN、DB/queue、4G 或生产凭证。
- 不把 PR #5 `PRRT_kwDOSWB9286CJ3tX` 写成 resolved。
- 不提交 git；本规划任务只创建下一轮 sprint 计划文档。
