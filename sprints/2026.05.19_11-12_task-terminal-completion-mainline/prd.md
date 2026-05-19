# Sprint 2026.05.19_11-12 Task Terminal Completion Mainline - PRD

## 1. 用户价值和产品北极星

本轮产品目标是把 dropoff / cancel terminal action 从“只读材料、回执或 review handoff”升级为 `task_terminal_completion_mainline`：Robot task_record、diagnostics 和 mobile web 都能在同一 safe `evidence_ref` 下解释 terminal action 的状态、用户确认语义、失败原因和下一步证据要求。

面向用户和现场 owner 的价值：

- 手机端能看懂 terminal action 是“待确认、已收到软件证明、缺真实材料、需要人工复核”，而不是把 ACK 或材料通过误认为真实投放/取消完成。
- Robot diagnostics 能把 terminal action summary 和 task_record 对齐，方便下一次真实现场材料回填时复盘。
- Engineer 不再围绕 PR #4 route/elevator blocker 继续堆 metadata wrapper，而是推进主链路字段和 fail-closed 契约。

产品北极星：普通手机用户最终能用低成本机器人完成送垃圾闭环。本轮只推进闭环中的 terminal action 可观察主路径，不证明真实 dropoff、真实 cancel、真实 delivery 或真实手机。

## 2. OKR 映射

| Objective | 映射 | 本轮是否提高完成度 |
| --- | --- | --- |
| Objective 5 | 当前约 68%，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover 或真实手机/browser proof。 | 否。本轮不做 O5 metadata depth，不证明 external proof。 |
| Objective 1 | 当前约 81%，上一轮已完成硬件真实材料升级请求；仍缺 WAVE ROVER/UART/HIL 和 PR #5 2D LiDAR / ToF 真实材料。 | 否。本轮不碰硬件材料，不提高 O1。 |
| Objective 2 | 当前约 99%，仍缺真实 dropoff completion、cancel completion、delivery result 和真实现场 task record。 | 仅推进 terminal action 主链路软件契约；不提高真实完成度。 |
| Objective 3 | 当前约 99%，仍缺真实 Nav2/fixed-route runtime、route completion signal 和现场复账。 | 仅要求 terminal action summary 可与同一 `evidence_ref` 的 route/task record 复盘；不证明真实路线。 |
| Objective 4 | 当前约 99%，手机端需解释 terminal action 状态和安全边界。 | 仅新增/调整只读可见性；不证明真实手机或 production app。 |

## 3. KR 拆解或更新

### KR-A：Robot terminal action task_record / diagnostics mainline

作为 Robot Platform Engineer，我需要 task_record / diagnostics 输出 `task_terminal_completion_mainline` summary，让 dropoff / cancel terminal action 成为主链路可复盘字段，而不是散落在旁路材料里。

必须包含：

- `schema`: `trashbot.task_terminal_completion_mainline.v1` 或 summary alias。
- `evidence_ref`: safe string，必须和相关 task_record / route evidence 对齐。
- `terminal_action`: `dropoff` / `cancel` / `unknown`。
- `terminal_status`: `missing_materials` / `awaiting_user_confirmation` / `software_proof_ready` / `blocked_not_proven`。
- `operator_confirmation_required` 和 `operator_confirmation_status`。
- `dropoff_completion_proven=false`、`cancel_completion_proven=false`、`delivery_success=false`。
- `primary_actions_enabled=false` 和 `not_proven` evidence boundary。
- `failure_reason`、`missing_required_materials`、`next_required_evidence`。

验收口径：缺 task_record、缺 evidence_ref、unsupported schema、unsafe copy、raw artifact、success wording、completion claim、HIL claim、O5 external proof claim 都必须 fail closed。

### KR-B：mobile/web terminal action mainline display

作为 User Touchpoint Full-Stack Engineer，我需要 mobile/web 展示 terminal action mainline 状态，并且保持 Start Delivery、Confirm Dropoff、Cancel gating 不扩大。

必须展示：

- safe terminal action status。
- safe `evidence_ref`。
- dropoff / cancel 是否仍 `not_proven`。
- operator confirmation 状态。
- missing materials 和 next required evidence。
- `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

验收口径：panel 不得触发 ACK、cursor、diagnostics fetch、Start Delivery、Confirm Dropoff、Cancel、handoff route、review route 或 robot command。缺 summary 时展示 fail-closed 状态。

### KR-C：Product closeout and OKR evidence boundary

作为 Product OKR Owner，我需要实现后更新 sprint closeout、OKR 和 progress log，说明本轮只是 terminal action 主链路软件契约。

验收口径：最终必须明确 Objective 5 不提高、Objective 1 不提高、Objective 2/3/4 只得到 software-proof 主链路可观察性；不把 PRD、diagnostics summary 或 mobile panel 写成真实投放、真实取消、真实电梯、真实手机或 delivery success。

## 4. 本轮核心抓手

`task_terminal_completion_mainline` 是本轮唯一核心抓手。

它不是 route/elevator material wrapper、不是真实 field-run intake、不是 HIL runner、不是 cloud probe、不是手机真实验收。它要回答一个更靠近主链路的问题：当用户或现场 owner 触发 dropoff / cancel terminal action 时，Robot 记录、diagnostics 和 mobile web 是否能用一致字段解释“发生了什么、还缺什么、为什么不能声明完成”。

## 5. 需要做什么

1. Robot：实现/调整 task_record 与 diagnostics 的 terminal action summary，增加 targeted tests 和接口文档同步。
2. Full-Stack：在 mobile/web 展示 terminal action mainline 状态，更新 fixtures/tests 和 `docs/product/mobile_user_flow.md`。
3. Product：实现后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
4. Autonomy：只读提供 route/fixed-route evidence 字段建议，避免 terminal summary 与 route evidence 语义冲突。
5. Hardware：本轮无写范围。

## 6. 优先级和验收口径

优先级：

1. P0：Robot summary 字段和 fail-closed 契约先稳定，确保不产生 completion / delivery success claim。
2. P0：mobile/web 不扩大 Start Delivery、Confirm Dropoff、Cancel gating；缺 summary 必须 fail closed。
3. P1：字段必须能支撑下一次真实现场材料回填：same `evidence_ref`、operator confirmation、missing materials、next required evidence。
4. P1：Product closeout 必须保守记录 OKR，不上调真实完成度。

全局验收口径：

- 必须包含 `task_terminal_completion_mainline`。
- 必须包含 `dropoff`、`cancel`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 必须显式提到 Objective 5、Objective 1、Objective 2、Objective 4、PR #4、PR #5。
- 必须由 `robot-software-engineer`、`full-stack-software-engineer`、`product-okr-owner` 三个 owner 并行/分段负责；Autonomy 只读咨询，Hardware 不写文件。

## 7. 风险、阻塞和证据链

- 当前主机只有 Docker，没有真实 WAVE ROVER、UART、2D LiDAR、ToF、真实电梯、真实 Nav2/fixed-route、真实手机、4G、OSS/CDN 或 production DB/queue。
- 本轮即使全部验证通过，也只能证明 repo 的 `software_proof` 主链路字段和 UI/diagnostics 展示工作，不能证明真实 dropoff completion、cancel completion、delivery success、HIL、真实手机或 O5 external proof。
- PR #4 真实 route/elevator materials 仍需现场 owner 后续提供：真实门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、真实 task record、completion signal、dropoff/cancel completion 和 delivery result。
- PR #5 真实 2D LiDAR / ToF materials 仍需现场 owner 后续提供；本轮不得新增或猜测硬件事实。

## 8. 需要创建或更新的 sprint 文档

本阶段已创建 PRD。实现后必须更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

Product closeout 必须再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。任何 Robot、mobile/web 或接口契约变更必须同步更新对应 `docs/` 文档。
