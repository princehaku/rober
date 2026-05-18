# Sprint 2026.05.18_17-18 Route Task Acceptance Execution Rerun Result Intake - Pre Start

## 1. Sprint 类型与启动结论

- sprint_type: epic
- 启动时间：2026-05-18 17:18 Asia/Shanghai。
- 主题：`route_task_field_retest_acceptance_execution_rerun_result_intake`。
- 证据边界：`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate`。
- 本轮目标：把上一轮受控复跑队列推进为“受控复跑结果回执入口 / 结果材料 intake”metadata-only software proof。
- 明确不做：真实 route/elevator field pass、真实 delivery success、HIL、真实手机/browser、Objective 5 external proof、PR #5 硬件 baseline 真实材料闭环。

## 2. 用户价值和产品北极星

产品北极星仍是：普通手机用户把垃圾交给低成本 ROS2 小车后，小车沿固定路线完成送达、电梯 assisted delivery 和异常解释，而用户不需要接触 SSH、ROS2、串口、raw JSON 或底层硬件材料。

本轮用户价值不是证明现场复跑成功，而是让现场 owner、Robot diagnostics 和手机端都能接住同一 `evidence_ref` 的复跑结果回执材料，并把结果分成可执行的下一步：进入 review、要求 backfill、要求同一证据重跑、拦截 unsafe copy、或拒绝 unsupported queue。这样避免把“队列已准备好”误读成“真实路线 / 电梯 / 投放已经通过”。

## 3. 证据输入

- `OKR.md` 4.1 当前快照：Objective 5 约 68% 为最低；但仍缺真实 HTTPS/TLS、公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser。按 stop rule，本轮不继续本地 O5 metadata。
- `OKR.md` 4.1 当前快照：Objective 1 约 81%；但本机无真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report，且硬件 blocker 已反复消费。本轮不继续包装同一硬件 blocker。
- 最新 sprint `sprints/2026.05.18_16-17_route-task-acceptance-execution-rerun-queue/final.md`：已完成 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`，剩余真实 route/elevator materials 包括真实 route completion signal、task record、dropoff/cancel completion、delivery result 等。
- PR #4 已合并，elevator-assisted delivery 成为必达主链，后续 route/elevator sprint 不能把电梯链路当作可选 H2 分支。
- PR #5 review 指出 `docs/product/production_hardware_boundary.md` 的默认硬件集合与 `monocular + 2D LiDAR + ToF` baseline 曾存在矛盾；新硬件 baseline 缺 `docs/vendor/` source citation；OKR lowest narrative 曾不一致。这些是硬件真实材料和评审风险，本 Docker-only sprint 不虚假解决。
- 硬件事实边界已按 `docs/vendor/VENDOR_INDEX.md` 核对：本地 vendor tree 覆盖 Orange Pi Zero 3、WAVE ROVER、UART newline-delimited JSON、WAVE ROVER ESP32 firmware/vendor app 和机械资料；它不证明项目 2D LiDAR / ToF SKU、采购、安装、接线、供电、标定或 HIL。

## 4. 本轮核心抓手

本轮抓手是新增受控复跑结果回执入口，把上一轮 rerun queue artifact / summary 和可选 safe rerun result packet 转成 metadata-only intake 状态：

- `ready_for_acceptance_execution_rerun_result_review_not_proven`
- `needs_acceptance_execution_rerun_result_backfill`
- `evidence_ref_mismatch_rerun_result`
- `blocked_unsafe_rerun_result`
- `blocked_unsupported_rerun_queue`

所有输出必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. Owner 与并行形态

本轮是 Epic sprint，按三条互不重叠文件范围并行执行：

- Autonomy Algorithm Engineer：实现 PC evidence gate、focused tests、PC README 和 evidence contract。
- Robot Platform Engineer：让 operator gateway diagnostics 只读消费 sanitized summary，不暴露 raw artifact 或控制入口。
- User Touchpoint Full-Stack Engineer：让 mobile/web 只读展示 result intake 状态，保持 Start / Confirm Dropoff / Cancel fail-closed。

Product Owner 只维护 sprint 留档、验收口径和阶段收口；不改产品代码、测试代码、硬件配置或业务实现。

## 6. 风险、阻塞和证据链缺口

- 真实 O5 proof 仍缺：HTTPS/TLS、公网、4G/SIM、OSS/CDN、production DB/queue、worker/cutover、真实手机/browser。本轮不提升 Objective 5。
- 真实 O1 proof 仍缺：WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report。本轮不提升 Objective 1。
- 真实 route/elevator materials 仍缺：真实 route completion signal、task record、Nav2/fixed-route runtime log、真实门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result。
- PR #5 硬件风险仍缺真实材料：2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 本轮只能证明 repo 内 Docker/local metadata gate、diagnostics summary 和 mobile/web read-only panel 的 fail-closed 合约。

## 7. 本轮需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`。
- 本轮规划阶段必须创建：`prd.md`、`tech-plan.md`。
- 后续 Engineer 并行实现完成后必须更新：`tech-done.md`、`side2side_check.md`、`final.md`。
