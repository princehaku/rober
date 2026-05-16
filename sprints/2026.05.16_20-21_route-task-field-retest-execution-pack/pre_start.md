# Sprint 2026.05.16_20-21 Route Task Field Retest Execution Pack - Pre Start

sprint_type: epic

## 1. 启动背景

本轮是下一轮 Epic sprint 入口，目标抓手命名为 `route_task_field_retest_execution_pack`。它承接上一轮 `2026.05.16_19-20_route-task-terminal-review-decision` 的 review decision、owner handoff、next required evidence 和 field retest request guidance，把这些复核结论转成下一次真实 Nav2/fixed-route + task record + route completion signal 同一 `evidence_ref` 材料可打包、可复跑、可回填的执行包。

当前 `OKR.md` 4.1 更新时间为 2026-05-16 19:20 Asia/Shanghai，最新 sprint 为 `2026.05.16_19-20_route-task-terminal-review-decision`。Objective 5 当前约 66%，仍是数值最低 Objective；但 `OKR.md` 第 6 节明确，只有真实外部材料才能继续推进 O5 completion，包括公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等。本机只有 Docker，因此本轮不能继续叠加本地 O5 metadata depth。

PR #4 在 2026-05-14 把 elevator-assisted delivery 写成主线必须能力，要求 behavior / platform / full-stack ownership 覆盖电梯状态与 evidence chain。PR #5 在 2026-05-14 的 Codex review 给出三条具体意见：P1 默认硬件集合与 mandatory sensor baseline 不一致；P2 OKR 最低 objective 叙述与表格不一致；P2 新 mandatory sensor assumptions 缺 `docs/vendor/` 来源。最近两轮 `2026.05.16_17-18_hardware-baseline-source-alignment` 与 `2026.05.16_18-19_hardware-sensor-hil-entry-config-precheck` 已连续消费 PR #5 硬件/source/config blocker；根据 `AGENTS.md` 同一 blocker 最多消费 2 轮 sprint 的红线，本轮不能启动第三个硬件 blocker wrapper，必须切换 Objective 或升级 CEO 决策。

本轮选择切换到下一个可行动低完成度 Objective 2 / Objective 3，继续推进真实现场复测材料准备，而不是重复硬件 blocker 或 O5 外部材料 blocker。

## 2. 用户价值和产品北极星

用户价值：现场同学和普通手机用户需要知道下一次真实 field retest 具体要带哪些材料、跑哪些命令、如何保证同一 `evidence_ref`、谁负责回填，以及为什么当前仍是 `not_proven`。这比继续展示一个 review decision 更进一步：它把复核建议转成可执行的现场复测包。

产品北极星：`rober` 要成为普通手机用户能使用、现场可复盘、证据链可信的低成本 ROS2 自主垃圾投递机器人。本轮不证明真实送达，而是让下一次真实 Nav2/fixed-route + task record + route completion signal 的现场材料具备统一入口、统一 evidence boundary 和 fail-closed 回填路径。

## 3. OKR 映射

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。推进 route/task field retest 的执行包，服务未来同一 `evidence_ref` 下 task record、route completion signal、dropoff/cancel completion 或 delivery result 的现场复账。
- Objective 3：可验证导航与固定路线。推进真实 Nav2/fixed-route runtime log、route completion signal、fixed-route rerun command 和材料打包路径。
- Objective 4：手机用户体验与低成本量产边界。只读展示 execution pack，让手机端能解释下一次现场复测需要什么，但不改变 Start / Confirm Dropoff / Cancel gating。
- Objective 5：保持 blocked，不上调。本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
- Objective 1：不作为本轮主线。最近两轮已消费 PR #5 硬件/source/config blocker，本轮不继续第三轮硬件 blocker wrapper。

## 4. KR 拆解或更新

- O2 KR5 / KR6 / KR7：下一次 field retest 必须要求同一 `evidence_ref` 的 task record、route completion signal、operator handoff、field retest checklist 和 boundary；仍不得写成真实送达或电梯通过。
- O3 KR2 / KR3 / KR4：PC gate 输出 rerun commands、required field materials 和 fixed-route / Nav2 材料清单，支持后续真实 route evidence 回填。
- O4 KR1 / KR5 / KR6 / KR7：mobile/web 新增只读 field retest execution pack panel，copy/export whitelist-only，所有 primary actions 保持 fail-closed。
- O5 KR1-KR6：仅记录 blocked external proof，不消费本轮 scope。

## 5. 本轮核心抓手

核心抓手是 `route_task_field_retest_execution_pack`。

统一证据边界必须固定为：

- `software_proof_docker_route_task_field_retest_execution_pack_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

所有工程输出必须保持 software proof only，不得宣称真实 field pass、HIL、真实手机/browser、真实 Nav2/fixed-route 成功、真实 dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 6. 需要做什么

- Task A Autonomy：新增 PC gate，把上一轮 `route_task_terminal_review_decision` summary 或显式 JSON 转成 `trashbot.route_task_field_retest_execution_pack.v1` / summary。
- Task B Robot：metadata-only 消费 execution pack summary，缺失、unsupported、unsafe、evidence_ref mismatch fail closed。
- Task C Full-stack：新增 mobile/web 只读 field retest execution pack panel，copy/export whitelist-only，Start / Confirm Dropoff / Cancel gating 不变。
- Task D Product：完成 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` closeout。

## 7. 优先级和验收口径

P0：

- PC gate 能消费上一轮 review decision 或显式 JSON，并输出 execution pack artifact / summary。
- Summary 必须含同一 `evidence_ref`、required field materials、rerun commands、operator handoff、field retest checklist 和 boundary。
- Robot diagnostics 与 mobile/web 均只读消费，不触发 collect、dropoff、cancel、ACK、cursor、Nav2、HIL 或 delivery success。
- 所有路径遇到缺失、unsupported、unsafe 或 evidence_ref mismatch 均 fail closed。

P1：

- 更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。
- Closeout 必须说明 Objective 5 stop rule、PR #5 blocker 两轮消费、PR #4 主线能力要求，以及本轮转向 O2/O3 的理由。

验收通过只代表 `software_proof_docker_route_task_field_retest_execution_pack_gate`，不能作为真实现场通过或 OKR 外部证据。

## 8. 对应责任 Engineer

- Task A：Autonomy Algorithm Engineer。
- Task B：Robot Platform Engineer。
- Task C：User Touchpoint Full-Stack Engineer。
- Task D：Product Manager / OKR Owner。

## 9. 风险、阻塞和需要补齐的证据链

阻塞：

- Objective 5 继续推进需要真实外部材料，本机 Docker 无法补齐。
- PR #5 硬件/source/config blocker 已连续两轮消费，本轮不得继续做第三个 wrapper。

剩余证据链：

- 真实 Nav2/fixed-route runtime log。
- 真实 route completion signal。
- 真实 task record。
- 同一 `evidence_ref` 的现场材料回填。
- 真实门状态、真实楼层确认、真实人工协助记录。
- 真实 dropoff/cancel completion 或 delivery result。
- 真实 WAVE ROVER/UART/HIL、真实手机/browser 和 Objective 5 external proof。

## 10. 需要创建或更新的 sprint 文档

本轮启动阶段创建：

- `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/pre_start.md`
- `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/prd.md`
- `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/tech-plan.md`

后续实现与收口必须继续更新：

- `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/tech-done.md`
- `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/side2side_check.md`
- `sprints/2026.05.16_20-21_route-task-field-retest-execution-pack/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
