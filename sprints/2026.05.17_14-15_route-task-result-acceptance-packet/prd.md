# Sprint 2026.05.17_14-15 Route Task Result Acceptance Packet - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

北极星：普通手机用户交给小车的垃圾能被可验证地送到垃圾站；如果还不能真实送达，用户、现场同学和支持同学必须清楚知道还缺什么证据、谁负责、怎么重跑、什么条件下才能进入下一步。

上一轮 `route_task_field_retest_result_reconciliation` 已经把 review-result handoff、result-intake 和 result-reconciliation 之间的 safe lineage 接起来。但 reconciliation summary 仍偏工程复账，不足以直接交给现场或支持做验收执行。本轮要新增 `route_task_field_retest_result_acceptance_packet`，把复账结果翻译为 acceptance packet。

## 2. OKR 映射

- Objective 2：服务“可送垃圾任务 + 电梯 assisted delivery 必达闭环”。packet 聚焦真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 和 delivery result 的验收缺口。
- Objective 3：服务“可验证导航与固定路线”。packet 聚焦 Nav2/fixed-route runtime log、route completion signal、task record 和同一 `evidence_ref` 的现场复账缺口。
- Objective 5：不推进。`OKR.md` 第 6 节已经明确没有真实 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或真实手机/browser 证据时，不继续堆本地 O5 metadata。
- PR #4：作为 route/elevator evidence chain 的主线依据。
- PR #5：作为硬件边界风险来源；本轮只引用其缺口，不尝试完成真实硬件材料。

## 3. KR 拆解或更新

本轮不直接修改 `OKR.md`，但工程完成后的 closeout 应按以下 KR 口径判断是否小幅推进：

- O2 KR5 / KR6 / KR7：任务记录、失败原因、电梯 assisted delivery 证据链和人工接管材料被 packet 明确列出、分配 owner、给出 rerun/pass/fail 口径。
- O3 KR2 / KR3 / KR4：fixed-route / Nav2 结果材料能通过 packet 从 result reconciliation 继续追踪，支持下一次现场复测按同一 `evidence_ref` 回填。
- O4 KR4 / KR5：手机/支持侧只读展示 packet，普通用户或支持同学不需要读 raw artifact、ROS2、串口或本地路径即可知道还缺什么。
- O5 不更新：没有真实 external proof。

## 4. 本轮核心抓手

把 `route_task_field_retest_result_reconciliation` 的工程复账转成 `route_task_field_retest_result_acceptance_packet`：

- 输入：latest result reconciliation artifact / summary。
- 输出：artifact schema `trashbot.route_task_field_retest_result_acceptance_packet.v1` 和 summary schema `trashbot.route_task_field_retest_result_acceptance_packet_summary.v1`。
- 证据边界：`software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`。
- 必须保留：safe lineage、八类 required result materials、missing items、mismatch reasons、owner handoff、rerun commands、pass/fail criteria、safe copy、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 需要做什么

Task A / Autonomy：新增 PC evidence gate，消费 reconciliation 输出并生成 acceptance packet。packet 要能 fail closed，不能读取 raw upstream handoff artifact。

Task B / Robot：diagnostics 只读消费 packet summary，并把状态、缺口、owner handoff、rerun commands、pass/fail criteria 暴露为 phone-safe metadata。

Task C / Full-stack：mobile/web 新增只读 acceptance packet panel，展示 safe packet，不改变 Start Delivery、Confirm Dropoff、Cancel gating。

Task D / Product：工程完成后更新 sprint closeout、OKR 进度和进度日志；如果只是 Docker/local software proof，只允许保守更新 O2/O3，不更新 O5。

## 6. 优先级和验收口径

P0 验收：

- packet 能从有效 result reconciliation 生成。
- packet 显式列出八类 required result materials。
- packet 有 owner handoff、rerun commands、pass/fail criteria。
- packet 和所有消费者保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- unsupported schema、缺 source、缺 evidence_ref、unsafe copy、success/control claim 必须 fail closed。

P1 验收：

- Robot diagnostics 支持 file/env/top-level/nested summary 只读消费。
- mobile/web 只展示白名单字段，copy/export 只包含 safe copy / safe metadata。
- 文档同步更新 `docs/navigation/fixed_route_workflow.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md` 和 sprint closeout 文档。
- 验证只跑围栏命令，不新增真实硬件/云/手机 proof，不新增大测试。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：Task A，主责 PC gate 和导航/路线文档。
- Robot Platform Engineer：Task B，主责 diagnostics contract 和 Robot 接口文档。
- User Touchpoint Full-Stack Engineer：Task C，主责 mobile/web 只读 panel 和产品触点文档。
- Product Manager / OKR Owner：Task D，主责 closeout、OKR 边界和证据口径。

## 8. 风险、阻塞和需要补齐的证据链

- 真实现场缺口仍在：route/elevator field pass、Nav2/fixed-route runtime、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result 都还没有真实材料。
- acceptance packet 可能让支持侧误以为“验收通过”；因此文案和 schema 必须使用 `not_proven`，并明确 pass/fail criteria 是下一次现场复测的判断口径，不是本轮结果。
- O5 和 PR #5 不可本地补齐：缺真实外部云材料和真实 2D LiDAR / ToF 采购/安装/HIL-entry 材料。

## 9. 需要创建或更新的 sprint 文档

本轮已创建规划三件套：`pre_start.md`、`prd.md`、`tech-plan.md`。工程执行完成后必须补齐 `tech-done.md`、`side2side_check.md`、`final.md`，并由 Product closeout 判断是否更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
