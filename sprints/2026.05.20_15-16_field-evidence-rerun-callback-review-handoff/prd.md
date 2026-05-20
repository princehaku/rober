# Sprint 2026.05.20_15-16 Field Evidence Rerun Callback Review Handoff - PRD

## 1. 用户价值

现场 owner 已经可以提交回执并获得 review decision，但仍需要一个明确交接包：谁负责补材料、缺口是什么、下一次 rerun 用什么命令、哪些 blocker 不能由手机用户处理。本轮把复核结论推进为只读 handoff，让现场支持、Robot diagnostics 和 mobile/web 看到同一份安全摘要，减少“复核完但不知道下一步”的灰区。

## 2. OKR 映射

- Objective 2：把电梯门、楼层、人工协助、dropoff/cancel completion 和 delivery result 的复核结论转成 owner handoff。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、field task record 和 same safe `evidence_ref` 的复核结论转成 rerun guidance。
- Objective 4：手机端只读展示现场证据复跑复核交接，不暴露 raw JSON、ROS topic、串口或控制授权。
- Objective 5：不推进；仍缺真实外部云 / 4G / OSS/CDN / DB / queue / production proof。
- Objective 1：不推进；仍缺 PR #5 `PRRT_kwDOSWB9286CJ3tX` 所需真实 2D LiDAR / ToF / HIL-entry materials 和 WAVE ROVER/UART/HIL 证据。

## 3. 范围

### In Scope

- 新增 PC gate `field_evidence_rerun_callback_review_handoff`。
- 新增 Robot diagnostics safe alias。
- 新增 mobile/web 只读 panel 和 fixture 显示。
- 更新 PC README、evidence contract、ROS contract、mobile user flow、sprint closeout、OKR 和 progress log。

### Out of Scope

- 真实 route/elevator field pass。
- 真实 Nav2/fixed-route runtime、真实电梯、真实 dropoff/cancel completion 或 delivery success。
- 真实手机/browser/PWA/userChoice 验收。
- O5 external proof。
- WAVE ROVER/UART/HIL 或 PR #5 thread resolution。

## 4. 验收口径

1. PC gate 能读取 `trashbot.field_evidence_rerun_callback_review_decision.v1` 或 summary / wrapper / nested JSON。
2. 输出 schema 为 `trashbot.field_evidence_rerun_callback_review_handoff.v1` 和 `trashbot.field_evidence_rerun_callback_review_handoff_summary.v1`。
3. 输出固定包含 `software_proof_docker_field_evidence_rerun_callback_review_handoff_gate`、`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
4. unsafe copy、raw path、credential、DB/queue URL、ROS topic、serial/UART/WAVE ROVER detail、success/control claim、`safe_to_control=true`、`delivery_success=true` 或 `primary_actions_enabled=true` 必须 fail closed。
5. Robot diagnostics 只读暴露 safe alias，不触发任何控制路径。
6. mobile/web 只读 panel 展示 handoff status、handoff owner/reason、next required evidence、rerun guidance 和 boundary；主操作 gating 不变。

## 5. 推荐下一步 OKR

本轮推荐继续深入 Objective 2 / Objective 3 / Objective 4 的现场证据复跑链，而不是 Objective 5 或 Objective 1：

- 证据 1：`OKR.md` 4.1 明确 O5 最低但受真实外部云材料阻断；继续本地 O5 metadata depth 不会提高 completion。
- 证据 2：PR #5 `PRRT_kwDOSWB9286CJ3tX` live 仍 unresolved，要求真实 vendor/source/material；本机没有真实硬件，不应再把 local reply wrapper 写成 O1 proof。
- 证据 3：最近三轮已形成 field evidence dispatch -> callback intake -> callback review decision 的连续链路；本轮 handoff 是 review decision 后的功能下一跳，能给现场 owner 可执行材料要求，而不是重复同一 blocker。
