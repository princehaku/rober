# Sprint 2026.05.17_06-07 Route Task Field Retest Evidence Dispatch - PRD

sprint_type: epic

## 1. 用户问题

上一轮 `route_task_field_retest_acceptance_brief` 已把现场复测从 drill console 推进为 acceptance brief：现场准入、执行 checklist、pass/fail criteria、required evidence packet、owner handoff 和 rerun notes 已能被 PC / Robot / mobile 共同只读消费。但现场支持仍缺一份 evidence packet dispatch：每份真实材料由谁采集、文件名如何命名、回填顺序是什么、哪些 callback checklist 必须逐项确认、失败时如何 fail closed 并重新派发。

本轮要新增 `route_task_field_retest_evidence_dispatch`：一个 Docker-only、dependency-free、metadata-only 的现场证据包派发链路。它消费 acceptance brief artifact / summary，输出 `trashbot.route_task_field_retest_evidence_dispatch.v1` 与 `_summary.v1`，并让 Robot diagnostics 与 mobile/web 只读展示同一份 phone-safe dispatch summary。

## 2. 用户价值和产品北极星

用户价值：

- 现场支持可以围绕同一 `evidence_ref` 获得材料 owner、建议文件名、回填顺序、callback checklist 和 fail-closed rerun notes。
- Robot diagnostics 可以展示证据包派发状态，但不会把 dispatch 解释成机器人动作授权、ACK、route completion 或 delivery success。
- 手机端可以用中文只读 panel 告诉现场人员下一步要补哪些材料、谁负责、缺什么仍必须 fail closed，同时保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。

产品北极星：

- 普通手机用户最终能用手机理解机器人送垃圾任务状态和异常处理。
- 现场/工程侧每个关键行为都有可观测、可回放、可解释的同一 `evidence_ref` 证据链。
- Docker-only software proof 必须和真实 route/elevator field pass、HIL、真实手机/browser、真实投放、dropoff/cancel completion、delivery success、Objective 5 external proof 明确分离。

## 3. OKR 映射

- Objective 2：把 route/elevator assisted delivery 所需 door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 分派到明确 owner、文件名和 callback checklist。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 分派到同一 `evidence_ref` 下，强化固定路线复测材料顺序和可复盘性。
- Objective 4：mobile/web 只读“现场证据包派发” panel 提升现场支持可读性，但不改变主操作授权。
- Objective 5：保持约 66%。本轮不是 Objective 5 external proof；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- Objective 1：本轮不推进硬件 HIL-entry；PR #5 暴露的硬件 baseline、2D LiDAR / ToF、vendor/source 和参数化约束仍需要真实材料。

## 4. KR 拆解或更新

本轮不直接改 `OKR.md` 的 KR 文本，先以 sprint 验收口径承接：

- KR-A：PC gate 可消费 `route_task_field_retest_acceptance_brief` artifact / summary / wrapper / nested JSON，输出 `trashbot.route_task_field_retest_evidence_dispatch.v1` 与 `trashbot.route_task_field_retest_evidence_dispatch_summary.v1`。
- KR-B：输出固定 `software_proof_docker_route_task_field_retest_evidence_dispatch_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- KR-C：dispatch 必须包含材料 owner、建议文件名、同一 `evidence_ref` 约束、回填顺序、callback checklist、fail-closed rerun notes 和 not-proven boundary。
- KR-D：required evidence packet 至少覆盖 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- KR-E：Robot diagnostics 和 mobile/web 只消费 metadata-only safe summary；unsupported schema、unsafe copy、success wording、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。

## 5. 本轮核心抓手

核心抓手是 `software_proof_docker_route_task_field_retest_evidence_dispatch_gate`。它承接 acceptance brief 的下一层现场执行动作，把“需要哪些材料才可验收”翻译成“每份材料谁采、叫什么、何时回填、如何 callback、失败后如何重跑”，让真实材料到位后能按同一 `evidence_ref` 更快完成现场复测和 Product closeout。

## 6. 需要做什么

Task A - Autonomy Algorithm Engineer：

- 新增 dependency-free PC evidence dispatch gate。
- 读取 `route_task_field_retest_acceptance_brief` artifact / summary / wrapper / nested JSON。
- 输出 dispatch artifact / summary，包含 dispatch status、safe `evidence_ref`、material owners、recommended filenames、same-evidence-ref rule、backfill order、callback checklist、fail-closed rerun notes、required evidence packet、boundary 和 not-proven 列表。
- 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。

Task B - Robot Platform Engineer：

- 新增 diagnostics metadata-only consumer。
- 支持 dispatch artifact、summary、Robot-compatible summary 和 nested diagnostics summary。
- 暴露 safe status、safe `evidence_ref`、owner/file dispatch、backfill order、callback checklist、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Fail closed，绝不触发 collect、dropoff、cancel、ACK、Nav2、HIL、cursor、diagnostics fetch 或 delivery success。

Task C - User Touchpoint Full-Stack Engineer：

- 新增 mobile/web 只读“现场证据包派发” panel。
- 只展示 dispatch status、safe `evidence_ref`、material owners、recommended filenames、backfill order、callback checklist、fail-closed rerun notes、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Start Delivery、Confirm Dropoff、Cancel gating 不变。
- Copy/export 采用 whitelist-only，不展示 raw artifact、raw JSON、raw path、credential、ROS topic、serial/UART、WAVE ROVER、DB/queue URL、OSS AK/SK、checksums、complete artifact 或 raw robot response。

Task D - Product Manager / OKR Owner：

- 实现后汇总 worker 证据，更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- 只在 worker 证据真实落地后保守评估 Objective 2 / Objective 3 / Objective 4 进度；Objective 5 不因本地 dispatch 提升。

## 7. 优先级和验收口径

优先级：

1. PC gate schema、boundary、same-`evidence_ref` 规则、fail-closed 行为和 summary 输出。
2. Robot diagnostics metadata-only consumer 的安全过滤和动作隔离。
3. mobile/web panel 的 phone-safe 展示和主操作 gating 不变。
4. 文档同步：ROS contracts、mobile user flow 和 sprint closeout 在实现阶段随代码更新。

验收口径：

- 所有输出必须包含 `software_proof_docker_route_task_field_retest_evidence_dispatch_gate`。
- 所有输出必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Evidence dispatch 必须明确 required field materials：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- 缺输入、坏 JSON、unsupported schema/boundary、证据号不一致、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER、success wording、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- 本轮只接受 Docker/local software proof，不接受把本地 dispatch 写成真实 route/elevator field pass、HIL、真实手机/browser、真实投放、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 8. 风险、阻塞和需要补齐的证据链

- 真实 route/elevator field materials 仍未补齐：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- O5 external proof 仍不可用：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
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
