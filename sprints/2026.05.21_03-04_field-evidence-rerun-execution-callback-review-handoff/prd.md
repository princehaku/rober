# Field Evidence Rerun Execution Callback Review Handoff PRD

## 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给低成本 ROS2 小车后，小车能沿固定路线完成送达、电梯 assisted delivery、投放或人工取走，并且每一次结果都有可回放证据。本 sprint 的用户价值不是证明机器人真实完成了送达，而是把上一轮 execution callback review decision 转成清晰的 owner handoff：现场 owner 下一步该补什么证据、用哪个 same-safe-`evidence_ref`、哪些 rerun/reconciliation guidance 可执行、哪些内容仍然 `not_proven`。

## OKR 映射

- Objective 5：当前最低，约 68%。本 sprint 不直接推进 O5，因为 Docker-only host 没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 true phone/browser external proof；近期 O5 local guards 已是 metadata/software proof，不能再堆同类 blocker。
- Objective 1：约 81%。PR #5 已 merge，但 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false`，保守 reply comment id `3269642220` 不等于 thread resolved，也不是真实硬件证明。本机无 WAVE ROVER/UART/HIL、无真实 2D LiDAR / ToF materials，因此本 sprint 不提升 O1。
- Objective 2/3/4：本 sprint 只服务 field evidence rerun 的 owner handoff、next evidence、rerun guidance 软件证明链。它可以让现场复跑证据链更可执行，但不提升真实路线、电梯、手机、投放或送达完成度。

## KR 拆解或更新

- KR-A：PC gate 生成 `field_evidence_rerun_execution_callback_review_handoff` artifact/summary，承接上一轮 review decision 并输出 owner handoff、next required evidence、rerun guidance、reconciliation guidance 和 safe copy。
- KR-B：Robot diagnostics 暴露 `robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary` safe alias，只给手机和 operator 支持面读取安全摘要。
- KR-C：mobile/web 增加只读“现场证据复跑执行回执复核交接”panel，展示 owner handoff、next evidence 和 rerun guidance，但不改变 Start Delivery / Confirm Dropoff / Cancel gating。
- KR-D：所有链路保留 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 和 `software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate`。

## 本轮核心抓手

核心抓手是把“复核决策”变成“下一次现场 owner 能执行的交接包”。交接包必须回答：

- 哪个 owner 负责下一份真实材料。
- 哪个 same-safe-`evidence_ref` 必须继续沿用。
- 下一份证据最少需要哪些字段和材料。
- 哪些 rerun/reconciliation 步骤可执行。
- 哪些缺口仍然不能写成 `delivery_success=true` 或 field pass。

## 需要做什么

1. Autonomy PC gate：读取上一轮 review decision summary，生成 handoff artifact 和 summary。
2. Robot diagnostics：把 handoff summary 作为 safe alias 暴露，拒绝 unsafe/raw material。
3. Full-Stack mobile/web：只读展示 handoff summary，保持所有主操作 fail-closed。
4. Product closeout：后续实现完成后只可保守更新 OKR 和 sprint closeout，不把本 sprint 写成真实 proof。

## 优先级和验收口径

Priority P0:

- handoff gate 必须 fail closed，不能把 missing/rejected/blocked decision 转成 ready 或 success。
- safe copy 不能包含 raw ROS topics、`/cmd_vel`、serial/UART、WAVE ROVER、credential、local path、checksum、traceback、complete artifact、success/control wording。
- mobile/web panel 不能发送 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor、diagnostics fetch、queue scheduling、execution scheduling、callback submission、review submission 或 robot command request。

验收口径：

- PC gate、Robot alias、mobile panel 三个 worker 的围栏命令通过。
- required `rg` 能命中 `field_evidence_rerun_execution_callback_review_handoff`、`software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven`。
- 输出只能是 `software_proof` / metadata-only handoff，不得声称真实 field rerun、route/elevator pass、HIL、O5 external proof、PR #5 thread resolved、dropoff/cancel completion 或 delivery success。

## 对应责任 Engineer

- Autonomy Algorithm Engineer：PC handoff gate、artifact/summary schema、focused unittest、PC evidence docs。
- Robot Platform Engineer：operator diagnostics safe alias、focused diagnostics unittest、runtime contract docs。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture、focused mobile unittest、mobile user flow docs。
- Product Manager / OKR Owner：sprint planning、验收口径、后续 OKR closeout 和 sprint final。

## 风险、阻塞和证据链

- O5 blocker：缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser external proof。
- O1 blocker：PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false`，缺 mandatory sensor baseline vendor/source materials；PR #5 reply comment id `3269642220` 只是保守回复，不是 reviewer resolution。
- PR #6 blocker boundary：README/docs-only、无 review threads，不是 runtime/hardware/HIL/phone/browser/O5 external proof。
- Field-evidence blocker：仍缺真实 same-safe-`evidence_ref` task record、Nav2/fixed-route runtime log、route completion signal、elevator door/floor/human-assistance evidence、dropoff/cancel completion、delivery result 和 true phone/browser field material。

## 非声明边界

This sprint must not claim real field rerun, real route/elevator field pass, real Nav2/fixed-route runtime, real task record generation, real route completion signal generation, real elevator door/floor/human assistance proof, real phone/browser validation, real PWA prompt/userChoice, WAVE ROVER/UART/HIL, delivery success, dropoff completion, cancel completion, O5 external proof, public HTTPS/TLS proof, 4G/SIM proof, OSS/CDN live traffic proof, production DB/queue or worker/cutover proof, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved.

## 需要创建或更新的 Sprint 文档

- Created in planning: `pre_start.md`, `prd.md`, `tech-plan.md`.
- To be created after implementation if this sprint continues: `tech-done.md`, `side2side_check.md`, `final.md`.
