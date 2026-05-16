# Sprint 2026.05.16_20-21 Route Task Field Retest Execution Pack - Final

sprint_type: epic

## 1. 收口结论

本轮 `route_task_field_retest_execution_pack` 已完成 Task A / B / C / D closeout。三条 worker 输出已把上一轮 `route_task_terminal_review_decision` 转成下一次真实现场复测可用的 execution pack、Robot diagnostics metadata-only summary 和 mobile/web 只读 panel。

本轮只代表 `software_proof_docker_route_task_field_retest_execution_pack_gate`。统一状态保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 用户价值和产品北极星

用户价值：现场同学现在有明确的复测执行包，知道要收集真实 Nav2/fixed-route runtime log、route completion signal、task record、operator handoff、field retest checklist，以及电梯场景的 door state、target floor confirmation、human assistance note。普通手机用户和现场支持也能在 mobile/web 只读面板里看到下一步需要补什么，而不会误以为已经完成真实送达。

产品北极星：本轮继续服务“普通手机用户能理解、现场可复测、证据可复盘”的低成本 ROS2 自主垃圾投递机器人；它推进 O2/O3/O4 的现场复测准备度，不把 local Docker proof 写成真实 field pass。

## 3. OKR 更新

- Objective 1：保持约 75%。本轮未产生真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或真实传感器材料。
- Objective 2：约 80% -> 约 81%。Execution pack 将任务复测材料、同一 `evidence_ref`、operator handoff 和 checklist 变成可执行链路，支持下一次真实 field retest。
- Objective 3：约 80% -> 约 81%。Nav2/fixed-route runtime log、route completion signal、task record 和 rerun commands 现在被纳入同一 execution pack。
- Objective 4：约 89% -> 约 90%。Mobile/web 新增只读“现场复测执行包”解释面板，copy/export whitelist-only，Start / Confirm Dropoff / Cancel gating 未改变。
- Objective 5：保持约 66%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料。

## 4. Blocker 回顾

Objective 5 仍是数值最低 Objective，但当前主机只有 Docker，缺公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration 等真实外部材料。继续堆本地 O5 metadata depth 不能提高 Objective 5 completion，因此本轮不消费 O5。

PR #5 硬件/source/config blocker 已在 `2026.05.16_17-18_hardware-baseline-source-alignment` 与 `2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck` 连续两轮消费。本轮遵守 `AGENTS.md` 同一 blocker 最多消费 2 轮红线，切换到 Objective 2 / Objective 3 的 route-task field retest execution pack。

PR #4 将 elevator-assisted delivery 写成主线必须能力。本轮把电梯 door state、target floor confirmation、human assistance note 作为 execution pack 必需材料，但没有宣称真实电梯闭环。

## 5. 实际改动文件

Product closeout 修改：

- `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/tech-done.md`
- `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/side2side_check.md`
- `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Engineer worker 改动见 `tech-done.md`。

## 6. 验证结果

Task A Autonomy：py_compile passed；unittest `Ran 10 tests in 0.022s OK`；CLI `--help` passed；required `rg` passed；scoped `git diff --check` passed。

Task B Robot：py_compile passed；diagnostics unittest `Ran 112 tests in 0.125s OK`；required `rg` passed；scoped `git diff --check` passed。第一轮 unittest 发现 summary wrapper 没读自身 `safe_evidence_ref`，已修复并复验。

Task C Full-stack：mobile unittest `Ran 14 tests in 0.028s OK`；`node --check mobile/web/app.js` passed；required `rg` passed；scoped `git diff --check` passed。

Task D Product closeout 验收：

```text
rg -n "route_task_field_retest_execution_pack|software_proof_docker_route_task_field_retest_execution_pack_gate|Objective 5|Objective 2|Objective 3|PR #5|PR #4|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_20-21_route-task-field-retest-execution-pack
passed

Key hits:
OKR.md:161 Objective 2 约 81%，software_proof_docker_route_task_field_retest_execution_pack_gate，not_proven，delivery_success=false，primary_actions_enabled=false
OKR.md:162 Objective 3 约 81%，route_task_field_retest_execution_pack
OKR.md:163 Objective 4 约 90%，现场复测执行包只读 panel
OKR.md:164 Objective 5 约 66%，Docker-only，not real Objective 5 external proof
docs/process/okr_progress_log.md:15-21 Task A/B/C/D evidence and PR #5 blocker redirection recorded
sprints/.../tech-done.md:119 PR #5 blocker 两轮消费，本轮切换 Objective
sprints/.../tech-done.md:121 PR #4 elevator-assisted delivery 主线材料要求 recorded

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/tech-done.md sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/side2side_check.md sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/final.md
passed
```

## 7. 剩余风险

仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、真实楼层确认、人工协助记录、dropoff/cancel completion、delivery result、WAVE ROVER/UART/HIL、真实手机/browser、Objective 5 external proof。

本轮没有证明真实 field pass、真实 route/elevator execution、真实投放、真实取消完成、delivery success、真实云/4G/OSS/CDN/DB/queue 或生产 worker/migration。
