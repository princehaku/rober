# Sprint 2026.05.17_15-16 Route Task Result Acceptance Backfill - Pre Start

sprint_type: epic

## 1. 启动背景

本轮按 `OKR.md` 4.1 和第 6 节重新排序。当前数值最低仍是 Objective 5（约 68%），但第 6 节明确写明：没有真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 或真实手机/browser 证据时，不应继续推进本地 O5 wrapper 或 metadata depth。本机没有真实硬件，只有 Docker，因此本轮不推进 Objective 5 completion。

最新 sprint `sprints/2026.05.17_14-15_route-task-result-acceptance-packet/final.md` 已完成 `route_task_field_retest_result_acceptance_packet`。该 packet 把上一轮 result reconciliation 的 safe lineage、八类 required result materials、owner handoff、rerun commands 和 pass/fail criteria 转成 PC / Robot / mobile 三侧只读验收包；Objective 2 / Objective 3 已到约 95%。下一步不是再做一个验收包，而是让现场同学能把真实材料按同一 `evidence_ref` 回填进 Docker/local software-proof gate，并让 Robot diagnostics 与 mobile/web 只读看到回填状态。

近期 PR / review 证据：

- PR #4：elevator-assisted delivery 已成为必须能力，且没有 review comments；这要求 route/elevator evidence chain 继续围绕真实门状态、目标楼层确认、人工协助、dropoff/cancel completion 和 delivery result 做同一 `evidence_ref` 回填。
- PR #5 Codex review：`docs/product/production_hardware_boundary.md` 曾存在默认硬件集合与 `monocular + 2D LiDAR + ToF` mandatory baseline 的矛盾；OKR 最低目标叙述曾漂移；mandatory sensor assumptions 缺 `docs/vendor/` citation。近期硬件/source blocker 已多轮消费，本机无真实硬件，本轮不再包装同一 blocker。
- `OKR.md` 第 6 节：当前最高可行动作之一是 Objective 2 / Objective 3 的受控现场材料回填，包括真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record / completion signal、dropoff/cancel completion 或 delivery result。

## 2. 用户价值和产品北极星

产品北极星仍是普通手机用户把垃圾交给小车后，小车能可验证地完成固定路线 / 电梯 assisted delivery，并且失败时用户和支持同学知道缺什么证据、谁负责、怎么回填、下一步能否继续。

本轮用户价值是把上一轮 acceptance packet 从“可验收清单”推进到“可回填入口”：现场材料暂时还不在本机，但 PC gate 应能接收 acceptance packet summary 和 `--material-dir` 中八类材料，生成 safe backfill artifact / summary。Robot diagnostics 和 mobile/web 只能只读消费该 summary，帮助支持同学判断材料是否齐全、是否同一 `evidence_ref`、是否仍为 `not_proven`。

## 3. OKR 映射

- Objective 2：推进可送垃圾任务 + 电梯 assisted delivery 的现场结果回填链路，重点覆盖 door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result。
- Objective 3：推进可验证导航与固定路线的回填链路，重点覆盖 Nav2/fixed-route runtime log、route completion signal、task record 和同一 `evidence_ref` 复账。
- Objective 5：当前约 68%，数值最低但不推进；没有真实 external proof，不能把本轮 Docker/local backfill gate 写成 O5 production proof。
- Objective 1 / Objective 4：只保留风险边界；本轮不证明真实 WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF、真实手机/browser 或 production app。

## 4. 本轮核心抓手

新增 `route_task_field_retest_result_acceptance_backfill`。它消费上一轮 acceptance packet summary，再读取 `--material-dir` 下八类现场材料，输出 safe backfill artifact / summary：

- Nav2/fixed-route runtime log
- route completion signal
- task record
- door state
- target floor confirmation
- human assistance note
- dropoff/cancel completion
- delivery result

证据边界固定为 `software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate`，且必须保留：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- 不声明真实 route/elevator field pass
- 不声明真实 Nav2/fixed-route、HIL、真实手机/browser、Objective 5 external proof 或 delivery success

## 5. 需要做什么

1. Autonomy Algorithm Engineer：新增 PC backfill gate，接收 acceptance packet summary 与 `--material-dir` 八类材料，生成 safe artifact / summary，并 fail closed。
2. Robot Platform Engineer：让 Robot diagnostics 只读消费 backfill summary，暴露缺口、同一 `evidence_ref` 状态、owner handoff 和 rerun summary，不改变任务控制能力。
3. User Touchpoint Full-Stack Engineer：让 mobile/web 只读展示 backfill summary，copy/export 仅白名单字段，Start / Confirm Dropoff / Cancel gating 不变。
4. Product Manager / OKR Owner：工程完成后收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和进度日志；本 planning worker 只创建规划三件套，不修改 `OKR.md` 或产品代码。

## 6. 优先级和验收口径

P0：PC gate 必须能从 acceptance packet summary + `--material-dir` 生成 backfill artifact / summary，并显式检查八类材料是否存在、是否同一 `evidence_ref`、是否含 unsafe success/control claim。

P0：backfill 输出必须包含 source packet summary、material completeness、evidence_ref alignment、missing/rejected material categories、owner handoff、rerun commands、safe copy 和 pass/fail decision inputs；但 verdict 仍是 `not_proven`，不是现场通过。

P0：Robot diagnostics 和 mobile/web 只能只读消费 summary，不读取 raw artifact，不暴露 raw paths、checksums、ROS topics、`/cmd_vel`、serial/UART、WAVE ROVER 参数、credentials 或 Objective 5 materials。

P1：围栏验证只使用 focused unittest、`py_compile`、`node --check`、`rg` 和 scoped `git diff --check`，不新增大测试，不跑真实硬件/云/手机 proof。

## 7. 风险、阻塞和证据链缺口

- O5 blocker：仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 证据；本轮不得推进 Objective 5。
- PR #5 blocker：仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry；近期硬件/source blocker 已多轮消费，本轮不再堆硬件 metadata。
- O2/O3 剩余缺口：本机没有真实现场材料；backfill gate 只能证明 Docker/local 回填入口和只读消费链路，不证明真实 route/elevator field pass。
- 产品风险：backfill 这个词容易被误读为“现场材料已补齐”。所有 schema、文案和 closeout 必须把 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 写入可见字段。

## 8. 需要创建或更新的 sprint 文档

本 planning worker 只创建：

- `sprints/2026.05.17_15-16_route-task-result-acceptance-backfill/pre_start.md`
- `sprints/2026.05.17_15-16_route-task-result-acceptance-backfill/prd.md`
- `sprints/2026.05.17_15-16_route-task-result-acceptance-backfill/tech-plan.md`

工程执行后必须继续更新：

- `sprints/2026.05.17_15-16_route-task-result-acceptance-backfill/tech-done.md`
- `sprints/2026.05.17_15-16_route-task-result-acceptance-backfill/side2side_check.md`
- `sprints/2026.05.17_15-16_route-task-result-acceptance-backfill/final.md`
