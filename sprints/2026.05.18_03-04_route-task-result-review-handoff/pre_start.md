# Sprint 2026.05.18_03-04 Route Task Result Review Handoff - Pre Start

sprint_type: epic

## 1. 启动结论

本轮启动 `route_task_field_retest_result_review_handoff`，承接最新 sprint `sprints/2026.05.18_02-03_route-task-result-review-decision/final.md` 的 `route_task_field_retest_result_review_decision`。目标不是继续包装 Objective 5 本地 metadata，也不是第四轮消费 Objective 1 的真实 WAVE ROVER / HIL packet blocker，而是把 result review decision 转成 Autonomy、Robot、Full-stack 可直接执行的 handoff package。

本轮 planning 只创建 `pre_start.md`、`prd.md`、`tech-plan.md`。后续实现证据边界固定为 `software_proof_docker_route_task_field_retest_result_review_handoff_gate`，必须保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 近期证据

- `OKR.md` 4.1：Objective 5 约 68%，是当前数值最低 Objective；但本机 Docker-only，缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof，O5 stop rule 继续成立。
- `OKR.md` 4.1：Objective 1 约 81%；但最近 `2026.05.17_21-22_wave-rover-hil-packet-intake`、`2026.05.17_22-23_wave-rover-hil-packet-review-decision`、`2026.05.17_23-24_wave-rover-hil-packet-execution-pack` 已连续消费真实 WAVE ROVER/HIL packet blocker，本机没有真实硬件，不能继续本地包装。
- 最新 `sprints/2026.05.18_02-03_route-task-result-review-decision/final.md`：下一步需要真实现场 review decision 回填材料和同一 `evidence_ref` 上车复账；仍缺真实门状态、楼层确认、人工协助、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 和 delivery result。
- PR #4：`Add elevator-assisted delivery capability to agents, registry and OKR` 已合并；Testing 明确 no runtime integration tests，说明 route/elevator 仍需要继续结果材料链，不能把 schema/fixture 当现场完成。
- PR #5 review comments：P1 default hardware set 与 mandatory `monocular + 2D LiDAR + ToF` baseline 矛盾；P2 mandatory sensor assumptions 缺 `docs/vendor/` source；P2 lowest-objective narrative 曾误导 routing。本 sprint 保留这些作为边界，不解决真实 sensor/HIL 材料。

## 3. 用户价值和产品北极星

用户价值：现场支持同学拿到 result review decision 后，需要一包可执行交接材料，清楚知道哪些材料 accepted、哪些 blocked、哪些需要 rerun、哪个 owner 接手、下一次 callback 必须带什么材料，以及如何用同一 safe `evidence_ref` 复跑。

产品北极星：把低成本 ROS2 垃圾投递机器人推进到“真实路线/电梯/任务结果材料可交接、可复核、可回填、可追责”，但不越过真实硬件、真实现场、真实手机和真实外部云证据边界。

## 4. OKR 映射

- Objective 2：主目标。把 route/elevator result review decision 转成 owner work orders、accepted/blocked/rerun reasons、next material callback requirements，让 delivery 闭环材料能进入下一次现场回填。
- Objective 3：主目标。要求 Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion 与 delivery result 在同一 safe `evidence_ref` 下进入 handoff package。
- Objective 4：受益目标。Robot diagnostics 和 mobile/web 后续只读展示 handoff status，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- Objective 5：不作为本轮目标。缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof。
- Objective 1：不作为本轮目标。最近三轮已围绕同一 WAVE ROVER/HIL packet blocker 做 intake、review decision、execution pack；没有真实 WAVE ROVER/UART/HIL packet 时不继续消费。

## 5. 本轮核心抓手

新增 `route_task_field_retest_result_review_handoff`，把上一轮 decision 的 accepted / blocked / rerun 结论转成 owner 可执行 package：

- handoff status 和 package status。
- owner work orders：Autonomy / Robot / Full-stack / Product 后续动作边界。
- accepted / blocked / rerun reasons。
- same-evidence-ref package 与 mismatch fail-closed 规则。
- next material callback requirements。
- rerun commands 和 next required evidence。

任何状态都不得表示真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 dropoff/cancel completion、真实 delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 6. 责任 Engineer

- Autonomy Algorithm Engineer：主责 PC evidence handoff gate、same-evidence-ref package、route/elevator material work orders 和 focused unittest。
- Robot Platform Engineer：负责 Robot diagnostics metadata-only consumer，保证 ROS2/diagnostics 只读暴露 handoff status，不产生控制动作。
- User Touchpoint Full-Stack Engineer：负责 mobile/web 只读 panel 和 fixture，保证 phone-safe copy、Start/Confirm/Cancel gating 不变。
- Product Manager / OKR Owner：负责 sprint planning、验收口径、OKR 边界和最终 closeout，不把软件证明写成真实现场通过。

## 7. 风险、阻塞和证据链

- 阻塞：本机仍是 Docker-only，没有真实电梯、真实 Nav2/fixed-route、真实 task record、真实 completion signal、真实 dropoff/cancel completion、真实 WAVE ROVER/UART/HIL、真实手机/browser、真实公网 HTTPS/TLS、真实 4G/SIM、真实 OSS/CDN live traffic 或 production DB/queue。
- PR #5 硬件材料仍缺真实 2D LiDAR / ToF source、receipt、procurement、install、wiring、power、calibration 和 HIL-entry；本轮只在证据边界中引用该风险，不替代硬件履约。
- 成功口径：本轮 planning 完成后，Engineer 可按 `tech-plan.md` 并行实现；后续实现必须更新 `tech-done.md`、`side2side_check.md`、`final.md` 和相关 `docs/`。

## 8. 本轮需创建或更新的 sprint 文档

- `sprints/2026.05.18_03-04_route-task-result-review-handoff/pre_start.md`
- `sprints/2026.05.18_03-04_route-task-result-review-handoff/prd.md`
- `sprints/2026.05.18_03-04_route-task-result-review-handoff/tech-plan.md`

后续实现完成后必须继续补齐 `tech-done.md -> side2side_check.md -> final.md`，并按实际 durable work 更新 `OKR.md` 与相关 `docs/`。
