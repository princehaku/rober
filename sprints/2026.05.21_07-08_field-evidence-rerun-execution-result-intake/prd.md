# Field Evidence Rerun Execution Result Intake PRD

## 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给低成本 ROS2 小车后，小车能沿固定路线完成送达、电梯 assisted delivery、投放或人工取走，并且每一次结果都有可回放证据。本 sprint 的用户价值不是证明机器人真实完成了送达，而是让 execution handoff 后的现场 owner 回填结果有一个安全入口：结果包是缺失、已接收、被拒绝还是被阻塞，下一步该补什么证据，哪些内容仍然 `not_proven`。

## OKR 映射

- Objective 5：当前最低，约 68%。本 sprint 不直接推进 O5，因为最新 `cloud_poll_backoff_rate_limit_guard` final 已明确本地 O5 guard 不应继续重复；除非出现真实 external material 或 fresh unguarded failure mode，否则不能把本地 metadata guard 当作 O5 进度。
- Objective 1：约 81%。PR #5 live review state 仍保守：`PRRT_kwDOSWB9286CJ3tQ`、`PRRT_kwDOSWB9286CJ3tU` resolved；`PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`。PR #6 是 README/docs-only，不是 runtime/hardware/HIL/phone/browser/O5 external proof。本机没有 WAVE ROVER/UART/HIL、无真实 2D LiDAR / ToF materials，因此本 sprint 不提升 O1。
- Objective 2/3/4：本 sprint 服务 field evidence rerun 的 execution result intake 软件证明链。它让现场结果回填路径可执行、可复核、可在手机端安全展示，但不提升真实路线、电梯、手机、投放或送达完成度。

## KR 拆解或更新

- KR-A：PC gate 生成 `field_evidence_rerun_execution_result_intake` artifact/summary，承接 `field_evidence_rerun_execution_callback_review_handoff` 后的 owner execution result packet，并输出 intake status：`missing`、`accepted`、`rejected` 或 `blocked`。
- KR-B：Robot diagnostics 暴露 `robot_diagnostics_field_evidence_rerun_execution_result_intake_summary` safe alias，只给 operator 支持面和手机读取安全摘要。
- KR-C：mobile/web 增加只读“现场证据复跑执行结果回填”panel，展示 safe `evidence_ref`、result packet state、missing/rejected/blocked reason、next required evidence 和 evidence boundary，但不改变 Start Delivery / Confirm Dropoff / Cancel gating。
- KR-D：所有链路保留 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 和 `software_proof_docker_field_evidence_rerun_execution_result_intake_gate`。

## 本轮核心抓手

核心抓手是把 execution handoff 之后的“现场执行结果回填 packet”变成统一入口。入口必须回答：

- 现场 owner 是否回填了结果包。
- 回填包是否沿用同一 safe `evidence_ref`。
- 回填状态是 `missing`、`accepted`、`rejected` 还是 `blocked`。
- 被拒绝或阻塞时，阻塞原因和下一份材料是什么。
- 哪些字段只能作为 software proof metadata，不能写成 `delivery_success=true` 或 field pass。

## 需要做什么

1. Autonomy PC gate：读取上一轮 execution callback review handoff summary 和可选 owner-safe result packet，生成 result-intake artifact 和 summary。
2. Robot diagnostics：把 result-intake summary 作为 safe alias 暴露，拒绝 unsafe/raw result material。
3. Full-Stack mobile/web：只读展示 result-intake summary，保持所有主操作 fail-closed。
4. Product closeout：后续实现完成后只可保守更新 OKR 和 sprint closeout，不把本 sprint 写成真实 proof。

## 优先级和验收口径

Priority P0:

- result-intake gate 必须 fail closed，不能把 missing/rejected/blocked packet 转成 field pass 或 success。
- safe copy 不能包含 raw ROS topics、`/cmd_vel`、serial/UART、WAVE ROVER、credential、DB/queue URL、OSS AK/SK、local path、checksum、traceback、complete artifact、success/control wording。
- mobile/web panel 不能发送 Start Delivery、Confirm Dropoff、Cancel、ACK、cursor、diagnostics fetch、queue scheduling、execution scheduling、callback submission、review submission、handoff submission、result submission 或 robot command request。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 必须继续呈现为 unresolved / `hardware_material_pending`；PR #6 必须继续呈现为 docs-only。

验收口径：

- PC gate、Robot alias、mobile panel 三个 worker 的围栏命令通过。
- required `rg` 能命中 `field_evidence_rerun_execution_result_intake`、`software_proof_docker_field_evidence_rerun_execution_result_intake_gate`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven`、`PRRT_kwDOSWB9286CJ3tX` 和 `PR #6`。
- 输出只能是 `software_proof` / metadata-only result intake，不得声称真实 field rerun、route/elevator pass、Nav2/fixed-route runtime、HIL、O5 external proof、PR #5 thread resolved、dropoff/cancel completion 或 delivery success。

## 对应责任 Engineer

- Autonomy Algorithm Engineer：PC result-intake gate、artifact/summary schema、focused unittest、PC evidence docs。
- Robot Platform Engineer：operator diagnostics safe alias、focused diagnostics unittest、runtime contract docs。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture、focused mobile unittest、mobile user flow docs。
- Product Manager / OKR Owner：sprint planning、验收口径、后续 OKR closeout 和 sprint final。

## 风险、阻塞和证据链

- O5 blocker：缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser external proof。
- O1 blocker：PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`，缺 mandatory sensor baseline vendor/source/procurement/installation/calibration/HIL-entry materials；PR #6 是 README/docs-only。
- Field-evidence blocker：仍缺真实 same-safe-`evidence_ref` task record、Nav2/fixed-route runtime log、route completion signal、elevator door/floor/human-assistance evidence、dropoff/cancel completion、delivery result 和 true phone/browser field material。
- 当前主机只有 Docker，没有真实硬件和真实现场材料；本 sprint 只能形成 `software_proof_docker_field_evidence_rerun_execution_result_intake_gate`。

## 非声明边界

This sprint must not claim real field rerun, real route/elevator field pass, real Nav2/fixed-route runtime, real task record generation, real route completion signal generation, real elevator door/floor/human assistance proof, real phone/browser validation, real PWA prompt/userChoice, WAVE ROVER/UART/HIL, delivery success, dropoff completion, cancel completion, O5 external proof, public HTTPS/TLS proof, 4G/SIM proof, OSS/CDN live traffic proof, production DB/queue or worker/cutover proof, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved.

## 需要创建或更新的 Sprint 文档

- Created in planning: `pre_start.md`, `prd.md`, `tech-plan.md`.
- To be created after implementation if this sprint continues: `tech-done.md`, `side2side_check.md`, `final.md`.
