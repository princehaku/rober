# Sprint 2026.05.17_12-13 Route Task Handoff Result Intake Bridge - Side2Side Check

sprint_type: epic

## 1. 验收结论

本轮 Product side2side 验收通过。工程结果与 PRD / tech-plan 的核心口径一致：review-result handoff 可以进入既有 result-intake gate，输出仍是 result-intake schema 和 `software_proof_docker_route_task_field_retest_result_intake_gate`，并保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 需求对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 支持 `route_task_field_retest_review_result_handoff` artifact / summary | 通过 | Task A 新增 `trashbot.route_task_field_retest_review_result_handoff.v1` / `_summary.v1` 来源支持。 |
| 支持 wrapper / nested JSON | 通过 | Task A source candidate 白名单新增 wrapper key 和 nested JSON key。 |
| 输出保持 result-intake schema | 通过 | 输出仍为 `trashbot.route_task_field_retest_result_intake.v1` / `_summary.v1`。 |
| evidence boundary 不漂移 | 通过 | 输出仍为 `software_proof_docker_route_task_field_retest_result_intake_gate`。 |
| 八类 result materials 不被 upstream 裁剪 | 通过 | Task A 保留 nav/runtime、completion signal、task record、door state、target floor confirmation、human assistance、dropoff/cancel、delivery result 八类材料。 |
| Robot 只读消费不授权动作 | 通过 | Task B 证明 diagnostics consumer 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。 |
| Mobile 只读展示不改 gating | 通过 | Task C 未改 `app.js` / `styles.css`，Start Delivery / Confirm Dropoff / Cancel gating 未变。 |
| Objective 5 不借本轮上调 | 通过 | 本轮没有真实 external proof，OKR closeout 保持 Objective 5 约 68%。 |

## 3. OKR side2side

- Objective 2：从约 92% 到约 93%。证据是 PR #4 route/elevator review-result handoff 已被 result-intake gate 消费，后续真实 door state、target floor confirmation、human assistance note、dropoff/cancel completion、delivery result 可以进入同一 result-intake contract。
- Objective 3：从约 92% 到约 93%。证据是 Nav2/fixed-route runtime log、route completion signal、task record 等 result materials 继续由 result-intake gate 固定要求，没有因 handoff schema 被裁剪。
- Objective 5：保持约 68%。证据是本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实手机/browser，因此不构成 Objective 5 external proof。

## 4. 证据边界

本轮不是：

- 真实 route/elevator field pass。
- 真实 Nav2/fixed-route runtime pass。
- 真实 route completion signal 或 task record。
- 真实电梯门状态、目标楼层确认或人工协助记录。
- 真实 dropoff/cancel completion 或 delivery success。
- 真实手机/browser、production app 或 PWA prompt/user choice。
- WAVE ROVER、真实串口/UART、HIL。
- Objective 5 external proof。
- PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。

## 5. 需要 CEO/现场补齐的证据

下一步若要把 OKR 从 software proof 推到真实闭环，必须补齐至少一组真实现场材料：同一 `evidence_ref` 的 Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff_or_cancel_completion、delivery_result。若要推进 Objective 5，则必须提供真实 external proof，而不是继续新增本地 metadata wrapper。
