# Sprint 2026.05.16_22-23 Route Task Field Retest Result Intake - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：现场复测结束后，团队需要一个能接收“结果材料”的入口，而不是继续停在 handoff checklist。该入口必须告诉现场同学：哪些真实材料已经按同一 `evidence_ref` 回填，哪些材料缺失或不可信，为什么当前仍是 `not_proven`，以及哪些信息可以安全展示给手机用户和支持同学。

产品北极星：把 `rober` 做成普通手机用户能理解、现场支持能复测、证据链能复盘的低成本 ROS2 自主垃圾投递机器人。本轮只推进 Objective 2 / Objective 3 的现场复测结果 intake readiness，不把 Docker software proof 包装成真实 field pass。

## 2. 问题背景

上一轮 `route_task_field_retest_session_handoff` 已把 execution pack 转成现场交接材料，但 `final.md` 明确仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result。

如果没有 result intake contract，现场回填后会出现三类断裂：

- 不同材料没有沿用同一 `evidence_ref`，导致 PC artifact、Robot diagnostics、mobile/web 和 OKR closeout 不能对账。
- 只上传了 summary 或 wrapper，缺关键八类结果材料，仍被误读为 field pass。
- 手机端或 diagnostics 把“材料入口已生成”写成真实送达、真实 route/elevator execution、dropoff/cancel completion 或 delivery success。

## 3. OKR 映射

- Objective 2：将送垃圾任务 + 电梯 assisted delivery 的现场复测结果材料拆成同一 `evidence_ref` 的 result intake，覆盖 task record、door_state、target_floor_confirmation、human_assistance_note、dropoff/cancel completion、delivery_result。
- Objective 3：将固定路线与 Nav2 的现场复测结果材料拆成 runtime log、route completion signal、route/task evidence bundle 和 intake verdict。
- Objective 4：为普通手机用户和现场支持提供只读、中文优先、phone-safe 的“现场复测结果入口”说明，不改变主操作授权。
- Objective 5：保持约 66%，不推进。缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 时，Docker-only planning 或 metadata wrapper 不能提升 Objective 5。

## 4. KR 拆解或更新

本轮不新增 OKR/KR 文本，只把 Objective 2 / Objective 3 现有 KR 的下一步证据链具体化：

- O2 KR4 / KR5 / KR6 / KR7：result intake 必须检查任务结果、失败原因、task record、门状态、目标楼层确认、人工协助记录、人工接管原因、投放/取消完成材料和同一 `evidence_ref` 回填口径。
- O3 KR2 / KR3 / KR4 / KR5：result intake 必须检查 fixed-route/Nav2 runtime log、route completion signal、PC 调试/复测材料、result bundle 和重跑摘要。
- O4 KR1 / KR5 / KR6 / KR7：mobile/web 只读 panel 必须普通用户可理解，不暴露 raw ROS topic、raw JSON、硬件细节或控制成功文案。

## 5. 本轮核心抓手

核心抓手是 `route_task_field_retest_result_intake`：

- 上游输入：`route_task_field_retest_session_handoff` 之后产生或回填的 artifact / summary / wrapper / nested JSON。
- PC 输出：`trashbot.route_task_field_retest_result_intake.v1` artifact 与 phone-safe summary。
- Robot 输出：diagnostics metadata-only consumer，缺失或不安全时 fail closed。
- Mobile 输出：只读“路线任务现场复测结果入口” panel 与 fixture/test，copy/export whitelist-only。
- Product 输出：closeout 文档、OKR 保守进度、过程日志。

统一证据边界：

- `software_proof_docker_route_task_field_retest_result_intake_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 6. 八类结果材料摘要

result intake 必须检查并摘要以下八类材料；缺失任一类都不得宣称 field pass：

1. `nav2_or_fixed_route_runtime_log`
2. `route_completion_signal`
3. `task_record`
4. `door_state`
5. `target_floor_confirmation`
6. `human_assistance_note`
7. `dropoff_or_cancel_completion`
8. `delivery_result`

## 7. 范围内

- Task A Autonomy：创建 `pc-tools/evidence/route_task_field_retest_result_intake.py` 和测试，更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`。
- Task B Robot：更新 diagnostics consumer 和 tests，更新 `docs/interfaces/ros_contracts.md`。
- Task C Full-stack：更新 `mobile/web` panel、fixture/test 和 `docs/product/mobile_user_flow.md`。
- Task D Product closeout：更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 8. 范围外

- 不证明真实 Nav2/fixed-route execution 已通过。
- 不证明真实 route completion signal 或真实 task record 已产生。
- 不证明真实电梯 door_state、target_floor_confirmation、human_assistance_note 已采集。
- 不证明真实 dropoff/cancel completion、delivery_result 或 delivery success。
- 不证明真实 WAVE ROVER/UART/HIL、真实手机/browser、production app、Objective 5 external proof。
- 不新增 Objective 5 本地 metadata wrapper。
- 不继续第三轮消费 PR #5 硬件/source/config blocker。

## 9. 优先级和验收口径

P0：所有输出必须 fail closed，并保留 `software_proof_docker_route_task_field_retest_result_intake_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

P0：PC artifact / summary 必须支持 artifact / summary / wrapper / nested JSON 输入，要求 same `evidence_ref`，并检查八类结果材料摘要。

P0：Robot diagnostics 只能 metadata-only 消费，不能启用 primary actions，不能把 summary 解释成真实通过。

P0：mobile/web panel 只读、phone-safe、copy/export whitelist-only，Start / Confirm Dropoff / Cancel gating 不变。

P1：Product closeout 必须保守同步 OKR；若没有真实外部材料，Objective 5 不上调；若没有完整真实 field materials，O2/O3 最多记录 result intake readiness，不宣称 field pass。

P1：测试只做围栏：py_compile、focused unittest、node --check、required rg、scoped git diff check。

## 10. 对应责任 Engineer

- Autonomy Algorithm Engineer 负责 Task A。
- Robot Platform Engineer 负责 Task B。
- User Touchpoint Full-Stack Engineer 负责 Task C。
- Product Manager / OKR Owner 负责 Task D。

## 11. 风险、阻塞和需要补齐的证据链

- Docker-only 阻塞：本轮不能产生真实 HIL、真实固定路线、真实电梯或真实手机/browser field evidence。
- Objective 5 阻塞：缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- PR #5 硬件 blocker 红线：最近两轮已消费硬件/source/config blocker，本轮不能继续做同一根因 wrapper。
- PR #4 主线要求：电梯 assisted delivery 已是必须能力，因此 result intake 不能漏掉 door_state、target_floor_confirmation、human_assistance_note。
- 证据链缺口：下一次现场必须补同一 `evidence_ref` 的真实 Nav2/fixed-route runtime log、route completion signal、task record、真实门状态、真实楼层确认、人工协助记录、dropoff/cancel completion 和 delivery_result。

## 12. 需要创建或更新的 sprint 文档

本轮 planning 已创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现后 Task D 必须继续创建或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
