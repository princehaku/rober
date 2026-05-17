# Sprint 2026.05.17_10-11 Route Task Field Retest Callback Review Decision - PRD

sprint_type: epic

## 1. 用户问题

上一轮 `route_task_field_retest_callback_intake` 已把 PR #4 route/elevator field material 链路从 evidence dispatch 推进到 sanitized callback 可回填：现场人员可以登记推荐文件名收到状态、缺项、same-`evidence_ref` 检查和下一步回填动作。但 intake 状态本身还不是 decision：现场支持仍需要一个 review decision 层来判断是否可以进入 result intake，还是必须补材料、重跑同一证据号、修 schema 或阻断越界成功/控制声明。

本轮要新增 `route_task_field_retest_callback_review_decision`：一个 Docker-only、dependency-free、metadata-only 的现场回执复核决策 gate。它消费 callback intake artifact / summary / wrapper / nested JSON，输出 `trashbot.route_task_field_retest_callback_review_decision.v1` 与 `_summary.v1`，并让 Robot diagnostics 与 mobile/web 只读展示同一份 phone-safe decision summary。

## 2. 用户价值和产品北极星

用户价值：

- 现场支持可以围绕同一 `evidence_ref` 获得明确下一步：`ready_for_result_intake`、`needs_material_backfill`、`evidence_ref_mismatch_rerun`、`unsupported_callback_schema` 等。
- Robot diagnostics 可以展示 decision，但不会把 decision 解释成机器人动作授权、ACK、route completion、result intake 已完成或 delivery success。
- 手机端可以用中文只读 panel 告诉现场人员当前回执能否进入结果入口、缺哪些材料、是否需要重跑同一证据号，同时保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。

产品北极星：

- 普通手机用户最终能用手机理解机器人送垃圾任务状态和异常处理。
- 现场/工程侧每个关键行为都有可观测、可回放、可解释的同一 `evidence_ref` 证据链。
- Docker-only software proof 必须和真实 route/elevator field pass、HIL、真实手机/browser、真实投放、dropoff/cancel completion、delivery success、Objective 5 external proof 明确分离。

## 3. OKR 映射

- Objective 2：把 route/elevator assisted delivery 所需 door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 的 callback intake 状态审阅成 result-intake / backfill / rerun decision。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 的 same-`evidence_ref` 回执复核固化，强化固定路线复测材料的可复盘性和错配阻断。
- Objective 4：mobile/web 只读“现场回执复核决策” panel 提升现场支持可读性，但不改变主操作授权。
- Objective 5：保持约 68%。本轮不是 Objective 5 external proof；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser。
- Objective 1：本轮不推进硬件 HIL-entry；PR #5 暴露的 mandatory sensor baseline、2D LiDAR / ToF、vendor/source 和参数化约束仍需要真实材料。

## 4. KR 拆解或更新

本轮不直接改 `OKR.md` 的 KR 文本，先以 sprint 验收口径承接：

- KR-A：PC gate 可消费 `route_task_field_retest_callback_intake` artifact / summary / wrapper / nested JSON，输出 `trashbot.route_task_field_retest_callback_review_decision.v1` 与 `trashbot.route_task_field_retest_callback_review_decision_summary.v1`。
- KR-B：输出固定 `software_proof_docker_route_task_field_retest_callback_review_decision_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- KR-C：decision 必须覆盖 `ready_for_result_intake`、`needs_material_backfill`、`evidence_ref_mismatch_rerun`、`unsupported_callback_schema`、`blocked_unsafe_callback`、`blocked_success_claim`。
- KR-D：required evidence packet 至少覆盖 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- KR-E：Robot diagnostics 和 mobile/web 只消费 metadata-only safe summary；unsupported schema、unsafe copy、success wording、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。

## 5. 本轮核心抓手

核心抓手是 `software_proof_docker_route_task_field_retest_callback_review_decision_gate`。它承接 callback intake 的下一层现场审阅动作，把“回执收到什么、缺什么、证据号是否一致”翻译成“能否进入 result intake、是否要补材料、是否要重跑证据号、是否 schema/边界不支持”，让真实材料到位后能按同一 `evidence_ref` 更快进入结果入口和 Product closeout。

## 6. 需要做什么

Task A - Autonomy Algorithm Engineer：

- 新增 dependency-free PC callback review decision gate。
- 读取 `route_task_field_retest_callback_intake` artifact / summary / wrapper / nested JSON。
- 输出 review decision artifact / summary，包含 review decision、safe `evidence_ref`、source intake status、received/missing summary、same-evidence-ref verdict、next required evidence、result-intake readiness、owner handoff、rerun command summary、boundary 和 not-proven 列表。
- 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。

Task B - Robot Platform Engineer：

- 新增 diagnostics metadata-only decision consumer。
- 支持 review decision artifact、summary、Robot-compatible summary 和 nested diagnostics summary。
- 暴露 safe status、safe `evidence_ref`、review decision、blocked reasons、next required evidence、result-intake readiness、owner handoff、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Fail closed，绝不触发 collect、dropoff、cancel、ACK、Nav2、HIL、cursor、diagnostics fetch、result intake 或 delivery success。

Task C - User Touchpoint Full-Stack Engineer：

- 新增 mobile/web 只读“现场回执复核决策” panel。
- 只展示 review decision、safe `evidence_ref`、source intake status、missing/backfill summary、same-evidence-ref verdict、next required evidence、result-intake readiness、owner handoff、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Start Delivery、Confirm Dropoff、Cancel gating 不变。
- Copy/export 采用 whitelist-only，不展示 raw artifact、raw JSON、raw path、credential、ROS topic、serial/UART、WAVE ROVER、DB/queue URL、OSS AK/SK、checksums、complete artifact 或 raw robot response。

Task D - Product Manager / OKR Owner：

- 实现后汇总 worker 证据，更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- 只在 worker 证据真实落地后保守评估 Objective 2 / Objective 3 / Objective 4 进度；Objective 5 不因本地 callback review decision 提升。

## 7. 优先级和验收口径

优先级：

1. PC gate schema、boundary、same-`evidence_ref` 规则、decision mapping、fail-closed 行为和 summary 输出。
2. Robot diagnostics metadata-only consumer 的安全过滤和动作隔离。
3. mobile/web panel 的 phone-safe 展示和主操作 gating 不变。
4. 文档同步：PC README、fixed route workflow、ROS contracts、mobile user flow 和 sprint closeout 在实现阶段随代码更新。

验收口径：

- 所有输出必须包含 `software_proof_docker_route_task_field_retest_callback_review_decision_gate`。
- 所有输出必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Review decision 必须明确 required field materials：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- 缺输入、坏 JSON、unsupported schema/boundary、证据号不一致、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER、success wording、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- 本轮只接受 Docker/local software proof，不接受把本地 callback review decision 写成真实 route/elevator field pass、HIL、真实手机/browser、真实投放、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

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
