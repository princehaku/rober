# Sprint 2026.05.17_16-17 Route Task Result Backfill Review Decision - PRD

sprint_type: epic

## 1. 产品问题

上一轮 `route_task_field_retest_result_acceptance_backfill` 已经把 route/elevator result materials 接入 backfill 入口，但它仍偏“材料是否回填”的检查层。下一次真实现场补录需要的是“该接受、缺什么、退回什么、谁补、怎么重跑”的决策层。

本轮要规划并交给工程实现 `route_task_field_retest_result_backfill_review_decision`：把 backfill artifact / summary 转成 review decision、accepted / missing / rejected material status、owner handoff、next required evidence 和 rerun commands，并让 Robot diagnostics 与 `mobile/web` 只读展示。

## 2. 用户价值和产品北极星

用户价值：

- 现场支持人员能快速判断同一 `evidence_ref` 下哪些 route/elevator 材料已可接受、哪些缺失、哪些需要退回。
- 普通手机用户或非 ROS2 支持人员看到的是中文优先的下一步，不需要理解 raw JSON、ROS topic、串口、Nav2 或本地文件路径。
- Engineer 能按明确 rerun commands 和 owner handoff 继续补材料，而不是重新解读上一轮 artifact。

产品北极星：

把 `rober` 做成低成本、可复核、可交付的 ROS2 垃圾投递机器人。核心不是堆节点或测试数量，而是让“用户把垃圾交给小车 -> 小车跨路线/电梯 -> 到站投递/异常可接管”具备可追溯证据链。

## 3. 背景证据

- `OKR.md` 4.1 2026-05-17 15:18 快照显示 Objective 5 约 68%，仍最低；但 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 证据。因此本轮不做 O5 metadata wrapper。
- `2026.05.17_15-16_route-task-result-acceptance-backfill` 完成 `software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate`，Objective 2 / Objective 3 到约 96%，但真实现场仍缺 route/elevator field pass、Nav2/fixed-route、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion 和 delivery_result。
- PR #4 把 elevator-assisted delivery 设为主线必须能力，因此 route/elevator 材料链需要继续推进到 review decision。
- PR #5 review 指出 hardware boundary、mandatory sensor baseline 和 vendor/source citation 问题；但真实 2D LiDAR / ToF 材料不可得，本轮不包装硬件 blocker。
- 本轮证据必须保持 `software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. OKR 映射

Objective 2：送垃圾任务 + 电梯 assisted delivery 必达闭环。

- 本轮通过 review decision 明确 route/elevator result backfill 的材料状态，让真实 door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery_result 的补录/退回路径可执行。

Objective 3：可验证导航与固定路线能力。

- 本轮通过同一 `evidence_ref` 的 material status 和 rerun commands，推动 Nav2/fixed-route runtime log、route completion signal、task record 从材料回填入口进入复核决策。

Objective 4：手机用户体验与低成本量产边界。

- 本轮让 mobile/web 只读显示 review decision 和下一步，保证普通用户/支持人员能理解状态，同时不暴露 raw artifact 或控制授权。

Objective 5：云中转 + OSS/CDN 数据通路产品化。

- 本轮不推进 Objective 5。缺真实 external proof 时，任何本地 Docker-only wrapper 都不能证明公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser。

## 5. KR 拆解或更新

KR1：PC review decision gate。

- 输入：上一轮 `trashbot.route_task_field_retest_result_acceptance_backfill.v1` artifact 或 summary。
- 输出：`trashbot.route_task_field_retest_result_backfill_review_decision.v1` artifact 与 summary。
- 必须包含：source backfill status、safe `evidence_ref`、material status、accepted materials、missing materials、rejected materials、owner handoff、next required evidence、rerun commands、safe copy、not proven、boundary flags。

KR2：Robot diagnostics 只读消费。

- 支持 file/env/top-level/nested summary。
- 对 unsupported schema/boundary、unsafe copy、success claim、`delivery_success=true`、`primary_actions_enabled=true` fail closed。
- 不改变 task_orchestrator、action server、Start、Confirm Dropoff、Cancel 控制语义。

KR3：Mobile/web 只读展示。

- 新增“路线任务回填复核决策” panel。
- 展示 review decision、material status、owner handoff、next required evidence、rerun command summary、safe evidence ref、not proven 和 boundary。
- copy/export 只使用白名单字段；缺 safe copy 时显示 blocked copy unavailable。

KR4：Product closeout。

- 更新 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 若实现确实落地且验证通过，再按证据边界更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- 确保相关 `docs/` 产品文档反映新增 review decision surface。

## 6. 本轮核心抓手

把上一轮 backfill 的“材料入口”升级为“复核决策”。工程输出必须帮助下一次真实现场材料补录：哪些材料 accepted，哪些 missing，哪些 rejected，谁负责补，下一步补什么，如何重跑。

## 7. 范围

本轮做：

- PC software proof gate。
- Robot diagnostics metadata-only consumer。
- `mobile/web` read-only panel。
- 产品与接口文档同步。
- sprint 收口与 OKR 证据边界更新准备。

本轮不做：

- 不接入真实 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。
- 不证明真实 route/elevator field pass、HIL、真实手机/browser、O5 external proof、dropoff success、cancel success 或 delivery success。
- 不修 PR #5 硬件材料 blocker，不新增 2D LiDAR / ToF hardware facts。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。

## 8. 验收口径

P0：

- `software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate` 出现在 PC artifact、Robot diagnostics summary、mobile/web copy 和 sprint closeout 中。
- 所有输出保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- review decision 覆盖 accepted / missing / rejected material status、owner handoff、next required evidence 和 rerun commands。
- Robot diagnostics 与 mobile/web 只读展示，不能改变控制授权。
- 通过小围栏验证：`py_compile`、focused unittest、CLI `--help`、`node --check`、required `rg`、scoped `git diff --check`。

P1：

- 同一 `evidence_ref` mismatch、unsupported schema、unsupported boundary、unsafe copy、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 被拒绝。
- mobile copy 中文优先，不能出现真实完成、真实送达、真实 HIL、真实手机通过或 O5 production proof 暗示。

## 9. 对应责任 Engineer

- `autonomy-engineer`：PC gate、schema、focused unittest、CLI help、evidence docs snippet。
- `robot-software-engineer`：diagnostics consumer、diagnostics tests、ROS contract 文档。
- `full-stack-software-engineer`：mobile/web panel、fixture、mobile tests、`docs/product/mobile_user_flow.md`。
- `product-okr-owner`：sprint docs、OKR mapping、side-by-side check、final closeout。

## 10. 风险、阻塞和证据链缺口

- 本轮只处理 Docker/local software proof，不会补齐真实路线、真实电梯、真实 Nav2/fixed-route、真实 task record、真实 completion signal、真实 dropoff/cancel completion、delivery_result 或 delivery_success。
- Objective 5 仍最低，但缺真实 external proof，本轮不能提升 O5。
- PR #5 hardware blocker 仍存在，但没有真实 sensor/source/procurement/install/calibration/HIL-entry 材料，本轮不继续消费。
- 若工程实现只新增展示但未形成 review decision schema 与 fail-closed 规则，则不能视为完成本 PRD。

## 11. 需要创建或更新的 sprint 文档

本 planning 阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现和收口阶段必须继续创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
