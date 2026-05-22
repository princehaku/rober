# Field Evidence Rerun Acceptance Review Handoff Pre-Start

Run time: 2026-05-22 23:04 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_rerun_execution_result_acceptance_review_handoff`

Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate`

## 开工证据

- `OKR.md` 4.1 当前最低 Objective 是 Objective 5，约 68%。但同一节和第 6 节都明确：没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result material 时，不要继续增加本地 O5 metadata depth。
- Objective 1 约 81%，但当前没有真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF material、operator HIL report 或 reviewer resolution。PR #5 live review threads 已复核：`PRRT_kwDOSWB9286CJ3tQ` resolved，`PRRT_kwDOSWB9286CJ3tU` resolved，`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`。
- 上一轮 sprint `sprints/2026.05.22_22-23_field-evidence-rerun-acceptance-backfill-review-decision/` 已完成 `field_evidence_rerun_execution_result_acceptance_backfill_review_decision`，边界为 `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate`。
- 上一轮 `final.md` 和 `tech-done.md` 明确输出 ready state `ready_for_field_rerun_result_acceptance_review_handoff`，并把 remaining risk 指向真实 field rerun result acceptance review handoff 需要同一 safe `evidence_ref` 的真实材料。
- 本轮不是重复判定 backfill review decision，而是把上一轮 safe output 转成可交给 field owner / support / reviewer 的 handoff package。

## 用户价值和产品北极星

用户价值：现场 owner、support 和 reviewer 需要一份可执行交接包，知道上一轮 acceptance backfill review decision 的结论、同一 safe `evidence_ref`、仍缺的真实材料、禁止声明的范围和下一步动作。普通手机用户仍只看到安全的只读状态，不会被误导为任务已真实送达或可以继续控制。

产品北极星：`rober` 要成为低成本、手机可用、证据可复盘的 ROS2 垃圾投递机器人。当前 Docker/local handoff package 的价值是把真实 field rerun result acceptance review 所需证据交接清楚，不是替代真实 route/elevator pass、真实手机/browser、delivery success、O5 external proof、O1 HIL 或 PR #5 resolution。

## 本轮核心抓手

本轮实现 `field_evidence_rerun_execution_result_acceptance_review_handoff`：消费上一轮 review decision 的 safe output，生成 PC-only handoff gate、Robot diagnostics safe alias、mobile/web read-only panel，并把 handoff package 明确交给 field owner / support / reviewer。

Handoff package 必须包含：

- capability、evidence boundary 和 source：`software_proof`。
- same safe `evidence_ref`，但不暴露 raw artifact、local path、checksum、traceback 或敏感材料。
- 上一轮 decision：`ready_for_field_rerun_result_acceptance_review_handoff`。
- reviewer/support/field owner next step。
- required real-material checklist：真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 或 delivery result、真实手机/browser evidence。
- hard boundary：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## OKR 映射

- Objective 2：把送达任务、电梯 assisted delivery 和现场复跑结果验收从 review decision 推进到 handoff，方便后续真实 field owner 按同一 `evidence_ref` 补齐材料。
- Objective 3：把 route completion signal 与 Nav2/fixed-route runtime log 的真实材料要求纳入 handoff checklist，但不声明真实路线通过。
- Objective 4：让 mobile/web 只读展示 handoff status、缺口、owner next step 和安全边界，不启用 Start Delivery、Confirm Dropoff 或 Cancel。
- Objective 5：仍是最低约 68%，但缺真实 external proof；本轮不做 O5 metadata depth，不产生 Objective 5 completion lift。
- Objective 1：约 81%，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；本轮不处理硬件材料 closure，不产生 HIL 或 reviewer resolution。

## 本轮范围边界

In scope:

- 规划 A/B/C/D 四个任务，后续由对应 Engineer / Product owner 实现和收口。
- A Autonomy：新增 PC-only handoff gate、focused tests、`pc-tools/README.md`、`docs/interfaces/evidence_contracts.md`。
- B Robot：新增 Robot diagnostics safe alias、diagnostics focused tests、`docs/interfaces/ros_runtime_contracts.md`。
- C Full-Stack：新增 `mobile/web` read-only panel/fixture/focused tests、`docs/product/mobile_user_flow.md`。
- D Product：A/B/C 完成后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

Out of scope:

- 不声明真实 route/elevator field pass。
- 不声明真实手机/browser、真实 iPhone/Android device behavior、PWA prompt/userChoice 或 production app proof。
- 不声明 delivery success、dropoff completion、cancel completion 或 verified terminal result。
- 不声明 Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。
- 不声明 Objective 1 HIL、真实 WAVE ROVER/UART、真实 `/odom`、`/imu/data`、`/battery` 或 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution。

## Owner 和启动规则

- A Autonomy Algorithm Engineer：PC-only handoff gate、focused tests、evidence docs。
- B Robot Platform Engineer：Robot diagnostics safe alias、focused tests、runtime contract docs。
- C User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture、focused tests、mobile flow docs。
- D Product Manager / OKR Owner：只在 A/B/C 完成后做 closeout、OKR 和 progress log。

本 sprint 是跨 owner Epic。`tech-plan.md` 完成后必须并行启动 A/B/C 三个 Engineer worker；D Product 不得抢先写 closeout 或更新 OKR。

## 风险、阻塞和证据缺口

- O5 仍缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal result。
- O1 仍缺真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF SKU/source/receipt、采购/安装/接线/电源/标定、operator HIL report、PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution。
- O2/O3/O4 仍缺真实 same-safe-`evidence_ref` field materials：真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result、真实手机/browser evidence。
- 本轮只能形成 `software_proof` handoff package。所有 summary 和 UI 必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

## 需要创建或更新的 sprint 文档

本规划任务创建：

- `sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/pre_start.md`
- `sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/prd.md`
- `sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/tech-plan.md`

A/B/C 实现完成后，D 必须创建或更新：

- `sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/tech-done.md`
- `sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/side2side_check.md`
- `sprints/2026.05.22_23-24_field-evidence-rerun-acceptance-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
