# Sprint 2026.05.18_19-20 Route Task Acceptance Execution Rerun Result Review Handoff - Pre Start

## 1. Sprint 类型与启动结论

- sprint_type: epic
- 启动时间：2026-05-18 19:03 Asia/Shanghai。
- 主题：`route_task_field_retest_acceptance_execution_rerun_result_review_handoff`。
- 目标证据边界：`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`。
- 本轮目标：把上一轮 `route_task_field_retest_acceptance_execution_rerun_result_review_decision` 转成 owner 可执行 handoff package、Robot diagnostics safe alias 和 mobile read-only handoff panel。
- 明确不做：不读取真实材料目录、不触发机器人、不证明现场通过、不证明 Objective 5 external proof、不证明 Objective 1 HIL 或 WAVE ROVER 硬件闭环。

## 2. 用户价值和产品北极星

产品北极星仍是：普通手机用户把垃圾交给低成本 ROS2 小车后，小车沿固定路线完成送达、电梯 assisted delivery、异常解释和可复盘证据链，而用户不需要接触 SSH、ROS2、串口、raw JSON、硬件接线或云基础设施。

本轮用户价值是把复核决策从“系统判断下一步”推进到“现场 owner 可执行交接”。现场 owner 应该拿到只含 sanitized metadata 的 handoff package，知道要补哪些真实材料、谁负责、如何用同一 safe `evidence_ref` 回填 PR #4 route/elevator 现场证据；Robot diagnostics 和手机端只能展示只读交接状态，不把 handoff、ACK、summary 或 artifact pass 写成真实送达成功。

## 3. OKR 映射

- Objective 5：`OKR.md` 4.1 当前数字最低项，约 68%。本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部证据。按 stop rule，本轮不继续堆本地 O5 metadata。
- Objective 1：约 81%。本机没有真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report；PR #5 的 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料仍缺。本轮不第三次消费同一硬件 blocker。
- Objective 2 / Objective 3 / Objective 4：本轮推进 route/elevator 现场证据链的 PR #4 准备层，把 review decision 变成 owner handoff、Robot 只读诊断和 mobile 只读交接展示。

## 4. 证据输入

- `OKR.md` 4.1 最新快照：Objective 5 数值最低但受真实外部云、4G、DB/queue、OSS/CDN、worker/cutover 和真实手机/browser 证据阻塞。
- `OKR.md` 4.1 最新快照：Objective 1 仍受真实硬件、HIL、WAVE ROVER feedback 和 PR #5 2D LiDAR / ToF 真实材料阻塞。
- 上一轮 `sprints/2026.05.18_18-19_route-task-acceptance-execution-rerun-result-review-decision/final.md` 已完成 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`，并明确下一步需要把 review decision 带到 PR #4 真实现场回填 / owner handoff。
- PR #4 已合并：电梯 assisted delivery 进入主链，route/elevator 现场证据链必须继续推进。
- PR #5 review 未解决点：`docs/product/production_hardware_boundary.md` 默认硬件集合与 `monocular + 2D LiDAR + ToF` mandatory baseline 矛盾；新增 sensor baseline 缺 `docs/vendor/` source citation；OKR 最低项叙述曾漂移。本轮只引用这些风险，不改硬件事实。

## 5. 本轮核心抓手

本轮抓手是 metadata-only handoff package：

- 由 Autonomy 产出 `route_task_field_retest_acceptance_execution_rerun_result_review_handoff` PC gate 和 focused tests。
- 由 Robot diagnostics 转发 safe alias，只暴露 schema、handoff status、safe `evidence_ref`、owner、next required evidence、boundary flags。
- 由 mobile/web 展示只读 handoff panel，不改变 Start Delivery、Confirm Dropoff、Cancel 的 fail-closed gating。

所有输出必须保持 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 6. 需要做什么

1. Autonomy：把上一轮 review decision summary 转成 owner handoff package，覆盖 ready handoff、needs backfill、mismatch、unsafe、unsupported 等交接分支。
2. Robot：在 operator gateway diagnostics 中新增 sanitized handoff alias，保持只读、fail-closed、无 raw artifact 泄漏。
3. Full-stack：在 mobile/web 新增只读 handoff panel 和 fixture/test，保持手机主操作不被 handoff 解锁。
4. Product：后续只做 tech-done、side2side_check、final、OKR.md 和 `docs/process/okr_progress_log.md` 的收口；不改产品代码、测试代码或硬件配置。

## 7. 优先级和验收口径

P0：

- 三个 owner 都使用 `route_task_field_retest_acceptance_execution_rerun_result_review_handoff` family。
- 三个 surface 都包含 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`。
- 三个 surface 都保持 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Robot/mobile 不泄漏 raw artifact、local path、checksum、credentials、DB/queue URL、ROS topic、serial/UART、WAVE ROVER low-level control、success 或 control wording。

P1：

- docs/interfaces 和 docs/product 写清本轮只是 PR #4 真实现场回填准备层。
- final.md 收口时回顾 Objective 5 / Objective 1 blocker 是否仍成立，不因 software proof 上调 O5/O1。

## 8. 对应责任 Engineer

- Autonomy Algorithm Engineer：PC handoff gate、focused unittest、PC README、evidence contract。
- Robot Platform Engineer：operator gateway diagnostics safe alias、Robot diagnostics focused test、ROS contract。
- User Touchpoint Full-Stack Engineer：mobile/web read-only handoff panel、fixture、mobile web focused test、mobile user flow docs。
- Product Manager / OKR Owner：sprint 留档、验收口径和收口证据；不做实现。

## 9. 风险、阻塞和需要补齐的证据链

- PR #4 真实现场仍缺：真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record/completion signal、dropoff/cancel completion 或 delivery result。
- Objective 5 仍缺：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 外部证据。
- Objective 1 仍缺：真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 2D LiDAR / ToF 真实材料。
- PR #5 硬件边界和 vendor source citation 问题本轮只保留为风险，不做硬件事实修复。

## 10. 需要创建或更新的 sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- Engineer 并行实现后更新：`tech-done.md`。
- Product 验收后更新：`side2side_check.md`、`final.md`。
