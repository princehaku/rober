# Sprint 2026.05.17_12-13 Route Task Handoff Result Intake Bridge - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

产品北极星：普通手机用户交付垃圾后，小车可以沿固定路线或跨楼层 assisted delivery 完成送达；当现场材料不足时，系统必须告诉操作者缺什么、谁补、用哪个 same-`evidence_ref` 补，而不是用技术细节或成功文案误导用户。

本轮用户价值：把上一轮 review-result handoff 变成 result intake gate 可直接消费的输入。现场团队拿到 review-result handoff artifact、summary、wrapper 或 nested JSON 后，不需要人工改写 schema，就能生成 result-intake artifact / summary，并继续让 Robot diagnostics 和 mobile/web 只读展示缺口。

## 2. 背景问题

上一轮已完成 `route_task_field_retest_review_result_handoff`，其边界是：

- `software_proof_docker_route_task_field_retest_review_result_handoff_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

但当前 `route_task_field_retest_result_intake` 的 SOURCE_SCHEMAS 只支持 session handoff、result、intake 系列 schema，不支持：

- `trashbot.route_task_field_retest_review_result_handoff.v1`
- `trashbot.route_task_field_retest_review_result_handoff_summary.v1`

结果是 handoff 不能直接进入 result intake。该断点会阻塞后续 result reconciliation / execution evidence，也会削弱 PR #4 route/elevator field materials 的证据链连续性。

## 3. OKR 映射

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。KR6 / KR7 需要电梯状态链和现场证据可复盘；本轮把 review-result handoff 接到 result intake，帮助后续真实 door state、target floor confirmation、human assistance note 和 delivery result 回填。
- Objective 3：可验证导航与固定路线。KR2 / KR3 / KR4 需要 route data、fixed-route、Nav2 waypoint 和关键状态可重复验证；本轮让 runtime log、route completion signal 和 task record 的材料入口能消费 handoff。
- Objective 4：手机用户体验与低成本量产边界。手机只显示 phone-safe 只读结果入口状态，不暴露 raw JSON、ROS topic、串口、硬件细节或成功宣称。
- Objective 5：约 68% 且数字最低，但本轮不推进。缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser；继续本地 metadata 不提升 O5。

## 4. KR 拆解

本轮可交付 KR：

1. result intake gate 支持 `route_task_field_retest_review_result_handoff` artifact / summary 作为来源 schema。
2. result intake gate 支持 wrapper / nested JSON 中嵌套的 review-result handoff 对象。
3. 输出仍是 `trashbot.route_task_field_retest_result_intake.v1` 和 `trashbot.route_task_field_retest_result_intake_summary.v1`。
4. 输出边界仍是 `software_proof_docker_route_task_field_retest_result_intake_gate`。
5. 对 unsafe copy、success claim、不同 `evidence_ref`、placeholder、缺材料继续 fail closed。
6. Robot diagnostics 只验证既有 result-intake consumer 可读取输出，不新增动作授权。
7. mobile/web 只验证既有 result-intake panel 或 consumer 可读取输出，不改变 Start Delivery、Confirm Dropoff、Cancel gate。

非目标 KR：

- 不做真实现场复测。
- 不补真实 Nav2/fixed-route log。
- 不补真实电梯门状态、目标楼层确认、人工协助记录。
- 不补真实 dropoff/cancel completion 或 delivery result。
- 不补 Objective 5 external proof。
- 不补 PR #5 真实 2D LiDAR / ToF source、receipt、install、wiring、calibration 或 HIL-entry。

## 5. 本轮核心抓手

核心抓手是“schema bridge + phone-safe/diagnostics read-only verification”：

- 在 PC gate 上把 review-result handoff schema 纳入 SOURCE_SCHEMAS 和 nested candidate 白名单。
- 保留 result-intake 的固定八类材料清单，不让 upstream handoff 裁剪 required materials。
- 保留 same-`evidence_ref`、safe basename、脱敏、unsafe copy、raw path、success claim 和 action release fail-closed 规则。
- 用窄测试证明 artifact、summary、wrapper、nested JSON 都能进入 result intake。
- 用现有 Robot/mobile consumer 的最小验证证明下游仍能读取 result-intake 输出，且 `primary_actions_enabled=false`。

## 6. 优先级

P0：

- 支持 `trashbot.route_task_field_retest_review_result_handoff.v1` 和 `trashbot.route_task_field_retest_review_result_handoff_summary.v1`。
- wrapper / nested JSON 能找到 handoff 对象。
- result-intake output schema、boundary 和 fail-closed flags 不变。
- scoped tests 覆盖 positive path、unsupported/missing schema 和 unsafe/success claim。

P1：

- Robot diagnostics consumer 窄验证读取新产出的 result-intake summary。
- mobile/web consumer 窄验证读取新产出的 result-intake summary。
- 文档补充：本轮只是 software proof bridge，不是 field pass。

P2：

- 若发现既有 consumer 的字段命名不能稳定展示 result-intake output，后续可另开小 sprint；本轮不扩大为 UI 重构。

## 7. 验收口径

本轮验收必须满足：

- `route_task_field_retest_result_intake.py` 能读取 review-result handoff artifact / summary / wrapper / nested JSON。
- 输出 schema 为 result-intake 系列，不输出新的 handoff schema。
- 输出 evidence boundary 为 `software_proof_docker_route_task_field_retest_result_intake_gate`。
- 输出包含 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 缺真实材料时仍列出 missing / required materials，不把 handoff readiness 写成 delivery success。
- Robot/mobile 验证只读读取，不新增控制动作。
- sprint closeout 不上调 Objective 5；Objective 2 / Objective 3 如有代码和验证落地，可按 software proof 边界保守评估。

## 8. 风险、阻塞和证据链缺口

- 风险：handoff summary 字段和 result-intake field parser 命名不完全一致，可能需要 mapping，但不能接受 raw artifact copy。
- 风险：wrapper / nested JSON 递归过宽可能误吞 unrelated payload，必须白名单 key。
- 风险：mobile/web 若没有现成 panel 字段，不能为展示方便改变 primary action gate。
- 阻塞：无真实现场材料时，本轮无法证明 route/elevator field pass。
- 阻塞：Objective 5 外部 proof 仍缺，不能借本轮 bridge 更新 O5。
- 证据缺口：真实 Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result、HIL、WAVE ROVER/UART、真实手机/browser 均仍缺。

## 9. 对应责任 Engineer

- Autonomy Algorithm Engineer：P0 主责，修改 PC evidence gate 和测试。
- Robot Platform Engineer：P1，只读 diagnostics consumer 验证。
- User Touchpoint Full-Stack Engineer：P1，只读 mobile/web consumer 验证。
- Product Manager / OKR Owner：验收证据、OKR 映射、`tech-done.md` / `side2side_check.md` / `final.md` closeout。
