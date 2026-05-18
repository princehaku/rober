# Sprint 2026.05.18_18-19 Route Task Acceptance Execution Rerun Result Review Decision - PRD

## 1. 用户价值和产品北极星

北极星：普通手机用户可以把垃圾交给低成本 ROS2 小车，由小车沿固定路线完成送达、电梯 assisted delivery、异常解释和可复盘证据链；用户不需要懂 ROS2、串口、raw JSON、硬件接线或云基础设施。

本轮用户价值：把“受控复跑结果回执入口”推进成“复跑结果复核决策”。现场 owner 提交 result intake 后，系统必须给出下一步明确判定：进入 handoff、要求 backfill、同一 `evidence_ref` mismatch、unsafe copy 拦截、或 unsupported intake 拒绝。手机用户和支持人员只能看到 phone-safe、只读、fail-closed 状态，不能把 review decision 当成真实路线、电梯、投放或 delivery success。

## 2. OKR 映射

- Objective 5：当前约 68%，是 `OKR.md` 4.1 数字最低项。但缺真实外部 HTTPS/TLS、4G/SIM、OSS/CDN、production DB/queue、worker/cutover、真实手机/browser。按 stop rule，本轮不继续堆本地 Objective 5 metadata，也不把本轮 artifact 写成 O5 external proof。
- Objective 1：当前约 81%。本机无真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report；PR #5 还缺真实 2D LiDAR / ToF vendor/source/receipt/procurement/HIL-entry 材料。本轮不继续包装同一 O1 hardware blocker。
- Objective 2：本轮直接服务“可送垃圾任务 + 电梯 assisted delivery 必达闭环”，接续 PR #4 的 route/elevator 主链，把 result intake 转成可执行 review decision。
- Objective 3：本轮服务“可验证导航与固定路线能力”，把真实 route completion signal、task record、Nav2/fixed-route runtime log、dropoff/cancel completion、delivery result 的缺口转成明确复核判定。
- Objective 4：本轮服务手机用户体验边界，让 mobile/web 只读展示 review decision，而不开放 Start / Confirm Dropoff / Cancel。

## 3. KR 拆解或更新

- KR-A：新增 PC gate `route_task_field_retest_acceptance_execution_rerun_result_review_decision`，消费上一轮 result intake artifact/summary，输出安全 review decision。
- KR-B：复核决策支持五类结果：`ready_for_acceptance_execution_rerun_result_handoff`、`needs_acceptance_execution_rerun_result_backfill`、`evidence_ref_mismatch_rerun_result`、`blocked_unsafe_rerun_result`、`blocked_unsupported_rerun_result_intake`。
- KR-C：Robot diagnostics 输出 sanitized review decision summary alias，保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，拒绝 raw artifact、路径、checksum、凭证、ROS topic、串口/UART 等 unsafe copy。
- KR-D：mobile/web 新增只读 result review decision panel，展示 decision status、safe evidence ref、owner handoff、next required evidence、evidence boundary 和 fail-closed flags。
- KR-E：docs/interface 与 docs/product 同步说明新 contract 和手机展示边界，避免 Engineer 把 review decision 误写成 delivery result success。

## 4. 本轮核心抓手

抓手是 metadata-only result review decision，而不是真实现场通过：

- 输入：上一轮 `route_task_field_retest_acceptance_execution_rerun_result_intake` artifact/summary。
- 输出：`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate` 下的 sanitized artifact/summary。
- 必须保留：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 必须写清：not real route/elevator field pass、not delivery success、not HIL、not real phone/browser、not Objective 5 external proof。

## 5. 需要做什么

1. Autonomy 建 PC evidence review decision gate 和 focused tests，严格区分 ready handoff、backfill、mismatch、unsafe、unsupported。
2. Robot 在 diagnostics 中只读消费 review decision summary alias，保持 support-facing sanitized 字段，不暴露原始路径或控制能力。
3. Full-stack 在 mobile/web 增加只读 result review decision panel 和 fixture/test，保持 primary action gating 不变。
4. 所有 owner 同步接口文档或产品文档，不新增真实硬件、真实云、真实手机或真实 delivery success 声明。

## 6. 优先级和验收口径

P0 验收：

- 三个 owner 都能基于同一 safe `evidence_ref` 表达 result review decision 状态。
- 证据边界必须出现并保持：`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`。
- 所有 surface 必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 必须明确不是 real route/elevator field pass、not delivery success、not HIL、not real phone/browser、not Objective 5 external proof。

P1 验收：

- Robot/mobile 不暴露 raw artifact、complete artifact、checksum、local path、credentials、ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER low-level detail。
- mobile/web 不改变 Start Delivery、Confirm Dropoff、Cancel 的 fail-closed gating。
- docs/interfaces 和 docs/product 说明新增 contract 与 phone-safe 边界。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：PC gate、PC test、PC README、evidence contract。
- Robot Platform Engineer：operator gateway diagnostics、Robot diagnostics tests、ROS contract。
- User Touchpoint Full-Stack Engineer：mobile/web app、fixture、mobile web tests、mobile user flow docs。
- Product Manager / OKR Owner：本 sprint 的 PRD、tech-plan、验收口径、后续 tech-done / side2side / final 收口；不改实现。

## 8. 风险、阻塞和需要补齐的证据链

- PR #4 已把 elevator-assisted delivery 推成必达主链；本轮只补 result review decision metadata，仍缺真实 route/elevator field pass。
- PR #5 unresolved review threads 的 hardware baseline 风险仍存在：默认硬件集合 vs `monocular + 2D LiDAR + ToF` baseline、新 sensor baseline 缺 `docs/vendor/` source citation、真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料缺失。本轮不得虚假解决这些硬件材料。
- 真实 route/elevator 回填仍缺：route completion signal、task record、Nav2/fixed-route runtime log、dropoff/cancel completion、delivery result、门状态、楼层确认、人工协助记录。
- 本轮若只有 Docker/local 证明，不得更新 OKR 完成度为真实现场通过。

## 9. 需要创建或更新的 sprint 文档

- 本阶段：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实现后：`tech-done.md` 记录三 owner 实际改动、验证结果和偏差。
- 验收后：`side2side_check.md` 对照 PRD 验收。
- 收口后：`final.md` 回顾 OKR 最低优先级核对、证据边界和剩余风险。
