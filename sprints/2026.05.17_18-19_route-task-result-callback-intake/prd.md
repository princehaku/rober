# Sprint 2026.05.17_18-19 Route Task Result Callback Intake - PRD

sprint_type: epic

## 1. 用户价值和产品北极星

用户价值：现场支持按上一轮 dispatch 的 owner work orders 回填 callback packet 后，产品能立即判断同一 `safe_evidence_ref` 下哪些材料已 accepted、哪些仍 missing、哪些 rejected，需要谁补、补什么、下一轮 review decision 能否继续。

产品北极星：把低成本 ROS2 垃圾投递机器人从“本地 dry-run 证据”推进到“真实 route/elevator field materials 可回填、可复核、可追责”的闭环。当前 PRD 聚焦证据摄取，不证明真实送达。

## 2. 背景证据

- `OKR.md` 4.1 显示 Objective 5 约 68%，是数值最低 Objective；但当前 Docker-only 环境缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof，因此本轮不能提升 Objective 5。
- PR #4 已把 elevator-assisted delivery 写成主行为链和证据链；当前最有价值的路线是继续推进 route/elevator materials。
- PR #5 已明确单目 + 2D LiDAR + ToF 硬件基线，但真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍缺；本轮不把该缺口包装成硬件进展。
- 上一轮 `route_task_field_retest_result_review_dispatch` 已产出 owner work orders、callback packet requirements 和 rerun commands；下一步自然承接为 `route_task_field_retest_result_callback_intake`。
- 上一轮 tech-done 明确 `software_proof_docker_route_task_field_retest_result_review_dispatch_gate` 不是 real field pass / HIL / phone / O5 proof；本轮必须延续这个证据边界。

## 3. 目标

本轮交付 `route_task_field_retest_result_callback_intake` 的 PC / Robot / mobile 三面闭环规划和实现：

- 摄取 dispatch 后的 callback packet。
- 校验 packet 是否绑定同一 `safe_evidence_ref`。
- 校验 callback packet 是否覆盖 `owner_work_orders` 和 `callback_packet_requirements`。
- 输出 accepted / missing / rejected 的更新结果。
- 给后续 review decision 提供安全 summary 和 rerun / owner follow-up。
- 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. 非目标

- 不证明真实 route/elevator field pass。
- 不证明真实 Nav2/fixed-route 运行。
- 不证明真实 route completion signal、task record 或 delivery result。
- 不证明真实手机/browser、production app 或 PWA prompt/user choice。
- 不证明 WAVE ROVER、UART、HIL 或 Objective 1。
- 不推进 Objective 5 external proof。
- 不改变 Start Delivery / Confirm Dropoff / Cancel gating。

## 5. KR 拆解或更新

KR-A Autonomy callback intake gate：

- 输入 dispatch artifact / summary 和 callback packet safe sample / fixture。
- 校验 schema、boundary、`safe_evidence_ref`、work order fulfilment 和 callback requirements。
- 输出 `trashbot.route_task_field_retest_result_callback_intake.v1` / `_summary.v1`。

KR-B Robot diagnostics metadata-only consumer：

- 从 file / env / diagnostics summary 安全读取 callback intake summary。
- 对 schema mismatch、unsafe evidence ref、missing summary、success/control claim fail closed。
- 不改变 task_orchestrator、action server、Start、Dropoff、Cancel、ACK、Nav2 或 HIL 控制语义。

KR-C Full-stack read-only panel：

- 在 mobile/web 呈现 callback intake status、accepted / missing / rejected updates、owner follow-up、safe evidence ref、boundary flags 和 `not_proven`。
- copy/export 仅使用 backend-provided `safe_copy`；缺失时显示 `blocked copy unavailable`。
- `delivery_success=false`、`primary_actions_enabled=false` 必须在 UI copy 中保留。

KR-D Product closeout：

- 在实现后更新 `tech-done.md`、`side2side_check.md`、`final.md`。
- 如 durable work landed，再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`；本 planning 阶段不得修改 `OKR.md`。

## 6. 优先级

P0：

- `safe_evidence_ref` 与上一轮 dispatch 一致。
- `owner_work_orders` fulfilment 和 `callback_packet_requirements` 被明确校验。
- callback intake summary 必须 fail closed，禁止 delivery success / primary action enabled。
- PC / Robot / mobile 都只消费 safe summary，不暴露 raw artifact、local path、checksum、credentials、ROS topic、serial/UART 细节或 WAVE ROVER 参数。

P1：

- accepted / missing / rejected 更新结果可被后续 review decision 直接消费。
- rerun commands 和 owner follow-up 使用安全摘要，不要求真实硬件。
- mobile copy 维持中文优先、现场支持可读。

P2：

- 保留 sample / fixture 便于 Docker-only fenced verification。

## 7. 验收口径

验收必须同时满足：

- 产物命名和 schema 包含 `route_task_field_retest_result_callback_intake`。
- 证据边界包含 `software_proof_docker_route_task_field_retest_result_callback_intake_gate`。
- 所有输出包含或透传 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- callback packet 能根据 dispatch requirements 更新 accepted / missing / rejected。
- Robot diagnostics 和 mobile/web 只能显示 metadata-only / phone-safe summary。
- 围栏验证通过；不得使用 broad regression sweep 替代 scoped commands。

## 8. 对应责任 Engineer

- Autonomy Algorithm Engineer：callback intake PC gate、sample/fixture、focused unit validation、evidence contract doc。
- Robot Platform Engineer：diagnostics metadata-only consumer、focused diagnostics tests、ROS contract doc。
- User Touchpoint Full-Stack Engineer：mobile/web read-only panel、fixture、focused mobile test、product doc。
- Product Manager / OKR Owner：sprint closeout、OKR 边界、progress log 和验收复盘。

## 9. 风险、阻塞和需要补齐的证据链

- 当前无真实硬件，只有 Docker；不能把 sample / fixture 写成真实 field pass。
- O5 仍最低，但缺真实 external proof；不能靠本轮提升 Objective 5。
- PR #5 硬件材料仍缺真实 source / receipt / procurement / installation / wiring / power / calibration / HIL-entry。
- 后续仍需真实现场 callback packet：真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery result。
- 若 callback packet 不满足同一 `safe_evidence_ref`，后续 review decision 必须 blocked。
