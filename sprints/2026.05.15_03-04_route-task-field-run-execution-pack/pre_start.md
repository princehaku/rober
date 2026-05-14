# Sprint 2026.05.15_03-04 Route Task Field Run Execution Pack - Pre Start

sprint_type: epic

## 1. 启动背景

当前 `OKR.md` 4.1 更新时间为 2026-05-15 02:14 Asia/Shanghai。Objective 2 和 Objective 3 均约 62%，低于 Objective 5 约 66%、Objective 1 / Objective 4 约 73%。

上一轮 `2026.05.15_02-03_route-task-field-run-review-console` 已完成 `software_proof_docker_route_task_field_run_review_console_gate`，把 field-run intake/crosscheck 变成 operator/support 可读的 review console、Robot diagnostics metadata-only summary 和 mobile 只读复核 panel。

本轮目标是在 Docker-only 主机上继续推进 Objective 2 / Objective 3，从 review console 往前做成可交给现场人员执行的现场联跑执行包：`software_proof_docker_route_task_field_run_execution_pack_gate`。

## 2. 用户价值和产品北极星

用户价值：现场人员拿到一份可执行 manifest、材料模板、命令清单、重跑清单和 phone-safe summary，不需要临时拼 route status、task record、runtime log、robot-side task evidence 和 mobile summary 的采集要求。

产品北极星：普通手机用户最终只需交付垃圾和看懂状态；工程侧必须先把 route/task 现场联跑材料链做成可重复、可复账、可解释的执行包，才能从软件复盘走向真实路线任务验证。

## 3. 上轮未完成项和本轮继承风险

- 仍缺真实 Nav2/fixed-route 运行。
- 仍缺真实路线采集。
- 仍缺同一 `evidence_ref` 的上车复账。
- 仍缺 dropoff/cancel completion。
- 仍缺 delivery success。
- 仍缺 WAVE ROVER、真实串口/UART、HIL 或真实 `hil_pass`。
- Objective 5 仍需要真实外部材料：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration；本机只有 Docker/local 软件环境，本轮不推进 O5。

## 4. 本轮核心抓手

本轮抓手是 `software_proof_docker_route_task_field_run_execution_pack_gate`：

- 从 review console 输出继续整理为现场联跑 execution pack manifest。
- 明确 required materials：route status、task record、Nav2/fixed-route runtime log、robot-side task evidence、support-safe mobile summary、上一轮 review console。
- 固化同一 `evidence_ref` 要求，任何材料缺失或 ref 不一致都进入 blocked/not_proven。
- 输出现场命令清单与重跑清单，区分 first-run commands 和 rerun commands。
- 输出 phone-safe summary，供 diagnostics/mobile 只读展示，不放行 Start/Confirm/Cancel。
- 固定 `not_proven` 边界：不证明 HIL、真实 Nav2/fixed-route、真实路线采集、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 5. Sprint 类型和 Owner

本轮是 Epic sprint，因为它跨 Autonomy、Robot、Full-stack、Product 四个 owner，并新增一个完整现场执行包能力模块。

- `autonomy-engineer`：主责 execution pack artifact、材料模板、命令清单和 sample drill。
- `robot-software-engineer`：主责 diagnostics metadata-only summary，不触发 collect/dropoff/cancel、ACK、cursor、HIL 或 delivery success。
- `full-stack-software-engineer`：主责 mobile/web 只读 phone-safe summary，不改变控制 gating。
- `product-okr-owner`：主责 sprint closeout、OKR 口径、`docs/process/okr_progress_log.md` 和验收边界。

## 6. Blocker 重复消费核对

最近两轮主要剩余风险均指向真实 Nav2/fixed-route、真实路线采集、同一 `evidence_ref` 上车复账、HIL、dropoff/cancel completion、delivery success 和 Objective 5 external proof。

本轮不把这些缺口包装成已解决，也不重复消费 Objective 5 外部材料 blocker。它只把 O2/O3 的下一次现场联跑执行材料做成可交付执行包，帮助下一轮真实现场人员采集材料。

## 7. 本阶段边界

本阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。不修改产品代码、测试代码、硬件配置或 `OKR.md`。完成度更新必须等实现、验证、`tech-done.md`、`side2side_check.md` 和 `final.md` 收口后再处理。
