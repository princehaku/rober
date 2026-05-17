# Sprint 2026.05.17_14-15 Route Task Result Acceptance Packet - Pre Start

sprint_type: epic

## 1. 启动背景

本轮按 `OKR.md` 4.1 和第 6 节重新排序。当前数值最低仍是 Objective 5（约 68%），但继续推进 Objective 5 completion 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 或真实手机/browser 证据。本机只有 Docker，没有这些真实外部材料，因此本轮不继续堆 O5 local metadata。

最新 sprint `sprints/2026.05.17_13-14_route-task-handoff-result-reconciliation-bridge/final.md` 已完成 `route_task_field_retest_review_result_handoff -> result_intake -> result_reconciliation` safe lineage bridge。Objective 2 / Objective 3 已推进到约 94%，但仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、真实 route completion signal、真实 task record、真实 dropoff/cancel completion、真实 cancel completion 和 delivery result。

近期 PR / review 证据：

- PR #4 把 elevator-assisted delivery 设为必达主线能力，要求 route/elevator evidence chain 可追溯、可复账、可交接。
- PR #5 Codex review 指出硬件默认集与 2D LiDAR / ToF mandatory baseline 矛盾、OKR lowest-objective narrative drift、sensor assumptions 缺 vendor citation；但本机没有真实硬件，真实 SKU/source/receipt/install/wiring/calibration/HIL-entry 不能在本轮完成。
- CEO 已明确约束：“本机没有真实硬件，只有docker”“重新在功能往前走”“别测试代码一堆，测试只围栏”。

## 2. 用户价值和产品北极星

产品北极星仍是普通手机用户能把垃圾交给小车，并在跨楼层或固定路线场景中获得可解释、可恢复、可复盘的送达体验。本轮用户价值不是证明现场已经通过，而是把上一轮 result reconciliation 结果整理成现场/支持/手机都能理解的 acceptance packet：谁负责补材料、缺哪八类 result materials、如何重跑、什么算 pass/fail、为什么当前仍是 `not_proven`。

## 3. OKR 映射

- Objective 2：把电梯 assisted delivery 必达链路的结果复账转成验收包，明确门状态、目标楼层确认、人工协助、dropoff/cancel completion 和 delivery result 的现场材料缺口。
- Objective 3：把 fixed-route / Nav2 result reconciliation 转成可执行验收包，明确 runtime log、route completion signal、task record 和同一 `evidence_ref` 的复账要求。
- Objective 5：本轮不推进。数值最低但缺真实外部证据，继续本地 metadata 会重复消费 blocker。
- Objective 1 / Objective 4：只读消费边界相关，不新增真实硬件 proof 或真实手机/browser proof。

## 4. 本轮核心抓手

新增 `route_task_field_retest_result_acceptance_packet`：消费最新 `route_task_field_retest_result_reconciliation` artifact / summary，把 safe lineage、八类 required result materials、缺口、owner handoff、rerun commands、pass/fail criteria 和 support/mobile safe copy 汇总成一个 acceptance packet。

该 packet 必须保持 Docker-only `software_proof`：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- 不声明真实 route/elevator field pass
- 不声明 HIL、真实手机/browser、Objective 5 external proof 或 delivery success

## 5. 需要做什么

1. Autonomy Algorithm Engineer：实现 PC evidence gate，定义 packet artifact / summary，消费 result reconciliation 输出并生成 acceptance packet。
2. Robot Platform Engineer：让 Robot diagnostics 只读消费 packet summary，fail closed，不改变任务状态机或控制能力。
3. User Touchpoint Full-Stack Engineer：让 mobile/web 只读展示 packet，copy/export 白名单字段，不改变 Start / Confirm Dropoff / Cancel gating。
4. Product Manager / OKR Owner：工程完成后收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和进度日志，保持证据边界不漂移。

## 6. 优先级和验收口径

P0：packet 必须能从 result reconciliation artifact / summary 生成，并显式列出八类 required result materials：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance operator note、dropoff/cancel completion、delivery result。

P0：packet 必须包含 owner handoff、rerun commands、pass/fail criteria、safe lineage 和 safe copy；如果输入缺失、schema 不支持、evidence_ref 不一致、出现 success/control claim 或 unsafe raw material，则 fail closed。

P1：Robot diagnostics 和 mobile/web 只能只读展示 packet summary，不读取 raw artifact，不暴露 raw paths、checksums、ROS topics、`/cmd_vel`、serial/UART、WAVE ROVER 参数、credentials 或 Objective 5 materials。

P1：围栏验证只使用 focused unittest、`py_compile`、`node --check`、`rg` 和 scoped `git diff --check`，不新增大测试、不跑真实硬件/云/手机 proof。

## 7. 风险、阻塞和证据链缺口

- O5 blocker：没有真实 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或真实手机/browser 证据，本轮不得推进 O5 completion。
- PR #5 blocker：没有真实 2D LiDAR / ToF SKU/source/receipt/install/wiring/calibration/HIL-entry，本轮不得把硬件 blocker 包成又一轮 metadata completion。
- O2/O3 剩余缺口：真实 route/elevator field pass、Nav2/fixed-route runtime、真实 route completion signal、真实 task record、真实 dropoff/cancel completion、delivery result 和同一 `evidence_ref` 上车复账仍未完成。
- 本轮 acceptance packet 只把当前缺口变得可执行，不把缺口本身标记为已完成。

## 8. 需要创建或更新的 sprint 文档

本轮先创建：

- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/pre_start.md`
- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/prd.md`
- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-plan.md`

工程执行后必须继续更新：

- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/tech-done.md`
- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/side2side_check.md`
- `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/final.md`
