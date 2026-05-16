# Sprint 2026.05.16_23-24 Route Task Field Result Reconciliation - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动新 Epic sprint：`route_task_field_retest_result_reconciliation`。

目标是在 Docker-only 条件下，把上一轮 `route_task_field_retest_result_intake`、再上一轮 `route_task_field_retest_session_handoff`、以及 `route_task_field_retest_execution_pack` 相关摘要，按同一 `evidence_ref` 做 fail-closed 结果复账。复账范围覆盖八类现场结果材料：

- `nav2_or_fixed_route_runtime_log`
- `route_completion_signal`
- `task_record`
- `door_state`
- `target_floor_confirmation`
- `human_assistance_note`
- `dropoff_or_cancel_completion`
- `delivery_result`

统一证据边界固定为：

- `software_proof_docker_route_task_field_retest_result_reconciliation_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

本轮不宣称真实现场通过、真实电梯、真实 Nav2/fixed-route、真实手机/browser、WAVE ROVER/UART/HIL 或 Objective 5 external proof。

## 2. 用户价值和产品北极星

用户价值：现场复测结果不再停留在“入口已准备”，而是能对同一 `evidence_ref` 的交接包、结果入口和八类现场材料做一致性复账。现场同学、Robot diagnostics 和手机端都只能看到安全摘要、缺失项、mismatch 和下一步动作，避免把 intake readiness 误解成 field pass。

产品北极星：继续把 `rober` 做成普通手机用户可理解、现场支持可复测、证据链可复盘的低成本 ROS2 自主垃圾投递机器人。本轮推进 Objective 2 / Objective 3 的 route-task field result reconciliation，不推进本地 O5 metadata depth。

## 3. 已核对证据

- `OKR.md` 4.1 显示 Objective 5 当前数值最低，约 66%；但当前主机 Docker-only，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration，因此不能继续堆本地 O5 metadata wrapper。
- 最新 sprint `sprints/2026.05.16_22-23_route-task-field-retest-result-intake/final.md` 建议：若仍没有 O5 外部材料，继续围绕同一 `evidence_ref` 推进真实现场材料回填或 field result reconciliation，不要把 intake readiness 当 field pass。
- 最近三轮已完成 `route_task_field_retest_execution_pack -> route_task_field_retest_session_handoff -> route_task_field_retest_result_intake`，但仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- GitHub PR #4 已把 elevator-assisted delivery 写成主线必须能力，因此本轮必须继续覆盖 `door_state`、`target_floor_confirmation`、`human_assistance_note`，但只作为 software-proof reconciliation，不写成真实电梯闭环。
- GitHub PR #5 review threads 仍有硬件基线、2D LiDAR、ToF、vendor source 的 P1/P2 风险；但 `2026.05.16_17-18` 和 `2026.05.16_18-19` 已连续两轮消费该硬件/source/config blocker，上一轮已按 `AGENTS.md` 同一 blocker 红线转向 O2/O3，本轮继续避免第三次消费同一 blocker。

## 4. 本轮核心抓手

本轮核心抓手是 `route_task_field_retest_result_reconciliation`：

1. PC artifact/summary：新增 dependency-free reconciliation contract，读取上一轮 result intake / session handoff / execution pack 摘要或 artifact wrapper，输出同一 `evidence_ref` 的复账 verdict、missing/mismatch、operator next steps、rerun summary 和 phone-safe summary。
2. Robot diagnostics metadata-only summary：只消费 PC summary，不读取 raw artifact，不改变控制路径，不产生 ACK、cursor 或任务成功语义。
3. mobile/web 只读 panel：展示复账状态、八类材料对账、mismatch、缺失项、下一步和 safe copy；不改变 Start Delivery、Confirm Dropoff、Cancel gating。
4. Product closeout：等 Autonomy / Robot / Full-stack 返回后，更新本 sprint 后续文档、OKR 进度和 process log，保守记录 Objective 2 / Objective 3 的 software proof 进展。

## 5. 需要做什么

- Autonomy Algorithm Engineer：实现 PC-side `route_task_field_retest_result_reconciliation` gate 和 focused unit tests。
- Robot Platform Engineer：接入 Robot diagnostics metadata-only consumer，保持 fail-closed。
- User Touchpoint Full-Stack Engineer：在 `mobile/web` 增加只读“路线任务现场结果复账” panel、fixture/test 和产品文档同步。
- Product Manager / OKR Owner：收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. 优先级和验收口径

优先级：P0。原因是 Objective 5 外部证明当前受限，而 Objective 2 / Objective 3 的真实送达闭环缺口已经集中到同一 `evidence_ref` 的现场材料一致性复账。

验收口径：

- PC gate 能 fail closed 输出 `trashbot.route_task_field_retest_result_reconciliation.v1` 和 summary。
- Robot diagnostics 只能输出 metadata-only summary，缺失、schema 不匹配、`evidence_ref` mismatch、成功措辞、`delivery_success=true`、`primary_actions_enabled=true` 都必须 blocked。
- mobile/web panel 只读展示安全摘要和下一步，不暴露 raw artifact，不改动主操作授权。
- 全链路统一保留 `software_proof_docker_route_task_field_retest_result_reconciliation_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 验证只跑 tech-plan 中列出的围栏命令，不跑 broad regression。

## 7. 风险、阻塞和证据缺口

- Docker-only 主机无法产生真实 field pass、真实 Nav2/fixed-route、真实电梯、真实手机/browser、WAVE ROVER/UART/HIL 或 Objective 5 external proof。
- 如果输入只包含 placeholder summary，本轮只能输出 blocked / missing / mismatch，不能写成可控现场通过。
- 如果同一 `evidence_ref` 在 execution pack、handoff、result intake 和现场结果材料之间不一致，必须 fail closed。
- PR #5 硬件基线、2D LiDAR、ToF、vendor source 风险仍存在，但本轮不继续消费该 blocker；后续只有拿到真实 source/procurement/installation/wiring/calibration/HIL-entry 材料才重新推进。

## 8. 需要创建或更新的 sprint 文档

本轮启动阶段创建：

- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/pre_start.md`
- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/prd.md`
- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/tech-plan.md`

实现完成后必须继续创建或更新：

- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/tech-done.md`
- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/side2side_check.md`
- `sprints/2026.05.16_23-24_route-task-field-result-reconciliation/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
