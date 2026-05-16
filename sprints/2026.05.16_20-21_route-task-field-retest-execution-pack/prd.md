# Sprint 2026.05.16_20-21 Route Task Field Retest Execution Pack - PRD

sprint_type: epic

## 1. 产品问题

上一轮 `route_task_terminal_review_decision` 已经把 terminal completion rehearsal 的缺口转成 review decision、owner handoff、next required evidence 和 field retest request guidance。但它仍停在“复核决策”层：现场同学下一次真实复测时，还缺一个明确的 execution pack，告诉他们必须收集哪些材料、如何复跑、如何绑定同一 `evidence_ref`、如何回填给 Robot diagnostics 和 mobile/web。

当前用户价值缺口不是再做一个本地证明，而是把复核建议变成下一次真实 Nav2/fixed-route + task record + route completion signal 可执行的材料包。这个包必须足够具体，但仍必须保守：没有真实现场材料前，一律保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 用户价值和产品北极星

用户价值：

- 现场执行者知道下一次 field retest 要跑什么命令、收什么材料、谁负责回填。
- 手机端用户和支持人员能只读看到“下一次现场复测执行包”，理解当前仍未证明送达。
- 工程同学能用同一 `evidence_ref` 把 PC gate、Robot diagnostics 和 mobile/web 解释链路接起来，避免材料分散后无法复盘。

产品北极星：

把 `rober` 做成一台普通手机用户能理解、现场能复测、证据能复盘的低成本 ROS2 自主垃圾投递机器人。本轮推进 O2/O3 的现场复测准备度，但不把 software proof 写成真实 delivery success。

## 3. 已核实证据

- `OKR.md` 4.1 更新时间：2026-05-16 19:20 Asia/Shanghai。
- 最新 sprint：`2026.05.16_19-20_route-task-terminal-review-decision`。
- Objective 5 当前约 66%，数值最低；但 `OKR.md` 第 6 节要求真实外部材料才能继续推进 O5 completion。
- 本机只有 Docker，没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
- PR #4 要求 elevator-assisted delivery 成为主线必须能力，behavior / platform / full-stack 需覆盖电梯状态与 evidence chain。
- PR #5 review 暴露硬件基线与 source attribution 风险；最近两轮 `hardware-baseline-source-alignment` 与 `hardware-sensor-hil-entry-config-precheck` 已连续消费该 blocker。
- `AGENTS.md` 要求同一 blocker 最多消费 2 轮 sprint；第 3 轮起必须切换 Objective 或升级 CEO 决策。
- 上一轮 `route_task_terminal_review_decision` 已为下一次 field retest 形成 review decision、owner handoff、next required evidence 和 field retest request guidance。

## 4. OKR 映射

Objective 2：本轮服务“可送垃圾任务 + 电梯 assisted delivery 必达闭环”的现场复测执行包。它要求 task record、route completion signal、operator handoff、field retest checklist 和 boundary 绑定同一 `evidence_ref`，但仍不证明真实送达。

Objective 3：本轮服务“可验证导航与固定路线能力”。Execution pack 必须让真实 Nav2/fixed-route runtime log、fixed-route rerun command、route completion signal 和现场材料具备明确收集路径。

Objective 4：本轮给 mobile/web 增加只读解释面板，帮助普通用户和现场支持理解下一次复测需要什么；不改变控制按钮授权。

Objective 5：本轮不推进。Objective 5 仍最低，但外部材料 blocked；继续做本地 Docker metadata 不能增加 O5 completion。

Objective 1：本轮不继续消费 PR #5 硬件/source/config blocker，避免第三轮重复消费同一根因。

## 5. KR 拆解或更新

- KR-O2-field-retest-pack：形成 `trashbot.route_task_field_retest_execution_pack.v1` artifact 和 summary，包含 same `evidence_ref`、required field materials、rerun commands、operator handoff、field retest checklist 和 boundary。
- KR-O2-fail-closed：Robot diagnostics 缺失、unsupported、unsafe 或 evidence_ref mismatch 时必须 fail closed，不触发任何 collect/dropoff/cancel/ACK/cursor/Nav2/HIL/delivery success。
- KR-O3-rerun-materials：固定路线文档必须说明 first-run / rerun materials、route completion signal、task record 和 execution pack 的同一 evidence_ref 关系。
- KR-O4-phone-safe-panel：mobile/web 只读展示 execution pack，并保持 copy/export whitelist-only。
- KR-O5-stop-rule：closeout 必须明确本轮不是 Objective 5 external proof。

## 6. 本轮核心抓手

抓手名称：`route_task_field_retest_execution_pack`。

Artifact / summary 名称：

- `trashbot.route_task_field_retest_execution_pack.v1`
- `trashbot.route_task_field_retest_execution_pack_summary.v1`

Evidence boundary：

- `software_proof_docker_route_task_field_retest_execution_pack_gate`

必须固定状态：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 7. 范围

In scope：

- PC gate：消费上一轮 `route_task_terminal_review_decision` summary 或显式 JSON，输出 execution pack artifact / summary。
- Robot diagnostics：metadata-only 消费 execution pack summary，fail closed。
- Mobile web：只读 panel 和 whitelist-only copy/export。
- Docs：同步 PC tools、fixed route workflow、ROS contracts、mobile user flow 和 sprint closeout。

Out of scope：

- 不运行真实 Nav2/fixed-route。
- 不声明真实 field pass。
- 不声明 HIL、WAVE ROVER/UART、`T=1001` feedback 或真实传感器材料。
- 不声明真实手机/browser、production app 或 PWA prompt/user choice。
- 不声明 dropoff/cancel completion、delivery success 或 Objective 5 external proof。
- 不修改 Start / Confirm Dropoff / Cancel gating。

## 8. 优先级和验收口径

P0 acceptance：

- `route_task_field_retest_execution_pack` PC gate 生成 schema/version/status/evidence_ref/boundary/not_proven 字段。
- Required field materials 至少覆盖 real Nav2/fixed-route runtime log、route completion signal、task record、operator field note、mobile/diagnostics safe summary；如含电梯场景，还必须覆盖 door state、target floor confirmation 和 human assistance note。
- Rerun commands 必须可由现场同学复跑，并保持同一 `evidence_ref`。
- Robot diagnostics 和 mobile/web 只读消费，不改变 primary actions。
- 所有输出必须包含 `software_proof_docker_route_task_field_retest_execution_pack_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

P1 acceptance：

- Documentation 同步到 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。
- Tests / checks 采用围栏验证，不做无关大回归。
- Product closeout 更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，并说明 O5 blocked 与 PR #5 blocker 不再第三轮消费。

## 9. 对应责任 Engineer

- Task A Autonomy：Autonomy Algorithm Engineer。
- Task B Robot：Robot Platform Engineer。
- Task C Full-stack：User Touchpoint Full-Stack Engineer。
- Task D Product：Product Manager / OKR Owner。

## 10. 风险、阻塞和证据链

风险：

- 如果 execution pack 文案写成“ready/pass/success”而没有保留 not_proven，会污染 OKR 和手机端解释。
- 如果 Robot diagnostics 或 mobile/web 对缺失 summary 宽松通过，会误开 primary action。
- 如果 evidence_ref 没有贯穿 PC gate、Robot diagnostics 和 mobile/web，下一次真实现场材料仍无法复盘。

阻塞：

- Objective 5 需要真实外部材料；当前 Docker-only 环境无法推进。
- Objective 1 / PR #5 硬件/source/config blocker 已连续消费两轮；本轮不应继续消费。

需要补齐的真实证据链：

- 真实 Nav2/fixed-route runtime log。
- 真实 route completion signal。
- 真实 task record。
- 真实电梯门状态、楼层确认、人工协助记录。
- 真实 dropoff/cancel completion 或 delivery result。
- 真实 WAVE ROVER/UART/HIL。
- 真实手机/browser 和 Objective 5 external proof。
