# Sprint 2026.05.15_06-07 Route Task Field Run Console - Pre Start

sprint_type: epic

## 1. 启动背景

最新 `OKR.md` 4.1 更新时间为 2026-05-15 04:19 Asia/Shanghai，最新 sprint 为 `2026.05.15_05-06_route-task-completion-signal`。当前完成度最低的是 Objective 2 与 Objective 3，均约 65%；Objective 5 约 66%，但它下一步需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 等外部材料，本机 Docker-only 环境无法补齐。

上一轮已完成 `software_proof_docker_route_task_completion_signal_gate`，把 route/task 材料推进到 completion signal。`final.md` 明确建议：若继续 O2/O3，应从 completion signal 走向真实 field-run；但当前主机没有真实硬件、串口、4G、公网云或真实路线采集条件，因此本轮不能宣称真实 Nav2/fixed-route、真实路线采集、WAVE ROVER/HIL、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 2. 本轮目标

本轮创建并执行 `route_task_field_run_console` 能力规划：把 completion signal 继续推进为 PC/operator-facing 的 field-run 操作台、API、CLI 或同等可执行入口。该入口必须能在 Docker/local 环境中加载 execution pack、completion signal、route status 与 task record，生成现场操作步骤、材料采集模板、same `evidence_ref` 校验和只读状态输出；Robot diagnostics 与 `mobile/web` 只能只读消费 summary。

证据边界固定为 `software_proof_docker_route_task_field_run_console_gate`。它是 field-run 准备与采集入口的软件证明，不是真实 Nav2/fixed-route、真实路线采集、真实硬件/HIL、真实 dropoff/cancel completion、delivery success 或 O5 external proof。

## 3. 本轮用户价值和产品北极星

产品北极星：让普通手机用户最终能把垃圾交给小车，并清楚知道任务是否真实完成、哪里需要人工介入、哪些证据支撑下一次现场复测。

本轮用户价值：现场操作员和 Engineer 不再从散落 JSON、日志和 completion signal 中手动拼 field-run 材料，而是通过一个统一入口拿到“今天要怎么跑、必须采哪些材料、同一个 `evidence_ref` 是否一致、哪些状态仍是 not_proven”。这能把 O2/O3 从软件 completion signal 推向真实 field-run 的可执行准备，而不是继续包一层纯 metadata。

## 4. OKR 映射

- Objective 2：推进 KR4/KR5。field-run console 必须把 task record 状态、dropoff/cancel completion 材料需求、失败/恢复原因和人工下一步收敛为可执行现场步骤；缺真实材料时必须保留 `delivery_success=false` 和 `not_proven`。
- Objective 3：推进 KR2/KR3/KR5。field-run console 必须把 fixed-route status、route execution pack、completion signal 和 task record 的 same `evidence_ref` 校验固化为 PC/operator 可见流程。
- Objective 4：只做支援。`mobile/web` 如有改动，仅可只读展示 field-run summary，不改变 Start/Confirm/Cancel gating，不证明真实手机或 production app。
- Objective 5：本轮不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration 材料时，不继续堆本地 O5 metadata。

## 5. Owner 和执行方式

本轮是跨 owner Epic，默认并行启动 3-4 个 worker：

- Autonomy Algorithm Engineer：主责 PC/evidence field-run console/CLI/API 入口与 route/task material 校验。
- Robot Platform Engineer：主责 diagnostics metadata-only summary consumption 和 ROS2/behavior 边界说明。
- User Touchpoint Full-Stack Engineer：主责 `mobile/web` 只读 summary 消费，保持 phone-safe 和 fail-closed。
- Product Manager / OKR Owner：主责阶段验收、OKR/KR 边界、sprint closeout 和 `OKR.md` 证据更新；不写工程代码。

Hardware Infra Engineer 本轮不写代码，因为没有真实串口、WAVE ROVER、Orange Pi、UART 或机械安装改动。若实现中触及硬件事实，必须先读 `docs/vendor/VENDOR_INDEX.md` 及其指向资料。

## 6. 风险和阻塞

- 本机 Docker-only，无法产生真实 Nav2/fixed-route、真实路线采集、真实串口、WAVE ROVER feedback、HIL、真实 dropoff/cancel completion 或 delivery success。
- Objective 5 仍缺真实外部材料；本轮不能把本地 field-run console 当作 O5 external proof。
- Field-run console 若只输出新 metadata 而不生成可执行现场步骤、采集模板和 same `evidence_ref` 校验，将不能推动 O2/O3。
- Robot diagnostics 和 `mobile/web` 只能消费 summary；任何 raw artifact、本机路径、traceback、credentials、ROS topic、serial/UART、baudrate、WAVE ROVER 或 DB/queue URL 都必须被排除。

## 7. 本轮需要创建或更新的 sprint 文档

Planning 阶段创建：

- `sprints/2026.05.15_06-07_route-task-field-run-console/pre_start.md`
- `sprints/2026.05.15_06-07_route-task-field-run-console/prd.md`
- `sprints/2026.05.15_06-07_route-task-field-run-console/tech-plan.md`

实现完成后必须继续补齐：

- `sprints/2026.05.15_06-07_route-task-field-run-console/tech-done.md`
- `sprints/2026.05.15_06-07_route-task-field-run-console/side2side_check.md`
- `sprints/2026.05.15_06-07_route-task-field-run-console/final.md`
