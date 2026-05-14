# Sprint 2026.05.15_05-06 Route Task Completion Signal - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动 fresh Epic sprint：`2026.05.15_05-06_route-task-completion-signal`。

核心抓手是 `software_proof_docker_route_task_completion_signal_gate`。本轮不继续做 O5 本地 metadata depth，而是针对 live `OKR.md` 4.1 中最低的 Objective 2 与 Objective 3，把上一轮 reconciliation verdict 推进到 Docker/local route/task chain 可生成的 completion signal 软件证据。

## 2. 读取依据

- `AGENTS.md`：Epic sprint 需要完整 planning 链路，2+ owner 需并行派发，主节点不得写产品代码、测试代码或硬件配置。
- `OKR.md`：2026-05-15 03:19 快照显示 Objective 2 与 Objective 3 均约 64%，是当前最低；Objective 5 约 66%，但下一步依赖真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料。
- `sprints/2026.05.15_04-05_route-task-field-run-reconciliation/final.md`：上一轮完成 `software_proof_docker_route_task_field_run_reconciliation_gate`，下一轮应从 reconciliation verdict 进入真实/可执行路线任务材料，尤其 dropoff/cancel completion、same evidence_ref、真实 Nav2/fixed-route 或现场复账。
- `docs/product/mobile_user_flow.md`：mobile/web 已有路线任务现场复账只读 panel，Start/Confirm/Cancel 继续 fail closed，所有现场材料类 panel 必须保留 `delivery_success=false`、`not_proven` 和 phone-safe whitelist。
- `docs/process/iteration_velocity.md`：本轮跨 Autonomy、Robot、Full-stack 三 owner，属于 Epic；`tech-plan.md` 必须包含 OKR 最低优先级核对。

## 3. 上轮未完成项

- Objective 2 仍缺真实送达任务闭环：真实 Nav2/fixed-route 运行、dropoff completion、cancel completion、失败恢复实测、同一 `evidence_ref` 的上车实机复账和 delivery success。
- Objective 3 仍缺真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据、WAVE ROVER/HIL 和同一 `evidence_ref` 上车复账。
- Objective 5 仍缺真实外部材料；本 Docker-only 主机不适合继续用本地 metadata 证明公网、4G、OSS/CDN 或 production DB/queue。

## 4. 本轮目标

把 reconciliation verdict 之后的下一层软件能力定义清楚：同一 `evidence_ref` 下汇总 fixed-route status/replay、task record state transitions、dropoff/cancel completion flags、failure/recovery reason，并输出 completion verdict 给 diagnostics 与 mobile 只读消费。

本轮默认证据边界：

- `evidence_boundary=software_proof_docker_route_task_completion_signal_gate`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `not_proven` 必须包含真实送达、真实 dropoff/cancel completion、真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、真实手机设备和 Objective 5 external proof。

## 5. Owner 与并行策略

- Autonomy：主责 PC/evidence completion-signal CLI、样例/测试围栏、`docs/navigation/` 路线任务完成信号口径。
- Robot：主责 diagnostics metadata-only consumption、operator gateway diagnostics 测试围栏、`docs/interfaces/` 契约同步。
- Full-stack：主责 `mobile/web` 只读 completion panel、phone-safe whitelist、`docs/product/` 用户流程同步。

三条线文件范围互不重叠，接口通过 `trashbot.route_task_completion_signal.v1` 与 `software_proof_docker_route_task_completion_signal_gate` 对齐；实现阶段必须并行派发 3 个 worker。

## 6. Blocker 扫描

最近两轮 sprint：

- `2026.05.15_03-04_route-task-field-run-execution-pack/final.md`：主结论不是 blocked；证据边界是 execution pack software proof，未证明真实 Nav2/fixed-route、dropoff/cancel completion 或 delivery success。
- `2026.05.15_04-05_route-task-field-run-reconciliation/final.md`：主结论不是 blocked；明确 O5 外部材料仍缺失，但本轮针对最低 O2/O3 的 Docker/local 软件复账层推进。

结论：本轮不是第三次消费同一 O5 外部 blocker；本轮从 O2/O3 的上一层 reconciliation 继续推进到 completion signal 软件证据。

## 7. 非目标

- 不修改硬件、WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 底盘协议或机械尺寸。
- 不宣称真实送达、真实投放、真实 cancel completed、真实 Nav2/fixed-route、HIL、真实串口或 Objective 5 external proof。
- 不放行 Start Delivery、Confirm Dropoff 或 Cancel；mobile/web 只做只读 completion panel。
- 不把 ACK、HTTP accepted、route/task artifact pass、diagnostics summary 或 mobile panel 写成 delivery success。

