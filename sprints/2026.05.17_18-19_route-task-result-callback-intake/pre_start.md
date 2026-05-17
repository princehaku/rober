# Sprint 2026.05.17_18-19 Route Task Result Callback Intake - Pre Start

sprint_type: epic

## 1. 启动结论

状态：`PLANNED_READY_FOR_TEAM_EXECUTION`。

本轮新建 fresh Epic sprint：`sprints/2026.05.17_18-19_route-task-result-callback-intake/`。核心抓手是 `route_task_field_retest_result_callback_intake`，接在上一轮 `route_task_field_retest_result_review_dispatch` 之后，消费现场 callback packet，并把 accepted / missing / rejected 材料状态更新成后续 review decision 可消费的安全 summary。

本轮仍只允许 Docker-only software proof。目标证据边界为 `software_proof_docker_route_task_field_retest_result_callback_intake_gate`，必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。它不是现场通过，不是真实手机/browser，不是 HIL，也不是 Objective 5 external proof。

## 2. 已读证据

- `AGENTS.md`：Epic sprint 必须有 `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md` 链路；实现和验证需由对应 Engineer 子 agent 执行，测试只围栏。
- `OKR.md` 4.1：Objective 5 约 68%，是数值最低 Objective；但只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof 才能继续提升。当前本机只有 Docker，不能推进 O5 completion。
- PR #4：`Add elevator-assisted delivery capability to agents, registry and OKR`，把 elevator-assisted delivery 写成主行为链与证据链。
- PR #5：`Make elevator-assisted delivery mandatory; update agents, OKR and hardware baseline`，明确单目 + 2D LiDAR + ToF 硬件基线；但真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料仍缺。
- 最新 sprint `sprints/2026.05.17_17-18_route-task-result-review-dispatch/final.md`：已完成 `route_task_field_retest_result_review_dispatch`，把 result backfill review decision 推进到现场 dispatch / owner work orders / callback packet requirements / rerun commands，剩余风险要求补真实现场材料。
- 最新 sprint `sprints/2026.05.17_17-18_route-task-result-review-dispatch/tech-done.md`：本轮边界是 `software_proof_docker_route_task_field_retest_result_review_dispatch_gate`，不是 real field pass / HIL / phone / O5 proof。
- `docs/product/mobile_user_flow.md`：mobile/web 的 route/elevator 材料类 panel 必须只读、phone-safe、copy/export 白名单、不得改变 Start Delivery / Confirm Dropoff / Cancel gating。

## 3. 用户价值和产品北极星

用户价值：现场支持在收到 dispatch work orders 后，可以按同一 `safe_evidence_ref` 回填 callback packet；系统能区分哪些材料已 accepted、哪些仍 missing、哪些 rejected，避免后续 review decision 再靠人工口头追问。

产品北极星：低成本 ROS2 自主垃圾投递机器人闭环。当前阶段的产品抓手不是再做 O5 本地 metadata，而是把 PR #4 route/elevator 证据链推进到“派发 -> 回调摄取 -> 复核决策”的可追踪闭环。

## 4. OKR 映射

- Objective 2：主目标。callback intake 让 route/elevator delivery 材料从 dispatch 要求进入安全摄取和 fulfilment 状态更新，继续推进可送垃圾任务 + elevator-assisted delivery 证据链。
- Objective 3：主目标。callback intake 要校验 Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result 是否与同一 `safe_evidence_ref` 对齐。
- Objective 4：支援目标。mobile/web 只读 panel 可展示 callback intake 状态，但不改变 primary action gating，也不证明真实手机。
- Objective 5：不推进。它仍是数值最低 Objective，但 Docker-only 无真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。
- Objective 1：不推进。PR #5 的 2D LiDAR / ToF 真实来源、采购、安装、接线、电源、标定和 HIL-entry 材料仍缺，本轮不包装该 blocker。

## 5. 本轮核心抓手

`route_task_field_retest_result_callback_intake`：

- 输入上一轮 dispatch artifact / summary，以及现场 callback packet 的安全样本或 Docker-only fixture。
- 校验 `safe_evidence_ref`、`owner_work_orders` fulfilment、`callback_packet_requirements` 完整性。
- 输出 accepted / missing / rejected 更新结果、owner follow-up、review decision handoff。
- 全程保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 6. Team 分工

- Autonomy Algorithm Engineer：实现 PC callback intake gate 和 focused fixture validation。
- Robot Platform Engineer：实现 diagnostics metadata-only consumer，保持 ROS2 task/action/control 语义不变。
- User Touchpoint Full-Stack Engineer：实现 mobile/web 只读 callback intake panel，copy/export 只允许 `safe_copy`。
- Product Manager / OKR Owner：维护 sprint closeout、OKR 边界和证据语言；本 planning 阶段不修改 `OKR.md`。

## 7. Blocker 扫描

最近两轮的真实 blocker 不是代码无法继续，而是外部证据不可得：O5 external proof 不可得，PR #5 真实硬件材料不可得，上一轮 O2/O3 route/elevator dispatch 仍需现场 callback materials。按“同一 blocker 不重复消费”规则，本轮不继续包装 O5 或 PR #5 硬件缺口，改推可在 Docker-only 中安全执行的 callback intake contract。

## 8. 需要创建或更新的 sprint 文档

本 planning 阶段创建：

- `sprints/2026.05.17_18-19_route-task-result-callback-intake/pre_start.md`
- `sprints/2026.05.17_18-19_route-task-result-callback-intake/prd.md`
- `sprints/2026.05.17_18-19_route-task-result-callback-intake/tech-plan.md`

实现完成后必须继续补齐：

- `sprints/2026.05.17_18-19_route-task-result-callback-intake/tech-done.md`
- `sprints/2026.05.17_18-19_route-task-result-callback-intake/side2side_check.md`
- `sprints/2026.05.17_18-19_route-task-result-callback-intake/final.md`
