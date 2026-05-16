# Sprint 2026.05.16_09-10 Mobile Field Material Retest Request - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

产品北极星：让普通手机用户可以把垃圾交给低成本 ROS2 小车，并在固定路线 / 电梯 assisted delivery 场景里可验证地完成送达；失败时现场人员能知道缺什么证据、下一次怎么复测、由谁补齐，而不是靠工程师口头判断。

本轮用户价值：把上一轮 review decision 的 blockers 和 next-required-evidence 变成一份 route/elevator field retest request。现场人员下一次复测前可以直接看到需要补采的材料清单、同一 `evidence_ref` 要求、owner handoff 和 fail-closed 边界；手机端只读展示，不让用户误以为小车已经具备真实路线、电梯、投放或交付能力。

## 2. OKR 映射

- Objective 2：主线。retest request 把送垃圾任务 + 电梯 assisted delivery 的缺口转成现场复测请求，覆盖真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel material 和 delivery result 的下一步证据。
- Objective 3：主线。retest request 强制 route/elevator field material、Nav2/fixed-route runtime log、task record、completion signal 与 same `evidence_ref` 对齐，支撑可验证导航与固定路线复测。
- Objective 4：支撑。`mobile/web` 只读 request panel 把复测请求 phone-safe 地展示给现场人员，但不改变 Start / Confirm Dropoff / Cancel gating。
- Objective 1：不上调。本轮不接触真实 WAVE ROVER、UART、Orange Pi、`T=1001` feedback 或 HIL。
- Objective 5：不上调。当前缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration；本轮不补 O5 external proof。

## 3. KR 拆解或更新

本轮不直接修改 `OKR.md`，只定义后续实现若完成后可支撑的 KR 证据：

- Objective 2 KR5 / KR6 / KR7：输出 retest request，要求下一次现场材料必须包含电梯门状态、目标楼层确认、人工协助记录、失败/恢复原因、dropoff/cancel 或 delivery result，并保持 `delivery_success=false` 直到真实送达证据存在。
- Objective 3 KR2 / KR3 / KR4 / KR5：把 Nav2/fixed-route runtime log、task record、completion signal、route/elevator material checklist 和 PC/diagnostics/mobile summaries 放进 same `evidence_ref` 复测请求。
- Objective 4 KR1 / KR5 / KR6 / KR7：手机端显示中文优先、只读、phone-safe 的复测请求，让非工程用户知道下一步怎么采证，但不得暴露 raw JSON、ROS topic、硬件调试字段或 credentials。

## 4. 本轮核心抓手

从“review decision 告诉我们缺什么”推进到“retest request 告诉现场人员下一次怎么补”。

建议契约：

- artifact/schema：`trashbot.mobile_field_material_retest_request.v1`
- summary/schema：`trashbot.mobile_field_material_retest_request_summary.v1`
- evidence boundary：`software_proof_docker_mobile_field_material_retest_request_gate`
- 关键字段：
  - `source_review_decision`
  - `blockers`
  - `next_required_evidence`
  - `retest_request`
  - `route_elevator_material_checklist`
  - `owner_handoff`
  - `evidence_ref`
  - `same_evidence_ref_required`
  - `same_evidence_ref_status`
  - `not_proven`
  - `delivery_success=false`
  - `primary_actions_enabled=false`

## 5. 需要做什么

### 建议 1：Autonomy 先把 review decision 转成 retest request artifact

具体证据：08-09 `final.md` 写明 PC gate 已能把 intake 转为 review decision、blocker、next-required-evidence 和 owner handoff；`OKR.md` 4.1 写明 O2/O3 仍缺真实 route/elevator field material、Nav2/fixed-route runtime log、task record/completion signal 和 same `evidence_ref` 上车实机复账。

需要做：

- 新增 `pc-tools/evidence/mobile_field_material_retest_request.py`。
- 新增 targeted tests，覆盖 missing blocker、missing next-required-evidence、same-evidence-ref mismatch、unsafe success claim、placeholder material 和 valid request。
- 输入上一轮 `mobile_field_material_review_decision` artifact/summary。
- 输出 `trashbot.mobile_field_material_retest_request.v1` artifact 和 summary-compatible payload。
- 所有 verdict 保持 `not_proven`，`delivery_success=false`，`primary_actions_enabled=false`。

责任 Engineer：Autonomy Algorithm Engineer。

### 建议 2：Robot diagnostics 只做 metadata-only consumer

具体证据：08-09 `tech-done.md` 写明 Robot diagnostics 已以 metadata-only / fail-closed 方式消费 review decision，且 command、ACK、cursor、persistence、Nav2、HIL、dropoff/cancel、delivery-success flags 均保持 false。本轮应延续同一边界到 retest request。

需要做：

- 在 `operator_gateway_diagnostics.py` 增加 `mobile_field_material_retest_request` / summary consumer。
- 支持 explicit ref、environment variable、diagnostics source。
- 建议 env 名：`TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST`。
- bad JSON、missing、unsupported schema、unsafe copy、success wording、boundary mismatch 必须 fail closed。
- 输出只进入 diagnostics / phone readiness metadata，不触发 robot command 或 ACK。

责任 Engineer：Robot Platform Engineer。

### 建议 3：Full-stack 在 `mobile/web` 增加只读 request panel

具体证据：`docs/product/mobile_user_flow.md` 已定义手机入口是普通用户唯一入口，现有 mobile PWA 多个现场材料 / 评审 / 交接 panel 均要求 read-only、phone-safe、`delivery_success=false`、`primary_actions_enabled=false`、不暴露 raw ROS topic、`/cmd_vel`、串口、WAVE ROVER、credentials、local path 或 complete artifact。08-09 `final.md` 也写明 review decision panel 不改变 Start / Confirm Dropoff / Cancel gating。

需要做：

- 在 `mobile/web` 增加“现场复测请求”只读 panel。
- 展示 source review decision、blockers、next-required-evidence、retest request、material checklist、owner handoff、safe `evidence_ref`、same-evidence-ref status、`not_proven`、evidence boundary。
- Copy/export 只允许 whitelist-safe copy。
- 缺 summary 时显示 blocked/not_proven。
- Start Delivery、Confirm Dropoff、Cancel gating 不变。

责任 Engineer：User Touchpoint Full-Stack Engineer。

### 建议 4：Product closeout 后置，按工程证据更新 OKR

具体证据：08-09 `final.md` 写明 Product closeout 只在 Full-stack、Robot、Autonomy 三个 worker 返回目标文件和 fence command 后更新 sprint closeout、`OKR.md` 与 `docs/process/okr_progress_log.md`。本阶段用户明确限定只做 plan，所以不能提前改 `OKR.md` 或 closeout 文档。

需要做：

- 等 A/B/C worker 返回实际改动和验证结果后，再更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 若验证通过，只能按 `software_proof_docker_mobile_field_material_retest_request_gate` 保守记录 O2/O3/O4 支撑；Objective 1 / 5 不上调。
- 如果任何 worker 缺 fail-closed 边界，Product closeout 不得更新 OKR 进度。

责任 Engineer：Product Manager / OKR Owner。

## 6. 优先级与验收口径

P0：Autonomy retest request gate

- 必须产出 artifact + summary。
- 必须保留 source review decision 与 same `evidence_ref`。
- 必须明确 blockers、next_required_evidence、route/elevator material checklist、owner handoff。
- 必须 fail closed，并固定 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

P0：Robot diagnostics metadata-only consumer

- 必须接受 artifact/summary，输出 phone-safe diagnostics metadata。
- 不得触发 command、ACK、cursor、persistence、Nav2/fixed-route、HIL、dropoff/cancel 或 delivery success。
- unsafe / missing / bad schema 必须 fail closed。

P0：Full-stack read-only request panel

- 必须只读展示 retest request。
- 缺 summary 时保持 blocked/not_proven。
- 不改变 Start / Confirm Dropoff / Cancel authorization。
- 不暴露 raw artifact、local path、credentials、ROS topic、硬件调试字段或 success wording。

P1：Product closeout

- 只在工程验证返回后更新 closeout / OKR / docs process。
- 明确本轮是 software proof，不是真实手机、route/elevator、HIL、O5 external proof 或 delivery success。

## 7. 风险、阻塞和证据链

- O5 阻塞：没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、worker/migration，本轮不能上调 Objective 5。
- O1 阻塞：没有真实 WAVE ROVER、UART、Orange Pi 串口、`T=1001` feedback 或 HIL，本轮不能上调 Objective 1。
- O2/O3 证据缺口：仍缺真实 route/elevator field retest、真实 Nav2/fixed-route runtime、真实 task record/completion signal、真实 dropoff/cancel completion、真实 delivery result。
- O4 证据缺口：仍缺真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice；mobile panel 只是 phone-safe support surface。
- 文案风险：任何“复测通过”“送达成功”“电梯成功”“HIL passed”“真实手机通过”都必须禁止，除非未来有真实证据链。

## 8. 需要创建或更新的 sprint / docs / OKR 文档

本 planning-only 阶段创建：

- `sprints/2026.05.16_09-10_mobile-field-material-retest-request/pre_start.md`
- `sprints/2026.05.16_09-10_mobile-field-material-retest-request/prd.md`
- `sprints/2026.05.16_09-10_mobile-field-material-retest-request/tech-plan.md`

后续实现完成后再更新：

- `sprints/2026.05.16_09-10_mobile-field-material-retest-request/tech-done.md`
- `sprints/2026.05.16_09-10_mobile-field-material-retest-request/side2side_check.md`
- `sprints/2026.05.16_09-10_mobile-field-material-retest-request/final.md`
- `docs/product/mobile_user_flow.md`
- `docs/interfaces/ros_contracts.md`
- `docs/navigation/fixed_route_workflow.md`
- `pc-tools/README.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

本阶段不更新以上后续文件。
