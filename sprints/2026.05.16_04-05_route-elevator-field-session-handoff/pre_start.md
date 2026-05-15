# Sprint 2026.05.16_04-05 Route Elevator Field Session Handoff - Pre Start

sprint_type: epic

## 1. 本轮启动判断

本轮目标是新增 `route_elevator_field_session_handoff`，把上一轮 PC route debug console 与 nested elevator-route reconciliation 的软件 proof，整理成现场同学可执行、Robot diagnostics 可只读消费、mobile/web 可只读展示的 field-session handoff artifact/summary。

产品北极星保持不变：让普通手机用户把垃圾交给小车后，小车沿固定路线跨电梯 assisted delivery 完成投递，并且每次现场运行都有同一 `evidence_ref` 的可复盘证据链，而不是把本机 console summary 写成真实送达。

## 2. 为什么本轮不继续 O5 本地 metadata

当前 `OKR.md` 4.1 显示 Objective 5 约 66%，是数字最低 Objective；但 `OKR.md` 第 6 节明确写明：只有拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据时，才应继续推进 O5 completion。当前本机仍只有 Docker/local software proof，继续堆本地 O5 metadata 会重复消费同一 blocker。

上一轮 `sprints/2026.05.16_03-04_pc-route-elevator-console-integration/final.md` 的结论也已经把下一步指向 O2/O3 的现场/上车复账链路：Nav2/fixed-route runtime log、route completion signal、task record、真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 和 delivery result。

因此本轮选择 Objective 2 + Objective 3 的 route/elevator field-session handoff，而不是继续 Objective 5 本地 metadata。

## 3. 最近证据输入

- `aeed84e Add PC route elevator console integration`：已完成 `software_proof_docker_pc_route_elevator_console_integration_gate`，PC console、Robot diagnostics、mobile 面板可以展示 nested route/elevator reconciliation。
- `25a6883 Add elevator route evidence reconciliation gate`：已把 elevator rehearsal evidence 与 route completion signal 对齐到同一 `evidence_ref`，但仍是 Docker/local software proof。
- `85a7c21 Add elevator evidence-driven mainline gate`：已能生成 evidence-driven elevator rehearsal 主链路输入，但不证明真实电梯门、楼层或路线运行。
- `b52df55 Add elevator rehearsal execution pack gate`：已能整理受控电梯演练执行包，但仍缺真实现场材料回填。

反复出现的问题是：同一 `evidence_ref` 的现场材料仍未落地，软件 proof 不能写成真实送达、真实 Nav2/fixed-route、真实电梯或 HIL。

## 4. 本轮核心抓手

把“PC console 已经能看 route + elevator reconciliation”推进成“现场 session 前后都能交接和回填”的 handoff gate：

- Autonomy Task A：新增 `route_elevator_field_session_handoff` CLI/schema/test/docs，汇总 PC route debug console、route completion signal、elevator-route reconciliation、现场材料清单和 operator handoff。
- Robot Task B：Robot diagnostics metadata-only 消费 handoff summary，继续 fail-closed，不启用控制、ACK、Nav2、dropoff/cancel 或 success claim。
- Full-stack Task C：mobile/web 只读展示 handoff summary，Start / Confirm Dropoff / Cancel 继续 fail-closed。
- Product Closeout：验收后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 5. Owner 和交付边界

- 主责 owner：Autonomy Algorithm Engineer，负责新 CLI/schema/test/docs，并定义 handoff artifact/summary 的唯一可信来源。
- 协作 owner：Robot Platform Engineer，负责 diagnostics metadata-only 消费。
- 协作 owner：User Touchpoint Full-Stack Engineer，负责 mobile/web 只读展示。
- Product Manager / OKR Owner：负责本轮阶段验收、OKR 边界、收口文档和进度日志。

Hardware Infra Engineer 本轮不介入；本轮不新增 WAVE ROVER、Orange Pi、UART、波特率、引脚、电压、机械尺寸或真实硬件配置假设。

## 6. 预期证据边界

本轮最多产出 `software_proof_docker_route_elevator_field_session_handoff_gate`。

它只证明 Docker/local handoff artifact/summary 可以把 PC route debug console、route completion signal、elevator-route reconciliation 和现场回填清单整理成同一 `evidence_ref` 的安全交接材料；不证明真实 Nav2/fixed-route、真实路线采集、真实电梯门状态、真实目标楼层确认、真实人工协助、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion、真实 delivery result、真实手机设备/browser 或 Objective 5 external proof。

## 7. 需要创建或更新的 sprint 文档

本轮启动时创建：

- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/pre_start.md`
- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/prd.md`
- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/tech-plan.md`

工程验收后必须继续更新：

- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/tech-done.md`
- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/side2side_check.md`
- `sprints/2026.05.16_04-05_route-elevator-field-session-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
