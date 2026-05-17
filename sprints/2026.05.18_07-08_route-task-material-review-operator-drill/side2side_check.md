# Sprint 2026.05.18_07-08 Route Task Material Review Operator Drill - Side2Side Check

sprint_type: epic

## 1. 验收口径对照

| Owner | 计划验收口径 | 实际结果 | Product 判定 |
| --- | --- | --- | --- |
| A / Autonomy | `route_task_field_retest_operator_drill` 支持 `route_task_field_retest_material_callback_review_decision` artifact / summary / wrapper / nested diagnostics，并保留 material pack 兼容。 | 已完成。A worker 报告 operator drill 优先消费 review decision，保留 material pack 兼容，mixed wrapper 优先 review decision。focused unittest `Ran 6 tests in 0.024s OK`。 | 通过。满足 PR #4 route/elevator material review decision 进入现场 operator drill 的最小闭环，但仍是 `software_proof_docker_route_task_field_retest_operator_drill_gate`。 |
| A / Autonomy | 输出保持 `trashbot.route_task_field_retest_operator_drill.v1` / summary schema，拒绝 unsupported schema、bad boundary、weak evidence_ref、unsafe raw path、credentials、success claim、`delivery_success=true`、`primary_actions_enabled=true`。 | 已完成。A worker 报告 required rg pass，fail-closed 测试覆盖 review-decision-derived 输入和 unsafe claims。 | 通过。Product 未发现把 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 改成真实完成的表述。 |
| B / Robot | diagnostics 只读消费 operator drill summary，输出 `robot_diagnostics_route_task_field_retest_operator_drill_summary` alias，支持 nested/top-level discovery。 | 已完成。B worker 报告 alias、nested/top-level discovery 和 review-decision-derived raw fields fail-closed filtering 已落地；diagnostics unittest `Ran 175 tests OK`。 | 通过。Robot diagnostics 仍是 metadata-only，不启用 task_orchestrator、Start、Confirm Dropoff、Cancel、ACK、Nav2、HIL 或 primary actions。 |
| C / Full-stack | mobile/web first-screen “现场操作演练” panel 承接 material callback review decision，展示 source decision、operator drill status、safe `evidence_ref`、commands/checklist/outputs/rerun/boundary。 | 已完成。C worker 报告 `node --check` pass，mobile unittest `Ran 72 tests OK`，copy/export whitelist-only。 | 通过。手机端 copy/export 只读，Start Delivery、Confirm Dropoff、Cancel gating 不变。 |
| Product | 更新 `OKR.md`、`docs/process/okr_progress_log.md` 和 sprint closeout docs，明确 Objective 5 保持约 68%、Objective 1 保持约 81%、Objective 2/3/4 保守保持约 99%。 | 已完成。Product closeout 新增 `tech-done.md`、`side2side_check.md`、`final.md`，更新 OKR snapshot 和 progress log。 | 通过。没有把 software proof 写成真实 route/elevator field pass、HIL、真实手机/browser 或 O5 external proof。 |

## 2. 用户价值对照

本轮的用户价值是避免现场 operator 从旧 material pack-only drill 重新开始，而是从最新 `route_task_field_retest_material_callback_review_decision` 的 accepted / missing / rejected materials、owner acknowledgement 和 next required evidence 继续执行。

实际结果满足该目标：PC gate 负责把 review decision 转成 operator commands / callback checklist / required outputs / rerun path，Robot diagnostics 和 mobile/web 只读展示同一安全摘要。普通手机用户和现场 operator 看到的是 `safe_evidence_ref`、状态、命令和边界，而不是 raw artifact、local path、credentials、ROS topic、UART、Nav2/HIL claim 或 success wording。

## 3. 证据边界对照

本轮证据只覆盖：

- `route_task_field_retest_material_callback_review_decision` 能作为 operator drill 的优先输入。
- `route_task_field_retest_operator_drill` 能输出 metadata-only summary。
- Robot diagnostics 和 mobile/web 能只读消费该 summary。
- 全链路保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

本轮不覆盖：

- 真实 route/elevator field pass。
- 真实 Nav2/fixed-route runtime。
- 真实 route completion signal 或 task record。
- 真实 dropoff/cancel completion 或 delivery success。
- 真实 WAVE ROVER/UART/HIL。
- 真实手机/browser/device behavior。
- Objective 5 external proof，包括公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration/cutover。

## 4. 验收结论

Product 判定本轮 A/B/C 验收口径已满足，可以作为 `software_proof_docker_route_task_field_retest_operator_drill_gate` 收口。OKR 数字按产品结论保守处理：Objective 5 保持约 68%，Objective 1 保持约 81%，Objective 2 / 3 / 4 保守保持约 99%。
