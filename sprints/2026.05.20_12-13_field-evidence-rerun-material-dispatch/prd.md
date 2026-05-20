# Sprint 2026.05.20_12-13 Field Evidence Rerun Material Dispatch - PRD

## 1. 用户价值和产品北极星

用户价值：现场 owner 能拿到一个同一 safe `evidence_ref` 下的真实材料 rerun 派发包，知道必须回填或重跑哪些材料、由谁负责、下游如何验收。普通手机用户和支持同学只看到只读、安全、中文可解释的材料状态，不会把 metadata 或 ACK 当成真实送达。

产品北极星：rober 的核心是普通手机用户可用的低成本自主垃圾投递闭环。证据链必须能区分“本地软件证明”和“真实现场通过”，避免在 O5 云、O1 硬件、O4 手机或 route/elevator 真实材料缺失时虚增 OKR。

## 2. OKR 映射

主映射：

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。本轮把真实 route/elevator rerun 必需材料列成派发包，但不证明真实送达。
- Objective 3：可验证导航与固定路线。本轮要求真实 Nav2/fixed-route runtime log、route completion signal 和 task record 保持同一 safe `evidence_ref`。
- Objective 4：手机用户体验与低成本量产边界。本轮让 mobile/web 只读展示现场材料派发状态和 next required evidence，但不证明真实手机/browser。

受限映射：

- Objective 5 当前约 68%，最低，但只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料才能继续提高。本轮不得提高 O5。
- Objective 1 当前约 81%，次低，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending。Q/U 已 resolved；reply publication 或 vendor-source citation reply 不等于 O1 提升。本轮不得提高 O1。

## 3. KR 拆解

### KR-A：PC evidence gate

Autonomy 产出 `field_evidence_rerun_material_dispatch` gate，输入最近 route/elevator rerun review handoff、real-material followup/escalation/status 或兼容 summary，输出现场 owner 可执行材料派发包。

必须列出：

- 真实 route completion signal。
- 真实 field task record。
- 真实 Nav2/fixed-route runtime log。
- 真实 elevator door summary。
- 真实 target floor / floor arrival summary。
- 真实 human-assistance summary。
- 真实 dropoff completion 或 cancel completion。
- 真实 delivery result。
- 真实手机/browser evidence。
- 同一 safe `evidence_ref` 约束、owner、rerun command、material callback packet 要求。

### KR-B：Robot diagnostics safe alias

Robot 输出 `robot_diagnostics_field_evidence_rerun_material_dispatch_summary`，只读消费 PC gate summary 或兼容 artifact，保持 fail-closed。Robot 不触发 `/cmd_vel`、Nav2 runtime、serial/UART、WAVE ROVER、HIL、ACK、cursor、collect/dropoff/cancel。

### KR-C：Mobile web 只读 panel

Full-stack 在 mobile/web 加“现场证据复跑材料派发”panel，展示 owner handoff、missing material groups、rerun guidance、same safe `evidence_ref`、evidence boundary、`not_proven`，并保持 Start Delivery / Confirm Dropoff / Cancel gating 不变。

### KR-D：Product closeout

Product 收口时更新当前 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`，并按证据边界更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。如果没有真实材料，OKR 百分比保持保守不变。

## 4. 本轮核心抓手

`field_evidence_rerun_material_dispatch` 是一个跨 owner 受控派发包。它的核心不是再加一层“已交接”的本地 wrapper，而是把真实现场必须补齐的材料和 rerun 命令明确给 Autonomy、Robot、mobile 三方：

- Autonomy 决定真实 field rerun 的材料清单和 gate。
- Robot 只读消费 safe alias，防止下游误认为可以控制。
- mobile/web 用用户可读语言展示缺口和下一步。
- Product closeout 保持 OKR 不虚增，并记录真实材料到位前的剩余风险。

## 5. 需要做什么

实现阶段需要并行启动 3 个 Engineer worker：

- Autonomy Algorithm Engineer：新增 PC evidence gate 和 focused test。
- Robot Platform Engineer：新增 diagnostics safe alias、focused test 和 `docs/interfaces/ros_contracts.md`。
- User Touchpoint Full-Stack Engineer：新增 mobile/web panel、fixture/test 和 `docs/product/mobile_user_flow.md`。

Product 在工程 worker 回传后做 closeout：

- 汇总实际改动和验证结果。
- 更新 sprint closeout docs。
- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`，但只写软件证明层收益。

## 6. 优先级和验收口径

优先级 P0：

- 同一 safe `evidence_ref` 必须贯穿 PC gate、Robot safe alias 和 mobile/web panel。
- 输出必须固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 缺输入、坏 JSON、unsupported schema、unsafe copy、evidence_ref mismatch、success phrasing 或真实 pass claim 必须 fail closed。

优先级 P1：

- Robot/mobile 消费必须只读，不能改变控制按钮状态。
- docs 同步必须覆盖接口和手机流程。
- 验收命令必须围栏，不跑 broad regression。

验收完成条件：

- PC gate、Robot diagnostics、mobile/web 三方都能用 focused tests 证明 fail-closed behavior。
- `rg` 能在工程文件、tests、docs、sprint docs 中找到 gate 名、safe alias、forbidden-claim guard 和固定 false 状态。
- `git diff --check` scoped to touched paths 通过。

## 7. 风险、阻塞和证据链

风险：

- 如果现场 owner 仍不提交真实材料，本轮只能输出派发包，不能证明现场通过。
- 如果后续 worker 把 ACK、reply publication、review handoff 或 local fixture 写成真实 pass，必须回退到 fail-closed 文案。
- 如果 PC gate 输入 family 命名混用旧 route-task callback-intake，可能造成 Robot/mobile 消费错 schema。

证据链：

- `OKR.md` 4.1：Objective 5 约 68%，Objective 1 约 81%，O2/O3/O4 仍缺真实现场材料。
- PR #5 `PRRT_kwDOSWB9286CJ3tX`：unresolved / `is_resolved=false` / material pending。
- 最新 O4 sprint final：`mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff` 只推进 phone-safe handoff chain，不提高 OKR。
- 2026-05-18 route/elevator rerun chain 与 2026-05-19 real-material followup/escalation/status：下一步需要真实现场 owner 提交材料。

## 8. 需要创建或更新的 sprint 文档

Planning 阶段：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现和收口阶段：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
