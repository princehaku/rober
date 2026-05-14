# Sprint 2026.05.15_00-01 Route Task Field Run Readiness - Pre Start

sprint_type: epic

## 开工判断

本轮创建 fresh Epic sprint：`sprints/2026.05.15_00-01_route-task-field-run-readiness/`。

触发背景：

- `OKR.md` 4.1 当前最低 Objective 是 Objective 5，约 68%，但本机仍是 Docker-only，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration；继续堆本地 metadata 不能提升 O5。
- Objective 1 约 75%，但本机缺真实 WAVE ROVER、串口/UART、`T=1001` feedback、HIL 或真实底盘运动材料；本轮不能推进硬件完成度。
- 最新 sprint `sprints/2026.05.14_23-24_pc-route-debug-console/final.md` 明确建议：若无 O5 外部材料，下一轮转向 Objective 2/3，用真实 Nav2/fixed-route 或同一 `evidence_ref` 上车复账材料，把 PC console software proof 连接到真实路线/任务证据。
- 近两轮 route/task sprint 都把结论写在 Docker/local software proof 边界内，没有真实 route run、HIL 或 delivery success；本轮目标不是再包装一个成功结论，而是把下一次真实路线-任务联跑前需要准备、运行、补证据和复账的材料变成可执行 readiness handoff。

## 用户价值和产品北极星

北极星仍是：普通手机用户把垃圾交给小车后，小车可验证地沿固定路线送到垃圾站/垃圾桶点位，并在失败时给出可理解、可复盘、可支持的证据链。

本轮用户价值：

- 现场操作员在下一次真实路线-任务联跑前，不再从 PC route debug console、route_task operator review、execution bundle、diagnostics 和手机只读摘要里手工拼材料。
- 工程同学能围绕同一 `evidence_ref` 准备真实路线/任务联跑所需的命令、缺失材料、not_proven 列表、phone/support-safe 摘要和复账要求。
- 手机用户只看到只读 availability / next evidence 摘要，不接触 raw artifact、本地路径、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 参数或任何会误解成控制授权的内容。

## OKR 映射

- Objective 2：本轮服务“可送垃圾任务完整闭环”的复盘和下一次真实联跑准备。只允许在最终有工程 proof 后保守调整；不得宣称真实送达、dropoff/cancel completion 或 delivery success。
- Objective 3：本轮服务“可验证导航与固定路线能力”的 route/task handoff，要求能把 PC debug、operator review、execution bundle 汇总到同一 `evidence_ref` 的 field-run readiness 包。
- Objective 5：本轮不提升。缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- Objective 1：本轮不提升。缺真实 WAVE ROVER、串口/UART、HIL、真实 feedback 和底盘实机样本。

## 本轮核心抓手

交付 `route_task_field_run_readiness` handoff：

- schema：`trashbot.route_task_field_run_readiness.v1`
- evidence boundary：`software_proof_docker_route_task_field_run_readiness_gate`
- 输入：PC route debug console summary、route_task operator review、execution bundle 或兼容 diagnostics summary。
- 输出：同一 `evidence_ref` 要求、缺失材料、可运行命令、not_proven、phone/support-safe 摘要、下一次真实路线-任务联跑前的 readiness verdict。

## 责任分工

- Task A `autonomy-engineer`：新增/更新 `pc-tools/evidence/route_task_field_run_readiness.py`、相关 README / `docs/navigation`，负责 readiness artifact schema、CLI、输入汇总和固定路线/任务材料清单。
- Task B `robot-software-engineer`：在 diagnostics 中 metadata-only 消费 readiness artifact，更新 tests/docs，证明不触发控制动作。
- Task C `full-stack-software-engineer`：在 `mobile/web` 增加只读 route-task field-run readiness availability / next evidence panel，更新 fixture/test/docs，不读取 raw artifact，不改变 Start/Confirm/Cancel gating。
- Task D `product-okr-owner`：工程完成后收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`；保守更新 Objective 2/3，Objective 5 不提升。

## 风险和阻塞

- 真实路线、HIL、delivery success 仍阻塞于真实 Nav2/fixed-route 上车运行、真实 WAVE ROVER/串口/HIL 和同一 `evidence_ref` 的现场材料。
- O5 仍阻塞于真实外部材料，不得用本轮 Docker/local readiness artifact 替代。
- readiness 包如果没有明确 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 和 phone-safe copy，容易被误读为真实联跑通过；tech-plan 必须把这些字段列为验收要求。
- 本轮涉及跨 owner 接口，但文件范围互不重叠；后续实现应按 tech-plan 同一轮并行派 3 个 engineer worker，Product closeout 只在工程返回后进行。
