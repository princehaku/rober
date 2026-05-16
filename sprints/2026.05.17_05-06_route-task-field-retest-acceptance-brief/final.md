# Sprint 2026.05.17_05-06 Route Task Field Retest Acceptance Brief - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`，把 `route_task_field_retest_drill_console` 后的现场复测动作整理为 acceptance brief / handoff packet。PC gate、Robot diagnostics 和 mobile/web 均能围绕 `route_task_field_retest_acceptance_brief` 只读消费 safe summary，并保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

本轮是 Docker-only local software proof，不是真实 route/elevator field pass、HIL、真实手机/browser、production app、真实投放、dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 2. 用户价值和产品北极星

用户价值：现场支持不再只看到 drill console 的命令和缺失材料，而是得到一份可执行验收简报：现场准入条件、执行 checklist、pass/fail criteria、required evidence packet、owner handoff 和 rerun notes 都绑定同一 safe `evidence_ref`。

产品北极星：普通手机用户最终只需要理解任务是否可继续、哪里需要人工介入；工程侧必须保留可回放证据链。本轮提高了“可解释、可复盘、可交接”的程度，但仍未证明真实送达。

## 3. OKR 更新

保守更新：

- Objective 1：保持约 77%。本轮没有真实 WAVE ROVER、UART、HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或真实 2D LiDAR / ToF 材料。
- Objective 2：约 87% -> 约 88%。理由是 acceptance brief 把真实门状态、目标楼层确认、人工协助、dropoff/cancel completion 和 delivery result 的准入/判定/交接固化到 required evidence packet，下一次 field retest 更可执行。
- Objective 3：约 87% -> 约 88%。理由是 Nav2/fixed-route runtime log、route completion signal、task record 被纳入 pass/fail criteria 和 evidence packet，固定路线复测材料缺口更清晰。
- Objective 4：约 98% -> 约 99%。理由是 mobile/web 新增 phone-safe 只读“现场复测验收简报” panel，现场支持能看懂 acceptance status、safe evidence ref、required evidence packet、owner handoff 和边界，且主操作 gating 不变。
- Objective 5：保持约 66%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration；Objective 5 仍不得因本地 metadata/software proof 提升。

## 4. 验证证据

Worker 验证已完成：

- Task A Autonomy：py_compile PASS；unittest `Ran 5 tests ... OK`；CLI help PASS；required `rg` PASS；scoped diff check PASS。
- Task B Robot：py_compile PASS；diagnostics unittest `Ran 130 tests ... OK`；required `rg` PASS；scoped diff check PASS。
- Task C Full-stack：mobile unittest `Ran 32 tests ... OK`；`node --check mobile/web/app.js` PASS；required `rg` PASS；scoped diff check PASS。

Product closeout 验证：

- Required closeout `rg`：PASS，命中 sprint closeout、`OKR.md` 4.1 和 progress log 中的 `route_task_field_retest_acceptance_brief`、`software_proof_docker_route_task_field_retest_acceptance_brief_gate`、Objective 2 / Objective 3 / Objective 4 / Objective 5、Docker-only、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 与 PR #5 边界。
- Scoped closeout `git diff --check`：PASS，无输出。

## 5. 失败定位

Task A 首轮 unittest 因 safe summary 自身包含 forbidden wording 触发 `blocked_unsafe_acceptance_brief_summary`，已修正并复验通过。

Product closeout 未发现工程实现文件需要回滚或覆盖；本轮只改 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 6. OKR 最低优先级复核

`OKR.md` 4.1 中 Objective 5 仍是数值最低 Objective，约 66%。本轮不针对 Objective 5 的理由仍成立：当前没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。继续堆本地 O5 metadata depth 不会形成 Objective 5 external proof。

本轮也不转向 Objective 1 的理由仍成立：PR #5 暴露的单目 + 2D LiDAR + ToF safety ring、真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍缺真实材料；继续本地硬件 wrapper 会重复消费硬件 blocker。

## 7. 剩余风险和下一步证据链

- Objective 2 / Objective 3 下一步必须拿真实现场材料：Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result，并保持同一 `evidence_ref`。
- Objective 4 下一步仍需真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 和真实现场 phone behavior。
- Objective 1 下一步仍需真实 WAVE ROVER/UART/HIL、`T=1001` feedback、`/odom`、`/imu/data`、`/battery`，以及真实 2D LiDAR / ToF 材料。
- Objective 5 下一步只有在外部材料到位时才应继续推进：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。

## 8. 最终状态

本轮 Product closeout 接受为 O2/O3/O4 的 software proof 增量：acceptance brief / handoff packet 已让现场复测进入“可执行验收简报”阶段。边界保持保守，不宣称真实 field pass、HIL、真实手机、Objective 5 external proof 或 delivery success。
