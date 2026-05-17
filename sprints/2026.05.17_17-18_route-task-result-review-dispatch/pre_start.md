# Sprint 2026.05.17_17-18 Route Task Result Review Dispatch - Pre Start

sprint_type: epic

## 1. 启动结论

状态：`PLANNING_READY_FOR_ENGINEERING_DISPATCH`。

本轮新建 epic sprint：`sprints/2026.05.17_17-18_route-task-result-review-dispatch/`。核心抓手是 `route_task_field_retest_result_review_dispatch`，证据边界固定为 `software_proof_docker_route_task_field_retest_result_review_dispatch_gate`。

本轮只规划下一步工程执行，不修改产品代码、测试代码、`OKR.md` 或其他 `docs/`。实现阶段必须由工程 agent 并行执行，并继续创建或更新 `tech-done.md`、`side2side_check.md`、`final.md`。

## 2. 用户价值和产品北极星

用户价值：上一轮已经能把 route/elevator result backfill 转成 accepted / missing / rejected review decision；本轮要把这个决策变成现场可执行的派发包，让现场 owner 知道哪些材料已接受、哪些要补、哪些要退回、回调包要带什么、如何重跑，以及所有材料必须继续绑定同一 `evidence_ref`。

产品北极星仍是低成本 ROS2 自主垃圾投递机器人闭环。当前不追求再包装云端或硬件 blocker，而是把 PR #4 elevator-assisted delivery 主链的 route/elevator 现场材料链继续往前推进，帮助后续真实现场补料能按 owner work order 执行和复核。

## 3. 当前证据

- `OKR.md` 4.1 当前显示 Objective 5 约 68%，数值最低；但第 6 节要求只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover 或真实手机/browser external proof 才继续推进 O5 completion。本机只有 Docker，没有真实硬件或真实 external proof。
- 最新 sprint `sprints/2026.05.17_16-17_route-task-result-backfill-review-decision/final.md` 已完成 `route_task_field_retest_result_backfill_review_decision`，Objective 2 / Objective 3 到约 97%。剩余缺口仍是真实 route/elevator field pass、真实 Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result。
- PR #4 merged “Add elevator-assisted delivery capability to agents, registry and OKR”，无 review comments；它把 elevator-assisted delivery 变成主链。
- PR #5 merged “Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline”。Codex review comments 指出 `docs/product/production_hardware_boundary.md` 默认硬件集与 mandatory `monocular + 2D LiDAR + ToF` baseline 矛盾，`OKR.md` lowest objective narrative 曾与表格不一致，mandatory sensor assumptions 缺 `docs/vendor/` 本地资料引用。
- 最近几轮已多次消费 O5 external proof blocker 与 PR #5 hardware/source/config blocker；本轮按同一 blocker 重复消费红线，切换到可在 Docker-only 上推进的 Objective 2 / Objective 3 route/elevator result-material 派发闭环。

## 4. 本轮 OKR 映射

- Objective 2：把电梯 assisted delivery 主链的现场结果材料从 review decision 推进到 owner 派发与 callback packet 要求，让 door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result 的补料路径可执行。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 等路线结果材料从 accepted/missing/rejected 决策推进到 rerun commands 与同一 `evidence_ref` work order。
- Objective 5：本轮不推进。缺真实 external proof 时，不得把本地 Docker-only dispatch gate 写成 O5 production proof。

## 5. 本轮核心抓手

抓手：`route_task_field_retest_result_review_dispatch`。

输出目标：

- accepted / missing / rejected material categories。
- owner work orders。
- callback packet requirements。
- rerun commands。
- `same_evidence_ref_required=true`。
- `safe_copy`。
- `not_proven`。
- `delivery_success=false`。
- `primary_actions_enabled=false`。

## 6. Owner 与并行规则

本轮是跨 owner epic，默认拆 4 个并行工程 agent：

- `autonomy-engineer`：PC dispatch gate。
- `robot-software-engineer`：diagnostics metadata-only consumer。
- `full-stack-software-engineer`：mobile/web 只读 panel。
- `product-okr-owner`：closeout、OKR 边界和 sprint 收口。

## 7. 风险、阻塞和证据链缺口

- 本轮只规划 Docker-only software proof，不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 route completion signal、真实 dropoff/cancel completion、delivery success、真实手机/browser、WAVE ROVER、真实串口/UART、HIL 或 Objective 5 external proof。
- PR #5 真实 2D LiDAR / ToF source、SKU、receipt、procurement、installation、wiring、power、calibration、HIL-entry 材料仍缺；本轮不继续消费该 blocker。
- 若实现阶段只做展示而没有 dispatch schema、owner work orders、callback packet requirements 和 fail-closed 规则，不能视为完成。

## 8. 需要创建或更新的 sprint 文档

Planning 阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

工程实现与收口阶段必须继续创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
