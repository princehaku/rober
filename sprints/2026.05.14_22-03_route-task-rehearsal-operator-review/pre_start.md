# Sprint 2026.05.14_22-03 Route Task Rehearsal Operator Review - Pre Start

sprint_type: epic

## 开工背景

本轮目标是把上一轮 `2026.05.14_21-22_route-task-rehearsal-execution-bundle` 的 route/task rehearsal execution bundle 和 diagnostics 摘要，推进成面向操作员的任务复盘/下一轮重跑决策能力。目标 evidence boundary 为 `software_proof_docker_route_task_rehearsal_operator_review_gate`。

当前 `OKR.md` 4.1 显示 Objective 5 约 68%，是数字最低 Objective；但 `OKR.md` 第 6 节与最近 final 均明确：继续推进 O5 completion 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料。本机只有 Docker，没有真实外部云材料，因此本轮不继续叠加本地 O5 metadata。

Objective 1 约 75%，但 CEO 已明确“本机没有真实硬件，只有docker”。当前环境不得声明 HIL、真实 WAVE ROVER、真实 UART/串口、`T=1001` feedback、`/odom`、`/imu/data` 或 `/battery` 实机样本。

Objective 2 和 Objective 3 均约 80%。上一轮已经完成 `software_proof_docker_route_task_rehearsal_execution_bundle_gate`，但 final 明确后续不要继续扩展本地 bundle 包装层，应推进真实路线/任务证据，或更接近操作员复盘/下一轮重跑决策的功能。本轮选择后者：在 Docker-only 可执行边界内，把 execution bundle 变成操作员可读、phone/support-safe、可用于判断下一次 rehearsal 是否重跑的 review package。

## 用户价值和产品北极星

产品北极星仍是：普通手机用户把垃圾交给小车后，小车能沿固定路线完成送达，并且失败时用户和支持人员能看懂下一步怎么处理。本轮不证明真实送达，而是让支持/操作员从 route/task rehearsal 的软件证据中快速判断：

- 这次排练关联哪个 `evidence_ref`；
- crosscheck 是否通过，HIL alignment 是否仍为 `not_proven`；
- 是否存在 mismatch、缺材料或 schema 不兼容；
- 下一轮应该重跑 rehearsal、补路线/task record、补真实硬件材料，还是升级到真实路线/任务证据；
- 哪些字段可以安全展示或复制给手机/支持人员，且不会泄露 artifact/raw path、凭证、硬件细节或把 ACK/metadata 写成 delivery success。

## OKR 映射

- Objective 2：把“可送垃圾任务闭环”的软件复盘从 execution bundle 推进到 operator review decision，帮助定位装载、送达、失败恢复与 dropoff/cancel completion 仍缺什么证据。
- Objective 3：把固定路线软件排练从 route status/task record/crosscheck artifact 串联，推进到操作员可读的 next rehearsal decision，帮助下一轮走向真实 route/Nav2/fixed-route 证据。
- Objective 5：数字最低但外部材料阻塞。本轮只允许 phone/support-safe 展示，不新增云中转 readiness claim，不替代真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料。
- Objective 1：硬件阻塞。本轮不读取硬件、不触发 Nav2、不声明 HIL、WAVE ROVER 或真实串口。

## 本轮核心抓手

核心抓手是 `software_proof_docker_route_task_rehearsal_operator_review_gate`：一个只读、phone/support-safe、metadata-only 的 operator review 链路，消费上一轮 `route_task_rehearsal_execution_bundle.json`，输出操作员能直接复盘的 summary，并在 diagnostics 与 `mobile/web` 首屏/诊断区域展示。

## 需要做什么

1. Autonomy 生成 operator review package：消费 execution bundle，输出 `evidence_ref`、crosscheck/HIL 边界、mismatch 摘要、`next_rehearsal_decision`、`not_proven` 和 whitelist-only `safe_copy`。
2. Robot diagnostics 只读消费 operator review package：生成 diagnostics summary，metadata-only，不触发 Start/Confirm/Cancel、ACK POST、cursor/persistence、HIL、dropoff/cancel completion 或 delivery success。
3. Full-stack 在 `mobile/web` 首屏或诊断附近渲染 operator review 摘要：只消费 `/api/status`、`phone_readiness`、`/api/diagnostics` 的 phone-safe 字段；Start/Confirm/Cancel 保持 fail-closed。

## Owner 与并行策略

本轮是跨 owner epic sprint，默认并行 3 个工程子 agent：

- Task A：`autonomy-engineer` 主责 operator review/report 生成器。
- Task B：`robot-software-engineer` 主责 diagnostics 只读消费与 metadata-only 围栏。
- Task C：`full-stack-software-engineer` 主责 `mobile/web` phone-safe 展示与 whitelist-only copy。

三个任务文件范围互不重叠，但接口耦合在 operator review package schema。Autonomy 先定义最小 schema；Robot 与 Full-stack 可并行围绕该 schema 做只读消费，若 schema 字段不一致，退回 Autonomy 修正并重跑围栏。

## 风险、阻塞和证据链

- O5 风险：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料；本轮不得上调 O5。
- O1 风险：本机只有 Docker，没有真实硬件；本轮不得声明 HIL、WAVE ROVER、真实串口或底盘 feedback。
- O2/O3 风险：operator review 仍是软件复盘，不是真实 Nav2/fixed-route 实跑，不是同一 `evidence_ref` 的上车复账，不是真实 dropoff/cancel completion，也不是 delivery success。
- 隐私和安全风险：mobile/support copy 必须 whitelist-only，不暴露 artifact/raw path、local path、traceback、checksum、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER、credential、DB/queue URL 或完整 raw artifact。

## 需要创建或更新的 sprint 文档

本轮先创建：

- `sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/pre_start.md`
- `sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/prd.md`
- `sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/tech-plan.md`

工程完成后必须继续更新：

- `sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/tech-done.md`
- `sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/side2side_check.md`
- `sprints/2026.05.14_22-03_route-task-rehearsal-operator-review/final.md`

若实现改变用户流程或接口说明，还必须同步更新 `docs/` 下相关文档；Product closeout 才能在 final 中判断是否更新 `OKR.md` 进度。
