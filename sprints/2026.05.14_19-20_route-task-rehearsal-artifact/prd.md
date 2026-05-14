# Sprint 2026.05.14_19-20 Route Task Rehearsal Artifact - PRD

## 用户价值和产品北极星

普通用户最终要的是小车能稳定完成“我把垃圾放上车后，它能按固定路线送到垃圾站，并且失败时能解释原因”。当前 Docker-only 环境不能证明真实路线实跑，但可以先把路线状态、任务记录和对账结果合成一个可保存的 rehearsal artifact，让工程团队在上车前知道：

- 当前 fixed-route 软件状态是否能被复盘。
- task record 是否和路线进度使用同一个 `evidence_ref`。
- 对账工具是否能明确区分软件排练、真实 HIL 缺失和失败原因。
- 后续真实 Nav2/fixed-route / HIL run 要补哪些证据，而不是靠聊天或零散日志口头判断。

产品北极星：每一次路线/任务排练都能留下同一 `evidence_ref` 的可复核证据包，支撑后续从软件排练走向真实路线实跑和真实送达闭环。

## OKR 映射

- Objective 2：可送垃圾任务完整闭环
  - KR2：送达 action 使用 garbage station waypoint/fixed route 输入，不再停留在占位逻辑。artifact 要能说明本次任务使用的 route/task 证据。
  - KR4：导航失败、投放失败、超时取消需要明确 action result 和 error message。artifact 要保存失败边界，不把失败包装成成功。
  - KR5：每次任务产出可复盘记录。artifact 要把 task record 与路线 evidence 对齐。
- Objective 3：可验证导航与固定路线能力
  - KR2：fixed-route 输入输出格式和文档固化。artifact schema 与文档必须写清。
  - KR3：fixed route dry-run 在无 Nav2/无硬件环境下验证路线读取、状态输出和软件回放。artifact 是本轮核心交付。
  - KR5：PC 侧能展示或至少保存当前位置、目标点、匹配状态、失败原因和最近任务状态的证据摘要。本轮先做保存型 artifact，不做新 UI。

本轮不直接提升 Objective 1 或 Objective 5。Objective 1 缺真实硬件，Objective 5 缺真实外部云/4G/OSS/CDN/DB/queue 材料。

## KR 拆解或更新

本轮把 O2/O3 的软件证据拆为三个可验收增量：

1. Route rehearsal artifact summary
   - 输入：fixed-route status JSON、software proof replay JSONL、可选 task record、可选 HIL gate 输出。
   - 输出：可保存 JSON 或 markdown summary，包含 schema/version、`evidence_ref`、route status、task status、crosscheck result、`not_proven`。
   - 边界：证据类型固定为 `software_proof_docker_route_task_rehearsal_artifact_gate`。

2. Task record compatibility
   - task record 中的 `route_progress`、`nav_results[-1].evidence.route_progress`、`evidence_ref` 要能被 artifact 消费。
   - 缺失、错配或 HIL gate 非 `hil_pass` 时必须显示 blocked / not proven，不允许生成 delivery success。

3. Product closeout
   - `OKR.md` 和 `docs/process/okr_progress_log.md` 只记录 Docker-only 软件排练证据。
   - sprint closeout docs 必须说明仍缺真实 Nav2/fixed-route、WAVE ROVER、HIL 和真实送达。

## 本轮核心抓手

核心抓手是“同一 `evidence_ref` 的路线任务排练证据包”，不是新增路线算法、不是手机 UI，也不是云端能力。

必须产出的可交付能力：

- `pc-tools/evidence/evidence_crosscheck.py` 或相邻 evidence helper 支持 summary/artifact output。
- artifact 中能看到 status/replay/task_record/HIL gate 的对账结论。
- 文档说明如何保存 artifact、如何理解 `software_proof_docker_route_task_rehearsal_artifact_gate`、哪些真实证据仍未证明。
- 既有 fenced test 或最小新增测试覆盖 artifact schema、match/mismatch、HIL 非 pass 边界。

## 非目标

- 不实现真实 Nav2 实跑。
- 不接 WAVE ROVER、ESP32、Orange Pi 串口，不声明 `hil_pass`。
- 不新增手机端 UI，不继续堆 O4 手机材料。
- 不新增云端、公网、4G/SIM、OSS/CDN、production DB/queue 能力。
- 不把 ACK、HTTP accepted、task record success 或 artifact pass 写成真实 delivery success。
- 不做大规模测试扩张；只做与 artifact 输出和兼容性直接相关的 fenced validation。

## 优先级和验收口径

P0：

- artifact 输出存在且可保存，schema/version/evidence boundary 明确。
- artifact 能消费 fixed-route status + replay，并在存在 task record 时校验 `evidence_ref` 与 `route_progress`。
- artifact 明确输出 `software_proof_docker_route_task_rehearsal_artifact_gate`。
- `not_proven` 至少包含真实 Nav2/fixed-route、WAVE ROVER、真实串口、HIL、真实 dropoff/cancel completion、真实 delivery success。
- HIL gate 缺失或非 `hil_pass` 时，artifact 不得声明真实 run closure。

P1：

- `pc-tools/README.md` 与 `docs/navigation/fixed_route_workflow.md` 更新 artifact 使用说明。
- `docs/interfaces/ros_contracts.md` 更新 task record / evidence boundary 兼容说明。
- Product closeout 按结果更新 OKR 和 progress log。

## 责任 Engineer

- `autonomy-engineer`：Task A，route/evidence artifact 输出与导航文档。
- `robot-software-engineer`：Task B，task record / behavior compatibility 与 ROS contract 文档。
- `product-okr-owner`：Task C，OKR、进度日志、sprint 收口与证据边界。

## 风险、阻塞和证据链缺口

- Docker-only 主机不能证明真实 Nav2、真实硬件运动或 HIL；最终必须保留软件证明边界。
- 如果 task record 当前只覆盖部分 fixed-route 场景，Robot 侧需要先补兼容性或 fenced test，不能由 Product 文档替代。
- 如果 artifact pass 只是对账通过，仍不等于任务真实送达；必须在 schema 和文档里固定 `not_proven`。
- 后续真正提升 O2/O3 仍需要真实路线采集、Nav2/fixed-route 实跑、关键帧实景证据、同一 `evidence_ref` 的上车复账。

## 需要创建或更新的 sprint 文档

本轮规划阶段创建：

- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/pre_start.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/prd.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/tech-plan.md`

实现与验收后必须继续更新：

- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/tech-done.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/side2side_check.md`
- `sprints/2026.05.14_19-20_route-task-rehearsal-artifact/final.md`
