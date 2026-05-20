# Sprint 2026.05.20_13-14 Field Evidence Rerun Callback Intake - Pre Start

## 1. Sprint 声明

- `sprint_type: epic`
- 当前时间：2026-05-20 13:02 CST。
- 主题：`field_evidence_rerun_callback_intake`。
- 上一轮 sprint：`sprints/2026.05.20_12-13_field-evidence-rerun-material-dispatch/`。
- 上一轮 final 已完成 `field_evidence_rerun_material_dispatch`，边界为 `software_proof_docker_field_evidence_rerun_material_dispatch_gate`。

本轮不重复 dispatch，不再生成同义 owner work order。目标是只读接收现场 owner 返回的 callback packet，校验是否满足上一轮派发包要求，并输出 accepted / missing / rejected / blocked 的 intake summary。

## 2. 用户价值和产品北极星

北极星仍是普通手机用户可以把垃圾交给小车，小车沿固定路线完成送达、电梯辅助、投放或人工取走，并且失败时普通用户知道下一步需要谁补什么证据。

本轮用户价值不是新增控制能力，而是把现场复跑材料从“已派发”推进到“可回执、可校验、可复盘”。这能让现场 owner 提交的 route completion signal、field task record、Nav2/fixed-route runtime log、电梯门/楼层/人工协助 summaries、dropoff/cancel completion、delivery result、真实手机/browser evidence 被统一判定为 accepted / missing / rejected / blocked，避免工程同学在不同入口重复解释同一缺口。

## 3. 背景证据

- `OKR.md` 4.1 显示 Objective 5 仍是最低约 68%，但仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof；本机只有 Docker，不得继续堆同义 O5 local metadata。
- Objective 1 约 81%，PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending。GitHub review thread evidence shows Q/U resolved, X unresolved，且最新 manual reply `3269642220` 仍不是真实硬件证明。
- 最新 12-13 sprint 已把真实 route completion signal、field task record、Nav2/fixed-route runtime log、电梯门/楼层/人工协助 summaries、dropoff/cancel completion、delivery result、真实手机/browser evidence 转成 owner work orders、rerun commands 和 callback packet requirements。
- 下一步是接收和校验 callback packet，而不是重复派发同一组材料要求。

## 4. OKR 映射

| Objective | 当前状态 | 本轮关系 |
| --- | --- | --- |
| Objective 1 | 约 81%，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending | 只保留缺口可见性；除非真实 2D LiDAR / ToF 或 WAVE ROVER/UART/HIL 材料实际出现，否则不提升。 |
| Objective 2 | 约 99%，仍缺真实电梯、dropoff/cancel completion、delivery result | 本轮接收 route/elevator field rerun callback packet，形成 intake summary，但保持 `not_proven`。 |
| Objective 3 | 约 99%，仍缺真实 Nav2/fixed-route runtime log、route completion signal 和 field task record | 本轮校验这些材料是否在 callback packet 中出现且同一 safe `evidence_ref` 对齐。 |
| Objective 4 | 约 99%，仍缺真实手机/browser、production app 和 PWA prompt/userChoice | 本轮只在 mobile/web 计划只读显示 callback intake summary，不改变控制 gating。 |
| Objective 5 | 约 68%，仍缺外部公网/4G/OSS/CDN/DB/queue/worker/真实手机 external proof | 本轮不针对 O5，不继续堆同义本地 cloud metadata。 |

## 5. Repeated Blocker Rationale

Objective 5 已多轮停在外部材料缺失：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof 均不在本机 Docker 环境内。继续做同义 O5 local metadata 会重复消费同一根因 blocker。

Objective 1 的 `PRRT_kwDOSWB9286CJ3tX` 仍需要真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 或真实 WAVE ROVER/UART/HIL evidence。manual reply `3269642220` 和本地 PR closeout packet 不能替代真实硬件材料。

因此本轮切换到 O2/O3/O4 的现场证据回执链：上一轮已 dispatch，本轮只读 intake callback packet，判断哪些材料 accepted、missing、rejected 或 blocked。该切换不宣称 OKR 百分比提升，只减少现场材料回填和复跑之间的产品/工程摩擦。

## 6. 本轮核心抓手

建立 `software_proof_docker_field_evidence_rerun_callback_intake_gate`：

- Autonomy 提供 PC gate，读取 dispatch summary 和 callback packet，输出 `field_evidence_rerun_callback_intake` artifact / summary。
- Robot 提供 diagnostics safe alias `robot_diagnostics_field_evidence_rerun_callback_intake_summary`，只读暴露 intake summary。
- Full-stack 在 mobile/web 增加只读 panel，展示 accepted / missing / rejected / blocked 和下一步材料要求。
- Product closeout 在实现后只更新 sprint 收口文档、`OKR.md` 和 `docs/process/okr_progress_log.md`，如无真实材料则不提升 OKR 百分比。

固定证据边界和安全状态：

- `software_proof_docker_field_evidence_rerun_callback_intake_gate`
- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 7. Owner 和下一步

| Owner | 责任 |
| --- | --- |
| Autonomy Algorithm Engineer | 实现 PC callback intake gate、测试、PC README、evidence contract 文档。 |
| Robot Platform Engineer | 实现 `operator_gateway_diagnostics.py` safe alias、测试、ROS contract 文档。 |
| User Touchpoint Full-Stack Engineer | 实现 mobile/web 只读 panel、fixture、mobile tests、mobile user flow 文档。 |
| Product Manager / OKR Owner | 收口 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。 |

## 8. 风险、阻塞和证据链

- 本机只有 Docker，没有真实硬件、真实电梯、真实路线、真实手机/browser 或真实外部云材料。
- callback packet 可能为空、缺字段、schema 不匹配、safe `evidence_ref` 不一致，必须 fail closed 到 blocked / missing / rejected。
- 不得把 callback intake summary 写成 route/elevator field pass、delivery success、dropoff/cancel completion、HIL、真实手机验收或 O5 external proof。
- 如果现场 owner 真正提交真实材料，Product closeout 才能在 final 和 `OKR.md` 中重新评估是否产生 OKR 百分比变化。

## 9. 需要创建或更新的 sprint 文档

本 planning task 只创建：

- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/pre_start.md`
- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/prd.md`
- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/tech-plan.md`

实现和收口阶段后续再更新：

- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/tech-done.md`
- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/side2side_check.md`
- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
