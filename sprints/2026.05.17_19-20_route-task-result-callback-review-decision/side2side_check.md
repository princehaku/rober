# Sprint 2026.05.17_19-20 Route Task Result Callback Review Decision - Side2Side Check

sprint_type: epic

## 1. 对照结论

状态：`PASS_WITH_SOFTWARE_PROOF_BOUNDARY`。

本轮 PRD 目标是把 callback packet 摄取结果进一步收敛成 review decision：哪些材料可进入结果复核，哪些需要 owner backfill，哪些必须 callback rerun、evidence-ref mismatch rerun 或 unsafe rejection。A/B/C worker 结果与 PRD 一致，Product closeout 已把 OKR 与进展日志更新到同一证据边界。

## 2. 用户价值和产品北极星

用户价值：现场支持人员不再只看到 accepted/missing/rejected updates，而是能看到下一步复核决策、owner handoff、next required evidence 和 rerun path，减少 route/elevator 现场材料回填后的口头判断。

产品北极星：把低成本 ROS2 垃圾投递机器人推进到“证据链可回填、可复核、可追责”，但不越过真实硬件、真实路线、真实手机和真实外部云证据边界。

## 3. OKR 映射和 KR 拆解

- Objective 2：PR #4 elevator-assisted delivery 主链继续从 callback intake 进入 callback review decision，覆盖 door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result 的 owner 决策。
- Objective 3：固定路线 / Nav2 result materials 继续从 callback updates 进入 result-review 前置决策，覆盖 runtime log、route completion signal 和 task record 的 backfill / rerun 路径。
- Objective 4：mobile/web 只读 panel 展示 review decision 和安全边界，不改变 Start / Confirm / Cancel gating。
- Objective 5：仍是数值最低但本轮不推进；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。

KR 拆解结果：

- 已完成：callback review decision gate。
- 已完成：Robot diagnostics metadata-only consumer。
- 已完成：mobile/web read-only review-decision panel。
- 已完成：OKR / progress log / sprint closeout 更新。
- 未完成且不应冒充完成：真实 field pass、真实 Nav2/fixed-route、真实手机/browser、真实 HIL、Objective 5 external proof。

## 4. 本轮核心抓手和责任 Engineer

- Autonomy Algorithm Engineer：PC gate 和 evidence contract。
- Robot Platform Engineer：diagnostics metadata-only consumer。
- User Touchpoint Full-Stack Engineer：mobile/web 只读 panel。
- Product Manager / OKR Owner：OKR、progress log、tech-done、side2side 和 final closeout。

## 5. 验收口径对照

| 验收项 | 结果 |
| --- | --- |
| PC gate 支持 ready / missing / rejected / mismatch fixture fail-closed 判定 | 通过，Task A unittest `Ran 6 tests OK` |
| Robot diagnostics 支持 file/env/top-level/nested summary 并 fail closed | 通过，Task B unittest `Ran 156 tests OK` |
| mobile/web 展示 review decision、material status、owner handoff、next evidence 和 boundary flags | 通过，Task C unittest `Ran 52 tests OK`，`node --check` pass |
| 保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` | 通过，A/B/C/D required `rg` 均覆盖 |
| Product closeout 更新 OKR、progress log 和 sprint 文档 | 通过，Task D required `rg` 与 scoped `git diff --check` pass |

## 6. 风险、阻塞和证据链缺口

- 本轮仍是 `software_proof_docker_route_task_field_retest_result_callback_review_decision_gate`，不是实际 field run。
- 真实 route/elevator 材料仍缺：门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery result。
- 真实手机/browser、production app、真实 PWA prompt/user choice 没有补齐。
- Objective 5 external proof 仍不可用，不得把本轮写成 O5 progress。
- PR #5 2D LiDAR / ToF 真实 source、receipt、采购、安装、接线、电源、标定与 HIL-entry 材料仍未补齐。

## 7. Side2Side 判断

本轮满足 PRD 和 tech-plan 验收口径，可以进入 final closeout。下一步不应继续堆本地 metadata 深度来提升 Objective 5；若没有真实 external proof，应把下一轮限定到真实设备/现场材料回填或明确等待 CEO 提供现场材料。
