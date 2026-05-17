# Sprint 2026.05.17_09-10 Route Task Field Retest Callback Intake - PRD

sprint_type: epic

## 1. 用户问题

上一轮 `route_task_field_retest_evidence_dispatch` 已把现场复测材料派发给 owner、推荐文件名、同一 `evidence_ref`、回填顺序和 callback checklist。但现场支持仍缺一个 callback intake：现场人员拿到材料后，如何用 sanitized JSON 回传“推荐文件名是否收到、证据号是否一致、缺哪些材料、下一次回填动作是什么”。

本轮要新增 `route_task_field_retest_callback_intake`：一个 Docker-only、dependency-free、metadata-only 的现场回执入口。它消费 evidence dispatch artifact / summary 与现场人员 sanitized callback JSON，输出 `trashbot.route_task_field_retest_callback_intake.v1` 与 `_summary.v1`，并让 Robot diagnostics 与 mobile/web 只读展示同一份 phone-safe callback intake summary。

## 2. 用户价值和产品北极星

用户价值：

- 现场支持可以围绕同一 `evidence_ref` 登记推荐文件名是否收到、哪些材料缺失、证据号是否一致、下一次回填动作。
- Robot diagnostics 可以展示 callback intake 状态，但不会把回执解释成机器人动作授权、ACK、route completion 或 delivery success。
- 手机端可以用中文只读 panel 告诉现场人员哪些回传已收到、缺什么、下一步补什么，同时保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。

产品北极星：

- 普通手机用户最终能用手机理解机器人送垃圾任务状态和异常处理。
- 现场/工程侧每个关键行为都有可观测、可回放、可解释的同一 `evidence_ref` 证据链。
- Docker-only software proof 必须和真实 route/elevator field pass、HIL、真实手机/browser、真实投放、dropoff/cancel completion、delivery success、Objective 5 external proof 明确分离。

## 3. OKR 映射

- Objective 2：把 route/elevator assisted delivery 所需 door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 从派发清单推进为 callback intake。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 的回填状态绑定到同一 `evidence_ref`，强化固定路线复测材料的可复盘性。
- Objective 4：mobile/web 只读“现场回执入口” panel 提升现场支持可读性，但不改变主操作授权。
- Objective 5：保持约 68%。本轮不是 Objective 5 external proof；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser。
- Objective 1：本轮不推进硬件 HIL-entry；PR #5 暴露的 mandatory sensor baseline、2D LiDAR / ToF、vendor/source 和参数化约束仍需要真实材料。

## 4. KR 拆解或更新

本轮不直接改 `OKR.md` 的 KR 文本，先以 sprint 验收口径承接：

- KR-A：PC gate 可消费 `route_task_field_retest_evidence_dispatch` artifact / summary / wrapper / nested JSON 与 sanitized callback JSON，输出 `trashbot.route_task_field_retest_callback_intake.v1` 与 `trashbot.route_task_field_retest_callback_intake_summary.v1`。
- KR-B：输出固定 `software_proof_docker_route_task_field_retest_callback_intake_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- KR-C：callback intake 必须包含推荐文件名收到状态、same-`evidence_ref` 检查、缺项列表、下一次回填动作、owner handoff、callback checklist result 和 not-proven boundary。
- KR-D：required evidence packet 至少覆盖 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- KR-E：Robot diagnostics 和 mobile/web 只消费 metadata-only safe summary；unsupported schema、unsafe copy、success wording、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。

## 5. 本轮核心抓手

核心抓手是 `software_proof_docker_route_task_field_retest_callback_intake_gate`。它承接 evidence dispatch 的下一层现场回执动作，把“材料已派发给谁、应该叫什么”翻译成“现场是否收到、是否同一证据号、缺哪些、下一步怎么回填”，让真实材料到位后能按同一 `evidence_ref` 更快完成现场复测和 Product closeout。

## 6. 需要做什么

Task A - Autonomy Algorithm Engineer：

- 新增 dependency-free PC callback intake gate。
- 读取 `route_task_field_retest_evidence_dispatch` artifact / summary / wrapper / nested JSON。
- 接收 sanitized callback JSON，只允许推荐文件名收到状态、`evidence_ref` 一致性、缺项、下一次回填动作、owner callback note 等 metadata。
- 输出 callback intake artifact / summary，包含 intake status、safe `evidence_ref`、received filenames、missing materials、evidence-ref match result、next backfill action、callback checklist result、owner handoff、boundary 和 not-proven 列表。
- 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。

Task B - Robot Platform Engineer：

- 新增 diagnostics metadata-only consumer。
- 支持 callback intake artifact、summary、Robot-compatible summary 和 nested diagnostics summary。
- 暴露 safe status、safe `evidence_ref`、received/missing summary、evidence-ref match result、next backfill action、callback checklist result、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Fail closed，绝不触发 collect、dropoff、cancel、ACK、Nav2、HIL、cursor、diagnostics fetch 或 delivery success。

Task C - User Touchpoint Full-Stack Engineer：

- 新增 mobile/web 只读“现场回执入口” panel。
- 只展示 intake status、safe `evidence_ref`、received filenames、missing materials、evidence-ref match result、next backfill action、callback checklist result、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Start Delivery、Confirm Dropoff、Cancel gating 不变。
- Copy/export 采用 whitelist-only，不展示 raw artifact、raw JSON、raw path、credential、ROS topic、serial/UART、WAVE ROVER、DB/queue URL、OSS AK/SK、checksums、complete artifact 或 raw robot response。

Task D - Product Manager / OKR Owner：

- 实现后汇总 worker 证据，更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- 只在 worker 证据真实落地后保守评估 Objective 2 / Objective 3 / Objective 4 进度；Objective 5 不因本地 callback intake 提升。

## 7. 优先级和验收口径

优先级：

1. PC gate schema、boundary、same-`evidence_ref` 规则、fail-closed 行为和 summary 输出。
2. Robot diagnostics metadata-only consumer 的安全过滤和动作隔离。
3. mobile/web panel 的 phone-safe 展示和主操作 gating 不变。
4. 文档同步：PC README、fixed route workflow、ROS contracts、mobile user flow 和 sprint closeout 在实现阶段随代码更新。

验收口径：

- 所有输出必须包含 `software_proof_docker_route_task_field_retest_callback_intake_gate`。
- 所有输出必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Callback intake 必须明确 required field materials：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- 缺输入、坏 JSON、unsupported schema/boundary、证据号不一致、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER、success wording、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- 本轮只接受 Docker/local software proof，不接受把本地 callback intake 写成真实 route/elevator field pass、HIL、真实手机/browser、真实投放、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 8. 风险、阻塞和需要补齐的证据链

- 真实 route/elevator field materials 仍未补齐：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- O5 external proof 仍不可用：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover。
- 硬件链下一步需要真实 2D LiDAR / ToF / HIL-entry 材料，本轮不能替代 PR #5 要求。
- mobile/web panel 只能证明本地 UI 可展示 phone-safe summary，不证明真实 iPhone/Android、production app 或真实 PWA prompt/user choice。

## 9. 需要创建或更新的 sprint 文档

本 planning 阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现和 Product closeout 必须补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

后续 Product closeout 才允许基于 worker 证据更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。
