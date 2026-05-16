# Sprint 2026.05.17_04-05 Route Task Field Retest Drill Console - PRD

sprint_type: epic

## 1. 用户问题

上一轮 `route_task_field_retest_operator_drill` 已把现场复测的 material pack、result intake、result reconciliation 命令串起来，但现场人员仍需要在 artifact、summary、Robot diagnostics 和 mobile/web 面板之间切换理解演练状态。

本轮要把 operator drill 推进为 `route_task_field_retest_drill_console`：一个 Docker-only、dependency-free、只读、安全摘要优先的演练控制台链路。它消费 operator drill artifact / summary，输出 `trashbot.route_task_field_retest_drill_console.v1` 和 summary，并让 Robot diagnostics 与 mobile/web 展示同一份 safe checklist / copy。

## 2. 用户价值和产品北极星

用户价值：

- 现场支持同学可以围绕同一 `evidence_ref` 看到下一步应该补哪些 route/elevator field materials，而不是从多个文件人工拼接。
- Robot diagnostics 可以 fail closed 地展示演练控制台状态，不把演练摘要变成机器人动作授权。
- 手机端可以用中文只读 panel 告诉现场人员“这是现场复测演练控制台，不是真实通过”，并保持 Start Delivery、Confirm Dropoff、Cancel gating 不变。

产品北极星：

- 普通手机用户最终能用手机理解机器人送垃圾任务状态和异常处理。
- 现场/工程侧每个关键行为都有可观测、可回放、可解释的证据链。
- Docker-only 软件证明必须和真实 route/elevator field pass、HIL、真实手机、Objective 5 external proof 明确分离。

## 3. OKR 映射

- Objective 2：把 route/elevator assisted delivery 的现场复测从 operator drill 推进为演练控制台，帮助补齐门状态、目标楼层、人工协助、dropoff/cancel completion 和 delivery result 的同一 `evidence_ref` 回填路径。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、task record 等材料的回填清单进一步可视化，降低真实 fixed-route 现场复测时的材料遗漏。
- Objective 4：mobile/web 新增只读“现场复测演练控制台” panel，提升现场支持可读性，但不改变主操作授权。
- Objective 5：保持约 66%。本轮不是 Objective 5 external proof；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- Objective 1：本轮不推进硬件 HIL-entry；2D LiDAR / ToF / WAVE ROVER / UART / HIL 仍等待真实材料。

## 4. KR 拆解或更新

本轮不直接改 `OKR.md` 的 KR 文本，先以 sprint 验收口径承接：

- KR-A：PC gate 可消费 `route_task_field_retest_operator_drill` artifact / summary，输出 `trashbot.route_task_field_retest_drill_console.v1` 与 `trashbot.route_task_field_retest_drill_console_summary.v1`。
- KR-B：输出固定 `software_proof_docker_route_task_field_retest_drill_console_gate`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- KR-C：Robot diagnostics 只消费 metadata-only safe summary，任何 unsupported schema、unsafe copy、success wording 或 actions enabled 都 fail closed。
- KR-D：mobile/web 只读 panel 展示 console status、safe `evidence_ref`、safe checklist/copy、missing material prompts、operator callback checklist、boundary 和 not-proven 状态，且 Start Delivery / Confirm Dropoff / Cancel gating 不变。

## 5. 本轮核心抓手

核心抓手是 `software_proof_docker_route_task_field_retest_drill_console_gate`。它不是再新增一个 O5 local metadata wrapper，而是承接 operator drill 的下一层现场复测可读控制台，让真实材料到位后能按同一 `evidence_ref` 更快完成 material pack、result intake、result reconciliation。

## 6. 需要做什么

Task A - Autonomy Algorithm Engineer：

- 新增 dependency-free PC drill console gate。
- 读取 `route_task_field_retest_operator_drill` artifact / summary / wrapper / nested JSON。
- 输出 console artifact / summary，包含 safe checklist、copyable command labels、required field-material categories、missing prompts、operator callback checklist、rerun notes、boundary 和 not-proven 列表。
- 不读取真实材料目录，不声明 field pass。

Task B - Robot Platform Engineer：

- 新增 diagnostics metadata-only consumer。
- 支持 console artifact / summary / compatible summary。
- 暴露 safe status、safe `evidence_ref`、checklist labels、missing prompts、callback checklist、boundary。
- Fail closed，绝不触发 collect、dropoff、cancel、ACK、Nav2、HIL 或 delivery success。

Task C - User Touchpoint Full-Stack Engineer：

- 新增 mobile/web 只读“现场复测演练控制台” panel。
- 只展示 safe checklist/copy、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- Start Delivery、Confirm Dropoff、Cancel gating 不变。
- 不展示 raw artifact、raw JSON、raw path、credential、ROS topic、serial/UART、WAVE ROVER、DB/queue、OSS/CDN secret 或 checksums。

## 7. 优先级和验收口径

优先级：

1. PC gate schema、boundary、fail-closed 行为和 summary 输出。
2. Robot diagnostics metadata-only consumer 的安全过滤和动作隔离。
3. mobile/web panel 的 phone-safe 展示和主操作 gating 不变。
4. 文档同步：PC、ROS contract、mobile user flow 在实现阶段随代码更新。

验收口径：

- 所有输出必须包含 `software_proof_docker_route_task_field_retest_drill_console_gate`。
- 所有输出必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 缺输入、坏 JSON、unsupported schema/boundary、证据号不一致、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER、success wording、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
- 本轮只接受 Docker/local software proof，不接受把本地演练控制台写成真实 route/elevator field pass、HIL、真实手机/browser、真实投放或 Objective 5 external proof。

## 8. 风险、阻塞和需要补齐的证据链

- 真实 route/elevator field materials 仍未补齐：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- O5 external proof 仍不可用：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。
- 硬件链下一步需要真实 2D LiDAR / ToF / HIL-entry 材料，本轮不能替代。
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
