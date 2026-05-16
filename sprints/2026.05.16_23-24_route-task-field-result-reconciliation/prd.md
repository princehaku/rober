# Sprint 2026.05.16_23-24 Route Task Field Result Reconciliation - PRD

sprint_type: epic

## 1. 背景

上一轮 `route_task_field_retest_result_intake` 已把现场复测结果材料做成可回填入口，但入口不等于现场通过。当前最关键的产品缺口是：同一 `evidence_ref` 下，execution pack、session handoff、result intake 和八类现场结果材料之间是否一致、缺什么、哪里 mismatch、下一步该由谁补证据。

Objective 5 仍是数值最低约 66%，但当前主机 Docker-only，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。本轮不继续堆本地 O5 metadata wrapper，转向 Objective 2 / Objective 3 的 field result reconciliation。

## 2. 用户价值和产品北极星

用户价值：

- 现场同学能知道同一 `evidence_ref` 下哪些真实材料缺失或互相矛盾。
- 支持同学能通过 PC / Robot diagnostics / mobile/web 看到同一份 fail-closed 摘要，不需要打开 raw artifacts。
- 普通手机用户不会看到“成功”“已送达”这类越界结论，只会看到当前仍是 `not_proven`、还缺哪些现场材料、下一步由谁补齐。

产品北极星：让 `rober` 从一次性 demo 继续走向可复盘、可验收、可安全解释的低成本 ROS2 自主垃圾投递机器人。本轮只推进证据链一致性，不把 software proof 包装成真实送达。

## 3. OKR 映射

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。本轮对 `door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion`、`delivery_result` 做同一 `evidence_ref` 复账，服务于真实任务闭环证据补齐。
- Objective 3：可验证导航与固定路线能力。本轮对 `nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record` 做同一 `evidence_ref` 复账，服务于真实 Nav2/fixed-route 材料回填。
- Objective 4：手机用户体验与低成本量产边界。本轮只读 panel 让手机端能解释现场结果复账状态，但不改变主操作授权，不证明真实手机/browser。
- Objective 5：云中转 + OSS/CDN 数据通路产品化。本轮不直接推进；缺真实外部云/4G/OSS/CDN/DB/queue/worker 证据时保持不提升。

## 4. KR 拆解或更新

本轮不改写 `OKR.md` 的 KR 文案，只拆成执行抓手：

- KR-A：PC-side reconciliation artifact 能检查 result intake / session handoff / execution pack 与八类现场结果材料的同一 `evidence_ref`、schema/boundary、missing/mismatch 和 unsafe success claims。
- KR-B：Robot diagnostics 只能消费 sanitized summary，并将缺失、mismatch 或越界声明展示为 blocked/not_proven。
- KR-C：mobile/web 只读 panel 能展示复账 verdict、safe `evidence_ref`、八类材料状态、operator next steps、safe copy 和边界；主操作按钮 gating 不变。
- KR-D：Product closeout 保守更新 sprint / OKR / process log，明确本轮是 `software_proof_docker_route_task_field_retest_result_reconciliation_gate`。

## 5. 本轮核心抓手

核心抓手：`route_task_field_retest_result_reconciliation`。

该抓手不要求真实硬件、不要求真实手机、不访问 ROS graph，不读 serial/UART，不碰云端外部服务。它只把已有 software-proof 摘要和未来现场回填材料做一致性复账，并把结论收敛成 PC artifact、Robot diagnostics metadata-only summary 和 mobile/web 只读 panel。

## 6. 范围

### In Scope

- 新增 PC reconciliation contract、CLI、focused tests 和 PC 文档同步。
- Robot diagnostics 增加 metadata-only summary consumer。
- mobile/web 增加只读 panel、fixture/test 和 `docs/product/mobile_user_flow.md` 同步。
- sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md` 保守同步。

### Out of Scope

- 不做真实 Nav2/fixed-route 实跑。
- 不做真实电梯验收。
- 不做真实手机/iPhone/Android/browser 证明。
- 不做 WAVE ROVER、UART、ESP32、Orange Pi、2D LiDAR、ToF、引脚、电压、波特率、固件或机械安装改动。
- 不做 Objective 5 的公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- 不改变 Start Delivery、Confirm Dropoff、Cancel 授权语义。

## 7. 验收口径

本轮通过的定义：

- 所有新增输出都包含 `software_proof_docker_route_task_field_retest_result_reconciliation_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 八类现场结果材料均有明确状态：present、missing、mismatch、placeholder 或 unsafe。
- 同一 `evidence_ref` 不成立时必须 blocked，不能降级为 warning。
- PC / Robot / mobile 三端摘要字段一致，且均不暴露 raw artifact、raw JSON、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 参数、credentials、DB/queue URLs、OSS AK/SK、local paths、tracebacks、checksums 或完整 artifacts。
- mobile/web 不新增控制动作，不改变 existing Start / Confirm Dropoff / Cancel gating。
- Product closeout 不把本轮写成 field pass、HIL、真实手机/browser 或 Objective 5 external proof。

## 8. 对应责任 Engineer

- Autonomy Algorithm Engineer：PC reconciliation gate、CLI、unit tests、PC/fixed-route 文档同步。
- Robot Platform Engineer：operator diagnostics metadata-only consumer、tests、ROS contract 文档同步。
- User Touchpoint Full-Stack Engineer：mobile/web 只读 panel、fixture/tests、mobile user flow 文档同步。
- Product Manager / OKR Owner：sprint closeout、OKR 保守同步、process log 同步和最终验收。

## 9. 风险、阻塞和需要补齐的证据链

- 当前仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- 当前仍缺真实电梯、真实路线采集、真实 WAVE ROVER/UART/HIL、真实手机/browser 和 Objective 5 external proof。
- PR #4 的电梯 assisted delivery 主线要求仍需真实现场材料才能进入受控验收。
- PR #5 的硬件基线、2D LiDAR、ToF 和 vendor/source 风险未消失；只是本轮因 blocker 红线不继续消费。

## 10. 需要创建或更新的 sprint 文档

本 PRD 对应启动阶段三份文档：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现完成后，Product closeout 必须继续补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
