# Sprint 2026.05.15_04-05 Route Task Field Run Reconciliation - Pre Start

sprint_type: epic

## 1. 启动背景

当前 `OKR.md` 4.1 更新时间为 2026-05-15 02:44 Asia/Shanghai。Objective 2 和 Objective 3 均约 63%，低于 Objective 5 约 66%、Objective 1 / Objective 4 约 73%。

上一轮 `2026.05.15_03-04_route-task-field-run-execution-pack` 已完成 `software_proof_docker_route_task_field_run_execution_pack_gate`，生成现场材料模板、同一 `evidence_ref` 要求、first-run/rerun commands、diagnostics summary 和 mobile 只读 panel。

本轮目标是在 Docker-only 主机上继续推进 Objective 2 / Objective 3，从 execution pack 往前做成同一 `evidence_ref` 的现场材料复账 gate：`software_proof_docker_route_task_field_run_reconciliation_gate`。

## 2. 用户价值和产品北极星

用户价值：现场人员采回 route/task field-run 材料后，需要一份可复账 verdict，明确 execution pack、field-run intake/review 材料是否属于同一 `evidence_ref`，哪些材料缺失或不一致，下一步该重跑什么，而不是把多个 artifact 手工对照。

产品北极星：普通手机用户最终只需交付垃圾并看懂状态；工程侧必须先把 route/task 现场材料链从“可执行”推进到“可复账”，才能可靠判断一次送垃圾任务是否具备进入真实 Nav2/fixed-route、dropoff/cancel completion 和 delivery success 验收的条件。

## 3. 上轮未完成项和本轮继承风险

- 仍缺真实 Nav2/fixed-route 运行。
- 仍缺真实路线采集。
- 仍缺同一 `evidence_ref` 的上车复账。
- 仍缺 dropoff/cancel completion。
- 仍缺 delivery success。
- 仍缺 WAVE ROVER、真实串口/UART、HIL 或真实 `hil_pass`。
- Objective 5 仍需要真实外部材料：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；本机只有 Docker/local 软件环境，本轮不推进 Objective 5，也不继续堆本地 O5 metadata。

## 4. 本轮核心抓手

本轮抓手是 `software_proof_docker_route_task_field_run_reconciliation_gate`：

- 消费上一轮 execution pack JSON，以及 field-run intake/review 材料。
- 固化 `same_evidence_ref_required=true`，如果 execution pack、intake/review 材料的 `evidence_ref` 缺失或不一致，输出 blocked/not_proven。
- 输出 `reconciliation_verdict`，区分可人工复核、缺材料、证据 ref 不一致、schema/boundary 不支持和 unsafe summary。
- 输出 `materials_status`、`operator_next_steps`、`phone_safe_summary` 和 `not_proven`，供 PC、Robot diagnostics 和 mobile 只读面板消费。
- 固定 `delivery_success=false`、`primary_actions_enabled=false`；不证明真实 Nav2/fixed-route、真实路线采集、HIL、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 5. Sprint 类型和 Owner

本轮是 Epic sprint，因为它跨 Autonomy、Robot、Full-stack、Product 四个 owner，并新增一个完整现场复账能力模块。

- `autonomy-engineer`：主责 reconciliation CLI、测试、PC 工具文档和 fixed-route 工作流文档。
- `robot-software-engineer`：主责 diagnostics metadata-only 消费 reconciliation summary，不触发 collect/dropoff/cancel、ACK、cursor、terminal ACK、Nav2、HIL 或 delivery success。
- `full-stack-software-engineer`：主责 `mobile/web` 只读“路线任务现场复账”panel，不读取 raw artifact、本机路径或改变 Start/Confirm/Cancel gating。
- `product-okr-owner`：等 A/B/C 完成后主责 `OKR.md`、`docs/process/okr_progress_log.md` 和 sprint closeout。

## 6. Blocker 重复消费核对

最近两轮主要剩余风险均指向真实 Nav2/fixed-route、真实路线采集、同一 `evidence_ref` 上车复账、HIL、dropoff/cancel completion、delivery success 和 Objective 5 external proof。

本轮不把这些缺口包装成已解决，也不重复消费 Objective 5 外部材料 blocker。它只把 O2/O3 的现场执行材料推进到 Docker/local 可复账 verdict，帮助下一轮真实现场人员按同一 `evidence_ref` 补齐或重跑材料。

## 7. 本阶段边界

本阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。不修改产品代码、测试代码、硬件配置或 `OKR.md`。完成度更新必须等实现、验证、`tech-done.md`、`side2side_check.md` 和 `final.md` 收口后再处理。
