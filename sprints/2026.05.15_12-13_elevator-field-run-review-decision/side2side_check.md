# Sprint 2026.05.15_12-13 Elevator Field Run Review Decision - Side2Side Check

sprint_type: epic

## 1. 用户价值和产品北极星

产品北极星仍是：普通手机用户把垃圾交给小车后，小车能沿固定路线完成可复盘、可恢复、可解释的送垃圾任务；跨楼层场景中，电梯 assisted delivery 必须能把“需要人工协助”和“仍未证明真实送达”的边界讲清楚。

本轮用户价值不是让小车真的进电梯，而是让现场同学拿到上一轮材料校验结果后，可以直接看到复核决策、缺口分类、复跑命令和采集清单，避免把 raw JSON、模板材料或 unsafe copy 误读成现场完成。

## 2. OKR 映射

- Objective 2：推进 KR6/KR7 的电梯 assisted delivery 复核链，把缺材料、模板未替换、同一 `evidence_ref` 不一致、unsafe copy 和越界成功声明转成现场下一步。
- Objective 3：继续要求 Nav2/fixed-route runtime log 与 task record、completion signal、diagnostics/mobile summary 使用同一 `evidence_ref`，但仍只停留在 review decision software proof。
- Objective 5：不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration；not real O5 external proof。

## 3. KR 拆解或更新

- O2 KR6/KR7：新增 `elevator_field_run_review` 决策层后，现场材料链从 validation artifact 推进到人工复核/复跑指令，因此 O2 可从约 71% 保守上调到约 72%。
- O3 KR2/KR3/KR4/KR5：review decision 保留 Nav2/fixed-route runtime log 的 same `evidence_ref` 要求和复跑清单，因此 O3 可从约 70% 保守上调到约 71%。
- O5 KR1-KR6：无真实外部材料，不上调，保持约 66%。

## 4. 本轮核心抓手

核心抓手是 `software_proof_docker_elevator_field_review_decision_gate`：

- Autonomy 生成 review artifact 和 summary。
- Robot diagnostics metadata-only 暴露 review summary。
- Mobile 只读 panel 展示复核决策和复跑动作。
- Product closeout 只按 software proof 更新 O2/O3，不把它写成真实送达或 O5 external proof。

## 5. 需要做什么

已完成：

- 将工程线结果汇总到 `tech-done.md`。
- 将验收对照和产品边界写入本文件。
- 将阶段复盘和 OKR 影响写入 `final.md`。
- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。

下一步需要现场材料，而不是继续叠本地 gate：

- 真实电梯门状态、真实楼层确认、真实人工协助记录。
- 真实 Nav2/fixed-route runtime log、真实 task record、真实 completion signal。
- 同一 `evidence_ref` 的 WAVE ROVER/UART/HIL 或上车实机复账。

## 6. 优先级和验收口径

验收通过口径：

- 三条工程线均返回 focused tests、`py_compile`、required `rg` 和 scoped `git diff --check` 通过。
- Closeout 文件、`OKR.md`、`docs/process/okr_progress_log.md` 均包含 `elevator_field_run_review`、`software_proof_docker_elevator_field_review_decision_gate`、`delivery_success=false`、`不证明` 或 `not real` 边界。
- Objective 5 保持约 66%，不因本轮 Docker/local software proof 上调。

验收不通过口径：

- 任何文档把 review decision 写成真实电梯、真实楼层确认、真实人协助、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion、delivery success、真实手机/browser 或 Objective 5 external proof。

## 7. 对应责任 Engineer

- `autonomy-engineer`：PC review decision CLI/schema/test/docs。
- `robot-software-engineer`：diagnostics metadata-only consumption。
- `full-stack-software-engineer`：mobile/web 只读 panel、fixture/test/docs。
- `product-okr-owner`：sprint closeout、OKR 和 progress log。

## 8. 风险、阻塞和证据链

- 风险：review decision 可指导复跑，但仍不能替代真实现场材料。
- 阻塞：本机没有真实硬件、真实电梯、真实公网、4G/SIM、OSS/CDN live traffic 或 production DB/queue。
- 证据链缺口：真实电梯、真实楼层确认、真实人工协助、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion、delivery success、真实手机/browser 和 Objective 5 external proof。

## 9. 需要创建或更新的 sprint 文档

- 已创建 `tech-done.md`。
- 已创建 `side2side_check.md`。
- 已创建 `final.md`。
- 已更新 `OKR.md`。
- 已更新 `docs/process/okr_progress_log.md`。
