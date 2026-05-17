# Sprint 2026.05.18_07-08 Route Task Material Review Operator Drill - PRD

sprint_type: epic

## 1. 用户价值

上一轮已经把 route/elevator 现场材料回执推进到 `route_task_field_retest_material_callback_review_decision`。如果 operator drill 仍只从旧 material pack 生成，现场执行会绕开最新复核结论，导致 accepted / missing / rejected materials、owner acknowledgement 和 next required evidence 在 drill 阶段丢失。

本轮要让 `route_task_field_retest_operator_drill` 消费上一轮 review decision artifact / summary / wrapper / nested diagnostics，把复核决策翻译成现场 operator 能执行的下一步命令、回执 checklist、rerun notes 和 phone-safe summary。它服务“普通用户交垃圾后，小车沿固定路线、必要时借助电梯完成可靠投递”的证据链，但仍是 Docker/local software proof。

## 2. 产品北极星

北极星不是让本机 Docker 证明真实送达，而是让每一步现场材料都能被同一 `evidence_ref` 复账：现场缺什么、谁补、下一次怎么跑、手机端能安全显示什么，都必须可追踪、可回放、可 fail closed。

本轮核心抓手是：从 `route_task_field_retest_material_callback_review_decision` 进入 operator drill，而不是回退到 material pack-only drill。

## 3. OKR 映射

- Objective 2：补强 route/elevator assisted delivery 的现场执行链，把 review decision 接入 operator drill；仍不证明真实送达、电梯通过、dropoff/cancel completion 或 delivery success。
- Objective 3：让 Nav2/fixed-route runtime log、route completion signal、task record 等现场材料的 review decision 能转成下一步 drill；仍不证明真实路线实跑。
- Objective 4：验证或小补 mobile/web first-screen 只读展示，帮助非工程用户理解下一步现场操作；仍不证明真实手机设备、真实 browser 或 production app。
- Objective 1：不推进；没有真实 WAVE ROVER/UART/HIL 材料，PR #5 硬件 source 风险仍保留。
- Objective 5：不推进；没有真实外部云/4G/OSS/CDN/DB/queue/worker/cutover 材料，Objective 5 约 68% 的 stop rule 继续成立。

## 4. KR 拆解

KR-A / Autonomy：

- `route_task_field_retest_operator_drill` 支持 `route_task_field_retest_material_callback_review_decision` artifact / summary / wrapper / nested diagnostics 输入。
- 输出 schema 不变：`trashbot.route_task_field_retest_operator_drill.v1` 和 `trashbot.route_task_field_retest_operator_drill_summary.v1`。
- 输出 boundary 不变：`software_proof_docker_route_task_field_retest_operator_drill_gate`。

KR-B / Robot：

- diagnostics contract 能消费或保留 operator drill summary，并确认从 review decision 来源生成的 summary 不会启用控制语义。
- 兼容 alias 保持 metadata-only：`route_task_field_retest_operator_drill`、`route_task_field_retest_operator_drill_summary`、`robot_diagnostics_route_task_field_retest_operator_drill_summary`。

KR-C / Full-stack：

- mobile/web first-screen panel 能只读展示 operator drill summary，并确认 material callback review decision 在 panel 顺序和 copy/export 中不被绕过。
- Start Delivery、Confirm Dropoff、Cancel、dispatch、callback、ACK、cursor、robot command gating 不因 summary 存在而改变。

KR-D / Product：

- 工程完成后更新 `OKR.md`、`docs/process/okr_progress_log.md` 和本 sprint `tech-done.md` / `side2side_check.md` / `final.md`。
- 收口语言必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 优先级和验收口径

P0：

- PC gate 真实支持 review decision 输入链路，且 focused test 覆盖 artifact、summary、wrapper、nested diagnostics。
- 不接受 unsupported schema、bad boundary、weak evidence_ref、same evidence_ref mismatch、unsafe raw path、credentials、success claim、`delivery_success=true` 或 `primary_actions_enabled=true`。

P1：

- Robot diagnostics 与 mobile/web 验证现有 summary 支持；如缺字段或顺序问题，做最小补充。
- 文档同步更新到 `docs/interfaces/evidence_contracts.md`、`docs/interfaces/ros_contracts.md`、`docs/product/mobile_user_flow.md`。

P2：

- Product closeout 更新 OKR / progress / sprint docs，并明确没有新增 Objective 5 external proof 或 Objective 1 real HIL proof。

验收失败条件：

- 把 operator drill 写成 real route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。
- 因 `route_task_field_retest_operator_drill` 存在而启用 Start / Confirm / Cancel / dispatch / callback / ACK / cursor / robot command。
- 回退到只消费 material pack，而没有消费 `route_task_field_retest_material_callback_review_decision`。

## 6. 对应责任 Engineer

- A / Autonomy Algorithm Engineer：PC gate、focused tests、evidence contract docs。
- B / Robot Platform Engineer：diagnostics contract 验证或小补、ROS contract docs。
- C / User Touchpoint Full-Stack Engineer：mobile/web first-screen panel 验证或小补、mobile flow docs。
- Product Manager / OKR Owner：工程完成后的 OKR 和 sprint closeout。

## 7. 风险、阻塞和证据链

当前阻塞仍是外部证据和真实硬件证据不可得：Objective 5 缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover；Objective 1 缺真实 WAVE ROVER/UART/HIL。

本轮证据链只能证明本地 Docker software proof：`route_task_field_retest_material_callback_review_decision` 可以进入 `route_task_field_retest_operator_drill`，并被 diagnostics/mobile 只读消费。真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record/completion signal、真实 dropoff/cancel completion、delivery success、HIL、真实手机/browser 和 O5 external proof 都留到后续真实材料回填。
