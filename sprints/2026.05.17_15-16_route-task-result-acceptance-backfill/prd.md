# Sprint 2026.05.17_15-16 Route Task Result Acceptance Backfill - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

北极星：普通手机用户把垃圾交给小车后，系统能在固定路线 / 电梯 assisted delivery 场景中可验证地送达；当还没有真实现场证明时，现场同学、支持同学和用户触点必须清楚知道材料是否齐全、是否同一 `evidence_ref`、下一步谁补、是否仍禁止主操作。

上一轮 `route_task_field_retest_result_acceptance_packet` 已经把 result reconciliation 转成验收包，但它仍是“准备现场验收”的 packet。本轮新增 `route_task_field_retest_result_acceptance_backfill`，把 acceptance packet summary 和 `--material-dir` 下八类现场材料接起来，形成可回填、可复核、可只读展示的 safe artifact / summary。

## 2. OKR 映射

- Objective 2：服务“可送垃圾任务 + 电梯 assisted delivery 必达闭环”。本轮聚焦 door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result 的回填入口。
- Objective 3：服务“可验证导航与固定路线”。本轮聚焦 Nav2/fixed-route runtime log、route completion signal、task record 和同一 `evidence_ref` 的回填复账。
- Objective 5：不推进。当前约 68%，但缺真实 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或真实手机/browser 证据，本轮不能写成 production proof。
- PR #4：elevator-assisted delivery 是必达能力，本轮按它要求继续补 route/elevator evidence chain。
- PR #5：硬件/source blocker 仍是独立风险；本轮只引用其证据缺口，不继续包装为 hardware completion。

## 3. KR 拆解或更新

本 planning worker 不修改 `OKR.md`。工程完成后，Product closeout 可按以下 KR 口径判断是否保守更新：

- O2 KR5 / KR6 / KR7：task record、门状态、楼层确认、人工协助、dropoff/cancel completion 和 delivery result 具备同一 `evidence_ref` 的 backfill 检查入口，并能输出缺口与 owner handoff。
- O3 KR2 / KR3 / KR4：Nav2/fixed-route runtime log、route completion signal、task record 可进入 backfill gate，被 PC / Robot / mobile 三侧以 summary 形式只读追踪。
- O4 KR4 / KR5：mobile/web 和 diagnostics 能展示 phone-safe backfill 状态，但不改变普通用户主操作授权。
- O5 不更新：没有真实 external proof。

## 4. 本轮核心抓手

把上一轮 acceptance packet 从“验收清单”推进为“回填入口”：

- 输入 A：`trashbot.route_task_field_retest_result_acceptance_packet_summary.v1` 或兼容 acceptance packet summary。
- 输入 B：`--material-dir`，包含八类现场材料。
- 输出 artifact schema：`trashbot.route_task_field_retest_result_acceptance_backfill.v1`。
- 输出 summary schema：`trashbot.route_task_field_retest_result_acceptance_backfill_summary.v1`。
- 证据边界：`software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate`。
- 必须固定：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

八类材料：

1. Nav2/fixed-route runtime log
2. route completion signal
3. task record
4. door state
5. target floor confirmation
6. human assistance note
7. dropoff/cancel completion
8. delivery result

## 5. 需要做什么

Task A / Autonomy：新增 PC backfill gate。它接收 acceptance packet summary 与 `--material-dir`，输出 safe artifact / summary；缺 material、schema 不支持、`evidence_ref` 不一致、success/control claim、unsafe copy 必须 fail closed。

Task B / Robot：diagnostics 只读消费 backfill summary，并把材料完整性、同一 `evidence_ref` 状态、缺口、owner handoff、rerun commands 和 safe copy 暴露为 Robot-safe metadata。

Task C / Full-stack：mobile/web 新增只读 “路线任务结果回填” panel，展示 backfill summary，不改变 Start Delivery、Confirm Dropoff、Cancel gating。

Task D / Product：工程完成后更新 sprint closeout、OKR 进度和进度日志；只在三侧围栏验证通过后保守更新 Objective 2 / Objective 3，不更新 Objective 5。

## 6. 优先级和验收口径

P0 验收：

- backfill gate 能从 valid acceptance packet summary + material directory 生成 summary。
- 八类材料全部显式检查；缺失、占位、unsupported schema、`evidence_ref` mismatch、unsafe copy、success/control claim 必须 fail closed。
- artifact / summary 含 material completeness、alignment status、missing/rejected material categories、owner handoff、rerun commands、safe copy、pass/fail decision inputs。
- 所有输出和消费者都保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

P1 验收：

- Robot diagnostics 支持 file/env/top-level/nested summary 只读消费。
- mobile/web 只展示白名单字段，copy/export 只包含 safe copy / safe metadata。
- 文档同步更新由后续实现 worker 负责：`docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 和 sprint closeout 文档。
- 验证只跑围栏命令，不新增真实硬件/云/手机 proof，不新增大测试。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：Task A，主责 PC backfill gate、focused unittest、导航/路线文档。
- Robot Platform Engineer：Task B，主责 diagnostics contract、Robot tests、接口文档。
- User Touchpoint Full-Stack Engineer：Task C，主责 mobile/web 只读 panel、fixture/test、产品触点文档。
- Product Manager / OKR Owner：Task D，主责 closeout、OKR 边界和证据口径。

## 8. 风险、阻塞和需要补齐的证据链

- 本轮 backfill gate 是 Docker/local software proof only。即使八类 sample material 在本地通过，也不证明真实现场通过、真实电梯运行、真实 Nav2/fixed-route、HIL、真实手机/browser 或 delivery success。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或真实手机/browser 证据。
- PR #5 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry；本轮不得继续消费同一硬件 blocker。
- 后续真实现场执行仍需人工提供同一 `evidence_ref` 的材料，而不是由本机 Docker gate 生成真实材料。

## 9. 需要创建或更新的 sprint 文档

本轮已创建规划三件套：`pre_start.md`、`prd.md`、`tech-plan.md`。工程执行完成后必须补齐 `tech-done.md`、`side2side_check.md`、`final.md`，并由 Product closeout 判断是否更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
