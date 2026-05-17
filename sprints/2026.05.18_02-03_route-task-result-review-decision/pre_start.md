# Sprint 2026.05.18_02-03 Route Task Result Review Decision - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动 `route_task_field_retest_result_review_decision`，承接上一轮 `route_task_field_retest_result_review_intake`。目标不是继续包装最低数值 Objective 5，也不是继续消费 Objective 1 的真实 WAVE ROVER HIL packet blocker，而是把 PR #4 的 route/elevator result chain 推进到可执行的复核决策层：哪些 intake 材料可进入 acceptance/backfill，哪些缺失必须补，哪些 evidence_ref mismatch 必须 rerun，哪些 owner 需要接手。

证据边界固定为 `software_proof_docker_route_task_field_retest_result_review_decision_gate`。本轮只能声明 Docker-only / PC-only / metadata-only / read-only mobile software proof，必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 近期证据

- PR #4：elevator-assisted delivery 已成为必须能力，route/elevator evidence chain 是当前主线；因此本轮继续围绕真实路线、电梯、任务记录和投放/取消结果的证据链做决策层，而不是回到纯规划。
- PR #5 review：`docs/product/production_hardware_boundary.md` 曾出现默认硬件集与 mandatory `monocular + 2D LiDAR + ToF` baseline 的矛盾；新增 sensor baseline 又缺 `docs/vendor/` source。这说明硬件材料仍需真实 source、receipt、install、calibration 和 HIL-entry 证据，不能继续本地包装成硬件完成。
- 最新 sprint `2026.05.18_01-02_route-task-result-review-intake/final.md`：已完成 result review intake，但仍缺真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record/completion signal、dropoff/cancel completion 和 delivery result；下一步应进入 result review decision。
- `OKR.md` 4.1：Objective 5 仍约 68%，但缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser external proof；Objective 1 约 81%，但最近三轮已消费同一真实 WAVE ROVER HIL packet blocker。

## 3. 用户价值和产品北极星

用户价值：现场或支持同学拿到 result review intake 后，不应再靠人工翻聊天判断“能不能继续复核”。系统需要把 intake 材料转成明确 review decision：进入后续 result acceptance/backfill、补齐材料、拒绝 unsafe evidence_ref、或生成 rerun 指令。

产品北极星：把低成本 ROS2 垃圾投递机器人推进到“真实路线/电梯/任务结果材料可复核、可追责、可回填”，但不越过真实硬件、真实现场、真实手机和真实外部云证据边界。

## 4. OKR 映射

- Objective 2：主目标。PR #4 route/elevator 必须能力需要从 intake 进入 review decision，明确真实门状态、楼层确认、人工协助、dropoff/cancel completion 和 delivery result 缺口。
- Objective 3：主目标。Nav2/fixed-route runtime log、route completion signal、task record 和同一 safe `evidence_ref` 的复核决策，是固定路线能力从材料入口走向结果验收的下一步。
- Objective 4：受益目标。手机/Web/diagnostics 后续只读展示 review decision，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- Objective 5：不作为本轮目标。缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof。
- Objective 1：不作为本轮目标。最近三轮已围绕同一 WAVE ROVER HIL packet blocker 做 intake、review decision、execution pack；没有真实 WAVE ROVER/UART/HIL packet 时不继续消费。

## 5. 本轮核心抓手

新增 `route_task_field_retest_result_review_decision`，把上一轮 intake 的 missing materials、review-ready package、rerun package 和 safe `evidence_ref` 转成决策输出：

- `ready_for_result_acceptance_backfill_not_proven`
- `needs_route_elevator_material_backfill_not_proven`
- `evidence_ref_mismatch_rerun_not_proven`
- `blocked_missing_result_review_intake_not_proven`
- `unsupported_result_review_intake_schema_not_proven`

任何状态都不得表示真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 dropoff/cancel completion、真实 delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 6. 责任 Engineer

- Autonomy Algorithm Engineer：主责 PC evidence gate 与 route/elevator result decision 规则，保证 Nav2/fixed-route、route completion signal、task record、dropoff/cancel completion 和 delivery result 缺口被明确分类。
- Robot Platform Engineer：负责 Robot diagnostics metadata-only consumer，保证 ROS2/diagnostics 只读暴露 review decision，不产生控制动作。
- User Touchpoint Full-Stack Engineer：负责 mobile/web 只读 panel 和 fixture，保证 phone-safe copy、Start/Confirm/Cancel gating 不变。
- Product Manager / OKR Owner：负责 sprint planning、验收口径、OKR 边界和最终 closeout，不把软件证明写成真实现场通过。

## 7. 风险、阻塞和证据链

- 阻塞：本机仍是 Docker-only，没有真实电梯、真实 Nav2/fixed-route、真实 task record、真实 completion signal、真实 dropoff/cancel completion、真实 WAVE ROVER/UART/HIL、真实手机/browser、真实公网 HTTPS/TLS、真实 4G/SIM、真实 OSS/CDN live traffic 或 production DB/queue。
- PR #5 硬件材料仍缺真实 2D LiDAR / ToF source、receipt、procurement、install、wiring、power、calibration 和 HIL-entry；本轮只在证据边界中引用该风险，不替代硬件履约。
- 成功口径：新增 planning 后，Engineer 可按 `tech-plan.md` 拆分实现；后续实现必须更新 `tech-done.md`、`side2side_check.md`、`final.md` 和相关 `docs/`。

## 8. 本轮需创建或更新的 sprint 文档

- `sprints/2026.05.18_02-03_route-task-result-review-decision/pre_start.md`
- `sprints/2026.05.18_02-03_route-task-result-review-decision/prd.md`
- `sprints/2026.05.18_02-03_route-task-result-review-decision/tech-plan.md`

后续实现完成后必须继续补齐 `tech-done.md -> side2side_check.md -> final.md`，并按实际 durable work 更新 `OKR.md` 与相关 `docs/`。
