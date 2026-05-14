# Sprint 2026.05.15_00-01 Route Task Field Run Readiness - PRD

sprint_type: epic

## 产品目标

把上一轮 `software_proof_docker_pc_route_debug_console_gate`、更早的 route_task operator review 和 execution bundle，汇总成下一次真实路线-任务联跑前可执行的 readiness handoff。

本轮不是宣称真实 route run、HIL 或 delivery success，而是让真实试跑前的材料准备变得可复用、可检查、可交接。

## 用户价值和北极星对齐

北极星：普通手机用户可以完成送垃圾任务，且失败时有清晰、可信、可支持的证据链。

用户价值拆解：

- 对现场操作员：知道下一次上车路线-任务联跑前必须准备哪些材料、如何保持同一 `evidence_ref`、运行哪些命令、哪些证据仍然 `not_proven`。
- 对工程同学：把 PC route debug console / operator review / execution bundle 的软件证据组织成一个统一 readiness artifact，减少真实联跑时口径漂移。
- 对支持与手机用户：只看到 phone/support-safe 的 readiness availability 和 next evidence，不接触 raw artifact，也不会看到 delivery success 或控制授权误导。

## OKR 映射

### Objective 2：可送垃圾任务完整闭环

本轮支持 KR5“每次任务产出可复盘记录”。readiness handoff 必须要求下一次真实联跑围绕同一 `evidence_ref` 产出起止时间、目标、状态转换、失败原因、导航结果、检测快照引用或明确缺失项。

预计影响：若工程完整落地并通过验证，可作为 Objective 2 的保守软件准备进展，但不能替代真实送达、投放、取消或恢复实测。

### Objective 3：可验证导航与固定路线能力

本轮支持 KR3/KR5：把 fixed route software replay、PC route debug console、operator review、execution bundle 汇总成下一次真实 fixed-route / Nav2 现场联跑前的 readiness package。

预计影响：若工程完整落地并通过验证，可作为 Objective 3 的保守软件准备进展，但不能替代真实路线采集、Nav2/fixed-route 实跑或关键帧实景证据。

### Objective 5：云中转 + OSS/CDN 数据通路产品化

本轮不提升 Objective 5。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration，readiness artifact 也不应被 cloud readiness 消费为外部 proof。

## KR 拆解

1. Autonomy readiness artifact：
   - 生成 `schema=trashbot.route_task_field_run_readiness.v1`。
   - 输出 `evidence_boundary=software_proof_docker_route_task_field_run_readiness_gate`。
   - 汇总 PC route debug console summary、route_task operator review、execution bundle 或兼容 diagnostics summary。
   - 明确同一 `evidence_ref` 要求、缺失材料、可运行命令、next field-run checklist、`not_proven`、`delivery_success=false`、`hil_pass=false` 或等价未证明字段。

2. Robot diagnostics metadata-only：
   - 只读消费 readiness artifact。
   - 输出 phone/support-safe summary。
   - 不触发 collect/dropoff/cancel、ACK POST、cursor/persistence、Nav2、WAVE ROVER、HIL 或任何控制动作。

3. Mobile read-only panel：
   - 展示 route-task field-run readiness availability / next evidence。
   - 不读取 raw artifact，不展示本机路径、checksum、traceback、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 参数。
   - 不改变 Start/Confirm/Cancel gating，缺材料时 fail closed / `not_proven`。

4. Product closeout：
   - 工程完成后更新 sprint 收口文档、OKR 和进度日志。
   - Objective 2/3 只在证据充分时保守上调。
   - Objective 5 保持约 68%，不因本地 Docker readiness gate 上调。

## 范围边界

### 本轮必须做

- 建立 `route_task_field_run_readiness` artifact 和 diagnostics/mobile 只读消费路径。
- 明确真实路线-任务联跑前需要的同一 `evidence_ref` 材料。
- 明确可运行命令和缺失材料，不把缺失项藏在自然语言里。
- 更新相关 README、navigation docs、interface docs、mobile user flow docs。
- 用 targeted tests、py_compile、node check、required `rg`、scoped `git diff --check` 做验证围栏。

### 本轮不做

- 不接硬件、不改 WAVE ROVER、UART、Orange Pi、serial baudrate 或 launch 硬件参数。
- 不运行真实 Nav2/fixed-route、不宣称真实路线、HIL、真实串口、真实底盘运动、dropoff/cancel completion 或 delivery success。
- 不推进 Objective 5 外部 proof，不声明公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 已满足。
- 不改变手机 Start Delivery、Confirm Dropoff、Cancel 的授权逻辑。

## 优先级和验收口径

P0：

- `trashbot.route_task_field_run_readiness.v1` artifact 能从已有 PC route debug / operator review / execution bundle 类材料生成 readiness summary。
- 所有输出都包含 `software_proof_docker_route_task_field_run_readiness_gate`、`not_proven`、同一 `evidence_ref` 要求和 `delivery_success=false` 或等价禁止成功口径。
- diagnostics 和 mobile 消费路径均 metadata-only / read-only，不触发控制动作。

P1：

- 文档明确下一次真实联跑材料包应该包含哪些文件、命令、现场记录和复账要求。
- fixture / tests 覆盖缺材料、unsupported schema、unsafe copy、missing evidence 的 blocked/not_proven 降级。

验收失败条件：

- 任一界面或 summary 把 Docker/local readiness 描述成 HIL、真实 route run、delivery success、dropoff/cancel completion 或 O5 external proof。
- 任一实现读取 raw artifact 到 mobile，暴露本机路径、凭证、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 参数、traceback、checksum 或完整证据文件。
- 任一实现改变 Start/Confirm/Cancel gating 或触发控制动作。

## 责任 Engineer

- `autonomy-engineer`：Task A，readiness artifact 与 fixed-route/task handoff 文档。
- `robot-software-engineer`：Task B，diagnostics metadata-only 消费与 interface docs。
- `full-stack-software-engineer`：Task C，mobile read-only panel、fixture、entrypoint tests、product docs。
- `product-okr-owner`：Task D，阶段验收、OKR/progress/sprint docs 收口。

## 风险、阻塞和证据链

- 真实 route run / HIL / delivery success 仍需要真实硬件、真实串口、Nav2/fixed-route 实跑和现场复账材料。
- 本轮 readiness package 只是把下一次真实联跑的材料要求变成可执行清单；如果没有后续现场材料，OKR 只能保守小幅推进 O2/O3，不能关闭核心缺口。
- O5 的最低完成度是事实，但当前缺外部材料，Product closeout 必须再次确认 Objective 5 不提升。
