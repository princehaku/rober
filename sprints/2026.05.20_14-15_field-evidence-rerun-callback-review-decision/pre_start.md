# Sprint 2026.05.20_14-15 Field Evidence Rerun Callback Review Decision - Pre Start

## 1. Sprint 声明

- `sprint_type: epic`
- 当前时间：2026-05-20 14:15 CST。
- 主题：`field_evidence_rerun_callback_review_decision`。
- 上一轮 sprint：`sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/`。
- 上一轮 final 已完成 `field_evidence_rerun_callback_intake`，边界为 `software_proof_docker_field_evidence_rerun_callback_intake_gate`。

本轮不创建第三个本地 blocker wrapper，也不重复 callback intake。目标是把 callback-intake output 转成明确的 callback review decision：`accepted`、`missing`、`rejected` 或 `blocked`，并给出 owner handoff、next required evidence 和 rerun guidance。

## 2. 用户价值和产品北极星

产品北极星仍是普通手机用户可以把垃圾交给小车，小车沿固定路线完成送达、电梯辅助、投放或人工取走，并且失败时普通用户知道下一步由谁补什么证据。

本轮用户价值是把“现场回执已摄取”推进到“现场回执已复核并可行动”。现场 owner、Robot diagnostics 和手机端不应只看到 accepted / missing / rejected / blocked 的原始 intake 分类，还要看到每类材料是否足以进入下一步、缺口归属给谁、需要重跑哪条命令或补哪类真实材料。

## 3. 背景证据

- `OKR.md` 4.1 当前最低 Objective 5 约 68%，但仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。本机只有 Docker，继续做同义 O5 metadata depth 不会改变最低 Objective 的真实缺口。
- Objective 1 约 81%，但 GitHub PR #5 thread `PRRT_kwDOSWB9286CJ3tX` live 仍 unresolved / material pending；`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` 已 resolved，manual reply `3269642220` 不是硬件 proof。
- 最新 `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/final.md` 已完成 `field_evidence_rerun_callback_intake`：PC gate、Robot diagnostics alias 和 mobile/web 只读 panel 已把现场 callback packet 转成 accepted / missing / rejected / blocked intake summary。
- 下一步应推进 `field_evidence_rerun_callback_review_decision`，把 intake output 转成 review decision、owner handoff、next required evidence、rerun guidance，仍保持 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 4. OKR 映射

| Objective | 当前状态 | 本轮关系 |
| --- | --- | --- |
| Objective 1 | 约 81%，PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending | 本轮只引用该缺口作为不提升 O1 的证据；不关闭 thread，不写硬件 proof。 |
| Objective 2 | 约 99%，仍缺真实电梯、dropoff/cancel completion、delivery result | 本轮把 O2 相关 callback-intake 输出转成复核结论和下一步真实材料要求。 |
| Objective 3 | 约 99%，仍缺真实 Nav2/fixed-route runtime log、route completion signal、field task record | 本轮明确 route/task 材料 accepted/missing/rejected/blocked 后的 rerun guidance。 |
| Objective 4 | 约 99%，仍缺真实手机/browser、production app、PWA prompt/userChoice | 本轮让 mobile/web 只读展示 callback review decision，不改变控制 gating。 |
| Objective 5 | 约 68%，仍缺外部公网/4G/OSS/CDN/DB/queue/worker/真实手机 external proof | 本轮不针对 O5，不继续堆同义本地 cloud metadata。 |

## 5. KR 拆解或更新

| KR | 本轮抓手 |
| --- | --- |
| O2 KR4 / KR5 / KR6 / KR7 | 将电梯门、楼层、人工协助、dropoff/cancel 和 delivery result 的 callback-intake 分类转成 review decision 和下一步现场材料要求。 |
| O3 KR3 / KR4 / KR5 | 将 route completion signal、field task record、Nav2/fixed-route runtime log 和 same `evidence_ref` 状态转成可复跑的 review decision。 |
| O4 KR5 / KR6 / KR7 | 手机端只读展示 review decision / owner handoff / rerun guidance，不显示 raw JSON、ROS topic 或控制授权。 |
| O1 KR1-KR5 | 不更新；`PRRT_kwDOSWB9286CJ3tX` 仍需真实硬件材料。 |
| O5 KR1-KR6 | 不更新；缺真实外部材料。 |

## 6. 本轮核心抓手

建立 `software_proof_docker_field_evidence_rerun_callback_review_decision_gate`：

- Autonomy 提供 PC review-decision gate，读取 `field_evidence_rerun_callback_intake` output，输出 review decision artifact / summary。
- Robot 提供 diagnostics safe alias `robot_diagnostics_field_evidence_rerun_callback_review_decision_summary`，只读暴露 review decision。
- Full-stack 在 mobile/web 增加只读 panel，展示 review decision、owner handoff、next required evidence、rerun guidance。
- Product closeout 在实现后更新 sprint 收口、`OKR.md` 和 progress log；如无真实材料，不提高 Objective 5、Objective 1 或 O2/O3/O4 的实机完成度。

固定证据边界和安全状态：

- `software_proof_docker_field_evidence_rerun_callback_review_decision_gate`
- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 7. Priority / Owner

| 优先级 | Owner | 责任 |
| --- | --- | --- |
| P0 | Autonomy Algorithm Engineer | PC review-decision gate、schema、tests、PC/evidence contract docs。 |
| P0 | Robot Platform Engineer | Robot diagnostics safe alias、blocked default summary、tests、ROS contract docs。 |
| P0 | User Touchpoint Full-Stack Engineer | mobile/web 只读 panel、fixtures、mobile tests、mobile user flow docs。 |
| P1 | Product Manager / OKR Owner | tech-done、side2side、final、OKR、progress log closeout。 |

## 8. 风险、阻塞和证据链

- 本机只有 Docker，没有真实公网、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker、真实手机/browser、真实路线、电梯或硬件材料。
- callback-intake output 可能为空、schema 不匹配、同一 `evidence_ref` 不一致、或只包含文字说明；review decision 必须 fail closed 到 `missing`、`rejected` 或 `blocked`。
- 不得把 `accepted` review decision 写成真实 route/elevator field pass、dropoff/cancel completion、delivery success、HIL、真实手机验收或 O5 external proof。
- 如果现场 owner 真正提交真实材料，Product closeout 才能在 final 和 `OKR.md` 中重新评估 OKR 百分比。

## 9. 需要创建或更新的 sprint 文档

本 planning task 只创建：

- `sprints/2026.05.20_14-15_field-evidence-rerun-callback-review-decision/pre_start.md`
- `sprints/2026.05.20_14-15_field-evidence-rerun-callback-review-decision/prd.md`
- `sprints/2026.05.20_14-15_field-evidence-rerun-callback-review-decision/tech-plan.md`

实现和收口阶段后续再更新：

- `sprints/2026.05.20_14-15_field-evidence-rerun-callback-review-decision/tech-done.md`
- `sprints/2026.05.20_14-15_field-evidence-rerun-callback-review-decision/side2side_check.md`
- `sprints/2026.05.20_14-15_field-evidence-rerun-callback-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
