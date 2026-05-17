# Sprint 2026.05.17_11-12 Route Task Field Retest Review Result Handoff - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

产品北极星：普通手机用户不需要理解 ROS2、路线日志、电梯材料或回执 schema，也能知道小车送垃圾任务当前是否具备进入结果入口的条件；工程团队也能用同一 `evidence_ref` 复盘为什么可以 intake、为什么要 backfill、为什么要 rerun，或者为什么必须 blocked。

本轮用户价值：把 `route_task_field_retest_callback_review_decision` 的审阅结论转成执行前交接包，避免现场人员、Robot diagnostics 和 mobile/web 各自解释材料状态。这个交接包不启用真实动作，只把下一步证据链、owner、阻塞原因和 result-intake readiness 说清楚。

## 2. OKR 映射

### Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环

映射 KR：

- KR4：失败、超时、取消和未满足条件时返回明确 action result / error message 的产品口径。本轮先在 result-handoff 层定义 blocked/backfill/mismatch 的可读原因。
- KR5：每次任务产出可复盘记录。本轮要求交接包保留 safe `evidence_ref`、source decision、required evidence、owner handoff 和 boundary。
- KR6 / KR7：电梯 assisted delivery 的 door_state、target_floor_confirmation、human_assistance_note 仍作为 result-intake 前必须核对的材料字段，不把缺失材料包装成现场完成。

### Objective 3：建立可验证导航与固定路线能力

映射 KR：

- KR2：route/fixed-route 输入输出格式继续固化。本轮 result-handoff 读取上轮 callback review decision，输出下游 result-intake 前置 contract。
- KR3：无 Nav2/无硬件环境下可验证路线材料读取和状态输出。本轮仍是 Docker-only software proof。
- KR5：PC 关键帧/调试链路需要展示当前位置、目标、匹配、失败原因和最近任务状态。本轮先把 result-handoff 的 read-only 状态给 PC/Robot/mobile 对齐。

### Objective 5：云中转 + OSS/CDN 数据通路产品化

不提升 Objective 5。本轮不是公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser proof。

## 3. KR 拆解和更新

本轮不修改 `OKR.md` 数值，只为下一轮实现建立可验收 planning baseline。后续实现完成后可以保守评估 Objective 2 / Objective 3 是否各 +1pp；不得因为本轮规划文档本身提高 OKR。

本轮交付 KR：

- KR-A：定义 `route_task_field_retest_review_result_handoff` PC artifact / summary contract，输入为 callback review decision artifact / summary，输出为 result-intake 前交接包。
- KR-B：定义 Robot diagnostics metadata-only 消费规则，保证 missing/unsupported/unsafe/success/action-enabled 全部 fail closed。
- KR-C：定义 mobile/web 只读 result-handoff panel，展示 review decision、handoff status、required evidence、owner、boundary 和 safe `evidence_ref`，不改变 Start / Confirm Dropoff / Cancel gating。
- KR-D：定义并行 owner 文件范围、验收命令和证据边界，让后续 Autonomy、Robot、Full-stack 可在互不覆盖文件的情况下执行。

## 4. 本轮核心抓手

核心抓手是 `route_task_field_retest_review_result_handoff`：

- 输入：`route_task_field_retest_callback_review_decision` artifact 或 summary。
- 输出：`trashbot.route_task_field_retest_review_result_handoff.v1` 和 `trashbot.route_task_field_retest_review_result_handoff_summary.v1`。
- Gate：`software_proof_docker_route_task_field_retest_review_result_handoff_gate`。
- 固定边界：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 需要做什么

### Autonomy

需要新增 PC gate，读取 callback review decision，生成 result-handoff artifact / summary。必须区分：

- `ready_for_result_intake`：可生成 `handoff_status=ready_for_result_intake_handoff`，但仍要求人工结果材料进入下一步 intake。
- `needs_material_backfill`：生成 `handoff_status=blocked_until_material_backfill`。
- `evidence_ref_mismatch_rerun`：生成 `handoff_status=blocked_until_same_evidence_ref_rerun`。
- `unsupported_callback_schema`：生成 `handoff_status=blocked_unsupported_source_schema`。
- `blocked_unsafe_callback` / `blocked_success_claim`：生成 `handoff_status=blocked_unsafe_source_review`。

### Robot

需要在 diagnostics 中新增 metadata-only consumer，只暴露 sanitized summary。不得新增 ACK、cursor、Nav2 command、dropoff/cancel result、delivery result 或任何 primary action。

### Full-stack

需要在 mobile/web 增加只读 panel，phone-safe 展示交接状态和下一步材料要求。copy/export whitelist-only，主操作 gating 不变。

### Product

实现后需要验收证据边界，更新 sprint closeout、`OKR.md` 和相关 `docs/`。本规划阶段只创建 pre_start、prd、tech-plan。

## 6. 优先级和验收口径

优先级：

1. Autonomy PC gate 和 schema：最高优先级，因为 Robot/mobile 都依赖 summary contract。
2. Robot diagnostics consumer：第二优先级，负责统一后端状态边界。
3. Full-stack mobile/web read-only panel：第三优先级，负责用户触点解释。
4. Product closeout：实现后执行，负责 OKR 和证据边界。

验收口径：

- 所有输出必须包含 `software_proof_docker_route_task_field_retest_review_result_handoff_gate`。
- 所有输出必须包含 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- `ready_for_result_intake` 只能表示“可进入结果材料入口前交接”，不能表示真实结果已完成。
- 缺材料、schema mismatch、unsafe copy、success claim 或 action-enabled 必须 fail closed。
- Mobile/web 不得显示真实完成、真实投放、真实送达、HIL、现场通过等成功语义。

## 7. 对应责任 Engineer

- `autonomy-engineer`：PC result-handoff CLI、artifact/summary schema、focused tests、`docs/navigation/fixed_route_workflow.md`。
- `robot-software-engineer`：`operator_gateway_diagnostics.py` metadata-only consumer、focused tests、`docs/interfaces/ros_contracts.md`。
- `full-stack-software-engineer`：mobile/web panel、fixture、entrypoint tests、`docs/product/mobile_user_flow.md`。
- `product-okr-owner`：验收口径、closeout、`OKR.md` 和 process log。只在实现完成后更新。

## 8. 风险、阻塞和证据链

- 仍缺真实 route/elevator field materials：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。
- 仍缺真实 WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF SKU/source/receipt/install/wiring/calibration/HIL-entry。
- 仍缺真实手机/browser、production app 和 PWA prompt/user choice。
- 仍缺 Objective 5 external proof。
- 本轮后续实现只能产出 Docker-only software proof，不得写成真实现场完成。

## 9. 需要创建或更新的 sprint 文档

规划阶段已覆盖：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现完成后必须新增或更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- `docs/navigation/fixed_route_workflow.md`
- `docs/interfaces/ros_contracts.md`
- `docs/product/mobile_user_flow.md`
