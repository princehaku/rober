# Sprint 2026.05.18_16-17 Route Task Acceptance Execution Rerun Queue - PRD

## 1. 背景和问题

上一轮已经把 `route_task_field_retest_acceptance_execution_handoff_intake` 做成 owner handoff intake / acknowledgement gate。它能判断 handoff intake 是否 ready、是否缺 owner ack、是否需要 backfill、是否 evidence_ref mismatch 或 unsafe。

当前缺口是：现场 owner 下一步仍需要一个 metadata-only queue package，把 handoff intake 的结论、可选 queue request 和下一步材料要求整理成受控现场复跑队列状态。没有这个队列包，后续 Autonomy / Robot / Full-stack 很容易把“ready for queue”误说成“已经复跑”或把缺材料状态误放行给手机端。

## 2. 用户价值和产品北极星

用户价值:

- 现场支持人员可以围绕同一 safe `evidence_ref` 判断是否进入受控现场复跑准备。
- 普通手机用户不会看到 raw JSON、ROS topic、串口、路径、凭证或底层材料，只看到“等待现场材料/等待 owner 确认/可准备复跑”的解释。
- Product / OKR 可以继续区分 software proof、现场材料准备、真实 field pass、HIL 和 O5 external proof。

产品北极星:

`rober` 是普通手机用户可用的低成本 ROS2 自主垃圾投递机器人。本轮只推进送达/电梯 assisted delivery 的证据链组织能力，不新增机械能力、不新增硬件假设、不宣称真实送达成功。

## 3. OKR 映射

### Objective 2

`route_task_field_retest_acceptance_execution_rerun_queue` 直接服务可送垃圾任务 + 电梯 assisted delivery 闭环。它把 PR #4 的 route/elevator 必达能力继续推向受控现场复跑准备，但不越界宣称真实电梯或真实送达。

### Objective 3

复跑队列包必须继续要求真实 Nav2/fixed-route runtime log、task record、completion signal、同一 `evidence_ref` 和 route/elevator completion material。缺这些材料时只能 blocked/backfill。

### Objective 4

手机端只读展示 queue status、owner handoff、next required evidence 和 not-proven boundary，让普通用户和现场支持看到下一步，但不改变 Start / Confirm Dropoff / Cancel gating。

### Objective 5

Objective 5 数字最低，但本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser。该 Objective 本轮只作为 stop-rule 说明，不作为主线。

### Objective 1

Objective 1 次低，但本机没有真实 WAVE ROVER/UART/HIL、PR #5 2D LiDAR / ToF 真实材料。本轮不做硬件声明、不改硬件配置、不宣称 HIL。

## 4. KR 拆解或更新

- KR-A: Autonomy 提供 `trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1` artifact 和 `trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1` summary。
- KR-B: Robot diagnostics 提供 `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary` safe alias，并保持 metadata-only。
- KR-C: Full-stack mobile/web 提供只读“受控复跑队列” panel，并继续 fail-closed，不触发机器人动作。
- KR-D: Product closeout 把本轮证据写入 sprint 和 OKR 边界，明确 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate` 不等于真实 field pass、HIL、delivery success 或 Objective 5 proof。

## 5. 本轮核心抓手

新增受控现场复跑队列包：

- 输入 1: handoff intake artifact / summary / wrapper / nested JSON。
- 输入 2: 可选 queue request JSON，必须只包含 phone-safe / owner-safe metadata。
- 输出: queue artifact、queue summary、safe copy、owner handoff、next required evidence、safe rerun hint、queue status、blocked reason。
- 队列状态建议:
  - `queued_for_controlled_field_rerun_not_proven`
  - `needs_owner_ack_before_queue`
  - `needs_acceptance_execution_rerun_queue_backfill`
  - `evidence_ref_mismatch_rerun_queue`
  - `blocked_unsafe_rerun_queue`
  - `blocked_unsupported_handoff_intake`
- 所有状态必须固定 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 6. 需要做什么

### Autonomy

- 新增 PC gate `pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py`。
- 新增 focused unittest `tests/test_route_task_field_retest_acceptance_execution_rerun_queue.py`。
- 只读消费上一轮 handoff intake 产物和可选 queue request。
- 校验 schema、boundary、safe `evidence_ref`、source readiness、owner ack、queue request same-evidence-ref、unsafe copy、success/control claims。
- 更新 PC evidence README / evidence contract。

### Robot

- 在 operator diagnostics 中新增 rerun queue summary safe alias。
- 支持 explicit ref、status nested summary、diagnostics nested summary 和缺省 blocked summary。
- 确认该 alias 不触发 collect/dropoff/cancel、ACK、cursor、Nav2、serial/UART、WAVE ROVER 或 HIL。
- 更新 ROS / diagnostics 文档。

### Full-stack

- 在 `mobile/web` 新增只读“受控复跑队列” panel。
- fixture 和 tests 覆盖 top-level、Robot safe alias、nested diagnostics 和 missing/unsafe 状态。
- UI 只显示 safe fields，不暴露 raw artifact、complete JSON、checksum、local path、ROS topic、serial/UART、credentials 或 success copy。
- Start / Confirm Dropoff / Cancel gating 不变。

### Product

- 收口 sprint 文档，核对 PR #4 / PR #5 / OKR evidence。
- 如实现完成，更新 `OKR.md` 和 `docs/process/okr_progress_log.md`，但保持软件证明口径。

## 7. 优先级和验收口径

P0 验收:

- PC gate fail closed。
- Robot diagnostics safe alias 不释放动作。
- Mobile panel 只读且不泄露 raw / control / success copy。
- 三方使用同一 `evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`。
- 集成 `rg` 命中 `PR #4`、`PR #5`、`Objective 5`、`Objective 1` 和 not-proven flags。

P1 验收:

- 文档同步到 `docs/` 对应 contract。
- 新增代码中文技术注释比例超过 20%，注释解释边界和失败原因。
- 不新增硬件事实；如果后续触碰 2D LiDAR / ToF / WAVE ROVER / UART，必须回到 `docs/vendor/VENDOR_INDEX.md`。

## 8. 责任 Engineer

- `autonomy-engineer`: PC gate、unit test、schema/boundary、PC docs。
- `robot-software-engineer`: diagnostics safe alias、metadata fence、diagnostics tests、ROS docs。
- `full-stack-software-engineer`: mobile/web panel、fixture/tests、mobile docs。
- `product-okr-owner`: sprint evidence、OKR mapping、closeout 和边界语言。

## 9. 风险、阻塞和需要补齐的证据链

- 没有真实现场复跑材料时，queue package 不能证明 field pass。
- 没有真实 WAVE ROVER/UART/HIL 时，不能证明 Objective 1。
- 没有真实公网/4G/OSS/CDN/DB/queue/worker/手机时，不能证明 Objective 5。
- PR #5 的 2D LiDAR / ToF 真实 SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry 仍缺。
- 后续实现必须防止 success phrasing、`delivery_success=true`、`primary_actions_enabled=true`、raw artifact 或 complete local path 泄漏到 summary/mobile。

## 10. 需要创建或更新的 sprint 文档

本轮计划阶段已创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现阶段必须追加：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

