# Sprint 2026.05.18_18-19 Route Task Acceptance Execution Rerun Result Review Decision - Pre Start

## 1. Sprint 类型与启动结论

- sprint_type: epic
- 启动时间：2026-05-18 18:19 Asia/Shanghai。
- 主题：`route_task_field_retest_acceptance_execution_rerun_result_review_decision`。
- 目标证据边界：`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`。
- 本轮目标：把上一轮 `route_task_field_retest_acceptance_execution_rerun_result_intake` 转成可执行的 review decision，明确进入 handoff、backfill、mismatch、unsafe 或 unsupported 分支。
- 明确不做：真实 route/elevator field pass、真实 delivery success、HIL、真实手机/browser、Objective 5 external proof、PR #5 2D LiDAR / ToF 真实硬件材料闭环。

## 2. 用户价值和产品北极星

产品北极星仍是：普通手机用户把垃圾交给低成本 ROS2 小车后，小车沿固定路线完成送达、电梯 assisted delivery、异常解释和可复盘证据链，而用户不需要接触 SSH、ROS2、串口、raw JSON、硬件接线或云基础设施。

本轮用户价值是让现场 owner、Robot diagnostics 和手机端都能把“受控复跑结果回执入口”变成明确下一步，而不是停留在 intake 状态。现场材料足够时进入 `ready_for_acceptance_execution_rerun_result_handoff`；材料不足时进入 backfill；同一 `evidence_ref` 不一致时进入 mismatch；存在 unsafe copy 或成功宣称时拦截；输入不属于上一轮支持的 intake/queue 时拒绝 unsupported。

## 3. 证据输入

- `OKR.md` 4.1 当前快照：Objective 5 约 68% 为数字最低；但仍缺真实外部 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover、真实手机/browser。按 stop rule，本轮不继续堆 Objective 5 本地 metadata。
- `OKR.md` 4.1 当前快照：Objective 1 约 81%；但本机无真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，且 PR #5 2D LiDAR / ToF 真实 vendor/source/receipt/procurement/HIL-entry 材料仍缺。本轮不继续消费同一硬件 blocker。
- 最新 sprint `sprints/2026.05.18_17-18_route-task-acceptance-execution-rerun-result-intake/final.md`：已完成 `route_task_field_retest_acceptance_execution_rerun_result_intake`，并明确下一步是 review/backfill/mismatch/unsafe/unsupported 判定。
- PR #4 要求 elevator-assisted delivery 进入主链；route/elevator 现场材料链必须继续可回填、可复核、可追责。
- PR #5 unresolved review threads 指出 `docs/product/production_hardware_boundary.md` 默认硬件集合与 `monocular + 2D LiDAR + ToF` baseline 矛盾，以及新增 sensor baseline 缺 `docs/vendor/` source citation。本轮只把该风险保留为真实硬件材料缺口，不伪造解决。

## 4. 本轮核心抓手

本轮抓手是 result intake 后的 metadata-only review decision：

- `ready_for_acceptance_execution_rerun_result_handoff`
- `needs_acceptance_execution_rerun_result_backfill`
- `evidence_ref_mismatch_rerun_result`
- `blocked_unsafe_rerun_result`
- `blocked_unsupported_rerun_result_intake`

所有输出必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. Owner 与并行形态

本轮是 Epic sprint，预计 3 个 Engineer 并行执行，文件范围互不重叠：

- Autonomy Algorithm Engineer：实现 PC evidence review decision gate、focused tests、PC README 和 evidence contract。
- Robot Platform Engineer：让 operator gateway diagnostics 只读消费 sanitized review decision summary，不暴露 raw artifact 或控制入口。
- User Touchpoint Full-Stack Engineer：让 mobile/web 只读展示 result review decision 状态，保持 Start / Confirm Dropoff / Cancel fail-closed。

Product Manager / OKR Owner 只维护 sprint 留档、验收口径和阶段收口；不改产品代码、测试代码、硬件配置或业务实现。

## 6. 风险、阻塞和证据链缺口

- Objective 5 仍缺真实外部 proof：HTTPS/TLS、公网、4G/SIM、OSS/CDN、production DB/queue、worker/cutover、真实手机/browser。本轮不提升 Objective 5。
- Objective 1 仍缺真实硬件 proof：WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report、PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。本轮不提升 Objective 1。
- PR #4 现场证据仍缺：真实 route completion signal、task record、Nav2/fixed-route runtime log、真实门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result。
- 本轮只能证明 repo 内 Docker/local metadata gate、diagnostics summary 和 mobile/web read-only panel 的 fail-closed 合约。

## 7. 本轮需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`。
- 本轮规划阶段必须创建：`prd.md`、`tech-plan.md`。
- 后续 Engineer 并行实现完成后必须更新：`tech-done.md`、`side2side_check.md`、`final.md`。
