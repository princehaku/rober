# Sprint 2026.05.17_06-07 Route Task Field Retest Evidence Dispatch - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `software_proof_docker_route_task_field_retest_evidence_dispatch_gate`。A/B/C worker 已把 `route_task_field_retest_acceptance_brief` 后续证据要求推进为 PC / Robot / mobile 三端共同消费的现场证据包派发层：同一 safe `evidence_ref` 下可看到 dispatch status、material owners、recommended filenames、same-evidence-ref rule、backfill order、callback checklist、fail-closed rerun notes 和 required evidence packet。

本轮证据边界保持：Docker-only、software proof、metadata-only、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 用户价值和产品北极星

用户价值：现场支持人员现在能按 owner 和推荐文件名收集真实证据，而不是只读到一份验收简报。证据包派发层把 door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result、Nav2/fixed-route runtime log、route completion signal 和 task record 的回填顺序固定下来，减少现场复测漏项。

产品北极星：继续服务“普通手机用户交付垃圾后，小车可验证地完成固定路线/电梯 assisted delivery 送达闭环”。本轮没有把 software proof 夸大成真实送达。

## 3. OKR 更新

- Objective 1：保持约 77%。本轮没有真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery`，也没有 PR #5 所需真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- Objective 2：约 88% -> 约 89%。理由是 evidence dispatch 把 door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 从 acceptance brief 推进为 owner/file/backfill/callback dispatch；仍不是真实 field pass。
- Objective 3：约 88% -> 约 89%。理由是 Nav2/fixed-route runtime log、route completion signal、task record 的同一 `evidence_ref` 回填顺序、建议文件名和 callback checklist 被固化；仍不是真实 Nav2/fixed-route。
- Objective 4：保持约 99%。理由是手机只读“现场证据包派发” panel 是 phone-safe 支援增量，但没有真实 phone/browser 或 production app proof，且 O4 已接近 99%。
- Objective 5：保持约 66%。本机 Docker-only；本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他 Objective 5 external proof。

## 4. KR 拆解或更新

- Objective 2 KR5/KR6/KR7：证据包派发层明确任务记录、门状态、楼层确认、人工协助、dropoff/cancel completion 与 delivery result 的 owner/file/backfill/callback 口径。
- Objective 3 KR2/KR3/KR4：固定路线复测所需 runtime log、completion signal、task record 的文件命名和同一 `evidence_ref` 规则被固化。
- Objective 4 KR1/KR5/KR6/KR7：手机端新增只读解释层，但不改变主操作授权，不暴露 raw JSON、raw path、credential、ROS topic、serial/UART、WAVE ROVER、DB/queue URL 或完整 artifact。

## 5. 本轮实际改动

Product Closeout 改动：

- `sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/tech-done.md`
- `sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/side2side_check.md`
- `sprints/2026.05.17_06-07_route-task-field-retest-evidence-dispatch/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Engineer worker 改动已由各 owner 完成并由 `tech-done.md` 汇总；Product Closeout 未修改工程代码或 worker 文件。

## 6. 验证结果

Product Closeout 验收命令通过：

```text
rg route_task_field_retest_evidence_dispatch / closeout boundary coverage
pass

git diff --check scoped to Product Closeout files
pass

git status --short
reviewed; only intended Product Closeout files plus known A/B/C/planning files are present
```

A/B/C worker 验证摘要：

- Task A Autonomy：py_compile pass；unittest `Ran 5 tests in 0.067s OK`；CLI help pass；rg coverage pass；scoped diff check pass。
- Task B Robot：py_compile pass；diagnostics unittest `Ran 132 tests in 0.186s OK`；rg pass；scoped diff check pass。
- Task C Full-stack：mobile unittest `Ran 34 tests in 0.081s OK`；`node --check mobile/web/app.js` pass；rg pass；scoped diff check pass；首轮 fixture forbidden `raw path` wording 已修复。

## 7. 失败定位

Product Closeout 未出现未关闭失败。

已知 worker 失败定位：

- Task C 首轮 fixture forbidden `raw path` wording 被围栏拦截，已修复并复验通过。

## 8. 剩余风险和证据链缺口

- 本轮不是真实 route/elevator field pass、真实 Nav2/fixed-route、真实 task record、真实 route completion signal、真实 dropoff/cancel completion、delivery success、真实手机/browser、production app、WAVE ROVER、真实串口/UART、HIL 或 Objective 5 external proof。
- 仍需按同一 `evidence_ref` 回填真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion 和 delivery_result。
- PR #4 相关电梯 assisted delivery 的真实门状态、目标楼层确认、人工协助记录仍未完成。
- PR #5 相关单目 + 2D LiDAR + ToF 安全环仍缺真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- Objective 5 仍是最低数值，但缺真实外部云/4G/OSS/CDN/DB/queue 证据；不得继续用本地 metadata depth 上调。

## 9. 下一步

下一轮优先不要再堆本地 wrapper。若没有 Objective 5 外部材料，应转向真实现场材料回填：用本轮 dispatch 指定的 owner/file/backfill/callback checklist 收集同一 `evidence_ref` 下的 route/elevator field materials，或补 PR #5 真实 2D LiDAR / ToF 材料。
